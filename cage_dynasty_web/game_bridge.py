"""
Cage Dynasty - Game Bridge
Connects Flask web app to the real CLI game engine.

This module bridges the gap between the Flask templates (which expect
a specific data format) and the real game engine classes.
"""

import sys
import os
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

# Add the cage_dynasty directory to path so we can import game modules
GAME_PATH = os.path.join(os.path.dirname(__file__), '..', 'cage_dynasty')
if os.path.exists(GAME_PATH):
    sys.path.insert(0, GAME_PATH)
else:
    GAME_PATH = os.path.expanduser('~/Desktop/Games/cage_dynasty')
    if os.path.exists(GAME_PATH):
        sys.path.insert(0, GAME_PATH)

# Also ensure the web app's OWN directory is on sys.path so flat modules
# (fotn.py, rivalry.py, judges.py, facilities.py, etc.) can be imported.
_WEB_DIR = os.path.dirname(os.path.abspath(__file__))
if _WEB_DIR not in sys.path:
    sys.path.insert(0, _WEB_DIR)

# Now try to import game modules
GAME_MODULES_AVAILABLE = False
try:
    from core.game_state import GameState, get_game_state, reset_game_state, GamePhase
    from core.persistence import save_game, load_game, list_saves
    from entities.fighter import Fighter
    from entities.camp import Camp
    from core.types import WeightClass, FightingStyle
    GAME_MODULES_AVAILABLE = True
    print("✅ Real game modules loaded successfully!")
except ImportError as e:
    print(f"⚠️ Could not load real game modules: {e}")
    print("   Running in mock mode.")

# Optional feature modules — loaded independently so one failure doesn't break others
JUDGES_AVAILABLE = False
for _judges_mod in ["judges", "systems.judges"]:
    try:
        import importlib as _ilj
        _jm = _ilj.import_module(_judges_mod)
        generate_decision              = _jm.generate_decision
        calculate_dominance_from_fight = getattr(_jm, "calculate_dominance_from_fight", None)
        DecisionResult                 = getattr(_jm, "DecisionResult", None)
        DecisionType                   = _jm.DecisionType
        JUDGES_AVAILABLE               = True
        print(f"✅ judges loaded from {_judges_mod}")
        break
    except (ImportError, AttributeError):
        pass
if not JUDGES_AVAILABLE:
    print("⚠️ judges not available")

FOTN_AVAILABLE = False
for _fotn_mod in ["fotn", "systems.fotn"]:
    try:
        import importlib as _ilf
        _fm = _ilf.import_module(_fotn_mod)
        select_fotn              = _fm.select_fotn
        FOTN_BONUS               = _fm.FOTN_BONUS
        get_excitement_tier      = getattr(_fm, "get_excitement_tier", lambda s: "standard")
        format_fotn_announcement = getattr(_fm, "format_fotn_announcement", None)
        FOTN_AVAILABLE           = True
        print(f"✅ fotn loaded from {_fotn_mod}")
        break
    except (ImportError, AttributeError):
        pass
if not FOTN_AVAILABLE:
    FOTN_BONUS = 50000
    print("⚠️ fotn not available — using builtin")

RIVALRY_AVAILABLE = False
for _rivalry_path in ["rivalry", "narrative.rivalry"]:
    try:
        import importlib as _ilr
        _rm = _ilr.import_module(_rivalry_path)
        FightContext         = _rm.FightContext
        get_rivalry_system   = _rm.get_rivalry_system
        get_heat_description = getattr(_rm, "get_heat_description", lambda s: "")
        get_heat_stage       = _rm.get_heat_stage
        HeatStage            = _rm.HeatStage
        RivalryIntensity     = _rm.RivalryIntensity
        RIVALRY_AVAILABLE    = True
        print(f"✅ rivalry loaded from {_rivalry_path}")
        break
    except (ImportError, AttributeError):
        pass
if not RIVALRY_AVAILABLE:
    print("⚠️ rivalry not available")

FACILITIES_AVAILABLE = False
try:
    from facilities import (
        get_effective_training_gain, get_stat_cap,
        FACILITY_STAT_CAPS, TRAINING_EFFICIENCY,
    )
    FACILITIES_AVAILABLE = True
    print("✅ facilities.py loaded")
except ImportError as e:
    print(f"⚠️ facilities.py not available: {e}")

INJURY_AVAILABLE = False
try:
    from systems.injury import (
        InjurySystem, InjuryType, generate_fight_injury,
        generate_training_injury, calculate_fight_injury_probability,
        calculate_training_injury_probability, RECOVERY_TIMES,
    )
    from core.types import FightOutcome
    INJURY_AVAILABLE = True
    print("✅ injury system loaded from systems.injury")
except ImportError as e:
    print(f"⚠️ injury system not available: {e}")
    InjurySystem = None

MEDIA_AVAILABLE = False
for _media_path in ["media", "narrative.media"]:
    try:
        import importlib as _ilm
        _mm = _ilm.import_module(_media_path)
        generate_fight_reactions = _mm.generate_fight_reactions
        MEDIA_AVAILABLE = True
        print(f"✅ media loaded from {_media_path}")
        break
    except (ImportError, AttributeError):
        pass
if not MEDIA_AVAILABLE:
    print("⚠️ media not available")

SCOUTING_AVAILABLE = False
for _scout_mod in ["scouting", "systems.scouting"]:
    try:
        import importlib as _ils
        _sm = _ils.import_module(_scout_mod)
        get_fighter_strengths  = _sm.get_fighter_strengths
        get_fighter_weaknesses = _sm.get_fighter_weaknesses
        assess_potential       = _sm.assess_potential
        POTENTIAL_GRADES       = _sm.POTENTIAL_GRADES
        SCOUTING_AVAILABLE     = True
        print(f"✅ scouting loaded from {_scout_mod}")
        break
    except (ImportError, AttributeError):
        pass
if not SCOUTING_AVAILABLE:
    print("⚠️ scouting not available")

TRAITS_AVAILABLE = False
for _traits_mod in ["traits", "systems.traits"]:
    try:
        import importlib as _ilt
        _tm = _ilt.import_module(_traits_mod)
        FIGHTER_TRAITS                   = _tm.FIGHTER_TRAITS
        get_trait_fight_modifiers        = _tm.get_trait_fight_modifiers
        get_trait_win_bonus              = getattr(_tm, "get_trait_win_bonus", lambda t: 0.0)
        get_pressure_counter_interaction = getattr(_tm, "get_pressure_counter_interaction", lambda a, b: (0.0, 0.0))
        TRAITS_AVAILABLE                 = True
        print(f"✅ traits loaded from {_traits_mod}")
        break
    except (ImportError, AttributeError):
        pass
if not TRAITS_AVAILABLE:
    print("⚠️ traits not available")

CONDITION_AVAILABLE = False
for _cond_mod in ["condition", "systems.condition"]:
    try:
        import importlib as _ilc
        _cm = _ilc.import_module(_cond_mod)
        get_starting_stamina  = _cm.get_starting_stamina
        get_fight_readiness   = _cm.get_fight_readiness
        get_fatigue_category  = _cm.get_fatigue_category
        CONDITION_AVAILABLE   = True
        print(f"✅ condition loaded from {_cond_mod}")
        break
    except (ImportError, AttributeError):
        pass
if not CONDITION_AVAILABLE:
    print("⚠️ condition not available")

FIGHT_ENGINE_AVAILABLE = False
try:
    import sys as _sys, os as _os
    _web_dir = _os.path.dirname(_os.path.abspath(__file__))
    # Ensure web dir is FIRST — must beat CLI root fight_engine.py
    if _sys.path and _sys.path[0] != _web_dir:
        _sys.path.insert(0, _web_dir)

    # Force reload fight_engine from web dir in case CLI version was cached
    for _mod in ['fight_engine', 'fight_integration']:
        if _mod in _sys.modules:
            del _sys.modules[_mod]

    import fight_integration as _fem
    _simulate_narrated_fight_fn = _fem.simulate_narrated_fight
    _FighterAttributes          = _fem.FighterAttributes
    _NarratedFightResult        = _fem.NarratedFightResult
    try:
        _FightConfig = _fem.FightConfig if hasattr(_fem, 'FightConfig') else None
    except Exception:
        _FightConfig = None
    try:
        FI_DAMAGE_MULTIPLIER = _fem.FI_DAMAGE_MULTIPLIER if hasattr(_fem, 'FI_DAMAGE_MULTIPLIER') else 0.42
    except Exception:
        FI_DAMAGE_MULTIPLIER = 0.42
    FIGHT_ENGINE_AVAILABLE      = True
    print("✅ fight engine loaded from fight_integration")
except Exception as _fe_e:
    print(f"⚠️ fight_integration not available: {_fe_e}")
    _FightConfig = None
    FI_DAMAGE_MULTIPLIER = 0.42
if not FIGHT_ENGINE_AVAILABLE:
    print("⚠️ fight engine falling back to score-based simulation")

POPULARITY_AVAILABLE = False
for _pop_mod in ["popularity", "systems.popularity"]:
    try:
        import importlib as _ilp2
        _pm = _ilp2.import_module(_pop_mod)
        calculate_popularity_change = _pm.calculate_popularity_change
        apply_popularity_decay      = _pm.apply_popularity_decay
        POPULARITY_AVAILABLE        = True
        print(f"✅ popularity loaded from {_pop_mod}")
        break
    except (ImportError, AttributeError):
        pass
if not POPULARITY_AVAILABLE:
    print("⚠️ popularity not available")

TOT_AVAILABLE = False
for _tot_mod in ["tale_of_tape", "systems.tale_of_tape"]:
    try:
        import importlib as _iltot
        _tot = _iltot.import_module(_tot_mod)
        FighterTapeData       = _tot.FighterTapeData
        generate_tale_of_tape = _tot.generate_tale_of_tape
        analyze_matchup       = _tot.analyze_matchup
        TOT_AVAILABLE         = True
        print(f"✅ tale_of_tape loaded from {_tot_mod}")
        break
    except (ImportError, AttributeError):
        pass
if not TOT_AVAILABLE:
    print("⚠️ tale_of_tape not available")

WATCHLIST_AVAILABLE = False
for _wl_mod in ["watchlist", "systems.watchlist"]:
    try:
        import importlib as _ilwl
        _wlm = _ilwl.import_module(_wl_mod)
        Watchlist        = _wlm.Watchlist
        WatchCategory    = _wlm.WatchCategory
        WatchPriority    = _wlm.WatchPriority
        CATEGORY_INFO    = _wlm.CATEGORY_INFO
        PRIORITY_SYMBOLS = _wlm.PRIORITY_SYMBOLS
        WATCHLIST_AVAILABLE = True
        print(f"✅ watchlist loaded from {_wl_mod}")
        break
    except (ImportError, AttributeError):
        pass
if not WATCHLIST_AVAILABLE:
    print("⚠️ watchlist not available")

CARD_BUILDER_AVAILABLE = False
try:
    from card_builder import CardBuilder, CardSlot, SLOT_LIMITS, SCORE_THRESHOLDS
    CARD_BUILDER_AVAILABLE = True
    print("✅ card_builder loaded")
except Exception as _cbe:
    print(f"⚠️ card_builder not available: {_cbe}")

MATCHMAKING_AVAILABLE = False
try:
    from matchmaking import calculate_cooldown, is_title_eligible, MatchmakingEngine
    MATCHMAKING_AVAILABLE = True
    print("✅ matchmaking loaded")
except Exception as _mme:
    print(f"⚠️ matchmaking not available: {_mme}")

AGING_AVAILABLE = False
try:
    from aging import (
        AgingSystem, get_career_phase, calculate_retirement_probability,
        CareerPhase,
    )
    AGING_AVAILABLE = True
    print("✅ aging loaded")
except Exception as _ae:
    print(f"⚠️ aging not available: {_ae}")

FACILITIES_AVAILABLE = False
try:
    from facilities import (
        get_stat_cap, get_effective_training_gain,
        get_max_fighters, apply_facility_cap,
    )
    FACILITIES_AVAILABLE = True
    print("✅ facilities loaded")
except Exception as _fe2:
    print(f"⚠️ facilities not available: {_fe2}")

MAINTENANCE_AVAILABLE = False
try:
    from maintenance_training import (
        MaintenanceTrainingSystem, process_weekly_maintenance,
    )
    MAINTENANCE_AVAILABLE = True
    print("✅ maintenance_training loaded")
except Exception as _me:
    print(f"⚠️ maintenance_training not available: {_me}")

STYLES_AVAILABLE = False
try:
    from styles import get_style_matchup_modifier
    from core.types import FightingStyle as _FightingStyleEnum
    STYLES_AVAILABLE = True
    print("✅ styles loaded")
except Exception as _se:
    print(f"⚠️ styles not available: {_se}")


# ============================================================================
# WEIGHT CLASS CONSTANTS
# ============================================================================

WEIGHT_CLASSES = [
    "Strawweight", "Flyweight", "Bantamweight", "Featherweight",
    "Lightweight", "Welterweight", "Middleweight", 
    "Light Heavyweight", "Heavyweight"
]

DIVISION_ABBREV = {
    "Strawweight": "STW", "Flyweight": "FLW", "Bantamweight": "BW",
    "Featherweight": "FW", "Lightweight": "LW", "Welterweight": "WW",
    "Middleweight": "MW", "Light Heavyweight": "LHW", "Heavyweight": "HW"
}

# ── Contract system constants ─────────────────────────────────────────────────
CONTRACT_OPTIONS = {
    3: {"label": "3-Fight Deal",  "premium": 1.00, "min_tier": "GARAGE"},
    6: {"label": "6-Fight Deal",  "premium": 1.12, "min_tier": "LOCAL"},
    9: {"label": "9-Fight Deal",  "premium": 1.20, "min_tier": "NATIONAL"},
}
# Morale thresholds
MORALE_HOLDOUT   = 25   # Below this: fighter enters holdout (last warning)
MORALE_WALKOUT   = 10   # Below this: fighter walks — becomes free agent
HOLDOUT_WINDOW   = 4    # Weeks before a holdout fighter walks
# Tier unlock for contract lengths
TIER_CONTRACT_MAX = {
    "GARAGE": 3, "LOCAL": 6, "REGIONAL": 6, "NATIONAL": 9, "ELITE": 9
}

# ── Founding fighter ───────────────────────────────────────────────────────────
# Player's starter fighter (created at new-game). Invisible loyalty bonus:
# tougher to lose, accepts longer deals. Tunable; designed to be felt over a
# long career, not noticed in one session. No badge, no UI indicator —
# the flag lives only in the _contracts dict.
FOUNDING_FIGHTER_MORALE_FLOOR     = 45   # Won't drop below this (normal: no floor)
FOUNDING_FIGHTER_LOSS_PENALTY     = 7    # Per-loss morale hit (normal: 10)
FOUNDING_FIGHTER_STREAK_PENALTY   = 2    # Per-streak compounding (normal: 3)
FOUNDING_FIGHTER_IDLE_THRESHOLD   = 14   # Idle weeks before decay starts (normal: 10)
FOUNDING_FIGHTER_IDLE_DECAY       = 1    # Idle decay per week (normal: 2)
FOUNDING_FIGHTER_HOLDOUT_WINDOW   = 7    # Weeks to re-sign before walk (normal: 4 — HOLDOUT_WINDOW)
FOUNDING_FIGHTER_MAX_CONTRACT     = 5    # Max fight length regardless of tier (normal: tier-gated)
FOUNDING_FIGHTER_WALK_ROSTER_HIT  = 10   # Morale loss applied to remaining fighters when founder walks
# Non-founder walk roster hit also -10, fires only when fighter is "important":
# is_champion OR top-10 ranked OR fights_completed >= 6

# ── Coach contracts ──────────────────────────────────────────────
# Ship C2: dumber version of fighter contracts. Financial-pressure
# system: coaches quit if underpaid or paychecks get skipped.
# No holdout, no severance, no W/L morale. Asymmetric from fighters.
COACH_DEFAULT_CONTRACT_WEEKS  = 52    # 1-year default
COACH_MORALE_START            = 80    # signing morale
COACH_MORALE_WALKOUT          = 10    # below this: walks immediately
COACH_UNDERPAID_DECAY         = 1     # morale loss per week if underpaid
COACH_UNDERPAID_THRESHOLD     = 0.85  # salary < 85% of market rate = underpaid
COACH_SKIPPED_PAYCHECK_DECAY  = 3     # morale loss per skipped paycheck
COACH_MARKET_RATE_PER_RATING  = 12    # base $/wk per rating point (75 rating = $900/wk market)
# Tier-gated contract length options for hiring
COACH_TIER_CONTRACT_OPTIONS = {
    "GARAGE":   [26],
    "LOCAL":    [26, 52],
    "REGIONAL": [26, 52, 78],
    "NATIONAL": [26, 52, 78],
    "ELITE":    [52, 78, 104],
}
# Ship MC1b: max coaching staff size per tier
COACH_TIER_STAFF_SLOTS = {
    "GARAGE":   1,
    "LOCAL":    2,
    "REGIONAL": 3,
    "NATIONAL": 4,
    "ELITE":    5,
}
# Placeholder when no coach hired — keeps existing read sites safe
COACH_VACANT_PLACEHOLDER = {
    "name":      "Vacant",
    "specialty": "none",
    "rating":    0,
    "salary":    0,
}

# Promotion brand name — used for all event name generation.
# Change here to rename everywhere.
PROMOTION_NAME = "Cage Dynasty"

# ── Corner advice ────────────────────────────────────────────────
# Ship K1: between-round coach advice for player fights. Reactive
# to RoundStats; specialty + rating tier determine content depth.
# Path α mechanical bonus: small pre-fight attribute buff to the
# player fighter — approximation of "having a good coach helps"
# (per-round reactive buffs need engine surgery, deferred).
CORNER_ADVICE_ENABLED          = True
CORNER_RATING_TIER_LOW         = 65    # rating <= this: tier "low"
CORNER_RATING_TIER_MID         = 80    # rating <= this and > LOW: tier "mid"
                                       # rating > MID: tier "high"
CORNER_BONUS_BASE              = 1.0   # base bonus magnitude when advice fires
CORNER_BONUS_PER_RATING_POINT  = 0.04  # extra bonus per rating point above 60
CORNER_SECONDARY_DOMAIN_MIN    = 80    # min rating to give secondary-domain reads
CORNER_GENERALIST_DEPTH_MIN    = 75    # MMA head coach min rating for deeper reads

# ── Training history ──────────────────────────────────────────────────────────
# Ship A: rolling per-fighter training log surfaced on dashboard.
# Each entry captures one week's training-plan gains, coach passive boosts,
# and maintenance decays. FIFO eviction at this depth.
TRAINING_HISTORY_WEEKS = 4

# ── Camp personality archetypes ───────────────────────────────────────────────
# Each archetype has signing preferences as weight multipliers.
# Higher = more likely to sign that type of fighter.
CAMP_ARCHETYPES = {
    "Prospect Factory": {
        "desc":         "Develops raw young talent into stars",
        "age_max":      24,       # Strongly prefers under 24
        "age_bonus":    3.0,      # 3x score for young fighters
        "potential_min":75,       # Won't touch low-ceiling prospects
        "potential_bonus":2.5,    # Ceiling matters most
        "ovr_care":     0.3,      # Doesn't care much about current rating
        "style_pref":   [],       # No style preference
        "emoji":        "🌱",
    },
    "Veteran Hub": {
        "desc":         "Signs proven fighters in their prime or late career",
        "age_min":      28,       # Prefers experienced fighters
        "age_bonus":    2.0,
        "win_bonus":    2.0,      # Record matters
        "potential_min":0,        # Doesn't care about ceiling
        "ovr_care":     2.0,      # Current rating important
        "style_pref":   [],
        "emoji":        "⚔️",
    },
    "Striker's Gym": {
        "desc":         "Builds world-class stand-up fighters",
        "style_pref":   ["Striker","Muay Thai","Pressure Fighter","Counter Striker","Brawler"],
        "style_bonus":  2.5,
        "style_penalty":0.4,      # Penalizes grapplers
        "grapple_styles":["Wrestler","BJJ Specialist","Grappler","Ground & Pound"],
        "ovr_care":     1.0,
        "emoji":        "🥊",
    },
    "Wrestling Room": {
        "desc":         "Dominant grappling-based camp",
        "style_pref":   ["Wrestler","Ground & Pound","Grappler","BJJ Specialist"],
        "style_bonus":  2.5,
        "style_penalty":0.5,
        "grapple_styles":["Striker","Muay Thai","Brawler"],
        "ovr_care":     1.0,
        "emoji":        "🤼",
    },
    "Submission Specialists": {
        "desc":         "Elite BJJ and submission-based camp",
        "style_pref":   ["BJJ Specialist","Grappler","Wrestler"],
        "style_bonus":  2.8,
        "style_penalty":0.4,
        "grapple_styles":["Striker","Muay Thai","Pressure Fighter"],
        "ovr_care":     0.8,
        "emoji":        "🥋",
    },
    "Star Factory": {
        "desc":         "Signs high-profile fighters with crowd appeal",
        "popularity_bonus": 3.0,  # Popularity matters hugely
        "popularity_min":   30,
        "win_bonus":    1.5,
        "ovr_care":     1.5,
        "style_pref":   [],
        "emoji":        "⭐",
    },
    "Hometown Camp": {
        "desc":         "Signs local fighters from same country/region",
        "nationality_bonus": 4.0, # Massive bonus for same nationality
        "ovr_care":     0.8,
        "style_pref":   [],
        "emoji":        "🏠",
    },
    "Numbers Game": {
        "desc":         "Signs whoever is available — maximizes roster size",
        "ovr_care":     0.5,
        "style_pref":   [],
        "emoji":        "📊",
    },
    "Elite Academy": {
        "desc":         "Top-tier camp, only signs proven ranked fighters",
        "rank_bonus":   3.0,      # Ranked fighters get huge bonus
        "rank_max":     8,        # Only signs top-8 or better
        "ovr_min":      72,       # Won't touch sub-72 OVR
        "ovr_care":     2.0,
        "style_pref":   [],
        "emoji":        "🏆",
    },
    "Finisher Stable": {
        "desc":         "Loves high-finish-rate fighters",
        "finish_bonus": 2.5,      # Bonus for KO/SUB artists
        "ovr_care":     0.8,
        "style_pref":   ["Striker","BJJ Specialist","Brawler","Pressure Fighter"],
        "style_bonus":  1.5,
        "emoji":        "💥",
    },
}

def _assign_camp_archetype(camp_name: str, camp_country: str,
                            camp_tier: str, camp_id: str) -> str:
    """
    Assign a personality archetype to an AI camp based on name/country/tier.
    Uses deterministic seeding so the same camp always gets the same archetype.
    """
    import hashlib
    seed = int(hashlib.md5(camp_id.encode()).hexdigest(), 16) % 1000

    # Country biases
    country_bias: dict = {
        "Brazil":        ["Submission Specialists", "Finisher Stable"],
        "Russia":        ["Wrestling Room", "Veteran Hub"],
        "Kazakhstan":    ["Wrestling Room", "Submission Specialists"],
        "Uzbekistan":    ["Wrestling Room", "Numbers Game"],
        "United States": ["Star Factory", "Elite Academy", "Striker's Gym",
                          "Prospect Factory", "Numbers Game"],
        "United Kingdom":["Striker's Gym", "Prospect Factory"],
        "Ireland":       ["Striker's Gym", "Finisher Stable"],
        "Japan":         ["Submission Specialists", "Veteran Hub"],
        "Netherlands":   ["Striker's Gym", "Finisher Stable"],
    }
    # Tier biases
    tier_bias: dict = {
        "ELITE":    ["Elite Academy", "Star Factory", "Veteran Hub"],
        "NATIONAL": ["Star Factory", "Elite Academy", "Prospect Factory"],
        "REGIONAL": ["Prospect Factory", "Hometown Camp", "Numbers Game"],
        "LOCAL":    ["Numbers Game", "Hometown Camp", "Prospect Factory"],
        "GARAGE":   ["Numbers Game", "Hometown Camp"],
    }

    candidates = list(CAMP_ARCHETYPES.keys())
    # Weight by country then tier
    country_favored = country_bias.get(camp_country, [])
    tier_favored    = tier_bias.get(camp_tier.upper(), [])
    # Build weighted pool: base 1 each, +3 for country match, +2 for tier match
    weights = {a: 1 for a in candidates}
    for a in country_favored:
        weights[a] = weights.get(a, 1) + 3
    for a in tier_favored:
        weights[a] = weights.get(a, 1) + 2

    pool = []
    for a, w in weights.items():
        pool.extend([a] * w)

    # Pick deterministically from seeded index
    return pool[seed % len(pool)]


# ============================================================================
# WEB-FRIENDLY DATA CLASSES
# ============================================================================

@dataclass
class WebFighter:
    """Fighter data formatted for web templates"""
    # Identity — no defaults
    fighter_id: str
    name: str
    nickname: Optional[str]
    age: int
    country: str
    weight_class: str
    division_abbrev: str
    fighting_style: str
    wins: int
    losses: int
    draws: int
    ko_wins: int
    sub_wins: int
    record_str: str
    overall_rating: int
    potential: int
    fights_total: int
    ovr_at_signing: int
    popularity: int
    ranking: Optional[int]
    is_champion: bool
    is_active: bool

    # Physical
    height: str
    reach: str

    # Attributes (17 total)
    strength: int
    speed: int
    cardio: int
    chin: int
    recovery: int
    boxing: int
    kicks: int
    clinch_striking: int
    striking_defense: int
    takedowns: int
    takedown_defense: int
    top_control: int
    submissions: int
    guard: int
    heart: int
    fight_iq: int
    composure: int

    # Status
    fatigue: int
    morale: int
    condition_status: str
    condition_color: str

    # Streaks
    win_streak: int
    lose_streak: int

    # Traits & history
    traits: List[str]
    fight_history: List[Dict[str, Any]]

    # ── Fields with defaults must come LAST ─────────────────────────────
    momentum_tag:     str  = ""
    is_injured:       bool = False
    injury_desc:      str  = ""
    injury_weeks_out: int  = 0
    camp_id:          Optional[str] = None
    camp_name:        str  = ""
    # Loss method breakdown (default 0 so legacy saves load cleanly;
    # populated from FighterRecord.ko_losses / sub_losses if present).
    ko_losses:        int  = 0
    sub_losses:       int  = 0
    # Chin durability tracking (Ship #44)
    ko_losses_received: int   = 0
    chin_perm_erosion:  float = 0.0
    # Career FOTN awards — incremented when fighter is part of FOTN selection.
    career_fotn_awards: int = 0
    # Body frame relative to weight class (1=very small, 10=very large).
    # Drives cut severity in the engine and division-move alerts.
    body_frame:            int = 5
    natural_weight_class:  str = ""


@dataclass
class WebCamp:
    """Camp data formatted for web templates"""
    camp_id: str
    name: str
    tier: str
    location: str
    reputation: int
    balance: int
    is_player: bool
    max_fighters: int
    fighter_ids: List[str]
    
    # Record
    wins: int
    losses: int
    record_str: str
    win_percentage: int
    championships: int
    
    # Coach
    head_coach_name: str
    head_coach_specialty: str
    head_coach_rating: int


@dataclass  
class WebFightOffer:
    """Fight offer formatted for web templates"""
    offer_id: str
    fighter_id: str
    opponent_id: str
    opponent_name: str
    opponent_record: str
    opponent_rating: int
    opponent_rank: Optional[int]
    event_name: str
    week: int
    weeks_away: int
    purse: int
    win_bonus: int
    is_title_fight: bool
    risk_level: int  # 1-5
    reward_level: int  # 1-5
    matchup_quality: str
    accept_chance: int


@dataclass
class WebNewsItem:
    """News item formatted for web templates"""
    news_id: str
    headline: str
    category: str
    week: int
    icon: str


# ============================================================================
# CARD CAPACITY CONSTANT (sub-ship A)
# Shared between _build_card_for_week's target count, Phase 2 capacity gate
# in _top_up_pipeline, and load-time auto-truncate in from_dict.
# ============================================================================
CARD_TARGET_FIGHTS = 9

# ============================================================================
# PIPELINE WINDOW CONSTANT (Ship D2)
# Rolling card pipeline depth. Shared across:
# - Phase 3 build loop in _top_up_pipeline
# - Phase 2 hand-off drain filter
# - In-window booking check in title-fight booker
# Increase to show fights further out on the schedule.
# ============================================================================
PIPELINE_WINDOW_WEEKS = 8   # Rolling card pipeline depth.


# =============================================================
# SPONSOR SYSTEM (Ship S1)
# Each brand has tier (local/regional/elite), personality
# (aggressive/image/loyalty/prestige), weekly retainer paid to
# camp, per-fight bonus, attribute boost dict applied at engine
# call, and client cap.
# =============================================================
SPONSOR_BRANDS = {
    "aggressive": [
        {"id": "apex_combat",    "name": "Apex Combat",
         "tier": "local",    "personality": "aggressive",
         "weekly_retainer": 200,  "fight_bonus": 800,
         "attr_boost": {"chin": 1, "heart": 1},
         "boost_pct": 0.01, "max_clients": 8},
        {"id": "iron_will",      "name": "Iron Will Energy",
         "tier": "regional", "personality": "aggressive",
         "weekly_retainer": 600,  "fight_bonus": 4000,
         "attr_boost": {"chin": 2, "heart": 2},
         "boost_pct": 0.02, "max_clients": 4},
        {"id": "venom_sports",   "name": "Venom Sports",
         "tier": "elite",    "personality": "aggressive",
         "weekly_retainer": 2000, "fight_bonus": 25000,
         "attr_boost": {"chin": 3, "heart": 3},
         "boost_pct": 0.03, "max_clients": 2},
    ],
    "image": [
        {"id": "metro_wear",     "name": "Metro Wear",
         "tier": "local",    "personality": "image",
         "weekly_retainer": 150,  "fight_bonus": 700,
         "attr_boost": {"composure": 1, "fight_iq": 1},
         "boost_pct": 0.01, "max_clients": 10},
        {"id": "pinnacle_gear",  "name": "Pinnacle Gear",
         "tier": "regional", "personality": "image",
         "weekly_retainer": 500,  "fight_bonus": 3500,
         "attr_boost": {"composure": 2, "fight_iq": 2},
         "boost_pct": 0.02, "max_clients": 5},
        {"id": "champion_brand", "name": "Champion Brand",
         "tier": "elite",    "personality": "image",
         "weekly_retainer": 1800, "fight_bonus": 20000,
         "attr_boost": {"composure": 3, "fight_iq": 3},
         "boost_pct": 0.03, "max_clients": 2},
    ],
    "loyalty": [
        {"id": "hometown_gym",   "name": "Hometown Gym",
         "tier": "local",    "personality": "loyalty",
         "weekly_retainer": 100,  "fight_bonus": 500,
         "attr_boost": {"cardio": 1, "recovery": 1},
         "boost_pct": 0.01, "max_clients": 10},
        {"id": "regional_pride", "name": "Regional Pride",
         "tier": "regional", "personality": "loyalty",
         "weekly_retainer": 400,  "fight_bonus": 3000,
         "attr_boost": {"cardio": 2, "recovery": 2},
         "boost_pct": 0.02, "max_clients": 5},
        {"id": "legacy_sports",  "name": "Legacy Sports",
         "tier": "elite",    "personality": "loyalty",
         "weekly_retainer": 1500, "fight_bonus": 18000,
         "attr_boost": {"cardio": 3, "recovery": 3},
         "boost_pct": 0.03, "max_clients": 3},
    ],
    "prestige": [
        {"id": "elite_wear",     "name": "Elite Wear",
         "tier": "elite",    "personality": "prestige",
         "weekly_retainer": 2500, "fight_bonus": 35000,
         "attr_boost": {"boxing": 2, "speed": 2,
                        "composure": 2, "chin": 1},
         "boost_pct": 0.03, "max_clients": 1},
    ],
}

# Flat lookup by brand id
_SPONSOR_BY_ID = {
    b["id"]: b
    for brands in SPONSOR_BRANDS.values()
    for b in brands
}


# ============================================================================
# GAME BRIDGE CLASS
# ============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# POTENTIAL DISPLAY GRADES
# Internal data uses Elite/High/Average/Limited/Low.
# UI always shows A+/A/A-/B+/B/B-/C+/C/C-/D.
# One conversion function — no logic elsewhere changes.
# ─────────────────────────────────────────────────────────────────────────────
def ceiling_to_display_grade(ceiling: int) -> str:
    """Convert a potential ceiling (0-99) to a display grade (A+, A, A-, ... D).
    Thresholds align with existing Elite(88+)/High(78+)/Average(65+)/Limited(55+)/Low bands.
    """
    if ceiling >= 94: return "A+"   # 94-99: true generational
    if ceiling >= 88: return "A"    # 88-93: elite (former "Elite" band top)
    if ceiling >= 83: return "A-"   # 83-87: elite low end
    if ceiling >= 78: return "B+"   # 78-82: high potential (former "High" top)
    if ceiling >= 73: return "B"    # 73-77: high potential mid
    if ceiling >= 65: return "B-"   # 65-72: high potential low / average top
    if ceiling >= 58: return "C+"   # 58-64: average
    if ceiling >= 50: return "C"    # 50-57: limited
    if ceiling >= 42: return "C-"   # 42-49: limited low
    return "D"                       # <42: low

def grade_color(display_grade: str) -> str:
    """CSS color for a display grade."""
    return {
        "A+": "#ffd700", "A": "#ffd700", "A-": "#ffe44d",
        "B+": "#00e676", "B": "#00e676", "B-": "#4caf50",
        "C+": "#29b6f6", "C": "#29b6f6", "C-": "#78909c",
        "D":  "#616161",
    }.get(display_grade, "#9e9e9e")


class GameBridge:
    """
    Bridges the Flask web app to the real game engine.
    
    Handles all translation between game data structures and
    web-friendly formats expected by templates.
    """
    
    def __init__(self):
        self.game_started = False
        self._game_state: Optional[Any] = None
        self._mock_mode = not GAME_MODULES_AVAILABLE
        
        # Cache for expensive operations
        self._fighter_cache: Dict[str, WebFighter] = {}
        self._camp_cache: Dict[str, WebCamp] = {}
        
        # Internal tracking for real mode (simple implementation)
        self._scheduled_fights: List[Dict[str, Any]] = []
        # Sub-ship A: AI fights with target_week beyond pipeline window.
        # Drained into _upcoming_cards by _top_up_pipeline's hand-off pass
        # when target_week enters current+1..current+8. Strict invariant:
        # an AI fight is in EITHER this list OR _upcoming_cards, never both.
        self._ai_deferred_bookings: List[Dict[str, Any]] = []
        self._fight_offers: List[Dict[str, Any]] = []
        self._completed_events: List[Dict[str, Any]] = []
        self._news_items: List[Dict[str, Any]] = []

        # Negotiation + fight camp state
        self._pending_negotiations: Dict[str, Any] = {}   # neg_id -> negotiation dict
        # Ship K5: async player challenges — AI responds in 1-2 weeks
        self._pending_challenges: Dict[str, Any] = {}     # chal_id -> challenge dict
        # Ship A1: track fighters signed from amateur circuit (for graduates tab)
        self._amateur_graduates: List[Dict[str, Any]] = []
        self._fight_camps: Dict[str, Any] = {}            # fight_id -> camp choices dict
        self._neg_counter: int = 0

        # Economy state
        self._camp_balance:  int = 50000
        self._camp_location:   str  = "Las Vegas, NV"
        self._player_camp_wins:   int = 0  # tracked separately — persists through save/load
        self._player_camp_losses: int = 0
        self._last_week_recap:  Dict[str, Any] = {}  # server-side recap storage
        self._last_fight_night: Dict[str, Any] = {}  # server-side fight night storage           # Starting balance
        self._camp_name:    str = "My Camp"       # Camp name
        self._total_purses_earned: int = 0
        self._week_purses_earned:  int = 0  # resets each advance_week — shown on recap
        self._total_overhead_paid: int = 0

        # Coach data — stored from new_game setup
        self._coach: Dict[str, Any] = {
            "name":      "Head Coach",
            "specialty": "boxing",
            "rating":    60,
            "salary":    800,
        }

        # Ship C2: coach contract — parallels fighter _contracts but simpler.
        # {} when no coach hired (vacant). Always paired with _coach dict.
        self._coach_contract: Dict[str, Any] = {}

        # Ship MC1a (foundation): multi-coach staff structures. Dormant —
        # legacy save migration on load mirrors _coach into _coaching_staff.
        # Read sites still consume _coach / _coach_contract above until
        # MC1b migrates them. New code can call _get_head_coach() to read
        # through whichever storage is populated.
        self._coaching_staff: List[Dict[str, Any]] = []
        self._head_coach_id: Optional[str] = None
        self._coach_market: List[Dict[str, Any]] = []
        # Equipment system — { camp_id: { equipment_type: tier } }
        self._camp_equipment: Dict[str, Dict[str, str]] = {}
        self._coach_market_week: int = 0

        # Per-fighter weekly training plans — {fighter_id: {focus, intensity}}
        # Set once, applied automatically every week advance
        self._fighter_training_plans: Dict[str, Dict[str, Any]] = {}

        # Fighters who declined a challenge this week — reset each advance_week
        # {fighter_id: week_number}
        self._week_declines: Dict[str, int] = {}

        # Fight commentary cache — generated lazily on first view
        self._fight_commentary: Dict[str, List[str]] = {}

        # Title history — {weight_class: [reign_dict, ...]}
        # Records every championship reign chronologically
        self._title_history: Dict[str, List[Dict[str, Any]]] = {}

        # Ship HOF1: Hall of Fame inductees — career-end records
        # for retired fighters who crossed the prestige threshold.
        self._hof_inductees: List[Dict[str, Any]] = []

        # Injury system — tracks active injuries and history
        self._injury_system = InjurySystem() if INJURY_AVAILABLE and InjurySystem else None

        # Belt vacating tracker — {weight_class: weeks_since_last_defense}
        self._champ_weeks_since_defense: Dict[str, int] = {}

        # Slice 3 — champion injury decision pipeline
        self._pending_injury_decisions: List[Dict[str, Any]] = []
        self._champion_holds:           Dict[str, Dict[str, Any]] = {}

        # Cumulative camp stat gains — {fighter_id: {stat: float}}
        # Accumulates fractional weekly gains so UI shows real progress
        self._camp_stat_totals: Dict[str, Dict[str, float]] = {}

        # Ship A: rolling per-fighter training history — last N weekly
        # entries with focus/intensity/gains/coach_boosts/decays. Capped
        # at TRAINING_HISTORY_WEEKS via FIFO eviction. Surfaced on
        # dashboard via get_training_history().
        self._training_history: Dict[str, List[Dict[str, Any]]] = {}

        # Fighter contracts — {fighter_id: contract_dict}
        self._contracts: Dict[str, Dict[str, Any]] = {}

        # Camp personality archetypes — {camp_id: archetype_name}
        # Populated lazily on first use
        self._camp_archetypes: Dict[str, str] = {}

        # Multi-card scheduling — {week_number: card_dict}
        # Always 8 weeks of cards in the pipeline
        self._upcoming_cards: Dict[int, Dict[str, Any]] = {}

        # Fighter cooldowns — {fighter_id: first_available_week}
        self._fighter_cooldowns: Dict[str, int] = {}

        # Fighter signing delay — {fighter_id: first_week_claimable}
        # Set after cooldown clears. Winners and losers both get a window
        # before they can be booked. Written by _apply_signing_delay.
        self._fighter_signing_available: Dict[str, int] = {}

        # CardBuilder instance (if available)
        self._card_builder = CardBuilder() if CARD_BUILDER_AVAILABLE else None

        # Aging system — one instance tracks per-fighter processed years
        self._aging_system = AgingSystem() if AGING_AVAILABLE else None

        # Belt history — populated by Ship #28's WorldInitializer handoff at
        # new_game time, restored from save in web_load. Holds BeltReign
        # records for sim-history champion lineages (won_from, defenses,
        # lost_to, retire-vacate events). Runtime title-fight writes go to
        # self._title_history, NOT here — two separate stores by design.
        try:
            from world_init import BeltHistory as _BH_cls
            self._belt_history = _BH_cls()
        except ImportError:
            self._belt_history = None

        # Ship C: DFC event numbering offset. World-gen produces N events
        # (DFC 1 - DFC N); the player career should start at DFC N+1, not
        # DFC 1. Captured from game_state.next_event_number after world-gen
        # in new_game; persisted across save/load. Default 0 means no
        # offset (legacy saves + slot3 keep their existing labels).
        self._dfc_event_offset: int = 0

        # Maintenance training system
        self._maintenance_system = (
            MaintenanceTrainingSystem() if MAINTENANCE_AVAILABLE else None
        )

        # Interview state — fight_id -> {winner_done, loser_done, quotes}
        self._fight_interviews: Dict[str, Dict[str, Any]] = {}

        # Watchlist — fighter_id -> WatchEntry-like dict
        self._watchlist: Dict[str, Dict[str, Any]] = {}

        # Media reactions — fight_id -> list of reaction dicts
        self._media_reactions: Dict[str, List[Dict[str, Any]]] = {}
        
    @property
    def week_number(self) -> int:
        if self._game_state:
            return self._game_state.week_number
        return 1
    
    def new_game(self, camp_name: str, camp_location: str, camp_tier: str,
                 coach_data: Dict, fighter_data: Dict) -> bool:
        """
        Start a new game with player's choices.
        
        Returns True if successful, False otherwise.
        """
        if self._mock_mode:
            return self._new_game_mock(camp_name, camp_location, camp_tier, 
                                       coach_data, fighter_data)
        
        try:
            reset_game_state()
            self._game_state = get_game_state()
            
            # Use the real game's new_game flow
            self._game_state.new_game(
                player_camp_name=camp_name,
                player_name="Player"
            )
            
            # IMPORTANT: Populate the world with AI camps and fighters!
            # Ship #28: route through world_init.WorldInitializer instead of
            # the simple game_state.initialize_world stub. The rich path runs
            # HistorySimulator (sim'd fight history, champion lineages, Ship
            # #23 aging hooks, Ship #25 sim-seeded rivalries) so the
            # lived-in-world payoff actually reaches production new_game.
            # Existing slot3 etc. unaffected — they load via web_load, not
            # new_game. Falls back to the simple stub on any failure so
            # new_game stays robust if rich world-gen breaks.
            print("Populating world with AI camps and fighters...")
            try:
                from world_init import initialize_world as _world_init_func
                _initializer = _world_init_func(self._game_state, history_years=2.5)
                # Ship #29: capture BeltHistory off the initializer before it
                # goes out of scope. Holds the sim'd champion lineages (reigns,
                # defenses, won_from / lost_to / vacate events) for later
                # querying via bridge.get_fighter_reigns(). Persisted via
                # web_save/web_load.
                _captured_bh = _initializer.get_belt_history()
                if _captured_bh is not None:
                    self._belt_history = _captured_bh
                # Ship C: capture next-event-number from world-gen so player
                # career events continue from DFC N+1 (where N = sim event
                # count) instead of colliding at DFC 1. Read directly from
                # the initializer object (same source world-gen's "Next
                # Event: DFC X" print uses). The earlier transfer path
                # via game_state.next_event_number was discovered dead in
                # Tier 2: world_init.py:2460 has a hasattr guard that
                # silently fails because GameState doesn't define the
                # attribute. Reading from _initializer.get_next_event_number()
                # bypasses the broken transfer. Subtract 1 to derive the
                # additive offset for week→DFC label.
                try:
                    _next_dfc = _initializer.get_next_event_number()
                    if _next_dfc and _next_dfc > 1:
                        self._dfc_event_offset = _next_dfc - 1
                except Exception:
                    pass
                print(f"Created {len(_initializer.camps)} camps, "
                      f"{len(_initializer.fighters)} fighters with simulated history")
            except Exception as _wie:
                print(f"⚠️  Rich world-gen failed ({_wie}) — falling back to simple init")
                counts = self._game_state.initialize_world(
                    num_ai_camps=40,           # 40 AI camps
                    fighters_per_division=25,   # 25 fighters per weight class = 225 total
                    generate_history=True       # Create some fight history
                )
                print(f"Created {counts.get('camps', 0)} camps, {counts.get('fighters', 0)} fighters")

            # ── Deduplicate fighter names across all camps ─────────────────
            # Generators run per-camp so same name can appear in different camps
            # Suffix uses Roman numerals for clean MMA-style disambiguation
            all_names: dict = {}
            dup_counters: dict = {}  # track how many times each base name has been used
            for fid, ftr in self._game_state.fighters.items():
                name = ftr.name
                if name in all_names:
                    # Use II, III, IV... for duplicates — clean and readable
                    dup_counters[name] = dup_counters.get(name, 1) + 1
                    roman = {2: "II", 3: "III", 4: "IV", 5: "V"}.get(
                        dup_counters[name], str(dup_counters[name])
                    )
                    new_name = f"{name} {roman}"
                    # If somehow that's also taken, keep incrementing
                    while new_name in all_names:
                        dup_counters[name] += 1
                        roman = {2: "II", 3: "III", 4: "IV", 5: "V"}.get(
                            dup_counters[name], str(dup_counters[name])
                        )
                        new_name = f"{name} {roman}"
                    ftr.name = new_name
                    all_names[new_name] = fid
                else:
                    all_names[name] = fid

            # ── Enrich _fighter_data with fighting styles ──────────────
            # The CLI GameState doesn't store style in _fighter_data,
            # so we inject it here using weighted random seeded per fighter.
            _STYLE_POOL    = ["Striker","Counter Striker","Pressure Fighter",
                               "Muay Thai","Wrestler","Ground & Pound",
                               "BJJ Specialist","Sprawl & Brawl",
                               "Point Fighter","Clinch Fighter","Balanced"]
            _STYLE_WEIGHTS = [14, 8, 10, 9, 12, 9, 10, 8, 6, 7, 7]
            import random as _srnd
            for _fid, _frec in self._game_state.fighters.items():
                _fdata = self._game_state._fighter_data.get(_fid, {})
                if "style" not in _fdata:
                    # Seed per fighter for consistency across calls
                    _srnd.seed(hash(_fid) & 0xFFFFFFFF)
                    _style = _srnd.choices(_STYLE_POOL, weights=_STYLE_WEIGHTS, k=1)[0]
                    _fdata["style"] = _style
                    # Also store on the FighterRecord if it has the field
                    if hasattr(_frec, 'fighting_style') and (
                            not _frec.fighting_style or _frec.fighting_style == "Balanced"):
                        _frec.fighting_style = _style
                    self._game_state._fighter_data[_fid] = _fdata
            
            # Create player's starting fighter from selected prospect
            if fighter_data and fighter_data.get('name'):
                print(f"Creating player's fighter: {fighter_data.get('name')}")
                self._create_player_fighter(fighter_data)
            
            # Initialize the 8-week card pipeline
            self.initialize_card_pipeline()
            # F37 fix: populate weeks 4-6 organically so the player
            # doesn't open to 3 empty cards. Without this, those
            # weeks sit at 0 fights until the first advance_week.
            self._top_up_pipeline()

            # Store coach data for passive training and advice
            if coach_data:
                _ct = coach_data.get("traits", [])
                _traits_norm = [t if isinstance(t, str) else getattr(t, 'value', str(t)) for t in _ct]
                _arch = coach_data.get("archetype", "")
                _arch_norm = _arch.value if hasattr(_arch, 'value') else str(_arch)
                self._coach = {
                    "name":      coach_data.get("name",      "Head Coach"),
                    "specialty": coach_data.get("specialty", "boxing").lower(),
                    "rating":    int(coach_data.get("rating", 60)),
                    "salary":    int(coach_data.get("salary", 800)),
                    "traits":    _traits_norm,
                    "archetype": _arch_norm,
                }
                print(f"  ✅ Coach: {self._coach['name']} ({self._coach['specialty']}, {self._coach['rating']} rating)")

                # Ship C2: create coach contract alongside the coach dict
                self._coach_contract = {
                    "coach_id":          coach_data.get("id", "starter_coach"),
                    "name":              self._coach["name"],
                    "specialty":         self._coach["specialty"],
                    "rating":            self._coach["rating"],
                    "salary":            self._coach["salary"],
                    "traits":            _traits_norm,
                    "archetype":         _arch_norm,
                    "total_weeks":       COACH_DEFAULT_CONTRACT_WEEKS,
                    "weeks_completed":   0,
                    "weeks_remaining":   COACH_DEFAULT_CONTRACT_WEEKS,
                    "morale":            COACH_MORALE_START,
                    "signed_week":       self._game_state.week_number if self._game_state else 0,
                    "skipped_paychecks": 0,
                }
                print(f"  📝 Coach contract: {self._coach['name']} — {COACH_DEFAULT_CONTRACT_WEEKS}w @ ${self._coach['salary']}/wk")

                # MC1c: mirror starter coach into staff so multi-coach
                # training loop and UI see them from week 1, not just
                # after a save-reload migration.
                if self._coach_contract and not self._coaching_staff:
                    import uuid as _uuid
                    _cid = self._coach_contract.get("coach_id") or str(_uuid.uuid4())[:12]
                    self._coach["coach_id"] = _cid
                    self._coach_contract["coach_id"] = _cid
                    _entry = dict(self._coach)
                    _entry["contract"] = self._coach_contract
                    self._coaching_staff = [_entry]
                    self._head_coach_id = _cid

            # Store camp location for display
            self._camp_location = camp_location or "Las Vegas, NV"

            self.game_started = True
            self._clear_cache()
            return True
            
        except Exception as e:
            print(f"Error starting new game: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_player_fighter(self, fighter_data: Dict) -> None:
        """Create the player's starting fighter from prospect data."""
        if not self._game_state:
            return
        
        from core.game_state import FighterRecord
        
        # Create fighter record
        fighter_id = fighter_data.get('id', f"player_fighter_{id(fighter_data)}")
        
        fighter = FighterRecord(
            fighter_id=fighter_id,
            name=fighter_data.get('name', 'Unknown Fighter'),
            nickname=fighter_data.get('nickname'),
            weight_class=fighter_data.get('weight_class', 'Lightweight'),
            camp_id=self._game_state.player_camp_id,
            is_champion=False,
            is_active=True,
            overall_rating=fighter_data.get('overall', 65),
            popularity=10,
            wins=0,
            losses=0,
            draws=0,
            ko_wins=0,
            sub_wins=0,
        )
        
        # Add to game state
        self._game_state.fighters[fighter_id] = fighter
        
        # Add to player camp
        if self._game_state.player_camp_id:
            camp = self._game_state.camps.get(self._game_state.player_camp_id)
            if camp:
                camp.fighter_count += 1
        
        # Store rich data so _convert_real_fighter can read style/age/country
        self._game_state._fighter_data[fighter_id] = {
            "id":          fighter_id,
            "name":        fighter_data.get("name", "Unknown"),
            "weight_class":fighter_data.get("weight_class", "Lightweight"),
            "age":         fighter_data.get("age", 21),
            "country":     fighter_data.get("country", "USA"),
            "style":       fighter_data.get("style", "Balanced"),
            "traits":      fighter_data.get("traits", []),
            "potential":   fighter_data.get("potential", fighter_data.get("overall", 65) + 10),
            "nickname":    fighter_data.get("nickname"),
        }

        # Initialize founding-fighter contract. Closes pre-existing bug where
        # the starter never had a contract entry — _process_contracts would
        # silently skip them. Shape mirrors resign_fighter's contract dict
        # plus the is_founding_fighter flag (invisible loyalty bonus).
        self._contracts[fighter_id] = {
            "fighter_id":          fighter_id,
            "camp_id":             self._game_state.player_camp_id,
            "total_fights":        3,
            "fights_remaining":    3,
            "fights_completed":    0,
            "purse_per_fight":     5000 + fighter.overall_rating * 100,
            "morale":              80,
            "holdout_weeks":       0,
            "is_holdout":          False,
            "signed_week":         self._game_state.week_number,
            "is_founding_fighter": True,
        }
        print(f"  📋 Founding contract: {fighter.name} — 3-fight deal")

        print(f"  ✅ Created fighter: {fighter.name} ({fighter.weight_class}) - OVR {fighter.overall_rating}")
    
    def _new_game_mock(self, camp_name: str, camp_location: str, camp_tier: str,
                       coach_data: Dict, fighter_data: Dict) -> bool:
        """Mock new game for when real modules aren't available"""
        # Use the mock data generator from models.py
        from models import MockDataGenerator
        self._mock_generator = MockDataGenerator()
        self._mock_generator.generate_world_with_player(
            camp_name=camp_name,
            camp_location=camp_location,
            camp_tier=camp_tier,
            coach_id=coach_data.get('id', 'coach_0'),
            fighter_id=fighter_data.get('id', 'prospect_0')
        )
        self.game_started = True
        return True
    
    def load_game(self, slot_name: str) -> bool:
        """Load a saved game"""
        if self._mock_mode:
            return False
            
        try:
            self._game_state = load_game(slot_name)
            self.game_started = True
            self._clear_cache()
            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False
    
    def save_game(self, slot_name: str) -> bool:
        """Save current game"""
        if self._mock_mode or not self._game_state:
            return False
            
        try:
            save_game(self._game_state, slot_name)
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def get_saves(self) -> List[Dict]:
        """List available save files"""
        if self._mock_mode:
            return []
        try:
            return list_saves()
        except:
            return []

    # =========================================================================
    # WEB SAVE / LOAD SYSTEM
    # =========================================================================
    # The CLI persistence only saves game_state (fighters/world data).
    # We layer our own JSON save on top for all bridge state.

    def _saves_dir(self) -> str:
        """Directory for web save files."""
        import os
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saves')
        os.makedirs(d, exist_ok=True)
        return d

    def _bridge_save_path(self, slot: str) -> str:
        import os
        return os.path.join(self._saves_dir(), f"bridge_{slot}.json")

    def _dfc_label(self, week: int) -> str:
        """Ship C: format DFC event name with the world-gen offset applied.
        week=1 + offset=130 → "DFC 131". offset=0 (legacy saves) preserves
        the original labels."""
        return f"{PROMOTION_NAME} {week + self._dfc_event_offset}"

    def web_save(self, slot: str = "autosave") -> Dict[str, Any]:
        """
        Save complete game state to a named slot.
        Saves both CLI game_state (fighters/world) and bridge state (pipeline, money, etc.)
        """
        import json, os
        from datetime import datetime

        if not self._game_state:
            return {"success": False, "error": "No game to save"}

        # 1. Save CLI game_state
        try:
            save_game(self._game_state, f"web_{slot}")
        except Exception as e:
            print(f"⚠️ CLI save failed: {e}")

        # 2. Serialize bridge state
        player_fighters = self.get_player_fighters()
        player_camp = self.get_player_camp()
        camp_name = getattr(player_camp, 'name', self._camp_name) if player_camp else self._camp_name
        meta = {
            "slot":         slot,
            "saved_at":     datetime.now().isoformat(),
            "week":         self._game_state.week_number,
            "camp_name":    camp_name,
            "camp_balance": self._camp_balance,
            "fighter_name": player_fighters[0].name if player_fighters else "Unknown",
            "record":       player_fighters[0].record_str if player_fighters else "0-0",
        }

        # Serialize _upcoming_cards — strip non-serializable engine results
        def clean_fight(f):
            d = {k: v for k, v in f.items() if k != '_engine_result'}
            return d

        upcoming_clean = {}
        for wk, card in self._upcoming_cards.items():
            upcoming_clean[str(wk)] = {
                **{k: v for k, v in card.items() if k != 'fights'},
                'fights': [clean_fight(f) for f in card.get('fights', [])],
            }

        bridge_data = {
            "meta":                     meta,
            "camp_name":                camp_name,
            "camp_location":            self._camp_location,
            "player_camp_wins":         self._player_camp_wins,
            "player_camp_losses":       self._player_camp_losses,
            "camp_balance":             self._camp_balance,
            "total_purses_earned":      self._total_purses_earned,
            "coach":                    self._coach,
            "coach_contract":           self._coach_contract,
            # Ship MC1a foundation — additive multi-coach state
            "coaching_staff":           self._coaching_staff,
            "head_coach_id":            self._head_coach_id,
            "coach_market":             self._coach_market,
            "camp_equipment":           self._camp_equipment,
            "coach_market_week":        self._coach_market_week,
            "scheduled_fights":         [clean_fight(f) for f in self._scheduled_fights],
            "ai_deferred_bookings":     [clean_fight(f) for f in self._ai_deferred_bookings],
            "upcoming_cards":           upcoming_clean,
            "fighter_cooldowns":        self._fighter_cooldowns,
            "fighter_signing_available":    self._fighter_signing_available,
            "fighter_training_plans":   self._fighter_training_plans,
            "fight_camps":              self._fight_camps,
            "week_declines":            self._week_declines,
            "neg_counter":              self._neg_counter,
            "fight_interviews":         self._fight_interviews,
            "watchlist":                self._watchlist,
            "fight_commentary":         {k: v for k, v in self._fight_commentary.items()},
            "title_history":            self._title_history,
            "yearly_awards":            self._yearly_awards if hasattr(self, '_yearly_awards') else [],
            "hof_inductees":            self._hof_inductees,
            "camp_stat_totals":         self._camp_stat_totals,
            "training_history":         self._training_history,
            "contracts":                self._contracts,
            "camp_archetypes":          self._camp_archetypes,
            "injury_system":            self._injury_system.to_dict() if self._injury_system else {},
            "rivalry_system":           get_rivalry_system().to_dict() if RIVALRY_AVAILABLE else {},
            "belt_history":             self._belt_history.to_dict() if self._belt_history else {},
            "dfc_event_offset":         self._dfc_event_offset,
            "champ_weeks_since_defense": self._champ_weeks_since_defense,
            "pending_injury_decisions": self._pending_injury_decisions,
            "pending_challenges":       self._pending_challenges,
            "amateur_graduates":        self._amateur_graduates,
            "champion_holds":           self._champion_holds,
            "fight_offers":             self._fight_offers,
            "completed_events":         [
                {**{k: v for k, v in ev.items() if k != 'fights'},
                 'fights': [clean_fight(f) for f in ev.get('fights', [])]}
                for ev in self._completed_events[-50:]  # Last 50 events
            ],
            "news_items":               self._news_items[-100:],
            # Ship WS1: serialize game_state so fighters persist across saves
            "fighters":             {fid: f.to_dict() for fid, f in self._game_state.fighters.items()},
            "fighter_data":         dict(self._game_state._fighter_data),
            "camps":                {cid: c.to_dict() for cid, c in self._game_state.camps.items()},
            "divisions":            {wc: d.to_dict() for wc, d in self._game_state.divisions.items()},
            "player_camp_id":       self._game_state.player_camp_id,
            "game_week_number":     self._game_state.week_number,
            "media_reactions":          self._media_reactions,
            "aging_processed":          self._aging_system._last_processed_year
                                        if self._aging_system else {},
        }

        try:
            path = self._bridge_save_path(slot)
            with open(path, 'w') as f:
                json.dump(bridge_data, f, indent=2, default=str)
            print(f"✅ Game saved to slot '{slot}' (Week {meta['week']})")
            return {"success": True, "meta": meta}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def web_load(self, slot: str) -> Dict[str, Any]:
        """
        Load a saved game from a named slot.
        Restores both CLI game_state and bridge state.
        """
        import json, os

        bridge_path = self._bridge_save_path(slot)
        if not os.path.exists(bridge_path):
            return {"success": False, "error": f"Save slot '{slot}' not found"}

        # 1. Load CLI game_state
        try:
            result = load_game(f"web_{slot}")
            if hasattr(result, 'game_state') and result.game_state:
                self._game_state = result.game_state
            else:
                print(f"  ⚠️ CLI load returned no game_state for slot {slot} — will restore from bridge JSON")
        except Exception as _le:
            print(f"  ⚠️ CLI load failed for slot {slot}: {_le} — will restore from bridge JSON")

        # If CLI load didn't produce a game_state, create a minimal one
        # so the WS1 bridge-JSON restore block can still run.
        # All canonical data (fighters, camps, divisions, week) lives in
        # the bridge JSON — the CLI world save is secondary.
        if not self._game_state:
            try:
                from core.game_state import GameState
                self._game_state = GameState()
                print(f"  ℹ️ Created fresh GameState for bridge-JSON restore")
            except Exception as _gse:
                print(f"  ⚠️ Could not create GameState: {_gse}")

        # 2. Restore bridge state
        try:
            with open(bridge_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            return {"success": False, "error": f"Could not read save file: {e}"}

        self._camp_name               = data.get("camp_name", "My Camp")
        self._camp_location           = data.get("camp_location", "Las Vegas, NV")
        self._player_camp_wins        = data.get("player_camp_wins", 0)
        self._player_camp_losses      = data.get("player_camp_losses", 0)
        self._camp_balance            = data.get("camp_balance", 50000)
        self._total_purses_earned     = data.get("total_purses_earned", 0)
        self._coach                   = data.get("coach", {})
        self._coach_contract          = data.get("coach_contract", {})

        # Ship MC1a foundation — additive multi-coach state restore.
        # Reads still hit _coach/_coach_contract above; staff is populated
        # for future MC1b code to consume.
        self._coaching_staff          = data.get("coaching_staff", [])
        self._head_coach_id           = data.get("head_coach_id", None)
        self._coach_market            = data.get("coach_market", [])
        self._camp_equipment          = data.get("camp_equipment", {})
        self._coach_market_week       = data.get("coach_market_week", 0)
        # Legacy save migration: if old save has a populated coach contract
        # but no coaching_staff entry, mirror it into the staff list so
        # future _coaching_staff reads see the data. Idempotent — skipped
        # once staff is populated.
        if not self._coaching_staff and self._coach_contract:
            import uuid as _uuid_mig
            _cid = self._coach_contract.get("coach_id") or str(_uuid_mig.uuid4())[:8]
            _legacy_entry = dict(self._coach or {})
            _legacy_entry["coach_id"] = _cid
            _legacy_entry["contract"] = dict(self._coach_contract or {})
            self._coaching_staff = [_legacy_entry]
            self._head_coach_id = _cid
        self._scheduled_fights        = data.get("scheduled_fights", [])
        self._ai_deferred_bookings    = data.get("ai_deferred_bookings", [])

        # Sub-ship A: auto-truncate over-capacity cards on load. Cleanup for
        # any save state that accumulated bloat before Phase 2's capacity
        # gate landed. Sort by (player_first, slot_priority, -score) and
        # keep top N. Player fights are protected from truncation — the
        # player accepted them, they shouldn't disappear silently regardless
        # of slot/score. _completed_events deliberately untouched — history
        # preserved.
        _SLOT_PRIORITY = {"main_event": 0, "co_main": 1, "main_card": 2,
                          "prelim": 3, "early_prelim": 4}
        _truncated_total = 0
        for _wk, _card in self._upcoming_cards.items():
            _fights = _card.get("fights", [])
            if len(_fights) > CARD_TARGET_FIGHTS:
                _sorted = sorted(_fights, key=lambda f: (
                    0 if f.get("is_player_fight") else 1,  # player fights first (protected)
                    _SLOT_PRIORITY.get(f.get("card_slot", "prelim"), 99),
                    -float(f.get("matchup_score", 0) or 0),
                ))
                _kept = _sorted[:CARD_TARGET_FIGHTS]
                _dropped = len(_fights) - len(_kept)
                _card["fights"] = _kept
                _truncated_total += _dropped
                print(f"  🔧 [CARD TRUNCATE] {PROMOTION_NAME} {_wk} had {len(_fights)} fights, "
                      f"kept top {CARD_TARGET_FIGHTS} (player fights protected), dropped {_dropped}")
        if _truncated_total > 0:
            print(f"🔧 [SUB-SHIP A LOAD CLEANUP] Truncated {_truncated_total} fights total "
                  f"from over-capacity cards (player fights protected).")
        self._fighter_training_plans  = data.get("fighter_training_plans", {})
        self._fight_camps             = data.get("fight_camps", {})
        self._week_declines           = {k: int(v) for k, v in
                                          data.get("week_declines", {}).items()}
        self._neg_counter             = data.get("neg_counter", 0)
        self._news_items              = data.get("news_items", [])
        self._media_reactions         = data.get("media_reactions", {})
        self._fight_interviews        = data.get("fight_interviews", {})
        self._watchlist               = data.get("watchlist", {})
        self._fight_commentary        = data.get("fight_commentary", {})
        self._title_history           = data.get("title_history", {})
        self._camp_stat_totals        = data.get("camp_stat_totals", {})
        self._training_history        = data.get("training_history", {})
        self._contracts               = data.get("contracts", {})
        self._yearly_awards           = data.get("yearly_awards", [])
        self._hof_inductees           = data.get("hof_inductees", [])

        # WS1 restore diagnostic
        _fighters_in_bridge = len(data.get("fighters", {}))
        _fdata_in_bridge = len(data.get("fighter_data", {}))
        print(f"  📦 WS1 restore: game_state={'present' if self._game_state else 'NONE'}, "
              f"fighters_in_bridge={_fighters_in_bridge}, fdata_in_bridge={_fdata_in_bridge}")

        # Ship WS1: restore game_state fighters/camps/divisions from save
        if self._game_state:
            from core.game_state import FighterRecord, CampRecord, DivisionState
            _fighters_data = data.get("fighters", {})
            if _fighters_data:
                self._game_state.fighters = {
                    fid: FighterRecord.from_dict(fd)
                    for fid, fd in _fighters_data.items()
                }
            _fd = data.get("fighter_data", {})
            if _fd:
                self._game_state._fighter_data = _fd
            _camps_data = data.get("camps", {})
            if _camps_data:
                self._game_state.camps = {
                    cid: CampRecord.from_dict(cd)
                    for cid, cd in _camps_data.items()
                }
            _divs_data = data.get("divisions", {})
            if _divs_data:
                self._game_state.divisions = {
                    wc: DivisionState.from_dict(dd)
                    for wc, dd in _divs_data.items()
                }
            _pci = data.get("player_camp_id")
            if _pci:
                self._game_state.player_camp_id = _pci
            _gwn = data.get("game_week_number")
            if _gwn is not None:
                self._game_state.week_number = _gwn
        self._camp_archetypes         = data.get("camp_archetypes", {})
        self._champ_weeks_since_defense = data.get("champ_weeks_since_defense", {})
        self._pending_injury_decisions  = data.get("pending_injury_decisions", [])
        self._champion_holds            = data.get("champion_holds", {})
        if INJURY_AVAILABLE and InjurySystem and "injury_system" in data:
            try:
                self._injury_system = InjurySystem.from_dict(data["injury_system"])
            except Exception as _ie:
                print(f"⚠️ Could not restore injury state: {_ie}")
                self._injury_system = InjurySystem() if InjurySystem else None
        if RIVALRY_AVAILABLE and "rivalry_system" in data:
            try:
                # Mutate the module-level singleton in-place so all callers
                # of get_rivalry_system() see the restored state. Same
                # mutation pattern as reset_rivalry_system() at rivalry.py:972.
                from rivalry import RivalrySystem as _RivSys
                import rivalry as _rivalry_module
                _rivalry_module._rivalry_system = _RivSys.from_dict(data["rivalry_system"])
                if self._game_state and hasattr(self._game_state, 'register_rivalry_system'):
                    self._game_state.register_rivalry_system(_rivalry_module._rivalry_system)
            except Exception as _re:
                print(f"⚠️ Could not restore rivalry state: {_re}")
        if "belt_history" in data:
            try:
                # Ship #29: restore sim'd champion lineages so reigns survive
                # Flask restarts. Backward compat: legacy saves without the
                # key fall through to the empty BeltHistory set in __init__.
                from world_init import BeltHistory as _BH_load
                self._belt_history = _BH_load.from_dict(data["belt_history"])
            except Exception as _bhe:
                print(f"⚠️ Could not restore belt history: {_bhe}")
        # Ship C: restore DFC event-numbering offset. Backward compat:
        # legacy saves without the key default to 0 (no offset, original
        # labels preserved).
        self._dfc_event_offset = int(data.get("dfc_event_offset", 0) or 0)
        self._fight_offers            = data.get("fight_offers", [])
        self._fighter_cooldowns       = {k: int(v) for k, v in
                                          data.get("fighter_cooldowns", {}).items()}
        self._fighter_signing_available = {k: int(v) for k, v in
                                            data.get("fighter_signing_available", {}).items()}

        # Restore completed events
        self._completed_events = data.get("completed_events", [])

        # ── Nickname backfill — one-shot for legacy saves ──────────────
        # Fighters who already meet the earned-nickname threshold (≥2 wins
        # AND ≥3 total fights) but lack a nickname get one assigned on load.
        # Raw prospects (<3 fights or <2 wins) stay nameless until they
        # earn it through performance. Idempotent.
        try:
            from game_state import NICKNAMES_POOL as _NK_POOL
            import random as _nk_rand
            if self._game_state and hasattr(self._game_state, 'fighters'):
                _backfilled = 0
                for _f in self._game_state.fighters.values():
                    if not getattr(_f, 'nickname', None):
                        _wins  = getattr(_f, 'wins', 0) or 0
                        _total = _wins + (getattr(_f, 'losses', 0) or 0) + (getattr(_f, 'draws', 0) or 0)
                        if _wins >= 2 and _total >= 3:
                            _f.nickname = _nk_rand.choice(_NK_POOL)
                            _backfilled += 1
                if _backfilled:
                    print(f"  ✨ [NICKNAME BACKFILL] {_backfilled} fighters earned nicknames retroactively")
        except Exception as _nk_exc:
            print(f"⚠️ Nickname backfill skipped: {_nk_exc}")

        # Restore upcoming cards — convert str keys back to int
        raw_cards = data.get("upcoming_cards", {})
        self._upcoming_cards = {int(k): v for k, v in raw_cards.items()}

        # Lock any card already at capacity so Phase 3 skips rebuilding it.
        # Legacy saves predate the locked flag — derive truth from count.
        for _wk_lock, _card_lock in self._upcoming_cards.items():
            if len(_card_lock.get("fights", [])) >= CARD_TARGET_FIGHTS:
                _card_lock["locked"] = True

        # Restore aging state
        if self._aging_system and "aging_processed" in data:
            self._aging_system._last_processed_year = {
                k: int(v) for k, v in data["aging_processed"].items()
            }

        # Restore pending negotiations (empty on load — in-progress negs don't persist)
        self._pending_negotiations = {}
        # Ship K5: pending challenges DO persist (multi-week resolution)
        self._pending_challenges = data.get("pending_challenges", {})
        # Ship A1: amateur graduates persist for the graduates tab
        self._amateur_graduates = data.get("amateur_graduates", [])

        self.game_started = True
        self._clear_cache()

        # F33-C: Do NOT recompute rankings on load. Saved rankings are canonical —
        # they were produced by the same algorithm at the time of the last fight
        # night or week advancement, and are stable as long as fighter state
        # hasn't drifted. Recomputing here mutates the saved state and (per
        # Ship F33-B 2026-05-31 trace) introduces process-level non-determinism
        # because the recompute itself depends on dict/set iteration order.
        # The fix for the recompute non-determinism is filed as F33-D.

        meta = data.get("meta", {})
        print(f"✅ Game loaded from slot '{slot}' (Week {meta.get('week', '?')})")

        return {"success": True, "meta": meta}

    def get_web_saves(self) -> List[Dict[str, Any]]:
        """List all available web save slots with metadata."""
        import json, os
        slots = ["slot1", "slot2", "slot3", "autosave"]
        saves = []
        for slot in slots:
            path = self._bridge_save_path(slot)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    meta = data.get("meta", {})
                    saves.append({
                        "slot":         slot,
                        "label":        slot.replace("slot", "Slot ").replace("autosave", "Auto"),
                        "exists":       True,
                        "week":         meta.get("week", "?"),
                        "camp_name":    meta.get("camp_name", ""),
                        "fighter_name": meta.get("fighter_name", ""),
                        "record":       meta.get("record", ""),
                        "saved_at":     meta.get("saved_at", ""),
                    })
                except Exception:
                    saves.append({"slot": slot, "label": slot, "exists": False})
            else:
                saves.append({
                    "slot":   slot,
                    "label":  slot.replace("slot", "Slot ").replace("autosave", "Auto"),
                    "exists": False,
                })
        return saves

    def autosave_if_due(self, week: int) -> None:
        """Autosave every 5 weeks automatically."""
        if week % 5 == 0 and week > 0:
            self.web_save("autosave")
    
    def advance_week(self) -> Dict[str, Any]:
        """Advance the game by one week"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                result = self._mock_generator.advance_week()
                self._clear_cache()
                return {"success": True, **result}
            return {"success": False}
        
        if not self._game_state:
            return {"success": False}

        # Slice 3 — block advance if any champion injury decisions are pending
        if self._pending_injury_decisions:
            return {
                "success": False,
                "error": (f"Decision required: {len(self._pending_injury_decisions)} "
                          f"champion injury choice(s) pending. Visit /champion-injury "
                          f"to decide."),
                "blocking_decisions": self._pending_injury_decisions,
            }

        try:
            import random

            # Decrement remaining fights' weeks_until + advance the game
            # week BEFORE simulating this week's fights. This way, player
            # fights fire during the advance INTO their target week (matching
            # the AI card sim convention) and tag with the same week as
            # their DFC card. Fixes Bug E + Bug G timing root cause.

            # Decrement weeks_until for remaining fights
            for fight in self._scheduled_fights:
                fight["weeks_until"] = max(0, fight.get("weeks_until", 1) - 1)

            # Advance the game week
            report = self._game_state.advance_week()

            # Check for fights this week
            fights_this_week = [f for f in self._scheduled_fights if f.get("weeks_until", 0) <= 0]
            fight_results = []
            week_events: Dict[str, Dict] = {}
            self._week_purses_earned = 0  # reset weekly purse tracker

            # ── Snapshot ranks BEFORE fights ──────────────────────────
            pre_ranks: Dict[str, Optional[int]] = {}
            for fight in fights_this_week:
                for fid in [fight.get("fighter1_id"), fight.get("fighter2_id")]:
                    if fid and fid not in pre_ranks:
                        rec = self._game_state.get_fighter(fid) if self._game_state else None
                        pre_ranks[fid] = self._get_fighter_rank(rec) if rec else None

            for fight in fights_this_week:
                # Skip if either fighter isn't cleared to fight (injury)
                if INJURY_AVAILABLE and self._injury_system:
                    f1id = fight.get("fighter1_id", "")
                    f2id = fight.get("fighter2_id", "")
                    _f1_clr = self._injury_system.is_cleared_to_fight(f1id)
                    _f2_clr = self._injury_system.is_cleared_to_fight(f2id)
                    if not _f1_clr or not _f2_clr:
                        _uncleared_names = []
                        if not _f1_clr: _uncleared_names.append(fight.get("fighter1_name", ""))
                        if not _f2_clr: _uncleared_names.append(fight.get("fighter2_name", ""))
                        self._news_items.insert(0, {
                            "headline": (f"🚫 {fight.get('fighter1_name','')} vs "
                                         f"{fight.get('fighter2_name','')} at "
                                         f"{fight.get('event_name','event')} cancelled — "
                                         f"{' and '.join(_uncleared_names)} not cleared to fight."),
                            "category": "fight_cancelled",
                            "week": self._game_state.week_number if self._game_state else 1,
                        })
                        continue
                result = self._simulate_fight(fight)
                fight_results.append(result)

                # Group by event name
                ev_name = fight.get("event_name", self._dfc_label(self._game_state.week_number))
                ev_id   = f"event_{self._game_state.week_number}_{ev_name.replace(' ', '_')}"
                if ev_name not in week_events:
                    week_events[ev_name] = {
                        "event_id":   ev_id,
                        "event_name": ev_name,
                        "week":       self._game_state.week_number,
                        "fights":     [],
                        "main_event": None,
                        "fotn":       None,
                    }
                week_events[ev_name]["fights"].append(result)
                # First fight added = main event (can be overridden by is_player_fight)
                if week_events[ev_name]["main_event"] is None or fight.get("is_player_fight"):
                    week_events[ev_name]["main_event"] = result

            # FOTN handled below via all_card_fights (player + AI combined)

            # NOTE: player events stored AFTER AI merge below — don't store here yet
            # week_events will be merged into AI card or stored individually

            # ── Economy: deduct weekly overhead ─────────────────
            overhead_paid = self._deduct_weekly_overhead()

            # ── Economy: pay purses + generate media for each fight ──
            for result in fight_results:
                purse = self._pay_fight_purse(result)
                fid   = result.get("fight_id", "")
                if fid:
                    reactions = self._generate_media_reactions(result)
                    if reactions:
                        self._media_reactions[fid] = reactions

            # Remove completed fights
            self._scheduled_fights = [f for f in self._scheduled_fights if f.get("weeks_until", 0) > 0]
            
            # ── Reset weekly decline tracking ─────────────────────────
            current_week = self._game_state.week_number
            self._week_declines = {
                fid: wk for fid, wk in self._week_declines.items()
                if wk >= current_week
            }

            # ── Advance amateur circuit ───────────────────────────────
            amateur_events = self._advance_amateur_week(current_week)

            # ── Aging — annual stat decay and retirements ─────────────
            self._advance_aging_week(current_week)

            # ── Slice 4: champion-hold cardio decay + milestone news ──
            # Tapered decay: weeks 1-4 = -0.25/wk, 5-12 = -0.5/wk, 13+ = -0.75/wk
            # Float accumulator avoids rounding-loss; cardio decremented when ≥1.0
            for _fid, _entry in self._champion_holds.items():
                _ftr = self._game_state.get_fighter(_fid)
                if not _ftr:
                    continue
                _weeks_in_hold = current_week - _entry.get("start_week", current_week)
                if _weeks_in_hold <= 4:
                    _rate = 0.25
                elif _weeks_in_hold <= 12:
                    _rate = 0.5
                else:
                    _rate = 0.75
                _accum = _entry.get("cardio_decay_accum", 0.0) + _rate
                while _accum >= 1.0 and _ftr.cardio > 1:
                    _ftr.cardio -= 1
                    _accum -= 1.0
                _entry["cardio_decay_accum"] = _accum

                # Milestone hype news — 4w/2w/1w until return
                _weeks_until = _entry.get("return_week", current_week) - current_week
                _wc_h = _entry.get("weight_class", "")
                if _weeks_until == 4:
                    _hl_h = f"🏆 {_ftr.name} 4 weeks from return — {_wc_h} title defense pending"
                elif _weeks_until == 2:
                    _hl_h = f"🏆 {_ftr.name} 2 weeks from return"
                elif _weeks_until == 1:
                    _hl_h = f"🏆 {_ftr.name} cleared next week — {_wc_h} title defense imminent"
                else:
                    _hl_h = None
                if _hl_h:
                    self._news_items.insert(0, {
                        "headline": _hl_h,
                        "category": "title",
                        "week":     current_week,
                    })

            # ── Maintenance training — coach boosts + idle decay ──────
            self._advance_maintenance_week(current_week)

            # ── Apply weekly training plans for all player fighters ──────
            training_report = self._apply_weekly_training()

            # ── Simulate this week's pre-built card ──────────────────
            current_week = self._game_state.week_number
            ai_event = None
            card = self._upcoming_cards.pop(current_week, None)
            if card and card["fights"]:
                # Only simulate AI fights (player fights already handled above)
                ai_fights_this_week = [
                    f for f in card["fights"]
                    if f.get("is_ai_fight") and not f.get("is_player_fight")
                ]
                if ai_fights_this_week:
                    ai_event = self._simulate_card_fights(card, ai_fights_this_week)
                    if ai_event:
                        # ── Merge player fights into this card if same event ──
                        player_ev_name = ai_event.get("event_name", "").strip()
                        merged_keys = []
                        for ev_key, ev in list(week_events.items()):
                            ev_name = ev.get("event_name", "").strip()
                            # Match by name OR by week (player fight on same card)
                            if ev_name == player_ev_name or ev.get("week") == ai_event.get("week"):
                                # Move player fights into the AI event
                                ai_event["fights"] = ev["fights"] + ai_event["fights"]
                                # Keep better main_event
                                if ev.get("main_event"):
                                    pf_slot = ev["main_event"].get("card_slot","")
                                    ae_slot = (ai_event.get("main_event") or {}).get("card_slot","")
                                    slot_rank = {"main_event":0,"co_main":1,"main_card":2,"prelim":3,"early_prelim":4}
                                    if slot_rank.get(pf_slot,9) <= slot_rank.get(ae_slot,9):
                                        ai_event["main_event"] = ev["main_event"]
                                merged_keys.append(ev_key)
                        # Remove merged events so they don't get double-stored
                        for k in merged_keys:
                            week_events.pop(k, None)
                        self._completed_events.append(ai_event)
                # Store any player events that genuinely didn't merge
                # (edge case: player fight on a completely different card)
                for ev in week_events.values():
                    if ev.get("fights"):  # Only store if it has actual fights
                        self._completed_events.append(ev)
            else:
                # Fallback — no pre-built card (shouldn't happen normally)
                ai_event = self._simulate_ai_fights_week()
                if ai_event and ai_event["fights"]:
                    self._completed_events.append(ai_event)
                # Store player events (no AI card to merge into)
                for ev in week_events.values():
                    self._completed_events.append(ev)

            # ── Apply cooldowns to fighters who just fought ────────────
            for result in fight_results:
                for fid, won in [(result.get("winner_id"), True),
                                  (result.get("loser_id"),  False)]:
                    if not fid:
                        continue
                    ftr = self._game_state.get_fighter(fid)
                    if ftr:
                        is_champ = getattr(ftr, 'is_champion', False)
                        self._apply_cooldown(ftr, current_week, is_champ)
                        self._apply_signing_delay(ftr, current_week, is_champ)
                # Ship DR2b: draws have winner_id=None + loser_id=None so
                # the fid loop above skips both fighters. Apply cooldown
                # to both directly via fighter1_id/fighter2_id.
                if result.get("method") == "Draw":
                    for _dfid in [result.get("fighter1_id"),
                                  result.get("fighter2_id")]:
                        if not _dfid:
                            continue
                        _dftr = self._game_state.get_fighter(_dfid)
                        if _dftr:
                            self._apply_cooldown(
                                _dftr, current_week,
                                getattr(_dftr, 'is_champion', False))
                            self._apply_signing_delay(
                                _dftr, current_week,
                                getattr(_dftr, 'is_champion', False))
            if ai_event:
                for fight in ai_event.get("fights", []):
                    for fid in [fight.get("winner_id"), fight.get("loser_id")]:
                        if not fid:
                            continue
                        ftr = self._game_state.get_fighter(fid)
                        if ftr:
                            self._apply_cooldown(ftr, current_week,
                                                  getattr(ftr, 'is_champion', False))
                            self._apply_signing_delay(ftr, current_week,
                                                       getattr(ftr, 'is_champion', False))
                    # Ship DR2b: same draw fallback as player loop above.
                    if fight.get("method") == "Draw":
                        for _dfid in [fight.get("fighter1_id"),
                                      fight.get("fighter2_id")]:
                            if not _dfid:
                                continue
                            _dftr = self._game_state.get_fighter(_dfid)
                            if _dftr:
                                self._apply_cooldown(
                                    _dftr, current_week,
                                    getattr(_dftr, 'is_champion', False))
                                self._apply_signing_delay(
                                    _dftr, current_week,
                                    getattr(_dftr, 'is_champion', False))

            # ── Contract processing — decrement and handle expiry ─────
            self._process_contracts(current_week)

            # Ship C2: weekly coach contract tick — morale + expiration
            self._process_coach_contract(current_week)

            # Ship K2: proactive weight class alerts
            self._check_weight_class_alerts()

            # Ship K3: AI fighters consider weight class moves
            self._check_ai_weight_class_moves()

            # Ship K5: resolve pending player challenges (1-2 week delay)
            self._process_pending_challenges(current_week)

            # Ship L1: AI camp roster management — cuts, demands, FA sweep
            self._process_ai_camp_roster(current_week)
            self._process_ai_free_agent_bidding(current_week)

            # Ship S1: weekly sponsor processing — retainers, drops, offers
            self._process_weekly_sponsors(current_week)

            # ── Top up pipeline — add week N+8 ────────────────────────
            self._top_up_pipeline()

            # ── Injury healing — process one week for all fighters ────
            if INJURY_AVAILABLE and self._injury_system:
                healed = self._injury_system.process_weekly_healing()

                # ── Slice 4: champion hold heal-sweep ─────────────────
                # Must run BEFORE generic recovery news loop so _slice4_handled
                # can gate the generic line for champions whose replacement
                # headline already fired. Three branches:
                #   (a) already-booked → pop, generic recovery still fires
                #   (b) booking succeeds → pop + suppress generic (helper fired headline)
                #   (c) booking fails → keep entry alive, retry next week, generic fires
                _slice4_handled = set()
                for _fid_s4 in list(self._champion_holds.keys()):
                    _entry_s4 = self._champion_holds[_fid_s4]
                    if _entry_s4.get("return_week", 0) > current_week:
                        continue
                    _wc_s4 = _entry_s4.get("weight_class", "")
                    _ftr_s4 = self._game_state.get_fighter(_fid_s4)
                    if not _ftr_s4:
                        del self._champion_holds[_fid_s4]  # defensive; fighter gone
                        continue
                    # Branch (a): champion already booked → existing fight is the return
                    _booked_s4 = set()
                    for _sf_s4 in self._scheduled_fights:
                        _booked_s4.add(_sf_s4.get("fighter1_id", ""))
                        _booked_s4.add(_sf_s4.get("fighter2_id", ""))
                    for _wk_b_s4, _card_b_s4 in self._upcoming_cards.items():
                        for _f_b_s4 in _card_b_s4.get("fights", []):
                            _booked_s4.add(_f_b_s4.get("fighter1_id", ""))
                            _booked_s4.add(_f_b_s4.get("fighter2_id", ""))
                    if _fid_s4 in _booked_s4:
                        print(f"  🏆 [SLICE 4] {_ftr_s4.name} healed; existing fight is the return")
                        del self._champion_holds[_fid_s4]
                        continue
                    # Branch (b)/(c): attempt booking via shared helper (sub-ship B)
                    _booking_s4 = self._book_title_fight(_wc_s4, fixed_fighter=_ftr_s4)
                    if _booking_s4:
                        _slice4_handled.add(_fid_s4)
                        del self._champion_holds[_fid_s4]
                    # else: keep entry alive, retry next advance_week (indefinite)

                for fid_h, descriptions in healed.items():
                    if fid_h in _slice4_handled:
                        continue  # Slice 4 fired replacement headline; suppress generic
                    ftr_h = self._game_state.get_fighter(fid_h) if self._game_state else None
                    fname_h = getattr(ftr_h, 'name', fid_h) if ftr_h else fid_h
                    for desc in descriptions:
                        print(f"  ✅ [RECOVERY] {fname_h} cleared: {desc}")
                        self._news_items.append({
                            "headline": f"✅ {fname_h} has been medically cleared — ready to compete",
                            "category": "injury",
                            "week": current_week,
                        })

                # Weekly injury report summary
                all_injured = self._injury_system.get_all_injured_fighters()
                if all_injured:
                    from systems.injury import InjuryType
                    _severe  = 0
                    _mod     = 0
                    _minor   = 0
                    for _ifid in all_injured:
                        _worst = self._injury_system.get_worst_injury(_ifid)
                        if _worst:
                            if _worst.injury_type in (InjuryType.SEVERE, InjuryType.CAREER):
                                _severe += 1
                            elif _worst.injury_type == InjuryType.MODERATE:
                                _mod += 1
                            else:
                                _minor += 1
                    print(f"  🤕 [INJURY REPORT] Week {current_week}: "
                          f"{len(all_injured)} fighters injured "
                          f"({_severe} severe, {_mod} moderate, {_minor} minor)")

            # ── Belt vacating — champion injured too long ─────────────
            if INJURY_AVAILABLE and self._injury_system and self._game_state:
                for wc in self._game_state.WEIGHT_CLASSES:
                    div = self._game_state.divisions.get(wc)
                    if not div or not div.champion_id:
                        continue
                    champ_inj = self._injury_system.get_injuries(div.champion_id)
                    if not champ_inj:
                        # Reset counter if champion is healthy
                        self._champ_weeks_since_defense[wc] = 0
                        continue
                    # Champion is injured — increment counter
                    self._champ_weeks_since_defense[wc] =                         self._champ_weeks_since_defense.get(wc, 0) + 1
                    weeks_injured = self._champ_weeks_since_defense[wc]
                    # Strip belt after 25 weeks of injury (Career-level threshold per design spec)
                    if weeks_injured >= 25:
                        champ = self._game_state.get_fighter(div.champion_id)
                        champ_name = getattr(champ, 'name', 'The Champion') if champ else 'The Champion'
                        print(f"  👑 [VACATED] {champ_name} stripped of {wc} title — "
                              f"{weeks_injured} weeks injured")
                        self._news_items.insert(0, {
                            "headline": f"👑 TITLE VACATED: {champ_name} relinquishes the {wc} "
                                        f"belt during recovery.",
                            "category": "title",
                            "week": current_week,
                        })
                        # Strip belt
                        if champ:
                            champ.is_champion = False
                        div.champion_id   = None
                        div.champion_name = None
                        self._champ_weeks_since_defense[wc] = 0
                        # Close the reign in title history
                        history = self._title_history.get(wc, [])
                        if history and history[-1].get("is_active"):
                            history[-1]["is_active"]   = False
                            history[-1]["lost_week"]    = current_week
                            history[-1]["lost_event"]   = "Vacated (injury)"
                            history[-1]["lost_to_name"] = "Vacated"
                            history[-1]["lost_method"]  = "Injury"

                        # ── Slice 2: book vacant-title fight ──────────
                        # Top-2 non-player contenders fight for the
                        # vacant belt at the next card with an open
                        # main_event slot. Player excluded — Slice 2 is
                        # AI-only; player vacant-title path is Slice 2.5.
                        _all_booked = set()
                        for _sf in self._scheduled_fights:
                            _all_booked.add(_sf.get("fighter1_id", ""))
                            _all_booked.add(_sf.get("fighter2_id", ""))
                        for _wk_b, _card_b in self._upcoming_cards.items():
                            for _f_b in _card_b.get("fights", []):
                                _all_booked.add(_f_b.get("fighter1_id", ""))
                                _all_booked.add(_f_b.get("fighter2_id", ""))

                        _player_camp_id = self._game_state.player_camp_id

                        # ── Slice 2.5: player-owned #1 contender? offer flow ──
                        # If player owns rank-#1 (and not also rank-#2), fire a
                        # vacant-title offer instead of auto-booking. Decline
                        # path: decline_fight_offer triggers AI #2 vs #3 fallback.
                        # Multi-fighter at #1 AND #2: skip, fall through to AI.
                        _slice_2_5_handled = False
                        if _player_camp_id and len(div.rankings) >= 2:
                            _r1_ftr = self._game_state.get_fighter(div.rankings[0])
                            _r2_ftr = self._game_state.get_fighter(div.rankings[1])
                            _player_at_1 = bool(_r1_ftr and _r1_ftr.is_active
                                                 and _r1_ftr.camp_id == _player_camp_id)
                            _player_at_2 = bool(_r2_ftr and _r2_ftr.is_active
                                                 and _r2_ftr.camp_id == _player_camp_id)
                            if _player_at_1 and not _player_at_2:
                                _ai_opp = None
                                for _aid in div.rankings[1:8]:
                                    _aftr = self._game_state.get_fighter(_aid)
                                    if not _aftr or not _aftr.is_active:
                                        continue
                                    if _aftr.camp_id == _player_camp_id:
                                        continue
                                    if _aftr.fighter_id in _all_booked:
                                        continue
                                    if INJURY_AVAILABLE and self._injury_system \
                                            and not self._injury_system.is_cleared_to_fight(_aftr.fighter_id):
                                        continue
                                    _ai_opp = _aftr
                                    break
                                if _ai_opp:
                                    _t25_target = None
                                    for _wk25 in sorted(self._upcoming_cards.keys()):
                                        if _wk25 <= current_week:
                                            continue
                                        _card25 = self._upcoming_cards[_wk25]
                                        _has_main_25 = any(
                                            _f25.get("card_slot") == "main_event"
                                            for _f25 in _card25.get("fights", [])
                                        )
                                        if not _has_main_25:
                                            _t25_target = _card25
                                            break
                                    if _t25_target:
                                        _t25_week  = _t25_target["week"]
                                        _t25_event = _t25_target["event_name"]
                                        _offer = {
                                            "offer_id":         f"vacant_title_{wc}_{_r1_ftr.fighter_id}_{current_week}",
                                            "fighter_id":       _r1_ftr.fighter_id,
                                            "fighter_name":     _r1_ftr.name,
                                            "opponent_id":      _ai_opp.fighter_id,
                                            "opponent_name":    _ai_opp.name,
                                            "opponent_record":  f"{_ai_opp.wins}-{_ai_opp.losses}",
                                            "opponent_rating":  _ai_opp.overall_rating,
                                            "opponent_rank":    self._get_fighter_rank(_ai_opp),
                                            "opponent_momentum": self._get_momentum_tag(_ai_opp),
                                            "weight_class":     wc,
                                            "event_name":       _t25_event,
                                            "week":             _t25_week,
                                            "weeks_away":       max(1, _t25_week - current_week),
                                            "purse":            100000,
                                            "win_bonus":        50000,
                                            "is_title_fight":   True,
                                            "risk_level":       3,
                                            "reward_level":     5,
                                            "matchup_quality":  "Excellent",
                                            "source":           "vacant_title",
                                            "vacant_division":  wc,
                                            "created_week":     current_week,
                                        }
                                        self._fight_offers.append(_offer)
                                        self._news_items.insert(0, {
                                            "headline": (f"🏆 VACANT TITLE OFFER: "
                                                         f"{_r1_ftr.name} vs {_ai_opp.name} "
                                                         f"for the {wc} belt at {_t25_event}."),
                                            "category": "title",
                                            "week":     current_week,
                                        })
                                        print(f"  🏆 [VACANT TITLE OFFER] {wc} — "
                                              f"{_r1_ftr.name} (player) vs {_ai_opp.name} "
                                              f"at {_t25_event} (Wk {_t25_week})")
                                        _slice_2_5_handled = True

                        if _slice_2_5_handled:
                            continue

                        # Slice 2 — book vacant-title fight via shared helper (sub-ship B)
                        self._book_title_fight(
                            wc,
                            exclude_ids={champ.fighter_id} if champ else None,
                        )

            # ── Autosave every 5 weeks ─────────────────────────────────
            self.autosave_if_due(self._game_state.week_number)

            # ── Update all division rankings ───────────────────────────
            self._update_all_rankings()

            # ── Attach rank deltas to each fight result ────────────────
            player_ids_set = {f.fighter_id for f in self.get_player_fighters()}
            for result in fight_results:
                for role, fid in [("winner", result.get("winner_id")),
                                   ("loser",  result.get("loser_id"))]:
                    if not fid:
                        continue
                    old_r = pre_ranks.get(fid)
                    rec   = self._game_state.get_fighter(fid) if self._game_state else None
                    new_r = self._get_fighter_rank(rec) if rec else None
                    if role == "winner":
                        result["winner_old_rank"] = old_r
                        result["winner_new_rank"] = new_r
                        result["winner_rank_delta"] = self._rank_delta(old_r, new_r)
                    else:
                        result["loser_old_rank"] = old_r
                        result["loser_new_rank"] = new_r
                        result["loser_rank_delta"] = self._rank_delta(old_r, new_r)

            # ── Media reactions ────────────────────────────────────────
            for result in fight_results:
                fid = result.get("fight_id", "")
                if fid and fid not in self._media_reactions:
                    reactions = self._generate_media_reactions(result)
                    if reactions:
                        self._media_reactions[fid] = reactions

            # ── FOTN — select from ALL fights on this card (player + AI) ──
            # Gather all fights including the AI card so player can win FOTN
            all_card_fights = list(fight_results)
            if ai_event:
                all_card_fights.extend(ai_event.get("fights", []))

            fotn_result = None
            fotn_score  = 0.0
            if len(all_card_fights) >= 2:
                try:
                    if FOTN_AVAILABLE:
                        fotn_result, fotn_score = select_fotn(all_card_fights)
                    else:
                        fotn_result = self._select_fotn_builtin(all_card_fights)
                except Exception:
                    fotn_result = self._select_fotn_builtin(all_card_fights)

            if fotn_result:
                fotn_fid = fotn_result.get("fight_id")
                # Flag exactly ONE fight — explicitly clear all others
                for fr in fight_results:
                    if fr.get("fight_id") == fotn_fid:
                        fr["is_fotn"] = True
                        if fr.get("winner_id") in player_ids_set or fr.get("loser_id") in player_ids_set:
                            self._camp_balance        += FOTN_BONUS
                            self._total_purses_earned += FOTN_BONUS
                            self._week_purses_earned  += FOTN_BONUS
                    else:
                        fr["is_fotn"] = False  # Explicitly clear
                # Career FOTN awards — both fighters in the selected fight get +1
                for _fid in [fotn_result.get('fighter1_id', ''),
                             fotn_result.get('fighter2_id', '')]:
                    if _fid and self._game_state:
                        _ff = self._game_state.get_fighter(_fid)
                        if _ff:
                            _ff.career_fotn_awards = getattr(
                                _ff, 'career_fotn_awards', 0) + 1
                if ai_event:
                    for fr in ai_event.get("fights", []):
                        if fr.get("fight_id") == fotn_fid:
                            fr["is_fotn"] = True
                        else:
                            fr["is_fotn"] = False  # Explicitly clear
                f1n = fotn_result.get("fighter1_name", "")
                f2n = fotn_result.get("fighter2_name", "")
                # Populate event.fotn on the containing event for archive surface
                # Use systems/fotn factory so score, excitement tier, method,
                # and was_title_fight reach the templates. Override bonus key
                # name (factory produces bonus_amount; templates read bonus).
                # Fighter IDs are set explicitly — factory falls back to
                # winner_id/loser_id which can differ from f1/f2 ordering.
                if FOTN_AVAILABLE and hasattr(_fm, 'create_fotn_result'):
                    _fotn_obj = _fm.create_fotn_result(fotn_result, fotn_score, f1n, f2n)
                    fotn_dict = _fotn_obj.to_dict()
                    fotn_dict['fight_id']        = fotn_fid
                    fotn_dict['fighter1_id']     = fotn_result.get('fighter1_id', '')
                    fotn_dict['fighter2_id']     = fotn_result.get('fighter2_id', '')
                    fotn_dict['excitement_tier'] = get_excitement_tier(fotn_score)
                    fotn_dict['score']           = round(fotn_score, 1)
                    fotn_dict['bonus']           = FOTN_BONUS
                else:
                    fotn_dict = {
                        "fight_id":        fotn_fid,
                        "fighter1_name":   f1n,
                        "fighter2_name":   f2n,
                        "fighter1_id":     fotn_result.get('fighter1_id', ''),
                        "fighter2_id":     fotn_result.get('fighter2_id', ''),
                        "bonus":           FOTN_BONUS,
                        "excitement_tier": "",
                        "score":           0,
                    }
                current_wk = self._game_state.week_number if self._game_state else 0
                for ev in self._completed_events:
                    if ev.get("week") == current_wk and any(
                            f.get("fight_id") == fotn_fid for f in ev.get("fights", [])):
                        ev["fotn"] = fotn_dict
                        break
                self._news_items.insert(0, {
                    "headline": f"🔥 FIGHT OF THE NIGHT: {f1n} vs {f2n} — ${FOTN_BONUS:,} bonus each!",
                    "category": "fotn",
                    "week":     self._game_state.week_number if self._game_state else 1,
                })

            # ── Inbound fight offers from promotion ───────────────────
            # 20% chance per week per idle player fighter — promotion offers
            # a fight against a nearby ranked opponent. Creates passive pressure.
            self._maybe_generate_inbound_offers()

            # ── Yearly awards — fire every 52 weeks ───────────────────
            if self._game_state.week_number % 52 == 0:
                self._run_yearly_awards(self._game_state.week_number)

            # Offers are no longer auto-generated — fights come from the ladder

            self._clear_cache()
            return {
                "success":          True,
                "week":             self._game_state.week_number,
                "report":           report,
                "fights_completed": fight_results,
                "training_report":  training_report,
            }
        except Exception as e:
            print(f"Error advancing week: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _run_yearly_awards(self, week: int) -> None:
        """
        Fire yearly awards at week 52, 104, 156...
        Categories: Fighter of the Year, Young Fighter of the Year (<25),
        KO of Year, Sub of Year, Comeback Fighter, Camp of Year.
        Results stored as news items and in _yearly_awards.
        """
        import random
        if not self._game_state:
            return

        year = week // 52
        fighters = [f for f in self._game_state.fighters.values() if f.is_active]
        # Only fighters with fights this year (in completed events last 52 weeks)
        year_start = week - 52
        active_fids = set()
        year_fights: Dict[str, List[Dict]] = {}  # fighter_id → fights this year
        for ev in self._completed_events:
            if ev.get('week', 0) < year_start:
                continue
            for fight in ev.get('fights', []):
                for fid in [fight.get('winner_id'), fight.get('loser_id')]:
                    if fid:
                        active_fids.add(fid)
                        year_fights.setdefault(fid, []).append(fight)

        if not active_fids:
            return

        def wins_this_year(fid):
            return sum(1 for f in year_fights.get(fid, []) if f.get('winner_id') == fid)

        def best_win_rank(fid):
            best = 99
            for f in year_fights.get(fid, []):
                if f.get('winner_id') == fid:
                    opp_id = f.get('loser_id')
                    if opp_id:
                        opp = self._game_state.get_fighter(opp_id)
                        if opp:
                            r = self._get_fighter_rank(opp) or 99
                            best = min(best, r)
            return best

        awards = []
        structured: Dict[str, Any] = {}   # Ship YS1: structured per-award capture

        # ── GOAT formula applied to this year's fights only ────────
        # Points = (wins × 10) + (KO/TKO wins × 5) + (SUB wins × 3) − (losses × 2)
        # Same formula as the all-time GOAT rankings, scoped to year window.
        def year_points(fid):
            pts = 0
            for f in year_fights.get(fid, []):
                if f.get('winner_id') == fid:
                    method = f.get('method', 'DEC')
                    pts += 10
                    if method in ('KO', 'TKO'):
                        pts += 5
                    elif method == 'SUB':
                        pts += 3
                else:
                    pts -= 2
            return pts

        # ── Fighter of the Year ─────────────────────────────────────
        candidates = [(fid, year_points(fid))
                      for fid in active_fids if year_points(fid) > 0]
        if candidates:
            foty_id, foty_pts = max(candidates, key=lambda x: x[1])
            foty = self._game_state.get_fighter(foty_id)
            if foty:
                wins = wins_this_year(foty_id)
                awards.append(f"🏆 FIGHTER OF THE YEAR (Year {year}): {foty.name} "
                              f"({foty_pts} pts · {wins} wins · {foty.wins}-{foty.losses})")
                structured["fighter_of_year"] = {
                    "fighter_id": foty_id,
                    "name":       foty.name,
                    "pts":        foty_pts,
                    "wins":       wins,
                    "record":     f"{foty.wins}-{foty.losses}-{foty.draws}",
                }

        # ── Young Fighter of the Year (under 25) ────────────────────
        young = [(fid, year_points(fid))
                 for fid in active_fids
                 if year_points(fid) > 0 and
                    getattr(self._game_state.get_fighter(fid), 'age', 30) < 25]
        if young:
            yoty_id, yoty_pts = max(young, key=lambda x: x[1])
            yoty = self._game_state.get_fighter(yoty_id)
            if yoty:
                wins = wins_this_year(yoty_id)
                awards.append(f"⭐ YOUNG FIGHTER OF THE YEAR (Year {year}): {yoty.name} "
                              f"(Age {yoty.age} · {yoty_pts} pts · {wins} wins)")
                structured["young_foty"] = {
                    "fighter_id": yoty_id,
                    "name":       yoty.name,
                    "pts":        yoty_pts,
                    "wins":       wins,
                    "age":        getattr(yoty, 'age', 0),
                }

        # ── KO of the Year ──────────────────────────────────────────
        ko_fights = [
            f for ev in self._completed_events
            if ev.get('week', 0) >= year_start
            for f in ev.get('fights', [])
            if f.get('method') in ('KO', 'TKO') and f.get('is_fotn')
        ]
        if ko_fights:
            ko = random.choice(ko_fights)
            awards.append(f"💥 KO OF THE YEAR (Year {year}): "
                          f"{ko.get('winner_name')} def. {ko.get('loser_name')} "
                          f"via {ko.get('method')} R{ko.get('round_finished', '?')}")
            structured["ko_of_year"] = {
                "winner_id":   ko.get("winner_id", ""),
                "winner_name": ko.get("winner_name", ""),
                "loser_name":  ko.get("loser_name", ""),
                "method":      ko.get("method", "KO"),
                "round":       ko.get("round_finished", 0),
                "fight_id":    ko.get("fight_id", ""),
            }

        # ── Submission of the Year ──────────────────────────────────
        sub_fights = [
            f for ev in self._completed_events
            if ev.get('week', 0) >= year_start
            for f in ev.get('fights', [])
            if f.get('method') == 'SUB' and f.get('is_fotn')
        ]
        if sub_fights:
            sub = random.choice(sub_fights)
            awards.append(f"🥋 SUBMISSION OF THE YEAR (Year {year}): "
                          f"{sub.get('winner_name')} def. {sub.get('loser_name')} "
                          f"by SUB R{sub.get('round_finished', '?')}")
            structured["sub_of_year"] = {
                "winner_id":   sub.get("winner_id", ""),
                "winner_name": sub.get("winner_name", ""),
                "loser_name":  sub.get("loser_name", ""),
                "round":       sub.get("round_finished", 0),
                "fight_id":    sub.get("fight_id", ""),
            }

        # ── Comeback Fighter of the Year ────────────────────────────
        comeback = None
        best_comeback_wins = 0
        for fid in active_fids:
            f = self._game_state.get_fighter(fid)
            if not f:
                continue
            w = wins_this_year(fid)
            history = getattr(f, 'fight_history', [])
            if len(history) >= 4 and w >= 3:
                # Check if they had a losing streak before this year's wins
                recent = history[-6:]
                had_loss = any(h.get('result') == 'L' for h in recent[:3])
                if had_loss and w > best_comeback_wins:
                    best_comeback_wins = w
                    comeback = f
        if comeback:
            awards.append(f"💪 COMEBACK FIGHTER OF THE YEAR (Year {year}): "
                          f"{comeback.name} ({wins_this_year(comeback.fighter_id)} wins this year)")
            structured["comeback"] = {
                "fighter_id": comeback.fighter_id,
                "name":       comeback.name,
                "wins":       best_comeback_wins,
            }

        # ── Camp of the Year ────────────────────────────────────────
        camp_wins: Dict[str, int] = {}
        for ev in self._completed_events:
            if ev.get('week', 0) < year_start:
                continue
            for fight in ev.get('fights', []):
                wid = fight.get('winner_id')
                if wid:
                    wf = self._game_state.get_fighter(wid)
                    if wf and wf.camp_id:
                        camp_wins[wf.camp_id] = camp_wins.get(wf.camp_id, 0) + 1
        if camp_wins:
            best_camp_id = max(camp_wins, key=camp_wins.get)
            best_camp    = self._game_state.camps.get(best_camp_id)
            if best_camp:
                awards.append(f"🏟️ CAMP OF THE YEAR (Year {year}): "
                              f"{best_camp.name} ({camp_wins[best_camp_id]} wins)")
                structured["camp_of_year"] = {
                    "camp_id": best_camp_id,
                    "name":    best_camp.name,
                    "wins":    camp_wins[best_camp_id],
                }

        # ── Fire all awards as news ──────────────────────────────────
        for award_text in awards:
            self._news_items.insert(0, {
                "headline": award_text,
                "category": "award",
                "week":     week,
                "icon":     "🏆",
            })
            print(f"🏆 {award_text}")

        # Store in record
        if not hasattr(self, '_yearly_awards'):
            self._yearly_awards = []
        self._yearly_awards.append({"year": year, "week": week,
                                    "awards": awards, "structured": structured})

        # Ship HOF1: induct eligible retired fighters at each year boundary.
        HOF_THRESHOLD = 60
        _all_ftrs = list(self._game_state.fighters.values())
        _inducted_ids = {h["fighter_id"] for h in self._hof_inductees}
        for _ftr in _all_ftrs:
            if getattr(_ftr, 'is_active', True):
                continue
            if _ftr.fighter_id in _inducted_ids:
                continue
            _reigns = [
                r for _wc_list in self._title_history.values()
                for r in _wc_list
                if r.get("champion_id") == _ftr.fighter_id
            ]
            _title_count = len(_reigns)
            _def_count = sum(r.get("successful_defenses", 0) for r in _reigns)
            _best = getattr(_ftr, 'best_rank', 99)
            _rank_pts = max(0, (15 - _best) * 2)
            _score = (
                _ftr.wins * 3
                + _ftr.ko_wins * 2
                + _ftr.sub_wins * 2
                + _title_count * 25
                + _def_count * 10
                + _rank_pts
                + getattr(_ftr, 'popularity', 10) * 0.3
            )
            if _score < HOF_THRESHOLD:
                continue
            _wc = getattr(_ftr, 'weight_class', '')
            self._hof_inductees.append({
                "fighter_id":     _ftr.fighter_id,
                "name":           _ftr.name,
                "nickname":       getattr(_ftr, 'nickname', None),
                "weight_class":   _wc,
                "record":         f"{_ftr.wins}-{_ftr.losses}-{_ftr.draws}",
                "wins":           _ftr.wins,
                "losses":         _ftr.losses,
                "ko_wins":        _ftr.ko_wins,
                "sub_wins":       _ftr.sub_wins,
                "title_reigns":   _title_count,
                "title_defenses": _def_count,
                "best_rank":      _best,
                "popularity":     getattr(_ftr, 'popularity', 10),
                "prestige_score": round(_score),
                "year_inducted":  year,
                "week_inducted":  week,
            })
            _inducted_ids.add(_ftr.fighter_id)
            self._news_items.insert(0, {
                "headline":    (f"🏛️ HALL OF FAME: {_ftr.name} inducted "
                                f"into the Cage Dynasty Hall of Fame!"),
                "category":    "award",
                "week":        week,
                "icon":        "🏛️",
                "fighter1_id": _ftr.fighter_id,
            })
            print(f"  🏛️  [HOF] {_ftr.name} inducted (score: {round(_score)})")

    def get_yearly_awards(self) -> List[Dict[str, Any]]:
        """Ship YS1: return all yearly award records for the year-summary
        surface. Each entry: {year, week, awards: List[str], structured: Dict}."""
        return list(getattr(self, '_yearly_awards', []))

    def _expire_stale_offers(self, max_age_weeks: int = 3) -> None:
        """Drop offers older than max_age_weeks. Fires once per advance.
        Legacy offers without created_week get stamped on first sight."""
        if not self._game_state:
            return
        current = self._game_state.week_number
        kept, dropped = [], []
        for o in self._fight_offers:
            created = o.get("created_week")
            if created is None:
                o["created_week"] = current
                kept.append(o)
                continue
            if current - created > max_age_weeks:
                dropped.append(o)
            else:
                kept.append(o)
        self._fight_offers = kept
        for o in dropped:
            self._news_items.insert(0, {
                "headline": (f"⌛ Offer lapsed: "
                             f"{o.get('fighter_name','?')} vs "
                             f"{o.get('opponent_name','?')} "
                             f"({o.get('event_name','?')})"),
                "category": "signing",
                "week":     current,
            })

    def _maybe_generate_inbound_offers(self) -> None:
        """
        Promotion occasionally approaches player fighters with fight offers.
        Tier-aware probability per idle fighter per week. Opponent is
        ±3 ranks from player (champion only takes top-5 contenders).
        Creates passive pressure — player isn't always the aggressor.
        """
        self._expire_stale_offers()
        import random
        if not self._game_state:
            return

        scheduled_fids = set()
        for sf in self._scheduled_fights:
            scheduled_fids.add(sf.get('fighter1_id', ''))
            scheduled_fids.add(sf.get('fighter2_id', ''))

        # Check existing offers — don't pile on
        existing_offer_fids = {o.get('fighter_id') for o in self._fight_offers}

        player_fighters = self._game_state.get_player_fighters()
        week = self._game_state.week_number

        for pf in player_fighters:
            fid = pf.fighter_id
            # Skip if already scheduled or has offer pending
            if fid in scheduled_fids or fid in existing_offer_fids:
                continue

            # Skip injured fighters — they can't accept fights
            if INJURY_AVAILABLE and self._injury_system:
                if not self._injury_system.is_cleared_to_fight(fid):
                    continue
            # Tier-aware offer probability — higher ranked fighters
            # attract more offers. Champion only gets top-5 challengers.
            _pr = self._get_fighter_rank(pf)
            if _pr == 0:                        # Champion
                _offer_chance = 0.40
            elif _pr is not None and _pr <= 5:  # Top 5
                _offer_chance = 0.30
            elif _pr is not None and _pr <= 15: # Top 15
                _offer_chance = 0.20
            else:                               # Unranked
                _offer_chance = 0.10
            # Ship K5: personality biases offer frequency
            _personality = self._game_state._fighter_data.get(
                fid, {}).get('personality') or getattr(
                    pf, 'personality', '') or 'Competitor'
            _PERS_OFFER_MULT = {
                "Warrior":    1.3,
                "Hungry":     1.4,
                "Competitor": 1.0,
                "Calculated": 0.7,
                "Political":  0.8,
            }
            _offer_chance *= _PERS_OFFER_MULT.get(_personality, 1.0)
            _offer_chance = min(_offer_chance, 0.70)

            if random.random() > _offer_chance:
                continue

            # Find an appropriate opponent: ±3 ranks
            division = self._game_state.divisions.get(pf.weight_class)
            if not division:
                continue

            player_rank = _pr  # already computed above
            candidates  = []

            for ranked_id in division.rankings:
                if ranked_id == fid or ranked_id in scheduled_fids:
                    continue
                opp = self._game_state.get_fighter(ranked_id)
                if not opp or not opp.is_active:
                    continue
                opp_rank = self._get_fighter_rank(opp)
                if opp_rank is None:
                    continue
                # Allow ±3 rank difference, or unranked vs rank 10-15
                if player_rank is None:
                    if opp_rank and opp_rank >= 10:
                        candidates.append(opp)
                elif abs((opp_rank or 99) - player_rank) <= 3:
                    candidates.append(opp)

            # Champion only fights top-5 contenders
            if _pr == 0:
                candidates = [c for c in candidates
                              if self._get_fighter_rank(c) is not None
                              and self._get_fighter_rank(c) <= 5]
            if not candidates:
                continue

            opp = random.choice(candidates)
            opp_rank = self._get_fighter_rank(opp)
            weeks_away = self._weeks_out_for_fight(
                self._get_fighter_rank(pf), opp_rank
            )
            event_week = week + weeks_away
            event_name = self._dfc_label(event_week)

            # Purse scales with rank + situational modifiers
            base_purse = max(8000, 25000 - ((opp_rank or 10) * 800))

            # Situational multipliers
            win_streak  = getattr(pf, 'win_streak', 0) or 0
            lose_streak = getattr(pf, 'lose_streak', 0) or 0
            is_title    = (opp_rank == 0)
            sit_mult = 1.0
            if win_streak >= 3:  sit_mult += 0.25   # Leverage from hot streak
            elif win_streak >= 1: sit_mult += 0.10  # Fresh win
            if lose_streak >= 2:  sit_mult -= 0.15  # Skid = lower bids
            if is_title:          sit_mult += 0.60  # Title fight premium
            elif (opp_rank or 10) <= 3: sit_mult += 0.35  # Top contender danger money
            if weeks_away <= 3:   sit_mult += 0.30  # Short notice premium

            purse     = int(base_purse * max(0.7, sit_mult) * random.uniform(0.9, 1.1))
            win_bonus = int(purse * 0.5)

            risk_level   = min(5, max(1, 3 + ((opp_rank or 8) - (player_rank or 8))))
            reward_level = min(5, max(1, 4 - ((opp_rank or 8) - (player_rank or 8))))

            offer_id = f"inbound_{fid}_{week}_{opp.fighter_id}"
            offer = {
                "offer_id":        offer_id,
                "fighter_id":      fid,
                "fighter_name":    pf.name,
                "opponent_id":     opp.fighter_id,
                "opponent_name":   opp.name,
                "opponent_record": f"{opp.wins}-{opp.losses}",
                "opponent_rating": opp.overall_rating,
                "opponent_rank":   opp_rank,
                "opponent_momentum": self._get_momentum_tag(opp),
                "weight_class":    pf.weight_class if isinstance(pf.weight_class, str) else str(pf.weight_class),
                "event_name":      event_name,
                "week":            event_week,
                "weeks_away":      weeks_away,
                "purse":           purse,
                "win_bonus":       win_bonus,
                "is_title_fight":  is_title,
                "risk_level":      risk_level,
                "reward_level":    reward_level,
                "matchup_quality": "Excellent" if risk_level <= 2 else "Good" if risk_level <= 3 else "Fair",
                "accept_chance":   75,
                "source":          "promotion",
                "created_week":    week,
            }
            self._fight_offers.append(offer)

            self._news_items.insert(0, {
                "headline": f"📨 {PROMOTION_NAME} offers {pf.name} a fight vs {opp.name}"
                            f" ({opp.wins}-{opp.losses})"
                            f"{f' · #{opp_rank}' if opp_rank else ''}",
                "category": "signing",
                "week":     week,
                "icon":     "📨",
            })

    def _apply_post_fight_camp_record(
        self, winner, loser, fight: Dict[str, Any], method: str,
    ) -> None:
        """
        Update camp records and emit player-camp result headlines after a fight.

        - Bumps camp_rec.total_wins / total_losses for both fighters' camps.
        - Bumps self._player_camp_wins / _player_camp_losses when a player
          camp fighter is involved (persists through save/load).
        - Inserts a contextual headline into self._news_items for player results.
        - Clears self._camp_cache so the dashboard reflects updated state.

        No-op when self._game_state is None.
        """
        if not self._game_state:
            return

        is_title_fight = fight.get("is_title_fight", False)

        for fid, is_win in [(winner.fighter_id, True), (loser.fighter_id, False)]:
            ftr = self._game_state.get_fighter(fid)
            if not ftr:
                continue
            # Earn nickname on win when threshold crossed:
            # 5 wins, 7 fights, AND (≥40% finish rate OR ≥3-fight streak).
            # Backfill in web_load keeps the looser legacy gate so old saves
            # don't strip veterans of their nicknames on load.
            if is_win and not getattr(ftr, 'nickname', None):
                _total_fights = (ftr.wins or 0) + (ftr.losses or 0) + (ftr.draws or 0)
                _finish_rate = 0.0
                if _total_fights > 0:
                    _finishes = sum(
                        1 for f in (getattr(ftr, 'fight_history', []) or [])
                        if isinstance(f, dict)
                        and f.get('method') in ('KO', 'TKO', 'SUB')
                        and f.get('result') == 'W'
                    )
                    _finish_rate = _finishes / _total_fights
                _win_streak = 0
                _fh = list(getattr(ftr, 'fight_history', []) or [])
                for _fh_entry in reversed(_fh):
                    if not isinstance(_fh_entry, dict):
                        break
                    if _fh_entry.get('result') == 'W':
                        _win_streak += 1
                    else:
                        break
                _perf_gate = (_finish_rate >= 0.40 or _win_streak >= 3)
                if ftr.wins >= 5 and _total_fights >= 7 and _perf_gate:
                    from game_state import NICKNAMES_POOL as _NK_POOL
                    import random as _nk_random
                    ftr.nickname = _nk_random.choice(_NK_POOL)
                    self._news_items.insert(0, {
                        "headline": f"📢 {ftr.name} adopts the nickname \"{ftr.nickname}\".",
                        "category": "fighter",
                        "week": self._game_state.week_number if self._game_state else 1,
                    })
                    print(f"  📢 [NICKNAME] {ftr.name} → \"{ftr.nickname}\" "
                          f"({ftr.wins}-{ftr.losses}{f'-{ftr.draws}' if ftr.draws else ''})")

            # Pro debut alert — signed amateur's first pro fight (Slice A.1)
            if len(getattr(ftr, 'fight_history', []) or []) == 1:
                _sys = self._get_amateur_system()
                if _sys and _sys.amateurs.get(fid):
                    _ev = fight.get('event_name', PROMOTION_NAME)
                    _opp_name = loser.name if is_win else winner.name
                    if is_win:
                        _hl = f"🆕 {ftr.name} wins pro debut over {_opp_name} at {_ev} — {method}"
                    else:
                        _hl = f"🆕 {ftr.name} drops pro debut to {_opp_name} at {_ev} — {method}"
                    self._news_items.insert(0, {
                        "headline": _hl,
                        "category": "fight",
                        "week": self._game_state.week_number if self._game_state else 1,
                    })
                    print(f"  🆕 [PRO DEBUT] {ftr.name} "
                          f"{'wins' if is_win else 'loses'} via {method}")
            # Update via camp record if available
            if ftr.camp_id:
                camp_rec = self._game_state.camps.get(ftr.camp_id)
                if camp_rec:
                    if is_win:
                        camp_rec.total_wins = getattr(camp_rec, 'total_wins', 0) + 1
                    else:
                        camp_rec.total_losses = getattr(camp_rec, 'total_losses', 0) + 1
            # Also track player camp wins on bridge (persists through save/load)
            # Check both camp_id match AND direct player fighter list
            _is_player_fighter = any(
                pf.fighter_id == fid
                for pf in self.get_player_fighters()
            )
            _camp_match = (self._game_state.player_camp_id and
                           ftr.camp_id == self._game_state.player_camp_id)
            if _is_player_fighter or _camp_match:
                if is_win:
                    self._player_camp_wins   += 1
                    # Contextual win headline
                    _fname = ftr.name.split()[0] if ftr.name else "Fighter"
                    _opp_name = loser.name if is_win else winner.name
                    if is_title_fight:
                        _hl = f"🏆 {ftr.name} IS THE NEW CHAMPION — stunning title win at {fight.get('event_name', PROMOTION_NAME)}!"
                    elif method in ("KO", "TKO"):
                        _hl = f"💥 {ftr.name} puts the division on notice — {method} finish at {fight.get('event_name', PROMOTION_NAME)}"
                    elif method == "SUB":
                        _hl = f"🔒 {ftr.name} locks up the submission — makes a statement at {fight.get('event_name','DFC')}"
                    else:
                        _hl = f"📋 {ftr.name} grinds out the decision — showing championship mentality"
                    self._news_items.insert(0, {
                        "headline": _hl,
                        "category": "player_result",
                        "week": self._game_state.week_number,
                    })
                else:
                    self._player_camp_losses += 1
                    # Contextual loss headline
                    _hl = f"📉 {ftr.name} suffers setback — back to the drawing board"
                    self._news_items.insert(0, {
                        "headline": _hl,
                        "category": "player_result",
                        "week": self._game_state.week_number,
                    })
            elif fight.get("is_player_fight") and not ftr.camp_id:
                # Free-agent the player booked via challenge/offer flow.
                # No camp-record bump (no camp to bump). Fire a 📋 Free Agents
                # news item so the player knows the booking resolved and the
                # fighter is back in the pool, addressable via /fighter/<id>
                # (existing Challenge button on profile page).
                _opp_name = loser.name if is_win else winner.name
                _ev = fight.get("event_name", "DFC")
                if is_win:
                    _hl = (f"📋 Free agent {ftr.name} won for you over {_opp_name} "
                           f"at {_ev} — back in the pool, available to challenge again.")
                else:
                    _hl = (f"📋 Free agent {ftr.name} dropped one to {_opp_name} "
                           f"at {_ev} — back in the pool.")
                self._news_items.insert(0, {
                    "headline": _hl,
                    "category": "contract",
                    "week":     self._game_state.week_number,
                })
        # Clear camp cache so dashboard shows updated record
        self._camp_cache.clear()

    def _apply_post_fight_experience(
        self,
        fighter_id: str,
        opponent_id: str,
        my_stats: List[Dict[str, Any]],
        opp_stats: List[Dict[str, Any]],
        method: str,
        won: bool,
        total_rounds: int,
    ) -> None:
        """Post-fight stat nudges driven by what actually happened in the fight.

        Reads per-round stats from the engine (NarratedFightResult) and bumps
        attributes that the fight exercised. Small magnitudes (≤0.4 raw per
        stat) — meant to compound over a career, not to swing a single OVR.

        Routes through _diminishing_gain so the OVR2 athletic/technical
        multiplier + per-fighter potential ceiling + camp-tier soft ceil
        all apply. Negative nudges (cumulative damage, lost-via-KO) apply
        directly with a floor of 1.

        Caller is responsible for demuxing engine fighter1_stats vs
        fighter2_stats into my_stats/opp_stats — NarratedFightResult
        doesn't carry fighter1_id/fighter2_id so the bridge does it.
        """
        if not self._game_state:
            return
        fighter = self._game_state.get_fighter(fighter_id)
        if fighter is None:
            return
        if not my_stats:
            return

        # Sum across all rounds
        total_td_landed         = sum(r.get("td_landed", 0) for r in my_stats)
        total_sub_att           = sum(r.get("sub_att", 0) for r in my_stats)
        total_control           = sum(r.get("control_time", 0.0) for r in my_stats)
        total_sig_landed        = sum(r.get("sig_strikes_landed", 0) for r in my_stats)
        total_knockdowns_scored = sum(r.get("knockdowns", 0) for r in my_stats)
        # Head strikes RECEIVED — come from opponent's "head_strikes" (= landed by them).
        total_head_received     = sum(r.get("head_strikes", 0) for r in (opp_stats or []))

        nudges: Dict[str, float] = {}

        # Grappling experience
        if total_td_landed >= 3:
            nudges["takedowns"] = 0.4 + min(0.4, total_td_landed * 0.05)
        if total_sub_att >= 2:
            nudges["submissions"] = 0.3 + min(0.4, total_sub_att * 0.08)
        if total_control >= 60:   # seconds
            nudges["top_control"] = 0.3 + min(0.3, total_control / 300)

        # Striking experience
        if total_sig_landed >= 20:
            nudges["boxing"] = 0.3 + min(0.3, total_sig_landed * 0.005)
        if total_knockdowns_scored >= 1:
            nudges["composure"] = 0.4   # finishing instinct / mental edge

        # Durability (head strikes received) — toughness vs cumulative damage.
        # Severe-damage threshold overrides the toughness nudge (negative wins).
        if total_head_received >= 15:
            nudges["chin"] = 0.2
        if total_head_received >= 30:
            nudges["chin"] = -0.3

        # Method-based outcome bumps
        method_upper = method.upper()
        if won:
            if "SUB" in method_upper:
                nudges["submissions"] = nudges.get("submissions", 0) + 0.3
                nudges["guard"] = 0.2     # finishing subs requires guard work
            if "KO" in method_upper or "TKO" in method_upper:
                nudges["composure"] = nudges.get("composure", 0) + 0.3
        else:
            if "SUB" in method_upper:
                nudges["guard"] = nudges.get("guard", 0) + 0.4   # learned the hard way
            if "KO" in method_upper or "TKO" in method_upper:
                nudges["chin"] = nudges.get("chin", 0) - 0.2     # cumulative damage

        # Cardio (rounds survived)
        if total_rounds >= 3:
            nudges["cardio"] = 0.2 * min(total_rounds, 5) / 3

        # Apply nudges
        camp_tier = self._get_camp_tier()
        _fp = self._game_state._fighter_data.get(fighter_id, {}).get("potential")
        _fp = int(_fp) if _fp is not None else None

        # Stats live in _fighter_data (Ship #32) — read/write there.
        _exp_fdata = self._game_state._fighter_data.get(fighter_id, {})
        for stat, raw in list(nudges.items()):
            if raw == 0:
                continue
            current = float(_exp_fdata.get(stat, 50))
            if raw > 0:
                effective = self._diminishing_gain(
                    current, raw, camp_tier,
                    fighter_potential=_fp, stat_name=stat,
                )
                new_val = min(100.0, current + effective)
            else:
                # Negative nudge (damage / loss) — direct, floor at 1.
                new_val = max(1.0, current + raw)
            if fighter_id in self._game_state._fighter_data:
                self._game_state._fighter_data[fighter_id][stat] = round(new_val, 2)

        # Style-weighted OVR — see _compute_ovr for weight vectors.
        fighter.overall_rating = self._compute_ovr(fighter)

        # Log what actually changed
        changed = {s: r for s, r in nudges.items() if r != 0}
        if changed:
            print(f"  🎓 [EXPERIENCE] {fighter.name}: "
                  + ", ".join(f"{s}{'+' if v>0 else ''}{v:.1f}"
                              for s, v in changed.items()))

    def _simulate_fight(self, fight: Dict) -> Dict:
        """Simulate a fight and return enriched result dict."""
        import random

        fighter1 = self._game_state.get_fighter(fight["fighter1_id"])
        fighter2 = self._game_state.get_fighter(fight["fighter2_id"])

        if not fighter1 or not fighter2:
            return {"error": "Fighter not found"}

        f1_name = getattr(fighter1, 'name', fight.get("fighter1_name", "Fighter 1"))
        f2_name = getattr(fighter2, 'name', fight.get("fighter2_name", "Fighter 2"))

        # ── Real fight engine path ────────────────────────────────
        if FIGHT_ENGINE_AVAILABLE:
            try:
                result = self._run_real_engine(fight, fighter1, fighter2, f1_name, f2_name)
                if result:
                    return result
            except Exception as _rfe_exc:
                print(f"⚠️ Real fight engine failed: {_rfe_exc}, falling back to score sim")

        # ── Score-based fallback ──────────────────────────────────
        # Outcome based on record, rank, condition, and traits
        def _fight_score(f) -> float:
            wins   = getattr(f, 'wins', 0)
            losses = getattr(f, 'losses', 0)
            ko_w   = getattr(f, 'ko_wins', 0)
            sub_w  = getattr(f, 'sub_wins', 0)
            total  = wins + losses
            win_pct     = wins / max(1, total)
            finish_rate = (ko_w + sub_w) / max(1, wins)
            rank        = self._get_fighter_rank(f)
            rank_bonus  = (15 - (rank if rank is not None else 20)) * 1.5
            base = win_pct * 50 + finish_rate * 15 + rank_bonus + random.uniform(0, 30)

            # Condition modifier — fatigue reduces effectiveness
            if CONDITION_AVAILABLE:
                try:
                    fatigue  = getattr(f, 'fatigue', 0)
                    stamina  = get_starting_stamina(fatigue)   # 65-100
                    cond_mod = (stamina - 100) / 4             # -8.75 to 0
                    base    += cond_mod
                except Exception:
                    pass

            # Trait modifier
            if TRAITS_AVAILABLE:
                try:
                    fdata   = {}
                    if self._game_state and f.fighter_id in self._game_state._fighter_data:
                        fdata = self._game_state._fighter_data[f.fighter_id]
                    traits  = fdata.get("traits", [])
                    base   += get_trait_win_bonus(traits) * 100
                except Exception:
                    pass

            return base

        f1_score = _fight_score(fighter1)
        f2_score = _fight_score(fighter2)

        # Pressure/Counter trait interaction
        if TRAITS_AVAILABLE:
            try:
                def _get_traits(f):
                    if self._game_state and f.fighter_id in self._game_state._fighter_data:
                        return self._game_state._fighter_data[f.fighter_id].get("traits", [])
                    return []
                f1_t = _get_traits(fighter1)
                f2_t = _get_traits(fighter2)
                f1_mod, f2_mod = get_pressure_counter_interaction(f1_t, f2_t)
                f1_score += f1_mod * 50
                f2_score += f2_mod * 50
            except Exception:
                pass

        # ── Rivalry heat modifier ─────────────────────────────────
        if RIVALRY_AVAILABLE:
            try:
                rsys = get_rivalry_system()
                rivalry = rsys.get_rivalry(fighter1.fighter_id, fighter2.fighter_id)
                if rivalry:
                    heat = rivalry.score
                    if heat >= 60:
                        boost = heat * 0.08
                        f1_score += boost + random.uniform(-boost*0.5, boost*0.5)
                        f2_score += boost + random.uniform(-boost*0.5, boost*0.5)
                    elif heat >= 30:
                        boost = heat * 0.04
                        f1_score += boost
                        f2_score += boost
            except Exception:
                pass

        # ── Gameplan modifier — player uses saved gameplan, AI uses style-based ──
        # Style → gameplan lookup (mirrors _gameplan_from_style_matchup)
        _STYLE_GAMEPLAN = {
            "Wrestler":        "TAKEDOWN",   "Ground & Pound":  "GNP",
            "BJJ Specialist":  "SUBMISSION", "Clinch Fighter":  "CLINCH",
            "Muay Thai":       "AGGRESSIVE", "Brawler":         "AGGRESSIVE",
            "Pressure Fighter":"AGGRESSIVE", "Counter Striker": "DEFENSIVE",
            "Point Fighter":   "DEFENSIVE",  "Sprawl & Brawl":  "DEFENSIVE",
            "Sambo":           "TAKEDOWN",   "Judo":            "TAKEDOWN",
            "Kickboxer":       "MEASURED",   "Orthodox Boxer":  "MEASURED",
            "Karate":          "DEFENSIVE",  "Hybrid":          "BALANCED",
        }
        player_fids = set()
        if self._game_state and self._game_state.player_camp_id:
            player_fids = {
                f.fighter_id for f in self._game_state.get_player_fighters()
            }

        # Player gameplan from fight dict; AI gameplan from style
        if fighter1.fighter_id in player_fids:
            f1_gameplan = fight.get("gameplan", "BALANCED")
            f2_gameplan = _STYLE_GAMEPLAN.get(
                getattr(fighter2, 'fighting_style', ''), "BALANCED")
        elif fighter2.fighter_id in player_fids:
            f2_gameplan = fight.get("gameplan", "BALANCED")
            f1_gameplan = _STYLE_GAMEPLAN.get(
                getattr(fighter1, 'fighting_style', ''), "BALANCED")
        else:
            # AI vs AI — both get style-based gameplans
            f1_gameplan = _STYLE_GAMEPLAN.get(
                getattr(fighter1, 'fighting_style', ''), "BALANCED")
            f2_gameplan = _STYLE_GAMEPLAN.get(
                getattr(fighter2, 'fighting_style', ''), "BALANCED")

        GAMEPLAN_BONUS = {
            "AGGRESSIVE":  8,   "DEFENSIVE":   4,   "MEASURED":    5,
            "BALANCED":    2,   "TAKEDOWN":    7,   "GNP":         9,
            "SUBMISSION":  6,   "CLINCH":      6,
        }
        f1_score += GAMEPLAN_BONUS.get(f1_gameplan, 2)
        f2_score += GAMEPLAN_BONUS.get(f2_gameplan, 2)
        if f1_gameplan == "DEFENSIVE":   f2_score -= 4
        if f2_gameplan == "DEFENSIVE":   f1_score -= 4
        if f1_gameplan == "TAKEDOWN":    f1_score += 2
        if f2_gameplan == "TAKEDOWN":    f2_score += 2
        if f1_gameplan == "GNP":         f1_score += 1
        if f2_gameplan == "GNP":         f2_score += 1

        if f1_score >= f2_score:
            winner, loser = fighter1, fighter2
            winner_num, loser_num = 1, 2
        else:
            winner, loser = fighter2, fighter1
            winner_num, loser_num = 2, 1

        # Method selection — influenced by winner's actual gameplan
        winner_gameplan = f1_gameplan if winner.fighter_id == fighter1.fighter_id else f2_gameplan
        # Trait KO/Sub modifiers
        trait_ko_mod  = 0.0
        trait_sub_mod = 0.0
        if TRAITS_AVAILABLE:
            try:
                def _get_traits(f):
                    if self._game_state and f.fighter_id in self._game_state._fighter_data:
                        return self._game_state._fighter_data[f.fighter_id].get("traits", [])
                    return []
                w_traits = _get_traits(winner)
                for t in w_traits:
                    td = FIGHTER_TRAITS.get(t, {})
                    trait_ko_mod  += td.get("ko_mod", 0.0)
                    trait_sub_mod += td.get("sub_mod", 0.0)
            except Exception:
                pass
        # Thresholds: KO | TKO | SUB | DEC
        if winner_gameplan == "AGGRESSIVE":
            t_ko, t_tko, t_sub = 0.35, 0.55, 0.65   # Most KOs
        elif winner_gameplan == "DEFENSIVE":
            t_ko, t_tko, t_sub = 0.20, 0.38, 0.52   # Mostly decisions
        elif winner_gameplan == "MEASURED":
            t_ko, t_tko, t_sub = 0.25, 0.44, 0.60   # Patient, late finishes
        elif winner_gameplan == "TAKEDOWN":
            t_ko, t_tko, t_sub = 0.12, 0.30, 0.55   # Wrestle for control, sub threat
        elif winner_gameplan == "GNP":
            t_ko, t_tko, t_sub = 0.22, 0.58, 0.65   # Heavy TKOs from top
        elif winner_gameplan == "SUBMISSION":
            t_ko, t_tko, t_sub = 0.10, 0.22, 0.75   # Highest sub rate
        elif winner_gameplan == "CLINCH":
            t_ko, t_tko, t_sub = 0.18, 0.50, 0.62   # TKOs from clinch/elbows
        else:
            t_ko, t_tko, t_sub = 0.30, 0.50, 0.65
        # Apply trait modifiers
        t_ko  = min(0.55, max(0.05, t_ko  + trait_ko_mod))
        t_sub = min(0.80, max(t_tko + 0.01, t_sub + trait_sub_mod))
        thresholds = (t_ko, t_tko, t_sub)

        method_roll = random.random()
        if method_roll < thresholds[0]:
            method = "KO"
            round_finished = random.randint(1, 3)
        elif method_roll < thresholds[1]:
            method = "TKO"
            round_finished = random.randint(1, 3)
        elif method_roll < thresholds[2]:
            method = "SUB"
            round_finished = random.randint(1, 3)
        else:
            method = "DEC"
            round_finished = fight.get("total_rounds", 3)

        time_str = f"{random.randint(0, 4)}:{random.randint(10, 59):02d}"
        is_title_fight = fight.get("is_title_fight", False)

        # Update records
        winner.wins  += 1
        loser.losses += 1
        if method in ("KO", "TKO"):
            winner.ko_wins += 1
            loser.ko_losses = getattr(loser, 'ko_losses', 0) + 1
        elif method == "SUB":
            winner.sub_wins += 1
            loser.sub_losses = getattr(loser, 'sub_losses', 0) + 1

        # ── Judges scorecards (decisions only) ──────────────────
        scorecard_data = None
        if method == "DEC" and JUDGES_AVAILABLE:
            try:
                winner_rating = winner.overall_rating
                loser_rating  = loser.overall_rating
                dominance = calculate_dominance_from_fight(winner_rating, loser_rating)
                # fighter1 is always "fighter 1" in generate_decision
                # F39 fix: regenerate scorecard until tally agrees with
                # bridge's winner_num. Caps at 5 attempts (~99.99%
                # resolution at ~15% base mismatch rate).
                for _f39_attempt in range(5):
                    if winner_num == 1:
                        dec = generate_decision(
                            winner_dominance=dominance,
                            total_rounds=round_finished,
                            is_title_fight=is_title_fight,
                            fighter1_name=f1_name,
                            fighter2_name=f2_name,
                        )
                    else:
                        # Invert so fighter 1 in the card is the actual loser
                        dec = generate_decision(
                            winner_dominance=1.0 - dominance,
                            total_rounds=round_finished,
                            is_title_fight=is_title_fight,
                            fighter1_name=f1_name,
                            fighter2_name=f2_name,
                        )
                    _f1_tot = sum(sc.fighter1_score for sc in dec.scorecards)
                    _f2_tot = sum(sc.fighter2_score for sc in dec.scorecards)
                    _card_w = (1 if _f1_tot > _f2_tot
                               else 2 if _f2_tot > _f1_tot else 0)
                    if _card_w == winner_num or _card_w == 0:
                        break  # tally matches winner_num, or draw
                # Store scorecard as plain dicts for template rendering
                scorecard_data = {
                    "decision_type":    dec.decision_type.value,
                    "is_split":         dec.is_split,
                    "is_controversial": dec.is_controversial,
                    "controversy_reason": dec.controversy_reason,
                    "scores_display":   dec.get_scores_display(),
                    "judges": [
                        {
                            "name":    sc.judge_name,
                            "f1_score": sc.fighter1_score,
                            "f2_score": sc.fighter2_score,
                            "round_scores": sc.round_scores,
                            "winner_num": sc.winner,
                        }
                        for sc in dec.scorecards
                    ],
                }
                # Upgrade method string to split/unanimous for display
                if dec.is_split:
                    method = "SPLIT DEC"
                elif dec.decision_type.value == "Majority Decision":
                    method = "MAJ DEC"
                else:
                    method = "UNY DEC"
            except Exception as exc:
                print(f"⚠️ Scorecard generation failed: {exc}")

        # ── Build result dict ────────────────────────────────────
        result = {
            "fight_id":       fight.get("fight_id"),
            "fighter1_id":    fighter1.fighter_id,
            "fighter2_id":    fighter2.fighter_id,
            "fighter1_name":  f1_name,
            "fighter2_name":  f2_name,
            "winner_id":      winner.fighter_id,
            "winner_name":    winner.name,
            "winner_num":     winner_num,
            "loser_id":       loser.fighter_id,
            "loser_name":     loser.name,
            "method":         method,
            "round_finished": round_finished,
            "time":           time_str,
            "weight_class":   fight["weight_class"],
            "event_name":     fight["event_name"],
            "card_slot":      fight.get("card_slot", "prelim"),
            "is_title_fight": is_title_fight,
            "is_player_fight":fight.get("is_player_fight", False),
            "purse":          fight.get("purse", 0),
            "scorecard":      scorecard_data,
            "rivalry":        None,
        }

        # ── Rivalry detection ────────────────────────────────────
        if RIVALRY_AVAILABLE:
            try:
                ctx = FightContext(
                    fight_id=result["fight_id"] or f"fight_{fighter1.fighter_id}_{fighter2.fighter_id}",
                    fighter1_id=fighter1.fighter_id,
                    fighter2_id=fighter2.fighter_id,
                    fighter1_name=f1_name,
                    fighter2_name=f2_name,
                    winner_id=winner.fighter_id,
                    method="SPLIT" if "SPLIT" in method else method[:3] if len(method) >= 3 else method,
                    is_title_fight=is_title_fight,
                    is_main_event=fight.get("is_main_event", False),
                    round_ended=round_finished,
                    total_rounds=fight.get("total_rounds", 3),
                    was_close="SPLIT" in method or "MAJ" in method,
                    was_controversial=bool(scorecard_data and scorecard_data.get("is_controversial")),
                )
                rsys    = get_rivalry_system()
                rivalry = rsys.process_fight(ctx)
                if rivalry:
                    heat_score = rivalry.score
                    stage      = get_heat_stage(heat_score)
                    result["rivalry"] = {
                        "score":      heat_score,
                        "stage":      stage.value,
                        "desc":       get_heat_description(heat_score),
                        "fights":     rivalry.fights,
                        "intensity":  rivalry.intensity.name.title(),
                    }
                    # News item if above TENSION and involves player
                    player_ids = []
                    if self._game_state:
                        player_ids = [f.fighter_id for f in self._game_state.get_player_fighters()]
                    if (fighter1.fighter_id in player_ids or fighter2.fighter_id in player_ids) \
                            and heat_score >= 30:
                        self._news_items.insert(0, {
                            "headline":  f"🔥 Rivalry forming: {f1_name} vs {f2_name} "
                                         f"(Heat: {heat_score}/100)",
                            "category": "rivalry",
                            "week":      self._game_state.week_number if self._game_state else 1,
                        })
            except Exception as exc:
                print(f"⚠️ Rivalry detection failed: {exc}")

        # ── Streak and record milestones ─────────────────────────────
        if self._game_state:
            self._fire_streak_news(winner, fight.get("week", self._game_state.week_number))
            self._fire_record_news(winner, fight.get("week", self._game_state.week_number))

        # ── Upset detection ───────────────────────────────────────────
        if self._game_state:
            try:
                w_rank = self._get_fighter_rank(winner)
                l_rank = self._get_fighter_rank(loser)
                # Upset: winner was ranked significantly lower (or unranked) vs a top fighter
                is_upset = False
                if w_rank is None and l_rank is not None and l_rank <= 5:
                    is_upset = True  # Unranked beats top-5
                elif w_rank and l_rank and w_rank > l_rank + 5:
                    is_upset = True  # Ranked 6+ spots below beats opponent
                if is_upset:
                    w_label = f"#{w_rank}" if w_rank else "unranked"
                    l_label = f"#{l_rank}" if l_rank else "unranked"
                    self._news_items.insert(0, {
                        "headline": f"😱 UPSET! {winner.name} ({w_label}) defeats "
                                    f"{loser.name} ({l_label}) via {method}!",
                        "category": "upset",
                        "week":     self._game_state.week_number,
                        "icon":     "😱",
                    })
            except Exception:
                pass

        # ── Update camp record ────────────────────────────────────────
        self._apply_post_fight_camp_record(winner, loser, fight, method)

        # Post-fight experience feedback — score-based fallback path
        # has no eng_result (no per-round stats produced), so this is
        # a no-op gated on eng_result. Kept here for forward compat —
        # if the score path ever wires through stats, the helper call
        # is ready. Real-engine path fires the same logic in
        # _run_real_engine after its own camp-record call.
        eng_result = None
        if eng_result is not None:
            for fid, opp_id, did_win in [
                (winner.fighter_id, loser.fighter_id, True),
                (loser.fighter_id,  winner.fighter_id, False),
            ]:
                try:
                    _my  = eng_result.fighter1_stats if fid == fighter1.fighter_id else eng_result.fighter2_stats
                    _opp = eng_result.fighter2_stats if fid == fighter1.fighter_id else eng_result.fighter1_stats
                    self._apply_post_fight_experience(
                        fighter_id=fid, opponent_id=opp_id,
                        my_stats=_my or [], opp_stats=_opp or [],
                        method=method, won=did_win,
                        total_rounds=getattr(eng_result, "total_rounds", 3),
                    )
                except Exception as _xe:
                    print(f"  ⚠️  [EXPERIENCE] Failed for {fid}: {_xe}")

        # ── Popularity update ────────────────────────────────────────
        if POPULARITY_AVAILABLE:
            try:
                for ftr, won in [(winner, True), (loser, False)]:
                    streak = 0
                    for h in reversed(getattr(ftr, 'fight_history', [])):
                        if (h.get('result') if isinstance(h, dict) else '') == ('W' if won else 'L'):
                            streak += 1
                        else:
                            break
                    delta = calculate_popularity_change(
                        won=won,
                        method=method,
                        was_title_fight=is_title_fight,
                        win_streak=streak if won else 0,
                        loss_streak=streak if not won else 0,
                        current_popularity=getattr(ftr, 'popularity', 10),
                    )
                    ftr.popularity = max(0, min(100, getattr(ftr, 'popularity', 10) + delta))
            except Exception:
                pass

        # ── Fight history ─────────────────────────────────────────
        # Write to both fighters' records so profiles/streaks stay current
        winner_history_entry = {
            "opponent_name":  loser.name,
            "opponent_id":    loser.fighter_id,
            "result":         "W",
            "method":         method,
            "round_finished": round_finished,
            "event_name":     fight.get("event_name", ""),
            "fight_id":       fight.get("fight_id", ""),
            "week":           self._game_state.week_number if self._game_state else 1,
        }
        loser_history_entry = {
            "opponent_name":  winner.name,
            "opponent_id":    winner.fighter_id,
            "result":         "L",
            "method":         method,
            "round_finished": round_finished,
            "event_name":     fight.get("event_name", ""),
            "fight_id":       fight.get("fight_id", ""),
            "week":           self._game_state.week_number if self._game_state else 1,
        }
        if not hasattr(winner, "fight_history"):
            winner.fight_history = []
        if not hasattr(loser, "fight_history"):
            loser.fight_history = []
        winner.fight_history.append(winner_history_entry)
        loser.fight_history.append(loser_history_entry)

        # Belt-and-suspenders: also store in game_state._fighter_data
        if self._game_state:
            for _fid, _entry in [(winner.fighter_id, winner_history_entry),
                                  (loser.fighter_id,  loser_history_entry)]:
                _fd = self._game_state._fighter_data
                if _fid not in _fd:
                    _fd[_fid] = {}
                _fd[_fid].setdefault('fight_history', []).append(_entry)

        # ── Update division rankings ──────────────────────────────
        self._update_rankings_after_fight(fight.get("weight_class", ""))

        # ── News headline ─────────────────────────────────────────
        if method in ("KO", "TKO"):
            headline = f"💥 {winner.name} stops {loser.name} in Round {round_finished}!"
        elif method == "SUB":
            headline = f"🔒 {winner.name} submits {loser.name}!"
        elif "SPLIT" in method:
            headline = f"📋 {winner.name} wins by split decision over {loser.name}"
        else:
            headline = f"📋 {winner.name} defeats {loser.name} by decision"

        self._news_items.insert(0, {
            "headline":  headline,
            "category": "fight",
            "week":      self._game_state.week_number if self._game_state else 1,
        })

        return result
    
    def _clear_cache(self):
        """Clear cached data after state changes"""
        self._fighter_cache.clear()
        self._camp_cache.clear()
    
    # =========================================================================
    # DATA ACCESS METHODS
    # =========================================================================
    

    # Roster caps by camp tier — scales with facility upgrades
    _ROSTER_CAPS = {
        "GARAGE":   3,
        "LOCAL":    6,
        "REGIONAL": 10,
        "NATIONAL": 15,
        "ELITE":    25,
    }

    def _roster_cap_for_tier(self, tier: str) -> int:
        return self._ROSTER_CAPS.get(tier.upper(), 3)

    def get_player_cap(self) -> int:
        """Return player's current roster cap based on facility tier."""
        camp = self.get_player_camp()
        tier = getattr(camp, 'tier', 'GARAGE') if camp else 'GARAGE'
        return self._roster_cap_for_tier(str(tier))

    def get_facility_info(self) -> Dict[str, Any]:
        """Return facility state and upgrade path for the UI."""
        camp = self.get_player_camp()
        tier = getattr(camp, 'tier', 'GARAGE') if camp else 'GARAGE'
        tier_up = str(tier).upper()

        TIER_NAMES = {
            "GARAGE":"Garage Gym","LOCAL":"Local Gym",
            "REGIONAL":"Regional Facility","NATIONAL":"National Center","ELITE":"Elite Complex",
        }
        TIER_ORDER = ["GARAGE","LOCAL","REGIONAL","NATIONAL","ELITE"]
        UPGRADE_COSTS_MAP = {"LOCAL":25000,"REGIONAL":100000,"NATIONAL":500000,"ELITE":2000000}
        # Bumped 2026-06-02 (F1): tighter win curve, top-tier still gated
        # on title accomplishments. REGIONAL=5 (was 10), NATIONAL=15 (was
        # 25), ELITE=30 (was 50). Title-win requirements unchanged.
        UPGRADE_REQS = {
            "LOCAL":    {"wins":3},
            "REGIONAL": {"wins":5},
            "NATIONAL": {"wins":15,"title_wins":1},
            "ELITE":    {"wins":30,"title_wins":3},
        }
        EFFICIENCY = {"GARAGE":1.0,"LOCAL":1.05,"REGIONAL":1.10,"NATIONAL":1.15,"ELITE":1.25}
        WEEKLY_COST = {"GARAGE":500,"LOCAL":1500,"REGIONAL":5000,"NATIONAL":15000,"ELITE":50000}

        idx = TIER_ORDER.index(tier_up) if tier_up in TIER_ORDER else 0
        next_tier = TIER_ORDER[idx + 1] if idx < len(TIER_ORDER) - 1 else None

        camp_wins   = getattr(camp, 'wins', 0) if camp else 0
        title_wins  = getattr(camp, 'championships', 0) if camp else 0

        info = {
            "tier":          tier_up,
            "tier_display":  TIER_NAMES.get(tier_up, tier_up),
            "stat_ceil":     self._TIER_SOFT_CEIL.get(tier_up, 65),
            "roster_cap":    self._roster_cap_for_tier(tier_up),
            "efficiency":    EFFICIENCY.get(tier_up, 1.0),
            "weekly_cost":   WEEKLY_COST.get(tier_up, 500),
            "balance":       self._camp_balance,
            "camp_wins":     camp_wins,
            "title_wins":    title_wins,
            "next_tier":     next_tier,
            "can_upgrade":   False,
        }

        if next_tier:
            cost  = UPGRADE_COSTS_MAP.get(next_tier, 0)
            reqs  = UPGRADE_REQS.get(next_tier, {})
            req_w = reqs.get("wins", 0)
            req_t = reqs.get("title_wins", 0)
            can   = self._camp_balance >= cost and camp_wins >= req_w and title_wins >= req_t

            info.update({
                "next_tier_display": TIER_NAMES.get(next_tier, next_tier),
                "upgrade_cost":      cost,
                "req_wins":          req_w,
                "req_title_wins":    req_t,
                "meets_wins":        camp_wins >= req_w,
                "meets_titles":      title_wins >= req_t,
                "can_afford":        self._camp_balance >= cost,
                "can_upgrade":       can,
                "next_stat_ceil":    self._TIER_SOFT_CEIL.get(next_tier, 100),
                "next_roster_cap":   self._roster_cap_for_tier(next_tier),
                "next_efficiency":   EFFICIENCY.get(next_tier, 1.0),
            })

        # Add equipment data
        try:
            eq_data = self.get_camp_equipment("player")
            info["equipment"] = eq_data
        except Exception:
            info["equipment"] = {}

        return info

    def upgrade_facility(self) -> Dict[str, Any]:
        """Upgrade player facility to next tier if requirements are met."""
        if not self._game_state:
            return {"success": False, "error": "No game loaded"}

        info = self.get_facility_info()
        if not info.get("next_tier"):
            return {"success": False, "error": "Already at maximum tier (Elite Complex)"}
        if not info.get("can_upgrade"):
            reasons = []
            if not info.get("can_afford"):
                reasons.append(f"Need ${info['upgrade_cost']:,} (have ${info['balance']:,})")
            if not info.get("meets_wins"):
                reasons.append(f"Need {info['req_wins']} wins (have {info['camp_wins']})")
            if not info.get("meets_titles") and info.get("req_title_wins", 0) > 0:
                reasons.append(f"Need {info['req_title_wins']} title wins")
            return {"success": False, "error": " · ".join(reasons)}

        cost      = info["upgrade_cost"]
        next_tier = info["next_tier"]

        self._camp_balance -= cost

        real_camp = self._game_state.get_camp(self._game_state.player_camp_id)
        if real_camp and hasattr(real_camp, 'tier'):
            real_camp.tier = next_tier

        self._clear_cache()

        self._news_items.insert(0, {
            "headline": (f"🏗️ {info['tier_display']} upgraded to "
                         f"{info['next_tier_display']}! "
                         f"Training ceiling now {info['next_stat_ceil']} · "
                         f"Roster cap: {info['next_roster_cap']}"),
            "category": "facility",
            "week":     self._game_state.week_number,
        })

        return {
            "success": True,
            "new_tier": next_tier,
            "new_tier_display": info["next_tier_display"],
            "cost": cost,
            "message": f"Upgraded to {info['next_tier_display']}!",
        }

    def get_camp_equipment(self, camp_id: str = "player") -> Dict[str, Any]:
        """Return current equipment for a camp with metadata."""
        _id = self._game_state.player_camp_id if camp_id == "player" and self._game_state else camp_id
        equipment = self._camp_equipment.get(_id, {})
        player_camp = self.get_player_camp()
        facility_tier = str(getattr(player_camp, 'tier', 'GARAGE')).upper() if player_camp else 'GARAGE'
        slots_total = self._EQUIPMENT_SLOTS.get(facility_tier, 2)
        slots_used  = len(equipment)
        slots_free  = max(0, slots_total - slots_used)
        allowed_eq_tiers = self._EQUIPMENT_TIER_GATES.get(facility_tier, ["BASIC"])

        result = {}
        for eq_type, meta in self._EQUIPMENT_TYPES.items():
            current_tier = equipment.get(eq_type)
            upgrades = []
            for eq_tier, tdata in self._EQUIPMENT_TIERS.items():
                if eq_tier not in allowed_eq_tiers:
                    continue
                if current_tier == eq_tier:
                    continue
                tier_order = ["BASIC","PRO","ELITE"]
                if current_tier and tier_order.index(eq_tier) <= tier_order.index(current_tier):
                    continue
                can_afford = self._camp_balance >= tdata["cost"]
                has_slot = slots_free > 0 or current_tier is not None
                upgrades.append({
                    "tier":       eq_tier,
                    "cost":       tdata["cost"],
                    "gain_bonus": tdata["gain_bonus"],
                    "decay_bonus":tdata["decay_bonus"],
                    "can_afford": can_afford,
                    "has_slot":   has_slot,
                    "can_buy":    can_afford and has_slot,
                })
            result[eq_type] = {
                **meta,
                "eq_type":     eq_type,
                "current_tier":current_tier,
                "upgrades":    upgrades,
            }

        return {
            "equipment":    result,
            "slots_total":  slots_total,
            "slots_used":   slots_used,
            "slots_free":   slots_free,
            "facility_tier":facility_tier,
            "allowed_tiers":allowed_eq_tiers,
        }

    def buy_equipment(self, eq_type: str, eq_tier: str) -> Dict[str, Any]:
        """Purchase or upgrade a piece of equipment."""
        if not self._game_state:
            return {"success": False, "error": "No game loaded"}
        if eq_type not in self._EQUIPMENT_TYPES:
            return {"success": False, "error": "Unknown equipment type"}
        if eq_tier not in self._EQUIPMENT_TIERS:
            return {"success": False, "error": "Unknown equipment tier"}

        player_camp = self.get_player_camp()
        facility_tier = str(getattr(player_camp, 'tier', 'GARAGE')).upper() if player_camp else 'GARAGE'
        allowed = self._EQUIPMENT_TIER_GATES.get(facility_tier, ["BASIC"])
        if eq_tier not in allowed:
            return {"success": False, "error": f"Upgrade your facility to purchase {eq_tier} equipment"}

        camp_id = self._game_state.player_camp_id
        equipment = self._camp_equipment.get(camp_id, {})

        slots_total = self._EQUIPMENT_SLOTS.get(facility_tier, 2)
        existing_tier = equipment.get(eq_type)
        if not existing_tier and len(equipment) >= slots_total:
            return {"success": False, "error": f"No equipment slots available. Upgrade your facility to unlock more slots."}

        tier_order = ["BASIC","PRO","ELITE"]
        if existing_tier and tier_order.index(eq_tier) <= tier_order.index(existing_tier):
            return {"success": False, "error": f"Already have {existing_tier} {eq_type.replace('_',' ')}"}

        cost = self._EQUIPMENT_TIERS[eq_tier]["cost"]
        if self._camp_balance < cost:
            return {"success": False, "error": f"Need ${cost:,}, have ${self._camp_balance:,}"}

        self._camp_balance -= cost
        if camp_id not in self._camp_equipment:
            self._camp_equipment[camp_id] = {}
        self._camp_equipment[camp_id][eq_type] = eq_tier

        eq_name = self._EQUIPMENT_TYPES[eq_type]["name"]
        self._news_items.insert(0, {
            "headline": f"🏗️ {eq_tier.title()} {eq_name} installed at your facility!",
            "category": "facility",
            "week":     self._game_state.week_number,
        })
        self._clear_cache()
        return {"success": True, "message": f"Purchased {eq_tier} {eq_name} for ${cost:,}"}

    def get_equipment_gain_bonus(self, camp_id: str, domain: str) -> float:
        """Return the gain multiplier from equipment for a given domain. 1.0 = no bonus."""
        equipment = self._camp_equipment.get(camp_id, {})
        best_bonus = 0.0
        for eq_type, meta in self._EQUIPMENT_TYPES.items():
            if meta["domain"] != domain:
                continue
            tier = equipment.get(eq_type)
            if tier:
                best_bonus = max(best_bonus, self._EQUIPMENT_TIERS[tier]["gain_bonus"])
        return 1.0 + best_bonus

    def get_equipment_decay_reduction(self, camp_id: str, domain: str) -> float:
        """Return decay reduction multiplier from equipment. 1.0 = no reduction."""
        equipment = self._camp_equipment.get(camp_id, {})
        best_bonus = 0.0
        for eq_type, meta in self._EQUIPMENT_TYPES.items():
            if meta["domain"] != domain:
                continue
            tier = equipment.get(eq_type)
            if tier:
                best_bonus = max(best_bonus, self._EQUIPMENT_TIERS[tier]["decay_bonus"])
        return 1.0 - best_bonus

    def get_player_camp(self) -> Optional[WebCamp]:
        """Get the player's camp"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return self._convert_mock_camp(self._mock_generator.get_player_camp())
            return None
        
        if not self._game_state:
            return None
            
        camp_id = self._game_state.player_camp_id
        return self.get_camp(camp_id)
    
    def get_player_fighters(self) -> List[WebFighter]:
        """Get all fighters in the player's camp"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return [self._convert_mock_fighter(f) 
                        for f in self._mock_generator.get_player_fighters()]
            return []
        
        if not self._game_state:
            return []
        
        # Use game_state's get_player_fighters directly
        fighter_records = self._game_state.get_player_fighters()
        return [self._convert_real_fighter(f) for f in fighter_records]
    
    def get_fighter(self, fighter_id: str) -> Optional[WebFighter]:
        """Get a fighter by ID. Falls through to amateur registry for
        unsigned amateurs (signed amateurs are in _game_state.fighters
        already, so the pro lookup catches them)."""
        if fighter_id in self._fighter_cache:
            return self._fighter_cache[fighter_id]

        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                f = self._mock_generator.get_fighter(fighter_id)
                if f:
                    web_f = self._convert_mock_fighter(f)
                    self._fighter_cache[fighter_id] = web_f
                    return web_f
            return None

        if not self._game_state:
            return None

        # Pro registry lookup (signed amateurs land here too — unified IDs)
        fighter = self._game_state.get_fighter(fighter_id)
        if fighter:
            web_f = self._convert_real_fighter(fighter)
            self._fighter_cache[fighter_id] = web_f
            return web_f

        # Fallback: amateur registry — unsigned amateurs aren't in the pro
        # fighters dict but should still resolve for profile rendering
        sys = self._get_amateur_system()
        if sys:
            amateur = sys.amateurs.get(fighter_id)
            if amateur:
                web_f = self._convert_amateur_fighter(amateur)
                self._fighter_cache[fighter_id] = web_f
                return web_f

        return None
    
    def get_camp(self, camp_id: str) -> Optional[WebCamp]:
        """Get a camp by ID"""
        if camp_id in self._camp_cache:
            return self._camp_cache[camp_id]
        
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                c = self._mock_generator.camps.get(camp_id)
                if c:
                    web_c = self._convert_mock_camp(c)
                    self._camp_cache[camp_id] = web_c
                    return web_c
            return None
        
        if not self._game_state:
            return None
        
        camp = self._game_state.get_camp(camp_id)
        if not camp:
            return None
        
        web_c = self._convert_real_camp(camp)
        self._camp_cache[camp_id] = web_c
        return web_c
    
    def get_all_camps(self) -> List[WebCamp]:
        """Get all camps"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return [self._convert_mock_camp(c) 
                        for c in self._mock_generator.camps.values()]
            return []
        
        if not self._game_state:
            return []
        
        return [self.get_camp(cid) for cid in self._game_state.camps.keys()
                if self.get_camp(cid)]
    
    def get_division_rankings(self, weight_class: str) -> List[WebFighter]:
        """Get ranked fighters in a division"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return [self._convert_mock_fighter(f) 
                        for f in self._mock_generator.get_division_rankings(weight_class)]
            return []
        
        if not self._game_state:
            return []
        
        division = self._game_state.divisions.get(weight_class)
        if not division:
            return []
        
        # Get champion first
        fighters = []
        if division.champion_id:
            champ = self.get_fighter(division.champion_id)
            if champ:
                fighters.append(champ)
        
        # Then ranked fighters
        for fid in division.rankings:
            f = self.get_fighter(fid)
            if f:
                fighters.append(f)
        
        return fighters
    
    def get_champion(self, weight_class: str) -> Optional[WebFighter]:
        """Get champion of a division"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                champ = self._mock_generator.get_champion(weight_class)
                return self._convert_mock_fighter(champ) if champ else None
            return None
        
        if not self._game_state:
            return None
        
        division = self._game_state.divisions.get(weight_class)
        if not division or not division.champion_id:
            return None
        
        return self.get_fighter(division.champion_id)
    
    def get_division_unranked(self, weight_class: str, limit: int = 15) -> List[WebFighter]:
        """Get active fighters in a division who are NOT in the ranked list."""
        if not self._game_state:
            return []
        division = self._game_state.divisions.get(weight_class)
        if not division:
            return []
        ranked_ids = set(division.rankings)
        champ_id   = division.champion_id or ""
        unranked = []
        for f in self._game_state.fighters.values():
            if (f.weight_class == weight_class
                    and f.is_active
                    and f.fighter_id not in ranked_ids
                    and f.fighter_id != champ_id):
                wf = self._convert_real_fighter(f)
                if wf:
                    unranked.append(wf)
        # Sort by overall rating descending so best unranked appear first
        unranked.sort(key=lambda x: x.overall_rating, reverse=True)
        return unranked[:limit]

    def get_fight_offers(self) -> List[WebFightOffer]:
        """Get all fight offers for player's fighters"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return [self._convert_mock_offer(o) 
                        for o in self._mock_generator.fight_offers]
            return []
        
        if not self._game_state:
            return []
        
        # Generate offers if we don't have any
        if not self._fight_offers:
            self._generate_fight_offers()
        
        # Convert to WebFightOffer format
        return [self._dict_to_web_offer(o) for o in self._fight_offers]
    
    def _generate_fight_offers(self) -> None:
        """
        Fight offers are no longer auto-generated — fights are booked directly
        through the Division Ladder challenge system. This method is kept as a
        no-op so existing call sites don't crash.
        """
        pass
    
    def _get_fighter_rank(self, fighter) -> Optional[int]:
        """Get a fighter's rank in their division"""
        if not self._game_state:
            return None
        
        division = self._game_state.divisions.get(fighter.weight_class)
        if not division:
            return None
        
        if division.champion_id == fighter.fighter_id:
            return 0  # Champion
        
        if fighter.fighter_id in division.rankings:
            return division.rankings.index(fighter.fighter_id) + 1
        
        return None
    
    def _dict_to_web_offer(self, offer: Dict) -> WebFightOffer:
        """Convert offer dict to WebFightOffer.
        WebFightOffer fields: offer_id, fighter_id, opponent_id, opponent_name,
        opponent_record, opponent_rating, opponent_rank, event_name, week,
        weeks_away, purse, win_bonus, is_title_fight, risk_level, reward_level,
        matchup_quality, accept_chance.
        """
        weeks_away = offer.get("weeks_away", 4)
        week       = offer.get("week",
                               (self._game_state.week_number if self._game_state else 1) + weeks_away)
        return WebFightOffer(
            offer_id=offer["offer_id"],
            fighter_id=offer["fighter_id"],
            opponent_id=offer["opponent_id"],
            opponent_name=offer["opponent_name"],
            opponent_record=offer["opponent_record"],
            opponent_rating=offer["opponent_rating"],
            opponent_rank=offer.get("opponent_rank"),
            event_name=offer["event_name"],
            week=week,
            weeks_away=weeks_away,
            purse=offer["purse"],
            win_bonus=offer["win_bonus"],
            is_title_fight=offer.get("is_title_fight", False),
            risk_level=offer.get("risk_level", 3),
            reward_level=offer.get("reward_level", 3),
            matchup_quality=offer.get("matchup_quality", "Fair"),
            accept_chance=offer.get("accept_chance", 75),
        )
    
    def get_news_feed(self, limit: int = 30) -> List[WebNewsItem]:
        """Get recent news items"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return [self._convert_mock_news(n) 
                        for n in self._mock_generator.news_feed[:limit]]
            return []
        
        # Convert internal news to WebNewsItem
        icons = {
            "fight":      "🥊",
            "signing":    "📝",
            "injury":     "🏥",
            "title":      "🏆",
            "streak":     "🔥",
            "record":     "📊",
            "training":   "💪",
            "decay":      "📉",
            "career":     "⏳",
            "retirement": "🥊",
            "facility":   "🏗️",
            "scouting":   "👀",
        }
        
        # Sort newest first by week, then by insertion order within same week
        sorted_items = sorted(
            self._news_items,
            key=lambda x: x.get("week", 0),
            reverse=True,
        )
        return [
            WebNewsItem(
                news_id=f"news_{i}",
                headline=n["headline"],
                category=n.get("category", "general"),
                week=n.get("week", 1),
                icon=icons.get(n.get("category", ""), "📰"),
            )
            for i, n in enumerate(sorted_items[:limit])
        ]
    
    def accept_fight_offer(self, offer_id: str) -> Dict[str, Any]:
        """Accept a fight offer and schedule the fight"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return self._mock_generator.accept_offer(offer_id)
            return {"success": False, "error": "No game loaded"}
        
        if not self._game_state:
            return {"success": False, "error": "No game loaded"}
        
        # Find the offer
        offer = next((o for o in self._fight_offers if o["offer_id"] == offer_id), None)
        if not offer:
            return {"success": False, "error": "Offer not found"}

        # Block if either fighter is injured
        if INJURY_AVAILABLE and self._injury_system:
            _pfid = offer.get("fighter_id", "")
            _ofid = offer.get("opponent_id", "")
            if _pfid and not self._injury_system.is_cleared_to_fight(_pfid):
                return {"success": False,
                        "error": f"{offer.get('fighter_name','Your fighter')} "
                                 f"is injured and cannot fight."}
            if _ofid and not self._injury_system.is_cleared_to_fight(_ofid):
                return {"success": False,
                        "error": f"{offer.get('opponent_name','Opponent')} "
                                 f"is injured and unavailable."}

        # Schedule the fight
        fight = {
            "fight_id": f"fight_{offer['fighter_id']}_{offer['opponent_id']}",
            "fighter1_id": offer["fighter_id"],
            "fighter1_name": offer["fighter_name"],
            "fighter2_id": offer["opponent_id"],
            "fighter2_name": offer["opponent_name"],
            "weight_class": offer["weight_class"],
            "week": self._game_state.week_number + offer["weeks_away"],
            "weeks_until": offer["weeks_away"],
            "event_name": offer["event_name"],
            "purse": offer["purse"],
            "win_bonus": offer["win_bonus"],
            "is_title_fight": offer.get("is_title_fight", False),
            "is_player_fight": True,
        }

        self._scheduled_fights.append(fight)
        
        # Remove the accepted offer and any other offers for this fighter
        self._fight_offers = [o for o in self._fight_offers if o["fighter_id"] != offer["fighter_id"]]
        
        # Add news
        self._news_items.insert(0, {
            "headline": f"📝 SIGNED: {offer['fighter_name']} vs {offer['opponent_name']}",
            "category": "signing",
            "week": self._game_state.week_number,
        })
        
        return {
            "success": True,
            "message": f"Fight scheduled: {offer['fighter_name']} vs {offer['opponent_name']}",
            "fight_id": fight["fight_id"],
        }
    
    def decline_fight_offer(self, offer_id: str) -> Dict[str, Any]:
        """Decline a fight offer"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return self._mock_generator.decline_offer(offer_id)
            return {"success": False, "error": "No game loaded"}

        # Find the offer before removing — need source for vacant-title fallback
        _declined = next((o for o in self._fight_offers
                          if o["offer_id"] == offer_id), None)

        # Remove the offer
        self._fight_offers = [o for o in self._fight_offers if o["offer_id"] != offer_id]

        # Vacant-title decline → AI #1 vs #2 fallback (Slice 2.5, sub-ship B)
        if _declined and _declined.get("source") == "vacant_title":
            _wc = _declined.get("vacant_division")
            if _wc:
                self._book_title_fight(_wc, decline_context="player declined the shot")

        return {"success": True, "message": "Offer declined"}

    def _preview_vacant_title_contenders(
        self,
        wc: str,
        exclude_fighter_ids: Optional[Set[str]] = None,
        min_contenders: int = 2,
        require_open_slot: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Slice 3 — read-only preview of who'd fight for a vacant title in {wc}.
        Returns dict with top1, top2 (may be None if min_contenders=1),
        target_event_name, target_week, weeks_away, or None if booking
        not possible. Idempotent — safe from a route render handler.

        Sub-ship B parameterization:
        - min_contenders: 1 if caller only needs an opponent (mandatory return
          defense) else 2 (vacant title needs top1 + top2). Default 2.
        - require_open_slot: when False, contender selection runs but the
          next-open-main-event scan is skipped (target_event_name/target_week
          come back as None). Lead-time-aware callers compute target_week
          themselves via _weeks_out_for_fight."""
        if not self._game_state:
            return None
        div = self._game_state.divisions.get(wc)
        if not div:
            return None
        exclude = set(exclude_fighter_ids or [])

        current_week = self._game_state.week_number
        _player_camp_id = self._game_state.player_camp_id

        _all_booked = set()
        for sf in self._scheduled_fights:
            _all_booked.add(sf.get("fighter1_id", ""))
            _all_booked.add(sf.get("fighter2_id", ""))
        for _wk_b, _card_b in self._upcoming_cards.items():
            for _f_b in _card_b.get("fights", []):
                _all_booked.add(_f_b.get("fighter1_id", ""))
                _all_booked.add(_f_b.get("fighter2_id", ""))
        # Sub-ship B: include queue entries to prevent double-pairing across
        # helper-origin and booker-origin bookings on the same fighters.
        for q_fight in self._ai_deferred_bookings:
            _all_booked.add(q_fight.get("fighter1_id", ""))
            _all_booked.add(q_fight.get("fighter2_id", ""))

        _contenders = []
        for _fid in div.rankings[:8]:
            _ftr = self._game_state.get_fighter(_fid)
            if not _ftr or not _ftr.is_active:
                continue
            if _ftr.fighter_id in exclude:
                continue
            if _player_camp_id and _ftr.camp_id == _player_camp_id:
                continue
            if _ftr.fighter_id in _all_booked:
                continue
            if INJURY_AVAILABLE and self._injury_system \
                    and not self._injury_system.is_cleared_to_fight(_ftr.fighter_id):
                continue
            _contenders.append(_ftr)
            if len(_contenders) >= 2:
                break

        if len(_contenders) < min_contenders:
            return None

        # Slot scan is optional — lead-time-aware callers compute target_week
        # themselves from _weeks_out_for_fight and don't need preview's scan.
        _target_card = None
        if require_open_slot:
            for _wk_s in sorted(self._upcoming_cards.keys()):
                if _wk_s <= current_week:
                    continue
                _card_s = self._upcoming_cards[_wk_s]
                _has_main = any(
                    _f_s.get("card_slot") == "main_event"
                    for _f_s in _card_s.get("fights", [])
                )
                if not _has_main:
                    _target_card = _card_s
                    break
            if not _target_card:
                return None

        return {
            "top1":              _contenders[0],
            "top2":              _contenders[1] if len(_contenders) > 1 else None,
            "target_event_name": _target_card["event_name"] if _target_card else None,
            "target_week":       _target_card["week"] if _target_card else None,
            "weeks_away":        (_target_card["week"] - current_week) if _target_card else None,
        }

    def _book_title_fight(
        self,
        wc: str,
        fixed_fighter: Optional["WebFighter"] = None,
        exclude_ids: Optional[Set[str]] = None,
        apply_lead_time: bool = True,
        decline_context: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Sub-ship B (Ship #21) — unified title-fight booking helper.

        Replaces _book_vacant_title_fight (vacant title via top1+top2),
        _book_mandatory_return_defense (champion vs top1), and
        _book_vacant_title_ai_fallback (decline-fallback wrapper). All four
        slice helper sites (Slice 0.75/2 auto-vacate, Slice 4 mandatory return,
        Slice 2.5 decline fallback, Slice 3 player vacate) route through here.

        When apply_lead_time=True (default), routes via Ship #20's
        _ai_deferred_bookings queue when target_week is outside the rolling
        8-week pipeline window, or direct-writes when in window with an open
        main_event slot. When False, falls back to next-open-slot direct-write
        via preview's slot scan (override path; not used by current sites,
        kept for future flexibility).

        Args:
            wc: weight class
            fixed_fighter: champion (mandatory return mode) or None (vacant)
            exclude_ids: extra fighters to exclude from contender pool
            apply_lead_time: if True, route via _weeks_out_for_fight + queue;
                             if False, use preview's next-open-slot direct-write
            decline_context: narrative suffix for news/log (Slice 2.5 decline)

        Returns: booked fight info dict on success, None on deferral.
        """
        if not self._game_state:
            return None

        _exclude = set(exclude_ids or [])
        if fixed_fighter is not None:
            _exclude.add(fixed_fighter.fighter_id)

        _is_mandatory = fixed_fighter is not None
        _min_contenders = 1 if _is_mandatory else 2

        # Lead-time path doesn't need preview's open-slot scan — we compute
        # target_week ourselves. Override path needs the slot scan.
        preview = self._preview_vacant_title_contenders(
            wc, _exclude,
            min_contenders=_min_contenders,
            require_open_slot=not apply_lead_time,
        )
        if not preview:
            _label = "MANDATORY DEFENSE" if _is_mandatory else "VACANT TITLE"
            _who = f" for {fixed_fighter.name}" if _is_mandatory else ""
            print(f"  ⚠️ [{_label}] {wc} — no bookable contender{_who}; deferred")
            return None

        # Pair selection
        if _is_mandatory:
            f1 = fixed_fighter
            f2 = preview["top1"]
        else:
            f1 = preview["top1"]
            f2 = preview["top2"]

        current = self._game_state.week_number

        # target_week: lead-time computation vs preview's slot scan
        if apply_lead_time:
            if _is_mandatory:
                # Champion is rank 0 sentinel; opponent uses real rank
                _r1, _r2 = 0, self._get_fighter_rank(f2)
            else:
                # Vacant title: both contenders use real ranks
                _r1 = self._get_fighter_rank(f1)
                _r2 = self._get_fighter_rank(f2)
            _wks_out = self._weeks_out_for_fight(_r1, _r2)
            target_week = current + _wks_out
            event_name = self._dfc_label(target_week)
        else:
            target_week = preview["target_week"]
            event_name = preview["target_event_name"]

        # Build the fight dict (same shape as booker-origin queue entries)
        fdict = self._make_scheduled_fight(
            f1, f2, wc, event_name, target_week, "main_event", is_title=True,
        )

        # Routing: direct-write to in-window card with open main_event slot,
        # else queue for Phase 2 hand-off (lead-time path) or fail (override).
        in_window = (current + 1 <= target_week
                     <= current + PIPELINE_WINDOW_WEEKS)
        target_card = self._upcoming_cards.get(target_week) if in_window else None
        has_open_main = target_card is not None and not any(
            _f.get("card_slot") == "main_event"
            for _f in target_card.get("fights", [])
        )

        if in_window and has_open_main:
            target_card["fights"].append(fdict)
            _routed = "BOOKED"
        elif apply_lead_time:
            # Out of window OR slot taken — queue for Phase 2 hand-off.
            # Phase 1 cancellation re-eval (broken pair) and Phase 2 capacity
            # gate apply equally to helper-origin entries; no special handling.
            self._ai_deferred_bookings.append(fdict)
            _routed = "QUEUED"
        else:
            # Override path with no open slot found (defensive — preview would
            # have returned None already, but guard against future drift)
            return None

        # Terminal log + news headline
        _label = "MANDATORY DEFENSE" if _is_mandatory else "VACANT TITLE"
        _emoji = "🏆" if _routed == "BOOKED" else "📅"
        _suffix = f" ({decline_context})" if decline_context else ""
        _wks_away = target_week - current
        print(f"  {_emoji} [{_label} {_routed}] {wc} — {f1.name} vs {f2.name} "
              f"at {event_name} (Wk {target_week}, +{_wks_away}w){_suffix}")

        if _is_mandatory:
            _headline = (f"🏆 {f1.name} returns to action — {wc} title defense "
                         f"booked vs {f2.name} at {event_name}")
        else:
            _headline_suffix = f" ({decline_context})." if decline_context else "."
            _headline = (f"🏆 VACANT TITLE FIGHT: {f1.name} vs {f2.name} "
                         f"for the {wc} belt at {event_name}{_headline_suffix}")
        self._news_items.insert(0, {
            "headline": _headline,
            "category": "title",
            "week":     current,
        })

        return {
            "f1_name":      f1.name,
            "f2_name":      f2.name,
            "target_event": event_name,
            "target_week":  target_week,
            "fight_id":     fdict.get("fight_id"),
            "routed":       _routed,
        }

    def _maybe_queue_champion_injury_decision(self, ftr, injury) -> None:
        """Slice 3 — queue a vacate-or-hold decision when a player champion
        takes a Severe (9-24w) injury. Career-level (>=25w) skips this and
        falls through to Slice 0.75's auto-vacate. Idempotent — won't
        double-queue the same fighter."""
        if not (self._game_state and ftr and getattr(ftr, 'is_champion', False)):
            return
        if ftr.camp_id != self._game_state.player_camp_id:
            return
        _weeks = getattr(injury, 'recovery_weeks', 0) or 0
        if not (9 <= _weeks <= 24):
            return
        if any(d.get("fighter_id") == ftr.fighter_id
               for d in self._pending_injury_decisions):
            return
        _wk = self._game_state.week_number
        self._pending_injury_decisions.append({
            "fighter_id":     ftr.fighter_id,
            "weight_class":   getattr(ftr, 'weight_class', ''),
            "injury_desc":    getattr(injury, 'description', 'injury'),
            "recovery_weeks": _weeks,
            "queued_at_week": _wk,
            "return_week":    _wk + _weeks,
        })
        print(f"  ⚠️ [INJURY DECISION QUEUED] {ftr.name} ({ftr.weight_class}) — "
              f"{_weeks}w injury. advance_week blocked until decision.")

    def resolve_champion_injury_decision(
        self, fighter_id: str, choice: str,
    ) -> Dict[str, Any]:
        """Slice 3 — player picks vacate or hold for an injured champion.
        choice: 'vacate' or 'hold'. Removes the pending decision and fires
        the appropriate machinery."""
        if choice not in ("vacate", "hold"):
            return {"success": False, "error": "Invalid choice"}

        decision = next((d for d in self._pending_injury_decisions
                         if d.get("fighter_id") == fighter_id), None)
        if not decision:
            return {"success": False, "error": "No pending decision for this fighter"}

        ftr = self._game_state.get_fighter(fighter_id) if self._game_state else None
        if not ftr:
            return {"success": False, "error": "Fighter not found"}
        wc = decision["weight_class"]

        if choice == "vacate":
            div = self._game_state.divisions.get(wc)
            if div and div.champion_id == fighter_id:
                ftr.is_champion = False
                div.champion_id = None
                div.champion_name = None
                history = self._title_history.get(wc, [])
                if history and history[-1].get("is_active"):
                    history[-1]["is_active"]   = False
                    history[-1]["lost_week"]   = self._game_state.week_number
                    history[-1]["lost_event"]  = "Vacated (player choice)"
                    history[-1]["lost_to_name"] = "Vacated"
                    history[-1]["lost_method"] = "Injury (vacated)"
                self._news_items.insert(0, {
                    "headline": (f"👑 TITLE VACATED: {ftr.name} relinquishes "
                                 f"the {wc} belt during recovery."),
                    "category": "title",
                    "week":     self._game_state.week_number,
                })
            self._book_title_fight(
                wc, exclude_ids={fighter_id},
            )
        elif choice == "hold":
            self._champion_holds[fighter_id] = {
                "fighter_id":   fighter_id,
                "weight_class": wc,
                "start_week":   self._game_state.week_number,
                "return_week":  decision["return_week"],
                "injury_desc":  decision["injury_desc"],
            }
            self._news_items.insert(0, {
                "headline": (f"🏆 {ftr.name} holds the {wc} belt during recovery — "
                             f"return Week {decision['return_week']}."),
                "category": "title",
                "week":     self._game_state.week_number,
            })

        self._pending_injury_decisions = [
            d for d in self._pending_injury_decisions
            if d.get("fighter_id") != fighter_id
        ]
        return {"success": True, "choice": choice, "fighter_name": ftr.name}

    def get_scheduled_fights(self) -> List[Dict[str, Any]]:
        """Get all scheduled fights for player's fighters"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return self._mock_generator.get_player_scheduled_fights()
            return []
        
        return self._scheduled_fights
    
    # get_upcoming_events — real implementation below at card pipeline section
    
    def get_completed_events(self) -> List[Dict[str, Any]]:
        """Get completed events"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return self._mock_generator.completed_events
            return []
        
        return self._completed_events
    
    # =========================================================================
    # CONVERSION METHODS (Mock Data)
    # =========================================================================
    
    def _convert_mock_fighter(self, f) -> WebFighter:
        """Convert mock Fighter to WebFighter"""
        return WebFighter(
            fighter_id=f.fighter_id,
            name=f.name,
            nickname=f.nickname,
            age=f.age,
            country=f.country,
            weight_class=f.weight_class,
            division_abbrev=DIVISION_ABBREV.get(f.weight_class, "??"),
            fighting_style=f.fighting_style,
            wins=f.wins,
            losses=f.losses,
            draws=getattr(f, 'draws', 0),
            ko_wins=f.ko_wins,
            sub_wins=f.sub_wins,
            ko_losses=getattr(f, 'ko_losses', 0) or 0,
            ko_losses_received=int(fdata.get('ko_losses_received', 0)),
            chin_perm_erosion=float(fdata.get('chin_permanent_erosion', 0.0)),
            sub_losses=getattr(f, 'sub_losses', 0) or 0,
            career_fotn_awards=getattr(f, 'career_fotn_awards', 0) or 0,
            record_str=f.record_str,
            overall_rating=f.overall_rating,
            potential=f.potential,
            popularity=f.popularity,
            ranking=f.ranking,
            is_champion=f.is_champion,
            is_active=f.is_active,
            camp_id=f.camp_id,
            camp_name=f.camp_name,
            height=f.height,
            reach=f.reach,
            strength=f.strength,
            speed=f.speed,
            cardio=f.cardio,
            chin=f.chin,
            recovery=f.recovery,
            boxing=f.boxing,
            kicks=f.kicks,
            clinch_striking=f.clinch_striking,
            striking_defense=f.striking_defense,
            takedowns=f.takedowns,
            takedown_defense=f.takedown_defense,
            top_control=f.top_control,
            submissions=f.submissions,
            guard=f.guard,
            heart=f.heart,
            fight_iq=f.fight_iq,
            composure=f.composure,
            fatigue=f.fatigue,
            morale=f.morale,
            condition_status=f.condition_status,
            condition_color=f.condition_color,
            win_streak=f.win_streak,
            lose_streak=f.lose_streak,
            traits=f.traits,
            fight_history=f.fight_history
        )
    
    def _convert_mock_camp(self, c) -> WebCamp:
        """Convert mock Camp to WebCamp"""
        return WebCamp(
            camp_id=c.camp_id,
            name=c.name,
            tier=c.tier,
            location=c.location,
            reputation=c.reputation,
            balance=c.balance,
            is_player=c.is_player,
            max_fighters=c.max_fighters,
            fighter_ids=c.fighter_ids,
            wins=c.wins,
            losses=c.losses,
            record_str=c.record_str,
            win_percentage=c.win_percentage,
            championships=c.championships,
            head_coach_name=c.head_coach_name,
            head_coach_specialty=c.head_coach_specialty,
            head_coach_rating=c.head_coach_rating
        )
    
    def _convert_mock_offer(self, o) -> WebFightOffer:
        """Convert mock FightOffer to WebFightOffer"""
        return WebFightOffer(
            offer_id=o.offer_id,
            fighter_id=o.fighter_id,
            opponent_id=o.opponent_id,
            opponent_name=o.opponent_name,
            opponent_record=o.opponent_record,
            opponent_rating=o.opponent_rating,
            opponent_rank=o.opponent_rank,
            event_name=o.event_name,
            week=o.week,
            weeks_away=o.weeks_away,
            purse=o.purse,
            win_bonus=o.win_bonus,
            is_title_fight=o.is_title_fight,
            risk_level=o.risk_level,
            reward_level=o.reward_level,
            matchup_quality=o.matchup_quality,
            accept_chance=o.accept_chance
        )
    
    def _convert_mock_news(self, n) -> WebNewsItem:
        """Convert mock NewsItem to WebNewsItem"""
        return WebNewsItem(
            news_id=n.news_id,
            headline=n.headline,
            category=n.category,
            week=n.week,
            icon=n.icon
        )
    
    # =========================================================================
    # CONVERSION METHODS (Real Game Data)
    # =========================================================================

    def _convert_real_camp(self, camp) -> WebCamp:
        """Convert real CampRecord to WebCamp"""
        # CampRecord is a lightweight dataclass, not the full Camp object
        # Get fighter_ids from game_state if available
        fighter_ids = []
        if self._game_state:
            camp_fighters = self._game_state.get_camp_fighters(camp.camp_id)
            fighter_ids = [f.fighter_id for f in camp_fighters]
        
        # Count live champions from division state — titles_held on CampRecord
        # is never updated so we derive it directly from authoritative source.
        live_championships = 0
        if self._game_state:
            for division in self._game_state.divisions.values():
                if division.champion_id:
                    champ = self._game_state.fighters.get(division.champion_id)
                    if champ and champ.camp_id == camp.camp_id:
                        live_championships += 1

        tier_str  = camp.tier if isinstance(camp.tier, str) else str(camp.tier)

        return WebCamp(
            camp_id=camp.camp_id,
            name=camp.name,
            tier=tier_str,
            location=self._camp_location if camp.is_player else (camp.location_str if hasattr(camp, 'location_str') else f"{camp.city}, {camp.country}" if getattr(camp, 'city', None) else "Unknown"),
            reputation=camp.reputation,
            balance=self._camp_balance if camp.is_player else getattr(camp, 'balance', 0),
            is_player=camp.is_player,
            max_fighters=self._roster_cap_for_tier(tier_str),
            fighter_ids=fighter_ids,
            wins=self._player_camp_wins if camp.is_player else camp.total_wins,
            losses=self._player_camp_losses if camp.is_player else camp.total_losses,
            record_str=f"{self._player_camp_wins}-{self._player_camp_losses}" if camp.is_player else f"{camp.total_wins}-{camp.total_losses}",
            win_percentage=int(camp.total_wins / max(1, camp.total_wins + camp.total_losses) * 100),
            championships=live_championships,
            head_coach_name="Head Coach",
            head_coach_specialty="MMA",
            head_coach_rating=50
        )
    
    def _convert_amateur_fighter(self, amateur) -> WebFighter:
        """
        Convert an AmateurFighter (amateur_system.amateurs registry) to a
        WebFighter for profile rendering. Amateurs are stub-rendered:
        full identity + attributes + style, but no camp, no pro ranking,
        no fight history. The existing fighter_profile template handles
        the empty fields via its defensive `if X` guards.
        """
        wc_str = amateur.weight_class if isinstance(amateur.weight_class, str) else str(amateur.weight_class)
        attrs = getattr(amateur, 'attributes', {}) or {}

        def _a(key: str, default: int = 50) -> int:
            return int(attrs.get(key, default))

        # Pro record 0-0 for unsigned amateurs (consistent with sign-time
        # behavior in sign_amateur — amateur W/L lives on the credential
        # line on profile, never on the big pro record).
        wins   = 0
        losses = 0

        return WebFighter(
            fighter_id=amateur.fighter_id,
            name=amateur.name,
            nickname=None,
            age=getattr(amateur, 'age', 22),
            country=getattr(amateur, 'nationality', ''),
            weight_class=wc_str,
            division_abbrev=DIVISION_ABBREV.get(wc_str, "??"),
            fighting_style=getattr(amateur, 'fighting_style', 'Balanced'),
            wins=wins,
            losses=losses,
            draws=0,
            ko_wins=0,
            sub_wins=0,
            record_str=f"{wins}-{losses}",
            overall_rating=int(getattr(amateur, 'overall_rating', 60)),
            potential=int(getattr(amateur, 'potential_ceiling', 75)),
            popularity=5,
            ranking=None,
            is_champion=False,
            is_active=getattr(amateur, 'is_active', True),
            height=getattr(amateur, 'height', '') or '',
            reach=getattr(amateur, 'reach', '') or '',
            strength=_a('strength'),
            speed=_a('speed'),
            cardio=_a('cardio'),
            chin=_a('chin'),
            recovery=_a('recovery'),
            boxing=_a('boxing'),
            kicks=_a('kicks'),
            clinch_striking=_a('clinch_striking'),
            striking_defense=_a('striking_defense'),
            takedowns=_a('takedowns'),
            takedown_defense=_a('takedown_defense'),
            top_control=_a('top_control'),
            submissions=_a('submissions'),
            guard=_a('guard'),
            heart=_a('heart'),
            fight_iq=_a('fight_iq'),
            composure=_a('composure'),
            fatigue=0,
            morale=75,
            condition_status="Fresh",
            condition_color="var(--neon-green)",
            win_streak=0,
            lose_streak=0,
            traits=list(getattr(amateur, 'traits', []) or []),
            fight_history=[],
        )

    def _convert_real_fighter(self, fighter) -> WebFighter:
        """
        Convert a FighterRecord (game_state registry) to WebFighter.

        FighterRecord is a lightweight reference — it has overall_rating but
        no per-attribute breakdown.  We pull richer data from _fighter_data if
        it was stored there; otherwise we generate realistic per-attribute
        variance from the overall so profiles look like distinct fighters rather
        than 17×same-number.
        """
        import random as _rnd

        history  = getattr(fighter, 'fight_history', []) or []
        # Fallback: read from _fighter_data if the fighter object has no history
        # (covers edge case where player fighter ID mismatch means append went nowhere)
        if not history and self._game_state:
            history = self._game_state._fighter_data.get(
                fighter.fighter_id, {}).get('fight_history', [])
        wc_str   = fighter.weight_class if isinstance(fighter.weight_class, str) else str(fighter.weight_class)

        # ── Streaks ───────────────────────────────────────────────
        win_streak = lose_streak = 0
        for f in reversed(history):
            res = f.get('result') if isinstance(f, dict) else getattr(f, 'result', '')
            if win_streak == 0 and lose_streak == 0:
                if res == 'W':
                    win_streak += 1
                elif res == 'L':
                    lose_streak += 1
                else:
                    break
            elif win_streak > 0:
                if res == 'W':
                    win_streak += 1
                else:
                    break
            elif lose_streak > 0:
                if res == 'L':
                    lose_streak += 1
                else:
                    break

        # ── Camp name ─────────────────────────────────────────────
        camp_name = "Free Agent"
        if fighter.camp_id and self._game_state:
            camp = self._game_state.get_camp(fighter.camp_id)
            if camp:
                camp_name = camp.name

        # ── Division ranking ──────────────────────────────────────
        ranking = None
        if self._game_state and wc_str:
            division = self._game_state.divisions.get(wc_str)
            if division:
                if division.champion_id == fighter.fighter_id:
                    ranking = 0
                elif fighter.fighter_id in division.rankings:
                    ranking = division.rankings.index(fighter.fighter_id) + 1

        # ── Per-attribute values ──────────────────────────────────
        # Prefer stored _fighter_data; fall back to seeded randomised variance.
        # The seed is fixed per fighter so attributes stay stable across calls.
        ovr  = fighter.overall_rating
        fdata = {}
        if self._game_state and fighter.fighter_id in self._game_state._fighter_data:
            fdata = self._game_state._fighter_data[fighter.fighter_id]
        elif self._game_state:
            # Fighter exists but has no _fighter_data — backfill from world gen data
            # Read style directly from FighterRecord if available
            real_style = getattr(fighter, 'fighting_style', None)
            if not real_style or real_style == 'Balanced':
                # Only fall back to random if truly unset
                import random as _rs
                _rs.seed(hash(fighter.fighter_id) & 0xFFFFFFFF)
                real_style = _rs.choices(
                    ["Striker","Counter Striker","Pressure Fighter","Muay Thai",
                     "Wrestler","Ground & Pound","BJJ Specialist",
                     "Sprawl & Brawl","Point Fighter","Clinch Fighter","Balanced"],
                    weights=[14,8,10,9,12,9,10,8,6,7,7], k=1
                )[0]
            fdata = {
                "style":       real_style,
                "age":         getattr(fighter, 'age', 26),
                "country":     getattr(fighter, 'country', 'USA'),
                "potential":   fighter.overall_rating + 8,
            }
            # Cache it so we don't regenerate next call
            self._game_state._fighter_data[fighter.fighter_id] = fdata

        def _attr(key: str, default_offset: int = 0) -> int:
            if key in fdata:
                return int(fdata[key])
            # Seeded variance: ±12 around overall, clamped 20–100.
            # Ship #32: replaced Python's hash() (process-randomized via
            # PYTHONHASHSEED) with hashlib.md5 for cross-process stability.
            # Defense-in-depth — sim-history fighters have attributes in
            # fdata after Ship #32, but player-created fighters and
            # free-agent edge cases still hit this fallback path.
            import hashlib as _hl
            _seed = int.from_bytes(
                _hl.md5((fighter.fighter_id + key).encode('utf-8')).digest()[:4],
                'big',
            )
            rng = _rnd.Random(_seed)
            return max(20, min(100, ovr + default_offset + rng.randint(-12, 12)))

        # Fighter identity pulled from stored data or sensible defaults
        age            = int(fdata.get("age", 26))
        country        = str(fdata.get("country", "USA"))
        _raw_style     = str(fdata.get("style", fdata.get("fighting_style", "Balanced")))
        # Translate legacy martial art names to display names
        _STYLE_XLAT = {
            "Karate":            "Point Fighter",
            "MMA Hybrid":        "Balanced",
            "Boxing":            "Striker",
            "Orthodox Boxer":    "Striker",
            "Kickboxer":         "Striker",
            "Kickboxing":        "Striker",
            "Judo":              "Wrestler",
            "Sambo":             "Wrestler",
            "Brawler":           "Pressure Fighter",
            "Submission Artist": "BJJ Specialist",
            "Submissions":       "BJJ Specialist",
            "Grappling":         "Wrestler",
        }
        fighting_style = _STYLE_XLAT.get(_raw_style, _raw_style)
        nickname       = fighter.nickname or fdata.get("nickname")
        fatigue        = int(fdata.get("fatigue", 0))

        # Condition label from fatigue
        if fatigue <= 20:
            condition_status, condition_color = "Fresh",    "fresh"
        elif fatigue <= 40:
            condition_status, condition_color = "Rested",   "rested"
        elif fatigue <= 60:
            condition_status, condition_color = "Ready",    "ready"
        elif fatigue <= 80:
            condition_status, condition_color = "Tired",    "tired"
        else:
            condition_status, condition_color = "Exhausted","exhausted"

        # ── Injury status ──────────────────────────────────────────
        _is_injured = False
        _injury_desc = ""
        _injury_weeks_out = 0
        if INJURY_AVAILABLE and self._injury_system:
            _is_injured = self._injury_system.has_injuries(fighter.fighter_id)
            if _is_injured:
                _worst = self._injury_system.get_worst_injury(fighter.fighter_id)
                if _worst:
                    _injury_desc      = _worst.description
                    _injury_weeks_out = _worst.weeks_remaining

        # ── Momentum tag ───────────────────────────────────────────
        _ws = win_streak
        _ls = lose_streak
        _rank_num = ranking if ranking and ranking > 0 else 99
        is_champion = getattr(fighter, 'is_champion', False)
        if is_champion and _ws >= 1:
            _mtag = "👑 Dominant"
        elif _ws >= 5:
            _mtag = "🔥 On a tear"
        elif _ws >= 3:
            _mtag = "🔥 Hot streak"
        elif _ls >= 3:
            _mtag = "📉 Skid"
        elif _ws >= 2 and _rank_num > 8:
            _mtag = "⚡ Rising"
        else:
            _mtag = ""

        return WebFighter(
            fighter_id=fighter.fighter_id,
            name=fighter.name,
            nickname=nickname,
            age=age,
            is_injured=_is_injured,
            injury_desc=_injury_desc,
            injury_weeks_out=_injury_weeks_out,
            country=country,
            weight_class=wc_str,
            division_abbrev=DIVISION_ABBREV.get(wc_str, "??"),
            fighting_style=fighting_style,
            wins=fighter.wins,
            losses=fighter.losses,
            draws=fighter.draws,
            ko_wins=fighter.ko_wins,
            sub_wins=fighter.sub_wins,
            ko_losses=getattr(fighter, 'ko_losses', 0) or 0,
            sub_losses=getattr(fighter, 'sub_losses', 0) or 0,
            career_fotn_awards=getattr(fighter, 'career_fotn_awards', 0) or 0,
            body_frame=int(fdata.get('body_frame',
                getattr(fighter, 'body_frame', 5)) or 5),
            natural_weight_class=str(fdata.get('natural_weight_class',
                getattr(fighter, 'natural_weight_class', '') or fighter.weight_class)),
            record_str=fighter.record,
            overall_rating=ovr,
            potential=int(fdata.get("potential", ovr + 8)),
            fights_total=int(fighter.wins + fighter.losses + getattr(fighter, 'draws', 0)),
            ovr_at_signing=int(fdata.get('ovr_at_signing', 0)),
            popularity=fighter.popularity,
            ranking=ranking,
            is_champion=fighter.is_champion,
            is_active=fighter.is_active,
            camp_id=fighter.camp_id,
            camp_name=camp_name,
            height=str(fdata.get("height", "5'10\"")),
            reach=str(fdata.get("reach", "72\"")),
            # Attributes: read from fdata if present, else seeded variance
            strength=_attr("strength"),
            speed=_attr("speed",       +3),
            cardio=_attr("cardio",     +2),
            chin=_attr("chin",         -2),
            recovery=_attr("recovery"),
            boxing=_attr("boxing"),
            kicks=_attr("kicks",       -4),
            clinch_striking=_attr("clinch_striking", -3),
            striking_defense=_attr("striking_defense"),
            takedowns=_attr("takedowns",         -2),
            takedown_defense=_attr("takedown_defense"),
            top_control=_attr("top_control",     -4),
            submissions=_attr("submissions",     -5),
            guard=_attr("guard",                 -5),
            heart=_attr("heart",                 +4),
            fight_iq=_attr("fight_iq",           +2),
            composure=_attr("composure",         +1),
            fatigue=fatigue,
            morale=int(fdata.get("morale", 75)),
            condition_status=condition_status,
            condition_color=condition_color,
            win_streak=win_streak,
            lose_streak=lose_streak,
            traits=list(fdata.get("traits", [])),
            momentum_tag=_mtag,
            fight_history=[
                {
                    'opponent_name': f.get('opponent_name', '') if isinstance(f, dict) else '',
                    'opponent_id':   f.get('opponent_id',   '') if isinstance(f, dict) else '',
                    'result':        f.get('result',        '') if isinstance(f, dict) else '',
                    'method':        str(f.get('method',    '')) if isinstance(f, dict) else '',
                    'round_finished':f.get('round_finished', 0) if isinstance(f, dict) else 0,
                    'event_name':    f.get('event_name',    '') if isinstance(f, dict) else '',
                    'fight_id':      f.get('fight_id',      '') if isinstance(f, dict) else '',
                    'week':          f.get('week',          0) if isinstance(f, dict) else 0,
                }
                for f in history[-10:]
            ],
        )


    # =========================================================================
    # FACILITY CAP — TRAINING
    # =========================================================================

    # Two-axis training model: group (domain) + emphasis (weighted stats).
    # Replaces the flat 16-key _FOCUS_ATTRS / _FOCUS_DOMAIN dicts.
    # Each emphasis distributes raw_gain across multiple stats by weight
    # (1.0=primary, 0.5=secondary, 0.25=tertiary). Domain = stats kept
    # "warm" by any focus in this group (used by decay system).
    _TRAINING_GROUPS = {
        "STRIKING": {
            "emphases": {
                "boxing":    {"boxing":1.0,"kicks":0.5,"clinch_striking":0.25,"striking_defense":0.25},
                "kicks":     {"kicks":1.0,"boxing":0.5,"clinch_striking":0.5,"striking_defense":0.25},
                "clinch":    {"clinch_striking":1.0,"boxing":0.5,"kicks":0.25,"striking_defense":0.25},
                "defense":   {"striking_defense":1.0,"boxing":0.25,"kicks":0.25,"clinch_striking":0.25},
            },
            "domain": ["boxing","kicks","clinch_striking","striking_defense","chin","composure","fight_iq"],
        },
        "GRAPPLING": {
            "emphases": {
                "takedowns":         {"takedowns":1.0,"top_control":0.5,"takedown_defense":0.25,"guard":0.25},
                "takedown_defense":  {"takedown_defense":1.0,"takedowns":0.5,"guard":0.25},
                "top_control":       {"top_control":1.0,"takedowns":0.5,"submissions":0.25,"guard":0.25},
                "submissions":       {"submissions":1.0,"guard":0.5,"top_control":0.25},
                "guard":             {"guard":1.0,"submissions":0.5,"takedown_defense":0.25},
            },
            "domain": ["takedowns","takedown_defense","top_control","submissions","guard","fight_iq"],
        },
        "CONDITIONING": {
            "emphases": {
                "cardio":    {"cardio":1.0,"recovery":0.5,"heart":0.25},
                "strength":  {"strength":1.0,"cardio":0.5,"chin":0.25},
                "toughness": {"chin":1.0,"heart":0.5,"recovery":0.5},
            },
            "domain": ["cardio","strength","chin","recovery","heart","speed"],
        },
        "MENTAL": {
            "emphases": {
                "fight_iq":  {"fight_iq":1.0,"composure":0.5,"striking_defense":0.25},
                "composure": {"composure":1.0,"fight_iq":0.5,"heart":0.25},
            },
            "domain": ["fight_iq","composure","striking_defense","heart"],
        },
        "SPARRING": {
            "emphases": {
                "sparring": {"boxing":0.5,"takedown_defense":0.5,"fight_iq":0.5,"speed":0.5},
            },
            "domain": ["boxing","kicks","takedown_defense","fight_iq","composure","chin","speed"],
        },
    }

    # Backward-compat alias map: old flat focus key → (group, emphasis).
    # Legacy saves and any code path still passing a flat key falls
    # through cleanly.
    _FOCUS_LEGACY_MAP = {
        "boxing":           ("STRIKING",     "boxing"),
        "kicks":            ("STRIKING",     "kicks"),
        "clinch_striking":  ("STRIKING",     "clinch"),
        "striking_defense": ("STRIKING",     "defense"),
        "muay_thai":        ("STRIKING",     "kicks"),
        "wrestling":        ("GRAPPLING",    "takedowns"),
        "takedowns":        ("GRAPPLING",    "takedowns"),
        "takedown_defense": ("GRAPPLING",    "takedown_defense"),
        "top_control":      ("GRAPPLING",    "top_control"),
        "bjj":              ("GRAPPLING",    "submissions"),
        "submissions":      ("GRAPPLING",    "submissions"),
        "guard":            ("GRAPPLING",    "guard"),
        "cardio":           ("CONDITIONING", "cardio"),
        "strength":         ("CONDITIONING", "strength"),
        "fight_iq":         ("MENTAL",       "fight_iq"),
        "sparring":         ("SPARRING",     "sparring"),
    }

    # Raw weekly gains per intensity (before cap)
    _INTENSITY_GAIN: Dict[str, int] = {
        "REST": 0, "LIGHT": 1, "MODERATE": 2, "INTENSE": 3, "EXTREME": 4,
    }

    # Soft ceiling per tier — above this, gains diminish but never zero.
    # Bumped 2026-06-02 (F1): tighter gaps between tiers so each upgrade
    # feels meaningful but no tier is a wall for solid prospects.
    _TIER_SOFT_CEIL = {
        "GARAGE":   72,
        "LOCAL":    78,
        "REGIONAL": 85,
        "NATIONAL": 92,
        "ELITE":    100,
    }

    # Equipment system constants
    _EQUIPMENT_TYPES = {
        "heavy_bags":       {"name": "Heavy Bags",      "icon": "🥊",
                             "domain": "striking",
                             "desc": "Boxing, kicks, clinch striking"},
        "wrestling_mats":   {"name": "Wrestling Mats",  "icon": "🤼",
                             "domain": "wrestling",
                             "desc": "Takedowns, top control, TD defense"},
        "submission_mats":  {"name": "Submission Mats", "icon": "🥋",
                             "domain": "bjj",
                             "desc": "BJJ, submissions, guard"},
        "weight_room":      {"name": "Weight Room",     "icon": "💪",
                             "domain": "physical",
                             "desc": "Strength, speed, cardio"},
        "recovery_tank":    {"name": "Recovery Tank",   "icon": "🛁",
                             "domain": "recovery",
                             "desc": "Reduces fatigue accumulation"},
        "cage":             {"name": "Octagon/Cage",    "icon": "🔷",
                             "domain": "mental",
                             "desc": "Fight IQ, composure, heart"},
    }

    _EQUIPMENT_TIERS = {
        "BASIC": {
            "cost":        15_000,
            "gain_bonus":  0.05,
            "decay_bonus": 0.0,
            "passive":     None,
        },
        "PRO": {
            "cost":        40_000,
            "gain_bonus":  0.10,
            "decay_bonus": 0.20,
            "passive":     None,
        },
        "ELITE": {
            "cost":        100_000,
            "gain_bonus":  0.15,
            "decay_bonus": 0.40,
            "passive":     "elite_passive",
        },
    }

    _EQUIPMENT_SLOTS = {
        "GARAGE":   2,
        "LOCAL":    4,
        "REGIONAL": 6,
        "NATIONAL": 8,
        "ELITE":    99,
    }

    _EQUIPMENT_TIER_GATES = {
        "GARAGE":   ["BASIC"],
        "LOCAL":    ["BASIC", "PRO"],
        "REGIONAL": ["BASIC", "PRO", "ELITE"],
        "NATIONAL": ["BASIC", "PRO", "ELITE"],
        "ELITE":    ["BASIC", "PRO", "ELITE"],
    }

    _EQUIPMENT_DOMAIN_STATS = {
        "striking":  ["boxing", "kicks", "clinch_striking", "striking_defense"],
        "wrestling": ["takedowns", "top_control", "takedown_defense"],
        "bjj":       ["submissions", "guard"],
        "physical":  ["strength", "speed", "cardio"],
        "recovery":  ["recovery", "chin"],
        "mental":    ["fight_iq", "composure", "heart"],
    }

    # OVR4 — per-style stat weights for the OVR average. A Wrestler's
    # OVR weights takedowns/td_defense/top_control higher than boxing.
    # Weights >1 mean "this stat matters more for this style"; <1 means
    # less. Average normalizes by sum of weights so result stays 0-100.
    # Unknown styles fall through to Balanced (uniform 1.0 = flat avg,
    # current behavior preserved). Stats not listed in a style's dict
    # default to 1.0.
    _STYLE_OVR_WEIGHTS = {
        "Striker":         {"boxing":2.2,"kicks":1.8,"clinch_striking":1.4,
                            "striking_defense":1.8,"speed":1.6,"fight_iq":1.2,
                            "composure":1.2,"chin":1.1,"cardio":1.1,
                            "takedowns":0.6,"takedown_defense":0.8,
                            "top_control":0.5,"submissions":0.4,"guard":0.5,
                            "strength":0.9,"recovery":1.0,"heart":1.0},
        "Muay Thai":       {"boxing":1.8,"kicks":2.2,"clinch_striking":2.0,
                            "striking_defense":1.6,"speed":1.4,"fight_iq":1.2,
                            "composure":1.2,"chin":1.2,"cardio":1.3,
                            "takedowns":0.7,"takedown_defense":0.9,
                            "top_control":0.5,"submissions":0.4,"guard":0.5,
                            "strength":1.0,"recovery":1.0,"heart":1.1},
        "Karate":          {"boxing":1.6,"kicks":2.0,"striking_defense":2.0,
                            "speed":2.0,"fight_iq":1.4,"composure":1.4,
                            "clinch_striking":1.0,"chin":1.0,"cardio":1.1,
                            "takedowns":0.5,"takedown_defense":0.8,
                            "top_control":0.4,"submissions":0.4,"guard":0.5,
                            "strength":0.8,"recovery":1.0,"heart":1.0},
        "Counter Striker": {"fight_iq":2.2,"composure":2.0,"striking_defense":2.0,
                            "speed":1.8,"boxing":1.6,"kicks":1.2,
                            "clinch_striking":0.8,"chin":1.2,"cardio":1.1,
                            "takedowns":0.5,"takedown_defense":0.8,
                            "top_control":0.4,"submissions":0.4,"guard":0.5,
                            "strength":0.8,"recovery":1.0,"heart":1.1},
        "Point Fighter":   {"fight_iq":2.0,"composure":1.8,"speed":2.2,
                            "striking_defense":1.8,"boxing":1.6,"kicks":1.4,
                            "clinch_striking":0.7,"chin":0.9,"cardio":1.2,
                            "takedowns":0.5,"takedown_defense":0.7,
                            "top_control":0.4,"submissions":0.4,"guard":0.5,
                            "strength":0.7,"recovery":1.0,"heart":1.0},
        "BJJ Specialist":  {"submissions":2.4,"guard":2.2,"top_control":1.6,
                            "takedowns":1.4,"takedown_defense":1.2,
                            "fight_iq":1.3,"composure":1.2,"cardio":1.1,
                            "boxing":0.7,"kicks":0.5,"clinch_striking":0.8,
                            "striking_defense":0.8,"chin":1.0,
                            "strength":1.0,"speed":0.9,"recovery":1.0,"heart":1.1},
        "Wrestler":        {"takedowns":2.2,"takedown_defense":2.0,"top_control":1.8,
                            "strength":1.6,"cardio":1.3,"heart":1.2,
                            "submissions":0.9,"guard":0.8,"fight_iq":1.1,
                            "boxing":0.8,"kicks":0.5,"clinch_striking":1.0,
                            "striking_defense":0.8,"composure":1.0,
                            "speed":1.0,"chin":1.1,"recovery":1.1},
        "Ground & Pound":  {"takedowns":2.0,"top_control":1.8,"strength":2.0,
                            "boxing":1.6,"chin":1.2,"heart":1.3,"cardio":1.2,
                            "takedown_defense":1.4,"submissions":0.7,"guard":0.7,
                            "kicks":0.6,"clinch_striking":1.0,
                            "striking_defense":0.9,"composure":1.0,
                            "speed":0.9,"fight_iq":1.0,"recovery":1.1},
        "Sprawl & Brawl":  {"takedown_defense":2.2,"boxing":1.8,"chin":1.4,
                            "heart":1.4,"strength":1.4,"striking_defense":1.6,
                            "cardio":1.2,"takedowns":0.8,"top_control":0.8,
                            "submissions":0.6,"guard":0.7,"kicks":1.0,
                            "clinch_striking":1.1,"composure":1.1,
                            "speed":1.0,"fight_iq":1.1,"recovery":1.1},
        "Judo":            {"takedowns":2.0,"top_control":1.8,"takedown_defense":1.6,
                            "clinch_striking":1.4,"strength":1.4,"guard":1.2,
                            "submissions":1.2,"heart":1.1,"cardio":1.1,
                            "boxing":0.8,"kicks":0.6,"striking_defense":0.9,
                            "composure":1.0,"fight_iq":1.0,
                            "speed":1.0,"chin":1.0,"recovery":1.0},
        "Sambo":           {"takedowns":1.8,"submissions":1.8,"top_control":1.6,
                            "strength":1.4,"takedown_defense":1.4,"guard":1.2,
                            "boxing":1.2,"heart":1.2,"cardio":1.1,
                            "kicks":0.8,"clinch_striking":1.0,
                            "striking_defense":0.9,"composure":1.0,
                            "fight_iq":1.1,"speed":0.9,"chin":1.0,"recovery":1.0},
        "Pressure Fighter":{"chin":2.0,"heart":2.0,"cardio":1.8,"strength":1.6,
                            "boxing":1.6,"clinch_striking":1.4,"recovery":1.3,
                            "takedowns":0.9,"takedown_defense":1.0,
                            "top_control":0.7,"submissions":0.6,"guard":0.7,
                            "kicks":0.8,"striking_defense":1.0,"composure":1.2,
                            "speed":0.9,"fight_iq":1.0},
        "Clinch Fighter":  {"clinch_striking":2.2,"takedowns":1.6,"top_control":1.6,
                            "strength":1.6,"chin":1.4,"heart":1.4,"cardio":1.4,
                            "takedown_defense":1.2,"boxing":1.2,"guard":0.9,
                            "submissions":0.9,"kicks":0.8,"striking_defense":1.0,
                            "composure":1.1,"speed":0.9,"fight_iq":1.1,"recovery":1.1},
        "Balanced":        {},  # empty = all stats at 1.0 (flat avg)
    }

    # Legacy-name → canonical-name redirect for the weights lookup.
    # Catches world_init.py output (Grappler, Brawler) and any
    # FighterRecord still carrying old strings (Orthodox Boxer, etc).
    _STYLE_OVR_ALIASES = {
        "Orthodox Boxer":    "Striker",
        "Kickboxer":         "Striker",
        "Kickboxing":        "Striker",
        "Boxing":            "Striker",
        "Counter-Striker":   "Counter Striker",
        "Submission Artist": "BJJ Specialist",
        "Submissions":       "BJJ Specialist",
        "Grappler":          "Wrestler",
        "Grappling":         "Wrestler",
        "Brawler":           "Pressure Fighter",
        "MMA Hybrid":        "Balanced",
        "Hybrid":            "Balanced",
    }

    def _read_stat(self, fighter, stat) -> float:
        """Read a per-attribute stat with _fighter_data fallback.

        During training, code does setattr(fighter, stat, val) and the
        attribute exists transiently on the FighterRecord. But after
        save/load, FighterRecord comes back from from_dict with only
        its declared fields — per-stat attributes don't survive as
        attrs (they live in _fighter_data per Ship #32). This helper
        prefers the attribute when present, falls back to _fighter_data
        when not, so _compute_ovr works in both transient-attr and
        cold-load scenarios.
        """
        val = getattr(fighter, stat, None)
        if val is not None:
            return float(val)
        if self._game_state:
            fdata = self._game_state._fighter_data.get(
                getattr(fighter, 'fighter_id', ''), {})
            return float(fdata.get(stat, 0))
        return 0.0

    def _compute_ovr(self, fighter) -> int:
        """Style-weighted OVR. Weights are normalized to sum to
        len(_TRAINABLE) so the result stays in the same 0-100
        range as the pre-OVR4 flat average. Higher weights shift
        emphasis toward style-relevant stats without inflating
        or deflating the overall number.

        Legacy-save guard: if fewer than 10 of 17 stats have
        real data, preserve the saved overall_rating. Prevents
        legacy saves (pre-Ship-#32) from having OVRs nuked by
        missing stat data.
        """
        _TRAINABLE = [
            "strength","speed","cardio","chin","recovery",
            "boxing","kicks","clinch_striking","striking_defense",
            "takedowns","takedown_defense","top_control","submissions",
            "guard","heart","fight_iq","composure",
        ]

        # Legacy-save guard: count stats with real data.
        # Pre-Ship-#32 saves have no per-stat entries — preserve
        # the saved overall_rating rather than computing from zeros.
        stat_vals = [self._read_stat(fighter, s) for s in _TRAINABLE]
        stats_with_data = sum(1 for v in stat_vals if v > 0)
        if stats_with_data < 10:
            return int(getattr(fighter, 'overall_rating', 65) or 65)

        raw_style = str(getattr(fighter, 'fighting_style', '') or 'Balanced')
        canonical = self._STYLE_OVR_ALIASES.get(raw_style, raw_style)
        weights = self._STYLE_OVR_WEIGHTS.get(canonical,
                  self._STYLE_OVR_WEIGHTS.get("Balanced", {}))

        raw_weights = [weights.get(stat, 1.0) for stat in _TRAINABLE]
        total_raw = sum(raw_weights)
        n = len(_TRAINABLE)
        scale = n / total_raw if total_raw > 0 else 1.0
        normalized = [w * scale for w in raw_weights]

        weighted_sum = sum(
            v * w for v, w in zip(stat_vals, normalized)
        )
        return round(weighted_sum / n)

    # Athletic vs technical stat split. Athletic base = body capacity
    # (physiology) — builds slowly with conditioning, persists for weeks
    # after training stops. Technical skills = motor patterns + ring IQ —
    # respond fast to focused reps, rust fast without practice.
    # Drives per-stat gain multipliers in _diminishing_gain and decay
    # multipliers in maintenance_training.get_decay_multiplier.
    _ATHLETIC_BASE_STATS = {
        "strength", "speed", "cardio", "chin", "recovery", "heart"
    }
    _TECHNICAL_STATS = {
        "boxing", "kicks", "clinch_striking", "striking_defense",
        "takedowns", "takedown_defense", "top_control",
        "submissions", "guard", "fight_iq", "composure"
    }

    # Per-archetype passive-boost multiplier. sc_coach compensates for the
    # athletic ×0.5 multiplier inside _diminishing_gain (OVR2 split) so its
    # gains land comparable in magnitude to technical coaches. mma_coach
    # spreads over only 2 attrs (post-G3 heart-to-sc move), so the boost
    # widens its effective per-week contribution.
    _ARCHETYPE_BOOST = {
        "striking_coach":  1.0,
        "grappling_coach": 1.0,
        "sc_coach":        2.0,
        "mma_coach":       1.5,
    }

    def _diminishing_gain(self, current: float, raw_gain: float,
                           camp_tier: str,
                           fighter_potential: Optional[int] = None,
                           stat_name: Optional[str] = None) -> float:
        """
        Diminishing returns above the effective ceiling. Effective ceiling
        is min(camp_soft_ceil, fighter_potential) when potential known —
        a high-potential fighter in a low-tier camp is still capped by
        the camp; a low-potential fighter caps out earlier than the camp
        tier would allow.

        Below ceiling → full gain.
        Above ceiling → gain tapers linearly, reaching ~5% at 30pts above.
        Never actually zero — a fighter can always grind, just very slowly.

        Formula:
            effective_ceil = min(soft_ceil, fighter_potential)  (or soft_ceil if None)
            overshoot = max(0, current - effective_ceil)
            multiplier = max(0.05, 1 - overshoot / 30)
            effective = raw_gain * multiplier
        """
        soft_ceil = self._TIER_SOFT_CEIL.get(camp_tier.upper(), 65)
        effective_ceil = (min(soft_ceil, fighter_potential)
                          if fighter_potential is not None
                          else soft_ceil)
        overshoot = max(0.0, current - effective_ceil)
        multiplier = max(0.05, 1.0 - overshoot / 30.0)

        # Athletic base builds slowly (physiology); technical skills
        # respond faster to focused reps.
        if stat_name in self._ATHLETIC_BASE_STATS:
            multiplier *= 0.5
        elif stat_name in self._TECHNICAL_STATS:
            multiplier *= 1.2

        # Facility efficiency bonus — better gym = faster gains below ceiling too
        if FACILITIES_AVAILABLE:
            try:
                from facilities import get_training_efficiency
                multiplier *= get_training_efficiency(camp_tier)
            except Exception:
                pass

        return raw_gain * multiplier

    def apply_training_week(self, fighter_id: str, focus: str,
                             intensity: str, camp_tier: str) -> Dict[str, Any]:
        """
        Apply one week of training to a fighter.
        Uses Option A diminishing returns — no hard cap, gains taper
        above the tier's soft ceiling. A 73 OVR fighter in GARAGE
        (ceil 65) still improves, just slowly in stats already above 65.
        """
        intensity_up  = intensity.upper()
        raw_gain      = self._INTENSITY_GAIN.get(intensity_up, 2)

        # Resolve flat legacy key OR "GROUP:emphasis" format to
        # (group_name, emphasis_name).
        if ":" in str(focus):
            _grp, _emp = focus.split(":", 1)
            _grp = _grp.upper()
        else:
            _grp, _emp = self._FOCUS_LEGACY_MAP.get(
                str(focus).lower(), ("SPARRING", "sparring")
            )

        _group_data = self._TRAINING_GROUPS.get(_grp, self._TRAINING_GROUPS["SPARRING"])
        _emphasis_weights = _group_data["emphases"].get(
            _emp, list(_group_data["emphases"].values())[0]
        )
        _domain = _group_data["domain"]

        fatigue_delta = {
            "REST": -15, "LIGHT": 2, "MODERATE": 5, "INTENSE": 10, "EXTREME": 18,
        }.get(intensity_up, 5)

        actual_gains: Dict[str, float] = {}

        if self._game_state and raw_gain > 0:
            fighter = self._game_state.get_fighter(fighter_id)
            # Per-fighter potential ceiling — read from _fighter_data once.
            _fp = self._game_state._fighter_data.get(fighter_id, {}).get("potential")
            _fp = int(_fp) if _fp is not None else None
            if fighter and hasattr(fighter, 'overall_rating'):
                # Apply gains using emphasis weights (1.0=primary, 0.5=secondary,
                # 0.25=tertiary). Stats outside the emphasis dict get 0 gain.
                # Stats in domain but not emphasis still benefit from coach passive.
                # Stats live in _fighter_data dict, not on FighterRecord
                # (Ship #32). Read from there; setattr-on-FighterRecord
                # writes never reach the UI or save layer.
                _fdata = self._game_state._fighter_data.get(fighter_id, {})
                _style = str(getattr(fighter, 'fighting_style',
                             _fdata.get('style', 'Balanced')) or 'Balanced')
                _STYLE_AFFINITY = {
                    "Striker":        {"boxing":1.3,"kicks":1.2,"striking_defense":1.2,
                                       "clinch_striking":1.1,"takedowns":0.75,"submissions":0.75},
                    "Wrestler":       {"takedowns":1.35,"top_control":1.3,"takedown_defense":1.25,
                                       "boxing":0.9,"kicks":0.8},
                    "BJJ Specialist": {"submissions":1.35,"guard":1.3,"top_control":1.2,
                                       "takedowns":1.1,"boxing":0.85},
                    "Ground & Pound": {"takedowns":1.3,"top_control":1.25,"boxing":1.2,
                                       "submissions":0.85},
                    "Pressure Fighter":{"boxing":1.2,"clinch_striking":1.25,"chin":1.1,
                                        "cardio":1.15,"takedown_defense":1.1},
                    "Counter Striker":{"striking_defense":1.3,"fight_iq":1.25,"composure":1.2,
                                       "boxing":1.1,"takedowns":0.8},
                    "Balanced":       {},
                }
                _affinity = _STYLE_AFFINITY.get(_style, {})
                for stat, weight in _emphasis_weights.items():
                    current = float(_fdata.get(stat,
                                    getattr(fighter, 'overall_rating', 65)))
                    weighted_gain = raw_gain * weight
                    effective = self._diminishing_gain(
                        current, weighted_gain, camp_tier,
                        fighter_potential=_fp, stat_name=stat
                    )
                    effective *= _affinity.get(stat, 1.0)
                    # Equipment gain bonus — multiply by domain bonus from player camp equipment
                    try:
                        if self._game_state:
                            _camp_id = self._game_state.player_camp_id
                            _FOCUS_TO_DOMAIN = {
                                "boxing":           "striking",
                                "kicks":            "striking",
                                "clinch_striking":  "striking",
                                "striking_defense": "striking",
                                "muay_thai":        "striking",
                                "wrestling":        "wrestling",
                                "top_control":      "wrestling",
                                "takedown_defense": "wrestling",
                                "bjj":              "bjj",
                                "submissions":      "bjj",
                                "cardio":           "physical",
                                "strength":         "physical",
                                "fight_iq":         "mental",
                                "sparring":         "mental",
                            }
                            _domain = _FOCUS_TO_DOMAIN.get(focus, "")
                            if _domain:
                                _eq_bonus = self.get_equipment_gain_bonus(_camp_id, _domain)
                                effective = effective * _eq_bonus
                    except Exception:
                        pass
                    if effective > 0.01:
                        if fighter_id in self._game_state._fighter_data:
                            _fdata_ref = self._game_state._fighter_data[fighter_id]
                            _new_val = round(min(100.0, current + effective), 2)
                            # Chin permanent erosion cap — facility soft ceil drops
                            # by permanent erosion amount; chin cannot train above it.
                            if stat == 'chin':
                                _perm_erosion = float(_fdata_ref.get(
                                    'chin_permanent_erosion', 0.0))
                                if _perm_erosion > 0:
                                    _chin_ceil = min(100.0,
                                        self._TIER_SOFT_CEIL.get(
                                            camp_tier.upper(), 65) - _perm_erosion)
                                    _new_val = min(_new_val, _chin_ceil)
                            _fdata_ref[stat] = _new_val
                        actual_gains[stat] = round(effective, 2)

                # Read current fatigue from _fighter_data (canonical source) —
                # FighterRecord has no fatigue field post-Ship-#32 so getattr
                # would always return 0, making fatigue effectively a per-week
                # delta instead of accumulating across weeks.
                _current_fatigue = float(
                    self._game_state._fighter_data.get(fighter_id, {}).get('fatigue', 0)
                )
                fatigue = max(0, min(100, _current_fatigue + fatigue_delta))
                if fighter_id in self._game_state._fighter_data:
                    self._game_state._fighter_data[fighter_id]['fatigue'] = fatigue
                if hasattr(fighter, 'fatigue'):
                    fighter.fatigue = fatigue

                # Style-weighted OVR — see _compute_ovr for weight vectors.
                fighter.overall_rating = self._compute_ovr(fighter)
            else:
                for stat in _emphasis_weights:
                    actual_gains[stat] = float(raw_gain)
        else:
            for stat in _emphasis_weights:
                actual_gains[stat] = 0.0

        self._clear_cache()
        soft_ceil = self._TIER_SOFT_CEIL.get(camp_tier.upper(), 65)

        # ── Injury system — real CLI injury module ─────────────────
        import random as _ir
        _injured = False
        if INJURY_AVAILABLE and self._injury_system and self._game_state:
            _rftr = self._game_state.get_fighter(fighter_id)
            _fatigue = getattr(_rftr, 'fatigue', 0) or 0
            _fight_dmg = getattr(_rftr, 'fight_damage', 0) or 0
            # Map intensity to the CLI system's integer value (1-4)
            _int_val = {"REST":0,"LIGHT":1,"MODERATE":2,"INTENSE":3,"EXTREME":4}.get(intensity_up, 2)
            # Fight damage adds extra risk — higher fatigue equivalent
            _effective_fatigue = min(100, _fatigue + _fight_dmg * 0.5)
            _prob = calculate_training_injury_probability(_int_val, _effective_fatigue)
            # INJURY_RISK + INTENSE — both push training injury chance up 40%, capped at 25%
            _coach_t_inj = self._coach.get('traits', []) if getattr(self, '_coach', None) else []
            if 'INJURY_RISK' in _coach_t_inj or 'INTENSE' in _coach_t_inj:
                _prob = min(_prob * 1.4, 0.25)
            if _int_val > 0 and _ir.random() < _prob:
                _injured = True
                injury = generate_training_injury(fighter_id)
                self._injury_system.add_injury(injury)
                # Halve gains this week
                actual_gains = {k: round(v * 0.5, 2) for k, v in actual_gains.items()}
                # Clear fight_damage after injury fires
                if _rftr:
                    try: setattr(_rftr, 'fight_damage', 0)
                    except Exception: pass
                _fname = getattr(_rftr, 'name', fighter_id) if _rftr else fighter_id
                print(f"  🤕 [INJURY] {_fname} — {injury.description} ({injury.severity_name}) "
                      f"· {injury.recovery_weeks}w recovery")
                # News item for player fighter injuries OR champion injuries
                _pids = {f.fighter_id for f in self.get_player_fighters()}
                _is_champ = bool(_rftr and getattr(_rftr, 'is_champion', False))
                if (fighter_id in _pids or _is_champ) and self._game_state:
                    if _is_champ:
                        _wc = getattr(_rftr, 'weight_class', '')
                        _hl = (f"🏆 {_fname} ({_wc} Champion) suffers "
                               f"{injury.description} — out {injury.recovery_weeks} weeks. "
                               f"Title defense delayed.")
                    else:
                        _hl = (f"🤕 {_fname} suffers training injury: {injury.description} "
                               f"— {injury.recovery_weeks} week recovery")
                    self._news_items.insert(0, {
                        "headline": _hl,
                        "category": "injury",
                        "week": self._game_state.week_number,
                    })
                    self._maybe_queue_champion_injury_decision(_rftr, injury)

                    # Ship IN1: auto-cancel scheduled fights the injured
                    # player fighter can't make (recovery > weeks until
                    # the bout). Mirrors the division-move cancellation
                    # pipeline at line ~13060: drop from _scheduled_fights,
                    # _upcoming_cards (unlock if under cap), and
                    # _ai_deferred_bookings.
                    if fighter_id in _pids:
                        _inj_fid   = fighter_id
                        _inj_weeks = getattr(injury, 'recovery_weeks',
                                             getattr(injury, 'weeks', 0))
                        _fights_to_cancel = []
                        for _sf in list(self._scheduled_fights):
                            if (_sf.get("fighter1_id") == _inj_fid
                                    or _sf.get("fighter2_id") == _inj_fid):
                                _wks = _sf.get("weeks_until",
                                               _sf.get("week", 0) -
                                               self._game_state.week_number)
                                if _inj_weeks > max(_wks, 0):
                                    _fights_to_cancel.append(_sf)
                        for _sf in _fights_to_cancel:
                            _opp = (_sf.get("fighter2_name", "?")
                                    if _sf.get("fighter1_id") == _inj_fid
                                    else _sf.get("fighter1_name", "?"))
                            if _sf in self._scheduled_fights:
                                self._scheduled_fights.remove(_sf)
                            _tgt_wk = _sf.get("week", 0)
                            if _tgt_wk in self._upcoming_cards:
                                _card = self._upcoming_cards[_tgt_wk]
                                _card["fights"] = [
                                    f for f in _card.get("fights", [])
                                    if f.get("fight_id") != _sf.get("fight_id")
                                ]
                                if len(_card.get("fights", [])) < CARD_TARGET_FIGHTS:
                                    _card["locked"] = False
                            self._ai_deferred_bookings = [
                                q for q in self._ai_deferred_bookings
                                if q.get("fight_id") != _sf.get("fight_id")
                            ]
                            self._news_items.insert(0, {
                                "headline": (f"⚕️ {_fname} injured — "
                                             f"bout vs {_opp} cancelled."),
                                "category": "injury",
                                "week":     self._game_state.week_number,
                                "icon":     "⚕️",
                            })
                            print(f"  ⚕️  [INJURY CANCEL] {_fname} vs {_opp} "
                                  f"cancelled ({_inj_weeks}w injury)")
        else:
            # Fallback if injury system not available
            _INJURY_BASE = {"REST":0.0,"LIGHT":0.0,"MODERATE":0.01,
                            "INTENSE":0.03,"EXTREME":0.08}.get(intensity_up, 0.0)
            if _INJURY_BASE > 0 and _ir.random() < _INJURY_BASE:
                _injured = True
                actual_gains = {k: round(v * 0.5, 2) for k, v in actual_gains.items()}

        return {
            "success":       True,
            "injured":       _injured,
            "focus":         focus,
            "intensity":     intensity_up,
            "raw_gain":      raw_gain,
            "actual_gains":  actual_gains,
            "soft_ceiling":  soft_ceil,
            "camp_tier":     camp_tier,
            "fatigue_delta": fatigue_delta,
        }

    # =========================================================================
    # TRAINING PLAN SYSTEM
    # =========================================================================

    def set_training_plan(self, fighter_id: str, focus: str, intensity: str) -> Dict[str, Any]:
        """
        Set a fighter's weekly training plan.
        Applied automatically every advance_week — not immediately.
        """
        self._fighter_training_plans[fighter_id] = {
            "focus":     focus,
            "intensity": intensity.upper(),
        }
        fighter = self.get_fighter(fighter_id)
        name    = fighter.name if fighter else fighter_id
        return {"success": True, "message": f"{name}'s training plan updated: {focus} at {intensity}"}

    def get_training_plan(self, fighter_id: str) -> Dict[str, Any]:
        """Get a fighter's current training plan, or sensible default."""
        return self._fighter_training_plans.get(fighter_id, {
            "focus":     "sparring",
            "intensity": "MODERATE",
        })

    def _record_training_week(self,
                              fighter_id: str,
                              week: int,
                              focus: str,
                              intensity: str,
                              is_fight_camp: bool,
                              ovr_before: int,
                              ovr_after: int,
                              gains: Dict[str, float]) -> None:
        """
        Ship A: append this week's training entry to fighter's rolling
        history. Capped at TRAINING_HISTORY_WEEKS entries via FIFO.
        Maintenance decays + coach passive boosts are stitched onto the
        same entry later in _advance_maintenance_week.
        """
        entry = {
            "week":          week,
            "focus":         focus,
            "intensity":     intensity,
            "is_fight_camp": is_fight_camp,
            "ovr_before":    ovr_before,
            "ovr_after":     ovr_after,
            "gains":         {k: float(v) for k, v in gains.items() if v > 0.01},
            "coach_boosts":  {},   # filled in by _advance_maintenance_week
            "decays":        {},   # filled in by _advance_maintenance_week
        }
        if fighter_id not in self._training_history:
            self._training_history[fighter_id] = []
        self._training_history[fighter_id].append(entry)
        # FIFO eviction — keep only the most recent N entries
        if len(self._training_history[fighter_id]) > TRAINING_HISTORY_WEEKS:
            self._training_history[fighter_id] = (
                self._training_history[fighter_id][-TRAINING_HISTORY_WEEKS:]
            )

    def get_training_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return rolling training history for all player fighters.
        Each fighter's list is capped at TRAINING_HISTORY_WEEKS entries,
        most recent last. Ship A.
        """
        if not self._game_state:
            return {}
        player_ids = {f.fighter_id for f in self.get_player_fighters()}
        return {fid: list(entries) for fid, entries in self._training_history.items()
                if fid in player_ids}

    def _apply_weekly_training(self) -> Dict[str, Any]:
        """
        Called each advance_week.
        1. Applies each player fighter's training plan.
        2. Applies passive coach specialty gains to all player fighters.
        Returns a report dict: {fighter_id: {name, gains, focus, intensity, ovr_before, ovr_after}}
        """
        if not self._game_state:
            return {}

        player_camp = self.get_player_camp()
        camp_tier   = player_camp.tier.upper() if player_camp else "GARAGE"
        player_fighters = self._game_state.get_player_fighters()

        # SPECIALTY_MAP + _ARCHETYPE_DOMAIN — reused per coach inside the
        # fighter loop. Ship MC1b: training gain is multi-coach. Each coach
        # on staff contributes independently; coaches sharing a domain
        # apply diminishing rates (1.0 / 0.50 / 0.25 / 0.10).
        SPECIALTY_MAP = {
            # Striking
            "striking": "striking_coach",    "boxing":   "striking_coach",
            "kickboxing": "striking_coach",  "muay thai": "striking_coach",
            "muay_thai":  "striking_coach",
            # Grappling
            "wrestling":   "grappling_coach", "grappling": "grappling_coach",
            "bjj":         "grappling_coach", "submissions": "grappling_coach",
            # Jiu-Jitsu — generated as "Jiu-Jitsu" by world-gen; both
            # hyphen and underscore forms route to grappling_coach.
            "jiu-jitsu":   "grappling_coach", "jiu_jitsu": "grappling_coach",
            # S&C (merged strength + conditioning)
            "s&c":         "sc_coach",        "strength":    "sc_coach",
            "conditioning": "sc_coach",       "cardio":      "sc_coach",
            "s and c":     "sc_coach",
            # Head Coach / MMA
            "mma":         "mma_coach",       "head coach":  "mma_coach",
            "cornering":   "mma_coach",       "strategy":    "mma_coach",
        }
        _ARCHETYPE_DOMAIN = {
            "striking_coach":  "striking",
            "grappling_coach": "grappling",
            "sc_coach":        "sc",
            "mma_coach":       "mma_head",
        }

        report = {}

        for fighter in player_fighters:
            fid  = fighter.fighter_id
            plan = self._fighter_training_plans.get(fid)

            # If fighter has a fight booked, use fight camp settings instead
            fight_plan = None
            for fight in self._scheduled_fights:
                if fight.get("fighter1_id") == fid or fight.get("fighter2_id") == fid:
                    if fight.get("training_focus"):
                        fight_plan = {
                            "focus":     fight["training_focus"],
                            "intensity": fight.get("intensity", "MODERATE"),
                        }
                    break

            active_plan = fight_plan or plan or {"focus": "sparring", "intensity": "MODERATE"}

            # Snapshot OVR before
            real_fighter = self._game_state.get_fighter(fid)
            ovr_before = getattr(real_fighter, 'overall_rating', 0) if real_fighter else 0

            result = self.apply_training_week(fid, active_plan["focus"], active_plan["intensity"], camp_tier)

            # ── MC1b: Multi-coach passive gain pass ───────────────────────
            # Each coach on staff contributes independently. Coaches in the
            # same domain apply diminishing rates so 3 striking coaches
            # don't 3× a fighter's striking gains.
            if self._coaching_staff:
                _active_coaches = list(self._coaching_staff)
            elif self._coach_contract and self._coach:
                # Legacy single-coach fallback (pre-MC1a saves)
                _active_coaches = [self._coach]
            else:
                _active_coaches = []

            # Per-fighter context — computed once, reused across coaches
            _fighter_age = getattr(fighter, 'age', 25) or 25
            _contract_cur = self._contracts.get(fid, {})
            _morale_cur = _contract_cur.get('morale', 75)
            _hist_cur = getattr(fighter, 'fight_history', []) or []
            _last_result = (_hist_cur[-1].get('result')
                            if _hist_cur and isinstance(_hist_cur[-1], dict)
                            else None)
            _lose_streak = getattr(fighter, 'lose_streak', 0) or 0

            # Per-archetype attrs (which stats each archetype trains)
            _COACH_ATTRS = {
                "striking_coach":  ["boxing", "kicks", "clinch_striking", "striking_defense"],
                "grappling_coach": ["takedowns", "takedown_defense", "top_control",
                                    "submissions", "guard"],
                "sc_coach":        ["strength", "speed", "cardio", "chin",
                                    "recovery", "heart"],
                "mma_coach":       ["fight_iq", "composure"],
            }

            # Specialist attr sets (reused per coach)
            _GRAPPLING_ATTRS    = {'takedowns','takedown_defense',
                                    'top_control','submissions','guard'}
            _STRIKING_ATTRS     = {'boxing','kicks','clinch_striking',
                                    'striking_defense'}
            _CONDITIONING_ATTRS = {'cardio','recovery','chin'}
            _FINISHER_ATTRS     = {'boxing','kicks','clinch_striking',
                                    'submissions'}
            _DEFENSIVE_ATTRS    = {'striking_defense','takedown_defense'}

            _domain_coach_count: Dict[str, int] = {}

            real_fighter = self._game_state.get_fighter(fid)
            # Per-fighter potential ceiling for the coach passive boost too.
            _fp = self._game_state._fighter_data.get(fid, {}).get("potential")
            _fp = int(_fp) if _fp is not None else None

            for _cs in _active_coaches:
                cs_specialty = str(_cs.get("specialty", "boxing") or "boxing").lower()
                cs_rating    = int(_cs.get("rating", 60) or 60)
                cs_name      = _cs.get("name", "Coach")
                cs_traits    = _cs.get("traits", []) or []
                cs_passive   = max(0.1, (cs_rating - 50) / 25)
                cs_focus     = SPECIALTY_MAP.get(cs_specialty, "mma_coach")
                cs_attrs     = _COACH_ATTRS.get(cs_focus, ["fight_iq"])
                cs_boost     = self._ARCHETYPE_BOOST.get(cs_focus, 1.0)

                # Domain diminishing rate — same-domain coaches dilute
                _domain = _ARCHETYPE_DOMAIN.get(cs_focus, "mma_head")
                _dc = _domain_coach_count.get(_domain, 0)
                if   _dc == 0: _rate = 1.0
                elif _dc == 1: _rate = 0.50
                elif _dc == 2: _rate = 0.25
                else:          _rate = 0.10
                _domain_coach_count[_domain] = _dc + 1

                # ── Per-coach trait multiplier (composable, flat ifs) ─────
                _trait_delta = 0.0
                if 'TECHNICAL_GENIUS' in cs_traits:
                    _trait_delta += 0.15
                if 'DIAMOND_POLISHER' in cs_traits and _fighter_age < 28:
                    _trait_delta += 0.25
                if 'VETERANS_TOUCH' in cs_traits and _fighter_age >= 30:
                    _trait_delta += 0.20
                if 'MOTIVATOR' in cs_traits and _morale_cur < 60:
                    _trait_delta += 0.15
                if 'IRON_SHARPENER' in cs_traits:
                    _trait_delta += 0.10
                if 'BURNED_OUT' in cs_traits:
                    _trait_delta -= 0.15
                if 'FAIR_WEATHER' in cs_traits:
                    if _last_result == 'L':
                        _trait_delta -= 0.20
                    elif _last_result == 'W':
                        _trait_delta += 0.20
                if 'OLD_SCHOOL' in cs_traits:
                    _trait_delta += 0.10
                if 'MODERN_METHODS' in cs_traits and _fighter_age < 26:
                    _trait_delta += 0.15
                if 'INTENSE' in cs_traits:
                    _trait_delta += 0.10
                if 'DISCIPLINARIAN' in cs_traits:
                    _trait_delta += 0.10
                if 'TASKMASTER' in cs_traits:
                    _trait_delta += 0.15
                    if _morale_cur < 40:
                        _trait_delta += 0.10
                if 'PATIENT' in cs_traits and _lose_streak >= 2:
                    _trait_delta += 0.15
                _trait_mult = max(0.5, 1.0 + _trait_delta)

                # Per-coach specialist mult — closure binds cs_traits via default arg
                def _specialist_mult(attr_name: str, _t=cs_traits) -> float:
                    _sm = 1.0
                    if 'ANALYTICAL' in _t and attr_name in {'fight_iq', 'composure'}:
                        _sm += 0.20
                    if 'CONDITIONING_COACH' in _t and attr_name in _CONDITIONING_ATTRS:
                        _sm += 0.20
                    if 'GRAPPLING_SPECIALIST' in _t and attr_name in _GRAPPLING_ATTRS:
                        _sm += 0.20
                    if 'STRIKING_SPECIALIST' in _t and attr_name in _STRIKING_ATTRS:
                        _sm += 0.20
                    if 'FINISHER' in _t and attr_name in _FINISHER_ATTRS:
                        _sm += 0.20
                    if 'DEFENSIVE_MINDED' in _t and attr_name in _DEFENSIVE_ATTRS:
                        _sm += 0.20
                    return _sm

                _base_per_attr_gain = ((cs_passive / len(cs_attrs))
                                       * cs_boost * _trait_mult * _rate)

                if real_fighter and _base_per_attr_gain > 0:
                    _fdata_c = self._game_state._fighter_data.get(fid, {})
                    for attr in cs_attrs:
                        per_attr_gain = _base_per_attr_gain * _specialist_mult(attr)
                        current = float(_fdata_c.get(attr,
                                        getattr(real_fighter, 'overall_rating', 50)))
                        effective = self._diminishing_gain(current, per_attr_gain, camp_tier,
                                                           fighter_potential=_fp,
                                                           stat_name=attr)
                        if effective > 0.01:
                            if fid in self._game_state._fighter_data:
                                self._game_state._fighter_data[fid][attr] = round(
                                    min(100.0, current + effective), 2)
                            if result.get("actual_gains") is not None:
                                result["actual_gains"][f"{attr} (coach: {cs_name})"] = round(effective, 2)

            # Recompute OVR once after all coaches have contributed
            if real_fighter:
                real_fighter.overall_rating = self._compute_ovr(real_fighter)

            ovr_after = getattr(self._game_state.get_fighter(fid), 'overall_rating', ovr_before)

            # ── Terminal: player training report ──────────────────────
            _ptype = "FIGHT CAMP" if fight_plan else "WEEKLY PLAN"
            _ag    = result.get("actual_gains") or {}
            _main  = {k: v for k, v in _ag.items() if "(coach:" not in k}
            _cch   = {k: v for k, v in _ag.items() if "(coach:" in k}
            _m_str = ", ".join(f"{k}+{v:.1f}" for k, v in list(_main.items())[:3] if v)
            _c_str = ", ".join(f"{k.split(' (coach:')[0]}+{v:.1f}" for k, v in list(_cch.items())[:2] if v)
            _ftr   = self._game_state.get_fighter(fid) if self._game_state else None
            _ovr_n = getattr(_ftr, 'overall_rating', ovr_before)
            print(f"  📊 [{_ptype}] {getattr(fighter,'name',fid)[:12]} "
                  f"| {active_plan['focus']}@{active_plan['intensity']} "
                  f"| OVR {ovr_before}→{_ovr_n} "
                  f"| {_m_str or '—'}"
                  + (f" | coach:{_c_str}" if _c_str else ""))

            # Accumulate fractional gains for display
            if fid not in self._camp_stat_totals:
                self._camp_stat_totals[fid] = {}
            week_gains = result.get("actual_gains", {})
            for stat, gain in week_gains.items():
                if "(coach:" not in stat and gain > 0.05:
                    self._camp_stat_totals[fid][stat] = (
                        self._camp_stat_totals[fid].get(stat, 0.0) + float(gain)
                    )

            report[fid] = {
                "name":          fighter.name if hasattr(fighter, 'name') else fid,
                "focus":         active_plan["focus"].replace("_", " ").title(),
                "intensity":     active_plan["intensity"],
                "gains":         {k: v for k, v in result.get("actual_gains", {}).items() if v > 0.01},
                "camp_totals":   dict(self._camp_stat_totals.get(fid, {})),
                "ovr_before":    ovr_before,
                "ovr_after":     ovr_after,
                "ovr_delta":     ovr_after - ovr_before,
                "is_fight_camp": bool(fight_plan),
                "capped_stats":  result.get("capped_stats", []),
            }

            # Ship A: append this week's entry to rolling 4-week history.
            # Pre-split gains into plan vs coach-attributed so the UI can
            # render them as separate pill types. Maintenance boosts/decays
            # stitched onto the same entry later in _advance_maintenance_week.
            _ag_all      = result.get("actual_gains", {}) or {}
            _plan_gains  = {k: v for k, v in _ag_all.items()
                            if "(coach:" not in k and v > 0.01}
            _coach_gains: Dict[str, float] = {}
            for _k, _v in _ag_all.items():
                if "(coach:" in _k and _v > 0.01:
                    _attr = _k.split(" (coach:")[0]
                    _coach_gains[_attr] = _coach_gains.get(_attr, 0.0) + _v
            self._record_training_week(
                fighter_id    = fid,
                week          = self._game_state.week_number,
                focus         = active_plan["focus"],
                intensity     = active_plan["intensity"],
                is_fight_camp = bool(fight_plan),
                ovr_before    = ovr_before,
                ovr_after     = ovr_after,
                gains         = _plan_gains,
            )
            # Pre-fill coach-attributed gains from training onto the entry
            # just appended (maintenance loop also writes to coach_boosts).
            if fid in self._training_history and self._training_history[fid]:
                self._training_history[fid][-1]["coach_boosts"].update(_coach_gains)

            # M1 Phase 2a — record activity for every stat in the focus's
            # domain so the decay system sees this week's training and won't
            # flag the trained-domain stats as idle. Closes the missing wire
            # between _apply_weekly_training and the maintenance activity
            # tracker. Falls back to [focus] for unknown focus keys.
            if self._maintenance_system:
                _focus_str = active_plan["focus"]
                if ":" in str(_focus_str):
                    _g, _e = _focus_str.split(":", 1)
                else:
                    _g, _e = self._FOCUS_LEGACY_MAP.get(
                        str(_focus_str).lower(), ("SPARRING", "sparring"))
                if _g.upper() == "SPARRING":
                    # Sparring = maintenance week — keeps all attributes
                    # warm. Full decay shield; gains remain low/thin
                    # (unchanged — sparring still distributes gains
                    # across 7 stats at normal per-stat rate).
                    _domain_stats = [
                        "boxing", "kicks", "clinch_striking",
                        "striking_defense", "takedowns",
                        "takedown_defense", "top_control",
                        "submissions", "guard", "cardio",
                        "strength", "chin", "recovery", "heart",
                        "fight_iq", "composure", "speed",
                    ]
                else:
                    _domain_stats = self._TRAINING_GROUPS.get(
                        _g.upper(), {}).get("domain", [str(_focus_str)])
                self._maintenance_system.record_training_camp_activity(
                    fid, _domain_stats, self._game_state.week_number,
                )

        # Cache invalidation parity — Block 1's apply_training_week fires
        # _clear_cache() per-fighter; this weekly path needs the same so
        # _convert_real_fighter rebuilds WebFighters with fresh _fighter_data stats.
        self._clear_cache()

        return report

    def store_fight_night(self, data: Dict[str, Any]) -> None:
        """Store fight night data server-side to avoid cookie size limits."""
        self._last_fight_night = data

    def get_fight_night(self) -> Dict[str, Any]:
        """Retrieve fight night data."""
        return self._last_fight_night

    def clear_fight_night(self) -> None:
        """Clear fight night data after use."""
        self._last_fight_night = {}

    def store_week_recap(self, recap: Dict[str, Any]) -> None:
        """Store week recap server-side to avoid cookie size limits."""
        self._last_week_recap = recap

    def get_week_recap(self) -> Dict[str, Any]:
        """Retrieve last week's recap data."""
        return self._last_week_recap

    def get_weekly_digest(self) -> Dict[str, Any]:
        """
        Generate a weekly training digest for Coach's Corner.
        Coach voice is archetype-specific — Striking/Grappling/S&C/Head Coach
        each have distinct personalities and observations.
        Used on both the dashboard and the week results recap.
        """
        import random
        if not self._game_state:
            return {}

        coach_name    = self._coach.get("name", "Coach")
        coach_rating  = self._coach.get("rating", 60)
        coach_spec    = self._coach.get("specialty", "MMA").lower()
        player_camp   = self.get_player_camp()

        # Map specialty to archetype
        if coach_spec in ("striking", "boxing", "kickboxing", "muay thai", "muay_thai"):
            archetype = "striking"
            icon      = "🥊"
        elif coach_spec in ("grappling", "wrestling", "bjj", "submissions"):
            archetype = "grappling"
            icon      = "🤼"
        elif coach_spec in ("s&c", "strength", "conditioning", "cardio"):
            archetype = "sc"
            icon      = "💪"
        else:
            archetype = "mma"
            icon      = "🧠"

        # Archetype-specific quote banks
        # Keyed by (archetype, situation)
        _QUOTES = {
            ("striking", "hard"):     [
                "Combinations. Not singles. We're building timing, not just power.",
                "Your hands are the sharpest weapon in that gym. Use them.",
                "Every session is a rep. Sharpen the tools.",
                "I want combinations until they're automatic. Then we talk power.",
            ],
            ("striking", "fresh"):    [
                "You're fresh. That means we go harder this week. No excuses.",
                "Good condition. Now let's see what you can do with it.",
                "Save the rest for after the belt. Right now, combinations.",
            ],
            ("striking", "tired"):    [
                "Body's talking. You listen to it. Smart fighters know the difference.",
                "Pull back the intensity. A sharp fighter beats a tired one every time.",
                "Recovery is part of the game. Don't fight me on this.",
            ],
            ("striking", "default"):  [
                "Keep the hands busy. Defense starts with offense.",
                "Footwork and timing. That's what wins fights.",
                "We're building something here. Trust the process.",
            ],
            ("grappling", "hard"):    [
                "Drill that double leg until it's muscle memory. We own the mat.",
                "Chain wrestling. Don't stop at the takedown — work for position.",
                "The fight goes to the ground on your terms, not theirs.",
                "Your guard retention is improving. Keep building those escapes.",
            ],
            ("grappling", "fresh"):   [
                "Fresh body means extra drilling today. Let's put the time in.",
                "Good. Now we sharpen the transitions. Guard to mount, mount to back.",
                "You're moving well. Let's make the takedown automatic.",
            ],
            ("grappling", "tired"):   [
                "Active recovery. Light drilling, flow rolling. Keep the feel.",
                "A tired body makes mistakes on the mat. Pull back.",
                "Rest isn't losing ground. It's protecting what we built.",
            ],
            ("grappling", "default"): [
                "Control the clinch, control the fight.",
                "Every session on the mat is an investment. Keep banking it.",
                "We're building a game that works from everywhere. Stay patient.",
            ],
            ("sc", "hard"):           [
                "Explosiveness translates to damage. You'll feel this fight night.",
                "Your base is getting stronger every week. Numbers don't lie.",
                "Power, conditioning, durability. We're building a machine.",
                "Last rounds are won in this gym right now. Remember that.",
            ],
            ("sc", "fresh"):          [
                "Great condition. Now let's push the ceiling this week.",
                "Low fatigue means we can load up. Don't leave anything in the gym.",
                "This is the window. Fresh body, hard week. Let's go.",
            ],
            ("sc", "tired"):          [
                "You're running hot. Walk, don't run. Active recovery.",
                "Overtrained is undertrained. Pull back this week.",
                "Your body built the engine. Now let it rest and run properly.",
            ],
            ("sc", "default"):        [
                "Conditioning is the one thing you can always control.",
                "Every fighter has skill. Not every fighter has your engine.",
                "The last round is where this work pays off. Keep going.",
            ],
            ("mma", "hard"):          [
                "Study the opponent. The fight's won before you step in the cage.",
                "Your IQ is your biggest weapon. Sharpen it.",
                "Trust the game plan. I've seen this opponent's patterns. We're ready.",
                "Composure under pressure separates champions. Build that this week.",
            ],
            ("mma", "fresh"):         [
                "Sharp mind, fresh body. This is your week to put it all together.",
                "Good condition. Now think your way through every session.",
                "Use this clarity. Map the game plan, trust the preparation.",
            ],
            ("mma", "tired"):         [
                "Mental clarity goes with physical fatigue. Pull back and reset.",
                "Rest is strategy. Come back sharper.",
                "A tired fighter makes emotional decisions. We need your mind clear.",
            ],
            ("mma", "default"):       [
                "The best fighter isn't always the most talented. It's the smartest.",
                "Every rep teaches the body. Every session teaches the mind.",
                "I've seen talent lose to preparation. Be prepared.",
            ],
        }

        observations = []
        highlights   = []

        for f in self.get_player_fighters():
            fid       = f.fighter_id
            plan      = self._fighter_training_plans.get(fid, {})

            # If fighter has a fight booked, use fight camp settings
            fight_plan = None
            for fight in self._scheduled_fights:
                if fight.get("fighter1_id") == fid or fight.get("fighter2_id") == fid:
                    if fight.get("training_focus"):
                        fight_plan = {
                            "focus":     fight["training_focus"],
                            "intensity": fight.get("intensity", "MODERATE"),
                            "is_fight_camp": True,
                        }
                    break

            active = fight_plan or plan or {}
            focus     = active.get("focus", "sparring")
            intensity = active.get("intensity", "MODERATE")
            is_fc     = active.get("is_fight_camp", False)
            fatigue   = getattr(f, 'fatigue', 0)
            wins      = getattr(f, 'wins', 0)
            losses    = getattr(f, 'losses', 0)

            # Determine situation for quote selection
            if fatigue > 65:
                situation = "tired"
            elif fatigue < 25:
                situation = "fresh"
            elif intensity in ("INTENSE", "EXTREME"):
                situation = "hard"
            else:
                situation = "default"

            # Pick archetype quote
            quote_key = (archetype, situation)
            quotes    = _QUOTES.get(quote_key, _QUOTES.get((archetype, "default"), ["Keep working."]))
            quote     = random.choice(quotes)

            # Status line
            # Avoid "Sparring:Sparring" — use friendly display names
            _FOCUS_DISPLAY = {
                "sparring":          "General MMA",
                "striking":          "Striking",
                "grappling":         "Grappling",
                "wrestling":         "Wrestling",
                "bjj":               "BJJ",
                "cardio":            "Cardio",
                "strength":          "Strength",
                "defense":           "Defense",
                "striking_defense":  "Striking Defense",
                "grappling_takedowns": "Grappling: Takedowns",
                "grappling_submissions": "Grappling: Submissions",
            }
            focus_label = _FOCUS_DISPLAY.get(focus, focus.replace("_", " ").title())
            intensity_emoji = {
                "REST": "😴", "LIGHT": "🚶", "MODERATE": "🏃",
                "INTENSE": "🔥", "EXTREME": "⚡"
            }.get(intensity.upper(), "🏋️")

            # Fatigue color
            if fatigue > 65:
                fatigue_color = "var(--blood-red)"
                fatigue_label = "Fatigued"
            elif fatigue > 40:
                fatigue_color = "var(--warning)"
                fatigue_label = "Tired"
            elif fatigue < 20:
                fatigue_color = "var(--neon-green)"
                fatigue_label = "Fresh"
            else:
                fatigue_color = "var(--text-muted)"
                fatigue_label = "Ready"

            observations.append({
                "fighter_id":    f.fighter_id,
                "fighter_name":  f.name,
                "quote":         quote,
                "focus":         focus_label,
                "intensity":     intensity.title(),
                "intensity_emoji": intensity_emoji,
                "fatigue":       fatigue,
                "fatigue_label": fatigue_label,
                "fatigue_color": fatigue_color,
                "situation":     situation,
                "record":        f"{wins}-{losses}",
                "is_fight_camp": is_fc,
            })

            # Highlight for serious warnings
            if fatigue > 75:
                highlights.append({
                    "icon":  "⚠️",
                    "color": "var(--blood-red)",
                    "text":  f"{f.name} is running dangerously hot — strongly consider REST",
                })

        # Surface fight-cancelled alerts from this week as one-shot
        # highlights. After the player advances past this week the
        # cancellation drops out of highlights naturally (week filter)
        # while persisting in the news feed for history.
        current_week = self._game_state.week_number if self._game_state else 1
        for _ni in self._news_items:
            if (_ni.get("category") == "fight_cancelled"
                and _ni.get("week") == current_week):
                highlights.append({
                    "icon":  "🚫",
                    "color": "var(--blood-red)",
                    "text":  _ni["headline"] + " Book a new opponent from the ladder.",
                })

        return {
            "coach_name":    coach_name,
            "coach_rating":  coach_rating,
            "coach_spec":    coach_spec,
            "archetype":     archetype,
            "icon":          icon,
            "observations":  observations,
            "highlights":    highlights,
        }

    def get_coach(self) -> Dict[str, Any]:
        """Get the player's hired coach data."""
        return dict(self._coach)

    # =========================================================================
    # RIVALRY DATA
    # =========================================================================

    def get_fighter_rivalries(self, fighter_id: str) -> List[Dict[str, Any]]:
        """
        Return serialized rivalry data for a fighter.
        Empty list if rivalry module unavailable or no rivalries exist.
        """
        if not RIVALRY_AVAILABLE:
            return []
        try:
            rsys      = get_rivalry_system()
            rivalries = rsys.get_active_rivalries(fighter_id)
            out = []
            for r in rivalries:
                score = r.score
                stage = get_heat_stage(score)
                out.append({
                    "opponent_id":   r.fighter2_id if r.fighter1_id == fighter_id else r.fighter1_id,
                    "opponent_name": r.fighter2_name if r.fighter1_id == fighter_id else r.fighter1_name,
                    "score":         score,
                    "stage":         stage.value,
                    "stage_display": stage.value.replace("_", " ").title(),
                    "desc":          get_heat_description(score),
                    "fights":        r.fights,
                    "intensity":     r.intensity.name.title(),
                    "type":          r.rivalry_type.value.replace("_", " ").title(),
                    "heat_color":    {
                        "neutral":   "#6b7280",
                        "tension":   "#3b82f6",
                        "bad_blood": "#f59e0b",
                        "heated":    "#ef4444",
                        "war":       "#dc2626",
                    }.get(stage.value, "#6b7280"),
                })
            return sorted(out, key=lambda x: x["score"], reverse=True)
        except Exception as exc:
            print(f"⚠️ get_fighter_rivalries failed: {exc}")
            return []

    def get_fighter_reigns(self, fighter_id: str) -> List[Dict[str, Any]]:
        """
        Return serialized championship reign data for a fighter.
        Empty list if no belt history exists or fighter never held a belt.
        Reigns ordered chronologically (oldest first).
        Ship #29: data flows world-gen → bridge → save/load → routes; Ship
        #30 will surface this on fighter_profile.html.
        """
        if self._belt_history is None:
            return []
        try:
            reigns = self._belt_history.get_fighter_reigns(fighter_id)
            out = []
            for r in reigns:
                out.append({
                    "weight_class":        r.weight_class,
                    "won_week":            r.won_week,
                    "won_event":           r.won_event,
                    "won_from":            r.won_from,
                    "won_from_name":       r.won_from_name,
                    "won_method":          r.won_method,
                    "successful_defenses": r.successful_defenses,
                    "lost_week":           r.lost_week,
                    "lost_event":          r.lost_event,
                    "lost_to":             r.lost_to,
                    "lost_to_name":        r.lost_to_name,
                    "lost_method":         r.lost_method,
                    "is_active":           r.is_active,
                })
            out.sort(key=lambda x: x["won_week"])
            return out
        except Exception as exc:
            print(f"⚠️ get_fighter_reigns failed: {exc}")
            return []

    def get_rivalry_between(self, fighter1_id: str, fighter2_id: str) -> Optional[Dict[str, Any]]:
        """Get rivalry data between two specific fighters (for pre-fight display)."""
        if not RIVALRY_AVAILABLE:
            return None
        try:
            rsys    = get_rivalry_system()
            rivalry = rsys.get_rivalry(fighter1_id, fighter2_id)
            if not rivalry:
                return None
            score = rivalry.score
            stage = get_heat_stage(score)
            return {
                "score":    score,
                "stage":    stage.value,
                "desc":     get_heat_description(score),
                "fights":   rivalry.fights,
                "intensity": rivalry.intensity.name.title(),
            }
        except Exception as exc:
            print(f"⚠️ get_rivalry_between failed: {exc}")
            return None

    # =========================================================================
    # ECONOMY — BASIC CASH/OVERHEAD/PURSE SYSTEM
    # =========================================================================

    _PURSE_BY_TIER: Dict[str, int] = {
        "champion": 500000, "top_5": 150000, "top_10": 75000,
        "top_15": 40000, "ranked": 30000, "unranked": 18000, "debut": 12000,
    }
    _WEEKLY_OVERHEAD: Dict[str, int] = {
        "GARAGE": 125, "LOCAL": 750, "REGIONAL": 2500,
        "NATIONAL": 7500, "ELITE": 18750,
    }

    def _get_camp_tier(self) -> str:
        camp = self.get_player_camp()
        return camp.tier.upper() if camp else "GARAGE"

    def get_camp_finances(self) -> Dict[str, Any]:
        tier          = self._get_camp_tier()
        overhead      = self._WEEKLY_OVERHEAD.get(tier, 125)
        roster_size   = len(self.get_player_fighters())
        fighter_cost  = {"GARAGE": 0, "LOCAL": 25, "REGIONAL": 75, "NATIONAL": 200, "ELITE": 400}.get(tier, 0)
        coach_salary  = self._coach_contract.get("salary", 0) if self._coach_contract else 0
        total_weekly  = overhead + roster_size * fighter_cost + coach_salary
        balance       = self._camp_balance
        return {
            "balance":              balance,
            "weekly_overhead":      total_weekly,
            "camp_overhead":        overhead,
            "fighter_costs":        roster_size * fighter_cost,
            "coach_salary":         coach_salary,
            "roster_size":          roster_size,
            "weeks_runway":         balance // total_weekly if total_weekly > 0 else 999,
            "total_purses_earned":  self._total_purses_earned,
            "week_purses_earned":   self._week_purses_earned,
            "total_overhead_paid":  self._total_overhead_paid,
        }

    def _deduct_weekly_overhead(self) -> int:
        tier         = self._get_camp_tier()
        overhead     = self._WEEKLY_OVERHEAD.get(tier, 125)
        roster       = len(self.get_player_fighters())
        fighter_cost = {"GARAGE": 0, "LOCAL": 25, "REGIONAL": 75, "NATIONAL": 200, "ELITE": 400}.get(tier, 0)
        fighter_total = roster * fighter_cost

        # Ship C2: coach salary is part of weekly overhead now
        coach_salary = self._coach_contract.get("salary", 0) if self._coach_contract else 0

        total = overhead + fighter_total + coach_salary

        # Ship C2: check if balance covers everything; if not, mark coach skipped
        if self._camp_balance >= total:
            self._camp_balance        -= total
            self._total_overhead_paid += total
        else:
            # Pay what we can on non-coach overhead first; coach paycheck gets skipped
            non_coach = overhead + fighter_total
            paid_non_coach = min(self._camp_balance, non_coach)
            self._camp_balance        = max(0, self._camp_balance - non_coach)
            self._total_overhead_paid += paid_non_coach
            # Skip coach paycheck — increments skipped_paychecks for morale decay
            if self._coach_contract and coach_salary > 0:
                self._coach_contract["skipped_paychecks"] = (
                    self._coach_contract.get("skipped_paychecks", 0) + 1
                )
                self._news_items.insert(0, {
                    "headline": f"⚠️ Couldn't cover {self._coach_contract['name']}'s ${coach_salary} paycheck this week",
                    "category": "finance",
                    "week":     self._game_state.week_number if self._game_state else 0,
                })

        self._camp_cache.clear()   # balance changed — invalidate cache
        return total

    def _pay_fight_purse(self, fight_result: Dict[str, Any]) -> int:
        """
        Pay out the fight purse to the player camp.
        Uses the negotiated purse if one was set (real money decision),
        otherwise falls back to rank-based defaults.
        """
        player_ids  = {f.fighter_id for f in self.get_player_fighters()}
        winner_id   = fight_result.get("winner_id", "")
        loser_id    = fight_result.get("loser_id", "")
        player_won  = winner_id in player_ids
        player_lost = loser_id  in player_ids
        if not player_won and not player_lost:
            return 0

        # If the fight had a negotiated purse, use it — that was the deal
        negotiated = fight_result.get("purse")
        if negotiated and negotiated > 0:
            base = negotiated
        else:
            # Rank-based default
            RANK_PURSES = {
                0: 150_000, 1: 80_000, 2: 65_000, 3: 55_000,
                4: 45_000,  5: 38_000, 6: 30_000, 7: 25_000,
                8: 22_000,  9: 20_000, 10: 18_000, 11: 16_000,
                12: 14_000, 13: 13_000, 14: 12_000, 15: 11_000,
            }
            def _rank_purse(fid):
                if not self._game_state: return 9_000
                f = self._game_state.get_fighter(fid)
                if not f: return 9_000
                r = self._get_fighter_rank(f)
                return RANK_PURSES.get(r, 9_000) if r is not None else 9_000

            fid = winner_id if player_won else loser_id
            base = _rank_purse(fid)

        if player_won:
            earned = base * 2   # show + win bonus combined
            if fight_result.get("is_fotn"):        earned += 50_000
            if fight_result.get("is_title_fight"): earned = int(earned * 2.0)
        else:
            earned = base       # show money only

        # Popularity multiplier — popular fighters earn more
        player_fid = fight_result.get("winner_id") if player_won else fight_result.get("loser_id")
        if player_fid and self._game_state:
            pf = self._game_state.get_fighter(player_fid)
            pop = getattr(pf, 'popularity', 10) if pf else 10
            # +0% at pop 10 (baseline), up to +50% at pop 100
            pop_mult = 1.0 + (pop - 10) / 180.0
            earned = int(earned * max(0.85, pop_mult))

        self._camp_balance        += earned
        self._total_purses_earned += earned
        self._week_purses_earned  += earned

        # Ship S1: sponsor fight bonuses (using player_fid from earlier scope)
        if player_fid and self._game_state:
            for s in (self._game_state._fighter_data.get(
                    player_fid, {}).get("sponsors", []) or []):
                brand = _SPONSOR_BY_ID.get(s.get("sponsor_id", ""))
                if brand:
                    self._camp_balance        += brand["fight_bonus"]
                    self._total_purses_earned += brand["fight_bonus"]
                    self._week_purses_earned  += brand["fight_bonus"]

        self._camp_cache.clear()   # balance changed — invalidate cache
        return earned

    # =========================================================================
    # SCOUTING — STRENGTHS / WEAKNESSES / REPORT
    # =========================================================================

    def get_scouting_report(self, fighter_id: str) -> Optional[Dict[str, Any]]:
        fighter = self.get_fighter(fighter_id)
        if not fighter:
            return None
        try:
            if not SCOUTING_AVAILABLE:
                raise ImportError("scouting not loaded")
            strengths  = get_fighter_strengths(fighter, top_n=3)
            weaknesses = get_fighter_weaknesses(fighter, top_n=3)
            potential_data = None
            try:
                pa = assess_potential(fighter)
                potential_data = {
                    "grade": pa.potential_grade,
                        "display_grade": ceiling_to_display_grade(pa.potential_ceiling),
                        "grade_color": grade_color(ceiling_to_display_grade(pa.potential_ceiling)),
                        "ceiling": pa.potential_ceiling,
                    "upside": pa.upside, "years_to_peak": pa.years_to_peak,
                    "description": POTENTIAL_GRADES.get(pa.potential_grade, {}).get("description", ""),
                    "worth_developing": pa.is_worth_developing,
                }
            except Exception:
                pass
            return {
                "strengths":  [{"attr": s.attribute, "value": s.value, "category": s.category, "desc": s.description} for s in strengths],
                "weaknesses": [{"attr": w.attribute, "value": w.value, "category": w.category, "desc": w.description} for w in weaknesses],
                "potential":  potential_data,
            }
        except ImportError:
            attr_list = [
                ("Strength","strength"),("Speed","speed"),("Cardio","cardio"),("Chin","chin"),
                ("Boxing","boxing"),("Kicks","kicks"),("Takedowns","takedowns"),
                ("Submissions","submissions"),("Heart","heart"),("Fight IQ","fight_iq"),
                ("Composure","composure"),("Guard","guard"),
            ]
            scored = sorted(
                [(n, getattr(fighter, k, fighter.overall_rating)) for n, k in attr_list],
                key=lambda x: x[1], reverse=True
            )
            return {
                "strengths":  [{"attr": n, "value": v, "category": "", "desc": ""} for n, v in scored[:3]],
                "weaknesses": [{"attr": n, "value": v, "category": "", "desc": ""} for n, v in scored[-3:]],
                "potential":  None,
            }
        except Exception as exc:
            print(f"⚠️ get_scouting_report failed: {exc}")
            return None

    # =========================================================================
    # POST-FIGHT INTERVIEWS
    # =========================================================================

    _WINNER_CHOICES = [
        ("humble",         "Humble — Thank the team, respect the opponent"),
        ("trash_talk",     "Trash Talk — Call out the division"),
        ("call_out",       "Call Out — Demand a specific fight"),
        ("respectful",     "Respectful — Honor both fighters"),
        ("emotional",      "Emotional — Let the moment show"),
        ("thank_sponsors", "Thank Sponsors — Shoutout and earn bonus"),
    ]
    _LOSER_CHOICES = [
        ("accept_defeat",     "Accept Defeat — Show class, move on"),
        ("demand_rematch",    "Demand Rematch — Want another shot"),
        ("cite_injury",       "Cite Injury — Mention camp problems"),
        ("question_decision", "Question Decision — Challenge the judges"),
        ("retirement_hint",   "Retirement Hint — Suggest you may be done"),
        ("blame_camp",        "Blame Camp — Put it on the corner"),
    ]

    def get_pending_interviews(self) -> List[Dict[str, Any]]:
        pending    = []
        seen_fids  = set()  # Deduplicate — same fight can appear in merged events
        player_ids = {f.fighter_id for f in self.get_player_fighters()}
        for event in self._completed_events[-10:]:
            for fight in event.get("fights", []):
                fid  = fight.get("fight_id") or f"fight_{fight.get('winner_id','')}"
                if fid in seen_fids:
                    continue
                iv   = self._fight_interviews.get(fid, {})
                wid  = fight.get("winner_id", "")
                lid  = fight.get("loser_id",  "")
                added = False
                if wid in player_ids and not iv.get("winner_done"):
                    pending.append({"fight_id": fid, "fighter_id": wid,
                        "fighter_name": fight.get("winner_name", ""),
                        "opponent_id": lid, "opponent_name": fight.get("loser_name", ""),
                        "role": "winner", "method": fight.get("method", ""),
                        "choices": self._WINNER_CHOICES, "event_name": event.get("event_name", ""),
                        "fight_summary": f"{'Win' if wid in player_ids else 'Loss'} vs {fight.get('loser_name','opponent')} ({fight.get('method','DEC')})"})
                    added = True
                if lid in player_ids and not iv.get("loser_done"):
                    pending.append({"fight_id": fid, "fighter_id": lid,
                        "fighter_name": fight.get("loser_name", ""),
                        "opponent_id": wid, "opponent_name": fight.get("winner_name", ""),
                        "role": "loser", "method": fight.get("method", ""),
                        "choices": self._LOSER_CHOICES, "event_name": event.get("event_name", ""),
                        "fight_summary": f"Loss vs {fight.get('winner_name','opponent')} ({fight.get('method','DEC')})"})
                    added = True
                if added:
                    seen_fids.add(fid)

        # Cap at 1 — only show the most recent pending interview.
        # Older interviews expire naturally; players shouldn't face
        # a backlog of stale post-fight obligations.
        if pending:
            pending = pending[-1:]

        return pending

    def process_interview(self, fight_id: str, fighter_id: str,
                          role: str, choice: str,
                          call_out_id: Optional[str] = None) -> Dict[str, Any]:
        if fight_id not in self._fight_interviews:
            self._fight_interviews[fight_id] = {}
        iv = self._fight_interviews[fight_id]

        # Resolve fighter name and week BEFORE try block so fallback can use them
        fighter = self.get_fighter(fighter_id)
        fname   = fighter.name if fighter else "Fighter"
        week    = self.week_number

        try:
            from interviews import InterviewManager, WinnerResponse, LoserResponse, WINNER_TEMPLATES, LOSER_TEMPLATES
            import random
            mgr     = InterviewManager()
            opp_id, opp_name, method = "", "", "DEC"
            for ev in self._completed_events:
                for f in ev.get("fights", []):
                    fid2 = f.get("fight_id") or f"fight_{f.get('winner_id','')}"
                    if fid2 == fight_id:
                        if role == "winner":
                            opp_id = f.get("loser_id",""); opp_name = f.get("loser_name","")
                        else:
                            opp_id = f.get("winner_id",""); opp_name = f.get("winner_name","")
                        method = f.get("method","DEC"); break
            co_fighter = self.get_fighter(call_out_id) if call_out_id else None
            co_name    = co_fighter.name if co_fighter else ""
            if role == "winner":
                resp   = WinnerResponse(choice)
                result = mgr.process_winner_response(
                    fighter_id=fighter_id, fighter_name=fname, opponent_id=opp_id,
                    opponent_name=opp_name, response=resp, fight_id=fight_id, week=week,
                    call_out_target_id=call_out_id, call_out_target_name=co_name)
                templates = WINNER_TEMPLATES.get(resp, [])
                iv["winner_done"] = True
            else:
                resp   = LoserResponse(choice)
                result = mgr.process_loser_response(
                    fighter_id=fighter_id, fighter_name=fname, opponent_id=opp_id,
                    opponent_name=opp_name, response=resp, fight_id=fight_id,
                    week=week, method=method)
                templates = LOSER_TEMPLATES.get(resp, [])
                iv["loser_done"] = True
            tpl   = random.choice(templates) if templates else f'{fname}: "No comment."'
            quote = tpl.format(name=fname, opponent=opp_name,
                               target=co_name, sponsors="our sponsors")
            bonus = getattr(result, "sponsor_bonus_earned", 0)
            if bonus: self._camp_balance += bonus
            pop   = getattr(result, "popularity_change", 0)
            if abs(pop) >= 5:
                sign = "+" if pop > 0 else ""
                self._news_items.insert(0, {
                    "headline": f"📣 {fname}: \"{quote[:70]}{'...' if len(quote)>70 else ''}\" ({sign}{pop} pop)",
                    "category": "interview", "week": week})
            iv.setdefault("quotes", []).append(
                {"fighter": fname, "role": role, "choice": choice,
                 "quote": quote, "pop_delta": pop, "bonus": bonus})
            return {"success": True, "quote": quote,
                    "headline": getattr(result, "headline", ""),
                    "pop_delta": pop, "bonus": bonus,
                    "rivalry_created": getattr(result, "rivalry_created", False),
                    "opponent_response": getattr(result, "opponent_response", None)}
        except ImportError:
            fallbacks = {
                "humble":         f'"{fname}: I just thank God and my team."',
                "trash_talk":     f'"{fname}: Nobody in this division can touch me!"',
                "accept_defeat":  f'"{fname}: Credit where it\'s due. Back to the gym."',
                "demand_rematch": f'"{fname}: I want the rematch!"',
            }
            iv[f"{role}_done"] = True
            quote = fallbacks.get(choice, f'"{fname}: No comment."')
            return {"success": True, "quote": quote, "pop_delta": 0, "bonus": 0}
        except Exception as exc:
            print(f"⚠️ process_interview failed: {exc}")
            return {"success": False, "error": str(exc)}

    def get_fight_quotes(self, fight_id: str) -> List[Dict[str, Any]]:
        return self._fight_interviews.get(fight_id, {}).get("quotes", [])

    # =========================================================================
    # MEDIA REACTIONS
    # =========================================================================

    def _generate_media_reactions(self, fight_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            if not MEDIA_AVAILABLE:
                return []
            player_ids = {f.fighter_id for f in self.get_player_fighters()}
            is_title   = fight_result.get("is_title_fight", False)
            method     = fight_result.get("method", "DEC")
            involves   = fight_result.get("winner_id","") in player_ids or fight_result.get("loser_id","") in player_ids
            if not (is_title or involves or method in ("KO","TKO","SUB")):
                return []
            winner = None
            if self._game_state:
                winner = self._game_state.get_fighter(fight_result.get("winner_id",""))
            return generate_fight_reactions(
                method=method,
                winner_name=fight_result.get("winner_name",""),
                loser_name=fight_result.get("loser_name",""),
                round_finished=fight_result.get("round_finished", 3),
                is_title_fight=is_title,
                is_main_event=fight_result.get("is_main_event", False),
                was_upset=False,
                winner_age=getattr(winner,"age",28) if winner else 28,
                winner_fights=(getattr(winner,"wins",0)+getattr(winner,"losses",0)) if winner else 0,
                winner_streak=getattr(winner,"win_streak",0) if winner else 0,
                winner_wins=getattr(winner,"wins",0) if winner else 0,
                winner_losses=getattr(winner,"losses",0) if winner else 0,
            )
        except Exception as exc:
            print(f"⚠️ Media reactions failed: {exc}")
            return []

    def get_media_reactions(self, fight_id: str) -> List[Dict[str, Any]]:
        return self._media_reactions.get(fight_id, [])

    # =========================================================================
    # AMATEUR CIRCUIT — WEEKLY ADVANCEMENT
    # =========================================================================

    def _get_coach_region(self) -> str:
        """Map coach's nationality/location to an amateur region."""
        # Coach specialty doesn't have nationality — use camp location
        location = ""
        if self._game_state:
            camp = self._game_state.get_camp(self._game_state.player_camp_id)
            if camp:
                location = getattr(camp, 'location', '') or ''

        # Try to map camp location country to amateur region
        try:
            from amateur import NATIONALITY_TO_REGION
            for country, region in NATIONALITY_TO_REGION.items():
                if country.lower() in location.lower():
                    return region
        except ImportError:
            pass

        # Fallback: map by coach specialty (cultural association)
        specialty_region = {
            "bjj":       "Americas",   # Brazil/USA BJJ culture
            "wrestling": "Americas",   # USA wrestling culture
            "boxing":    "Americas",   # Boxing Belt USA/Mexico
            "muay thai": "Asia",
            "kicks":     "Asia",
            "sambo":     "Europe",
        }
        specialty = self._coach.get("specialty", "").lower()
        return specialty_region.get(specialty, "Americas")

    def _advance_amateur_week(self, week: int) -> Dict[str, Any]:
        """
        Process one week of the amateur circuit.
        - Runs scheduled tournaments
        - Ages fighters annually
        - Triggers AI signing of elite prospects
        - Fires coach scouting tip if relevant
        Returns summary of what happened.
        """
        import random
        sys = self._get_amateur_system()
        if not sys:
            return {}

        try:
            events = sys.process_week(week)
        except Exception as e:
            print(f"⚠️ Amateur process_week failed: {e}")
            return {}

        newly_eligible = events.get("newly_eligible", [])
        tournaments_run = events.get("tournaments_run", [])

        # Stamp eligible_week so the signing window works correctly
        sys2 = self._get_amateur_system()
        if sys2 and newly_eligible:
            for fid in newly_eligible:
                a = sys2.amateurs.get(fid)
                if a and not hasattr(a, 'eligible_week'):
                    a.eligible_week = week

        if not tournaments_run:
            return events

        # ── AI signing — Elite/High potential tournament winners ───────
        # Only sign fighters who just won a tournament (champions)
        # AI camps are selective — they prioritise Elite > High potential
        if self._game_state:
            player_camp_id = self._game_state.player_camp_id
            ai_camps = [
                c for c in self._game_state.camps.values()
                if c.camp_id != player_camp_id and getattr(c, 'is_active', True)
            ]

            for result in tournaments_run:
                champion_id = getattr(result, 'champion_id', None)
                champion_name = getattr(result, 'champion_name', '')
                if not champion_id:
                    continue

                amateur = sys.amateurs.get(champion_id)
                if not amateur or not amateur.is_active or amateur.turned_pro:
                    continue
                if not amateur.is_pro_eligible:
                    continue

                # AI signing aggressiveness by grade:
                # Elite/High: always — promotions want talent
                # Average: 80% chance — solid filler fighters
                # Low: 60% chance — cards need prelim fighters
                # Limited: 30% chance — desperation/thin cards
                if amateur.potential_grade == "Elite":
                    pass  # Always sign
                elif amateur.potential_grade == "High":
                    pass  # Always sign
                elif amateur.potential_grade == "Average":
                    if random.random() > 0.80:
                        continue
                elif amateur.potential_grade == "Low":
                    if random.random() > 0.60:
                        continue
                else:
                    # Limited/Unknown — 30% chance, keeps cards full
                    if random.random() > 0.30:
                        continue

                # AI camp signs this fighter — pick based on camp personality
                # Each camp scores the fighter according to its archetype
                # Camp with highest score wins the signing
                eligible_camps = [c for c in ai_camps if
                                  getattr(c, 'fighter_count', 0) <
                                  getattr(c, 'max_fighters', 6)]
                if not eligible_camps:
                    continue

                # Score this fighter for each eligible camp
                camp_scores = []
                for ec in eligible_camps:
                    score = self._score_fighter_for_camp(amateur, ec.camp_id)
                    if score > 0:
                        camp_scores.append((score, ec))

                if not camp_scores:
                    # No camp wants them — fall back to random
                    signing_camp = random.choice(eligible_camps)
                else:
                    # Weighted random from top scorers (not always highest)
                    # This creates realistic variation
                    camp_scores.sort(key=lambda x: x[0], reverse=True)
                    top_camps = camp_scores[:5]  # Consider top 5
                    weights   = [s for s, _ in top_camps]
                    total_w   = sum(weights)
                    if total_w > 0:
                        r = random.uniform(0, total_w)
                        cumulative = 0
                        signing_camp = top_camps[0][1]
                        for w, ec in top_camps:
                            cumulative += w
                            if r <= cumulative:
                                signing_camp = ec
                                break
                    else:
                        signing_camp = random.choice(eligible_camps)

                # Mark as turned pro — remove from amateur pool
                # Give player a 3-week window to sign Elite prospects first
                eligible_since = getattr(amateur, 'eligible_week', week)
                window = 3 if amateur.potential_grade == "Elite" else 1
                if week < eligible_since + window:
                    continue  # Player still has first crack at Elite prospects

                amateur.turned_pro = True
                amateur.is_active  = False

                self._news_items.insert(0, {
                    "headline": f"🏆 {champion_name} "
                                f"(Grade {ceiling_to_display_grade(getattr(amateur,'potential_ceiling',70))}) "
                                f"signs pro contract with {signing_camp.name}",
                    "category": "signing",
                    "week":     week,
                })

        # ── Coach scouting tip ─────────────────────────────────────────
        # If a tournament ran in the coach's region and produced
        # an eligible fighter, notify the player
        coach_region = self._get_coach_region()
        player_ids_signed = {
            f.fighter_id for f in self.get_player_fighters()
        }

        for result in tournaments_run:
            if getattr(result, 'region', '') != coach_region:
                continue

            # Look for newly eligible fighters in this region's result
            for fid in getattr(result, 'newly_eligible', []):
                amateur = sys.amateurs.get(fid)
                if not amateur or amateur.turned_pro:
                    continue
                if amateur.potential_grade not in ("Elite", "High", "Average"):
                    continue

                dg = ceiling_to_display_grade(getattr(amateur, 'potential_ceiling', 70))
                grade_emoji = {"A+":"⭐⭐⭐","A":"⭐⭐⭐","A-":"⭐⭐",
                               "B+":"⭐⭐","B":"⭐⭐","B-":"⭐",
                               "C+":"⭐","C":"⭐","C-":"","D":""}.get(dg, "⭐")

                self._news_items.insert(0, {
                    "headline": f"👀 Scout Report: {amateur.name} ({amateur.weight_class}, "
                                f"{amateur.wins}-{amateur.losses}) just turned pro-eligible "
                                f"in {coach_region}. {grade_emoji} Grade {dg} — "
                                f"worth a look.",
                    "category": "scouting",
                    "week":     week,
                    "amateur_id": fid,
                })
                break  # One tip per week max

        # ── Schedule next year's tournaments when year ends ────────────
        if week % 52 == 0:
            next_year = (week // 52) + 1
            try:
                sys.schedule_year_tournaments(
                    year=next_year,
                    start_week=week + 1
                )
            except Exception:
                pass

        return events

    # =========================================================================
    # AGING SYSTEM
    # =========================================================================

    def _advance_aging_week(self, week: int) -> None:
        """
        Called every advance_week.
        Annual aging fires on week % 52 == 0.
        Applies stat decay, career phase transitions, retirement checks.
        """
        if not self._game_state or not AGING_AVAILABLE or not self._aging_system:
            return

        # Only process once per year
        current_year = max(1, week // 52)
        if week % 52 != 0:
            return

        import random
        retiring = []

        for fid, fighter in list(self._game_state.fighters.items()):
            if not fighter.is_active:
                continue

            age = getattr(fighter, 'age', 25)
            if age < 33:
                continue  # No decline before 33

            # Check if already processed this year
            if not self._aging_system.should_process_annual_aging(fid, current_year):
                continue

            ko_losses = getattr(fighter, 'ko_losses', 0)
            lose_streak = self._get_fighter_lose_streak(fighter)
            is_champion = getattr(fighter, 'is_champion', False)
            total_fights = fighter.wins + fighter.losses
            morale = getattr(fighter, 'morale', 50)

            # Apply annual decline
            phase, changes = self._aging_system.process_birthday(
                fighter_id=fid,
                new_age=age,
                ko_losses=ko_losses,
            )

            # Write changes back
            for attr, delta in changes.items():
                if hasattr(fighter, attr) and delta != 0:
                    current = getattr(fighter, attr, 50)
                    setattr(fighter, attr, max(1, int(current + delta)))

            # Age the fighter
            if hasattr(fighter, 'age'):
                fighter.age = age + 1

            self._aging_system.mark_annual_aging_processed(fid, current_year)

            # Career phase transition news
            old_phase = get_career_phase(age - 1) if age > 1 else None
            new_phase = get_career_phase(age + 1)
            if old_phase and new_phase != old_phase:
                phase_msgs = {
                    "VETERAN": f"⏳ {fighter.name} enters the veteran phase of their career (Age {age+1})",
                    "TWILIGHT": f"🌅 {fighter.name} (Age {age+1}) is in the twilight of their career",
                }
                msg = phase_msgs.get(new_phase.name)
                if msg:
                    self._news_items.insert(0, {
                        "headline": msg,
                        "category": "career",
                        "week": week,
                    })

            # Retirement check — 35+
            if age >= 35:
                should_retire = self._aging_system.check_retirement(
                    fighter_id=fid,
                    age=age + 1,
                    lose_streak=lose_streak,
                    is_champion=is_champion,
                    total_fights=total_fights,
                    morale=morale,
                )
                if should_retire:
                    retiring.append((fighter, age + 1))

        # Process retirements
        for fighter, ret_age in retiring:
            fighter.is_active = False
            record = f"{fighter.wins}-{fighter.losses}"
            self._news_items.insert(0, {
                "headline": f"🥊 {fighter.name} ({record}) retires at age {ret_age}",
                "category": "retirement",
                "week": week,
            })
            # Update rankings to remove retired fighter
            self._update_rankings_after_fight(
                getattr(fighter, 'weight_class', ''))

    # =========================================================================
    # MAINTENANCE TRAINING
    # =========================================================================

    def _advance_maintenance_week(self, week: int) -> None:
        """
        Process weekly maintenance training for all player fighters.
        - Coaches passively boost their specialty
        - Idle stats decay gradually
        - Decay warnings surface in news
        """
        if not self._game_state or not MAINTENANCE_AVAILABLE or not self._maintenance_system:
            return

        player_fighters = self._game_state.get_player_fighters()
        if not player_fighters:
            return

        coach = self._coach
        coach_id   = coach.get("id",       "coach_0")
        coach_name = coach.get("name",     "Coach")
        coach_spec = coach.get("specialty","boxing")
        coach_rtg  = coach.get("rating",   60)

        player_camp_id = self._game_state.player_camp_id

        # Build fighter dicts for the maintenance system
        fighter_dicts = []
        camp_assignments = {}
        camp_coaches = {player_camp_id: [{
            "id":        coach_id,
            "name":      coach_name,
            "specialty": coach_spec,
            "rating":    coach_rtg,
        }]}

        for f in player_fighters:
            fdata = {}
            if f.fighter_id in self._game_state._fighter_data:
                fdata = self._game_state._fighter_data[f.fighter_id]
            fighter_dicts.append({
                "id":          f.fighter_id,
                "name":        f.name,
                "attributes":  {attr: getattr(f, attr, 50)
                                for attr in [
                                    "boxing","kicks","wrestling","bjj",
                                    "submissions","chin","cardio","strength",
                                    "speed","fight_iq","composure","heart",
                                ]},
                "fight_history": getattr(f, 'fight_history', []),
            })
            camp_assignments[f.fighter_id] = player_camp_id

        # Fighters in active fight camp are excluded from decay
        fighters_in_camp = {
            sf.get("fighter1_id") for sf in self._scheduled_fights
        } | {sf.get("fighter2_id") for sf in self._scheduled_fights}

        try:
            boosts, decays, warnings = process_weekly_maintenance(
                system          = self._maintenance_system,
                fighters        = fighter_dicts,
                camp_assignments= camp_assignments,
                camp_coaches    = camp_coaches,
                current_week    = week,
                fighters_in_camp= fighters_in_camp,
            )

            # Apply boosts to real fighters
            for boost in boosts:
                ftr = self._game_state.get_fighter(boost.fighter_id)
                if ftr and hasattr(ftr, boost.stat):
                    current = getattr(ftr, boost.stat, 50)
                    setattr(ftr, boost.stat, min(100, current + boost.amount))
                if boost.amount >= 2 and boost.specialty_match:
                    self._news_items.append({
                        "headline": f"💪 {boost.coach_name} strong session with "
                                    f"{boost.fighter_name} (+{boost.amount} {boost.stat})",
                        "category": "training",
                        "week":     week,
                    })

            # Apply decays to real fighters
            for decay in decays:
                ftr = self._game_state.get_fighter(decay.fighter_id)
                if ftr and hasattr(ftr, decay.stat):
                    current = getattr(ftr, decay.stat, 50)
                    setattr(ftr, decay.stat, max(1, current - decay.amount))
                _STAT_DISPLAY = {
                    "accuracy": "striking accuracy", "wrestling": "takedown game",
                    "td_defense": "takedown defense", "clinch": "clinch work",
                    "bjj": "ground game", "jiu_jitsu": "ground game",
                    "boxing": "boxing", "kicks": "kicks",
                    "clinch_striking": "clinch striking",
                    "striking_defense": "striking defense",
                    "takedowns": "takedowns", "takedown_defense": "takedown defense",
                    "top_control": "top control", "submissions": "submissions",
                    "composure": "composure", "fight_iq": "fight IQ",
                    "heart": "heart", "speed": "speed", "cardio": "cardio",
                    "chin": "chin", "recovery": "recovery", "strength": "strength",
                    "guard": "guard", "striking": "striking",
                }
                _stat_display = _STAT_DISPLAY.get(decay.stat, decay.stat.replace("_", " "))
                pass  # Decay surfaced on training page instead of news feed

            # Ship A: stitch maintenance boosts/decays onto each fighter's
            # current-week training history entry. _apply_weekly_training
            # already appended the entry earlier in advance_week — we look up
            # the most-recent entry per fighter and merge in maintenance data.
            # Guard against missing entries (edge case: fighter wasn't trained
            # this week for some reason).
            for boost in boosts:
                fid = boost.fighter_id
                if fid in self._training_history and self._training_history[fid]:
                    latest = self._training_history[fid][-1]
                    if latest.get("week") == week:
                        current = latest["coach_boosts"].get(boost.stat, 0.0)
                        latest["coach_boosts"][boost.stat] = current + float(boost.amount)
            for decay in decays:
                fid = decay.fighter_id
                if fid in self._training_history and self._training_history[fid]:
                    latest = self._training_history[fid][-1]
                    if latest.get("week") == week:
                        current = latest["decays"].get(decay.stat, 0.0)
                        latest["decays"][decay.stat] = current + float(decay.amount)

            # Warnings — only show severe ones so feed isn't flooded
            for warn in warnings:
                if warn.weeks_until_decay <= 1:
                    pass  # Decay warnings surfaced on training page instead

            # ── Terminal: maintenance summary ──────────────────────────
            if boosts or decays:
                b_str = ", ".join(f"{getattr(b,'fighter_name','?')[:8]} {getattr(b,'stat','?')}+{getattr(b,'amount',0):.1f}" for b in boosts[:3])
                d_str = ", ".join(f"{getattr(d,'fighter_name','?')[:8]} {getattr(d,'stat','?')}-{getattr(d,'amount',0):.1f}" for d in decays[:3])
                print(f"  🔧 [MAINTENANCE] Boosts: {b_str or 'none'} | Decays: {d_str or 'none'}")

        except Exception as e:
            print(f"  ⚠️ [MAINTENANCE] Failed: {e}")

        # ── AI Camp Coaching — passive gains every 2 weeks ────────────
        # AI fighters develop over time via their camp's coaching specialty.
        # Cadence + breadth lifted by the potential rework: every 2 weeks
        # (was 4), primary + secondary stat each pass (was primary only),
        # and the per-fighter potential ceiling now bounds growth.
        self._advance_ai_fighter_training(week)

    def _advance_ai_fighter_training(self, week: int) -> None:
        """
        Apply passive training gains to all AI fighters every 2 weeks.
        Each fighter trains TWO stats per pass: primary (full gain) +
        secondary (50%), both keyed off their fighting style. Young
        fighters gain more; veterans plateau. Ceiling is min(camp tier
        cap, fighter's stored potential).
        """
        if not self._game_state:
            return

        # AI fighter training focuses on their primary style stat
        # This is independent of coach archetypes — each fighter's style
        # determines what they drill between fights
        _STYLE_FOCUS = {
            "Orthodox Boxer":   "boxing",        "Muay Thai":       "kicks",
            "Kickboxer":        "kicks",          "Wrestler":        "takedowns",
            "BJJ Specialist":   "submissions",    "Ground & Pound":  "top_control",
            "Clinch Fighter":   "clinch_striking", "Counter Striker": "striking_defense",
            "Pressure Fighter": "boxing",          "Sambo":          "takedowns",
            "Brawler":          "strength",        "Judo":           "takedowns",
            "Point Fighter":    "fight_iq",        "Hybrid":         "fight_iq",
            "Karate":           "striking_defense","Sprawl & Brawl": "takedown_defense",
        }
        # Secondary stat per style — gets 50% of the primary's gain.
        # Picks a complementary attr that the style realistically drills.
        _STYLE_SECONDARY = {
            "Orthodox Boxer":   "striking_defense",
            "Muay Thai":        "clinch_striking",
            "Kickboxer":        "striking_defense",
            "Wrestler":         "takedown_defense",
            "BJJ Specialist":   "guard",
            "Ground & Pound":   "takedowns",
            "Clinch Fighter":   "top_control",
            "Counter Striker":  "fight_iq",
            "Pressure Fighter": "cardio",
            "Sambo":            "submissions",
            "Brawler":          "chin",
            "Judo":             "top_control",
            "Point Fighter":    "speed",
            "Hybrid":           "composure",
            "Karate":           "speed",
            "Sprawl & Brawl":   "striking_defense",
        }

        player_camp_id = self._game_state.player_camp_id

        for camp in self._game_state.camps.values():
            if camp.camp_id == player_camp_id:
                continue  # Player fighters handled separately

            # Get camp tier cap
            tier = getattr(camp, 'tier', 'LOCAL').upper()
            tier_cap = {"GARAGE": 65, "LOCAL": 72, "REGIONAL": 80,
                        "NATIONAL": 90, "ELITE": 100}.get(tier, 72)

            for fid in getattr(camp, 'fighter_ids', []):
                fighter = self._game_state.get_fighter(fid)
                if not fighter or not fighter.is_active:
                    continue

                age = getattr(fighter, 'age', 28)
                style = getattr(fighter, 'fighting_style', 'Orthodox Boxer')
                focus_attr = _STYLE_FOCUS.get(style, 'fight_iq')
                secondary_attr = _STYLE_SECONDARY.get(style, 'composure')

                # Age modifier: young fighters improve faster
                if age < 24:
                    base_gain = 0.8
                elif age < 28:
                    base_gain = 0.5
                elif age < 33:
                    base_gain = 0.3
                else:
                    base_gain = 0.1  # Veterans plateau

                # Per-fighter potential bounds growth alongside tier cap.
                ovr_now = getattr(fighter, 'overall_rating', 60)
                stored_potential = self._game_state._fighter_data.get(fid, {}).get(
                    "potential", ovr_now + 8)
                effective_cap = min(tier_cap, int(stored_potential))

                # Train both primary (full gain) and secondary (50%).
                # Stats live in _fighter_data (Ship #32) — writes here.
                _ai_fdata = self._game_state._fighter_data.get(fid, {})
                for attr, mult in ((focus_attr, 1.0), (secondary_attr, 0.5)):
                    current = float(_ai_fdata.get(attr, 60))
                    gain = base_gain * mult
                    # Athletic vs technical per-stat multiplier — mirrors
                    # _diminishing_gain on the player side.
                    if attr in self._ATHLETIC_BASE_STATS:
                        gain *= 0.5
                    elif attr in self._TECHNICAL_STATS:
                        gain *= 1.2
                    if current >= effective_cap:
                        gain *= max(0.1, 1 - (current - effective_cap) * 0.1)
                    if gain > 0.05:
                        if fid in self._game_state._fighter_data:
                            self._game_state._fighter_data[fid][attr] = round(
                                min(100.0, current + gain), 2)

                # Style-weighted OVR — see _compute_ovr for weight vectors.
                fighter.overall_rating = self._compute_ovr(fighter)

        # Sample output to show AI is developing
        if self._game_state:
            import random as _airand
            ai_fighters = [f for f in self._game_state.fighters.values()
                          if f.is_active and f.camp_id != self._game_state.player_camp_id
                          and hasattr(f, 'overall_rating')]
            if ai_fighters:
                sample = _airand.sample(ai_fighters, min(4, len(ai_fighters)))
                s = " | ".join(f"{f.name[:10]}:{f.overall_rating}" for f in sample)
                print(f"  🌍 [AI DEV week {week}] Sample OVRs → {s}")

    _WATCH_CATEGORIES = [
        ("SIGN_TARGET","📝","Sign Target"),("OPPONENT","⚔️","Opponent"),
        ("RIVAL","👊","Rival"),("PROSPECT","⭐","Prospect"),("THREAT","⚠️","Threat"),
        ("SCOUT","🔍","Scout"),("AVOID","🚫","Avoid"),("FAVORITE","❤️","Favorite"),
    ]

    def get_watchlist(self) -> List[Dict[str, Any]]:
        result = []
        for fid, entry in self._watchlist.items():
            live = self.get_fighter(fid)
            e    = dict(entry)
            if live:
                e.update({"record_str": live.record_str, "overall_rating": live.overall_rating,
                           "ranking": live.ranking, "is_champion": live.is_champion,
                           "weight_class": live.weight_class})
            result.append(e)
        prio = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}
        result.sort(key=lambda x: (prio.get(x.get("priority","NONE"), 3), x.get("fighter_name","")))
        return result

    def watchlist_add(self, fighter_id: str, category: str = "SCOUT", priority: str = "NONE") -> Dict[str, Any]:
        if fighter_id in self._watchlist:
            return {"success": False, "msg": "Already on watchlist"}
        fighter = self.get_fighter(fighter_id)
        if not fighter:
            return {"success": False, "msg": "Fighter not found"}
        from datetime import datetime
        icons = {k: ic for k, ic, _ in self._WATCH_CATEGORIES}
        self._watchlist[fighter_id] = {
            "fighter_id": fighter_id, "fighter_name": fighter.name,
            "category": category, "category_icon": icons.get(category,"🔍"),
            "priority": priority, "added_date": datetime.now().strftime("%b %d, %Y"),
            "notes": [], "tags": [], "weight_class": fighter.weight_class,
            "record_str": fighter.record_str, "overall_rating": fighter.overall_rating,
            "ranking": fighter.ranking, "is_champion": fighter.is_champion,
        }
        return {"success": True, "msg": f"{fighter.name} added to watchlist"}

    def watchlist_remove(self, fighter_id: str) -> Dict[str, Any]:
        if fighter_id not in self._watchlist:
            return {"success": False, "msg": "Not on watchlist"}
        name = self._watchlist.pop(fighter_id)["fighter_name"]
        return {"success": True, "msg": f"{name} removed from watchlist"}

    def watchlist_add_note(self, fighter_id: str, note: str) -> Dict[str, Any]:
        if fighter_id not in self._watchlist:
            return {"success": False, "msg": "Not on watchlist"}
        from datetime import datetime
        ts = datetime.now().strftime("%b %d")
        self._watchlist[fighter_id]["notes"].append(f"[{ts}] {note}")
        return {"success": True}

    # is_on_watchlist — real implementation below in watchlist section

    # =========================================================================

    def _weeks_out_for_fight(self, fighter_rank: Optional[int], opponent_rank: Optional[int]) -> int:
        """Calculate weeks of fight prep based on the best rank involved."""
        import random
        ranks = [r for r in [fighter_rank, opponent_rank] if r is not None]
        if not ranks:
            return random.randint(3, 4)     # Unranked debut
        best = min(ranks)
        if best == 0:                        # Title fight
            return random.randint(8, 12)
        elif best <= 3:
            return random.randint(7, 9)
        elif best <= 5:
            return random.randint(6, 8)
        elif best <= 10:
            return random.randint(5, 7)
        elif best <= 15:
            return random.randint(4, 6)
        else:
            return random.randint(3, 5)

    # =========================================================================
    # NEGOTIATION ENGINE
    # =========================================================================

    # ─────────────────────────────────────────────────────────────────────────
    # MATCHMAKING ENGINE — record & rank based, no ratings
    # ─────────────────────────────────────────────────────────────────────────

    def _fight_acceptance_probability(
        self,
        challenger_id: str,
        target_id: str,
    ) -> int:
        """
        Return 0-100 probability the target fighter accepts a challenge.

        Based entirely on record and rank — no ratings involved.
        Same formula applies to player challenges and AI vs AI matchmaking.

        Factors:
          1. Rank gap (spine of the system)
          2. Record quality modifier (finish rate, win streak)
          3. Desperation modifier (losing streak makes fighters more willing)
          4. Booked check (already scheduled = 0)
        """
        import random as _rnd

        if not self._game_state:
            return 50

        challenger = self._game_state.get_fighter(challenger_id)
        target     = self._game_state.get_fighter(target_id)
        if not challenger or not target:
            return 0

        # Already booked?
        for f in self._scheduled_fights:
            if f.get("fighter1_id") == target_id or f.get("fighter2_id") == target_id:
                return 0

        c_rank = self._get_fighter_rank(challenger)  # None = unranked
        t_rank = self._get_fighter_rank(target)       # 0 = champion

        # ── 1. Base probability from rank gap ─────────────────────────────
        def _tier(rank):
            if rank is None:       return "unranked"
            if rank == 0:          return "champion"
            if rank <= 5:          return "top5"
            if rank <= 10:         return "top10"
            return "ranked"

        c_tier = _tier(c_rank)
        t_tier = _tier(t_rank)

        BASE = {
            # (challenger_tier, target_tier): base acceptance %
            ("unranked",  "unranked"):  88,
            ("unranked",  "ranked"):    55,
            ("unranked",  "top10"):     30,
            ("unranked",  "top5"):       8,
            ("unranked",  "champion"):   3,
            ("ranked",    "unranked"):  75,
            ("ranked",    "ranked"):    72,
            ("ranked",    "top10"):     65,
            ("ranked",    "top5"):      45,
            ("ranked",    "champion"):  20,
            ("top10",     "unranked"):  60,
            ("top10",     "ranked"):    68,
            ("top10",     "top10"):     78,
            ("top10",     "top5"):      55,
            ("top10",     "champion"):  30,
            ("top5",      "unranked"):  45,
            ("top5",      "ranked"):    55,
            ("top5",      "top10"):     70,
            ("top5",      "top5"):      80,
            ("top5",      "champion"):  75,
            ("champion",  "top5"):      80,
            ("champion",  "top10"):     50,
            ("champion",  "ranked"):    30,
            ("champion",  "unranked"):  10,
        }
        prob = BASE.get((c_tier, t_tier), 50)

        # For same ranked tier, tighten based on actual position gap
        if c_rank is not None and t_rank is not None and t_rank > 0:
            gap = abs(c_rank - t_rank)
            if gap <= 2:   prob = min(prob + 10, 95)
            elif gap <= 5: pass  # no change
            elif gap <= 8: prob = max(prob - 10, 5)
            else:          prob = max(prob - 20, 3)

        # ── 2. Record quality modifier (challenger looks dangerous) ────────
        c_wins    = getattr(challenger, 'wins', 0)
        c_losses  = getattr(challenger, 'losses', 0)
        c_total   = c_wins + c_losses
        c_ko_wins = getattr(challenger, 'ko_wins', 0)
        c_sub_wins= getattr(challenger, 'sub_wins', 0)
        c_finishes= c_ko_wins + c_sub_wins

        # Win streak
        c_streak = 0
        for fh in reversed(getattr(challenger, 'fight_history', [])):
            if (fh.get('result') if isinstance(fh, dict) else '') == 'W':
                c_streak += 1
            else:
                break

        if c_streak >= 5:   prob += 12
        elif c_streak >= 3: prob += 6
        elif c_streak >= 2: prob += 3

        # Finish rate — dangerous challengers are avoided by lower fighters
        # but respected by higher ones
        if c_total >= 3:
            finish_rate = c_finishes / c_total
            if finish_rate >= 0.70:
                if t_tier in ("unranked", "ranked"):  prob -= 8   # they don't want to get finished
                else:                                  prob += 5   # elite respect danger
            elif finish_rate >= 0.50:
                prob += 2

        # ── 3. Target desperation modifier ────────────────────────────────
        t_losses = getattr(target, 'losses', 0)
        t_streak = 0
        for fh in reversed(getattr(target, 'fight_history', [])):
            if (fh.get('result') if isinstance(fh, dict) else '') == 'L':
                t_streak += 1
            else:
                break

        if t_streak >= 3:   prob += 20   # desperate, needs a win
        elif t_streak >= 2: prob += 10
        elif t_streak == 1 and t_losses >= 3: prob += 5

        # ── 4. Camp personality modifier ──────────────────────────────────
        # Each archetype has different willingness to accept challenges
        target_camp_id = getattr(target, 'camp_id', None)
        if target_camp_id:
            arch = self._get_camp_archetype(target_camp_id)
            arch_mods = {
                "Numbers Game":          +15,  # Signs anyone
                "Hometown Camp":         +10,  # Easy to book
                "Prospect Factory":      +5,   # Will fight for experience
                "Finisher Stable":       +5,   # Wants action
                "Submission Specialists": 0,   # Neutral
                "Wrestling Room":         0,   # Neutral
                "Striker's Gym":          0,   # Neutral
                "Veteran Hub":           -10,  # Picky about opponents
                "Star Factory":          -15,  # Protects image
                "Elite Academy":         -20,  # Very selective
            }
            prob += arch_mods.get(arch, 0)

        # ── 5. Clamp ──────────────────────────────────────────────────────
        return max(2, min(97, prob))

    def _get_ai_neg_personality(self, fighter) -> str:
        """
        Personality from rank and record — drives negotiation style.
        WARRIOR:   unranked or on a losing streak — takes anything
        PROSPECT:  unranked but hot streak — starting to be picky
        CONTENDER: ranked #6-15 — wants fights that move them up
        ELITE:     ranked #1-5 — very selective, money demands
        """
        rank    = self._get_fighter_rank(fighter)
        wins    = getattr(fighter, 'wins',   0)
        losses  = getattr(fighter, 'losses', 0)

        # Streak
        streak = 0
        for fh in reversed(getattr(fighter, 'fight_history', [])):
            if (fh.get('result') if isinstance(fh, dict) else '') == 'W':
                streak += 1
            else:
                break

        if rank is not None and rank <= 5:
            return "ELITE"
        elif rank is not None and rank <= 15:
            return "CONTENDER"
        elif streak >= 3 and wins >= 3:
            return "PROSPECT"
        else:
            return "WARRIOR"

    def _generate_ai_counter(self, neg: Dict) -> Dict:
        """
        AI fight negotiation response.
        Acceptance is determined by _fight_acceptance_probability.
        Purse counters are meaningful — they affect what the player pays.
        """
        import random
        personality   = neg["ai_personality"]
        offered_purse = neg["current_purse"]
        exchange      = neg["exchange_count"]
        weeks_out     = neg["weeks_out"]

        # Get acceptance probability for this specific matchup
        prob = self._fight_acceptance_probability(
            neg["player_fighter_id"], neg["ai_fighter_id"]
        )

        # On first exchange — does the AI even want this fight?
        if exchange == 1:
            roll = random.randint(1, 100)

            if roll <= prob:
                # They want the fight — may still counter on money
                if personality == "WARRIOR":
                    # Warriors just say yes
                    return {"decision": "ACCEPT", "message": None, "counter_purse": None}

                elif personality == "PROSPECT":
                    if random.random() < 0.40:
                        bump = int(offered_purse * 0.12)
                        return {
                            "decision": "COUNTER",
                            "message": f"I'm building my name. Make it ${offered_purse+bump:,} and I'm in.",
                            "counter_purse": offered_purse + bump,
                        }
                    return {"decision": "ACCEPT", "message": None, "counter_purse": None}

                elif personality == "CONTENDER":
                    if random.random() < 0.60:
                        bump = int(offered_purse * random.uniform(0.15, 0.25))
                        return {
                            "decision": "COUNTER",
                            "message": f"I'm ranked. That needs to reflect in the pay — ${offered_purse+bump:,}.",
                            "counter_purse": offered_purse + bump,
                        }
                    return {"decision": "ACCEPT", "message": None, "counter_purse": None}

                elif personality == "ELITE":
                    # Always counter on money first
                    bump = int(offered_purse * random.uniform(0.25, 0.45))
                    return {
                        "decision": "COUNTER",
                        "message": f"You know what a fight with me is worth. ${offered_purse+bump:,} or find someone else.",
                        "counter_purse": offered_purse + bump,
                    }
            else:
                # Don't want the fight — decline with reason
                decline_msgs = {
                    "ELITE":     "That matchup doesn't make sense for where I'm at. Come back when you've earned it.",
                    "CONTENDER": "I'm not fighting down. Win a few more and we'll talk.",
                    "PROSPECT":  "My team doesn't like this matchup right now.",
                    "WARRIOR":   "Not the right time. Ask me again next month.",
                }
                return {
                    "decision": "DECLINE",
                    "message": decline_msgs.get(personality, "Not interested."),
                    "counter_purse": None,
                }

        # Second exchange — player has countered, AI responds
        if personality == "WARRIOR":
            return {"decision": "ACCEPT", "message": None, "counter_purse": None}
        elif personality in ("PROSPECT", "CONTENDER"):
            if random.random() < 0.65:
                return {"decision": "ACCEPT", "message": None, "counter_purse": None}
            return {
                "decision": "DECLINE",
                "message": "We can't find common ground. Come back with a better number.",
                "counter_purse": None,
            }
        else:  # ELITE
            if random.random() < 0.50:
                return {"decision": "ACCEPT", "message": None, "counter_purse": None}
            return {
                "decision": "DECLINE",
                "message": "We're too far apart. This one isn't happening.",
                "counter_purse": None,
            }

    def initiate_challenge(self, challenger_id: str, opponent_id: str) -> Dict[str, Any]:
        """Alias for challenge_fighter used by the ladder route."""
        result = self.challenge_fighter(challenger_id, opponent_id)
        if result.get("success"):
            return {"success": True, "neg_id": result["neg_id"]}
        return {"success": False, "msg": result.get("error", "Challenge failed")}

    def challenge_fighter(self, player_fighter_id: str, target_fighter_id: str) -> Dict[str, Any]:
        """
        Initiate a fight challenge / negotiation.
        Returns {"success": True, "neg_id": ...} or {"success": False, "error": ...}.
        """
        if not self._game_state:
            return {"success": False, "error": "No game loaded"}

        import random

        player_fighter = self._game_state.get_fighter(player_fighter_id)
        ai_fighter     = self._game_state.get_fighter(target_fighter_id)

        if not player_fighter or not ai_fighter:
            return {"success": False, "error": "Fighter not found"}

        # Neither fighter can already be booked in a scheduled fight
        for f in self._scheduled_fights:
            ids = {f.get("fighter1_id"), f.get("fighter2_id")}
            if player_fighter_id in ids:
                name = getattr(player_fighter, 'name', player_fighter_id)
                return {"success": False, "error": f"{name} is already scheduled to fight"}
            if target_fighter_id in ids:
                name = getattr(ai_fighter, 'name', target_fighter_id)
                return {"success": False, "error": f"{name} is already booked for another fight"}

        # Block if player fighter is injured
        if INJURY_AVAILABLE and self._injury_system:
            if not self._injury_system.is_cleared_to_fight(player_fighter_id):
                _pname = getattr(player_fighter, 'name', player_fighter_id)
                return {"success": False,
                        "error": f"{_pname} is injured and cannot fight."}
            if not self._injury_system.is_cleared_to_fight(target_fighter_id):
                _tname = getattr(ai_fighter, 'name', target_fighter_id)
                return {"success": False,
                        "error": f"{_tname} is injured and unavailable."}

        # Block if target has a truly active (unresolved) negotiation
        _resolved = ("COMPLETED", "BROKEN_DOWN", "AI_DECLINED")
        for neg in self._pending_negotiations.values():
            if neg.get("ai_fighter_id") == target_fighter_id and \
               neg.get("status") not in _resolved:
                name = getattr(ai_fighter, 'name', target_fighter_id)
                return {"success": False, "error": f"{name} is already in negotiations"}
            if neg.get("player_fighter_id") == player_fighter_id and \
               neg.get("status") not in _resolved:
                name = getattr(player_fighter, 'name', player_fighter_id)
                return {"success": False, "error": f"{name} already has an open negotiation"}

        # Clean up resolved negs so they don't accumulate
        self._pending_negotiations = {
            nid: n for nid, n in self._pending_negotiations.items()
            if n.get("status") not in _resolved
        }

        # Block if target declined a challenge this week
        if self._game_state and            self._week_declines.get(target_fighter_id) == self._game_state.week_number:
            name = getattr(ai_fighter, 'name', target_fighter_id)
            return {"success": False, "error": f"{name} already declined a fight this week — try again next week"}

        player_rank = self._get_fighter_rank(player_fighter)

        # Ship K5: async challenge — AI responds in 1-2 weeks rather than
        # immediately. Pending challenge tracked in self._pending_challenges
        # and resolved by _process_pending_challenges each advance_week.
        chal_id = f"chal_{player_fighter_id[:8]}_{target_fighter_id[:8]}_{self._game_state.week_number}"
        current_week = self._game_state.week_number
        target_personality = (
            self._game_state._fighter_data.get(target_fighter_id, {})
                .get('personality')
            or getattr(ai_fighter, 'personality', '')
            or 'Competitor'
        )
        self._pending_challenges[chal_id] = {
            "challenge_id":        chal_id,
            "player_fighter_id":   player_fighter_id,
            "player_fighter_name": player_fighter.name,
            "target_fighter_id":   target_fighter_id,
            "target_fighter_name": ai_fighter.name,
            "target_personality":  target_personality,
            "created_week":        current_week,
            "response_week":       current_week + random.randint(1, 2),
            "weight_class":        player_fighter.weight_class
                if isinstance(player_fighter.weight_class, str)
                else str(player_fighter.weight_class),
            "status":              "PENDING",
            "player_rank":         player_rank,
            "target_rank":         self._get_fighter_rank(ai_fighter),
        }
        self._news_items.insert(0, {
            "headline": (f"⏳ Challenge sent to {ai_fighter.name} — "
                         f"waiting for their response."),
            "category": "signing",
            "week":     current_week,
        })
        return {
            "success":  True,
            "pending":  True,
            "message":  (f"Challenge sent to {ai_fighter.name}! "
                         f"Expect a response within 1-2 weeks."),
            "chal_id":  chal_id,
        }

    def get_negotiation(self, neg_id: str) -> Optional[Dict]:
        """Get negotiation state by ID."""
        return self._pending_negotiations.get(neg_id)

    def respond_to_negotiation(self, neg_id: str, action: str,
                                counter_purse: Optional[int] = None) -> Dict[str, Any]:
        """
        Player responds to negotiation.
        action: "ACCEPT" | "COUNTER" | "WALK"
        Max 2 total AI exchanges — on exchange 2, it resolves regardless.
        """
        neg = self._pending_negotiations.get(neg_id)
        if not neg:
            return {"success": False, "error": "Negotiation not found"}
        if neg["status"] in ("COMPLETED", "BROKEN_DOWN"):
            return {"success": False, "error": "Negotiation already resolved"}

        neg["history"].append({
            "by":      "PLAYER",
            "decision": action,
            "purse":    counter_purse or neg["current_purse"],
        })

        if action == "ACCEPT":
            neg["status"] = "COMPLETED"
            fight = self._book_fight_from_neg(neg)
            neg["fight_id"] = fight["fight_id"]
            return {"success": True, "outcome": "ACCEPTED", "fight_id": fight["fight_id"]}

        if action == "WALK":
            neg["status"] = "BROKEN_DOWN"
            return {"success": True, "outcome": "WALKED"}

        if action == "COUNTER":
            if neg["exchange_count"] >= 2:
                # Max exchanges — talks collapse
                neg["status"] = "BROKEN_DOWN"
                return {
                    "success": True,
                    "outcome": "BROKEN_DOWN",
                    "message": "Too many rounds of back-and-forth. Negotiations collapsed.",
                }

            if counter_purse:
                neg["current_purse"] = counter_purse

            neg["exchange_count"] += 1
            ai_resp = self._generate_ai_counter(neg)
            neg["ai_last_response"] = ai_resp

            if ai_resp["decision"] == "ACCEPT":
                neg["status"] = "AI_ACCEPTED_COUNTER"
                neg["history"].append({"by": "AI", "decision": "ACCEPT", "message": None, "purse": neg["current_purse"]})
                return {"success": True, "outcome": "AI_ACCEPTED"}
            elif ai_resp["decision"] == "COUNTER":
                neg["status"] = "AI_COUNTERED"
                if ai_resp["counter_purse"]:
                    neg["current_purse"] = ai_resp["counter_purse"]
                neg["history"].append({"by": "AI", "decision": "COUNTER",
                                       "message": ai_resp.get("message"), "purse": neg["current_purse"]})
                return {"success": True, "outcome": "AI_COUNTERED"}
            else:
                neg["status"] = "AI_DECLINED"
                neg["history"].append({"by": "AI", "decision": "DECLINE",
                                       "message": ai_resp.get("message"), "purse": neg["current_purse"]})
                return {"success": True, "outcome": "AI_DECLINED"}

        return {"success": False, "error": "Invalid action"}

    def _book_fight_from_neg(self, neg: Dict) -> Dict:
        """Convert a completed negotiation into a scheduled fight."""
        fight = {
            "fight_id":      f"fight_{neg['player_fighter_id']}_{neg['ai_fighter_id']}",
            "fighter1_id":   neg["player_fighter_id"],
            "fighter1_name": neg["player_fighter_name"],
            "fighter2_id":   neg["ai_fighter_id"],
            "fighter2_name": neg["ai_fighter_name"],
            "weight_class":  neg["weight_class"],
            "week":          self._game_state.week_number + neg["weeks_out"],
            "weeks_until":   neg["weeks_out"],
            "event_name":    neg["event_name"],
            "purse":         neg["current_purse"],
            "win_bonus":     neg["current_purse"] // 2,
            "is_title_fight":  False,
            "is_player_fight": True,
        }
        # Assign to the right DFC card
        event_name = self.assign_player_fight_to_card(fight)
        fight["event_name"] = event_name

        self._scheduled_fights.append(fight)
        self._fight_offers = [o for o in self._fight_offers
                               if o["fighter_id"] != neg["player_fighter_id"]]
        self._news_items.insert(0, {
            "headline":  f"📝 SIGNED: {neg['player_fighter_name']} vs {neg['ai_fighter_name']}",
            "category": "signing",
            "week":      self._game_state.week_number,
        })
        return fight

    # =========================================================================
    # FIGHT CAMP
    # =========================================================================

    def get_fight_camp_data(self, fight_id: str) -> Optional[Dict[str, Any]]:
        """Get all data needed for the fight camp setup screen (3-zone UI)."""
        fight = next((f for f in self._scheduled_fights if f.get("fight_id") == fight_id), None)
        if not fight:
            return None

        player_fighter = self._game_state.get_fighter(fight["fighter1_id"]) if self._game_state else None
        opponent       = self._game_state.get_fighter(fight["fighter2_id"]) if self._game_state else None

        if not player_fighter or not opponent:
            return None

        web_player   = self._convert_real_fighter(player_fighter)
        web_opponent = self._convert_real_fighter(opponent)

        existing = self._fight_camps.get(fight_id, {})
        weeks_until = fight.get("weeks_until", 4)

        # Tale of Tape matchup analysis
        tot_data = None
        if TOT_AVAILABLE:
            try:
                def _to_tape(wf):
                    return FighterTapeData(
                        name=wf.name,
                        age=wf.age,
                        wins=wf.wins, losses=wf.losses, draws=wf.draws,
                        ko_wins=wf.ko_wins, sub_wins=wf.sub_wins,
                        dec_wins=max(0, wf.wins - wf.ko_wins - wf.sub_wins),
                        is_champion=wf.is_champion,
                        ranking=wf.ranking or 0,
                        fighting_style=wf.fighting_style,
                        camp_name=wf.camp_name or "",
                        nationality=wf.country,
                        traits=wf.traits,
                        stats={
                            "boxing":            wf.boxing,
                            "kicks":             wf.kicks,
                            "clinch":            wf.clinch_striking,
                            "wrestling":         wf.takedowns,
                            "bjj":               wf.submissions,
                            "guard":             wf.guard,
                            "td_defense":        wf.takedown_defense,
                            "striking_def":      wf.striking_defense,
                            "chin":              wf.chin,
                            "cardio":            wf.cardio,
                            "strength":          wf.strength,
                            "speed":             wf.speed,
                            "fight_iq":          wf.fight_iq,
                            "composure":         wf.composure,
                            "top_control":       wf.top_control,
                            "heart":             wf.heart,
                        },
                    )
                tape = generate_tale_of_tape(
                    _to_tape(web_player), _to_tape(web_opponent),
                    is_title_fight=fight.get("is_title_fight", False),
                    weight_class=fight.get("weight_class", ""),
                )
                tot_data = {
                    "striking_adv":    tape.striking_advantage,
                    "grappling_adv":   tape.grappling_advantage,
                    "physical_adv":    tape.physical_advantage,
                    "experience_adv":  tape.experience_advantage,
                    "comparisons": [
                        {
                            "name":  c.display_name,
                            "val1":  c.value1,
                            "val2":  c.value2,
                            "edge":  c.advantage,
                        }
                        for c in tape.stat_comparisons[:8]
                    ],
                }
            except Exception as exc:
                print(f"⚠️ tale_of_tape failed: {exc}")

        # Generate opponent tendencies from fight history
        opp_tendencies = self._generate_opponent_tendencies(web_opponent)

        return {
            "fight":             fight,
            "player":            web_player,
            "opponent":          web_opponent,
            "weeks_until":       weeks_until,
            "existing_gameplan": existing.get("gameplan",        None),
            "existing_focus":    existing.get("training_focus",  ""),
            "existing_intensity":existing.get("intensity",       None),
            "coach_suggestion":  self._generate_coach_suggestion(web_player, web_opponent, weeks_until),
            "tale_of_tape":      tot_data,
            "tendencies":        opp_tendencies,
        }

    def _get_momentum_tag(self, fighter) -> str:
        """Quick momentum tag from a FighterRecord or WebFighter."""
        if hasattr(fighter, 'momentum_tag') and fighter.momentum_tag:
            return fighter.momentum_tag
        ws = getattr(fighter, 'win_streak', 0) or 0
        ls = getattr(fighter, 'lose_streak', 0) or 0
        is_champ = getattr(fighter, 'is_champion', False)
        if is_champ and ws >= 1:
            return "👑 Dominant"
        if ws >= 5:
            return "🔥 On a tear"
        if ws >= 3:
            return "🔥 Hot streak"
        if ls >= 3:
            return "📉 Skid"
        if ws >= 2:
            return "⚡ Rising"
        return ""

    def _generate_opponent_tendencies(self, opponent: Any) -> list:
        """
        Generate 2-3 human-readable scouting lines about an opponent.
        Uses ko_wins, sub_wins, wins, losses, fighting_style from WebFighter.
        Returns list of {icon, text} dicts.
        """
        lines = []
        total = max(1, getattr(opponent, 'wins', 0) + getattr(opponent, 'losses', 0))
        wins  = getattr(opponent, 'wins', 0)
        ko    = getattr(opponent, 'ko_wins', 0)
        sub   = getattr(opponent, 'sub_wins', 0)
        dec   = max(0, wins - ko - sub)
        style = getattr(opponent, 'fighting_style', '') or ''

        # Finish rate
        finish_rate = (ko + sub) / max(1, wins)
        if wins == 0:
            lines.append({"icon": "📋", "text": "No pro record — unknown quantity."})
        elif finish_rate >= 0.75:
            lines.append({"icon": "💥", "text": f"Dangerous finisher — {int(finish_rate*100)}% of wins by stoppage."})
        elif finish_rate <= 0.25:
            lines.append({"icon": "📋", "text": f"Decision hunter — goes the distance {int((1-finish_rate)*100)}% of the time."})

        # KO threat
        if wins > 0 and ko / wins >= 0.5:
            lines.append({"icon": "⚡", "text": f"KO artist — {ko} of {wins} wins by KO. Keep your hands up."})
        elif wins > 0 and sub / wins >= 0.5:
            lines.append({"icon": "🥋", "text": f"Submission specialist — {sub} of {wins} wins by sub. Stay off your back."})

        # Fight history finish timing — check fight_history if available
        history = getattr(opponent, 'fight_history', []) or []
        if history and wins > 0:
            early_finishes = sum(1 for f in history
                                 if isinstance(f, dict)
                                 and f.get('result') == 'W'
                                 and f.get('method', '') not in ('DEC', 'DRAW')
                                 and f.get('round_finished', 3) <= 1)
            if early_finishes >= 2:
                lines.append({"icon": "🔥", "text": f"Comes out fast — {early_finishes} first-round finishes. Survive the storm."})
            late_finishes = sum(1 for f in history
                                if isinstance(f, dict)
                                and f.get('result') == 'W'
                                and f.get('method', '') not in ('DEC', 'DRAW')
                                and f.get('round_finished', 1) >= 3)
            if late_finishes >= 2 and early_finishes < 2:
                lines.append({"icon": "⏱️", "text": f"Dangerous late — {late_finishes} finishes in round 3+. Don't let it go long."})

        # Style-based tendency
        style_tendencies = {
            "Wrestler":      ("🤼", "Expect takedown attempts — he'll try to grind you out."),
            "BJJ Specialist":("🥋", "World-class ground game — avoid the grapple."),
            "Striker":       ("🥊", "Stand-up specialist — expect volume and combinations."),
            "Muay Thai":     ("🦵", "Dangerous from range and in the clinch — watch the elbows."),
            "Pressure Fighter":("⚡","High-pressure style — he'll cut off the cage and push the pace."),
            "Counter Striker":("🛡️","Patient counter fighter — he'll wait for your mistakes."),
            "Ground & Pound":("👊", "Will look to take you down and unload from top — stay on your feet."),
            "Clinch Fighter":("🤛", "Dirty boxing specialist — the clinch is his home turf."),
        }
        if style in style_tendencies:
            icon, text = style_tendencies[style]
            lines.append({"icon": icon, "text": text})

        # Losing streak — vulnerability note
        losses = getattr(opponent, 'losses', 0)
        if losses >= 3 and wins > 0 and losses / total >= 0.45:
            lines.append({"icon": "📉", "text": "Struggling lately — may be on the decline."})

        return lines[:3]  # Cap at 3 to avoid clutter

    def _generate_coach_suggestion(self, player: Any, opponent: Any, weeks_until: int) -> Dict[str, Any]:
        """
        Coach advice engine.
        Weights: style matchup (40%), vulnerability vs this opponent (30%),
                 coach specialty bias (20%), weeks-out → intensity (10%).
        Lower-rated coach has 50% bias chance vs 25% for a good coach.
        """
        import random

        # Style matchup → recommended gameplan
        rec_gameplan = self._gameplan_from_style_matchup(player.fighting_style, opponent.fighting_style)

        # Vulnerability → recommended training focus
        vuln_focus, vuln_reason = self._find_vulnerability(player, opponent)

        # Read real coach data
        coach_specialty = self._coach.get("specialty", "boxing")
        coach_rating    = self._coach.get("rating", 60)

        # Intensity from weeks
        if weeks_until >= 8:
            rec_intensity     = "INTENSE"
            intensity_reason  = f"{weeks_until} weeks is a full camp. Go hard now."
        elif weeks_until >= 5:
            rec_intensity     = "MODERATE"
            intensity_reason  = f"{weeks_until} weeks is solid prep. Stay sharp."
        elif weeks_until >= 3:
            rec_intensity     = "MODERATE"
            intensity_reason  = f"Only {weeks_until} weeks — work smart, not reckless."
        else:
            rec_intensity     = "LIGHT"
            intensity_reason  = f"{weeks_until} weeks out — stay fresh, no new injuries."

        # Bias check
        bias_threshold = 0.25 if coach_rating >= 70 else 0.50
        coach_biased   = random.random() < bias_threshold

        if coach_biased:
            # Map coach specialty to a valid _FOCUS_ATTRS key
            _SPEC_TO_FOCUS = {
                "striking": "boxing",    "boxing": "boxing",
                "kickboxing": "kicks",   "muay thai": "kicks",   "muay_thai": "kicks",
                "grappling": "wrestling","wrestling": "wrestling",
                "bjj": "bjj",           "submissions": "submissions",
                "s&c": "cardio",        "strength": "strength",  "conditioning": "cardio",
                "mma": "sparring",      "head coach": "fight_iq","cornering": "fight_iq",
            }
            rec_gameplan  = self._gameplan_from_specialty(coach_specialty)
            rec_focus     = _SPEC_TO_FOCUS.get(coach_specialty.lower(), "sparring")
            confidence    = "Medium"
            bias_note     = f"⚠️ Coach may be biased — defaulting to their {coach_specialty} specialty"
        else:
            rec_focus  = vuln_focus
            confidence = "High" if coach_rating >= 75 else "Medium"
            bias_note  = None

        coach_quote = self._build_coach_quote(player, opponent, rec_focus,
                                               vuln_reason, rec_intensity, intensity_reason)
        return {
            "gameplan":      rec_gameplan,
            "focus":         rec_focus,
            "intensity":     rec_intensity,
            "confidence":    confidence,
            "bias_note":     bias_note,
            "coach_biased":  coach_biased,
            "coach_quote":   coach_quote,
            "vuln_focus":    vuln_focus,
            "vuln_reason":   vuln_reason,
        }

    def _gameplan_from_style_matchup(self, player_style: str, opp_style: str) -> str:
        """Recommend gameplan stance based on style matchup."""
        LOOKUP = {
            ("Wrestler",        "Striker"):          "TAKEDOWN",
            ("Wrestler",        "Counter Striker"):  "TAKEDOWN",
            ("Wrestler",        "Point Fighter"):    "TAKEDOWN",
            ("Wrestler",        "BJJ Specialist"):   "GNP",
            ("Ground & Pound",  "Striker"):          "TAKEDOWN",
            ("Ground & Pound",  "Counter Striker"):  "GNP",
            ("Ground & Pound",  "Wrestler"):         "GNP",
            ("Ground & Pound",  "BJJ Specialist"):   "GNP",
            ("BJJ Specialist",  "Wrestler"):         "SUBMISSION",
            ("BJJ Specialist",  "Ground & Pound"):   "SUBMISSION",
            ("BJJ Specialist",  "Striker"):          "SUBMISSION",
            ("Clinch Fighter",  "Striker"):          "CLINCH",
            ("Clinch Fighter",  "Counter Striker"):  "CLINCH",
            ("Clinch Fighter",  "Point Fighter"):    "CLINCH",
            ("Muay Thai",       "Clinch Fighter"):   "CLINCH",
            ("BJJ Specialist",  "Wrestler"):         "COUNTER",
            ("BJJ Specialist",  "Ground & Pound"):   "COUNTER",
            ("Counter Striker", "Pressure Fighter"): "DEFENSIVE",
            ("Counter Striker", "Striker"):          "DEFENSIVE",
            ("Pressure Fighter","Counter Striker"):  "AGGRESSIVE",
            ("Pressure Fighter","Point Fighter"):    "AGGRESSIVE",
            ("Sprawl & Brawl",  "Wrestler"):         "DEFENSIVE",
            ("Sprawl & Brawl",  "BJJ Specialist"):   "DEFENSIVE",
            ("Muay Thai",       "Clinch Fighter"):   "AGGRESSIVE",
            ("Striker",         "BJJ Specialist"):   "AGGRESSIVE",
            ("Striker",         "Wrestler"):         "DEFENSIVE",
        }
        return LOOKUP.get((player_style, opp_style), "BALANCED")

    def _find_vulnerability(self, player: Any, opponent: Any) -> tuple:
        """
        Find player's biggest vulnerability against THIS opponent.
        Not just weakest stat overall — the stat the opponent will specifically exploit.
        """
        # Maps opponent style → which player attributes they target
        STYLE_THREATS = {
            "Wrestler":        [("takedown_defense", "wrestling"),  ("top_control",    "top control")],
            "Ground & Pound":  [("takedown_defense", "takedowns"),  ("chin",           "ground and pound")],
            "BJJ Specialist":  [("guard",            "submissions"), ("takedown_defense","trips to the mat")],
            "Striker":         [("striking_defense", "boxing"),     ("chin",           "power shots")],
            "Counter Striker": [("striking_defense", "counters"),   ("composure",      "composure under fire")],
            "Pressure Fighter":[("cardio",           "pace"),       ("chin",           "volume")],
            "Muay Thai":       [("striking_defense", "kicks"),      ("clinch_striking","Thai clinch")],
            "Point Fighter":   [("striking_defense", "footwork"),   ("fight_iq",       "IQ")],
            "Clinch Fighter":  [("takedown_defense", "cage control"),("clinch_striking","dirty boxing")],
            "Sprawl & Brawl":  [("boxing",           "standup"),    ("striking_defense","counters")],
            "Balanced":        [("fight_iq",         "adaptability"),("striking_defense","all-around game")],
        }
        threats = STYLE_THREATS.get(opponent.fighting_style, [("fight_iq", "overall game")])

        # Find the threat this player is weakest against
        weakest_attr   = None
        weakest_val    = 101
        weakest_threat = ""
        for attr, threat_name in threats:
            val = getattr(player, attr, 50)
            if val < weakest_val:
                weakest_val    = val
                weakest_attr   = attr
                weakest_threat = threat_name

        if not weakest_attr:
            weakest_attr   = "fight_iq"
            weakest_threat = "overall game"
            weakest_val    = getattr(player, "fight_iq", 50)

        reason = f"Their {opponent.fighting_style} will exploit your {weakest_threat} ({weakest_val})"
        return weakest_attr, reason

    def _gameplan_from_specialty(self, specialty: str) -> str:
        """Map coach archetype to recommended gameplan stance."""
        _SP = specialty.lower()
        if _SP in ("striking", "boxing", "kickboxing", "muay thai",
                   "muay_thai", "striking_coach"):
            return "AGGRESSIVE"
        if _SP in ("wrestling", "grappling", "bjj", "submissions",
                   "grappling_coach"):
            return "SUBMISSION"
        if _SP in ("s&c", "strength", "conditioning", "cardio", "sc_coach"):
            return "MEASURED"  # S&C coaches preach pacing and attrition
        if _SP in ("mma", "head coach", "cornering", "strategy", "mma_coach"):
            return "BALANCED"
        return "BALANCED"

    def _build_coach_quote(self, player: Any, opponent: Any, focus: str,
                            vuln_reason: str, intensity: str, intensity_reason: str) -> str:
        """Short, direct coach voice. Mentions specific numbers."""
        DISPLAY = {
            "boxing": "boxing",          "kicks": "kicking",
            "clinch_striking": "clinch", "striking_defense": "defense",
            "takedowns": "wrestling",    "takedown_defense": "takedown defense",
            "top_control": "top control","submissions": "submissions",
            "guard": "guard work",       "cardio": "cardio",
            "chin": "chin",              "recovery": "recovery",
            "heart": "heart",            "fight_iq": "fight IQ",
            "composure": "composure",    "strength": "strength",
            "speed": "speed",
        }
        focus_display = DISPLAY.get(focus, focus)
        opp_last = opponent.name.split()[-1]
        player_val = getattr(player, focus, 50)

        return (
            f"{opp_last} is a {opponent.fighting_style} — {vuln_reason.lower()}. "
            f"Your {focus_display} is at {player_val}; that's where this fight gets decided. "
            f"{intensity_reason}"
        )

    def save_fight_camp(self, fight_id: str, gameplan: str,
                         training_focus: str, intensity: str) -> Dict[str, Any]:
        """Save player's fight camp setup choices."""
        fight = next((f for f in self._scheduled_fights if f.get("fight_id") == fight_id), None)
        if not fight:
            return {"success": False, "error": "Fight not found"}

        # Reset accumulated stat totals for this fighter — new camp starting
        for fid_reset in [fight.get("fighter1_id"), fight.get("fighter2_id")]:
            if fid_reset and fid_reset in self._camp_stat_totals:
                self._camp_stat_totals[fid_reset] = {}

        self._fight_camps[fight_id] = {
            "gameplan":       gameplan,
            "training_focus": training_focus,
            "intensity":      intensity,
        }
        # Write onto the scheduled fight so fight engine can read it later
        fight["gameplan"]       = gameplan
        fight["training_focus"] = training_focus
        fight["intensity"]      = intensity

        return {"success": True, "message": "Fight camp saved"}


    # =========================================================================
    # DIVISION RANKINGS — LIVE UPDATE
    # =========================================================================

    def _update_rankings_after_fight(self, weight_class: str, bypass_clamp: bool = False) -> None:
        """
        Re-sort a division's rankings after any fight completes.
        Pure record-based — NO rating involved.

        Formula:
          base     = wins*5 + finish_wins*2 - losses*3
          streak   = win_streak*1.5
          quality  = ranked_wins*8  (beating ranked opponents matters most)
          total    = base + streak + quality

        Requirements:
          - At least 3 wins to enter top 10
          - At least 1 win to appear at all
        """
        if not self._game_state or not weight_class:
            return
        division = self._game_state.divisions.get(weight_class)
        if not division:
            return

        ranked_ids = set(division.rankings) | (
            {division.champion_id} if division.champion_id else set()
        )

        fighters = [
            f for f in self._game_state.fighters.values()
            if f.weight_class == weight_class
            and f.is_active
            and f.fighter_id != division.champion_id
            and f.wins >= 1
        ]

        # Snapshot current rankings for movement cap
        old_rankings = list(division.rankings)

        def rank_score(f) -> float:
            # Count wins over ranked opponents from fight history
            ranked_wins = sum(
                1 for h in getattr(f, 'fight_history', [])
                if isinstance(h, dict)
                and h.get('result') == 'W'
                and h.get('opponent_id') in ranked_ids
            )
            finish_wins = getattr(f, 'ko_wins', 0) + getattr(f, 'sub_wins', 0)

            # Recency weight: last 3 fights 4x, fights 4-8 2x, 9 = 0.5x
            # W = +2.5×weight; L = -2.0×weight (recent losses hurt heavier)
            history = list(reversed(getattr(f, 'fight_history', []) or []))
            recency_bonus = 0.0
            for i, h in enumerate(history[:9]):
                if not isinstance(h, dict):
                    continue
                result = h.get('result', '')
                weight = 4.0 if i < 3 else (2.0 if i < 8 else 0.5)
                if result == 'W':
                    recency_bonus += weight * 2.5
                elif result == 'L':
                    recency_bonus -= weight * 2.0

            score = (
                f.wins        * 5.0
                + finish_wins * 2.0
                - f.losses    * 3.0
                + ranked_wins * 20.0   # Quality of opposition — beating ranked matters
                + recency_bonus        # Recent form (replaces streak term — recency captures it)
            )
            return score

        # Stable tiebreaker: when rank_score ties, sort by fighter_id
        # (alphabetical, stable across save/load). Ship F33-A — fixes
        # Finding #33 (ranking shuffle on load due to dict-iteration
        # order varying between fresh-game and post-load processes).
        fighters.sort(key=lambda f: (-rank_score(f), f.fighter_id))

        # Require wins to rank — higher bar for top slots
        # top 10: 5+ wins; spots 11-15: 3+ wins
        top10 = [f for f in fighters[:10] if f.wins >= 5]
        rest  = [f for f in fighters if f not in top10 and f.wins >= 3]
        new_order = [f.fighter_id for f in (top10 + rest)[:15]]

        # Cap single-event rank movement at ±3 positions for existing ranked fighters.
        # New entrants (unranked) can't enter above rank #9, EXCEPT former top-5 fighters
        # returning to ranking (e.g., from injury) — they re-enter at score-warranted position.
        # Pass bypass_clamp=True to skip both clamps (used by re-rank-on-load).
        MAX_MOVE      = 3
        NEW_ENTRY_CAP = 8  # Unranked entrants can't enter above rank #9 (index 8)
        final_order = list(new_order)
        if not bypass_clamp:
            for i, fid in enumerate(new_order):
                if fid in old_rankings:
                    old_pos = old_rankings.index(fid)
                    new_pos = i
                    if abs(new_pos - old_pos) > MAX_MOVE:
                        if new_pos < old_pos:
                            clamped = max(0, old_pos - MAX_MOVE)
                        else:
                            clamped = min(14, old_pos + MAX_MOVE)
                        clamped = max(0, min(14, clamped))
                        if fid in final_order:
                            final_order.remove(fid)
                            final_order.insert(clamped, fid)
                else:
                    # New entrant — cap entry position UNLESS former top-5
                    fighter = self._game_state.fighters.get(fid)
                    is_returning_contender = (
                        fighter is not None
                        and getattr(fighter, 'best_rank', 99) <= 5
                    )
                    if i < NEW_ENTRY_CAP and not is_returning_contender:
                        clamped = NEW_ENTRY_CAP
                        if fid in final_order:
                            final_order.remove(fid)
                            final_order.insert(clamped, fid)

        division.rankings = final_order[:15]

        # Update best_rank for each currently-ranked fighter (1-based index).
        # Tracked as min — a fighter who fell out of rankings keeps their previous best.
        for idx, fid in enumerate(division.rankings):
            fighter = self._game_state.fighters.get(fid)
            if fighter is None:
                continue
            current_rank = idx + 1
            if current_rank < getattr(fighter, 'best_rank', 99):
                fighter.best_rank = current_rank

    def _update_all_rankings(self, bypass_clamp: bool = False) -> None:
        """Update rankings for every division — called each week.

        bypass_clamp=True skips per-fight movement caps and new-entry caps
        (used by re-rank-on-load to converge to the formula's true equilibrium).
        """
        if not self._game_state:
            return
        # Snapshot before update for movement detection
        _pre = {}
        for _wc in self._game_state.WEIGHT_CLASSES:
            _div = self._game_state.divisions.get(_wc)
            if _div:
                _pre[_wc] = list(_div.rankings[:5])

        for wc in self._game_state.WEIGHT_CLASSES:
            self._update_rankings_after_fight(wc, bypass_clamp=bypass_clamp)

        # Print notable ranking movements (top-5 entries/exits)
        for _wc, _pre_top5 in _pre.items():
            _div = self._game_state.divisions.get(_wc)
            if not _div:
                continue
            _post_top5 = _div.rankings[:5]
            for _new_idx, _fid in enumerate(_post_top5):
                if _fid not in _pre_top5:
                    _ftr = self._game_state.get_fighter(_fid)
                    _fname = getattr(_ftr, 'name', _fid) if _ftr else _fid
                    _ws = getattr(_ftr, 'win_streak', 0) or 0
                    _streak_note = f" ({_ws}-win streak)" if _ws >= 2 else ""
                    _wc_abbr = {"Strawweight":"STR","Flyweight":"FLY",
                                "Bantamweight":"BAN","Featherweight":"FEA",
                                "Lightweight":"LIG","Welterweight":"WEL",
                                "Middleweight":"MID","Light Heavyweight":"LHW",
                                "Heavyweight":"HVY"}.get(_wc, _wc[:3])
                    print(f"  📈 [RANKINGS] {_fname} {_wc_abbr}: entered top 5 "
                          f"at #{_new_idx+1}{_streak_note}")

    # =========================================================================
    # AI WORLD SIMULATION — WEEKLY FIGHTS
    # =========================================================================

    def _simulate_card_fights(self, card: Dict[str, Any],
                               fights_to_sim: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Simulate a list of AI fights from a pre-built card.
        Returns a completed event dict.
        """
        import random

        week       = card["week"]
        event_name = card["event_name"]
        event: Dict[str, Any] = {
            "event_id":    card["event_id"],
            "event_name":  event_name,
            "week":        week,
            "fights":      [],
            "main_event":  None,
            "fotn":        None,
            "is_ai_event": True,
        }

        # Snapshot ALL fighter ranks BEFORE any fights run
        # This prevents rank updates from earlier fights contaminating
        # the "pre-fight rank" of later fights on the same card
        pre_rank_snapshot: Dict[str, Optional[int]] = {}
        for fight in fights_to_sim:
            for fid in [fight.get("fighter1_id"), fight.get("fighter2_id")]:
                if fid and fid not in pre_rank_snapshot:
                    ftr = self._game_state.get_fighter(fid)
                    pre_rank_snapshot[fid] = self._get_fighter_rank(ftr) if ftr else None

        for fight in fights_to_sim:
            f1 = self._game_state.get_fighter(fight["fighter1_id"])
            f2 = self._game_state.get_fighter(fight["fighter2_id"])
            if not f1 or not f2:
                continue
            # Skip if either fighter isn't cleared to fight (injury)
            if INJURY_AVAILABLE and self._injury_system:
                _f1_clr = self._injury_system.is_cleared_to_fight(f1.fighter_id)
                _f2_clr = self._injury_system.is_cleared_to_fight(f2.fighter_id)
                if not _f1_clr or not _f2_clr:
                    _uncleared_names = []
                    if not _f1_clr: _uncleared_names.append(f1.name)
                    if not _f2_clr: _uncleared_names.append(f2.name)
                    self._news_items.insert(0, {
                        "headline": (f"🚫 {f1.name} vs {f2.name} at "
                                     f"{event_name} cancelled — "
                                     f"{' and '.join(_uncleared_names)} not cleared to fight."),
                        "category": "injury",
                        "week": week,
                    })
                    continue

            # Ship DR2: track draws to skip winner/loser-specific blocks
            _is_draw_a = False
            # Use real engine or fallback
            if FIGHT_ENGINE_AVAILABLE:
                try:
                    fa1  = self._make_fighter_attrs(f1, f1.name, f1.fighter_id)
                    fa2  = self._make_fighter_attrs(f2, f2.name, f2.fighter_id)
                    _slot = fight.get("card_slot", "prelim")
                    _rnds = 5 if (fight.get("is_title_fight") or _slot in ("main_event","co_main")) else 3
                    _fight_cfg = _FightConfig(
                        scheduled_rounds=_rnds,
                        standup_threshold=10,
                        exchanges_per_round=55,
                        submission_progress_to_finish=70.0,
                        submission_escape_threshold=85.0,
                        damage_multiplier=FI_DAMAGE_MULTIPLIER,
                    ) if _FightConfig else None
                    _eng = _simulate_narrated_fight_fn(
                        fa1, fa2, rounds=_rnds,
                        **({"config": _fight_cfg} if _fight_cfg else {})
                    )
                    try:
                        if _eng and hasattr(_eng, 'fighter1_stats'):
                            _wk = self._game_state.week_number if self._game_state else 0
                            for _fid, _stats in [(fa1.fighter_id, _eng.fighter1_stats),
                                                  (fa2.fighter_id, _eng.fighter2_stats)]:
                                self._accumulate_career_stats(
                                    _fid,
                                    strikes=sum(int(s.get('sig_strikes_landed', 0)) for s in _stats),
                                    takedowns=sum(int(s.get('td_landed', 0)) for s in _stats),
                                    sub_attempts=sum(int(s.get('sub_att', 0)) for s in _stats),
                                    control_time=sum(float(s.get('control_time', 0.0)) for s in _stats),
                                    week=_wk,
                                )
                    except Exception as _cse:
                        print(f"⚠️ Career stat accumulation failed: {_cse}")
                    try:
                        _loser_id = _eng.loser_id
                        _method   = _eng.method
                        if _loser_id and _method:
                            self._apply_chin_erosion(_loser_id, _method,
                                self._game_state.week_number if self._game_state else 0)
                    except Exception as _ce:
                        print(f"⚠️  Chin erosion failed: {_ce}")
                    if _eng.winner_id is None:
                        # Ship DR2: engine returned a draw — skip winner pick
                        _is_draw_a = True
                        winner = None
                        loser  = None
                        method = "Draw"
                        rnd    = _rnds
                    else:
                        winner = f1 if _eng.winner_id in (f1.fighter_id, "fighter_1") else f2
                        loser  = f2 if winner is f1 else f1
                        _raw   = _eng.method or "DEC"
                        # Engine returns "Submission (xxx)" — normalise to SUB
                        if _raw.startswith("Submission"):
                            method = "SUB"
                        elif _raw in ("KO",):
                            method = "KO"
                        elif _raw in ("TKO",):
                            method = "TKO"
                        elif "Decision" in _raw or _raw == "DEC":
                            method = "DEC"
                        else:
                            method = "DEC"
                        rnd    = getattr(_eng,'finish_round',None) or _rnds
                        rnd = rnd or _rnds
                except Exception:
                    f1_s = f1.wins/(max(1,f1.wins+f1.losses))*60 + random.randint(0,30)
                    f2_s = f2.wins/(max(1,f2.wins+f2.losses))*60 + random.randint(0,30)
                    winner = f1 if f1_s >= f2_s else f2
                    loser  = f2 if winner is f1 else f1
                    roll = random.random()
                    if   roll < 0.28: method, rnd = "KO",  random.randint(1,3)
                    elif roll < 0.48: method, rnd = "TKO", random.randint(1,3)
                    elif roll < 0.63: method, rnd = "SUB", random.randint(1,3)
                    else:             method, rnd = "DEC", 3
            else:
                f1_s = f1.wins/(max(1,f1.wins+f1.losses))*60 + random.randint(0,30)
                f2_s = f2.wins/(max(1,f2.wins+f2.losses))*60 + random.randint(0,30)
                winner = f1 if f1_s >= f2_s else f2
                loser  = f2 if winner is f1 else f1
                roll = random.random()
                if   roll < 0.28: method, rnd = "KO",  random.randint(1,3)
                elif roll < 0.48: method, rnd = "TKO", random.randint(1,3)
                elif roll < 0.63: method, rnd = "SUB", random.randint(1,3)
                else:             method, rnd = "DEC", 3

            # Ship DR2: draw short-circuit. Increment draws on both fighters,
            # build a draw-shape result dict, append, and skip the rest of the
            # per-fight loop body (record mutations, fight history, rankings,
            # title record, terminal log all assume winner/loser non-None).
            if _is_draw_a:
                f1.draws = getattr(f1, 'draws', 0) + 1
                f2.draws = getattr(f2, 'draws', 0) + 1
                result = {
                    "fight_id":          fight["fight_id"],
                    "fighter1_id":       fight["fighter1_id"],
                    "fighter2_id":       fight["fighter2_id"],
                    "fighter1_name":     fight["fighter1_name"],
                    "fighter2_name":     fight["fighter2_name"],
                    "winner_id":         None,
                    "winner_name":       "",
                    "loser_id":          None,
                    "loser_name":        "",
                    "method":            "Draw",
                    "round_finished":    rnd,
                    "weight_class":      fight["weight_class"],
                    "event_name":        event_name,
                    "is_title_fight":    fight.get("is_title_fight", False),
                    "is_ai_fight":       True,
                    "card_slot":         fight.get("card_slot", "prelim"),
                    "winner_new_rank":   None,
                    "loser_new_rank":    None,
                    "winner_rank_delta": 0,
                    "loser_rank_delta":  0,
                }
                event["fights"].append(result)
                print(f"   [DRAW] {f1.name} vs {f2.name} — Draw (R{rnd})")
                continue

            pre_w = pre_rank_snapshot.get(winner.fighter_id)
            pre_l = pre_rank_snapshot.get(loser.fighter_id)

            winner.wins += 1; loser.losses += 1
            if method in ("KO","TKO"):
                winner.ko_wins += 1
                loser.ko_losses = getattr(loser, 'ko_losses', 0) + 1
            elif method == "SUB":
                winner.sub_wins += 1
                loser.sub_losses = getattr(loser, 'sub_losses', 0) + 1
            self._apply_post_fight_camp_record(winner, loser, fight, method)

            # Track fight damage for next camp injury risk
            _dmg = {"KO":80,"TKO":55,"SUB":30,"DEC":10}.get(method, 10)
            try: setattr(loser,  'fight_damage', _dmg)
            except Exception: pass
            try: setattr(winner, 'fight_damage', _dmg // 4)
            except Exception: pass

            # ── AI contract decrement ────────────────────────────────
            # Decrement fights_remaining for both fighters in game_state._contract_data
            # When it hits 0: fighter becomes free agent (personality-driven bidding)
            if self._game_state:
                for _ftr_c in [winner, loser]:
                    _cid = getattr(_ftr_c, 'contract_id', None)
                    if not _cid:
                        _cid = self._game_state.active_contracts.get(_ftr_c.fighter_id)
                    if _cid and _cid in self._game_state._contract_data:
                        _cd = self._game_state._contract_data[_cid]
                        _cd["fights_remaining"] = max(0, _cd.get("fights_remaining", 1) - 1)
                        if _cd["fights_remaining"] == 0:
                            # Contract expired — fighter becomes free agent
                            _camp_c = self._game_state.get_camp(_ftr_c.camp_id) if _ftr_c.camp_id else None
                            _camp_nm = getattr(_camp_c, 'name', 'their camp') if _camp_c else 'their camp'
                            _ftr_c.camp_id = None
                            _ftr_c.contract_id = None
                            self._game_state.free_agents.add(_ftr_c.fighter_id)
                            self._game_state.active_contracts.pop(_ftr_c.fighter_id, None)
                            print(f"  📋 [AI CONTRACT] {_ftr_c.name} contract expired at {_camp_nm} — free agent")
                            self._news_items.append({
                                "headline": f"📋 {_ftr_c.name} is a free agent — contract with {_camp_nm} expired",
                                "category": "contract",
                                "week": week,
                            })
                            # AI camps bid for newly available fighter
                            self._ai_bid_for_free_agent(_ftr_c.fighter_id, _ftr_c)

            # Fight injury rolls — real injury system
            if INJURY_AVAILABLE and self._injury_system:
                # Map method string to FightOutcome enum
                _outcome_map = {
                    "KO":  FightOutcome.KO, "TKO": FightOutcome.TKO,
                    "SUB": FightOutcome.SUBMISSION, "DEC": FightOutcome.DECISION_UNANIMOUS,
                }
                _fo = _outcome_map.get(method, FightOutcome.DECISION_UNANIMOUS)
                for _ftr, _is_loser in [(loser, True), (winner, False)]:
                    _prob = calculate_fight_injury_probability(_fo, rnd, _is_loser)
                    if __import__('random').random() < _prob:
                        _opp_id = winner.fighter_id if _is_loser else loser.fighter_id
                        _inj = generate_fight_injury(_ftr.fighter_id, _fo, _is_loser, _opp_id)
                        self._injury_system.add_injury(_inj)
                        print(f"  🤕 [FIGHT INJURY] {_ftr.name} — {_inj.description} "
                              f"({_inj.severity_name}) · {_inj.recovery_weeks}w")
                        if getattr(_ftr, 'is_champion', False):
                            _hl = (f"🏆 {_ftr.name} ({_ftr.weight_class} Champion) suffers "
                                   f"{_inj.description} — out {_inj.recovery_weeks} weeks. "
                                   f"Title defense delayed.")
                        else:
                            _hl = (f"🤕 {_ftr.name} injured at {event_name}: "
                                   f"{_inj.description} — {_inj.recovery_weeks}w recovery")
                        self._news_items.append({
                            "headline": _hl,
                            "category": "injury", "week": week,
                        })
                        self._maybe_queue_champion_injury_decision(_ftr, _inj)

            for ftr, res, opp in [(winner,"W",loser),(loser,"L",winner)]:
                if not hasattr(ftr,"fight_history"): ftr.fight_history = []
                ftr.fight_history.append({
                    "opponent_name": opp.name,
                    "opponent_id":   opp.fighter_id,
                    "result": res,
                    "method": method, "round_finished": rnd,
                    "event_name": event_name, "week": week,
                })

            self._update_rankings_after_fight(fight["weight_class"])
            new_w = self._get_fighter_rank(winner)
            new_l = self._get_fighter_rank(loser)

            result = {
                "fight_id":         fight["fight_id"],
                "fighter1_id":      fight["fighter1_id"],
                "fighter2_id":      fight["fighter2_id"],
                "fighter1_name":    fight["fighter1_name"],
                "fighter2_name":    fight["fighter2_name"],
                "winner_id":        winner.fighter_id,
                "winner_name":      winner.name,
                "loser_id":         loser.fighter_id,
                "loser_name":       loser.name,
                "method":           method,
                "round_finished":   rnd,
                "weight_class":     fight["weight_class"],
                "event_name":       event_name,
                "is_title_fight":   fight.get("is_title_fight", False),
                "is_ai_fight":      True,
                "card_slot":        fight.get("card_slot", "prelim"),
                "winner_new_rank":  new_w,
                "loser_new_rank":   new_l,
                "winner_rank_delta": self._rank_delta(pre_w, new_w),
                "loser_rank_delta":  self._rank_delta(pre_l, new_l),
            }
            event["fights"].append(result)
            # event["main_event"] is set only when the actual main_event-
            # slotted fight resolves — never provisionally. Slot was
            # assigned at card-build time, so this read is authoritative.
            if (event["main_event"] is None
                and fight.get("card_slot") == "main_event"):
                event["main_event"] = result

            # Record title fight results into history
            if fight.get("is_title_fight"):
                self._record_title_result(
                    weight_class = fight["weight_class"],
                    winner       = winner,
                    loser        = loser,
                    method       = method,
                    rnd          = rnd,
                    event_name   = event_name,
                    week         = week,
                )

            # Terminal: one line per fight result
            slot_tag = {"main_event":"[ME]","co_main":"[CM]","main_card":"[MC]","prelim":"[PR]"}.get(fight.get("card_slot","prelim"),"[PR]")
            print(f"   {slot_tag} {winner.name} def. {loser.name} via {method} R{rnd}")

            if method in ("KO","TKO","SUB"):
                icon = "💥" if method in ("KO","TKO") else "🔒"
                self._news_items.append({
                    "headline":  f"{icon} {winner.name} def. {loser.name} by {method} (R{rnd}) at {event_name}",
                    "category":  "fight",
                    "week":      week,
                    "winner_id": winner.fighter_id,
                    "loser_id":  loser.fighter_id,
                    "fight_id":  fight.get("fight_id", ""),
                    "event_id":  event.get("event_id", ""),
                })

        # ── Terminal: card fight distribution summary ─────────────────
        if event["fights"]:
            _methods = [f.get("method","DEC") for f in event["fights"]]
            _ko  = sum(1 for m in _methods if m == "KO")
            _tko = sum(1 for m in _methods if m == "TKO")
            _sub = sum(1 for m in _methods if m == "SUB")
            _dec = sum(1 for m in _methods if m == "DEC")
            _total = len(_methods)
            _fin_rate = int((_ko + _tko + _sub) / _total * 100) if _total else 0
            print(f"  📊 [{event.get('event_name', PROMOTION_NAME)}] {_total} fights "
                  f"— KO:{_ko} TKO:{_tko} SUB:{_sub} DEC:{_dec} "
                  f"(finish rate: {_fin_rate}%)")

        return event if event["fights"] else None

    def _simulate_ai_fights_week(self) -> Optional[Dict[str, Any]]:
        """
        Simulate one weekly AI card: ~5 fights across different divisions.
        Returns a completed-event dict (or None if no fights could be made).
        These fights keep the world alive — AI fighters accumulate records,
        rankings evolve, and news items are generated for notable finishes.
        """
        if not self._game_state:
            return None
        import random

        week       = self._game_state.week_number
        event_name = self._dfc_label(week)
        event_id   = f"ai_event_{week}"
        event: Dict[str, Any] = {
            "event_id":    event_id,
            "event_name":  event_name,
            "week":        week,
            "fights":      [],
            "main_event":  None,
            "fotn":        None,
            "is_ai_event": True,
        }

        player_camp_id = self._game_state.player_camp_id
        # 10-12 fights per week across all divisions — realistic card size
        # Each division contributes 1-2 fights
        target_fights = random.randint(10, 12)
        all_wcs = list(self._game_state.WEIGHT_CLASSES)
        random.shuffle(all_wcs)
        # Build division list with repetitions to hit target count
        divisions = []
        while len(divisions) < target_fights:
            divisions.extend(all_wcs)
        divisions = divisions[:target_fights]

        for wc in divisions:
            division = self._game_state.divisions.get(wc)
            if not division:
                continue

            # AI fighters only (not player camp), not already booked
            booked_ids = {
                fid for f in self._scheduled_fights
                for fid in [f.get("fighter1_id"), f.get("fighter2_id")]
            }
            pool = [
                f for f in self._game_state.fighters.values()
                if f.weight_class == wc
                and f.is_active
                and f.camp_id != player_camp_id
                and f.fighter_id not in booked_ids
                and not (INJURY_AVAILABLE and self._injury_system
                         and not self._injury_system.is_cleared_to_fight(f.fighter_id))
            ]
            if len(pool) < 2:
                continue

            # Rank-based matchmaking: pair fighters by ladder position
            # Champion fights #1 contender; #2 fights #3; etc.
            # Unranked fight unranked of similar record
            ranked_ids  = ([division.champion_id] if division.champion_id else []) + list(division.rankings[:15])
            ranked_pool = [f for f in pool if f.fighter_id in ranked_ids]
            unrank_pool = [f for f in pool if f.fighter_id not in ranked_ids]

            f1 = f2 = None
            if len(ranked_pool) >= 2:
                # Pick adjacent pair from ranked list
                idx = random.randint(0, len(ranked_pool) - 2)
                f1, f2 = ranked_pool[idx], ranked_pool[idx + 1]
            elif len(unrank_pool) >= 2:
                # Two unranked
                f1, f2 = random.sample(unrank_pool, 2)
            elif len(pool) >= 2:
                f1, f2 = random.sample(pool, 2)
            else:
                continue

            # Title status from champion presence (no pre-built card carries it here)
            is_title = getattr(f1, 'is_champion', False) or getattr(f2, 'is_champion', False)

            # ── AI fight outcome ────────────────────────────────────
            # Ship DR2: track draws to skip winner/loser-specific blocks
            _is_draw_b = False
            if FIGHT_ENGINE_AVAILABLE:
                try:
                    # Use real engine — no commentary stored for AI fights
                    fa1 = self._make_fighter_attrs(f1, f1.name, f1.fighter_id)
                    fa2 = self._make_fighter_attrs(f2, f2.name, f2.fighter_id)
                    _rnds = 5 if is_title else 3
                    _fight_cfg = _FightConfig(
                        scheduled_rounds=_rnds,
                        standup_threshold=10,
                        exchanges_per_round=55,
                        submission_progress_to_finish=70.0,
                        submission_escape_threshold=85.0,
                        damage_multiplier=FI_DAMAGE_MULTIPLIER,
                    ) if _FightConfig else None
                    _eng = _simulate_narrated_fight_fn(
                        fa1, fa2, rounds=_rnds,
                        **({"config": _fight_cfg} if _fight_cfg else {})
                    )
                    try:
                        if _eng and hasattr(_eng, 'fighter1_stats'):
                            _wk = self._game_state.week_number if self._game_state else 0
                            for _fid, _stats in [(fa1.fighter_id, _eng.fighter1_stats),
                                                  (fa2.fighter_id, _eng.fighter2_stats)]:
                                self._accumulate_career_stats(
                                    _fid,
                                    strikes=sum(int(s.get('sig_strikes_landed', 0)) for s in _stats),
                                    takedowns=sum(int(s.get('td_landed', 0)) for s in _stats),
                                    sub_attempts=sum(int(s.get('sub_att', 0)) for s in _stats),
                                    control_time=sum(float(s.get('control_time', 0.0)) for s in _stats),
                                    week=_wk,
                                )
                    except Exception as _cse:
                        print(f"⚠️ Career stat accumulation failed: {_cse}")
                    try:
                        _loser_id = _eng.loser_id
                        _method   = _eng.method
                        if _loser_id and _method:
                            self._apply_chin_erosion(_loser_id, _method,
                                self._game_state.week_number if self._game_state else 0)
                    except Exception as _ce:
                        print(f"⚠️  Chin erosion failed: {_ce}")
                    if _eng.winner_id is None:
                        # Ship DR2: engine returned a draw
                        _is_draw_b = True
                        winner = None
                        loser  = None
                        method = "Draw"
                        rnd    = _rnds
                    else:
                        winner = f1 if _eng.winner_id in (f1.fighter_id, "fighter_1") else f2
                        loser  = f2 if winner is f1 else f1
                        _raw   = _eng.method or "DEC"
                        if _raw.startswith("Submission"):
                            method = "SUB"
                        elif _raw in ("KO",):
                            method = "KO"
                        elif _raw in ("TKO",):
                            method = "TKO"
                        else:
                            method = "DEC"
                        rnd    = getattr(_eng,'finish_round',None) or _rnds
                        rnd = rnd or _rnds
                except Exception:
                    # Fallback to score-based if engine errors
                    f1_pct = f1.wins / max(1, f1.wins + f1.losses)
                    f2_pct = f2.wins / max(1, f2.wins + f2.losses)
                    f1_r   = self._get_fighter_rank(f1)
                    f2_r   = self._get_fighter_rank(f2)
                    f1_s   = f1_pct * 60 + (15-(f1_r or 20))*2 + random.randint(0,25)
                    f2_s   = f2_pct * 60 + (15-(f2_r or 20))*2 + random.randint(0,25)
                    winner = f1 if f1_s >= f2_s else f2
                    loser  = f2 if f1_s >= f2_s else f1
                    roll = random.random()
                    if   roll < 0.28: method, rnd = "KO",  random.randint(1,3)
                    elif roll < 0.48: method, rnd = "TKO", random.randint(1,3)
                    elif roll < 0.63: method, rnd = "SUB", random.randint(1,3)
                    else:             method, rnd = "DEC", 3
            else:
                f1_pct = f1.wins / max(1, f1.wins + f1.losses)
                f2_pct = f2.wins / max(1, f2.wins + f2.losses)
                f1_r   = self._get_fighter_rank(f1)
                f2_r   = self._get_fighter_rank(f2)
                f1_s   = f1_pct * 60 + (15-(f1_r or 20))*2 + random.randint(0,25)
                f2_s   = f2_pct * 60 + (15-(f2_r or 20))*2 + random.randint(0,25)
                winner = f1 if f1_s >= f2_s else f2
                loser  = f2 if f1_s >= f2_s else f1
                roll = random.random()
                if   roll < 0.28: method, rnd = "KO",  random.randint(1,3)
                elif roll < 0.48: method, rnd = "TKO", random.randint(1,3)
                elif roll < 0.63: method, rnd = "SUB", random.randint(1,3)
                else:             method, rnd = "DEC", 3

            # Ship DR2: draw short-circuit — see site A comment for rationale.
            if _is_draw_b:
                f1.draws = getattr(f1, 'draws', 0) + 1
                f2.draws = getattr(f2, 'draws', 0) + 1
                fight_result: Dict[str, Any] = {
                    "fight_id":          f"ai_fight_{week}_{f1.fighter_id}_{f2.fighter_id}",
                    "fighter1_id":       f1.fighter_id,
                    "fighter2_id":       f2.fighter_id,
                    "fighter1_name":     f1.name,
                    "fighter2_name":     f2.name,
                    "winner_id":         None,
                    "winner_name":       "",
                    "loser_id":          None,
                    "loser_name":        "",
                    "method":            "Draw",
                    "round_finished":    rnd,
                    "weight_class":      wc,
                    "event_name":        event_name,
                    "is_title_fight":    False,
                    "is_ai_fight":       True,
                    "scorecard":         None,
                    "rivalry":           None,
                    "winner_new_rank":   None,
                    "loser_new_rank":    None,
                    "winner_rank_delta": 0,
                    "loser_rank_delta":  0,
                }
                event["fights"].append(fight_result)
                continue

            # Snapshot ranks BEFORE record update
            pre_w_rank = self._get_fighter_rank(winner)
            pre_l_rank = self._get_fighter_rank(loser)

            # Update records
            winner.wins   += 1
            loser.losses  += 1
            if method in ("KO", "TKO"):
                winner.ko_wins  += 1
                loser.ko_losses = getattr(loser, 'ko_losses', 0) + 1
            elif method == "SUB":
                winner.sub_wins += 1
                loser.sub_losses = getattr(loser, 'sub_losses', 0) + 1
            self._apply_post_fight_camp_record(
                winner, loser,
                {"event_name": event_name, "is_title_fight": is_title},
                method,
            )

            # Fight history
            for ftr, res, opp in [(winner, "W", loser), (loser, "L", winner)]:
                if not hasattr(ftr, "fight_history"):
                    ftr.fight_history = []
                ftr.fight_history.append({
                    "opponent_name": opp.name,
                    "opponent_id":   opp.fighter_id,
                    "result":        res,
                    "method":        method,
                    "round_finished": rnd,
                    "event_name":    event_name,
                    "week":          week,
                })

            self._update_rankings_after_fight(wc)

            # Rank deltas AFTER rankings updated
            new_w_rank = self._get_fighter_rank(winner)
            new_l_rank = self._get_fighter_rank(loser)

            fight_result: Dict[str, Any] = {
                "fight_id":         f"ai_fight_{week}_{f1.fighter_id}_{f2.fighter_id}",
                "fighter1_id":      f1.fighter_id,
                "fighter2_id":      f2.fighter_id,
                "fighter1_name":    f1.name,
                "fighter2_name":    f2.name,
                "winner_id":        winner.fighter_id,
                "winner_name":      winner.name,
                "loser_id":         loser.fighter_id,
                "loser_name":       loser.name,
                "method":           method,
                "round_finished":   rnd,
                "weight_class":     wc,
                "event_name":       event_name,
                "is_title_fight":   False,
                "is_ai_fight":      True,
                "scorecard":        None,
                "rivalry":          None,
                # Rank data for recap display
                "winner_new_rank":  new_w_rank,
                "loser_new_rank":   new_l_rank,
                "winner_rank_delta": self._rank_delta(pre_w_rank, new_w_rank),
                "loser_rank_delta":  self._rank_delta(pre_l_rank, new_l_rank),
            }
            event["fights"].append(fight_result)
            # event["main_event"] is set exclusively post-loop by
            # _score_and_slot_fights (line ~7594). No provisional write
            # here — the fight loop runs before slot assignment, so
            # "first fight processed" is not a meaningful main event.

            # Notable finishes → news
            if method in ("KO", "TKO", "SUB"):
                icon = "💥" if method in ("KO", "TKO") else "🔒"
                self._news_items.append({
                    "headline":  f"{icon} {winner.name} def. {loser.name} by {method} (R{rnd}) at {event_name}",
                    "category":  "fight",
                    "week":      week,
                    "winner_id": winner.fighter_id,
                    "loser_id":  loser.fighter_id,
                    "fight_id":  fight.get("fight_id", ""),
                    "event_id":  event.get("event_id", ""),
                })

        # Ship G1: apply unified slot assignment via shared helper.
        # Saturday Findings #5/#6/#7: fallback path produced cards with
        # empty main_event slot, UR-vs-UR co-mains, and stacked title
        # fights because slot assignment was never wired. The primary
        # path (_build_card_for_week) has had slot assignment since
        # Ship #26 (commit e2d90e7) — Ship G1 extends the same logic
        # to this permissive-matchmaking fallback via _score_and_slot_fights.
        if event["fights"]:
            _main = self._score_and_slot_fights(event_name, week, event["fights"])
            if _main is not None:
                event["main_event"] = _main

        return event if event["fights"] else None

    # =========================================================================
    # FULL DIVISION LADDER
    # =========================================================================

    def get_full_division_ladder(self, weight_class: str,
                                  player_fighter_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Return the complete division ladder for one weight class.

        Sections:
          champion   — single WebFighter or None
          ranked     — list of WebFighter (#1–15), ordered
          unranked   — ALL remaining active fighters in division, sorted by rating
          player_row — WebFighter for the player's fighter (always present even if
                       they don't appear in any section above due to world-gen gaps)
          player_section — "champion" | "ranked" | "unranked" | None
          player_rank    — numeric rank or None
        """
        if not self._game_state:
            return {
                "champion": None, "ranked": [], "unranked": [],
                "player_row": None, "player_section": None, "player_rank": None,
            }

        division = self._game_state.divisions.get(weight_class)
        if not division:
            return {
                "champion": None, "ranked": [], "unranked": [],
                "player_row": None, "player_section": None, "player_rank": None,
            }

        # ── Champion ──────────────────────────────────────────────────────────
        champion_web = None
        champ_id     = division.champion_id
        if champ_id:
            champ_rec = self._game_state.get_fighter(champ_id)
            if champ_rec and champ_rec.is_active:
                champion_web = self._convert_real_fighter(champ_rec)

        # ── Ranked #1–15 ──────────────────────────────────────────────────────
        ranked_ids = list(division.rankings[:15])
        ranked_web = []
        for fid in ranked_ids:
            rec = self._game_state.get_fighter(fid)
            if rec and rec.is_active:
                ranked_web.append(self._convert_real_fighter(rec))

        # ── Unranked — everyone else active in this division ─────────────────
        known_ids  = {champ_id} | set(ranked_ids)
        all_in_div = [
            f for f in self._game_state.fighters.values()
            if f.weight_class == weight_class
            and f.is_active
            and f.fighter_id not in known_ids
        ]
        all_in_div.sort(key=lambda x: x.overall_rating, reverse=True)
        unranked_web = [self._convert_real_fighter(f) for f in all_in_div]

        # ── Player row ────────────────────────────────────────────────────────
        player_row     = None
        player_section = None
        player_rank    = None

        if player_fighter_id:
            # Find which section the player is in
            if champion_web and champion_web.fighter_id == player_fighter_id:
                player_row     = champion_web
                player_section = "champion"
                player_rank    = 0
            else:
                for i, f in enumerate(ranked_web):
                    if f.fighter_id == player_fighter_id:
                        player_row     = f
                        player_section = "ranked"
                        player_rank    = i + 1
                        break
                if not player_row:
                    for f in unranked_web:
                        if f.fighter_id == player_fighter_id:
                            player_row     = f
                            player_section = "unranked"
                            player_rank    = None
                            break
                # Fighter exists in game but wasn't in any division list
                # (world-gen edge case) — still show them
                if not player_row:
                    rec = self._game_state.get_fighter(player_fighter_id)
                    if rec:
                        player_row     = self._convert_real_fighter(rec)
                        player_section = "unranked"
                        player_rank    = None
                        unranked_web.append(player_row)

        return {
            "champion":       champion_web,
            "ranked":         ranked_web,
            "unranked":       unranked_web,
            "player_row":     player_row,
            "player_section": player_section,
            "player_rank":    player_rank,
        }


    # =========================================================================
    # WEEKLY CAMP DIGEST — immersion feed for dashboard + recap
    # =========================================================================

    def get_camp_digest(self) -> Dict[str, Any]:
        """
        Generate the weekly camp digest — coach observations, training
        highlights, fight week build-up, and milestone moments.
        Pulls from news_items, training plans, fight schedule, and fighter state.
        Returns structured data for the dashboard and recap.
        """
        if not self._game_state:
            return {"observations": [], "fight_week": None, "highlights": []}

        import random
        week     = self._game_state.week_number
        fighters = self._game_state.get_player_fighters()
        coach    = self._coach
        coach_name = coach.get("name", "Coach")
        coach_spec = coach.get("specialty", "boxing").lower()

        items      = []   # Feed items — each has type, text, icon, color
        highlights = []   # Milestone moments (big gains, ranking moves)
        fight_week = None # Upcoming fight context if ≤2 weeks out

        # ── Training observations from last week's news ────────────────
        training_news = [n for n in self._news_items[-20:]
                         if n.get("week") == week and
                         n.get("category") in ("training",)]
        for tn in training_news[:3]:
            h = tn.get("headline", "")
            if "+" in h and any(f.name.split()[0] in h for f in fighters):
                items.append({
                    "type":  "training",
                    "icon":  "💪",
                    "color": "var(--neon-green)",
                    "text":  h,
                })
            elif "decay" in h.lower() or "rusty" in h.lower():
                items.append({
                    "type":  "decay",
                    "icon":  "📉",
                    "color": "var(--warning)",
                    "text":  h,
                })

        # ── Coach observations — generated from fighter state ──────────
        SPECIALTY_ATTRS = {
            "boxing":    ("boxing",     "boxing"),
            "wrestling": ("takedowns",  "wrestling"),
            "bjj":       ("submissions","ground game"),
            "muay thai": ("kicks",      "striking"),
            "kicks":     ("kicks",      "striking"),
            "cardio":    ("cardio",     "conditioning"),
            "strength":  ("strength",   "strength work"),
            "cornering": ("fight_iq",   "fight IQ"),
            "strategy":  ("fight_iq",   "game planning"),
        }
        attr_key, attr_label = SPECIALTY_ATTRS.get(
            coach_spec, ("fight_iq", "overall game"))

        for fighter in fighters[:3]:
            ftr = self._game_state.get_fighter(fighter.fighter_id)
            if not ftr:
                continue
            val = getattr(ftr, attr_key, 50)
            plan = self._fighter_training_plans.get(fighter.fighter_id, {})
            intensity = plan.get("intensity", "MODERATE")

            # Positive observation — hard worker or good stat
            if intensity in ("INTENSE", "EXTREME") and val >= 65:
                items.append({
                    "type":  "coach",
                    "icon":  "🧠",
                    "color": "var(--gold)",
                    "text":  (f'"{fighter.name.split()[0]} is putting in the work. '
                              f'That {attr_label} is coming along." — {coach_name}'),
                })
            elif val >= 75:
                items.append({
                    "type":  "coach",
                    "icon":  "🧠",
                    "color": "var(--gold)",
                    "text":  ('"' + fighter.name.split()[0] + " has elite-level "
                              + attr_label + '. We are in good shape." — ' + coach_name),
                })
            elif intensity == "REST":
                items.append({
                    "type":  "rest",
                    "icon":  "😴",
                    "color": "var(--info)",
                    "text":  (f'"{fighter.name.split()[0]} is on a rest week. '
                              f'Recovery is part of the process." — {coach_name}'),
                })

            # Decline concern
            fatigue = getattr(ftr, "fatigue", 0)
            if fatigue >= 75:
                items.append({
                    "type":  "warning",
                    "icon":  "⚠️",
                    "color": "var(--blood-red)",
                    "text":  (f'"{fighter.name.split()[0]} looks drained. '
                              f'We need to manage the load before fight week." — {coach_name}'),
                })

        # ── Milestones — OVR round numbers, ranking breakthroughs ──────
        for fighter in fighters:
            ftr = self._game_state.get_fighter(fighter.fighter_id)
            if not ftr:
                continue
            ovr = int(getattr(ftr, 'overall_rating', 0))
            for milestone in (60, 65, 70, 75, 80, 85, 90):
                key = f"milestone_{fighter.fighter_id}_{milestone}"
                if ovr >= milestone and key not in self._fighter_cooldowns:
                    self._fighter_cooldowns[key] = week  # reuse as seen-flag
                    highlights.append({
                        "icon":  "⭐",
                        "color": "var(--gold)",
                        "text":  (f'{fighter.name} reached {milestone} OVR — '
                                  f'{"elite territory" if milestone >= 85 else "contender territory" if milestone >= 75 else "solid pro level"}!'),
                    })
                    break

            rank = getattr(fighter, 'ranking', None)
            if rank and rank <= 5:
                prev_key = f"top5_{fighter.fighter_id}"
                if prev_key not in self._fighter_cooldowns:
                    self._fighter_cooldowns[prev_key] = week
                    highlights.append({
                        "icon":  "🔥",
                        "color": "var(--blood-red)",
                        "text":  f'{fighter.name} is ranked #{rank} — Top 5 in the world!',
                    })

        # ── Fight week build-up ────────────────────────────────────────
        scheduled = self.get_scheduled_fights()
        player_ids = {f.fighter_id for f in fighters}
        for sf in sorted(scheduled, key=lambda x: x.get("weeks_until", 99)):
            wu = sf.get("week", 0) - week
            if wu > 2:
                break
            f1id = sf.get("fighter1_id", "")
            f2id = sf.get("fighter2_id", "")
            if f1id not in player_ids and f2id not in player_ids:
                continue

            player_fid = f1id if f1id in player_ids else f2id
            opp_id     = f2id if f1id in player_ids else f1id
            player_f   = self._game_state.get_fighter(player_fid)
            opp_f      = self._game_state.get_fighter(opp_id)
            if not player_f or not opp_f:
                continue

            fatigue   = getattr(player_f, "fatigue", 0)
            opp_style = self._game_state._fighter_data.get(opp_id, {}).get("style", "Balanced")
            opp_rec   = f"{opp_f.wins}-{opp_f.losses}"
            opp_rank  = self._get_fighter_rank(opp_f)

            cond_word = ("fresh" if fatigue < 25 else
                         "ready" if fatigue < 50 else
                         "a little tired" if fatigue < 70 else "gassed")
            cond_color = ("var(--neon-green)" if fatigue < 25 else
                          "var(--info)" if fatigue < 50 else
                          "var(--warning)" if fatigue < 70 else "var(--blood-red)")

            # Rivalry heat
            rivalry_line = ""
            if RIVALRY_AVAILABLE:
                try:
                    rsys = get_rivalry_system()
                    rv = rsys.get_rivalry(player_fid, opp_id)
                    if rv and rv.score >= 40:
                        rivalry_line = f" There's bad blood here — heat level {rv.score}."
                except Exception:
                    pass

            rank_str = (f"#{opp_rank}" if opp_rank else "unranked")
            weeks_str = ("FIGHT WEEK" if wu <= 0 else
                         "fight next week" if wu == 1 else f"{wu} weeks out")

            fight_week = {
                "fighter_name": player_f.name,
                "opponent_name": opp_f.name,
                "opponent_record": opp_rec,
                "opponent_rank":   rank_str,
                "opponent_style":  opp_style,
                "opponent_momentum": self._get_momentum_tag(opp_f) if opp_f else "",
                "event_name":      sf.get("event_name", ""),
                "weeks_until":     wu,
                "weeks_str":       weeks_str,
                "condition":       cond_word,
                "condition_color": cond_color,
                "fatigue":         fatigue,
                "rivalry_line":    rivalry_line,
                "is_title":        sf.get("is_title_fight", False),
                "coach_note": (
                    '"' + player_f.name.split()[0] + " looks " + cond_word +
                    " heading in. Watch their " + opp_style.lower() +
                    " — that is where this fight gets decided." +
                    rivalry_line + '" — ' + coach_name
                ),
            }
            break

        return {
            "observations":      items[:6],   # Cap at 6 items
            "highlights": highlights[:3],
            "fight_week": fight_week,
            "coach_name": coach_name,
        }


    # =========================================================================
    # RECORD BOOK
    # =========================================================================

    def get_record_book(self) -> Dict[str, Any]:
        """
        Compile all-time records across all fighters.
        Returns records by category for the Record Book page.
        """
        if not self._game_state:
            return {}

        fighters = list(self._game_state.fighters.values())
        active   = [f for f in fighters if f.is_active]

        def streak(f):
            s = 0
            for h in reversed(getattr(f, 'fight_history', [])):
                if isinstance(h, dict) and h.get('result') == 'W':
                    s += 1
                else:
                    break
            return s

        def max_streak(f):
            best = cur = 0
            for h in getattr(f, 'fight_history', []):
                if isinstance(h, dict) and h.get('result') == 'W':
                    cur += 1; best = max(best, cur)
                else:
                    cur = 0
            return best

        def web(f):
            return self._convert_real_fighter(f)

        # Sort helpers
        by_wins     = sorted(active, key=lambda f: f.wins, reverse=True)
        by_ko       = sorted(active, key=lambda f: getattr(f,'ko_wins',0), reverse=True)
        by_sub      = sorted(active, key=lambda f: getattr(f,'sub_wins',0), reverse=True)
        by_streak   = sorted(active, key=lambda f: streak(f), reverse=True)
        by_maxstreak= sorted(active, key=lambda f: max_streak(f), reverse=True)
        by_total    = sorted(active, key=lambda f: f.wins + f.losses, reverse=True)

        # Career fight-stat helpers
        def career_strikes(f):
            return int(self._game_state._fighter_data.get(
                f.fighter_id, {}).get('career_strikes', 0))
        def career_td(f):
            return int(self._game_state._fighter_data.get(
                f.fighter_id, {}).get('career_takedowns', 0))
        def career_sub_att(f):
            return int(self._game_state._fighter_data.get(
                f.fighter_id, {}).get('career_sub_attempts', 0))

        by_strikes = sorted(active, key=career_strikes, reverse=True)
        by_td      = sorted(active, key=career_td, reverse=True)
        by_sub_att = sorted(active, key=career_sub_att, reverse=True)

        def row(f, extra=""):
            wf = web(f)
            return {"fighter": wf, "value": extra}

        return {
            "most_wins":      [{"fighter": web(f), "value": f.wins}       for f in by_wins[:5]],
            "most_ko":        [{"fighter": web(f), "value": getattr(f,'ko_wins',0)} for f in by_ko[:5]],
            "most_sub":       [{"fighter": web(f), "value": getattr(f,'sub_wins',0)} for f in by_sub[:5]],
            "active_streak":  [{"fighter": web(f), "value": streak(f)}    for f in by_streak[:5] if streak(f) > 0],
            "longest_streak": [{"fighter": web(f), "value": max_streak(f)} for f in by_maxstreak[:5] if max_streak(f) > 0],
            "most_fights":    [{"fighter": web(f), "value": f.wins+f.losses} for f in by_total[:5]],
            "most_strikes":   [{"fighter": web(f), "value": career_strikes(f)}
                               for f in by_strikes[:5] if career_strikes(f) > 0],
            "most_takedowns": [{"fighter": web(f), "value": career_td(f)}
                               for f in by_td[:5] if career_td(f) > 0],
            "most_sub_attempts": [{"fighter": web(f), "value": career_sub_att(f)}
                                  for f in by_sub_att[:5] if career_sub_att(f) > 0],
            "hof_inductees":  sorted(self._hof_inductees,
                                     key=lambda h: h["prestige_score"], reverse=True),
            "title_records":  self._get_title_records(),
        }

    def _accumulate_career_stats(self, fighter_id: str,
                                  strikes: int, takedowns: int,
                                  sub_attempts: int, control_time: float,
                                  week: int) -> None:
        """Add per-fight stats to career totals in _fighter_data.
        Fires milestone news when thresholds are crossed."""
        if not self._game_state or fighter_id not in self._game_state._fighter_data:
            return

        fdata = self._game_state._fighter_data[fighter_id]

        # Accumulate
        prev_strikes  = int(fdata.get('career_strikes', 0))
        prev_td       = int(fdata.get('career_takedowns', 0))
        prev_sub_att  = int(fdata.get('career_sub_attempts', 0))
        prev_ctrl     = float(fdata.get('career_control_time', 0.0))

        new_strikes   = prev_strikes + strikes
        new_td        = prev_td + takedowns
        new_sub_att   = prev_sub_att + sub_attempts
        new_ctrl      = prev_ctrl + control_time

        fdata['career_strikes']       = new_strikes
        fdata['career_takedowns']     = new_td
        fdata['career_sub_attempts']  = new_sub_att
        fdata['career_control_time']  = round(new_ctrl, 1)

        # Get fighter name for news
        fighter = self._game_state.get_fighter(fighter_id)
        name = getattr(fighter, 'name', 'Fighter') if fighter else 'Fighter'

        # Milestone news — strike thresholds
        _STRIKE_MILESTONES = [100, 250, 500, 1000, 2000]
        for threshold in _STRIKE_MILESTONES:
            if prev_strikes < threshold <= new_strikes:
                self._news_items.insert(0, {
                    "headline": f"💥 {name} lands their {threshold}th career significant strike!",
                    "category": "record",
                    "week": week,
                })

        # Milestone news — takedown thresholds
        _TD_MILESTONES = [25, 50, 100, 200]
        for threshold in _TD_MILESTONES:
            if prev_td < threshold <= new_td:
                self._news_items.insert(0, {
                    "headline": f"🤼 {name} completes their {threshold}th career takedown!",
                    "category": "record",
                    "week": week,
                })

    def _apply_chin_erosion(self, fighter_id: str, method: str, week: int) -> None:
        """Apply chin erosion after a KO/TKO loss.

        First 2 KO losses: recoverable stat decrease (-2, -3).
        3rd+ KO losses: additional permanent -1 per loss on top of recoverable hit.
        Permanent erosion is tracked separately and subtracted from any chin gains
        during training — the fighter's ceiling drops, not just their current value.
        Only applies to KO and TKO finishes — not decisions or submissions.
        """
        if not self._game_state:
            return

        method_upper = str(method).upper()
        if not any(m in method_upper for m in ['KO', 'TKO']):
            return

        fdata = self._game_state._fighter_data.get(fighter_id, {})
        if not fdata:
            return

        fighter = self._game_state.get_fighter(fighter_id)
        if not fighter:
            return

        ko_losses = int(fdata.get('ko_losses_received', 0))
        ko_losses += 1
        fdata['ko_losses_received'] = ko_losses

        if ko_losses == 1:
            erosion = 2
        elif ko_losses == 2:
            erosion = 3
        else:
            erosion = 4

        current_chin = float(fdata.get('chin', getattr(fighter, 'chin', 50)))
        new_chin = max(20.0, current_chin - erosion)
        fdata['chin'] = round(new_chin, 1)

        if hasattr(fighter, 'chin'):
            fighter.chin = new_chin

        if ko_losses >= 3:
            perm = float(fdata.get('chin_permanent_erosion', 0.0))
            perm += 1.0
            fdata['chin_permanent_erosion'] = round(perm, 1)

        name = getattr(fighter, 'name', 'Fighter')
        if ko_losses == 1:
            headline = f"🩹 {name} takes their first KO loss — chin durability affected."
        elif ko_losses == 2:
            headline = f"⚠️ {name} suffers a second KO loss. Chin durability is a concern."
        else:
            headline = f"🚨 {name} knocked out for the {ko_losses}{'rd' if ko_losses==3 else 'th'} time. Serious durability questions."

        self._news_items.insert(0, {
            "headline": headline,
            "category": "injury",
            "week": week,
        })

        self._clear_cache()

    def _get_title_records(self) -> Dict[str, Any]:
        """Ship HOF1: aggregate title-related records across champions."""
        champ_data: Dict[str, Dict[str, Any]] = {}
        for _wc_reigns in self._title_history.values():
            for _r in _wc_reigns:
                _fid = _r.get("champion_id", "")
                if not _fid:
                    continue
                if _fid not in champ_data:
                    champ_data[_fid] = {
                        "fighter_id": _fid,
                        "name":       _r.get("champion_name", ""),
                        "reigns":     0,
                        "defenses":   0,
                        "divisions":  set(),
                    }
                _cd = champ_data[_fid]
                _cd["reigns"]   += 1
                _cd["defenses"] += _r.get("successful_defenses", 0)
                _cd["divisions"].add(_r.get("weight_class", ""))
        for _cd in champ_data.values():
            _cd["division_count"] = len(_cd["divisions"])
            del _cd["divisions"]
        _ranked = sorted(champ_data.values(), key=lambda x: x["reigns"],   reverse=True)
        _by_def = sorted(champ_data.values(), key=lambda x: x["defenses"], reverse=True)
        return {
            "most_reigns":   _ranked[:5],
            "most_defenses": _by_def[:5],
        }

    # =========================================================================
    # ENHANCED NEWS — streak and record categories
    # =========================================================================

    def _fire_streak_news(self, fighter, week: int) -> None:
        """Fire a streak milestone news item."""
        ws = getattr(fighter, 'win_streak', 0)
        if ws in (3, 5, 7, 10):
            self._news_items.insert(0, {
                "headline": f"🔥 {fighter.name} is on a {ws}-fight win streak!",
                "category": "streak",
                "week":     week,
            })

    def _fire_record_news(self, fighter, week: int) -> None:
        """Fire a personal record news item."""
        wins = fighter.wins
        if wins in (5, 10, 15, 20):
            self._news_items.insert(0, {
                "headline": f"📊 {fighter.name} reaches {wins} career wins!",
                "category": "record",
                "week":     week,
            })

    # =========================================================================
    # COACH 3-STAT SYSTEM
    # =========================================================================

    def get_coach_detail(self) -> Dict[str, Any]:
        """
        Return coach with Teaching / Cornering / Scouting breakdown.
        Derived from rating + specialty so no new storage needed.
        """
        c     = self._coach
        base  = c.get("rating", 60)
        spec  = c.get("specialty", "boxing").lower()

        # Specialties that emphasize each stat
        TEACH_SPECS   = {"bjj","wrestling","boxing","muay thai","kicks","grappling","submissions"}
        CORNER_SPECS  = {"cornering","strategy","boxing","striking","mma"}
        SCOUT_SPECS   = {"cornering","strategy","conditioning","strength"}

        import random as _r
        _seed = hash(c.get("name","coach") + spec) % 10000
        _r.seed(_seed)

        def _stat(is_primary, base):
            if is_primary:
                return min(99, base + _r.randint(3, 10))
            return max(40, base - _r.randint(5, 20))

        teaching   = _stat(spec in TEACH_SPECS,  base)
        cornering  = _stat(spec in CORNER_SPECS, base)
        scouting   = _stat(spec in SCOUT_SPECS,  base)

        return {
            **c,
            "teaching":  teaching,
            "cornering": cornering,
            "scouting":  scouting,
            "teaching_desc":  "Weekly passive stat gains for your fighters",
            "cornering_desc": "Between-round fight IQ and composure boost",
            "scouting_desc":  "Quality of amateur tips from coach's region",
        }

    # =========================================================================
    # POPULARITY
    # =========================================================================

    def get_fighter_popularity(self, fighter_id: str) -> int:
        """Return a fighter's popularity score (0-100)."""
        f = self._game_state.get_fighter(fighter_id) if self._game_state else None
        return getattr(f, 'popularity', 10) if f else 10

    def get_top_popular(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top fighters by popularity for the dashboard widget."""
        if not self._game_state:
            return []
        fighters = sorted(
            self._game_state.fighters.values(),
            key=lambda f: getattr(f, 'popularity', 10),
            reverse=True,
        )
        out = []
        for f in fighters[:limit]:
            wf = self._convert_real_fighter(f)
            out.append({
                "fighter":    wf,
                "popularity": getattr(f, 'popularity', 10),
            })
        return out

    # =========================================================================
    # RIVALRIES DASHBOARD WIDGET
    # =========================================================================

    def get_hot_rivalries(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Return the hottest current rivalries for dashboard display."""
        if not RIVALRY_AVAILABLE:
            return []
        try:
            rsys = get_rivalry_system()
            all_rivalries = []
            seen = set()
            if self._game_state:
                for fid in list(self._game_state.fighters.keys())[:50]:
                    for r in rsys.get_active_rivalries(fid):
                        key = tuple(sorted([r.fighter1_id, r.fighter2_id]))
                        if key in seen or r.score < 25:
                            continue
                        seen.add(key)
                        all_rivalries.append(r)
            all_rivalries.sort(key=lambda r: r.score, reverse=True)
            out = []
            for r in all_rivalries[:limit]:
                f1 = self._game_state.get_fighter(r.fighter1_id) if self._game_state else None
                f2 = self._game_state.get_fighter(r.fighter2_id) if self._game_state else None
                if not f1 or not f2:
                    continue
                stage = get_heat_stage(r.score)
                heat_colors = {
                    "neutral":"#6b7280","tension":"#3b82f6",
                    "bad_blood":"#f59e0b","heated":"#ef4444","war":"#dc2626",
                }
                out.append({
                    "f1_name":  f1.name,
                    "f2_name":  f2.name,
                    "f1_id":    r.fighter1_id,
                    "f2_id":    r.fighter2_id,
                    "score":    r.score,
                    "stage":    stage.value.replace("_"," ").title(),
                    "color":    heat_colors.get(stage.value, "#6b7280"),
                    "fights":   r.fights,
                })
            return out
        except Exception:
            return []

    # =========================================================================
    # CARD SCHEDULING SYSTEM
    # =========================================================================

    def _get_fighter_lose_streak(self, fighter) -> int:
        """Count current losing streak from fight history."""
        streak = 0
        for h in reversed(getattr(fighter, 'fight_history', [])):
            r = h.get('result') if isinstance(h, dict) else getattr(h, 'result', '')
            if r == 'L':
                streak += 1
            else:
                break
        return streak

    def _get_sponsor_client_count(self, sponsor_id: str) -> int:
        """Count how many fighters currently hold this sponsor."""
        if not self._game_state:
            return 0
        count = 0
        for fid, fdata in self._game_state._fighter_data.items():
            for s in fdata.get("sponsors", []) or []:
                if s.get("sponsor_id") == sponsor_id:
                    count += 1
        return count

    def _get_fighter_win_streak(self, fighter) -> int:
        """Compute current win streak from fight_history.
        Canonical source — mirrors _get_fighter_lose_streak."""
        streak = 0
        for h in reversed(getattr(fighter, 'fight_history', []) or []):
            r = h.get('result') if isinstance(h, dict) \
                else getattr(h, 'result', '')
            if r == 'W':
                streak += 1
            else:
                break
        return streak

    def _cooldown_weeks(self, fighter, is_champion: bool = False) -> int:
        """
        Cooldown = pure recovery time before a fighter can SIGN another fight.
        The fight itself is then scheduled 3-12 weeks out (handled by _weeks_out_for_fight).

        Philosophy: fighters sign contracts while hot. Cooldown is just
        physical/promotional recovery — not the full gap between fights.

        Real cadence this produces (post-Ship M2 — winner cooldown removed):
          Winners (any tier): 0w cooldown — available to sign immediately;
                              fight-to-fight gap comes from camp scheduling
                              alone (3-12w via _weeks_out_for_fight).
          Loser (1 loss):    4w cooldown + 3-5w camp  = ~7-9w fight-to-fight
          Loser (streak):    up to 8w cooldown — taking L's, need time to reset
        """
        lose_streak = self._get_fighter_lose_streak(fighter)
        rank = self._get_fighter_rank(fighter)

        if is_champion:
            return 0  # Winner cooldown removed (was 4w champion defense)

        if lose_streak == 0:
            # Winner — cooldown removed (was 1-2w based on rank)
            if rank is not None and rank <= 5:
                return 0
            elif rank is not None and rank <= 10:
                return 0
            elif rank is not None:
                return 0
            else:
                return 0

        # Loser — needs more time, especially on streaks
        base = 4
        return min(8, base + (lose_streak - 1) * 2)

    def _apply_cooldown(self, fighter, week: int, is_champion: bool = False) -> None:
        """Record when this fighter is next available."""
        cooldown = self._cooldown_weeks(fighter, is_champion)
        self._fighter_cooldowns[fighter.fighter_id] = week + cooldown

    def _is_available(self, fighter_id: str, week: int) -> bool:
        """True if fighter has no cooldown and signing delay blocking them."""
        return (self._fighter_cooldowns.get(fighter_id, 0) <= week and
                self._fighter_signing_available.get(fighter_id, 0) <= week)

    def _signing_delay_weeks(self, fighter, is_champion: bool = False) -> int:
        """Weeks a fighter waits after cooldown before they can be booked.
        Applies to winners and losers alike — everyone takes time to decide.
        Champions/top-5: 3w, top 6-15: 2w, unranked: 1w.
        """
        if is_champion:
            return 3
        rank = self._get_fighter_rank(fighter)
        if rank is not None and rank <= 5:
            return 3
        elif rank is not None and rank <= 15:
            return 2
        else:
            return 1

    def _apply_signing_delay(self, fighter, week: int, is_champion: bool = False) -> None:
        """Record when this fighter is next claimable for booking.
        Called after _apply_cooldown. The signing window opens after
        cooldown ends, so claimable_week = cooldown_end + signing_delay.
        """
        cooldown_end = self._fighter_cooldowns.get(fighter.fighter_id, week)
        delay = self._signing_delay_weeks(fighter, is_champion)
        self._fighter_signing_available[fighter.fighter_id] = cooldown_end + delay

    def _is_signable(self, fighter_id: str, week: int) -> bool:
        """True if fighter's signing window has opened this week."""
        return self._fighter_signing_available.get(fighter_id, 0) <= week

    def _weeks_since_fought(self, f1, f2) -> Optional[int]:
        """
        Return how many weeks ago f1 and f2 last fought each other.
        Returns None if they have never fought.
        Used to enforce rematch cooldowns in card building.
        """
        current_week = self._game_state.week_number if self._game_state else 0
        f2_id = f2.fighter_id
        for entry in getattr(f1, 'fight_history', []):
            if isinstance(entry, dict) and entry.get('opponent_id') == f2_id:
                fought_week = entry.get('week', 0)
                if fought_week:
                    return current_week - fought_week
        # Also check _fighter_data for belt-and-suspenders
        if self._game_state:
            fd = self._game_state._fighter_data.get(f1.fighter_id, {})
            for entry in fd.get('fight_history', []):
                if isinstance(entry, dict) and entry.get('opponent_id') == f2_id:
                    fought_week = entry.get('week', 0)
                    if fought_week:
                        return current_week - fought_week
        return None

    def _record_title_result(
        self,
        weight_class: str,
        winner,
        loser,
        method: str,
        rnd: int,
        event_name: str,
        week: int,
    ) -> None:
        """
        Record a title fight result into _title_history and update
        division.champion_id and fighter.is_champion flags.
        Called after every title fight regardless of player involvement.
        """
        if not self._game_state:
            return

        division = self._game_state.divisions.get(weight_class)
        if not division:
            return

        old_champ_id = division.champion_id
        is_new_champ = (winner.fighter_id != old_champ_id)

        # Update division + fighter flags
        if is_new_champ:
            # Strip old champion
            old_champ = self._game_state.fighters.get(old_champ_id)
            if old_champ:
                old_champ.is_champion = False
            # Crown new champion
            winner.is_champion = True
            division.champion_id   = winner.fighter_id
            division.champion_name = winner.name
            print(f"  🏆 [TITLE CHANGE] {winner.name} wins {weight_class} belt "
                  f"from {loser.name} via {method} R{rnd} at {event_name}")
        else:
            print(f"  🏆 [TITLE DEFENSE] {winner.name} retains {weight_class} belt "
                  f"vs {loser.name} via {method} R{rnd} at {event_name}")

        # Record into _title_history
        if weight_class not in self._title_history:
            self._title_history[weight_class] = []

        history = self._title_history[weight_class]

        if is_new_champ:
            # Close out previous reign
            if history and history[-1].get("is_active"):
                history[-1]["is_active"]      = False
                history[-1]["lost_week"]       = week
                history[-1]["lost_event"]      = event_name
                history[-1]["lost_to_name"]    = winner.name
                history[-1]["lost_method"]     = method

            # Open new reign
            old_name = loser.name if is_new_champ else None
            history.append({
                "champion_id":         winner.fighter_id,
                "champion_name":       winner.name,
                "weight_class":        weight_class,
                "won_week":            week,
                "won_event":           event_name,
                "won_from_name":       old_name,
                "won_method":          method,
                "successful_defenses": 0,
                "is_active":           True,
                "lost_week":           None,
                "lost_event":          None,
                "lost_to_name":        None,
                "lost_method":         None,
            })
        else:
            # Successful defense — increment counter on active reign
            if history and history[-1].get("is_active"):
                history[-1]["successful_defenses"] = \
                    history[-1].get("successful_defenses", 0) + 1

    def get_champions_history(self, weight_class: str) -> Dict[str, Any]:
        """Return belt lineage data for the champions page."""
        if not self._game_state:
            return {"reigns": [], "total_changes": 0, "most_defenses": 0}

        history = self._title_history.get(weight_class, [])

        # If no recorded history, seed from current division state
        if not history:
            division = self._game_state.divisions.get(weight_class)
            if division and division.champion_id:
                champ = self._game_state.fighters.get(division.champion_id)
                if champ:
                    history = [{
                        "champion_id":         champ.fighter_id,
                        "champion_name":       champ.name,
                        "weight_class":        weight_class,
                        "won_week":            0,
                        "won_event":           "Season Opener",
                        "won_from_name":       None,
                        "won_method":          "Inaugural Champion",
                        "successful_defenses": 0,
                        "is_active":           True,
                        "lost_week":           None,
                        "lost_event":          None,
                        "lost_to_name":        None,
                        "lost_method":         None,
                    }]

        total_changes  = sum(1 for r in history if r.get("won_method") != "Inaugural Champion")
        most_defenses  = max((r.get("successful_defenses", 0) for r in history), default=0)

        return {
            "reigns":        list(reversed(history)),  # newest first
            "total_changes": total_changes,
            "most_defenses": most_defenses,
        }

    def _would_decline_fight(self, fighter, opponent,
                               rank_f: Optional[int],
                               rank_opp: Optional[int],
                               weeks_out: int = 6) -> bool:
        """
        Returns True if this fighter (via their camp's archetype) would
        decline the proposed matchup. Used during card building.

        Decline conditions:
        1. Elite Academy / Veteran Hub: refuses opponents ranked more than
           6 spots below them (no ranking padding)
        2. Any camp: refuses a fight with less than 3 weeks notice if
           fighter is currently on a losing streak
        3. Star Factory: refuses opponents with popularity below 15 if
           fighter is in top 5 (image protection)
        4. Low morale fighter (< 40): 30% chance to refuse any fight
        """
        if not fighter or not self._game_state:
            return False

        import random
        camp_id  = getattr(fighter, 'camp_id', None)
        if not camp_id:
            return False

        arch_name = self._get_camp_archetype(camp_id)
        rank_f    = rank_f or 99
        rank_opp  = rank_opp or 99

        # 1. Rank gap — elite camps protect their fighters from mismatches
        rank_gap = rank_opp - rank_f  # positive = opponent is lower ranked
        if arch_name in ("Elite Academy", "Veteran Hub", "Star Factory"):
            if rank_gap > 6 and rank_f <= 10:
                # Top-10 ranked fighter won't fight someone 6+ spots below
                return random.random() < 0.70  # 70% decline

        # 2. Short notice + losing streak
        lose_streak = getattr(fighter, 'lose_streak', 0) or 0
        if weeks_out < 3 and lose_streak >= 2:
            return random.random() < 0.55

        # 3. Star Factory image protection
        if arch_name == "Star Factory" and rank_f <= 5:
            opp_pop = getattr(opponent, 'popularity', 0) or 0
            if opp_pop < 15:
                return random.random() < 0.50

        # 4. Low morale
        # Check morale from _contracts if it's a player fighter,
        # otherwise approximate from fight record
        morale = 75
        if fighter.fighter_id in self._contracts:
            morale = self._contracts[fighter.fighter_id].get('morale', 75)
        elif lose_streak >= 3:
            morale = 30  # Approximate bad morale from losing streak
        if morale < 40:
            return random.random() < 0.30

        return False

    def _matchup_score(self, f1, f2, is_title: bool = False) -> float:
        """Score a matchup for card slot assignment — rank and record only, no OVR."""
        if CARD_BUILDER_AVAILABLE and f1 and f2:
            r1 = self._get_fighter_rank(f1)
            r2 = self._get_fighter_rank(f2)
            return self._card_builder.calculate_matchup_score(
                fighter1_rating=0,   # unused in new formula
                fighter2_rating=0,
                fighter1_rank=r1,
                fighter2_rank=r2,
                is_title_fight=is_title,
                fighter1_wins=getattr(f1, 'wins', 0),
                fighter1_losses=getattr(f1, 'losses', 0),
                fighter2_wins=getattr(f2, 'wins', 0),
                fighter2_losses=getattr(f2, 'losses', 0),
            )
        # Fallback — rank-based only
        r1 = self._get_fighter_rank(f1) if f1 else None
        r2 = self._get_fighter_rank(f2) if f2 else None
        if r1 is not None and r2 is not None:
            gap = abs(r1 - r2)
            return max(0, 70 - gap * 4)
        return 20.0

    def _assign_card_slot(self, event_name: str, score: float,
                           is_title: bool, combined_rating: int,
                           f1_rank: Optional[int] = None,
                           f2_rank: Optional[int] = None,
                           f1=None, f2=None,
                           min_slot: Optional["CardSlot"] = None) -> str:
        """Return slot string for a fight.
        min_slot: optional caller-provided floor. When passed, overrides
        the internally-computed rank-based floor. Used by callers that
        need to force a slot (e.g., excess title fights → CO_MAIN floor).
        """
        if not CARD_BUILDER_AVAILABLE:
            return "prelim"

        ranks = [r for r in [f1_rank, f2_rank] if r is not None]
        top_rank = min(ranks) if ranks else None

        # Top-5 hard floor: any fight where either fighter is top-5 gets
        # an elevated slot regardless of title-eligibility check. The old
        # matchup_credible gate (require both fighters title-eligible)
        # was too restrictive and let title-tier matchups fall to prelims.
        # If caller provided min_slot, use it directly (override path).
        # Ship CB2: tightened rank-based floor. Ranks 1-2 → CO_MAIN min;
        # ranks 3-10 → MAIN_CARD min. Unranked / rank 11+ have no floor
        # and can fall to PRELIM / EARLY_PRELIM via score routing.
        if min_slot is None and top_rank is not None:
            if top_rank <= 2:
                score = max(score, SCORE_THRESHOLDS[CardSlot.CO_MAIN] + 1)
                min_slot = CardSlot.CO_MAIN
            elif top_rank <= 10:
                score = max(score, SCORE_THRESHOLDS[CardSlot.MAIN_CARD] + 1)
                min_slot = CardSlot.MAIN_CARD

        slot, _ = self._card_builder.assign_slot(
            event_name=event_name,
            weeks_until=4,
            matchup_score=score,
            is_title_fight=is_title,
            combined_rating=combined_rating,
            min_slot=min_slot,
        )
        return slot.value

    def _print_event_card(
        self,
        card: Dict[str, Any],
        event_name: str,
        target_week: int,
    ) -> None:
        """Structured card printer — Ship CB1.
        Groups fights by slot with headers and scores visible
        for diagnostics. Replaces two inline print blocks."""
        SLOT_HEADERS = {
            "main_event":  "── MAIN EVENT ──",
            "co_main":     "── CO-MAIN ──",
            "main_card":   "── MAIN CARD ──",
            "prelim":      "── PRELIMS ──",
            "early_prelim":"── EARLY PRELIMS ──",
        }
        SLOT_ORDER = ["main_event", "co_main", "main_card",
                      "prelim", "early_prelim"]

        def _rank_str(r):
            if r == 0: return "#C"
            if r is not None: return f"#{r}"
            return "UR"

        def _rank_of(fid):
            if not fid or not self._game_state:
                return None
            ftr = self._game_state.get_fighter(fid)
            return self._get_fighter_rank(ftr) if ftr else None

        fights = card.get("fights", [])
        by_slot: Dict[str, List[Dict[str, Any]]] = {s: [] for s in SLOT_ORDER}
        for f in fights:
            slot = f.get("card_slot", "prelim")
            if slot not in by_slot:
                slot = "prelim"
            by_slot[slot].append(f)

        total = len(fights)
        print(f"📅 {event_name} (Wk {target_week}) — {total} fights:")

        for slot in SLOT_ORDER:
            slot_fights = by_slot[slot]
            if not slot_fights:
                continue
            print(f"   {SLOT_HEADERS[slot]}")
            for f in slot_fights:
                f1 = f.get("fighter1_name", "?")
                f2 = f.get("fighter2_name", "?")
                r1 = _rank_str(_rank_of(f.get("fighter1_id")))
                r2 = _rank_str(_rank_of(f.get("fighter2_id")))
                title = "🏆" if f.get("is_title_fight") else ""
                score = f.get("_g1_score")
                score_str = f" [score:{score:.0f}]" if score is not None else ""
                print(f"   {title}{f1}{r1} vs {f2}{r2}{score_str}")

    def _score_and_slot_fights(self, event_name: str, target_week: int,
                                  fight_dicts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Ship G1: shared slot-assignment helper.

        Walks fight_dicts (already on the card), scores each via
        _matchup_score, applies title-fight cap (max 2 per card,
        different divisions; excess demoted to is_title_fight=False),
        sorts by score descending, and writes card_slot to each dict
        via _assign_card_slot with co_main_used tracking.

        Mutates fight_dicts in place. Returns the dict that received
        the main_event slot (or None if no fights). Caller updates
        event["main_event"] from the return value.

        Expected fight_dict shape:
          - fighter1_id, fighter2_id (required)
          - is_title_fight (bool, optional — default False)
          - weight_class (str, optional — used for title-cap dedup)
          - card_slot (written in place)

        This helper is currently called from _simulate_ai_fights_week
        (the permissive-matchmaking fallback path). _build_card_for_week
        retains its inline slot-assignment integrated with lead-time
        routing (Ship #26's proven path) — both paths converge at the
        underlying _assign_card_slot helper.
        """
        if not fight_dicts or not self._game_state:
            return None

        # Score each fight up front (cache as private key on dict)
        for f in fight_dicts:
            f1 = self._game_state.get_fighter(f.get("fighter1_id", ""))
            f2 = self._game_state.get_fighter(f.get("fighter2_id", ""))
            f["_g1_score"] = self._matchup_score(
                f1, f2, bool(f.get("is_title_fight", False))
            )

        # Sort by score descending — best matchups first
        fight_dicts.sort(key=lambda x: x.get("_g1_score", 0), reverse=True)

        # Title-fight cap: max 2 per card, must be different divisions.
        # Excess title fights KEEP is_title_fight=True (preserves semantic
        # truth for engine + UI: rounds, headline, "title defense" copy).
        # The cap is enforced via a CO_MAIN slot floor passed to
        # _assign_card_slot below, so excess title fights never fall to
        # prelims even when ME and CO_MAIN are already taken.
        title_count = 0
        title_divisions: Set[str] = set()
        _excess_title_fids: Set[str] = set()
        for f in fight_dicts:
            if f.get("is_title_fight"):
                wc = f.get("weight_class", "")
                if title_count < 2 and wc not in title_divisions:
                    title_count += 1
                    title_divisions.add(wc)
                else:
                    _excess_title_fids.add(f.get("fight_id", ""))

        # Reset CardBuilder state for this event so the assign_slot
        # capacity counters start clean (matches Ship #26's update-from-
        # fights pattern at line 8184). Pass an empty list since we're
        # about to call assign_slot for each fight in order — that
        # increments the state correctly.
        if CARD_BUILDER_AVAILABLE:
            self._card_builder.update_card_state_from_fights(event_name, target_week, [])

        main_event_dict: Optional[Dict[str, Any]] = None
        co_main_used = 0
        for f in fight_dicts:
            f1 = self._game_state.get_fighter(f.get("fighter1_id", ""))
            f2 = self._game_state.get_fighter(f.get("fighter2_id", ""))
            r1 = self._get_fighter_rank(f1) if f1 else None
            r2 = self._get_fighter_rank(f2) if f2 else None

            # Co-main override: first #1-rank fight can claim co_main,
            # subsequent ones get demoted to main_card (mirrors primary
            # path logic at line 8418-8423).
            override_f1, override_f2 = r1, r2
            ranks = [r for r in [r1, r2] if r is not None]
            top_rank = min(ranks) if ranks else None
            if top_rank is not None and top_rank <= 1 and co_main_used >= 1:
                override_f1 = 3 if r1 == 1 else r1
                override_f2 = 3 if r2 == 1 else r2

            combined_rating = 100
            if f1 and f2:
                combined_rating = (getattr(f1, 'overall_rating', 50) +
                                   getattr(f2, 'overall_rating', 50))

            # Excess title fights get a CO_MAIN floor — keeps title fights
            # off the prelims even when ME + CO_MAIN are already taken by
            # the first two title fights on the card.
            _slot_floor = (CardSlot.CO_MAIN
                           if f.get("fight_id", "") in _excess_title_fids
                           else None)
            slot = self._assign_card_slot(
                event_name,
                f.get("_g1_score", 0),
                bool(f.get("is_title_fight", False)),
                combined_rating=combined_rating,
                f1_rank=override_f1, f2_rank=override_f2,
                f1=f1, f2=f2,
                min_slot=_slot_floor,
            )
            f["card_slot"] = slot
            if slot in ("co_main", "main_event"):
                co_main_used += 1
            if slot == "main_event" and main_event_dict is None:
                main_event_dict = f

        # Clean up the temporary scoring key — don't pollute the saved dict
        for f in fight_dicts:
            f.pop("_g1_score", None)

        return main_event_dict

    def _create_empty_card_dict(self, target_week: int) -> Dict[str, Any]:
        """Sub-ship A — empty card dict for a target week. Used by both
        _build_card_for_week (when no drained items exist) and
        _top_up_pipeline's hand-off pass (when target week's card needs
        creating to receive a drained queue item)."""
        return {
            "event_id":    f"event_{target_week}",
            "event_name":  self._dfc_label(target_week),
            "week":        target_week,
            "fights":      [],
            "is_ai_event": True,
            "locked":      False,
        }

    def _build_card_for_week(self, target_week: int) -> Dict[str, Any]:
        """
        Build a full DFC card for target_week.
        - 12 fights, structured by card slot
        - Ranked vs ranked preferred
        - Cooldowns respected
        - Player's booked fights inserted automatically
        """
        import random

        event_name = self._dfc_label(target_week)
        event_id   = f"event_{target_week}"

        # Sub-ship A: reuse existing card if hand-off pass already drained
        # queued fights into it. Otherwise create fresh via shared helper.
        # Drained fights count toward target_count and are reflected in
        # all_booked downstream (the target_week skip is also dropped below).
        card = self._upcoming_cards.get(target_week)
        if card is None:
            card = self._create_empty_card_dict(target_week)

        if not self._game_state:
            return card

        if CARD_BUILDER_AVAILABLE:
            # Re-sync state from existing card fights so repeated rebuilds
            # don't accumulate slot counts. Sub-ship A's always-call pattern
            # (Ship #20) calls _build_card_for_week per advance; without this
            # re-sync, get_or_create_card_state preserved stale counts and
            # title fights cascaded past full main_event slots into co-main
            # or prelim. update_card_state_from_fights replaces state with
            # truth derived from card["fights"] (card_builder.py:218-244).
            self._card_builder.update_card_state_from_fights(event_name, target_week, card["fights"])

        # Collect already-booked fighter IDs for this week
        booked_here = set()
        # Check if player has a fight on this card
        for sf in self._scheduled_fights:
            if sf.get("week") == target_week or                (self._game_state and
                self._game_state.week_number + sf.get("weeks_until", 0) == target_week):
                booked_here.add(sf.get("fighter1_id",""))
                booked_here.add(sf.get("fighter2_id",""))
                # Sub-ship A fix: skip if fight already on the card.
                # Phase 3 always-call rebuilds reuse cards via Site 4;
                # without this dedup, every rebuild re-appends the player fight.
                # Tech debt: scheduled-fight injection arguably belongs in
                # _top_up_pipeline Phase 2 alongside AI queue hand-off — see
                # tech_debt_player_fight_injection_location_2026-05-04.md
                _existing_ids = {f.get("fight_id") for f in card["fights"]
                                 if f.get("fight_id")}
                if sf.get("fight_id") in _existing_ids:
                    continue
                # Insert player fight into card
                score = self._matchup_score(
                    self._game_state.get_fighter(sf.get("fighter1_id","")),
                    self._game_state.get_fighter(sf.get("fighter2_id","")),
                    sf.get("is_title_fight", False),
                ) if self._game_state else 50
                _pf1 = self._game_state.get_fighter(sf.get("fighter1_id",""))
                _pf2 = self._game_state.get_fighter(sf.get("fighter2_id",""))
                slot = self._assign_card_slot(
                    event_name, score, sf.get("is_title_fight", False),
                    combined_rating=100,
                    f1_rank=self._get_fighter_rank(_pf1) if _pf1 else None,
                    f2_rank=self._get_fighter_rank(_pf2) if _pf2 else None,
                    f1=_pf1, f2=_pf2,
                )
                sf["card_slot"]  = slot
                sf["event_name"] = event_name
                card["fights"].append(sf)

        # Fighters already on any other pipeline card are unavailable
        # Each fighter should appear on at most one upcoming card.
        # Sub-ship A: target_week's card may already hold drained queue
        # items, so include those fighters in all_booked too.
        all_booked = set()
        for sf in self._scheduled_fights:
            all_booked.add(sf.get("fighter1_id",""))
            all_booked.add(sf.get("fighter2_id",""))
        for wk, existing_card in self._upcoming_cards.items():
            for f in existing_card.get("fights", []):
                all_booked.add(f.get("fighter1_id",""))
                all_booked.add(f.get("fighter2_id",""))
        # Sub-ship A: include fighters in deferred queue
        for q_fight in self._ai_deferred_bookings:
            all_booked.add(q_fight.get("fighter1_id",""))
            all_booked.add(q_fight.get("fighter2_id",""))

        player_camp_id = self._game_state.player_camp_id
        target_count   = CARD_TARGET_FIGHTS

        # ── Collect ALL candidate matchups across every division ──────────
        # Then sort by matchup score so best fights get top slots.
        # This replaces the old random-shuffle-per-division approach.
        candidates = []   # list of (score, f1, f2, wc, is_title)

        for wc in self._game_state.WEIGHT_CLASSES:
            # Always scan all weight classes — don't break early
            # This ensures every division gets a representative fight

            division = self._game_state.divisions.get(wc)
            if not division:
                continue

            available = [
                f for f in self._game_state.fighters.values()
                if f.weight_class == wc
                and f.is_active
                and (not player_camp_id or f.camp_id != player_camp_id)
                and f.fighter_id not in all_booked
                and f.fighter_id not in booked_here
                and self._is_available(f.fighter_id, target_week)
                # Exclude injured fighters from card building
                and not (INJURY_AVAILABLE and self._injury_system
                         and not self._injury_system.is_cleared_to_fight(f.fighter_id))
            ]
            if len(available) < 2:
                continue

            # ── Title fight: champion vs highest available contender ─────
            champ_id = division.champion_id
            champ = next((f for f in available if f.fighter_id == champ_id), None)
            if champ:
                # Try #1 through #10 in order — expanded from top-5 so
                # champion doesn't sit out when top contenders are busy
                top = None
                for contender_id in division.rankings[:10]:
                    candidate = next((f for f in available
                                      if f.fighter_id == contender_id), None)
                    if candidate and candidate.fighter_id != champ_id:
                        top = candidate
                        break
                if top:
                    score = self._matchup_score(champ, top, is_title=True)
                    # Sub-ship A: rank-aware lead time. Champion is rank 0.
                    _top_rank = self._get_fighter_rank(top)
                    _wks_out = self._weeks_out_for_fight(0, _top_rank)
                    _ttw = self._game_state.week_number + _wks_out
                    candidates.append((score, champ, top, wc, True, _ttw))
                    continue
                else:
                    all_booked.add(champ_id)
                    continue

            # ── Ranked vs ranked: pick best available pair ────────────────
            ranked_ids   = set(division.rankings[:14])
            ranked_avail = sorted(
                [f for f in available if f.fighter_id in ranked_ids],
                key=lambda f: division.rankings.index(f.fighter_id)
                              if f.fighter_id in division.rankings else 99
            )

            if len(ranked_avail) >= 2:
                best_pair = None
                best_pair_score = -1
                for i in range(min(len(ranked_avail) - 1, 6)):
                    for j in range(i + 1, min(len(ranked_avail), i + 4)):
                        f_a = ranked_avail[i]
                        f_b = ranked_avail[j]
                        r_a = division.rankings.index(f_a.fighter_id) + 1 if f_a.fighter_id in division.rankings else 99
                        r_b = division.rankings.index(f_b.fighter_id) + 1 if f_b.fighter_id in division.rankings else 99
                        s = self._matchup_score(f_a, f_b)
                        # Rematch cooldown
                        last_fought = self._weeks_since_fought(f_a, f_b)
                        if last_fought is not None and last_fought < 6:
                            continue
                        if last_fought is not None and last_fought < 12:
                            s -= 50
                        # Fight declining — check if either camp would refuse
                        if self._would_decline_fight(f_a, f_b, r_a, r_b):
                            continue
                        if self._would_decline_fight(f_b, f_a, r_b, r_a):
                            continue
                        # Win streak bonus
                        ws_a = getattr(f_a, 'win_streak', 0) or 0
                        ws_b = getattr(f_b, 'win_streak', 0) or 0
                        s += (ws_a + ws_b) * 2
                        # Style diversity bonus
                        style_a = getattr(f_a, 'fighting_style', '') or ''
                        style_b = getattr(f_b, 'fighting_style', '') or ''
                        if style_a and style_b and style_a != style_b:
                            s += 5
                        if s > best_pair_score:
                            best_pair_score = s
                            best_pair = (f_a, f_b)
                if best_pair:
                    # Sub-ship A: rank-aware lead time
                    _r_a_p2 = self._get_fighter_rank(best_pair[0])
                    _r_b_p2 = self._get_fighter_rank(best_pair[1])
                    _wks_out = self._weeks_out_for_fight(_r_a_p2, _r_b_p2)
                    _ttw = self._game_state.week_number + _wks_out
                    candidates.append((best_pair_score, best_pair[0], best_pair[1], wc, False, _ttw))

            elif len(ranked_avail) == 1 and len(available) >= 2:
                ranked_f = ranked_avail[0]
                r = self._get_fighter_rank(ranked_f)
                if r is not None and r >= 6:
                    unranked_pool = [f for f in available if f.fighter_id not in ranked_ids]
                    if unranked_pool:
                        opp = random.choice(unranked_pool)
                        score = self._matchup_score(ranked_f, opp)
                        # Sub-ship A: rank-aware lead time (one ranked, one unranked)
                        _wks_out = self._weeks_out_for_fight(r, None)
                        _ttw = self._game_state.week_number + _wks_out
                        candidates.append((score, ranked_f, opp, wc, False, _ttw))

            elif not ranked_avail and len(available) >= 2:
                # Unranked matchup — pair by record similarity, not pure random
                # Sort by wins desc so fighters with similar records get paired
                unranked_sorted = sorted(available,
                    key=lambda f: f.wins - f.losses, reverse=True)
                # Pair top vs second, third vs fourth (record-matched)
                for k in range(0, min(len(unranked_sorted)-1, 4), 2):
                    f1_u = unranked_sorted[k]
                    f2_u = unranked_sorted[k+1]
                    last_u = self._weeks_since_fought(f1_u, f2_u)
                    if last_u is not None and last_u < 6:
                        continue
                    score_u = self._matchup_score(f1_u, f2_u)
                    # Win streak bonus for unranked too
                    score_u += ((getattr(f1_u,'win_streak',0) or 0) +
                                (getattr(f2_u,'win_streak',0) or 0)) * 1.5
                    # Sub-ship A: rank-aware lead time (both unranked)
                    _wks_out = self._weeks_out_for_fight(None, None)
                    _ttw = self._game_state.week_number + _wks_out
                    candidates.append((score_u, f1_u, f2_u, wc, False, _ttw))
                    break  # One unranked fight per division

        # ── Sort candidates by score descending ───────────────────────────
        candidates.sort(key=lambda x: x[0], reverse=True)

        # ── Ship CB2: split title vs non-title; title fights claim the
        # MAIN_EVENT/CO_MAIN slots BEFORE any regular fight gets a chance.
        # Excess title fights (3rd+ or duplicate-division) defer naturally
        # to the next pipeline rebuild — no explicit cooldown applied.
        _title_candidates   = [c for c in candidates if c[4]]
        _regular_candidates = [c for c in candidates if not c[4]]

        # Title cap — max 2 per card, must be different divisions
        _title_kept: List[Any] = []
        _title_divs: Set[str] = set()
        for c in _title_candidates:
            _wc = c[3]
            if len(_title_kept) < 2 and _wc not in _title_divs:
                _title_kept.append(c)
                _title_divs.add(_wc)
            # else: excess title fight deferred to next pipeline build

        # Merge: title fights first, then non-title in score order
        candidates = _title_kept + _regular_candidates

        # ── Fill card slots top-to-bottom ─────────────────────────────────
        # Sub-ship A: route by computed_target_week. Candidates whose lead
        # time matches this card → place here. Others → defer to queue
        # for hand-off when target_week enters the pipeline window.
        used_in_candidates = set()
        co_main_used = 0   # Track co-main slot usage for floor management
        for score, f1, f2, wc, is_title, computed_target_week in candidates:
            # Skip if either fighter was already matched in a higher-score fight
            if f1.fighter_id in used_in_candidates or f2.fighter_id in used_in_candidates:
                continue

            r1 = self._get_fighter_rank(f1)
            r2 = self._get_fighter_rank(f2)
            ranks = [r for r in [r1, r2] if r is not None]
            top_rank = min(ranks) if ranks else None

            # Adjust floor based on how many premium slots are already committed
            # First #1 contender fight can claim co-main, subsequent ones get main-card
            override_f1 = r1
            override_f2 = r2
            if top_rank is not None and top_rank <= 1 and co_main_used >= 1:
                # Co-main already claimed — floor this to main_card instead
                override_f1 = 3 if r1 == 1 else r1
                override_f2 = 3 if r2 == 1 else r2

            # Ship CB2: per-fight reality check — high-ranked fighters
            # never prelim. Belt-and-suspenders with _assign_card_slot's
            # wrapper floor logic; the score bump here is required because
            # _find_available_slot returns PRELIM when start_idx > floor_idx.
            min_slot: Optional[CardSlot] = None
            if top_rank is not None:
                if top_rank <= 2:
                    min_slot = CardSlot.CO_MAIN
                    score = max(score, SCORE_THRESHOLDS[CardSlot.CO_MAIN] + 1)
                elif top_rank <= 5:
                    min_slot = CardSlot.MAIN_CARD
                    score = max(score, SCORE_THRESHOLDS[CardSlot.MAIN_CARD] + 1)

            slot = self._assign_card_slot(
                event_name, score, is_title,
                f1.overall_rating + f2.overall_rating,
                f1_rank=override_f1, f2_rank=override_f2,
                f1=f1, f2=f2,
                min_slot=min_slot,
            )

            if computed_target_week == target_week:
                # This card matches lead time — place here
                if len(card["fights"]) >= target_count:
                    print(f"  ⏭️  [LEAD-TIME DISPLACED] {f1.name} vs {f2.name} "
                          f"dropped (DFC {target_week} full)")
                    card["locked"] = True
                    continue  # card full, drop (next top-up regenerates)
                if slot in ("co_main", "main_event"):
                    co_main_used += 1
                fight_dict = self._make_scheduled_fight(
                    f1, f2, wc, event_name, target_week, slot, is_title=is_title)
                card["fights"].append(fight_dict)
                if len(card["fights"]) >= target_count:
                    card["locked"] = True
            else:
                # Different lead-time target — defer to queue for hand-off
                _q_event_name = self._dfc_label(computed_target_week)
                fight_dict = self._make_scheduled_fight(
                    f1, f2, wc, _q_event_name, computed_target_week, slot, is_title=is_title)
                self._ai_deferred_bookings.append(fight_dict)
                print(f"  📅 [LEAD-TIME QUEUE] {f1.name} vs {f2.name} → "
                      f"{_q_event_name} ({computed_target_week - target_week:+d}w)")

            used_in_candidates.add(f1.fighter_id)
            used_in_candidates.add(f2.fighter_id)
            all_booked.add(f1.fighter_id)
            all_booked.add(f2.fighter_id)

        # ── Terminal summary ── Ship CB1: structured by slot
        self._print_event_card(card, event_name, target_week)

        return card

    def _make_scheduled_fight(self, f1, f2, wc: str, event_name: str,
                               target_week: int, slot: str,
                               is_title: bool = False) -> Dict[str, Any]:
        """Build a scheduled fight dict for the card pipeline."""
        weeks_out = target_week - (self._game_state.week_number if self._game_state else 0)
        return {
            "fight_id":       f"fight_{target_week}_{f1.fighter_id}_{f2.fighter_id}",
            "fighter1_id":    f1.fighter_id,
            "fighter1_name":  f1.name,
            "fighter2_id":    f2.fighter_id,
            "fighter2_name":  f2.name,
            "weight_class":   wc,
            "event_name":     event_name,
            "week":           target_week,
            "weeks_until":    max(0, weeks_out),
            "card_slot":      slot,
            "is_title_fight": is_title,
            "is_player_fight": False,
            "is_ai_fight":    True,
            "purse":          0,
        }

    def initialize_card_pipeline(self) -> None:
        """
        Called once on new_game.
        Builds 6 weeks of DFC cards with intentional structure:
        - Title fights are pre-assigned across cards (no front-loading)
        - Each division's champion fights exactly once in the pipeline
        - Ranked matchups fill remaining slots from all available fighters
        """
        if not self._game_state:
            return
        current = self._game_state.week_number

        all_wcs = list(self._game_state.WEIGHT_CLASSES)  # 9 divisions
        num_cards = 3   # Pre-build 3 intentional cards; top_up fills the rest organically
        weeks = list(range(current + 1, current + num_cards + 1))

        # Pre-assign title fights: max 2 per card, spread across all 9 divisions
        # With 9 divisions and 3 cards: first 6 get 2 per card, last 3 sit out
        # They get picked up naturally in subsequent pipeline builds
        import random
        random.shuffle(all_wcs)
        title_assignments: Dict[int, List[str]] = {w: [] for w in weeks}
        for i, wc in enumerate(all_wcs):
            card_week = weeks[i % num_cards]
            if len(title_assignments[card_week]) < 2:  # Max 2 title fights per card
                title_assignments[card_week].append(wc)

        # Track globally booked fighters across the whole pipeline
        pipeline_booked: set = set()
        for sf in self._scheduled_fights:
            pipeline_booked.add(sf.get("fighter1_id", ""))
            pipeline_booked.add(sf.get("fighter2_id", ""))

        for w in weeks:
            card = self._build_card_for_week_planned(
                target_week=w,
                title_divisions=title_assignments[w],
                pipeline_booked=pipeline_booked,
            )
            self._upcoming_cards[w] = card
            # Mark all fighters on this card as booked for the rest of the pipeline
            for f in card.get("fights", []):
                pipeline_booked.add(f.get("fighter1_id", ""))
                pipeline_booked.add(f.get("fighter2_id", ""))

        print(f"✅ Card pipeline initialized: {PROMOTION_NAME} {current+1} – {PROMOTION_NAME} {current+num_cards}")

    def _build_card_for_week_planned(
        self,
        target_week: int,
        title_divisions: List[str],
        pipeline_booked: set,
    ) -> Dict[str, Any]:
        """
        Build one card with pre-assigned title fight divisions.
        title_divisions: which weight classes have their title fight on this card.
        pipeline_booked: fighters already on other pipeline cards (shared, mutated here).
        """
        import random
        event_name = self._dfc_label(target_week)
        card: Dict[str, Any] = {
            "event_id":    f"event_{target_week}",
            "event_name":  event_name,
            "week":        target_week,
            "fights":      [],
            "is_ai_event": True,
        }
        if not self._game_state:
            return card
        if CARD_BUILDER_AVAILABLE:
            self._card_builder.get_or_create_card_state(event_name, target_week)

        locally_booked: set = set()
        candidates: List[tuple] = []

        all_wcs = list(self._game_state.WEIGHT_CLASSES)

        # ── Phase 1: Title fights for pre-assigned divisions ──────────────
        for wc in title_divisions:
            division = self._game_state.divisions.get(wc)
            if not division:
                continue
            champ_id = division.champion_id
            if not champ_id or champ_id in pipeline_booked:
                continue
            champ = self._game_state.get_fighter(champ_id)
            if not champ or not champ.is_active:
                continue
            # Find highest-available ranked contender
            # Must not be pipeline_booked AND must not be on cooldown
            top = None
            for cid in division.rankings[:10]:
                if cid in pipeline_booked or cid == champ_id:
                    continue
                if not self._is_available(cid, target_week):
                    continue  # On cooldown — skip
                f = self._game_state.get_fighter(cid)
                if f and f.is_active:
                    top = f
                    break
            if top:
                score = self._matchup_score(champ, top, is_title=True)
                candidates.append((score, champ, top, wc, True))
            else:
                # No ranked contender available — protect champion from
                # being paired by later phases (never fight unranked)
                pipeline_booked.add(champ_id)

        # ── Phase 2: Ranked matchups from ALL divisions ───────────────────
        # IMPORTANT: Only use ranks 6-15 here.
        # Ranks 1-5 are reserved for title fights — consuming them here
        # leaves champions without contenders on later pipeline cards.
        # Champion is explicitly excluded (only appears via Phase 1).
        for wc in all_wcs:
            division = self._game_state.divisions.get(wc)
            if not division:
                continue
            champ_id_here = division.champion_id or ""
            # rankings[0] = #1, rankings[5] = #6 — use indices 5-13 (ranks 6-14)
            ranked_ids = list(division.rankings[5:14])
            available_ranked = [
                self._game_state.get_fighter(fid)
                for fid in ranked_ids
                if fid and fid not in pipeline_booked and fid != champ_id_here
            ]
            available_ranked = [f for f in available_ranked
                                 if f and f.is_active]
            if len(available_ranked) >= 2:
                # Pick best pair by score (adjacent ranks preferred)
                best_pair = None
                best_score = -1
                for i in range(min(len(available_ranked)-1, 6)):
                    for j in range(i+1, min(len(available_ranked), i+4)):
                        s = self._matchup_score(available_ranked[i],
                                                available_ranked[j])
                        if s > best_score:
                            best_score = s
                            best_pair = (available_ranked[i], available_ranked[j])
                if best_pair:
                    candidates.append((best_score, best_pair[0],
                                       best_pair[1], wc, False))

        # ── Phase 2.5: Top contenders (ranks 1-5) from non-title divisions ──
        # HARD LIMIT: max 2 per card. With 9 divisions and 3 pipeline cards,
        # each card gets at most 2 top-contender matchups from non-title divisions.
        # This prevents card 1 from consuming every #1 and #2 in the game,
        # leaving nothing ranked for cards 2-7.
        title_divs_set = set(title_divisions)
        top_contender_count = 0
        MAX_TOP_CONTENDER_PER_CARD = 2

        for wc in all_wcs:
            if top_contender_count >= MAX_TOP_CONTENDER_PER_CARD:
                break
            if wc in title_divs_set:
                continue  # Title divisions handled in Phase 1
            division = self._game_state.divisions.get(wc)
            if not division:
                continue
            champ_id_here = division.champion_id or ""
            top_ids = list(division.rankings[:5])
            available_top = [
                self._game_state.get_fighter(fid)
                for fid in top_ids
                if fid and fid not in pipeline_booked and fid != champ_id_here
            ]
            available_top = [f for f in available_top if f and f.is_active]
            if len(available_top) >= 2:
                best_pair = None
                best_score = -1
                for i in range(min(len(available_top)-1, 4)):
                    for j in range(i+1, min(len(available_top), i+3)):
                        s = self._matchup_score(available_top[i], available_top[j])
                        if s > best_score:
                            best_score = s
                            best_pair = (available_top[i], available_top[j])
                if best_pair:
                    candidates.append((max(best_score, 60.0), best_pair[0],
                                       best_pair[1], wc, False))
                    top_contender_count += 1

        # ── Phase 3: Sort and fill ─────────────────────────────────────────
        candidates.sort(key=lambda x: x[0], reverse=True)

        # Cap title fights at 2
        title_count = 0
        capped = []
        for c in candidates:
            if c[4]:
                if title_count < 2:
                    capped.append(c); title_count += 1
            else:
                capped.append(c)
        candidates = capped

        co_main_used = 0
        target_count = 9
        for score, f1, f2, wc, is_title in candidates:
            if len(card["fights"]) >= target_count:
                break
            if (f1.fighter_id in pipeline_booked or
                    f2.fighter_id in pipeline_booked or
                    f1.fighter_id in locally_booked or
                    f2.fighter_id in locally_booked):
                continue
            r1 = self._get_fighter_rank(f1)
            r2 = self._get_fighter_rank(f2)
            ranks = [r for r in [r1, r2] if r is not None]
            top_rank = min(ranks) if ranks else None
            eff_r1, eff_r2 = r1, r2
            if top_rank is not None and top_rank <= 1 and co_main_used >= 1:
                eff_r1 = 3 if r1 == 1 else r1
                eff_r2 = 3 if r2 == 1 else r2
            slot = self._assign_card_slot(
                event_name, score, is_title,
                f1.overall_rating + f2.overall_rating,
                f1_rank=eff_r1, f2_rank=eff_r2,
                f1=f1, f2=f2,
            )
            if slot in ("co_main", "main_event"):
                co_main_used += 1
            fight_dict = self._make_scheduled_fight(
                f1, f2, wc, event_name, target_week, slot, is_title=is_title)
            card["fights"].append(fight_dict)
            locally_booked.add(f1.fighter_id)
            locally_booked.add(f2.fighter_id)

        # Print card summary ── Ship CB1: structured by slot
        self._print_event_card(card, event_name, target_week)
        return card

    def _top_up_pipeline(self) -> None:
        """
        Maintain rolling 8-week pipeline. Sub-ship A — three phases:
          1. Cancellation re-eval — drop deferred-queue items with broken pairs
             (one fighter retired / now-injured / contract-expired). Next
             top-up regenerates fresh candidates via normal _build_card flow.
          2. Hand-off — drain queue items whose target_week has entered
             window (current+1 to current+8) into _upcoming_cards.
          3. Build/extend — call _build_card_for_week for each pipeline week
             (creates fresh cards for empty weeks, tops up drain-only cards).
        """
        if not self._game_state:
            return
        current = self._game_state.week_number

        # Phase 1: cancellation re-eval — drop queue items with broken pairs
        _kept_q = []
        for q_fight in self._ai_deferred_bookings:
            f1id = q_fight.get("fighter1_id", "")
            f2id = q_fight.get("fighter2_id", "")
            f1 = self._game_state.get_fighter(f1id)
            f2 = self._game_state.get_fighter(f2id)
            _valid = (
                f1 and f2 and f1.is_active and f2.is_active
                and (not (INJURY_AVAILABLE and self._injury_system)
                     or (self._injury_system.is_cleared_to_fight(f1id)
                         and self._injury_system.is_cleared_to_fight(f2id)))
            )
            if _valid:
                _kept_q.append(q_fight)
            else:
                print(f"  🚫 [LEAD-TIME CANCEL] {q_fight.get('fighter1_name','?')} vs "
                      f"{q_fight.get('fighter2_name','?')} dropped (broken pair)")
        self._ai_deferred_bookings = _kept_q

        # Phase 1b: defensive unlock sweep — if any card's fight count fell
        # below capacity (e.g. external code removed a fight), clear the
        # lock so Phase 3 can top it up. Self-healing — lock converges to
        # truth based on actual fight count.
        for _wk_unlock, _card_unlock in self._upcoming_cards.items():
            if (_card_unlock.get("locked", False)
                    and len(_card_unlock.get("fights", [])) < CARD_TARGET_FIGHTS):
                _card_unlock["locked"] = False

        # Phase 2: hand-off — drain queue items whose target_week is in window
        _to_drain = [q for q in self._ai_deferred_bookings
                     if current + 1 <= q.get("week", 0)
                        <= current + PIPELINE_WINDOW_WEEKS]
        _drained_ids = set()
        for q_fight in _to_drain:
            target = q_fight.get("week", 0)
            if target not in self._upcoming_cards:
                self._upcoming_cards[target] = self._create_empty_card_dict(target)
            # Sub-ship A regression fix: respect card capacity on hand-off.
            # Without this gate, queue items accumulated across multiple
            # advance-weeks all drain onto the same card when target_week
            # enters window (DFC 45 reached 29 fights pre-fix). Dropped
            # queue items become eligible in next advance's candidate
            # generation since they're no longer in any sink.
            if self._upcoming_cards[target].get("locked", False):
                print(f"  ⚠️  [LEAD-TIME OVERFLOW] "
                      f"{q_fight.get('fighter1_name','?')} vs "
                      f"{q_fight.get('fighter2_name','?')} dropped "
                      f"({self._dfc_label(target)} locked)")
                _drained_ids.add(q_fight.get("fight_id", ""))
                continue
            if len(self._upcoming_cards[target]["fights"]) >= CARD_TARGET_FIGHTS:
                print(f"  ⚠️  [LEAD-TIME OVERFLOW] {q_fight.get('fighter1_name','?')} vs "
                      f"{q_fight.get('fighter2_name','?')} dropped ({self._dfc_label(target)} at capacity)")
                _drained_ids.add(q_fight.get("fight_id", ""))
                continue
            # Ship LT1: re-derive slot at drain time so rank floors +
            # per-slot caps are respected at the target card's actual
            # state, not the enqueue-time state weeks earlier.
            _tgt_event = (self._upcoming_cards[target].get("event_name")
                          or self._dfc_label(target))
            _cb = getattr(self, '_card_builder', None)
            if _cb:
                _cb.update_card_state_from_fights(
                    _tgt_event, target,
                    self._upcoming_cards[target]["fights"])
            _qf1 = (self._game_state.get_fighter(q_fight.get("fighter1_id", ""))
                    if self._game_state else None)
            _qf2 = (self._game_state.get_fighter(q_fight.get("fighter2_id", ""))
                    if self._game_state else None)
            _qscore = self._matchup_score(
                _qf1, _qf2, q_fight.get("is_title_fight", False))
            _qslot = self._assign_card_slot(
                _tgt_event,
                _qscore,
                q_fight.get("is_title_fight", False),
                combined_rating=(getattr(_qf1, 'overall_rating', 50)
                                  + getattr(_qf2, 'overall_rating', 50)
                                  if _qf1 and _qf2 else 100),
                f1_rank=self._get_fighter_rank(_qf1) if _qf1 else None,
                f2_rank=self._get_fighter_rank(_qf2) if _qf2 else None,
                f1=_qf1, f2=_qf2,
            )
            q_fight["card_slot"]  = _qslot
            q_fight["event_name"] = _tgt_event
            self._upcoming_cards[target]["fights"].append(q_fight)
            _drained_ids.add(q_fight.get("fight_id", ""))
            print(f"  📅 [LEAD-TIME HANDOFF] {q_fight.get('fighter1_name','?')} vs "
                  f"{q_fight.get('fighter2_name','?')} → {self._dfc_label(target)}")
        self._ai_deferred_bookings = [q for q in self._ai_deferred_bookings
                                       if q.get("fight_id", "") not in _drained_ids]

        # Phase 3: build/extend cards for pipeline window
        # (always-call so drain-only cards get topped up; idempotent because
        #  Site 4's reuse-existing logic preserves existing fights and
        #  target_count gate prevents over-fill)
        # Locked cards skip rebuild — saves the per-WC candidate scan when
        # the card is already at capacity. Lock clears in Phase 1 if any
        # fight drops the card below capacity.
        for w in range(current + 1,
                       current + PIPELINE_WINDOW_WEEKS + 1):
            existing = self._upcoming_cards.get(w, {})
            if existing.get("locked", False):
                continue  # Card full and locked — skip rebuild
            self._upcoming_cards[w] = self._build_card_for_week(w)

    def get_upcoming_events(self, limit: int = 8, max_weeks_out: int = 10) -> List[Dict[str, Any]]:
        """Return upcoming DFC cards for the UI — capped at limit events and max_weeks_out."""
        if not self._game_state:
            return []
        current = self._game_state.week_number
        out = []
        for wk in sorted(self._upcoming_cards.keys()):
            if wk <= current:
                continue
            weeks_out = wk - current
            if weeks_out > max_weeks_out:
                continue  # Don't show cards more than max_weeks_out away
            card = self._upcoming_cards[wk]
            weeks_out = wk - current
            out.append({
                "event_name":  card["event_name"],
                "week":        wk,
                "weeks_out":   weeks_out,
                "fight_count": len(card["fights"]),
                "fights":      card["fights"],
                "has_title":   any(f.get("is_title_fight") for f in card["fights"]),
                "has_player":  any(
                    f.get("fighter1_id") in {pf.fighter_id for pf in self.get_player_fighters()} or
                    f.get("fighter2_id") in {pf.fighter_id for pf in self.get_player_fighters()}
                    for f in card["fights"]
                ),
            })
            if len(out) >= limit:
                break
        return out

    def get_card_for_week(self, week: int) -> Optional[Dict[str, Any]]:
        """Get the pre-built card for a specific week."""
        return self._upcoming_cards.get(week)

    def assign_player_fight_to_card(self, fight: Dict[str, Any]) -> str:
        """
        When player books a fight, assign it to the right DFC card.
        Finds earliest card with an open slot that fits cooldown.
        Returns the event_name it was placed on.
        """
        if not self._game_state:
            return fight.get("event_name", "Cage Dynasty ?")

        target_week = fight.get("week",
                       self._game_state.week_number + fight.get("weeks_until", 4))

        # Find or create card for target_week
        if target_week not in self._upcoming_cards:
            self._upcoming_cards[target_week] = self._build_card_for_week(target_week)

        card = self._upcoming_cards[target_week]

        # Score and assign slot
        f1 = self._game_state.get_fighter(fight.get("fighter1_id",""))
        f2 = self._game_state.get_fighter(fight.get("fighter2_id",""))
        if f1 and f2:
            score = self._matchup_score(f1, f2, fight.get("is_title_fight", False))
            slot  = self._assign_card_slot(
                card["event_name"], score,
                fight.get("is_title_fight", False),
                (f1.overall_rating + f2.overall_rating),
                f1_rank=self._get_fighter_rank(f1),
                f2_rank=self._get_fighter_rank(f2),
                f1=f1, f2=f2,
            )
        else:
            score = 50
            slot  = "prelim"

        fight["card_slot"]   = slot
        fight["event_name"]  = card["event_name"]
        fight["week"]        = target_week
        fight["weeks_until"] = target_week - self._game_state.week_number
        fight["matchup_score"] = round(score, 1)

        # Remove any existing AI fight on that card involving these fighters
        card["fights"] = [
            f for f in card["fights"]
            if f.get("fighter1_id") not in {fight["fighter1_id"], fight["fighter2_id"]}
            and f.get("fighter2_id") not in {fight["fighter1_id"], fight["fighter2_id"]}
        ]
        card["fights"].append(fight)

        return card["event_name"]

    # =========================================================================
    # REAL FIGHT ENGINE INTEGRATION
    # =========================================================================

    # Style string → FightingStyle enum mapping
    _STYLE_MAP = {
        # Current 11 display names
        "Striker":          "STRIKER",
        "Counter Striker":  "COUNTER_STRIKER",
        "Pressure Fighter": "PRESSURE_FIGHTER",
        "Point Fighter":    "POINT_FIGHTER",
        "Muay Thai":        "MUAY_THAI",
        "Wrestler":         "WRESTLER",
        "Ground & Pound":   "GROUND_AND_POUND",
        "BJJ Specialist":   "BJJ_SPECIALIST",
        "Clinch Fighter":   "CLINCH_FIGHTER",
        "Sprawl & Brawl":   "SPRAWL_AND_BRAWL",
        "Balanced":         "BALANCED",
        # Generation style names that need mapping
        "Orthodox Boxer":   "STRIKER",
        "Kickboxer":        "STRIKER",
        "Submission Artist":"BJJ_SPECIALIST",
        "Sambo":            "WRESTLER",
        "Karate":           "POINT_FIGHTER",
        "Brawler":          "PRESSURE_FIGHTER",
        # Legacy names from _STYLE_XLAT
        "MMA Hybrid":       "BALANCED",
        "Boxing":           "STRIKER",
        "Judo":             "WRESTLER",
        "Grappling":        "WRESTLER",
        "Submissions":      "BJJ_SPECIALIST",
        "Counter-Striker":  "COUNTER_STRIKER",
    }

    def _make_fighter_attrs(self, fighter, name: str, fighter_id: str):
        """Convert a FighterRecord/WebFighter to FighterAttributes for the engine."""
        fdata = {}
        if self._game_state and fighter_id in self._game_state._fighter_data:
            fdata = self._game_state._fighter_data[fighter_id]

        ovr = getattr(fighter, 'overall_rating', 65)

        def _a(attr, offset=0):
            return max(1, min(99, int(fdata.get(attr, getattr(fighter, attr, ovr + offset)))))

        style_str = fdata.get("style", getattr(fighter, 'fighting_style', "Balanced"))
        style_key = self._STYLE_MAP.get(style_str, "BALANCED")

        from core.types import FightingStyle
        style = FightingStyle[style_key]

        return _FighterAttributes(
            fighter_id  = fighter_id,
            name        = name,
            strength    = _a("strength"),
            speed       = _a("speed",     +3),
            cardio      = _a("cardio",    +2),
            chin        = _a("chin",      -2),
            recovery    = _a("recovery"),
            boxing      = _a("boxing"),
            kicks       = _a("kicks",     -4),
            clinch_striking     = _a("clinch_striking", -3),
            striking_defense    = _a("striking_defense"),
            takedowns           = _a("takedowns",       -4),
            takedown_defense    = _a("takedown_defense"),
            top_control         = _a("top_control",     -5),
            submissions         = _a("submissions",     -4),
            guard               = _a("guard",           -5),
            heart               = _a("heart",           +2),
            fight_iq            = _a("fight_iq"),
            composure           = _a("composure"),
            fighting_style      = style,
        )

    # ── Ship K1: corner advice helpers ────────────────────────────
    def _apply_corner_prefight_buff(self, fa) -> Optional[Dict[str, Any]]:
        """
        Path α mechanical bonus. Buff the player fighter's engine
        attributes by a small amount before sim runs. `fa` is the
        _FighterAttributes dataclass instance produced by
        _make_fighter_attrs — throwaway per-fight, mutation-safe.
        Returns the applied buff payload (for logging) or None.
        """
        if not CORNER_ADVICE_ENABLED:
            return None
        if not self._coach_contract:
            return None
        try:
            from corner_advice import compute_prefight_buff
        except ImportError:
            return None
        buff = compute_prefight_buff(self._coach)
        if not buff:
            return None
        for attr in buff["attrs"]:
            cur = getattr(fa, attr, None)
            if cur is None:
                continue
            setattr(fa, attr, min(99, int(cur + buff["amount"])))
        return buff

    def _apply_sponsor_boost(self, fa, fighter) -> None:
        """Apply active sponsor attribute boosts to FighterAttributes
        before engine call. Mirrors the corner-advice buff pattern.
        Fires for both player and AI fighters (sponsors are universal)."""
        if not self._game_state:
            return
        fid = getattr(fighter, 'fighter_id', None)
        if not fid:
            return
        sponsors = self._game_state._fighter_data.get(
            fid, {}).get("sponsors", []) or []
        for s in sponsors:
            brand = _SPONSOR_BY_ID.get(s.get("sponsor_id", ""))
            if not brand:
                continue
            for attr, amount in brand["attr_boost"].items():
                cur = getattr(fa, attr, None)
                if cur is not None:
                    setattr(fa, attr, min(99, int(cur + amount)))

    def _inject_corner_advice(
        self,
        commentary_lines: List[str],
        eng_result,
        player_fighter,
        opponent_fighter,
        player_is_f1: bool,
    ) -> List[str]:
        """
        Walk commentary_lines, generate between-round corner advice for
        the player fighter, and inject `=== CORNER ===` marker blocks
        before each subsequent round header. Silent (returns input
        unchanged) when coach is vacant, advice disabled, or no
        round-by-round stats are available.
        """
        if not CORNER_ADVICE_ENABLED:
            return commentary_lines
        if not self._coach_contract:
            return commentary_lines
        try:
            from corner_advice import generate_corner_advice
        except ImportError:
            return commentary_lines

        p_stats_list = (
            eng_result.fighter1_stats if player_is_f1 else eng_result.fighter2_stats
        )
        o_stats_list = (
            eng_result.fighter2_stats if player_is_f1 else eng_result.fighter1_stats
        )
        if not p_stats_list:
            return commentary_lines

        total_rounds = getattr(eng_result, "total_rounds", len(p_stats_list)) or len(p_stats_list)
        p_health = (
            getattr(eng_result, "fighter1_final_health", 100.0)
            if player_is_f1
            else getattr(eng_result, "fighter2_final_health", 100.0)
        )
        o_health = (
            getattr(eng_result, "fighter2_final_health", 100.0)
            if player_is_f1
            else getattr(eng_result, "fighter1_final_health", 100.0)
        )

        # Stamina approximated per-round from cumulative volume up to
        # that round — computed inside the loop below, not here.
        # (Was a bug: single value computed once → same tags every round.)

        # Per-round score deltas accumulate into a cards-style gap.
        from corner_advice import _round_score
        cumulative_gap = 0.0

        # Build advice per between-round boundary (after R1, after R2, ...).
        # Skip after the last completed round (no "next round").
        n_rounds_completed = len(p_stats_list)
        last_for_advice = min(n_rounds_completed, total_rounds) - 1

        # Per-round health proxy: linear interp on final health.
        def _round_health(final_h: float, r_idx: int) -> float:
            # r_idx is 0-based completed-round index; assume monotonic decline
            n = max(1, n_rounds_completed)
            return 100.0 - (100.0 - final_h) * ((r_idx + 1) / n)

        advice_by_round: Dict[int, Dict[str, Any]] = {}
        for r_idx in range(last_for_advice):
            p_rs = p_stats_list[r_idx] if isinstance(p_stats_list[r_idx], dict) else {}
            o_rs = o_stats_list[r_idx] if (r_idx < len(o_stats_list) and isinstance(o_stats_list[r_idx], dict)) else {}
            cumulative_gap += _round_score(p_rs) - _round_score(o_rs)
            # Per-round stamina: cumulative volume up to this round
            _cum_strikes = sum(s.get("sig_strikes_att", 0) for s in p_stats_list[:r_idx+1])
            _cum_td      = sum(s.get("td_att", 0) for s in p_stats_list[:r_idx+1])
            approx_player_stamina = max(0, 100 - (_cum_strikes // 2) - (_cum_td * 3))
            adv = generate_corner_advice(
                coach_dict             = self._coach,
                fighter_name           = getattr(player_fighter, "name", "Fighter"),
                opponent_name          = getattr(opponent_fighter, "name", "Opponent"),
                player_health          = _round_health(p_health, r_idx),
                player_stamina         = approx_player_stamina,
                opponent_health        = _round_health(o_health, r_idx),
                round_stats_player     = p_rs,
                round_stats_opponent   = o_rs,
                cumulative_score_gap   = cumulative_gap,
                round_num              = r_idx + 1,   # 1-based round just completed
                total_rounds           = total_rounds,
            )
            if adv:
                advice_by_round[r_idx + 1] = adv

        if not advice_by_round:
            return commentary_lines

        # Walk commentary and inject corner blocks AFTER each round-end
        # bracketed summary. The real engine emits `[Round N: <summary>]`
        # reliably at the end of every round; round-start lines are
        # inconsistent (sometimes "Round N", sometimes mid-round prose,
        # sometimes missing). End-of-round summaries are the reliable
        # boundary, and matching the cinematic intent — the coach
        # speaks after the round closes.
        import re
        ROUND_END_PATTERN = re.compile(r"^\[Round (\d+):", re.IGNORECASE)
        new_lines: List[str] = []
        for line in commentary_lines:
            new_lines.append(line)
            m = ROUND_END_PATTERN.match(line)
            if m:
                ended_round = int(m.group(1))
                if ended_round in advice_by_round:
                    adv = advice_by_round[ended_round]
                    new_lines.append("=== CORNER ===")
                    for advice_line in adv["lines"]:
                        new_lines.append(f"{adv['coach_name']}: {advice_line}")
                    # Closing marker so parser doesn't sweep next-round
                    # intro prose ("Round 2 begins!" etc.) into the
                    # corner block.
                    new_lines.append("=== /CORNER ===")
        return new_lines

    # Round-flavored variants for repeated corner advice. Keyed by the
    # round the advice is heard BEFORE (i.e. round 2 variants are the
    # ones swapped in for duplicates appearing after round 1 ends).
    _CORNER_VARIANTS_BY_ROUND = {
        2: [
            "Good round. Keep the pressure — don't let him breathe.",
            "You're ahead. Don't change what's working.",
            "He's adjusting. Stay one step ahead.",
            "Mid-fight now. This is where champions separate themselves.",
        ],
        3: [
            "Last round. Leave everything in the cage.",
            "Three minutes. Everything you've built — now.",
            "He's tired. You're not. Finish this.",
            "Championship rounds. This is what we trained for.",
        ],
        4: [
            "Halfway through. Control the pace.",
            "Your cardio is the weapon now. Keep working.",
        ],
        5: [
            "Final round. Make it count.",
            "You want this more than he does. Prove it.",
        ],
    }

    def _dedupe_corner_advice_by_round(self, lines: List[str]) -> List[str]:
        """Replace duplicate corner advice with round-specific variants so each
        between-round corner sounds distinct. Parses the '=== CORNER ===' ...
        '=== /CORNER ===' blocks emitted by _inject_corner_advice. Tracks
        advice text seen in earlier rounds — if the same advice repeats in
        round 2+, it's swapped for a round-flavored alternate keyed off the
        most recent '[Round N: ...]' marker."""
        import re as _re_dedupe
        import random as _rng_dedupe

        round_end_pattern = _re_dedupe.compile(r"^\[Round (\d+):", _re_dedupe.IGNORECASE)
        out: List[str] = []
        seen_advice: set = set()
        last_ended_round = 0
        in_corner = False

        for line in lines:
            stripped = line.strip()
            m = round_end_pattern.match(stripped)
            if m:
                last_ended_round = int(m.group(1))

            if stripped == "=== CORNER ===":
                in_corner = True
                out.append(line)
                continue
            if stripped == "=== /CORNER ===":
                in_corner = False
                out.append(line)
                continue

            if in_corner and ":" in line:
                coach_part, _, advice_text = line.partition(":")
                advice_norm = advice_text.strip()
                coach_name = coach_part.strip()
                # Advice given after round N ends is heard before round N+1 starts
                target_round = last_ended_round + 1

                if advice_norm and advice_norm in seen_advice and \
                        target_round in self._CORNER_VARIANTS_BY_ROUND:
                    variant = _rng_dedupe.choice(
                        self._CORNER_VARIANTS_BY_ROUND[target_round]
                    )
                    out.append(f"{coach_name}: {variant}")
                    continue

                if advice_norm:
                    seen_advice.add(advice_norm)

            out.append(line)

        return out

    def _enrich_round_summaries(self, lines: List[str]) -> List[str]:
        """Replace generic round summary lines with more varied descriptions.
        The engine always outputs 'A grappling-heavy round' even when
        striking dominated. We post-process to add variety."""
        import re as _re_rnd
        import random as _rng_rnd

        _SUMMARY_PATTERN = _re_rnd.compile(
            r'^\[Round (\d+): A grappling-heavy round (.*?)\]$',
            _re_rnd.IGNORECASE
        )
        _STRIKING_PATTERN = _re_rnd.compile(
            r'^\[Round (\d+): A striking-heavy round (.*?)\]$',
            _re_rnd.IGNORECASE
        )

        # Varied templates keyed by outcome phrase
        _GRAPPLING_VARIANTS = [
            "A grappling clinic",
            "A wrestling masterclass",
            "Ground control dominated this round",
            "The fight lived on the mat",
            "A grappler's round",
        ]
        _STRIKING_VARIANTS = [
            "A striking showcase",
            "The fighters traded on the feet",
            "A technical striking round",
            "Stand-up warfare",
            "Punches and kicks flew freely",
        ]
        _CLOSE_VARIANTS = [
            "A competitive round",
            "A closely contested round",
            "Hard to score this one",
            "Both fighters had their moments",
            "A back-and-forth round",
        ]

        out = []
        for line in lines:
            m = _SUMMARY_PATTERN.match(line.strip())
            if m:
                rnd_num = m.group(1)
                outcome = m.group(2)  # e.g. "controlled by Timur - clearly won by Timur"

                # Pick variant based on outcome language
                if "clearly won" in outcome:
                    desc = _rng_rnd.choice(_GRAPPLING_VARIANTS)
                elif "edged" in outcome:
                    desc = _rng_rnd.choice(_CLOSE_VARIANTS)
                else:
                    desc = _rng_rnd.choice(_GRAPPLING_VARIANTS)

                out.append(f"[Round {rnd_num}: {desc} — {outcome}]")
                continue

            m2 = _STRIKING_PATTERN.match(line.strip())
            if m2:
                rnd_num = m2.group(1)
                outcome = m2.group(2)
                if "clearly won" in outcome:
                    desc = _rng_rnd.choice(_STRIKING_VARIANTS)
                elif "edged" in outcome:
                    desc = _rng_rnd.choice(_CLOSE_VARIANTS)
                else:
                    desc = _rng_rnd.choice(_STRIKING_VARIANTS)
                out.append(f"[Round {rnd_num}: {desc} — {outcome}]")
                continue

            out.append(line)
        return out

    def _fix_back_control_commentary(self, lines: List[str]) -> List[str]:
        """Fix two back-control commentary bugs:
        1. Wrong fighter name — defender appears as the one landing punches
        2. Repetitive lines — same back control lines cycling rapidly

        Detects who has back control from position announcement lines,
        then checks strike lines for name swap."""
        import re as _re_bc
        import random as _rng_bc

        # Lines that announce who has back control
        _BACK_CONTROL_ANNOUNCES = [
            "has the back", "back control", "BACK MOUNT",
            "hooks are in", "Back control for",
        ]
        # Strike lines that should only come from the controller
        _CONTROLLER_STRIKE_PATTERNS = [
            r"(.+?) lands short punches to the side of (.+?)'s head",
            r"(.+?) digs in punches while controlling the back",
            r"(.+?) punishes (.+?) from behind",
            r"Short shots connect from (.+?) with the back taken",
        ]

        _BACK_CONTROL_VARIANTS = [
            "Relentless back control from {controller}.",
            "{controller} maintaining dominant position.",
            "{defender} fighting the hooks from the bottom.",
            "Back control still locked in for {controller}.",
            "Tight control from {controller}.",
        ]

        out = []
        controller = None  # who currently has back control
        defender = None
        seen_in_sequence = {}  # line -> count in current back control sequence
        in_back_control = False

        for line in lines:
            stripped = line.strip()

            # Detect back control announcements
            if any(phrase in stripped for phrase in _BACK_CONTROL_ANNOUNCES):
                # Try to extract controller name from "Back control for X"
                m = _re_bc.search(r"Back control for (.+?)!", stripped)
                if m:
                    controller = m.group(1).strip()
                m2 = _re_bc.search(r"(.+?) has the back!", stripped)
                if m2:
                    controller = m2.group(1).strip()
                m3 = _re_bc.search(r"(.+?) takes the back", stripped)
                if m3:
                    controller = m3.group(1).strip()
                in_back_control = True
                seen_in_sequence = {}
                out.append(line)
                continue

            # Detect position change away from back control
            if in_back_control and any(x in stripped for x in [
                "stands back up", "scramble", "guard position",
                "side control", "full mount", "half guard",
                "stand up", "referee", "STANDING", "Round"
            ]):
                in_back_control = False
                controller = None
                defender = None
                seen_in_sequence = {}

            # Fix wrong names + deduplicate in back control sequence
            if in_back_control and controller:
                # Check for name swap bug
                for pattern in _CONTROLLER_STRIKE_PATTERNS:
                    m = _re_bc.search(pattern, stripped)
                    if m and hasattr(m, 'group'):
                        try:
                            actor = m.group(1).strip()
                            # If actor is NOT the controller, names are swapped
                            if actor and controller and actor != controller:
                                # Swap names in the line
                                line = line.replace(actor, "___TEMP___")
                                line = line.replace(controller, actor)
                                line = line.replace("___TEMP___", controller)
                                stripped = line.strip()
                        except Exception:
                            pass

                # Deduplicate — replace 3rd+ occurrence of same line
                key = stripped[:50]  # first 50 chars as key
                seen_in_sequence[key] = seen_in_sequence.get(key, 0) + 1
                if seen_in_sequence[key] >= 3 and controller:
                    variant = _rng_bc.choice(_BACK_CONTROL_VARIANTS)
                    line = variant.format(
                        controller=controller,
                        defender=defender or "opponent"
                    )

            out.append(line)

        return out

    def _run_real_engine(self, fight: Dict, fighter1, fighter2,
                          f1_name: str, f2_name: str) -> Optional[Dict]:
        """
        Run the full narrated fight engine and translate result back to our
        fight result dict format.

        Commentary is NOT stored here — it's generated lazily on first view.
        We only store a reference to the engine result for replay.
        """
        import random

        f1_id = fighter1.fighter_id
        f2_id = fighter2.fighter_id

        fa1 = self._make_fighter_attrs(fighter1, f1_name, f1_id)
        fa2 = self._make_fighter_attrs(fighter2, f2_name, f2_id)

        # Read pre-fight fatigue and convert to starting stamina.
        # Tired fighters start with less stamina — their taper
        # discipline (or lack of it) now affects fight outcomes.
        _f1_fatigue = int(getattr(fighter1, 'fatigue', 0) or 0)
        _f2_fatigue = int(getattr(fighter2, 'fatigue', 0) or 0)
        _f1_stamina = get_starting_stamina(_f1_fatigue) if CONDITION_AVAILABLE else 100.0
        _f2_stamina = get_starting_stamina(_f2_fatigue) if CONDITION_AVAILABLE else 100.0
        print(f"  💪 [STAMINA] {fighter1.name}: fatigue={_f1_fatigue} "
              f"→ stamina={_f1_stamina:.0f} | "
              f"{fighter2.name}: fatigue={_f2_fatigue} "
              f"→ stamina={_f2_stamina:.0f}")

        # Weight-cut penalty — fighters cutting below natural class
        # take stamina hits on fight night. Scaled by age (+3%/yr after 27)
        # and softened by cardio (high cardio offsets some of the cut tax).
        _cut1 = self._get_cut_severity(f1_id)
        _cut2 = self._get_cut_severity(f2_id)
        if _cut1 > 0:
            _f1_record = self._game_state.get_fighter(f1_id) if self._game_state else None
            _age1 = getattr(_f1_record, 'age', 25) or 25
            _cardio1 = (self._game_state._fighter_data.get(f1_id, {}).get('cardio', 65)
                        if self._game_state else 65)
            _age_mult1 = 1.0 + max(0, (_age1 - 27) * 0.03)
            _stamina_pen1 = _cut1 * 12 * _age_mult1
            _cardio_offset1 = (_cardio1 - 50) / 200
            _stamina_pen1 = max(0, _stamina_pen1 - _cardio_offset1 * 10)
            _f1_stamina = max(60, _f1_stamina - _stamina_pen1)
            print(f"  ✂️  [CUT] {fighter1.name} cut penalty: "
                  f"-{_stamina_pen1:.1f} stamina "
                  f"(severity={_cut1}, age={_age1})")
        if _cut2 > 0:
            _f2_record = self._game_state.get_fighter(f2_id) if self._game_state else None
            _age2 = getattr(_f2_record, 'age', 25) or 25
            _cardio2 = (self._game_state._fighter_data.get(f2_id, {}).get('cardio', 65)
                        if self._game_state else 65)
            _age_mult2 = 1.0 + max(0, (_age2 - 27) * 0.03)
            _stamina_pen2 = _cut2 * 12 * _age_mult2
            _cardio_offset2 = (_cardio2 - 50) / 200
            _stamina_pen2 = max(0, _stamina_pen2 - _cardio_offset2 * 10)
            _f2_stamina = max(60, _f2_stamina - _stamina_pen2)
            print(f"  ✂️  [CUT] {fighter2.name} cut penalty: "
                  f"-{_stamina_pen2:.1f} stamina "
                  f"(severity={_cut2}, age={_age2})")

        # Ship K1: pre-fight coach buff for player fighter (Path α)
        _player_ids_k1 = {f.fighter_id for f in self.get_player_fighters()}
        _player_is_f1 = f1_id in _player_ids_k1
        _player_is_f2 = f2_id in _player_ids_k1
        if _player_is_f1:
            self._apply_corner_prefight_buff(fa1)
        elif _player_is_f2:
            self._apply_corner_prefight_buff(fa2)

        # Ship S1: sponsor fight-night attribute boost (both fighters)
        self._apply_sponsor_boost(fa1, fighter1)
        self._apply_sponsor_boost(fa2, fighter2)

        is_title = fight.get("is_title_fight", False)
        is_main  = fight.get("card_slot") in ("main_event", "co_main")
        total_rounds = 5 if (is_title or fight.get("card_slot") == "main_event" or fight.get("card_slot") == "co_main") else 3

        # Style matchup modifier (-0.05 to +0.05)
        style_mod = 0.0
        if STYLES_AVAILABLE:
            try:
                _STYLE_STR_MAP = {
                    "Striker":          "STRIKER",
                    "Counter Striker":  "COUNTER_STRIKER",
                    "Counter-Striker":  "COUNTER_STRIKER",
                    "Pressure Fighter": "PRESSURE_FIGHTER",
                    "Point Fighter":    "POINT_FIGHTER",
                    "Muay Thai":        "MUAY_THAI",
                    "Wrestler":         "WRESTLER",
                    "Ground & Pound":   "GROUND_AND_POUND",
                    "BJJ Specialist":   "BJJ_SPECIALIST",
                    "Clinch Fighter":   "CLINCH_FIGHTER",
                    "Sprawl & Brawl":   "SPRAWL_AND_BRAWL",
                    "Balanced":         "BALANCED",
                    "Orthodox Boxer":   "STRIKER",
                    "Kickboxer":        "STRIKER",
                    "Submission Artist":"BJJ_SPECIALIST",
                    "Sambo":            "WRESTLER",
                    "Karate":           "POINT_FIGHTER",
                    "Brawler":          "PRESSURE_FIGHTER",
                    "MMA Hybrid":       "BALANCED",
                    "Boxing":           "STRIKER",
                    "Judo":             "WRESTLER",
                    "Grappling":        "WRESTLER",
                    "Submissions":      "BJJ_SPECIALIST",
                }
                s1 = self._game_state._fighter_data.get(f1_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
                s2 = self._game_state._fighter_data.get(f2_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
                fs1 = _FightingStyleEnum(_STYLE_STR_MAP.get(s1, 'BALANCED'))
                fs2 = _FightingStyleEnum(_STYLE_STR_MAP.get(s2, 'BALANCED'))
                style_mod = get_style_matchup_modifier(fs1, fs2)
            except Exception:
                pass

        _fight_cfg = _FightConfig(
            scheduled_rounds=total_rounds,
            standup_threshold=10,
            exchanges_per_round=55,
            submission_progress_to_finish=70.0,
            submission_escape_threshold=85.0,
            damage_multiplier=FI_DAMAGE_MULTIPLIER,
        ) if _FightConfig else None
        eng_result: _NarratedFightResult = _simulate_narrated_fight_fn(
            fa1, fa2,
            rounds        = total_rounds,
            is_title_fight= is_title,
            is_main_event = is_main,
            starting_stamina_f1=_f1_stamina,
            starting_stamina_f2=_f2_stamina,
            **({"config": _fight_cfg} if _fight_cfg else {})
        )
        try:
            if eng_result and hasattr(eng_result, 'fighter1_stats'):
                _wk = self._game_state.week_number if self._game_state else 0
                for _fid, _stats in [(fa1.fighter_id, eng_result.fighter1_stats),
                                      (fa2.fighter_id, eng_result.fighter2_stats)]:
                    self._accumulate_career_stats(
                        _fid,
                        strikes=sum(int(s.get('sig_strikes_landed', 0)) for s in _stats),
                        takedowns=sum(int(s.get('td_landed', 0)) for s in _stats),
                        sub_attempts=sum(int(s.get('sub_att', 0)) for s in _stats),
                        control_time=sum(float(s.get('control_time', 0.0)) for s in _stats),
                        week=_wk,
                    )
        except Exception as _cse:
            print(f"⚠️ Career stat accumulation failed: {_cse}")
        try:
            _loser_id = eng_result.loser_id
            _method   = eng_result.method
            if _loser_id and _method:
                self._apply_chin_erosion(_loser_id, _method,
                    self._game_state.week_number if self._game_state else 0)
        except Exception as _ce:
            print(f"⚠️  Chin erosion failed: {_ce}")

        # Translate engine result → our dict format
        import random as _rnd2
        # Ship DR1 partial: guard draws before winner
        # determination corrupts records.
        if eng_result.winner_id is None:
            _is_draw   = True
            winner_id  = None
            loser_id   = None
            winner_num = 0
            winner     = None
            loser      = None
            method     = "Draw"
        else:
            _is_draw = False
            raw_winner_f1 = (eng_result.winner_id == "fighter_1"
                             or eng_result.winner_id == f1_id)
            if style_mod != 0.0 and abs(style_mod) >= 0.02:
                flip_chance = abs(style_mod) * 0.4
                if _rnd2.random() < flip_chance:
                    raw_winner_f1 = True if style_mod > 0 else False
            winner_id  = f1_id if raw_winner_f1 else f2_id
            loser_id   = f2_id if raw_winner_f1 else f1_id
            winner_num = 1 if raw_winner_f1 else 2
            winner = fighter1 if raw_winner_f1 else fighter2
            loser  = fighter2 if raw_winner_f1 else fighter1

        method_raw = eng_result.method or "DEC"
        # Normalise method string
        method_map = {
            "KO": "KO", "TKO": "TKO",
            "Submission": "SUB", "SUB": "SUB",
            "Unanimous Decision": "UNY DEC",
            "Split Decision":    "SPLIT DEC",
            "Majority Decision": "MAJ DEC",
            "Decision": "DEC",
        }
        method = method_map.get(method_raw, method_raw[:10] if len(method_raw) > 10 else method_raw)

        round_finished = getattr(eng_result, 'finish_round', None) or total_rounds
        time_str = getattr(eng_result,'finish_time',None) or "5:00"
        is_title_fight = fight.get("is_title_fight", False)

        # Update records — Ship DR1 partial: draws never touch winner/loser
        if _is_draw:
            fighter1.draws = getattr(fighter1, 'draws', 0) + 1
            fighter2.draws = getattr(fighter2, 'draws', 0) + 1
        else:
            winner.wins  += 1; loser.losses += 1
            if method in ("KO", "TKO"):
                winner.ko_wins  += 1
                loser.ko_losses = getattr(loser, 'ko_losses', 0) + 1
            elif method in ("SUB",):
                winner.sub_wins += 1
                loser.sub_losses = getattr(loser, 'sub_losses', 0) + 1
            self._apply_post_fight_camp_record(winner, loser, fight, method)

        # Post-fight experience feedback — read per-round stats from
        # eng_result and nudge attributes based on what the fight
        # actually exercised. Demux f1/f2 stats here since
        # NarratedFightResult doesn't carry fighter1_id / fighter2_id.
        for fid, opp_id, did_win in [
            (winner_id, loser_id, True),
            (loser_id,  winner_id, False),
        ]:
            try:
                _my_stats  = eng_result.fighter1_stats if fid == f1_id else eng_result.fighter2_stats
                _opp_stats = eng_result.fighter2_stats if fid == f1_id else eng_result.fighter1_stats
                self._apply_post_fight_experience(
                    fighter_id=fid,
                    opponent_id=opp_id,
                    my_stats=_my_stats or [],
                    opp_stats=_opp_stats or [],
                    method=method,
                    won=did_win,
                    total_rounds=getattr(eng_result, "total_rounds", 3),
                )
            except Exception as _xe:
                print(f"  ⚠️  [EXPERIENCE] Failed for {fid}: {_xe}")

        # AI contract decrement (fallback fight path)
        if self._game_state:
            for _ftr_c2 in [winner, loser]:
                _cid2 = self._game_state.active_contracts.get(_ftr_c2.fighter_id)
                if _cid2 and _cid2 in self._game_state._contract_data:
                    _cd2 = self._game_state._contract_data[_cid2]
                    _cd2["fights_remaining"] = max(0, _cd2.get("fights_remaining", 1) - 1)
                    if _cd2["fights_remaining"] == 0:
                        _ftr_c2.camp_id = None
                        _ftr_c2.contract_id = None
                        self._game_state.free_agents.add(_ftr_c2.fighter_id)
                        self._game_state.active_contracts.pop(_ftr_c2.fighter_id, None)
                        self._ai_bid_for_free_agent(_ftr_c2.fighter_id, _ftr_c2)

        # Fight history — write BEFORE return so cooldown loop in advance_week
        # can read lose_streak correctly (Bug S).
        for ftr, res, opp in [(winner, "W", loser), (loser, "L", winner)]:
            if not hasattr(ftr, "fight_history"):
                ftr.fight_history = []
            ftr.fight_history.append({
                "opponent_name":  opp.name,
                "opponent_id":    opp.fighter_id,
                "result":         res,
                "method":         method,
                "round_finished": round_finished,
                "event_name":     fight.get("event_name", ""),
                "week":           self._game_state.week_number if self._game_state else 1,
            })

        # Scorecard from engine if decision
        scorecard_data = None
        if method in ("DEC","UNY DEC","SPLIT DEC","MAJ DEC") and JUDGES_AVAILABLE:
            try:
                dominance = calculate_dominance_from_fight(
                    winner.overall_rating, loser.overall_rating)
                if winner_num != 1:
                    dominance = 1.0 - dominance
                # F39 fix: regenerate scorecard until tally agrees with
                # winner_num. Caps at 5 attempts.
                for _f39_attempt in range(5):
                    dec = generate_decision(
                        winner_dominance=dominance,
                        total_rounds=round_finished,
                        is_title_fight=is_title_fight,
                        fighter1_name=f1_name,
                        fighter2_name=f2_name,
                    )
                    _f1_tot = sum(sc.fighter1_score for sc in dec.scorecards)
                    _f2_tot = sum(sc.fighter2_score for sc in dec.scorecards)
                    _card_w = (1 if _f1_tot > _f2_tot
                               else 2 if _f2_tot > _f1_tot else 0)
                    if _card_w == winner_num or _card_w == 0:
                        break  # tally matches or draw
                scorecard_data = {
                    "decision_type":    dec.decision_type.value,
                    "is_split":         dec.is_split,
                    "is_controversial": dec.is_controversial,
                    "controversy_reason": dec.controversy_reason,
                    "scores_display":   dec.get_scores_display(),
                    "judges": [{"name": sc.judge_name, "f1_score": sc.fighter1_score,
                                "f2_score": sc.fighter2_score, "winner_num": sc.winner}
                               for sc in dec.scorecards],
                }
                if dec.is_split:         method = "SPLIT DEC"
                elif "Majority" in dec.decision_type.value: method = "MAJ DEC"
                else:                    method = "UNY DEC"
            except Exception:
                pass

        player_fids = set()
        if self._game_state and self._game_state.player_camp_id:
            player_fids = {f.fighter_id for f in self._game_state.get_player_fighters()}

        result = {
            "fight_id":       fight.get("fight_id"),
            "fighter1_id":    f1_id,
            "fighter2_id":    f2_id,
            "fighter1_name":  f1_name,
            "fighter2_name":  f2_name,
            "winner_id":      winner_id,
            "winner_name":    winner.name if winner else "",
            "winner_num":     winner_num,
            "loser_id":       loser_id,
            "loser_name":     loser.name if loser else "",
            "method":         method,
            "round_finished": round_finished,
            "time":           time_str,
            "weight_class":   fight.get("weight_class", ""),
            "event_name":     fight.get("event_name", ""),
            "is_title_fight": is_title_fight,
            "is_player_fight":fight.get("is_player_fight", False),
            "purse":          fight.get("purse", 0),
            "scorecard":      scorecard_data,
            "rivalry":        None,
            # Store raw engine result for lazy commentary generation
            "_engine_result": eng_result,
        }

        # ── Fight injury rolls for player fights ─────────────────────
        if INJURY_AVAILABLE and self._injury_system and self._game_state:
            import random as _pir
            _outcome_map = {
                "KO":  FightOutcome.KO, "TKO": FightOutcome.TKO,
                "SUB": FightOutcome.SUBMISSION, "DEC": FightOutcome.DECISION_UNANIMOUS,
            }
            _fo = _outcome_map.get(method, FightOutcome.DECISION_UNANIMOUS)
            for _fid_inj, _is_loser_inj in [(loser_id, True), (winner_id, False)]:
                _prob = calculate_fight_injury_probability(_fo, round_finished, _is_loser_inj)
                if _pir.random() < _prob:
                    _opp_inj = winner_id if _is_loser_inj else loser_id
                    _inj = generate_fight_injury(_fid_inj, _fo, _is_loser_inj, _opp_inj)
                    self._injury_system.add_injury(_inj)
                    _ftr_inj = self._game_state.get_fighter(_fid_inj)
                    _inj_name = getattr(_ftr_inj, 'name', _fid_inj) if _ftr_inj else _fid_inj
                    print(f"  🤕 [FIGHT INJURY] {_inj_name} — {_inj.description} "
                          f"({_inj.severity_name}) · {_inj.recovery_weeks}w")
                    if _ftr_inj and getattr(_ftr_inj, 'is_champion', False):
                        _wc_c = getattr(_ftr_inj, 'weight_class', '')
                        _hl = (f"🏆 {_inj_name} ({_wc_c} Champion) suffers "
                               f"{_inj.description} — out {_inj.recovery_weeks} weeks. "
                               f"Title defense delayed.")
                    else:
                        _hl = (f"🤕 {_inj_name} injured: {_inj.description} "
                               f"— {_inj.recovery_weeks} week recovery")
                    self._news_items.insert(0, {
                        "headline": _hl,
                        "category": "injury",
                        "week": self._game_state.week_number,
                    })
                    self._maybe_queue_champion_injury_decision(_ftr_inj, _inj)
                    # Store fight damage for training camp injury risk
                    if _ftr_inj:
                        _dmg = {"KO":80,"TKO":55,"SUB":30,"DEC":10}.get(method, 10)
                        try: setattr(_ftr_inj, 'fight_damage', _dmg if _is_loser_inj else _dmg//4)
                        except Exception: pass

        # ── Record title fight into belt history ──────────────────────
        if is_title_fight and self._game_state:
            try:
                winner_obj = self._game_state.get_fighter(winner_id)
                loser_obj  = self._game_state.get_fighter(loser_id)
                if winner_obj and loser_obj:
                    self._record_title_result(
                        weight_class = fight.get("weight_class", ""),
                        winner       = winner_obj,
                        loser        = loser_obj,
                        method       = method,
                        rnd          = round_finished,
                        event_name   = fight.get("event_name", "DFC"),
                        week         = self._game_state.week_number,
                    )
            except Exception as _te:
                print(f"  ⚠️ Title history recording failed: {_te}")

        # ── Extract and cache commentary immediately ──────────────────
        # _engine_result is stripped on save (not serializable).
        # Cache commentary as plain strings NOW so it survives save/load.
        fight_id_key = result.get("fight_id") or f"fight_{fighter1.fighter_id}_{fighter2.fighter_id}"
        if fight_id_key and fight_id_key not in self._fight_commentary:
            lines = []
            try:
                # Try full_commentary string first
                if hasattr(eng_result, 'full_commentary') and eng_result.full_commentary:
                    lines = [l for l in eng_result.full_commentary.split("\n") if l.strip()]
                # Fallback: build from round_commentary list
                if not lines and hasattr(eng_result, 'round_commentary'):
                    for rnd in (eng_result.round_commentary or []):
                        if isinstance(rnd, str):
                            lines.extend([l for l in rnd.split("\n") if l.strip()])
                        elif hasattr(rnd, 'commentary'):
                            lines.extend([l for l in str(rnd.commentary).split("\n") if l.strip()])
            except Exception as _ce:
                print(f"⚠️ Commentary extraction error: {_ce}")

            # Final fallback — always store something so watch page never blank
            if not lines:
                w_name = result.get("winner_name", "The winner")
                l_name = result.get("loser_name", "their opponent")
                method = result.get("method", "DEC")
                rnd    = result.get("round_finished", 1)
                print(f"⚠️ No commentary from engine for {fight_id_key} — using fallback")
                lines = [
                    f"=== ROUND 1 ===",
                    f"{w_name} and {l_name} touch gloves and get underway.",
                    f"{w_name} establishes early control.",
                ]
                if rnd > 1:
                    lines += [f"=== ROUND {rnd} ==="]
                lines += [
                    f"{w_name} closes the show.",
                    f"{w_name} wins by {method} in round {rnd}.",
                    f"[Result: {w_name} def. {l_name} · {method} R{rnd}]",
                ]

            # Ship K1: inject between-round corner advice for player fights.
            # Reads eng_result.fighter{1,2}_stats for per-round triggers.
            if _player_is_f1 or _player_is_f2:
                _player_ftr = fighter1 if _player_is_f1 else fighter2
                _opp_ftr    = fighter2 if _player_is_f1 else fighter1
                try:
                    lines = self._inject_corner_advice(
                        lines, eng_result, _player_ftr, _opp_ftr, _player_is_f1,
                    )
                except Exception as _ke:
                    print(f"⚠️ Corner advice injection failed ({fight_id_key}): {_ke}")
                try:
                    lines = self._dedupe_corner_advice_by_round(lines)
                except Exception as _ke:
                    print(f"⚠️ Corner advice dedupe failed ({fight_id_key}): {_ke}")
                try:
                    lines = self._enrich_round_summaries(lines)
                except Exception as _ke:
                    print(f"⚠️  Round summary enrichment failed ({fight_id_key}): {_ke}")
                try:
                    lines = self._fix_back_control_commentary(lines)
                except Exception as _ke:
                    print(f"⚠️  Back control commentary fix failed ({fight_id_key}): {_ke}")

            self._fight_commentary[fight_id_key] = lines
            print(f"✅ Commentary stored: {fight_id_key} ({len(lines)} lines)")

        return result

    def get_fight_commentary(self, fight_id: str) -> List[str]:
        """
        Return commentary for a fight. Always returns something — never empty.
        Check order: exact match → fuzzy match → _engine_result → synthetic fallback.
        """
        # 1. Exact match
        if fight_id in self._fight_commentary:
            return self._fight_commentary[fight_id]

        # 2. Fuzzy match — fight_id format may differ slightly between storage and lookup
        for stored_id, lines in self._fight_commentary.items():
            if stored_id and fight_id:
                parts = [p for p in fight_id.split('_') if len(p) > 6]
                if parts and any(p in stored_id for p in parts):
                    # Cache under the requested ID too for future lookups
                    self._fight_commentary[fight_id] = lines
                    return lines

        # 3. Try extracting from _engine_result stored in completed events
        fight_result = None
        eng_result   = None
        for ev in self._completed_events:
            for fight in ev.get("fights", []):
                if fight.get("fight_id") == fight_id:
                    fight_result = fight
                    eng_result   = fight.get("_engine_result")
                    break
            if fight_result:
                break

        if eng_result is not None:
            try:
                if isinstance(eng_result, str):
                    import re
                    m = re.search(r"full_commentary='(.*?)'(?:,|\))", eng_result, re.DOTALL)
                    if m:
                        raw = m.group(1).replace("\\n", "\n").replace("\\'", "'")
                        commentary = [l for l in raw.split("\n") if l.strip()]
                        if commentary:
                            self._fight_commentary[fight_id] = commentary
                            return commentary
                elif hasattr(eng_result, 'full_commentary') and eng_result.full_commentary:
                    commentary = [l for l in eng_result.full_commentary.split("\n") if l.strip()]
                    if commentary:
                        self._fight_commentary[fight_id] = commentary
                        return commentary
            except Exception:
                pass

        # 4. Synthetic fallback — at least show the result
        if fight_result:
            w_name = fight_result.get("winner_name", "The winner")
            l_name = fight_result.get("loser_name", "their opponent")
            method = fight_result.get("method", "DEC")
            rnd    = fight_result.get("round_finished", 3)
            lines  = [
                f"=== ROUND 1 ===",
                f"{w_name} and {l_name} touch gloves.",
                f"{w_name} takes control early.",
            ]
            if rnd > 1:
                lines.append(f"=== ROUND {rnd} ===")
            lines += [
                f"{w_name} seals it.",
                f"[Result: {w_name} def. {l_name} · {method} R{rnd}]",
            ]
            self._fight_commentary[fight_id] = lines
            return lines

        return []

        # Look for raw engine result in completed events
        eng_result = None
        for ev in self._completed_events:
            for fight in ev.get("fights", []):
                if fight.get("fight_id") == fight_id:
                    eng_result = fight.get("_engine_result")
                    break
            if eng_result:
                break

        if eng_result is None:
            return []

        try:
            # eng_result may be stored as a string repr or as the actual object
            if isinstance(eng_result, str):
                # Stored as string — extract full_commentary from the repr
                # Look for full_commentary= in the string
                import re
                m = re.search(r"full_commentary='(.*?)'(?:,|\))", eng_result, re.DOTALL)
                if m:
                    raw = m.group(1).replace("\\n", "\n").replace("\'", "'")
                    commentary = [l for l in raw.split("\n") if l.strip()]
                else:
                    commentary = []
            elif hasattr(eng_result, 'full_commentary') and eng_result.full_commentary:
                commentary = [l for l in eng_result.full_commentary.split("\n") if l.strip()]
            elif hasattr(eng_result, 'commentary'):
                commentary = eng_result.commentary or []
            else:
                commentary = []
            self._fight_commentary[fight_id] = commentary
            return commentary
        except Exception:
            return []

    # =========================================================================
    # RANK DELTA + FOTN HELPERS
    # =========================================================================

    @staticmethod
    def _rank_delta(old_rank: Optional[int], new_rank: Optional[int]) -> Optional[int]:
        """Positive = moved up (lower number = better rank)."""
        if old_rank is None or new_rank is None:
            return None
        return old_rank - new_rank  # positive = rose, negative = dropped

    def _select_fotn_builtin(self, fights: List[Dict]) -> Optional[Dict]:
        """
        Built-in FOTN selection — no external module needed.
        Priority: finish involving ranked fighters > any finish > best decision.
        """
        if not fights:
            return None
        finishes  = [f for f in fights if f.get("method") in ("KO", "TKO", "SUB")]
        decisions = [f for f in fights if f not in finishes]

        def _excitement(fight: Dict) -> float:
            # Finish type bonus — SUB > KO > TKO > DEC
            method = fight.get("method", "DEC")
            method_bonus = {"SUB": 400, "KO": 350, "TKO": 200}.get(method, 0)
            # Early finish bonus
            rnd = fight.get("round_finished", 3) or 3
            early_bonus = max(0, (4 - rnd) * 50)
            # Prestige (rank quality) — still matters but doesn't dominate
            ranks = [r for r in [fight.get("winner_new_rank"), fight.get("loser_new_rank")]
                     if r is not None]
            prestige = (999 - min(ranks)) * 0.3 if ranks else 0
            return method_bonus + early_bonus + prestige

        # Always prefer finishes, but within finishes use excitement score
        pool = finishes if finishes else decisions
        return max(pool, key=_excitement) if pool else fights[0]

    # =========================================================================
    # WATCHLIST
    # =========================================================================

    def _get_watchlist(self):
        """Lazy-init the real Watchlist object."""
        if not hasattr(self, '_watchlist_obj') or self._watchlist_obj is None:
            if WATCHLIST_AVAILABLE:
                self._watchlist_obj = Watchlist(max_entries=100)
            else:
                self._watchlist_obj = None
        return self._watchlist_obj

    def get_watchlist_entries(self) -> List[Dict[str, Any]]:
        """Return all watchlist entries as plain dicts for templates."""
        wl = self._get_watchlist()
        if not wl:
            return list(self._watchlist)  # fallback to legacy list
        out = []
        for entry in wl._entries.values():
            fighter = self.get_fighter(entry.fighter_id)
            out.append({
                "fighter_id":  entry.fighter_id,
                "name":        entry.fighter_name,
                "category":    entry.category.value,
                "category_icon": CATEGORY_INFO.get(entry.category, {}).get("icon", "👀") if WATCHLIST_AVAILABLE else "👀",
                "priority":    entry.priority.value,
                "priority_icon": PRIORITY_SYMBOLS.get(entry.priority, "⚪") if WATCHLIST_AVAILABLE else "⚪",
                "notes":       entry.notes[-1] if entry.notes else "",
                "tags":        entry.tags,
                "record":      fighter.record_str if fighter else entry.record,
                "ranking":     fighter.ranking if fighter else entry.ranking,
                "weight_class":fighter.weight_class if fighter else entry.weight_class,
                "is_champion": fighter.is_champion if fighter else entry.is_champion,
            })
        return sorted(out, key=lambda x: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}.get(x["priority"], 3),
            x["name"]
        ))

    def add_to_watchlist(self, fighter_id: str, category: str = "SCOUT",
                          priority: str = "NONE", note: str = "") -> Dict[str, Any]:
        """Add a fighter to the watchlist."""
        fighter = self.get_fighter(fighter_id)
        if not fighter:
            return {"success": False, "error": "Fighter not found"}
        wl = self._get_watchlist()
        if wl and WATCHLIST_AVAILABLE:
            try:
                cat = WatchCategory(category)
                pri = WatchPriority(priority)
                ok, msg = wl.add(
                    fighter_id=fighter_id,
                    fighter_name=fighter.name,
                    category=cat,
                    priority=pri,
                    note=note or None,
                    weight_class=fighter.weight_class,
                    record=fighter.record_str,
                    ranking=fighter.ranking or 0,
                    is_champion=fighter.is_champion,
                )
                return {"success": ok, "message": msg}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            # Fallback to legacy list
            if not any(w.get("fighter_id") == fighter_id for w in self._watchlist):
                self._watchlist.append({
                    "fighter_id": fighter_id,
                    "name": fighter.name,
                    "category": category,
                })
                return {"success": True, "message": f"Added {fighter.name} to watchlist"}
            return {"success": False, "error": "Already on watchlist"}

    def remove_from_watchlist(self, fighter_id: str) -> Dict[str, Any]:
        """Remove a fighter from the watchlist."""
        wl = self._get_watchlist()
        if wl and WATCHLIST_AVAILABLE:
            ok, msg = wl.remove(fighter_id)
            return {"success": ok, "message": msg}
        self._watchlist = [w for w in self._watchlist if w.get("fighter_id") != fighter_id]
        return {"success": True, "message": "Removed from watchlist"}

    def is_on_watchlist(self, fighter_id: str) -> bool:
        """Check if a fighter is on the watchlist."""
        wl = self._get_watchlist()
        if wl and WATCHLIST_AVAILABLE:
            return wl.contains(fighter_id)
        return any(w.get("fighter_id") == fighter_id for w in self._watchlist)

    def get_week_declines(self) -> List[str]:
        """Return fighter IDs who declined a challenge this week."""
        if not self._game_state:
            return []
        current = self._game_state.week_number
        return [fid for fid, wk in self._week_declines.items() if wk == current]

    def get_active_neg_fighter_ids(self) -> List[str]:
        """Return fighter IDs currently in a genuinely open negotiation."""
        _resolved = ("COMPLETED", "BROKEN_DOWN", "AI_DECLINED")
        active = []
        for neg in self._pending_negotiations.values():
            if neg.get("status") not in _resolved:
                active.append(neg.get("ai_fighter_id", ""))
                active.append(neg.get("player_fighter_id", ""))
        return [fid for fid in active if fid]

    # =========================================================================
    # DIVISION FIGHT BOARD
    # =========================================================================

    def get_division_fight_board(self, fighter_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns the Division Fight Board for one of the player's fighters.
        Shows their position in the division and all challengeable opponents
        with per-matchup risk/reward data.
        """
        if not self._game_state:
            return None

        fighter = self._game_state.get_fighter(fighter_id)
        if not fighter:
            return None

        wc = fighter.weight_class if isinstance(fighter.weight_class, str) else str(fighter.weight_class)
        division = self._game_state.divisions.get(wc)
        if not division:
            return None

        web_fighter  = self._convert_real_fighter(fighter)
        player_rank  = web_fighter.ranking   # 0=champ, 1-15=ranked, None=unranked

        is_booked = any(
            f.get("fighter1_id") == fighter_id or f.get("fighter2_id") == fighter_id
            for f in self._scheduled_fights
        )

        # Build ranked-order list of opponents (champion first, then #1-#15)
        ordered_ids: List[str] = []
        if division.champion_id and division.champion_id != fighter_id:
            ordered_ids.append(division.champion_id)
        for fid in division.rankings[:15]:
            if fid != fighter_id and fid not in ordered_ids:
                ordered_ids.append(fid)

        opponents = []
        for fid in ordered_ids:
            opp = self._game_state.get_fighter(fid)
            if not opp or not opp.is_active:
                continue

            opp_rank: Optional[int] = (
                0 if fid == division.champion_id
                else (division.rankings.index(fid) + 1
                      if fid in division.rankings else None)
            )

            diff = opp.overall_rating - fighter.overall_rating
            if   diff > 15: risk, reward = 5, 5
            elif diff >  8: risk, reward = 4, 4
            elif diff >  0: risk, reward = 3, 4
            elif diff > -8: risk, reward = 2, 3
            else:           risk, reward = 1, 2

            # In-range: can challenge up to 5 spots above; always challenge below
            in_range = True
            if player_rank is not None and opp_rank is not None and player_rank > 0:
                if opp_rank - player_rank < -5:
                    in_range = False

            opp_booked = any(
                f.get("fighter1_id") == fid or f.get("fighter2_id") == fid
                for f in self._scheduled_fights
            )

            camp_name = "Free Agent"
            if opp.camp_id:
                c = self._game_state.get_camp(opp.camp_id)
                if c:
                    camp_name = c.name

            # Purse estimate
            avg_rating = (fighter.overall_rating + opp.overall_rating) // 2
            est_purse  = 5000 + avg_rating * 120

            opponents.append({
                "fighter_id":  fid,
                "name":        opp.name,
                "record":      opp.record,
                "rating":      opp.overall_rating,
                "rank":        opp_rank,
                "rank_label":  "C" if opp_rank == 0 else (f"#{opp_rank}" if opp_rank else "NR"),
                "is_champion": opp.is_champion,
                "risk":        risk,
                "reward":      reward,
                "rating_diff": diff,
                "in_range":    in_range,
                "is_booked":   opp_booked,
                "camp_name":   camp_name,
                "wins":        opp.wins,
                "losses":      opp.losses,
                "est_purse":   est_purse,
            })

        champ_data = None
        if division.champion_id:
            cr = self._game_state.get_fighter(division.champion_id)
            if cr:
                champ_data = {
                    "fighter_id": division.champion_id,
                    "name":       cr.name,
                    "record":     cr.record,
                    "rating":     cr.overall_rating,
                }

        return {
            "fighter":      web_fighter,
            "fighter_id":   fighter_id,
            "division":     wc,
            "is_booked":    is_booked,
            "player_rank":  player_rank,
            "opponents":    opponents,
            "champion":     champ_data,
            "total_in_division": division.fighter_count,
        }

    # =========================================================================
    # PROSPECTS / FREE AGENTS
    # =========================================================================

    def get_prospects(self, wc_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Return free agents available to sign to the player's camp.
        Includes roster-cap and affordability data.
        """
        if not self._game_state:
            return {
                "prospects": [], "can_sign": False,
                "roster_size": 0, "max_fighters": 3,
                "balance": 0, "weight_classes": [], "wc_filter": wc_filter,
            }

        player_camp  = self._game_state.get_camp(self._game_state.player_camp_id) if self._game_state.player_camp_id else None
        tier         = getattr(player_camp, 'tier', 'GARAGE') if player_camp else 'GARAGE'
        max_fighters = self._roster_cap_for_tier(str(tier))
        roster_size  = len(self._game_state.get_player_fighters())
        can_sign     = roster_size < max_fighters

        # Champions are never signable as free agents — filter them out even
        # if they technically have no camp_id due to world-gen ordering.
        free_agents = [
            fa for fa in self._game_state.get_free_agents(wc_filter)
            if not fa.is_champion
        ]

        prospects = []
        for fa in free_agents[:60]:
            web_f        = self._convert_real_fighter(fa)
            signing_cost = 5000 + fa.overall_rating * 300
            affordable   = self._camp_balance >= signing_cost
            prospects.append({
                "fighter":      web_f,
                "signing_cost": signing_cost,
                "affordable":   affordable,
                "can_sign":     can_sign and affordable,
            })

        prospects.sort(key=lambda x: x["fighter"].overall_rating, reverse=True)

        return {
            "prospects":      prospects,
            "can_sign":       can_sign,
            "roster_size":    roster_size,
            "max_fighters":   max_fighters,
            "balance":        self._camp_balance,
            "weight_classes": self._game_state.WEIGHT_CLASSES,
            "wc_filter":      wc_filter,
        }

    # =========================================================================
    # CAMP PERSONALITY SYSTEM
    # =========================================================================

    def _get_camp_archetype(self, camp_id: str) -> str:
        """Return (and cache) the personality archetype for a camp."""
        if camp_id in self._camp_archetypes:
            return self._camp_archetypes[camp_id]
        if not self._game_state:
            return "Numbers Game"
        camp = self._game_state.get_camp(camp_id)
        if not camp:
            return "Numbers Game"
        name    = getattr(camp, 'name', '')
        country = getattr(camp, 'country', '')
        tier    = str(getattr(camp, 'tier', 'GARAGE'))
        arch = _assign_camp_archetype(name, country, tier, camp_id)
        self._camp_archetypes[camp_id] = arch
        return arch

    def _score_fighter_for_camp(self, fighter, camp_id: str) -> float:
        """
        Score how much a camp wants a particular fighter based on its archetype.
        Higher = stronger preference.
        Returns 0.0 if camp refuses to sign this fighter at all.
        """
        import random
        arch_name = self._get_camp_archetype(camp_id)
        arch      = CAMP_ARCHETYPES.get(arch_name, CAMP_ARCHETYPES["Numbers Game"])

        age     = getattr(fighter, 'age', 25)
        ovr     = getattr(fighter, 'overall_rating', 50)
        style   = getattr(fighter, 'fighting_style', '') or ''
        wins    = getattr(fighter, 'wins', 0)
        losses  = getattr(fighter, 'losses', 0)
        ko_wins = getattr(fighter, 'ko_wins', 0)
        sub_wins= getattr(fighter, 'sub_wins', 0)
        pop     = getattr(fighter, 'popularity', 10)
        nat     = getattr(fighter, 'nationality', '') or getattr(fighter, 'country', '') or ''
        ceiling = 0
        if self._game_state and fighter.fighter_id in self._game_state._fighter_data:
            ceiling = self._game_state._fighter_data[fighter.fighter_id].get('potential', ovr + 5)

        # Get camp nationality for hometown check
        camp_country = ""
        if self._game_state:
            camp_rec = self._game_state.get_camp(camp_id)
            camp_country = getattr(camp_rec, 'country', '') if camp_rec else ''

        score = 50.0  # Base

        # ── OVR contribution ──
        score += ovr * arch.get("ovr_care", 1.0)

        # ── Age preferences ──
        age_max = arch.get("age_max", 99)
        age_min = arch.get("age_min", 0)
        if age <= age_max and "age_bonus" in arch:
            score += (age_max - age) * arch["age_bonus"]
        elif age >= age_min and "age_bonus" in arch:
            score += (age - age_min + 1) * arch["age_bonus"]

        # ── Potential ceiling ──
        pot_min = arch.get("potential_min", 0)
        if ceiling < pot_min:
            return 0.0  # Hard pass
        if "potential_bonus" in arch:
            score += ceiling * arch["potential_bonus"]

        # ── OVR floor ──
        if ovr < arch.get("ovr_min", 0):
            return 0.0  # Hard pass

        # ── Style preference ──
        style_pref = arch.get("style_pref", [])
        grapple_styles = arch.get("grapple_styles", [])
        if style_pref and style in style_pref:
            score += arch.get("style_bonus", 2.0) * 20
        elif grapple_styles and style in grapple_styles:
            score *= arch.get("style_penalty", 0.5)

        # ── Win record ──
        if "win_bonus" in arch and wins > 0:
            score += wins * arch["win_bonus"] * 3

        # ── Popularity ──
        if pop < arch.get("popularity_min", 0):
            return 0.0
        if "popularity_bonus" in arch:
            score += pop * arch["popularity_bonus"]

        # ── Hometown bonus ──
        if "nationality_bonus" in arch and nat and camp_country:
            if nat.lower() == camp_country.lower():
                score += arch["nationality_bonus"] * 25

        # ── Rank preference ──
        rank = None
        if self._game_state:
            div = self._game_state.divisions.get(getattr(fighter, 'weight_class', ''))
            if div and fighter.fighter_id in (div.rankings or []):
                rank = div.rankings.index(fighter.fighter_id) + 1
        if "rank_bonus" in arch:
            rank_max = arch.get("rank_max", 15)
            if rank and rank <= rank_max:
                score += arch["rank_bonus"] * 20
            elif arch.get("rank_bonus", 0) > 2:
                return 0.0  # Elite Academy won't sign unranked

        # ── Finisher bonus ──
        if "finish_bonus" in arch and wins > 0:
            finish_rate = (ko_wins + sub_wins) / wins
            score += finish_rate * arch["finish_bonus"] * 20

        # Small random variance so same-score fighters aren't always identical
        score += random.uniform(-3, 3)
        return max(0.0, score)

    # =========================================================================
    # CONTRACT SYSTEM
    # =========================================================================

    def _process_coach_contract(self, current_week: int) -> None:
        """Weekly coach contract tick. Ship MC1b: iterates over all staff
        coaches independently. Each has its own contract clock + morale.
        Releases mutate the staff list, so iterate over a snapshot.
        """
        # Build iteration source: prefer staff, fall back to legacy single
        if self._coaching_staff:
            _iter_source = list(self._coaching_staff)
        elif self._coach_contract:
            _iter_source = [{"coach_id": self._coach_contract.get("coach_id"),
                             "contract": self._coach_contract}]
        else:
            return

        for _cs in _iter_source:
            contract = _cs.get('contract') if 'contract' in _cs else _cs
            if not contract:
                continue
            cid = _cs.get('coach_id') or contract.get('coach_id')

            # Decrement contract clock
            contract["weeks_completed"] = contract.get("weeks_completed", 0) + 1
            contract["weeks_remaining"] = max(0,
                contract.get("total_weeks", 26) - contract["weeks_completed"])

            # Skipped-paycheck morale decay
            skipped = contract.get("skipped_paychecks", 0)
            if skipped > 0:
                contract["morale"] = max(0,
                    contract.get("morale", COACH_MORALE_START)
                    - (skipped * COACH_SKIPPED_PAYCHECK_DECAY))
                contract["skipped_paychecks"] = 0

            # Underpaid morale decay
            market_rate = int(contract.get("rating", 60) * COACH_MARKET_RATE_PER_RATING)
            if contract.get("salary", 0) < market_rate * COACH_UNDERPAID_THRESHOLD:
                contract["morale"] = max(0,
                    contract.get("morale", COACH_MORALE_START) - COACH_UNDERPAID_DECAY)

            # Legacy mirror: if this is the head coach, keep _coach_contract in sync
            if cid and cid == self._head_coach_id:
                self._coach_contract = contract

            # Contract expiry → immediate walk
            if contract["weeks_remaining"] <= 0:
                self._release_coach('contract_expired', coach_id=cid)
                continue

            # Morale walkout → immediate
            if contract.get("morale", COACH_MORALE_START) <= COACH_MORALE_WALKOUT:
                underpaid = contract.get("salary", 0) < market_rate * COACH_UNDERPAID_THRESHOLD
                if underpaid:
                    self._release_coach('quit_underpaid', coach_id=cid)
                else:
                    self._release_coach('quit_skipped_pay', coach_id=cid)

    def _release_coach(self, reason: str, coach_id: Optional[str] = None) -> None:
        """Coach departs. Ship MC1b: accepts optional coach_id to target a
        specific staff member; falls back to head coach. Removes from
        _coaching_staff, re-elects head if needed, mirrors legacy state."""
        # Resolve target — prefer staff lookup, fall back to legacy contract
        target_entry = None
        target_id = coach_id or self._head_coach_id
        if target_id:
            for c in self._coaching_staff:
                if c.get('coach_id') == target_id:
                    target_entry = c
                    break
        if target_entry:
            name = target_entry.get('name', 'Coach')
        elif self._coach_contract:
            name = self._coach_contract.get("name", "Coach")
            target_id = self._coach_contract.get("coach_id") or target_id
        else:
            return

        current_week = self._game_state.week_number if self._game_state else 0

        if reason == 'quit_underpaid':
            headline = f"💼 {name} quit — said you weren't paying him what he's worth"
        elif reason == 'quit_skipped_pay':
            headline = f"💼 {name} walked out — too many missed paychecks"
        elif reason == 'contract_expired':
            headline = f"📋 {name}'s contract expired — they've moved on"
        elif reason == 'fired':
            headline = f"🚪 You released {name} from the camp"
        else:
            headline = f"💼 {name} left the camp"

        self._news_items.insert(0, {
            "headline": headline,
            "category": "coach",
            "week":     current_week,
        })
        print(f"  💼 [COACH] {name} departed — {reason}")

        # Remove from staff list
        if target_id:
            self._coaching_staff = [
                c for c in self._coaching_staff
                if c.get('coach_id') != target_id
            ]

        # Re-elect head if the departing coach was head
        if self._head_coach_id == target_id:
            self._head_coach_id = (
                self._coaching_staff[0].get('coach_id')
                if self._coaching_staff else None
            )

        # Legacy dual-write — sync _coach/_coach_contract to new head, or
        # clear to placeholder if no coaches remain
        if self._head_coach_id:
            new_head = next(
                (c for c in self._coaching_staff
                 if c.get('coach_id') == self._head_coach_id),
                None,
            )
            if new_head:
                self._coach = {
                    "name":      new_head["name"],
                    "specialty": new_head["specialty"],
                    "rating":    new_head["rating"],
                    "salary":    new_head["salary"],
                    "traits":    new_head.get("traits", []),
                    "archetype": new_head.get("archetype", "mma_head"),
                    "coach_id":  self._head_coach_id,
                }
                self._coach_contract = new_head.get("contract", {})
            else:
                self._coach_contract = {}
                self._coach = dict(COACH_VACANT_PLACEHOLDER)
        else:
            self._coach_contract = {}
            self._coach = dict(COACH_VACANT_PLACEHOLDER)

        self._clear_cache()

    def _process_contracts(self, current_week: int) -> None:
        """
        Called each advance_week:
        1. Decrement fights_remaining for fighters who fought this week
        2. Update morale based on performance + inactivity
        3. Handle expiry → holdout → walkout
        4. Notify player of expiring contracts
        """
        if not self._game_state:
            return

        player_camp_id = self._game_state.player_camp_id

        # Identify who fought this week via fight_history
        for fid, contract in list(self._contracts.items()):
            if contract.get('camp_id') != player_camp_id:
                continue
            ftr = self._game_state.get_fighter(fid)
            if not ftr:
                self._contracts.pop(fid, None)
                continue

            # Founding-fighter loyalty bonus: softer morale curves + floor.
            # Flag set only at _create_player_fighter for the starter.
            is_founder = contract.get('is_founding_fighter', False)
            morale_floor = FOUNDING_FIGHTER_MORALE_FLOOR if is_founder else 0
            loss_penalty = FOUNDING_FIGHTER_LOSS_PENALTY if is_founder else 10
            streak_penalty = FOUNDING_FIGHTER_STREAK_PENALTY if is_founder else 3
            idle_threshold = FOUNDING_FIGHTER_IDLE_THRESHOLD if is_founder else 10
            idle_decay = FOUNDING_FIGHTER_IDLE_DECAY if is_founder else 2
            holdout_window = FOUNDING_FIGHTER_HOLDOUT_WINDOW if is_founder else HOLDOUT_WINDOW

            history = getattr(ftr, 'fight_history', []) or []

            # Decrement if they fought this week
            if history and isinstance(history[-1], dict):
                if history[-1].get('week') == current_week:
                    contract['fights_completed'] = contract.get('fights_completed', 0) + 1
                    contract['fights_remaining'] = max(0,
                        contract['total_fights'] - contract['fights_completed'])
                    # Morale: win = +8, loss compounds with streak (founder eased)
                    last_result = history[-1].get('result', '')
                    ls = getattr(ftr, 'lose_streak', 0) or 0
                    if last_result == 'W':
                        contract['morale'] = min(100, contract.get('morale', 75) + 8)
                    elif last_result == 'L':
                        contract['morale'] = max(morale_floor,
                            contract.get('morale', 75) - (loss_penalty + ls * streak_penalty))
                    # Ship L1: win streak demand — fighter wants recognition.
                    # One-shot per streak via win_demand_fired_week flag.
                    win_streak = self._get_fighter_win_streak(ftr)
                    fights_completed = contract.get('fights_completed', 0)
                    if (win_streak >= 3
                            and not contract.get('win_demand_fired_week')
                            and fights_completed >= 1):
                        contract['win_demand_fired_week'] = current_week
                        self._news_items.insert(0, {
                            "headline": (f"💰 {ftr.name} is on a {win_streak}-"
                                         f"fight win streak and wants contract "
                                         f"recognition. Consider re-signing early."),
                            "category": "contract",
                            "week": current_week,
                        })
                    elif win_streak == 0:
                        contract.pop('win_demand_fired_week', None)
                    # Coach trait morale effects — fire on fight week
                    _coach_traits = (self._coach.get('traits', [])
                                     if getattr(self, '_coach', None) else [])
                    if _coach_traits:
                        _m = contract.get('morale', 75)
                        if 'TASKMASTER' in _coach_traits:
                            _m -= 3
                        if 'MOTIVATOR' in _coach_traits and _m < 60:
                            _m += 5
                        if 'PLAYERS_COACH' in _coach_traits:
                            _m += 3
                        if 'SUPPORTIVE' in _coach_traits:
                            _m += 3
                        if 'BURNED_OUT' in _coach_traits:
                            _m += 5  # silver lining
                        if 'CALM_CORNER' in _coach_traits:
                            # Post-fight morale recovery if last fight was a loss
                            _last_r = None
                            _fh_cc = list(getattr(ftr, 'fight_history', []) or [])
                            if _fh_cc and isinstance(_fh_cc[-1], dict):
                                _last_r = _fh_cc[-1].get('result')
                            if _last_r == 'L':
                                _m += 5
                        contract['morale'] = max(morale_floor, min(100, _m))
            else:
                # Inactivity morale decay — founder: 1 pt/wk after 14w; others: 2 pt/wk after 10w
                last_fight_week = history[-1].get('week', 0) if history and isinstance(history[-1], dict) else 0
                if current_week - last_fight_week >= idle_threshold:
                    contract['morale'] = max(morale_floor, contract.get('morale', 75) - idle_decay)

            morale = contract.get('morale', 75)
            fights_remaining = contract.get('fights_remaining', 1)

            # Terminal: morale status for low fighters
            if morale <= 50:
                _ftr_name = getattr(ftr, 'name', fid)
                _ls = getattr(ftr, 'lose_streak', 0) or 0
                _reason = []
                if _ls >= 2:   _reason.append(f"{_ls}L streak")
                history = getattr(ftr, 'fight_history', []) or []
                _last_w = history[-1].get('week', 0) if history and isinstance(history[-1], dict) else 0
                _inactive = (current_week - _last_w) if _last_w else 0
                if _inactive >= 8: _reason.append(f"{_inactive}w inactive")
                _mood = "😠" if morale <= 30 else "😐"
                print(f"  {_mood} [MORALE] {_ftr_name} — {morale} morale"
                      + (f" ({', '.join(_reason)})" if _reason else ""))

            # Last fight warning
            if fights_remaining == 1 and not contract.get('is_holdout'):
                self._news_items.insert(0, {
                    "headline": f"📋 {ftr.name} is on the last fight of their contract — consider re-signing",
                    "category": "contract",
                    "week": current_week,
                })

            # Contract expired → holdout (founder gets longer window + softer headline)
            if fights_remaining <= 0:
                if contract.get('is_holdout'):
                    hw = contract.get('holdout_weeks', 0) + 1
                    contract['holdout_weeks'] = hw
                    if hw >= holdout_window:
                        self._release_fighter_to_free_agency(fid, ftr.name, 'contract expired')
                        continue
                    else:
                        remaining = holdout_window - hw
                        self._news_items.insert(0, {
                            "headline": f"⚠️ {ftr.name} in holdout — re-sign within {remaining}w or lose them",
                            "category": "contract",
                            "week": current_week,
                        })
                else:
                    contract['is_holdout'] = True
                    contract['holdout_weeks'] = 0
                    if is_founder:
                        _headline = f"📋 {ftr.name}'s contract is up — they want to talk before walking"
                    else:
                        _headline = f"📋 {ftr.name}'s contract expired — {holdout_window} weeks to re-sign"
                    self._news_items.insert(0, {
                        "headline": _headline,
                        "category": "contract",
                        "week": current_week,
                    })

            # Low morale → holdout or walkout
            elif morale <= MORALE_WALKOUT:
                self._release_fighter_to_free_agency(fid, ftr.name, 'unhappy')
            elif morale <= MORALE_HOLDOUT and not contract.get('is_holdout'):
                contract['is_holdout'] = True
                contract['holdout_weeks'] = 0
                self._news_items.insert(0, {
                    "headline": f"😠 {ftr.name} is unhappy with the camp — re-sign or they'll leave",
                    "category": "contract",
                    "week": current_week,
                })

    def _release_fighter_to_free_agency(self, fighter_id: str,
                                         name: str, reason: str) -> None:
        """Strip fighter from player camp, add to free agents, AI may pick up."""
        if not self._game_state:
            return
        ftr = self._game_state.get_fighter(fighter_id)
        if ftr:
            ftr.camp_id = None
            ftr.contract_id = None
        self._game_state.free_agents.add(fighter_id)

        # Capture contract context BEFORE pop so we can branch news headline
        # and decide whether to apply roster-wide morale hit.
        contract = self._contracts.get(fighter_id, {})
        is_founder = contract.get('is_founding_fighter', False)
        fights_completed = contract.get('fights_completed', 0)

        # Non-founders trigger roster hit only when "important" (champ, top-10,
        # or veteran with 6+ fights completed). Founders always trigger.
        is_important = False
        if ftr:
            _rank = self._get_fighter_rank(ftr)
            is_important = (
                getattr(ftr, 'is_champion', False)
                or (_rank is not None and _rank <= 10)
                or fights_completed >= 6
            )

        self._contracts.pop(fighter_id, None)
        reason_str = "contract expired" if reason == 'contract expired' else "unhappy with camp"

        # Branched headline — founders get a heavier line that acknowledges
        # the history without exposing the founding-fighter mechanic.
        if is_founder:
            _headline = f"💔 {name} — once the heart of your camp — walks away as a free agent"
        else:
            _headline = f"🚪 {name} has left your camp ({reason_str}) — now a free agent"
        self._news_items.insert(0, {
            "headline": _headline,
            "category": "contract",
            "week": self._game_state.week_number,
        })
        print(f"  🚪 [CONTRACT] {name} left — {reason_str}")

        # Roster morale hit when a meaningful departure happens
        should_hit_roster = is_founder or is_important
        if should_hit_roster:
            hit = FOUNDING_FIGHTER_WALK_ROSTER_HIT
            affected = 0
            for other_fid, other_contract in self._contracts.items():
                if other_fid == fighter_id:
                    continue
                current = other_contract.get('morale', 75)
                other_contract['morale'] = max(0, current - hit)
                affected += 1
            if affected > 0:
                reason_tag = "founding member" if is_founder else "key fighter"
                print(f"  💔 [ROSTER MORALE] {name} leaving as {reason_tag} — roster down {hit} morale ({affected} fighters)")

        # AI camps may immediately bid for released fighter
        self._ai_bid_for_free_agent(fighter_id, ftr)
        self._clear_cache()

    def _ai_bid_for_free_agent(self, fighter_id: str, fighter) -> None:
        """
        After a fighter becomes a free agent, AI camps bid personality-first.
        50% chance AI picks them up within the same week (simulates fast market).
        """
        if not self._game_state or not fighter:
            return
        import random
        if random.random() > 0.50:
            return  # Fighter stays free agent this week

        ai_camps = [
            c for c in self._game_state.camps.values()
            if not c.is_player
            and getattr(c, 'fighter_count', 0) < getattr(c, 'max_fighters', 6)
        ]
        if not ai_camps:
            return

        camp_scores = []
        for ec in ai_camps:
            score = self._score_fighter_for_camp(fighter, ec.camp_id)
            if score > 0:
                camp_scores.append((score, ec))

        if not camp_scores:
            return

        camp_scores.sort(key=lambda x: x[0], reverse=True)
        winning_camp = camp_scores[0][1]

        # Sign them via the canonical helper (creates contract, increments
        # fighter_count, updates _camp_data["fighters"], populates
        # active_contracts + _contract_data, discards from free_agents)
        contract_id = self._game_state._sign_fighter_to_camp(
            fighter_id, winning_camp.camp_id
        )
        if not contract_id:
            return  # Sign failed; don't fire news
        arch = self._get_camp_archetype(winning_camp.camp_id)
        arch_emoji = CAMP_ARCHETYPES.get(arch, {}).get("emoji", "🏟️")
        _top_score = camp_scores[0][0] if camp_scores else 0
        # Filter: only post news for established signings (≥60 OVR or has fight history).
        # Suppresses spam from world-init churn now that fighter_count is correctly tracked.
        _has_fights = bool(getattr(fighter, 'fight_history', []) or [])
        _ovr = getattr(fighter, 'overall_rating', 0) or 0
        if _ovr >= 60 or _has_fights:
            _style = getattr(fighter, 'fighting_style', 'Balanced')
            self._news_items.insert(0, {
                "headline": f"{arch_emoji} {fighter.name} signs with {winning_camp.name} — {_style}, OVR {_ovr}",
                "category": "signing",
                "week": self._game_state.week_number,
            })
        print(f"  {arch_emoji} [AI SIGNING] {fighter.name} → {winning_camp.name} "
              f"({arch}) [score: {_top_score:.0f}]")

    def _get_head_coach(self) -> Dict[str, Any]:
        """Ship MC1a foundation: return head coach dict.
        Prefers _coaching_staff if populated; falls back to legacy
        self._coach until MC1b migrates write sites. Never returns None.
        """
        if self._coaching_staff:
            if self._head_coach_id:
                for c in self._coaching_staff:
                    if c.get('coach_id') == self._head_coach_id:
                        return c
            return self._coaching_staff[0]
        _legacy = getattr(self, '_coach', None)
        if _legacy:
            return _legacy
        return {
            "name":      "Head Coach",
            "specialty": "boxing",
            "rating":    60,
            "salary":    800,
            "traits":    [],
            "archetype": "mma_head",
        }

    def _get_head_coach_contract(self) -> Dict[str, Any]:
        """Ship MC1a foundation: return head coach contract dict.
        Prefers _coaching_staff if populated; falls back to legacy
        self._coach_contract. Empty dict signals no coach hired."""
        if self._coaching_staff:
            hc = self._get_head_coach()
            cid = hc.get('coach_id')
            if cid:
                for c in self._coaching_staff:
                    if c.get('coach_id') == cid:
                        return c.get('contract', {})
            return {}
        return getattr(self, '_coach_contract', None) or {}

    def get_coach_contract_status(self) -> Dict[str, Any]:
        """
        Returns coach contract details for UI display. Includes
        underpaid status and morale band. Ship C2.
        """
        if not self._coach_contract:
            return {"has_coach": False}
        c = self._coach_contract
        market_rate = int(c["rating"] * COACH_MARKET_RATE_PER_RATING)
        is_underpaid = c["salary"] < market_rate * COACH_UNDERPAID_THRESHOLD
        morale = c.get("morale", COACH_MORALE_START)
        if morale >= 70:
            morale_label = "Happy"
            morale_color = "var(--neon-green)"
        elif morale >= 40:
            morale_label = "OK"
            morale_color = "var(--warning)"
        else:
            morale_label = "Unhappy"
            morale_color = "var(--blood-red)"
        return {
            "has_coach":         True,
            "name":              c["name"],
            "specialty":         c["specialty"],
            "rating":            c["rating"],
            "salary":            c["salary"],
            "market_rate":       market_rate,
            "is_underpaid":      is_underpaid,
            "total_weeks":       c["total_weeks"],
            "weeks_remaining":   c.get("weeks_remaining", c["total_weeks"]),
            "weeks_completed":   c.get("weeks_completed", 0),
            "morale":            morale,
            "morale_label":      morale_label,
            "morale_color":      morale_color,
            "traits":            c.get("traits", []),
            "archetype":         c.get("archetype", ""),
            # Ship MC1b — staff list for facility multi-coach UI
            "staff_list":        self._get_staff_list_for_ui(),
        }

    def _get_staff_list_for_ui(self) -> List[Dict[str, Any]]:
        """Return coaching staff formatted for the facility template.
        Ship MC1b."""
        try:
            from routes import _TRAIT_DISPLAY as _td
        except Exception:
            _td = {}
        result = []
        for c in self._coaching_staff:
            contract = c.get('contract', {})
            traits = c.get('traits', [])
            trait_display = [
                _td.get(t, (t.replace('_', ' ').title(), 'personality'))
                for t in traits
            ]
            result.append({
                "coach_id":        c.get('coach_id'),
                "name":            c.get('name', 'Coach'),
                "specialty":       c.get('specialty', 'mma'),
                "archetype":       c.get('archetype', 'mma_head'),
                "rating":          c.get('rating', 60),
                "salary":          c.get('salary', 800),
                "traits":          traits,
                "trait_display":   trait_display,
                "is_head":         (c.get('coach_id') == self._head_coach_id),
                "morale":          contract.get('morale', 85),
                "weeks_remaining": contract.get('weeks_remaining', 0),
                "total_weeks":     contract.get('total_weeks', 52),
            })
        return result

    def fire_coach(self, coach_id: Optional[str] = None) -> Dict[str, Any]:
        """Fire a coach by id, or head coach if no id given. Ship MC1b."""
        if not self._coaching_staff and not self._coach_contract:
            return {"success": False, "error": "No coach to fire"}
        target_id = coach_id or self._head_coach_id or (
            self._coaching_staff[0].get('coach_id')
            if self._coaching_staff else None
        )
        self._release_coach('fired', coach_id=target_id)
        return {"success": True, "message": "Coach released"}

    def hire_coach(self, coach_data: Dict[str, Any], contract_weeks: int) -> Dict[str, Any]:
        """Hire a coach onto the staff. Ship MC1b: supports multiple coaches
        up to tier slot limit. Dual-writes to legacy _coach/_coach_contract
        AND _coaching_staff so existing read sites continue to work until
        MC1c migrates them."""
        import uuid as _uuid
        tier = self._get_camp_tier()
        max_slots = COACH_TIER_STAFF_SLOTS.get(tier, 1)
        if len(self._coaching_staff) >= max_slots:
            return {
                "success": False,
                "error": (f"Staff full — {tier} tier allows "
                          f"{max_slots} coach"
                          f"{'es' if max_slots != 1 else ''}"),
            }
        valid_weeks = COACH_TIER_CONTRACT_OPTIONS.get(tier, [26])
        if contract_weeks not in valid_weeks:
            contract_weeks = valid_weeks[-1]

        coach_id = (coach_data.get("coach_id")
                    or coach_data.get("id")
                    or str(_uuid.uuid4())[:12])
        name      = coach_data.get("name", "Coach")
        specialty = str(coach_data.get("specialty", "mma") or "mma").lower()
        rating    = int(coach_data.get("rating", 60) or 60)
        salary    = int(coach_data.get("salary", 800) or 800)
        _ct = coach_data.get("traits", []) or []
        traits = [t if isinstance(t, str) else getattr(t, 'value', str(t)) for t in _ct]
        _arch = coach_data.get("archetype", "mma_head")
        archetype = _arch.value if hasattr(_arch, 'value') else str(_arch) or "mma_head"

        contract = {
            "coach_id":          coach_id,
            "name":              name,
            "specialty":         specialty,
            "rating":            rating,
            "salary":            salary,
            "traits":            traits,
            "archetype":         archetype,
            "total_weeks":       contract_weeks,
            "weeks_completed":   0,
            "weeks_remaining":   contract_weeks,
            "morale":            COACH_MORALE_START,
            "signed_week":       (self._game_state.week_number
                                  if self._game_state else 0),
            "skipped_paychecks": 0,
        }
        staff_entry = {
            "coach_id":  coach_id,
            "name":      name,
            "specialty": specialty,
            "rating":    rating,
            "salary":    salary,
            "traits":    traits,
            "archetype": archetype,
            "contract":  contract,
        }
        self._coaching_staff.append(staff_entry)

        # Designate as head if first on staff
        if not self._head_coach_id:
            self._head_coach_id = coach_id

        # Legacy dual-write — existing read sites continue to work until MC1c
        if self._head_coach_id == coach_id:
            self._coach = {
                "name":      name,
                "specialty": specialty,
                "rating":    rating,
                "salary":    salary,
                "traits":    traits,
                "archetype": archetype,
                "coach_id":  coach_id,
            }
            self._coach_contract = contract

        self._news_items.insert(0, {
            "headline": (f"✅ Signed {name} as head coach — "
                         f"{contract_weeks}w @ ${salary:,}/wk"
                         if self._head_coach_id == coach_id else
                         f"📝 Signed {name} to coaching staff — "
                         f"{contract_weeks}w @ ${salary:,}/wk"),
            "category": "coach",
            "week":     (self._game_state.week_number
                         if self._game_state else 0),
        })
        print(f"  ✅ Coach: {name} ({specialty}, {rating} rating)")
        print(f"  📝 Coach contract: {name} — {contract_weeks}w @ ${salary:,}/wk")
        self._clear_cache()
        return {"success": True, "coach_id": coach_id,
                "message": f"Signed {name}"}

    def set_head_coach(self, coach_id: str) -> Dict[str, Any]:
        """Designate a staff coach as head coach. Updates legacy
        _coach/_coach_contract to point at the new head. Ship MC1b."""
        target = None
        for c in self._coaching_staff:
            if c.get('coach_id') == coach_id:
                target = c
                break
        if not target:
            return {"success": False, "error": "Coach not on staff"}
        self._head_coach_id = coach_id
        self._coach = {
            "name":      target["name"],
            "specialty": target["specialty"],
            "rating":    target["rating"],
            "salary":    target["salary"],
            "traits":    target.get("traits", []),
            "archetype": target.get("archetype", "mma_head"),
            "coach_id":  coach_id,
        }
        self._coach_contract = target.get("contract", {})
        self._clear_cache()
        return {"success": True}

    def get_coach_market(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Return the persistent coaching market. Refreshes if empty,
        force_refresh=True, or market is older than 12 weeks. Ship MC1b."""
        current_week = (self._game_state.week_number
                        if self._game_state else 0)
        age = current_week - self._coach_market_week
        if (not self._coach_market or force_refresh or age >= 12):
            self._coach_market = self._generate_coach_market()
            self._coach_market_week = current_week
        return self._coach_market

    def _generate_coach_market(self) -> List[Dict[str, Any]]:
        """Generate a fresh pool of available coaches. 6 candidates,
        excludes coaches already on staff. Ship MC1b."""
        import uuid as _uuid
        try:
            from game_start import COACH_TRAITS, generate_starting_coaches
            raw = generate_starting_coaches(num_coaches=8)
        except Exception:
            return []

        staff_names = {c.get('name', '') for c in self._coaching_staff}
        pool = []
        for c in raw:
            name = getattr(c, 'name', '') or (c.get('name', '') if isinstance(c, dict) else '')
            if not name or name in staff_names:
                continue
            raw_traits = getattr(c, 'traits', None)
            if raw_traits is None and isinstance(c, dict):
                raw_traits = c.get('traits', [])
            raw_traits = raw_traits or []
            traits = []
            for t in raw_traits:
                _k = str(t).upper().replace(' ', '_').replace("'", '')
                if _k in COACH_TRAITS:
                    traits.append(_k)
            specialty = (getattr(c, 'specialty', None)
                         or (c.get('specialty') if isinstance(c, dict) else None)
                         or 'mma')
            rating = int(getattr(c, 'skill_level', None)
                         or getattr(c, 'rating', None)
                         or (c.get('rating') if isinstance(c, dict) else 60)
                         or 60)
            salary = int(getattr(c, 'weekly_salary', None)
                         or getattr(c, 'salary', None)
                         or (c.get('salary') if isinstance(c, dict) else 800)
                         or 800)
            pool.append({
                "coach_id": str(_uuid.uuid4())[:12],
                "name":      name,
                "specialty": specialty,
                "rating":    rating,
                "salary":    salary,
                "traits":    traits,
                "archetype": self._specialty_to_archetype(specialty),
            })
            if len(pool) >= 6:
                break
        return pool

    def _specialty_to_archetype(self, specialty: str) -> str:
        """Map specialty string to archetype bucket. Ship MC1b."""
        _s = str(specialty).lower()
        if _s in {'boxing','kickboxing','muay thai','muay_thai',
                  'striking','clinch'}:
            return 'striking'
        if _s in {'wrestling','bjj','judo','grappling','submissions',
                  'sambo','jiu-jitsu','jiu_jitsu'}:
            return 'grappling'
        if _s in {'strength','conditioning','sc','s&c','s and c',
                  'fitness','athletic','cardio'}:
            return 'sc'
        return 'mma_head'

    def remove_from_coach_market(self, coach_id: str) -> None:
        """Remove a hired coach from the market. Ship MC1b."""
        self._coach_market = [
            c for c in self._coach_market
            if c.get('coach_id') != coach_id
        ]

    def get_coach_contract_options(self) -> List[int]:
        """Available contract lengths for hiring at current tier. Ship C2."""
        tier = self._get_camp_tier()
        return COACH_TIER_CONTRACT_OPTIONS.get(tier, [26])

    def get_contract_status(self, fighter_id: str) -> Optional[Dict[str, Any]]:
        """Return contract info for a player fighter."""
        c = self._contracts.get(fighter_id)
        if not c:
            return None
        morale = c.get('morale', 75)
        fr = c.get('fights_remaining', 0)
        return {
            "total_fights":     c['total_fights'],
            "fights_remaining": fr,
            "fights_completed": c.get('fights_completed', 0),
            "morale":           morale,
            "is_holdout":       c.get('is_holdout', False),
            "holdout_weeks":    c.get('holdout_weeks', 0),
            "contract_label":   f"{fr} of {c['total_fights']} fights remaining",
            "warning":          fr <= 1 or c.get('is_holdout', False),
            "morale_label": (
                "😠 Unhappy"     if morale <= 30 else
                "😐 Disgruntled" if morale <= 50 else
                "🙂 Content"     if morale <= 70 else
                "😊 Happy"       if morale <= 85 else
                "🔥 Fired up"
            ),
            "morale_color": (
                "var(--blood-red)"  if morale <= 30 else
                "var(--warning)"    if morale <= 50 else
                "var(--text-muted)" if morale <= 70 else
                "var(--neon-green)"
            ),
        }

    def _get_cut_severity(self, fighter_id: str) -> int:
        """Return cut severity for a fighter.
        0 = no cut (fighting at or above natural class)
        1 = one-class cut (moderate)
        2 = two-class cut (severe, rare)
        Uses natural_weight_class vs current weight_class."""
        _WC = ["Strawweight","Flyweight","Bantamweight",
               "Featherweight","Lightweight","Welterweight",
               "Middleweight","Light Heavyweight","Heavyweight"]
        fighter = self._game_state.get_fighter(fighter_id) if self._game_state else None
        if not fighter:
            return 0
        current = getattr(fighter, 'weight_class', '') or ''
        natural = getattr(fighter, 'natural_weight_class', '') or ''
        # Fallback to _fighter_data if FighterRecord doesn't have it set
        if not natural and self._game_state:
            natural = self._game_state._fighter_data.get(
                fighter_id, {}).get('natural_weight_class', '') or ''
        if not current or not natural or current == natural:
            return 0
        try:
            cur_idx = _WC.index(current)
            nat_idx = _WC.index(natural)
        except ValueError:
            return 0
        # Cut = natural is heavier than current (fighting below natural weight)
        return max(0, nat_idx - cur_idx)

    def _check_weight_class_alerts(self) -> None:
        """Proactive coach suggestions when a player fighter's body frame
        signals they should consider a class change. 12-week per-fighter
        cooldown so the channel doesn't spam."""
        if not self._game_state:
            return
        current_week = self._game_state.week_number
        if not hasattr(self, '_wc_alert_fired'):
            self._wc_alert_fired = {}

        _WC = ["Strawweight","Flyweight","Bantamweight",
               "Featherweight","Lightweight","Welterweight",
               "Middleweight","Light Heavyweight","Heavyweight"]

        for pf in self.get_player_fighters():
            fid = pf.fighter_id
            last_fired = self._wc_alert_fired.get(fid, -99)
            if current_week - last_fired < 12:
                continue  # 12-week cooldown — don't spam

            bf = getattr(pf, 'body_frame',
                self._game_state._fighter_data.get(fid, {}).get('body_frame', 5)) or 5
            natural = (getattr(pf, 'natural_weight_class', None)
                       or pf.weight_class)
            current = pf.weight_class
            age = getattr(pf, 'age', 25) or 25

            coach_name = (self._coach.get('name', 'Your coach')
                          if getattr(self, '_coach', None) else 'Your coach')

            # Signal: naturally large for class — should consider moving up
            if (bf >= 8 and natural != current and current in _WC
                    and _WC.index(current) < len(_WC) - 1):
                self._news_items.insert(0, {
                    "headline": (f"💪 {coach_name} on {pf.name}: "
                                 f"'{pf.name} is a natural {natural}. The cut to "
                                 f"{current} is holding them back — consider moving up.'"),
                    "category": "coach",
                    "week": current_week,
                })
                self._wc_alert_fired[fid] = current_week

            # Signal: naturally small for class + losing streak
            elif (bf <= 3 and natural != current and current in _WC
                    and _WC.index(current) > 0
                    and getattr(pf, 'lose_streak', 0) >= 2):
                self._news_items.insert(0, {
                    "headline": (f"📉 {coach_name} on {pf.name}: "
                                 f"'{pf.name} has the skills but is getting outmuscled. "
                                 f"Moving down to {natural} could unlock their potential.'"),
                    "category": "coach",
                    "week": current_week,
                })
                self._wc_alert_fired[fid] = current_week

            # Signal: aging fighter cutting hard
            elif age >= 30 and bf >= 7 and natural != current:
                self._news_items.insert(0, {
                    "headline": (f"⏳ {coach_name} on {pf.name}: "
                                 f"'At {age}, the cut to {current} is getting harder "
                                 f"every camp. Moving to {natural} could extend their career.'"),
                    "category": "coach",
                    "week": current_week,
                })
                self._wc_alert_fired[fid] = current_week

    def _check_ai_weight_class_moves(self) -> None:
        """AI fighters consider moving weight class based on losing
        streaks and body frame. 26-week cooldown. Champions never
        move. Injury-blocked fighters skip."""
        if not self._game_state:
            return
        current_week = self._game_state.week_number
        if not hasattr(self, '_ai_wc_move_cooldown'):
            self._ai_wc_move_cooldown = {}

        _WC = ["Strawweight","Flyweight","Bantamweight",
               "Featherweight","Lightweight","Welterweight",
               "Middleweight","Light Heavyweight","Heavyweight"]

        import random
        player_ids = {pf.fighter_id for pf in self.get_player_fighters()}

        for fid, fighter in self._game_state.fighters.items():
            # Skip player fighters, champions, inactive
            if fid in player_ids:
                continue
            if getattr(fighter, 'is_champion', False):
                continue
            if not getattr(fighter, 'is_active', True):
                continue

            # Cooldown check
            last_move = self._ai_wc_move_cooldown.get(fid, -99)
            if current_week - last_move < 26:
                continue

            wc = getattr(fighter, 'weight_class', '')
            if wc not in _WC:
                continue
            idx = _WC.index(wc)

            bf = int(self._game_state._fighter_data.get(
                fid, {}).get('body_frame', 5) or 5)
            lose_streak = getattr(fighter, 'lose_streak', 0) or 0
            age = getattr(fighter, 'age', 25) or 25

            moved = False

            # Move up: aging large-frame fighter on losing streak
            if (lose_streak >= 2 and bf >= 7 and age >= 30
                    and idx < len(_WC) - 1):
                if random.random() < 0.20:
                    new_class = _WC[idx + 1]
                    fighter.weight_class = new_class
                    old_div = self._game_state.divisions.get(wc)
                    if old_div:
                        old_div.rankings = [r for r in old_div.rankings if r != fid]
                    self._update_rankings_after_fight(wc)
                    self._update_rankings_after_fight(new_class)
                    self._ai_wc_move_cooldown[fid] = current_week
                    self._news_items.insert(0, {
                        "headline": (f"💪 {fighter.name} moves up to "
                                     f"{new_class} after struggling at {wc}."),
                        "category": "signing",
                        "week": current_week,
                    })
                    moved = True

            # Move down: small-frame fighter on extended losing streak
            if (not moved and lose_streak >= 3 and bf <= 3 and idx > 0):
                if random.random() < 0.15:
                    new_class = _WC[idx - 1]
                    fighter.weight_class = new_class
                    old_div = self._game_state.divisions.get(wc)
                    if old_div:
                        old_div.rankings = [r for r in old_div.rankings if r != fid]
                    self._update_rankings_after_fight(wc)
                    self._update_rankings_after_fight(new_class)
                    self._ai_wc_move_cooldown[fid] = current_week
                    self._news_items.insert(0, {
                        "headline": (f"📉 {fighter.name} drops to {new_class} "
                                     f"— looking for a fresh start."),
                        "category": "signing",
                        "week": current_week,
                    })

    def _process_ai_camp_roster(self, current_week: int) -> None:
        """AI camp roster management — fires weekly.

        Three actions:
        1. Cut underperformers: 3+ lose streak, unranked or outside top 10,
           10% chance per week. 26-week per-fighter cooldown.
        2. Demand release: Hungry/Warrior personality with 4+ lose streak
           demands out. 20% chance.
        3. Idle self-release: unused 20+ weeks with 2+ lose streak, 15%.

        Releases bypass _release_fighter_to_free_agency (which is
        player-centric) and inline the bare release operation."""
        if not self._game_state:
            return
        import random as _rnd

        if not hasattr(self, '_ai_cut_cooldown'):
            self._ai_cut_cooldown = {}

        player_camp_id = self._game_state.player_camp_id

        def _release_to_fa(_fid, _ftr):
            """Inline AI-side release — no player-centric news, no
            immediate re-bid (the FA bidding sweep handles pickup)."""
            old_camp_id = _ftr.camp_id
            _ftr.camp_id = None
            _ftr.contract_id = None
            self._game_state.free_agents.add(_fid)
            old_camp = self._game_state.camps.get(old_camp_id)
            if old_camp:
                old_camp.fighter_count = max(0, old_camp.fighter_count - 1)
            _cd = self._game_state._camp_data.get(old_camp_id, {})
            if isinstance(_cd.get('fighters'), list) and _fid in _cd['fighters']:
                _cd['fighters'].remove(_fid)

        for fid, fighter in list(self._game_state.fighters.items()):
            # Skip player camp, champions, inactive, free agents
            if fighter.camp_id == player_camp_id:
                continue
            if not fighter.camp_id:
                continue
            if not getattr(fighter, 'is_active', True):
                continue
            if getattr(fighter, 'is_champion', False):
                continue

            # Cooldown — don't cut same fighter twice in 26w
            last_cut = self._ai_cut_cooldown.get(fid, -99)
            if current_week - last_cut < 26:
                continue

            lose_streak = self._get_fighter_lose_streak(fighter)
            rank = self._get_fighter_rank(fighter)
            personality = (
                self._game_state._fighter_data.get(fid, {})
                    .get('personality')
                or getattr(fighter, 'personality', '')
                or 'Competitor'
            )
            camp_name = ""
            camp = self._game_state.camps.get(fighter.camp_id)
            if camp:
                camp_name = getattr(camp, 'name', '')

            released = False

            # Action 1: camp cuts underperformer
            if (lose_streak >= 3
                    and (rank is None or rank > 10)):
                if _rnd.random() < 0.10:
                    _release_to_fa(fid, fighter)
                    self._ai_cut_cooldown[fid] = current_week
                    # News only for ranked/familiar fighters (suppress churn spam)
                    if rank is not None and rank <= 15:
                        self._news_items.insert(0, {
                            "headline": (f"🚪 {fighter.name} released by "
                                         f"{camp_name} after "
                                         f"{lose_streak}-fight skid."),
                            "category": "signing",
                            "week": current_week,
                        })
                    released = True

            # Action 2: fighter demands release (personality)
            if (not released
                    and lose_streak >= 4
                    and personality in ("Hungry", "Warrior")):
                if _rnd.random() < 0.20:
                    _release_to_fa(fid, fighter)
                    self._ai_cut_cooldown[fid] = current_week
                    self._news_items.insert(0, {
                        "headline": (f"📢 {fighter.name} demands release "
                                     f"from {camp_name} — looking for "
                                     f"a fresh start."),
                        "category": "signing",
                        "week": current_week,
                    })
                    released = True

            # Action 3: idle fighter self-release
            if not released and lose_streak >= 2:
                history = getattr(fighter, 'fight_history', []) or []
                last_fight_week = 0
                if history and isinstance(history[-1], dict):
                    last_fight_week = history[-1].get('week', 0)
                idle_weeks = current_week - last_fight_week
                if idle_weeks >= 20:
                    if _rnd.random() < 0.15:
                        _release_to_fa(fid, fighter)
                        self._ai_cut_cooldown[fid] = current_week
                        self._news_items.insert(0, {
                            "headline": (f"📢 {fighter.name} parts ways "
                                         f"with {camp_name} after "
                                         f"{idle_weeks} weeks of inactivity."),
                            "category": "signing",
                            "week": current_week,
                        })

    def _process_weekly_sponsors(self, current_week: int) -> None:
        """Weekly sponsor processing:
        1. Pay weekly retainers to player camp.
        2. Check drop conditions per personality:
             aggressive — drops after 2 consecutive decisions
             image     — drops after loss
             prestige  — drops if fighter falls out of top 5
             loyalty   — never drops
        3. Generate inbound sponsor offers for player fighters
           based on rank tier (10% per week per eligible brand).
        4. Assign sponsors to a small AI sample per week."""
        if not self._game_state:
            return
        import random as _rnd

        player_fighter_ids = {pf.fighter_id for pf in self.get_player_fighters()}

        # --- 1. Pay retainers + check drop conditions ---
        for fid in list(player_fighter_ids):
            fdata = self._game_state._fighter_data.get(fid, {})
            sponsors = fdata.get("sponsors", []) or []
            kept = []
            for s in sponsors:
                brand = _SPONSOR_BY_ID.get(s.get("sponsor_id", ""))
                if not brand:
                    continue
                fighter = self._game_state.get_fighter(fid)
                dropped = False
                personality = brand["personality"]

                # Pay retainer
                self._camp_balance += brand["weekly_retainer"]

                if personality == "aggressive":
                    history = getattr(fighter, 'fight_history', []) or []
                    recent = [f for f in history[-3:] if isinstance(f, dict)]
                    dec_streak = 0
                    for f in reversed(recent):
                        if f.get('result') == 'W' and f.get('method') == 'DEC':
                            dec_streak += 1
                        else:
                            break
                    if dec_streak >= 2:
                        dropped = True
                elif personality == "image":
                    history = getattr(fighter, 'fight_history', []) or []
                    if history and isinstance(history[-1], dict):
                        last = history[-1]
                        if last.get('result') == 'L':
                            p_rank = self._get_fighter_rank(fighter)
                            lose_streak = self._get_fighter_lose_streak(fighter)
                            if lose_streak >= 1 and (p_rank is None or p_rank > 10):
                                dropped = True
                elif personality == "prestige":
                    rank = self._get_fighter_rank(fighter)
                    if rank is None or rank > 5:
                        dropped = True
                # loyalty never drops

                if dropped:
                    self._news_items.insert(0, {
                        "headline": (f"💔 {brand['name']} drops "
                                     f"{getattr(fighter,'name',fid)} "
                                     f"from their roster."),
                        "category": "signing",
                        "week": current_week,
                    })
                else:
                    kept.append(s)
            fdata["sponsors"] = kept

        # --- 2. Inbound sponsor offers for player fighters ---
        for fid in player_fighter_ids:
            fighter = self._game_state.get_fighter(fid)
            if not fighter:
                continue
            fdata = self._game_state._fighter_data.setdefault(fid, {})
            current_sponsors = {s["sponsor_id"]
                                for s in fdata.get("sponsors", []) or []}
            rank = self._get_fighter_rank(fighter)

            eligible_tiers = ["local"]
            if rank is not None and rank <= 15:
                eligible_tiers.append("regional")
            if rank is not None and rank <= 5:
                eligible_tiers.append("elite")

            for personality, brands in SPONSOR_BRANDS.items():
                for brand in brands:
                    if brand["tier"] not in eligible_tiers:
                        continue
                    if brand["id"] in current_sponsors:
                        continue
                    if self._get_sponsor_client_count(brand["id"]) >= brand["max_clients"]:
                        continue
                    if (brand["personality"] == "prestige"
                            and (rank is None or rank > 5)):
                        continue
                    if _rnd.random() > 0.10:
                        continue
                    fdata.setdefault("sponsors", []).append({
                        "sponsor_id":  brand["id"],
                        "signed_week": current_week,
                    })
                    self._news_items.insert(0, {
                        "headline": (f"🎯 {brand['name']} signs "
                                     f"{getattr(fighter,'name',fid)}! "
                                     f"+${brand['weekly_retainer']:,}/wk "
                                     f"retainer + "
                                     f"${brand['fight_bonus']:,} per fight."),
                        "category": "signing",
                        "week": current_week,
                    })
                    current_sponsors.add(brand["id"])

        # --- 3. AI fighter sponsor assignment (sample 5/week) ---
        all_fids = list(self._game_state._fighter_data.keys())
        _rnd.shuffle(all_fids)
        ai_processed = 0
        for fid in all_fids:
            if fid in player_fighter_ids:
                continue
            if ai_processed >= 5:
                break
            fdata = self._game_state._fighter_data[fid]
            if fdata.get("sponsors"):
                continue
            fighter = self._game_state.get_fighter(fid)
            if not fighter:
                continue
            rank = self._get_fighter_rank(fighter)
            if rank is not None and rank <= 5:
                tier = "elite"
            elif rank is not None and rank <= 15:
                tier = "regional"
            else:
                tier = "local"
            candidates = [
                b for brands in SPONSOR_BRANDS.values()
                for b in brands
                if b["tier"] == tier
                and self._get_sponsor_client_count(b["id"]) < b["max_clients"]
            ]
            if not candidates:
                continue
            brand = _rnd.choice(candidates)
            fdata.setdefault("sponsors", []).append({
                "sponsor_id":  brand["id"],
                "signed_week": current_week,
            })
            ai_processed += 1

    def _process_ai_free_agent_bidding(self, current_week: int) -> None:
        """Weekly AI free agent pickup sweep. Caps at 3 signings
        per advance to prevent thrash. Uses existing
        _ai_bid_for_free_agent helper (which discards from
        free_agents on successful sign)."""
        if not self._game_state:
            return
        free_agents = self._game_state.get_free_agents()
        if not free_agents:
            return
        import random as _rnd
        _rnd.shuffle(free_agents)
        signed = 0
        for fa in free_agents:
            if signed >= 3:
                break
            # Helper takes (fighter_id, fighter) and discards from
            # free_agents on successful sign — detect via post-call check.
            self._ai_bid_for_free_agent(fa.fighter_id, fa)
            if fa.fighter_id not in self._game_state.free_agents:
                signed += 1

    def _process_pending_challenges(self, current_week: int) -> None:
        """Resolve pending player challenges after a 1-2 week delay.
        Uses fighter personality + rank + streak to decide accept/decline.
        Accepted challenges promote to _pending_negotiations so the player
        can finalize via the existing negotiation flow."""
        if not self._pending_challenges or not self._game_state:
            return
        import random as _rnd

        to_remove = []
        for cid, chal in self._pending_challenges.items():
            if chal.get("status") != "PENDING":
                to_remove.append(cid)
                continue
            if current_week < chal.get("response_week", 9999):
                continue  # Not time yet

            target_id   = chal["target_fighter_id"]
            player_id   = chal["player_fighter_id"]
            target_name = chal["target_fighter_name"]
            player_name = chal["player_fighter_name"]
            personality = chal.get("target_personality", "Competitor")

            target = self._game_state.get_fighter(target_id)
            player = self._game_state.get_fighter(player_id)

            # Base acceptance chance — 0.60 so same-tier
            # challenges feel viable by default
            chance = 0.60

            # Ranking proximity — tiered bonus/penalty.
            # Treat unranked fighters as rank 16 so proximity
            # bonus still fires for unranked vs unranked (gap=0)
            # and unranked vs low-ranked (small gap).
            p_rank = chal.get("player_rank")
            t_rank = chal.get("target_rank")
            _p = p_rank if p_rank else 16
            _t = t_rank if t_rank else 16
            gap = abs(_t - _p)
            proximity_bonus = 0.0
            if gap <= 3:
                proximity_bonus = 0.25   # Same tier — strong bonus
            elif gap <= 5:
                proximity_bonus = 0.10   # Close tier — small bonus
            elif gap > 6:
                proximity_bonus = -0.15  # Big gap — penalty
            chance += proximity_bonus

            # Player win streak — momentum makes you
            # attractive as an opponent
            p_streak = self._get_fighter_win_streak(player) \
                if player else 0
            chance += min(p_streak * 0.08, 0.24)

            # Target lose streak — desperate to bounce back
            t_lose = getattr(target, 'lose_streak', 0) or 0
            chance += min(t_lose * 0.10, 0.20)

            # Target idle weeks — hasn't fought recently.
            # max(0, ...) guards against negative values from
            # sim-history week mismatches (e.g. fight_history
            # entries with week > current_week post-load).
            t_idle = 0
            t_history = getattr(target, 'fight_history', []) or []
            if t_history:
                last_week = t_history[-1].get('week', 0) if isinstance(t_history[-1], dict) else 0
                t_idle = max(0, current_week - last_week)
                chance += min(t_idle * 0.05, 0.15)

            # Title shot proximity penalty — top contenders are picky
            title_pen = 0.0
            if t_rank is not None and t_rank <= 2:
                title_pen = -0.15
                chance += title_pen

            # Tightened spread — personality flavors decisions
            # without completely blocking fair matchups
            _PERSONALITY_MULT = {
                "Warrior":    1.3,
                "Hungry":     1.3,
                "Competitor": 1.1,
                "Calculated": 0.85,
                "Political":  0.90,
            }
            mult = _PERSONALITY_MULT.get(personality, 1.0)
            chance *= mult

            # Political: only accepts if fight helps ranking
            if personality == "Political":
                if t_rank and p_rank and p_rank > t_rank:
                    chance *= 0.4   # Won't fight down
                else:
                    chance *= 1.3   # Happy to fight up

            chance = max(0.05, min(0.95, chance))
            roll = _rnd.random()
            accepted = roll < chance

            if accepted:
                # Promote to a real negotiation using the existing schema
                # so the player can finalize via /negotiate/<neg_id>.
                neg_id = f"neg_{player_id[:8]}_{target_id[:8]}_{current_week}"
                wc = chal.get("weight_class",
                              getattr(player, 'weight_class', '') if player else '')
                p_ovr = getattr(player, 'overall_rating', 70) if player else 70
                t_ovr = getattr(target, 'overall_rating', 70) if target else 70
                base_purse = max(5000, int((p_ovr + t_ovr) * 100))
                weeks_out = self._weeks_out_for_fight(p_rank, t_rank)
                event_name = self._dfc_label(current_week + weeks_out)
                t_record = (f"{getattr(target, 'wins', 0)}-"
                            f"{getattr(target, 'losses', 0)}"
                            if target else "")
                neg = {
                    "neg_id":              neg_id,
                    "player_fighter_id":   player_id,
                    "player_fighter_name": player_name,
                    "ai_fighter_id":       target_id,
                    "ai_fighter_name":     target_name,
                    "ai_fighter_record":   t_record,
                    "ai_fighter_rating":   t_ovr,
                    "ai_fighter_rank":     t_rank,
                    "ai_personality":      personality,
                    "weight_class":        wc,
                    "base_purse":          base_purse,
                    "current_purse":       base_purse,
                    "weeks_out":           weeks_out,
                    "exchange_count":      1,
                    "status":              "AI_ACCEPTED",
                    "history":             [{"by": "AI", "decision": "ACCEPT",
                                             "purse": base_purse}],
                    "event_name":          event_name,
                }
                self._pending_negotiations[neg_id] = neg
                self._news_items.insert(0, {
                    "headline": (f"✅ {target_name} accepted your challenge! "
                                 f"Head to negotiations to finalize."),
                    "category": "signing",
                    "week":     current_week,
                })
            else:
                _DECLINE_REASONS = {
                    "Warrior":    "isn't interested in that matchup right now.",
                    "Hungry":     "already has other opportunities lined up.",
                    "Competitor": "doesn't think the timing is right.",
                    "Calculated": "feels the risk doesn't suit their plans.",
                    "Political":  "is focused on fights that move the needle.",
                }
                reason = _DECLINE_REASONS.get(personality, "passed on the challenge.")
                self._news_items.insert(0, {
                    "headline": (f"❌ {target_name} {reason} "
                                 f"Your challenge was declined."),
                    "category": "signing",
                    "week":     current_week,
                })
                # 4-week re-challenge cooldown
                if not hasattr(self, '_challenge_cooldown'):
                    self._challenge_cooldown = {}
                self._challenge_cooldown[target_id] = current_week

            chal["status"] = "ACCEPTED" if accepted else "DECLINED"
            to_remove.append(cid)

        for cid in to_remove:
            self._pending_challenges.pop(cid, None)

    def get_pending_challenges(self) -> List[Dict[str, Any]]:
        """Return pending challenges for dashboard display."""
        return [
            c for c in self._pending_challenges.values()
            if c.get("status") == "PENDING"
        ]

    def get_pending_negotiations(self) -> List[Dict[str, Any]]:
        """Return open negotiations awaiting player action,
        for dashboard display. These are accepted challenges
        the player hasn't finalized yet."""
        if not self._game_state:
            return []
        result = []
        for neg in self._pending_negotiations.values():
            status = neg.get("status", "")
            # Only surface negs the player needs to act on
            if status not in ("AI_ACCEPTED", "AI_COUNTERED"):
                continue
            result.append({
                "neg_id":              neg.get("neg_id", ""),
                "player_fighter_name": neg.get("player_fighter_name", ""),
                "ai_fighter_name":     neg.get("ai_fighter_name", ""),
                "weight_class":        neg.get("weight_class", ""),
                "status":              status,
                "status_label":        ("Accepted — awaiting you"
                                        if status == "AI_ACCEPTED"
                                        else "Countered — needs your response"),
                "event_name":          neg.get("event_name", ""),
            })
        return result

    def get_player_sponsors(self) -> List[Dict[str, Any]]:
        """Return sponsor info for player fighters, for profile display."""
        result = []
        if not self._game_state:
            return result
        for pf in self.get_player_fighters():
            fid = pf.fighter_id
            sponsors = self._game_state._fighter_data.get(
                fid, {}).get("sponsors", []) or []
            for s in sponsors:
                brand = _SPONSOR_BY_ID.get(s.get("sponsor_id", ""))
                if brand:
                    result.append({
                        "fighter_id":      fid,
                        "fighter_name":    pf.name,
                        "brand_name":      brand["name"],
                        "tier":            brand["tier"],
                        "personality":     brand["personality"],
                        "weekly_retainer": brand["weekly_retainer"],
                        "fight_bonus":     brand["fight_bonus"],
                        "attr_boost":      brand["attr_boost"],
                    })
        return result

    def move_weight_class(self, fighter_id: str,
                          new_class: str) -> Dict[str, Any]:
        """Move a player fighter to an adjacent weight class.
        Vacates belt if champion. Cancels scheduled fights.
        Removes from old division rankings. Updates weight_class.
        12-week per-fighter cooldown tracked in _wc_move_cooldown."""
        if not self._game_state:
            return {"success": False, "error": "No active game."}

        _WC = ["Strawweight","Flyweight","Bantamweight",
               "Featherweight","Lightweight","Welterweight",
               "Middleweight","Light Heavyweight","Heavyweight"]

        fighter = self._game_state.get_fighter(fighter_id)
        if not fighter:
            return {"success": False, "error": "Fighter not found."}

        old_class = fighter.weight_class
        if new_class not in _WC:
            return {"success": False,
                    "error": f"{new_class} is not a valid weight class."}

        # Adjacency gate — only ±1 class allowed
        try:
            old_idx = _WC.index(old_class)
            new_idx = _WC.index(new_class)
        except ValueError:
            return {"success": False, "error": "Invalid weight class."}
        if abs(new_idx - old_idx) != 1:
            return {"success": False,
                    "error": "Can only move one weight class at a time."}

        # Injury gate
        if INJURY_AVAILABLE and self._injury_system:
            if not self._injury_system.is_cleared_to_fight(fighter_id):
                return {"success": False,
                        "error": f"{fighter.name} is injured and "
                                 f"cannot change weight class right now."}

        # Cooldown gate — 12 weeks between moves
        if not hasattr(self, '_wc_move_cooldown'):
            self._wc_move_cooldown = {}
        current_week = self._game_state.week_number
        last_move = self._wc_move_cooldown.get(fighter_id, -99)
        if current_week - last_move < 12:
            weeks_left = 12 - (current_week - last_move)
            return {"success": False,
                    "error": f"{fighter.name} must wait {weeks_left} "
                             f"more week(s) before changing class again."}

        direction = "up" if new_idx > old_idx else "down"
        direction_label = "moves up to" if direction == "up" else "drops down to"

        # 1. Vacate belt if champion
        if fighter.is_champion:
            fighter.is_champion = False
            old_div = self._game_state.divisions.get(old_class)
            if old_div:
                old_div.champion_id = None
                old_div.champion_name = None
            self._news_items.insert(0, {
                "headline": (f"🏆 {fighter.name} vacates the "
                             f"{old_class} title to move "
                             f"{direction} to {new_class}."),
                "category": "title",
                "week": current_week,
            })

        # 2. Cancel scheduled fights
        cancelled = [f for f in self._scheduled_fights
                     if f.get("fighter1_id") == fighter_id
                     or f.get("fighter2_id") == fighter_id]
        for f in cancelled:
            self._scheduled_fights.remove(f)
            opp = (f.get("fighter2_name")
                   if f.get("fighter1_id") == fighter_id
                   else f.get("fighter1_name"))
            self._news_items.insert(0, {
                "headline": (f"🚫 {fighter.name} vs {opp} cancelled "
                             f"— {fighter.name} {direction_label} "
                             f"{new_class}."),
                "category": "signing",
                "week": current_week,
            })

        # Cancel from upcoming cards — unlock if card drops below capacity
        for wk_card in self._upcoming_cards.values():
            wk_card["fights"] = [
                f for f in wk_card.get("fights", [])
                if f.get("fighter1_id") != fighter_id
                and f.get("fighter2_id") != fighter_id
            ]
            if len(wk_card.get("fights", [])) < CARD_TARGET_FIGHTS:
                wk_card["locked"] = False

        # Cancel from deferred queue
        self._ai_deferred_bookings = [
            q for q in self._ai_deferred_bookings
            if q.get("fighter1_id") != fighter_id
            and q.get("fighter2_id") != fighter_id
        ]

        # Cancel fight offers involving this fighter
        self._fight_offers = [
            o for o in self._fight_offers
            if o.get("fighter_id") != fighter_id
            and o.get("opponent_id") != fighter_id
        ]

        # 3. Remove from old division rankings + decrement count
        old_div = self._game_state.divisions.get(old_class)
        if old_div:
            old_div.rankings = [r for r in old_div.rankings if r != fighter_id]
            old_div.fighter_count = max(0, old_div.fighter_count - 1)

        # 4. Update weight class on the FighterRecord
        fighter.weight_class = new_class
        # If moving to natural class, ensure _fighter_data is in sync.
        # setdefault avoids losing the write when fighter_id isn't in the dict.
        nat = getattr(fighter, 'natural_weight_class', '') or ''
        if nat == new_class:
            _fd = self._game_state._fighter_data.setdefault(fighter_id, {})
            _fd['natural_weight_class'] = new_class

        # 5. Update new division fighter count
        new_div = self._game_state.divisions.get(new_class)
        if new_div:
            new_div.fighter_count += 1

        # 6. Refresh rankings for both divisions
        self._update_rankings_after_fight(old_class)
        self._update_rankings_after_fight(new_class)

        # 7. Set cooldown
        self._wc_move_cooldown[fighter_id] = current_week

        # 8. News headline
        icon = "💪" if direction == "up" else "📉"
        self._news_items.insert(0, {
            "headline": (f"{icon} {fighter.name} {direction_label} "
                         f"{new_class}! They'll begin their campaign "
                         f"unranked in the new division."),
            "category": "signing",
            "week": current_week,
        })

        self._clear_cache()
        msg = (f"{fighter.name} has moved {direction} to {new_class}. "
               f"They start unranked in the new division.")
        if cancelled:
            msg += f" {len(cancelled)} scheduled fight(s) cancelled."
        return {"success": True, "message": msg}

    def _morale_label(self, morale: int) -> str:
        """Short label for morale value — mirrors get_contract_status tiers."""
        if morale >= 86: return "🔥 Fired up"
        if morale >= 71: return "😊 Happy"
        if morale >= 51: return "🙂 Content"
        if morale >= 31: return "😐 Disgruntled"
        return "😠 Unhappy"

    def get_expiring_contracts(self) -> List[Dict[str, Any]]:
        """Return contracts with <=2 fights remaining for player camp fighters.
        Used by dashboard alert."""
        expiring = []
        if not self._game_state:
            return expiring
        player_camp_id = self._game_state.player_camp_id
        for fid, contract in self._contracts.items():
            if contract.get('camp_id') != player_camp_id:
                continue
            fights_left = contract.get('fights_remaining', 0)
            if fights_left <= 2:
                fighter = self._game_state.get_fighter(fid)
                if not fighter:
                    continue
                expiring.append({
                    "fighter_id":   fid,
                    "fighter_name": getattr(fighter, 'name', fid),
                    "fights_left":  fights_left,
                    "morale":       contract.get('morale', 75),
                    "morale_label": self._morale_label(contract.get('morale', 75)),
                })
        return expiring

    def get_contract_ask(self, fighter_id: str) -> Dict[str, Any]:
        """Generate the fighter's re-sign ask message based on morale and
        recent record. Returns flavor text and a suggested purse multiplier."""
        contract = self._contracts.get(fighter_id, {})
        morale = contract.get('morale', 75)
        fighter = self._game_state.get_fighter(fighter_id) if self._game_state else None

        # Recent record from fight history
        history = getattr(fighter, 'fight_history', []) or []
        recent = history[-3:] if len(history) >= 3 else history
        recent_wins = sum(1 for f in recent if f.get('result') == 'W')
        win_streak = 0
        for f in reversed(history):
            if f.get('result') == 'W':
                win_streak += 1
            else:
                break

        # Build the ask
        if morale >= 80 and win_streak >= 3:
            msg = (f"I've won {win_streak} straight. "
                   f"I think I've earned a raise.")
            multiplier = 1.3
        elif morale >= 80 and recent_wins >= 2:
            msg = ("Things are going well here. "
                   "I want to stay — let's get a deal done.")
            multiplier = 1.15
        elif morale >= 60:
            msg = ("I'm happy with how things are going. "
                   "Fair terms and I'll sign.")
            multiplier = 1.0
        elif morale >= 40:
            msg = ("It's been a tough run. "
                   "I just want to keep competing.")
            multiplier = 0.9
        elif win_streak == 0 and len(history) >= 2:
            msg = ("I need a change. "
                   "If you want me to stay, show me you believe in me.")
            multiplier = 1.1  # unhappy but wants validation
        else:
            msg = ("I'm not sure this is working out. "
                   "Make me an offer.")
            multiplier = 1.0

        base_purse = contract.get('purse_per_fight', 5000)
        suggested = int(base_purse * multiplier)
        return {
            "message":    msg,
            "multiplier": multiplier,
            "suggested":  suggested,
            "morale":     morale,
            "win_streak": win_streak,
        }

    def resign_fighter(self, fighter_id: str,
                       contract_fights: int = 3) -> Dict[str, Any]:
        """Re-sign an existing roster fighter to a new contract."""
        if not self._game_state:
            return {"success": False, "error": "No game loaded"}
        ftr = self._game_state.get_fighter(fighter_id)
        if not ftr:
            return {"success": False, "error": "Fighter not found"}
        if ftr.camp_id != self._game_state.player_camp_id:
            return {"success": False, "error": "Not your fighter"}

        player_camp = self._game_state.get_camp(self._game_state.player_camp_id)
        tier = str(getattr(player_camp, 'tier', 'GARAGE') if player_camp else 'GARAGE').upper()
        max_contract = TIER_CONTRACT_MAX.get(tier, 3)
        # Founding fighter override: extended-length unlock regardless of tier
        current = self._contracts.get(fighter_id, {})
        if current.get('is_founding_fighter'):
            max_contract = max(FOUNDING_FIGHTER_MAX_CONTRACT, max_contract)
        if contract_fights not in CONTRACT_OPTIONS:
            contract_fights = 3
        if contract_fights > max_contract:
            return {"success": False, "error": f"Your {tier} facility can only offer {max_contract}-fight deals"}
        base = current.get('purse_per_fight', 5000 + ftr.overall_rating * 100)
        premium = CONTRACT_OPTIONS[contract_fights]["premium"]
        resign_cost = max(5000, int(base * 1.2 * premium * contract_fights * 0.1))

        if self._camp_balance < resign_cost:
            return {"success": False, "error": f"Need ${resign_cost:,}. Have ${self._camp_balance:,}"}

        self._camp_balance -= resign_cost
        self._contracts[fighter_id] = {
            "fighter_id":          fighter_id,
            "camp_id":             self._game_state.player_camp_id,
            "total_fights":        contract_fights,
            "fights_remaining":    contract_fights,
            "fights_completed":    0,
            "purse_per_fight":     int(base * 1.1),
            "morale":              min(100, current.get('morale', 75) + 15),
            "holdout_weeks":       0,
            "is_holdout":          False,
            "signed_week":         self._game_state.week_number,
            # Preserve founding-fighter flag through re-sign so loyalty
            # bonus carries forward across contract renewals.
            "is_founding_fighter": current.get('is_founding_fighter', False),
        }
        self._news_items.insert(0, {
            "headline": f"✅ EXTENDED: {ftr.name} re-signs — {contract_fights}-fight deal (${resign_cost:,})",
            "category": "signing",
            "week": self._game_state.week_number,
        })
        self._clear_cache()
        return {"success": True, "message": f"Re-signed {ftr.name} — {contract_fights}-fight deal"}

    def get_contract_options_for_tier(self, fighter_id: Optional[str] = None) -> List[Dict]:
        """Available contract lengths for the player's current facility tier.

        Optional fighter_id: when provided, founding-fighter contracts can
        unlock longer deals regardless of tier (Ship B loyalty bonus).
        """
        player_camp = self.get_player_camp()
        tier = str(getattr(player_camp, 'tier', 'GARAGE') if player_camp else 'GARAGE').upper()
        max_fights = TIER_CONTRACT_MAX.get(tier, 3)
        if fighter_id:
            _c = self._contracts.get(fighter_id, {})
            if _c.get('is_founding_fighter'):
                max_fights = max(FOUNDING_FIGHTER_MAX_CONTRACT, max_fights)
        return [
            {
                "fights":        n,
                "label":         opts["label"],
                "premium":       opts["premium"],
                "available":     n <= max_fights,
                "locked_reason": f"Upgrade to {opts['min_tier']} to unlock" if n > max_fights else "",
            }
            for n, opts in CONTRACT_OPTIONS.items()
        ]

    def sign_free_agent(self, fighter_id: str,
                        contract_fights: int = 3) -> Dict[str, Any]:
        """Sign a free agent to the player's camp with a fight-based contract."""
        if not self._game_state:
            return {"success": False, "error": "No game loaded"}

        fighter = self._game_state.get_fighter(fighter_id)
        if not fighter:
            return {"success": False, "error": "Fighter not found"}
        if fighter.camp_id:
            return {"success": False, "error": f"{fighter.name} is already signed to a camp"}
        if fighter.fighter_id not in self._game_state.free_agents:
            return {"success": False, "error": f"{fighter.name} is not available"}

        # Validate contract length vs camp tier
        player_camp  = self._game_state.get_camp(self._game_state.player_camp_id)
        tier         = str(getattr(player_camp, 'tier', 'GARAGE') if player_camp else 'GARAGE').upper()
        max_contract = TIER_CONTRACT_MAX.get(tier, 3)
        if contract_fights not in CONTRACT_OPTIONS:
            contract_fights = 3
        if contract_fights > max_contract:
            return {"success": False, "error": f"Your {tier} facility can only offer {max_contract}-fight deals. Upgrade to unlock longer contracts."}

        # Calculate signing cost with contract premium
        premium      = CONTRACT_OPTIONS[contract_fights]["premium"]
        signing_cost = int((5000 + fighter.overall_rating * 300) * premium)
        if self._camp_balance < signing_cost:
            return {"success": False, "error": f"Insufficient funds. Need ${signing_cost:,}, have ${self._camp_balance:,}"}

        max_fighters = self._roster_cap_for_tier(tier)
        roster_size  = len(self._game_state.get_player_fighters())
        if roster_size >= max_fighters:
            return {"success": False, "error": f"Roster full ({roster_size}/{max_fighters}). Upgrade your facility to sign more."}

        self._game_state._sign_fighter_to_camp(fighter_id, self._game_state.player_camp_id)
        self._camp_balance -= signing_cost

        # Store signing OVR for career development summary
        if fighter_id not in self._game_state._fighter_data:
            self._game_state._fighter_data[fighter_id] = {}
        self._game_state._fighter_data[fighter_id]['ovr_at_signing'] = fighter.overall_rating
        self._game_state._fighter_data[fighter_id]['week_signed'] = self._game_state.week_number

        # Create contract record
        self._contracts[fighter_id] = {
            "fighter_id":       fighter_id,
            "camp_id":          self._game_state.player_camp_id,
            "total_fights":     contract_fights,
            "fights_remaining": contract_fights,
            "fights_completed": 0,
            "purse_per_fight":  max(8000, 5000 + fighter.overall_rating * 100),
            "morale":           75,       # Starts happy
            "holdout_weeks":    0,        # Weeks in holdout state
            "is_holdout":       False,
            "signed_week":      self._game_state.week_number,
        }

        self._news_items.insert(0, {
            "headline": f"📝 SIGNED: {fighter.name} — {contract_fights}-fight deal (${signing_cost:,})",
            "category": "signing",
            "week":     self._game_state.week_number,
        })
        self._clear_cache()
        return {"success": True, "message": f"Signed {fighter.name} — {contract_fights}-fight deal for ${signing_cost:,}"}


    # =========================================================================
    # AMATEUR CIRCUIT
    # =========================================================================

    def _get_amateur_system(self):
        """Lazy-init the amateur system."""
        if not hasattr(self, '_amateur_system') or self._amateur_system is None:
            try:
                for _mod in ["amateur", "systems.amateur"]:
                    try:
                        import importlib as _ila
                        _am = _ila.import_module(_mod)
                        self._amateur_system = _am.AmateurSystem()
                        self._amateur_system.initialize_pools()
                        # Schedule year 1 tournaments
                        self._amateur_system.schedule_year_tournaments(
                            year=1, start_week=1
                        )
                        # Fast-forward to current week so loaded games
                        # have a populated amateur circuit immediately
                        current = self.week_number if self.game_started else 0
                        if current > 1:
                            for w in range(1, current):
                                try:
                                    self._amateur_system.process_week(w)
                                except Exception:
                                    pass
                        print(f"✅ Amateur system initialized from {_mod}"
                              f" (fast-forwarded to week {current})")
                        break
                    except (ImportError, AttributeError, Exception) as e:
                        self._amateur_system = None
            except Exception:
                self._amateur_system = None
        return self._amateur_system

    def get_amateur_data(self) -> Dict[str, Any]:
        """Alias for get_amateur_overview — used by the web route."""
        return self.get_amateur_overview()

    def get_amateur_overview(self) -> Dict[str, Any]:
        """
        Return overview data for the amateur circuit browse page.
        Shows regional rankings, upcoming tournaments, and pro-eligible fighters.
        """
        sys = self._get_amateur_system()
        if not sys:
            return {"available": False}

        week = self.week_number

        # Pro-eligible fighters per weight class
        eligible: Dict[str, List[Dict]] = {}
        from amateur import WEIGHT_CLASSES as _AMATEUR_WCS
        for wc in _AMATEUR_WCS:
            try:
                fighters = sys.get_eligible_amateurs(wc)
                # Filter: ceiling must exceed OVR (real growth upside)
                # and ceiling >= 65 (worth a pro contract)
                # Sort by ceiling desc so elite prospects appear first
                prospects = sorted(
                    [f for f in fighters
                     if getattr(f, 'potential_ceiling', 0) > getattr(f, 'overall_rating', 60)
                     and getattr(f, 'potential_ceiling', 0) >= 65],
                    key=lambda f: getattr(f, 'potential_ceiling', 0),
                    reverse=True
                )
                eligible[wc] = [
                    {
                        "id":             f.fighter_id,
                        "name":           f.name,
                        "age":            getattr(f, 'age', 20),
                        "region":         getattr(f, 'region', 'Unknown'),
                        "record":         f"{f.wins}-{f.losses}",
                        "wins":           f.wins,
                        "losses":         f.losses,
                        "overall":        getattr(f, 'overall_rating', 60),
                        "potential":      getattr(f, 'potential_ceiling', 75),
                        "potential_ceiling": getattr(f, 'potential_ceiling', 75),
                        "potential_grade":getattr(f, 'potential_grade', 'Average'),
                        "display_grade":  ceiling_to_display_grade(getattr(f, 'potential_ceiling', 75)),
                        "grade_color":    grade_color(ceiling_to_display_grade(getattr(f, 'potential_ceiling', 75))),
                        "style":          getattr(f, 'fighting_style', 'Balanced'),
                        "nationality":    getattr(f, 'nationality', 'USA'),
                        "tournament_wins":getattr(f, 'tournament_wins', 0),
                        "tournament_finals":getattr(f, 'tournament_finals', 0),
                        "tournament_semis":getattr(f, 'tournament_semis', 0),
                        # Ship A1: extra fields for the redesigned prospect cards
                        "weight_class":   getattr(f, 'weight_class', wc),
                        "eligibility_reason": getattr(f, 'eligibility_reason', ''),
                        "regional_rank":  getattr(f, 'regional_rank', None),
                        "traits":         list(getattr(f, 'traits', []) or []),
                        "weeks_in_amateur": getattr(f, 'weeks_in_amateur', 0),
                        "signing_cost":   self._compute_amateur_signing_cost(f),
                    }
                    for f in prospects[:12]
                ]
            except Exception:
                eligible[wc] = []

        # All active amateurs for Scout tab — not just pro-ready
        all_prospects = []
        try:
            for f in sys.amateurs.values():
                if f.is_active and not f.turned_pro:
                    all_prospects.append({
                        "id":            f.fighter_id,
                        "name":          f.name,
                        "age":           f.age,
                        "weight_class":  f.weight_class,
                        "record":        f"{f.wins}-{f.losses}",
                        "overall":       getattr(f, 'overall_rating', 0),
                        "potential":     getattr(f, 'potential_grade', 'Average'),
                        "style":         getattr(f, 'fighting_style', 'Balanced'),
                        "is_eligible":   f.is_pro_eligible,
                        "weeks_in_amateur": getattr(f, 'weeks_in_amateur', 0),
                        "fights_needed": max(0, 8 - f.total_fights),
                        "weeks_needed":  max(0, 26 - getattr(f, 'weeks_in_amateur', 0)),
                    })
            all_prospects.sort(key=lambda x: (
                -x['is_eligible'],
                x['potential'] == 'Elite' and -1 or
                x['potential'] == 'High' and 0 or 1,
                -x['overall']
            ))
        except Exception:
            all_prospects = []

        # Regional rankings top 5 per division (sample weight classes)
        regional_rankings: Dict[str, List[Dict]] = {}
        for region in ["Americas", "Europe", "Asia", "Pacific"]:
            try:
                rr = sys.rankings.get(region, {})
                top = []
                for wc, rank_obj in list(rr.items()):
                    raw = getattr(rank_obj, 'rankings', [])
                    for i, entry in enumerate(raw[:5]):
                        # Rankings are (fighter_id, score) tuples
                        if isinstance(entry, (list, tuple)) and len(entry) >= 1:
                            fid = entry[0]
                        elif isinstance(entry, str):
                            fid = entry
                        else:
                            fid = getattr(entry, 'fighter_id', None)
                        if not fid:
                            continue
                        f = sys.amateurs.get(fid)
                        if f and f.is_active:
                            top.append({
                                "rank":    i + 1,
                                "name":    f.name,
                                "fighter_id": fid,    # for profile linking
                                "record":  f"{f.wins}-{f.losses}",
                                "wc":           wc,
                                "weight_class": wc,
                                "overall": getattr(f, 'overall_rating', 60),
                                "eligible": f.is_pro_eligible,
                            })
                regional_rankings[region] = top[:10]
            except Exception:
                regional_rankings[region] = []

        # Recent completed tournaments
        recent_tourneys = []
        for t in getattr(sys, 'completed_tournaments', [])[-6:]:
            try:
                champ_id   = getattr(t, 'champion_id', None)
                champ_obj  = sys.amateurs.get(champ_id) if champ_id else None
                champ_name = champ_obj.name if champ_obj else "Unknown"
                recent_tourneys.append({
                    "name":    getattr(t, 'name', 'Tournament'),
                    "region":  getattr(t, 'region', ''),
                    "wc":      getattr(t, 'weight_class', ''),
                    "week":    getattr(t, 'week', 0),
                    "champion":champ_name,
                    "champion_id": champ_id or '',
                })
            except Exception:
                pass

        # Ship A1: top-level counters surfaced for the redesigned page
        _pro_eligible_count = sum(len(v) for v in eligible.values())
        _tournaments_run = len(getattr(sys, 'completed_tournaments', []))
        return {
            "available":         True,
            "eligible":          eligible,
            "all_prospects":     all_prospects,
            "regional_rankings": regional_rankings,
            "recent_tourneys":   recent_tourneys,
            "week":              week,
            "total_amateurs":    len(getattr(sys, 'amateurs', {})),
            "pro_eligible_count": _pro_eligible_count,
            "tournaments_run":   _tournaments_run,
        }

    def _compute_amateur_signing_cost(self, amateur) -> int:
        """Compute signing cost for an amateur fighter. Single source
        of truth — sign_amateur calls this helper."""
        ovr = int(getattr(amateur, 'overall_rating', 60))
        if ovr >= 72:   signing_cost = 80_000
        elif ovr >= 65: signing_cost = 40_000
        elif ovr >= 58: signing_cost = 20_000
        else:           signing_cost = 8_000
        grade = getattr(amateur, 'potential_grade', 'Average')
        if grade == 'Elite': signing_cost = int(signing_cost * 1.5)
        elif grade == 'High': signing_cost = int(signing_cost * 1.2)
        return signing_cost

    def get_amateur_graduates(self) -> List[Dict[str, Any]]:
        """Return fighters signed from the amateur circuit, with their
        current pro record and status — for the graduates tab."""
        if not hasattr(self, '_amateur_graduates'):
            return []
        result = []
        for g in self._amateur_graduates:
            fid = g.get("fighter_id", "")
            fighter = (self._game_state.get_fighter(fid)
                       if self._game_state else None)
            result.append({
                **g,
                "pro_wins":    getattr(fighter, 'wins', 0) if fighter else 0,
                "pro_losses":  getattr(fighter, 'losses', 0) if fighter else 0,
                "is_active":   getattr(fighter, 'is_active', True) if fighter else False,
                "is_champion": getattr(fighter, 'is_champion', False) if fighter else False,
            })
        return result

    def sign_amateur(self, amateur_id: str) -> Dict[str, Any]:
        """Sign a pro-eligible amateur to the player's camp."""
        sys = self._get_amateur_system()
        if not sys:
            return {"success": False, "error": "Amateur system not available"}

        player_camp = self._game_state.get_camp(self._game_state.player_camp_id) if self._game_state else None
        tier        = getattr(player_camp, 'tier', 'GARAGE') if player_camp else 'GARAGE'
        max_f       = self._roster_cap_for_tier(str(tier))
        roster_size = len(self._game_state.get_player_fighters()) if self._game_state else 0

        if roster_size >= max_f:
            return {"success": False, "error": f"Roster full ({roster_size}/{max_f})"}

        try:
            amateur = sys.amateurs.get(amateur_id)
            if not amateur:
                return {"success": False, "error": "Amateur not found"}

            # Single source of truth — same helper used to surface
            # cost on the prospect cards.
            signing_cost = self._compute_amateur_signing_cost(amateur)
            if self._camp_balance < signing_cost:
                return {"success": False,
                        "error": f"Need ${signing_cost:,}, have ${self._camp_balance:,}"}

            # Create FighterRecord in main game
            if self._game_state:
                import uuid
                fid = amateur_id  # Unified ID — amateur identity travels into pro registry
                from core.game_state import FighterRecord
                rec = FighterRecord(
                    fighter_id=fid,
                    name=amateur.name,
                    weight_class=getattr(amateur, 'weight_class', 'Lightweight'),
                    overall_rating=int(getattr(amateur, 'overall_rating', 60)),
                    wins=0,    # Pro record starts fresh per Sherdog model
                    losses=0,  # Amateur W/L stays in amateur_system.amateurs as credential
                    camp_id=self._game_state.player_camp_id,
                    is_active=True,
                    popularity=5,
                )
                self._game_state.fighters[fid] = rec
                self._game_state._fighter_data[fid] = {
                    "id":      fid,
                    "name":    amateur.name,
                    "age":     getattr(amateur, 'age', 20),
                    "country": getattr(amateur, 'nationality', 'USA'),
                    "style":   getattr(amateur, 'fighting_style', 'Balanced'),
                    "traits":  [],
                    "weight_class": getattr(amateur, 'weight_class', 'Lightweight'),
                    "potential": getattr(amateur, 'potential_ceiling', 75),
                        "display_grade": ceiling_to_display_grade(getattr(amateur, 'potential_ceiling', 75)),
                        "grade_color":   grade_color(ceiling_to_display_grade(getattr(amateur, 'potential_ceiling', 75))),
                }
                self._game_state.free_agents.discard(fid)
                self._game_state._sign_fighter_to_camp(fid, self._game_state.player_camp_id)

                # Store signing OVR for career development summary
                if fid not in self._game_state._fighter_data:
                    self._game_state._fighter_data[fid] = {}
                self._game_state._fighter_data[fid]['ovr_at_signing'] = int(getattr(amateur, 'overall_rating', 0))
                self._game_state._fighter_data[fid]['week_signed'] = self._game_state.week_number

            self._camp_balance -= signing_cost

            # Ship A1: track graduate for the "Your Graduates" tab
            if not hasattr(self, '_amateur_graduates'):
                self._amateur_graduates = []
            self._amateur_graduates.append({
                "fighter_id":      amateur_id,
                "fighter_name":    amateur.name,
                "signed_week":     (self._game_state.week_number
                                    if self._game_state else 0),
                "weight_class":    getattr(amateur, 'weight_class', ''),
                "region":          getattr(amateur, 'region', ''),
                "potential_grade": getattr(amateur, 'potential_grade', ''),
            })

            self._news_items.insert(0, {
                "headline": f"📝 SIGNED: {amateur.name} goes pro with your camp (${signing_cost:,})",
                "category": "signing",
                "week":     self.week_number,
            })
            self._clear_cache()
            return {"success": True,
                    "message": f"Signed {amateur.name} for ${signing_cost:,}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================

_bridge_instance: Optional[GameBridge] = None

def get_bridge() -> GameBridge:
    """Get the global GameBridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = GameBridge()
    return _bridge_instance

def reset_bridge() -> None:
    """Reset the GameBridge (for new games)"""
    global _bridge_instance
    _bridge_instance = GameBridge()
