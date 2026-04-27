# narrative/rivalry.py
# Module 22: Rivalry System
# Lines: ~750
#
# Detects, tracks, and evolves rivalries between fighters based on
# fight history, interactions, and narrative triggers.

"""
Cage Dynasty - Rivalry System

Creates emergent narratives through dynamic rivalry detection and tracking.
Rivalries form organically from:
- Close/controversial fights
- Title disputes
- Trash talk and callouts
- Gym defections
- Regional/national pride

Usage:
    from narrative.rivalry import (
        RivalrySystem,
        RivalryType,
        detect_rivalry_from_fight,
        get_rivalry_intensity_description,
    )
    
    # After a fight
    rivalry = detect_rivalry_from_fight(fight_result, fighter1, fighter2)
    
    # Check existing rivalry
    rivalry = system.get_rivalry(fighter1_id, fighter2_id)
    if rivalry and rivalry.is_heated():
        print(f"Bad blood between these two!")
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from datetime import datetime

from core.events import emit


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class RivalryType(Enum):
    """Types of rivalries that can form"""
    COMPETITIVE = "competitive"      # Evenly matched, respect-based
    BAD_BLOOD = "bad_blood"          # Personal animosity
    TITLE_DISPUTE = "title_dispute"  # Championship contention
    GYM_WAR = "gym_war"              # Former teammates
    NATIONAL_PRIDE = "national_pride"  # Country vs country
    STYLE_CLASH = "style_clash"      # Striker vs grappler narratives
    GENERATIONAL = "generational"    # Old guard vs new blood
    REVENGE = "revenge"              # One fighter seeking payback


class RivalryIntensity(Enum):
    """Intensity levels of rivalries"""
    BUDDING = 1       # Just starting, minor tension
    NOTABLE = 2       # Fans are aware, some heat
    HEATED = 3        # Significant animosity
    FIERCE = 4        # Major rivalry, high stakes
    LEGENDARY = 5     # All-time great rivalry


class HeatStage(Enum):
    """Heat stages for fight effects - maps to intensity but focused on fight impact."""
    NEUTRAL = "neutral"       # 0-20: Normal fight, no special effects
    TENSION = "tension"       # 21-40: Slight edge, minor effects
    BAD_BLOOD = "bad_blood"   # 41-60: Personal, noticeable effects
    HEATED = "heated"         # 61-80: Significant animosity, major effects
    WAR = "war"               # 81-100: All-out war, maximum effects


# Intensity thresholds (rivalry score ranges)
INTENSITY_THRESHOLDS: Dict[RivalryIntensity, Tuple[int, int]] = {
    RivalryIntensity.BUDDING: (10, 29),
    RivalryIntensity.NOTABLE: (30, 49),
    RivalryIntensity.HEATED: (50, 69),
    RivalryIntensity.FIERCE: (70, 89),
    RivalryIntensity.LEGENDARY: (90, 100),
}

# Score modifiers for different events
RIVALRY_SCORE_MODIFIERS: Dict[str, int] = {
    # Fight outcomes
    "close_decision": 15,
    "split_decision": 20,
    "controversial_stoppage": 25,
    "knockout_loss": 10,
    "submission_loss": 8,
    "dominant_victory": 5,
    
    # Fight context
    "title_fight": 15,
    "rematch": 10,
    "trilogy": 20,
    "main_event": 5,
    
    # Interactions
    "trash_talk": 10,
    "callout": 8,
    "physical_altercation": 30,
    "press_conference_incident": 20,
    "social_media_beef": 5,
    
    # Background
    "same_gym_history": 15,
    "gym_defection": 25,
    "same_country": 5,
    "rival_countries": 10,
    "coach_conflict": 15,
    
    # Career context
    "title_holder_challenger": 10,
    "ranking_dispute": 8,
    "both_undefeated": 15,
    "win_streak_collision": 10,
}

# Decay rate per month of inactivity
RIVALRY_DECAY_PER_MONTH: int = 2

# Minimum score to maintain a rivalry
MIN_RIVALRY_SCORE: int = 10

# Heat stage thresholds (score ranges)
HEAT_STAGE_THRESHOLDS: Dict[HeatStage, Tuple[int, int]] = {
    HeatStage.NEUTRAL: (0, 20),
    HeatStage.TENSION: (21, 40),
    HeatStage.BAD_BLOOD: (41, 60),
    HeatStage.HEATED: (61, 80),
    HeatStage.WAR: (81, 100),
}

# Fight modifiers by heat stage
# (damage_multiplier, composure_penalty, finish_bonus, aggression_bonus)
HEAT_FIGHT_MODIFIERS: Dict[HeatStage, Tuple[float, int, float, float]] = {
    HeatStage.NEUTRAL: (1.00, 0, 0.00, 0.00),
    HeatStage.TENSION: (1.05, 3, 0.05, 0.05),
    HeatStage.BAD_BLOOD: (1.10, 5, 0.10, 0.10),
    HeatStage.HEATED: (1.15, 8, 0.15, 0.15),
    HeatStage.WAR: (1.20, 12, 0.20, 0.20),
}

# Additional heat sources (beyond existing RIVALRY_SCORE_MODIFIERS)
HEAT_SOURCE_MODIFIERS: Dict[str, int] = {
    "snubbed_challenge": 15,         # Player withdrew from accepted fight
    "callout_ignored": 10,           # Ignored a callout
    "ended_streak": 12,              # One ended the other's win streak
    "chasing_same_title": 3,         # Both pursuing same championship (per week)
    "controversial_judging": 18,     # Robbery decision
    "post_fight_brawl": 30,          # Physical altercation after fight
    "interview_disrespect": 8,       # Disrespectful in interview
    "social_media_callout": 5,       # Called out on social media
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RivalryEvent:
    """
    A single event that contributes to a rivalry.
    
    Attributes:
        event_type: Type of event (fight, callout, incident, etc.)
        description: Human-readable description
        score_change: How much this affected rivalry score
        date: When the event occurred
        fight_id: Associated fight ID if applicable
    """
    event_type: str
    description: str
    score_change: int
    date: str  # ISO format
    fight_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "description": self.description,
            "score_change": self.score_change,
            "date": self.date,
            "fight_id": self.fight_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RivalryEvent":
        return cls(
            event_type=data["event_type"],
            description=data["description"],
            score_change=data["score_change"],
            date=data["date"],
            fight_id=data.get("fight_id"),
        )


@dataclass
class Rivalry:
    """
    Represents a rivalry between two fighters.
    
    Attributes:
        fighter1_id: First fighter's ID
        fighter2_id: Second fighter's ID
        fighter1_name: First fighter's name (for display)
        fighter2_name: Second fighter's name (for display)
        rivalry_type: Primary type of rivalry
        score: Current rivalry intensity score (0-100)
        fights: Number of fights between them
        fighter1_wins: Wins by fighter 1
        fighter2_wins: Wins by fighter 2
        draws: Number of draws
        history: List of rivalry events
        started_date: When rivalry began
        last_updated: Last activity date
        is_active: Whether rivalry is currently active
    """
    fighter1_id: str
    fighter2_id: str
    fighter1_name: str
    fighter2_name: str
    rivalry_type: RivalryType
    score: int = 0
    fights: int = 0
    fighter1_wins: int = 0
    fighter2_wins: int = 0
    draws: int = 0
    history: List[RivalryEvent] = field(default_factory=list)
    started_date: str = ""
    last_updated: str = ""
    is_active: bool = True
    
    # Additional tracking
    secondary_types: List[RivalryType] = field(default_factory=list)
    peak_score: int = 0
    total_events: int = 0
    
    def __post_init__(self):
        if not self.started_date:
            self.started_date = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = self.started_date
        self.peak_score = max(self.peak_score, self.score)
    
    @property
    def intensity(self) -> RivalryIntensity:
        """Get current intensity level"""
        for intensity, (min_score, max_score) in INTENSITY_THRESHOLDS.items():
            if min_score <= self.score <= max_score:
                return intensity
        if self.score < 10:
            return RivalryIntensity.BUDDING
        return RivalryIntensity.LEGENDARY
    
    @property
    def head_to_head(self) -> str:
        """Get head-to-head record string"""
        return f"{self.fighter1_wins}-{self.fighter2_wins}-{self.draws}"
    
    @property
    def series_leader(self) -> Optional[str]:
        """Get ID of fighter leading the series"""
        if self.fighter1_wins > self.fighter2_wins:
            return self.fighter1_id
        elif self.fighter2_wins > self.fighter1_wins:
            return self.fighter2_id
        return None
    
    @property
    def is_tied(self) -> bool:
        """Check if series is tied"""
        return self.fighter1_wins == self.fighter2_wins
    
    def is_heated(self) -> bool:
        """Check if rivalry is at heated level or above"""
        return self.score >= 50
    
    def is_legendary(self) -> bool:
        """Check if rivalry has reached legendary status"""
        return self.score >= 90 or self.peak_score >= 90
    
    def add_score(self, amount: int, event_type: str, description: str, 
                  fight_id: Optional[str] = None) -> None:
        """Add to rivalry score with event tracking"""
        self.score = min(100, max(0, self.score + amount))
        self.peak_score = max(self.peak_score, self.score)
        self.last_updated = datetime.now().isoformat()
        self.total_events += 1
        
        event = RivalryEvent(
            event_type=event_type,
            description=description,
            score_change=amount,
            date=self.last_updated,
            fight_id=fight_id,
        )
        self.history.append(event)
    
    def record_fight(self, winner_id: Optional[str], is_draw: bool = False) -> None:
        """Record a fight result"""
        self.fights += 1
        
        if is_draw:
            self.draws += 1
        elif winner_id == self.fighter1_id:
            self.fighter1_wins += 1
        elif winner_id == self.fighter2_id:
            self.fighter2_wins += 1
    
    def apply_decay(self, months: int = 1) -> None:
        """Apply time-based decay to rivalry score"""
        decay = RIVALRY_DECAY_PER_MONTH * months
        self.score = max(0, self.score - decay)
        
        # Deactivate if score too low
        if self.score < MIN_RIVALRY_SCORE:
            self.is_active = False
    
    def add_secondary_type(self, rivalry_type: RivalryType) -> None:
        """Add a secondary rivalry type"""
        if rivalry_type != self.rivalry_type and rivalry_type not in self.secondary_types:
            self.secondary_types.append(rivalry_type)
    
    def get_narrative_summary(self) -> str:
        """Generate a narrative summary of the rivalry"""
        intensity_desc = {
            RivalryIntensity.BUDDING: "budding",
            RivalryIntensity.NOTABLE: "notable",
            RivalryIntensity.HEATED: "heated",
            RivalryIntensity.FIERCE: "fierce",
            RivalryIntensity.LEGENDARY: "legendary",
        }
        
        type_desc = {
            RivalryType.COMPETITIVE: "competitive rivalry",
            RivalryType.BAD_BLOOD: "bitter feud",
            RivalryType.TITLE_DISPUTE: "title rivalry",
            RivalryType.GYM_WAR: "gym war",
            RivalryType.NATIONAL_PRIDE: "national pride clash",
            RivalryType.STYLE_CLASH: "style matchup rivalry",
            RivalryType.GENERATIONAL: "generational clash",
            RivalryType.REVENGE: "revenge quest",
        }
        
        summary = f"A {intensity_desc[self.intensity]} {type_desc[self.rivalry_type]} "
        summary += f"between {self.fighter1_name} and {self.fighter2_name}. "
        
        if self.fights > 0:
            summary += f"Head-to-head: {self.head_to_head}. "
            
            if self.fights >= 3:
                summary += "This trilogy has captivated fans. "
            elif self.fights == 2:
                summary += "Their rematch added fuel to the fire. "
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "fighter1_id": self.fighter1_id,
            "fighter2_id": self.fighter2_id,
            "fighter1_name": self.fighter1_name,
            "fighter2_name": self.fighter2_name,
            "rivalry_type": self.rivalry_type.value,
            "score": self.score,
            "fights": self.fights,
            "fighter1_wins": self.fighter1_wins,
            "fighter2_wins": self.fighter2_wins,
            "draws": self.draws,
            "history": [e.to_dict() for e in self.history],
            "started_date": self.started_date,
            "last_updated": self.last_updated,
            "is_active": self.is_active,
            "secondary_types": [t.value for t in self.secondary_types],
            "peak_score": self.peak_score,
            "total_events": self.total_events,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rivalry":
        """Deserialize from dictionary"""
        rivalry = cls(
            fighter1_id=data["fighter1_id"],
            fighter2_id=data["fighter2_id"],
            fighter1_name=data["fighter1_name"],
            fighter2_name=data["fighter2_name"],
            rivalry_type=RivalryType(data["rivalry_type"]),
            score=data["score"],
            fights=data["fights"],
            fighter1_wins=data["fighter1_wins"],
            fighter2_wins=data["fighter2_wins"],
            draws=data["draws"],
            started_date=data["started_date"],
            last_updated=data["last_updated"],
            is_active=data["is_active"],
            peak_score=data.get("peak_score", data["score"]),
            total_events=data.get("total_events", 0),
        )
        
        rivalry.history = [RivalryEvent.from_dict(e) for e in data.get("history", [])]
        rivalry.secondary_types = [RivalryType(t) for t in data.get("secondary_types", [])]
        
        return rivalry


# ============================================================================
# RIVALRY DETECTION
# ============================================================================

@dataclass
class FightContext:
    """Context about a fight for rivalry detection"""
    fight_id: str
    fighter1_id: str
    fighter2_id: str
    fighter1_name: str
    fighter2_name: str
    winner_id: Optional[str]
    method: str  # "KO", "TKO", "SUB", "DEC", "SPLIT", "DRAW"
    is_title_fight: bool = False
    is_main_event: bool = False
    round_ended: int = 3
    total_rounds: int = 3
    fighter1_knockdowns: int = 0
    fighter2_knockdowns: int = 0
    was_close: bool = False
    was_controversial: bool = False
    # Optional background
    fighter1_country: str = ""
    fighter2_country: str = ""
    fighter1_camp: str = ""
    fighter2_camp: str = ""
    fighter1_style: str = ""
    fighter2_style: str = ""


def detect_rivalry_triggers(context: FightContext) -> List[Tuple[str, int, str]]:
    """
    Detect rivalry triggers from a fight.
    
    Returns:
        List of (event_type, score_modifier, description) tuples
    """
    triggers: List[Tuple[str, int, str]] = []
    
    # Fight outcome triggers
    if context.method == "SPLIT":
        triggers.append((
            "split_decision",
            RIVALRY_SCORE_MODIFIERS["split_decision"],
            "Split decision leaves questions unanswered"
        ))
    elif context.method == "DEC" and context.was_close:
        triggers.append((
            "close_decision",
            RIVALRY_SCORE_MODIFIERS["close_decision"],
            "Close decision could have gone either way"
        ))
    
    if context.was_controversial:
        triggers.append((
            "controversial_stoppage",
            RIVALRY_SCORE_MODIFIERS["controversial_stoppage"],
            "Controversial finish demands a rematch"
        ))
    
    # Context triggers
    if context.is_title_fight:
        triggers.append((
            "title_fight",
            RIVALRY_SCORE_MODIFIERS["title_fight"],
            "Championship implications raise the stakes"
        ))
    
    if context.is_main_event:
        triggers.append((
            "main_event",
            RIVALRY_SCORE_MODIFIERS["main_event"],
            "Main event spotlight intensifies the rivalry"
        ))
    
    # Finish type triggers
    if context.method in ["KO", "TKO"]:
        # Knockout creates motivation for revenge
        triggers.append((
            "knockout_loss",
            RIVALRY_SCORE_MODIFIERS["knockout_loss"],
            "Devastating knockout loss fuels revenge"
        ))
    elif context.method == "SUB":
        triggers.append((
            "submission_loss",
            RIVALRY_SCORE_MODIFIERS["submission_loss"],
            "Submission loss stings the ego"
        ))
    
    # Back-and-forth action
    if context.fighter1_knockdowns > 0 and context.fighter2_knockdowns > 0:
        triggers.append((
            "close_decision",
            10,
            "Both fighters were hurt in a war"
        ))
    
    # Style clash potential
    if context.fighter1_style and context.fighter2_style:
        if _is_style_clash(context.fighter1_style, context.fighter2_style):
            triggers.append((
                "style_clash",
                8,
                f"{context.fighter1_style} vs {context.fighter2_style} creates narrative"
            ))
    
    # Country rivalry potential
    if context.fighter1_country and context.fighter2_country:
        if _are_rival_countries(context.fighter1_country, context.fighter2_country):
            triggers.append((
                "rival_countries",
                RIVALRY_SCORE_MODIFIERS["rival_countries"],
                "National pride on the line"
            ))
    
    return triggers


def _is_style_clash(style1: str, style2: str) -> bool:
    """Check if two styles create a narrative clash"""
    striking_styles = {"boxing", "kickboxing", "muay_thai", "karate"}
    grappling_styles = {"wrestling", "bjj", "sambo", "judo"}
    
    style1_lower = style1.lower().replace(" ", "_")
    style2_lower = style2.lower().replace(" ", "_")
    
    is_striker1 = style1_lower in striking_styles
    is_grappler1 = style1_lower in grappling_styles
    is_striker2 = style2_lower in striking_styles
    is_grappler2 = style2_lower in grappling_styles
    
    return (is_striker1 and is_grappler2) or (is_grappler1 and is_striker2)


def _are_rival_countries(country1: str, country2: str) -> bool:
    """Check if two countries have a natural sports rivalry"""
    rivalries = [
        {"United States", "Russia"},
        {"United States", "Mexico"},
        {"Brazil", "United States"},
        {"Ireland", "United Kingdom"},
        {"Russia", "Ukraine"},
        {"Japan", "South Korea"},
        {"Brazil", "Argentina"},
    ]
    
    pair = {country1, country2}
    return pair in rivalries


def determine_rivalry_type(
    context: FightContext,
    existing_rivalry: Optional[Rivalry] = None
) -> RivalryType:
    """Determine the primary type of rivalry based on context"""
    
    # Title fights create title disputes
    if context.is_title_fight:
        return RivalryType.TITLE_DISPUTE
    
    # Controversial results create bad blood
    if context.was_controversial or context.method == "SPLIT":
        return RivalryType.BAD_BLOOD
    
    # Gym wars
    if context.fighter1_camp and context.fighter1_camp == context.fighter2_camp:
        return RivalryType.GYM_WAR
    
    # Country rivalries
    if context.fighter1_country and context.fighter2_country:
        if _are_rival_countries(context.fighter1_country, context.fighter2_country):
            return RivalryType.NATIONAL_PRIDE
    
    # Style clashes
    if context.fighter1_style and context.fighter2_style:
        if _is_style_clash(context.fighter1_style, context.fighter2_style):
            return RivalryType.STYLE_CLASH
    
    # Existing rivalry continues
    if existing_rivalry:
        return existing_rivalry.rivalry_type
    
    # Default to competitive
    return RivalryType.COMPETITIVE


def detect_rivalry_from_fight(
    context: FightContext,
    existing_rivalry: Optional[Rivalry] = None
) -> Tuple[Optional[Rivalry], List[RivalryEvent]]:
    """
    Detect or update a rivalry based on a fight result.
    
    Args:
        context: Fight context information
        existing_rivalry: Existing rivalry if any
        
    Returns:
        Tuple of (Rivalry or None, list of new events)
    """
    # Get triggers from this fight
    triggers = detect_rivalry_triggers(context)
    
    # Calculate total score from triggers
    total_score = sum(score for _, score, _ in triggers)
    
    # Need minimum score to create/update rivalry
    if total_score < 10 and existing_rivalry is None:
        return None, []
    
    # Create new rivalry or update existing
    if existing_rivalry:
        rivalry = existing_rivalry
    else:
        rivalry_type = determine_rivalry_type(context, None)
        rivalry = Rivalry(
            fighter1_id=context.fighter1_id,
            fighter2_id=context.fighter2_id,
            fighter1_name=context.fighter1_name,
            fighter2_name=context.fighter2_name,
            rivalry_type=rivalry_type,
        )
    
    # Record the fight
    is_draw = context.winner_id is None and context.method == "DRAW"
    rivalry.record_fight(context.winner_id, is_draw)
    
    # Check for rematch/trilogy bonus
    if rivalry.fights == 2:
        triggers.append((
            "rematch",
            RIVALRY_SCORE_MODIFIERS["rematch"],
            "The rematch intensifies the rivalry"
        ))
    elif rivalry.fights >= 3:
        triggers.append((
            "trilogy",
            RIVALRY_SCORE_MODIFIERS["trilogy"],
            "Trilogy status cemented"
        ))
    
    # Apply all triggers
    events = []
    for event_type, score, description in triggers:
        rivalry.add_score(score, event_type, description, context.fight_id)
        events.append(rivalry.history[-1])
    
    # Emit event
    emit("rivalry_updated", {
        "fighter1_id": rivalry.fighter1_id,
        "fighter2_id": rivalry.fighter2_id,
        "score": rivalry.score,
        "intensity": rivalry.intensity.name,
    })
    
    return rivalry, events


# ============================================================================
# RIVALRY SYSTEM
# ============================================================================

class RivalrySystem:
    """
    Central rivalry management system.
    
    Tracks all rivalries, detects new ones, and manages evolution over time.
    """
    
    def __init__(self):
        # Store rivalries by pair key (sorted IDs)
        self._rivalries: Dict[str, Rivalry] = {}
        
        # Fighter lookup (fighter_id -> list of rivalry keys)
        self._fighter_rivalries: Dict[str, List[str]] = {}
        
        # Stats
        self.total_rivalries_created: int = 0
        self.total_events_recorded: int = 0
    
    def _get_pair_key(self, fighter1_id: str, fighter2_id: str) -> str:
        """Get canonical key for a fighter pair"""
        return ":".join(sorted([fighter1_id, fighter2_id]))
    
    def get_rivalry(self, fighter1_id: str, fighter2_id: str) -> Optional[Rivalry]:
        """Get rivalry between two fighters"""
        key = self._get_pair_key(fighter1_id, fighter2_id)
        return self._rivalries.get(key)
    
    def get_fighter_rivalries(self, fighter_id: str) -> List[Rivalry]:
        """Get all rivalries for a fighter"""
        keys = self._fighter_rivalries.get(fighter_id, [])
        return [self._rivalries[k] for k in keys if k in self._rivalries]
    
    def get_active_rivalries(self, fighter_id: str) -> List[Rivalry]:
        """Get active rivalries for a fighter"""
        return [r for r in self.get_fighter_rivalries(fighter_id) if r.is_active]
    
    def get_top_rivalry(self, fighter_id: str) -> Optional[Rivalry]:
        """Get fighter's most intense active rivalry"""
        active = self.get_active_rivalries(fighter_id)
        if not active:
            return None
        return max(active, key=lambda r: r.score)
    
    def add_rivalry(self, rivalry: Rivalry) -> None:
        """Add a rivalry to the system"""
        key = self._get_pair_key(rivalry.fighter1_id, rivalry.fighter2_id)
        
        is_new = key not in self._rivalries
        self._rivalries[key] = rivalry
        
        # Update fighter lookup
        for fid in [rivalry.fighter1_id, rivalry.fighter2_id]:
            if fid not in self._fighter_rivalries:
                self._fighter_rivalries[fid] = []
            if key not in self._fighter_rivalries[fid]:
                self._fighter_rivalries[fid].append(key)
        
        if is_new:
            self.total_rivalries_created += 1
            emit("rivalry_created", {
                "fighter1_id": rivalry.fighter1_id,
                "fighter2_id": rivalry.fighter2_id,
                "type": rivalry.rivalry_type.value,
            })
    
    def process_fight(self, context: FightContext) -> Optional[Rivalry]:
        """
        Process a fight result for rivalry implications.
        
        Returns:
            Updated or new rivalry if any
        """
        existing = self.get_rivalry(context.fighter1_id, context.fighter2_id)
        rivalry, events = detect_rivalry_from_fight(context, existing)
        
        if rivalry:
            self.add_rivalry(rivalry)
            self.total_events_recorded += len(events)
        
        return rivalry
    
    def add_interaction(
        self,
        fighter1_id: str,
        fighter2_id: str,
        fighter1_name: str,
        fighter2_name: str,
        interaction_type: str,
        description: str = ""
    ) -> Optional[Rivalry]:
        """
        Record an interaction between fighters (callout, trash talk, etc.)
        
        Args:
            fighter1_id: Initiating fighter
            fighter2_id: Target fighter
            interaction_type: Type of interaction
            description: Optional description
            
        Returns:
            Updated rivalry
        """
        score = RIVALRY_SCORE_MODIFIERS.get(interaction_type, 5)
        
        if not description:
            descriptions = {
                "trash_talk": f"{fighter1_name} calls out {fighter2_name}",
                "callout": f"{fighter1_name} demands a fight with {fighter2_name}",
                "physical_altercation": f"Physical confrontation between fighters",
                "press_conference_incident": f"Heated press conference exchange",
                "social_media_beef": f"Social media back and forth",
            }
            description = descriptions.get(interaction_type, f"{interaction_type} incident")
        
        rivalry = self.get_rivalry(fighter1_id, fighter2_id)
        
        if rivalry is None:
            # Create new rivalry from interaction
            rivalry = Rivalry(
                fighter1_id=fighter1_id,
                fighter2_id=fighter2_id,
                fighter1_name=fighter1_name,
                fighter2_name=fighter2_name,
                rivalry_type=RivalryType.BAD_BLOOD,  # Interactions create bad blood
            )
        
        rivalry.add_score(score, interaction_type, description)
        self.add_rivalry(rivalry)
        self.total_events_recorded += 1
        
        return rivalry
    
    def record_gym_defection(
        self,
        fighter_id: str,
        fighter_name: str,
        former_teammates: List[Tuple[str, str]]  # List of (id, name)
    ) -> List[Rivalry]:
        """
        Record a gym defection, creating gym war rivalries.
        
        Args:
            fighter_id: Defecting fighter's ID
            fighter_name: Defecting fighter's name
            former_teammates: List of (id, name) tuples
            
        Returns:
            List of created/updated rivalries
        """
        rivalries = []
        
        for teammate_id, teammate_name in former_teammates:
            rivalry = self.get_rivalry(fighter_id, teammate_id)
            
            if rivalry is None:
                rivalry = Rivalry(
                    fighter1_id=fighter_id,
                    fighter2_id=teammate_id,
                    fighter1_name=fighter_name,
                    fighter2_name=teammate_name,
                    rivalry_type=RivalryType.GYM_WAR,
                )
            else:
                rivalry.add_secondary_type(RivalryType.GYM_WAR)
            
            rivalry.add_score(
                RIVALRY_SCORE_MODIFIERS["gym_defection"],
                "gym_defection",
                f"{fighter_name} leaves gym, creating tension with {teammate_name}"
            )
            
            self.add_rivalry(rivalry)
            rivalries.append(rivalry)
        
        return rivalries
    
    def apply_monthly_decay(self) -> List[str]:
        """
        Apply monthly decay to all rivalries.
        
        Returns:
            List of rivalry keys that became inactive
        """
        deactivated = []
        
        for key, rivalry in self._rivalries.items():
            if rivalry.is_active:
                rivalry.apply_decay(1)
                if not rivalry.is_active:
                    deactivated.append(key)
        
        return deactivated
    
    def get_heated_rivalries(self) -> List[Rivalry]:
        """Get all currently heated rivalries"""
        return [r for r in self._rivalries.values() if r.is_active and r.is_heated()]
    
    def get_legendary_rivalries(self) -> List[Rivalry]:
        """Get all legendary rivalries (current or historical)"""
        return [r for r in self._rivalries.values() if r.is_legendary()]
    
    def get_division_rivalries(
        self,
        fighter_ids: List[str],
        min_intensity: RivalryIntensity = RivalryIntensity.BUDDING
    ) -> List[Rivalry]:
        """Get rivalries within a set of fighters (e.g., a division)"""
        id_set = set(fighter_ids)
        rivalries = []
        seen = set()
        
        for fid in fighter_ids:
            for rivalry in self.get_active_rivalries(fid):
                key = self._get_pair_key(rivalry.fighter1_id, rivalry.fighter2_id)
                
                if key in seen:
                    continue
                    
                # Check both fighters in division
                if rivalry.fighter1_id in id_set and rivalry.fighter2_id in id_set:
                    if rivalry.intensity.value >= min_intensity.value:
                        rivalries.append(rivalry)
                        seen.add(key)
        
        return sorted(rivalries, key=lambda r: r.score, reverse=True)
    
    def get_rivalry_stats(self) -> Dict[str, Any]:
        """Get system-wide rivalry statistics"""
        active = [r for r in self._rivalries.values() if r.is_active]
        
        intensity_counts = {i.name: 0 for i in RivalryIntensity}
        type_counts = {t.name: 0 for t in RivalryType}
        
        for rivalry in active:
            intensity_counts[rivalry.intensity.name] += 1
            type_counts[rivalry.rivalry_type.name] += 1
        
        return {
            "total_rivalries": len(self._rivalries),
            "active_rivalries": len(active),
            "legendary_rivalries": len(self.get_legendary_rivalries()),
            "heated_rivalries": len(self.get_heated_rivalries()),
            "intensity_distribution": intensity_counts,
            "type_distribution": type_counts,
            "total_events": self.total_events_recorded,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "rivalries": {k: r.to_dict() for k, r in self._rivalries.items()},
            "total_rivalries_created": self.total_rivalries_created,
            "total_events_recorded": self.total_events_recorded,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RivalrySystem":
        """Deserialize from dictionary"""
        system = cls()
        
        for key, r_data in data.get("rivalries", {}).items():
            rivalry = Rivalry.from_dict(r_data)
            system._rivalries[key] = rivalry
            
            # Rebuild fighter lookup
            for fid in [rivalry.fighter1_id, rivalry.fighter2_id]:
                if fid not in system._fighter_rivalries:
                    system._fighter_rivalries[fid] = []
                if key not in system._fighter_rivalries[fid]:
                    system._fighter_rivalries[fid].append(key)
        
        system.total_rivalries_created = data.get("total_rivalries_created", 0)
        system.total_events_recorded = data.get("total_events_recorded", 0)
        
        return system


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global rivalry system instance
_rivalry_system: Optional[RivalrySystem] = None


def get_rivalry_system() -> RivalrySystem:
    """Get the global rivalry system instance"""
    global _rivalry_system
    if _rivalry_system is None:
        _rivalry_system = RivalrySystem()
    return _rivalry_system


def reset_rivalry_system() -> None:
    """Reset the global rivalry system"""
    global _rivalry_system
    _rivalry_system = RivalrySystem()


def get_rivalry_intensity_description(intensity: RivalryIntensity) -> str:
    """Get human-readable description of rivalry intensity"""
    descriptions = {
        RivalryIntensity.BUDDING: "A rivalry beginning to take shape",
        RivalryIntensity.NOTABLE: "A notable rivalry fans are watching",
        RivalryIntensity.HEATED: "A heated rivalry with real animosity",
        RivalryIntensity.FIERCE: "A fierce rivalry that captivates the sport",
        RivalryIntensity.LEGENDARY: "A legendary rivalry for the ages",
    }
    return descriptions.get(intensity, "Unknown rivalry level")


def get_rivalry_type_description(rivalry_type: RivalryType) -> str:
    """Get human-readable description of rivalry type"""
    descriptions = {
        RivalryType.COMPETITIVE: "Mutual respect, but fierce competition",
        RivalryType.BAD_BLOOD: "Personal animosity and genuine dislike",
        RivalryType.TITLE_DISPUTE: "Championship stakes drive this rivalry",
        RivalryType.GYM_WAR: "Former teammates turned enemies",
        RivalryType.NATIONAL_PRIDE: "Countries clash through these fighters",
        RivalryType.STYLE_CLASH: "Striker vs grappler defines this matchup",
        RivalryType.GENERATIONAL: "Old guard vs new generation",
        RivalryType.REVENGE: "One fighter seeks redemption",
    }
    return descriptions.get(rivalry_type, "Unknown rivalry type")


# ============================================================================
# HEAT SYSTEM - FIGHT EFFECTS
# ============================================================================

@dataclass
class HeatFightModifiers:
    """
    Fight modifiers based on rivalry heat level.
    
    These are applied during fight simulation to make heated rivalries
    more intense and consequential.
    """
    heat_level: int                    # Raw score 0-100
    heat_stage: HeatStage              # Stage enum
    damage_multiplier: float           # Both fighters hit harder
    composure_penalty: int             # Both fighters more emotional
    finish_bonus: float                # Higher chance to push for finish
    aggression_bonus: float            # More aggressive fight style
    
    @property
    def stage_name(self) -> str:
        """Human-readable stage name."""
        names = {
            HeatStage.NEUTRAL: "Normal",
            HeatStage.TENSION: "Tension",
            HeatStage.BAD_BLOOD: "Bad Blood",
            HeatStage.HEATED: "Heated",
            HeatStage.WAR: "WAR",
        }
        return names.get(self.heat_stage, "Unknown")
    
    @property
    def has_effects(self) -> bool:
        """Check if heat level has any fight effects."""
        return self.heat_stage != HeatStage.NEUTRAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "heat_level": self.heat_level,
            "heat_stage": self.heat_stage.value,
            "damage_multiplier": self.damage_multiplier,
            "composure_penalty": self.composure_penalty,
            "finish_bonus": self.finish_bonus,
            "aggression_bonus": self.aggression_bonus,
        }


def get_heat_stage(score: int) -> HeatStage:
    """Get heat stage from rivalry score."""
    for stage, (min_score, max_score) in HEAT_STAGE_THRESHOLDS.items():
        if min_score <= score <= max_score:
            return stage
    return HeatStage.WAR if score > 100 else HeatStage.NEUTRAL


def get_heat_fight_modifiers(
    fighter1_id: str,
    fighter2_id: str,
    rivalry_system: Optional["RivalrySystem"] = None
) -> HeatFightModifiers:
    """
    Get fight modifiers based on rivalry heat between two fighters.
    
    Args:
        fighter1_id: First fighter's ID
        fighter2_id: Second fighter's ID
        rivalry_system: Optional rivalry system (uses global if not provided)
    
    Returns:
        HeatFightModifiers with all applicable modifiers
    """
    if rivalry_system is None:
        rivalry_system = get_rivalry_system()
    
    rivalry = rivalry_system.get_rivalry(fighter1_id, fighter2_id)
    
    if not rivalry or not rivalry.is_active:
        # No rivalry - return neutral modifiers
        return HeatFightModifiers(
            heat_level=0,
            heat_stage=HeatStage.NEUTRAL,
            damage_multiplier=1.0,
            composure_penalty=0,
            finish_bonus=0.0,
            aggression_bonus=0.0,
        )
    
    heat_level = rivalry.score
    heat_stage = get_heat_stage(heat_level)
    
    damage_mult, composure_pen, finish_bon, aggression_bon = HEAT_FIGHT_MODIFIERS[heat_stage]
    
    return HeatFightModifiers(
        heat_level=heat_level,
        heat_stage=heat_stage,
        damage_multiplier=damage_mult,
        composure_penalty=composure_pen,
        finish_bonus=finish_bon,
        aggression_bonus=aggression_bon,
    )


def add_heat_from_event(
    fighter1_id: str,
    fighter2_id: str,
    event_type: str,
    description: str = "",
    rivalry_system: Optional["RivalrySystem"] = None,
) -> Optional[int]:
    """
    Add heat between two fighters from a specific event.
    
    Args:
        fighter1_id: First fighter's ID
        fighter2_id: Second fighter's ID  
        event_type: Type of event (from HEAT_SOURCE_MODIFIERS or RIVALRY_SCORE_MODIFIERS)
        description: Optional description for the event
        rivalry_system: Optional rivalry system
    
    Returns:
        New heat level, or None if no change
    """
    # Get modifier amount
    modifier = HEAT_SOURCE_MODIFIERS.get(event_type)
    if modifier is None:
        modifier = RIVALRY_SCORE_MODIFIERS.get(event_type, 0)
    
    if modifier == 0:
        return None
    
    if rivalry_system is None:
        rivalry_system = get_rivalry_system()
    
    rivalry = rivalry_system.get_rivalry(fighter1_id, fighter2_id)
    
    if not description:
        description = f"{event_type.replace('_', ' ').title()} incident"
    
    if rivalry:
        # Add to existing rivalry
        rivalry.add_score(modifier, event_type, description)
        return rivalry.score
    else:
        # Create new rivalry
        rivalry = rivalry_system.create_rivalry(
            fighter1_id=fighter1_id,
            fighter2_id=fighter2_id,
            fighter1_name="",  # Will be filled by system
            fighter2_name="",
            rivalry_type=RivalryType.BAD_BLOOD,
            initial_score=modifier,
        )
        if rivalry:
            rivalry.add_score(0, event_type, description)  # Just log the event
            return rivalry.score
    
    return None


def get_heat_description(score: int) -> str:
    """Get a narrative description of the heat level."""
    stage = get_heat_stage(score)
    
    descriptions = {
        HeatStage.NEUTRAL: "No significant tension between these fighters.",
        HeatStage.TENSION: "There's an edge between these two. Something's brewing.",
        HeatStage.BAD_BLOOD: "Bad blood is evident. This has gotten personal.",
        HeatStage.HEATED: "A heated rivalry. These fighters genuinely dislike each other.",
        HeatStage.WAR: "All-out WAR. This goes beyond sport - it's personal vendetta.",
    }
    
    return descriptions.get(stage, "Unknown tension level.")


def get_heat_commentary_tag(score: int) -> Optional[str]:
    """Get a short tag for commentary based on heat level."""
    stage = get_heat_stage(score)
    
    tags = {
        HeatStage.NEUTRAL: None,
        HeatStage.TENSION: "tension",
        HeatStage.BAD_BLOOD: "bad_blood", 
        HeatStage.HEATED: "heated",
        HeatStage.WAR: "war",
    }
    
    return tags.get(stage)


def check_for_rivalry(fighter1_id: str, fighter2_id: str) -> bool:
    """Quick check if a rivalry exists between two fighters"""
    system = get_rivalry_system()
    rivalry = system.get_rivalry(fighter1_id, fighter2_id)
    return rivalry is not None and rivalry.is_active


def get_rivalry_score(fighter1_id: str, fighter2_id: str) -> int:
    """Get rivalry score between two fighters (0 if no rivalry)"""
    system = get_rivalry_system()
    rivalry = system.get_rivalry(fighter1_id, fighter2_id)
    return rivalry.score if rivalry else 0


def format_rivalry_display(rivalry: Rivalry) -> str:
    """Format rivalry for display"""
    intensity_emoji = {
        RivalryIntensity.BUDDING: "ðŸŒ±",
        RivalryIntensity.NOTABLE: "âš¡",
        RivalryIntensity.HEATED: "ðŸ”¥",
        RivalryIntensity.FIERCE: "ðŸ’¥",
        RivalryIntensity.LEGENDARY: "ðŸ‘‘",
    }
    
    emoji = intensity_emoji.get(rivalry.intensity, "")
    
    return (
        f"{emoji} {rivalry.fighter1_name} vs {rivalry.fighter2_name}\n"
        f"   Type: {rivalry.rivalry_type.value.replace('_', ' ').title()}\n"
        f"   Intensity: {rivalry.intensity.name.title()} ({rivalry.score}/100)\n"
        f"   Record: {rivalry.head_to_head}"
    )
