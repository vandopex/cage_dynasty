# core/events.py
# Module 2: Event Bus System
# Lines: 298
#
# The nervous system of Cage Dynasty. This enables organic, emergent behavior
# by allowing systems to react to events without knowing about each other.

"""
Cage Dynasty - Event Bus System

This module implements a publish-subscribe event system that allows
loose coupling between game systems. When something happens (a fight ends,
a fighter signs, a rivalry forms), an event is emitted and any interested
system can react to it.

KEY CONCEPTS:
- Events: Things that happen in the game world
- Publishers: Systems that emit events when things happen
- Subscribers: Systems that react when specific events occur
- Event Bus: The central hub that routes events to subscribers

USAGE:
    from core.events import event_bus, GameEvent, EventType
    
    # Subscribe to an event
    def on_fight_completed(event: GameEvent):
        print(f"Fight ended: {event.data}")
    
    event_bus.subscribe(EventType.FIGHT_COMPLETED, on_fight_completed)
    
    # Emit an event
    event_bus.emit(EventType.FIGHT_COMPLETED, {"winner": "Fighter A"})

IMPORT RULES:
- This module imports ONLY from core.types and Python standard library
- All other game modules may import from this module
"""

from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import logging
import uuid
from collections import defaultdict

from core.types import EventType

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# EVENT PRIORITY
# ============================================================================

class EventPriority(Enum):
    """
    Priority levels for event handlers.
    Higher priority handlers are called first.
    """
    CRITICAL = 100   # System-critical handlers (save state, etc.)
    HIGH = 75        # Important game logic (rankings, titles)
    NORMAL = 50      # Standard handlers (most game systems)
    LOW = 25         # Non-essential handlers (statistics, logging)
    BACKGROUND = 0   # Background tasks (analytics, achievements)


# ============================================================================
# GAME EVENT
# ============================================================================

@dataclass
class GameEvent:
    """
    Represents something that happened in the game world.
    
    Attributes:
        event_type: The type of event (from EventType enum)
        data: Dictionary containing event-specific data
        timestamp: When the event occurred
        event_id: Unique identifier for this event instance
        source: Optional identifier for what triggered the event
        propagate: If False, stops event from reaching more handlers
    """
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: Optional[str] = None
    propagate: bool = True
    
    def stop_propagation(self) -> None:
        """Prevent this event from reaching additional handlers"""
        self.propagate = False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Convenience method to get data from the event"""
        return self.data.get(key, default)
    
    def __str__(self) -> str:
        return f"GameEvent({self.event_type.name}, id={self.event_id})"
    
    def __repr__(self) -> str:
        return f"GameEvent(type={self.event_type.name}, data={self.data}, source={self.source})"


# ============================================================================
# EVENT HANDLER WRAPPER
# ============================================================================

@dataclass
class EventHandler:
    """
    Wrapper for event handler functions with metadata.
    
    Attributes:
        callback: The function to call when event fires
        priority: Handler priority (higher = called first)
        handler_id: Unique identifier for this handler
        description: Human-readable description of what this handler does
        once: If True, handler is removed after first invocation
    """
    callback: Callable[[GameEvent], None]
    priority: EventPriority = EventPriority.NORMAL
    handler_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    once: bool = False
    
    def __call__(self, event: GameEvent) -> None:
        """Allow the handler to be called directly"""
        self.callback(event)
    
    def __hash__(self) -> int:
        return hash(self.handler_id)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, EventHandler):
            return self.handler_id == other.handler_id
        return False


# ============================================================================
# EVENT BUS
# ============================================================================

class EventBus:
    """
    Central event routing system for the game.
    
    The EventBus maintains a registry of handlers for each event type
    and routes events to the appropriate handlers when they're emitted.
    
    Features:
    - Priority-based handler ordering
    - One-time handlers (auto-remove after first call)
    - Event propagation control
    - Event history for debugging
    - Wildcard subscriptions (listen to all events)
    """
    
    def __init__(self, keep_history: bool = True, max_history: int = 1000):
        """
        Initialize the event bus.
        
        Args:
            keep_history: Whether to maintain event history
            max_history: Maximum number of events to keep in history
        """
        # Map of event_type -> list of handlers
        self._handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        
        # Handlers that listen to ALL events
        self._global_handlers: List[EventHandler] = []
        
        # Event history for debugging
        self._history: List[GameEvent] = []
        self._keep_history = keep_history
        self._max_history = max_history
        
        # Track if we're currently emitting (prevent recursion issues)
        self._emitting: bool = False
        self._deferred_events: List[GameEvent] = []
        
        # Statistics
        self._emit_count: int = 0
        self._handler_call_count: int = 0
    
    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[GameEvent], None],
        priority: EventPriority = EventPriority.NORMAL,
        description: str = "",
        once: bool = False
    ) -> str:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The type of event to listen for
            callback: Function to call when event fires
            priority: Handler priority (higher = called first)
            description: Human-readable description
            once: If True, handler removed after first invocation
        
        Returns:
            handler_id: Unique ID that can be used to unsubscribe
        """
        handler = EventHandler(
            callback=callback,
            priority=priority,
            description=description,
            once=once
        )
        
        self._handlers[event_type].append(handler)
        self._sort_handlers(event_type)
        
        logger.debug(f"Subscribed handler {handler.handler_id} to {event_type.name}")
        return handler.handler_id
    
    def subscribe_all(
        self,
        callback: Callable[[GameEvent], None],
        priority: EventPriority = EventPriority.LOW,
        description: str = ""
    ) -> str:
        """
        Subscribe to ALL events (useful for logging/debugging).
        
        Args:
            callback: Function to call for every event
            priority: Handler priority
            description: Human-readable description
        
        Returns:
            handler_id: Unique ID for unsubscribing
        """
        handler = EventHandler(
            callback=callback,
            priority=priority,
            description=description or "Global handler"
        )
        
        self._global_handlers.append(handler)
        self._global_handlers.sort(key=lambda h: h.priority.value, reverse=True)
        
        logger.debug(f"Subscribed global handler {handler.handler_id}")
        return handler.handler_id
    
    def unsubscribe(self, handler_id: str) -> bool:
        """
        Remove a handler by its ID.
        
        Args:
            handler_id: The ID returned from subscribe()
        
        Returns:
            True if handler was found and removed, False otherwise
        """
        # Check specific event handlers
        for event_type, handlers in self._handlers.items():
            for handler in handlers:
                if handler.handler_id == handler_id:
                    handlers.remove(handler)
                    logger.debug(f"Unsubscribed handler {handler_id} from {event_type.name}")
                    return True
        
        # Check global handlers
        for handler in self._global_handlers:
            if handler.handler_id == handler_id:
                self._global_handlers.remove(handler)
                logger.debug(f"Unsubscribed global handler {handler_id}")
                return True
        
        return False
    
    def emit(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None
    ) -> GameEvent:
        """
        Emit an event to all registered handlers.
        
        Args:
            event_type: The type of event to emit
            data: Event-specific data dictionary
            source: Optional identifier for event source
        
        Returns:
            The GameEvent that was emitted
        """
        event = GameEvent(
            event_type=event_type,
            data=data or {},
            source=source
        )
        
        # Handle nested emissions by deferring
        if self._emitting:
            self._deferred_events.append(event)
            return event
        
        self._emit_event(event)
        
        # Process any events that were deferred during emission
        while self._deferred_events:
            deferred = self._deferred_events.pop(0)
            self._emit_event(deferred)
        
        return event
    
    def _emit_event(self, event: GameEvent) -> None:
        """Internal method to actually emit an event"""
        self._emitting = True
        self._emit_count += 1
        
        try:
            # Add to history
            if self._keep_history:
                self._history.append(event)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
            
            # Collect handlers to call
            handlers_to_remove: List[tuple] = []
            
            # Call specific handlers for this event type
            for handler in self._handlers.get(event.event_type, []):
                if not event.propagate:
                    break
                
                try:
                    handler(event)
                    self._handler_call_count += 1
                    
                    if handler.once:
                        handlers_to_remove.append((event.event_type, handler))
                        
                except Exception as e:
                    logger.error(f"Handler {handler.handler_id} raised exception: {e}")
            
            # Call global handlers
            for handler in self._global_handlers:
                if not event.propagate:
                    break
                
                try:
                    handler(event)
                    self._handler_call_count += 1
                except Exception as e:
                    logger.error(f"Global handler {handler.handler_id} raised exception: {e}")
            
            # Remove one-time handlers
            for event_type, handler in handlers_to_remove:
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
                    
        finally:
            self._emitting = False
    
    def _sort_handlers(self, event_type: EventType) -> None:
        """Sort handlers by priority (highest first)"""
        self._handlers[event_type].sort(
            key=lambda h: h.priority.value,
            reverse=True
        )
    
    def clear(self, event_type: Optional[EventType] = None) -> None:
        """
        Remove all handlers for an event type, or all handlers if no type specified.
        
        Args:
            event_type: Specific event type to clear, or None for all
        """
        if event_type:
            self._handlers[event_type].clear()
            logger.debug(f"Cleared all handlers for {event_type.name}")
        else:
            self._handlers.clear()
            self._global_handlers.clear()
            logger.debug("Cleared all event handlers")
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[GameEvent]:
        """
        Get event history, optionally filtered by type.
        
        Args:
            event_type: Filter to specific event type
            limit: Maximum number of events to return
        
        Returns:
            List of GameEvents (most recent last)
        """
        if event_type:
            filtered = [e for e in self._history if e.event_type == event_type]
            return filtered[-limit:]
        return self._history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the event bus"""
        handler_counts = {
            et.name: len(handlers)
            for et, handlers in self._handlers.items()
            if handlers
        }
        
        return {
            "total_emits": self._emit_count,
            "total_handler_calls": self._handler_call_count,
            "history_size": len(self._history),
            "handler_counts": handler_counts,
            "global_handlers": len(self._global_handlers)
        }
    
    def handler_count(self, event_type: Optional[EventType] = None) -> int:
        """Get the number of handlers registered"""
        if event_type:
            return len(self._handlers.get(event_type, []))
        return sum(len(h) for h in self._handlers.values()) + len(self._global_handlers)


# ============================================================================
# GLOBAL EVENT BUS INSTANCE
# ============================================================================

# Singleton instance for the entire game
event_bus = EventBus()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def emit(
    event_type: EventType,
    data: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None
) -> GameEvent:
    """Convenience function to emit on the global event bus"""
    return event_bus.emit(event_type, data, source)


def subscribe(
    event_type: EventType,
    callback: Callable[[GameEvent], None],
    priority: EventPriority = EventPriority.NORMAL
) -> str:
    """Convenience function to subscribe on the global event bus"""
    return event_bus.subscribe(event_type, callback, priority)


def unsubscribe(handler_id: str) -> bool:
    """Convenience function to unsubscribe from the global event bus"""
    return event_bus.unsubscribe(handler_id)
