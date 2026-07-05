# simulation/fight_integration.py
# Module 16: Fight Integration
# Lines: ~850
#
# Bridges fight_engine and commentary systems for complete
# narrated fight simulation with play-by-play commentary.

"""
Cage Dynasty - Fight Integration Module

This module provides:
- Integrated fight simulation with live commentary
- Event-driven commentary generation
- Complete fight narratives with round-by-round breakdowns
- Fight result packaging with full stats and story
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto

# Fight engine imports - only import what actually exists
from fight_engine import (
    # Core types
    Position, StrikeType, SubmissionType, GrapplingAction,
    STANDING_POSITIONS, CLINCH_POSITIONS, DOMINANT_POSITIONS,
    LEG_ENTANGLEMENT_POSITIONS, FRONT_HEADLOCK_POSITIONS,
    STRIKE_PROPERTIES,
    # State classes
    FighterAttributes, FighterState, FightState, FightConfig,
    RoundStats, FightResult, BodyPartDamage,
    # GAMEPLAN-WIRE1: threaded through the call chain, not yet consumed
    Gameplan,
    # Functions
    get_available_strikes, get_available_submissions,
    get_available_grappling_actions, select_action,
    calculate_strike_success, calculate_strike_damage,
    calculate_grappling_success, apply_position_change,
    attempt_submission, process_submission_progress,
    score_round,
    # V7 Balance Constants (centralized in fight_engine)
    DAMAGE_MULTIPLIER,
    FLASH_KO_DAMAGE_THRESHOLD, FLASH_KO_BASE_CHANCE, FLASH_KO_MAX_CHANCE,
    TKO_GNP_HEALTH_THRESHOLD, TKO_GNP_BASE_CHANCE, TKO_GNP_MAX_CHANCE,
    TKO_STANDING_HEALTH_THRESHOLD, TKO_STANDING_BASE_CHANCE,
)

# fight_integration runs a longer commentary exchange loop than fight_engine.simulate_fight
# so the effective damage per fight is higher — this multiplier is tuned separately
# to produce realistic finish rates (50-55% target) for the narrated fight path.
# Ship A two-iteration tune (2026-05-09):
#   0.32 (Saturday play: 11% finish rate, broken)
#   → 0.38 (Tier 2 verified: 70% across DFC 16-18, over-corrected)
#   → 0.36 (final, lands in 50-55% target)
# Synthetic-vs-production gap: synthetic n=300 batches predicted finish rates
# ~20-30 points below production reality at the same multiplier. Production
# may have damage-amplifying factors (gameplan, condition, fighter attrs from
# real game_state) that the random-Gaussian synthetic doesn't capture. Future
# tuning should weight production observations over synthetic.
FI_DAMAGE_MULTIPLIER = 0.48

# Define missing position sets locally
GROUND_TOP_POSITIONS = {
    Position.FULL_GUARD_TOP, Position.CLOSED_GUARD_TOP,
    Position.HALF_GUARD_TOP, Position.BUTTERFLY_GUARD_TOP,
    Position.SIDE_CONTROL_TOP, Position.MOUNT, Position.BACK_MOUNT,
    Position.NORTH_SOUTH_TOP, Position.CRUCIFIX_TOP, Position.TURTLE_TOP,
}

GROUND_BOTTOM_POSITIONS = {
    Position.FULL_GUARD_BOTTOM, Position.CLOSED_GUARD_BOTTOM,
    Position.HALF_GUARD_BOTTOM, Position.BUTTERFLY_GUARD_BOTTOM,
    Position.RUBBER_GUARD_BOTTOM,
    Position.SIDE_CONTROL_BOTTOM, Position.MOUNT_BOTTOM, Position.BACK_MOUNT_BOTTOM,
    Position.NORTH_SOUTH_BOTTOM, Position.CRUCIFIX_BOTTOM, Position.TURTLE_BOTTOM,
}

# Define missing helper functions locally
def get_position_control(position: Position) -> str:
    """Get who has control in a position."""
    if position in DOMINANT_POSITIONS or position in GROUND_TOP_POSITIONS:
        return "top"
    elif position in GROUND_BOTTOM_POSITIONS:
        return "bottom"
    elif position in STANDING_POSITIONS or position in CLINCH_POSITIONS:
        return "neutral"
    elif position in LEG_ENTANGLEMENT_POSITIONS:
        return "neutral"
    return "neutral"

def get_style_action_weights(style) -> Dict[str, float]:
    """Action weight multipliers by fighting style.
    Applied on top of base select_action weights.
    Grapplers get more submission/grapple; strikers more striking.
    Mirrors the inline dict in fight_engine.select_action."""
    weights = {
        "ORTHODOX_BOXER":    {"strike":1.4,"grapple":0.7,"submission":0.3},
        "KICKBOXER":         {"strike":1.4,"grapple":0.7,"submission":0.3},
        "MUAY_THAI":         {"strike":1.3,"grapple":0.9,"submission":0.4},
        "PRESSURE_FIGHTER":  {"strike":1.2,"grapple":1.0,"submission":0.4},
        "COUNTER_STRIKER":   {"strike":1.3,"grapple":0.8,"submission":0.3},
        "POINT_FIGHTER":     {"strike":1.4,"grapple":0.6,"submission":0.2},
        "KARATE":            {"strike":1.3,"grapple":0.7,"submission":0.3},
        "WRESTLER":          {"strike":0.8,"grapple":1.4,"submission":0.9},
        "BJJ_SPECIALIST":    {"strike":0.6,"grapple":1.2,"submission":2.0},
        "SAMBO":             {"strike":0.9,"grapple":1.3,"submission":1.4},
        "JUDO":              {"strike":0.8,"grapple":1.5,"submission":0.9},
        "GROUND_AND_POUND":  {"strike":1.0,"grapple":1.4,"submission":0.6},
        "SPRAWL_AND_BRAWL":  {"strike":1.3,"grapple":0.7,"submission":0.4},
        "CLINCH_FIGHTER":    {"strike":1.0,"grapple":1.3,"submission":0.7},
        "BRAWLER":           {"strike":1.3,"grapple":0.8,"submission":0.4},
        "HYBRID":            {"strike":1.0,"grapple":1.0,"submission":0.8},
        "STRIKER":           {"strike":1.4,"grapple":0.7,"submission":0.3},
        "BALANCED":          {"strike":1.0,"grapple":1.0,"submission":1.0},
    }
    s = getattr(style, 'name', '') or str(style)
    return weights.get(s.upper(),
        {"strike":1.0,"grapple":1.0,"submission":1.0})

# Event logging types
class FightEventType(Enum):
    """Types of events that can occur in a fight."""
    STRIKE = auto()
    TAKEDOWN = auto()
    SUBMISSION_ATTEMPT = auto()
    POSITION_CHANGE = auto()
    KNOCKDOWN = auto()
    FINISH = auto()

def create_event(event_type: FightEventType, **kwargs) -> Dict[str, Any]:
    """Create a fight event dictionary."""
    return {"type": event_type, **kwargs}

# Core types
from core.types import FightingStyle  # For style support

# Commentary imports
from commentary import (
    ActionType, DamageLevel, EventSignificance,
    FightContext, FightEvent, RoundSummary,
    FightCommentarySystem,
    create_commentary_system,
)


# ============================================================================
# NARRATED FIGHT RESULT
# ============================================================================

@dataclass
class NarratedFightResult:
    """
    Complete fight result with commentary and narrative.
    
    Combines fight_engine's FightResult with commentary system's
    narrative output for a complete fight package.
    """
    # Core result
    winner_id: Optional[str]
    winner_name: str
    loser_id: Optional[str]
    loser_name: str
    method: str
    sub_type: str = ""      # Submission type e.g. "rear_naked_choke", "" for non-subs

    # Timing
    finish_round: Optional[int] = None
    finish_time: Optional[str] = None
    total_rounds: int = 3
    
    # Scoring (for decisions)
    judge_scores: List[Tuple[int, int]] = field(default_factory=list)
    decision_type: Optional[str] = None
    
    # Stats per round
    fighter1_stats: List[Dict[str, Any]] = field(default_factory=list)
    fighter2_stats: List[Dict[str, Any]] = field(default_factory=list)
    
    # Final states
    fighter1_final_health: float = 100.0
    fighter2_final_health: float = 100.0
    
    # Commentary & Narrative
    round_summaries: List[Dict[str, Any]] = field(default_factory=list)
    key_moments: List[Dict[str, Any]] = field(default_factory=list)
    full_commentary: str = ""
    fight_narrative: str = ""
    
    # Bonus tracking
    fight_of_night: bool = False
    performance_bonus: bool = False
    
    @property
    def is_finish(self) -> bool:
        return "Decision" not in self.method and self.method != "Draw"
    
    @property
    def is_decision(self) -> bool:
        return "Decision" in self.method
    
    @property
    def is_draw(self) -> bool:
        return self.method == "Draw"
    
    def get_summary(self) -> str:
        """Get a brief summary of the fight"""
        if self.is_finish:
            return f"{self.winner_name} def. {self.loser_name} via {self.method} (R{self.finish_round}, {self.finish_time})"
        elif self.is_draw:
            return f"{self.winner_name} vs {self.loser_name} - Draw"
        else:
            scores = ", ".join([f"{s1}-{s2}" for s1, s2 in self.judge_scores])
            return f"{self.winner_name} def. {self.loser_name} via {self.decision_type} Decision ({scores})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            "winner_id": self.winner_id,
            "winner_name": self.winner_name,
            "loser_id": self.loser_id,
            "loser_name": self.loser_name,
            "method": self.method,
            "finish_round": self.finish_round,
            "finish_time": self.finish_time,
            "total_rounds": self.total_rounds,
            "judge_scores": self.judge_scores,
            "decision_type": self.decision_type,
            "fighter1_stats": self.fighter1_stats,
            "fighter2_stats": self.fighter2_stats,
            "round_summaries": self.round_summaries,
            "key_moments": self.key_moments,
            "fight_of_night": self.fight_of_night,
            "performance_bonus": self.performance_bonus,
            "summary": self.get_summary()
        }


# ============================================================================
# ACTION TYPE MAPPING
# ============================================================================

def strike_to_action_type(strike: StrikeType) -> ActionType:
    """Map strike type to commentary action type"""
    kick_strikes = {
        StrikeType.LEG_KICK, StrikeType.BODY_KICK, StrikeType.HEAD_KICK,
        StrikeType.FRONT_KICK, StrikeType.SIDE_KICK, StrikeType.SPINNING_BACK_KICK,
        StrikeType.WHEEL_KICK, StrikeType.AXE_KICK, StrikeType.CALF_KICK,
        StrikeType.OBLIQUE_KICK
    }
    
    gnp_strikes = {
        StrikeType.GNP_PUNCH, StrikeType.GNP_HAMMER_FIST, StrikeType.GNP_ELBOW,
        StrikeType.ELBOW_UPWARD  # Ground elbow from bottom position
    }
    
    clinch_strikes = {
        StrikeType.CLINCH_KNEE, StrikeType.CLINCH_ELBOW, StrikeType.DIRTY_BOXING,
        StrikeType.KNEE_BODY, StrikeType.KNEE_HEAD
    }
    
    if strike in kick_strikes:
        return ActionType.KICK
    elif strike in gnp_strikes:
        return ActionType.GROUND_STRIKE
    elif strike in clinch_strikes:
        return ActionType.CLINCH_STRIKE
    else:
        return ActionType.STRIKE


def grappling_to_action_type(action: GrapplingAction) -> ActionType:
    """Map grappling action to commentary action type"""
    takedowns = {
        GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG,
        GrapplingAction.BODY_LOCK_TAKEDOWN, GrapplingAction.HIP_TOSS,
        GrapplingAction.TRIP, GrapplingAction.SLAM, GrapplingAction.SUPLEX
    }
    
    sweeps = {
        GrapplingAction.SCISSOR_SWEEP, GrapplingAction.FLOWER_SWEEP,
        GrapplingAction.BUTTERFLY_SWEEP, GrapplingAction.ELEVATOR_SWEEP,
        GrapplingAction.HIP_BUMP
    }
    
    escapes = {
        GrapplingAction.SHRIMP_ESCAPE, GrapplingAction.BRIDGE_ESCAPE,
        GrapplingAction.ELBOW_ESCAPE, GrapplingAction.GRANBY_ROLL,
        GrapplingAction.CLINCH_BREAK  # Escaping the clinch
    }
    
    clinch_actions = {
        GrapplingAction.CLINCH_ENTRY, GrapplingAction.PUSH_TO_CAGE
    }
    
    if action in takedowns:
        return ActionType.TAKEDOWN
    elif action in sweeps:
        return ActionType.SWEEP
    elif action in escapes:
        return ActionType.ESCAPE
    elif action in clinch_actions:
        return ActionType.CLINCH
    elif action == GrapplingAction.STAND_UP or action == GrapplingAction.TECHNICAL_STANDUP:
        return ActionType.STAND_UP
    else:
        return ActionType.POSITION_ADVANCE


# ============================================================================
# INTEGRATED FIGHT SIMULATOR
# ============================================================================

class NarratedFightSimulator:
    """
    Simulates fights with integrated commentary.
    
    Combines the fight_engine's simulation with the commentary
    system to produce complete narrated fight experiences.
    """
    
    def __init__(
        self,
        fighter1: FighterAttributes,
        fighter2: FighterAttributes,
        config: Optional[FightConfig] = None,
        verbose: bool = True,
        corner_bonus_f1: float = 0.0,
        corner_bonus_f2: float = 0.0,
        starting_stamina_f1: float = 100.0,
        starting_stamina_f2: float = 100.0,
        gameplan_f1: Optional[Gameplan] = None,
        gameplan_f2: Optional[Gameplan] = None,
    ):
        self.fighter1 = fighter1
        self.fighter2 = fighter2
        self.config = config or FightConfig.standard_fight()
        self.verbose = verbose

        # GAMEPLAN-WIRE1: per-fighter tendency dial. Threaded to
        # select_action but not consumed this ship — SHIP2 activates.
        # Stored verbatim; None means "no gameplan", which select_action
        # currently treats identically to a neutral Gameplan().
        self._gameplan_f1 = gameplan_f1
        self._gameplan_f2 = gameplan_f2

        # Cornering bonuses (0.0 to 0.5 scale)
        # Affects between-round recovery and composure when hurt
        self.corner_bonus_f1 = max(0.0, min(0.5, corner_bonus_f1))
        self.corner_bonus_f2 = max(0.0, min(0.5, corner_bonus_f2))

        # Pre-fight stamina (set by fatigue from training camp).
        # Fresh fighters start at 100; tired fighters start lower.
        self.starting_stamina_f1 = starting_stamina_f1
        self.starting_stamina_f2 = starting_stamina_f2

        # Per-round stamina recovery penalty from fatigue level.
        # Mirrors get_cardio_recovery_penalty() bucketing:
        # FRESH=0, RESTED=0, READY=1, TIRED=2, EXHAUSTED=4
        def _fatigue_to_penalty(s: float) -> float:
            if s >= 95: return 0.0
            if s >= 88: return 0.0
            if s >= 78: return 1.0
            if s >= 65: return 2.0
            return 4.0
        self._fatigue_penalty_f1 = _fatigue_to_penalty(starting_stamina_f1)
        self._fatigue_penalty_f2 = _fatigue_to_penalty(starting_stamina_f2)
        
        # Initialize commentary system
        self.commentary = create_commentary_system(
            fighter1_name=fighter1.name,
            fighter2_name=fighter2.name,
            total_rounds=self.config.scheduled_rounds,
            is_title_fight=self.config.is_title_fight,
            exchanges_per_round=self.config.exchanges_per_round
        )
        
        # Fight state
        self.fighter1_state: Optional[FighterState] = None
        self.fighter2_state: Optional[FighterState] = None
        self.fight_state: Optional[FightState] = None
        
        # Round tracking
        self.current_round = 0
        self.round_stats: Dict[str, RoundStats] = {}
        self.all_round_stats: List[Dict[str, RoundStats]] = []
        self.round_scores: List[Tuple[int, int]] = []
        
        # Result tracking
        self.finished = False
        self.finish_result: Optional[Tuple[str, str]] = None  # (winner_id, method)
        self.finish_round: Optional[int] = None
        self.finish_exchange: Optional[int] = None
    
    def _init_fight(self):
        """Initialize fight state"""
        # Create fighter states
        self.fighter1_state = FighterState(
            fighter_id=self.fighter1.fighter_id,
            name=self.fighter1.name,
            health=100.0 + self.fighter1.chin * 0.5,
            stamina=self.starting_stamina_f1
        )

        self.fighter2_state = FighterState(
            fighter_id=self.fighter2.fighter_id,
            name=self.fighter2.name,
            health=100.0 + self.fighter2.chin * 0.5,
            stamina=self.starting_stamina_f2
        )
        
        # Create fight state
        self.fight_state = FightState(
            fighter1=self.fighter1_state,
            fighter2=self.fighter2_state,
            position=Position.STANDING_OPEN
        )
        
        self.finished = False
        self.finish_result = None
        self.all_round_stats = []
        self.round_scores = []
    
    def _init_round(self):
        """Initialize round state"""
        self.round_stats = {
            self.fighter1.fighter_id: RoundStats(),
            self.fighter2.fighter_id: RoundStats()
        }
        
        # Reset fighter round states (includes base stamina recovery)
        self.fighter1_state._current_round = self.current_round
        self.fighter2_state._current_round = self.current_round
        self.fighter1_state.new_round()
        self.fighter2_state.new_round()
        
        # === CORNER BONUS: Between-round recovery ===
        # Good corners help fighters recover more stamina and clear their head
        if self.corner_bonus_f1 > 0 and self.current_round > 1:
            # Bonus stamina recovery (up to +7.5 extra with max 0.5 bonus)
            bonus_stamina = 15 * self.corner_bonus_f1
            self.fighter1_state.stamina = min(100, self.fighter1_state.stamina + bonus_stamina)
            # Slight health recovery from corner work (cuts, ice, etc)
            bonus_health = 2 * self.corner_bonus_f1
            self.fighter1_state.health = min(
                100 + self.fighter1.chin * 0.5,  # Can't exceed starting health
                self.fighter1_state.health + bonus_health
            )
        
        if self.corner_bonus_f2 > 0 and self.current_round > 1:
            bonus_stamina = 15 * self.corner_bonus_f2
            self.fighter2_state.stamina = min(100, self.fighter2_state.stamina + bonus_stamina)
            bonus_health = 2 * self.corner_bonus_f2
            self.fighter2_state.health = min(
                100 + self.fighter2.chin * 0.5,
                self.fighter2_state.health + bonus_health
            )

        # Fatigue compounds through rounds — tired fighters recover
        # stamina more slowly between rounds.
        # get_cardio_recovery_penalty returns 0/1/2/4 by fatigue bucket.
        if hasattr(self, '_fatigue_penalty_f1'):
            self.fighter1_state.stamina = max(0.0,
                self.fighter1_state.stamina - self._fatigue_penalty_f1)
            self.fighter2_state.stamina = max(0.0,
                self.fighter2_state.stamina - self._fatigue_penalty_f2)

        # Reset fight state for new round
        self.fight_state.current_round = self.current_round
        self.fight_state.exchanges_this_round = 0
        self.fight_state.position = Position.STANDING_OPEN
        self.fight_state.top_fighter_id = None
        self.fight_state.cage_controller_id = None  # NEW
        self.fight_state.front_headlock_controller_id = None  # NEW
        self.fight_state.submission_active = False
    
    def _get_fighter_and_state(self, fighter_id: str) -> Tuple[FighterAttributes, FighterState]:
        """Get fighter attributes and state by ID"""
        if fighter_id == self.fighter1.fighter_id:
            return self.fighter1, self.fighter1_state
        return self.fighter2, self.fighter2_state
    
    def _get_opponent_and_state(self, fighter_id: str) -> Tuple[FighterAttributes, FighterState]:
        """Get opponent attributes and state"""
        if fighter_id == self.fighter1.fighter_id:
            return self.fighter2, self.fighter2_state
        return self.fighter1, self.fighter1_state
    
    def _determine_initiative(self) -> str:
        """Determine which fighter acts this exchange"""
        f1_init = self.fighter1.speed + random.randint(-10, 10)
        f2_init = self.fighter2.speed + random.randint(-10, 10)
        
        # Momentum bonus
        if self.fight_state.momentum_fighter_id == self.fighter1.fighter_id:
            f1_init += 5
        elif self.fight_state.momentum_fighter_id == self.fighter2.fighter_id:
            f2_init += 5
        
        # Position advantage
        if self.fight_state.top_fighter_id == self.fighter1.fighter_id:
            f1_init += 10
        elif self.fight_state.top_fighter_id == self.fighter2.fighter_id:
            f2_init += 10
        
        return self.fighter1.fighter_id if f1_init >= f2_init else self.fighter2.fighter_id
    
    def _simulate_exchange(self, exchange_num: int) -> Optional[Tuple[str, str]]:
        """
        Simulate a single exchange with commentary.
        
        Returns (winner_id, method) if fight ends, else None.
        """
        self.fight_state.exchanges_this_round = exchange_num
        self.fight_state.total_exchanges += 1
        
        # Track if there was meaningful ground action this exchange
        # (used to prevent referee standup during active ground fighting)
        self._ground_action_this_exchange = False
        
        # Handle active submission
        if self.fight_state.submission_active:
            self._ground_action_this_exchange = True  # Submission = activity
            return self._process_submission_exchange(exchange_num)
        
        # Determine who acts
        actor_id = self._determine_initiative()
        actor, actor_state = self._get_fighter_and_state(actor_id)
        defender, defender_state = self._get_opponent_and_state(actor_id)

        # GAMEPLAN-WIRE1: hand the actor's gameplan to select_action.
        # select_action currently ignores it (SHIP2 will consume the
        # aggression dial). None flows through unchanged so callers
        # that didn't pass a Gameplan get byte-identical behavior.
        _actor_gameplan = (self._gameplan_f1
                           if actor_id == self.fighter1.fighter_id
                           else self._gameplan_f2)

        # Select action
        action_type, action_data = select_action(
            actor, defender, self.fight_state, actor_state,
            gameplan=_actor_gameplan,
        )

        # ── Sambo chain — force immediate sub attempt ─────
        # When sambo set _sambo_chain on last exchange, the
        # NEXT exchange auto-routes into a position-appropriate
        # submission attempt before guard recovery fires.
        if getattr(actor_state, '_sambo_chain', False):
            actor_state._sambo_chain = False
            _pos = self.fight_state.position
            _forced_sub = None
            if _pos == Position.BACK_MOUNT:
                _forced_sub = SubmissionType.REAR_NAKED_CHOKE
            elif _pos == Position.MOUNT:
                _forced_sub = SubmissionType.ARMBAR
            elif _pos == Position.SIDE_CONTROL_TOP:
                _forced_sub = SubmissionType.KIMURA
            if _forced_sub is not None:
                action_type = "submission"
                action_data = _forced_sub

        # Execute action
        if action_type == "strike":
            return self._execute_strike(
                actor, defender, actor_state, defender_state,
                action_data, exchange_num
            )
        elif action_type == "grappling":
            return self._execute_grappling(
                actor, defender, actor_state, defender_state,
                action_data, exchange_num
            )
        elif action_type == "submission":
            self._ground_action_this_exchange = True  # Submission attempt = activity
            return self._execute_submission_attempt(
                actor, defender, actor_state, defender_state,
                action_data, exchange_num
            )
        
        return None
    
    def _execute_strike(
        self,
        attacker: FighterAttributes,
        defender: FighterAttributes,
        attacker_state: FighterState,
        defender_state: FighterState,
        strike: StrikeType,
        exchange_num: int
    ) -> Optional[Tuple[str, str]]:
        """Execute a strike and generate commentary"""
        # ── Adrenaline surge window decrement ─────────────
        # Survived-the-rock window: 3-exchange momentum burst,
        # decays back to 50 when the window closes.
        if getattr(attacker_state, '_surge_exchanges', 0) > 0:
            attacker_state._surge_exchanges -= 1
            if attacker_state._surge_exchanges == 0:
                attacker_state.momentum = max(
                    50, attacker_state.momentum - 25)

        # ── Sprawl counter window decrement ───────────────
        # Sprawl-and-brawl just defended a takedown; brief
        # momentum boost on the counter strike.
        if getattr(attacker_state, '_sprawl_counter', 0) > 0:
            attacker_state._sprawl_counter -= 1
            attacker_state.momentum = min(
                100, attacker_state.momentum + 20)

        # ── Counter Striker window — apply ───────────────
        # fight_iq = timing quality; speed = execution quality.
        # Both needed for elite counter striking.
        _counter_mult = 1.0
        if getattr(attacker_state, '_counter_window', 0) > 0:
            attacker_state._counter_window = 0
            _iq = getattr(attacker, 'fight_iq', 70)
            _spd = getattr(attacker, 'speed', 70)
            _iq_mult = (
                1.6 if _iq >= 85 else
                1.45 if _iq >= 75 else
                1.3)
            _spd_mod = (
                1.0 if _spd >= 75 else
                0.90 if _spd >= 65 else
                0.80)
            _counter_mult = _iq_mult * _spd_mod

        # ── Brawler counter — consume pending power ──────
        # Brawler just walked through a head strike; the
        # return shot carries extra power.
        _brawler_mult = getattr(
            attacker_state, '_brawler_counter', 1.0)
        if _brawler_mult > 1.0:
            attacker_state._brawler_counter = 1.0

        # Calculate success
        landed, was_counter = calculate_strike_success(
            attacker, defender, strike,
            attacker_state, defender_state, self.fight_state
        )
        
        damage = 0.0
        target_area = "head"
        caused_knockdown = False
        caused_rock = False

        if not landed:
            # ── Fight IQ: read and react ───────────────────
            # Any fighter can counter but IQ determines how
            # reliably they recognize the opening. Counter
            # strikers always set the window; others gate on
            # fight_iq tiers.
            _def_style_cw = str(getattr(
                defender.fighting_style, 'name', '')
                or defender.fighting_style or '').upper()
            _def_iq = getattr(defender, 'fight_iq', 70)
            _counter_set = False
            if 'COUNTER' in _def_style_cw:
                _counter_set = True
            elif _def_iq >= 85:
                _counter_set = random.random() < 0.45
            elif _def_iq >= 75:
                _counter_set = random.random() < 0.25
            elif _def_iq >= 65:
                _counter_set = random.random() < 0.10
            if _counter_set:
                defender_state._counter_window = 1

        if landed:
            # Calculate damage
            damage, target_area = calculate_strike_damage(
                attacker, defender, strike,
                attacker_state, defender_state, was_counter
            )

            # Use fight_integration specific multiplier — tuned separately from
            # fight_engine.DAMAGE_MULTIPLIER because the exchange loops differ
            damage = damage * FI_DAMAGE_MULTIPLIER

            # ── Strength KO amplification ─────────────────
            # Hard hitters punch through defense more.
            # Ngannou effect — str 70 = 1.0x, str 90 = 1.06x.
            if target_area == 'head':
                _str = getattr(attacker, 'strength', 70)
                _str_mod = 1.0 + max(0, _str - 70) * 0.003
                damage *= _str_mod

            # ── Muay Thai knee amplification ───────────────
            # Knee_head and knee_body bypass guard differently
            # from punches in clinch.
            _sv = strike.value if hasattr(
                strike, 'value') else str(strike)
            _att_style = str(getattr(
                attacker.fighting_style, 'name', '')
                or attacker.fighting_style or '').upper()
            if 'MUAY_THAI' in _att_style:
                if _sv == 'knee_head':
                    damage *= 1.30 * 1.10
                elif _sv in ('knee_body', 'knee_strike'):
                    damage *= 1.30

            # ── Counter Striker damage multiplier ──────────
            if _counter_mult > 1.0:
                damage *= _counter_mult

            # ── Brawler counter damage multiplier ──────────
            if _brawler_mult > 1.0:
                damage *= _brawler_mult

            # ── Karate patience power bonus ────────────────
            if (getattr(attacker_state,
                        '_karate_patience', False)
                    and target_area == 'head'):
                damage *= 1.40
                attacker_state._karate_patience = False

            # ── Point Fighter off the line — defender ──────
            # Defender moving on angles takes reduced damage.
            if getattr(defender_state,
                       '_movement_window', 0) > 0:
                defender_state._movement_window -= 1
                damage *= 0.80

            # ── Brawler walk-through — defender rolls with it ──
            _def_brawl_style = str(getattr(
                defender.fighting_style, 'name', '')
                or defender.fighting_style or '').upper()
            if ('BRAWLER' in _def_brawl_style
                    and target_area == 'head'):
                _b_chin = getattr(defender, 'chin', 70)
                _b_chance = (
                    0.25 if _b_chin >= 80 else
                    0.18 if _b_chin >= 70 else
                    0.10)
                if random.random() < _b_chance:
                    damage *= 0.75
                    _b_power = (
                        1.4 if _b_chin >= 80 else
                        1.3 if _b_chin >= 70 else
                        1.2)
                    defender_state._brawler_counter = _b_power

            # ── Point Fighter — set movement window on land ──
            _att_style_pf = str(getattr(
                attacker.fighting_style, 'name', '')
                or attacker.fighting_style or '').upper()
            if 'POINT' in _att_style_pf:
                attacker_state._movement_window = 2

            # Apply damage
            caused_knockdown, is_finish = defender_state.apply_damage(
                damage, target_area
            )

            # ── Body shot stamina drain ───────────────
            # Body work steals the opponent's breath.
            # Strategically pays off in later rounds.
            if target_area == 'body':
                defender_state.spend_stamina(damage * 0.4)

            # ── Clinch body accumulation ───────────────
            # Repeated body work in clinch forces stoppages.
            # Muay Thai specialty.
            _in_clinch_pos = (
                self.fight_state.position
                in CLINCH_POSITIONS)
            if target_area == 'body' and _in_clinch_pos:
                _prev_cb = getattr(
                    defender_state, '_clinch_body_acc', 0)
                _cb_rate = (
                    1.4 if 'MUAY_THAI' in _att_style
                    else 1.0)
                defender_state._clinch_body_acc = (
                    _prev_cb + damage * _cb_rate)
                if defender_state._clinch_body_acc >= 30:
                    _cb_tko = min(0.22,
                        (defender_state._clinch_body_acc
                         - 25) * 0.025)
                    _cb_tko *= max(0.4,
                        1 - getattr(defender,
                            'heart', 70) / 320
                        - getattr(defender,
                            'composure', 70) / 450)
                    if random.random() < _cb_tko:
                        method = "TKO (Body Shots)"
                        self._log_finish(
                            attacker.fighter_id,
                            method, exchange_num)
                        return (attacker.fighter_id, method)
            if self.fight_state.position not in CLINCH_POSITIONS:
                defender_state._clinch_body_acc = 0

            # ── Knockdown stamina tax ─────────────────
            # Standing back up after a KD is exhausting —
            # fighters are visibly slower after the canvas.
            if caused_knockdown:
                defender_state.spend_stamina(8)

            # ── GnP accumulation — dominant-position TKO ──
            _gnp_pos_check = str(getattr(
                self.fight_state, 'position', '')).upper()
            _in_gnp_pos = any(p in _gnp_pos_check
                for p in ('MOUNT', 'BACK_MOUNT',
                          'SIDE_CONTROL'))
            _att_gnp_style = str(getattr(
                attacker.fighting_style, 'name', '')
                or attacker.fighting_style or '').upper()
            _is_gnp = 'GROUND' in _att_gnp_style
            if (not is_finish
                    and _in_gnp_pos
                    and target_area == 'head'):
                _rate = 1.2 if _is_gnp else 1.0
                if 'MOUNT' in _gnp_pos_check:
                    _rate *= 1.1
                _prev_gnp = getattr(
                    defender_state, '_gnp_accumulation', 0)
                defender_state._gnp_accumulation = (
                    _prev_gnp + damage * _rate)
                if defender_state._gnp_accumulation >= 75:
                    _gnp_tko = min(0.22,
                        (defender_state._gnp_accumulation
                         - 70) * 0.025)
                    _gnp_tko *= max(0.35,
                        1 - getattr(defender, 'heart', 70) / 300
                        - getattr(defender, 'composure', 70) / 450)
                    if random.random() < _gnp_tko:
                        method = "TKO (Ground and Pound)"
                        self._log_finish(
                            attacker.fighter_id,
                            method, exchange_num)
                        return (attacker.fighter_id, method)
            if self.fight_state.position in STANDING_POSITIONS:
                defender_state._gnp_accumulation = 0

            # ── Leg kick TKO — accumulated leg damage ──────
            if (not is_finish and target_area == "legs"
                    and defender_state.damage.is_compromised_legs):
                _leg_tko_chance = min(0.15,
                    (defender_state.damage.leg_kicks_absorbed - 6) * 0.02)
                if defender_state.stamina < 50:
                    _leg_tko_chance *= 1.4
                if random.random() < _leg_tko_chance:
                    is_finish = True
                    method = "TKO (Leg Kicks)"
                    self._log_finish(attacker.fighter_id,
                                     method, exchange_num)
                    return (attacker.fighter_id, method)

            # ── Referee stoppage — unanswered shots while rocked ──
            if (not is_finish
                    and defender_state.is_rocked
                    and target_area == "head"):
                if not hasattr(defender_state, '_rocked_shots'):
                    defender_state._rocked_shots = 0
                defender_state._rocked_shots += 1
                _ref_chance = min(0.22,
                    defender_state._rocked_shots * 0.05)
                _ref_chance *= max(0.35,
                    1 - (defender.fight_iq / 250)
                      - (defender.heart / 350)
                      - (defender.composure / 400))
                if random.random() < _ref_chance:
                    method = "TKO (Referee Stoppage)"
                    self._log_finish(attacker.fighter_id,
                                     method, exchange_num)
                    return (attacker.fighter_id, method)

            # ── Rocked fighter in standup — grappler exploits ──
            if (not is_finish
                    and defender_state.is_rocked
                    and target_area == "head"
                    and self.fight_state.position in STANDING_POSITIONS):
                # Scenario A: wrestler shoots
                if attacker.takedowns >= 68:
                    _shoot = min(0.18,
                        (attacker.takedowns - 60) * 0.006)
                    _shoot *= max(0.8,
                        1 + (attacker.takedowns
                             - defender.takedown_defense) / 150)
                    if random.random() < _shoot:
                        self.fight_state.position = (
                            Position.BACK_MOUNT
                            if random.random() < 0.55
                            else Position.MOUNT
                        )
                        self.fight_state.top_fighter_id = (
                            attacker.fighter_id)
                # Scenario B: submission specialist takes back
                elif (attacker.submissions >= 65
                        and getattr(defender_state, '_rocked_shots', 0) >= 2):
                    _back = min(0.12,
                        (attacker.submissions - 60) * 0.004)
                    if random.random() < _back:
                        self.fight_state.position = Position.STANDING_BACK
                        self.fight_state.top_fighter_id = (
                            attacker.fighter_id)

            # === V7 FLASH KO SYSTEM ===
            # Big head shots can cause sudden KOs even without accumulating damage
            if (not is_finish and target_area == "head" and 
                damage >= FLASH_KO_DAMAGE_THRESHOLD):
                
                flash_ko_chance = (damage - FLASH_KO_DAMAGE_THRESHOLD) * FLASH_KO_BASE_CHANCE
                
                # Striker bonus (elite boxing or kicks)
                if attacker.boxing >= 85 or attacker.kicks >= 85:
                    flash_ko_chance += 0.022
                
                # Power bonus (high strength)
                if attacker.strength >= 85:
                    flash_ko_chance += 0.015
                
                # Hurt bonus (defender already rocked)
                if defender_state.is_rocked or defender_state.health < 40:
                    flash_ko_chance += 0.035
                
                # Cap the chance
                flash_ko_chance = min(flash_ko_chance, FLASH_KO_MAX_CHANCE)
                
                if random.random() < flash_ko_chance:
                    # Flash KO!
                    caused_knockdown = True
                    is_finish = True
                    defender_state.health = 0
            
            # === V7 TKO GNP SYSTEM ===
            # Referee stops fight when defender takes sustained damage from dominant position
            if (not is_finish and 
                self.fight_state.top_fighter_id == attacker.fighter_id and
                defender_state.health < TKO_GNP_HEALTH_THRESHOLD and
                self.fight_state.position in DOMINANT_POSITIONS):
                
                tko_chance = TKO_GNP_BASE_CHANCE
                
                # Rocked bonus
                if defender_state.is_rocked:
                    tko_chance += 0.03
                
                # Multiple knockdowns bonus
                if defender_state.knockdowns_this_round >= 2:
                    tko_chance += 0.04
                
                # GnP specialist bonus
                if attacker.top_control >= 85:
                    tko_chance += 0.02
                
                # Cap the chance
                tko_chance = min(tko_chance, TKO_GNP_MAX_CHANCE)
                
                if random.random() < tko_chance:
                    # TKO by GnP!
                    is_finish = True
            
            # === V7 TKO STANDING SYSTEM ===
            # Referee stops fight when fighter is badly hurt on the feet
            if (not is_finish and
                defender_state.is_rocked and
                defender_state.health < TKO_STANDING_HEALTH_THRESHOLD and
                self.fight_state.position in STANDING_POSITIONS):
                
                tko_standing_chance = TKO_STANDING_BASE_CHANCE
                
                # Very low health bonus
                if defender_state.health < 20:
                    tko_standing_chance += 0.05
                
                # Multiple knockdowns in round
                if defender_state.knockdowns_this_round >= 1:
                    tko_standing_chance += 0.04
                
                if random.random() < tko_standing_chance:
                    # Standing TKO!
                    is_finish = True
            
            # Mark ground action if strike landed on the ground
            # (prevents referee standup during active GNP)
            if (self.fight_state.position not in STANDING_POSITIONS and
                self.fight_state.position not in CLINCH_POSITIONS):
                self._ground_action_this_exchange = True
            
            # Update stats
            stats = self.round_stats[attacker.fighter_id]
            stats.significant_strikes_attempted += 1
            stats.significant_strikes_landed += 1
            stats.damage_dealt += damage
            
            if target_area == "head":
                stats.head_strikes_landed += 1
            elif target_area == "body":
                stats.body_strikes_landed += 1
            elif target_area == "legs":
                stats.leg_strikes_landed += 1
            
            # NOTE: rocked/knockdown is already handled inside FighterState.apply_damage()
            # in fight_engine.py — no duplicate check needed here.

            # Check for finish
            if is_finish:
                # Named specialty finishes — specific strike logged
                # so records and commentary surface the exact KO type
                _sv = strike.value if hasattr(strike, 'value') else str(strike)
                _specialty_map = {
                    "flying_knee":        "KO (Flying Knee)",
                    "wheel_kick":         "KO (Wheel Kick)",
                    "elbow_spinning":     "KO (Spinning Elbow)",
                    "head_kick":          "KO (Head Kick)",
                    "knee_head":          "KO (Knee)",
                    "spinning_back_kick": "KO (Spinning Back Kick)",
                    "superman_punch":     "KO (Superman Punch)",
                    "body_kick":          "TKO (Body Shot)",
                    "knee_body":          "TKO (Body Shot)",
                    "front_kick":         "TKO (Body Shot)",
                }
                if defender_state.health <= 0:
                    method = _specialty_map.get(_sv, "KO")
                else:
                    if target_area == "body":
                        method = _specialty_map.get(_sv, "TKO (Body Shot)")
                    else:
                        method = "TKO"
                self._log_finish(attacker.fighter_id, method, exchange_num)
                return (attacker.fighter_id, method)
            
            # Handle knockdown
            if caused_knockdown:
                stats.knockdowns += 1
                defender_state.knockdowns_this_round += 1
                defender_state.knockdowns_total += 1
                self.fight_state.position = Position.KNOCKDOWN_STANDING
                self.fight_state.top_fighter_id = attacker.fighter_id
                
                # Log knockdown
                self.commentary.log_event(
                    action_type=ActionType.KNOCKDOWN,
                    actor=attacker.name,
                    target=defender.name,
                    action=strike.value,
                    success=True,
                    damage=damage,
                    exchange_num=exchange_num
                )
        else:
            # Miss - update attempt
            self.round_stats[attacker.fighter_id].significant_strikes_attempted += 1
        
        # Log strike (if not already logged as knockdown)
        if not caused_knockdown:
            action_type = strike_to_action_type(strike)
            # Determine if this is a ground strike for commentary
            is_ground_strike = (
                self.fight_state.position not in STANDING_POSITIONS and
                self.fight_state.position not in CLINCH_POSITIONS
            )
            self.commentary.log_event(
                action_type=action_type,
                actor=attacker.name,
                target=defender.name,
                action=strike.value,
                success=landed,
                damage=damage if landed else 0.0,
                exchange_num=exchange_num,
                is_ground=is_ground_strike,
                target_health=defender_state.health if landed else None,
                position=self.fight_state.position.value
            )
        
        # Spend stamina
        props = STRIKE_PROPERTIES.get(strike, (5, 0.02, 4, "head"))
        attacker_state.spend_stamina(props[2])
        
        # Update momentum
        if landed and damage > 8:
            self.fight_state.momentum_fighter_id = attacker.fighter_id
            attacker_state.momentum = min(100, attacker_state.momentum + 10)
            defender_state.momentum = max(0, defender_state.momentum - 10)
        
        return None
    
    def _execute_grappling(
        self,
        attacker: FighterAttributes,
        defender: FighterAttributes,
        attacker_state: FighterState,
        defender_state: FighterState,
        action: GrapplingAction,
        exchange_num: int
    ) -> Optional[Tuple[str, str]]:
        """Execute a grappling action and generate commentary"""
        # Calculate success
        success = calculate_grappling_success(
            attacker, defender, action,
            attacker_state, defender_state, self.fight_state
        )
        
        old_position = self.fight_state.position
        new_position = None
        
        if success:
            # Apply position change
            new_position = apply_position_change(
                self.fight_state, action, attacker.fighter_id, True
            )
            
            # Mark ground action for successful grappling
            # (prevents referee standup during active wrestling/BJJ)
            if new_position and new_position not in STANDING_POSITIONS:
                self._ground_action_this_exchange = True
            
            # Update stats for takedowns
            takedown_actions = {
                GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG,
                GrapplingAction.BODY_LOCK_TAKEDOWN, GrapplingAction.HIP_TOSS,
                GrapplingAction.TRIP, GrapplingAction.SLAM, GrapplingAction.SUPLEX
            }
            
            if action in takedown_actions:
                self.round_stats[attacker.fighter_id].takedowns_attempted += 1
                self.round_stats[attacker.fighter_id].takedowns_landed += 1

                # ── Takedown impact stamina drain ─────
                # Scramble, impact, position recovery —
                # the defender's gas tank takes a hit.
                defender_state.spend_stamina(8)

                # Slam damage
                if action == GrapplingAction.SLAM:
                    slam_damage = 5 + attacker.strength * 0.1
                    defender_state.apply_damage(slam_damage, "body")

                # ── Sambo/Judo throw-to-position routing ──
                # fight_iq + takedowns determines landing.
                # Elite skill = almost always back mount.
                _throw_style = str(getattr(
                    attacker.fighting_style, 'name', '')
                    or attacker.fighting_style or '').upper()
                _is_sambo = 'SAMBO' in _throw_style
                _is_judo = 'JUDO' in _throw_style
                if _is_sambo or _is_judo:
                    _td = getattr(attacker, 'takedowns', 70)
                    _iq = getattr(attacker, 'fight_iq', 70)
                    _pos_skill = (
                        _td * 0.6 + _iq * 0.4) / 100
                    if _is_judo:
                        _back_mount_pct = min(0.88,
                            0.70 + (_pos_skill - 0.70) * 0.60)
                        _side_ctrl_pct = min(0.10,
                            0.20 - (_pos_skill - 0.70) * 0.30)
                    else:
                        _back_mount_pct = min(0.82,
                            0.60 + (_pos_skill - 0.65) * 0.55)
                        _side_ctrl_pct = 0.30
                    _r = random.random()
                    if _r < _back_mount_pct:
                        new_pos = Position.BACK_MOUNT
                    elif _r < _back_mount_pct + _side_ctrl_pct:
                        new_pos = Position.SIDE_CONTROL_TOP
                    else:
                        new_pos = Position.FULL_GUARD_TOP
                    self.fight_state.position = new_pos
                    self.fight_state.top_fighter_id = (
                        attacker.fighter_id)
                    new_position = new_pos

                    # ── Sambo immediate sub chain ─────────
                    # Sambo chains takedown directly into sub.
                    if (_is_sambo
                            and getattr(attacker,
                                'submissions', 0) >= 65):
                        _chain_chance = (
                            0.35 if _td >= 85 and _iq >= 75
                            else 0.25 if _td >= 80
                            else 0.22 if _td >= 75
                            else 0.12)
                        if random.random() < _chain_chance:
                            attacker_state._sambo_chain = True
        else:
            # Failed attempt
            if action in {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG}:
                self.round_stats[attacker.fighter_id].takedowns_attempted += 1
                # ── Counter off the sprawl ────────────────
                # Sprawl-and-brawl fighters get a brief counter
                # window after successfully defending a takedown.
                _s_style = str(getattr(
                    defender.fighting_style, 'name', '')
                    or defender.fighting_style or '')
                if 'SPRAWL' in _s_style.upper():
                    defender_state._sprawl_counter = 2
        
        # Log grappling action with new position if applicable
        action_type = grappling_to_action_type(action)
        position_str = new_position.value if new_position else None
        self.commentary.log_event(
            action_type=action_type,
            actor=attacker.name,
            target=defender.name,
            action=action.value,
            success=success,
            damage=0.0,
            exchange_num=exchange_num,
            new_position=position_str
        )
        
        # Spend stamina (grappling is tiring)
        attacker_state.spend_stamina(5)
        if not success:
            attacker_state.spend_stamina(3)  # Extra cost for failed attempt

        # Update control time
        if success and new_position in DOMINANT_POSITIONS:
            self.round_stats[attacker.fighter_id].control_time += 1.0

        # Bug V — any grappling resolved on the ground counts as
        # activity (success or fail). Was: only success+position-change
        # flagged. Caused referee standup during active defensive
        # grappling and maintained dominant control.
        if self.fight_state.position not in STANDING_POSITIONS:
            self._ground_action_this_exchange = True

        return None

    def _execute_submission_attempt(
        self,
        attacker: FighterAttributes,
        defender: FighterAttributes,
        attacker_state: FighterState,
        defender_state: FighterState,
        submission: SubmissionType,
        exchange_num: int
    ) -> Optional[Tuple[str, str]]:
        """Execute a submission attempt"""
        # Attempt submission
        locked_in, finished, progress = attempt_submission(
            attacker, defender, submission,
            attacker_state, defender_state, self.fight_state
        )

        self.round_stats[attacker.fighter_id].submission_attempts += 1

        # Bug V — submission attempts are always activity, even when
        # they don't lock in. Was: only active submission flagged.
        self._ground_action_this_exchange = True
        
        if locked_in:
            # Start submission sequence
            self.fight_state.submission_active = True
            self.fight_state.submission_type = submission
            self.fight_state.submission_attacker_id = attacker.fighter_id
            self.fight_state.submission_progress = progress
            
            # Log attempt
            self.commentary.log_event(
                action_type=ActionType.SUBMISSION,
                actor=attacker.name,
                target=defender.name,
                action=submission.value,
                success=True,
                exchange_num=exchange_num
            )
            
            if finished:
                self._log_finish(attacker.fighter_id, f"Submission ({submission.value})", exchange_num)
                return (attacker.fighter_id, "Submission", submission.value)
        else:
            # Failed to lock in
            self.commentary.log_event(
                action_type=ActionType.SUBMISSION,
                actor=attacker.name,
                target=defender.name,
                action=submission.value,
                success=False,
                exchange_num=exchange_num
            )
        
        attacker_state.spend_stamina(6)
        
        return None
    
    def _process_submission_exchange(self, exchange_num: int) -> Optional[Tuple[str, str]]:
        """Process an exchange during active submission"""
        attacker_id = self.fight_state.submission_attacker_id
        attacker, attacker_state = self._get_fighter_and_state(attacker_id)
        defender, defender_state = self._get_opponent_and_state(attacker_id)
        
        escaped, finished = process_submission_progress(
            attacker, defender,
            attacker_state, defender_state,
            self.fight_state, self.config
        )
        
        if finished:
            sub_name = self.fight_state.submission_type.value
            self._log_finish(attacker_id, f"Submission ({sub_name})", exchange_num)
            return (attacker_id, "Submission", sub_name)
        
        if escaped:
            # ── Capture drama context BEFORE clearing state ──────
            _sub_type = self.fight_state.submission_type
            _sub_name = (_sub_type.value if _sub_type
                         else 'submission')
            _progress = self.fight_state.submission_progress or 0.0
            _finish_threshold = (
                self.config.submission_progress_to_finish or 70.0)
            _progress_pct = (_progress / _finish_threshold
                             if _finish_threshold else 0.0)

            # Tier the escape by how close to finish it was.
            # 0.85+ = near-tap escape (Sandman moment),
            # 0.55+ = got tight,
            # else  = flat deflection.
            if _progress_pct >= 0.85:
                _stage = "escape_dramatic"
            elif _progress_pct >= 0.55:
                _stage = "escape_tight"
            else:
                _stage = "escape"

            # Get formatted commentary direct from generator so the
            # custom stage routes to the right pool. Append to log
            # manually since log_event's routing doesn't know about
            # stage-tiered escapes.
            # Templates use {actor}=submission attempter, {target}=the
            # one defending/escaping ("{target} defends ... brilliantly").
            # Pass attacker.name as actor and defender.name as target so
            # the commentary names the right fighter as the escaper.
            try:
                _escape_text = self.commentary.generate_submission_commentary(
                    actor=attacker.name,
                    target=defender.name,
                    move=_sub_name,
                    stage=_stage,
                )
                if _escape_text:
                    self.commentary.commentary_log.append(_escape_text)
            except Exception:
                pass

            # Log event for stats / event_log. log_event routes ESCAPE
            # through generate_position_commentary, whose ESCAPE_TEMPLATES
            # use {actor} for the escaper — so pass defender.name (the
            # one who got out) as actor here. action="escape" (not
            # "escape_<sub>") so the routing matches the escape template
            # pool instead of falling to the generic "advances to a
            # better position" pool.
            try:
                self.commentary.log_event(
                    action_type=ActionType.ESCAPE,
                    actor=defender.name,
                    target=attacker.name,
                    action="escape",
                    success=True,
                    damage=0.0,
                    exchange_num=exchange_num,
                )
            except Exception:
                pass

            self.fight_state.submission_active = False
            self.fight_state.submission_type = None
            self.fight_state.submission_attacker_id = None
            self.fight_state.submission_progress = 0.0
            self.fight_state.submission_escape_progress = 0.0

        return None
    
    def _log_finish(self, winner_id: str, method: str, exchange_num: int):
        """Log a fight finish with guaranteed dramatic buildup"""
        winner, _ = self._get_fighter_and_state(winner_id)
        loser, _ = self._get_opponent_and_state(winner_id)
        
        # === GUARANTEED FINISH BUILDUP ===
        # Generate dramatic buildup before the finish call
        # This ensures finishes never feel abrupt
        method_lower = method.lower()
        
        if "ko" in method_lower or "tko" in method_lower:
            # Full dramatic sequence for KO/TKO
            # Uses existing FINISH_SEQUENCE templates
            self.commentary.generate_full_finish_sequence(winner.name, loser.name)
        elif "submission" in method_lower:
            # Shorter buildup for submissions (they have their own drama)
            # Just add the "locked in tight" moment
            sub_buildup = [
                f"{winner.name} has it LOCKED IN! {loser.name} is in DEEP!",
                f"The submission is TIGHT! {loser.name} has nowhere to go!",
                f"{loser.name} is caught! This could be it!",
                f"{winner.name} cranks the hold! TAP OR SNAP!",
            ]
            self.commentary.commentary_log.append(random.choice(sub_buildup))
        
        # Now log the actual finish event
        self.commentary.log_event(
            action_type=ActionType.FINISH,
            actor=winner.name,
            target=loser.name,
            action=method,
            success=True,
            exchange_num=exchange_num
        )
        
        self.finished = True
        self.finish_result = (winner_id, method)
        self.finish_round = self.current_round
        self.finish_exchange = exchange_num
    
    def _simulate_round(self) -> Optional[Tuple[str, str]]:
        """Simulate a complete round"""
        self.current_round += 1
        self._init_round()
        
        # Start round commentary
        self.commentary.start_round(self.current_round)
        
        # Simulate exchanges
        for exchange in range(1, self.config.exchanges_per_round + 1):
            result = self._simulate_exchange(exchange)
            
            if result:
                # IMPORTANT: Store round stats BEFORE returning on a finish
                # Otherwise stats will be 0 for fights that end mid-round
                self.all_round_stats.append({
                    self.fighter1.fighter_id: self.round_stats[self.fighter1.fighter_id],
                    self.fighter2.fighter_id: self.round_stats[self.fighter2.fighter_id]
                })
                self.finish_round = self.current_round
                self.finish_exchange = exchange
                return result
            
            # Stamina recovery
            self.fighter1_state.recover_stamina(0.5)
            self.fighter2_state.recover_stamina(0.5)
            
            # NOTE: Health regain happens per-ROUND in FighterState.new_round()
            # (fight_engine.py lines 520-523) - corner work, catching breath, etc.
            # Per-exchange regain was removed to fix double-healing bug.
            
            # === CONTROL TIME TRACKING (per exchange) ===
            # Ground control: top fighter accumulates control time
            if self.fight_state.is_ground and self.fight_state.top_fighter_id:
                self.round_stats[self.fight_state.top_fighter_id].ground_control_time += 1.0
                self.round_stats[self.fight_state.top_fighter_id].control_time += 1.0
            # Clinch control: cage controller accumulates control time
            elif self.fight_state.is_clinch:
                if self.fight_state.cage_controller_id:
                    self.round_stats[self.fight_state.cage_controller_id].clinch_control_time += 1.0
                    self.round_stats[self.fight_state.cage_controller_id].control_time += 1.0
            
            # Rock duration countdown
            # === CORNER BONUS: Composure help when rocked ===
            # Good corners help fighters recover from being hurt faster
            if self.fighter1_state.is_rocked:
                # Base countdown is 1, corner bonus adds chance for extra recovery
                recovery = 1
                if self.corner_bonus_f1 > 0 and random.random() < self.corner_bonus_f1:
                    recovery += 1  # Corner helps clear their head faster
                self.fighter1_state.rock_duration -= recovery
                if self.fighter1_state.rock_duration <= 0:
                    self.fighter1_state.is_rocked = False
                    # ── Survived the storm — adrenaline surge ──
                    # ~12% chance: fighter who survives being rocked
                    # gets a brief momentum burst. "Hurt and dangerous."
                    if random.random() < 0.12:
                        self.fighter1_state.momentum = min(
                            100, self.fighter1_state.momentum + 30)
                        self.fighter1_state._surge_exchanges = 3

            if self.fighter2_state.is_rocked:
                recovery = 1
                if self.corner_bonus_f2 > 0 and random.random() < self.corner_bonus_f2:
                    recovery += 1
                self.fighter2_state.rock_duration -= recovery
                if self.fighter2_state.rock_duration <= 0:
                    self.fighter2_state.is_rocked = False
                    if random.random() < 0.12:
                        self.fighter2_state.momentum = min(
                            100, self.fighter2_state.momentum + 30)
                        self.fighter2_state._surge_exchanges = 3
            
            # Referee standup check - only if on the ground
            if (self.fight_state.position not in STANDING_POSITIONS and
                self.fight_state.position not in CLINCH_POSITIONS):
                
                # Check if there was meaningful ground action this exchange
                # If yes, reset inactivity counter (active fighting)
                # If no, increment inactivity counter
                if getattr(self, '_ground_action_this_exchange', False):
                    # Active ground fighting - reset inactivity
                    self.fight_state.ground_inactivity = 0
                else:
                    # No meaningful action - increment inactivity.
                    # Bug V — dominant positions count as half-activity:
                    # holding back mount / mount / side control is real
                    # work even without a flashy transition this exchange.
                    if self.fight_state.position in DOMINANT_POSITIONS:
                        self.fight_state.ground_inactivity += 0.5
                    else:
                        self.fight_state.ground_inactivity += 1

                    if self.fight_state.ground_inactivity >= self.config.standup_threshold:
                        # Log the referee standup
                        self.commentary.log_event(
                            action_type=ActionType.STAND_UP,
                            actor="Referee",
                            target="",
                            action="ref_standup",
                            success=True,
                            damage=0.0,
                            exchange_num=exchange
                        )
                        self.fight_state.position = Position.STANDING_OPEN
                        self.fight_state.top_fighter_id = None
                        self.fight_state.ground_inactivity = 0
        
        # ── Between-round stoppages ──────────────────────
        # Doctor, corner, cut stoppages. Rare by design.
        # Only fires if another round remains.
        if self.current_round < self.config.scheduled_rounds:
            for _ftr, _ftr_state, _opp in [
                (self.fighter1, self.fighter1_state, self.fighter2),
                (self.fighter2, self.fighter2_state, self.fighter1),
            ]:
                _stop = None

                # Cut stoppage
                if _ftr_state.damage.cuts >= 3:
                    _cc = min(0.35,
                        (_ftr_state.damage.cuts - 2) * 0.08)
                    _cc *= max(0.4, 1 - (_ftr.heart / 200))
                    if random.random() < _cc:
                        _stop = "TKO (Doctor Stoppage - Cuts)"

                # Doctor stoppage
                if (not _stop
                        and _ftr_state.health < 28
                        and _ftr_state.damage.head > 55):
                    _dc = min(0.14,
                        (55 - _ftr_state.health) * 0.003)
                    _dc *= max(0.5, 1 - (_ftr.heart / 250))
                    if getattr(_ftr_state, 'chin_compromised', False):
                        _dc *= 1.35
                    if random.random() < _dc:
                        _stop = "TKO (Doctor Stoppage)"

                # Corner stoppage (round 2+, 2+ knockdowns)
                if (not _stop
                        and self.current_round >= 2
                        and _ftr_state.health < 22
                        and getattr(_ftr_state, 'knockdowns_total', 0) >= 2):
                    _corn = min(0.18,
                        (getattr(_ftr_state, 'knockdowns_total', 0) - 1)
                        * 0.06)
                    _corn *= max(0.3, 1 - (_ftr.heart / 300))
                    if random.random() < _corn:
                        _stop = "TKO (Corner Stoppage)"

                if _stop:
                    self._log_finish(
                        _opp.fighter_id, _stop,
                        self.config.exchanges_per_round)
                    return (_opp.fighter_id, _stop)

        # Score the round
        # NOTE: knockdowns_this_round tracks knockdowns SUFFERED, but score_round
        # expects knockdowns INFLICTED. So we swap: f2's suffered = f1's inflicted
        score1, score2 = score_round(
            self.round_stats[self.fighter1.fighter_id],
            self.round_stats[self.fighter2.fighter_id],
            self.fighter2_state.knockdowns_this_round,  # KDs inflicted BY f1 (suffered by f2)
            self.fighter1_state.knockdowns_this_round   # KDs inflicted BY f2 (suffered by f1)
        )
        
        self.round_scores.append((score1, score2))
        
        # Store round stats
        self.all_round_stats.append({
            self.fighter1.fighter_id: self.round_stats[self.fighter1.fighter_id],
            self.fighter2.fighter_id: self.round_stats[self.fighter2.fighter_id]
        })
        
        # End round commentary - pass control time data for accurate round description
        control_time_data = {
            self.fighter1.name: self.round_stats[self.fighter1.fighter_id].control_time,
            self.fighter2.name: self.round_stats[self.fighter2.fighter_id].control_time
        }
        self.commentary.end_round(score1, score2, control_time_data)
        
        return None
    
    def simulate(self) -> NarratedFightResult:
        """
        Simulate the complete fight with commentary.
        
        Returns a NarratedFightResult with full stats and narrative.
        """
        self._init_fight()
        
        # Simulate rounds
        for round_num in range(1, self.config.scheduled_rounds + 1):
            result = self._simulate_round()
            
            if result:
                winner_id, method, *_sub_extra = result
                _sub_type_str = _sub_extra[0] if _sub_extra else ""
                return self._build_finish_result(winner_id, method, _sub_type_str)
        
        # Decision
        return self._build_decision_result()
    
    def _build_finish_result(self, winner_id: str, method: str, sub_type: str = "") -> NarratedFightResult:
        """Build result for a finish"""
        winner, winner_state = self._get_fighter_and_state(winner_id)
        loser, loser_state = self._get_opponent_and_state(winner_id)
        
        time_str = self.commentary.get_time_str(
            self.finish_exchange, 
            self.config.exchanges_per_round
        )
        
        # Build stats
        f1_stats = []
        f2_stats = []
        for round_stats in self.all_round_stats:
            f1_stats.append(round_stats[self.fighter1.fighter_id].to_dict())
            f2_stats.append(round_stats[self.fighter2.fighter_id].to_dict())
        
        # Get commentary output
        fight_narrative = self.commentary.get_fight_narrative(
            winner=winner.name,
            method=method
        )
        
        # Determine bonuses
        performance_bonus = self.finish_round <= 2  # Early finish
        total_kd = sum(
            rs[winner_id].knockdowns 
            for rs in self.all_round_stats 
            if winner_id in rs
        )
        if total_kd >= 2:
            performance_bonus = True
        
        return NarratedFightResult(
            winner_id=winner_id,
            winner_name=winner.name,
            loser_id=loser.fighter_id,
            loser_name=loser.name,
            method=method,
            sub_type=sub_type,
            finish_round=self.finish_round,
            finish_time=time_str,
            total_rounds=self.current_round,
            fighter1_stats=f1_stats,
            fighter2_stats=f2_stats,
            fighter1_final_health=self.fighter1_state.health,
            fighter2_final_health=self.fighter2_state.health,
            round_summaries=[s.to_dict() if hasattr(s, 'to_dict') else {} 
                           for s in self.commentary.round_summaries],
            key_moments=[e.to_dict() for e in self.commentary.get_key_moments()],
            full_commentary=self.commentary.get_full_commentary(),
            fight_narrative=fight_narrative,
            performance_bonus=performance_bonus
        )
    
    def _build_decision_result(self) -> NarratedFightResult:
        """Build result for a decision"""
        # Tally scores
        total1 = sum(s[0] for s in self.round_scores)
        total2 = sum(s[1] for s in self.round_scores)
        
        # Simulate 3 judges with slight variance
        judge_scores = []
        judge_winners = []
        
        for _ in range(3):
            j1, j2 = total1, total2
            # Small variance per judge
            if random.random() < 0.1:
                variance = random.choice([-1, 1])
                if random.random() < 0.5:
                    j1 += variance
                else:
                    j2 += variance
            
            judge_scores.append((j1, j2))
            if j1 > j2:
                judge_winners.append(self.fighter1.fighter_id)
            elif j2 > j1:
                judge_winners.append(self.fighter2.fighter_id)
            else:
                judge_winners.append(None)
        
        # Determine winner
        f1_wins = judge_winners.count(self.fighter1.fighter_id)
        f2_wins = judge_winners.count(self.fighter2.fighter_id)
        
        if f1_wins >= 2:
            winner_id = self.fighter1.fighter_id
        elif f2_wins >= 2:
            winner_id = self.fighter2.fighter_id
        else:
            winner_id = None  # Draw
        
        # Decision type
        if winner_id:
            if f1_wins == 3 or f2_wins == 3:
                decision_type = "Unanimous"
            elif judge_winners.count(None) > 0:
                decision_type = "Majority"
            else:
                decision_type = "Split"
        else:
            decision_type = None
        
        # Build stats
        f1_stats = []
        f2_stats = []
        for round_stats in self.all_round_stats:
            f1_stats.append(round_stats[self.fighter1.fighter_id].to_dict())
            f2_stats.append(round_stats[self.fighter2.fighter_id].to_dict())
        
        # Get names
        if winner_id:
            winner, _ = self._get_fighter_and_state(winner_id)
            loser, _ = self._get_opponent_and_state(winner_id)
            winner_name = winner.name
            loser_id = loser.fighter_id
            loser_name = loser.name
            method = f"{decision_type} Decision"
        else:
            winner_name = self.fighter1.name
            loser_id = self.fighter2.fighter_id
            loser_name = self.fighter2.name
            method = "Draw"
        
        # Log decision
        self.commentary.log_event(
            action_type=ActionType.FINISH,
            actor=winner_name,
            target=loser_name,
            action=method,
            success=True,
            exchange_num=self.config.exchanges_per_round
        )
        
        fight_narrative = self.commentary.get_fight_narrative(
            winner=winner_name if winner_id else None,
            method=method
        )
        
        # Fight of the night check
        total_strikes = sum(
            rs[self.fighter1.fighter_id].significant_strikes_landed +
            rs[self.fighter2.fighter_id].significant_strikes_landed
            for rs in self.all_round_stats
        )
        total_damage = sum(
            rs[self.fighter1.fighter_id].damage_dealt +
            rs[self.fighter2.fighter_id].damage_dealt
            for rs in self.all_round_stats
        )
        fight_of_night = total_strikes > 50 and total_damage > 100
        
        return NarratedFightResult(
            winner_id=winner_id,
            winner_name=winner_name,
            loser_id=loser_id,
            loser_name=loser_name,
            method=method,
            finish_round=None,
            finish_time=None,
            total_rounds=self.config.scheduled_rounds,
            judge_scores=judge_scores,
            decision_type=decision_type,
            fighter1_stats=f1_stats,
            fighter2_stats=f2_stats,
            fighter1_final_health=self.fighter1_state.health,
            fighter2_final_health=self.fighter2_state.health,
            round_summaries=[s.to_dict() if hasattr(s, 'to_dict') else {}
                           for s in self.commentary.round_summaries],
            key_moments=[e.to_dict() for e in self.commentary.get_key_moments()],
            full_commentary=self.commentary.get_full_commentary(),
            fight_narrative=fight_narrative,
            fight_of_night=fight_of_night
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def simulate_narrated_fight(
    fighter1: FighterAttributes,
    fighter2: FighterAttributes,
    rounds: int = 3,
    is_title_fight: bool = False,
    is_main_event: bool = False,
    starting_stamina_f1: float = 100.0,
    starting_stamina_f2: float = 100.0,
    config: 'FightConfig' = None,
    gameplan_f1: Optional[Gameplan] = None,
    gameplan_f2: Optional[Gameplan] = None,
) -> NarratedFightResult:
    """
    Simulate a fight with full commentary.
    If config is provided, use it directly (preserves bridge
    per-fight tuning — damage_multiplier, thresholds, etc).
    Otherwise build config from fight type flags.

    GAMEPLAN-WIRE1: gameplan_f1 / gameplan_f2 are threaded to the
    simulator and on to select_action, but are not yet consumed
    (SHIP2 will activate the AGGRESSION dial). Defaults None → no-op.
    """
    if config is None:
        if is_title_fight:
            config = FightConfig.championship_fight()
        elif is_main_event:
            config = FightConfig.main_event()
        else:
            config = FightConfig.standard_fight()

    if rounds == 5:
        config.scheduled_rounds = 5

    simulator = NarratedFightSimulator(
        fighter1, fighter2, config,
        starting_stamina_f1=starting_stamina_f1,
        starting_stamina_f2=starting_stamina_f2,
        gameplan_f1=gameplan_f1,
        gameplan_f2=gameplan_f2,
    )
    return simulator.simulate()


def quick_narrated_fight(
    f1_overall: int,
    f2_overall: int,
    f1_name: str = "Fighter One",
    f2_name: str = "Fighter Two",
    rounds: int = 3,
    f1_style: FightingStyle = FightingStyle.BALANCED,
    f2_style: FightingStyle = FightingStyle.BALANCED
) -> NarratedFightResult:
    """
    Quick fight simulation with generated fighters.
    
    Args:
        f1_overall: Fighter 1 overall rating (1-100)
        f2_overall: Fighter 2 overall rating (1-100)
        f1_name: Fighter 1 name
        f2_name: Fighter 2 name
        rounds: Number of rounds
        f1_style: Fighter 1 fighting style
        f2_style: Fighter 2 fighting style
        
    Returns:
        NarratedFightResult
    """
    fighter1 = FighterAttributes(
        fighter_id="fighter_1",
        name=f1_name,
        # Physical (5)
        strength=f1_overall, speed=f1_overall, cardio=f1_overall, 
        chin=f1_overall, recovery=f1_overall,
        # Striking (4)
        boxing=f1_overall, kicks=f1_overall, clinch_striking=f1_overall,
        striking_defense=f1_overall,
        # Grappling (5)
        takedowns=f1_overall, takedown_defense=f1_overall,
        top_control=f1_overall, submissions=f1_overall, guard=f1_overall,
        # Clinch (1)
        clinch_control=f1_overall,
        # Mental (3)
        heart=f1_overall, fight_iq=f1_overall, composure=f1_overall,
        fighting_style=f1_style
    )
    
    fighter2 = FighterAttributes(
        fighter_id="fighter_2",
        name=f2_name,
        # Physical (5)
        strength=f2_overall, speed=f2_overall, cardio=f2_overall, 
        chin=f2_overall, recovery=f2_overall,
        # Striking (4)
        boxing=f2_overall, kicks=f2_overall, clinch_striking=f2_overall,
        striking_defense=f2_overall,
        # Grappling (5)
        takedowns=f2_overall, takedown_defense=f2_overall,
        top_control=f2_overall, submissions=f2_overall, guard=f2_overall,
        # Clinch (1)
        clinch_control=f2_overall,
        # Mental (3)
        heart=f2_overall, fight_iq=f2_overall, composure=f2_overall,
        fighting_style=f2_style
    )
    
    return simulate_narrated_fight(fighter1, fighter2, rounds=rounds)


def get_fight_summary(result: NarratedFightResult) -> str:
    """Get a one-line fight summary"""
    return result.get_summary()


def print_fight_narrative(result: NarratedFightResult):
    """Print the full fight narrative"""
    print("=" * 60)
    print(result.get_summary())
    print("=" * 60)
    print()
    print(result.fight_narrative)
    print()
    if result.fight_of_night:
        print("ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â  FIGHT OF THE NIGHT CANDIDATE")
    if result.performance_bonus:
        print(f"ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â  PERFORMANCE OF THE NIGHT: {result.winner_name}")
