"""
Cage Dynasty - Game Bridge
Connects Flask web app to the real CLI game engine.

This module bridges the gap between the Flask templates (which expect
a specific data format) and the real game engine classes.
"""

import sys
import os
from typing import Dict, List, Optional, Any
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


# ============================================================================
# WEB-FRIENDLY DATA CLASSES
# ============================================================================

@dataclass
class WebFighter:
    """Fighter data formatted for web templates"""
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
    camp_id: Optional[str]
    camp_name: str
    
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
    
    # Traits
    traits: List[str]
    
    # Fight history
    fight_history: List[Dict[str, Any]]


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
        self._camp_balance: int = 50000           # Starting balance
        self._camp_name:    str = "My Camp"       # Camp name
        self._total_purses_earned: int = 0
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
            "camp_balance":             self._camp_balance,
            "coach":                    self._coach,
            "scheduled_fights":         [clean_fight(f) for f in self._scheduled_fights],
            "upcoming_cards":           upcoming_clean,
            "fighter_cooldowns":        self._fighter_cooldowns,
            "fighter_training_plans":   self._fighter_training_plans,
            "fight_camps":              self._fight_camps,
            "week_declines":            self._week_declines,
            "neg_counter":              self._neg_counter,
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
        self._camp_balance            = data.get("camp_balance", 50000)
        self._coach                   = data.get("coach", {})
        self._scheduled_fights        = data.get("scheduled_fights", [])
        self._fighter_training_plans  = data.get("fighter_training_plans", {})
        self._fight_camps             = data.get("fight_camps", {})
        self._week_declines           = {k: int(v) for k, v in
                                          data.get("week_declines", {}).items()}
        self._neg_counter             = data.get("neg_counter", 0)
        self._news_items              = data.get("news_items", [])
        self._media_reactions         = data.get("media_reactions", {})
        self._fighter_cooldowns       = {k: int(v) for k, v in
                                          data.get("fighter_cooldowns", {}).items()}

        # Restore completed events
        self._completed_events = data.get("completed_events", [])

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
        
        try:
            import random

            # Check for fights this week
            fights_this_week = [f for f in self._scheduled_fights if f.get("weeks_until", 0) <= 0]
            fight_results = []
            week_events: Dict[str, Dict] = {}

            # ── Snapshot ranks BEFORE fights ──────────────────────────
            pre_ranks: Dict[str, Optional[int]] = {}
            for fight in fights_this_week:
                for fid in [fight.get("fighter1_id"), fight.get("fighter2_id")]:
                    if fid and fid not in pre_ranks:
                        rec = self._game_state.get_fighter(fid) if self._game_state else None
                        pre_ranks[fid] = self._get_fighter_rank(rec) if rec else None

            for fight in fights_this_week:
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

            # ── FOTN selection per event ──────────────────────────
            if FOTN_AVAILABLE:
                for ev in week_events.values():
                    if len(ev["fights"]) >= 2:
                        try:
                            fotn_fight, fotn_score = select_fotn(ev["fights"])
                            if fotn_fight:
                                ev["fotn"] = {
                                    "fighter1_name": fotn_fight.get("fighter1_name", ""),
                                    "fighter2_name": fotn_fight.get("fighter2_name", ""),
                                    "score":         round(fotn_score, 1),
                                    "tier":          get_excitement_tier(fotn_score),
                                    "bonus":         FOTN_BONUS,
                                    "fight_id":      fotn_fight.get("fight_id"),
                                }
                                # Tag the winning fight result
                                for fr in ev["fights"]:
                                    if fr.get("fight_id") == fotn_fight.get("fight_id"):
                                        fr["is_fotn"] = True
                                # News item
                                f1n = fotn_fight.get("fighter1_name", "")
                                f2n = fotn_fight.get("fighter2_name", "")
                                self._news_items.insert(0, {
                                    "headline":  f"🔥 FIGHT OF THE NIGHT: {f1n} vs {f2n} — "
                                                 f"${FOTN_BONUS:,} bonus each!",
                                    "category": "fotn",
                                    "week":      self._game_state.week_number,
                                })
                        except Exception as exc:
                            print(f"⚠️ FOTN selection failed: {exc}")

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
            
            # Decrement weeks_until for remaining fights
            for fight in self._scheduled_fights:
                fight["weeks_until"] = max(0, fight.get("weeks_until", 1) - 1)
            
            # Advance the game week
            report = self._game_state.advance_week()
            
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
            self._apply_weekly_training()

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
                        player_ev_name = ai_event.get("event_name", "")
                        for ev in list(week_events.values()):
                            if ev.get("event_name") == player_ev_name:
                                # Move player fights into the AI event
                                ai_event["fights"] = ev["fights"] + ai_event["fights"]
                                # Keep better main_event (prefer title fight or high slot)
                                if ev.get("main_event"):
                                    pf_slot = ev["main_event"].get("card_slot","")
                                    ae_slot = (ai_event.get("main_event") or {}).get("card_slot","")
                                    slot_rank = {"main_event":0,"co_main":1,"main_card":2,"prelim":3,"early_prelim":4}
                                    if slot_rank.get(pf_slot,9) <= slot_rank.get(ae_slot,9):
                                        ai_event["main_event"] = ev["main_event"]
                                # Remove from week_events so we don't double-store
                                week_events.pop(ev["event_name"], None)
                                break
                        self._completed_events.append(ai_event)
                # Store any player events that didn't merge (different event name)
                for ev in week_events.values():
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

            # ── Top up pipeline — add week N+8 ────────────────────────
            self._top_up_pipeline()

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

            # ── FOTN — use module if available, else builtin ──────────
            if FOTN_AVAILABLE and len(fight_results) >= 2:
                try:
                    fotn_result, _ = select_fotn(fight_results)
                except Exception:
                    fotn_result = self._select_fotn_builtin(fight_results)
            else:
                fotn_result = self._select_fotn_builtin(fight_results)
            if fotn_result:
                fotn_fid = fotn_result.get("fight_id")
                for fr in fight_results:
                    if fr.get("fight_id") == fotn_fid:
                        fr["is_fotn"] = True
                        if fr.get("winner_id") in player_ids_set or fr.get("loser_id") in player_ids_set:
                            self._camp_balance        += 50_000
                            self._total_purses_earned += 50_000
                f1n = fotn_result.get("fighter1_name", "")
                f2n = fotn_result.get("fighter2_name", "")
                self._news_items.insert(0, {
                    "headline": f"🔥 FIGHT OF THE NIGHT: {f1n} vs {f2n} — $50,000 bonus each!",
                    "category": "fotn",
                    "week":     self._game_state.week_number if self._game_state else 1,
                })

            # Offers are no longer auto-generated — fights come from the ladder

            self._clear_cache()
            return {
                "success": True, 
                "week": self._game_state.week_number, 
                "report": report,
                "fights_completed": fight_results,
            }
        except Exception as e:
            print(f"Error advancing week: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
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

        # ── Gameplan modifier for player fighter ──────────────────
        # Gameplan is stored on the fight dict when player books
        gameplan = fight.get("gameplan", "BALANCED")
        player_fids = set()
        if self._game_state and self._game_state.player_camp_id:
            player_fids = {
                f.fighter_id for f in self._game_state.get_player_fighters()
            }
        GAMEPLAN_BONUS = {
            "AGGRESSIVE":  8,   # Pressure striking — high offense
            "DEFENSIVE":   4,   # Counter — opponent score penalty
            "MEASURED":    5,   # Pacing — moderate with cardio edge
            "BALANCED":    2,   # No bias
            "TAKEDOWN":    7,   # Wrestling control — high for wrestlers
            "GNP":         9,   # Ground & pound — highest ceiling
            "SUBMISSION":  6,   # Sub hunting — trades position risk
            "CLINCH":      6,   # Dirty box / clinch control
        }
        bonus = GAMEPLAN_BONUS.get(gameplan, 2)
        if fighter1.fighter_id in player_fids:
            f1_score += bonus
            if gameplan == "DEFENSIVE":   f2_score -= 4
            if gameplan == "TAKEDOWN":    f1_score += 2   # wrestling bonus stacks
            if gameplan == "GNP":         f1_score += 1   # slight extra edge
        elif fighter2.fighter_id in player_fids:
            f2_score += bonus
            if gameplan == "DEFENSIVE":   f1_score -= 4
            if gameplan == "TAKEDOWN":    f2_score += 2
            if gameplan == "GNP":         f2_score += 1

        if f1_score >= f2_score:
            winner, loser = fighter1, fighter2
            winner_num, loser_num = 1, 2
        else:
            winner, loser = fighter2, fighter1
            winner_num, loser_num = 2, 1

        # Method selection — influenced by winner's gameplan + traits
        winner_gameplan = fight.get("gameplan", "BALANCED") if winner.fighter_id in player_fids else "BALANCED"
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

        # ── Update camp record ────────────────────────────────────────
        if self._game_state:
            for fid, is_win in [(winner.fighter_id, True), (loser.fighter_id, False)]:
                ftr = self._game_state.get_fighter(fid)
                if ftr and ftr.camp_id:
                    camp_rec = self._game_state.camps.get(ftr.camp_id)
                    if camp_rec:
                        if is_win:
                            camp_rec.total_wins = getattr(camp_rec, 'total_wins', 0) + 1
                        else:
                            camp_rec.total_losses = getattr(camp_rec, 'total_losses', 0) + 1
            # Clear camp cache so dashboard shows updated record
            self._camp_cache.clear()

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
            "opponent_name": loser.name,
            "opponent_id":   loser.fighter_id,
            "result": "W",
            "method": method,
            "round_finished": round_finished,
            "event_name": fight.get("event_name", ""),
            "week": self._game_state.week_number if self._game_state else 1,
        }
        loser_history_entry = {
            "opponent_name": winner.name,
            "opponent_id":   winner.fighter_id,
            "result": "L",
            "method": method,
            "round_finished": round_finished,
            "event_name": fight.get("event_name", ""),
            "week": self._game_state.week_number if self._game_state else 1,
        }
        if not hasattr(winner, "fight_history"):
            winner.fight_history = []
        if not hasattr(loser, "fight_history"):
            loser.fight_history = []
        winner.fight_history.append(winner_history_entry)
        loser.fight_history.append(loser_history_entry)

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
        """Get a fighter by ID"""
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
        
        # Get from real game state
        fighter = self._game_state.get_fighter(fighter_id)
        if not fighter:
            return None
        
        web_f = self._convert_real_fighter(fighter)
        self._fighter_cache[fighter_id] = web_f
        return web_f
    
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
            "is_title_fight": False,
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
        
        # Remove the offer
        self._fight_offers = [o for o in self._fight_offers if o["offer_id"] != offer_id]
        
        return {"success": True, "message": "Offer declined"}
    
    def get_scheduled_fights(self) -> List[Dict[str, Any]]:
        """Get all scheduled fights for player's fighters"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return self._mock_generator.get_player_scheduled_fights()
            return []
        
        return self._scheduled_fights
    
    def get_upcoming_events(self) -> List[Dict[str, Any]]:
        """Get upcoming events"""
        if self._mock_mode:
            if hasattr(self, '_mock_generator'):
                return self._mock_generator.get_upcoming_events()
            return []
        
        # Group scheduled fights by week
        events = {}
        for fight in self._scheduled_fights:
            week = fight["week"]
            if week not in events:
                events[week] = {
                    "week": week,
                    "event_name": fight["event_name"],
                    "fights": []
                }
            events[week]["fights"].append(fight)
        
        return sorted(events.values(), key=lambda e: e["week"])
    
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
            location=camp.location_str if hasattr(camp, 'location_str') else f"{camp.city}, {camp.country}" if camp.city else "Unknown",
            reputation=camp.reputation,
            balance=self._camp_balance if camp.is_player else getattr(camp, 'balance', 0),
            is_player=camp.is_player,
            max_fighters=self._roster_cap_for_tier(tier_str),
            fighter_ids=fighter_ids,
            wins=camp.total_wins,
            losses=camp.total_losses,
            record_str=f"{camp.total_wins}-{camp.total_losses}",
            win_percentage=int(camp.total_wins / max(1, camp.total_wins + camp.total_losses) * 100),
            championships=live_championships,
            head_coach_name="Head Coach",
            head_coach_specialty="MMA",
            head_coach_rating=50
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

        history  = getattr(fighter, 'fight_history', [])
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

        return WebFighter(
            fighter_id=fighter.fighter_id,
            name=fighter.name,
            nickname=nickname,
            age=age,
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
            fight_history=[
                {
                    'opponent':    f.get('opponent_name', '') if isinstance(f, dict) else '',
                    'opponent_id': f.get('opponent_id',   '') if isinstance(f, dict) else '',
                    'result':      f.get('result',        '') if isinstance(f, dict) else '',
                    'method':      str(f.get('method',    '')) if isinstance(f, dict) else '',
                    'round':       f.get('round_finished', 0) if isinstance(f, dict) else 0,
                    'event':       f.get('event_name',    '') if isinstance(f, dict) else '',
                    'week':        f.get('week',          0) if isinstance(f, dict) else 0,
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
        return {
            "success":       True,
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

    def _apply_weekly_training(self) -> None:
        """
        Called each advance_week.
        1. Applies each player fighter's training plan.
        2. Applies passive coach specialty gains to all player fighters.
        """
        if not self._game_state:
            return

        player_camp = self.get_player_camp()
        camp_tier   = player_camp.tier.upper() if player_camp else "GARAGE"
        player_fighters = self._game_state.get_player_fighters()

        coach_specialty = self._coach.get("specialty", "boxing")
        coach_rating    = self._coach.get("rating", 60)

        # Passive coach gain per week — scales with rating
        # 60-rated coach: 0 passive, 70: 0.5, 80: 1.0, 90: 1.5, 95+: 2
        passive_gain = max(0, (coach_rating - 60) / 20)

        # Map coach specialty string to focus key
        SPECIALTY_MAP = {
            "striking": "boxing",  "boxing": "boxing",
            "kickboxing": "kicks", "muay thai": "kicks",
            "wrestling": "wrestling", "grappling": "wrestling",
            "bjj": "bjj", "submissions": "bjj",
            "conditioning": "cardio", "cardio": "cardio",
            "strength": "strength", "cornering": "fight_iq",
            "strategy": "fight_iq", "mma": "sparring",
        }
        coach_focus = SPECIALTY_MAP.get(coach_specialty.lower(), "sparring")

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
            self.apply_training_week(fid, active_plan["focus"], active_plan["intensity"], camp_tier)

            # Passive coach gains — also subject to diminishing returns
            if passive_gain > 0:
                coach_attrs  = self._FOCUS_ATTRS.get(coach_focus, ["fight_iq"])
                real_fighter = self._game_state.get_fighter(fid)
                if real_fighter:
                    for attr in coach_attrs[:1]:
                        current = float(getattr(real_fighter, attr,
                                        getattr(real_fighter, 'overall_rating', 50)))
                        effective = self._diminishing_gain(current, passive_gain, camp_tier)
                        if hasattr(real_fighter, attr):
                            setattr(real_fighter, attr, min(100.0, current + effective))

                    # Recalculate overall_rating after passive gains
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
                    "grade": pa.potential_grade, "ceiling": pa.potential_ceiling,
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
        player_ids = {f.fighter_id for f in self.get_player_fighters()}
        for event in self._completed_events[-10:]:
            for fight in event.get("fights", []):
                fid  = fight.get("fight_id") or f"fight_{fight.get('winner_id','')}"
                iv   = self._fight_interviews.get(fid, {})
                wid  = fight.get("winner_id", "")
                lid  = fight.get("loser_id",  "")
                if wid in player_ids and not iv.get("winner_done"):
                    pending.append({"fight_id": fid, "fighter_id": wid,
                        "fighter_name": fight.get("winner_name", ""),
                        "opponent_id": lid, "opponent_name": fight.get("loser_name", ""),
                        "role": "winner", "method": fight.get("method", ""),
                        "choices": self._WINNER_CHOICES, "event_name": event.get("event_name", "")})
                if lid in player_ids and not iv.get("loser_done"):
                    pending.append({"fight_id": fid, "fighter_id": lid,
                        "fighter_name": fight.get("loser_name", ""),
                        "opponent_id": wid, "opponent_name": fight.get("winner_name", ""),
                        "role": "loser", "method": fight.get("method", ""),
                        "choices": self._LOSER_CHOICES, "event_name": event.get("event_name", "")})
        return pending

    def process_interview(self, fight_id: str, fighter_id: str,
                          role: str, choice: str,
                          call_out_id: Optional[str] = None) -> Dict[str, Any]:
        if fight_id not in self._fight_interviews:
            self._fight_interviews[fight_id] = {}
        iv = self._fight_interviews[fight_id]
        try:
            from interviews import InterviewManager, WinnerResponse, LoserResponse, WINNER_TEMPLATES, LOSER_TEMPLATES
            import random
            mgr     = InterviewManager()
            fighter = self.get_fighter(fighter_id)
            fname   = fighter.name if fighter else "Fighter"
            week    = self.week_number
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

                # Only sign Elite or High potential
                if amateur.potential_grade not in ("Elite", "High"):
                    continue

                # AI camp signs this fighter — pick a random camp
                # with roster space (basic check)
                import random
                eligible_camps = [c for c in ai_camps if
                                  getattr(c, 'fighter_count', 0) <
                                  getattr(c, 'max_fighters', 6)]
                if not eligible_camps:
                    continue

                signing_camp = random.choice(eligible_camps)

                # Mark as turned pro — remove from amateur pool
                amateur.turned_pro = True
                amateur.is_active  = False

                self._news_items.insert(0, {
                    "headline": f"🏆 {champion_name} ({amateur.potential_grade} potential) "
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

                grade_emoji = {"Elite": "⭐⭐⭐", "High": "⭐⭐", "Average": "⭐"}.get(
                    amateur.potential_grade, "⭐")

                self._news_items.insert(0, {
                    "headline": f"👀 Scout Report: {amateur.name} ({amateur.weight_class}, "
                                f"{amateur.wins}-{amateur.losses}) just turned pro-eligible "
                                f"in {coach_region}. {grade_emoji} {amateur.potential_grade} potential — "
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
                self._news_items.append({
                    "headline": f"📉 {decay.fighter_name}'s {decay.stat} getting rusty "
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

        except Exception as e:
            pass  # Maintenance is non-critical

    # =========================================================================
    # WATCHLIST
    # =========================================================================

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

    def is_on_watchlist(self, fighter_id: str) -> bool:
        return fighter_id in self._watchlist

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

        # ── 4. Clamp ──────────────────────────────────────────────────────
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
        }

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
            rec_gameplan  = self._gameplan_from_specialty(coach_specialty)
            rec_focus     = coach_specialty
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
        """Map a coach's specialty stat to a gameplan stance."""
        return {
            "boxing":           "AGGRESSIVE",
            "kicks":            "AGGRESSIVE",
            "clinch_striking":  "CLINCH",
            "takedowns":        "TAKEDOWN",
            "top_control":      "GNP",
            "submissions":      "SUBMISSION",
            "guard":            "SUBMISSION",
            "striking_defense": "DEFENSIVE",
            "takedowns":        "AGGRESSIVE",
            "takedown_defense": "DEFENSIVE",
            "top_control":      "AGGRESSIVE",
            "submissions":      "AGGRESSIVE",
            "guard":            "DEFENSIVE",
            "cardio":           "AGGRESSIVE",
        }.get(specialty, "BALANCED")

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

    def _update_rankings_after_fight(self, weight_class: str) -> None:
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

        def rank_score(f) -> float:
            # Count wins over ranked opponents from fight history
            ranked_wins = sum(
                1 for h in getattr(f, 'fight_history', [])
                if isinstance(h, dict)
                and h.get('result') == 'W'
                and h.get('opponent_id') in ranked_ids
            )
            # Win streak
            streak = 0
            for h in reversed(getattr(f, 'fight_history', [])):
                if isinstance(h, dict) and h.get('result') == 'W':
                    streak += 1
                else:
                    break
            finish_wins = getattr(f, 'ko_wins', 0) + getattr(f, 'sub_wins', 0)
            score = (
                f.wins    * 5.0
                + finish_wins * 2.0
                - f.losses  * 3.0
                + streak    * 1.5
                + ranked_wins * 8.0
            )
            return score

        fighters.sort(key=rank_score, reverse=True)

        # Top 10 requires 3+ wins; bottom 5 spots (11-15) require 1+ win
        top10  = [f for f in fighters[:10] if f.wins >= 3]
        rest   = [f for f in fighters if f not in top10 and f.wins >= 1]
        division.rankings = [f.fighter_id for f in (top10 + rest)[:15]]

    def _update_all_rankings(self) -> None:
        """Update rankings for every division — called each week."""
        if not self._game_state:
            return
        for wc in self._game_state.WEIGHT_CLASSES:
            self._update_rankings_after_fight(wc)

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

        for fight in fights_to_sim:
            f1 = self._game_state.get_fighter(fight["fighter1_id"])
            f2 = self._game_state.get_fighter(fight["fighter2_id"])
            if not f1 or not f2:
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

            pre_w = self._get_fighter_rank(winner)
            pre_l = self._get_fighter_rank(loser)

            winner.wins += 1; loser.losses += 1
            if method in ("KO","TKO"): winner.ko_wins += 1
            elif method == "SUB":       winner.sub_wins += 1

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

            if method in ("KO","TKO","SUB"):
                icon = "💥" if method in ("KO","TKO") else "🔒"
                self._news_items.append({
                    "headline": f"{icon} {winner.name} def. {loser.name} by {method} (R{rnd}) at {event_name}",
                    "category": "fight", "week": week,
                })

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

            # ── AI fight outcome ────────────────────────────────────
            if FIGHT_ENGINE_AVAILABLE:
                try:
                    # Use real engine — no commentary stored for AI fights
                    fa1 = self._make_fighter_attrs(f1, f1.name, f1.fighter_id)
                    fa2 = self._make_fighter_attrs(f2, f2.name, f2.fighter_id)
                    _rnds = 5 if fight.get("is_title_fight") else 3
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
                    "headline": f"{icon} {winner.name} def. {loser.name} by {method} (R{rnd}) at {event_name}",
                    "category": "fight",
                    "week":     week,
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
        Cooldown after a fight.
        Winners: 0 weeks (available immediately).
        Losers: 6 + (lose_streak - 1) weeks, max 12.
        Champions defending: 8 weeks minimum.
        """
        lose_streak = self._get_fighter_lose_streak(fighter)
        if is_champion:
            return max(8, 6 + lose_streak)
        if lose_streak == 0:
            return 0          # Winner — fight again anytime
        return min(12, 6 + (lose_streak - 1))

    def _apply_cooldown(self, fighter, week: int, is_champion: bool = False) -> None:
        """Record when this fighter is next available."""
        cooldown = self._cooldown_weeks(fighter, is_champion)
        self._fighter_cooldowns[fighter.fighter_id] = week + cooldown

    def _is_available(self, fighter_id: str, week: int) -> bool:
        """True if fighter has no cooldown blocking them this week."""
        return self._fighter_cooldowns.get(fighter_id, 0) <= week

    def _matchup_score(self, f1, f2, is_title: bool = False) -> float:
        """Score a matchup for card slot assignment."""
        if CARD_BUILDER_AVAILABLE:
            r1 = self._get_fighter_rank(f1)
            r2 = self._get_fighter_rank(f2)
            return self._card_builder.calculate_matchup_score(
                fighter1_rating=f1.overall_rating,
                fighter2_rating=f2.overall_rating,
                fighter1_rank=r1,
                fighter2_rank=r2,
                is_title_fight=is_title,
            )
        # Fallback
        return (f1.overall_rating + f2.overall_rating) / 2.0

    def _assign_card_slot(self, event_name: str, score: float,
                           is_title: bool, combined_rating: int) -> str:
        """Return slot string for a fight."""
        if not CARD_BUILDER_AVAILABLE:
            return "prelim"
        slot, _ = self._card_builder.assign_slot(
            event_name=event_name,
            weeks_until=4,
            matchup_score=score,
            is_title_fight=is_title,
            combined_rating=combined_rating,
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
                slot = self._assign_card_slot(
                    event_name, score, sf.get("is_title_fight", False),
                    combined_rating=100,
                )
                sf["card_slot"]  = slot
                sf["event_name"] = event_name
                card["fights"].append(sf)

        # Also collect fighters booked on other weeks
        all_booked = set()
        for sf in self._scheduled_fights:
            all_booked.add(sf.get("fighter1_id",""))
            all_booked.add(sf.get("fighter2_id",""))
        # Booked on OTHER cards in the pipeline
        for wk, existing_card in self._upcoming_cards.items():
            if wk == target_week:
                continue
            for f in existing_card.get("fights", []):
                all_booked.add(f.get("fighter1_id",""))
                all_booked.add(f.get("fighter2_id",""))

        player_camp_id = self._game_state.player_camp_id
        target_count   = 12

        # ── Collect ALL candidate matchups across every division ──────────
        # Then sort by matchup score so best fights get top slots.
        # This replaces the old random-shuffle-per-division approach.
        candidates = []   # list of (score, f1, f2, wc, is_title)

        for wc in self._game_state.WEIGHT_CLASSES:
            if len(card["fights"]) + len(candidates) >= target_count * 2:
                break  # Enough candidates, stop scanning

            division = self._game_state.divisions.get(wc)
            if not division:
                continue

            available = [
                f for f in self._game_state.fighters.values()
                if f.weight_class == wc
                and f.is_active
                and f.fighter_id not in all_booked
                and f.fighter_id not in booked_here
                and self._is_available(f.fighter_id, target_week)
            ]
            if len(available) < 2:
                continue

            # ── Title fight: champion vs #1 contender ────────────────────
            champ_id = division.champion_id
            top_id   = division.rankings[0] if division.rankings else None
            if champ_id and top_id:
                champ = next((f for f in available if f.fighter_id == champ_id), None)
                top   = next((f for f in available if f.fighter_id == top_id), None)
                if champ and top:
                    score = self._matchup_score(champ, top, is_title=True)
                    candidates.append((score, champ, top, wc, True))
                    continue  # Don't also add a non-title fight from this division

            # ── Ranked vs ranked: pick best available pair ────────────────
            ranked_ids   = set(division.rankings[:14])
            ranked_avail = sorted(
                [f for f in available if f.fighter_id in ranked_ids],
                key=lambda f: division.rankings.index(f.fighter_id)
                              if f.fighter_id in division.rankings else 99
            )

            if len(ranked_avail) >= 2:
                # Try adjacent ranked pairs — pick the highest-scoring pair
                best_pair = None
                best_pair_score = -1
                for i in range(min(len(ranked_avail) - 1, 6)):
                    for j in range(i + 1, min(len(ranked_avail), i + 4)):
                        s = self._matchup_score(ranked_avail[i], ranked_avail[j])
                        if s > best_pair_score:
                            best_pair_score = s
                            best_pair = (ranked_avail[i], ranked_avail[j])
                if best_pair:
                    candidates.append((best_pair_score, best_pair[0], best_pair[1], wc, False))
            elif len(available) >= 2:
                # No ranked fighters available — unranked matchup
                f1, f2 = random.sample(available, 2)
                score  = self._matchup_score(f1, f2)
                candidates.append((score, f1, f2, wc, False))

        # ── Sort candidates by score descending ───────────────────────────
        candidates.sort(key=lambda x: x[0], reverse=True)

        # ── Fill card slots top-to-bottom ─────────────────────────────────
        used_in_candidates = set()
        for score, f1, f2, wc, is_title in candidates:
            if len(card["fights"]) >= target_count:
                break
            # Skip if either fighter was already matched in a higher-score fight
            if f1.fighter_id in used_in_candidates or f2.fighter_id in used_in_candidates:
                continue

            slot = self._assign_card_slot(
                event_name, score, is_title,
                f1.overall_rating + f2.overall_rating
            )
            fight_dict = self._make_scheduled_fight(
                f1, f2, wc, event_name, target_week, slot, is_title=is_title)
            card["fights"].append(fight_dict)
            used_in_candidates.add(f1.fighter_id)
            used_in_candidates.add(f2.fighter_id)
            all_booked.add(f1.fighter_id)
            all_booked.add(f2.fighter_id)

        return card

    def _make_scheduled_fight(self, f1, f2, wc: str, event_name: str,
                               target_week: int, slot: str,
                               is_title: bool = False) -> Dict[str, Any]:
        """Build a scheduled fight dict for the card pipeline."""
        weeks_out = target_week - (self._game_state.week_number if self._game_state else 0)
        return {
            "fight_id":       f"fight_{target_week}_{f1.fighter_id[:8]}_{f2.fighter_id[:8]}",
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
        Builds 8 weeks of DFC cards upfront.
        """
        if not self._game_state:
            return
        current = self._game_state.week_number
        for w in range(current + 1, current + 7):
            self._upcoming_cards[w] = self._build_card_for_week(w)
        print(f"✅ Card pipeline initialized: DFC {current+1} – DFC {current+6}")

    def _top_up_pipeline(self) -> None:
        """Add one more week to the pipeline. Called each advance_week."""
        if not self._game_state:
            return
        current = self._game_state.week_number
        new_week = current + 6
        if new_week not in self._upcoming_cards:
            self._upcoming_cards[new_week] = self._build_card_for_week(new_week)

    def get_upcoming_events(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Return upcoming DFC cards for the UI."""
        if not self._game_state:
            return []
        current = self._game_state.week_number
        out = []
        for wk in sorted(self._upcoming_cards.keys()):
            if wk <= current:
                continue
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
        is_main  = fight.get("card_slot") in ("main_event", "co_main") or fight.get("is_player_fight", False)
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
        return result

    def get_fight_commentary(self, fight_id: str) -> List[str]:
        """
        Return commentary for a fight.
        Generated lazily on first call — not stored during simulation.
        Cached after first generation.
        """
        # Check cache first
        if fight_id in self._fight_commentary:
            return self._fight_commentary[fight_id]

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

        def _prestige(fight: Dict) -> int:
            ranks = [r for r in [fight.get("winner_new_rank"), fight.get("loser_new_rank")]
                     if r is not None]
            return 999 - min(ranks) if ranks else 0

        pool = finishes if finishes else decisions
        return max(pool, key=_prestige) if pool else fights[0]

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

    def sign_free_agent(self, fighter_id: str) -> Dict[str, Any]:
        """Sign a free agent to the player's camp."""
        if not self._game_state:
            return {"success": False, "error": "No game loaded"}

        fighter = self._game_state.get_fighter(fighter_id)
        if not fighter:
            return {"success": False, "error": "Fighter not found"}
        if fighter.camp_id:
            return {"success": False, "error": f"{fighter.name} is already signed to a camp"}
        if fighter.fighter_id not in self._game_state.free_agents:
            return {"success": False, "error": f"{fighter.name} is not available"}

        signing_cost = 5000 + fighter.overall_rating * 300
        if self._camp_balance < signing_cost:
            return {"success": False, "error": f"Insufficient funds. Need ${signing_cost:,}, have ${self._camp_balance:,}"}

        player_camp  = self._game_state.get_camp(self._game_state.player_camp_id)
        tier         = getattr(player_camp, 'tier', 'GARAGE') if player_camp else 'GARAGE'
        max_fighters = self._roster_cap_for_tier(str(tier))
        roster_size  = len(self._game_state.get_player_fighters())
        if roster_size >= max_fighters:
            return {"success": False, "error": f"Roster full ({roster_size}/{max_fighters}). Upgrade your facility to sign more."}

        self._game_state._sign_fighter_to_camp(fighter_id, self._game_state.player_camp_id)
        self._camp_balance -= signing_cost

        self._news_items.insert(0, {
            "headline": f"📝 SIGNED: {fighter.name} joins your camp (${signing_cost:,})",
            "category": "signing",
            "week":     self._game_state.week_number,
        })
        self._clear_cache()
        return {"success": True, "message": f"Signed {fighter.name} for ${signing_cost:,}"}


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
        for wc in ["Lightweight", "Welterweight", "Bantamweight",
                   "Featherweight", "Middleweight", "Heavyweight"]:
            try:
                fighters = sys.get_eligible_amateurs(wc)
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
                        "style":          getattr(f, 'fighting_style', 'Balanced'),
                        "nationality":    getattr(f, 'nationality', 'USA'),
                        "tournament_wins":getattr(f, 'tournament_wins', 0),
                    }
                    for f in fighters[:20]
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

            signing_cost = 3000 + int(getattr(amateur, 'overall_rating', 60)) * 200
            if self._camp_balance < signing_cost:
                return {"success": False,
                        "error": f"Need ${signing_cost:,}, have ${self._camp_balance:,}"}

            # Create FighterRecord in main game
            if self._game_state:
                import uuid
                fid = f"amateur_{amateur_id[:12]}"
                from core.game_state import FighterRecord
                rec = FighterRecord(
                    fighter_id=fid,
                    name=amateur.name,
                    weight_class=getattr(amateur, 'weight_class', 'Lightweight'),
                    overall_rating=int(getattr(amateur, 'overall_rating', 60)),
                    wins=getattr(amateur, 'wins', 0),
                    losses=getattr(amateur, 'losses', 0),
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
