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
    # P3-4d added `power` — the 19th stat, 6th physical.
    "strength", "speed", "cardio", "chin", "recovery", "power",
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


# ── P3-4d C23 — CANONICAL POWER STYLE OFFSET ────────────────────────
# Single source of truth used by:
#   1) world_init._persist_fighter_to_gs (display-name lookup, e.g.
#      fighter.fighting_style == 'Knockout Artist') — bias world-gen
#      base power roll by fighting style.
#   2) game_bridge._make_fighter_attrs._a_power_derived (enum-string
#      lookup, e.g. style_key == 'STRIKER' after `_STYLE_MAP` normalizes
#      the display name) — same offset applied at load-time when a
#      pre-4d save lacks 'power' in _fighter_data.
#
# The two lookup schemes read the SAME dict via different keys — union
# entries below cover both. Values are the world_init canonical set
# (KO-artist archetypes +6..+10, grappler archetypes −4..−8, balanced
# ~0). Bridge's pre-C23 enum-keyed subset already matched these values;
# unification collapses the two tables without any behavioral drift
# vs the bridge's pre-C23 derived values for enum keys the bridge sees.
# Any drift under this ship comes from world_init's superset display
# names (e.g., 'Knockout Artist' +10 vs bridge fallback 0) which were
# never lookable from the bridge before.
POWER_STYLE_OFFSET: dict = {
    # ── Display names (used by world_init before bridge normalization) ──
    'Knockout Artist':   +10,
    'Power Puncher':     +8,
    'Sprawl & Brawl':    +6,
    'Pressure Fighter':  +5,
    'Boxing':            +4,
    'Ground and Pound':  +3,
    'Muay Thai':         +2,
    'Kickboxing':        +2,
    'Clinch Fighter':    +2,
    'Karate':             0,
    'Balanced':           0,
    'Counter Striker':   -1,
    'Point Fighter':     -2,
    'Judo':              -4,
    'Sambo':             -4,
    'Wrestler':          -6,
    'BJJ Specialist':    -8,
    # ── Dispatch-spelling aliases (BF-2, P5-B1-BIS) ──
    # world_init.FighterGenerator dispatches these display strings via
    # generate_style_for_fighter (and the fallback list at
    # world_init.py:1078). They differ from the canonical PSO entries
    # above only by punctuation ("Ground & Pound" vs "Ground and Pound")
    # or by name-vs-enum ("Striker" the display name isn't in the
    # display-key block, only "STRIKER" the enum key). Alias entries
    # inherit the canonical value so any dispatched string resolves.
    'Ground & Pound':    +3,   # alias of 'Ground and Pound'
    'Striker':           +4,   # alias of 'STRIKER' enum-key entry
    # ── Enum-key strings (used by game_bridge after _STYLE_MAP) ──
    'STRIKER':           +4,   # 'Boxing'/'Kickboxer' family
    'COUNTER_STRIKER':   -1,
    'PRESSURE_FIGHTER':  +5,
    'POINT_FIGHTER':     -2,
    'MUAY_THAI':         +2,
    'WRESTLER':          -6,
    'GROUND_AND_POUND':  +3,
    'BJJ_SPECIALIST':    -8,
    'CLINCH_FIGHTER':    +2,
    'SPRAWL_AND_BRAWL':  +6,
    'BALANCED':           0,
}
