## Ship History (compact)

Full recaps for older ships in `CLAUDE_archive.md`. Most recent 7 days kept in full below.

| Date | Ship | Commit | What |
|---|---|---|---|
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

## Shipped 2026-05-30

### Ship C2 — Coach contracts (dumber version of fighter contracts)

First ship after a ~2.5 week break. Closes pre-existing dead-code
bug (coach salary stored but never deducted) and adds parallel-
but-simpler contract system: coaches as financial-pressure system,
not relationship system.

**Two morale triggers only:** underpaid (salary < 85% market) and
skipped paychecks (balance insufficient to cover salary). No W/L
morale, no holdout, no severance. Asymmetric from fighters by
design — fighters give you a window to fix things; coaches give
you a final straw moment.

**New UI surfaces:** Facility page Head Coach panel + new
/coach/hire page with tier-gated contract length picker.

**Architectural pattern instance #7** of "data exists but doesn't
reach the surface" — dead-code-with-promise subvariant. Salary
was stored AND surfaced to player at setup, but the runtime never
read it. Three-way gap closed.

**Tier 2 verified:** fire flow + hire flow end-to-end. Long-term
quit triggers (underpaid, skipped paychecks) deferred to natural
play.

**Next:** Corner advice during player fights (the other stated
pre-deploy must-have).

## Next session priority
**Bug AA — DOWNGRADED 2026-04-30.** Architectural gap confirmed at `game_bridge.py:1743-1758`
(reads `_scheduled_fights` only), but Bug Z's fix neutralized the live reproduction path —
no code path today writes player fighters into `_upcoming_cards`, so the gap is dead under
current code. Revisit only if a concrete failure surfaces or if a future feature reintroduces
a player-fight write to `_upcoming_cards`. Not shipping defensive code for a hypothetical.
See `memory/bug_AA_offer_queue_doesnt_reconcile_2026-04-29.md`.

**Filed: challenge_fighter same-family gap, harmless under current code.** `game_bridge.py:5166-5173`
reads `_scheduled_fights` only when validating challenge target. UI gates the Challenge button via
`scheduled_map` (routes.py:875-886) which reads both sinks, so unreachable in normal play. Defensive
note for future UI work — any new challenge entry point that doesn't reuse `scheduled_map` would
expose the gap. Same UI/backend predicate-source-divergence family as Bug AA. See
`memory/challenge_fighter_harmless_gap_2026-04-30.md`.

Then: Pre-gen world history (Phase 2 of OVR-out-of-rankings) — `_generate_initial_history`
in `game_state.py` is currently a trivial stub. Either build engine-driven pre-gen there
or wire up the dormant `world_init.HistorySimulator`. Decision needed at session start.

Also queued: Bug H (AI offer skips gameplan — adjacent to Z/AA, may bundle), Bug C second
path, Bug T (amateur tournament audit — not a fix, system verification), Bug Y (talent
rarity rebalance — camp start only, design questions first), SUB-rate undershoot tuning
(see `memory/sub_rate_undershoots_2026-04-28.md`).

Deferred low-priority cleanup: Sub-bug O.1 (asymmetric round override at fight_integration.py),
line 7923 redundant slot check, Sub-bug S.1 (rankings update missing in `_run_real_engine`),
Sub-bug S.2 (`_fighter_data` mirror), Sub-bug S.3 (news headline — verify symptom first).
Bundle whenever `fight_integration.py` or `_run_real_engine` is touched for another reason.
See `CLAUDE_NOTES/2026-04-26-slot-fix-followup.md`.

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
- Save to slot3 (main save).

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

1. **DONE 2026-04-27** — Wire FOTN module to UI. Verified in play-test (FOTN headlines rendering on dashboard for Watanabe-Murphy Wk11 and Shavkat-MacDonald Wk13).
2. **DONE 2026-05-02** — Fighter profile UI polish. Five-component bundle shipped at commit `f9c2a07`: style-class banner with family taglines, promoted nickname rendering, 4-quadrant accent-colored stat blocks (Striking=red / Physical=amber / Grappling=blue / Mental=teal), W(KO)-L(KO)-D record format. Verified across striker / grappler / hybrid / champion profiles. Nickname rendering ships dormant — generation/wiring filed at `memory/nickname_population_investigation_2026-05-02.md` for next session.
3. Card builder slot assignment — `calculate_matchup_score` and `assign_slot`
   already exist in `cage_dynasty_web/card_builder.py`, but the bridge
   defaults everything to prelim. Need to wire them.

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
