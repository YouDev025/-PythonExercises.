#!/usr/bin/env python3
"""
File Upload Security Lab - Flask Application
Demonstrates secure vs vulnerable file upload implementations
Run with: python file_upload_security_lab.py
"""

import os
import uuid
import logging
from pathlib import Path
from flask import Flask, request, render_template_string, redirect, url_for, flash

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# Configuration
UPLOAD_FOLDER = Path('uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf'}
MODE_VULNERABLE = 'vulnerable'
MODE_SECURE = 'secure'

# Global variable to control mode (can be toggled via web interface)
current_mode = MODE_VULNERABLE  # Start in vulnerable mode for demonstration

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)

# HTML Templates (embedded as strings)
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Upload Security Lab</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-top: 0;
        }
        .mode-indicator {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
        }
        .mode-vulnerable {
            background-color: #ffebee;
            color: #c62828;
            border: 1px solid #ffcdd2;
        }
        .mode-secure {
            background-color: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #c8e6c9;
        }
        .upload-form {
            margin: 20px 0;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 5px;
        }
        .btn {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
            text-decoration: none;
            display: inline-block;
        }
        .btn-danger {
            background-color: #f44336;
        }
        .btn-warning {
            background-color: #ff9800;
        }
        .btn-info {
            background-color: #2196f3;
        }
        .file-list {
            margin-top: 20px;
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
        }
        .file-item {
            padding: 5px;
            border-bottom: 1px solid #eee;
            font-family: monospace;
        }
        .message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        input[type="file"] {
            margin: 10px 0;
            padding: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 File Upload Security Lab</h1>

        <div class="mode-indicator {{ 'mode-vulnerable' if mode == 'vulnerable' else 'mode-secure' }}">
            Current Mode: <strong>{{ mode.upper() }}</strong>
            {% if mode == 'vulnerable' %}
                ⚠️ Accepts any file type - NO validation!
            {% else %}
                ✅ Only safe files allowed (jpg, png, gif, pdf)
            {% endif %}
        </div>

        <div class="upload-form">
            <h3>Upload File</h3>
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <br>
                <button type="submit" class="btn">Upload File</button>
            </form>
        </div>

        <div>
            <a href="/toggle_mode" class="btn {{ 'btn-warning' if mode == 'vulnerable' else 'btn-info' }}">
                🔄 Switch to {{ 'Secure' if mode == 'vulnerable' else 'Vulnerable' }} Mode
            </a>
            <a href="/" class="btn">🔄 Refresh</a>
        </div>

        {% if message %}
        <div class="message {{ message_type }}">
            {{ message }}
        </div>
        {% endif %}

        <div class="file-list">
            <h3>📁 Uploaded Files ({{ files|length }})</h3>
            {% if files %}
                {% for file in files %}
                <div class="file-item">
                    {{ file }}
                    {% if mode == 'vulnerable' and (file.endswith('.php') or file.endswith('.py') or file.endswith('.exe')) %}
                        <span style="color: red;">⚠️ DANGEROUS FILE DETECTED!</span>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <p>No files uploaded yet.</p>
            {% endif %}
        </div>

        <div class="info" style="margin-top: 20px;">
            <h4>📖 Security Education</h4>
            <p><strong>Vulnerable Mode:</strong> Accepts ANY file type. Try uploading a <code>.php</code>, <code>.py</code>, or <code>.exe</code> file to see the risk!</p>
            <p><strong>Secure Mode:</strong> Implements proper security measures:</p>
            <ul>
                <li>✅ Only allows safe extensions (jpg, png, gif, pdf)</li>
                <li>✅ Validates actual file type (not just extension)</li>
                <li>✅ Renames files with UUID to prevent path traversal</li>
                <li>✅ Limits file size to 5MB</li>
                <li>✅ Prevents directory traversal attacks</li>
            </ul>
        </div>
    </div>
</body>
</html>
'''


def get_allowed_extensions():
    """Return set of allowed extensions for secure mode"""
    return ALLOWED_EXTENSIONS


def is_safe_extension(filename):
    """Check if file has a safe extension"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_file_type(filepath):
    """Validate actual file type (magic numbers)"""
    # Check file signature (magic numbers)
    with open(filepath, 'rb') as f:
        header = f.read(8)

    # Check for various file types
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif header.startswith(b'\xff\xd8'):
        return 'jpg'
    elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        return 'gif'
    elif header.startswith(b'%PDF'):
        return 'pdf'
    return None


def save_file_secure(file, filename):
    """Save file with security measures (secure mode)"""
    try:
        # 1. Check extension
        if not is_safe_extension(filename):
            return False, "File extension not allowed. Allowed: jpg, png, gif, pdf"

        # 2. Generate safe filename with UUID
        ext = filename.rsplit('.', 1)[1].lower()
        safe_filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = UPLOAD_FOLDER / safe_filename

        # 3. Save temporarily
        file.save(filepath)

        # 4. Validate actual file type
        detected_type = validate_file_type(filepath)
        if not detected_type or detected_type != ext:
            # Remove malicious file
            filepath.unlink()
            return False, f"File type mismatch! Detected: {detected_type}, Expected: {ext}"

        # 5. Additional security: prevent execution by setting permissions
        os.chmod(filepath, 0o644)  # Read-only for others

        logger.info(f"SECURE MODE: Uploaded {safe_filename} (original: {filename})")
        return True, f"File uploaded securely! Saved as: {safe_filename}"

    except Exception as e:
        logger.error(f"Error in secure upload: {e}")
        return False, f"Upload failed: {str(e)}"


def save_file_vulnerable(file, filename):
    """Save file without any validation (vulnerable mode)"""
    try:
        # DANGEROUS: No validation, path traversal possible
        filepath = UPLOAD_FOLDER / filename

        # Check for path traversal (simulate security but still vulnerable)
        if '..' in filename or filename.startswith('/'):
            logger.warning(f"POTENTIAL PATH TRAVERSAL ATTEMPT: {filename}")

        file.save(filepath)

        # Set executable permissions (dangerous!)
        if filename.endswith(('.php', '.py', '.sh', '.exe')):
            os.chmod(filepath, 0o755)  # Make executable
            logger.warning(f"DANGEROUS FILE UPLOADED: {filename} (executable)")

        logger.info(f"VULNERABLE MODE: Uploaded {filename}")
        return True, f"File uploaded (UNSAFE): {filename}"

    except Exception as e:
        logger.error(f"Error in vulnerable upload: {e}")
        return False, f"Upload failed: {str(e)}"


@app.route('/')
def index():
    """Main page with upload form"""
    # Get list of uploaded files
    files = [f.name for f in UPLOAD_FOLDER.iterdir() if f.is_file()]
    files.sort(reverse=True)

    return render_template_string(
        INDEX_TEMPLATE,
        mode=current_mode,
        files=files[:20],  # Show last 20 files
        message=None,
        message_type=None
    )


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return render_template_string(
            INDEX_TEMPLATE,
            mode=current_mode,
            files=[f.name for f in UPLOAD_FOLDER.iterdir() if f.is_file()],
            message="No file selected!",
            message_type="error"
        )

    file = request.files['file']

    if file.filename == '':
        return render_template_string(
            INDEX_TEMPLATE,
            mode=current_mode,
            files=[f.name for f in UPLOAD_FOLDER.iterdir() if f.is_file()],
            message="No file selected!",
            message_type="error"
        )

    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset pointer

    if size > app.config['MAX_CONTENT_LENGTH']:
        return render_template_string(
            INDEX_TEMPLATE,
            mode=current_mode,
            files=[f.name for f in UPLOAD_FOLDER.iterdir() if f.is_file()],
            message=f"File too large! Max size: {app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)}MB",
            message_type="error"
        )

    # Choose mode
    if current_mode == MODE_SECURE:
        success, msg = save_file_secure(file, file.filename)
    else:
        success, msg = save_file_vulnerable(file, file.filename)

    # Refresh file list
    files = [f.name for f in UPLOAD_FOLDER.iterdir() if f.is_file()]

    return render_template_string(
        INDEX_TEMPLATE,
        mode=current_mode,
        files=files[:20],
        message=msg,
        message_type="success" if success else "error"
    )


@app.route('/toggle_mode')
def toggle_mode():
    """Toggle between vulnerable and secure modes"""
    global current_mode
    current_mode = MODE_SECURE if current_mode == MODE_VULNERABLE else MODE_VULNERABLE

    # Log mode change
    logger.info(f"Mode changed to: {current_mode.upper()}")

    # Show notification
    files = [f.name for f in UPLOAD_FOLDER.iterdir() if f.is_file()]

    message = f"Switched to {current_mode.upper()} mode. "
    if current_mode == MODE_SECURE:
        message += "Now only safe files (jpg, png, pdf) are allowed."
    else:
        message += "⚠️ WARNING: Now accepting ANY file type - vulnerable to attacks!"

    return render_template_string(
        INDEX_TEMPLATE,
        mode=current_mode,
        files=files[:20],
        message=message,
        message_type="info"
    )


@app.route('/demo_attack')
def demo_attack():
    """Demonstrate what happens when a dangerous file is uploaded"""
    if current_mode == MODE_VULNERABLE:
        # Create a simulated malicious PHP file
        malicious_content = """<?php
// MALICIOUS CODE - SIMULATION ONLY
echo "This is a SIMULATED malicious PHP file!";
echo "In a real attack, this could execute arbitrary code on the server.";
system('whoami');  // Would show server user
?>
"""
        test_file = UPLOAD_FOLDER / "simulated_malicious.php"
        with open(test_file, 'w') as f:
            f.write(malicious_content)

        logger.warning("SIMULATION: Malicious PHP file created for demonstration")

        message = "⚠️ SIMULATION: A malicious PHP file was created! In vulnerable mode, this could lead to remote code execution (RCE). Switch to Secure Mode to prevent this."
        message_type = "error"
    else:
        message = "✅ In Secure Mode, this attack is blocked. Try uploading a .php file to see the validation in action!"
        message_type = "success"

    files = [f.name for f in UPLOAD_FOLDER.iterdir() if f.is_file()]

    return render_template_string(
        INDEX_TEMPLATE,
        mode=current_mode,
        files=files[:20],
        message=message,
        message_type=message_type
    )


if __name__ == '__main__':
    print("=" * 60)
    print("🔒 FILE UPLOAD SECURITY LAB")
    print("=" * 60)
    print(f"Server starting at: http://127.0.0.1:5000")
    print(f"Upload folder: {UPLOAD_FOLDER.absolute()}")
    print(f"Current mode: {current_mode.upper()}")
    print("\n⚠️  SECURITY WARNING: This is a lab environment!")
    print("   Do not deploy in production or expose to the internet.")
    print("=" * 60)

    # Run Flask app
    app.run(debug=True, host='127.0.0.1', port=5000)