"""
============================================================
  Browser Fingerprinting Educational Lab
  ----------------------------------------
  Author  : Senior Python / Cybersecurity Instructor
  Purpose : Demonstrate browser fingerprinting transparently
  Run     : python browser_fingerprinting_lab.py
  Access  : http://127.0.0.1:5000
============================================================

ETHICS NOTICE
-------------
- No data is stored, shared, or transmitted externally.
- All processing happens in memory on localhost only.
- This tool is strictly for educational demonstration.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import hashlib
import json
import logging
from datetime import datetime

from flask import Flask, request, render_template_string, jsonify

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------
app = Flask(__name__)

# Configure structured terminal logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fingerprint-lab")

# ---------------------------------------------------------------------------
# Fingerprint Utilities
# ---------------------------------------------------------------------------

def generate_fingerprint(data: dict) -> str:
    """
    Create a short SHA-256 fingerprint from a dictionary of browser attributes.
    Only non-null values are included so that the hash reflects meaningful data.
    """
    meaningful = {k: v for k, v in data.items() if v not in (None, "", "unknown")}
    raw = json.dumps(meaningful, sort_keys=True)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return digest[:16].upper()          # Readable 16-char prefix


def extract_server_data(req) -> dict:
    """
    Extract fingerprint attributes available on the server side via HTTP headers.
    Returns a dict with keys: ip, user_agent, language, platform, dnt.
    """
    # Respect X-Forwarded-For for completeness, but this is localhost only
    ip = req.headers.get("X-Forwarded-For", req.remote_addr)

    user_agent   = req.headers.get("User-Agent",       "unknown")
    language     = req.headers.get("Accept-Language",  "unknown")
    platform     = req.headers.get("Sec-CH-UA-Platform", "").strip('"') or "unknown"
    dnt          = req.headers.get("DNT", "not set")   # Do-Not-Track header

    return {
        "ip":          ip,
        "user_agent":  user_agent,
        "language":    language,
        "platform":    platform,
        "dnt":         dnt,
    }


def log_fingerprint(server_data: dict, fp_id: str, privacy_mode: bool) -> None:
    """
    Print collected data to the terminal in a readable format.
    This replaces any database write — data lives only in this log line.
    """
    mode_label = "PRIVACY" if privacy_mode else "NORMAL"
    logger.info(
        "New visit | mode=%-7s | fp=%-16s | ip=%-15s | ua=%.60s",
        mode_label, fp_id,
        server_data.get("ip", "?"),
        server_data.get("user_agent", "?"),
    )


# ---------------------------------------------------------------------------
# HTML Template (render_template_string — no external files needed)
# ---------------------------------------------------------------------------

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Browser Fingerprinting — Educational Lab</title>
  <style>
    /* ── Reset & Base ── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:        #0d1117;
      --surface:   #161b22;
      --border:    #30363d;
      --accent:    #58a6ff;
      --warn:      #f0883e;
      --ok:        #3fb950;
      --danger:    #ff7b72;
      --text:      #c9d1d9;
      --muted:     #8b949e;
      --radius:    8px;
      --mono:      "Fira Mono", "Courier New", monospace;
    }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 15px;
      line-height: 1.6;
      padding: 2rem 1rem;
    }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }

    /* ── Layout ── */
    .container { max-width: 860px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 2rem; }
    header h1 { font-size: 1.9rem; color: var(--accent); letter-spacing: .5px; }
    header p  { color: var(--muted); margin-top: .4rem; }

    /* ── Ethics Banner ── */
    .ethics-banner {
      background: #1c2a1c;
      border: 1px solid var(--ok);
      border-left: 4px solid var(--ok);
      border-radius: var(--radius);
      padding: 1rem 1.2rem;
      margin-bottom: 1.8rem;
      font-size: .9rem;
      color: #b4e6b4;
    }
    .ethics-banner strong { color: var(--ok); }

    /* ── Mode Toggle ── */
    .toggle-row {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.8rem;
      flex-wrap: wrap;
    }
    .toggle-label { font-size: .85rem; color: var(--muted); }
    .toggle-btn {
      cursor: pointer;
      padding: .45rem 1.1rem;
      border-radius: 20px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      font-size: .85rem;
      transition: background .2s, border-color .2s;
    }
    .toggle-btn:hover { background: #21262d; border-color: var(--accent); }
    .toggle-btn.active-normal  { background: #0d419d; border-color: var(--accent); color: #fff; }
    .toggle-btn.active-privacy { background: #1f3d2b; border-color: var(--ok);     color: #fff; }

    /* ── Fingerprint Hero ── */
    .fp-hero {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.4rem 1.6rem;
      margin-bottom: 1.8rem;
      display: flex;
      align-items: center;
      gap: 1.2rem;
      flex-wrap: wrap;
    }
    .fp-icon { font-size: 2.4rem; }
    .fp-label { font-size: .8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
    .fp-value { font-family: var(--mono); font-size: 1.5rem; color: var(--accent); letter-spacing: 2px; }
    .fp-sub   { font-size: .78rem; color: var(--muted); margin-top: .2rem; }

    /* ── Data Cards ── */
    .section-title {
      font-size: .75rem;
      text-transform: uppercase;
      letter-spacing: 1.2px;
      color: var(--muted);
      margin-bottom: .8rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: .4rem;
    }
    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 1rem;
      margin-bottom: 1.8rem;
    }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1rem 1.1rem;
      transition: border-color .2s;
    }
    .card:hover { border-color: var(--accent); }
    .card-header {
      display: flex;
      align-items: center;
      gap: .5rem;
      margin-bottom: .5rem;
    }
    .card-icon { font-size: 1.1rem; }
    .card-name  { font-size: .78rem; text-transform: uppercase; letter-spacing: .8px; color: var(--muted); }
    .card-value {
      font-family: var(--mono);
      font-size: .88rem;
      color: var(--text);
      word-break: break-all;
    }
    .card-value.redacted {
      color: var(--warn);
      font-style: italic;
    }
    .card-source {
      margin-top: .4rem;
      font-size: .72rem;
      color: var(--muted);
    }
    .badge {
      display: inline-block;
      font-size: .65rem;
      padding: .1rem .45rem;
      border-radius: 10px;
      font-family: var(--mono);
    }
    .badge-server { background: #1a2a4a; color: var(--accent); border: 1px solid #1f4080; }
    .badge-client { background: #2a1a0a; color: var(--warn);   border: 1px solid #5a3010; }

    /* ── Raw Payload ── */
    .raw-section { margin-bottom: 1.8rem; }
    .raw-toggle {
      cursor: pointer;
      font-size: .83rem;
      color: var(--accent);
      user-select: none;
    }
    .raw-toggle:hover { text-decoration: underline; }
    pre {
      background: #010409;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1rem;
      font-family: var(--mono);
      font-size: .8rem;
      overflow-x: auto;
      color: #79c0ff;
      margin-top: .6rem;
      display: none;
    }
    pre.visible { display: block; }

    /* ── How It Works ── */
    .how-it-works {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.2rem 1.4rem;
      margin-bottom: 1.8rem;
      font-size: .88rem;
    }
    .how-it-works h3 { color: var(--accent); margin-bottom: .7rem; }
    .how-it-works ol { padding-left: 1.4rem; color: var(--muted); }
    .how-it-works li { margin-bottom: .4rem; }
    .how-it-works li span { color: var(--text); }

    /* ── Footer ── */
    footer {
      text-align: center;
      font-size: .78rem;
      color: var(--muted);
      border-top: 1px solid var(--border);
      padding-top: 1rem;
    }

    /* ── Loading State ── */
    #loading-overlay {
      position: fixed; inset: 0;
      background: var(--bg);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 99;
      font-family: var(--mono);
      color: var(--accent);
      font-size: 1.1rem;
      letter-spacing: 2px;
      transition: opacity .4s;
    }
    #loading-overlay.hidden { opacity: 0; pointer-events: none; }
    .spinner {
      width: 28px; height: 28px;
      border: 3px solid var(--border);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin .7s linear infinite;
      margin-right: 1rem;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>

<!-- Loading overlay (hidden once JS data arrives) -->
<div id="loading-overlay">
  <div class="spinner"></div>
  COLLECTING FINGERPRINT DATA…
</div>

<div class="container">

  <!-- Header -->
  <header>
    <h1>🔍 Browser Fingerprinting Lab</h1>
    <p>An open, transparent demonstration of browser fingerprinting techniques.</p>
  </header>

  <!-- Ethics Banner -->
  <div class="ethics-banner">
    <strong>⚠ Educational Simulation — Transparency Notice</strong><br>
    This page demonstrates what data a website <em>could</em> collect about your browser.
    <strong>No data is stored, logged to a database, or sent anywhere.</strong>
    Everything runs locally on <code>127.0.0.1:5000</code> and is discarded after display.
    Terminal output is limited to this session only.
  </div>

  <!-- Privacy Mode Toggle -->
  <div class="toggle-row">
    <span class="toggle-label">Collection mode:</span>
    <button class="toggle-btn active-normal"  id="btn-normal"  onclick="setMode('normal')">
      🔓 Normal Mode
    </button>
    <button class="toggle-btn" id="btn-privacy" onclick="setMode('privacy')">
      🛡 Privacy Mode
    </button>
    <span id="mode-description" style="font-size:.82rem; color:var(--muted);">
      All available attributes collected.
    </span>
  </div>

  <!-- Fingerprint Hero -->
  <div class="fp-hero">
    <div class="fp-icon">🪪</div>
    <div>
      <div class="fp-label">Generated Fingerprint ID</div>
      <div class="fp-value" id="fp-display">——————————</div>
      <div class="fp-sub">
        SHA-256 hash of collected attributes (first 16 hex chars) ·
        <span id="fp-attr-count">?</span> attributes used
      </div>
    </div>
  </div>

  <!-- Data Cards — Server-Side -->
  <div class="section-title">🖥 Server-Side Data (HTTP Headers)</div>
  <div class="cards-grid" id="server-cards">

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🌐</span>
        <span class="card-name">IP Address</span>
      </div>
      <div class="card-value" id="val-ip">{{ ip }}</div>
      <div class="card-source"><span class="badge badge-server">SERVER</span> Remote address / X-Forwarded-For</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🤖</span>
        <span class="card-name">User-Agent</span>
      </div>
      <div class="card-value" id="val-ua" style="font-size:.78rem;">{{ user_agent }}</div>
      <div class="card-source"><span class="badge badge-server">SERVER</span> User-Agent header</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">💬</span>
        <span class="card-name">Accept-Language</span>
      </div>
      <div class="card-value" id="val-lang">{{ language }}</div>
      <div class="card-source"><span class="badge badge-server">SERVER</span> Accept-Language header</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">💻</span>
        <span class="card-name">Platform Hint</span>
      </div>
      <div class="card-value" id="val-platform">{{ platform }}</div>
      <div class="card-source"><span class="badge badge-server">SERVER</span> Sec-CH-UA-Platform header</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🚫</span>
        <span class="card-name">Do-Not-Track</span>
      </div>
      <div class="card-value" id="val-dnt">{{ dnt }}</div>
      <div class="card-source"><span class="badge badge-server">SERVER</span> DNT header</div>
    </div>

  </div>

  <!-- Data Cards — Client-Side -->
  <div class="section-title">📡 Client-Side Data (JavaScript)</div>
  <div class="cards-grid" id="client-cards">

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🖥</span>
        <span class="card-name">Screen Resolution</span>
      </div>
      <div class="card-value" id="val-screen">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> screen.width × screen.height</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🪟</span>
        <span class="card-name">Viewport Size</span>
      </div>
      <div class="card-value" id="val-viewport">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> window.innerWidth × innerHeight</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🕐</span>
        <span class="card-name">Timezone</span>
      </div>
      <div class="card-value" id="val-tz">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> Intl.DateTimeFormat resolvedOptions</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🌍</span>
        <span class="card-name">JS Language</span>
      </div>
      <div class="card-value" id="val-jslang">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> navigator.language</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🖱</span>
        <span class="card-name">Color Depth</span>
      </div>
      <div class="card-value" id="val-color">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> screen.colorDepth (bits)</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">⚙️</span>
        <span class="card-name">CPU Cores (hint)</span>
      </div>
      <div class="card-value" id="val-cpu">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> navigator.hardwareConcurrency</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🔌</span>
        <span class="card-name">Plugins Count</span>
      </div>
      <div class="card-value" id="val-plugins">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> navigator.plugins.length</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🍪</span>
        <span class="card-name">Cookies Enabled</span>
      </div>
      <div class="card-value" id="val-cookies">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> navigator.cookieEnabled</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">📦</span>
        <span class="card-name">JS Platform</span>
      </div>
      <div class="card-value" id="val-jsplatform">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> navigator.platform</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🖋</span>
        <span class="card-name">Canvas Fingerprint</span>
      </div>
      <div class="card-value" id="val-canvas" style="font-size:.78rem;">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> HTML5 Canvas rendering hash</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🔊</span>
        <span class="card-name">Audio Context</span>
      </div>
      <div class="card-value" id="val-audio">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> AudioContext.sampleRate</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-icon">🕶</span>
        <span class="card-name">Touch Support</span>
      </div>
      <div class="card-value" id="val-touch">collecting…</div>
      <div class="card-source"><span class="badge badge-client">CLIENT</span> navigator.maxTouchPoints</div>
    </div>

  </div>

  <!-- Raw JSON payload -->
  <div class="raw-section">
    <span class="raw-toggle" onclick="toggleRaw()">▶ Show raw fingerprint payload (JSON)</span>
    <pre id="raw-json"></pre>
  </div>

  <!-- How It Works -->
  <div class="how-it-works">
    <h3>📖 How Browser Fingerprinting Works</h3>
    <ol>
      <li><span>Your browser sends <strong>HTTP headers</strong> with every request — revealing User-Agent, preferred language, and platform hints.</span></li>
      <li><span><strong>JavaScript APIs</strong> expose screen dimensions, timezone, installed plugins, hardware concurrency, and more.</span></li>
      <li><span>The <strong>Canvas API</strong> renders text/shapes; tiny rendering differences across GPU drivers and fonts produce a unique hash.</span></li>
      <li><span>These attributes are combined and <strong>hashed</strong> (SHA-256) to produce a stable identifier — without any cookies.</span></li>
      <li><span><strong>Privacy Mode</strong> simulates what browsers like Firefox or Brave return — hardened/randomised values that resist fingerprinting.</span></li>
    </ol>
  </div>

  <footer>
    Browser Fingerprinting Educational Lab · Localhost only · No data stored · For learning purposes only<br>
    <span id="ts" style="font-family:monospace;"></span>
  </footer>

</div><!-- .container -->

<!-- ===================================================================
     JavaScript — Client-Side Fingerprint Collection
=================================================================== -->
<script>
"use strict";

/* ------------------------------------------------------------------ */
/*  State                                                               */
/* ------------------------------------------------------------------ */
let currentMode = "normal";
let clientData  = {};

/* ------------------------------------------------------------------ */
/*  Canvas fingerprint — renders text and extracts pixel hash          */
/* ------------------------------------------------------------------ */
function getCanvasFingerprint() {
  try {
    const c   = document.createElement("canvas");
    c.width   = 220;
    c.height  = 40;
    const ctx = c.getContext("2d");
    ctx.font      = "15px Arial, sans-serif";
    ctx.fillStyle = "#f60";
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.fillStyle = "#069";
    ctx.fillText("BrowserFP Lab 🔍", 4, 26);
    ctx.strokeStyle = "rgba(102,204,0,0.7)";
    ctx.beginPath();
    ctx.arc(110, 20, 16, 0, Math.PI * 2);
    ctx.stroke();
    const raw  = c.toDataURL().slice(-64);   // last 64 chars of base64
    // Simple hash: sum char-codes, format as hex
    let sum = 0;
    for (let i = 0; i < raw.length; i++) sum = (sum * 31 + raw.charCodeAt(i)) >>> 0;
    return sum.toString(16).padStart(8, "0");
  } catch(e) { return "unavailable"; }
}

/* ------------------------------------------------------------------ */
/*  Audio context sample rate                                           */
/* ------------------------------------------------------------------ */
function getAudioInfo() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return "unsupported";
    const ctx = new AudioCtx();
    const sr  = ctx.sampleRate + " Hz";
    ctx.close();
    return sr;
  } catch(e) { return "blocked"; }
}

/* ------------------------------------------------------------------ */
/*  Collect all client-side attributes                                  */
/* ------------------------------------------------------------------ */
function collectClientData(privacyMode) {
  if (privacyMode) {
    // Privacy mode: return hardened / redacted values
    return {
      screen:       "redacted",
      viewport:     "redacted",
      timezone:     "redacted",
      js_language:  "redacted",
      color_depth:  "redacted",
      cpu_cores:    "redacted",
      plugins_count:"redacted",
      cookies:      "redacted",
      js_platform:  "redacted",
      canvas_hash:  "redacted",
      audio:        "redacted",
      touch_points: "redacted",
    };
  }
  return {
    screen:        screen.width  + " × " + screen.height,
    viewport:      window.innerWidth + " × " + window.innerHeight,
    timezone:      Intl.DateTimeFormat().resolvedOptions().timeZone || "unknown",
    js_language:   navigator.language || "unknown",
    color_depth:   screen.colorDepth + "-bit",
    cpu_cores:     (navigator.hardwareConcurrency || "unknown") + " logical cores",
    plugins_count: navigator.plugins ? navigator.plugins.length + " plugin(s)" : "unknown",
    cookies:       navigator.cookieEnabled ? "enabled" : "disabled",
    js_platform:   navigator.platform || "unknown",
    canvas_hash:   getCanvasFingerprint(),
    audio:         getAudioInfo(),
    touch_points:  navigator.maxTouchPoints + " point(s)",
  };
}

/* ------------------------------------------------------------------ */
/*  Send client data to backend, receive fingerprint hash              */
/* ------------------------------------------------------------------ */
async function submitFingerprint(privacyMode) {
  clientData = collectClientData(privacyMode);

  try {
    const res = await fetch("/fingerprint", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ client: clientData, privacy_mode: privacyMode }),
    });
    const json = await res.json();
    return json;
  } catch(err) {
    console.error("Fingerprint API error:", err);
    return null;
  }
}

/* ------------------------------------------------------------------ */
/*  Render collected data into cards                                    */
/* ------------------------------------------------------------------ */
function renderCards(data, privacyMode) {
  const cd = data.client_data;
  const sd = data.server_data;

  const set = (id, val) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (typeof val === "string" && val === "redacted") {
      el.textContent = "⊘ redacted in privacy mode";
      el.className   = "card-value redacted";
    } else {
      el.textContent = val || "unavailable";
      el.className   = "card-value";
    }
  };

  // Server-side
  if (privacyMode) {
    set("val-ip",       "⊘ redacted");
    set("val-ua",       "⊘ redacted");
    set("val-lang",     "⊘ redacted");
    set("val-platform", "⊘ redacted");
    set("val-dnt",      sd.dnt);     // DNT is shown even in privacy mode (it's your choice)
  } else {
    set("val-ip",       sd.ip);
    set("val-ua",       sd.user_agent);
    set("val-lang",     sd.language);
    set("val-platform", sd.platform);
    set("val-dnt",      sd.dnt);
  }

  // Client-side
  set("val-screen",    cd.screen);
  set("val-viewport",  cd.viewport);
  set("val-tz",        cd.timezone);
  set("val-jslang",    cd.js_language);
  set("val-color",     cd.color_depth);
  set("val-cpu",       cd.cpu_cores);
  set("val-plugins",   cd.plugins_count);
  set("val-cookies",   cd.cookies);
  set("val-jsplatform",cd.js_platform);
  set("val-canvas",    cd.canvas_hash);
  set("val-audio",     cd.audio);
  set("val-touch",     cd.touch_points);
}

/* ------------------------------------------------------------------ */
/*  Update fingerprint hero                                             */
/* ------------------------------------------------------------------ */
function renderFP(fpId, attrCount, privacyMode) {
  const el = document.getElementById("fp-display");
  el.textContent = privacyMode ? "PRIVACY-MODE" : fpId;
  el.style.color = privacyMode ? "var(--ok)" : "var(--accent)";
  document.getElementById("fp-attr-count").textContent = privacyMode ? "0 (redacted)" : attrCount;
}

/* ------------------------------------------------------------------ */
/*  Toggle raw JSON panel                                               */
/* ------------------------------------------------------------------ */
let rawVisible = false;
function toggleRaw() {
  rawVisible = !rawVisible;
  const pre = document.getElementById("raw-json");
  pre.classList.toggle("visible", rawVisible);
  document.querySelector(".raw-toggle").textContent =
    (rawVisible ? "▼" : "▶") + " Show raw fingerprint payload (JSON)";
}

function updateRawJson(data) {
  document.getElementById("raw-json").textContent = JSON.stringify(data, null, 2);
}

/* ------------------------------------------------------------------ */
/*  Mode switching                                                       */
/* ------------------------------------------------------------------ */
function setMode(mode) {
  currentMode = mode;
  const isPrivacy = (mode === "privacy");

  document.getElementById("btn-normal" ).className = "toggle-btn" + (isPrivacy ? "" : " active-normal");
  document.getElementById("btn-privacy").className = "toggle-btn" + (isPrivacy ? " active-privacy" : "");
  document.getElementById("mode-description").textContent = isPrivacy
    ? "🛡 Privacy mode: attributes redacted — fingerprint suppressed."
    : "🔓 Normal mode: all available attributes collected.";

  runFingerprint(isPrivacy);
}

/* ------------------------------------------------------------------ */
/*  Main entry point                                                    */
/* ------------------------------------------------------------------ */
async function runFingerprint(privacyMode) {
  const data = await submitFingerprint(privacyMode);
  if (!data) return;

  renderCards(data, privacyMode);
  renderFP(data.fingerprint_id, data.attributes_used, privacyMode);
  updateRawJson(data);

  // Hide loading overlay
  const ov = document.getElementById("loading-overlay");
  ov.classList.add("hidden");
  setTimeout(() => ov.remove(), 500);
}

/* ------------------------------------------------------------------ */
/*  Timestamp                                                           */
/* ------------------------------------------------------------------ */
document.getElementById("ts").textContent =
  "Session: " + new Date().toLocaleString();

/* ------------------------------------------------------------------ */
/*  Boot                                                                */
/* ------------------------------------------------------------------ */
window.addEventListener("DOMContentLoaded", () => runFingerprint(false));
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """
    Serve the main lab page.
    Server-side data is injected directly into the template at render time.
    """
    server_data = extract_server_data(request)
    return render_template_string(
        PAGE_TEMPLATE,
        ip         = server_data["ip"],
        user_agent = server_data["user_agent"],
        language   = server_data["language"],
        platform   = server_data["platform"],
        dnt        = server_data["dnt"],
    )


@app.route("/fingerprint", methods=["POST"])
def fingerprint():
    """
    Receive client-side fingerprint data collected by JavaScript.
    Combine with server-side data, compute the fingerprint hash, log to terminal.

    Returns JSON: { fingerprint_id, attributes_used, server_data, client_data }

    Privacy contract:
    - No persistence — data lives only for the duration of this request.
    - No external calls.
    - Logging writes one info line to stdout, nothing else.
    """
    payload = request.get_json(force=True, silent=True) or {}
    privacy_mode = bool(payload.get("privacy_mode", False))
    client_data  = payload.get("client", {})

    # Always collect server-side data freshly from this request
    server_data = extract_server_data(request)

    if privacy_mode:
        # In privacy mode we do not hash real attributes — return a placeholder
        fp_id          = "PRIVACY-MODE"
        attributes_used = 0
    else:
        # Merge server and client dicts for hashing
        combined = {**server_data, **client_data}
        fp_id    = generate_fingerprint(combined)
        attributes_used = sum(
            1 for v in combined.values() if v not in (None, "", "unknown", "redacted")
        )

    # Terminal log (one line, no DB, no file write)
    log_fingerprint(server_data, fp_id, privacy_mode)

    return jsonify({
        "fingerprint_id":  fp_id,
        "attributes_used": attributes_used,
        "privacy_mode":    privacy_mode,
        "server_data":     server_data if not privacy_mode else {k: "redacted" for k in server_data},
        "client_data":     client_data,
        "generated_at":    datetime.utcnow().isoformat() + "Z",
    })


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  🔍  Browser Fingerprinting Educational Lab")
    print("  ─────────────────────────────────────────")
    print("  URL  : http://127.0.0.1:5000")
    print("  Mode : Localhost only — no external data")
    print("  Stop : Ctrl-C")
    print("=" * 60)
    # debug=False keeps the output clean; use_reloader=False avoids double-start
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)