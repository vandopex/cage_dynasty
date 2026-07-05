# AUTOLOAD-SAVE-DIAG1

Read-only diagnostic. Scope for auto-loading the newest save on landing.

## TL;DR — surprising finding

**The feature is already shipped.** Commit `484e7f8` (July, ~10 commits before
current HEAD `bd38a2f`) merged an `AUTOLOAD-SHIP1` block into `dashboard()`
plus a `get_newest_save_slot()` picker on the bridge. CLAUDE.md's
top-of-backlog #1 entry is stale — this predates my session and never got
reconciled into the ship-history table.

End-to-end trace below confirms the code is wired correctly. What remains
is a small **coverage gap**, not a build: autoload only fires on `/`.
Bookmarks and typed URLs to any other route (`/roster`, `/training`, …)
still bounce a returning user through `/new-game`. Whether that's a real
gap depends on user behavior — most people land on `/`.

Nothing to change under this diag. Ship-or-not decision below.

---

## 1. Landing path (returning user, existing session, no game loaded)

Request flow through `routes.py`:

1. **`_ensure_user_identity` `@app.before_request`** (`routes.py:215-229`) —
   idempotent. If `session['user_id']` already exists (returning cookie),
   it's a no-op. If not, mints a fresh uuid. Skipped on `/static/*` and
   `/api/git-pull`.

2. **`dashboard()` at `/`** (`routes.py:583-602`) calls `get_bridge()`:
   - `get_bridge()` (`routes.py:234-240`) reads `session['user_id']`,
     looks it up in `app.game_bridges` (module-scope dict, `app.py:105`).
     Miss → creates a fresh `GameBridge()`, stamps `_b._user_id = uid`,
     stores it. Hit → returns existing bridge.

3. **AUTOLOAD-SHIP1 block** (`routes.py:588-602`):
   ```python
   if not bridge.game_started:
       _newest = bridge.get_newest_save_slot()
       if _newest is None:
           return redirect(url_for('new_game'))
       _result = bridge.web_load(_newest)
       if not (isinstance(_result, dict) and _result.get('success')):
           return redirect(url_for('new_game'))
       # fall through — dashboard renders on the loaded bridge
   ```

**What a returning user sees today (post-`484e7f8`)** on `/`:
- **≥1 save on disk**: autoload runs, dashboard renders their newest slot.
- **0 saves**: redirected to `/new-game`.
- **Save exists but web_load fails** (corrupt JSON): redirected to
  `/new-game`. No error surfaced to the UI — silent fallback.

**Where the "which save, if any" decision lives:** `dashboard()` (the route
handler), delegating to `bridge.get_newest_save_slot()`.

## 2. "Most recent" definition

`get_newest_save_slot()` at `game_bridge.py:3133-3157`:

- Iterates a **hardcoded slot list**: `["slot1", "slot2", "slot3", "slot4",
  "slot5", "autosave"]`.
- For each slot, resolves to disk path via `self._bridge_save_path(slot)`
  → `{saves_dir}/bridge_{uid}_{slot}.json` (`game_bridge.py:2388-2393`).
- Picks the slot with **max `os.path.getmtime()`** across existing files.
- Per-slot `try/except OSError` guards a stat race (file vanished mid-loop).

**Filesystem mtime, not a save-embedded timestamp.** This is fine because
`web_save` writes the file each time via a single `json.dump`, so mtime
tracks last-write cleanly. No timestamp-inside-save is read.

**Scoping:** every path passes through `_bridge_save_path`, which reads
`self._user_id`. The bridge's `_user_id` was stamped at `get_bridge()` from
`session['user_id']` and is not mutable via user input. Directory listing is
never used — only per-slot direct-path stats. **Cross-user reads are
impossible via this path** (would require crafting a slot name that
escapes the filename template, which is a fixed set of six strings).

## 3. New-visitor vs returning fork

The branch collapses to one signal check: `bridge.game_started`.

- **Fresh bridge** (`__init__`): `game_started = False` (`game_bridge.py:1775`).
- **After successful web_load**: `game_started = True` (`game_bridge.py:2964`).
- **After successful new_game / wizard finish**: `game_started = True`
  (`game_bridge.py:2195`, `2337`, `2347`).

The autoload block runs only when `game_started == False` AND
`get_newest_save_slot() is not None`. The two signals combine to define
the fork:

| user_id has saves? | game_started | branch |
|---|---|---|
| No | False | redirect `/new-game` (brand-new user) |
| Yes | False | web_load newest, render dashboard (returning) |
| — | True | skip autoload, render dashboard (mid-play) |

This is the correct place for the check — it's inside `dashboard()`, on the
one route explicit-in-being-the-landing-page. All other routes hand-roll
their own `if not bridge.game_started: redirect(url_for('new_game'))` guard
(see `roster()` at `routes.py:781` as a representative). See §7 for the
scope observation about that.

## 4. Isolation guardrail

Verified — autoload cannot cross-load or race another user's bridge:

- **Bridge scoping**: `get_bridge()` reads `session['user_id']` from the
  signed cookie and returns `app.game_bridges[uid]`. Every subsequent call
  inside the same request touches only that one bridge object.
- **Save-path scoping**: every disk touch goes through `_bridge_save_path`,
  which pulls `self._user_id` from the bridge instance (not from request
  input). The picker constructs six exact paths and stats them individually
  — no `glob`, no directory scan, no user-supplied filename fragment.
- **Per-bridge lock**: `web_load()` (`game_bridge.py:2632-2638`) is one of
  the six mutating operations wrapped in `with self._lock:` (RLock at
  `game_bridge.py:1773`). If two concurrent requests for the same session
  (double-tap, tab reopen) both trigger autoload, the second serializes
  on the RLock; the first sets `game_started=True`, the second reads it
  set and skips.
- **Session cookie integrity**: forgery requires `SECRET_KEY`. CLAUDE.md
  flags that as a hard PA requirement; a missing key would break identity
  system-wide long before this feature.

The **one edge worth naming**: `get_newest_save_slot()` is a pure read and
takes NO lock (docstring calls this out). A concurrent `delete_web_save`
or `web_save` for the same user in another request could race the mtime
scan. The per-slot `try/except OSError` covers the vanish case. In the
worst case the picker picks a slot whose file was overwritten mid-stat,
`web_load` reads it (still valid JSON, just fresher than expected), and
that's fine — same user, same session bridge, same identity. **No
cross-user leakage possible.**

## 5. Idempotency

The `if not bridge.game_started:` guard is the whole story. Concrete cases:

- **Mid-play, dashboard revisit**: user already played some weeks,
  clicks the dashboard link. `game_started == True` → autoload block
  skipped entirely, current in-memory state renders. **No clobber.**
- **Mid-play, browser refresh on `/`**: same as above.
- **Mid-play, Flask restart / deploy**: in-memory bridge dict wiped,
  fresh bridge created on next request with `game_started == False`,
  autoload picks the newest slot (may be the autosave written 5 weeks
  back, not the exact in-memory state — that's the deploy-recovery UX
  the feature is *for*, and is the closest reachable state).
- **Mid-wizard**: user is between `/setup/camp` and `/start-game`.
  `game_started` is still False at that point, but the wizard doesn't
  route through `/`. If the user manually navigates back to `/` during
  the wizard, autoload WOULD fire and load a prior save — clobbering
  the wizard draft. **Small edge case, not likely, not a regression
  (pre-shipping there was no autoload; the wizard-draft loss existed
  because navigating back to `/` just showed New Game either way).**

The feature is idempotent for the intended use. The wizard-back edge is
harmless polish, not a correctness bug.

## 6. Legacy-claim / cookie fresh-start interaction

Two extra fork points worth documenting since they're one hop from this
feature:

- **New browser, no cookie**: `_ensure_user_identity` mints a fresh uuid.
  This user_id has no saves under `bridge_{new_uuid}_*.json`, so autoload
  returns None → `/new-game`. Correct.
- **Van's own returning session (user_id='van')**: cookie survives across
  visits. `get_newest_save_slot()` reads `bridge_van_slot*.json` +
  `bridge_van_autosave.json` files. Correct.
- **Post-`/api/claim-legacy` bind**: token flow ends in
  `return redirect(url_for('saves_menu'))` (`routes.py:264`), NOT `/`. So
  the legacy-claim path does not go through the autoload branch. That's
  intentional — the claim flow explicitly wants the saves menu.

## 7. Scope observations (not gaps in the shipped feature, gaps in coverage)

### 7a. Autoload only fires on `/`
Bookmark to `/roster`, `/training`, `/rankings`, etc. → each route
independently checks `if not bridge.game_started: redirect('new_game')`.
A returning user with a bookmark to a non-root page still sees New Game.

**Options if this matters:**
1. Do nothing — the landing page IS `/`, most users hit `/` first.
2. Hoist the autoload block into a `@before_request` handler behind a
   path allowlist (`/`, `/roster`, `/training`, ...) — but this bloats
   the per-request path and complicates the wizard flow.
3. Change `require_game_started` decorator (`routes.py:291-298`) to run
   autoload before the redirect. Then apply the decorator to non-`/`
   routes. Cleaner but requires applying the decorator, which today is
   defined-but-never-used (grep for `@require_game_started` returns 0
   hits — dead code).

### 7b. `require_game_started` is dead code
`routes.py:291-298` defines it. Zero routes apply it — each hand-rolls
its own `if not bridge.game_started` check inline. Either apply it (with
autoload embedded) or delete it. Small cleanup, low priority.

### 7c. Silent fallback masks corrupt-save cases
If `web_load` returns `{'success': False}` (unreadable file), user gets
`/new-game` with no indication that a save existed. Real "corrupt save"
cases are rare, but a flash message on the New Game screen (`"⚠️ Your
last save couldn't be loaded — start fresh or restore from a slot"`)
would be a nice UX pass. Design call, not a bug.

### 7d. `get_newest_save_slot()` slot list is hardcoded
`["slot1"..."slot5", "autosave"]`. If the save-slot mechanism ever grows
(e.g. dated auto-slots), this needs updating. Grep for the same slot
list elsewhere finds `web_save`, `web_load`, and the saves-menu route —
they all hand-roll the same six names. Consolidating to a module-level
constant is a real-but-tiny cleanup; ship if any slot-list-touching
work goes through here again.

### 7e. CLAUDE.md backlog is stale
Top-of-backlog #1 in CLAUDE.md is exactly this feature, listed as
unshipped. Ship (`484e7f8`) predates the current CLAUDE.md edit but
was never surfaced to the ship-history table. Housekeeping fix, not
a code change: promote `484e7f8` into the table and remove the
"elevated 2026-07-03" entry.

## 8. Recommendation

Given the feature is already shipped, the actionable outputs are:

- **CLAUDE.md**: reconcile — add `484e7f8` to the ship-history table
  (`feat(session): auto-load most recent save on landing`), remove the
  "#1 elevated 2026-07-03" backlog entry.
- **Optional polish** (defer unless prompted): §7a coverage extension,
  §7b dead-decorator cleanup, §7c corrupt-save flash message.
- **No engine work required.**

If the intent behind the diag was "why does my testing still land on
New Game" — worth checking (a) does the browser have a valid `user_id`
cookie, (b) does that cookie's user_id have any `bridge_{uid}_*.json`
files under `cage_dynasty_web/saves/`. The signal path is deterministic:
if both are true, `/` autoloads.
