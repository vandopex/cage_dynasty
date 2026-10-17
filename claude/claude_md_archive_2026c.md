# CLAUDE.md archive 2026c — OWED ITEMS + 5c1477d resolution
Moved verbatim from CLAUDE.md L989–1008 at cd6f7e80 (ARCHIVE4, 2026-09-22). Do not edit; history.

### OWED ITEMS CARRIED (from MC ODDS ship 2026-08-19)

- **PA timing measurement pre-N-lock.** Dev measured 15.62 ms/sim
  full-path this ship. Spec expects 2-5× slower on PA (INFERRED,
  not measured). Recompute on PA before adjusting `MC_ODDS_N_BASE`
  or `MC_ODDS_N_MAX`. Needs a live card to measure meaningfully;
  Van starts fresh saves.
- **ENGINE-STRIKE-SENS1 design call** — RESOLVED 2026-08-22:
  skill-into-damage chosen first (Van), shipped as STRIKE-SKILL-DMG1
  phase 1a at K=1.0 (see filing above). Remaining fix candidates
  (de-cliff kicks, landing curve, classifier, SD, judge weights)
  carried in that filing's QUEUE, each as its own future arc.

### `5c1477d` resolution (ledger correction)

Commit `5c1477d` ("docs: close COMMENTARY-STALE1 arc + convert
FOTN caveat-#2 to MEASURED", 2026-08-18) exists and is a docs-only
close-out. Its omission from the prior close-out table was a
ledger gap, not fabrication.


SUPERSEDED by b8f45cb 2026-07-14 (ORACLE-CONFIG-TRIPLE-TEST1), one day after filing; tripwire behaviour not re-measured. Moved ARCHIVE4 commit 2.
### Stage 0d `_assert_sanctioned_config` is a tripwire for ORACLE-BRIDGE1 too [filed 2026-07-13]

Same pattern already documented for Stage 0c: `_assert_sanctioned_config`
at `fight_engine.py:~863` raises `AssertionError` on any `(exchanges,
damage, standup)` triple outside the three sanctioned allowlist entries
(`LIVE_PLAY`, `PRE_GEN_LEGACY`, `FI_FALLBACK`). The assertion fires
INSIDE `simulate_narrated_fight`, before the fight body runs.

**Consequence for ORACLE-BRIDGE1 perturbation testing:** any nudge to
`damage_multiplier`, `exchanges_per_round`, or `standup_threshold` in
`game_bridge.py`'s `_FightConfig(...)` constructions
(`:13597, :17518`) trips the assertion first. The fixture never sees
outcome divergence because the fight never runs. Instead, the crash
cascades via the `_eng` bug above and 74/78 fights die — the fixture
"catches" on `meta.total_captured_fights: 78 != 4`, which is corpse
count, not detection.

**Two-step proof procedure for future config-triple perturbation
tests** (same shape as Stage 0c's discrimination procedure):

1. Prove the assertion fires: install perturbation, run fixture, observe
   `AssertionError` in the checker stderr. Undo.
2. Temporarily widen the allowlist in `fight_engine.py` — add the
   perturbed triple to `_SANCTIONED_TRIPLES` so the assertion passes.
   Re-run perturbation. Verify fixture catches on outcome fields.
   Undo the widening.

For discrimination proof at the config-triple axis, ORACLE-BRIDGE1's
`perturbation_test.py` currently sidesteps this by targeting
`submission_progress_to_finish` (a non-asserted `FightConfig` field).
That's a real signal for "config is passed correctly" but does NOT
prove the fixture catches the specific triple values. Extending to
the full triple axis needs the two-step procedure above.

**Third instance of this pattern.** Stage 0d assertion also blinded
POISON-0.42 (see the poison test — checker returned 928/928 with
poison in place). Stage 0d protects live-play behavior but shadows
diagnostic tools that want to observe what fights do under out-of-band
configs. Documenting the pattern here so the next diagnostic tool
starts with awareness instead of hitting it fresh.

NAMING DEFECT, open, no code change; one-line hazard retained in CLAUDE.md Key constants. Moved ARCHIVE4 commit 2.
### `standup_threshold` observed effect is not referee-standup frequency [filed 2026-07-14]

`fight_engine.py:FightConfig.standup_threshold` is named for governing
how often the referee stands grounded fighters up. The Phase 1
standup-lever discrimination probe measured its actual observed
effect and it isn't that.

**The measurement:** the standup-lever probe (Phase 1 of the
authored two-phase design, session dated 2026-07-14) ran all 78
ORACLE-BRIDGE1 fixture fights through `fight_engine.simulate_fight`
at both `standup_threshold=6` and `standup_threshold=10`, same
fighters, same seeds, one variable moved. Required temporary
in-memory widening of `_SANCTIONED_TRIPLES` to admit `(55, 0.42, 10)`;
widening reverted post-measurement, `cage_dynasty_web/` working tree
verified clean, Stage 0c 928/928 and ORACLE-BRIDGE1 78/78 re-verified
GREEN after revert.

**What changed between the two configs (Phase 1 aggregates):**
- 73 of 78 fights had different outcomes at `standup=10` vs `standup=6`
- 38 of the 73 had a different `method`
- 16 of the 73 had a different `winner_id`
- All 73 had different `control_time_per_round` distributions
- **0 of the 78 had a change in `ref_standup_events` count** — the
  dial moved 73 fights' outcomes without changing how many times
  the referee stood fighters up on any of them

**Observed mechanism:** the standup threshold governs how many
exchanges of ground-inactivity accumulate before an implicit stand-up
would fire. On this fixture, the value change affected outcomes by
shifting how long ground state persists per exchange, which reroutes
the downstream RNG-consumption cascade (see the "STAGE 1 addendum —
random-coupling hazard" section elsewhere in this file for the
RNG-coupling framing). The dial is wired; its effect on outcomes is
real; its mechanism is not what the name describes.

**Scope of this finding, stated explicitly:** single fixture (78
ORACLE-BRIDGE1 fights), single comparison (`standup_threshold=6` vs
`standup_threshold=10`, `damage_multiplier` held at 0.42,
`exchanges_per_round` held at 55). "No change in `ref_standup_events`"
was observed **on this measurement.** This finding does NOT establish
that the standup mechanic is inert at other threshold values, on
ground-heavier matchup distributions, or at other damage/exchange
settings — those weren't tested. The claim is "named mechanism ≠
observed mechanism, as measured on this fixture," not "the knob does
nothing anywhere."

**Trap for future work:** anyone modifying `standup_threshold` and
reasoning from the name (governs referee standups) will be wrong
about what it does on distributions like this one. Its observed
outcome-changing effect runs through ground-state-persistence and
RNG-coupling. Treat as a ground-state-cascade knob, not a referee-
frequency knob, until measurement on other distributions says
otherwise.

LATENT per filing; elif still at game_bridge.py:7392 at 3896da9; one-line hazard retained in CLAUDE.md Known hazards. Moved ARCHIVE4 commit 2.
### `game_bridge.py` "backfill" branch is metadata-only [filed 2026-07-24]

**`game_bridge.py` "backfill" branch backfills metadata, not stats —
latent.** The `elif` following the tier-1-present path in the fighter-
data assembly, commented "backfill from world gen data," writes exactly
4 keys: `style`, `age`, `country`, `potential`. It writes zero of the 18
stat keys `_a` reads. A `FighterRecord` reaching this branch has all 18
engine stats absent from `_fighter_data` and stays tier-2/tier-3
eligible on every one — the "backfill" does not backfill what the engine
consumes. Comment marked false-as-written rather than corrected in code
(docs commit only). **Latent, not live:** per the tier-3 census this
flow fired zero times across available saves; a shape that would inject
default/offset stats *if* a record ever reached it, not an observed bug.
Confirmed on fresh bytes at HEAD `8e721c9`, this session.


ARCHIVE4 commit 3 — Top-of-backlog status paragraphs (deploy #6/#7 era), superseded by deploy #8 (CLAUDE.md L230–231 at f0684fa4)
<!-- ARCHIVE3 --> Next in order (Van's ruling 2026-09-10, resolution recorded 2026-09-14, deploy #6 2026-09-16): (d) resolved into RECENTLY-FOUGHT1 (deferred; player-only caller, negligible) and REMATCH-COOLDOWN1 (CLOSED 2026-09-16 by browser check; shipped 9faeba8, on PA at 46c094f). FOUNDING-ROW2 also CLOSED 2026-09-16 (shipped 46c094f, canonical streak walkers, browser-verified). NEW dockets from deploy #6 browser session: BELT-LINEAGE1, RECAP-STALE1, HISTORY-CAP1, NAME-COLLISION1, DIVISION-GENDER1, DRAW-SEMANTICS1 (upgraded), HARNESS-ENV1, DUMP-PROVENANCE1. Continuing: PROSPECT-BONUS1 instrument rule → PROSPECT-BONUS1 retune. WEEK-AXIS1 (a)+(b)+(c) ON PA at 46c094f (deploy #6, 2026-09-16, API-driven, 10/10 gates PASS, filing claude/deploy6_2026-09-16.md). Filings claude/week_axis1_b_filing_2026-09-10.md + claude/week_axis1_c_filing_2026-09-11.md + claude/deploy4_2026-09-11.md + claude/rematch_cooldown1_filing_2026-09-14.md + claude/deploy5_2026-09-15.md + claude/deploy6_2026-09-16.md. Behind: see the board.
<!-- ARCHIVE3 --> DEPLOY #7 (2026-09-20 PDT, filing claude/deploy7_2026-09-20.md): shipped 25adadd (CHAMPIONS-PAGE1) + 6540d3c (RECORD-BOOK-REPOINT1) to PA at 4e72bab; steps 0–11 PASS; runtime set N=1 (cage_dynasty_web/game_bridge.py); IMPORT-PATH-PROOF confirms cage_dynasty_web/ resolution; DEPLOY-GATE-REF1 (a) invoked; Van's PA browser check PASS 2026-09-20 (deploy7 filing §k); RECORD-BOOK1 + BELT-LINEAGE1 display half closed.

ARCHIVE4 commit 3 — Current top-of-list section, redundant with Top-of-backlog pointer (CLAUDE.md L545–551 at f0684fa4)
## Current top-of-list

See `claude/backlog.md` for the live backlog board (moved out 2026-09-09 by ARCHIVE3; rewritten 2026-07-03 prior). <!-- ARCHIVE3 -->
The April-May items previously listed here (FOTN wire, fighter profile polish,
card-builder slot assignment) all shipped and were removed to prevent stale
references. Historical ship recaps are in `CLAUDE_archive.md`.


ARCHIVE4 commit 3 — legacy save migration record, completed 2026-07-03 (CLAUDE.md L157–161 at f0684fa4)
**Legacy save migration already ran** on both dev and PA — `bridge_slot*.json` and
`bridge_autosave.json` were backed up (`.bak`) then renamed to `bridge_van_*.json`.
The old `.legacy_claimed` marker file (from the retired first-visitor auto-claim) is
inert — no code reads it anymore.

