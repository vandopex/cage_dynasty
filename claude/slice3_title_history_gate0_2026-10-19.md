# Slice 3 Gate 0 — `_title_history` retirement census (2026-10-19)

Base commit: b6ed6fe. Read-only against the engine. Grep pattern used throughout:
`git grep -n '_title_history\|title_history' -- 'cage_dynasty_web/*.py' 'cage_dynasty_web/templates/*.html' 'narrative/*.py' 'claude/tools/*.py'` — 14 hits, all in `cage_dynasty_web/game_bridge.py`; zero in templates, routes, narrative, or claude/tools.

## 1. Occurrences table

| file:line | R/W | What it does | `_belt_history` already serves this? |
|---|---|---|---|
| game_bridge.py:2201 | W | `GameBridge.__init__` — init empty dict `self._title_history: Dict[str, List[Dict[str, Any]]] = {}` | **Y** — same `__init__` block builds `self._belt_history = _BH_cls()` at :2278-2280 (lazy fallback None at :2282). |
| game_bridge.py:2275 | — | Comment ("legacy parallel store, retirement pending (TITLE-KEYS1)") touched at 1791962. No read/write. | — |
| game_bridge.py:2977 | W | `web_save` — serializes `self._title_history` under key `"title_history"` in the save dict. | **partial** — `web_save` at :2986 serializes `self._belt_history.to_dict()` under key `"belt_history"`. Both stores persist, independently. |
| game_bridge.py:3203 | R | `web_load` — `self._title_history = data.get("title_history", {})`. Default `{}` on absent key. | **partial** — `web_load` at :3282 restores `self._belt_history = _BH_load.from_dict(data["belt_history"])`. Both stores restore independently. |
| game_bridge.py:4060 | R→W | Injury auto-vacate — reads `self._title_history.get(wc, [])`, then mutates `history[-1]` (is_active=False, lost_week, lost_event="Vacated (injury)", lost_to_name="Vacated", lost_method="Injury"). | **Y** — `self._belt_history.vacate_belt(...)` on the same code path at **:4057** (added by 1791962, event_name = `_dfc_label(current_week)` by 9418952). Writes identical fields. |
| game_bridge.py:6944 | R→W | Player-vacate (`resolve_champion_injury_decision`) — reads `self._title_history.get(wc, [])`, then mutates `history[-1]` (is_active=False, lost_week, lost_event="Vacated (player choice)", lost_to_name="Vacated", lost_method="Injury (vacated)"). | **Y** — `self._belt_history.vacate_belt(...)` on the same code path at **:6943** (added by 1791962, event_name = `_dfc_label(self._game_state.week_number)` by 9418952). |
| game_bridge.py:9591 | — | Comment inside `get_fighter_reigns` — "when it eventually is, this parse handles it uniformly". No read/write. | — |
| game_bridge.py:15780 | — | Docstring on `_record_title_result` — "Record a title fight result into _title_history and update division.champion_id and fighter.is_champion flags." | — |
| game_bridge.py:15810 | — | Comment "# Record into _title_history". | — |
| game_bridge.py:15811 | R | Membership check `if weight_class not in self._title_history:`. | **Y** — `self._belt_history.reigns` is pre-initialized with `{wc: [] for wc in WEIGHT_CLASSES}` at world_init.py:1945, so no per-wc init needed on the `_belt_history` side. |
| game_bridge.py:15812 | W | Lazy per-wc init `self._title_history[weight_class] = []`. | **Y** (structural equivalent as above). |
| game_bridge.py:15814 | R→W | Reads list, then two branches: (a) new champion — closes previous reign's is_active/lost_week/lost_event/lost_to_name/lost_method AND appends a new reign dict (champion_id, won_week, won_event, won_from_name, won_method, successful_defenses, is_active); (b) defense — increments `successful_defenses` on the active reign. | **Y** — BELT-STORE-UNIFY1 writes mirror into `_belt_history` on the same path: `self._belt_history.title_changes_hands(...)` at **:15866** (new-champ with old champ), `self._belt_history.crown_initial_champion(..., won_method="Won Vacant Title (…)")` at **:15878** (new-champ from vacant), `self._belt_history.record_title_defense(weight_class)` at **:15903** (defense). |
| game_bridge.py:15845 | — | Comment inside `_record_title_result` — "sync with _title_history + division.champion_id". | — |
| game_bridge.py:15893 | — | Comment inside `_record_title_result` — "the profile's reign card increments alongside _title_history". | — |

**Summary**: three substantive non-save/load write sites (`:4060`, `:6944`, `:15814`), one structural init (`:2201`), one lazy per-wc init (`:15812`). Every substantive write already has a paired `_belt_history` write on the same code path (added by BELT-STORE-UNIFY1 + VACATED-REIGN1 1791962). The structural inits have `_belt_history` equivalents at bridge `__init__` (:2278-2280) and `BeltHistory.__init__` (world_init.py:1945). The save/load pair at :2977/:3203 persists `_title_history` independently.

## 2. Save/load pair — load-time behavior

- **Write** (`:2977`): `"title_history": self._title_history,` — top-level key in the save dict.
- **Read** (`:3203`): `self._title_history = data.get("title_history", {})` — default `{}` on absent key. So an older save without the key loads as a fresh empty dict; later reads/writes operate on `{}` until the next title fight / vacate populates it.
- **Any other code read of the loaded `data` dict after :3203?** No. `data["title_history"]` / `data.get("title_history")` appears only at :3203. Downstream code reads `self._title_history` (the already-copied-in reference), not `data`. The in-memory references diverge from the save-dict object the moment this line runs.
- **Belt-history pair for comparison** (`:3282`): `self._belt_history = _BH_load.from_dict(data["belt_history"])` — subscript access (not `.get`), inside a `try/except` block starting at :3281, so a missing key raises `KeyError` and the except branch leaves `self._belt_history` at whatever `__init__` set.

## 3. Non-save/load writes — same-path `_belt_history` equivalence at HEAD

| site | `_title_history` write (R→W) | `_belt_history` write on same path |
|---|---|---|
| Injury auto-vacate | `:4060` reads+mutates — closes reign | `:4057` `self._belt_history.vacate_belt(...)` (`event_name=self._dfc_label(current_week)`, `reason="Vacated (injury)"`) |
| Player-vacate | `:6944` reads+mutates — closes reign | `:6943` `self._belt_history.vacate_belt(...)` (`event_name=self._dfc_label(self._game_state.week_number)`, `reason="Vacated (player choice)"`) |
| `_record_title_result` new-champ (vs reigning old champ) | `:15814` closes previous reign + appends new reign dict | `:15866` `self._belt_history.title_changes_hands(...)` |
| `_record_title_result` new-champ (vacant title) | `:15814` appends reign dict with `won_from_name=None` | `:15878` `self._belt_history.crown_initial_champion(..., won_method="Won Vacant Title (…)")` |
| `_record_title_result` successful defense | `:15814` increments `successful_defenses` | `:15903` `self._belt_history.record_title_defense(weight_class)` |

Every substantive `_title_history` write has a paired `_belt_history` write on the same code path at HEAD. Retiring the `_title_history` writes would not lose any state that `_belt_history` doesn't also carry — modulo field coverage differences (e.g. `_title_history` carries `lost_to_name="Vacated"` as a literal string, `_belt_history.vacate_belt` sets `lost_to=None, lost_to_name=None, lost_method=reason`; readers that want "Vacated" as a loss-opponent name would see None instead and need an is-vacate check via `lost_method` presence).

## 4. Readers that produce player-visible output

**None found.**

Grep patterns:
- `git grep -n '_title_history\|title_history' -- cage_dynasty_web/routes.py` → **0 matches**.
- `git grep -n '_title_history\|title_history' -- 'cage_dynasty_web/templates/*.html'` → **0 matches**.
- `git grep -n '_title_history\|title_history' -- 'narrative/*.py' 'claude/tools/*.py'` → **0 matches**.
- All 14 occurrences in the codebase are inside `cage_dynasty_web/game_bridge.py`: 2 structural inits (:2201, :15812), 1 save (:2977), 1 load (:3203), 3 substantive writes (:4060, :6944, :15814), 1 membership check (:15811), 5 comments/docstrings (:2275, :9591, :15780, :15810, :15845, :15893 — count 6 if the file-local docstring at :15780 is counted).

Player-visible surfaces that *used to* read `_title_history` have all been repointed to `_belt_history` as part of the BELT-HISTORY arc:
- **Hall of Fame** — `_compute_hof_score` reads `_belt_history` (HOF-REPOINT1 at `0c4bfb6`, 2026-09-21). Was `_title_history`.
- **Record Book** — `_get_title_records` reads `_belt_history` (RECORD-BOOK-REPOINT1 at `6540d3c`, 2026-09-19). Was `_title_history`.
- **Champions page** — `_get_division_lineage` reads `_belt_history` (CHAMPIONS-PAGE1 at `25adadd`, 2026-09-19). Was `_title_history`.
- **Fighter profile reign cards** — read via `bridge.get_fighter_reigns(...)` at `:9570-9610`, which iterates `self._belt_history.get_fighter_reigns(fighter_id)`. Never read `_title_history`.

`_title_history` is write-only from the player's perspective at HEAD: three internal mutation sites, one save, one load, zero readers that surface to the UI. The store is a vestigial second copy of state that `_belt_history` already holds, kept persistable in save files for backwards compatibility.

**Implications for Slice 3 ("retire the writes")**:
- Retiring the three substantive writes (:4060, :6944, :15814) is behaviorally safe at HEAD — no reader is listening.
- Save compatibility is the only concern: an older save that reaches live code expecting `self._title_history` populated could, in theory, break on an internal invariant. Grep shows there's nothing to break — the only internal consumers of `self._title_history` are the three write sites themselves (closing a reign requires having opened one), save (writes whatever's in memory), and load (unconditional `data.get(..., {})`). A `_title_history = {}` left permanently empty is behaviorally identical to a cold start with no title fights.
- Decision point for Slice 3: delete the writes entirely vs. keep them for save-roundtrip visibility (debugging/forensics). The second option bloats save files; the first requires nothing beyond deleting ~20 lines across three sites + the save/load keys.

## 5. Measured — 92bd7fa
- Edit: −74/+1, grep '_title_history|title_history' in cage_dynasty_web/ = 0, py_compile clean.
- Equivalence (the discriminating instrument, not an md5): claude/tools/save_invariants.py --seed 20260921 --weeks 0 --dump on HEAD (b6ed6fe, via stash) and on the edit — 286/286 pre-gen fighters, 0 differing rows; 34/34 _belt_history reigns, 0 diffs on (champion_name, won_week, won_method, successful_defenses, lost_week, lost_method, won_from_name, lost_to_name). Dumps outputs/vacated_reign1/dump_slice3_{head,edit}.json (untracked). A serialized-dict md5 was tried first and differs across processes — uuid4 ids, SAME SEED — and is not an equivalence gate for this store.
- Save round-trip: to_dict equal before/after web_load; "title_history" absent from the new save. Legacy: newest save carrying the key loaded, 21 reigns restored, key ignored. lost_event_gate unchanged. 12-week smoke clean.
- HARNESS-ENV1 evidence: save_invariants printed a SIMULATION-SHIM FAILED line ("cannot import name 'Gameplan'") alongside a success line. Same environment both sides so the comparison stands; whether the tool runs the production engine is that docket's question.
- TITLE-KEYS1 closed: nothing creates the empty keys anymore.
