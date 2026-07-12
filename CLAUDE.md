## 🚨 CRITICAL — LIVE COMMENTARY FILE (read before any commentary work)

**Verified empirically 2026-07-07.** Under PA's actual wsgi.py sys.path
(`cage_dynasty_web/`, `systems/`, `narrative/`, `simulation/` — **NOT
repo root**), `from commentary import` at `fight_integration.py:140`
resolves to `narrative/commentary.py`, **NOT** the repo-root
`commentary.py`. The repo-root file is **dead-in-runtime** — PA never
loads it because repo root is not on sys.path.

- **Live commentary file on PA**: `narrative/commentary.py`
- **Dead-in-runtime**: repo-root `commentary.py`
- **How verified**: PA's `/var/www/vandopegaming_pythonanywhere_com_wsgi.py`
  fetched via Files API + local Python replicated its exact sys.path
  and imported `commentary` → resolved to narrative/commentary.py.
  Files API fetch of narrative/commentary.py on PA showed NONE of
  our recent ship signatures (no `emit_fight_open`, no
  `_maybe_emit_contrast_callout`, no championship-fix markers) — the
  running file has none of the three commentary ships below.

**Consequence — three shipped commits are INERT in production:**

| Commit | Ship | Target |
|---|---|---|
| `642c43c` | COMMENTARY-CHAMPIONSHIP-FIX1 | repo-root commentary.py (dead) |
| `cf34aa9` | COMMENTARY-ENTRANCES1 | repo-root commentary.py (dead) — game_bridge/fight_integration edits DO reach PA, but the emit hooks call methods that don't exist on narrative/commentary.py |
| `a46487c` | COMMENTARY-GAMEPLAN-CONTRAST1 | repo-root commentary.py (dead) — same story |

These features will NOT appear in-game until either (A) the changes
are ported to narrative/commentary.py, or (B) wsgi.py is amended to
add repo root to sys.path (which reintroduces the CLI-fork shadowing
that wsgi.py was specifically designed to prevent). **NOT YET
FIXED — deferred to next session for a clear-headed A-vs-B decision.**

The prior memory `architecture_commentary_live_file_2026-06-20.md`
claiming root is live / narrative is the drifted dead fork is
**WRONG for PA's actual config** and is superseded by this notice
and by the corrected memory pointer of the same name.

Full trace + evidence in the CROSS-TREE-IMPORT-TRACE1 session output
2026-07-07 (session transcript, not committed).

## 🚨 ALSO — PA silent-fail feature losses (same root cause)

Under PA's sys.path, `from systems.injury import (...)` and
`from systems.coaches import CoachSystem, Coach` both **FAIL** —
because `systems` resolves to `cage_dynasty_web/systems/` (a
stub package containing only `game_start.py`), and Python does not
continue searching sys.path for a `systems` package that has the
requested submodule.

- **Injury system disabled on PA.** All champion-injury slices
  (auto-vacate, hold-path cardio decay, cleared-to-fight gate,
  injury news headlines) depend on `INJURY_AVAILABLE` — silently
  `False` in production. `⚠️ injury system not available: No module
  named 'systems.injury'` prints at PA startup.
- **Coach save/restore disabled** (lazy at `game_bridge.py:11912`).
  Hiring UI still works via the local `COACH_TYPES` constant, but
  reloading a save with existing coach state warns and skips coach
  reconstruction. Only visible when loading pre-existing saves.

Separate finding from the commentary issue but same class of cause
(sys.path resolution hitting the shadowing stub package before
reaching the CLI tree). File for later — do NOT fix in the same
sitting as the commentary re-target.

## Ship History (compact)

Full recaps for older ships in `CLAUDE_archive.md`. Table below is reverse-chron; pre-Ship-C2 (2026-05-30) entries kept for architectural-pattern reference. `git log --oneline` is authoritative for anything between rows.

| Date | Ship | Commit | What |
|---|---|---|---|
| 2026-07-11 | TITLE-SHOT-GATE1 | b069dad | Player challenges to the reigning champion had no eligibility gate and booked as non-title fights (hardcoded `is_title_fight=False`). Gated champion-challenges through `matchmaking.is_title_eligible` (top-5 + 3 pro fights, record fallbacks), derived `is_title_fight` from `division.champion_id` at booking (not rank proximity — anti-fire tested), hid Challenge button when ineligible with server-side gate as the real enforcement. Player-challenge path only; AI `_book_title_fight` untouched (filed for belt epic). Deployed. |
| 2026-07-11 | EVENT-DETAIL-WC-LABEL1 | f00afcb | `event_detail.html` fight boxes omitted the weight-class pill that `week_results.html` renders. Mirrored the existing pill (3-letter uppercase, links to rankings), guarded for missing `weight_class`. Template-only; data was already populated on every fight record (zero data gap). Retroactive — all events, existing and new. Deployed. |
| 2026-07-11 | STREAK-INAUGURAL-FILTER1 | 907ad19 | Win/best-win-streak loops counted the synthetic "Inaugural Crown" tombstone (`world_init.py:1275`) as a real win, inflating founding champions' streaks by 1 (the "14 on a 13-0 record" bug). Filtered `method=="Inaugural Crown"` from both loops at `game_bridge.py:7152`/`:7175`. Compute-time only — no `fight_history` mutation, no `wins`/record touch. Retroactive on existing saves. Deployed. |
| 2026-07-11 | OVR-AT-SIGNING-CAPTURE1 | d4e16fb | `ovr_at_signing` was only captured at the two player-sign wrappers; world-gen and AI-signed fighters never got it, leaving the profile career-arc "At Signing / Growth" cells blank. Seeded world-creation baseline in `world_init.py` fdata block; added first-write-wins guard in `game_state._sign_fighter_to_camp` covering all AI + player sign callers. Existing player-sign wrappers still overwrite (intentional "OVR when signed to your camp" semantic). Forward-only. Deployed. |
| 2026-07-11 | PROFILE-REDESIGN1 | 3e8d04f | `fighter_profile.html` restructure: stats-hero layout, four tier-colored attribute panels (Striking, Physical, Grappling with Wrestling/BJJ sub-groups, Intangibles), added previously-hidden `recovery` + `composure`, tier-colored bars+numbers with restored gold ≥90 elite band (6-tier scale), championship-reign arc, rivalries paired row, tier-driven scout report, career-arc row, mobile breakpoints. Fight history: round-key hedge (`fight.round_finished or fight.round` — pre-gen fights now show their round), decision-type display, Inaugural Crown pill. Template-only. Deployed. |
| 2026-07-11 | FOTN-PERSIST-FIX1 | 2794aee | `career_fotn_awards` was incremented but not declared on `FighterRecord`, so it dropped every save round-trip; the profile FOTN badge never rendered persistently. Added field declaration + `to_dict`/`from_dict` serialization with backwards-compat default. Forward-only — new saves persist correctly; existing saves stay at whatever count they had at that boundary. Deployed. |
| 2026-07-10 | MATCHMAKING-ENFORCE1 | 18a2438 | Score-driven opponent selection in `_build_card_for_week`'s "1 ranked left" branch, replaces `random.choice(unranked_pool)`. 75/25 competitive/step-up via 3 named module-level constants. Deployed. |
| 2026-07-10 | NEWS-CHIN-FILTER1 | afa26f7 | Chin/durability news gate at `_apply_chin_erosion._news_items.insert` — emits only for player-owned OR current champion OR watchlisted fighters. Chin stat erosion still runs for every fighter; only the news emit is gated. Deployed. |
| 2026-07-10 | GROUND-STOPPAGE-FIX1 | 40dd8d5 | Accumulated-damage TKO respects chin/heart/composure via `_tko_durability_mult`; TKO_GNP threshold 25.0→18.0, TKO_STANDING 20.0→15.0. Deployed non-regressive. **Founding premise (a ~22%→40% DEC gap) was false — the AI-vs-AI pool rate was already 44.6% pre-fix per the POOL-DEC-RATE1 extraction. Net live effect on the pool is unmeasured; treat as safe (in-band) but not as "closing a gap that didn't exist."** |
| 2026-07-05 | AGGRESSION-NARRATION1 | b97e7bd | Fight-open intent line in watched-fight timeline for forward/patient sides |
| 2026-07-05 | BRIDGE-WIRE-AGGR1 | 0f3154b | Player gameplan resolved → Gameplan and passed into real engine at `_run_real_engine` |
| 2026-07-05 | GAMEPLAN-DIAL-AGGR1 | d1d927d | Aggression dial live in engine (config B — initiative ±2, pre-fight ±4, IQ-gated strike weights) |
| 2026-07-05 | GAMEPLAN-WIRE1 | ec78b3b | Optional Gameplan threaded through `simulate_narrated_fight` → simulator → `select_action` (additive) |
| 2026-07-05 | JUDO-SAMBO-BUCKET-FIX1 | bd38a2f | judo/sambo coach specialty routes to wrestling bucket (was clinch) — legacy-save training corrected |
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

**Gameplan dial state (live as of 2026-07-05):**
Four ships wired the aggression axis end-to-end: GAMEPLAN-WIRE1 (`ec78b3b`,
threading) → GAMEPLAN-DIAL-AGGR1 (`d1d927d`, engine behaviour, config B) →
BRIDGE-WIRE-AGGR1 (`0f3154b`, resolve stored gameplan in `_run_real_engine`)
→ AGGRESSION-NARRATION1 (`b97e7bd`, fight-open intent line). Live on PA.

Only the **aggression** axis is wired. The eight UI presets collapse to
three live behaviours today:

| Preset (routes.py:2213) | Aggression | Live behaviour |
|---|---|---|
| AGGRESSIVE, GNP, CLINCH | +1 | Forward — press-the-pace intent line + initiative +2 + pre-fight boxing/kicks +4 |
| BALANCED, TAKEDOWN, SUBMISSION, unset | 0 → None | Neutral — byte-identical to pre-wire, no intent line |
| MEASURED, DEFENSIVE | −1 | Patient — patience intent line + initiative −2 + pre-fight striking_defense +4 |

**Known debt from that collapse (queued, filed against future dials):**
- **RANGE dial** — separates TAKEDOWN and SUBMISSION from AGGRESSIVE-family
  and pulls GNP/CLINCH off the "≡ Go Forward" alias. Design memo:
  `outputs/gameplan_range_design1.md`.
- **finish-seek dial** — separates SUBMISSION from TAKEDOWN and gives DEFENSIVE
  its own posture distinct from MEASURED.
- Until those ship, the UI-vs-engine mismatch is real and documented:
  TAKEDOWN and SUBMISSION are placebo, GNP ≡ CLINCH ≡ AGGRESSIVE (same forward
  behaviour), DEFENSIVE ≡ MEASURED.

**Counter-window finding (also filed, do not misdiagnose as a Patient bug):**
The engine's counter-window logic keys on **fighting style** (Counter Striker,
Point Fighter, Sprawl & Brawl in the STRIKER_FAMILY at `styles.py`), not on
Gameplan and not on any trait. So a Patient MEASURED gameplan on a Muay Thai
or Pressure fighter does not activate a counter mechanic — patience is a
posture/output shift only. Do not tune counter values in response to
"MEASURED doesn't counter" reports; the mechanism lives elsewhere.

**Small logging debt (demote-to-debug):**
The 🎯 `[GAMEPLAN WIRE]` stdout print in `game_bridge.py:_run_real_engine`
(added by BRIDGE-WIRE-AGGR1 for the tier-2 live gate) still fires on every
non-neutral player fight. Useful during rollout — noise now that it's live.
Demote to a debug-guarded print (e.g. behind an env flag or a module-level
`_GAMEPLAN_DEBUG = False`) on the next `game_bridge.py` touch.

**Queued, not scheduled:**
- **TWO-ENGINE CONSOLIDATION arc (HIGH, filed 2026-07-11).**
  `fight_engine.simulate_fight` (pre-gen path) and
  `fight_integration.simulate_narrated_fight` (live-play path) are two
  simulators with parallel exchange loops that have drifted since
  2026-06-14 (`d347de9` "all in fight_integration layer"). Same fighters,
  same seeds: pre-gen 26% finish rate vs live-play 98% on striker-vs-
  striker. FI has ~8 accumulator-TKO paths and ~6 style windows FE
  lacks; FE has an elbow-cut writer FI lacks. All simulation primitives
  (select_action, calculate_strike_damage, attempt_submission, etc.)
  are imported from FE by FI, so consolidation onto one simulator is
  feasible. Recommended direction: port FI-only mechanics into FE,
  retire FI's exchange loop, keep `NarratedFightResult` +
  `simulate_narrated_fight` as a decorator over
  `FightResult.event_log`. Multi-session arc. Full audit +
  step-by-step plan: `outputs/two_engine_consolidation_diag1.md`.
  **Do not tune finish rates before this ship** — any number tuned
  now has to be re-tuned twice.
- **PRE-GEN WORLD COHERENCE epic (HIGH, filed 2026-07-11).** World-init generates
  self-contradicting title histories that no live-play code path can fix. Read-only
  diagnostic first, then scoped ships. Three known threads:
  - **Belt-state consistency.** Strawweight evidence on a week-9 save: a fighter
    shown defending a belt he'd already lost per belt_history; two fighters both
    claiming the active title; ladder view disagreeing with the reign records.
    Suspected root cause: the post-gen `TITLE-TRANSFER-FIX1` (`5e4bbe1`, 2026-07-03)
    that closed the AI-champion-doesn't-lose-belt bug was never ported to the
    world-init generator — parallel unfixed copy in `world_init.py`. Also flagged:
    `_book_title_fight` (AI title-booking path) needs a rank-discipline audit
    (`is_title_eligible` / `find_title_challenger` exist in `matchmaking.py` but
    are dead-in-runtime for the web app; AI title-booking has its own separate
    logic that hasn't been audited against them).
  - **Rematch rules parity.** Pre-gen opponent selection may not match post-gen's
    rematch discipline (16w hard minimum, 20w for title rematches, intervening-fight
    guard, contender-earned-title-shot guard — shipped `07491d1` 2026-06-22 for the
    live paths and mirrored into world-gen at that time, but re-verify given the
    belt evidence above).
  - **Timing/spacing.** Pre-gen fights sometimes cluster rather than realistically
    spacing across the simulated years.
  - Discipline: forward-only (only affects fresh saves). Diagnostic first — do NOT
    scope fixes cold. When picked up, this is a multi-session arc, not a single
    ship.
- **COACH-GRAPPLE-SPLIT1** — split the `grappling_coach` training bucket into
  distinct wrestling and BJJ archetypes. Sandman-grade fighter-identity work
  deferred from the 2026-07-03 coach arc.
- **Coach trait design deepening** — 16-trait system is now wired (post-Ship
  ac9a2a6) but under-tuned; some traits still don't produce visibly different
  fighter outcomes across a play session.
- **EC1 economy arc** — coach salaries are now differentiated by rating
  (post-CURVE1), giving budget vs. elite a real tradeoff. Downstream: fight
  purses, sponsorship depth, facility ROI curves.
- **FOTN full-fidelity scoring (unblocked, small).** Current FOTN badge reads a
  lighter subset of per-round stats. The full per-round data (sig strikes /
  takedowns / sub attempts / control time) already flows through
  `all_round_stats` on every engine result and is aggregated into `career_*`
  fields on `_fighter_data` — the plumbing that would have been a foundation
  ship is already built. Upgrading FOTN scoring to consume the full-fidelity
  slice is a small consumer change, not a plumbing project. See per-round
  persistence reframe below.
- **SUB-rate undershoot tuning** — see `memory/sub_rate_undershoots_2026-04-28.md`.
  Pre-verify still applies against the current engine-tuning arc before shipping.
- **Older Bug X items** filed pre-multiuser (Bug H, Bug C second path, Bug T, Bug Y).
  Re-verify each against current code before shipping — several may already be closed
  by the July ship cascade.

**Per-round persistence reframe (filed 2026-07-11):**
What looked like one big "per-round persistence project" (foundation-level, weeks
of work) is actually **two separate gaps wearing one umbrella**, and the larger
half is already built:

- **DONE (proven live):** sig strikes, takedowns, sub attempts, control time.
  Engine computes per-round via `RoundStats` (`fight_engine.py:621-660`), carries
  them as list-of-dicts on the result (`fight_integration.py:1815`, `.to_dict()`
  conversion → `NarratedFightResult.fighter1_stats`), and the bridge aggregates
  into `career_strikes` / `career_takedowns` / `career_sub_attempts` /
  `career_control_time` on `_fighter_data` via `_accumulate_career_stats`
  (`game_bridge.py:14981`) — called from all three fight-resolution paths
  (`_simulate_card_fights:13747`, `_simulate_ai_fights_week:14255`,
  `_run_real_engine:18069`). Verified on 2026-07-03 local `bridge_van_autosave`:
  114/287 fighters carry `career_strikes > 0`, top-5 all active at 78-98 strikes,
  Record Book renders full populated lists. **Foundation is complete for this
  half.** Consumers: Record Book (works), FOTN full-fidelity scoring (unblocked).
- **REMAINING (the actual gap):** finish position + specialty method label.
  These are NOT on the fight-record write path — CLAUDE.md's 2026-07-10 note
  on finish-composition already flagged this. Smaller, isolated instrumentation
  ship — persist finish position + specialty method label in
  `completed_events[].fights[]` in `_run_real_engine` /
  `_simulate_ai_fights_week`. Same file, same site, similar shape. Unblocks
  finish-composition measurement + the profile's specialty-method display.

Practical implication: do NOT scope FOTN scoring or Record Book granular stats
as "part of a foundation project." Both are one small consumer/plumbing change
away. Finish-composition remains the only genuine per-round instrumentation
ship on the board.

**Recently reconciled (closed):**
- **Record Book "No records yet" for granular stats — RESOLVED not-a-bug
  (2026-07-11).** Original symptom: sig-strikes / takedowns / sub-attempts
  categories showed the empty-branch placeholder despite the standard
  wins/KOs/subs categories rendering. Diagnostic traced the full pipeline
  end-to-end and found every layer wired: engine → carrier → aggregator
  → career fields → Record Book read → template render. Grep on the
  2026-07-03 local `bridge_van_autosave.json` confirmed 114/287 active
  fighters carry `career_strikes > 0` (top-5 all active, values 78-98);
  live PA save renders the full populated top-5 lists per Van's browser
  verification. The original "No records yet" reading was honest reporting
  on a thin/early save that hadn't accumulated enough live-play fights;
  it self-resolved as the world played out. Closed as not-a-bug. Also
  see the per-round persistence reframe above — this diagnostic bought
  the reframe that stopped a phantom "foundation project" from being
  filed.
- **Judo/Sambo coach bucket routes to wrestling** — JUDO-SAMBO-BUCKET-DIAG1
  (2026-07-05, `outputs/judo_sambo_bucket_diag1.md`) traced the outlier: the
  `_SPECIALTY_ALIASES` table sent `judo`/`sambo` to `clinch_coach` while every
  other consumer treated them as grappling/wrestler-family (style-inference,
  attribute weights, engine style bucket, gameplan bucket). Closed by
  JUDO-SAMBO-BUCKET-FIX1 (`bd38a2f`, 2026-07-05) — two-line alias change +
  matching hire-card banner. Legacy saves with judo/sambo coaches now train
  the takedowns/top_control stats the fighter identity implies instead of the
  clinch_control/clinch_striking stats every other system disagrees with.
  `COACH_TYPE_MIGRATION` display migration for existing coach labels is a
  cosmetic follow-up, not blocking.
- **Auto-load most recent save on landing** — filed as top-of-backlog #1 on
  2026-07-03; AUTOLOAD-RECONCILE1 (2026-07-05) confirmed the feature was
  already shipped at `484e7f8` (feat(session): auto-load most recent save
  on landing) between the elevation and the reconcile. AUTOLOAD-SAVE-DIAG1
  (`outputs/autoload_save_diag1.md`) traced the landing path end-to-end
  and verified guards hold: `dashboard()` (`routes.py:583-602`) gates on
  `bridge.game_started`, `get_newest_save_slot()`
  (`game_bridge.py:3133-3157`) picks by mtime scoped to
  `bridge_{user_id}_{slot}.json`, per-bridge `_lock` serializes `web_load`.
  Coverage note: autoload fires only on `/` — bookmarks to other routes
  (e.g. `/roster`) still bounce returning users to `/new-game`. Optional
  polish items (dead `require_game_started` decorator, corrupt-save flash
  message, hardcoded slot list) filed in the diag §7 but not blocking.
- **Matchmaking diversity / rematch prevention** — filed as an in-conversation
  concern 2026-07-04; MATCHMAKING-RECONCILE1 (2026-07-05) confirmed this is
  substantively closed by two prior ships: `07491d1` (2026-06-22) replaced the
  old 6w/12w recency-only cooldown with a 16w hard minimum (20w for title
  rematches) PLUS an intervening-fight guard (`_both_fought_since`) and
  contender-earned-title-shot guard (≥2 wins vs different opponents since last
  meeting), and mirrored the same guards into world-gen. `b3b16c8` (2026-06-27)
  added tiered rivalry heat bonus into `_matchup_score` (0/5/15/25/35 by heat
  30/50/70/90). Empirical on 2026-07-03 autosave: 99 unique pairs across 10
  events, only 2 pairs met twice, only 1 pair met three times, max = 3.
  Yesterday's investigation predated these ships and is stale.

**Deferred low-priority cleanup:**
- Sub-bug O.1 — asymmetric round override at `fight_integration.py:1228-1229`.
  Bundle with any future `fight_integration.py` touch.
- Off-week semantics contradiction — surfaced in TITLE-TRANSFER-DIAG1. Off weeks
  discard the pipeline card but the fallback path (`_simulate_ai_fights_week`)
  still generates fresh AI fights, contradicting the "no event" print. Not a
  correctness bug — a design call on whether off weeks should truly skip AI sim.
- `card_builder.calculate_matchup_score(is_rivalry=False)` param is dead — no
  caller passes it (game_bridge's `_matchup_score` adds `_rivalry_heat_bonus`
  on the returned score instead). The 12.0 flat rivalry bonus at
  `card_builder.py:348` never fires. Small cleanup, no behavior change.
- Empty-main_card residual rate ~10% of events (1/10 on the 2026-07-03
  autosave). `CARDSLOT-BACKFILL1` (`222a502`, 2026-07-03) cosmetically promotes
  a top-scoring prelim into MAIN_CARD when it routes empty, so the visible
  symptom is masked. Root cause (main_card score threshold ≥55 misses on
  thin-week candidate pools) is unaddressed. Design call, not a bug — either
  loosen threshold, thicken matchmaking density in thin weeks, or leave the
  cosmetic backfill as-is.
- **Finish-composition data instrumentation (filed 2026-07-10, re-scoped
  2026-07-11).** The narrative-feel question ("does every finish read as
  back-mount GnP?") is unmeasurable from the save today: finish position
  isn't persisted and specialty method labels collapse to bare
  KO/TKO/SUB/DEC before write. If finish-composition ever needs measuring,
  it's an instrumentation ship — persist finish position + specialty
  method label in the `completed_events[].fights[]` write path in
  `_run_real_engine` / `_simulate_ai_fights_week`. Until then it's a
  Van-eyeball call on narrated fights, not a data question. Note: this
  is the **only genuine per-round persistence gap remaining** post-reframe;
  the sig-strikes/takedowns/sub-attempts half is proven live. See the
  per-round persistence reframe under Top-of-backlog.

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
- **PA `wsgi.py` VERIFIED match** as of 2026-07-07 (via Files API fetch of
  `/var/www/vandopegaming_pythonanywhere_com_wsgi.py`, 479 bytes). Byte-
  equivalent to repo's `cage_dynasty_web/wsgi.py` modulo comments. sys.path
  adds `simulation/`, `narrative/`, `systems/`, `cage_dynasty_web/` in that
  insertion order (project_home ends up at index 0). Repo root is
  **explicitly NOT** on sys.path — this is what makes bare `import
  commentary` resolve to `narrative/commentary.py` on PA (see the CRITICAL
  block at the top of this file).
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
- **Saves persist across deploys; a save generated before a ship does not
  reflect that ship.** `_fighter_data` and `fight_history` are frozen at
  world-init time and survive every subsequent deploy through save/load.
  Before drawing conclusions from a save — especially when verifying an
  engine-touching ship — check generation provenance. Concrete signal:
  fight_history entry count. A 130-week world produces ~3,700 entries
  across all fighters; a 60-week world produces ~1,600. Filed after
  PREGEN-FULL-ENGINE-FIX1 (2026-07-12): the "engine is running but style-
  mismatch dampens the OVR signal at high gaps" interpretation was built
  on stale 130-week save data that predated the fix, and a plausible-
  sounding theory got repeated as if established. The truly-fresh
  post-fix save showed a 97.7% favorite win rate at 21+ OVR gap, not 72%.

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

**Damage multipliers — CORRECTED 2026-07-11 by TWO-ENGINE-CONSOLIDATION-DIAG1.**
Prior claim "0.48 × 0.24 = 0.1152 effective per-strike scale" was
FICTION — `fight_integration` never reads `config.damage_multiplier`
(grep confirmed: zero call sites). The 0.24 the bridge passes at three
`_FightConfig(...)` sites is a **DEAD KNOB**.

**Pre-gen and live-play are TWO DIFFERENT SIMULATORS**, not one engine
with two configs. Each has its own damage scale:

- **Live-play** (`fight_integration.simulate_narrated_fight`) — per-strike
  scale = `FI_DAMAGE_MULTIPLIER = 0.48` (module const at
  `fight_integration.py:82`, applied at `:832`). ONLY damage scale in this
  path.
- **Pre-gen** (`fight_engine.simulate_fight` called by `world_init`) —
  per-strike scale = `config.damage_multiplier = 0.42` (default from
  `FightConfig.standard_fight()`, applied at `fight_engine.py:3199`).
  ONLY damage scale in this path.
- Rivalry heat compounds ONLY on pre-gen path — `fight_engine.py:3915`
  `replace(config, damage_multiplier=... * heat_damage_mult)`. Live-play
  reads no heat multiplier (`fight_integration` never reads `heat_level`
  either).

**Dead knobs (do NOT tune these, they don't do anything):**
- `game_bridge.py:{13540, 14061, 18001}` `damage_multiplier = 0.24`
  passed to `_FightConfig(...)` — read by no live-play code path.
- `fight_engine.py:415` `DAMAGE_MULTIPLIER = 0.55` — imported at
  `fight_integration.py:44`, never read.
- `FightConfig.doctor_check_cut_threshold = 2` at `fight_engine.py:771` —
  neither engine reads it. Cut stoppage threshold is hardcoded at
  `cuts >= 3` in both `fight_engine.py:4000` and `fight_integration.py:1717`.
- `defender_state.damage.cuts` in `fight_integration`. The value is READ
  at :1717 but no code path WRITES it (cut accumulation exists only at
  `fight_engine.py:3234` inside `simulate_fight`). Live-play cut
  stoppages are structurally impossible until this is either wired up
  or the check is removed.

**Correcting a prior claim**: earlier CLAUDE.md revisions and session
notes asserted that PREGEN-FULL-ENGINE-FIX1 (`efaf7f6`, 2026-07-11)
made pre-gen and live-play "share one engine." That is wrong. What
that ship did was route pre-gen away from `simulate_fight_simple`
(coin-flip fallback) into `fight_engine.simulate_fight`. Live-play was
already running `fight_integration.simulate_narrated_fight` — a parallel
implementation that shares only submission math and primitive helpers
with `fight_engine`. See `outputs/two_engine_consolidation_diag1.md` for
the full structural audit and consolidation direction.

**Empirical divergence**: on the same fighters, same seeds, 400-fight
probes (FINISH-DISTRIBUTION-DIAG1):
- Striker-vs-striker: pre-gen 26% finish rate vs live-play **98%**
- Balanced-vs-balanced: pre-gen 17% vs live-play 56%
- Within-TKO cut share: pre-gen 68-100% vs live-play 0%

- Submission threshold: 70.0
- Rankings: `MAX_MOVE = 3`, `NEW_ENTRY_CAP = 8`
- Contract: `HOLDOUT = 25`, `WALKOUT = 10`, `HOLDOUT_WINDOW = 4 weeks`

## Certified cell baselines (symmetric skill)

**Principle**: certified balance numbers live in this committed record
with their harness shape + N + CI, never in session conversation — an
uncommitted number mutates. Both of the entries below drifted precisely
because they lived only in chat. If you find yourself citing a balance
figure that isn't in this section, verify it against a fresh probe
before treating it as authoritative.

All numbers below are at symmetric OVR=75, `damage_multiplier=0.24`,
3-round non-title, gameplan=None (neutral). Probe harnesses were
committed inline in the referenced diag memos.

### Wr-BJJ (Wrestler vs BJJ Specialist)

- **Wrestler win rate ~48%** (Harness A 47.3% CI [43.3, 51.4] N=577;
  reproduces 47-49% across 3 harness shapes — see
  `outputs/wr_bjj_drift_diag1.md`).
- **BJJ submission path intact ~16.5%** (99/600 subs, all landed by
  the BJJ side).
- Verified byte-identical across the 8e3f670→efaf7f6 boundary by
  WR-BJJ-DRIFT-DIAG1 (2026-07-07) — this is the correct stable
  baseline, **not a regression**.
- **RETIRED**: the "60.2% CI [56.2, 64.0] N=600" figure never existed
  in any committed artifact — a mis-reference, likely conflated with
  Wr-Str's 60-70% band that GNP-BUFF certified. Do not treat 60.2%
  as a prior baseline in any future work.
- **48% is a design point, not a bug**: BJJ's off-back sub path has
  no symmetric wrestler answer at OVR=75-vs-OVR=75. Moving wrestler%
  upward here is a deliberate new tuning decision, not a
  restoration.

### Wr-Str (Wrestler vs Striker) — post-GNP-BUFF

- **Wrestler win rate 50.3%**, 95% CI [46.3, 54.3], N=600 (variance
  probe, stable, dispersion 0.67×).
- **RETIRED**: the GNP-BUFF commit message's "40%→67%, into 60-70%
  band" claim is retired — overstated from a single N=30 lucky draw
  matrix. Real gain was ~40%→50%.
- Residual gap to any 60% target is addressed by the asymmetric §7
  lever from `outputs/control_conversion_diag1.md` §7, **NOT another
  `GNP_DOMINANT_DAMAGE_MULT` bump** — that shared constant would
  re-break Wr-BJJ.

### Pool decision rate (live-save extraction, POOL-DEC-RATE1 2026-07-10)

- **DEC 44.6%** pool, 157 AI-vs-AI fights, `bridge_van_autosave.json`
  week 15 — read from `completed_events[].fights[].method`, zero
  simulation. In-band vs the 40-50% target.
- **SUB 1.3%** pool (2/157). Ground truth from the same extraction.
- Slot breakdown: main_event 7.7% DEC (13 fights, 9 title fights, all
  9 finished), co_main 26.7%, main_card 48.8%, prelim 50.8%,
  early_prelim 51.7%.
- **HEADLINE-FINISH-TRACE (2026-07-10)** — the headline finish spike is
  the 5-round confound, not a slot mechanic. Apples-to-apples restricted
  to finished-by-R3 (what prelims can reach): headline 50.0% vs prelim
  49.2%, statistically identical (P=0.56). 47% of headline finishes land
  in R4-R5, rounds prelims don't have. Code trace exhaustive:
  `is_title_fight` / `is_main_event` / `card_slot` do nothing in the
  fight-resolution path beyond setting `scheduled_rounds=5`. No damage
  boost, no threshold change, no attribute mutation — `FightConfig`
  constants (damage_multiplier=0.24, standup_threshold=10, submission
  thresholds) identical across slots. **No slot-specific finishing
  mechanism to fix.**
- Title-fight caveat (watch-on-accumulation, no task filed): 9/9
  finished on N=9 is significant vs prelim rate (P=0.0017) but Wilson
  CI on the underlying title finish rate is [70.1%, 100.0%] — could be
  anywhere from ~75% to ~99%. If another 10-20 title fights keep
  finishing, the CI tightens and the rate itself may become worth a
  fresh read.
- **RETIRED**: any citation of the decision rate at ~18-22%. That
  number was a main-event-slice observation (7.7% DEC on 13
  title-heavy headliners) mistaken for the pool rate. It never
  appeared in this doc — recording preemptively so a future session
  can't re-derive it from headline eyeballing and relaunch a
  finish-rate chase.
- **RETIRED**: any citation of the sub rate at 8-10%. Harness
  population artifact — synthetic BJJ Specialists rolled sub-offense
  means around 74; live-booked population means around 59. The sub
  gate is not broken; the synthetic pool inflated it. Live is 1.3%
  and stable.
- Caveats: N=157 is thin (single save, week 15). Sample is pre-fix
  engine (`e1be619`). The three 2026-07-10 ships are deployed but
  their AI-vs-AI-pool effect is unmeasured until fresh fights
  accumulate. In-band is confirmed for pre-fix, presumed for
  post-fix. Worth one clean re-read after enough post-fix fights
  land; not blocking.

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
