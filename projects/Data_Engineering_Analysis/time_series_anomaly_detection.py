"""
=============================================================================
Time-Series Anomaly Detection for Security Event Data
=============================================================================
Author  : Senior Python / Data-Science / Cybersecurity Developer
Purpose : Detect anomalies (spikes) in simulated security event streams
          using sliding-window statistics (moving average + std deviation).
Usage   : python time_series_anomaly_detection.py
Deps    : Python standard library only (datetime, random, statistics, math)
=============================================================================
"""

import datetime
import math
import os
import random
import statistics
import time


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_WINDOW_SIZE      = 15       # Sliding window length
DEFAULT_K_VALUE          = 2.5      # Sensitivity: anomaly if value > mean + k*std
DEFAULT_DATA_POINTS      = 60       # Number of data points to generate
DEFAULT_NORMAL_MEAN      = 100      # Baseline event count (normal behaviour)
DEFAULT_NORMAL_STD       = 15       # Natural variance in normal data
DEFAULT_SPIKE_PROBABILITY= 0.10     # ~10 % chance of a spike at any point
DEFAULT_SPIKE_MULTIPLIER = 4.0      # Spike = normal_mean * multiplier
EXPORT_FILENAME          = "anomaly_report.txt"
INTERVAL_SECONDS         = 1        # Simulated seconds between data points


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────
class DataPoint:
    """Represents a single time-series observation."""

    def __init__(self, timestamp: datetime.datetime, event_count: int,
                 is_anomaly: bool = False, z_score: float = 0.0,
                 mean: float = 0.0, std_dev: float = 0.0,
                 threshold: float = 0.0):
        self.timestamp   = timestamp
        self.event_count = event_count
        self.is_anomaly  = is_anomaly
        self.z_score     = z_score
        self.mean        = mean
        self.std_dev     = std_dev
        self.threshold   = threshold

    def __repr__(self) -> str:
        return (f"DataPoint(ts={self.timestamp.strftime('%H:%M:%S')}, "
                f"count={self.event_count}, anomaly={self.is_anomaly})")


# ─────────────────────────────────────────────────────────────────────────────
# DATA GENERATION
# ─────────────────────────────────────────────────────────────────────────────
def generate_time_series(
        num_points: int       = DEFAULT_DATA_POINTS,
        normal_mean: float    = DEFAULT_NORMAL_MEAN,
        normal_std: float     = DEFAULT_NORMAL_STD,
        spike_prob: float     = DEFAULT_SPIKE_PROBABILITY,
        spike_mult: float     = DEFAULT_SPIKE_MULTIPLIER,
        start_time: datetime.datetime | None = None
) -> list[dict]:
    """
    Generate synthetic security event time-series data.

    Returns a list of raw dicts:  { 'timestamp': datetime, 'event_count': int }
    Spikes are injected randomly to simulate anomalous security events
    (e.g., brute-force attempts, DDoS bursts, log floods).
    """
    if start_time is None:
        start_time = datetime.datetime.now()

    series = []
    for i in range(num_points):
        ts = start_time + datetime.timedelta(seconds=i * INTERVAL_SECONDS)

        # Decide: normal sample or spike?
        if random.random() < spike_prob:
            # Spike: mean * multiplier + small noise
            count = int(random.gauss(normal_mean * spike_mult,
                                     normal_std * spike_mult * 0.2))
        else:
            # Normal: Gaussian around baseline
            count = int(random.gauss(normal_mean, normal_std))

        # Clamp to non-negative (event counts can't be negative)
        count = max(0, count)
        series.append({"timestamp": ts, "event_count": count})

    return series


# ─────────────────────────────────────────────────────────────────────────────
# SLIDING WINDOW STATISTICS
# ─────────────────────────────────────────────────────────────────────────────
class SlidingWindowStats:
    """
    Maintains a fixed-size FIFO window of numeric values and exposes
    running mean, standard deviation and Z-score helpers.
    """

    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE):
        if window_size < 2:
            raise ValueError("Window size must be at least 2.")
        self.window_size = window_size
        self._buffer: list[float] = []

    # ── public interface ──────────────────────────────────────────────────────

    def push(self, value: float) -> None:
        """Add a new value; evict oldest if window is full."""
        self._buffer.append(value)
        if len(self._buffer) > self.window_size:
            self._buffer.pop(0)

    def mean(self) -> float:
        """Arithmetic mean of the current window."""
        if not self._buffer:
            return 0.0
        return statistics.mean(self._buffer)

    def std_dev(self) -> float:
        """
        Population std-dev when window < 3 (avoids ZeroDivisionError),
        sample std-dev otherwise for an unbiased estimator.
        """
        n = len(self._buffer)
        if n < 2:
            return 0.0
        if n < 3:
            return statistics.pstdev(self._buffer)
        return statistics.stdev(self._buffer)

    def z_score(self, value: float) -> float:
        """
        Z-score = (value - mean) / std_dev.
        Returns 0.0 when std_dev is effectively zero (flat signal).
        """
        sd = self.std_dev()
        if sd < 1e-9:
            return 0.0
        return (value - self.mean()) / sd

    def is_ready(self) -> bool:
        """True once the window holds enough data for meaningful statistics."""
        return len(self._buffer) >= max(3, self.window_size // 3)

    def __len__(self) -> int:
        return len(self._buffer)


# ─────────────────────────────────────────────────────────────────────────────
# ANOMALY DETECTOR
# ─────────────────────────────────────────────────────────────────────────────
class AnomalyDetector:
    """
    Processes a stream of raw data points and labels each one.

    Detection rule:
        value > mean + (k * std_dev)   →  ANOMALY

    Z-score is also computed for every point as an additional metric.
    """

    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE,
                 k: float = DEFAULT_K_VALUE):
        self.window_size = window_size
        self.k           = k
        self._stats      = SlidingWindowStats(window_size)
        self.results: list[DataPoint] = []

    # ── core processing ───────────────────────────────────────────────────────

    def process(self, raw_series: list[dict]) -> list[DataPoint]:
        """
        Iterate over raw data dicts, update the sliding window *before*
        scoring each point, then label anomalies.

        Note: the current point is NOT included in the window when computing
        its own threshold — this avoids look-ahead bias.
        """
        self.results = []

        for record in raw_series:
            ts    = record["timestamp"]
            value = float(record["event_count"])

            # Snapshot statistics BEFORE adding current value
            mu        = self._stats.mean()
            sigma     = self._stats.std_dev()
            threshold = mu + self.k * sigma
            z         = self._stats.z_score(value)

            # Determine anomaly only when the window is statistically ready
            is_anomaly = (
                self._stats.is_ready()
                and sigma > 0          # flat lines → no anomaly by default
                and value > threshold
            )

            dp = DataPoint(
                timestamp   = ts,
                event_count = int(value),
                is_anomaly  = is_anomaly,
                z_score     = z,
                mean        = mu,
                std_dev     = sigma,
                threshold   = threshold,
            )
            self.results.append(dp)

            # Update window with current value for future points
            self._stats.push(value)

        return self.results

    # ── summary helpers ───────────────────────────────────────────────────────

    def summary(self) -> dict:
        """Return high-level statistics about the detection run."""
        if not self.results:
            return {}
        total     = len(self.results)
        anomalies = [r for r in self.results if r.is_anomaly]
        counts    = [r.event_count for r in self.results]
        return {
            "total_points"   : total,
            "anomaly_count"  : len(anomalies),
            "anomaly_rate_pct": round(len(anomalies) / total * 100, 2),
            "global_mean"    : round(statistics.mean(counts), 2),
            "global_std"     : round(statistics.stdev(counts) if total > 1 else 0, 2),
            "max_value"      : max(counts),
            "min_value"      : min(counts),
        }


# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY / REPORTING
# ─────────────────────────────────────────────────────────────────────────────
ANSI_RED    = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN  = "\033[92m"
ANSI_CYAN   = "\033[96m"
ANSI_BOLD   = "\033[1m"
ANSI_RESET  = "\033[0m"

# Detect if the terminal supports ANSI (Windows cmd may not)
_USE_COLOR = hasattr(os, "get_terminal_size")


def colorize(text: str, color: str) -> str:
    """Wrap text in ANSI escape codes if the terminal supports colour."""
    if _USE_COLOR:
        return f"{color}{text}{ANSI_RESET}"
    return text


def print_header() -> None:
    """Print a decorative programme header."""
    border = "═" * 68
    print(colorize(f"\n╔{border}╗", ANSI_CYAN))
    print(colorize("║{:^68}║".format(
        "  🔒  TIME-SERIES SECURITY ANOMALY DETECTOR  🔒  "), ANSI_CYAN))
    print(colorize(f"╚{border}╝\n", ANSI_CYAN))


def print_column_headers() -> None:
    """Print the table column headers."""
    hdr = (
        f"{'Timestamp':^10} │ {'Events':^7} │ {'Mean':^8} │ "
        f"{'StdDev':^8} │ {'Threshold':^10} │ {'Z-Score':^8} │ Status"
    )
    sep = "─" * len(hdr)
    print(colorize(sep, ANSI_CYAN))
    print(colorize(hdr, ANSI_BOLD))
    print(colorize(sep, ANSI_CYAN))


def format_row(dp: DataPoint) -> str:
    """Format a single DataPoint as a table row string."""
    # Status label
    if dp.is_anomaly:
        status = colorize("⚠  ANOMALY DETECTED", ANSI_RED + ANSI_BOLD)
        count_str = colorize(f"{dp.event_count:>7}", ANSI_RED + ANSI_BOLD)
    else:
        status    = colorize("✔  Normal", ANSI_GREEN)
        count_str = f"{dp.event_count:>7}"

    # Highlight extreme Z-scores even for non-anomalies (informational)
    z_str = f"{dp.z_score:>+8.2f}"
    if abs(dp.z_score) > 3:
        z_str = colorize(z_str, ANSI_YELLOW)

    row = (
        f"{dp.timestamp.strftime('%H:%M:%S'):^10} │ {count_str} │ "
        f"{dp.mean:>8.1f} │ {dp.std_dev:>8.2f} │ "
        f"{dp.threshold:>10.1f} │ {z_str} │ {status}"
    )
    return row


def print_results(results: list[DataPoint], live_delay: float = 0.0) -> None:
    """
    Print all detection results, optionally with a per-row delay to
    simulate a live stream.
    """
    print_column_headers()
    for dp in results:
        print(format_row(dp))
        if live_delay > 0:
            time.sleep(live_delay)
    border = "─" * 80
    print(colorize(border, ANSI_CYAN))


def print_summary(det: AnomalyDetector) -> None:
    """Print the post-run summary statistics table."""
    s = det.summary()
    if not s:
        print("  No results to summarise.")
        return

    print(colorize("\n┌─ Detection Summary " + "─" * 48 + "┐", ANSI_CYAN))
    lines = [
        ("Total data points",   s["total_points"]),
        ("Anomalies detected",  s["anomaly_count"]),
        ("Anomaly rate",        f"{s['anomaly_rate_pct']} %"),
        ("Global mean",         s["global_mean"]),
        ("Global std deviation",s["global_std"]),
        ("Maximum event count", s["max_value"]),
        ("Minimum event count", s["min_value"]),
        ("K sensitivity factor",det.k),
        ("Window size",         det.window_size),
    ]
    for label, value in lines:
        print(f"│  {label:<30} : {str(value):<32} │")
    print(colorize("└" + "─" * 68 + "┘\n", ANSI_CYAN))


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def export_anomalies(results: list[DataPoint],
                     filename: str = EXPORT_FILENAME) -> str:
    """
    Write anomalous data points (and a summary) to a plain-text file.
    Returns the absolute path of the written file.
    """
    anomalies = [r for r in results if r.is_anomaly]
    filepath  = os.path.abspath(filename)

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write("TIME-SERIES ANOMALY DETECTION REPORT\n")
        fh.write(f"Generated : {datetime.datetime.now()}\n")
        fh.write("=" * 60 + "\n\n")

        if not anomalies:
            fh.write("No anomalies detected in this run.\n")
        else:
            fh.write(f"Total anomalies : {len(anomalies)}\n\n")
            fh.write(
                f"{'Timestamp':<12} {'Events':>8} {'Mean':>10} "
                f"{'StdDev':>10} {'Threshold':>12} {'Z-Score':>10}\n"
            )
            fh.write("-" * 64 + "\n")
            for dp in anomalies:
                fh.write(
                    f"{dp.timestamp.strftime('%H:%M:%S'):<12} "
                    f"{dp.event_count:>8} {dp.mean:>10.1f} "
                    f"{dp.std_dev:>10.2f} {dp.threshold:>12.1f} "
                    f"{dp.z_score:>+10.2f}\n"
                )

        fh.write("\n" + "=" * 60 + "\n")
        fh.write("END OF REPORT\n")

    return filepath


# ─────────────────────────────────────────────────────────────────────────────
# LIVE STREAM SIMULATION (bonus feature)
# ─────────────────────────────────────────────────────────────────────────────
def run_live_stream(
        num_points: int  = DEFAULT_DATA_POINTS,
        window_size: int = DEFAULT_WINDOW_SIZE,
        k: float         = DEFAULT_K_VALUE,
        delay: float     = 0.08          # seconds between printed rows
) -> list[DataPoint]:
    """
    Generate and detect anomalies in a live-stream fashion:
    data is produced one point at a time and scored immediately,
    giving the impression of a real-time security monitor.
    """
    print(colorize("\n  ▶  Starting live stream simulation …\n", ANSI_YELLOW))
    raw    = generate_time_series(num_points=num_points)
    det    = AnomalyDetector(window_size=window_size, k=k)
    stats  = SlidingWindowStats(window_size)

    print_column_headers()

    results: list[DataPoint] = []
    for record in raw:
        value     = float(record["event_count"])
        ts        = record["timestamp"]
        mu        = stats.mean()
        sigma     = stats.std_dev()
        threshold = mu + k * sigma
        z         = stats.z_score(value)

        is_anomaly = (
            stats.is_ready()
            and sigma > 0
            and value > threshold
        )

        dp = DataPoint(
            timestamp   = ts,
            event_count = int(value),
            is_anomaly  = is_anomaly,
            z_score     = z,
            mean        = mu,
            std_dev     = sigma,
            threshold   = threshold,
        )
        results.append(dp)
        stats.push(value)

        print(format_row(dp))
        time.sleep(delay)

    print(colorize("─" * 80, ANSI_CYAN))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# INPUT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def prompt_int(prompt: str, default: int, min_val: int = 1,
               max_val: int = 10_000) -> int:
    """Prompt the user for an integer with validation and a default value."""
    while True:
        raw = input(f"  {prompt} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(f"  ⚠  Please enter a value between {min_val} and {max_val}.")
        except ValueError:
            print("  ⚠  Invalid input – please enter a whole number.")


def prompt_float(prompt: str, default: float, min_val: float = 0.1,
                 max_val: float = 100.0) -> float:
    """Prompt the user for a float with validation and a default value."""
    while True:
        raw = input(f"  {prompt} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            val = float(raw)
            if min_val <= val <= max_val:
                return val
            print(f"  ⚠  Please enter a value between {min_val} and {max_val}.")
        except ValueError:
            print("  ⚠  Invalid input – please enter a number.")


def prompt_yes_no(prompt: str, default: bool = True) -> bool:
    """Prompt for a yes/no answer."""
    default_str = "Y/n" if default else "y/N"
    raw = input(f"  {prompt} [{default_str}]: ").strip().lower()
    if raw == "":
        return default
    return raw in ("y", "yes")


# ─────────────────────────────────────────────────────────────────────────────
# MENU SYSTEM
# ─────────────────────────────────────────────────────────────────────────────
# Shared state between menu options
_raw_data: list[dict]       = []
_results:  list[DataPoint]  = []
_config: dict = {
    "num_points"  : DEFAULT_DATA_POINTS,
    "window_size" : DEFAULT_WINDOW_SIZE,
    "k"           : DEFAULT_K_VALUE,
    "normal_mean" : DEFAULT_NORMAL_MEAN,
    "normal_std"  : DEFAULT_NORMAL_STD,
    "spike_prob"  : DEFAULT_SPIKE_PROBABILITY,
    "spike_mult"  : DEFAULT_SPIKE_MULTIPLIER,
}


def menu_generate() -> None:
    """CLI option 1 – Generate (or re-generate) the time-series data."""
    global _raw_data, _results

    print(colorize("\n  ── Generate Time-Series Data ──", ANSI_BOLD))

    if prompt_yes_no("Customise generation parameters?", default=False):
        _config["num_points"]  = prompt_int(
            "Number of data points", _config["num_points"], 10, 10_000)
        _config["normal_mean"] = prompt_int(
            "Normal mean event count", _config["normal_mean"], 1, 100_000)
        _config["normal_std"]  = prompt_int(
            "Normal std deviation", _config["normal_std"], 1, 10_000)
        _config["spike_prob"]  = prompt_float(
            "Spike probability (0.01–0.50)", _config["spike_prob"], 0.01, 0.50)
        _config["spike_mult"]  = prompt_float(
            "Spike multiplier (1.5–20)", _config["spike_mult"], 1.5, 20.0)

    _raw_data = generate_time_series(
        num_points   = _config["num_points"],
        normal_mean  = _config["normal_mean"],
        normal_std   = _config["normal_std"],
        spike_prob   = _config["spike_prob"],
        spike_mult   = _config["spike_mult"],
    )
    _results = []   # Invalidate old results

    print(colorize(
        f"\n  ✔  Generated {len(_raw_data)} data points successfully.", ANSI_GREEN))
    print(f"     First timestamp : {_raw_data[0]['timestamp'].strftime('%H:%M:%S')}")
    print(f"     Last  timestamp : {_raw_data[-1]['timestamp'].strftime('%H:%M:%S')}")
    print(f"     Event range     : "
          f"{min(r['event_count'] for r in _raw_data)} – "
          f"{max(r['event_count'] for r in _raw_data)}")


def menu_detect() -> None:
    """CLI option 2 – Run anomaly detection on the current dataset."""
    global _results

    if not _raw_data:
        print(colorize(
            "\n  ✖  No data available. Please generate data first (option 1).",
            ANSI_RED))
        return

    print(colorize("\n  ── Run Anomaly Detection ──", ANSI_BOLD))

    if prompt_yes_no("Customise detection parameters?", default=False):
        _config["window_size"] = prompt_int(
            "Sliding window size", _config["window_size"], 3, 200)
        _config["k"]           = prompt_float(
            "Sensitivity k (higher = less sensitive)", _config["k"], 0.5, 10.0)

    det      = AnomalyDetector(
        window_size = _config["window_size"],
        k           = _config["k"],
    )
    _results = det.process(_raw_data)

    print(colorize("\n  ── Detection Results ──\n", ANSI_BOLD))
    print_results(_results)
    print_summary(det)


def menu_live_stream() -> None:
    """CLI option 3 – Run live-stream simulation."""
    global _results

    print(colorize("\n  ── Live Stream Simulation ──", ANSI_BOLD))

    if prompt_yes_no("Customise parameters?", default=False):
        _config["num_points"]  = prompt_int(
            "Number of data points", _config["num_points"], 10, 10_000)
        _config["window_size"] = prompt_int(
            "Sliding window size", _config["window_size"], 3, 200)
        _config["k"]           = prompt_float(
            "Sensitivity k", _config["k"], 0.5, 10.0)

    delay = prompt_float("Row display delay in seconds", 0.08, 0.0, 5.0)

    _results = run_live_stream(
        num_points  = _config["num_points"],
        window_size = _config["window_size"],
        k           = _config["k"],
        delay       = delay,
    )

    # Build a temporary detector for summary only (results already computed)
    det         = AnomalyDetector(_config["window_size"], _config["k"])
    det.results = _results
    print_summary(det)


def menu_show_raw() -> None:
    """CLI option 4 – Display raw generated data."""
    if not _raw_data:
        print(colorize(
            "\n  ✖  No data. Please generate data first (option 1).", ANSI_RED))
        return

    print(colorize("\n  ── Raw Time-Series Data ──\n", ANSI_BOLD))
    header = f"  {'#':>5}  {'Timestamp':^10}  {'Event Count':>12}"
    print(colorize(header, ANSI_CYAN))
    print(colorize("  " + "─" * 32, ANSI_CYAN))
    for i, r in enumerate(_raw_data, 1):
        print(f"  {i:>5}  {r['timestamp'].strftime('%H:%M:%S'):^10}  "
              f"{r['event_count']:>12}")
    print()


def menu_export() -> None:
    """CLI option 5 – Export anomalies to a text file."""
    if not _results:
        print(colorize(
            "\n  ✖  No results. Please run detection first (option 2 or 3).",
            ANSI_RED))
        return

    fname    = input(f"  Output filename [{EXPORT_FILENAME}]: ").strip()
    fname    = fname if fname else EXPORT_FILENAME
    filepath = export_anomalies(_results, fname)

    anomaly_count = sum(1 for r in _results if r.is_anomaly)
    print(colorize(
        f"\n  ✔  Report saved: {filepath}", ANSI_GREEN))
    print(f"     Anomalies exported: {anomaly_count}")


def menu_config() -> None:
    """CLI option 6 – Display current configuration."""
    print(colorize("\n  ── Current Configuration ──\n", ANSI_BOLD))
    labels = {
        "num_points"  : "Data points to generate",
        "normal_mean" : "Normal baseline mean",
        "normal_std"  : "Normal baseline std dev",
        "spike_prob"  : "Spike probability",
        "spike_mult"  : "Spike multiplier",
        "window_size" : "Sliding window size",
        "k"           : "Sensitivity factor (k)",
    }
    for key, label in labels.items():
        print(f"  {label:<35} : {_config[key]}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
MENU_OPTIONS = {
    "1": ("Generate time-series data",        menu_generate),
    "2": ("Run anomaly detection",             menu_detect),
    "3": ("Live-stream simulation",            menu_live_stream),
    "4": ("Show raw data",                     menu_show_raw),
    "5": ("Export anomaly report to file",     menu_export),
    "6": ("Show current configuration",        menu_config),
    "0": ("Exit",                              None),
}


def print_menu() -> None:
    """Render the main CLI menu."""
    print(colorize("\n  ┌─ Main Menu " + "─" * 40 + "┐", ANSI_CYAN))
    for key, (label, _) in MENU_OPTIONS.items():
        indicator = colorize(f"[{key}]", ANSI_BOLD)
        print(f"  │  {indicator}  {label:<40} │")
    print(colorize("  └" + "─" * 52 + "┘", ANSI_CYAN))
    print()


def main() -> None:
    """Application entry point – main interactive loop."""
    print_header()

    # Seed the PRNG for reproducibility hint
    random.seed()   # Uses system time → different each run

    print("  Welcome to the Time-Series Security Anomaly Detector.")
    print("  Tip: Start by generating data (1), then run detection (2).\n")

    while True:
        print_menu()
        choice = input("  Enter option: ").strip()

        if choice not in MENU_OPTIONS:
            print(colorize("  ⚠  Invalid option. Please choose from the menu.",
                           ANSI_YELLOW))
            continue

        label, handler = MENU_OPTIONS[choice]

        if choice == "0":
            print(colorize("\n  Goodbye! Stay secure. 🔒\n", ANSI_GREEN))
            break

        print(colorize(f"\n  → {label}", ANSI_BOLD))
        try:
            handler()
        except KeyboardInterrupt:
            print(colorize("\n  ⚠  Operation interrupted by user.", ANSI_YELLOW))
        except Exception as exc:        # Broad catch keeps the menu alive
            print(colorize(f"\n  ✖  Unexpected error: {exc}", ANSI_RED))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colorize("\n\n  Session terminated. Goodbye!\n", ANSI_YELLOW))