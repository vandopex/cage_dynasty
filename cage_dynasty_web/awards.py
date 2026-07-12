"""PREGEN-YEARLY-AWARDS1: shared yearly-awards compute.

Consumed by live-play (advance_week → _run_yearly_awards) and world-init
(history sim → _compute_yearly_awards_for_year). Both callers adapt into
YearlyAwardsFight, delegate to compute_yearly_awards.

Behavior contract vs the pre-extraction inline _run_yearly_awards compute:
byte-identical (awards, structured) for identical inputs. Verified by a
mechanical-equivalence gate at ship time.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


def canonical_specialty_method(engine_method: str, sub_type: str = '') -> str:
    """FINISH-DETAIL-PERSIST: canonical form for the specialty_method field.

    Consumed by both live-play (game_bridge._simulate_fight / _run_real_engine /
    _simulate_card_fights / _simulate_ai_fights_week) and pre-gen (world_init.
    simulate_fight_full_engine / simulate_fight_simple). Kept here so both
    stores emit the SAME string shape — the recurring divergence trap
    (round vs round_finished, is_title_fight vs was_title_fight, flat-avg vs
    style-weighted OVR) has bitten us three times; the specialty label
    format joins that same class and gets normalized once, here.

    Canonical shape:
      "KO (Head Kick)"            — engine's specialty KO label (kept as-is)
      "TKO (Body Shot)"           — engine's specialty TKO label (kept as-is)
      "SUB (armbar)"              — normalized from engine's "Submission (armbar)"
                                     (raw fight_engine) or synthesized from
                                     ("Submission", "armbar") (fight_integration)
      "KO"                        — bare label (boxing-punch KO, no specialty)
      "TKO"                       — bare label (accumulated-damage stoppage)
      "SUB"                       — defensive default; should not occur since
                                     the engine always names a submission
      "DEC" / "UNY DEC" / "SPLIT DEC" / "MAJ DEC" — decisions (no specialty)
      "DRAW"                      — draws (no specialty)

    Args:
      engine_method: The engine's method string. From raw fight_engine.simulate_fight
        this may be "Submission (armbar)" / "KO (Head Kick)" / "KO" / "Decision"-
        style. From fight_integration.NarratedFightResult this may be bare
        "Submission" (with sub_type in a separate field) or "KO (Head Kick)".
      sub_type: Optional bare sub_type name (from NarratedFightResult.sub_type).
        Only used when engine_method is bare "Submission" and sub_type is set.

    Returns:
      The canonical specialty_method string.
    """
    if engine_method.startswith('Submission ('):
        # Raw engine format: "Submission (armbar)" → "SUB (armbar)"
        return 'SUB' + engine_method[len('Submission'):]
    if engine_method == 'Submission' and sub_type:
        # NarratedFightResult format: bare "Submission" + separate sub_type
        return f'SUB ({sub_type})'
    if engine_method == 'Submission':
        return 'SUB'
    # KO/TKO specialty labels ("KO (Head Kick)", "TKO (Body Shot)"), bare
    # "KO"/"TKO", "Decision" variants, "Draw" — kept as-is (already canonical).
    return engine_method


@dataclass
class YearlyAwardsFight:
    """Normalized fight shape consumed by compute_yearly_awards.

    Live-play adapter reads _completed_events fight dicts (has 'winner_id',
    'is_fotn', 'round_finished'). Pre-gen adapter reads per-fighter
    fight_history entries (has 'result', 'opponent_id', 'round') plus the
    fighter's own name. Both adapt into this shape at the module boundary.
    """
    week:           int
    winner_id:      str
    loser_id:       str
    winner_name:    str
    loser_name:     str
    method:         str
    round_finished: Optional[int]  # canonical; pre-gen 'round' normalized here
    is_fotn:        bool = False   # pre-gen adapter always emits False
    is_title_fight: bool = False   # AWARDS-KOTY-SOTY-RESELECT: title-bonus input
    fight_id:       str = ''       # pre-gen adapter emits '' (no fight_id in sim records)


def _adapt_completed_events(
    completed_events: List[Dict[str, Any]],
    year_start:       int,
) -> Tuple[Dict[str, List[YearlyAwardsFight]], List[YearlyAwardsFight]]:
    """Live-play adapter: _completed_events → (year_fights, all_year_fights).

    year_fights maps fighter_id → list of that fighter's fights this year
    (each fight appears in BOTH sides' lists — matches original iteration
    at game_bridge.py:4033-4036).
    all_year_fights is the flat list of unique fights in event order
    (matches original KO/Sub/Camp-of-Year event iteration at :4114-4200).
    """
    all_year_fights: List[YearlyAwardsFight] = []
    year_fights: Dict[str, List[YearlyAwardsFight]] = {}
    for ev in completed_events:
        if ev.get('week', 0) < year_start:
            continue
        for fight in ev.get('fights', []):
            wid = fight.get('winner_id')
            lid = fight.get('loser_id')
            if not (wid and lid):
                continue
            yaf = YearlyAwardsFight(
                week=ev.get('week', 0),
                winner_id=wid,
                loser_id=lid,
                winner_name=fight.get('winner_name', ''),
                loser_name=fight.get('loser_name', ''),
                method=fight.get('method', 'DEC'),
                round_finished=fight.get('round_finished'),
                is_fotn=bool(fight.get('is_fotn', False)),
                is_title_fight=bool(fight.get('is_title_fight', False)),
                fight_id=fight.get('fight_id', ''),
            )
            all_year_fights.append(yaf)
            year_fights.setdefault(wid, []).append(yaf)
            year_fights.setdefault(lid, []).append(yaf)
    return year_fights, all_year_fights


def _adapt_pregen_history(
    fighters,               # Dict[str, GeneratedFighter]
    year_start: int,
    week:       int,
) -> Tuple[Dict[str, List[YearlyAwardsFight]], List[YearlyAwardsFight]]:
    """Pre-gen adapter: per-fighter fight_history → (year_fights, all_year_fights).

    Canonicalizes on the winner-side entry (result=='W'); the loser-side
    entry is skipped since the winner side already emitted the fight.
    'round' key drift normalized to round_finished HERE — no template hedge.
    Draws (result != 'W'/'L') defensively skipped with a warning; current
    pre-gen doesn't write draws to fight_history, but this future-proofs.
    Inaugural Crown tombstones (opponent_id=None) skip naturally via the
    empty-opponent guard.
    """
    all_year_fights: List[YearlyAwardsFight] = []
    year_fights: Dict[str, List[YearlyAwardsFight]] = {}
    for fid, f in fighters.items():
        for entry in getattr(f, 'fight_history', []) or []:
            if not isinstance(entry, dict):
                continue
            ew = entry.get('week', 0)
            if not (year_start <= ew < week):
                continue
            res = entry.get('result')
            if res == 'L':
                continue  # winner side will emit
            if res != 'W':
                print(f"  ⚠️  [PREGEN-YEARLY-AWARDS1] skipped fight_history "
                      f"entry for {fid}: result='{res}' (expected W or L)")
                continue
            opp_id = entry.get('opponent_id')
            if not opp_id:
                # Inaugural Crown tombstone (opponent_id=None) or corrupt entry
                continue
            yaf = YearlyAwardsFight(
                week=ew,
                winner_id=fid,
                loser_id=opp_id,
                winner_name=getattr(f, 'name', ''),
                loser_name=entry.get('opponent_name', ''),
                method=entry.get('method', 'DEC'),
                round_finished=entry.get('round'),  # drift normalize
                is_fotn=False,
                # AWARDS-KOTY-SOTY-RESELECT: pre-gen writes 'was_title_fight',
                # live-play writes 'is_title_fight'. Same shape difference the
                # awards adapter already handles for round vs round_finished.
                is_title_fight=bool(entry.get('was_title_fight', False)),
                fight_id='',
            )
            all_year_fights.append(yaf)
            year_fights.setdefault(fid, []).append(yaf)
            year_fights.setdefault(opp_id, []).append(yaf)
    return year_fights, all_year_fights


def compute_yearly_awards(
    fighters,                                                  # Dict[str, FighterRecord|GeneratedFighter]
    year_fights: Dict[str, List[YearlyAwardsFight]],
    all_year_fights: List[YearlyAwardsFight],
    year:        int,
    camps=None,                                                # Dict[str, Camp|GeneratedCamp] or None
    rand_pick: Optional[Callable[[List], Any]] = None,
    resolve_opponent_rank: Optional[Callable[[str], Optional[int]]] = None,
) -> Tuple[List[str], Dict[str, Any]]:
    """Pure yearly-awards compute.

    Categories: FOTY, YFOTY (<25), KO of Year, Sub of Year, Comeback,
    Camp of Year (skipped if camps is None).

    Behavior byte-identical to the pre-extraction inline compute at
    game_bridge.py:4023-4201 for identical inputs, verified by the
    equivalence gate. rand_pick defaults to random.choice; equivalence
    tests inject a seeded picker.
    """
    if rand_pick is None:
        import random
        rand_pick = random.choice

    active_fids = set(year_fights.keys())
    if not active_fids:
        return [], {}

    def wins_this_year(fid: str) -> int:
        return sum(1 for f in year_fights.get(fid, []) if f.winner_id == fid)

    def year_points(fid: str) -> int:
        pts = 0
        for f in year_fights.get(fid, []):
            if f.winner_id == fid:
                pts += 10
                if f.method in ('KO', 'TKO'):
                    pts += 5
                elif f.method == 'SUB':
                    pts += 3
            else:
                pts -= 2
        return pts

    awards: List[str] = []
    structured: Dict[str, Any] = {}

    # ── FOTY ─────────────────────────────────────────────────────
    candidates = [(fid, year_points(fid))
                  for fid in active_fids if year_points(fid) > 0]
    if candidates:
        foty_id, foty_pts = max(candidates, key=lambda x: x[1])
        foty = fighters.get(foty_id)
        if foty:
            wins = wins_this_year(foty_id)
            awards.append(f"🏆 FIGHTER OF THE YEAR (Year {year}): {foty.name} "
                          f"({foty_pts} pts · {wins} wins · {foty.wins}-{foty.losses})")
            structured["fighter_of_year"] = {
                "fighter_id": foty_id,
                "name":       foty.name,
                "pts":        foty_pts,
                "wins":       wins,
                "record":     f"{foty.wins}-{foty.losses}-{foty.draws}",
            }

    # ── YFOTY (age < 25) ─────────────────────────────────────────
    young = [(fid, year_points(fid))
             for fid in active_fids
             if year_points(fid) > 0 and
                getattr(fighters.get(fid), 'age', 30) < 25]
    if young:
        yoty_id, yoty_pts = max(young, key=lambda x: x[1])
        yoty = fighters.get(yoty_id)
        if yoty:
            wins = wins_this_year(yoty_id)
            awards.append(f"⭐ YOUNG FIGHTER OF THE YEAR (Year {year}): {yoty.name} "
                          f"(Age {yoty.age} · {yoty_pts} pts · {wins} wins)")
            structured["young_foty"] = {
                "fighter_id": yoty_id,
                "name":       yoty.name,
                "pts":        yoty_pts,
                "wins":       wins,
                "age":        getattr(yoty, 'age', 0),
            }

    # ── KO of Year — AWARDS-KOTY-SOTY-RESELECT ──────────────────────
    # Was: random.choice over pool gated on is_fotn — an arbitrary KO
    # from an arbitrary subset. Now: deterministic scoring across ALL
    # KO/TKO finishes in the year. FOTN gate dropped entirely — a
    # round-1 walk-off is exactly the KO that should win, and exactly
    # the fight that never wins FOTN. Scoring inputs use only fields
    # both stores carry (round, opponent rank via injected callback,
    # method, title flag). fight_id / time / etc. are display-only.
    def _opponent_rank_bonus(loser_id: str) -> int:
        if resolve_opponent_rank is None:
            return 0
        r = resolve_opponent_rank(loser_id)
        if r is None:
            return 0
        if r == 0:      return 10  # champion
        if r <= 5:      return 5   # top contender
        if r <= 15:     return 2   # ranked
        return 0

    def _score_ko(f: YearlyAwardsFight) -> Tuple[int, int, str]:
        rf = f.round_finished if f.round_finished is not None else 5
        round_bonus  = max(0, 5 - rf)
        method_bonus = 1 if f.method == 'KO' else 0    # KO > TKO
        title_bonus  = 3 if f.is_title_fight else 0
        opp_bonus    = _opponent_rank_bonus(f.loser_id)
        total        = round_bonus + opp_bonus + method_bonus + title_bonus
        # Deterministic tiebreaker: same save → same award. Higher score
        # wins; tie → earlier week (rewards decisive early-year finishes);
        # tie → lex winner_id (total ordering guarantee).
        return (total, -f.week, f.winner_id)

    def _score_sub(f: YearlyAwardsFight) -> Tuple[int, int, str]:
        rf = f.round_finished if f.round_finished is not None else 5
        round_bonus  = max(0, 5 - rf)
        title_bonus  = 3 if f.is_title_fight else 0
        opp_bonus    = _opponent_rank_bonus(f.loser_id)
        total        = round_bonus + opp_bonus + title_bonus  # no method_bonus for SOTY
        return (total, -f.week, f.winner_id)

    ko_fights = [f for f in all_year_fights if f.method in ('KO', 'TKO')]
    if ko_fights:
        ko = max(ko_fights, key=_score_ko)
        _rnd = ko.round_finished if ko.round_finished is not None else '?'
        awards.append(f"💥 KO OF THE YEAR (Year {year}): "
                      f"{ko.winner_name} def. {ko.loser_name} "
                      f"via {ko.method} R{_rnd}")
        structured["ko_of_year"] = {
            "winner_id":   ko.winner_id,
            "winner_name": ko.winner_name,
            "loser_name":  ko.loser_name,
            "method":      ko.method,
            "round":       ko.round_finished if ko.round_finished is not None else 0,
            "fight_id":    ko.fight_id,
        }

    # ── Sub of Year — AWARDS-KOTY-SOTY-RESELECT ─────────────────────
    sub_fights = [f for f in all_year_fights if f.method == 'SUB']
    if sub_fights:
        sub = max(sub_fights, key=_score_sub)
        _rnd = sub.round_finished if sub.round_finished is not None else '?'
        awards.append(f"🥋 SUBMISSION OF THE YEAR (Year {year}): "
                      f"{sub.winner_name} def. {sub.loser_name} "
                      f"by SUB R{_rnd}")
        structured["sub_of_year"] = {
            "winner_id":   sub.winner_id,
            "winner_name": sub.winner_name,
            "loser_name":  sub.loser_name,
            "round":       sub.round_finished if sub.round_finished is not None else 0,
            "fight_id":    sub.fight_id,
        }

    # ── Comeback ─────────────────────────────────────────────────
    comeback = None
    best_comeback_wins = 0
    for fid in active_fids:
        f = fighters.get(fid)
        if not f:
            continue
        w = wins_this_year(fid)
        history = getattr(f, 'fight_history', [])
        if len(history) >= 4 and w >= 3:
            recent = history[-6:]
            had_loss = any(h.get('result') == 'L' for h in recent[:3])
            if had_loss and w > best_comeback_wins:
                best_comeback_wins = w
                comeback = f
    if comeback:
        awards.append(f"💪 COMEBACK FIGHTER OF THE YEAR (Year {year}): "
                      f"{comeback.name} ({wins_this_year(comeback.fighter_id)} wins this year)")
        structured["comeback"] = {
            "fighter_id": comeback.fighter_id,
            "name":       comeback.name,
            "wins":       best_comeback_wins,
        }

    # ── Camp of Year ─────────────────────────────────────────────
    if camps is not None:
        camp_wins: Dict[str, int] = {}
        for f in all_year_fights:
            wf = fighters.get(f.winner_id)
            if wf and getattr(wf, 'camp_id', None):
                camp_wins[wf.camp_id] = camp_wins.get(wf.camp_id, 0) + 1
        if camp_wins:
            best_camp_id = max(camp_wins, key=camp_wins.get)
            best_camp    = camps.get(best_camp_id)
            if best_camp:
                awards.append(f"🏟️ CAMP OF THE YEAR (Year {year}): "
                              f"{best_camp.name} ({camp_wins[best_camp_id]} wins)")
                structured["camp_of_year"] = {
                    "camp_id": best_camp_id,
                    "name":    best_camp.name,
                    "wins":    camp_wins[best_camp_id],
                }

    return awards, structured
