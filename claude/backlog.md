# CAGE DYNASTY BACKLOG — LIVE BOARD

This file is the disk-canonical backlog, same status as claude/fight_model_p3_scope_v0_1.md.
It is EDITED IN PLACE: open dockets are updated here, closed ones are pruned to an archive
file as ordinary backlog edits. It is NOT a claude_md_archive_* file.
Created 2026-09-09 by ARCHIVE3. The body below was MOVED VERBATIM from CLAUDE.md
lines 514-1037 at HEAD f9b1b8a (md5 0062f1d92a7116dead4842959130cc88, 524 lines); the verbatim
guarantee applies to the moving commit only.
Pointer back: CLAUDE.md "## Top-of-backlog" (<!-- ARCHIVE3 --> lines).

---

**New dockets from interim deploy 2026-09-07** (one line each; full context
in `claude/playtest_notes_2026-09-07.md` + `claude/interim_deploy_2026-09-07.md`):
- **PLAYER-CREATE1** (supersedes POWER1) — SHIPPED LOCALLY 4f50b78→1839545→64a879f, ON PA at 7555c35 (deploy #3, 2026-09-08, accepted on proof — filing `claude/deploy3_2026-09-08.md`). Prospect generator returns 19 stats with §4-derived style; player record gets style, _compute_ovr, at_signing; training/compare render 19. Seed-20260907 baseline MOVED to outputs/sm_inv/dump_20260908.json — the old dump is a pre-(a) world. Filing: claude/player_create1_filing_2026-09-08.md.
- **PLAYER-CREATE1 findings, none fixed** — PROSPECT-BONUS1 (5/9 draft prospects derive Balanced; balance-touching), OVR-FORMULA1 (AI OVR frozen at unweighted mean, player on _compute_ovr; pool bias −1.6), SETUP-OVR1, HARNESS-RNG1 (only the instrument's numbers are quoted), stale systems/game_start.py, G&P commentary string. Detail: filing §5.
- **TOKEN-HYGIENE1** (HALF DONE, HALF OPEN as of deploy #4 2026-09-11) — DONE: new PA API token lives in ~/.pa_token (chmod 600, outside git); deploy #4 read it inline as `T=$(cat ~/.pa_token)` — no shell log, no script file. Residual: the token IS in `curl` argv per call (visible to `ps` during the call); `-H @file` (curl reads header from file/stdin) closes that. OPEN: deploy.sh at repo root still carries the two literals (PA_TOKEN at :5 revoked/dead; DEPLOY_TOKEN at :8 git-pull webhook, status unknown, treat as live); both in git history. Two options: (a) rotate DEPLOY_TOKEN and rewrite deploy.sh to read from ~/.pa_token; (b) delete deploy.sh now that the API path is the standing procedure. SECRET_KEY still open — session cookies forgeable, warning fires at PA startup. Detail: `claude/deploy3_2026-09-08.md` §5 + `claude/deploy4_2026-09-11.md` §5.
- **WEEK-AXIS1** — (a) STAMP dcee687, (b) SEED 266e382 + BOOKER1 1ccefa0 + CHAMP-A 23c7599, (c) PREDICATE ada3955 — ON PA at 54e3b68 (deploy #4, 2026-09-11, API-driven, all 12 gates PASS, filing `claude/deploy4_2026-09-11.md`). R06 8→7→2→0 predicted by count and name ((b) only); R03 FP 0 in two runs + one confirm (before-count is process-dependent: 1 on dump_champ_2, 1/2/4/6/7 seen); T-4 0; pre-gen 0 diffs; render probe 0 violations across 3 fighters incl. multi-reign; Van's browser check on fresh save wk 1 PASS (Chan Sung Hong founding HW: 👑 founding + 🛡️ ×2 in-window + no post-reign badge; Pedro Lopes successor: 👑 + 🛡️ ×4 "4 defenses"; Denis Kuznetsov no reigns → no badges; card 61 = 9 fights). Filings `claude/week_axis1_b_filing_2026-09-10.md` + `claude/week_axis1_c_filing_2026-09-11.md` + `claude/deploy4_2026-09-11.md`. NEXT: (d) _recently_fought (measure first). FOUNDING-ROW2 open. VACATED-REIGN1 filed. CONSOLE-STARTED1 filed (deploy-side).
- **HARNESS-RNG2** (tools; NOT blocking as of 2026-09-10) — live play is not cross-process reproducible: same code, seed 20260907 --weeks 14, two processes → 85/293 fighters differ in history length; pre-gen 0/1618. PYTHONHASHSEED=0 pair: 120 — hash salt is NOT the cause. uuid4-pinned pair: 52, but those runs took 47-57 min vs 5.6 (4,657 uuid4 calls per 2-week run cannot cost that) — wrapper slowdown UNEXPLAINED, so the 52 is not quoted. Third source unnamed (candidates: crc32(fight_id) → MC odds feeding a live decision; datetime.now in news). What IS process-stable: R06 pregen_to_live_seam = 8 in 7/7 runs across every perturbation, T-4, pre-gen rows, R10 histogram. Rule: a live-play count may gate a commit only if it was shown stable across ≥2 fresh runs on each side. HARNESS-RNG1's "process-stable" claim is pre-gen only.
- **LINEAGE1** — R05 FAIL 2 (Middleweight: reign[0].lost_to != reign[1].champion_id) in dump_stamp_a, uuidseed_1, hs0_1; PASS in dump_20260908, base_rerun, uuidseed_2, hs0_2 — identical code. A live belt transition INTERMITTENTLY writes an inconsistent lineage. Engine bug, not harness noise; the harness only makes it visible. Gate 0: diff the Middleweight belt_history of a FAIL dump against a PASS dump; find the transition path that wrote lost_to.
- **VACATED-REIGN1** — two-store finding surfaced during (c) Gate 0: vacate paths (`game_bridge.py:4045-4053` injury, `:6926-6933` player choice) write only to `_title_history`; `BeltHistory` has no `vacate_reign` method (crown_initial_champion + title_changes_hands only), so `_belt_history` reign stays `is_active=True` until a successor is crowned via title_changes_hands. GATE (window FP): between vacate and successor-crowning, the ex-champion's next win in that division renders 🛡️ under (c)'s new predicate — because `belt_history` still reports the reign open. Not fired in dump_champ_2 (0 vacates on the harness; needs browser exercise). SKETCH (Candidate B, do NOT ship as-is): add `BeltHistory.vacate_reign(wc, week, event_name, method)` in world_init.py near `:607 title_changes_hands`; call from both vacate sites with `event_name=self._dfc_label(current_week)` so `lost_event_number` parses. OPEN ITEMS for the arc's Gate 0: (1) `is_active` in draft — BeltReign.is_active is a `@property` (world_init.py:531-534) returning `self.lost_week is None`, so writing lost_week auto-flips it; validate the sketch relies only on writing lost_week/lost_event/lost_to/lost_to_name/lost_method and does NOT try to assign is_active directly. (2) Print title_changes_hands behavior when called on an already-vacated reign — does the vacate's lost_week/lost_event get overwritten by the successor's, or preserved? Print the sequence on a synthetic reign before writing the fix. (3) Off-week `_dfc_label` collision — a vacate on `week % 3 == 0` gets the previous card's label; measure the frequency of vacates on off-weeks in a longer run (not just this seed) before deciding whether to shift to `current_week - 1` or accept the collision.
- **BADGE-SEMANTICS1** — deploy #4 browser check (2026-09-11, Van): Jose Flores renders 6 🛡️ badges alongside a "5 defenses" text on the same profile page. The (c) predicate treats any in-window W as a defense; `was_title_fight` is not consulted, and `_convert_real_fighter` (game_bridge.py:7556) does not forward it to WebFighter anyway (ROW-SCHEMA1 dropped-keys list). Gate 0: print Jose Flores's raw fight_history rows including `was_title_fight`; confirm at least one in-window W is non-title (which the "5 defenses" count would exclude but the 🛡️ mark did not). Fix direction TBD — likely forward `was_title_fight` through _convert_real_fighter and add `and fight.was_title_fight` to the template's defended clause. Small, forward-only. Not fixed here.
- **RECORD-BOOK1** — deploy #4 browser check: on a fresh save with 9 founding reigns and ≥2 title changes, the "Most Title Reigns" and "Most Defenses" record-book sections render EMPTY while other sections populate. Gate 0: `grep -n "record_book\|Most Title Reigns\|Most Defenses" cage_dynasty_web/routes.py cage_dynasty_web/templates/records.html` to find the render path, then print whether it reads `_title_history` (which has founding + live changes) or `_belt_history` (which the Van 2026-09-11 VACATED-REIGN1 finding shows is populated at world_init crown_initial_champions but written asymmetrically after). Same two-store pattern as VACATED-REIGN1 is the leading suspect. Not fixed here.
- **FOUNDING-ROW2 symptom (streak+1)** — deploy #4 browser check: founding champions show streak = wins + 1 (Fedorov 9-0-0 with 10W streak; Flores 6-0-0 with 7W streak). Non-founding champion Jenkins shows 9-0-0 / 9W streak correctly — his history has no founding row. Third confirmation of the same class as playtest note #9 "streak vs record" (Almeida 8-0-0 / 9W). Gate 0: `grep -n "win_streak\|_compute_streak\|current_streak" cage_dynasty_web/game_bridge.py` to find the streak computation; print whether it filters rows by `method != 'Inaugural Crown'` or `event_number != 0` (STAMP now stamps founding as 0) or `was_title_fight` (won't help — founding IS a title fight). HYPOTHESIS (unmeasured): bridge stores `wins`/`losses` from a separate counter that already filters founding; streak reads fight_history unfiltered. FOUNDING-ROW2 open under the older filing; this is a symptom to add there.
- **COOLDOWN-CONSTANTS1** — _cooldown_weeks (~:15464) returns 0 for champions and all winners (Ship M2); COOLDOWN_CHAMPION=8 dead on the bridge path; COOLDOWN_WINNER=4 used only by SEED. Live gaps ≥4 only via booking lead time. R06's floor 4 is the instrument's, not the engine's; the seam is now stricter than live play (SEED's 4 = documented placeholder). Detail: filing §4.
- **DAMAGE-COOLDOWN1** (design, own arc) — Van 2026-09-10: winners should have cooldowns, derived from the fight (method, rounds, damage), not the result; today cooldown is a loser penalty. No medical-suspension mechanism exists (R07). Sequenced after playtesting the seeded opening cards.
- **TITLE-CADENCE1** (observation, n=1 seed) — a champion skipped for cooldown at wk 2 was not rebooked until wk 11; planned builder fires weeks 1-3 only, then lead-time booking (10-12w). Live title fights in 14 weeks 9→6 after CHAMP-A. Measure across seeds before scoping.
- **OFFWEEK-CARD1** (waste, harmless) — initialize_card_pipeline builds week 1..3 with num_cards=3 hardcoded; week 3 is an off-week, its card (labelled "Cage Dynasty 62", colliding with week 2) is built then discarded at advance (:3782-3784). No rows reach fight_history (census 0 collisions).
- **ROW-SCHEMA1** — two-stage lossy fight_history pipeline. Stage 1: raw writes — live fight_history rows write `round_finished`, pre-gen writes `round`; live rows omit `weight_class`; both write `event_number` post-STAMP. Stage 2: `_convert_real_fighter` (game_bridge.py:7556-7568) cherry-picks 8 keys into WebFighter.fight_history — `opponent_name, opponent_id, result, method, round_finished, event_name, fight_id, week` — **DROPPED KEYS from raw rows**: `event_number`, `weight_class`, `was_title_fight`, `specialty_method`, `opponent_rank_at_fight`, `round` (pre-gen only). (c) PREDICATE added `event_number` + `weight_class` back to the cherry-pick because the template needs them; the other four remain dropped. Forward-only unification, own commit. Consider: emit the raw row unchanged (Dict-in Dict-out) instead of cherry-pick, gate the raw shape at the write sites.
- **PERF1** — local timing 1d8b4e1 vs b6e1d74 on one seed to make the PA hypothesis (start-game 11.5→31.1s, advance-week 16.1→32.3s, N=1 each) a measurement.
- **OFFER-SCREEN1** — playtest note #15: Fight Offers screen currently shows Risk/Reward at ★★★★★ both sides; add opponent archetype, 4-6 stat side-by-side (link Compare), last-3 results, MC odds, contract context.
- **DEVELOPMENT1 Gate 0** — playtest note #3: OVR dropped 67→63 in one week while every reported stat delta was positive; measurement first (dump 18 stats at wk0 and wk1, recompute OVR both ways). — CLOSED by PLAYER-CREATE1 (b): the drop was the wizard's roll target vs _compute_ovr at first advance (Gate 0 two-formulas finding); creation OVR is now _compute_ovr. Remaining DEVELOPMENT1 Gate 0 items unchanged.
- **at_signing player path** — playtest note #5: capture fires on AI signing, not on `setup_fighter`; player's own fresh fighter shows blank. — CLOSED by PLAYER-CREATE1 (b): _create_player_fighter now writes ovr_at_signing and week_signed (R12 PASS).
- **god-stat + height/reach/nationality census** — playtest notes #6+#7: 11-of-19 stats at 95 on FLW champ (88 OVR); three fighters all "Brazil, 5'10\", 72\" reach"; plus `72""` double-quote render bug.
- **streak vs record** — playtest note #9: founding-title row counted in streak but not in record (Almeida 8-0-0 with 9W streak).
- **record-book stat keys** — playtest note #10: pre-gen fights carry no stat keys; "No records yet" for Sig. Strikes / Sub Attempts / Takedowns.
- **UI-strings batch** — playtest notes #8+#12+#13+#14: snake_case leaks in UI ("Fight Iq", "Bjj", "Kickboxing_coach", "calf_slicer", "General Mma"); Scout Report weaknesses as bottom-3 not absolute threshold; injury body-part vs technique mismatch ("Shoulder strain via calf_slicer"); coach corner generic; training focus label mismatch ("General Mma" vs "Sparring").
- **SECRET_KEY on PA** — 5b probe surfaced startup warning: `SECRET_KEY env var is unset` on PA, cookies forgeable. CLAUDE.md L1203-1206 already flagged the shape; this ships the env var.
- **Four dead fight_engine.py copies census** — root + interface/ + simulation/ + systems/. First three CLI-only (already Ship-1-queued); the 5th (`cage_dynasty_web/fight_engine.py`) stays. Reconcile with the pre-existing Ship-1 filing before `git rm`.
- **HARNESS-OUTPATH1** — `claude/tools/config_observe_harness.py` hardcodes output under `outputs/sm1/saveload1/`; PA-SMOKE1 wrapper had to text-sub the path. Fix: derive from CLI arg or env, its own single-purpose commit.
- **No dependency manifest** — repo has no `requirements.txt` / `pyproject.toml` / `Pipfile` / `setup.py`. PA's venv is out of git. Reproducibility docket.
- **ARCHIVE3** — CLOSED 1f1f08a (2026-09-09): Top-of-backlog (524 lines) moved verbatim to this file as the live board; CLAUDE.md 101,266 → 66,258 bytes. Second pass (KNOWN DEFECTS subsections, GOLDEN MASTER if superseded) not scheduled.

Full playtest context (all 19 items + measured/hypothesis-graded confirmations): `claude/playtest_notes_2026-09-07.md`.

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
- **Ship 1 — `git rm` the three orphaned CLI-era `fight_engine.py`
  copies (post-arc, filed 2026-07-12).** Full-tree hash compare on
  2026-07-12 proved 4 of the 5 stale `.py` copies are byte-identical
  PA-to-repo (no drift), and grep proved 3 of the 5 are genuinely
  unreachable — no code imports from them, in either the web tree or
  the CLI tree:
  - `/cage_dynasty/fight_engine.py` (root)
  - `/cage_dynasty/interface/fight_engine.py`
  - `/cage_dynasty/systems/fight_engine.py`

  The other 2 (`simulation/fight_engine.py` and
  `simulation/fight_integration.py`) are load-bearing for the CLI
  (`interface/cli.py`, `core/release_diagnostic.py`, four test files)
  and STAY. Whether to retire the CLI itself is a separate design call
  not part of this arc.

  **Deferred to post-arc for a specific reason**: the consolidation
  arc's premise is import-path stability. The `sys.path.insert` +
  force-delete hack in `game_bridge.py:190-199` exists specifically to
  beat root `/cage_dynasty/fight_engine.py`. Deleting that file
  mid-arc changes what the hack is defending against right before the
  file it protects gets relocated into. IMPORT-PATH-PROOF (`db15e3a`)
  has disarmed the concrete guard we need; the shadow file itself can
  wait five minutes post-arc.

  **PREREQUISITE** — reconcile PA's dirty root `fight_engine.py`
  before shipping this `git rm`. Root PA carries 11 manually-appended
  constants (see Known-hazards section "Root `fight_engine.py` on PA
  has 11 manually-appended constants — CONFIRMED REAL"). `git pull`
  has been tolerating this for months only because the repo copy
  hasn't changed. This `git rm` would be the change that makes git
  refuse — deploy would error mid-pull with "would overwrite locally
  modified file." Order of operations must be:
  1. PA console: `cd ~/cage_dynasty && git checkout HEAD -- fight_engine.py`
     (restores PA's copy to match repo state; the appended constants
     go into the diff we're about to make anyway)
  2. Local: `git rm fight_engine.py interface/fight_engine.py systems/fight_engine.py`
  3. Also clean the orphaned `.pyc`: after step 1, run
     `cd ~/cage_dynasty/__pycache__ && rm fight_engine.cpython-313.pyc`
     on PA console (pyc without matching source is inert but tidy)
  4. Local: single-purpose commit + `./deploy.sh`
  5. Confirm IMPORT-PATH-PROOF still names the `cage_dynasty_web/`
     copies (regression test, unchanged in this ship)
- **World-gen books EVERY event's main_event as a title fight
  (surfaced by Stage 0c golden-master fixture 2026-07-12).**
  Verified on seed=1000 world (60 events): 60 main_events, all
  60 title fights, **zero non-title main events in the entire
  simulated history**. `card_slot` is not broken — all five slot
  values (`main_event`, `co_main`, `main_card`, `prelims`,
  `early_prelims`) present in the harvest. This is genuine
  matchmaking behavior in `world_init.HistorySimulator`, not a
  generator bug.

  **Three separate concerns, one root cause:**

  1. *Probably a real matchmaking bug.* Real MMA promotions run
     ~4-6 title fights a year across ~40 events. Pre-gen giving
     the player a history where every event since Cage Dynasty 1
     was headlined by a championship bout makes the belt worth
     nothing — no scarcity, no build, no meaning. For a game
     whose north star is "the simulation made them care,"
     inheriting a world where title fights are the *default*
     is a world where the title does not mean anything. Fix
     candidate lives in `world_init.HistorySimulator._build_event_card`
     or its callees — title-fight booking discipline should be
     rank-gated + spacing-gated, not defaulted.

  2. *Real oracle gap for the consolidation arc.* Stage 0c
     fixture correctly reflects pre-gen population (that was
     the right call — synthetic populations produced the
     99% striker-vs-striker artifact this arc has been
     defending against). But the fixture has 800 modal + 15
     coverage 5R title fights and **zero 5R non-title mains**.
     If live-play's matchmaking booker produces non-title
     main events, that live code path is invisible to the
     oracle. Stage 2b could break it and every gate would
     stay green. **Check needed before Stage 2a**: does
     `card_builder` / `matchmaking` in live-play produce 5R
     non-title mains? If yes, add a small synthetic coverage
     cell (~3-4 entries, structurally constructed) to the
     fixture and regenerate. If no, close 0c as-is.

  3. *Independent gameplay finding.* The pre-gen belt-story
     work already filed as PRE-GEN WORLD COHERENCE epic
     (2026-07-11) intersects with this — belt-state consistency
     bugs surfaced on strawweight (fighter defending a belt
     he'd already lost, ladder disagreeing with reign records)
     probably compound with 60-events-of-title-fights driving
     lineage churn much higher than intended. Bundle both
     under the epic when it picks up.

  Do NOT fix any of these mid-arc. Consolidation is import-path
  and behavior stability first; pre-gen matchmaking is a
  substantive design touch and its own multi-session ship. File
  and hold.

  **Companion finding — pre-gen rest cadence is compressed** (measured
  2026-07-12 by Stage 0d A7 diagnostic). `world_init.HistorySimulator`
  DOES consult a cooldown gate: `_is_fighter_available` at
  `world_init.py:1737-1751` enforces `current_week - fighter_last_fight
  >= 4`. So "no cooldown at all" is false. But the floor is 4 weeks
  and it pins the distribution hard:

  ```
  seed=1000, HISTORY_WEEKS=60, 293 fighters, 289 with >=2 fights,
  1328 consecutive-fight gaps:

    min:    4        p10:    4     mode:   4  (301 hits, 22.7% of gaps)
    median: 7        mean:   9.22  p90:   20
    p99:   32        max:   45     gaps<4: 0  (floor enforced)
  ```

  **Measurement caveat — read before citing any of these numbers.**
  The 60-week window RIGHT-CENSORS the gap distribution. A fighter
  with a genuine 30-week layoff only registers a gap if BOTH fights
  fall inside the 60-week window; a fighter who fights at week 40
  and would have fought at week 70 shows NO gap at all (the second
  fight is outside the window). Long gaps are SYSTEMATICALLY
  UNDERREPRESENTED. The bias hits different stats in DIFFERENT
  DIRECTIONS:

  **SURVIVES the window (trustworthy):**
  - `mode = 4` — robust. Long gaps were never the mode; removing
    them can't change the modal value.
  - `301 gaps on the floor` — a raw COUNT, not a share. Censoring
    can only ADD unobserved gaps, never remove observed ones. So
    301 is a hard LOWER BOUND on the true count.

  **BIASED HIGH by the window:**
  - `22.7% (share of gaps on the floor)` — inflated, because
    censoring shrinks the DENOMINATOR (the long gaps that would
    dilute this share never get observed). True share is lower.
    Do NOT tune against 22.7%, and do NOT read a future drop in
    this share as improvement — it may be censoring arithmetic,
    not a better scheduler.

  **BIASED LOW by the window:**
  - `mean = 9.22`, `p90 = 20` — the missing long-tail gaps would
    pull both stats up. True distribution has a heavier right tail
    than these numbers show. Do NOT tune against 9.22 as if it
    were a clean measurement.

  The FINDING is unchanged: the scheduler is pressed flat against
  its minimum. But the numbers that PROVE it are the mode and the
  raw count, not the percentage. When 301 fights land on the
  earliest legal date, the scheduler isn't choosing — it's taking
  the first legal option every time. Same bug as 60/60 title-fight
  bookings: the "default" won.

  Real UFC cadence is typically 12-26 weeks between fights for
  active competitors. Pre-gen mode is 4 and 301 fights land on
  the floor. Bundle under the same PRE-GEN WORLD COHERENCE epic
  as the 60/60 bug. Do NOT fix mid-arc.
- **TWO-ENGINE CONSOLIDATION arc (HIGH, filed 2026-07-11).**
  `fight_engine.simulate_fight` (pre-gen path) and
  `fight_integration.simulate_narrated_fight` (live-play path) are two
  simulators with parallel exchange loops that have drifted since
  2026-06-14 (`d347de9` "all in fight_integration layer"). Same fighters,
  same seeds: pre-gen 26% finish rate vs live-play 98% on striker-vs-
  striker ⚠ **the "26/98" figures are FALSE — see full correction in
  "Key constants" section below.** Re-measured pooled 10-seed:
  42% pre-gen / 81% live-play on SxS (Δ +38.8pp not +72pp). Direction
  survives; magnitudes were pre-uuid-patch and unreproducible.
  FI has ~8 accumulator-TKO paths and ~6 style windows FE
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

    Partial fix landed 2026-07-11 (BELT-STORE-UNIFY1, `e6b8033`, forward-only):
    (1) belt-history writes are now correct for transfer / vacant / defense;
    (2) historical saves from before the ship still carry the fork — the
    strawweight evidence above was observed on a pre-ship save and remains
    representative of that state; (3) load-time reconciliation for existing
    saves is filed separately and remains open, per e6b8033's own
    commit-message deferral.
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
- **LIVE-PLAY MATCHMAKING backlog (HIGH, filed 2026-07-12).** Distinct from the
  PRE-GEN epic above — this is the *live-play* card-building surface, which has
  its own set of drift issues surfaced by CARD-PATH DIAG and PATH-B INTEGRITY
  DIAG on Van's session save (`bridge_50e1bdaa-..._slot2.json`, 3 events, wk1-3).
  Threads:
  - **Path A over-issues title fights.** `_build_card_for_week` stamps title
    fights on both `main_event` *and* `co_main` slots on every card the session
    generated (4 title bouts across 18 fights on 3 cards). Same underlying
    dysfunction as the pre-gen 60/60 title bug but through a different code
    path — cannot be closed by fixing world_init. Rank-gating + spacing-gating
    audit needed in `_build_card_for_week` and the card-slot title-flagging
    logic. Filed but not scoped.
  - **PATH-B-BOOKING1 (shipped as `8ecec6f`; previously framed
    "queued, scope locked" in error).** Deleted `_simulate_ai_fights_week`
    entirely — 548 lines, one production caller (pre-ship, `game_bridge.py:3617`), zero
    helpers reachable only from it (verified). Off week is honest: no
    fights, no card, no event numbering advance. Closed the class of Path B
    bugs (double-booking, per-fighter cooldown bypass, title over-issuance in
    the fallback path, absent card-summary telemetry) as one deletion. This
    supersedes the "Off-week semantics contradiction" note below.
  - **`_dfc_label` off-week collision closes as a byproduct of PATH-B-BOOKING1.**
    The function itself has 15 call sites (`_top_up_pipeline`, quarantine
    messaging, `_run_real_engine`, `_book_title_fight`, pipeline pop-loop, etc.)
    and **stays**. What dies is the specific collision instance: Path B minting
    an off-week event name via `_dfc_label(week)` after Path A had already
    named a card the same week. Prior in-conversation filing of this under
    PRE-GEN WORLD COHERENCE was mis-scoped — the collision is live-play, not
    world-gen. Any *other* `_dfc_label` collision (e.g. two pre-built cards
    landing on the same week) is separate and not addressed by PATH-B-BOOKING1.
  - **AVAILABILITY-DRIVEN CADENCE (multi-session, deferred).** Real successor
    to both the 3-week off-week rule *and* the per-fighter cooldown floor.
    Fighter availability (KO/injury pushes out, clean-decision win pulls in)
    would govern card frequency emergently instead of by calendar constant.
    Off weeks become weeks where too few fighters are available. Layoffs
    become story. Downstream of PATH-B-BOOKING1.
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
- **`get_fight_commentary` synthetic fallback is dead code — DEAD
  (falsified by arm-3 live harness, 2026-08-19).** Reviewer-originated
  inference from a folded read: the eng_result-extraction branch's loop
  had a `fight_result = fight` assignment (`game_bridge.py`, currently
  ~`:18057`) that was dropped in transcription, leading to the claim
  that `if fight_result:` at the synthetic-fallback branch could never
  fire and the synthetic fallback was never-executed dead code. Falsified live during COMMENTARY-STALE1
  gate design: a two-line harness (bridge instance, `_completed_events`
  populated with `fight_id` but no `_engine_result`, empty
  `_fight_commentary`) returned 6 synthetic lines starting
  `['=== ROUND 1 ===', '{Winner} and {Loser} touch gloves.', ...]`
  with `cached_after_call: True` in OLD bytes — direct empirical
  proof of reachability. Gate arm-3 then reproduced this in the full
  4-arm pack (OLD via `6b873c4` worktree, NEW via current fix). The
  synthetic block STAYS live under COMMENTARY-STALE1's shipped fix,
  now uncached; it remains explicitly EXCLUDED from the dead-code
  strip scope (see item 4 UPDATE in COMMENTARY-STALE1's SHIPPED block).
  Filed under Cleared-suspects so the "synthetic branch is dead"
  reading never gets re-proposed as a strip target. Two-line lesson:
  folded reads can drop assignments as easily as they drop
  references; verify branch reachability with a harness, not with
  code-inspection alone.
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
- **"Do unranked fighters have a way to enter the ladder in live-play?" — YES,
  confirmed 2026-07-12 (LIVE-PLAY UNRANKED PIPELINE VERIFY).** Question raised
  during PATH-B-BOOKING1 scoping as a risk check against Option A (delete Path
  B). Read-only grep + save inspection confirmed the mechanism is present in
  Path A and fires in production:
  - **Booking mechanism** — `_build_card_for_week` has explicit unranked
    handling: `unranked_pool = [f for f in available if f.fighter_id not in
    ranked_ids]` (game_bridge.py:~16649) in the "1 ranked left" branch, scored
    via `_matchup_score` with a 75/25 competitive/step-up split (MATCHMAKING-
    ENFORCE1 constants). Delegates to `matchmaking.find_unranked_matchup`
    (unranked-vs-unranked, `matchmaking.py:1273`) and `find_ranked_matchup`
    (ranked-vs-ranked, `:1233`). Multiple callers, 12 "unranked" hits in
    `_build_card_for_week` alone.
  - **Promotion mechanism is score-driven, not slot-gated** — `matchmaking.
    calculate_ranking_score` at `:658` computes rank score from wins / losses
    / opposition quality; `game_bridge._update_rankings_after_fight`
    (`:13340`) fires after every fight regardless of ranked-vs-unranked pool.
    Sort at `:13413` produces the top-15 purely from score. Any win — even
    unranked-vs-unranked prelim — contributes to rank score, so an unranked
    fighter can climb into the top-15 through the normal pipeline.
  - **Verified live** — Van's session log wk1 shows 7 fighters emitting
    `📈 [RANKINGS] {name} {wc}: entered top 5 at #N` (Timothy Lewis FLY,
    Dennis Lee BAN, Kennedy Adesanya BAN, Scott Davis FEA, Wu Li LIG, +2).
    Ladder promotion pipeline fires in production. Not a theoretical
    mechanism — actively producing ranked fighters from the unranked pool.
  - **Consequence for PATH-B-BOOKING1**: Path B's unranked handling is not
    load-bearing. Deleting it leaves Path A's real unranked pipeline
    untouched. The "how does the ladder have a bottom rung" fear is
    unfounded — Path A has been the answer to that question all along.
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

  **⚠️ CORRECTION 2026-07-12 — this "substantively closed" verdict was WRONG
  for Path B specifically. The 16w rematch minimum + intervening-fight guard
  + per-fighter cadence discipline shipped in `07491d1` were added to Path A
  (`_build_card_for_week` → matchmaking helpers) and to world-gen. They were
  never wired into `_simulate_ai_fights_week` (Path B), which has its own
  soft, opponent-specific `self._recently_fought(f1, f2, weeks=4)` and no
  per-fighter cooldown of any kind.**

  **Measured against actual save data (PATH-B INTEGRITY DIAG, Van's session
  save `bridge_50e1bdaa-..._slot2.json`, wk3 Path B card):**
  - **6/6 consecutive-fight gaps under 4 weeks** on Path B (including 2 gaps
    of 0 weeks — same fighter booked twice on the same off-week card:
    Dieselnoi Fairtex main_event KO + prelim TKO; Usman Ngannou two prelims).
  - Path A on the same save: 0 sub-4w gap violations, matches the
    2026-07-03 autosave finding.

  The "4-week cadence gate exists and works" reading of MATCHMAKING-RECONCILE1
  was TRUE for the 2026-07-03 autosave because that save's data was harvested
  from a state where Path B hadn't yet fired an off-week card during the
  measurement window. As soon as an off-week landed with a healthy pipeline,
  Path B kicked in and produced the pattern documented above. The reconcile's
  denominator was Path A only. **Documented as FALSE for Path B, not quietly
  amended, because a wrong number sitting in the source of truth is worse
  than an uncomfortable correction.**

  PATH-B-BOOKING1 (LIVE-PLAY MATCHMAKING backlog above) closed this by
  deleting Path B entirely — the wrong cadence gate stops firing because
  the code that ignored the right one stops existing. Path A's cadence
  discipline stays untouched.

**Deferred low-priority cleanup:**
- Sub-bug O.1 — asymmetric round override at `fight_integration.py:1228-1229`.
  Bundle with any future `fight_integration.py` touch.
- Off-week semantics contradiction — surfaced in TITLE-TRANSFER-DIAG1. Off weeks
  discard the pipeline card but the fallback path (`_simulate_ai_fights_week`)
  still generates fresh AI fights, contradicting the "no event" print.
  **Escalated 2026-07-12 from "design call" to real correctness bug** — the
  fallback is now known to double-book fighters and bypass every cooldown gate
  (see PATH-B INTEGRITY DIAG on Van's session save: 4 duplicate-fight-instances
  on wk3, 6/6 gaps under 4w). Answered by PATH-B-BOOKING1 in the LIVE-PLAY
  MATCHMAKING backlog above.
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

