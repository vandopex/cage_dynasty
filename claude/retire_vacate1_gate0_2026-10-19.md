# RETIRE-VACATE1 — Gate 0 (2026-10-19)

READ-ONLY census. No code changes. Line numbers at HEAD f45dba9.

## 0. Anchor check

```
92bd7fa      601
873b2a8      603
281ec76      604
f45dba9      605
```

Prior handoff (deploy9 §1) asserted "CLAUDE.md 43.3 KB, 601 lines"; wc at
f45dba9 is 605. 4-line drift is from the three DOCS commits that followed
92bd7fa. Line-number anchors in handoffs before f45dba9 are stale; symbol
anchors stand.

## 1. Census — every write site that sets a fighter retired

Grep basis:
- `grep -rn "retired" cage_dynasty_web/ narrative/ --include="*.py"` (32 hits,
  mostly news / comments / variable names).
- `grep -rn "retire_fighter\|retire(" cage_dynasty_web/ narrative/ --include="*.py"`
- `grep -n "is_active = False\|is_active=False" cage_dynasty_web/game_bridge.py cage_dynasty_web/routes.py cage_dynasty_web/world_init.py`

Four write sites across two layers (bridge is live-play; world_init is
pre-gen). No `is_retired` field exists anywhere; retirement is encoded by
clearing `fighter.is_active` to False. Count is TWO live-play sites, not
one — the handoff "~11390" referenced one of them.

### Live-play site A — aging block (annual, non-player branch)
- **File:line**: `cage_dynasty_web/game_bridge.py:11371` inside
  `_advance_aging_week` (def at `:11263`); call chain
  `_advance_aging_week` → `AgingSystem.check_retirement` →
  `retiring.append((fighter, age+1))` at `:11368` →
  `fighter.is_active = False` at `:11371` inside the `for fighter, ret_age
  in retiring:` loop at `:11370`.
- **Triggering path**: `_advance_aging_week(week)` called every advance
  week; retire branch only fires when `week % 52 == 0` AND fighter age ≥
  35 AND `check_retirement` RNG hit AND fighter's `camp_id !=
  self._game_state.player_camp_id` (player-owned fighters divert to the
  prompt dict at `:11354`, not to `retiring`).
- **Held-belt check**: NONE. The branch at `:11343-11368` checks age,
  streak, is_champion (as a probability INPUT to check_retirement — reduces
  retire chance), total_fights, morale. `is_champion=True` reduces the
  probability but does not skip the retire. No branch anywhere in the
  loop asks "is this fighter a champion?" to vacate the belt.
- **What it does to (a) division champion**: NOTHING. The code at
  `:11370-11462` writes `fighter.is_active = False`, removes the fighter
  from the camp roster (`:11380-11388`), writes `_fighter_data[fid]
  ['is_active'] = False` (`:11389`), emits retirement news, calls
  `_update_rankings_after_fight(wc)` (`:11460`), and
  `_check_hof_on_retire(fighter)` (`:11462`). It does NOT touch
  `division.champion_id`, `division.champion_name`, or `fighter.is_champion`.
- **What it does to (b) `_belt_history`**: NOTHING. No
  `_belt_history.vacate_belt(…)` call, no `current_champions.pop(…)`, no
  mutation of the active reign's `lost_week` / `lost_event` / `lost_to` /
  `lost_method`. The reign stays `is_active=True` because `is_active` is
  a `@property` at `world_init.py:567` keyed on `lost_week is None`.

### Live-play site B — `/fighter/<id>/retirement-decision` POST (player branch)
- **File:line**: `cage_dynasty_web/routes.py:2747` inside the handler at
  `routes.py:2729` (`def retirement_decision(fighter_id)`), route decorator
  at `:2727`. Branch `if decision == 'retire':` at `:2745`.
- **Triggering path**: Form POST with `decision=retire`. The handler reads
  `bridge._pending_retirement_prompts.pop(fighter_id, None)`; the prompt
  is only populated by Site A's player-branch at `game_bridge.py:11354`
  (previous annual tick marked this player fighter for retirement). So
  the only way this fires is: annual aging tick → player fighter
  flagged → dashboard decision card → player clicks "Retire".
- **Held-belt check**: NONE. Branch does not read `fighter.is_champion`
  or `division.champion_id`; no belt-related gate.
- **What it does to (a) division champion**: NOTHING. Writes
  `fighter.is_active = False` at `:2747`, prunes camp roster at
  `:2749-2755`, writes `_fighter_data[fid]['is_active'] = False` at
  `:2756-2758`, inserts a retirement news entry, calls
  `bridge._check_hof_on_retire(fighter)` at `:2769`. No touch of
  `division.champion_id` / `champion_name` / `fighter.is_champion`.
- **What it does to (b) `_belt_history`**: NOTHING. No vacate_belt call.

### Pre-gen site — `_retire_fighter` (world_init HistorySimulator)
- **File:line**: `cage_dynasty_web/world_init.py:3117-3137` (def), callers
  at `:3084` (annual age-check during pre-gen) and `:3113` (post-fight
  lose-streak retirement).
- **Triggering path**: Pre-gen only. Runs during `WorldInitializer.run()`
  on new_game.
- **Held-belt check**: YES — `if fighter.is_champion:` at `:3125`.
- **What it does to (a) division champion**: `fighter.is_champion = False`
  at `:3127`; `self.title_holders.pop(wc, None)` at `:3129`;
  `self.vacant_divisions.add(wc)` at `:3135`. (`title_holders` is the
  HistorySimulator's own dict; `division.champion_id` in `_game_state` is
  populated separately post-sim via `_crown_initial_champion` in
  `game_state.py:901`.)
- **What it does to (b) `_belt_history`**: `self.belt_history.vacate_belt(
  weight_class=wc, week=current_week, event_name=reason, reason="Retired")`
  at `:3130-3135`. **This is the one retire path on HEAD that does call
  `vacate_belt` — but it is pre-gen only; it never fires in live play.**

### Not a fighter-retire site — amateur promotion
- `cage_dynasty_web/amateur.py:1856-1884` returns a list of
  `fighter.fighter_id` and sets `fighter.is_active = False` inside the
  amateur system for amateurs turning pro / dropping out. Not a career
  retirement; distinct state machine. Flagged to rule out of the census.

## 2. `vacate_belt` — signature, callers, buckets

- **Signature + file:line**:
  ```
  world_init.py:684
  def vacate_belt(self, weight_class: str, week: int, event_name: str,
                  reason: str = "Retired") -> None:
  ```
- **Body (`:684-694`)** writes to the current reign's `lost_week`,
  `lost_event`, `lost_to=None`, `lost_to_name=None`, `lost_method=reason`,
  then `self.current_champions.pop(weight_class, None)`.
- **Callers** (`grep -n "vacate_belt" cage_dynasty_web/`):
  - `world_init.py:3130` — `_retire_fighter`, `reason="Retired"` (pre-gen).
  - `game_bridge.py:4051` — injury-vacate, `reason="Vacated (injury)"`.
  - `game_bridge.py:6929` — player-choice vacate, `reason="Vacated (player
    choice)"`.
  - `game_bridge.py:21370` — weight-move vacate, `reason="Vacated (weight
    move)"`.
- **lost_method bucket strings currently reachable**:
  - `"Retired"` (pre-gen only).
  - `"Vacated (injury)"`
  - `"Vacated (player choice)"`
  - `"Vacated (weight move)"`
- **Retirement bucket in live play**: NONE. The pre-gen path uses
  `"Retired"`; no live-play caller passes it, and neither live-play
  retire site (`game_bridge.py:11371`, `routes.py:2747`) calls
  `vacate_belt` at all.

## 3. Reader grep

### (a) Readers of `fighter.is_active`
51 hits in `game_bridge.py` + 1 in `world_init.py` + 1 in `routes.py`.
Representative load-bearing readers for the retire question:

- `game_bridge.py:14448` (`_get_ladder_data`): `if champ_rec and
  champ_rec.is_active: champion_web = _convert_real_fighter(champ_rec)` —
  **retired champion silently drops from ladder's champion slot**;
  `champion_web = None`, template renders blank.
- `game_bridge.py:16925` (`_build_card_for_week` title-fight booking):
  `if not champ or not champ.is_active: continue` — **title fight for
  that division is never queued post-retire**; `division.champion_id`
  still points at retired fighter but availability check vetoes the
  booking. Belt sits open indefinitely.
- `game_bridge.py:11281` (aging loop pre-filter): `if not
  fighter.is_active: continue` — once retired, aging is a no-op.
- `game_bridge.py:14741` (roster): `active = [f for f in fighters if
  f.is_active]` — retired fighter drops out of roster view.
- Rankings: `_update_rankings_after_fight(wc)` called at `:11460` after
  retire prunes the fighter from `division.rankings` immediately.

### (b) Readers of `_belt_history` lost_event / lost_method / lost_to
- `game_bridge.py:9571-9586` (`get_fighter_reigns`): copies
  `r.lost_week`, `r.lost_event`, `r.lost_event_number` (via
  `_event_number_from_name(r.lost_event)`), `r.lost_to`, `r.lost_to_name`,
  `r.lost_method`, `r.is_active` into the dict the template consumes.
  **On a retired champion with the live-play paths on HEAD, every lost_*
  field is None; is_active=True.**
- `templates/fighter_profile.html:893, 911, 913, 921, 922`: reign card
  branch is `{% if reign.is_active %} … Current champion … {% elif
  reign.lost_to_name %} … Lost to … {% else %} … Vacated {% endif %}`.
  **With is_active=True (lost_week=None) the FIRST branch fires: "Current
  champion" on a retired fighter's profile.** The `· Vacated` branch is
  only reachable when is_active is False AND lost_to_name is None (the
  three live vacate buckets' shape).
- `templates/fighter_profile.html:1216` (🛡️ window predicate): `{% set
  _r_lost_en = r.get('lost_event_number') %}` → None →
  `(_r_lost_en is none or _fight_en < _r_lost_en)` → **window never
  closes** for a retired champion. No post-retire fights means no false
  🛡️ marks today, but the window is open-ended if any synthetic row ever
  shows up with an event_number > won_event_number.
- `templates/champions.html:85, 90, 104, 105`: reign card prints "CURRENT"
  badge on `is_active=True` and only prints "Lost to … via lost_method"
  when `not is_active and lost_to_name`. **Retired champion's reign
  renders with CURRENT badge; no vacate line.**

### (c) Readers of division champion
- `game_bridge.py:14446, 14448` (ladder): reads `division.champion_id`,
  dereferences `_game_state.get_fighter(champ_id)`, filters on
  `is_active`. Retired champ: `champ_id` still set, record exists but
  inactive → `champion_web=None`.
- `game_bridge.py:16922-16938` (`_build_card_for_week`): same pattern —
  `champ_id = division.champion_id` → `is_active` check → skip. No
  booking.
- `game_bridge.py:6192-6220, 6279`: various champion lookups that only
  dereference `division.champion_id` without an `is_active` filter will
  return the retired record; whether that's a bug depends on each site
  (e.g. `:6279` compares `division.champion_id == fighter.fighter_id` to
  gate a flag; retired champ matches → flag set).
- `_belt_history.current_champions.get(weight_class)` at
  `world_init.py:696-698`: NO live-play reader found via grep —
  live-play readers go through `get_fighter_reigns` and
  `_get_title_records`, which iterate `reigns`, not `current_champions`.
  The dict holds the retired fighter_id as a stale mapping; no observable
  effect on current readers.

### Record Book / HOF readers (both consume reigns, is_active-agnostic)
- `game_bridge.py:15089 _get_title_records`: iterates
  `self._belt_history.reigns.values()`, counts reigns and sums
  `successful_defenses`. **Retired champion's reign still counts as a
  reign; defense total unchanged. Record Book "Most Title Reigns" /
  "Most Defenses" show the retired champ exactly as if they were still
  active.**
- `game_bridge.py:4376 _compute_hof_score`: `len(_reigns)` and
  `sum(r.successful_defenses for r in _reigns)`. Reign count unaffected
  by `is_active`. **HOF score includes the open reign at 25 pts.**
- `_check_hof_on_retire` at `game_bridge.py:4460` fires on both live
  retire sites; the HOF score for the retiring champion is computed with
  the open reign intact.

## 4. Measurement path options

Three options to force a sitting-champion retire on HEAD under a harness.
Not building any of them in this Gate 0.

### Option A — direct call into aging block
- **Mechanism**: Build bridge via `save_invariants`-style `_harness_env`
  (or dev1 harness). After `new_game`, pick any non-player champion,
  override `fighter.age = 55` and `fighter.morale = 1`, then call
  `bridge._advance_aging_week(week=52)`.
- **What it needs**: `AGING_AVAILABLE=True` on the harness (check
  `game_bridge.py:389,395`); the HARNESS-ENV1 note in deploy9 handoff §3
  warns that `save_invariants` currently prints a SIMULATION-SHIM FAILED
  line, so verify aging actually loads before relying on this. The retire
  branch gates on `fighter.camp_id != player_camp_id`, so pick a champion
  whose camp isn't the player's.
- **Advantages**: Exercises the entire retire path including HOF, news,
  camp pruning, ranking removal. Representative.
- **Risks**: `check_retirement` is RNG; set age high enough (≥45 →
  base_prob=0.8) + morale low to guarantee ≥1.0 effective probability.
  Still a stochastic gate; may need a seeded random.

### Option B — Flask test client POST `/retirement-decision`
- **Mechanism**: Build bridge; crown a PLAYER-owned fighter as champion
  (or pick an existing player champion); inject
  `bridge._pending_retirement_prompts[fid] = {...}` directly to simulate
  "aging already queued"; `Flask.test_client().post('/fighter/{fid}/
  retirement-decision', data={'decision': 'retire'})`.
- **What it needs**: Session binding (route uses `get_bridge()`); player
  camp containing a champion; the pending-prompt dict seeded by hand.
- **Advantages**: Exercises the exact code path a human player hits.
- **Risks**: Needs a session fixture; player retire is the branch least
  likely to touch champion state (same silent-fail as A).

### Option C — minimal retire helper
- **Mechanism**: Build bridge; pick a champion; manually run just the
  write subset: `fighter.is_active = False`;
  `_update_rankings_after_fight(wc)`; `_check_hof_on_retire(fighter)`.
- **What it needs**: Nothing beyond a built bridge.
- **Advantages**: Deterministic, no RNG, fast.
- **Risks**: Skips the aging block's camp pruning and the player-branch
  prompt dict — not representative of the paths users hit. Useful only
  for the belt / division-champion side of the question, which is what
  Gate 0 is actually about.

**Recommended for probe v4**: Option C for the belt + division
observation (fast, deterministic); Option A as a representativeness
check once the fix lands.

## 5. Predicted pre-state on HEAD (prediction, not measurement)

For a sitting champion who retires via Site A (aging) or Site B
(/retirement-decision), with no other mutations:

- `fighter.is_active` → False (both sites write it).
- `fighter.is_champion` → **True (unchanged)**. Neither live-play site
  clears it.
- `division.champion_id` / `division.champion_name` → **unchanged, still
  point at the retired fighter**. Ladder's `_get_ladder_data` sees
  `is_active=False` and renders `champion_web=None`; matchmaking's
  `_build_card_for_week` sees the same and skips the title fight. Belt
  sits open indefinitely with no vacant-title booking queued.
- `_belt_history.reigns[wc][-1]`:
  - `lost_week` = None → `is_active` property returns True.
  - `lost_event` = None.
  - `lost_to` = None.
  - `lost_to_name` = None.
  - `lost_method` = None.
- `_belt_history.current_champions[wc]` → **stale, still mapped to the
  retired fighter_id**. No live reader on HEAD observes this via
  `get_current_champion`, so no visible symptom through that door.
- `_get_title_records`: counts the open reign (reigns += 1, defenses
  unchanged). Retired champion still appears on "Most Title Reigns" /
  "Most Defenses" exactly as before.
- `_compute_hof_score`: counts the open reign at `title_count * 25` and
  defenses at `def_count * 10`. HOF-on-retire fires with the open-reign
  score intact; whether the fighter crosses `HOF_THRESHOLD` is unchanged
  from "the second before they retired".

Rendered surfaces:
- **fighter_profile.html reign card** (`:893, 911`): is_active=True →
  gold border + "Current champion" line. No `· Vacated` line, no "Lost
  to" line.
- **fighter_profile.html top-of-page CHAMPION badge** (`:167`): fighter.
  is_champion=True → badge still rendered on the retired fighter's
  profile.
- **fighter_profile.html 🛡️ window** (`:1216`): `_r_lost_en=None` →
  window stays open. No in-window live fights post-retire (fighter is
  inactive), so no false 🛡️ marks today. Any synthetic row post-retire
  would be marked.
- **champions.html belt lineage** (`:85, 90, 104`): reign is_active=True
  → "CURRENT" badge; `champion_name` = retired fighter; no "Lost to … via
  lost_method" line.
- **Record Book "Most Title Reigns" / "Most Defenses"**: retired champ
  included; counts unchanged from active state.
- **Ladder for the division**: champion slot blank (`champion_web=None`);
  rankings exclude retired fighter (pruned by
  `_update_rankings_after_fight`).

Same ghost-reign class as the three VACATED-REIGN1 pre-fix cases, with
one extra edge: `fighter.is_champion` is also not cleared (the three
VACATED-REIGN1 sites all cleared it). So the retire-ghost is strictly
worse-shaped than the pre-fix vacate-ghost for the retired fighter's own
profile badge.
