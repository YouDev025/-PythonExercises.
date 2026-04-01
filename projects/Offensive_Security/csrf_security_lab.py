"""
=============================================================================
  CSRF Educational Lab — Cross-Site Request Forgery Demonstration
  Author  : Senior Python / Cybersecurity Instructor
  Purpose : Safe, local-only lab illustrating CSRF attack & defence
  Run     : python csrf_lab.py  →  open http://127.0.0.1:5000
=============================================================================
"""

import os
import secrets
import logging
from datetime import datetime
from functools import wraps
from flask import (
    Flask, request, session, redirect,
    url_for, make_response, render_template_string
)

# ──────────────────────────────────────────────────────────────────────────────
#  App bootstrap
# ──────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)   # signs the session cookie

# ──────────────────────────────────────────────────────────────────────────────
#  Logging — every security-relevant event is printed with a timestamp
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("csrf_lab")


def log_event(tag: str, msg: str, ok: bool = True):
    """Emit a colourised terminal line and return a plain string for the UI."""
    GREEN, RED, CYAN, RESET = "\033[92m", "\033[91m", "\033[96m", "\033[0m"
    colour = GREEN if ok else RED
    line   = f"{colour}[{tag}]{RESET} {msg}"
    log.info(line)
    return f"[{tag}] {msg}"


# ──────────────────────────────────────────────────────────────────────────────
#  In-memory "database"  (reset on restart — intentional for the lab)
# ──────────────────────────────────────────────────────────────────────────────
USERS: dict[str, dict] = {
    "alice": {"password": "hunter2", "email": "alice@example.com"},
    "bob":   {"password": "correct-horse", "email": "bob@example.com"},
}

# Stores per-session audit trail shown in the UI
AUDIT: list[str] = []


def audit(tag: str, msg: str, ok: bool = True):
    entry = log_event(tag, msg, ok)
    ts    = datetime.now().strftime("%H:%M:%S")
    AUDIT.append({"time": ts, "tag": tag, "msg": msg, "ok": ok})
    return entry


# ──────────────────────────────────────────────────────────────────────────────
#  Auth helpers
# ──────────────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────────────────────────────────────
#  CSRF token helpers
# ──────────────────────────────────────────────────────────────────────────────
def generate_csrf_token() -> str:
    """Create a cryptographically-random token and store it in the session."""
    token = secrets.token_hex(32)
    session["csrf_token"] = token
    audit("CSRF", f"Token generated → {token[:12]}…", ok=True)
    return token


def get_csrf_token() -> str:
    """Return existing token or create one."""
    return session.get("csrf_token") or generate_csrf_token()


def validate_csrf_token(submitted: str | None) -> bool:
    """Compare submitted token against session token (constant-time)."""
    stored = session.get("csrf_token")
    if not submitted or not stored:
        audit("CSRF", "Token missing in request!", ok=False)
        return False
    ok = secrets.compare_digest(submitted, stored)
    if ok:
        audit("CSRF", f"Token valid → {submitted[:12]}…", ok=True)
    else:
        audit("CSRF", f"Token MISMATCH! got={submitted[:12]}…", ok=False)
    return ok


# ──────────────────────────────────────────────────────────────────────────────
#  Shared HTML pieces
# ──────────────────────────────────────────────────────────────────────────────
BASE_CSS = """
<style>
  :root {
    --bg: #0f1117; --panel: #1a1d2e; --border: #2d3150;
    --accent: #7c6af7; --danger: #e05c5c; --success: #4caf7d;
    --text: #e2e4f0; --muted: #7b7f9e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg); color: var(--text);
    font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh; padding: 2rem;
  }
  h1 { font-size: 1.6rem; margin-bottom: .25rem; }
  h2 { font-size: 1.2rem; margin-bottom: 1rem; color: var(--accent); }
  p  { color: var(--muted); margin-bottom: .75rem; line-height: 1.5; }
  a  { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }

  .card {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.75rem; margin-bottom: 1.5rem;
    max-width: 680px;
  }
  label  { display: block; margin-bottom: .35rem; color: var(--muted); font-size: .875rem; }
  input  {
    width: 100%; padding: .65rem .9rem; border-radius: 8px;
    border: 1px solid var(--border); background: #22263a;
    color: var(--text); font-size: .95rem; margin-bottom: 1rem;
  }
  input:focus { outline: 2px solid var(--accent); border-color: transparent; }
  button, .btn {
    display: inline-block; padding: .65rem 1.4rem;
    border-radius: 8px; border: none; cursor: pointer;
    font-size: .9rem; font-weight: 600; transition: opacity .15s;
  }
  button:hover, .btn:hover { opacity: .85; }
  .btn-primary  { background: var(--accent); color: #fff; }
  .btn-danger   { background: var(--danger); color: #fff; }
  .btn-success  { background: var(--success); color: #fff; }
  .btn-outline  {
    background: transparent; color: var(--accent);
    border: 1px solid var(--accent);
  }
  .badge {
    display: inline-block; padding: .2rem .6rem; border-radius: 20px;
    font-size: .78rem; font-weight: 700; text-transform: uppercase;
  }
  .badge-vuln   { background: #3d1a1a; color: var(--danger); }
  .badge-secure { background: #1a3d2b; color: var(--success); }
  .badge-info   { background: #1a2a3d; color: #5ba4f5; }

  .audit {
    background: #0a0c14; border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem; font-family: monospace;
    font-size: .82rem; max-height: 300px; overflow-y: auto;
  }
  .audit-row   { padding: .3rem 0; border-bottom: 1px solid #181b2a; display: flex; gap: .75rem; }
  .audit-time  { color: var(--muted); min-width: 60px; }
  .audit-tag   { min-width: 70px; font-weight: 700; }
  .audit-ok    { color: var(--success); }
  .audit-fail  { color: var(--danger); }

  .nav {
    display: flex; gap: 1rem; align-items: center;
    padding-bottom: 1.25rem; margin-bottom: 1.5rem;
    border-bottom: 1px solid var(--border); flex-wrap: wrap;
  }
  .nav-brand { font-weight: 700; font-size: 1.1rem; color: var(--accent); }
  .flash {
    padding: .75rem 1rem; border-radius: 8px; margin-bottom: 1rem;
    font-size: .9rem; max-width: 680px;
  }
  .flash-ok   { background: #1a3d2b; border: 1px solid var(--success); color: var(--success); }
  .flash-err  { background: #3d1a1a; border: 1px solid var(--danger);  color: var(--danger);  }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; max-width: 680px; }
  @media (max-width: 580px) { .grid2 { grid-template-columns: 1fr; } }
  .token-box {
    background: #0a0c14; border: 1px dashed var(--border);
    border-radius: 6px; padding: .5rem .75rem; font-family: monospace;
    font-size: .78rem; word-break: break-all; color: #5ba4f5;
    margin-bottom: 1rem;
  }
  details summary { cursor: pointer; color: var(--accent); margin-bottom: .5rem; }
  details p { font-size: .85rem; }
  hr { border: none; border-top: 1px solid var(--border); margin: 1.25rem 0; }
</style>
"""

def nav(username=None):
    user_info = f'<span style="color:var(--muted)">Logged in as <b style="color:var(--text)">{username}</b></span>' if username else ""
    logout = '<a href="/logout" class="btn btn-outline" style="padding:.4rem .9rem;font-size:.82rem">Logout</a>' if username else ""
    return f"""
    <div class="nav">
      <span class="nav-brand">🔐 CSRF Lab</span>
      <a href="/">Home</a>
      <a href="/vulnerable/dashboard">Vulnerable App</a>
      <a href="/secure/dashboard">Secure App</a>
      <a href="/attacker">Attacker Page</a>
      <a href="/audit">Audit Log</a>
      {user_info}
      {logout}
    </div>"""


def flash_html(msg, kind="ok"):
    cls = "flash-ok" if kind == "ok" else "flash-err"
    icon = "✅" if kind == "ok" else "❌"
    return f'<div class="flash {cls}">{icon} {msg}</div>'


# ──────────────────────────────────────────────────────────────────────────────
#  Route: Home / index
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    html = f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="utf-8"><title>CSRF Lab</title>{BASE_CSS}</head><body>
    {nav(session.get("username"))}
    <h1>Cross-Site Request Forgery — Educational Lab</h1>
    <p>A safe, local-only environment to understand CSRF attacks and defences.</p>

    <div class="grid2" style="margin-top:1.5rem">
      <div class="card">
        <span class="badge badge-vuln">Vulnerable</span>
        <h2 style="margin-top:.75rem">App without CSRF protection</h2>
        <p>Forms submit without any token. An attacker page can silently trigger
        sensitive actions on behalf of a logged-in user.</p>
        <a href="/vulnerable/login" class="btn btn-danger">Enter →</a>
      </div>
      <div class="card">
        <span class="badge badge-secure">Secure</span>
        <h2 style="margin-top:.75rem">App with CSRF token protection</h2>
        <p>Every sensitive form embeds a random per-session token.
        The server rejects requests that don't include a valid token.</p>
        <a href="/secure/login" class="btn btn-success">Enter →</a>
      </div>
    </div>

    <div class="card" style="margin-top:1rem">
      <span class="badge badge-info">Attacker</span>
      <h2 style="margin-top:.75rem">Simulated Malicious Page</h2>
      <p>Mimics a third-party site that auto-submits a form to both apps.
      Log in to one (or both) apps first, then visit this page to see the attack.</p>
      <a href="/attacker" class="btn btn-outline">Open Attacker Page →</a>
    </div>

    <div class="card">
      <h2>How CSRF works — 30-second primer</h2>
      <p>1. You log in to <em>bank.com</em> — your browser stores the session cookie.</p>
      <p>2. You visit a malicious site. It contains a hidden form targeting <em>bank.com</em>.</p>
      <p>3. Your browser auto-attaches the bank cookie when submitting the form.</p>
      <p>4. The bank server sees a valid session and executes the action — without your consent.</p>
      <p><b>Token defence:</b> the server generates an unpredictable secret per session.
      The legitimate page embeds it; the attacker page cannot read it (same-origin policy).</p>
    </div>
    </body></html>"""
    return html


# ──────────────────────────────────────────────────────────────────────────────
#  ██████  Vulnerable Application  ██████
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/vulnerable/login", methods=["GET", "POST"])
def vuln_login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = USERS.get(username)
        audit("AUTH", f"[VULN] Login attempt for '{username}'")
        if user and user["password"] == password:
            session["username"] = username
            session["mode"] = "vulnerable"
            audit("AUTH", f"[VULN] Login SUCCESS for '{username}'")
            return redirect(url_for("vuln_dashboard"))
        audit("AUTH", f"[VULN] Login FAILED for '{username}'", ok=False)
        error = "Invalid credentials."

    html = f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="utf-8"><title>Vulnerable Login</title>{BASE_CSS}</head><body>
    {nav(session.get("username"))}
    <span class="badge badge-vuln" style="margin-bottom:.75rem">Vulnerable App</span>
    <h1>Login</h1>
    <p>Credentials: <code>alice / hunter2</code> &nbsp;or&nbsp; <code>bob / correct-horse</code></p>
    {''.join([flash_html(error, "err")]) if error else ""}
    <div class="card">
      <form method="POST">
        <label>Username</label><input name="username" placeholder="alice">
        <label>Password</label><input name="password" type="password">
        <button class="btn-danger">Login to Vulnerable App</button>
      </form>
    </div>
    </body></html>"""
    return html


@app.route("/vulnerable/dashboard")
@login_required
def vuln_dashboard():
    username = session["username"]
    email = USERS[username]["email"]
    html = f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="utf-8"><title>Vulnerable Dashboard</title>{BASE_CSS}</head><body>
    {nav(username)}
    <span class="badge badge-vuln">Vulnerable App</span>
    <h1 style="margin-top:.75rem">Dashboard — {username}</h1>
    <p>Current email: <b>{email}</b></p>

    <div class="card">
      <h2>Change Email  <span style="color:var(--danger);font-size:.8rem">(no CSRF protection)</span></h2>
      <p>This form has <b>no CSRF token</b>. Any site can POST to this endpoint
      while your session cookie is active.</p>

      <details style="margin-bottom:1rem">
        <summary>Why is this dangerous?</summary>
        <p>The server only checks the session cookie — not the origin of the request.
        A malicious page can craft an identical POST and the server can't tell the difference.</p>
      </details>

      <form method="POST" action="/vulnerable/change-email">
        <label>New Email</label>
        <input name="new_email" placeholder="new@example.com">
        <button class="btn-danger">Change Email</button>
      </form>
    </div>
    </body></html>"""
    return html


@app.route("/vulnerable/change-email", methods=["POST"])
@login_required
def vuln_change_email():
    """Vulnerable endpoint — accepts any POST with a valid session cookie."""
    username  = session["username"]
    new_email = request.form.get("new_email", "").strip()
    origin    = request.headers.get("Origin", "no-origin-header")
    referer   = request.headers.get("Referer", "no-referer")

    audit("REQUEST", f"[VULN] Change-email received from origin='{origin}'")
    audit("REQUEST", f"[VULN] Referer='{referer}'")

    if not new_email:
        audit("ACTION", "[VULN] Change-email REJECTED — empty email", ok=False)
        return redirect(url_for("vuln_dashboard"))

    old_email = USERS[username]["email"]
    USERS[username]["email"] = new_email

    audit("ACTION",
          f"[VULN] ✔ Email changed: {old_email} → {new_email}  "
          f"(session owner: {username}, request may be FORGED!)", ok=True)

    html = f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="utf-8"><title>Email Changed</title>{BASE_CSS}</head><body>
    {nav(username)}
    <span class="badge badge-vuln">Vulnerable App</span>
    {flash_html(f"Email changed to <b>{new_email}</b> — action executed with NO token check!")}
    <div class="card">
      <p>The server accepted this request <b>only because a valid session cookie
      was present</b>. It performed zero verification of where the request originated.</p>
      <p>Origin header seen: <code>{origin}</code><br>
         Referer header seen: <code>{referer}</code></p>
      <p style="color:var(--danger)">⚠ An attacker page sent the same POST — and it worked.</p>
      <a href="/vulnerable/dashboard" class="btn btn-outline">Back to dashboard</a>
    </div>
    </body></html>"""
    return html


# ──────────────────────────────────────────────────────────────────────────────
#  ██████  Secure Application  ██████
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/secure/login", methods=["GET", "POST"])
def secure_login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = USERS.get(username)
        audit("AUTH", f"[SECURE] Login attempt for '{username}'")
        if user and user["password"] == password:
            session["username"] = username
            session["mode"] = "secure"
            generate_csrf_token()                # create token on login
            audit("AUTH", f"[SECURE] Login SUCCESS for '{username}'")
            return redirect(url_for("secure_dashboard"))
        audit("AUTH", f"[SECURE] Login FAILED for '{username}'", ok=False)
        error = "Invalid credentials."

    html = f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="utf-8"><title>Secure Login</title>{BASE_CSS}</head><body>
    {nav(session.get("username"))}
    <span class="badge badge-secure" style="margin-bottom:.75rem">Secure App</span>
    <h1>Login</h1>
    <p>Credentials: <code>alice / hunter2</code> &nbsp;or&nbsp; <code>bob / correct-horse</code></p>
    {''.join([flash_html(error, "err")]) if error else ""}
    <div class="card">
      <form method="POST">
        <label>Username</label><input name="username" placeholder="alice">
        <label>Password</label><input name="password" type="password">
        <button class="btn-success">Login to Secure App</button>
      </form>
    </div>
    </body></html>"""
    return html


@app.route("/secure/dashboard")
@login_required
def secure_dashboard():
    username = session["username"]
    email    = USERS[username]["email"]
    token    = get_csrf_token()

    html = f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="utf-8"><title>Secure Dashboard</title>{BASE_CSS}</head><body>
    {nav(username)}
    <span class="badge badge-secure">Secure App</span>
    <h1 style="margin-top:.75rem">Dashboard — {username}</h1>
    <p>Current email: <b>{email}</b></p>

    <div class="card">
      <h2>Change Email  <span style="color:var(--success);font-size:.8rem">(CSRF token protected)</span></h2>
      <p>This form embeds a hidden CSRF token.  The server validates it before acting.
      An attacker page cannot read or guess this token (same-origin policy).</p>

      <details style="margin-bottom:.75rem">
        <summary>Token embedded in this form</summary>
        <div class="token-box">{token}</div>
        <p>This value lives in your session on the server.
        The attacker's page sends a different (or missing) token → rejected.</p>
      </details>

      <form method="POST" action="/secure/change-email">
        <!-- ✅ Hidden CSRF token — the attacker cannot read or replicate this -->
        <input type="hidden" name="csrf_token" value="{token}">
        <label>New Email</label>
        <input name="new_email" placeholder="new@example.com">
        <button class="btn-success">Change Email (protected)</button>
      </form>
    </div>
    </body></html>"""
    return html


@app.route("/secure/change-email", methods=["POST"])
@login_required
def secure_change_email():
    """Secure endpoint — validates CSRF token before acting."""
    username       = session["username"]
    submitted_tok  = request.form.get("csrf_token")
    new_email      = request.form.get("new_email", "").strip()
    origin         = request.headers.get("Origin", "no-origin-header")

    audit("REQUEST", f"[SECURE] Change-email received from origin='{origin}'")
    audit("CSRF",    f"[SECURE] Validating token…")

    # ── Core defence: token validation ────────────────────────────────────────
    if not validate_csrf_token(submitted_tok):
        audit("ACTION", "[SECURE] Request BLOCKED — CSRF token invalid!", ok=False)
        html = f"""<!DOCTYPE html><html lang="en"><head>
        <meta charset="utf-8"><title>Blocked</title>{BASE_CSS}</head><body>
        {nav(username)}
        <span class="badge badge-secure">Secure App</span>
        {flash_html("Request BLOCKED — CSRF token missing or invalid!", "err")}
        <div class="card">
          <h2>Attack Neutralised 🛡</h2>
          <p>The server expected a valid CSRF token embedded in the form.
          The request arrived without one (or with a wrong one) — typical of a
          cross-site request forgery.</p>
          <p>Token submitted: <code>{submitted_tok or "None"}</code></p>
          <p>Token in session: <code>{session.get("csrf_token", "None")}</code></p>
          <p>Because these don't match, the action was <b>never executed</b>.
          The user's email is unchanged.</p>
          <a href="/secure/dashboard" class="btn btn-outline">Back to dashboard</a>
        </div>
        </body></html>"""
        return html, 403

    if not new_email:
        return redirect(url_for("secure_dashboard"))

    old_email = USERS[username]["email"]
    USERS[username]["email"] = new_email

    # Rotate token after use (prevents replay attacks)
    generate_csrf_token()
    audit("ACTION", f"[SECURE] ✔ Email changed: {old_email} → {new_email}", ok=True)

    html = f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="utf-8"><title>Email Changed</title>{BASE_CSS}</head><body>
    {nav(username)}
    <span class="badge badge-secure">Secure App</span>
    {flash_html(f"Email changed to <b>{new_email}</b> — token was valid ✅")}
    <div class="card">
      <p>This request came from the legitimate form (same origin), so it carried
      the correct CSRF token. The server verified it and executed the action.</p>
      <p>A new token has been issued for the next request (token rotation).</p>
      <a href="/secure/dashboard" class="btn btn-outline">Back to dashboard</a>
    </div>
    </body></html>"""
    return html


# ──────────────────────────────────────────────────────────────────────────────
#  ██████  Attacker's Malicious Page  ██████
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/attacker")
def attacker():
    """
    Simulates a page on a different origin.
    In a real attack this would be hosted at evil.com.
    It auto-submits forms to both vulnerable and secure endpoints.
    The attacker has no way to know the CSRF token stored in the victim's session.
    """
    audit("ATTACKER", "Malicious page loaded by visitor", ok=False)

    # The attacker guesses / fabricates a token — it will not match
    fake_token = "ATTACKER_FABRICATED_" + secrets.token_hex(8)

    html = f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="utf-8"><title>😈 Attacker Page</title>{BASE_CSS}
    <style>
      .evil {{ border-color: var(--danger); }}
      .evil h2 {{ color: var(--danger); }}
      body {{ max-width: 800px; margin: 0 auto; }}
    </style>
    </head><body>
    {nav(session.get("username"))}

    <div style="background:#1a0808;border:1px solid var(--danger);border-radius:12px;
                padding:1rem 1.5rem;margin-bottom:1.5rem;max-width:680px">
      <p style="color:var(--danger);font-weight:700;margin-bottom:.25rem">
        ⚠ Simulated Attacker Page (localhost/attacker)
      </p>
      <p>In a real attack this page would be at <code>http://evil.com/</code>.
      Your browser auto-sends session cookies to <code>localhost:5000</code> because
      they were set without the <code>SameSite=Strict</code> attribute.</p>
    </div>

    <!-- ── Attack 1: Vulnerable endpoint ────────────────────────────────── -->
    <div class="card evil">
      <span class="badge badge-vuln">Attack 1 — Vulnerable App</span>
      <h2 style="margin-top:.75rem">Forged request — no token needed</h2>
      <p>This hidden form targets the <b>vulnerable</b> change-email endpoint.
      It will succeed if you are logged into the vulnerable app in this browser.</p>
      <p>Attacker's goal email: <code>hacked-by-attacker@evil.com</code></p>

      <!--
        The form is invisible to the victim.
        JavaScript submits it automatically — victim sees nothing.
        The browser attaches the session cookie because the target is localhost:5000.
      -->
      <form id="atk1" method="POST" action="/vulnerable/change-email"
            style="display:none">
        <input name="new_email" value="hacked-by-attacker@evil.com">
      </form>
      <button class="btn-danger" onclick="document.getElementById('atk1').submit()">
        🚀 Launch Attack → Vulnerable App
      </button>
      <p style="margin-top:.75rem;font-size:.83rem;color:var(--muted)">
        (In the wild this submit() is called automatically on page load — no click needed.)
      </p>
    </div>

    <!-- ── Attack 2: Secure endpoint ─────────────────────────────────────── -->
    <div class="card">
      <span class="badge badge-secure">Attack 2 — Secure App</span>
      <h2>Forged request — with a fabricated token (will fail)</h2>
      <p>This form targets the <b>secure</b> endpoint. The attacker guesses a token,
      but the server's session holds a different value.</p>

      <p>Fabricated token:<br>
      <span class="token-box">{fake_token}</span></p>

      <form id="atk2" method="POST" action="/secure/change-email"
            style="display:none">
        <!-- Attacker plants a FAKE token — server will reject it -->
        <input type="hidden" name="csrf_token" value="{fake_token}">
        <input name="new_email" value="hacked-secure@evil.com">
      </form>
      <button class="btn-outline" onclick="document.getElementById('atk2').submit()">
        🚀 Launch Attack → Secure App (should be blocked)
      </button>
    </div>

    <div class="card">
      <h2>Why can't the attacker steal the real token?</h2>
      <p><b>Same-Origin Policy (SOP)</b>: JavaScript running on
      <code>evil.com</code> cannot read the DOM or cookies of <code>bank.com</code>.
      The CSRF token lives inside the legitimate page's HTML — totally inaccessible
      cross-origin. Without the correct token, the server rejects the forged request.</p>
      <p>Cookies <em>are</em> sent cross-origin (that's the whole problem CSRF exploits),
      but the token is <em>not</em> a cookie — it's a hidden form field the attacker
      cannot read.</p>
      <a href="/audit" class="btn btn-outline" style="margin-top:.5rem">
        View audit log →
      </a>
    </div>
    </body></html>"""
    return html


# ──────────────────────────────────────────────────────────────────────────────
#  Audit Log page
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/audit")
def audit_page():
    rows = ""
    for entry in reversed(AUDIT[-100:]):          # show latest 100, newest first
        css  = "audit-ok" if entry["ok"] else "audit-fail"
        rows += (
            f'<div class="audit-row">'
            f'<span class="audit-time">{entry["time"]}</span>'
            f'<span class="audit-tag {css}">{entry["tag"]}</span>'
            f'<span>{entry["msg"]}</span>'
            f'</div>'
        )
    if not rows:
        rows = '<div class="audit-row"><span style="color:var(--muted)">No events yet. Interact with the app.</span></div>'

    html = f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="utf-8"><title>Audit Log</title>{BASE_CSS}
    <meta http-equiv="refresh" content="5">
    </head><body>
    {nav(session.get("username"))}
    <h1>Security Audit Log</h1>
    <p>Auto-refreshes every 5 seconds. All security-relevant events are logged here
    and printed to the terminal with colour coding.</p>
    <div class="audit" style="max-width:720px;max-height:600px">{rows}</div>
    <p style="margin-top:.75rem;font-size:.82rem">
      <span style="color:var(--success)">■</span> Success &nbsp;
      <span style="color:var(--danger)">■</span> Failure / Attack
    </p>
    </body></html>"""
    return html


# ──────────────────────────────────────────────────────────────────────────────
#  Logout
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    username = session.get("username", "unknown")
    audit("AUTH", f"Logout: {username}")
    session.clear()
    return redirect(url_for("index"))


# ──────────────────────────────────────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  CSRF Educational Lab  —  http://127.0.0.1:5000")
    print("="*60)
    print("  Vulnerable app : /vulnerable/login")
    print("  Secure app     : /secure/login")
    print("  Attacker page  : /attacker")
    print("  Audit log      : /audit")
    print("  Credentials    : alice/hunter2  |  bob/correct-horse")
    print("="*60 + "\n")

    # debug=False keeps output clean; use_reloader=False avoids double-start
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)