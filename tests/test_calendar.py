# tests/test_calendar.py
# Tests for Module 4: Time & Calendar System
# Lines: 312

"""
Comprehensive tests for core/calendar.py

Run with: python3 -m pytest tests/test_calendar.py -v
"""

import pytest
from datetime import date
from core.types import EventType
from core.events import EventBus
from core.calendar import (
    GameDate, GameCalendar, DayOfWeek,
    calendar, current_date, advance_week, weeks_until,
    format_weeks_duration, calculate_age_on_date,
    get_month_name, get_month_abbrev,
    DEFAULT_START_DATE, DAYS_PER_WEEK, WEEKS_PER_YEAR
)


class TestDayOfWeek:
    """Tests for DayOfWeek enum"""
    
    def test_days_have_correct_values(self):
        """Days should match Python's weekday convention"""
        assert DayOfWeek.MONDAY.value == 0
        assert DayOfWeek.SUNDAY.value == 6
    
    def test_from_date(self):
        """Should correctly identify day from date"""
        # January 1, 2025 is a Wednesday
        wed = date(2025, 1, 1)
        assert DayOfWeek.from_date(wed) == DayOfWeek.WEDNESDAY
        
        # January 4, 2025 is a Saturday
        sat = date(2025, 1, 4)
        assert DayOfWeek.from_date(sat) == DayOfWeek.SATURDAY


class TestGameDate:
    """Tests for GameDate dataclass"""
    
    def test_creation(self):
        """GameDate should store date components"""
        gd = GameDate(2025, 6, 15)
        assert gd.year == 2025
        assert gd.month == 6
        assert gd.day == 15
    
    def test_from_date(self):
        """Should create from Python date"""
        d = date(2025, 3, 20)
        gd = GameDate.from_date(d)
        
        assert gd.year == 2025
        assert gd.month == 3
        assert gd.day == 20
    
    def test_to_date(self):
        """Should convert back to Python date"""
        gd = GameDate(2025, 7, 4)
        d = gd.to_date()
        
        assert d == date(2025, 7, 4)
    
    def test_add_days(self):
        """add_days should return new GameDate"""
        gd = GameDate(2025, 1, 1)
        result = gd.add_days(10)
        
        assert result.day == 11
        assert gd.day == 1  # Original unchanged (immutable)
    
    def test_add_weeks(self):
        """add_weeks should add correct number of days"""
        gd = GameDate(2025, 1, 1)
        result = gd.add_weeks(2)
        
        assert result.day == 15  # 1 + 14
    
    def test_add_days_crosses_month(self):
        """add_days should handle month boundaries"""
        gd = GameDate(2025, 1, 30)
        result = gd.add_days(5)
        
        assert result.month == 2
        assert result.day == 4
    
    def test_subtract_days(self):
        """subtract_days should work correctly"""
        gd = GameDate(2025, 1, 15)
        result = gd.subtract_days(10)
        
        assert result.day == 5
    
    def test_days_until(self):
        """days_until should calculate difference"""
        start = GameDate(2025, 1, 1)
        end = GameDate(2025, 1, 11)
        
        assert start.days_until(end) == 10
        assert end.days_until(start) == -10
    
    def test_weeks_until(self):
        """weeks_until should calculate whole weeks"""
        start = GameDate(2025, 1, 1)
        end = GameDate(2025, 1, 22)
        
        assert start.weeks_until(end) == 3  # 21 days = 3 weeks
    
    def test_day_of_week(self):
        """Should return correct day of week"""
        # January 1, 2025 is Wednesday
        gd = GameDate(2025, 1, 1)
        assert gd.day_of_week == DayOfWeek.WEDNESDAY
    
    def test_is_weekend(self):
        """Should identify weekend days"""
        saturday = GameDate(2025, 1, 4)
        sunday = GameDate(2025, 1, 5)
        monday = GameDate(2025, 1, 6)
        
        assert saturday.is_weekend is True
        assert sunday.is_weekend is True
        assert monday.is_weekend is False
    
    def test_week_of_year(self):
        """Should return ISO week number"""
        gd = GameDate(2025, 1, 6)  # First full week
        assert gd.week_of_year >= 1
    
    def test_quarter(self):
        """Should return correct quarter"""
        q1 = GameDate(2025, 2, 15)
        q2 = GameDate(2025, 5, 15)
        q3 = GameDate(2025, 8, 15)
        q4 = GameDate(2025, 11, 15)
        
        assert q1.quarter == 1
        assert q2.quarter == 2
        assert q3.quarter == 3
        assert q4.quarter == 4
    
    def test_format_styles(self):
        """Should format in different styles"""
        gd = GameDate(2025, 1, 15)
        
        assert gd.format("short") == "1/15/25"
        assert "Jan" in gd.format("medium")
        assert "January" in gd.format("long")
        assert gd.format("iso") == "2025-01-15"
    
    def test_comparison_operators(self):
        """Comparison operators should work"""
        early = GameDate(2025, 1, 1)
        late = GameDate(2025, 12, 31)
        
        assert early < late
        assert late > early
        assert early <= early
        assert early >= early
        assert not (early > late)
    
    def test_immutability(self):
        """GameDate should be immutable"""
        gd = GameDate(2025, 1, 1)
        with pytest.raises(Exception):
            gd.year = 2026


class TestGameCalendar:
    """Tests for GameCalendar class"""
    
    @pytest.fixture
    def cal(self):
        """Create a fresh calendar for each test"""
        return GameCalendar(date(2025, 1, 1))
    
    def test_initialization(self, cal):
        """Calendar should initialize with correct date"""
        assert cal.current_date.year == 2025
        assert cal.current_date.month == 1
        assert cal.current_date.day == 1
        assert cal.total_weeks == 0
    
    def test_default_start_date(self):
        """Calendar should use default start if none provided"""
        cal = GameCalendar()
        assert cal.current_date.year == DEFAULT_START_DATE.year
    
    def test_advance_week(self, cal):
        """advance_week should move date forward by 7 days"""
        cal.advance_week()
        
        assert cal.current_date.day == 8
        assert cal.total_weeks == 1
    
    def test_advance_multiple_weeks(self, cal):
        """advance_weeks should advance correct amount"""
        cal.advance_weeks(4)
        
        assert cal.total_weeks == 4
        assert cal.current_date.day == 29
    
    def test_advance_week_emits_event(self, cal):
        """advance_week should emit WEEK_ADVANCED event"""
        events_received = []
        
        def handler(event):
            events_received.append(event.event_type)
        
        from core.events import event_bus
        handler_id = event_bus.subscribe(EventType.WEEK_ADVANCED, handler)
        
        cal.advance_week()
        
        assert EventType.WEEK_ADVANCED in events_received
        event_bus.unsubscribe(handler_id)
    
    def test_month_change_emits_event(self, cal):
        """Crossing month boundary should emit MONTH_ADVANCED"""
        events_received = []
        
        def handler(event):
            events_received.append(event.event_type)
        
        from core.events import event_bus
        handler_id = event_bus.subscribe(EventType.MONTH_ADVANCED, handler)
        
        # Advance to February (5 weeks from Jan 1)
        cal.advance_weeks(5)
        
        assert EventType.MONTH_ADVANCED in events_received
        event_bus.unsubscribe(handler_id)
    
    def test_year_change_emits_event(self):
        """Crossing year boundary should emit YEAR_ADVANCED"""
        cal = GameCalendar(date(2025, 12, 25))
        events_received = []
        
        def handler(event):
            events_received.append(event.event_type)
        
        from core.events import event_bus
        handler_id = event_bus.subscribe(EventType.YEAR_ADVANCED, handler)
        
        # Advance past New Year
        cal.advance_weeks(2)
        
        assert EventType.YEAR_ADVANCED in events_received
        event_bus.unsubscribe(handler_id)
    
    def test_advance_to_date(self, cal):
        """advance_to_date should advance to target (in whole weeks)"""
        target = GameDate(2025, 2, 12)  # 6 weeks from Jan 1
        weeks_advanced = cal.advance_to_date(target)
        
        assert weeks_advanced > 0
        # advance_to_date moves in whole weeks, so we get close to target
        assert cal.total_weeks == weeks_advanced
    
    def test_advance_to_past_raises_error(self, cal):
        """advance_to_date should raise for past dates"""
        cal.advance_weeks(10)
        past = GameDate(2025, 1, 1)
        
        with pytest.raises(ValueError):
            cal.advance_to_date(past)
    
    def test_weeks_until(self, cal):
        """weeks_until should calculate correctly"""
        target = GameDate(2025, 2, 1)
        weeks = cal.weeks_until(target)
        
        assert weeks == 4  # About 31 days = 4 weeks
    
    def test_date_from_weeks(self, cal):
        """date_from_weeks should return future date"""
        future = cal.date_from_weeks(4)
        
        assert future.month == 1
        assert future.day == 29
    
    def test_is_past_future_today(self, cal):
        """Date checking methods should work"""
        today = cal.current_date
        yesterday = today.subtract_days(1)
        tomorrow = today.add_days(1)
        
        assert cal.is_today(today)
        assert cal.is_past(yesterday)
        assert cal.is_future(tomorrow)
    
    def test_get_next_saturday(self, cal):
        """Should find next Saturday"""
        saturday = cal.get_next_saturday()
        
        assert saturday.day_of_week == DayOfWeek.SATURDAY
        assert saturday > cal.current_date
    
    def test_get_saturdays_in_range(self, cal):
        """Should return all Saturdays in range"""
        saturdays = cal.get_saturdays_in_range(8)
        
        assert len(saturdays) >= 8
        for sat in saturdays:
            assert sat.day_of_week == DayOfWeek.SATURDAY
    
    def test_iter_weeks(self, cal):
        """iter_weeks should yield future dates"""
        weeks = list(cal.iter_weeks(4))
        
        assert len(weeks) == 4
        assert all(w > cal.current_date for w in weeks)
    
    def test_to_dict_from_dict(self, cal):
        """Should serialize and deserialize correctly"""
        cal.advance_weeks(10)
        
        data = cal.to_dict()
        restored = GameCalendar.from_dict(data)
        
        assert restored.current_date == cal.current_date
        assert restored.total_weeks == cal.total_weeks
    
    def test_set_date(self, cal):
        """set_date should directly set date"""
        new_date = GameDate(2026, 6, 15)
        cal.set_date(new_date)
        
        assert cal.current_date == new_date


class TestUtilityFunctions:
    """Tests for utility functions"""
    
    def test_format_weeks_duration_singular(self):
        """Should handle singular week"""
        assert format_weeks_duration(1) == "1 week"
    
    def test_format_weeks_duration_plural(self):
        """Should handle plural weeks"""
        assert format_weeks_duration(3) == "3 weeks"
    
    def test_format_weeks_duration_months(self):
        """Should convert to months"""
        result = format_weeks_duration(8)
        assert "month" in result
    
    def test_format_weeks_duration_years(self):
        """Should convert to years"""
        result = format_weeks_duration(52)
        assert "year" in result
    
    def test_format_weeks_duration_zero(self):
        """Zero should return 'now'"""
        assert format_weeks_duration(0) == "now"
    
    def test_format_weeks_duration_negative(self):
        """Negative should show 'ago'"""
        result = format_weeks_duration(-5)
        assert "ago" in result
    
    def test_calculate_age_on_date(self):
        """Should calculate age correctly"""
        birth = GameDate(1990, 6, 15)
        
        before_birthday = GameDate(2025, 6, 1)
        after_birthday = GameDate(2025, 6, 20)
        
        assert calculate_age_on_date(birth, before_birthday) == 34
        assert calculate_age_on_date(birth, after_birthday) == 35
    
    def test_get_month_name(self):
        """Should return full month names"""
        assert get_month_name(1) == "January"
        assert get_month_name(12) == "December"
    
    def test_get_month_abbrev(self):
        """Should return abbreviated month names"""
        assert get_month_abbrev(1) == "Jan"
        assert get_month_abbrev(12) == "Dec"


class TestGlobalCalendar:
    """Tests for global calendar instance"""
    
    def test_global_calendar_exists(self):
        """Global calendar should exist"""
        assert calendar is not None
        assert isinstance(calendar, GameCalendar)
    
    def test_current_date_function(self):
        """current_date() should return date"""
        result = current_date()
        assert isinstance(result, GameDate)
    
    def test_weeks_until_function(self):
        """weeks_until() should calculate correctly"""
        target = current_date().add_weeks(5)
        result = weeks_until(target)
        assert result == 5


class TestConstants:
    """Tests for module constants"""
    
    def test_days_per_week(self):
        """Should be 7 days per week"""
        assert DAYS_PER_WEEK == 7
    
    def test_weeks_per_year(self):
        """Should be 52 weeks per year"""
        assert WEEKS_PER_YEAR == 52


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
