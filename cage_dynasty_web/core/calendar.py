# core/calendar.py — stub for web app
from dataclasses import dataclass
from typing import Optional
from datetime import date as _date

@dataclass
class GameDate:
    year: int = 1
    month: int = 1
    day: int = 1
    week: int = 1

    def format(self, style: str = "short") -> str:
        return f"Year {self.year}, Week {self.week}"

    def advance_week(self) -> "GameDate":
        self.week += 1
        if self.week > 52:
            self.week = 1
            self.year += 1
        return self

class _Calendar:
    def __init__(self):
        self.current_date = GameDate()
    def advance_week(self) -> GameDate:
        return self.current_date.advance_week()

calendar = _Calendar()


class GameCalendar:
    """Calendar stub for web deployment — tracks week number only."""
    def __init__(self, start_date=None):
        self.start_date = start_date
        self.current_week = 0

    def advance_week(self) -> int:
        self.current_week += 1
        return self.current_week

    def get_current_week(self) -> int:
        return self.current_week

    def get_date_for_week(self, week: int):
        return GameDate(week=week)

    def to_dict(self):
        return {"current_week": self.current_week, "start_date": str(self.start_date)}

    @classmethod
    def from_dict(cls, data: dict) -> "GameCalendar":
        from datetime import date as _d
        cal = cls()
        cal.current_week = data.get("current_week", 0)
        return cal
