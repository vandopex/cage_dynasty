"""FINISH-DISTRIBUTION probe — Q1 measurement.

Runs the SAME engine (fight_engine.simulate_fight) through BOTH configs
Van's app uses in production:

  - Pre-gen config:  FightConfig.standard_fight()          (defaults)
                     damage_multiplier=0.42, standup_threshold=6,
                     doctor_check_cut_threshold=2

  - Live-play config: _FightConfig(...) as constructed at
                     game_bridge.py:{13540, 14061, 18001}
                     damage_multiplier=0.24, standup_threshold=10,
                     exchanges_per_round=55,
                     submission_progress_to_finish=70.0,
                     submission_escape_threshold=85.0

Purpose (Van's Q1): "Does this hit live-play too, or only pre-gen? …
Run the engine directly through both call paths and compare the finish
distributions. If they differ, name why."

Additional guardrail: also runs live-play through the
fight_integration.NarratedFightResult wrapper (which composes a second
per-strike damage dampener FI_DAMAGE_MULTIPLIER=0.48 on top). That is
the ACTUAL live-play scale on PA. Pre-gen bypasses fight_integration.

Read-only diagnostic. No commit, no ship.
"""
from __future__ import annotations

import os
import random
import sys
from collections import Counter

# sys.path setup mirroring wsgi.py EXACTLY. wsgi.py inserts in the order
# [simulation, narrative, systems, project_home(=web)] so cage_dynasty_web
# ends up at INDEX 0 and shadows the older CLI simulation/fight_engine.py.
_ROOT = "/Users/vandope/Desktop/Games/cage_dynasty"
_WEB = os.path.join(_ROOT, "cage_dynasty_web")
for _p in (os.path.join(_ROOT, "simulation"),
           os.path.join(_ROOT, "narrative"),
           os.path.join(_ROOT, "systems"),
           _WEB):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import fight_engine as fe  # noqa: E402
import fight_integration as fi  # noqa: E402
# Verify we got the WEB engine (has _specialty_ko_map + doctor_check_cut_threshold)
assert "cage_dynasty_web" in fe.__file__, f"Wrong fight_engine loaded: {fe.__file__}"
assert "cage_dynasty_web" in fi.__file__, f"Wrong fight_integration loaded: {fi.__file__}"


def make_fighter(fid, name, style_profile):
    """Build a FighterAttributes at OVR ~75 with a style profile.

    style_profile is one of: 'striker', 'grappler', 'bjj', 'balanced'.
    """
    base = 60
    if style_profile == "striker":
        stats = dict(
            boxing=85, kicks=85, striking_defense=80,
            clinch_striking=70,
            takedown_defense=75, takedowns=45, guard=55, submissions=45,
            top_control=50,
            cardio=75, chin=75, speed=75, strength=75, heart=75, recovery=70,
            fight_iq=72, composure=70,
        )
    elif style_profile == "grappler":
        stats = dict(
            boxing=60, kicks=55, striking_defense=60,
            clinch_striking=60,
            takedown_defense=85, takedowns=90, guard=75, submissions=65,
            top_control=88,
            cardio=80, chin=75, speed=70, strength=80, heart=75, recovery=72,
            fight_iq=72, composure=70,
        )
    elif style_profile == "bjj":
        stats = dict(
            boxing=55, kicks=55, striking_defense=55,
            clinch_striking=55,
            takedown_defense=70, takedowns=65, guard=90, submissions=92,
            top_control=75,
            cardio=75, chin=70, speed=70, strength=68, heart=75, recovery=70,
            fight_iq=72, composure=70,
        )
    else:  # balanced
        stats = dict(
            boxing=72, kicks=72, striking_defense=72,
            clinch_striking=70,
            takedown_defense=72, takedowns=72, guard=70, submissions=68,
            top_control=70,
            cardio=75, chin=72, speed=72, strength=72, heart=72, recovery=72,
            fight_iq=72, composure=70,
        )
    return fe.FighterAttributes(
        fighter_id=fid, name=name,
        **stats,
    )


def _classify(method):
    m = (method or "").upper()
    if "SUBMISSION" in m or m.startswith("SUB"):
        return "SUB"
    if "DECISION" in m or "DRAW" in m:
        return "DEC"
    if m.startswith("KO"):
        return "KO"
    if "DOCTOR" in method.upper() and "CUT" in method.upper():
        return "TKO_CUT"
    if "DOCTOR" in method.upper():
        return "TKO_DOC"
    if "CORNER" in method.upper():
        return "TKO_COR"
    if "LEG KICKS" in method.upper():
        return "TKO_LEG"
    if m.startswith("TKO"):
        return "TKO_ACC"
    return "OTHER"


def run_config(label, config_builder, matchup_maker, n=500, seed=1000,
               engine="raw"):
    """Run n fights of a given matchup through a given config.

    engine="raw" → fight_engine.simulate_fight directly (world_init pre-gen path)
    engine="fi"  → fight_integration.simulate_narrated_fight (live-play path)
    """
    random.seed(seed)
    dist = Counter()
    method_detail = Counter()
    sub_attempts_total = 0
    sub_attempts_count_fights = 0
    for i in range(n):
        f1, f2 = matchup_maker(i)
        config = config_builder()
        if engine == "raw":
            result = fe.simulate_fight(f1, f2, config)
            method = result.method
            # Sum submission_attempts across rounds for both fighters
            sa = 0
            for s in (result.fighter1_stats or []):
                sa += s.get("sub_att", 0) if isinstance(s, dict) else 0
            for s in (result.fighter2_stats or []):
                sa += s.get("sub_att", 0) if isinstance(s, dict) else 0
        else:  # fi
            result = fi.simulate_narrated_fight(f1, f2,
                rounds=config.scheduled_rounds,
                is_title_fight=config.is_title_fight,
                config=config,
            )
            method = result.method
            sa = 0
            # NarratedFightResult uses fighter1_stats/fighter2_stats (list-of-round-dicts)
            for s in (result.fighter1_stats or []):
                sa += (s.get("submission_attempts", 0)
                       or s.get("sub_att", 0)
                       or 0) if isinstance(s, dict) else 0
            for s in (result.fighter2_stats or []):
                sa += (s.get("submission_attempts", 0)
                       or s.get("sub_att", 0)
                       or 0) if isinstance(s, dict) else 0
        cat = _classify(method)
        dist[cat] += 1
        method_detail[method] += 1
        if sa:
            sub_attempts_total += sa
            sub_attempts_count_fights += 1
    return dist, method_detail, sub_attempts_total, sub_attempts_count_fights


def pregen_config():
    return fe.FightConfig.standard_fight()


def liveplay_config():
    return fe.FightConfig(
        scheduled_rounds=3,
        standup_threshold=10,
        exchanges_per_round=55,
        submission_progress_to_finish=70.0,
        submission_escape_threshold=85.0,
        damage_multiplier=0.24,
    )


def liveplay_5_config():
    c = liveplay_config()
    c.scheduled_rounds = 5
    c.is_title_fight = True
    return c


def matchup_balanced_v_balanced(i):
    return (make_fighter(f"a{i}", "A", "balanced"),
            make_fighter(f"b{i}", "B", "balanced"))


def matchup_striker_v_striker(i):
    return (make_fighter(f"a{i}", "A", "striker"),
            make_fighter(f"b{i}", "B", "striker"))


def matchup_striker_v_bjj(i):
    return (make_fighter(f"a{i}", "A", "striker"),
            make_fighter(f"b{i}", "B", "bjj"))


def matchup_grappler_v_bjj(i):
    return (make_fighter(f"a{i}", "A", "grappler"),
            make_fighter(f"b{i}", "B", "bjj"))


def matchup_striker_v_grappler(i):
    return (make_fighter(f"a{i}", "A", "striker"),
            make_fighter(f"b{i}", "B", "grappler"))


def _pct(n, total):
    return f"{100.0 * n / total:5.1f}%" if total else "  n/a"


def print_dist(label, dist, method_detail, n, sub_atts=0, sub_fights=0):
    print(f"\n─── {label} (N={n}) ────────────────────────────")
    total_ko = dist.get("KO", 0)
    total_tko = (dist.get("TKO_CUT", 0) + dist.get("TKO_DOC", 0)
                 + dist.get("TKO_COR", 0) + dist.get("TKO_LEG", 0)
                 + dist.get("TKO_ACC", 0))
    total_sub = dist.get("SUB", 0)
    total_dec = dist.get("DEC", 0)
    print(f"  KO                 {total_ko:4d}  {_pct(total_ko, n)}")
    print(f"  TKO — accumulated  {dist.get('TKO_ACC', 0):4d}  {_pct(dist.get('TKO_ACC', 0), n)}")
    print(f"  TKO — cuts         {dist.get('TKO_CUT', 0):4d}  {_pct(dist.get('TKO_CUT', 0), n)}")
    print(f"  TKO — doctor       {dist.get('TKO_DOC', 0):4d}  {_pct(dist.get('TKO_DOC', 0), n)}")
    print(f"  TKO — corner       {dist.get('TKO_COR', 0):4d}  {_pct(dist.get('TKO_COR', 0), n)}")
    print(f"  TKO — leg kicks    {dist.get('TKO_LEG', 0):4d}  {_pct(dist.get('TKO_LEG', 0), n)}")
    print(f"  ─ TKO total        {total_tko:4d}  {_pct(total_tko, n)}")
    print(f"  SUB                {total_sub:4d}  {_pct(total_sub, n)}")
    print(f"  DEC                {total_dec:4d}  {_pct(total_dec, n)}")
    finish_pct = 100.0 * (total_ko + total_tko + total_sub) / n if n else 0
    print(f"  ─ finish rate      {finish_pct:5.1f}%   (target 50-55%)")
    # % of TKOs that are cuts:
    if total_tko:
        cut_share = 100.0 * dist.get("TKO_CUT", 0) / total_tko
        print(f"  ─ within-TKO cut%  {cut_share:5.1f}%   (target 5-10%)")
    # Sub-attempt density
    avg_sub_atts = sub_atts / n if n else 0
    print(f"  ─ sub attempts     {sub_atts:4d} across {sub_fights:4d} fights "
          f"({avg_sub_atts:.2f}/fight)  → {total_sub} finished "
          f"({100.0 * total_sub / sub_atts if sub_atts else 0:.1f}% conversion)")


def main():
    N = 400
    for matchup_name, matchup in [
        ("Balanced vs Balanced", matchup_balanced_v_balanced),
        ("Striker vs Striker", matchup_striker_v_striker),
        ("Striker vs BJJ", matchup_striker_v_bjj),
        ("Grappler vs BJJ", matchup_grappler_v_bjj),
        ("Striker vs Grappler", matchup_striker_v_grappler),
    ]:
        print(f"\n=========== {matchup_name} ===========")
        pd, pm, ps, pf = run_config("pregen", pregen_config, matchup,
                                    n=N, seed=1000, engine="raw")
        print_dist("PRE-GEN — fight_engine.simulate_fight (world_init path). "
                   "config.damage_multiplier=0.42",
                   pd, pm, N, ps, pf)
        # Raw-with-liveplay-config: what happens if we ran fight_engine with
        # the bridge's config? (Not the actual live-play — just isolates
        # the config field effect from the wrapper.)
        rd, rm, rs, rf = run_config("raw_lp_cfg", liveplay_config, matchup,
                                    n=N, seed=1000, engine="raw")
        print_dist("RAW ENGINE + LIVE-PLAY CFG (config.damage_multiplier=0.24). "
                   "NOT the actual live-play. isolates the dead 0.24 knob.",
                   rd, rm, N, rs, rf)
        # Actual live-play: fight_integration
        fid_, fim, fis, fif = run_config("liveplay_fi", liveplay_config, matchup,
                                         n=N, seed=1000, engine="fi")
        print_dist("LIVE-PLAY (ACTUAL) — fight_integration.simulate_narrated_fight. "
                   "FI_DAMAGE_MULTIPLIER=0.48. config.damage_multiplier=0.24 IGNORED.",
                   fid_, fim, N, fis, fif)


if __name__ == "__main__":
    main()
