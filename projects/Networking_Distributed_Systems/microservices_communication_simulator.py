"""
microservices_communication_simulator.py

Simulates communication between microservices in a distributed architecture.
Covers synchronous (direct HTTP-style) calls, asynchronous pub/sub via a
MessageBroker, a ServiceRegistry for discovery, circuit-breaking, and a
CommunicationManager that logs every event with full tracing.
"""

import uuid
import time
import random
import threading
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Optional, Callable, Any


# ──────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────

class ServiceStatus(Enum):
    UP       = "UP"
    DOWN     = "DOWN"
    DEGRADED = "DEGRADED"
    STARTING = "STARTING"


class RequestStatus(Enum):
    PENDING   = "PENDING"
    SUCCESS   = "SUCCESS"
    FAILED    = "FAILED"
    TIMEOUT   = "TIMEOUT"
    RETRYING  = "RETRYING"


class CircuitState(Enum):
    CLOSED   = "CLOSED"    # normal – requests pass through
    OPEN     = "OPEN"      # tripped – requests rejected immediately
    HALF_OPEN = "HALF_OPEN"  # probe – one test request allowed


class LogLevel(Enum):
    INFO    = "INFO "
    WARN    = "WARN "
    ERROR   = "ERROR"
    DEBUG   = "DEBUG"
    EVENT   = "EVENT"


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def _short_id() -> str:
    return str(uuid.uuid4())[:8].upper()


LEVEL_ICONS = {
    LogLevel.INFO:  "ℹ️ ",
    LogLevel.WARN:  "⚠️ ",
    LogLevel.ERROR: "❌",
    LogLevel.DEBUG: "🔍",
    LogLevel.EVENT: "📡",
}


# ──────────────────────────────────────────────────────────────
# EventLog  – central structured log
# ──────────────────────────────────────────────────────────────

@dataclass
class LogEntry:
    timestamp: str
    level: LogLevel
    source: str
    message: str
    trace_id: Optional[str] = None


class EventLog:
    """Append-only structured log with filtering and pretty-printing."""

    def __init__(self):
        self._entries: list[LogEntry] = []
        self._lock = threading.Lock()

    def log(self, level: LogLevel, source: str, message: str,
            trace_id: Optional[str] = None) -> None:
        entry = LogEntry(_ts(), level, source, message, trace_id)
        with self._lock:
            self._entries.append(entry)
        icon  = LEVEL_ICONS.get(level, "  ")
        trace = f"  trace={trace_id}" if trace_id else ""
        print(f"  {entry.timestamp}  {icon}  [{level.value}]  "
              f"[{source:<22}] {message}{trace}")

    def entries_for(self, source: str) -> list[LogEntry]:
        with self._lock:
            return [e for e in self._entries if e.source == source]

    def entries_by_level(self, level: LogLevel) -> list[LogEntry]:
        with self._lock:
            return [e for e in self._entries if e.level == level]

    def all_entries(self) -> list[LogEntry]:
        with self._lock:
            return list(self._entries)

    def summary(self) -> dict:
        with self._lock:
            counts: dict[str, int] = defaultdict(int)
            for e in self._entries:
                counts[e.level.name] += 1
            return dict(counts)


# ──────────────────────────────────────────────────────────────
# Request
# ──────────────────────────────────────────────────────────────

class Request:
    """Represents one service-to-service call or async message."""

    def __init__(self, source_service: str, destination_service: str,
                 payload: Any, method: str = "GET", path: str = "/",
                 trace_id: Optional[str] = None):
        if not source_service or not isinstance(source_service, str):
            raise ValueError("source_service must be a non-empty string.")
        if not destination_service or not isinstance(destination_service, str):
            raise ValueError("destination_service must be a non-empty string.")

        self.request_id: str          = _short_id()
        self.source_service: str      = source_service
        self.destination_service: str = destination_service
        self.payload: Any             = payload
        self.method: str              = method.upper()
        self.path: str                = path
        self.trace_id: str            = trace_id or _short_id()
        self.timestamp: datetime      = datetime.now()
        self.status: RequestStatus    = RequestStatus.PENDING
        self.response: Any            = None
        self.latency_ms: float        = 0.0
        self.retry_count: int         = 0

    def __repr__(self) -> str:
        return (f"Request(id={self.request_id}, "
                f"{self.source_service}->{self.destination_service}, "
                f"{self.method} {self.path}, "
                f"status={self.status.value})")


# ──────────────────────────────────────────────────────────────
# CircuitBreaker
# ──────────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Per-service circuit breaker.
    Trips OPEN after `failure_threshold` consecutive failures;
    after `recovery_timeout` seconds allows one HALF_OPEN probe.
    """

    def __init__(self, service_name: str,
                 failure_threshold: int = 3,
                 recovery_timeout: float = 4.0):
        self.service_name      = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self.state             = CircuitState.CLOSED
        self._failures         = 0
        self._opened_at: Optional[float] = None
        self._lock             = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if time.time() - self._opened_at >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            # HALF_OPEN: allow exactly one probe
            return True

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self.state     = CircuitState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if (self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)
                    and self._failures >= self.failure_threshold):
                self.state      = CircuitState.OPEN
                self._opened_at = time.time()

    def __repr__(self) -> str:
        return f"CircuitBreaker({self.service_name}, {self.state.value})"


# ──────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────

class Service:
    """
    A microservice node.  Handles inbound requests and publishes responses.
    """

    def __init__(self, service_id: str, name: str,
                 endpoint: str,
                 failure_rate: float = 0.0,
                 latency_range: tuple[float, float] = (0.01, 0.05),
                 log: Optional[EventLog] = None):
        if not service_id:
            raise ValueError("service_id must be non-empty.")
        if not name:
            raise ValueError("name must be non-empty.")
        if not endpoint.startswith("http"):
            raise ValueError("endpoint must start with http.")
        if not (0.0 <= failure_rate <= 1.0):
            raise ValueError("failure_rate must be 0.0–1.0.")

        self.service_id: str    = service_id
        self.name: str          = name
        self.endpoint: str      = endpoint
        self.status: ServiceStatus = ServiceStatus.UP
        self.failure_rate: float   = failure_rate
        self.latency_range         = latency_range
        self._log                  = log or EventLog()
        self._handlers: dict[str, Callable] = {}
        self._processed: int    = 0
        self._failed: int       = 0
        self._lock               = threading.Lock()

    # ── handler registration ──────────────────────────────────

    def on(self, path: str, handler: Callable[[Request], Any]) -> None:
        """Register a handler function for a URL path."""
        if not callable(handler):
            raise TypeError("handler must be callable.")
        self._handlers[path] = handler

    # ── request processing ────────────────────────────────────

    def handle(self, request: Request) -> tuple[bool, Any]:
        """
        Simulate handling an inbound request.
        Returns (success, response_payload).
        """
        if self.status == ServiceStatus.DOWN:
            self._log.log(LogLevel.ERROR, self.name,
                          f"Service DOWN – rejected REQ#{request.request_id}",
                          request.trace_id)
            with self._lock:
                self._failed += 1
            return False, {"error": "service_unavailable"}

        # Simulate latency
        latency = random.uniform(*self.latency_range)
        time.sleep(latency)
        request.latency_ms = latency * 1000

        # Simulate random failure
        if random.random() < self.failure_rate:
            self._log.log(LogLevel.WARN, self.name,
                          f"Processing error for REQ#{request.request_id} "
                          f"(simulated fault)",
                          request.trace_id)
            with self._lock:
                self._failed += 1
            return False, {"error": "internal_error"}

        # Dispatch to registered handler or default echo
        handler = self._handlers.get(request.path)
        if handler:
            response = handler(request)
        else:
            response = {"status": "ok", "echo": request.payload,
                        "served_by": self.name}

        with self._lock:
            self._processed += 1
        self._log.log(LogLevel.INFO, self.name,
                      f"Handled REQ#{request.request_id} "
                      f"{request.method} {request.path} "
                      f"latency={request.latency_ms:.1f}ms",
                      request.trace_id)
        return True, response

    # ── lifecycle ─────────────────────────────────────────────

    def go_down(self) -> None:
        self.status = ServiceStatus.DOWN
        self._log.log(LogLevel.ERROR, self.name, "Service went DOWN.")

    def come_up(self) -> None:
        self.status = ServiceStatus.UP
        self._log.log(LogLevel.INFO, self.name, "Service came back UP.")

    def set_degraded(self, failure_rate: float) -> None:
        self.status       = ServiceStatus.DEGRADED
        self.failure_rate = failure_rate
        self._log.log(LogLevel.WARN, self.name,
                      f"Service DEGRADED (failure_rate={failure_rate:.0%}).")

    # ── stats ─────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        with self._lock:
            return {"name": self.name, "status": self.status.value,
                    "processed": self._processed, "failed": self._failed,
                    "success_rate": (
                        f"{self._processed / (self._processed + self._failed):.0%}"
                        if (self._processed + self._failed) > 0 else "N/A"
                    )}

    def __repr__(self) -> str:
        return (f"Service(id={self.service_id!r}, name={self.name!r}, "
                f"status={self.status.value})")


# ──────────────────────────────────────────────────────────────
# ServiceRegistry
# ──────────────────────────────────────────────────────────────

class ServiceRegistry:
    """
    Central registry for service discovery.
    Supports registration, deregistration, health filtering, and lookup.
    """

    def __init__(self, log: EventLog):
        self._services: dict[str, Service] = {}
        self._lock = threading.Lock()
        self._log  = log

    def register(self, service: Service) -> None:
        if not isinstance(service, Service):
            raise TypeError("service must be a Service instance.")
        with self._lock:
            self._services[service.service_id] = service
        self._log.log(LogLevel.INFO, "ServiceRegistry",
                      f"Registered '{service.name}' "
                      f"at {service.endpoint}")

    def deregister(self, service_id: str) -> None:
        with self._lock:
            svc = self._services.pop(service_id, None)
        if svc:
            self._log.log(LogLevel.WARN, "ServiceRegistry",
                          f"Deregistered '{svc.name}'")

    def discover(self, name: str) -> Optional[Service]:
        """Return a healthy service by name, or None if unavailable."""
        with self._lock:
            candidates = [
                s for s in self._services.values()
                if s.name == name and s.status != ServiceStatus.DOWN
            ]
        return candidates[0] if candidates else None

    def discover_by_id(self, service_id: str) -> Optional[Service]:
        with self._lock:
            return self._services.get(service_id)

    def list_all(self) -> list[Service]:
        with self._lock:
            return list(self._services.values())

    def list_healthy(self) -> list[Service]:
        with self._lock:
            return [s for s in self._services.values()
                    if s.status == ServiceStatus.UP]

    def health_report(self) -> None:
        print("\n  Service Registry — Health Report")
        print(f"  {'Name':<24} {'ID':<12} {'Status':<10} {'Endpoint'}")
        print(f"  {'─' * 72}")
        for svc in self.list_all():
            icon = {"UP": "✅", "DOWN": "🔴",
                    "DEGRADED": "🟡", "STARTING": "🔵"}.get(svc.status.value, "❓")
            print(f"  {icon} {svc.name:<22} {svc.service_id:<12} "
                  f"{svc.status.value:<10} {svc.endpoint}")
        print()


# ──────────────────────────────────────────────────────────────
# MessageBroker  – async pub/sub + queue
# ──────────────────────────────────────────────────────────────

@dataclass
class BrokerMessage:
    message_id: str = field(default_factory=_short_id)
    topic: str      = ""
    sender: str     = ""
    payload: Any    = None
    timestamp: str  = field(default_factory=_ts)
    headers: dict   = field(default_factory=dict)


class MessageBroker:
    """
    Simulates an async message bus supporting:
      - Publish / Subscribe (fan-out to all topic subscribers)
      - Named queues (competing consumers – one consumer per message)
    """

    def __init__(self, log: EventLog):
        self._log            = log
        self._subscriptions: dict[str, list[Callable]] = defaultdict(list)
        self._queues: dict[str, deque]                  = defaultdict(deque)
        self._queue_consumers: dict[str, list[Callable]] = defaultdict(list)
        self._lock           = threading.Lock()
        self._published: int = 0
        self._consumed: int  = 0

    # ── pub/sub ───────────────────────────────────────────────

    def subscribe(self, topic: str, handler: Callable[[BrokerMessage], None],
                  subscriber_name: str = "?") -> None:
        if not callable(handler):
            raise TypeError("handler must be callable.")
        with self._lock:
            self._subscriptions[topic].append(handler)
        self._log.log(LogLevel.INFO, "MessageBroker",
                      f"'{subscriber_name}' subscribed to topic '{topic}'")

    def publish(self, topic: str, sender: str, payload: Any,
                headers: Optional[dict] = None) -> BrokerMessage:
        msg = BrokerMessage(topic=topic, sender=sender,
                            payload=payload, headers=headers or {})
        with self._lock:
            handlers = list(self._subscriptions.get(topic, []))
        self._log.log(LogLevel.EVENT, "MessageBroker",
                      f"Published MSG#{msg.message_id} on '{topic}' "
                      f"by '{sender}' -> {len(handlers)} subscriber(s)")
        self._published += 1
        for handler in handlers:
            try:
                handler(msg)
                self._consumed += 1
            except Exception as exc:
                self._log.log(LogLevel.ERROR, "MessageBroker",
                              f"Handler error on topic '{topic}': {exc}")
        return msg

    # ── queue-based ───────────────────────────────────────────

    def enqueue(self, queue_name: str, sender: str, payload: Any) -> BrokerMessage:
        msg = BrokerMessage(topic=queue_name, sender=sender, payload=payload)
        with self._lock:
            self._queues[queue_name].append(msg)
        self._log.log(LogLevel.EVENT, "MessageBroker",
                      f"Enqueued MSG#{msg.message_id} on queue '{queue_name}'")
        self._published += 1
        self._dispatch_queue(queue_name)
        return msg

    def register_queue_consumer(self, queue_name: str,
                                handler: Callable[[BrokerMessage], None],
                                consumer_name: str = "?") -> None:
        with self._lock:
            self._queue_consumers[queue_name].append(handler)
        self._log.log(LogLevel.INFO, "MessageBroker",
                      f"'{consumer_name}' consuming from queue '{queue_name}'")

    def _dispatch_queue(self, queue_name: str) -> None:
        with self._lock:
            consumers = self._queue_consumers.get(queue_name, [])
            if not consumers or not self._queues[queue_name]:
                return
            msg = self._queues[queue_name].popleft()
            # round-robin: rotate list
            consumer = consumers[0]
            self._queue_consumers[queue_name] = consumers[1:] + [consumers[0]]
        try:
            consumer(msg)
            self._consumed += 1
            self._log.log(LogLevel.INFO, "MessageBroker",
                          f"Delivered MSG#{msg.message_id} from queue '{queue_name}'")
        except Exception as exc:
            self._log.log(LogLevel.ERROR, "MessageBroker",
                          f"Queue consumer error '{queue_name}': {exc}")

    @property
    def stats(self) -> dict:
        with self._lock:
            return {"published": self._published, "consumed": self._consumed,
                    "topics": list(self._subscriptions.keys()),
                    "queues": {q: len(msgs)
                               for q, msgs in self._queues.items()}}


# ──────────────────────────────────────────────────────────────
# CommunicationManager
# ──────────────────────────────────────────────────────────────

class CommunicationManager:
    """
    Orchestrates synchronous service-to-service calls.
    Integrates service discovery, circuit breaking, retries, and logging.
    """

    MAX_RETRIES     = 2
    RETRY_DELAY     = 0.15   # seconds

    def __init__(self, registry: ServiceRegistry,
                 broker: MessageBroker,
                 log: EventLog):
        self._registry  = registry
        self._broker    = broker
        self._log       = log
        self._breakers: dict[str, CircuitBreaker] = {}
        self._call_log: list[Request]              = []
        self._lock                                 = threading.Lock()

    # ── circuit breaker access ────────────────────────────────

    def _breaker(self, service_name: str) -> CircuitBreaker:
        with self._lock:
            if service_name not in self._breakers:
                self._breakers[service_name] = CircuitBreaker(service_name)
            return self._breakers[service_name]

    # ── synchronous call ──────────────────────────────────────

    def call(self, source_name: str, dest_name: str,
             payload: Any, method: str = "GET", path: str = "/",
             trace_id: Optional[str] = None) -> Request:
        """
        Perform a synchronous call from source to dest with retries
        and circuit-breaker protection.
        """
        trace_id = trace_id or _short_id()
        breaker  = self._breaker(dest_name)

        req = Request(source_service=source_name,
                      destination_service=dest_name,
                      payload=payload, method=method,
                      path=path, trace_id=trace_id)

        self._log.log(LogLevel.INFO, source_name,
                      f"-> SYNC CALL to '{dest_name}' "
                      f"{method} {path} REQ#{req.request_id}",
                      trace_id)

        # Circuit-breaker check
        if not breaker.allow_request():
            req.status   = RequestStatus.FAILED
            req.response = {"error": "circuit_open"}
            self._log.log(LogLevel.WARN, "CommunicationManager",
                          f"Circuit OPEN for '{dest_name}' – "
                          f"REQ#{req.request_id} rejected immediately",
                          trace_id)
            with self._lock:
                self._call_log.append(req)
            return req

        # Discover service
        dest_svc = self._registry.discover(dest_name)
        if dest_svc is None:
            req.status   = RequestStatus.FAILED
            req.response = {"error": "service_not_found"}
            self._log.log(LogLevel.ERROR, "CommunicationManager",
                          f"Service '{dest_name}' not found in registry.",
                          trace_id)
            breaker.record_failure()
            with self._lock:
                self._call_log.append(req)
            return req

        # Attempt with retries
        for attempt in range(1, self.MAX_RETRIES + 2):
            success, response = dest_svc.handle(req)
            if success:
                req.status   = RequestStatus.SUCCESS
                req.response = response
                breaker.record_success()
                cb_state = self._breaker(dest_name).state.value
                self._log.log(LogLevel.INFO, "CommunicationManager",
                              f"REQ#{req.request_id} SUCCESS "
                              f"latency={req.latency_ms:.1f}ms "
                              f"circuit={cb_state}",
                              trace_id)
                break
            else:
                breaker.record_failure()
                if attempt <= self.MAX_RETRIES:
                    req.status      = RequestStatus.RETRYING
                    req.retry_count = attempt
                    self._log.log(LogLevel.WARN, "CommunicationManager",
                                  f"REQ#{req.request_id} FAILED – "
                                  f"retry {attempt}/{self.MAX_RETRIES} "
                                  f"circuit={breaker.state.value}",
                                  trace_id)
                    time.sleep(self.RETRY_DELAY)
                    # Re-check circuit after failure recording
                    if not breaker.allow_request():
                        req.status   = RequestStatus.FAILED
                        req.response = {"error": "circuit_open_after_retry"}
                        self._log.log(LogLevel.WARN, "CommunicationManager",
                                      f"Circuit OPENED mid-retry for '{dest_name}'",
                                      trace_id)
                        break
                else:
                    req.status   = RequestStatus.FAILED
                    req.response = response
                    self._log.log(LogLevel.ERROR, "CommunicationManager",
                                  f"REQ#{req.request_id} EXHAUSTED retries "
                                  f"for '{dest_name}'",
                                  trace_id)

        with self._lock:
            self._call_log.append(req)
        return req

    # ── async shortcuts ───────────────────────────────────────

    def publish(self, sender_name: str, topic: str, payload: Any,
                headers: Optional[dict] = None) -> BrokerMessage:
        return self._broker.publish(topic, sender_name, payload, headers)

    def enqueue(self, sender_name: str, queue: str, payload: Any) -> BrokerMessage:
        return self._broker.enqueue(queue, sender_name, payload)

    # ── stats ─────────────────────────────────────────────────

    def call_stats(self) -> dict:
        with self._lock:
            total   = len(self._call_log)
            success = sum(1 for r in self._call_log
                          if r.status == RequestStatus.SUCCESS)
            failed  = sum(1 for r in self._call_log
                          if r.status == RequestStatus.FAILED)
            avg_lat = (sum(r.latency_ms for r in self._call_log) / total
                       if total else 0)
        return {"total": total, "success": success,
                "failed": failed,
                "success_rate": f"{success / total:.0%}" if total else "N/A",
                "avg_latency_ms": f"{avg_lat:.1f}"}

    def circuit_report(self) -> None:
        print("\n  Circuit Breaker States:")
        with self._lock:
            breakers = dict(self._breakers)
        for name, cb in breakers.items():
            icon = {"CLOSED": "🟢", "OPEN": "🔴",
                    "HALF_OPEN": "🟡"}.get(cb.state.value, "❓")
            print(f"    {icon} {name:<24} {cb.state.value:<10} "
                  f"failures={cb._failures}")
        print()


# ──────────────────────────────────────────────────────────────
# SimulationManager  – orchestrates the whole demo
# ──────────────────────────────────────────────────────────────

class SimulationManager:
    """
    Top-level façade that wires all components together and
    provides helpers for running named simulation scenarios.
    """

    def __init__(self):
        self.log      = EventLog()
        self.registry = ServiceRegistry(self.log)
        self.broker   = MessageBroker(self.log)
        self.comms    = CommunicationManager(self.registry, self.broker, self.log)
        self._services: dict[str, Service] = {}

    # ── factory ───────────────────────────────────────────────

    def create_service(self, sid: str, name: str, endpoint: str,
                       failure_rate: float = 0.0,
                       latency_ms: tuple[float, float] = (10, 50)) -> Service:
        svc = Service(
            service_id=sid, name=name, endpoint=endpoint,
            failure_rate=failure_rate,
            latency_range=(latency_ms[0] / 1000, latency_ms[1] / 1000),
            log=self.log,
        )
        self._services[sid] = svc
        self.registry.register(svc)
        return svc

    # ── stats printout ────────────────────────────────────────

    def print_summary(self) -> None:
        sep = "=" * 68
        print(f"\n{sep}")
        print("  SIMULATION SUMMARY")
        print(sep)

        cs = self.comms.call_stats()
        print(f"  Sync calls : {cs['total']}  "
              f"success={cs['success']}  failed={cs['failed']}  "
              f"rate={cs['success_rate']}  "
              f"avg_latency={cs['avg_latency_ms']}ms")

        bs = self.broker.stats
        print(f"  Async msgs : published={bs['published']}  "
              f"consumed={bs['consumed']}")
        print(f"  Topics     : {', '.join(bs['topics']) or 'none'}")
        print(f"  Queues     : {dict(bs['queues']) or 'none'}")

        log_sum = self.log.summary()
        print(f"\n  Log counts : "
              + "  ".join(f"{k}={v}" for k, v in sorted(log_sum.items())))

        print(f"\n  Per-service stats:")
        print(f"  {'Name':<24} {'Status':<10} {'Processed':>10} "
              f"{'Failed':>8} {'Success%':>10}")
        print(f"  {'─' * 64}")
        for svc in self._services.values():
            s = svc.stats
            icon = {"UP": "✅", "DOWN": "🔴",
                    "DEGRADED": "🟡"}.get(s['status'], "❓")
            print(f"  {icon} {s['name']:<22} {s['status']:<10} "
                  f"{s['processed']:>10} {s['failed']:>8} "
                  f"{s['success_rate']:>10}")
        print(sep)


# ──────────────────────────────────────────────────────────────
# Scenario helpers
# ──────────────────────────────────────────────────────────────

def _header(title: str) -> None:
    print(f"\n{'═' * 68}")
    print(f"  {title}")
    print(f"{'═' * 68}")


def _sub(title: str) -> None:
    print(f"\n  ── {title} {'─' * (60 - len(title))}")


# ──────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────

def main() -> None:
    _header("MICROSERVICES COMMUNICATION SIMULATOR")

    # ══════════════════════════════════════════════════════════
    # SCENARIO 1 — Service discovery + happy-path sync calls
    # ══════════════════════════════════════════════════════════
    _header("SCENARIO 1 — Service Discovery & Synchronous Calls")

    sim1 = SimulationManager()

    gateway    = sim1.create_service("gw-01",  "api-gateway",
                                     "http://gateway:8080",
                                     latency_ms=(5, 15))
    user_svc   = sim1.create_service("usr-01", "user-service",
                                     "http://user-svc:8081",
                                     latency_ms=(10, 30))
    order_svc  = sim1.create_service("ord-01", "order-service",
                                     "http://order-svc:8082",
                                     latency_ms=(15, 40))
    inv_svc    = sim1.create_service("inv-01", "inventory-service",
                                     "http://inventory:8083",
                                     latency_ms=(8, 20))

    # Register handlers
    user_svc.on("/users/profile",
                lambda req: {"user_id": req.payload.get("user_id"),
                             "name": "Jane Doe", "tier": "premium"})
    order_svc.on("/orders/create",
                 lambda req: {"order_id": _short_id(),
                              "items": req.payload.get("items"),
                              "status": "created"})
    inv_svc.on("/inventory/check",
               lambda req: {"sku": req.payload.get("sku"),
                            "in_stock": True, "qty": 42})

    sim1.registry.health_report()

    trace = _short_id()
    _sub("Client -> API Gateway -> User Service")
    sim1.comms.call("api-gateway", "user-service",
                    {"user_id": "U-001"}, "GET", "/users/profile", trace)

    _sub("API Gateway -> Order Service")
    sim1.comms.call("api-gateway", "order-service",
                    {"user_id": "U-001", "items": ["SKU-A", "SKU-B"]},
                    "POST", "/orders/create", trace)

    _sub("Order Service -> Inventory Service")
    sim1.comms.call("order-service", "inventory-service",
                    {"sku": "SKU-A"}, "GET", "/inventory/check", trace)

    sim1.print_summary()

    # ══════════════════════════════════════════════════════════
    # SCENARIO 2 — Service failure + retries + circuit breaker
    # ══════════════════════════════════════════════════════════
    _header("SCENARIO 2 — Failures, Retries & Circuit Breaker")

    sim2 = SimulationManager()

    auth_svc  = sim2.create_service("auth-01", "auth-service",
                                    "http://auth:8080",
                                    failure_rate=0.0)
    pay_svc   = sim2.create_service("pay-01",  "payment-service",
                                    "http://payment:8081",
                                    failure_rate=0.75,   # very unreliable
                                    latency_ms=(20, 60))
    notif_svc = sim2.create_service("ntf-01",  "notification-service",
                                    "http://notify:8082",
                                    failure_rate=0.0)

    _sub("Auth -> Payment (high failure rate – retries expected)")
    for i in range(1, 5):
        sim2.comms.call("auth-service", "payment-service",
                        {"tx_id": f"TX-{i:03d}", "amount": 99.99},
                        "POST", "/pay")

    sim2.comms.circuit_report()

    _sub("Taking payment-service DOWN entirely")
    pay_svc.go_down()
    sim2.comms.call("auth-service", "payment-service",
                    {"tx_id": "TX-005"}, "POST", "/pay")

    _sub("Payment service comes back UP")
    pay_svc.come_up()
    pay_svc.failure_rate = 0.0
    time.sleep(4.5)   # wait for circuit recovery timeout
    sim2.comms.call("auth-service", "payment-service",
                    {"tx_id": "TX-006"}, "POST", "/pay")

    sim2.comms.circuit_report()
    sim2.print_summary()

    # ══════════════════════════════════════════════════════════
    # SCENARIO 3 — Async pub/sub via MessageBroker
    # ══════════════════════════════════════════════════════════
    _header("SCENARIO 3 — Asynchronous Pub/Sub Messaging")

    sim3 = SimulationManager()

    catalog_svc  = sim3.create_service("cat-01", "catalog-service",
                                       "http://catalog:8080")
    search_svc   = sim3.create_service("srch-01", "search-service",
                                       "http://search:8081")
    rec_svc      = sim3.create_service("rec-01",  "recommendation-service",
                                       "http://recs:8082")
    analytics    = sim3.create_service("ana-01",  "analytics-service",
                                       "http://analytics:8083")

    received: list[str] = []

    # Subscribers
    def on_product_update(msg: BrokerMessage) -> None:
        sim3.log.log(LogLevel.EVENT, "search-service",
                     f"Indexing product update: {msg.payload}")
        received.append(f"search:{msg.message_id}")

    def on_product_update_recs(msg: BrokerMessage) -> None:
        sim3.log.log(LogLevel.EVENT, "recommendation-service",
                     f"Refreshing recs for: {msg.payload.get('product_id')}")
        received.append(f"recs:{msg.message_id}")

    def on_any_event(msg: BrokerMessage) -> None:
        sim3.log.log(LogLevel.DEBUG, "analytics-service",
                     f"Analytics received '{msg.topic}': {msg.payload}")

    sim3.broker.subscribe("product.updated", on_product_update,
                          "search-service")
    sim3.broker.subscribe("product.updated", on_product_update_recs,
                          "recommendation-service")
    sim3.broker.subscribe("product.updated", on_any_event,
                          "analytics-service")
    sim3.broker.subscribe("order.placed",    on_any_event,
                          "analytics-service")

    _sub("Catalog publishes product.updated (fan-out to 3 subscribers)")
    sim3.comms.publish("catalog-service", "product.updated",
                       {"product_id": "P-999", "price": 49.99,
                        "title": "Wireless Headphones"})

    _sub("Order service publishes order.placed")
    sim3.comms.publish("order-service", "order.placed",
                       {"order_id": "ORD-777", "user_id": "U-001",
                        "total": 149.98})

    print(f"\n  Total async deliveries received: {len(received)}")
    sim3.print_summary()

    # ══════════════════════════════════════════════════════════
    # SCENARIO 4 — Queue-based competing consumers
    # ══════════════════════════════════════════════════════════
    _header("SCENARIO 4 — Queue-Based Competing Consumers")

    sim4 = SimulationManager()

    email_A  = sim4.create_service("em-A", "email-worker-A",
                                   "http://email-a:8080")
    email_B  = sim4.create_service("em-B", "email-worker-B",
                                   "http://email-b:8081")
    api      = sim4.create_service("api",  "api-gateway",
                                   "http://api:8080")

    handled: list[str] = []

    def worker_a(msg: BrokerMessage) -> None:
        sim4.log.log(LogLevel.INFO, "email-worker-A",
                     f"Sending email to {msg.payload.get('to')}")
        handled.append(f"A:{msg.message_id}")

    def worker_b(msg: BrokerMessage) -> None:
        sim4.log.log(LogLevel.INFO, "email-worker-B",
                     f"Sending email to {msg.payload.get('to')}")
        handled.append(f"B:{msg.message_id}")

    sim4.broker.register_queue_consumer("email.queue", worker_a, "email-worker-A")
    sim4.broker.register_queue_consumer("email.queue", worker_b, "email-worker-B")

    _sub("Enqueueing 6 email tasks (round-robined between A and B)")
    recipients = ["alice@x.com", "bob@x.com", "carol@x.com",
                  "dave@x.com", "eve@x.com", "frank@x.com"]
    for r in recipients:
        sim4.comms.enqueue("api-gateway", "email.queue",
                           {"to": r, "subject": "Your order confirmation"})

    print(f"\n  Messages handled by worker-A: "
          f"{sum(1 for h in handled if h.startswith('A'))}")
    print(f"  Messages handled by worker-B: "
          f"{sum(1 for h in handled if h.startswith('B'))}")
    sim4.print_summary()

    # ══════════════════════════════════════════════════════════
    # SCENARIO 5 — Full microservices e-commerce flow
    # ══════════════════════════════════════════════════════════
    _header("SCENARIO 5 — Full E-Commerce Request Flow")

    sim5 = SimulationManager()

    gw       = sim5.create_service("gw",   "api-gateway",
                                   "http://gateway:8080",  latency_ms=(2, 8))
    auth     = sim5.create_service("auth", "auth-service",
                                   "http://auth:8081",     latency_ms=(5, 15))
    users    = sim5.create_service("usr",  "user-service",
                                   "http://users:8082",    latency_ms=(8, 20))
    products = sim5.create_service("prd",  "product-service",
                                   "http://products:8083", latency_ms=(6, 18))
    basket   = sim5.create_service("bkt",  "basket-service",
                                   "http://basket:8084",   latency_ms=(4, 12))
    orders   = sim5.create_service("ord",  "order-service",
                                   "http://orders:8085",   latency_ms=(10, 25),
                                   failure_rate=0.2)
    payment  = sim5.create_service("pay",  "payment-service",
                                   "http://payment:8086",  latency_ms=(20, 60))
    shipping = sim5.create_service("shp",  "shipping-service",
                                   "http://shipping:8087", latency_ms=(5, 15))
    notify   = sim5.create_service("ntf",  "notification-service",
                                   "http://notify:8088",   latency_ms=(3, 8))

    # Wire up async listeners
    def on_order_confirmed(msg: BrokerMessage) -> None:
        sim5.log.log(LogLevel.EVENT, "shipping-service",
                     f"Scheduling shipment for order {msg.payload.get('order_id')}")

    def on_order_confirmed_notify(msg: BrokerMessage) -> None:
        sim5.log.log(LogLevel.EVENT, "notification-service",
                     f"Sending order confirmation email for "
                     f"order {msg.payload.get('order_id')}")

    sim5.broker.subscribe("order.confirmed", on_order_confirmed,
                          "shipping-service")
    sim5.broker.subscribe("order.confirmed", on_order_confirmed_notify,
                          "notification-service")

    sim5.registry.health_report()

    trace = _short_id()
    _sub("Step 1 — Authenticate user")
    r1 = sim5.comms.call("api-gateway", "auth-service",
                         {"token": "Bearer eyJhb..."}, "POST", "/auth/verify",
                         trace)

    _sub("Step 2 — Fetch user profile")
    r2 = sim5.comms.call("api-gateway", "user-service",
                         {"user_id": "U-042"}, "GET", "/users/U-042", trace)

    _sub("Step 3 — Browse product catalogue")
    for sku in ["SKU-101", "SKU-202", "SKU-303"]:
        sim5.comms.call("api-gateway", "product-service",
                        {"sku": sku}, "GET", f"/products/{sku}", trace)

    _sub("Step 4 — Add items to basket")
    sim5.comms.call("api-gateway", "basket-service",
                    {"user_id": "U-042",
                     "items": [{"sku": "SKU-101", "qty": 2},
                               {"sku": "SKU-202", "qty": 1}]},
                    "POST", "/basket/add", trace)

    _sub("Step 5 — Place order (may need retry)")
    sim5.comms.call("api-gateway", "order-service",
                    {"user_id": "U-042",
                     "items": [{"sku": "SKU-101", "qty": 2},
                               {"sku": "SKU-202", "qty": 1}],
                     "total": 189.97},
                    "POST", "/orders/create", trace)

    _sub("Step 6 — Process payment")
    sim5.comms.call("order-service", "payment-service",
                    {"user_id": "U-042", "amount": 189.97,
                     "card_last4": "4242"},
                    "POST", "/payments/charge", trace)

    _sub("Step 7 — Publish order.confirmed (async fan-out)")
    sim5.comms.publish("order-service", "order.confirmed",
                       {"order_id": _short_id(), "user_id": "U-042",
                        "total": 189.97},
                       headers={"trace_id": trace})

    sim5.comms.circuit_report()
    sim5.print_summary()

    _header("All scenarios complete.")


if __name__ == "__main__":
    main()