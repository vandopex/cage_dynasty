# Cage Dynasty — slot fix follow-up + filed bugs (end of 2026-04-26 session)

## Context

Tonight's slot-inflation fix in `_assign_card_slot` worked as designed: the `matchup_credible` gate stops the rank-floor from forcing CO_MAIN/MAIN_EVENT when fighters fail `is_title_eligible`. **But play-test reveals a second-order bug**: Hiroshi (0-0, OVR 78, Strawweight) vs Matthew Davis still landed in a 4-round-capable slot at DFC 3 (KO R4 + FOTN), proving slot ≥ co_main. Both 0-0 fighters fail `is_title_eligible`, so `matchup_credible = False` and `min_slot = None`. The rank-floor did NOT fire. Yet the slot was still elevated. Diagnosis below identifies the root cause and files two unrelated bugs for next session.

## Finding 1 — Score-based slot promotion bypasses the credibility gate

**The slot-determination chain when `matchup_credible=False`:**

`_assign_card_slot` (`game_bridge.py:7104`) → `card_builder.assign_slot` (`card_builder.py:346`) → `_get_target_slot_by_score(matchup_score)` (`card_builder.py:382`) → routes by score thresholds:

```
score >= 80 → MAIN_EVENT  (5 rounds)
score >= 70 → CO_MAIN     (5 rounds)
score >= 55 → MAIN_CARD   (3 rounds)
score < 55  → PRELIM      (3 rounds)
```

The `min_slot` parameter is a *floor* (don't go below this), not a *ceiling*. With `min_slot=None`, score alone decides target, and `_find_available_slot` (`card_builder.py:393`) starts from `target` and only iterates *down*. So a high score promotes the fight even when the rank-floor is suppressed.

**Score formula** (`card_builder.calculate_matchup_score`, `card_builder.py:246–344`) — for two ranked fighters with adjacent ranks:

- `base_score = 40` (both ranked)
- `rank_bonus += 30` (rank_diff ≤ 1, "the gold standard")
- `rank_bonus += 12` (top_rank == 1, top-contender bonus)
- `record_bonus = 0` (combined_fights < 6)
- **Total = 82 → MAIN_EVENT target → 5 rounds**

For the Hiroshi/Davis matchup specifically: if both got ranked despite being 0-0 (the deferred `world_init.py` rookie-ranking issue), and matchmaking paired them adjacent, score is ≈ 82 and slot promotes regardless of the credibility gate. The rank_penalty branch (-50 for ranked-vs-unranked) doesn't fire because *both* are ranked.

**Conclusion:** The credibility gate (tonight's fix) and the score formula are independent levers. Both can promote a slot. Tonight we patched the rank-floor path; the score-formula path is untouched.

## Finding 2 — No alternative slot-stamping path for player fights

Question 2 from tonight's session: confirmed there is **no** secondary slot stamping that bypasses `_assign_card_slot` for player fights. The full path is:

```
challenge_fighter (game_bridge.py:5115)
  → respond_to_negotiation (game_bridge.py:5248)
     → _book_fight_from_neg (game_bridge.py:5313)
        → assign_player_fight_to_card (game_bridge.py:7740)
           → _assign_card_slot (game_bridge.py:7104)
              → card_builder.assign_slot (card_builder.py:346)
        → fight["card_slot"] = slot   (game_bridge.py:7775)   ← only stamp
```

`_make_scheduled_fight` (`game_bridge.py:7424`) also stamps `card_slot`, but it's the **AI** path (`is_ai_fight: True` at line 7442, called only from card-building loops at 7383 and 7651). Not used for player fights.

## Recommended next-session fix for Finding 1

**Tighten the score formula at `card_builder.py:246–344` so a "credibility-style" check applies to score generation as well as to the rank-floor.** Two options to weigh:

- **Option A — score-side credibility check.** In `calculate_matchup_score`, accept `fighter1_wins/losses` and `fighter2_wins/losses` (already accepted today, see lines 254–257) and apply a hard cap when either fighter has `total_fights < TITLE_MIN_PRO_FIGHTS` (=3): cap total at e.g. 50 (sub-MAIN_CARD threshold). This keeps the formula intact for veteran matchups but stops rookie-vs-rookie or rookie-vs-vet from scoring into MAIN_EVENT/CO_MAIN purely on rank adjacency.
- **Option B — eligibility check upstream.** Pass `matchup_credible` (already computed in `_assign_card_slot`) into `card_builder.assign_slot` as a new param, and inside `_get_target_slot_by_score` cap the target at MAIN_CARD when `matchup_credible=False`. Smaller change to score logic, but adds a new param to a public-ish function.

Option A is more honest (the score itself was inflated). Option B is a tighter blast radius. Recommend A unless we see other consumers of `calculate_matchup_score` that should preserve the unrestricted formula.

**Critical files to modify:**
- `cage_dynasty_web/card_builder.py:246–344` — `calculate_matchup_score` formula
- (Option B only) `cage_dynasty_web/card_builder.py:346` — `assign_slot` signature + `_get_target_slot_by_score` call site
- (Option B only) `cage_dynasty_web/game_bridge.py:7104` — `_assign_card_slot` to pass new param

**Functions/utilities to reuse:** `is_title_eligible(wins, losses, rank, is_champion)` from `matchmaking.py:387` — already imported at `game_bridge.py:270` as `MATCHMAKING_AVAILABLE` gated. Same idiom used in tonight's fix.

## Filed for next session — Bug C: Champion booked to fight himself

**Symptom:** "Gustavo Moreira#C vs Gustavo Moreira#C" appearing on a DFC 10 preview after a title change.

**Root cause:** `game_bridge.py:7244–7252` — the AI title-fight contender selection iterates `division.rankings[:10]` looking for the first available candidate, **without filtering out the champion's own fighter_id**:

```python
champ_id = division.champion_id
champ = next((f for f in available if f.fighter_id == champ_id), None)
if champ:
    top = None
    for contender_id in division.rankings[:10]:
        candidate = next((f for f in available
                          if f.fighter_id == contender_id), None)
        if candidate:
            top = candidate          # ← no check that contender_id != champ_id
            break
```

If the champion's ID also appears in their own division's `rankings` list (which can happen post-title-change if rankings weren't pruned), the loop picks the champion as their own contender.

**Fix sketch (one-liner):** change line 7250 to `if candidate and candidate.fighter_id != champ_id:`.

**Worth verifying alongside:** does `division.rankings` always exclude the champion? If not, this is also worth a separate cleanup at the rankings-update path. The fix above is defense-in-depth either way.

## Filed for next session — Bug D: media.py `randrange(3, 2)` crash

**Symptom:** `⚠️ Media reactions failed: empty range in randrange(3, 2)` printed twice in the Flask terminal.

**Catch site:** `cage_dynasty_web/game_bridge.py:4217` — try/except around the media-reactions generation.

**Root cause:** `narrative/media.py:838` — `"{ko_num}": str(random.randint(3, wins))`. When the winner has `wins == 1`, `random.randint(3, 1)` calls `randrange(3, 2)` internally (since `randint(a, b)` is `randrange(a, b+1)`), which raises `ValueError: empty range in randrange(3, 2)`. Matches the error string exactly.

`wins` is sourced at line 830: `winner_data.get("wins", random.randint(5, 15))`. Default is fine; the bug fires when actual winner data has `wins < 3`. Also worth checking line 839 (`random.randint(2, max(2, wins // 2))` is *probably* safe due to `max(2, ...)`, but worth re-reading the surrounding token-substitution block for sibling crashes).

**Fix sketch:** wrap the bound: `random.randint(3, max(3, wins))`, OR pick from the smaller pool: `random.randint(min(3, wins), wins)`. Pick whichever matches the intended semantics — `ko_num` is "career KO count," so capping at the lower bound makes more sense for fighters with few wins. Don't fix without checking siblings at lines 837–846 for the same pattern.

## Verification (after either next-session fix)

For Finding 1 fix:
1. Restart Flask, start fresh game.
2. Confirm two 0-0 rookies (e.g. via the Strawweight initial roster) booked against each other land in `prelim` or `early_prelim` with 3 rounds — NOT co_main / main_event.
3. Confirm a legit title contender matchup (champion + #1, both with ≥3 fights) still lands in MAIN_EVENT with 5 rounds.
4. Spot-check `🥊 [AI SIGNING]` and 📊 [DFC N] terminal logs for slot distribution sanity.

For Bug C fix:
1. Use a save with a recent title change. Advance week and trigger AI card building.
2. Confirm DFC card lists champion vs a real contender (not themselves).

For Bug D fix:
1. Trigger a fight where the winner has `wins == 0` going into the bout (so `wins == 1` after). Watch terminal — no `⚠️ Media reactions failed` line.

## Memory entries to add (post-plan-mode)

When out of plan mode, add to `/Users/vandope/.claude/projects/-Users-vandope-Desktop-Games-cage-dynasty/memory/`:

- **Bug C** — `bug_champion_self_fight.md` (project type) — pointing at `game_bridge.py:7244–7252`.
- **Bug D** — `bug_media_randrange.md` (project type) — pointing at `narrative/media.py:838`.
- **Score-formula note** — `tech_note_score_promotes_slot.md` (project type) — recording that `calculate_matchup_score` independently promotes slot regardless of `matchup_credible` (the lesson from tonight). Useful so a future session doesn't repeat the same surprise.
