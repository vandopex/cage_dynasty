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


# P3-4c §5a — SUBMISSION classification (choke | joint_lock). Spine
# cranks (neck_crank, can_opener, twister) classified as joint_lock
# per prompt. Complete map for all 23 SubmissionType entries.
SUBMISSION_KIND = {
    # Chokes (10)
    SubmissionType.REAR_NAKED_CHOKE:   "choke",
    SubmissionType.GUILLOTINE:         "choke",
    SubmissionType.ARM_TRIANGLE:       "choke",
    SubmissionType.DARCE_CHOKE:        "choke",
    SubmissionType.ANACONDA_CHOKE:     "choke",
    SubmissionType.NORTH_SOUTH_CHOKE:  "choke",
    SubmissionType.TRIANGLE_CHOKE:     "choke",
    SubmissionType.GOGOPLATA:          "choke",
    SubmissionType.BULLDOG_CHOKE:      "choke",
    SubmissionType.VON_FLUE_CHOKE:     "choke",
    # Joint locks (13, including 3 spine cranks per prompt)
    SubmissionType.ARMBAR:             "joint_lock",
    SubmissionType.KIMURA:             "joint_lock",
    SubmissionType.AMERICANA:          "joint_lock",
    SubmissionType.OMOPLATA:           "joint_lock",
    SubmissionType.WRIST_LOCK:         "joint_lock",
    SubmissionType.HEEL_HOOK:          "joint_lock",
    SubmissionType.KNEEBAR:            "joint_lock",
    SubmissionType.TOE_HOLD:           "joint_lock",
    SubmissionType.CALF_SLICER:        "joint_lock",
    SubmissionType.ANKLE_LOCK:         "joint_lock",
    SubmissionType.NECK_CRANK:         "joint_lock",  # spine crank
    SubmissionType.CAN_OPENER:         "joint_lock",  # spine crank
    SubmissionType.TWISTER:            "joint_lock",  # spine crank
}


# ============================================================================
# P3-4c §5a — SUBMISSION MODEL constants (PROVISIONAL, P3-5 calibrates)
# ============================================================================
# Escape composites live in CONTEST_RECIPES/CONTEST_TARGETS above under
# key "sub_escape" (P_EVEN=0.10, EDGE20_TARGET=0.28 → S ≈ 2.88 derived).
# CONTEST_P_MIN/MAX auto-derive: min=0.04, max=0.37.
#
# Tap threshold: heart-scaled × state-scaled. Base = TAP_BASE, defaulting
# to config.submission_progress_to_finish so existing config dial still
# governs. Formula:
#   effective_tap = TAP_BASE
#                 × (1 + TAP_HEART_SPREAD × (heart − 60) / 40)
#                 × state_mult
# where state_mult = TAP_STATE_FLOOR
#                    + TAP_STATE_STAMINA_WEIGHT × (stamina/100)
#                    + TAP_STATE_HEALTH_WEIGHT × (health/max_health)
# max state_mult = FLOOR + STAM_W + HEALTH_W = 1.0 at fresh/healthy.
# min state_mult = FLOOR at fully gassed & fully hurt (excl KO).
TAP_HEART_SPREAD           = 0.30    # heart=100 → +30% threshold, heart=20 → -30%
TAP_STATE_FLOOR            = 0.70    # min state_mult (gassed+hurt taps early)
TAP_STATE_STAMINA_WEIGHT   = 0.15
TAP_STATE_HEALTH_WEIGHT    = 0.15

# Refusal band: progress units past effective_tap. Inside band → still
# refusing; past band end → sleep (choke) or injury (joint_lock).
REFUSAL_WIDTH_BASE         = 15.0    # progress units past effective_tap
REFUSAL_HEART_SPREAD       = 0.60    # heart=100 → band 24; heart=20 → 6

# Joint-lock injury severity buckets (progress overshoot past band).
# Deeper overshoot → higher severity. All expressed as multiplier
# of REFUSAL_WIDTH_BASE. Bucketing:
#   overshoot < 1.0 × WIDTH → MODERATE
#   overshoot ∈ [1.0, 2.0) × WIDTH → SEVERE
#   overshoot ≥ 2.0 × WIDTH → CAREER
# (MINOR reserved for scratch-level; §5a joint-lock finish is always
# at least a torn-something → MODERATE floor.)


# ============================================================================
# CHIN + COMPOSURE wiring constants (PROVISIONAL, P3-5 calibrates)
# ============================================================================
# apply_damage's KD/rock rolls gain a chin modulation factor:
#   factor = 1 − CHIN_KD_RESIST_SPREAD × (chin − 60) / 40
# chin=100 → 1 − 0.30 = 0.70 (30% less KD chance); chin=20 → 1.30.
# Clamped [FLOOR, CAP].
CHIN_KD_RESIST_SPREAD      = 0.30
CHIN_KD_RESIST_FLOOR       = 0.50
CHIN_KD_RESIST_CAP         = 1.50
CHIN_ROCK_RESIST_SPREAD    = 0.30
CHIN_ROCK_RESIST_FLOOR     = 0.50
CHIN_ROCK_RESIST_CAP       = 1.50

# Composure modulates rock_duration (high composure = shorter rock)
# and the rocked d_eff × 0.5 exploit (high composure = less exploitable).
#   rock_dur_mult = 1 − COMPOSURE_ROCK_DUR_SPREAD × (composure − 60)/40
#   rocked_d_eff_mult = 0.5 + COMPOSURE_ROCK_EXPLOIT_SPREAD × (composure − 60)/40
# composure=100 → dur×0.60, exploit=0.65 (less exploitable);
# composure=20 → dur×1.40, exploit=0.35 (more exploitable).
COMPOSURE_ROCK_DUR_SPREAD  = 0.40
COMPOSURE_ROCK_DUR_FLOOR   = 0.50
COMPOSURE_ROCK_DUR_CAP     = 1.50
COMPOSURE_ROCK_EXPLOIT_SPREAD = 0.30
COMPOSURE_ROCK_EXPLOIT_FLOOR  = 0.30
COMPOSURE_ROCK_EXPLOIT_CAP    = 0.85


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
    GUARD_PULL = "guard_pull"
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
# BALANCE CONSTANTS — exported for fight_integration.py
# ============================================================================
# ENGINE-DEAD-KNOBS1 (2026-07-11): DAMAGE_MULTIPLIER = 0.55 removed —
# imported by fight_integration but never read (FI uses its own
# FI_DAMAGE_MULTIPLIER=0.48 module const). See two_engine_consolidation_diag1.md.
FLASH_KO_DAMAGE_THRESHOLD    = 70.0
FLASH_KO_BASE_CHANCE         = 0.03
FLASH_KO_MAX_CHANCE          = 0.12
TKO_GNP_HEALTH_THRESHOLD     = 18.0   # GROUND-STOPPAGE-FIX1: was 25.0 —
TKO_GNP_BASE_CHANCE          = 0.15   # raised so fighters must be more
TKO_GNP_MAX_CHANCE           = 0.45   # hurt before ref-stop rolls are
TKO_STANDING_HEALTH_THRESHOLD= 15.0   # eligible. Was 20.0 for standing.
TKO_STANDING_BASE_CHANCE     = 0.10

# GROUND-STOPPAGE-FIX1 — defender-durability multiplier for the two big
# accumulated-damage TKO paths (TKO_GNP + TKO_STANDING at
# fight_integration.py:1060-1107). Pre-fix, both fired on pure
# health-under-threshold + rocked/KD-count checks with ZERO defender-
# attribute respect — a granite-chinned fighter got stopped at the same
# rate as a china-chinned one. Post-fix, the tko_chance is scaled by:
#   max(FLOOR, 1 - chin/CHIN_DIV - heart/HEART_DIV - composure/COMP_DIV)
# Mirrors the shape already used by the smaller Path C / D / E accumulator
# stoppages (GnP-accumulator TKO, clinch body TKO, ref stoppage — all at
# fight_integration.py:901-1000) that ALREADY factor heart+composure.
# This ship extends the same durability language to A + B and adds CHIN
# as a first-class factor across all of them, so flash-KO (post its own
# fix) and accumulated-TKO now respect the same attribute set.
#
# Calibration reference: elite durability (chin 90 / heart 90 / composure
# 90) → 1 - 0.30 - 0.26 - 0.20 = 0.24 → clamped to FLOOR (0.35). Roughly
# HALVES the TKO roll. Poor durability (all 40) → 1 - 0.13 - 0.11 - 0.09
# = 0.67 → 67% of base roll. Fragile fighters still get stopped.
TKO_DURABILITY_FLOOR             = 0.35
TKO_DURABILITY_CHIN_DIVISOR      = 300.0
TKO_DURABILITY_HEART_DIVISOR     = 350.0
TKO_DURABILITY_COMPOSURE_DIVISOR = 450.0

# GNP-DAMAGE-BUFF1 — dominant-position damage multiplier.
# Read by calculate_strike_damage when the attacker is the top fighter
# in a DOMINANT position (MOUNT / SIDE_CONTROL_TOP / BACK_MOUNT / etc.).
# Applied BEFORE FI_DAMAGE_MULTIPLIER so composition is clean:
#   final_damage = base × strength × … × dominant_mult × FI_DAMAGE_MULTIPLIER
# Real-MMA reference: strikes from mount are 2-3× standing damage. The
# sim historically ran GnP at ~0.6× standing (CONTROL-CONVERSION-DIAG1
# §2b: Wr-Str wrestler ground damage 52 ≈ striker ground damage 48
# despite 64% control). Value chosen by GNP-DAMAGE-BUFF1 sweep.
GNP_DOMINANT_DAMAGE_MULT     = 1.25

# STRIKE-SKILL-DMG1 phase 1a — skill-into-damage dial.
# Read at call time from this module global inside
# calculate_strike_damage (plain name lookup, not captured into a
# local) so the harness can sweep K by rebinding this attribute
# between runs without any engine edit. K=1.0 chosen from the
# sweep grid (Commit 2): arm E (striking 88v55) row K=1.0
# p_fav=0.6945 ±0.0206, KO+TKO share 0.383, mean_rounds 2.467.
STRIKE_SKILL_DAMAGE_K        = 1.0

# STRIKE-SKILL-DMG1 phase 1a — safety floor on the damage
# multiplier. At K=1.0 the unclamped factor range for legal skills
# 1-99 is [0.26, 1.24], so the 0.25 floor is deterministically
# inert (max(0.25, ≥0.26) = the unclamped value). It exists to
# protect future K retunes from producing negative or near-zero
# damage factors on low-skill fighters. Plain-global read at call
# time, same pattern as STRIKE_SKILL_DAMAGE_K.
STRIKE_SKILL_DAMAGE_FLOOR    = 0.25

# STRIKE-SKILL-DMG1 phase 1b — kick-family gap-into-damage dial.
# Two-sided: factor = 1 + K * (attacker.kicks - defender.kicks) / 100,
# clamped to [FLOOR, CEIL]. Plain-global reads at call time so the
# harness can sweep K by module attribute rebind without any engine
# edit. Attacker- AND defender-side read (defender-side stays
# within the replaced cliffs' existing precedent — no new defender
# channel opens). K=1.0 chosen by Van off the phase-1b sweep grid
# (Commit 2): arm E (striking family 88v55) refill +5.05pp vs the
# cliff's +3.75pp on the same arm; arm H4 (kicks 80v55, the
# cliff's canonical instance) refill +6.60pp vs the cliff's
# +5.55pp. See CLAUDE.md STRIKE-SKILL-DMG1 phase 1b filing for
# the full grid and the E re-choose above the 1a band.
# Clamps [0.5, 1.5] are ACTIVE PROTECTION (not deterministically
# inert like the 1a floor) — legal skill gaps range up to ±98
# (99-vs-1), where at K=1.0 the unclamped factor would reach ±1.98.
KICK_GAP_DAMAGE_K            = 1.0
KICK_GAP_DAMAGE_FLOOR        = 0.5
KICK_GAP_DAMAGE_CEIL         = 1.5

# ============================================================================
# P5-A FINISH MODEL — health as stoppage pressure (D9, structural)
# ============================================================================
# ONE central helper (`check_stoppage`) replaces the twelve scattered
# accumulator-driven stoppage rolls (F1-F7, F11-F13 in the P5-A census).
# ~8 knobs replace ~55. Old constants stay as damage-input dials only;
# their stoppage-decision roles are RETIRED. See the P5-A filing for
# the mapping and the wrong-numbers rule application.
#
# Model:
#   - HEALTH is the stoppage pressure meter (D1 promoted).
#   - Effective critical line = BASE - HEART_LINE_SHIFT * ((heart-50)/50)
#     + rocked-unanswered bump - safe-in-guard damp.
#   - Once per exchange + once per between-round gap, roll a quadratic
#     curve on the slack below the critical line. No cliffs.
#   - Between-round check gets BETWEEN_ROUND_MULT so cornermen and
#     doctors have real teeth.
# Provisional values chosen to APPROXIMATE current behavior — P5-C
# calibrates. Reference: current TKO_GNP fires when health<18 with
# 15-45% roll; new curve fires when health<critical_line with
# CURVE_STEEPNESS * (slack/critical)^2 — at health=10, heart=70,
# critical=~34, p = 0.9 * (24/34)^2 = 0.45 (in the same range).
FINISH_CRITICAL_LINE_BASE       = 40.0
FINISH_CURVE_STEEPNESS          = 0.90
FINISH_HEART_LINE_SHIFT         = 20.0
FINISH_CONTEXT_ROCKED_BUMP      = 8.0
FINISH_CONTEXT_GUARD_DAMP       = 5.0
FINISH_BETWEEN_ROUND_MULT       = 2.5
FINISH_LEG_KICK_ACCUM_THRESHOLD = 6     # carve-out (D12, private dial)
FINISH_CUT_STOP_THRESHOLD       = 2     # carve-out (structural cuts)


def _finish_specialty_label(strike_val: str, target_area: str,
                             health_zero: bool) -> str:
    """Strike-specialty label routing (F8 preserved from old model)."""
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
    if health_zero:
        return _specialty_map.get(strike_val, "KO")
    if target_area == "body":
        return _specialty_map.get(strike_val, "TKO (Body Shot)")
    return "TKO"


def check_stoppage(defender_state, defender, context: dict) -> Optional[str]:
    """
    THE ONE CHECK. Returns method string if fight stops, else None.

    Args:
        defender_state: FighterState of the fighter under pressure.
        defender: FighterAttributes of same.
        context: dict carrying label + probability inputs. Keys read:
            - 'is_between_round' (bool): between-round check
            - 'current_round' (int): for corner-stoppage eligibility
            - 'attacker_is_top' (bool): dominant-position label routing
            - 'position' (str): position enum name for label routing
            - 'target_area' (str): 'head'|'body'|'legs' — label routing
            - 'strike_value' (str): strike enum value — specialty map
            - 'rocked_unanswered' (bool): context bump
            - 'safe_in_guard' (bool): context damp
            - 'unanswered_streak' (int): for referee-stoppage label routing

    Naming table:
        health <= 0                              → KO (specialty or fallback)
        between_round + cuts >= threshold        → TKO (Doctor Stoppage - Cuts)
        between_round + KDs >= 2 + round >= 2    → TKO (Corner Stoppage)
        between_round otherwise                  → TKO (Doctor Stoppage)
        in_exchange + dominant + top             → TKO (Ground and Pound)
        in_exchange + clinch + body              → TKO (Body Shots)
        in_exchange + body                       → TKO (Body Shot)  (specialty for body_kick)
        in_exchange + rocked + unanswered >= 2   → TKO (Referee Stoppage)
        otherwise                                → TKO
    """
    strike_val = context.get('strike_value', '') or ''
    target_area = context.get('target_area', '') or ''

    # Health <= 0 is the KO trigger. Label from strike specialty.
    if defender_state.health <= 0:
        return _finish_specialty_label(strike_val, target_area, health_zero=True)

    # Effective critical line: heart shifts it down, context nudges.
    heart = getattr(defender, 'heart', 70)
    heart_shift = FINISH_HEART_LINE_SHIFT * ((heart - 50) / 50.0)
    critical_line = FINISH_CRITICAL_LINE_BASE - heart_shift
    if context.get('rocked_unanswered', False):
        critical_line += FINISH_CONTEXT_ROCKED_BUMP
    if context.get('safe_in_guard', False):
        critical_line -= FINISH_CONTEXT_GUARD_DAMP
    critical_line = max(5.0, critical_line)

    if defender_state.health >= critical_line:
        return None

    slack = critical_line - defender_state.health
    p = FINISH_CURVE_STEEPNESS * (slack / critical_line) ** 2
    if context.get('is_between_round', False):
        p *= FINISH_BETWEEN_ROUND_MULT
    p = min(0.95, p)

    if random.random() >= p:
        return None

    # FIRED — pick label from circumstances.
    if context.get('is_between_round', False):
        cuts = getattr(defender_state.damage, 'cuts', 0)
        if cuts >= FINISH_CUT_STOP_THRESHOLD:
            return "TKO (Doctor Stoppage - Cuts)"
        kds = getattr(defender_state, 'knockdowns_total', 0)
        cur_round = context.get('current_round', 1)
        if kds >= 2 and cur_round >= 2:
            return "TKO (Corner Stoppage)"
        return "TKO (Doctor Stoppage)"

    # In-exchange labels.
    position = context.get('position', '')
    pos_upper = str(position).upper() if position else ''
    is_top = context.get('attacker_is_top', False)

    if is_top and any(p2 in pos_upper for p2 in
                       ('MOUNT', 'BACK_MOUNT', 'SIDE_CONTROL')):
        return "TKO (Ground and Pound)"

    in_clinch = any(p2 in pos_upper for p2 in
                     ('CLINCH', 'DIRTY_BOXING', 'THAI_PLUM',
                      'OVER_UNDER', 'PLUM'))
    if target_area == 'body' and in_clinch:
        return "TKO (Body Shots)"

    if target_area == 'body':
        return _finish_specialty_label(strike_val, target_area, health_zero=False)

    if defender_state.is_rocked and context.get('unanswered_streak', 0) >= 2:
        return "TKO (Referee Stoppage)"

    return _finish_specialty_label(strike_val, target_area, health_zero=False)


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


# STAMINA-DRAIN1: drain-side knobs on FighterState.spend_stamina.
# effective = amount * DRAIN_SCALE_K * (1 + DRAIN_CARDIO_S * (60 - cardio_rating) / 40)
# B9 (2026-09-01, Van signal 2): K=0.6, S=0.5.
DRAIN_SCALE_K   = 0.6
DRAIN_CARDIO_S  = 0.5

# STAMINA-LEVER2 (P3-4a): regen-side cardio-spread multiplier on
# FighterState.recover_stamina — mirror of DRAIN's cardio spread.
# effective = amount * (1 + REGEN_CARDIO_S * (cardio_rating - 60) / 40)
# C20 (2026-09-04, Van): S_r=0.5 ratified — minimal dose that pays
# T1_R3 debt (14.12 → 29.2, target ≥20). P3-5 calibration may retune.
REGEN_CARDIO_S = 0.5


# STAMINA-DMGCURVE1: damage-side stamina curve at fe:2492 call site.
# Identity at DMG_COMPRESS=1.0 → function returns (s/100)*0.5+0.5 for
# every stamina (byte-identical to today's inline factor).
DMG_PIVOT       = 0.0
DMG_COMPRESS    = 1.0

def damage_stamina_factor(stamina):
    f = (stamina / 100) * 0.5 + 0.5
    p = (DMG_PIVOT / 100) * 0.5 + 0.5
    if stamina <= DMG_PIVOT:
        return f
    return p + DMG_COMPRESS * (f - p)


@dataclass
class FighterState:
    """Complete state of a fighter during the fight"""
    fighter_id: str
    name: str
    
    health: float = 100.0
    max_health: float = 100.0  # For recovery calculations
    stamina: float = 100.0
    damage: BodyPartDamage = field(default_factory=BodyPartDamage)
    
    is_rocked: bool = False
    rock_duration: int = 0
    is_knocked_down: bool = False
    knockdowns_this_round: int = 0
    knockdowns_total: int = 0
    
    chin_compromised: bool = False
    momentum: float = 50.0
    
    # Recovery attribute (stored for between-round calculations)
    recovery_rating: int = 50
    # STAMINA-DRAIN1: cardio at fight time — used by spend_stamina.
    # Default 60 = neutral (g=1 at any S). Callers pass fighter.cardio.
    cardio_rating: int = 60
    # P3-4c — chin + composure at fight time for the KD/rock/rocked-
    # exploit wiring. Defaults at 60 = neutral (all resistance mults
    # collapse to 1.0, all exploit mults collapse to 0.5). Callers
    # pass fighter.chin / fighter.composure. Byte-inert when
    # FI_CHIN_WIRING_ENABLED / FI_COMPOSURE_WIRING_ENABLED are False.
    chin_rating: int = 60
    composure_rating: int = 60

    def apply_damage(self, amount: float, target: str = "head") -> Tuple[bool, bool]:
        """Apply damage and return (is_knockdown, is_finish)."""
        self.damage.apply_damage(amount, target)
        self.health = max(0, self.health - amount)
        self.momentum = max(0, self.momentum - amount * 0.5)
        
        is_knockdown = False
        is_finish = False
        
        if self.health <= 0:
            is_finish = True
        elif target == "body" and self.damage.body >= 65:
            # Accumulated body damage — liver shot TKO
            # Fighter can't continue from cumulative body punishment
            _body_tko_chance = min(0.40, (self.damage.body - 65) * 0.04)
            if random.random() < _body_tko_chance:
                is_finish = True
        elif target == "head" and amount >= 12:
            # ── Chin erosion — knockdowns make next finish easier ──
            # Each prior KD adds 4 to _chin_erosion; multiplier scales
            # KD + rock chance up to 1.30× at 12 points of erosion.
            _erosion = getattr(self, '_chin_erosion', 0)
            _erosion_mult = 1.0 + min(0.30, _erosion * 0.025)
            # P3-4c — CHIN attribute modulation. Behind flag; default
            # OFF is byte-identical (factor forced to 1.0). When ON,
            # per-attribute chin scales KD and rock chances via the
            # CHIN_KD_RESIST_SPREAD / CHIN_ROCK_RESIST_SPREAD constants.
            _chin_kd_mult = 1.0
            _chin_rock_mult = 1.0
            try:
                # Access via module attr so runtime flag flips propagate
                # (`from X import Y` would bind the value at import time
                # and never see subsequent wreg.FI_CHIN_WIRING_ENABLED
                # mutations — silent no-op bug on OFF/ON gates).
                import window_registry as _wreg_kd
                if _wreg_kd.FI_CHIN_WIRING_ENABLED:
                    _chin_stat = getattr(self, 'chin_rating', 60)
                    _kd_delta = CHIN_KD_RESIST_SPREAD * ((_chin_stat - 60) / 40.0)
                    _rk_delta = CHIN_ROCK_RESIST_SPREAD * ((_chin_stat - 60) / 40.0)
                    _chin_kd_mult = max(CHIN_KD_RESIST_FLOOR,
                                        min(CHIN_KD_RESIST_CAP, 1.0 - _kd_delta))
                    _chin_rock_mult = max(CHIN_ROCK_RESIST_FLOOR,
                                          min(CHIN_ROCK_RESIST_CAP, 1.0 - _rk_delta))
            except ImportError:
                pass
            if random.random() < amount * 0.015 * _erosion_mult * _chin_kd_mult:
                is_knockdown = True
                self.knockdowns_this_round += 1
                self.knockdowns_total += 1
                # Cumulative tax — represents real damage.
                self._chin_erosion = _erosion + 4
            elif random.random() < amount * 0.025 * _erosion_mult * _chin_rock_mult:
                self.is_rocked = True
                # ── Rock stamina drain ────────────────
                # Absorbing a rocking shot changes breathing —
                # legs get heavy immediately.
                self.spend_stamina(4)
                # HIGH RECOVERY: Shake off cobwebs faster
                reduction = 1 if self.recovery_rating >= 80 else 0
                # P3-4c — COMPOSURE modulation of rock_duration. Behind
                # flag; OFF → byte-identical to pre-wire.
                _composure_dur_mult = 1.0
                try:
                    import window_registry as _wreg_dur
                    if _wreg_dur.FI_COMPOSURE_WIRING_ENABLED:
                        _comp_stat = getattr(self, 'composure_rating', 60)
                        _dur_delta = COMPOSURE_ROCK_DUR_SPREAD * ((_comp_stat - 60) / 40.0)
                        _composure_dur_mult = max(COMPOSURE_ROCK_DUR_FLOOR,
                            min(COMPOSURE_ROCK_DUR_CAP, 1.0 - _dur_delta))
                except ImportError:
                    pass
                _raw_dur = random.randint(1, 3) - reduction
                self.rock_duration = max(1, int(round(_raw_dur * _composure_dur_mult)))
        
        return is_knockdown, is_finish
    
    def recover_stamina(self, amount: float) -> None:
        # STAMINA-LEVER2: cardio-spread multiplier at the choke.
        # Identity at S_r=0.0 → effective = amount (byte-identical).
        effective = amount * (
            1 + REGEN_CARDIO_S * (self.cardio_rating - 60) / 40)
        self.stamina = min(100, self.stamina + effective)
    
    def spend_stamina(self, amount: float) -> None:
        # STAMINA-DRAIN1: K + cardio-spread multiplier at the choke.
        # Identity at K=1.0, S=0.0 → effective = amount (byte-identical).
        effective = amount * DRAIN_SCALE_K * (
            1 + DRAIN_CARDIO_S * (60 - self.cardio_rating) / 40)
        self.stamina = max(0, self.stamina - effective)
    
    def new_round(self) -> None:
        """Between-round recovery using recovery attribute."""
        self.knockdowns_this_round = 0
        self.is_knocked_down = False

        # Recovery stat now meaningfully separates fighters.
        # Base: 15 (up from 10 — accounts for new stamina drains)
        # Bonus: scales 0-25 with recovery stat (was 0-10)
        # Elite (90+) gets back ~40 stamina between rounds;
        # poor (40-) gets back ~18.
        # R1-REFILL1: skip refill at R1 to preserve condition-derived
        # starting_stamina (cut/fatigue). `!= 1` means unset
        # _current_round (default 0) still refills — protects any
        # caller that doesn't propagate round explicitly.
        if getattr(self, '_current_round', 0) != 1:
            base_recovery = 15
            _rec = self.recovery_rating
            bonus_recovery = (_rec / 100) * 25
            # Championship round bonus — adrenaline in late rounds
            if getattr(self, '_current_round', 0) >= 4:
                bonus_recovery *= 1.3
            self.stamina = min(100,
                self.stamina + base_recovery + bonus_recovery)

        # Health recovery: up to 8 points (was 5).
        health_regain = self.recovery_rating * 0.08
        self.health = min(self.max_health,
            self.health + health_regain)

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

    # Tracks continuous exchanges in ANY dominant grappling cluster
    # (BACK_MOUNT, TRUCK, MOUNT, SIDE_CONTROL, CRUCIFIX, NORTH_SOUTH).
    # Unlike position_duration, this does NOT reset when transitioning between
    # positions within the same dominant cluster (e.g. BACK_MOUNT ↔ TRUCK).
    # Reset only when the bottom fighter escapes to a neutral/standing position.
    dominant_control_duration: int = 0
    
    submission_active: bool = False
    submission_type: Optional[SubmissionType] = None
    submission_attacker_id: Optional[str] = None
    submission_progress: float = 0.0
    submission_escape_progress: float = 0.0
    # P3-4c §5a — effective tap threshold at the moment of the last tick.
    # Stashed by process_submission_progress so fi can tier escape drama
    # by progress-vs-actual-threshold (not raw config threshold).
    submission_effective_threshold: float = 0.0
    
    last_action: Optional[str] = None
    momentum_fighter_id: Optional[str] = None
    
    # Rivalry heat level (0-100) - affects damage and aggression
    heat_level: int = 0
    
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
        self.dominant_control_duration = 0
        self.submission_active = False
        # PREGEN-ROUND-WIRE1: propagate round to fighters (live path sets this in fi._init_round)
        self.fighter1._current_round = self.current_round
        self.fighter2._current_round = self.current_round
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
    """Configuration for a fight.

    STAGE 0d (2026-07-12) — CONFIG INVARIANT CONTRACT.

    Three fields — exchanges_per_round, damage_multiplier, standup_threshold —
    are ONE atomic invariant. They were tuned together against live-play, and
    changing one without the others is the bug the fight-start assertion
    (_assert_sanctioned_config, below) exists to catch. Live-play's values
    are the surviving contract; the defaults on this class ARE that contract.

    Two OTHER triples are sanctioned by the assertion allowlist. Each carries
    a death date:

      LIVE_PLAY      = (55, 0.48, 10)  the surviving contract (this class's defaults)
      PRE_GEN_LEGACY = (55, 0.42, 6)   KNOWN DRIFT. Deleted at Stage 3.
                                       Do not tune.
      FI_FALLBACK    = (55, 0.48, 6)   KNOWN CORNER. Not on production
                                       live-play path. Deleted at Stage 3.
                                       Do not tune.

    At Stage 3 (pre-gen delegation to live-play engine + FI/FE split
    retirement) the two lower entries are deleted from the allowlist and the
    assertion collapses to the single invariant. Write those deletions as a
    one-line diff with a measurement attached.

    DISCIPLINE — NO SITE INHERITS THESE THREE FIELDS. Every construction
    site in the tree passes them explicitly. If you find yourself calling
    FightConfig() and only setting scheduled_rounds, you are creating the
    exact class of drift this ship exists to prevent — either use one of
    the pinned classmethods (standard_fight / championship_fight /
    main_event, all pinned to PRE_GEN_LEGACY) or pass all three fields
    explicitly.

    The assertion sits BEFORE the heat replace() at simulate_fight:~3922.
    Heat scaling (up to ×1.20 on damage_multiplier) is sanctioned mutation
    inside FE, NOT drift — filed for the Stage 1 parity map as an FI/FE
    divergence (FI has no heat mechanism).
    """
    scheduled_rounds: int = 3
    # LIVE_PLAY contract — see docstring. NO SITE INHERITS THESE.
    exchanges_per_round: int = 55
    damage_multiplier: float = 0.48
    standup_threshold: int = 10
    # ENGINE-DEAD-KNOBS1 (2026-07-11): default was 2, but both engines
    # hardcoded the threshold at `>= 3`. Default lifted to 3 to match the
    # actual hardcoded behavior before the threshold check is unified with
    # the config field below. Do NOT tune this value at ship time —
    # anything ≠ 3 is a behavior change deferred to consolidation.
    doctor_check_cut_threshold: int = 3

    submission_progress_to_finish: float = 70.0  # Was 80.0, then 70.0 — keep
    submission_escape_threshold: float = 85.0

    is_title_fight: bool = False
    is_main_event: bool = False

    # STAGE 0d — factories pin PRE_GEN_LEGACY (55, 0.42, 6) EXPLICITLY.
    # Every classmethod below is a FE-fed pre-gen path. Byte-identical to
    # pre-Stage-0d behavior (pre-gen ran at 0.42/6 by INHERITING the OLD
    # defaults; now runs at 0.42/6 by explicit pin — same value, no
    # inheritance). Deleted at Stage 3 when pre-gen delegates to
    # live-play's engine and PRE_GEN_LEGACY dies.
    @classmethod
    def standard_fight(cls) -> 'FightConfig':
        return cls(
            scheduled_rounds=3,
            exchanges_per_round=55,
            damage_multiplier=0.48,
            standup_threshold=10,
        )

    @classmethod
    def championship_fight(cls) -> 'FightConfig':
        return cls(
            scheduled_rounds=5,
            exchanges_per_round=55,
            damage_multiplier=0.48,
            standup_threshold=10,
            is_title_fight=True,
            is_main_event=True,
        )

    @classmethod
    def main_event(cls) -> 'FightConfig':
        return cls(
            scheduled_rounds=5,
            exchanges_per_round=55,
            damage_multiplier=0.42,
            standup_threshold=6,
            is_main_event=True,
        )


# STAGE 0d — SANCTIONED CONFIG TRIPLES.
# The assertion at fight start allowlists exactly these. Anything else
# raises. See FightConfig docstring for the full contract and death dates.
_TRIPLE_LIVE_PLAY = (55, 0.48, 10)
_TRIPLE_PRE_GEN_LEGACY = (55, 0.42, 6)
_TRIPLE_FI_FALLBACK = (55, 0.48, 6)
_SANCTIONED_TRIPLES = {
    _TRIPLE_LIVE_PLAY,        # the surviving contract
    _TRIPLE_PRE_GEN_LEGACY,   # KNOWN DRIFT. Deleted at Stage 3. Do not tune.
    _TRIPLE_FI_FALLBACK,      # KNOWN CORNER. Deleted at Stage 3. Do not tune.
}


def _assert_sanctioned_config(config: 'FightConfig') -> None:
    """Raise if config's (exchanges, damage, standup) triple is not in the
    sanctioned allowlist. Called at fight-start on BOTH engine paths
    (fight_engine.simulate_fight, fight_integration.NarratedFightSimulator).

    Placed UPSTREAM of the heat replace() in simulate_fight: heat scaling
    is a sanctioned mutation, not drift. See the comment at the mutation
    site for the rationale.
    """
    triple = (
        config.exchanges_per_round,
        config.damage_multiplier,
        config.standup_threshold,
    )
    if triple not in _SANCTIONED_TRIPLES:
        raise AssertionError(
            f"UNSANCTIONED CONFIG TRIPLE: (exchanges={triple[0]}, "
            f"damage_multiplier={triple[1]}, standup_threshold={triple[2]}). "
            f"Allowlist:\n"
            f"  LIVE_PLAY      = {_TRIPLE_LIVE_PLAY}   the surviving contract\n"
            f"  PRE_GEN_LEGACY = {_TRIPLE_PRE_GEN_LEGACY}    KNOWN DRIFT. Deleted at Stage 3.\n"
            f"  FI_FALLBACK    = {_TRIPLE_FI_FALLBACK}    KNOWN CORNER. Deleted at Stage 3.\n"
            f"See FightConfig docstring for the full contract."
        )


# ============================================================================
# GAMEPLAN (GAMEPLAN-WIRE1 — additive tendency dial; not yet consumed)
# ============================================================================

@dataclass(frozen=True)
class Gameplan:
    """Per-fighter tendency dial threaded through the fight call chain.

    GAMEPLAN-WIRE1 (this ship) threads the object through
    simulate_narrated_fight → NarratedFightSimulator → select_action
    with an additive contract: existing callers that don't pass a
    Gameplan get byte-identical behavior. select_action accepts the
    param and does not read it — SHIP2 (GAMEPLAN-DIAL-AGGR1) will
    activate the first dial. See outputs/gameplan_design1.md §3 for
    the full dial-step table and outcome tradeoffs.

    Fields (all default to identity — no bias):
        aggression:   -1 patient       · 0 neutral · +1 forward
        range_bias:   -1 keep-standing · 0 neutral · +1 grapple-seek
        finish_seek:  -1 safe          · 0 neutral · +1 hunt
        preset_name:  optional label for logging/UI ('AGGRESSIVE', etc.)
    """
    aggression: int = 0
    range_bias: int = 0
    finish_seek: int = 0
    preset_name: str = 'BALANCED'


def neutral_gameplan() -> Gameplan:
    """Identity Gameplan — no bias on any dial. Used as the effective
    default when None is passed through the call chain."""
    return Gameplan()


# GAMEPLAN-DIAL-AGGR1 — IQ execution gate for dial effects.
# Per gameplan_design1.md §4: low-IQ fighters under-execute the plan;
# tired fighters revert further. Applied to the DELTA from 1.0, not
# to the multiplier itself — so at IQ 50 the fighter gets 40% of the
# intended dial swing; at IQ 86+ full effect. Extracted as a helper
# so all dial sites use the same formula (no per-site drift).
def dial_execution(fighter_attrs, fighter_state) -> float:
    """Return the fraction of a dial delta the fighter actually executes.
    IQ 50 → 0.4 · IQ 80 → 0.9 · IQ 86+ → 1.0. Stamina under 40 → ×0.7.
    Safe on missing attrs (defaults IQ 65, stamina 100)."""
    _iq = getattr(fighter_attrs, 'fight_iq', 65) or 65
    _exec = min(1.0, 0.4 + (_iq - 50) / 60.0)
    _exec = max(0.0, _exec)
    _stamina = getattr(fighter_state, 'stamina', 100.0) or 100.0
    if _stamina < 40:
        _exec *= 0.7
    return _exec


# ============================================================================
# FIGHT EVENT (for commentary generation)
# ============================================================================

@dataclass
class FightEvent:
    """A single event during a fight for commentary generation."""
    event_type: str  # "strike", "takedown", "submission", "knockdown", "position", "round_start", "round_end", "finish"
    round_num: int
    exchange_num: int
    actor_id: str
    actor_name: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    action: Optional[str] = None  # Specific action (e.g., "jab", "single_leg", "armbar")
    success: bool = True
    damage: float = 0.0
    position: Optional[str] = None
    new_position: Optional[str] = None
    is_knockdown: bool = False
    is_finish: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "round": self.round_num,
            "exchange": self.exchange_num,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "action": self.action,
            "success": self.success,
            "damage": self.damage,
            "position": self.position,
            "new_position": self.new_position,
            "is_knockdown": self.is_knockdown,
            "is_finish": self.is_finish,
            "extra": self.extra
        }


# ============================================================================
# FIGHTER ATTRIBUTES INTERFACE
# ============================================================================

@dataclass
class FighterAttributes:
    """Fighter attributes for the fight engine (19-attribute system).

    P3-4d (C23): POWER split from STRENGTH. Strength keeps the
    grappling-physicality lanes (throws/slams, clinch break, escape
    assist); POWER takes over striking-damage + flash-KO. Behind
    FI_POWER_WIRING_ENABLED (default OFF) at the damage sites so the
    ship is byte-inert until the flag flips. Default power=50 mirrors
    strength=50 for any test constructor that doesn't specify power.
    """
    fighter_id: str
    name: str

    # Physical (6)
    strength: int = 50      # Grappling physicality — throws/slams/clinch break
    speed: int = 50         # Hand speed, movement, reaction time
    cardio: int = 50        # Stamina, gas tank
    chin: int = 50          # Ability to absorb damage
    recovery: int = 50      # Between-round recovery, shaking off being hurt
    power: int = 50         # Striking damage, KD/flash-KO chance (P3-4d D7)

    # Striking (4)
    boxing: int = 50            # Punching technique, combinations
    kicks: int = 50             # Kicking technique
    clinch_striking: int = 50   # Knees, elbows, dirty boxing
    striking_defense: int = 50  # Head movement, blocking, footwork

    # Grappling (5)
    takedowns: int = 50         # Ability to bring fight to ground
    takedown_defense: int = 50  # Sprawl, cage wrestling defense
    top_control: int = 50       # Holding position, GnP, preventing sweeps
    submissions: int = 50       # Finishing ability - chokes/locks
    guard: int = 50             # Sweeps, guard retention, getting back up

    # Clinch (1) — positional dominance, separate from clinch_striking damage
    clinch_control: int = 50    # Grip dominance, cage control, clinch entry/break

    # Mental (3)
    heart: int = 50         # Willingness to fight through adversity
    fight_iq: int = 50      # In-fight adjustments, strategy
    composure: int = 50     # Performance under pressure
    
    is_generational: bool = False
    
    # Fighting style for AI behavior
    fighting_style: Optional[Any] = None
    
    @property
    def overall_striking(self) -> int:
        """Calculate overall striking ability."""
        return (self.boxing * 2 + self.kicks + self.clinch_striking + self.striking_defense) // 5
    
    @property
    def overall_grappling(self) -> int:
        """Calculate overall grappling ability."""
        return (self.takedowns + self.top_control + self.submissions + self.guard + self.takedown_defense) // 5
    
    @property
    def overall(self) -> int:
        """Calculate overall fighter rating.

        P3-4d: physical composite now includes power (6 stats / 6).
        Same arithmetic shape as pre-C23; new stat contributes
        equally to the physical bucket.
        """
        physical = (self.strength + self.speed + self.cardio +
                    self.chin + self.recovery + self.power) // 6
        mental = (self.heart + self.fight_iq + self.composure) // 3
        return (self.overall_striking + self.overall_grappling + physical + mental) // 4
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            # Physical (6) — P3-4d added `power`
            "strength": self.strength,
            "speed": self.speed,
            "cardio": self.cardio,
            "chin": self.chin,
            "recovery": self.recovery,
            "power": self.power,
            # Striking (4)
            "boxing": self.boxing,
            "kicks": self.kicks,
            "clinch_striking": self.clinch_striking,
            "striking_defense": self.striking_defense,
            # Grappling (5)
            "takedowns": self.takedowns,
            "takedown_defense": self.takedown_defense,
            "top_control": self.top_control,
            "submissions": self.submissions,
            "guard": self.guard,
            # Clinch (1)
            "clinch_control": self.clinch_control,
            # Mental (3)
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
    fighter_attrs: FighterAttributes,
    fight_state: Optional['FightState'] = None,
) -> List[GrapplingAction]:
    """Get grappling actions available from current position.

    `fight_state` is optional — when provided, allows position_duration
    gates on actions like ENTER_TRUCK (stops back_mount ↔ truck cycling).
    """
    actions = []
    my_style_hint = detect_fighter_style(fighter_attrs)

    if position in STANDING_POSITIONS:
        actions.append(GrapplingAction.CLINCH_ENTRY)
        # Distance shots + snap-down gated on style — pure strikers
        # don't shoot double legs. Clinch trip path still available
        # via CLINCH_ENTRY → BODY_LOCK_TAKEDOWN.
        _striker_styles = ("muay_thai", "striker", "kickboxer",
                           "brawler", "counter_striker",
                           "point_fighter", "sprawl_and_brawl")
        if my_style_hint not in _striker_styles:
            actions.extend([
                GrapplingAction.SINGLE_LEG,
                GrapplingAction.DOUBLE_LEG,
            ])
            if fighter_attrs.takedowns >= 50:
                actions.append(GrapplingAction.SNAP_DOWN)
        if fighter_attrs.takedowns >= 60:
            actions.append(GrapplingAction.HIP_TOSS)
        if fighter_attrs.guard >= 70:  # Guard players can Imanari roll
            actions.append(GrapplingAction.IMANARI_ROLL)
        # BJJ fighters with low takedowns can pull guard from standing
        if my_style_hint == "bjj" and fighter_attrs.takedowns < 62:
            actions.append(GrapplingAction.GUARD_PULL)
    
    elif position in CLINCH_POSITIONS:
        actions.extend([
            GrapplingAction.BODY_LOCK_TAKEDOWN, GrapplingAction.TRIP,
            GrapplingAction.CLINCH_BREAK, GrapplingAction.PUSH_TO_CAGE
        ])
        if fighter_attrs.takedowns >= 70:
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
        if fighter_attrs.submissions >= 60:
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
            # Gate ENTER_TRUCK: only available in the first 3 ticks of
            # back mount. After that, forcing fighter to commit to strikes
            # or sub attempts instead of cycling BACK_MOUNT ↔ TRUCK.
            _bm_duration = getattr(fight_state, 'position_duration', 0) if fight_state else 0
            if fighter_attrs.submissions >= 65 and _bm_duration < 3:
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
            if fighter_attrs.guard >= 65:
                actions.append(GrapplingAction.ENTER_SINGLE_LEG_X)
        elif position == Position.HALF_GUARD_BOTTOM:
            actions.extend([
                GrapplingAction.ELEVATOR_SWEEP, GrapplingAction.REGUARD,
                GrapplingAction.STAND_UP
            ])
            if fighter_attrs.guard >= 60:
                actions.append(GrapplingAction.ENTER_SINGLE_LEG_X)
        elif position == Position.BUTTERFLY_GUARD_BOTTOM:
            actions.extend([
                GrapplingAction.BUTTERFLY_SWEEP, GrapplingAction.STAND_UP
            ])
            if fighter_attrs.guard >= 55:
                actions.append(GrapplingAction.ENTER_SINGLE_LEG_X)
        elif position in {Position.SIDE_CONTROL_BOTTOM, Position.MOUNT_BOTTOM}:
            actions.extend([
                GrapplingAction.SHRIMP_ESCAPE, GrapplingAction.BRIDGE_ESCAPE,
                GrapplingAction.ELBOW_ESCAPE, GrapplingAction.REGUARD
            ])
        elif position == Position.BACK_MOUNT_BOTTOM:
            actions.extend([
                GrapplingAction.GRANBY_ROLL,
                GrapplingAction.STAND_UP,   # Hip-escape to feet against cage
            ])
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
    Detect a fighter's primary style based on attributes.
    Returns one of 11 styles matching styles.py FightingStyle definitions.
    Thresholds calibrated for LOCAL tier (60-75 range) so styles emerge
    at mid-level play, not just elite.
    """
    striking_score    = (fighter.boxing * 2 + fighter.kicks) / 3
    wrestling_score   = (fighter.takedowns + fighter.top_control) / 2
    bjj_score         = (fighter.submissions + fighter.guard) / 2
    clinch_score      = (fighter.clinch_striking + fighter.clinch_control) / 2
    defense_score     = (fighter.striking_defense + fighter.composure) / 2
    pressure_score    = (fighter.cardio + fighter.heart + fighter.chin) / 3

    # Well-rounded check — if no skill more than 10 above others AND decent avg
    all_skills = [fighter.boxing, fighter.kicks, fighter.takedowns,
                  fighter.submissions, fighter.clinch_striking]
    skill_range = max(all_skills) - min(all_skills)
    avg_skill   = sum(all_skills) / len(all_skills)
    if skill_range <= 10 and avg_skill >= 68:
        return "balanced"

    # ── STYLE HINT: stored fighting_style as soft tiebreaker ───────────────
    # The stored style from world-gen/game_start reflects intent.
    # If stats are borderline, honor the stored style rather than defaulting
    # to balanced. Only fires when stats are close to a threshold.
    _hint = ""
    if hasattr(fighter, 'fighting_style') and fighter.fighting_style is not None:
        _fs = str(fighter.fighting_style.name if hasattr(fighter.fighting_style, 'name') else fighter.fighting_style).upper()
        _HINT_MAP = {
            "BJJ_SPECIALIST":   "bjj",
            "WRESTLER":         "wrestler",
            "MUAY_THAI":        "muay_thai",
            "GROUND_AND_POUND": "ground_and_pound",
            "SPRAWL_AND_BRAWL": "sprawl_and_brawl",
            "CLINCH_FIGHTER":   "clinch_fighter",
            "PRESSURE_FIGHTER": "pressure_fighter",
            "COUNTER_STRIKER":  "counter_striker",
            "POINT_FIGHTER":    "point_fighter",
            "STRIKER":          "striker",
            "SAMBO":            "sambo",
        }
        _hint = _HINT_MAP.get(_fs, "")

    # ── PRIMARY CHECKS (highest thresholds first) ──────────────────────────

    # Sambo: strong wrestling AND strong BJJ — the complete grappler
    # Real examples: Khabib, Makhachev, Chimaev
    if wrestling_score >= 72 and bjj_score >= 68:
        return "sambo"

    # Ground & Pound: wrestling + power, hunts TKO not sub
    # Real examples: early Khabib, DC, Derrick Lewis on the ground
    # Checked BEFORE wrestler since G&P adds a strength requirement —
    # otherwise a 70+ wrestling fighter with high strength gets caught
    # by the wrestler check and never reaches the more specific G&P check.
    if wrestling_score >= 65 and fighter.strength >= 68 and bjj_score < 65:
        return "ground_and_pound"

    # Pure Wrestler: wrestling dominant, BJJ secondary
    # Real examples: Usman, Covington, Belal
    if wrestling_score >= 70 and bjj_score < 65:
        return "wrestler"

    # BJJ Specialist: submission/guard dominant, wrestling not required
    # Real examples: Oliveira, Maia, Ryan Hall
    if bjj_score >= 70 and wrestling_score < 68:
        return "bjj"

    # Muay Thai: clinch + kicks combo — the complete 8-limb striker
    # Real examples: Aldo, Shevchenko, Yan
    if clinch_score >= 72 and fighter.kicks >= 68:
        return "muay_thai"

    # Sprawl & Brawl: elite TDD + strong striking — the anti-wrestler
    # Real examples: Liddell, Cro Cop, Wonderboy
    if fighter.takedown_defense >= 70 and striking_score >= 65:
        return "sprawl_and_brawl"

    # Clinch Fighter: cage pressure + dirty boxing + cardio
    # Real examples: Couture, Covington, Dvalishvili
    if clinch_score >= 65 and fighter.cardio >= 68 and wrestling_score >= 58:
        return "clinch_fighter"

    # Pressure Fighter: cardio + chin + heart — the walking forward style
    # Real examples: Gaethje, Holloway, Poirier
    if pressure_score >= 70 and striking_score >= 60:
        return "pressure_fighter"

    # Counter Striker: defense + composure + fight IQ — wait and punish
    # Real examples: Machida, Thompson, early Anderson
    if defense_score >= 68 and fighter.fight_iq >= 65 and striking_score >= 62:
        return "counter_striker"

    # Point Fighter: speed + defense + fight IQ — move and score
    # Real examples: Cruz, Dillashaw, early O'Malley
    if fighter.speed >= 70 and defense_score >= 65 and fighter.fight_iq >= 65:
        return "point_fighter"

    # Kickboxer: high kicks + boxing, weak grappling
    # Real examples: Holloway (early), Volkov, Machida (striking side)
    if fighter.kicks >= 70 and fighter.boxing >= 65 and wrestling_score < 58:
        return "kickboxer"

    # Pure Striker: boxing dominant
    if striking_score >= 68 and wrestling_score < 62 and bjj_score < 62:
        return "striker"

    # ── SECONDARY CHECKS (lower thresholds, style is present but not dominant) ─

    if wrestling_score >= 65 and bjj_score >= 62:
        return "sambo"
    if wrestling_score >= 63:
        return "wrestler"
    if bjj_score >= 63:
        return "bjj"
    if clinch_score >= 65 and fighter.kicks >= 62:
        return "muay_thai"
    if fighter.takedown_defense >= 65 and striking_score >= 60:
        return "sprawl_and_brawl"
    if pressure_score >= 65 and striking_score >= 58:
        return "pressure_fighter"
    if defense_score >= 63 and fighter.fight_iq >= 62:
        return "counter_striker"
    if striking_score >= 62:
        return "striker"

    # If stats don't clearly identify a style but we have a stored hint,
    # use it — the fighter was generated with that identity in mind.
    if _hint:
        return _hint
    return "balanced"


def is_grappler(fighter: FighterAttributes) -> bool:
    """Check if fighter prefers grappling over striking."""
    grappling = (fighter.takedowns + fighter.submissions + fighter.top_control + fighter.guard) / 4
    striking = (fighter.boxing + fighter.kicks) / 2
    return grappling > striking


def is_clinch_fighter(fighter: FighterAttributes) -> bool:
    """Check if fighter excels in clinch (Muay Thai, Sambo, Dirty Boxing).
    True specialists in either dimension qualify: elite striker (high
    clinch_striking, e.g. classic Muay Thai) OR elite controller (high
    clinch_control, e.g. cage-pressure Sambo). Combined-average gate
    filters out fighters who are merely average at both."""
    wrestling_ability = (fighter.takedowns + fighter.top_control) / 2
    bjj_ability = (fighter.submissions + fighter.guard) / 2
    has_clinch_skill = (
        (fighter.clinch_striking >= 70 or fighter.clinch_control >= 70)
        and (fighter.clinch_striking + fighter.clinch_control) / 2 >= 62
    )
    return has_clinch_skill or (wrestling_ability >= 70 and bjj_ability >= 65)


# ============================================================================
# ACTION DECISION ENGINE - STYLE AWARE
# ============================================================================

def select_action(
    fighter_attrs: FighterAttributes,
    opponent_attrs: FighterAttributes,
    fight_state: FightState,
    fighter_state: FighterState,
    gameplan: Optional['Gameplan'] = None,
) -> Tuple[str, Any]:
    """
    Select the best action based on position, attributes, and fight state.
    Now style-aware: wrestlers clinch against strikers, etc.

    GAMEPLAN-WIRE1: `gameplan` is accepted for future dial-based tendency
    bias but is NOT read this ship. SHIP2 (GAMEPLAN-DIAL-AGGR1) activates
    the AGGRESSION dial. Zero behavior change when the param is None or
    when a neutral Gameplan() is passed.
    """
    is_top = fight_state.top_fighter_id == fighter_attrs.fighter_id
    position = fight_state.position
    
    # Get available actions
    strikes = get_available_strikes(position, is_top)
    submissions = get_available_submissions(position, is_top, fighter_attrs)
    grappling = get_available_grappling_actions(position, is_top, fighter_attrs, fight_state)
    
    # Position secured check for submissions - must control position longer before sub attempts
    # In real MMA, fighters work position for a while before going for subs.
    # For dominant cluster (back mount / truck cycling) use the persistent counter
    # so the TRUCK↔BACK_MOUNT loop doesn't keep resetting the timer.
    _DOMINANT_CLUSTER_POSITIONS = {
        Position.BACK_MOUNT, Position.TRUCK, Position.MOUNT,
        Position.SIDE_CONTROL_TOP, Position.CRUCIFIX_TOP, Position.NORTH_SOUTH_TOP,
    }
    if position in _DOMINANT_CLUSTER_POSITIONS:
        position_secured = fight_state.dominant_control_duration >= 3
    else:
        # Ship Sub-Fix: elite BJJ sets up faster from bottom/guard
        # positions — skilled grapplers need fewer ticks to find the
        # opening. Dominant-cluster keeps the 3-tick threshold above.
        _subs = getattr(fighter_attrs, 'submissions', 0) or 0
        if _subs >= 85 and position in (GUARD_POSITIONS | INFERIOR_POSITIONS):
            _secure_threshold = 2
        elif _subs >= 75:
            _secure_threshold = 4
        else:
            _secure_threshold = 5
        position_secured = fight_state.position_duration >= _secure_threshold
    
    # Detect styles (hoisted above the sub filter so style is available
    # for the grappler-family gate on exotic subs).
    my_style = detect_fighter_style(fighter_attrs)
    opp_style = detect_fighter_style(opponent_attrs)

    # Filter submissions by skill + style. Exotic subs are gated behind
    # grappler-family styles (BJJ/Sambo) OR very-elite submissions skill.
    # Prevents Ground & Pound / Striker fighters from busting out
    # Calf Slicers and Twisters with mid-tier sub stats.
    if submissions:
        exotic_subs = {
            SubmissionType.TWISTER, SubmissionType.GOGOPLATA,
            SubmissionType.HEEL_HOOK, SubmissionType.CALF_SLICER,
            SubmissionType.NECK_CRANK, SubmissionType.DARCE_CHOKE,
            SubmissionType.ANACONDA_CHOKE, SubmissionType.BULLDOG_CHOKE,
            SubmissionType.OMOPLATA,
        }
        intermediate_subs = {
            SubmissionType.ARM_TRIANGLE,
            SubmissionType.KIMURA, SubmissionType.KNEEBAR,
            SubmissionType.ANKLE_LOCK, SubmissionType.TOE_HOLD,
            SubmissionType.NORTH_SOUTH_CHOKE,
        }
        standard_subs = {
            SubmissionType.REAR_NAKED_CHOKE, SubmissionType.ARMBAR,
            SubmissionType.TRIANGLE_CHOKE, SubmissionType.GUILLOTINE,
        }

        _grappler_family = {"bjj", "sambo"}
        _is_grappler = my_style in _grappler_family
        _sub_skill = fighter_attrs.submissions

        filtered_subs = []
        for sub in submissions:
            if sub in exotic_subs:
                # Grappler with decent subs OR elite subs (any style)
                if (_is_grappler and _sub_skill >= 75) or _sub_skill >= 85:
                    filtered_subs.append(sub)
            elif sub in intermediate_subs:
                if _sub_skill >= 55:
                    filtered_subs.append(sub)
            elif sub in standard_subs:
                if _sub_skill >= 60:
                    filtered_subs.append(sub)
            else:
                filtered_subs.append(sub)
        submissions = filtered_subs

    # Base weights - TUNED for realistic action distribution
    # Real MMA: ~70% standing exchanges, ~20% grappling, ~10% ground
    # Subs should be RARE but DANGEROUS - now more accessible
    strike_weight = 120  # High strike bias everywhere
    sub_weight = 0      # START AT ZERO - only add when conditions are right
    grapple_weight = 13  # Reduced from 18 — style weights now bias grapplers further
    
    # Block submissions if position not secured
    if not position_secured:
        sub_weight = 0
        if position not in STANDING_POSITIONS:
            grapple_weight += 15
    
    # =========================================================================
    # STYLE-SPECIFIC STRATEGY ADJUSTMENTS
    # =========================================================================
    
    if position in STANDING_POSITIONS:

        # ── WRESTLER / SAMBO: Clinch first, avoid striking exchanges ──────
        # Real MMA: wrestlers don't just spam shots — they use strikes to set
        # up clinch entries, then get the takedown from body lock or trip.
        if my_style in ("wrestler", "sambo") and opp_style in (
                "striker", "kickboxer", "sprawl_and_brawl", "counter_striker",
                "point_fighter", "pressure_fighter"):
            strike_weight = 55
            grapple_weight = 35
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 15  # Strongly prefer clinch entry vs strikers

        elif my_style in ("wrestler", "sambo"):
            strike_weight -= 5
            grapple_weight += 15
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 8

        # ── MUAY THAI: Seeks clinch vs grapplers, leg kicks vs boxers ─────
        # Real MMA: Thai fighters use leg kicks to set up clinch, punish
        # wrestlers trying to shoot with knees, dominate in close range.
        elif my_style == "muay_thai":
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 22
            strike_weight += 12
            if opp_style in ("striker", "kickboxer", "counter_striker"):
                strike_weight += 12  # Leg kicks work vs pure boxers
            elif opp_style in ("wrestler", "sambo", "ground_and_pound"):
                strike_weight += 18  # Punish takedown attempts with knees
                grapple_weight += 12  # Want clinch to land knees on entry

        # ── GROUND & POUND: Takedown hunting machine ───────────────────────
        # Real MMA: G&P fighters use strikes only to create openings for
        # takedowns. They don't want a boxing match — they want the cage.
        elif my_style == "ground_and_pound":
            strike_weight = 50   # Strike to set up, not to finish standing
            grapple_weight = 50  # Equally happy shooting as striking
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 20  # Clinch → body lock → slam

        # ── SPRAWL & BRAWL: Elite TDD + forward striking pressure ─────────
        # Real MMA: Chuck Liddell didn't just defend takedowns — he punished
        # every shot attempt with an uppercut on the way up. Stays outside,
        # times opponents, explodes on counters.
        elif my_style == "sprawl_and_brawl":
            strike_weight += 30
            grapple_weight -= 20  # Never wants to grapple
            # If opponent tries to grapple, punish harder
            if opp_style in ("wrestler", "sambo", "bjj", "ground_and_pound"):
                strike_weight += 15  # Explosive counter on every shot

        # ── CLINCH FIGHTER: Cage pressure and dirty boxing ────────────────
        # Real MMA: Covington, Dvalishvili — they smother opponents against
        # the cage, drain them with clinch work, win ugly. Not flashy,
        # but suffocating. Mid-range is their kill zone.
        elif my_style == "clinch_fighter":
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 35  # Always seeking clinch
            strike_weight += 5   # Some strikes to close distance

        # ── PRESSURE FIGHTER: Never stops coming forward ──────────────────
        # Real MMA: Gaethje, Holloway — they eat shots to land shots.
        # High output, always forward, cardio is their weapon.
        # Late rounds are where they take over.
        elif my_style == "pressure_fighter":
            strike_weight += 35  # High volume forward pressure
            grapple_weight -= 5  # Occasionally clinch to rest or land body work

        # ── COUNTER STRIKER: Wait, bait, punish ───────────────────────────
        # Real MMA: Machida would circle for 90 seconds then land one clean
        # counter for a KO. Thompson waits on the back foot. Low output,
        # very high accuracy. The engine should reflect the patience.
        elif my_style == "counter_striker":
            strike_weight = 80   # Lower output — selective not spammy
            grapple_weight -= 15 # Stay outside, don't engage

        # ── POINT FIGHTER: Move, score, exit ──────────────────────────────
        # Real MMA: Cruz, early Dillashaw — constant movement, touch-and-go
        # striking, never stays in the pocket. Makes opponents chase.
        elif my_style == "point_fighter":
            strike_weight += 15  # Active but not heavy
            grapple_weight -= 20  # Never wants to grapple

        # ── BJJ: Close distance, pull guard if needed ─────────────────────
        # Real MMA: Maia would shoot a sloppy double leg, get stuffed, end
        # up in a scramble and somehow wind up with a choke. Ryan Hall pulls
        # guard from standing when takedowns fail. They find a way down.
        elif my_style == "bjj":
            if fighter_attrs.takedowns >= 62:
                grapple_weight += 25  # Try takedown first
            else:
                grapple_weight += 18  # Close distance, look for any entry
            # BJJ fighters with low takedowns use guard pull
            if fighter_attrs.takedowns < 60 and GrapplingAction.GUARD_PULL in grappling:
                grapple_weight += 20  # Prefer guard pull over failed shots

        # ── SAMBO (standalone): Clinch trips and throws ───────────────────
        elif my_style == "sambo":
            grapple_weight += 22
            if GrapplingAction.CLINCH_ENTRY in grappling:
                grapple_weight += 12

        # ── PURE STRIKER / KICKBOXER: Keep distance ───────────────────────
        elif my_style in ("striker", "kickboxer"):
            strike_weight += 25
            grapple_weight -= 15

        # ── GENERIC GRAPPLER: Catch-all for high-grapple fighters ─────────
        elif is_grappler(fighter_attrs):
            strike_weight -= 15
            grapple_weight += 25
            if fighter_attrs.takedowns > 68:
                grapple_weight += 10
    
    elif position in CLINCH_POSITIONS:

        # ── MUAY THAI: This is their home ─────────────────────────────────
        # Knees and elbows from clinch are their signature.
        # Nightmare for wrestlers who shoot into a clinch.
        if my_style == "muay_thai":
            strike_weight += 55
            grapple_weight -= 10
            if opp_style in ("wrestler", "sambo", "ground_and_pound"):
                strike_weight += 25  # Punish with knees on entry

        # ── WRESTLER / SAMBO: Takedown from clinch ────────────────────────
        elif my_style in ("wrestler", "sambo"):
            strike_weight = 15   # Some dirty boxing to set up
            grapple_weight = 75  # But mainly want the takedown

        # ── GROUND & POUND: Body lock to slam ─────────────────────────────
        elif my_style == "ground_and_pound":
            strike_weight = 10
            grapple_weight = 85  # All-in on the takedown from here

        # ── CLINCH FIGHTER: This is their kill zone ───────────────────────
        # Dirty boxing, knees, trips — they thrive here.
        # Covington, Dvalishvili grind you against the cage.
        elif my_style == "clinch_fighter":
            strike_weight += 40  # Dirty boxing and elbows
            grapple_weight += 20  # Cage trips and body locks

        # ── SPRAWL & BRAWL: Escape and punish ────────────────────────────
        # Chuck Liddell would break the clinch and counter.
        elif my_style == "sprawl_and_brawl":
            strike_weight += 20   # Short punches while breaking
            grapple_weight += 30  # Get out of here

        # ── PRESSURE FIGHTER: Loves being close ──────────────────────────
        # Body work, short hooks, knees — pressure fighters are comfortable
        # in tight quarters.
        elif my_style == "pressure_fighter":
            strike_weight += 30  # Body work and short hooks
            grapple_weight += 10

        # ── COUNTER STRIKER: Clinch is bad, escape ───────────────────────
        elif my_style == "counter_striker":
            strike_weight += 10
            grapple_weight += 35  # Wants to break out and get back to distance

        # ── POINT FIGHTER: Get out immediately ───────────────────────────
        elif my_style == "point_fighter":
            grapple_weight += 50  # Break clinch, reset to distance

        # ── BJJ: Pull guard from here ─────────────────────────────────────
        elif my_style == "bjj":
            grapple_weight += 40  # Guard pull or takedown
            strike_weight -= 15

        # ── GENERIC GRAPPLER ──────────────────────────────────────────────
        elif is_grappler(fighter_attrs):
            strike_weight -= 10
            grapple_weight += 30

        # ── STRIKER / KICKBOXER: Dirty boxing, look to break ─────────────
        elif my_style in ("striker", "kickboxer"):
            strike_weight += 12
            grapple_weight += 22
            if opp_style in ("wrestler", "sambo", "ground_and_pound"):
                strike_weight += 15  # Short elbows and punches to punish
    
    elif position in DOMINANT_POSITIONS:
        if position_secured:
            # Ground & Pound: GNP all day, subs are an afterthought
            # Real MMA: Khabib rarely hunted subs — he just smothered and hit
            if my_style == "ground_and_pound":
                strike_weight += 80  # Heavy GNP bias
                sub_weight += 10     # Rare sub attempt
            # BJJ / Sambo: Hunt the submission from top
            elif my_style in ("bjj", "sambo"):
                if fighter_attrs.submissions >= 60:
                    sub_weight += 120
                elif fighter_attrs.submissions >= 50:
                    sub_weight += 60
                strike_weight += 20  # Some GNP to open sub attempts
            # Everyone else — tiered by skill
            else:
                if fighter_attrs.submissions >= 85:
                    sub_weight += 100
                elif fighter_attrs.submissions >= 75:
                    sub_weight += 50
                elif fighter_attrs.submissions >= 60:
                    sub_weight += 20
                strike_weight += 50  # GNP default
        else:
            strike_weight += 50  # GNP while working to secure position
        grapple_weight += 10   # Position advancement always available
    
    elif position in INFERIOR_POSITIONS:
        grapple_weight += 45  # Escape is priority
        if position_secured:
            # BJJ fighters are dangerous from bottom — guard recovery
            if my_style in ("bjj", "sambo"):
                if fighter_attrs.submissions >= 55:
                    sub_weight += 100  # Dangerous from bad spots
                elif fighter_attrs.submissions >= 45:
                    sub_weight += 50
            else:
                if fighter_attrs.submissions >= 85:
                    sub_weight += 70
                elif fighter_attrs.submissions >= 75:
                    sub_weight += 35
                elif fighter_attrs.submissions >= 60:
                    sub_weight += 15
    
    elif position in LEG_ENTANGLEMENT_POSITIONS:
        if position_secured:
            # Sambo gets a strong leg lock bonus — this is their scramble game
            # Real MMA: Khabib, Makhachev, Chimaev love leg entanglements
            if my_style == "sambo":
                if fighter_attrs.submissions >= 55:
                    sub_weight += 200
                elif fighter_attrs.submissions >= 45:
                    sub_weight += 120
            elif my_style == "bjj":
                if fighter_attrs.submissions >= 60:
                    sub_weight += 180
                elif fighter_attrs.submissions >= 50:
                    sub_weight += 100
            else:
                if fighter_attrs.submissions >= 85:
                    sub_weight += 120
                elif fighter_attrs.submissions >= 75:
                    sub_weight += 70
                elif fighter_attrs.submissions >= 60:
                    sub_weight += 35
        grapple_weight += 20
        strike_weight = 0
    
    elif position in GUARD_POSITIONS:
        if is_top:
            strike_weight += 45   # GNP from top guard
            grapple_weight += 20  # Guard passing
        else:
            # Bottom guard — BJJ's domain
            grapple_weight += 20  # Sweeps and transitions
            if position_secured:
                if my_style in ("bjj", "sambo"):
                    # Dangerous from guard bottom even at lower skill
                    if fighter_attrs.submissions >= 55:
                        sub_weight += 200
                    elif fighter_attrs.submissions >= 45:
                        sub_weight += 120
                    elif fighter_attrs.submissions >= 35:
                        sub_weight += 60
                else:
                    if fighter_attrs.submissions >= 85:
                        sub_weight += 140
                    elif fighter_attrs.submissions >= 75:
                        sub_weight += 70
                    elif fighter_attrs.submissions >= 60:
                        sub_weight += 30
    
    # Fight state adjustments - removed desperate sub boost

    # Top control bonus — wrestlers with elite control
    # can threaten submissions even without elite sub skill.
    # This represents grinding pressure, not technique.
    if (position_secured
            and getattr(fighter_attrs, 'top_control', 0) >= 72
            and getattr(fighter_attrs, 'submissions', 0) >= 52):
        _tc_bonus = int(
            (getattr(fighter_attrs, 'top_control', 0) - 63)
            * 1.0)
        sub_weight += _tc_bonus

    # ── Guard threat from bottom ──────────────────────
    # BJJ specialists are dangerous from their back.
    # High guard stat + GUARD position = active sub threat.
    # Represents triangle/armbar hunting from bottom.
    if (position in GUARD_POSITIONS
            and not is_top
            and getattr(fighter_attrs, 'guard', 0) >= 70
            and getattr(fighter_attrs, 'submissions', 0) >= 65):
        _guard_sub_bonus = int(
            (getattr(fighter_attrs, 'guard', 0) - 60) * 0.9
            + (getattr(fighter_attrs, 'submissions', 0) - 60)
            * 0.5)
        sub_weight += _guard_sub_bonus

    if fighter_state.momentum > 70:
        strike_weight += 10

    # ── Style action bias ────────────────────────────────
    # Multiply base weights by fighter style preferences.
    # Grapplers get more submission/grapple; strikers more striking.
    # Inlined here to avoid circular import from fight_integration.
    _STYLE_WEIGHTS = {
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
    _style_key = ""
    _fs = getattr(fighter_attrs, 'fighting_style', None)
    if _fs is not None:
        _style_key = getattr(_fs, 'name', '') or str(_fs)
    # Normalize ampersands + whitespace so raw strings like
    # "Ground & Pound" match dict keys like "GROUND_AND_POUND".
    _style_key = (_style_key.upper()
                  .replace(' & ', ' AND ')
                  .replace('&', 'AND')
                  .strip())
    # Alias map — covers both enum-NAME format and raw strings
    # from world_gen / template system. Falls through to
    # whitespace→underscore for direct dict hits.
    _STYLE_ALIASES = {
        'SAMBO': 'SAMBO',
        'JUDO': 'JUDO',
        'KARATE': 'KARATE',
        'ORTHODOX_BOXER': 'ORTHODOX_BOXER',
        'ORTHODOX BOXER': 'ORTHODOX_BOXER',
        'BJJ': 'BJJ_SPECIALIST',
        'BJJ SPECIALIST': 'BJJ_SPECIALIST',
        'GROUND AND POUND': 'GROUND_AND_POUND',
        'SPRAWL AND BRAWL': 'SPRAWL_AND_BRAWL',
        'CLINCH FIGHTER': 'CLINCH_FIGHTER',
        'COUNTER STRIKER': 'COUNTER_STRIKER',
        'PRESSURE FIGHTER': 'PRESSURE_FIGHTER',
        'POINT FIGHTER': 'POINT_FIGHTER',
        'MUAY THAI': 'MUAY_THAI',
    }
    _style_key = _STYLE_ALIASES.get(
        _style_key, _style_key.replace(' ', '_'))
    _sw = _STYLE_WEIGHTS.get(_style_key,
        {"strike":1.0,"grapple":1.0,"submission":1.0})
    strike_weight = int(strike_weight * _sw["strike"])
    grapple_weight = int(grapple_weight * _sw["grapple"])
    sub_weight = int(sub_weight * _sw["submission"])

    # ── GAMEPLAN-DIAL-AGGR1 · AGGRESSION dial ─────────────
    # Aggression multiplies AFTER _STYLE_WEIGHTS so it composes with
    # style, not overrides it (memo §3): a wrestler on AGGRESSIVE
    # stays majority-grapple, just more forward. Only strike output
    # is affected (grapple/sub weights untouched — grapple vs strike
    # bias is RANGE dial's territory, SHIP3). Delta is IQ-gated via
    # dial_execution(). `gameplan=None` (SHIP1 callers / live bridge
    # today) skips this block and is byte-identical to SHIP1.
    # Neutral Gameplan(aggression=0) engages the block but the
    # multiplier evaluates to 1.0 → also identical.
    #
    # Asymmetric per memo §3 table: forward +15% strike weight,
    # patient −10% (patient is a smaller step so it stays viable
    # for defensive strikers).
    if gameplan is not None:
        _agg = int(getattr(gameplan, 'aggression', 0) or 0)
        # Forward tilts strike_weight up +8%; patient tilts it down
        # −5% (asymmetric: patient is the smaller step so defensive
        # gameplans stay legitimate). IQ-gated via dial_execution().
        # Bounds tuned so a wrestler on AGGRESSIVE stays majority-
        # grapple — the dial biases within the style envelope, doesn't
        # override it. Larger bumps were tested and destabilized
        # (over-committed strikers get grappled — see the tuning arc
        # in gameplan_design1.md §3).
        if _agg > 0:
            _exec = dial_execution(fighter_attrs, fighter_state)
            strike_weight = int(strike_weight * (1.0 + 0.08 * _exec))
        elif _agg < 0:
            _exec = dial_execution(fighter_attrs, fighter_state)
            strike_weight = int(strike_weight * (1.0 - 0.05 * _exec))

        # ── GAMEPLAN-DIAL-RANGE-CORE1 · RANGE dial (§1a + §1f) ─
        # Sign convention: range_bias = +1 grapple-seek, -1 keep-
        # standing, 0 neutral. Multipliers per gameplan_range_
        # design1.md §1a and diag §1a: grapple_weight ×1.20 / ×0.85,
        # sub_weight ×1.10 / ×0.80. Both IQ-gated on the delta from
        # 1.0 (same primitive AGGRESSION uses). strike_weight is
        # untouched here — AGGRESSION owns it; no overlap risk. §1f
        # sprawl reflex fires only on keep-standing in STANDING when
        # opponent has a takedown threat and I'm not already S&B
        # (S&B block at :1521-1526 already runs — double-fire guard).
        # Composition audit: diag §2 confirms clean — no shared
        # mutable state with AGGRESSION, no weight-variable overlap.
        _rng = int(getattr(gameplan, 'range_bias', 0) or 0)
        if _rng > 0:
            _exec_r = dial_execution(fighter_attrs, fighter_state)
            grapple_weight = int(grapple_weight * (1.0 + 0.20 * _exec_r))
            sub_weight     = int(sub_weight     * (1.0 + 0.10 * _exec_r))
        elif _rng < 0:
            _exec_r = dial_execution(fighter_attrs, fighter_state)
            grapple_weight = int(grapple_weight * (1.0 - 0.15 * _exec_r))
            sub_weight     = int(sub_weight     * (1.0 - 0.20 * _exec_r))
            # §1f sprawl reflex — commit to striking-first posture
            # when a real TD threat is across the cage. Not IQ-gated
            # (pre-fight posture, per design §4a). Excludes S&B
            # (already gets +30/-20 at :1521-1526) so no double-fire.
            if (position in STANDING_POSITIONS
                    and my_style != "sprawl_and_brawl"
                    and getattr(opponent_attrs, 'takedowns', 0) >= 70):
                strike_weight += 8

    # ── Late-round cardio advantage ──────────────────────
    # Cardio gap widens the longer the fight goes.
    # A fighter with much better cardio dominates round 3.
    _round = getattr(fight_state, 'current_round', 1) or 1
    if _round >= 2:
        _opp_cardio = getattr(opponent_attrs, 'cardio', 70)
        _my_cardio = getattr(fighter_attrs, 'cardio', 70)
        _cardio_gap = _my_cardio - _opp_cardio
        if _cardio_gap >= 12:
            _cardio_mult = 1.0 + (
                (_cardio_gap - 10) * 0.015 * _round)
            _cardio_mult = min(_cardio_mult, 1.35)
            strike_weight = int(strike_weight * _cardio_mult)
            grapple_weight = int(grapple_weight * _cardio_mult)
            sub_weight = int(sub_weight * _cardio_mult)

    # ── Clinch/pressure style advantage ──────────────
    # Pressure / clinch fighters thrive in close quarters.
    if _style_key in (
            'PRESSURE_FIGHTER', 'CLINCH_FIGHTER', 'BRAWLER'):
        if position in CLINCH_POSITIONS:
            strike_weight = int(strike_weight * 1.25)
            grapple_weight = int(grapple_weight * 1.15)

    # ── Point Fighter first-exchange jab ──────────────
    # Fastest to establish range at round start.
    if (_style_key == 'POINT_FIGHTER'
            and getattr(fight_state,
                'exchanges_this_round', 1) <= 1):
        strike_weight = int(strike_weight * 1.20)

    # ── Karate patience — wait and punish ─────────────
    # If Karate fighter hasn't landed yet this round,
    # flag for a power bonus on next head strike.
    # Lyoto Machida / Wonderboy effect.
    if _style_key == 'KARATE':
        _strikes_landed = getattr(
            fighter_state, 'strikes_landed', 0)
        if _strikes_landed == 0:
            fighter_state._karate_patience = True

    # Stamina factor
    stamina_factor = fighter_state.stamina / 100
    strike_weight = int(strike_weight * stamina_factor)
    sub_weight = int(sub_weight * stamina_factor)
    grapple_weight = int(grapple_weight * stamina_factor)
    
    # Ensure minimum weights
    strike_weight = max(5, strike_weight) if strikes else 0
    # Sub gate: BJJ/Sambo can attempt subs at 45+, everyone else at 60+
    _sub_threshold = 45 if my_style in ("bjj", "sambo") else 60
    if submissions and fighter_attrs.submissions >= _sub_threshold:
        sub_weight = max(1, sub_weight)
    else:
        sub_weight = 0
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
        action = select_grappling_action(
            grappling, fighter_attrs, position, is_top,
            gameplan=gameplan, fighter_state=fighter_state)
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
    is_top: bool,
    gameplan: Optional['Gameplan'] = None,
    fighter_state: Optional[FighterState] = None,
) -> GrapplingAction:
    """Select grappling action based on attributes and situation.

    GAMEPLAN-DIAL-RANGE-CORE1 (§1b, §1c): optional `gameplan` +
    `fighter_state` power the RANGE-dial per-action bias. Both
    default to None → byte-identical to pre-RANGE behavior (SHIP1
    additive contract). §1b biases CLINCH_BREAK vs. TDs in CLINCH.
    §1c biases STAND_UP + guard-work sweeps in INFERIOR_POSITIONS.
    """
    # Range-dial IQ gate — computed once if the dial is engaged and
    # fighter_state is available. dial_execution needs both; when
    # fighter_state is None (older callers), gate defaults to 1.0.
    _rng = 0
    if gameplan is not None:
        _rng = int(getattr(gameplan, 'range_bias', 0) or 0)
    _rng_iq = 1.0
    if _rng != 0 and fighter_state is not None:
        _rng_iq = dial_execution(fighter, fighter_state)

    weights = {}

    for action in available:
        weight = 10

        # Takedown-based actions (use takedowns attribute)
        if action in {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG,
                     GrapplingAction.BODY_LOCK_TAKEDOWN, GrapplingAction.SUPLEX,
                     GrapplingAction.HIP_TOSS, GrapplingAction.TRIP}:
            weight += fighter.takedowns // 4
            # §1b clinch tendency — from CLINCH, grapple-seek wants
            # the takedown out; keep-standing wants to break instead.
            if _rng != 0 and position in CLINCH_POSITIONS:
                if _rng > 0:
                    weight += int(20 * _rng_iq)
                else:
                    weight -= int(20 * _rng_iq)

        # Guard/sweep actions (use guard attribute)
        elif action in {GrapplingAction.SCISSOR_SWEEP, GrapplingAction.FLOWER_SWEEP,
                       GrapplingAction.BUTTERFLY_SWEEP, GrapplingAction.SHRIMP_ESCAPE}:
            weight += fighter.guard // 4
            # §1c work guard — grapple-seek accepts bottom, hunts
            # sweeps rather than escape. Only fires from bottom
            # positions where sweeps make sense.
            if (_rng > 0
                    and position in (INFERIOR_POSITIONS | GUARD_POSITIONS)
                    and not is_top):
                weight += int(15 * _rng_iq)

        # Top control actions (use top_control attribute)
        elif action in {GrapplingAction.PASS_TO_SIDE, GrapplingAction.TAKE_BACK,
                       GrapplingAction.PASS_TO_MOUNT, GrapplingAction.KNEE_SLICE}:
            weight += fighter.top_control // 4

        # Clinch entry - wrestlers and Muay Thai fighters
        # Uses clinch_control (positional grappling), not clinch_striking
        # (damage). Entering the clinch is a control action.
        elif action == GrapplingAction.CLINCH_ENTRY:
            weight += (fighter.takedowns + fighter.clinch_control) // 6
            if fighter.clinch_control >= 70:
                weight += 15  # Clinch specialist bonus

        # Stand up attempts (guard + explosiveness)
        elif action == GrapplingAction.STAND_UP:
            if fighter.guard > 60 or fighter.strength > 60:
                weight += 15
            # §1c stand-up preference — keep-standing pushes STAND_UP
            # +25, grapple-seek pulls it −15. IQ-gated. Diag §1a
            # anchor correction: this is the real STAND_UP selection
            # site (design memo :2613 pointed at the position-change
            # writer, not the selector).
            if _rng > 0:
                weight -= int(15 * _rng_iq)
            elif _rng < 0:
                weight += int(25 * _rng_iq)

        # Clinch break - strikers want this
        elif action == GrapplingAction.CLINCH_BREAK:
            if fighter.boxing > fighter.takedowns:
                weight += 20  # Strikers really want to break clinch
            # §1b clinch tendency — keep-standing wants out of clinch,
            # grapple-seek stays committed. IQ-gated.
            if _rng < 0:
                weight += int(30 * _rng_iq)
            elif _rng > 0:
                weight -= int(20 * _rng_iq)

        # Guard pull - BJJ fighters with low takedowns
        elif action == GrapplingAction.GUARD_PULL:
            weight += fighter.guard // 4  # Better guard = more confident pulling

        weights[action] = max(1, int(weight))

    actions_list = list(weights.keys())
    probs = list(weights.values())
    return random.choices(actions_list, weights=probs, k=1)[0]
# ============================================================================
# ACTION RESOLUTION
# ============================================================================

# ============================================================================
# P3-3 CONTEST FUNCTION (D13 ratified 2026-09-04; scope
# claude/fight_model_p3_scope_v0_1.md; composites
# claude/fight_model_composites_v1.md; contract fight_model_v1_0.md §4).
#
#   P_c = clamp(P_MIN, P_MAX, P_EVEN + S × (A_eff/(A_eff+D_eff) − ½))
#
# CONTEST_RECIPES = per event class {attack: {attr: weight}, defense: same}
# CONTEST_TARGETS = per event class (P_EVEN, EDGE20_TARGET) from D10
# S values DERIVED analytically at import time from (P_EVEN,
# EDGE20_TARGET, recipe) — printed at first import for provenance.
# P_MIN = 0.4 × P_EVEN. P_MAX = min(0.90, P_EVEN + 1.5 × edge_gain).
#
# Situational scalars (stamina, rocked, grappler-pressure) multiply
# composites BEFORE the P_c form — never scale the result. Result-level
# upset branches from the pre-D13 CSS/CGS retire here (D4 vindicated
# by F9 measurement; upset was paying fighters to be worse).
# ============================================================================

# D13 recipes (canonical: fight_model_composites_v1.md)
CONTEST_RECIPES = {
    "punch":          {"a": {"boxing": 0.7, "speed": 0.3},          "d": {"striking_defense": 0.65, "speed": 0.35}},
    "kick":           {"a": {"kicks": 0.7, "speed": 0.3},           "d": {"striking_defense": 0.65, "speed": 0.35}},
    "clinch_strike":  {"a": {"clinch_striking": 0.75, "speed": 0.25}, "d": {"striking_defense": 0.6, "clinch_control": 0.4}},
    "td_distance":    {"a": {"takedowns": 1.0},                     "d": {"takedown_defense": 0.7, "speed": 0.3}},
    "td_clinch":      {"a": {"takedowns": 0.6, "clinch_control": 0.4}, "d": {"takedown_defense": 0.6, "strength": 0.4}},
    "throw":          {"a": {"strength": 0.5, "takedowns": 0.5},    "d": {"takedown_defense": 0.6, "strength": 0.4}},
    "pass":           {"a": {"top_control": 1.0},                   "d": {"guard": 1.0}},
    "sweep":          {"a": {"guard": 0.8, "strength": 0.2},        "d": {"top_control": 1.0}},
    "standup":        {"a": {"guard": 0.7, "strength": 0.3},        "d": {"top_control": 1.0}},
    "clinch_entry":   {"a": {"clinch_control": 0.6, "takedowns": 0.4}, "d": {"clinch_control": 0.6, "striking_defense": 0.4}},
    "clinch_break":   {"a": {"strength": 1.0},                      "d": {"clinch_control": 0.7, "strength": 0.3}},
    "sub_lockin":     {"a": {"submissions": 1.0},                   "d": {"guard": 0.5, "submissions": 0.5}},
    # P3-4c §5a — technical-escape per-tick contest. "Attacker" side of the
    # contest is the DEFENDER-of-sub trying to escape (guard 0.5 + subs 0.5);
    # "defender" side is the ATTACKER-of-sub trying to hold (submissions 1.0).
    "sub_escape":     {"a": {"guard": 0.5, "submissions": 0.5},     "d": {"submissions": 1.0}},
}

# D10 P_EVEN targets + EDGE20 targets (per D10 tier tables; strikes +15pp,
# takedowns +22pp, throws +17pp, sub lockin preserves F8 slope +14pp)
CONTEST_TARGETS = {
    "punch":         {"P_EVEN": 0.45, "EDGE20_TARGET": 0.60},
    "kick":          {"P_EVEN": 0.42, "EDGE20_TARGET": 0.57},
    "clinch_strike": {"P_EVEN": 0.48, "EDGE20_TARGET": 0.63},
    "td_distance":   {"P_EVEN": 0.30, "EDGE20_TARGET": 0.52},
    "td_clinch":     {"P_EVEN": 0.45, "EDGE20_TARGET": 0.67},
    "throw":         {"P_EVEN": 0.38, "EDGE20_TARGET": 0.55},
    "pass":          {"P_EVEN": 0.45, "EDGE20_TARGET": 0.60},
    "sweep":         {"P_EVEN": 0.35, "EDGE20_TARGET": 0.50},
    "standup":       {"P_EVEN": 0.50, "EDGE20_TARGET": 0.60},
    "clinch_entry":  {"P_EVEN": 0.40, "EDGE20_TARGET": 0.55},
    "clinch_break":  {"P_EVEN": 0.45, "EDGE20_TARGET": 0.60},
    "sub_lockin":    {"P_EVEN": 0.35, "EDGE20_TARGET": 0.49},  # F8 preserve
    # P3-4c §5a — per-tick technical-escape chance. Provisional; P3-5 calibrates.
    # P_EVEN=0.10 → parity: 10% escape per tick. Steep S so guard/subs advantage
    # bites. EDGE20=0.28 at +20pt escaper composite edge (derived S ≈ 2.88).
    "sub_escape":    {"P_EVEN": 0.10, "EDGE20_TARGET": 0.28},
}


def _composite_eff(stat_dict, weights):
    """Weighted-average composite: A_eff = Σ weight_i × attr_i."""
    return sum(weights[k] * stat_dict[k] for k in weights)


def _derive_S(cls_key):
    """Analytically derive S for a class from its recipe + (P_EVEN, EDGE20_TARGET).
    Convention: 20-pt edge is on the attacker's PRIMARY (highest-weighted)
    attribute; defender + assist attrs held at baseline 50."""
    tgt = CONTEST_TARGETS[cls_key]
    rec = CONTEST_RECIPES[cls_key]
    p_even = tgt["P_EVEN"]
    edge_target = tgt["EDGE20_TARGET"]
    a_wts, d_wts = rec["a"], rec["d"]
    primary = max(a_wts.items(), key=lambda kv: kv[1])[0]
    base = 50.0
    a_stats_even = {k: base for k in a_wts}
    d_stats_even = {k: base for k in d_wts}
    a_eff_even = _composite_eff(a_stats_even, a_wts)
    d_eff_even = _composite_eff(d_stats_even, d_wts)
    # At even, ratio = 0.5 - 0.5 = 0, P_c = P_EVEN ✓
    a_stats_edge = {k: (base + 20 if k == primary else base) for k in a_wts}
    a_eff_edge = _composite_eff(a_stats_edge, a_wts)
    d_eff_edge = d_eff_even  # defender unchanged
    ratio = a_eff_edge / (a_eff_edge + d_eff_edge) - 0.5
    if ratio <= 0:
        return 0.0
    return (edge_target - p_even) / ratio


# Derive S per class at module import; print for provenance
CONTEST_S = {k: round(_derive_S(k), 4) for k in CONTEST_TARGETS}
CONTEST_P_MIN = {k: round(0.4 * CONTEST_TARGETS[k]["P_EVEN"], 4)
                  for k in CONTEST_TARGETS}
CONTEST_P_MAX = {k: round(min(0.90, CONTEST_TARGETS[k]["P_EVEN"]
                                + 1.5 * (CONTEST_TARGETS[k]["EDGE20_TARGET"]
                                          - CONTEST_TARGETS[k]["P_EVEN"])), 4)
                  for k in CONTEST_TARGETS}


def _get_attr_dict(fighter, wts):
    """Materialize the attribute values for the recipe weights."""
    return {k: float(getattr(fighter, k)) for k in wts}


def _assemble_composite(cls_key, attacker, defender):
    """Return (A_eff, D_eff) for the attacker vs defender on class cls_key.
    Composite-only; NO situational factors. Caller applies stamina, rocked,
    pressure, etc. as multiplicative composite scalers per D13."""
    rec = CONTEST_RECIPES[cls_key]
    a_stats = _get_attr_dict(attacker, rec["a"])
    d_stats = _get_attr_dict(defender, rec["d"])
    return (_composite_eff(a_stats, rec["a"]),
            _composite_eff(d_stats, rec["d"]))


def _p_c(cls_key, a_eff, d_eff):
    """Contest form: P_c = clamp(P_MIN, P_MAX, P_EVEN + S × (A/(A+D) − ½))."""
    tgt = CONTEST_TARGETS[cls_key]
    p_even = tgt["P_EVEN"]
    s = CONTEST_S[cls_key]
    p_min = CONTEST_P_MIN[cls_key]
    p_max = CONTEST_P_MAX[cls_key]
    if a_eff + d_eff <= 0:
        return p_even
    ratio = a_eff / (a_eff + d_eff) - 0.5
    return max(p_min, min(p_max, p_even + s * ratio))


# Provenance print (fires once at import). Format matches STAMINA-DRAIN1's
# ship line so the arc's diagnostic tools recognize P3-3 activation.
import sys as _p33_sys
_p33_sys.stderr.write(
    "✅ [P3-3 CONTEST] loaded; per-class S derived from (P_EVEN, EDGE20_TARGET):\n")
for _k in CONTEST_TARGETS:
    _t = CONTEST_TARGETS[_k]
    _p33_sys.stderr.write(
        f"    {_k:<14s}  P_EVEN={_t['P_EVEN']:.2f}  EDGE20={_t['EDGE20_TARGET']:.2f}  "
        f"S={CONTEST_S[_k]:.4f}  P_MIN={CONTEST_P_MIN[_k]:.4f}  P_MAX={CONTEST_P_MAX[_k]:.4f}\n")


# Strike-family classifier (used by CSS)
def _strike_class(strike):
    if strike in {StrikeType.JAB, StrikeType.CROSS, StrikeType.HOOK,
                  StrikeType.UPPERCUT, StrikeType.OVERHAND}:
        return "punch"
    if "kick" in strike.value.lower():
        return "kick"
    if strike in {StrikeType.CLINCH_KNEE, StrikeType.CLINCH_ELBOW,
                  StrikeType.DIRTY_BOXING}:
        return "clinch_strike"
    return "clinch_strike"  # else fallthrough (knees, elbows, GnP)


# Grappling classifier (used by CGS)
def _grapple_class(action):
    if action in {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG}:
        return "td_distance"
    if action == GrapplingAction.BODY_LOCK_TAKEDOWN:
        return "td_clinch"
    if action in {GrapplingAction.TRIP, GrapplingAction.HIP_TOSS,
                  GrapplingAction.SUPLEX}:
        return "throw"
    if action in {GrapplingAction.PASS_TO_SIDE, GrapplingAction.PASS_TO_MOUNT,
                  GrapplingAction.KNEE_SLICE}:
        return "pass"
    if action in {GrapplingAction.SCISSOR_SWEEP, GrapplingAction.BUTTERFLY_SWEEP,
                  GrapplingAction.FLOWER_SWEEP}:
        return "sweep"
    if action in {GrapplingAction.SHRIMP_ESCAPE, GrapplingAction.BRIDGE_ESCAPE}:
        return "standup"  # bottom-to-neutral, same recipe as STAND_UP
    if action == GrapplingAction.STAND_UP:
        return "standup"
    if action == GrapplingAction.CLINCH_ENTRY:
        return "clinch_entry"
    if action == GrapplingAction.CLINCH_BREAK:
        return "clinch_break"
    return "td_distance"  # default: mirrors old default's takedowns-primary shape


def calculate_strike_success(
    attacker: FighterAttributes,
    defender: FighterAttributes,
    strike: StrikeType,
    attacker_state: FighterState,
    defender_state: FighterState,
    fight_state: FightState
) -> Tuple[bool, bool]:
    """P3-3: Contest function rebuild (D13). Returns (landed, was_counter).

    Composites per fight_model_composites_v1.md; P_c form per §4 of the
    contract. Situational scalars (stamina, rocked, grappler-pressure,
    sub-threat) multiply composites — never scale the result. Result-level
    upset branches from the pre-D13 CSS are RETIRED-NOT-DELETED (see
    _legacy_calculate_strike_success below).
    """
    cls = _strike_class(strike)
    a_eff, d_eff = _assemble_composite(cls, attacker, defender)

    # Situational scalars (composite-space per D13). Only the pressure /
    # threat modifiers survive from the pre-D13 CSS — additive defensive
    # bonuses (elite wrestler defends strikes +15) are RETIRED under the
    # scopes contract: strike-defense recipe is SD + speed/CC, not TD.
    if fight_state.position in STANDING_POSITIONS:
        takedown_threat = defender.takedowns - attacker.takedowns
        if takedown_threat >= 30:
            a_eff *= 0.75
        elif takedown_threat >= 20:
            a_eff *= 0.82
        elif takedown_threat >= 10:
            a_eff *= 0.90
        sub_threat = defender.submissions - attacker.submissions
        if sub_threat >= 30:
            a_eff *= 0.88
        elif sub_threat >= 20:
            a_eff *= 0.94

    # Stamina (composite scalar)
    a_eff *= (attacker_state.stamina / 100)
    d_eff *= (defender_state.stamina / 100)

    # Rocked opponent easier to hit (composite scalar on defender).
    # P3-4c — COMPOSURE modulation. Behind flag; OFF → exploit
    # stays at 0.5 (byte-identical). ON → composure=100 fighter
    # gets 0.65 (less exploitable), composure=20 fighter gets 0.35
    # (more exploitable). Clamped [FLOOR, CAP].
    if defender_state.is_rocked:
        _rocked_mult = 0.5
        try:
            import window_registry as _wreg_exp
            if _wreg_exp.FI_COMPOSURE_WIRING_ENABLED:
                _comp_stat = getattr(defender_state, 'composure_rating', 60)
                _rocked_mult = 0.5 + COMPOSURE_ROCK_EXPLOIT_SPREAD * (
                    (_comp_stat - 60) / 40.0)
                _rocked_mult = max(COMPOSURE_ROCK_EXPLOIT_FLOOR,
                                   min(COMPOSURE_ROCK_EXPLOIT_CAP, _rocked_mult))
        except ImportError:
            pass
        d_eff *= _rocked_mult

    # Symmetric two-sided variance per D13 (both sides get their own draw).
    # The pre-D13 form had offense-only ±25% — F3/F6 traced part of the
    # dead defense layer to that asymmetry.
    a_eff *= random.uniform(0.85, 1.15)
    d_eff *= random.uniform(0.85, 1.15)

    # Contest form
    p_c = _p_c(cls, a_eff, d_eff)
    landed = random.random() < p_c

    # Counter check (unchanged from pre-D13 — separate mechanism)
    was_counter = False
    if landed and defender.fight_iq > 60 and random.random() < 0.15:
        was_counter = True

    return landed, was_counter


def _legacy_calculate_strike_success(
    attacker: FighterAttributes,
    defender: FighterAttributes,
    strike: StrikeType,
    attacker_state: FighterState,
    defender_state: FighterState,
    fight_state: FightState
) -> Tuple[bool, bool]:
    """RETIRED-NOT-DELETED (P3-3, C19 pending). Pre-D13 CSS.

    Verbatim pre-D13 code preserved as-is for provenance. Any code
    calling this by name is out of the P3-3 contest form and will
    reintroduce F4/F6/F9 signatures (boxing inversion, dead landing
    dial, upset-branch inversion). Do not resurrect without a filing.
    """
    # Determine relevant skills
    if strike in {StrikeType.JAB, StrikeType.CROSS, StrikeType.HOOK,
                 StrikeType.UPPERCUT, StrikeType.OVERHAND}:
        offense = attacker.boxing
        defense = defender.striking_defense
    elif "kick" in strike.value.lower():
        offense = attacker.kicks
        defense = defender.striking_defense
        if attacker.kicks >= 80 and defender.kicks < 60:
            offense += 10
    elif strike in {StrikeType.CLINCH_KNEE, StrikeType.CLINCH_ELBOW, StrikeType.DIRTY_BOXING}:
        offense = attacker.clinch_striking
        defense = (defender.striking_defense + defender.takedowns) // 2
    else:
        offense = attacker.clinch_striking
        defense = defender.striking_defense
    offense += attacker.speed // 10
    defense += defender.speed // 10
    if fight_state.position in STANDING_POSITIONS:
        if defender.takedowns >= 85: defense += 15
        elif defender.takedowns >= 75: defense += 10
        elif defender.takedowns >= 60: defense += 5
        if defender.guard >= 85: defense += 10
        elif defender.guard >= 75: defense += 5
        takedown_threat = defender.takedowns - attacker.takedowns
        if takedown_threat >= 30: offense *= 0.75
        elif takedown_threat >= 20: offense *= 0.82
        elif takedown_threat >= 10: offense *= 0.90
        sub_threat = defender.submissions - attacker.submissions
        if sub_threat >= 30: offense *= 0.88
        elif sub_threat >= 20: offense *= 0.94
    offense *= (attacker_state.stamina / 100)
    defense *= (defender_state.stamina / 100)
    if defender_state.is_rocked:
        defense *= 0.5
    variance = random.uniform(0.75, 1.25)
    offense *= variance
    success_chance = 0.20 + (offense / (offense + defense + 1)) * 0.5
    success_chance = max(0.15, min(0.85, success_chance))
    if offense < defense * 0.85:
        upset_roll = random.random()
        if upset_roll < 0.18:
            success_chance = max(success_chance, 0.70)
        elif upset_roll < 0.35:
            success_chance = min(success_chance + 0.22, 0.70)
    landed = random.random() < success_chance
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
    was_counter: bool = False,
    is_dominant_position: bool = False,
) -> Tuple[float, str]:
    """Calculate damage from a strike. Returns (damage, target_area).

    GNP-DAMAGE-BUFF1: `is_dominant_position` is True when the attacker
    is the top fighter in a DOMINANT position (MOUNT / SIDE_CONTROL_TOP
    / BACK_MOUNT / etc.). Real-MMA reference: mount strikes are 2-3×
    standing damage. Applied BEFORE the caller's FI_DAMAGE_MULTIPLIER so
    composition stays clean. Default False preserves byte-identical
    behavior for callers that don't opt in (e.g., the dead
    fight_engine.simulate_exchange path).
    """
    base_damage, ko_power, stamina_cost, target = STRIKE_PROPERTIES[strike]

    # P3-4d: POWER lane (default OFF → reads strength, byte-identical to
    # pre-C23). Flag flip re-routes striking damage to POWER; strength
    # keeps grappling-physicality lanes untouched. Read via module attr
    # so runtime flips propagate (same pattern as CHIN/COMPOSURE at
    # fe:737-747).
    _power_or_strength = attacker.strength
    try:
        import window_registry as _wreg_pw
        if _wreg_pw.FI_POWER_WIRING_ENABLED:
            _power_or_strength = getattr(
                attacker, 'power', attacker.strength)
    except ImportError:
        pass

    # Strike-family base damage bonus — reads POWER (or STRENGTH when
    # flag OFF; identical arithmetic in OFF mode).
    damage = base_damage + (_power_or_strength - 50) / 10

    # Power punchers bonus — same POWER/STRENGTH gate.
    if strike in {StrikeType.CROSS, StrikeType.HOOK, StrikeType.OVERHAND}:
        damage *= 1 + (_power_or_strength / 200)

    # STRIKE-SKILL-DMG1 phase 1a — skill-into-damage dial.
    # Attacker-side only. Deterministic (no random). Family mapping
    # mirrors calculate_strike_success (:2269-2288):
    #   boxing family                          → attacker.boxing
    #   kick strikes                           → attacker.kicks
    #   clinch family + fallback (incl. GnP)   → attacker.clinch_striking
    # K read by plain global name at call time so the sweep harness
    # can vary it by module attribute rebind. At K=0 the factor is
    # 1.0 exactly and this line is byte-identical to no-op.
    if strike in {StrikeType.JAB, StrikeType.CROSS, StrikeType.HOOK,
                  StrikeType.UPPERCUT, StrikeType.OVERHAND}:
        _skill = attacker.boxing
    elif "kick" in strike.value.lower():
        _skill = attacker.kicks
    elif strike in {StrikeType.CLINCH_KNEE, StrikeType.CLINCH_ELBOW,
                    StrikeType.DIRTY_BOXING}:
        _skill = attacker.clinch_striking
    else:
        _skill = attacker.clinch_striking
    damage *= max(STRIKE_SKILL_DAMAGE_FLOOR,
                  1 + (STRIKE_SKILL_DAMAGE_K * (_skill - 75) / 100))

    # STRIKE-SKILL-DMG1 phase 1b — kick-family gap-into-damage
    # gradient. Two-sided: factor scales per-exchange kick gap,
    # clamped to [KICK_GAP_DAMAGE_FLOOR, KICK_GAP_DAMAGE_CEIL].
    # Replaces the historical MUAY-THAI-VS-BOXER cliffs (deleted
    # this commit) with a level-independent gap-driven multiplier.
    # Attacker- and defender-side read; defender-side stays within
    # the replaced cliffs' existing precedent. Plain-global reads
    # at call time; sweepable by module attribute rebind.
    if "kick" in strike.value.lower():
        _kick_gap = attacker.kicks - defender.kicks
        damage *= max(KICK_GAP_DAMAGE_FLOOR,
                      min(KICK_GAP_DAMAGE_CEIL,
                          1 + (KICK_GAP_DAMAGE_K * _kick_gap / 100)))

    # Counter bonus
    if was_counter:
        damage *= 1.3

    # Stamina affects power
    damage *= damage_stamina_factor(attacker_state.stamina)

    # Compromised chin
    if target == "head" and defender_state.chin_compromised:
        damage *= 1.2

    # GNP-DAMAGE-BUFF1: attacker landing from top of a dominant
    # position gets a real-MMA-shaped amplifier. The strike menu here
    # is GNP_PUNCH / GNP_HAMMER_FIST / GNP_ELBOW (bases 6-9) — without
    # this bump they hit softer than standing power strikes, which
    # inverts the control-to-damage conversion the DIAG1 memo traced.
    # The check is deliberately narrow: only DOMINANT positions with the
    # actor on top qualify — guard-top passes / side-control-top rides
    # do not. See outputs/control_conversion_diag1.md §5.
    if is_dominant_position:
        damage *= GNP_DOMINANT_DAMAGE_MULT

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
    """P3-3: Contest function rebuild (D13). Returns bool (success).

    Composites per fight_model_composites_v1.md; P_c form per contract
    §4. Family-specific base_chance bumps + upset variance branches
    from the pre-D13 CGS are RETIRED — F9 measurement showed the
    upset branch paid fighters to be worse (−9.3pp extreme). Skill
    differential is now analytical via S constants derived from D10
    targets, not threshold-based bumps.
    See _legacy_calculate_grappling_success below for pre-D13 code.
    """
    cls = _grapple_class(action)
    a_eff, d_eff = _assemble_composite(cls, attacker, defender)

    # Stamina (composite scalar). No pressure/threat scalars here —
    # grappling has no "you can't commit" penalty analogous to strikes.
    a_eff *= (attacker_state.stamina / 100)
    d_eff *= (defender_state.stamina / 100)

    # Symmetric variance (D13)
    a_eff *= random.uniform(0.85, 1.15)
    d_eff *= random.uniform(0.85, 1.15)

    p_c = _p_c(cls, a_eff, d_eff)
    return random.random() < p_c


def _legacy_calculate_grappling_success(
    attacker: FighterAttributes,
    defender: FighterAttributes,
    action: GrapplingAction,
    attacker_state: FighterState,
    defender_state: FighterState,
    fight_state: FightState
) -> bool:
    """RETIRED-NOT-DELETED (P3-3, C19 pending). Pre-D13 CGS verbatim."""
    takedown_diff = attacker.takedowns - defender.takedowns
    if action in {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG}:
        # DISTANCE TAKEDOWNS: takedowns vs takedown_defense
        # Shooting from distance is HARD - defenders see it coming
        offense = attacker.takedowns
        defense = defender.takedown_defense + defender.speed // 4  # Speed helps sprawl
        base_chance = 0.08  # LOW base - distance TDs are hard
        multiplier = 0.32  # Reduced multiplier
        
        # TAKEDOWN DIFFERENTIAL BONUS - small
        if takedown_diff >= 35:
            base_chance += 0.04
        elif takedown_diff >= 25:
            base_chance += 0.02
        
        # High TDD defenders get bonus
        if defender.takedown_defense >= 75:
            base_chance -= 0.03
        
        # STRIKER SPRAWL BONUS: Athletic strikers stuff shots
        if defender.speed >= 85:
            base_chance -= 0.03
            
    elif action == GrapplingAction.BODY_LOCK_TAKEDOWN:
        # CLINCH TAKEDOWNS: (takedowns + top_control) / 2 vs takedown_defense
        # Easier than distance but still contested
        offense = (attacker.takedowns + attacker.top_control) // 2
        defense = defender.takedown_defense + defender.strength // 4
        base_chance = 0.22  # REDUCED from 0.32
        multiplier = 0.38  # REDUCED
        
        # Takedown differential bonus - small
        if takedown_diff >= 35:
            base_chance += 0.06
        elif takedown_diff >= 25:
            base_chance += 0.03
            
    elif action in {GrapplingAction.TRIP, GrapplingAction.HIP_TOSS, GrapplingAction.SUPLEX}:
        # JUDO/GRECO THROWS: Requires timing and setup
        offense = (attacker.takedowns + attacker.top_control) // 2
        defense = (defender.takedowns + defender.top_control) // 2 + defender.strength // 4
        base_chance = 0.20  # REDUCED from 0.32
        multiplier = 0.40  # REDUCED from 0.50
        # Judo throws work better vs non-wrestlers
        if takedown_diff >= 30:
            base_chance += 0.06
        elif takedown_diff >= 20:
            base_chance += 0.03
            
    elif action in {GrapplingAction.PASS_TO_SIDE, GrapplingAction.PASS_TO_MOUNT,
                   GrapplingAction.KNEE_SLICE}:
        # GUARD PASSING: top_control vs guard
        offense = attacker.top_control
        defense = defender.guard
        base_chance = 0.28
        multiplier = 0.55
        # Top control differential bonus
        control_diff = attacker.top_control - defender.guard
        if control_diff >= 30:
            base_chance += 0.15
        elif control_diff >= 20:
            base_chance += 0.10
            
    elif action in {GrapplingAction.SCISSOR_SWEEP, GrapplingAction.BUTTERFLY_SWEEP,
                   GrapplingAction.FLOWER_SWEEP}:
        # SWEEPS: guard vs top_control - need timing
        offense = attacker.guard
        defense = defender.top_control + defender.strength // 4
        base_chance = 0.20  # REDUCED from 0.35
        multiplier = 0.45  # REDUCED from 0.55
        # Guard differential bonus
        sweep_diff = attacker.guard - defender.top_control
        if sweep_diff >= 30:
            base_chance += 0.08
        elif sweep_diff >= 20:
            base_chance += 0.04
            
    elif action in {GrapplingAction.SHRIMP_ESCAPE, GrapplingAction.BRIDGE_ESCAPE}:
        # ESCAPES: (guard + takedowns)/2 + strength vs top_control + strength
        offense = (attacker.guard + attacker.takedowns) // 2 + attacker.strength // 2
        defense = defender.top_control + defender.strength // 2
        base_chance = 0.48  # Balanced for control time vs sub finishes
        multiplier = 0.50
        # Strikers have hard time escaping controllers
        control_diff = defender.top_control - attacker.guard
        if control_diff >= 25:
            base_chance -= 0.05
            
    elif action == GrapplingAction.STAND_UP:
        # STANDING UP: (guard + takedowns)/2 + strength vs top_control
        offense = (attacker.guard + attacker.takedowns) // 2 + attacker.strength // 3
        defense = defender.top_control + defender.strength // 3
        base_chance = 0.28  # REDUCED - standing up is hard
        multiplier = 0.45
        
        # STRIKER STAND-UP BONUS: Strikers train for this
        if attacker.boxing >= 80 or attacker.kicks >= 80:
            base_chance += 0.06
        
        # Much harder vs elite controllers
        if defender.top_control >= 85:
            base_chance -= 0.08
        elif defender.top_control >= 75:
            base_chance -= 0.04
            
    elif action == GrapplingAction.CLINCH_ENTRY:
        # CLINCH ENTRY: (takedowns + clinch_control)/2 vs striking_defense
        # Both wrestlers AND clinch specialists can close distance.
        # Uses clinch_control (positional grappling) rather than clinch_striking
        # (damage) — entering the clinch is a control action.
        offense = (attacker.takedowns + attacker.clinch_control) // 2
        defense = defender.striking_defense + defender.speed // 3  # Speed helps avoid clinch
        
        base_chance = 0.20  # LOW base - closing distance is hard
        multiplier = 0.35
        
        # TAKEDOWN DIFFERENTIAL BONUS - small
        if takedown_diff >= 35:
            base_chance += 0.06
        elif takedown_diff >= 25:
            base_chance += 0.04
        elif takedown_diff >= 15:
            base_chance += 0.02
        
        # STRIKER DISTANCE BONUS: Good strikers maintain range
        if defender.striking_defense >= 85:
            base_chance -= 0.08  # Elite strikers keep distance
        elif defender.striking_defense >= 75:
            base_chance -= 0.04
        
        # Speed differential matters for closing distance
        speed_diff = attacker.speed - defender.speed
        if speed_diff >= 15:
            base_chance += 0.04
        elif speed_diff <= -15:
            base_chance -= 0.04
            
    elif action == GrapplingAction.CLINCH_BREAK:
        # CLINCH BREAK - Strikers need to escape to have a chance
        offense = attacker.strength // 2 + attacker.speed // 4  # Speed helps break
        defense = defender.top_control + defender.strength // 2
        base_chance = 0.15  # INCREASED from 0.12
        multiplier = 0.38  # INCREASED from 0.35
        
        # STRIKER CLINCH BREAK BONUS: Strikers train specifically to disengage
        if attacker.striking_defense >= 85:
            base_chance += 0.10  # Elite strikers escape better
        elif attacker.striking_defense >= 75:
            base_chance += 0.05
        
        # Speed differential helps break
        speed_diff = attacker.speed - defender.speed
        if speed_diff >= 10:
            base_chance += 0.04
        
        # Top control differential makes it harder
        control_diff = defender.top_control - attacker.guard
        if control_diff >= 35:
            base_chance -= 0.04
        elif control_diff >= 25:
            base_chance -= 0.02
    else:
        # Default: takedowns vs guard
        offense = attacker.takedowns
        defense = defender.guard
        base_chance = 0.25
        multiplier = 0.55
    
    # Stamina matters greatly in grappling
    offense *= (attacker_state.stamina / 100)
    defense *= (defender_state.stamina / 100)
    
    # BASE VARIANCE: Add significant randomness to every exchange
    # This creates "any given Sunday" upsets
    variance = random.uniform(0.75, 1.25)  # Â±25% variance (was Â±15%)
    offense *= variance
    
    # Calculate success chance
    success_chance = base_chance + (offense / (offense + defense + 1)) * multiplier
    success_chance = max(0.12, min(0.88, success_chance))
    
    # UPSET VARIANCE: Underdogs can succeed sometimes
    if offense < defense * 0.85:
        upset_roll = random.random()
        if upset_roll < 0.18:  # INCREASED from 15%
            success_chance = max(success_chance, 0.65)
        elif upset_roll < 0.35:  # INCREASED from 28%
            success_chance = min(success_chance + 0.25, 0.75)
    
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
    elif action == GrapplingAction.GUARD_PULL:
        new_position = Position.CLOSED_GUARD_BOTTOM
        new_top = None  # opponent becomes top
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

        # Maintain dominant_control_duration:
        # Increment when staying inside the dominant cluster,
        # reset when the bottom fighter escapes to neutral/standing.
        _DOMINANT_CLUSTER = {
            Position.BACK_MOUNT, Position.TRUCK,
            Position.MOUNT, Position.SIDE_CONTROL_TOP,
            Position.CRUCIFIX_TOP, Position.NORTH_SOUTH_TOP,
            Position.BACK_MOUNT_BOTTOM, Position.MOUNT_BOTTOM,
            Position.SIDE_CONTROL_BOTTOM, Position.CRUCIFIX_BOTTOM,
            Position.NORTH_SOUTH_BOTTOM,
        }
        if new_position in _DOMINANT_CLUSTER:
            fight_state.dominant_control_duration += 1
        else:
            fight_state.dominant_control_duration = 0
    
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
    
    Uses new 17-attribute system:
    - submissions: Offense (finishing ability)
    - guard + submissions: Defense (you need to know subs to defend them)
    
    Philosophy: Subs are EXTREMELY RARE but NEARLY ALWAYS FINISH
    - Only elite submission specialists (85+) attempt
    - But when they DO attempt, very high success rate
    """
    danger, escape_diff, positions = SUBMISSION_PROPERTIES[sub_type]

    if fight_state.position not in positions:
        return False, False, 0.0

    # ── P3-3: LOCK-IN via P_c form (sub_lockin class) ──
    # D13 recipe: submissions 100 vs guard 50 + submissions 50. S derived from
    # (P_EVEN=0.35, EDGE20_TARGET=0.49) preserves F8's measured +14pp/20pt slope.
    # RETIRED (pre-D13 lock-in): sub_diff threshold ladder (+0.35/0.28/0.20/0.12
    # up, −0.30/−0.18/−0.08 down); PURE SUBMISSION SPECIALIST additive; base
    # 0.30 constant; danger/10, heart//20, escape_diff/10, guard//35 divisor-zoo
    # additives; and the _sub_cap ceiling (P_MAX in CONTEST_P_MAX handles that
    # structurally). Skill differential is now analytical.
    a_eff_sub, d_eff_sub = _assemble_composite("sub_lockin", attacker, defender)
    a_eff_sub *= (attacker_state.stamina / 100)
    d_eff_sub *= (defender_state.stamina / 100)
    a_eff_sub *= random.uniform(0.85, 1.15)
    d_eff_sub *= random.uniform(0.85, 1.15)
    lock_in_chance = _p_c("sub_lockin", a_eff_sub, d_eff_sub)
    locked_in = random.random() < lock_in_chance

    if not locked_in:
        return False, False, 0.0

    # sub_diff still needed for the (unchanged) starting-progress bonuses below.
    sub_diff = attacker.submissions - defender.submissions
    # _tick_offense: pre-D13 stamina-scaled offense used for base_progress.
    # Tick mechanics stay this docket (§5a rebuild is P3-4).
    offense = (attacker.submissions + (danger / 10)) * (attacker_state.stamina / 100)
    
    # Start submission sequence - small starting progress so the race
    # actually plays out over multiple ticks rather than instant finish
    fight_state.submission_active = True
    fight_state.submission_type = sub_type
    fight_state.submission_attacker_id = attacker.fighter_id

    # Starting progress — low base leaves room for actual tick race
    base_progress = offense * 0.15

    # Specialist bonus — meaningful but not instant
    if attacker.submissions >= 92:
        base_progress *= 1.4
    elif attacker.submissions >= 88:
        base_progress *= 1.2

    # Submission differential — advantage, not auto-finish
    if sub_diff >= 30:
        base_progress *= 1.6
    elif sub_diff >= 20:
        base_progress *= 1.25
    elif sub_diff >= 10:
        base_progress *= 1.2
    
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
) -> Tuple[bool, bool, Optional[str]]:
    """P3-4c §5a submission model. Returns (escaped, finished, finish_kind).

    finish_kind ∈ {"tap", "sleep", "injury", None}. Non-None only when
    finished=True. Old tick mechanics preserved as
    `_legacy_process_submission_progress` (returned (escaped, finished)).

    Per-tick loop:
      1. Attacker tightens — same tighten_rate as legacy (skill still bites).
      2. Defender ESCAPE via P_c contest (new class "sub_escape").
      3. Stamina drain (attacker 3, defender 5) unchanged.
      4. TAP threshold = TAP_BASE × HEART_MULT × STATE_MULT. Base takes
         config.submission_progress_to_finish so the existing config
         dial still governs the neutral case.
      5. Refusal band past tap: choke → sleep, joint_lock → injury.

    Callers (fi._process_submission_exchange) unpack the 3-tuple; the
    finish_kind drives the outcome-string routing (Tap vs
    Technical Submission vs Submission (Injury)).
    """
    if not fight_state.submission_active:
        return False, False, None
    sub_type = fight_state.submission_type
    if sub_type is None:
        fight_state.submission_active = False
        return False, False, None

    danger, escape_diff, _ = SUBMISSION_PROPERTIES[sub_type]
    kind = SUBMISSION_KIND.get(sub_type, "joint_lock")

    # 1. Attacker tightens — preserve legacy tighten_rate (skill scaling
    #    remains). progress accumulator unchanged.
    offense = attacker.submissions * (attacker_state.stamina / 100)
    tighten_rate = 0.65 if attacker.submissions >= 92 else 0.45
    fight_state.submission_progress += (
        offense * tighten_rate * random.uniform(0.75, 1.25))

    # 2. Defender ESCAPE via P_c contest (sub_escape class).
    #    Assemble composites: escaper (defender) offense = guard 0.5 +
    #    subs 0.5; opponent (attacker) defense = subs 1.0. Stamina
    #    scales each side; two-sided variance.
    a_eff_e, d_eff_e = _assemble_composite(
        "sub_escape", defender, attacker)
    a_eff_e *= (defender_state.stamina / 100)
    d_eff_e *= (attacker_state.stamina / 100)
    a_eff_e *= random.uniform(0.85, 1.15)
    d_eff_e *= random.uniform(0.85, 1.15)
    escape_chance = _p_c("sub_escape", a_eff_e, d_eff_e)
    _escape_roll = random.random()

    # 3. Stamina drain (matches legacy).
    attacker_state.spend_stamina(3)
    defender_state.spend_stamina(5)

    if _escape_roll < escape_chance:
        fight_state.submission_active = False
        return True, False, None

    # 4. Tap threshold — heart × state modulation on TAP_BASE.
    tap_base = float(config.submission_progress_to_finish)
    _heart = getattr(defender, 'heart', 70)
    heart_mult = 1.0 + TAP_HEART_SPREAD * ((_heart - 60) / 40.0)
    _def_stam = getattr(defender_state, 'stamina', 100)
    _def_hp = getattr(defender_state, 'health', 100.0)
    _def_max_hp = 100.0 + getattr(defender, 'chin', 70) * 0.3
    _hp_frac = _def_hp / _def_max_hp if _def_max_hp else 0.0
    state_mult = (
        TAP_STATE_FLOOR
        + TAP_STATE_STAMINA_WEIGHT * min(1.0, max(0.0, _def_stam / 100.0))
        + TAP_STATE_HEALTH_WEIGHT * min(1.0, max(0.0, _hp_frac)))
    effective_tap = tap_base * heart_mult * state_mult
    fight_state.submission_effective_threshold = effective_tap

    # 5. Refusal band width (heart-scaled).
    refusal_width = REFUSAL_WIDTH_BASE * (
        1.0 + REFUSAL_HEART_SPREAD * ((_heart - 60) / 40.0))
    refusal_width = max(0.0, refusal_width)

    if fight_state.submission_progress >= effective_tap + refusal_width:
        # Past refusal band — the fighter never taps.
        fight_state.submission_active = False
        if kind == "choke":
            return False, True, "sleep"
        else:
            return False, True, "injury"
    if fight_state.submission_progress >= effective_tap:
        # Inside/at threshold — tap.
        fight_state.submission_active = False
        return False, True, "tap"

    return False, False, None


def _legacy_process_submission_progress(
    attacker: FighterAttributes,
    defender: FighterAttributes,
    attacker_state: FighterState,
    defender_state: FighterState,
    fight_state: FightState,
    config: FightConfig
) -> Tuple[bool, bool]:
    """RETIRED (P3-4c). Pre-§5a tick loop. Preserved for provenance;
    NOT called by production code. Returns (escaped, finished)."""
    if not fight_state.submission_active:
        return False, False
    sub_type = fight_state.submission_type
    if sub_type is None:
        fight_state.submission_active = False
        return False, False
    danger, escape_diff, _ = SUBMISSION_PROPERTIES[sub_type]
    offense = attacker.submissions * (attacker_state.stamina / 100)
    tighten_rate = 0.65 if attacker.submissions >= 92 else 0.45
    fight_state.submission_progress += offense * tighten_rate * random.uniform(0.75, 1.25)
    defense = ((defender.guard + defender.submissions) // 2) * (defender_state.stamina / 100)
    defense += defender.heart * 0.03
    fight_state.submission_escape_progress += defense * 0.38 * random.uniform(0.75, 1.25)
    attacker_state.spend_stamina(3)
    defender_state.spend_stamina(5)
    if fight_state.submission_progress >= config.submission_progress_to_finish:
        fight_state.submission_active = False
        return False, True
    _def_stamina = getattr(defender_state, 'stamina', 100)
    _composure = getattr(defender, 'composure', 70)
    _composure_bonus = (_composure - 70) * 0.002
    _fatigue_escape_mult = max(0.55,
        _def_stamina / 100 + 0.3 + _composure_bonus)
    effective_escape = (
        config.submission_escape_threshold * _fatigue_escape_mult)
    if fight_state.submission_escape_progress >= effective_escape:
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
    round_stats: Dict[str, RoundStats],
    event_log: Optional[List[FightEvent]] = None
) -> Optional[Tuple[str, str]]:
    """
    Simulate a single exchange.
    Returns (winner_id, finish_method) if fight ends, else None.
    
    If event_log is provided, significant events will be appended for commentary.
    """
    fight_state.exchanges_this_round += 1
    fight_state.total_exchanges += 1
    fight_state.position_duration += 1
    
    current_round = fight_state.current_round
    current_exchange = fight_state.exchanges_this_round
    
    def log_event(event_type: str, actor: FighterAttributes, target: FighterAttributes,
                  action: str = None, success: bool = True, damage: float = 0.0,
                  is_knockdown: bool = False, is_finish: bool = False, 
                  new_position: str = None, extra: Dict = None):
        """Helper to log events if event_log is provided."""
        if event_log is not None:
            event_log.append(FightEvent(
                event_type=event_type,
                round_num=current_round,
                exchange_num=current_exchange,
                actor_id=actor.fighter_id,
                actor_name=actor.name,
                target_id=target.fighter_id,
                target_name=target.name,
                action=action,
                success=success,
                damage=damage,
                position=fight_state.position.value if fight_state.position else None,
                new_position=new_position,
                is_knockdown=is_knockdown,
                is_finish=is_finish,
                extra=extra or {}
            ))
    
    # Process ongoing submission
    if fight_state.submission_active:
        attacker = fighter1 if fight_state.submission_attacker_id == fighter1.fighter_id else fighter2
        defender = fighter2 if attacker == fighter1 else fighter1
        attacker_state = fighter1_state if attacker == fighter1 else fighter2_state
        defender_state = fighter2_state if attacker == fighter1 else fighter1_state
        
        # C22 FIX A: 3-tuple unpack matches P3-4c §5a
        # process_submission_progress return shape. finish_kind is
        # discarded here — this fe.simulate_fight path is retired-not-
        # deleted (no live web-app caller per verify.md T1) and returns
        # only the legacy "Submission (<sub>)" form. When a live caller
        # exists again it should upgrade to the finish_kind vocabulary.
        escaped, finished, _finish_kind = process_submission_progress(
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
    
    # TAKEDOWN INITIATIVE BONUS: Grapplers threatening but not dominating
    # In standing, wrestlers use level changes and feints that disrupt striker rhythm
    if fight_state.position in STANDING_POSITIONS:
        # Wrestlers get initiative bonus - but reduced to prevent dominance
        if fighter1.takedowns >= 85:
            f1_initiative += 6  # REDUCED from 12
        elif fighter1.takedowns >= 70:
            f1_initiative += 3  # REDUCED from 6
        if fighter2.takedowns >= 85:
            f2_initiative += 6  # REDUCED from 12
        elif fighter2.takedowns >= 70:
            f2_initiative += 3  # REDUCED from 6
        
        # SUBMISSION THREAT: High-level submission artists threaten from everywhere
        # Imanari rolls, guard pulls, flying submissions - they're dangerous
        if fighter1.submissions >= 85:
            f1_initiative += 8  # Elite sub game - always a threat
        elif fighter1.submissions >= 75:
            f1_initiative += 4
        if fighter2.submissions >= 85:
            f2_initiative += 8
        elif fighter2.submissions >= 75:
            f2_initiative += 4
    
    # IN CLINCH: Takedowns AND clinch striking matter
    # The faster fighter can't "run away" when clinched
    if fight_state.position in CLINCH_POSITIONS:
        # Takedown skill gives initiative in clinch
        f1_initiative += fighter1.takedowns // 6  # Up to +15 for 95 takedowns
        f2_initiative += fighter2.takedowns // 6
        
        # CLINCH MASTERY: clinch_control drives positional initiative.
        # The fighter with grip dominance dictates what happens in the
        # clinch — they decide whether to strike, takedown, or break.
        f1_initiative += fighter1.clinch_control // 5  # Up to +18 for 90 clinch_control
        f2_initiative += fighter2.clinch_control // 5

        # ELITE CLINCH CONTROLLER BONUS: True specialists get extra
        if fighter1.clinch_control >= 85:
            f1_initiative += 10  # Elite grip dominance
        if fighter2.clinch_control >= 85:
            f2_initiative += 10
        
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
            # Cache strike key once for downstream use (leg TKO, cut tracking, named finishes)
            _st_val = strike.value if hasattr(strike, 'value') else str(strike)
            damage, target = calculate_strike_damage(
                attacker, defender, strike, attacker_state, defender_state, was_counter
            )
            
            # WRESTLER THREAT DAMAGE REDUCTION
            # Strikers can't throw with full power when worried about takedowns
            # This is CRITICAL - grapplers pressure makes strikers tentative
            if fight_state.position in STANDING_POSITIONS:
                takedown_threat = defender.takedowns - attacker.takedowns
                if takedown_threat >= 30:
                    damage *= 0.65  # 35% damage reduction vs elite wrestler
                elif takedown_threat >= 20:
                    damage *= 0.75  # 25% reduction
                elif takedown_threat >= 10:
                    damage *= 0.85  # 15% reduction
                
                # Submission threat also makes strikers cautious (flying subs, imanari)
                sub_threat = defender.submissions - attacker.submissions
                if sub_threat >= 30:
                    damage *= 0.85  # Additional 15% reduction
                elif sub_threat >= 20:
                    damage *= 0.92  # Additional 8% reduction

            # GnP bonus from dominant positions — compensates for the
            # global strike base drop (0.3→0.20) which incidentally
            # suppressed ground-and-pound finish rates.
            _DOMINANT_GNP = {
                Position.BACK_MOUNT, Position.MOUNT,
                Position.SIDE_CONTROL_TOP, Position.CRUCIFIX_TOP,
                Position.NORTH_SOUTH_TOP,
            }
            if fight_state.position in _DOMINANT_GNP:
                damage *= GNP_DOMINANT_DAMAGE_MULT

            # Apply config damage multiplier (compensates for increased exchanges)
            damage *= config.damage_multiplier
            
            is_knockdown, is_finish = defender_state.apply_damage(damage, target)

            # ── Leg kick TKO ──────────────────────────────
            # Once legs are severely compromised, each additional
            # leg strike risks a TKO — fighter can't stand/move.
            if (not is_finish and target == "legs"
                    and defender_state.damage.is_compromised_legs):
                _leg_tko_chance = min(0.15,
                    (defender_state.damage.leg_kicks_absorbed - 6) * 0.02)
                if defender_state.stamina < 50:
                    _leg_tko_chance *= 1.4
                if random.random() < _leg_tko_chance:
                    is_finish = True
                    finish_type = "TKO (Leg Kicks)"
                    log_event(
                        event_type="finish",
                        actor=attacker,
                        target=defender,
                        action=finish_type,
                        is_finish=True,
                        extra={"finish_type": finish_type}
                    )
                    return (attacker.fighter_id, finish_type)

            # ── Cut accumulation from elbows ─────────────
            _elbow_types = {
                "elbow_horizontal", "elbow_vertical",
                "elbow_spinning", "elbow_upward",
                "gnp_elbow", "clinch_elbow"
            }
            if _st_val in _elbow_types and target == "head":
                _cut_chance = 0.25 + (attacker.strength / 400)
                if random.random() < _cut_chance:
                    defender_state.damage.cuts += 1

            # FLASH KO MECHANIC: anyone can catch their opponent with
            # a clean head shot. Power/boxing fighters more likely;
            # already-hurt defenders much more vulnerable.
            if not is_finish and target == "head" and damage >= 5:
                flash_ko_chance = 0.01
                if attacker.boxing >= 75 or attacker.strength >= 75:
                    flash_ko_chance *= 1.5
                elif attacker.boxing >= 65 or attacker.strength >= 65:
                    flash_ko_chance *= 1.2
                if defender_state.health < 40:
                    flash_ko_chance *= 2.0
                flash_ko_chance = min(0.12, flash_ko_chance)
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
            
            # Log strike event
            log_event(
                event_type="strike",
                actor=attacker,
                target=defender,
                action=strike.value if hasattr(strike, 'value') else str(strike),
                success=True,
                damage=damage,
                is_knockdown=is_knockdown,
                is_finish=is_finish,
                extra={"target_area": target, "was_counter": was_counter}
            )
            
            if is_finish:
                # Named finish types — specific strike method logged
                _specialty_ko_map = {
                    "flying_knee":         "KO (Flying Knee)",
                    "wheel_kick":          "KO (Wheel Kick)",
                    "spinning_elbow":      "KO (Spinning Elbow)",
                    "elbow_spinning":      "KO (Spinning Elbow)",
                    "head_kick":           "KO (Head Kick)",
                    "knee_head":           "KO (Knee)",
                    "spinning_back_kick":  "KO (Spinning Back Kick)",
                    "superman_punch":      "KO (Superman Punch)",
                    "body_kick":           "TKO (Body Shot)",
                    "knee_body":           "TKO (Body Shot)",
                    "front_kick":          "TKO (Body Shot)" if target == "body" else "KO",
                }
                if target == "body":
                    finish_type = _specialty_ko_map.get(_st_val, "TKO (Body Shot)")
                else:
                    finish_type = _specialty_ko_map.get(_st_val, "KO")
                log_event(
                    event_type="finish",
                    actor=attacker,
                    target=defender,
                    action=finish_type,
                    is_finish=True,
                    extra={"finish_type": finish_type, "strike_type": _st_val}
                )
                return (attacker.fighter_id, finish_type)

            # ── Referee stoppage — taking unanswered shots while rocked ──
            if (not is_finish
                    and defender_state.is_rocked
                    and target == "head"):
                if not hasattr(defender_state, '_rocked_shots_taken'):
                    defender_state._rocked_shots_taken = 0
                defender_state._rocked_shots_taken += 1
                _ref_stop_chance = min(0.35,
                    defender_state._rocked_shots_taken * 0.08)
                _ref_stop_chance *= max(0.4,
                    1 - (defender.fight_iq / 250) - (defender.heart / 350))
                if random.random() < _ref_stop_chance:
                    _ref_method = "TKO (Referee Stoppage)"
                    log_event(
                        event_type="finish",
                        actor=attacker,
                        target=defender,
                        action=_ref_method,
                        is_finish=True,
                        extra={"finish_type": _ref_method}
                    )
                    return (attacker.fighter_id, _ref_method)

            # ── Rocked fighter in standup → grappler exploits ──
            # A) High takedowns shoot; B) High submissions take the back
            if (not is_finish
                    and defender_state.is_rocked
                    and target == "head"
                    and fight_state.position in STANDING_POSITIONS):

                if attacker.takedowns >= 68:
                    _shoot_chance = min(0.18,
                        (attacker.takedowns - 60) * 0.006)
                    _shoot_chance *= max(0.8,
                        1 + (attacker.takedowns - defender.takedown_defense) / 150)
                    if random.random() < _shoot_chance:
                        fight_state.position = (
                            Position.BACK_MOUNT
                            if random.random() < 0.55
                            else Position.MOUNT
                        )
                        fight_state.top_fighter_id = attacker.fighter_id
                        log_event(
                            event_type="grappling",
                            actor=attacker,
                            target=defender,
                            action="takedown_rocked",
                            success=True,
                            extra={"position": fight_state.position.value,
                                   "rocked_takedown": True}
                        )

                elif (attacker.submissions >= 65
                        and getattr(defender_state, '_rocked_shots_taken', 0) >= 2):
                    _back_chance = min(0.12,
                        (attacker.submissions - 60) * 0.004)
                    if random.random() < _back_chance:
                        fight_state.position = Position.STANDING_BACK
                        fight_state.top_fighter_id = attacker.fighter_id
                        log_event(
                            event_type="grappling",
                            actor=attacker,
                            target=defender,
                            action="take_back_standing",
                            success=True,
                            extra={"position": "standing_back",
                                   "rocked_back_take": True}
                        )

            if is_knockdown:
                round_stats[attacker.fighter_id].knockdowns += 1
                fight_state.position = Position.KNOCKDOWN_STANDING
                fight_state.top_fighter_id = attacker.fighter_id
                log_event(
                    event_type="knockdown",
                    actor=attacker,
                    target=defender,
                    action=strike.value if hasattr(strike, 'value') else str(strike),
                    is_knockdown=True,
                    damage=damage
                )
        else:
            # Strike missed or blocked - log only occasionally for pacing
            if random.random() < 0.15:  # Log ~15% of misses for variety
                log_event(
                    event_type="strike",
                    actor=attacker,
                    target=defender,
                    action=strike.value if hasattr(strike, 'value') else str(strike),
                    success=False,
                    damage=0.0,
                    extra={"blocked": random.random() < 0.5}  # 50% blocked, 50% missed
                )
    
    elif action_type == "submission":
        sub_type = action_data
        locked_in, finished, progress = attempt_submission(
            attacker, defender, sub_type, attacker_state, defender_state, fight_state
        )
        
        round_stats[attacker.fighter_id].submission_attempts += 1
        attacker_state.spend_stamina(5)
        
        # Log submission attempt
        log_event(
            event_type="submission",
            actor=attacker,
            target=defender,
            action=sub_type.value if hasattr(sub_type, 'value') else str(sub_type),
            success=locked_in,
            extra={"locked_in": locked_in, "progress": progress}
        )
        
        # FLASH SUBMISSION: any fighter with submission skill who
        # locks in gets a chance to finish — specialists much more often,
        # already-hurt defenders harder to defend.
        if locked_in and not finished and attacker.submissions >= 60:
            flash_sub_chance = 0.02
            if attacker.submissions >= 85:
                flash_sub_chance *= 2.0
            elif attacker.submissions >= 75:
                flash_sub_chance *= 1.5
            if defender_state.health < 50:
                flash_sub_chance *= 1.3
            flash_sub_chance = min(0.10, flash_sub_chance)
            if random.random() < flash_sub_chance:
                finished = True  # Flash submission!
        
        if finished:
            log_event(
                event_type="finish",
                actor=attacker,
                target=defender,
                action=f"Submission ({sub_type.value})",
                is_finish=True,
                extra={"finish_type": "submission", "submission_type": sub_type.value}
            )
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
        
        # Determine grappling event type for logging
        takedown_actions = {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG,
                          GrapplingAction.BODY_LOCK_TAKEDOWN}
        sweep_actions = {
            GrapplingAction.SCISSOR_SWEEP, GrapplingAction.FLOWER_SWEEP,
            GrapplingAction.BUTTERFLY_SWEEP, GrapplingAction.ELEVATOR_SWEEP,
        }
        escape_actions = {
            GrapplingAction.SHRIMP_ESCAPE, GrapplingAction.BRIDGE_ESCAPE,
            GrapplingAction.ELBOW_ESCAPE, GrapplingAction.TECHNICAL_STANDUP,
            GrapplingAction.STAND_UP, GrapplingAction.ESCAPE_LEGS,
            GrapplingAction.CLINCH_BREAK,
        }
        
        if success:
            new_pos = apply_position_change(fight_state, action, attacker.fighter_id, True)
            
            # Log successful grappling
            if action in takedown_actions:
                log_event(
                    event_type="takedown",
                    actor=attacker,
                    target=defender,
                    action=action.value if hasattr(action, 'value') else str(action),
                    success=True,
                    new_position=new_pos.value if new_pos and hasattr(new_pos, 'value') else str(new_pos)
                )
            elif action in sweep_actions:
                log_event(
                    event_type="sweep",
                    actor=attacker,
                    target=defender,
                    action=action.value if hasattr(action, 'value') else str(action),
                    success=True,
                    new_position=new_pos.value if new_pos and hasattr(new_pos, 'value') else str(new_pos)
                )
            elif action in escape_actions:
                log_event(
                    event_type="escape",
                    actor=attacker,
                    target=defender,
                    action=action.value if hasattr(action, 'value') else str(action),
                    success=True,
                    new_position=new_pos.value if new_pos and hasattr(new_pos, 'value') else str(new_pos)
                )
            else:
                # Position advance or other grappling
                log_event(
                    event_type="position",
                    actor=attacker,
                    target=defender,
                    action=action.value if hasattr(action, 'value') else str(action),
                    success=True,
                    new_position=new_pos.value if new_pos and hasattr(new_pos, 'value') else str(new_pos)
                )
            
            if new_pos in DOMINANT_POSITIONS:
                attacker_state.momentum = min(100, attacker_state.momentum + 10)
                defender_state.momentum = max(0, defender_state.momentum - 10)
            elif new_pos in STANDING_POSITIONS and action in escape_actions:
                attacker_state.momentum = min(100, attacker_state.momentum + 5)
                defender_state.momentum = max(0, defender_state.momentum - 5)
        else:
            # Log failed grappling (only takedown stuffs are interesting)
            if action in takedown_actions:
                log_event(
                    event_type="takedown",
                    actor=attacker,
                    target=defender,
                    action=action.value if hasattr(action, 'value') else str(action),
                    success=False,
                    extra={"stuffed": True}
                )
            
            # FAILED GRAPPLING PUNISHMENT
            # When takedowns/clinch entries fail, the defender can counter
            # This is especially important for Muay Thai vs Wrestlers
            if action in {GrapplingAction.SINGLE_LEG, GrapplingAction.DOUBLE_LEG,
                         GrapplingAction.CLINCH_ENTRY, GrapplingAction.BODY_LOCK_TAKEDOWN}:
                # Clinch fighters punish failed entries with knees.
                # Max() preserves Muay Thai's identity: elite strike skill
                # alone qualifies for devastating counter knees. Position
                # dominance (clinch_control) is tracked separately in
                # initiative/entry calcs — this gate is about damage.
                if fight_state.position in STANDING_POSITIONS or fight_state.position in CLINCH_POSITIONS:
                    counter_damage = 0
                    clinch_skill = max(defender.clinch_striking,
                                       defender.clinch_control)

                    # High clinch skill = DEVASTATING counter strikes
                    if clinch_skill >= 85:
                        counter_damage = random.uniform(5, 10)  # Elite Muay Thai knee
                    elif clinch_skill >= 75:
                        counter_damage = random.uniform(3, 7)
                    elif clinch_skill >= 65:
                        counter_damage = random.uniform(2, 5)
                    
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
            fight_state.dominant_control_duration = 0
    elif not fight_state.is_ground:
        fight_state.ground_inactivity = 0

    # Back-control stalemate break: after 12 exchanges in a dominant cluster
    # with no active submission, force an escape attempt to prevent infinite
    # BACK_MOUNT ↔ TRUCK cycling.
    _BACK_CONTROL_POSITIONS = {Position.BACK_MOUNT, Position.TRUCK,
                                Position.BACK_MOUNT_BOTTOM}
    if (fight_state.position in _BACK_CONTROL_POSITIONS
            and not fight_state.submission_active
            and fight_state.dominant_control_duration >= 12):
        # Roll for escape: bottom fighter has a 45% chance to escape
        # (weighted by guard attribute if we can identify the bottom fighter)
        escape_roll = random.random()
        if escape_roll < 0.45:
            # Escape succeeds - return to standing
            fight_state.position = Position.STANDING_OPEN
            fight_state.top_fighter_id = None
            fight_state.dominant_control_duration = 0
            fight_state.ground_inactivity = 0
            # Log the escape event
            bottom_id = (fighter2.fighter_id
                         if fight_state.top_fighter_id == fighter1.fighter_id
                         else fighter1.fighter_id)
            bottom_fighter = fighter1 if bottom_id == fighter1.fighter_id else fighter2
            top_fighter   = fighter2 if bottom_id == fighter1.fighter_id else fighter1
            log_event(
                event_type="escape",
                actor=bottom_fighter,
                target=top_fighter,
                action="back_escape",
                success=True,
                new_position=Position.STANDING_OPEN.value
            )
        else:
            # Escape fails — reset counter partway so it can try again soon
            fight_state.dominant_control_duration = 8
    
    # Stamina recovery
    attacker_state.recover_stamina(0.5)
    defender_state.recover_stamina(0.5)
    
    # Rock duration
    if fighter1_state.is_rocked:
        fighter1_state.rock_duration -= 1
        if fighter1_state.rock_duration <= 0:
            fighter1_state.is_rocked = False
            fighter1_state._rocked_shots_taken = 0
    if fighter2_state.is_rocked:
        fighter2_state.rock_duration -= 1
        if fighter2_state.rock_duration <= 0:
            fighter2_state.is_rocked = False
            fighter2_state._rocked_shots_taken = 0
    
    return None


# ============================================================================
# ROUND SCORING
# ============================================================================

def score_round(
    stats1: RoundStats,
    stats2: RoundStats,
    kd_inflicted_by_1: int,
    kd_inflicted_by_2: int
) -> Tuple[int, int]:
    """
    Score a round using 10-point must system.
    Balanced scoring: grappling control valued higher.

    #22 fix (fight_model_v1_0 §7): the KD args are now unambiguously named
    to prevent the fe.simulate_fight suffered-vs-inflicted mismatch that
    awarded rounds to the knocked-down fighter (227/227 measured).
    Callers must pass INFLICTED counts (KDs delivered BY that fighter),
    not the defender_state.knockdowns_this_round SUFFERED counters.
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
    if kd_inflicted_by_1 >= 2 and kd_inflicted_by_2 == 0:
        return (10, 8) if kd_inflicted_by_1 == 2 else (10, 7)
    if kd_inflicted_by_2 >= 2 and kd_inflicted_by_1 == 0:
        return (8, 10) if kd_inflicted_by_2 == 2 else (7, 10)

    # Single knockdown advantage
    if kd_inflicted_by_1 > kd_inflicted_by_2:
        if score1 > score2 * 1.5 and score1 > 20:
            return (10, 8)
        return (10, 9)
    if kd_inflicted_by_2 > kd_inflicted_by_1:
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
    elif ratio >= 0.52:
        return (10, 9)
    elif ratio <= 0.48:
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
    
    # Event log for commentary generation
    event_log: List[FightEvent] = field(default_factory=list)
    
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
            "fighter2_stats": self.fighter2_stats,
            "event_log": [e.to_dict() for e in self.event_log]
        }


# ============================================================================
# MAIN FIGHT SIMULATION
# ============================================================================

def simulate_fight(
    fighter1: FighterAttributes,
    fighter2: FighterAttributes,
    config: Optional[FightConfig] = None,
    fighter1_fatigue: int = 0,
    fighter2_fatigue: int = 0,
    heat_level: int = 0,
) -> FightResult:
    """
    Simulate a complete fight.
    
    Args:
        fighter1: First fighter's attributes
        fighter2: Second fighter's attributes
        config: Fight configuration (rounds, etc.)
        fighter1_fatigue: Fighter 1's fatigue level (0-100), affects starting stamina
        fighter2_fatigue: Fighter 2's fatigue level (0-100), affects starting stamina
        heat_level: Rivalry heat level (0-100), affects damage and aggression
    
    Returns:
        Complete fight result
    """
    if config is None:
        config = FightConfig.standard_fight()

    # STAGE 0d — assert the atomic config invariant BEFORE any heat scaling.
    # Fires on every FE call site (world_init pre-gen, quick_simulate, direct
    # callers). See FightConfig docstring + _assert_sanctioned_config for the
    # full contract.
    _assert_sanctioned_config(config)

    # Calculate heat modifiers
    # Heat stages: 0-20 neutral, 21-40 tension, 41-60 bad blood, 61-80 heated, 81-100 war
    heat_damage_mult = 1.0
    heat_composure_penalty = 0
    heat_aggression_bonus = 0.0
    
    if heat_level > 80:
        heat_damage_mult = 1.20
        heat_composure_penalty = 12
        heat_aggression_bonus = 0.20
    elif heat_level > 60:
        heat_damage_mult = 1.15
        heat_composure_penalty = 8
        heat_aggression_bonus = 0.15
    elif heat_level > 40:
        heat_damage_mult = 1.10
        heat_composure_penalty = 5
        heat_aggression_bonus = 0.10
    elif heat_level > 20:
        heat_damage_mult = 1.05
        heat_composure_penalty = 3
        heat_aggression_bonus = 0.05
    
    # Calculate starting stamina based on fatigue
    # Fatigued fighters start with reduced stamina
    def get_starting_stamina(fatigue: int) -> float:
        """Calculate starting stamina from fatigue level.

        Rewards smart camp management — coming in at peak condition
        gives a small but meaningful starting stamina bonus.
        The engine uses stamina as a multiplier on action effectiveness,
        so starting at 103 vs 100 matters in close fights.
        """
        fatigue = max(0, min(100, fatigue))
        if fatigue <= 10:
            return 103.0  # Peak condition — perfect taper
        elif fatigue <= 20:
            return 100.0  # Fresh
        elif fatigue <= 40:
            return 95.0   # Rested
        elif fatigue <= 60:
            return 88.0   # Ready
        elif fatigue <= 80:
            return 78.0   # Tired
        else:
            return 65.0   # Exhausted
    
    f1_starting_stamina = get_starting_stamina(fighter1_fatigue)
    f2_starting_stamina = get_starting_stamina(fighter2_fatigue)
    
    # Apply heat composure penalty (temporary reduction during fight)
    # Store original values to not permanently modify the fighter
    f1_effective_composure = max(20, fighter1.composure - heat_composure_penalty)
    f2_effective_composure = max(20, fighter2.composure - heat_composure_penalty)
    
    # Calculate starting health (base + chin bonus)
    # Lowered to 100 + chin*0.3 for raised finish rate
    f1_max_health = 100.0 + fighter1.chin * 0.3
    f2_max_health = 100.0 + fighter2.chin * 0.3
    
    # Initialize states with recovery rating for between-round mechanics
    # P3-4c — chin_rating + composure_rating mirrored from RECOVERY-WIRE1.
    # Byte-inert until FI_CHIN_WIRING_ENABLED / FI_COMPOSURE_WIRING_ENABLED
    # are True (defaults False).
    f1_state = FighterState(
        fighter_id=fighter1.fighter_id,
        name=fighter1.name,
        health=f1_max_health,
        max_health=f1_max_health,
        stamina=f1_starting_stamina,
        recovery_rating=fighter1.recovery,
        cardio_rating=fighter1.cardio,
        chin_rating=fighter1.chin,
        composure_rating=fighter1.composure,
    )
    f2_state = FighterState(
        fighter_id=fighter2.fighter_id,
        name=fighter2.name,
        health=f2_max_health,
        max_health=f2_max_health,
        stamina=f2_starting_stamina,
        recovery_rating=fighter2.recovery,
        cardio_rating=fighter2.cardio,
        chin_rating=fighter2.chin,
        composure_rating=fighter2.composure,
    )
    
    fight_state = FightState(fighter1=f1_state, fighter2=f2_state)
    
    # Apply heat damage multiplier to config (creates modified version)
    # Heat makes both fighters hit harder due to adrenaline/emotion
    #
    # STAGE 0d — SANCTIONED CONFIG MUTATION. The only legal one in the tree.
    # Produces damage_multiplier outside the allowlist by design
    # (0.42 × up to 1.20 = 0.42–0.504, or 0.48 × up to 1.20 = 0.48–0.576).
    # The triple assertion sits UPSTREAM of this line ON PURPOSE — if you
    # are here because you found a config carrying an unlisted
    # damage_multiplier and grepped the allowlist, this is why. Heat scaling
    # is an FE-only mechanism; FI has no equivalent. Filed for the Stage 1
    # parity map (Stage 3 delegation must resolve which behavior survives).
    if heat_damage_mult > 1.0:
        # Create a copy with modified damage multiplier
        from dataclasses import replace
        config = replace(config, damage_multiplier=config.damage_multiplier * heat_damage_mult)
    
    # Store heat level for event logging
    fight_state.heat_level = heat_level
    
    # Round stats
    all_stats: Dict[str, List[RoundStats]] = {
        fighter1.fighter_id: [],
        fighter2.fighter_id: []
    }
    
    round_scores: List[Tuple[int, int]] = []
    
    # Event log for commentary
    event_log: List[FightEvent] = []
    
    # Fight loop
    for round_num in range(1, config.scheduled_rounds + 1):
        fight_state.current_round = round_num
        fight_state.new_round()
        
        round_stats = {
            fighter1.fighter_id: RoundStats(),
            fighter2.fighter_id: RoundStats()
        }
        
        # Log round start
        event_log.append(FightEvent(
            event_type="round_start",
            round_num=round_num,
            exchange_num=0,
            actor_id=fighter1.fighter_id,
            actor_name=fighter1.name,
            target_id=fighter2.fighter_id,
            target_name=fighter2.name,
            extra={"total_rounds": config.scheduled_rounds}
        ))
        
        # Exchange loop
        for _ in range(config.exchanges_per_round):
            result = simulate_exchange(
                fighter1, fighter2,
                f1_state, f2_state,
                fight_state, config,
                round_stats,
                event_log  # Pass event_log
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
                    fighter2_final_state=f2_state.to_dict(),
                    event_log=event_log
                )
        
        # End of round
        all_stats[fighter1.fighter_id].append(round_stats[fighter1.fighter_id])
        all_stats[fighter2.fighter_id].append(round_stats[fighter2.fighter_id])

        # ── Between-round stoppages ──────────────────────────
        # Doctor, corner, cut stoppages. All rare by design —
        # when they happen, they're memorable. Only fires if
        # the fight isn't already over and another round remains.
        if round_num < config.scheduled_rounds:
            for _ftr, _ftr_state, _opp in [
                (fighter1, f1_state, fighter2),
                (fighter2, f2_state, fighter1),
            ]:
                _stopped = False
                _stop_method = None

                # Cut stoppage — deep cuts from elbows
                # ENGINE-DEAD-KNOBS1 (2026-07-11): threshold now reads
                # config.doctor_check_cut_threshold (default 3, was
                # hardcoded 3 before this ship). At the default value
                # the behavior is byte-identical.
                _cut_thr = config.doctor_check_cut_threshold
                if _ftr_state.damage.cuts >= _cut_thr and not _stopped:
                    _cut_stop_chance = min(0.35,
                        (_ftr_state.damage.cuts - (_cut_thr - 1)) * 0.08)
                    _cut_stop_chance *= max(0.4, 1 - (_ftr.heart / 200))
                    if random.random() < _cut_stop_chance:
                        _stop_method = "TKO (Doctor Stoppage - Cuts)"
                        _stopped = True

                # Doctor stoppage — severe cumulative damage
                if (not _stopped
                        and _ftr_state.health < 28
                        and _ftr_state.damage.head > 55):
                    _doc_chance = min(0.14,
                        (55 - _ftr_state.health) * 0.003)
                    _doc_chance *= max(0.5, 1 - (_ftr.heart / 250))
                    if _ftr_state.chin_compromised:
                        _doc_chance *= 1.35
                    if random.random() < _doc_chance:
                        _stop_method = "TKO (Doctor Stoppage)"
                        _stopped = True

                # Corner stoppage — trainer throws in the towel
                if (not _stopped
                        and round_num >= 2
                        and _ftr_state.health < 22
                        and _ftr_state.knockdowns_total >= 2):
                    _corner_chance = min(0.18,
                        (_ftr_state.knockdowns_total - 1) * 0.06)
                    _corner_chance *= max(0.3, 1 - (_ftr.heart / 300))
                    if random.random() < _corner_chance:
                        _stop_method = "TKO (Corner Stoppage)"
                        _stopped = True

                if _stopped and _stop_method:
                    event_log.append(FightEvent(
                        event_type="finish",
                        round_num=round_num,
                        exchange_num=config.exchanges_per_round,
                        actor_id=_opp.fighter_id,
                        actor_name=_opp.name,
                        target_id=_ftr.fighter_id,
                        target_name=_ftr.name,
                        action=_stop_method,
                        is_finish=True,
                        extra={"finish_type": _stop_method,
                               "between_round": True}
                    ))
                    return FightResult(
                        winner_id=_opp.fighter_id,
                        loser_id=_ftr.fighter_id,
                        method=_stop_method,
                        finish_round=round_num,
                        finish_time="5:00",
                        fighter1_stats=[s.to_dict() for s in
                                        all_stats[fighter1.fighter_id]],
                        fighter2_stats=[s.to_dict() for s in
                                        all_stats[fighter2.fighter_id]],
                        fighter1_final_state=f1_state.to_dict(),
                        fighter2_final_state=f2_state.to_dict(),
                        event_log=event_log
                    )

        # Score round
        # #22 fix (fight_model_v1_0 §7): knockdowns_this_round on a FighterState
        # is KDs SUFFERED by that fighter, so INFLICTED-by-1 == f2.suffered
        # and INFLICTED-by-2 == f1.suffered. Pre-fix passed the suffered
        # order (matched-order call), awarding round bonuses to the KD
        # sufferer — 227/227 asymmetric rounds measured.
        s1, s2 = score_round(
            round_stats[fighter1.fighter_id],
            round_stats[fighter2.fighter_id],
            f2_state.knockdowns_this_round,  # KDs inflicted BY fighter1
            f1_state.knockdowns_this_round   # KDs inflicted BY fighter2
        )
        round_scores.append((s1, s2))
        
        # Log round end
        event_log.append(FightEvent(
            event_type="round_end",
            round_num=round_num,
            exchange_num=config.exchanges_per_round,
            actor_id=fighter1.fighter_id,
            actor_name=fighter1.name,
            target_id=fighter2.fighter_id,
            target_name=fighter2.name,
            extra={
                "f1_score": s1, 
                "f2_score": s2,
                "f1_strikes": round_stats[fighter1.fighter_id].significant_strikes_landed,
                "f2_strikes": round_stats[fighter2.fighter_id].significant_strikes_landed,
                "f1_takedowns": round_stats[fighter1.fighter_id].takedowns_landed,
                "f2_takedowns": round_stats[fighter2.fighter_id].takedowns_landed,
            }
        ))
    
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
                # Judges system returned no winner — break by cumulative
                # judge totals across all scorecards. Only true draw when
                # sums are exactly equal.
                _f1_total_p = sum(sc.fighter1_score
                                  for sc in decision_result.scorecards)
                _f2_total_p = sum(sc.fighter2_score
                                  for sc in decision_result.scorecards)
                if _f1_total_p > _f2_total_p:
                    winner_id = fighter1.fighter_id
                    loser_id = fighter2.fighter_id
                    winner_name = fighter1.name
                    loser_name = fighter2.name
                elif _f2_total_p > _f1_total_p:
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
            # Tiebreaker case — judges system returned None winner but
            # cumulative totals broke the tie. Mark as Split for narrative.
            if (winner_id is not None
                    and decision_result.winner not in (1, 2)):
                decision_type = "Split"
            
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
                fighter2_final_state=f2_state.to_dict(),
                event_log=event_log
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
    elif f1_wins == 0 and f2_wins == 0:
        # All judges tied — break by cumulative judge totals.
        # Only a true draw when sums are exactly equal.
        _f1_total = sum(j1 for j1, _ in judge_scores)
        _f2_total = sum(j2 for _, j2 in judge_scores)
        if _f1_total > _f2_total:
            winner_id = fighter1.fighter_id
            loser_id = fighter2.fighter_id
            decision_type = "Split"  # narrow win
        elif _f2_total > _f1_total:
            winner_id = fighter2.fighter_id
            loser_id = fighter1.fighter_id
            decision_type = "Split"
        else:
            winner_id = None
            loser_id = None
            decision_type = None
    else:
        # 1-1-1 split (impossible in fallback path since judges
        # use identical scoring with noise — but defensive).
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
        fighter2_final_state=f2_state.to_dict(),
        event_log=event_log
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
        # Physical (P3-4d added power)
        strength=f1_overall, speed=f1_overall, cardio=f1_overall,
        chin=f1_overall, recovery=f1_overall, power=f1_overall,
        # Striking
        boxing=f1_overall, kicks=f1_overall, clinch_striking=f1_overall,
        striking_defense=f1_overall,
        # Grappling
        takedowns=f1_overall, takedown_defense=f1_overall, top_control=f1_overall,
        submissions=f1_overall, guard=f1_overall,
        # Clinch (1)
        clinch_control=f1_overall,
        # Mental
        heart=f1_overall, fight_iq=f1_overall, composure=f1_overall
    )
    fighter2 = FighterAttributes(
        fighter_id="f2",
        name="Fighter 2",
        # Physical
        # Physical (P3-4d added power)
        strength=f2_overall, speed=f2_overall, cardio=f2_overall,
        chin=f2_overall, recovery=f2_overall, power=f2_overall,
        # Striking
        boxing=f2_overall, kicks=f2_overall, clinch_striking=f2_overall,
        striking_defense=f2_overall,
        # Grappling
        takedowns=f2_overall, takedown_defense=f2_overall, top_control=f2_overall,
        submissions=f2_overall, guard=f2_overall,
        # Clinch (1)
        clinch_control=f2_overall,
        # Mental
        heart=f2_overall, fight_iq=f2_overall, composure=f2_overall
    )
    
    # STAGE 0d — pinned to PRE_GEN_LEGACY explicitly. quick_simulate is a
    # tests/CLI helper; pre-Stage-0d it inherited (55, 0.42, 6) via the OLD
    # dataclass defaults. Explicit pin keeps that behavior when the default
    # lifted to LIVE_PLAY. Deleted at Stage 3 with PRE_GEN_LEGACY.
    config = FightConfig(
        scheduled_rounds=rounds,
        exchanges_per_round=55,
        damage_multiplier=0.42,
        standup_threshold=6,
    )
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
