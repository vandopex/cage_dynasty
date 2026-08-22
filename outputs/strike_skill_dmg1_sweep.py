"""STRIKE-SKILL-DMG1 phase 1a — sweep harness (no commit; measurement only).

Sweeps STRIKE_SKILL_DAMAGE_K ∈ {0.5, 1.0, 1.5, 2.0} × arms
{E, G1, H3, J1, F}, N=2000 each. K varied by module attribute
rebind (fe.STRIKE_SKILL_DAMAGE_K = K) — no engine edit between runs.

DISCRIMINATORS (BINDING):
  - J1 (all-75 symmetric) — every attr = 75 → _skill-75=0 → factor=1.0
    exactly at any K. Must be BIT-IDENTICAL across all K.
  - F (grappling family 88v55) — striking attrs all 75 → factor=1.0
    exactly at any K. Must be BIT-IDENTICAL across all K.
  If either moves at any K, the wiring leaked and NO sweep number is
  reportable.

H1 CONSERVATION: same fixture as J1 (all-75 symmetric); reported
under both labels for clarity, but the underlying run is identical.
J1's bit-identity check across K IS the H1 conservation gate.

KICK-ARM CAVEAT: at H3 (kicks 74v61), the dial stacks on top of the
existing :2394-2398 kick cliffs. Since kicks 74 fails the >=75 cliff
threshold, the cliff itself does not fire in H3 at any K; the dial
is the only kick-specific damage channel active for H3. Flagged for
readers of the H3 row.

CSVs per K embed the active K in header. Full grid rendered inline
at end of run.
"""
import os, sys, time, random, math, csv, subprocess
from collections import Counter
import statistics

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


DECISION_METHODS = {"Unanimous Decision", "Split Decision",
                    "Majority Decision", "Draw"}


def run_arm(arm_name, slot1_stats, slot2_stats, N):
    br, gs = _make_test_bridge()
    _s1 = f"{arm_name}_slot1"
    _s2 = f"{arm_name}_slot2"
    fA = _make_bare_fighter(_s1, _s1, **slot1_stats)
    fB = _make_bare_fighter(_s2, _s2, **slot2_stats)
    _register_fighter(gs, fA); _register_fighter(gs, fB)
    fight = _make_fight_const(_s1, _s2)

    _b = br._assemble_prefight(fight, fA, fB, fA.name, fB.name,
                                fA.fighter_id, fB.fighter_id, **_PA_KW)
    assert getattr(_b["config"], "standup_threshold", None) == 10

    rows = []
    for i in range(N):
        random.seed(i)
        bundle = br._assemble_prefight(
            fight, fA, fB, fA.name, fB.name,
            fA.fighter_id, fB.fighter_id, **_PA_KW)
        eng = _run_path_a_ref(bundle)
        rows.append({
            "arm": arm_name, "seed": i,
            "winner": getattr(eng, "winner_id", None),
            "method": getattr(eng, "method", None),
            "total_rounds": getattr(eng, "total_rounds", None),
        })
    return rows, _s1, _s2


def summarize_arm(arm_name, rows, slot1_id, slot2_id):
    N = len(rows)
    fav_wins = sum(1 for r in rows if r["winner"] == slot1_id)
    unf_wins = sum(1 for r in rows if r["winner"] == slot2_id)
    draws = sum(1 for r in rows if r["winner"] not in (slot1_id, slot2_id))
    p = fav_wins / N
    se = math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0
    kotko = sum(1 for r in rows
                if r["method"] and (r["method"].startswith("KO")
                                    or r["method"].startswith("TKO")))
    finishes = sum(1 for r in rows if r["method"] not in DECISION_METHODS)
    kotko_share = kotko / N
    mean_rounds = statistics.mean([r["total_rounds"] for r in rows
                                    if r["total_rounds"] is not None])
    return {
        "arm": arm_name, "N": N, "fav_wins": fav_wins, "unf_wins": unf_wins,
        "draws": draws, "p_fav": p, "se2": 2*se,
        "ko_tko": kotko, "ko_tko_share": kotko_share,
        "finishes": finishes, "mean_rounds": mean_rounds,
    }


def main():
    _flush("=" * 70)
    _flush("STRIKE-SKILL-DMG1 phase 1a — SWEEP")
    _flush("=" * 70)
    try:
        _head = subprocess.check_output(
            ["git", "-C", _REPO, "rev-parse", "HEAD"], text=True).strip()
    except Exception as _e:
        _head = f"<git failed: {_e}>"
    _flush(f"repo HEAD: {_head}")
    _flush(f"fight_engine       from: {fe.__file__}")
    _flush(f"fight_integration  from: {fi.__file__}")
    _flush(f"engine module STRIKE_SKILL_DAMAGE_K (before sweep): "
           f"{fe.STRIKE_SKILL_DAMAGE_K}")
    _flush("")

    K_VALUES = [0.5, 1.0, 1.5, 2.0]
    N = 2000

    # Fixture generator per arm
    def _stats_for(arm):
        if arm == "E":
            return _stats_with_family(STRIKING_FAMILY)
        if arm == "F":
            return _stats_with_family(GRAPPLING_FAMILY)
        if arm == "G1":
            return _stats_with_family(("boxing",))
        if arm == "H3":
            fav = dict(BASE_75); fav["kicks"] = 74; fav["overall_rating"] = 75
            unf = dict(BASE_75); unf["kicks"] = 61; unf["overall_rating"] = 75
            return fav, unf
        if arm == "J1":
            fav = dict(BASE_75); fav["overall_rating"] = 75
            unf = dict(BASE_75); unf["overall_rating"] = 75
            return fav, unf
        raise ValueError(arm)

    ARMS = ("E", "G1", "H3", "J1", "F")
    all_summaries = {}   # (K, arm) -> summary
    all_rows      = {}   # (K, arm) -> list of row dicts (for discriminator MD5)

    total_start = time.perf_counter()
    for K in K_VALUES:
        # Rebind module attribute — sweep by attribute, no engine edit
        fe.STRIKE_SKILL_DAMAGE_K = K
        _flush("=" * 60)
        _flush(f"K = {K}   (fe.STRIKE_SKILL_DAMAGE_K rebind confirmed: "
               f"{fe.STRIKE_SKILL_DAMAGE_K})")
        _flush("=" * 60)
        k_start = time.perf_counter()
        for arm in ARMS:
            fav_stats, unf_stats = _stats_for(arm)
            arm_start = time.perf_counter()
            rows, s1, s2 = run_arm(arm, fav_stats, unf_stats, N)
            arm_dt = time.perf_counter() - arm_start
            summ = summarize_arm(arm, rows, s1, s2)
            all_summaries[(K, arm)] = summ
            all_rows[(K, arm)] = rows
            _flush(f"  arm {arm}: N={N}  wall={arm_dt:.1f}s  "
                   f"p_fav={summ['p_fav']:.4f} ±{summ['se2']:.4f}  "
                   f"KO+TKO={summ['ko_tko']} ({summ['ko_tko_share']:.3f})  "
                   f"finishes={summ['finishes']}  draws={summ['draws']}  "
                   f"mean_rounds={summ['mean_rounds']:.3f}")
        k_dt = time.perf_counter() - k_start
        _flush(f"  K={K} block wall: {k_dt:.1f}s")

        # Dump per-K CSV
        csv_path = os.path.join(
            _HERE, f"strike_skill_dmg1_sweep_K{K}_raw.csv")
        with open(csv_path, "w", newline="") as fh:
            fh.write(f"# STRIKE-SKILL-DMG1 sweep\n")
            fh.write(f"# K: {K}\n")
            fh.write(f"# repo_HEAD: {_head}\n")
            fh.write(f"# fe.STRIKE_SKILL_DAMAGE_K observed: {fe.STRIKE_SKILL_DAMAGE_K}\n")
            fh.write(f"# arms: {ARMS}  N: {N}\n")
            w = csv.DictWriter(fh, fieldnames=["K","arm","seed","winner",
                                                "method","total_rounds"])
            w.writeheader()
            for arm in ARMS:
                for r in all_rows[(K, arm)]:
                    w.writerow({"K": K, **r})
        _flush(f"  CSV: {csv_path}")

    total_dt = time.perf_counter() - total_start
    _flush("")
    _flush(f"TOTAL sweep wall clock: {total_dt:.1f}s")

    # ============ DISCRIMINATOR CHECK ============
    # J1 and F must be bit-identical across all K values.
    _flush("")
    _flush("=" * 70)
    _flush("DISCRIMINATOR CHECK — J1 and F must be bit-identical across K")
    _flush("=" * 70)
    import hashlib
    def _rows_hash(rows):
        m = hashlib.md5()
        for r in rows:
            m.update(f"{r['seed']}|{r['winner']}|{r['method']}|{r['total_rounds']}\n"
                     .encode("utf-8"))
        return m.hexdigest()
    for disc_arm in ("J1", "F"):
        hashes = {K: _rows_hash(all_rows[(K, disc_arm)]) for K in K_VALUES}
        _flush(f"  {disc_arm}:")
        for K, h in hashes.items():
            _flush(f"    K={K}: rows_md5={h}")
        _all_same = len(set(hashes.values())) == 1
        _flush(f"    → all K identical? {_all_same}")

    # ============ H1 CONSERVATION ============
    # H1 fixture is J1 fixture (all-75 symmetric); reported explicitly.
    _flush("")
    _flush("=" * 70)
    _flush("H1 CONSERVATION — H1 fixture is J1 fixture (all-75 symmetric).")
    _flush("=" * 70)
    _flush("  J1 discriminator hashes above ARE the H1 conservation check.")

    # ============ SUMMARY GRID (paste-worthy) ============
    _flush("")
    _flush("=" * 70)
    _flush("SUMMARY GRID (all summaries, per (K, arm))")
    _flush("=" * 70)
    _flush(f"  {'K':>4}  {'arm':<3}  {'N':>5}  {'p_fav':>7}  {'±2σ':>7}  "
           f"{'KO+TKO':>7}  {'kotko_%':>8}  {'finish':>7}  "
           f"{'draws':>5}  {'mn_rnds':>7}")
    for K in K_VALUES:
        for arm in ARMS:
            s = all_summaries[(K, arm)]
            _flush(f"  {K:>4}  {arm:<3}  {s['N']:>5}  {s['p_fav']:>7.4f}  "
                   f"{s['se2']:>7.4f}  {s['ko_tko']:>7}  "
                   f"{s['ko_tko_share']:>8.4f}  {s['finishes']:>7}  "
                   f"{s['draws']:>5}  {s['mean_rounds']:>7.3f}")

    # Reset engine module attr to zero for cleanliness (not committed)
    fe.STRIKE_SKILL_DAMAGE_K = 0.0
    _flush("")
    _flush(f"engine module STRIKE_SKILL_DAMAGE_K (after sweep, reset): "
           f"{fe.STRIKE_SKILL_DAMAGE_K}")
    _flush("DONE.")


if __name__ == "__main__":
    main()
