# entities/fighter.py
# Module 5: Fighter Entity
# Lines: ~870
#
# The heart of Cage Dynasty - the fighters themselves.
# Everything revolves around these athletes.

"""
Cage Dynasty - Fighter Entity

This module defines the Fighter class, representing an MMA fighter
in the game world. Fighters have:
- Physical attributes (strength, speed, cardio, etc.)
- Technical skills (striking, grappling, etc.)
- Mental attributes (heart, IQ, composure)
- Fighting style (one of 11 archetypes)
- Traits (special abilities like Iron Chin, Cardio Machine)
- Career history (record, fight history, rankings)
- Personal info (name, age, nationality, nickname)
- Status tracking (injuries, activity, morale)

USAGE:
    from entities.fighter import Fighter, create_fighter
    
    # Create a fighter
    fighter = create_fighter(
        first_name="John",
        last_name="Smith",
        weight_class=WeightClass.LIGHTWEIGHT,
        birth_date=GameDate(1995, 6, 15)
    )
    
    # Access info
    print(fighter.full_name)       # "John Smith"
    print(fighter.record)          # "0-0"
    print(fighter.age)             # 29
    print(fighter.fighting_style)  # FightingStyle.STRIKER
    print(fighter.traits)          # ["Iron Chin", "Cardio Machine"]
    
    # Update after fight
    fighter.add_win(method=FightOutcome.KO, opponent_name="Jane Doe")

IMPORT RULES:
- This module imports from core modules only
- Other entity modules may import Fighter
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import date
import uuid

from core.types import (
    WeightClass, FighterStatus, FightOutcome, InjuryType, FightingStyle,
    FightRecord, AttributeSet, WEIGHT_CLASS_SPECS,
    ATTR_MIN, ATTR_MAX, ATTR_AVERAGE,
    clamp_attribute, validate_fighter_name,
    FighterID, EventType
)
from core.calendar import GameDate, calendar, calculate_age_on_date
from core.events import emit
from core.config import get_config


# ============================================================================
# FIGHTER HISTORY ENTRY
# ============================================================================

@dataclass
class FightHistoryEntry:
    """Record of a single fight in a fighter's career"""
    date: GameDate
    opponent_name: str
    result: str  # "W", "L", "D", "NC"
    method: FightOutcome
    round_finished: int
    time_in_round: str
    opponent_id: Optional[str] = None  # Made optional with default None
    event_name: str = ""
    was_title_fight: bool = False
    weight_class: Optional[WeightClass] = None
    
    def __str__(self) -> str:
        method_str = self.method.value
        if self.result == "W":
            return f"W - def. {self.opponent_name} via {method_str} R{self.round_finished}"
        elif self.result == "L":
            return f"L - lost to {self.opponent_name} via {method_str} R{self.round_finished}"
        elif self.result == "D":
            return f"D - drew with {self.opponent_name}"
        else:
            return f"NC - {self.opponent_name}"


@dataclass
class InjuryRecord:
    """Record of an injury"""
    injury_type: InjuryType
    description: str
    date_occurred: GameDate
    recovery_weeks: int
    weeks_remaining: int = 0
    
    @property
    def is_healed(self) -> bool:
        return self.weeks_remaining <= 0
    
    def heal_week(self) -> None:
        """Process one week of healing"""
        if self.weeks_remaining > 0:
            self.weeks_remaining -= 1


# ============================================================================
# FIGHTER CLASS
# ============================================================================

class Fighter:
    """
    Represents an MMA fighter in the game.
    
    This is the core entity that everything else revolves around.
    Fighters train, fight, age, get injured, develop rivalries,
    and build legacies.
    """
    
    def __init__(
        self,
        first_name: str,
        last_name: str,
        weight_class: WeightClass,
        birth_date: GameDate,
        nationality: str = "USA",
        attributes: Optional[AttributeSet] = None,
        fighter_id: Optional[str] = None,
        fighting_style: Optional[FightingStyle] = None,
        traits: Optional[List[str]] = None
    ):
        """
        Create a new fighter.
        
        Args:
            first_name: Fighter's first name
            last_name: Fighter's last name
            weight_class: Primary weight class
            birth_date: Date of birth
            nationality: Country of origin
            attributes: Starting attributes (defaults to average)
            fighter_id: Unique ID (auto-generated if not provided)
            fighting_style: Combat archetype (defaults to BALANCED)
            traits: Special abilities (defaults to empty list)
        """
        # Identity
        self._id = fighter_id or str(uuid.uuid4())[:12]
        self._first_name = validate_fighter_name(first_name)
        self._last_name = validate_fighter_name(last_name)
        self._nickname: Optional[str] = None
        self._nationality = nationality
        
        # Physical
        self._birth_date = birth_date
        self._weight_class = weight_class
        self._natural_weight = WEIGHT_CLASS_SPECS[weight_class].natural_weight_avg
        
        # Attributes
        self._attributes = attributes or AttributeSet()
        self._potential = AttributeSet()  # Maximum potential for each stat
        
        # Fighting Style & Traits
        self._fighting_style = fighting_style or FightingStyle.BALANCED
        self._traits: List[str] = traits.copy() if traits else []
        
        # Career
        self._record = FightRecord()
        self._fight_history: List[FightHistoryEntry] = []
        self._status = FighterStatus.FREE_AGENT
        self._rank: Optional[int] = None  # None = unranked
        self._is_champion = False
        
        # Camp/Contract
        self._camp_id: Optional[str] = None
        self._contract_fights_remaining: int = 0
        
        # Health & Condition
        self._injuries: List[InjuryRecord] = []
        self._fatigue: int = 0  # 0-100
        self._morale: int = 75  # 0-100
        self._last_fight_date: Optional[GameDate] = None
        
        # Career stats
        self._ko_wins: int = 0
        self._submission_wins: int = 0
        self._decision_wins: int = 0
        self._ko_losses: int = 0
        self._total_fight_time_seconds: int = 0
        
        # Win/Loss streak tracking
        self._current_win_streak: int = 0
        self._current_loss_streak: int = 0
        
        # Popularity & Money
        self._popularity: int = 10  # 0-100, affects marketability
        self._career_earnings: int = 0
        
        # Metadata
        self._created_date = calendar.current_date
        self._debut_date: Optional[GameDate] = None
        self._retirement_date: Optional[GameDate] = None
    
    # ========================================================================
    # IDENTITY PROPERTIES
    # ========================================================================
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def first_name(self) -> str:
        return self._first_name
    
    @property
    def last_name(self) -> str:
        return self._last_name
    
    @property
    def full_name(self) -> str:
        return f"{self._first_name} {self._last_name}"
    
    @property
    def display_name(self) -> str:
        """Name with nickname if available"""
        if self._nickname:
            return f'{self._first_name} "{self._nickname}" {self._last_name}'
        return self.full_name
    
    @property
    def nickname(self) -> Optional[str]:
        return self._nickname
    
    @nickname.setter
    def nickname(self, value: Optional[str]) -> None:
        self._nickname = value
    
    @property
    def nationality(self) -> str:
        return self._nationality
    
    # ========================================================================
    # PHYSICAL PROPERTIES
    # ========================================================================
    
    @property
    def birth_date(self) -> GameDate:
        return self._birth_date
    
    @property
    def age(self) -> int:
        """Current age based on game date"""
        return calculate_age_on_date(self._birth_date, calendar.current_date)
    
    def age_on_date(self, on_date: GameDate) -> int:
        """Age on a specific date"""
        return calculate_age_on_date(self._birth_date, on_date)
    
    @property
    def weight_class(self) -> WeightClass:
        return self._weight_class
    
    @weight_class.setter
    def weight_class(self, value: WeightClass) -> None:
        self._weight_class = value
    
    @property
    def natural_weight(self) -> int:
        return self._natural_weight
    
    # ========================================================================
    # FIGHTING STYLE & TRAITS
    # ========================================================================
    
    @property
    def fighting_style(self) -> FightingStyle:
        """Fighter's primary fighting style archetype"""
        return self._fighting_style
    
    @fighting_style.setter
    def fighting_style(self, value: FightingStyle) -> None:
        self._fighting_style = value
    
    @property
    def fighting_style_display(self) -> str:
        """Display-friendly style name"""
        return self._fighting_style.value
    
    @property
    def traits(self) -> List[str]:
        """List of special traits (copy to prevent modification)"""
        return self._traits.copy()
    
    def has_trait(self, trait_name: str) -> bool:
        """Check if fighter has a specific trait"""
        return trait_name in self._traits
    
    def add_trait(self, trait_name: str) -> bool:
        """Add a trait if not already present. Returns True if added."""
        if trait_name not in self._traits:
            self._traits.append(trait_name)
            return True
        return False
    
    def remove_trait(self, trait_name: str) -> bool:
        """Remove a trait if present. Returns True if removed."""
        if trait_name in self._traits:
            self._traits.remove(trait_name)
            return True
        return False
    
    @property
    def traits_display(self) -> str:
        """Comma-separated display of traits"""
        if not self._traits:
            return "None"
        return ", ".join(self._traits)
    
    # ========================================================================
    # ATTRIBUTES
    # ========================================================================
    
    @property
    def attributes(self) -> AttributeSet:
        return self._attributes
    
    @property
    def overall(self) -> int:
        """Overall rating (average of all attributes)"""
        return self._attributes.overall
    
    @property
    def overall_rating(self) -> int:
        """Alias for overall - overall rating (average of all attributes)"""
        return self._attributes.overall
    
    @property
    def striking_overall(self) -> int:
        return self._attributes.striking_overall
    
    @property
    def grappling_overall(self) -> int:
        return self._attributes.grappling_overall
    
    def get_attribute(self, attr_name: str) -> int:
        """Get a specific attribute value"""
        return self._attributes.get(attr_name)
    
    def set_attribute(self, attr_name: str, value: int) -> None:
        """Set a specific attribute value"""
        self._attributes = self._attributes.with_change(attr_name, value)
    
    def modify_attribute(self, attr_name: str, delta: int) -> int:
        """Modify an attribute by delta, return new value"""
        current = self.get_attribute(attr_name)
        new_value = clamp_attribute(current + delta)
        self.set_attribute(attr_name, new_value)
        return new_value
    
    # ========================================================================
    # CAREER PROPERTIES
    # ========================================================================
    
    @property
    def record(self) -> FightRecord:
        return self._record
    
    @property
    def record_string(self) -> str:
        return str(self._record)
    
    @property
    def status(self) -> FighterStatus:
        return self._status
    
    @status.setter
    def status(self, value: FighterStatus) -> None:
        self._status = value
    
    @property
    def is_active(self) -> bool:
        """Whether fighter is available to fight (not retired, injured, or suspended)"""
        return self._status in (FighterStatus.ACTIVE, FighterStatus.FREE_AGENT, FighterStatus.NEGOTIATING)
    
    @property
    def rank(self) -> Optional[int]:
        return self._rank
    
    @rank.setter
    def rank(self, value: Optional[int]) -> None:
        self._rank = value
    
    @property
    def is_champion(self) -> bool:
        return self._is_champion
    
    @is_champion.setter
    def is_champion(self, value: bool) -> None:
        self._is_champion = value
    
    @property
    def is_ranked(self) -> bool:
        return self._rank is not None
    
    @property
    def is_contender(self) -> bool:
        """Top 5 ranked fighter"""
        return self._rank is not None and self._rank <= 5
    
    @property
    def fight_history(self) -> List[FightHistoryEntry]:
        return self._fight_history.copy()
    
    @property
    def total_fights(self) -> int:
        return self._record.total_fights
    
    # ========================================================================
    # WIN/LOSS STREAKS
    # ========================================================================
    
    @property
    def win_streak(self) -> int:
        """Current consecutive win streak"""
        return self._current_win_streak
    
    @property
    def loss_streak(self) -> int:
        """Current consecutive loss streak"""
        return self._current_loss_streak
    
    # ========================================================================
    # CAMP/CONTRACT
    # ========================================================================
    
    @property
    def camp_id(self) -> Optional[str]:
        return self._camp_id
    
    @camp_id.setter
    def camp_id(self, value: Optional[str]) -> None:
        self._camp_id = value
    
    @property
    def is_signed(self) -> bool:
        return self._camp_id is not None
    
    @property
    def is_free_agent(self) -> bool:
        return self._camp_id is None
    
    # ========================================================================
    # HEALTH & CONDITION
    # ========================================================================
    
    @property
    def injuries(self) -> List[InjuryRecord]:
        """List of current injuries"""
        return self._injuries.copy()
    
    @property
    def is_injured(self) -> bool:
        return any(not inj.is_healed for inj in self._injuries)
    
    @property
    def current_injury(self) -> Optional[InjuryRecord]:
        for inj in self._injuries:
            if not inj.is_healed:
                return inj
        return None
    
    @property
    def weeks_until_healthy(self) -> int:
        if not self.is_injured:
            return 0
        return max(inj.weeks_remaining for inj in self._injuries if not inj.is_healed)
    
    @property
    def fatigue(self) -> int:
        return self._fatigue
    
    @fatigue.setter
    def fatigue(self, value: int) -> None:
        self._fatigue = max(0, min(100, value))
    
    @property
    def morale(self) -> int:
        return self._morale
    
    @morale.setter
    def morale(self, value: int) -> None:
        self._morale = max(0, min(100, value))
    
    @property
    def last_fight_date(self) -> Optional[GameDate]:
        return self._last_fight_date
    
    @property
    def weeks_since_fight(self) -> int:
        """Weeks since last fight, 0 if never fought"""
        if self._last_fight_date is None:
            return 0
        current = calendar.current_date
        return current.weeks_since(self._last_fight_date)
    
    # ========================================================================
    # CAREER STATS
    # ========================================================================
    
    @property
    def ko_wins(self) -> int:
        return self._ko_wins
    
    @property
    def submission_wins(self) -> int:
        return self._submission_wins
    
    @property
    def decision_wins(self) -> int:
        return self._decision_wins
    
    @property
    def ko_losses(self) -> int:
        return self._ko_losses
    
    @property
    def finish_rate(self) -> float:
        """Percentage of wins by finish (KO or SUB)"""
        if self._record.wins == 0:
            return 0.0
        finishes = self._ko_wins + self._submission_wins
        return (finishes / self._record.wins) * 100
    
    # ========================================================================
    # POPULARITY & MONEY
    # ========================================================================
    
    @property
    def popularity(self) -> int:
        return self._popularity
    
    @popularity.setter
    def popularity(self, value: int) -> None:
        self._popularity = max(0, min(100, value))
    
    @property
    def career_earnings(self) -> int:
        return self._career_earnings
    
    def add_earnings(self, amount: int) -> None:
        """Add to career earnings"""
        self._career_earnings += amount
    
    # ========================================================================
    # FIGHT MANAGEMENT
    # ========================================================================
    
    def add_win(
        self,
        method: FightOutcome,
        opponent_name: str,
        opponent_id: Optional[str] = None,
        round_finished: int = 3,
        time_in_round: str = "5:00",
        event_name: str = "",
        was_title_fight: bool = False
    ) -> None:
        """Record a win"""
        self._record = self._record.with_win()
        self._last_fight_date = calendar.current_date
        
        # Update streak tracking
        self._current_win_streak += 1
        self._current_loss_streak = 0
        
        # Update finish stats
        if method in (FightOutcome.KO, FightOutcome.TKO):
            self._ko_wins += 1
        elif method == FightOutcome.SUBMISSION:
            self._submission_wins += 1
        else:
            self._decision_wins += 1
        
        # Update morale
        self.morale = min(100, self._morale + 10)
        
        entry = FightHistoryEntry(
            date=calendar.current_date,
            opponent_name=opponent_name,
            opponent_id=opponent_id,
            result="W",
            method=method,
            round_finished=round_finished,
            time_in_round=time_in_round,
            event_name=event_name,
            was_title_fight=was_title_fight,
            weight_class=self._weight_class
        )
        self._fight_history.append(entry)
        
        emit(EventType.FIGHTER_WIN, {"fighter_id": self._id, "method": method.value})
    
    def add_loss(
        self,
        method: FightOutcome,
        opponent_name: str,
        opponent_id: Optional[str] = None,
        round_finished: int = 3,
        time_in_round: str = "5:00",
        event_name: str = "",
        was_title_fight: bool = False
    ) -> None:
        """Record a loss"""
        self._record = self._record.with_loss()
        self._last_fight_date = calendar.current_date
        
        # Update streak tracking
        self._current_loss_streak += 1
        self._current_win_streak = 0
        
        # Track KO losses
        if method in (FightOutcome.KO, FightOutcome.TKO):
            self._ko_losses += 1
        
        # Update morale
        self.morale = max(0, self._morale - 15)
        
        entry = FightHistoryEntry(
            date=calendar.current_date,
            opponent_name=opponent_name,
            opponent_id=opponent_id,
            result="L",
            method=method,
            round_finished=round_finished,
            time_in_round=time_in_round,
            event_name=event_name,
            was_title_fight=was_title_fight,
            weight_class=self._weight_class
        )
        self._fight_history.append(entry)
        
        emit(EventType.FIGHTER_LOSS, {"fighter_id": self._id, "method": method.value})
    
    def add_draw(
        self,
        opponent_name: str,
        opponent_id: Optional[str] = None,
        event_name: str = "",
        was_title_fight: bool = False
    ) -> None:
        """Record a draw"""
        self._record = self._record.with_draw()
        self._last_fight_date = calendar.current_date
        
        # Draws reset both streaks
        self._current_win_streak = 0
        self._current_loss_streak = 0
        
        entry = FightHistoryEntry(
            date=calendar.current_date,
            opponent_name=opponent_name,
            opponent_id=opponent_id,
            result="D",
            method=FightOutcome.DRAW,
            round_finished=3,
            time_in_round="5:00",
            event_name=event_name,
            was_title_fight=was_title_fight,
            weight_class=self._weight_class
        )
        self._fight_history.append(entry)
    
    # ========================================================================
    # INJURY MANAGEMENT
    # ========================================================================
    
    def add_injury(
        self,
        injury_type: InjuryType,
        description: str,
        recovery_weeks: int
    ) -> None:
        """Add an injury to the fighter"""
        injury = InjuryRecord(
            injury_type=injury_type,
            description=description,
            date_occurred=calendar.current_date,
            recovery_weeks=recovery_weeks,
            weeks_remaining=recovery_weeks
        )
        self._injuries.append(injury)
        self._status = FighterStatus.INJURED
        
        emit(EventType.FIGHTER_INJURED, {"fighter_id": self._id, "injury": description})
    
    def heal_injuries(self, weeks: int = 1) -> None:
        """Process healing for all injuries"""
        for injury in self._injuries:
            for _ in range(weeks):
                injury.heal_week()
        
        # Check if fully healed
        if not self.is_injured:
            self._status = FighterStatus.ACTIVE
            emit(EventType.FIGHTER_RECOVERED, {"fighter_id": self._id})
    
    # ========================================================================
    # RETIREMENT
    # ========================================================================
    
    def retire(self) -> None:
        """Retire the fighter"""
        self._status = FighterStatus.RETIRED
        self._retirement_date = calendar.current_date
        emit(EventType.FIGHTER_RETIRED, {"fighter_id": self._id, "record": str(self._record)})
    
    @property
    def is_retired(self) -> bool:
        return self._status == FighterStatus.RETIRED
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Export fighter data for saving"""
        return {
            "id": self._id,
            "first_name": self._first_name,
            "last_name": self._last_name,
            "nickname": self._nickname,
            "nationality": self._nationality,
            "birth_date": {
                "year": self._birth_date.year,
                "month": self._birth_date.month,
                "day": self._birth_date.day
            },
            "weight_class": self._weight_class.value,
            "natural_weight": self._natural_weight,
            "fighting_style": self._fighting_style.value,
            "traits": self._traits.copy(),
            "attributes": {
                attr: self._attributes.get(attr)
                for attr in [
                    "strength", "speed", "cardio", "chin", "recovery",
                    "boxing", "kicks", "clinch", "power", "accuracy",
                    "wrestling", "bjj", "td_defense", "top_control", "submissions",
                    "heart", "iq", "composure", "aggression"
                ]
            },
            "record": {
                "wins": self._record.wins,
                "losses": self._record.losses,
                "draws": self._record.draws,
                "no_contests": self._record.no_contests
            },
            "status": self._status.name,
            "rank": self._rank,
            "is_champion": self._is_champion,
            "camp_id": self._camp_id,
            "popularity": self._popularity,
            "career_earnings": self._career_earnings,
            "ko_wins": self._ko_wins,
            "submission_wins": self._submission_wins,
            "decision_wins": self._decision_wins,
            "ko_losses": self._ko_losses,
            "fatigue": self._fatigue,
            "morale": self._morale,
            "win_streak": self._current_win_streak,
            "loss_streak": self._current_loss_streak,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Fighter':
        """Create fighter from saved data"""
        bd = data["birth_date"]
        birth_date = GameDate(bd["year"], bd["month"], bd["day"])
        
        attrs = AttributeSet(**data["attributes"])
        
        # Parse fighting style (with fallback for old saves)
        style_str = data.get("fighting_style", "Balanced")
        try:
            fighting_style = FightingStyle(style_str)
        except ValueError:
            fighting_style = FightingStyle.BALANCED
        
        # Parse traits (with fallback for old saves)
        traits = data.get("traits", [])
        
        fighter = cls(
            first_name=data["first_name"],
            last_name=data["last_name"],
            weight_class=WeightClass(data["weight_class"]),
            birth_date=birth_date,
            nationality=data.get("nationality", "USA"),
            attributes=attrs,
            fighter_id=data["id"],
            fighting_style=fighting_style,
            traits=traits
        )
        
        fighter._nickname = data.get("nickname")
        fighter._natural_weight = data.get("natural_weight", fighter._natural_weight)
        
        rec = data["record"]
        fighter._record = FightRecord(
            wins=rec["wins"],
            losses=rec["losses"],
            draws=rec.get("draws", 0),
            no_contests=rec.get("no_contests", 0)
        )
        
        fighter._status = FighterStatus[data["status"]]
        fighter._rank = data.get("rank")
        fighter._is_champion = data.get("is_champion", False)
        fighter._camp_id = data.get("camp_id")
        fighter._popularity = data.get("popularity", 10)
        fighter._career_earnings = data.get("career_earnings", 0)
        fighter._ko_wins = data.get("ko_wins", 0)
        fighter._submission_wins = data.get("submission_wins", 0)
        fighter._decision_wins = data.get("decision_wins", 0)
        fighter._ko_losses = data.get("ko_losses", 0)
        fighter._fatigue = data.get("fatigue", 0)
        fighter._morale = data.get("morale", 75)
        fighter._current_win_streak = data.get("win_streak", 0)
        fighter._current_loss_streak = data.get("loss_streak", 0)
        
        return fighter
    
    def __repr__(self) -> str:
        return f"Fighter({self.full_name}, {self._weight_class.value}, {self.record_string})"
    
    def __str__(self) -> str:
        return f"{self.display_name} ({self._weight_class.value}, {self.record_string})"


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_fighter(
    first_name: str,
    last_name: str,
    weight_class: WeightClass,
    birth_date: GameDate,
    nationality: str = "USA",
    attributes: Optional[Dict[str, int]] = None,
    fighting_style: Optional[FightingStyle] = None,
    traits: Optional[List[str]] = None
) -> Fighter:
    """
    Factory function to create a new fighter.
    
    Args:
        first_name: Fighter's first name
        last_name: Fighter's last name
        weight_class: Primary weight class
        birth_date: Date of birth
        nationality: Country of origin
        attributes: Optional dict of attribute values
        fighting_style: Combat archetype (defaults to BALANCED)
        traits: Special abilities (defaults to empty list)
    
    Returns:
        New Fighter instance
    """
    attr_set = None
    if attributes:
        attr_set = AttributeSet(**attributes)
    
    return Fighter(
        first_name=first_name,
        last_name=last_name,
        weight_class=weight_class,
        birth_date=birth_date,
        nationality=nationality,
        attributes=attr_set,
        fighting_style=fighting_style,
        traits=traits
    )
