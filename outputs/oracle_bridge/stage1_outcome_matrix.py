"""STAGE 1 — OUTCOME MATRIX. READ-ONLY.

Reads outputs/oracle_bridge/fixture.json (78 fights, seed=42) to compute
the live-play outcome surface, then re-runs the SAME fighter matchups
through fight_engine.simulate_fight (pre-gen path) with PRE_GEN_LEGACY
config to compute the pre-gen matrix on the same population.

Slices:
  - by method: KO / TKO-strikes / TKO-doctor / SUB / DEC / Draw
  - by round of finish
  - by style matchup: striker-v-striker / striker-v-grappler / grappler-v-grappler / (hybrid-involved)
  - by title vs non-title (5R vs 3R)

N per cell reported; thin cells flagged. No tuning proposed.
No engine touched.
"""
import _common  # noqa: F401 — sys.path + uuid patch + seed setup
import io
import json
import os
import random
import contextlib
import sys
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(_HERE, "fixture.json")

# ── Style family taxonomy (from cage_dynasty_web/styles.py:517-527) ──
STRIKER_STYLES = {"Striker", "Counter Striker", "Pressure Fighter",
                  "Point Fighter", "Muay Thai"}
GRAPPLER_STYLES = {"Wrestler", "Ground & Pound", "BJJ Specialist",
                   "Clinch Fighter"}
HYBRID_STYLES = {"Sprawl & Brawl", "Balanced"}

def style_bucket(style):
    if style in STRIKER_STYLES:
        return "S"  # striker
    if style in GRAPPLER_STYLES:
        return "G"  # grappler
    return "H"  # hybrid

def matchup_bucket(s1, s2):
    b1, b2 = style_bucket(s1), style_bucket(s2)
    # Canonicalize (S,G)==(G,S) etc.
    key = tuple(sorted([b1, b2]))
    return {
        ("S", "S"): "SxS",
        ("G", "G"): "GxG",
        ("G", "S"): "SxG",
        ("H", "S"): "SxH",
        ("G", "H"): "GxH",
        ("H", "H"): "HxH",
    }[key]

# ── Method classification ──────────────────────────────────────────
def classify_method(method, specialty_method=None, event_log_repr=None):
    """Return one of: KO, TKO_STRIKES, TKO_DOCTOR, SUB, DEC, DRAW, OTHER."""
    if not method:
        return "OTHER"
    m = method.strip()
    if m == "Draw":
        return "DRAW"
    if m.startswith("Decision") or m == "DEC" or "DEC" in m.upper():
        return "DEC"
    if m.startswith("Submission") or m == "SUB":
        return "SUB"
    if m.startswith("KO") and "TKO" not in m:
        return "KO"
    if m == "KO":
        return "KO"
    if m.startswith("TKO") or m == "TKO":
        # Distinguish doctor stoppage: engine sets method to "TKO (Doctor Stoppage - Cut)"
        # or specialty_method carries "Doctor" or similar
        if specialty_method and ("Doctor" in str(specialty_method) or "Cut" in str(specialty_method)):
            return "TKO_DOCTOR"
        if "Doctor" in m or "Cut" in m:
            return "TKO_DOCTOR"
        return "TKO_STRIKES"
    return "OTHER"

# ── Cell aggregator ────────────────────────────────────────────────
def new_agg():
    return {
        "n": 0,
        "methods": Counter(),
        "finish_rounds": Counter(),
        "sub_attempts_total": 0,
        "sub_landed_total": 0,  # count of SUB-method fights
        "cuts_stopped": 0,      # count of TKO_DOCTOR
        "damage_per_exchange_samples": [],
    }

def collect(agg, method_class, finish_round, sub_atts, damage_samples, is_doctor):
    agg["n"] += 1
    agg["methods"][method_class] += 1
    if method_class in ("KO", "TKO_STRIKES", "TKO_DOCTOR", "SUB"):
        agg["finish_rounds"][finish_round or 0] += 1
    if method_class == "SUB":
        agg["sub_landed_total"] += 1
    if is_doctor:
        agg["cuts_stopped"] += 1
    agg["sub_attempts_total"] += sub_atts
    agg["damage_per_exchange_samples"].extend(damage_samples)

# ── LIVE-PLAY extraction from fixture ──────────────────────────────
def extract_live_play():
    fx = json.load(open(FIXTURE))
    cells = defaultdict(new_agg)  # (matchup, title_bucket) → agg
    all_cell = new_agg()
    for f in fx["fights"]:
        er = f.get("engine_result", {})
        method = er.get("method", "")
        finish_round = er.get("finish_round", 0)
        fa1 = f.get("fa1", {}) or {}
        fa2 = f.get("fa2", {}) or {}
        style1 = fa1.get("fighting_style")
        style2 = fa2.get("fighting_style")
        if not style1 or not style2:
            continue  # can't slice
        mb = matchup_bucket(style1, style2)
        # Title from source-of-truth field (Path A doesn't pass is_title_fight kwarg —
        # ORACLE-BRIDGE1 enrichment reads it from _completed_events)
        is_title = f.get("source_is_title_fight", False)
        # Also 5R vs 3R: rounds passed via kwarg is our source
        rounds = f.get("rounds", 3)
        title_bucket = "5R" if rounds == 5 else "3R"

        # Sub attempts + damage per exchange from per-round stats
        sub_atts = 0
        damages = []
        for side_stats in (er.get("fighter1_stats") or [], er.get("fighter2_stats") or []):
            for rs in side_stats:
                sub_atts += int(rs.get("sub_att", 0) or 0)
                damages.append(rs.get("damage", 0) or 0)

        # Doctor stoppage classification — live-play's method may embed "Doctor" or "Cut"
        # or specialty_method may carry it. Fall back: TKO with cut context if available.
        method_class = classify_method(method)
        is_doctor = (method_class == "TKO_DOCTOR")
        # Since we don't have specialty_method here, TKO_DOCTOR from fixture will be rare —
        # noting so the reader knows this is method-string based.

        cells[(mb, title_bucket)].__setitem__  # noqa
        collect(cells[(mb, title_bucket)], method_class, finish_round, sub_atts, damages, is_doctor)
        collect(all_cell, method_class, finish_round, sub_atts, damages, is_doctor)
    return cells, all_cell

# ── PRE-GEN re-run through fight_engine.simulate_fight ─────────────
def reconstruct_fighter_attrs(fa_dict, fight_engine):
    """Given the fixture's fa1/fa2 dict, rebuild a FighterAttributes."""
    from dataclasses import fields
    valid_keys = {fld.name for fld in fields(fight_engine.FighterAttributes)}
    kwargs = {k: v for k, v in fa_dict.items() if k in valid_keys}
    # Handle enum-encoded fighting_style — fixture stores it as string "Muay Thai" etc.
    # FightingStyle lives in styles module, not fight_engine.
    style = kwargs.get("fighting_style")
    if style and isinstance(style, str):
        try:
            from styles import FightingStyle
            matched = None
            for m in FightingStyle:
                if m.value == style:
                    matched = m
                    break
            kwargs["fighting_style"] = matched
        except Exception:
            kwargs["fighting_style"] = None
    try:
        return fight_engine.FighterAttributes(**kwargs)
    except TypeError:
        return None

def extract_pregen():
    """Re-run each fight through fight_engine.simulate_fight (pre-gen path)."""
    import fight_engine as fe
    cells = defaultdict(new_agg)
    all_cell = new_agg()
    fx = json.load(open(FIXTURE))
    misses = 0
    for i, f in enumerate(fx["fights"]):
        fa1_dict = f.get("fa1") or {}
        fa2_dict = f.get("fa2") or {}
        fa1 = reconstruct_fighter_attrs(fa1_dict, fe)
        fa2 = reconstruct_fighter_attrs(fa2_dict, fe)
        if not fa1 or not fa2:
            misses += 1
            continue
        style1 = fa1_dict.get("fighting_style")
        style2 = fa2_dict.get("fighting_style")
        if not style1 or not style2:
            misses += 1
            continue
        mb = matchup_bucket(style1, style2)
        is_title = f.get("source_is_title_fight", False)
        rounds = f.get("rounds", 3)
        title_bucket = "5R" if rounds == 5 else "3R"

        # Pre-gen config: standard or championship. Same rounds.
        cfg = fe.FightConfig.championship_fight() if is_title else fe.FightConfig.standard_fight()
        if rounds == 5 and not is_title:
            # Non-title main/co_main gets 5R (world_init would also override)
            from dataclasses import replace
            cfg = replace(cfg, scheduled_rounds=5)

        # Seed each simulation deterministically from fight index
        random.seed(1000 + i)
        with contextlib.redirect_stdout(io.StringIO()):
            r = fe.simulate_fight(fa1, fa2, cfg, heat_level=0)

        method = r.method or ""
        finish_round = r.finish_round or 0
        method_class = classify_method(method)
        is_doctor = (method_class == "TKO_DOCTOR")

        # Sub attempts + damage per round
        sub_atts = 0
        damages = []
        for rs_list in (r.fighter1_stats or [], r.fighter2_stats or []):
            for rs in rs_list:
                # RoundStats may be object or dict
                if isinstance(rs, dict):
                    sub_atts += int(rs.get("sub_att", 0) or 0)
                    damages.append(rs.get("damage", 0) or 0)
                else:
                    sub_atts += int(getattr(rs, "submission_attempts", 0) or 0)
                    damages.append(getattr(rs, "damage", 0) or 0)

        collect(cells[(mb, title_bucket)], method_class, finish_round, sub_atts, damages, is_doctor)
        collect(all_cell, method_class, finish_round, sub_atts, damages, is_doctor)
    return cells, all_cell, misses

# ── Reporting ──────────────────────────────────────────────────────
def fmt_pct(n, d):
    if d == 0:
        return "  —  "
    return f"{100*n/d:5.1f}%"

def fmt_agg_line(label, agg):
    n = agg["n"]
    if n == 0:
        return f"{label:<10} N=0     — no fights in this cell —"
    m = agg["methods"]
    ko = m.get("KO", 0)
    tko_s = m.get("TKO_STRIKES", 0)
    tko_d = m.get("TKO_DOCTOR", 0)
    sub = m.get("SUB", 0)
    dec = m.get("DEC", 0)
    draw = m.get("DRAW", 0)
    finish_n = ko + tko_s + tko_d + sub
    return (f"{label:<10} N={n:<3}  "
            f"KO {fmt_pct(ko,n)}  TKO {fmt_pct(tko_s,n)}  DOC {fmt_pct(tko_d,n)}  "
            f"SUB {fmt_pct(sub,n)}  DEC {fmt_pct(dec,n)}  DRW {fmt_pct(draw,n)}  "
            f"finish {fmt_pct(finish_n,n)}")

def report_matrix(name, cells, all_cell):
    print(f"\n{'='*90}")
    print(f"{name}")
    print(f"{'='*90}")
    print(fmt_agg_line("AGGREGATE", all_cell))
    print()
    print("Sliced by matchup × rounds (N per cell):")
    print("-" * 90)
    order = [("SxS", "striker-v-striker"), ("SxG", "striker-v-grappler"),
             ("GxG", "grappler-v-grappler"), ("SxH", "striker-v-hybrid"),
             ("GxH", "grappler-v-hybrid"), ("HxH", "hybrid-v-hybrid")]
    for mb, mb_name in order:
        for tb in ("3R", "5R"):
            agg = cells.get((mb, tb), new_agg())
            label = f"{mb_name[:12]:<12} {tb}"
            if agg["n"] == 0:
                continue
            marker = " ⚠️THIN" if agg["n"] < 5 else ""
            print(f"  {fmt_agg_line(label, agg)}{marker}")
    print()

    # Sub attempts vs conversions
    print("Submissions — attempts vs conversions:")
    all_atts = all_cell["sub_attempts_total"]
    all_land = all_cell["sub_landed_total"]
    print(f"  AGG: attempts={all_atts}   landed={all_land}   conv={fmt_pct(all_land, all_atts)}")
    for mb, mb_name in order:
        for tb in ("3R", "5R"):
            agg = cells.get((mb, tb), new_agg())
            if agg["n"] == 0:
                continue
            a = agg["sub_attempts_total"]
            l = agg["sub_landed_total"]
            print(f"  {mb_name[:12]:<12} {tb} — attempts={a:<4} landed={l:<3} conv={fmt_pct(l,a)}")
    print()

    # Damage per exchange distribution (aggregate only — thin per cell)
    damages = all_cell["damage_per_exchange_samples"]
    if damages:
        damages_sorted = sorted(damages)
        n = len(damages_sorted)
        avg = sum(damages_sorted) / n
        median = damages_sorted[n // 2]
        p90 = damages_sorted[int(n * 0.9)]
        max_d = damages_sorted[-1]
        print(f"Damage per round (samples across all fighters, aggregate):")
        print(f"  N={n}  avg={avg:.2f}  median={median:.2f}  p90={p90:.2f}  max={max_d:.2f}")
    print()

    # Cut / doctor stoppage share of finishes
    doc = all_cell["cuts_stopped"]
    total_finishes = sum(all_cell["methods"].get(m, 0) for m in ("KO", "TKO_STRIKES", "TKO_DOCTOR", "SUB"))
    print(f"Doctor stoppages / cut-stopped TKOs:")
    print(f"  AGG: {doc} of {total_finishes} finishes ({fmt_pct(doc, total_finishes)})")

def main():
    print("=" * 90)
    print("STAGE 1 — OUTCOME MATRIX")
    print("Source: outputs/oracle_bridge/fixture.json (seed=42, 78 fights)")
    print("=" * 90)

    live_cells, live_all = extract_live_play()
    print(f"\n[measurement] live-play captures: N={live_all['n']}")
    report_matrix("LIVE-PLAY (fight_integration.simulate_narrated_fight)", live_cells, live_all)

    print()
    print("─" * 90)
    print("Re-running same matchups through PRE-GEN engine "
          "(fight_engine.simulate_fight, PRE_GEN_LEGACY config = 55/0.42/6)")
    print("─" * 90)
    pregen_cells, pregen_all, misses = extract_pregen()
    if misses:
        print(f"\n[measurement] pre-gen misses (couldn't reconstruct FighterAttributes): {misses}")
    print(f"[measurement] pre-gen captures: N={pregen_all['n']}")
    report_matrix("PRE-GEN (fight_engine.simulate_fight, standard/championship config)",
                  pregen_cells, pregen_all)

    # Side-by-side finish rate summary
    print()
    print("=" * 90)
    print("SIDE-BY-SIDE — finish rate by matchup (both tiers combined)")
    print("=" * 90)
    print(f"{'matchup':<24} {'live_N':>8} {'live_fin%':>10} {'pregen_N':>10} {'pregen_fin%':>12}  Δ")
    for mb, mb_name in [("SxS", "striker-v-striker"),
                        ("SxG", "striker-v-grappler"),
                        ("GxG", "grappler-v-grappler"),
                        ("SxH", "striker-v-hybrid"),
                        ("GxH", "grappler-v-hybrid"),
                        ("HxH", "hybrid-v-hybrid")]:
        live_n = sum(live_cells.get((mb, tb), new_agg())["n"] for tb in ("3R", "5R"))
        pregen_n = sum(pregen_cells.get((mb, tb), new_agg())["n"] for tb in ("3R", "5R"))
        def combo_finish(cells_dict):
            n = 0; fin = 0
            for tb in ("3R", "5R"):
                a = cells_dict.get((mb, tb), new_agg())
                n += a["n"]
                for m in ("KO", "TKO_STRIKES", "TKO_DOCTOR", "SUB"):
                    fin += a["methods"].get(m, 0)
            return n, fin
        ln, lf = combo_finish(live_cells)
        pn, pf = combo_finish(pregen_cells)
        live_pct = f"{100*lf/ln:.1f}%" if ln else "—"
        pg_pct = f"{100*pf/pn:.1f}%" if pn else "—"
        try:
            delta = f"{100*lf/ln - 100*pf/pn:+.1f}pp"
        except ZeroDivisionError:
            delta = "—"
        thin = " ⚠️THIN" if (ln < 5 or pn < 5) else ""
        print(f"  {mb_name:<24} {live_n:>8} {live_pct:>10} {pregen_n:>10} {pg_pct:>12}  {delta}{thin}")

    print()
    print("Note: THIN = cell has N<5. Per-cell finish rates on thin cells are noise, not signal.")
    print("Note: TKO_DOCTOR classification here is method-string based. Live-play method")
    print("      strings may not embed 'Doctor'/'Cut' — the real signal for doctor stoppages")
    print("      is in the engine result's specialty_method or event_log, which the fixture")
    print("      does not currently capture as a distinct field. Filed for follow-up.")

if __name__ == "__main__":
    main()
