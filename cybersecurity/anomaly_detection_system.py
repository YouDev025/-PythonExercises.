"""
Anomaly Detection System
========================
A modular OOP-based system for detecting statistical anomalies in datasets.
"""

import math
import statistics
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
#  DataPoint
# ─────────────────────────────────────────────

class DataPoint:
    """Represents a single data observation with a value and timestamp."""

    def __init__(self, value: float, timestamp: Optional[datetime] = None):
        self._value = self._validate_value(value)
        self._timestamp = timestamp or datetime.now()

    # ── Validation ────────────────────────────
    @staticmethod
    def _validate_value(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid data value: '{value}'. Must be numeric.")

    # ── Properties ────────────────────────────
    @property
    def value(self) -> float:
        return self._value

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def __repr__(self) -> str:
        ts = self._timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"DataPoint(value={self._value:.4f}, timestamp='{ts}')"


# ─────────────────────────────────────────────
#  AnomalyDetector
# ─────────────────────────────────────────────

class AnomalyDetector:
    """
    Analyses a list of DataPoints using z-score statistics.

    A point is flagged as anomalous when its z-score exceeds *threshold*
    (default = 2.0 standard deviations from the mean).
    """

    DEFAULT_THRESHOLD = 2.0
    MIN_POINTS = 2          # need at least 2 points for std-dev

    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        if threshold <= 0:
            raise ValueError("Threshold must be a positive number.")
        self._threshold = threshold
        self._mean: Optional[float] = None
        self._std: Optional[float] = None
        self._anomalies: list[tuple[DataPoint, float]] = []   # (point, z-score)

    # ── Properties ────────────────────────────
    @property
    def threshold(self) -> float:
        return self._threshold

    @property
    def mean(self) -> Optional[float]:
        return self._mean

    @property
    def std(self) -> Optional[float]:
        return self._std

    @property
    def anomalies(self) -> list[tuple[DataPoint, float]]:
        return list(self._anomalies)

    # ── Core analysis ─────────────────────────
    def analyse(self, data_points: list[DataPoint]) -> None:
        """Compute statistics and identify anomalous points."""
        if len(data_points) < self.MIN_POINTS:
            raise ValueError(
                f"Need at least {self.MIN_POINTS} data points to run detection."
            )

        values = [dp.value for dp in data_points]
        self._mean = statistics.mean(values)
        self._std = statistics.pstdev(values)   # population std-dev
        self._anomalies = []

        if self._std == 0:
            # All values identical – no anomalies possible
            return

        for dp in data_points:
            z = abs((dp.value - self._mean) / self._std)
            if z > self._threshold:
                self._anomalies.append((dp, round(z, 4)))

    # ── Display ───────────────────────────────
    def display_results(self) -> None:
        """Print a formatted summary of the analysis."""
        if self._mean is None:
            print("  [!] No analysis has been run yet.")
            return

        print("\n" + "═" * 55)
        print("  ANOMALY DETECTION RESULTS")
        print("═" * 55)
        print(f"  Mean              : {self._mean:.4f}")
        print(f"  Std Deviation     : {self._std:.4f}")
        print(f"  Threshold (σ)     : {self._threshold}")
        normal_range = (
            self._mean - self._threshold * self._std,
            self._mean + self._threshold * self._std,
        )
        print(f"  Normal range      : [{normal_range[0]:.4f}, {normal_range[1]:.4f}]")
        print("─" * 55)

        if not self._anomalies:
            print("  ✔  No anomalies detected.")
        else:
            print(f"  ✘  {len(self._anomalies)} anomaly(ies) detected:\n")
            for i, (dp, z) in enumerate(self._anomalies, 1):
                ts = dp.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  [{i}] Value: {dp.value:.4f}  |  Z-score: {z:.4f}  |  {ts}")
        print("═" * 55 + "\n")


# ─────────────────────────────────────────────
#  DetectionManager
# ─────────────────────────────────────────────

class DetectionManager:
    """
    Manages the dataset lifecycle and coordinates the detection workflow.

    Responsibilities
    ----------------
    * Add / remove / clear data points
    * Delegate analysis to AnomalyDetector
    * Provide dataset summaries for the CLI
    """

    def __init__(self, threshold: float = AnomalyDetector.DEFAULT_THRESHOLD):
        self._data: list[DataPoint] = []
        self._detector = AnomalyDetector(threshold)

    # ── Dataset management ────────────────────
    def add_point(self, value: float, timestamp: Optional[datetime] = None) -> DataPoint:
        """Validate and append a new DataPoint; return it."""
        dp = DataPoint(value, timestamp)
        self._data.append(dp)
        return dp

    def remove_last(self) -> Optional[DataPoint]:
        """Remove and return the most-recently added point, or None."""
        return self._data.pop() if self._data else None

    def clear(self) -> None:
        """Delete all data points."""
        self._data.clear()

    @property
    def data(self) -> list[DataPoint]:
        return list(self._data)

    @property
    def count(self) -> int:
        return len(self._data)

    # ── Detection coordination ─────────────────
    def run_detection(self) -> None:
        """Run the anomaly analysis on the current dataset."""
        self._detector.analyse(self._data)
        self._detector.display_results()

    # ── Summary ───────────────────────────────
    def display_dataset(self) -> None:
        """Print every data point currently stored."""
        if not self._data:
            print("\n  Dataset is empty.\n")
            return

        print("\n" + "─" * 55)
        print(f"  DATASET  ({self.count} point(s))")
        print("─" * 55)
        for i, dp in enumerate(self._data, 1):
            ts = dp.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {i:>3}. {dp.value:>12.4f}   {ts}")
        print("─" * 55 + "\n")


# ─────────────────────────────────────────────
#  Command-Line Interface
# ─────────────────────────────────────────────

class CLI:
    """Text-based menu interface for the Anomaly Detection System."""

    BANNER = r"""
  ╔══════════════════════════════════════════════════╗
  ║        ANOMALY  DETECTION  SYSTEM  v1.0          ║
  ║   Statistical outlier detection via z-scores     ║
  ╚══════════════════════════════════════════════════╝
"""

    MENU = """
  ┌─────────────────────────────────────────────┐
  │  1. Add a data value                        │
  │  2. Add multiple values (comma-separated)   │
  │  3. View current dataset                    │
  │  4. Run anomaly detection                   │
  │  5. Remove last entry                       │
  │  6. Change detection threshold              │
  │  7. Clear dataset                           │
  │  8. Load demo dataset                       │
  │  9. Exit                                    │
  └─────────────────────────────────────────────┘
  Choice: """

    DEMO_VALUES = [12, 14, 13, 15, 14, 200, 13, 12, 11, 14, -150, 13, 15]

    def __init__(self):
        self._manager = DetectionManager()

    # ── Helpers ───────────────────────────────
    @staticmethod
    def _input_float(prompt: str) -> Optional[float]:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print(f"  [!] '{raw}' is not a valid number.")
            return None

    # ── Menu actions ──────────────────────────
    def _add_single(self) -> None:
        val = self._input_float("  Enter value: ")
        if val is not None:
            dp = self._manager.add_point(val)
            print(f"  ✔  Added {dp}")

    def _add_multiple(self) -> None:
        raw = input("  Enter values (comma-separated): ").strip()
        added = 0
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            try:
                dp = self._manager.add_point(float(token))
                print(f"  ✔  Added {dp}")
                added += 1
            except ValueError as exc:
                print(f"  [!] Skipped '{token}': {exc}")
        print(f"\n  {added} value(s) added.")

    def _remove_last(self) -> None:
        dp = self._manager.remove_last()
        if dp:
            print(f"  ✔  Removed {dp}")
        else:
            print("  [!] Dataset is already empty.")

    def _change_threshold(self) -> None:
        val = self._input_float(
            f"  Current threshold: {self._manager._detector.threshold}\n"
            "  Enter new threshold (σ, e.g. 2.0): "
        )
        if val is not None:
            try:
                self._manager = DetectionManager(threshold=val)
                # Re-populate with existing data (rebuild manager)
                print(f"  ✔  Threshold set to {val}σ. Dataset cleared – please re-add data.")
            except ValueError as exc:
                print(f"  [!] {exc}")

    def _load_demo(self) -> None:
        self._manager.clear()
        for v in self.DEMO_VALUES:
            self._manager.add_point(v)
        print(f"  ✔  Loaded {len(self.DEMO_VALUES)} demo values: {self.DEMO_VALUES}")

    # ── Main loop ─────────────────────────────
    def run(self) -> None:
        print(self.BANNER)

        actions = {
            "1": self._add_single,
            "2": self._add_multiple,
            "3": self._manager.display_dataset,
            "4": self._run_detection_safe,
            "5": self._remove_last,
            "6": self._change_threshold,
            "7": self._clear_confirmed,
            "8": self._load_demo,
            "9": None,  # Exit sentinel
        }

        while True:
            choice = input(self.MENU).strip()
            if choice == "9":
                print("\n  Goodbye!\n")
                break
            action = actions.get(choice)
            if action is None and choice != "9":
                print("  [!] Invalid choice. Please enter 1-9.")
            elif action:
                try:
                    action()
                except Exception as exc:
                    print(f"  [!] Error: {exc}")

    def _run_detection_safe(self) -> None:
        try:
            self._manager.run_detection()
        except ValueError as exc:
            print(f"\n  [!] Cannot run detection: {exc}\n")

    def _clear_confirmed(self) -> None:
        confirm = input(
            f"  Clear all {self._manager.count} data point(s)? (yes/no): "
        ).strip().lower()
        if confirm in ("yes", "y"):
            self._manager.clear()
            print("  ✔  Dataset cleared.")
        else:
            print("  Cancelled.")


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    CLI().run()