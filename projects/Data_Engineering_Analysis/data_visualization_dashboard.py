"""
data_visualization_dashboard.py
================================
A real-time security-log visualization dashboard built with Flask + Chart.js.
All HTML/CSS/JS is embedded via render_template_string — no external files needed.

Run:
    python data_visualization_dashboard.py

Then open:
    http://127.0.0.1:5000
"""

import json
import random
import threading
import time
import math
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, jsonify, render_template_string


# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

class Config:
    HOST              = "127.0.0.1"
    PORT              = 5000
    DEBUG             = False
    MAX_EVENTS        = 500          # rolling window kept in memory
    GENERATE_INTERVAL = 1.5          # seconds between new events
    EVENTS_PER_TICK   = (1, 4)       # min/max events generated each tick
    HISTORY_HOURS     = 6            # hours of pre-seeded history on startup


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LAYER  –  event store + generator
# ═══════════════════════════════════════════════════════════════════════════

EVENT_TYPES   = ["login", "request", "error", "alert"]
STATUSES      = ["success", "failure"]
STATUS_WEIGHTS = [0.68, 0.32]

# A pool of IPs that makes "repeat offender" patterns visible in the UI
_IP_POOL = (
    [f"10.0.{r}.{h}"    for r in range(4) for h in [12, 45, 88, 120, 200]]
  + [f"192.168.{r}.{h}" for r in range(3) for h in [5, 77, 142]]
  + ["45.33.32.156", "198.51.100.23", "185.220.101.5", "203.0.113.8"]
)

_event_lock  = threading.Lock()
_event_store : list = []          # list of dicts, newest last
_event_id    = 0


def _next_id() -> int:
    global _event_id
    _event_id += 1
    return _event_id


def _make_event(ts: datetime | None = None) -> dict:
    """Create a single random security event dict."""
    etype  = random.choice(EVENT_TYPES)
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

    if etype in ("error", "alert") or status == "failure":
        severity = random.choices(
            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            weights=[15, 40, 32, 13], k=1)[0]
    else:
        severity = random.choices(
            ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            weights=[60, 28, 9, 3], k=1)[0]

    now = ts or datetime.now()
    return {
        "id"        : _next_id(),
        "timestamp" : now.strftime("%Y-%m-%dT%H:%M:%S"),
        "time_label": now.strftime("%H:%M:%S"),
        "date_label": now.strftime("%Y-%m-%d"),
        "hour"      : now.strftime("%H:00"),
        "event_type": etype,
        "status"    : status,
        "severity"  : severity,
        "source_ip" : random.choice(_IP_POOL),
        "bytes"     : random.randint(128, 65536),
        "duration_ms": random.randint(5, 2500),
    }


def _seed_history() -> None:
    """Pre-populate the store with several hours of simulated history."""
    now    = datetime.now()
    events = []
    for minutes_ago in range(Config.HISTORY_HOURS * 60, 0, -1):
        ts    = now - timedelta(minutes=minutes_ago)
        count = random.randint(1, 6)
        for _ in range(count):
            events.append(_make_event(ts))
    with _event_lock:
        _event_store.extend(events[-Config.MAX_EVENTS:])


def _background_generator() -> None:
    """Daemon thread: continuously appends fresh events to the store."""
    while True:
        time.sleep(Config.GENERATE_INTERVAL)
        lo, hi = Config.EVENTS_PER_TICK
        batch  = [_make_event() for _ in range(random.randint(lo, hi))]
        with _event_lock:
            _event_store.extend(batch)
            # Keep rolling window bounded
            excess = len(_event_store) - Config.MAX_EVENTS
            if excess > 0:
                del _event_store[:excess]


# ═══════════════════════════════════════════════════════════════════════════
#  FLASK APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ── API: raw events ────────────────────────────────────────────────────────

@app.route("/data")
def api_data():
    """Return the most recent 100 events as JSON."""
    with _event_lock:
        recent = list(_event_store[-100:])
    return jsonify({"events": recent, "count": len(recent)})


# ── API: aggregated statistics ─────────────────────────────────────────────

@app.route("/stats")
def api_stats():
    """
    Compute and return all aggregates needed by the dashboard charts:
      - counts by event type
      - counts by status
      - counts by severity
      - events per hour (line chart)
      - top source IPs
      - summary KPIs
    """
    with _event_lock:
        events = list(_event_store)   # snapshot under lock

    if not events:
        return jsonify({})

    by_type     = defaultdict(int)
    by_status   = defaultdict(int)
    by_severity = defaultdict(int)
    by_hour     = defaultdict(int)
    by_ip       = defaultdict(int)
    total = errors = alerts = failures = critical = 0

    for e in events:
        by_type    [e["event_type"]] += 1
        by_status  [e["status"]]     += 1
        by_severity[e["severity"]]   += 1
        by_hour    [e["hour"]]       += 1
        by_ip      [e["source_ip"]]  += 1
        total += 1
        if e["event_type"] == "error":   errors   += 1
        if e["event_type"] == "alert":   alerts   += 1
        if e["status"]     == "failure": failures += 1
        if e["severity"]   == "CRITICAL": critical += 1

    # Sort hours chronologically for the line chart
    sorted_hours  = sorted(by_hour.keys())
    hour_labels   = sorted_hours
    hour_values   = [by_hour[h] for h in sorted_hours]

    # Top 8 IPs by event count
    top_ips = sorted(by_ip.items(), key=lambda x: -x[1])[:8]

    # Last 20 events for the live feed table (newest first)
    recent_feed = list(reversed(events[-20:]))

    return jsonify({
        "kpis": {
            "total"   : total,
            "errors"  : errors,
            "alerts"  : alerts,
            "failures": failures,
            "critical": critical,
            "failure_rate": round(failures / total * 100, 1) if total else 0,
        },
        "by_type"    : dict(by_type),
        "by_status"  : dict(by_status),
        "by_severity": dict(by_severity),
        "timeline"   : {"labels": hour_labels, "values": hour_values},
        "top_ips"    : [{"ip": ip, "count": c} for ip, c in top_ips],
        "feed"       : recent_feed,
    })


# ── Main page ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


# ═══════════════════════════════════════════════════════════════════════════
#  EMBEDDED DASHBOARD  (HTML / CSS / JS)
# ═══════════════════════════════════════════════════════════════════════════

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>SecureWatch — Live Security Dashboard</title>

<!-- Chart.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<!-- Google Fonts: Space Mono (monospace identity) + Syne (display) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">

<style>
/* ── Design tokens ─────────────────────────────────────────── */
:root {
  --bg-base      : #080c12;
  --bg-panel     : #0d1320;
  --bg-card      : #111927;
  --bg-hover     : #162030;
  --border       : #1e2d42;
  --border-bright: #2a4060;

  --accent-cyan  : #00e5ff;
  --accent-green : #00ff9d;
  --accent-red   : #ff3b5c;
  --accent-amber : #ffb800;
  --accent-purple: #c084fc;
  --accent-blue  : #4da6ff;

  --text-primary : #e2eaf4;
  --text-secondary: #7a96b8;
  --text-dim     : #3a5272;

  --font-display : 'Syne', sans-serif;
  --font-mono    : 'Space Mono', monospace;

  --radius       : 10px;
  --radius-sm    : 6px;
  --shadow       : 0 4px 32px rgba(0,0,0,.6);
}

/* ── Reset / base ──────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 14px; }
body {
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-mono);
  min-height: 100vh;
  overflow-x: hidden;
}

/* Subtle scanline texture */
body::before {
  content: '';
  position: fixed; inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,229,255,.012) 2px,
    rgba(0,229,255,.012) 4px
  );
  pointer-events: none;
  z-index: 1000;
}

/* ── Header ────────────────────────────────────────────────── */
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 28px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}
.logo {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 1.35rem;
  letter-spacing: .04em;
  color: var(--accent-cyan);
  text-shadow: 0 0 20px rgba(0,229,255,.4);
}
.logo span { color: var(--text-secondary); font-weight: 400; }
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.live-badge {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: .75rem;
  color: var(--accent-green);
  letter-spacing: .08em;
  text-transform: uppercase;
}
.pulse-dot {
  width: 8px; height: 8px;
  background: var(--accent-green);
  border-radius: 50%;
  animation: pulse 1.6s ease-in-out infinite;
  box-shadow: 0 0 6px var(--accent-green);
}
@keyframes pulse {
  0%,100% { opacity: 1; transform: scale(1); }
  50%      { opacity: .4; transform: scale(1.4); }
}
#clock {
  font-size: .78rem;
  color: var(--text-secondary);
  letter-spacing: .06em;
}
.refresh-info {
  font-size: .7rem;
  color: var(--text-dim);
}

/* ── Layout ────────────────────────────────────────────────── */
main { padding: 24px 28px 40px; max-width: 1600px; margin: 0 auto; }

/* ── KPI strip ─────────────────────────────────────────────── */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 22px;
}
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
  transition: border-color .25s, transform .2s;
}
.kpi-card:hover { border-color: var(--border-bright); transform: translateY(-2px); }
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: var(--accent);
  opacity: .8;
}
.kpi-card[data-accent="cyan"]    { --accent: var(--accent-cyan); }
.kpi-card[data-accent="green"]   { --accent: var(--accent-green); }
.kpi-card[data-accent="red"]     { --accent: var(--accent-red); }
.kpi-card[data-accent="amber"]   { --accent: var(--accent-amber); }
.kpi-card[data-accent="purple"]  { --accent: var(--accent-purple); }
.kpi-label {
  font-size: .68rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.kpi-value {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
  text-shadow: 0 0 18px color-mix(in srgb, var(--accent) 30%, transparent);
  transition: all .4s;
}
.kpi-sub {
  font-size: .67rem;
  color: var(--text-dim);
  margin-top: 8px;
  letter-spacing: .05em;
}

/* ── Chart grid ────────────────────────────────────────────── */
.chart-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.chart-grid-bottom {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.panel-title {
  font-family: var(--font-display);
  font-size: .88rem;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--text-secondary);
}
.panel-badge {
  font-size: .65rem;
  letter-spacing: .08em;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 99px;
  background: rgba(0,229,255,.08);
  color: var(--accent-cyan);
  border: 1px solid rgba(0,229,255,.2);
}

/* Chart canvases */
.chart-wrap { position: relative; }
.chart-wrap canvas { display: block; }

/* ── Top IPs table ─────────────────────────────────────────── */
.ip-table { width: 100%; border-collapse: collapse; }
.ip-table th {
  font-size: .65rem;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--text-dim);
  text-align: left;
  padding: 0 0 10px 0;
  border-bottom: 1px solid var(--border);
}
.ip-table td {
  padding: 9px 0;
  font-size: .78rem;
  border-bottom: 1px solid rgba(30,45,66,.5);
  vertical-align: middle;
}
.ip-table tr:last-child td { border-bottom: none; }
.ip-bar-wrap {
  width: 100px;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}
.ip-bar-fill {
  height: 100%;
  background: var(--accent-cyan);
  border-radius: 2px;
  transition: width .5s ease;
  box-shadow: 0 0 6px var(--accent-cyan);
}
.ip-mono { font-family: var(--font-mono); color: var(--text-primary); }
.ip-count { color: var(--accent-cyan); font-family: var(--font-display); font-weight: 700; }

/* ── Live event feed ───────────────────────────────────────── */
.feed-table { width: 100%; border-collapse: collapse; font-size: .74rem; }
.feed-table th {
  font-size: .63rem;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--text-dim);
  text-align: left;
  padding: 0 10px 10px 0;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.feed-table td {
  padding: 8px 10px 8px 0;
  border-bottom: 1px solid rgba(30,45,66,.4);
  vertical-align: middle;
  white-space: nowrap;
}
.feed-table tbody tr {
  transition: background .2s;
}
.feed-table tbody tr:hover { background: var(--bg-hover); }
.feed-table tbody tr.new-row {
  animation: rowIn .4s ease forwards;
}
@keyframes rowIn {
  from { opacity: 0; transform: translateX(-8px); background: rgba(0,229,255,.06); }
  to   { opacity: 1; transform: translateX(0);    background: transparent; }
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: .65rem;
  letter-spacing: .06em;
  font-weight: 700;
  text-transform: uppercase;
}
.badge-success  { background: rgba(0,255,157,.12); color: var(--accent-green);  border: 1px solid rgba(0,255,157,.25); }
.badge-failure  { background: rgba(255,59,92,.12);  color: var(--accent-red);    border: 1px solid rgba(255,59,92,.25); }
.badge-login    { background: rgba(77,166,255,.1);  color: var(--accent-blue);   border: 1px solid rgba(77,166,255,.2); }
.badge-request  { background: rgba(0,229,255,.08);  color: var(--accent-cyan);   border: 1px solid rgba(0,229,255,.18); }
.badge-error    { background: rgba(255,184,0,.1);   color: var(--accent-amber);  border: 1px solid rgba(255,184,0,.2); }
.badge-alert    { background: rgba(192,132,252,.12);color: var(--accent-purple); border: 1px solid rgba(192,132,252,.25); }
.sev-low      { color: var(--text-secondary); }
.sev-medium   { color: var(--accent-amber); }
.sev-high     { color: var(--accent-red); }
.sev-critical { color: var(--accent-red); font-weight: 700;
                text-shadow: 0 0 8px rgba(255,59,92,.5); }
.mono { font-family: var(--font-mono); color: var(--text-secondary); }

/* ── Status bar ────────────────────────────────────────────── */
footer {
  border-top: 1px solid var(--border);
  padding: 10px 28px;
  font-size: .68rem;
  color: var(--text-dim);
  display: flex;
  justify-content: space-between;
  letter-spacing: .06em;
}

/* ── Scrollbar ─────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 3px; }
</style>
</head>

<body>

<!-- ─── Header ──────────────────────────────────────────────────────────── -->
<header>
  <div class="logo">Secure<span>Watch</span></div>
  <div class="header-right">
    <div class="live-badge"><div class="pulse-dot"></div>Live</div>
    <div id="clock">--:--:--</div>
    <div class="refresh-info">↻ auto-refresh 3s</div>
  </div>
</header>

<!-- ─── Main ────────────────────────────────────────────────────────────── -->
<main>

  <!-- KPI strip -->
  <div class="kpi-strip">
    <div class="kpi-card" data-accent="cyan">
      <div class="kpi-label">Total Events</div>
      <div class="kpi-value" id="kpi-total">—</div>
      <div class="kpi-sub">rolling window</div>
    </div>
    <div class="kpi-card" data-accent="red">
      <div class="kpi-label">Errors</div>
      <div class="kpi-value" id="kpi-errors">—</div>
      <div class="kpi-sub">event_type = error</div>
    </div>
    <div class="kpi-card" data-accent="amber">
      <div class="kpi-label">Alerts</div>
      <div class="kpi-value" id="kpi-alerts">—</div>
      <div class="kpi-sub">event_type = alert</div>
    </div>
    <div class="kpi-card" data-accent="purple">
      <div class="kpi-label">Failures</div>
      <div class="kpi-value" id="kpi-failures">—</div>
      <div class="kpi-sub" id="kpi-failure-rate">—% failure rate</div>
    </div>
    <div class="kpi-card" data-accent="green">
      <div class="kpi-label">Critical</div>
      <div class="kpi-value" id="kpi-critical">—</div>
      <div class="kpi-sub">severity = CRITICAL</div>
    </div>
  </div>

  <!-- Top row: line chart (wide) + bar + pie -->
  <div class="chart-grid">
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Events Over Time</span>
        <span class="panel-badge">Hourly</span>
      </div>
      <div class="chart-wrap" style="height:220px">
        <canvas id="chartLine"></canvas>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">By Event Type</span>
        <span class="panel-badge">Count</span>
      </div>
      <div class="chart-wrap" style="height:220px">
        <canvas id="chartBar"></canvas>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Status Split</span>
        <span class="panel-badge">Ratio</span>
      </div>
      <div class="chart-wrap" style="height:220px">
        <canvas id="chartPie"></canvas>
      </div>
    </div>
  </div>

  <!-- Middle row: severity doughnut + top IPs -->
  <div class="chart-grid-bottom">
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Severity Distribution</span>
        <span class="panel-badge">Doughnut</span>
      </div>
      <div class="chart-wrap" style="height:200px">
        <canvas id="chartSeverity"></canvas>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Top Source IPs</span>
        <span class="panel-badge">By Volume</span>
      </div>
      <div style="overflow-y:auto; max-height:220px;">
        <table class="ip-table">
          <thead>
            <tr>
              <th>IP Address</th>
              <th>Events</th>
              <th style="width:110px">Share</th>
            </tr>
          </thead>
          <tbody id="ip-tbody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Live feed -->
  <div class="panel">
    <div class="panel-header">
      <span class="panel-title">Live Event Feed</span>
      <span class="panel-badge" id="feed-count">0 events</span>
    </div>
    <div style="overflow-x:auto;">
      <table class="feed-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Time</th>
            <th>Source IP</th>
            <th>Event Type</th>
            <th>Status</th>
            <th>Severity</th>
            <th>Bytes</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody id="feed-tbody"></tbody>
      </table>
    </div>
  </div>

</main>

<footer>
  <span>SecureWatch Dashboard  ·  Flask + Chart.js  ·  Pure Python</span>
  <span id="footer-ts">Last updated: —</span>
</footer>

<!-- ─── JavaScript ───────────────────────────────────────────────────────── -->
<script>
/* ── Chart.js global defaults ──────────────────────────────── */
Chart.defaults.color          = '#7a96b8';
Chart.defaults.font.family    = "'Space Mono', monospace";
Chart.defaults.font.size      = 11;
Chart.defaults.plugins.legend.display = false;

const CYAN   = '#00e5ff';
const GREEN  = '#00ff9d';
const RED    = '#ff3b5c';
const AMBER  = '#ffb800';
const PURPLE = '#c084fc';
const BLUE   = '#4da6ff';
const DIM    = '#1e2d42';

/* Gradient helper */
function linearGrad(ctx, color, alpha1 = .55, alpha2 = .02) {
  const g = ctx.createLinearGradient(0, 0, 0, 300);
  const hex2rgb = h => [
    parseInt(h.slice(1,3),16),
    parseInt(h.slice(3,5),16),
    parseInt(h.slice(5,7),16),
  ];
  const [r,g2,b] = hex2rgb(color);
  g.addColorStop(0, `rgba(${r},${g2},${b},${alpha1})`);
  g.addColorStop(1, `rgba(${r},${g2},${b},${alpha2})`);
  return g;
}

/* ── Chart: Line (events over time) ───────────────────────── */
const ctxLine = document.getElementById('chartLine').getContext('2d');
const chartLine = new Chart(ctxLine, {
  type: 'line',
  data: { labels: [], datasets: [{
    label: 'Events',
    data: [],
    borderColor: CYAN,
    borderWidth: 2,
    pointRadius: 3,
    pointBackgroundColor: CYAN,
    pointBorderColor: '#080c12',
    pointBorderWidth: 2,
    tension: 0.4,
    fill: true,
    backgroundColor: linearGrad(ctxLine, '#00e5ff'),
  }]},
  options: {
    responsive: true, maintainAspectRatio: false,
    animation: { duration: 600 },
    scales: {
      x: { grid: { color: DIM }, ticks: { maxTicksLimit: 8, maxRotation: 0 } },
      y: { grid: { color: DIM }, beginAtZero: true,
           ticks: { precision: 0 } },
    },
    plugins: { tooltip: { callbacks: {
      label: ctx => ` ${ctx.parsed.y} events`
    }}},
  }
});

/* ── Chart: Bar (by event type) ────────────────────────────── */
const ctxBar = document.getElementById('chartBar').getContext('2d');
const chartBar = new Chart(ctxBar, {
  type: 'bar',
  data: { labels: [], datasets: [{
    label: 'Count',
    data: [],
    backgroundColor: [BLUE, CYAN, AMBER, PURPLE],
    borderRadius: 5,
    borderSkipped: false,
  }]},
  options: {
    responsive: true, maintainAspectRatio: false,
    animation: { duration: 500 },
    scales: {
      x: { grid: { display: false } },
      y: { grid: { color: DIM }, beginAtZero: true, ticks: { precision: 0 } },
    },
  }
});

/* ── Chart: Pie (success vs failure) ──────────────────────── */
const ctxPie = document.getElementById('chartPie').getContext('2d');
const chartPie = new Chart(ctxPie, {
  type: 'doughnut',
  data: { labels: ['Success', 'Failure'], datasets: [{
    data: [],
    backgroundColor: [GREEN, RED],
    borderColor: '#0d1320',
    borderWidth: 3,
    hoverOffset: 8,
  }]},
  options: {
    responsive: true, maintainAspectRatio: false,
    cutout: '65%',
    animation: { duration: 600 },
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: { padding: 16, usePointStyle: true, pointStyleWidth: 10 },
      },
      tooltip: { callbacks: {
        label: ctx => {
          const total = ctx.dataset.data.reduce((a,b)=>a+b,0);
          const pct   = total ? (ctx.parsed / total * 100).toFixed(1) : 0;
          return ` ${ctx.label}: ${ctx.parsed} (${pct}%)`;
        }
      }},
    },
  }
});

/* ── Chart: Severity doughnut ──────────────────────────────── */
const ctxSev = document.getElementById('chartSeverity').getContext('2d');
const chartSeverity = new Chart(ctxSev, {
  type: 'doughnut',
  data: {
    labels: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
    datasets: [{
      data: [],
      backgroundColor: ['#2a4060', AMBER, RED, '#ff0040'],
      borderColor: '#0d1320',
      borderWidth: 3,
      hoverOffset: 8,
    }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    cutout: '60%',
    animation: { duration: 600 },
    plugins: {
      legend: {
        display: true, position: 'right',
        labels: { padding: 14, usePointStyle: true, pointStyleWidth: 10 },
      },
    },
  }
});

/* ── KPI updater ─────────────────────────────────────────────── */
let prevTotal = 0;
function updateKPIs(kpis) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el && el.textContent !== String(val)) {
      el.textContent = val;
      el.style.transition = 'none';
      el.style.opacity = '.4';
      requestAnimationFrame(() => {
        el.style.transition = 'opacity .35s';
        el.style.opacity = '1';
      });
    }
  };
  set('kpi-total',    kpis.total);
  set('kpi-errors',   kpis.errors);
  set('kpi-alerts',   kpis.alerts);
  set('kpi-failures', kpis.failures);
  set('kpi-critical', kpis.critical);
  const rateEl = document.getElementById('kpi-failure-rate');
  if (rateEl) rateEl.textContent = `${kpis.failure_rate}% failure rate`;
}

/* ── Top IPs updater ─────────────────────────────────────────── */
function updateIPs(ips) {
  const tbody  = document.getElementById('ip-tbody');
  const maxCnt = ips.length ? ips[0].count : 1;
  tbody.innerHTML = ips.map(({ip, count}) => {
    const pct = Math.round(count / maxCnt * 100);
    return `<tr>
      <td class="ip-mono">${ip}</td>
      <td class="ip-count">${count}</td>
      <td><div class="ip-bar-wrap"><div class="ip-bar-fill" style="width:${pct}%"></div></div></td>
    </tr>`;
  }).join('');
}

/* ── Live feed updater ───────────────────────────────────────── */
let lastFeedId = 0;
const SEV_CLASS  = { LOW:'sev-low', MEDIUM:'sev-medium', HIGH:'sev-high', CRITICAL:'sev-critical' };
const TYPE_CLASS = { login:'login', request:'request', error:'error', alert:'alert' };

function updateFeed(events) {
  const tbody  = document.getElementById('feed-tbody');
  const countEl = document.getElementById('feed-count');
  if (countEl) countEl.textContent = `${events.length} events`;

  // Only prepend truly new rows
  const newRows = events.filter(e => e.id > lastFeedId);
  if (!newRows.length) return;
  lastFeedId = Math.max(...newRows.map(e => e.id));

  const html = newRows.map(e => `
    <tr class="new-row">
      <td class="mono" style="color:var(--text-dim)">#${e.id}</td>
      <td class="mono">${e.time_label}</td>
      <td class="mono" style="font-size:.7rem">${e.source_ip}</td>
      <td><span class="badge badge-${TYPE_CLASS[e.event_type]||'request'}">${e.event_type}</span></td>
      <td><span class="badge badge-${e.status}">${e.status}</span></td>
      <td class="${SEV_CLASS[e.severity]||''}">${e.severity}</td>
      <td class="mono" style="color:var(--text-secondary)">${(e.bytes/1024).toFixed(1)}K</td>
      <td class="mono" style="color:var(--text-secondary)">${e.duration_ms}ms</td>
    </tr>`).join('');

  tbody.insertAdjacentHTML('afterbegin', html);

  // Keep table bounded to 30 rows
  while (tbody.rows.length > 30) tbody.deleteRow(tbody.rows.length - 1);
}

/* ── Main fetch + render ─────────────────────────────────────── */
async function refresh() {
  try {
    const res  = await fetch('/stats');
    const data = await res.json();
    if (!data.kpis) return;

    updateKPIs(data.kpis);

    // Line chart
    chartLine.data.labels             = data.timeline.labels;
    chartLine.data.datasets[0].data   = data.timeline.values;
    chartLine.update('none');

    // Bar chart
    const typeOrder = ['login','request','error','alert'];
    chartBar.data.labels           = typeOrder;
    chartBar.data.datasets[0].data = typeOrder.map(t => data.by_type[t] || 0);
    chartBar.update('none');

    // Pie
    chartPie.data.datasets[0].data = [
      data.by_status.success || 0,
      data.by_status.failure || 0,
    ];
    chartPie.update('none');

    // Severity doughnut
    chartSeverity.data.datasets[0].data = [
      data.by_severity.LOW      || 0,
      data.by_severity.MEDIUM   || 0,
      data.by_severity.HIGH     || 0,
      data.by_severity.CRITICAL || 0,
    ];
    chartSeverity.update('none');

    updateIPs(data.top_ips   || []);
    updateFeed(data.feed     || []);

    const tsEl = document.getElementById('footer-ts');
    if (tsEl) tsEl.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
  } catch (err) {
    console.warn('Refresh failed:', err);
  }
}

/* ── Clock ───────────────────────────────────────────────────── */
function tickClock() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('en-GB', {hour12: false});
}

/* ── Boot ────────────────────────────────────────────────────── */
refresh();
tickClock();
setInterval(refresh,   3000);
setInterval(tickClock, 1000);
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════
#  STARTUP
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 1. Seed historical data so charts are populated immediately on load
    print("[*] Seeding historical event data …")
    _seed_history()
    print(f"[*] Seeded {len(_event_store)} events.")

    # 2. Start background generator in a daemon thread
    gen_thread = threading.Thread(target=_background_generator, daemon=True, name="EventGenerator")
    gen_thread.start()
    print(f"[*] Event generator started (every {Config.GENERATE_INTERVAL}s).")

    # 3. Launch Flask
    print(f"[*] Dashboard → http://{Config.HOST}:{Config.PORT}")
    print("[*] Press Ctrl+C to stop.\n")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=False,   # reloader conflicts with the generator thread
    )