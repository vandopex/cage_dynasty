# tests/test_events.py
# Tests for Module 2: Event Bus System
# Lines: 275

"""
Comprehensive tests for core/events.py

Run with: python3 -m pytest tests/test_events.py -v
"""

import pytest
from datetime import datetime
from core.types import EventType
from core.events import (
    EventBus, GameEvent, EventHandler, EventPriority,
    event_bus, emit, subscribe, unsubscribe
)


class TestGameEvent:
    """Tests for GameEvent dataclass"""
    
    def test_event_creation(self):
        """Events should be created with correct attributes"""
        event = GameEvent(
            event_type=EventType.FIGHT_COMPLETED,
            data={"winner": "Fighter A"}
        )
        
        assert event.event_type == EventType.FIGHT_COMPLETED
        assert event.data["winner"] == "Fighter A"
        assert event.propagate is True
        assert event.event_id is not None
    
    def test_event_timestamp(self):
        """Events should have automatic timestamps"""
        before = datetime.now()
        event = GameEvent(event_type=EventType.FIGHTER_CREATED)
        after = datetime.now()
        
        assert before <= event.timestamp <= after
    
    def test_event_get_method(self):
        """Event.get() should retrieve data with default"""
        event = GameEvent(
            event_type=EventType.FIGHTER_SIGNED,
            data={"fighter": "John", "camp": "Alpha"}
        )
        
        assert event.get("fighter") == "John"
        assert event.get("missing") is None
        assert event.get("missing", "default") == "default"
    
    def test_stop_propagation(self):
        """stop_propagation() should set propagate to False"""
        event = GameEvent(event_type=EventType.FIGHT_COMPLETED)
        assert event.propagate is True
        
        event.stop_propagation()
        assert event.propagate is False
    
    def test_event_string_representation(self):
        """Events should have readable string representations"""
        event = GameEvent(event_type=EventType.TITLE_WON)
        
        assert "TITLE_WON" in str(event)
        assert event.event_id in str(event)


class TestEventHandler:
    """Tests for EventHandler wrapper"""
    
    def test_handler_creation(self):
        """Handlers should be created with correct attributes"""
        def my_callback(event):
            pass
        
        handler = EventHandler(
            callback=my_callback,
            priority=EventPriority.HIGH,
            description="Test handler"
        )
        
        assert handler.callback == my_callback
        assert handler.priority == EventPriority.HIGH
        assert handler.description == "Test handler"
        assert handler.once is False
    
    def test_handler_callable(self):
        """Handlers should be directly callable"""
        results = []
        
        def my_callback(event):
            results.append(event.event_type)
        
        handler = EventHandler(callback=my_callback)
        event = GameEvent(event_type=EventType.WEEK_ADVANCED)
        
        handler(event)
        assert results == [EventType.WEEK_ADVANCED]
    
    def test_handler_equality(self):
        """Handlers with same ID should be equal"""
        def callback(e):
            pass
        
        h1 = EventHandler(callback=callback)
        h2 = EventHandler(callback=callback)
        h2.handler_id = h1.handler_id  # Force same ID
        
        assert h1 == h2
        assert hash(h1) == hash(h2)


class TestEventBus:
    """Tests for EventBus class"""
    
    @pytest.fixture
    def bus(self):
        """Create a fresh EventBus for each test"""
        return EventBus()
    
    def test_subscribe_and_emit(self, bus):
        """Basic subscribe and emit should work"""
        results = []
        
        def handler(event):
            results.append(event.data.get("value"))
        
        bus.subscribe(EventType.FIGHT_COMPLETED, handler)
        bus.emit(EventType.FIGHT_COMPLETED, {"value": 42})
        
        assert results == [42]
    
    def test_multiple_handlers(self, bus):
        """Multiple handlers should all be called"""
        results = []
        
        def handler1(event):
            results.append("h1")
        
        def handler2(event):
            results.append("h2")
        
        bus.subscribe(EventType.FIGHTER_CREATED, handler1)
        bus.subscribe(EventType.FIGHTER_CREATED, handler2)
        bus.emit(EventType.FIGHTER_CREATED)
        
        assert len(results) == 2
        assert "h1" in results
        assert "h2" in results
    
    def test_handler_priority(self, bus):
        """Higher priority handlers should be called first"""
        results = []
        
        def low_handler(event):
            results.append("low")
        
        def high_handler(event):
            results.append("high")
        
        def normal_handler(event):
            results.append("normal")
        
        # Subscribe in random order
        bus.subscribe(EventType.FIGHT_BOOKED, low_handler, EventPriority.LOW)
        bus.subscribe(EventType.FIGHT_BOOKED, high_handler, EventPriority.HIGH)
        bus.subscribe(EventType.FIGHT_BOOKED, normal_handler, EventPriority.NORMAL)
        
        bus.emit(EventType.FIGHT_BOOKED)
        
        # Should be called in priority order: high, normal, low
        assert results == ["high", "normal", "low"]
    
    def test_unsubscribe(self, bus):
        """Handlers should be removable by ID"""
        results = []
        
        def handler(event):
            results.append("called")
        
        handler_id = bus.subscribe(EventType.FIGHTER_INJURED, handler)
        bus.emit(EventType.FIGHTER_INJURED)
        assert len(results) == 1
        
        # Unsubscribe
        removed = bus.unsubscribe(handler_id)
        assert removed is True
        
        # Should not be called again
        bus.emit(EventType.FIGHTER_INJURED)
        assert len(results) == 1  # Still 1, not 2
    
    def test_unsubscribe_nonexistent(self, bus):
        """Unsubscribing non-existent handler should return False"""
        result = bus.unsubscribe("fake-id-12345")
        assert result is False
    
    def test_once_handler(self, bus):
        """Once handlers should only fire once"""
        results = []
        
        def handler(event):
            results.append("called")
        
        bus.subscribe(EventType.TITLE_WON, handler, once=True)
        
        bus.emit(EventType.TITLE_WON)
        bus.emit(EventType.TITLE_WON)
        bus.emit(EventType.TITLE_WON)
        
        assert len(results) == 1  # Only called once
    
    def test_stop_propagation(self, bus):
        """Events that stop propagation should not reach later handlers"""
        results = []
        
        def stopping_handler(event):
            results.append("stopper")
            event.stop_propagation()
        
        def other_handler(event):
            results.append("other")
        
        # Stopping handler has higher priority, called first
        bus.subscribe(EventType.FIGHT_CANCELLED, stopping_handler, EventPriority.HIGH)
        bus.subscribe(EventType.FIGHT_CANCELLED, other_handler, EventPriority.LOW)
        
        bus.emit(EventType.FIGHT_CANCELLED)
        
        # Only stopping handler should have been called
        assert results == ["stopper"]
    
    def test_event_isolation(self, bus):
        """Handlers should only receive events they subscribed to"""
        results = []
        
        def fight_handler(event):
            results.append("fight")
        
        def injury_handler(event):
            results.append("injury")
        
        bus.subscribe(EventType.FIGHT_COMPLETED, fight_handler)
        bus.subscribe(EventType.FIGHTER_INJURED, injury_handler)
        
        bus.emit(EventType.FIGHT_COMPLETED)
        
        assert results == ["fight"]  # Only fight handler called
    
    def test_global_handlers(self, bus):
        """Global handlers should receive all events"""
        results = []
        
        def global_handler(event):
            results.append(event.event_type.name)
        
        bus.subscribe_all(global_handler)
        
        bus.emit(EventType.FIGHT_COMPLETED)
        bus.emit(EventType.FIGHTER_CREATED)
        bus.emit(EventType.CAMP_UPGRADED)
        
        assert len(results) == 3
        assert "FIGHT_COMPLETED" in results
        assert "FIGHTER_CREATED" in results
        assert "CAMP_UPGRADED" in results
    
    def test_event_history(self, bus):
        """Event history should track emitted events"""
        bus.emit(EventType.WEEK_ADVANCED, {"week": 1})
        bus.emit(EventType.WEEK_ADVANCED, {"week": 2})
        bus.emit(EventType.MONTH_ADVANCED, {"month": 1})
        
        history = bus.get_history()
        assert len(history) == 3
        
        # Filter by type
        week_history = bus.get_history(EventType.WEEK_ADVANCED)
        assert len(week_history) == 2
    
    def test_history_limit(self):
        """History should respect max_history limit"""
        bus = EventBus(max_history=5)
        
        for i in range(10):
            bus.emit(EventType.WEEK_ADVANCED, {"week": i})
        
        history = bus.get_history()
        assert len(history) == 5
        # Should have most recent events
        assert history[-1].data["week"] == 9
    
    def test_clear_handlers(self, bus):
        """clear() should remove handlers"""
        results = []
        
        def handler(event):
            results.append("called")
        
        bus.subscribe(EventType.FIGHT_COMPLETED, handler)
        bus.clear(EventType.FIGHT_COMPLETED)
        bus.emit(EventType.FIGHT_COMPLETED)
        
        assert len(results) == 0
    
    def test_clear_all_handlers(self, bus):
        """clear() with no args should remove all handlers"""
        results = []
        
        def handler(event):
            results.append("called")
        
        bus.subscribe(EventType.FIGHT_COMPLETED, handler)
        bus.subscribe(EventType.FIGHTER_CREATED, handler)
        bus.subscribe_all(handler)
        
        bus.clear()
        
        bus.emit(EventType.FIGHT_COMPLETED)
        bus.emit(EventType.FIGHTER_CREATED)
        
        assert len(results) == 0
    
    def test_handler_count(self, bus):
        """handler_count should return correct counts"""
        def handler(e):
            pass
        
        assert bus.handler_count() == 0
        
        bus.subscribe(EventType.FIGHT_COMPLETED, handler)
        bus.subscribe(EventType.FIGHT_COMPLETED, handler)
        bus.subscribe(EventType.FIGHTER_CREATED, handler)
        
        assert bus.handler_count(EventType.FIGHT_COMPLETED) == 2
        assert bus.handler_count(EventType.FIGHTER_CREATED) == 1
        assert bus.handler_count() == 3
    
    def test_stats(self, bus):
        """get_stats should return usage statistics"""
        def handler(e):
            pass
        
        bus.subscribe(EventType.FIGHT_COMPLETED, handler)
        bus.emit(EventType.FIGHT_COMPLETED)
        bus.emit(EventType.FIGHT_COMPLETED)
        
        stats = bus.get_stats()
        assert stats["total_emits"] == 2
        assert stats["total_handler_calls"] == 2
    
    def test_exception_handling(self, bus):
        """Exceptions in handlers should not break other handlers"""
        results = []
        
        def bad_handler(event):
            raise ValueError("I broke!")
        
        def good_handler(event):
            results.append("good")
        
        # Bad handler has higher priority
        bus.subscribe(EventType.FIGHT_COMPLETED, bad_handler, EventPriority.HIGH)
        bus.subscribe(EventType.FIGHT_COMPLETED, good_handler, EventPriority.LOW)
        
        # Should not raise exception
        bus.emit(EventType.FIGHT_COMPLETED)
        
        # Good handler should still be called
        assert results == ["good"]


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""
    
    def test_global_emit(self):
        """emit() should use global event bus"""
        results = []
        
        def handler(event):
            results.append(event.event_type)
        
        handler_id = subscribe(EventType.YEAR_ADVANCED, handler)
        emit(EventType.YEAR_ADVANCED)
        
        assert EventType.YEAR_ADVANCED in results
        
        # Cleanup
        unsubscribe(handler_id)
    
    def test_global_subscribe_unsubscribe(self):
        """subscribe/unsubscribe should work with global bus"""
        results = []
        
        def handler(event):
            results.append("called")
        
        handler_id = subscribe(EventType.RIVALRY_STARTED, handler)
        emit(EventType.RIVALRY_STARTED)
        assert len(results) == 1
        
        unsubscribe(handler_id)
        emit(EventType.RIVALRY_STARTED)
        assert len(results) == 1  # Not called again


class TestEventPriority:
    """Tests for EventPriority enum"""
    
    def test_priority_ordering(self):
        """Priority values should be ordered correctly"""
        assert EventPriority.CRITICAL.value > EventPriority.HIGH.value
        assert EventPriority.HIGH.value > EventPriority.NORMAL.value
        assert EventPriority.NORMAL.value > EventPriority.LOW.value
        assert EventPriority.LOW.value > EventPriority.BACKGROUND.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
