"""STAGE 1 — RANDOM-PARITY TRACE. READ-ONLY.

The 41pp gap between FE (pre-gen) and FI (live-play) is confounded.
It's some mix of:
  (a) random-state offset — FI burns one random.getrandbits(64) at
      fight-init to seed commentary.rng (fight_integration.py:494);
      FE doesn't
  (b) pure mechanic gap — four FI-only TKO accumulator paths
      (_gnp_accumulation :1016, _clinch_body_acc :974,
       leg_kicks_absorbed :1033, _rocked_shots :1052) plus style
      windows FE lacks

This probe separates them.

Method: monkey-patch FE.simulate_fight to consume one getrandbits(64)
draw BEFORE the fight, phase-matching FI. Re-run outcome matrix.
Measure how much of 41pp closes from alignment alone. Residual =
pure mechanic gap = Stage 2a's success target.

Van's watchpoints (wired in below):
  W1: If alignment closes MORE than expected, be suspicious. The
      26.1%/3.5% TKO-strikes measurement says accumulators fire
      substantially — a big alignment close would contradict.
      Report the alignment delta AND the TKO-strikes delta on the
      aligned distribution. They must reconcile.
  W2: Step 5 spot check: on decision-ending fights that hit no
      accumulator, primitive sequences MUST align exchange-for-
      exchange after offset. If not, a second FI-only random
      consumer exists and :494 is only part of the coupling.
      Report each spot-check verbatim — no partial-alignment
      handwave.

Rules: observation-only, gates before + after, no engine changes.
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

# ── Style buckets (fixed here for reporting) ───────────────────────
STRIKER_STYLES = {"Striker", "Counter Striker", "Pressure Fighter",
                  "Point Fighter", "Muay Thai"}
GRAPPLER_STYLES = {"Wrestler", "Ground & Pound", "BJJ Specialist",
                   "Clinch Fighter"}

def style_bucket(s):
    if s in STRIKER_STYLES: return "S"
    if s in GRAPPLER_STYLES: return "G"
    return "H"

def matchup(s1, s2):
    b1, b2 = style_bucket(s1), style_bucket(s2)
    key = tuple(sorted([b1, b2]))
    return {("S","S"):"SxS", ("G","G"):"GxG", ("G","S"):"SxG",
            ("H","S"):"SxH", ("G","H"):"GxH", ("H","H"):"HxH"}[key]

def classify(method):
    if not method: return "OTHER"
    m = method.strip()
    if m == "Draw": return "DRAW"
    if "Decision" in m or m == "DEC": return "DEC"
    if m.startswith("Submission") or m == "SUB": return "SUB"
    if m.startswith("TKO"):
        if "Doctor" in m or "Cut" in m: return "TKO_DOCTOR"
        if "(" in m and ")" in m: return "TKO_STRIKES"  # includes specialties
        return "TKO_STRIKES"
    if m.startswith("KO"): return "KO"
    return "OTHER"

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

# ── Primitive-call trace (shared list) ─────────────────────────────
_trace = []
def _log(kind, **kw): _trace.append({"kind": kind, "seq": len(_trace), **kw})
def _summ(o):
    if o is None: return None
    if isinstance(o, (int, float, str, bool)): return o
    if hasattr(o, 'value'): return o.value
    if hasattr(o, 'fighter_id'): return f"F#{o.fighter_id[:8]}"
    if isinstance(o, (list, tuple)) and len(o) < 6: return [_summ(x) for x in o]
    return f"<{type(o).__name__}>"

def install_primitive_hooks(fe):
    orig_sa = fe.select_action
    orig_csd = fe.calculate_strike_damage
    orig_as = fe.attempt_submission
    def wrap_sa(*args, **kw):
        r = orig_sa(*args, **kw)
        actor = args[0] if args else kw.get("fighter")
        pos = args[3] if len(args) > 3 else kw.get("position")
        is_top = args[4] if len(args) > 4 else kw.get("is_top")
        _log("select_action", actor=_summ(actor), pos=_summ(pos),
             is_top=_summ(is_top), action=_summ(r))
        return r
    def wrap_csd(*args, **kw):
        r = orig_csd(*args, **kw)
        _log("calc_damage",
             damage=(round(float(r), 3) if isinstance(r, (int, float)) else _summ(r)))
        return r
    def wrap_as(*args, **kw):
        r = orig_as(*args, **kw)
        _log("attempt_sub", result=_summ(r))
        return r
    fe.select_action = wrap_sa
    fe.calculate_strike_damage = wrap_csd
    fe.attempt_submission = wrap_as
    import fight_integration as fi
    fi_orig = {}
    for name, wrapped in [("select_action", wrap_sa),
                          ("calculate_strike_damage", wrap_csd),
                          ("attempt_submission", wrap_as)]:
        if hasattr(fi, name):
            fi_orig[name] = getattr(fi, name)
            setattr(fi, name, wrapped)
    def restore():
        fe.select_action = orig_sa
        fe.calculate_strike_damage = orig_csd
        fe.attempt_submission = orig_as
        for name, orig in fi_orig.items():
            setattr(fi, name, orig)
    return restore

# ── Run one fight — FE aligned OR unaligned, plus FI ──────────────
def run_pair(fixture_fight, seed, fe_align):
    """Return {fe_method, fi_method, fe_trace, fi_trace} or None."""
    import fight_engine as fe
    import fight_integration as fi

    fa1 = rebuild_fa(fixture_fight.get("fa1", {}), fe)
    fa2 = rebuild_fa(fixture_fight.get("fa2", {}), fe)
    if not fa1 or not fa2:
        return None

    rounds = fixture_fight.get("rounds", 3)
    is_title = fixture_fight.get("source_is_title_fight", False)
    is_main = fixture_fight.get("is_main_event", False)

    # ── FE run ────────────────────────────────────────────────────
    _trace.clear()
    restore = install_primitive_hooks(fe)
    try:
        fe_cfg = fe.FightConfig.championship_fight() if is_title else fe.FightConfig.standard_fight()
        if rounds == 5 and not is_title:
            fe_cfg = replace(fe_cfg, scheduled_rounds=5)
        random.seed(seed)
        if fe_align == 1:
            # W2-1-DRAW: mirror fight_integration.py:494 only.
            _ = random.getrandbits(64)
        elif fe_align == 3:
            # W2-3-DRAW: mirror :494 + :640 + :641 (initiative rolls).
            # random.randint(-10, 10) advances main random state ~2x per call
            # via getrandbits internally, but the FI order is:
            #   :494 getrandbits(64)  → 1 "logical" draw
            #   :640 randint(-10, 10) → 1 randint call
            #   :641 randint(-10, 10) → 1 randint call
            # Mirror exactly to preserve state advancement.
            _ = random.getrandbits(64)
            _ = random.randint(-10, 10)
            _ = random.randint(-10, 10)
        with contextlib.redirect_stdout(io.StringIO()):
            fe_result = fe.simulate_fight(fa1, fa2, fe_cfg, heat_level=0)
    finally:
        restore()
    fe_trace = list(_trace)

    # ── FI run ────────────────────────────────────────────────────
    _trace.clear()
    restore = install_primitive_hooks(fe)
    try:
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
        "fe_method": fe_result.method or "",
        "fi_method": fi_result.method or "",
        "fe_finish_round": fe_result.finish_round,
        "fi_finish_round": fi_result.finish_round,
        "fe_trace": fe_trace,
        "fi_trace": fi_trace,
    }

def first_divergence(t1, t2):
    minlen = min(len(t1), len(t2))
    for i in range(minlen):
        if t1[i] != t2[i]:
            return (i, t1[i], t2[i])
    if len(t1) != len(t2):
        return (minlen,
                t1[minlen] if len(t1) > minlen else "END",
                t2[minlen] if len(t2) > minlen else "END")
    return None

def matrix_from_results(results):
    """Aggregate + per-matchup finish rate."""
    per_mb = defaultdict(lambda: {"n":0, "finish":0, "dec":0, "tko_str":0, "tko_doc":0, "ko":0, "sub":0, "drw":0})
    agg = {"n":0, "finish":0, "dec":0, "tko_str":0, "tko_doc":0, "ko":0, "sub":0, "drw":0}
    for r in results:
        cls = classify(r["method"])
        mb = r["mb"]
        for target in (agg, per_mb[mb]):
            target["n"] += 1
            if cls in ("KO", "TKO_STRIKES", "TKO_DOCTOR", "SUB"): target["finish"] += 1
            if cls == "DEC": target["dec"] += 1
            if cls == "TKO_STRIKES": target["tko_str"] += 1
            if cls == "TKO_DOCTOR": target["tko_doc"] += 1
            if cls == "KO": target["ko"] += 1
            if cls == "SUB": target["sub"] += 1
            if cls == "DRAW": target["drw"] += 1
    return agg, per_mb

def pct(a, b): return f"{100*a/b:.1f}%" if b else "—"

def main():
    fx = json.load(open(FIXTURE))
    fights = fx["fights"]

    print("=" * 100)
    print("STAGE 1 — RANDOM-PARITY TRACE")
    print(f"  fixture: seed=42 baseline, N={len(fights)}")
    print("  hypothesis: alignment closes SOME of the 41pp; residual is the four FI-only accumulators")
    print("=" * 100)
    print()

    # ── Run four passes: unaligned, 1-draw offset, 3-draw offset, FI ─
    fe_unaligned_results = []
    fe_1draw_results = []
    fe_3draw_results = []
    fi_results = []
    divergence_indices_unaligned = []
    divergence_indices_1draw = []
    divergence_indices_3draw = []
    misses = 0

    decision_candidates = []  # W2 spot-check

    print("...running FE unaligned, FE +1draw, FE +3draw, FI per fight", file=sys.stderr)

    for i, f in enumerate(fights):
        s1 = (f.get("fa1") or {}).get("fighting_style")
        s2 = (f.get("fa2") or {}).get("fighting_style")
        if not s1 or not s2:
            misses += 1
            continue
        mb = matchup(s1, s2)

        # Unaligned FE + FI
        r_u = run_pair(f, seed=1000+i, fe_align=0)
        if r_u is None:
            misses += 1
            continue
        fe_unaligned_results.append({"method": r_u["fe_method"], "mb": mb})
        fi_results.append({"method": r_u["fi_method"], "mb": mb})
        d = first_divergence(r_u["fe_trace"], r_u["fi_trace"])
        divergence_indices_unaligned.append(d[0] if d else None)

        # 1-draw offset (original hypothesis: only :494)
        r_1 = run_pair(f, seed=1000+i, fe_align=1)
        fe_1draw_results.append({"method": r_1["fe_method"], "mb": mb})
        d1 = first_divergence(r_1["fe_trace"], r_1["fi_trace"])
        divergence_indices_1draw.append(d1[0] if d1 else None)

        # 3-draw offset (:494 + :640 + :641)
        r_3 = run_pair(f, seed=1000+i, fe_align=3)
        fe_3draw_results.append({"method": r_3["fe_method"], "mb": mb})
        d3 = first_divergence(r_3["fe_trace"], r_3["fi_trace"])
        divergence_indices_3draw.append(d3[0] if d3 else None)

        # Track DEC-vs-DEC for W2 (from 3-draw run — the "full" alignment attempt)
        fi_cls = classify(r_3["fi_method"])
        fe_cls = classify(r_3["fe_method"])
        if fi_cls == "DEC" and fe_cls == "DEC":
            decision_candidates.append({
                "fight_idx": i, "matchup": mb,
                "fi_method": r_3["fi_method"], "fe_method": r_3["fe_method"],
                "aligned_divergence_1": d1,
                "aligned_divergence_3": d3,
                "fi_trace_len": len(r_3["fi_trace"]),
                "fe_3draw_trace_len": len(r_3["fe_trace"]),
            })

    print(f"[measurement] traced fights: {len(fe_unaligned_results)}, misses: {misses}")
    print()

    # ── Aggregate + per-matchup matrices ──────────────────────────
    fe_u_agg, fe_u_mb = matrix_from_results(fe_unaligned_results)
    fe_1_agg, fe_1_mb = matrix_from_results(fe_1draw_results)
    fe_3_agg, fe_3_mb = matrix_from_results(fe_3draw_results)
    fi_agg, fi_mb = matrix_from_results(fi_results)

    print("=" * 100)
    print("RESULT 1 — aggregate finish rate (unaligned / +1draw / +3draw / FI)")
    print("=" * 100)
    fi_fin = 100*fi_agg["finish"]/fi_agg["n"] if fi_agg["n"] else 0
    fe_u_fin = 100*fe_u_agg["finish"]/fe_u_agg["n"] if fe_u_agg["n"] else 0
    fe_1_fin = 100*fe_1_agg["finish"]/fe_1_agg["n"] if fe_1_agg["n"] else 0
    fe_3_fin = 100*fe_3_agg["finish"]/fe_3_agg["n"] if fe_3_agg["n"] else 0
    print(f"  FI (live-play):      {fi_fin:.1f}%   (N={fi_agg['n']})")
    print(f"  FE unaligned:        {fe_u_fin:.1f}%   (N={fe_u_agg['n']})")
    print(f"  FE +1-draw offset:   {fe_1_fin:.1f}%   (N={fe_1_agg['n']})   — mirrors :494 only")
    print(f"  FE +3-draw offset:   {fe_3_fin:.1f}%   (N={fe_3_agg['n']})   — mirrors :494 + :640 + :641")
    print()
    print(f"  Baseline gap (FI - FE_unaligned): {fi_fin - fe_u_fin:+.1f}pp")
    print(f"  After +1-draw offset:             {fi_fin - fe_1_fin:+.1f}pp  (closed {(fi_fin-fe_u_fin)-(fi_fin-fe_1_fin):+.1f}pp)")
    print(f"  After +3-draw offset:             {fi_fin - fe_3_fin:+.1f}pp  (closed {(fi_fin-fe_u_fin)-(fi_fin-fe_3_fin):+.1f}pp)")
    print()
    residual_1 = fi_fin - fe_1_fin
    residual_3 = fi_fin - fe_3_fin
    print(f"  RESIDUAL after +1-draw: {residual_1:+.1f}pp")
    print(f"  RESIDUAL after +3-draw: {residual_3:+.1f}pp")
    print(f"  → Stage 2a target = residual under BEST alignment attempt")
    print()

    # W1: TKO-strikes reconciliation
    print("=" * 100)
    print("W1 — TKO-strikes reconciliation across aligned/unaligned")
    print("=" * 100)
    print("  If alignment closes 'too much' AND TKO-strikes gap remains huge, one is wrong.")
    print()
    fi_tko = 100 * fi_agg["tko_str"] / fi_agg["n"]
    fe_u_tko = 100 * fe_u_agg["tko_str"] / fe_u_agg["n"]
    fe_1_tko = 100 * fe_1_agg["tko_str"] / fe_1_agg["n"]
    fe_3_tko = 100 * fe_3_agg["tko_str"] / fe_3_agg["n"]
    print(f"  TKO-strikes rate:")
    print(f"    FI:                 {fi_tko:.1f}%")
    print(f"    FE unaligned:       {fe_u_tko:.1f}%  (gap {fi_tko - fe_u_tko:+.1f}pp)")
    print(f"    FE +1-draw:         {fe_1_tko:.1f}%  (gap {fi_tko - fe_1_tko:+.1f}pp)")
    print(f"    FE +3-draw:         {fe_3_tko:.1f}%  (gap {fi_tko - fe_3_tko:+.1f}pp)")
    print()
    print(f"  → TKO-strikes residual under best alignment: {fi_tko - fe_3_tko:+.1f}pp (mechanic gap)")
    print()
    print("  Reconciliation check: if aggregate closure ≫ TKO-strikes residual,")
    print("  the accumulator story would be undermined. If they line up, both hold.")

    # ── Per-matchup residual ──────────────────────────────────────
    print()
    print("=" * 100)
    print("Per-matchup residual (FI - FE_aligned)")
    print("=" * 100)
    for mb_name in ("SxS", "GxG", "SxG", "SxH", "GxH", "HxH"):
        fu = fe_u_mb.get(mb_name, {"n":0,"finish":0})
        f1 = fe_1_mb.get(mb_name, {"n":0,"finish":0})
        f3 = fe_3_mb.get(mb_name, {"n":0,"finish":0})
        ff = fi_mb.get(mb_name, {"n":0,"finish":0})
        if ff["n"] == 0: continue
        fi_p = 100*ff["finish"]/ff["n"]
        fu_p = 100*fu["finish"]/fu["n"] if fu["n"] else 0
        f1_p = 100*f1["finish"]/f1["n"] if f1["n"] else 0
        f3_p = 100*f3["finish"]/f3["n"] if f3["n"] else 0
        thin = "⚠THIN" if ff["n"] < 5 else ""
        print(f"  {mb_name:>4} (N={ff['n']:>3}): FI={fi_p:5.1f}%  FE_u={fu_p:5.1f}%  FE_+1={f1_p:5.1f}%  FE_+3={f3_p:5.1f}%  "
              f"residual_+3={fi_p-f3_p:+.1f}pp  {thin}")

    # ── Divergence index shift ────────────────────────────────────
    print()
    print("=" * 100)
    print("Trace-alignment check — first-divergence-index shift after offset")
    print("=" * 100)
    ident_u = sum(1 for x in divergence_indices_unaligned if x is None)
    ident_1 = sum(1 for x in divergence_indices_1draw if x is None)
    ident_3 = sum(1 for x in divergence_indices_3draw if x is None)
    print(f"  identical primitive sequences:")
    print(f"    unaligned:      {ident_u}/{len(divergence_indices_unaligned)}")
    print(f"    +1-draw offset: {ident_1}/{len(divergence_indices_1draw)}")
    print(f"    +3-draw offset: {ident_3}/{len(divergence_indices_3draw)}")

    # ── W2: spot-check three decision fights ──────────────────────
    print()
    print("=" * 100)
    print("W2 — SPOT-CHECK: 3 decision-ending fights, primitive sequences after alignment")
    print("=" * 100)
    print("  Failure mode Van flagged: if a DEC-vs-DEC fight (no FI-only accumulator hit)")
    print("  does NOT align exchange-for-exchange after single-draw offset, there's a")
    print("  SECOND FI-only random consumer we haven't found. Don't handwave.")
    print()
    if len(decision_candidates) == 0:
        print("  no DEC-vs-DEC fights to spot-check — parity trace inconclusive on W2")
    else:
        picks = decision_candidates[:3]
        for pk in picks:
            d1 = pk["aligned_divergence_1"]
            d3 = pk["aligned_divergence_3"]
            print(f"  fight[{pk['fight_idx']}] matchup={pk['matchup']} FI={pk['fi_method']} FE={pk['fe_method']}")
            print(f"    fi_trace_len={pk['fi_trace_len']}  fe_+3_trace_len={pk['fe_3draw_trace_len']}")
            for label, d in [("+1-draw", d1), ("+3-draw", d3)]:
                if d is None:
                    print(f"    ✓ {label}: IDENTICAL primitive sequences")
                else:
                    idx, a, b = d
                    print(f"    ✗ {label}: diverges at call {idx}")
                    if isinstance(a, dict) and isinstance(b, dict):
                        if a.get('actor') != b.get('actor'):
                            print(f"       FE actor: {a.get('actor')}  ≠  FI actor: {b.get('actor')}  ← DIFFERENT FIGHTER selected")
                        elif a.get('action') != b.get('action'):
                            print(f"       same actor, FE action: {a.get('action')}  ≠  FI action: {b.get('action')}")
            print()

    # ── W2 summary ────────────────────────────────────────────────
    print()
    print("=" * 100)
    print("W2 SUMMARY — decision-fight alignment across the fixture")
    print("=" * 100)
    dec_1_ident = sum(1 for pk in decision_candidates if pk["aligned_divergence_1"] is None)
    dec_3_ident = sum(1 for pk in decision_candidates if pk["aligned_divergence_3"] is None)
    print(f"  DEC-vs-DEC pairs total: {len(decision_candidates)}")
    print(f"    identical after +1-draw offset: {dec_1_ident}/{len(decision_candidates)}")
    print(f"    identical after +3-draw offset: {dec_3_ident}/{len(decision_candidates)}")
    if dec_3_ident == len(decision_candidates) and len(decision_candidates) > 0:
        print(f"  ✓ +3-draw offset EXPLAINS coupling on non-accumulator fights.")
        print(f"    Full random-state coupling: :494 + :640 + :641. Nothing else needed.")
    elif dec_3_ident > dec_1_ident:
        print(f"  ⚠ +3-draw improves over +1-draw ({dec_1_ident} → {dec_3_ident}) but doesn't close it fully.")
        print(f"    :494 + :640 + :641 are PART of coupling; MORE consumers still exist.")
    elif dec_3_ident == dec_1_ident:
        print(f"  ⚠ +3-draw doesn't improve over +1-draw. Alignment approach is wrong or")
        print(f"    the additional draws don't advance state the way I modeled them.")
        print(f"    Possible: FE also consumes randoms at init that offset the offset.")

if __name__ == "__main__":
    main()
