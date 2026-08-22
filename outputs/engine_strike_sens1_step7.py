"""ENGINE-STRIKE-SENS1 Step 7 — P1 classifier audit + P2 hit-chance
sweep + P3 classifier-pinned fight arms.

READ-ONLY. Writes outputs/ only.
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

# Direct imports of the classifier + resolution primitives per prompt.
from fight_engine import (
    detect_fighter_style,
    is_grappler,
    calculate_strike_success,
    calculate_strike_damage,
    FighterAttributes,
    FighterState,
    FightState,
    Position,
    StrikeType,
    FightConfig,
)


def _flush(m=""): print(m, flush=True)


# =====================================================================
# P1 — classifier audit
# =====================================================================
def _fa(fid, **kw):
    """Build FighterAttributes from a stats dict (all 18 attrs)."""
    defaults = dict(
        strength=75, speed=75, cardio=75, chin=75, recovery=75,
        boxing=75, kicks=75, clinch_striking=75, striking_defense=75,
        takedowns=75, takedown_defense=75, top_control=75,
        submissions=75, guard=75, clinch_control=75,
        heart=75, fight_iq=75, composure=75,
    )
    defaults.update(kw)
    return FighterAttributes(fighter_id=fid, name=fid, **defaults)


def _step1_stats():
    """STATS_X_EQ/Y_EQ/X_STR/X_GR_STR/OVERWHELMING/OVERMATCHED override boxing/
    kicks/clinch_striking/striking_defense (+ some others). All non-override
    attrs come from _make_bare_fighter's DEFAULTS block: strength/speed/cardio/
    chin/recovery/heart/fight_iq/composure = 70/70/70/70/70/72/70/70;
    takedowns/td_def/top_control/subs/guard/clinch_control = 65/70/65/60/65/65.
    """
    step1_defaults = dict(
        strength=70, speed=70, cardio=70, chin=70, recovery=70,
        takedowns=65, takedown_defense=70, top_control=65,
        submissions=60, guard=65, clinch_control=65,
        heart=72, fight_iq=70, composure=70,
    )
    def _mk(name, **overrides):
        d = dict(step1_defaults)
        d.update(dict(boxing=75, kicks=75, clinch_striking=75, striking_defense=75))
        d.update(overrides)
        return _fa(name, **d)
    # STATS_X_EQ / Y_EQ / X_STR / X_GR_STR from partB.py:128-138
    x_eq = _mk("S1_X_EQ", boxing=80, kicks=70, clinch_striking=65, striking_defense=70)
    y_eq = _mk("S1_Y_EQ", boxing=70, kicks=80, clinch_striking=65, striking_defense=70)
    x_str = _mk("S1_X_STR", boxing=100, kicks=90, clinch_striking=85, striking_defense=90)
    x_gr_str = _mk("S1_X_GR_STR", boxing=80, kicks=70, clinch_striking=65, striking_defense=70,
                    takedowns=85, takedown_defense=90, top_control=85, submissions=80, guard=85)
    overwhelming = _mk("S1_OVERWHELMING",
                        strength=88, speed=88, cardio=88, chin=85,
                        boxing=88, kicks=85, striking_defense=88,
                        takedown_defense=88, fight_iq=88, composure=88)
    overmatched  = _mk("S1_OVERMATCHED",
                        strength=55, speed=55, cardio=55, chin=52,
                        boxing=55, kicks=52, striking_defense=55,
                        takedown_defense=55, fight_iq=55, composure=55)
    # Pilot arm A was symmetric all-75 defaults per Step 0
    pilot = _mk("S1_pilot", boxing=70, kicks=70, clinch_striking=65, striking_defense=70)
    # Arm A used x_eq / y_eq
    # Arm B used x_str vs y_eq. Arm B' — slot swap — same identities
    # Arm C used x_gr_str vs y_eq. Arm D used overwhelming vs overmatched
    return [
        ("Step1_pilot_slot1", pilot),
        ("Step1_pilot_slot2", pilot),
        ("Step1_A_slot1_XEQ", x_eq),
        ("Step1_A_slot2_YEQ", y_eq),
        ("Step1_B_slot1_XSTR", x_str),
        ("Step1_B_slot2_YEQ", y_eq),
        ("Step1_Bp_slot1_YEQ", y_eq),
        ("Step1_Bp_slot2_XSTR", x_str),
        ("Step1_C_slot1_XGRSTR", x_gr_str),
        ("Step1_C_slot2_YEQ", y_eq),
        ("Step1_D_slot1_OVERWHELMING", overwhelming),
        ("Step1_D_slot2_OVERMATCHED", overmatched),
    ]


def _step2_stats():
    """Step 2 E/F fighters: BASE_75 with one family at 88 or 55."""
    def _fam(name, family_names, val):
        kw = {a: val for a in family_names}
        return _fa(name, **kw)
    E_fav = _fam("Step2_E_fav_STRIKE88",
                 ("boxing", "kicks", "clinch_striking", "striking_defense"), 88)
    E_unf = _fam("Step2_E_unf_STRIKE55",
                 ("boxing", "kicks", "clinch_striking", "striking_defense"), 55)
    F_fav = _fam("Step2_F_fav_GRAPPLE88",
                 ("takedowns", "takedown_defense", "top_control", "submissions", "guard"), 88)
    F_unf = _fam("Step2_F_unf_GRAPPLE55",
                 ("takedowns", "takedown_defense", "top_control", "submissions", "guard"), 55)
    return [
        ("Step2_E_slot1_favored", E_fav),
        ("Step2_E_slot2_unfavored", E_unf),
        ("Step2_F_slot1_favored", F_fav),
        ("Step2_F_slot2_unfavored", F_unf),
    ]


def _step3_stats():
    def _one(name, attr, val):
        kw = {attr: val}
        return _fa(name, **kw)
    out = []
    for arm, attrs in [("G1", ("boxing",)),
                        ("G2", ("kicks",)),
                        ("G3", ("clinch_striking",)),
                        ("G4", ("striking_defense",)),
                        ("G5", ("boxing", "kicks", "clinch_striking"))]:
        kw88 = {a: 88 for a in attrs}
        kw55 = {a: 55 for a in attrs}
        out.append((f"Step3_{arm}_slot1_favored", _fa(f"Step3_{arm}_favored", **kw88)))
        out.append((f"Step3_{arm}_slot2_unfavored", _fa(f"Step3_{arm}_unfavored", **kw55)))
    return out


def _step5_stats():
    # H1 both all-75; H2 boxing 88/55; H3 kicks 74/61
    return [
        ("Step5_H1_slot1", _fa("Step5_H1_fav")),
        ("Step5_H1_slot2", _fa("Step5_H1_unf")),
        ("Step5_H2_slot1_boxing88", _fa("Step5_H2_fav", boxing=88)),
        ("Step5_H2_slot2_boxing55", _fa("Step5_H2_unf", boxing=55)),
        ("Step5_H3_slot1_kicks74", _fa("Step5_H3_fav", kicks=74)),
        ("Step5_H3_slot2_kicks61", _fa("Step5_H3_unf", kicks=61)),
    ]


def part1_classifier_audit():
    _flush("=" * 70)
    _flush("P1 — CLASSIFIER AUDIT")
    _flush("=" * 70)
    _flush(f"detect_fighter_style loaded from: {detect_fighter_style.__module__}")
    _flush(f"is_grappler         loaded from: {is_grappler.__module__}")
    all_fixtures = (_step1_stats() + _step2_stats()
                    + _step3_stats() + _step5_stats())
    _flush(f"{'label':<40} {'style':<20} {'is_grappler':<12}")
    for label, fa in all_fixtures:
        _style = detect_fighter_style(fa)
        _ig = is_grappler(fa)
        _flush(f"{label:<40} {_style:<20} {str(_ig):<12}")


# =====================================================================
# P2 — resolution-layer direct probe
# =====================================================================
def part2_hit_chance_sweep():
    _flush("")
    _flush("=" * 70)
    _flush("P2 — HIT-CHANCE SWEEP (calculate_strike_success direct calls)")
    _flush("=" * 70)
    _flush(f"calculate_strike_success loaded from: {calculate_strike_success.__module__}")
    # Print confirmation that grappler-pressure branches cannot fire.
    _flush("branch-cold verification:")
    _flush("  attacker.takedowns=50, defender.takedowns=50 → defender.takedowns >= 60 "
           f"is {50 >= 60} (branch at fight_engine.py:2302 cold)")
    _flush("  defender.guard=50 → defender.guard >= 75 "
           f"is {50 >= 75} (branch at :2310 cold; >= 85 at :2308 cold)")
    _flush("  takedown_threat = def.td − att.td = 0 → all `>= 30/20/10` "
           "branches at :2313-2319 cold")
    _flush("  sub_threat = def.sub − att.sub = 0 → all `>= 30/20` "
           "branches at :2322-2325 cold")
    _flush("  defender.kicks=50 → attacker.kicks>=80 AND defender.kicks<60 "
           f"kick accuracy bonus at :2280 fires only if attacker.kicks>=80 AND defender.kicks<60.")
    _flush("  (For this sweep we use JAB/CROSS only — kick branch not entered.)")

    # Build FighterState with full stamina, not rocked.
    def _fs(fid):
        return FighterState(fighter_id=fid, name=fid, health=100.0, stamina=100.0)

    def _fight_state():
        # Position must be in STANDING_POSITIONS for the striking branch
        # to enter the grappler-pressure block (which we confirmed is cold).
        return FightState(
            fighter1=_fs("A"), fighter2=_fs("B"),
            position=Position.STANDING_OPEN,
        )

    def _mk_atk(**kw):
        base = dict(boxing=75, kicks=75, clinch_striking=75, striking_defense=75,
                     takedowns=50, submissions=50, guard=50,
                     speed=75, strength=75, cardio=75, chin=75,
                     takedown_defense=50, top_control=50, clinch_control=75,
                     heart=75, fight_iq=75, composure=75, recovery=75)
        base.update(kw)
        return FighterAttributes(fighter_id="atk", name="atk", **base)

    def _mk_def(**kw):
        base = dict(boxing=75, kicks=75, clinch_striking=75, striking_defense=75,
                     takedowns=50, submissions=50, guard=50,
                     speed=75, strength=75, cardio=75, chin=75,
                     takedown_defense=50, top_control=50, clinch_control=75,
                     heart=75, fight_iq=75, composure=75, recovery=75)
        base.update(kw)
        return FighterAttributes(fighter_id="dfd", name="dfd", **base)

    pairs = [
        (55, 75), (65, 75), (75, 75), (85, 75), (95, 75),
        (75, 55), (75, 95),
    ]
    N = 100000
    _flush(f"\nsweep: N={N} per pair; JAB/CROSS mix (random per call)")
    _flush(f"{'atk_boxing':>10} {'def_sd':>7}  {'landed':>10}  {'rate':>8}  {'2σ':>8}")
    for atk_bx, def_sd in pairs:
        _atk = _mk_atk(boxing=atk_bx)
        _def = _mk_def(striking_defense=def_sd)
        _atk_state = _fs("atk"); _def_state = _fs("dfd")
        _fst = FightState(fighter1=_atk_state, fighter2=_def_state,
                           position=Position.STANDING_OPEN)
        random.seed(20260821)  # deterministic per pair
        _landed = 0
        for i in range(N):
            _strike = StrikeType.JAB if random.random() < 0.5 else StrikeType.CROSS
            landed, _ = calculate_strike_success(
                _atk, _def, _strike, _atk_state, _def_state, _fst)
            if landed: _landed += 1
        _rate = _landed / N
        _se = math.sqrt(_rate * (1 - _rate) / N)
        _flush(f"{atk_bx:>10} {def_sd:>7}  {_landed:>10}  {_rate:>8.5f}  {2*_se:>8.5f}")


# =====================================================================
# P3 — classifier-pinned fight arms (Step-5 style harness)
# =====================================================================
CONST_FIGHT_ID = "arm_pair"


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
        ("strength", overrides.get("strength", 75)),
        ("speed", overrides.get("speed", 75)),
        ("cardio", overrides.get("cardio", 75)),
        ("chin", overrides.get("chin", 75)),
        ("recovery", overrides.get("recovery", 75)),
        ("boxing", overrides.get("boxing", 75)),
        ("kicks", overrides.get("kicks", 75)),
        ("clinch_striking", overrides.get("clinch_striking", 75)),
        ("striking_defense", overrides.get("striking_defense", 75)),
        ("takedowns", overrides.get("takedowns", 75)),
        ("takedown_defense", overrides.get("takedown_defense", 75)),
        ("top_control", overrides.get("top_control", 75)),
        ("submissions", overrides.get("submissions", 75)),
        ("guard", overrides.get("guard", 75)),
        ("clinch_control", overrides.get("clinch_control", 75)),
        ("heart", overrides.get("heart", 75)),
        ("fight_iq", overrides.get("fight_iq", 75)),
        ("composure", overrides.get("composure", 75)),
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


STAT_KEYS = ("sig_strikes_landed", "td_landed", "sub_att",
             "control_time", "damage", "knockdowns")


def _sum_rounds(round_dicts):
    tot = {k: 0.0 for k in STAT_KEYS}
    for rd in round_dicts:
        for k in STAT_KEYS:
            tot[k] += rd.get(k, 0)
    return tot


def run_arm_j(arm_name, fav_stats, unf_stats, N,
              extra_cliff_check=None):
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

    # ── Classifier verification: BOTH fighters must be "balanced" ──
    _fa_fav = FighterAttributes(fighter_id=_fav_id, name=_fav_id, **{k: getattr(f_favored, k)
        for k in ("strength","speed","cardio","chin","recovery","boxing","kicks",
                  "clinch_striking","striking_defense","takedowns","takedown_defense",
                  "top_control","submissions","guard","clinch_control",
                  "heart","fight_iq","composure")})
    _fa_unf = FighterAttributes(fighter_id=_unf_id, name=_unf_id, **{k: getattr(f_unfavored, k)
        for k in ("strength","speed","cardio","chin","recovery","boxing","kicks",
                  "clinch_striking","striking_defense","takedowns","takedown_defense",
                  "top_control","submissions","guard","clinch_control",
                  "heart","fight_iq","composure")})
    _style_fav = detect_fighter_style(_fa_fav)
    _style_unf = detect_fighter_style(_fa_unf)
    _flush(f"CLASSIFIER: favored={_style_fav!r}  unfavored={_style_unf!r}")
    if _style_fav != "balanced" or _style_unf != "balanced":
        _flush(f"CLASSIFIER FAIL — one or both fighters not balanced. STOP arm {arm_name}.")
        raise RuntimeError(f"arm {arm_name}: classifier not pinned to balanced")
    _flush(f"CLASSIFIER OK — both fighters return 'balanced'.")

    # Extra cliff/gate verification
    if extra_cliff_check:
        for label, expr, expected in extra_cliff_check:
            _got = expr()
            _flush(f"CLIFF CHECK: {label} = {_got} (expected {expected}); "
                   f"{'PASS' if _got == expected else 'FAIL'}")
            if _got != expected:
                raise RuntimeError(f"arm {arm_name}: cliff check {label} failed")

    _b_probe = br._assemble_prefight(
        fight, f_favored, f_unfavored,
        f_favored.name, f_unfavored.name,
        f_favored.fighter_id, f_unfavored.fighter_id, **_PA_KW,
    )
    _cfg = _b_probe["config"]
    _flush(f"config: standup={getattr(_cfg,'standup_threshold',None)}, "
           f"damage={getattr(_cfg,'damage_multiplier',None)}")
    assert getattr(_cfg, 'standup_threshold', None) == 10

    per_fight_rows = []
    fav_wins = unf_wins = draws = 0
    t0 = time.perf_counter()
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
    dt = time.perf_counter() - t0
    _flush(f"arm {arm_name} wall clock: {dt:.2f} sec  ({dt*1000/N:.2f} ms/sim)")
    return per_fight_rows, fav_wins, unf_wins, draws


def analyze_arm(arm_name, rows, fav_wins, unf_wins, draws, N,
                baseline_rows=None):
    _flush("")
    _flush(f"--- arm {arm_name} report ---")
    p_fav = fav_wins / N
    se = math.sqrt(p_fav * (1 - p_fav) / N) if 0 < p_fav < 1 else 0.0
    _flush(f"p(favored) = {fav_wins}/{N} = {p_fav:.4f}  ±2σ = ±{2*se:.4f}   "
           f"(unfav={unf_wins}, draws={draws})")
    # Fav − unfav paired differentials for THIS arm
    _flush(f"paired favored − unfavored differential (this arm):")
    for f in STAT_KEYS:
        diffs = [r["fav"][f] - r["unf"][f] for r in rows]
        _mean = statistics.mean(diffs)
        _sd = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
        _se = _sd / math.sqrt(len(diffs)) if len(diffs) > 1 else 0.0
        _flush(f"  Δ({f:<26}) = {_mean:>+9.3f}   ±2σ = ±{2*_se:.3f}   (SD={_sd:.3f})")
    # If baseline provided (J1), also report (arm.fav − J1.fav) and (arm.unf − J1.unf)
    if baseline_rows is not None:
        _flush(f"per-fighter differential vs baseline J1 (same seeds, "
               "so paired per-seed):")
        for who in ("fav", "unf"):
            for f in STAT_KEYS:
                arm_vals = [r[who][f] for r in rows]
                base_vals = [r[who][f] for r in baseline_rows]
                diffs = [a - b for a, b in zip(arm_vals, base_vals)]
                _mean = statistics.mean(diffs)
                _sd = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
                _se = _sd / math.sqrt(len(diffs)) if len(diffs) > 1 else 0.0
                _flush(f"  {who}.Δ({f:<26} vs J1) = {_mean:>+9.3f}   ±2σ = ±{2*_se:.3f}")


def part3_pinned_arms():
    _flush("")
    _flush("=" * 70)
    _flush("P3 — CLASSIFIER-PINNED FIGHT ARMS (J1/J2/J3, N=2000 each)")
    _flush("=" * 70)
    N = 2000

    # J1: all-75 symmetric
    fav = dict(overall_rating=75)
    unf = dict(overall_rating=75)
    rows_j1, fw, uw, dw = run_arm_j("J1", fav, unf, N,
        extra_cliff_check=None)
    analyze_arm("J1", rows_j1, fw, uw, dw, N)

    # J2: boxing 80 vs 70, all else 75
    fav = dict(overall_rating=75, boxing=80)
    unf = dict(overall_rating=75, boxing=70)
    rows_j2, fw, uw, dw = run_arm_j("J2", fav, unf, N,
        extra_cliff_check=None)
    analyze_arm("J2", rows_j2, fw, uw, dw, N, baseline_rows=rows_j1)

    # J3: kicks 80 vs 70. Confirm damage-cliff and accuracy-bonus don't fire.
    #   damage cliff #1 (fight_engine.py:2395): attacker.kicks>=75 AND defender.kicks<60
    #     → attacker=80 satisfies >=75, defender=70 fails <60 → COLD
    #   damage cliff #2 (:2397):               attacker.kicks>=65 AND defender.kicks<50
    #     → attacker=80 satisfies >=65, defender=70 fails <50 → COLD
    #   accuracy bonus (:2280):                attacker.kicks>=80 AND defender.kicks<60
    #     → attacker=80 satisfies >=80, defender=70 fails <60 → COLD
    fav = dict(overall_rating=75, kicks=80)
    unf = dict(overall_rating=75, kicks=70)
    rows_j3, fw, uw, dw = run_arm_j("J3", fav, unf, N,
        extra_cliff_check=[
            ("damage_cliff_1  (att.kicks>=75 AND def.kicks<60)",
             lambda: (80 >= 75) and (70 < 60), False),
            ("damage_cliff_2  (att.kicks>=65 AND def.kicks<50)",
             lambda: (80 >= 65) and (70 < 50), False),
            ("accuracy_bonus (att.kicks>=80 AND def.kicks<60)",
             lambda: (80 >= 80) and (70 < 60), False),
        ])
    analyze_arm("J3", rows_j3, fw, uw, dw, N, baseline_rows=rows_j1)


def main():
    _flush("=" * 70)
    _flush("ENGINE-STRIKE-SENS1 Step 7 — P1 + P2 + P3")
    _flush("=" * 70)
    _flush(f"fight_engine       from: {fe.__file__}")
    _flush(f"fight_integration  from: {fi.__file__}")
    _flush(f"game_bridge        from: {gb.__file__}")
    part1_classifier_audit()
    part2_hit_chance_sweep()
    part3_pinned_arms()
    _flush("")
    _flush("DONE.")


if __name__ == "__main__":
    main()
