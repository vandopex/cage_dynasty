# BELT-HISTORY Gate 0 — 2026-09-18

**Question this gate answers.** When a title changes hands in LIVE PLAY,
does the transfer reach `_belt_history`, `_title_history`, both, or
neither — and which store does each player-visible surface read?

Read-only. No edits to any tracked file. No commits.

Repo state: HEAD `6fe622d` (docs-tier), PA at `46c094f`, working tree
clean of tracked changes. Harness lives at `outputs/belt_history/gate0_harness_v2.py`
(untracked, per DUMP-PROVENANCE1 conventions). Raw stdout captured at
`outputs/belt_history/gate0_run_v2_full.txt`. JSON dump at
`outputs/belt_history/gate0_run_2026-09-18.json`. Three surface HTML
captures at `outputs/belt_history/gate0_{champions,record_book,profile}.html`;
supplement at `gate0_profile_liu.html`.

---

## §1  Store census

### `_belt_history`

WRITERS
- `cage_dynasty_web/game_bridge.py:2278` — `self._belt_history = _BH_cls()`
- `cage_dynasty_web/game_bridge.py:2280` — `self._belt_history = None`
- `cage_dynasty_web/game_bridge.py:2365` — `self._belt_history = _captured_bh` (post-`new_game` capture off the WorldInitializer)
- `cage_dynasty_web/game_bridge.py:3282` — `self._belt_history = _BH_load.from_dict(data["belt_history"])` (save/load)
- `cage_dynasty_web/game_bridge.py:15856` — `self._belt_history.title_changes_hands(...)` (live-play transfer)
- `cage_dynasty_web/game_bridge.py:15868` — `self._belt_history.crown_initial_champion(...)` (live-play vacant-title claim)
- `cage_dynasty_web/game_bridge.py:15893` — `self._belt_history.record_title_defense(weight_class)` (live-play defense)
- `cage_dynasty_web/world_init.py:3588` — `self._belt_history = self._history_sim.belt_history` (**PRE-GEN population**)

READERS
- `game_bridge.py:2363` — `_captured_bh = _initializer.get_belt_history()`
- `game_bridge.py:2986` — `"belt_history": self._belt_history.to_dict() if self._belt_history else {}` (save)
- `game_bridge.py:7103, 7105` — reads in `_convert_real_fighter` variant A
- `game_bridge.py:7298, 7300` — reads in `_convert_real_fighter` variant B
- `game_bridge.py:7580, 7582` — reads in `_convert_real_fighter` variant C
- `game_bridge.py:9574` — `if self._belt_history is None:` (guard)
- `game_bridge.py:9577` — `reigns = self._belt_history.get_fighter_reigns(fighter_id)` (**profile surface**)
- `game_bridge.py:15840` — `if self._belt_history is not None:` (guard in live transfer)
- `game_bridge.py:15889` — `if self._belt_history is not None:` (guard in live defense)
- `game_bridge.py:15890` — `_reigns = self._belt_history.reigns.get(weight_class, [])` (identity guard for defense mirror)
- `world_init.py:3606` — `return getattr(self, '_belt_history', None)` (initializer accessor)
- `cage_dynasty_web/routes.py` — no hits
- `cage_dynasty_web/templates/` — no hits

### `_title_history`

WRITERS
- `game_bridge.py:2201` — `self._title_history: Dict[str, List[Dict[str, Any]]] = {}` (initial empty)
- `game_bridge.py:3203` — `self._title_history = data.get("title_history", {})` (save/load)
- `game_bridge.py:15801` — `if weight_class not in self._title_history: self._title_history[weight_class] = []` (lazy init per division on first live title fight)
- `game_bridge.py:15802` — `history = self._title_history[weight_class]` (reads too)
- `game_bridge.py:15804` — `history = self._title_history[weight_class]` (reads too)
- Reign append at `game_bridge.py:15817-15831` (live-play transfer body)
- Reign defense counter increment at `game_bridge.py:15879-15880` (live-play defense body)

READERS
- `game_bridge.py:2977` — `"title_history": self._title_history,` (save)
- `game_bridge.py:4058` — `history = self._title_history.get(wc, [])` (vacate injury path)
- `game_bridge.py:4393` — iterated in the `_advance_week_impl` sweep
- `game_bridge.py:6939` — `history = self._title_history.get(wc, [])` (vacate player path)
- `game_bridge.py:9907` — read
- `game_bridge.py:15112` — `for _wc_reigns in self._title_history.values():` (**record book aggregator `_get_title_records`**)
- `game_bridge.py:15907` — `history = self._title_history.get(weight_class, [])` (**Champions page `get_champions_history`**)
- `cage_dynasty_web/routes.py` — no hits
- `cage_dynasty_web/templates/` — no hits

### Surface trace

**Champions page**
- Route: `champions_history()` at `cage_dynasty_web/routes.py:1777`, URL `/champions` or `/champions/<division>`
- Template: `cage_dynasty_web/templates/champions.html`
- **Reads `_title_history`** via `bridge.get_champions_history(division)` at `game_bridge.py:15907`. If `_title_history[wc]` is empty, `get_champions_history` synthesizes a "Season Opener / Inaugural Champion" reign from `division.champion_id` (`game_bridge.py:15910-15929`).

**Record book**
- Route: `record_book()` at `cage_dynasty_web/routes.py:2878`, URL `/record-book`
- Template: `cage_dynasty_web/templates/record_book.html`
- Renders `records = bridge.get_record_book()`. Within it, the "Most Title Reigns" and "Most Defenses" cards come from `records["title_records"]`, populated by `_get_title_records()` at `game_bridge.py:15109`, which iterates `self._title_history.values()` at `:15112`. **Reads `_title_history`.**

**Fighter profile**
- Route: `fighter_profile()` at `cage_dynasty_web/routes.py:839`, URL `/fighter/<fighter_id>`
- Template: `cage_dynasty_web/templates/fighter_profile.html`
- Reads reigns via `bridge.get_fighter_reigns(fighter_id)` at `game_bridge.py:9566`, which reads `self._belt_history.get_fighter_reigns(fighter_id)` at `:9577`. **Reads `_belt_history`.**

### Writer coincidence, at the transfer site

Two writes fire on any live-play title change, in this order
(`game_bridge.py:15800-15900`):

1. `_title_history[wc]` — reign row appended (or defense counter incremented).
2. `_belt_history` — mirrored via `title_changes_hands` / `crown_initial_champion` / `record_title_defense` (BELT-STORE-UNIFY1 block, comment at `:15833-15839`).

Live-play writes to **both** stores.

Pre-gen population (`world_init.py:3588`) writes to `_belt_history` **only**.
No pre-gen path writes to `_title_history`.

---

## §2  Fresh world with a live transfer

Harness preamble output:
```
fight_engine.__file__ = /Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty_web/fight_engine.py
world_init.FULL_ENGINE_AVAILABLE = True
✅ [IMPORT-PATH-PROOF] fight_engine.__file__=/Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty_web/fight_engine.py
✅ [IMPORT-PATH-PROOF] fight_integration.__file__=/Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty_web/fight_integration.py
✅ Real engine bound at web-copy path AND FULL_ENGINE_AVAILABLE=True
```

Harness note (HARNESS-ENV1): the first attempt via `_harness_env` and
the second attempt with just `PYTHONPATH=narrative:systems:cage_dynasty_web`
both hit the SIMULATION-SHIM failure (`Gameplan` not in
`systems/fight_engine.py`) because when the script lives outside
`cage_dynasty_web/`, Python prepends the script's own directory to
`sys.path[0]` and PYTHONPATH's entry order puts `systems/` ahead of
`cage_dynasty_web/`. Both routes let `import fight_engine` resolve to the
CLI copy at shim-load time. The v2 harness prepends
`/Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty_web` to `sys.path[0]`
at the very top of the module — before any project import — mirroring
what happens when `python3 cage_dynasty_web/app.py` runs directly. That
puts the web copy first and the SIMULATION-SHIM succeeds. This is a
practical workaround for HARNESS-ENV1, not a fix to it.

- SEED = `20260918`
- `bridge.new_game(...)` OK — world initialized with 60 pre-gen weeks
- Advance loop runs `bridge.advance_week()` until any division has a
  `_title_history` entry with `won_week >= 1` and
  `won_method != "Inaugural Champion"` and `won_from_name is not None`
- First live transfer: **Featherweight at live-axis week 1**
  (Cage Dynasty 61: Noah Johnson def. Liu Xiaolong via TKO R2)
- Bridge is at live week 1 when the transfer is detected.

Note on the axis label emitted by the harness for reigns [1-3] of
`_belt_history` below (Benoit Dupont wk 7, Mikhail Popov wk 28,
Liu Xiaolong wk 47): the harness's `_axis()` classifier calls anything
`won_week >= 1` "LIVE-AXIS", which is wrong for pre-gen reigns whose
`won_week` also runs in `1..history_weeks`. The correct disambiguator
is `won_event`: pre-gen events are labelled "Cage Dynasty 1-60", live
events start at "Cage Dynasty 61" (the first live-axis event for this
world). By that criterion, reigns [1-3] are PRE-GEN despite the
classifier's label. Only reign [4] is truly LIVE-AXIS.

---

## §3  Side-by-side, Featherweight

`_belt_history.reigns['Featherweight']` — **5 reigns** (verbatim from
harness `§3` output):

| # | axis | champion | won_week | won_event | won_from | won_method | lost_week | lost_event | lost_to | lost_method | defs | active |
|---|------|----------|----------|-----------|----------|------------|-----------|------------|---------|-------------|------|--------|
| 0 | PRE-GEN | Joseph King | 0 | Cage Dynasty Founding — Featherweight Championship | (none) | Inaugural Crown | 7 | Cage Dynasty 7 | Benoit Dupont | SUB | 0 | False |
| 1 | PRE-GEN | Benoit Dupont | 7 | Cage Dynasty 7 | Joseph King | SUB | 28 | Cage Dynasty 28 | Mikhail Popov | SUB | 0 | False |
| 2 | PRE-GEN | Mikhail Popov | 28 | Cage Dynasty 28 | Benoit Dupont | SUB | 47 | Cage Dynasty 47 | Liu Xiaolong | SUB | 1 | False |
| 3 | PRE-GEN | Liu Xiaolong | 47 | Cage Dynasty 47 | Mikhail Popov | SUB | 1 | Cage Dynasty 61 | Noah Johnson | TKO | 0 | False |
| 4 | LIVE | Noah Johnson | 1 | Cage Dynasty 61 | Liu Xiaolong | TKO | — | — | — | — | 0 | **True** |

(Reign [3]'s `lost_week=1` is the LIVE-AXIS week — the pre-gen champion
lost the belt in the first live-play card, which is exactly the axis-
crossing this Gate 0 was designed to observe.)

`_title_history['Featherweight']` — **1 entry**:

| # | axis | champion | won_week | won_event | won_from | won_method | lost_week | defs | active |
|---|------|----------|----------|-----------|----------|------------|-----------|------|--------|
| 0 | LIVE | Noah Johnson | 1 | Cage Dynasty 61 | Liu Xiaolong | TKO | None | 0 | True |

Founding champion of Featherweight, both stores:
- `_belt_history[0]`: Joseph King, `won_week=0`, method=`'Inaugural Crown'`
- `_title_history[0]`: Noah Johnson, `won_week=1`, method=`'TKO'`

The two stores name **different fighters** as "the first reign for this
division". The founding champion (Joseph King) does not appear in
`_title_history` at all. Neither do the two intermediate pre-gen
champions (Benoit Dupont, Mikhail Popov). Neither does Liu Xiaolong,
the pre-gen champion who was defeated in the observed live transfer.

**`_title_history` contains only reigns that were opened by a live-play
title fight.** Every pre-gen reign is invisible to it.

---

## §4  Surface reads, same save, same division

Fetched via Flask `test_client` with the harness's bridge wired into
`app.game_bridges["gate0_belt_history"]`.

### (a) Champions page — `/champions/Featherweight`

`HTTP 200`. Verbatim division-stats block (from
`outputs/belt_history/gate0_champions.html:295-315`):

- **Title Changes: 1**
- **Most Defenses: 0**
- **Total Reigns: 1**

Belt Lineage section (verbatim from `gate0_champions.html:317-345`):

- Reign 1 (CURRENT): **Noah Johnson**
  "Won from Liu Xiaolong via TKO at Cage Dynasty 61"
  "0 successful defenses"

Reigns for Joseph King, Benoit Dupont, Mikhail Popov, Liu Xiaolong: **not rendered**.

### (b) Record book — `/record-book`

`HTTP 200`. "Most Title Reigns" card (verbatim from
`gate0_record_book.html:232-259`):

- 1. Noah Johnson — 1x
- 2. Steven Garcia — 1x

"Most Defenses" card (verbatim from `gate0_record_book.html:259-284`):

- 1. Noah Johnson — 0
- 2. Steven Garcia — 0

Both rows are the two live-axis transfers that fired in the first
week of play (Featherweight and Middleweight; Steven Garcia won the
Middleweight belt at Cage Dynasty 61 on the same night). Every pre-gen
reign — 9 founding champions across 9 divisions plus every
intra-pre-gen transfer — is absent from both cards.

### (c) Current champion's profile — `/fighter/6b43b5db` (Noah Johnson)

`HTTP 200`. "Championship Reigns" section (verbatim from
`gate0_profile.html:761-800`):

- Featherweight (Active)
- "Won from Liu Xiaolong · Cage Dynasty 61 · TKO"
- "0 defenses · Current champion"

Noah has one reign; it renders correctly.

### (c-supplement) Deposed champion's profile — Liu Xiaolong (id `90b799b9`)

Fetched by a second harness (`gate0_supplement_liu.py`), same seed, same
week-1 state. HTTP 200. "Championship Reigns" section (verbatim from
`gate0_profile_liu.html:765-800`):

- Featherweight
- "Won from Mikhail Popov · Cage Dynasty 47 · SUB"
- "0 defenses · Lost to Noah Johnson · Cage Dynasty 61 · TKO"

Liu's PRE-GEN reign renders correctly on his profile — pre-gen
`won_from_name`, pre-gen `won_event`, pre-gen method, plus the live-axis
loss to Noah. The profile is reading `_belt_history` via
`get_fighter_reigns`, which returns Liu's reign object including all
its pre-gen fields.

### Surface / store / content / render table

| Surface | Store read | Store contains live transfer? | Store contains pre-gen chain? | What surface shows for Featherweight |
|---|---|---|---|---|
| Champions page | `_title_history` (via `get_champions_history`) | **Yes** (Noah Johnson, wk 1) | **No** (0 of 4 pre-gen reigns) | Total Reigns 1; Noah Johnson labelled reign #1, "Won from Liu Xiaolong via TKO at CD 61" (label correct on that reign only; four prior reigns invisible) |
| Record book "Most Title Reigns" | `_title_history` (via `_get_title_records`) | **Yes** (Noah + Steven Garcia counted 1x each) | **No** (0 pre-gen reigns aggregated) | 2 entries (Noah 1x, Garcia 1x). 9 founding champions across 9 divisions absent |
| Fighter profile — current champ | `_belt_history` (via `get_fighter_reigns`) | **Yes** (Noah reign [4]) | **Yes** (Noah is contiguous with prior reigns; his one reign renders correctly) | 1 reign, Won from Liu Xiaolong |
| Fighter profile — deposed champ | `_belt_history` (via `get_fighter_reigns`) | N/A (Liu was lost-to, not gained-from, at live wk 1) | **Yes** (Liu's pre-gen reign [3] with wk-47 win, live-axis wk-1 loss) | 1 reign, "Won from Mikhail Popov · CD 47 · SUB · Lost to Noah Johnson · CD 61 · TKO" — full pre-gen + axis-crossing history renders |

---

## §5  Interpretation

**The evidence supports (b): one store is missing the pre-gen population,
and the surfaces reading it therefore render an incomplete lineage. It
is a WRITE-PATH gap, not a read-side mis-selection.**

Both stores receive the live transfer — `game_bridge.py:15801-15900`
writes `_title_history` and mirrors into `_belt_history` on any live
title change. That mirror block was added deliberately (BELT-STORE-UNIFY1
comment at `:15833-15839`), and the harness measurement confirms Noah
Johnson's reign is present in both stores after the wk-1 transfer.

The asymmetry lives upstream, in the pre-gen population path.
`world_init.py:3588` captures `_history_sim.belt_history` into
`self._belt_history`. That's the only pre-gen writer to either store.
There is no matching write to `_title_history` during pre-gen — no
line in `world_init.py`, no line anywhere else. `_title_history`
starts empty at `game_bridge.py:2201` and stays empty for any
division that hasn't had a live-play title fight yet.

**Consequence, measured on this world at seed 20260918, live wk 1:**
`_belt_history[Featherweight]` carries 5 reigns (4 pre-gen + 1 live);
`_title_history[Featherweight]` carries 1 reign (the live one only).
The Champions page and record book, which read `_title_history`,
have no way to know Joseph King, Benoit Dupont, and Mikhail Popov
ever held the belt. The fighter profile, which reads `_belt_history`,
renders every reign correctly for both the deposed and the newly
crowned champion.

**Same class of finding as BELT-LINEAGE1 in the deploy #6 browser
session** ("Machado labeled 'Inaugural Champion at Season Opener' —
but Machado's own profile shows he won the belt from Steven Thompson
at CD59"). That case is a variant of the write-path gap where the
new live-play champion's reign IS in `_title_history` (like Noah
here), but the Champions page synthesized a "Season Opener /
Inaugural Champion" label because the store-lookup logic at
`get_champions_history` `:15910-15929` seeds a synthetic inaugural
reign only when `_title_history[wc]` is EMPTY. The specific label
Van saw ("Inaugural Champion at Season Opener") is that seeded
synthetic — Machado's transfer must have landed under a code path
that didn't populate `_title_history`, or the synthetic seed was
serving before Machado's transfer wrote. Either way the root is the
same: pre-gen reigns don't reach `_title_history`, so any surface
that reads `_title_history` sees an incomplete or synthetic lineage.

**Same class of finding as RECORD-BOOK1** — "Most Title Reigns" and
"Most Defenses" render populated in this measurement (not "blank"
as the docket text described from Van's browser session), but they
count ONLY live-axis reigns. On a fresh save the deploy-#6 browser
session was reading, the count is zero live-axis reigns → blank
sections. The `_get_title_records` writer at `:15112` iterates
`self._title_history.values()`; if that dict is empty the records
list is empty. Same root: pre-gen reigns don't land in
`_title_history`.

Not measured this pass:
- The `crown_initial_champion` path on `_belt_history` at `:15868`
  (fires only when a live-play title fight resolves in a division that
  has no existing champion — vacant-title claim). No such case
  occurred in this seed's first 30 weeks.
- The vacate paths at `game_bridge.py:4045-4053` (injury) and
  `:6926-6933` (player choice), both of which touch `_title_history`
  and are the subject of VACATED-REIGN1.
- The behavior of `_get_title_records` under the "Machado labeled
  Inaugural" configuration (where the seed synthesis at
  `:15910-15929` fires) — we didn't reproduce that exact seed state
  because Noah's transfer already populated `_title_history` before
  the Champions page rendered.
- Behavior across HARNESS-RNG2 non-reproducibility. This measurement
  was run once on seed 20260918. The direction (pre-gen missing from
  `_title_history`) is structural — no seed will change the writer
  gap — but the specific pre-gen reign counts per division will vary.
- What happens to `_title_history` on save/load in a world where a
  pre-gen champion has since been defeated live-play. The `save`
  path at `game_bridge.py:2977` writes whatever the dict currently
  holds; the `load` path at `:3203` reads it back. If pre-gen reigns
  are never in the dict at save time, they will never be in the dict
  at load time either.

Not on the docket: whether the write-path fix is "populate
`_title_history` from `_belt_history` at world init" or "collapse to
a single store and re-target the readers". Both are viable; the choice
is the arc's design call, not this Gate 0's finding.

## §6 Corrections and reader trace (2026-09-18, post-report)

§1 was produced by a delegated grep and contained at least one phantom:
game_bridge.py:9907 is not a `_title_history` reader (line is a
sponsor-milestone write; nearest mention is a comment at :9586).
Corrected census, self-grepped:

```
=== _title_history in cage_dynasty_web/game_bridge.py (self-grep) ===
2201: WRITER  self._title_history: Dict[str, List[Dict[str, Any]]] = {}
2275: comment (excluded — not a read/write)
2977: READER  "title_history": self._title_history,          (save)
3203: WRITER  self._title_history = data.get("title_history", {})   (load)
4058: READER  history = self._title_history.get(wc, [])      (vacate-injury)
4393: READER  r for _wc_list in self._title_history.values() (HOF)
6939: READER  history = self._title_history.get(wc, [])      (vacate-player)
9586: comment (excluded — not a read/write)
15112: READER for _wc_reigns in self._title_history.values() (record book)
15770: docstring (excluded)
15800: comment (excluded)
15801: WRITER  if weight_class not in self._title_history: self._title_history[wc] = []
15802: R/W    history = self._title_history[weight_class]
15804: R/W    history = self._title_history[weight_class]
15835: comment (excluded)
15883: comment (excluded)
15907: READER history = self._title_history.get(weight_class, []) (Champions page)

=== _belt_history in cage_dynasty_web/game_bridge.py (self-grep) ===
2278: WRITER  self._belt_history = _BH_cls()
2280: WRITER  self._belt_history = None
2363: READER  _captured_bh = _initializer.get_belt_history()  (via accessor)
2365: WRITER  self._belt_history = _captured_bh
2986: READER  "belt_history": self._belt_history.to_dict() ... (save)
3282: WRITER  self._belt_history = _BH_load.from_dict(...)   (load)
7103: READER  guard
7105: READER  _reigns_d = self._belt_history.get_fighter_reigns(...)
7298: READER  guard
7300: READER  _reigns_d = self._belt_history.get_fighter_reigns(...)
7580: READER  guard
7582: READER  _reigns_d = self._belt_history.get_fighter_reigns(...)
9574: READER  guard
9577: READER  reigns = self._belt_history.get_fighter_reigns(fighter_id)  (profile)
9585: comment (excluded)
15833: comment (excluded)
15837: comment (excluded)
15840: READER  guard
15856: WRITER  self._belt_history.title_changes_hands(...)   (live transfer)
15868: WRITER  self._belt_history.crown_initial_champion(...) (vacant claim)
15882: comment (excluded)
15884: comment (excluded)
15889: READER  guard
15890: READER  _reigns = self._belt_history.reigns.get(weight_class, [])
15893: WRITER  self._belt_history.record_title_defense(weight_class) (defense)
15897: comment (excluded)

=== world_init.py ===
_title_history: 0 hits
_belt_history:
3588: WRITER  self._belt_history = self._history_sim.belt_history  (PRE-GEN)
3604: accessor def
3606: READER  return getattr(self, '_belt_history', None)

=== routes.py: 0 hits either store ===
=== templates/: 0 hits either store ===
```

Diff against §1 of the report:
- `_title_history:9907` — was listed as READER in §1; **not in file** (real line is `self._camp_balance += bonus` inside sponsor milestone handler). PHANTOM.
- Six comments correctly excluded by §1: `_title_history` :2275/:9586/:15770/:15800/:15835/:15883; six for `_belt_history` :9585/:15833/:15837/:15882/:15884/:15897. Not deltas.
- Every other line in §1 confirmed by self-grep.

`_title_history` readers after correction: **six** — `:2977` save, `:4058` vacate-injury, `:4393` HOF, `:6939` vacate-player, `:15112` record book, `:15907` Champions page. cc's trace report to the architect (chat, 2026-09-18, not in this file) said "5, not 6" and listed six — an arithmetic slip; the correct count was six all along (the phantom would have made §1's list seven; six is what remains).

Reader trace:

| line | function | consumer | display-or-decision |
|---|---|---|---|
| 4393 | `_compute_hof_score` (called by `_induct_into_hof` year-end at :4382 + on-retire at :4478) | HOF induction threshold (score < 60 skip); news headline; persisted `_hof_inductees` record with `title_reigns` and `title_defenses` fields. Reigns count 25pt each — largest coefficient in the prestige score. | **DECISION** (news + persisted record + story-logic HOF induction) |
| 9907 | — (phantom; Explore agent misgrep, no real reader at this line) | — | — |
| 4058 | `_advance_week_impl` (25w-injury auto-vacate branch, declared :3609) | Read + mutate — closes active reign row with `is_active=False` + vacate metadata; emits vacate news. | **DECISION** (state transition on vacate) |
| 6939 | `resolve_champion_injury_decision` choice='vacate' branch (called from `routes.py:2159`) | Read + mutate — closes active reign row on player-chosen vacate; emits vacate news. | **DECISION** (state transition on vacate) |

Tier is per commit (CLAUDE.md L836): Champions-page and record-book repoints are display tier; `_compute_hof_score` repoint is engine tier (feeds news + HOF induction, 25/reign is the largest coefficient) and requires before/after HOF-score measurement, not an equivalence gate. Van ruling 2026-09-18: single canonical store, `_belt_history`.
