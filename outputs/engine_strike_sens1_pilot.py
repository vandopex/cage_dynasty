"""ENGINE-STRIKE-SENS1 Step 0 — Pilot (arm A only, symmetric baseline).

READ-ONLY intent. Reads harness (instrument), writes outputs/ only,
does NOT edit game_bridge.py or read engine code this turn.

Design:
  - Reuse mc_odds_harness's fixture builders (_make_bare_fighter,
    _register_fighter, _make_fight) and its Path A byte-copy call
    (build inline here to avoid touching the harness).
  - Symmetric OVR=75 clone pair, no buff.
  - N=20 sims, deterministic seeds 0..19 via random.seed(i).
  - Assert live-play config triple (standup==10, damage==0.48,
    exch==55). If we're on _TRIPLE_FI_FALLBACK (standup==6), STOP.
  - Report per-sim outcome (winner, method, round), plus timing.
"""

import os
import sys
import time
import random

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_WEB  = os.path.join(_REPO, "cage_dynasty_web")
_NARR = os.path.join(_REPO, "narrative")
_SYS  = os.path.join(_REPO, "systems")

sys.path.insert(0, _NARR)
sys.path.insert(0, _WEB)
sys.path.append(_SYS)

# Prime commentary from narrative/ (see harness comment — repo root
# would otherwise win via subsequent transitive imports).
import commentary as _priming_commentary  # noqa: F401

import game_bridge as gb
fi = sys.modules["fight_integration"]
fe = sys.modules["fight_engine"]


def _flush(msg=""):
    print(msg, flush=True)


# ---------- Fixture builders (copied from mc_odds_harness.py) --------
def _make_bare_fighter(fid, name, style_name="Balanced", **overrides):
    class _F:
        pass
    f = _F()
    f.fighter_id = fid
    f.name = name
    f.overall_rating = overrides.get("overall_rating", 75)
    f.fighting_style = style_name
    f.wins = overrides.get("wins", 5)
    f.losses = overrides.get("losses", 2)
    f.draws = 0
    f.ko_wins = 2; f.sub_wins = 1
    f.ko_losses = 0; f.sub_losses = 0
    f.fatigue = overrides.get("fatigue", 0)
    f.weight_class = "Lightweight"
    f.natural_weight_class = "Lightweight"
    f.age = 28
    f.popularity = 40
    f.is_champion = False
    f.nickname = None
    f.camp_id = None
    f.contract_id = None
    for k, v in overrides.items():
        setattr(f, k, v)
    for a, val in [
        ("strength",           overrides.get("strength", 70)),
        ("speed",              overrides.get("speed", 70)),
        ("cardio",             overrides.get("cardio", 70)),
        ("chin",               overrides.get("chin", 70)),
        ("recovery",           overrides.get("recovery", 70)),
        ("boxing",             overrides.get("boxing", 70)),
        ("kicks",              overrides.get("kicks", 70)),
        ("clinch_striking",    overrides.get("clinch_striking", 65)),
        ("striking_defense",   overrides.get("striking_defense", 70)),
        ("takedowns",          overrides.get("takedowns", 65)),
        ("takedown_defense",   overrides.get("takedown_defense", 70)),
        ("top_control",        overrides.get("top_control", 65)),
        ("submissions",        overrides.get("submissions", 60)),
        ("guard",              overrides.get("guard", 65)),
        ("clinch_control",     overrides.get("clinch_control", 65)),
        ("heart",              overrides.get("heart", 72)),
        ("fight_iq",           overrides.get("fight_iq", 70)),
        ("composure",          overrides.get("composure", 70)),
    ]:
        setattr(f, a, val)
    return f


def _make_test_bridge():
    br = gb.GameBridge()
    class _GS:
        def __init__(self):
            self._fighter_data = {}
            self.player_camp_id = None
            self.week_number = 1
            self.free_agents = set()
            self.active_contracts = {}
            self._contract_data = {}
            self._fighters = {}
        def get_fighter(self, fid):
            return self._fighters.get(fid)
        def get_player_fighters(self):
            return []
        def get_camp(self, cid):
            return None
    gs = _GS()
    br._game_state = gs
    return br, gs


def _register_fighter(gs, f):
    gs._fighters[f.fighter_id] = f
    gs._fighter_data[f.fighter_id] = {
        "style":                f.fighting_style,
        "strength":             f.strength,
        "speed":                f.speed,
        "cardio":               f.cardio,
        "chin":                 f.chin,
        "recovery":             f.recovery,
        "boxing":               f.boxing,
        "kicks":                f.kicks,
        "clinch_striking":      f.clinch_striking,
        "striking_defense":     f.striking_defense,
        "takedowns":            f.takedowns,
        "takedown_defense":     f.takedown_defense,
        "top_control":          f.top_control,
        "submissions":          f.submissions,
        "guard":                f.guard,
        "clinch_control":       f.clinch_control,
        "heart":                f.heart,
        "fight_iq":             f.fight_iq,
        "composure":            f.composure,
        "fatigue":              f.fatigue,
        "natural_weight_class": f.natural_weight_class,
    }


def _make_fight(f1, f2, slot="prelim", is_title=False, gameplan="BALANCED"):
    return {
        "fight_id":       f"fid_{f1.fighter_id}_{f2.fighter_id}",
        "fighter1_id":    f1.fighter_id,
        "fighter2_id":    f2.fighter_id,
        "fighter1_name":  f1.name,
        "fighter2_name":  f2.name,
        "weight_class":   "Lightweight",
        "card_slot":      slot,
        "is_title_fight": is_title,
        "event_name":     "Test Event",
        "gameplan":       gameplan,
    }


# ---------- Path A byte-copy (from game_bridge.py:17806-17820) --------
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


# ---------- Path A kwarg pack for _assemble_prefight -----------------
_PA_KW = dict(
    fatigue_source="attr",
    apply_cut_penalty=True,
    apply_player_buffs=True,
    apply_sponsor_boost=True,
    compute_style_mod=True,
    verbose=False,
)


# ---------- Config header ----------------------------------------------
def _print_config_header(br, gs):
    _flush("=" * 70)
    _flush("ENGINE-STRIKE-SENS1 Step 0 — Pilot (arm A: symmetric baseline)")
    _flush("=" * 70)
    _flush(f"fight_engine       from: {fe.__file__}")
    _flush(f"fight_integration  from: {fi.__file__}")
    _flush(f"game_bridge        from: {gb.__file__}")
    _flush(f"FIGHT_ENGINE_AVAILABLE = {gb.FIGHT_ENGINE_AVAILABLE}")

    # Build a throwaway bundle to inspect the resolved config identity.
    _fx = _make_bare_fighter("cfg_A", "Cfg-A", overall_rating=75)
    _fy = _make_bare_fighter("cfg_B", "Cfg-B", overall_rating=75)
    _register_fighter(gs, _fx); _register_fighter(gs, _fy)
    _fight = _make_fight(_fx, _fy)
    _bundle = br._assemble_prefight(
        _fight, _fx, _fy, _fx.name, _fy.name,
        _fx.fighter_id, _fy.fighter_id, **_PA_KW,
    )
    _cfg = _bundle["config"]
    _standup = getattr(_cfg, "standup_threshold", None)
    _dmg     = getattr(_cfg, "damage_multiplier", None)
    _exch    = getattr(_cfg, "exchanges_per_round", None)
    _sub_f   = getattr(_cfg, "submission_progress_to_finish", None)
    _sub_e   = getattr(_cfg, "submission_escape_threshold", None)
    _flush(f"Resolved config identity (from _assemble_prefight bundle):")
    _flush(f"  type            = {type(_cfg).__name__}")
    _flush(f"  standup         = {_standup}")
    _flush(f"  damage          = {_dmg}")
    _flush(f"  exchanges       = {_exch}")
    _flush(f"  sub_progress    = {_sub_f}")
    _flush(f"  sub_escape      = {_sub_e}")
    assert _standup == 10, (
        f"standup_threshold={_standup} — expected 10 (_TRIPLE_LIVE_PLAY). "
        "Value 6 would mean the bundle carries _TRIPLE_FI_FALLBACK; STOP."
    )
    assert _dmg == 0.48, f"damage={_dmg} != 0.48"
    assert _exch == 55, f"exchanges={_exch} != 55"
    _flush(f"  ASSERT standup==10, dmg==0.48, exch==55 — PASS "
           "(config is _TRIPLE_LIVE_PLAY)")
    # Report fight_id sequence — for arm A this is the SAME fight_id
    # per sim (we vary the seed, not the fight identity). Print the
    # single fight_id being sampled 20 times.
    _pilot_fight_id = f"fid_pilot_arm_A"
    _flush(f"fight_id in use (arm A, sampled 20 times): {_pilot_fight_id!r}")
    _flush(f"seed sequence: random.seed(i) for i in 0..19")


def main():
    br, gs = _make_test_bridge()
    _print_config_header(br, gs)

    # Symmetric baseline pair — byte-identical defaults, OVR=75.
    fA = _make_bare_fighter("pilotA_A", "Pilot-A", overall_rating=75)
    fB = _make_bare_fighter("pilotA_B", "Pilot-B", overall_rating=75)
    _register_fighter(gs, fA); _register_fighter(gs, fB)
    fight = _make_fight(fA, fB)
    fight["fight_id"] = "fid_pilot_arm_A"  # explicit for header consistency

    N = 20
    outcomes = []
    t0 = time.perf_counter()
    for i in range(N):
        random.seed(i)  # deterministic per sim
        _bundle = br._assemble_prefight(
            fight, fA, fB, fA.name, fB.name, fA.fighter_id, fB.fighter_id,
            **_PA_KW,
        )
        eng = _run_path_a_ref(_bundle)
        _wid = getattr(eng, "winner_id", None)
        _method = getattr(eng, "method", None)
        _round = getattr(eng, "final_round", None)
        _total = getattr(eng, "total_rounds", None)
        outcomes.append({
            "sim":     i,
            "seed":    i,
            "winner":  _wid,
            "method":  _method,
            "round":   _round,
            "rounds":  _total,
        })
    dt = time.perf_counter() - t0

    _flush("")
    _flush(f"Wall clock (N={N}): {dt*1000:.1f} ms")
    _flush(f"Per-sim mean:       {dt*1000/N:.2f} ms")
    _flush(f"Projected 2000 sims (4 arms × N=500): "
           f"{dt*1000/N*2000/1000:.1f} sec")
    _flush("")
    _flush(f"Raw outcomes (N={N}):")
    _flush(f"  {'sim':>3}  {'seed':>4}  {'winner':<12}  {'method':<24}  {'round':>5}  {'rounds':>6}")
    for row in outcomes:
        _flush(f"  {row['sim']:>3}  {row['seed']:>4}  "
               f"{str(row['winner']):<12}  {str(row['method']):<24}  "
               f"{str(row['round']):>5}  {str(row['rounds']):>6}")

    # Method distribution summary.
    from collections import Counter
    _methods = Counter(r["method"] for r in outcomes)
    _wins    = Counter(r["winner"] for r in outcomes)
    _flush("")
    _flush(f"Method distribution: {dict(_methods)}")
    _flush(f"Winner distribution: {dict(_wins)}")
    _flush(f"Distinct methods observed: {len(_methods)}")


if __name__ == "__main__":
    main()
