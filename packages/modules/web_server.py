"""
Web Server Module for AAIA - Real-time Dashboard and API

Provides Flask-based web server for monitoring AAIA system status,
viewing logs, goals, economics, and master model data in real-time.

This module runs in a separate thread to avoid blocking the main
application loop.
"""

import threading
import time
import sqlite3
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, request

# Try to import SocketIO, but don't fail if not installed
try:
    from flask_socketio import SocketIO
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False
    SocketIO = None

from modules.bus import EventBus, get_event_bus


def _suppress_flask_logging():
    """Suppress Flask's verbose logging to keep console clean."""
    # Suppress Werkzeug (Flask's WSGI server) request logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Suppress Flask's main logger
    app_log = logging.getLogger('flask')
    app_log.setLevel(logging.ERROR)

    # Remove all handlers from werkzeug logger
    for handler in log.handlers[:]:
        log.removeHandler(handler)


class WebServer:
    """Flask web server for AAIA dashboard and API."""

    def __init__(self, event_bus=None, container=None, config=None, quiet=True, data_aggregator=None):
        """
        Initialize web server.

        Args:
            event_bus: EventBus instance for event subscriptions
            container: DI Container for accessing other modules
            config: SystemConfig with web server settings
            quiet: If True (default), suppress Flask console logging
            data_aggregator: DashboardDataAggregator for data access
        """
        self.event_bus = event_bus or get_event_bus()
        self.container = container
        self.config = config
        self.quiet = quiet
        self.data_aggregator = data_aggregator

        # Get web server config
        if config:
            web_config = config.web_server
        else:
            from modules.settings import get_config
            web_config = get_config().web_server

        self.host = web_config.host
        self.port = web_config.port
        self.debug = web_config.debug
        self.secret_key = web_config.secret_key

        # Suppress logging if quiet mode enabled (default: yes)
        if self.quiet:
            _suppress_flask_logging()

        # Create Flask app
        self.app = self._create_app()

        # Initialize SocketIO (after app creation) - if available
        self.socketio = None
        self.ws_handler = None
        if HAS_SOCKETIO and SocketIO:
            self.socketio = SocketIO(
                self.app,
                async_mode='threading',
                cors_allowed_origins='*',
                ping_timeout=60,
                ping_interval=25
            )
            # Setup WebSocket handler
            self._setup_websocket()

        # Thread management
        self.thread = None
        self.running = False

    def _create_app(self) -> Flask:
        """Create and configure Flask application."""
        app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent.parent / "templates"),
            static_folder=str(Path(__file__).parent.parent / "static"),
        )

        app.config["SECRET_KEY"] = self.secret_key

        # Suppress app logger if in quiet mode
        if self.quiet:
            app.logger.setLevel(logging.ERROR)

        # Register routes
        self._register_routes(app)

        return app

    def _register_routes(self, app: Flask):
        """Register Flask routes."""
        from modules.web_api import create_api_blueprint

        @app.route("/")
        def index():
            """Main dashboard page."""
            return render_template("dashboard.html")

        @app.route("/goals")
        def goals():
            """Goals management page."""
            return render_template("goals.html")

        @app.route("/economics")
        def economics():
            """Economics page."""
            return render_template("economics.html")

        @app.route("/master-model")
        def master_model():
            """Master psychological profile page."""
            return render_template("master_model.html")

        @app.route("/logs")
        def logs():
            """System logs page."""
            return render_template("logs.html")

        @app.route("/tasks")
        def tasks():
            """Scheduler tasks page."""
            return render_template("tasks.html")

        @app.route("/tools")
        def tools():
            """Tools registry page."""
            return render_template("tools.html")

        @app.route("/config")
        def config():
            """Configuration page."""
            return render_template("config.html")

        # Register API blueprint
        api_blueprint = create_api_blueprint(
            data_aggregator=self.data_aggregator,
            container=self.container
        )
        app.register_blueprint(api_blueprint)

        @app.errorhandler(404)
        def not_found(e):
            """Handle 404 errors."""
            return jsonify({"error": "Not found"}), 404

        @app.errorhandler(500)
        def server_error(e):
            """Handle 500 errors."""
            return jsonify({"error": "Internal server error"}), 500

    def _setup_websocket(self):
        """Set up WebSocket handler."""
        from modules.web_socketio import WebSocketHandler

        self.ws_handler = WebSocketHandler(
            socketio=self.socketio,
            event_bus=self.event_bus,
            data_aggregator=self.data_aggregator,
            container=self.container
        )
        self.ws_handler.setup()

    def _get_system_status(self) -> dict:
        """Gather current system status."""
        try:
            from modules.settings import get_config

            config = get_config()
            
            # Get basic info
            status = {
                "timestamp": time.time(),
                "status": "running",
                "uptime": 0,  # TODO: track uptime
            }

            # Try to get database info
            try:
                conn = sqlite3.connect(config.database.path)
                cursor = conn.cursor()

                # Get balance
                cursor.execute(
                    "SELECT value FROM system_state WHERE key='current_balance'"
                )
                balance_row = cursor.fetchone()
                status["balance"] = (
                    float(balance_row[0]) if balance_row else 100.00
                )

                # Get action count
                cursor.execute("SELECT COUNT(*) FROM action_log")
                status["actions_logged"] = cursor.fetchone()[0]

                conn.close()
            except Exception as e:
                status["balance"] = 100.00
                status["actions_logged"] = 0

            # Get scheduler status if available
            try:
                if self.container:
                    scheduler = self.container.get("AutonomousScheduler")
                    status["scheduler_running"] = (
                        scheduler.running if scheduler else False
                    )
            except Exception:
                status["scheduler_running"] = False

            return status
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": time.time(),
            }

    def start(self):
        """Start web server in background thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="WebServerThread",
        )
        self.thread.start()

    def _run_server(self):
        """Run Flask-SocketIO or Flask server (in thread)."""
        try:
            if self.socketio and HAS_SOCKETIO:
                self.socketio.run(
                    self.app,
                    host=self.host,
                    port=self.port,
                    debug=self.debug,
                    use_reloader=False,
                    allow_unsafe_werkzeug=True
                )
            else:
                # Fallback to regular Flask
                self.app.run(
                    host=self.host,
                    port=self.port,
                    debug=self.debug,
                    use_reloader=False,
                    threaded=True
                )
        except Exception as e:
            if self.running:
                print(f"Web server error: {e}")
        finally:
            self.running = False

    def stop(self):
        """Stop web server (graceful shutdown)."""
        self.running = False
        # Flask-Werkzeug doesn't have a built-in stop method for threaded servers
        # The daemon thread will terminate when the main process exits


def create_app(test_mode=False, quiet=True):
    """Factory function to create Flask app (for testing)."""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent.parent / "templates"),
        static_folder=str(Path(__file__).parent.parent / "static"),
    )

    if test_mode:
        app.config["TESTING"] = True

    app.config["SECRET_KEY"] = "test-secret-key"

    # Suppress logging if quiet mode enabled
    if quiet:
        _suppress_flask_logging()
        app.logger.setLevel(logging.ERROR)

    # Register routes
    @app.route("/")
    def index():
        return render_template("dashboard.html")

    @app.route("/api/status")
    def api_status():
        return jsonify({"status": "healthy", "timestamp": time.time()})

    @app.route("/api/health")
    def api_health():
        return jsonify({"status": "healthy", "timestamp": time.time()})

    return app
