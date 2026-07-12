"""O3 — coverage-tier reachability.

For each coverage cell, verify the entries ACTUALLY exercised the branch
they were chosen for. A '5R_title' fight that finished in R2 does not
test championship-round mechanics.
"""
import json, os, sys

REPO = "/Users/vandope/Desktop/Games/cage_dynasty"
WEB = os.path.join(REPO, "cage_dynasty_web")
for _p in (os.path.join(REPO, "simulation"),
           os.path.join(REPO, "narrative"),
           os.path.join(REPO, "systems"),
           WEB):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import fight_engine as fe

FIXTURE = "/Users/vandope/Desktop/Games/cage_dynasty/outputs/stage0c_golden_master/fixture.json"

with open(FIXTURE) as f:
    fx = json.load(f)

coverage = [e for e in fx["entries"] if e["tier"] == "coverage"]
by_cell = {}
for e in coverage:
    by_cell.setdefault(e["coverage_cell"], []).append(e)

print("═" * 76)
print("O3 — coverage-tier reachability")
print("═" * 76)

for cell in ["5R_title", "5R_main_nontitle", "extreme_ovr_gap_up",
             "extreme_ovr_gap_down", "r1_finish", "goes_the_distance",
             "style_diversity_sampler", "high_heat_synth"]:
    entries = by_cell.get(cell, [])
    n = len(entries)
    if n == 0:
        print(f"\n{cell:<32s} n=0   UNREACHABLE FROM WORLD_INIT OUTPUT — reported, not synthesized")
        continue

    print(f"\n{cell:<32s} n={n}")

    if cell == "5R_title":
        # Championship rounds are R4 and R5. Fight must reach one of those
        # OR the fixture's expected result must be a decision (rounds 1-3 finish
        # doesn't exercise championship mechanics at all).
        r4_or_5 = 0
        r_1_to_3 = 0
        decision = 0
        for e in entries:
            fr = e["expected_fi"]["finish_round"]
            if fr in (4, 5):
                r4_or_5 += 1
            elif fr is None:
                decision += 1
            else:
                r_1_to_3 += 1
        print(f"    R4/R5 finish: {r4_or_5}     decision: {decision}     R1-R3 finish (NO champ-round exercise): {r_1_to_3}")
        exercised = r4_or_5 + decision
        print(f"    exercised championship rounds: {exercised}/{n}")

    elif cell == "extreme_ovr_gap_up":
        # Use the real FighterAttributes.overall property, not a proxy.
        def _real_ovr(d):
            fa = fe.FighterAttributes(**d, fighting_style=None)
            return fa.overall
        gaps = [_real_ovr(e["fighter1"]) - _real_ovr(e["fighter2"]) for e in entries]
        met = sum(1 for g in gaps if g >= 15)
        print(f"    fighter1 OVR - fighter2 OVR: min={min(gaps)}  max={max(gaps)}  median={sorted(gaps)[n//2]}")
        print(f"    fights where fighter1 OVR gap >=15: {met}/{n}")

    elif cell == "extreme_ovr_gap_down":
        def _real_ovr(d):
            fa = fe.FighterAttributes(**d, fighting_style=None)
            return fa.overall
        gaps = [_real_ovr(e["fighter2"]) - _real_ovr(e["fighter1"]) for e in entries]
        met = sum(1 for g in gaps if g >= 15)
        print(f"    fighter2 OVR - fighter1 OVR: min={min(gaps)}  max={max(gaps)}  median={sorted(gaps)[n//2]}")
        print(f"    fights where fighter2 OVR gap >=15: {met}/{n}")

    elif cell == "r1_finish":
        # The fixture selected these because the WORLD_INIT sim finished R1.
        # But the fixture entry captures a NEW result under fixture seed.
        # Check whether the fixture's captured expected result also finishes R1.
        r1 = sum(1 for e in entries if e["expected_fi"]["finish_round"] == 1)
        print(f"    fixture-captured expected FI finishes in R1: {r1}/{n}")
        print(f"    (world_init sim gave these R1 finishes; fixture seed may differ)")

    elif cell == "goes_the_distance":
        distance = sum(1 for e in entries if e["expected_fi"]["finish_round"] is None)
        print(f"    fixture-captured expected FI went to decision: {distance}/{n}")

    elif cell == "style_diversity_sampler":
        # Verify variety
        # (we don't have style stored on fighter dict since it was on GeneratedFighter,
        # not FighterAttributes — we can only check for FIGHTER PAIR diversity)
        pairs = set()
        for e in entries:
            key = (e["fighter1"]["name"], e["fighter2"]["name"])
            pairs.add(key)
        print(f"    unique fighter-pair combinations: {len(pairs)}/{n}")
        print(f"    (structural: entries were chosen for distinct style pairs)")

    elif cell == "high_heat_synth":
        heats = [e["heat_level"] for e in entries]
        met = sum(1 for h in heats if h > 40)
        print(f"    heat_level values: {sorted(set(heats))}")
        print(f"    entries with heat > 40: {met}/{n}")

print("\n" + "═" * 76)
print("Summary: which cells effectively test what they aimed at?")
print("═" * 76)
