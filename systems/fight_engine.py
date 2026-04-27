# simulation/fight_engine.py
# Module 14: Comprehensive Fight Engine
# Lines: ~2550
#
# A thorough MMA fight simulation with detailed positions,
# strikes, submissions, counters, and realistic outcomes.
# Integrated with judges.py for realistic decision scoring.
#
# BALANCE PATCH v2.0 - December 2024
# - Wrestlers/grapplers now use clinch-first strategy vs strikers
# - Clinch takedowns are more reliable than distance shots
# - Muay Thai fighters dominate in clinch striking
# - Sambo fighters combine wrestling + submissions effectively
# - Added upset variance for underdogs
# - Improved submission rates and escape difficulty

"""
Cage Dynasty - Fight Engine

A comprehensive MMA fight simulation featuring:
- 20+ ground/standing positions with realistic transitions
- Detailed strike types (jabs, crosses, hooks, kicks, elbows, knees)
- Body part damage tracking (head, body, legs)
- Submission system with setups, attempts, and escapes
- Counter-strike and reversal mechanics
- Referee interactions (stand-ups, doctor stoppages)
- Momentum and rhythm systems
- Fighter IQ affecting tactical decisions
- Stamina affecting performance over time
- Style-aware action selection (wrestlers clinch, strikers keep distance)
"""

from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import random
import math

from core.types import WeightClass, FightOutcome, EventType
from core.events import emit
from core.config import get_config
from core.calendar import GameDate, calendar

# Judge system for realistic decisions
try:
    from systems.judges import (
        generate_decision,
        DecisionResult,
        DecisionType,
        Scorecard,
        format_decision_for_commentary,
        calculate_dominance_from_fight,
        JUDGE_NAMES,
    )
    JUDGES_AVAILABLE = True
except ImportError:
    JUDGES_AVAILABLE = False
    DecisionResult = None


# ============================================================================
# POSITIONS - Comprehensive MMA Position System
# ============================================================================

class Position(Enum):
    """All possible fight positions"""
    # Standing
    STANDING_OPEN = "standing_open"              # Open stance, mid-range
    STANDING_CLOSE = "standing_close"            # Close range, boxing distance
    STANDING_CAGE = "standing_cage"              # Against the cage
    STANDING_CAGE_PRESSED = "standing_cage_pressed"  # Pressed against cage
    
    # Clinch
    CLINCH_DOUBLE_COLLAR = "clinch_double_collar"    # Thai clinch
    CLINCH_SINGLE_COLLAR = "clinch_single_collar"   # One hand on head
    CLINCH_OVER_UNDER = "clinch_over_under"         # Overhook/underhook
    CLINCH_BODY_LOCK = "clinch_body_lock"           # Bear hug
    CLINCH_CAGE = "clinch_cage"                     # Clinch against cage
    
    # Guard positions
    FULL_GUARD_TOP = "full_guard_top"
    FULL_GUARD_BOTTOM = "full_guard_bottom"
    CLOSED_GUARD_TOP = "closed_guard_top"
    CLOSED_GUARD_BOTTOM = "closed_guard_bottom"
    HALF_GUARD_TOP = "half_guard_top"
    HALF_GUARD_BOTTOM = "half_guard_bottom"
    BUTTERFLY_GUARD_TOP = "butterfly_guard_top"
    BUTTERFLY_GUARD_BOTTOM = "butterfly_guard_bottom"
    RUBBER_GUARD_BOTTOM = "rubber_guard_bottom"
    
    # Dominant ground positions
    SIDE_CONTROL_TOP = "side_control_top"
    SIDE_CONTROL_BOTTOM = "side_control_bottom"
    MOUNT = "mount"
    MOUNT_BOTTOM = "mount_bottom"
    BACK_MOUNT = "back_mount"
    BACK_MOUNT_BOTTOM = "back_mount_bottom"
    NORTH_SOUTH_TOP = "north_south_top"
    NORTH_SOUTH_BOTTOM = "north_south_bottom"
    CRUCIFIX_TOP = "crucifix_top"
    CRUCIFIX_BOTTOM = "crucifix_bottom"
    
    # Transitional positions
    TURTLE_TOP = "turtle_top"
    TURTLE_BOTTOM = "turtle_bottom"
    SPRAWL = "sprawl"
    SINGLE_LEG_ATTACK = "single_leg_attack"
    DOUBLE_LEG_ATTACK = "double_leg_attack"
    STANDING_BACK = "standing_back"               # Back control standing
    
    # Special positions
    KNOCKDOWN_STANDING = "knockdown_standing"     # Attacker standing over downed opponent
    AGAINST_CAGE_GROUND = "against_cage_ground"   # Ground fighting at cage
    
    # Front headlock positions (for guillotine, darce, anaconda, bulldog)
    FRONT_HEADLOCK = "front_headlock"             # Sprawl with head control
    FRONT_HEADLOCK_GUARD = "front_headlock_guard" # In guard with head trapped
    
    # Leg entanglement positions (for leg locks)
    SINGLE_LEG_X = "single_leg_x"                 # SLX/Ashi garami
    FIFTY_FIFTY = "fifty_fifty"                   # 50/50 guard
    INSIDE_SANKAKU = "inside_sankaku"             # Inside heel hook position (honeyhole)
    
    # Truck position (for twister, calf slicer)
    TRUCK = "truck"                               # Leg entanglement from back control


# Position categories for logic
STANDING_POSITIONS = {
    Position.STANDING_OPEN, Position.STANDING_CLOSE, 
    Position.STANDING_CAGE, Position.STANDING_CAGE_PRESSED
}

CLINCH_POSITIONS = {
    Position.CLINCH_DOUBLE_COLLAR, Position.CLINCH_SINGLE_COLLAR,
    Position.CLINCH_OVER_UNDER, Position.CLINCH_BODY_LOCK, Position.CLINCH_CAGE
}

GUARD_POSITIONS = {
    Position.FULL_GUARD_TOP, Position.FULL_GUARD_BOTTOM,
    Position.CLOSED_GUARD_TOP, Position.CLOSED_GUARD_BOTTOM,
    Position.HALF_GUARD_TOP, Position.HALF_GUARD_BOTTOM,
    Position.BUTTERFLY_GUARD_TOP, Position.BUTTERFLY_GUARD_BOTTOM,
    Position.RUBBER_GUARD_BOTTOM
}

DOMINANT_POSITIONS = {
    Position.SIDE_CONTROL_TOP, Position.MOUNT, Position.BACK_MOUNT,
    Position.NORTH_SOUTH_TOP, Position.CRUCIFIX_TOP, Position.TURTLE_TOP,
    Position.KNOCKDOWN_STANDING, Position.FRONT_HEADLOCK, Position.TRUCK
}

INFERIOR_POSITIONS = {
    Position.SIDE_CONTROL_BOTTOM, Position.MOUNT_BOTTOM, Position.BACK_MOUNT_BOTTOM,
    Position.NORTH_SOUTH_BOTTOM, Position.CRUCIFIX_BOTTOM, Position.TURTLE_BOTTOM
}

# Leg entanglement positions (neutral - both can attack)
LEG_ENTANGLEMENT_POSITIONS = {
    Position.SINGLE_LEG_X, Position.FIFTY_FIFTY, Position.INSIDE_SANKAKU
}

# Front headlock positions
FRONT_HEADLOCK_POSITIONS = {
    Position.FRONT_HEADLOCK, Position.FRONT_HEADLOCK_GUARD
}


# ============================================================================
# STRIKE TYPES - Detailed Striking System
# ============================================================================

class StrikeType(Enum):
    """All strike types in MMA"""
    # Punches
    JAB = "jab"
    CROSS = "cross"
    HOOK = "hook"
    UPPERCUT = "uppercut"
    OVERHAND = "overhand"
    BACKFIST = "backfist"
    SUPERMAN_PUNCH = "superman_punch"
    
    # Kicks
    LEG_KICK = "leg_kick"
    BODY_KICK = "body_kick"
    HEAD_KICK = "head_kick"
    FRONT_KICK = "front_kick"
    SIDE_KICK = "side_kick"
    SPINNING_BACK_KICK = "spinning_back_kick"
    WHEEL_KICK = "wheel_kick"
    AXE_KICK = "axe_kick"
    CALF_KICK = "calf_kick"
    OBLIQUE_KICK = "oblique_kick"
    
    # Knees
    KNEE_BODY = "knee_body"
    KNEE_HEAD = "knee_head"
    FLYING_KNEE = "flying_knee"
    
    # Elbows
    ELBOW_HORIZONTAL = "elbow_horizontal"
    ELBOW_VERTICAL = "elbow_vertical"
    ELBOW_SPINNING = "elbow_spinning"
    ELBOW_UPWARD = "elbow_upward"
    
    # Ground and Pound
    GNP_PUNCH = "gnp_punch"
    GNP_HAMMER_FIST = "gnp_hammer_fist"
    GNP_ELBOW = "gnp_elbow"
    
    # Clinch strikes
    CLINCH_KNEE = "clinch_knee"
    CLINCH_ELBOW = "clinch_elbow"
    DIRTY_BOXING = "dirty_boxing"


# Strike properties: (base_damage, ko_power, stamina_cost, target_area)
STRIKE_PROPERTIES = {
    # Punches - Fast, moderate damage
    StrikeType.JAB: (3, 0.01, 2, "head"),
    StrikeType.CROSS: (8, 0.03, 4, "head"),
    StrikeType.HOOK: (10, 0.05, 5, "head"),
    StrikeType.UPPERCUT: (9, 0.04, 5, "head"),
    StrikeType.OVERHAND: (12, 0.06, 6, "head"),
    StrikeType.BACKFIST: (6, 0.02, 4, "head"),
    StrikeType.SUPERMAN_PUNCH: (11, 0.05, 8, "head"),
    
    # Kicks - High damage, higher stamina cost
    StrikeType.LEG_KICK: (7, 0.00, 4, "legs"),
    StrikeType.BODY_KICK: (10, 0.01, 6, "body"),
    StrikeType.HEAD_KICK: (15, 0.12, 8, "head"),
    StrikeType.FRONT_KICK: (8, 0.02, 5, "body"),
    StrikeType.SIDE_KICK: (9, 0.02, 6, "body"),
    StrikeType.SPINNING_BACK_KICK: (14, 0.08, 10, "body"),
    StrikeType.WHEEL_KICK: (16, 0.15, 12, "head"),
    StrikeType.AXE_KICK: (12, 0.06, 8, "head"),
    StrikeType.CALF_KICK: (6, 0.00, 3, "legs"),
    StrikeType.OBLIQUE_KICK: (5, 0.00, 3, "legs"),
    
    # Knees - High damage in clinch
    StrikeType.KNEE_BODY: (9, 0.02, 5, "body"),
    StrikeType.KNEE_HEAD: (14, 0.10, 7, "head"),
    StrikeType.FLYING_KNEE: (18, 0.18, 12, "head"),
    
    # Elbows - Cut potential, close range
    StrikeType.ELBOW_HORIZONTAL: (8, 0.03, 4, "head"),
    StrikeType.ELBOW_VERTICAL: (10, 0.04, 5, "head"),
    StrikeType.ELBOW_SPINNING: (14, 0.08, 8, "head"),
    StrikeType.ELBOW_UPWARD: (9, 0.04, 5, "head"),
    
    # Ground and Pound
    StrikeType.GNP_PUNCH: (7, 0.02, 4, "head"),
    StrikeType.GNP_HAMMER_FIST: (6, 0.02, 3, "head"),
    StrikeType.GNP_ELBOW: (9, 0.03, 5, "head"),
    
    # Clinch strikes
    StrikeType.CLINCH_KNEE: (10, 0.04, 5, "body"),
    StrikeType.CLINCH_ELBOW: (8, 0.03, 4, "head"),
    StrikeType.DIRTY_BOXING: (5, 0.01, 3, "head"),
}


# ============================================================================
# SUBMISSIONS - Comprehensive Submission System
# ============================================================================

class SubmissionType(Enum):
    """All submission types"""
    # Chokes
    REAR_NAKED_CHOKE = "rear_naked_choke"
    GUILLOTINE = "guillotine"
    ARM_TRIANGLE = "arm_triangle"
    DARCE_CHOKE = "darce_choke"
    ANACONDA_CHOKE = "anaconda_choke"
    NORTH_SOUTH_CHOKE = "north_south_choke"
    TRIANGLE_CHOKE = "triangle_choke"
    GOGOPLATA = "gogoplata"
    BULLDOG_CHOKE = "bulldog_choke"
    VON_FLUE_CHOKE = "von_flue_choke"
    
    # Arm locks
    ARMBAR = "armbar"
    KIMURA = "kimura"
    AMERICANA = "americana"
    OMOPLATA = "omoplata"
    WRIST_LOCK = "wrist_lock"
    
    # Leg locks
    HEEL_HOOK = "heel_hook"
    KNEEBAR = "kneebar"
    TOE_HOLD = "toe_hold"
    CALF_SLICER = "calf_slicer"
    ANKLE_LOCK = "ankle_lock"
    
    # Other
    NECK_CRANK = "neck_crank"
    CAN_OPENER = "can_opener"
    TWISTER = "twister"


# Submission properties: (danger_level, escape_difficulty, positions_available)
SUBMISSION_PROPERTIES = {
    # Chokes - Most common finishes
    SubmissionType.REAR_NAKED_CHOKE: (95, 70, {Position.BACK_MOUNT, Position.STANDING_BACK}),
    SubmissionType.GUILLOTINE: (80, 60, {
        Position.FRONT_HEADLOCK, Position.FRONT_HEADLOCK_GUARD, 
        Position.STANDING_CLOSE, Position.CLOSED_GUARD_BOTTOM
    }),
    SubmissionType.ARM_TRIANGLE: (75, 55, {Position.SIDE_CONTROL_TOP, Position.MOUNT, Position.HALF_GUARD_TOP}),
    SubmissionType.DARCE_CHOKE: (70, 50, {Position.FRONT_HEADLOCK, Position.TURTLE_TOP, Position.HALF_GUARD_TOP}),
    SubmissionType.ANACONDA_CHOKE: (70, 50, {Position.FRONT_HEADLOCK, Position.TURTLE_TOP}),
    SubmissionType.NORTH_SOUTH_CHOKE: (65, 45, {Position.NORTH_SOUTH_TOP}),
    SubmissionType.TRIANGLE_CHOKE: (85, 65, {Position.FULL_GUARD_BOTTOM, Position.CLOSED_GUARD_BOTTOM, Position.RUBBER_GUARD_BOTTOM}),
    SubmissionType.GOGOPLATA: (60, 40, {Position.RUBBER_GUARD_BOTTOM}),
    SubmissionType.BULLDOG_CHOKE: (55, 40, {Position.FRONT_HEADLOCK, Position.SPRAWL}),
    SubmissionType.VON_FLUE_CHOKE: (50, 35, {Position.SIDE_CONTROL_TOP}),
    
    # Arm locks
    SubmissionType.ARMBAR: (90, 65, {
        Position.FULL_GUARD_BOTTOM, Position.CLOSED_GUARD_BOTTOM,
        Position.MOUNT, Position.SIDE_CONTROL_TOP, Position.BACK_MOUNT
    }),
    SubmissionType.KIMURA: (75, 55, {
        Position.FULL_GUARD_BOTTOM, Position.CLOSED_GUARD_BOTTOM,
        Position.HALF_GUARD_BOTTOM, Position.SIDE_CONTROL_TOP, Position.NORTH_SOUTH_TOP
    }),
    SubmissionType.AMERICANA: (60, 45, {Position.MOUNT, Position.SIDE_CONTROL_TOP}),
    SubmissionType.OMOPLATA: (55, 40, {Position.FULL_GUARD_BOTTOM, Position.RUBBER_GUARD_BOTTOM}),
    SubmissionType.WRIST_LOCK: (40, 30, {Position.MOUNT, Position.SIDE_CONTROL_TOP, Position.FULL_GUARD_BOTTOM}),
    
    # Leg locks - ONLY from leg entanglement positions
    SubmissionType.HEEL_HOOK: (95, 75, {Position.INSIDE_SANKAKU, Position.FIFTY_FIFTY}),
    SubmissionType.KNEEBAR: (70, 55, {Position.SINGLE_LEG_X, Position.FIFTY_FIFTY}),
    SubmissionType.TOE_HOLD: (55, 45, {Position.SINGLE_LEG_X, Position.FIFTY_FIFTY, Position.INSIDE_SANKAKU}),
    SubmissionType.CALF_SLICER: (50, 40, {Position.TRUCK, Position.HALF_GUARD_TOP}),
    SubmissionType.ANKLE_LOCK: (60, 50, {Position.SINGLE_LEG_X, Position.FIFTY_FIFTY}),
    
    # Other
    SubmissionType.NECK_CRANK: (45, 35, {Position.BACK_MOUNT, Position.CRUCIFIX_TOP}),
    SubmissionType.CAN_OPENER: (30, 25, {Position.CLOSED_GUARD_TOP}),
    SubmissionType.TWISTER: (55, 45, {Position.TRUCK}),
}


# ============================================================================
# GRAPPLING ACTIONS - Transitions, Sweeps, Escapes
# ============================================================================

class GrapplingAction(Enum):
    """Non-strike grappling actions"""
    # Takedowns
    SINGLE_LEG = "single_leg"
    DOUBLE_LEG = "double_leg"
    BODY_LOCK_TAKEDOWN = "body_lock_takedown"
    HIP_TOSS = "hip_toss"
    TRIP = "trip"
    SLAM = "slam"
    SUPLEX = "suplex"
    
    # Clinch transitions
    CLINCH_ENTRY = "clinch_entry"
    CLINCH_BREAK = "clinch_break"
    PUSH_TO_CAGE = "push_to_cage"
    
    # Front headlock entries
    SNAP_DOWN = "snap_down"
    SPRAWL_TO_FRONT_HEADLOCK = "sprawl_to_front_headlock"
    
    # Leg entanglement entries
    IMANARI_ROLL = "imanari_roll"
    INSIDE_TRIP_TO_LEGS = "inside_trip_to_legs"
    ENTER_SINGLE_LEG_X = "enter_single_leg_x"
    ENTER_FIFTY_FIFTY = "enter_fifty_fifty"
    
    # Truck entry
    ENTER_TRUCK = "enter_truck"
    
    # Guard passes
    PASS_TO_SIDE = "pass_to_side"
    PASS_TO_MOUNT = "pass_to_mount"
    PASS_TO_HALF = "pass_to_half"
    KNEE_SLICE = "knee_slice"
    TORREANDO = "torreando"
    LEG_DRAG = "leg_drag"
    
    # Sweeps
    SCISSOR_SWEEP = "scissor_sweep"
    FLOWER_SWEEP = "flower_sweep"
    BUTTERFLY_SWEEP = "butterfly_sweep"
    ELEVATOR_SWEEP = "elevator_sweep"
    HIP_BUMP = "hip_bump"
    TECHNICAL_STANDUP = "technical_standup"
    
    # Escapes
    SHRIMP_ESCAPE = "shrimp_escape"
    BRIDGE_ESCAPE = "bridge_escape"
    ELBOW_ESCAPE = "elbow_escape"
    GRANBY_ROLL = "granby_roll"
    STAND_UP = "stand_up"
    POP_HEAD_OUT = "pop_head_out"
    ESCAPE_LEGS = "escape_legs"
    
    # Transitions
    TAKE_BACK = "take_back"
    MOUNT_TRANSITION = "mount_transition"
    REGUARD = "reguard"
    SCRAMBLE = "scramble"


# ============================================================================
# DAMAGE & HEALTH SYSTEM
# ============================================================================

@dataclass
class BodyPartDamage:
    """Tracks damage to specific body parts"""
    head: float = 0.0
    body: float = 0.0
    legs: float = 0.0
    
    cuts: int = 0
    leg_kicks_absorbed: int = 0
    
    @property
    def total(self) -> float:
        return self.head + self.body + self.legs
    
    @property
    def is_compromised_legs(self) -> bool:
        return self.leg_kicks_absorbed >= 6 or self.legs >= 50
    
    @property
    def is_cut_badly(self) -> bool:
        return self.cuts >= 3
    
    def apply_damage(self, amount: float, target: str) -> None:
        if target == "head":
            self.head += amount
        elif target == "body":
            self.body += amount
        elif target == "legs":
            self.legs += amount
            self.leg_kicks_absorbed += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "head": self.head,
            "body": self.body,
            "legs": self.legs,
            "cuts": self.cuts,
            "leg_kicks_absorbed": self.leg_kicks_absorbed
        }


@dataclass
class FighterState:
    """Complete state of a fighter during the fight"""
    fighter_id: str
    name: str
    
    health: float = 100.0
    stamina: float = 100.0
    damage: BodyPartDamage = field(default_factory=BodyPartDamage)
    
    is_rocked: bool = False
    rock_duration: int = 0
    is_knocked_down: bool = False
    knockdowns_this_round: int = 0
    knockdowns_total: int = 0
    
    chin_compromised: bool = False
    momentum: float = 50.0
    
    def apply_damage(self, amount: float, target: str = "head") -> Tuple[bool, bool]:
        """Apply damage and return (is_knockdown, is_finish)."""
        self.damage.apply_damage(amount, target)
        self.health = max(0, self.health - amount)
        self.momentum = max(0, self.momentum - amount * 0.5)
        
        is_knockdown = False
        is_finish = False
        
        if self.health <= 0:
            is_finish = True
        elif target == "head" and amount >= 12:
            if random.random() < amount * 0.01:
                is_knockdown = True
                self.knockdowns_this_round += 1
                self.knockdowns_total += 1
            elif random.random() < amount * 0.02:
                self.is_rocked = True
                self.rock_duration = random.randint(1, 3)
        
        return is_knockdown, is_finish
    
    def recover_stamina(self, amount: float) -> None:
        self.stamina = min(100, self.stamina + amount)
    
    def spend_stamina(self, amount: float) -> None:
        self.stamina = max(0, self.stamina - amount)
    
    def new_round(self) -> None:
        self.knockdowns_this_round = 0
        self.is_knocked_down = False
        self.stamina = min(100, self.stamina + 15)
        self.is_rocked = False
        self.rock_duration = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            "health": self.health,
            "stamina": self.stamina,
            "damage": self.damage.to_dict(),
            "knockdowns_total": self.knockdowns_total,
            "momentum": self.momentum
        }


# ============================================================================
# ROUND STATISTICS
# ============================================================================

@dataclass
class RoundStats:
    """Statistics for a single round"""
    significant_strikes_attempted: int = 0
    significant_strikes_landed: int = 0
    head_strikes_landed: int = 0
    body_strikes_landed: int = 0
    leg_strikes_landed: int = 0
    
    takedowns_attempted: int = 0
    takedowns_landed: int = 0
    submission_attempts: int = 0
    
    control_time: float = 0.0
    clinch_control_time: float = 0.0
    ground_control_time: float = 0.0
    
    damage_dealt: float = 0.0
    knockdowns: int = 0
    reversals: int = 0
    
    @property
    def striking_accuracy(self) -> float:
        if self.significant_strikes_attempted == 0:
            return 0.0
        return self.significant_strikes_landed / self.significant_strikes_attempted
    
    @property
    def takedown_accuracy(self) -> float:
        if self.takedowns_attempted == 0:
            return 0.0
        return self.takedowns_landed / self.takedowns_attempted
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sig_strikes_att": self.significant_strikes_attempted,
            "sig_strikes_landed": self.significant_strikes_landed,
            "head_strikes": self.head_strikes_landed,
            "body_strikes": self.body_strikes_landed,
            "leg_strikes": self.leg_strikes_landed,
            "td_att": self.takedowns_attempted,
            "td_landed": self.takedowns_landed,
            "sub_att": self.submission_attempts,
            "control_time": self.control_time,
            "damage": self.damage_dealt,
            "knockdowns": self.knockdowns,
            "reversals": self.reversals
        }


# ============================================================================
# FIGHT STATE
# ============================================================================

@dataclass
class FightState:
    """Complete state of the fight"""
    fighter1: FighterState
    fighter2: FighterState
    
    position: Position = Position.STANDING_OPEN
    top_fighter_id: Optional[str] = None
    cage_controller_id: Optional[str] = None
    
    current_round: int = 1
    exchanges_this_round: int = 0
    total_exchanges: int = 0
    
    position_duration: int = 0
    ground_inactivity: int = 0
    
    submission_active: bool = False
    submission_type: Optional[SubmissionType] = None
    submission_attacker_id: Optional[str] = None
    submission_progress: float = 0.0
    submission_escape_progress: float = 0.0
    
    last_action: Optional[str] = None
    momentum_fighter_id: Optional[str] = None
    
    def get_fighter_state(self, fighter_id: str) -> FighterState:
        if self.fighter1.fighter_id == fighter_id:
            return self.fighter1
        return self.fighter2
    
    def get_opponent_state(self, fighter_id: str) -> FighterState:
        if self.fighter1.fighter_id == fighter_id:
            return self.fighter2
        return self.fighter1
    
    @property
    def is_standing(self) -> bool:
        return self.position in STANDING_POSITIONS
    
    @property
    def is_clinch(self) -> bool:
        return self.position in CLINCH_POSITIONS
    
    @property
    def is_ground(self) -> bool:
        return not self.is_standing and not self.is_clinch
    
    def new_round(self) -> None:
        self.position = Position.STANDING_OPEN
        self.top_fighter_id = None
        self.exchanges_this_round = 0
        self.position_duration = 0
        self.ground_inactivity = 0
        self.submission_active = False
        self.fighter1.new_round()
        self.fighter2.new_round()
    
    def get_round_time_str(self) -> str:
        seconds_per_exchange = 12
        total_seconds = self.exchanges_this_round * seconds_per_exchange
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"


# ============================================================================
# FIGHT CONFIGURATION
# ============================================================================

@dataclass
class FightConfig:
    """Configuration for a fight"""
    scheduled_rounds: int = 3
    exchanges_per_round: int = 80  # INCREASED from 50 for more realistic action volume
    
    damage_multiplier: float = 0.43  # Tuned for ~28-30% KO rate
    standup_threshold: int = 6  # Balanced for ground time
    doctor_check_cut_threshold: int = 2
    
    submission_progress_to_finish: float = 75.0  # REDUCED from 100 for faster finishes
    submission_escape_threshold: float = 100.0  # INCREASED - even harder to escape
    
    is_title_fight: bool = False
    is_main_event: bool = False
    
    @classmethod
    def standard_fight(cls) -> 'FightConfig':
        return cls(scheduled_rounds=3)
    
    @classmethod
    def championship_fight(cls) -> 'FightConfig':
        return cls(scheduled_rounds=5, is_title_fight=True, is_main_event=True)
    
    @classmethod
    def main_event(cls) -> 'FightConfig':
        return cls(scheduled_rounds=5, is_main_event=True)


# ============================================================================
# FIGHTER ATTRIBUTES INTERFACE
# ============================================================================

@dataclass
class FighterAttributes:
    """Fighter attributes for the fight engine."""
    fighter_id: str
    name: str
    
    # Physical
    strength: int = 50
    speed: int = 50
    cardio: int = 50
    chin: int = 50
    
    # Striking
    boxing: int = 50
    kicks: int = 50
    clinch_striking: int = 50
    striking_defense: int = 50
    
    # Grappling
    wrestling: int = 50
    bjj: int = 50
    takedown_defense: int = 50
    
    # Mental
    heart: int = 50
    fight_iq: int = 50
    composure: int = 50
    
    is_generational: bool = False
    
    @property
    def overall_striking(self) -> int:
        return (self.boxing * 2 + self.kicks + self.clinch_striking) // 4
    
    @property
    def overall_grappling(self) -> int:
        return (self.wrestling + self.bjj * 2 + self.takedown_defense) // 4
    
    @property
    def overall(self) -> int:
        return (self.overall_striking + self.overall_grappling + 
                self.chin + self.cardio + self.heart) // 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            "strength": self.strength,
            "speed": self.speed,
            "cardio": self.cardio,
            "chin": self.chin,
            "boxing": self.boxing,
            "kicks": self.kicks,
            "clinch_striking": self.clinch_striking,
            "striking_defense": self.striking_defense,
            "wrestling": self.wrestling,
            "bjj": self.bjj,
            "takedown_defense": self.takedown_defense,
            "heart": self.heart,
            "fight_iq": self.fight_iq,
            "composure": self.composure,
            "is_generational": self.is_generational,
        }
# ============================================================================
# ACTION SELECTION SYSTEM
# ============================================================================

def get_available_strikes(position: Position, is_top: bool = True) -> List[StrikeType]:
    """Get strikes available from current position."""
    if position in STANDING_POSITIONS:
        return [
            StrikeType.JAB, StrikeType.CROSS, StrikeType.HOOK, 
            StrikeType.UPPERCUT, StrikeType.OVERHAND,
            StrikeType.LEG_KICK, StrikeType.BODY_KICK, StrikeType.HEAD_KICK,
            StrikeType.FRONT_KICK, StrikeType.CALF_KICK,
            StrikeType.FLYING_KNEE, StrikeType.SUPERMAN_PUNCH
        ]
    
    if position in CLINCH_POSITIONS:
        return [
            StrikeType.CLINCH_KNEE, StrikeType.CLINCH_ELBOW,
            StrikeType.DIRTY_BOXING, StrikeType.KNEE_BODY,
            StrikeType.ELBOW_HORIZONTAL
        ]
    
    if position in FRONT_HEADLOCK_POSITIONS:
        if is_top:
            return [StrikeType.CLINCH_KNEE]
        return []
    
    if position in LEG_ENTANGLEMENT_POSITIONS:
        return []
    
    if position == Position.TRUCK:
        if is_top:
            return [StrikeType.GNP_PUNCH]
        return []
    
    # Ground positions
    if is_top:
        if position in {Position.MOUNT, Position.SIDE_CONTROL_TOP, 
                       Position.NORTH_SOUTH_TOP, Position.CRUCIFIX_TOP}:
            return [
                StrikeType.GNP_PUNCH, StrikeType.GNP_HAMMER_FIST,
                StrikeType.GNP_ELBOW
            ]
        elif position in {Position.FULL_GUARD_TOP, Position.HALF_GUARD_TOP,
                         Position.CLOSED_GUARD_TOP}:
            return [StrikeType.GNP_PUNCH, StrikeType.GNP_ELBOW]
        elif position == Position.KNOCKDOWN_STANDING:
            return [
                StrikeType.GNP_PUNCH, StrikeType.GNP_HAMMER_FIST,
                StrikeType.LEG_KICK
            ]
    
    return [StrikeType.ELBOW_UPWARD]


def get_available_submissions(
    position: Position, 
    is_top: bool,
    fighter_attrs: FighterAttributes
) -> List[SubmissionType]:
    """Get submissions available from current position."""
    available = []
    
    for sub_type, (danger, escape_diff, positions) in SUBMISSION_PROPERTIES.items():
        if position in positions:
            if position in LEG_ENTANGLEMENT_POSITIONS:
                if sub_type in {
                    SubmissionType.HEEL_HOOK, SubmissionType.KNEEBAR,
                    SubmissionType.TOE_HOLD, SubmissionType.ANKLE_LOCK
                }:
                    available.append(sub_type)
                continue
            
            if position in FRONT_HEADLOCK_POSITIONS:
                if is_top and sub_type in {
                    SubmissionType.GUILLOTINE, SubmissionType.DARCE_CHOKE,
                    SubmissionType.ANACONDA_CHOKE, SubmissionType.BULLDOG_CHOKE
                }:
                    available.append(sub_type)
                continue
            
            top_subs = {
                SubmissionType.REAR_NAKED_CHOKE, SubmissionType.ARM_TRIANGLE,
                SubmissionType.DARCE_CHOKE, SubmissionType.ANACONDA_CHOKE,
                SubmissionType.NORTH_SOUTH_CHOKE, SubmissionType.AMERICANA,
                SubmissionType.VON_FLUE_CHOKE, SubmissionType.NECK_CRANK,
                SubmissionType.BULLDOG_CHOKE, SubmissionType.CAN_OPENER,
                SubmissionType.CALF_SLICER, SubmissionType.TWISTER,
                SubmissionType.ARMBAR, SubmissionType.KIMURA,
            }
            bottom_subs = {
                SubmissionType.TRIANGLE_CHOKE, SubmissionType.ARMBAR,
                SubmissionType.KIMURA, SubmissionType.GUILLOTINE,
                SubmissionType.OMOPLATA, SubmissionType.GOGOPLATA,
                SubmissionType.WRIST_LOCK,
            }
            
            if is_top and sub_type in top_subs:
                available.append(sub_type)
            elif not is_top and sub_type in bottom_subs:
                available.append(sub_type)
            elif sub_type not in top_subs and sub_type not in bottom_subs:
                available.append(sub_type)
    
    return available


def get_available_grappling_actions(
    position: Position,
    is_top: bool,
    fighter_attrs: FighterAttributes
) -> List[GrapplingAction]:
    """Get grappling actions available from current position."""
    actions = []
    
    if position in STANDING_POSITIONS:
        actions.extend([
            GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG,
            GrapplingAction.CLINCH_ENTRY
        ])
        if fighter_attrs.wrestling >= 60:
            actions.append(GrapplingAction.HIP_TOSS)
        if fighter_attrs.bjj >= 70:
            actions.append(GrapplingAction.IMANARI_ROLL)
        if fighter_attrs.wrestling >= 50:
            actions.append(GrapplingAction.SNAP_DOWN)
    
    elif position in CLINCH_POSITIONS:
        actions.extend([
            GrapplingAction.BODY_LOCK_TAKEDOWN, GrapplingAction.TRIP,
            GrapplingAction.CLINCH_BREAK, GrapplingAction.PUSH_TO_CAGE
        ])
        if fighter_attrs.wrestling >= 70:
            actions.extend([GrapplingAction.SUPLEX, GrapplingAction.HIP_TOSS])
        actions.append(GrapplingAction.SNAP_DOWN)
    
    elif position in FRONT_HEADLOCK_POSITIONS:
        if is_top:
            actions.extend([
                GrapplingAction.TAKE_BACK,
                GrapplingAction.PASS_TO_SIDE,
            ])
        else:
            actions.extend([
                GrapplingAction.POP_HEAD_OUT,
                GrapplingAction.STAND_UP,
            ])
    
    elif position in LEG_ENTANGLEMENT_POSITIONS:
        actions.extend([
            GrapplingAction.ESCAPE_LEGS,
            GrapplingAction.STAND_UP,
        ])
        if fighter_attrs.bjj >= 60:
            if position != Position.INSIDE_SANKAKU:
                actions.append(GrapplingAction.ENTER_FIFTY_FIFTY)
    
    elif position == Position.TRUCK:
        if is_top:
            actions.append(GrapplingAction.TAKE_BACK)
        else:
            actions.extend([
                GrapplingAction.GRANBY_ROLL,
                GrapplingAction.ESCAPE_LEGS,
            ])
    
    elif is_top:
        if position in {Position.FULL_GUARD_TOP, Position.CLOSED_GUARD_TOP}:
            actions.extend([
                GrapplingAction.PASS_TO_SIDE, GrapplingAction.PASS_TO_HALF,
                GrapplingAction.KNEE_SLICE, GrapplingAction.TORREANDO
            ])
        elif position == Position.HALF_GUARD_TOP:
            actions.extend([
                GrapplingAction.PASS_TO_SIDE, GrapplingAction.PASS_TO_MOUNT,
                GrapplingAction.KNEE_SLICE
            ])
        elif position == Position.SIDE_CONTROL_TOP:
            actions.extend([
                GrapplingAction.MOUNT_TRANSITION, GrapplingAction.TAKE_BACK
            ])
        elif position == Position.MOUNT:
            actions.append(GrapplingAction.TAKE_BACK)
        elif position == Position.TURTLE_TOP:
            actions.extend([
                GrapplingAction.TAKE_BACK,
                GrapplingAction.ENTER_TRUCK,
            ])
        elif position == Position.BACK_MOUNT:
            if fighter_attrs.bjj >= 65:
                actions.append(GrapplingAction.ENTER_TRUCK)
        elif position == Position.SPRAWL:
            actions.extend([
                GrapplingAction.SPRAWL_TO_FRONT_HEADLOCK,
                GrapplingAction.TAKE_BACK,
            ])
    
    else:  # Bottom position
        if position in {Position.FULL_GUARD_BOTTOM, Position.CLOSED_GUARD_BOTTOM}:
            actions.extend([
                GrapplingAction.SCISSOR_SWEEP, GrapplingAction.FLOWER_SWEEP,
                GrapplingAction.HIP_BUMP, GrapplingAction.STAND_UP
            ])
            if fighter_attrs.bjj >= 65:
                actions.append(GrapplingAction.ENTER_SINGLE_LEG_X)
        elif position == Position.HALF_GUARD_BOTTOM:
            actions.extend([
                GrapplingAction.ELEVATOR_SWEEP, GrapplingAction.REGUARD,
                GrapplingAction.STAND_UP
            ])
            if fighter_attrs.bjj >= 60:
                actions.append(GrapplingAction.ENTER_SINGLE_LEG_X)
        elif position == Position.BUTTERFLY_GUARD_BOTTOM:
            actions.extend([
                GrapplingAction.BUTTERFLY_SWEEP, GrapplingAction.STAND_UP
            ])
            if fighter_attrs.bjj >= 55:
                actions.append(GrapplingAction.ENTER_SINGLE_LEG_X)
        elif position in {Position.SIDE_CONTROL_BOTTOM, Position.MOUNT_BOTTOM}:
            actions.extend([
                GrapplingAction.SHRIMP_ESCAPE, GrapplingAction.BRIDGE_ESCAPE,
                GrapplingAction.ELBOW_ESCAPE, GrapplingAction.REGUARD
            ])
        elif position == Position.BACK_MOUNT_BOTTOM:
            actions.append(GrapplingAction.GRANBY_ROLL)
        elif position == Position.TURTLE_BOTTOM:
            actions.extend([
                GrapplingAction.GRANBY_ROLL, GrapplingAction.STAND_UP
            ])
    
    return actions


# ============================================================================
# FIGHTER STYLE DETECTION
# ============================================================================

def detect_fighter_style(fighter: FighterAttributes) -> str:
    """
    Detect a fighter's primary style based on their attributes.
    Returns: 'striker', 'wrestler', 'bjj', 'sambo', 'muay_thai', 'kickboxer', 'balanced'
    """
    # Calculate style scores
    striking_score = (fighter.boxing * 2 + fighter.kicks) / 3
    wrestling_score = fighter.wrestling
    bjj_score = fighter.bjj
    clinch_score = fighter.clinch_striking
    
    # Check if fighter is well-rounded first (prevents false positives)
    all_skills = [fighter.boxing, fighter.kicks, fighter.wrestling, fighter.bjj]
    skill_range = max(all_skills) - min(all_skills)
    avg_skill = sum(all_skills) / 4
    if skill_range <= 12 and avg_skill >= 70:
        return "balanced"
    
    # Sambo: High wrestling AND high BJJ (must have BOTH elite)
    # Check this before wrestler to catch true sambo fighters
    if wrestling_score >= 85 and bjj_score >= 80:
        return "sambo"
    
    # Pure Wrestler: High wrestling, BJJ not elite
    if wrestling_score >= 80 and bjj_score < 80:
        return "wrestler"
    
    # Pure BJJ: High BJJ, wrestling not elite
    if bjj_score >= 80 and wrestling_score < 80:
        return "bjj"
    
    # Muay Thai: Must have ELITE clinch (90+) and good kicks
    if clinch_score >= 90 and fighter.kicks >= 80:
        return "muay_thai"
    
    # Kickboxer: High kicks, good boxing, weak grappling
    if fighter.kicks >= 85 and fighter.boxing >= 75 and wrestling_score < 60:
        return "kickboxer"
    
    # Pure Striker: High striking, weak grappling
    if striking_score >= 80 and wrestling_score < 65 and bjj_score < 65:
        return "striker"
    
    # Secondary checks with lower thresholds
    if wrestling_score >= 75 and bjj_score >= 75:
        return "sambo"
    if wrestling_score >= 75:
        return "wrestler"
    if bjj_score >= 75:
        return "bjj"
    if clinch_score >= 80 and fighter.kicks >= 75:
        return "muay_thai"
    if striking_score >= 70:
        return "striker"
    
    return "balanced"


def is_grappler(fighter: FighterAttributes) -> bool:
    """Check if fighter prefers grappling over striking."""
    grappling = (fighter.wrestling + fighter.bjj) / 2
    striking = (fighter.boxing + fighter.kicks) / 2
    return grappling > striking


def is_clinch_fighter(fighter: FighterAttributes) -> bool:
    """Check if fighter excels in clinch (Muay Thai, Sambo, Dirty Boxing)."""
    return fighter.clinch_striking >= 70 or (fighter.wrestling >= 70 and fighter.bjj >= 65)


# ============================================================================
# ACTION DECISION ENGINE - STYLE AWARE
# ============================================================================

def select_action(
    fighter_attrs: FighterAttributes,
    opponent_attrs: FighterAttributes,
    fight_state: FightState,
    fighter_state: FighterState
) -> Tuple[str, Any]:
    """
    Select the best action based on position, attributes, and fight state.
    Now style-aware: wrestlers clinch against strikers, etc.
    """
    is_top = fight_state.top_fighter_id == fighter_attrs.fighter_id
    position = fight_state.position
    
    # Get available actions
    strikes = get_available_strikes(position, is_top)
    submissions = get_available_submissions(position, is_top, fighter_attrs)
    grappling = get_available_grappling_actions(position, is_top, fighter_attrs)
    
    # Position secured check for submissions - must control position longer before sub attempts
    # In real MMA, fighters work position for a while before going for subs
    position_secured = fight_state.position_duration >= 5  # REDUCED to allow more sub attempts
    
    # Filter submissions by BJJ skill
    if submissions:
        advanced_subs = {
            SubmissionType.TWISTER, SubmissionType.GOGOPLATA, 
            SubmissionType.HEEL_HOOK, SubmissionType.CALF_SLICER,
            SubmissionType.OMOPLATA, SubmissionType.DARCE_CHOKE,
            SubmissionType.ANACONDA_CHOKE, SubmissionType.BULLDOG_CHOKE,
        }
        intermediate_subs = {
            SubmissionType.TRIANGLE_CHOKE, SubmissionType.ARM_TRIANGLE,
            SubmissionType.KIMURA, SubmissionType.KNEEBAR,
            SubmissionType.ANKLE_LOCK, SubmissionType.TOE_HOLD,
            SubmissionType.NORTH_SOUTH_CHOKE,
        }
        
        filtered_subs = []
        for sub in submissions:
            if sub in advanced_subs:
                if fighter_attrs.bjj >= 70:
                    filtered_subs.append(sub)
            elif sub in intermediate_subs:
                if fighter_attrs.bjj >= 55:
                    filtered_subs.append(sub)
            else:
                filtered_subs.append(sub)
        submissions = filtered_subs
    
    # Detect styles
    my_style = detect_fighter_style(fighter_attrs)
    opp_style = detect_fighter_style(opponent_attrs)
    
    # Base weights - TUNED for realistic action distribution
    # Real MMA: ~70% standing exchanges, ~20% grappling, ~10% ground
    # Subs should be EXTREMELY RARE but VERY DANGEROUS when attempted
    strike_weight = 120  # High strike bias everywhere
    sub_weight = 0      # START AT ZERO - only add when conditions are perfect
    grapple_weight = 10  # REDUCED from 15 - less grappling, more striking
    
    # Block submissions if position not secured
    if not position_secured:
        sub_weight = 0
        if position not in STANDING_POSITIONS:
            grapple_weight += 15
    
    # =========================================================================
    # STYLE-SPECIFIC STRATEGY ADJUSTMENTS
    # =========================================================================
    
    if position in STANDING_POSITIONS:
        # --- WRESTLER VS STRIKER: Clinch first strategy ---
        if my_style in ("wrestler", "sambo") and opp_style in ("striker", "kickboxer"):
            # Wrestlers want to clinch but shouldn't spam TDs
            strike_weight = 45  # INCREASED - more striking, less grappling
            grapple_weight = 45  # REDUCED from 60
            # Prioritize clinch entry over shooting from distance
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 15  # REDUCED from 20
        
        # Also handle wrestler vs bjj, wrestler vs balanced
        elif my_style in ("wrestler", "sambo") and opp_style in ("bjj", "balanced", "muay_thai"):
            strike_weight -= 5  # REDUCED penalty
            grapple_weight += 15  # REDUCED from 25
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 8  # REDUCED from 10
        
        # --- MUAY THAI: Wants clinch for knees/elbows, uses leg kicks vs boxers ---
        elif my_style == "muay_thai":
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 25  # Thai fighters love clinch
            strike_weight += 10  # But still good strikers
            
            # MUAY THAI VS PURE BOXER: Leg kicks disrupt boxing rhythm
            # This is a well-known stylistic advantage
            if opp_style == "striker":
                strike_weight += 15  # More aggressive striking - leg kicks work
            
            # Muay Thai vs Kickboxer is more even
            elif opp_style == "kickboxer":
                strike_weight += 5
            
            # MUAY THAI VS WRESTLER: Thai clinch is dangerous for wrestlers
            # In real MMA, Muay Thai fighters can catch wrestlers in the clinch
            # with devastating knees as they shoot or in the clinch
            elif opp_style in ("wrestler", "sambo"):
                strike_weight += 20  # More aggressive - punish takedown attempts
                grapple_weight += 15  # Want to get to clinch to land knees
        
        # --- SAMBO: Clinch for trips and throws ---
        elif my_style == "sambo":
            grapple_weight += 20  # REDUCED from 35
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 10  # REDUCED from 15
        
        # --- PURE STRIKER: Keep distance, avoid clinch ---
        elif my_style in ("striker", "kickboxer"):
            strike_weight += 25
            grapple_weight -= 15  # Don't want to grapple
        
        # --- BJJ: Pull guard or get clinched ---
        elif my_style == "bjj":
            if fighter_attrs.wrestling >= 60:
                grapple_weight += 30  # Try to take it down
            else:
                # Lower wrestling BJJ guys still try to close distance
                grapple_weight += 20
        
        # --- Generic grappler advantage ---
        elif is_grappler(fighter_attrs):
            strike_weight -= 20
            grapple_weight += 40
            if fighter_attrs.wrestling > 70:
                grapple_weight += 15
            if fighter_attrs.wrestling > 85:
                grapple_weight += 15  # Elite wrestlers shoot constantly
    
    elif position in CLINCH_POSITIONS:
        # --- IN CLINCH: Style determines what happens ---
        
        # Muay Thai DOMINATES clinch striking - this is their home
        if my_style == "muay_thai":
            strike_weight += 50  # INCREASED - Devastating knees and elbows
            grapple_weight -= 15  # Very happy to stay in clinch
            
            # MUAY THAI VS WRESTLER IN CLINCH: Thai clinch is nightmare for wrestlers
            # Real MMA: Wanderlei Silva, Anderson Silva used this
            if opp_style in ("wrestler", "sambo"):
                strike_weight += 25  # Even MORE aggressive - punish them
        
        # Wrestlers/Sambo want takedowns from clinch but not 95% of the time
        elif my_style in ("wrestler", "sambo"):
            strike_weight = 15  # INCREASED from 5 - throw some dirty boxing
            grapple_weight = 70  # REDUCED from 85 - still mainly TD focused
        
        # Generic grapplers also want takedowns
        elif is_grappler(fighter_attrs):
            strike_weight -= 15
            grapple_weight += 35
        
        # Strikers want to break clinch BADLY
        elif my_style in ("striker", "kickboxer"):
            # Prioritize clinch break - they're in danger here
            grapple_weight += 40  # Desperate to escape
            strike_weight -= 20  # Not great in clinch
        
        # BJJ wants to pull guard or get takedown
        elif my_style == "bjj":
            grapple_weight += 30
            strike_weight -= 10
    
    elif position in DOMINANT_POSITIONS:
        if position_secured:
            # Two main tiers - 85-87 (Sambo) is near-zero
            if fighter_attrs.bjj >= 92:  # Pure BJJ specialists
                sub_weight += 120  # INCREASED from 90
            elif fighter_attrs.bjj >= 88:  # High-level BJJ
                sub_weight += 45   # INCREASED from 32
            elif fighter_attrs.bjj >= 85:  # Sambo - rare subs
                sub_weight += 2
        strike_weight += 50  # GNP
        grapple_weight += 10  # Position advancement
    
    elif position in INFERIOR_POSITIONS:
        grapple_weight += 45  # Want to escape badly
        if position_secured:
            if fighter_attrs.bjj >= 92:
                sub_weight += 85   # INCREASED from 65
            elif fighter_attrs.bjj >= 88:
                sub_weight += 35   # INCREASED from 26
            elif fighter_attrs.bjj >= 85:
                sub_weight += 1  # Near-zero for Sambo
    
    elif position in LEG_ENTANGLEMENT_POSITIONS:
        if position_secured:
            if fighter_attrs.bjj >= 92:
                sub_weight += 150  # INCREASED from 115
            elif fighter_attrs.bjj >= 88:
                sub_weight += 60   # INCREASED from 45
            elif fighter_attrs.bjj >= 85:
                sub_weight += 3  # Minimal for Sambo
        grapple_weight += 20  # Position battles common
        strike_weight = 0
    
    # GUARD POSITIONS - BJJ's specialty
    elif position in GUARD_POSITIONS:
        if is_top:
            strike_weight += 45  # GNP from top
            grapple_weight += 20  # Passing guard
        else:
            # BOTTOM GUARD - BJJ's home
            grapple_weight += 20  # Sweeps
            if position_secured:
                if fighter_attrs.bjj >= 92:
                    sub_weight += 180  # INCREASED from 140
                elif fighter_attrs.bjj >= 88:
                    sub_weight += 70   # INCREASED from 52
                elif fighter_attrs.bjj >= 85:
                    sub_weight += 3  # Minimal for Sambo
    
    # Fight state adjustments - removed desperate sub boost
    
    if fighter_state.momentum > 70:
        strike_weight += 10
    
    # Stamina factor
    stamina_factor = fighter_state.stamina / 100
    strike_weight = int(strike_weight * stamina_factor)
    sub_weight = int(sub_weight * stamina_factor)
    grapple_weight = int(grapple_weight * stamina_factor)
    
    # Ensure minimum weights
    strike_weight = max(5, strike_weight) if strikes else 0
    # Only BJJ specialists (85+) can attempt subs
    if submissions and fighter_attrs.bjj >= 85:
        sub_weight = max(1, sub_weight)
    elif submissions and sub_weight > 0 and fighter_attrs.bjj >= 85:
        sub_weight = max(1, sub_weight)
    else:
        sub_weight = 0  # No subs for non-specialists
        sub_weight = 0  # No subs for low BJJ fighters
    grapple_weight = max(5, grapple_weight) if grappling else 0
    
    # Select action category
    total = strike_weight + sub_weight + grapple_weight
    if total == 0:
        return ("strike", random.choice(strikes) if strikes else StrikeType.JAB)
    
    roll = random.random() * total
    
    if roll < strike_weight:
        strike = select_strike(strikes, fighter_attrs, opponent_attrs, position)
        return ("strike", strike)
    elif roll < strike_weight + sub_weight:
        sub = random.choice(submissions)
        return ("submission", sub)
    else:
        action = select_grappling_action(grappling, fighter_attrs, position, is_top)
        return ("grappling", action)


def select_strike(
    available: List[StrikeType],
    fighter: FighterAttributes,
    opponent: FighterAttributes,
    position: Position
) -> StrikeType:
    """Select the best strike based on attributes and position."""
    weights = {}
    
    for strike in available:
        base_damage, ko_power, stamina, target = STRIKE_PROPERTIES[strike]
        weight = 10
        
        # Skill-based weights
        if strike in {StrikeType.JAB, StrikeType.CROSS, StrikeType.HOOK, 
                     StrikeType.UPPERCUT, StrikeType.OVERHAND}:
            weight += fighter.boxing // 5
        elif "kick" in strike.value.lower() or "knee" in strike.value.lower():
            weight += fighter.kicks // 5
        elif "elbow" in strike.value.lower() or "clinch" in strike.value.lower():
            weight += fighter.clinch_striking // 5
        
        # Fight IQ targeting
        if fighter.fight_iq > 60:
            if target == "legs" and opponent.speed > 70:
                weight += 10
            if target == "body" and opponent.cardio > 70:
                weight += 10
        
        # Speed for complex strikes
        if strike in {StrikeType.WHEEL_KICK, StrikeType.SPINNING_BACK_KICK}:
            weight = int(weight * (fighter.speed / 70))
        
        weights[strike] = max(1, int(weight))
    
    strikes_list = list(weights.keys())
    probs = list(weights.values())
    return random.choices(strikes_list, weights=probs, k=1)[0]


def select_grappling_action(
    available: List[GrapplingAction],
    fighter: FighterAttributes,
    position: Position,
    is_top: bool
) -> GrapplingAction:
    """Select grappling action based on attributes and situation."""
    weights = {}
    
    for action in available:
        weight = 10
        
        # Wrestling-based actions
        if action in {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG,
                     GrapplingAction.BODY_LOCK_TAKEDOWN, GrapplingAction.SUPLEX,
                     GrapplingAction.HIP_TOSS, GrapplingAction.TRIP}:
            weight += fighter.wrestling // 4
        
        # BJJ-based actions
        elif action in {GrapplingAction.SCISSOR_SWEEP, GrapplingAction.FLOWER_SWEEP,
                       GrapplingAction.BUTTERFLY_SWEEP, GrapplingAction.SHRIMP_ESCAPE,
                       GrapplingAction.PASS_TO_SIDE, GrapplingAction.TAKE_BACK}:
            weight += fighter.bjj // 4
        
        # Clinch entry - wrestlers and sambo love this
        elif action == GrapplingAction.CLINCH_ENTRY:
            weight += fighter.wrestling // 3
            if fighter.clinch_striking >= 70:
                weight += 15  # Muay Thai bonus
        
        # Stand up attempts
        elif action == GrapplingAction.STAND_UP:
            if fighter.wrestling > 60 or fighter.strength > 60:
                weight += 15
        
        # Clinch break - strikers want this
        elif action == GrapplingAction.CLINCH_BREAK:
            if fighter.boxing > fighter.wrestling:
                weight += 20  # Strikers really want to break clinch
        
        weights[action] = max(1, int(weight))
    
    actions_list = list(weights.keys())
    probs = list(weights.values())
    return random.choices(actions_list, weights=probs, k=1)[0]
# ============================================================================
# ACTION RESOLUTION
# ============================================================================

def calculate_strike_success(
    attacker: FighterAttributes,
    defender: FighterAttributes,
    strike: StrikeType,
    attacker_state: FighterState,
    defender_state: FighterState,
    fight_state: FightState
) -> Tuple[bool, bool]:
    """
    Calculate if a strike lands and if it's a counter.
    Returns (landed, was_counter)
    """
    # Determine relevant skills
    if strike in {StrikeType.JAB, StrikeType.CROSS, StrikeType.HOOK,
                 StrikeType.UPPERCUT, StrikeType.OVERHAND}:
        offense = attacker.boxing
        defense = defender.striking_defense
    elif "kick" in strike.value.lower():
        offense = attacker.kicks
        defense = defender.striking_defense
        
        # MUAY THAI VS BOXER: Leg kicks are devastating vs pure boxers
        # Boxers don't train to check kicks and have narrow stances
        if attacker.kicks >= 80 and defender.kicks < 60:
            offense += 10  # Significant accuracy bonus vs non-kickers
    elif strike in {StrikeType.CLINCH_KNEE, StrikeType.CLINCH_ELBOW, StrikeType.DIRTY_BOXING}:
        offense = attacker.clinch_striking
        # In clinch, wrestling helps defend
        defense = (defender.striking_defense + defender.wrestling) // 2
    else:
        offense = attacker.clinch_striking
        defense = defender.striking_defense
    
    # Speed modifier
    offense += attacker.speed // 10
    defense += defender.speed // 10
    
    # GRAPPLER PRESSURE: When standing, grapplers affect both offense AND defense
    # Strikers can't fully commit when worried about takedowns
    if fight_state.position in STANDING_POSITIONS:
        # Defensive bonus - grappler's threat makes striker tentative
        if defender.wrestling >= 85:
            defense += 15  # Elite wrestler - striker very cautious
        elif defender.wrestling >= 75:
            defense += 10  # Good wrestler 
        elif defender.wrestling >= 60:
            defense += 5
        
        # BJJ defensive bonus - imanari rolls, guard pulls make strikers wary
        if defender.bjj >= 85:
            defense += 10
        elif defender.bjj >= 75:
            defense += 5
        
        # OFFENSIVE PENALTY - strikers can't load up vs elite wrestlers
        # This is key - even if they're more skilled, they can't fully use it
        wrestling_threat = defender.wrestling - attacker.wrestling
        if wrestling_threat >= 30:
            offense *= 0.75  # 25% offense reduction vs elite wrestler
        elif wrestling_threat >= 20:
            offense *= 0.82  # 18% reduction
        elif wrestling_threat >= 10:
            offense *= 0.90  # 10% reduction
        
        # BJJ threat offense penalty
        bjj_threat = defender.bjj - attacker.bjj
        if bjj_threat >= 30:
            offense *= 0.88  # 12% reduction
        elif bjj_threat >= 20:
            offense *= 0.94  # 6% reduction
    
    # Stamina affects accuracy
    offense *= (attacker_state.stamina / 100)
    defense *= (defender_state.stamina / 100)
    
    # Rocked opponent is easier to hit
    if defender_state.is_rocked:
        defense *= 0.5
    
    # Base success chance
    success_chance = 0.3 + (offense / (offense + defense + 1)) * 0.5
    success_chance = max(0.25, min(0.85, success_chance))
    
    # UPSET VARIANCE: Underdogs can land lucky shots
    # More generous - anyone can land a lucky punch in MMA
    if offense < defense * 0.85:
        upset_roll = random.random()
        if upset_roll < 0.07:  # 7% lucky punch chance
            success_chance = max(success_chance, 0.60)
        elif upset_roll < 0.12:  # Additional 5% for small boost
            success_chance = min(success_chance + 0.12, 0.55)
    
    landed = random.random() < success_chance
    
    # Counter check
    was_counter = False
    if landed and defender.fight_iq > 60 and random.random() < 0.15:
        was_counter = True
    
    return landed, was_counter


def calculate_strike_damage(
    attacker: FighterAttributes,
    defender: FighterAttributes,
    strike: StrikeType,
    attacker_state: FighterState,
    defender_state: FighterState,
    was_counter: bool = False
) -> Tuple[float, str]:
    """Calculate damage from a strike. Returns (damage, target_area)."""
    base_damage, ko_power, stamina_cost, target = STRIKE_PROPERTIES[strike]
    
    # Strength adds damage
    damage = base_damage + (attacker.strength - 50) / 10
    
    # Power punchers bonus
    if strike in {StrikeType.CROSS, StrikeType.HOOK, StrikeType.OVERHAND}:
        damage *= 1 + (attacker.strength / 200)
    
    # MUAY THAI VS BOXER: Kicks do extra damage to non-kickers
    # Boxers don't check kicks properly and their legs get chewed up
    if "kick" in strike.value.lower():
        if attacker.kicks >= 75 and defender.kicks < 60:
            damage *= 1.25  # 25% bonus damage
        elif attacker.kicks >= 65 and defender.kicks < 50:
            damage *= 1.15  # 15% bonus
    
    # Counter bonus
    if was_counter:
        damage *= 1.3
    
    # Stamina affects power
    damage *= (attacker_state.stamina / 100) * 0.5 + 0.5
    
    # Compromised chin
    if target == "head" and defender_state.chin_compromised:
        damage *= 1.2
    
    # Variance
    damage *= random.uniform(0.8, 1.2)
    
    return damage, target


def calculate_grappling_success(
    attacker: FighterAttributes,
    defender: FighterAttributes,
    action: GrapplingAction,
    attacker_state: FighterState,
    defender_state: FighterState,
    fight_state: FightState
) -> bool:
    """Calculate if a grappling action succeeds."""
    
    # Calculate wrestling differential - THIS IS THE KEY
    # When a wrestler has 30+ point advantage, they should dominate grappling
    wrestling_diff = attacker.wrestling - defender.wrestling
    
    # Determine relevant skills
    if action in {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG}:
        offense = attacker.wrestling
        defense = defender.takedown_defense
        # DISTANCE SHOTS: Real UFC is ~30-35% average
        base_chance = 0.12  # REDUCED from 0.15 to hit 1-2 TD/fight target
        multiplier = 0.40
        
        # WRESTLING DIFFERENTIAL BONUS - elite wrestlers still succeed
        # Elite wrestler (95) vs striker wrestler (60) = 35 point gap
        if wrestling_diff >= 35:
            base_chance += 0.15
        elif wrestling_diff >= 25:
            base_chance += 0.10
        elif wrestling_diff >= 15:
            base_chance += 0.06
        
        # Elite wrestler bonus
        if attacker.wrestling >= 90:
            base_chance += 0.04
            
    elif action == GrapplingAction.BODY_LOCK_TAKEDOWN:
        offense = attacker.wrestling
        defense = defender.takedown_defense
        # CLINCH TAKEDOWNS: Wrestlers' bread and butter but still contested
        base_chance = 0.35  # REDUCED from 0.50
        multiplier = 0.40  # REDUCED from 0.45
        
        # WRESTLING DIFFERENTIAL BONUS
        if wrestling_diff >= 35:
            base_chance += 0.18  # REDUCED from 0.25
        elif wrestling_diff >= 25:
            base_chance += 0.12  # REDUCED from 0.18
        elif wrestling_diff >= 15:
            base_chance += 0.08  # REDUCED from 0.12
        
        # Elite chain wrestling
        if attacker.wrestling >= 90:
            base_chance += 0.05
            
    elif action in {GrapplingAction.TRIP, GrapplingAction.HIP_TOSS, GrapplingAction.SUPLEX}:
        offense = attacker.wrestling
        defense = defender.wrestling
        base_chance = 0.32
        multiplier = 0.50
        # Judo throws work well vs non-wrestlers
        if wrestling_diff >= 20:
            base_chance += 0.12
            
    elif action in {GrapplingAction.PASS_TO_SIDE, GrapplingAction.PASS_TO_MOUNT,
                   GrapplingAction.KNEE_SLICE}:
        offense = attacker.bjj
        defense = defender.bjj
        base_chance = 0.28
        multiplier = 0.55
        # BJJ differential bonus
        bjj_diff = attacker.bjj - defender.bjj
        if bjj_diff >= 30:
            base_chance += 0.15
        elif bjj_diff >= 20:
            base_chance += 0.10
            
    elif action in {GrapplingAction.SCISSOR_SWEEP, GrapplingAction.BUTTERFLY_SWEEP,
                   GrapplingAction.FLOWER_SWEEP}:
        offense = attacker.bjj
        defense = defender.wrestling
        base_chance = 0.35  # INCREASED from 0.28 for more reversals
        multiplier = 0.55
        # BJJ vs wrestling for sweeps
        sweep_diff = attacker.bjj - defender.wrestling
        if sweep_diff >= 25:
            base_chance += 0.12
            
    elif action in {GrapplingAction.SHRIMP_ESCAPE, GrapplingAction.BRIDGE_ESCAPE}:
        offense = attacker.bjj + attacker.strength // 2
        defense = defender.wrestling + defender.strength // 2
        base_chance = 0.48  # Balanced for control time vs sub finishes
        multiplier = 0.50
        # Strikers have hard time escaping wrestlers
        if wrestling_diff <= -25:  # Attacker is weaker wrestler
            base_chance -= 0.05
            
    elif action == GrapplingAction.STAND_UP:
        offense = attacker.wrestling + attacker.strength // 2
        defense = defender.wrestling
        base_chance = 0.50  # Balanced for control time vs sub finishes
        multiplier = 0.50
        # Much harder to stand up vs elite wrestlers
        if wrestling_diff <= -30:
            base_chance -= 0.08
            
    elif action == GrapplingAction.CLINCH_ENTRY:
        # CLINCH ENTRY - THE CRITICAL ACTION
        # Elite wrestlers MUST be able to close distance reliably
        offense = attacker.wrestling + attacker.speed // 4
        defense = defender.striking_defense + defender.speed // 4
        
        # Higher base for wrestlers
        base_chance = 0.50
        multiplier = 0.40
        
        # WRESTLING DIFFERENTIAL BONUS - the key!
        # 95 wrestling vs 60 wrestling = 35 point gap
        if wrestling_diff >= 35:
            base_chance += 0.25  # ~85% success rate
        elif wrestling_diff >= 25:
            base_chance += 0.18  # ~78% success rate
        elif wrestling_diff >= 15:
            base_chance += 0.12  # ~72% success rate
        
        # BJJ ALTERNATIVE PATH: High-level BJJ fighters can close distance too
        # They use setups like Imanari rolls, collar ties, snap downs
        # This helps BJJ specialists who may not have elite wrestling
        bjj_diff = attacker.bjj - defender.bjj
        if bjj_diff >= 35:
            base_chance += 0.15  # BJJ wizards find a way in
        elif bjj_diff >= 25:
            base_chance += 0.10
        elif bjj_diff >= 15:
            base_chance += 0.06
        
        # Elite wrestler relentlessness
        if attacker.wrestling >= 90:
            base_chance += 0.05
            
    elif action == GrapplingAction.CLINCH_BREAK:
        # CLINCH BREAK - Should be VERY hard vs wrestlers
        # This is critical - once clinched, strikers shouldn't easily escape
        offense = attacker.strength // 2 + attacker.wrestling // 4
        defense = defender.wrestling + defender.strength // 2
        base_chance = 0.12  # Very low base
        multiplier = 0.35
        
        # Wrestling differential makes it even harder
        # Negative diff means attacker is weaker wrestler
        if wrestling_diff <= -35:
            base_chance -= 0.05  # Nearly impossible
        elif wrestling_diff <= -25:
            base_chance -= 0.03
    else:
        offense = attacker.wrestling
        defense = defender.bjj
        base_chance = 0.25
        multiplier = 0.55
    
    # Stamina matters greatly in grappling
    offense *= (attacker_state.stamina / 100)
    defense *= (defender_state.stamina / 100)
    
    # Calculate success chance
    success_chance = base_chance + (offense / (offense + defense + 1)) * multiplier
    success_chance = max(0.12, min(0.88, success_chance))
    
    # UPSET VARIANCE: Underdogs can succeed sometimes
    # More generous trigger - applies when attacker is notably weaker
    if offense < defense * 0.85:
        upset_roll = random.random()
        if upset_roll < 0.08:  # 8% upset chance (was 6%)
            success_chance = max(success_chance, 0.55)
        elif upset_roll < 0.15:  # Additional 7% for small boost
            success_chance = min(success_chance + 0.15, 0.65)
    
    return random.random() < success_chance


def apply_position_change(
    fight_state: FightState,
    action: GrapplingAction,
    attacker_id: str,
    success: bool
) -> Optional[Position]:
    """Apply position change from grappling action with weighted outcomes."""
    if not success:
        return None
    
    new_position = None
    new_top = None
    
    # === TAKEDOWN OUTCOMES ===
    if action == GrapplingAction.SINGLE_LEG:
        outcomes = [
            (Position.HALF_GUARD_TOP, 50),
            (Position.FULL_GUARD_TOP, 30),
            (Position.SIDE_CONTROL_TOP, 15),
            (Position.STANDING_OPEN, 5),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id if new_position != Position.STANDING_OPEN else None
        
    elif action == GrapplingAction.DOUBLE_LEG:
        outcomes = [
            (Position.FULL_GUARD_TOP, 45),
            (Position.HALF_GUARD_TOP, 30),
            (Position.SIDE_CONTROL_TOP, 20),
            (Position.MOUNT, 5),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id
        
    elif action == GrapplingAction.BODY_LOCK_TAKEDOWN:
        # Clinch takedowns land in better positions
        outcomes = [
            (Position.SIDE_CONTROL_TOP, 50),
            (Position.HALF_GUARD_TOP, 25),
            (Position.MOUNT, 18),
            (Position.BACK_MOUNT, 7),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id
        
    elif action in {GrapplingAction.TRIP, GrapplingAction.HIP_TOSS}:
        outcomes = [
            (Position.SIDE_CONTROL_TOP, 45),
            (Position.MOUNT, 25),
            (Position.HALF_GUARD_TOP, 20),
            (Position.BACK_MOUNT, 10),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id
        
    elif action == GrapplingAction.SUPLEX:
        outcomes = [
            (Position.BACK_MOUNT, 40),
            (Position.SIDE_CONTROL_TOP, 35),
            (Position.MOUNT, 20),
            (Position.TURTLE_TOP, 5),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id
    
    # === GUARD PASS OUTCOMES ===
    elif action == GrapplingAction.PASS_TO_SIDE:
        outcomes = [
            (Position.SIDE_CONTROL_TOP, 70),
            (Position.HALF_GUARD_TOP, 25),
            (Position.NORTH_SOUTH_TOP, 5),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id
        
    elif action == GrapplingAction.KNEE_SLICE:
        outcomes = [
            (Position.SIDE_CONTROL_TOP, 60),
            (Position.HALF_GUARD_TOP, 30),
            (Position.MOUNT, 10),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id
        
    elif action == GrapplingAction.TORREANDO:
        outcomes = [
            (Position.SIDE_CONTROL_TOP, 55),
            (Position.NORTH_SOUTH_TOP, 25),
            (Position.MOUNT, 15),
            (Position.FULL_GUARD_TOP, 5),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id
    
    # === SWEEP OUTCOMES ===
    elif action in {GrapplingAction.SCISSOR_SWEEP, GrapplingAction.FLOWER_SWEEP}:
        outcomes = [
            (Position.MOUNT, 50),
            (Position.FULL_GUARD_TOP, 35),
            (Position.SIDE_CONTROL_TOP, 15),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id
        
    elif action == GrapplingAction.BUTTERFLY_SWEEP:
        outcomes = [
            (Position.FULL_GUARD_TOP, 45),
            (Position.MOUNT, 30),
            (Position.STANDING_OPEN, 25),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id if new_position != Position.STANDING_OPEN else None
        
    elif action in {GrapplingAction.ELEVATOR_SWEEP, GrapplingAction.HIP_BUMP}:
        outcomes = [
            (Position.FULL_GUARD_TOP, 50),
            (Position.MOUNT, 35),
            (Position.HALF_GUARD_TOP, 15),
        ]
        new_position = _weighted_choice(outcomes)
        new_top = attacker_id
    
    # === STANDARD TRANSITIONS ===
    elif action == GrapplingAction.PASS_TO_MOUNT:
        new_position = Position.MOUNT
        new_top = attacker_id
    elif action == GrapplingAction.PASS_TO_HALF:
        new_position = Position.HALF_GUARD_TOP
        new_top = attacker_id
    elif action == GrapplingAction.MOUNT_TRANSITION:
        new_position = Position.MOUNT
        new_top = attacker_id
    elif action == GrapplingAction.TAKE_BACK:
        new_position = Position.BACK_MOUNT
        new_top = attacker_id
    
    # === ESCAPES ===
    elif action in {GrapplingAction.SHRIMP_ESCAPE, GrapplingAction.ELBOW_ESCAPE}:
        new_position = Position.FULL_GUARD_BOTTOM
    elif action == GrapplingAction.BRIDGE_ESCAPE:
        new_position = Position.HALF_GUARD_BOTTOM
    elif action == GrapplingAction.REGUARD:
        new_position = Position.FULL_GUARD_BOTTOM
    elif action == GrapplingAction.GRANBY_ROLL:
        new_position = Position.FULL_GUARD_BOTTOM
    elif action == GrapplingAction.STAND_UP:
        new_position = Position.STANDING_OPEN
        new_top = None
    elif action == GrapplingAction.TECHNICAL_STANDUP:
        new_position = Position.STANDING_OPEN
        new_top = None
    
    # === CLINCH TRANSITIONS ===
    elif action == GrapplingAction.CLINCH_ENTRY:
        new_position = Position.CLINCH_OVER_UNDER
        new_top = None
    elif action == GrapplingAction.CLINCH_BREAK:
        new_position = Position.STANDING_OPEN
        new_top = None
    elif action == GrapplingAction.PUSH_TO_CAGE:
        new_position = Position.CLINCH_CAGE
    
    # === FRONT HEADLOCK ===
    elif action == GrapplingAction.SNAP_DOWN:
        new_position = Position.FRONT_HEADLOCK
        new_top = attacker_id
    elif action == GrapplingAction.SPRAWL_TO_FRONT_HEADLOCK:
        new_position = Position.FRONT_HEADLOCK
        new_top = attacker_id
    elif action == GrapplingAction.POP_HEAD_OUT:
        new_position = Position.STANDING_OPEN
        new_top = None
    
    # === LEG ENTANGLEMENT ===
    elif action == GrapplingAction.IMANARI_ROLL:
        new_position = Position.SINGLE_LEG_X
        new_top = None
    elif action == GrapplingAction.ENTER_SINGLE_LEG_X:
        new_position = Position.SINGLE_LEG_X
        new_top = None
    elif action == GrapplingAction.ENTER_FIFTY_FIFTY:
        new_position = Position.FIFTY_FIFTY
        new_top = None
    elif action == GrapplingAction.INSIDE_TRIP_TO_LEGS:
        new_position = Position.INSIDE_SANKAKU
        new_top = None
    elif action == GrapplingAction.ESCAPE_LEGS:
        new_position = Position.STANDING_OPEN
        new_top = None
    
    # === TRUCK ===
    elif action == GrapplingAction.ENTER_TRUCK:
        new_position = Position.TRUCK
        new_top = attacker_id
    
    # Apply the position change
    if new_position:
        fight_state.position = new_position
        if new_top is not None:
            fight_state.top_fighter_id = new_top
        elif action in {GrapplingAction.STAND_UP, GrapplingAction.CLINCH_BREAK,
                       GrapplingAction.ESCAPE_LEGS, GrapplingAction.POP_HEAD_OUT}:
            fight_state.top_fighter_id = None
        fight_state.position_duration = 0
    
    return new_position


def _weighted_choice(outcomes: List[Tuple[Position, int]]) -> Position:
    """Select a position based on weighted probabilities."""
    positions = [o[0] for o in outcomes]
    weights = [o[1] for o in outcomes]
    return random.choices(positions, weights=weights, k=1)[0]


# ============================================================================
# SUBMISSION RESOLUTION
# ============================================================================

def attempt_submission(
    attacker: FighterAttributes,
    defender: FighterAttributes,
    sub_type: SubmissionType,
    attacker_state: FighterState,
    defender_state: FighterState,
    fight_state: FightState
) -> Tuple[bool, bool, float]:
    """
    Attempt a submission.
    Returns (locked_in, finished, progress)
    
    Philosophy: Subs are EXTREMELY RARE but NEARLY ALWAYS FINISH
    - Only elite BJJ (85+) attempts (handled in select_action)
    - Selection rates are low (~15% for BJJ, ~5% for Sambo)
    - But when they DO attempt, very high success rate
    """
    danger, escape_diff, positions = SUBMISSION_PROPERTIES[sub_type]
    
    if fight_state.position not in positions:
        return False, False, 0.0
    
    # Calculate lock-in chance - VERY HIGH base
    offense = attacker.bjj + (danger / 10)
    defense = defender.bjj + (escape_diff / 10)
    
    # BJJ DIFFERENTIAL BONUS - MASSIVE for specialists
    bjj_diff = attacker.bjj - defender.bjj
    bjj_bonus = 0.0
    if bjj_diff >= 40:
        bjj_bonus = 0.35  # Near-certain lock
    elif bjj_diff >= 30:
        bjj_bonus = 0.28
    elif bjj_diff >= 20:
        bjj_bonus = 0.20
    elif bjj_diff >= 10:
        bjj_bonus = 0.12
    
    # PURE BJJ SPECIALIST BONUS (92+) - massive advantage
    if attacker.bjj >= 92:
        bjj_bonus += 0.15
    elif attacker.bjj >= 88:
        bjj_bonus += 0.08
    
    # Stamina is crucial
    offense *= (attacker_state.stamina / 100)
    defense *= (defender_state.stamina / 100)
    
    # Heart helps defense - minimal
    defense += defender.heart // 20
    
    # Wrestling helps defend submissions - minimal
    defense += defender.wrestling // 35
    
    # Lock-in chance - VERY HIGH because attempts are now rare
    lock_in_chance = 0.65 + bjj_bonus + (offense / (offense + defense + 1)) * 0.25
    lock_in_chance = min(0.98, lock_in_chance)  # Cap at 98%
    locked_in = random.random() < lock_in_chance
    
    if not locked_in:
        return False, False, 0.0
    
    # Start submission sequence - high progress for fast finish
    fight_state.submission_active = True
    fight_state.submission_type = sub_type
    fight_state.submission_attacker_id = attacker.fighter_id
    
    # Starting progress - HIGH because attempts are rare
    base_progress = offense * 1.2  # INCREASED from 0.9
    
    # PURE BJJ SPECIALIST (92+) locks it in tighter
    if attacker.bjj >= 92:
        base_progress *= 1.5
    elif attacker.bjj >= 88:
        base_progress *= 1.25
    
    # BJJ differential = faster finish
    if bjj_diff >= 30:
        base_progress *= 2.5  # Near-instant tap
    elif bjj_diff >= 20:
        base_progress *= 2.0
    elif bjj_diff >= 10:
        base_progress *= 1.5
    
    fight_state.submission_progress = base_progress
    fight_state.submission_escape_progress = 0.0
    
    return True, False, fight_state.submission_progress


def process_submission_progress(
    attacker: FighterAttributes,
    defender: FighterAttributes,
    attacker_state: FighterState,
    defender_state: FighterState,
    fight_state: FightState,
    config: FightConfig
) -> Tuple[bool, bool]:
    """
    Process ongoing submission attempt.
    Returns (escaped, finished)
    
    Philosophy: Once locked in, subs should USUALLY finish
    - Rare to get locked in (handled in attempt_submission)
    - But once locked in, very hard to escape
    """
    if not fight_state.submission_active:
        return False, False
    
    sub_type = fight_state.submission_type
    if sub_type is None:
        fight_state.submission_active = False
        return False, False
    
    danger, escape_diff, _ = SUBMISSION_PROPERTIES[sub_type]
    
    # Attacker tightens - VERY FAST once locked in
    offense = attacker.bjj * (attacker_state.stamina / 100)
    
    # PURE BJJ SPECIALIST (92+) tightens MUCH faster
    tighten_rate = 1.0 if attacker.bjj >= 92 else 0.75
    fight_state.submission_progress += offense * tighten_rate
    
    # Defender fights escape - EXTREMELY HARD to escape
    defense = defender.bjj * (defender_state.stamina / 100)
    defense += defender.heart * 0.03  # REDUCED
    fight_state.submission_escape_progress += defense * 0.10  # REDUCED from 0.15
    
    # Stamina drain - submission is exhausting
    attacker_state.spend_stamina(3)
    defender_state.spend_stamina(5)  # INCREASED - being submitted is exhausting
    
    # Check for finish
    if fight_state.submission_progress >= config.submission_progress_to_finish:
        fight_state.submission_active = False
        return False, True
    
    # Check for escape (threshold is now 95, was 80)
    if fight_state.submission_escape_progress >= config.submission_escape_threshold:
        fight_state.submission_active = False
        return True, False
    
    return False, False
# ============================================================================
# EXCHANGE SIMULATION
# ============================================================================

def simulate_exchange(
    fighter1: FighterAttributes,
    fighter2: FighterAttributes,
    fighter1_state: FighterState,
    fighter2_state: FighterState,
    fight_state: FightState,
    config: FightConfig,
    round_stats: Dict[str, RoundStats]
) -> Optional[Tuple[str, str]]:
    """
    Simulate a single exchange.
    Returns (winner_id, finish_method) if fight ends, else None.
    """
    fight_state.exchanges_this_round += 1
    fight_state.total_exchanges += 1
    fight_state.position_duration += 1
    
    # Process ongoing submission
    if fight_state.submission_active:
        attacker = fighter1 if fight_state.submission_attacker_id == fighter1.fighter_id else fighter2
        defender = fighter2 if attacker == fighter1 else fighter1
        attacker_state = fighter1_state if attacker == fighter1 else fighter2_state
        defender_state = fighter2_state if attacker == fighter1 else fighter1_state
        
        escaped, finished = process_submission_progress(
            attacker, defender, attacker_state, defender_state, fight_state, config
        )
        
        if finished:
            round_stats[attacker.fighter_id].submission_attempts += 1
            sub_name = fight_state.submission_type.value if fight_state.submission_type else "unknown"
            return (attacker.fighter_id, f"Submission ({sub_name})")
        
        if escaped:
            round_stats[defender.fighter_id].reversals += 1
        
        return None
    
    # Determine initiative - who acts this exchange
    # Base: speed + momentum + randomness
    f1_initiative = fighter1.speed + fighter1_state.momentum // 2 + random.randint(-15, 15)
    f2_initiative = fighter2.speed + fighter2_state.momentum // 2 + random.randint(-15, 15)
    
    # UNDERDOG AGGRESSION: Fighters who are losing fight harder
    # This creates upset potential - underdogs get more chances to attack
    f1_overall = fighter1.overall
    f2_overall = fighter2.overall
    overall_gap = abs(f1_overall - f2_overall)
    
    if f1_overall < f2_overall and overall_gap >= 8:
        # Fighter 1 is the underdog - they're more aggressive
        aggression_bonus = min(12, overall_gap // 2)  # Up to +12 for 24+ point gap
        f1_initiative += aggression_bonus
    elif f2_overall < f1_overall and overall_gap >= 8:
        # Fighter 2 is the underdog
        aggression_bonus = min(12, overall_gap // 2)
        f2_initiative += aggression_bonus
    
    # WRESTLING INITIATIVE BONUS: Grapplers are constantly threatening
    # In standing, wrestlers use level changes and feints that disrupt striker rhythm
    if fight_state.position in STANDING_POSITIONS:
        # Wrestlers get big initiative bonus - they're always threatening
        if fighter1.wrestling >= 85:
            f1_initiative += 12  # Elite wrestler - constant threat
        elif fighter1.wrestling >= 70:
            f1_initiative += 6
        if fighter2.wrestling >= 85:
            f2_initiative += 12
        elif fighter2.wrestling >= 70:
            f2_initiative += 6
        
        # BJJ THREAT: High-level BJJ fighters threaten from everywhere
        # Imanari rolls, guard pulls, flying submissions - they're dangerous
        if fighter1.bjj >= 85:
            f1_initiative += 8  # Elite BJJ - always a threat
        elif fighter1.bjj >= 75:
            f1_initiative += 4
        if fighter2.bjj >= 85:
            f2_initiative += 8
        elif fighter2.bjj >= 75:
            f2_initiative += 4
    
    # IN CLINCH: Wrestling AND clinch striking matter
    # The faster fighter can't "run away" when clinched
    if fight_state.position in CLINCH_POSITIONS:
        # Wrestling skill gives initiative in clinch
        f1_initiative += fighter1.wrestling // 6  # Up to +15 for 95 wrestling
        f2_initiative += fighter2.wrestling // 6
        
        # MUAY THAI CLINCH MASTERY: Clinch strikers DOMINATE clinch initiative
        # This is crucial - Muay Thai's whole game IS the clinch
        # They should be the kings of clinch fighting
        f1_initiative += fighter1.clinch_striking // 5  # Up to +18 for 90 clinch striking
        f2_initiative += fighter2.clinch_striking // 5
        
        # ELITE CLINCH STRIKER BONUS: True specialists get extra
        if fighter1.clinch_striking >= 85:
            f1_initiative += 10  # INCREASED from 8 - Elite Thai clinch
        if fighter2.clinch_striking >= 85:
            f2_initiative += 10  # INCREASED from 8
        
        # MUAY THAI VS WRESTLER IN CLINCH: Huge advantage for Thai fighters
        # Wrestlers struggle against the Thai plum and devastating knees
        f1_style = detect_fighter_style(fighter1)
        f2_style = detect_fighter_style(fighter2)
        
        if f1_style == "muay_thai" and f2_style in ("wrestler", "sambo"):
            f1_initiative += 12  # Big advantage - clinch is MT's domain
        if f2_style == "muay_thai" and f1_style in ("wrestler", "sambo"):
            f2_initiative += 12
        
        # Speed matters much less in the clinch
        f1_initiative -= fighter1.speed // 10  # Reduce speed contribution
        f2_initiative -= fighter2.speed // 10
    
    # Position affects initiative
    if fight_state.top_fighter_id == fighter1.fighter_id:
        f1_initiative += 8
    elif fight_state.top_fighter_id == fighter2.fighter_id:
        f2_initiative += 8
    
    # Active guard bonus
    if fight_state.position in GUARD_POSITIONS:
        if fight_state.top_fighter_id == fighter1.fighter_id:
            f2_initiative += 5
        elif fight_state.top_fighter_id == fighter2.fighter_id:
            f1_initiative += 5
    
    # Determine attacker - with coin flip for near-ties to prevent first-mover advantage
    if abs(f1_initiative - f2_initiative) <= 3:
        # Close initiative - coin flip
        if random.random() < 0.5:
            attacker, defender = fighter1, fighter2
            attacker_state, defender_state = fighter1_state, fighter2_state
        else:
            attacker, defender = fighter2, fighter1
            attacker_state, defender_state = fighter2_state, fighter1_state
    elif f1_initiative > f2_initiative:
        attacker, defender = fighter1, fighter2
        attacker_state, defender_state = fighter1_state, fighter2_state
    else:
        attacker, defender = fighter2, fighter1
        attacker_state, defender_state = fighter2_state, fighter1_state
    
    # Select action
    action_type, action_data = select_action(attacker, defender, fight_state, attacker_state)
    
    # Resolve action
    if action_type == "strike":
        strike = action_data
        landed, was_counter = calculate_strike_success(
            attacker, defender, strike, attacker_state, defender_state, fight_state
        )
        
        _, _, stamina_cost, _ = STRIKE_PROPERTIES[strike]
        attacker_state.spend_stamina(stamina_cost)
        round_stats[attacker.fighter_id].significant_strikes_attempted += 1
        
        if landed:
            damage, target = calculate_strike_damage(
                attacker, defender, strike, attacker_state, defender_state, was_counter
            )
            
            # WRESTLER THREAT DAMAGE REDUCTION
            # Strikers can't throw with full power when worried about takedowns
            # This is CRITICAL - grapplers pressure makes strikers tentative
            if fight_state.position in STANDING_POSITIONS:
                wrestling_threat = defender.wrestling - attacker.wrestling
                if wrestling_threat >= 30:
                    damage *= 0.65  # 35% damage reduction vs elite wrestler
                elif wrestling_threat >= 20:
                    damage *= 0.75  # 25% reduction
                elif wrestling_threat >= 10:
                    damage *= 0.85  # 15% reduction
                
                # BJJ threat also makes strikers cautious (flying subs, imanari)
                bjj_threat = defender.bjj - attacker.bjj
                if bjj_threat >= 30:
                    damage *= 0.85  # Additional 15% reduction
                elif bjj_threat >= 20:
                    damage *= 0.92  # Additional 8% reduction
            
            # Apply config damage multiplier (compensates for increased exchanges)
            damage *= config.damage_multiplier
            
            is_knockdown, is_finish = defender_state.apply_damage(damage, target)
            
            # FLASH KO MECHANIC: Underdogs can score flash knockouts
            # This represents the "anyone can get caught" reality of MMA
            # In real MMA, massive upsets happen - Francis Ngannou, Matt Serra, etc.
            if not is_finish and target == "head":
                attacker_overall = attacker.overall
                defender_overall = defender.overall
                skill_gap = defender_overall - attacker_overall
                
                # Triggers when attacker is underdog (5+ points)
                if skill_gap >= 5:
                    # Flash KO chance - SIGNIFICANTLY INCREASED
                    # 5 point gap: 1.5%, 10 point gap: 3%, 20 point gap: 6%, 30 point gap: 9%
                    flash_ko_chance = min(0.09, skill_gap * 0.003)
                    
                    # Damage bonus - harder shots more likely to flash KO
                    if damage >= 8:
                        flash_ko_chance *= 1.5
                    elif damage >= 5:
                        flash_ko_chance *= 1.2
                    
                    # Bonus if underdog has decent power/boxing
                    if attacker.strength >= 75 or attacker.boxing >= 75:
                        flash_ko_chance *= 1.4  # 40% bonus for power punchers
                    elif attacker.strength >= 65 or attacker.boxing >= 65:
                        flash_ko_chance *= 1.2
                    
                    if random.random() < flash_ko_chance:
                        is_finish = True  # Flash KO!
            
            round_stats[attacker.fighter_id].significant_strikes_landed += 1
            round_stats[attacker.fighter_id].damage_dealt += damage
            
            if target == "head":
                round_stats[attacker.fighter_id].head_strikes_landed += 1
            elif target == "body":
                round_stats[attacker.fighter_id].body_strikes_landed += 1
            else:
                round_stats[attacker.fighter_id].leg_strikes_landed += 1
            
            attacker_state.momentum = min(100, attacker_state.momentum + damage * 0.3)
            
            if is_finish:
                finish_type = "KO" if target == "head" else "TKO"
                return (attacker.fighter_id, finish_type)
            
            if is_knockdown:
                round_stats[attacker.fighter_id].knockdowns += 1
                fight_state.position = Position.KNOCKDOWN_STANDING
                fight_state.top_fighter_id = attacker.fighter_id
    
    elif action_type == "submission":
        sub_type = action_data
        locked_in, finished, progress = attempt_submission(
            attacker, defender, sub_type, attacker_state, defender_state, fight_state
        )
        
        round_stats[attacker.fighter_id].submission_attempts += 1
        attacker_state.spend_stamina(5)
        
        # FLASH SUBMISSION: BJJ specialists can catch people quickly
        # Think Ryan Hall, Demian Maia - they catch people in transitions
        if locked_in and not finished:
            attacker_overall = attacker.overall
            defender_overall = defender.overall
            skill_gap = defender_overall - attacker_overall
            
            if skill_gap >= 5 and attacker.bjj >= 70:
                # Flash sub chance based on skill gap and BJJ
                flash_sub_chance = min(0.06, skill_gap * 0.002)
                
                # BJJ specialist bonus
                if attacker.bjj >= 85:
                    flash_sub_chance *= 1.5
                elif attacker.bjj >= 75:
                    flash_sub_chance *= 1.25
                
                if random.random() < flash_sub_chance:
                    finished = True  # Flash submission!
        
        if finished:
            return (attacker.fighter_id, f"Submission ({sub_type.value})")
    
    elif action_type == "grappling":
        action = action_data
        success = calculate_grappling_success(
            attacker, defender, action, attacker_state, defender_state, fight_state
        )
        
        # Takedown tracking
        if action in {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG,
                     GrapplingAction.BODY_LOCK_TAKEDOWN}:
            round_stats[attacker.fighter_id].takedowns_attempted += 1
            if success:
                round_stats[attacker.fighter_id].takedowns_landed += 1
        
        # Sweep tracking
        sweep_actions = {
            GrapplingAction.SCISSOR_SWEEP, GrapplingAction.FLOWER_SWEEP,
            GrapplingAction.BUTTERFLY_SWEEP, GrapplingAction.ELEVATOR_SWEEP,
        }
        if action in sweep_actions and success:
            round_stats[attacker.fighter_id].reversals += 1
        
        # Escape tracking
        escape_actions = {
            GrapplingAction.SHRIMP_ESCAPE, GrapplingAction.BRIDGE_ESCAPE,
            GrapplingAction.ELBOW_ESCAPE, GrapplingAction.TECHNICAL_STANDUP,
            GrapplingAction.STAND_UP, GrapplingAction.ESCAPE_LEGS,
            GrapplingAction.CLINCH_BREAK,
        }
        if action in escape_actions and success:
            round_stats[attacker.fighter_id].reversals += 1
        
        attacker_state.spend_stamina(4)
        
        if success:
            new_pos = apply_position_change(fight_state, action, attacker.fighter_id, True)
            
            if new_pos in DOMINANT_POSITIONS:
                attacker_state.momentum = min(100, attacker_state.momentum + 10)
                defender_state.momentum = max(0, defender_state.momentum - 10)
            elif new_pos in STANDING_POSITIONS and action in escape_actions:
                attacker_state.momentum = min(100, attacker_state.momentum + 5)
                defender_state.momentum = max(0, defender_state.momentum - 5)
        else:
            # FAILED GRAPPLING PUNISHMENT
            # When takedowns/clinch entries fail, the defender can counter
            # This is especially important for Muay Thai vs Wrestlers
            if action in {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG,
                         GrapplingAction.CLINCH_ENTRY, GrapplingAction.BODY_LOCK_TAKEDOWN}:
                # Clinch strikers punish failed entries with knees
                if fight_state.position in STANDING_POSITIONS or fight_state.position in CLINCH_POSITIONS:
                    counter_damage = 0
                    
                    # High clinch striking = DEVASTATING counter strikes
                    # This is how Muay Thai fighters stop wrestlers
                    if defender.clinch_striking >= 85:
                        counter_damage = random.uniform(5, 10)  # INCREASED - Elite Muay Thai knee
                    elif defender.clinch_striking >= 75:
                        counter_damage = random.uniform(3, 7)  # INCREASED
                    elif defender.clinch_striking >= 65:
                        counter_damage = random.uniform(2, 5)  # INCREASED
                    
                    # Good boxing also counters failed takedowns
                    elif defender.boxing >= 80:
                        counter_damage = random.uniform(3, 6)  # INCREASED - Uppercut on shoot
                    
                    if counter_damage > 0:
                        # Apply config damage multiplier
                        counter_damage *= config.damage_multiplier
                        # Apply counter damage to the failed grappler
                        attacker_state.apply_damage(counter_damage, "head")
                        defender_state.momentum = min(100, defender_state.momentum + 8)  # INCREASED
                        attacker_state.momentum = max(0, attacker_state.momentum - 8)  # INCREASED
    
    # Control time tracking
    if fight_state.is_ground and fight_state.top_fighter_id:
        round_stats[fight_state.top_fighter_id].ground_control_time += 1
        round_stats[fight_state.top_fighter_id].control_time += 1
    elif fight_state.is_clinch:
        # In clinch, track control for the fighter with better position
        if fight_state.cage_controller_id:
            round_stats[fight_state.cage_controller_id].clinch_control_time += 1
            round_stats[fight_state.cage_controller_id].control_time += 1
    
    # Referee standup check
    if fight_state.is_ground and not fight_state.submission_active:
        fight_state.ground_inactivity += 1
        if fight_state.ground_inactivity >= config.standup_threshold:
            fight_state.position = Position.STANDING_OPEN
            fight_state.top_fighter_id = None
            fight_state.ground_inactivity = 0
    elif not fight_state.is_ground:
        fight_state.ground_inactivity = 0
    
    # Stamina recovery
    attacker_state.recover_stamina(0.5)
    defender_state.recover_stamina(0.5)
    
    # Rock duration
    if fighter1_state.is_rocked:
        fighter1_state.rock_duration -= 1
        if fighter1_state.rock_duration <= 0:
            fighter1_state.is_rocked = False
    if fighter2_state.is_rocked:
        fighter2_state.rock_duration -= 1
        if fighter2_state.rock_duration <= 0:
            fighter2_state.is_rocked = False
    
    return None


# ============================================================================
# ROUND SCORING
# ============================================================================

def score_round(
    stats1: RoundStats,
    stats2: RoundStats,
    knockdowns1: int,
    knockdowns2: int
) -> Tuple[int, int]:
    """
    Score a round using 10-point must system.
    Balanced scoring: grappling control valued higher.
    """
    # Scoring weights - grappling valued more
    score1 = (
        stats1.damage_dealt * 1.5 +
        stats1.significant_strikes_landed * 1.0 +
        stats1.takedowns_landed * 8.0 +      # Increased from 5
        stats1.control_time * 1.5 +           # Increased from 0.5
        stats1.knockdowns * 20.0 +
        stats1.submission_attempts * 4.0      # Increased from 3
    )
    
    score2 = (
        stats2.damage_dealt * 1.5 +
        stats2.significant_strikes_landed * 1.0 +
        stats2.takedowns_landed * 8.0 +
        stats2.control_time * 1.5 +
        stats2.knockdowns * 20.0 +
        stats2.submission_attempts * 4.0
    )
    
    # Multiple knockdowns = automatic 10-8 or worse
    if knockdowns1 >= 2 and knockdowns2 == 0:
        return (10, 8) if knockdowns1 == 2 else (10, 7)
    if knockdowns2 >= 2 and knockdowns1 == 0:
        return (8, 10) if knockdowns2 == 2 else (7, 10)
    
    # Single knockdown advantage
    if knockdowns1 > knockdowns2:
        if score1 > score2 * 1.5 and score1 > 20:
            return (10, 8)
        return (10, 9)
    if knockdowns2 > knockdowns1:
        if score2 > score1 * 1.5 and score2 > 20:
            return (8, 10)
        return (9, 10)
    
    # No knockdowns - normal scoring
    total_score = score1 + score2
    
    if total_score < 10:
        if score1 > score2:
            return (10, 9)
        elif score2 > score1:
            return (9, 10)
        else:
            return (10, 10)
    
    if score1 + score2 > 0:
        ratio = score1 / (score1 + score2)
    else:
        ratio = 0.5
    
    if ratio >= 0.75 and score1 >= 30:
        return (10, 8)
    elif ratio <= 0.25 and score2 >= 30:
        return (8, 10)
    elif ratio >= 0.55:
        return (10, 9)
    elif ratio <= 0.45:
        return (9, 10)
    else:
        return (10, 10)


# ============================================================================
# FIGHT RESULT
# ============================================================================

@dataclass
class FightResult:
    """Complete result of a fight."""
    winner_id: Optional[str]
    loser_id: Optional[str]
    method: str
    finish_round: Optional[int]
    finish_time: Optional[str]
    
    judge_scores: List[Tuple[int, int]] = field(default_factory=list)
    decision_type: Optional[str] = None
    
    judge_names: List[str] = field(default_factory=list)
    judge_scorecards: List[Dict] = field(default_factory=list)
    is_controversial: bool = False
    controversy_reason: Optional[str] = None
    decision_commentary: Optional[str] = None
    
    fighter1_stats: List[Dict] = field(default_factory=list)
    fighter2_stats: List[Dict] = field(default_factory=list)
    
    fighter1_final_state: Optional[Dict] = None
    fighter2_final_state: Optional[Dict] = None
    
    @property
    def is_finish(self) -> bool:
        return "Decision" not in self.method and self.method != "Draw"
    
    @property
    def is_decision(self) -> bool:
        return "Decision" in self.method
    
    @property
    def is_draw(self) -> bool:
        return self.method == "Draw"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "winner_id": self.winner_id,
            "loser_id": self.loser_id,
            "method": self.method,
            "finish_round": self.finish_round,
            "finish_time": self.finish_time,
            "judge_scores": self.judge_scores,
            "decision_type": self.decision_type,
            "judge_names": self.judge_names,
            "judge_scorecards": self.judge_scorecards,
            "is_controversial": self.is_controversial,
            "controversy_reason": self.controversy_reason,
            "decision_commentary": self.decision_commentary,
            "fighter1_stats": self.fighter1_stats,
            "fighter2_stats": self.fighter2_stats
        }


# ============================================================================
# MAIN FIGHT SIMULATION
# ============================================================================

def simulate_fight(
    fighter1: FighterAttributes,
    fighter2: FighterAttributes,
    config: Optional[FightConfig] = None
) -> FightResult:
    """
    Simulate a complete fight.
    
    Args:
        fighter1: First fighter's attributes
        fighter2: Second fighter's attributes
        config: Fight configuration (rounds, etc.)
    
    Returns:
        Complete fight result
    """
    if config is None:
        config = FightConfig.standard_fight()
    
    # Initialize states
    f1_state = FighterState(
        fighter_id=fighter1.fighter_id,
        name=fighter1.name,
        health=100.0 + fighter1.chin * 0.5,
        stamina=100.0
    )
    f2_state = FighterState(
        fighter_id=fighter2.fighter_id,
        name=fighter2.name,
        health=100.0 + fighter2.chin * 0.5,
        stamina=100.0
    )
    
    fight_state = FightState(fighter1=f1_state, fighter2=f2_state)
    
    # Round stats
    all_stats: Dict[str, List[RoundStats]] = {
        fighter1.fighter_id: [],
        fighter2.fighter_id: []
    }
    
    round_scores: List[Tuple[int, int]] = []
    
    # Fight loop
    for round_num in range(1, config.scheduled_rounds + 1):
        fight_state.current_round = round_num
        fight_state.new_round()
        
        round_stats = {
            fighter1.fighter_id: RoundStats(),
            fighter2.fighter_id: RoundStats()
        }
        
        # Exchange loop
        for _ in range(config.exchanges_per_round):
            result = simulate_exchange(
                fighter1, fighter2,
                f1_state, f2_state,
                fight_state, config,
                round_stats
            )
            
            if result:
                winner_id, method = result
                loser_id = fighter2.fighter_id if winner_id == fighter1.fighter_id else fighter1.fighter_id
                
                all_stats[fighter1.fighter_id].append(round_stats[fighter1.fighter_id])
                all_stats[fighter2.fighter_id].append(round_stats[fighter2.fighter_id])
                
                return FightResult(
                    winner_id=winner_id,
                    loser_id=loser_id,
                    method=method,
                    finish_round=round_num,
                    finish_time=fight_state.get_round_time_str(),
                    fighter1_stats=[s.to_dict() for s in all_stats[fighter1.fighter_id]],
                    fighter2_stats=[s.to_dict() for s in all_stats[fighter2.fighter_id]],
                    fighter1_final_state=f1_state.to_dict(),
                    fighter2_final_state=f2_state.to_dict()
                )
        
        # End of round
        all_stats[fighter1.fighter_id].append(round_stats[fighter1.fighter_id])
        all_stats[fighter2.fighter_id].append(round_stats[fighter2.fighter_id])
        
        # Score round
        s1, s2 = score_round(
            round_stats[fighter1.fighter_id],
            round_stats[fighter2.fighter_id],
            f1_state.knockdowns_this_round,
            f2_state.knockdowns_this_round
        )
        round_scores.append((s1, s2))
    
    # Decision - calculate dominance
    f1_total_strikes = sum(s.significant_strikes_landed for s in all_stats[fighter1.fighter_id])
    f2_total_strikes = sum(s.significant_strikes_landed for s in all_stats[fighter2.fighter_id])
    f1_control = sum(s.control_time for s in all_stats[fighter1.fighter_id])
    f2_control = sum(s.control_time for s in all_stats[fighter2.fighter_id])
    
    f1_rounds = sum(1 for s1, s2 in round_scores if s1 > s2)
    f2_rounds = sum(1 for s1, s2 in round_scores if s2 > s1)
    
    if f1_rounds > f2_rounds:
        winner_dominance = 0.5 + (f1_rounds - f2_rounds) / (config.scheduled_rounds * 2)
    elif f2_rounds > f1_rounds:
        winner_dominance = 0.5 - (f2_rounds - f1_rounds) / (config.scheduled_rounds * 2)
    else:
        if f1_total_strikes > f2_total_strikes:
            winner_dominance = 0.52
        elif f2_total_strikes > f1_total_strikes:
            winner_dominance = 0.48
        else:
            winner_dominance = 0.5
    
    # Use judges system if available
    if JUDGES_AVAILABLE:
        try:
            decision_result = generate_decision(
                winner_dominance=winner_dominance,
                total_rounds=config.scheduled_rounds,
                is_title_fight=getattr(config, 'is_title_fight', False),
                fighter1_name=fighter1.name,
                fighter2_name=fighter2.name,
            )
            
            if decision_result.winner == 1:
                winner_id = fighter1.fighter_id
                loser_id = fighter2.fighter_id
                winner_name = fighter1.name
                loser_name = fighter2.name
            elif decision_result.winner == 2:
                winner_id = fighter2.fighter_id
                loser_id = fighter1.fighter_id
                winner_name = fighter2.name
                loser_name = fighter1.name
            else:
                winner_id = None
                loser_id = None
                winner_name = None
                loser_name = None
            
            decision_type = decision_result.decision_type.value.replace(" Decision", "") if decision_result.decision_type else None
            
            judge_scores = [(sc.fighter1_score, sc.fighter2_score) for sc in decision_result.scorecards]
            judge_names = [sc.judge_name for sc in decision_result.scorecards]
            judge_scorecards = [
                {
                    "judge_name": sc.judge_name,
                    "fighter1_score": sc.fighter1_score,
                    "fighter2_score": sc.fighter2_score,
                    "round_scores": sc.round_scores,
                }
                for sc in decision_result.scorecards
            ]
            
            decision_commentary = None
            if winner_name and loser_name:
                decision_commentary = format_decision_for_commentary(
                    decision_result, winner_name, loser_name
                )
            
            method = f"{decision_type} Decision" if decision_type else "Draw"
            
            return FightResult(
                winner_id=winner_id,
                loser_id=loser_id,
                method=method,
                finish_round=None,
                finish_time=None,
                judge_scores=judge_scores,
                decision_type=decision_type,
                judge_names=judge_names,
                judge_scorecards=judge_scorecards,
                is_controversial=decision_result.is_controversial,
                controversy_reason=decision_result.controversy_reason,
                decision_commentary=decision_commentary,
                fighter1_stats=[s.to_dict() for s in all_stats[fighter1.fighter_id]],
                fighter2_stats=[s.to_dict() for s in all_stats[fighter2.fighter_id]],
                fighter1_final_state=f1_state.to_dict(),
                fighter2_final_state=f2_state.to_dict()
            )
        except Exception as e:
            # Fallback if judges system fails
            pass
    
    # Fallback decision logic
    judge_scores = []
    for _ in range(3):
        j1, j2 = 0, 0
        for s1, s2 in round_scores:
            if random.random() < 0.1:
                if s1 > s2:
                    s1, s2 = s2, s1
            j1 += s1
            j2 += s2
        judge_scores.append((j1, j2))
    
    f1_wins = sum(1 for j1, j2 in judge_scores if j1 > j2)
    f2_wins = sum(1 for j1, j2 in judge_scores if j2 > j1)
    
    if f1_wins >= 2:
        winner_id = fighter1.fighter_id
        loser_id = fighter2.fighter_id
        decision_type = "Unanimous" if f1_wins == 3 else "Split"
    elif f2_wins >= 2:
        winner_id = fighter2.fighter_id
        loser_id = fighter1.fighter_id
        decision_type = "Unanimous" if f2_wins == 3 else "Split"
    else:
        winner_id = None
        loser_id = None
        decision_type = None
    
    method = f"{decision_type} Decision" if decision_type else "Draw"
    
    return FightResult(
        winner_id=winner_id,
        loser_id=loser_id,
        method=method,
        finish_round=None,
        finish_time=None,
        judge_scores=judge_scores,
        decision_type=decision_type,
        judge_names=[],
        judge_scorecards=[],
        is_controversial=False,
        controversy_reason=None,
        decision_commentary=None,
        fighter1_stats=[s.to_dict() for s in all_stats[fighter1.fighter_id]],
        fighter2_stats=[s.to_dict() for s in all_stats[fighter2.fighter_id]],
        fighter1_final_state=f1_state.to_dict(),
        fighter2_final_state=f2_state.to_dict()
    )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def quick_simulate(
    f1_overall: int,
    f2_overall: int,
    rounds: int = 3
) -> FightResult:
    """Quick simulation with just overall ratings."""
    fighter1 = FighterAttributes(
        fighter_id="f1",
        name="Fighter 1",
        boxing=f1_overall, kicks=f1_overall,
        wrestling=f1_overall, bjj=f1_overall,
        chin=f1_overall, cardio=f1_overall,
        speed=f1_overall, strength=f1_overall,
        heart=f1_overall, fight_iq=f1_overall,
        composure=f1_overall
    )
    fighter2 = FighterAttributes(
        fighter_id="f2",
        name="Fighter 2",
        boxing=f2_overall, kicks=f2_overall,
        wrestling=f2_overall, bjj=f2_overall,
        chin=f2_overall, cardio=f2_overall,
        speed=f2_overall, strength=f2_overall,
        heart=f2_overall, fight_iq=f2_overall,
        composure=f2_overall
    )
    
    config = FightConfig(scheduled_rounds=rounds)
    return simulate_fight(fighter1, fighter2, config)


def get_fight_outcome(result: FightResult) -> FightOutcome:
    """Convert FightResult to FightOutcome enum."""
    method = result.method.lower()
    
    if "ko" in method and "tko" not in method:
        return FightOutcome.KO
    elif "tko" in method:
        return FightOutcome.TKO
    elif "submission" in method:
        return FightOutcome.SUBMISSION
    elif "decision" in method:
        if result.decision_type == "Unanimous":
            return FightOutcome.DECISION_UNANIMOUS
        elif result.decision_type == "Split":
            return FightOutcome.DECISION_SPLIT
        else:
            return FightOutcome.DECISION_UNANIMOUS
    elif "draw" in method:
        return FightOutcome.DRAW
    else:
        return FightOutcome.DECISION_UNANIMOUS
