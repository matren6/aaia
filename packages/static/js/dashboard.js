/**
 * Dashboard Real-Time Updates
 * Updates dashboard elements based on WebSocket events
 */

class Dashboard {
    constructor() {
        this.wsClient = null;
        this.statusCache = {};
        this.eventFeedMaxItems = 50;
        this.init();
    }

    init() {
        /**
         * Initialize dashboard
         */
        this.wsClient = wsClient || initWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        /**
         * Set up WebSocket event listeners for dashboard
         */
        if (!this.wsClient) return;

        // Connection events
        this.wsClient.on('connected', () => this.onConnected());
        this.wsClient.on('disconnected', () => this.onDisconnected());

        // System updates
        this.wsClient.on('system_status', (data) => this.updateSystemStatus(data));
        this.wsClient.on('event_feed', (data) => this.addEventToFeed(data));

        // Goal events
        this.wsClient.on('goal_created', (data) => this.onGoalCreated(data));
        this.wsClient.on('goal_completed', (data) => this.onGoalCompleted(data));

        // Economic events
        this.wsClient.on('economic_transaction', (data) => this.onTransaction(data));

        // Notifications
        this.wsClient.on('notification', (data) => this.showNotification(data));
    }

    loadInitialData() {
        /**
         * Load initial dashboard data via REST API
         */
        this.fetchSystemStatus();
        this.fetchEventFeed();
    }

    async fetchSystemStatus() {
        /**
         * Fetch system status from API
         */
        try {
            const response = await fetch('/api/status');
            if (response.ok) {
                const data = await response.json();
                this.updateSystemStatus(data);
            }
        } catch (error) {
            console.error('Error fetching system status:', error);
        }
    }

    async fetchEventFeed() {
        /**
         * Fetch recent events from API (for initial load)
         */
        try {
            const response = await fetch('/api/logs?limit=10&offset=0');
            if (response.ok) {
                const data = await response.json();
                // Display initial logs
                this.displayInitialEvents(data.logs);
            }
        } catch (error) {
            console.error('Error fetching event feed:', error);
        }
    }

    updateSystemStatus(data) {
        /**
         * Update system status display
         */
        if (!data) return;

        // Cache status
        this.statusCache = data;

        // Update balance
        if (data.balance !== undefined) {
            const balanceEl = document.getElementById('balance-value');
            if (balanceEl) {
                balanceEl.textContent = `$${data.balance.toFixed(2)}`;
                // Add color based on balance
                const balanceCard = document.getElementById('balance-card');
                if (balanceCard) {
                    if (data.balance < 10) {
                        balanceCard.classList.add('text-danger');
                    } else if (data.balance < 50) {
                        balanceCard.classList.add('text-warning');
                    } else {
                        balanceCard.classList.remove('text-danger', 'text-warning');
                    }
                }
            }
        }

        // Update actions logged
        if (data.actions_logged !== undefined) {
            const actionsEl = document.getElementById('actions-value');
            if (actionsEl) {
                actionsEl.textContent = data.actions_logged.toLocaleString();
            }
        }

        // Update tier
        if (data.tier) {
            const tierEl = document.getElementById('tier-value');
            if (tierEl) {
                tierEl.textContent = data.tier.name || 'Unknown';
            }

            const progressEl = document.getElementById('tier-progress');
            if (progressEl && data.tier.progress !== undefined) {
                progressEl.style.width = `${data.tier.progress * 100}%`;
            }
        }

        // Update scheduler status
        if (data.scheduler_running !== undefined) {
            const schedulerEl = document.getElementById('scheduler-status');
            if (schedulerEl) {
                schedulerEl.textContent = data.scheduler_running ? '● Running' : '● Stopped';
                schedulerEl.className = data.scheduler_running ? 'text-success' : 'text-danger';
            }
        }
    }

    addEventToFeed(event) {
        /**
         * Add event to activity feed (real-time)
         */
        if (!event) return;

        const feedContainer = document.getElementById('activity-feed');
        if (!feedContainer) return;

        // Create event item
        const eventItem = document.createElement('div');
        eventItem.className = 'event-item alert alert-info fade show';
        eventItem.style.animation = 'slideIn 0.3s ease-in';

        const timestamp = new Date(event.timestamp).toLocaleTimeString();
        const typeLabel = this.getEventTypeLabel(event.type);

        eventItem.innerHTML = `
            <div class="d-flex justify-content-between">
                <span><strong>${typeLabel}</strong></span>
                <small class="text-muted">${timestamp}</small>
            </div>
            <small>${JSON.stringify(event.data).substring(0, 100)}...</small>
        `;

        // Add to top of feed
        feedContainer.insertBefore(eventItem, feedContainer.firstChild);

        // Keep only last N items
        while (feedContainer.children.length > this.eventFeedMaxItems) {
            feedContainer.removeChild(feedContainer.lastChild);
        }

        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            eventItem.classList.remove('show');
            setTimeout(() => eventItem.remove(), 150);
        }, 10000);
    }

    displayInitialEvents(logs) {
        /**
         * Display initial events from API
         */
        const feedContainer = document.getElementById('activity-feed');
        if (!feedContainer || !logs) return;

        feedContainer.innerHTML = '';

        logs.forEach(log => {
            const eventItem = document.createElement('div');
            eventItem.className = 'event-item alert alert-light small';

            eventItem.innerHTML = `
                <div class="d-flex justify-content-between">
                    <span><strong>${log.action || 'Event'}</strong></span>
                    <small>${new Date(log.timestamp).toLocaleTimeString()}</small>
                </div>
            `;

            feedContainer.appendChild(eventItem);
        });
    }

    onGoalCreated(data) {
        /**
         * Handle goal created event
         */
        if (!data) return;
        
        // Could update goals page if visible
        const goalsContainer = document.getElementById('goals-container');
        if (goalsContainer) {
            this.showNotification({
                type: 'info',
                message: `Goal created: ${data.goal_text || 'New goal'}`
            });
        }
    }

    onGoalCompleted(data) {
        /**
         * Handle goal completed event
         */
        if (!data) return;

        this.showNotification({
            type: 'success',
            message: `Goal completed: ${data.goal_text || 'Goal'}`
        });
    }

    onTransaction(data) {
        /**
         * Handle economic transaction event
         */
        if (!data) return;

        const amount = data.amount || 0;
        const verb = amount > 0 ? 'Income' : 'Expense';
        const icon = amount > 0 ? '💰' : '💸';

        this.addEventToFeed({
            type: 'ECONOMIC_TRANSACTION',
            data: { amount, reason: data.reason },
            timestamp: new Date().toISOString()
        });
    }

    showNotification(data) {
        /**
         * Show notification to user
         */
        if (!data) return;

        // Browser notification (if permitted)
        if ('Notification' in window && Notification.permission === 'granted' && data.type === 'urgent') {
            new Notification('AAIA Alert', {
                body: data.message,
                icon: '/static/img/logo.png',
                badge: '/static/img/logo.png'
            });
        }

        // In-page notification
        this.showInPageNotification(data);
    }

    showInPageNotification(data) {
        /**
         * Show in-page notification
         */
        const container = document.getElementById('notifications-container');
        if (!container) return;

        const notif = document.createElement('div');
        notif.className = `alert alert-${this.getAlertClass(data.type)} alert-dismissible fade show`;
        notif.role = 'alert';

        notif.innerHTML = `
            <strong>${this.capitalizeFirstLetter(data.type)}:</strong> ${data.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        container.appendChild(notif);

        // Auto-dismiss non-urgent
        if (data.type !== 'urgent') {
            setTimeout(() => {
                notif.classList.remove('show');
                setTimeout(() => notif.remove(), 150);
            }, 5000);
        }
    }

    onConnected() {
        /**
         * Handle WebSocket connection
         */
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.classList.add('connected');
            statusEl.textContent = '● Connected';
        }
    }

    onDisconnected() {
        /**
         * Handle WebSocket disconnection
         */
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.classList.add('disconnected');
            statusEl.textContent = '○ Disconnected';
        }
    }

    getEventTypeLabel(eventType) {
        /**
         * Get human-readable label for event type
         */
        const labels = {
            'ECONOMIC_TRANSACTION': '💰 Transaction',
            'GOAL_CREATED': '🎯 Goal Created',
            'GOAL_COMPLETED': '✅ Goal Completed',
            'LLM_REQUEST': '🤖 LLM Request',
            'LLM_RESPONSE': '💬 LLM Response',
            'TOOL_CREATED': '🔧 Tool Created',
            'SCHEDULER_TASK_STARTED': '⚙️ Task Started',
            'SCHEDULER_TASK_COMPLETED': '✓ Task Completed',
        };
        return labels[eventType] || eventType;
    }

    getAlertClass(type) {
        /**
         * Get Bootstrap alert class for notification type
         */
        const classes = {
            'info': 'info',
            'warning': 'warning',
            'error': 'danger',
            'urgent': 'danger',
            'success': 'success',
        };
        return classes[type] || 'info';
    }

    capitalizeFirstLetter(str) {
        /**
         * Capitalize first letter
         */
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }

    requestNotificationPermission() {
        /**
         * Request browser notification permission
         */
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
}

// Global instance
let dashboard = null;

function initDashboard() {
    /**
     * Initialize global dashboard
     */
    if (!dashboard) {
        dashboard = new Dashboard();
    }
    return dashboard;
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .event-item {
        animation: slideIn 0.3s ease-in;
    }

    #connection-status {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.875rem;
        font-weight: bold;
    }

    #connection-status.connected {
        color: #28a745;
        background-color: #d4edda;
    }

    #connection-status.disconnected {
        color: #dc3545;
        background-color: #f8d7da;
    }
`;
document.head.appendChild(style);
