#!/usr/bin/env python3
"""
Fight Engine Balance Validation Test Suite

Tests the fight engine for realistic outcomes across:
- Rating advantages (better fighters should win more)
- Style matchups (all styles should be competitive at equal skill)
- Finish rates (KO, SUB, DEC distribution)
- Specialist advantages (strikers get KOs, grapplers get subs)
- Upset potential (underdogs occasionally win)
- Mirror matchups (should be ~50/50)

Fighter Styles Tested:
- Striker (Boxing focused)
- Kickboxer (Kicks + Boxing)
- Muay Thai (Clinch striking + Kicks)
- Wrestler (Takedowns + Control)
- BJJ (Submissions from guard)
- Sambo (Wrestling + Submissions combined)
- Balanced MMA (All-around)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.fight_engine import (
    FighterAttributes, 
    FightConfig, 
    simulate_fight,
    detect_fighter_style
)
from collections import defaultdict


# ============================================================================
# FIGHTER TEMPLATES - Comprehensive Style Archetypes
# ============================================================================

def create_elite_striker() -> FighterAttributes:
    """Elite pure boxer/striker - thinks they can KO anyone"""
    return FighterAttributes(
        fighter_id="elite_striker",
        name="Elite Striker",
        boxing=92, kicks=75, clinch_striking=70, striking_defense=88,
        wrestling=55, bjj=50, takedown_defense=72,
        strength=78, speed=88, cardio=80, chin=82,
        heart=80, fight_iq=82, composure=85
    )  # OVR ~77

def create_elite_kickboxer() -> FighterAttributes:
    """Elite kickboxer - high kicks, head kick KO threat"""
    return FighterAttributes(
        fighter_id="elite_kickboxer",
        name="Elite Kickboxer",
        boxing=80, kicks=92, clinch_striking=65, striking_defense=85,
        wrestling=50, bjj=48, takedown_defense=70,
        strength=75, speed=90, cardio=82, chin=78,
        heart=78, fight_iq=80, composure=82
    )  # OVR ~75

def create_elite_muay_thai() -> FighterAttributes:
    """Elite Muay Thai - dominates in clinch with knees/elbows"""
    return FighterAttributes(
        fighter_id="elite_muay_thai",
        name="Elite Muay Thai",
        boxing=78, kicks=88, clinch_striking=95, striking_defense=82,
        wrestling=62, bjj=55, takedown_defense=75,
        strength=80, speed=82, cardio=85, chin=80,
        heart=85, fight_iq=78, composure=80
    )  # OVR ~78

def create_elite_wrestler() -> FighterAttributes:
    """Elite wrestler - smothering control, ground and pound"""
    return FighterAttributes(
        fighter_id="elite_wrestler",
        name="Elite Wrestler",
        boxing=70, kicks=55, clinch_striking=68, striking_defense=72,
        wrestling=95, bjj=75, takedown_defense=92,
        strength=90, speed=80, cardio=88, chin=85,
        heart=88, fight_iq=80, composure=85
    )  # OVR ~80

def create_elite_bjj() -> FighterAttributes:
    """Elite BJJ specialist - dangerous from guard, submission hunter"""
    return FighterAttributes(
        fighter_id="elite_bjj",
        name="Elite BJJ",
        boxing=72, kicks=65, clinch_striking=60, striking_defense=70,
        wrestling=68, bjj=95, takedown_defense=70,
        strength=75, speed=82, cardio=80, chin=75,
        heart=85, fight_iq=88, composure=82
    )  # OVR ~77

def create_elite_sambo() -> FighterAttributes:
    """Elite Sambo - wrestling + submissions combined (Khabib style)"""
    return FighterAttributes(
        fighter_id="elite_sambo",
        name="Elite Sambo",
        boxing=75, kicks=65, clinch_striking=78, striking_defense=75,
        wrestling=92, bjj=85, takedown_defense=88,
        strength=88, speed=78, cardio=90, chin=82,
        heart=90, fight_iq=85, composure=88
    )  # OVR ~82

def create_elite_mma() -> FighterAttributes:
    """Elite complete MMA fighter - well rounded everywhere"""
    return FighterAttributes(
        fighter_id="elite_mma",
        name="Elite MMA",
        boxing=85, kicks=82, clinch_striking=80, striking_defense=85,
        wrestling=82, bjj=80, takedown_defense=85,
        strength=82, speed=85, cardio=85, chin=82,
        heart=85, fight_iq=88, composure=88
    )  # OVR ~83

def create_good_striker() -> FighterAttributes:
    """Good striker - solid boxing, vulnerable on ground"""
    return FighterAttributes(
        fighter_id="good_striker",
        name="Good Striker",
        boxing=82, kicks=68, clinch_striking=65, striking_defense=78,
        wrestling=50, bjj=45, takedown_defense=62,
        strength=72, speed=78, cardio=72, chin=75,
        heart=72, fight_iq=70, composure=72
    )  # OVR ~68

def create_good_wrestler() -> FighterAttributes:
    """Good wrestler - solid takedowns and control"""
    return FighterAttributes(
        fighter_id="good_wrestler",
        name="Good Wrestler",
        boxing=62, kicks=50, clinch_striking=60, striking_defense=65,
        wrestling=85, bjj=65, takedown_defense=82,
        strength=80, speed=72, cardio=78, chin=78,
        heart=80, fight_iq=72, composure=78
    )  # OVR ~72

def create_good_bjj() -> FighterAttributes:
    """Good BJJ - solid submissions, weaker wrestling"""
    return FighterAttributes(
        fighter_id="good_bjj",
        name="Good BJJ",
        boxing=65, kicks=60, clinch_striking=55, striking_defense=62,
        wrestling=58, bjj=85, takedown_defense=60,
        strength=68, speed=72, cardio=72, chin=68,
        heart=78, fight_iq=78, composure=75
    )  # OVR ~68

def create_good_sambo() -> FighterAttributes:
    """Good Sambo - wrestling + BJJ combined"""
    return FighterAttributes(
        fighter_id="good_sambo",
        name="Good Sambo",
        boxing=65, kicks=58, clinch_striking=70, striking_defense=68,
        wrestling=82, bjj=78, takedown_defense=80,
        strength=78, speed=70, cardio=80, chin=75,
        heart=82, fight_iq=75, composure=78
    )  # OVR ~74

def create_good_muay_thai() -> FighterAttributes:
    """Good Muay Thai - clinch specialist"""
    return FighterAttributes(
        fighter_id="good_muay_thai",
        name="Good Muay Thai",
        boxing=70, kicks=80, clinch_striking=85, striking_defense=72,
        wrestling=55, bjj=50, takedown_defense=65,
        strength=72, speed=75, cardio=78, chin=72,
        heart=78, fight_iq=70, composure=72
    )  # OVR ~70

def create_good_mma() -> FighterAttributes:
    """Good balanced fighter"""
    return FighterAttributes(
        fighter_id="good_mma",
        name="Good MMA",
        boxing=75, kicks=72, clinch_striking=70, striking_defense=75,
        wrestling=72, bjj=70, takedown_defense=75,
        strength=72, speed=75, cardio=75, chin=72,
        heart=75, fight_iq=75, composure=75
    )  # OVR ~73

def create_avg_striker() -> FighterAttributes:
    """Average striker"""
    return FighterAttributes(
        fighter_id="avg_striker",
        name="Avg Striker",
        boxing=72, kicks=60, clinch_striking=58, striking_defense=68,
        wrestling=45, bjj=40, takedown_defense=55,
        strength=65, speed=70, cardio=65, chin=68,
        heart=65, fight_iq=62, composure=65
    )  # OVR ~61

def create_avg_wrestler() -> FighterAttributes:
    """Average wrestler"""
    return FighterAttributes(
        fighter_id="avg_wrestler",
        name="Avg Wrestler",
        boxing=55, kicks=48, clinch_striking=55, striking_defense=58,
        wrestling=75, bjj=58, takedown_defense=72,
        strength=72, speed=65, cardio=70, chin=70,
        heart=72, fight_iq=65, composure=68
    )  # OVR ~64

def create_avg_bjj() -> FighterAttributes:
    """Average BJJ specialist"""
    return FighterAttributes(
        fighter_id="avg_bjj",
        name="Avg BJJ",
        boxing=58, kicks=52, clinch_striking=50, striking_defense=55,
        wrestling=52, bjj=75, takedown_defense=55,
        strength=62, speed=65, cardio=65, chin=62,
        heart=70, fight_iq=70, composure=68
    )  # OVR ~61

def create_avg_mma() -> FighterAttributes:
    """Average balanced fighter"""
    return FighterAttributes(
        fighter_id="avg_mma",
        name="Avg MMA",
        boxing=68, kicks=65, clinch_striking=62, striking_defense=68,
        wrestling=65, bjj=62, takedown_defense=68,
        strength=65, speed=68, cardio=68, chin=65,
        heart=68, fight_iq=68, composure=68
    )  # OVR ~66

def create_below_avg() -> FighterAttributes:
    """Below average fighter - raw and developing"""
    return FighterAttributes(
        fighter_id="below_avg",
        name="Below Avg",
        boxing=58, kicks=52, clinch_striking=50, striking_defense=55,
        wrestling=55, bjj=52, takedown_defense=55,
        strength=58, speed=60, cardio=58, chin=58,
        heart=60, fight_iq=55, composure=55
    )  # OVR ~56

def create_prospect() -> FighterAttributes:
    """Raw prospect - limited skills"""
    return FighterAttributes(
        fighter_id="prospect",
        name="Prospect",
        boxing=52, kicks=48, clinch_striking=45, striking_defense=50,
        wrestling=50, bjj=48, takedown_defense=50,
        strength=55, speed=58, cardio=55, chin=55,
        heart=55, fight_iq=50, composure=50
    )  # OVR ~51


def calculate_overall(f: FighterAttributes) -> int:
    """Calculate overall rating for a fighter."""
    striking = (f.boxing * 2 + f.kicks + f.clinch_striking) // 4
    grappling = (f.wrestling + f.bjj * 2 + f.takedown_defense) // 4
    return (striking + grappling + f.chin + f.cardio + f.heart) // 5


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def run_matchup(f1: FighterAttributes, f2: FighterAttributes, num_fights: int = 200) -> dict:
    """Run multiple fights and collect statistics."""
    results = {
        "f1_wins": 0, "f2_wins": 0, "draws": 0,
        "f1_ko": 0, "f1_sub": 0, "f1_dec": 0,
        "f2_ko": 0, "f2_sub": 0, "f2_dec": 0,
        "finish_rounds": []
    }
    
    for _ in range(num_fights):
        result = simulate_fight(f1, f2)
        
        if result.winner_id is None:
            results["draws"] += 1
        elif result.winner_id == f1.fighter_id:
            results["f1_wins"] += 1
            method = result.method.lower()
            if "ko" in method or "tko" in method:
                results["f1_ko"] += 1
            elif "sub" in method:
                results["f1_sub"] += 1
            else:
                results["f1_dec"] += 1
            if result.finish_round:
                results["finish_rounds"].append(result.finish_round)
        else:
            results["f2_wins"] += 1
            method = result.method.lower()
            if "ko" in method or "tko" in method:
                results["f2_ko"] += 1
            elif "sub" in method:
                results["f2_sub"] += 1
            else:
                results["f2_dec"] += 1
            if result.finish_round:
                results["finish_rounds"].append(result.finish_round)
    
    return results


def print_matchup_results(f1: FighterAttributes, f2: FighterAttributes, results: dict, num_fights: int):
    """Print formatted matchup results."""
    f1_ovr = calculate_overall(f1)
    f2_ovr = calculate_overall(f2)
    f1_style = detect_fighter_style(f1)
    f2_style = detect_fighter_style(f2)
    
    print("\n" + "=" * 70)
    print(f"{f1.name} (OVR {f1_ovr}) vs {f2.name} (OVR {f2_ovr})")
    print(f"Style: {f1_style.title()} vs {f2_style.title()}")
    print(f"Rating Diff: {abs(f1_ovr - f2_ovr)} points")
    print("=" * 70)
    
    f1_pct = results["f1_wins"] / num_fights * 100
    f2_pct = results["f2_wins"] / num_fights * 100
    
    print(f"\nResults over {num_fights} fights:")
    print(f"  {f1.name}: {results['f1_wins']} wins ({f1_pct:.1f}%)")
    print(f"    - KO/TKO: {results['f1_ko']}")
    print(f"    - SUB: {results['f1_sub']}")
    print(f"    - DEC: {results['f1_dec']}")
    print(f"  {f2.name}: {results['f2_wins']} wins ({f2_pct:.1f}%)")
    print(f"    - KO/TKO: {results['f2_ko']}")
    print(f"    - SUB: {results['f2_sub']}")
    print(f"    - DEC: {results['f2_dec']}")
    if results["draws"] > 0:
        print(f"  Draws: {results['draws']}")
    
    total_finishes = results["f1_ko"] + results["f1_sub"] + results["f2_ko"] + results["f2_sub"]
    finish_rate = total_finishes / num_fights * 100
    print(f"\n  Finish Rate: {finish_rate:.1f}%")
    if results["finish_rounds"]:
        avg_round = sum(results["finish_rounds"]) / len(results["finish_rounds"])
        print(f"  Avg Finish Round: {avg_round:.1f}")
    
    return f1_pct, f2_pct


def test_rating_advantage():
    """Test that higher rated fighters win more often."""
    print("\n" + "=" * 70)
    print("TEST 1: RATING ADVANTAGE VALIDATION")
    print("Higher rated fighters should win more often")
    print("=" * 70)
    
    matchups = [
        (create_elite_mma(), create_good_mma(), 66),
        (create_good_mma(), create_avg_mma(), 67),
        (create_avg_mma(), create_below_avg(), 68),
        (create_elite_mma(), create_avg_mma(), 78),
        (create_elite_mma(), create_prospect(), 95),
    ]
    
    all_passed = True
    for f1, f2, expected_min in matchups:
        results = run_matchup(f1, f2)
        f1_pct, f2_pct = print_matchup_results(f1, f2, results, 200)
        
        if f1_pct >= expected_min:
            print(f"  ✅ PASS: Higher rated won {f1_pct:.1f}% (expected ~{expected_min}%+)")
        else:
            print(f"  ⚠️ FAIL: Higher rated won only {f1_pct:.1f}% (expected ~{expected_min}%+)")
            all_passed = False
    
    return all_passed


def test_style_matchups():
    """Test that different styles create competitive matchups."""
    print("\n" + "=" * 70)
    print("TEST 2: STYLE MATCHUP VALIDATION")
    print("Different styles should be competitive at similar skill levels")
    print("=" * 70)
    
    matchups = [
        (create_elite_striker(), create_elite_wrestler(), "Striker vs Wrestler"),
        (create_elite_striker(), create_elite_bjj(), "Striker vs BJJ"),
        (create_elite_striker(), create_elite_sambo(), "Striker vs Sambo"),
        (create_elite_striker(), create_elite_muay_thai(), "Striker vs Muay Thai"),
        (create_elite_wrestler(), create_elite_bjj(), "Wrestler vs BJJ"),
        (create_elite_wrestler(), create_elite_sambo(), "Wrestler vs Sambo"),
        (create_elite_muay_thai(), create_elite_wrestler(), "Muay Thai vs Wrestler"),
        (create_elite_sambo(), create_elite_bjj(), "Sambo vs BJJ"),
        (create_elite_kickboxer(), create_elite_wrestler(), "Kickboxer vs Wrestler"),
        (create_good_striker(), create_good_wrestler(), "Good Striker vs Wrestler"),
        (create_good_muay_thai(), create_good_wrestler(), "Good MT vs Wrestler"),
        (create_good_sambo(), create_good_striker(), "Good Sambo vs Striker"),
        (create_avg_striker(), create_avg_bjj(), "Avg Striker vs BJJ"),
        (create_avg_striker(), create_avg_wrestler(), "Avg Striker vs Wrestler"),
    ]
    
    balanced_count = 0
    skewed_count = 0
    
    for f1, f2, label in matchups:
        results = run_matchup(f1, f2)
        f1_pct, f2_pct = print_matchup_results(f1, f2, results, 200)
        
        if 35 <= f1_pct <= 65:
            print(f"  ✅ BALANCED: Neither fighter dominates")
            balanced_count += 1
        else:
            winner = f1.name if f1_pct > 50 else f2.name
            print(f"  ⚠️ SKEWED: {winner} wins too often")
            skewed_count += 1
    
    print(f"\nStyle Matchup Summary: {balanced_count} balanced, {skewed_count} skewed")
    return skewed_count <= 4


def test_finish_rates():
    """Test that finish rates are realistic."""
    print("\n" + "=" * 70)
    print("TEST 3: FINISH RATE VALIDATION")
    print("Testing KO/TKO, SUB, and DEC distribution")
    print("=" * 70)
    
    fights = []
    fights.extend([run_matchup(create_elite_mma(), create_good_mma(), 100)])
    fights.extend([run_matchup(create_elite_striker(), create_elite_wrestler(), 100)])
    fights.extend([run_matchup(create_good_striker(), create_good_bjj(), 100)])
    fights.extend([run_matchup(create_avg_mma(), create_avg_mma(), 100)])
    fights.extend([run_matchup(create_elite_sambo(), create_elite_bjj(), 100)])
    fights.extend([run_matchup(create_elite_muay_thai(), create_good_wrestler(), 100)])
    fights.extend([run_matchup(create_good_sambo(), create_good_striker(), 100)])
    
    total_fights = 700
    total_ko = sum(f["f1_ko"] + f["f2_ko"] for f in fights)
    total_sub = sum(f["f1_sub"] + f["f2_sub"] for f in fights)
    total_dec = sum(f["f1_dec"] + f["f2_dec"] + f["draws"] for f in fights)
    
    ko_rate = total_ko / total_fights * 100
    sub_rate = total_sub / total_fights * 100
    dec_rate = total_dec / total_fights * 100
    finish_rate = (total_ko + total_sub) / total_fights * 100
    
    print(f"\nOverall Statistics ({total_fights} fights):")
    print(f"  KO/TKO Rate: {ko_rate:.1f}%")
    print(f"  Submission Rate: {sub_rate:.1f}%")
    print(f"  Decision Rate: {dec_rate:.1f}%")
    print(f"  Total Finish Rate: {finish_rate:.1f}%")
    
    print(f"\n  Expected (real MMA): ~30% KO/TKO, ~15% SUB, ~50% DEC")
    
    all_passed = True
    if 18 <= ko_rate <= 40:
        print(f"  ✅ KO/TKO rate is realistic")
    else:
        print(f"  ⚠️ KO/TKO rate outside expected range")
        all_passed = False
    
    if 8 <= sub_rate <= 22:
        print(f"  ✅ Submission rate is realistic")
    else:
        print(f"  ⚠️ Submission rate outside expected range")
        all_passed = False
    
    if 40 <= dec_rate <= 75:
        print(f"  ✅ Decision rate is realistic")
    else:
        print(f"  ⚠️ Decision rate outside expected range")
        all_passed = False
    
    return all_passed


def test_specialist_advantage():
    """Test that specialists excel in their domain."""
    print("\n" + "=" * 70)
    print("TEST 4: SPECIALIST ADVANTAGE VALIDATION")
    print("Strikers should get more KOs, grapplers more subs")
    print("=" * 70)
    
    striker_results = run_matchup(create_good_striker(), create_avg_mma())
    striker_ko_rate = (striker_results["f1_ko"] / max(1, striker_results["f1_wins"])) * 100
    
    bjj_results = run_matchup(create_good_bjj(), create_avg_mma())
    bjj_sub_rate = (bjj_results["f1_sub"] / max(1, bjj_results["f1_wins"])) * 100
    
    wrestler_results = run_matchup(create_good_wrestler(), create_avg_mma())
    wrestler_dec_rate = (wrestler_results["f1_dec"] / max(1, wrestler_results["f1_wins"])) * 100
    
    sambo_results = run_matchup(create_good_sambo(), create_avg_mma())
    sambo_sub_rate = (sambo_results["f1_sub"] / max(1, sambo_results["f1_wins"])) * 100
    
    mt_results = run_matchup(create_good_muay_thai(), create_avg_mma())
    mt_ko_rate = (mt_results["f1_ko"] / max(1, mt_results["f1_wins"])) * 100
    
    print(f"\nGood Striker KO/TKO rate (of wins): {striker_ko_rate:.1f}%")
    print(f"Good BJJ Submission rate (of wins): {bjj_sub_rate:.1f}%")
    print(f"Good Wrestler Decision rate (of wins): {wrestler_dec_rate:.1f}%")
    print(f"Good Sambo Submission rate (of wins): {sambo_sub_rate:.1f}%")
    print(f"Good Muay Thai KO/TKO rate (of wins): {mt_ko_rate:.1f}%")
    
    print(f"\n  Specialists should outperform in their domain")
    
    all_passed = True
    if striker_ko_rate >= 25:
        print(f"  ✅ Strikers get elevated KO rate")
    else:
        print(f"  ⚠️ Strikers not getting enough KOs")
        all_passed = False
    
    if bjj_sub_rate >= 10:
        print(f"  ✅ BJJ specialists get elevated submission rate")
    else:
        print(f"  ⚠️ BJJ specialists not getting enough submissions")
        all_passed = False
    
    if sambo_sub_rate >= 8:
        print(f"  ✅ Sambo fighters get submissions")
    else:
        print(f"  ⚠️ Sambo not submitting enough")
        all_passed = False
    
    return all_passed


def test_upset_potential():
    """Test that underdogs can occasionally win."""
    print("\n" + "=" * 70)
    print("TEST 5: UPSET POTENTIAL VALIDATION")
    print("Lower rated can win, but not too often")
    print("=" * 70)
    
    matchups = [
        (create_elite_mma(), create_below_avg(), "Elite vs Below Avg"),
        (create_elite_mma(), create_prospect(), "Elite vs Prospect"),
        (create_good_mma(), create_prospect(), "Good vs Prospect"),
    ]
    
    upset_found = False
    for f1, f2, label in matchups:
        results = run_matchup(f1, f2)
        underdog_wins = results["f2_wins"]
        pct = underdog_wins / 200 * 100
        
        print(f"\n{label}:")
        print(f"  Underdog wins: {underdog_wins}/200 ({pct:.1f}%)")
        
        if underdog_wins > 0:
            print(f"  ✅ Upsets can happen")
            upset_found = True
        else:
            print(f"  ⚠️ No upsets at all - may be too deterministic")
    
    return upset_found


def test_mirror_matchups():
    """Test that same fighter vs same fighter is ~50/50."""
    print("\n" + "=" * 70)
    print("TEST 6: MIRROR MATCHUP VALIDATION")
    print("Same fighter vs same fighter should be ~50/50")
    print("=" * 70)
    
    templates = [
        ("Elite MMA", create_elite_mma),
        ("Good Striker", create_good_striker),
        ("Avg Wrestler", create_avg_wrestler),
        ("Elite Sambo", create_elite_sambo),
        ("Good Muay Thai", create_good_muay_thai),
    ]
    
    all_balanced = True
    for name, create_func in templates:
        f1 = create_func()
        f2 = create_func()
        f1.fighter_id = "f1"
        f2.fighter_id = "f2"
        f2.name = f"{name} 2"
        
        results = run_matchup(f1, f2)
        f1_pct = results["f1_wins"] / 200 * 100
        f2_pct = results["f2_wins"] / 200 * 100
        
        print(f"\n{name} vs {name}:")
        print(f"  Fighter 1 wins: {f1_pct:.1f}%")
        print(f"  Fighter 2 wins: {f2_pct:.1f}%")
        
        if 40 <= f1_pct <= 60:
            print(f"  ✅ Balanced as expected")
        else:
            print(f"  ⚠️ Unbalanced mirror matchup")
            all_balanced = False
    
    return all_balanced


def test_style_detection():
    """Test that style detection works correctly."""
    print("\n" + "=" * 70)
    print("TEST 7: STYLE DETECTION VALIDATION")
    print("Verifying style detection function")
    print("=" * 70)
    
    fighters = [
        (create_elite_striker(), "striker"),
        (create_elite_kickboxer(), "kickboxer"),
        (create_elite_muay_thai(), "muay_thai"),
        (create_elite_wrestler(), "wrestler"),
        (create_elite_bjj(), "bjj"),
        (create_elite_sambo(), "sambo"),
        (create_elite_mma(), "balanced"),
    ]
    
    all_correct = True
    for fighter, expected_style in fighters:
        detected = detect_fighter_style(fighter)
        status = "✅" if detected == expected_style else "⚠️"
        print(f"  {status} {fighter.name}: detected as '{detected}' (expected '{expected_style}')")
        if detected != expected_style:
            all_correct = False
    
    return all_correct


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("FIGHT ENGINE BALANCE VALIDATION")
    print("=" * 70)
    
    print("\nTesting with comprehensive fighter archetypes")
    print("Styles: Striker, Kickboxer, Muay Thai, Wrestler, BJJ, Sambo, Balanced")
    
    results = {}
    results["style_detection"] = test_style_detection()
    results["rating_advantage"] = test_rating_advantage()
    results["style_matchups"] = test_style_matchups()
    results["finish_rates"] = test_finish_rates()
    results["specialist_advantage"] = test_specialist_advantage()
    results["upset_potential"] = test_upset_potential()
    results["mirror_matchups"] = test_mirror_matchups()
    
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "⚠️ NEEDS TUNING"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    print("=" * 70)
