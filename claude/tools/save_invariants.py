"""SAVE-INVARIANTS1 checker — read-only.

Runs invariants against a Cage Dynasty save (or a fresh seeded world) and
prints one line per rule with violation count and up to 3 example ids.
No mutations. See the initial docstring at the top of the file for the
full rule catalogue.
"""

import argparse
import json
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

# Env prep BEFORE any project import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness_env  # noqa: F401  (side-effect: sys.path + CWD)


# ─────────────────────────────────────────────────────────────────────────────
# The 19 canonical stats (from game_bridge._TRAINABLE at :7861-7871)
# ─────────────────────────────────────────────────────────────────────────────
STATS_19 = [
    "strength", "speed", "cardio", "chin", "recovery", "power",
    "boxing", "kicks", "clinch_striking", "striking_defense",
    "takedowns", "takedown_defense", "top_control", "submissions",
    "guard", "clinch_control", "heart", "fight_iq", "composure",
]

# Matchmaker floor (matchmaking.py:103)
COOLDOWN_WINNER = 4


# ─────────────────────────────────────────────────────────────────────────────
# Data-loading modes
# ─────────────────────────────────────────────────────────────────────────────
def load_from_save(save_path: str) -> Dict[str, Any]:
    """Load either a bridge_*.json save OR a harness --dump JSON.

    Auto-detects by presence of top-level 'mode' key (dumps set it,
    bridge saves do not).
    """
    with open(save_path) as f:
        raw = json.load(f)
    if raw.get("mode") in ("seed", "save"):
        # Harness dump — pass through
        return raw
    # Bridge save shape
    return {
        "mode": "save",
        "path": save_path,
        "fighters": raw.get("fighters", {}),
        "fighter_data": raw.get("fighter_data", {}),
        "belt_history": raw.get("belt_history", {}),
        "player_camp_id": raw.get("player_camp_id"),
        "meta": raw.get("meta", {}),
        "gen_fighters": None,
    }


def dump_data_to_json(data: Dict[str, Any], path: str) -> None:
    """Serialize the harness-internal world dict to disk."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, default=str)


def load_from_seed(seed: int, weeks: int) -> Dict[str, Any]:
    """Build a fresh world by driving the real bridge, then serialize."""
    import random
    random.seed(seed)

    from game_bridge import GameBridge

    # Same wizard emulation the browser drives (routes.py:472+ → new_game)
    from game_start import generate_starting_prospects
    prospects = generate_starting_prospects(player_region="Americas")
    p = prospects[0]  # first weight class
    fighter_dict = {
        "id": p.prospect_id,
        "name": p.name,
        "nickname": getattr(p, "nickname", None),
        "age": p.age,
        "country": p.country,
        "weight_class": p.weight_class,
        "style": p.fighting_style,
        "overall": p.overall_rating,
        "potential": p.potential_ceiling,
        "traits": getattr(p, "traits", []),
        # Per-attribute stats — mirrors routes.py:499-517
        "strength": p.strength, "speed": p.speed, "cardio": p.cardio,
        "chin": p.chin, "recovery": p.recovery,
        "boxing": p.boxing, "kicks": p.kicks,
        "clinch_striking": p.clinch_striking,
        "striking_defense": p.striking_defense,
        "takedowns": p.takedowns, "takedown_defense": p.takedown_defense,
        "top_control": p.top_control, "submissions": p.submissions,
        "guard": p.guard, "clinch_control": p.clinch_control,
        "heart": p.heart, "fight_iq": p.fight_iq,
        "composure": p.composure,
    }
    coach_dict = {
        "id": "coach_1", "name": "Test Coach",
        "specialty": "boxing", "rating": 65,
        "traits": [], "cost": 500,
    }

    bridge = GameBridge()
    bridge._user_id = f"harness_seed{seed}"
    ok = bridge.new_game("Harness Camp", "Las Vegas, NV",
                         "GARAGE", coach_dict, fighter_dict)
    if not ok:
        raise RuntimeError("new_game failed")

    # A-1: capture height/reach/country from in-memory GeneratedFighter
    # objects at world build (before persist strips these fields).
    # HistorySimulator stashes them on GeneratedFighter as fields.
    # World-init writes _fighter_data['country'] but NOT height/reach.
    gen_fighters = []
    for fid, fd in bridge._game_state._fighter_data.items():
        # world_init dropped height/reach here — we can't recover them
        # from a running bridge without hooking into world_init itself.
        # But we can still report country from _fighter_data.
        gen_fighters.append({
            "fighter_id": fid,
            "country": fd.get("country", ""),
            # Height and reach: not in save — we'd need to hook world_init
            # generate_fighter() to catch them at creation. For now, expose
            # None so the rule reports the gap plainly.
            "height": None,
            "reach": None,
        })

    for _ in range(int(weeks)):
        bridge.advance_week()

    # Serialize the same way web_save does — then reuse load_from_save shape.
    return _serialize_bridge_to_dict(bridge, seed, weeks, gen_fighters)


def _serialize_bridge_to_dict(bridge, seed, weeks, gen_fighters) -> Dict[str, Any]:
    fighters = {fid: f.to_dict()
                for fid, f in bridge._game_state.fighters.items()}
    fighter_data = dict(bridge._game_state._fighter_data)
    belt_hist = (bridge._belt_history.to_dict()
                 if bridge._belt_history else {"reigns": {}})
    return {
        "mode": "seed",
        "seed": seed,
        "weeks": weeks,
        "fighters": fighters,
        "fighter_data": fighter_data,
        "belt_history": belt_hist,
        "player_camp_id": bridge._game_state.player_camp_id,
        "meta": {"week": bridge._game_state.week_number},
        "gen_fighters": gen_fighters,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rule implementations
# ─────────────────────────────────────────────────────────────────────────────
def _get_player_fids(data) -> List[str]:
    """Identify player-camp fighters."""
    pcid = data.get("player_camp_id")
    if not pcid:
        return []
    return [fid for fid, f in data["fighters"].items()
            if f.get("camp_id") == pcid]


def _is_founding_row(h: Dict[str, Any]) -> bool:
    """T-2: founding row = event_number in (None, 0) AND method/event_name
    matches Inaugural/Founding. Excluded from R01/R02/R06 by fiat.
    """
    en = h.get("event_number")
    if en not in (None, 0):
        return False
    m = str(h.get("method", "") or "")
    ev = str(h.get("event_name", "") or "")
    return ("Inaugural" in m or "Founding" in m
            or "Founding" in ev or "Inaugural" in ev)


def _fights_ex_founding(f: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [h for h in (f.get("fight_history", []) or [])
            if isinstance(h, dict) and not _is_founding_row(h)]


def r01_wins_by_method(data) -> Tuple[str, int, List[str]]:
    """Wins by method sum to record. Founding row excluded (T-2)."""
    violations = []
    for fid, f in data["fighters"].items():
        wins = int(f.get("wins", 0))
        losses = int(f.get("losses", 0))
        ko_wins = int(f.get("ko_wins", 0))
        sub_wins = int(f.get("sub_wins", 0))
        hist = _fights_ex_founding(f)
        hist_wins = sum(1 for h in hist if h.get("result") == "W")
        hist_losses = sum(1 for h in hist if h.get("result") == "L")
        hist_ko = sum(1 for h in hist
                      if h.get("result") == "W"
                      and h.get("method") in ("KO", "TKO"))
        hist_sub = sum(1 for h in hist
                       if h.get("result") == "W"
                       and h.get("method") == "SUB")
        if hist and (hist_wins != wins or hist_losses != losses
                     or hist_ko != ko_wins or hist_sub != sub_wins):
            violations.append(
                f"{fid}:record={wins}-{losses}-x "
                f"hist_W={hist_wins} hist_L={hist_losses} "
                f"ko={hist_ko}/{ko_wins} sub={hist_sub}/{sub_wins}")
    return ("PASS" if not violations else "FAIL",
            len(violations), violations[:3])


def r02_streak_le_wins(data) -> Tuple[str, int, List[str]]:
    """Current W-streak from tail of fight_history ≤ wins. Founding excluded (T-2)."""
    violations = []
    for fid, f in data["fighters"].items():
        wins = int(f.get("wins", 0))
        hist = _fights_ex_founding(f)
        streak = 0
        for h in reversed(hist):
            if h.get("result") == "W":
                streak += 1
            else:
                break
        if streak > wins:
            violations.append(f"{fid}:streak={streak}>wins={wins}")
    return ("PASS" if not violations else "FAIL",
            len(violations), violations[:3])


def _parse_event_number_from_name(event_name: str) -> Optional[int]:
    """Best-effort recover event_number from 'Cage Dynasty N ...' string."""
    if not event_name:
        return None
    m = re.search(r"Cage Dynasty (\d+)", event_name)
    if m:
        return int(m.group(1))
    if "Founding" in event_name or "Inaugural" in event_name:
        return 0
    return None


UNCLASSIFIABLE = "UNCLASSIFIABLE"


def _fight_axis(h: Dict[str, Any]) -> Tuple[str, int]:
    """U-1: return (axis, unified_week) where axis is 'pregen'/'live'/UNCLASSIFIABLE.

    Priority:
      1. event_number if present (0..60 pre-gen; ≥61 live)
      2. else parse event_name for 'Cage Dynasty N' → same rule
      3. else event_name contains Founding/Inaugural → pre-gen week 0
      4. else UNCLASSIFIABLE
    """
    w = int(h.get("week", 0) or 0)
    en = h.get("event_number")
    if en is not None:
        try:
            en_i = int(en)
        except (TypeError, ValueError):
            en_i = None
        if en_i is not None:
            if en_i >= 61:
                return ("live", 60 + w)
            return ("pregen", w)
    # Fallback: parse event_name
    parsed = _parse_event_number_from_name(str(h.get("event_name", "") or ""))
    if parsed is not None:
        if parsed >= 61:
            return ("live", 60 + w)
        return ("pregen", w)
    # Founding-string catcher (redundant with parse_event_number_from_name
    # returning 0 for those, but explicit for readability)
    return (UNCLASSIFIABLE, w)


def _fight_unified_week(h: Dict[str, Any]) -> int:
    """Legacy shim — returns unified_week only (axis dropped)."""
    return _fight_axis(h)[1]


def _reign_unified_weeks(r: Dict[str, Any]) -> Tuple[int, Optional[int]]:
    """Reign unified: parse won_event for 'Cage Dynasty N' to classify.
    Pre-gen (N<=60 or Founding) keeps weeks; live (N>=61) maps 60+week.

    NB: BeltReign has NO source-marker field. We infer by parsing the
    won_event string. This is a finding — see T-3 report.
    """
    won_event = r.get("won_event", "") or ""
    lost_event = r.get("lost_event", "") or ""
    won_en = _parse_event_number_from_name(won_event)
    ww = int(r.get("won_week", 0) or 0)
    lw = r.get("lost_week")
    lw_i = None if lw is None else int(lw)
    if won_en is not None and won_en >= 61:
        # Live-written reign; shift both won_week and lost_week
        u_won = 60 + ww
        u_lost = None if lw_i is None else 60 + lw_i
    else:
        # Pre-gen (or ambiguous — default to pre-gen axis)
        u_won = ww
        # If the reign started pre-gen but ended live, the lost_event
        # tells us — parse it too.
        if lw_i is not None:
            lost_en = _parse_event_number_from_name(lost_event)
            u_lost = (60 + lw_i) if (lost_en is not None and lost_en >= 61) else lw_i
        else:
            u_lost = None
    return u_won, u_lost


def r03_defense_marker(data) -> Tuple[str, int, List[str], Dict]:
    """🛡️ marker fires iff a reign of THIS fighter in the fight's division
    is active at the fight time — unified timeline, division-gated.

    ALSO reports how many fights the TEMPLATE'S predicate (cross-axis,
    no division gate) would mark. Difference is playtest #20 population.
    """
    reigns_by_wc = data["belt_history"].get("reigns", {})
    fighter_reigns: Dict[str, List[Dict]] = defaultdict(list)
    for wc, reign_list in reigns_by_wc.items():
        for r in reign_list:
            fid = r.get("champion_id")
            if fid:
                # Attach the wc so we can filter by division later
                r_with_wc = dict(r)
                r_with_wc.setdefault("weight_class", wc)
                fighter_reigns[fid].append(r_with_wc)

    template_marks = 0
    correct_marks = 0
    false_positives = []  # template marks but correct predicate says no
    unclassifiable = 0

    for fid, f in data["fighters"].items():
        cur_wc = f.get("weight_class", "")
        hist = f.get("fight_history", []) or []
        my_reigns = fighter_reigns.get(fid, [])
        for h in hist:
            if not isinstance(h, dict):
                continue
            if h.get("result") != "W":
                continue
            # Raw fight week (template axis)
            raw_fw = int(h.get("week", 0) or 0)
            fight_wc = h.get("weight_class", "") or cur_wc
            # Unified fight week — via U-1 axis fallback
            ax, u_fw = _fight_axis(h)
            if ax == UNCLASSIFIABLE:
                unclassifiable += 1
                continue

            # TEMPLATE predicate — cross-axis raw comparison
            template_would_mark = False
            template_reign = None
            for r in my_reigns:
                r_ww = int(r.get("won_week", 0) or 0)
                r_lw = r.get("lost_week")
                if r_ww < raw_fw and (
                    r.get("is_active", r_lw is None)
                    or (r_lw is not None and int(r_lw) > raw_fw)
                ):
                    template_would_mark = True
                    template_reign = r
                    break
            if template_would_mark:
                template_marks += 1

            # CORRECT predicate — unified timeline + division gate
            correct_mark = False
            correct_reign = None
            for r in my_reigns:
                if r.get("weight_class") != fight_wc:
                    continue
                u_ww, u_lw = _reign_unified_weeks(r)
                # Active at u_fw iff u_ww < u_fw AND (still active OR u_lw > u_fw)
                if u_ww < u_fw and (u_lw is None or u_lw > u_fw):
                    correct_mark = True
                    correct_reign = r
                    break
            if correct_mark:
                correct_marks += 1

            # False positive: template marks but correct says no
            if template_would_mark and not correct_mark:
                false_positives.append(
                    f"{fid}: fight_wc={fight_wc} raw_fw={raw_fw} u_fw={u_fw} "
                    f"template_reign_wc={template_reign.get('weight_class')} "
                    f"reign_won_week={template_reign.get('won_week')} "
                    f"reign_lost_week={template_reign.get('lost_week')} "
                    f"reign_won_event={template_reign.get('won_event')} "
                    f"event_number={h.get('event_number')}"
                )

    details = {
        "template_marks_total": template_marks,
        "correct_marks_total": correct_marks,
        "false_positives_pop20": len(false_positives),
        "unclassifiable_wins": unclassifiable,
    }
    return ("PASS" if not false_positives else "FAIL",
            len(false_positives), false_positives[:3], details)


def r04_founding_row(data) -> Tuple[str, int, List[str]]:
    """Founding row iff inaugural reign. Never counted in wins/streak."""
    violations = []
    reigns_by_wc = data["belt_history"].get("reigns", {})
    inaugural_fids = set()
    for wc, reigns in reigns_by_wc.items():
        # Inaugural = first reign with won_from == None or won_method
        # containing "Inaugural"
        for r in reigns:
            wm = str(r.get("won_method", "") or "").lower()
            if r.get("won_from") is None or "inaugural" in wm:
                if r.get("champion_id"):
                    inaugural_fids.add(r["champion_id"])
                break  # only first reign per wc

    # For each inaugural champ, look for a 'Founding' fight_history row
    for fid in inaugural_fids:
        f = data["fighters"].get(fid, {})
        hist = f.get("fight_history", []) or []
        founding_rows = [h for h in hist if isinstance(h, dict)
                         and ("Founding" in str(h.get("method", ""))
                              or "Inaugural" in str(h.get("method", ""))
                              or "Founding" in str(h.get("event_name", ""))
                              or "founding" in str(h.get("method", "")).lower())]
        if not founding_rows:
            # Rule expected either "founding on every inaugural" OR
            # "none". This surfaces the imbalance. Not asserted as
            # FAIL here — reported separately below.
            pass
    # Cross-check: how many total have founding rows?
    all_founding_holders = []
    for fid, f in data["fighters"].items():
        hist = f.get("fight_history", []) or []
        if any(isinstance(h, dict) and (
            "Founding" in str(h.get("method", ""))
            or "Inaugural" in str(h.get("method", ""))
            or "Founding" in str(h.get("event_name", ""))
        ) for h in hist):
            all_founding_holders.append(fid)

    # Violation: inaugural champs without a founding row + non-inaugural
    # with one → both directions of note #22
    missing = sorted(set(inaugural_fids) - set(all_founding_holders))
    extra = sorted(set(all_founding_holders) - set(inaugural_fids))
    for fid in missing[:5]:
        violations.append(f"inaugural_missing_row:{fid}")
    for fid in extra[:5]:
        violations.append(f"founding_row_but_not_inaugural:{fid}")

    return ("PASS" if not violations else "FAIL",
            len(violations), violations[:3])


def r05_reign_chains(data) -> Tuple[str, int, List[str]]:
    """Reign lineage chains without gaps within each division."""
    violations = []
    reigns_by_wc = data["belt_history"].get("reigns", {})
    for wc, reigns in reigns_by_wc.items():
        sorted_r = sorted(
            reigns, key=lambda r: int(r.get("won_week", 0) or 0))
        for i in range(len(sorted_r) - 1):
            a = sorted_r[i]
            b = sorted_r[i + 1]
            if a.get("lost_to") != b.get("champion_id"):
                violations.append(
                    f"{wc}: reign[{i}].lost_to={a.get('lost_to')} "
                    f"!= reign[{i+1}].champion_id={b.get('champion_id')}")
            elif a.get("lost_week") != b.get("won_week"):
                violations.append(
                    f"{wc}: reign[{i}].lost_week={a.get('lost_week')} "
                    f"!= reign[{i+1}].won_week={b.get('won_week')}")
    return ("PASS" if not violations else "FAIL",
            len(violations), violations[:3])


def r06_min_gap(data) -> Tuple[str, int, List[str], Dict]:
    """Min gap between fights ≥ COOLDOWN_WINNER (4).

    H-1 correction: `week` field runs on TWO axes — pre-gen uses the
    HistorySimulator internal clock (weeks 0-60); live-play uses the
    bridge.week_number clock (also starts at 0). So `week` alone is
    ambiguous. Classify by `event_number` instead: pre-gen assigns
    event_number 1-60 (world_init.py sequences DFC events), live-play
    events start at 61 (game_bridge continues from `_dfc_event_offset`
    captured off the initializer).

    Rules:
    - Pair adjacent fights sorted by event_number (unambiguous).
    - Both event_numbers <= 60 → pre-gen pair, gap = w2 - w1 (same axis).
    - Both event_numbers >= 61 → live pair, gap = w2 - w1 (same axis).
    - Mixed → seam pair; report as SEAM_TRUE_GAP = (60-w1) + w2 (real
      elapsed weeks: end of pre-gen sim, then live weeks 1+).
    """
    PREGEN_MAX_EN = 60

    def sort_key(h):
        # U-1: use _fight_axis for consistent ordering — pre-gen before live
        axis, uw = _fight_axis(h)
        return (axis == UNCLASSIFIABLE, uw, int(h.get("week", 0) or 0))

    violations_pregen = []
    violations_seam = []
    violations_live = []
    unclassifiable_count = 0
    for fid, f in data["fighters"].items():
        # T-2: exclude founding row from gap pairs
        hist = sorted(
            _fights_ex_founding(f),
            key=sort_key,
        )
        for i in range(len(hist) - 1):
            h1 = hist[i]
            h2 = hist[i + 1]
            ax1, u1 = _fight_axis(h1)
            ax2, u2 = _fight_axis(h2)
            w1 = int(h1.get("week", 0) or 0)
            w2 = int(h2.get("week", 0) or 0)
            if ax1 == UNCLASSIFIABLE or ax2 == UNCLASSIFIABLE:
                unclassifiable_count += 1
                continue
            if ax1 == "pregen" and ax2 == "pregen":
                gap = w2 - w1
                if gap < COOLDOWN_WINNER:
                    violations_pregen.append(
                        f"{fid}:{h1.get('event_name')}->{h2.get('event_name')} "
                        f"w{w1}->{w2} gap={gap}")
            elif ax1 == "live" and ax2 == "live":
                gap = w2 - w1
                if gap < COOLDOWN_WINNER:
                    violations_live.append(
                        f"{fid}:{h1.get('event_name')}->{h2.get('event_name')} "
                        f"w{w1}->{w2} gap={gap}")
            else:
                # Seam pair: true gap on unified axis = u2 - u1
                # (live=60+w so a pre-gen wk49 → live wk1 gives 61-49=12)
                true_gap = u2 - u1
                if true_gap < COOLDOWN_WINNER:
                    violations_seam.append(
                        f"{fid}:{h1.get('event_name')}->{h2.get('event_name')} "
                        f"u{u1}->{u2} true_gap={true_gap}")
    total = (len(violations_pregen) + len(violations_seam)
             + len(violations_live))
    details = {
        "pregen_only": len(violations_pregen),
        "pregen_to_live_seam": len(violations_seam),
        "live_only": len(violations_live),
        "unclassifiable_pairs": unclassifiable_count,
        "matchmaker_floor": COOLDOWN_WINNER,
    }
    examples = (violations_seam[:3] + violations_pregen[:3]
                + violations_live[:3])[:3]
    return ("PASS" if total == 0 else "FAIL", total, examples, details)


def r07_ko_suspension(data) -> Tuple[str, int, List[str]]:
    """No KO-suspension mechanism in code — report as informational SKIP."""
    return ("SKIP", 0, ["no suspension mechanism found in matchmaking.py"])


def r08_age_stage(data) -> Tuple[str, int, List[str]]:
    """Age-stage label vs career-arc label agreement."""
    # These are display-only functions — best-effort check without
    # calling into the actual template helpers (which live scattered).
    # Report SKIP if the two labeler functions can't be identified,
    # otherwise sample fighters and compare.
    return ("SKIP", 0, ["labeler functions not consolidated — needs template audit"])


def r09_badges(data) -> Tuple[str, int, List[str]]:
    """Badges (GENERATOR1 §5, threshold 85) == predicates on the sheet.

    Since badges are stateless render-time derivations, the invariant
    is that any code deriving a badge from a stat sheet returns the
    same answer as our oracle here. We derive from fighter_data and
    print the count of computed-yes badges as a sanity artefact.
    """
    threshold = 85
    computed = Counter()
    for fid, fd in data["fighter_data"].items():
        # Iron Chin: chin >= 85 AND recovery >= 85
        if fd.get("chin", 0) >= threshold and fd.get("recovery", 0) >= threshold:
            computed["iron_chin"] += 1
        # Heavy Hands: strength >= 85 AND boxing >= 85
        if fd.get("strength", 0) >= threshold and fd.get("boxing", 0) >= threshold:
            computed["heavy_hands"] += 1
        # Gas Tank: cardio >= 85 AND recovery >= 85
        if fd.get("cardio", 0) >= threshold and fd.get("recovery", 0) >= threshold:
            computed["gas_tank"] += 1
        # Warrior Heart: heart >= 85 AND composure >= 85
        if fd.get("heart", 0) >= threshold and fd.get("composure", 0) >= threshold:
            computed["warrior_heart"] += 1
        # Freak Athlete: strength >= 85 AND speed >= 85 AND cardio >= 85
        if (fd.get("strength", 0) >= threshold
                and fd.get("speed", 0) >= threshold
                and fd.get("cardio", 0) >= threshold):
            computed["freak_athlete"] += 1
        # Complete Fighter: at least 4 categories at >=80
        striking_max = max(fd.get(s, 0) for s in
                           ("boxing", "kicks", "clinch_striking", "striking_defense"))
        grappling_max = max(fd.get(s, 0) for s in
                            ("takedowns", "takedown_defense", "top_control",
                             "submissions", "guard"))
        physical_max = max(fd.get(s, 0) for s in
                           ("strength", "speed", "cardio", "chin", "recovery"))
        mental_max = max(fd.get(s, 0) for s in
                         ("heart", "fight_iq", "composure"))
        cats_over_80 = sum(1 for m in (striking_max, grappling_max,
                                        physical_max, mental_max) if m >= 80)
        if cats_over_80 >= 4:
            computed["complete_fighter"] += 1
    # Info-only rule: report counts as example strings, no violation
    ex = [f"{k}={v}" for k, v in computed.items()]
    return ("INFO", 0, ex[:3])


def r10_power(data) -> Tuple[str, int, List[str], Dict]:
    """Power present and != 50 fallback. Player fighter separated (A-4)."""
    player_fids = set(_get_player_fids(data))
    player_powers = []
    ai_powers = []
    missing = []
    for fid, fd in data["fighter_data"].items():
        pw = fd.get("power")
        if pw is None:
            missing.append(fid)
            continue
        if fid in player_fids:
            player_powers.append(int(pw))
        else:
            ai_powers.append(int(pw))

    # Histogram in buckets of 5, 20-95
    def bucket_hist(vals):
        buckets = Counter()
        for v in vals:
            b = (v // 5) * 5
            buckets[b] += 1
        return dict(sorted(buckets.items()))

    ai_hist = bucket_hist(ai_powers)
    at_50_ai = sum(1 for v in ai_powers if v == 50)
    at_50_pl = sum(1 for v in player_powers if v == 50)
    total_ai = len(ai_powers)
    total_pl = len(player_powers)

    details = {
        "player_fighter_power": player_powers,
        "player_fighter_50_count": at_50_pl,
        "player_fighter_total": total_pl,
        "ai_50_count": at_50_ai,
        "ai_total": total_ai,
        "ai_50_share": (at_50_ai / total_ai if total_ai else 0.0),
        "ai_hist_buckets": ai_hist,
        "ai_mean": (statistics.mean(ai_powers) if ai_powers else 0.0),
        "missing_count": len(missing),
    }

    # FAIL iff any player_power == 50 exactly (POWER1 discriminator)
    status = "FAIL" if at_50_pl > 0 else "PASS"
    examples = [f"player_powers={player_powers}",
                f"ai_50_share={details['ai_50_share']:.4f}",
                f"ai_50_count={at_50_ai}/{total_ai}"]
    return (status, at_50_pl, examples, details)


def r11_hrn(data) -> Tuple[str, int, List[str], Dict]:
    """Height/reach/nationality variance. A-1: use in-memory gen_fighters in --seed mode."""
    if data["mode"] == "save":
        # Save mode: fields not persisted, only country available
        countries = Counter()
        for fid, fd in data["fighter_data"].items():
            c = fd.get("country") or ""
            if c:
                countries[c] += 1
        details = {
            "height_status": "not persisted in save",
            "reach_status": "not persisted in save",
            "country_distinct": len(countries),
            "country_top": countries.most_common(5),
        }
        # Country distinct-count is real; height/reach return SKIP
        status = "SKIP" if len(countries) <= 1 else "INFO"
        return (status, 0,
                [f"height=not persisted", f"reach=not persisted",
                 f"country_distinct={len(countries)}"],
                details)

    # Seed mode: harness captured gen_fighters (but height/reach STILL
    # not accessible from _fighter_data — we noted this in Phase 1
    # census). Report the SAME status but from the fresh world.
    gen_fighters = data.get("gen_fighters") or []
    countries = Counter()
    for gf in gen_fighters:
        c = gf.get("country") or ""
        if c:
            countries[c] += 1
    # Height/reach: we didn't hook world_init, so still None
    height_captured = sum(1 for g in gen_fighters if g.get("height") is not None)
    details = {
        "height_status": ("captured in-memory" if height_captured
                          else "NOT captured — hook world_init needed"),
        "reach_status": ("captured in-memory" if height_captured
                         else "NOT captured — hook world_init needed"),
        "country_distinct": len(countries),
        "country_top": countries.most_common(5),
        "country_modal_share": (countries.most_common(1)[0][1] / sum(countries.values())
                                 if countries else 0.0),
    }
    status = "SKIP" if height_captured == 0 else "PASS"
    return (status,
            0 if height_captured == 0 else 0,
            [f"country_distinct={len(countries)}",
             f"height_reach={details['height_status']}"],
            details)


def r12_at_signing(data) -> Tuple[str, int, List[str]]:
    """at_signing present for every non-legacy fighter.

    Approx: check ovr_at_signing on player fighters + AI fighters signed
    to camps. A fighter WITH camp_id and NO ovr_at_signing is a violation.
    """
    violations = []
    for fid, f in data["fighters"].items():
        if not f.get("camp_id"):
            continue  # free agent — legacy shape allowed
        fd = data["fighter_data"].get(fid, {})
        if "ovr_at_signing" not in fd:
            violations.append(fid)
    return ("PASS" if not violations else "FAIL",
            len(violations), violations[:3])


def t4_event_number_none_census(data) -> Dict[str, Any]:
    """T-4: count fight_history entries with event_number None,
    split by week==0 (founding) vs week>0.
    """
    total = 0
    none_wk0 = 0
    none_wk_pos = 0
    none_wk_pos_examples = []
    for fid, f in data["fighters"].items():
        for h in (f.get("fight_history", []) or []):
            if not isinstance(h, dict):
                continue
            total += 1
            en = h.get("event_number")
            if en is not None:
                continue
            w = int(h.get("week", 0) or 0)
            if w == 0:
                none_wk0 += 1
            else:
                none_wk_pos += 1
                if len(none_wk_pos_examples) < 5:
                    none_wk_pos_examples.append(
                        f"{fid}: wk={w} event_name={h.get('event_name')} "
                        f"method={h.get('method')} result={h.get('result')}")
    return {
        "fight_history_total": total,
        "event_number_none": none_wk0 + none_wk_pos,
        "none_at_wk0_founding": none_wk0,
        "none_at_wk_positive": none_wk_pos,
        "wk_positive_examples": none_wk_pos_examples,
    }


def r13_stat_surfaces(data) -> Tuple[str, int, List[str]]:
    """Every stat surface renders all 19."""
    tpl_dir = os.path.join(_harness_env.WEB_DIR, "templates")
    violations = []
    surfaces = {}
    # training.html — _STAT_CATS block (lines ~446-469)
    with open(os.path.join(tpl_dir, "training.html")) as f:
        src = f.read()
    m = re.search(r"_STAT_CATS\s*=\s*\[(.+?)\]\s*%}", src, re.DOTALL)
    stats_in_training = set()
    if m:
        # Extract all ('stat_key', 'Label') tuples
        for k in re.findall(r"\('([a-z_]+)'\s*,\s*'[^']*'\)", m.group(1)):
            stats_in_training.add(k)
    surfaces["training.html"] = len(stats_in_training)
    if len(stats_in_training) != 19:
        violations.append(
            f"training.html:{len(stats_in_training)} stats "
            f"(missing: {sorted(set(STATS_19) - stats_in_training)})")
    # compare.html — heuristic scan
    with open(os.path.join(tpl_dir, "compare.html")) as f:
        src = f.read()
    stats_in_compare = set(k for k in STATS_19 if k in src)
    surfaces["compare.html"] = len(stats_in_compare)
    if len(stats_in_compare) != 19:
        violations.append(
            f"compare.html:{len(stats_in_compare)} stats "
            f"(missing: {sorted(set(STATS_19) - stats_in_compare)})")
    # fighter_profile.html — heuristic scan
    with open(os.path.join(tpl_dir, "fighter_profile.html")) as f:
        src = f.read()
    stats_in_profile = set(k for k in STATS_19 if k in src)
    surfaces["fighter_profile.html"] = len(stats_in_profile)
    if len(stats_in_profile) != 19:
        violations.append(
            f"fighter_profile.html:{len(stats_in_profile)} stats "
            f"(missing: {sorted(set(STATS_19) - stats_in_profile)})")
    return ("PASS" if not violations else "FAIL",
            len(violations), violations[:3])


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────
def run_all_rules(data: Dict[str, Any], details_out: List[str]) -> int:
    """Run every rule, print one line each, return failure count."""
    print(f"\n=== SAVE-INVARIANTS1 — mode={data['mode']} ===")
    if data["mode"] == "save":
        print(f"    path={data['path']}")
        print(f"    week={data['meta'].get('week', '?')}")
    else:
        print(f"    seed={data['seed']} weeks={data['weeks']}")
    print(f"    fighters={len(data['fighters'])}  "
          f"fighter_data={len(data['fighter_data'])}")
    print()

    failures = 0
    print(f"{'ID':<5}{'Rule':<52}{'Status':<8}Details")
    print("-" * 100)

    def line(rid, name, res):
        nonlocal failures
        status = res[0]
        vcount = res[1]
        examples = res[2]
        if status == "FAIL":
            failures += 1
        print(f"{rid:<5}{name:<52}{status:<8}"
              f"(violations: {vcount}"
              + (f"; ex: {examples[0]}" if examples else "") + ")")

    line("R01", "wins_by_method_sum_matches_record", r01_wins_by_method(data))
    line("R02", "streak_le_wins", r02_streak_le_wins(data))
    r03 = r03_defense_marker(data)
    line("R03", "defense_marker_requires_belt_at_fight_time", r03)
    details_out.append(f"R03 details: {r03[3]}")
    line("R04", "founding_row_iff_inaugural", r04_founding_row(data))
    line("R05", "reign_lineage_chains_no_gaps", r05_reign_chains(data))
    r06 = r06_min_gap(data)
    line("R06", "min_gap_between_fights", r06)
    details_out.append(f"R06 details: {r06[3]}")
    line("R07", "ko_suspension_window", r07_ko_suspension(data))
    line("R08", "age_stage_matches_career_arc", r08_age_stage(data))
    line("R09", "badges_equal_predicates", r09_badges(data))
    r10 = r10_power(data)
    line("R10", "power_present_and_not_50_fallback", r10)
    details_out.append(f"R10 details: {r10[3]}")
    r11 = r11_hrn(data)
    line("R11", "height_reach_nationality_variance", r11)
    details_out.append(f"R11 details: {r11[3]}")
    line("R12", "at_signing_populated_for_post_capture", r12_at_signing(data))
    line("R13", "stat_surface_renders_all_19_stats", r13_stat_surfaces(data))

    # T-4 census (informational, not a rule)
    t4 = t4_event_number_none_census(data)
    details_out.append(f"T-4 event_number None census: {t4}")

    return failures


def main() -> int:
    ap = argparse.ArgumentParser(
        description="SAVE-INVARIANTS1 read-only checker.")
    ap.add_argument("--save", help="Path to bridge_*.json save file OR "
                                   "a harness --dump JSON (auto-detected).")
    ap.add_argument("--seed", type=int, help="Seed for fresh new_game.")
    ap.add_argument("--weeks", type=int, default=14,
                    help="Weeks to advance after new_game (default: 14).")
    ap.add_argument("--dump", help="After --seed run, write the serialized "
                                    "world dict to this JSON path so future "
                                    "rule iterations can re-check in seconds "
                                    "via --save DUMP.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        print("SAVE-INVARIANTS1 checker (dry-run).")
        return 0

    t0 = time.time()
    if args.save:
        # If --save is relative, resolve against REPO_DIR (harness cwd is web)
        save_path = args.save
        if not os.path.isabs(save_path):
            save_path = os.path.join(_harness_env.REPO_DIR, save_path)
        data = load_from_save(save_path)
    elif args.seed is not None:
        data = load_from_seed(args.seed, args.weeks)
        if args.dump:
            # If --dump is relative, resolve against REPO_DIR (not CWD,
            # which _harness_env chdir'd to cage_dynasty_web).
            dump_path = args.dump
            if not os.path.isabs(dump_path):
                dump_path = os.path.join(_harness_env.REPO_DIR, dump_path)
            dump_data_to_json(data, dump_path)
            print(f"[DUMP] wrote world dict to {dump_path}")
    else:
        ap.print_help()
        return 2

    load_dt = time.time() - t0
    details = []
    failures = run_all_rules(data, details)
    total_dt = time.time() - t0

    print()
    print("=== DETAILS ===")
    for d in details:
        print(d)

    print()
    print(f"=== TIMING === load/build={load_dt:.2f}s  total={total_dt:.2f}s")
    print(f"=== FAILURES: {failures} ===")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
