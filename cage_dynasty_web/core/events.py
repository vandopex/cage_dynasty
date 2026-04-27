# core/events.py — stub for web app
# emit() is a no-op in the web layer; we don't need the event bus
from typing import Any

def emit(event_type: Any, data: Any = None) -> None:
    """No-op event emitter for web app compatibility."""
    pass

class EventBus:
    def emit(self, event_type: Any, data: Any = None) -> None:
        pass
    def subscribe(self, *args, **kwargs):
        pass

event_bus = EventBus()
