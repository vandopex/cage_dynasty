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

`e1be619` (COMMENTARY-RETARGET-PORT, 2026-07-07) later retargeted all three
ships onto `narrative/commentary.py`; they are no longer inert.

These features will NOT appear in-game until either (A) the changes
are ported to narrative/commentary.py, or (B) wsgi.py is amended to
add repo root to sys.path (which reintroduces the CLI-fork shadowing
that wsgi.py was specifically designed to prevent). **NOT YET
FIXED — deferred to next session for a clear-headed A-vs-B decision.**

The (A)/(B) framing above is documented-was-wrong: accurate at
authoring time, superseded ~50 minutes later when Option (A) shipped
as `e1be619` (COMMENTARY-RETARGET-PORT). The features now appear
in-game.

Present at HEAD (verified this session, 2026-07-19):
`narrative/commentary.py` is committed and present in the live file at
HEAD. The file's latest touch at HEAD is `b8c7136` (COMMENTARY-RNG-
DECOUPLE), layered on `e1be619`'s retarget. PA deploy-verification was
NOT re-run this pass; whether PA has pulled `e1be619` since 2026-07-07
is not attested by git alone and is out of scope for this docs commit.

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

## 🚨 CRITICAL — GOLDEN MASTER IS A FIGHT-ENGINE ORACLE, NOT A LIVE-PLAY ORACLE

**Measured empirically 2026-07-13** by the POISON-0.42 diagnostic. The
Stage 0c golden master at `outputs/stage0c_golden_master/checker.py`
imports `fight_engine` and `fight_integration` **directly** at
`:35-36`. It **never** imports `game_bridge`. Verified by installing
poison RuntimeErrors at three fallbacks in `game_bridge.py:210/212/269`
that raise on live-app import: the fixture returned **928/928 PASS
with the poison in place** because the fixture never loaded the module
that would have fired it.

**Consequence, load-bearing for the consolidation arc:**

- `game_bridge.py` is ~21,400 lines and is the orchestration layer
  through which every live fight actually runs. **The golden master
  does not cover it.** Any bug living in `game_bridge`'s fight path —
  a wrong config passed, a fallback captured, a knob dropped, a
  matchmaker firing that shouldn't — is **invisible to the gate this
  arc has been trusting**.
- **PATH-B-BOOKING1 is the proof this already happened**: 548 lines
  of broken booking, resolving ~53% of every fight for months, and
  the golden master was byte-identical the entire time it ran AND
  after we deleted it (`8ecec6f`). "928/928 unchanged" was recorded
  as confirmation the scoping held. It was equally confirmation that
  **the oracle can't see that layer at all**.
- Everywhere the arc's language says "928/928 proves live-play
  unchanged" is **overclaiming**. The correct claim is "928/928 proves
  the fight-engine layer is unchanged for the inputs in the fixture."
  Whether live-play behavior changed is a separate question the
  fixture does not answer.

**Prerequisite for Stage 2a:** Stage 2a physically relocates FI's
loop body into `fight_engine`. If `game_bridge` sits between the caller
and the code being moved (probable but unverified as of this notice),
then the gate for that relocation is not observing the caller. **The
oracle-coverage gap needs closing before Stage 2a, not after.** Filed
as ORACLE-COVERAGE1 (diagnostic).

**Fixture inputs and fixture module coverage are two different limits.**
Section §2 of "PRE-GEN WORLD COHERENCE epic" below already noted a
*fixture-input* gap (fixture lacks 5R non-title mains). This notice is
about the *fixture-module* gap — a strictly larger blind spot. Both
apply. Do not conflate.

## 🚨 CRITICAL — "SAME SEED" MEASUREMENTS HAVE NEVER BEEN REPRODUCIBLE

**Measured empirically 2026-07-13** by the ORACLE-BRIDGE1 determinism
probe. `uuid.uuid4()` uses `os.urandom` and **ignores `random.seed()`
entirely**. The game generates 30+ IDs per new_game via `uuid.uuid4()`
(fighter_id, camp_id, fight_id, event_id, news_id, offer_id,
contract_id, prospect_id, coach_id, reign_id, champion_id, game_id).
Each new run reshuffles every ID, and downstream operations that read
those IDs — matchmaking sorts, set iteration, dict-key lookups — see
different pairs, different orders, different fights.

**Direct measurement:** identical `random.seed(42)` + `PYTHONHASHSEED=0`
+ subprocess-fresh state, two runs = **29 bouts vs 26 bouts** and the
first fight_id differed on the first pairing.

**Consequence — every "same seed" measurement in this project's
recorded history was measuring a *differently-shuffled world*:**

- The `outputs/wr_bjj_drift_diag1.md` "Harness A 47.3% CI [43.3, 51.4]
  N=577" and every certified-baseline number under `CLAUDE.md`'s
  "Certified cell baselines" section.
- The PIPELINE-DENSITY multi-seed "10/10 seeds landing on week 4"
  finding.
- The PATH-B-BOOKING1 before/after 5-run "distribution" measurement
  that had to report a distribution instead of a single point.
- Every synthetic probe under `outputs/` that fixed `random.seed(N)`
  and re-ran.

**The big findings survive** because they were measured across enough
noise to hold up: "10/10 seeds on wk 4" is 10/10 across 10 truly
distinct worlds, which is a *stronger* signal than 10 seeds on the
same world. But **exact numbers are per-world**, not per-seed, and
tuning a constant to hit a specific single-point number was always
noisier than the arithmetic suggested.

**Reproducibility is achievable** via monkey-patching `uuid.uuid4()`
to draw from a seeded `random.Random` stream. Verified 2026-07-13:
identical byte-equal `completed_events` across two subprocess-fresh
runs. **But that patch lives in the harness, not in production.**
Live saves keep genuine random UUIDs; making saves reproducible as a
feature ("share this seed, get this exact world") is a real ship,
not filed here.

Filed as a fact about all prior measurements, not as an action item.
Trust distributions over single seed-runs when reading historical
diagnostics.

## 🚨 KNOWN DEFECTS — filed, not scheduled

### `_eng` UnboundLocalError at `game_bridge.py:13816` — one bad fight cascades [filed 2026-07-13]

`cage_dynasty_web/game_bridge.py:13633-13816` — the Path A fight loop:

```python
if FIGHT_ENGINE_AVAILABLE:
    try:
        # ... setup ...
        _eng = _simulate_narrated_fight_fn(fa1, fa2, ...)     # :13633
        # ... commentary storage, winner/loser derivation ...
        winner = f1 if _eng.winner_id in (...) else f2         # :13725
        # ...
    except Exception:
        # Fallback: set winner/loser/method/rnd via score-based path
        winner = f1 if f1_s >= f2_s else f2                    # :13744
        # ... but _eng is NEVER bound here
# Later, OUTSIDE the try/except:
_specialty = canonical_specialty_method(
    getattr(_eng, 'method', '') or method,                     # :13816
    _eng_sub_type,
)                                                              # UnboundLocalError
```

When `_simulate_narrated_fight_fn` at `:13633` raises, the `except`
at `:13741` catches it and builds a score-based fallback (sets
`winner/loser/method/rnd`). **But `_eng` is never bound in the except
path.** The downstream line at `:13816` reads `getattr(_eng, 'method', ...)`,
which raises `UnboundLocalError` — **crashing not just the current
fight but the whole card via the outer exception boundary in
`_advance_week_impl:3589`.**

**Surfaced by ORACLE-BRIDGE1 perturbation #1** during the initial
damage-multiplier nudge test: any damage_multiplier ≠ 0.48 tripped
Stage 0d's `_assert_sanctioned_config` inside `simulate_narrated_fight`,
which raised, which unbound `_eng`, which crashed 74 of 78 fights
in the fixture run. **Dormant in production today** because
`simulate_narrated_fight` doesn't normally raise (Stage 0d assertion
only fires on tampered configs, which never occur in prod). **Fragile
if it ever does raise** — a single bad fight would cascade into
killing the rest of the card.

**Fix candidate (not scheduled):** add `_eng = None` at the top of the
`try:` block (or in the `except:` handler) so `getattr(_eng, 'method', '')`
returns `''` cleanly. One-line fix. Waiting on scope alignment because
touching this file requires re-verifying against both Stage 0c and
ORACLE-BRIDGE1.

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

### `_create_player_fighter` fighter_id falls back to a memory address [filed 2026-07-13]

`cage_dynasty_web/game_bridge.py:2418`:

```python
fighter_id = fighter_data.get('id', f"player_fighter_{id(fighter_data)}")
```

When `fighter_data` doesn't include an `id` key, the fallback embeds
Python's `id(fighter_data)` — a **runtime memory address** — into the
fighter_id string. That value:

- Is **nondeterministic** across runs (address randomization).
- Is **non-portable**: a save file containing `player_fighter_{addr}`
  cannot round-trip meaningfully across Python processes.
- **Landed in ORACLE-BRIDGE1's first fixture run** — the checker failed
  on the PLAYER tier because run 1's `player_fighter_4528888384`
  differed from run 2's `player_fighter_4310611776`. Fixed in the harness
  by passing an explicit `id` field.

**Why it hasn't bitten hard yet:** the two real callers (new-game route
+ setup wizards) always populate `id` via the prospect selection flow,
so the fallback is dormant in normal play. But it's a live path — any
future caller that skips `id` writes a nondeterministic ID into the
save.

**Fix candidate (not scheduled):** replace with a stable default —
`fighter_id = fighter_data.get('id') or f"player_fighter_{uuid.uuid4().hex[:8]}"`
— so the fallback still uniqueizes without embedding process state.
Or hard-fail the missing-id case since it's a caller bug.

**Ship discipline:** the ORACLE-BRIDGE1 harness works around this by
requiring explicit `id`. That is a HARNESS workaround, not a fix. File
as production defect. Do NOT fix inside ORACLE-BRIDGE1 — single-purpose.

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

**Where startup diagnostics land on PA (verified 2026-07-12).**
Under uWSGI, module-load-time prints from `game_bridge.py`, `app.py`, and the
rest of the web app go to **`server.log`**, regardless of whether they use
`sys.stderr` or `sys.stdout`. Only the pre-uWSGI shim prints (from
`cage_dynasty_web/simulation/__init__.py` and
`cage_dynasty_web/systems/__init__.py`) reach `error.log` — those fire at
interpreter startup, before uWSGI has taken over the process's stderr. So:
- `[SIMULATION-SHIM]`, `[SYSTEMS-SHIM]` → `error.log`
- `[IMPORT-PATH-PROOF]`, `✅ ... loaded`, `⚠️ SECURITY WARNING`, everything
  else the app prints during module-load → `server.log`
- Runtime errors (unhandled exceptions during requests) → `error.log`

Files-API paths:
- `/var/log/vandopegaming.pythonanywhere.com.server.log`
- `/var/log/vandopegaming.pythonanywhere.com.error.log`
- `/var/log/vandopegaming.pythonanywhere.com.access.log`

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
- Top-level `cage_dynasty/narrative/` — reached because wsgi.py adds
  `/home/vandopegaming/cage_dynasty/narrative` to sys.path, so bare
  `import commentary` / `import rivalry` / `import media` in the web tree
  find the `.py` files inside it directly. (Repo root itself is NOT on
  sys.path — see the CRITICAL block at the top.)
- `cage_dynasty_web/simulation/` — real shim package (`__init__.py`
  registers bare `fight_engine` into `sys.modules` under the
  `simulation.fight_engine` name so `from simulation.fight_engine import
  ...` resolves to the web engine). Was a broken symlink at one point;
  became a real dir with PREGEN-FULL-ENGINE-FIX1.
- `cage_dynasty_web/narrative` — **still a broken symlink** to
  `../cage_dynasty/narrative` (the relative target resolves to
  `cage_dynasty/cage_dynasty/narrative`, which doesn't exist). Confirmed
  inert on PA 2026-07-12 via Files API. Every web-tree consumer of
  `narrative.X` (rivalry, media, commentary) is inside a
  `try/except ImportError` block that falls back to the BARE-name import
  which resolves via wsgi.py's `narrative_path` on sys.path. If anyone
  writes `from narrative.X import Y` WITHOUT a try/except, they get
  ImportError on PA and hit the exact silent-failure trap the
  coin-flip fallback + injury-system-dark bugs came from. Ship 1
  (post-arc `git rm`) sweeps this dead symlink.

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
- One broken symlink remains at `cage_dynasty_web/narrative` — inert on
  PA (Files API confirms) and every consumer is guarded by
  `try/except ImportError`. See the architecture note above. The
  companion `cage_dynasty_web/simulation` is NO LONGER a symlink — it's
  a real shim package now.
- Flat-first import loop: `from foo import x` finds `cage_dynasty_web/foo.py`
  before `cage_dynasty_web/foo/__init__.py`, before top-level. Adding a flat
  file with a name that collides with a package shadows the package.
- `types.py` shadows stdlib `types`. Use built-in `dict`, `list`, `set` —
  never `Dict`, `List`, `Set` type hints.
- WebFighter dataclass crashed once because fields with defaults were placed
  before fields without. Always read the whole class before adding fields.
- **Root `fight_engine.py` on PA has 11 manually-appended constants —
  CONFIRMED REAL 2026-07-12 (not the myth it was suspected of being).**
  Full-tree hash compare of every one of the 227 tracked files, PA vs repo:
  225 byte-match, 1 diff. The diff is root `/home/vandopegaming/cage_dynasty/fight_engine.py`
  — PA is 133782 bytes, repo is 133480 (Δ +302). PA carries 11 lines
  appended after the last function that git doesn't know about:
  ```
  DAMAGE_MULTIPLIER = 0.42
  # Web app compatibility constants
  FLASH_KO_DAMAGE_THRESHOLD = 25.0
  FLASH_KO_BASE_CHANCE = 0.05
  FLASH_KO_MAX_CHANCE = 0.25
  TKO_GNP_HEALTH_THRESHOLD = 30.0
  TKO_GNP_BASE_CHANCE = 0.08
  TKO_GNP_MAX_CHANCE = 0.35
  TKO_STANDING_HEALTH_THRESHOLD = 25.0
  TKO_STANDING_BASE_CHANCE = 0.06
  ```
  **Provenance** (Van, 2026-07-12): fossil of the pre-`sys.path`-hack
  ImportError fix era. Before wsgi.py explicitly excluded repo root
  from `sys.path` and before `game_bridge`'s force-delete-then-reimport
  block landed, bare `import fight_engine` sometimes resolved to root
  `/cage_dynasty/fight_engine.py`. That file didn't have the FLASH_KO /
  TKO_GNP / TKO_STANDING constants FI needed, so `from fight_engine
  import (...)` raised ImportError, `FIGHT_ENGINE_AVAILABLE` fell to
  False, and pre-gen quietly ran on the score-based coin-flip fallback —
  the two-month bug PREGEN-FULL-ENGINE-FIX1 (`e6e295e`, 2026-07-11;
  previously cited `efaf7f6` (which is GAMEPLAN-AI-SELECT1) in error)
  finally closed. Someone (probably Van, in a firefight) diagnosed the
  ImportError correctly but fixed it at the wrong end: hand-appended
  the missing constants to root fight_engine.py on the live box instead
  of fixing which file got imported. The proper fix — the `sys.path`
  insert + force-delete in `game_bridge.py:190-199` — came later and
  made this workaround inert. But the appended lines never got cleaned
  up, and they've sat on PA in a modified-but-tracked state ever since.
  **Values are meaningfully different from what live-play uses today.**
  Root-PA's `TKO_GNP_HEALTH_THRESHOLD = 30.0` vs live web's `18.0`
  post-GROUND-STOPPAGE-FIX1. Root-PA's `FLASH_KO_DAMAGE_THRESHOLD =
  25.0` vs live web's `70.0`. If any code path ever accidentally
  resolves `import fight_engine` to root, these old constants silently
  override the tuned live values and produce different fight outcomes.
  **NOT affecting live behavior today** — IMPORT-PATH-PROOF (`db15e3a`,
  2026-07-12) directly measures `fight_engine.__file__` in the running
  app; it names `/home/vandopegaming/cage_dynasty/cage_dynasty_web/fight_engine.py`,
  not root. That guard is now the standing regression test for this
  specific ghost.
  **Why `git pull` has silently tolerated this for months (the
  deploy-breaker warning):** `git pull` only refuses to overwrite a
  locally-modified tracked file when the incoming merge would touch
  that file. Root `fight_engine.py` hasn't been modified in the repo
  since commit `56bf807` (2026-04-27, initial commit) — nothing to
  overwrite, nothing to complain about. Every deploy has been
  fast-forwarding around it happily. **The trap springs the instant
  that file changes upstream.** Ship 1 (the `git rm` of the three
  orphaned CLI-era fight_engine.py copies, filed for post-arc) IS
  exactly that upstream change. Before shipping it, reconcile PA's
  dirty root copy first — restore it to repo state via console `git
  checkout HEAD -- fight_engine.py` on PA — or the pull will error
  mid-deploy and require manual intervention on a live box.
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

## Fossils — comments that outlived the code they describe

Historical preservation of documentation that was measurably wrong at
the moment it was deleted. Kept here to remind future readers that
comment blocks age worse than code — the code gets tuned, the comment
does not — and to make the shape of that decay visible.

### `FI_DAMAGE_MULTIPLIER` justification block (deleted 2026-07-12 by Stage 0d)

Sat above `fight_integration.py:83` for ~8 weeks. Verbatim:

```
# fight_integration runs a longer commentary exchange loop than fight_engine.simulate_fight
# so the effective damage per fight is higher — this multiplier is tuned separately
# to produce realistic finish rates (50-55% target) for the narrated fight path.
# Ship A two-iteration tune (2026-05-09):
#   0.32 (Saturday play: 11% finish rate, broken)
#   → 0.38 (Tier 2 verified: 70% across DFC 16-18, over-corrected)
#   → 0.36 (final, lands in 50-55% target)
# Synthetic-vs-production gap: synthetic n=300 batches predicted finish rates
# ~20-30 points below production reality at the same multiplier. Production
# may have damage-amplifying factors (gameplan, condition, fighter attrs from
# real game_state) that the random-Gaussian synthetic doesn't capture. Future
# tuning should weight production observations over synthetic.
FI_DAMAGE_MULTIPLIER = 0.48
```

**Two things were false at the time it was deleted, both load-bearing
for the arc that consumed it:**

1. **The value it justifies is not the value in the code.** Comment
   documents an "Ship A two-iteration tune" landing at `0.36`. The
   code below it says `0.48`. The delta was tuned later by `d666e24`
   (2026-06-15, "Tune: raise FI_DAMAGE_MULTIPLIER — restore finish
   rates after stamina tuning") and the justification block was never
   updated. For eight weeks the file read as if 0.36 were the tuned
   answer.

2. **The premise it argues from was measured false.** *"runs a
   longer commentary exchange loop than fight_engine.simulate_fight"*
   was the entire justification for a separate multiplier. Stage 0b
   check C2 measured both engines at exactly 55 exchanges per round
   × 3 rounds = 165 total. Same loop length. The 0.48-vs-0.42 gap
   was naked drift, not compensation for a real loop-length
   difference — measured at `outputs/two_engine_0b_close.md` §C2.

**Why it survived**: nobody looked at it as the tuning arc landed the
next value. Comment blocks describing "why we tuned to X" become
invisible the moment the code says Y — they read as historical
context, and historical context doesn't get audited during a tune.

**Lesson for future comments justifying constants**: if the number in
the code moves, the comment moves with it or the comment gets
deleted. A justification block that outlives its value is not a
docstring, it's a fossil.

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
notes asserted that PREGEN-FULL-ENGINE-FIX1 (`e6e295e`, 2026-07-11;
previously cited `efaf7f6` (which is GAMEPLAN-AI-SELECT1) in error)
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

**⚠️ CORRECTION 2026-07-14 — STAGE 1 OUTCOME MATRIX (10-seed pooled,
N=782 per side, uuid-patched deterministic worlds).** The three
FINISH-DISTRIBUTION-DIAG1 numbers above **predate the uuid finding**
(DOCS-SEED-NONDETERMINISM1, 2026-07-13) and were measured on
unreproducible worlds — every "same seed" was actually a differently-
shuffled fighter population. Re-measured this arc's headlines on
matched fighters, matched seeds:

| Headline claim | STAGE 1 measurement (pooled 10 seeds) | Verdict |
|---|---|---|
| striker-v-striker 26% pre-gen / 98% live-play | **42.2% pre-gen / 81.0% live-play** (N=147) — Δ +38.8pp | **FALSE**. Real gap, magnitude exaggerated. |
| within-TKO cut share pre-gen 68-100% vs live-play 0% | live-play 0% CONFIRMED (grep verified: `ENGINE-DEAD-KNOBS1` comment at `fight_integration.py:~1770` says cut-stoppage branch was unreachable and was REMOVED — live-play has **no cut mechanism at all**). Pre-gen cut share not re-measured (needs specialty_method break-out per-seed; queued). | **PARTIAL** — live side confirmed structurally. Pre-gen number not re-verified but base claim (asymmetry) survives. |
| 82% of pre-gen TKOs are doctor stoppages (referenced elsewhere in arc scoping) | Denominator error on original: **6 total TKOs in seed=42 N=78** made the 82% meaningless. Pooled 10-seed pre-gen has TKO_DOCTOR+TKO_DOCTOR_CUT = 8.7% of all fights, TKO_STRIKES = 3.5% — but the two engines' doctor stoppages are apples-to-oranges (see above). | **FALSE as scoping input**. |
| 2% submissions | live-play 3.7% pool / pre-gen 5.8% pool. Single-seed detail: 2.4% live / 3.0% pre-gen. Sub attempts 4-8× conversions. | **CONFIRMED direction**. |

**What survives and matters:**

- **Aggregate live vs pre-gen finish rate: 76.9% vs 35.4% pooled (Δ +41.4pp on N=782 per side).** The arc's core divergence is real and larger in aggregate than the individual headline cells suggested.
- **The largest per-method divergence is TKO-strikes**: live 26.1% vs pre-gen 3.5% (Δ +22.6pp pool). Pre-gen essentially never produces a strike TKO. This is the specific mechanic gap the consolidation arc has to close.
- **The same-family-vs-cross-family asymmetry hypothesis is DISPROVED across worlds**: seed=42 showed SxS/GxG ~50pp vs SxG ~19pp, but pooled 10-seed shows SxS +38.8pp / GxG +41.2pp / SxG +43.9pp — nearly uniform ~40pp across matchup types. The seed=42 pattern was a single-world artifact.
- **Every specific number in the arc's scoping is now suspect** because they predate the uuid finding. Direction survives; magnitudes need re-measurement against the ORACLE-BRIDGE1 fixture and pooled multi-seed.

Full multi-seed data: `outputs/oracle_bridge/stage1_multiseed_result.txt`. Per-seed
matrix from `outputs/oracle_bridge/stage1_multiseed_matrix.py`.
Single-seed matrix from `outputs/oracle_bridge/stage1_outcome_matrix.py`.

**Rule going forward: no arc scoping number gets quoted without an
N and a seed count.** Direction claims fine; exact percentages need
provenance.

### STAGE 1 addendum — random-coupling hazard (STAGE1-PARITY1, 2026-07-14)

The follow-up first-divergence and parity traces produced a finding
that changes how Stage 2a has to think about byte-equivalence.

**Random-consumption divergence between FE and FI is bigger than one
line.** `fight_integration.py:494` (`self.commentary.rng.seed(random.
getrandbits(64))`) was the obvious candidate: FI burns one main-random
draw at fight-init that FE does not. The comment above :494 says
"advances by exactly 1 per fight, always, so commentary-on vs
commentary-off produce byte-identical fight outcomes under the same
top-level seed." That comment is **correct within FI** — it does not
address FE-vs-FI compatibility, and reading it as covering the full
coupling story would be a mistake.

**Measured coupling as of 2026-07-14 [grep + measurement]:**
- `:494` — `random.getrandbits(64)` for commentary rng seed (1 draw)
- `:640` — `random.randint(-10, 10)` for fighter1 initiative
- `:641` — `random.randint(-10, 10)` for fighter2 initiative
- **At least three lines**, probably more. Alignment attempts (+1 draw,
  +3 draw) both failed to align the primitive-call traces on 12/12
  DEC-vs-DEC fights. Two of those fights show a **different fighter
  selected first** — same seed, not just different action — which is
  either structural (initial-actor logic differs) or evidence of
  additional random-consumption divergence beyond the three grep-named
  sites.

**The offset-vs-mechanic decomposition of the 41pp gap is NOT
obtainable before Stage 2a.** No amount of harness alignment can
match the two engines' random-consumption orders while they remain
two engines. **Only the structural relocation — one loop, one RNG-
consumption order, by construction — makes the decomposition question
answerable.** Do not scope Stage 2a's success criteria against any
"residual after alignment" number; those numbers are all measured
under alignment attempts that don't align.

**What Stage 2a MUST resolve alongside the accumulator port:**
1. Consolidate the RNG-consumption order. FI's :494/:640/:641 (and
   whatever else surfaces during the port) become one deterministic
   sequence when the loops merge, or byte-equivalence with pre-gen
   remains structurally impossible even after every mechanic ports
   cleanly.
2. Reconcile the initial-actor selection. Whether it's random-order
   coincidence or a real logic difference between engines needs to
   be answered when the code is in one place.

**What survives regardless of alignment attempt [measurement, offset-
invariant across N=0/+1/+3 draws]:**
- **TKO-strikes gap holds at 22-27pp.** Real mechanic, not phase noise.

  **⚠️ PREVIOUSLY STATED: four FI-only accumulator paths at
  `fight_integration.py:974/1016/1033/1052` are the confirmed source
  and FE has no equivalent — FALSE.** Corrected 2026-07-14 by the
  Stage 2a read-only diagnostic. Actual code-level split of those four
  gates (grep-verified against HEAD, both files):

  | gate | FI location | FE equivalent | FE numerical relation |
  |---|---|---|---|
  | `_clinch_body_acc` | `:958-980` | **none** (0 refs in fight_engine.py) | genuinely FI-only |
  | `_gnp_accumulation` | `:1005-1022` | **none** (0 refs in fight_engine.py) | genuinely FI-only |
  | leg-TKO on `leg_kicks_absorbed` | `:1024-1037` | `fight_engine.py:3303-3323` | **byte-identical** logic — field is FE-native at `:474`; both blocks share `min(0.15, (absorbed - 6) * 0.02)` + `*1.4` if stamina<50 |
  | rocked-shots ref stoppage | `_rocked_shots` at `:1042-1055`, cap `min(0.22, N*0.05)`, mult `1 - iq/250 - heart/350 - composure/400` | `_rocked_shots_taken` at `fight_engine.py:3406-3413`, cap `min(0.35, N*0.08)`, mult `1 - iq/250 - heart/350` | **FE gate is STRONGER** on every axis: faster increment (0.08 vs 0.05), higher cap (0.35 vs 0.22), no composure protection |

  **Two are genuinely FI-only. One is FE-native and byte-identical.
  One is present in FE with different, stronger constants.**

  **Counterintuitive consequence flagged explicitly:** FE's rocked-
  shots gate, *if it fires*, is stronger than FI's — cap 0.35 vs
  0.22, faster ramp, no composure discount. It therefore cannot be
  a source of FE's finish-rate deficit relative to FI. Leg-TKO being
  byte-identical explains none of the gap either. **The code-level
  attribution of the TKO-strikes gap narrows to `_clinch_body_acc`
  and `_gnp_accumulation` — pending a firing measurement.** Do NOT
  read this as "clinch-body + gnp are the confirmed cause": whether
  FE's leg-TKO and rocked-shots gates actually fire in pre-gen (or
  are present-but-dormant) is unmeasured. Firing frequency is what
  closes the attribution; a code presence check does not.

  **Named trace item** (queued, requires the two-step allowlist
  widening at `fight_engine.py:863`'s `_assert_sanctioned_config`):
  do FE's `leg-TKO` and `_rocked_shots_taken` ref-stoppage gates
  actually fire in pre-gen production, or are they dormant paths that
  never trigger on the fighter/damage distributions world_init
  produces? Answering this is what would confirm or deny the narrowed
  attribution above.
- **Style windows FE lacks** (`_counter_window` at
  `fight_integration.py:787-937`, `_movement_window` nearby) — flagged
  but not individually quantified. Port scope includes these.

**Do NOT run a deeper draw-by-draw coupling audit.** That's the rabbit
hole — match three consumers, find a fourth, match four, find a fifth.
The port itself resolves the coupling by unification. Filing the
sizing here so the next diagnostic doesn't try to enumerate its way to
byte-equivalence from outside.

Full record: commits `c208041` (first-divergence trace + heat probe)
and STAGE1-PARITY1 (parity trace). Data: `outputs/oracle_bridge/
first_divergence_trace.py`, `random_parity_trace.py`,
`heat_magnitude_probe.py`.

### STAGE 1 addendum — config-lever measurement [filed 2026-07-14]

The two config dials that differ between pre-gen and live-play
(`damage_multiplier` 0.42 vs 0.48, `standup_threshold` 6 vs 10) close
**53% of the known finish-rate gap by themselves.** This measurement
narrows the STAGE 1 addendum above — it does not falsify it. The
mechanics it named (TKO-strikes gap, two genuinely-FI-only accumulators,
style windows FE lacks) are still real. They are a smaller share of the
41.4pp aggregate than the framing implies, and the surviving residual
after both dials is a mix with no further pre-port lever available to
narrow it (see (e) — the increment-rate candidate proved structural).

**Measurement — ORACLE-BRIDGE1 fixture, 78 matched fighter pairs, matched
seeds (1000 + fight_index):**

| config | triple | finish rate |
|---|---|---:|
| baseline (pre-gen) | (55, 0.42, 6) `_TRIPLE_PRE_GEN_LEGACY` | 37.2% |
| damage-only matched | (55, 0.48, 6) `_TRIPLE_FI_FALLBACK` | 57.7% |
| standup-only matched | (55, 0.42, 10) **widened in-memory, reverted post-run** | 46.2% |
| both dials matched (LIVE_PLAY) | (55, 0.48, 10) `_TRIPLE_LIVE_PLAY` | 59.0% |

- **Baseline → LIVE_PLAY = +21.8pp of finish rate.** Against the Stage 1
  pooled 10-seed gap of **+41.4pp** (live 76.9% vs pre-gen 35.4%), this
  is **53% of the arc's known aggregate gap, config drift alone.**

**Interaction term, as measured fact:**

- Damage-alone closed **+20.5pp** (37.2% → 57.7%).
- Standup-alone Ledger A (finish-rate only) closed **+9.0pp** (37.2%
  → 46.2%).
- **Additive estimate: +29.5pp.** Measured combined: **+21.8pp.**
- **Interaction term: −7.7pp.** The two dials interact negatively —
  they overlap rather than add. Additive estimate overstates the
  two-dial closure by ~35%. This is why the combined triple was
  measured directly rather than estimated from single-lever runs.

**Standup caveat — carried from the filed mechanism finding:** the
standup contribution above is Ledger A only (net finish-rate movement),
per `### standup_threshold observed effect is not referee-standup
frequency [filed 2026-07-14]`. The Phase 1 discrimination probe surfaced
24 winner-flip / method-change-within-class fights that the standup dial
also moves — this churn is real observed behavior but does NOT count
toward gap closure and is explicitly excluded from the +9.0pp above. Do
not sum Ledger A and Ledger B when quoting standup's effect.

**Surviving residual — unseparated mix, NOT "the size of the surgery":**

- **+19.6pp** survives after both dials are matched (41.4pp known aggregate
  − 21.8pp measured combined).
- **This residual is a mix** of at least: (a) the two genuinely-FI-only
  accumulators `_clinch_body_acc` (`fight_integration.py:958-980`) and
  `_gnp_accumulation` (`:1005-1022`); (b) style windows FE lacks
  (`_counter_window`, `_movement_window`, `_surge_exchanges`); (c)
  input-distribution differences between `world_init` and the Path A
  fixture population, which no engine change resolves; (d) the
  rocked-shots numerical difference (FE cap 0.35 vs FI cap 0.22, per the
  STAGE 1 addendum table); (e) **the divergent standup-gate counter —
  a STRUCTURAL difference (the initial finding's "config lever"
  classification was wrong): FE counts consecutive
  ground exchanges (uniform +1, no activity check) at
  `fight_engine.py:3693-3702`; FI counts exchanges since last meaningful
  ground action (reset-on-activity, +0.25 dominant / +2 non-dominant
  otherwise) at `fight_integration.py:1691-1739`. Two different
  measurements feeding the same threshold, not a rate that can be
  matched. Adopting FI's rule requires an activity signal FE does not
  compute — multi-site signal wiring at ~5 mechanics FE has but does
  not instrument (FI's set-sites at :685/:689/:748/:1181/:1320/:1430/
  :1454). That is Stage 2a port surface, not a pre-port config override.
  Verdict from the increment-rate scoping pass (read-only, session
  2026-07-14): entangled with the mechanic port, resolvable only by
  unification. The residual contribution is real; the classification
  as a "possibly-cheap lever" was wrong.**
- **The +19.6pp residual is the Stage 2a-relevant target with no
  further pre-port narrowing available.** The scoping pass on (e)
  proved no separable pre-port lever exists at this vein — the
  increment-rate difference is structural and part of the port surface,
  not a config match that could be measured first. Do not read +19.6pp
  as the size of Stage 2a's port either: it is a MIX (components a-e
  above), and (c) input-distribution differences cannot be resolved by
  any engine change. The bound holds; further-narrowing before the
  port does not.

**Framing correction — proportion, not falsification.** The arc has
been scoping the full ~41pp as substantially a mechanics problem.
Measured, **~53% was config drift** (two dials that were already sanctioned
in `_SANCTIONED_TRIPLES` at `fight_engine.py:853-860`, differing only in
which triple each engine happens to construct). The increment-rate candidate
initially treated as an additional pre-port lever proved structural on
scoping (see (e)), so no further pre-port lever narrows the residual before
Stage 2a. The mechanics the STAGE 1 addendum
named — the TKO-strikes gap, the two FI-only accumulators, the style
windows — are still real contributors to the residual. Their share of
the 41.4pp aggregate is smaller than the earlier framing implied, not
zero.

**Data provenance:** two untracked probe scripts in `outputs/oracle_
bridge/`:
- `damage_lever_probe.py` — 37.2% → 57.7% at damage 0.42→0.48, standup
  held at 6, both triples sanctioned, no widening.
- `standup_lever_probe_phase2.py` — three configs at (55,0.42,6),
  (55,0.42,10), (55,0.48,10). Middle triple required in-memory widening
  of `_SANCTIONED_TRIPLES`; widening was reverted post-run and
  fight_engine.py bytes verified unchanged. Stage 0c golden master
  (928/928) and ORACLE-BRIDGE1 harness (78/78) both re-checked GREEN
  after revert.

The finding stands on the committed numbers in the table and interaction
paragraph above. The probe scripts are named for reproducibility, not
because they are the record. Untracked status is intentional — these are
one-shot measurement instruments, not fixtures.

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

All numbers below are at symmetric OVR=75, 3-round non-title, gameplan=None
(neutral). Harness config passes `damage_multiplier=0.24`
(documented-was-misleading: per this file's KEY CONSTANTS,
`fight_integration` ignores config damage and uses
`FI_DAMAGE_MULTIPLIER=0.48`; numbers below at effective 0.48, not 0.24).
Probe harnesses were
committed inline in the referenced diag memos.

### Wr-BJJ (Wrestler vs BJJ Specialist)

- **Wrestler win rate ~48%** (Harness A 47.3% CI [43.3, 51.4] N=577;
  reproduces 47-49% across 3 harness shapes — see
  `outputs/wr_bjj_drift_diag1.md`).
- **BJJ submission path intact ~16.5%** (99/600 subs, all landed by
  the BJJ side).
- Verified byte-identical across the 8e3f670→efaf7f6 boundary by
  WR-BJJ-DRIFT-DIAG1 (2026-07-07) — the "this is the correct stable
  baseline, **not a regression**" framing was documented-was-overreach.
  Certifies the LIVE-PLAY path only, across GAMEPLAN-AI-SELECT1; does
  NOT cover the pre-gen engine (PREGEN-FULL-ENGINE-FIX1, `e6e295e`) —
  see coverage gap subsection below.
- **RETIRED**: the "60.2% CI [56.2, 64.0] N=600" figure never existed
  in any committed artifact — a mis-reference, likely conflated with
  Wr-Str's 60-70% band that GNP-BUFF certified. Do not treat 60.2%
  as a prior baseline in any future work.
- **48% is a design point, not a bug**: BJJ's off-back sub path has
  no symmetric wrestler answer at OVR=75-vs-OVR=75. Moving wrestler%
  upward here is a deliberate new tuning decision, not a
  restoration.

### Wr-BJJ — pre-gen coverage gap

The pre-gen coverage gap is REASONED from a proven-empty transitive import
graph, NOT measured by running fights across the e6e295e~1 → e6e295e
boundary. **No fight was run.** The measurement was scoped in the
reconciliation thread and then dropped because the import graph proved the
harness structurally cannot observe the pre-gen path — running fights would
have produced a null-by-construction diff, and reading that null as
"baseline survives" would have been false reassurance (the golden-master
coverage-gap pattern this file's own CRITICAL block at "GOLDEN MASTER IS A
FIGHT-ENGINE ORACLE" already warns against).

Reasoning voice, not measurement voice, is the honest attribution.

**Consequence:** the certified Wr-BJJ numbers above measure LIVE-PLAY only.
The pre-gen engine (PREGEN-FULL-ENGINE-FIX1, `e6e295e`) writes rival records
during world_init history simulation and is not covered by any certified
number in this section. No pre-gen Wr-BJJ baseline currently exists.

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
