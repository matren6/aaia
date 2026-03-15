"""
REST API Module for Web Dashboard

Provides REST endpoints for accessing AAIA system data.
Uses Flask Blueprints for modular endpoint organization.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

# Suppress Werkzeug logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)


def create_api_blueprint(data_aggregator=None, container=None):
    """
    Create REST API blueprint.
    
    Args:
        data_aggregator: DashboardDataAggregator instance
        container: DI Container for accessing modules
    
    Returns:
        Blueprint with all API endpoints
    """
    api = Blueprint('api', __name__, url_prefix='/api')

    # Store references for use in endpoints
    api.data_aggregator = data_aggregator
    api.container = container

    # ===== System Status =====

    @api.route('/status', methods=['GET'])
    def get_status():
        """Get current system status."""
        try:
            if api.data_aggregator:
                data = api.data_aggregator.get_system_status()
            else:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "status": "running",
                    "balance": 100.0,
                    "actions_logged": 0,
                }
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
        })

    # ===== Goals =====

    @api.route('/goals', methods=['GET'])
    def get_goals():
        """Get goals with optional filtering and pagination."""
        try:
            status = request.args.get('status', 'active')
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))

            # Validate parameters
            if limit < 1 or limit > 500:
                limit = 50
            if offset < 0:
                offset = 0

            if api.data_aggregator:
                data = api.data_aggregator.get_goals(status=status, limit=limit, offset=offset)
            else:
                data = {"goals": [], "total": 0, "limit": limit, "offset": offset}

            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/goals/<int:goal_id>', methods=['GET'])
    def get_goal(goal_id):
        """Get specific goal details."""
        try:
            # TODO: Implement when goal detail view needed
            return jsonify({"error": "Not implemented"}), 501
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Economics =====

    @api.route('/economics', methods=['GET'])
    def get_economics():
        """Get economics data for specified period."""
        try:
            days = int(request.args.get('days', 30))

            if days < 1 or days > 365:
                days = 30

            if api.data_aggregator:
                data = api.data_aggregator.get_economics(days=days)
            else:
                data = {
                    "balance": 100.0,
                    "total_income": 0,
                    "total_costs": 0,
                    "net_profit": 0,
                    "profit_margin": 0,
                    "is_profitable": False,
                }

            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/economics/resource-costs', methods=['GET'])
    def get_resource_costs():
        """Get breakdown of resource costs."""
        try:
            days = int(request.args.get('days', 30))
            
            # TODO: Implement detailed resource cost breakdown
            return jsonify({
                "total": 0.0,
                "breakdown": {
                    "cpu": 0.0,
                    "memory": 0.0,
                    "llm": 0.0,
                    "other": 0.0,
                },
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Master Model =====

    @api.route('/master-model/profile', methods=['GET'])
    def get_master_profile():
        """Get master psychological profile."""
        try:
            if api.data_aggregator:
                data = api.data_aggregator.get_master_profile()
            else:
                data = {
                    "profile": {},
                    "interaction_count": 0,
                    "last_reflection": None,
                    "confidence": 0.0,
                }

            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/master-model/interactions', methods=['GET'])
    def get_master_interactions():
        """Get recent master interactions."""
        try:
            days = int(request.args.get('days', 7))
            limit = int(request.args.get('limit', 100))

            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            db_manager = api.container.get('DatabaseManager')

            try:
                interactions = db_manager.query(
                    '''SELECT id, timestamp, interaction_type, user_input, 
                              system_response, intent_detected, success, notes
                       FROM master_interactions
                       WHERE timestamp >= datetime('now', '-' || ? || ' days')
                       ORDER BY timestamp DESC
                       LIMIT ?''',
                    (days, limit)
                )

                return jsonify({
                    "interactions": [dict(row) for row in interactions],
                    "total": len(interactions),
                })
            except Exception as db_error:
                if "no such table" in str(db_error).lower():
                    return jsonify({
                        "interactions": [],
                        "total": 0,
                        "warning": "master_interactions table not available (database migration needed)"
                    })
                raise

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/master-model/reflect', methods=['POST'])
    def trigger_reflection():
        """Trigger a reflection cycle."""
        try:
            # TODO: Implement when reflection cycle control needed
            return jsonify({"error": "Not implemented"}), 501
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Logs =====

    @api.route('/logs', methods=['GET'])
    def get_logs():
        """Get action logs with optional filtering."""
        try:
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            action = request.args.get('action')
            status = request.args.get('status')

            # Validate parameters
            if limit < 1 or limit > 500:
                limit = 50
            if offset < 0:
                offset = 0

            filters = {}
            if action:
                filters['action'] = action
            if status:
                filters['status'] = status

            if api.data_aggregator:
                data = api.data_aggregator.get_logs(filters=filters, limit=limit, offset=offset)
            else:
                data = {"logs": [], "total": 0, "limit": limit, "offset": offset}

            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/logs/export', methods=['GET'])
    def export_logs():
        """Export logs as CSV or JSON."""
        try:
            format_type = request.args.get('format', 'json')

            # TODO: Implement export functionality
            return jsonify({"error": "Not implemented"}), 501
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== LLM Interactions =====

    @api.route('/llm/interactions', methods=['GET'])
    def get_llm_interactions():
        """Get recent LLM interactions."""
        try:
            limit = int(request.args.get('limit', 100))
            provider = request.args.get('provider')

            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            llm_tracker = api.container.get_optional('LLMInteractionTracker')
            if not llm_tracker:
                db_manager = api.container.get('DatabaseManager')
                try:
                    if provider:
                        rows = db_manager.query('''
                            SELECT * FROM llm_interactions
                            WHERE provider = ?
                            ORDER BY timestamp DESC
                            LIMIT ?
                        ''', (provider, limit))
                    else:
                        rows = db_manager.query('''
                            SELECT * FROM llm_interactions
                            ORDER BY timestamp DESC
                            LIMIT ?
                        ''', (limit,))

                    interactions = [dict(row) for row in rows]
                    return jsonify({
                        "interactions": interactions,
                        "total": len(interactions)
                    })
                except Exception as db_error:
                    if "no such table" in str(db_error).lower():
                        return jsonify({
                            "interactions": [],
                            "total": 0,
                            "warning": "llm_interactions table not available (database migration needed)"
                        })
                    raise

            interactions = llm_tracker.get_interactions(provider=provider, limit=limit)
            return jsonify({
                "interactions": interactions,
                "total": len(interactions)
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/llm/statistics', methods=['GET'])
    def get_llm_statistics():
        """Get LLM usage statistics."""
        try:
            hours = int(request.args.get('hours', 24))

            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            llm_tracker = api.container.get_optional('LLMInteractionTracker')
            if not llm_tracker:
                db_manager = api.container.get('DatabaseManager')
                try:
                    rows = db_manager.query('''
                        SELECT 
                            provider,
                            model,
                            COUNT(*) as call_count,
                            SUM(tokens_used) as total_tokens,
                            SUM(cost) as total_cost,
                            AVG(latency_ms) as avg_latency_ms
                        FROM llm_interactions
                        WHERE timestamp >= datetime('now', '-' || ? || ' hours')
                        GROUP BY provider, model
                        ORDER BY call_count DESC
                    ''', (hours,))

                    return jsonify({
                        'statistics': [dict(row) for row in rows],
                        'period_hours': hours
                    })
                except Exception as db_error:
                    if "no such table" in str(db_error).lower():
                        return jsonify({
                            'statistics': [],
                            'period_hours': hours,
                            'warning': 'llm_interactions table not available'
                        })
                    raise

            stats = llm_tracker.get_interaction_stats(hours=hours)
            return jsonify(stats)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Tasks =====

    @api.route('/tasks', methods=['GET'])
    def get_tasks():
        """Get scheduler tasks."""
        try:
            if api.data_aggregator:
                data = api.data_aggregator.get_tasks()
            else:
                data = {"tasks": [], "next_proposed_action": None}

            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/tasks/<task_id>/trigger', methods=['POST'])
    def trigger_task(task_id):
        """Manually trigger a scheduler task."""
        try:
            if api.container:
                scheduler = api.container.get('AutonomousScheduler')
                # TODO: Implement task triggering
                return jsonify({
                    "success": True,
                    "message": f"Task '{task_id}' triggered",
                })
            return jsonify({"error": "Scheduler not available"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/tasks/<task_id>/toggle', methods=['PUT'])
    def toggle_task(task_id):
        """Enable/disable a scheduler task."""
        try:
            data = request.get_json()
            enabled = data.get('enabled', True)

            if api.container:
                scheduler = api.container.get('AutonomousScheduler')
                # TODO: Implement task toggling
                return jsonify({
                    "success": True,
                    "task": {"id": task_id, "enabled": enabled},
                })
            return jsonify({"error": "Scheduler not available"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Tools =====

    @api.route('/tools', methods=['GET'])
    def get_tools():
        """Get registered tools."""
        try:
            if api.data_aggregator:
                data = api.data_aggregator.get_tools()
            else:
                data = {"tools": [], "total": 0}

            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/tools/<tool_name>', methods=['DELETE'])
    def delete_tool(tool_name):
        """Delete a tool."""
        try:
            # TODO: Implement tool deletion
            return jsonify({"error": "Not implemented"}), 501
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Configuration =====

    @api.route('/config', methods=['GET'])
    def get_config():
        """Get current configuration."""
        try:
            if api.data_aggregator:
                data = api.data_aggregator.get_config()
            else:
                data = {}

            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/config/<path:key>', methods=['PUT'])
    def update_config(key):
        """Update configuration value."""
        try:
            data = request.get_json()
            value = data.get('value')

            # TODO: Implement config update with validation
            return jsonify({
                "success": True,
                "key": key,
                "new_value": value,
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Commands (Master <-> Agent Communication) =====

    @api.route('/command', methods=['POST'])
    def execute_command():
        """Execute a command from the master."""
        try:
            data = request.get_json()
            command = data.get('command', '').strip()
            urgent = data.get('urgent', False)
            context = data.get('context', {})

            if not command:
                return jsonify({"error": "Command cannot be empty"}), 400

            # Get command executor from container
            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            command_executor = api.container.get_optional('CommandExecutor')
            if not command_executor:
                return jsonify({"error": "Command executor not available"}), 500

            # Execute command
            execution_id = command_executor.execute_command(
                command=command,
                urgent=urgent,
                context=context
            )

            return jsonify({
                "success": True,
                "execution_id": execution_id,
                "command": command,
                "status": "queued"
            }), 202

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/command/<execution_id>', methods=['GET'])
    def get_command_status(execution_id):
        """Get status of a command execution."""
        try:
            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            command_executor = api.container.get_optional('CommandExecutor')
            if not command_executor:
                return jsonify({"error": "Command executor not available"}), 500

            execution = command_executor.get_execution(execution_id)
            if not execution:
                return jsonify({"error": "Execution not found"}), 404

            return jsonify(execution.to_dict())

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/command/history', methods=['GET'])
    def get_command_history():
        """Get command execution history."""
        try:
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))

            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            command_executor = api.container.get_optional('CommandExecutor')
            if not command_executor:
                return jsonify({"error": "Command executor not available"}), 500

            commands = command_executor.get_history(limit=limit, offset=offset)

            return jsonify({
                "commands": commands,
                "limit": limit,
                "offset": offset,
                "total": len(commands)
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/command/<execution_id>', methods=['DELETE'])
    def cancel_command(execution_id):
        """Cancel a queued or running command."""
        try:
            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            command_executor = api.container.get_optional('CommandExecutor')
            if not command_executor:
                return jsonify({"error": "Command executor not available"}), 500

            success = command_executor.cancel_command(execution_id)

            if success:
                return jsonify({
                    "success": True,
                    "message": f"Command {execution_id} cancelled"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Command not found or cannot be cancelled"
                }), 404

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/command/history', methods=['DELETE'])
    def clear_command_history():
        """Clear old command history."""
        try:
            days = int(request.args.get('older_than_days', 7))

            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            command_executor = api.container.get_optional('CommandExecutor')
            if not command_executor:
                return jsonify({"error": "Command executor not available"}), 500

            deleted = command_executor.clear_history(older_than_days=days)

            return jsonify({
                "success": True,
                "cleared": deleted,
                "message": f"Cleared {deleted} command records"
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Pending Dialogues =====

    @api.route('/dialogues/pending', methods=['GET'])
    def get_pending_dialogues():
        """Get all pending dialogues requiring master decision."""
        try:
            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            dialogue_manager = api.container.get_optional('DialogueManager')
            if not dialogue_manager:
                return jsonify({"error": "Dialogue manager not available"}), 500

            dialogues = dialogue_manager.get_pending_dialogues(status='pending')

            return jsonify({
                "dialogues": dialogues,
                "count": len(dialogues),
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/dialogues/<int:dialogue_id>', methods=['GET'])
    def get_dialogue(dialogue_id):
        """Get specific dialogue details."""
        try:
            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            dialogue_manager = api.container.get_optional('DialogueManager')
            if not dialogue_manager:
                return jsonify({"error": "Dialogue manager not available"}), 500

            # Get all dialogues and find the specific one
            dialogues = dialogue_manager.get_pending_dialogues(status='pending')
            dialogue = next((d for d in dialogues if d['id'] == dialogue_id), None)

            if not dialogue:
                # Check if it was already responded to
                responded = dialogue_manager.get_pending_dialogues(status='responded')
                dialogue = next((d for d in responded if d['id'] == dialogue_id), None)

                if not dialogue:
                    return jsonify({"error": "Dialogue not found"}), 404

            return jsonify(dialogue)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/dialogues/<int:dialogue_id>/respond', methods=['POST'])
    def respond_to_dialogue(dialogue_id):
        """Master responds to a pending dialogue."""
        try:
            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            dialogue_manager = api.container.get_optional('DialogueManager')
            if not dialogue_manager:
                return jsonify({"error": "Dialogue manager not available"}), 500

            # Get response from request
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            decision = data.get('decision')
            modified_command = data.get('modified_command')

            if not decision:
                return jsonify({"error": "Decision is required"}), 400

            # Validate decision
            valid_decisions = ['p', 'c', 'm', '1', '2', '3', '4', '5']
            if decision not in valid_decisions:
                return jsonify({"error": f"Invalid decision: {decision}"}), 400

            # Record response
            success = dialogue_manager.respond_to_dialogue(
                dialogue_id=dialogue_id,
                decision=decision,
                modified_command=modified_command
            )

            if not success:
                return jsonify({"error": "Failed to record response"}), 500

            return jsonify({
                "success": True,
                "dialogue_id": dialogue_id,
                "decision": decision,
                "message": "Response recorded successfully"
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/llm/expensive', methods=['GET'])
    def get_expensive_interactions():
        """Get most expensive LLM interactions for cost optimization."""
        try:
            if not api.container:
                return jsonify({"error": "System not initialized"}), 500

            tracker = api.container.get_optional('LLMInteractionTracker')
            if not tracker:
                return jsonify({"error": "LLM tracker not available"}), 500

            hours = int(request.args.get('hours', 24))
            limit = int(request.args.get('limit', 20))

            interactions = tracker.get_expensive_interactions(hours=hours, limit=limit)

            return jsonify({
                "expensive_interactions": interactions,
                "count": len(interactions),
                "period_hours": hours
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ===== Error Handlers =====

    @api.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({"error": "Endpoint not found"}), 404

    @api.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({"error": "Internal server error"}), 500

    return api
