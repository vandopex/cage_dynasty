"""A2 + A3 — seed control tests for ENGINE-STRIKE-SENS1 Step 1 gate.

A2 (critical): fixed fight_id, random.seed(0) for all 20 reps.
  Expect: 20 identical outcomes → global seed controls the stream.
  Any variation → uncontrolled nondeterministic source. STOP.

A3 (diagnostic): seeds 0..19 with a DIFFERENT constant fight_id
  vs pilot Part 3's outcomes.
  Identical to A1 → fight_id inert on this DIRECT path.
    (Note: this direct path bypasses _compute_mc_odds_for_fight's
     crc32 seeding; testing here whether anything else in
     _assemble_prefight or the sim consumes fight_id → RNG.)

READ-ONLY. Writes only to outputs/.
"""
import os, sys, time, random

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


# ----- copied verbatim from mc_odds_harness / pilot -----
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

def _make_fight(f1, f2, slot="prelim", is_title=False, gameplan="BALANCED"):
    return {
        "fight_id": f"fid_{f1.fighter_id}_{f2.fighter_id}",
        "fighter1_id": f1.fighter_id, "fighter2_id": f2.fighter_id,
        "fighter1_name": f1.name, "fighter2_name": f2.name,
        "weight_class": "Lightweight", "card_slot": slot,
        "is_title_fight": is_title, "event_name": "Test Event",
        "gameplan": gameplan,
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


def _one_shot(br, fA, fB, fight_id_str, global_seed):
    fight = _make_fight(fA, fB)
    fight["fight_id"] = fight_id_str
    random.seed(global_seed)
    _bundle = br._assemble_prefight(
        fight, fA, fB, fA.name, fB.name, fA.fighter_id, fB.fighter_id,
        **_PA_KW,
    )
    eng = _run_path_a_ref(_bundle)
    return (getattr(eng, "winner_id", None),
            getattr(eng, "method", None),
            getattr(eng, "total_rounds", None))


def main():
    br, gs = _make_test_bridge()
    # Same symmetric baseline pair as pilot Step 0.
    fA = _make_bare_fighter("pilotA_A", "Pilot-A", overall_rating=75)
    fB = _make_bare_fighter("pilotA_B", "Pilot-B", overall_rating=75)
    _register_fighter(gs, fA); _register_fighter(gs, fB)

    # ---- A2 — fixed fight_id, seed(0) 20 times ----
    _flush("=" * 66)
    _flush("A2 — fixed fight_id + random.seed(0) x20 (global-seed determinism)")
    _flush("=" * 66)
    _fid_A2 = "fid_pilot_arm_A"
    _flush(f"fight_id: {_fid_A2!r}   fighter_ids: {fA.fighter_id!r}, {fB.fighter_id!r}")
    _flush(f"seed sequence: random.seed(0) x 20")
    A2 = []
    for i in range(20):
        outcome = _one_shot(br, fA, fB, _fid_A2, 0)
        A2.append(outcome)
    for i, o in enumerate(A2):
        _flush(f"  rep {i:>2}: winner={o[0]:<10} method={o[1]:<24} rounds={o[2]}")
    _n_unique_A2 = len(set(A2))
    _flush(f"  distinct outcomes: {_n_unique_A2}  "
           f"(1 → global seed controls the stream; >1 → nondeterministic source)")

    # ---- A3 — seeds 0..19 with DIFFERENT constant fight_id ----
    _flush("")
    _flush("=" * 66)
    _flush("A3 — seeds 0..19, DIFFERENT constant fight_id (fight_id inertness)")
    _flush("=" * 66)
    _fid_A3 = "fid_A3_DIFFERENT_STRING_TO_TEST"
    _flush(f"fight_id: {_fid_A3!r}")
    _flush(f"seed sequence: random.seed(i) for i in 0..19")
    A3 = []
    for i in range(20):
        outcome = _one_shot(br, fA, fB, _fid_A3, i)
        A3.append(outcome)
    for i, o in enumerate(A3):
        _flush(f"  seed {i:>2}: winner={o[0]:<10} method={o[1]:<24} rounds={o[2]}")

    # Read pilot A1 outcomes from disk to compare (no re-run, no dep on state).
    # Direct compute: rebuild them here with the pilot's fight_id.
    _fid_A1 = "fid_pilot_arm_A"
    _flush("")
    _flush("A3 diagnostic: comparing to A1 (same seeds, fight_id='fid_pilot_arm_A')")
    A1 = []
    for i in range(20):
        outcome = _one_shot(br, fA, fB, _fid_A1, i)
        A1.append(outcome)
    _identical = (A1 == A3)
    if _identical:
        _flush(f"  A3 outcomes IDENTICAL to A1 (all 20 triples byte-match).")
        _flush(f"  → fight_id is INERT on this DIRECT path "
               "(bypasses _compute_mc_odds_for_fight's crc32 seeding).")
    else:
        _n_diff = sum(1 for i in range(20) if A1[i] != A3[i])
        _flush(f"  A3 outcomes DIFFER from A1 in {_n_diff}/20 reps.")
        _flush(f"  → something on this path DOES consume fight_id "
               "(or a fight_id-derived value) into RNG.")
        _flush("  Diff table (seed, A1, A3):")
        for i in range(20):
            if A1[i] != A3[i]:
                _flush(f"    seed {i:>2}: A1={A1[i]}  A3={A3[i]}")


if __name__ == "__main__":
    main()
