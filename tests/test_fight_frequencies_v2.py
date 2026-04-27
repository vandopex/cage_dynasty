#!/usr/bin/env python3
"""
CAGE DYNASTY - COMPREHENSIVE FIGHT FREQUENCY & STATISTICS TEST
==============================================================

Tests fight engine balance by running large sample sizes and measuring:
1. Finish method distributions (KO/TKO/Sub/Decision)
2. Style-appropriate outcomes (strikers get KOs, BJJ gets subs)
3. Action frequencies (TD rate, sub attempts, striking volume, control time)
4. Round count effects (3-round vs 5-round decision rates)
5. Skill gap impact on outcomes

UFC Reference Ranges:
- KO/TKO Rate: 35-40%
- Submission Rate: 10-15%
- Decision Rate: 45-55%
- Draw Rate: < 1%
- Avg Takedown Success: ~40-45%
- Avg Sig Strikes/Min: ~4-5
"""

import sys
import os
import argparse
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# LOCAL FIGHTING STYLE ENUM (matches core.types.FightingStyle)
# ============================================================================

class FightingStyle(Enum):
    """Local enum matching core.types.FightingStyle exactly"""
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
# AGGREGATE STATISTICS TRACKER
# ============================================================================

@dataclass
class FightAggregateStats:
    """Aggregates statistics across many fights"""
    test_name: str
    description: str = ""
    
    # Fight counts
    total_fights: int = 0
    fighter1_wins: int = 0
    fighter2_wins: int = 0
    draws: int = 0
    
    # Finish methods
    ko_finishes: int = 0
    tko_finishes: int = 0
    sub_finishes: int = 0
    decisions: int = 0
    
    # By winner (for checking style-appropriate finishes)
    f1_ko_wins: int = 0
    f1_tko_wins: int = 0
    f1_sub_wins: int = 0
    f1_dec_wins: int = 0
    f2_ko_wins: int = 0
    f2_tko_wins: int = 0
    f2_sub_wins: int = 0
    f2_dec_wins: int = 0
    
    # Round tracking
    r1_finishes: int = 0
    r2_finishes: int = 0
    r3_finishes: int = 0
    r4_finishes: int = 0
    r5_finishes: int = 0
    
    # Aggregate action stats
    f1_strikes_landed: int = 0
    f1_strikes_attempted: int = 0
    f2_strikes_landed: int = 0
    f2_strikes_attempted: int = 0
    
    f1_td_landed: int = 0
    f1_td_attempted: int = 0
    f2_td_landed: int = 0
    f2_td_attempted: int = 0
    
    f1_sub_attempts: int = 0
    f2_sub_attempts: int = 0
    
    f1_knockdowns: int = 0
    f2_knockdowns: int = 0
    
    f1_control_time: float = 0.0
    f2_control_time: float = 0.0
    
    total_rounds_fought: int = 0
    
    # Fighter info
    f1_style: str = ""
    f2_style: str = ""
    f1_overall: int = 0
    f2_overall: int = 0
    scheduled_rounds: int = 3
    
    def add_fight(self, result, f1_name: str, f2_name: str):
        """Add a fight result to the aggregate"""
        self.total_fights += 1
        
        # Determine winner
        is_f1_win = result.winner_name == f1_name
        is_f2_win = result.winner_name == f2_name
        is_draw = result.method == "Draw"
        
        if is_draw:
            self.draws += 1
        elif is_f1_win:
            self.fighter1_wins += 1
        elif is_f2_win:
            self.fighter2_wins += 1
        
        # Parse finish method
        method = result.method.lower()
        is_ko = "ko" in method and "tko" not in method
        is_tko = "tko" in method
        is_sub = "submission" in method or "tap" in method
        is_dec = "decision" in method
        
        if is_ko:
            self.ko_finishes += 1
            if is_f1_win:
                self.f1_ko_wins += 1
            elif is_f2_win:
                self.f2_ko_wins += 1
        elif is_tko:
            self.tko_finishes += 1
            if is_f1_win:
                self.f1_tko_wins += 1
            elif is_f2_win:
                self.f2_tko_wins += 1
        elif is_sub:
            self.sub_finishes += 1
            if is_f1_win:
                self.f1_sub_wins += 1
            elif is_f2_win:
                self.f2_sub_wins += 1
        elif is_dec:
            self.decisions += 1
            if is_f1_win:
                self.f1_dec_wins += 1
            elif is_f2_win:
                self.f2_dec_wins += 1
        
        # Track finish round
        if result.finish_round:
            if result.finish_round == 1:
                self.r1_finishes += 1
            elif result.finish_round == 2:
                self.r2_finishes += 1
            elif result.finish_round == 3:
                self.r3_finishes += 1
            elif result.finish_round == 4:
                self.r4_finishes += 1
            elif result.finish_round == 5:
                self.r5_finishes += 1
        
        # Aggregate round stats
        rounds_in_fight = result.finish_round if result.finish_round else self.scheduled_rounds
        self.total_rounds_fought += rounds_in_fight
        
        # Extract per-round stats
        for i, round_stats in enumerate(result.fighter1_stats):
            self.f1_strikes_landed += round_stats.get("sig_strikes_landed", 0)
            self.f1_strikes_attempted += round_stats.get("sig_strikes_att", 0)
            self.f1_td_landed += round_stats.get("td_landed", 0)
            self.f1_td_attempted += round_stats.get("td_att", 0)
            self.f1_sub_attempts += round_stats.get("sub_att", 0)
            self.f1_knockdowns += round_stats.get("knockdowns", 0)
            self.f1_control_time += round_stats.get("control_time", 0.0)
        
        for i, round_stats in enumerate(result.fighter2_stats):
            self.f2_strikes_landed += round_stats.get("sig_strikes_landed", 0)
            self.f2_strikes_attempted += round_stats.get("sig_strikes_att", 0)
            self.f2_td_landed += round_stats.get("td_landed", 0)
            self.f2_td_attempted += round_stats.get("td_att", 0)
            self.f2_sub_attempts += round_stats.get("sub_att", 0)
            self.f2_knockdowns += round_stats.get("knockdowns", 0)
            self.f2_control_time += round_stats.get("control_time", 0.0)
    
    # ========== Computed Properties ==========
    
    @property
    def f1_win_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.fighter1_wins / self.total_fights * 100
    
    @property
    def f2_win_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.fighter2_wins / self.total_fights * 100
    
    @property
    def ko_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.ko_finishes / self.total_fights * 100
    
    @property
    def tko_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.tko_finishes / self.total_fights * 100
    
    @property
    def ko_tko_rate(self) -> float:
        return self.ko_rate + self.tko_rate
    
    @property
    def sub_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.sub_finishes / self.total_fights * 100
    
    @property
    def decision_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.decisions / self.total_fights * 100
    
    @property
    def finish_rate(self) -> float:
        return 100 - self.decision_rate - (self.draws / max(1, self.total_fights) * 100)
    
    @property
    def draw_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.draws / self.total_fights * 100
    
    @property
    def f1_td_success_rate(self) -> float:
        if self.f1_td_attempted == 0:
            return 0.0
        return self.f1_td_landed / self.f1_td_attempted * 100
    
    @property
    def f2_td_success_rate(self) -> float:
        if self.f2_td_attempted == 0:
            return 0.0
        return self.f2_td_landed / self.f2_td_attempted * 100
    
    @property
    def f1_striking_accuracy(self) -> float:
        if self.f1_strikes_attempted == 0:
            return 0.0
        return self.f1_strikes_landed / self.f1_strikes_attempted * 100
    
    @property
    def f2_striking_accuracy(self) -> float:
        if self.f2_strikes_attempted == 0:
            return 0.0
        return self.f2_strikes_landed / self.f2_strikes_attempted * 100
    
    @property
    def f1_strikes_per_round(self) -> float:
        if self.total_rounds_fought == 0:
            return 0.0
        return self.f1_strikes_landed / self.total_rounds_fought
    
    @property
    def f2_strikes_per_round(self) -> float:
        if self.total_rounds_fought == 0:
            return 0.0
        return self.f2_strikes_landed / self.total_rounds_fought
    
    @property
    def f1_control_per_round(self) -> float:
        if self.total_rounds_fought == 0:
            return 0.0
        return self.f1_control_time / self.total_rounds_fought
    
    @property
    def f2_control_per_round(self) -> float:
        if self.total_rounds_fought == 0:
            return 0.0
        return self.f2_control_time / self.total_rounds_fought
    
    @property
    def f1_knockdowns_per_fight(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.f1_knockdowns / self.total_fights
    
    @property
    def f2_knockdowns_per_fight(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.f2_knockdowns / self.total_fights


# ============================================================================
# TEST CASE DEFINITIONS
# ============================================================================

TEST_CASES = [
    # ==================== SECTION 1: BASELINE TESTS (Equal Skill) ====================
    {
        "name": "T01_Balanced_v_Balanced_3Rd",
        "description": "Baseline: Two balanced fighters, 3 rounds",
        "f1_style": FightingStyle.BALANCED,
        "f2_style": FightingStyle.BALANCED,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T02_Balanced_v_Balanced_5Rd",
        "description": "Baseline: Two balanced fighters, 5 rounds (title fight)",
        "f1_style": FightingStyle.BALANCED,
        "f2_style": FightingStyle.BALANCED,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 5,
    },
    
    # ==================== SECTION 2: STYLE MATCHUPS (Equal Overall) ====================
    {
        "name": "T03_Striker_v_Striker_3Rd",
        "description": "Two strikers - expect high KO/TKO rate",
        "f1_style": FightingStyle.STRIKER,
        "f2_style": FightingStyle.STRIKER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T04_Wrestler_v_Wrestler_3Rd",
        "description": "Two wrestlers - expect high TD activity, decisions",
        "f1_style": FightingStyle.WRESTLER,
        "f2_style": FightingStyle.WRESTLER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T05_BJJ_v_BJJ_3Rd",
        "description": "Two BJJ fighters - expect high sub attempts/finishes",
        "f1_style": FightingStyle.BJJ_SPECIALIST,
        "f2_style": FightingStyle.BJJ_SPECIALIST,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T06_Striker_v_Wrestler_3Rd",
        "description": "Classic striker vs wrestler - key style clash",
        "f1_style": FightingStyle.STRIKER,
        "f2_style": FightingStyle.WRESTLER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T07_Striker_v_BJJ_3Rd",
        "description": "Striker vs BJJ - KO threat vs sub threat",
        "f1_style": FightingStyle.STRIKER,
        "f2_style": FightingStyle.BJJ_SPECIALIST,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T08_Wrestler_v_BJJ_3Rd",
        "description": "Wrestler vs BJJ - grappling styles clash",
        "f1_style": FightingStyle.WRESTLER,
        "f2_style": FightingStyle.BJJ_SPECIALIST,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T09_GnP_v_BJJ_3Rd",
        "description": "Ground & Pound vs BJJ - top control vs subs",
        "f1_style": FightingStyle.GROUND_AND_POUND,
        "f2_style": FightingStyle.BJJ_SPECIALIST,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T10_MuayThai_v_Wrestler_3Rd",
        "description": "Muay Thai vs Wrestler - clinch battle",
        "f1_style": FightingStyle.MUAY_THAI,
        "f2_style": FightingStyle.WRESTLER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    
    # ==================== SECTION 3: SKILL GAP TESTS ====================
    {
        "name": "T11_Elite90_v_Average70_3Rd",
        "description": "20-point skill gap - elite should dominate",
        "f1_style": FightingStyle.BALANCED,
        "f2_style": FightingStyle.BALANCED,
        "f1_overall": 90,
        "f2_overall": 70,
        "rounds": 3,
    },
    {
        "name": "T12_Elite95_v_Journeyman65_3Rd",
        "description": "30-point skill gap - elite should dominate heavily",
        "f1_style": FightingStyle.BALANCED,
        "f2_style": FightingStyle.BALANCED,
        "f1_overall": 95,
        "f2_overall": 65,
        "rounds": 3,
    },
    {
        "name": "T13_Can50_v_Can50_3Rd",
        "description": "Low-skill fighters - sloppy, more variability",
        "f1_style": FightingStyle.BALANCED,
        "f2_style": FightingStyle.BALANCED,
        "f1_overall": 50,
        "f2_overall": 50,
        "rounds": 3,
    },
    
    # ==================== SECTION 4: STYLE ADVANTAGE TESTS ====================
    {
        "name": "T14_Striker90_v_Wrestler80_3Rd",
        "description": "Better striker vs lesser wrestler",
        "f1_style": FightingStyle.STRIKER,
        "f2_style": FightingStyle.WRESTLER,
        "f1_overall": 90,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T15_Wrestler90_v_Striker80_3Rd",
        "description": "Better wrestler vs lesser striker",
        "f1_style": FightingStyle.WRESTLER,
        "f2_style": FightingStyle.STRIKER,
        "f1_overall": 90,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T16_BJJ90_v_Striker80_3Rd",
        "description": "Better BJJ vs lesser striker - sub specialist advantage",
        "f1_style": FightingStyle.BJJ_SPECIALIST,
        "f2_style": FightingStyle.STRIKER,
        "f1_overall": 90,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T17_Striker80_v_BJJ90_3Rd",
        "description": "Lesser striker vs better BJJ",
        "f1_style": FightingStyle.STRIKER,
        "f2_style": FightingStyle.BJJ_SPECIALIST,
        "f1_overall": 80,
        "f2_overall": 90,
        "rounds": 3,
    },
    
    # ==================== SECTION 5: 5-ROUND COMPARISON ====================
    {
        "name": "T18_Striker_v_Wrestler_5Rd",
        "description": "Striker vs Wrestler in 5 rounds - more time to work",
        "f1_style": FightingStyle.STRIKER,
        "f2_style": FightingStyle.WRESTLER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 5,
    },
    {
        "name": "T19_BJJ_v_Wrestler_5Rd",
        "description": "BJJ vs Wrestler in 5 rounds",
        "f1_style": FightingStyle.BJJ_SPECIALIST,
        "f2_style": FightingStyle.WRESTLER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 5,
    },
    {
        "name": "T20_Striker_v_Striker_5Rd",
        "description": "Two strikers in 5 rounds - expect more finishes",
        "f1_style": FightingStyle.STRIKER,
        "f2_style": FightingStyle.STRIKER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 5,
    },
    
    # ==================== SECTION 6: SPECIALIZED STYLE TESTS ====================
    {
        "name": "T21_Pressure_v_Counter_3Rd",
        "description": "Pressure fighter vs counter striker",
        "f1_style": FightingStyle.PRESSURE_FIGHTER,
        "f2_style": FightingStyle.COUNTER_STRIKER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T22_SprawlBrawl_v_Wrestler_3Rd",
        "description": "Sprawl & Brawl vs Wrestler - TDD test",
        "f1_style": FightingStyle.SPRAWL_AND_BRAWL,
        "f2_style": FightingStyle.WRESTLER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T23_Clinch_v_Striker_3Rd",
        "description": "Clinch fighter vs pure striker",
        "f1_style": FightingStyle.CLINCH_FIGHTER,
        "f2_style": FightingStyle.STRIKER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
    {
        "name": "T24_Point_v_Pressure_3Rd",
        "description": "Point fighter vs pressure - technical vs aggressive",
        "f1_style": FightingStyle.POINT_FIGHTER,
        "f2_style": FightingStyle.PRESSURE_FIGHTER,
        "f1_overall": 80,
        "f2_overall": 80,
        "rounds": 3,
    },
]


# ============================================================================
# IMPORT AND RUN FUNCTIONS
# ============================================================================

def get_fight_functions():
    """Import the fight simulation functions"""
    try:
        from simulation.fight_integration import (
            simulate_narrated_fight,
            FighterAttributes,
            NarratedFightResult,
            FightingStyle as ProjectFightingStyle
        )
        
        # Map local enum to project enum
        style_map = {
            FightingStyle.STRIKER: ProjectFightingStyle.STRIKER,
            FightingStyle.WRESTLER: ProjectFightingStyle.WRESTLER,
            FightingStyle.BJJ_SPECIALIST: ProjectFightingStyle.BJJ_SPECIALIST,
            FightingStyle.BALANCED: ProjectFightingStyle.BALANCED,
            FightingStyle.COUNTER_STRIKER: ProjectFightingStyle.COUNTER_STRIKER,
            FightingStyle.PRESSURE_FIGHTER: ProjectFightingStyle.PRESSURE_FIGHTER,
            FightingStyle.POINT_FIGHTER: ProjectFightingStyle.POINT_FIGHTER,
            FightingStyle.MUAY_THAI: ProjectFightingStyle.MUAY_THAI,
            FightingStyle.SPRAWL_AND_BRAWL: ProjectFightingStyle.SPRAWL_AND_BRAWL,
            FightingStyle.GROUND_AND_POUND: ProjectFightingStyle.GROUND_AND_POUND,
            FightingStyle.CLINCH_FIGHTER: ProjectFightingStyle.CLINCH_FIGHTER,
        }
        
        return simulate_narrated_fight, FighterAttributes, style_map
    except ImportError as e:
        print(f"ERROR: Could not import fight simulation modules: {e}")
        print("\nMake sure you're running from the cage_dynasty root directory:")
        print("  cd ~/Desktop/Games/cage_dynasty")
        print("  python3 tests/test_fight_frequencies_v2.py")
        sys.exit(1)


def create_fighter(
    fighter_id: str,
    name: str,
    overall: int,
    style,
    FighterAttributes,
    style_map
):
    """Create a FighterAttributes object with the given overall rating"""
    mapped_style = style_map.get(style, style)
    
    return FighterAttributes(
        fighter_id=fighter_id,
        name=name,
        # Physical (5)
        strength=overall,
        speed=overall,
        cardio=overall,
        chin=overall,
        recovery=overall,
        # Striking (4)
        boxing=overall,
        kicks=overall,
        clinch_striking=overall,
        striking_defense=overall,
        # Grappling (5)
        takedowns=overall,
        takedown_defense=overall,
        top_control=overall,
        submissions=overall,
        guard=overall,
        # Mental (3)
        heart=overall,
        fight_iq=overall,
        composure=overall,
        fighting_style=mapped_style
    )


def run_test_case(
    test_config: Dict,
    num_fights: int,
    simulate_narrated_fight,
    FighterAttributes,
    style_map
) -> FightAggregateStats:
    """Run a single test case and return aggregate stats"""
    
    stats = FightAggregateStats(
        test_name=test_config["name"],
        description=test_config["description"],
        f1_style=test_config["f1_style"].value,
        f2_style=test_config["f2_style"].value,
        f1_overall=test_config["f1_overall"],
        f2_overall=test_config["f2_overall"],
        scheduled_rounds=test_config["rounds"],
    )
    
    f1_name = "Fighter One"
    f2_name = "Fighter Two"
    
    for i in range(num_fights):
        try:
            fighter1 = create_fighter(
                "fighter_1", f1_name,
                test_config["f1_overall"],
                test_config["f1_style"],
                FighterAttributes, style_map
            )
            fighter2 = create_fighter(
                "fighter_2", f2_name,
                test_config["f2_overall"],
                test_config["f2_style"],
                FighterAttributes, style_map
            )
            
            result = simulate_narrated_fight(
                fighter1, fighter2,
                rounds=test_config["rounds"]
            )
            
            stats.add_fight(result, f1_name, f2_name)
            
        except Exception as e:
            print(f"  ERROR in fight {i+1}: {e}")
    
    return stats


# ============================================================================
# REPORTING FUNCTIONS
# ============================================================================

def print_header():
    """Print test suite header"""
    print("=" * 100)
    print(" CAGE DYNASTY - COMPREHENSIVE FIGHT FREQUENCY & STATISTICS TEST")
    print("=" * 100)
    print()
    print(" UFC Reference Ranges:")
    print("   KO/TKO Rate: 35-40%  |  Submission Rate: 10-15%  |  Decision Rate: 45-55%")
    print("   Takedown Success: 40-45%  |  Avg Strikes/Round: ~15-25")
    print("=" * 100)
    print()


def print_summary_table(all_stats: List[FightAggregateStats]):
    """Print summary table of all test results"""
    print()
    print("=" * 120)
    print(" SUMMARY TABLE - FINISH METHODS")
    print("=" * 120)
    print(f"{'Test Name':<35} {'F1 Win%':>8} {'F2 Win%':>8} {'KO%':>6} {'TKO%':>6} {'Sub%':>6} {'Dec%':>6} {'Draw%':>6} {'Finish%':>8}")
    print("-" * 120)
    
    for s in all_stats:
        print(f"{s.test_name:<35} {s.f1_win_rate:>7.1f}% {s.f2_win_rate:>7.1f}% "
              f"{s.ko_rate:>5.1f}% {s.tko_rate:>5.1f}% {s.sub_rate:>5.1f}% "
              f"{s.decision_rate:>5.1f}% {s.draw_rate:>5.1f}% {s.finish_rate:>7.1f}%")
    
    print("-" * 120)


def print_action_stats_table(all_stats: List[FightAggregateStats]):
    """Print action statistics table"""
    print()
    print("=" * 140)
    print(" ACTION STATISTICS (Per Round Averages)")
    print("=" * 140)
    print(f"{'Test Name':<35} {'F1 Str/Rd':>10} {'F2 Str/Rd':>10} {'F1 TD%':>8} {'F2 TD%':>8} "
          f"{'F1 SubAtt':>9} {'F2 SubAtt':>9} {'F1 KD/Ft':>8} {'F2 KD/Ft':>8}")
    print("-" * 140)
    
    for s in all_stats:
        print(f"{s.test_name:<35} {s.f1_strikes_per_round:>9.1f} {s.f2_strikes_per_round:>9.1f} "
              f"{s.f1_td_success_rate:>7.1f}% {s.f2_td_success_rate:>7.1f}% "
              f"{s.f1_sub_attempts:>9} {s.f2_sub_attempts:>9} "
              f"{s.f1_knockdowns_per_fight:>7.2f} {s.f2_knockdowns_per_fight:>7.2f}")
    
    print("-" * 140)


def print_detailed_report(stats: FightAggregateStats):
    """Print detailed report for a single test case"""
    print()
    print(f"{'='*80}")
    print(f" {stats.test_name}")
    print(f" {stats.description}")
    print(f"{'='*80}")
    print()
    print(f" Matchup: {stats.f1_style.upper()} ({stats.f1_overall} OVR) vs "
          f"{stats.f2_style.upper()} ({stats.f2_overall} OVR) | {stats.scheduled_rounds} Rounds")
    print(f" Total Fights: {stats.total_fights} | Total Rounds Fought: {stats.total_rounds_fought}")
    print()
    
    # Win distribution
    print(" WIN DISTRIBUTION:")
    print(f"   Fighter 1 ({stats.f1_style}): {stats.fighter1_wins} wins ({stats.f1_win_rate:.1f}%)")
    print(f"   Fighter 2 ({stats.f2_style}): {stats.fighter2_wins} wins ({stats.f2_win_rate:.1f}%)")
    print(f"   Draws: {stats.draws} ({stats.draw_rate:.1f}%)")
    print()
    
    # Finish method distribution
    print(" FINISH METHOD DISTRIBUTION:")
    print(f"   KO:         {stats.ko_finishes:>5} ({stats.ko_rate:>5.1f}%)")
    print(f"   TKO:        {stats.tko_finishes:>5} ({stats.tko_rate:>5.1f}%)")
    print(f"   KO/TKO:     {stats.ko_finishes + stats.tko_finishes:>5} ({stats.ko_tko_rate:>5.1f}%)")
    print(f"   Submission: {stats.sub_finishes:>5} ({stats.sub_rate:>5.1f}%)")
    print(f"   Decision:   {stats.decisions:>5} ({stats.decision_rate:>5.1f}%)")
    print()
    
    # Finish by round
    print(" FINISHES BY ROUND:")
    print(f"   R1: {stats.r1_finishes} | R2: {stats.r2_finishes} | R3: {stats.r3_finishes}", end="")
    if stats.scheduled_rounds == 5:
        print(f" | R4: {stats.r4_finishes} | R5: {stats.r5_finishes}")
    else:
        print()
    print()
    
    # Win method by fighter
    print(" WINS BY METHOD:")
    print(f"   F1 ({stats.f1_style}): KO={stats.f1_ko_wins} TKO={stats.f1_tko_wins} "
          f"Sub={stats.f1_sub_wins} Dec={stats.f1_dec_wins}")
    print(f"   F2 ({stats.f2_style}): KO={stats.f2_ko_wins} TKO={stats.f2_tko_wins} "
          f"Sub={stats.f2_sub_wins} Dec={stats.f2_dec_wins}")
    print()
    
    # Action stats
    print(" ACTION STATISTICS:")
    print(f"   Strikes Landed:     F1={stats.f1_strikes_landed:>6} | F2={stats.f2_strikes_landed:>6}")
    print(f"   Strikes/Round:      F1={stats.f1_strikes_per_round:>6.1f} | F2={stats.f2_strikes_per_round:>6.1f}")
    print(f"   Striking Accuracy:  F1={stats.f1_striking_accuracy:>5.1f}% | F2={stats.f2_striking_accuracy:>5.1f}%")
    print(f"   Takedowns Landed:   F1={stats.f1_td_landed:>6} | F2={stats.f2_td_landed:>6}")
    print(f"   Takedown Success:   F1={stats.f1_td_success_rate:>5.1f}% | F2={stats.f2_td_success_rate:>5.1f}%")
    print(f"   Sub Attempts:       F1={stats.f1_sub_attempts:>6} | F2={stats.f2_sub_attempts:>6}")
    print(f"   Knockdowns:         F1={stats.f1_knockdowns:>6} | F2={stats.f2_knockdowns:>6}")
    print(f"   Knockdowns/Fight:   F1={stats.f1_knockdowns_per_fight:>6.2f} | F2={stats.f2_knockdowns_per_fight:>6.2f}")
    print(f"   Control Time:       F1={stats.f1_control_time:>6.1f}s | F2={stats.f2_control_time:>6.1f}s")
    print(f"   Control/Round:      F1={stats.f1_control_per_round:>6.1f}s | F2={stats.f2_control_per_round:>6.1f}s")


def analyze_balance_issues(all_stats: List[FightAggregateStats]):
    """Analyze and report potential balance issues"""
    print()
    print("=" * 100)
    print(" BALANCE ANALYSIS")
    print("=" * 100)
    print()
    
    issues = []
    observations = []
    
    for s in all_stats:
        # Check for expected ranges
        
        # Equal skill should be ~50/50
        if s.f1_overall == s.f2_overall:
            if s.f1_win_rate < 40 or s.f1_win_rate > 60:
                issues.append(f"⚠️  {s.test_name}: Equal skill win rate {s.f1_win_rate:.1f}% deviates from 50/50")
        
        # Skill gaps should show appropriate advantage
        skill_gap = s.f1_overall - s.f2_overall
        if skill_gap >= 20:
            if s.f1_win_rate < 70:
                issues.append(f"⚠️  {s.test_name}: 20+ point gap only producing {s.f1_win_rate:.1f}% win rate")
        elif skill_gap >= 10:
            if s.f1_win_rate < 55:
                issues.append(f"⚠️  {s.test_name}: 10+ point gap only producing {s.f1_win_rate:.1f}% win rate")
        
        # Striker vs Striker should have high KO/TKO
        if "Striker_v_Striker" in s.test_name:
            if s.ko_tko_rate < 40:
                issues.append(f"⚠️  {s.test_name}: Striker mirror has low KO/TKO rate ({s.ko_tko_rate:.1f}%)")
            else:
                observations.append(f"✓  {s.test_name}: Good KO/TKO rate ({s.ko_tko_rate:.1f}%)")
        
        # BJJ vs BJJ should have elevated sub rate
        if "BJJ_v_BJJ" in s.test_name:
            if s.sub_rate < 15:
                issues.append(f"⚠️  {s.test_name}: BJJ mirror has low sub rate ({s.sub_rate:.1f}%)")
            else:
                observations.append(f"✓  {s.test_name}: Good sub rate for BJJ mirror ({s.sub_rate:.1f}%)")
        
        # Wrestler should have more TDs than striker in Striker vs Wrestler
        if "Striker_v_Wrestler" in s.test_name:
            if s.f2_td_landed < s.f1_td_landed:
                issues.append(f"⚠️  {s.test_name}: Striker has more TDs than Wrestler")
            else:
                observations.append(f"✓  {s.test_name}: Wrestler has more TDs ({s.f2_td_landed} vs {s.f1_td_landed})")
        
        # BJJ should have more sub attempts
        if "BJJ" in s.f1_style.upper() and "BJJ" not in s.f2_style.upper():
            if s.f1_sub_attempts < s.f2_sub_attempts:
                issues.append(f"⚠️  {s.test_name}: Non-BJJ fighter has more sub attempts")
        
        # 5-round fights should have similar or higher finish rate than 3-round
        # (More time = more chances to finish, though also more decisions possible)
        
        # Check for unrealistic decision rates in striking battles
        if "Striker" in s.test_name and s.decision_rate > 60:
            issues.append(f"⚠️  {s.test_name}: Very high decision rate ({s.decision_rate:.1f}%) for striking matchup")
    
    # Print issues
    if issues:
        print(" POTENTIAL ISSUES:")
        for issue in issues:
            print(f"   {issue}")
        print()
    else:
        print(" No major balance issues detected!")
        print()
    
    # Print observations
    if observations:
        print(" POSITIVE OBSERVATIONS:")
        for obs in observations:
            print(f"   {obs}")
        print()
    
    # Overall stats
    total_fights = sum(s.total_fights for s in all_stats)
    total_ko = sum(s.ko_finishes for s in all_stats)
    total_tko = sum(s.tko_finishes for s in all_stats)
    total_sub = sum(s.sub_finishes for s in all_stats)
    total_dec = sum(s.decisions for s in all_stats)
    
    print(" OVERALL STATISTICS ACROSS ALL TESTS:")
    print(f"   Total Fights: {total_fights}")
    print(f"   KO Rate:      {total_ko/total_fights*100:.1f}%")
    print(f"   TKO Rate:     {total_tko/total_fights*100:.1f}%")
    print(f"   KO/TKO Rate:  {(total_ko+total_tko)/total_fights*100:.1f}%")
    print(f"   Sub Rate:     {total_sub/total_fights*100:.1f}%")
    print(f"   Decision Rate:{total_dec/total_fights*100:.1f}%")
    print()
    
    # UFC comparison
    print(" UFC COMPARISON:")
    ko_tko_pct = (total_ko + total_tko) / total_fights * 100
    sub_pct = total_sub / total_fights * 100
    dec_pct = total_dec / total_fights * 100
    
    if 35 <= ko_tko_pct <= 45:
        print(f"   ✓ KO/TKO Rate ({ko_tko_pct:.1f}%) within UFC range (35-40%)")
    elif ko_tko_pct < 35:
        print(f"   ⚠️  KO/TKO Rate ({ko_tko_pct:.1f}%) below UFC range (35-40%)")
    else:
        print(f"   ⚠️  KO/TKO Rate ({ko_tko_pct:.1f}%) above UFC range (35-40%)")
    
    if 8 <= sub_pct <= 18:
        print(f"   ✓ Submission Rate ({sub_pct:.1f}%) within UFC range (10-15%)")
    elif sub_pct < 8:
        print(f"   ⚠️  Submission Rate ({sub_pct:.1f}%) below UFC range (10-15%)")
    else:
        print(f"   ⚠️  Submission Rate ({sub_pct:.1f}%) above UFC range (10-15%)")
    
    if 40 <= dec_pct <= 60:
        print(f"   ✓ Decision Rate ({dec_pct:.1f}%) within UFC range (45-55%)")
    elif dec_pct < 40:
        print(f"   ⚠️  Decision Rate ({dec_pct:.1f}%) below UFC range (45-55%)")
    else:
        print(f"   ⚠️  Decision Rate ({dec_pct:.1f}%) above UFC range (45-55%)")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Fight Frequency Statistics Test")
    parser.add_argument("-n", "--num-fights", type=int, default=1000,
                        help="Number of fights per test case (default: 1000)")
    parser.add_argument("-s", "--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print detailed report for each test")
    parser.add_argument("-t", "--test", type=str, default=None,
                        help="Run specific test by name (e.g., T03_Striker_v_Striker_3Rd)")
    args = parser.parse_args()
    
    # Set random seed
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Random seed: {args.seed}")
    
    # Import fight functions
    simulate_narrated_fight, FighterAttributes, style_map = get_fight_functions()
    
    # Filter test cases if specific test requested
    if args.test:
        test_cases = [tc for tc in TEST_CASES if args.test.lower() in tc["name"].lower()]
        if not test_cases:
            print(f"No test found matching '{args.test}'")
            print("Available tests:")
            for tc in TEST_CASES:
                print(f"  {tc['name']}")
            sys.exit(1)
    else:
        test_cases = TEST_CASES
    
    # Print header
    print_header()
    print(f" Running {len(test_cases)} test cases with {args.num_fights} fights each")
    print(f" Total fights: {len(test_cases) * args.num_fights:,}")
    print()
    
    # Run all tests
    all_stats = []
    for i, tc in enumerate(test_cases):
        print(f"[{i+1}/{len(test_cases)}] {tc['name']}...")
        print(f"        {tc['description']}")
        
        stats = run_test_case(tc, args.num_fights, simulate_narrated_fight, FighterAttributes, style_map)
        all_stats.append(stats)
        
        print(f"        -> F1 Win: {stats.f1_win_rate:.1f}% | KO/TKO: {stats.ko_tko_rate:.1f}% | "
              f"Sub: {stats.sub_rate:.1f}% | Dec: {stats.decision_rate:.1f}%")
        print()
    
    # Print summary tables
    print_summary_table(all_stats)
    print_action_stats_table(all_stats)
    
    # Print detailed reports if verbose
    if args.verbose:
        for stats in all_stats:
            print_detailed_report(stats)
    
    # Analyze balance
    analyze_balance_issues(all_stats)


if __name__ == "__main__":
    main()
