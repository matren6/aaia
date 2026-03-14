"""
Command Executor Module

Handles command execution from the web UI with history tracking,
progress monitoring, and notification system integration.
"""

import threading
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, asdict


@dataclass
class CommandExecution:
    """Represents a command execution."""
    execution_id: str
    command: str
    status: str  # 'queued', 'running', 'completed', 'error', 'cancelled'
    output: str = ''
    error: str = ''
    started_at: str = ''
    completed_at: str = ''
    duration_seconds: float = 0
    urgent: bool = False
    created_by: str = 'web_ui'
    context: Dict[str, Any] = None

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


class CommandExecutor:
    """Executes commands from the web UI with history tracking."""

    def __init__(self, process_command_fn: Callable = None, 
                 notify_fn: Callable = None,
                 emit_fn: Callable = None,
                 database_fn: Callable = None):
        """
        Initialize command executor.

        Args:
            process_command_fn: Function to process commands (from Arbiter)
            notify_fn: Function to send notifications
            emit_fn: Function to emit WebSocket events
            database_fn: Function to store/retrieve commands
        """
        self.process_command = process_command_fn
        self.notify = notify_fn
        self.emit = emit_fn
        self.store_command = database_fn

        self.execution_history: Dict[str, CommandExecution] = {}
        self.execution_lock = threading.Lock()

    def execute_command(self, command: str, urgent: bool = False, 
                       context: Dict = None) -> str:
        """
        Queue and execute a command asynchronously.

        Args:
            command: Command to execute
            urgent: If True, prioritize execution
            context: Additional context for the command

        Returns:
            Execution ID for tracking
        """
        execution_id = str(uuid.uuid4())
        execution = CommandExecution(
            execution_id=execution_id,
            command=command,
            status='queued',
            urgent=urgent,
            context=context or {}
        )

        with self.execution_lock:
            self.execution_history[execution_id] = execution

        # Store in database
        if self.store_command:
            self.store_command('INSERT', execution)

        # Emit queued event
        if self.emit:
            self.emit('command_queued', execution.to_dict())

        # Execute in background thread
        thread = threading.Thread(
            target=self._execute_async,
            args=(execution_id, command, urgent, context),
            daemon=True,
            name=f'CommandExecutor-{execution_id}'
        )
        thread.start()

        return execution_id

    def _execute_async(self, execution_id: str, command: str, 
                      urgent: bool, context: Dict):
        """Execute command asynchronously."""
        with self.execution_lock:
            execution = self.execution_history.get(execution_id)
            if not execution:
                return

            execution.status = 'running'
            execution.started_at = datetime.now().isoformat()

        # Emit started event
        if self.emit:
            self.emit('command_started', execution.to_dict())

        start_time = time.time()

        try:
            # Execute the command
            if self.process_command:
                output = self.process_command(
                    command=command,
                    urgent=urgent,
                    context=context or {}
                )
                output = output or ''
            else:
                output = f"Command executed: {command}"

            # Update execution
            with self.execution_lock:
                execution = self.execution_history[execution_id]
                execution.status = 'completed'
                execution.output = str(output)
                execution.completed_at = datetime.now().isoformat()
                execution.duration_seconds = time.time() - start_time

            # Emit progress events
            if self.emit:
                self.emit('command_progress', {
                    'execution_id': execution_id,
                    'status': 'completed',
                    'output': execution.output
                })

            # Notify user
            if self.notify:
                self.notify(
                    notification_type='success',
                    message=f'Command completed: {command}',
                    action_url=f'/command/{execution_id}'
                )

            logging.info(f'Command {execution_id} completed successfully')

        except Exception as e:
            error_msg = str(e)
            logging.error(f'Command {execution_id} failed: {error_msg}')

            with self.execution_lock:
                execution = self.execution_history[execution_id]
                execution.status = 'error'
                execution.error = error_msg
                execution.completed_at = datetime.now().isoformat()
                execution.duration_seconds = time.time() - start_time

            # Emit error event
            if self.emit:
                self.emit('command_error', {
                    'execution_id': execution_id,
                    'error': error_msg
                })

            # Notify user
            if self.notify:
                self.notify(
                    notification_type='error',
                    message=f'Command failed: {command}',
                    action_url=f'/command/{execution_id}'
                )

        finally:
            # Store in database
            if self.store_command:
                with self.execution_lock:
                    execution = self.execution_history.get(execution_id)
                    if execution:
                        self.store_command('UPDATE', execution)

    def get_execution(self, execution_id: str) -> Optional[CommandExecution]:
        """Get command execution by ID."""
        with self.execution_lock:
            return self.execution_history.get(execution_id)

    def get_history(self, limit: int = 50, offset: int = 0) -> list:
        """Get command history with pagination."""
        with self.execution_lock:
            items = list(self.execution_history.values())

        # Sort by creation time (newest first)
        items.sort(
            key=lambda x: x.started_at or x.completed_at,
            reverse=True
        )

        return [item.to_dict() for item in items[offset:offset+limit]]

    def cancel_command(self, execution_id: str) -> bool:
        """Cancel a queued or running command."""
        with self.execution_lock:
            execution = self.execution_history.get(execution_id)
            if not execution:
                return False

            if execution.status in ['queued', 'running']:
                execution.status = 'cancelled'
                execution.completed_at = datetime.now().isoformat()

                if self.store_command:
                    self.store_command('UPDATE', execution)

                if self.emit:
                    self.emit('command_cancelled', execution.to_dict())

                return True

        return False

    def clear_history(self, older_than_days: int = 7) -> int:
        """Clear old command history."""
        cutoff_time = datetime.fromtimestamp(
            time.time() - (older_than_days * 86400)
        )

        with self.execution_lock:
            to_delete = []
            for exec_id, execution in self.execution_history.items():
                if execution.completed_at:
                    completed = datetime.fromisoformat(execution.completed_at)
                    if completed < cutoff_time:
                        to_delete.append(exec_id)

            for exec_id in to_delete:
                del self.execution_history[exec_id]

            return len(to_delete)
