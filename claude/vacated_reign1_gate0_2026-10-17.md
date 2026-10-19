# VACATED-REIGN1 Gate 0 (2026-10-17)

Base commit: f091db9. Read-only against the engine; no edits to engine files.
Census teed to `outputs/vacated_reign1/gate0_2026-10-17.txt`
(and `gate0b_2026-10-17.txt`).

## 1. Live retirement — does the belt get vacated?

Two live code paths retire a fighter. **Neither vacates the belt in any
store.** Pre-gen's `HistorySimulator._retire_fighter`
(`cage_dynasty_web/world_init.py:3118-3136`) is the only correct retire-
vacate path in the codebase — at `:3130` it calls
`self.belt_history.vacate_belt(weight_class=wc, week=current_week,
event_name=reason, reason="Retired")` and sets `is_champion=False` +
`title_holders.pop(wc, None)`. The two live paths below drift from that
shape.

### Aging block (game_bridge.py:11354-11485, inside advance_week)
- `cage_dynasty_web/game_bridge.py:11354-11388` — `should_retire` via
  `AgingSystem.check_retirement`; player fighters route to
  `_pending_retirement_prompts`, non-player appends to `retiring`.
- `cage_dynasty_web/game_bridge.py:11391-11485` — processes the
  `retiring` list:
  - `fighter.is_active = False` (`:11392`)
  - Camp roster removal + `_fighter_data` mirror (`:11394-11411`)
  - News headline (`:11472-11481`)
  - Rankings update for the division (`:11484`)
  - HOF eval (`:11486` via `_check_hof_on_retire`)
- **Missing**: `fighter.is_champion = False`; `division.champion_id =
  None`; close of `_title_history[wc][-1]` (is_active/lost_week/
  lost_event/lost_to_name/lost_method); `self._belt_history.vacate_belt(...)`.

### /retirement-decision 'retire' branch (routes.py:2727-2770, player-only)
- `cage_dynasty_web/routes.py:2745-2770` — reimplements the aging
  block's retire-handling in miniature:
  - `fighter.is_active = False` (`:2747`)
  - Camp roster removal + `_fighter_data` mirror (`:2748-2762`)
  - News headline (`:2763-2767`)
  - HOF eval (`:2769`)
- **Same hole**: no `is_champion=False`, no `division.champion_id=None`,
  no `_title_history` close, no `_belt_history.vacate_belt(...)`. The
  route is a parallel implementation of the aging block's retire path
  (not a dispatch into it), so a single fix would need to land in both
  places or be hoisted into a shared helper.

Consequence: when a champion retires in live play (either path),
`division.champion_id` keeps pointing at them,
`_title_history[wc][-1].is_active` stays True, and
`_belt_history.reigns[wc][-1].is_active` stays True (plus
`_belt_history.current_champions[wc]` still names them). Live
retirement is a **4th vacate hole**, on top of the three in
VACATED-REIGN1's docket.

**Probe implication**: v2 of the probe drops site 4 (retirement).
Neither live retire path calls a bridge method — both inline the
retire-handling — so there is no `bridge.retire_fighter(...)` to
invoke. The finding above stands by inspection; it is simply not
probe-covered. Any future fix should hoist the retire-handling into
a shared helper (which the probe can then call) rather than add a
third parallel implementation.

## 2. Write-set table — three known live vacate sites

| Site | Range | division.champion_id = None | _title_history keys set | _belt_history.vacate_belt | News |
|---|---|---|---|---|---|
| Injury auto-vacate | game_bridge.py:4053-4066 | **Y** (`:4054` id, `:4055` name) | `is_active=False`, `lost_week`, `lost_event="Vacated (injury)"`, `lost_to_name="Vacated"`, `lost_method="Injury"` (`:4059-4063`) | **N** | **Y** (`:4046`) |
| Player vacate (resolve_champion_injury_decision) | game_bridge.py:6934-6950 | **Y** (`:6939` id, `:6940` name) | `is_active=False`, `lost_week`, `lost_event="Vacated (player choice)"`, `lost_to_name="Vacated"`, `lost_method="Injury (vacated)"` (`:6943-6946`) | **N** | **Y** (`:6948`) |
| move_weight_class | game_bridge.py:21432-21444 | **Y** (`:21436` id, `:21437` name) | **No writes — reign stays `is_active=True` in `_title_history`** | **N** | **Y** (`:21439`) |

Correction vs backlog entry: `move_weight_class` is a **two-store miss**,
not just a `_belt_history` miss. Neither `_title_history` nor
`_belt_history` is written. The backlog's "two-store finding" (writes to
`_title_history`, misses `_belt_history`) applies only to the injury and
player paths. `move_weight_class` is strictly worse.

## 3. Other live sites that clear division.champion_id

`grep 'champion_id\s*=\s*None' cage_dynasty_web/game_bridge.py` returns
exactly three hits:

- `cage_dynasty_web/game_bridge.py:4054` — injury auto-vacate (§2)
- `cage_dynasty_web/game_bridge.py:6938` — player vacate (§2)
- `cage_dynasty_web/game_bridge.py:21436` — move_weight_class (§2)

No fourth live site clears the pointer. The retire paths in §1 do not
touch it (that is their defect, not a different site). Complete.

## 4. bridge._belt_history identity chain

Four pointers, one object:

- `cage_dynasty_web/world_init.py:1945` — `self.belt_history =
  BeltHistory()` inside `HistorySimulator.__init__`
- `cage_dynasty_web/world_init.py:3588` — `self._belt_history =
  self._history_sim.belt_history` inside `WorldInitializer`
- `cage_dynasty_web/world_init.py:3604` — `def get_belt_history(self)`
  returns `getattr(self, '_belt_history', None)`
- `cage_dynasty_web/game_bridge.py:2363-2365` — `_captured_bh =
  _initializer.get_belt_history(); if _captured_bh is not None:
  self._belt_history = _captured_bh`

Any `vacate_belt` call via `bridge._belt_history` lands on the reign
dicts the initializer built; writes propagate to the pre-gen reigns
without a copy step.

## Known false

`cage_dynasty_web/game_bridge.py:2274-2275` comment — "Runtime title-
fight writes go to `self._title_history`, NOT here — two separate stores
by design." — is **stale since BELT-STORE-UNIFY1**.
`_record_title_result` at `cage_dynasty_web/game_bridge.py:15836-15881`
explicitly mirrors live title changes AND defenses into `_belt_history`
via `title_changes_hands`, `crown_initial_champion`, and
`record_title_defense`. The comment described the design pre-BELT-
STORE-UNIFY1 and no longer matches the code. Any fix for VACATED-REIGN1
should delete or rewrite that comment too.

## 5. Measured — probe v3, HEAD f091db9 vs post-fix 1791962
Instrument: outputs/vacated_reign1/vacate_probe_v3.py (md5 a1a0de70efc34665139c2b8980bca002, untracked — DUMP-PROVENANCE1). Dumps: probe_head_f091db9_v3.json (a356255959fc1d256fa864447945355a), probe_post_fix.json (786ad853a1b38561e159304b015c4063). Seed 20260921, fresh world, three sites on three divisions: injury auto-vacate (CAREER injury injected, 26 weeks advanced — the 25-week counter fired, pointer cleared, so this path is live in play), player decision (staged pending decision, resolve 'vacate'), weight move (adjacent class).
- HEAD, all three post-vacate snapshots: division.champion_id None; _belt_history active_reigns 1, in_current_champions True, reign is_active True, lost_week None. The ghost, measured 3/3.
- POST, all three: active_reigns 0, in_current_champions False, is_active False, lost_week set (25/26/26), lost_method = bucket, lost_event = prose. Pre-vacate rows identical between runs on non-id fields (names, weeks, methods); ids differ per process — SAME SEED.
- HEAD Flyweight resolution sequence, corrected from the first read: reign A Francis Saint Denis (ghost, never closed); reign B Francis reclaims the vacant belt at resolution week 8 — a probe artifact, the probe's own _book_title_fight(wc) call lacked the exclude_ids the real player path passes; reign C Alexei Ankalaev beats Francis via SUB week 55 (title_changes_hands closes B). End state total 3, active 2, longest = Francis (B). Nothing ever closed A. POST: Alexei "Won Vacant Title (TKO)", active 1. Divergence after the fix is expected (booking reads the store).
- Live retirement (§1) remains inspection-only: no bridge method to probe. RETIRE-VACATE1.
- Site 4 absent; get_longest_reign fallback behaviour when no completed reigns exist is unread (census cut at the if-not-completed branch).

## 6. Observations filed, not scoped
- VACANT-FILL1: two of three vacated divisions (Strawweight, Bantamweight) went 40 weeks uncrowned; _book_title_fight returned None without exception both times; active fighters 32, scheduled fights 0 in the snapshot. One seed, probe conditions. Gate 0 later: what does _book_title_fight require to produce a fight.
- RETIRE-VACATE1: live retirement vacates no store; both retire paths inline. Fix shape: hoist into one helper, then vacate_belt. After Slice 3.
- Probe v4: pass exclude_ids on the probe's booking; print week-by-week title news for probed wcs; tee, never tail.
- _champ_weeks_since_defense counts injured weeks, not weeks since defense. Naming fossil.
- (b) 9418952: event_name → self._dfc_label(week) at all three sites. Reader-side finding: fighter_profile.html L1215–1216 keys the 🛡️ window on lost_event_number and treats None as open; 1791962's prose event_name parsed to None, so post-vacate wins would badge as defenses — the original (c) window FP with a new cause. Gate: outputs/vacated_reign1/lost_event_gate.py — after move_weight_class vacate, get_fighter_reigns gives lost_event 'Cage Dynasty 60', lost_event_number 60, lost_method 'Vacated (weight move)'. Off-week label = previous card = correct upper bound; L22 item (3) closed by that reading. Render-level confirmation (render_probe.py against a save with live vacates) still owed — Sunday, after deploy #9.
