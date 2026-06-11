"""
Standalone fight engine test harness.

Generates 11 matchups × 20 fights = 220 simulated fights at LOCAL tier
(OVR ~65-70) covering all 11 fighting styles. Uses fight_engine.simulate_fight
directly (no commentary path) for speed.

Reports:
- Overall finish rate (KO / TKO / SUB) vs decision rate
- Per-method breakdown
- Per-matchup result distribution
- Average finishing round
- Style-detection sanity check on every generated fighter
- Errors encountered
"""

import os
import sys
import traceback
from collections import defaultdict

# Ensure the flat-file imports resolve when run from the cage_dynasty_web dir
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from fight_engine import (
    FighterAttributes,
    simulate_fight,
    detect_fighter_style,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fighter generators — LOCAL tier OVR ~65-70, calibrated so detect_fighter_style
# clearly identifies each style (skill_range > 10 OR avg < 68 to dodge balanced
# short-circuit, while hitting the primary-check thresholds).
# ─────────────────────────────────────────────────────────────────────────────

def _make(name, style_hint, **stats):
    """Build a FighterAttributes with defaults filled in and an OVR-ish value."""
    base = dict(
        strength=62, speed=64, cardio=66, chin=64, recovery=64,
        boxing=62, kicks=60, clinch_striking=60, striking_defense=62,
        takedowns=62, takedown_defense=62, top_control=62,
        submissions=58, guard=58,
        heart=66, fight_iq=64, composure=64,
    )
    base.update(stats)
    avg = sum(base.values()) // len(base)
    return FighterAttributes(
        fighter_id=name.lower().replace(" ", "_"),
        name=name,
        fighting_style=style_hint,
        is_generational=False,
        **base,
    ), avg


def make_bjj(name):
    # bjj_score = (sub + guard)/2 >= 70, wrestling < 68
    f, _ = _make(name, "BJJ_SPECIALIST",
                 submissions=78, guard=78,
                 takedowns=62, top_control=64,
                 boxing=58, kicks=56, clinch_striking=58)
    return f

def make_wrestler(name):
    # wrestling = (td + tc)/2 >= 70, bjj < 65
    f, _ = _make(name, "WRESTLER",
                 takedowns=78, top_control=76, takedown_defense=72,
                 submissions=58, guard=60,
                 boxing=62, kicks=58, clinch_striking=62)
    return f

def make_sambo(name):
    # wrestling >= 72 AND bjj >= 68
    f, _ = _make(name, "SAMBO",
                 takedowns=74, top_control=72,
                 submissions=70, guard=68,
                 boxing=60, kicks=58, clinch_striking=62)
    return f

def make_muay_thai(name):
    # clinch_striking >= 72 AND kicks >= 68
    f, _ = _make(name, "MUAY_THAI",
                 clinch_striking=76, kicks=72,
                 boxing=66, striking_defense=66,
                 takedowns=58, submissions=58)
    return f

def make_gnp(name):
    # wrestling >= 65 AND strength >= 68 AND bjj < 65
    f, _ = _make(name, "GROUND_AND_POUND",
                 strength=72,
                 takedowns=70, top_control=70, takedown_defense=66,
                 submissions=58, guard=58,
                 boxing=62, kicks=58)
    return f

def make_sprawl_brawl(name):
    # TDD >= 70 AND striking_score >= 65
    f, _ = _make(name, "SPRAWL_AND_BRAWL",
                 takedown_defense=75,
                 boxing=68, kicks=66, striking_defense=68,
                 takedowns=58, top_control=58, submissions=58, guard=58)
    return f

def make_clinch_fighter(name):
    # clinch >= 65 AND cardio >= 68 AND wrestling >= 58
    f, _ = _make(name, "CLINCH_FIGHTER",
                 clinch_striking=70, cardio=72,
                 takedowns=62, top_control=64,
                 boxing=62, kicks=60, submissions=58, guard=58)
    return f

def make_pressure(name):
    # pressure = (cardio + heart + chin)/3 >= 70 AND striking >= 60
    f, _ = _make(name, "PRESSURE_FIGHTER",
                 cardio=74, heart=72, chin=70,
                 boxing=65, kicks=60,
                 takedowns=58, submissions=58)
    return f

def make_counter(name):
    # defense = (sd + comp)/2 >= 68 AND fight_iq >= 65 AND striking >= 62
    f, _ = _make(name, "COUNTER_STRIKER",
                 striking_defense=72, composure=68, fight_iq=70,
                 boxing=66, kicks=62,
                 takedowns=58, submissions=58)
    return f

def make_point(name):
    # speed >= 70 AND defense >= 65 AND fight_iq >= 65
    f, _ = _make(name, "POINT_FIGHTER",
                 speed=74, striking_defense=68, composure=66, fight_iq=70,
                 boxing=64, kicks=62,
                 takedowns=58, submissions=58)
    return f

def make_striker(name):
    # striking >= 68, wrestling < 62, bjj < 62
    f, _ = _make(name, "STRIKER",
                 boxing=72, kicks=68, striking_defense=65,
                 takedowns=58, top_control=58, submissions=58, guard=58)
    return f

def make_balanced(name):
    # range <= 10 AND avg >= 68 on the five checked skills
    f, _ = _make(name, "BALANCED",
                 boxing=70, kicks=68, clinch_striking=68,
                 takedowns=68, top_control=70,
                 submissions=70, guard=68,
                 striking_defense=68, takedown_defense=68,
                 cardio=70, chin=68, recovery=68, strength=68,
                 speed=68, heart=70, fight_iq=70, composure=68)
    return f


# ─────────────────────────────────────────────────────────────────────────────
# Method classification — bucket the engine's method strings
# ─────────────────────────────────────────────────────────────────────────────

def classify_method(method):
    if not method:
        return "OTHER"
    m = method
    if "Decision" in m:
        return "DEC"
    if m == "Draw":
        return "DRAW"
    if "Submission" in m:
        return "SUB"
    if "TKO" in m:
        return "TKO"
    if "KO" in m:
        return "KO"
    return "OTHER"


# ─────────────────────────────────────────────────────────────────────────────
# Matchup definitions
# ─────────────────────────────────────────────────────────────────────────────

MATCHUPS = [
    ("bjj vs wrestler",                make_bjj,            make_wrestler),
    ("muay_thai vs striker",           make_muay_thai,      make_striker),
    ("sambo vs bjj",                   make_sambo,          make_bjj),
    ("ground_and_pound vs striker",    make_gnp,            make_striker),
    ("sprawl_and_brawl vs wrestler",   make_sprawl_brawl,   make_wrestler),
    ("counter_striker vs pressure",    make_counter,        make_pressure),
    ("point_fighter vs muay_thai",     make_point,          make_muay_thai),
    ("clinch_fighter vs wrestler",     make_clinch_fighter, make_wrestler),
    ("pressure vs striker",            make_pressure,       make_striker),
    ("bjj vs bjj",                     make_bjj,            make_bjj),
    ("balanced vs balanced",           make_balanced,       make_balanced),
]

FIGHTS_PER_MATCHUP = 20


def main():
    # ── Style detection sanity check ────────────────────────────────────────
    print("=" * 72)
    print("STYLE DETECTION CHECK (LOCAL tier stats, OVR ~65-70)")
    print("=" * 72)
    print(f"{'Builder':<22}{'fighting_style hint':<22}{'detected':<20}")
    print("-" * 72)
    for label, maker_a, _ in MATCHUPS:
        f = maker_a("Sample A")
        detected = detect_fighter_style(f)
        hint = f.fighting_style or ""
        print(f"{maker_a.__name__:<22}{str(hint):<22}{detected:<20}")
    print()

    # ── Run the matchups ────────────────────────────────────────────────────
    print("=" * 72)
    print(f"RUNNING {len(MATCHUPS)} MATCHUPS × {FIGHTS_PER_MATCHUP} FIGHTS = "
          f"{len(MATCHUPS) * FIGHTS_PER_MATCHUP} TOTAL")
    print("=" * 72)

    overall = defaultdict(int)
    per_matchup = {}
    finish_rounds = []
    errors = []
    error_count = 0

    for label, maker_a, maker_b in MATCHUPS:
        bucket = defaultdict(int)
        rounds_in_matchup = []
        for i in range(FIGHTS_PER_MATCHUP):
            try:
                f1 = maker_a(f"A_{i}")
                f2 = maker_b(f"B_{i}")
                # Give them distinct ids so winner/loser routing works
                f1.fighter_id = f"{label}_A_{i}"
                f2.fighter_id = f"{label}_B_{i}"
                result = simulate_fight(f1, f2)
                bucket_key = classify_method(result.method)
                bucket[bucket_key] += 1
                overall[bucket_key] += 1
                if bucket_key in ("KO", "TKO", "SUB") and result.finish_round:
                    finish_rounds.append(result.finish_round)
                    rounds_in_matchup.append(result.finish_round)
            except Exception as e:
                error_count += 1
                errors.append(f"[{label} #{i}] {type(e).__name__}: {e}")
        per_matchup[label] = (dict(bucket), rounds_in_matchup)

    # ── Per-matchup breakdown ───────────────────────────────────────────────
    print()
    print("=" * 72)
    print("PER-MATCHUP BREAKDOWN")
    print("=" * 72)
    print(f"{'Matchup':<34}{'KO':>5}{'TKO':>5}{'SUB':>5}{'DEC':>5}"
          f"{'DRAW':>6}{'OTHER':>7}{'avgR':>6}")
    print("-" * 72)
    for label, (bucket, rounds_in) in per_matchup.items():
        avg_r = (sum(rounds_in) / len(rounds_in)) if rounds_in else 0.0
        print(f"{label:<34}"
              f"{bucket.get('KO', 0):>5}"
              f"{bucket.get('TKO', 0):>5}"
              f"{bucket.get('SUB', 0):>5}"
              f"{bucket.get('DEC', 0):>5}"
              f"{bucket.get('DRAW', 0):>6}"
              f"{bucket.get('OTHER', 0):>7}"
              f"{avg_r:>6.2f}")

    # ── Overall summary ─────────────────────────────────────────────────────
    total = sum(overall.values())
    print()
    print("=" * 72)
    print("OVERALL SUMMARY")
    print("=" * 72)
    if total == 0:
        print("No fights completed.")
    else:
        finishes = overall["KO"] + overall["TKO"] + overall["SUB"]
        print(f"Total fights:    {total}")
        print(f"Errors caught:   {error_count}")
        print(f"Finish rate:     {finishes}/{total} = "
              f"{100.0 * finishes / total:.1f}%")
        print(f"Decision rate:   {overall['DEC']}/{total} = "
              f"{100.0 * overall['DEC'] / total:.1f}%")
        if overall["DRAW"]:
            print(f"Draws:           {overall['DRAW']}/{total} = "
                  f"{100.0 * overall['DRAW'] / total:.1f}%")
        if overall["OTHER"]:
            print(f"Other (unparsed):{overall['OTHER']}/{total} = "
                  f"{100.0 * overall['OTHER'] / total:.1f}%")
        print()
        print("Method distribution:")
        print(f"  KO:   {overall['KO']:>3}  ({100.0 * overall['KO'] / total:5.1f}%)")
        print(f"  TKO:  {overall['TKO']:>3}  ({100.0 * overall['TKO'] / total:5.1f}%)")
        print(f"  SUB:  {overall['SUB']:>3}  ({100.0 * overall['SUB'] / total:5.1f}%)")
        print(f"  DEC:  {overall['DEC']:>3}  ({100.0 * overall['DEC'] / total:5.1f}%)")
        if finish_rounds:
            avg = sum(finish_rounds) / len(finish_rounds)
            print()
            print(f"Average finishing round: {avg:.2f} "
                  f"(n={len(finish_rounds)} finishes)")
            # Per-round breakdown
            from collections import Counter
            round_counts = Counter(finish_rounds)
            print("  Finishes by round:")
            for r in sorted(round_counts):
                print(f"    Round {r}: {round_counts[r]}")

    if errors:
        print()
        print("=" * 72)
        print(f"ERRORS ({len(errors)})")
        print("=" * 72)
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
