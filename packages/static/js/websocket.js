/**
 * WebSocket Client Handler
 * Manages Socket.IO connection and event handling for real-time updates
 */

class WebSocketClient {
    constructor(options = {}) {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
        this.eventHandlers = {};
        this.debug = options.debug || false;

        this.init();
    }

    init() {
        /**
         * Initialize Socket.IO connection
         * Requires socket.io library: https://cdn.socket.io/4.6.0/socket.io.min.js
         */
        if (typeof io === 'undefined') {
            console.error('Socket.IO library not loaded. Add <script src="https://cdn.socket.io/4.6.0/socket.io.min.js"></script>');
            return;
        }

        this.socket = io({
            reconnection: true,
            reconnectionDelay: this.reconnectDelay,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: this.maxReconnectAttempts,
        });

        this.setupEventHandlers();
    }

    setupEventHandlers() {
        /**
         * Set up Socket.IO event handlers
         */
        if (!this.socket) return;

        // Connection events
        this.socket.on('connect', () => this.onConnect());
        this.socket.on('disconnect', () => this.onDisconnect());
        this.socket.on('connect_error', (error) => this.onConnectError(error));

        // Data events
        this.socket.on('system_status', (data) => this.emit('system_status', data));
        this.socket.on('event_feed', (data) => this.emit('event_feed', data));

        // Goal events
        this.socket.on('goal_created', (data) => this.emit('goal_created', data));
        this.socket.on('goal_completed', (data) => this.emit('goal_completed', data));
        this.socket.on('goal_failed', (data) => this.emit('goal_failed', data));

        // Economic events
        this.socket.on('economic_transaction', (data) => this.emit('economic_transaction', data));
        this.socket.on('income_recorded', (data) => this.emit('income_recorded', data));
        this.socket.on('economic_crisis', (data) => this.emit('economic_crisis', data));

        // LLM events
        this.socket.on('llm_request', (data) => this.emit('llm_request', data));
        this.socket.on('llm_response', (data) => this.emit('llm_response', data));
        this.socket.on('llm_error', (data) => this.emit('llm_error', data));

        // Scheduler events
        this.socket.on('scheduler_task_started', (data) => this.emit('scheduler_task_started', data));
        this.socket.on('scheduler_task_completed', (data) => this.emit('scheduler_task_completed', data));

        // Resource events
        this.socket.on('resource_usage', (data) => this.emit('resource_usage', data));

        // Notifications
        this.socket.on('notification', (data) => this.emit('notification', data));

        // Command updates
        this.socket.on('command_update', (data) => this.emit('command_update', data));
    }

    onConnect() {
        /**
         * Handle successful connection
         */
        this.connected = true;
        this.reconnectAttempts = 0;
        this.log('Connected to WebSocket server');

        // Update connection status in UI
        this.updateConnectionStatus(true);

        // Emit custom connect event
        this.emit('connected', { timestamp: new Date().toISOString() });
    }

    onDisconnect() {
        /**
         * Handle disconnection
         */
        this.connected = false;
        this.log('Disconnected from WebSocket server');

        // Update connection status in UI
        this.updateConnectionStatus(false);

        // Emit custom disconnect event
        this.emit('disconnected', { timestamp: new Date().toISOString() });
    }

    onConnectError(error) {
        /**
         * Handle connection error
         */
        this.reconnectAttempts++;
        this.log(`Connection error: ${error}. Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
    }

    on(eventName, callback) {
        /**
         * Register event handler
         */
        if (!this.eventHandlers[eventName]) {
            this.eventHandlers[eventName] = [];
        }
        this.eventHandlers[eventName].push(callback);
    }

    emit(eventName, data) {
        /**
         * Emit event to registered handlers
         */
        if (this.eventHandlers[eventName]) {
            this.eventHandlers[eventName].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventName}:`, error);
                }
            });
        }
    }

    updateConnectionStatus(connected) {
        /**
         * Update connection status indicator in UI
         */
        const statusIndicator = document.getElementById('connection-status');
        if (!statusIndicator) return;

        if (connected) {
            statusIndicator.classList.add('connected');
            statusIndicator.classList.remove('disconnected');
            statusIndicator.innerHTML = '● Connected';
            statusIndicator.title = 'WebSocket connected';
        } else {
            statusIndicator.classList.add('disconnected');
            statusIndicator.classList.remove('connected');
            statusIndicator.innerHTML = '○ Disconnected';
            statusIndicator.title = 'WebSocket disconnected';
        }
    }

    isConnected() {
        /**
         * Check if WebSocket is connected
         */
        return this.connected && this.socket && this.socket.connected;
    }

    log(message) {
        /**
         * Log message if debug enabled
         */
        if (this.debug) {
            console.log(`[WebSocket] ${message}`);
        }
    }

    disconnect() {
        /**
         * Disconnect from server
         */
        if (this.socket) {
            this.socket.disconnect();
        }
    }

    reconnect() {
        /**
         * Manually reconnect to server
         */
        if (this.socket) {
            this.socket.connect();
        }
    }
}

// Global instance
let wsClient = null;

function initWebSocket() {
    /**
     * Initialize global WebSocket client
     */
    if (!wsClient) {
        wsClient = new WebSocketClient({ debug: false });
    }
    return wsClient;
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWebSocket);
} else {
    initWebSocket();
}
