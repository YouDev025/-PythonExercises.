#!/usr/bin/env python3
"""
HTTP Cookie Security Educational Lab
A safe environment to demonstrate cookie security concepts including:
- HttpOnly flag protection
- Secure flag for HTTPS-only transmission
- SameSite attribute for CSRF protection
- JavaScript cookie access simulation
"""

from flask import Flask, request, make_response, jsonify, render_template_string
import secrets
import logging
from datetime import datetime, timedelta

# Configure logging for educational output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cookie Security Lab</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .secure { border-left: 4px solid #4CAF50; }
        .insecure { border-left: 4px solid #f44336; }
        button {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            cursor: pointer;
            border-radius: 4px;
            font-family: monospace;
        }
        button:hover { background-color: #0b7dda; }
        .danger-btn { background-color: #f44336; }
        .danger-btn:hover { background-color: #da190b; }
        .success-btn { background-color: #4CAF50; }
        .success-btn:hover { background-color: #45a049; }
        pre {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        .log {
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .warning { background-color: #fff3cd; color: #856404; }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>🍪 HTTP Cookie Security Educational Lab</h1>

    <div class="container">
        <h2>Cookie Configuration</h2>
        <form id="configForm">
            <label>
                <input type="checkbox" id="httpOnly" {{ 'checked' if http_only else '' }}>
                HttpOnly Flag (Prevents JavaScript access)
            </label><br>
            <label>
                <input type="checkbox" id="secure" {{ 'checked' if secure else '' }}>
                Secure Flag (HTTPS only - simulated)
            </label><br>
            <label>
                <select id="sameSite">
                    <option value="None" {{ 'selected' if same_site == 'None' else '' }}>None</option>
                    <option value="Lax" {{ 'selected' if same_site == 'Lax' else '' }}>Lax</option>
                    <option value="Strict" {{ 'selected' if same_site == 'Strict' else '' }}>Strict</option>
                </select>
                SameSite Attribute
            </label><br>
            <button type="button" onclick="updateConfig()">Update Configuration</button>
        </form>
    </div>

    <div class="container">
        <h2>Cookie Operations</h2>
        <button onclick="setCookie()">Set Session Cookie</button>
        <button onclick="readCookie()">Read Current Cookie</button>
        <button onclick="deleteCookie()">Delete Cookie</button>
    </div>

    <div class="container">
        <h2>🔒 Security Simulation</h2>
        <button class="danger-btn" onclick="simulateMaliciousJS()">⚠️ Simulate Malicious JavaScript Cookie Access</button>
        <div id="attackResult" class="status" style="display:none;"></div>
    </div>

    <div class="container">
        <h2>Current Cookie Information</h2>
        <div id="cookieInfo"></div>
    </div>

    <div class="container">
        <h2>📋 Educational Log</h2>
        <div id="logMessages" class="log"></div>
    </div>

    <script>
        // Function to add messages to the educational log
        function addLogMessage(message, type) {
            const logDiv = document.getElementById('logMessages');
            const timestamp = new Date().toLocaleTimeString();
            const color = type === 'error' ? '#f44336' : (type === 'warning' ? '#ff9800' : '#4CAF50');
            const logEntry = `<div style="color: ${color}; margin: 5px 0;">[${timestamp}] ${message}</div>`;
            logDiv.innerHTML += logEntry;
            logDiv.scrollTop = logDiv.scrollHeight;
        }

        // Update cookie configuration
        async function updateConfig() {
            const config = {
                http_only: document.getElementById('httpOnly').checked,
                secure: document.getElementById('secure').checked,
                same_site: document.getElementById('sameSite').value
            };

            const response = await fetch('/update_config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });

            const result = await response.json();
            addLogMessage(`Configuration updated: HttpOnly=${config.http_only}, Secure=${config.secure}, SameSite=${config.same_site}`, 'info');
            alert('Configuration updated successfully!');
        }

        // Set a cookie
        async function setCookie() {
            const response = await fetch('/set_cookie', {method: 'POST'});
            const result = await response.json();
            addLogMessage(result.message, 'info');
            readCookie();
        }

        // Read current cookie
        async function readCookie() {
            const response = await fetch('/read_cookie');
            const result = await response.json();

            const cookieInfo = document.getElementById('cookieInfo');
            if (result.cookie_data) {
                cookieInfo.innerHTML = `
                    <table>
                        <tr><th>Property</th><th>Value</th></tr>
                        <tr><td>Session ID</td><td>${result.cookie_data.session_id}</td></tr>
                        <tr><td>Created</td><td>${result.cookie_data.created}</td></tr>
                        <tr><td>Expires</td><td>${result.cookie_data.expires}</td></tr>
                        <tr><td>HttpOnly</td><td>${result.cookie_data.http_only}</td></tr>
                        <tr><td>Secure</td><td>${result.cookie_data.secure}</td></tr>
                        <tr><td>SameSite</td><td>${result.cookie_data.same_site}</td></tr>
                    </table>
                `;
                addLogMessage(`Cookie read successfully. Session ID: ${result.cookie_data.session_id}`, 'info');
            } else {
                cookieInfo.innerHTML = '<p class="warning">No active cookie found.</p>';
                addLogMessage('No active cookie found', 'warning');
            }
        }

        // Delete cookie
        async function deleteCookie() {
            const response = await fetch('/delete_cookie', {method: 'POST'});
            const result = await response.json();
            addLogMessage(result.message, 'info');
            readCookie();
        }

        // Simulate malicious JavaScript trying to access cookies
        async function simulateMaliciousJS() {
            const resultDiv = document.getElementById('attackResult');
            resultDiv.style.display = 'block';

            try {
                // This simulates what malicious JavaScript would attempt
                const cookieAccess = document.cookie;
                const response = await fetch('/simulate_attack', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({attempted_access: cookieAccess})
                });

                const result = await response.json();

                if (result.success) {
                    resultDiv.className = 'status error';
                    resultDiv.innerHTML = `
                        <strong>⚠️ ATTACK SIMULATION:</strong><br>
                        ${result.message}<br>
                        <strong>Educational Note:</strong> The cookie was accessible to JavaScript because HttpOnly flag was not set.
                        This is a security risk as malicious scripts could steal session tokens.
                    `;
                    addLogMessage(`ATTACK SIMULATION: ${result.message}`, 'error');
                } else {
                    resultDiv.className = 'status success';
                    resultDiv.innerHTML = `
                        <strong>✅ ATTACK BLOCKED:</strong><br>
                        ${result.message}<br>
                        <strong>Educational Note:</strong> The cookie was protected by HttpOnly flag, preventing JavaScript access.
                        This is the correct security practice for session cookies.
                    `;
                    addLogMessage(`ATTACK BLOCKED: ${result.message}`, 'success');
                }
            } catch (error) {
                addLogMessage(`Error in attack simulation: ${error.message}`, 'error');
            }
        }

        // Initial read
        readCookie();
        addLogMessage('Cookie Security Lab initialized. Ready for experiments!', 'info');
    </script>
</body>
</html>
"""

# Store current cookie configuration
current_config = {
    'http_only': True,  # Default to secure configuration
    'secure': True,
    'same_site': 'Lax'
}

# Simulate a session store (in memory)
session_store = {}


@app.route('/')
def index():
    """Render the main educational interface"""
    return render_template_string(
        HTML_TEMPLATE,
        http_only=current_config['http_only'],
        secure=current_config['secure'],
        same_site=current_config['same_site']
    )


@app.route('/update_config', methods=['POST'])
def update_config():
    """Update cookie security configuration"""
    global current_config
    data = request.json

    current_config['http_only'] = data.get('http_only', True)
    current_config['secure'] = data.get('secure', True)
    current_config['same_site'] = data.get('same_site', 'Lax')

    logger.info(f"Configuration updated: {current_config}")

    return jsonify({
        'status': 'success',
        'message': f"Configuration updated: HttpOnly={current_config['http_only']}, "
                   f"Secure={current_config['secure']}, SameSite={current_config['same_site']}"
    })


@app.route('/set_cookie', methods=['POST'])
def set_cookie():
    """Set a session cookie with current security configuration"""
    # Generate a unique session ID
    session_id = secrets.token_urlsafe(32)
    timestamp = datetime.now().isoformat()

    # Store in simulated session store
    session_store[session_id] = {
        'created': timestamp,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }

    # Create response with cookie
    response = make_response(jsonify({
        'status': 'success',
        'message': f"Cookie set with Session ID: {session_id[:16]}... "
                   f"(HttpOnly={current_config['http_only']}, "
                   f"Secure={current_config['secure']}, "
                   f"SameSite={current_config['same_site']})"
    }))

    # Build cookie attributes
    cookie_attrs = {
        'path': '/',
        'max_age': 3600,  # 1 hour
        'httponly': current_config['http_only'],
        'samesite': current_config['same_site']
    }

    # Add Secure flag if configured (simulated - in real HTTPS only)
    if current_config['secure']:
        cookie_attrs['secure'] = True

    # Set the cookie
    response.set_cookie('session_id', session_id, **cookie_attrs)

    logger.info(f"Cookie set: Session ID={session_id[:16]}..., Config={current_config}")

    return response


@app.route('/read_cookie')
def read_cookie():
    """Read and display current cookie information"""
    session_id = request.cookies.get('session_id')

    if not session_id:
        return jsonify({
            'status': 'info',
            'message': 'No cookie found',
            'cookie_data': None
        })

    # Get session info from store
    session_info = session_store.get(session_id, {})

    cookie_data = {
        'session_id': session_id[:16] + '...' if len(session_id) > 16 else session_id,
        'created': session_info.get('created', 'Unknown'),
        'expires': '1 hour from creation',
        'http_only': current_config['http_only'],
        'secure': current_config['secure'],
        'same_site': current_config['same_site']
    }

    logger.info(f"Cookie read: Session ID={session_id[:16]}...")

    return jsonify({
        'status': 'success',
        'message': 'Cookie read successfully',
        'cookie_data': cookie_data
    })


@app.route('/delete_cookie', methods=['POST'])
def delete_cookie():
    """Delete the current session cookie"""
    session_id = request.cookies.get('session_id')

    if session_id and session_id in session_store:
        del session_store[session_id]
        logger.info(f"Cookie deleted: Session ID={session_id[:16]}...")

    response = make_response(jsonify({
        'status': 'success',
        'message': 'Cookie deleted successfully'
    }))
    response.delete_cookie('session_id')

    return response


@app.route('/simulate_attack', methods=['POST'])
def simulate_attack():
    """
    Simulate a malicious JavaScript attempt to access cookies
    This demonstrates the HttpOnly flag protection
    """
    data = request.json
    attempted_access = data.get('attempted_access', '')

    # Get the actual cookie from the request
    actual_cookie = request.cookies.get('session_id')

    # Check if the cookie is protected by HttpOnly
    is_protected = current_config['http_only']

    if is_protected:
        # With HttpOnly, document.cookie shouldn't contain the session cookie
        logger.warning(f"Attack simulation: JavaScript attempted to access cookie but was BLOCKED by HttpOnly flag")
        return jsonify({
            'success': False,
            'message': f"Attack blocked! HttpOnly flag prevented JavaScript access to the cookie. "
                       f"JavaScript saw: '{attempted_access or 'empty'}' but the actual cookie value is protected."
        })
    else:
        # Without HttpOnly, the cookie would be accessible
        logger.error(f"Attack simulation: JavaScript successfully accessed cookie (INSECURE CONFIGURATION)")
        return jsonify({
            'success': True,
            'message': f"SECURITY BREACH! The cookie was accessible to JavaScript because HttpOnly flag is NOT set. "
                       f"Malicious script could steal: {attempted_access}"
        })


if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║         🍪 HTTP COOKIE SECURITY EDUCATIONAL LAB 🍪                      ║
    ╚═══════════════════════════════════════════════════════════════════════╝

    📚 EDUCATIONAL CONCEPTS DEMONSTRATED:

    1. HttpOnly Flag:
       - Prevents JavaScript from accessing cookies
       - Critical protection against XSS attacks
       - Toggle on/off to see the difference

    2. Secure Flag:
       - Ensures cookies only sent over HTTPS
       - Prevents man-in-the-middle attacks
       - Simulated in this local environment

    3. SameSite Attribute:
       - Controls cross-site request behavior
       - Lax: Sent with top-level navigation
       - Strict: Never sent cross-site
       - Helps prevent CSRF attacks

    4. Cookie Lifecycle:
       - Creation, storage, transmission, expiration

    🔬 HOW TO USE THIS LAB:

    1. Open your browser to: http://127.0.0.1:5000
    2. Try different cookie configurations
    3. Set a cookie and observe the security flags
    4. Click "Simulate Malicious JavaScript" to see HttpOnly in action
    5. Watch the educational log for detailed explanations

    ⚠️  IMPORTANT: This is a SAFE educational environment
    - No real data is ever transmitted or stolen
    - All operations are simulated locally
    - Perfect for understanding cookie security concepts

    🚀 Starting the educational server...
    """)

    # Run the Flask application
    app.run(host='127.0.0.1', port=5000, debug=True)