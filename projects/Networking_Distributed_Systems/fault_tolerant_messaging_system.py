"""
fault_tolerant_messaging_system.py
A Python OOP simulation of a fault-tolerant message broker with ACKs,
retries, persistence, and replication.
"""

import uuid
import time
import random
import threading
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional, Callable


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class MessageStatus(Enum):
    PENDING     = "PENDING"       # queued, not yet delivered
    IN_FLIGHT   = "IN_FLIGHT"     # handed to consumer, awaiting ACK
    DELIVERED   = "DELIVERED"     # ACK received
    FAILED      = "FAILED"        # all retries exhausted
    DEAD_LETTER = "DEAD_LETTER"   # moved to DLQ


class ConsumerStatus(Enum):
    ONLINE  = "ONLINE"
    OFFLINE = "OFFLINE"
    BUSY    = "BUSY"


# ─────────────────────────────────────────────────────────────
# Message
# ─────────────────────────────────────────────────────────────

class Message:
    """Immutable envelope carrying a payload between producer and consumer."""

    MAX_RETRIES = 3

    def __init__(self, sender: str, receiver: str, content: str,
                 topic: str = "default"):
        if not sender or not isinstance(sender, str):
            raise ValueError("sender must be a non-empty string.")
        if not receiver or not isinstance(receiver, str):
            raise ValueError("receiver must be a non-empty string.")
        if not content or not isinstance(content, str):
            raise ValueError("content must be a non-empty string.")
        if not topic or not isinstance(topic, str):
            raise ValueError("topic must be a non-empty string.")

        self.message_id: str          = str(uuid.uuid4())[:8].upper()
        self.sender: str              = sender
        self.receiver: str            = receiver
        self.content: str             = content
        self.topic: str               = topic
        self.timestamp: datetime      = datetime.now()
        self.status: MessageStatus    = MessageStatus.PENDING
        self.retry_count: int         = 0
        self.last_attempt: Optional[datetime] = None
        self._ack_event               = threading.Event()

    # ── state transitions ─────────────────────────────────────

    def mark_in_flight(self) -> None:
        self.status       = MessageStatus.IN_FLIGHT
        self.last_attempt = datetime.now()
        self.retry_count += 1

    def acknowledge(self) -> None:
        self.status = MessageStatus.DELIVERED
        self._ack_event.set()

    def fail(self) -> None:
        if self.retry_count >= self.MAX_RETRIES:
            self.status = MessageStatus.DEAD_LETTER
        else:
            self.status = MessageStatus.FAILED

    def can_retry(self) -> bool:
        return self.retry_count < self.MAX_RETRIES

    def wait_for_ack(self, timeout: float = 2.0) -> bool:
        return self._ack_event.wait(timeout=timeout)

    # ── display ───────────────────────────────────────────────

    def short(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        return (f"[{ts}] MSG#{self.message_id} "
                f"{self.sender}->{self.receiver} "
                f"topic={self.topic!r} "
                f"retry={self.retry_count} "
                f"status={self.status.value}")

    def __repr__(self) -> str:
        return f"Message(id={self.message_id}, status={self.status.value})"


# ─────────────────────────────────────────────────────────────
# MessageQueue
# ─────────────────────────────────────────────────────────────

class MessageQueue:
    """Thread-safe FIFO queue for a single topic, with persistence."""

    def __init__(self, topic: str, max_size: int = 500):
        if not topic:
            raise ValueError("topic must be a non-empty string.")
        if max_size < 1:
            raise ValueError("max_size must be ≥ 1.")

        self.topic: str                   = topic
        self.max_size: int                = max_size
        self._queue: list[Message]        = []
        self._persisted: dict[str, Message] = {}   # id -> msg (write-ahead log)
        self._dead_letter: list[Message]  = []
        self._lock                        = threading.Lock()
        self._enqueue_count: int          = 0
        self._dequeue_count: int          = 0

    # ── enqueue / dequeue ─────────────────────────────────────

    def enqueue(self, msg: Message) -> bool:
        with self._lock:
            if len(self._queue) >= self.max_size:
                return False
            self._queue.append(msg)
            self._persisted[msg.message_id] = msg   # persist immediately
            self._enqueue_count += 1
            return True

    def dequeue(self) -> Optional[Message]:
        with self._lock:
            if not self._queue:
                return None
            msg = self._queue.pop(0)
            self._dequeue_count += 1
            return msg

    def requeue(self, msg: Message) -> None:
        """Put a failed-but-retryable message back at the head."""
        with self._lock:
            self._queue.insert(0, msg)

    def move_to_dlq(self, msg: Message) -> None:
        """Move exhausted messages to the dead-letter queue."""
        with self._lock:
            msg.status = MessageStatus.DEAD_LETTER
            self._dead_letter.append(msg)
            self._persisted.pop(msg.message_id, None)

    def confirm_delivery(self, message_id: str) -> None:
        """Remove from persistence store after successful ACK."""
        with self._lock:
            self._persisted.pop(message_id, None)

    # ── accessors ─────────────────────────────────────────────

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def dlq_size(self) -> int:
        with self._lock:
            return len(self._dead_letter)

    def dead_letters(self) -> list[Message]:
        with self._lock:
            return list(self._dead_letter)

    def persisted_ids(self) -> list[str]:
        with self._lock:
            return list(self._persisted.keys())

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "topic":    self.topic,
                "queued":   len(self._queue),
                "persisted": len(self._persisted),
                "dlq":      len(self._dead_letter),
                "enqueued": self._enqueue_count,
                "dequeued": self._dequeue_count,
            }

    def __repr__(self) -> str:
        return f"MessageQueue(topic={self.topic!r}, size={self.size()})"


# ─────────────────────────────────────────────────────────────
# ReplicaStore  (simulated backup storage)
# ─────────────────────────────────────────────────────────────

class ReplicaStore:
    """Simulates a secondary in-memory replica for fault tolerance."""

    def __init__(self, name: str):
        self.name = name
        self._store: dict[str, Message] = {}
        self._lock = threading.Lock()
        self._online = True

    def replicate(self, msg: Message) -> bool:
        if not self._online:
            return False
        with self._lock:
            self._store[msg.message_id] = msg
            return True

    def recover(self) -> list[Message]:
        """Return all replicated messages (used after primary failure)."""
        with self._lock:
            return list(self._store.values())

    def remove(self, message_id: str) -> None:
        with self._lock:
            self._store.pop(message_id, None)

    def set_online(self, state: bool) -> None:
        self._online = state
        status = "ONLINE" if state else "OFFLINE"
        print(f"  💾  Replica '{self.name}' -> {status}")

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)

    def __repr__(self) -> str:
        return f"ReplicaStore(name={self.name!r}, stored={self.size})"


# ─────────────────────────────────────────────────────────────
# Producer
# ─────────────────────────────────────────────────────────────

class Producer:
    """Sends messages to the broker."""

    def __init__(self, producer_id: str,
                 failure_rate: float = 0.0):
        if not producer_id:
            raise ValueError("producer_id must be a non-empty string.")
        if not (0.0 <= failure_rate <= 1.0):
            raise ValueError("failure_rate must be between 0.0 and 1.0.")

        self.producer_id: str          = producer_id
        self.failure_rate: float       = failure_rate
        self._sent_count: int          = 0
        self._failed_count: int        = 0
        self._broker: Optional[object] = None   # set by broker on registration

    def connect(self, broker: "Broker") -> None:
        self._broker = broker
        print(f"  🔌  Producer '{self.producer_id}' connected to broker.")

    def send(self, receiver: str, content: str, topic: str = "default") -> Optional[Message]:
        if self._broker is None:
            raise RuntimeError("Producer not connected to a broker.")
        if not content:
            raise ValueError("content must not be empty.")

        # Simulate producer-side failure
        if random.random() < self.failure_rate:
            self._failed_count += 1
            print(f"  ✗  Producer '{self.producer_id}' failed to send (simulated fault).")
            return None

        msg = Message(sender=self.producer_id, receiver=receiver,
                      content=content, topic=topic)
        accepted = self._broker.route(msg)
        if accepted:
            self._sent_count += 1
            print(f"  [SENT] [{self.producer_id}] Sent MSG#{msg.message_id} "
                  f"-> {receiver!r} topic={topic!r}  content={content[:40]!r}")
        else:
            self._failed_count += 1
            print(f"  ✗  Broker rejected MSG#{msg.message_id} (queue full?).")
        return msg if accepted else None

    @property
    def stats(self) -> dict:
        return {"id": self.producer_id,
                "sent": self._sent_count,
                "failed": self._failed_count}

    def __repr__(self) -> str:
        return f"Producer(id={self.producer_id!r}, sent={self._sent_count})"


# ─────────────────────────────────────────────────────────────
# Consumer
# ─────────────────────────────────────────────────────────────

class Consumer:
    """Receives and processes messages from the broker."""

    def __init__(self, consumer_id: str,
                 processing_failure_rate: float = 0.0,
                 offline_probability: float = 0.0):
        if not consumer_id:
            raise ValueError("consumer_id must be a non-empty string.")
        if not (0.0 <= processing_failure_rate <= 1.0):
            raise ValueError("processing_failure_rate must be 0.0–1.0.")
        if not (0.0 <= offline_probability <= 1.0):
            raise ValueError("offline_probability must be 0.0–1.0.")

        self.consumer_id: str              = consumer_id
        self.processing_failure_rate: float = processing_failure_rate
        self.offline_probability: float    = offline_probability
        self.status: ConsumerStatus        = ConsumerStatus.ONLINE
        self._received: list[Message]      = []
        self._lock                         = threading.Lock()
        self._subscriptions: set[str]      = set()

    # ── subscriptions ─────────────────────────────────────────

    def subscribe(self, topic: str) -> None:
        self._subscriptions.add(topic)

    def is_subscribed(self, topic: str) -> bool:
        return topic in self._subscriptions or "default" in self._subscriptions

    # ── delivery ──────────────────────────────────────────────

    def deliver(self, msg: Message) -> bool:
        """
        Attempt to deliver a message.
        Returns True if processed successfully (ACK), False otherwise (NACK).
        """
        # Simulate consumer going offline
        if random.random() < self.offline_probability:
            self.status = ConsumerStatus.OFFLINE
            print(f"  📵  Consumer '{self.consumer_id}' went OFFLINE "
                  f"(MSG#{msg.message_id} undeliverable).")
            return False

        self.status = ConsumerStatus.ONLINE

        # Simulate processing failure
        if random.random() < self.processing_failure_rate:
            print(f"  ⚠  Consumer '{self.consumer_id}' processing FAILED "
                  f"for MSG#{msg.message_id}.")
            return False

        # Success path
        with self._lock:
            self._received.append(msg)
        msg.acknowledge()
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  📥  [{ts}] Consumer '{self.consumer_id}' ACK MSG#{msg.message_id} "
              f"content={msg.content[:40]!r}")
        return True

    def go_online(self) -> None:
        self.status = ConsumerStatus.ONLINE
        print(f"  ✅  Consumer '{self.consumer_id}' is back ONLINE.")

    def go_offline(self) -> None:
        self.status = ConsumerStatus.OFFLINE
        print(f"  🔴  Consumer '{self.consumer_id}' forced OFFLINE.")

    @property
    def received_count(self) -> int:
        with self._lock:
            return len(self._received)

    @property
    def stats(self) -> dict:
        return {"id": self.consumer_id,
                "status": self.status.value,
                "received": self.received_count,
                "subscriptions": list(self._subscriptions)}

    def __repr__(self) -> str:
        return (f"Consumer(id={self.consumer_id!r}, "
                f"status={self.status.value}, "
                f"received={self.received_count})")


# ─────────────────────────────────────────────────────────────
# Broker
# ─────────────────────────────────────────────────────────────

class Broker:
    """
    Routes messages from producers to consumers.
    Handles queuing, retry logic, ACK tracking, and replication.
    """

    RETRY_DELAY = 0.3   # seconds between retries

    def __init__(self, broker_id: str = "primary"):
        self.broker_id: str                             = broker_id
        self._queues: dict[str, MessageQueue]           = {}
        self._consumers: dict[str, Consumer]            = {}   # consumer_id -> Consumer
        self._topic_consumers: dict[str, list[str]]     = defaultdict(list)
        self._replicas: list[ReplicaStore]              = []
        self._delivered: list[Message]                  = []
        self._dead_letters: list[Message]               = []
        self._lock                                      = threading.Lock()
        self._total_routed: int                         = 0
        self._total_delivered: int                      = 0
        self._total_failed: int                         = 0

    # ── registration ──────────────────────────────────────────

    def register_consumer(self, consumer: Consumer,
                          topics: Optional[list[str]] = None) -> None:
        topics = topics or ["default"]
        for t in topics:
            consumer.subscribe(t)
            if consumer.consumer_id not in self._topic_consumers[t]:
                self._topic_consumers[t].append(consumer.consumer_id)
            if t not in self._queues:
                self._queues[t] = MessageQueue(t)
        self._consumers[consumer.consumer_id] = consumer
        print(f"  ✔  Consumer '{consumer.consumer_id}' registered "
              f"for topics {topics}.")

    def add_replica(self, replica: ReplicaStore) -> None:
        self._replicas.append(replica)
        print(f"  💾  Replica store '{replica.name}' attached to broker.")

    def _get_or_create_queue(self, topic: str) -> MessageQueue:
        if topic not in self._queues:
            self._queues[topic] = MessageQueue(topic)
        return self._queues[topic]

    # ── routing ───────────────────────────────────────────────

    def route(self, msg: Message) -> bool:
        """Accept a message from a producer and enqueue it."""
        queue = self._get_or_create_queue(msg.topic)
        ok = queue.enqueue(msg)
        if ok:
            # Replicate immediately
            for replica in self._replicas:
                replica.replicate(msg)
            self._total_routed += 1
        return ok

    # ── delivery engine ───────────────────────────────────────

    def _select_consumer(self, topic: str, receiver: str) -> Optional[Consumer]:
        """
        Find the best available consumer for this message.
        Prefer the explicit receiver; fall back to any online subscriber.
        """
        # Try explicit receiver first
        consumer = self._consumers.get(receiver)
        if consumer and consumer.status == ConsumerStatus.ONLINE:
            return consumer

        # Round-robin over online subscribers on this topic
        for cid in self._topic_consumers.get(topic, []):
            c = self._consumers.get(cid)
            if c and c.status == ConsumerStatus.ONLINE and cid != receiver:
                return c
        return None

    def _attempt_delivery(self, msg: Message,
                          consumer: Consumer) -> bool:
        msg.mark_in_flight()
        success = consumer.deliver(msg)
        if success:
            queue = self._queues.get(msg.topic)
            if queue:
                queue.confirm_delivery(msg.message_id)
            for replica in self._replicas:
                replica.remove(msg.message_id)
            with self._lock:
                self._delivered.append(msg)
                self._total_delivered += 1
        return success

    def dispatch(self, topic: str = "default") -> int:
        """
        Drain a queue, delivering each message with retry logic.
        Returns number of successfully delivered messages.
        """
        queue = self._queues.get(topic)
        if not queue or queue.size() == 0:
            return 0

        delivered_this_round = 0

        while queue.size() > 0:
            msg = queue.dequeue()
            if msg is None:
                break

            delivered = False
            while not delivered and msg.can_retry():
                consumer = self._select_consumer(msg.topic, msg.receiver)
                if consumer is None:
                    print(f"  ⏳  No consumer available for MSG#{msg.message_id} "
                          f"(attempt {msg.retry_count + 1}/{Message.MAX_RETRIES}). "
                          f"Retrying…")
                    time.sleep(self.RETRY_DELAY)
                    msg.retry_count += 1   # count the wait as an attempt
                    continue

                delivered = self._attempt_delivery(msg, consumer)
                if not delivered:
                    if msg.can_retry():
                        print(f"  🔁  Retrying MSG#{msg.message_id} "
                              f"(attempt {msg.retry_count}/{Message.MAX_RETRIES})…")
                        time.sleep(self.RETRY_DELAY)
                    else:
                        break

            if delivered:
                delivered_this_round += 1
            else:
                msg.fail()
                queue.move_to_dlq(msg)
                with self._lock:
                    self._dead_letters.append(msg)
                    self._total_failed += 1
                print(f"  ☠  MSG#{msg.message_id} moved to Dead-Letter Queue "
                      f"after {msg.retry_count} attempt(s).")

        return delivered_this_round

    def dispatch_all(self) -> dict[str, int]:
        """Dispatch all known topics. Returns {topic: delivered_count}."""
        results = {}
        for topic in list(self._queues.keys()):
            count = self.dispatch(topic)
            results[topic] = count
        return results

    # ── accessors ─────────────────────────────────────────────

    def queue_snapshot(self) -> dict[str, dict]:
        return {t: q.stats for t, q in self._queues.items()}

    @property
    def stats(self) -> dict:
        return {
            "broker_id":  self.broker_id,
            "total_routed":    self._total_routed,
            "total_delivered": self._total_delivered,
            "total_failed":    self._total_failed,
            "dead_letters":    len(self._dead_letters),
            "replicas":        len(self._replicas),
        }

    def __repr__(self) -> str:
        return (f"Broker(id={self.broker_id!r}, "
                f"delivered={self._total_delivered}, "
                f"failed={self._total_failed})")


# ─────────────────────────────────────────────────────────────
# MessagingManager
# ─────────────────────────────────────────────────────────────

class MessagingManager:
    """
    Top-level coordinator: registers all components, runs scenarios,
    and displays system-wide statistics.
    """

    def __init__(self, broker: Broker):
        if not isinstance(broker, Broker):
            raise TypeError("broker must be a Broker instance.")
        self.broker = broker
        self._producers: dict[str, Producer]  = {}
        self._consumers: dict[str, Consumer]  = {}

    # ── registration ──────────────────────────────────────────

    def add_producer(self, producer: Producer) -> None:
        producer.connect(self.broker)
        self._producers[producer.producer_id] = producer

    def add_consumer(self, consumer: Consumer,
                     topics: Optional[list[str]] = None) -> None:
        self.broker.register_consumer(consumer, topics)
        self._consumers[consumer.consumer_id] = consumer

    # ── helpers ───────────────────────────────────────────────

    def get_producer(self, pid: str) -> Producer:
        p = self._producers.get(pid)
        if p is None:
            raise KeyError(f"Producer '{pid}' not found.")
        return p

    def get_consumer(self, cid: str) -> Consumer:
        c = self._consumers.get(cid)
        if c is None:
            raise KeyError(f"Consumer '{cid}' not found.")
        return c

    # ── dispatch ──────────────────────────────────────────────

    def flush(self, topic: Optional[str] = None) -> None:
        """Dispatch queued messages (one topic or all)."""
        if topic:
            n = self.broker.dispatch(topic)
            print(f"  ⚡  Flushed topic {topic!r}: {n} message(s) delivered.")
        else:
            results = self.broker.dispatch_all()
            total = sum(results.values())
            print(f"  ⚡  Flushed all topics: {total} message(s) delivered "
                  f"({dict(results)}).")

    # ── statistics ────────────────────────────────────────────

    def print_statistics(self) -> None:
        sep = "═" * 64
        print(f"\n{sep}")
        print("  MESSAGING SYSTEM — STATISTICS")
        print(sep)

        bs = self.broker.stats
        print(f"  Broker          : {bs['broker_id']}")
        print(f"  Total routed    : {bs['total_routed']}")
        print(f"  Total delivered : {bs['total_delivered']}")
        print(f"  Total failed    : {bs['total_failed']}")
        print(f"  Dead-letter Q   : {bs['dead_letters']}")
        print(f"  Replica stores  : {bs['replicas']}")

        # Delivery rate
        if bs['total_routed'] > 0:
            rate = bs['total_delivered'] / bs['total_routed'] * 100
            print(f"  Delivery rate   : {rate:.1f}%")

        print(f"\n  Queue snapshots:")
        for topic, qs in self.broker.queue_snapshot().items():
            print(f"    [{topic}]  queued={qs['queued']}  "
                  f"persisted={qs['persisted']}  dlq={qs['dlq']}  "
                  f"enqueued={qs['enqueued']}  dequeued={qs['dequeued']}")

        print(f"\n  Producers:")
        for p in self._producers.values():
            ps = p.stats
            print(f"    {ps['id']:<20}  sent={ps['sent']}  "
                  f"failed={ps['failed']}")

        print(f"\n  Consumers:")
        for c in self._consumers.values():
            cs = c.stats
            print(f"    {cs['id']:<20}  status={cs['status']:<8}  "
                  f"received={cs['received']}  "
                  f"topics={cs['subscriptions']}")

        # Dead-letter summary
        dead = self.broker._dead_letters
        if dead:
            print(f"\n  Dead-Letter Messages ({len(dead)}):")
            for m in dead:
                print(f"    ☠  MSG#{m.message_id}  "
                      f"{m.sender}->{m.receiver}  "
                      f'"{m.content[:35]}"  '
                      f"retries={m.retry_count}")

        print(sep)

    def monitor(self) -> None:
        """Print a live-style snapshot of queue depths."""
        print("\n  ── Queue Monitor ──────────────────────────────")
        for topic, qs in self.broker.queue_snapshot().items():
            bar_len = 20
            used = min(bar_len, qs['queued'])
            bar  = "█" * used + "░" * (bar_len - used)
            print(f"  [{topic:<12}] [{bar}] {qs['queued']:>3} pending  "
                  f"dlq={qs['dlq']}")
        for c in self._consumers.values():
            icon = "✅" if c.status == ConsumerStatus.ONLINE else "🔴"
            print(f"  {icon}  {c.consumer_id:<20} "
                  f"status={c.status.value:<8}  received={c.received_count}")
        print("  ─────────────────────────────────────────────")


# ─────────────────────────────────────────────────────────────
# Demo / main
# ─────────────────────────────────────────────────────────────

def _section(title: str) -> None:
    print(f"\n{'═' * 64}")
    print(f"  {title}")
    print(f"{'═' * 64}")


def main() -> None:
    _section("FAULT-TOLERANT MESSAGING SYSTEM  —  Demo")

    # ══════════════════════════════════════════════════════════
    # SCENARIO 1: Happy Path — normal delivery, no failures
    # ══════════════════════════════════════════════════════════
    _section("SCENARIO 1 — Happy Path (no failures)")

    broker1  = Broker("broker-alpha")
    replica1 = ReplicaStore("replica-1")
    broker1.add_replica(replica1)

    mgr1 = MessagingManager(broker1)

    p1 = Producer("alice")
    p2 = Producer("bob")
    c1 = Consumer("consumer-A")
    c2 = Consumer("consumer-B")

    mgr1.add_producer(p1)
    mgr1.add_producer(p2)
    mgr1.add_consumer(c1, topics=["orders", "default"])
    mgr1.add_consumer(c2, topics=["notifications", "default"])

    print()
    p1.send("consumer-A", "New order #1001 placed",       topic="orders")
    p1.send("consumer-A", "New order #1002 placed",       topic="orders")
    p2.send("consumer-B", "Welcome email for user@x.com", topic="notifications")
    p2.send("consumer-B", "Password reset requested",     topic="notifications")
    p1.send("consumer-B", "System health: OK",            topic="default")

    print()
    mgr1.monitor()
    print()
    mgr1.flush()
    mgr1.print_statistics()

    # ══════════════════════════════════════════════════════════
    # SCENARIO 2: Consumer goes offline -> retry -> comes back
    # ══════════════════════════════════════════════════════════
    _section("SCENARIO 2 — Consumer Offline -> Retry -> Recovery")

    broker2  = Broker("broker-beta")
    replica2 = ReplicaStore("replica-2")
    broker2.add_replica(replica2)

    mgr2 = MessagingManager(broker2)

    prod  = Producer("service-gateway")
    cons  = Consumer("worker-1", processing_failure_rate=0.0)

    mgr2.add_producer(prod)
    mgr2.add_consumer(cons, topics=["tasks"])

    print()
    prod.send("worker-1", "Process job #A",  topic="tasks")
    prod.send("worker-1", "Process job #B",  topic="tasks")
    prod.send("worker-1", "Process job #C",  topic="tasks")

    # Force consumer offline before dispatch
    cons.go_offline()
    print()
    mgr2.monitor()

    # First dispatch attempt — consumer is offline (retries will exhaust or wait)
    # We'll only do one forced flush to show the waiting, then bring it back
    print("\n  ── Attempting dispatch (consumer offline) …")

    # Deliver first message in a thread, then bring consumer back mid-flight
    def _delayed_recovery():
        time.sleep(0.5)
        cons.go_online()

    t = threading.Thread(target=_delayed_recovery, daemon=True)
    t.start()

    mgr2.flush(topic="tasks")
    t.join()
    mgr2.print_statistics()

    # ══════════════════════════════════════════════════════════
    # SCENARIO 3: Processing failures -> retries -> dead-letter
    # ══════════════════════════════════════════════════════════
    _section("SCENARIO 3 — Processing Failures & Dead-Letter Queue")

    broker3 = Broker("broker-gamma")
    mgr3    = MessagingManager(broker3)

    sender    = Producer("api-gateway")
    flaky_svc = Consumer("flaky-service",
                         processing_failure_rate=0.85)  # very unreliable

    mgr3.add_producer(sender)
    mgr3.add_consumer(flaky_svc, topics=["payments"])

    print()
    for i in range(1, 6):
        sender.send("flaky-service", f"Payment txn #{i:03d}", topic="payments")

    print()
    mgr3.flush(topic="payments")
    mgr3.print_statistics()

    # ══════════════════════════════════════════════════════════
    # SCENARIO 4: Replica recovery simulation
    # ══════════════════════════════════════════════════════════
    _section("SCENARIO 4 — Replica / Persistence Recovery")

    broker4  = Broker("broker-delta")
    primary  = ReplicaStore("primary-replica")
    secondary = ReplicaStore("secondary-replica")

    broker4.add_replica(primary)
    broker4.add_replica(secondary)

    mgr4 = MessagingManager(broker4)

    writer = Producer("data-writer")
    reader = Consumer("data-reader")

    mgr4.add_producer(writer)
    mgr4.add_consumer(reader, topics=["events"])

    print()
    writer.send("data-reader", "Event: user.signup id=42",  topic="events")
    writer.send("data-reader", "Event: purchase.done id=7", topic="events")
    writer.send("data-reader", "Event: logout id=99",       topic="events")

    print(f"\n  Primary replica holds   : {primary.size} message(s)")
    print(f"  Secondary replica holds : {secondary.size} message(s)")

    # Simulate primary replica going offline
    primary.set_online(False)
    print("\n  ── Primary replica offline; secondary still intact ──")
    print(f"  Messages recoverable from secondary: {secondary.size}")

    # Deliver from broker (queue still has messages)
    print()
    mgr4.flush(topic="events")

    # After delivery, replicas should be cleared
    print(f"\n  Primary replica after delivery   : {primary.size} message(s)")
    print(f"  Secondary replica after delivery : {secondary.size} message(s)")

    mgr4.print_statistics()

    # ══════════════════════════════════════════════════════════
    # SCENARIO 5: Multi-topic fan-out with mixed consumers
    # ══════════════════════════════════════════════════════════
    _section("SCENARIO 5 — Multi-Topic Fan-Out")

    broker5  = Broker("broker-epsilon")
    mgr5     = MessagingManager(broker5)

    gateway = Producer("api-v2", failure_rate=0.1)

    email_svc   = Consumer("email-service")
    sms_svc     = Consumer("sms-service")
    audit_log   = Consumer("audit-logger")
    push_notif  = Consumer("push-notifications", processing_failure_rate=0.3)

    mgr5.add_producer(gateway)
    mgr5.add_consumer(email_svc,  topics=["email", "default"])
    mgr5.add_consumer(sms_svc,    topics=["sms"])
    mgr5.add_consumer(audit_log,  topics=["audit", "email", "sms"])
    mgr5.add_consumer(push_notif, topics=["push"])

    print()
    # Send to various topics
    messages = [
        ("email-service",       "Verify your email: token=abc123",   "email"),
        ("sms-service",         "OTP: 847291",                       "sms"),
        ("audit-logger",        "Admin login: user=root ip=10.0.0.1","audit"),
        ("push-notifications",  "Flash sale! 50% off today only",    "push"),
        ("push-notifications",  "Your order shipped",                 "push"),
        ("email-service",       "Monthly newsletter",                 "email"),
        ("sms-service",         "Account balance alert",              "sms"),
    ]
    for receiver, content, topic in messages:
        gateway.send(receiver, content, topic=topic)

    print()
    mgr5.monitor()
    print()
    mgr5.flush()
    mgr5.print_statistics()

    _section("All scenarios complete.")


if __name__ == "__main__":
    main()