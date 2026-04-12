"""
real_time_data_streaming_webapp.py
===================================
Flask web application to control the real-time security-log streaming simulator.
Provides start, stop, and restart functionality with live metrics dashboard.

Run:
    python real_time_data_streaming_webapp.py

Access:
    http://localhost:5000
"""

import queue
import random
import threading
import time
import os
import sys
import signal
import collections
import itertools
import json
from typing import Dict, List, Optional, DefaultDict
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import atexit


# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

class Config:
    # ── Producer settings ─────────────────────────────────────────────────
    NUM_PRODUCERS        : int   = 3
    PRODUCE_INTERVAL_MIN : float = 0.3
    PRODUCE_INTERVAL_MAX : float = 1.2
    BURST_PROBABILITY    : float = 0.05
    BURST_SIZE           : int   = 8

    # ── Consumer settings ─────────────────────────────────────────────────
    NUM_CONSUMERS        : int   = 2
    BATCH_SIZE           : int   = 5
    CONSUMER_INTERVAL    : float = 0.4

    # ── Queue ─────────────────────────────────────────────────────────────
    QUEUE_MAX_SIZE       : int   = 500

    # ── Anomaly detection thresholds ──────────────────────────────────────
    FAILED_LOGIN_WINDOW  : int   = 10
    FAILED_LOGIN_LIMIT   : int   = 5
    HIGH_FREQ_WINDOW     : int   = 5
    HIGH_FREQ_LIMIT      : int   = 15
    ALERT_COOLDOWN       : int   = 8

    # ── Web Dashboard ─────────────────────────────────────────────────────
    UPDATE_INTERVAL      : float = 1.0  # seconds between metric updates
    EVENT_LOG_MAX_LINES  : int   = 20


# ═══════════════════════════════════════════════════════════════════════════
#  EVENT MODEL
# ═══════════════════════════════════════════════════════════════════════════

_EVENT_TYPES  = ["login", "request", "error", "alert", "scan", "transfer"]
_STATUSES     = ["success", "failure"]
_STATUS_WEIGHTS = [0.65, 0.35]

_IP_POOL: List[str] = (
    [f"10.0.{r}.{h}"      for r in range(5)  for h in random.sample(range(2, 254), 8)]
  + [f"192.168.{r}.{h}"   for r in range(3)  for h in random.sample(range(2, 254), 6)]
  + [f"172.16.{r}.{h}"    for r in range(2)  for h in random.sample(range(2, 254), 4)]
  + ["45.33.32.156", "198.51.100.23", "203.0.113.77",
     "185.220.101.5", "91.108.4.183", "66.249.66.1"]
)

_EVENT_ID_COUNTER = itertools.count(1)


def make_event(producer_id: int) -> Dict:
    """Build a single security-event dict."""
    etype  = random.choice(_EVENT_TYPES)
    status = random.choices(_STATUSES, weights=_STATUS_WEIGHTS, k=1)[0]

    if etype in ("error", "alert") or status == "failure":
        severity = random.choices(
            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            weights=[10, 40, 35, 15], k=1
        )[0]
    else:
        severity = random.choices(
            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            weights=[60, 30, 8, 2], k=1
        )[0]

    return {
        "id"         : next(_EVENT_ID_COUNTER),
        "timestamp"  : time.strftime("%H:%M:%S"),
        "epoch"      : time.time(),
        "producer_id": producer_id,
        "source_ip"  : random.choice(_IP_POOL),
        "event_type" : etype,
        "status"     : status,
        "severity"   : severity,
        "payload_sz" : random.randint(64, 8192),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  SHARED STATE
# ═══════════════════════════════════════════════════════════════════════════

class SharedState:
    """Thread-safe central store for all metrics and event logs."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

        # Counters
        self.total_produced  : int = 0
        self.total_consumed  : int = 0
        self.events_by_type  : DefaultDict[str, int] = collections.defaultdict(int)
        self.events_by_status: DefaultDict[str, int] = collections.defaultdict(int)
        self.events_by_sev   : DefaultDict[str, int] = collections.defaultdict(int)
        self.alerts_triggered: int = 0
        self.producer_counts : DefaultDict[int, int] = collections.defaultdict(int)

        # Anomaly detection windows
        self.failed_login_times : collections.deque = collections.deque()
        self.all_event_times    : collections.deque = collections.deque()
        self._alert_last_seen   : Dict[str, float] = {}

        # Live event feed
        self.event_log : collections.deque = collections.deque(
            maxlen=Config.EVENT_LOG_MAX_LINES
        )
        self.alert_log : collections.deque = collections.deque(maxlen=10)

        # Runtime
        self.start_epoch : float = time.time()
        self.is_running  : bool = False

    def reset(self) -> None:
        """Reset all metrics for a fresh start."""
        with self._lock:
            self.total_produced = 0
            self.total_consumed = 0
            self.events_by_type.clear()
            self.events_by_status.clear()
            self.events_by_sev.clear()
            self.alerts_triggered = 0
            self.producer_counts.clear()
            self.failed_login_times.clear()
            self.all_event_times.clear()
            self._alert_last_seen.clear()
            self.event_log.clear()
            self.alert_log.clear()
            self.start_epoch = time.time()

    def record_produced(self) -> None:
        with self._lock:
            self.total_produced += 1

    def record_consumed(self, event: Dict) -> None:
        with self._lock:
            self.total_consumed  += 1
            self.events_by_type  [event["event_type"]] += 1
            self.events_by_status[event["status"]]     += 1
            self.events_by_sev   [event["severity"]]   += 1
            self.producer_counts [event["producer_id"]]  += 1
            now = event["epoch"]
            self.all_event_times.append(now)
            if event["event_type"] == "login" and event["status"] == "failure":
                self.failed_login_times.append(now)
            self.event_log.append(event)

    def check_anomalies(self) -> Optional[Dict]:
        """Check for anomalies and return alert if triggered."""
        with self._lock:
            now = time.time()

            # Prune stale entries
            cutoff_fl = now - Config.FAILED_LOGIN_WINDOW
            cutoff_hf = now - Config.HIGH_FREQ_WINDOW
            while self.failed_login_times and self.failed_login_times[0] < cutoff_fl:
                self.failed_login_times.popleft()
            while self.all_event_times and self.all_event_times[0] < cutoff_hf:
                self.all_event_times.popleft()

            alert_msg = None

            # Check brute-force
            if len(self.failed_login_times) >= Config.FAILED_LOGIN_LIMIT:
                msg = (f"🔑 BRUTE-FORCE DETECTED — "
                       f"{len(self.failed_login_times)} failed logins "
                       f"in {Config.FAILED_LOGIN_WINDOW}s window")
                if self._fire_alert("BRUTE_FORCE", msg, now):
                    alert_msg = {"type": "brute_force", "message": msg, "timestamp": time.strftime("%H:%M:%S")}

            # Check high frequency
            if len(self.all_event_times) >= Config.HIGH_FREQ_LIMIT:
                msg = (f"⚡ HIGH-FREQUENCY TRAFFIC — "
                       f"{len(self.all_event_times)} events "
                       f"in {Config.HIGH_FREQ_WINDOW}s window")
                if self._fire_alert("HIGH_FREQ", msg, now):
                    alert_msg = {"type": "high_freq", "message": msg, "timestamp": time.strftime("%H:%M:%S")}

            return alert_msg

    def _fire_alert(self, key: str, msg: str, now: float) -> bool:
        """Emit alert if not in cooldown. Returns True if alert was fired."""
        last = self._alert_last_seen.get(key, 0.0)
        if now - last < Config.ALERT_COOLDOWN:
            return False
        self._alert_last_seen[key] = now
        self.alerts_triggered += 1
        ts = time.strftime("%H:%M:%S", time.localtime(now))
        self.alert_log.append({"timestamp": ts, "message": msg, "type": key})
        return True

    def snapshot(self) -> Dict:
        with self._lock:
            return {
                "produced"      : self.total_produced,
                "consumed"      : self.total_consumed,
                "by_type"       : dict(self.events_by_type),
                "by_status"     : dict(self.events_by_status),
                "by_sev"        : dict(self.events_by_sev),
                "alerts"        : self.alerts_triggered,
                "producer_counts": dict(self.producer_counts),
                "event_log"     : list(self.event_log),
                "alert_log"     : list(self.alert_log),
                "uptime"        : time.time() - self.start_epoch if self.is_running else 0,
                "is_running"    : self.is_running,
            }


# ═══════════════════════════════════════════════════════════════════════════
#  SIMULATOR THREADS
# ═══════════════════════════════════════════════════════════════════════════

class Producer(threading.Thread):
    def __init__(self, producer_id: int, stream_queue: queue.Queue,
                 state: SharedState, stop_event: threading.Event) -> None:
        super().__init__(name=f"Producer-{producer_id}", daemon=True)
        self.pid = producer_id
        self.queue = stream_queue
        self.state = state
        self.stop_event = stop_event

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                if random.random() < Config.BURST_PROBABILITY:
                    for _ in range(Config.BURST_SIZE):
                        if self.stop_event.is_set():
                            break
                        self._emit()
                else:
                    self._emit()

                interval = random.uniform(Config.PRODUCE_INTERVAL_MIN,
                                         Config.PRODUCE_INTERVAL_MAX)
                for _ in range(int(interval * 10)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
            except Exception:
                time.sleep(0.5)

    def _emit(self) -> None:
        if self.stop_event.is_set():
            return
        event = make_event(self.pid)
        try:
            self.queue.put(event, block=True, timeout=0.5)
            self.state.record_produced()
        except queue.Full:
            pass


class Consumer(threading.Thread):
    def __init__(self, consumer_id: int, stream_queue: queue.Queue,
                 state: SharedState, stop_event: threading.Event,
                 alert_callback=None) -> None:
        super().__init__(name=f"Consumer-{consumer_id}", daemon=True)
        self.cid = consumer_id
        self.queue = stream_queue
        self.state = state
        self.stop_event = stop_event
        self.alert_callback = alert_callback

    def run(self) -> None:
        while not self.stop_event.is_set():
            batch: List[Dict] = []

            for _ in range(Config.BATCH_SIZE):
                if self.stop_event.is_set():
                    break
                try:
                    event = self.queue.get(block=True, timeout=0.2)
                    batch.append(event)
                    self.queue.task_done()
                except queue.Empty:
                    break

            if batch:
                for event in batch:
                    self.state.record_consumed(event)
                alert = self.state.check_anomalies()
                if alert and self.alert_callback:
                    self.alert_callback(alert)

            for _ in range(int(Config.CONSUMER_INTERVAL * 10)):
                if self.stop_event.is_set():
                    break
                time.sleep(0.1)


# ═══════════════════════════════════════════════════════════════════════════
#  SIMULATOR CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════

class SimulatorController:
    """Manages the simulator lifecycle."""

    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.stream_queue: Optional[queue.Queue] = None
        self.state: SharedState = SharedState()
        self.stop_event: Optional[threading.Event] = None
        self.producers: List[Producer] = []
        self.consumers: List[Consumer] = []
        self.update_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def alert_callback(self, alert: Dict):
        """Called when an anomaly is detected."""
        self.socketio.emit('alert', alert)

    def start(self) -> bool:
        """Start the simulator."""
        with self._lock:
            if self.state.is_running:
                return False

            self.stream_queue = queue.Queue(maxsize=Config.QUEUE_MAX_SIZE)
            self.stop_event = threading.Event()
            self.state.is_running = True
            self.state.start_epoch = time.time()

            # Create producers
            self.producers = []
            for pid in range(1, Config.NUM_PRODUCERS + 1):
                p = Producer(pid, self.stream_queue, self.state, self.stop_event)
                self.producers.append(p)
                p.start()

            # Create consumers
            self.consumers = []
            for cid in range(1, Config.NUM_CONSUMERS + 1):
                c = Consumer(cid, self.stream_queue, self.state, self.stop_event,
                            self.alert_callback)
                self.consumers.append(c)
                c.start()

            # Start update thread for WebSocket emissions
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()

            self.socketio.emit('status', {'running': True})
            return True

    def stop(self) -> bool:
        """Stop the simulator."""
        with self._lock:
            if not self.state.is_running:
                return False

            self.state.is_running = False
            if self.stop_event:
                self.stop_event.set()

            # Wait for threads to finish
            for p in self.producers:
                p.join(timeout=2.0)
            for c in self.consumers:
                c.join(timeout=2.0)

            self.producers.clear()
            self.consumers.clear()
            self.stream_queue = None
            self.stop_event = None

            self.socketio.emit('status', {'running': False})
            return True

    def restart(self) -> bool:
        """Restart the simulator."""
        self.stop()
        time.sleep(0.5)
        self.state.reset()
        return self.start()

    def _update_loop(self) -> None:
        """Send periodic updates to clients via WebSocket."""
        while self.state.is_running and self.stop_event and not self.stop_event.is_set():
            snapshot = self.state.snapshot()
            snapshot['queue_size'] = self.stream_queue.qsize() if self.stream_queue else 0
            self.socketio.emit('metrics', snapshot)
            time.sleep(Config.UPDATE_INTERVAL)

    def get_snapshot(self) -> Dict:
        """Get current metrics snapshot."""
        snapshot = self.state.snapshot()
        if self.stream_queue:
            snapshot['queue_size'] = self.stream_queue.qsize()
        else:
            snapshot['queue_size'] = 0
        return snapshot


# ═══════════════════════════════════════════════════════════════════════════
#  FLASK APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global simulator controller
simulator = SimulatorController(socketio)


# HTML Template (embedded for single-file simplicity)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Event Streaming Simulator</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .title h1 {
            font-size: 28px;
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .title p {
            color: #888;
            font-size: 14px;
            margin-top: 5px;
        }

        .controls {
            display: flex;
            gap: 15px;
        }

        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .btn-start {
            background: linear-gradient(135deg, #00b4db, #0083b0);
            color: white;
        }

        .btn-start:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 180, 219, 0.4);
        }

        .btn-stop {
            background: linear-gradient(135deg, #f093fb, #f5576c);
            color: white;
        }

        .btn-stop:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(245, 87, 108, 0.4);
        }

        .btn-restart {
            background: linear-gradient(135deg, #fa709a, #fee140);
            color: #1a1a2e;
        }

        .btn-restart:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(250, 112, 154, 0.4);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }

        .status-running {
            background: rgba(0, 255, 0, 0.2);
            color: #0f0;
            border: 1px solid #0f0;
            animation: pulse 2s infinite;
        }

        .status-stopped {
            background: rgba(255, 0, 0, 0.2);
            color: #f00;
            border: 1px solid #f00;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-label {
            color: #888;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .stat-value {
            font-size: 36px;
            font-weight: bold;
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .chart-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .chart-title {
            color: #888;
            font-size: 16px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .events-panel {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .event-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            max-height: 400px;
            overflow-y: auto;
        }

        .event-card::-webkit-scrollbar {
            width: 8px;
        }

        .event-card::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }

        .event-card::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
        }

        .event-item {
            padding: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }

        .event-time {
            color: #888;
            margin-right: 10px;
        }

        .event-success {
            color: #0f0;
        }

        .event-failure {
            color: #f00;
        }

        .alert-item {
            padding: 10px;
            margin-bottom: 5px;
            background: rgba(255, 0, 0, 0.1);
            border-left: 3px solid #f00;
            border-radius: 5px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                transform: translateX(-20px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .alert-time {
            color: #888;
            font-size: 12px;
            margin-right: 10px;
        }

        .alert-message {
            color: #f00;
            font-weight: 600;
        }

        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 15px;
            }

            .events-panel {
                grid-template-columns: 1fr;
            }

            .charts-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">
                <h1>🚀 Security Event Streaming Simulator</h1>
                <p>Real-time security event monitoring and anomaly detection</p>
            </div>
            <div class="controls">
                <button class="btn btn-start" id="btn-start" onclick="startSimulator()">▶ Start</button>
                <button class="btn btn-stop" id="btn-stop" onclick="stopSimulator()" disabled>⏹ Stop</button>
                <button class="btn btn-restart" id="btn-restart" onclick="restartSimulator()" disabled>🔄 Restart</button>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Status</div>
                <div class="stat-value" id="status-display">
                    <span class="status-badge status-stopped" id="status-badge">STOPPED</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Uptime</div>
                <div class="stat-value" id="uptime">00:00:00</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Events Produced</div>
                <div class="stat-value" id="produced">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Events Consumed</div>
                <div class="stat-value" id="consumed">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Queue Size</div>
                <div class="stat-value" id="queue-size">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Alerts Fired</div>
                <div class="stat-value" id="alerts">0</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title">Events by Type</div>
                <canvas id="typeChart"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title">Events by Severity</div>
                <canvas id="severityChart"></canvas>
            </div>
        </div>

        <div class="events-panel">
            <div class="event-card">
                <div class="chart-title">📋 Live Events</div>
                <div id="event-log"></div>
            </div>
            <div class="event-card">
                <div class="chart-title">🚨 Alerts</div>
                <div id="alert-log"></div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let typeChart, severityChart;

        // Initialize charts
        function initCharts() {
            const typeCtx = document.getElementById('typeChart').getContext('2d');
            const severityCtx = document.getElementById('severityChart').getContext('2d');

            typeChart = new Chart(typeCtx, {
                type: 'doughnut',
                data: {
                    labels: ['login', 'request', 'error', 'alert', 'scan', 'transfer'],
                    datasets: [{
                        data: [0, 0, 0, 0, 0, 0],
                        backgroundColor: [
                            '#00d2ff', '#3a7bd5', '#f093fb', '#f5576c', '#fa709a', '#fee140'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            labels: { color: '#eee' }
                        }
                    }
                }
            });

            severityChart = new Chart(severityCtx, {
                type: 'bar',
                data: {
                    labels: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
                    datasets: [{
                        label: 'Events',
                        data: [0, 0, 0, 0],
                        backgroundColor: ['#00d2ff', '#3a7bd5', '#f093fb', '#f5576c']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            labels: { color: '#eee' }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            ticks: { color: '#eee' }
                        },
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            ticks: { color: '#eee' }
                        }
                    }
                }
            });
        }

        // Socket event handlers
        socket.on('connect', () => {
            console.log('Connected to server');
        });

        socket.on('metrics', (data) => {
            updateDisplay(data);
        });

        socket.on('alert', (alert) => {
            addAlert(alert);
        });

        socket.on('status', (data) => {
            updateButtonStates(data.running);
            updateStatusBadge(data.running);
        });

        // Update functions
        function updateDisplay(data) {
            document.getElementById('produced').textContent = data.produced.toLocaleString();
            document.getElementById('consumed').textContent = data.consumed.toLocaleString();
            document.getElementById('queue-size').textContent = data.queue_size;
            document.getElementById('alerts').textContent = data.alerts.toLocaleString();
            
            const uptime = formatUptime(data.uptime);
            document.getElementById('uptime').textContent = uptime;

            // Update charts
            if (typeChart) {
                typeChart.data.datasets[0].data = [
                    data.by_type.login || 0,
                    data.by_type.request || 0,
                    data.by_type.error || 0,
                    data.by_type.alert || 0,
                    data.by_type.scan || 0,
                    data.by_type.transfer || 0
                ];
                typeChart.update();
            }

            if (severityChart) {
                severityChart.data.datasets[0].data = [
                    data.by_sev.LOW || 0,
                    data.by_sev.MEDIUM || 0,
                    data.by_sev.HIGH || 0,
                    data.by_sev.CRITICAL || 0
                ];
                severityChart.update();
            }

            // Update event log
            updateEventLog(data.event_log || []);
            updateAlertLog(data.alert_log || []);
        }

        function formatUptime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }

        function updateEventLog(events) {
            const container = document.getElementById('event-log');
            container.innerHTML = events.slice(-15).reverse().map(e => {
                const statusClass = e.status === 'success' ? 'event-success' : 'event-failure';
                return `<div class="event-item">
                    <span class="event-time">${e.timestamp}</span>
                    <span>P${e.producer_id}</span>
                    <span style="margin-left: 10px; color: #00d2ff;">${e.source_ip}</span>
                    <span style="margin-left: 10px;">${e.event_type}</span>
                    <span class="${statusClass}" style="margin-left: 10px;">${e.status}</span>
                    <span style="margin-left: 10px; color: #888;">${e.severity}</span>
                </div>`;
            }).join('');
        }

        function updateAlertLog(alerts) {
            const container = document.getElementById('alert-log');
            container.innerHTML = alerts.slice(-10).reverse().map(a => `
                <div class="alert-item">
                    <span class="alert-time">${a.timestamp}</span>
                    <span class="alert-message">${a.message}</span>
                </div>
            `).join('');
        }

        function addAlert(alert) {
            const container = document.getElementById('alert-log');
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert-item';
            alertDiv.innerHTML = `
                <span class="alert-time">${alert.timestamp}</span>
                <span class="alert-message">${alert.message}</span>
            `;
            container.insertBefore(alertDiv, container.firstChild);
            
            // Keep only last 10 alerts
            while (container.children.length > 10) {
                container.removeChild(container.lastChild);
            }
        }

        function updateButtonStates(running) {
            document.getElementById('btn-start').disabled = running;
            document.getElementById('btn-stop').disabled = !running;
            document.getElementById('btn-restart').disabled = !running;
        }

        function updateStatusBadge(running) {
            const badge = document.getElementById('status-badge');
            badge.className = running ? 'status-badge status-running' : 'status-badge status-stopped';
            badge.textContent = running ? 'RUNNING' : 'STOPPED';
        }

        // Control functions
        function startSimulator() {
            fetch('/api/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert('Failed to start simulator');
                    }
                });
        }

        function stopSimulator() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert('Failed to stop simulator');
                    }
                });
        }

        function restartSimulator() {
            fetch('/api/restart', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert('Failed to restart simulator');
                    }
                });
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {
            initCharts();
            
            // Get initial status
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateButtonStates(data.running);
                    updateStatusBadge(data.running);
                    updateDisplay(data);
                });
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Serve the main dashboard page."""
    return HTML_TEMPLATE


@app.route('/api/status')
def api_status():
    """Get current simulator status."""
    snapshot = simulator.get_snapshot()
    return jsonify(snapshot)


@app.route('/api/start', methods=['POST'])
def api_start():
    """Start the simulator."""
    success = simulator.start()
    return jsonify({'success': success, 'running': simulator.state.is_running})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop the simulator."""
    success = simulator.stop()
    return jsonify({'success': success, 'running': simulator.state.is_running})


@app.route('/api/restart', methods=['POST'])
def api_restart():
    """Restart the simulator."""
    success = simulator.restart()
    return jsonify({'success': success, 'running': simulator.state.is_running})


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    snapshot = simulator.get_snapshot()
    emit('metrics', snapshot)
    emit('status', {'running': simulator.state.is_running})


def cleanup():
    """Clean up on exit."""
    simulator.stop()


def main():
    """Main entry point."""
    atexit.register(cleanup)

    print("\n" + "="*60)
    print("🚀 Security Event Streaming Simulator - Web Interface")
    print("="*60)
    print(f"📍 Access the dashboard at: http://localhost:5000")
    print(f"🛑 Press Ctrl+C to stop the server")
    print("="*60 + "\n")

    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down server...")
        cleanup()


if __name__ == '__main__':
    # Install Flask-SocketIO if not already installed
    try:
        from flask_socketio import SocketIO
    except ImportError:
        print("Installing required packages...")
        os.system(f"{sys.executable} -m pip install flask flask-socketio")
        from flask_socketio import SocketIO

    main()