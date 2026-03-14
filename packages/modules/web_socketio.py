"""
WebSocket Module for Real-Time Dashboard Updates

Handles WebSocket connections and emits real-time events from Event Bus
to connected web clients for live dashboard updates.
"""

import threading
import time
import logging
from datetime import datetime
from typing import Set

from modules.bus import EventBus, EventType, get_event_bus

# Suppress werkzeug logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)


class WebSocketHandler:
    """Handles WebSocket connections and event broadcasting."""

    def __init__(self, socketio=None, event_bus=None, data_aggregator=None, container=None):
        """
        Initialize WebSocket handler.

        Args:
            socketio: Flask-SocketIO instance
            event_bus: EventBus for subscribing to events
            data_aggregator: DashboardDataAggregator for data access
            container: DI Container
        """
        self.socketio = socketio
        self.event_bus = event_bus or get_event_bus()
        self.data_aggregator = data_aggregator
        self.container = container
        self.connected_clients: Set[str] = set()
        self.subscription_ids = []

    def setup(self):
        """Set up WebSocket handlers and Event Bus subscriptions."""
        if not self.socketio:
            return

        # Register WebSocket event handlers
        self.socketio.on_event('connect', self.on_connect)
        self.socketio.on_event('disconnect', self.on_disconnect)

        # Subscribe to Event Bus events
        self._subscribe_to_events()

        # Start periodic update thread
        self._start_periodic_updates()

    def on_connect(self):
        """Handle client connection."""
        from flask_socketio import request
        client_id = request.sid
        self.connected_clients.add(client_id)
        
        # Send initial system status
        status = self.data_aggregator.get_system_status() if self.data_aggregator else {}
        self.socketio.emit('system_status', status, to=client_id)
        
        return True

    def on_disconnect(self):
        """Handle client disconnection."""
        from flask_socketio import request
        client_id = request.sid
        self.connected_clients.discard(client_id)

    def _subscribe_to_events(self):
        """Subscribe to Event Bus events."""
        if not self.event_bus:
            return

        # Major event types to subscribe to (only if they exist)
        event_types_to_try = [
            'ECONOMIC_TRANSACTION',
            'GOAL_CREATED',
            'GOAL_COMPLETED',
            'LLM_REQUEST',
            'LLM_RESPONSE',
            'TOOL_CREATED',
            'EVOLUTION_STARTED',
            'DIAGNOSIS_COMPLETED',
            'SCHEDULER_TASK_STARTED',
            'SCHEDULER_TASK_COMPLETED',
            'SYSTEM_START',
            'SYSTEM_SHUTDOWN',
        ]

        for event_name in event_types_to_try:
            try:
                # Check if EventType has this attribute
                if hasattr(EventType, event_name):
                    event_type = getattr(EventType, event_name)
                    sub_id = self.event_bus.on(event_type, self._handle_event)
                    self.subscription_ids.append(sub_id)
            except Exception as e:
                # Silently skip events that don't exist or can't be subscribed to
                logging.debug(f"Could not subscribe to {event_name}: {e}")
                pass

    def _handle_event(self, event):
        """
        Handle Event Bus event and emit to connected clients.
        
        Args:
            event: Event object from Event Bus
        """
        if not self.socketio or not event:
            return

        try:
            event_data = {
                'type': getattr(event.type, 'value', str(event.type)),
                'data': event.data if hasattr(event, 'data') else {},
                'source': getattr(event, 'source', 'unknown'),
                'timestamp': datetime.now().isoformat(),
            }

            # Emit to all connected clients
            self.socketio.emit('event_feed', event_data, broadcast=True)

        except Exception as e:
            logging.error(f"Error handling WebSocket event: {e}")

    def _start_periodic_updates(self):
        """Start background thread for periodic updates."""
        def periodic_update():
            while len(self.connected_clients) > 0:
                try:
                    # Update system status every 5 seconds
                    if self.data_aggregator:
                        status = self.data_aggregator.get_system_status()
                        self.socketio.emit('system_status', status, broadcast=True)

                    time.sleep(5)
                except Exception as e:
                    logging.error(f"Error in periodic update: {e}")
                    time.sleep(5)

        thread = threading.Thread(target=periodic_update, daemon=True, name='WebSocketPeriodicUpdater')
        thread.start()

    def emit_notification(self, notification_type: str, message: str, action_url: str = None):
        """
        Emit notification to all connected clients.

        Args:
            notification_type: 'info', 'warning', 'error', or 'urgent'
            message: Notification message
            action_url: Optional URL for action button
        """
        if not self.socketio:
            return

        notification = {
            'type': notification_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
        }
        if action_url:
            notification['action_url'] = action_url

        self.socketio.emit('notification', notification, broadcast=True)

    def emit_command_update(self, execution_id: str, status: str, output: str = None):
        """
        Emit command progress update.

        Args:
            execution_id: Command execution ID
            status: 'started', 'running', 'completed', 'error'
            output: Command output (optional)
        """
        if not self.socketio:
            return

        update = {
            'execution_id': execution_id,
            'status': status,
            'timestamp': datetime.now().isoformat(),
        }
        if output:
            update['output'] = output

        self.socketio.emit('command_update', update, broadcast=True)

    def emit_command_result(self, execution_id: str, status: str, 
                           output: str = '', error: str = ''):
        """
        Emit command execution result.

        Args:
            execution_id: Command execution ID
            status: 'completed' or 'error'
            output: Command output
            error: Error message if failed
        """
        if not self.socketio:
            return

        result = {
            'execution_id': execution_id,
            'status': status,
            'output': output,
            'error': error,
            'timestamp': datetime.now().isoformat(),
        }

        self.socketio.emit('command_result', result, broadcast=True)
