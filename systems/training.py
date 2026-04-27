# systems/training.py
# Module: Enhanced Training System
# Lines: ~1,450
#
# Fighters improve through structured training camps with coach integration,
# sparring partners, private lessons, and dynamic training events.

"""
Cage Dynasty - Enhanced Training System

This module handles fighter development through training:
- Training camps (8-week fight preparation)
- Coach specialty matching and trait bonuses
- Automatic sparring partner bonuses
- Private lessons (coach focuses on one fighter)
- Dynamic training events (breakthroughs, setbacks, flavor)
- Attribute improvement with multiple factors
- Camp Journal for tracking all events

Training effectiveness depends on:
- Camp tier (facilities)
- Coach quality and specialty
- Coach-fighter chemistry
- Sparring partners in camp
- Private lessons
- Fighter age and potential
- Current attribute level (diminishing returns)
- Training intensity

USAGE:
    from systems.training import (
        TrainingSystem, TrainingCamp, TrainingFocus,
        TrainingEvent, calculate_training_gain,
        calculate_sparring_bonus, get_private_lesson_assignments
    )
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import random

# Try to import from package structure, fall back to flat
try:
    from core.types import (
        EventType, CampTier,
        PHYSICAL_ATTRIBUTES, STRIKING_ATTRIBUTES,
        GRAPPLING_ATTRIBUTES, MENTAL_ATTRIBUTES,
        ALL_ATTRIBUTES
    )
    from core.calendar import GameDate, calendar
    from core.events import emit
    from core.config import get_config
except ImportError:
    try:
        from types import (
            EventType, CampTier,
            PHYSICAL_ATTRIBUTES, STRIKING_ATTRIBUTES,
            GRAPPLING_ATTRIBUTES, MENTAL_ATTRIBUTES,
            ALL_ATTRIBUTES
        )
        from calendar import GameDate, calendar
        from events import emit
        from config import get_config
    except ImportError:
        # Minimal fallback for testing
        class EventType(Enum):
            TRAINING_STARTED = auto()
            TRAINING_COMPLETED = auto()
            TRAINING_EVENT = auto()
        
        class CampTier(Enum):
            GARAGE = 1
            LOCAL = 2
            REGIONAL = 3
            NATIONAL = 4
            ELITE = 5
        
        # 17-attribute system
        PHYSICAL_ATTRIBUTES = ["strength", "speed", "cardio", "chin", "recovery"]
        STRIKING_ATTRIBUTES = ["boxing", "kicks", "clinch_striking", "striking_defense"]
        GRAPPLING_ATTRIBUTES = ["takedowns", "takedown_defense", "top_control", "submissions", "guard"]
        MENTAL_ATTRIBUTES = ["heart", "fight_iq", "composure"]
        ALL_ATTRIBUTES = PHYSICAL_ATTRIBUTES + STRIKING_ATTRIBUTES + GRAPPLING_ATTRIBUTES + MENTAL_ATTRIBUTES
        
        class GameDate:
            def __init__(self, year=1, month=1, day=1):
                self.year = year
                self.month = month
                self.day = day
        
        class MockCalendar:
            current_date = GameDate()
        calendar = MockCalendar()
        
        def emit(event_type, data):
            pass
        
        def get_config(key, default):
            return default


# ============================================================================
# TRAINING FOCUS
# ============================================================================

class TrainingFocus(Enum):
    """
    Areas a fighter can focus training on.
    
    Each focus improves specific attributes:
    - STRIKING: Stand-up fighting (boxing, kicks, defense)
    - WRESTLING: Takedowns and control (wrestling, TD defense, clinch)
    - JIUJITSU: Ground submissions (BJJ, submissions, guard)
    - CONDITIONING: Gas tank and recovery (cardio, recovery)
    - STRENGTH_POWER: Raw athleticism (strength, speed, power)
    - BALANCED: All attributes (smaller gains each)
    - FIGHT_SPECIFIC: Tailored to opponent weaknesses
    """
    STRIKING = "Striking"
    WRESTLING = "Wrestling"
    JIUJITSU = "Jiu-Jitsu"
    CONDITIONING = "Conditioning"
    STRENGTH_POWER = "Strength & Power"
    BALANCED = "Balanced"
    FIGHT_SPECIFIC = "Fight Specific"


# Focus to attribute mapping - what each focus improves (17-attribute system)
FOCUS_ATTRIBUTES: Dict[TrainingFocus, List[str]] = {
    TrainingFocus.STRIKING: [
        "boxing", "kicks", "clinch_striking", "striking_defense"
    ],
    TrainingFocus.WRESTLING: [
        "takedowns", "takedown_defense", "top_control"
    ],
    TrainingFocus.JIUJITSU: [
        "submissions", "guard", "takedown_defense"
    ],
    TrainingFocus.CONDITIONING: [
        "cardio", "recovery"
    ],
    TrainingFocus.STRENGTH_POWER: [
        "strength", "speed", "chin"
    ],
    TrainingFocus.BALANCED: [
        "boxing", "kicks", "takedowns", "submissions", "cardio", 
        "strength", "speed", "takedown_defense"
    ],
    TrainingFocus.FIGHT_SPECIFIC: [],  # Determined by opponent analysis
}

# Descriptions for each training focus
FOCUS_DESCRIPTIONS: Dict[TrainingFocus, str] = {
    TrainingFocus.STRIKING: "Hands, kicks, head movement, defense",
    TrainingFocus.WRESTLING: "Takedowns, sprawls, cage control, top position",
    TrainingFocus.JIUJITSU: "Submissions, sweeps, guard work, getting back up",
    TrainingFocus.CONDITIONING: "Cardio, gas tank, between-round recovery",
    TrainingFocus.STRENGTH_POWER: "Raw power, explosiveness, speed, durability",
    TrainingFocus.BALANCED: "Well-rounded camp, smaller gains in all areas",
    TrainingFocus.FIGHT_SPECIFIC: "Tailored to exploit opponent's weaknesses",
}


# ============================================================================
# COACH SPECIALTY MATCHING
# ============================================================================

class CoachSpecialty(Enum):
    """Coach specialization areas - matches with TrainingFocus."""
    STRIKING = "Striking"
    WRESTLING = "Wrestling"
    JIU_JITSU = "Jiu-Jitsu"
    CONDITIONING = "Conditioning"
    STRENGTH = "Strength"
    CORNERING = "Cornering"


# Which coach specialties match which training focuses
SPECIALTY_TO_FOCUS: Dict[str, List[TrainingFocus]] = {
    "STRIKING": [TrainingFocus.STRIKING],
    "Striking": [TrainingFocus.STRIKING],
    "WRESTLING": [TrainingFocus.WRESTLING],
    "Wrestling": [TrainingFocus.WRESTLING],
    "JIU_JITSU": [TrainingFocus.JIUJITSU],
    "Jiu-Jitsu": [TrainingFocus.JIUJITSU],
    "CONDITIONING": [TrainingFocus.CONDITIONING],
    "Conditioning": [TrainingFocus.CONDITIONING],
    "STRENGTH": [TrainingFocus.STRENGTH_POWER],
    "Strength": [TrainingFocus.STRENGTH_POWER],
    "CORNERING": [],  # Cornering helps in fights, not training
    "Cornering": [],
}

def coach_specialty_matches_focus(specialty: str, focus: TrainingFocus) -> bool:
    """Check if a coach's specialty matches the training focus."""
    if specialty is None:
        return False
    
    # Normalize specialty string
    specialty_str = str(specialty)
    if hasattr(specialty, 'value'):
        specialty_str = specialty.value
    elif hasattr(specialty, 'name'):
        specialty_str = specialty.name
    
    matching_focuses = SPECIALTY_TO_FOCUS.get(specialty_str, [])
    return focus in matching_focuses


# ============================================================================
# TRAINING INTENSITY
# ============================================================================

class TrainingIntensity(Enum):
    """How hard the fighter trains"""
    REST = 0        # Full rest, no training, fatigue recovery
    LIGHT = 1       # Recovery focused, minimal gains
    MODERATE = 2    # Standard training
    INTENSE = 3     # Hard training, good gains, fatigue risk
    EXTREME = 4     # Maximum effort, injury risk


INTENSITY_MULTIPLIERS = {
    TrainingIntensity.REST: 0.0,
    TrainingIntensity.LIGHT: 0.5,
    TrainingIntensity.MODERATE: 1.0,
    TrainingIntensity.INTENSE: 1.5,
    TrainingIntensity.EXTREME: 2.0,
}

INTENSITY_FATIGUE = {
    TrainingIntensity.REST: -15,    # Recovery! Reduces fatigue
    TrainingIntensity.LIGHT: 2,
    TrainingIntensity.MODERATE: 5,
    TrainingIntensity.INTENSE: 10,
    TrainingIntensity.EXTREME: 18,
}

INTENSITY_INJURY_RISK = {
    TrainingIntensity.REST: 0.0,
    TrainingIntensity.LIGHT: 0.0,
    TrainingIntensity.MODERATE: 0.01,
    TrainingIntensity.INTENSE: 0.03,
    TrainingIntensity.EXTREME: 0.08,
}

# Variance for fatigue (adds randomness to each week)
INTENSITY_FATIGUE_VARIANCE = {
    TrainingIntensity.REST: 3,      # -18 to -12
    TrainingIntensity.LIGHT: 1,     # 1 to 3
    TrainingIntensity.MODERATE: 2,  # 3 to 7
    TrainingIntensity.INTENSE: 3,   # 7 to 13
    TrainingIntensity.EXTREME: 4,   # 14 to 22
}


def get_fatigue_with_variance(intensity: TrainingIntensity) -> int:
    """Get fatigue change with random variance."""
    import random
    base = INTENSITY_FATIGUE.get(intensity, 5)
    variance = INTENSITY_FATIGUE_VARIANCE.get(intensity, 2)
    return base + random.randint(-variance, variance)


# ============================================================================
# CAMP TEMPLATES
# ============================================================================

class CampTemplate(Enum):
    """Training camp strategy templates."""
    STEADY = "Steady Build"
    PEAK_LATE = "Hard Finish"
    FRONT_LOAD = "Fast Start"
    GRINDER = "No Days Off"
    CAUTIOUS = "Recovery Camp"


TEMPLATE_INFO: Dict['CampTemplate', Dict[str, Any]] = {
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


def generate_camp_schedule(template: CampTemplate, weeks: int) -> List[TrainingIntensity]:
    """
    Generate a week-by-week intensity schedule for a template.
    Scales to any camp duration (4-12 weeks).
    """
    weeks = max(4, min(12, weeks))
    
    if template == CampTemplate.STEADY:
        return _generate_steady_schedule(weeks)
    elif template == CampTemplate.PEAK_LATE:
        return _generate_peak_late_schedule(weeks)
    elif template == CampTemplate.FRONT_LOAD:
        return _generate_front_load_schedule(weeks)
    elif template == CampTemplate.GRINDER:
        return _generate_grinder_schedule(weeks)
    elif template == CampTemplate.CAUTIOUS:
        return _generate_cautious_schedule(weeks)
    else:
        return _generate_steady_schedule(weeks)


def _generate_steady_schedule(weeks: int) -> List[TrainingIntensity]:
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


def _generate_peak_late_schedule(weeks: int) -> List[TrainingIntensity]:
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


def _generate_front_load_schedule(weeks: int) -> List[TrainingIntensity]:
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


def _generate_grinder_schedule(weeks: int) -> List[TrainingIntensity]:
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


def _generate_cautious_schedule(weeks: int) -> List[TrainingIntensity]:
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


def estimate_template_fatigue(template: CampTemplate, weeks: int) -> Tuple[int, int, int]:
    """
    Estimate total fatigue for a template.
    Returns (min, expected, max).
    """
    schedule = generate_camp_schedule(template, weeks)
    
    total_base = 0
    total_variance = 0
    
    for intensity in schedule:
        total_base += INTENSITY_FATIGUE.get(intensity, 5)
        total_variance += INTENSITY_FATIGUE_VARIANCE.get(intensity, 2)
    
    return (total_base - total_variance, total_base, total_base + total_variance)


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
    """AI selects the best template based on situation."""
    traits = fighter_traits or []
    
    scores = {
        CampTemplate.STEADY: 40,
        CampTemplate.PEAK_LATE: 25,
        CampTemplate.FRONT_LOAD: 20,
        CampTemplate.GRINDER: 15,
        CampTemplate.CAUTIOUS: 10,
    }
    
    skill_gap = fighter_overall - opponent_overall
    
    # GRINDER factors
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
    
    # PEAK_LATE factors
    if is_title_fight:
        scores[CampTemplate.PEAK_LATE] += 30
    if is_champion:
        scores[CampTemplate.PEAK_LATE] += 15
    if fighter_rank and fighter_rank <= 5:
        scores[CampTemplate.PEAK_LATE] += 15
    if camp_weeks >= 8:
        scores[CampTemplate.PEAK_LATE] += 10
    
    # FRONT_LOAD factors
    if camp_weeks <= 5:
        scores[CampTemplate.FRONT_LOAD] += 25
    if fighter_fatigue > 30 and fighter_fatigue <= 50:
        scores[CampTemplate.FRONT_LOAD] += 20
    if skill_gap > 10:
        scores[CampTemplate.FRONT_LOAD] += 10
    
    # CAUTIOUS factors
    if fighter_fatigue > 50:
        scores[CampTemplate.CAUTIOUS] += 35
    if "Injury Prone" in traits:
        scores[CampTemplate.CAUTIOUS] += 25
    if fighter_age > 35:
        scores[CampTemplate.CAUTIOUS] += 20
    if coming_off_injury:
        scores[CampTemplate.CAUTIOUS] += 30
    
    # STEADY factors
    if abs(skill_gap) < 5:
        scores[CampTemplate.STEADY] += 20
    if 28 <= fighter_age <= 32:
        scores[CampTemplate.STEADY] += 10
    if camp_weeks >= 8:
        scores[CampTemplate.STEADY] += 10
    
    # Negative modifiers
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
    
    # Add randomness
    for template in scores:
        scores[template] += random.randint(-10, 10)
    
    return max(scores, key=scores.get)


# ============================================================================
# TRAINING EVENTS
# ============================================================================

class TrainingEventType(Enum):
    """Types of training events that can occur."""
    # Positive events
    BREAKTHROUGH = "breakthrough"
    COACH_INSIGHT = "coach_insight"
    PERFECT_WEEK = "perfect_week"
    FILM_STUDY = "film_study"
    CONDITIONING_BREAKTHROUGH = "conditioning_breakthrough"
    TIMING_IMPROVED = "timing_improved"
    SUBMISSION_SAVVY = "submission_savvy"
    TAKEDOWN_TIMING = "takedown_timing"
    MENTAL_EDGE = "mental_edge"
    POWER_INCREASE = "power_increase"
    EARLY_PEAK = "early_peak"
    GREAT_CHEMISTRY = "great_chemistry"
    INSPIRED_TRAINING = "inspired_training"
    VETERAN_WISDOM = "veteran_wisdom"
    YOUNG_HUNGER = "young_hunger"
    
    # Negative events
    MINOR_TWEAK = "minor_tweak"
    OVERTRAINING = "overtraining"
    OFF_WEEK = "off_week"
    CAMP_FRICTION = "camp_friction"
    MINOR_ILLNESS = "minor_illness"
    BAD_SPARRING = "bad_sparring"
    FOCUS_CONFUSION = "focus_confusion"
    NAGGING_PAIN = "nagging_pain"
    WEIGHT_CUT_ISSUES = "weight_cut_issues"
    MENTAL_BLOCK = "mental_block"
    
    # Neutral/Flavor events
    HARD_SPARRING = "hard_sparring"
    REST_DAY_CALLED = "rest_day_called"
    TECHNIQUE_FOCUS = "technique_focus"
    CARDIO_DAY = "cardio_day"
    PAD_WORK = "pad_work"
    GRAPPLING_DAY = "grappling_day"
    STRATEGY_SESSION = "strategy_session"
    LIGHT_WEEK = "light_week"
    MEDIA_DAY = "media_day"
    CAMP_VISITOR = "camp_visitor"
    NEW_DRILL = "new_drill"
    MORNING_RUN = "morning_run"


@dataclass
class TrainingEvent:
    """A training event that occurred during camp."""
    event_type: TrainingEventType
    category: str  # "positive", "negative", "neutral"
    headline: str
    description: str
    stat_changes: Dict[str, int] = field(default_factory=dict)
    skip_week: bool = False
    gains_modifier: float = 1.0  # Multiplier for this week's gains
    fatigue_change: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "category": self.category,
            "headline": self.headline,
            "description": self.description,
            "stat_changes": self.stat_changes.copy(),
            "skip_week": self.skip_week,
            "gains_modifier": self.gains_modifier,
            "fatigue_change": self.fatigue_change,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingEvent':
        return cls(
            event_type=TrainingEventType(data["event_type"]),
            category=data["category"],
            headline=data["headline"],
            description=data["description"],
            stat_changes=data.get("stat_changes", {}),
            skip_week=data.get("skip_week", False),
            gains_modifier=data.get("gains_modifier", 1.0),
            fatigue_change=data.get("fatigue_change", 0),
        )


# Event definitions with base chances and conditions
TRAINING_EVENTS = {
    # ===== POSITIVE EVENTS =====
    TrainingEventType.BREAKTHROUGH: {
        "base_chance": 0.05,
        "category": "positive",
        "conditions": ["young_or_high_chemistry"],
        "headline": "{fighter} has a breakthrough!",
        "description": "Something clicks for {fighter}. {coach} has been drilling this for weeks.",
        "stat_changes": {"focus_random": (2, 3)},
    },
    TrainingEventType.COACH_INSIGHT: {
        "base_chance": 0.06,
        "category": "positive",
        "conditions": ["coach_quality_3_plus"],
        "headline": "Coach spots a flaw",
        "description": "{coach} identifies a weakness and fixes it. +{gain} {attribute}",
        "stat_changes": {"weakness_random": (1, 2)},
    },
    TrainingEventType.PERFECT_WEEK: {
        "base_chance": 0.04,
        "category": "positive",
        "conditions": ["moderate_intensity"],
        "headline": "Perfect training week",
        "description": "Everything clicks. Best training week of camp.",
        "gains_modifier": 1.5,
    },
    TrainingEventType.FILM_STUDY: {
        "base_chance": 0.05,
        "category": "positive",
        "conditions": ["analytical_coach"],
        "headline": "Film study pays off",
        "description": "Hours of film work. {fighter} knows the opponent cold.",
        "stat_changes": {"fight_iq": (1, 1)},
    },
    TrainingEventType.CONDITIONING_BREAKTHROUGH: {
        "base_chance": 0.04,
        "category": "positive",
        "conditions": ["conditioning_focus"],
        "headline": "Conditioning breakthrough",
        "description": "{fighter} pushes through the wall. Gas tank expanding.",
        "stat_changes": {"cardio": (2, 2)},
    },
    TrainingEventType.TIMING_IMPROVED: {
        "base_chance": 0.04,
        "category": "positive",
        "conditions": ["striking_focus"],
        "headline": "Timing improved",
        "description": "{coach} drills timing. {fighter}'s counters are sharper.",
        "stat_changes": {"speed": (1, 1)},
    },
    TrainingEventType.SUBMISSION_SAVVY: {
        "base_chance": 0.04,
        "category": "positive",
        "conditions": ["bjj_focus"],
        "headline": "Submission savvy",
        "description": "New submission setup clicked. Dangerous on the ground.",
        "stat_changes": {"submissions": (1, 2)},
    },
    TrainingEventType.TAKEDOWN_TIMING: {
        "base_chance": 0.04,
        "category": "positive",
        "conditions": ["wrestling_focus"],
        "headline": "Takedown timing clicks",
        "description": "Shot timing improved. Takedowns coming easier.",
        "stat_changes": {"takedowns": (1, 2)},
    },
    TrainingEventType.MENTAL_EDGE: {
        "base_chance": 0.03,
        "category": "positive",
        "conditions": ["veteran_or_high_iq"],
        "headline": "Mental edge gained",
        "description": "{fighter} is locked in. Mentally sharper than ever.",
        "stat_changes": {"composure": (1, 1)},
    },
    TrainingEventType.POWER_INCREASE: {
        "base_chance": 0.03,
        "category": "positive",
        "conditions": ["strength_focus"],
        "headline": "Power increase",
        "description": "Strength work paying off. {fighter} hitting harder.",
        "stat_changes": {"strength": (1, 2)},
    },
    TrainingEventType.EARLY_PEAK: {
        "base_chance": 0.03,
        "category": "positive",
        "conditions": ["week_5_to_7"],
        "headline": "Peaking at the right time",
        "description": "Ready for fight night. {fighter} is in the zone.",
        "stat_changes": {"focus_all": (1, 1)},
    },
    TrainingEventType.GREAT_CHEMISTRY: {
        "base_chance": 0.05,
        "category": "positive",
        "conditions": ["high_chemistry"],
        "headline": "Great chemistry day",
        "description": "{coach} and {fighter} in perfect sync today.",
        "stat_changes": {"random": (1, 1)},
    },
    TrainingEventType.INSPIRED_TRAINING: {
        "base_chance": 0.03,
        "category": "positive",
        "conditions": [],
        "headline": "Inspired training session",
        "description": "{fighter} came in motivated. Exceptional session.",
        "stat_changes": {"random": (2, 2)},
    },
    TrainingEventType.VETERAN_WISDOM: {
        "base_chance": 0.03,
        "category": "positive",
        "conditions": ["age_30_plus"],
        "headline": "Veteran wisdom",
        "description": "Experience shows. {fighter} refining their craft.",
        "stat_changes": {"fight_iq": (1, 1)},
    },
    TrainingEventType.YOUNG_HUNGER: {
        "base_chance": 0.04,
        "category": "positive",
        "conditions": ["age_under_25"],
        "headline": "Young hunger",
        "description": "Youth and energy. {fighter} absorbing everything.",
        "stat_changes": {"random": (1, 2)},
    },
    
    # ===== NEGATIVE EVENTS =====
    TrainingEventType.MINOR_TWEAK: {
        "base_chance": 0.04,
        "category": "negative",
        "conditions": ["high_intensity_or_injury_prone"],
        "headline": "Minor injury in training",
        "description": "{fighter} tweaks their {body_part}. Light week ordered.",
        "skip_week": True,
    },
    TrainingEventType.OVERTRAINING: {
        "base_chance": 0.03,
        "category": "negative",
        "conditions": ["extreme_intensity_high_fatigue"],
        "headline": "Overtraining warning",
        "description": "Pushed too hard. {fighter} is burnt out.",
        "stat_changes": {"random": (-1, -1)},
        "fatigue_change": 15,
    },
    TrainingEventType.OFF_WEEK: {
        "base_chance": 0.06,
        "category": "negative",
        "conditions": [],
        "headline": "Off week",
        "description": "Flat session. It happens to everyone.",
        "gains_modifier": 0.5,
    },
    TrainingEventType.CAMP_FRICTION: {
        "base_chance": 0.03,
        "category": "negative",
        "conditions": ["low_chemistry"],
        "headline": "Camp friction",
        "description": "Tension with {coach}. Unproductive week.",
        "skip_week": True,
    },
    TrainingEventType.MINOR_ILLNESS: {
        "base_chance": 0.03,
        "category": "negative",
        "conditions": [],
        "headline": "Minor illness",
        "description": "{fighter} caught a bug. Rest ordered.",
        "skip_week": True,
    },
    TrainingEventType.BAD_SPARRING: {
        "base_chance": 0.03,
        "category": "negative",
        "conditions": ["multiple_fighters"],
        "headline": "Bad sparring session",
        "description": "Sparring got heated. {fighter} took some damage.",
        "stat_changes": {"random": (-1, -1)},
        "fatigue_change": 10,
    },
    TrainingEventType.FOCUS_CONFUSION: {
        "base_chance": 0.03,
        "category": "negative",
        "conditions": ["specialty_mismatch"],
        "headline": "Focus confusion",
        "description": "Mixed signals from coaching. {fighter} looks lost.",
        "stat_changes": {"focus_random": (-1, -1)},
    },
    TrainingEventType.NAGGING_PAIN: {
        "base_chance": 0.03,
        "category": "negative",
        "conditions": ["age_32_plus"],
        "headline": "Nagging pain",
        "description": "Old injuries flaring up. Careful week.",
        "gains_modifier": 0.5,
    },
    TrainingEventType.WEIGHT_CUT_ISSUES: {
        "base_chance": 0.02,
        "category": "negative",
        "conditions": [],
        "headline": "Weight cut complications",
        "description": "Weight cut complications. Training paused.",
        "skip_week": True,
        "fatigue_change": 10,
    },
    TrainingEventType.MENTAL_BLOCK: {
        "base_chance": 0.03,
        "category": "negative",
        "conditions": ["after_loss"],
        "headline": "Mental block",
        "description": "{fighter} struggling mentally. Doubt creeping in.",
        "stat_changes": {"composure": (-1, -1)},
    },
    
    # ===== NEUTRAL/FLAVOR EVENTS =====
    TrainingEventType.HARD_SPARRING: {
        "base_chance": 0.08,
        "category": "neutral",
        "conditions": ["multiple_fighters"],
        "headline": "Hard sparring week",
        "description": "Intense sparring. Battle-tested but tired.",
        "stat_changes": {"random": (1, 1)},
        "fatigue_change": 5,
    },
    TrainingEventType.REST_DAY_CALLED: {
        "base_chance": 0.05,
        "category": "neutral",
        "conditions": ["high_fatigue"],
        "headline": "Rest day called",
        "description": "{coach} calls for recovery. Smart move.",
        "gains_modifier": 0.0,
        "fatigue_change": -15,
    },
    TrainingEventType.TECHNIQUE_FOCUS: {
        "base_chance": 0.05,
        "category": "neutral",
        "conditions": ["quality_coach"],
        "headline": "Technique focus",
        "description": "Pure technique day. Refining the details.",
    },
    TrainingEventType.CARDIO_DAY: {
        "base_chance": 0.04,
        "category": "neutral",
        "conditions": [],
        "headline": "Cardio day",
        "description": "Conditioning-only session. Building the gas tank.",
        "stat_changes": {"cardio": (1, 1)},
    },
    TrainingEventType.PAD_WORK: {
        "base_chance": 0.05,
        "category": "neutral",
        "conditions": ["striking_focus"],
        "headline": "Pad work session",
        "description": "All pads today. Sharpening combinations.",
    },
    TrainingEventType.GRAPPLING_DAY: {
        "base_chance": 0.05,
        "category": "neutral",
        "conditions": ["grappling_focus"],
        "headline": "Grappling day",
        "description": "Mats only. Wrestling and submissions.",
    },
    TrainingEventType.STRATEGY_SESSION: {
        "base_chance": 0.04,
        "category": "neutral",
        "conditions": ["analytical_coach"],
        "headline": "Strategy session",
        "description": "Film and whiteboard day. Studying the opponent.",
        "stat_changes": {"fight_iq": (0, 1)},
    },
    TrainingEventType.LIGHT_WEEK: {
        "base_chance": 0.04,
        "category": "neutral",
        "conditions": [],
        "headline": "Light week",
        "description": "Deload week. Recovery and light work.",
        "gains_modifier": 0.75,
        "fatigue_change": -10,
    },
    TrainingEventType.MEDIA_DAY: {
        "base_chance": 0.02,
        "category": "neutral",
        "conditions": ["upcoming_fight"],
        "headline": "Media obligations",
        "description": "Media day. No training today.",
        "gains_modifier": 0.0,
    },
    TrainingEventType.CAMP_VISITOR: {
        "base_chance": 0.02,
        "category": "neutral",
        "conditions": [],
        "headline": "Camp visitor",
        "description": "Former champion visits camp! {fighter} gains motivation.",
        "stat_changes": {"random": (1, 1)},
    },
    TrainingEventType.NEW_DRILL: {
        "base_chance": 0.04,
        "category": "neutral",
        "conditions": [],
        "headline": "New drill introduced",
        "description": "{coach} introduces new drill. Mixing it up.",
    },
    TrainingEventType.MORNING_RUN: {
        "base_chance": 0.03,
        "category": "neutral",
        "conditions": [],
        "headline": "Morning run",
        "description": "5am run with the team. Camp bonding.",
        "stat_changes": {"cardio": (0, 1)},
    },
}

# Body parts for injury descriptions
BODY_PARTS = [
    "shoulder", "knee", "ankle", "back", "hip",
    "elbow", "wrist", "hamstring", "groin", "neck"
]


def should_trigger_event(
    fighter_age: int,
    weeks_completed: int,
    total_weeks: int,
    intensity: TrainingIntensity,
    chemistry: int,
    fatigue: int,
    is_receiving_private_lessons: bool = False
) -> bool:
    """
    Determine if a training event should occur this week.
    
    Base chance: 18% per week (~1.5 events per 8-week camp)
    """
    # Base chance: 18% = ~1.5 events per 8-week camp
    base_chance = 0.18
    modifiers = 0.0
    
    # High intensity = more happens
    if intensity == TrainingIntensity.INTENSE:
        modifiers += 0.04
    elif intensity == TrainingIntensity.EXTREME:
        modifiers += 0.08
    
    # Chemistry affects event rate
    if chemistry >= 70:
        modifiers += 0.03  # Good chemistry, more moments
    elif chemistry < 40:
        modifiers += 0.05  # Bad chemistry, more friction
    
    # Young fighters have more learning moments
    if fighter_age < 25:
        modifiers += 0.03
    
    # First 2 weeks: settling in
    if weeks_completed < 2:
        modifiers -= 0.05
    
    # Final week: high stakes
    if weeks_completed >= total_weeks - 1:
        modifiers += 0.05
    
    # Private lessons = more coach interaction = more events
    if is_receiving_private_lessons:
        modifiers += 0.04
    
    final_chance = base_chance + modifiers
    return random.random() < final_chance


def get_event_weight(
    event_type: TrainingEventType,
    event_data: Dict,
    context: Dict[str, Any]
) -> float:
    """
    Calculate the weight for this event type based on context.
    Returns 0 if event shouldn't be possible.
    """
    base_chance = event_data.get("base_chance", 0.05)
    conditions = event_data.get("conditions", [])
    
    # Check conditions
    for condition in conditions:
        if condition == "young_or_high_chemistry":
            if context.get("age", 30) >= 30 and context.get("chemistry", 50) < 60:
                return 0
        elif condition == "coach_quality_3_plus":
            if context.get("coach_quality", 3) < 3:
                return 0
        elif condition == "moderate_intensity":
            if context.get("intensity") != TrainingIntensity.MODERATE:
                base_chance *= 0.5
        elif condition == "analytical_coach":
            if not context.get("coach_is_analytical", False):
                return 0
        elif condition == "conditioning_focus":
            if context.get("focus") != TrainingFocus.CONDITIONING:
                return 0
        elif condition == "striking_focus":
            if context.get("focus") != TrainingFocus.STRIKING:
                base_chance *= 0.3
        elif condition == "bjj_focus":
            if context.get("focus") != TrainingFocus.JIUJITSU:
                return 0
        elif condition == "wrestling_focus":
            if context.get("focus") != TrainingFocus.WRESTLING:
                return 0
        elif condition == "strength_focus":
            if context.get("focus") != TrainingFocus.STRENGTH_POWER:
                return 0
        elif condition == "veteran_or_high_iq":
            if context.get("age", 25) < 30 and context.get("fight_iq", 50) < 70:
                return 0
        elif condition == "week_5_to_7":
            week = context.get("weeks_completed", 0)
            if week < 4 or week > 6:
                return 0
        elif condition == "high_chemistry":
            if context.get("chemistry", 50) < 70:
                return 0
        elif condition == "age_30_plus":
            if context.get("age", 25) < 30:
                return 0
        elif condition == "age_under_25":
            if context.get("age", 25) >= 25:
                return 0
        elif condition == "high_intensity_or_injury_prone":
            is_intense = context.get("intensity") in [TrainingIntensity.INTENSE, TrainingIntensity.EXTREME]
            is_injury_prone = context.get("is_injury_prone", False)
            if not is_intense and not is_injury_prone:
                base_chance *= 0.3
        elif condition == "extreme_intensity_high_fatigue":
            if context.get("intensity") != TrainingIntensity.EXTREME or context.get("fatigue", 0) < 60:
                return 0
        elif condition == "low_chemistry":
            if context.get("chemistry", 50) >= 40:
                return 0
        elif condition == "multiple_fighters":
            if context.get("camp_fighter_count", 1) < 2:
                return 0
        elif condition == "specialty_mismatch":
            if context.get("specialty_matches", True):
                return 0
        elif condition == "age_32_plus":
            if context.get("age", 25) < 32:
                return 0
        elif condition == "after_loss":
            if not context.get("lost_last_fight", False):
                return 0
        elif condition == "high_fatigue":
            if context.get("fatigue", 0) < 50:
                return 0
        elif condition == "quality_coach":
            if context.get("coach_quality", 3) < 3:
                base_chance *= 0.5
        elif condition == "grappling_focus":
            if context.get("focus") not in [TrainingFocus.WRESTLING, TrainingFocus.JIUJITSU]:
                base_chance *= 0.3
        elif condition == "upcoming_fight":
            if context.get("weeks_until_fight", 99) > 2:
                return 0
    
    return base_chance


def generate_training_event(
    fighter_name: str,
    coach_name: str,
    context: Dict[str, Any]
) -> Optional[TrainingEvent]:
    """
    Generate a training event based on context.
    
    Context should include:
    - age, chemistry, focus, intensity, fatigue
    - coach_quality, coach_is_analytical, specialty_matches
    - weeks_completed, camp_fighter_count
    - is_injury_prone, lost_last_fight, weeks_until_fight, fight_iq
    """
    # Calculate weights for all events
    weights = []
    event_types = []
    
    for event_type, event_data in TRAINING_EVENTS.items():
        weight = get_event_weight(event_type, event_data, context)
        if weight > 0:
            weights.append(weight)
            event_types.append(event_type)
    
    if not weights:
        return None
    
    # Adjust weights based on chemistry (positive events more likely with good chemistry)
    chemistry = context.get("chemistry", 50)
    adjusted_weights = []
    for i, event_type in enumerate(event_types):
        event_data = TRAINING_EVENTS[event_type]
        category = event_data.get("category", "neutral")
        weight = weights[i]
        
        if chemistry >= 70:
            if category == "positive":
                weight *= 1.3
            elif category == "negative":
                weight *= 0.6
        elif chemistry < 40:
            if category == "positive":
                weight *= 0.6
            elif category == "negative":
                weight *= 1.4
        
        adjusted_weights.append(weight)
    
    # Select event
    total = sum(adjusted_weights)
    if total == 0:
        return None
    
    normalized = [w / total for w in adjusted_weights]
    selected_type = random.choices(event_types, weights=normalized, k=1)[0]
    event_data = TRAINING_EVENTS[selected_type]
    
    # Generate the event
    headline = event_data["headline"].format(
        fighter=fighter_name,
        coach=coach_name
    )
    
    body_part = random.choice(BODY_PARTS)
    description = event_data["description"].format(
        fighter=fighter_name,
        coach=coach_name,
        body_part=body_part,
        gain="1-2",
        attribute="random"
    )
    
    # Process stat changes
    stat_changes = {}
    raw_changes = event_data.get("stat_changes", {})
    focus = context.get("focus", TrainingFocus.BALANCED)
    focus_attrs = FOCUS_ATTRIBUTES.get(focus, [])
    
    for key, value_range in raw_changes.items():
        if isinstance(value_range, tuple):
            min_val, max_val = value_range
            change = random.randint(min_val, max_val)
        else:
            change = value_range
        
        if key == "focus_random" and focus_attrs:
            attr = random.choice(focus_attrs)
            stat_changes[attr] = change
        elif key == "focus_all" and focus_attrs:
            for attr in focus_attrs:
                stat_changes[attr] = change
        elif key == "weakness_random":
            # Pick a random low attribute (use new attribute names)
            possible = ["boxing", "takedowns", "submissions", "cardio", "composure"]
            attr = random.choice(possible)
            stat_changes[attr] = change
        elif key == "random":
            # Random attribute from new 17-attribute system
            attr = random.choice(["boxing", "takedowns", "submissions", "cardio", "strength", "speed", "fight_iq"])
            stat_changes[attr] = change
        elif key in ["cardio", "fight_iq", "composure", "submissions", "takedowns", "strength", "speed"]:
            stat_changes[key] = change
    
    return TrainingEvent(
        event_type=selected_type,
        category=event_data.get("category", "neutral"),
        headline=headline,
        description=description,
        stat_changes=stat_changes,
        skip_week=event_data.get("skip_week", False),
        gains_modifier=event_data.get("gains_modifier", 1.0),
        fatigue_change=event_data.get("fatigue_change", 0),
    )


# ============================================================================
# SPARRING SYSTEM
# ============================================================================

def calculate_sparring_bonus(
    camp_fighters: List[Dict[str, Any]],
    coach_has_iron_sharpener: bool = False
) -> Tuple[float, str]:
    """
    Calculate sparring bonus for the camp.
    Fully automatic - player doesn't control this.
    
    Args:
        camp_fighters: List of dicts with 'overall' and optionally 'fighting_style'
        coach_has_iron_sharpener: True if any coach has Iron Sharpener trait
    
    Returns:
        Tuple of (bonus_multiplier, description)
    """
    num_fighters = len(camp_fighters)
    
    # Need at least 2 fighters for sparring
    if num_fighters < 2:
        return 0.0, "No sparring partners available"
    
    # Base bonus for having partners (5%)
    bonus = 0.05
    
    # Quality of partners
    if camp_fighters:
        avg_overall = sum(f.get("overall", 50) for f in camp_fighters) / num_fighters
        if avg_overall >= 80:
            bonus += 0.05
            quality_desc = "Elite"
        elif avg_overall >= 70:
            bonus += 0.03
            quality_desc = "Good"
        elif avg_overall >= 60:
            bonus += 0.01
            quality_desc = "Decent"
        else:
            quality_desc = "Developing"
    else:
        quality_desc = "Unknown"
    
    # Style diversity bonus
    styles = set(f.get("fighting_style", "Unknown") for f in camp_fighters)
    if len(styles) >= 3:
        bonus += 0.03
        diversity = "Diverse styles"
    elif len(styles) >= 2:
        bonus += 0.01
        diversity = "Some variety"
    else:
        diversity = "Similar styles"
    
    # Iron Sharpener coach trait
    if coach_has_iron_sharpener:
        bonus += 0.05
    
    # Diminishing returns on large camps
    if num_fighters > 6:
        bonus *= 0.8  # Crowded gym
    
    # Cap at 15%
    bonus = min(0.15, bonus)
    
    description = f"{quality_desc} sparring ({num_fighters} partners, {diversity})"
    
    return bonus, description


# ============================================================================
# PRIVATE LESSONS
# ============================================================================

def calculate_private_lesson_score(
    coach_quality: int,
    coach_traits: List[str],
    fighter_age: int,
    fighter_potential: int,
    chemistry: int,
    has_scheduled_fight: bool,
    weeks_until_fight: int = 99
) -> int:
    """
    Score how much a coach wants to focus on this fighter.
    Higher score = more likely to receive private lessons.
    
    Returns score (0-100+). Threshold of 40 needed to trigger.
    """
    # Only quality 3+ coaches give private lessons
    if coach_quality < 3:
        return 0
    
    score = 0
    
    # Upcoming fight = highest priority
    if has_scheduled_fight:
        if weeks_until_fight <= 4:
            score += 60
        elif weeks_until_fight <= 8:
            score += 40
        else:
            score += 20
    
    # High chemistry = natural attention
    if chemistry >= 80:
        score += 35
    elif chemistry >= 60:
        score += 20
    elif chemistry >= 40:
        score += 10
    
    # Diamond Polisher + young prospect
    if "Diamond Polisher" in coach_traits and fighter_age < 25:
        score += 30
    
    # Veteran's Touch + veteran fighter
    if "Veteran's Touch" in coach_traits and fighter_age > 32:
        score += 25
    
    # High potential prospects
    if fighter_age < 25 and fighter_potential >= 80:
        score += 20
    
    return score


def get_private_lesson_assignments(
    coaches: List[Dict[str, Any]],
    fighters: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Determine which coaches give private lessons to which fighters.
    
    Args:
        coaches: List of coach dicts with 'coach_id', 'quality', 'traits'
        fighters: List of fighter dicts with 'fighter_id', 'age', 'potential',
                  'chemistry', 'has_scheduled_fight', 'weeks_until_fight'
    
    Returns:
        Dict mapping coach_id -> fighter_id for private lessons
    """
    assignments = {}
    assigned_fighters = set()
    
    # Sort coaches by quality (best coaches choose first)
    sorted_coaches = sorted(coaches, key=lambda c: c.get("quality", 3), reverse=True)
    
    for coach in sorted_coaches:
        coach_id = coach.get("coach_id", "")
        quality = coach.get("quality", 3)
        traits = coach.get("traits", [])
        
        # Only quality 3+ coaches give private lessons
        if quality < 3:
            continue
        
        best_score = 0
        best_fighter_id = None
        
        for fighter in fighters:
            fighter_id = fighter.get("fighter_id", "")
            
            # Can't assign to already-assigned fighter
            if fighter_id in assigned_fighters:
                continue
            
            score = calculate_private_lesson_score(
                coach_quality=quality,
                coach_traits=traits,
                fighter_age=fighter.get("age", 25),
                fighter_potential=fighter.get("potential", 70),
                chemistry=fighter.get("chemistry", 50),
                has_scheduled_fight=fighter.get("has_scheduled_fight", False),
                weeks_until_fight=fighter.get("weeks_until_fight", 99)
            )
            
            if score > best_score:
                best_score = score
                best_fighter_id = fighter_id
        
        # Threshold to trigger private lessons
        if best_score >= 40 and best_fighter_id:
            assignments[coach_id] = best_fighter_id
            assigned_fighters.add(best_fighter_id)
    
    return assignments


# ============================================================================
# TRAINING CAMP
# ============================================================================

@dataclass
class TrainingCamp:
    """
    A structured training camp for fight preparation.
    
    Typically 8 weeks of focused training before a fight.
    Now supports camp templates with week-by-week intensity schedules.
    """
    fighter_id: str
    camp_id: str
    focus: TrainingFocus = TrainingFocus.BALANCED
    intensity: TrainingIntensity = TrainingIntensity.MODERATE  # Legacy fallback
    total_weeks: int = 8
    weeks_completed: int = 0
    
    # Template system (new)
    template: Optional[CampTemplate] = None
    schedule: List[TrainingIntensity] = field(default_factory=list)
    
    # Tracking
    attribute_gains: Dict[str, int] = field(default_factory=dict)
    total_fatigue_accumulated: int = 0
    injuries_during_camp: int = 0
    
    # Events
    events: List[TrainingEvent] = field(default_factory=list)
    
    # Opponent-specific (for FIGHT_SPECIFIC focus)
    opponent_id: Optional[str] = None
    opponent_weaknesses: List[str] = field(default_factory=list)
    
    # Dates
    start_date: Optional[GameDate] = None
    
    def get_current_intensity(self) -> TrainingIntensity:
        """Get the intensity for the current week based on schedule."""
        if self.schedule and 0 <= self.weeks_completed < len(self.schedule):
            return self.schedule[self.weeks_completed]
        return self.intensity  # Fallback to legacy
    
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
    def progress_percentage(self) -> float:
        if self.total_weeks == 0:
            return 100.0
        return (self.weeks_completed / self.total_weeks) * 100
    
    @property
    def total_gains(self) -> int:
        """Sum of all attribute improvements"""
        return sum(self.attribute_gains.values())
    
    @property
    def positive_events(self) -> int:
        return len([e for e in self.events if e.category == "positive"])
    
    @property
    def negative_events(self) -> int:
        return len([e for e in self.events if e.category == "negative"])
    
    def record_gain(self, attribute: str, amount: int) -> None:
        """Record an attribute gain"""
        if attribute in self.attribute_gains:
            self.attribute_gains[attribute] += amount
        else:
            self.attribute_gains[attribute] = amount
    
    def record_event(self, event: TrainingEvent) -> None:
        """Record a training event"""
        self.events.append(event)
    
    def complete_week(self) -> None:
        """Mark a week as completed"""
        self.weeks_completed += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Export camp data"""
        return {
            "fighter_id": self.fighter_id,
            "camp_id": self.camp_id,
            "focus": self.focus.value,
            "intensity": self.intensity.name,
            "template": self.template.value if self.template else None,
            "schedule": [i.name for i in self.schedule] if self.schedule else [],
            "total_weeks": self.total_weeks,
            "weeks_completed": self.weeks_completed,
            "attribute_gains": self.attribute_gains.copy(),
            "total_fatigue_accumulated": self.total_fatigue_accumulated,
            "injuries_during_camp": self.injuries_during_camp,
            "events": [e.to_dict() for e in self.events],
            "opponent_id": self.opponent_id,
            "opponent_weaknesses": self.opponent_weaknesses.copy(),
            "start_date": {
                "year": self.start_date.year,
                "month": self.start_date.month,
                "day": self.start_date.day
            } if self.start_date else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingCamp':
        """Create camp from saved data"""
        # Parse template
        template = None
        if data.get("template"):
            try:
                template = CampTemplate(data["template"])
            except (ValueError, KeyError):
                template = None
        
        # Parse schedule
        schedule = []
        if data.get("schedule"):
            for intensity_name in data["schedule"]:
                try:
                    schedule.append(TrainingIntensity[intensity_name])
                except (ValueError, KeyError):
                    schedule.append(TrainingIntensity.MODERATE)
        
        camp = cls(
            fighter_id=data["fighter_id"],
            camp_id=data["camp_id"],
            focus=TrainingFocus(data["focus"]),
            intensity=TrainingIntensity[data["intensity"]],
            template=template,
            schedule=schedule,
            total_weeks=data["total_weeks"],
            weeks_completed=data["weeks_completed"]
        )
        camp.attribute_gains = data.get("attribute_gains", {})
        camp.total_fatigue_accumulated = data.get("total_fatigue_accumulated", 0)
        camp.injuries_during_camp = data.get("injuries_during_camp", 0)
        camp.opponent_id = data.get("opponent_id")
        camp.opponent_weaknesses = data.get("opponent_weaknesses", [])
        
        # Load events
        for event_data in data.get("events", []):
            camp.events.append(TrainingEvent.from_dict(event_data))
        
        if data.get("start_date"):
            sd = data["start_date"]
            camp.start_date = GameDate(sd["year"], sd["month"], sd["day"])
        
        return camp


# ============================================================================
# TRAINING CALCULATIONS
# ============================================================================

def calculate_diminishing_returns(current_value: int) -> float:
    """
    Calculate diminishing returns multiplier based on current attribute.
    """
    if current_value < 50:
        return 1.2  # Easier to improve low attributes
    elif current_value < 70:
        return 1.0  # Normal improvement
    elif current_value < 80:
        return 0.7  # Harder
    elif current_value < 90:
        return 0.4  # Much harder
    else:
        return 0.2  # Elite level, very hard to improve


def calculate_age_modifier(age: int) -> float:
    """
    Calculate training effectiveness based on age.
    """
    prime_start = get_config("aging.prime_start", 26)
    prime_end = get_config("aging.prime_end", 32)
    
    if age < 22:
        return 1.3  # Young fighters learn fast
    elif age < prime_start:
        return 1.15  # Still developing
    elif age <= prime_end:
        return 1.0  # Prime years
    elif age <= 35:
        return 0.7  # Declining learning ability
    else:
        return 0.4  # Hard to improve at older age


def calculate_camp_tier_bonus(tier: CampTier) -> float:
    """
    Get training bonus from camp facilities.
    """
    tier_bonuses = get_config("camp.tier_training_bonus", {
        1: 0.9,  # Garage
        2: 1.0,  # Local
        3: 1.1,  # Regional
        4: 1.2,  # National
        5: 1.3,  # Elite
    })
    
    if hasattr(tier, 'value'):
        return tier_bonuses.get(tier.value, 1.0)
    return tier_bonuses.get(tier, 1.0)


def calculate_coach_quality_bonus(coach_quality: int) -> float:
    """
    Calculate training bonus from coach quality.
    """
    quality_bonuses = get_config("camp.coach_quality_multiplier", {
        1: 0.6,
        2: 0.8,
        3: 1.0,
        4: 1.2,
        5: 1.5,
    })
    return quality_bonuses.get(coach_quality, 1.0)


def calculate_training_gain(
    base_gain: float,
    current_value: int,
    age: int,
    camp_tier: CampTier,
    coach_quality: int = 3,
    intensity: TrainingIntensity = TrainingIntensity.MODERATE,
    is_focus_attribute: bool = False,
    coach_specialty_matches: bool = False,
    chemistry_multiplier: float = 1.0,
    coach_trait_multiplier: float = 1.0,
    sparring_bonus: float = 0.0,
    private_lessons: bool = False,
    someone_else_has_private: bool = False,
) -> int:
    """
    Calculate actual attribute gain from training.
    
    Full calculation with all modifiers.
    """
    # Start with base gain
    gain = base_gain
    
    # Apply modifiers
    gain *= calculate_diminishing_returns(current_value)
    gain *= calculate_age_modifier(age)
    gain *= calculate_camp_tier_bonus(camp_tier)
    gain *= calculate_coach_quality_bonus(coach_quality)
    gain *= INTENSITY_MULTIPLIERS[intensity]
    
    # Focus bonus
    if is_focus_attribute:
        gain *= 1.5
    
    # Coach specialty match (+25%)
    if coach_specialty_matches:
        gain *= 1.25
    
    # Chemistry multiplier (0.8 to 1.2)
    gain *= chemistry_multiplier
    
    # Coach trait multiplier (Diamond Polisher, etc.)
    gain *= coach_trait_multiplier
    
    # Sparring bonus (0 to 0.15)
    gain *= (1 + sparring_bonus)
    
    # Private lessons (+20%)
    if private_lessons:
        gain *= 1.20
    elif someone_else_has_private:
        gain *= 0.97  # -3% when coach is distracted
    
    # Add some randomness (+/- 20%)
    variance = random.uniform(0.8, 1.2)
    gain *= variance
    
    # Return integer gain (minimum 0)
    return max(0, int(gain))


# ============================================================================
# TRAINING SYSTEM
# ============================================================================

class TrainingSystem:
    """
    Manages training camps and fighter development.
    
    Enhanced with coach integration, sparring, private lessons, and events.
    """
    
    def __init__(self):
        self._active_camps: Dict[str, TrainingCamp] = {}  # fighter_id -> camp
    
    @property
    def active_camps(self) -> List[TrainingCamp]:
        """Get all active training camps"""
        return list(self._active_camps.values())
    
    def start_camp(
        self,
        fighter_id: str,
        camp_id: str,
        focus: TrainingFocus = TrainingFocus.BALANCED,
        intensity: TrainingIntensity = TrainingIntensity.MODERATE,
        weeks: int = 8,
        opponent_id: Optional[str] = None,
        template: Optional[CampTemplate] = None,
    ) -> TrainingCamp:
        """
        Start a new training camp for a fighter.
        
        If template is provided, generates a week-by-week schedule.
        Otherwise uses the legacy single intensity for all weeks.
        """
        weeks = max(1, min(weeks, get_config("training.max_camp_weeks", 12)))
        
        # Generate schedule if template provided
        schedule = []
        if template:
            schedule = generate_camp_schedule(template, weeks)
            # Set the first week's intensity as the base intensity
            if schedule:
                intensity = schedule[0]
        
        camp = TrainingCamp(
            fighter_id=fighter_id,
            camp_id=camp_id,
            focus=focus,
            intensity=intensity,
            template=template,
            schedule=schedule,
            total_weeks=weeks,
            opponent_id=opponent_id,
            start_date=calendar.current_date
        )
        
        self._active_camps[fighter_id] = camp
        
        emit(EventType.TRAINING_STARTED, {
            "fighter_id": fighter_id,
            "camp_id": camp_id,
            "focus": focus.value,
            "template": template.value if template else None,
            "weeks": weeks
        })
        
        return camp
    
    def get_camp(self, fighter_id: str) -> Optional[TrainingCamp]:
        """Get active training camp for a fighter"""
        return self._active_camps.get(fighter_id)
    
    def has_active_camp(self, fighter_id: str) -> bool:
        """Check if fighter has an active training camp"""
        camp = self._active_camps.get(fighter_id)
        return camp is not None and not camp.is_complete
    
    def process_training_week(
        self,
        fighter_id: str,
        current_attributes: Dict[str, int],
        age: int,
        camp_tier: CampTier = None,
        coach_quality: int = 3,
        fatigue: int = 0,
        # New parameters for enhanced system
        coach_specialty: str = None,
        chemistry: int = 50,
        coach_trait_multiplier: float = 1.0,
        coach_traits: List[str] = None,
        sparring_bonus: float = 0.0,
        is_receiving_private_lessons: bool = False,
        someone_else_has_private: bool = False,
        camp_fighter_count: int = 1,
        fighter_name: str = "Fighter",
        coach_name: str = "Coach",
        fighter_traits: List[str] = None,
        lost_last_fight: bool = False,
        weeks_until_fight: int = 99,
        fight_iq: int = 50,
    ) -> Tuple[Dict[str, int], Optional[TrainingEvent]]:
        """
        Process one week of training for a fighter.
        
        Returns:
            Tuple of (attribute gains dict, optional training event)
        """
        camp = self._active_camps.get(fighter_id)
        if not camp or camp.is_complete:
            return {}, None
        
        gains: Dict[str, int] = {}
        event = None
        base_gain = get_config("training.base_weekly_gain", 1.5)
        max_weekly = get_config("training.max_gain_per_week", 3)
        
        # Default camp tier
        if camp_tier is None:
            camp_tier = CampTier.LOCAL
        
        # Fatigue reduces training effectiveness
        fatigue_penalty = 1.0 - (fatigue / 200)
        fatigue_penalty = max(0.3, fatigue_penalty)
        
        # Check for training event first
        coach_traits = coach_traits or []
        fighter_traits = fighter_traits or []
        
        specialty_matches = coach_specialty_matches_focus(coach_specialty, camp.focus)
        
        # Build context for event generation
        event_context = {
            "age": age,
            "chemistry": chemistry,
            "focus": camp.focus,
            "intensity": camp.intensity,
            "fatigue": fatigue,
            "coach_quality": coach_quality,
            "coach_is_analytical": "Analytical" in coach_traits,
            "specialty_matches": specialty_matches,
            "weeks_completed": camp.weeks_completed,
            "camp_fighter_count": camp_fighter_count,
            "is_injury_prone": "Injury Prone" in fighter_traits,
            "lost_last_fight": lost_last_fight,
            "weeks_until_fight": weeks_until_fight,
            "fight_iq": fight_iq,
        }
        
        # Roll for training event
        if should_trigger_event(
            fighter_age=age,
            weeks_completed=camp.weeks_completed,
            total_weeks=camp.total_weeks,
            intensity=camp.intensity,
            chemistry=chemistry,
            fatigue=fatigue,
            is_receiving_private_lessons=is_receiving_private_lessons
        ):
            event = generate_training_event(fighter_name, coach_name, event_context)
            if event:
                camp.record_event(event)
                
                # Apply immediate stat changes from event
                for attr, change in event.stat_changes.items():
                    if change != 0:
                        current_val = current_attributes.get(attr, 50)
                        new_val = max(1, min(100, current_val + change))
                        gains[attr] = change
                        camp.record_gain(attr, change)
        
        # Check if event skips training
        if event and event.skip_week:
            camp.complete_week()
            if camp.is_complete:
                self._complete_camp(camp)
            return gains, event
        
        # Get gains modifier from event
        gains_modifier = 1.0
        if event:
            gains_modifier = event.gains_modifier
        
        # If gains_modifier is 0, skip normal training (rest day)
        if gains_modifier <= 0:
            camp.complete_week()
            if camp.is_complete:
                self._complete_camp(camp)
            return gains, event
        
        # Determine which attributes to train
        focus_attrs = set(FOCUS_ATTRIBUTES.get(camp.focus, []))
        
        # For balanced training, train all but less intensely
        if camp.focus == TrainingFocus.BALANCED:
            all_attrs = list(ALL_ATTRIBUTES) if ALL_ATTRIBUTES else [
                "boxing", "kicks", "takedowns", "submissions", "cardio", 
                "strength", "speed", "takedown_defense"
            ]
            attrs_to_train = random.sample(all_attrs, min(6, len(all_attrs)))
        else:
            attrs_to_train = list(focus_attrs)
        
        # Chemistry multiplier
        if chemistry >= 80:
            chemistry_mult = 1.2
        elif chemistry >= 60:
            chemistry_mult = 1.1
        elif chemistry >= 40:
            chemistry_mult = 1.0
        elif chemistry >= 20:
            chemistry_mult = 0.9
        else:
            chemistry_mult = 0.8
        
        # Calculate gains for each attribute
        for attr in attrs_to_train:
            current_val = current_attributes.get(attr, 50)
            is_focus = attr in focus_attrs
            
            gain = calculate_training_gain(
                base_gain=base_gain,
                current_value=current_val,
                age=age,
                camp_tier=camp_tier,
                coach_quality=coach_quality,
                intensity=camp.intensity,
                is_focus_attribute=is_focus,
                coach_specialty_matches=specialty_matches and is_focus,
                chemistry_multiplier=chemistry_mult,
                coach_trait_multiplier=coach_trait_multiplier,
                sparring_bonus=sparring_bonus,
                private_lessons=is_receiving_private_lessons,
                someone_else_has_private=someone_else_has_private,
            )
            
            # Apply fatigue penalty
            gain = int(gain * fatigue_penalty)
            
            # Apply event modifier
            gain = int(gain * gains_modifier)
            
            # Cap weekly gain
            gain = min(gain, max_weekly)
            
            if gain > 0:
                if attr in gains:
                    gains[attr] += gain
                else:
                    gains[attr] = gain
                camp.record_gain(attr, gain)
        
        # Track fatigue
        fatigue_added = INTENSITY_FATIGUE[camp.intensity]
        if event and event.fatigue_change:
            fatigue_added += event.fatigue_change
        camp.total_fatigue_accumulated += max(0, fatigue_added)
        
        # Check for training injury
        injury_occurred = self._check_training_injury(camp, fatigue, "Injury Prone" in fighter_traits)
        if injury_occurred:
            camp.injuries_during_camp += 1
        
        # Complete the week
        camp.complete_week()
        
        # Check if camp is finished
        if camp.is_complete:
            self._complete_camp(camp)
        
        return gains, event
    
    def _check_training_injury(
        self,
        camp: TrainingCamp,
        current_fatigue: int,
        is_injury_prone: bool = False
    ) -> bool:
        """
        Check if a training injury occurs.
        """
        base_risk = INTENSITY_INJURY_RISK[camp.intensity]
        
        # Fatigue increases injury risk
        fatigue_risk = current_fatigue / 500  # Max +20% at 100 fatigue
        
        # Injury Prone trait
        if is_injury_prone:
            base_risk *= 1.5
        
        total_risk = base_risk + fatigue_risk
        
        return random.random() < total_risk
    
    def _complete_camp(self, camp: TrainingCamp) -> None:
        """Handle camp completion"""
        emit(EventType.TRAINING_COMPLETED, {
            "fighter_id": camp.fighter_id,
            "camp_id": camp.camp_id,
            "weeks": camp.total_weeks,
            "total_gains": camp.total_gains,
            "attribute_gains": camp.attribute_gains.copy(),
            "events": len(camp.events),
            "positive_events": camp.positive_events,
            "negative_events": camp.negative_events,
        })
    
    def cancel_camp(self, fighter_id: str) -> bool:
        """Cancel an active training camp."""
        if fighter_id in self._active_camps:
            del self._active_camps[fighter_id]
            return True
        return False
    
    def end_camp(self, fighter_id: str) -> Optional[TrainingCamp]:
        """End and remove a training camp."""
        if fighter_id in self._active_camps:
            camp = self._active_camps.pop(fighter_id)
            if not camp.is_complete:
                self._complete_camp(camp)
            return camp
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Export system state"""
        return {
            "active_camps": {
                fid: camp.to_dict()
                for fid, camp in self._active_camps.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingSystem':
        """Create system from saved data"""
        system = cls()
        for fid, camp_data in data.get("active_camps", {}).items():
            system._active_camps[fid] = TrainingCamp.from_dict(camp_data)
        return system


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_recommended_training(
    gameplan_focus: str,
    opponent_style: str = None,
    opponent_strengths: List[str] = None,
    opponent_weaknesses: List[str] = None
) -> List[Tuple[TrainingFocus, str]]:
    """
    Get training recommendations based on gameplan and opponent.
    """
    recommendations = []
    
    # Gameplan to training mapping
    gameplan_to_training = {
        "STRIKING": [TrainingFocus.STRIKING, TrainingFocus.CONDITIONING],
        "GRAPPLING": [TrainingFocus.WRESTLING, TrainingFocus.JIUJITSU],
        "CLINCH": [TrainingFocus.WRESTLING, TrainingFocus.STRIKING],
        "MIXED": [TrainingFocus.BALANCED],
    }
    
    # Base recommendations from gameplan
    base_focuses = gameplan_to_training.get(gameplan_focus, [TrainingFocus.BALANCED])
    for focus in base_focuses:
        recommendations.append((focus, f"Aligns with your {gameplan_focus.lower()} gameplan"))
    
    # Opponent-based recommendations
    if opponent_style:
        style_lower = opponent_style.lower()
        
        if "wrestler" in style_lower:
            recommendations.append((TrainingFocus.JIUJITSU, "Work off your back vs wrestler"))
            recommendations.append((TrainingFocus.CONDITIONING, "Survive scrambles and cage work"))
        elif "bjj" in style_lower or "jiu" in style_lower:
            recommendations.append((TrainingFocus.WRESTLING, "Avoid the ground or control top"))
        elif "boxer" in style_lower or "striker" in style_lower:
            recommendations.append((TrainingFocus.WRESTLING, "Take the fight to the mat"))
        elif "brawler" in style_lower:
            recommendations.append((TrainingFocus.STRIKING, "Outclass them technically"))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_recommendations = []
    for focus, reason in recommendations:
        if focus not in seen:
            seen.add(focus)
            unique_recommendations.append((focus, reason))
    
    return unique_recommendations[:4]


def estimate_camp_gains(
    weeks: int,
    camp_tier: CampTier,
    coach_quality: int,
    age: int,
    focus: TrainingFocus,
    intensity: TrainingIntensity = TrainingIntensity.MODERATE,
    coach_specialty_matches: bool = False,
    chemistry: int = 50,
    sparring_bonus: float = 0.0,
) -> int:
    """
    Estimate total attribute gains from a training camp.
    """
    base_gain = get_config("training.base_weekly_gain", 1.5)
    
    # Calculate modifier
    modifier = calculate_camp_tier_bonus(camp_tier)
    modifier *= calculate_coach_quality_bonus(coach_quality)
    modifier *= calculate_age_modifier(age)
    modifier *= INTENSITY_MULTIPLIERS[intensity]
    
    # Specialty match
    if coach_specialty_matches:
        modifier *= 1.25
    
    # Chemistry
    if chemistry >= 70:
        modifier *= 1.15
    elif chemistry < 40:
        modifier *= 0.9
    
    # Sparring
    modifier *= (1 + sparring_bonus)
    
    # Estimate weekly gain
    weekly_gain = base_gain * modifier
    
    # Focus gives bonus
    if focus != TrainingFocus.BALANCED:
        weekly_gain *= 1.3
    
    # Total across all trained attributes (roughly 4-5 per week)
    attrs_per_week = 5 if focus == TrainingFocus.BALANCED else 4
    
    return int(weekly_gain * weeks * attrs_per_week)


# ============================================================================
# CAMP SETUP HELPERS (For CLI and AI)
# ============================================================================

@dataclass
class TrainingFocusOption:
    """A training focus option for menu display."""
    key: str
    name: str
    description: str
    focus: TrainingFocus
    matching_specialties: List[str]
    is_recommended: bool = False
    recommendation_reason: str = ""
    coach_matches: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "focus": self.focus.value,
            "matching_specialties": self.matching_specialties,
            "is_recommended": self.is_recommended,
            "recommendation_reason": self.recommendation_reason,
            "coach_matches": self.coach_matches,
        }


@dataclass
class IntensityOption:
    """An intensity option for menu display."""
    key: str
    name: str
    gains_percent: int
    injury_risk_percent: int
    description: str
    intensity: TrainingIntensity
    is_default: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "gains_percent": self.gains_percent,
            "injury_risk_percent": self.injury_risk_percent,
            "description": self.description,
            "intensity": self.intensity.value,
            "is_default": self.is_default,
        }


@dataclass
class CampSetupEstimate:
    """Estimated results from a training camp setup."""
    duration_weeks: int
    focus_name: str
    intensity_name: str
    coach_name: str
    coach_bonus_percent: int
    specialty_matches: bool
    age: int
    age_category: str
    age_note: str
    
    # Calculated estimates
    estimated_min_gains: int = 0
    estimated_max_gains: int = 0
    injury_risk_per_week: int = 0
    
    # Breakdown factors
    intensity_multiplier: float = 1.0
    coach_multiplier: float = 1.0
    focus_multiplier: float = 1.0
    specialty_multiplier: float = 1.0
    age_multiplier: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_weeks": self.duration_weeks,
            "focus_name": self.focus_name,
            "intensity_name": self.intensity_name,
            "coach_name": self.coach_name,
            "coach_bonus_percent": self.coach_bonus_percent,
            "specialty_matches": self.specialty_matches,
            "age": self.age,
            "age_category": self.age_category,
            "age_note": self.age_note,
            "estimated_min_gains": self.estimated_min_gains,
            "estimated_max_gains": self.estimated_max_gains,
            "injury_risk_per_week": self.injury_risk_per_week,
        }


def get_training_focus_options(
    coach_specialty: Optional[str] = None,
    recommended_focus: Optional[TrainingFocus] = None,
    recommendation_reason: str = "",
) -> List[TrainingFocusOption]:
    """
    Get all training focus options with coach matching info.
    
    Args:
        coach_specialty: The assigned coach's specialty (if any)
        recommended_focus: Which focus to mark as recommended
        recommendation_reason: Why that focus is recommended
        
    Returns:
        List of TrainingFocusOption objects
    """
    options = []
    
    focus_data = [
        ("1", "Striking", "Boxing, kicks, striking defense", 
         TrainingFocus.STRIKING, ["Striking"]),
        ("2", "Jiu-Jitsu", "BJJ, submissions, guard work",
         TrainingFocus.JIUJITSU, ["Jiu-Jitsu", "JIU_JITSU"]),
        ("3", "Wrestling", "Takedowns, TD defense, control",
         TrainingFocus.WRESTLING, ["Wrestling"]),
        ("4", "Conditioning", "Cardio, recovery, stamina",
         TrainingFocus.CONDITIONING, ["Conditioning"]),
        ("5", "Strength & Power", "Strength, speed, explosiveness",
         TrainingFocus.STRENGTH_POWER, ["Strength"]),
        ("6", "Balanced", "All areas (smaller gains each)",
         TrainingFocus.BALANCED, []),
    ]
    
    for key, name, desc, focus, matching_specs in focus_data:
        # Check coach match
        coach_matches = False
        if coach_specialty and matching_specs:
            coach_matches = coach_specialty in matching_specs
        
        # Check if recommended
        is_rec = (recommended_focus == focus) if recommended_focus else False
        
        options.append(TrainingFocusOption(
            key=key,
            name=name,
            description=desc,
            focus=focus,
            matching_specialties=matching_specs,
            is_recommended=is_rec,
            recommendation_reason=recommendation_reason if is_rec else "",
            coach_matches=coach_matches,
        ))
    
    return options


def get_intensity_options() -> List[IntensityOption]:
    """
    Get all intensity options for menu display.
    
    Returns:
        List of IntensityOption objects
    """
    return [
        IntensityOption(
            key="0",
            name="Rest",
            gains_percent=0,
            injury_risk_percent=0,
            description="Full rest week, recover fatigue (-15)",
            intensity=TrainingIntensity.REST,
            is_default=False,
        ),
        IntensityOption(
            key="1",
            name="Light",
            gains_percent=50,
            injury_risk_percent=0,
            description="Recovery mode, maintain skills",
            intensity=TrainingIntensity.LIGHT,
            is_default=False,
        ),
        IntensityOption(
            key="2",
            name="Moderate",
            gains_percent=100,
            injury_risk_percent=1,
            description="Standard training, balanced risk",
            intensity=TrainingIntensity.MODERATE,
            is_default=True,
        ),
        IntensityOption(
            key="3",
            name="Intense",
            gains_percent=150,
            injury_risk_percent=3,
            description="Push hard, faster improvement",
            intensity=TrainingIntensity.INTENSE,
            is_default=False,
        ),
        IntensityOption(
            key="4",
            name="Extreme",
            gains_percent=200,
            injury_risk_percent=8,
            description="Maximum effort, injury danger!",
            intensity=TrainingIntensity.EXTREME,
            is_default=False,
        ),
    ]


def recommend_training_focus(
    fighter_stats: Dict[str, int],
    opponent_stats: Optional[Dict[str, int]] = None,
    gameplan_focus: Optional[str] = None,
) -> Tuple[TrainingFocus, str]:
    """
    Recommend a training focus based on opponent and gameplan.
    
    Args:
        fighter_stats: Dict with fighter's attributes
        opponent_stats: Dict with opponent's attributes (optional)
        gameplan_focus: The gameplan focus selected (STRIKING, GRAPPLING, etc.)
        
    Returns:
        Tuple of (recommended TrainingFocus, reason string)
    """
    # Default recommendation
    recommended = TrainingFocus.CONDITIONING
    reason = "Build cardio for a tough fight"
    
    # If gameplan is set, align training with it
    if gameplan_focus:
        gameplan_upper = gameplan_focus.upper()
        if gameplan_upper == "GRAPPLING":
            recommended = TrainingFocus.WRESTLING
            reason = "Matches your grappling gameplan"
        elif gameplan_upper == "STRIKING":
            recommended = TrainingFocus.STRIKING
            reason = "Matches your striking gameplan"
        elif gameplan_upper == "CLINCH":
            recommended = TrainingFocus.WRESTLING
            reason = "Wrestling helps clinch work"
    
    # Override based on opponent threats if available
    if opponent_stats:
        # Support both old and new attribute names for compatibility
        opp_submissions = opponent_stats.get("submissions", opponent_stats.get("bjj", 50))
        opp_takedowns = opponent_stats.get("takedowns", opponent_stats.get("wrestling", 50))
        opp_striking = (opponent_stats.get("boxing", 50) + opponent_stats.get("kicks", 50)) / 2
        
        your_takedowns = fighter_stats.get("takedowns", fighter_stats.get("wrestling", 50))
        your_submissions = fighter_stats.get("submissions", fighter_stats.get("bjj", 50))
        your_striking = (fighter_stats.get("boxing", 50) + fighter_stats.get("kicks", 50)) / 2
        
        # Counter their biggest threat
        if opp_submissions >= 80 and your_takedowns < 70:
            recommended = TrainingFocus.WRESTLING
            reason = "Counter their submission game with takedown defense"
        elif opp_takedowns >= 80 and your_submissions < 65:
            recommended = TrainingFocus.JIUJITSU
            reason = "Survive if taken down"
        elif opp_striking >= 80 and your_takedowns >= 65:
            recommended = TrainingFocus.WRESTLING
            reason = "Take them out of their striking game"
        elif opp_striking >= 80 and your_striking < 65:
            recommended = TrainingFocus.STRIKING
            reason = "Close the striking gap"
    
    return recommended, reason


def estimate_camp_gains_detailed(
    weeks: int,
    focus: TrainingFocus,
    intensity: TrainingIntensity,
    coach_quality: int = 0,
    coach_specialty_matches: bool = False,
    age: int = 28,
    camp_tier: str = "GARAGE",
) -> CampSetupEstimate:
    """
    Calculate detailed estimated gains for a training camp.
    
    Args:
        weeks: Camp duration in weeks
        focus: Training focus
        intensity: Training intensity
        coach_quality: Coach quality (0-100)
        coach_specialty_matches: Whether coach specialty matches focus
        age: Fighter's age
        camp_tier: Camp tier name
        
    Returns:
        CampSetupEstimate with all calculations
    """
    # Base gains per week
    base_gains = weeks * 2
    
    # Intensity multiplier
    intensity_mult = {
        TrainingIntensity.LIGHT: 0.5,
        TrainingIntensity.MODERATE: 1.0,
        TrainingIntensity.INTENSE: 1.5,
        TrainingIntensity.EXTREME: 2.0,
    }.get(intensity, 1.0)
    
    # Coach bonus
    coach_bonus_pct = coach_quality // 10 if coach_quality else 0
    coach_mult = 1.0 + (coach_bonus_pct / 100)
    
    # Focus multiplier (non-balanced gets more focused gains)
    focus_mult = 1.3 if focus != TrainingFocus.BALANCED else 1.0
    
    # Specialty match
    specialty_mult = 1.25 if coach_specialty_matches else 1.0
    
    # Age calculations
    if age < 26:
        age_mult = 1.3
        age_category = "young"
        age_note = "Fast learner"
    elif age <= 32:
        age_mult = 1.0
        age_category = "prime"
        age_note = "Prime years"
    elif age <= 35:
        age_mult = 0.7
        age_category = "veteran"
        age_note = "Slower gains"
    else:
        age_mult = 0.4
        age_category = "old"
        age_note = "Diminished returns"
    
    # Calculate total
    total_mult = intensity_mult * coach_mult * focus_mult * specialty_mult * age_mult
    est_min = int(base_gains * total_mult * 0.8)
    est_max = int(base_gains * total_mult * 1.2)
    
    # Injury risk
    injury_risk = {
        TrainingIntensity.LIGHT: 0,
        TrainingIntensity.MODERATE: 1,
        TrainingIntensity.INTENSE: 3,
        TrainingIntensity.EXTREME: 8,
    }.get(intensity, 1)
    
    return CampSetupEstimate(
        duration_weeks=weeks,
        focus_name=focus.value,
        intensity_name=intensity.name.title(),
        coach_name="",  # Filled by caller
        coach_bonus_percent=coach_bonus_pct,
        specialty_matches=coach_specialty_matches,
        age=age,
        age_category=age_category,
        age_note=age_note,
        estimated_min_gains=est_min,
        estimated_max_gains=est_max,
        injury_risk_per_week=injury_risk,
        intensity_multiplier=intensity_mult,
        coach_multiplier=coach_mult,
        focus_multiplier=focus_mult,
        specialty_multiplier=specialty_mult,
        age_multiplier=age_mult,
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "TrainingFocus",
    "TrainingIntensity",
    "TrainingEventType",
    "CoachSpecialty",
    "CampTemplate",
    
    # Data classes
    "TrainingCamp",
    "TrainingEvent",
    "TrainingFocusOption",
    "IntensityOption",
    "CampSetupEstimate",
    
    # System
    "TrainingSystem",
    
    # Template functions
    "generate_camp_schedule",
    "estimate_template_fatigue",
    "select_ai_template",
    "TEMPLATE_INFO",
    
    # Fatigue with variance
    "get_fatigue_with_variance",
    "INTENSITY_FATIGUE_VARIANCE",
    
    # Calculations
    "calculate_training_gain",
    "calculate_diminishing_returns",
    "calculate_age_modifier",
    "calculate_camp_tier_bonus",
    "calculate_coach_quality_bonus",
    
    # Coach integration
    "coach_specialty_matches_focus",
    "SPECIALTY_TO_FOCUS",
    
    # Sparring
    "calculate_sparring_bonus",
    
    # Private lessons
    "calculate_private_lesson_score",
    "get_private_lesson_assignments",
    
    # Events
    "should_trigger_event",
    "generate_training_event",
    "TRAINING_EVENTS",
    
    # Recommendations
    "get_recommended_training",
    "estimate_camp_gains",
    
    # Camp setup helpers (NEW)
    "get_training_focus_options",
    "get_intensity_options",
    "recommend_training_focus",
    "estimate_camp_gains_detailed",
    
    # Constants
    "FOCUS_ATTRIBUTES",
    "FOCUS_DESCRIPTIONS",
    "INTENSITY_MULTIPLIERS",
    "INTENSITY_FATIGUE",
    "INTENSITY_INJURY_RISK",
]
