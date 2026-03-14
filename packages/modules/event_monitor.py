"""
Event Monitor - Debugging and monitoring tool for event bus

Provides:
- Real-time event logging
- Event statistics
- Event replay
- Event visualization (CLI)
"""

from modules.bus import Event, EventType, get_event_bus
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EventMonitor:
    """Monitor and analyze event bus activity"""

    def __init__(self, event_bus=None):
        self.event_bus = event_bus or get_event_bus()
        self.enabled = False
        self.verbose = False

    def start(self, verbose: bool = False):
        """Start monitoring events"""
        self.enabled = True
        self.verbose = verbose
        self.event_bus.subscribe_all(self._on_event)
        logger.info("Event monitoring started")

    def stop(self):
        """Stop monitoring"""
        self.enabled = False
        try:
            self.event_bus.unsubscribe_all(self._on_event)
        except Exception:
            # Older EventBus implementations may not have unsubscribe_all
            pass
        logger.info("Event monitoring stopped")

    def _on_event(self, event: Event):
        if not self.enabled:
            return

        if self.verbose:
            logger.info(f"[{event.type.name}] {event.source}: {event.data}")
        else:
            logger.debug(f"{event.type.name} from {event.source}")

    def get_statistics(self, since: Optional[datetime] = None) -> Dict:
        stats = self.event_bus.get_statistics() if hasattr(self.event_bus, 'get_statistics') else {}

        if since:
            history = self.event_bus.get_history(limit=10000)
            history = [e for e in history if getattr(e, 'timestamp', None) and datetime.fromtimestamp(e.timestamp) >= since]
            type_counts = {}
            for event in history:
                t = event.type.name if hasattr(event.type, 'name') else str(event.type)
                type_counts[t] = type_counts.get(t, 0) + 1
            stats['filtered_events'] = len(history)
            stats['filtered_by_type'] = type_counts

        return stats

    def get_recent_events(self, event_type: Optional[EventType] = None, limit: int = 50) -> List[Event]:
        return self.event_bus.get_history(event_type=event_type, limit=limit)

    def print_summary(self):
        stats = self.event_bus.get_statistics() if hasattr(self.event_bus, 'get_statistics') else {}

        print("\n=== Event Bus Statistics ===")
        print(f"Total Events: {stats.get('total_events', 'N/A')}")
        print(f"History Size: {stats.get('history_size', 'N/A')}")
        print(f"Subscribers: {stats.get('subscriber_count', 'N/A')}")
        print(f"Wildcard Subscribers: {stats.get('wildcard_subscribers', 'N/A')}")

        print("\nEvents by Type:")
        for event_type, count in sorted(stats.get('events_by_type', {}).items(), key=lambda x: x[1], reverse=True):
            print(f"  {event_type}: {count}")

    def print_recent(self, limit: int = 10):
        events = self.get_recent_events(limit=limit)

        print(f"\n=== Recent Events ({len(events)}) ===")
        for event in events:
            # Support both timestamp formats
            ts = None
            if hasattr(event, 'timestamp'):
                try:
                    # timestamp could be float or datetime
                    if isinstance(event.timestamp, float) or isinstance(event.timestamp, int):
                        ts = datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S')
                    else:
                        ts = event.timestamp.strftime('%H:%M:%S')
                except Exception:
                    ts = str(event.timestamp)

            print(f"[{ts}] {getattr(event.type, 'name', str(event.type))} from {event.source}")
            if getattr(event, 'data', None):
                print(f"  Data: {event.data}")
