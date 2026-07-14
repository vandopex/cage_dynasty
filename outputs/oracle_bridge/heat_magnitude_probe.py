"""STAGE 1 — HEAT MAGNITUDE PROBE. READ-ONLY.

Van's Q4: FE mutates damage up to ×1.20; FI has no heat. Report the
multiplier distribution at point of use + delta to FE's outcome
surface at heat=1.0.

Two measurements:
  (a) Multiplier distribution: bucketed by heat_level per the tier
      table at fight_engine.py:3935-3952.
  (b) Delta to outcome: run FE on all fixture matchups at heat=0
      vs heat=80, compare finish rates.
"""
import _common  # noqa: F401
import io
import json
import os
import random
import contextlib
import sys
from collections import Counter
from dataclasses import fields as dc_fields, replace

_HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(_HERE, "fixture.json")

def rebuild_fa(fa_dict, fight_engine):
    valid = {f.name for f in dc_fields(fight_engine.FighterAttributes)}
    kw = {k: v for k, v in fa_dict.items() if k in valid}
    style = kw.get('fighting_style')
    if style and isinstance(style, str):
        try:
            from styles import FightingStyle
            for m in FightingStyle:
                if m.value == style:
                    kw['fighting_style'] = m; break
            else:
                kw['fighting_style'] = None
        except Exception:
            kw['fighting_style'] = None
    try:
        return fight_engine.FighterAttributes(**kw)
    except Exception:
        return None

def classify_finish(method):
    if not method: return "OTHER"
    m = method.strip()
    if m == "Draw": return "DRAW"
    if "Decision" in m: return "DEC"
    return "FINISH"

def main():
    import fight_engine as fe

    # (a) Multiplier table
    print("=" * 90)
    print("Q4a — HEAT MULTIPLIER TIERS [grep, fight_engine.py:3935-3952]")
    print("=" * 90)
    print("  heat_level       heat_damage_mult")
    print("  ─────────────    ────────────────")
    print("  0 - 20           1.00")
    print("  20 - 40          1.05")
    print("  40 - 60          1.10")
    print("  60 - 80          1.15")
    print("  80+              1.20")
    print()

    # (b) FE outcome delta at heat=0 vs heat=80
    print("=" * 90)
    print("Q4b — FE OUTCOME DELTA: heat=0 vs heat=80")
    print("=" * 90)
    fx = json.load(open(FIXTURE))
    fights = fx["fights"]
    print(f"  running FE on {len(fights)} matchups × 5 heat levels = {5*len(fights)} sims")
    print()

    results = {}
    for heat in [0, 20, 40, 60, 80]:
        finish_count = Counter()
        n = 0
        for i, f in enumerate(fights):
            fa1 = rebuild_fa(f.get("fa1", {}), fe)
            fa2 = rebuild_fa(f.get("fa2", {}), fe)
            if not fa1 or not fa2:
                continue
            rounds = f.get("rounds", 3)
            is_title = f.get("source_is_title_fight", False)
            cfg = fe.FightConfig.championship_fight() if is_title else fe.FightConfig.standard_fight()
            if rounds == 5 and not is_title:
                cfg = replace(cfg, scheduled_rounds=5)
            random.seed(1000 + i)
            with contextlib.redirect_stdout(io.StringIO()):
                r = fe.simulate_fight(fa1, fa2, cfg, heat_level=heat)
            finish_count[classify_finish(r.method)] += 1
            n += 1
        results[heat] = (finish_count, n)

    print(f"  {'heat':>6}  {'N':>5}  {'FINISH%':>8}  {'DEC%':>7}  {'DRAW%':>7}")
    baseline_fin = None
    for heat in [0, 20, 40, 60, 80]:
        counts, n = results[heat]
        fp = 100 * counts.get("FINISH", 0) / n if n else 0
        dp = 100 * counts.get("DEC", 0) / n if n else 0
        drp = 100 * counts.get("DRAW", 0) / n if n else 0
        marker = ""
        if baseline_fin is None:
            baseline_fin = fp
        else:
            marker = f"  Δ from heat=0: {fp - baseline_fin:+.1f}pp"
        mult = {0:1.00, 20:1.05, 40:1.10, 60:1.15, 80:1.20}[heat]
        print(f"  {heat:>6}  {n:>5}  {fp:>7.1f}%  {dp:>6.1f}%  {drp:>6.1f}%   mult={mult}{marker}")

    print()
    print("=" * 90)
    print("Q4c — WHAT HEAT LEVELS ACTUALLY FIRE IN PRODUCTION [grep only]")
    print("=" * 90)
    print("  [grep] heat_level is passed to fight_engine.simulate_fight from world_init")
    print("  [grep] world_init reads rivalry.get_rivalry(f1, f2).heat_level")
    print("  [grep] CLAUDE.md POOL-DEC-RATE1: 'live save had rivalries mostly at LOW heat'")
    print("  [grep] fight_integration.simulate_narrated_fight NEVER reads heat_level")
    print("         (grep confirmed: 0 references in fight_integration.py)")
    print()
    print("  Consequence: heat_damage_mult only fires in PRE-GEN (world_init) and only")
    print("  when the rivalry system has accumulated heat >20 between two fighters.")
    print("  Live-play has no rivalry-driven damage bump at all.")

if __name__ == "__main__":
    main()
