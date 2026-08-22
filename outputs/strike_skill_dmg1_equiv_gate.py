"""STRIKE-SKILL-DMG1 phase 1a — equivalence gate harness.

Runs arms E, F, G1, H3, J1 under CRN, dumps a single CSV. Header
embeds engine paths + git HEAD SHA + active K value so any artifact
can be traced to the world it was measured in.

USAGE (from outputs/):
  python3 -u strike_skill_dmg1_equiv_gate.py --tag baseline_c06b0f9
  # ... engine edit lands ...
  python3 -u strike_skill_dmg1_equiv_gate.py --tag postedit_K0
  diff baseline_c06b0f9_raw.csv postedit_K0_raw.csv   # must be empty

READ-ONLY on repo state. Writes only to outputs/.
"""
import os, sys, time, random, math, csv, argparse, subprocess

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


# ==================== CRN + fixture builders ====================
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


def _stats_with_family(family_names, val_favored=88, val_unfavored=55):
    fav = dict(BASE_75); unf = dict(BASE_75)
    for a in family_names:
        fav[a] = val_favored
        unf[a] = val_unfavored
    fav["overall_rating"] = 75
    unf["overall_rating"] = 75
    return fav, unf


def _make_bare_fighter(fid, name, style_name="Balanced", **overrides):
    """Byte-identical to the tracked SENS1 fixture builders."""
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


def _register_fighter(gs, f):
    gs._fighters[f.fighter_id] = f
    gs._fighter_data[f.fighter_id] = {
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


def _sum_rounds(round_dicts):
    keys = ("sig_strikes_landed", "td_landed", "sub_att",
            "control_time", "damage", "knockdowns")
    tot = {k: 0.0 for k in keys}
    for rd in round_dicts:
        for k in keys:
            tot[k] += rd.get(k, 0)
    return tot


def run_arm(arm_name, slot1_stats, slot2_stats, N):
    br, gs = _make_test_bridge()
    _s1_id = f"{arm_name}_slot1"
    _s2_id = f"{arm_name}_slot2"
    fA = _make_bare_fighter(_s1_id, _s1_id, **slot1_stats)
    fB = _make_bare_fighter(_s2_id, _s2_id, **slot2_stats)
    _register_fighter(gs, fA); _register_fighter(gs, fB)
    fight = _make_fight_const(_s1_id, _s2_id)

    _flush(f"  arm {arm_name}: N={N}")
    _b_probe = br._assemble_prefight(
        fight, fA, fB, fA.name, fB.name,
        fA.fighter_id, fB.fighter_id, **_PA_KW,
    )
    _cfg = _b_probe["config"]
    _standup = getattr(_cfg, "standup_threshold", None)
    assert _standup == 10, f"arm {arm_name}: standup={_standup} != 10"

    rows = []
    t0 = time.perf_counter()
    for i in range(N):
        random.seed(i)
        _bundle = br._assemble_prefight(
            fight, fA, fB, fA.name, fB.name,
            fA.fighter_id, fB.fighter_id, **_PA_KW,
        )
        eng = _run_path_a_ref(_bundle)
        f1_tot = _sum_rounds(eng.fighter1_stats)
        f2_tot = _sum_rounds(eng.fighter2_stats)
        rows.append({
            "arm": arm_name,
            "seed": i,
            "winner": getattr(eng, "winner_id", None),
            "method": getattr(eng, "method", None),
            "total_rounds": getattr(eng, "total_rounds", None),
            "f1_sig": f1_tot["sig_strikes_landed"],
            "f1_td":  f1_tot["td_landed"],
            "f1_sub": f1_tot["sub_att"],
            "f1_ctl": f1_tot["control_time"],
            "f1_dmg": f1_tot["damage"],
            "f1_kd":  f1_tot["knockdowns"],
            "f2_sig": f2_tot["sig_strikes_landed"],
            "f2_td":  f2_tot["td_landed"],
            "f2_sub": f2_tot["sub_att"],
            "f2_ctl": f2_tot["control_time"],
            "f2_dmg": f2_tot["damage"],
            "f2_kd":  f2_tot["knockdowns"],
        })
    dt = time.perf_counter() - t0
    _flush(f"    wall clock: {dt:.2f} sec  ({dt*1000/N:.2f} ms/sim)")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True,
                    help="output tag, e.g. baseline_c06b0f9 or postedit_K0")
    args = ap.parse_args()

    _flush("=" * 70)
    _flush("STRIKE-SKILL-DMG1 phase 1a — equivalence gate")
    _flush("=" * 70)
    _flush(f"tag: {args.tag}")

    # Header metadata — engine paths + git HEAD + K value.
    _flush(f"fight_engine       from: {fe.__file__}")
    _flush(f"fight_integration  from: {fi.__file__}")
    _flush(f"game_bridge        from: {gb.__file__}")
    try:
        _head = subprocess.check_output(
            ["git", "-C", _REPO, "rev-parse", "HEAD"],
            text=True).strip()
    except Exception as _e:
        _head = f"<git rev-parse failed: {_e}>"
    _flush(f"repo HEAD: {_head}")
    # STRIKE_SKILL_DAMAGE_K may or may not exist yet — probe attribute
    _K = getattr(fe, "STRIKE_SKILL_DAMAGE_K", None)
    _flush(f"STRIKE_SKILL_DAMAGE_K = {_K!r}  "
           f"(None = constant not yet present in engine)")
    _flush("")

    all_rows = []

    # E: striking family 88 vs 55, N=2000 (Step 2 arm E)
    fav, unf = _stats_with_family(STRIKING_FAMILY)
    all_rows.extend(run_arm("E", fav, unf, 2000))

    # F: grappling family 88 vs 55, N=2000 (Step 2 arm F)
    fav, unf = _stats_with_family(GRAPPLING_FAMILY)
    all_rows.extend(run_arm("F", fav, unf, 2000))

    # G1: boxing alone 88 vs 55, N=2000 (Step 3 arm G1)
    fav, unf = _stats_with_family(("boxing",))
    all_rows.extend(run_arm("G1", fav, unf, 2000))

    # H3: kicks 74 vs 61, N=500 (Step 5 arm H3)
    fav_h3 = dict(BASE_75); fav_h3["kicks"] = 74; fav_h3["overall_rating"] = 75
    unf_h3 = dict(BASE_75); unf_h3["kicks"] = 61; unf_h3["overall_rating"] = 75
    all_rows.extend(run_arm("H3", fav_h3, unf_h3, 500))

    # J1: all-75 symmetric, N=2000 (Step 7 P3 arm J1)
    fav_j1 = dict(BASE_75); fav_j1["overall_rating"] = 75
    unf_j1 = dict(BASE_75); unf_j1["overall_rating"] = 75
    all_rows.extend(run_arm("J1", fav_j1, unf_j1, 2000))

    csv_path = os.path.join(_HERE, f"strike_skill_dmg1_equiv_{args.tag}_raw.csv")
    with open(csv_path, "w", newline="") as fh:
        # Embed metadata as CSV comment lines
        fh.write(f"# STRIKE-SKILL-DMG1 phase 1a equivalence gate\n")
        fh.write(f"# tag: {args.tag}\n")
        fh.write(f"# repo_HEAD: {_head}\n")
        fh.write(f"# STRIKE_SKILL_DAMAGE_K: {_K!r}\n")
        fh.write(f"# fight_engine.__file__: {fe.__file__}\n")
        fh.write(f"# fight_integration.__file__: {fi.__file__}\n")
        fh.write(f"# arms: E(N=2000), F(N=2000), G1(N=2000), H3(N=500), J1(N=2000)\n")
        w = csv.DictWriter(fh, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        for r in all_rows:
            w.writerow(r)
    _flush(f"CSV: {csv_path}  ({len(all_rows)} rows)")
    _flush("DONE.")


if __name__ == "__main__":
    main()
