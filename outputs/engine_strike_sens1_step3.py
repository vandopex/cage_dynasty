"""ENGINE-STRIKE-SENS1 Step 3 — per-striking-stat localization.

READ-ONLY. No edits to tracked files, no engine code reading, no
mechanism explanations.

Rules carry from Step 2:
  F1 — fresh GameBridge + GameState + fighter objects per arm.
       No mutation between arms.
  F2 — runtime stat capture at sim entry (wrap fi.simulate_narrated_fight),
       print fa1/fa2 stats on sim 0 of each arm, STOP on mismatch.
  CRN — constant fight_id="arm_pair", per-arm consistent fighter_ids,
        seeds 0..N-1.
  Config header + assert standup == 10 per arm.
  Favored fighter in slot 1 (no slot mirrors — falsified in Step 2).

Arms (all non-target stats 75/75 for both fighters; N=2000 each):
  G1 — boxing alone:            88 vs 55
  G2 — kicks alone:             88 vs 55
  G3 — clinch_striking alone:   88 vs 55
  G4 — striking_defense alone:  88 vs 55
  G5 — offense trio (boxing, kicks, clinch_striking) 88 vs 55,
       striking_defense at 75/75

Per-arm report: F2 capture, p(favored)=favored_wins/N w/ 2σ, draw
count, method split by winner, decisions split separately (fav
decision wins / total decisions).

Summary table at end: arm, p(favored), decision-win share, KO+TKO
count for favored. Includes Step 2's E row for comparison.

CSV dump: outputs/engine_strike_sens1_step3_raw.csv
"""
import os, sys, time, random, math, csv
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


def _stats_with_family(family_names, val_favored=88, val_unfavored=55):
    """Return (favored_stats, unfavored_stats) — dicts with the given
    family attrs set to val_favored/val_unfavored, everything else 75."""
    fav = dict(BASE_75); unf = dict(BASE_75)
    for a in family_names:
        fav[a] = val_favored
        unf[a] = val_unfavored
    fav["overall_rating"] = 75
    unf["overall_rating"] = 75
    return fav, unf


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


DECISION_SET = {"Unanimous Decision", "Split Decision",
                "Majority Decision", "Draw"}
FINISH_KO_SET_PREFIX = ("KO",)  # methods starting with "KO"
FINISH_TKO_SET_PREFIX = ("TKO",)


def _is_ko_or_tko(method):
    if method is None: return False
    return method.startswith("KO") or method.startswith("TKO")


def run_arm(arm_name, family_names, N):
    """Fresh bridge/gs/fighters, favored in slot 1, F2 capture, run N."""
    fav_stats, unf_stats = _stats_with_family(family_names)

    br, gs = _make_test_bridge()

    _fav_id = f"{arm_name}_favored"
    _unf_id = f"{arm_name}_unfavored"
    f_favored   = _make_bare_fighter(_fav_id, _fav_id, **fav_stats)
    f_unfavored = _make_bare_fighter(_unf_id, _unf_id, **unf_stats)
    _register_fighter(gs, f_favored)
    _register_fighter(gs, f_unfavored)
    fight = _make_fight_const(f_favored.fighter_id, f_unfavored.fighter_id)

    _flush("")
    _flush("=" * 70)
    _flush(f"ARM {arm_name}   N={N}   family={family_names}   "
           f"favored_in_slot1=True")
    _flush("=" * 70)
    _flush(f"CRN: fight_id={CONST_FIGHT_ID!r}   "
           f"fighter1_id={fight['fighter1_id']!r}   "
           f"fighter2_id={fight['fighter2_id']!r}")
    _flush(f"seed sequence: random.seed(i) for i in 0..{N-1}")

    # Config assertion via probe bundle.
    _b_probe = br._assemble_prefight(
        fight, f_favored, f_unfavored,
        f_favored.name, f_unfavored.name,
        f_favored.fighter_id, f_unfavored.fighter_id,
        **_PA_KW,
    )
    _cfg = _b_probe["config"]
    _standup = getattr(_cfg, "standup_threshold", None)
    _dmg = getattr(_cfg, "damage_multiplier", None)
    _exch = getattr(_cfg, "exchanges_per_round", None)
    _flush(f"config: standup={_standup}, damage={_dmg}, exchanges={_exch}")
    assert _standup == 10, f"standup={_standup} != 10"

    # F2 wrapper — capture per-sim fa1/fa2 stats.
    captured = []
    _original_snf = fi.simulate_narrated_fight
    def _snf_capture(fa1_, fa2_, *args, **kwargs):
        captured.append({
            "sim_idx": len(captured),
            "fa1_id":  getattr(fa1_, 'fighter_id', None),
            "fa2_id":  getattr(fa2_, 'fighter_id', None),
            "fa1":     _fa_stats_dict(fa1_),
            "fa2":     _fa_stats_dict(fa2_),
        })
        return _original_snf(fa1_, fa2_, *args, **kwargs)
    fi.simulate_narrated_fight = _snf_capture

    outcomes = []
    t0 = time.perf_counter()
    try:
        for i in range(N):
            random.seed(i)
            _bundle = br._assemble_prefight(
                fight, f_favored, f_unfavored,
                f_favored.name, f_unfavored.name,
                f_favored.fighter_id, f_unfavored.fighter_id,
                **_PA_KW,
            )
            eng = _run_path_a_ref(_bundle)
            outcomes.append({
                "arm":  arm_name,
                "seed": i,
                "fight_id": CONST_FIGHT_ID,
                "f1_id": fight["fighter1_id"],
                "f2_id": fight["fighter2_id"],
                "favored_id":   _fav_id,
                "unfavored_id": _unf_id,
                "winner": getattr(eng, "winner_id", None),
                "method": getattr(eng, "method", None),
                "total_rounds": getattr(eng, "total_rounds", None),
            })
    finally:
        fi.simulate_narrated_fight = _original_snf
    dt = time.perf_counter() - t0
    _flush(f"arm {arm_name} wall clock: {dt:.2f} sec  "
           f"({dt*1000/N:.2f} ms/sim)")

    # F2 assert on sim 0
    assert captured, "no captured sims — wrapper failed"
    _cap0 = captured[0]
    _flush(f"F2 — runtime capture, sim 0:")
    _flush(f"  fa1[{_cap0['fa1_id']}] stats: {_cap0['fa1']}")
    _flush(f"  fa2[{_cap0['fa2_id']}] stats: {_cap0['fa2']}")
    _mismatches = []
    # fav is slot 1 in every Step 3 arm
    for a in family_names:
        if _cap0["fa1"].get(a) != 88:
            _mismatches.append(f"fa1.{a}: got={_cap0['fa1'].get(a)} want=88")
        if _cap0["fa2"].get(a) != 55:
            _mismatches.append(f"fa2.{a}: got={_cap0['fa2'].get(a)} want=55")
    _all_attrs = set(STRIKING_FAMILY) | set(GRAPPLING_FAMILY)
    for a in (_all_attrs - set(family_names)):
        if _cap0["fa1"].get(a) != 75:
            _mismatches.append(f"fa1.{a}: got={_cap0['fa1'].get(a)} want=75")
        if _cap0["fa2"].get(a) != 75:
            _mismatches.append(f"fa2.{a}: got={_cap0['fa2'].get(a)} want=75")
    if _mismatches:
        _flush(f"  F2 MISMATCH: {_mismatches}")
        raise RuntimeError(f"F2 stat capture mismatch in arm {arm_name}")
    _flush(f"  F2 ASSERT: captured stats match intended spec — PASS")

    return outcomes, _fav_id, _unf_id


def analyze_arm(arm_name, outcomes, favored_id, unfavored_id):
    N = len(outcomes)
    _fav_wins = sum(1 for o in outcomes if o["winner"] == favored_id)
    _unf_wins = sum(1 for o in outcomes if o["winner"] == unfavored_id)
    _draws    = sum(1 for o in outcomes if o["winner"] not in (favored_id, unfavored_id))
    p_fav = _fav_wins / N
    se = math.sqrt(p_fav * (1 - p_fav) / N) if 0 < p_fav < 1 else 0.0
    _flush("")
    _flush(f"--- arm {arm_name} report ---")
    _flush(f"1. captured stats — see F2 block above.")
    _flush(f"2. p(favored wins) = {_fav_wins}/{N} = {p_fav:.4f}  ±2σ = ±{2*se:.4f}")
    _flush(f"3. draws: {_draws}   (favored={_fav_wins}, unfavored={_unf_wins})")

    by_fav = Counter(o["method"] for o in outcomes if o["winner"] == favored_id)
    by_unf = Counter(o["method"] for o in outcomes if o["winner"] == unfavored_id)
    _flush(f"4. Method — split by winner:")
    _flush(f"   winner=favored   (n={_fav_wins}): {dict(by_fav)}")
    _flush(f"   winner=unfavored (n={_unf_wins}): {dict(by_unf)}")

    # Decisions split
    _fav_dec = sum(1 for o in outcomes
                    if o["winner"] == favored_id and o["method"] in DECISION_SET)
    _unf_dec = sum(1 for o in outcomes
                    if o["winner"] == unfavored_id and o["method"] in DECISION_SET)
    _total_dec = _fav_dec + _unf_dec + sum(1 for o in outcomes if o["method"] == "Draw")
    _dec_share_fav = _fav_dec / _total_dec if _total_dec else 0.0
    _flush(f"5. Decisions (Unan/Split/Majority/Draw): total_dec={_total_dec}, "
           f"fav_dec={_fav_dec}, unf_dec={_unf_dec}, draws={_total_dec - _fav_dec - _unf_dec}")
    _flush(f"   fav decision-win share = {_fav_dec}/{_total_dec} = "
           f"{_dec_share_fav:.4f}")

    # KO+TKO for favored
    _fav_kotko = sum(1 for o in outcomes
                      if o["winner"] == favored_id and _is_ko_or_tko(o["method"]))
    _flush(f"6. KO+TKO for favored: {_fav_kotko}")

    return {
        "arm": arm_name,
        "N": N,
        "p_fav": p_fav,
        "se2": 2*se,
        "fav_wins": _fav_wins,
        "unf_wins": _unf_wins,
        "draws": _draws,
        "fav_dec": _fav_dec,
        "unf_dec": _unf_dec,
        "total_dec": _total_dec,
        "dec_share_fav": _dec_share_fav,
        "fav_kotko": _fav_kotko,
    }


def main():
    N = 2000

    _flush("=" * 70)
    _flush("ENGINE-STRIKE-SENS1 Step 3 — per-striking-stat localization")
    _flush("=" * 70)
    _flush(f"fight_engine       from: {fe.__file__}")
    _flush(f"fight_integration  from: {fi.__file__}")
    _flush(f"game_bridge        from: {gb.__file__}")
    _flush(f"STRIKING_FAMILY  (4 attrs): {STRIKING_FAMILY}")
    _flush(f"GRAPPLING_FAMILY (5 attrs): {GRAPPLING_FAMILY}")
    _flush(f"All non-target attrs held at 75 for BOTH fighters.")

    summaries = []
    all_outcomes = []
    ARMS = [
        ("G1", ("boxing",)),
        ("G2", ("kicks",)),
        ("G3", ("clinch_striking",)),
        ("G4", ("striking_defense",)),
        ("G5", ("boxing", "kicks", "clinch_striking")),
    ]
    for name, family in ARMS:
        outc, favid, unfid = run_arm(name, family, N)
        summ = analyze_arm(name, outc, favid, unfid)
        summ["family"] = family
        summaries.append(summ)
        all_outcomes.extend(outc)

    # Step 2 E row (for comparison) — read from prior CSV to avoid re-run.
    _E_row = {
        "arm": "E (Step 2)",
        "N": 2000,
        "family": ("boxing", "kicks", "clinch_striking", "striking_defense"),
        "p_fav": 1073/2000,
        "se2": 2*math.sqrt((1073/2000)*(1-1073/2000)/2000),
        "fav_wins": 1073,
        "unf_wins": 859,
        "draws": 68,
        # Decisions from Step 2 arm E raw:
        # winner=fav: UD=521, MD=24 → fav_dec = 545
        # winner=unfav: UD=435, MD=17 → unf_dec = 452
        # Draw method count from pooled: Draw=68
        "fav_dec": 545,
        "unf_dec": 452,
        "total_dec": 545+452+68,
        "dec_share_fav": 545/(545+452+68),
        # KO+TKO for favored from Step 2 arm E winner=fav method dist:
        # KO=200, TKO=66, TKO(Doctor)=37, TKO(Body)=19, TKO(Legs)=12,
        # KO(HK)=10, KO(FK)=9, KO(SP)=1, TKO(GnP)=2, TKO(Ref)=1
        # = 200+66+37+19+12+10+9+1+2+1 = 357
        "fav_kotko": 357,
    }

    _flush("")
    _flush("=" * 70)
    _flush("SUMMARY TABLE (Step 3 arms + Step 2 arm E for comparison)")
    _flush("=" * 70)
    _flush(f"  {'arm':<12} {'family':<45} {'p_fav':>7} {'±2σ':>7} "
           f"{'dec_share_fav':>14} {'fav_KO+TKO':>12}")
    for s in [_E_row] + summaries:
        _fam_str = "+".join(s["family"])
        _flush(f"  {s['arm']:<12} {_fam_str:<45} {s['p_fav']:>7.4f} "
               f"{s['se2']:>7.4f} {s['dec_share_fav']:>14.4f} {s['fav_kotko']:>12}")

    # CSV dump
    csv_path = os.path.join(_HERE, "engine_strike_sens1_step3_raw.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["arm", "seed", "fight_id", "f1_id", "f2_id",
                    "favored_id", "unfavored_id",
                    "winner", "method", "total_rounds"])
        for o in all_outcomes:
            w.writerow([o["arm"], o["seed"], o["fight_id"],
                        o["f1_id"], o["f2_id"],
                        o["favored_id"], o["unfavored_id"],
                        o["winner"], o["method"], o["total_rounds"]])
    _flush("")
    _flush(f"CSV dump: {csv_path}  ({len(all_outcomes)} rows)")

    _flush("")
    _flush("DONE — numbers only, no interpretation.")


if __name__ == "__main__":
    main()
