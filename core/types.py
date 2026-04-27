# core/types.py
# Module 1: Core Data Types
# Lines: ~700
# 
# This is the foundation vocabulary for Cage Dynasty. Everything imports from here,
# nothing imports into here. Zero dependencies = zero circular import issues.

"""
Cage Dynasty - Core Type Definitions

This module defines all fundamental types, enums, protocols, and constants
used throughout the game. It serves as the single source of truth for:
- Weight classes and divisions
- Fighter attributes and their valid ranges
- Fight outcomes and methods
- Fighting styles
- Common data structures
- Validation utilities

IMPORT RULES:
- This module imports ONLY from Python standard library
- All other game modules may import from this module
- This module NEVER imports from other game modules
"""

from typing import Protocol, Dict, List, Optional, Any, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import date, datetime
from abc import ABC, abstractmethod
import re

# ============================================================================
# VERSION & METADATA
# ============================================================================

__version__ = "1.1.0"
__module_name__ = "core.types"

# ============================================================================
# ENUMS - Game State Classifications
# ============================================================================

class WeightClass(Enum):
    """
    Official weight class divisions.
    Using Enum ensures type safety and prevents typos like "Lightweigt"
    """
    STRAWWEIGHT = "Strawweight"
    FLYWEIGHT = "Flyweight"
    BANTAMWEIGHT = "Bantamweight"
    FEATHERWEIGHT = "Featherweight"
    LIGHTWEIGHT = "Lightweight"
    WELTERWEIGHT = "Welterweight"
    MIDDLEWEIGHT = "Middleweight"
    LIGHT_HEAVYWEIGHT = "Light Heavyweight"
    HEAVYWEIGHT = "Heavyweight"


class FightOutcome(Enum):
    """All possible ways a fight can end"""
    KO = "KO"
    TKO = "TKO"
    SUBMISSION = "Submission"
    DECISION_UNANIMOUS = "Unanimous Decision"
    DECISION_SPLIT = "Split Decision"
    DECISION_MAJORITY = "Majority Decision"
    DRAW = "Draw"
    NO_CONTEST = "No Contest"
    DQ = "Disqualification"


class FighterStatus(Enum):
    """Current status of a fighter in the game"""
    ACTIVE = auto()
    INJURED = auto()
    SUSPENDED = auto()
    RETIRED = auto()
    FREE_AGENT = auto()
    NEGOTIATING = auto()


class FightingStyle(Enum):
    """
    The 11 fighting style archetypes that define how a fighter approaches combat.
    
    STAND-UP SPECIALISTS (5):
    - STRIKER: Traditional boxing/kickboxing, looking for KO
    - COUNTER_STRIKER: Reactive timing master, waits and counters
    - PRESSURE_FIGHTER: Relentless forward movement, breaks opponents
    - POINT_FIGHTER: Movement and evasion, wins decisions
    - MUAY_THAI: Kicks, knees, elbows, Thai clinch mastery
    
    GRAPPLING SPECIALISTS (4):
    - WRESTLER: Control and ride time, grinds out decisions
    - GROUND_AND_POUND: Takes down and smashes, TKO on the mat
    - BJJ_SPECIALIST: Submission hunter, dangerous from anywhere
    - CLINCH_FIGHTER: Dirty boxing, cage grinding, smothering
    
    HYBRID STYLES (2):
    - SPRAWL_AND_BRAWL: Anti-wrestler striker, refuses to go down
    - BALANCED: Complete MMA, good everywhere
    """
    # Stand-up specialists
    STRIKER = "Striker"
    COUNTER_STRIKER = "Counter Striker"
    PRESSURE_FIGHTER = "Pressure Fighter"
    POINT_FIGHTER = "Point Fighter"
    MUAY_THAI = "Muay Thai"
    
    # Grappling specialists
    WRESTLER = "Wrestler"
    GROUND_AND_POUND = "Ground & Pound"
    BJJ_SPECIALIST = "BJJ Specialist"
    CLINCH_FIGHTER = "Clinch Fighter"
    
    # Hybrid styles
    SPRAWL_AND_BRAWL = "Sprawl & Brawl"
    BALANCED = "Balanced"


class ContractStatus(Enum):
    """Status of a fighter's contract"""
    ACTIVE = auto()
    EXPIRED = auto()
    NEGOTIATING = auto()
    TERMINATED = auto()


class CampTier(Enum):
    """
    Camp quality tiers - affects training effectiveness and costs.
    Player starts at GARAGE and works up.
    """
    GARAGE = 1       # Starting level - minimal facilities
    LOCAL = 2        # Small local gym
    REGIONAL = 3     # Recognized regional camp
    NATIONAL = 4     # Well-known national camp
    ELITE = 5        # World-class mega camp


class CampCulture(Enum):
    """
    Camp philosophies that affect fighter development and chemistry.
    Each culture has distinct advantages and playstyles.
    """
    FAMILY = "family"       # High loyalty, slower turnover, chemistry bonuses
    BUSINESS = "business"   # Results-focused, higher turnover, financial bonuses
    MILITARY = "military"   # Discipline-focused, cardio/mental bonuses
    CREATIVE = "creative"   # Innovation bonuses, technique development
    ELITE = "elite"         # Only top talent, prestige bonuses, expensive


class RivalryIntensity(Enum):
    """How heated a rivalry has become"""
    MILD = 1        # Competitive respect
    MODERATE = 2    # Public callouts
    HEATED = 3      # Personal animosity
    BITTER = 4      # Deep hatred
    LEGENDARY = 5   # Historic blood feud


class InjuryType(Enum):
    """Categories of injuries with different recovery implications"""
    MINOR = auto()      # Cuts, bruises - 1-2 weeks
    MODERATE = auto()   # Sprains, minor fractures - 4-8 weeks
    SEVERE = auto()     # Broken bones, torn ligaments - 3-6 months
    CAREER = auto()     # Career-threatening - 6-12+ months


class EventType(Enum):
    """Types of events that can be emitted through the event bus"""
    # Fight events
    FIGHT_BOOKED = auto()
    FIGHT_COMPLETED = auto()
    FIGHT_CANCELLED = auto()
    
    # Fighter events
    FIGHTER_CREATED = auto()
    FIGHTER_SIGNED = auto()
    FIGHTER_RELEASED = auto()
    FIGHTER_RETIRED = auto()
    FIGHTER_INJURED = auto()
    FIGHTER_RECOVERED = auto()
    FIGHTER_RANKED = auto()
    FIGHTER_WIN = auto()
    FIGHTER_LOSS = auto()
    FIGHTER_DRAW = auto()
    
    # Camp events
    CAMP_CREATED = auto()
    CAMP_UPGRADED = auto()
    CAMP_BANKRUPT = auto()
    
    # Title events
    TITLE_WON = auto()
    TITLE_LOST = auto()
    TITLE_VACATED = auto()
    
    # Narrative events
    RIVALRY_STARTED = auto()
    RIVALRY_ESCALATED = auto()
    RIVALRY_ENDED = auto()
    
    # Time events
    WEEK_ADVANCED = auto()
    MONTH_ADVANCED = auto()
    YEAR_ADVANCED = auto()
    
    # Training events
    TRAINING_STARTED = auto()
    TRAINING_COMPLETED = auto()


# ============================================================================
# WEIGHT CLASS SPECIFICATIONS
# ============================================================================

@dataclass(frozen=True)
class WeightClassSpec:
    """
    Complete specification for a weight class.
    frozen=True makes it immutable - these values never change.
    """
    name: WeightClass
    min_weight: int
    max_weight: int
    natural_weight_avg: int  # Average natural weight for fighters in this class


# Official weight class definitions
WEIGHT_CLASS_SPECS: Dict[WeightClass, WeightClassSpec] = {
    WeightClass.STRAWWEIGHT: WeightClassSpec(
        WeightClass.STRAWWEIGHT, 106, 115, 125
    ),
    WeightClass.FLYWEIGHT: WeightClassSpec(
        WeightClass.FLYWEIGHT, 116, 125, 135
    ),
    WeightClass.BANTAMWEIGHT: WeightClassSpec(
        WeightClass.BANTAMWEIGHT, 126, 135, 145
    ),
    WeightClass.FEATHERWEIGHT: WeightClassSpec(
        WeightClass.FEATHERWEIGHT, 136, 145, 155
    ),
    WeightClass.LIGHTWEIGHT: WeightClassSpec(
        WeightClass.LIGHTWEIGHT, 146, 155, 165
    ),
    WeightClass.WELTERWEIGHT: WeightClassSpec(
        WeightClass.WELTERWEIGHT, 156, 170, 185
    ),
    WeightClass.MIDDLEWEIGHT: WeightClassSpec(
        WeightClass.MIDDLEWEIGHT, 171, 185, 200
    ),
    WeightClass.LIGHT_HEAVYWEIGHT: WeightClassSpec(
        WeightClass.LIGHT_HEAVYWEIGHT, 186, 205, 220
    ),
    WeightClass.HEAVYWEIGHT: WeightClassSpec(
        WeightClass.HEAVYWEIGHT, 206, 265, 240
    ),
}

# Ordered list for iteration (lightest to heaviest)
WEIGHT_CLASS_ORDER: List[WeightClass] = [
    WeightClass.STRAWWEIGHT,
    WeightClass.FLYWEIGHT,
    WeightClass.BANTAMWEIGHT,
    WeightClass.FEATHERWEIGHT,
    WeightClass.LIGHTWEIGHT,
    WeightClass.WELTERWEIGHT,
    WeightClass.MIDDLEWEIGHT,
    WeightClass.LIGHT_HEAVYWEIGHT,
    WeightClass.HEAVYWEIGHT,
]


# ============================================================================
# FIGHTER ATTRIBUTES
# ============================================================================

# Physical attributes (5) - natural gifts, harder to train
PHYSICAL_ATTRIBUTES: Tuple[str, ...] = (
    "strength",      # Power behind strikes, clinch control
    "speed",         # Hand speed, movement, reaction time
    "cardio",        # Stamina, gas tank
    "chin",          # Ability to absorb damage
    "recovery",      # Between-round recovery, shaking off being hurt
)

# Striking attributes (4) - standup fighting skills
STRIKING_ATTRIBUTES: Tuple[str, ...] = (
    "boxing",            # Punching technique, combinations
    "kicks",             # Kicking technique (head, body, leg)
    "clinch_striking",   # Knees, elbows, dirty boxing
    "striking_defense",  # Head movement, blocking, footwork
)

# Grappling attributes (5) - ground fighting skills
GRAPPLING_ATTRIBUTES: Tuple[str, ...] = (
    "takedowns",         # Ability to bring fight to ground
    "takedown_defense",  # Sprawl, cage wrestling defense
    "top_control",       # Holding position, GnP, preventing sweeps
    "submissions",       # Finishing ability - chokes/locks
    "guard",             # Sweeps, guard retention, getting back up
)

# Mental attributes (3) - psychological factors
MENTAL_ATTRIBUTES: Tuple[str, ...] = (
    "heart",         # Willingness to fight through adversity
    "fight_iq",      # In-fight adjustments, strategy
    "composure",     # Performance under pressure
)

# Combined tuple for iteration (17 total)
ALL_ATTRIBUTES: Tuple[str, ...] = (
    PHYSICAL_ATTRIBUTES + 
    STRIKING_ATTRIBUTES + 
    GRAPPLING_ATTRIBUTES + 
    MENTAL_ATTRIBUTES
)

# Attribute bounds
ATTR_MIN: int = 1
ATTR_MAX: int = 100
ATTR_AVERAGE: int = 50
ATTR_ELITE: int = 85  # Top-tier threshold
ATTR_PROSPECT: int = 70  # Promising threshold


# ============================================================================
# FIGHT RECORD
# ============================================================================

@dataclass(frozen=True)
class FightRecord:
    """
    Immutable fight record. Each fight creates a new record.
    Using frozen=True ensures records can't be accidentally modified.
    """
    wins: int = 0
    losses: int = 0
    draws: int = 0
    no_contests: int = 0
    
    @property
    def total_fights(self) -> int:
        return self.wins + self.losses + self.draws + self.no_contests
    
    @property
    def win_percentage(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return (self.wins / self.total_fights) * 100
    
    def with_win(self) -> 'FightRecord':
        """Return new record with one more win"""
        return FightRecord(
            self.wins + 1, self.losses, self.draws, self.no_contests
        )
    
    def with_loss(self) -> 'FightRecord':
        """Return new record with one more loss"""
        return FightRecord(
            self.wins, self.losses + 1, self.draws, self.no_contests
        )
    
    def with_draw(self) -> 'FightRecord':
        """Return new record with one more draw"""
        return FightRecord(
            self.wins, self.losses, self.draws + 1, self.no_contests
        )
    
    def __str__(self) -> str:
        base = f"{self.wins}-{self.losses}"
        if self.draws > 0:
            base += f"-{self.draws}"
        if self.no_contests > 0:
            base += f" ({self.no_contests} NC)"
        return base


# ============================================================================
# FIGHT RESULT DATA
# ============================================================================

@dataclass(frozen=True)
class FightResultData:
    """
    Complete data about a fight result.
    Used for history tracking and statistics.
    """
    winner_id: str
    loser_id: str
    outcome: FightOutcome
    round_finished: int
    time_in_round: str  # Format: "M:SS"
    weight_class: WeightClass
    was_title_fight: bool = False
    was_main_event: bool = False
    event_name: str = ""
    event_date: Optional[date] = None


# ============================================================================
# ATTRIBUTE SET
# ============================================================================

@dataclass(frozen=True)
class AttributeSet:
    """
    Complete set of fighter attributes.
    Immutable to prevent accidental changes - create new sets instead.
    """
    # Physical
    strength: int = ATTR_AVERAGE
    speed: int = ATTR_AVERAGE
    cardio: int = ATTR_AVERAGE
    chin: int = ATTR_AVERAGE
    recovery: int = ATTR_AVERAGE
    
    # Striking
    boxing: int = ATTR_AVERAGE
    kicks: int = ATTR_AVERAGE
    clinch: int = ATTR_AVERAGE
    power: int = ATTR_AVERAGE
    accuracy: int = ATTR_AVERAGE
    
    # Grappling
    wrestling: int = ATTR_AVERAGE
    bjj: int = ATTR_AVERAGE
    td_defense: int = ATTR_AVERAGE
    top_control: int = ATTR_AVERAGE
    submissions: int = ATTR_AVERAGE
    
    # Mental
    heart: int = ATTR_AVERAGE
    iq: int = ATTR_AVERAGE
    composure: int = ATTR_AVERAGE
    aggression: int = ATTR_AVERAGE
    
    def get(self, attr_name: str) -> int:
        """Get attribute value by name"""
        return getattr(self, attr_name, ATTR_AVERAGE)
    
    def with_change(self, attr_name: str, new_value: int) -> 'AttributeSet':
        """Return new AttributeSet with one attribute changed"""
        current = {k: getattr(self, k) for k in ALL_ATTRIBUTES}
        current[attr_name] = clamp(new_value, ATTR_MIN, ATTR_MAX)
        return AttributeSet(**current)
    
    @property
    def overall(self) -> int:
        """Calculate overall rating (weighted average)"""
        total = sum(getattr(self, attr) for attr in ALL_ATTRIBUTES)
        return total // len(ALL_ATTRIBUTES)
    
    @property
    def striking_overall(self) -> int:
        """Average of striking attributes"""
        total = sum(getattr(self, attr) for attr in STRIKING_ATTRIBUTES)
        return total // len(STRIKING_ATTRIBUTES)
    
    @property
    def grappling_overall(self) -> int:
        """Average of grappling attributes"""
        total = sum(getattr(self, attr) for attr in GRAPPLING_ATTRIBUTES)
        return total // len(GRAPPLING_ATTRIBUTES)


# ============================================================================
# PROTOCOLS - Interface Contracts
# ============================================================================

class Identifiable(Protocol):
    """Any entity that has a unique ID"""
    @property
    def id(self) -> str: ...


class Displayable(Protocol):
    """Any entity that can be displayed to the user"""
    def display_name(self) -> str: ...
    def short_description(self) -> str: ...


class Serializable(Protocol):
    """Any entity that can be saved/loaded"""
    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Serializable': ...


class EventEmitter(Protocol):
    """Any entity that can emit events"""
    def emit(self, event_type: EventType, data: Dict[str, Any]) -> None: ...


class EventListener(Protocol):
    """Any entity that can listen for events"""
    def on_event(self, event_type: EventType, data: Dict[str, Any]) -> None: ...


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clamp(value: int, min_val: int, max_val: int) -> int:
    """Constrain a value within a range"""
    return max(min_val, min(max_val, value))


def clamp_attribute(value: int) -> int:
    """Constrain a value to valid attribute range (1-100)"""
    return clamp(value, ATTR_MIN, ATTR_MAX)


def calculate_age(birth_date: date, reference_date: Optional[date] = None) -> int:
    """
    Calculate age in years from birth date.
    
    Args:
        birth_date: Date of birth
        reference_date: Date to calculate age at (defaults to today)
    
    Returns:
        Age in complete years
    """
    if reference_date is None:
        reference_date = date.today()
    
    age = reference_date.year - birth_date.year
    
    # Adjust if birthday hasn't occurred yet this year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return max(0, age)


def format_record(record: FightRecord) -> str:
    """Format a fight record for display"""
    return str(record)


def format_money(amount: float) -> str:
    """
    Format money for display.
    
    Examples:
        1500000 -> "$1.5M"
        75000 -> "$75K"
        500 -> "$500"
    """
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:.0f}"


def get_weight_class_for_weight(weight: float) -> Optional[WeightClass]:
    """
    Determine the appropriate weight class for a given weight.
    
    Args:
        weight: Fighter's weight in pounds
    
    Returns:
        Appropriate WeightClass or None if weight is out of range
    """
    for wc in WEIGHT_CLASS_ORDER:
        spec = WEIGHT_CLASS_SPECS[wc]
        if spec.min_weight <= weight <= spec.max_weight:
            return wc
    
    # Handle edge cases
    if weight > 265:
        return WeightClass.HEAVYWEIGHT
    return None


def weight_classes_adjacent(wc1: WeightClass, wc2: WeightClass) -> bool:
    """Check if two weight classes are adjacent (for catchweight fights)"""
    idx1 = WEIGHT_CLASS_ORDER.index(wc1)
    idx2 = WEIGHT_CLASS_ORDER.index(wc2)
    return abs(idx1 - idx2) == 1


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_fighter_name(name: str) -> str:
    """
    Validate and clean a fighter name.
    
    Raises:
        ValueError: If name is invalid
    """
    name = name.strip()
    
    if not name:
        raise ValueError("Fighter name cannot be empty")
    
    if len(name) > 50:
        raise ValueError("Fighter name cannot exceed 50 characters")
    
    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        raise ValueError("Fighter name contains invalid characters")
    
    return name


def validate_weight(weight: float, weight_class: Optional[WeightClass] = None) -> float:
    """
    Validate a fighter's weight.
    
    Args:
        weight: Weight in pounds
        weight_class: Optional weight class to validate against
    
    Raises:
        ValueError: If weight is invalid
    """
    if weight < 100 or weight > 300:
        raise ValueError(f"Weight must be between 100-300 lbs, got {weight}")
    
    if weight_class:
        spec = WEIGHT_CLASS_SPECS[weight_class]
        if weight > spec.max_weight:
            raise ValueError(
                f"Weight {weight} exceeds {weight_class.value} limit of {spec.max_weight}"
            )
    
    return weight


def validate_attribute_dict(attrs: Dict[str, int]) -> Dict[str, int]:
    """
    Validate a dictionary of attributes.
    
    Returns:
        Dictionary with all values clamped to valid range
    """
    validated = {}
    for attr in ALL_ATTRIBUTES:
        value = attrs.get(attr, ATTR_AVERAGE)
        validated[attr] = clamp_attribute(value)
    return validated


def validate_fighting_style(style: str) -> FightingStyle:
    """
    Convert string to FightingStyle enum.
    
    Raises:
        ValueError: If style is not valid
    """
    try:
        return FightingStyle(style)
    except ValueError:
        valid = [fs.value for fs in FightingStyle]
        raise ValueError(
            f"Invalid fighting style '{style}'. "
            f"Must be one of: {', '.join(valid)}"
        )


# ============================================================================
# CONSTANTS - Game Balance Values
# ============================================================================

# Age-related constants
AGE_PRIME_START: int = 26
AGE_PRIME_END: int = 32
AGE_DECLINE_START: int = 33
AGE_RETIREMENT_AVG: int = 38
AGE_MIN_DEBUT: int = 18
AGE_MAX_DEBUT: int = 28

# Training constants
TRAINING_WEEKS_PER_CAMP: int = 8
TRAINING_MAX_GAIN_PER_WEEK: int = 2
TRAINING_FATIGUE_THRESHOLD: int = 80

# Financial constants
PURSE_MINIMUM: int = 5000
PURSE_CHAMPION_MULTIPLIER: float = 3.0
SPONSORSHIP_BASE: int = 1000

# Ranking constants
RANKINGS_PER_DIVISION: int = 15
RANKINGS_CHAMPION_SLOT: int = 0  # Champion is rank 0

# Fight constants
ROUNDS_STANDARD: int = 3
ROUNDS_CHAMPIONSHIP: int = 5
ROUND_LENGTH_MINUTES: int = 5


# ============================================================================
# TYPE ALIASES - For cleaner type hints elsewhere
# ============================================================================

FighterID = str
CampID = str
EventID = str
AttributeName = str
