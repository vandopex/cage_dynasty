"""ENGINE-STRIKE-SENS1 Step 2 — striking vs grappling at 88-vs-55.

READ-ONLY. No edits to tracked files, no engine code reading, no
mechanism explanations.

F1 (fixture rule 1): NO MUTATION. Fresh GameBridge, fresh GameState,
fresh fighter objects per arm. Slot-swapped arms (E', F') are built
in the OPPOSITE ORDER from scratch — same two fighter identities
(strong / weak), assigned to slots 1/2 in reverse.

F2 (fixture rule 2): RUNTIME STAT CAPTURE at sim entry. Wrap
fi.simulate_narrated_fight with a per-sim capture; print the fa1/fa2
striking + grappling stat block observed for sim 0 of each arm and
assert against the intended spec. Mismatch → STOP.

CRN: fight_id="arm_pair" literal; per-arm fighter_ids consistent per
identity (strike_strong / strike_weak / grapple_strong / grapple_weak);
seeds 0..N-1 identical across arms. Config asserted per arm.

Arms:
  E   — striking-only, slot1 favored (strong-boxing family in slot 1)
  E'  — striking-only, slot2 favored (constructed opposite order)
  F   — grappling-only, slot1 favored
  F'  — grappling-only, slot2 favored

Grappling family used: takedowns, takedown_defense, top_control,
submissions, guard (5 attrs). All other 13 attrs held at 75/75.

Striking family used: boxing, kicks, clinch_striking, striking_defense
(4 attrs). All other 14 attrs held at 75/75.

N=2000 per arm.
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


# ---- Constants (CRN) --------------------------------------------------
CONST_FIGHT_ID = "arm_pair"

# Family definitions (printed explicitly per Van's rule).
STRIKING_FAMILY  = ("boxing", "kicks", "clinch_striking", "striking_defense")
GRAPPLING_FAMILY = ("takedowns", "takedown_defense", "top_control",
                    "submissions", "guard")

# All-75 baseline for every stat.
BASE_75 = {
    "strength": 75, "speed": 75, "cardio": 75, "chin": 75, "recovery": 75,
    "boxing": 75, "kicks": 75, "clinch_striking": 75, "striking_defense": 75,
    "takedowns": 75, "takedown_defense": 75, "top_control": 75,
    "submissions": 75, "guard": 75, "clinch_control": 75,
    "heart": 75, "fight_iq": 75, "composure": 75,
}


def _make_strong_stats(family):
    """Build a stat dict: all-75 except family = 88."""
    out = dict(BASE_75)
    for a in family: out[a] = 88
    out["overall_rating"] = 75
    return out


def _make_weak_stats(family):
    """Build a stat dict: all-75 except family = 55."""
    out = dict(BASE_75)
    for a in family: out[a] = 55
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
    """Extract the stats subset the arms manipulate."""
    return {a: getattr(fa, a, None) for a in (
        list(STRIKING_FAMILY) + list(GRAPPLING_FAMILY)
        + ["strength", "speed", "cardio", "chin", "clinch_control",
           "heart", "fight_iq", "composure", "recovery"])}


def run_arm(arm_name, favored_family_stats, unfavored_family_stats,
            favored_id_base, unfavored_id_base, N,
            favored_in_slot1: bool,
            expected_favored_fa_capture: dict,
            expected_unfavored_fa_capture: dict):
    """Build fresh bridge/gs/fighters per arm. Wrap fi's sim entry to
    capture fa1/fa2 on sim 0 for F2 proof. Run N sims, return outcomes."""
    # Fresh state
    br, gs = _make_test_bridge()

    # Fresh fighter objects. IDs are consistent per arm-identity so
    # traceability holds across E/E' (or F/F') for stat-level meaning,
    # but each arm builds a brand-new GameState + brand-new fighter
    # objects — no mutation of prior arm's state.
    _fav_id = f"{arm_name}_{favored_id_base}"
    _unf_id = f"{arm_name}_{unfavored_id_base}"
    f_favored   = _make_bare_fighter(_fav_id, _fav_id, **favored_family_stats)
    f_unfavored = _make_bare_fighter(_unf_id, _unf_id, **unfavored_family_stats)

    # "Opposite order from scratch" — the SLOT the favored fighter
    # occupies is determined by the fight dict's fighter1_id/fighter2_id,
    # which is built from the desired slot assignment. We build both
    # fighters, then order them into the fight dict per arm intent.
    if favored_in_slot1:
        _register_fighter(gs, f_favored)   # register in slot-1 semantic order
        _register_fighter(gs, f_unfavored)
        fight = _make_fight_const(f_favored.fighter_id, f_unfavored.fighter_id)
        _slot1_fighter, _slot2_fighter = f_favored, f_unfavored
    else:
        _register_fighter(gs, f_unfavored) # register in slot-1 semantic order (reversed)
        _register_fighter(gs, f_favored)
        fight = _make_fight_const(f_unfavored.fighter_id, f_favored.fighter_id)
        _slot1_fighter, _slot2_fighter = f_unfavored, f_favored

    _flush("")
    _flush("=" * 70)
    _flush(f"ARM {arm_name}   N={N}   (favored_in_slot1={favored_in_slot1})")
    _flush("=" * 70)
    _flush(f"CRN: fight_id={CONST_FIGHT_ID!r}   "
           f"fighter1_id={fight['fighter1_id']!r}   "
           f"fighter2_id={fight['fighter2_id']!r}")
    _flush(f"seed sequence: random.seed(i) for i in 0..{N-1}")
    _flush(f"favored identity: {_fav_id!r}  (stats: "
           f"{ {k: getattr(f_favored, k) for k in STRIKING_FAMILY + GRAPPLING_FAMILY} })")
    _flush(f"unfavored identity: {_unf_id!r}  (stats: "
           f"{ {k: getattr(f_unfavored, k) for k in STRIKING_FAMILY + GRAPPLING_FAMILY} })")

    # Config assertion via probe bundle.
    _b_probe = br._assemble_prefight(
        fight, _slot1_fighter, _slot2_fighter,
        _slot1_fighter.name, _slot2_fighter.name,
        _slot1_fighter.fighter_id, _slot2_fighter.fighter_id,
        **_PA_KW,
    )
    _cfg = _b_probe["config"]
    _standup = getattr(_cfg, "standup_threshold", None)
    _dmg = getattr(_cfg, "damage_multiplier", None)
    _exch = getattr(_cfg, "exchanges_per_round", None)
    _flush(f"config: standup={_standup}, damage={_dmg}, exchanges={_exch}")
    assert _standup == 10, f"standup={_standup} != 10 → voids run"

    # F2 — install runtime capture wrapper on fi.simulate_narrated_fight.
    # The wrapper records fa1/fa2 stats seen at sim entry, per sim. We
    # keep only sim 0's capture for the report (and use it to assert
    # against intended spec).
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
                fight, _slot1_fighter, _slot2_fighter,
                _slot1_fighter.name, _slot2_fighter.name,
                _slot1_fighter.fighter_id, _slot2_fighter.fighter_id,
                **_PA_KW,
            )
            eng = _run_path_a_ref(_bundle)
            outcomes.append({
                "arm":  arm_name,
                "seed": i,
                "fight_id": CONST_FIGHT_ID,
                "f1_id":  fight["fighter1_id"],
                "f2_id":  fight["fighter2_id"],
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

    # Report sim-0 captured fa1/fa2 stats.
    assert captured, "no captured sims — wrapper failed to intercept"
    _cap0 = captured[0]
    _flush(f"F2 — runtime capture, sim 0:")
    _flush(f"  fa1[{_cap0['fa1_id']}] stats: {_cap0['fa1']}")
    _flush(f"  fa2[{_cap0['fa2_id']}] stats: {_cap0['fa2']}")

    # Assert captured fa stats match intended spec for the two fighters
    # (favored vs unfavored). Which fa is which depends on slot.
    if favored_in_slot1:
        _fa_fav = _cap0["fa1"]; _fa_unf = _cap0["fa2"]
    else:
        _fa_fav = _cap0["fa2"]; _fa_unf = _cap0["fa1"]
    _mismatches = []
    for k, want in expected_favored_fa_capture.items():
        got = _fa_fav.get(k)
        if got != want:
            _mismatches.append(f"favored.{k}: got={got} want={want}")
    for k, want in expected_unfavored_fa_capture.items():
        got = _fa_unf.get(k)
        if got != want:
            _mismatches.append(f"unfavored.{k}: got={got} want={want}")
    if _mismatches:
        _flush(f"  F2 MISMATCH: {_mismatches}")
        raise RuntimeError(f"F2 stat capture mismatch in arm {arm_name}: {_mismatches}")
    _flush(f"  F2 ASSERT: captured stats match intended spec — PASS")

    return outcomes, _fav_id, _unf_id


def analyze_arm(arm_name, outcomes, favored_id, unfavored_id):
    """Per Van's spec — favored_wins / N (direct); draw count; method
    split by winner then pooled; round of finish."""
    N = len(outcomes)
    _fav_wins = sum(1 for o in outcomes if o["winner"] == favored_id)
    _unf_wins = sum(1 for o in outcomes if o["winner"] == unfavored_id)
    _draws    = sum(1 for o in outcomes if o["winner"] not in (favored_id, unfavored_id))
    p_fav = _fav_wins / N
    se = math.sqrt(p_fav * (1 - p_fav) / N) if 0 < p_fav < 1 else 0.0
    _flush("")
    _flush(f"--- arm {arm_name} report ---")
    _flush(f"1. captured stats — see F2 block above.")
    _flush(f"2. p(favored wins) = favored_wins / N = {_fav_wins}/{N} = {p_fav:.4f}  "
           f"±2σ = ±{2*se:.4f}")
    _flush(f"3. draws: {_draws} / {N}   (favored={_fav_wins}, unfavored={_unf_wins}, "
           f"sum={_fav_wins+_unf_wins+_draws})")

    by_fav_win = Counter(o["method"] for o in outcomes if o["winner"] == favored_id)
    by_unf_win = Counter(o["method"] for o in outcomes if o["winner"] == unfavored_id)
    by_draw    = Counter(o["method"] for o in outcomes if o["winner"] not in (favored_id, unfavored_id))
    pooled     = Counter(o["method"] for o in outcomes)
    _flush(f"4. Method — split by winner:")
    _flush(f"   winner=favored   (n={_fav_wins}): {dict(by_fav_win)}")
    _flush(f"   winner=unfavored (n={_unf_wins}): {dict(by_unf_win)}")
    if _draws:
        _flush(f"   draws           (n={_draws}): {dict(by_draw)}")
    _flush(f"   pooled           (n={N}): {dict(pooled)}")

    _decision_set = {"Unanimous Decision", "Split Decision",
                     "Majority Decision", "Draw"}
    finishes = [o for o in outcomes if o["method"] not in _decision_set]
    finish_rounds = Counter(o["total_rounds"] for o in finishes)
    _flush(f"5. Round of finish (finishes only, n={len(finishes)}, field=total_rounds):")
    _flush(f"   distribution: "
           f"{dict(sorted(finish_rounds.items(), key=lambda x: (x[0] is None, x[0])))}")


def analyze_slot_pair(pair_name, outcomes_slot1_fav, outcomes_slot2_fav,
                       favored_id):
    """Compare p(favored wins) when favored is in slot 1 vs slot 2."""
    N1 = len(outcomes_slot1_fav)
    N2 = len(outcomes_slot2_fav)
    _fav_wins_1 = sum(1 for o in outcomes_slot1_fav if o["winner"] == favored_id)
    # In slot2-favored arm, the favored fighter has a different ID
    # (arm-name-prefixed). Detect by "favored_id" logged per row.
    _fav_wins_2 = sum(1 for o in outcomes_slot2_fav if o["winner"] == o["favored_id"])
    p1 = _fav_wins_1 / N1
    p2 = _fav_wins_2 / N2
    se1 = math.sqrt(p1*(1-p1)/N1) if 0 < p1 < 1 else 0.0
    se2 = math.sqrt(p2*(1-p2)/N2) if 0 < p2 < 1 else 0.0
    diff = p1 - p2
    diff_se = math.sqrt(se1**2 + se2**2)  # independent-samples approx
    _flush("")
    _flush("=" * 70)
    _flush(f"SLOT-BIAS TEST — {pair_name}")
    _flush("=" * 70)
    _flush(f"  favored in slot 1: p(favored wins) = {_fav_wins_1}/{N1} = "
           f"{p1:.4f}  ±2σ = ±{2*se1:.4f}")
    _flush(f"  favored in slot 2: p(favored wins) = {_fav_wins_2}/{N2} = "
           f"{p2:.4f}  ±2σ = ±{2*se2:.4f}")
    _flush(f"  Δ (slot1 − slot2) = {diff:+.4f}   ±2σ ≈ ±{2*diff_se:.4f}   "
           "(independent-samples SE)")


def main():
    N = 2000

    _flush("=" * 70)
    _flush("ENGINE-STRIKE-SENS1 Step 2 — striking vs grappling at 88-vs-55")
    _flush("=" * 70)
    _flush(f"fight_engine       from: {fe.__file__}")
    _flush(f"fight_integration  from: {fi.__file__}")
    _flush(f"game_bridge        from: {gb.__file__}")
    _flush(f"STRIKING_FAMILY  ({len(STRIKING_FAMILY)} attrs): {STRIKING_FAMILY}")
    _flush(f"GRAPPLING_FAMILY ({len(GRAPPLING_FAMILY)} attrs): {GRAPPLING_FAMILY}")
    _flush(f"All non-target attrs held at 75 for BOTH fighters.")

    # ---- Arm E — striking family, favored in slot 1 ----
    _strong_stat = _make_strong_stats(STRIKING_FAMILY)
    _weak_stat   = _make_weak_stats(STRIKING_FAMILY)
    # Expected fa capture: family=88 (favored) / 55 (unfavored), others=75
    _exp_fav_str = {**{a: 88 for a in STRIKING_FAMILY},
                     **{a: 75 for a in GRAPPLING_FAMILY}}
    _exp_unf_str = {**{a: 55 for a in STRIKING_FAMILY},
                     **{a: 75 for a in GRAPPLING_FAMILY}}
    out_E, favE, unfE = run_arm(
        "E", _strong_stat, _weak_stat, "strike_strong", "strike_weak", N,
        favored_in_slot1=True,
        expected_favored_fa_capture=_exp_fav_str,
        expected_unfavored_fa_capture=_exp_unf_str,
    )
    analyze_arm("E", out_E, favE, unfE)

    out_Ep, favEp, unfEp = run_arm(
        "E'", _strong_stat, _weak_stat, "strike_strong", "strike_weak", N,
        favored_in_slot1=False,
        expected_favored_fa_capture=_exp_fav_str,
        expected_unfavored_fa_capture=_exp_unf_str,
    )
    analyze_arm("E'", out_Ep, favEp, unfEp)

    analyze_slot_pair("STRIKING (E vs E')", out_E, out_Ep, favE)

    # ---- Arm F — grappling family, favored in slot 1 ----
    _strong_stat_g = _make_strong_stats(GRAPPLING_FAMILY)
    _weak_stat_g   = _make_weak_stats(GRAPPLING_FAMILY)
    _exp_fav_g = {**{a: 75 for a in STRIKING_FAMILY},
                   **{a: 88 for a in GRAPPLING_FAMILY}}
    _exp_unf_g = {**{a: 75 for a in STRIKING_FAMILY},
                   **{a: 55 for a in GRAPPLING_FAMILY}}
    out_F, favF, unfF = run_arm(
        "F", _strong_stat_g, _weak_stat_g, "grapple_strong", "grapple_weak", N,
        favored_in_slot1=True,
        expected_favored_fa_capture=_exp_fav_g,
        expected_unfavored_fa_capture=_exp_unf_g,
    )
    analyze_arm("F", out_F, favF, unfF)

    out_Fp, favFp, unfFp = run_arm(
        "F'", _strong_stat_g, _weak_stat_g, "grapple_strong", "grapple_weak", N,
        favored_in_slot1=False,
        expected_favored_fa_capture=_exp_fav_g,
        expected_unfavored_fa_capture=_exp_unf_g,
    )
    analyze_arm("F'", out_Fp, favFp, unfFp)

    analyze_slot_pair("GRAPPLING (F vs F')", out_F, out_Fp, favF)

    # CSV dump — all rows.
    csv_path = os.path.join(_HERE, "engine_strike_sens1_step2_raw.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["arm", "seed", "fight_id", "f1_id", "f2_id",
                    "favored_id", "unfavored_id",
                    "winner", "method", "total_rounds"])
        for o in out_E + out_Ep + out_F + out_Fp:
            w.writerow([o["arm"], o["seed"], o["fight_id"],
                        o["f1_id"], o["f2_id"],
                        o["favored_id"], o["unfavored_id"],
                        o["winner"], o["method"], o["total_rounds"]])
    _flush("")
    _flush(f"CSV dump: {csv_path}  ({4*N} rows)")

    _flush("")
    _flush("DONE — numbers only, no interpretation.")


if __name__ == "__main__":
    main()
