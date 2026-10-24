# RETIRE-VACATE1 — Gate 1 (2026-10-19)

PARTIAL. g1 retired an ex-champion (belt lost wk 25, retire tick wk 52); the sitting-champion case in Gate 0 §5 is unmeasured as of g1. See g2 below. Probe shape per Van's instruction: Option A only, age=50 +
morale=1, advance_week until %52==0 fires, STOP if the branch misses.
No tracked-file edits. New probe at `outputs/vacated_reign1/retire_probe_v4.py`
(untracked); JSON dump at `outputs/vacated_reign1/retire_probe_g1.json`.

## 0. Census gaps closed

Grep A — all `is_active` → False assignments, tree-wide:

```
cage_dynasty_web/game_state.py:932:            self.fighters[fighter_id].is_active = False
cage_dynasty_web/models.py:864:                        is_active=False,
cage_dynasty_web/amateur.py:1763:        fighter.is_active = False
cage_dynasty_web/amateur.py:1874:                fighter.is_active = False
cage_dynasty_web/world_init.py:3119:        fighter.is_active = False
cage_dynasty_web/game_start.py:392:            self.is_active = False
cage_dynasty_web/game_start.py:1297:            contract.is_active = False
cage_dynasty_web/game_start.py:1319:        contract.is_active = False
cage_dynasty_web/game_start.py:1331:            contract.is_active = False
cage_dynasty_web/routes.py:2747:                fighter.is_active = False
cage_dynasty_web/routes.py:2758:                        fighter_id]['is_active'] = False
cage_dynasty_web/game_bridge.py:3475:        # forever (retirement set is_active=False but never removed the
cage_dynasty_web/game_bridge.py:11371:            fighter.is_active = False
narrative/rivalry.py:325:            self.is_active = False
```

Grep B — `champion_id = None`, `is_champion = False`,
`current_champions.pop`:

```
cage_dynasty_web/game_state.py:949:                self.fighters[old_champion_id].is_champion = False
cage_dynasty_web/world_init.py:694:        self.current_champions.pop(weight_class, None)
cage_dynasty_web/world_init.py:2308:                loser.is_champion = False
cage_dynasty_web/world_init.py:3127:            fighter.is_champion = False
cage_dynasty_web/game_bridge.py:4047:                            champ.is_champion = False
cage_dynasty_web/game_bridge.py:6925:                ftr.is_champion = False
cage_dynasty_web/game_bridge.py:6926:                div.champion_id = None
cage_dynasty_web/game_bridge.py:15772:                old_champ.is_champion = False
cage_dynasty_web/game_bridge.py:21364:            fighter.is_champion = False
cage_dynasty_web/game_bridge.py:21367:                old_div.champion_id = None
```

**No downstream-sweep clears a champion on inactivity.**
`game_state.py:932` lives inside `_on_fighter_retired` (`:928`) — a
handler never registered or dispatched (grep: `grep -rn
"_on_fighter_retired" cage_dynasty_web/` returns only the definition
line; no `emit('fighter_retired', …)` fires it). The clears at
`:949` and `world_init.py:2308` happen on title transfer. The clears
at `game_bridge.py:4047 / 6925 / 15772 / 21364` are injury-vacate,
player-choice vacate, successor-crown-write-path (title transfer), and
weight-move. The lone pre-gen retire path (`world_init.py:3127`) does
clear `is_champion`. **No live-play reader reacts to `is_active=False`
by clearing `is_champion` or `division.champion_id`.** Gate 0 §1 count
of "retire paths that touch belt state" stands at zero.

(amateur.py and game_start.py hits are either amateur state machine
or coach-contract bookkeeping, out of census scope. rivalry.py:325 is
a `Rivalry` dataclass flag, not a fighter flag.)

## 1. Probe v3 located → copied to v4

- v3: `outputs/vacated_reign1/vacate_probe_v3.py` (410 lines, md5
  a1a0de70efc34665139c2b8980bca002, UNCHANGED).
- v4: `outputs/vacated_reign1/retire_probe_v4.py` (untracked, 322 lines).

v4 keeps v3's bridge-build + fight_engine binding gates, drops the
three vacate sections and the `_title_history` references (store was
retired at 92bd7fa), replaces with a single retire-via-aging path.

## 2. Run

Command:
`PYTHONPATH=narrative:systems:cage_dynasty_web python3 outputs/vacated_reign1/retire_probe_v4.py g1`

Head of output (environment gates):

```
RETIRE-PROBE v4 — label=g1
======================================================================
fight_engine.__file__            = /Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty_web/fight_engine.py
world_init.FULL_ENGINE_AVAILABLE = True
AGING_AVAILABLE                  = True
✅ Real engine, FULL_ENGINE_AVAILABLE=True, AGING_AVAILABLE=True

SEED = 20260921
```

Picked: `Ricardo Werdum (332a1c2c)` — Strawweight champion;
`camp_id='bb87870a'`, player_camp_id different (confirmed non-player
branch).

Applied: age=50, morale=1.

Advanced 52 weeks. Branch fired at week 52 (annual tick). One more
week advanced to settle side-effects (now wk 53).

Proof the branch fired (printed verbatim):

```
Post annual tick:
  gs.week_number           = 53
  fighter.is_active        = False
  fighter.is_champion      = False
  retirement news entries  = 2
  in _pending_retirement   = False

✅ Branch fired: is_active=False + 2 retirement news entry(ies) referencing Ricardo Werdum
```

Van's STOP criteria (`fighter.is_active is False AND a retirement
news entry exists`): BOTH satisfied. Probe did not STOP; dump written.

Retirement news headlines:
```
🏛️ Ricardo Werdum retires straight into the Hall of Fame as a All-Time Great!
🥊 Ricardo Werdum retires at 51 (6-1) — a respected career.
```

## 3. Pre/post JSON (dumped by probe; full file
`outputs/vacated_reign1/retire_probe_g1.json`)

### PRE (just before weekly loop begins; after age/morale override)

```json
{
  "fighter": {
    "fighter_id": "332a1c2c",
    "name": "Ricardo Werdum",
    "weight_class": "Strawweight",
    "is_active": true,
    "is_champion": true,
    "age": 50,
    "morale": 1,
    "wins": 5,
    "losses": 0,
    "camp_id": "bb87870a"
  },
  "division": {
    "wc": "Strawweight",
    "total_reigns_bh": 1,
    "active_reigns_bh": 1,
    "in_current_champions": true,
    "current_champions_value": "332a1c2c",
    "division_champion_id":   "332a1c2c",
    "division_champion_name": null,
    "last_reign_bh": {
      "champion_id":   "332a1c2c",
      "champion_name": "Ricardo Werdum",
      "won_week": 0,
      "won_event": "Cage Dynasty Founding — Strawweight Championship",
      "won_from": null,
      "won_from_name": null,
      "won_method": "Inaugural Crown",
      "lost_week": null,
      "lost_event": null,
      "lost_event_number": null,
      "lost_method": null,
      "lost_to": null,
      "lost_to_name": null,
      "is_active": true,
      "successful_defenses": 4
    }
  }
}
```

### POST (after annual tick + one settle week; wk 53)

```json
{
  "fighter": {
    "fighter_id": "332a1c2c",
    "name": "Ricardo Werdum",
    "weight_class": "Strawweight",
    "is_active": false,
    "is_champion": false,
    "age": 51,
    "morale": 1,
    "wins": 7,
    "losses": 1,
    "camp_id": "bb87870a"
  },
  "division": {
    "wc": "Strawweight",
    "total_reigns_bh": 2,
    "active_reigns_bh": 1,
    "in_current_champions": true,
    "current_champions_value": "c1781d01",
    "division_champion_id":   "c1781d01",
    "division_champion_name": "Sodiq Chimaev",
    "last_reign_bh": {
      "champion_id":   "c1781d01",
      "champion_name": "Sodiq Chimaev",
      "won_week": 25,
      "won_event": "Cage Dynasty 77",
      "won_from": "332a1c2c",
      "won_from_name": "Ricardo Werdum",
      "won_method": "TKO",
      "lost_week": null,
      "lost_event": null,
      "lost_event_number": null,
      "lost_method": null,
      "lost_to": null,
      "lost_to_name": null,
      "is_active": true,
      "successful_defenses": 1
    }
  }
}
```

## 4. Q4 — v3 lost_event + `_event_number_from_name("Retired")`

Both captured by the probe:

```
Q4: v3 injury_post.last_reign_bh.lost_event = 'Stripped after 25 weeks injured'
Q4: _event_number_from_name('Retired')      = None
```

**v3's `lost_event` is NOT `_dfc_label` output.** Probe v3 ran on
Oct 17 18:24 PDT at commit 1791962 (committed later same day, 20:45
PDT — the probe exercised the working tree). At 1791962, the injury
vacate wrote a prose string, not a card label. `_dfc_label` wiring at
the injury site landed in commit **9418952** (VACATED-REIGN1 (b),
2026-10-17 21:14 PDT) — AFTER the probe dump was captured. On HEAD
f45dba9 the string is now `_dfc_label(current_week)` → `"Cage Dynasty
NN"` which parses to int NN via `_event_number_from_name`. Gate 0 §2's
claim that the three live vacate sites pass `_dfc_label` is correct
for HEAD; probe v3's `probe_post_fix.json` reflects the pre-(b) prose
string and must be read with that commit in mind.

**`_event_number_from_name("Retired")` returns `None`.** The function
needs a trailing integer; the bare word "Retired" has none. If a
future retire-vacate fix passes `reason="Retired"` into `vacate_belt`
with `event_name=_dfc_label(current_week)` (the three-vacate-sites
pattern), the template consumes `lost_method="Retired"` for display
and `lost_event_number=NN` for the 🛡️ window — same shape as the
three current vacate buckets. If the fix instead passed `event_name="
Retired"` (reason-only, no card label), the template's 🛡️ window
predicate at `fighter_profile.html:1216` would get None for
`lost_event_number` and would never close — exactly the 1791962-pre-(b)
hazard the (b) commit eliminated.

## 5. Comparison vs Gate 0 §5 — findings

Gate 0 §5 predicted the state of **a sitting champion** retiring. The
probe's picked champion stayed in the role for 25 weeks of live play,
then **lost the belt to Sodiq Chimaev at week 25 via TKO at Cage
Dynasty 77**, fought a few more fights as a now-ex-champion, then
retired at week 52. So the probe fired the retire path on an
**ex-champion**, not a sitting champion. Comparison line-by-line:

| Gate 0 §5 prediction (sitting champ at retire) | Observed in run (ex-champ at retire) | Verdict |
|---|---|---|
| `fighter.is_active` → False | False ✓ | **Confirmed** (one half-step: works regardless of champion-at-retire-time) |
| `fighter.is_champion` → True (unchanged by retire) | False | **UNTESTED** — cleared at wk 25 by title_changes_hands write path at `game_bridge.py:15772`, not by retire. Prediction remains correct about the retire path's behavior, but not observable through this run. |
| `division.champion_id` / `champion_name` → still point at retired fighter | Points at Sodiq Chimaev (new champion since wk 25) | **UNTESTED** — updated at title transfer, not by retire. |
| Reign's `lost_week` → None | Werdum's reign has `lost_week=25`, `lost_to=Chimaev`, closed; Chimaev's new reign is the "last reign" and that one is active (None lost_*). | **UNTESTED** for retire's effect; the open reign in post belongs to the SUCCESSOR, not the retiree. |
| `_belt_history.current_champions[wc]` stale with retired fid | Mapped to Chimaev's fid | **UNTESTED** — updated at title transfer. |
| `_get_title_records` counts open reign | Count unchanged by retire itself (open reign now belongs to Chimaev) | **UNTESTED** |
| `_compute_hof_score` includes open reign | Fired at retire with Werdum's reign CLOSED (lost at wk 25, 4 defenses) → score pushed Werdum over HOF_THRESHOLD → "retires straight into the Hall of Fame" news emitted | **Observed**: HOF-on-retire fires; here with a closed reign, not an open one. |

### Primary finding — measurement gap

**Van's Option-A path cannot isolate a sitting-champion retire on
seed 20260921.** The first annual aging tick lands at week 52; by
that time, a champion active in the division has typically been
dethroned via normal matchmaking (Werdum: 5 defenses + 1 loss + 2 more
wins in 52 weeks). The retire path fired on an ex-champion.

Follow-up options (none built here, filed for the ruling):
- Alternative seed sweep until a champion makes it to week 52 still
  holding the belt (expensive; may require 10+ seeds × ~5 min pre-gen).
- Shorter window: patch `_advance_aging_week` or
  `AgingSystem.should_process_annual_aging` under harness to allow a
  week-1 tick (invasive — stops being Option A).
- Accept Option C as the mechanism (Van explicitly refused this).

### Secondary findings

1. **Gate 0 §1 census was accurate, but the retire path is not the
   whole story for a dethroned champion.** The 1791962 (b) + title
   transfer paths DO clear `is_champion` and update `division.
   champion_id` BEFORE the retire tick, so for the typical "aging
   champion loses belt then retires months later" trajectory, the
   belt-side state is correct by the time retire fires. The ghost
   case Gate 0 predicted (sitting champion retires with reign still
   open) is a NARROWER case than the aging path's full behavior —
   it only manifests when the retire tick lands on a still-sitting
   champion. One-year gap between retire checks makes that narrow.

2. **Retire path emits TWO news entries, not one.** `_check_hof_on_retire`
   fires inside the retire branch (`game_bridge.py:11462`), and
   `_induct_into_hof` writes a `category="retirement"` headline
   (`:4446-4449`). The aging block then writes its own
   `category="retirement"` entry (`:11450-11456`). Both reference the
   retired fighter. Gate 0 §1's "emits retirement news" was correct in
   direction but understated the count.

3. **`_event_number_from_name("Retired")` returns None.** Not a
   finding against HEAD — a design input for the fix. The retire-
   vacate fix must pass `event_name=_dfc_label(current_week)` (not
   the bucket string) for the template's `lost_event_number` to
   parse and the 🛡️ window to close.

4. **Probe v3's `probe_post_fix.json` holds a pre-(b) `lost_event`
   string**, retained for provenance. Not a defect, just a reader
   trap for anyone comparing v3's dump against HEAD's injury-vacate
   output.

### Gate 0 §5 claims that stand without change

- The retire path at `game_bridge.py:11371` writes
  `fighter.is_active = False` and nothing to `_belt_history`.
- Both live-play retire sites (aging block + /retirement-decision)
  do NOT touch `fighter.is_champion`, `division.champion_id`, or
  `_belt_history`. (Confirmed by Grep B + branch inspection; this
  run's `fighter.is_champion=False` is attributable to the title
  transfer at wk 25.)
- `_event_number_from_name` is None for the bare word "Retired";
  confirmed empirically.

### Gate 0 §5 claims that remain untested

Everything else in Gate 0 §5 — the belt-ghost case where a champion
retires while still holding the belt. The underlying question "does
the retire path leave `_belt_history` and `division.champion_id`
pointing at an inactive fighter" is still a prediction, not a
measurement.

## §6 — g2: sitting-champion case MEASURED

Probe v4 was edited (untracked) to: (a) advance with no mutation until
`gs.week_number % 52 == 51`; (b) pick a non-player sitting champion
where `division.champion_id == _belt_history.reigns[wc][-1].champion_id`
AND the last reign is active AND the champion has no scheduled fight
this week or next; (c) snapshot pre, apply age=50 + morale=1,
advance ONE week; (d) if the branch missed and `wk%52==0` now, advance
one more; (e) snapshot post immediately and once more one week later.

Run: `PYTHONPATH=narrative:systems:cage_dynasty_web python3
outputs/vacated_reign1/retire_probe_v4.py g2`
Dump: `outputs/vacated_reign1/retire_probe_g2.json`

### §6a — pick

`pick_scan` returned Strawweight on the first candidate; print trace:

```json
[{"wc": "Strawweight", "reason": "PICKED",
  "name": "Lyoto Nascimento", "fighter_id": "a906d975"}]
```

Lyoto Nascimento (fid `a906d975`) — Strawweight sitting champion at
wk 51. Won belt from Ricardo Werdum at wk 23 via TKO at Cage Dynasty
76; 1 successful defense since. Camp `b21e414c` (non-player). No
scheduled fight at wk 51 or wk 52.

Advanced through weeks 1-51 (51 advances from pre-gen start wk 0) with
no mutation; `wk%52==51` reached cleanly.

### §6b — branch fired on advance #1

```json
"ticks": [
    {"advance_n": 1, "week": 52, "annual_now": true,
     "fighter_is_active": false}
],
"fired_on_advance": 1
```

Fighter.is_active flipped on the very first advance_week call after
the pick. No second advance was needed. Retirement news count = 2
immediately, unchanged after one further week.

### §6c — Gate 0 §5 field-by-field vs g2 observation

| Field (Gate 0 §5 prediction) | PRE | POST (immediate) | POST (+1 wk) | Verdict |
|---|---|---|---|---|
| `fighter.is_active` → False | True | **False** | False | **Confirmed** |
| `fighter.is_champion` → True (UNCHANGED by retire) | True | **True** | True | **Confirmed** |
| `division.champion_id` → unchanged, retired fid | `a906d975` | `a906d975` | `a906d975` | **Confirmed** |
| `division.champion_name` → unchanged | "Lyoto Nascimento" | "Lyoto Nascimento" | "Lyoto Nascimento" | **Confirmed** |
| `reign.lost_week` → None | null | **null** | null | **Confirmed** |
| `reign.lost_event` → None | null | **null** | null | **Confirmed** |
| `reign.lost_event_number` → None | null | **null** | null | **Confirmed** |
| `reign.lost_to` → None | null | **null** | null | **Confirmed** |
| `reign.lost_to_name` → None | null | **null** | null | **Confirmed** |
| `reign.lost_method` → None | null | **null** | null | **Confirmed** |
| `reign.is_active` → True (open ghost) | True | **True** | True | **Confirmed** |
| `_belt_history.current_champions[wc]` → stale, retired fid | `a906d975` | `a906d975` | `a906d975` | **Confirmed** |
| Record Book / HOF reign-count readers see open reign | n/a | reign still counted (same reign, now ghost) | same | **Confirmed** indirectly: HOF-on-retire fired (2 news entries incl. HOF line) with the reign still open — Nascimento inducted "straight into the Hall of Fame as a All-Time Great". Score counted the open reign. |

**Gate 0 §5 confirmed, one case (seed 20260921, Strawweight).** Every
predicted field matches observation; the "retired fighter still has a
CHAMPION badge, still owns the belt in `_belt_history`, still points
back from `division.champion_id`, reign stays open with no lost_*
data" ghost is real on HEAD f45dba9. No field disagreed with
prediction.

### §6d — downstream-sweep check

The `post_plus_one` snapshot (one `advance_week` later) is byte-for-
byte identical to `post_immediate` on every division/reign/
current_champions field. Confirms Gate 1 §0's finding: no live-play
code path reacts to `is_active=False` by sweeping the belt. The ghost
state persists past the week it was created.

### §6e — pre-gen "Retired" bucket lookup

Probe scanned every reign in `_belt_history.reigns` for
`lost_method == "Retired"` and reported:

```json
"retired_sample": {
    "sample": null,
    "event_number_from_name_of_lost_event": null
}
```

**No pre-gen reign in this world has lost_method == "Retired".** The
`"Retired"` default on `vacate_belt(weight_class, week, event_name,
reason="Retired")` at `world_init.py:684` is dead in practice: the
only pre-gen caller is `_retire_fighter` at `:3130`, which passes
`reason=reason` where `reason` is `"Annual age check"` (callsite
`:3084`) or `f"Post-fight ({event_name})"` (callsite `:3113`) —
never the default. So "Retired" as a `lost_method` string is
**unreached** at HEAD f45dba9; filing is unused provenance.

**[KNOWN FALSE 2026-10-19 Gate 2 §1.]** Misread of the pre-gen call site.
At `world_init.py:3130` the call is
`self.belt_history.vacate_belt(weight_class=wc, week=current_week,
event_name=reason, reason="Retired")` — the `_retire_fighter`
parameter `reason` is passed as `event_name`; the `vacate_belt`
`reason=` kwarg is the HARDCODED STRING `"Retired"`. So pre-gen
retire DOES write `lost_method="Retired"` when it fires. The scan
returned zero because NO pre-gen champion retired in the g2 world
(seed 20260921, default HISTORY_WEEKS=60) — not because the default is
dead. In worlds where a pre-gen champion crosses the retirement
threshold, the resulting reign carries `lost_method="Retired"` +
`lost_event=<prose "Annual age check" or "Post-fight (CD NN)">`;
`_event_number_from_name` on those prose strings returns None (same
pre-9418952(b) hazard documented in §4). Gate 0 §1 pre-gen row and
Gate 0 §2 "Retired (pre-gen only)" are correct; §6e was wrong.

Implication for the RETIRE-VACATE1 fix: if the fix passes
`reason="Retired"` to `vacate_belt`, that becomes the FIRST reign in
the codebase to carry `lost_method == "Retired"`. Templates currently
render `lost_method` verbatim at `champions.html:105` and
`fighter_profile.html:922`; "Retired" would appear as the "via" phrase
("Lost to … via Retired"). That phrasing is wrong — a retired
champion wasn't lost TO anyone. Consider a different lost_method
string like `"Vacated (retirement)"` (matches the three existing
`"Vacated (…)"` buckets) and ensure `lost_to`/`lost_to_name` stay
None so the template's `{% elif reign.lost_to_name %}` branch at
`fighter_profile.html:913` falls through to the `· Vacated` else
branch at `:924` instead.

### §6f — findings summary

1. **Gate 0 §5 is now MEASURED, not predicted** — every row of the
   ghost-reign table confirms on HEAD f45dba9. Promote the prediction
   label to measurement in the §5 header on the next docs touch.
2. **The ghost is persistent across advance_week** — no downstream
   sweep. The fix must be in the retire-path itself.
3. **"Retired" as a lost_method value does not exist in current
   data** — a retire-vacate fix should use a different bucket string
   that fits the existing `"Vacated (…)"` family and keeps
   `lost_to=None` so templates fall through to the `· Vacated`
   branch, not the `· Lost to None` branch.
4. **g2 retirement news count = 2** (HOF + retire line), same shape
   as g1. The retire path writes both regardless of champion-status-at-
   retire-time.
5. **Lyoto Nascimento's post-g2 state is the exact bug Van filed as
   RETIRE-VACATE1**: profile would render CHAMPION badge + "Current
   champion" reign card + open 🛡️ window, Champions page would show
   CURRENT, Record Book + HOF would count the reign, matchmaking
   would skip Strawweight's title fight indefinitely (champ
   not-is_active per `_build_card_for_week` filter), the belt would
   sit open with the retired fighter still mapped as its holder.
