# entities/promotion.py
# Module 7: Promotion Entity
# Lines: 521
#
# The Dynasty Fighting Championship - where legends are made.
# Single promotion that hosts all events and crowns champions.

"""
Cage Dynasty - Promotion Entity

This module defines the Promotion class, representing the fighting
organization that hosts events and manages divisions. The default
promotion is "Dynasty Fighting Championship" (DFC).

A Promotion:
- Manages multiple weight class divisions
- Tracks champions and rankings per division
- Hosts fight events/cards
- Handles fighter contracts (promotional level)
- Manages event scheduling

USAGE:
    from entities.promotion import Promotion, create_promotion, Division
    
    # Create the promotion (usually just one)
    dfc = create_promotion("Dynasty Fighting Championship")
    
    # Access a division
    lightweight = dfc.get_division(WeightClass.LIGHTWEIGHT)
    
    # Check champion
    champ_id = dfc.get_champion(WeightClass.LIGHTWEIGHT)

IMPORT RULES:
- This module imports from core modules only
- Other modules may import Promotion
"""

from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import date
import uuid

from core.types import (
    WeightClass, EventType, FightOutcome,
    WEIGHT_CLASS_ORDER, RANKINGS_PER_DIVISION
)
from core.calendar import GameDate, calendar
from core.events import emit
from core.config import get_config


# ============================================================================
# DIVISION CLASS
# ============================================================================

class Division:
    """
    A weight class division within the promotion.
    
    Tracks the champion, rankings, and contenders for a single
    weight class.
    """
    
    def __init__(self, weight_class: WeightClass):
        """
        Create a new division.
        
        Args:
            weight_class: The weight class this division represents
        """
        self._weight_class = weight_class
        self._champion_id: Optional[str] = None
        self._rankings: List[str] = []  # Ordered list of fighter IDs, index 0 = #1 contender
        self._is_active = True
    
    @property
    def weight_class(self) -> WeightClass:
        return self._weight_class
    
    @property
    def name(self) -> str:
        return self._weight_class.value
    
    @property
    def champion_id(self) -> Optional[str]:
        return self._champion_id
    
    @property
    def has_champion(self) -> bool:
        return self._champion_id is not None
    
    @property
    def rankings(self) -> List[str]:
        """Get ranked fighters (copy)"""
        return self._rankings.copy()
    
    @property
    def ranked_count(self) -> int:
        """Number of ranked fighters"""
        return len(self._rankings)
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def set_champion(self, fighter_id: str) -> Optional[str]:
        """
        Set the division champion.
        
        Args:
            fighter_id: ID of new champion
        
        Returns:
            ID of previous champion (if any)
        """
        previous = self._champion_id
        self._champion_id = fighter_id
        
        # Remove from rankings if ranked
        if fighter_id in self._rankings:
            self._rankings.remove(fighter_id)
        
        return previous
    
    def vacate_title(self) -> Optional[str]:
        """
        Vacate the championship.
        
        Returns:
            ID of vacating champion (if any)
        """
        previous = self._champion_id
        self._champion_id = None
        return previous
    
    def get_rank(self, fighter_id: str) -> Optional[int]:
        """
        Get a fighter's ranking (1-indexed).
        
        Returns:
            Rank 1-15, or None if unranked
        """
        if fighter_id == self._champion_id:
            return 0  # Champion is rank 0
        
        try:
            return self._rankings.index(fighter_id) + 1
        except ValueError:
            return None
    
    def is_ranked(self, fighter_id: str) -> bool:
        """Check if fighter is ranked in this division"""
        return fighter_id == self._champion_id or fighter_id in self._rankings
    
    def set_rank(self, fighter_id: str, rank: int) -> None:
        """
        Set a fighter's ranking.
        
        Args:
            fighter_id: Fighter to rank
            rank: Desired rank (1-15)
        """
        if rank < 1 or rank > RANKINGS_PER_DIVISION:
            return
        
        # Remove from current position if ranked
        if fighter_id in self._rankings:
            self._rankings.remove(fighter_id)
        
        # Insert at new position (rank 1 = index 0)
        index = rank - 1
        if index >= len(self._rankings):
            self._rankings.append(fighter_id)
        else:
            self._rankings.insert(index, fighter_id)
        
        # Trim to max rankings
        self._rankings = self._rankings[:RANKINGS_PER_DIVISION]
    
    def remove_from_rankings(self, fighter_id: str) -> bool:
        """
        Remove a fighter from rankings.
        
        Returns:
            True if removed, False if not ranked
        """
        if fighter_id in self._rankings:
            self._rankings.remove(fighter_id)
            return True
        return False
    
    def get_top_contender(self) -> Optional[str]:
        """Get the #1 contender"""
        return self._rankings[0] if self._rankings else None
    
    def get_top_contenders(self, count: int = 5) -> List[str]:
        """Get top N contenders"""
        return self._rankings[:count]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export division data"""
        return {
            "weight_class": self._weight_class.value,
            "champion_id": self._champion_id,
            "rankings": self._rankings.copy(),
            "is_active": self._is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Division':
        """Create division from saved data"""
        division = cls(WeightClass(data["weight_class"]))
        division._champion_id = data.get("champion_id")
        division._rankings = data.get("rankings", [])
        division._is_active = data.get("is_active", True)
        return division
    
    def __repr__(self) -> str:
        champ_str = f"Champion: {self._champion_id}" if self._champion_id else "Vacant"
        return f"Division({self.name}, {champ_str}, {self.ranked_count} ranked)"


# ============================================================================
# SCHEDULED EVENT
# ============================================================================

@dataclass
class ScheduledEvent:
    """A scheduled fight card/event"""
    event_id: str
    name: str
    date: GameDate
    location: str
    fight_ids: List[str] = field(default_factory=list)
    main_event_fight_id: Optional[str] = None
    is_ppv: bool = False
    is_completed: bool = False
    
    def add_fight(self, fight_id: str, is_main_event: bool = False) -> None:
        """Add a fight to this event"""
        if fight_id not in self.fight_ids:
            self.fight_ids.append(fight_id)
        if is_main_event:
            self.main_event_fight_id = fight_id
    
    @property
    def fight_count(self) -> int:
        return len(self.fight_ids)
    
    def __str__(self) -> str:
        return f"{self.name} - {self.date.format('medium')} ({self.fight_count} fights)"


# ============================================================================
# PROMOTION CLASS
# ============================================================================

class Promotion:
    """
    The fighting organization that hosts events and manages divisions.
    
    Default is "Dynasty Fighting Championship" (DFC).
    """
    
    # Default promotion name
    DEFAULT_NAME = "Dynasty Fighting Championship"
    DEFAULT_ABBREVIATION = "DFC"
    
    def __init__(
        self,
        name: str = DEFAULT_NAME,
        abbreviation: str = DEFAULT_ABBREVIATION,
        promotion_id: Optional[str] = None
    ):
        """
        Create a promotion.
        
        Args:
            name: Full promotion name
            abbreviation: Short form (e.g., "DFC")
            promotion_id: Unique ID (auto-generated if not provided)
        """
        self._id = promotion_id or str(uuid.uuid4())[:12]
        self._name = name
        self._abbreviation = abbreviation
        
        # Create all divisions
        self._divisions: Dict[WeightClass, Division] = {
            wc: Division(wc) for wc in WEIGHT_CLASS_ORDER
        }
        
        # Signed fighters (promotional contracts)
        self._signed_fighter_ids: Set[str] = set()
        
        # Events
        self._scheduled_events: List[ScheduledEvent] = []
        self._completed_events: List[ScheduledEvent] = []
        self._next_event_number = 1
        
        # Stats
        self._total_events_held = 0
        self._total_fights_held = 0
        
        # Metadata
        self._created_date = calendar.current_date
    
    # ========================================================================
    # IDENTITY
    # ========================================================================
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def abbreviation(self) -> str:
        return self._abbreviation
    
    @property
    def full_name(self) -> str:
        return f"{self._name} ({self._abbreviation})"
    
    # ========================================================================
    # DIVISIONS
    # ========================================================================
    
    @property
    def divisions(self) -> List[Division]:
        """Get all divisions in weight order"""
        return [self._divisions[wc] for wc in WEIGHT_CLASS_ORDER]
    
    def get_division(self, weight_class: WeightClass) -> Division:
        """Get a specific division"""
        return self._divisions[weight_class]
    
    def get_champion(self, weight_class: WeightClass) -> Optional[str]:
        """Get champion ID for a weight class"""
        return self._divisions[weight_class].champion_id
    
    def set_champion(self, weight_class: WeightClass, fighter_id: str) -> None:
        """Set the champion for a weight class"""
        previous = self._divisions[weight_class].set_champion(fighter_id)
        
        emit(EventType.TITLE_WON, {
            "fighter_id": fighter_id,
            "weight_class": weight_class.value,
            "previous_champion_id": previous,
            "promotion_id": self._id
        })
        
        if previous:
            emit(EventType.TITLE_LOST, {
                "fighter_id": previous,
                "weight_class": weight_class.value,
                "new_champion_id": fighter_id,
                "promotion_id": self._id
            })
    
    def vacate_title(self, weight_class: WeightClass) -> Optional[str]:
        """Vacate a championship"""
        previous = self._divisions[weight_class].vacate_title()
        
        if previous:
            emit(EventType.TITLE_VACATED, {
                "fighter_id": previous,
                "weight_class": weight_class.value,
                "promotion_id": self._id
            })
        
        return previous
    
    def get_rankings(self, weight_class: WeightClass) -> List[str]:
        """Get ranked fighters for a weight class"""
        return self._divisions[weight_class].rankings
    
    def get_rank(self, weight_class: WeightClass, fighter_id: str) -> Optional[int]:
        """Get a fighter's rank in a division"""
        return self._divisions[weight_class].get_rank(fighter_id)
    
    def set_rank(self, weight_class: WeightClass, fighter_id: str, rank: int) -> None:
        """Set a fighter's rank"""
        self._divisions[weight_class].set_rank(fighter_id, rank)
        
        emit(EventType.FIGHTER_RANKED, {
            "fighter_id": fighter_id,
            "weight_class": weight_class.value,
            "rank": rank,
            "promotion_id": self._id
        })
    
    def is_champion(self, fighter_id: str) -> bool:
        """Check if fighter is champion in any division"""
        return any(d.champion_id == fighter_id for d in self._divisions.values())
    
    def get_all_champions(self) -> Dict[WeightClass, Optional[str]]:
        """Get all champions by weight class"""
        return {wc: d.champion_id for wc, d in self._divisions.items()}
    
    # ========================================================================
    # FIGHTER MANAGEMENT
    # ========================================================================
    
    @property
    def signed_fighter_ids(self) -> List[str]:
        """Get all signed fighter IDs"""
        return list(self._signed_fighter_ids)
    
    @property
    def roster_size(self) -> int:
        """Total signed fighters"""
        return len(self._signed_fighter_ids)
    
    def is_signed(self, fighter_id: str) -> bool:
        """Check if fighter is signed to promotion"""
        return fighter_id in self._signed_fighter_ids
    
    def sign_fighter(self, fighter_id: str) -> bool:
        """
        Sign a fighter to the promotion.
        
        Args:
            fighter_id: Fighter to sign
        
        Returns:
            True if signed, False if already signed
        """
        if fighter_id in self._signed_fighter_ids:
            return False
        
        self._signed_fighter_ids.add(fighter_id)
        return True
    
    def release_fighter(self, fighter_id: str) -> bool:
        """
        Release a fighter from the promotion.
        
        Args:
            fighter_id: Fighter to release
        
        Returns:
            True if released, False if not signed
        """
        if fighter_id not in self._signed_fighter_ids:
            return False
        
        self._signed_fighter_ids.remove(fighter_id)
        
        # Remove from all rankings
        for division in self._divisions.values():
            division.remove_from_rankings(fighter_id)
            if division.champion_id == fighter_id:
                division.vacate_title()
        
        return True
    
    # ========================================================================
    # EVENT MANAGEMENT
    # ========================================================================
    
    @property
    def scheduled_events(self) -> List[ScheduledEvent]:
        """Get upcoming events"""
        return self._scheduled_events.copy()
    
    @property
    def next_event(self) -> Optional[ScheduledEvent]:
        """Get the next scheduled event"""
        if not self._scheduled_events:
            return None
        return min(self._scheduled_events, key=lambda e: e.date.to_date())
    
    def schedule_event(
        self,
        date: GameDate,
        location: str = "Las Vegas",
        name: Optional[str] = None,
        is_ppv: bool = False
    ) -> ScheduledEvent:
        """
        Schedule a new event.
        
        Args:
            date: Event date
            location: Event location
            name: Custom event name (auto-generated if None)
            is_ppv: Is this a pay-per-view event?
        
        Returns:
            The scheduled event
        """
        if name is None:
            name = f"{self._abbreviation} {self._next_event_number}"
        
        event = ScheduledEvent(
            event_id=str(uuid.uuid4())[:8],
            name=name,
            date=date,
            location=location,
            is_ppv=is_ppv
        )
        
        self._scheduled_events.append(event)
        self._next_event_number += 1
        
        return event
    
    def get_event(self, event_id: str) -> Optional[ScheduledEvent]:
        """Find an event by ID"""
        for event in self._scheduled_events:
            if event.event_id == event_id:
                return event
        for event in self._completed_events:
            if event.event_id == event_id:
                return event
        return None
    
    def complete_event(self, event_id: str) -> bool:
        """
        Mark an event as completed.
        
        Returns:
            True if completed, False if not found
        """
        for event in self._scheduled_events:
            if event.event_id == event_id:
                event.is_completed = True
                self._scheduled_events.remove(event)
                self._completed_events.append(event)
                self._total_events_held += 1
                self._total_fights_held += event.fight_count
                return True
        return False
    
    def get_events_on_date(self, date: GameDate) -> List[ScheduledEvent]:
        """Get all events on a specific date"""
        return [e for e in self._scheduled_events if e.date == date]
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    @property
    def total_events(self) -> int:
        return self._total_events_held
    
    @property
    def total_fights(self) -> int:
        return self._total_fights_held
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Export promotion data for saving"""
        return {
            "id": self._id,
            "name": self._name,
            "abbreviation": self._abbreviation,
            "divisions": {
                wc.value: div.to_dict() 
                for wc, div in self._divisions.items()
            },
            "signed_fighter_ids": list(self._signed_fighter_ids),
            "scheduled_events": [
                {
                    "event_id": e.event_id,
                    "name": e.name,
                    "date": {"year": e.date.year, "month": e.date.month, "day": e.date.day},
                    "location": e.location,
                    "fight_ids": e.fight_ids,
                    "main_event_fight_id": e.main_event_fight_id,
                    "is_ppv": e.is_ppv,
                    "is_completed": e.is_completed
                }
                for e in self._scheduled_events
            ],
            "next_event_number": self._next_event_number,
            "total_events_held": self._total_events_held,
            "total_fights_held": self._total_fights_held
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Promotion':
        """Create promotion from saved data"""
        promotion = cls(
            name=data["name"],
            abbreviation=data["abbreviation"],
            promotion_id=data["id"]
        )
        
        # Restore divisions
        for wc_str, div_data in data.get("divisions", {}).items():
            wc = WeightClass(wc_str)
            promotion._divisions[wc] = Division.from_dict(div_data)
        
        promotion._signed_fighter_ids = set(data.get("signed_fighter_ids", []))
        
        # Restore scheduled events
        for event_data in data.get("scheduled_events", []):
            d = event_data["date"]
            event = ScheduledEvent(
                event_id=event_data["event_id"],
                name=event_data["name"],
                date=GameDate(d["year"], d["month"], d["day"]),
                location=event_data["location"],
                fight_ids=event_data.get("fight_ids", []),
                main_event_fight_id=event_data.get("main_event_fight_id"),
                is_ppv=event_data.get("is_ppv", False),
                is_completed=event_data.get("is_completed", False)
            )
            promotion._scheduled_events.append(event)
        
        promotion._next_event_number = data.get("next_event_number", 1)
        promotion._total_events_held = data.get("total_events_held", 0)
        promotion._total_fights_held = data.get("total_fights_held", 0)
        
        return promotion
    
    def __repr__(self) -> str:
        return f"Promotion({self._name}, {self.roster_size} fighters, {len(self._scheduled_events)} events scheduled)"
    
    def __str__(self) -> str:
        return self.full_name


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_promotion(
    name: str = Promotion.DEFAULT_NAME,
    abbreviation: str = Promotion.DEFAULT_ABBREVIATION
) -> Promotion:
    """
    Factory function to create a promotion.
    
    Args:
        name: Full promotion name (default: "Dynasty Fighting Championship")
        abbreviation: Short form (default: "DFC")
    
    Returns:
        New Promotion instance
    """
    return Promotion(name=name, abbreviation=abbreviation)


# ============================================================================
# CONVENIENCE - Default promotion instance
# ============================================================================

def create_dfc() -> Promotion:
    """Create the default Dynasty Fighting Championship"""
    return create_promotion()
