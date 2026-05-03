## Shipped 2026-05-01
- Bug AB (verified): per-fight FOTN badge spillover on event recap surfaces. Old buggy FOTN writer (pre-commit 56bf807) wrote `is_fotn=True` on every fight without clearing losers — slot3 events 1-30 had the corruption persisted on disk; events 31+ clean post-fix. Three template surfaces (`event_detail.html:80`, `week_results.html:153`, `archives.html:59`) read `fight.is_fotn` directly and rendered every old-event fight as FOTN. Fix: switched all three to derive from `event.fotn.fight_id == fight.fight_id` (event-level source of truth, populated by 2026-04-30's FOTN top-banner fix and `None` for legacy events). Self-fixes corrupted historical data without save migration — `event.fotn` is None for old events, so the conditional evaluates False everywhere → no badges rendered. New events match exactly one fight. Three template-only edits, identical pattern. Commit `69ff422`. Verified across all three surfaces × old/new events. Same "parallel sink / source of truth" architectural family as Bug Z and Bug AA.
- Diagnostics throughout the Bug AB hunt: two TEMPORARY-marked print blocks (FOTN block per-week + load-time audit at `web_load`) added to game_bridge.py during diagnosis, never committed (uncommitted instrumentation by design). Removed after verification — working tree returned to HEAD state, no removal commit needed.
- Bug AB.1 filed (NEW, NOT FIXED): `watch_fight.html:43` has the same FOTN spillover vulnerability shape but requires a ROUTE-level change because `routes.py:2010-2067` only passes `fight` to the template, not the containing `event`. Lower priority — single-fight context means spillover isn't visible the same way (no per-row comparison). Fix shape (route + template, ~10 lines) sketched in memo. See `memory/bug_AB1_watch_fight_fotn_spillover_2026-05-01.md`.
- Champion injury Slice 0.5 (verified): scheduled fights bypassed the injury filter that already guards new card construction at `game_bridge.py:7299` — champion auto-booked for a defense, gets injured between scheduling and event firing, fight ran with injured champion. Same hole on AI-vs-AI title defenses. Fix: three-site bundle adding `is_cleared_to_fight` checks at `advance_week:1259` (player loop), `_simulate_card_fights:5979` (AI card loop), `_simulate_ai_fights_week:6228` (AI fallback pool filter). Two patterns — loop-level `continue` skip on player+AI loops, filter-level exclusion on the fallback pool (mirrors existing card-builder filter at line 7299). Commit `e1b14fe`. Verified end-to-end on slot3: Lucas Adesanya (LGT champ) injured wk 35-36 → no defense booked, contenders auto-paired against each other; toe sprain cleared wk 37 → wk 38 ladder shows defense vs Freddie Johnson II at DFC 44 with no player intervention. Gabriel Costa fight-induced injury also gated correctly. All three guards short-circuit cleanly when injury system unavailable.
- Champion injury Slice 0.75 (verified): bumped pre-existing auto-vacate threshold at `game_bridge.py:1448` from 8 weeks to 25 weeks. Old threshold conflicted with design spec — Severe injuries (9-24w) auto-stripped belts that should hold pending player choice (Slice 3 work). New threshold cleanly demarcates Severe (≤24w, hold) from Career-level (≥25w, auto-vacate per spec). Two-line change (comment + value), no logic added. Commit `c3dfd47`. Filed deferred work: counter rename tech debt (`_champ_weeks_since_defense` actually tracks "weeks consecutively injured"; bundle when auto-vacate block is next touched) at `memory/tech_debt_champ_weeks_counter_naming_drift_2026-05-01.md`; Slice 5 sub-task to update existing vacate headline text ("interim title fight to be announced" references the unbuilt interim system) — amended into design spec at `memory/design_champion_injury_handling_2026-04-30.md`.
- Champion injury Slice 1 (shipped): champion-aware injury news at three sites (training `:3462`, fight score-fallback `:6120`, fight real-engine `:8157`) plus Slice 0.5 cancellation news at two sites (player loop `:1260`, AI card loop `:6001`). Champion injuries fire `🏆 [Name] ([Division] Champion) suffers [injury] — out [N] weeks. Title defense delayed.` Site A widens its prior player-only gate to (player OR champion), so AI champion training injuries now generate news for the first time; player non-champion path remains byte-identical 🤕. Sites B+C are pure conditional swaps (champion → 🏆, else → existing 🤕 unchanged). Cancelled fights from Slice 0.5's gate fire `🚫 [F1] vs [F2] at [Event] cancelled — [Uncleared(s)] not cleared to fight.` (handles single + both-uncleared via `" and ".join`). Site F (AI fallback pool filter) deliberately silent — filter-level exclusion has no specific scheduled fight to announce. Commit `804938b`. Verified by 3-week advance — existing 🤕 path firing through terminal output unchanged, no regressions on non-champion injuries. 🏆 and 🚫 surface naturally on champion-injury and gated-fight scenarios in future play.

## Shipped 2026-05-02
- Champion injury Slice 2 (shipped, code-reading verified): vacate-on-career now auto-books a vacant-title fight at the next available card. Pre-existing auto-vacate at `game_bridge.py:1460` (Slice 0.75 threshold) stripped the belt and fired 👑 TITLE VACATED news but didn't schedule a successor fight — divisions remained headless until manual intervention. Inline +71-line block inserted between strip completion (line 1484) and the autosave section (line 1486), still inside the `for wc` loop and `if weeks_injured >= 25:` block. Fires BEFORE line 1490's `_update_all_rankings()` so `div.rankings` still reflects pre-vacate state (ex-champion not in the list). Filtering predicates mirror existing card-builder patterns: active fighter, not the ex-champion (defensive), `camp_id != player_camp_id` (Slice 2 is AI-only), not in `_all_booked` set (computed from `_scheduled_fights + _upcoming_cards`), `is_cleared_to_fight`. Walks `div.rankings[:8]` to allow fallback past unavailable top-2; breaks at 2 contenders. Card selection scans `_upcoming_cards` chronologically for first card without an existing main_event slot — guarantees no double main events. Booking via `_make_scheduled_fight(top1, top2, wc, event_name, target_week, "main_event", is_title=True)`, append to `card["fights"]`. News fires `🏆 VACANT TITLE FIGHT: {top1} vs {top2} for the {wc} belt at {event_name}.` immediately after the existing 👑 TITLE VACATED entry. Edge cases gracefully degrade with terminal warnings (deferred booking, not crashes). Commit `b4ac430`. Verified by code-reading on slot1 — 8 weeks advanced, no champion hit ≥25w injury this cycle so the booking path didn't trigger; Slices 0.5/0.75/1 all firing correctly with no regressions. Filed Slice 2.5 (player vacant-title invitation prompt) at `memory/slice_2_5_player_vacant_title_invite_2026-05-02.md` — when player is ranked #1/#2 in a vacating division, Slice 2's AI-only filter passes them over; needs dashboard-blocking prompt to respect player agency. Same family as Bug Z. Bundles cleanly with Slice 3's prompt infrastructure when picked up.
- Bug AB.1 (verified): watch_fight FOTN banner spillover. `templates/watch_fight.html:43` was the fourth and final FOTN per-fight rendering surface still reading `fight.is_fotn` directly — old DFC 1-30 fights all showed the banner due to slot3's pre-commit-56bf807 corrupt is_fotn=True writes. Fix required ROUTE-level change because watch_fight handler at `routes.py:2010-2067` only loaded `fight_result` from `_completed_events`, not the containing event. Route now captures `fight_event = ev` alongside `fight_result = f` in the same loop iteration (line 2019), passes `event=fight_event` to render_template. Template gate switched from `{% if fight.is_fotn %}` to `{% if event and event.fotn and event.fotn.fight_id == fight.fight_id %}` — defensive `event and` guard for hypothetical None paths, mirrors Bug AB three-template pattern. Net diff: 4 lines across 2 files (3 in routes.py, 1 in template). Commit `7914647`. Verified across slot3 (week 38, both old corrupt and new clean events): old DFC 17-29 watch-fight URLs show no banner (self-fix via `event.fotn=None` for legacy events), new event watch-fight where fight WAS FOTN winner shows banner correctly, new event watch-fight where fight was NOT FOTN winner shows no banner. Scorecard/commentary/rounds rendering unchanged. **Closes the four-surface FOTN derivation family** — event_detail (Bug AB), week_results (Bug AB), archives (Bug AB), watch_fight (Bug AB.1) all source from `event.fotn.fight_id == fight.fight_id`. Single source of truth. Corrupt `fight.is_fotn` flag persisted in slot3 events 1-30 is now truly dead read data.
- Champion injury Slices 3+ remain queued: Slice 3 (player decision UX with dashboard prompt for Severe injuries on player's own champion + naturally bundles Slice 2.5's player vacant-title invitation), Slice 4 (hold-path consequences — cardio decay, mandatory return defense, news tone progression), Slice 5 (interim belts + cleanup of vacate headline text), Slice 6 (ring rust + polish). See `memory/design_champion_injury_handling_2026-04-30.md`.

## Shipped 2026-04-30
- Bug Z (verified): auto-booking after player gets ranked. `_build_card_for_week` ranked-vs-ranked pairing at `game_bridge.py:7326-7368` iterated `division.rankings[:14]` with no player-ownership guard — once a player fighter entered top 14 of any division, the auto-builder picked them into upcoming events without negotiation. Fix: one-line filter `(not player_camp_id or f.camp_id != player_camp_id)` added to availability list at line 7295. `player_camp_id` was already grabbed at line 7275 and previously unused. Belt-and-suspenders form so the filter no-ops cleanly if camp isn't yet established (Optional[str] = None at game_state.py:336). Commit `59193c5`. Verified: Wei Martin (player, #3 FLY) won SPLIT DEC at DFC 28; post-fight `/ladder/Flyweight` showed cooldown only, no auto-booking. Other 11 ranked FLY fighters auto-paired into DFC 29-34 as expected — filter is correctly selective. Same two-path-merger family as Bug O / Bug R / Bug Q / Bug S — system that should treat player and AI fighters differently but didn't.
- Filed: judge-tendency observation (grappling rounds possibly undercredited) — n=1 split decision where player controlled all 3 rounds via takedowns/back mounts/RNCs and 2 judges still scored against. Park, don't act. See `memory/judge_grappling_tendency_2026-04-30.md`.
- Sub-bug audit (S.1/S.2/S.3) closed — bundle diagnosis on `_run_real_engine` asymmetries vs other fight paths. Verdicts: **S.1 DEFER**, **S.2 KILL**, **S.3 KILL**. No code shipped. Key findings: (1) S.1 — `_run_real_engine` doesn't call `_update_rankings_after_fight` per-fight, but `advance_week:1471` calls `_update_all_rankings()` once per week which iterates every division — Bug E/G's verified rank-delta path runs through this bulk refresh, so the asymmetry is intentional coverage, not a gap. (2) S.2 — `_fighter_data['fight_history']` mirror is read only at lines 3050/6950 as fallbacks when canonical `fighter.fight_history` is empty; canonical is never empty post-Bug-S, so the mirror is functionally dead code. (3) S.3 — `_run_real_engine:7987` calls `_apply_post_fight_camp_record` which inserts `"category": "player_result"` news at lines 1914/1923 — player fights DO emit news, just under a different category by design. Same logic as Bug AA downgrade — not shipping defensive code for hypotheticals.
- Bug AA downgraded to architectural-gap-no-live-reproduction (covered separately above) and `challenge_fighter` harmless-gap filed — see commit `ba163fe`.
- Filed: pattern observation — diagnose-first discipline saved ~30+ minutes of speculative fix work on the S.1/S.2/S.3 audit; 2 of 3 filed concerns turned out to be misunderstandings of intentional design (S.3 categories) or coverage by a different mechanism (S.1 bulk refresh). Asymmetry between code paths ≠ bug; check coverage, intent, and dead-code status before proposing symmetry fixes. Trust prior verifications. See `memory/pattern_diagnose_first_saves_speculative_fixes_2026-04-30.md`.
- Filed: champion-injury-handling design spec (multi-session feature). Severity-tiered: Minor/Moderate (≤9w) auto-hold; Severe (9-24w) player chooses vacate vs hold; Career-level auto-vacate. Vacate path → top-2 fight for vacant belt, player returns #1 with tune-up-then-title-shot logic. Hold path → belt holds with cardio decay and mandatory title defense on return. Decision UX is a dashboard-blocking prompt after the injury fight. Slices 0-6 sequenced for incremental shipping; Slices 0+1 (auto-book audit + injury news headline) are next-session start, not auto-launched. **Slice 0 awaits fresh prompt — do not auto-start.** See `memory/design_champion_injury_handling_2026-04-30.md`.
- FOTN top banner (verified): event_detail page now renders the gold-gradient FOTN banner above the slot grid for events that produced a Fight of the Night. `_build_card_for_week` selection block at `game_bridge.py:1516-1540` was setting per-fight `is_fotn` flags but leaving `event["fotn"]` at its `None` initialization (line 1272), so the existing banner template at `event_detail.html:27-47` was dead code. Fix: +13-line block after FOTN selection succeeds populates a 4-key dict `{fight_id, fighter1_name, fighter2_name, bonus}` onto whichever event in `_completed_events` for the current week contains the FOTN fight. Bounded scan handles all branches (merged ai_event, unmerged player events, no-card else path). Commit `4736de7`. No-op path preserved: when `fotn_result` is None (card had <2 fights or score below 30 threshold), event.fotn stays None and banner stays hidden. Existing dashboard FOTN news headline (verified 2026-04-27) still fires unchanged.
- Bug AB filed (NEW, NOT FIXED): per-fight FOTN badge spillover on event_detail. All fights on the page render the "🔥 FOTN" badge + gold left border instead of just the actual FOTN winner. Pre-existing bug (clear loop at `game_bridge.py:1519-1533` is byte-identical to its pre-ship state — diagnosis confirms our diff cannot have caused it), exposed visually now that the top banner draws attention to FOTN. Investigation targets next session: clear loop not running, clear loop writing to wrong object references, or template gating bug. Cheap diagnostic print sketched in memo. See `memory/bug_AB_per_fight_fotn_badge_spillover_2026-04-30.md`.

## Shipped 2026-04-29
- Bug O (verified): prelim player fights running 5 rounds. `_run_real_engine` at `game_bridge.py:7922` was setting `is_main=True` for any player fight regardless of `card_slot` — conflated "player participation" with "main event status." This forced 5-round FightConfig for all player fights (the asymmetric upgrade-only round override at `fight_integration.py:1228-1229` then locked it in). Fix: remove the `or fight.get("is_player_fight", False)` clause from line 7922. Player fights now respect their slot semantics. Commit `7c3f8e1`. Verified: Raj Panyawong (player, prelim) won SPLIT DEC after R3; AI prelims max R3; title fights still 5 rounds (Oscar Gane DEC R5). No regressions. Same two-path-merger pattern as Bug R, Bug Q, Phase 0 — fields/flags diverging between player and AI paths. AI path was already correct.
- Filed: Sub-bug O.1 (`fight_integration.py:1228-1229` asymmetric upgrade-only round override — currently harmless post-Bug-O, defense-in-depth cleanup deferred). Tech-debt note: `game_bridge.py:7923` redundant slot check after `is_main` is already computed at 7922 — cosmetic cleanup. See `memory/sub_bug_O1_engine_round_override_asymmetric.md` and `memory/tech_debt_game_bridge_7923_redundant_slot_check.md`.
- Bug S (verified): cooldown not applied to player-fight opponents. `_run_real_engine` returned without writing `fight_history` for either fighter; cooldown loop in `advance_week` (lines 1367-1375) calls `_apply_cooldown` → `_cooldown_weeks` → `_get_fighter_lose_streak`, which reads `fight_history`. With no L recorded, `lose_streak == 0` → fell into the WINNER branch → unranked losers got 1w cooldown instead of 4w. Player could spam-rematch any AI fighter they just beat. Fix: 15-line `fight_history.append()` block inside `_run_real_engine` (between contract decrement and scorecard), mirroring AI path at `_simulate_card_fights:6073-6081` byte-for-byte. Commit `c203b51`. Verified: Wk 23 DFC 23 — Raj beat Ulugbek; Ulugbek now shows "Available Week 27 (4w)" on LHW ladder. Pre-existing latent bug (not Option P regression). Same two-path-merger family as Bug O / Bug R / Bug Q / Phase 0.
- Filed: Sub-bug S.1 (missing `_update_rankings_after_fight` in `_run_real_engine`), Sub-bug S.2 (missing `_fighter_data` fight_history mirror), Sub-bug S.3 (possibly missing news-headline insert — verify in dashboard before classifying). All low priority; bundle when `_run_real_engine` is touched again.
- Bug Z filed (NEW, HIGH, NOT FIXED): auto-booking after player gets ranked. Raj (#11 LHW) auto-scheduled into DFC 17 vs Robert Lopez (#8) without negotiation. Player agency lost. See `memory/bug_Z_auto_booking_ranked_player_2026-04-29.md`.
- Bug AA filed (NEW, HIGH-ish, NOT FIXED): offer queue doesn't reconcile with scheduled fights. Inbound offer arrived for a fighter already booked; offer stayed accept-able. Sequence Z first, AA second — fix shapes may share. See `memory/bug_AA_offer_queue_doesnt_reconcile_2026-04-29.md`.

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