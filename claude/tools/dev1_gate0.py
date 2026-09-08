"""DEVELOPMENT1 Gate 0 baseline — read-only harness."""

import argparse
import copy
import csv
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

# Env prep BEFORE any project import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness_env  # noqa: F401


STATS_19 = [
    "strength", "speed", "cardio", "chin", "recovery", "power",
    "boxing", "kicks", "clinch_striking", "striking_defense",
    "takedowns", "takedown_defense", "top_control", "submissions",
    "guard", "clinch_control", "heart", "fight_iq", "composure",
]

CONDITION_LABEL_5 = [  # game_bridge.py:7397-7406
    (20, "Fresh"), (40, "Rested"), (60, "Ready"),
    (80, "Tired"), (100, "Exhausted"),
]


def condition_label_5(fatigue: int) -> str:
    for limit, label in CONDITION_LABEL_5:
        if fatigue <= limit:
            return label
    return "Exhausted"


def _boot_bridge(seed: int):
    import random
    random.seed(seed)
    from game_bridge import GameBridge
    from game_start import generate_starting_prospects
    prospects = generate_starting_prospects(player_region="Americas")
    p = prospects[0]
    fighter_dict = {
        "id": p.prospect_id, "name": p.name,
        "nickname": getattr(p, "nickname", None),
        "age": p.age, "country": p.country,
        "weight_class": p.weight_class,
        "style": p.fighting_style,
        "overall": p.overall_rating,
        "potential": p.potential_ceiling,
        "traits": getattr(p, "traits", []),
        "strength": p.strength, "speed": p.speed, "cardio": p.cardio,
        "chin": p.chin, "recovery": p.recovery,
        "boxing": p.boxing, "kicks": p.kicks,
        "clinch_striking": p.clinch_striking,
        "striking_defense": p.striking_defense,
        "takedowns": p.takedowns, "takedown_defense": p.takedown_defense,
        "top_control": p.top_control, "submissions": p.submissions,
        "guard": p.guard, "clinch_control": p.clinch_control,
        "heart": p.heart, "fight_iq": p.fight_iq,
        "composure": p.composure,
    }
    coach_dict = {"id": "coach_1", "name": "Test Coach",
                  "specialty": "boxing", "rating": 65,
                  "traits": [], "cost": 500}
    bridge = GameBridge()
    bridge._user_id = f"harness_dev1_seed{seed}"
    ok = bridge.new_game("Harness Camp", "Las Vegas, NV",
                         "GARAGE", coach_dict, fighter_dict)
    if not ok:
        raise RuntimeError("new_game failed")
    return bridge


def _player_fid(bridge):
    pcid = bridge._game_state.player_camp_id
    for fid, f in bridge._game_state.fighters.items():
        if f.camp_id == pcid:
            return fid
    return None


def _read_stats(bridge, fid) -> Dict[str, int]:
    fd = bridge._game_state._fighter_data.get(fid, {})
    out = {}
    for s in STATS_19:
        out[s] = fd.get(s, 0)
    return out


def _read_fatigue(bridge, fid) -> int:
    return int(bridge._game_state._fighter_data.get(fid, {}).get("fatigue", 0))


def _read_ovr(bridge, fid) -> int:
    f = bridge._game_state.fighters.get(fid)
    return int(getattr(f, "overall_rating", 0)) if f else 0


def _read_last_autorest_news(bridge, fid, week) -> Optional[str]:
    """Scan news feed for training-category items about this fighter."""
    ftr_name = bridge._game_state.fighters.get(fid)
    if not ftr_name:
        return None
    name = ftr_name.name
    hits = []
    for n in bridge._news_items[:20]:  # feed is newest-first (insert(0))
        if n.get("category") != "training":
            continue
        if n.get("week") != week:
            continue
        h = n.get("headline", "")
        if name in h:
            hits.append(h)
    return hits[0] if hits else None


# ─────────────────────────────────────────────────────────────────────────────
# probe1_intensity_sweep
# ─────────────────────────────────────────────────────────────────────────────
def _snapshot_bridge_state(bridge):
    """Deep-copy the state needed to reset between intensity runs."""
    return {
        "fighter_data": copy.deepcopy(bridge._game_state._fighter_data),
        "fighters": {fid: (f.wins, f.losses, f.draws,
                            f.ko_wins, f.sub_wins,
                            f.overall_rating,
                            list(f.fight_history) if f.fight_history else [])
                     for fid, f in bridge._game_state.fighters.items()},
        "week": bridge._game_state.week_number,
        "training_plans": copy.deepcopy(bridge._fighter_training_plans),
        "scheduled_fights": copy.deepcopy(bridge._scheduled_fights),
        "fatigue_flags": {k: getattr(bridge, k)
                          for k in dir(bridge)
                          if k.startswith("_auto_resting_")},
    }


def _restore_bridge_state(bridge, snap):
    bridge._game_state._fighter_data = copy.deepcopy(snap["fighter_data"])
    for fid, tpl in snap["fighters"].items():
        f = bridge._game_state.fighters.get(fid)
        if f:
            (f.wins, f.losses, f.draws, f.ko_wins, f.sub_wins,
             f.overall_rating, hist) = tpl
            f.fight_history = list(hist)
    bridge._game_state.week_number = snap["week"]
    bridge._fighter_training_plans = copy.deepcopy(snap["training_plans"])
    bridge._scheduled_fights = copy.deepcopy(snap["scheduled_fights"])
    for k in list(dir(bridge)):
        if k.startswith("_auto_resting_"):
            try:
                delattr(bridge, k)
            except Exception:
                pass
    for k, v in snap["fatigue_flags"].items():
        setattr(bridge, k, v)


def probe1(seed: int, weeks: int, out_dir: str) -> Dict[str, Any]:
    """5 intensities × weeks. Reset to a shared start snapshot each run."""
    os.makedirs(out_dir, exist_ok=True)
    print(f"[probe1] booting bridge (seed={seed}, weeks={weeks})...")
    t0 = time.time()
    bridge = _boot_bridge(seed)
    print(f"[probe1] bridge booted in {time.time()-t0:.1f}s")
    pfid = _player_fid(bridge)
    ftr_obj = bridge._game_state.fighters[pfid]
    print(f"[probe1] player fighter: {ftr_obj.name} ({ftr_obj.weight_class})  fid={pfid[:8]}")

    snap = _snapshot_bridge_state(bridge)

    summary = {"seed": seed, "weeks": weeks, "player_fid": pfid,
               "player_name": ftr_obj.name, "intensities": {}}

    for intensity in ["REST", "LIGHT", "MODERATE", "INTENSE", "EXTREME"]:
        print(f"[probe1] --- intensity={intensity} ---")
        _restore_bridge_state(bridge, snap)
        bridge.set_training_plan(pfid, focus="sparring", intensity=intensity)

        rows = []
        # Week 0 snapshot BEFORE any advance
        f0 = _read_fatigue(bridge, pfid)
        ovr0 = _read_ovr(bridge, pfid)
        stats0 = _read_stats(bridge, pfid)
        rows.append({
            "week": 0, "intensity": intensity,
            "fatigue": f0, "condition_pct": 100 - f0,
            "condition_label": condition_label_5(f0),
            "ovr": ovr0, "auto_rest_fired": "",
            "auto_rest_reason": "",
            **{f"stat_{s}": stats0[s] for s in STATS_19},
        })

        auto_rests = []
        for w in range(1, weeks + 1):
            t_w = time.time()
            bridge.advance_week()
            f = _read_fatigue(bridge, pfid)
            ovr = _read_ovr(bridge, pfid)
            stats = _read_stats(bridge, pfid)
            news_line = _read_last_autorest_news(bridge, pfid,
                                                 bridge._game_state.week_number)
            # Detect any auto-rest signal — either the news line or a
            # setattr flag on the bridge.
            resting_flag = getattr(bridge, f"_auto_resting_{pfid}", False)
            reason = news_line or ""
            fired = bool(news_line) or bool(resting_flag)
            if fired and news_line:
                auto_rests.append((w, news_line))
                print(f"  wk{w:2d}  fatigue={f:2d}  ovr={ovr}  "
                      f"AUTO-REST FIRED: {news_line}")
            else:
                print(f"  wk{w:2d}  fatigue={f:2d}  ovr={ovr}  "
                      f"(advance: {time.time()-t_w:.1f}s)")
            rows.append({
                "week": w, "intensity": intensity,
                "fatigue": f, "condition_pct": 100 - f,
                "condition_label": condition_label_5(f),
                "ovr": ovr, "auto_rest_fired": "Y" if fired else "N",
                "auto_rest_reason": reason,
                **{f"stat_{s}": stats[s] for s in STATS_19},
            })

        # Write CSV
        csv_path = os.path.join(out_dir, f"sweep_{seed}_{intensity}.csv")
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)

        summary["intensities"][intensity] = {
            "csv": csv_path,
            "fatigue_start": rows[0]["fatigue"],
            "fatigue_end": rows[-1]["fatigue"],
            "fatigue_max": max(r["fatigue"] for r in rows),
            "fatigue_min": min(r["fatigue"] for r in rows),
            "ovr_start": rows[0]["ovr"],
            "ovr_end": rows[-1]["ovr"],
            "auto_rest_weeks": len(auto_rests),
            "auto_rest_events": auto_rests,
        }

    summary_path = os.path.join(out_dir, f"sweep_{seed}_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"[probe1] wrote {summary_path}")
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# probe2_ovr_attribution
# ─────────────────────────────────────────────────────────────────────────────
def probe2(seed: int, out_dir: str) -> Dict[str, Any]:
    """Week 0 -> 1 MODERATE. Full 19-stat dump + OVR recompute breakdown."""
    os.makedirs(out_dir, exist_ok=True)
    print(f"[probe2] booting bridge (seed={seed})...")
    bridge = _boot_bridge(seed)
    pfid = _player_fid(bridge)
    ftr_obj = bridge._game_state.fighters[pfid]

    bridge.set_training_plan(pfid, focus="sparring", intensity="MODERATE")

    # BEFORE
    stats_before = _read_stats(bridge, pfid)
    ovr_stored_before = _read_ovr(bridge, pfid)
    # Simple mean over 19 stats
    simple_mean_before = sum(stats_before[s] for s in STATS_19) / 19.0
    # Reuse the engine's own _compute_ovr against a synthetic fighter view
    ovr_computed_before = bridge._compute_ovr(ftr_obj)
    # stats_with_data (legacy-save guard at game_bridge.py:7876-7879)
    stats_with_data_before = sum(
        1 for s in STATS_19 if bridge._read_stat(ftr_obj, s) > 0)

    # Advance week 1
    print(f"[probe2] advance_week (MODERATE)...")
    t_w = time.time()
    bridge.advance_week()
    dt = time.time() - t_w
    print(f"[probe2] advance_week took {dt:.1f}s")

    # AFTER
    stats_after = _read_stats(bridge, pfid)
    ovr_stored_after = _read_ovr(bridge, pfid)
    simple_mean_after = sum(stats_after[s] for s in STATS_19) / 19.0
    ovr_computed_after = bridge._compute_ovr(ftr_obj)
    stats_with_data_after = sum(
        1 for s in STATS_19 if bridge._read_stat(ftr_obj, s) > 0)

    # Deltas
    deltas = {s: stats_after[s] - stats_before[s] for s in STATS_19}
    positive_deltas = {s: d for s, d in deltas.items() if d > 0}
    negative_deltas = {s: d for s, d in deltas.items() if d < 0}

    # Write markdown report
    md_path = os.path.join(out_dir, f"ovr_attribution_{seed}.md")
    with open(md_path, "w") as f:
        f.write(f"# DEV1 Gate 0 probe2_ovr_attribution — seed {seed}\n\n")
        f.write(f"Player fighter: **{ftr_obj.name}** "
                f"({ftr_obj.weight_class}, style={ftr_obj.fighting_style})\n")
        f.write(f"fid: `{pfid}`\n\n")
        f.write(f"## Legacy-save guard status (game_bridge.py:7876-7879)\n\n")
        f.write(f"- `stats_with_data_before` = **{stats_with_data_before}** "
                f"(guard fires if < 10)\n")
        f.write(f"- `stats_with_data_after`  = **{stats_with_data_after}**\n\n")
        f.write(f"## 19-stat dump\n\n")
        f.write(f"| Stat | Before | After | Δ |\n|---|---:|---:|---:|\n")
        for s in STATS_19:
            f.write(f"| {s} | {stats_before[s]} | {stats_after[s]} | "
                    f"{deltas[s]:+.2f} |\n")
        f.write(f"\n## OVR readings\n\n")
        f.write(f"| Reading | Before | After | Δ |\n|---|---:|---:|---:|\n")
        f.write(f"| `overall_rating` stored | {ovr_stored_before} | "
                f"{ovr_stored_after} | {ovr_stored_after - ovr_stored_before:+d} |\n")
        f.write(f"| `_compute_ovr()` recomputed | {ovr_computed_before} | "
                f"{ovr_computed_after} | "
                f"{ovr_computed_after - ovr_computed_before:+d} |\n")
        f.write(f"| Simple unweighted mean(19) | {simple_mean_before:.2f} | "
                f"{simple_mean_after:.2f} | "
                f"{simple_mean_after - simple_mean_before:+.2f} |\n")
        f.write(f"\n## Delta breakdown\n\n")
        f.write(f"- **Positive deltas** ({len(positive_deltas)}): "
                f"{positive_deltas}\n")
        f.write(f"- **Negative deltas** ({len(negative_deltas)}): "
                f"{negative_deltas}\n")
        f.write(f"- Zero-change stats: "
                f"{[s for s, d in deltas.items() if d == 0]}\n\n")
        f.write(f"## Interpretation\n\n")
        f.write(f"If `_compute_ovr` Δ ≠ stored `overall_rating` Δ, the store\n")
        f.write(f"was updated by a path other than the recompute this "
                f"probe reaches.\n")
        f.write(f"If simple-mean rose but weighted OVR fell, style-weight "
                f"redistribution is the culprit.\n")
        f.write(f"If any stat is missing from _fighter_data but present "
                f"on the FighterRecord attribute, `_read_stat` at "
                f"game_bridge.py:7828 uses the attribute — decays via "
                f"`setattr` in `_advance_maintenance_week` are "
                f"invisible to `_compute_ovr` because the write path is "
                f"the FighterRecord attribute, not `_fighter_data`.\n")
    print(f"[probe2] wrote {md_path}")

    return {
        "md_path": md_path,
        "stats_before": stats_before,
        "stats_after": stats_after,
        "ovr_stored_before": ovr_stored_before,
        "ovr_stored_after": ovr_stored_after,
        "ovr_computed_before": ovr_computed_before,
        "ovr_computed_after": ovr_computed_after,
        "simple_mean_before": simple_mean_before,
        "simple_mean_after": simple_mean_after,
        "stats_with_data_before": stats_with_data_before,
        "stats_with_data_after": stats_with_data_after,
    }


# ─────────────────────────────────────────────────────────────────────────────
# probe3_camp_vs_autorest
# ─────────────────────────────────────────────────────────────────────────────
def probe3(seed: int, weeks: int, out_dir: str) -> Dict[str, Any]:
    """Book a fight 8w out, lock camp MODERATE, advance and log."""
    os.makedirs(out_dir, exist_ok=True)
    print(f"[probe3] booting bridge (seed={seed}, weeks={weeks})...")
    bridge = _boot_bridge(seed)
    pfid = _player_fid(bridge)
    ftr_obj = bridge._game_state.fighters[pfid]
    start_week = bridge._game_state.week_number

    # B-1: prefer the game's own booking path. Try _book_fight_from_neg
    # or accept_fight_offer. The cleanest lever: pick an opponent from
    # the fighter's division ranked list and craft a fight offer via the
    # bridge's own offer generation, then accept it.
    #
    # Simpler approach that still uses live bridge structures: build a
    # _scheduled_fights entry by COPYING the shape of an existing
    # scheduled fight from the world (if any), else construct minimally
    # matching what _apply_weekly_training reads: fighter1_id, fighter2_id,
    # week, and optional training_focus/intensity.
    #
    # Since bridges may have no pre-existing scheduled_fights for the
    # player at boot, we construct one aligned to the shape used at
    # game_bridge.py:8522-8529.
    from world_init import WEIGHT_CLASSES
    wc = ftr_obj.weight_class
    # pick an unranked opponent in the same division
    opponent_fid = None
    for oid, of in bridge._game_state.fighters.items():
        if oid == pfid:
            continue
        if of.weight_class != wc:
            continue
        if not of.is_active:
            continue
        opponent_fid = oid
        break
    if not opponent_fid:
        print("[probe3] ABORT — no opponent found")
        return {"aborted": True, "reason": "no opponent"}

    fight_id = f"probe3_fight_{seed}"
    # weeks_away=9 so at wk1 (after first advance) weeks_to_fight=8,
    # in_fight_camp=False (camp threshold is <=7 per game_bridge.py:8690).
    # This gives us wk1-2 out-of-camp baseline before wk3+ enters camp.
    weeks_away = 9
    target_week = start_week + weeks_away
    # Shape mirrors accept_fight_offer (game_bridge.py:6522-6538) — must
    # include weeks_until because advance_week decrements it (line 3578)
    # and fires the fight at weeks_until <= 0 (line 3584).
    opp_obj = bridge._game_state.fighters[opponent_fid]
    ftr_name = ftr_obj.name
    sched = {
        "fight_id":       fight_id,
        "fighter1_id":    pfid,
        "fighter1_name":  ftr_name,
        "fighter2_id":    opponent_fid,
        "fighter2_name":  opp_obj.name,
        "weight_class":   wc,
        "week":           target_week,
        "weeks_until":    weeks_away,
        "event_name":     f"Cage Dynasty (probe3)",
        "purse":          10000,
        "win_bonus":      5000,
        "is_title_fight": False,
        "is_player_fight": True,
        "card_slot":      "prelim",
        "rounds":         3,
    }
    bridge._scheduled_fights.append(sched)

    # Lock camp intensity via bridge.save_fight_camp
    r = bridge.save_fight_camp(
        fight_id, gameplan="BALANCED",
        training_focus="sparring", intensity="MODERATE")
    print(f"[probe3] save_fight_camp result: {r}")
    if not r.get("success"):
        print(f"[probe3] save_fight_camp DID NOT report success; still checking readback")

    # B-1 assertions: at week 1 (after next advance), _weeks_to_fight
    # should not be None and _in_fight_camp should be False (8 weeks out).
    # Advance one week and inspect state.
    print(f"[probe3] advance week 1 (probe fires assertions before running full loop)")
    bridge.advance_week()
    cw = bridge._game_state.week_number
    # Recompute the same way _apply_weekly_training does at 8673-8680
    upcoming_wk = next(
        (sf.get("week", 99) for sf in bridge._scheduled_fights
         if sf.get("fighter1_id") == pfid or sf.get("fighter2_id") == pfid),
        None)
    if upcoming_wk is None:
        print(f"[probe3] ABORT — after wk1 advance, no scheduled fight for player")
        return {"aborted": True,
                "reason": "scheduled_fight not read back on next advance"}
    weeks_to_fight = upcoming_wk - cw
    in_fight_camp = weeks_to_fight <= 7
    print(f"[probe3] wk={cw} target={upcoming_wk} weeks_to_fight={weeks_to_fight} "
          f"_in_fight_camp={in_fight_camp}")
    if weeks_to_fight is None:
        return {"aborted": True, "reason": "weeks_to_fight None"}
    if in_fight_camp:
        print(f"[probe3] ABORT — expected NOT in fight camp at 8w out, "
              f"but weeks_to_fight={weeks_to_fight} so _in_fight_camp={in_fight_camp}")
        return {"aborted": True, "reason": f"in_fight_camp True at 8w out"}

    # Continue for the remaining weeks-1 advances, collecting rows
    rows = [{
        "week": cw,
        "weeks_to_fight": weeks_to_fight,
        "in_fight_camp": in_fight_camp,
        "fatigue": _read_fatigue(bridge, pfid),
        "auto_rest_news": _read_last_autorest_news(bridge, pfid, cw) or "",
    }]

    for _ in range(weeks - 1):
        bridge.advance_week()
        cw = bridge._game_state.week_number
        upcoming_wk = next(
            (sf.get("week", 99) for sf in bridge._scheduled_fights
             if sf.get("fighter1_id") == pfid or sf.get("fighter2_id") == pfid),
            None)
        if upcoming_wk is None:
            # Fight resolved this week
            weeks_to_fight = None
            in_fight_camp = False
        else:
            weeks_to_fight = upcoming_wk - cw
            in_fight_camp = weeks_to_fight <= 7
        f = _read_fatigue(bridge, pfid)
        news = _read_last_autorest_news(bridge, pfid, cw) or ""
        rows.append({
            "week": cw,
            "weeks_to_fight": weeks_to_fight,
            "in_fight_camp": in_fight_camp,
            "fatigue": f,
            "auto_rest_news": news,
        })
        print(f"  wk{cw:2d}  weeks_to_fight={weeks_to_fight}  "
              f"in_camp={in_fight_camp}  fatigue={f}  "
              + (f"NEWS: {news}" if news else ""))

    # Write CSV + md
    csv_path = os.path.join(out_dir, f"camp_vs_autorest_{seed}.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    md_path = os.path.join(out_dir, f"camp_vs_autorest_{seed}.md")
    with open(md_path, "w") as f:
        f.write(f"# DEV1 Gate 0 probe3 camp_vs_autorest — seed {seed}\n\n")
        f.write(f"Player: {ftr_obj.name} vs {opponent_fid[:8]}\n\n")
        f.write(f"| Week | weeks_to_fight | in_camp | fatigue | auto_rest_news |\n")
        f.write(f"|---|---:|:---:|---:|---|\n")
        for r in rows:
            f.write(f"| {r['week']} | {r['weeks_to_fight']} | "
                    f"{r['in_fight_camp']} | {r['fatigue']} | "
                    f"{r['auto_rest_news']} |\n")

    print(f"[probe3] wrote {csv_path}")
    print(f"[probe3] wrote {md_path}")
    return {"csv_path": csv_path, "md_path": md_path, "rows": rows,
            "aborted": False}


# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="DEVELOPMENT1 Gate 0 harness.")
    sub = ap.add_subparsers(dest="probe")

    p1 = sub.add_parser("probe1_intensity_sweep")
    p1.add_argument("--seed", type=int, required=True)
    p1.add_argument("--weeks", type=int, default=8)
    p1.add_argument("--out", default="outputs/dev1_gate0/")

    p2 = sub.add_parser("probe2_ovr_attribution")
    p2.add_argument("--seed", type=int, required=True)
    p2.add_argument("--out", default="outputs/dev1_gate0/")

    p3 = sub.add_parser("probe3_camp_vs_autorest")
    p3.add_argument("--seed", type=int, required=True)
    p3.add_argument("--weeks", type=int, default=8)
    p3.add_argument("--out", default="outputs/dev1_gate0/")

    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run or args.probe is None:
        print("dry-run — no execution")
        return 0

    # Resolve out_dir relative to REPO (harness_env cd's to WEB)
    out_dir = os.path.join(_harness_env.REPO_DIR, args.out)

    t0 = time.time()
    if args.probe == "probe1_intensity_sweep":
        r = probe1(args.seed, args.weeks, out_dir)
    elif args.probe == "probe2_ovr_attribution":
        r = probe2(args.seed, out_dir)
    elif args.probe == "probe3_camp_vs_autorest":
        r = probe3(args.seed, args.weeks, out_dir)
    else:
        ap.print_help()
        return 2

    print(f"\n[{args.probe}] TOTAL WALL-CLOCK: {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
