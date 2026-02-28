"""
Event Bus System for AAIA.

Provides decoupled communication between modules through an event-driven architecture.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time
import threading


class EventType(Enum):
    """Enumeration of all possible event types in the system."""
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    
    # Economic events
    ECONOMIC_TRANSACTION = "economic_transaction"
    BALANCE_LOW = "balance_low"
    INCOME_GENERATED = "income_generated"
    
    # Evolution events
    EVOLUTION_STARTED = "evolution_started"
    EVOLUTION_COMPLETED = "evolution_completed"
    EVOLUTION_FAILED = "evolution_failed"
    
    # Tool events
    TOOL_CREATED = "tool_created"
    TOOL_LOADED = "tool_loaded"
    TOOL_ERROR = "tool_error"
    
    # Goal events
    GOAL_CREATED = "goal_created"
    GOAL_COMPLETED = "goal_completed"
    GOAL_FAILED = "goal_failed"
    
    # Metacognition events
    REFLECTION_STARTED = "reflection_started"
    REFLECTION_COMPLETED = "reflection_completed"
    
    # Diagnosis events
    DIAGNOSIS_COMPLETED = "diagnosis_completed"
    DIAGNOSIS_ACTION_REQUIRED = "diagnosis_action_required"


@dataclass
class Event:
    """Represents an event in the system."""
    type: EventType
    data: Dict[str, Any]
    source: str
    timestamp: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.correlation_id is None:
            self.correlation_id = f"{self.source}:{self.type.value}:{self.timestamp}"


class EventBus:
    """
    Central event bus for publish-subscribe communication between modules.
    
    This enables loose coupling between modules - modules can publish events
    without knowing who subscribes to them, and subscribers can react to events
    without knowing who publishes them.
    """
    
    def __init__(self, enable_logging: bool = False):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._global_handlers: List[Callable] = []
        self._event_history: List[Event] = []
        self._max_history: int = 1000
        self._enable_logging = enable_logging
        self._lock = threading.RLock()
        
    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Subscribe a handler to a specific event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: Callback function that accepts an Event object
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
                
    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Unsubscribe a handler from a specific event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler to remove
        """
        with self._lock:
            if event_type in self._handlers:
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
                    
    def subscribe_all(self, handler: Callable) -> None:
        """
        Subscribe a handler to ALL events (useful for logging/monitoring).
        
        Args:
            handler: Callback function that accepts an Event object
        """
        with self._lock:
            if handler not in self._global_handlers:
                self._global_handlers.append(handler)
                
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish
        """
        with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
                
            if self._enable_logging:
                print(f"[EVENT] {event.type.value} from {event.source}")
                
        # Notify specific handlers
        handlers_to_notify = []
        with self._lock:
            if event.type in self._handlers:
                handlers_to_notify = list(self._handlers[event.type])
            global_handlers = list(self._global_handlers)
            
        # Execute handlers outside the lock to prevent deadlocks
        for handler in handlers_to_notify + global_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"[EVENT ERROR] Handler {handler.__name__} failed: {e}")
                
    def get_history(self, event_type: Optional[EventType] = None, 
                    limit: Optional[int] = None) -> List[Event]:
        """
        Get event history, optionally filtered by type.
        
        Args:
            event_type: If provided, filter by this event type
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        with self._lock:
            history = list(self._event_history)
            
        if event_type is not None:
            history = [e for e in history if e.type == event_type]
            
        if limit is not None:
            history = history[-limit:]
            
        return history
        
    def clear_history(self) -> None:
        """Clear the event history."""
        with self._lock:
            self._event_history.clear()
            
    def get_handler_count(self, event_type: Optional[EventType] = None) -> int:
        """
        Get the number of handlers subscribed to an event type.
        
        Args:
            event_type: If provided, count handlers for this type only
            
        Returns:
            Number of handlers
        """
        with self._lock:
            if event_type is not None:
                return len(self._handlers.get(event_type, []))
            return sum(len(handlers) for handlers in self._handlers.values())
            
    def has_handler(self, event_type: EventType) -> bool:
        """
        Check if there are any handlers for a specific event type.
        
        Args:
            event_type: The event type to check
            
        Returns:
            True if there are handlers, False otherwise
        """
        with self._lock:
            return event_type in self._handlers and len(self._handlers[event_type]) > 0
            
    def unsubscribe_all(self, handler: Callable) -> None:
        """
        Unsubscribe a handler from all events it was subscribed to.
        
        Args:
            handler: The handler to remove from all subscriptions
        """
        with self._lock:
            # Remove from specific handlers
            for event_type in list(self._handlers.keys()):
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
            # Remove from global handlers
            if handler in self._global_handlers:
                self._global_handlers.remove(handler)


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance (singleton pattern)."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def set_event_bus(bus: EventBus) -> None:
    """Set the global event bus instance (for testing)."""
    global _event_bus
    _event_bus = bus


def reset_event_bus() -> None:
    """Reset the global event bus."""
    global _event_bus
    _event_bus = None