# interface/cli_data.py
# Data classes for Cage Dynasty CLI
# Lines: 401

"""
Data classes used by the CLI for managing game state.

This module contains the expanded data structures that the CLI uses
to track fighters, fights, events, news, and offers.
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field


# ============================================================================
# FIGHTER DATA
# ============================================================================

@dataclass
class FighterFullData:
    """Complete fighter data with all attributes.
    
    This is the CLI's local representation of a fighter with all
    attributes expanded for display and manipulation.
    
    Updated to 17-attribute system:
    - Physical (5): strength, speed, cardio, chin, recovery
    - Striking (4): boxing, kicks, clinch_striking, striking_defense
    - Grappling (5): takedowns, takedown_defense, top_control, submissions, guard
    - Mental (3): heart, fight_iq, composure
    """
    
    # Identity
    fighter_id: str
    name: str
    nickname: Optional[str] = None
    
    # Bio
    country: str = "United States"
    age: int = 25
    height_cm: int = 178
    weight_lbs: float = 155.0
    reach_cm: int = 180
    
    # Classification
    weight_class: str = "Lightweight"
    camp_id: Optional[str] = None
    contract_id: Optional[str] = None
    is_champion: bool = False
    is_active: bool = True
    
    # Style
    fighting_style: str = "MMA Hybrid"
    build_type: str = "Athletic"
    personality: str = "Methodical"
    
    # Physical Attributes (5)
    strength: int = 50
    speed: int = 50
    cardio: int = 50
    chin: int = 50
    recovery: int = 50  # NEW: Between-round recovery
    
    # Striking Attributes (4)
    boxing: int = 50
    kicks: int = 50
    clinch_striking: int = 50
    striking_defense: int = 50
    
    # Grappling Attributes (5) - UPDATED
    takedowns: int = 50       # Getting fight to ground
    takedown_defense: int = 50
    top_control: int = 50     # Holding position, GnP, passing
    submissions: int = 50     # Finishing ability
    guard: int = 50           # Sweeps, escapes, sub defense
    
    # Mental Attributes (3)
    heart: int = 50
    fight_iq: int = 50
    composure: int = 50
    
    # Record
    wins: int = 0
    losses: int = 0
    draws: int = 0
    ko_wins: int = 0
    sub_wins: int = 0
    dec_wins: int = 0
    ko_losses: int = 0
    sub_losses: int = 0
    
    # Career stats
    title_defenses: int = 0
    fights_total: int = 0
    win_streak: int = 0
    lose_streak: int = 0
    
    # Condition tracking
    fatigue: int = 0              # Current fatigue level (0-100)
    last_fought_week: int = 0     # Week number of last fight
    lost_last_fight: bool = False # For training motivation bonuses
    
    # Development tracking
    potential_ceiling: int = 75   # Maximum potential
    
    # Traits (special abilities/characteristics)
    traits: List[str] = field(default_factory=list)
    
    # Active injuries
    injuries: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def overall_rating(self) -> int:
        """Calculate overall rating from 17 attributes."""
        striking = (self.boxing * 2 + self.kicks + self.clinch_striking + self.striking_defense) // 5
        grappling = (self.takedowns + self.top_control + self.submissions + self.guard + self.takedown_defense) // 5
        physical = (self.strength + self.speed + self.cardio + self.chin + self.recovery) // 5
        mental = (self.heart + self.fight_iq + self.composure) // 3
        return (striking + grappling + physical + mental) // 4
    
    @property
    def striking_rating(self) -> int:
        """Calculate striking overall."""
        return (self.boxing * 2 + self.kicks + self.clinch_striking + self.striking_defense) // 5
    
    @property
    def grappling_rating(self) -> int:
        """Calculate grappling overall."""
        return (self.takedowns + self.top_control + self.submissions + self.guard + self.takedown_defense) // 5
    
    @property
    def physical_rating(self) -> int:
        """Calculate physical overall."""
        return (self.strength + self.speed + self.cardio + self.chin + self.recovery) // 5
    
    @property
    def mental_rating(self) -> int:
        """Calculate mental overall."""
        return (self.heart + self.fight_iq + self.composure) // 3
    
    @property
    def record(self) -> str:
        """Format record as string."""
        if self.draws:
            return f"{self.wins}-{self.losses}-{self.draws}"
        return f"{self.wins}-{self.losses}"
    
    @property
    def height_display(self) -> str:
        """Convert cm to feet/inches."""
        total_inches = self.height_cm / 2.54
        feet = int(total_inches // 12)
        inches = int(total_inches % 12)
        return f"{feet}'{inches}\""
    
    @property
    def reach_display(self) -> str:
        """Convert cm to inches."""
        return f"{int(self.reach_cm / 2.54)}\""
    
    @property
    def finish_rate(self) -> float:
        """Calculate finish rate."""
        if self.wins == 0:
            return 0.0
        return (self.ko_wins + self.sub_wins) / self.wins
    
    @property
    def is_injured(self) -> bool:
        """Check if fighter has active injuries."""
        return len(self.injuries) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            "nickname": self.nickname,
            "country": self.country,
            "age": self.age,
            "height_cm": self.height_cm,
            "weight_lbs": self.weight_lbs,
            "reach_cm": self.reach_cm,
            "weight_class": self.weight_class,
            "camp_id": self.camp_id,
            "contract_id": self.contract_id,
            "is_champion": self.is_champion,
            "is_active": self.is_active,
            "fighting_style": self.fighting_style,
            "build_type": self.build_type,
            "personality": self.personality,
            # Physical (5)
            "strength": self.strength,
            "speed": self.speed,
            "cardio": self.cardio,
            "chin": self.chin,
            "recovery": self.recovery,
            # Striking (4)
            "boxing": self.boxing,
            "kicks": self.kicks,
            "clinch_striking": self.clinch_striking,
            "striking_defense": self.striking_defense,
            # Grappling (5)
            "takedowns": self.takedowns,
            "takedown_defense": self.takedown_defense,
            "top_control": self.top_control,
            "submissions": self.submissions,
            "guard": self.guard,
            # Mental (3)
            "heart": self.heart,
            "fight_iq": self.fight_iq,
            "composure": self.composure,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "ko_wins": self.ko_wins,
            "sub_wins": self.sub_wins,
            "dec_wins": self.dec_wins,
            "ko_losses": self.ko_losses,
            "sub_losses": self.sub_losses,
            "title_defenses": self.title_defenses,
            "fights_total": self.fights_total,
            "win_streak": self.win_streak,
            "lose_streak": self.lose_streak,
            # Condition tracking
            "fatigue": self.fatigue,
            "last_fought_week": self.last_fought_week,
            "lost_last_fight": self.lost_last_fight,
            # Development
            "potential_ceiling": self.potential_ceiling,
            "traits": self.traits,
            "injuries": self.injuries,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FighterFullData":
        """Deserialize from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================================================
# FIGHT DATA
# ============================================================================

@dataclass
class FightResult:
    """Result of a completed fight.
    
    Stores all information about a completed fight including
    participants, outcome, stats, and commentary.
    """
    
    fight_id: str
    event_id: str
    event_name: str
    week: int
    
    # Fighters
    fighter1_id: str
    fighter1_name: str
    fighter2_id: str
    fighter2_name: str
    
    # Result
    winner_id: str
    winner_name: str
    loser_id: str
    loser_name: str
    method: str  # KO, TKO, SUB, DEC, DRAW
    round_finished: int
    time_finished: str = "5:00"
    
    # Fight details
    weight_class: str = ""
    is_title_fight: bool = False
    is_main_event: bool = False
    rounds_scheduled: int = 3
    
    # Stats summary
    fighter1_strikes: int = 0
    fighter2_strikes: int = 0
    fighter1_takedowns: int = 0
    fighter2_takedowns: int = 0
    fighter1_sub_attempts: int = 0
    fighter2_sub_attempts: int = 0
    
    # Commentary summary
    fight_summary: str = ""
    key_moments: List[str] = field(default_factory=list)
    
    # Full fight data (for replay)
    full_narrative: str = ""
    round_by_round: List[str] = field(default_factory=list)
    round_summaries: List[str] = field(default_factory=list)
    judge_scores: List[Tuple[int, int]] = field(default_factory=list)
    fight_of_night: bool = False
    performance_bonus: bool = False
    
    @property
    def is_finish(self) -> bool:
        """Check if fight ended in a finish."""
        return self.method in ("KO", "TKO", "SUB")
    
    @property
    def is_decision(self) -> bool:
        """Check if fight went to decision."""
        return self.method in ("DEC", "UD", "SD", "MD")
    
    @property
    def headline(self) -> str:
        """Generate headline for this fight."""
        if self.method == "DRAW":
            return f"{self.fighter1_name} vs {self.fighter2_name} ends in DRAW"
        
        method_display = {
            "KO": "KO",
            "TKO": "TKO",
            "SUB": "Submission",
            "DEC": "Decision",
            "UD": "Unanimous Decision",
            "SD": "Split Decision",
            "MD": "Majority Decision",
        }.get(self.method, self.method)
        
        if self.is_finish:
            return f"{self.winner_name} defeats {self.loser_name} by {method_display} (R{self.round_finished})"
        return f"{self.winner_name} defeats {self.loser_name} by {method_display}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "fight_id": self.fight_id,
            "event_id": self.event_id,
            "event_name": self.event_name,
            "week": self.week,
            "fighter1_id": self.fighter1_id,
            "fighter1_name": self.fighter1_name,
            "fighter2_id": self.fighter2_id,
            "fighter2_name": self.fighter2_name,
            "winner_id": self.winner_id,
            "winner_name": self.winner_name,
            "loser_id": self.loser_id,
            "loser_name": self.loser_name,
            "method": self.method,
            "round_finished": self.round_finished,
            "time_finished": self.time_finished,
            "weight_class": self.weight_class,
            "is_title_fight": self.is_title_fight,
            "is_main_event": self.is_main_event,
            "rounds_scheduled": self.rounds_scheduled,
            "fighter1_strikes": self.fighter1_strikes,
            "fighter2_strikes": self.fighter2_strikes,
            "fighter1_takedowns": self.fighter1_takedowns,
            "fighter2_takedowns": self.fighter2_takedowns,
            "fighter1_sub_attempts": self.fighter1_sub_attempts,
            "fighter2_sub_attempts": self.fighter2_sub_attempts,
            "fight_summary": self.fight_summary,
            "key_moments": self.key_moments,
            "full_narrative": self.full_narrative,
            "round_by_round": self.round_by_round,
            "round_summaries": self.round_summaries,
            "judge_scores": self.judge_scores,
            "fight_of_night": self.fight_of_night,
            "performance_bonus": self.performance_bonus,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FightResult":
        """Deserialize from dictionary."""
        # Handle judge_scores conversion from list of lists to list of tuples
        if "judge_scores" in data and data["judge_scores"]:
            data["judge_scores"] = [tuple(s) for s in data["judge_scores"]]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================================================
# EVENT DATA
# ============================================================================

@dataclass
class CompletedEvent:
    """A completed fight event/card.
    
    Contains all fights from a single event and aggregate statistics.
    """
    
    event_id: str
    event_name: str
    week: int
    fights: List[FightResult] = field(default_factory=list)
    
    def add_fight(self, fight: FightResult) -> None:
        """Add a fight to this event."""
        self.fights.append(fight)
    
    @property
    def total_fights(self) -> int:
        """Total number of fights."""
        return len(self.fights)
    
    @property
    def knockouts(self) -> int:
        """Count of KO/TKO finishes."""
        return sum(1 for f in self.fights if f.method in ("KO", "TKO"))
    
    @property
    def submissions(self) -> int:
        """Count of submission finishes."""
        return sum(1 for f in self.fights if f.method == "SUB")
    
    @property
    def decisions(self) -> int:
        """Count of decisions."""
        return sum(1 for f in self.fights if f.method in ("DEC", "UD", "SD", "MD"))
    
    @property
    def main_event(self) -> Optional[FightResult]:
        """Get the main event fight."""
        for fight in reversed(self.fights):
            if fight.is_main_event:
                return fight
        return self.fights[-1] if self.fights else None
    
    @property
    def title_fights(self) -> List[FightResult]:
        """Get all title fights from this event."""
        return [f for f in self.fights if f.is_title_fight]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_id": self.event_id,
            "event_name": self.event_name,
            "week": self.week,
            "fights": [f.to_dict() for f in self.fights],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompletedEvent":
        """Deserialize from dictionary."""
        fights = [FightResult.from_dict(f) for f in data.get("fights", [])]
        return cls(
            event_id=data["event_id"],
            event_name=data["event_name"],
            week=data["week"],
            fights=fights,
        )


# ============================================================================
# NEWS DATA
# ============================================================================

@dataclass
class NewsItem:
    """A news item for the news feed.
    
    Categories: fight, title, injury, signing, retirement, general
    """
    
    headline: str
    category: str = "general"
    week: int = 0
    details: str = ""
    fighter_ids: List[str] = field(default_factory=list)
    
    @property
    def icon(self) -> str:
        """Get display icon for this news category."""
        icons = {
            "fight": "[FIGHT]",
            "title": "[TITLE]",
            "injury": "[INJ]",
            "signing": "[SIGN]",
            "retirement": "[RET]",
            "general": "[NEWS]",
        }
        return icons.get(self.category, "[NEWS]")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "headline": self.headline,
            "category": self.category,
            "week": self.week,
            "details": self.details,
            "fighter_ids": self.fighter_ids,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsItem":
        """Deserialize from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================================================
# FIGHT OFFERS
# ============================================================================

@dataclass
class FightOffer:
    """An offer for a fight.
    
    Represents a potential fight that can be accepted or declined.
    """
    
    offer_id: str
    fighter_id: str
    fighter_name: str
    opponent_id: str
    opponent_name: str
    weight_class: str
    is_title_fight: bool = False
    purse: int = 10000
    weeks_notice: int = 8
    event_name: str = "DFC Fight Night"
    
    # Opponent info for display
    opponent_record: str = "0-0"
    opponent_rating: int = 50
    opponent_rank: Optional[int] = None
    
    @property
    def is_short_notice(self) -> bool:
        """Check if this is a short notice fight (< 4 weeks)."""
        return self.weeks_notice < 4
    
    @property
    def summary(self) -> str:
        """Generate a summary string."""
        title_tag = " [TITLE]" if self.is_title_fight else ""
        rank_str = f"#{self.opponent_rank}" if self.opponent_rank else "Unranked"
        return f"vs {self.opponent_name} ({self.opponent_record}) - {rank_str}{title_tag}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "offer_id": self.offer_id,
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "opponent_id": self.opponent_id,
            "opponent_name": self.opponent_name,
            "weight_class": self.weight_class,
            "is_title_fight": self.is_title_fight,
            "purse": self.purse,
            "weeks_notice": self.weeks_notice,
            "event_name": self.event_name,
            "opponent_record": self.opponent_record,
            "opponent_rating": self.opponent_rating,
            "opponent_rank": self.opponent_rank,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FightOffer":
        """Deserialize from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "FighterFullData",
    "FightResult",
    "CompletedEvent",
    "NewsItem",
    "FightOffer",
]
