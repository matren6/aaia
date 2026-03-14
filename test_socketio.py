#!/usr/bin/env python3
"""
Test Flask-SocketIO WebSocket functionality
"""

import sys
sys.path.insert(0, '/mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia/packages')

print("Testing Flask-SocketIO installation...")

try:
    from flask_socketio import SocketIO
    print("✅ Flask-SocketIO imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Flask-SocketIO: {e}")
    sys.exit(1)

try:
    from flask import Flask
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Flask: {e}")
    sys.exit(1)

try:
    from modules.web_server import WebServer, HAS_SOCKETIO
    print(f"✅ WebServer imported successfully")
    print(f"   HAS_SOCKETIO = {HAS_SOCKETIO}")
except ImportError as e:
    print(f"❌ Failed to import WebServer: {e}")
    sys.exit(1)

try:
    from modules.web_socketio import WebSocketHandler
    print("✅ WebSocketHandler imported successfully")
except ImportError as e:
    print(f"❌ Failed to import WebSocketHandler: {e}")
    sys.exit(1)

# Test creating a simple Flask-SocketIO app
try:
    app = Flask(__name__)
    socketio = SocketIO(app, async_mode='threading')
    print("✅ Flask-SocketIO app created successfully")
    print(f"   SocketIO async_mode: {socketio.async_mode}")
except Exception as e:
    print(f"❌ Failed to create Flask-SocketIO app: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED - Flask-SocketIO is working!")
print("="*60)
