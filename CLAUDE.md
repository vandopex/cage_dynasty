## Ship History (compact)

Full recaps for older ships in `CLAUDE_archive.md`. Table below is reverse-chron; pre-Ship-C2 (2026-05-30) entries kept for architectural-pattern reference. `git log --oneline` is authoritative for anything between rows.

| Date | Ship | Commit | What |
|---|---|---|---|
| 2026-07-03 | TRAINING-ADVANCED-TOGGLE1 | 586fc0a | Hide floor column by default; CSS-only, floor inputs stay in DOM |
| 2026-07-03 | TITLE-TRANSFER-FIX1 | 5e4bbe1 | AI champions correctly lose belt in fallback-path fights |
| 2026-07-03 | COACH-RATING-CURVE1 | d10003c | Compress training-gain rating curve 21× → 3.4× |
| 2026-07-03 | COACH-COVERAGE1b | eaff397 | Coach cards advertise real bucket stats; single SPECIALTY_MAP source |
| 2026-07-03 | COACH-COVERAGE1a | 208608a | 7 canonical coach types with coverage guarantee |
| 2026-07-03 | LEGACY-CLAIM-FIX1 | ea595b0 | Secret-gated /api/claim-legacy replaces racy first-visitor claim |
| 2026-07-03 | MULTIUSER-ISOLATION1 | 29b0b55 | Session-scoped GameBridge dict + per-bridge lock + save-file namespacing |
| 2026-07-03 | OVR-FIX1 | 98d6c00 | Player-fighter 18-stat vector persists at creation |
| 2026-07-03 | FREEAGENT-STYLE1 | e30a883 | Free-agent list uses bridge.get_fighter (real styles, not Balanced) |
| 2026-07-03 | CARDSLOT-BACKFILL1 | 222a502 | Cosmetic Main Card backfill for weak-prelim weeks |
| 2026-07-03 | CARDSLOT-FIX-PLAYERSLOT1 | bcf69bd | accept_fight_offer routes through assign_player_fight_to_card |
| 2026-07-03 | COMPARE-LABEL1 | 2a0afed | Compare page: Wrestling → Takedowns label |
| 2026-07-03 | COMPARE-GUARD1 | a1b7c67 | Compare page: guard_work → guard (silent-0 bug) |
| 2026-07-03 | NEG-STATMIRROR1 | 256281c | Negotiation screen mirrors player style pill + stats |
| 2026-07-02 | MOBILE-SINGLECOL1 | cb83170 | Dashboard + week_results collapse to single column on phones |
| 2026-07-01 | COACH-TRAIT1 (Phase 2) | ac9a2a6 | Repair dead maintenance trait path; Taskmaster intensity-gated |
| 2026-07-01 | DASH-FEUD-REMOVE1 | c69ff04 | Remove Active Feuds dashboard card (engine untouched) |
| 2026-07-01 | DASH-CHAMP1 | 6cc9f29 | url_for('champions') → 'champions_history' — dashboard BuildError |
| 2026-07-01 | Save slots + delete | 579a0ab | 5 slots (was 3) + delete button with confirmation |
| 2026-07-01 | Fix setup_camp Jinja | dc3434e | loop.parent removed (Python 3.13 Jinja2 compat) |
| 2026-05-30 | Ship C2 | 0139e11 | Coach contracts (dumber version) — see full recap below |
| 2026-05-11 | Ship A | 9709f16 | Training report deepening — dashboard 4-week log |
| 2026-05-11 | Ship B | 411b265 | Starter contracts + founding fighter loyalty |
| 2026-05-11 | Ship #35 | e3eb35a | Player-fighter injury dashboard surface |
| 2026-05-10 | Ship G1 | 46fdfa0 | Unified slot assignment across card-build paths |
| 2026-05-10 | Ship #32 | bfe68e5 | Fighter attribute persistence (Path B) |
| 2026-05-09 | Ship C | bf448b1 | Event numbering continuity from world-gen |
| 2026-05-09 | Ship #29 | 5272ef4 | Belt history persistence |
| 2026-05-09 | Ship A (engine) | d4d0b2c | Fight engine finish rate (FI_DAMAGE_MULTIPLIER 0.32→0.36) |
| 2026-05-08 | Ship #28 | 14ec7f8 | Wire WorldInitializer into production new_game |
| 2026-05-08 | Ship #26 | e2d90e7 | Card slot assignment state-staleness fix |
| 2026-05-08 | Ship #25 | dbaab83 | Sim-seed rivalries during world-gen |
| 2026-05-08 | Ship #24 | f5c21eb | Rivalry persistence wire-up |
| 2026-05-07 | Ship #23 | 0fee7b6 | World-gen aging-during-sim |
| 2026-05-05 | Ship #22 | 9670864 | Free-agent booking UX |
| 2026-05-04 | Ship #21 | e3fa76a | Helper consolidation (_book_title_fight) |
| 2026-05-04 | Ship #20 | 73d2cd2 | AI booker lead-time integration |
| 2026-05-03 | Ship #19 | e373290 | /prospects route retired |
| 2026-05-03 | Ship #18 | 3695980 | Amateur tab Slice C Part A (visual polish) |
| 2026-05-03 | Ship #17 | fd41007 | News feed Free Agents tab |
| 2026-05-03 | Ship #16 | 7700775 | Champion injury Slice 4 (hold-path consequences) |
| 2026-05-03 | Ship #15 | e0fba25 | Signing + debut alerts |
| 2026-05-03 | Ship #14 | af14904 | Amateur tab Slice A (unified amateur ID) |
| 2026-05-02 | Champion injury Slice 3 | 2c13d0a | Player vacate-or-hold decision UX |
| 2026-05-02 | Champion injury Slice 2.5 | 33c8225 | Player vacant-title invitation |
| 2026-05-02 | Champion injury Slice 2 | b4ac430 | Auto-book vacant-title fight |
| 2026-05-02 | Earned-nickname feature | (in nickname commit) | Performance-earned nicknames |
| 2026-05-02 | Fighter profile polish | f9c2a07 | Style banner + tier-colored stats |
| 2026-05-02 | Bug AB.1 | 7914647 | watch_fight FOTN banner spillover fix |
| 2026-05-01 | Bug AB | 69ff422 | Per-fight FOTN badge spillover |
| 2026-05-01 | Champion injury Slice 0.5 | e1b14fe | Pre-fight injury gate |
| 2026-05-01 | Champion injury Slice 0.75 | c3dfd47 | Auto-vacate threshold |
| 2026-05-01 | Champion injury Slice 1 | 804938b | Champion-aware injury news |
| 2026-04-30 | Bug Z | 59193c5 | Auto-booking after player gets ranked |
| 2026-04-30 | FOTN top banner | 4736de7 | event.fotn dict populated |
| 2026-04-29 | Bug O | 7c3f8e1 | Prelim player fights running 5 rounds |
| 2026-04-29 | Bug S | c203b51 | Cooldown not applied to player-fight opponents |
| 2026-04-28 | Phase 0 | 2e169e7 | NameError fix in _simulate_ai_fights_week |
| 2026-04-28 | Bug E + G | 2123ac7 | Option P (timing alignment) |
| 2026-04-28 | Bug Q | 8c48417 | AI fight watch-link ID collision |
| 2026-04-28 | Bug R | e2360fc | Player fight event-detail rendering |
| 2026-04-27 | Multiple | (various) | OVR-out-of-rankings Phase 1, Bug F, Bug D, etc. |
| 2026-04-26 | Multiple | (various) | Slot Bug A, dashboard digest, NameError patches |

## Current deployment state

Multi-user isolation shipped 2026-07-03 (MULTIUSER-ISOLATION1 + LEGACY-CLAIM-FIX1).
Save files namespaced as `bridge_{user_id}_{slot}.json` in `cage_dynasty_web/saves/`.
Session-scoped `GameBridge` dict at `app.game_bridges`, keyed by `session['user_id']`,
lazy-created on first request per user. Per-bridge `threading.RLock` around the six
mutating operations (`new_game`, `advance_week`, `web_save`, `web_load`,
`accept_fight_offer`, `_book_fight_from_neg`).

**Required PA environment variables** (both currently set on the live app):
- `SECRET_KEY` — signs session cookies. Fallback exists but logs a security warning
  to stderr and is forgeable by anyone reading the source.
- `LEGACY_CLAIM_TOKEN` — gates `/api/claim-legacy?token=<value>` which binds a
  session to `user_id='van'`. Route returns 404 (not 403) when the env var is unset
  or the token doesn't match, so the route is invisible to anyone without the token.

**Legacy save migration already ran** on both dev and PA — `bridge_slot*.json` and
`bridge_autosave.json` were backed up (`.bak`) then renamed to `bridge_van_*.json`.
The old `.legacy_claimed` marker file (from the retired first-visitor auto-claim) is
inert — no code reads it anymore.

**Multiple saves per user** via the 5-slot + autosave system (Ship 2026-07-01). To
check current save state on any deploy: read the Save/Load page in-browser, or
`ls -lt cage_dynasty_web/saves/bridge_*_autosave.json` on the server for the most
recent by mtime. Do NOT hardcode a specific fighter name or save slot as "the"
active save — describe the mechanism, not the instance.

## Deploy workflow

`./deploy.sh` from repo root: pushes to GitHub `main` → triggers a PA webhook
that runs `git pull` in `~/cage_dynasty/cage_dynasty_web` → reloads the PA web app
via the PA API. Confirmed working end-to-end across ~20 ships between 2026-07-01
and 2026-07-03.

If the webhook returns HTTP 500 (rare, intermittent): manual fallback is `git pull`
on the PA bash console, then "Reload" on the PA Web tab.

## Top-of-backlog

**#1 (elevated 2026-07-03) — Auto-load most recent save on landing.** Blocks new-user
onboarding. Under current behavior a session with existing saves still drops on the
New Game screen when landing on `/`; users must manually go to `/saves` and pick a
slot. This matches Van's own workflow (deliberate fresh restarts) but is a bad first
impression for anyone else. Fix scope: when a session hits `/` with an unstarted
bridge, check for saves under this `user_id` and auto-load the most recent by mtime.

**Queued after #1, not scheduled:**
- **COACH-GRAPPLE-SPLIT1** — split the `grappling_coach` training bucket into
  distinct wrestling and BJJ archetypes. Sandman-grade fighter-identity work
  deferred from the 2026-07-03 coach arc.
- **Coach trait design deepening** — 16-trait system is now wired (post-Ship
  ac9a2a6) but under-tuned; some traits still don't produce visibly different
  fighter outcomes across a play session.
- **EC1 economy arc** — coach salaries are now differentiated by rating
  (post-CURVE1), giving budget vs. elite a real tradeoff. Downstream: fight
  purses, sponsorship depth, facility ROI curves.
- **SUB-rate undershoot tuning** — see `memory/sub_rate_undershoots_2026-04-28.md`.
  Pre-verify still applies against the current engine-tuning arc before shipping.
- **Older Bug X items** filed pre-multiuser (Bug H, Bug C second path, Bug T, Bug Y).
  Re-verify each against current code before shipping — several may already be closed
  by the July ship cascade.

**Deferred low-priority cleanup:**
- Sub-bug O.1 — asymmetric round override at `fight_integration.py:1228-1229`.
  Bundle with any future `fight_integration.py` touch.
- Off-week semantics contradiction — surfaced in TITLE-TRANSFER-DIAG1. Off weeks
  discard the pipeline card but the fallback path (`_simulate_ai_fights_week`)
  still generates fresh AI fights, contradicting the "no event" print. Not a
  correctness bug — a design call on whether off weeks should truly skip AI sim.

# CAGE DYNASTY — Claude Code instructions

## Project overview

Cage Dynasty is a browser-based MMA management simulation. Solo developer (Van).
Python/Flask web app at `~/Desktop/Games/cage_dynasty/cage_dynasty_web/`.
Deployment target: PythonAnywhere.

## North star

Emergent stories players tell unprompted. The reference is "Sandman" — an AI
rival in Leather (boxing management game) who fought the player three times,
became friends at feud Stage 30, never won a title, and got a player-written
story posted to Reddit. Nobody scripted it. The simulation made them care.
That's the bar.

## Design principles

**OVR is player-facing only, never engine input.** Overall Rating (`overall_rating`)
is a UI summary stat. It must NOT be used as input to any simulation system —
rankings, matchmaking, AI decisions (signing, contracts, retirement, trash talk),
fight outcomes, card slot assignment, title eligibility. Real MMA doesn't have
OVR. Rankings are earned through wins, recent form, and quality of opposition.
Engine work that needs a "strength number" must derive it inline from per-attribute
stats (striking, wrestling, cardio, etc.) — never reach for OVR as a shortcut.
See `memory/principle_OVR_player_facing_only.md` for full rationale and audit tactic.

## Architecture — VERIFIED April 2026 (do not trust other descriptions)

The web app is NOT a thin shim over the CLI engine. It is a substantially
independent codebase that shares a folder tree with the CLI by historical
accident.

**Live for the web app:**
- Flat .py files at `cage_dynasty_web/` root (`game_bridge.py`, `routes.py`,
  `game_state.py`, `fight_engine.py`, `fight_integration.py`,
  `card_builder.py`, `matchmaking.py`, `aging.py`, `amateur.py`,
  `facilities.py`, `maintenance_training.py`, `interviews.py`, `news.py`,
  `styles.py`, `world_init.py`, `name_database.py`)
- Stub packages: `cage_dynasty_web/core/`, `entities/`, `systems/` — small
  re-exporters that point back to the flat files above
- Top-level `cage_dynasty/simulation/` and `cage_dynasty/narrative/` —
  reached by accident: the symlinks `cage_dynasty_web/simulation` and
  `cage_dynasty_web/narrative` are BROKEN (relative target wrong), Python
  silently falls through to top-level via sys.path

**Dead from the web app's view:**
- Top-level `cage_dynasty/core/`, `entities/`, `systems/` — never imported
  by the web app. CLI tools use them. Web app does not.
- The CLI's `core/game_state.py` and web's flat `game_state.py` have
  diverged (~37 lines diff, drifted name generation). Sibling forks.

### Where to edit what

| Change | Edit this file |
|---|---|
| Game state, fighter records, name gen | `cage_dynasty_web/game_state.py` |
| Fight engine constants | `cage_dynasty_web/fight_engine.py` |
| Bridge / route handlers | `cage_dynasty_web/game_bridge.py`, `routes.py` |
| Card / slot assignment | `cage_dynasty_web/card_builder.py` |
| Matchmaking, training, aging | flat file at `cage_dynasty_web/` root |
| Templates | `cage_dynasty_web/templates/*.html` |
| Anything CLI-only | top-level `core/`, `systems/`, `entities/` |

### Known hazards

- Two parallel `game_state.py` files. Editing one does not update the other.
- Broken symlinks load top-level packages by accident. Don't "fix" them
  without verifying behavior first.
- Flat-first import loop: `from foo import x` finds `cage_dynasty_web/foo.py`
  before `cage_dynasty_web/foo/__init__.py`, before top-level. Adding a flat
  file with a name that collides with a package shadows the package.
- `types.py` shadows stdlib `types`. Use built-in `dict`, `list`, `set` —
  never `Dict`, `List`, `Set` type hints.
- WebFighter dataclass crashed once because fields with defaults were placed
  before fields without. Always read the whole class before adding fields.
- **CLI `fight_engine.py` manual constants on PA** (unverified). The PA copy
  reportedly has manually-appended engine constants not in the repo. Working
  tree matches HEAD as of 2026-07-01 audit; PA-side has not been re-audited
  since. Anything that changes fight_engine constants should be checked against
  PA's copy before deploy.
- **PA `wsgi.py` manually edited** (unverified). Diverged from repo `wsgi.py`
  during earlier deploy debugging. Repo file assumed authoritative but PA-side
  not confirmed. Diff against PA's `/var/www/*_wsgi.py` before touching
  WSGI-loaded modules.
- **Multi-user env-var dependencies (post-2026-07-03).** `SECRET_KEY` unset →
  cookies forgeable, session identity broken. `LEGACY_CLAIM_TOKEN` unset →
  `/api/claim-legacy` becomes a 404 (safe default). Any new PA deployment or
  environment migration needs both set BEFORE the first request or Van's own
  session can't reach his save.
- **`/api/claim-legacy` is a one-time bootstrap, not a repeatable pattern.**
  It was built to solve the specific transition from single-tenant to multi-user.
  Do NOT use it as a template for future "let admin log in as user X" flows —
  it's a spent mechanism. Better patterns for admin work: signed magic links,
  short-lived JWTs, or a proper login route.

## Recurring architectural pattern: "data exists but doesn't reach the surface"

Seven project instances. Recurring lesson: data integrity is necessary
but not sufficient — each rendering surface and persistence layer
needs intentional reading. When a system iterates a dict, audit
every code path that writes to that dict.

| Ship | Layer | Pattern direction |
|---|---|---|
| #29 (5272ef4) | Persistence | Belt history → wired save/load |
| C (bf448b1)   | Persistence | Event numbering → read from initializer |
| #32 (bfe68e5) | Persistence | Fighter attributes → wired world-gen population |
| #35 (e3eb35a) | UI          | Injury state → wired template read |
| B (411b265)   | State       | Starter contract → wired the missing writer (inverse) |
| A (9709f16)   | State + UI  | Training data → new persistence layer + dashboard |
| C2 (0139e11)  | State + economy | Coach salary → wired to economy + new contract layer |

## Workflow

Before editing any unfamiliar file:
1. Read it. Don't edit from memory.
2. If it's a dataclass, read the WHOLE class — defaulted fields must come
   AFTER non-defaulted fields.
3. If you're not sure where a function lives, trace the import:
   "what file is loaded when X is imported from Y? read the sys.path setup."

After editing a .py file:
1. Run `python3 -c "import ast; ast.parse(open('FILE').read())"` to syntax-check.
2. Show me a diff. I want to see what changed before declaring done.

I will:
- Restart Flask myself. You don't run servers.
- Test in the browser and report terminal output.
- Multi-user is live (post-2026-07-03): save slot names are `bridge_van_*.json`.
  Don't hardcode a specific slot as "the main save" — describe the mechanism
  (`bridge_{user_id}_{slot}.json`, 5 slots + autosave per user) or read the
  Save/Load page for the current session's most recent by timestamp.

## Communication

- Direct, concise. Match my energy.
- Diagnosis before code. Tell me the cause before writing the fix.
- Working copy discipline. Always read the file from disk before editing.
- Fix the engine, not the output. No band-aids. Find root cause.
- "Be proactive about crashes" — when I say this, triple-check spacing,
  imports, dataclass field ordering, name shadowing. Predict what will
  break before I find out at runtime.
- I will interrupt if you go the wrong direction. Don't take it personally.

## Do not

- Do not run the Flask server. I run it.
- Do not commit anything. No git operations unless I explicitly ask.
- Do not "improve" code I didn't ask you to touch.
- Do not flatten folder structure or move CLI files.
- Do not use `Dict`/`List`/`Set` type hints (types.py shadows stdlib).
- Do not edit top-level `core/`, `entities/`, `systems/` if the goal is to
  affect the web app — those don't reach it.

## Current top-of-list

See "Top-of-backlog" section near the top of this file (rewritten 2026-07-03).
The April-May items previously listed here (FOTN wire, fighter profile polish,
card-builder slot assignment) all shipped and were removed to prevent stale
references. Historical ship recaps are in `CLAUDE_archive.md`.

## Key constants (don't change without telling me)

- `cage_dynasty_web/fight_engine.py`: `DAMAGE_MULTIPLIER = 0.55`
- `cage_dynasty_web/fight_integration.py`: `FI_DAMAGE_MULTIPLIER = 0.32`
- Submission threshold: 70.0
- Rankings: `MAX_MOVE = 3`, `NEW_ENTRY_CAP = 8`
- Contract: `HOLDOUT = 25`, `WALKOUT = 10`, `HOLDOUT_WINDOW = 4 weeks`

## Terminal diagnostics (for tuning)

- 📊 [DFC N] — fight card summary (KO/TKO/SUB/DEC counts)
- 🤕 [INJURY REPORT] — weekly injury load
- 📋 [AI CONTRACT] — expirations
- 🥊 [AI SIGNING] — signings with personality scores
- 📈 [RANKINGS] — top-5 entries
- 😐 [MORALE] — fighter morale below 50


- CLI fork (`core/game_state.py`) has a country/name mismatch bug:
  fighter assigned name from country pool but `country` field re-rolls
  from a 5-element short-code list. Web fork is correct. Do not consolidate
  forks without auditing downstream `country == "..."` comparisons.

## Archive

Detailed ship recaps from before 2026-05-23 live in `CLAUDE_archive.md`
at the project root. That file is for historical reference — Claude
Code does not auto-load it. Open it manually when researching past
ships' diagnosis details or architectural patterns.
