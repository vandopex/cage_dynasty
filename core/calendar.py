# core/calendar.py
# Module 4: Time & Calendar System
# Lines: 387
#
# The heartbeat of Cage Dynasty. Manages game time, scheduling,
# and date-related calculations.

"""
Cage Dynasty - Time & Calendar System

This module handles all time-related functionality:
- Game clock (current date, week advancement)
- Date calculations and formatting
- Scheduling helpers
- Time-based event emission

The game operates on a weekly tick system where each "advance"
moves time forward by one week.

USAGE:
    from core.calendar import calendar, GameCalendar
    
    # Get current date
    today = calendar.current_date
    
    # Advance time
    calendar.advance_week()
    
    # Check dates
    weeks_until = calendar.weeks_until(some_date)
    is_available = calendar.is_date_available(fighter, date)

IMPORT RULES:
- This module imports from core.types, core.events, core.config
- All other game modules may import from this module
"""

from typing import Optional, List, Tuple, Dict, Any, Generator
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum, auto
import calendar as py_calendar

from core.types import EventType
from core.events import event_bus, emit
from core.config import get_config

# ============================================================================
# CONSTANTS
# ============================================================================

DAYS_PER_WEEK = 7
WEEKS_PER_YEAR = 52
MONTHS_PER_YEAR = 12

# Default game start date (January 1, 2025)
DEFAULT_START_DATE = date(2025, 1, 1)


# ============================================================================
# DAY OF WEEK ENUM
# ============================================================================

class DayOfWeek(Enum):
    """Days of the week for scheduling"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6
    
    @classmethod
    def from_date(cls, d: date) -> 'DayOfWeek':
        """Get day of week from a date"""
        return cls(d.weekday())


# ============================================================================
# GAME DATE - Immutable date wrapper
# ============================================================================

@dataclass(frozen=True)
class GameDate:
    """
    Immutable wrapper around a date with game-specific utilities.
    
    Provides convenient methods for date manipulation and comparison
    within the game context.
    """
    year: int
    month: int
    day: int
    
    @classmethod
    def from_date(cls, d: date) -> 'GameDate':
        """Create GameDate from Python date"""
        return cls(d.year, d.month, d.day)
    
    @classmethod
    def today(cls) -> 'GameDate':
        """Create GameDate for today"""
        return cls.from_date(date.today())
    
    def to_date(self) -> date:
        """Convert to Python date"""
        return date(self.year, self.month, self.day)
    
    def add_days(self, days: int) -> 'GameDate':
        """Return new GameDate with days added"""
        new_date = self.to_date() + timedelta(days=days)
        return GameDate.from_date(new_date)
    
    def add_weeks(self, weeks: int) -> 'GameDate':
        """Return new GameDate with weeks added"""
        return self.add_days(weeks * DAYS_PER_WEEK)
    
    def add_months(self, months: int) -> 'GameDate':
        """Return new GameDate with months added (approximate)"""
        # Simple approximation: 30 days per month
        return self.add_days(months * 30)
    
    def subtract_days(self, days: int) -> 'GameDate':
        """Return new GameDate with days subtracted"""
        return self.add_days(-days)
    
    def subtract_weeks(self, weeks: int) -> 'GameDate':
        """Return new GameDate with weeks subtracted"""
        return self.add_weeks(-weeks)
    
    def days_until(self, other: 'GameDate') -> int:
        """Calculate days until another date (negative if in past)"""
        return (other.to_date() - self.to_date()).days
    
    def weeks_until(self, other: 'GameDate') -> int:
        """Calculate weeks until another date"""
        return self.days_until(other) // DAYS_PER_WEEK
    
    def days_since(self, other: 'GameDate') -> int:
        """Calculate days since another date"""
        return -self.days_until(other)
    
    def weeks_since(self, other: 'GameDate') -> int:
        """Calculate weeks since another date"""
        return -self.weeks_until(other)
    
    @property
    def day_of_week(self) -> DayOfWeek:
        """Get the day of the week"""
        return DayOfWeek.from_date(self.to_date())
    
    @property
    def is_weekend(self) -> bool:
        """Check if date is Saturday or Sunday"""
        return self.day_of_week in (DayOfWeek.SATURDAY, DayOfWeek.SUNDAY)
    
    @property
    def week_of_year(self) -> int:
        """Get ISO week number (1-52/53)"""
        return self.to_date().isocalendar()[1]
    
    @property
    def quarter(self) -> int:
        """Get quarter of the year (1-4)"""
        return (self.month - 1) // 3 + 1
    
    def format(self, style: str = "medium") -> str:
        """
        Format date for display.
        
        Styles:
            short: "1/15/25"
            medium: "Jan 15, 2025"
            long: "January 15, 2025"
            iso: "2025-01-15"
        """
        d = self.to_date()
        
        if style == "short":
            return f"{self.month}/{self.day}/{self.year % 100}"
        elif style == "medium":
            return d.strftime("%b %d, %Y")
        elif style == "long":
            return d.strftime("%B %d, %Y")
        elif style == "iso":
            return d.isoformat()
        else:
            return str(d)
    
    def __str__(self) -> str:
        return self.format("medium")
    
    def __lt__(self, other: 'GameDate') -> bool:
        return self.to_date() < other.to_date()
    
    def __le__(self, other: 'GameDate') -> bool:
        return self.to_date() <= other.to_date()
    
    def __gt__(self, other: 'GameDate') -> bool:
        return self.to_date() > other.to_date()
    
    def __ge__(self, other: 'GameDate') -> bool:
        return self.to_date() >= other.to_date()


# ============================================================================
# GAME CALENDAR
# ============================================================================

class GameCalendar:
    """
    Central time management for the game.
    
    Tracks the current game date and provides utilities for:
    - Advancing time (weekly ticks)
    - Date calculations
    - Event scheduling
    - Time-based queries
    """
    
    def __init__(self, start_date: Optional[date] = None):
        """
        Initialize the calendar.
        
        Args:
            start_date: Starting date for the game (defaults to Jan 1, 2025)
        """
        if start_date is None:
            start_date = DEFAULT_START_DATE
        
        self._current_date = GameDate.from_date(start_date)
        self._start_date = GameDate.from_date(start_date)
        self._week_number = 1
        self._total_weeks_elapsed = 0
    
    @property
    def current_date(self) -> GameDate:
        """Get the current game date"""
        return self._current_date
    
    @property
    def start_date(self) -> GameDate:
        """Get the game's start date"""
        return self._start_date
    
    @property
    def week_number(self) -> int:
        """Get the current week number within the year"""
        return self._current_date.week_of_year
    
    @property
    def total_weeks(self) -> int:
        """Get total weeks elapsed since game start"""
        return self._total_weeks_elapsed
    
    @property
    def current_year(self) -> int:
        """Get the current year"""
        return self._current_date.year
    
    @property
    def current_month(self) -> int:
        """Get the current month (1-12)"""
        return self._current_date.month
    
    @property
    def current_quarter(self) -> int:
        """Get the current quarter (1-4)"""
        return self._current_date.quarter
    
    def advance_week(self) -> GameDate:
        """
        Advance time by one week.
        
        Emits appropriate events for week/month/year transitions.
        
        Returns:
            The new current date
        """
        old_date = self._current_date
        old_month = old_date.month
        old_year = old_date.year
        
        # Advance the date
        self._current_date = old_date.add_weeks(1)
        self._total_weeks_elapsed += 1
        
        # Emit week advanced event
        emit(EventType.WEEK_ADVANCED, {
            "previous_date": old_date,
            "new_date": self._current_date,
            "week_number": self._total_weeks_elapsed,
        })
        
        # Check for month change
        if self._current_date.month != old_month:
            emit(EventType.MONTH_ADVANCED, {
                "previous_month": old_month,
                "new_month": self._current_date.month,
                "year": self._current_date.year,
            })
        
        # Check for year change
        if self._current_date.year != old_year:
            emit(EventType.YEAR_ADVANCED, {
                "previous_year": old_year,
                "new_year": self._current_date.year,
            })
        
        return self._current_date
    
    def advance_weeks(self, count: int) -> GameDate:
        """
        Advance time by multiple weeks.
        
        Args:
            count: Number of weeks to advance
        
        Returns:
            The new current date
        """
        for _ in range(count):
            self.advance_week()
        return self._current_date
    
    def advance_to_date(self, target: GameDate) -> int:
        """
        Advance time until reaching target date.
        
        Args:
            target: Date to advance to
        
        Returns:
            Number of weeks advanced
        
        Raises:
            ValueError: If target is in the past
        """
        weeks = self._current_date.weeks_until(target)
        
        if weeks < 0:
            raise ValueError(f"Cannot advance to past date: {target}")
        
        self.advance_weeks(weeks)
        return weeks
    
    def weeks_until(self, target: GameDate) -> int:
        """Calculate weeks until a target date"""
        return self._current_date.weeks_until(target)
    
    def weeks_since(self, past: GameDate) -> int:
        """Calculate weeks since a past date"""
        return self._current_date.weeks_since(past)
    
    def date_from_weeks(self, weeks: int) -> GameDate:
        """Get a date that is N weeks from now"""
        return self._current_date.add_weeks(weeks)
    
    def is_past(self, check_date: GameDate) -> bool:
        """Check if a date is in the past"""
        return check_date < self._current_date
    
    def is_future(self, check_date: GameDate) -> bool:
        """Check if a date is in the future"""
        return check_date > self._current_date
    
    def is_today(self, check_date: GameDate) -> bool:
        """Check if a date is the current date"""
        return check_date == self._current_date
    
    def get_next_saturday(self) -> GameDate:
        """Get the next Saturday (typical fight night)"""
        current = self._current_date
        days_until_saturday = (5 - current.to_date().weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7  # Next Saturday, not today
        return current.add_days(days_until_saturday)
    
    def get_saturdays_in_range(
        self, 
        weeks_ahead: int
    ) -> List[GameDate]:
        """Get all Saturdays within a range of weeks"""
        saturdays = []
        current = self.get_next_saturday()
        end_date = self._current_date.add_weeks(weeks_ahead)
        
        while current <= end_date:
            saturdays.append(current)
            current = current.add_weeks(1)
        
        return saturdays
    
    def iter_weeks(self, count: int) -> Generator[GameDate, None, None]:
        """
        Iterate over future weeks without advancing time.
        
        Useful for scheduling lookahead.
        
        Args:
            count: Number of weeks to iterate
        
        Yields:
            GameDate for each future week
        """
        current = self._current_date
        for i in range(count):
            yield current.add_weeks(i + 1)
    
    def set_date(self, new_date: GameDate) -> None:
        """
        Directly set the current date (for loading saves).
        
        Warning: Does not emit events. Use advance_week for normal progression.
        
        Args:
            new_date: The date to set
        """
        self._current_date = new_date
        self._total_weeks_elapsed = self._start_date.weeks_until(new_date)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export calendar state for saving"""
        return {
            "current_date": {
                "year": self._current_date.year,
                "month": self._current_date.month,
                "day": self._current_date.day,
            },
            "start_date": {
                "year": self._start_date.year,
                "month": self._start_date.month,
                "day": self._start_date.day,
            },
            "total_weeks_elapsed": self._total_weeks_elapsed,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameCalendar':
        """Create calendar from saved data"""
        start = data["start_date"]
        start_date = date(start["year"], start["month"], start["day"])
        
        cal = cls(start_date)
        
        current = data["current_date"]
        cal._current_date = GameDate(
            current["year"], current["month"], current["day"]
        )
        cal._total_weeks_elapsed = data["total_weeks_elapsed"]
        
        return cal
    
    def __repr__(self) -> str:
        return f"GameCalendar(current={self._current_date}, week={self._total_weeks_elapsed})"


# ============================================================================
# DATE UTILITIES
# ============================================================================

def format_weeks_duration(weeks: int) -> str:
    """
    Format a number of weeks as human-readable duration.
    
    Examples:
        1 -> "1 week"
        4 -> "1 month"
        52 -> "1 year"
        78 -> "1 year, 6 months"
    """
    if weeks < 0:
        return f"{abs(weeks)} weeks ago"
    
    if weeks == 0:
        return "now"
    
    if weeks == 1:
        return "1 week"
    
    if weeks < 4:
        return f"{weeks} weeks"
    
    months = weeks // 4
    remaining_weeks = weeks % 4
    
    if months < 12:
        if remaining_weeks == 0:
            return f"{months} month{'s' if months > 1 else ''}"
        return f"{months} month{'s' if months > 1 else ''}, {remaining_weeks} week{'s' if remaining_weeks > 1 else ''}"
    
    years = months // 12
    remaining_months = months % 12
    
    if remaining_months == 0:
        return f"{years} year{'s' if years > 1 else ''}"
    return f"{years} year{'s' if years > 1 else ''}, {remaining_months} month{'s' if remaining_months > 1 else ''}"


def calculate_age_on_date(birth_date: GameDate, on_date: GameDate) -> int:
    """Calculate age in years on a specific date"""
    age = on_date.year - birth_date.year
    
    # Adjust if birthday hasn't occurred yet
    if (on_date.month, on_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return max(0, age)


def get_month_name(month: int) -> str:
    """Get full month name from month number"""
    return py_calendar.month_name[month]


def get_month_abbrev(month: int) -> str:
    """Get abbreviated month name"""
    return py_calendar.month_abbr[month]


# ============================================================================
# GLOBAL CALENDAR INSTANCE
# ============================================================================

# Singleton instance for the entire game
calendar = GameCalendar()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def current_date() -> GameDate:
    """Get current game date"""
    return calendar.current_date


def advance_week() -> GameDate:
    """Advance game time by one week"""
    return calendar.advance_week()


def weeks_until(target: GameDate) -> int:
    """Get weeks until a target date"""
    return calendar.weeks_until(target)
