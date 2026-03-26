"""
distributed_task_queue.py
=========================
A fully simulated distributed task queue with concurrent workers,
retry logic, a message broker, and a rich console dashboard.

Architecture
------------
  Producer  ──►  Broker  ──►  TaskQueue  ──►  Worker(s)
                                 ▲                │
                             QueueManager ◄───────┘
                             (monitor / retry / report)

No third-party dependencies — uses only the Python standard library.
"""

from __future__ import annotations

import inspect
import math
import random
import threading
import time
import traceback
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# Enumerations
# ═══════════════════════════════════════════════════════════════

class TaskStatus(Enum):
    PENDING   = auto()
    QUEUED    = auto()
    RUNNING   = auto()
    COMPLETED = auto()
    FAILED    = auto()
    RETRYING  = auto()


class WorkerState(Enum):
    IDLE    = auto()
    BUSY    = auto()
    STOPPED = auto()


# ═══════════════════════════════════════════════════════════════
# Task
# ═══════════════════════════════════════════════════════════════

@dataclass
class Task:
    """
    Represents a unit of work to be executed by a Worker.

    Parameters
    ----------
    function    : callable to run
    args        : positional arguments
    kwargs      : keyword arguments
    name        : human-readable label (auto-derived if omitted)
    max_retries : how many times to retry on failure
    priority    : lower = higher priority (1 is highest)
    """
    function:    Callable
    args:        Tuple      = field(default_factory=tuple)
    kwargs:      Dict       = field(default_factory=dict)
    name:        str        = ""
    max_retries: int        = 2
    priority:    int        = 5

    # ── set by the system ──────────────────────────────────────
    task_id:     str           = field(default_factory=lambda: uuid.uuid4().hex[:8])
    status:      TaskStatus    = field(default=TaskStatus.PENDING)
    result:      Any           = field(default=None)
    error:       str           = field(default="")
    attempt:     int           = field(default=0)
    created_at:  datetime      = field(default_factory=datetime.now)
    started_at:  Optional[datetime] = field(default=None)
    finished_at: Optional[datetime] = field(default=None)
    worker_id:   str           = field(default="")

    def __post_init__(self) -> None:
        if not callable(self.function):
            raise TypeError("Task.function must be callable.")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0.")
        if not (1 <= self.priority <= 10):
            raise ValueError("priority must be between 1 and 10.")
        if not self.name:
            self.name = getattr(self.function, "__name__", "task")

    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at and self.finished_at:
            delta = self.finished_at - self.started_at
            return round(delta.total_seconds() * 1000, 1)
        return None

    @property
    def retries_left(self) -> int:
        return max(0, self.max_retries - self.attempt)

    def __lt__(self, other: "Task") -> bool:
        """Enable priority-queue ordering (lower priority value = first)."""
        return self.priority < other.priority


# ═══════════════════════════════════════════════════════════════
# TaskQueue  (thread-safe priority queue)
# ═══════════════════════════════════════════════════════════════

class TaskQueue:
    """
    Thread-safe queue that stores pending tasks ordered by priority.
    """

    def __init__(self, maxsize: int = 0) -> None:
        self._lock      = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._tasks:    List[Task] = []
        self._maxsize   = maxsize  # 0 = unlimited

    # ── producers ─────────────────────────────────────────────

    def put(self, task: Task, block: bool = True, timeout: float = None) -> bool:
        """Enqueue a task.  Returns False if queue is full and block=False."""
        with self._not_empty:
            if self._maxsize > 0:
                deadline = (time.monotonic() + timeout) if timeout else None
                while len(self._tasks) >= self._maxsize:
                    if not block:
                        return False
                    remaining = (deadline - time.monotonic()) if deadline else None
                    if remaining is not None and remaining <= 0:
                        return False
                    self._not_empty.wait(timeout=remaining)
            task.status = TaskStatus.QUEUED
            self._tasks.append(task)
            self._tasks.sort()          # maintain priority order
            self._not_empty.notify_all()
        return True

    # ── consumers ─────────────────────────────────────────────

    def get(self, block: bool = True, timeout: float = None) -> Optional[Task]:
        """Dequeue the highest-priority task."""
        with self._not_empty:
            deadline = (time.monotonic() + timeout) if timeout else None
            while not self._tasks:
                if not block:
                    return None
                remaining = (deadline - time.monotonic()) if deadline else None
                if remaining is not None and remaining <= 0:
                    return None
                self._not_empty.wait(timeout=remaining)
            return self._tasks.pop(0)

    # ── inspection ────────────────────────────────────────────

    def __len__(self) -> int:
        with self._lock:
            return len(self._tasks)

    @property
    def empty(self) -> bool:
        return len(self) == 0

    def snapshot(self) -> List[Task]:
        with self._lock:
            return list(self._tasks)


# ═══════════════════════════════════════════════════════════════
# Worker
# ═══════════════════════════════════════════════════════════════

class Worker(threading.Thread):
    """
    Pulls tasks from a shared queue and executes them in its own thread.
    Reports results back to a callback provided by QueueManager.
    """

    def __init__(
        self,
        worker_id: str,
        queue: TaskQueue,
        result_cb: Callable[[Task], None],
        poll_interval: float = 0.1,
    ) -> None:
        super().__init__(daemon=True, name=f"Worker-{worker_id}")
        self.worker_id      = worker_id
        self._queue         = queue
        self._result_cb     = result_cb
        self._poll_interval = poll_interval
        self._state         = WorkerState.IDLE
        self._stop_event    = threading.Event()
        self._current_task: Optional[Task] = None
        self._tasks_done    = 0
        self._tasks_failed  = 0
        self._state_lock    = threading.Lock()

    # ── properties ────────────────────────────────────────────

    @property
    def state(self) -> WorkerState:
        with self._state_lock:
            return self._state

    @property
    def current_task(self) -> Optional[Task]:
        with self._state_lock:
            return self._current_task

    @property
    def is_idle(self) -> bool:
        return self.state == WorkerState.IDLE

    # ── lifecycle ─────────────────────────────────────────────

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            task = self._queue.get(block=True, timeout=self._poll_interval)
            if task is None:
                continue
            self._execute(task)

        with self._state_lock:
            self._state = WorkerState.STOPPED

    # ── execution ─────────────────────────────────────────────

    def _execute(self, task: Task) -> None:
        with self._state_lock:
            self._state        = WorkerState.BUSY
            self._current_task = task

        task.status     = TaskStatus.RUNNING
        task.worker_id  = self.worker_id
        task.started_at = datetime.now()
        task.attempt   += 1

        try:
            task.result     = task.function(*task.args, **task.kwargs)
            task.status     = TaskStatus.COMPLETED
            self._tasks_done += 1
        except Exception as exc:
            task.error       = f"{type(exc).__name__}: {exc}"
            task.status      = TaskStatus.FAILED
            self._tasks_failed += 1
        finally:
            task.finished_at = datetime.now()

        with self._state_lock:
            self._state        = WorkerState.IDLE
            self._current_task = None

        self._result_cb(task)

    # ── stats ─────────────────────────────────────────────────

    def stats(self) -> Dict:
        return {
            "worker_id":    self.worker_id,
            "state":        self.state.name,
            "tasks_done":   self._tasks_done,
            "tasks_failed": self._tasks_failed,
            "current_task": (self._current_task.task_id
                             if self._current_task else None),
        }


# ═══════════════════════════════════════════════════════════════
# Broker  (message-passing simulation)
# ═══════════════════════════════════════════════════════════════

class Broker:
    """
    Simulates a message broker (think Redis / RabbitMQ in miniature).
    Producers publish tasks; the Broker routes them into the TaskQueue.
    Also maintains a dead-letter deque for tasks that exhausted retries.
    """

    def __init__(self, queue: TaskQueue) -> None:
        self._queue      = queue
        self._lock       = threading.Lock()
        self._published  = 0
        self._dead_letter: Deque[Task] = deque(maxlen=200)

    def publish(self, task: Task) -> bool:
        """Route a task into the queue.  Returns False if queue is full."""
        ok = self._queue.put(task, block=False)
        if ok:
            with self._lock:
                self._published += 1
        return ok

    def dead_letter(self, task: Task) -> None:
        """Move an exhausted task to the dead-letter store."""
        with self._lock:
            self._dead_letter.append(task)

    def dead_letter_snapshot(self) -> List[Task]:
        with self._lock:
            return list(self._dead_letter)

    @property
    def published_count(self) -> int:
        with self._lock:
            return self._published


# ═══════════════════════════════════════════════════════════════
# QueueManager
# ═══════════════════════════════════════════════════════════════

class QueueManager:
    """
    Central orchestrator.

    Responsibilities
    ----------------
    • Spawn / stop Workers
    • Route task results (retry on failure, dead-letter if exhausted)
    • Track all tasks by ID
    • Expose a monitoring snapshot
    """

    def __init__(
        self,
        num_workers:     int   = 3,
        queue_maxsize:   int   = 0,
        retry_delay:     float = 0.5,
    ) -> None:
        if num_workers < 1:
            raise ValueError("num_workers must be >= 1.")
        self._queue        = TaskQueue(maxsize=queue_maxsize)
        self._broker       = Broker(self._queue)
        self._retry_delay  = retry_delay
        self._tasks:       Dict[str, Task] = {}
        self._lock         = threading.Lock()
        self._workers:     List[Worker] = []
        self._stats        = defaultdict(int)   # counters

        for i in range(num_workers):
            w = Worker(
                worker_id=f"W{i+1:02d}",
                queue=self._queue,
                result_cb=self._on_result,
            )
            self._workers.append(w)
            w.start()

    # ── public API ────────────────────────────────────────────

    def submit(self, task: Task) -> str:
        """Submit a task for execution. Returns task_id."""
        with self._lock:
            self._tasks[task.task_id] = task
            self._stats["submitted"] += 1
        if not self._broker.publish(task):
            raise RuntimeError("Task queue is full — try again later.")
        return task.task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def cancel_pending(self, task_id: str) -> bool:
        """Remove a QUEUED task before it runs. Returns True if cancelled."""
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None or task.status != TaskStatus.QUEUED:
            return False
        with self._queue._lock:
            try:
                self._queue._tasks.remove(task)
                task.status = TaskStatus.FAILED
                task.error  = "Cancelled by user."
                return True
            except ValueError:
                return False

    def shutdown(self, wait: bool = True) -> None:
        """Stop all workers gracefully."""
        for w in self._workers:
            w.stop()
        if wait:
            for w in self._workers:
                w.join(timeout=5)

    # ── monitoring ────────────────────────────────────────────

    def snapshot(self) -> Dict:
        with self._lock:
            tasks = list(self._tasks.values())
        by_status = defaultdict(list)
        for t in tasks:
            by_status[t.status].append(t)
        return {
            "queue_depth":  len(self._queue),
            "workers":      [w.stats() for w in self._workers],
            "tasks":        tasks,
            "by_status":    dict(by_status),
            "dead_letters": self._broker.dead_letter_snapshot(),
            "stats":        dict(self._stats),
        }

    # ── internal callback ─────────────────────────────────────

    def _on_result(self, task: Task) -> None:
        with self._lock:
            if task.status == TaskStatus.COMPLETED:
                self._stats["completed"] += 1
            elif task.status == TaskStatus.FAILED:
                if task.retries_left > 0:
                    self._schedule_retry(task)
                else:
                    self._stats["dead_lettered"] += 1
                    task.status = TaskStatus.FAILED
                    self._broker.dead_letter(task)

    def _schedule_retry(self, task: Task) -> None:
        task.status = TaskStatus.RETRYING

        def _retry() -> None:
            time.sleep(self._retry_delay)
            task.status = TaskStatus.PENDING
            self._broker.publish(task)

        threading.Thread(target=_retry, daemon=True).start()


# ═══════════════════════════════════════════════════════════════
# Built-in demo task functions
# ═══════════════════════════════════════════════════════════════

def task_add(a: float, b: float) -> float:
    time.sleep(random.uniform(0.2, 0.8))
    return a + b

def task_multiply(a: float, b: float) -> float:
    time.sleep(random.uniform(0.1, 0.5))
    return a * b

def task_factorial(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative.")
    time.sleep(random.uniform(0.3, 0.7))
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def task_sqrt(x: float) -> float:
    if x < 0:
        raise ValueError("Cannot take sqrt of a negative number.")
    time.sleep(random.uniform(0.1, 0.4))
    return math.sqrt(x)

def task_sleep(seconds: float) -> str:
    time.sleep(max(0.1, seconds))
    return f"Slept {seconds}s"

def task_random_fail(p: float = 0.5) -> str:
    """Fails with probability p — useful for testing retry logic."""
    time.sleep(random.uniform(0.1, 0.3))
    if random.random() < p:
        raise RuntimeError("Random failure triggered!")
    return "Success"

def task_fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative.")
    time.sleep(random.uniform(0.2, 0.6))
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

DEMO_TASKS: List[Callable] = [
    task_add, task_multiply, task_factorial,
    task_sqrt, task_sleep, task_random_fail, task_fibonacci,
]


# ═══════════════════════════════════════════════════════════════
# Console UI helpers
# ═══════════════════════════════════════════════════════════════

COLORS = {
    "reset":  "\033[0m",
    "bold":   "\033[1m",
    "green":  "\033[32m",
    "yellow": "\033[33m",
    "red":    "\033[31m",
    "cyan":   "\033[36m",
    "grey":   "\033[90m",
    "blue":   "\033[34m",
    "magenta":"\033[35m",
}

STATUS_COLOR = {
    TaskStatus.PENDING:   COLORS["grey"],
    TaskStatus.QUEUED:    COLORS["blue"],
    TaskStatus.RUNNING:   COLORS["yellow"],
    TaskStatus.COMPLETED: COLORS["green"],
    TaskStatus.FAILED:    COLORS["red"],
    TaskStatus.RETRYING:  COLORS["magenta"],
}

WORKER_COLOR = {
    WorkerState.IDLE:    COLORS["green"],
    WorkerState.BUSY:    COLORS["yellow"],
    WorkerState.STOPPED: COLORS["red"],
}


def c(text: str, color: str) -> str:
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def _fmt_status(status: TaskStatus) -> str:
    col = STATUS_COLOR.get(status, "")
    return f"{col}{status.name:<10}{COLORS['reset']}"


def _fmt_result(task: Task) -> str:
    if task.status == TaskStatus.COMPLETED:
        return c(str(task.result), "green")
    if task.status in (TaskStatus.FAILED, TaskStatus.RETRYING):
        return c(task.error or "—", "red")
    return c("—", "grey")


def _hr(width: int = 60, ch: str = "─") -> str:
    return ch * width


def _center(text: str, width: int = 60) -> str:
    return text.center(width)


def _prompt(msg: str, default=None, cast=str, validator=None):
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"  {msg}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            value = cast(raw)
        except (ValueError, TypeError):
            print(c(f"  ✗ Expected {cast.__name__}.", "red"))
            continue
        if validator and not validator(value):
            print(c("  ✗ Value out of allowed range.", "red"))
            continue
        return value


# ═══════════════════════════════════════════════════════════════
# Display routines
# ═══════════════════════════════════════════════════════════════

def display_workers(manager: QueueManager) -> None:
    snap = manager.snapshot()
    print(f"\n  {c('Workers', 'bold')}")
    print("  " + _hr(62))
    hdr = f"  {'ID':<8} {'State':<10} {'Done':>5} {'Failed':>7}  Current Task"
    print(c(hdr, "grey"))
    print("  " + _hr(62))
    for w in snap["workers"]:
        state_str = WorkerState[w["state"]]
        col = WORKER_COLOR.get(state_str, "")
        state_disp = f"{col}{w['state']:<10}{COLORS['reset']}"
        cur = w["current_task"] or "—"
        print(f"  {w['worker_id']:<8} {state_disp} {w['tasks_done']:>5} "
              f"{w['tasks_failed']:>7}  {cur}")
    qd = snap["queue_depth"]
    print(f"\n  Queue depth: {c(str(qd), 'cyan')}")


def display_tasks(manager: QueueManager, limit: int = 20) -> None:
    snap = manager.snapshot()
    tasks = sorted(snap["tasks"], key=lambda t: t.created_at, reverse=True)
    print(f"\n  {c('Recent Tasks', 'bold')} (latest {limit})")
    print("  " + _hr(80))
    hdr = (f"  {'ID':<10} {'Name':<16} {'Status':<12} {'Worker':<8} "
           f"{'ms':>7}  Result / Error")
    print(c(hdr, "grey"))
    print("  " + _hr(80))
    for task in tasks[:limit]:
        dur = f"{task.duration_ms}" if task.duration_ms is not None else "—"
        res = _fmt_result(task)
        print(f"  {task.task_id:<10} {task.name:<16} {_fmt_status(task.status)} "
              f"{task.worker_id or '—':<8} {dur:>7}  {res}")
    if not tasks:
        print(c("  (no tasks yet)", "grey"))


def display_stats(manager: QueueManager) -> None:
    snap = manager.snapshot()
    st   = snap["stats"]
    dl   = snap["dead_letters"]
    by_s = snap["by_status"]
    print(f"\n  {c('Statistics', 'bold')}")
    print("  " + _hr(42))
    for label, key in [
        ("Submitted",    "submitted"),
        ("Completed",    "completed"),
        ("Dead-lettered","dead_lettered"),
    ]:
        val = st.get(key, 0)
        col = "green" if key == "completed" else ("red" if val else "grey")
        print(f"  {label:<20} {c(str(val), col)}")
    running  = len(by_s.get(TaskStatus.RUNNING,  []))
    retrying = len(by_s.get(TaskStatus.RETRYING, []))
    queued   = len(by_s.get(TaskStatus.QUEUED,   []))
    print(f"  {'In flight':<20} {c(str(running), 'yellow')}")
    print(f"  {'Retrying':<20} {c(str(retrying), 'magenta')}")
    print(f"  {'Queued':<20} {c(str(queued), 'blue')}")
    if dl:
        print(f"\n  {c('Dead-letter queue', 'red')} ({len(dl)} tasks)")
        for t in dl[-5:]:
            print(f"    {t.task_id}  {t.name:<16}  {c(t.error, 'red')}")


def display_task_detail(manager: QueueManager, task_id: str) -> None:
    task = manager.get_task(task_id)
    if task is None:
        print(c(f"  Task '{task_id}' not found.", "red"))
        return
    print(f"\n  {c('Task Detail', 'bold')}")
    print("  " + _hr(50))
    fields = [
        ("ID",          task.task_id),
        ("Name",        task.name),
        ("Status",      task.status.name),
        ("Worker",      task.worker_id or "—"),
        ("Attempt",     f"{task.attempt} / {task.max_retries + 1}"),
        ("Priority",    task.priority),
        ("Created",     task.created_at.strftime("%H:%M:%S.%f")[:-3]),
        ("Started",     task.started_at.strftime("%H:%M:%S.%f")[:-3]
                        if task.started_at else "—"),
        ("Finished",    task.finished_at.strftime("%H:%M:%S.%f")[:-3]
                        if task.finished_at else "—"),
        ("Duration",    f"{task.duration_ms} ms" if task.duration_ms else "—"),
        ("Result",      str(task.result) if task.result is not None else "—"),
        ("Error",       task.error or "—"),
    ]
    for label, val in fields:
        print(f"  {label:<14} {val}")


# ═══════════════════════════════════════════════════════════════
# Submit helpers (interactive)
# ═══════════════════════════════════════════════════════════════

TASK_REGISTRY: Dict[str, Tuple[Callable, str, List]] = {
    "1": (task_add,         "Add(a, b)",          ["a (float)", "b (float)"]),
    "2": (task_multiply,    "Multiply(a, b)",      ["a (float)", "b (float)"]),
    "3": (task_factorial,   "Factorial(n)",        ["n (int, 0-15)"]),
    "4": (task_sqrt,        "Sqrt(x)",             ["x (float >= 0)"]),
    "5": (task_sleep,       "Sleep(seconds)",      ["seconds (0.1-5)"]),
    "6": (task_random_fail, "RandomFail(p)",       ["fail probability (0-1)"]),
    "7": (task_fibonacci,   "Fibonacci(n)",        ["n (int, 0-30)"]),
}

TASK_VALIDATORS: Dict[str, Callable] = {
    "1": lambda a, b: (float(a), float(b)),
    "2": lambda a, b: (float(a), float(b)),
    "3": lambda n: (int(n),) if 0 <= int(n) <= 15 else (_ for _ in ()).throw(
         ValueError("n must be 0-15")),
    "4": lambda x: (float(x),) if float(x) >= 0 else (_ for _ in ()).throw(
         ValueError("x must be >= 0")),
    "5": lambda s: (float(s),) if 0.1 <= float(s) <= 5 else (_ for _ in ()).throw(
         ValueError("seconds must be 0.1-5")),
    "6": lambda p: (float(p),) if 0 <= float(p) <= 1 else (_ for _ in ()).throw(
         ValueError("p must be 0-1")),
    "7": lambda n: (int(n),) if 0 <= int(n) <= 30 else (_ for _ in ()).throw(
         ValueError("n must be 0-30")),
}


def _collect_args(key: str) -> Optional[Tuple]:
    _, label, param_hints = TASK_REGISTRY[key]
    args = []
    for hint in param_hints:
        raw = input(f"    {hint}: ").strip()
        args.append(raw)
    try:
        validator = TASK_VALIDATORS[key]
        return validator(*args)
    except (ValueError, TypeError) as exc:
        print(c(f"  ✗ {exc}", "red"))
        return None


def submit_task_interactive(manager: QueueManager) -> None:
    print(f"\n  {c('Submit a Task', 'bold')}")
    print("  " + _hr(40))
    for k, (_, label, _) in TASK_REGISTRY.items():
        print(f"  {k}. {label}")
    print("  0. Back")
    print()
    choice = input("  Choose task type: ").strip()
    if choice == "0" or choice not in TASK_REGISTRY:
        return

    args = _collect_args(choice)
    if args is None:
        return

    priority = _prompt("Priority (1=high … 10=low)", default=5, cast=int,
                       validator=lambda v: 1 <= v <= 10)
    retries  = _prompt("Max retries", default=2, cast=int,
                       validator=lambda v: 0 <= v <= 5)

    fn, label, _ = TASK_REGISTRY[choice]
    task = Task(function=fn, args=args, priority=priority, max_retries=retries)
    tid  = manager.submit(task)
    print(c(f"  ✓ Task submitted: {tid}", "green"))


def submit_bulk_demo(manager: QueueManager, n: int = 12) -> None:
    """Submit a random mix of demo tasks for showcase purposes."""
    configs = [
        (task_add,         (random.uniform(1, 100), random.uniform(1, 100))),
        (task_multiply,    (random.uniform(1, 20),  random.uniform(1, 20))),
        (task_factorial,   (random.randint(0, 12),)),
        (task_sqrt,        (random.uniform(0, 200),)),
        (task_sleep,       (random.uniform(0.1, 1.5),)),
        (task_random_fail, (0.4,)),
        (task_fibonacci,   (random.randint(5, 25),)),
    ]
    submitted = []
    for _ in range(n):
        fn, args = random.choice(configs)
        task = Task(
            function=fn,
            args=args,
            priority=random.randint(1, 10),
            max_retries=random.choice([0, 1, 2]),
        )
        tid = manager.submit(task)
        submitted.append(tid)
    print(c(f"  ✓ {n} demo tasks submitted.", "green"))
    return submitted


# ═══════════════════════════════════════════════════════════════
# Live monitor
# ═══════════════════════════════════════════════════════════════

def live_monitor(manager: QueueManager, duration: float = 8.0,
                 refresh: float = 1.0) -> None:
    """Print a refreshing status snapshot for `duration` seconds."""
    print(c(f"\n  Live monitor ({duration}s) — press Ctrl+C to stop\n", "cyan"))
    start = time.monotonic()
    try:
        while time.monotonic() - start < duration:
            snap = manager.snapshot()
            by_s = snap["by_status"]
            parts = []
            for st, col in [
                (TaskStatus.QUEUED,    "blue"),
                (TaskStatus.RUNNING,   "yellow"),
                (TaskStatus.RETRYING,  "magenta"),
                (TaskStatus.COMPLETED, "green"),
                (TaskStatus.FAILED,    "red"),
            ]:
                cnt = len(by_s.get(st, []))
                parts.append(c(f"{st.name}: {cnt}", col))
            line = "  " + "  │  ".join(parts)
            print(f"\r{line}   ", end="", flush=True)
            time.sleep(refresh)
    except KeyboardInterrupt:
        pass
    print()  # newline after monitor exits


# ═══════════════════════════════════════════════════════════════
# Main menu
# ═══════════════════════════════════════════════════════════════

BANNER = r"""
  ╔══════════════════════════════════════════════════════╗
  ║       Distributed Task Queue Simulator  v1.0        ║
  ╚══════════════════════════════════════════════════════╝
"""

MENU = """
  ┌─ Menu ────────────────────────────────────────────┐
  │  1  Submit a task (interactive)                   │
  │  2  Submit bulk demo tasks (12 random tasks)      │
  │  3  View workers status                           │
  │  4  View task list                                │
  │  5  View statistics                               │
  │  6  Task detail (by ID)                           │
  │  7  Cancel a queued task                          │
  │  8  Live monitor (8 s refresh)                    │
  │  9  Exit                                          │
  └───────────────────────────────────────────────────┘"""


def _setup_manager() -> QueueManager:
    print(BANNER)
    print("  Configure the queue manager:\n")
    workers = _prompt("Number of workers", default=3, cast=int,
                      validator=lambda v: 1 <= v <= 10)
    manager = QueueManager(num_workers=workers, retry_delay=0.3)
    print(c(f"  ✓ Queue manager started with {workers} workers.\n", "green"))
    return manager


def main() -> None:
    manager = _setup_manager()

    while True:
        print(MENU)
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            submit_task_interactive(manager)

        elif choice == "2":
            submit_bulk_demo(manager, n=12)

        elif choice == "3":
            display_workers(manager)

        elif choice == "4":
            limit = _prompt("Max rows to display", default=20, cast=int,
                            validator=lambda v: 1 <= v <= 200)
            display_tasks(manager, limit=limit)

        elif choice == "5":
            display_stats(manager)

        elif choice == "6":
            tid = input("  Task ID: ").strip()
            display_task_detail(manager, tid)

        elif choice == "7":
            tid = input("  Task ID to cancel: ").strip()
            ok  = manager.cancel_pending(tid)
            if ok:
                print(c(f"  ✓ Task {tid} cancelled.", "green"))
            else:
                print(c("  ✗ Cannot cancel — task not found or not QUEUED.", "red"))

        elif choice == "8":
            live_monitor(manager, duration=8.0, refresh=0.8)

        elif choice == "9":
            print("\n  Shutting down workers …")
            manager.shutdown(wait=False)
            print(c("  Goodbye!\n", "green"))
            break

        else:
            print(c("  ✗ Unknown option. Enter 1–9.", "red"))


if __name__ == "__main__":
    main()