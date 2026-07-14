"""ORACLE-BRIDGE1 fixture generator.

Runs a determinized game and captures a wide result vector for every
fight that resolves through _simulate_card_fights (Path A / AI card
fights) and _run_real_engine (player fights).

Vector includes:
  1. INPUT capture — every value passed to simulate_narrated_fight
     (FighterAttributes, config, gameplan, starting stamina, intros).
     Catches perturbations to the six game_bridge decisions at the
     input boundary, before output divergence propagates.
  2. OUTPUT capture — the engine's NarratedFightResult (winner, method,
     round, per-round stats, judge scores, commentary hash).
  3. STATE DELTAS — fighter record changes (wins/losses/KOs/subs),
     rank changes, injuries added, chin erosion, career stats.

Writes fixture.json alongside this script.
"""
import _common  # noqa: F401 — sys.path + uuid patch + seed setup
import hashlib
import io
import json
import os
import sys
import contextlib
from copy import deepcopy

MAIN_WEEKS = 12  # covers 7 events per multi-seed pattern (wks 1,2,5,7,8,10,11)

# Wrapped call captures for each fight.
_captured_fights = []

# Simple utilities
def _sha16(s):
    if s is None:
        s = ""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def _fa_dict(fa):
    """FighterAttributes → sorted-key dict (deterministic serialization)."""
    if fa is None:
        return None
    d = {}
    for k in sorted(vars(fa).keys()):
        v = getattr(fa, k)
        if isinstance(v, (int, float, str, bool, type(None))):
            d[k] = v
        elif hasattr(v, "value"):  # enum
            d[k] = v.value
        else:
            d[k] = repr(v)  # fallback — attributes shouldn't hit this
    return d

def _cfg_dict(cfg):
    if cfg is None:
        return None
    d = {}
    for k in sorted(vars(cfg).keys()):
        v = getattr(cfg, k)
        if isinstance(v, (int, float, str, bool, type(None))):
            d[k] = v
        else:
            d[k] = repr(v)
    return d

def _gp_dict(gp):
    if gp is None:
        return None
    d = {}
    for k in sorted(vars(gp).keys()):
        v = getattr(gp, k)
        if isinstance(v, (int, float, str, bool, type(None))):
            d[k] = v
        else:
            d[k] = repr(v)
    return d

def _snapshot_fighter(bridge, fid):
    """Pre/post-fight snapshot of a fighter's state."""
    if not bridge._game_state:
        return None
    f = bridge._game_state.get_fighter(fid)
    if not f:
        return None
    fd = bridge._game_state._fighter_data.get(fid, {})
    injury_active = False
    if getattr(bridge, "_injury_system", None):
        try:
            injury_active = not bridge._injury_system.is_cleared_to_fight(fid)
        except Exception:
            pass
    return {
        "wins": getattr(f, "wins", 0),
        "losses": getattr(f, "losses", 0),
        "draws": getattr(f, "draws", 0),
        "ko_wins": getattr(f, "ko_wins", 0),
        "sub_wins": getattr(f, "sub_wins", 0),
        "ko_losses": getattr(f, "ko_losses", 0),
        "sub_losses": getattr(f, "sub_losses", 0),
        "overall_rating": getattr(f, "overall_rating", 0),
        "fighting_style": getattr(f, "fighting_style", None),
        "weight_class": getattr(f, "weight_class", None),
        "is_champion": getattr(f, "is_champion", False),
        "fatigue": int(getattr(f, "fatigue", 0) or 0),
        "chin": int(fd.get("chin", 0) or 0),
        "cardio": int(fd.get("cardio", 0) or 0),
        "career_strikes": int(fd.get("career_strikes", 0) or 0),
        "career_takedowns": int(fd.get("career_takedowns", 0) or 0),
        "career_sub_attempts": int(fd.get("career_sub_attempts", 0) or 0),
        "career_control_time": int(fd.get("career_control_time", 0) or 0),
        "career_fotn_awards": int(getattr(f, "career_fotn_awards", 0) or 0),
        "fight_history_len": len(getattr(f, "fight_history", []) or []),
        "injury_active": injury_active,
    }

def _dump_result(r):
    """NarratedFightResult → sorted-key dict."""
    if r is None:
        return None
    d = {}
    for k in ("winner_id", "loser_id", "method", "finish_round",
              "finish_time", "decision_type", "sub_type"):
        d[k] = getattr(r, k, None)
    # per-round stats
    for side, key in [("fighter1_stats", "fighter1_stats"), ("fighter2_stats", "fighter2_stats")]:
        stats = getattr(r, key, None) or []
        d[side] = [dict(s) for s in stats]
    # judges
    js = getattr(r, "judge_scores", None) or []
    d["judge_scores"] = [list(x) for x in js]
    # commentary hash — capture without hoarding text
    commentary = getattr(r, "full_commentary", "") or ""
    if not commentary:
        rc = getattr(r, "round_commentary", None) or []
        commentary = "\n".join(str(x) for x in rc)
    d["commentary_sha16"] = _sha16(commentary)
    d["commentary_len"] = len(commentary)
    d["key_moments_len"] = len(getattr(r, "key_moments", []) or [])
    return d

def build_wrapper(bridge, orig_fn):
    """Wrap _simulate_narrated_fight_fn to capture every call end-to-end."""
    def wrapped(*args, **kwargs):
        # INPUT capture
        fa1 = args[0] if args else kwargs.get("fighter1")
        fa2 = args[1] if len(args) > 1 else kwargs.get("fighter2")
        f1_id = getattr(fa1, "fighter_id", None)
        f2_id = getattr(fa2, "fighter_id", None)
        cur_week = bridge._game_state.week_number if bridge._game_state else 0
        pre = {
            "week_at_fight": cur_week,
            "f1_id": f1_id,
            "f2_id": f2_id,
            "f1_pre": _snapshot_fighter(bridge, f1_id),
            "f2_pre": _snapshot_fighter(bridge, f2_id),
            "fa1": _fa_dict(fa1),
            "fa2": _fa_dict(fa2),
            "rounds": kwargs.get("rounds"),
            "is_title_fight": kwargs.get("is_title_fight", False),
            "is_main_event": kwargs.get("is_main_event", False),
            "starting_stamina_f1": kwargs.get("starting_stamina_f1"),
            "starting_stamina_f2": kwargs.get("starting_stamina_f2"),
            "gameplan_f1": _gp_dict(kwargs.get("gameplan_f1")),
            "gameplan_f2": _gp_dict(kwargs.get("gameplan_f2")),
            "card_slot": kwargs.get("card_slot"),
            "intro_f1_present": kwargs.get("intro_f1") is not None,
            "intro_f2_present": kwargs.get("intro_f2") is not None,
            "config": _cfg_dict(kwargs.get("config")),
        }
        # Snapshot commentary storage BEFORE the fight
        pre_commentary_keys = set(getattr(bridge, "_fight_commentary", {}).keys())
        # RUN
        result = orig_fn(*args, **kwargs)
        # OUTPUT + POST-FIGHT STATE capture
        # Diff commentary storage to find what this fight added
        post_commentary_keys = set(getattr(bridge, "_fight_commentary", {}).keys())
        new_keys = post_commentary_keys - pre_commentary_keys
        stored_commentary_shas = {}
        for k in sorted(new_keys):
            val = bridge._fight_commentary.get(k, "")
            if isinstance(val, list):
                val = "\n".join(str(x) for x in val)
            stored_commentary_shas[k] = _sha16(str(val))
        post = {
            "engine_result": _dump_result(result),
            "f1_post": _snapshot_fighter(bridge, f1_id),
            "f2_post": _snapshot_fighter(bridge, f2_id),
            # _fight_commentary storage delta captured HERE fires
            # BEFORE the storage line at game_bridge.py:13680 runs
            # (that line is downstream of the fight-fn call inside
            # _simulate_card_fights). Placeholder — filled in by a
            # post-run pass that reads the final storage state and
            # matches fight_id.
            "stored_commentary_sha16": None,   # filled by post-run pass
            "stored_commentary_present": False,
        }
        _captured_fights.append({**pre, **post})
        return result
    return wrapped

# ── Fixed player-fighter data (deterministic) ──────────────────────
# id is critical — game_bridge._create_player_fighter falls back to
# f"player_fighter_{id(fighter_data)}" (memory address, nondeterministic)
# when no id is given. Explicit id keeps the player fighter's uuid
# reproducible across runs.
PLAYER_FIGHTER_DATA = {
    "id":           "player_baseline_lw_001",
    "name":         "Reference Fighter",
    "nickname":     "The Baseline",
    "weight_class": "Lightweight",
    "age":          26,
    "country":      "USA",
    "style":        "Balanced",
    "overall":      75,
    "potential":    85,
    "strength":     72, "speed": 78, "cardio": 76, "chin": 74, "recovery": 70,
    "boxing":       75, "kicks": 70, "clinch_striking": 65, "striking_defense": 72,
    "takedowns":    68, "takedown_defense": 74, "top_control": 70, "submissions": 65,
    "guard":        68, "clinch_control": 65,
    "heart":        75, "fight_iq": 78, "composure": 72,
}

# Gameplan presets for player-tier coverage.
GAMEPLAN_PRESETS = ["AGGRESSIVE", "BALANCED", "MEASURED", "DEFENSIVE"]

def _pick_opponent(bridge, player_fid, gameplan_index):
    """Deterministic AI opponent selection — same LW roster, index-picked."""
    if not bridge._game_state:
        return None
    lw_fighters = [
        f for f in bridge._game_state.fighters.values()
        if getattr(f, "weight_class", "") == "Lightweight"
        and f.fighter_id != player_fid
        and getattr(f, "is_active", True)
    ]
    lw_fighters.sort(key=lambda f: f.fighter_id)  # stable order (uuid seeded)
    if not lw_fighters:
        return None
    return lw_fighters[gameplan_index % len(lw_fighters)]

def run_main_tier(bridge):
    """MAIN tier — 12-week Path A world sim."""
    print(f"# MAIN tier: {MAIN_WEEKS} weeks of world sim")
    for w in range(MAIN_WEEKS):
        bridge.advance_week()
    n_events = len(bridge._completed_events)
    n_bouts = sum(len(e.get("fights", [])) for e in bridge._completed_events)
    print(f"  → {n_events} events, {n_bouts} bouts")

def run_player_tier(bridge, player_fid):
    """PLAYER tier — one player fight per gameplan preset.

    Each fight uses a different pre-fight fatigue value so the stamina-
    wiring path is exercised across the full input range. If wiring is
    bypassed to constant 100, the varied inputs collapse to the same
    output — fixture catches the divergence.
    """
    print(f"# PLAYER tier: {len(GAMEPLAN_PRESETS)} fights, one per gameplan preset")
    # Fatigue schedule per preset — non-zero values so get_starting_stamina
    # returns something != 100.0, making the stamina wiring observable.
    fatigue_by_preset = {"AGGRESSIVE": 0, "BALANCED": 25, "MEASURED": 50, "DEFENSIVE": 75}
    player = bridge._game_state.get_fighter(player_fid)
    for i, preset in enumerate(GAMEPLAN_PRESETS):
        opp = _pick_opponent(bridge, player_fid, i)
        if opp is None:
            print(f"  ⚠️  no opponent for preset {preset}")
            continue
        # Load fatigue into the player before this fight — game_bridge reads
        # `getattr(fighter, 'fatigue', 0)` at the stamina-wiring site.
        fatigue = fatigue_by_preset.get(preset, 0)
        try:
            setattr(player, "fatigue", fatigue)
        except Exception:
            pass
        fight = {
            "fight_id":       f"probe_player_{i}_{preset.lower()}",
            "fighter1_id":    player.fighter_id,
            "fighter2_id":    opp.fighter_id,
            "fighter1_name":  player.name,
            "fighter2_name":  opp.name,
            "weight_class":   "Lightweight",
            "event_name":     f"ORACLE-BRIDGE1 Player Fight {i}",
            "is_title_fight": False,
            "is_player_fight":True,
            "card_slot":      "co_main",
            "gameplan":       preset,
            "purse":          10000,
        }
        # Direct _run_real_engine invocation with player-side gameplan
        result = bridge._run_real_engine(fight, player, opp, player.name, opp.name)
        print(f"  → {preset}: fatigue={fatigue} winner={result.get('winner_name','?')[:24]} "
              f"method={result.get('method')} R{result.get('round_finished')}")

def build_fixture():
    import game_bridge as _gb
    # Wrap the fight-fn AT MODULE LEVEL so both _simulate_card_fights
    # (Path A) and _run_real_engine (player fight) hit the wrapper.
    _orig_fn = _gb._simulate_narrated_fight_fn

    from game_bridge import GameBridge
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bridge = GameBridge()
        bridge._user_id = "oracle_bridge_probe"

    # Wrap ONLY after bridge is instantiated (module-level var stable)
    _gb._simulate_narrated_fight_fn = build_wrapper(bridge, _orig_fn)

    with contextlib.redirect_stdout(buf):
        ok = bridge.new_game(camp_name="ProbeCamp", camp_location="LV",
                             camp_tier="GARAGE", coach_data={},
                             fighter_data=PLAYER_FIGHTER_DATA)
    if not ok:
        print("!!! new_game failed", file=sys.stderr)
        print(buf.getvalue()[-2000:], file=sys.stderr)
        sys.exit(1)

    # Locate player fighter
    player_fid = None
    for fid, f in bridge._game_state.fighters.items():
        if getattr(f, "camp_id", None) == bridge._game_state.player_camp_id:
            player_fid = fid
            break
    if not player_fid:
        print("!!! no player fighter created", file=sys.stderr)
        sys.exit(1)

    with contextlib.redirect_stdout(buf):
        run_main_tier(bridge)
        run_player_tier(bridge, player_fid)

    # Post-run pass A: enrich captures with fight-dict source-of-truth
    # fields that the fight-fn wrapper couldn't see. Path A does NOT pass
    # is_title_fight as a kwarg to simulate_narrated_fight (grep verified);
    # the flag is on the fight dict in _completed_events. Match by
    # (week, f1_id, f2_id) which is stable.
    completed = bridge._completed_events
    # Build lookup: (week, f1_id, f2_id) → source fight dict
    fight_lookup = {}
    for ev in completed:
        ev_week = ev.get("week")
        for f in ev.get("fights", []):
            key = (ev_week, f.get("fighter1_id"), f.get("fighter2_id"))
            fight_lookup[key] = f
            # Symmetric key
            rev_key = (ev_week, f.get("fighter2_id"), f.get("fighter1_id"))
            fight_lookup[rev_key] = f
    for cf in _captured_fights:
        wk = cf.get("week_at_fight")
        key = (wk, cf.get("f1_id"), cf.get("f2_id"))
        src = fight_lookup.get(key)
        if src is None:
            # Player fight — not in _completed_events under standard path.
            # Player-tier fights are stored differently. Fall back to
            # inference from the captured metadata: player fights have
            # f1_id starting with "player_" and card_slot from PLAYER tier.
            cf["source_is_title_fight"] = False
            cf["source_card_slot"] = cf.get("card_slot") or "co_main"
            cf["source_fight_id_prefix"] = "probe_player" if (cf.get("f1_id") or "").startswith("player_") else "unknown"
        else:
            cf["source_is_title_fight"] = bool(src.get("is_title_fight"))
            cf["source_card_slot"] = src.get("card_slot")
            fid = src.get("fight_id") or ""
            cf["source_fight_id_prefix"] = fid.split("_")[0] if fid else "unknown"

    # Post-run pass B: injury coverage — walk injury_system + news
    # to record which fights are downstream of a new injury.
    # Match: any injury news_item created during the run mentioning a
    # fighter → mark the last captured fight for that fighter.
    injury_events = []
    news_items = getattr(bridge, "_news_items", []) or []
    for n in news_items:
        if n.get("category") == "injury":
            injury_events.append({
                "fighter_id": n.get("fighter_id"),
                "week": n.get("week"),
                "headline_sha": _sha16(str(n.get("headline", ""))),
            })
    injuries_by_fid_week = {}
    for ie in injury_events:
        key = (ie["fighter_id"], ie["week"])
        injuries_by_fid_week[key] = ie["headline_sha"]
    for cf in _captured_fights:
        wk = cf.get("week_at_fight")
        cf["injury_after_fighter1"] = injuries_by_fid_week.get((cf.get("f1_id"), wk))
        cf["injury_after_fighter2"] = injuries_by_fid_week.get((cf.get("f2_id"), wk))

    # Post-run pass C: fill in each captured fight's stored_commentary_sha16
    # by reading the final _fight_commentary state (populated at
    # game_bridge.py:13680 for Path A and :17948 for player, both AFTER
    # the wrapped fight-fn returns).
    #
    # Path A keys are `fight_{week}_{f1_id}_{f2_id}` per _make_scheduled_fight
    # (game_bridge.py:16351). Player keys are our explicit
    # `probe_player_{i}_{preset}`. We match by both.
    commentary_all = getattr(bridge, "_fight_commentary", {})
    player_preset_order = [f"probe_player_{i}_{p.lower()}" for i, p in enumerate(GAMEPLAN_PRESETS)]
    player_idx = 0
    for cf in _captured_fights:
        f1_id = cf.get("f1_id")
        f2_id = cf.get("f2_id")
        wk = cf.get("week_at_fight", 0)
        found_key = None
        # Path A shape
        candidate = f"fight_{wk}_{f1_id}_{f2_id}"
        if candidate in commentary_all:
            found_key = candidate
        else:
            candidate = f"fight_{wk}_{f2_id}_{f1_id}"
            if candidate in commentary_all:
                found_key = candidate
        # Player fight — sequential match by capture order
        if found_key is None and (f1_id or "").startswith("player_"):
            if player_idx < len(player_preset_order):
                pk = player_preset_order[player_idx]
                player_idx += 1
                if pk in commentary_all:
                    found_key = pk
        if found_key:
            val = commentary_all[found_key]
            if isinstance(val, list):
                val = "\n".join(str(x) for x in val)
            cf["stored_commentary_sha16"] = _sha16(str(val))
            cf["stored_commentary_present"] = True
            cf["stored_commentary_key"] = found_key

    # Session-total is still recorded but the checker does not gate on it
    # (per Van's revision — hashes localize nothing). Kept for forensics.
    commentary_summary = []
    for k in sorted(commentary_all.keys()):
        v = commentary_all[k]
        if isinstance(v, list):
            v = "\n".join(str(x) for x in v)
        commentary_summary.append(f"{k}={_sha16(str(v))}")
    commentary_session_sha = _sha16("\n".join(commentary_summary))

    # ── Assemble fixture ──────────────────────────────────────────
    fixture = {
        "meta": {
            "seed": 42,
            "main_weeks": MAIN_WEEKS,
            "player_gameplans": GAMEPLAN_PRESETS,
            "fixture_version": 2,  # bumped: added commentary_session_sha
            "total_captured_fights": len(_captured_fights),
            "total_events": len(bridge._completed_events),
            "commentary_stored_key_count": len(commentary_all),
            "commentary_session_sha16": commentary_session_sha,
        },
        "fights": _captured_fights,
    }

    return fixture, buf.getvalue()

def main():
    fixture, log = build_fixture()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixture.json")
    with open(out_path, "w") as f:
        json.dump(fixture, f, indent=2, default=str, sort_keys=True)
    n = fixture["meta"]["total_captured_fights"]
    size = os.path.getsize(out_path)
    print(f"# fixture written: {out_path}")
    print(f"#   size: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"#   captured fights: {n}")
    print(f"#   MAIN events: {fixture['meta']['total_events']}")
    print()
    # Summary of fight distribution (uses ENRICHED source-of-truth fields)
    slots = {}
    titles = 0
    player_fights = 0
    styles_f1 = set()
    styles_f2 = set()
    wcs = set()
    injuries = 0
    for f in fixture["fights"]:
        s = f.get("source_card_slot") or f.get("card_slot", "?")
        slots[s] = slots.get(s, 0) + 1
        if f.get("source_is_title_fight"):
            titles += 1
        if f.get("gameplan_f1", {}) and (f.get("gameplan_f1") or {}).get("aggression") != 0:
            player_fights += 1
        if f.get("fa1"):
            styles_f1.add(f["fa1"].get("fighting_style"))
        if f.get("fa2"):
            styles_f2.add(f["fa2"].get("fighting_style"))
        wc = None
        if f.get("f1_pre"):
            wc = f["f1_pre"].get("weight_class")
        if wc:
            wcs.add(wc)
        # Injury signal — enriched from news_items cross-reference
        if f.get("injury_after_fighter1") or f.get("injury_after_fighter2"):
            injuries += 1
    print(f"# Coverage summary:")
    print(f"#   card_slot distribution: {slots}")
    print(f"#   title fights: {titles}")
    print(f"#   player-side non-neutral gameplans: {player_fights}")
    print(f"#   weight classes: {sorted(w for w in wcs if w)}")
    print(f"#   f1 fighting styles observed: {sorted(s for s in styles_f1 if s)}")
    print(f"#   new injuries during fights: {injuries}")

if __name__ == "__main__":
    main()
