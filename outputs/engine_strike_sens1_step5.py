"""ENGINE-STRIKE-SENS1 Step 5 — exchange-level instrumentation.

READ-ONLY. Fresh state per arm, F2 capture, CRN. N=500 each.

Arms (favored slot 1, all non-target stats 75/75):
  H1 — baseline symmetric (both all 75)
  H2 — boxing alone   88 vs 55
  H3 — kicks alone    74 vs 61   (both sides of the >=75 / <60
       damage conditional at fight_engine.py:2395-2397)

Capture per-fight per-fighter RoundStats totals (summed across rounds):
  sig_strikes (significant_strikes_landed)
  takedowns_landed
  control_time
  damage_dealt
  knockdowns
  submission_attempts

Report per arm:
  - mean, SD of each field per fighter
  - favored-minus-unfavored differential with 2σ (Wald on paired diff)
  - p(favored) = favored_wins / N
"""
import os, sys, time, random, math, csv, statistics
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_WEB  = os.path.join(_REPO, "cage_dynasty_web")
_NARR = os.path.join(_REPO, "narrative")
_SYS  = os.path.join(_REPO, "systems")
sys.path.insert(0, _NARR); sys.path.insert(0, _WEB); sys.path.append(_SYS)
import commentary as _prime  # noqa
import game_bridge as gb
fi = sys.modules["fight_integration"]
fe = sys.modules["fight_engine"]


def _flush(m=""): print(m, flush=True)


CONST_FIGHT_ID = "arm_pair"

STRIKING_FAMILY  = ("boxing", "kicks", "clinch_striking", "striking_defense")
GRAPPLING_FAMILY = ("takedowns", "takedown_defense", "top_control",
                    "submissions", "guard")

BASE_75 = {
    "strength": 75, "speed": 75, "cardio": 75, "chin": 75, "recovery": 75,
    "boxing": 75, "kicks": 75, "clinch_striking": 75, "striking_defense": 75,
    "takedowns": 75, "takedown_defense": 75, "top_control": 75,
    "submissions": 75, "guard": 75, "clinch_control": 75,
    "heart": 75, "fight_iq": 75, "composure": 75,
}


def _stats_with_one(attr, val):
    """Return one fighter's stats dict: all 75 except attr=val."""
    out = dict(BASE_75); out[attr] = val
    out["overall_rating"] = 75
    return out


def _make_bare_fighter(fid, name, style_name="Balanced", **overrides):
    class _F: pass
    f = _F()
    f.fighter_id = fid; f.name = name
    f.overall_rating = overrides.get("overall_rating", 75)
    f.fighting_style = style_name
    f.wins = overrides.get("wins", 5); f.losses = overrides.get("losses", 2); f.draws = 0
    f.ko_wins = 2; f.sub_wins = 1; f.ko_losses = 0; f.sub_losses = 0
    f.fatigue = overrides.get("fatigue", 0)
    f.weight_class = "Lightweight"; f.natural_weight_class = "Lightweight"
    f.age = 28; f.popularity = 40; f.is_champion = False
    f.nickname = None; f.camp_id = None; f.contract_id = None
    for k, v in overrides.items(): setattr(f, k, v)
    for a, val in [
        ("strength", overrides.get("strength", 70)),
        ("speed", overrides.get("speed", 70)),
        ("cardio", overrides.get("cardio", 70)),
        ("chin", overrides.get("chin", 70)),
        ("recovery", overrides.get("recovery", 70)),
        ("boxing", overrides.get("boxing", 70)),
        ("kicks", overrides.get("kicks", 70)),
        ("clinch_striking", overrides.get("clinch_striking", 65)),
        ("striking_defense", overrides.get("striking_defense", 70)),
        ("takedowns", overrides.get("takedowns", 65)),
        ("takedown_defense", overrides.get("takedown_defense", 70)),
        ("top_control", overrides.get("top_control", 65)),
        ("submissions", overrides.get("submissions", 60)),
        ("guard", overrides.get("guard", 65)),
        ("clinch_control", overrides.get("clinch_control", 65)),
        ("heart", overrides.get("heart", 72)),
        ("fight_iq", overrides.get("fight_iq", 70)),
        ("composure", overrides.get("composure", 70)),
    ]:
        setattr(f, a, val)
    return f


def _make_test_bridge():
    br = gb.GameBridge()
    class _GS:
        def __init__(self):
            self._fighter_data = {}; self.player_camp_id = None
            self.week_number = 1; self.free_agents = set()
            self.active_contracts = {}; self._contract_data = {}
            self._fighters = {}
        def get_fighter(self, fid): return self._fighters.get(fid)
        def get_player_fighters(self): return []
        def get_camp(self, cid): return None
    gs = _GS(); br._game_state = gs; return br, gs


def _fdata_from_fighter(f):
    return {
        "style": f.fighting_style, "strength": f.strength, "speed": f.speed,
        "cardio": f.cardio, "chin": f.chin, "recovery": f.recovery,
        "boxing": f.boxing, "kicks": f.kicks,
        "clinch_striking": f.clinch_striking,
        "striking_defense": f.striking_defense,
        "takedowns": f.takedowns, "takedown_defense": f.takedown_defense,
        "top_control": f.top_control, "submissions": f.submissions,
        "guard": f.guard, "clinch_control": f.clinch_control,
        "heart": f.heart, "fight_iq": f.fight_iq, "composure": f.composure,
        "fatigue": f.fatigue, "natural_weight_class": f.natural_weight_class,
    }


def _register_fighter(gs, f):
    gs._fighters[f.fighter_id] = f
    gs._fighter_data[f.fighter_id] = _fdata_from_fighter(f)


def _make_fight_const(f1_id, f2_id):
    return {
        "fight_id": CONST_FIGHT_ID,
        "fighter1_id": f1_id, "fighter2_id": f2_id,
        "fighter1_name": f1_id, "fighter2_name": f2_id,
        "weight_class": "Lightweight", "card_slot": "prelim",
        "is_title_fight": False, "event_name": "Test Event",
        "gameplan": "BALANCED",
    }


def _run_path_a_ref(_bundle):
    """Byte-copied from game_bridge.py:17806-17820 (Path A call)."""
    _is_title = _bundle["is_title_fight"]
    _slot_re  = _bundle["card_slot"]
    _is_main  = _slot_re in ("main_event", "co_main")
    _fight_cfg = _bundle["config"]
    return fi.simulate_narrated_fight(
        _bundle["fa1"], _bundle["fa2"],
        rounds        = _bundle["total_rounds"],
        is_title_fight= _is_title,
        is_main_event = _is_main,
        starting_stamina_f1=_bundle["starting_stamina_f1"],
        starting_stamina_f2=_bundle["starting_stamina_f2"],
        gameplan_f1   = _bundle["gameplan_f1"],
        gameplan_f2   = _bundle["gameplan_f2"],
        card_slot     = _slot_re,
        intro_f1      = _bundle["intro_f1"],
        intro_f2      = _bundle["intro_f2"],
        **({"config": _fight_cfg} if _fight_cfg else {})
    )


_PA_KW = dict(fatigue_source="attr", apply_cut_penalty=True,
              apply_player_buffs=True, apply_sponsor_boost=True,
              compute_style_mod=True, verbose=False)


def _fa_stats_dict(fa):
    return {a: getattr(fa, a, None) for a in (
        list(STRIKING_FAMILY) + list(GRAPPLING_FAMILY)
        + ["strength", "speed", "cardio", "chin", "clinch_control",
           "heart", "fight_iq", "composure", "recovery"])}


# RoundStats fields on the .to_dict() output (from fight_engine.py:653-668):
#   sig_strikes_att, sig_strikes_landed, head_strikes, body_strikes,
#   leg_strikes, td_att, td_landed, sub_att, control_time, damage,
#   knockdowns, (reversals)
STAT_KEYS = ("sig_strikes_landed", "td_landed", "sub_att",
             "control_time", "damage", "knockdowns")


def _sum_rounds(round_dicts):
    """Sum RoundStats fields across all rounds for one fighter."""
    tot = {k: 0.0 for k in STAT_KEYS}
    for rd in round_dicts:
        for k in STAT_KEYS:
            tot[k] += rd.get(k, 0)
    return tot


def run_arm_h(arm_name, fav_stats, unf_stats, N):
    br, gs = _make_test_bridge()
    _fav_id = f"{arm_name}_favored"
    _unf_id = f"{arm_name}_unfavored"
    f_favored = _make_bare_fighter(_fav_id, _fav_id, **fav_stats)
    f_unfavored = _make_bare_fighter(_unf_id, _unf_id, **unf_stats)
    _register_fighter(gs, f_favored)
    _register_fighter(gs, f_unfavored)
    fight = _make_fight_const(f_favored.fighter_id, f_unfavored.fighter_id)

    _flush("")
    _flush("=" * 70)
    _flush(f"ARM {arm_name}   N={N}   favored_in_slot1=True")
    _flush("=" * 70)
    _flush(f"CRN: fight_id={CONST_FIGHT_ID!r}   "
           f"fighter1_id={fight['fighter1_id']!r}   "
           f"fighter2_id={fight['fighter2_id']!r}")
    _flush(f"seed sequence: random.seed(i) for i in 0..{N-1}")
    _flush(f"favored stats (target dims): "
           f"{ {k: getattr(f_favored, k) for k in ('boxing','kicks','clinch_striking','striking_defense')} }")
    _flush(f"unfavored stats (target dims): "
           f"{ {k: getattr(f_unfavored, k) for k in ('boxing','kicks','clinch_striking','striking_defense')} }")

    _b_probe = br._assemble_prefight(
        fight, f_favored, f_unfavored,
        f_favored.name, f_unfavored.name,
        f_favored.fighter_id, f_unfavored.fighter_id, **_PA_KW,
    )
    _cfg = _b_probe["config"]
    _standup = getattr(_cfg, "standup_threshold", None)
    _dmg = getattr(_cfg, "damage_multiplier", None)
    _flush(f"config: standup={_standup}, damage={_dmg}")
    assert _standup == 10, f"standup={_standup} != 10 → voids run"

    # F2 capture (sim 0)
    captured_fa = []
    _original_snf = fi.simulate_narrated_fight
    def _snf_capture(fa1_, fa2_, *args, **kwargs):
        if len(captured_fa) == 0:  # only sim 0
            captured_fa.append({
                "fa1_id": getattr(fa1_, 'fighter_id', None),
                "fa2_id": getattr(fa2_, 'fighter_id', None),
                "fa1": _fa_stats_dict(fa1_),
                "fa2": _fa_stats_dict(fa2_),
            })
        return _original_snf(fa1_, fa2_, *args, **kwargs)
    fi.simulate_narrated_fight = _snf_capture

    per_fight_rows = []
    fav_wins = 0
    unf_wins = 0
    draws = 0
    t0 = time.perf_counter()
    try:
        for i in range(N):
            random.seed(i)
            _bundle = br._assemble_prefight(
                fight, f_favored, f_unfavored,
                f_favored.name, f_unfavored.name,
                f_favored.fighter_id, f_unfavored.fighter_id, **_PA_KW,
            )
            eng = _run_path_a_ref(_bundle)
            f1_tot = _sum_rounds(eng.fighter1_stats)
            f2_tot = _sum_rounds(eng.fighter2_stats)
            _winner = getattr(eng, "winner_id", None)
            _method = getattr(eng, "method", None)
            if _winner == _fav_id: fav_wins += 1
            elif _winner == _unf_id: unf_wins += 1
            else: draws += 1
            per_fight_rows.append({
                "arm": arm_name, "seed": i,
                "favored_id": _fav_id, "unfavored_id": _unf_id,
                "winner": _winner, "method": _method,
                "fav": f1_tot, "unf": f2_tot,
            })
    finally:
        fi.simulate_narrated_fight = _original_snf
    dt = time.perf_counter() - t0
    _flush(f"arm {arm_name} wall clock: {dt:.2f} sec  ({dt*1000/N:.2f} ms/sim)")

    # F2 sim-0 print
    _c0 = captured_fa[0]
    _flush(f"F2 — runtime capture, sim 0:")
    _flush(f"  fa1[{_c0['fa1_id']}]: "
           f"{ {k: _c0['fa1'].get(k) for k in ('boxing','kicks','clinch_striking','striking_defense','takedowns','submissions')} }")
    _flush(f"  fa2[{_c0['fa2_id']}]: "
           f"{ {k: _c0['fa2'].get(k) for k in ('boxing','kicks','clinch_striking','striking_defense','takedowns','submissions')} }")

    return per_fight_rows, fav_wins, unf_wins, draws


def analyze_arm(arm_name, rows, fav_wins, unf_wins, draws, N):
    _flush("")
    _flush(f"--- arm {arm_name} report ---")
    p_fav = fav_wins / N
    se = math.sqrt(p_fav * (1 - p_fav) / N) if 0 < p_fav < 1 else 0.0
    _flush(f"p(favored) = {fav_wins}/{N} = {p_fav:.4f}  ±2σ = ±{2*se:.4f}   "
           f"(unfav={unf_wins}, draws={draws})")
    _flush(f"per-fighter per-fight RoundStats totals (N={N}):")
    # Mean and SD for each fighter per field
    for who, key in [("favored", "fav"), ("unfavored", "unf")]:
        _flush(f"  {who}:")
        for f in STAT_KEYS:
            vals = [row[key][f] for row in rows]
            _mean = statistics.mean(vals)
            _sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
            _flush(f"    {f:<26} mean={_mean:>9.3f}  SD={_sd:>8.3f}")
    # Paired favored-minus-unfavored diff
    _flush(f"paired favored − unfavored differential:")
    for f in STAT_KEYS:
        diffs = [row["fav"][f] - row["unf"][f] for row in rows]
        _mean = statistics.mean(diffs)
        _sd = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
        _se = _sd / math.sqrt(len(diffs)) if len(diffs) > 1 else 0.0
        _flush(f"  Δ({f:<26}) = {_mean:>+9.3f}   ±2σ = ±{2*_se:.3f}   "
               f"(SD={_sd:.3f})")


def main():
    N = 500
    _flush("=" * 70)
    _flush("ENGINE-STRIKE-SENS1 Step 5 Part B — exchange-level instrumentation")
    _flush("=" * 70)
    _flush(f"fight_engine       from: {fe.__file__}")
    _flush(f"fight_integration  from: {fi.__file__}")
    _flush(f"game_bridge        from: {gb.__file__}")
    _flush(f"RoundStats fields captured (per-round, then summed): {STAT_KEYS}")

    all_rows = []

    # H1 — baseline symmetric (both all 75)
    _fav = dict(BASE_75); _fav["overall_rating"] = 75
    _unf = dict(BASE_75); _unf["overall_rating"] = 75
    rows_h1, fw, uw, dw = run_arm_h("H1", _fav, _unf, N)
    analyze_arm("H1", rows_h1, fw, uw, dw, N)
    all_rows.extend(rows_h1)

    # H2 — boxing 88 vs 55
    rows_h2, fw, uw, dw = run_arm_h(
        "H2", _stats_with_one("boxing", 88), _stats_with_one("boxing", 55), N)
    analyze_arm("H2", rows_h2, fw, uw, dw, N)
    all_rows.extend(rows_h2)

    # H3 — kicks 74 vs 61 (both sides of the >=75 / <60 damage conditional)
    rows_h3, fw, uw, dw = run_arm_h(
        "H3", _stats_with_one("kicks", 74), _stats_with_one("kicks", 61), N)
    analyze_arm("H3", rows_h3, fw, uw, dw, N)
    all_rows.extend(rows_h3)

    # CSV dump
    csv_path = os.path.join(_HERE, "engine_strike_sens1_step5_raw.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["arm", "seed", "favored_id", "unfavored_id",
                    "winner", "method",
                    "fav_sig_strikes", "fav_td_landed", "fav_sub_att",
                    "fav_control_time", "fav_damage", "fav_knockdowns",
                    "unf_sig_strikes", "unf_td_landed", "unf_sub_att",
                    "unf_control_time", "unf_damage", "unf_knockdowns"])
        for r in all_rows:
            w.writerow([r["arm"], r["seed"], r["favored_id"], r["unfavored_id"],
                        r["winner"], r["method"],
                        r["fav"]["sig_strikes_landed"], r["fav"]["td_landed"],
                        r["fav"]["sub_att"], r["fav"]["control_time"],
                        r["fav"]["damage"], r["fav"]["knockdowns"],
                        r["unf"]["sig_strikes_landed"], r["unf"]["td_landed"],
                        r["unf"]["sub_att"], r["unf"]["control_time"],
                        r["unf"]["damage"], r["unf"]["knockdowns"]])
    _flush("")
    _flush(f"CSV dump: {csv_path}  ({len(all_rows)} rows)")

    _flush("")
    _flush("DONE — numbers only, no interpretation.")


if __name__ == "__main__":
    main()
