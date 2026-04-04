import os
import secrets
import logging
from flask import Flask, session, request, redirect, url_for, render_template_string

# --- INITIALIZATION ---
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Disable standard Flask logging to make our custom logs clearer
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Configuration for the demo
app.config['SECURITY_MODE'] = 'VULNERABLE'  # Start in vulnerable mode

# --- HTML TEMPLATES (Inline) ---
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Session Fixation Demo</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; background: #f4f4f9; }
        .card { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .status { padding: 10px; border-radius: 4px; font-weight: bold; text-align: center; margin-bottom: 20px; }
        .vulnerable { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
        .secure { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
        .session-info { background: #263238; color: #cfd8dc; padding: 15px; border-radius: 5px; font-family: monospace; word-break: break-all; }
        .highlight { color: #ffeb3b; font-weight: bold; }
        button { background: #1976d2; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button.toggle { background: #455a64; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .terminal { background: #000; color: #00ff00; padding: 10px; border-radius: 4px; font-size: 0.9em; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Session Fixation Educational Demo</h1>

    <div class="status {{ 'vulnerable' if mode == 'VULNERABLE' else 'secure' }}">
        Current Mode: <strong>{{ mode }}</strong>
    </div>

    <div class="card">
        <h3>1. Instructions</h3>
        <p><strong>Goal:</strong> Observe if the "Session Token" changes after logging in.</p>
        <ol>
            <li>Observe the current <strong>Session Token</strong> below.</li>
            <li>Login with any username/password.</li>
            <li>In <strong>VULNERABLE</strong> mode: The token stays the same (Fixation possible).</li>
            <li>In <strong>SECURE</strong> mode: The token is regenerated (Secure).</li>
        </ol>
        <form action="/toggle" method="post">
            <button type="submit" class="toggle">Switch to {{ 'SECURE' if mode == 'VULNERABLE' else 'VULNERABLE' }} Mode</button>
        </form>
    </div>

    <div class="card">
        <h3>2. Session Diagnostics</h3>
        <div class="session-info">
            Current Token: <span class="highlight">{{ sid }}</span><br>
            User Status: <span class="highlight">{{ 'Logged In (' + user + ')' if user else 'Guest' }}</span>
        </div>
    </div>

    <div class="card">
        <h3>3. Authentication</h3>
        {% if not user %}
        <form action="/login" method="post">
            <input type="text" name="username" placeholder="Username (e.g. admin)" required>
            <input type="password" name="password" placeholder="Password (any)" required>
            <button type="submit">Login</button>
        </form>
        {% else %}
        <p>You are successfully authenticated!</p>
        <form action="/logout" method="post">
            <button type="submit" style="background: #d32f2f;">Logout / Reset Session</button>
        </form>
        {% endif %}
    </div>

    <div class="card">
        <h3>Educational Context</h3>
        <p><small><b>Session Fixation</b> occurs when an application provides a session ID to a user before they log in and fails to rotate that ID after a successful login. An attacker can "fix" a session ID for a victim (e.g., via a URL parameter), wait for them to log in, and then hijack the authenticated session because the ID remains valid.</small></p>
    </div>
</body>
</html>
"""


# --- HELPER FUNCTIONS ---

def get_session_display_id():
    """Extracts a readable portion of the session cookie to act as the 'ID' for demo purposes."""
    # In Flask, the session is the cookie itself.
    # We create a specific 'token' key if it doesn't exist to simulate a classic Session ID.
    if 'demo_token' not in session:
        session['demo_token'] = secrets.token_urlsafe(16)
    return session['demo_token']


def log_event(event):
    """Prints events to the console in a highlighted format."""
    print(f"\n[EVENT] {event}")
    print(f"[TOKEN] {session.get('demo_token', 'None')}")
    print("-" * 30)


# --- ROUTES ---

@app.route('/')
def index():
    # Initialize session token if first visit
    sid = get_session_display_id()
    return render_template_string(
        BASE_TEMPLATE,
        mode=app.config['SECURITY_MODE'],
        sid=sid,
        user=session.get('user')
    )


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    old_sid = session.get('demo_token')

    if app.config['SECURITY_MODE'] == 'SECURE':
        # --- SECURE LOGIC ---
        # 1. Capture old data if necessary (none needed here)
        # 2. Clear the old session entirely (Regeneration)
        session.clear()
        # 3. Create a brand new token
        session['demo_token'] = secrets.token_urlsafe(16)
        session['user'] = username
        log_event(f"SECURE LOGIN: Session regenerated. Old ID {old_sid} invalidated.")
    else:
        # --- VULNERABLE LOGIC ---
        # Keep the session exactly as it is, just add the user identity.
        session['user'] = username
        log_event(f"VULNERABLE LOGIN: User authenticated, but ID {old_sid} PERSIESTS!")

    return redirect(url_for('index'))


@app.route('/logout', methods=['POST'])
def logout():
    log_event("LOGOUT: Session cleared.")
    session.clear()
    return redirect(url_for('index'))


@app.route('/toggle', methods=['POST'])
def toggle():
    if app.config['SECURITY_MODE'] == 'VULNERABLE':
        app.config['SECURITY_MODE'] = 'SECURE'
    else:
        app.config['SECURITY_MODE'] = 'VULNERABLE'

    session.clear()  # Clear state when switching modes for clarity
    print(f"\n[CONFIG] Switched to {app.config['SECURITY_MODE']} mode.")
    return redirect(url_for('index'))


# --- MAIN ---

if __name__ == '__main__':
    print("=" * 60)
    print("SESSION FIXATION EDUCATIONAL DEMO")
    print("Open your browser at http://127.0.0.1:5000")
    print("Watch this terminal to see how the Session Token behaves.")
    print("=" * 60)

    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=False)