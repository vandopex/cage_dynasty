#!/usr/bin/env python3
"""
CAGE DYNASTY - Fight Simulation Balance & Mechanics Test Suite
==============================================================

This script runs thousands of simulated fights to validate:
- Section A: Style matchup balance (42 test cases)
- Section B: Fight engine mechanics (isolated attribute tests)

Run from project root:
    cd ~/Desktop/Games/cage_dynasty
    python3 tests/test_fight_simulation_balance.py [options]

Options:
    -n, --num-fights N    Fights per test case (default: 1000)
    -a, --section-a       Run only Section A (Style Balance)
    -b, --section-b       Run only Section B (Mechanics)
    -d, --detailed        Print detailed results for each test
    -q, --quiet           Minimal output during tests
    -s, --seed N          Random seed (default: 42, use -1 for random)

Created: January 2025
"""

import sys
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from enum import Enum

# ============================================================================
# PATH SETUP - Must happen before any project imports
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================================
# FIGHTING STYLE ENUM (matches types.py)
# ============================================================================

class FightingStyle(Enum):
    """
    The 11 fighting style archetypes.
    Must match the enum in types.py exactly.
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


# ============================================================================
# FIGHT SIMULATION WRAPPER
# ============================================================================

def get_fight_simulator():
    """
    Import and return the quick_narrated_fight function.
    Also returns a style mapping from local enum to project enum.
    """
    try:
        # Try nested structure first (production)
        from simulation.fight_integration import quick_narrated_fight
        from core.types import FightingStyle as ProjectFightingStyle
        
        # Map our local enum to project enum
        style_map = {
            FightingStyle.STRIKER: ProjectFightingStyle.STRIKER,
            FightingStyle.COUNTER_STRIKER: ProjectFightingStyle.COUNTER_STRIKER,
            FightingStyle.PRESSURE_FIGHTER: ProjectFightingStyle.PRESSURE_FIGHTER,
            FightingStyle.POINT_FIGHTER: ProjectFightingStyle.POINT_FIGHTER,
            FightingStyle.MUAY_THAI: ProjectFightingStyle.MUAY_THAI,
            FightingStyle.WRESTLER: ProjectFightingStyle.WRESTLER,
            FightingStyle.GROUND_AND_POUND: ProjectFightingStyle.GROUND_AND_POUND,
            FightingStyle.BJJ_SPECIALIST: ProjectFightingStyle.BJJ_SPECIALIST,
            FightingStyle.CLINCH_FIGHTER: ProjectFightingStyle.CLINCH_FIGHTER,
            FightingStyle.SPRAWL_AND_BRAWL: ProjectFightingStyle.SPRAWL_AND_BRAWL,
            FightingStyle.BALANCED: ProjectFightingStyle.BALANCED,
        }
        
        return quick_narrated_fight, style_map
    except ImportError as e:
        print(f"\nERROR: Could not import fight simulation modules: {e}")
        print(f"\nMake sure you're running from the cage_dynasty root directory:")
        print(f"  cd ~/Desktop/Games/cage_dynasty")
        print(f"  python3 tests/test_fight_simulation_balance.py")
        sys.exit(1)


def run_single_fight(
    f1_name: str,
    f1_style: FightingStyle,
    f1_ovr: int,
    f2_name: str,
    f2_style: FightingStyle,
    f2_ovr: int,
    rounds: int = 3
) -> Dict[str, Any]:
    """
    Run a single fight and return the NarratedFightResult.
    """
    quick_narrated_fight, style_map = get_fight_simulator()
    
    result = quick_narrated_fight(
        f1_overall=f1_ovr,
        f2_overall=f2_ovr,
        f1_name=f1_name,
        f2_name=f2_name,
        rounds=rounds,
        f1_style=style_map[f1_style],
        f2_style=style_map[f2_style]
    )
    
    return result


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

FIGHTS_PER_TEST = 1000  # Number of fights per test case
RANDOM_SEED = 42        # For reproducibility (set to None for true random)


# ============================================================================
# FIGHTER FACTORY FOR SECTION B (Custom Attributes)
# ============================================================================

def create_custom_fighter(
    fighter_id: str,
    name: str,
    base_ovr: int = 70,
    # Physical overrides
    strength: Optional[int] = None,
    speed: Optional[int] = None,
    cardio: Optional[int] = None,
    chin: Optional[int] = None,
    recovery: Optional[int] = None,
    # Striking overrides
    boxing: Optional[int] = None,
    kicks: Optional[int] = None,
    clinch_striking: Optional[int] = None,
    striking_defense: Optional[int] = None,
    # Grappling overrides
    takedowns: Optional[int] = None,
    takedown_defense: Optional[int] = None,
    top_control: Optional[int] = None,
    submissions: Optional[int] = None,
    guard: Optional[int] = None,
    # Mental overrides
    heart: Optional[int] = None,
    fight_iq: Optional[int] = None,
    composure: Optional[int] = None,
    # Style
    fighting_style: FightingStyle = FightingStyle.BALANCED,
) -> Dict[str, Any]:
    """
    Create a fighter attribute dictionary for Section B tests.
    
    All attributes default to base_ovr, then apply any overrides.
    Returns a dict that can be used with simulate_narrated_fight.
    """
    return {
        "fighter_id": fighter_id,
        "name": name,
        # Physical (5)
        "strength": strength if strength is not None else base_ovr,
        "speed": speed if speed is not None else base_ovr,
        "cardio": cardio if cardio is not None else base_ovr,
        "chin": chin if chin is not None else base_ovr,
        "recovery": recovery if recovery is not None else base_ovr,
        # Striking (4)
        "boxing": boxing if boxing is not None else base_ovr,
        "kicks": kicks if kicks is not None else base_ovr,
        "clinch_striking": clinch_striking if clinch_striking is not None else base_ovr,
        "striking_defense": striking_defense if striking_defense is not None else base_ovr,
        # Grappling (5)
        "takedowns": takedowns if takedowns is not None else base_ovr,
        "takedown_defense": takedown_defense if takedown_defense is not None else base_ovr,
        "top_control": top_control if top_control is not None else base_ovr,
        "submissions": submissions if submissions is not None else base_ovr,
        "guard": guard if guard is not None else base_ovr,
        # Mental (3)
        "heart": heart if heart is not None else base_ovr,
        "fight_iq": fight_iq if fight_iq is not None else base_ovr,
        "composure": composure if composure is not None else base_ovr,
        # Style
        "fighting_style": fighting_style,
    }


def get_simulate_narrated_fight():
    """Import and return the simulate_narrated_fight function, FighterAttributes class, and style map."""
    try:
        from simulation.fight_integration import simulate_narrated_fight
        from simulation.fight_engine import FighterAttributes
        from core.types import FightingStyle as ProjectFightingStyle
        
        # Map our local enum to project enum
        style_map = {
            FightingStyle.STRIKER: ProjectFightingStyle.STRIKER,
            FightingStyle.COUNTER_STRIKER: ProjectFightingStyle.COUNTER_STRIKER,
            FightingStyle.PRESSURE_FIGHTER: ProjectFightingStyle.PRESSURE_FIGHTER,
            FightingStyle.POINT_FIGHTER: ProjectFightingStyle.POINT_FIGHTER,
            FightingStyle.MUAY_THAI: ProjectFightingStyle.MUAY_THAI,
            FightingStyle.WRESTLER: ProjectFightingStyle.WRESTLER,
            FightingStyle.GROUND_AND_POUND: ProjectFightingStyle.GROUND_AND_POUND,
            FightingStyle.BJJ_SPECIALIST: ProjectFightingStyle.BJJ_SPECIALIST,
            FightingStyle.CLINCH_FIGHTER: ProjectFightingStyle.CLINCH_FIGHTER,
            FightingStyle.SPRAWL_AND_BRAWL: ProjectFightingStyle.SPRAWL_AND_BRAWL,
            FightingStyle.BALANCED: ProjectFightingStyle.BALANCED,
        }
        
        return simulate_narrated_fight, FighterAttributes, style_map
    except ImportError as e:
        print(f"\nERROR: Could not import fight simulation modules: {e}")
        print(f"\nMake sure you're running from the cage_dynasty root directory:")
        print(f"  cd ~/Desktop/Games/cage_dynasty")
        print(f"  python3 tests/test_fight_simulation_balance.py")
        sys.exit(1)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class FightStats:
    """Statistics for a single fight"""
    winner_name: str
    method: str
    finish_round: Optional[int]
    is_finish: bool
    is_ko: bool
    is_tko: bool
    is_submission: bool
    is_decision: bool
    is_draw: bool
    total_rounds: int
    fighter1_strikes: int = 0
    fighter2_strikes: int = 0
    fighter1_takedowns: int = 0
    fighter2_takedowns: int = 0


@dataclass
class TestResults:
    """Aggregated results for a test case"""
    test_name: str
    fighter1_style: str
    fighter2_style: str
    fighter1_ovr: int
    fighter2_ovr: int
    fighter1_name: str = "Fighter One"
    fighter2_name: str = "Fighter Two"
    total_fights: int = 0
    
    # Win tracking
    fighter1_wins: int = 0
    fighter2_wins: int = 0
    draws: int = 0
    
    # Method breakdown
    ko_finishes: int = 0
    tko_finishes: int = 0
    submission_finishes: int = 0
    decisions: int = 0
    
    # Round tracking
    round1_finishes: int = 0
    round2_finishes: int = 0
    round3_finishes: int = 0
    round4_finishes: int = 0
    round5_finishes: int = 0
    
    # Aggregate stats
    total_strikes_f1: int = 0
    total_strikes_f2: int = 0
    total_takedowns_f1: int = 0
    total_takedowns_f2: int = 0
    
    @property
    def fighter1_win_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.fighter1_wins / self.total_fights
    
    @property
    def fighter2_win_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.fighter2_wins / self.total_fights
    
    @property
    def finish_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return (self.ko_finishes + self.tko_finishes + self.submission_finishes) / self.total_fights
    
    @property
    def ko_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.ko_finishes / self.total_fights
    
    @property
    def tko_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.tko_finishes / self.total_fights
    
    @property
    def submission_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.submission_finishes / self.total_fights
    
    @property
    def decision_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.decisions / self.total_fights
    
    @property
    def avg_strikes_f1(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.total_strikes_f1 / self.total_fights
    
    @property
    def avg_strikes_f2(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.total_strikes_f2 / self.total_fights
    
    @property
    def avg_takedowns_f1(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.total_takedowns_f1 / self.total_fights
    
    @property
    def avg_takedowns_f2(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.total_takedowns_f2 / self.total_fights


# ============================================================================
# SIMULATION RUNNER
# ============================================================================

def extract_fight_stats(result, f1_name: str, f2_name: str) -> FightStats:
    """Extract statistics from a NarratedFightResult"""
    method = result.method.upper()
    
    is_ko = "KO" in method and "TKO" not in method
    is_tko = "TKO" in method
    is_submission = "SUB" in method
    is_decision = "DECISION" in method or "DEC" in method
    is_draw = result.is_draw if hasattr(result, 'is_draw') else False
    
    # Get strike/takedown stats from round stats if available
    f1_strikes = 0
    f2_strikes = 0
    f1_takedowns = 0
    f2_takedowns = 0
    
    if hasattr(result, 'fighter1_stats'):
        for round_stats in result.fighter1_stats:
            f1_strikes += round_stats.get("significant_strikes_landed", 0)
            f1_takedowns += round_stats.get("takedowns_landed", 0)
    
    if hasattr(result, 'fighter2_stats'):
        for round_stats in result.fighter2_stats:
            f2_strikes += round_stats.get("significant_strikes_landed", 0)
            f2_takedowns += round_stats.get("takedowns_landed", 0)
    
    return FightStats(
        winner_name=result.winner_name if hasattr(result, 'winner_name') else "",
        method=result.method,
        finish_round=result.finish_round if hasattr(result, 'finish_round') else None,
        is_finish=result.is_finish if hasattr(result, 'is_finish') else not is_decision,
        is_ko=is_ko,
        is_tko=is_tko,
        is_submission=is_submission,
        is_decision=is_decision,
        is_draw=is_draw,
        total_rounds=result.total_rounds if hasattr(result, 'total_rounds') else 3,
        fighter1_strikes=f1_strikes,
        fighter2_strikes=f2_strikes,
        fighter1_takedowns=f1_takedowns,
        fighter2_takedowns=f2_takedowns,
    )


def run_test_case(
    test_name: str,
    f1_style: FightingStyle,
    f1_ovr: int,
    f2_style: FightingStyle,
    f2_ovr: int,
    num_fights: int = FIGHTS_PER_TEST,
    rounds: int = 3,
    verbose: bool = False
) -> TestResults:
    """Run multiple fights and aggregate results"""
    
    f1_name = "Fighter One"
    f2_name = "Fighter Two"
    
    results = TestResults(
        test_name=test_name,
        fighter1_style=f1_style.value,
        fighter2_style=f2_style.value,
        fighter1_ovr=f1_ovr,
        fighter2_ovr=f2_ovr,
        fighter1_name=f1_name,
        fighter2_name=f2_name,
    )
    
    for i in range(num_fights):
        try:
            fight_result = run_single_fight(
                f1_name=f1_name,
                f1_style=f1_style,
                f1_ovr=f1_ovr,
                f2_name=f2_name,
                f2_style=f2_style,
                f2_ovr=f2_ovr,
                rounds=rounds
            )
            
            stats = extract_fight_stats(fight_result, f1_name, f2_name)
            
            # Track results
            results.total_fights += 1
            
            if stats.is_draw:
                results.draws += 1
            elif stats.winner_name == f1_name:
                results.fighter1_wins += 1
            elif stats.winner_name == f2_name:
                results.fighter2_wins += 1
            else:
                results.draws += 1  # Unknown winner treated as draw
            
            # Method tracking
            if stats.is_ko:
                results.ko_finishes += 1
            elif stats.is_tko:
                results.tko_finishes += 1
            elif stats.is_submission:
                results.submission_finishes += 1
            elif stats.is_decision:
                results.decisions += 1
            
            # Round tracking
            if stats.finish_round == 1:
                results.round1_finishes += 1
            elif stats.finish_round == 2:
                results.round2_finishes += 1
            elif stats.finish_round == 3:
                results.round3_finishes += 1
            elif stats.finish_round == 4:
                results.round4_finishes += 1
            elif stats.finish_round == 5:
                results.round5_finishes += 1
            
            # Stats tracking
            results.total_strikes_f1 += stats.fighter1_strikes
            results.total_strikes_f2 += stats.fighter2_strikes
            results.total_takedowns_f1 += stats.fighter1_takedowns
            results.total_takedowns_f2 += stats.fighter2_takedowns
            
            if verbose and (i + 1) % 100 == 0:
                print(f"  {test_name}: {i + 1}/{num_fights} fights completed")
                
        except Exception as e:
            print(f"  ERROR in fight {i + 1}: {e}")
            continue
    
    return results


# ============================================================================
# SECTION A: STYLE BALANCE TESTS (42 Test Cases)
# ============================================================================

def get_style_balance_test_cases() -> List[Dict[str, Any]]:
    """Define all 42 style balance test cases"""
    
    test_cases = []
    
    # --- Mirror Matches (Baseline) ---
    test_cases.extend([
        {"name": "A01_Mirror_Striker_Equal", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.STRIKER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A02_Mirror_Striker_Gap10", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.STRIKER, "f1_ovr": 90, "f2_ovr": 80},
        {"name": "A03_Mirror_Striker_Gap20", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.STRIKER, "f1_ovr": 90, "f2_ovr": 70},
        {"name": "A04_Mirror_Wrestler_Equal", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.WRESTLER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A05_Mirror_BJJ_Equal", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.BJJ_SPECIALIST, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A06_Mirror_Balanced_Equal", "f1_style": FightingStyle.BALANCED, "f2_style": FightingStyle.BALANCED, "f1_ovr": 85, "f2_ovr": 85},
    ])
    
    # --- Striker vs All Grapplers ---
    test_cases.extend([
        {"name": "A07_Striker_v_Wrestler", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.WRESTLER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A08_Striker_v_BJJ", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.BJJ_SPECIALIST, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A09_Striker_v_GnP", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.GROUND_AND_POUND, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A10_Striker_v_Clinch", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.CLINCH_FIGHTER, "f1_ovr": 90, "f2_ovr": 90},
    ])
    
    # --- Wrestler vs All Strikers ---
    test_cases.extend([
        {"name": "A11_Wrestler_v_Striker", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.STRIKER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A12_Wrestler_v_Counter", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.COUNTER_STRIKER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A13_Wrestler_v_Pressure", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.PRESSURE_FIGHTER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A14_Wrestler_v_Point", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.POINT_FIGHTER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A15_Wrestler_v_MuayThai", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.MUAY_THAI, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A16_Wrestler_v_Sprawl", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.SPRAWL_AND_BRAWL, "f1_ovr": 90, "f2_ovr": 90},
    ])
    
    # --- BJJ vs All Strikers ---
    test_cases.extend([
        {"name": "A17_BJJ_v_Striker", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.STRIKER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A18_BJJ_v_Counter", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.COUNTER_STRIKER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A19_BJJ_v_Pressure", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.PRESSURE_FIGHTER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A20_BJJ_v_Point", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.POINT_FIGHTER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A21_BJJ_v_MuayThai", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.MUAY_THAI, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A22_BJJ_v_Sprawl", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.SPRAWL_AND_BRAWL, "f1_ovr": 90, "f2_ovr": 90},
    ])
    
    # --- BJJ vs All Grapplers ---
    test_cases.extend([
        {"name": "A23_BJJ_v_Wrestler", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.WRESTLER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A24_BJJ_v_GnP", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.GROUND_AND_POUND, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A25_BJJ_v_Clinch", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.CLINCH_FIGHTER, "f1_ovr": 90, "f2_ovr": 90},
    ])
    
    # --- Wrestler vs Other Grapplers ---
    test_cases.extend([
        {"name": "A26_Wrestler_v_GnP", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.GROUND_AND_POUND, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A27_Wrestler_v_Clinch", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.CLINCH_FIGHTER, "f1_ovr": 90, "f2_ovr": 90},
    ])
    
    # --- Striker Sub-Style Clashes ---
    test_cases.extend([
        {"name": "A28_Striker_v_Counter", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.COUNTER_STRIKER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A29_Striker_v_Pressure", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.PRESSURE_FIGHTER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A30_Pressure_v_Counter", "f1_style": FightingStyle.PRESSURE_FIGHTER, "f2_style": FightingStyle.COUNTER_STRIKER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A31_Point_v_Pressure", "f1_style": FightingStyle.POINT_FIGHTER, "f2_style": FightingStyle.PRESSURE_FIGHTER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A32_MuayThai_v_Striker", "f1_style": FightingStyle.MUAY_THAI, "f2_style": FightingStyle.STRIKER, "f1_ovr": 90, "f2_ovr": 90},
    ])
    
    # --- Anti-Style Checks ---
    test_cases.extend([
        {"name": "A33_Sprawl_v_Wrestler", "f1_style": FightingStyle.SPRAWL_AND_BRAWL, "f2_style": FightingStyle.WRESTLER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A34_Sprawl_v_BJJ", "f1_style": FightingStyle.SPRAWL_AND_BRAWL, "f2_style": FightingStyle.BJJ_SPECIALIST, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A35_Sprawl_v_GnP", "f1_style": FightingStyle.SPRAWL_AND_BRAWL, "f2_style": FightingStyle.GROUND_AND_POUND, "f1_ovr": 90, "f2_ovr": 90},
    ])
    
    # --- Balanced vs Specialists ---
    test_cases.extend([
        {"name": "A36_Balanced_v_Striker", "f1_style": FightingStyle.BALANCED, "f2_style": FightingStyle.STRIKER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A37_Balanced_v_Wrestler", "f1_style": FightingStyle.BALANCED, "f2_style": FightingStyle.WRESTLER, "f1_ovr": 90, "f2_ovr": 90},
        {"name": "A38_Balanced_v_BJJ", "f1_style": FightingStyle.BALANCED, "f2_style": FightingStyle.BJJ_SPECIALIST, "f1_ovr": 90, "f2_ovr": 90},
    ])
    
    # --- Skill Gap Tests (Various Styles) ---
    test_cases.extend([
        {"name": "A39_Wrestler90_v_Striker80", "f1_style": FightingStyle.WRESTLER, "f2_style": FightingStyle.STRIKER, "f1_ovr": 90, "f2_ovr": 80},
        {"name": "A40_Striker90_v_Wrestler80", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.WRESTLER, "f1_ovr": 90, "f2_ovr": 80},
        {"name": "A41_BJJ90_v_Striker80", "f1_style": FightingStyle.BJJ_SPECIALIST, "f2_style": FightingStyle.STRIKER, "f1_ovr": 90, "f2_ovr": 80},
        {"name": "A42_Striker80_v_BJJ90", "f1_style": FightingStyle.STRIKER, "f2_style": FightingStyle.BJJ_SPECIALIST, "f1_ovr": 80, "f2_ovr": 90},
    ])
    
    return test_cases


# ============================================================================
# SECTION B: FIGHT ENGINE MECHANICS TESTS (Isolated Attributes)
# ============================================================================

def get_mechanics_test_cases() -> List[Dict[str, Any]]:
    """
    Define isolated mechanic test cases using custom FighterAttributes.
    
    These tests isolate specific attributes to validate individual mechanics.
    All other attributes are held constant at a baseline (typically 70).
    """
    
    BASE = 70  # Baseline for non-tested attributes
    
    test_cases = []
    
    # =========================================================================
    # B1: TAKEDOWN SUCCESS RATE BY WRESTLING DIFFERENTIAL
    # =========================================================================
    test_cases.extend([
        {
            "name": "B01_TD_High90_v_TDD50",
            "description": "High takedowns (90) vs low TDD (50) - should see high TD success",
            "f1_attrs": {"takedowns": 90, "top_control": 90},
            "f2_attrs": {"takedown_defense": 50, "guard": 50},
            "base_ovr": BASE,
        },
        {
            "name": "B02_TD_High90_v_TDD70",
            "description": "High takedowns (90) vs average TDD (70)",
            "f1_attrs": {"takedowns": 90, "top_control": 90},
            "f2_attrs": {"takedown_defense": 70, "guard": 70},
            "base_ovr": BASE,
        },
        {
            "name": "B03_TD_High90_v_TDD90",
            "description": "High takedowns (90) vs high TDD (90) - contested wrestling",
            "f1_attrs": {"takedowns": 90, "top_control": 90},
            "f2_attrs": {"takedown_defense": 90, "guard": 90},
            "base_ovr": BASE,
        },
        {
            "name": "B04_TD_Low50_v_TDD90",
            "description": "Low takedowns (50) vs high TDD (90) - should rarely get TD",
            "f1_attrs": {"takedowns": 50, "top_control": 50},
            "f2_attrs": {"takedown_defense": 90, "guard": 90},
            "base_ovr": BASE,
        },
    ])
    
    # =========================================================================
    # B2: SUBMISSION FINISH RATE BY BJJ DIFFERENTIAL
    # =========================================================================
    test_cases.extend([
        {
            "name": "B05_Sub_High90_v_Guard50",
            "description": "High submissions (90) vs low guard (50) - high sub rate expected",
            "f1_attrs": {"submissions": 90, "takedowns": 85, "top_control": 85},
            "f2_attrs": {"guard": 50, "takedown_defense": 50},
            "base_ovr": BASE,
        },
        {
            "name": "B06_Sub_High90_v_Guard70",
            "description": "High submissions (90) vs average guard (70)",
            "f1_attrs": {"submissions": 90, "takedowns": 85, "top_control": 85},
            "f2_attrs": {"guard": 70, "takedown_defense": 70},
            "base_ovr": BASE,
        },
        {
            "name": "B07_Sub_High90_v_Guard90",
            "description": "High submissions (90) vs high guard (90) - contested grappling",
            "f1_attrs": {"submissions": 90, "takedowns": 85, "top_control": 85},
            "f2_attrs": {"guard": 90, "takedown_defense": 85},
            "base_ovr": BASE,
        },
        {
            "name": "B08_Sub_Low50_v_Guard90",
            "description": "Low submissions (50) vs high guard (90) - very low sub rate",
            "f1_attrs": {"submissions": 50, "takedowns": 70, "top_control": 60},
            "f2_attrs": {"guard": 90, "takedown_defense": 85},
            "base_ovr": BASE,
        },
    ])
    
    # =========================================================================
    # B3: KO/TKO RATE BY STRIKING DIFFERENTIAL
    # =========================================================================
    test_cases.extend([
        {
            "name": "B09_KO_Boxing90_v_Defense50",
            "description": "High boxing (90) + power vs low defense (50) - high KO rate",
            "f1_attrs": {"boxing": 90, "strength": 90, "speed": 85},
            "f2_attrs": {"striking_defense": 50, "chin": 50},
            "base_ovr": BASE,
        },
        {
            "name": "B10_KO_Boxing90_v_Defense70",
            "description": "High boxing (90) vs average defense (70)",
            "f1_attrs": {"boxing": 90, "strength": 90, "speed": 85},
            "f2_attrs": {"striking_defense": 70, "chin": 70},
            "base_ovr": BASE,
        },
        {
            "name": "B11_KO_Boxing90_v_Defense90",
            "description": "High boxing (90) vs high defense (90) - contested striking",
            "f1_attrs": {"boxing": 90, "strength": 90, "speed": 85},
            "f2_attrs": {"striking_defense": 90, "chin": 90},
            "base_ovr": BASE,
        },
        {
            "name": "B12_KO_Boxing50_v_Defense90",
            "description": "Low boxing (50) vs high defense (90) - low KO rate",
            "f1_attrs": {"boxing": 50, "strength": 50, "speed": 50},
            "f2_attrs": {"striking_defense": 90, "chin": 90},
            "base_ovr": BASE,
        },
    ])
    
    # =========================================================================
    # B4: CHIN EFFECTIVENESS (Survival Rate)
    # =========================================================================
    test_cases.extend([
        {
            "name": "B13_IronChin90_v_KO_Artist",
            "description": "Iron chin (90) vs power puncher - chin should help survival",
            "f1_attrs": {"chin": 90, "recovery": 90, "heart": 85},
            "f2_attrs": {"boxing": 90, "strength": 90, "speed": 85},
            "base_ovr": BASE,
        },
        {
            "name": "B14_GlassChin50_v_KO_Artist",
            "description": "Glass chin (50) vs power puncher - high KO rate expected",
            "f1_attrs": {"chin": 50, "recovery": 50, "heart": 60},
            "f2_attrs": {"boxing": 90, "strength": 90, "speed": 85},
            "base_ovr": BASE,
        },
    ])
    
    # =========================================================================
    # B5: CARDIO EFFECT ON LATE ROUNDS (5-round fights)
    # =========================================================================
    test_cases.extend([
        {
            "name": "B15_Cardio_High90_v_Low50_5Rd",
            "description": "High cardio (90) vs low cardio (50) in 5 rounds - late advantage",
            "f1_attrs": {"cardio": 90, "heart": 85},
            "f2_attrs": {"cardio": 50, "heart": 60},
            "base_ovr": BASE,
            "rounds": 5,
        },
        {
            "name": "B16_Cardio_Equal70_5Rd",
            "description": "Equal cardio baseline in 5 rounds",
            "f1_attrs": {"cardio": 70, "heart": 70},
            "f2_attrs": {"cardio": 70, "heart": 70},
            "base_ovr": BASE,
            "rounds": 5,
        },
        {
            "name": "B17_Cardio_Low50_v_High90_5Rd",
            "description": "Low cardio (50) vs high cardio (90) - should lose late",
            "f1_attrs": {"cardio": 50, "heart": 60},
            "f2_attrs": {"cardio": 90, "heart": 85},
            "base_ovr": BASE,
            "rounds": 5,
        },
    ])
    
    # =========================================================================
    # B6: FIGHT IQ / COMPOSURE EFFECT
    # =========================================================================
    test_cases.extend([
        {
            "name": "B18_IQ_High90_v_Low50",
            "description": "High IQ/composure (90) vs low (50) - smarter fighting",
            "f1_attrs": {"fight_iq": 90, "composure": 90},
            "f2_attrs": {"fight_iq": 50, "composure": 50},
            "base_ovr": BASE,
        },
    ])
    
    # =========================================================================
    # B7: PURE GRAPPLER VS PURE STRIKER (Attribute-Based, No Style Modifier)
    # =========================================================================
    test_cases.extend([
        {
            "name": "B19_PureWrestler_v_PureStriker",
            "description": "Max grappling attrs vs max striking attrs - classic MMA clash",
            "f1_attrs": {
                "takedowns": 95, "takedown_defense": 90, "top_control": 95, 
                "submissions": 70, "guard": 85,
                "boxing": 50, "kicks": 50, "striking_defense": 60
            },
            "f2_attrs": {
                "boxing": 95, "kicks": 90, "striking_defense": 90, "strength": 85,
                "takedowns": 50, "takedown_defense": 60, "top_control": 50, "guard": 55
            },
            "base_ovr": 70,
            "f1_style": FightingStyle.WRESTLER,
            "f2_style": FightingStyle.STRIKER,
        },
        {
            "name": "B20_PureStriker_v_PureWrestler",
            "description": "Reverse of B19",
            "f1_attrs": {
                "boxing": 95, "kicks": 90, "striking_defense": 90, "strength": 85,
                "takedowns": 50, "takedown_defense": 60, "top_control": 50, "guard": 55
            },
            "f2_attrs": {
                "takedowns": 95, "takedown_defense": 90, "top_control": 95, 
                "submissions": 70, "guard": 85,
                "boxing": 50, "kicks": 50, "striking_defense": 60
            },
            "base_ovr": 70,
            "f1_style": FightingStyle.STRIKER,
            "f2_style": FightingStyle.WRESTLER,
        },
    ])
    
    # =========================================================================
    # B8: OVERALL SKILL GAP VALIDATION (Equal attributes, different levels)
    # =========================================================================
    test_cases.extend([
        {
            "name": "B21_Overall_90v90",
            "description": "Equal elite skill - should be ~50/50",
            "f1_attrs": {},
            "f2_attrs": {},
            "f1_base_ovr": 90,
            "f2_base_ovr": 90,
        },
        {
            "name": "B22_Overall_90v80",
            "description": "10 point gap - higher should win 60-75%",
            "f1_attrs": {},
            "f2_attrs": {},
            "f1_base_ovr": 90,
            "f2_base_ovr": 80,
        },
        {
            "name": "B23_Overall_90v70",
            "description": "20 point gap - higher should win 75-90%",
            "f1_attrs": {},
            "f2_attrs": {},
            "f1_base_ovr": 90,
            "f2_base_ovr": 70,
        },
        {
            "name": "B24_Overall_90v60",
            "description": "30 point gap - higher should dominate 85%+",
            "f1_attrs": {},
            "f2_attrs": {},
            "f1_base_ovr": 90,
            "f2_base_ovr": 60,
        },
        {
            "name": "B25_Overall_80v80",
            "description": "Equal mid-tier - should be ~50/50",
            "f1_attrs": {},
            "f2_attrs": {},
            "f1_base_ovr": 80,
            "f2_base_ovr": 80,
        },
        {
            "name": "B26_Overall_70v70",
            "description": "Equal lower-tier - should be ~50/50",
            "f1_attrs": {},
            "f2_attrs": {},
            "f1_base_ovr": 70,
            "f2_base_ovr": 70,
        },
    ])
    
    # =========================================================================
    # B9: EXTREME MATCHUPS
    # =========================================================================
    test_cases.extend([
        {
            "name": "B27_Elite95_v_Journeyman65",
            "description": "30pt gap - should be near total domination",
            "f1_attrs": {},
            "f2_attrs": {},
            "f1_base_ovr": 95,
            "f2_base_ovr": 65,
        },
        {
            "name": "B28_Can50_v_Can50",
            "description": "Two low-skill fighters - sloppy, unpredictable finishes",
            "f1_attrs": {},
            "f2_attrs": {},
            "f1_base_ovr": 50,
            "f2_base_ovr": 50,
        },
    ])
    
    return test_cases


# ============================================================================
# REPORT GENERATION
# ============================================================================

def print_section_header(title: str):
    """Print a formatted section header"""
    print()
    print("=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_results_table(results: List[TestResults], section: str):
    """Print results in a formatted table"""
    
    print_section_header(f"SECTION {section} RESULTS")
    
    # Header
    print(f"{'Test Name':<35} {'F1 Win%':>8} {'F2 Win%':>8} {'KO%':>6} {'TKO%':>6} {'Sub%':>6} {'Dec%':>6} {'Finish%':>8}")
    print("-" * 95)
    
    for r in results:
        print(f"{r.test_name:<35} {r.fighter1_win_rate*100:>7.1f}% {r.fighter2_win_rate*100:>7.1f}% "
              f"{r.ko_rate*100:>5.1f}% {r.tko_rate*100:>5.1f}% {r.submission_rate*100:>5.1f}% "
              f"{r.decision_rate*100:>5.1f}% {r.finish_rate*100:>7.1f}%")
    
    print("-" * 95)


def print_detailed_results(results: TestResults):
    """Print detailed breakdown for a single test"""
    print(f"\n--- {results.test_name} ---")
    print(f"  Matchup: {results.fighter1_style} ({results.fighter1_ovr}) vs {results.fighter2_style} ({results.fighter2_ovr})")
    print(f"  Total Fights: {results.total_fights}")
    print(f"  F1 Wins: {results.fighter1_wins} ({results.fighter1_win_rate*100:.1f}%)")
    print(f"  F2 Wins: {results.fighter2_wins} ({results.fighter2_win_rate*100:.1f}%)")
    print(f"  Draws: {results.draws}")
    print(f"  Methods:")
    print(f"    KO:  {results.ko_finishes} ({results.ko_rate*100:.1f}%)")
    print(f"    TKO: {results.tko_finishes} ({results.tko_rate*100:.1f}%)")
    print(f"    Sub: {results.submission_finishes} ({results.submission_rate*100:.1f}%)")
    print(f"    Dec: {results.decisions} ({results.decision_rate*100:.1f}%)")
    print(f"  Finish Rate: {results.finish_rate*100:.1f}%")
    print(f"  Avg Strikes: F1={results.avg_strikes_f1:.1f}, F2={results.avg_strikes_f2:.1f}")
    print(f"  Avg Takedowns: F1={results.avg_takedowns_f1:.2f}, F2={results.avg_takedowns_f2:.2f}")
    if results.round1_finishes + results.round2_finishes + results.round3_finishes > 0:
        total_finishes = results.round1_finishes + results.round2_finishes + results.round3_finishes + results.round4_finishes + results.round5_finishes
        print(f"  Finishes by Round: R1={results.round1_finishes}, R2={results.round2_finishes}, R3={results.round3_finishes}, R4={results.round4_finishes}, R5={results.round5_finishes}")


def generate_summary_report(section_a_results: List[TestResults], section_b_results: List[TestResults]):
    """Generate overall summary and recommendations"""
    
    print_section_header("SUMMARY ANALYSIS")
    
    # Calculate aggregates
    all_results = section_a_results + section_b_results
    
    total_fights = sum(r.total_fights for r in all_results)
    total_finishes = sum(r.ko_finishes + r.tko_finishes + r.submission_finishes for r in all_results)
    total_decisions = sum(r.decisions for r in all_results)
    total_kos = sum(r.ko_finishes for r in all_results)
    total_tkos = sum(r.tko_finishes for r in all_results)
    total_subs = sum(r.submission_finishes for r in all_results)
    
    print(f"\nOVERALL STATISTICS ({total_fights} total fights)")
    print(f"  Finish Rate: {total_finishes/total_fights*100:.1f}%")
    print(f"  Decision Rate: {total_decisions/total_fights*100:.1f}%")
    print(f"  KO Rate: {total_kos/total_fights*100:.1f}%")
    print(f"  TKO Rate: {total_tkos/total_fights*100:.1f}%")
    print(f"  Submission Rate: {total_subs/total_fights*100:.1f}%")
    
    # Flag potential issues
    print("\nPOTENTIAL BALANCE ISSUES:")
    issues_found = False
    
    for r in all_results:
        # Check mirror matches for 50/50
        if "Mirror" in r.test_name and "Equal" in r.test_name:
            if r.fighter1_win_rate < 0.42 or r.fighter1_win_rate > 0.58:
                print(f"  ⚠️  {r.test_name}: Win rate {r.fighter1_win_rate*100:.1f}% deviates from expected 50/50")
                issues_found = True
        
        # Check skill gaps
        if "Gap10" in r.test_name or "90v80" in r.test_name:
            if r.fighter1_win_rate < 0.55 or r.fighter1_win_rate > 0.85:
                print(f"  ⚠️  {r.test_name}: 10-point gap win rate {r.fighter1_win_rate*100:.1f}% outside expected 55-85%")
                issues_found = True
        
        if "Gap20" in r.test_name or "90v70" in r.test_name:
            if r.fighter1_win_rate < 0.70 or r.fighter1_win_rate > 0.95:
                print(f"  ⚠️  {r.test_name}: 20-point gap win rate {r.fighter1_win_rate*100:.1f}% outside expected 70-95%")
                issues_found = True
        
        # Check extreme finish rates
        if r.finish_rate > 0.85:
            print(f"  ⚠️  {r.test_name}: Very high finish rate {r.finish_rate*100:.1f}%")
            issues_found = True
        
        if r.finish_rate < 0.15:
            print(f"  ⚠️  {r.test_name}: Very low finish rate {r.finish_rate*100:.1f}%")
            issues_found = True
    
    if not issues_found:
        print("  ✅ No major balance issues detected!")
    
    print()


# ============================================================================
# MAIN TEST RUNNERS
# ============================================================================

def run_section_a(verbose: bool = True, num_fights: int = FIGHTS_PER_TEST) -> List[TestResults]:
    """Run all Section A (Style Balance) tests"""
    
    print_section_header("SECTION A: STYLE BALANCE TESTS")
    print(f"Running {num_fights} fights per test case...")
    
    test_cases = get_style_balance_test_cases()
    results = []
    
    for i, tc in enumerate(test_cases):
        print(f"\n[{i+1}/{len(test_cases)}] {tc['name']}...")
        
        result = run_test_case(
            test_name=tc["name"],
            f1_style=tc["f1_style"],
            f1_ovr=tc["f1_ovr"],
            f2_style=tc["f2_style"],
            f2_ovr=tc["f2_ovr"],
            num_fights=num_fights,
            verbose=verbose
        )
        
        results.append(result)
        
        if verbose:
            print(f"  -> F1 Win: {result.fighter1_win_rate*100:.1f}%, Finish: {result.finish_rate*100:.1f}%")
    
    return results


def run_section_b(verbose: bool = True, num_fights: int = FIGHTS_PER_TEST) -> List[TestResults]:
    """Run all Section B (Mechanics) tests using custom FighterAttributes"""
    
    print_section_header("SECTION B: FIGHT ENGINE MECHANICS TESTS")
    print(f"Running {num_fights} fights per test case...")
    print("(Using isolated attribute builds via simulate_narrated_fight)")
    
    # Get the simulation function, FighterAttributes class, and style map
    simulate_narrated_fight, FighterAttributes, style_map = get_simulate_narrated_fight()
    
    test_cases = get_mechanics_test_cases()
    results = []
    
    for i, tc in enumerate(test_cases):
        print(f"\n[{i+1}/{len(test_cases)}] {tc['name']}...")
        if "description" in tc:
            print(f"  ({tc['description']})")
        
        # Determine base overall for each fighter
        f1_base = tc.get("f1_base_ovr", tc.get("base_ovr", 70))
        f2_base = tc.get("f2_base_ovr", tc.get("base_ovr", 70))
        
        # Get attribute overrides
        f1_attrs = tc.get("f1_attrs", {})
        f2_attrs = tc.get("f2_attrs", {})
        
        # Get styles (default to BALANCED) and map to project enums
        f1_style_local = tc.get("f1_style", FightingStyle.BALANCED)
        f2_style_local = tc.get("f2_style", FightingStyle.BALANCED)
        f1_style = style_map[f1_style_local]
        f2_style = style_map[f2_style_local]
        
        # Get rounds (default 3)
        rounds = tc.get("rounds", 3)
        
        # Build custom fighters
        f1_dict = create_custom_fighter(
            fighter_id="fighter_1",
            name="Fighter One",
            base_ovr=f1_base,
            fighting_style=f1_style_local,  # Keep local for dict
            **f1_attrs
        )
        
        f2_dict = create_custom_fighter(
            fighter_id="fighter_2",
            name="Fighter Two",
            base_ovr=f2_base,
            fighting_style=f2_style_local,  # Keep local for dict
            **f2_attrs
        )
        
        # Create FighterAttributes objects with mapped styles
        fighter1 = FighterAttributes(
            fighter_id=f1_dict["fighter_id"],
            name=f1_dict["name"],
            strength=f1_dict["strength"],
            speed=f1_dict["speed"],
            cardio=f1_dict["cardio"],
            chin=f1_dict["chin"],
            recovery=f1_dict["recovery"],
            boxing=f1_dict["boxing"],
            kicks=f1_dict["kicks"],
            clinch_striking=f1_dict["clinch_striking"],
            striking_defense=f1_dict["striking_defense"],
            takedowns=f1_dict["takedowns"],
            takedown_defense=f1_dict["takedown_defense"],
            top_control=f1_dict["top_control"],
            submissions=f1_dict["submissions"],
            guard=f1_dict["guard"],
            heart=f1_dict["heart"],
            fight_iq=f1_dict["fight_iq"],
            composure=f1_dict["composure"],
            fighting_style=f1_style,  # Use mapped style
        )
        
        fighter2 = FighterAttributes(
            fighter_id=f2_dict["fighter_id"],
            name=f2_dict["name"],
            strength=f2_dict["strength"],
            speed=f2_dict["speed"],
            cardio=f2_dict["cardio"],
            chin=f2_dict["chin"],
            recovery=f2_dict["recovery"],
            boxing=f2_dict["boxing"],
            kicks=f2_dict["kicks"],
            clinch_striking=f2_dict["clinch_striking"],
            striking_defense=f2_dict["striking_defense"],
            takedowns=f2_dict["takedowns"],
            takedown_defense=f2_dict["takedown_defense"],
            top_control=f2_dict["top_control"],
            submissions=f2_dict["submissions"],
            guard=f2_dict["guard"],
            heart=f2_dict["heart"],
            fight_iq=f2_dict["fight_iq"],
            composure=f2_dict["composure"],
            fighting_style=f2_style,  # Use mapped style
        )
        
        # Initialize results
        test_results = TestResults(
            test_name=tc["name"],
            fighter1_style=f1_style_local.value if f1_style_local else "Balanced",
            fighter2_style=f2_style_local.value if f2_style_local else "Balanced",
            fighter1_ovr=fighter1.overall,
            fighter2_ovr=fighter2.overall,
            fighter1_name="Fighter One",
            fighter2_name="Fighter Two",
        )
        
        # Run fights
        for j in range(num_fights):
            try:
                fight_result = simulate_narrated_fight(fighter1, fighter2, rounds=rounds)
                
                stats = extract_fight_stats(fight_result, "Fighter One", "Fighter Two")
                
                # Track results
                test_results.total_fights += 1
                
                if stats.is_draw:
                    test_results.draws += 1
                elif stats.winner_name == "Fighter One":
                    test_results.fighter1_wins += 1
                elif stats.winner_name == "Fighter Two":
                    test_results.fighter2_wins += 1
                else:
                    test_results.draws += 1
                
                # Method tracking
                if stats.is_ko:
                    test_results.ko_finishes += 1
                elif stats.is_tko:
                    test_results.tko_finishes += 1
                elif stats.is_submission:
                    test_results.submission_finishes += 1
                elif stats.is_decision:
                    test_results.decisions += 1
                
                # Round tracking
                if stats.finish_round == 1:
                    test_results.round1_finishes += 1
                elif stats.finish_round == 2:
                    test_results.round2_finishes += 1
                elif stats.finish_round == 3:
                    test_results.round3_finishes += 1
                elif stats.finish_round == 4:
                    test_results.round4_finishes += 1
                elif stats.finish_round == 5:
                    test_results.round5_finishes += 1
                
                # Stats tracking
                test_results.total_strikes_f1 += stats.fighter1_strikes
                test_results.total_strikes_f2 += stats.fighter2_strikes
                test_results.total_takedowns_f1 += stats.fighter1_takedowns
                test_results.total_takedowns_f2 += stats.fighter2_takedowns
                
                if verbose and (j + 1) % 100 == 0:
                    print(f"    {j + 1}/{num_fights} fights completed")
                    
            except Exception as e:
                print(f"  ERROR in fight {j + 1}: {e}")
                continue
        
        results.append(test_results)
        
        if verbose:
            print(f"  -> F1 Win: {test_results.fighter1_win_rate*100:.1f}%, Finish: {test_results.finish_rate*100:.1f}%, "
                  f"KO: {test_results.ko_rate*100:.1f}%, Sub: {test_results.submission_rate*100:.1f}%")
            print(f"     Avg TDs: F1={test_results.avg_takedowns_f1:.1f}, F2={test_results.avg_takedowns_f2:.1f}")
    
    return results


def run_all_tests(
    verbose: bool = True,
    num_fights: int = FIGHTS_PER_TEST,
    run_a: bool = True,
    run_b: bool = True,
    detailed: bool = False
):
    """Run complete test suite"""
    
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)
        print(f"Random seed set to {RANDOM_SEED} for reproducibility")
    
    section_a_results = []
    section_b_results = []
    
    if run_a:
        section_a_results = run_section_a(verbose=verbose, num_fights=num_fights)
        print_results_table(section_a_results, "A")
        
        if detailed:
            for r in section_a_results:
                print_detailed_results(r)
    
    if run_b:
        section_b_results = run_section_b(verbose=verbose, num_fights=num_fights)
        print_results_table(section_b_results, "B")
        
        if detailed:
            for r in section_b_results:
                print_detailed_results(r)
    
    if run_a or run_b:
        generate_summary_report(section_a_results, section_b_results)
    
    return section_a_results, section_b_results


# ============================================================================
# PYTEST ENTRY POINTS
# ============================================================================

def test_fight_simulation_balance():
    """
    Pytest entry point - runs a smaller subset for CI/CD.
    Use standalone script for full 1000-fight tests.
    """
    # Run with fewer fights for pytest
    section_a_results, section_b_results = run_all_tests(
        verbose=False,
        num_fights=100,  # Reduced for faster test runs
        run_a=True,
        run_b=True,
        detailed=False
    )
    
    # Basic sanity checks
    for r in section_a_results + section_b_results:
        assert r.total_fights > 0, f"{r.test_name}: No fights completed"
        assert r.fighter1_wins + r.fighter2_wins + r.draws == r.total_fights, f"{r.test_name}: Win count mismatch"


# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cage Dynasty Fight Simulation Balance Tests")
    parser.add_argument("-n", "--num-fights", type=int, default=1000, help="Fights per test case (default: 1000)")
    parser.add_argument("-a", "--section-a", action="store_true", help="Run only Section A (Style Balance)")
    parser.add_argument("-b", "--section-b", action="store_true", help="Run only Section B (Mechanics)")
    parser.add_argument("-d", "--detailed", action="store_true", help="Print detailed results for each test")
    parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output during tests")
    parser.add_argument("-s", "--seed", type=int, default=42, help="Random seed (default: 42, use -1 for random)")
    
    args = parser.parse_args()
    
    # Set random seed
    if args.seed >= 0:
        random.seed(args.seed)
        print(f"Random seed: {args.seed}")
    else:
        print("Using random seed")
    
    # Determine which sections to run
    run_a = True
    run_b = True
    if args.section_a and not args.section_b:
        run_b = False
    elif args.section_b and not args.section_a:
        run_a = False
    
    print(f"\n{'='*80}")
    print(" CAGE DYNASTY - FIGHT SIMULATION BALANCE & MECHANICS TEST SUITE")
    print(f"{'='*80}")
    print(f" Fights per test: {args.num_fights}")
    print(f" Sections: {'A' if run_a else ''}{' + ' if run_a and run_b else ''}{'B' if run_b else ''}")
    total_tests = (42 if run_a else 0) + (25 if run_b else 0)
    print(f" Total test cases: {total_tests}")
    print(f" Total fights: {total_tests * args.num_fights:,}")
    print(f"{'='*80}\n")
    
    run_all_tests(
        verbose=not args.quiet,
        num_fights=args.num_fights,
        run_a=run_a,
        run_b=run_b,
        detailed=args.detailed
    )
