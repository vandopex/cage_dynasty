# systems/training_camp.py
# Module: Training Camp Integration & Camp Journal
# Lines: ~1,100
#
# Integrates training into the gameplay loop between fights.
# Includes Camp Journal for full history tracking of all events.

"""
Cage Dynasty - Training Camp Integration & Camp Journal

Connects the training system to the gameplay loop:
- Start/manage training camps between fights
- Apply facility caps to training gains
- Track progress with visual displays
- Camp Journal - full history of training events
- Handle fight-specific preparation
- Auto-schedule training around fights

CAMP JOURNAL:
============
The Camp Journal tracks every event during a training camp:
- Weekly training gains
- Training events (breakthroughs, setbacks, etc.)
- Transactions (sponsorship payments)
- Injuries
- Camp summary with rating

This creates a narrative of the camp that players can review.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random


# ============================================================================
# ENUMS
# ============================================================================

class TrainingFocus(Enum):
    """Areas a fighter can focus training on."""
    STRIKING = "STRIKING"
    WRESTLING = "WRESTLING"
    JIUJITSU = "JIU-JITSU"
    CONDITIONING = "CONDITIONING"
    STRENGTH_POWER = "STRENGTH_POWER"
    BALANCED = "BALANCED"
    FIGHT_SPECIFIC = "FIGHT_SPECIFIC"


class TrainingIntensity(Enum):
    """How hard the fighter trains."""
    REST = "REST"
    LIGHT = "LIGHT"
    MODERATE = "MODERATE"
    INTENSE = "INTENSE"
    EXTREME = "EXTREME"


class CampTemplate(Enum):
    """Training camp strategy templates."""
    STEADY = "Steady Build"
    PEAK_LATE = "Hard Finish"
    FRONT_LOAD = "Fast Start"
    GRINDER = "No Days Off"
    CAUTIOUS = "Recovery Camp"


class JournalEntryType(Enum):
    """Types of entries in the camp journal."""
    TRAINING = "training"
    EVENT = "event"
    INJURY = "injury"
    TRANSACTION = "transaction"
    SPARRING = "sparring"
    MILESTONE = "milestone"
    NOTE = "note"


# ============================================================================
# CONSTANTS
# ============================================================================

# Focus to attribute mapping
FOCUS_ATTRIBUTES: Dict[TrainingFocus, List[str]] = {
    TrainingFocus.STRIKING: ["boxing", "kicks", "clinch", "power", "accuracy"],
    TrainingFocus.WRESTLING: ["wrestling", "td_defense", "top_control"],
    TrainingFocus.JIUJITSU: ["bjj", "submissions", "guard"],
    TrainingFocus.CONDITIONING: ["cardio", "strength", "speed", "recovery"],
    TrainingFocus.STRENGTH_POWER: ["strength", "speed", "power"],
    TrainingFocus.BALANCED: [
        "boxing", "kicks", "clinch", "power", "accuracy",
        "bjj", "submissions", "top_control", "wrestling", "td_defense",
        "cardio", "strength", "speed", "recovery", "chin", "heart"
    ],
    TrainingFocus.FIGHT_SPECIFIC: [],  # Set based on opponent
}

# Intensity modifiers
INTENSITY_GAIN_MULTIPLIER: Dict[TrainingIntensity, float] = {
    TrainingIntensity.REST: 0.0,
    TrainingIntensity.LIGHT: 0.5,
    TrainingIntensity.MODERATE: 1.0,
    TrainingIntensity.INTENSE: 1.5,
    TrainingIntensity.EXTREME: 2.0,
}

INTENSITY_FATIGUE: Dict[TrainingIntensity, int] = {
    TrainingIntensity.REST: -15,
    TrainingIntensity.LIGHT: 2,
    TrainingIntensity.MODERATE: 5,
    TrainingIntensity.INTENSE: 10,
    TrainingIntensity.EXTREME: 18,
}

# Variance for fatigue (adds randomness)
INTENSITY_FATIGUE_VARIANCE: Dict[TrainingIntensity, int] = {
    TrainingIntensity.REST: 3,      # -18 to -12
    TrainingIntensity.LIGHT: 1,     # 1 to 3
    TrainingIntensity.MODERATE: 2,  # 3 to 7
    TrainingIntensity.INTENSE: 3,   # 7 to 13
    TrainingIntensity.EXTREME: 4,   # 14 to 22
}

INTENSITY_INJURY_RISK: Dict[TrainingIntensity, float] = {
    TrainingIntensity.REST: 0.00,
    TrainingIntensity.LIGHT: 0.00,
    TrainingIntensity.MODERATE: 0.01,
    TrainingIntensity.INTENSE: 0.03,
    TrainingIntensity.EXTREME: 0.08,
}

# Facility stat caps
FACILITY_STAT_CAPS: Dict[str, int] = {
    "GARAGE": 65,
    "LOCAL": 72,
    "REGIONAL": 80,
    "NATIONAL": 90,
    "ELITE": 100,
}

# Age modifiers
AGE_GAIN_MODIFIER: Dict[str, float] = {
    "young": 1.3,      # Under 26
    "prime": 1.0,      # 26-32
    "veteran": 0.7,    # 33-35
    "old": 0.4,        # 36+
}

# Default camp duration
DEFAULT_CAMP_WEEKS = 8
MAX_CAMP_WEEKS = 12
MIN_CAMP_WEEKS = 4


# ============================================================================
# TEMPLATE SCHEDULES
# ============================================================================

TEMPLATE_INFO: Dict[CampTemplate, Dict[str, Any]] = {
    CampTemplate.STEADY: {
        "name": "Steady Build",
        "icon": "🎯",
        "description": "Conservative approach, gradual intensity",
        "risk": "Low",
        "gains": "Medium",
        "pattern": "MOD → INT → LIGHT taper",
    },
    CampTemplate.PEAK_LATE: {
        "name": "Hard Finish",
        "icon": "📈",
        "description": "Light start, peak near fight week",
        "risk": "Medium",
        "gains": "Medium-High",
        "pattern": "LIGHT → MOD → INT → LIGHT",
    },
    CampTemplate.FRONT_LOAD: {
        "name": "Fast Start",
        "icon": "⚡",
        "description": "Intense early, long recovery taper",
        "risk": "Medium",
        "gains": "Medium",
        "pattern": "INT → MOD → LIGHT → REST",
    },
    CampTemplate.GRINDER: {
        "name": "No Days Off",
        "icon": "🔥",
        "description": "High intensity throughout - risky!",
        "risk": "HIGH",
        "gains": "Highest",
        "pattern": "INT throughout",
    },
    CampTemplate.CAUTIOUS: {
        "name": "Recovery Camp",
        "icon": "💚",
        "description": "Light training, focus on recovery",
        "risk": "None",
        "gains": "Low",
        "pattern": "LIGHT throughout, REST finish",
    },
}


def generate_schedule(template: CampTemplate, weeks: int) -> List[TrainingIntensity]:
    """
    Generate a week-by-week intensity schedule for a template.
    
    Scales to any camp duration (4-12 weeks).
    """
    weeks = max(MIN_CAMP_WEEKS, min(MAX_CAMP_WEEKS, weeks))
    
    if template == CampTemplate.STEADY:
        return _generate_steady(weeks)
    elif template == CampTemplate.PEAK_LATE:
        return _generate_peak_late(weeks)
    elif template == CampTemplate.FRONT_LOAD:
        return _generate_front_load(weeks)
    elif template == CampTemplate.GRINDER:
        return _generate_grinder(weeks)
    elif template == CampTemplate.CAUTIOUS:
        return _generate_cautious(weeks)
    else:
        return _generate_steady(weeks)


def _generate_steady(weeks: int) -> List[TrainingIntensity]:
    """STEADY: MOD base → INT peak → LIGHT taper"""
    schedule = []
    taper_weeks = max(1, weeks // 4)
    peak_weeks = max(1, weeks // 4)
    base_weeks = weeks - taper_weeks - peak_weeks
    
    for _ in range(base_weeks):
        schedule.append(TrainingIntensity.MODERATE)
    for _ in range(peak_weeks):
        schedule.append(TrainingIntensity.INTENSE)
    for _ in range(taper_weeks):
        schedule.append(TrainingIntensity.LIGHT)
    
    return schedule[:weeks]


def _generate_peak_late(weeks: int) -> List[TrainingIntensity]:
    """PEAK_LATE: LIGHT start → MOD build → INT peak → LIGHT finish"""
    schedule = []
    start_weeks = max(1, weeks // 4)
    build_weeks = max(1, weeks // 3)
    peak_weeks = max(1, weeks // 3)
    taper_weeks = max(1, weeks - start_weeks - build_weeks - peak_weeks)
    
    for _ in range(start_weeks):
        schedule.append(TrainingIntensity.LIGHT)
    for _ in range(build_weeks):
        schedule.append(TrainingIntensity.MODERATE)
    for _ in range(peak_weeks):
        schedule.append(TrainingIntensity.INTENSE)
    for _ in range(taper_weeks):
        schedule.append(TrainingIntensity.LIGHT)
    
    return schedule[:weeks]


def _generate_front_load(weeks: int) -> List[TrainingIntensity]:
    """FRONT_LOAD: INT early → MOD middle → LIGHT/REST finish"""
    schedule = []
    intense_weeks = max(1, weeks // 3)
    moderate_weeks = max(1, weeks // 3)
    taper_weeks = weeks - intense_weeks - moderate_weeks
    
    for _ in range(intense_weeks):
        schedule.append(TrainingIntensity.INTENSE)
    for _ in range(moderate_weeks):
        schedule.append(TrainingIntensity.MODERATE)
    for i in range(taper_weeks):
        if i >= taper_weeks - 1:
            schedule.append(TrainingIntensity.REST)
        else:
            schedule.append(TrainingIntensity.LIGHT)
    
    return schedule[:weeks]


def _generate_grinder(weeks: int) -> List[TrainingIntensity]:
    """GRINDER: INT throughout, minimal taper"""
    schedule = []
    taper_weeks = max(1, weeks // 6)
    intense_weeks = weeks - taper_weeks
    
    for _ in range(intense_weeks):
        schedule.append(TrainingIntensity.INTENSE)
    for i in range(taper_weeks):
        if i == taper_weeks - 1:
            schedule.append(TrainingIntensity.LIGHT)
        else:
            schedule.append(TrainingIntensity.MODERATE)
    
    return schedule[:weeks]


def _generate_cautious(weeks: int) -> List[TrainingIntensity]:
    """CAUTIOUS: LIGHT throughout, REST finish"""
    schedule = []
    rest_weeks = max(1, weeks // 4)
    moderate_weeks = max(1, weeks // 4)
    light_weeks = weeks - rest_weeks - moderate_weeks
    
    for _ in range(light_weeks):
        schedule.append(TrainingIntensity.LIGHT)
    for _ in range(moderate_weeks):
        schedule.append(TrainingIntensity.MODERATE)
    for _ in range(rest_weeks):
        schedule.append(TrainingIntensity.REST)
    
    return schedule[:weeks]


def get_fatigue_with_variance(intensity: TrainingIntensity) -> int:
    """Get fatigue change with random variance."""
    base = INTENSITY_FATIGUE.get(intensity, 5)
    variance = INTENSITY_FATIGUE_VARIANCE.get(intensity, 2)
    return base + random.randint(-variance, variance)


def estimate_template_fatigue(template: CampTemplate, weeks: int) -> Tuple[int, int, int]:
    """
    Estimate total fatigue for a template.
    Returns (min, expected, max).
    """
    schedule = generate_schedule(template, weeks)
    
    total_base = 0
    total_variance = 0
    
    for intensity in schedule:
        total_base += INTENSITY_FATIGUE.get(intensity, 5)
        total_variance += INTENSITY_FATIGUE_VARIANCE.get(intensity, 2)
    
    return (total_base - total_variance, total_base, total_base + total_variance)


# ============================================================================
# DISPLAY INFO
# ============================================================================

FOCUS_INFO: Dict[TrainingFocus, Dict[str, str]] = {
    TrainingFocus.STRIKING: {
        "name": "Striking",
        "icon": "ðŸ¥Š",
        "description": "Boxing, kicks, clinch work, power, accuracy",
        "improves": "Stand-up game and knockout power",
    },
    TrainingFocus.WRESTLING: {
        "name": "Wrestling",
        "icon": "ðŸ¤¼",
        "description": "Wrestling offense and takedown defense",
        "improves": "Dictate where the fight takes place",
    },
    TrainingFocus.JIUJITSU: {
        "name": "Jiu-Jitsu",
        "icon": "ðŸ¥‹",
        "description": "BJJ, submissions, guard work",
        "improves": "Ground game and submission threat",
    },
    TrainingFocus.CONDITIONING: {
        "name": "Conditioning",
        "icon": "ðŸƒ",
        "description": "Cardio, strength, speed, recovery",
        "improves": "Stamina, power, and durability",
    },
    TrainingFocus.STRENGTH_POWER: {
        "name": "Strength & Power",
        "icon": "ðŸ’ª",
        "description": "Raw power, explosiveness, speed",
        "improves": "Physical attributes and knockout power",
    },
    TrainingFocus.BALANCED: {
        "name": "Balanced",
        "icon": "âš–ï¸",
        "description": "Well-rounded training across all areas",
        "improves": "Overall game (lower gains per area)",
    },
    TrainingFocus.FIGHT_SPECIFIC: {
        "name": "Fight Specific",
        "icon": "ðŸŽ¯",
        "description": "Prepare for specific opponent's weaknesses",
        "improves": "Exploit upcoming opponent",
    },
}

INTENSITY_INFO: Dict[TrainingIntensity, Dict[str, Any]] = {
    TrainingIntensity.REST: {
        "name": "Rest",
        "icon": "💤",
        "gains": "0%",
        "injury_risk": "0%",
        "fatigue": "Recovery",
        "description": "Full rest week - recover fatigue (-15)",
    },
    TrainingIntensity.LIGHT: {
        "name": "Light",
        "icon": "🟢",
        "gains": "50%",
        "injury_risk": "0%",
        "fatigue": "Low",
        "description": "Recovery mode - maintain skills, minimal improvement",
    },
    TrainingIntensity.MODERATE: {
        "name": "Moderate",
        "icon": "🟡",
        "gains": "100%",
        "injury_risk": "1%",
        "fatigue": "Normal",
        "description": "Standard training - balanced risk and reward",
    },
    TrainingIntensity.INTENSE: {
        "name": "Intense",
        "icon": "🟠",
        "gains": "150%",
        "injury_risk": "3%",
        "fatigue": "High",
        "description": "Hard push - faster improvement, higher risk",
    },
    TrainingIntensity.EXTREME: {
        "name": "Extreme",
        "icon": "🔴",
        "gains": "200%",
        "injury_risk": "8%",
        "fatigue": "Very High",
        "description": "Maximum effort - huge gains but injury danger",
    },
}

# Event icons by category
EVENT_ICONS = {
    "positive": "ðŸ“ˆ",
    "negative": "ðŸ“‰",
    "neutral": "ðŸ“‹",
    "training": "ðŸ‹ï¸",
    "injury": "ðŸ¥",
    "transaction": "ðŸ’°",
    "sparring": "ðŸ¥Š",
    "milestone": "ðŸ†",
}


# ============================================================================
# CAMP JOURNAL
# ============================================================================

@dataclass
class CampJournalEntry:
    """Single entry in the camp journal."""
    week_number: int  # Week in camp (1-8)
    game_week: int  # Overall game week
    entry_type: JournalEntryType
    headline: str
    description: str
    category: str = ""  # "positive", "negative", "neutral" for events
    stat_changes: Dict[str, int] = field(default_factory=dict)
    money_change: int = 0
    icon: str = ""
    
    def __post_init__(self):
        if not self.icon:
            if self.category:
                self.icon = EVENT_ICONS.get(self.category, "ðŸ“‹")
            else:
                self.icon = EVENT_ICONS.get(self.entry_type.value, "ðŸ“‹")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "week_number": self.week_number,
            "game_week": self.game_week,
            "entry_type": self.entry_type.value,
            "headline": self.headline,
            "description": self.description,
            "category": self.category,
            "stat_changes": self.stat_changes.copy(),
            "money_change": self.money_change,
            "icon": self.icon,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampJournalEntry':
        return cls(
            week_number=data["week_number"],
            game_week=data.get("game_week", 0),
            entry_type=JournalEntryType(data["entry_type"]),
            headline=data["headline"],
            description=data.get("description", ""),
            category=data.get("category", ""),
            stat_changes=data.get("stat_changes", {}),
            money_change=data.get("money_change", 0),
            icon=data.get("icon", ""),
        )


@dataclass
class CampJournal:
    """
    Full journal for a training camp.
    
    Tracks every event, transaction, and milestone during camp.
    """
    fighter_id: str
    fighter_name: str
    camp_start_week: int
    focus: str
    coach_name: str
    entries: List[CampJournalEntry] = field(default_factory=list)
    
    # Summary stats (updated as we go)
    total_gains: Dict[str, int] = field(default_factory=dict)
    total_events: int = 0
    positive_events: int = 0
    negative_events: int = 0
    neutral_events: int = 0
    money_earned: int = 0
    money_spent: int = 0
    injuries: int = 0
    
    def add_training_entry(
        self,
        week_number: int,
        game_week: int,
        gains: Dict[str, int],
    ) -> CampJournalEntry:
        """Add a weekly training entry."""
        if not gains:
            headline = "Rest week"
            description = "No training gains this week."
        else:
            total = sum(gains.values())
            top_gains = sorted(gains.items(), key=lambda x: -x[1])[:3]
            gains_str = ", ".join(f"+{v} {k}" for k, v in top_gains)
            headline = f"Training: +{total} points"
            description = gains_str
        
        entry = CampJournalEntry(
            week_number=week_number,
            game_week=game_week,
            entry_type=JournalEntryType.TRAINING,
            headline=headline,
            description=description,
            stat_changes=gains,
            icon="ðŸ‹ï¸",
        )
        self.entries.append(entry)
        
        # Update totals
        for attr, gain in gains.items():
            self.total_gains[attr] = self.total_gains.get(attr, 0) + gain
        
        return entry
    
    def add_event_entry(
        self,
        week_number: int,
        game_week: int,
        headline: str,
        description: str,
        category: str,
        stat_changes: Dict[str, int] = None,
    ) -> CampJournalEntry:
        """Add a training event entry."""
        stat_changes = stat_changes or {}
        
        entry = CampJournalEntry(
            week_number=week_number,
            game_week=game_week,
            entry_type=JournalEntryType.EVENT,
            headline=headline,
            description=description,
            category=category,
            stat_changes=stat_changes,
            icon=EVENT_ICONS.get(category, "ðŸ“‹"),
        )
        self.entries.append(entry)
        
        # Update totals
        self.total_events += 1
        if category == "positive":
            self.positive_events += 1
        elif category == "negative":
            self.negative_events += 1
        else:
            self.neutral_events += 1
        
        # Add event stat changes to totals
        for attr, gain in stat_changes.items():
            self.total_gains[attr] = self.total_gains.get(attr, 0) + gain
        
        return entry
    
    def add_injury_entry(
        self,
        week_number: int,
        game_week: int,
        injury_description: str,
    ) -> CampJournalEntry:
        """Add an injury entry."""
        entry = CampJournalEntry(
            week_number=week_number,
            game_week=game_week,
            entry_type=JournalEntryType.INJURY,
            headline="Training Injury",
            description=injury_description,
            category="negative",
            icon="ðŸ¥",
        )
        self.entries.append(entry)
        self.injuries += 1
        
        return entry
    
    def add_transaction_entry(
        self,
        week_number: int,
        game_week: int,
        description: str,
        amount: int,
    ) -> CampJournalEntry:
        """Add a financial transaction entry."""
        if amount >= 0:
            headline = f"Income: +${amount:,}"
            self.money_earned += amount
        else:
            headline = f"Expense: -${abs(amount):,}"
            self.money_spent += abs(amount)
        
        entry = CampJournalEntry(
            week_number=week_number,
            game_week=game_week,
            entry_type=JournalEntryType.TRANSACTION,
            headline=headline,
            description=description,
            money_change=amount,
            icon="ðŸ’°",
        )
        self.entries.append(entry)
        
        return entry
    
    def add_sparring_entry(
        self,
        week_number: int,
        game_week: int,
        partner_name: str,
        result: str,
        stat_changes: Dict[str, int] = None,
    ) -> CampJournalEntry:
        """Add a sparring session entry."""
        stat_changes = stat_changes or {}
        
        entry = CampJournalEntry(
            week_number=week_number,
            game_week=game_week,
            entry_type=JournalEntryType.SPARRING,
            headline=f"Sparring with {partner_name}",
            description=result,
            stat_changes=stat_changes,
            icon="ðŸ¥Š",
        )
        self.entries.append(entry)
        
        return entry
    
    def add_milestone_entry(
        self,
        week_number: int,
        game_week: int,
        milestone: str,
        description: str = "",
    ) -> CampJournalEntry:
        """Add a milestone entry."""
        entry = CampJournalEntry(
            week_number=week_number,
            game_week=game_week,
            entry_type=JournalEntryType.MILESTONE,
            headline=milestone,
            description=description,
            category="positive",
            icon="ðŸ†",
        )
        self.entries.append(entry)
        
        return entry
    
    def get_entries_for_week(self, week_number: int) -> List[CampJournalEntry]:
        """Get all entries for a specific week."""
        return [e for e in self.entries if e.week_number == week_number]
    
    def get_camp_rating(self) -> Tuple[str, int]:
        """
        Calculate a camp rating based on events and gains.
        
        Returns (rating_text, stars out of 5)
        """
        total_gain_points = sum(self.total_gains.values())
        
        # Base score from gains
        if total_gain_points >= 25:
            score = 5
        elif total_gain_points >= 18:
            score = 4
        elif total_gain_points >= 12:
            score = 3
        elif total_gain_points >= 6:
            score = 2
        else:
            score = 1
        
        # Adjust for events
        event_modifier = self.positive_events - self.negative_events
        if event_modifier >= 2:
            score = min(5, score + 1)
        elif event_modifier <= -2:
            score = max(1, score - 1)
        
        # Penalty for injuries
        if self.injuries >= 2:
            score = max(1, score - 1)
        
        ratings = {
            5: "EXCELLENT",
            4: "GREAT",
            3: "GOOD",
            2: "FAIR",
            1: "POOR",
        }
        
        return ratings[score], score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "camp_start_week": self.camp_start_week,
            "focus": self.focus,
            "coach_name": self.coach_name,
            "entries": [e.to_dict() for e in self.entries],
            "total_gains": self.total_gains.copy(),
            "total_events": self.total_events,
            "positive_events": self.positive_events,
            "negative_events": self.negative_events,
            "neutral_events": self.neutral_events,
            "money_earned": self.money_earned,
            "money_spent": self.money_spent,
            "injuries": self.injuries,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampJournal':
        journal = cls(
            fighter_id=data["fighter_id"],
            fighter_name=data["fighter_name"],
            camp_start_week=data["camp_start_week"],
            focus=data["focus"],
            coach_name=data["coach_name"],
        )
        journal.entries = [CampJournalEntry.from_dict(e) for e in data.get("entries", [])]
        journal.total_gains = data.get("total_gains", {})
        journal.total_events = data.get("total_events", 0)
        journal.positive_events = data.get("positive_events", 0)
        journal.negative_events = data.get("negative_events", 0)
        journal.neutral_events = data.get("neutral_events", 0)
        journal.money_earned = data.get("money_earned", 0)
        journal.money_spent = data.get("money_spent", 0)
        journal.injuries = data.get("injuries", 0)
        
        return journal


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FighterTrainingInfo:
    """Fighter info needed for training calculations."""
    fighter_id: str
    name: str
    age: int
    attributes: Dict[str, int]
    fatigue: int = 0
    is_injured: bool = False
    scheduled_fight_date: Optional[str] = None
    scheduled_fight_weeks: int = 0
    traits: List[str] = field(default_factory=list)
    
    def get_attribute(self, attr: str) -> int:
        return self.attributes.get(attr, 50)
    
    def set_attribute(self, attr: str, value: int) -> None:
        self.attributes[attr] = max(1, min(100, value))


@dataclass
class TrainingWeekResult:
    """Results from one week of training."""
    week_number: int
    gains: Dict[str, int]  # attribute -> points gained
    fatigue_added: int
    injury_occurred: bool
    injury_type: str = ""
    capped_attributes: List[str] = field(default_factory=list)
    event_headline: str = ""
    event_description: str = ""
    event_category: str = ""
    
    @property
    def total_gains(self) -> int:
        return sum(self.gains.values())
    
    @property
    def had_event(self) -> bool:
        return bool(self.event_headline)


@dataclass 
class ActiveTrainingCamp:
    """An active training camp in progress."""
    camp_id: str
    fighter_id: str
    fighter_name: str
    
    # Settings
    focus: TrainingFocus
    intensity: TrainingIntensity  # Legacy - now use schedule
    facility_tier: str
    
    # Template system (new)
    template: Optional[CampTemplate] = None
    schedule: List[TrainingIntensity] = field(default_factory=list)
    
    # Duration
    total_weeks: int = 8
    weeks_completed: int = 0
    start_date: str = ""
    
    # Tracking
    weekly_results: List[TrainingWeekResult] = field(default_factory=list)
    total_gains: Dict[str, int] = field(default_factory=dict)
    total_fatigue: int = 0
    injuries: int = 0
    
    # Events
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Journal
    journal: Optional[CampJournal] = None
    
    # Fight-specific
    opponent_id: Optional[str] = None
    opponent_name: Optional[str] = None
    target_attributes: List[str] = field(default_factory=list)
    
    # Coach info
    coach_name: str = ""
    coach_specialty: str = ""
    
    def get_current_intensity(self) -> TrainingIntensity:
        """Get the intensity for the current week based on schedule."""
        if self.schedule and 0 <= self.weeks_completed < len(self.schedule):
            return self.schedule[self.weeks_completed]
        # Fallback to legacy single intensity
        return self.intensity
    
    def get_week_intensity(self, week: int) -> TrainingIntensity:
        """Get the intensity for a specific week (0-indexed)."""
        if self.schedule and 0 <= week < len(self.schedule):
            return self.schedule[week]
        return self.intensity
    
    @property
    def weeks_remaining(self) -> int:
        return max(0, self.total_weeks - self.weeks_completed)
    
    @property
    def is_complete(self) -> bool:
        return self.weeks_completed >= self.total_weeks
    
    @property
    def progress_percent(self) -> float:
        if self.total_weeks == 0:
            return 100.0
        return (self.weeks_completed / self.total_weeks) * 100
    
    @property
    def sum_total_gains(self) -> int:
        return sum(self.total_gains.values())
    
    @property
    def positive_events(self) -> int:
        return len([e for e in self.events if e.get("category") == "positive"])
    
    @property
    def negative_events(self) -> int:
        return len([e for e in self.events if e.get("category") == "negative"])
    
    def record_week(self, result: TrainingWeekResult, game_week: int = 0) -> None:
        """Record a week's training results."""
        self.weekly_results.append(result)
        self.weeks_completed += 1
        self.total_fatigue += result.fatigue_added
        
        for attr, gain in result.gains.items():
            self.total_gains[attr] = self.total_gains.get(attr, 0) + gain
        
        if result.injury_occurred:
            self.injuries += 1
        
        # Record event if any
        if result.had_event:
            self.events.append({
                "week": self.weeks_completed,
                "headline": result.event_headline,
                "description": result.event_description,
                "category": result.event_category,
            })
        
        # Update journal if exists
        if self.journal:
            self.journal.add_training_entry(
                week_number=self.weeks_completed,
                game_week=game_week,
                gains=result.gains,
            )
            
            if result.had_event:
                self.journal.add_event_entry(
                    week_number=self.weeks_completed,
                    game_week=game_week,
                    headline=result.event_headline,
                    description=result.event_description,
                    category=result.event_category,
                )
            
            if result.injury_occurred:
                self.journal.add_injury_entry(
                    week_number=self.weeks_completed,
                    game_week=game_week,
                    injury_description=result.injury_type,
                )
    
    def initialize_journal(self, game_week: int) -> None:
        """Initialize the camp journal."""
        self.journal = CampJournal(
            fighter_id=self.fighter_id,
            fighter_name=self.fighter_name,
            camp_start_week=game_week,
            focus=self.focus.value,
            coach_name=self.coach_name or "Coach",
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "camp_id": self.camp_id,
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "focus": self.focus.value,
            "intensity": self.intensity.value,
            "facility_tier": self.facility_tier,
            "template": self.template.value if self.template else None,
            "schedule": [i.value for i in self.schedule] if self.schedule else [],
            "total_weeks": self.total_weeks,
            "weeks_completed": self.weeks_completed,
            "start_date": self.start_date,
            "total_gains": self.total_gains,
            "total_fatigue": self.total_fatigue,
            "injuries": self.injuries,
            "events": self.events,
            "journal": self.journal.to_dict() if self.journal else None,
            "opponent_id": self.opponent_id,
            "opponent_name": self.opponent_name,
            "target_attributes": self.target_attributes,
            "coach_name": self.coach_name,
            "coach_specialty": self.coach_specialty,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActiveTrainingCamp":
        # Parse template if present
        template = None
        if data.get("template"):
            try:
                template = CampTemplate(data["template"])
            except (ValueError, KeyError):
                template = None
        
        # Parse schedule if present
        schedule = []
        if data.get("schedule"):
            for intensity_val in data["schedule"]:
                try:
                    schedule.append(TrainingIntensity(intensity_val))
                except (ValueError, KeyError):
                    schedule.append(TrainingIntensity.MODERATE)
        
        camp = cls(
            camp_id=data["camp_id"],
            fighter_id=data["fighter_id"],
            fighter_name=data["fighter_name"],
            focus=TrainingFocus(data["focus"]),
            intensity=TrainingIntensity(data["intensity"]),
            facility_tier=data["facility_tier"],
            template=template,
            schedule=schedule,
            total_weeks=data["total_weeks"],
            weeks_completed=data.get("weeks_completed", 0),
            start_date=data.get("start_date", ""),
            total_gains=data.get("total_gains", {}),
            total_fatigue=data.get("total_fatigue", 0),
            injuries=data.get("injuries", 0),
            events=data.get("events", []),
            opponent_id=data.get("opponent_id"),
            opponent_name=data.get("opponent_name"),
            target_attributes=data.get("target_attributes", []),
            coach_name=data.get("coach_name", ""),
            coach_specialty=data.get("coach_specialty", ""),
        )
        
        if data.get("journal"):
            camp.journal = CampJournal.from_dict(data["journal"])
        
        return camp


# ============================================================================
# TRAINING CALCULATIONS
# ============================================================================

def get_age_category(age: int) -> str:
    """Get age category for training modifier."""
    if age < 26:
        return "young"
    elif age <= 32:
        return "prime"
    elif age <= 35:
        return "veteran"
    else:
        return "old"


def calculate_diminishing_returns(current_value: int) -> float:
    """Higher stats are harder to improve."""
    if current_value < 50:
        return 1.2
    elif current_value < 70:
        return 1.0
    elif current_value < 80:
        return 0.7
    elif current_value < 90:
        return 0.4
    else:
        return 0.2


def calculate_facility_bonus(tier: str) -> float:
    """Better facilities = better training."""
    bonuses = {
        "GARAGE": 0.8,
        "LOCAL": 0.9,
        "REGIONAL": 1.0,
        "NATIONAL": 1.15,
        "ELITE": 1.3,
    }
    return bonuses.get(tier, 1.0)


def apply_facility_cap(
    current_value: int,
    raw_gain: int,
    facility_tier: str
) -> Tuple[int, int, bool]:
    """
    Apply facility cap to training gain.
    
    Returns:
        Tuple of (new_value, actual_gain, was_capped)
    """
    cap = FACILITY_STAT_CAPS.get(facility_tier, 100)
    new_value = current_value + raw_gain
    
    if new_value > cap:
        actual_gain = max(0, cap - current_value)
        return cap, actual_gain, True
    
    return new_value, raw_gain, False


def calculate_weekly_gain(
    base_gain: float,
    current_value: int,
    age: int,
    facility_tier: str,
    intensity: TrainingIntensity,
    is_focus_attribute: bool,
    fatigue: int = 0,
    coach_quality: int = 3,
    specialty_matches: bool = False,
    chemistry_mult: float = 1.0,
    sparring_bonus: float = 0.0,
    private_lessons: bool = False,
) -> int:
    """Calculate training gain for one attribute for one week."""
    gain = base_gain
    
    # Age modifier
    age_cat = get_age_category(age)
    gain *= AGE_GAIN_MODIFIER[age_cat]
    
    # Facility bonus
    gain *= calculate_facility_bonus(facility_tier)
    
    # Intensity multiplier
    gain *= INTENSITY_GAIN_MULTIPLIER[intensity]
    
    # Focus bonus (training specifically for this)
    if is_focus_attribute:
        gain *= 1.3
    
    # Coach quality bonus
    coach_bonus = {1: 0.6, 2: 0.8, 3: 1.0, 4: 1.2, 5: 1.5}.get(coach_quality, 1.0)
    gain *= coach_bonus
    
    # Specialty match bonus (+25%)
    if specialty_matches and is_focus_attribute:
        gain *= 1.25
    
    # Chemistry multiplier
    gain *= chemistry_mult
    
    # Sparring bonus
    gain *= (1 + sparring_bonus)
    
    # Private lessons bonus (+20%)
    if private_lessons:
        gain *= 1.20
    
    # Diminishing returns
    gain *= calculate_diminishing_returns(current_value)
    
    # Fatigue penalty
    fatigue_penalty = 1.0 - (fatigue / 200)
    gain *= max(0.3, fatigue_penalty)
    
    # Random variance (Â±20%)
    variance = random.uniform(0.8, 1.2)
    gain *= variance
    
    return max(0, int(gain))


def check_training_injury(
    intensity: TrainingIntensity,
    fatigue: int,
    is_injury_prone: bool = False,
) -> Tuple[bool, str]:
    """
    Check if training injury occurs.
    
    Returns:
        Tuple of (injury_occurred, injury_type)
    """
    base_risk = INTENSITY_INJURY_RISK[intensity]
    fatigue_risk = fatigue / 500  # +20% at 100 fatigue
    
    if is_injury_prone:
        base_risk *= 1.5
    
    total_risk = base_risk + fatigue_risk
    
    if random.random() < total_risk:
        injuries = [
            "Minor muscle strain",
            "Tweaked knee",
            "Shoulder inflammation",
            "Back tightness",
            "Sparring cut",
        ]
        return True, random.choice(injuries)
    
    return False, ""


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def format_camp_status(camp: ActiveTrainingCamp) -> List[str]:
    """Format training camp status for display."""
    focus_info = FOCUS_INFO.get(camp.focus, {"icon": "ðŸ¥Š", "name": camp.focus.value})
    intensity_info = INTENSITY_INFO.get(camp.intensity, {"icon": "ðŸŸ¡", "name": camp.intensity.value})
    
    lines = [
        "â•" * 50,
        f"  TRAINING CAMP: {camp.fighter_name}",
        "â•" * 50,
        f"  Focus: {focus_info['icon']} {focus_info['name']}",
        f"  Intensity: {intensity_info['icon']} {intensity_info['name']}",
        f"  Facility: {camp.facility_tier} (Cap: {FACILITY_STAT_CAPS.get(camp.facility_tier, 100)})",
        "",
        f"  Progress: {camp.weeks_completed}/{camp.total_weeks} weeks ({camp.progress_percent:.0f}%)",
        f"  {_progress_bar(camp.progress_percent, 30)}",
        "",
        f"  Total Gains: +{camp.sum_total_gains} points",
    ]
    
    if camp.total_gains:
        lines.append("  Improved:")
        for attr, gain in sorted(camp.total_gains.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"    {attr}: +{gain}")
    
    # Show events
    if camp.positive_events or camp.negative_events:
        lines.append("")
        lines.append(f"  Events: {camp.positive_events} positive, {camp.negative_events} negative")
    
    if camp.injuries > 0:
        lines.append(f"\n  âš ï¸ Injuries: {camp.injuries}")
    
    lines.append("â•" * 50)
    return lines


def format_camp_journal(journal: CampJournal) -> List[str]:
    """Format the camp journal for display."""
    lines = []
    
    lines.append("â•" * 60)
    lines.append(f"CAMP JOURNAL: {journal.fighter_name}")
    lines.append(f"Focus: {journal.focus} | Coach: {journal.coach_name} | Started: Week {journal.camp_start_week}")
    lines.append("â•" * 60)
    
    # Group entries by week
    max_week = max([e.week_number for e in journal.entries]) if journal.entries else 0
    
    for week in range(1, max_week + 1):
        week_entries = journal.get_entries_for_week(week)
        if not week_entries:
            continue
        
        lines.append("")
        lines.append(f"WEEK {week} (Week {journal.camp_start_week + week - 1})")
        
        for entry in week_entries:
            icon = entry.icon or "ðŸ“‹"
            
            if entry.entry_type == JournalEntryType.TRAINING:
                if entry.stat_changes:
                    gains_str = ", ".join(f"+{v} {k}" for k, v in entry.stat_changes.items() if v > 0)
                    lines.append(f"  {icon} [TRAINING] {gains_str}")
                else:
                    lines.append(f"  {icon} [TRAINING] Rest week")
            
            elif entry.entry_type == JournalEntryType.EVENT:
                lines.append(f"  {icon} [EVENT] {entry.headline}")
                if entry.description:
                    lines.append(f"       {entry.description}")
                if entry.stat_changes:
                    for attr, change in entry.stat_changes.items():
                        sign = "+" if change > 0 else ""
                        lines.append(f"       {sign}{change} {attr}")
            
            elif entry.entry_type == JournalEntryType.INJURY:
                lines.append(f"  {icon} [INJURY] {entry.description}")
            
            elif entry.entry_type == JournalEntryType.TRANSACTION:
                lines.append(f"  {icon} [TRANSACTION] {entry.headline}")
                if entry.description:
                    lines.append(f"       {entry.description}")
            
            elif entry.entry_type == JournalEntryType.SPARRING:
                lines.append(f"  {icon} [SPARRING] {entry.headline}")
                if entry.description:
                    lines.append(f"       {entry.description}")
            
            elif entry.entry_type == JournalEntryType.MILESTONE:
                lines.append(f"  {icon} [MILESTONE] {entry.headline}")
    
    # Summary
    lines.append("")
    lines.append("â”€" * 60)
    lines.append("CAMP SUMMARY")
    
    if journal.total_gains:
        gains_str = ", ".join(f"+{v} {k}" for k, v in sorted(journal.total_gains.items(), key=lambda x: -x[1]))
        lines.append(f"  Total Gains: {gains_str}")
    
    lines.append(f"  Events: {journal.positive_events} positive, {journal.negative_events} negative, {journal.neutral_events} neutral")
    
    if journal.injuries > 0:
        lines.append(f"  Injuries: {journal.injuries}")
    
    if journal.money_earned > 0 or journal.money_spent > 0:
        lines.append(f"  Money: +${journal.money_earned:,} earned, -${journal.money_spent:,} spent")
    
    rating_text, stars = journal.get_camp_rating()
    star_display = "â˜…" * stars + "â˜†" * (5 - stars)
    lines.append(f"\n  Camp Rating: {star_display} {rating_text}")
    lines.append("â”€" * 60)
    
    return lines


def _progress_bar(percent: float, width: int = 20) -> str:
    """Create a text progress bar."""
    filled = int(width * percent / 100)
    empty = width - filled
    return f"[{'â–ˆ' * filled}{'â–‘' * empty}]"


def format_week_result(result: TrainingWeekResult) -> List[str]:
    """Format weekly training result."""
    lines = [
        f"â”€â”€â”€ Week {result.week_number} Complete â”€â”€â”€",
    ]
    
    if result.gains:
        lines.append("  Improvements:")
        for attr, gain in result.gains.items():
            cap_note = " (CAPPED)" if attr in result.capped_attributes else ""
            lines.append(f"    {attr}: +{gain}{cap_note}")
        lines.append(f"  Total: +{result.total_gains}")
    else:
        lines.append("  No gains this week")
    
    if result.had_event:
        icon = EVENT_ICONS.get(result.event_category, "ðŸ“‹")
        lines.append(f"\n  {icon} EVENT: {result.event_headline}")
        if result.event_description:
            lines.append(f"     {result.event_description}")
    
    if result.injury_occurred:
        lines.append(f"\n  ðŸ¥ INJURY: {result.injury_type}")
    
    lines.append(f"  Fatigue: +{result.fatigue_added}")
    
    return lines


def format_camp_summary(camp: ActiveTrainingCamp) -> List[str]:
    """Format completed camp summary."""
    rating_text = "GOOD"
    stars = 3
    
    if camp.journal:
        rating_text, stars = camp.journal.get_camp_rating()
    else:
        # Estimate rating from gains
        total = camp.sum_total_gains
        if total >= 25:
            rating_text, stars = "EXCELLENT", 5
        elif total >= 18:
            rating_text, stars = "GREAT", 4
        elif total >= 12:
            rating_text, stars = "GOOD", 3
        elif total >= 6:
            rating_text, stars = "FAIR", 2
        else:
            rating_text, stars = "POOR", 1
    
    star_display = "â˜…" * stars + "â˜†" * (5 - stars)
    focus_info = FOCUS_INFO.get(camp.focus, {"name": camp.focus.value})
    
    lines = [
        "",
        "â•”" + "â•" * 48 + "â•—",
        "â•‘" + " TRAINING CAMP COMPLETE ".center(48) + "â•‘",
        "â• " + "â•" * 48 + "â•£",
        f"â•‘  Fighter: {camp.fighter_name}".ljust(49) + "â•‘",
        f"â•‘  Focus: {focus_info['name']}".ljust(49) + "â•‘",
        f"â•‘  Duration: {camp.weeks_completed} weeks".ljust(49) + "â•‘",
        "â• " + "â•" * 48 + "â•£",
        f"â•‘  TOTAL GAINS: +{camp.sum_total_gains} attribute points".ljust(49) + "â•‘",
        "â• " + "â•" * 48 + "â•£",
    ]
    
    if camp.total_gains:
        lines.append("â•‘  Attribute Improvements:".ljust(49) + "â•‘")
        for attr, gain in sorted(camp.total_gains.items(), key=lambda x: -x[1]):
            lines.append(f"â•‘    {attr}: +{gain}".ljust(49) + "â•‘")
    
    if camp.positive_events or camp.negative_events:
        lines.append("â• " + "â•" * 48 + "â•£")
        lines.append(f"â•‘  Events: {camp.positive_events} positive, {camp.negative_events} negative".ljust(49) + "â•‘")
    
    if camp.injuries > 0:
        lines.append("â• " + "â•" * 48 + "â•£")
        lines.append(f"â•‘  âš ï¸ Training Injuries: {camp.injuries}".ljust(49) + "â•‘")
    
    lines.append("â• " + "â•" * 48 + "â•£")
    lines.append(f"â•‘  Camp Rating: {star_display} {rating_text}".ljust(49) + "â•‘")
    lines.append("â•š" + "â•" * 48 + "â•")
    lines.append("")
    
    return lines


def get_focus_options() -> List[Tuple[str, TrainingFocus]]:
    """Get (display_name, focus) list for menus."""
    return [
        (f"{FOCUS_INFO[f]['icon']} {FOCUS_INFO[f]['name']}", f)
        for f in TrainingFocus
        if f in FOCUS_INFO
    ]


def get_intensity_options() -> List[Tuple[str, TrainingIntensity]]:
    """Get (display_name, intensity) list for menus."""
    return [
        (f"{INTENSITY_INFO[i]['icon']} {INTENSITY_INFO[i]['name']} ({INTENSITY_INFO[i]['gains']} gains)", i)
        for i in TrainingIntensity
    ]


# ============================================================================
# AI TEMPLATE SELECTION
# ============================================================================

def select_ai_template(
    fighter_overall: int,
    opponent_overall: int,
    fighter_age: int,
    fighter_fatigue: int,
    camp_weeks: int,
    is_title_fight: bool = False,
    fighter_traits: Optional[List[str]] = None,
    fighter_rank: Optional[int] = None,
    is_champion: bool = False,
    coming_off_injury: bool = False,
) -> CampTemplate:
    """
    AI selects the best template based on situation.
    """
    traits = fighter_traits or []
    
    # Initialize scores
    scores = {
        CampTemplate.STEADY: 40,
        CampTemplate.PEAK_LATE: 25,
        CampTemplate.FRONT_LOAD: 20,
        CampTemplate.GRINDER: 15,
        CampTemplate.CAUTIOUS: 10,
    }
    
    skill_gap = fighter_overall - opponent_overall
    
    # === GRINDER factors (push hard) ===
    if skill_gap > 15:
        scores[CampTemplate.GRINDER] += 25
    if fighter_age < 26:
        scores[CampTemplate.GRINDER] += 15
    if "Cardio Machine" in traits:
        scores[CampTemplate.GRINDER] += 20
    if "Gym Rat" in traits:
        scores[CampTemplate.GRINDER] += 15
    if "Durable" in traits:
        scores[CampTemplate.GRINDER] += 10
    if fighter_fatigue < 15:
        scores[CampTemplate.GRINDER] += 10
    
    # === PEAK_LATE factors (big stage) ===
    if is_title_fight:
        scores[CampTemplate.PEAK_LATE] += 30
    if is_champion:
        scores[CampTemplate.PEAK_LATE] += 15
    if fighter_rank and fighter_rank <= 5:
        scores[CampTemplate.PEAK_LATE] += 15
    if camp_weeks >= 8:
        scores[CampTemplate.PEAK_LATE] += 10
    
    # === FRONT_LOAD factors (arrive fresh) ===
    if camp_weeks <= 5:
        scores[CampTemplate.FRONT_LOAD] += 25
    if fighter_fatigue > 30 and fighter_fatigue <= 50:
        scores[CampTemplate.FRONT_LOAD] += 20
    if skill_gap > 10:
        scores[CampTemplate.FRONT_LOAD] += 10
    
    # === CAUTIOUS factors (protect yourself) ===
    if fighter_fatigue > 50:
        scores[CampTemplate.CAUTIOUS] += 35
    if "Injury Prone" in traits:
        scores[CampTemplate.CAUTIOUS] += 25
    if fighter_age > 35:
        scores[CampTemplate.CAUTIOUS] += 20
    if coming_off_injury:
        scores[CampTemplate.CAUTIOUS] += 30
    
    # === STEADY factors (reliable) ===
    if abs(skill_gap) < 5:
        scores[CampTemplate.STEADY] += 20
    if fighter_age >= 28 and fighter_age <= 32:
        scores[CampTemplate.STEADY] += 10
    if camp_weeks >= 8:
        scores[CampTemplate.STEADY] += 10
    
    # === Negative modifiers ===
    if is_title_fight:
        scores[CampTemplate.GRINDER] -= 20
    if fighter_fatigue > 40:
        scores[CampTemplate.GRINDER] -= 25
    if "Injury Prone" in traits:
        scores[CampTemplate.GRINDER] -= 30
    if fighter_age > 33:
        scores[CampTemplate.GRINDER] -= 15
    if camp_weeks <= 4:
        scores[CampTemplate.PEAK_LATE] -= 15
    if skill_gap < -10:
        scores[CampTemplate.CAUTIOUS] -= 15
    
    # Add randomness for variety
    for template in scores:
        scores[template] += random.randint(-10, 10)
    
    # Return highest scoring template
    return max(scores, key=scores.get)


# ============================================================================
# COACH INTERVENTION
# ============================================================================

@dataclass
class CoachIntervention:
    """Coach intervention warning during camp."""
    fighter_id: str
    fighter_name: str
    current_week: int
    current_fatigue: int
    projected_fatigue: int
    scheduled_intensity: TrainingIntensity
    message: str
    severity: str  # "warning" or "danger"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "current_week": self.current_week,
            "current_fatigue": self.current_fatigue,
            "projected_fatigue": self.projected_fatigue,
            "scheduled_intensity": self.scheduled_intensity.value,
            "message": self.message,
            "severity": self.severity,
        }


def check_for_intervention(
    fighter_id: str,
    fighter_name: str,
    current_fatigue: int,
    scheduled_intensity: TrainingIntensity,
    current_week: int,
    coach_name: str = "Coach",
) -> Optional[CoachIntervention]:
    """
    Check if coach should intervene about dangerous fatigue levels.
    """
    # Only intervene for intense training
    if scheduled_intensity not in [TrainingIntensity.INTENSE, TrainingIntensity.EXTREME]:
        return None
    
    # Calculate projected fatigue
    fatigue_add = INTENSITY_FATIGUE.get(scheduled_intensity, 10)
    projected = current_fatigue + fatigue_add
    
    # Danger threshold: will be exhausted
    if projected > 80:
        return CoachIntervention(
            fighter_id=fighter_id,
            fighter_name=fighter_name,
            current_week=current_week,
            current_fatigue=current_fatigue,
            projected_fatigue=projected,
            scheduled_intensity=scheduled_intensity,
            message=f"{coach_name} is concerned: {fighter_name} is approaching exhaustion. "
                    f"Continuing {scheduled_intensity.value} training could seriously impact fight performance.",
            severity="danger",
        )
    
    # Warning threshold: will be tired
    elif projected > 65:
        return CoachIntervention(
            fighter_id=fighter_id,
            fighter_name=fighter_name,
            current_week=current_week,
            current_fatigue=current_fatigue,
            projected_fatigue=projected,
            scheduled_intensity=scheduled_intensity,
            message=f"{coach_name} advises caution: {fighter_name}'s fatigue is building up. "
                    f"Consider easing off to arrive fresher for the fight.",
            severity="warning",
        )
    
    return None


# ============================================================================
# TEMPLATE DISPLAY HELPERS
# ============================================================================

def get_template_options(
    fighter_fatigue: int = 0,
    camp_weeks: int = 8,
) -> List[Dict[str, Any]]:
    """
    Get template options for menu display.
    """
    options = []
    
    for i, template in enumerate(CampTemplate, 1):
        info = TEMPLATE_INFO[template]
        min_fat, expected_fat, max_fat = estimate_template_fatigue(template, camp_weeks)
        
        # Calculate projected final fatigue
        projected_final = fighter_fatigue + expected_fat
        
        # Determine arrival condition
        if projected_final <= 20:
            arrival = "Fresh"
        elif projected_final <= 40:
            arrival = "Rested"
        elif projected_final <= 60:
            arrival = "Ready"
        elif projected_final <= 80:
            arrival = "Tired"
        else:
            arrival = "Exhausted"
        
        options.append({
            "key": str(i),
            "template": template,
            "name": info["name"],
            "icon": info["icon"],
            "description": info["description"],
            "risk": info["risk"],
            "gains": info["gains"],
            "pattern": info["pattern"],
            "fatigue_range": f"+{min_fat} to +{max_fat}",
            "expected_fatigue": expected_fat,
            "projected_arrival": arrival,
            "projected_final_fatigue": projected_final,
        })
    
    return options


def format_schedule_preview(schedule: List[TrainingIntensity]) -> str:
    """Format a schedule for display."""
    symbols = {
        TrainingIntensity.REST: "REST",
        TrainingIntensity.LIGHT: "LIGHT",
        TrainingIntensity.MODERATE: "MOD",
        TrainingIntensity.INTENSE: "INT",
        TrainingIntensity.EXTREME: "EXT",
    }
    parts = [symbols.get(i, "?") for i in schedule]
    return " → ".join(parts)


def format_template_menu(fighter_fatigue: int = 0, camp_weeks: int = 8) -> List[str]:
    """Format template options for CLI menu display."""
    lines = []
    options = get_template_options(fighter_fatigue, camp_weeks)
    
    for opt in options:
        lines.append(f"[{opt['key']}] {opt['icon']} {opt['name']}")
        lines.append(f"    {opt['description']}")
        lines.append(f"    Risk: {opt['risk']} | Gains: {opt['gains']}")
        lines.append(f"    Est. Fatigue: {opt['fatigue_range']} | Arrival: {opt['projected_arrival']}")
        lines.append("")
    
    return lines


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "TrainingFocus", "TrainingIntensity", "JournalEntryType", "CampTemplate",
    
    # Data classes
    "FighterTrainingInfo", "TrainingWeekResult", "ActiveTrainingCamp",
    "CampJournalEntry", "CampJournal", "CoachIntervention",
    
    # Template functions
    "generate_schedule", "estimate_template_fatigue", "select_ai_template",
    "get_template_options", "format_schedule_preview", "format_template_menu",
    "get_fatigue_with_variance",
    
    # Coach intervention
    "check_for_intervention",
    
    # Calculations
    "calculate_weekly_gain", "apply_facility_cap",
    "calculate_diminishing_returns", "check_training_injury",
    "get_age_category", "calculate_facility_bonus",
    
    # Display
    "format_camp_status", "format_week_result", 
    "format_camp_summary", "format_camp_journal",
    "get_focus_options", "get_intensity_options",
    
    # Constants
    "FOCUS_ATTRIBUTES", "FOCUS_INFO", "INTENSITY_INFO", "TEMPLATE_INFO",
    "FACILITY_STAT_CAPS", "DEFAULT_CAMP_WEEKS", "INTENSITY_FATIGUE",
    "INTENSITY_FATIGUE_VARIANCE", "EVENT_ICONS",
]
