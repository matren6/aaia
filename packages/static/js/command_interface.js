/**
 * Command Interface
 * Handles command submission, history, and real-time progress tracking
 */

class CommandInterface {
    constructor() {
        this.commands = [];
        this.currentExecution = null;
        this.wsClient = wsClient;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupWebSocketUpdates();
        this.loadCommandHistory();
    }

    setupEventListeners() {
        const cmdForm = document.getElementById('commandForm');
        if (cmdForm) {
            cmdForm.addEventListener('submit', (e) => this.submitCommand(e));
        }

        const clearBtn = document.getElementById('clearHistoryBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearHistory());
        }

        // Keyboard shortcut: Ctrl+Enter to submit
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const input = document.getElementById('commandInput');
                if (input && document.activeElement === input) {
                    this.submitCommand(new Event('submit'));
                }
            }
        });
    }

    setupWebSocketUpdates() {
        if (!this.wsClient) return;

        this.wsClient.on('command_queued', (data) => {
            this.onCommandQueued(data);
        });

        this.wsClient.on('command_started', (data) => {
            this.onCommandStarted(data);
        });

        this.wsClient.on('command_progress', (data) => {
            this.onCommandProgress(data);
        });

        this.wsClient.on('command_error', (data) => {
            this.onCommandError(data);
        });

        this.wsClient.on('command_cancelled', (data) => {
            this.onCommandCancelled(data);
        });
    }

    async submitCommand(e) {
        if (e.preventDefault) e.preventDefault();

        const input = document.getElementById('commandInput');
        const command = input.value.trim();

        if (!command) {
            alert('Please enter a command');
            return;
        }

        const urgent = document.getElementById('urgentCheckbox')?.checked || false;

        try {
            const response = await fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command, urgent })
            });

            if (response.ok) {
                const data = await response.json();
                this.currentExecution = data.execution_id;
                
                // Clear input
                input.value = '';
                
                // Show execution panel
                this.showExecutionPanel(data.execution_id);
                
                // Load history to show new command
                this.loadCommandHistory();
            } else {
                alert('Failed to execute command');
            }
        } catch (error) {
            console.error('Error executing command:', error);
            alert('Error executing command');
        }
    }

    onCommandQueued(data) {
        const item = this.createHistoryItem(data);
        item.classList.add('queued');
        this.prependToHistory(item);
        this.updateExecutionPanel(data);
    }

    onCommandStarted(data) {
        this.updateHistoryItem(data.execution_id, { status: 'running' });
        this.updateExecutionPanel(data, 'Running...');
    }

    onCommandProgress(data) {
        this.updateHistoryItem(data.execution_id, {
            status: 'completed',
            output: data.output
        });
        this.updateExecutionPanel(data, null, data.output);
    }

    onCommandError(data) {
        this.updateHistoryItem(data.execution_id, {
            status: 'error',
            error: data.error
        });
        this.updateExecutionPanel(data, `Error: ${data.error}`);
    }

    onCommandCancelled(data) {
        this.updateHistoryItem(data.execution_id, { status: 'cancelled' });
        this.updateExecutionPanel(data, 'Cancelled');
    }

    async loadCommandHistory() {
        try {
            const response = await fetch('/api/command/history?limit=20&offset=0');
            if (response.ok) {
                const data = await response.json();
                this.displayHistory(data.commands || []);
            }
        } catch (error) {
            console.error('Error loading command history:', error);
        }
    }

    displayHistory(commands) {
        const container = document.getElementById('commandHistoryList');
        if (!container) return;

        if (commands.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-3">No commands executed</p>';
            return;
        }

        const html = commands.map(cmd => this.createHistoryItem(cmd).outerHTML).join('');
        container.innerHTML = html;
    }

    createHistoryItem(cmd) {
        const item = document.createElement('div');
        item.className = `command-history-item alert alert-light mb-2 ${cmd.status}`;
        item.dataset.executionId = cmd.execution_id;

        const statusBadge = this.getStatusBadge(cmd.status);
        const duration = cmd.duration_seconds 
            ? ` (${cmd.duration_seconds.toFixed(2)}s)`
            : '';

        item.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                    <strong>${cmd.command}</strong>
                    <br>
                    <small class="text-muted">
                        ${new Date(cmd.started_at).toLocaleString()}${duration}
                    </small>
                </div>
                ${statusBadge}
            </div>
            ${cmd.output ? `
                <div class="bg-dark text-light p-2 rounded small" style="max-height: 150px; overflow-y: auto;">
                    <pre class="mb-0">${this.escapeHtml(cmd.output)}</pre>
                </div>
            ` : ''}
            ${cmd.error ? `
                <div class="alert alert-danger small mt-2 mb-0">
                    ${this.escapeHtml(cmd.error)}
                </div>
            ` : ''}
        `;

        item.addEventListener('click', () => this.showExecutionPanel(cmd.execution_id));

        return item;
    }

    getStatusBadge(status) {
        const badges = {
            'queued': '<span class="badge bg-secondary">⏳ Queued</span>',
            'running': '<span class="badge bg-info">▶ Running</span>',
            'completed': '<span class="badge bg-success">✓ Complete</span>',
            'error': '<span class="badge bg-danger">✗ Error</span>',
            'cancelled': '<span class="badge bg-warning">⊘ Cancelled</span>'
        };
        return badges[status] || '<span class="badge bg-secondary">Unknown</span>';
    }

    prependToHistory(item) {
        const container = document.getElementById('commandHistoryList');
        if (container) {
            if (container.textContent.includes('No commands')) {
                container.innerHTML = '';
            }
            container.insertBefore(item, container.firstChild);
        }
    }

    updateHistoryItem(executionId, updates) {
        const item = document.querySelector(`[data-execution-id="${executionId}"]`);
        if (!item) return;

        if (updates.status) {
            item.className = `command-history-item alert alert-light mb-2 ${updates.status}`;
            const oldBadge = item.querySelector('.badge');
            if (oldBadge) {
                oldBadge.outerHTML = this.getStatusBadge(updates.status);
            }
        }

        if (updates.output) {
            const outputDiv = item.querySelector('.bg-dark');
            if (outputDiv) {
                outputDiv.innerHTML = `<pre class="mb-0">${this.escapeHtml(updates.output)}</pre>`;
            } else {
                const newOutput = document.createElement('div');
                newOutput.className = 'bg-dark text-light p-2 rounded small';
                newOutput.style.cssText = 'max-height: 150px; overflow-y: auto;';
                newOutput.innerHTML = `<pre class="mb-0">${this.escapeHtml(updates.output)}</pre>`;
                item.appendChild(newOutput);
            }
        }

        if (updates.error) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger small mt-2 mb-0';
            errorDiv.textContent = updates.error;
            item.appendChild(errorDiv);
        }
    }

    showExecutionPanel(executionId) {
        const panel = document.getElementById('executionPanel');
        if (!panel) return;

        const item = document.querySelector(`[data-execution-id="${executionId}"]`);
        if (item) {
            item.scrollIntoView({ behavior: 'smooth' });
            item.classList.add('highlight');
            setTimeout(() => item.classList.remove('highlight'), 2000);
        }
    }

    updateExecutionPanel(data, status, output) {
        const panel = document.getElementById('executionPanel');
        if (!panel) return;

        if (status) {
            const statusEl = panel.querySelector('.execution-status');
            if (statusEl) statusEl.textContent = status;
        }

        if (output) {
            const outputEl = panel.querySelector('.execution-output');
            if (outputEl) {
                outputEl.innerHTML = `<pre>${this.escapeHtml(output)}</pre>`;
                outputEl.scrollTop = outputEl.scrollHeight;
            }
        }
    }

    async clearHistory() {
        if (!confirm('Clear all command history?')) return;

        try {
            const response = await fetch('/api/command/history', { method: 'DELETE' });
            if (response.ok) {
                this.loadCommandHistory();
                alert('Command history cleared');
            }
        } catch (error) {
            console.error('Error clearing history:', error);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

let commandInterface = null;

function initCommandInterface() {
    if (!commandInterface) {
        commandInterface = new CommandInterface();
    }
    return commandInterface;
}

document.addEventListener('DOMContentLoaded', initCommandInterface);
