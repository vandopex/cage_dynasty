# core/types.py — minimal stub for web app
# Only defines what fight_engine.py and fight_integration.py actually use.
# Deliberately avoids importing from typing to prevent circular import with
# stdlib types module when project types.py is on sys.path.
from enum import Enum, auto


class WeightClass(Enum):
    STRAWWEIGHT       = "Strawweight"
    FLYWEIGHT         = "Flyweight"
    BANTAMWEIGHT      = "Bantamweight"
    FEATHERWEIGHT     = "Featherweight"
    LIGHTWEIGHT       = "Lightweight"
    WELTERWEIGHT      = "Welterweight"
    MIDDLEWEIGHT      = "Middleweight"
    LIGHT_HEAVYWEIGHT = "Light Heavyweight"
    HEAVYWEIGHT       = "Heavyweight"


class FightOutcome(Enum):
    KO                 = "KO"
    TKO                = "TKO"
    SUBMISSION         = "Submission"
    DECISION_UNANIMOUS = "Unanimous Decision"
    DECISION_SPLIT     = "Split Decision"
    DECISION_MAJORITY  = "Majority Decision"
    DRAW               = "Draw"
    NO_CONTEST         = "No Contest"
    DQ                 = "Disqualification"


class FightingStyle(Enum):
    STRIKER          = "Striker"
    COUNTER_STRIKER  = "Counter Striker"
    PRESSURE_FIGHTER = "Pressure Fighter"
    POINT_FIGHTER    = "Point Fighter"
    MUAY_THAI        = "Muay Thai"
    WRESTLER         = "Wrestler"
    GROUND_AND_POUND = "Ground & Pound"
    BJJ_SPECIALIST   = "BJJ Specialist"
    CLINCH_FIGHTER   = "Clinch Fighter"
    SPRAWL_AND_BRAWL = "Sprawl & Brawl"
    BALANCED         = "Balanced"


class EventType(Enum):
    FIGHT_BOOKED      = auto()
    FIGHT_COMPLETED   = auto()
    FIGHT_CANCELLED   = auto()
    FIGHTER_CREATED   = auto()
    FIGHTER_SIGNED    = auto()
    FIGHTER_RELEASED  = auto()
    FIGHTER_RETIRED   = auto()
    FIGHTER_INJURED   = auto()
    FIGHTER_RECOVERED = auto()
    FIGHTER_RANKED    = auto()
    FIGHTER_WIN       = auto()
    FIGHTER_LOSS      = auto()
    FIGHTER_DRAW      = auto()
    CAMP_CREATED      = auto()
    CAMP_UPGRADED     = auto()
    TITLE_WON         = auto()
    TITLE_LOST        = auto()
    RIVALRY_STARTED   = auto()
    RIVALRY_ESCALATED = auto()
    WEEK_ADVANCED     = auto()
    MONTH_ADVANCED    = auto()


class FighterStatus(Enum):
    ACTIVE      = auto()
    INJURED     = auto()
    RETIRED     = auto()
    FREE_AGENT  = auto()


class InjuryType(Enum):
    MINOR    = auto()
    MODERATE = auto()
    SEVERE   = auto()
    CAREER   = auto()


# Attribute group tuples — used by aging.py, training.py, etc.
from typing import Tuple

PHYSICAL_ATTRIBUTES: Tuple[str, ...] = (
    "strength", "speed", "cardio", "chin", "recovery",
)

STRIKING_ATTRIBUTES: Tuple[str, ...] = (
    "boxing", "kicks", "clinch_striking", "striking_defense",
)

GRAPPLING_ATTRIBUTES: Tuple[str, ...] = (
    "takedowns", "takedown_defense", "top_control", "submissions", "guard",
)

MENTAL_ATTRIBUTES: Tuple[str, ...] = (
    "heart", "fight_iq", "composure",
)

ALL_ATTRIBUTES: Tuple[str, ...] = (
    PHYSICAL_ATTRIBUTES + STRIKING_ATTRIBUTES +
    GRAPPLING_ATTRIBUTES + MENTAL_ATTRIBUTES
)
