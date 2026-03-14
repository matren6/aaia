#!/usr/bin/env python3
"""
Live test of AAIA WebSocket functionality
Starts web server and verifies WebSocket connections work
"""

import sys
import time
import threading
sys.path.insert(0, '/mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia/packages')

print("Starting WebSocket Live Test...")
print("="*60)

# Import modules
from modules.container import Container
from modules.setup import SystemBuilder
from modules.settings import get_config

print("✅ Modules imported")

# Build system
config = get_config()
print(f"Config loaded - WebServer enabled: {config.web_server.enabled}")

builder = SystemBuilder(config)

try:
    # build() returns a dict with 'container' and 'modules'
    result = builder.build()
    container = result['container']
    print("✅ System built")
except Exception as e:
    print(f"❌ Failed to build system: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check if WebServer is registered
if not container.has('WebServer'):
    print("❌ WebServer is not registered in container!")
    sys.exit(1)
else:
    print("✅ WebServer is registered in container")

# Get web server
try:
    web_server = container.get('WebServer')
    print(f"✅ WebServer retrieved: {web_server}")
except Exception as e:
    print(f"❌ Failed to get WebServer: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if web_server is None:
    print("❌ WebServer is None!")
    sys.exit(1)

print(f"   Host: {web_server.host}")
print(f"   Port: {web_server.port}")
print(f"   SocketIO available: {web_server.socketio is not None}")
print(f"   WebSocket handler: {web_server.ws_handler is not None}")

# Start web server
print("\n" + "="*60)
print("Starting web server...")
print("="*60)

web_server.start()
time.sleep(2)

if web_server.running:
    print(f"✅ Web server started successfully")
    print(f"   URL: http://{web_server.host}:{web_server.port}")
    print(f"   Thread: {web_server.thread.name if web_server.thread else 'None'}")
    print(f"   Thread alive: {web_server.thread.is_alive() if web_server.thread else False}")
    
    # Check WebSocket handler
    if web_server.ws_handler:
        print(f"\n✅ WebSocket handler initialized")
        print(f"   Connected clients: {len(web_server.ws_handler.connected_clients)}")
        print(f"   Event subscriptions: {len(web_server.ws_handler.subscription_ids)}")
    
    print("\n" + "="*60)
    print("Web server is running!")
    print("Open browser to: http://192.168.178.104:5000")
    print("Press Ctrl+C to stop...")
    print("="*60)
    
    # Keep running for 30 seconds
    try:
        for i in range(30):
            time.sleep(1)
            if web_server.ws_handler:
                clients = len(web_server.ws_handler.connected_clients)
                if clients > 0:
                    print(f"  [{i+1}s] Connected clients: {clients}")
    except KeyboardInterrupt:
        print("\nStopping...")
    
    print("\n✅ Test completed successfully!")
    
else:
    print("❌ Web server failed to start")
    sys.exit(1)
