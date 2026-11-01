# RETIRE-VACATE1 — Gate 3 (2026-10-23)

Engine tier. Rulings carried: scope (b) small vacate helper called
from both sites, unify later (gate2 §2); bucket `"Vacated
(retirement)"`.

## 0. Baseline

```
0dff271 DOCS: RETIRE-VACATE1 backlog + index, missed from d9005dc. …
d9005dc DOCS: RETIRE-VACATE1 Gate 0–2 filings …
f45dba9 DOCS: handoff_post_deploy9 …
```

`git diff --stat f45dba9..HEAD -- cage_dynasty_web/ narrative/` is empty
(both intermediate commits are docs-only). g2 JSON is a valid
pre-state measurement for this fix.

Site 2 pattern copied from `cage_dynasty_web/game_bridge.py:6916-6945`:
`ftr.is_champion = False` → `div.champion_id = None` → `div.champion_name =
None` → `self._belt_history.vacate_belt(wc, week=W, event_name=
self._dfc_label(W), reason="Vacated (player choice)")` → title-category
news insert → `_book_title_fight(wc, exclude_ids={fighter_id})`. No
`_fighter_data` or `_champ_weeks_since_defense` write at site 2;
helper mirrors exactly that (gate 2 §3 agreement table was the input).

## 1. Helper + call sites

Helper `_vacate_on_retire(self, fighter, week)` inserted next to the
existing player-choice vacate (end of `resolve_champion_injury_decision`
at `game_bridge.py:6959+`). Signature `-> Optional[str]`.

Behavior:
- `return None` if `self._game_state` is None.
- Scan `self._game_state.divisions.items()` for a division whose
  `champion_id == fighter.fighter_id`. If none → `return None`.
- Otherwise site 2's order verbatim; bucket `"Vacated (retirement)"`.
- Resolves to `self._game_state.fighters[fid]` for the `is_champion =
  False` write to work when the caller passes a WebFighter copy
  (routes.py path — see gate 3d note below). Fallback to the passed
  object if the registry lookup misses.
- Returns `wc` on hit.

Call sites, both immediately after `fighter.is_active = False` and
before `_check_hof_on_retire`:

- Site A — `cage_dynasty_web/game_bridge.py:11417` (aging-block retire
  loop):  `self._vacate_on_retire(fighter, week)`
- Site B — `cage_dynasty_web/routes.py:2748` (`/retirement-decision`
  'retire' branch):  `bridge._vacate_on_retire(fighter, bridge._game_state.week_number)`

Diffstat:
```
 cage_dynasty_web/game_bridge.py | 47 +++++++++++++++++++++++++++++++++++++++++
 cage_dynasty_web/routes.py      |  1 +
 2 files changed, 48 insertions(+)
```

## 2. Gates

### 3a — py_compile

```
game_bridge py_compile ok
routes py_compile ok
```

### 3b — probe v4 g3 (RNG missed; rerun g3b fired)

Same seed (20260921), same probe, no probe edits. First run g3
`check_retirement` rolled below threshold (per CLAUDE.md "SAME SEED
MEASUREMENTS HAVE NEVER BEEN REPRODUCIBLE" — uuid4 reshuffles the
world per process so even with `random.seed(20260921)` the trajectory
through 51 weeks to the retire check differs). g3b fired on advance #1
(wk 52) and gave clean post-state:

Picked: Ricardo Werdum (`3282374f`), Strawweight sitting champion,
founder reign (won_week=0, "Cage Dynasty Founding — Strawweight
Championship", "Inaugural Crown"), 5 defenses, 6-0 record.

Post-fire snapshot vs Gate 0 §5 inverted expectations:

| Field | Gate 0 §5 inverted (fix target) | g3b observed | ✓/✗ |
|---|---|---|---|
| `fighter.is_active` | False | False | ✓ |
| `fighter.is_champion` | False (cleared by helper) | False | ✓ |
| `division.champion_id` | None | None | ✓ |
| `division.champion_name` | None | None | ✓ |
| `reign.lost_week` | retire week = 52 | 52 | ✓ |
| `reign.lost_event` | `_dfc_label(52)` → parses to int | `"Cage Dynasty 95"` | ✓ |
| `reign.lost_event_number` | 95 (parsed) | 95 | ✓ |
| `reign.lost_method` | `"Vacated (retirement)"` | `"Vacated (retirement)"` | ✓ |
| `reign.lost_to` | None | None | ✓ |
| `reign.lost_to_name` | None | None | ✓ |
| `reign.is_active` | False | False | ✓ |
| `_belt_history.current_champions[wc]` | absent / None | None | ✓ |
| title-cat news for that wc at that week | 1 new row | fires in-helper (unverified in g3b dump; verified in 3d(ii) delta=1) | ✓ |
| `_book_title_fight` called | yes | fires; "⚠️ [VACANT TITLE] Strawweight — no bookable contender; deferred" stdout line proves call | ✓ |

`post_plus_one` (one further `advance_week`): byte-identical to
`post_immediate` on every reign/division/current_champions field —
state settles.

### g3b pre → g3b post (same run)

The valid before/after is within g3b: `pre` snapshot captured at wk
51 right before `age=50 / morale=1` applied and advance fired; `post_
immediate` captured right after the annual tick retired Werdum.

| Field | g3b pre | g3b post | fix target met? |
|---|---|---|---|
| `fighter.is_active` | True | False | ✓ |
| `fighter.is_champion` | True | False | ✓ |
| `division.division_champion_id` | `3282374f` | None | ✓ |
| `division.division_champion_name` | `"Ricardo Werdum"` | None | ✓ |
| `division.active_reigns_bh` | 1 | 0 | ✓ |
| `division.in_current_champions` | True | False | ✓ |
| `division.current_champions_value` | `3282374f` | None | ✓ |
| `division.last_reign_bh.is_active` | True | False | ✓ |
| `division.last_reign_bh.lost_week` | None | 52 | ✓ |
| `division.last_reign_bh.lost_event` | None | `"Cage Dynasty 95"` | ✓ |
| `division.last_reign_bh.lost_event_number` | None | 95 | ✓ |
| `division.last_reign_bh.lost_method` | None | `"Vacated (retirement)"` | ✓ |
| `division.last_reign_bh.lost_to` | None | None | ✓ (vacate, not transfer) |
| `division.last_reign_bh.lost_to_name` | None | None | ✓ |
| `division.last_reign_bh.champion_id` | `3282374f` | `3282374f` (same reign closed) | ✓ |
| `division.last_reign_bh.won_week` | 0 | 0 | ✓ (unchanged) |
| `division.last_reign_bh.won_event` | `"Cage Dynasty Founding — Strawweight Championship"` | same | ✓ |
| `division.last_reign_bh.won_method` | `"Inaugural Crown"` | same | ✓ |
| `division.last_reign_bh.successful_defenses` | 5 | 5 | ✓ (unchanged) |

### pre-fix ghost shape (different world, same seed)

Comparison against g2 (same `random.seed(20260921)`, different
process → different world):

- g2 picked Lyoto Nascimento (`a906d975`), Strawweight successor at
  wk 23 (won from Werdum via TKO at Cage Dynasty 76, 1 defense).
- g3b picked Ricardo Werdum (`3282374f`), Strawweight founder at wk
  0, 5 defenses.

Both are valid sitting-champion-at-wk-51 selections; the two worlds
differ because `uuid.uuid4()` is unseeded (CLAUDE.md top-of-file
SAME SEED notice), so every ID reshuffles per process and
matchmaking/sort/set-iteration cascades diverge.

g2 served as the pre-fix measurement (gate 1b §6c measured the
ghost shape); g3b is the post-fix measurement. The within-run g3b
pre→post table above is the before/after for THIS fix. The
cross-run g2→g3b comparison is secondary: it shows the ghost shape
measured on an older world is identical in structure to the ghost
the fix would have left on g3b's world had the fix not been in
place (every `lost_*` field None, division.champion_id stale,
is_champion True on the retired fighter).

### Finding — live sim not seed-reproducible across processes (measured)

`g2` and `g3b` were run with identical `random.seed(20260921)`, same
probe code, same 51-week advance trajectory from new_game. They
diverged at week 23: g2's Werdum lost the Strawweight belt to Lyoto
Nascimento at wk 23 CD76; g3b's Werdum successfully defended through
all 5 defenses and still held the belt at wk 51. Different worlds,
same seed. The divergence is attributable to `uuid.uuid4()` being
unseeded (`os.urandom` per CLAUDE.md), which reshuffles every
fighter_id per process and changes downstream dict-key-lookup
ordering, matchmaker sort tie-breakers, and the random.random()
consumption trajectory through 51 weeks. Measured here, consistent
with CLAUDE.md's standing SAME SEED notice.

### 3c — Discrimination: non-champion retire

Side probe `retire_probe_v4_discrim.py` (untracked) loads the g2
autosave as a zero-cost fixture, picks a non-champion active fighter,
calls `bridge._vacate_on_retire(fighter, week=50)`:

```
PICK: Lyoto Lima (fb7d873f) wc=Strawweight is_champion=False
  _vacate_on_retire return = None
  divisions changed:       0
  _news_items length delta: 0
  title-cat news delta:     0
  3c PASS: True
```

Return `None`, zero divisions altered (loop over all 9), zero news
rows added, zero title news added. A fix that touched any division's
belt state would fail here.

### 3d — Flask test client /retirement-decision

Load g2 save → fresh user_id → `app.game_bridges[test_uid]` →
`test_client().post(url, data={'decision': 'retire'})` → inspect state.

**3d(i) — non-champion player retire:**

Picked Alex Hernandez (the player fighter, non-champion). Seeded
`_pending_retirement_prompts` by hand, POSTed.

```
3d(i) POST status: 302
  registry is_active after: True (pre-existing routes.py bug, not RV1)
  title-news delta: 0
  divs changed: []
  3d(i) RETIRE-VACATE1 scope PASS: True
```

My helper fires but finds no division where `champion_id == fid`,
returns None, no state change. The `registry is_active` staying True
is a **pre-existing routes.py bug** (filed below in §4) outside
RETIRE-VACATE1 scope.

**3d(ii) — player champion crowned via `_record_title_result`, then retire:**

No natural player champion in the save (every player fighter is
unranked at wk 50). Crowned Alex Hernandez via the live-pipeline
method `_record_title_result(weight_class='Strawweight', winner=alex,
loser=current_strawweight_champ, method='TKO', rnd=3,
event_name=_dfc_label(50), week=50)` — that path writes `old_champ.
is_champion=False`, `winner.is_champion=True`, `division.champion_id =
winner.fighter_id`, `division.champion_name = winner.name`, and calls
`BeltHistory.title_changes_hands(...)`. The crowning fired cleanly
("🏆 [TITLE CHANGE] Alex Hernandez wins Strawweight belt from Lyoto
Nascimento via TKO R3 at Cage Dynasty 94"). Then seeded the retire
prompt, POSTed:

```
3d(ii) POST status: 302
  registry is_active after: True (pre-existing routes.py bug, not RV1)
  is_champion after:      False
  division.champion_id:   None
  reign.lost_week:        50
  reign.lost_method:      Vacated (retirement)
  reign.lost_to:          None
  reign.is_active:        False
  title-news delta:       1
  3d(ii) RETIRE-VACATE1 scope PASS: True
```

Every RETIRE-VACATE1-scoped field matches target. Reign closed with
`lost_week=50`, `lost_method="Vacated (retirement)"`, `lost_to=None`,
`is_active=False`. Division cleared. One new title-category news row
emitted. `_book_title_fight(wc, exclude_ids={fid})` fired (stdout
"⚠️ [VACANT TITLE] Strawweight — no bookable contender; deferred" —
means the booking call ran).

### 3e — Save round-trip

Loaded g2 → picked sitting champion Lyoto Nascimento (Strawweight) →
set `is_active=False` by hand → called `_vacate_on_retire(fighter,
week=50)` directly → `web_save("autosave")` to new slot
`retire_probe_discrim_3e` → fresh `GameBridge` → `web_load("autosave")`
→ snapshot division + reign.

```
PICK: Lyoto Nascimento (a906d975) wc=Strawweight
  _vacate_on_retire return = 'Strawweight'
  web_save: success=True
  web_load fresh bridge: success=True
  in-memory post == post-reload: True
  3e PASS: True
```

`post_in_memory == post_after_reload` byte-for-byte on the reign dict
and division fields. The vacate state round-trips through save/load
without corruption.

### 3f — save_invariants smoke, --weeks 12

```
=== SAVE-INVARIANTS1 — mode=seed ===
    seed=20260921 weeks=12
    fighters=286  fighter_data=286
...
R01  wins_by_method_sum_matches_record                   PASS    (violations: 0)
R02  streak_le_wins                                      PASS    (violations: 0)
R03  defense_marker_requires_belt_at_fight_time          PASS    (violations: 0)
R04  founding_row_iff_inaugural                          PASS    (violations: 0)
R05  reign_lineage_chains_no_gaps                        FAIL    (violations: 6; ex: Strawweight: reign[0].lost_to=82a06f69 != reign[1].champion_id=6224c3af)
R06  min_gap_between_fights                              PASS    (violations: 0)
R07  ko_suspension_window                                SKIP    …
R08  age_stage_matches_career_arc                        SKIP    …
R09  badges_equal_predicates                             INFO    …
R10  power_present_and_not_50_fallback                   PASS    (violations: 0; ex: player_powers=[56])
R11  height_reach_nationality_variance                   SKIP    …
R12  at_signing_populated_for_post_capture               PASS    (violations: 0)
R13  stat_surface_renders_all_19_stats                   PASS    (violations: 0)
R14  streak_bounds_a_active_le_wins_b_longest_le_wins_c_active_le_longest PASS    (violations: 0)
T-4 event_number None census: {'fight_history_total': 1767, 'event_number_none': 0, …}
=== FAILURES: 1 ===
```

R05 is the LINEAGE1 pre-existing comparator artifact (filed in
backlog.md, inherited from HARNESS-ENV1 / cross-axis sort). Nothing
new introduced by this fix. T-4 census is 0 None entries. All 12
non-R05 rules PASS or SKIP for pre-existing reasons.

**HARNESS-ENV1 flag**: this run under `claude/tools/save_invariants.py`
tripped the SIMULATION-SHIM failure that handoff deploy9 §3 noted —
"[SIMULATION-SHIM] FAILED to shim simulation.fight_engine …
world_init.FULL_ENGINE_AVAILABLE will be False." Pre-gen fell back to
`simulate_fight_simple` for this smoke, which caps favorite win rate
~74%. The rule results above still stand (invariant checks are
engine-agnostic), but the "286 fighters, 1767 history entries" means
this was the fallback pre-gen path, not the full engine. Flagged for
provenance; HARNESS-ENV1 is open backlog, not Gate 3 scope.

## 3. Findings

### Pre-existing bug — routes.py `fighter.is_active = False` writes to WebFighter, not registry

`cage_dynasty_web/routes.py:2746` does `fighter = bridge.get_fighter(
fighter_id)` which returns a `WebFighter` instance (a converted,
derivative object; see `game_bridge.py:6098-6117` in `get_fighter`
body — it calls `_convert_real_fighter` and caches a WebFighter).
The subsequent `fighter.is_active = False` at `:2747` mutates the
WebFighter copy — not the `_game_state.fighters[fid]` FighterRecord
in the registry. The `_fighter_data[fid]['is_active'] = False` write
at `:2758` touches the auxiliary dict only. **The registry
FighterRecord's `is_active` stays True after the route completes.**

Readers like `_build_card_for_week` at `:16925` filter on
`champ.is_active` where `champ` is a FighterRecord obtained via
`_game_state.get_fighter(id)` — those readers see the retired player
as still-active. The route's intended effect is partially realized:
the WebFighter copy stops being usable (short-lived), and some
downstream displays may read `_fighter_data[fid]['is_active']` and
see False. But the matchmaker's primary gate reads the FighterRecord
flag, which is unchanged.

Gate 3 scope does not fix this. Filed in backlog under
RETIRE-PATH-UNIFY1 (gate 2 §2 companion). The 3d sub-tests had their
pass criteria rewritten to RETIRE-VACATE1 scope only, with an
explicit note of the pre-existing bug.

My helper now resolves the fighter back to the registry record
internally for its own `is_champion = False` write so the vacate side
of the fix doesn't inherit the same bug — the write persists on
registry.

### SAME SEED non-reproducibility — probe v4 is a probability gate

The g3 (first) and g3b (second) runs used identical `random.seed(
20260921)` but produced different worlds (uuid4 is unseeded per
CLAUDE.md). g3 picked Francis Saint Denis as the Strawweight champion
at wk 51 and `check_retirement` rolled below threshold; g3b picked
Ricardo Werdum and rolled a hit. Both runs are valid; the probe is
honest about the stochastic gate. The fix's correctness is tested by
the hit-path only; a miss returns `fighter.is_active=True` and the
probe STOPs by design.

## 4. Diff vs HEAD f45dba9

```
 cage_dynasty_web/game_bridge.py | 47 +++++++++++++++++++++++++++++++++++++++++
 cage_dynasty_web/routes.py      |  1 +
 2 files changed, 48 insertions(+)
```

Full inline diff in Van's workspace (`git diff cage_dynasty_web/`).

## 5. Draft commit message

```
RETIRE-VACATE1: live retirement vacates the belt. Site A (aging-block
non-player branch, game_bridge.py:11417) and Site B (/retirement-
decision 'retire' branch, routes.py:2748) each call a new helper
GameBridge._vacate_on_retire(fighter, week) immediately after
fighter.is_active = False, before _check_hof_on_retire.

Cause: on HEAD f45dba9, both live retire sites wrote
fighter.is_active=False and nothing to _belt_history (claude/
retire_vacate1_gate0_2026-10-19.md §1). A sitting champion who
retired left is_champion=True, division.champion_id pointing at the
retired fid, the _belt_history reign open with every lost_* field
None, current_champions[wc] stale, and no vacant-title fight queued
— measured ghost shape in gate1 §6c (seed 20260921, Strawweight Lyoto
Nascimento retire at wk 52, every row confirmed).

Fix shape (ruling: scope (b) small helper, unify later): one 36-line
helper mirrors the player-choice vacate at :6922-6937 (gate2 §3
agreement table) in its order: is_champion → champion_id →
champion_name → _belt_history.vacate_belt → title news →
_book_title_fight. Bucket "Vacated (retirement)". event_name=
_dfc_label(week) so lost_event_number parses (gate1 §4). Ex-champion
case leaves _belt_history untouched (helper returns None when no
division has that fid as champion_id).

Call sites both place the call at the first write slot after
is_active=False. Helper resolves fighter back to the registry
FighterRecord for its is_champion clear so Site B's WebFighter
caller works (pre-existing routes.py write-path bug filed under
RETIRE-PATH-UNIFY1).

Gates (claude/retire_vacate1_gate3_2026-10-23.md):
- 3a py_compile both files
- 3b probe v4 g3b (seed 20260921, sitting champion wk 52): fighter.
  is_champion False, division.champion_id/name None, reign lost_week
  52 lost_event "Cage Dynasty 95" lost_event_number 95 lost_method
  "Vacated (retirement)" lost_to None is_active False;
  current_champions[wc] None; title news fires; _book_title_fight
  called ("deferred: no bookable contender")
- 3c non-champion retire via helper: return None, zero divisions
  altered, zero news added
- 3d(i) Flask POST non-champion player: no belt effect
- 3d(ii) Flask POST player crowned via _record_title_result: full
  vacate state matches 3b
- 3e save → load: byte-identical reign + division
- 3f save_invariants --weeks 12: 1 FAIL (R05 LINEAGE1 pre-existing),
  12 PASS/SKIP/INFO; nothing new

Forward-only: pre-fix saves keep their ghost reigns per the
VACATED-REIGN1 2026-10-17 pattern.
```

## §7 — AGING-AGE1 (measured 2026-10-29, g2 autosave, one world)

Gate 3 §1 established that the aging block reads
`getattr(fighter, 'age', 25)` and `getattr(fighter, 'morale', 50)`
directly off the FighterRecord with defaults 25 and 50. The probe's
`setattr(picked_f, 'age', 50)` + `setattr(picked_f, 'morale', 1)`
writes to those same attributes, and the retire branch received
exactly those values. **In the probe. Under the harness. With the
override.**

Census of the g2 autosave (`cage_dynasty_web/saves/bridge_retire_probe_g2_autosave.json`,
loaded fresh into a GameBridge, `gs.fighters.values()`):

```
total                : 290
hasattr(f,'age')     : 0
age not None         : 0
hasattr(f,'morale')  : 0
morale not None      : 0

_fighter_data['age'] not None: 290 / 290
sample _fighter_data keys  : ['age', 'body_frame', 'boxing', 'cardio',
    'career_control_time', …, 'style']
```

**Zero of 290 FighterRecords carry an `age` attribute. Zero carry
`morale`.** Age is stored exclusively on `_fighter_data[fid]['age']`
(the auxiliary dict; written at `game_state.py:773` during
`_create_fighter` with `random.randint(21, 35)`). The FighterRecord
dataclass (`game_state.py:90-…`) has no `age` or `morale` field; the
`fighter.age = age + 1` write at `game_bridge.py:11359` is guarded by
`if hasattr(fighter, 'age')` which is always False → never writes.

Consequence for the production retire path:
- `_advance_aging_week:11330`: `age = getattr(fighter, 'age', 25)` →
  **returns 25 for every fighter in production**.
- `_advance_aging_week:11331`: `if age < 33: continue` → **triggers
  for every fighter**. The loop body never reaches `check_retirement`.
- `process_birthday`'s `calculate_physical_decline(age)` / `calculate_
  mental_decline(age)` / `calculate_chin_decline(age, ko_losses)` all
  compute `calculate_years_past_prime(age=25)` → 0 (or negative) →
  **zero decline for every fighter**.
- Player-fighter retire prompt (`:11354`) never populates
  `_pending_retirement_prompts`, so Site B's `/retirement-decision`
  retire branch is unreachable too.

**The entire aging + retire system is dead in production.** Nominally
wired, functionally inert. The retire-ghost shape measured in gate1
§6c and the fix shipped in e459701 are forward-insurance against a
world where the aging system is wired correctly — which it isn't
today.

Decline function reads (callers in `_advance_aging_week`): the aging
system takes `age` as a parameter, not reaching back into fighter_data
itself, so the fix is at `_advance_aging_week`'s `getattr` call —
either (a) the write side (set `fighter.age` on FighterRecord during
`_create_fighter`), (b) the read side (read from `_fighter_data[fid]
['age']`), or (c) both. Design call; forward-only; filed as AGING-AGE1
in backlog.

Scope: one world (g2 autosave, seed 20260921). Not generalized across
seeds — but the write-site reading at `game_state.py:773` and
FighterRecord's dataclass definition at `game_state.py:90` are
universal; no world-specific state could produce the attribute.
Expected to hold on all worlds; one-world census stands as sufficient
measurement to file.

RETIRE-VACATE1 e459701 remains correct under the fix's own test
(gate3 §3b + §3d measured both work when the retire path fires). The
PA-impact assessment reads: **no observable change on PA until
AGING-AGE1 ships**, because no non-player retire fires in live play
today and Site B's prompts never surface.
