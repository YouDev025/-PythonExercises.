#!/usr/bin/env python3
"""
Command Injection Security Lab - Flask Application
Demonstrates secure vs vulnerable command execution implementations
Run with: python command_injection_security_lab.py
"""

import os
import re
import subprocess
import logging
import ipaddress
import platform
from flask import Flask, request, render_template_string, redirect, url_for, flash

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'command-injection-lab-secure-key-2024'
app.config['MAX_CONTENT_LENGTH'] = 1024  # Limit input size

# Configuration
MODE_VULNERABLE = 'vulnerable'
MODE_SECURE = 'secure'
current_mode = MODE_VULNERABLE  # Start in vulnerable mode for demonstration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# HTML Templates (embedded as strings)
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Command Injection Security Lab</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Courier New', 'Segoe UI', monospace;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: #0a0e27;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            overflow: hidden;
            border: 1px solid #2a3f5e;
        }

        .header {
            background: #0a0e27;
            padding: 25px;
            border-bottom: 3px solid #00ff9d;
            text-align: center;
        }

        .header h1 {
            color: #00ff9d;
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header p {
            color: #8892b0;
            font-size: 14px;
        }

        .mode-badge {
            display: inline-block;
            padding: 8px 20px;
            margin-top: 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }

        .mode-vulnerable {
            background: #ff4757;
            color: white;
            box-shadow: 0 0 15px rgba(255,71,87,0.5);
        }

        .mode-secure {
            background: #00ff9d;
            color: #0a0e27;
            box-shadow: 0 0 15px rgba(0,255,157,0.5);
        }

        .content {
            padding: 30px;
        }

        .input-section {
            background: #0f142e;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 25px;
            border-left: 4px solid #00ff9d;
        }

        label {
            color: #00ff9d;
            font-weight: bold;
            display: block;
            margin-bottom: 10px;
            font-size: 16px;
        }

        input[type="text"] {
            width: 100%;
            padding: 12px;
            background: #1a1f3a;
            border: 2px solid #2a3f5e;
            color: #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            font-family: 'Courier New', monospace;
            transition: all 0.3s;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #00ff9d;
            box-shadow: 0 0 10px rgba(0,255,157,0.3);
        }

        button {
            background: #00ff9d;
            color: #0a0e27;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-size: 14px;
            margin-top: 15px;
            transition: all 0.3s;
            font-family: monospace;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,255,157,0.4);
        }

        .toggle-btn {
            background: #2a3f5e;
            color: white;
            margin-left: 10px;
        }

        .toggle-btn:hover {
            background: #3a5a7e;
        }

        .result {
            background: #0f142e;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            border: 1px solid #2a3f5e;
        }

        .result h3 {
            color: #00ff9d;
            margin-bottom: 15px;
            font-size: 18px;
        }

        .command-box {
            background: #000000;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #e0e0e0;
            border-left: 3px solid #00ff9d;
        }

        .warning {
            background: #ff4757;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            border-left: 4px solid #ff0000;
        }

        .success {
            background: #00ff9d;
            color: #0a0e27;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            border-left: 4px solid #00aa66;
        }

        .info {
            background: #2a3f5e;
            color: #e0e0e0;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }

        .examples {
            margin-top: 25px;
            background: #0f142e;
            padding: 20px;
            border-radius: 10px;
        }

        .examples h3 {
            color: #00ff9d;
            margin-bottom: 10px;
        }

        .example-item {
            background: #1a1f3a;
            padding: 8px;
            margin: 5px 0;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            cursor: pointer;
        }

        .example-item:hover {
            background: #2a2f4a;
        }

        .danger {
            color: #ff4757;
            font-weight: bold;
        }

        hr {
            border-color: #2a3f5e;
            margin: 20px 0;
        }

        .footer {
            background: #0a0e27;
            padding: 20px;
            text-align: center;
            color: #8892b0;
            font-size: 12px;
            border-top: 1px solid #2a3f5e;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Command Injection Security Lab</h1>
            <p>Learn how command injection attacks work and how to prevent them</p>
            <div class="mode-badge mode-{{ 'vulnerable' if mode == 'vulnerable' else 'secure' }}">
                {{ '⚠️ VULNERABLE MODE' if mode == 'vulnerable' else '✅ SECURE MODE' }}
            </div>
        </div>

        <div class="content">
            <div class="input-section">
                <label>🔍 Target IP Address or Domain:</label>
                <form method="POST" action="/execute">
                    <input type="text" name="target" placeholder="e.g., 8.8.8.8 or google.com" value="{{ request.form.get('target', '') }}" required>
                    <div>
                        <button type="submit">🚀 Execute Command</button>
                        <a href="/toggle_mode"><button type="button" class="toggle-btn">🔄 Switch to {{ 'Secure' if mode == 'vulnerable' else 'Vulnerable' }} Mode</button></a>
                    </div>
                </form>
            </div>

            {% if result %}
            <div class="result">
                <h3>📊 Execution Result</h3>
                <div class="command-box">
                    <strong>Command executed:</strong><br>
                    {{ command }}<br><br>
                    <strong>Output:</strong><br>
                    {{ result }}
                </div>
            </div>
            {% endif %}

            {% if warning %}
            <div class="warning">
                ⚠️ {{ warning }}
            </div>
            {% endif %}

            {% if info %}
            <div class="info">
                ℹ️ {{ info }}
            </div>
            {% endif %}

            <div class="examples">
                <h3>🎯 Test Examples</h3>
                <p style="color: #8892b0; margin-bottom: 10px; font-size: 12px;">Click on any example to test:</p>
                <div class="example-item" onclick="document.querySelector('input[name=\'target\']').value='8.8.8.8'">8.8.8.8 (Normal IP)</div>
                <div class="example-item" onclick="document.querySelector('input[name=\'target\']').value='google.com'">google.com (Normal Domain)</div>
                <div class="example-item danger" onclick="document.querySelector('input[name=\'target\']').value='8.8.8.8; ls'">8.8.8.8; ls (Command Injection - List files)</div>
                <div class="example-item danger" onclick="document.querySelector('input[name=\'target\']').value='8.8.8.8 && whoami'">8.8.8.8 && whoami (Command Injection - Who am I)</div>
                <div class="example-item danger" onclick="document.querySelector('input[name=\'target\']').value='8.8.8.8 | cat /etc/passwd'">8.8.8.8 | cat /etc/passwd (Command Injection - Read files)</div>
                <div class="example-item danger" onclick="document.querySelector('input[name=\'target\']').value='$(id)'">$(id) (Command Substitution)</div>
                <div class="example-item danger" onclick="document.querySelector('input[name=\'target\']').value='`whoami`'">`whoami` (Backtick Injection)</div>
            </div>

            <div class="info" style="margin-top: 20px;">
                <h3>📖 Security Education</h3>
                <p><strong>Vulnerable Mode:</strong> Directly concatenates user input into shell commands. Try the injection examples above to see the risk!</p>
                <p><strong>Secure Mode:</strong> Implements proper security measures:</p>
                <ul style="margin-left: 20px; margin-top: 5px;">
                    <li>✅ Validates input against IP/domain patterns</li>
                    <li>✅ Uses subprocess with no shell (shell=False)</li>
                    <li>✅ Sanitizes and escapes user input</li>
                    <li>✅ Detects and blocks malicious patterns</li>
                    <li>✅ Uses parameterized commands</li>
                </ul>
            </div>
        </div>

        <div class="footer">
            ⚠️ SECURITY LAB - For educational purposes only | Never executes harmful commands on real systems
        </div>
    </div>

    <script>
        // Simple JavaScript for example injection
        const exampleItems = document.querySelectorAll('.example-item');
        exampleItems.forEach(item => {
            item.addEventListener('click', function() {
                const input = document.querySelector('input[name="target"]');
                input.value = this.innerText;
                input.style.borderColor = '#ff4757';
                setTimeout(() => {
                    input.style.borderColor = '#2a3f5e';
                }, 500);
            });
        });
    </script>
</body>
</html>
'''


def detect_malicious_pattern(input_string):
    """Detect suspicious command injection patterns"""
    dangerous_patterns = [
        r';', r'&&', r'\|\|', r'\|', r'`', r'\$\(', r'\$\{',
        r'>', r'>>', r'<', r'&\s', r'\\n', r'\\r', r'\\t',
        r'whoami', r'cat\s', r'ls\s', r'id\s', r'passwd', r'shadow',
        r'rm\s', r'del\s', r'wget', r'curl', r'nc\s', r'netcat'
    ]

    detected = []
    for pattern in dangerous_patterns:
        if re.search(pattern, input_string, re.IGNORECASE):
            detected.append(pattern)

    return detected


def validate_target_secure(target):
    """Validate target input in secure mode"""
    # Remove whitespace
    target = target.strip()

    # Check for empty input
    if not target:
        return False, "Input cannot be empty"

    # Check for dangerous patterns
    malicious = detect_malicious_pattern(target)
    if malicious:
        return False, f"Potentially malicious input detected: {', '.join(malicious)}"

    # Validate as IP address
    try:
        ipaddress.ip_address(target)
        return True, target
    except ValueError:
        pass

    # Validate as domain name
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    if re.match(domain_pattern, target) and len(target) <= 253:
        return True, target

    return False, "Invalid IP address or domain name format"


def execute_command_vulnerable(target):
    """Execute command in vulnerable mode (simulated with validation)"""
    # Log the attempt
    logger.warning(f"VULNERABLE MODE - Target input: {target}")

    # Detect malicious patterns for simulation only
    malicious_patterns = detect_malicious_pattern(target)

    if malicious_patterns:
        # Simulate what would happen in a real injection
        logger.critical(f"COMMAND INJECTION DETECTED! Patterns: {malicious_patterns}")

        # Construct the simulated command (for display only)
        if platform.system() == 'Windows':
            base_cmd = f"ping -n 1 {target}"
        else:
            base_cmd = f"ping -c 1 {target}"

        simulated_output = f"[SIMULATION] Command injection attempt!\n"
        simulated_output += f"Would execute: {base_cmd}\n\n"
        simulated_output += f"⚠️ In a real vulnerable system, this could:\n"
        simulated_output += f"- Read sensitive files\n"
        simulated_output += f"- Execute arbitrary code\n"
        simulated_output += f"- Compromise the entire server\n"
        simulated_output += f"- Install malware or backdoors\n\n"
        simulated_output += f"Detected injection patterns: {', '.join(malicious_patterns)}"

        return base_cmd, simulated_output, "Command injection attempt detected and simulated!"

    # Normal execution simulation
    if platform.system() == 'Windows':
        command = f"ping -n 1 {target}"
    else:
        command = f"ping -c 1 {target}"

    # Simulate ping output (for educational purposes only)
    simulated_output = f"[SIMULATION] Command executed: {command}\n\n"
    simulated_output += f"PING {target} (192.168.1.1): 56 data bytes\n"
    simulated_output += f"64 bytes from 192.168.1.1: icmp_seq=0 ttl=64 time=0.123 ms\n\n"
    simulated_output += f"--- {target} ping statistics ---\n"
    simulated_output += f"1 packets transmitted, 1 packets received, 0.0% packet loss\n"
    simulated_output += f"round-trip min/avg/max/stddev = 0.123/0.123/0.123/0.000 ms\n"
    simulated_output += f"\n✅ Ping completed successfully (SIMULATED for security lab)"

    return command, simulated_output, None


def execute_command_secure(target):
    """Execute command in secure mode with proper validation"""
    logger.info(f"SECURE MODE - Validating target: {target}")

    # Validate input
    is_valid, validated_target = validate_target_secure(target)

    if not is_valid:
        logger.warning(f"SECURE MODE - Invalid input rejected: {target}")
        return None, None, validated_target

    # Use safe command execution (no shell)
    try:
        if platform.system() == 'Windows':
            # Windows ping command (safe with list format)
            command = ["ping", "-n", "1", validated_target]
            result = subprocess.run(command, capture_output=True, text=True, timeout=5, shell=False)
            output = result.stdout if result.stdout else result.stderr
        else:
            # Unix ping command (safe with list format)
            command = ["ping", "-c", "1", validated_target]
            result = subprocess.run(command, capture_output=True, text=True, timeout=5, shell=False)
            output = result.stdout if result.stdout else result.stderr

        logger.info(f"SECURE MODE - Successfully executed ping for: {validated_target}")
        return " ".join(command), output, None

    except subprocess.TimeoutExpired:
        logger.error(f"SECURE MODE - Timeout for: {validated_target}")
        return None, None, "Command timed out (5 seconds)"
    except Exception as e:
        logger.error(f"SECURE MODE - Error: {str(e)}")
        return None, None, f"Error executing command: {str(e)}"


@app.route('/')
def index():
    """Main page with command execution form"""
    return render_template_string(
        INDEX_TEMPLATE,
        mode=current_mode,
        result=None,
        command=None,
        warning=None,
        info=None,
        request=request
    )


@app.route('/execute', methods=['POST'])
def execute():
    """Handle command execution"""
    target = request.form.get('target', '').strip()

    if not target:
        return render_template_string(
            INDEX_TEMPLATE,
            mode=current_mode,
            result=None,
            command=None,
            warning="Please enter a target IP address or domain",
            info=None,
            request=request
        )

    # Execute based on current mode
    if current_mode == MODE_SECURE:
        command, output, error = execute_command_secure(target)

        if error:
            return render_template_string(
                INDEX_TEMPLATE,
                mode=current_mode,
                result=error,
                command="Command blocked due to validation",
                warning="Input validation failed!",
                info=None,
                request=request
            )

        return render_template_string(
            INDEX_TEMPLATE,
            mode=current_mode,
            result=output,
            command=command,
            warning=None,
            info="✅ Secure mode: Input validated and sanitized",
            request=request
        )

    else:  # Vulnerable mode
        command, output, warning = execute_command_vulnerable(target)

        if warning:
            return render_template_string(
                INDEX_TEMPLATE,
                mode=current_mode,
                result=output,
                command=command,
                warning=warning,
                info="⚠️ Vulnerable mode: Input directly concatenated into command!",
                request=request
            )

        return render_template_string(
            INDEX_TEMPLATE,
            mode=current_mode,
            result=output,
            command=command,
            warning=None,
            info="⚠️ Vulnerable mode: No input validation - try injection attacks!",
            request=request
        )


@app.route('/toggle_mode')
def toggle_mode():
    """Toggle between vulnerable and secure modes"""
    global current_mode
    current_mode = MODE_SECURE if current_mode == MODE_VULNERABLE else MODE_VULNERABLE

    logger.info(f"Mode toggled to: {current_mode.upper()}")

    info_message = f"Switched to {current_mode.upper()} mode. "
    if current_mode == MODE_SECURE:
        info_message += "Input is now validated and sanitized. Injection attempts will be blocked."
    else:
        info_message += "⚠️ WARNING: Now vulnerable to command injection! Try the example payloads."

    return render_template_string(
        INDEX_TEMPLATE,
        mode=current_mode,
        result=None,
        command=None,
        warning=None,
        info=info_message,
        request=request
    )


if __name__ == '__main__':
    print("=" * 70)
    print("🔧 COMMAND INJECTION SECURITY LAB")
    print("=" * 70)
    print(f"Server running at: http://127.0.0.1:5000")
    print(f"Current mode: {current_mode.upper()}")
    print("\n📖 EDUCATIONAL PURPOSE ONLY")
    print("This lab demonstrates command injection vulnerabilities")
    print("and how to properly secure applications against them.")
    print("\n⚠️  IMPORTANT:")
    print("   - Never deploy this in production")
    print("   - Do not expose to the internet")
    print("   - Only use for learning purposes")
    print("=" * 70)

    # Run Flask app
    app.run(debug=True, host='127.0.0.1', port=5000)