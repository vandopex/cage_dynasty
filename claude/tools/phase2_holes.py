"""Phase 2 holes — combined harness for H-1, H-6, H-7.

One boot of the world, then several read-only inspections.
Also runs probe2 with a style fix (H-4) and probe3B with pre-fatigued
fighter (H-2) — each with its own sub-command since they need separate
worlds.
"""

import argparse
import os
import random
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness_env  # noqa


SEED = 20260907
STATS_19 = [
    "strength", "speed", "cardio", "chin", "recovery", "power",
    "boxing", "kicks", "clinch_striking", "striking_defense",
    "takedowns", "takedown_defense", "top_control", "submissions",
    "guard", "clinch_control", "heart", "fight_iq", "composure",
]


# ─────────────────────────────────────────────────────────────────────────────
# H-7 world_init MONKEYPATCH — install BEFORE new_game
# ─────────────────────────────────────────────────────────────────────────────
CAPTURED_HRN = []  # list of dicts: {fighter_id, name, country, height, reach}


def install_hrn_monkeypatch():
    """Wrap world_init.FighterGenerator.generate_fighter so we capture
    every produced GeneratedFighter (height, reach, country) before
    the persist path strips them.

    Must be installed AFTER game_bridge is imported so game_bridge's
    sys.path fixup + force-delete has resolved fight_engine to the
    WEB copy. Otherwise world_init's `from simulation.fight_integration
    import ...` grabs the wrong fight_engine and pre-gen falls back to
    simulate_fight_simple.
    """
    import world_init
    orig = world_init.FighterGenerator.generate_fighter

    def wrapper(self, *a, **kw):
        gf = orig(self, *a, **kw)
        CAPTURED_HRN.append({
            "fighter_id": gf.fighter_id,
            "name": gf.name,
            "country": gf.country,
            "height": gf.height,
            "reach": gf.reach,
        })
        return gf
    world_init.FighterGenerator.generate_fighter = wrapper


def _boot_with_monkeypatch(seed: int = SEED):
    # Import game_bridge FIRST so its sys.path fixup runs and
    # fight_engine/fight_integration resolve to the WEB copies.
    random.seed(seed)
    from game_bridge import GameBridge
    # NOW install the monkeypatch (world_init is import-safe after fixup)
    install_hrn_monkeypatch()
    from game_start import generate_starting_prospects  # noqa
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
        **{s: getattr(p, s) for s in STATS_19 if s != "power"},
    }
    coach_dict = {"id": "coach_1", "name": "Test Coach",
                  "specialty": "boxing", "rating": 65,
                  "traits": [], "cost": 500}
    bridge = GameBridge()
    bridge._user_id = f"harness_h_{seed}"
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


# ─────────────────────────────────────────────────────────────────────────────
# H-1 WEEK AXIS
# ─────────────────────────────────────────────────────────────────────────────
def h1_week_axis(bridge, weeks: int):
    print(f"\n=== H-1 WEEK AXIS (seed={SEED}, weeks={weeks}) ===")
    # (a) bridge.week_number right after new_game
    wn_after_new_game = bridge._game_state.week_number
    print(f"(a) bridge.week_number IMMEDIATELY AFTER new_game: {wn_after_new_game}")

    # Advance the requested weeks
    print(f"    advancing {weeks} weeks...")
    for w in range(weeks):
        bridge.advance_week()
    print(f"    week_number after {weeks} advance_weeks: "
          f"{bridge._game_state.week_number}")

    # (b) Pick three fighters with BOTH pre-gen (any) and LIVE fights.
    # Live fight = week > wn_after_new_game (from bridge axis).
    candidates = []
    for fid, f in bridge._game_state.fighters.items():
        hist = f.fight_history or []
        if len(hist) < 2:
            continue
        # split by fight week vs bridge week 0 (pre-gen) — we don't yet
        # know the axis, so pick fighters with a broad week range
        weeks_seen = sorted(set(int(h.get("week", 0) or 0)
                                for h in hist if isinstance(h, dict)))
        if weeks_seen[0] < 15 and weeks_seen[-1] > 50:
            candidates.append((fid, f.name, len(hist)))
    print(f"(b) candidate fighters with ≥2 fights spanning wk<15 to wk>50: "
          f"{len(candidates)}")
    for fid, name, cnt in candidates[:3]:
        f = bridge._game_state.fighters[fid]
        print(f"\n    --- {name} ({fid[:8]}) — {cnt} fights ---")
        for i, h in enumerate(f.fight_history or []):
            if not isinstance(h, dict):
                continue
            print(f"      #{i:2d} wk={h.get('week'):>3} "
                  f"event_number={h.get('event_number')} "
                  f"event_name={h.get('event_name'):<30} "
                  f"result={h.get('result')} method={h.get('method')}")

    # (c) Last pre-gen event vs first live event
    # Enumerate the WorldInitializer's HistorySimulator event list.
    # bridge stashed _belt_history but not the raw simulation event
    # list, so we'll infer by scanning fight_history across all
    # fighters for the event with the highest event_number generated
    # by pre-gen.
    print()
    print("(c) pre-gen boundary probe")
    # HistorySimulator's DFC event numbers start at 1 and run through
    # history_weeks. Let's find the maximum event_number that has
    # week < wn_before_advance_start.
    # First scan all history entries.
    events_by_week = {}  # week -> set(event_numbers)
    for fid, f in bridge._game_state.fighters.items():
        for h in f.fight_history or []:
            if not isinstance(h, dict):
                continue
            w = int(h.get("week", 0) or 0)
            en = h.get("event_number")
            events_by_week.setdefault(w, set()).add(en)
    # Show first 10 weeks and last 5 weeks of event numbers observed
    sorted_weeks = sorted(events_by_week.keys())
    print(f"    unique weeks observed: {len(sorted_weeks)}, "
          f"range {sorted_weeks[0]}..{sorted_weeks[-1]}")
    print(f"    events at first 5 weeks:")
    for w in sorted_weeks[:5]:
        print(f"      wk={w} events={sorted(events_by_week[w], key=lambda x: (x is None, x))}")
    print(f"    events at last 5 weeks:")
    for w in sorted_weeks[-5:]:
        print(f"      wk={w} events={sorted(events_by_week[w], key=lambda x: (x is None, x))}")

    # Print completed_events chronology from the bridge if available
    ce = bridge._completed_events or []
    print(f"    bridge._completed_events count: {len(ce)}")
    if ce:
        first = ce[0]
        last = ce[-1]
        print(f"    first completed_event: name={first.get('event_name')} "
              f"week={first.get('week')} event_id={first.get('event_id')}")
        print(f"    last  completed_event: name={last.get('event_name')} "
              f"week={last.get('week')} event_id={last.get('event_id')}")

    # Look for a pre-gen-vs-live marker in fight dicts
    print()
    print("    key/marker census in fight_history[0] across sample fighters:")
    sample_keys = Counter()
    for fid, f in list(bridge._game_state.fighters.items())[:20]:
        for h in (f.fight_history or [])[:1]:
            if isinstance(h, dict):
                for k in h.keys():
                    sample_keys[k] += 1
    print(f"    keys seen: {sorted(sample_keys.keys())}")

    # Print template read locations for R03 (H-1 last question)
    print()
    print("(d) R03 template axis read — file:line evidence")
    print("    Template check (fighter_profile.html:1207): `if r.won_week == fight.week`")
    print("    Template check (fighter_profile.html:1209-1211): "
          "`r.won_week < fight.week and (r.is_active or r.lost_week > fight.week)`")
    print("    Template check (fighter_profile.html:1212): `fight.result == 'W'`")
    print("    Reign field `won_week`  written at world_init.py:600 "
          "(inaugural) and world_init.py:637 (title-change)")
    print("    Fight field `week` written at world_init.py:2406/2421 (pre-gen)")
    print("    Bridge write of live-play fight history at "
          "game_bridge.py:18443+ (search 'Fight history — write BEFORE return')")


# ─────────────────────────────────────────────────────────────────────────────
# H-6 VACUOUS PASSES
# ─────────────────────────────────────────────────────────────────────────────
def h6_vacuous(bridge):
    print(f"\n=== H-6 VACUOUS PASSES ===")
    reigns_by_wc = (bridge._belt_history.to_dict()
                    if bridge._belt_history else {"reigns": {}}).get("reigns", {})
    inaugural_fids = set()
    for wc, reigns in reigns_by_wc.items():
        for r in reigns:
            wm = str(r.get("won_method", "") or "").lower()
            if r.get("won_from") is None or "inaugural" in wm:
                if r.get("champion_id"):
                    inaugural_fids.add(r["champion_id"])
                break
    all_founding_holders = []
    for fid, f in bridge._game_state.fighters.items():
        hist = f.fight_history or []
        if any(isinstance(h, dict) and (
            "Founding" in str(h.get("method", ""))
            or "Inaugural" in str(h.get("method", ""))
            or "Founding" in str(h.get("event_name", ""))
        ) for h in hist):
            all_founding_holders.append(fid)
    print(f"R04: len(inaugural_fids)      = {len(inaugural_fids)}")
    print(f"R04: len(all_founding_holders)= {len(all_founding_holders)}")
    print(f"     intersection             = {len(set(inaugural_fids) & set(all_founding_holders))}")
    print(f"     inaugural_only           = {len(set(inaugural_fids) - set(all_founding_holders))}")
    print(f"     founding_only            = {len(set(all_founding_holders) - set(inaugural_fids))}")
    if len(all_founding_holders) == 0:
        print(f"     → PASS was vacuous: 0 founding rows means the check "
              f"has no evidence either way.")

    # R02 details: for each violator, print tail of fight_history
    print()
    print(f"R02: violator streak details")
    violators = []
    for fid, f in bridge._game_state.fighters.items():
        wins = int(getattr(f, "wins", 0))
        hist = f.fight_history or []
        streak = 0
        for h in reversed(hist):
            if isinstance(h, dict) and h.get("result") == "W":
                streak += 1
            else:
                break
        if streak > wins:
            violators.append((fid, streak, wins, hist))
    print(f"     total violators: {len(violators)}")
    for fid, streak, wins, hist in violators[:7]:
        # Check whether any of the last `streak` entries has founding/inaugural marker
        tail = [h for h in hist[-streak:] if isinstance(h, dict)]
        has_founding = any(
            "Founding" in str(h.get("method", ""))
            or "Inaugural" in str(h.get("method", ""))
            or "Founding" in str(h.get("event_name", ""))
            for h in tail)
        print(f"     {fid[:8]}: streak={streak} wins={wins} "
              f"has_founding_in_tail={has_founding}")
        if tail:
            for h in tail:
                print(f"        - wk={h.get('week')} event={h.get('event_name')} "
                      f"method={h.get('method')} result={h.get('result')}")

    # R12 details: is the single violator the player fighter?
    print()
    print(f"R12: violator identity")
    pfid = _player_fid(bridge)
    for fid, f in bridge._game_state.fighters.items():
        if not f.camp_id:
            continue
        fd = bridge._game_state._fighter_data.get(fid, {})
        if "ovr_at_signing" not in fd:
            is_player = (fid == pfid)
            print(f"     violator: {fid[:12]}  name={f.name}  "
                  f"is_player_fighter={is_player}")
            break


# ─────────────────────────────────────────────────────────────────────────────
# H-7 HRN RUNTIME WRAP report
# ─────────────────────────────────────────────────────────────────────────────
def h7_hrn(bridge):
    print(f"\n=== H-7 R11 RUNTIME WRAP (monkeypatched world_init) ===")
    print(f"    captured fighters: {len(CAPTURED_HRN)}")
    if not CAPTURED_HRN:
        print("    NO CAPTURE — monkeypatch didn't hook the generator path.")
        return
    heights = [g["height"] for g in CAPTURED_HRN]
    reaches = [g["reach"] for g in CAPTURED_HRN]
    countries = [g["country"] for g in CAPTURED_HRN]
    hc = Counter(heights)
    rc = Counter(reaches)
    cc = Counter(countries)
    print(f"    HEIGHT distinct: {len(hc)}   modal: {hc.most_common(1)}   "
          f"share: {hc.most_common(1)[0][1] / len(heights):.3f}")
    print(f"    REACH  distinct: {len(rc)}   modal: {rc.most_common(1)}   "
          f"share: {rc.most_common(1)[0][1] / len(reaches):.3f}")
    print(f"    COUNTRY distinct: {len(cc)}  modal: {cc.most_common(1)}  "
          f"share: {cc.most_common(1)[0][1] / len(countries):.3f}")
    print(f"    Height range: {min(heights)}..{max(heights)}")
    print(f"    Reach  range: {min(reaches)}..{max(reaches)}")
    print(f"    Top 5 heights: {hc.most_common(5)}")
    print(f"    Top 5 reaches: {rc.most_common(5)}")

    # Where does the bridge retain these? Check
    print()
    print("    Does the bridge retain GeneratedFighter objects at runtime?")
    for attr in ["_history_sim", "_world_gen", "_initializer",
                 "_generated_fighters"]:
        v = getattr(bridge, attr, None)
        print(f"      bridge.{attr:<24} = {type(v).__name__}"
              + (f"  (populated)" if v is not None else ""))


# ─────────────────────────────────────────────────────────────────────────────
# H-2 PROBE3B — pre-fatigue to 84, book 9w out, lock camp MODERATE
# ─────────────────────────────────────────────────────────────────────────────
def h2_probe3b():
    print(f"\n=== H-2 PROBE3B (pre-fatigue = 84 at boot) ===")
    random.seed(SEED)
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
        **{s: getattr(p, s) for s in STATS_19 if s != "power"},
    }
    coach_dict = {"id": "coach_1", "name": "Test Coach",
                  "specialty": "boxing", "rating": 65,
                  "traits": [], "cost": 500}
    bridge = GameBridge()
    bridge._user_id = f"h2_seed{SEED}"
    bridge.new_game("Harness Camp", "Las Vegas, NV",
                    "GARAGE", coach_dict, fighter_dict)

    pfid = _player_fid(bridge)
    ftr = bridge._game_state.fighters[pfid]
    # Pre-poke fatigue
    bridge._game_state._fighter_data[pfid]["fatigue"] = 84
    if hasattr(ftr, "fatigue"):
        ftr.fatigue = 84
    print(f"    player {ftr.name} pre-fatigue set to 84")

    # Book fight 9w out with same shape as probe3
    opp_fid = next(
        (oid for oid, of in bridge._game_state.fighters.items()
         if oid != pfid and of.weight_class == ftr.weight_class
         and of.is_active), None)
    if not opp_fid:
        print("    ABORT — no opponent")
        return
    start_wk = bridge._game_state.week_number
    weeks_away = 9
    sched = {
        "fight_id": f"h2_fight_{SEED}",
        "fighter1_id": pfid, "fighter1_name": ftr.name,
        "fighter2_id": opp_fid,
        "fighter2_name": bridge._game_state.fighters[opp_fid].name,
        "weight_class": ftr.weight_class,
        "week": start_wk + weeks_away, "weeks_until": weeks_away,
        "event_name": "Cage Dynasty (h2)",
        "purse": 10000, "win_bonus": 5000,
        "is_title_fight": False, "is_player_fight": True,
        "card_slot": "prelim", "rounds": 3,
    }
    bridge._scheduled_fights.append(sched)
    bridge.save_fight_camp("h2_fight_{}".format(SEED),
                            gameplan="BALANCED",
                            training_focus="sparring",
                            intensity="MODERATE")

    print()
    print(f"    Week table (weeks 1..8):")
    print(f"    {'wk':>3}  {'w2f':>3}  {'in_camp':>7}  {'fatigue':>7}  news")
    for _ in range(8):
        bridge.advance_week()
        cw = bridge._game_state.week_number
        upcoming = next(
            (sf.get("week", 99) for sf in bridge._scheduled_fights
             if sf.get("fighter1_id") == pfid or sf.get("fighter2_id") == pfid),
            None)
        if upcoming is None:
            w2f, in_camp = None, False
        else:
            w2f = upcoming - cw
            in_camp = w2f <= 7
        fat = int(bridge._game_state._fighter_data.get(pfid, {}).get("fatigue", 0))
        # collect any training news for this fighter this week
        news_hits = [n["headline"] for n in bridge._news_items[:30]
                     if n.get("category") == "training"
                     and n.get("week") == cw
                     and ftr.name in n.get("headline", "")]
        news_str = " | ".join(news_hits) if news_hits else ""
        print(f"    {cw:>3}  {str(w2f):>3}  {str(in_camp):>7}  "
              f"{fat:>7}  {news_str}")


# ─────────────────────────────────────────────────────────────────────────────
# H-4 PROBE2 with style fix
# ─────────────────────────────────────────────────────────────────────────────
def h4_probe2_stylefix():
    print(f"\n=== H-4 PROBE2 STYLE-FIX ===")
    random.seed(SEED)
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
        **{s: getattr(p, s) for s in STATS_19 if s != "power"},
    }
    coach_dict = {"id": "coach_1", "name": "Test Coach",
                  "specialty": "boxing", "rating": 65,
                  "traits": [], "cost": 500}
    bridge = GameBridge()
    bridge._user_id = f"h4_seed{SEED}"
    bridge.new_game("Harness Camp", "Las Vegas, NV",
                    "GARAGE", coach_dict, fighter_dict)
    pfid = _player_fid(bridge)
    ftr = bridge._game_state.fighters[pfid]
    prospect_style = p.fighting_style
    print(f"    Prospect fighting_style = {prospect_style!r}")
    print(f"    FighterRecord.fighting_style BEFORE fix = {ftr.fighting_style!r}")
    # THE FIX — mirror what world_init would do for AI fighters
    ftr.fighting_style = prospect_style
    print(f"    FighterRecord.fighting_style AFTER  fix = {ftr.fighting_style!r}")

    # Same probe2 measurement
    bridge.set_training_plan(pfid, focus="sparring", intensity="MODERATE")
    fd_b = bridge._game_state._fighter_data.get(pfid, {})
    stats_before = {s: fd_b.get(s, 0) for s in STATS_19}
    ovr_stored_before = int(getattr(ftr, "overall_rating", 0))
    ovr_computed_before = bridge._compute_ovr(ftr)
    simple_before = sum(stats_before.values()) / 19.0
    stats_with_data_before = sum(
        1 for s in STATS_19 if bridge._read_stat(ftr, s) > 0)

    print(f"    Advancing 1 week (MODERATE)...")
    t_w = time.time()
    bridge.advance_week()
    print(f"    advance: {time.time()-t_w:.1f}s")

    fd_a = bridge._game_state._fighter_data.get(pfid, {})
    stats_after = {s: fd_a.get(s, 0) for s in STATS_19}
    ovr_stored_after = int(getattr(ftr, "overall_rating", 0))
    ovr_computed_after = bridge._compute_ovr(ftr)
    simple_after = sum(stats_after.values()) / 19.0

    print()
    print(f"    Reading                    Before  After   Δ")
    print(f"    overall_rating stored      {ovr_stored_before:>6}  "
          f"{ovr_stored_after:>5}  {ovr_stored_after - ovr_stored_before:+d}")
    print(f"    _compute_ovr() recomputed  {ovr_computed_before:>6}  "
          f"{ovr_computed_after:>5}  {ovr_computed_after - ovr_computed_before:+d}")
    print(f"    simple mean(19)            {simple_before:>6.2f}  "
          f"{simple_after:>5.2f}  {simple_after - simple_before:+.2f}")
    print(f"    stats_with_data before/after: {stats_with_data_before}/"
          f"{sum(1 for s in STATS_19 if bridge._read_stat(ftr, s) > 0)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["h1_h6_h7", "h2", "h4"],
                    required=True,
                    help="h1_h6_h7 does the shared-boot triple; "
                         "h2 does probe3B; h4 does probe2 with style-fix")
    ap.add_argument("--weeks", type=int, default=14)
    args = ap.parse_args()

    t0 = time.time()
    if args.part == "h1_h6_h7":
        bridge = _boot_with_monkeypatch()
        h1_week_axis(bridge, args.weeks)
        h6_vacuous(bridge)
        h7_hrn(bridge)
    elif args.part == "h2":
        h2_probe3b()
    elif args.part == "h4":
        h4_probe2_stylefix()
    print(f"\n=== TOTAL WALL-CLOCK: {time.time()-t0:.1f}s ===")


if __name__ == "__main__":
    main()
