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

            # TODO: Implement when master model interactions tracking is available
            return jsonify({
                "interactions": [],
                "total": 0,
            })
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
