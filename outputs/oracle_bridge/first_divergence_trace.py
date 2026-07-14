"""STAGE 1 — FIRST-DIVERGENCE TRACE. READ-ONLY.

For each fixture matchup, run BOTH engines with primitive-level
instrumentation and diff the resulting call sequences.

Both engines share select_action / calculate_strike_damage /
attempt_submission (imported from fight_engine). Wrapping those
primitives via monkey-patch captures every call from either engine
with a call-index and arg/return summary — a "same seed → same
draws → same primitive sequence" instrument.

Divergence answers:
  Q1 — histogram of first-divergence CALL INDEX across the fixture
  Q2 — classify the first divergence by TYPE (action / damage / finish)
  Q3 — pick a fight that ends TKO-strikes in live and DEC in pre-gen,
       trace it exchange-by-exchange, name the accumulator FI has that
       FE doesn't
  Q4 — heat multiplier magnitude distribution (probe separately)

Rules:
  - Observation-only monkey-patch; production code untouched.
  - Non-perturbing (verified: primitives called with unchanged args,
    return values passed through unchanged).
  - Both gates before and after.
  - No engine changes. No tuning proposed.
"""
import _common  # noqa: F401
import io
import json
import os
import random
import contextlib
import sys
from collections import Counter, defaultdict
from dataclasses import fields as dc_fields, replace

_HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(_HERE, "fixture.json")

# ── Style buckets for reporting ────────────────────────────────────
STRIKER_STYLES = {"Striker", "Counter Striker", "Pressure Fighter",
                  "Point Fighter", "Muay Thai"}
GRAPPLER_STYLES = {"Wrestler", "Ground & Pound", "BJJ Specialist",
                   "Clinch Fighter"}

def style_bucket(s):
    if s in STRIKER_STYLES: return "S"
    if s in GRAPPLER_STYLES: return "G"
    return "H"

# ── Shared trace list ──────────────────────────────────────────────
_trace = []

def _log(kind, **kw):
    _trace.append({"kind": kind, "seq": len(_trace), **kw})

def _summ(obj):
    """Compact repr — enough to detect divergence, small enough to store."""
    if obj is None: return None
    if isinstance(obj, (int, float, str, bool)): return obj
    if hasattr(obj, 'value'): return obj.value
    if hasattr(obj, 'fighter_id'): return f"F#{obj.fighter_id[:8]}"
    if isinstance(obj, (list, tuple)) and len(obj) < 6:
        return [_summ(x) for x in obj]
    return f"<{type(obj).__name__}>"

def install_primitive_hooks(fight_engine):
    """Wrap select_action / calculate_strike_damage / attempt_submission
    for the duration of a fight. Returns a restore-fn."""
    orig_sa = fight_engine.select_action
    orig_csd = fight_engine.calculate_strike_damage
    orig_as = fight_engine.attempt_submission

    def wrap_sa(*args, **kwargs):
        result = orig_sa(*args, **kwargs)
        # Compact: log the fighter, position, top-flag, result action
        actor = args[0] if args else kwargs.get("fighter")
        pos = args[3] if len(args) > 3 else kwargs.get("position")
        is_top = args[4] if len(args) > 4 else kwargs.get("is_top")
        _log("select_action",
             actor=_summ(actor), pos=_summ(pos), is_top=_summ(is_top),
             action=_summ(result))
        return result

    def wrap_csd(*args, **kwargs):
        result = orig_csd(*args, **kwargs)
        _log("calc_damage",
             damage=(round(float(result), 3) if isinstance(result, (int, float)) else _summ(result)))
        return result

    def wrap_as(*args, **kwargs):
        result = orig_as(*args, **kwargs)
        # result may be a tuple (success, damage_dealt) or similar
        _log("attempt_sub", result=_summ(result))
        return result

    fight_engine.select_action = wrap_sa
    fight_engine.calculate_strike_damage = wrap_csd
    fight_engine.attempt_submission = wrap_as

    # Also wrap FI's references — FI imports these at module load
    import fight_integration as fi
    fi_orig = {}
    for name, wrapped in [("select_action", wrap_sa),
                          ("calculate_strike_damage", wrap_csd),
                          ("attempt_submission", wrap_as)]:
        if hasattr(fi, name):
            fi_orig[name] = getattr(fi, name)
            setattr(fi, name, wrapped)

    def restore():
        fight_engine.select_action = orig_sa
        fight_engine.calculate_strike_damage = orig_csd
        fight_engine.attempt_submission = orig_as
        for name, orig in fi_orig.items():
            setattr(fi, name, orig)
    return restore

# ── Reconstruct FighterAttributes from fixture dict ────────────────
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

# ── Run one fight through each engine, capture traces ──────────────
def run_pair(fixture_fight, seed):
    import fight_engine as fe
    import fight_integration as fi

    fa1 = rebuild_fa(fixture_fight.get("fa1", {}), fe)
    fa2 = rebuild_fa(fixture_fight.get("fa2", {}), fe)
    if not fa1 or not fa2:
        return None, None

    rounds = fixture_fight.get("rounds", 3)
    is_title = fixture_fight.get("source_is_title_fight", False)
    is_main = fixture_fight.get("is_main_event", False)

    # ── FE run ─────────────────────────────────────────────────
    _trace.clear()
    restore = install_primitive_hooks(fe)
    try:
        fe_cfg = fe.FightConfig.championship_fight() if is_title else fe.FightConfig.standard_fight()
        if rounds == 5 and not is_title:
            fe_cfg = replace(fe_cfg, scheduled_rounds=5)
        random.seed(seed)
        with contextlib.redirect_stdout(io.StringIO()):
            fe_result = fe.simulate_fight(fa1, fa2, fe_cfg, heat_level=0)
    finally:
        restore()
    fe_trace = list(_trace)

    # ── FI run ─────────────────────────────────────────────────
    _trace.clear()
    restore = install_primitive_hooks(fe)
    try:
        # FI wants LIVE_PLAY triple (55, 0.48, 10)
        fi_cfg = fe.FightConfig(
            scheduled_rounds=rounds,
            standup_threshold=10, exchanges_per_round=55,
            damage_multiplier=0.48,
            submission_progress_to_finish=70.0,
            submission_escape_threshold=85.0,
            is_title_fight=is_title, is_main_event=is_main,
        )
        random.seed(seed)
        with contextlib.redirect_stdout(io.StringIO()):
            fi_result = fi.simulate_narrated_fight(
                fa1, fa2, rounds=rounds,
                is_title_fight=is_title, is_main_event=is_main,
                config=fi_cfg)
    finally:
        restore()
    fi_trace = list(_trace)

    return {
        "fe_result": {"method": fe_result.method, "round": fe_result.finish_round},
        "fi_result": {"method": fi_result.method, "round": fi_result.finish_round},
        "fe_trace": fe_trace,
        "fi_trace": fi_trace,
    }

# ── Diff two traces ────────────────────────────────────────────────
def first_divergence(t1, t2):
    """Return (index, t1_entry, t2_entry) or None if identical prefix."""
    minlen = min(len(t1), len(t2))
    for i in range(minlen):
        a, b = t1[i], t2[i]
        if a != b:
            return (i, a, b)
    if len(t1) != len(t2):
        # One ran longer
        return (minlen, t1[minlen] if len(t1) > minlen else "END",
                        t2[minlen] if len(t2) > minlen else "END")
    return None

# ── Run across fixture ─────────────────────────────────────────────
def main():
    fx = json.load(open(FIXTURE))
    fights = fx["fights"]
    print(f"# Loaded {len(fights)} fights from fixture")
    print()

    diff_kinds = Counter()
    div_indices = []
    same_method = 0; diff_method = 0
    tko_dec_candidates = []  # for Q3
    per_fight_summary = []
    fights_traced = 0
    misses = 0

    for i, f in enumerate(fights):
        res = run_pair(f, seed=1000 + i)
        if res is None:
            misses += 1
            continue
        fights_traced += 1
        d = first_divergence(res["fe_trace"], res["fi_trace"])
        fe_m = res["fe_result"]["method"]
        fi_m = res["fi_result"]["method"]
        fe_cls = fe_m.split()[0] if fe_m else ""
        fi_cls = fi_m.split()[0] if fi_m else ""
        method_match = fe_m == fi_m
        if method_match: same_method += 1
        else: diff_method += 1

        # Q3 candidate: FI ends TKO, FE ends Decision
        if fi_m and fe_m and "TKO" in fi_m and "Decision" in fe_m:
            tko_dec_candidates.append({
                "fight_idx": i,
                "fe_method": fe_m, "fi_method": fi_m,
                "diff": d,
                "f1_style": (f.get("fa1") or {}).get("fighting_style"),
                "f2_style": (f.get("fa2") or {}).get("fighting_style"),
            })

        if d is None:
            div_indices.append(None)
            per_fight_summary.append(f"  fight[{i:>2}] IDENTICAL trace  ({fe_m} vs {fi_m})")
        else:
            idx, a, b = d
            div_indices.append(idx)
            kind_pair = f"{a.get('kind','END') if isinstance(a, dict) else a}/{b.get('kind','END') if isinstance(b, dict) else b}"
            diff_kinds[kind_pair] += 1
            per_fight_summary.append(
                f"  fight[{i:>2}] div@{idx:>4}  {kind_pair:<28}  "
                f"FE={fe_m[:20]:<20}  FI={fi_m[:20]:<20}"
            )

    print("=" * 100)
    print(f"OVERALL")
    print("=" * 100)
    print(f"  fights traced:              {fights_traced}")
    print(f"  fights with misses (skip):  {misses}")
    print(f"  identical trace / same result: {sum(1 for x in div_indices if x is None)}")
    print(f"  divergent trace:            {sum(1 for x in div_indices if x is not None)}")
    print(f"  same method:                {same_method}")
    print(f"  different method:           {diff_method}")
    print()

    # Q1 — histogram of first-divergence index
    print("=" * 100)
    print("Q1 — HISTOGRAM OF FIRST-DIVERGENCE CALL INDEX")
    print("=" * 100)
    real = [x for x in div_indices if x is not None]
    if real:
        real_sorted = sorted(real)
        print(f"  fights that diverge: {len(real)}")
        print(f"  first-divergence index: min={min(real)}  median={real_sorted[len(real)//2]}  "
              f"p90={real_sorted[int(len(real)*0.9)]}  max={max(real)}")
        # Bucket
        buckets = Counter()
        for x in real:
            if x == 0: b = "0 (immediate)"
            elif x <= 5: b = "1-5"
            elif x <= 20: b = "6-20"
            elif x <= 50: b = "21-50"
            elif x <= 100: b = "51-100"
            else: b = "101+"
        buckets[b] = buckets.get(b, 0) + 1
        buckets = Counter()
        for x in real:
            if x == 0: buckets["0 (immediate)"] += 1
            elif x <= 5: buckets["1-5"] += 1
            elif x <= 20: buckets["6-20"] += 1
            elif x <= 50: buckets["21-50"] += 1
            elif x <= 100: buckets["51-100"] += 1
            else: buckets["101+"] += 1
        for k in ("0 (immediate)", "1-5", "6-20", "21-50", "51-100", "101+"):
            if buckets.get(k, 0):
                print(f"    {k:<20}: {buckets[k]}")

    # Q2 — divergence type distribution
    print()
    print("=" * 100)
    print("Q2 — WHAT DIVERGES FIRST (kind_at_FE / kind_at_FI)")
    print("=" * 100)
    for kp, n in diff_kinds.most_common():
        print(f"  {n:>4}  {kp}")

    # Q3 — TKO-strikes in FI vs DEC in FE candidates
    print()
    print("=" * 100)
    print("Q3 — CANDIDATES: FI ends TKO, FE ends Decision")
    print("=" * 100)
    print(f"  found {len(tko_dec_candidates)} candidate fights")
    if tko_dec_candidates:
        c = tko_dec_candidates[0]
        print(f"  Trace subject: fight[{c['fight_idx']}] "
              f"({c['f1_style']} vs {c['f2_style']})")
        print(f"    FE: {c['fe_method']}")
        print(f"    FI: {c['fi_method']}")
        d = c['diff']
        if d:
            idx, a, b = d
            print(f"    first divergence at call {idx}:")
            print(f"      FE: {a}")
            print(f"      FI: {b}")

    # Per-fight summary (first 30 lines)
    print()
    print("=" * 100)
    print("Per-fight summary (first 30)")
    print("=" * 100)
    for line in per_fight_summary[:30]:
        print(line)
    if len(per_fight_summary) > 30:
        print(f"  ... and {len(per_fight_summary)-30} more")

if __name__ == "__main__":
    main()
