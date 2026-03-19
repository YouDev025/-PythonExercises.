"""
Thread Pool Implementation
==========================
A Python OOP implementation of a thread pool system for managing
and executing concurrent tasks efficiently.
"""

import threading
import queue
import time
import uuid
import logging
import random
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass, field


# ──────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-16s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# TaskStatus Enum
# ──────────────────────────────────────────────
class TaskStatus(Enum):
    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"
    CANCELLED = "CANCELLED"


# ──────────────────────────────────────────────
# Task
# ──────────────────────────────────────────────
@dataclass
class Task:
    """Represents a single unit of work to be executed by the thread pool."""

    function:  Callable
    args:      tuple        = field(default_factory=tuple)
    kwargs:    dict         = field(default_factory=dict)
    task_id:   str          = field(default_factory=lambda: str(uuid.uuid4())[:8])
    priority:  int          = 0          # lower number → higher priority
    status:    TaskStatus   = field(default=TaskStatus.PENDING, init=False)
    result:    Any          = field(default=None,  init=False)
    error:     Optional[Exception] = field(default=None, init=False)
    submitted_at: float     = field(default_factory=time.time, init=False)
    started_at:   Optional[float] = field(default=None, init=False)
    finished_at:  Optional[float] = field(default=None, init=False)

    # threading.Event lets callers block until the task finishes
    _done_event: threading.Event = field(default_factory=threading.Event, init=False, repr=False)

    # Allow priority queue ordering  (lower priority value = higher priority)
    def __lt__(self, other: "Task") -> bool:
        return self.priority < other.priority

    # ── public helpers ──────────────────────────────────────────────────────
    def wait(self, timeout: Optional[float] = None) -> bool:
        """Block until the task is done (or timeout expires). Returns True if done."""
        return self._done_event.wait(timeout)

    @property
    def elapsed(self) -> Optional[float]:
        """Wall-clock seconds from start to finish (or now if still running)."""
        if self.started_at is None:
            return None
        end = self.finished_at or time.time()
        return round(end - self.started_at, 4)

    def __str__(self) -> str:
        return (
            f"Task(id={self.task_id}, fn={self.function.__name__}, "
            f"status={self.status.value}, elapsed={self.elapsed}s)"
        )


# ──────────────────────────────────────────────
# WorkerThread
# ──────────────────────────────────────────────
class _Sentinel:
    """Unique sentinel object placed in the queue to stop a worker."""
    def __lt__(self, other): return False
    def __le__(self, other): return False


class WorkerThread(threading.Thread):
    """
    A daemon thread that continuously pulls tasks from a shared queue
    and executes them until it receives a sentinel shutdown signal.
    """

    _SENTINEL = _Sentinel()   # placed in the queue to signal shutdown

    def __init__(self, task_queue: queue.PriorityQueue, results_lock: threading.Lock) -> None:
        super().__init__(daemon=True)
        self._task_queue   = task_queue
        self._results_lock = results_lock
        self._tasks_done   = 0
        self._active       = False

    # ── properties ──────────────────────────────────────────────────────────
    @property
    def tasks_done(self) -> int:
        return self._tasks_done

    @property
    def is_active(self) -> bool:
        return self._active

    # ── main loop ───────────────────────────────────────────────────────────
    def run(self) -> None:
        logger.debug("%s started.", self.name)
        while True:
            _priority, item = self._task_queue.get()

            # Sentinel → graceful shutdown
            if item is self._SENTINEL:
                logger.debug("%s received shutdown signal.", self.name)
                self._task_queue.task_done()
                break

            task = item
            self._execute(task)
            self._task_queue.task_done()
            self._tasks_done += 1

        logger.debug("%s exiting.", self.name)

    def _execute(self, task: Task) -> None:
        """Run a single task, capturing its result or exception."""
        task.status     = TaskStatus.RUNNING
        task.started_at = time.time()
        self._active    = True
        logger.info("▶  [%s] starting  task %s", self.name, task.task_id)

        try:
            task.result = task.function(*task.args, **task.kwargs)
            task.status = TaskStatus.COMPLETED
            logger.info("✔  [%s] completed task %s  (%.4fs)",
                        self.name, task.task_id, task.elapsed)
        except Exception as exc:
            task.error  = exc
            task.status = TaskStatus.FAILED
            logger.error("✘  [%s] task %s FAILED: %s", self.name, task.task_id, exc)
        finally:
            task.finished_at = time.time()
            task._done_event.set()   # unblock any waiting callers
            self._active = False


# ──────────────────────────────────────────────
# ThreadPool
# ──────────────────────────────────────────────
class ThreadPool:
    """
    Manages a fixed pool of WorkerThreads and a shared priority task queue.

    Usage
    -----
    with ThreadPool(num_workers=4) as pool:
        task = pool.submit(my_function, args=(1, 2))
        task.wait()
        print(task.result)
    """

    def __init__(self, num_workers: int = 4, queue_maxsize: int = 0) -> None:
        if num_workers < 1:
            raise ValueError("num_workers must be ≥ 1")

        self._num_workers  = num_workers
        self._task_queue:  queue.PriorityQueue = queue.PriorityQueue(maxsize=queue_maxsize)
        self._results_lock = threading.Lock()
        self._all_tasks:   list[Task]          = []
        self._task_lock    = threading.Lock()
        self._shutdown     = False
        self._workers:     list[WorkerThread]  = []

        self._start_workers()
        logger.info("ThreadPool started with %d workers.", num_workers)

    # ── context-manager support ──────────────────────────────────────────────
    def __enter__(self) -> "ThreadPool":
        return self

    def __exit__(self, *_) -> None:
        self.shutdown(wait=True)

    # ── public API ───────────────────────────────────────────────────────────
    def submit(
        self,
        function: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        priority: int = 0,
    ) -> Task:
        """
        Create a Task and enqueue it for execution.

        Parameters
        ----------
        function : callable
        args     : positional arguments for *function*
        kwargs   : keyword arguments for *function*
        priority : lower value → executed sooner (default 0)

        Returns
        -------
        Task  – the submitted task object (status starts as PENDING)
        """
        if self._shutdown:
            raise RuntimeError("Cannot submit tasks after shutdown.")

        task = Task(function=function, args=args, kwargs=kwargs or {}, priority=priority)

        with self._task_lock:
            self._all_tasks.append(task)

        self._task_queue.put((priority, task))
        logger.debug("⏳ queued task %s (priority=%d)", task.task_id, priority)
        return task

    def map(self, function: Callable, iterable, priority: int = 0) -> list[Task]:
        """Submit one task per item in *iterable* and return the list of Tasks."""
        return [self.submit(function, args=(item,), priority=priority) for item in iterable]

    def wait_all(self, timeout: Optional[float] = None) -> None:
        """Block until all currently queued tasks are finished."""
        self._task_queue.join()

    def shutdown(self, wait: bool = True) -> None:
        """
        Signal all workers to stop after finishing their current task.

        Parameters
        ----------
        wait : if True (default), block until all workers have exited.
        """
        if self._shutdown:
            return
        self._shutdown = True
        logger.info("Shutting down thread pool …")

        # One sentinel per worker — priority=inf so it is processed last
        for _ in self._workers:
            self._task_queue.put((float("inf"), WorkerThread._SENTINEL))

        if wait:
            for w in self._workers:
                w.join()
            logger.info("All workers stopped.")

    def cancel_pending(self) -> int:
        """
        Mark all PENDING tasks in the queue as CANCELLED and drain the queue.
        Returns the number of tasks cancelled.
        """
        cancelled = 0
        with self._task_lock:
            for task in self._all_tasks:
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    task._done_event.set()
                    cancelled += 1
        # Drain the queue (items are already marked cancelled)
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
                self._task_queue.task_done()
            except queue.Empty:
                break
        logger.info("Cancelled %d pending tasks.", cancelled)
        return cancelled

    # ── monitoring ───────────────────────────────────────────────────────────
    def stats(self) -> dict:
        """Return a snapshot of pool statistics."""
        with self._task_lock:
            tasks = list(self._all_tasks)

        counts = {s: 0 for s in TaskStatus}
        for t in tasks:
            counts[t.status] += 1

        return {
            "workers_total":  self._num_workers,
            "workers_active": sum(1 for w in self._workers if w.is_active),
            "queue_size":     self._task_queue.qsize(),
            "tasks_total":    len(tasks),
            "tasks_pending":  counts[TaskStatus.PENDING],
            "tasks_running":  counts[TaskStatus.RUNNING],
            "tasks_completed":counts[TaskStatus.COMPLETED],
            "tasks_failed":   counts[TaskStatus.FAILED],
            "tasks_cancelled":counts[TaskStatus.CANCELLED],
        }

    def print_stats(self) -> None:
        s = self.stats()
        print("\n── ThreadPool Stats ─────────────────────────────")
        for k, v in s.items():
            print(f"   {k:<22} {v}")
        print("─────────────────────────────────────────────────\n")

    def print_results(self) -> None:
        """Pretty-print results for all tracked tasks."""
        with self._task_lock:
            tasks = list(self._all_tasks)
        print("\n── Task Results ─────────────────────────────────")
        for t in tasks:
            status_icon = {"COMPLETED": "✔", "FAILED": "✘",
                           "CANCELLED": "⊘", "PENDING": "⏳",
                           "RUNNING": "▶"}.get(t.status.value, "?")
            result_str = str(t.result) if t.status == TaskStatus.COMPLETED else (
                         str(t.error)  if t.status == TaskStatus.FAILED    else "–")
            print(f"   {status_icon} [{t.task_id}] {t.function.__name__:<20} "
                  f"{t.status.value:<10} result={result_str}  ({t.elapsed}s)")
        print("─────────────────────────────────────────────────\n")

    # ── private helpers ──────────────────────────────────────────────────────
    def _start_workers(self) -> None:
        for i in range(self._num_workers):
            w = WorkerThread(self._task_queue, self._results_lock)
            w.name = f"Worker-{i + 1}"
            w.start()
            self._workers.append(w)


# ══════════════════════════════════════════════
# Demo Task Functions
# ══════════════════════════════════════════════

def compute_factorial(n: int) -> int:
    """Compute n! iteratively."""
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def compute_fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (iterative)."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def simulate_io_task(duration: float) -> str:
    """Simulate a slow I/O-bound operation."""
    time.sleep(duration)
    return f"IO completed after {duration:.2f}s"


def risky_task(value: int) -> int:
    """A task that intentionally fails for even inputs."""
    if value % 2 == 0:
        raise ValueError(f"risky_task rejects even input: {value}")
    return value * value


def matrix_trace(size: int) -> int:
    """Return the trace (sum of diagonal) of a size×size identity matrix."""
    return size   # trace of identity matrix = size


# ══════════════════════════════════════════════
# Main Demo
# ══════════════════════════════════════════════

def main() -> None:
    print("=" * 55)
    print("       Thread Pool Implementation Demo")
    print("=" * 55)

    # ── 1. Basic calculation tasks ────────────────────────────────
    print("\n[1] Submitting calculation tasks …\n")
    with ThreadPool(num_workers=3) as pool:

        # Factorial tasks
        factorial_tasks = [pool.submit(compute_factorial, args=(n,)) for n in [10, 15, 20, 25]]

        # Fibonacci tasks
        fib_tasks = [pool.submit(compute_fibonacci, args=(n,)) for n in [10, 20, 30, 35]]

        pool.wait_all()
        pool.print_results()

    # ── 2. Mixed priorities ───────────────────────────────────────
    print("\n[2] Submitting tasks with different priorities …\n")
    with ThreadPool(num_workers=2) as pool:

        pool.submit(simulate_io_task, args=(0.3,), priority=10)   # low priority
        pool.submit(simulate_io_task, args=(0.2,), priority=1)    # high priority
        pool.submit(compute_fibonacci, args=(40,),  priority=5)
        pool.submit(compute_factorial, args=(12,),  priority=1)   # high priority

        pool.wait_all()
        pool.print_stats()
        pool.print_results()

    # ── 3. Error-handling demo ────────────────────────────────────
    print("\n[3] Submitting tasks where some will fail …\n")
    with ThreadPool(num_workers=4) as pool:

        risky = [pool.submit(risky_task, args=(i,)) for i in range(1, 9)]
        pool.wait_all()
        pool.print_results()

    # ── 4. pool.map() + wait individual tasks ─────────────────────
    print("\n[4] Using pool.map() and individual task.wait() …\n")
    with ThreadPool(num_workers=4) as pool:

        durations = [round(random.uniform(0.1, 0.5), 2) for _ in range(6)]
        tasks = pool.map(simulate_io_task, durations)

        # Wait individually and print as each finishes
        for t in tasks:
            t.wait()
            print(f"   Task {t.task_id} → {t.result}")

        pool.print_stats()

    # ── 5. Large workload stress test ─────────────────────────────
    print("\n[5] Stress test: 50 tasks on 6 workers …\n")
    with ThreadPool(num_workers=6) as pool:

        tasks = [
            pool.submit(compute_fibonacci, args=(random.randint(20, 35),))
            for _ in range(50)
        ]
        pool.wait_all()
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        print(f"   Completed {completed}/{len(tasks)} tasks successfully.")
        pool.print_stats()

    print("\nDemo finished. ✔\n")


if __name__ == "__main__":
    main()