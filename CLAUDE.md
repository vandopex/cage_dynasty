## Shipped 2026-04-29
- Bug O (verified): prelim player fights running 5 rounds. `_run_real_engine` at `game_bridge.py:7922` was setting `is_main=True` for any player fight regardless of `card_slot` — conflated "player participation" with "main event status." This forced 5-round FightConfig for all player fights (the asymmetric upgrade-only round override at `fight_integration.py:1228-1229` then locked it in). Fix: remove the `or fight.get("is_player_fight", False)` clause from line 7922. Player fights now respect their slot semantics. Commit `7c3f8e1`. Verified: Raj Panyawong (player, prelim) won SPLIT DEC after R3; AI prelims max R3; title fights still 5 rounds (Oscar Gane DEC R5). No regressions. Same two-path-merger pattern as Bug R, Bug Q, Phase 0 — fields/flags diverging between player and AI paths. AI path was already correct.
- Filed: Sub-bug O.1 (`fight_integration.py:1228-1229` asymmetric upgrade-only round override — currently harmless post-Bug-O, defense-in-depth cleanup deferred). Tech-debt note: `game_bridge.py:7923` redundant slot check after `is_main` is already computed at 7922 — cosmetic cleanup. See `memory/sub_bug_O1_engine_round_override_asymmetric.md` and `memory/tech_debt_game_bridge_7923_redundant_slot_check.md`.

## Shipped 2026-04-28
- Phase 0: NameError fix in `_simulate_ai_fights_week`. Two latent `fight` references at lines 6229 and 6285 were causing silent engine fallback (line 6229 inside try/except — every AI fight via this path was silently using score-based fallback) and a crash that derailed yesterday's Bug E/G attempt (line 6285). Replaced with local `is_title` derivation and inline dict literal. Side effect: AI fights via this path now use the real engine. Commit `2e169e7`.
- Bug E + G (verified): timing alignment via Option P. Player-fight simulation block moved to AFTER the week increment so both player and AI fights tag with the same post-advance week. Merge logic at lines 1326-1344 now actually matches; player fight appears in DFC card lineup AND on its event's recap. Single structural move, no source_week ceremony, no FOTN tag change. Commit `2123ac7`. Verified on fresh game: Carlos Gonzalez fight at DFC 3 appears on Week 3 recap + DFC 3 card lineup; FOTN headlines tagged Week 3; rank deltas working; AI fights firing normally.
- Filed: Bug O (prelim round count) — Carlos Gonzalez prelim fight ran R4 (should max R3 for prelims). Filed for next session diagnosis. See `memory/bug_O_prelim_round_count_2026-04-28.md`.
- Bug Q (verified): AI fight watch links collision fixed. `_make_scheduled_fight:7481` used `f1.fighter_id[:8]` which truncated to the `'fighter_'` prefix (exactly 8 chars) — every AI fight on a given week resolved to identical URL `/watch-fight/fight_N_fighter__fighter_`. Fix: removed `[:8]` slices, use full fighter_ids matching player-fight ID convention. Commit `8c48417`. Caveat: past archived events retain broken IDs (no migration).
- Bug R (verified): player fight rendering on event detail page fixed. `_simulate_fight` built result dict without `card_slot`, so player fights merged into `ai_event.fights` via Option P had no slot attribute and fell through to the unslotted fallback render (flat string "TKO X def. Y"). Fix: add `card_slot` to `_simulate_fight`'s result dict, default `'prelim'` matching `_simulate_card_fights:6057`. Commit `e2360fc`. Pre-existing latent bug unmasked by Option P — same pattern as Phase 0's NameError.
- Filed: Bug T (amateur tournament system audit, NOT a fix task), Bug S (cooldown — HIGH priority), Bug Y (talent rarity rebalance — camp-start only, not pre-gen). See respective memory files.

## Shipped 2026-04-27
- Bug C (partial): champion-self-fight contender loop guarded — but a second code path still fires it (re-confirmed in play-test, see memory).
- Bug D (verified): media.py randrange crash fixed (`min(3, wins)` clamp).
- Injury rates tuned: 5-change calibration to `cage_dynasty/systems/injury.py` — verified ~5/wk new injuries, 0 new severe across 35+ fights.
- Bug F (verified): camp record + player-result headlines now update across all 4 fight paths via `_apply_post_fight_camp_record` helper.
- FOTN wiring confirmed already done (CLAUDE.md TODO #1 marked DONE).
- New design principle added: OVR is player-facing only, never engine input. See "Design principles" section below.
- is_title crash fix in `_maybe_generate_inbound_offers` (use-before-assign at line 1800; assignment moved up).
- OVR-out-of-rankings Phase 1 (verified): 7-diff refactor — rank_score formula no longer reads OVR, drops streak term, bumps recency + ranked_wins weights; min-fights threshold raised to 5/3; `best_rank` field on FighterRecord with returning-contender NEW_ENTRY_CAP exemption; re-rank-on-load via `bypass_clamp=True`. Verified on slot3 LHW ladder — high-OVR thin records correctly unranked, low-OVR veterans correctly ranked. Phase 2 (pre-gen world history) is the priority next session.
- Bug I — championship phrases firing on non-title fights: `commentary.py:LATE_ROUND_CONTEXT` content-cleaned (selector was already gating correctly; pool itself contained title-themed phrases). Two phrases swapped for neutral alternatives.
- Bug K — standing-finish commentary on grounded fighters: `commentary.py:FINISH_SEQUENCE["hurt_followup"]` content-cleaned. Two standing-only phrases ("WOBBLES! POUNCES!", "THE LEGS ARE GONE!") swapped for neutral alternatives. Structural fix (position-aware selector signature) deferred — see `memory/tech_note_finish_sequence_position_aware.md`.
- Bug L1 — champion injury indicator on rankings: `templates/rankings.html` shows "🤕 INJURED — Xw out" next to champion name when `champion.is_injured`. WebFighter already carries injury fields; pure template-side change. Visibility prelude to Bug L (interim title system) — interim infrastructure NOT built.

## Shipped 2026-04-26
- Dashboard digest: bare except replaced with logged version
- is_champion NameError patched in _convert_real_fighter
- Negotiation routes hardened with .get() guards (3 sites)
- Slot inflation Bug A: rank-floor now gated on matchup_credible

## Next session priority
**HIGH — Bug S** (cooldown not applied to player-fight opponents). Matchmaking integrity
issue: AI fighters who lose to the player are immediately re-selectable (no cooldown)
while AI-vs-AI losers get proper cooldowns. Possible Option P regression OR latent
pre-existing bug exposed by playtest. Fix before any deeper rivalry/matchmaking work.
See `memory/bug_S_player_opponent_cooldown_missing_2026-04-28.md` for diagnostic framing.

Then: Pre-gen world history (Phase 2 of OVR-out-of-rankings) — `_generate_initial_history`
in `game_state.py` is currently a trivial stub. Either build engine-driven pre-gen there
or wire up the dormant `world_init.HistorySimulator`. Decision needed at session start.

Also queued: Bug H (AI offer skips gameplan), Bug C second path, Bug T (amateur tournament
audit — not a fix, system verification), Bug Y (talent rarity rebalance — camp start only,
design questions first), SUB-rate undershoot tuning (see `memory/sub_rate_undershoots_2026-04-28.md`).
Deferred low-priority cleanup from Bug O ship: Sub-bug O.1 (asymmetric round override) and
line 7923 redundant slot check — bundle whenever `fight_integration.py` or `_run_real_engine`
is touched for another reason.
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
2. Fighter profile UI polish — Leather-style screenshot-worthy stat blocks,
   bold color-coded stats, prominent nickname, fighting style as character
   class, KO record format like `24(20)-1-0`.
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