"""ENGINE-STRIKE-SENS1 Step 1 Part B — five arms with CRN discipline.

READ-ONLY. Writes outputs/ only. No engine code reading.

CRN discipline:
  - fight_id = "arm_pair" (constant string literal, identical across arms).
  - fighter_ids = "arm_slot1_fighter", "arm_slot2_fighter" (constant).
  - Between arms, mutate _fighter_data[fid] and fighter object attrs
    to the arm's stat block. Fighter identity is stable per slot;
    stats attach to slot semantics.
  - seed sequence = random.seed(i) for i in 0..N-1, identical across arms.

Arms:
  A  — symmetric baseline (X_eq vs Y_eq, no buff)               N=2000
  B  — buffed X_str (+20 all 4 striking stats) vs Y_eq          N=2000
  B' — arm B stats mapping SWAPPED between slots (X_str in slot 2)
       (fight dict + fighter_ids identical to arm B; only the
       _fighter_data payload each slot holds is swapped)         N=2000
  C  — grappling-family +20 (X_gr_str vs Y_eq)                  N=2000
  D  — positive control 88-vs-55 across 10 stat families         N=500

Filed entry's baseline (from CLAUDE.md:2222-2239) explicitly reads
the values used in the prior harness Step-4 measurement. Those were:
  X_eq  (box=80, kick=70, clin=65, sd=70)  vs
  Y_eq  (box=70, kick=80, clin=65, sd=70)  → p_f1 = 0.475
  X_str (box=100, kick=90, clin=85, sd=90) vs Y_eq → p_f1 = 0.545
Filed Δ = +7pp at N=200. Arm B reproduces this pair at N=2000.

Full report structure per arm:
  1. p_f1 with 2σ (Wald: 2*sqrt(p(1-p)/N))
  2. Paired Δ vs arm A: McNemar-style. b = seeds where THIS arm's f1
     wins but arm A's f1 loses; c = reverse. Δ = (b-c)/N.
     Paired SE ≈ sqrt(b+c)/N. Paired 2σ CI = [Δ-2SE, Δ+2SE].
  3. Method pooled and split by winner.
  4. Round-of-finish, finishes only. Uses `total_rounds` field
     from NarratedFightResult (which encodes finish round for
     non-decisions and scheduled rounds for decisions — same field
     Step 0 flagged as ambiguous; using with caveat).
  5. Arm B vs B' paired at end.

CSV dump: outputs/engine_strike_sens1_partB_raw.csv
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


# ---- fixture builders (harness-consistent) --------
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
    for a, val in [("strength", overrides.get("strength", 70)),
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
                    ("composure", overrides.get("composure", 70))]:
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
    gs._fighter_data[f.fighter_id] = _fdata_from_fighter(f)

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

# ---- Stat blocks per arm ---------------------------------------------
STATS_X_EQ = dict(overall_rating=75,
                   boxing=80, kicks=70, clinch_striking=65, striking_defense=70)
STATS_Y_EQ = dict(overall_rating=75,
                   boxing=70, kicks=80, clinch_striking=65, striking_defense=70)
STATS_X_STR = dict(overall_rating=75,
                    boxing=100, kicks=90, clinch_striking=85, striking_defense=90)
# grappling-family +20 from baseline defaults: takedowns 65→85, td_def 70→90,
# top_control 65→85, subs 60→80, guard 65→85. Striking left at X_eq values.
STATS_X_GR_STR = dict(overall_rating=75,
                       boxing=80, kicks=70, clinch_striking=65, striking_defense=70,
                       takedowns=85, takedown_defense=90, top_control=85,
                       submissions=80, guard=85)
STATS_OVERWHELMING = dict(overall_rating=88,
                           strength=88, speed=88, cardio=88, chin=85,
                           boxing=88, kicks=85, striking_defense=88,
                           takedown_defense=88, fight_iq=88, composure=88)
STATS_OVERMATCHED = dict(overall_rating=55,
                          strength=55, speed=55, cardio=55, chin=52,
                          boxing=55, kicks=52, striking_defense=55,
                          takedown_defense=55, fight_iq=55, composure=55)

# ---- Constants (CRN discipline) ---------------------------------------
CONST_FIGHT_ID = "arm_pair"
CONST_FIGHTER1_ID = "arm_slot1_fighter"
CONST_FIGHTER2_ID = "arm_slot2_fighter"

def _make_fight_const():
    return {
        "fight_id": CONST_FIGHT_ID,
        "fighter1_id": CONST_FIGHTER1_ID, "fighter2_id": CONST_FIGHTER2_ID,
        "fighter1_name": "Slot1", "fighter2_name": "Slot2",
        "weight_class": "Lightweight", "card_slot": "prelim",
        "is_title_fight": False, "event_name": "Test Event",
        "gameplan": "BALANCED",
    }

def _install_arm(br, gs, slot1_stats, slot2_stats):
    """Mutate the two fixed fighter_ids to hold the arm's stat blocks."""
    fA = _make_bare_fighter(CONST_FIGHTER1_ID, "Slot1", **slot1_stats)
    fB = _make_bare_fighter(CONST_FIGHTER2_ID, "Slot2", **slot2_stats)
    # Register (or re-register, overwriting).
    gs._fighters[CONST_FIGHTER1_ID] = fA
    gs._fighters[CONST_FIGHTER2_ID] = fB
    gs._fighter_data[CONST_FIGHTER1_ID] = _fdata_from_fighter(fA)
    gs._fighter_data[CONST_FIGHTER2_ID] = _fdata_from_fighter(fB)
    return fA, fB

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

def _snapshot_stats(f):
    return {a: getattr(f, a) for a in
            ("boxing","kicks","clinch_striking","striking_defense",
             "takedowns","takedown_defense","top_control","submissions",
             "guard","clinch_control","strength","speed","cardio","chin",
             "recovery","heart","fight_iq","composure")}


def run_arm(br, gs, arm_name, slot1_stats, slot2_stats, N):
    """Run one arm; return list of outcome dicts + config header."""
    fA, fB = _install_arm(br, gs, slot1_stats, slot2_stats)
    fight = _make_fight_const()

    # Header
    _flush("")
    _flush("=" * 70)
    _flush(f"ARM {arm_name}   N={N}")
    _flush("=" * 70)
    _flush(f"CRN: fight_id={CONST_FIGHT_ID!r}   "
           f"fighter1_id={CONST_FIGHTER1_ID!r}   "
           f"fighter2_id={CONST_FIGHTER2_ID!r}")
    _flush(f"seed sequence: random.seed(i) for i in 0..{N-1}")
    _flush(f"slot 1 stats: {_snapshot_stats(fA)}")
    _flush(f"slot 2 stats: {_snapshot_stats(fB)}")

    # Config assertion
    _b_probe = br._assemble_prefight(
        fight, fA, fB, fA.name, fB.name, fA.fighter_id, fB.fighter_id,
        **_PA_KW,
    )
    _cfg = _b_probe["config"]
    _standup = getattr(_cfg, "standup_threshold", None)
    _dmg = getattr(_cfg, "damage_multiplier", None)
    _exch = getattr(_cfg, "exchanges_per_round", None)
    _flush(f"config: standup={_standup}, damage={_dmg}, exchanges={_exch}")
    assert _standup == 10, f"standup={_standup} != 10 → voids run"

    # Sim loop
    outcomes = []
    t0 = time.perf_counter()
    for i in range(N):
        random.seed(i)
        _bundle = br._assemble_prefight(
            fight, fA, fB, fA.name, fB.name, fA.fighter_id, fB.fighter_id,
            **_PA_KW,
        )
        eng = _run_path_a_ref(_bundle)
        outcomes.append({
            "arm":     arm_name,
            "seed":    i,
            "fight_id": CONST_FIGHT_ID,
            "winner":  getattr(eng, "winner_id", None),
            "method":  getattr(eng, "method", None),
            "total_rounds": getattr(eng, "total_rounds", None),
        })
    dt = time.perf_counter() - t0
    _flush(f"arm {arm_name} wall clock: {dt:.2f} sec  "
           f"({dt*1000/N:.2f} ms/sim)")
    return outcomes, fA, fB


def analyze_arm(name, outcomes, arm_a_outcomes=None):
    """Report per-arm stats. If arm_a_outcomes provided, also compute
    paired McNemar-style Δ vs arm A."""
    N = len(outcomes)
    _slot1 = CONST_FIGHTER1_ID
    _slot2 = CONST_FIGHTER2_ID
    f1_wins = sum(1 for o in outcomes if o["winner"] == _slot1)
    _flush("")
    _flush(f"--- arm {name} report ---")
    p = f1_wins / N
    se = math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0
    _flush(f"1. p_f1 = {p:.4f}   ±2σ = ±{2*se:.4f}   "
           f"(f1_wins={f1_wins}/{N})")

    if arm_a_outcomes is not None and name != "A":
        # Paired McNemar-style Δ vs arm A on winner=slot1 outcome.
        # For each seed i, is arm's f1-win a 1 or 0? Is arm A's? Compute
        # discordant pairs.
        b = c = 0  # b: arm has f1-win, A has f2-win. c: reverse.
        both_1 = both_0 = 0
        for i in range(N):
            arm_f1w = (outcomes[i]["winner"] == _slot1)
            A_f1w = (arm_a_outcomes[i]["winner"] == _slot1)
            if arm_f1w and A_f1w: both_1 += 1
            elif arm_f1w and not A_f1w: b += 1
            elif not arm_f1w and A_f1w: c += 1
            else: both_0 += 1
        D = (b - c) / N
        # Paired SE for difference of proportions from matched pairs:
        # SE ≈ sqrt(b + c) / N (McNemar-based; ignores small-sample corr)
        paired_se = math.sqrt(b + c) / N if (b + c) > 0 else 0.0
        # Show the arithmetic:
        _flush(f"2. Paired vs arm A (per-seed McNemar):")
        _flush(f"     concordant: both f1-win={both_1}, both f2-win={both_0}")
        _flush(f"     discordant: b (this arm f1, A f2) = {b}   "
               f"c (this arm f2, A f1) = {c}")
        _flush(f"     Δ = (b-c)/N = ({b}-{c})/{N} = {D:+.4f}")
        _flush(f"     paired SE ≈ sqrt(b+c)/N = sqrt({b+c})/{N} = {paired_se:.4f}")
        _flush(f"     paired 2σ CI: [{D-2*paired_se:+.4f}, {D+2*paired_se:+.4f}]")

    # 3. Method pooled + split by winner
    pooled = Counter(o["method"] for o in outcomes)
    _flush(f"3. Method distribution (pooled): {dict(pooled)}")
    by_slot1 = Counter(o["method"] for o in outcomes if o["winner"] == _slot1)
    by_slot2 = Counter(o["method"] for o in outcomes if o["winner"] == _slot2)
    _flush(f"   winner=slot1 methods (n={sum(by_slot1.values())}): {dict(by_slot1)}")
    _flush(f"   winner=slot2 methods (n={sum(by_slot2.values())}): {dict(by_slot2)}")

    # 4. Round of finish, finishes only. Method 'Unanimous Decision' /
    # 'Split Decision' / 'Majority Decision' / 'Draw' are non-finishes.
    _decision_set = {"Unanimous Decision", "Split Decision",
                     "Majority Decision", "Draw"}
    finishes = [o for o in outcomes if o["method"] not in _decision_set]
    finish_rounds = Counter(o["total_rounds"] for o in finishes)
    _flush(f"4. Round of finish (finishes only, n={len(finishes)}):")
    _flush(f"   Field used: total_rounds from NarratedFightResult.")
    _flush(f"   Semantics: for finishes, this appears to be the round the")
    _flush(f"   fight ended in (a round-3 finish is separable from a")
    _flush(f"   round-3 decision only by method). See A0 caveat.")
    _flush(f"   distribution: {dict(sorted(finish_rounds.items(), key=lambda x: (x[0] is None, x[0])))}")


def analyze_bprime_vs_b(b_outcomes, bp_outcomes):
    """Compare arm B (buffed in slot 1) vs arm B' (buffed in slot 2).
    In arm B, p_f1 = P(buffed wins). In arm B', p_f2 = P(buffed wins),
    so P(buffed wins in arm B') = 1 - p_f1(B')."""
    N = len(b_outcomes)
    _slot1 = CONST_FIGHTER1_ID
    b_f1  = sum(1 for o in b_outcomes if o["winner"] == _slot1)
    bp_f1 = sum(1 for o in bp_outcomes if o["winner"] == _slot1)
    p_buffed_B  = b_f1 / N          # buffed = slot1 in arm B
    p_buffed_Bp = (N - bp_f1) / N   # buffed = slot2 in arm B'
    se_B  = math.sqrt(p_buffed_B*(1-p_buffed_B)/N) if 0<p_buffed_B<1 else 0.0
    se_Bp = math.sqrt(p_buffed_Bp*(1-p_buffed_Bp)/N) if 0<p_buffed_Bp<1 else 0.0
    _flush("")
    _flush("=" * 70)
    _flush("ARM B vs ARM B' — slot-symmetry check (P(buffed wins) either slot)")
    _flush("=" * 70)
    _flush(f"  arm B  (buffed in slot 1): P(buffed wins) = p_f1     = "
           f"{p_buffed_B:.4f}  ±2σ = ±{2*se_B:.4f}")
    _flush(f"  arm B' (buffed in slot 2): P(buffed wins) = 1-p_f1   = "
           f"{p_buffed_Bp:.4f}  ±2σ = ±{2*se_Bp:.4f}")
    _diff = p_buffed_B - p_buffed_Bp
    _diff_se = math.sqrt(se_B**2 + se_Bp**2)  # independent-samples SE
    _flush(f"  Δ (B − B') = {_diff:+.4f}   ±2σ = ±{2*_diff_se:.4f}   "
           f"(independent-samples approx)")
    # Also compute per-seed paired: for each seed, was buffed the winner in each arm?
    b_wins = 0
    bp_wins = 0
    both = 0
    neither = 0
    b_only = 0
    bp_only = 0
    for i in range(N):
        b_buffed_won  = (b_outcomes[i]["winner"] == _slot1)     # slot1 buffed in B
        bp_buffed_won = (bp_outcomes[i]["winner"] == CONST_FIGHTER2_ID)  # slot2 buffed in B'
        if b_buffed_won and bp_buffed_won: both += 1
        elif b_buffed_won and not bp_buffed_won: b_only += 1
        elif not b_buffed_won and bp_buffed_won: bp_only += 1
        else: neither += 1
    _flush(f"  per-seed paired: both buffed-wins={both}  neither={neither}   "
           f"b_only={b_only}  bp_only={bp_only}")
    _flush(f"  If Δ (B − B') falls outside its 2σ band, that's live slot bias.")


def main():
    br, gs = _make_test_bridge()

    N_MAIN = 2000
    N_D = 500

    _flush("=" * 70)
    _flush("ENGINE-STRIKE-SENS1 Step 1 Part B — five arms")
    _flush("=" * 70)
    _flush(f"fight_engine       from: {fe.__file__}")
    _flush(f"fight_integration  from: {fi.__file__}")
    _flush(f"game_bridge        from: {gb.__file__}")

    all_outcomes = []

    # Arm A
    outc_A, _fA_A, _fB_A = run_arm(br, gs, "A", STATS_X_EQ, STATS_Y_EQ, N_MAIN)
    all_outcomes.extend(outc_A)
    analyze_arm("A", outc_A)

    # Arm B (buffed in slot 1)
    outc_B, _fA_B, _fB_B = run_arm(br, gs, "B", STATS_X_STR, STATS_Y_EQ, N_MAIN)
    all_outcomes.extend(outc_B)
    analyze_arm("B", outc_B, arm_a_outcomes=outc_A)

    # Arm B' (buffed in slot 2 — swap stat mapping)
    outc_Bp, _fA_Bp, _fB_Bp = run_arm(br, gs, "B'", STATS_Y_EQ, STATS_X_STR, N_MAIN)
    all_outcomes.extend(outc_Bp)
    analyze_arm("B'", outc_Bp, arm_a_outcomes=outc_A)

    # Arm C (grappling +20 in slot 1)
    outc_C, _fA_C, _fB_C = run_arm(br, gs, "C", STATS_X_GR_STR, STATS_Y_EQ, N_MAIN)
    all_outcomes.extend(outc_C)
    analyze_arm("C", outc_C, arm_a_outcomes=outc_A)

    # Arm D (positive control 88 vs 55)
    outc_D, _fA_D, _fB_D = run_arm(br, gs, "D", STATS_OVERWHELMING, STATS_OVERMATCHED, N_D)
    all_outcomes.extend(outc_D)
    analyze_arm("D", outc_D)

    # B vs B' slot-symmetry
    analyze_bprime_vs_b(outc_B, outc_Bp)

    # CSV dump
    csv_path = os.path.join(_HERE, "engine_strike_sens1_partB_raw.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["arm", "seed", "fight_id", "winner",
                    "method", "total_rounds"])
        for o in all_outcomes:
            w.writerow([o["arm"], o["seed"], o["fight_id"],
                        o["winner"], o["method"], o["total_rounds"]])
    _flush("")
    _flush(f"CSV dump: {csv_path}  ({len(all_outcomes)} rows)")

    _flush("")
    _flush("DONE — numbers only, no interpretation.")


if __name__ == "__main__":
    main()
