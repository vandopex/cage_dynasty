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
    FIGHT_ENGINE_AVAILABLE      = True
    print("✅ fight engine loaded from fight_integration")
except Exception as _fe_e:
    print(f"⚠️ fight_integration not available: {_fe_e}")
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
        self._fight_offers: List[Dict[str, Any]] = []
        self._completed_events: List[Dict[str, Any]] = []
        self._news_items: List[Dict[str, Any]] = []

        # Negotiation + fight camp state
        self._pending_negotiations: Dict[str, Any] = {}   # neg_id -> negotiation dict
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

        # CardBuilder instance (if available)
        self._card_builder = CardBuilder() if CARD_BUILDER_AVAILABLE else None

        # Aging system — one instance tracks per-fighter processed years
        self._aging_system = AgingSystem() if AGING_AVAILABLE else None

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
            print("Populating world with AI camps and fighters...")
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

            # Store coach data for passive training and advice
            if coach_data:
                self._coach = {
                    "name":      coach_data.get("name",      "Head Coach"),
                    "specialty": coach_data.get("specialty", "boxing").lower(),
                    "rating":    int(coach_data.get("rating", 60)),
                    "salary":    int(coach_data.get("salary", 800)),
                }
                print(f"  ✅ Coach: {self._coach['name']} ({self._coach['specialty']}, {self._coach['rating']} rating)")

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
            "scheduled_fights":         [clean_fight(f) for f in self._scheduled_fights],
            "upcoming_cards":           upcoming_clean,
            "fighter_cooldowns":        self._fighter_cooldowns,
            "fighter_training_plans":   self._fighter_training_plans,
            "fight_camps":              self._fight_camps,
            "week_declines":            self._week_declines,
            "neg_counter":              self._neg_counter,
            "fight_interviews":         self._fight_interviews,
            "watchlist":                self._watchlist,
            "fight_commentary":         {k: v for k, v in self._fight_commentary.items()},
            "title_history":            self._title_history,
            "camp_stat_totals":         self._camp_stat_totals,
            "contracts":                self._contracts,
            "camp_archetypes":          self._camp_archetypes,
            "injury_system":            self._injury_system.to_dict() if self._injury_system else {},
            "champ_weeks_since_defense": self._champ_weeks_since_defense,
            "pending_injury_decisions": self._pending_injury_decisions,
            "champion_holds":           self._champion_holds,
            "fight_offers":             self._fight_offers,
            "completed_events":         [
                {**{k: v for k, v in ev.items() if k != 'fights'},
                 'fights': [clean_fight(f) for f in ev.get('fights', [])]}
                for ev in self._completed_events[-50:]  # Last 50 events
            ],
            "news_items":               self._news_items[-100:],
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
            elif hasattr(result, 'success') and not result.success:
                return {"success": False, "error": "Could not load game world data"}
        except Exception as e:
            print(f"⚠️ CLI load failed: {e} — bridge-only load")

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
        self._scheduled_fights        = data.get("scheduled_fights", [])
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
        self._contracts               = data.get("contracts", {})
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
        self._fight_offers            = data.get("fight_offers", [])
        self._fighter_cooldowns       = {k: int(v) for k, v in
                                          data.get("fighter_cooldowns", {}).items()}

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

        # Restore aging state
        if self._aging_system and "aging_processed" in data:
            self._aging_system._last_processed_year = {
                k: int(v) for k, v in data["aging_processed"].items()
            }

        # Restore pending negotiations (empty on load — in-progress negs don't persist)
        self._pending_negotiations = {}

        self.game_started = True
        self._clear_cache()

        # Re-rank all divisions under current formula. bypass_clamp=True so we
        # converge to the formula's true equilibrium in one pass — saves loaded
        # under an older ranking formula will see DRAMATIC one-time shifts here
        # (e.g., fighters who don't meet the new min-fights threshold drop out
        # entirely). This is intentional, not a bug.
        self._update_all_rankings(bypass_clamp=True)

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
                            "category": "injury",
                            "week": self._game_state.week_number if self._game_state else 1,
                        })
                        continue
                result = self._simulate_fight(fight)
                fight_results.append(result)

                # Group by event name
                ev_name = fight.get("event_name", f"DFC {self._game_state.week_number}")
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
            if ai_event:
                for fight in ai_event.get("fights", []):
                    for fid in [fight.get("winner_id"), fight.get("loser_id")]:
                        if not fid:
                            continue
                        ftr = self._game_state.get_fighter(fid)
                        if ftr:
                            self._apply_cooldown(ftr, current_week,
                                                  getattr(ftr, 'is_champion', False))

            # ── Contract processing — decrement and handle expiry ─────
            self._process_contracts(current_week)

            # ── Top up pipeline — add week N+8 ────────────────────────
            self._top_up_pipeline()

            # ── Injury healing — process one week for all fighters ────
            if INJURY_AVAILABLE and self._injury_system:
                healed = self._injury_system.process_weekly_healing()
                for fid_h, descriptions in healed.items():
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

                        # Slice 2 — book vacant-title fight via shared helper
                        self._book_vacant_title_fight(
                            wc,
                            exclude_fighter_ids={champ.fighter_id} if champ else None,
                        )

            # ── Slice 3: pop expired hold entries on heal ──────────────
            # Champion's recovery ended → pop their hold. Slice 4 will
            # hook here to fire the mandatory return defense + news.
            _heal_now = [fid for fid, entry in self._champion_holds.items()
                         if entry.get("return_week", 0) <= self._game_state.week_number]
            for _fid in _heal_now:
                del self._champion_holds[_fid]
                # Slice 4 will fire mandatory return defense booking here

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
            if len(all_card_fights) >= 2:
                try:
                    if FOTN_AVAILABLE:
                        fotn_result, _ = select_fotn(all_card_fights)
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
                if ai_event:
                    for fr in ai_event.get("fights", []):
                        if fr.get("fight_id") == fotn_fid:
                            fr["is_fotn"] = True
                        else:
                            fr["is_fotn"] = False  # Explicitly clear
                f1n = fotn_result.get("fighter1_name", "")
                f2n = fotn_result.get("fighter2_name", "")
                # Populate event.fotn on the containing event for archive surface
                fotn_dict = {
                    "fight_id":      fotn_fid,
                    "fighter1_name": f1n,
                    "fighter2_name": f2n,
                    "bonus":         FOTN_BONUS,
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
        self._yearly_awards.append({"year": year, "week": week, "awards": awards})

    def _maybe_generate_inbound_offers(self) -> None:
        """
        Promotion occasionally approaches player fighters with fight offers.
        20% chance per idle fighter per week. Opponent is ±3 ranks from player.
        Creates passive pressure — player isn't always the aggressor.
        """
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
            # 20% chance this week
            if random.random() > 0.20:
                continue

            # Find an appropriate opponent: ±3 ranks
            division = self._game_state.divisions.get(pf.weight_class)
            if not division:
                continue

            player_rank = self._get_fighter_rank(pf)
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

            if not candidates:
                continue

            opp = random.choice(candidates)
            opp_rank = self._get_fighter_rank(opp)
            weeks_away = self._weeks_out_for_fight(
                self._get_fighter_rank(pf), opp_rank
            )
            event_week = week + weeks_away
            event_name = f"DFC {event_week}"

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
            }
            self._fight_offers.append(offer)

            self._news_items.insert(0, {
                "headline": f"📨 DFC offers {pf.name} a fight vs {opp.name}"
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
            # Earn nickname on win when threshold crossed (≥2 wins, ≥3 total fights)
            if is_win and not getattr(ftr, 'nickname', None):
                _total_fights = (ftr.wins or 0) + (ftr.losses or 0) + (ftr.draws or 0)
                if ftr.wins >= 2 and _total_fights >= 3:
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
                    _ev = fight.get('event_name', 'DFC')
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
                        _hl = f"🏆 {ftr.name} IS THE NEW CHAMPION — stunning title win at {fight.get('event_name','DFC')}!"
                    elif method in ("KO", "TKO"):
                        _hl = f"💥 {ftr.name} puts the division on notice — {method} finish at {fight.get('event_name','DFC')}"
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
        # Clear camp cache so dashboard shows updated record
        self._camp_cache.clear()

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
        elif method == "SUB":
            winner.sub_wins += 1

        # ── Judges scorecards (decisions only) ──────────────────
        scorecard_data = None
        if method == "DEC" and JUDGES_AVAILABLE:
            try:
                winner_rating = winner.overall_rating
                loser_rating  = loser.overall_rating
                dominance = calculate_dominance_from_fight(winner_rating, loser_rating)
                # fighter1 is always "fighter 1" in generate_decision
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
        UPGRADE_REQS = {
            "LOCAL":    {"wins":3},
            "REGIONAL": {"wins":10},
            "NATIONAL": {"wins":25,"title_wins":1},
            "ELITE":    {"wins":50,"title_wins":3},
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

        # Vacant-title decline → AI #1 vs #2 fallback (Slice 2.5)
        if _declined and _declined.get("source") == "vacant_title":
            _wc = _declined.get("vacant_division")
            if _wc:
                self._book_vacant_title_ai_fallback(_wc)

        return {"success": True, "message": "Offer declined"}

    def _book_vacant_title_ai_fallback(self, wc: str) -> None:
        """Book AI #1 vs #2 vacant-title fight when player declines a Slice 2.5 offer."""
        self._book_vacant_title_fight(wc, decline_context="player declined the shot")

    def _preview_vacant_title_contenders(
        self,
        wc: str,
        exclude_fighter_ids: Optional[Set[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Slice 3 — read-only preview of who'd fight for a vacant title in {wc}.
        Returns dict with top1, top2, target_event_name, target_week, weeks_away,
        or None if booking would not be possible. Idempotent — safe from a route
        render handler. Used by Slice 3's decision page; also used internally by
        _book_vacant_title_fight as the contender filter + card scan."""
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

        if len(_contenders) < 2:
            return None

        _target_card = None
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
            "top2":              _contenders[1],
            "target_event_name": _target_card["event_name"],
            "target_week":       _target_card["week"],
            "weeks_away":        _target_card["week"] - current_week,
        }

    def _book_vacant_title_fight(
        self,
        wc: str,
        exclude_fighter_ids: Optional[Set[str]] = None,
        decline_context: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Slice 2/2.5/3 shared helper — book AI #1 vs #2 for vacant title.
        Used by Slice 2 (auto-vacate), Slice 2.5 fallback (decline), and
        Slice 3 (player vacate handler). Returns booked fight info dict or
        None if booking not possible."""
        preview = self._preview_vacant_title_contenders(wc, exclude_fighter_ids)
        if not preview:
            print(f"  ⚠️ [VACANT TITLE] {wc} — no bookable contender pair; deferred")
            return None

        target_card = self._upcoming_cards.get(preview["target_week"])
        if not target_card:
            return None

        top1, top2 = preview["top1"], preview["top2"]
        fdict = self._make_scheduled_fight(
            top1, top2, wc, preview["target_event_name"],
            preview["target_week"], "main_event", is_title=True,
        )
        target_card["fights"].append(fdict)

        _suffix = f" ({decline_context})" if decline_context else ""
        print(f"  🏆 [VACANT TITLE BOOKED] {wc} — {top1.name} vs {top2.name} "
              f"at {preview['target_event_name']} (Wk {preview['target_week']}){_suffix}")
        _headline_suffix = f" ({decline_context})." if decline_context else "."
        self._news_items.insert(0, {
            "headline": (f"🏆 VACANT TITLE FIGHT: {top1.name} vs {top2.name} "
                         f"for the {wc} belt at {preview['target_event_name']}{_headline_suffix}"),
            "category": "title",
            "week":     self._game_state.week_number,
        })
        return {
            "top1_name":    top1.name,
            "top2_name":    top2.name,
            "target_event": preview["target_event_name"],
            "target_week":  preview["target_week"],
            "fight_id":     fdict.get("fight_id"),
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
            self._book_vacant_title_fight(
                wc, exclude_fighter_ids={fighter_id},
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
            # Seeded variance: ±12 around overall, clamped 20–100
            rng = _rnd.Random(hash(fighter.fighter_id + key) & 0xFFFFFFFF)
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
            record_str=fighter.record,
            overall_rating=ovr,
            potential=int(fdata.get("potential", ovr + 8)),
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

    # Canonical mapping from focus key → which attributes it trains
    # Keys must match what routes.py sends as focus values
    _FOCUS_ATTRS: Dict[str, List[str]] = {
        # Striking
        "boxing":           ["boxing", "striking_defense"],
        "kicks":            ["kicks", "striking_defense"],
        "clinch_striking":  ["clinch_striking", "top_control"],
        "striking_defense": ["striking_defense", "composure"],
        "muay_thai":        ["kicks", "clinch_striking"],
        # Grappling
        "wrestling":        ["takedowns", "takedown_defense"],
        "takedowns":        ["takedowns", "top_control"],
        "takedown_defense": ["takedown_defense", "takedowns"],
        "top_control":      ["top_control", "takedowns"],
        "bjj":              ["submissions", "guard"],
        "submissions":      ["submissions", "guard"],
        "guard":            ["guard", "submissions"],
        # Physical
        "cardio":           ["cardio", "recovery"],
        "strength":         ["strength", "chin"],
        "fight_iq":         ["fight_iq", "composure"],
        # Balanced sparring — small gains across key areas
        "sparring":         ["boxing", "takedown_defense", "fight_iq"],
    }

    # Raw weekly gains per intensity (before cap)
    _INTENSITY_GAIN: Dict[str, int] = {
        "REST": 0, "LIGHT": 1, "MODERATE": 2, "INTENSE": 3, "EXTREME": 4,
    }

    # Soft ceiling per tier — above this, gains diminish but never zero
    _TIER_SOFT_CEIL = {
        "GARAGE":   65,
        "LOCAL":    72,
        "REGIONAL": 80,
        "NATIONAL": 90,
        "ELITE":    100,
    }

    def _diminishing_gain(self, current: float, raw_gain: float,
                           camp_tier: str) -> float:
        """
        Option A: diminishing returns above the tier's soft ceiling.
        Below ceiling → full gain.
        Above ceiling → gain tapers linearly, reaching ~5% at 30pts above.
        Never actually zero — a fighter can always grind, just very slowly.

        Formula:
            overshoot = max(0, current - soft_ceil)
            multiplier = max(0.05, 1 - overshoot / 30)
            effective = raw_gain * multiplier
        """
        soft_ceil = self._TIER_SOFT_CEIL.get(camp_tier.upper(), 65)
        overshoot = max(0.0, current - soft_ceil)
        multiplier = max(0.05, 1.0 - overshoot / 30.0)

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
        focus_attrs   = self._FOCUS_ATTRS.get(focus, ["fight_iq"])

        fatigue_delta = {
            "REST": -15, "LIGHT": 2, "MODERATE": 5, "INTENSE": 10, "EXTREME": 18,
        }.get(intensity_up, 5)

        actual_gains: Dict[str, float] = {}

        if self._game_state and raw_gain > 0:
            fighter = self._game_state.get_fighter(fighter_id)
            if fighter and hasattr(fighter, 'overall_rating'):
                for attr in focus_attrs:
                    current = float(getattr(fighter, attr,
                                            getattr(fighter, 'overall_rating', 65)))
                    effective = self._diminishing_gain(current, raw_gain, camp_tier)

                    # Style affinity — fighters improve faster in their natural discipline
                    _STYLE_AFFINITY = {
                        "Striker":         {"boxing":1.3,"kicks":1.2,"striking_defense":1.2,"takedowns":0.85,"submissions":0.75},
                        "Wrestler":        {"takedowns":1.3,"top_control":1.25,"takedown_defense":1.2,"boxing":0.85,"submissions":0.85},
                        "BJJ Specialist":  {"submissions":1.35,"guard":1.3,"takedowns":1.1,"kicks":0.8},
                        "Muay Thai":       {"kicks":1.35,"clinch_striking":1.3,"boxing":1.1,"takedowns":0.85},
                        "Pressure Fighter":{"cardio":1.2,"boxing":1.15,"clinch_striking":1.1},
                        "Counter Striker": {"striking_defense":1.3,"fight_iq":1.2,"boxing":1.1},
                        "Ground & Pound":  {"top_control":1.3,"takedowns":1.2,"boxing":1.1,"submissions":0.8},
                        "Clinch Fighter":  {"clinch_striking":1.35,"top_control":1.2,"takedowns":1.1},
                        "Grappler":        {"takedowns":1.3,"submissions":1.25,"top_control":1.2,"guard":1.15},
                        "Brawler":         {"boxing":1.25,"chin":1.2,"heart":1.15,"striking_defense":0.85},
                    }
                    _style = getattr(fighter, 'fighting_style', '') or ''
                    _affinity = _STYLE_AFFINITY.get(_style, {}).get(attr, 1.0)
                    effective = effective * _affinity

                    actual_gains[attr] = round(effective, 2)
                    if hasattr(fighter, attr):
                        setattr(fighter, attr,
                                min(100.0, current + effective))

                fatigue = max(0, min(100,
                    getattr(fighter, 'fatigue', 0) + fatigue_delta))
                if hasattr(fighter, 'fatigue'):
                    fighter.fatigue = fatigue

                # Recalculate overall_rating from all trainable stats
                _TRAINABLE = [
                    "strength","speed","cardio","chin","recovery",
                    "boxing","kicks","clinch_striking","striking_defense",
                    "takedowns","takedown_defense","top_control","submissions","guard",
                    "heart","fight_iq","composure",
                ]
                stat_vals = [getattr(fighter, a, 0) for a in _TRAINABLE
                             if hasattr(fighter, a)]
                if stat_vals:
                    fighter.overall_rating = int(sum(stat_vals) / len(stat_vals))
            else:
                for attr in focus_attrs:
                    actual_gains[attr] = float(raw_gain)
        else:
            for attr in focus_attrs:
                actual_gains[attr] = 0.0

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

        coach_specialty = self._coach.get("specialty", "boxing")
        coach_rating    = self._coach.get("rating", 60)

        passive_gain = max(0.1, (coach_rating - 50) / 25)  # Floor 0.1 at 50-rated, ~1.8 at 95-rated

        # Four coach archetypes — S&C merged, Head Coach is MMA/strategy
        # Striking Coach:  boxing, kicks, clinch, defense
        # Grappling Coach: wrestling, BJJ, submissions, guard
        # S&C Coach:       strength, cardio, chin, recovery (physical base)
        # Head Coach/MMA:  fight_iq, composure, heart (invisible stats)
        SPECIALTY_MAP = {
            # Striking
            "striking": "striking_coach",    "boxing":   "striking_coach",
            "kickboxing": "striking_coach",  "muay thai": "striking_coach",
            "muay_thai":  "striking_coach",
            # Grappling
            "wrestling":   "grappling_coach", "grappling": "grappling_coach",
            "bjj":         "grappling_coach", "submissions": "grappling_coach",
            # S&C (merged strength + conditioning)
            "s&c":         "sc_coach",        "strength":    "sc_coach",
            "conditioning": "sc_coach",       "cardio":      "sc_coach",
            "s and c":     "sc_coach",
            # Head Coach / MMA
            "mma":         "mma_coach",       "head coach":  "mma_coach",
            "cornering":   "mma_coach",       "strategy":    "mma_coach",
        }
        coach_focus = SPECIALTY_MAP.get(coach_specialty.lower(), "mma_coach")

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

            # Passive coach gains — each archetype trains a group of stats
            # Gain split across the group (not just first attr)
            _COACH_ATTRS = {
                "striking_coach":  ["boxing", "kicks", "clinch_striking", "striking_defense"],
                "grappling_coach": ["takedowns", "takedown_defense", "submissions", "guard"],
                "sc_coach":        ["strength", "cardio", "chin", "recovery"],
                "mma_coach":       ["fight_iq", "composure", "heart"],
            }
            coach_attrs = _COACH_ATTRS.get(coach_focus, ["fight_iq"])
            # Split passive gain across attrs — smaller per stat but broader
            per_attr_gain = passive_gain / len(coach_attrs)
            real_fighter = self._game_state.get_fighter(fid)
            if real_fighter and per_attr_gain > 0:
                for attr in coach_attrs:
                    current = float(getattr(real_fighter, attr,
                                    getattr(real_fighter, 'overall_rating', 50)))
                    effective = self._diminishing_gain(current, per_attr_gain, camp_tier)
                    if hasattr(real_fighter, attr) and effective > 0.01:
                        setattr(real_fighter, attr, min(100.0, current + effective))
                        if result.get("actual_gains") is not None:
                            result["actual_gains"][f"{attr} (coach)"] = round(effective, 2)

                    _TRAINABLE = [
                        "strength","speed","cardio","chin","recovery",
                        "boxing","kicks","clinch_striking","striking_defense",
                        "takedowns","takedown_defense","top_control","submissions","guard",
                        "heart","fight_iq","composure",
                    ]
                    stat_vals = [getattr(real_fighter, a, 0) for a in _TRAINABLE
                                 if hasattr(real_fighter, a)]
                    if stat_vals:
                        real_fighter.overall_rating = int(sum(stat_vals) / len(stat_vals))

            ovr_after = getattr(self._game_state.get_fighter(fid), 'overall_rating', ovr_before)

            # ── Terminal: player training report ──────────────────────
            _ptype = "FIGHT CAMP" if fight_plan else "WEEKLY PLAN"
            _ag    = result.get("actual_gains") or {}
            _main  = {k: v for k, v in _ag.items() if not k.endswith("(coach)")}
            _cch   = {k: v for k, v in _ag.items() if k.endswith("(coach)")}
            _m_str = ", ".join(f"{k}+{v:.1f}" for k, v in list(_main.items())[:3] if v)
            _c_str = ", ".join(f"{k.replace(' (coach)','')}+{v:.1f}" for k, v in list(_cch.items())[:2] if v)
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
                if "(coach)" not in stat and gain > 0.05:
                    self._camp_stat_totals[fid][stat] = (
                        self._camp_stat_totals[fid].get(stat, 0.0) + float(gain)
                    )

            report[fid] = {
                "name":          fighter.name if hasattr(fighter, 'name') else fid,
                "focus":         active_plan["focus"].replace("_", " ").title(),
                "intensity":     active_plan["intensity"],
                "gains":         {k: v for k, v in result.get("actual_gains", {}).items() if v > 0.05},
                "camp_totals":   dict(self._camp_stat_totals.get(fid, {})),
                "ovr_before":    ovr_before,
                "ovr_after":     ovr_after,
                "ovr_delta":     ovr_after - ovr_before,
                "is_fight_camp": bool(fight_plan),
                "capped_stats":  result.get("capped_stats", []),
            }

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
            focus_label = focus.replace("_", " ").title()
            intensity_emoji = {
                "REST": "😴", "LIGHT": "🚶", "MODERATE": "🏃",
                "INTENSE": "🔥", "EXTREME": "⚡"
            }.get(intensity.upper(), "🏋️")

            # Fatigue color
            if fatigue > 65:
                fatigue_color = "var(--blood-red)"
                fatigue_label = f"Fatigued ({fatigue}%)"
            elif fatigue > 40:
                fatigue_color = "var(--warning)"
                fatigue_label = f"Tired ({fatigue}%)"
            elif fatigue < 20:
                fatigue_color = "var(--neon-green)"
                fatigue_label = f"Fresh ({fatigue}%)"
            else:
                fatigue_color = "var(--text-muted)"
                fatigue_label = f"Ready ({fatigue}%)"

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
        total_weekly  = overhead + roster_size * fighter_cost
        balance       = self._camp_balance
        return {
            "balance":              balance,
            "weekly_overhead":      total_weekly,
            "camp_overhead":        overhead,
            "fighter_costs":        roster_size * fighter_cost,
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
        total        = overhead + roster * fighter_cost
        self._camp_balance     = max(0, self._camp_balance - total)
        self._total_overhead_paid += total
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
                        "choices": self._WINNER_CHOICES, "event_name": event.get("event_name", "")})
                    added = True
                if lid in player_ids and not iv.get("loser_done"):
                    pending.append({"fight_id": fid, "fighter_id": lid,
                        "fighter_name": fight.get("loser_name", ""),
                        "opponent_id": wid, "opponent_name": fight.get("winner_name", ""),
                        "role": "loser", "method": fight.get("method", ""),
                        "choices": self._LOSER_CHOICES, "event_name": event.get("event_name", "")})
                    added = True
                if added:
                    seen_fids.add(fid)
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
                self._news_items.append({
                    "headline": f"📉 {decay.fighter_name}'s {_stat_display} getting rusty "
                                f"(-{decay.amount}) — get them in the gym!",
                    "category": "training",
                    "week":     week,
                })

            # Warnings — only show severe ones so feed isn't flooded
            for warn in warnings:
                if warn.weeks_until_decay <= 1:
                    self._news_items.append({
                        "headline": f"⚠️ {warn.fighter_name}'s {warn.stat} "
                                    f"will decay next week without training",
                        "category": "training",
                        "week":     week,
                    })

            # ── Terminal: maintenance summary ──────────────────────────
            if boosts or decays:
                b_str = ", ".join(f"{getattr(b,'fighter_name','?')[:8]} {getattr(b,'stat','?')}+{getattr(b,'amount',0):.1f}" for b in boosts[:3])
                d_str = ", ".join(f"{getattr(d,'fighter_name','?')[:8]} {getattr(d,'stat','?')}-{getattr(d,'amount',0):.1f}" for d in decays[:3])
                print(f"  🔧 [MAINTENANCE] Boosts: {b_str or 'none'} | Decays: {d_str or 'none'}")

        except Exception as e:
            print(f"  ⚠️ [MAINTENANCE] Failed: {e}")

        # ── AI Camp Coaching — passive gains every 4 weeks ────────────
        # AI fighters develop over time via their camp's coaching specialty.
        # Runs every 4 weeks to keep world sim light but meaningful.
        if week % 4 == 0:
            self._advance_ai_fighter_training(week)

    def _advance_ai_fighter_training(self, week: int) -> None:
        """
        Apply passive training gains to all AI fighters every 4 weeks.
        Each camp's coach has a specialty — that stat gets a small boost.
        Young fighters (under 27) gain more; veterans (33+) gain less.
        Reflects the reality that AI camp fighters are also developing.
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

                # Age modifier: young fighters improve faster
                if age < 24:
                    gain = 0.8
                elif age < 28:
                    gain = 0.5
                elif age < 33:
                    gain = 0.3
                else:
                    gain = 0.1  # Veterans plateau

                current = float(getattr(fighter, focus_attr, 60))
                # Diminishing returns above tier cap
                if current >= tier_cap:
                    gain *= max(0.1, 1 - (current - tier_cap) * 0.1)

                if gain > 0.05 and hasattr(fighter, focus_attr):
                    setattr(fighter, focus_attr,
                            min(100.0, current + gain))

                    # Recalculate OVR
                    _TRAINABLE = [
                        "strength","speed","cardio","chin","recovery",
                        "boxing","kicks","clinch_striking","striking_defense",
                        "takedowns","takedown_defense","top_control","submissions","guard",
                        "heart","fight_iq","composure",
                    ]
                    vals = [getattr(fighter, a, 0) for a in _TRAINABLE if hasattr(fighter, a)]
                    if vals:
                        fighter.overall_rating = int(sum(vals) / len(vals))

        # Sample output every 4 weeks to show AI is developing
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
        ai_rank     = self._get_fighter_rank(ai_fighter)
        weeks_out   = self._weeks_out_for_fight(player_rank, ai_rank)

        # Purse from rank, not rating — mirrors real MMA pay structure
        RANK_PURSES = {
            0:  150_000,   # Champion
            1:   80_000,   # #1 contender
            2:   65_000,   # #2
            3:   55_000,
            4:   45_000,
            5:   38_000,   # Top 5
            6:   30_000,
            7:   25_000,
            8:   22_000,
            9:   20_000,
            10:  18_000,   # Top 10
            11:  16_000,
            12:  14_000,
            13:  13_000,
            14:  12_000,
            15:  11_000,   # Bottom ranked
        }
        p_purse = RANK_PURSES.get(player_rank, 9_000) if player_rank is not None else 9_000
        a_purse = RANK_PURSES.get(ai_rank,     9_000) if ai_rank     is not None else 9_000
        base_purse = (p_purse + a_purse) // 2

        self._neg_counter += 1
        neg_id = f"neg_{self._neg_counter}_{player_fighter_id[:6]}"

        pf_name = getattr(player_fighter, 'name', player_fighter_id)
        af_name = getattr(ai_fighter, 'name', target_fighter_id)

        neg = {
            "neg_id": neg_id,
            "player_fighter_id":   player_fighter_id,
            "player_fighter_name": pf_name,
            "ai_fighter_id":       target_fighter_id,
            "ai_fighter_name":     af_name,
            "ai_fighter_record":   f"{ai_fighter.wins}-{ai_fighter.losses}",
            "ai_fighter_rating":   ai_fighter.overall_rating,
            "ai_fighter_rank":     ai_rank,
            "ai_personality":      self._get_ai_neg_personality(ai_fighter),
            "weight_class":        player_fighter.weight_class if isinstance(player_fighter.weight_class, str) else str(player_fighter.weight_class),
            "base_purse":          base_purse,
            "current_purse":       base_purse,
            "weeks_out":           weeks_out,
            "exchange_count":      0,
            "status":              "AWAITING_AI",
            "history":             [],
            "event_name":          f"DFC {self._game_state.week_number + weeks_out}",
        }

        # Immediately resolve AI's first move
        neg["exchange_count"] = 1
        ai_resp = self._generate_ai_counter(neg)
        neg["ai_last_response"] = ai_resp

        if ai_resp["decision"] == "ACCEPT":
            neg["status"] = "AI_ACCEPTED"
        elif ai_resp["decision"] == "COUNTER":
            neg["status"] = "AI_COUNTERED"
            if ai_resp["counter_purse"]:
                neg["current_purse"] = ai_resp["counter_purse"]
        else:
            neg["status"] = "AI_DECLINED"
            # Record decline — this fighter can't be challenged again this week
            if self._game_state:
                self._week_declines[target_fighter_id] = self._game_state.week_number

        neg["history"].append({
            "by": "AI",
            "decision": ai_resp["decision"],
            "message":  ai_resp.get("message"),
            "purse":    neg["current_purse"],
        })

        self._pending_negotiations[neg_id] = neg
        return {"success": True, "neg_id": neg_id}

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
                            "boxing": wf.boxing, "kicks": wf.kicks,
                            "wrestling": wf.takedowns, "bjj": wf.submissions,
                            "chin": wf.chin, "cardio": wf.cardio,
                            "strength": wf.strength, "speed": wf.speed,
                            "fight_iq": wf.fight_iq,
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
            "existing_gameplan": existing.get("gameplan",        "BALANCED"),
            "existing_focus":    existing.get("training_focus",  "boxing"),
            "existing_intensity":existing.get("intensity",       "MODERATE"),
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

        fighters.sort(key=rank_score, reverse=True)

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

            # Use real engine or fallback
            if FIGHT_ENGINE_AVAILABLE:
                try:
                    fa1  = self._make_fighter_attrs(f1, f1.name, f1.fighter_id)
                    fa2  = self._make_fighter_attrs(f2, f2.name, f2.fighter_id)
                    _slot = fight.get("card_slot", "prelim")
                    _rnds = 5 if (fight.get("is_title_fight") or _slot in ("main_event","co_main")) else 3
                    _eng = _simulate_narrated_fight_fn(fa1, fa2, rounds=_rnds)
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

            pre_w = pre_rank_snapshot.get(winner.fighter_id)
            pre_l = pre_rank_snapshot.get(loser.fighter_id)

            winner.wins += 1; loser.losses += 1
            if method in ("KO","TKO"): winner.ko_wins += 1
            elif method == "SUB":       winner.sub_wins += 1
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
            if event["main_event"] is None or fight.get("card_slot") == "main_event":
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
            print(f"  📊 [{event.get('event_name','DFC')}] {_total} fights "
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
        event_name = f"DFC {week}"
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
            if FIGHT_ENGINE_AVAILABLE:
                try:
                    # Use real engine — no commentary stored for AI fights
                    fa1 = self._make_fighter_attrs(f1, f1.name, f1.fighter_id)
                    fa2 = self._make_fighter_attrs(f2, f2.name, f2.fighter_id)
                    _rnds = 5 if is_title else 3
                    _eng = _simulate_narrated_fight_fn(fa1, fa2, rounds=_rnds)
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

            # Snapshot ranks BEFORE record update
            pre_w_rank = self._get_fighter_rank(winner)
            pre_l_rank = self._get_fighter_rank(loser)

            # Update records
            winner.wins   += 1
            loser.losses  += 1
            if method in ("KO", "TKO"):
                winner.ko_wins  += 1
            elif method == "SUB":
                winner.sub_wins += 1
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
            if event["main_event"] is None:
                event["main_event"] = fight_result

            # Notable finishes → news
            if method in ("KO", "TKO", "SUB"):
                icon = "💥" if method in ("KO", "TKO") else "🔒"
                self._news_items.append({
                    "headline":  f"{icon} {winner.name} def. {loser.name} by {method} (R{rnd}) at {event_name}",
                    "category":  "fight",
                    "week":      week,
                    "winner_id": winner.fighter_id,
                    "loser_id":  loser.fighter_id,
                })

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

    def _cooldown_weeks(self, fighter, is_champion: bool = False) -> int:
        """
        Cooldown = pure recovery time before a fighter can SIGN another fight.
        The fight itself is then scheduled 3-12 weeks out (handled by _weeks_out_for_fight).

        Philosophy: fighters sign contracts while hot. Cooldown is just
        physical/promotional recovery — not the full gap between fights.

        Real cadence this produces:
          Unranked winner:   1w cooldown + 3-5w camp  = ~4-6w fight-to-fight
          Ranked winner:     2w cooldown + 5-8w camp  = ~7-10w fight-to-fight
          Top 5 winner:      2w cooldown + 8-10w camp = ~10-12w fight-to-fight
          Champion defense:  4w cooldown + 10-12w camp = ~14-16w fight-to-fight
          Loser (1 loss):    4w cooldown + 3-5w camp  = ~7-9w fight-to-fight
          Loser (streak):    up to 8w cooldown — taking L's, need time to reset
        """
        lose_streak = self._get_fighter_lose_streak(fighter)
        rank = self._get_fighter_rank(fighter)

        if is_champion:
            return 4  # Champion can sign defence within a month

        if lose_streak == 0:
            # Winner — minimal cooldown, can sign fast
            if rank is not None and rank <= 5:
                return 2   # Top contenders recover quick, high demand
            elif rank is not None and rank <= 10:
                return 2   # Mid-ranked, ready in 2 weeks
            elif rank is not None:
                return 1   # Lower ranked, hungry for next fight
            else:
                return 1   # Unranked prospects fight frequently

        # Loser — needs more time, especially on streaks
        base = 4
        return min(8, base + (lose_streak - 1) * 2)

    def _apply_cooldown(self, fighter, week: int, is_champion: bool = False) -> None:
        """Record when this fighter is next available."""
        cooldown = self._cooldown_weeks(fighter, is_champion)
        self._fighter_cooldowns[fighter.fighter_id] = week + cooldown

    def _is_available(self, fighter_id: str, week: int) -> bool:
        """True if fighter has no cooldown blocking them this week."""
        return self._fighter_cooldowns.get(fighter_id, 0) <= week

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
                           f1=None, f2=None) -> str:
        """Return slot string for a fight."""
        if not CARD_BUILDER_AVAILABLE:
            return "prelim"

        # Contender floor: only inflate slot when BOTH fighters are
        # credibly title-eligible. A high-ranked fighter vs an unproven
        # opponent (e.g. rookie) must NOT inflate — falls back to whatever
        # card_builder.assign_slot decides on score alone.
        ranks = [r for r in [f1_rank, f2_rank] if r is not None]
        top_rank = min(ranks) if ranks else None
        min_slot = None

        matchup_credible = False
        if MATCHMAKING_AVAILABLE and f1 is not None and f2 is not None:
            f1_eligible = is_title_eligible(
                f1.wins, f1.losses, f1_rank,
                getattr(f1, 'is_champion', False),
            )
            f2_eligible = is_title_eligible(
                f2.wins, f2.losses, f2_rank,
                getattr(f2, 'is_champion', False),
            )
            matchup_credible = f1_eligible and f2_eligible

        if top_rank is not None and matchup_credible:
            if top_rank <= 1:
                score = max(score, SCORE_THRESHOLDS[CardSlot.MAIN_EVENT] + 1)
                min_slot = CardSlot.CO_MAIN
            elif top_rank <= 3:
                score = max(score, SCORE_THRESHOLDS[CardSlot.CO_MAIN] + 1)
                min_slot = CardSlot.MAIN_CARD
            elif top_rank <= 6:
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

    def _build_card_for_week(self, target_week: int) -> Dict[str, Any]:
        """
        Build a full DFC card for target_week.
        - 12 fights, structured by card slot
        - Ranked vs ranked preferred
        - Cooldowns respected
        - Player's booked fights inserted automatically
        """
        import random

        event_name = f"DFC {target_week}"
        event_id   = f"event_{target_week}"

        card: Dict[str, Any] = {
            "event_id":    event_id,
            "event_name":  event_name,
            "week":        target_week,
            "fights":      [],      # pre-scheduled fight dicts
            "is_ai_event": True,
        }

        if not self._game_state:
            return card

        if CARD_BUILDER_AVAILABLE:
            self._card_builder.get_or_create_card_state(event_name, target_week)

        # Collect already-booked fighter IDs for this week
        booked_here = set()
        # Check if player has a fight on this card
        for sf in self._scheduled_fights:
            if sf.get("week") == target_week or                (self._game_state and
                self._game_state.week_number + sf.get("weeks_until", 0) == target_week):
                booked_here.add(sf.get("fighter1_id",""))
                booked_here.add(sf.get("fighter2_id",""))
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
        # Each fighter should appear on at most one upcoming card
        all_booked = set()
        for sf in self._scheduled_fights:
            all_booked.add(sf.get("fighter1_id",""))
            all_booked.add(sf.get("fighter2_id",""))
        for wk, existing_card in self._upcoming_cards.items():
            if wk == target_week:
                continue
            for f in existing_card.get("fights", []):
                all_booked.add(f.get("fighter1_id",""))
                all_booked.add(f.get("fighter2_id",""))

        player_camp_id = self._game_state.player_camp_id
        target_count   = 9

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
                    candidates.append((score, champ, top, wc, True))
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
                    candidates.append((best_pair_score, best_pair[0], best_pair[1], wc, False))

            elif len(ranked_avail) == 1 and len(available) >= 2:
                ranked_f = ranked_avail[0]
                r = self._get_fighter_rank(ranked_f)
                if r is not None and r >= 6:
                    unranked_pool = [f for f in available if f.fighter_id not in ranked_ids]
                    if unranked_pool:
                        opp = random.choice(unranked_pool)
                        score = self._matchup_score(ranked_f, opp)
                        candidates.append((score, ranked_f, opp, wc, False))

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
                    candidates.append((score_u, f1_u, f2_u, wc, False))
                    break  # One unranked fight per division

        # ── Sort candidates by score descending ───────────────────────────
        candidates.sort(key=lambda x: x[0], reverse=True)

        # ── Cap title fights: max 2 per card, must be different divisions ──
        title_count = 0
        title_divisions_used = set()
        capped = []
        for c in candidates:
            score_c, f1_c, f2_c, wc_c, is_title_c = c
            if is_title_c:
                if title_count < 2 and wc_c not in title_divisions_used:
                    capped.append(c)
                    title_count += 1
                    title_divisions_used.add(wc_c)
                # else: same division already has a title fight, or card is full
                # These fighters get re-scheduled next pipeline build
            else:
                capped.append(c)
        candidates = capped

        # ── Fill card slots top-to-bottom ─────────────────────────────────
        used_in_candidates = set()
        co_main_used = 0   # Track co-main slot usage for floor management
        for score, f1, f2, wc, is_title in candidates:
            if len(card["fights"]) >= target_count:
                break
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

            slot = self._assign_card_slot(
                event_name, score, is_title,
                f1.overall_rating + f2.overall_rating,
                f1_rank=override_f1, f2_rank=override_f2,
                f1=f1, f2=f2,
            )
            if slot in ("co_main", "main_event"):
                co_main_used += 1

            fight_dict = self._make_scheduled_fight(
                f1, f2, wc, event_name, target_week, slot, is_title=is_title)
            card["fights"].append(fight_dict)
            used_in_candidates.add(f1.fighter_id)
            used_in_candidates.add(f2.fighter_id)
            all_booked.add(f1.fighter_id)
            all_booked.add(f2.fighter_id)

        # ── Terminal summary — one line per card ──────────────────────────
        slot_icons = {"main_event":"🏆","co_main":"⭐","main_card":"🥊","prelim":"📋","early_prelim":"📋"}
        def _rank_str(r): return "#C" if r == 0 else f"#{r}" if r is not None else "UR"
        summary_parts = []
        for f in sorted(card["fights"], key=lambda x: {"main_event":0,"co_main":1,"main_card":2,"prelim":3,"early_prelim":4}.get(x.get("card_slot","prelim"),3)):
            icon = slot_icons.get(f.get("card_slot","prelim"), "📋")
            title_tag = "🏆" if f.get("is_title_fight") else ""
            r1_raw = self._get_fighter_rank(self._game_state.get_fighter(f['fighter1_id'])) if self._game_state and self._game_state.get_fighter(f.get('fighter1_id','')) else None
            r2_raw = self._get_fighter_rank(self._game_state.get_fighter(f['fighter2_id'])) if self._game_state and self._game_state.get_fighter(f.get('fighter2_id','')) else None
            r1 = _rank_str(r1_raw)
            r2 = _rank_str(r2_raw)
            summary_parts.append(f"{icon}{title_tag}{f['fighter1_name']}{r1} vs {f['fighter2_name']}{r2}")
        print(f"📅 {event_name} (Wk {target_week}) — {len(card['fights'])} fights:")
        for part in summary_parts:
            print(f"   {part}")

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

        print(f"✅ Card pipeline initialized: DFC {current+1} – DFC {current+num_cards}")

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
        event_name = f"DFC {target_week}"
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

        # Print card summary
        slot_icons = {"main_event":"🏆","co_main":"⭐","main_card":"🥊",
                      "prelim":"📋","early_prelim":"📋"}
        slot_order = {"main_event":0,"co_main":1,"main_card":2,"prelim":3,"early_prelim":4}
        print(f"📅 {event_name} (Wk {target_week}) — {len(card['fights'])} fights:")
        for f in sorted(card["fights"],
                        key=lambda x: slot_order.get(x.get("card_slot","prelim"),3)):
            icon = slot_icons.get(f.get("card_slot","prelim"),"📋")
            title_tag = "🏆" if f.get("is_title_fight") else ""
            ftr1 = self._game_state.get_fighter(f["fighter1_id"])
            ftr2 = self._game_state.get_fighter(f["fighter2_id"])
            r1 = self._get_fighter_rank(ftr1) if ftr1 else None
            r2 = self._get_fighter_rank(ftr2) if ftr2 else None
            rs1 = f"#{r1}" if r1 is not None else "UR"
            rs2 = f"#{r2}" if r2 is not None else "UR"
            print(f"   {icon}{title_tag} {f['fighter1_name']}{rs1} vs "
                  f"{f['fighter2_name']}{rs2}")
        return card

    def _top_up_pipeline(self) -> None:
        """
        Fill all missing weeks up to current+6. Called each advance_week.
        Pre-init only builds 3 cards — this fills weeks 4-6 organically
        on the first advance, then maintains a 6-week lookahead forever.
        """
        if not self._game_state:
            return
        current = self._game_state.week_number
        for w in range(current + 1, current + 7):
            if w not in self._upcoming_cards:
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
            return fight.get("event_name", "DFC ?")

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

        is_title = fight.get("is_title_fight", False)
        is_main  = fight.get("card_slot") in ("main_event", "co_main")
        total_rounds = 5 if (is_title or fight.get("card_slot") == "main_event" or fight.get("card_slot") == "co_main") else 3

        # Style matchup modifier (-0.05 to +0.05)
        style_mod = 0.0
        if STYLES_AVAILABLE:
            try:
                _STYLE_STR_MAP = {
                    "Striker": "STRIKER", "Counter Striker": "COUNTER_STRIKER",
                    "Pressure Fighter": "PRESSURE_FIGHTER", "Point Fighter": "POINT_FIGHTER",
                    "Muay Thai": "MUAY_THAI", "Wrestler": "WRESTLER",
                    "Ground & Pound": "GROUND_AND_POUND", "BJJ Specialist": "BJJ_SPECIALIST",
                    "Clinch Fighter": "CLINCH_FIGHTER", "Sprawl & Brawl": "SPRAWL_AND_BRAWL",
                    "Balanced": "BALANCED",
                }
                s1 = self._game_state._fighter_data.get(f1_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
                s2 = self._game_state._fighter_data.get(f2_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
                fs1 = _FightingStyleEnum(_STYLE_STR_MAP.get(s1, 'BALANCED'))
                fs2 = _FightingStyleEnum(_STYLE_STR_MAP.get(s2, 'BALANCED'))
                style_mod = get_style_matchup_modifier(fs1, fs2)
            except Exception:
                pass

        eng_result: _NarratedFightResult = _simulate_narrated_fight_fn(
            fa1, fa2,
            rounds        = total_rounds,
            is_title_fight= is_title,
            is_main_event = is_main,
        )

        # Translate engine result → our dict format
        import random as _rnd2
        raw_winner_f1 = (eng_result.winner_id == "fighter_1" or eng_result.winner_id == f1_id)
        if style_mod != 0.0 and abs(style_mod) >= 0.02:
            flip_chance = abs(style_mod) * 0.4
            if _rnd2.random() < flip_chance:
                raw_winner_f1 = True if style_mod > 0 else False
        winner_id  = f1_id if raw_winner_f1 else f2_id
        loser_id   = f2_id if winner_id == f1_id else f1_id
        winner_num = 1 if winner_id == f1_id else 2

        winner = fighter1 if winner_id == f1_id else fighter2
        loser  = fighter2 if winner_id == f1_id else fighter1

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

        # Update records
        winner.wins  += 1; loser.losses += 1
        if method in ("KO", "TKO"): winner.ko_wins  += 1
        elif method in ("SUB",):     winner.sub_wins += 1
        self._apply_post_fight_camp_record(winner, loser, fight, method)

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
                dec = generate_decision(
                    winner_dominance=dominance,
                    total_rounds=round_finished,
                    is_title_fight=is_title_fight,
                    fighter1_name=f1_name,
                    fighter2_name=f2_name,
                )
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
            "winner_name":    winner.name,
            "winner_num":     winner_num,
            "loser_id":       loser_id,
            "loser_name":     loser.name,
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

            history = getattr(ftr, 'fight_history', []) or []

            # Decrement if they fought this week
            if history and isinstance(history[-1], dict):
                if history[-1].get('week') == current_week:
                    contract['fights_completed'] = contract.get('fights_completed', 0) + 1
                    contract['fights_remaining'] = max(0,
                        contract['total_fights'] - contract['fights_completed'])
                    # Morale: win = +8, loss compounds with streak
                    last_result = history[-1].get('result', '')
                    ls = getattr(ftr, 'lose_streak', 0) or 0
                    if last_result == 'W':
                        contract['morale'] = min(100, contract.get('morale', 75) + 8)
                    elif last_result == 'L':
                        contract['morale'] = max(0,
                            contract.get('morale', 75) - (10 + ls * 3))
            else:
                # Inactivity morale decay — 2 pts/week after 10 inactive weeks
                last_fight_week = history[-1].get('week', 0) if history and isinstance(history[-1], dict) else 0
                if current_week - last_fight_week >= 10:
                    contract['morale'] = max(0, contract.get('morale', 75) - 2)

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

            # Contract expired → holdout
            if fights_remaining <= 0:
                if contract.get('is_holdout'):
                    hw = contract.get('holdout_weeks', 0) + 1
                    contract['holdout_weeks'] = hw
                    if hw >= HOLDOUT_WINDOW:
                        self._release_fighter_to_free_agency(fid, ftr.name, 'contract expired')
                        continue
                    else:
                        remaining = HOLDOUT_WINDOW - hw
                        self._news_items.insert(0, {
                            "headline": f"⚠️ {ftr.name} in holdout — re-sign within {remaining}w or lose them",
                            "category": "contract",
                            "week": current_week,
                        })
                else:
                    contract['is_holdout'] = True
                    contract['holdout_weeks'] = 0
                    self._news_items.insert(0, {
                        "headline": f"📋 {ftr.name}'s contract expired — {HOLDOUT_WINDOW} weeks to re-sign",
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
        self._contracts.pop(fighter_id, None)
        reason_str = "contract expired" if reason == 'contract expired' else "unhappy with camp"
        self._news_items.insert(0, {
            "headline": f"🚪 {name} has left your camp ({reason_str}) — now a free agent",
            "category": "contract",
            "week": self._game_state.week_number,
        })
        print(f"  🚪 [CONTRACT] {name} left — {reason_str}")

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
        # Filter: only post news for established signings (≥70 OVR or has fight history).
        # Suppresses spam from world-init churn now that fighter_count is correctly tracked.
        _has_fights = bool(getattr(fighter, 'fight_history', []) or [])
        _ovr = getattr(fighter, 'overall_rating', 0) or 0
        if _ovr >= 70 or _has_fights:
            _style = getattr(fighter, 'fighting_style', 'Balanced')
            self._news_items.insert(0, {
                "headline": f"{arch_emoji} {fighter.name} signs with {winning_camp.name} — {_style}, OVR {_ovr}",
                "category": "signing",
                "week": self._game_state.week_number,
            })
        print(f"  {arch_emoji} [AI SIGNING] {fighter.name} → {winning_camp.name} "
              f"({arch}) [score: {_top_score:.0f}]")

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
        if contract_fights not in CONTRACT_OPTIONS:
            contract_fights = 3
        if contract_fights > max_contract:
            return {"success": False, "error": f"Your {tier} facility can only offer {max_contract}-fight deals"}

        current = self._contracts.get(fighter_id, {})
        base = current.get('purse_per_fight', 5000 + ftr.overall_rating * 100)
        premium = CONTRACT_OPTIONS[contract_fights]["premium"]
        resign_cost = max(5000, int(base * 1.2 * premium * contract_fights * 0.1))

        if self._camp_balance < resign_cost:
            return {"success": False, "error": f"Need ${resign_cost:,}. Have ${self._camp_balance:,}"}

        self._camp_balance -= resign_cost
        self._contracts[fighter_id] = {
            "fighter_id":       fighter_id,
            "camp_id":          self._game_state.player_camp_id,
            "total_fights":     contract_fights,
            "fights_remaining": contract_fights,
            "fights_completed": 0,
            "purse_per_fight":  int(base * 1.1),
            "morale":           min(100, current.get('morale', 75) + 15),
            "holdout_weeks":    0,
            "is_holdout":       False,
            "signed_week":      self._game_state.week_number,
        }
        self._news_items.insert(0, {
            "headline": f"✅ EXTENDED: {ftr.name} re-signs — {contract_fights}-fight deal (${resign_cost:,})",
            "category": "signing",
            "week": self._game_state.week_number,
        })
        self._clear_cache()
        return {"success": True, "message": f"Re-signed {ftr.name} — {contract_fights}-fight deal"}

    def get_contract_options_for_tier(self) -> List[Dict]:
        """Available contract lengths for the player's current facility tier."""
        player_camp = self.get_player_camp()
        tier = str(getattr(player_camp, 'tier', 'GARAGE') if player_camp else 'GARAGE').upper()
        max_fights = TIER_CONTRACT_MAX.get(tier, 3)
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
                        "potential_grade":getattr(f, 'potential_grade', 'Average'),
                        "display_grade":  ceiling_to_display_grade(getattr(f, 'potential_ceiling', 75)),
                        "grade_color":    grade_color(ceiling_to_display_grade(getattr(f, 'potential_ceiling', 75))),
                        "style":          getattr(f, 'fighting_style', 'Balanced'),
                        "nationality":    getattr(f, 'nationality', 'USA'),
                        "tournament_wins":getattr(f, 'tournament_wins', 0),
                    }
                    for f in prospects[:8]
                ]
            except Exception:
                eligible[wc] = []

        # Regional rankings top 5 per division (sample weight classes)
        regional_rankings: Dict[str, List[Dict]] = {}
        for region in ["Americas", "Europe", "Asia", "Pacific"]:
            try:
                rr = sys.rankings.get(region, {})
                top = []
                for wc, rank_obj in list(rr.items())[:3]:
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
                                "wc":      wc,
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

        return {
            "available":         True,
            "eligible":          eligible,
            "regional_rankings": regional_rankings,
            "recent_tourneys":   recent_tourneys,
            "week":              week,
            "total_amateurs":    len(getattr(sys, 'amateurs', {})),
        }

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

            # Use the same tiered signing costs as amateur.py defines
            ovr = int(getattr(amateur, 'overall_rating', 60))
            if ovr >= 80:   signing_cost = 100_000
            elif ovr >= 70: signing_cost = 50_000
            elif ovr >= 60: signing_cost = 25_000
            else:           signing_cost = 10_000
            # Potential grade premium
            grade = getattr(amateur, 'potential_grade', 'Average')
            if grade == 'Elite': signing_cost = int(signing_cost * 1.5)
            elif grade == 'High': signing_cost = int(signing_cost * 1.2)
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

            self._camp_balance -= signing_cost
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
