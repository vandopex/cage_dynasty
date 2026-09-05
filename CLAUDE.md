> ARCHIVE SPLIT (2026-08-15, ARCHIVE-SPLIT commit). Closed-arc
> narratives, superseded measurement logs, and pure-provenance content
> live in `CLAUDE_archive.md` at repo root. This file (CLAUDE.md) holds
> only load-bearing rules and open work. Future sessions: MOVE, don't
> delete — if a section here becomes closed, relocate it byte-identical
> to the archive with a pointer here ONLY if something live references
> it by name. No merging, no rewording. If unsure whether to move:
> leave it here and flag it. Existing `## Archive` section at end of
> this file (older pre-existing scope) is unchanged.

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

**Fixture `repo_sha` records "generation-time HEAD", not "write-commit".**
The generator's `_repo_sha()` (`generator.py:415-417`) stamps
`git rev-parse HEAD` at generation — a different question from which
commit contains the fixture in git. For this fixture: `repo_sha` =
`6fdc341` (HEAD when generator ran); write-commit = `a475a82` (child
of `6fdc341`, adding the fixture and generator's synth-cell edits
together). Both true, different questions; the recorded value is not
a stale mistake to correct — it's accurate under the field's design.
Secondary limit: `git rev-parse HEAD` captures committed HEAD, not
working-tree, so a fixture generated from a dirty tree can't be fully
identified by `repo_sha` alone. Filed so a future session doesn't
re-investigate.

[STRIKE-AND-PRESERVE, 2026-08-15 post-`68dbd52` — see
`### STYLE-DEAD1 [MEASURED, bytes at HEAD 68dbd52]` in the Key
constants section below. The "production live-play is style-aware"
framing is MEASURED-FALSE at the OUTCOME layer: `_STYLE_STR_MAP`
in `game_bridge.py` emits enum NAMES; the `_FightingStyleEnum(...)`
construction two lines below is VALUE lookup; ValueError swallowed
by `except Exception: pass` → `style_mod = 0.0` every fight since
the map was written. The `fighting_style` enum IS populated on
`FighterAttributes` at construction (that part of the block below
remains correct), but the branch that would make style
outcome-affecting has never fired in production. Retroactive
re-reading also owed for any upset-probe / outcome-attribution
memo under `outputs/odds_*` that inherited this framing. Text
preserved for provenance; corrected reading is under the
STYLE-DEAD1 section.]

**Fixture is style-blind; production live-play is style-aware. Third
coverage limit on the 928/928 gate.**
Bytes-confirmed at HEAD `1f98b5f`, both bridges + both fixture replay
paths. Pre-gen's `world_init._fighter_to_attributes` constructs
`FighterAttributes` **without** the `fighting_style` kwarg → the enum
defaults to `None`. Live-play's `game_bridge._make_fighter_attrs`
constructs **with** `fighting_style = FightingStyle[_STYLE_MAP.get(...)]`
→ enum populated. Fixture's serialize path `fighter_attrs_to_dict` at
`outputs/stage0c_golden_master/generator.py` explicitly excludes
`fighting_style` (`if f.name != "fighting_style"`). Fixture's rehydrate
path `dict_to_fighter_attrs` at both `checker.py` and `generator.py`
is byte-identical: `return fe.FighterAttributes(**d, fighting_style=None)`.
So `expected_fe` faithfully mirrors production pre-gen (both style-blind),
but `expected_fi` diverges from production live-play (fixture blind,
production aware). FI's style-gated branches (7 clusters, grep-locatable
via the single-line fragment `.fighting_style, 'name', ''` in
`fight_integration.py` — the getattr call is broken across two lines so
the fuller pattern doesn't resolve as a one-line grep) fire the else
path in the fixture and enum paths in production. Consequence for the
arc: **928/928 certifies engine equivalence under style-blind conditions
only.** Whether a merged engine post-Stage-2a preserves live-play
behavior is not answerable from the fixture — the style-aware condition
production actually runs was never sampled. Same "coverage limit, not
coverage bug" framing as the two paragraphs above: FE-side is faithful,
FI-side is a distinct gap. Third limit alongside fixture-inputs and
fixture-modules; all three apply. Do not conflate.

Corollary, filed so a future v2-fixture audit doesn't re-scope it:
three FI style branches keyed on `'BRAWLER'` / `'SAMBO'` / `'JUDO'`
substrings in `fight_integration.py` are structurally unreachable in
production. `_STYLE_MAP` in `game_bridge.py` normalizes those strings to
`PRESSURE_FIGHTER` / `WRESTLER` / `WRESTLER` before enum construction,
and neither `FightingStyle` (11 members in `core/types.py`, none named
BRAWLER/SAMBO/JUDO) nor `world_init` generation ever emits them. Dead
in production under any fixture design.

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
  **[STRIKE-AND-PRESERVE, 2026-08-15 post-`68dbd52` — the "VERIFIED match
  ... 479 bytes" and "Byte-equivalent to repo's `cage_dynasty_web/wsgi.py`
  modulo comments" claims are FALSE-AS-WRITTEN AT HEAD. PA `wsgi.py`
  measured 610 bytes this pass (+131 vs the recorded 479). See
  `### wsgi-610 [MEASURED, filed 2026-08-15]` in the Key constants section
  below. The sys.path insertion order and bare-import resolution behavior
  paragraph remains UNCHANGED-IN-EFFECT (verified independently across
  narrative/commentary + systems/fotn resolutions this pass). Text
  preserved for provenance; the byte-equivalence claim is retired, the
  behavior claim survives.]
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

Recurring lesson: data integrity is necessary but not sufficient —
each rendering surface and persistence layer needs intentional
reading. **When a system iterates a dict, audit every code path
that writes to that dict.**

Full section archived: CLAUDE_archive.md → '## Recurring architectural pattern: "data exists but doesn't reach the surface"' (phase 2, 2026-08-15)

## Fossils — comments that outlived the code they describe

**Lesson for future comments justifying constants**: if the number
in the code moves, the comment moves with it or the comment gets
deleted. A justification block that outlives its value is not a
docstring, it's a fossil.

Full section archived: CLAUDE_archive.md → '## Fossils — comments that outlived the code they describe' (phase 2, 2026-08-15)

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

**Truth at HEAD** [MEASURED, sourced to STAGE 0d `ba8cece`, 2026-07-12; verbatim from the archived correction-layer narrative]**:** live-play per-strike damage scale is
`self.config.damage_multiplier`, read live in the strike-damage path
(currently `fight_integration.py:867`). The `FightConfig.damage_multiplier`
dataclass field defaults to `0.48` (currently `fight_engine.py:798`).
The value the config carries is pinned by the atomic-config-invariant
contract via `_SANCTIONED_TRIPLES` (currently `fight_engine.py:853–859`)
to one of `{0.42, 0.48}`. `_TRIPLE_LIVE_PLAY = (55, 0.48, 10)` is
annotated as "the surviving contract" in the `_SANCTIONED_TRIPLES` set
(currently `fight_engine.py:857`). The 0.48 value survives 0d by design
— the read site's own comment (currently `fight_integration.py:866`)
states "Byte-identical to the pre-0d FI_DAMAGE_MULTIPLIER=0.48." Every
line reference above is tagged "currently" because line numbers drift;
the identity of each fact is its symbol (`config.damage_multiplier`,
`FI_DAMAGE_MULTIPLIER`, `_SANCTIONED_TRIPLES`, `_assert_sanctioned_config`,
`_TRIPLE_LIVE_PLAY`, `FightConfig.damage_multiplier`).

**Other current constants** [⚠️ HOIST — these three bullets are HOISTED from the tail of `### STAGE 1 addendum — config-lever measurement [filed 2026-07-14]` where they lived in the pre-phase-2 bytes at L1657-1659. Semantic home is here, not there. This is a location move, not a content edit; the three bullets are verbatim]:
- Submission threshold: 70.0
- Rankings: `MAX_MOVE = 3`, `NEW_ENTRY_CAP = 8`
- Contract: `HOLDOUT = 25`, `WALKOUT = 10`, `HOLDOUT_WINDOW = 4 weeks`

**Rule going forward: no arc scoping number gets quoted without an
N and a seed count.** Direction claims fine; exact percentages need
provenance.

Full section archived: CLAUDE_archive.md → '## Key constants (don't change without telling me)' (phase 2, 2026-08-15)

> **[ARCHIVED C28 2026-09-05 — moved verbatim to `claude/claude_md_archive_2026a.md`]**
>
> Five sections lived here (pre-arc addenda, closed history):
> - `### STAGE 1 addendum — random-coupling hazard (STAGE1-PARITY1, 2026-07-14)`
> - `### STAGE 1 addendum — config-lever measurement [filed 2026-07-14]`
> - `### STAGE 2a addendum — config vs engine, measured 2x2 [filed 2026-07-26]`
> - `### STAGE 2a addendum — production-path measurement of the classmethod flip [filed 2026-08-01]`
> - `### Framing correction — "the aggregate gap" is population-specific [filed 2026-08-01]`

### Measurement hazard — runtime-rebind sweeps vs source literals [filed 2026-08-14, AMP-RECONCILIATION arc, dec968b]

**Rule.** Runtime-rebind sweeps cannot reach source literals. Pre-gen world construction consumes `fight_engine.py`'s dominance amp site at `:3293` (measured `simulate_exchange` call count during `world_init` pool build = **231,601** at 120-week history; the amp fires on the dominant-GnP position subset). Any swept constant must have EVERY consumer site — including world build — bound to the swept knob, or the sweep measures fights in a stale world.

**Five-world measurement table** (all FI leg, N=400, seed=1000; artifacts referenced by name, untracked in `outputs/`):

| environment | line 459 (constant) | line 3293 during pre-gen | GNP const at FI fight-time | pool | FI finish% | FI SUB | FI DOM_TOP N | FI R1 hp |
|---|---|---|---|---:|---:|---:|---:|---:|
| verify (source edit) | 1.25 | 1.25 (hoisted) | 1.25 | 297 | 54.25% | 13 | 28373/54864 | 51.45 |
| literal-3293 (this probe) | 1.6 base | 1.25 (probe literal) | 1.25 (runtime rebind) | 297 | 54.25% | 13 | 28373/54864 | 51.45 |
| rebind_only | 1.6 base | 1.35 (base literal) | 1.25 (runtime rebind) | 298 | 55.50% | 6 | 28633/55429 | 49.84 |
| rebind_early | 1.6 base | 1.35 (base literal) | 1.25 (rebind pre-build) | 298 | 55.50% | 6 | 28633/55429 | 49.84 |
| sweep AMP=1.25 (fe_pat) | 1.6 base | 1.35 (base literal; FI uses fe_mod) | 1.25 (runtime rebind) | 298 | 55.50% | 6 | 28633/55429 | 49.84 |

The lever is column `line 3293 during pre-gen`. Every other column is constant across the four "stuck" rows. Pool size flips 297↔298 alongside outcome — one fighter's world-life differs when pre-gen fires 1.25 vs 1.35.

**Discriminating chain (six links, in order — each link denies a distinct hypothesis with a distinct artifact):**

1. **uuid-drift as a floor beneath measurement — DENIED.** Control run (verify harness against unedited production source, no source edit, no fe_pat, no rebind: `outputs/amp_verify_control_out.txt`) byte-matched the sweep BASELINE arm (FI 72.00% / FE 41.00%, both method mixes exact). No drift floor exists to hide cross-arm differences behind — running the same code in different processes produces byte-identical results.

2. **from-import of the constant `GNP_DOMINANT_DAMAGE_MULT` capturing a stale binding at pre-fe_pat load — DENIED** (`outputs/amp_consumers.txt`, `outputs/amp_consumers_full.txt`: 3 hits with the hoist in place (1 definition at `:459` + 2 consumer sites at `:2420` and `:3293`) / 2 at base (`:3293` still a literal) — either way, zero outside `fight_engine.py`). No cross-module `from … import` exists that could capture a stale binding.

3. **Second knob at `:3293` on FI's live leg — DENIED** (`outputs/site_3293_census_out.txt`: FI `total_calls=0` for `fight_engine.simulate_exchange`; FI's narrated fight body never invokes the module-level function containing `:3293`). Scope-corrected in `### Site-3293 census — scope correction [filed 2026-08-14]`: the census answered the live-leg question correctly but did NOT answer the world-construction question — link 6 below is the one that did.

4. **fe_pat co-load as environmental perturbation — DENIED** (`outputs/rebind_only_out.txt` byte-matches sweep AMP=1.25 arm without fe_pat loaded in the process at all — same FI 55.50% / SUB=6 / mix / DOM_TOP N / R1 hp / pool 298).

5. **rebind timing (before vs after pool build) — DENIED** (`outputs/rebind_early_out.txt` byte-matches sweep AMP=1.25 arm even with rebind moved pre-build; the harness's counter on `fe_mod.simulate_exchange` proved **231,601** calls during pool build, so pre-gen fired extensively — but not on the rebound constant).

6. **`:3293` literal consumption during pre-gen world construction — PROVEN** (`outputs/literal3293_out.txt` byte-matches verify at 54.25% / SUB=13 / pool 297, with `line 459` unchanged at 1.6 and only the literal at `:3293` flipped 1.35→1.25 — every non-mechanism variable held identical to the rebind_only environment).

**Artifacts (untracked in `outputs/`):** `rebind_only_harness.py`, `rebind_only_out.txt`, `rebind_early_harness.py`, `rebind_early_out.txt`, `literal3293_harness.py`, `literal3293_out.txt`, and prior `amp_sweep_harness.py`, `amp_sweep_out.txt`, `amp_verify_harness.py`, `amp_verify_out.txt`, `amp_verify_control_out.txt`, `amp_consumers.txt`, `amp_consumers_full.txt`, `site_3293_census_harness.py`, `site_3293_census_out.txt`.

### Site-3293 census — scope correction [filed 2026-08-14, AMP-RECONCILIATION arc, dec968b]

**Original claim** (in-conversation reviewer reading of `outputs/site_3293_census_out.txt`):
> "FI `total_calls=0` → `fight_engine.py:3293` cannot affect FI's numbers."

**Struck as over-read. Correction below; original is preserved above per the wrong-numbers rule — false-as-generalized, not deleted.**

**Correction.** The measurement was correct: FI's live leg never executes `fight_engine.simulate_exchange`, so the amp at `:3293` never fires during FI-narrated fight bodies. The generalization was false. `:3293` fires extensively during pre-gen world construction (via `world_init.HistorySimulator` → `fight_engine.simulate_fight` → `simulate_exchange`; measured 231,601 total `simulate_exchange` calls per 120-week pool build), and the resulting fighter records / world composition are the inputs FI later fights on. `:3293` therefore *does* affect FI's numbers — through the world it built, not through FI's own exchange loop.

**Attribution.** The measurement is what it is; the over-read is the reviewer's, filed here as a scope correction rather than as an instrument flaw. Future census verdicts of the form "site X has zero calls from consumer Y" must be qualified: "at live-play time, on the measured code path"; the same site's world-construction consumption is a separate question requiring its own probe (see `### Measurement hazard — runtime-rebind sweeps vs source literals [filed 2026-08-14]`).

**Corollary hazard, general form.** Any constant defined in `fight_engine.py` is a pre-gen consumer by default until measured otherwise. Live-leg call counts do not answer the pre-gen consumption question.

### STAGE 2a addendum — amp placement + FE-defined/FI-consumed constants [filed 2026-08-14, AMP-RECONCILIATION arc, dec968b]

**Prior placement finding** (in-conversation, drafted during the arc). Same amp value ≠ same amp placement. FI applies the amp in-primitive via `calculate_strike_damage` when `is_dominant_position=True` (`fight_engine.py:~2420`, reads `GNP_DOMINANT_DAMAGE_MULT` at call time); FE applies it post-primitive at `:3293` after damage is computed. FI's placement compounds against the un-scaled damage before subsequent multipliers (config `damage_multiplier`, etc.) apply; FE's does not. Measured effect (`outputs/amp_sweep_out.txt`, arms AMP=1.0 → AMP=1.5, symmetric FI=FE=amp): FI finish% moves 39.50 → 68.00 (Δ +28.5pp over 0.5 amp = **+5.7pp per 0.1**); FE finish% moves 35.00 → 45.75 (Δ +10.75pp over 0.5 amp = **+2.15pp per 0.1**). Ratio = **FI is ~2.65× more amp-responsive than FE** on the same fixture, same seeds. The two engines respond to the same constant with different sensitivities because the constant enters their damage equations at different points.

**Consequence for Stage 2a.** Unifying to a single engine requires unifying the placement, not just the value. Two changes are load-bearing and must ship together:

1. Amp application site is unified (either both in-primitive at `:2420` or both post-primitive at `:3293`) so future amp tuning has one location and one measured effect. Choice of site is a Stage 2a design call; both options were unmeasured pre-arc.

2. FE-defined constants consumed by FI (currently: `GNP_DOMINANT_DAMAGE_MULT` at `fight_engine.py:459`, and any others surfaced during Stage 2a's structural pass) are relocated out of `fight_engine.py`. Living in `fight_engine.py` makes them pre-gen consumers by default (see `### Site-3293 census — scope correction [filed 2026-08-14]`); relocation lets each constant declare its consumers explicitly rather than by module residency.

**Contract for future constants.** Until measured otherwise, any constant defined in `fight_engine.py` is a pre-gen consumer. Any sweep of such a constant must either (a) source-edit the value and rebuild the world under the swept value, or (b) rebind before pool build AND source-hoist any literal consumers in the same file. Runtime rebind alone measures a stale world (see the five-row world table in `### Measurement hazard — runtime-rebind sweeps vs source literals [filed 2026-08-14]`).

### Architecture correction — top-level `systems/` imports [filed 2026-08-15, FOTN full-fidelity wire, 8fd4573]

**The claim at CLAUDE.md `:1099-1100`** — *"Top-level `cage_dynasty/core/`, `entities/`, `systems/` — never imported by the web app. CLI tools use them. Web app does not."* — is **FALSE-AS-WRITTEN for `systems/fotn.py`.**

**Correction (bytes-verified).** PA's `wsgi.py` inserts `/home/vandopegaming/cage_dynasty/systems` onto `sys.path`. `game_bridge.py:62-78` uses `importlib.import_module` to dynamically load bare `"fotn"` before falling through to `"systems.fotn"`. The bare-name import resolves to `systems/fotn.py` via that sys.path entry. **MEASURED on PA:** `server.log` shows `✅ fotn loaded from fotn` on every reload in log retention; console `__file__` probe under the replicated sys.path confirms resolution.

**Scoped correction (both facts hold):**
- `from systems.X import ...` continues to FAIL on PA (the shadow via `cage_dynasty_web/systems/` intercepts package-form imports — the injury/coaches note remains correct as-written).
- Bare-name imports via `importlib.import_module` against paths on wsgi's `sys.path` DO succeed. `systems/fotn.py` is live in production via this mechanism.

**Grep hazard filed for future censuses.** Static import censuses (`^from`, `^import`) are structurally blind to `importlib.import_module(<string>)` and `__import__(<string>)`. Section 4b of the FOTN scoping (`outputs/fotn_scope.txt`) missed the fotn import for exactly this reason. Any future consumer-census claim must ALSO grep for `import_module(` and `__import__(` before asserting "no consumers."

The `## Architecture` block's package-form claim is left intact as the correct diagnosis for `from systems.X import Y` patterns; this entry annotates the exception rather than editing the block.

> **[ARCHIVED C28 2026-09-05 — moved verbatim to `claude/claude_md_archive_2026a.md`]**
>
> Two sections lived here (FOTN full-fidelity wire follow-ups, closed):
> - `### Builtin scorer status — never-fired fallback [filed 2026-08-15, FOTN full-fidelity wire, 8fd4573]`
> - `### Follow-up filed — tier threshold recalibration [filed 2026-08-15, FOTN full-fidelity wire, 8fd4573]`

### Regression + doc-hygiene sweep — post-`68dbd52` [filed 2026-08-15]

Docs sweep after the `_player_is_f1`/`_player_is_f2` NameError hotfix
at `68dbd5258341266f0abed38089d2cf1108af3e34`. Each subsection dated
2026-08-15, bytes-anchored at HEAD `68dbd52`. Two strike-and-preserve
edits applied elsewhere in this file (`## Architecture / Known hazards`
on wsgi.py; the `**Fixture is style-blind ...**` block above under the
928/928 gate coverage-limit discussion) — cross-referenced here.

#### STYLE-DEAD1 [MEASURED, bytes at HEAD `68dbd52`]

**`style_mod` is 0.0 on every live-play fight; the style-matchup
branch is dead in production.** Anchors: `_STYLE_STR_MAP` (dict
literal inside the `if STYLES_AVAILABLE:` guard block near
`_assemble_prefight`'s style-mod computation in `game_bridge.py`)
and the `_FightingStyleEnum(_STYLE_STR_MAP.get(...))` call two lines
below it. Enum def: `class FightingStyle(Enum)` in `core/types.py`.

Bytes:
- `_STYLE_STR_MAP` values are uppercase enum NAMES (`"STRIKER"`,
  `"COUNTER_STRIKER"`, `"BJJ_SPECIALIST"`, `"BALANCED"`,
  `"WRESTLER"`, ...).
- `FightingStyle` members have display-string VALUES:
  `STRIKER = "Striker"`, `WRESTLER = "Wrestler"`,
  `BJJ_SPECIALIST = "BJJ Specialist"`, `BALANCED = "Balanced"`,
  etc. Names are uppercase; values are the human-readable strings.
- `_FightingStyleEnum(_STYLE_STR_MAP.get(s1, 'BALANCED'))` is
  CONSTRUCTOR-form, i.e. **VALUE lookup**. `FightingStyle("STRIKER")`
  raises `ValueError` because no member has value `"STRIKER"` (only
  member `STRIKER` with value `"Striker"`).
- Enclosing `try:` / `except Exception: pass` swallows the
  ValueError silently.
- Consequence: `style_mod = get_style_matchup_modifier(fs1, fs2)`
  never executes; `style_mod` retains its pre-try value (`0.0`) on
  every fight.

**Corollaries:**

**(a)** Path A post-sim style-flip has never fired in production
— byte-verified via the flip's own guard. Anchor in `_run_real_engine`:
`if style_mod != 0.0 and abs(style_mod) >= 0.02:` (the flip body reads
`flip_chance = abs(style_mod) * 0.4` and inverts `raw_winner_f1` on
RNG hit). At `style_mod = 0.0`, `0.0 != 0.0` is `False` → the whole
condition is False → the flip body is unreachable, byte-verified at
the guard site. Any consumer downstream of `style_mod` in
`_run_real_engine` / `_assemble_prefight` sees `0.0` on every fight
since the map was written.

**(b)** The upset-probe artifacts under `outputs/odds_upset_curve*`
inherit their "production is style-aware" framing from the
`**Fixture is style-blind ...**` block earlier in this file. That
framing is FALSE AS WRITTEN at the outcome layer. Strike-and-preserve
applied to that block this pass — corrected reading points to this
STYLE-DEAD1 section. The construction-layer claim ("fighting_style
enum populated on `FighterAttributes`") remains correct — the enum
IS populated by `_make_fighter_attrs`. The outcome-layer claim
("production is style-aware in the fight outcome") is what's
falsified: the enum flows into a branch that value-lookups its own
name, ValueErrors, and gets caught.

**Fix has two behavior changes:**
1. Fix the map/constructor mismatch (either `_FightingStyleEnum[name]`
   bracket-form for name lookup, or change map values to display
   strings). This activates matchup modifiers — every fight with a
   non-BALANCED style pair starts producing a non-zero `style_mod`.
2. The Path A post-sim style-flip that reads `style_mod` starts
   firing — outcome behavior changes for fights with non-neutral
   matchups.

**Flip decision required first.** The dead branch has been dead for
the entire life of the map. Turning it on is a substantive
live-play tuning change, not a bugfix — the magnitude of
`get_style_matchup_modifier`'s output against the current tuned
finish rate is unmeasured. **NOT scheduled.**

#### COMMENTARY-STALE1 [MEASURED, bytes at HEAD `68dbd52`]

**`get_fight_commentary`'s fuzzy-match fallback poisons the cache
under the requested `fight_id`, and the write-path guard makes the
poisoning permanent.** Anchors: `def get_fight_commentary` in
`game_bridge.py` and the `if fight_id_key and fight_id_key not in
self._fight_commentary:` guard in the commentary-storage block
inside `_run_real_engine` (fires immediately after the sim call
returns).

Bytes:
- **Fuzzy match**: for each stored `(stored_id, lines)` in
  `self._fight_commentary.items()`, split the REQUESTED `fight_id`
  on `_`, keep parts `len > 6`, match if `any(p in stored_id for p
  in parts)`. Any 7+ char token collision returns another fight's
  commentary lines.
- **Cached under requested key**: `self._fight_commentary[fight_id]
  = lines` before return. Subsequent lookups on the same `fight_id`
  hit exact-match (poisoned) forever.
- **Synthetic fallback** (built from `winner_name` / `loser_name` /
  `method` / `round_finished` scanned out of `self._completed_events`)
  ALSO caches under the requested key at the end of its block.
- **Write-path guard** at the commentary-storage block inside
  `_run_real_engine`: `if fight_id_key and fight_id_key not in
  self._fight_commentary:` — the entire store block is SKIPPED if
  the key already has anything. Once poisoned by fuzzy or synthetic
  fallback, real commentary from a subsequent successful sim can
  never overwrite it.

**Origin — git log -S MEASURED**: `git log -S 'if parts and any(p
in stored_id for p in parts)' -- cage_dynasty_web/game_bridge.py`
returns exactly one commit: `56bf807 End of 2026-04-27 session — OVR
Phase 1, Bug D/F, is_title fix shipped` (initial commit,
2026-04-27). The fuzzy fallback is original code, ~4 months older
than the regression at `9adfeba`. **It did NOT paper over the
write-side failure — the write-side failure did not exist when it
was written.** The two bugs are unrelated in origin but compound in
effect: `9adfeba` broke the write side (fixed at `68dbd52`);
`56bf807`'s fuzzy match then made the resulting stale-content
behavior sticky under any `fight_id` whose split produced a
colliding token.

**Approved-in-principle fix scope (not scheduled, filed here):**
1. Delete the fuzzy-match block entirely.
2. Keyed miss → return `[]` with a loud log: `⚠️ commentary miss:
   {fight_id}`.
3. Narrow the Path B whole-block `except Exception: pass` around
   commentary extraction to specific exceptions and log on catch.
4. Dead unreachable block after the `return []` at the end of the
   eng_result-path branch (~40 lines duplicating the earlier
   extraction logic): filed as separate tech-debt commit, not part
   of the fuzzy-match fix.

**SHIPPED — `3e90dfe`, deploy-verified 2026-08-19 on PA.**

- Deploy: `git rev-parse HEAD` on PA matched local after manual
  `git pull` + Reload on the Web tab (webhook not used per operator
  choice).
- Server.log after one watched fight, standard grep set:
  `"Commentary stored"` present, `"Real fight engine failed"` **zero**,
  `"commentary miss"` **zero on happy path** (line exists in shipped
  bytes on PA, confirmed via the pull byte-match).
- Fix-scope items 1-3 shipped as filed; item 4 scope UPDATED
  (see below). Additional edit landed alongside: cache line at the
  synthetic-fallback branch's tail DELETED (uncached synthetic —
  same class of poisoning as fuzzy match via the write-path guard at
  `_run_real_engine:17968`).
- Item 2 filed-format-vs-shipped: filed spec at item 2 above shows
  one space between `⚠️` and `commentary miss`; shipped code
  (`game_bridge.py`, currently ~`:18102`) emits two spaces. Code is
  truth (strike-and-preserve — filed text preserved above, this
  line documents the alignment). Deploy grep substring
  `"commentary miss"` catches both spacings; no operational impact.
- Item 3 phrasing correction: spec's "Path B whole-block
  `except Exception: pass`" was descriptive-was-imprecise. The
  literal `: pass` pattern lived in `get_fight_commentary`'s
  eng_result-extraction branch except; `_simulate_card_fights:13657`
  (which the project
  vocabulary actually calls "Path B") already logged via
  `except Exception as _ce: print(...)`. BOTH excepts narrowed to
  `(AttributeError, TypeError)` in the ship for scope hygiene;
  both log with fight_id. Filed text preserved above; this line
  documents the two-site landing.
- **Item 4 scope UPDATE — dead-code strip is ONLY the unreachable
  block after the final `return []`** inside `get_fight_commentary`
  (content-anchor: begins with the comment
  `# Look for raw engine result in completed events`; ~40 lines
  duplicating the eng_result-extraction branch's logic). **The
  synthetic-fallback branch (`if fight_result:` block) is NOT dead code**
  — gate arm-3 falsified the session-inference to that effect; the
  branch fires whenever `fight_id` is in `_completed_events` without
  an `_engine_result` (a real production state), and the UI's
  "always non-empty when possible" contract depends on it. See
  cleared-suspect entry under `## Top-of-backlog` → "Recently
  reconciled (closed)".

**Gate at ship: 4 arms OLD (`6b873c4` via git worktree) vs NEW.**
- Arm 1 poisoning-kill: OLD returns A's lines under B's key
  + caches under B (poisoning); NEW returns `[]` + logs
  `⚠️  commentary miss: {fid}` + does not cache. PASS.
- Arm 2 regression exact-match: byte-identical. PASS.
- Arm 3 synthetic reachability: same 6 synthetic lines returned
  in both; OLD caches under fid, NEW does not. Also falsifies the
  "synthetic branch is dead" reading.
- Arm 4 re-poisoning under production write-path guard: OLD sticky
  (r2 = synthetic; guard blocks the real store because synthetic
  is already cached); NEW picks up real (r2 = REAL). Class-of-bug
  kill validated end-to-end.

#### Regression post-mortem — `9adfeba` → `68dbd52` [filed 2026-08-15]

**Extraction equivalence gates must run the ENCLOSING FUNCTION
end-to-end.** The v3 gate exercised `_assemble_prefight` in
isolation, then invoked `_simulate_narrated_fight_fn` directly.
It never ran `_run_real_engine`'s post-sim commentary-storage
block, which is where the lost locals (`_player_is_f1`,
`_player_is_f2`) were consumed. **Blast radius of an extraction
refactor = the scope of the enclosing function that was edited, not
just the byte-count of the moved lines.** A gate that scopes tighter
than the edit cannot certify the edit.

**Diff attribution requires locals analysis, not keyword greps.**
`outputs/stale_commentary_diag1.md` §5's "refactor NEGATIVE" verdict
was based on `git diff | grep -c 'commentary keywords'` returning 0.
That check measured the WRONG property: it looked for
commentary-related identifiers in the diff, when the actual failure
mode was locals-defined-by-the-removed-block still referenced by
unmoved code below. The correct attribution required: (i) enumerate
locals defined by the removed hunk; (ii) grep the post-sim range for
references to each; (iii) find the intersection.
`outputs/regression_attr1.md` did this and identified
`_player_is_f1` / `_player_is_f2` immediately. **A measurement of
the wrong property is worse than an inference from the right
property — because a measurement closes inquiry, and an inference
invites verification.**

**Deploy grep set update.** Add `"Real fight engine failed"` to the
standard PA `server.log` grep sweep alongside existing markers.
Any hit at production is a Path A crash under the enclosing
`try/except` in `_simulate_fight`, which fell back to score-based
sim and dropped commentary. First-line signal.

**Deploy grep set update — 2026-08-19, COMMENTARY-STALE1 ship
(`3e90dfe`).** Add `"commentary miss"` as a standing member of the
grep sweep. Zero hits on the happy path (real commentary stored →
hit at the exact-match branch). Any hit indicates a
`get_fight_commentary` call for a `fight_id` that has neither
stored commentary nor an entry in `_completed_events` — surfaces
new callers, save-load boundary issues, or `fight_id` schema drift
between store-side and read-side. Substring `"commentary miss"`
catches the emitted `⚠️  commentary miss: {fight_id}` regardless
of the ⚠️-vs-space count.

**Reviewer miss recorded.** The v3 gate was endorsed without an
enclosing-function requirement. Next extraction gate must either
(a) call the enclosing function end-to-end with a
live-representative fixture, or (b) explicitly prove the extracted
region contains no locals referenced downstream in the enclosing
function. Reviewer-side rule: **an assembly-isolation gate cannot
certify enclosing-function equivalence, ever.** Do not accept one
on that promise.

#### save/restore-required-for-presim [MEASURED, filed 2026-08-15]

**9 of 20 seeds flip live outcomes if pre-sim setup advances the
global RNG without save/restore around it.** Measurement from the
FOTN arc harness: `random.getstate()` before pre-sim +
`random.setstate()` after, vs. no bracketing, on 20 fixture-seed
pairs. 9/20 diverged (winner or method). Load-bearing for any code
path that (a) calls a computation consuming the global `random`
state before the fight, and (b) is expected to produce reproducible
fight outcomes under a fixed `random.seed(N)`.

**Gate-grade rule**, applies at least to:
- MC odds precompute (`_run_real_engine` sibling or wrapping caller
  — the arc's next scheduled work).
- Scouting reports (any RNG-consuming pre-fight computation on a
  fight the player will subsequently simulate).
- Amateur pipeline (if pre-fight bracketing computations consume
  RNG before advance).

**Pattern:**
```
saved = random.getstate()
try:
    _pre_sim_computation()
finally:
    random.setstate(saved)
```

If the computation is inside a subprocess-isolated context or uses
its own `random.Random(seed)` instance, save/restore is unnecessary.
The rule applies to the global module-level `random` state only.

#### SYSTEMS-on-sys.path harness rule [filed 2026-08-15]

**Any harness that instantiates `GameBridge` or invokes
`_run_real_engine` MUST include `sys.path.append(SYSTEMS)`.** The v1
assembly gate omitted this and silently ran with
`CONDITION_AVAILABLE = False` because `systems.condition` failed to
import. The stamina branch in `_assemble_prefight` was inert; the
gate reported PASS on an unexercised branch.

**Correct anchor pattern (v3+, standard):**
```
sys.path.insert(0, NARR)     # for `import commentary`
sys.path.insert(0, WEB)      # for `import game_bridge`
sys.path.append(SYSTEMS)     # for `from systems.condition import ...`
```
(Append, not insert — production wsgi.py appends `systems/` too, and
inserting would shadow flat-file resolution the web tree depends
on.)

**General rule:** unexercised branches do not equal PASS. Before
endorsing a gate, grep the harness's captured stdout / imports for
the `⚠️ ... not available` prints that the web tree emits at
module-load when a systems import fails. Absence of those warnings
is a necessary condition for the harness to have actually run
production code.

#### wsgi-610 [MEASURED 2026-08-15; re-measured 2026-08-20]

**Correction, 2026-08-20 measurement.** PA
`/var/www/vandopegaming_pythonanywhere_com_wsgi.py` measures
**479 bytes** as of the MC ODDS post-deploy hand-diff. Repo
`cage_dynasty_web/wsgi.py` is 610 bytes. The 131-byte delta is
COMMENTS + WHITESPACE only: repo carries two extra explanatory
comment lines (`# Add specific subdirs from game root — NOT the
root itself` and `# (adding root would expose CLI fight_engine.py
which shadows the web one)`) and one whitespace change on
`project_home =` that PA does not have. Functional sys.path.insert
lines (project_home / systems_path / narrative_path with the same
target strings) are byte-identical between PA and repo. No sys.path
behavior change.

The prior 2026-08-15 measurement recorded PA at 610 bytes; today
PA measures 479. **PA has shrunk since 2026-08-15**, presumably via
a hand-edit on PA console that stripped the two comment lines.
`git pull` on PA has tolerated this because the diff is in
untracked bytes (whitespace/comments beneath tracked line
identities). Drift is real but functional-equivalent;
reconciliation direction (repo→PA or PA→repo) is Van's call.

**Strike-and-preserve applied** to the `## Architecture / Known
hazards` bullet claiming byte-equivalence — the byte-equivalence
claim is retired for the current PA wsgi.py; the sys.path insertion
order and bare-import resolution behavior claims following it
remain UNCHANGED-IN-EFFECT. The file has grown in repo and shrunk
on PA; its role has not.

#### PA `fight_engine.py` drift re-confirmed [filed 2026-08-15]

Re-measured this pass. PA's `/home/vandopegaming/cage_dynasty/fight_engine.py`
still carries the 11 appended constants (repo +302 bytes) documented
under `## Known hazards`. Survived two `git pull` cycles since the
last check. Still latent — IMPORT-PATH-PROOF at `db15e3a` still
holds (running `fight_engine.__file__` in the live app resolves to
`cage_dynasty_web/fight_engine.py`, not root). No change to the
disposition or ordering of the reconcile-before-`git rm` prerequisite
already documented under Ship 1.

#### `cage_dynasty_web/.claude/` → `.gitignore` candidate [filed 2026-08-15]

`git status --porcelain` at HEAD `68dbd52` shows `?? cage_dynasty_web/.claude/`
as untracked. This is Claude Code's per-directory config, not a
project artifact. Bundle with the next `.gitignore` sweep (co-candidate:
the `outputs/` untracked entries that appear in every session's
status).

#### Caveat-#2 conversion — FOTN full-fidelity wire [filed 2026-08-15]

`### Follow-up filed — tier threshold recalibration [filed
2026-08-15, FOTN full-fidelity wire, 8fd4573]`'s caveat #2 ("**Harness
scored harness-built dicts, not bridge-built dicts.** ... Wiring
correctness is inferred from the diff ... but not measured end-to-end
through the bridge. **Production-path confirmation owed at deploy**")
remains **INFERRED** at HEAD `68dbd52`. The regression gate in this
session exercised `_run_real_engine` end-to-end
(`outputs/regression_gate_probe.py`, byte-identical 10/10 vs
worktree at `f334d6f`), but its result-field whitelist did NOT
include `fighter1_stats` / `fighter2_stats` — so it cannot certify
the FOTN wire specifically, only the commentary-storage block.
**Owed-at-deploy status unchanged.** PA `server.log` grep for
`⚠️ FOTN select_fotn failed` post-8fd4573 pull + template-render
check for `event.fotn.excitement_tier` values above `"Excellent"`
remains the outstanding conversion evidence.

### Belt-marker diagnostic — 3 sources + Bug X/Y split [filed 2026-08-19]

**Symptom set (three exhibits from live play):**
(A) 🏆 title-win marker on a fight PREDATING first recorded reign;
(B) 🛡️ title-defense marker on a fight inside a beltless gap
between reigns; (C) fight where fighter LOST their title carries no
marker at all.

**Working hypothesis at diagnostic entry:** "icons from per-fight
flags at booking/sim time, reigns from separate ledger at
title-change time, flags-vs-ledger can disagree." **FALSIFIED for
the 🏆/🛡️ icons; reframed for the 'Belt lost' text** — see
per-source breakdown.

**Three sources drive belt-related rendering on `fighter_profile.html`,
MEASURED bytes-anchored at HEAD `5c1477d` (pre-Bug-Y):**

1. **🏆/🛡️ icons** — computed inside the Jinja `{% set bns =
   namespace(won=false, defended=false) %}` block that iterates
   `{% for r in (belt_history or []) %}` in `fighter_profile.html`
   (currently `:1155-1194`). 🏆 fires when `r.won_week == fight.week`;
   🛡️ fires when `r.won_week < fight.week AND (r.is_active OR
   r.lost_week > fight.week) AND fight.result == 'W'`. **NO per-fight
   title flag involved** — icons cross-reference the ledger against a
   generic `fight.week` field. Ledger source: the
   `bridge.get_fighter_reigns(fighter_id)` method (currently
   `game_bridge.py:9328`) → serializes `self._belt_history` (a
   `world_init.BeltHistory` instance).
2. **"Belt lost" text** at the `{% if fight.was_title_fight and not
   is_win and not is_draw %}` gate in `fighter_profile.html`
   (currently `:1192`). Uses the per-fight `was_title_fight` flag.
3. **Reign card** (separate display element on the profile) — reads
   from the ledger, same source as source 1.

**Hypothesis: FALSIFIED for icons.** The icons don't consult any
per-fight `is_title_win`/`is_title_defense` flag; they compute from
ledger × fight.week alignment. There is one source for the icons,
not two. Symptoms A + B trace to **ledger data integrity** (see
Bug X below), not to flags-vs-ledger disagreement.

**Hypothesis: PARTIALLY CONFIRMED for source 2, with "disagreement"
reframed as "missing writer"** — see Bug Y below.

**Bug Y — SHIPPED at `2e4b328` (2026-08-19).** Live-play
fight_history writers did not populate `was_title_fight`.

- Three live-play writer sites: the `_simulate_fight` helper
  (winner_history_entry + loser_history_entry — the score-based
  fallback path; currently `game_bridge.py:5514/:5526`),
  `_simulate_card_fights` (Path B AI-fight loop's
  `ftr.fight_history.append({...})`; currently `:13913`), and
  `_run_real_engine` (Path A player-fight
  `ftr.fight_history.append({...})`; currently `:17818`). All three
  wrote ~10 keys per fight_history entry; none included
  `was_title_fight` pre-fix.
- Positive control: grep for `was_title_fight` writes across web +
  narrative + systems trees found writers ONLY in `world_init.py` —
  the inaugural-crown tombstone (currently `:1315`), the two
  `_simulate_single_fight` fight-record dicts (currently `:1701`,
  `:1716`), and the `_record_fight_history` helper's parameter
  passthrough (currently `:749`) — all pre-gen. Zero live-play
  writers.
- Consequence: every live-play fight_history entry had
  `fight.was_title_fight = None` under `dict.get`. Template's
  "Belt lost" gate short-circuited to falsy at operand 1.
  Structurally impossible to render "Belt lost" on any live-play
  title-loss fight.
- Fix: +4 lines, one `"was_title_fight": <bool>` per entry-dict.
  Bool semantics match pre-gen (`fight.get("is_title_fight", False)`
  never returns None).
- Forward-only: past saves' entries stay flagless as designed; no
  backfill.
- Gate: 8 entries (2 paths × 2 configs × 2 perspectives) OLD via
  `5c1477d` worktree vs NEW. OLD absent everywhere, NEW present with
  correct bool, all other keys byte-identical. Template consequence
  MEASURED at operand level (Jinja `and` short-circuit flips from
  `None`-falsy to `True`-passes).
- Site 1 (score-based fallback) is dormant since the `68dbd52`
  regression fix; bytes-verified via diff, not exercised at runtime
  in the gate. Filed honestly rather than claimed as covered.
- **UI proof of "Belt lost" text at HEAD `2e4b328`** lands
  organically at the next live title change in a session.
  Post-deploy verification is UI-side, not log-side; no new grep-set
  line expected.

**Bug X — OPEN, filed as design decision, not scoped ship.** Symptoms
A + B trace to legacy-save ledger data integrity from the
pre-BELT-STORE-UNIFY1 era (`e6b8033`, 2026-07-11). Two class-level
mechanisms bytes-visible in the current ledger writers at the
`world_init.BeltHistory` class (currently `world_init.py:551-650`):

1. Reigns with fabricated `won_week` values matching earlier fight
   weeks (Symptom A explanation).
2. Reigns with stale `is_active=True` or missing `lost_week`
   (Symptom B explanation) — pre-BELT-STORE-UNIFY1 title-transfer
   paths that failed to close the previous reign.

BELT-STORE-UNIFY1 closed the WRITE path forward-only. Reigns
generated post-`e6b8033` are consistent. But existing saves carrying
pre-fix drift were never reconciled — grep for `reconcile` in
`game_bridge.py` returned zero hits, confirming the
deferred-reconciliation-on-load noted in BELT-STORE-UNIFY1's own
commit deferral.

**Design fork, unscheduled:**
- **Option A: live with it on legacy saves.** New games
  post-`e6b8033` are clean by construction; legacy saves carry
  their stale ledgers forever. Occasional Symptom A/B renders on
  old saves are cosmetic.
- **Option B: template-side sanity checks.** `fighter_profile.html`
  could add defensive logic — e.g., if `r.won_week == fight.week`
  match ALSO requires the corresponding `fight.was_title_fight` to
  be truthy (post-Bug-Y, live-play entries have this field),
  spurious 🏆 markers on non-title fights would be suppressed.
  Doesn't fix Symptom B (stale `is_active` on the ledger side;
  needs ledger-side logic). Half a fix.
- **Option C: full ledger reconciliation on load.** Walk
  `_belt_history` at load time, cross-check against
  `_fighter_data` fight_history's `was_title_fight` entries, mark
  reigns as inactive where the ledger disagrees with the fight
  record. Substantive ship. Backfill-discipline concern: rewriting
  historical reign data changes saved state — needs a safety pass
  on what depends on `_belt_history` internals.

**No decision made by this entry.** Filed so the trade-offs are
visible next time a legacy-save Symptom A/B report comes in. Bug X
and Bug Y are decoupled — Bug Y's shipping doesn't affect Bug X's
disposition.

### MC ODDS — SPEC (Phase 3 step 2, pre-implementation) [filed 2026-08-18]

Pre-implementation spec for the MC odds loop — the arc's next scheduled
work per the save/restore-required-for-presim rule's "MC odds
precompute" bullet (currently `~L1716`). Source attribution per line:
**(F)** = feasibility memo `outputs/odds_mc_feasibility1.md` (293 lines,
untracked); **(S)** = signal inventory `outputs/odds_signal_inventory1.md`
(455 lines, untracked); **(T)** = timing output
`outputs/odds_mc_timing_out.txt` (120 lines, untracked);
**(C)** = existing CLAUDE.md rule/entry; **(INFERRED)** = session-handoff
decision, NOT on-disk in F/S/T. `outputs/odds_upset_curve*` explicitly
EXCLUDED from spec inputs per STYLE-DEAD1 corollary (b) — falsified
"production is style-aware" framing.

**Decision — MC on the real engine; formula-predictor rejected.**
- **(F, §Harness)** MC calls `fight_integration.simulate_narrated_fight`
  directly with real `FighterAttributes` and the LIVE_PLAY config
  triple `(55, 0.48, 10)`. Same engine live-play uses.
- **(S, Candidate 4)** Zero pre-fight probability functions exist in
  `fight_engine.py` / `fight_integration.py` (grep-verified on
  `def predict`, `win_chance`, `win_probability`, `favored`,
  `calculate_win`, `attribute_advantage`, `tale_of_the_tape` — six
  patterns, zero hits; positive control: `def calculate_strike_damage`
  present). No formula predictor to adopt.
- **(S, Candidate 5)** The one native pre-fight probability formula in
  the tree, `world_init.HistorySimulator.simulate_fight_simple`
  (currently `world_init.py:1465-1512`), is DORMANT on PA (fallback
  path only) and its input `skill_rating` "may not exist on live
  fighters (INFERRED — not verified)."
- **(INFERRED)** The "REJECTED" framing on the formula-predictor
  option is a Van handoff decision. Bytes support rejection
  (dormancy + input-ownership uncertainty + 0.2-0.8 clamp cap) but
  don't state "rejected" as a decision.

**Input consumption — same assembly path live fights use.**
- **(F, §4)** Live fights consume `_make_fighter_attrs` output
  (18 engine stats + fighting_style) + `_resolve_gameplan` output +
  LIVE_PLAY config triple + `starting_stamina_f{1,2}` derived from
  `_fighter_data['fatigue']` + player-side coach buffs
  (`_apply_corner_prefight_buff`, `_apply_coach_iq_prefight_buff`;
  neither fires on AI-vs-AI).
- **(INFERRED)** MC odds SHOULD call the `_assemble_prefight` bundle
  (the extraction that landed in `9adfeba` and was regression-fixed
  at `68dbd52`) to reuse the exact assembly path live fights use.
  F names `_make_fighter_attrs`, not `_assemble_prefight` — the
  bundle-reuse choice is a Van handoff.

**Save/restore around every MC batch — REQUIRED, gate-grade.**
- **(C, save/restore-required-for-presim rule, currently `~L1716`)**
  Already covers MC odds as its named consumer. Do NOT duplicate the
  pattern here; reference the rule.
- **(F, §2 recommended pattern)** Exact shape:
  ```
  _saved = random.getstate()
  try:
      for i in range(N):
          random.seed(mc_seed_offset + i)
          winner = fi.simulate_narrated_fight(fa1, fa2, config=cfg).winner_id
          # tally
  finally:
      random.setstate(_saved)
  ```
- **(F, §2 caveat)** The feasibility harness's UNSAFE-vs-SAFE test
  was INCONCLUSIVE on the tested pair (near-equal Strawweight,
  N=100, seed=42) — both variants landed on the same winner.
  Mathematics still guarantees state advancement; the CLAUDE.md rule
  stands on that basis, not on the test's null result.

**Adaptive N — 50 base, escalate toward ~400 in the uncertainty
band.**
- **(F, §3 stability table)** N=50 sufficient for one-sided pairs
  (gap-12 and gap-25 both showed 100/100 across 200 sims — zero
  variance to resolve).
- **(F, §3 SE math)** N≈400 needed for ±3pp CI half-width at p≈0.1
  (matches `4*0.09/0.0009 = 400`); N≈1111 at p=0.5 worst case.
- **(INFERRED)** The specific escalation trigger band — "35-65%" —
  is a Van handoff choice. F only says "adaptively increase N only
  when early sims show uncertainty" without naming a percentage
  threshold; 30-70% and 40-60% would equally satisfy the memo.

**Compute point — EVENT START, not booking; no line movement in v1.**
- **(F, §4 "Design implication")** Feasibility file frames BOTH
  options explicitly as "not a recommendation, just observation" —
  booking-time freezes the 6 fight-time-only inputs against stale
  snapshots; event-start sees live values.
- **(F, §4 enumeration 1-6)** The 6 fight-time-only inputs that
  drift booking → event: (1) fatigue → starting_stamina; (2) player
  gameplan choice; (3) AI gameplan (GAMEPLAN-AI-SELECT1); (4)
  injury cancellation / clearance; (5) attribute drift from
  weekly training; (6) coach staff for player. Config triple
  (`_assert_sanctioned_config`-pinned) does NOT drift.
- **(INFERRED)** EVENT-START decision is Van handoff. Rationale
  supported by bytes (6-input drift surface) but not decided in F.
- **(INFERRED)** "No line movement in v1" — single compute at
  event start, no re-computation as week progresses — not stated
  anywhere in F/S/T. Van handoff decision.

**Timing — MEASURED on dev, UNMEASURED on PA.**
- **(T, TIMING table)** Dev workstation: median **21.98-24.70 ms
  per sim** across N ∈ {1, 50, 100, 200}; p95 ≈ 1.3× median (no
  long-tail sim outliers); throughput **40.5-47.2 sims/sec**
  sustained. Machine profile **(F, §1)**: darwin, Python 3.13,
  no threads.
- **(F, §1)** PA production is **UNMEASURED this session. Expect
  2-5× slower (INFERRED, not measured)**. Recompute the timing on
  PA before locking any N choice.
- **(F, §1 per-card estimates on dev)** 10-fight card:
  N=100/matchup → ~21 sec (tolerable at card-build, background-able);
  N=400/matchup → ~92 sec ("uncomfortable during a UI request;
  would need async / background job"); N=1000/matchup → ~230 sec
  (not viable at card-build). PA multiplier stacks on top.

**STYLE-DEAD1 interaction — odds inherit style-blindness by
construction.**
- **(C, `#### STYLE-DEAD1` block, currently `~L1471`)**
  `_STYLE_STR_MAP` emits enum names; `_FightingStyleEnum(...)` does
  value lookup; ValueError swallowed → `style_mod = 0.0` on every
  live fight. Path A post-sim style-flip byte-verified unreachable
  at its guard.
- **(INFERRED)** MC odds run the real engine (see Decision above),
  so they inherit whatever style behavior production runs.
  Currently: style-blind at outcome layer. If STYLE-DEAD1 is ever
  fixed, odds inherit the fix automatically — no odds-side change
  needed.

**Downstream — Step 3 (display + American odds mapping), Step 4
(was_upset truth fix).**
- **(INFERRED)** Step 3: display + American-odds mapping (e.g.,
  prob 0.75 → −300, prob 0.25 → +300). Not addressed in F/S/T.
  Van handoff.
- **(S, Candidate 6 "The wire gap")** Step 4 target is
  `game_bridge.py:10642` (currently) — the sole live call to
  `generate_fight_reactions` hardcodes `was_upset=False`. The
  bridge's own `is_upset` computation at `:5350-5365` (currently)
  is never propagated into media reactions. Fix flows the computed
  bool through the call site.
- **(INFERRED)** Ordering rule: do NOT fix Step 4 (was_upset wire)
  before odds exist. F/S/T do not specify this ordering; Van
  handoff. Rationale (Van, confirmed 2026-08-18): once odds exist,
  "upset" can be defined by odds threshold (loser's implied
  probability > X%) rather than by the current rank-gap proxy at
  `:5350`.

**Not implemented, not scheduled by this entry.** Spec-first docs
commit for future work. Every (INFERRED) tag above will be
validated against the actual code path at implementation time —
Van handoff choices need to survive first contact with bytes.

### MC ODDS — SHIPPED (Phase 3 step 2) [ratified 2026-08-19, code `4ef0bd4`]

Decisions ratified at ship, sourced to the pre-implementation spec
above (§MC ODDS — SPEC) and the Step 1b/1c/parity-gate/M6-audit
iteration:

- **(a) Kwarg policy MIRRORS THE LIVE PATH PER FIGHT.** Player-
  involved → Path A: fatigue_source="attr", apply_cut_penalty=True,
  apply_player_buffs=True, apply_sponsor_boost=True,
  compute_style_mod=True. AI-vs-AI → Path B: fatigue_source="fdata",
  all other kwargs default False. Player-involvement resolved via
  the `get_player_fighters()`-derived predicate used inside
  `_assemble_prefight` and at the Path A player-fids resolution.
  `is_main_event` derivation also mirrors per fight — player-
  involved: `slot in {main_event, co_main}` (Path A); AI-vs-AI:
  `slot == main_event` (Path B).
- **(b) Assembly PER-SIM.** `_assemble_prefight` is called fresh
  inside each MC sim. Rationale (Step 1b mutation finding): the
  aggression buff at `fight_integration.py:403-412` is an in-place
  mutation on the caller's `FighterAttributes` and stacks under
  bundle reuse. Assembly-per-sim reproduces the live-fight lifecycle
  (fresh throwaway objects per fight) byte-identically; the buff
  fires exactly once per sim. Cost is amortized (M4 timing).
- **(c) Compute at EVENT START.** Odds fire once per fight at the
  start of the event containing that fight — for player-involved
  fights via a `_precompute_odds_for_fights` call before the
  player fight-sim loop in `_advance_week_impl`, for AI-vs-AI
  fights before `_simulate_card_fights`. Fatigue divergence from
  fight-time state is INTENDED — see spec §Compute point for the
  6 fight-time-only inputs. No re-computation as week progresses;
  no line movement in v1.
- **(d) Per-fight seed base.** Each fight's MC batch seeds RNG
  with `zlib.crc32(fight_id) + MC_ODDS_SEED_OFFSET + sim_index`.
  crc32 is stable across Python processes (unlike Python's str
  hash, which is PYTHONHASHSEED-salted and would silently break
  reproducibility across restarts). Deterministic per fight
  across processes; different fights draw different sequences.
  One unlucky N=50 batch is now a per-fight artifact, not a
  global sequence pinned onto every matchup. No line movement is
  possible by construction — recomputing identical inputs on the
  same fight_id yields identical odds.
  Ratified 2026-08-19; superseded the initial "identical sequence
  for every fight" scheme after M6a's 10-block sweep showed
  single-N=50 batch noise floor ~±14pp on symmetric matchups.
- **(e) N_BASE/N_MAX stay at 50/400.** Adaptive: 50 base;
  escalate to 400 if base landed in [0.35, 0.65] uncertainty band.
  Pending PA timing measurement — no re-tuning until PA is
  measured.
- **Storage.** Per-fight `mc_odds` dict on both the fight dict
  (pre-sim) and each result dict (post-sim, 4 propagation sites:
  score-fallback `_simulate_fight`, Path B non-draw + draw, Path
  A `_run_real_engine`). Shape:
  ```
  {"f1_id": str, "f2_id": str,
   "p_f1": float, "p_f2": float, "n_sims": int}
  ```
  Forward-only: `fight.get("mc_odds")` returns None on legacy
  saves and on fights where compute was skipped/failed. Never
  default to a displayed 50/50 — absent means absent.

**Pre-commit parity-gate finding (MEASURED).** First implementation
omitted `config=` on the MC sim call, silently running under
`_TRIPLE_FI_FALLBACK` (55, 0.48, standup=6) — a sanctioned triple
that passes `_assert_sanctioned_config`'s allowlist but is NOT the
`_TRIPLE_LIVE_PLAY` (55, 0.48, standup=10) live-play runs.
`standup_threshold` is a known outcome-moving lever (73/78 fixture
fights moved at 6 vs 10 per STAGE 1 addendum measurement above).
Fix: thread `_bundle["config"]` via the same `**({"config": ...}
if _fight_cfg else {})` form the live sites use. M5 config-
threading harness proof (`outputs/mc_odds_harness_out.txt`)
directly measures 3/3 MC sims receive standup_threshold=10,
damage=0.48, exchanges=55, submission_progress_to_finish=70.0,
submission_escape_threshold=85.0.

**M2 history correction (documented false, not dropped).** First
harness M2 built its reference sim by re-derivation, omitting
`config=` — so both the reference sim AND the MC sim ran under
the fallback triple. Bytes matched because both were wrong the
same way. That "byte-identical fight result" reading is FALSE-AS-
PROOF-OF-PARITY at the pre-fix diff and has been superseded by
the current M2 which byte-copies its reference sim from the Path A
call site. Pattern lesson: harness reference paths must be
byte-anchored to the live call, not rebuilt from memory.

**M6 INSTRUMENT SAGA (documented false, not dropped).** The first
M6 was VACUOUS: two byte-identical clone fighters + a deterministic
per-seed sim → Run 2 was byte-identically the SAME sim as Run 1
with labels swapped. p_f1 = 0.340 in both runs was guaranteed
regardless of any slot bias. Verdicts:
- "Corner bias detected" — **RETRACTED** (unestablished).
- "Live-play has been running with this bias since forever" —
  **RETRACTED** (INFERRED from a vacuous instrument).
- Step 3 clone-determinism re-run byte-exact confirms the sim is
  deterministic per seed given (fighters, config); slot alone does
  not perturb outcome on identical inputs.
- M6a 10-block sweep (10 × N=50 on the clone pair, seeds shifted):
  aggregate 0.482 across 500 sims, 2σ CI [0.437, 0.527] contains
  0.500. The production seed batch (0..49) reading of p_f1=0.340
  was an unlucky draw at the low end of the scatter, not a
  systematic effect on the pair.
- M6c/Step-4 discrimination probes were designed under the
  assumption "striking-only buff should move p_f1 sharply" —
  that assumption is falsified by the ENGINE-STRIKE-SENS1 finding
  below. Those probes cannot certify slot-symmetry.

### FILED OBSERVATIONS (from MC ODDS ship 2026-08-19, code `4ef0bd4`)

> **[ARCHIVED C28 2026-09-05 — moved verbatim to `claude/claude_md_archive_2026a.md`]**
>
> Two bullets lived here (MC ODDS filed observations, minor):
> - `- **Balance observation (INFERRED, single N=50 dev harness).**`
> - `- **N=50 noise floor (MEASURED).**`
>
> The larger `ENGINE-STRIKE-SENS1 [CLOSED 2026-08-21]` bullet that followed remains inline below (cited from OWED ITEMS CARRIED; contains four PROCESS RULES).

- **ENGINE-STRIKE-SENS1 [CLOSED 2026-08-21 — diagnostic complete,
  design call outstanding].**

  **ORIGINAL FINDING DOCUMENTED AS FALSE.** Filed 2026-08-20 as
  "+20 across all four striking stats vs a symmetric-elsewhere
  opponent moved P(win) by only +7pp at N=200 (2σ ≈ ±7pp)." N=2000
  paired confirmation measured **+1.0pp ±2.8pp** (Step 1 arm B vs
  A). Original +7pp was noise at 2σ; the "HIGH diagnostic
  candidate" filing at ≤2σ without a confirmatory run at 4×N is
  itself documented as a process defect (see PROCESS RULES below).
  Original number preserved above, not deleted.

  **ESTABLISHED RESULTS (MEASURED, N + CI in each):**
  - Striking family 88 vs 55 across 4 attrs (Step 2 arm E, N=2000):
    p_f1 = 0.5365 ±0.0223 (slot 1); arm E' = 0.5220 ±0.0223 (slot 2).
  - Grappling family 88 vs 55 across 5 attrs (Step 2 arm F, N=2000):
    p_f1 = 0.8035 ±0.0178; arm F' = 0.7980 ±0.0180. Same magnitude
    gap in the grappling family produces ~7× the win-rate movement
    of the striking family.
  - Kicks-alone 74 vs 61 (Step 5 arm H3, N=500) — placed
    deliberately below the fight_engine.py:2395 damage cliff
    (att.kicks>=75 AND def.kicks<60) — **p_f1 = 0.4160 ±0.0441.
    The better striker LOSES 58% of the time**, >3σ below chance.
  - Boxing 88 vs 55 (Step 3 arm G1, N=2000): p_f1 = 0.4805 ±0.0223.
    Point estimate on the wrong side of 0.500.
  - P2 landing-rate curve (100k direct calls to
    calculate_strike_success, grappler-pressure branches verified
    cold, JAB/CROSS mix): atk_boxing 55→0.47845; 65→0.46907;
    75→0.46551; 85→0.46276; 95→0.47508. Defender-side mirror:
    def_sd 55→0.48162; 95→0.47466. Curve is flat with a mid-range
    dip; 55-vs-75 out-lands 85-vs-75 by 1.6pp at ~7σ.
  - Classifier-pinned arms (Step 7 P3, both fighters verified
    `balanced`, all cliffs verified cold, N=2000 each):
    J1 (all-75) = 0.4840 ±0.0223; J2 (boxing 80 vs 70) = 0.4770
    ±0.0223; J3 (kicks 80 vs 70) = 0.4915 ±0.0224. All three
    statistically indistinguishable from each other and from chance.

  **FIVE MECHANISMS (all now anchored):**
  1. **LANDING-FLAT/INVERT** — hit-chance formula
     `success_chance = 0.20 + offense/(offense+defense+1) × 0.5`
     at `fight_engine.py:2344` compresses a 33-point gap to ~2pp;
     the upset branch at `:2346-2353` (offense < defense × 0.85 →
     18% chance of 0.70 floor, 17% chance of +0.22 boost) can
     invert the direction on close-boundary pairs. MEASURED (P2).
  2. **DAMAGE-SKILL-ABSENT** — `calculate_strike_damage`
     (`fight_engine.py:2364-2425`) reads `attacker.strength` for
     base damage and power bonus. Boxing and clinch_striking appear
     nowhere in this function. Kicks enters only as two binary
     cliffs (`:2395` >=75/<60 → ×1.25; `:2397` >=65/<50 → ×1.15).
     TRACED (Step 6 code); corroborated by P3 nulls.
  3. **STYLE-CLIFF** — `detect_fighter_style`
     (`fight_engine.py:1335-1467`): the balanced check requires
     `skill_range <= 10 across [boxing, kicks, takedowns,
     submissions, clinch_striking]` AND `avg_skill >= 68` (`:1354`).
     Any single-family gap >10 breaks balanced and enters a
     ladder whose first rung is sambo at wrestling_score>=72 AND
     bjj_score>=68 (`:1385`). Sambo carries `_STYLE_WEIGHTS`
     strike×0.9, grapple×1.3, sub×1.4 (`:1926`) plus +200 sub_weight
     tiers under BJJ/sambo branches (`:1798, 1821, 1838, 1867`).
     Labels eat stats. MEASURED (P1: H2 both sambo, H3 favored
     balanced / unfavored sambo, Step 1 defaults → ground_and_pound).
  4. **JUDGE-WEIGHTS** — `score_round` (`fight_engine.py:3762-3778`):
     `damage_dealt × 1.5, significant_strikes_landed × 1.0,
     takedowns_landed × 8.0, control_time × 1.5, knockdowns × 20.0,
     submission_attempts × 4.0`. On H1 baseline means the sig-strikes
     count channel is ~16 pts/round vs damage ~116 pts/round;
     striking-skill's only scorecard voice is the count channel
     (~7% of score) because its damage channel is empty (see #2).
     TRACED; corroborated by decision-share splits.
  5. **SD-AS-ANTI-CLINCH** — `striking_defense` at
     `fight_engine.py:2560` (`defense = defender.striking_defense
     + defender.speed // 3`) guards `CLINCH_ENTRY` grappling
     resolution, and at `:2575, 2577` gates a distance-keeping
     bonus for elite sd fighters against clinch closers. Effect on
     G4 (Step 3): win-neutral (0.4905 ±0.0224) but violently
     method-active — total finishes ~1088 vs ~850 in comparable
     arms; both fighters' KO+TKO up; submissions collapsed
     globally. Classifier ruled out for G4 (P1: both `balanced`).
     TRACED + MEASURED.

  **OBSERVATIONS FILED, NOT CHASED:**
  - `final_round=None` on 26,500+ consecutive sims across five
    Steps. NarratedFightResult carries the field; nothing populates
    it. STYLE-DEAD1-shape. Not chased this arc.
  - Draws scale with striking gap: 11 baseline → 68/82 in Step 2
    striking arms → 28/15 in grappling arms. Unexplained scoring
    interaction.
  - Slot-lean in Step 5 per-fighter stat differentials that the
    win column doesn't show: H1 symmetric fixture shows f1-leaning
    sig-strikes/control/damage. Instrument-level lean; all
    differentials should be read against H1, not against zero.
  - Baseline 75/75 sits on multiple engine thresholds — takedowns
    >=75 grants +10 striking defense to every fighter (`:2300`);
    kicks damage cliff needs >=75; sub-weight ladders at 75. Our
    "neutral" baseline was a loaded position.
  - **M6a Step-1-fixture caveat.** Step 1's default-defaults
    (strength/speed/cardio/chin=70; takedowns=65, td_def=70,
    top_control=65, subs=60, guard=65, clinch_control=65) resolve
    to style = `ground_and_pound` per P1 direct call. Step 2/3
    all-75 fixtures resolve to `balanced`. M6a's 10-block sweep on
    Step-1 defaults measured `ground_and_pound`-style behavior;
    Step 2/3 aggregate readings measured `balanced`-style behavior.
    The pairs are not equivalent baselines. Within-arm CRN
    comparisons unaffected; cross-arm generalization needs the
    caveat.
  - Arm C GnP asymmetry: dominant grappler (X_gr_str) won by GnP
    6 times; his outmatched opponent won by GnP 91 times. P1
    classifier lines from `outputs/engine_strike_sens1_step7_out.txt`
    (verbatim):
    `Step1_C_slot1_XGRSTR                     sambo                True`
    `Step1_C_slot2_YEQ                        ground_and_pound     False`
    → labels split (X_gr_str reclassified to sambo by the +20
    grappling family; opponent stayed ground_and_pound). Likely
    **STYLE-CLIFF** (mechanism #3), not a new finding. Verify
    before opening as a separate candidate.

  **PROCESS RULES ADOPTED (this arc):**
  (a) **No HIGH diagnostic filing at ≤2σ without a confirmatory
      run at 4× N.** ENGINE-STRIKE-SENS1's original +7pp at N=200
      with 2σ=±7pp burned two sessions before the N=2000
      confirmation caught it. Rule applies to all future
      diagnostic filings.
  (b) **Reported statistics must be pasted from output files, never
      transcribed.** Adopted after one fabricated-statistic incident
      this arc: the Step 5 report typed "246/234/20" as an H1
      win-count that has never appeared in any output file
      (caught only when the architect demanded the source line;
      the raw file always contained 250/230/20). Every reported
      statistic must be a grep hit from a persisted output.
  (c) **Primary evidence delivered inline, not as tool-output panes;
      no summary in place of primary evidence.** Adopted after the
      Step 4 report was delivered as collapsed sed panes that
      failed to survive the paste to the architect; only cc's
      summary reached them, and cc then self-scored its own
      predictions against the un-delivered primary. Code bodies
      and long pastes must be quoted as fenced blocks inline in
      the report text; scoring predictions is the architect's job.
  (d) **Redact tokens in pasted output.** Any output that contains
      credentials, session tokens, or API keys must be redacted at
      paste time. (Follows the general secret-handling rule.)

  **Design call outstanding.** Fix candidates each reshape the
  balance surface: skill-into-damage, gradient not cliff, retuned
  upset branch, classifier hysteresis or continuous styles,
  judge-weight rebalance. This arc's harness (`outputs/
  engine_strike_sens1_*.py`, CSV dumps) is the before/after
  instrument for whichever subset is chosen. Not scheduled.
> **[ARCHIVED C28 2026-09-05 — moved verbatim to `claude/claude_md_archive_2026a.md`]**
>
> Twenty-one bullets lived here (predecessor arc from MC ODDS follow-ups through the STRIKE-SKILL / LANDING / STAMINA / RECOVERY / DRAIN chain, culminating in STAMINA-DRAIN1 C12+C13 — all closed pre-fight-model-arc history):
> - `- **Live-inconsistency observation (MEASURED, docs-only).**`
> - `- **Refactor candidate (STRONG, parked).**`
> - `- **Cleanup candidate (C from Step 1b, parked).**`
> - `- **STRIKE-SKILL-DMG1 phase 1a [SHIPPED 2026-08-22, commits 6df956e + 668a7b1; ... 1b1ecee]**`
> - `- **STRIKE-SKILL-DMG1 phase 1b [SHIPPED 2026-08-24, commits 0562687 + a11d47b; ... 5429e0d]**`
> - `- **STRIKE-LANDING-AUDIT1 [CLOSED 2026-08-24, read-only diagnostic at HEAD a04faf4]**`
> - `- **LANDING-CURVE-RETUNE1 — Gate 0 [CLOSED 2026-08-25, C1 docs checkpoint at baseline 107a3c8]**`
> - `- **LANDING-CURVE-RETUNE1 — Gate 2 [CLOSED 2026-08-26, C3 docs checkpoint at baseline a242dc1]**`
> - `- **STAMINA-MODEL1 — Gate 0(b) [CLOSED 2026-08-28, C4 docs checkpoint at baseline 1f06802]**`
> - `- **STAMINA-MODEL1 — Gate 0(c) [CLOSED 2026-08-28, C4 docs checkpoint at baseline 1f06802]**`
> - `- **STAMINA-MODEL1 — Gate 1 pre-execution verification session [CLOSED 2026-08-29, C5 docs checkpoint at baseline 896425c]**`
> - `- **STAMINA-MODEL1 — A3-a fix + Gate 1 Step 2' outcome [SHIPPED 2026-08-30 as C6]**`
> - `- **STAMINA-MODEL1 — Gate 1 CLOSED + G1F findings + Q4d premise correction [SHIPPED 2026-08-30 as C7]**`
> - `- **STAMINA-MODEL1 — RECOVERY-WIRE1 fix + fixture re-baseline [SHIPPED 2026-08-30 as C8]**`
> - `- **STAMINA-MODEL1 — Design Gate 0 [CLOSED 2026-08-31, docs checkpoint at baseline 0ca052c]**`
> - `- **PREGEN-ROUND-WIRE1 [SHIPPED 2026-08-31 as C10 engine+docs commit]**`
> - `- **R1-REFILL1 [SHIPPED 2026-08-31 as C11 engine+docs commit]**`
> - `- **STAMINA-DRAIN1 [SHIPPED as C12 engine + C13 docs, 2026-09-01]**`
>
> Names still cited from the current arc (DMGCURVE1, ENGINE-STRIKE-SENS1, STRIKE-SKILL-DMG1, MC ODDS, RECOVERY-WIRE1) resolve to their full filings in the archive file. The C14 KEEP ruling below refers to the STAMINA-DMGCURVE1 identity wire (design detail in archive's STAMINA-DRAIN1 bullet).

- **DMGCURVE1-WIRE + P1 RULINGS [COMMITTED as C14, 2026-09-02]**

  WIRE DISPOSITION (Van P1 ruling 3: KEEP). The STAMINA-DMGCURVE1
  identity wire commits as a future dial: `damage_stamina_factor()`
  + `DMG_PIVOT = 0.0` / `DMG_COMPRESS = 1.0` (fe.py +15/−1, sites
  per as-built §3.2 / fe:554-562). Proven byte-inert at Gate 1a
  (3680/3680 A/B identical). NO behavior change ships in C14.

  P1 RULINGS RECORDED (Van, 2026-09-02, post-#22 measurement):
  (1) SURVIVING ENGINE = fi. fight_integration is the consolidation
  chassis; fe-only mechanisms (cut writer, heat system, failed-
  grappling counter damage) are deliberate carry-over candidates at
  P3, not lost. Evidence: P0 comparison_master (EP1@ident fi 32.91%
  / fe 29.74% DEC — both in Van's 25-45 band; POP@B9 fi 28.57% /
  fe 42.04%), fi's richer finish/style mechanics, correct KD-scoring
  call, activity-aware standup.
  (2) DEPLOY = GO, EXECUTED 2026-09-02 ~23:00 PDT: C6→C13 pushed
  896425c..727dee8; PA proof legs — refs/heads/main =
  727dee822aeb628813c0467ab38e029044dc0165, running
  cage_dynasty_web/fight_engine.py:547-548 = DRAIN_SCALE_K 0.6 /
  DRAIN_CARDIO_S 0.5, site HTTP 200. Instrument note: running-file
  grep is the PRIMARY proof leg henceforth; ref-file read is
  secondary (ref proves where main points, not what's checked out).
  Post-deploy owed items now DUE: PA violence-shift monitoring,
  tierA re-vintage, live-roster violence check on next live card.
  (3) DMGCURVE1 wire = KEEP (this commit).

  DIVERGENCE #22 — MEASURED + CONFIRMED (2026-09-02, artifacts
  outputs/sm1/fight_model/div22/): fe awards KD-asymmetric decided
  rounds to the KD SUFFERER 227/227 (100%); fi awards to the SCORER
  245/245 (100%) — opposite sides, instrument discriminated before
  acceptance. Consumer grep: round scores feed ONLY decision
  resolution in both engines, so P0 comparison DEC/finish RATES are
  CLEAN — #22 corrupts decision WINNERS only. Blast radius: ≤1.8%
  of fe decisions (54/2935 with ≥1 KD-asymmetric round, upper
  bound). The earlier "fe DEC rates contaminated" claim (P1 handoff
  + retiring-thread recap) is documented FALSE. Fix lands at Fight
  Model consolidation (fe retires); forward-only, no backfill.

  NEW FINDING (open): fi:1240 double-writes knockdowns_this_round
  (apply_damage already increments at fe:616) → fi per-round KD
  counts 2× actual; inflates 10-8 margins, does not flip winners on
  observed rows. Re-opens at consolidation.

- **FIGHT MODEL P1 CLOSED + P3 OPENED [C15 filing; rides with P3-1 commit]**
  P1 design phase CLOSED 2026-09-03. Ratified contract:
  claude/fight_model_v1_0.md (D1-D12; fi chassis; roster 19 incl. POWER;
  one contest function with declared P_even/S_c; five-part finish model,
  leg-kick TKO private dial ~1%; elite-peer mix 22/20/16/40/~2).
  P3 scope ratified 2026-09-03: claude/fight_model_p3_scope_v0_1.md
  (dockets P3-0..6; deploy freeze after P3-1 until P3-5 gates).
  D2 docket findings filed: F6 landing skill-slope ≈ 0 (signed,
  exact-anchored 2455/2455 both worlds); F7 finish-fest = sub-tick
  collapse under drain (12.59% vs 0.80%/tick, 15.7×); F8 submissions
  the one live skill wire (+13-16pp, +38pp extreme); F9 upset-branch
  inversion (−9.3pp extreme, vindicates upset-branch retirement).
  Artifacts: outputs/sm1/fight_model/d2_peven/ (per-call event CSVs
  banked). P2 sensitivity baseline artifacts:
  outputs/sm1/fight_model/p2_sensitivity/.

  INSTRUMENT NOTES (P3-1b, 2026-09-03): GE-6 filed — the P3-1 twin gate
  compared A/(A+B+D) to 50; with ~4% draws fair is ~48 (GE-2's error
  repeated by the architect). Corrected decided-share verdict: baseline
  52.8% (F1 bias), post-fix blocks ~49.5%/51.0% — fair. The P2b-pattern
  initiative wrapper is NOT RNG-neutral once the coin-flip tie-break
  exists (replay draws 2, tied path draws 3) — wrapper RETIRED for all
  post-fix-1 engines, ~1pp artifact measured. Seed block 950000+ pulled
  ~2.5pp low on twin decided-share — noise envelope of the coin-flip
  cascade is wider than naive binomial; future twin gates pool ≥2 blocks.

- **FIGHT MODEL P3-2 CONSOLIDATION [COMMITTED as C18, 2026-09-03]**
  Pre-gen now routes through fi — one engine. world_init:1425 calls
  simulate_narrated_fight with EXPLICIT config (LIVE_PLAY /
  championship); P3-2b three-path probe proved config= reaches
  LIVE_PLAY directly (bundle path NOT structurally required — the
  D2-era belief is amended in the design doc; D2 anchors remain
  self-consistent). simulation shim mirrors the fe pattern; sub_type
  wired to canonical_specialty_method (submission flavor preserved).
  fe.simulate_fight loses its last production caller —
  RETIRED-NOT-DELETED (the module still serves fi's shared
  primitives and score_round).
  MEASURED (2 worlds, seeds 20260904/20268823, before/after):
  0 simulate_fight_simple fallback fires; cut-MECHANISM finishes
  103 → 0 (fe-only writer; carry queued P3-4; fi's independent
  head-damage doctor stoppages persist, 12-19/world); records +
  belt lineage intact; world-gen wall 7.67s → 9.08s (+18%, vs 53%
  inferred pre-measurement); direct-call fi 4.92 ms/fight vs fe
  4.62 (+6.5%). BRIDGE STATE: pre-gen DEC 45.1% → 29.2% — INSIDE
  the 25-45 band, matching POP fi@B9's 28.6% (P0 instrument
  predicted the consolidated world). TKO share doubles (fi
  accumulator paths). Accepted per S4(a); never deploys under the
  freeze. Artifacts: outputs/sm1/fight_model/p32_census/ + p32_exec/.

- **FIGHT MODEL P3-3 CONTEST REBUILD [COMMITTED as C19, 2026-09-04 — STRUCTURAL]**
  One contest form everywhere: P_c = clamp(P_MIN, P_MAX,
  P_EVEN + S × (A/(A+D) − ½)), D13 composites, symmetric two-sided
  variance, upset branches RETIRED (_legacy_* preserved), sub lock-in
  on the same form, initiative dampened (K_SPEED_INIT=0.35, speed−50
  centered, coin-flip tie-break unchanged).
  CONSTANTS ARE PROVISIONAL per ruling S5 — magnitude calibration
  deferred to P3-5's single pass (contest dials + finish knobs together,
  final physics).
  STRUCTURAL GATES ALL PASSED: logger inert 100/100; no-op 600/600;
  F4 FIXED (boxing +2.13pp, CI excludes 0 — inversion lived in the
  contest layer); F3 striking_defense ALIVE (+3.94pp); F9 inversion
  GONE; F8 preserved (+13.3pp vs +14 target); F6 direction fixed
  (all strike slopes positive).
  MAGNITUDE READINGS (deferred, not failed): P_EVEN 2-6pp under
  targets (situational fog); slopes shallow vs D10 (dilution); speed
  neutral at all K (K sweep 0.02-0.35 exhausted, logged) — NEW
  FINDING F10, THE ACTIVITY TAX: acting more now costs stamina that
  the amplified stamina channel punishes (cardio +18.48pp, was +8.95).
  Speed's worth re-ruled at P3-5 after lever two.
  EP1 drift 99.4% finish — bridge state, P3-5 calibration target,
  freeze-protected. Artifacts: outputs/sm1/fight_model/p33_gates/
  (incl. full_diff.patch + dial log).

- **STAMINA-LEVER2 [COMMITTED as C20, 2026-09-04]**
  Cardio-owned in-round regen: `recover_stamina` scaled by
  `(1 + REGEN_CARDIO_S × (cardio − 60) / 40)`, S_r=0.5 (Van's word;
  minimal dose clearing T1). Between-round fatigue penalty routed
  through `spend_stamina` (K×g scaling) — fi:623/625 direct-write
  bypass CLOSED. Identity gate 200/200 pre-values (S_r=0.0 +
  routing=False); file-vs-rebind parity 200/200 byte-identical
  (MD5 `33178973796446aa6a4c129d16fb1144` on 200 fixed-seed POP
  fights, pre-flip runtime rebind vs post-flip file defaults —
  Gate-3a pattern).

  T1_R3 DEBT PAID: 14.12 → 29.2 at S_r=0.5 (target ≥20, owed to
  lever two since B9/C12) — measured 4a, B7 donors N=200/arm.

  B9 PREDICTION REFINED (documented as false in part): T2's
  remainder was assigned to lever two; measured on T2's DEFINING
  instrument (touched-zero, pop_pool1 flag — NOT close ≤ ε, NOT
  ledger-close; the architect's ledger assertion was corrected by
  measurement in 4a-bis discrimination probe), regen does not move
  touched-zero (R1 ~34% vs <25 target across the whole S_r sweep;
  R2 ~53% vs <40 target). T2 remainder refiled to P3-5 calibration
  (drain-side / activity economy).

  Report cells (P3-5 inputs, forwarded from 4a): cardio +25.25pp
  and climbing; speed −16.5pp (F10 deepens); POP ~50% DEC vs EP1
  99% finish — pool divergence noted for per-class targets.
  4a-bis instrument notes: ledger < proxy direction (grapple/sub
  drains fire post-last-CSS; mean Δ −1.69pt across 42 fighter-
  rounds, 20/42 ledger < proxy, 6/42 ledger > proxy — cc's
  "proxy inflated" hypothesis REFUTED, opposite direction);
  corner-bonus writes at fi:615-633 unwrapped in the probe ledger
  (3.24pt residual max, touched-zero boolean flag unaffected).

  No deploy per S2 freeze.

  Artifacts: outputs/sm1/fight_model/lever2* +
  outputs/sm1/stamina_drain1/p3_4a_bis/ (harness.py, parity_worker.py,
  parity_rebind.csv, parity_file.csv, frontier_table.csv,
  discrimination_probe.csv, p3_4a_bis_out.txt).

- **FIGHT MODEL P3-4b WINDOWS + CARRY-OVERS [COMMITTED as C21, 2026-09-04]**
  WINDOW mechanism (`cage_dynasty_web/window_registry.py`): 10 rows —
  7 existing style mechanics restated through one dispatch path
  (karate_patience, point_fighter_movement, brawler_walkthrough,
  counter_striker, adrenaline_surge, sambo_chain,
  sprawl_counter_momentum) + 3 new (elbow_cut_writer,
  doctor_cut_stoppage, sprawl_punish_attack).

  BYTE-EQUIVALENCE GATE: 700/700 (EP1-500 + POP-200) winner+method+
  round identical vs a pristine C20 worktree — restatement changed
  nothing. Data MD5s: EP1 `f9b4126e114f1602ac0fb2ea45112df2`, POP
  `33178973796446aa6a4c129d16fb1144` (same both trees, zero diff
  lines). No-op proofs: every new flag OFF → MD5-identical full
  file on POP-200 (`dae3732b6470373d59a57a4220e69c8b`).

  MEASURED ON:
  - Cuts RETURN to fi: **43 cut TKOs / 700 fights** across 2 worlds
    (POP 30/200 = 15%, EP1 13/500 = 2.6%). fe baseline reference
    ~52/world (103/2W). POP rate is ~2× fe baseline AND above the
    ~5-10%-of-TKOs design note — **CUT-RATE flagged to P3-5
    calibration** (dial `CUT_BASE_CHANCE=0.25` and/or the doctor
    constants). Two of five sample fights end on the new stoppage
    string `"TKO (Doctor Stoppage - Cuts)"`.
  - Sprawl-punish window: fires **41 times / 21 fights (10.5%)** on
    POP-200. Δwin +0.0pp on the current pool at ×1.25 — mechanism
    is live but sub-threshold at this magnitude. P3-5 dials
    `SPRAWL_PUNISH_DAMAGE_MULT` or extends window duration.
  - Heat: `heat_level` param wired ready on fi (`simulate_narrated_fight`
    + `NarratedFightSimulator.__init__`). Level 0 byte-inert
    (MD5 matches baseline). Level 80 → **+15pp finish rate**
    (46% → 61%, 25 decisions displaced). **ZERO live callers** —
    grep-verified (`heat_level` returns 5 hits in fe = the block
    itself, 2 in `narrative/rivalry.py` = Rivalry record field +
    serialize, 0 in `game_bridge.py`). Socket only; no heat
    source invented.

  Commentary layer: `log_window_event()` added to
  `FightCommentarySystem` in **`narrative/commentary.py`** (the
  LIVE file per PA sys.path — NOT the dead repo-root fork).
  12 hook lines mapped; window beats surface in
  `commentary.commentary_log` when `WINDOWS_LOG_ENABLED=True`
  (default False — no live rendering yet, opt-in only).

  Filed for architect review (in gate_tables.md):
  1. `_karate_patience` write site lives in fe (fe:2148-2156) and
     reaches fi via the `select_action` import at fi:38. Load-
     bearing cross-module dep not consolidated by P3-3; not broken
     but noted.
  2. `heat_composure_penalty` + `heat_aggression_bonus` are dead in
     fe (computed, never read); ported the shape to fi for parity;
     only `heat_damage_mult` wires downstream in either engine.
  3. Sprawl-punish Δwin=0.0pp on POP-200 → P3-5 dials.
  4. `"TKO (Doctor Stoppage - Cuts)"` is a new method string —
     downstream renderers/analytics keying on method may need
     pattern-matching updates (already handle the
     `"TKO (Doctor Stoppage)"` family).
  5. Draws vanish at heat=80 (5 → 0). Not a bug; scorecard
     separation cleans up when damage multiplies.

  No deploy per S2 freeze.

  Census (verbatim source sites for every mechanic):
  `outputs/sm1/fight_model/p3_4b/census.md` (436 lines).
  Artifacts: `outputs/sm1/fight_model/p3_4b/` (gate_tables.md,
  staged.patch, gate_worker.py, method_mix.txt).

- **FIGHT MODEL P3-4c SUBMISSION MODEL + CHIN/COMPOSURE WIRED [COMMITTED as C22, 2026-09-04]**

  §5a submission model shipped as REPLACEMENT (no toggle). Sleep +
  injury emerge alongside tap under heart-modulated tap threshold +
  refusal band. Chin + composure wiring flipped ON. Downstream
  method-string routing fixed (Path A, Path B, awards). Injury
  persistence wired via injury_hook. S2 freeze holds — NO DEPLOY.

  **FIX A — 3-tuple unpack (fe:3652 + test_sub_sim.py:128).**
  P3-4c §5a's `process_submission_progress` returns
  `(escaped, finished, finish_kind)`. Legacy 2-tuple unpackers at
  `fe.simulate_fight`'s internal loop and in `test_sub_sim.py`
  patched to consume the new 3-tuple (`_finish_kind` discarded on
  the fe path, which is retired-not-deleted and has no live
  production caller per verify.md T1).

  **FIX B — method-string routing (three sites).**
  1. `game_bridge.py:13748` (Path B `_simulate_card_fights`
     AI-vs-AI collapse): changed `_raw.startswith("Submission")`
     to `"Submission" in _raw`. Pre-C22 collapsed
     `"Technical Submission (rear_naked_choke)"` to `"DEC"`,
     causing `winner.sub_wins` at :13857 NOT to increment for
     AI-vs-AI submission-by-sleep finishes.
  2. `game_bridge.py:17919` (Path A `_run_real_engine` player-fight
     collapse): substring `"Submission" in method_raw` short-circuits
     to `"SUB"` before the method_map lookup. Pre-C22 the
     method_map miss fell to `method_raw[:10]` which produced
     `"Technical "` (10-char slice with trailing space) that
     persisted into `fight_history.method` and rendered as decision
     in templates.
  3. `awards.py:50` `canonical_specialty_method`: added explicit
     branches for `"Technical Submission ("` and
     `"Submission (Injury - "`. All three §5a submission forms now
     canonicalize to `"SUB (<sub>)"` — sleep + injury normalize
     to the same specialty as a tap of that sub type.

  **FIX C — injury_hook wired.** Added `GameBridge._sub_injury_hook`
  (`game_bridge.py:~9948-10063`) mirroring the existing
  `generate_fight_injury` persistence pattern from
  `_simulate_card_fights:13898-13930` — same `InjurySystem`, same
  `add_injury`, same `_apply_medical_recovery_reduction` call, same
  champion/top-15 news-headline shape. Hook maps fi's severity
  vocabulary (`MODERATE`/`SEVERE`/`CAREER`) to `InjuryType`, calls
  `generate_injury(fighter_id, injury_type, source="submission:<sub>",
  opponent_id=…)`. Random location pick from the severity's
  `INJURY_DESCRIPTIONS` table (matches how `generate_fight_injury`
  picks). Silent-guarded per fi's `try/except Exception: pass`
  wrapper at fi:1776-1777.

  Wired at Path A (`gb:17838-17847`, `_run_real_engine`) and Path B
  (`gb:13651-13662`, `_simulate_card_fights`). NOT wired at MC odds
  (`gb:17276+`): MC is a probability estimator that runs many sims
  per fight; persisting injuries there would multi-count.

  **FLAGS FLIPPED ON (window_registry.py).**
  `FI_CHIN_WIRING_ENABLED = True` and
  `FI_COMPOSURE_WIRING_ENABLED = True`. Van-approved by C22 paste
  based on verify.md T4 measurements:
  - HEART: sub-loss Δ = −21.5pp ±4.3pp (~10σ) at heart 90 vs 50
    defenders on sub-specialist attacker. HEART is not gated — read
    directly at fe:3522/3536.
  - CHIN (wiring-gated): kd_mean −18% relative at chin 90 vs 50
    (0.207 → 0.169). Aggregate KO+TKO shifts in the OPPOSITE naive
    direction (+7.2pp) because chin also lifts `_def_max_hp` at
    fe:3526 → higher `state_mult` at fe:3528 → higher tap threshold
    → sub finishes plummet, KO+TKO catches the rest.
  - COMPOSURE (wiring-gated): mean rock_duration −32% relative at
    composure 90 vs 50. Tertiary KO-while-rocked FLAT (composure
    gates duration, not KO probability per-rock-tick).
  - All three positive controls (attacker submissions 65→99;
    boxing 65→99; strength 65→99) proven-discriminating.
  N=1000/cell, seed block 981000+, on-disk flag state verified
  False during measurement.

  **GATES (all MEASURED, artifacts under
  `outputs/sm1/fight_model/p3_4c/verify/`).**
  - G1 ROUTING PROBE (`g1_routing_probe.py`): 18/18 assertions
    PASS. All three §5a submission forms collapse to SUB in Path A,
    Path B, and awards. No `"Technical "` truncation artifact.
    Sanity: KO / TKO / Decision do NOT leak to SUB.
  - G2 BRIDGE SMOKE (`g2_bridge_smoke.py`): located sleep finish
    at seed 982011 (`"Technical Submission (von_flue_choke)"` R1)
    and injury finish at seed 982001
    (`"Submission (Injury - calf_slicer)"` R1). Path A collapse
    routes both to `"SUB"` → `sub_wins`-branch guard passes for
    sleep + injury + tap. Scratch bridge `_sub_injury_hook` call
    persisted MODERATE injury to `_injury_system._injuries[fid]`
    (Δ=1); severity mapping smoke verified MODERATE/SEVERE/CAREER
    round-trip; invalid severity `"BOGUS"` produced silent no-op.
  - G3 RE-MEASURE EP1_500 flags-ON (`g3_ep1_flags_on.py`,
    `g3_ep1_flags_on.csv`): 500 fights, seed_base=982000, flags-ON
    disk state. **127 subs total (tap=100 sleep=7 injury=20)**;
    KO=275, TKO=87, DEC=11. INJURY_HITS via hook: MODERATE=20
    SEVERE=0 CAREER=0. `hook_fires == injury_kinds` ✓.
    Compare gate_tables.md flags-OFF seed_base=980000 baseline
    (119 subs — tap=85 sleep=7 injury=27). Drift is expected (flag
    state + seed base differ; CHIN+COMP ON cascade produces ~19.6%
    diff-line share on EP1 per T5 reconcile).
  - G4 SYNTAX + IMPORT (`ast.parse` on 6 touched files, plus
    `import game_bridge` end-to-end): PASS. Runtime flag state
    `True/True`.

  **RIDERS FILED (docs-only, C22 carries):**

  - **Legacy sub-model fields dead-in-legacy-only.**
    `submission_escape_progress` (fe:923) and
    `submission_escape_threshold` (fe:1036) are read only by the
    retired `_legacy_process_submission_progress`. Config kwarg
    `submission_escape_threshold=85.0` at `gb:17160` is harmless-
    but-dead. Deletion deferred to a future consolidation ship
    that retires `_legacy_process_submission_progress` itself.
  - **Pre-existing Path A specialty-label truncation surfaced by
    G1 sanity row.** `"KO (Head Kick)"` → `"KO (Head K"` in Path A
    (`gb:17931` fallback slice `method_raw[:10]`). Pre-C22
    behavior; not caused by this ship; symmetric to the sleep-string
    bug FIX B closed for submissions. Queued as a small cleanup
    for the next natural gb touch — substring-first classification
    for KO/TKO specialty labels would close the class.
  - **Pre-gen coverage for injury_hook.** `world_init.HistorySimulator`
    calls `engine_simulate_narrated_fight` at world_init:1441 but
    does not pass `injury_hook` (world_init doesn't own an
    `InjurySystem`). Consequence: joint-lock injuries in pre-gen
    history sim are NOT persisted. Fresh saves start with clean
    injury registries by design; live-play (post-new_game) is the
    first firing surface for the hook. Filed as a future design
    call, not a defect.
  - **P3-5 calibration inputs added.** Verify.md T4 sensitivity
    tables + gate_tables.md §5a EP1/POP splits + G3 flags-ON
    re-measurement are the before/after instruments for P3-5's
    single calibration pass (sub tap threshold width, refusal
    band, CHIN_KD_RESIST_SPREAD, COMPOSURE_ROCK_DUR_SPREAD).

  **SCOPE-DOC SYNC INCOMPLETE (owed to architect).**
  `claude/fight_model_p3_scope_v0_1.md` (disk) does NOT carry the
  "CUTS1" or "WEIGHTCUT1" post-arc entries or the "P3-5 item-7
  rate-only wording" the C22 spec referenced. Per architect
  directive ("if the disk copy lacks them, say so and STOP for the
  sync block rather than improvising"), only the base "4c SHIPPED
  as C22" mark landed in the scope doc this ship. The four
  addenda that were labeled by name in the C22 paste (CUTS1,
  WEIGHTCUT1, P3-5 item 7 rate-only) need to be paste-synced from
  wherever the architect's "project copy" lives — no attempt to
  reconstruct them here.

  **PROCESS RULES ADOPTED (this arc):**
  (a) No wiring flag flips without a defining-instrument
      sensitivity reading in a prior verify pass. C22's CHIN + COMP
      flip is anchored to verify.md T4's direct instrument
      measurements (kd_mean and mean rock_duration) — the aggregate
      KO+TKO rates were correctly identified as confounded and NOT
      used as the flip criterion.
  (b) When adding a hook socket to a shared engine, the wire in
      production callers must land in the SAME commit as the
      socket, unless there's a scoping reason (there wasn't here).
      C22 lands both together; heat_level's dangling-socket state
      (per CLAUDE.md P3-4b filing: "ZERO live callers") is the
      counter-example this arc explicitly avoided repeating.

  Artifacts (under `outputs/sm1/fight_model/p3_4c/verify/`):
  - `probe_arm_a_heart.py` + `arm_a_heart.csv`
  - `probe_arm_b_chin.py` + `arm_b_chin.csv`
  - `probe_arm_c_composure.py` + `arm_c_composure.csv`
  - `g1_routing_probe.py`
  - `g2_bridge_smoke.py`
  - `g3_ep1_flags_on.py` + `g3_ep1_flags_on.csv`

  Companion doc: `outputs/sm1/fight_model/p3_4c/verify.md` (654
  lines — full verify pass report).

- **FIGHT MODEL P3-4d POWER/STRENGTH SPLIT (D7) [COMMITTED as C23, 2026-09-04]**

  Split POWER (the 19th stat) from STRENGTH. Strength keeps the
  grappling-physicality lanes (throws/slams, clinch break, escape
  assist); POWER takes over the striking-damage + flash-KO lanes.
  Flag ON on disk. Style-informed distribution at world-gen +
  deterministic derivation at load-time for pre-4d saves. S2 freeze
  holds — NO DEPLOY.

  **LANES MOVED (fe:2833, fe:2837, fi:1328).** Read via module attr
  so runtime flag flips propagate (same pattern as CHIN/COMPOSURE
  at fe:737-747). At `FI_POWER_WIRING_ENABLED=True`:
  - fe:2833: strike-family base damage bonus (`base + (X - 50)/10`)
    reads `attacker.power` (was strength).
  - fe:2837: CROSS/HOOK/OVERHAND "power puncher" bonus
    (`damage *= 1 + X/200`) reads `attacker.power` (was strength).
  - fi:1328: V7 flash-KO branch (`if X >= 85: chance += 0.015`)
    reads `attacker.power` (was strength).

  **LANES KEPT for STRENGTH (grappling physicality):**
  - Takedown defense (fe:2973, fe:2986).
  - Guard passing / sweep contest (fe:3013, fe:3025-3037).
  - Clinch break (fe:3085-3086).
  - Slam damage (fi:1571).
  - Elbow-cut writer (fe:3863) — skin-contact pressure, not
    concussive power.
  - Combo-throw threshold gate (fe:3872-3874) — threshold check,
    not damage output.

  **FLAG ON RATIONALE.** `FI_POWER_WIRING_ENABLED = True` shipped on
  disk (was False through C22). G2 separability at N=1000/cell, seed
  base 983000, flag ON runtime probe:
  - POWER+20 (attacker) → KO+TKO share 0.9040 → 0.9340,
    **Δ = +3.0pp ±2.4pp (2SE) ALIVE**; kd_mean 0.012 → 0.034 (×2.8).
  - STRENGTH+20 (attacker) → KO+TKO share 0.8890 → 0.8900,
    **Δ = +0.1pp ±2.8pp FLAT** (strength correctly keeps grappling
    role and does NOT bleed into KO channel).
  - Positive controls (boxing+20 for striking channel; takedowns+20
    for grappling channel) both discriminate cleanly.
  - Direction gate satisfied: the one-punch assassin (power=90) and
    the ox (strength=90) are distinguishable on the KO instrument.
  - Per C22 rule (a): no wiring-flag flips without a defining-
    instrument sensitivity reading in a prior verify pass. G2 is
    that reading; Van approved the flip via C23 paste.

  **CANONICAL STYLE OFFSET at `core.types.POWER_STYLE_OFFSET`.** One
  dict, 28 entries, keyed by BOTH display names AND FightingStyle
  enum-string keys (union). World-gen (`_persist_fighter_to_gs`)
  reads by display name; bridge (`_make_fighter_attrs._a_power_derived`)
  reads by enum-string key (post `_STYLE_MAP` normalization). Both
  paths resolve to the same values. Pre-C23 two duplicated tables
  existed at world_init and game_bridge with an in-code comment
  falsely claiming they were the same table — now consolidated
  into one canonical dict. Values (world_init canonical set, bridge
  enum-keyed subset already matched — zero bridge-behavior drift
  from consolidation):
  ```
  KO-artist:  Knockout Artist +10, Power Puncher +8, Sprawl & Brawl +6,
              Pressure Fighter +5, Boxing +4, Ground and Pound +3,
              Muay Thai +2, Kickboxing +2
  Neutral:    Karate 0, Balanced 0, Clinch Fighter +2
  Grappler:   Counter Striker -1, Point Fighter -2, Judo -4, Sambo -4,
              Wrestler -6, BJJ Specialist -8
  ```

  **LOAD-TIME DERIVATION FORMULA** (`game_bridge._make_fighter_attrs.
  _a_power_derived`). For every fighter reaching the engine:
  1. If `_fighter_data['power']` present → use it (post-4d saves).
  2. Else if fighter object has `power` attr → use it (transients).
  3. Else derive:
     `power = clamp(1, 99, strength + POWER_STYLE_OFFSET[style_key]
              + crc32_noise(fighter_id, span=7) - 3)`.
     Noise is deterministic per fighter_id (crc32-seeded, so
     PYTHONHASHSEED-invariant across processes) and bounded to
     [-3, +3]. FORWARD-ONLY — derived value returned to engine but
     NOT written back to `_fighter_data`; same fighter_id yields
     same power on every reload. Pre-C23 saves REPLACE `strength`
     with `power` on the flag-gated damage lanes but their
     `_fighter_data` stays untouched.

  **WORLD-GEN POWER at `world_init.py`.** Two-step:
  1. `generate_attributes:991-1001` rolls `power` per skill_tier
     uniform range (novice 20-45 through elite 70-95). Pre-C23 the
     key existed but was DROPPED at persist ("dead key, no
     canonical analog" — verify.md T0c BURIED FINDING: the
     generator has been rolling and throwing away power since
     project launch).
  2. `_persist_fighter_to_gs` NOW un-drops the key AND applies
     `POWER_STYLE_OFFSET` bias (KO-artist +10 through BJJ Specialist
     -8), clamped to [20, 95].

  **MEASURE 1 — OVR DRIFT (seed 984000, N=289 AI fighters).**
  Physical composite went from `(str+spd+card+chin+rec)/5` (pre-C23)
  to `(str+spd+card+chin+rec+power)/6` (post-C23). ΔOVR = ΔPhysical/4
  (physical is one of four buckets in `FighterAttributes.overall`).
  Verbatim:
  ```
  AGGREGATE:
    |ΔPhysical| mean = 1.218    max = 4
    |ΔOVR|      mean = 0.304    max = 1.000
    fighters with |ΔOVR| ≥ 1 : 1 / 289 = 0.3%
    fighters with |ΔOVR| ≥ 2 : 0 / 289 = 0.0%

  BY STYLE (|ΔOVR| mean):
    BJJ Specialist   0.359   Balanced         0.382
    Clinch Fighter   0.341   Counter Striker  0.250
    Ground & Pound   0.344   Muay Thai        0.284
    Point Fighter    0.298   Pressure Fighter 0.271
    Sprawl & Brawl   0.370   Striker          0.243
    Wrestler         0.286
  ```
  **Roster OVR wobble is imperceptible.** Max shift = 1 point on 1
  of 289 fighters; zero shift ≥ 2. No visible player-side OVR
  disruption; existing rosters read the same post-C23 as pre-C23.

  **MEASURE 2 — WORLD-GEN POWER DISTRIBUTION (seed 984000, N=289).**
  Verbatim:
  ```
  AGGREGATE:
    power mean = 57.75    sd = 14.51    min = 30    max = 95
    fighters at 20-clamp:  0    at 95-clamp:  1

  BY STYLE (mean power, sorted high→low):
    Point Fighter    62.52 (sd 13.97)   [POWER_STYLE_OFFSET -2]
    Counter Striker  60.09 (sd 16.97)   [-1]
    Wrestler         59.94 (sd 14.90)   [-6]
    Muay Thai        59.72 (sd 15.49)   [+2]
    Pressure Fighter 58.20 (sd 18.11)   [+5]
    BJJ Specialist   57.48 (sd 13.80)   [-8]
    Sprawl & Brawl   57.13 (sd 13.48)   [+6]
    Striker          56.69 (sd 11.08)   [+4]
    Ground & Pound   54.79 (sd 14.93)   [+3]
    Balanced         53.74 (sd 13.00)   [ 0]
    Clinch Fighter   53.32 (sd 11.07)   [+2]
  ```
  Clamp discipline good: 0 at 20-pin, 1 at 95-pin (Pressure Fighter
  elite-tier fighter caught the +5 offset onto a high roll).
  **BUT — aggregate style ordering is SKILL-TIER-DOMINATED, NOT
  offset-dominated.** Sprawl & Brawl (offset +6, mean 57.13) sits
  BELOW BJJ Specialist (offset -8, mean 57.48). The +14pp offset
  spread between those two archetypes is invisible at aggregate
  because `_generate_fighter_attributes` rolls `power` uniformly
  over the skill_tier range (novice-elite spans 20-95), and each
  style's fighter pool has different skill-tier distributions.
  Style-tier confound dominates the offset signal at aggregate
  scale.

  The offset IS being applied (verified by G3 determinism test:
  Sprawl & Brawl offset +6 → derived power ∈ [strength+3,
  strength+9]) and IS separating fighters at the individual level
  and at fight-outcome scale (verified by G2 KO+TKO +3.0pp per +20
  power). The aggregate-mean tier confound is filed for P3-5
  calibration if per-style differentiation needs to be more visible
  at world-gen scan (e.g., tier-controlled offset or wider offset
  spread).

  **DAMAGE RECIPE SWAP (three sites).** All three read via
  `import window_registry as _wreg_pw; if _wreg_pw.FI_POWER_WIRING_ENABLED:
  _stat = attacker.power else _stat = attacker.strength`, matching
  the C22 CHIN/COMPOSURE runtime-flip-propagation pattern.

  **ENUMERATION SWEEP.** 30+ sites where the 19th stat had to be
  added or it would be silently dropped. Full list at
  `outputs/sm1/fight_model/p3_4d/census.md`. Key groups:
  - Engine dataclass: `FighterAttributes` field (`power: int = 50`),
    `to_dict`, `overall` composite (divides physical by 6).
  - Bridge assembly: `_make_fighter_attrs`, sc_coach specialty,
    `_DECLINE_PHYSICAL_STATS`, `_ATHLETIC_BASE_STATS`, `_TRAINABLE`,
    prospect-fighter stat check (18→19 threshold), scout-report
    attr_list, `_COMBAT_ATTRS`, equipment domain "physical".
  - World-gen: un-drop at persist, `_fighter_to_attributes` kwarg.
  - Attribute lists: `core/types.py:PHYSICAL_ATTRIBUTES`,
    `maintenance_training.py:PHYSICAL_STATS`,
    `models.py:ProspectAttributes`, amateur pools, routes stat lists.
  - Templates: fighter_profile Physical section, compare attr list,
    fight_camp tale-of-tape Physical group, training.html data-stats
    CSV (19 values) + JS signatures + `stats.length !== 19` check.

  **GATES (all MEASURED, artifacts under
  `outputs/sm1/fight_model/p3_4d/verify/`).**
  - G1 NO-OP EP1_200: MD5 byte-identical
    (`dc7cd9a3accce0452ee30e36fb12f7dd`) staged tree flag-OFF vs
    pristine C22 worktree. Confirmed byte-inert-OFF discipline.
  - G2 SEPARABILITY N=1000: POWER+20 ALIVE +3.0pp; STRENGTH+20 FLAT
    +0.1pp; positive controls discriminate. See flag-on rationale.
  - G3 DERIVATION: pre-4d fighter derives power=71 deterministically
    (Sprawl & Brawl, strength=68 → 68+6+noise); zero write-back;
    fdata['power']=87 respected; 6/7 distinct values across ids.
    Re-run post-canonical-table-unification: identical results
    (bridge enum-keyed subset already matched world_init values,
    so consolidation was arithmetic-neutral for the bridge derive
    path).
  - G4 ENUMERATION SWEEP: zero remaining 5-physical lists in web-
    tree production code; zero remaining 18-count JS checks.
  - G5 UI SMOKE: Power row in fighter_profile / compare /
    fight_camp; training.html threads fighter.power (2 sites), JS
    signatures + length check updated.
  - G6 SENSITIVITY SPOT N=500: direction consistent, power lift is
    0.27× kicks lift (no god-stat), strength Δ ≈ 0 (grappling role
    preserved).

  **RIDERS FILED (docs-only, C23 carries):**
  - Style-template goals in `training.html` don't yet reference
    `power` — the JS signature + statMap now include the arg (D14
    can wire `{focus:'power', target:goal(power,X)}` without a
    schema touch). Filed for D14 tuning batch.
  - `_STYLE_OVR_WEIGHTS` at `game_bridge.py:7595` doesn't declare
    per-style weights for `power`; `.get(stat, 1.0)` fallback at
    :7747 gives power weight 1.0 across all 11 styles. Filed for
    D14 per-style rebalancing.
  - CLI fork `systems/training.py:80` still enumerates 5 physicals
    (missing power) — CLI dead-in-runtime for the web app per the
    architecture doc; filed as pre-existing cleanup.
  - Pre-existing Path A specialty-label truncation (C22 rider,
    "KO (Head Kick)" → "KO (Head K") unchanged this ship.
  - Aggregate-mean tier confound at MEASURE 2 filed for P3-5.
  - **BURIED FINDING: world_init's `generate_attributes` at
    world_init:991-1001 has been rolling a `power` key per
    skill_tier since project launch, and `_persist_fighter_to_gs`
    at world_init:3068 explicitly dropped it ("dead key, no
    canonical analog"). Pre-C23 world_init world-gen rolled and
    discarded power on every fresh save. C23 un-drops it. No
    historical impact — the stat was invisible everywhere.**

  **PROCESS INCIDENTS (this arc, logged not hidden):**
  - The initial `_a_power_derived` docstring falsely claimed the
    game_bridge `_POWER_STYLE_OFFSET` table was "the same style-
    offset table as world_init._persist_fighter_to_gs" when it was
    a duplicated copy with matching values (bridge's enum-keyed
    subset happened to agree with world_init's display-name-keyed
    corresponding entries). C23 FIX A consolidated to one canonical
    dict at `core.types.POWER_STYLE_OFFSET` so the docstring
    becomes true; the pre-C23 comment shipped a doc-code drift
    that would have re-broken on the next unrelated bridge edit.
  - MEASURE 2 aggregate ordering did NOT show KO-artist above
    grappler by fighting_style at aggregate scale — expected the
    per-style mean to visibly order by offset, but skill-tier
    distribution per style dominates the +5 to -8 offset range.
    Not a bug (per-fighter derivation is correct; separability at
    fight scale is proven at G2) but the aggregate readout doesn't
    confirm the intent in one glance. Reported honestly. P3-5
    tier-controlled measurement is the natural follow-up if the
    per-style signal needs to emerge at world-scan visibility.

  Artifacts under `outputs/sm1/fight_model/p3_4d/`:
  - `position_census.md` (D15 step 1 ride-along, 34 positions +
    12 transitions + full consumer map).
  - `census.md` (T0c power census).
  - `gate_report.md` (verbatim gate outputs).
  - `measure_ovr_and_power.py` + `measure_ovr_and_power.json` (this
    ship's measurements).
  - `verify/g1_noop_ep1_200.py` + CSVs
  - `verify/g2_separability.py` + `g2_separability.csv`
  - `verify/g3_derivation.py`
  - `verify/g5_ui_smoke.py`
  - `verify/g6_sensitivity_spot.py`

- **FIGHT MODEL P3-4e AGGRESSION (D8) — MACHINERY SHIPPED DARK [COMMITTED as C24, 2026-09-04]**

  TENDENCY function + 4-rule circumstance table + FIGHT_IQ execution
  lane machinery all present; **both flags left FALSE on disk** based
  on bridge-path measurement (below). Machinery is dark on the live
  path; wired for the next iteration once the (b) instrument is
  fixed and the (d) Wrestler collapse is understood. S2 freeze
  holds — NO DEPLOY.

  **BURIED FINDING (elevated from census).** `FighterRecord` has no
  baseline `fighting_style` attribute — the field is only set on the
  record via the `hasattr(_frec, 'fighting_style')`-guarded dynamic
  path at `game_bridge.py:2344`, which never fires for fresh AI
  fighters. `_fighter_data[fid]['style']` is where world_init
  actually stores the style. **Consequence:** pre-C24
  `_resolve_gameplan`'s AI branch has been reading empty string,
  falling through `_STYLE_TO_CANONICAL.get('','')` → '' →
  `ai_gameplan_for_style('')` → `'BALANCED'` → aggr=0 range=0 →
  collapse to None for every AI fighter, every fight. **AI
  gameplans have been silently None since GAMEPLAN-AI-SELECT1
  shipped.** MEASURE section (c) below reproduces this at bridge
  scale: OFF arm = 19026/19026 (100%) None, ON arm = 26.4% None.

  **THREE MECHANISMS ADDED (machinery present, all dark):**

  1. **TENDENCY function** — `styles.tendency_for_fighter(style,
     personality)` returns `(aggression, range_bias)`. Pure
     deterministic table-lookup + int-add + clamp. Reload-stable
     by construction. Tilt tables:
     ```
     Personality: Warrior/Hungry +1; Competitor 0; Calculated/Political -1
     Style aggr:  Striker/Pressure/GnP/Sprawl&Brawl +1;
                  Counter Striker/Point Fighter -1; others 0
     Style range: Wrestler/BJJ/GnP +1; Counter Striker/Sprawl&Brawl -1
     ```
     Companion `preset_for_tendency(a, r)` and
     `TENDENCY_PRESET_MAP` (9 entries).

  2. **4-rule circumstance table** (`fi._apply_aggression_rules`,
     called at top of `_init_round`). Behind
     `FI_AGGRESSION_RULES_ENABLED`. Rules:
     - R1 behind on cards final round → aggr +1
       ("need a finish")
     - R2 chin ≤60 vs opponent.power ≥80 → aggr −1
       ("off the fence")
     - R3 opponent stamina ≤25 AND round ≥2 → aggr +1
       ("smells blood")
     - R4 ahead ≥2 pts + final + own health >70 → pull to 0
       ("run out the clock")
     G2 fixture pass: all 4 rules fire dial + commentary correctly.

  3. **FIGHT_IQ execution lane** (`fi._apply_iq_execution`, called
     at top of each `_simulate_exchange`). Behind
     `FI_IQ_EXECUTION_ENABLED`. Fires when fighter's `is_rocked`
     rises AND drift not yet applied for this rock episode:
     IQ<50 → aggression to +1 (brawler panic); 50-79 → +1 clamp;
     IQ≥80 → NO drift (elite composure). G3 defining instrument
     confirmed ALIVE at N=1000/cell: IQ 50 drifts on 7.8% of
     fights; IQ 90 drifts on 0.0% (elite composure gate holds).

  Also: TENDENCY-based AI plan (IMPL 2) is gated under
  `FI_AGGRESSION_RULES_ENABLED` — packages with the rules table
  because the AI-plan resolution reads `_fighter_data['style']`
  only under that flag (flag-OFF preserves the pre-C24 broken-but-
  stable empty-string → None collapse for G1 byte-identity).

  **G1 NO-OP EP1_200 vs pristine C23:** MD5 byte-identical
  `b6f7dac91ce983f4449152445477488f`. Confirms machinery is inert
  at flag OFF.

  **G4 TENDENCY table** (seed 985000, N=292 AI fighters):
  9 tuple outcomes across 5 personalities × 11 styles. Repeat-load
  stability 20/20 (pure-function guaranteed).

  **BRIDGE-PATH MEASUREMENT (the missing defining instrument for
  the decision gate — verbatim, N=321 OFF / N=309 ON, scratch world
  seed 986000).**

  **(a) Method mix:**
  ```
  bucket        OFF     ON      Δ
  DRAW             0      6     +6
  KO             153     90    -63
  TKO             61     78    +17
  OTHER          107    135    +28    ← includes short-form DEC codes
  ```
  Method-mix classifier missed the bridge's short-form `"DEC"` /
  `"SUB"` codes → they land in OTHER. Instrument note: KO drops
  63 fights (−41%), TKO gains 17. Real drift.

  **(b) PER-STYLE td/sub INSTRUMENT FAILURE.** All cells returned
  n=0 — the `_engine_result` reference isn't preserved on the
  completed-event fight dict at the Path B (`_simulate_card_fights`)
  path my hook exercised. Instrument bug, not data absence. **I
  cannot verify the grappler-vs-striker differentiation direction
  the DECISION GATE requires.** Filed as the first P3-5 dependency:
  either instrument this differently, or wait until per-fight
  engine result is persisted on the fight dict.

  **(c) RESOLVED PLANS — the BURIED FINDING repro:**
  ```
  preset            OFF (n=19026)    ON (n=11822)
  NONE              19026 (100.0%)   3120 ( 26.4%)
  AGGRESSIVE            0 (  0.0%)   3287 ( 27.8%)
  GNP                   0 (  0.0%)   1822 ( 15.4%)
  MEASURED              0 (  0.0%)   1618 ( 13.7%)
  TAKEDOWN              0 (  0.0%)    809 (  6.8%)
  DEFENSIVE             0 (  0.0%)    656 (  5.5%)
  SUBMISSION            0 (  0.0%)    510 (  4.3%)
  ```
  Bridge-scale confirmation: pre-C24 AI plans were 100% None; C24
  flag ON produces real presets.

  **(d) WIN-RATE SANITY (n≥5 in either arm):**
  ```
  style              n_off n_on  win_off  win_on   Δ
  Wrestler            20    15   55.0%    26.7%   -28.3pp  ← COLLAPSE
  Striker             20    12   60.0%    33.3%   -26.7pp  ← COLLAPSE
  BJJ Specialist       8    14   12.5%    50.0%   +37.5pp  ← BOOM
  Counter Striker      6    11   33.3%    63.6%   +30.3pp  ← BOOM
  Clinch Fighter      10    15   20.0%    46.7%   +26.7pp
  Ground & Pound      10    12   50.0%    66.7%   +16.7pp
  Balanced            11     9   54.5%    66.7%   +12.1pp
  Point Fighter        8     5   50.0%    60.0%   +10.0pp
  Muay Thai           15    13   60.0%    53.8%    -6.2pp
  Pressure Fighter    13    12   53.8%    58.3%    +4.5pp
  Sprawl & Brawl       5     4   80.0%     0.0%   -80.0pp
  ```
  Wrestler collapsed 55%→27% and Striker 60%→33% under flag ON.
  My strict `n≥20 both arms` gate reported "clean" because
  Wrestler's n_on=15 < 20, but the underlying pattern is
  incompatible with a "smarter AI" ship: grapplers other than
  Wrestler are winning MORE; Wrestler alone (which gets the
  TAKEDOWN preset) is losing MORE.

  **DECISION BRANCH FIRED: DARK.** Per the C24 spec's DECISION
  GATE: "If (d) trips or (b) is inverted: leave BOTH flags False
  on disk, commit the machinery dark, and file the measurement to
  P3-5 with the failing numbers." Both conditions apply:
  - (b) instrument failed — cannot confirm right direction.
  - (d) shows collapses (Wrestler −28pp, Striker −27pp) on styles
    with n=20 in one arm; the "clean" verdict from my code was
    too-strict-n interpretation of the gate. Wrestler at n_off=20
    with a 28pp swing is exactly the "collapse or explode" the
    gate protects against.

  **P3-5 CALIBRATION INPUTS filed with the numbers above:**
  - Fix the (b) instrument (persist `_engine_result` on the fight
    dict at Path B) so td/sub-per-style is measurable.
  - Diagnose the Wrestler collapse: TAKEDOWN preset applies
    `range_bias=+1` (grapple_weight ×1.20, sub_weight ×1.10) —
    likely over-commits Wrestlers to takedowns, they get sprawled
    or fail the shot, opponent counters. Candidate: soften range
    tilt for Wrestlers when opponent is a Sprawl & Brawl / high-
    TDD style.
  - R3 fires 64.5% on symmetric-cardio fixtures (G2 Part B) —
    ubiquity says the trigger is too permissive. Tighten the
    stamina threshold OR require a real gassed-signal (rock
    duration?) alongside stamina.

  **RIDERS (all filed, none fixed this ship):**
  - **`Gameplan.finish_seek` field is DEAD** (fe:1141). Third
    gameplan dial has no consumer. Filed for a separate ship if
    the third gameplan axis needs to come alive.
  - **`_heat_aggression_bonus` computed-never-read** in fi
    (`fi:427-446`). Mirrors C21 finding on fe. Filed.
  - **Counter mechanism keys on `fighting_style` substring** in
    `calculate_strike_success`'s counter branch (not on Gameplan
    or personality). DEFENSIVE preset does not activate a counter
    — the mechanism-vs-intent mismatch CLAUDE.md top-of-backlog
    already tracks. Redesign candidate.
  - **FighterRecord.fighting_style as a real field** — cleaner
    fix than reading through `_fighter_data['style']`. Filed as
    a separate cleanup ship; not this arc's problem.
  - **Bridge Path B method-string collapse** — bridge writes
    method as `"DEC"` / `"SUB"` short codes. My `bucket()`
    classifier keyed on "Decision"/"Submission" long forms. Not
    a bug in the bridge (short codes are the intended
    persistence shape) but a note for future measurement
    harnesses.

  **PROCESS INCIDENTS (this arc, logged not hidden):**
  - **G1 first attempt failed byte-identity** because I initially
    made IMPL 2 (tendency-based AI-plan resolution) unconditional.
    Even with FI_AGGRESSION_RULES_ENABLED=False, the swap changed
    AI plans on flag-OFF too, breaking pristine C23 byte-identity.
    Fixed by gating IMPL 2 behind `FI_AGGRESSION_RULES_ENABLED`
    (packaging TENDENCY-based AI plan + 4-rule table as "smarter
    AI" pack). G1 passed on retry.
  - **BURIED FINDING surfaced during G4 development.** I built the
    G4 harness reading `getattr(record, 'fighting_style', '')` and
    got N=0 fighters with real style. Traced the null result and
    found the field never gets set on FighterRecord. Pre-C24 AI
    gameplans have been silently None for the entire life of
    GAMEPLAN-AI-SELECT1. Not a regression from C24; an existing
    defect the resurrection measurement documented.

  Artifacts under `outputs/sm1/fight_model/p3_4e/`:
  - `census.md` (6-part read-only census)
  - `gate_report.md` (verbatim G1-G6 outputs)
  - `verify/g1_noop_ep1_200.py` + CSVs
  - `verify/g2_rule_fires.py`
  - `verify/g3_iq_execution.py`
  - `verify/g4_tendency_table.py` + JSON
  - `verify/g5_before_after.py` + CSVs
  - `verify/g5b_bridge_before_after.py` + JSON  ← this ship's
    bridge-path measurement

  **C25/C26 addendum (2026-09-05, docs-only correction to C24's
  measurement framing).** The C24 filing above reports the
  bridge-path (d) win-rate swings — Wrestler 55%→27%
  (Δ=−28.3pp) and Striker 60%→33% (Δ=−26.7pp) — as evidence that
  the machinery must ship dark. **Those swings are hypotheses,
  not findings.** Both style's n_off = 20 and n_on = 15/12; at
  those sample sizes the Wilson 95% CI on a proportion is roughly
  ±22pp per arm, so the observed ±28pp deltas are within noise.
  The two arms also ran on structurally divergent worlds
  (different fight matchups per week — 19026 plan-resolution
  calls OFF vs 11822 ON reflects the world's own AI-plan-driven
  scheduling divergence, not a per-fight discrepancy), so
  per-style paired comparison isn't even the correct instrument
  for this data.

  The correct re-measurement is fixed-card sets: identical
  pairings both arms, CRN seeds, N≥100 per style of interest.
  Filed as P3-5 item 11 STEP 0 in the scope doc. The DECISION
  to keep the flags dark still stands — but on the softer basis
  that (b) instrument was broken and (d) was inconclusive
  rather than "collapse confirmed." No dial moves until the
  re-measurement gives a real signal.

  Wrong-numbers rule applied: the C24 filing text above is
  preserved as-written (with the swing numbers as recorded);
  this addendum layers the correct framing on top rather than
  rewriting history.

  **C27 addendum (2026-09-05, docs-only correction to C25's
  byte-identical claim + KEEP ruling).** The C25 filing above
  claimed byte-identical MD5 vs pristine C24 (Gate 3
  `b6f7dac91ce983f4449152445477488f`). **That claim held only on
  the synthetic-fighter instrument** — the C25 G3 gate used the
  EP1 `gate_worker` whose fighter objects are plain `_F`
  instances without a `fighting_style` attribute, so both trees
  resolved to empty-string identically. **On the production
  path, C25 activated style-based AI plans at flag OFF** because
  `_resolve_gameplan` reads `getattr(_record, 'fighting_style',
  '')` and the promoted dataclass field now returns the real
  style instead of an empty string; the pre-C25 empty-string
  collapse-to-None that silently protected byte-identity is gone
  for post-C25 worlds. STEP 0 (P3-5 item 11) surfaced this as
  Finding #1.

  **C27 measurement.** 720 fixed pairings (120 per focal style ×
  6), CRN seeds 989100+, both arms at flags OFF; ARM A runtime-
  blanks `fighting_style` to reproduce the pre-C25 empty-string
  collapse; ARM B keeps fields as-is (production). Plan census
  confirmed ARM A = 100% None (1440/1440) and ARM B = 2.6% None
  (38/1440) + real presets. Per-focal-style win-rate deltas
  ranged from −7.5pp (BJJ Specialist) to +3.3pp (Pressure
  Fighter), ALL within ±2SE=12.3-12.9pp; **zero styles show
  confirmed >10pp swing (Δ>10pp AND |Δ|>2SE)**. Overall method
  mix moved DEC +3.9pp, DRAW −1.0pp, KO 0.0pp, SUB −2.5pp, TKO
  −0.4pp — no bucket over the 8pp trigger. Outcome MD5s diverge
  as expected (ARM A `2725115facd00744dbba8269693422e4` vs ARM B
  `0fdd0a77c9c7d66e165870b3783a4329`).

  **Decision (Van-approved via C27 paste): KEEP.** The activated
  behavior is `GAMEPLAN-AI-SELECT1`'s designed intent finally
  functioning after ~2 months of silent no-op. Docs-only C27;
  no code change to re-dark.

  Full C27 measurement: `outputs/sm1/fight_model/p3_5/item11_c27/
  report.md`.


### NEW STANDING RULE (C27 lesson, 2026-09-05)

**Equivalence gates must run on the PRODUCTION population when a
change touches record shape or bridge lookups.** A synthetic-
fixture MD5 cannot certify bridge behavior. C25's Gate 3 passed
byte-identical against pristine C24 because the EP1 `gate_worker`
uses plain `_F` synthetic fighter objects that don't carry the
promoted `fighting_style` attribute — the gate could not observe
the very change C25 was making. The C25 change was safe (Van-
ruled KEEP at C27), but the gate did not certify safety; it
certified only that the synthetic path was unaffected.

Practical shape of the rule going forward: any commit that
touches `FighterRecord` / `CampRecord` / other dataclass fields
consumed by the bridge, or that touches `_resolve_gameplan` /
`_make_fighter_attrs` / any bridge helper that reads through a
record, MUST include an equivalence gate that:
1. Builds a fresh world via `bridge.new_game()` (real
   FighterRecords, not synthetic fixtures), OR
2. Loads a real save via `bridge.web_load()`, OR
3. Explicitly documents "no bridge-lookup change; synthetic
   fixture certifies engine layer only."

The gate must exercise the code path the change touches on the
production population. Byte-identical against a synthetic fixture
is not evidence when the change lives above the engine.


### FIGHT MODEL P5-A FINISH MODEL [COMMITTED as C29, 2026-09-05]

D9 build shipped: **health as stoppage pressure, one check, naming
table** (fight_model_v1_0 §9). fi's ~55 scattered stoppage
constants collapse to 8 named globals in fe.py, plus §5a's already-
named submission set and two structural carve-out thresholds (F3
leg-kick D12 carve-out; F11 doctor-cut writer flag-gated).
Machinery only — **no calibration**; P5-C is the single tuning
pass. S2 freeze holds — NO DEPLOY.

**D9 BUILD.**
- New `fe.check_stoppage()` helper: single choke-point that reads
  post-damage health against a heart-adjusted critical line, with
  context bumps (rocked +8 / dominant-position guard damp −5) and
  a between-round multiplier (×2.5). Emits KO / TKO (specialty) /
  TKO (Referee Stoppage) / TKO (Doctor Stoppage) / TKO (Corner
  Stoppage) via `_finish_specialty_label()` naming table.
- fi call-site: one `check_stoppage(...)` at the end of
  `_execute_strike` (in-exchange path), one
  `check_stoppage(is_between_round=True)` in the between-round
  block of `_simulate_round`. Rolls in F1/F2/F4/F5/F6/F7/F12/F13
  **removed**; accumulator state (`_clinch_body_acc`,
  `_gnp_accumulation`, `_rocked_shots`) **kept** for context.
- Carve-outs preserved per D12 spec: F3 leg-kick TKO
  (private-dial), F11 doctor-cut writer (`FI_CUT_WRITER_ENABLED`
  flag-gated, dark on disk today), F10 §5a submissions
  (untouched), F16 decision scoring (untouched), F0 `apply_damage`
  body-cumulative TKO branch (preserved as damage-input
  fallthrough).

**THE 8 KNOBS** (fe.py new module-level constants, provisional
values — magnitude calibration deferred to P5-C):
- `FINISH_CRITICAL_LINE_BASE = 40.0` — health level below which
  check_stoppage begins rolling. Approximation: legacy F6/F7's
  TKO_GNP_HEALTH_THRESHOLD/TKO_STANDING_HEALTH_THRESHOLD were 18
  and 15 with rocked/KD gates layered on; new base sits higher
  because it applies uniformly and context bumps carry the
  differentiation.
- `FINISH_CURVE_STEEPNESS = 0.90` — steepness of the pressure
  curve below the line. Higher = sharper cliff. Approximation:
  chosen so the aggregate finish rate lands near legacy
  behavior at the fixture level; P5-C sweeps this against
  target §9 40% DEC.
- `FINISH_HEART_LINE_SHIFT = 20.0` — critical-line reduction at
  HEART=100 (linear from 50). At HEART=90: line = 40 − 20*(90−50)/50
  = 24; at HEART=50: line = 40 (no shift). Direction confirmed by
  G6 defining instrument (Δ mean HP at stoppage = +6.28pp per
  40-point heart gap, elite heart takes ~6pp more damage before
  stoppage).
- `FINISH_CONTEXT_ROCKED_BUMP = 8.0` — added to effective critical
  line when defender is rocked (rocked fighters stop earlier).
  Approximation: legacy F4 rocked-shots gate had a 0.05 per-shot
  ramp; +8 line-shift chosen to reproduce roughly the same "rocked
  amplifies finish" magnitude.
- `FINISH_CONTEXT_GUARD_DAMP = 5.0` — subtracted from effective
  critical line when defender is in a defensive/guarded position
  (dampens stoppage pressure). Approximation: mirrors the direction
  legacy F6's `top_control >= 85` boost implied (elite grapplers
  finish faster in dominant, defenders survive longer in guarded).
- `FINISH_BETWEEN_ROUND_MULT = 2.5` — multiplier applied to
  stoppage pressure at round breaks (doctor + corner windows).
  Approximation: legacy F12 doctor gate compressed ~30 in-round
  ticks worth of pressure into one between-round check; ×2.5
  chosen so a defender at critical-line health has meaningful
  stoppage probability at the round bell.
- `FINISH_LEG_KICK_ACCUM_THRESHOLD = 6` — F3 D12 carve-out.
  Legacy hard-coded `6` at fi:1553-1565 promoted to named constant;
  value unchanged (~1% target rate per D12).
- `FINISH_CUT_STOP_THRESHOLD = 2` — F11 D12 carve-out. Legacy
  `doctor_check_cut_threshold` (config) promoted to named constant;
  value unchanged. Flag-dark today per `FI_CUT_WRITER_ENABLED`.

**RETIRED CONSTANTS** (documented-superseded; retained as module-
level constants in fe.py and re-imported by fi.py for provenance
grep — flagged as retired-as-decision-dials, no longer read by any
production stoppage path):
- `FLASH_KO_DAMAGE_THRESHOLD` (70.0), `FLASH_KO_BASE_CHANCE`
  (0.03), `FLASH_KO_MAX_CHANCE` (0.12) — F5 flash-KO roll removed.
- `TKO_GNP_HEALTH_THRESHOLD` (18.0), `TKO_GNP_BASE_CHANCE` (0.15),
  `TKO_GNP_MAX_CHANCE` (0.45) — F6 V7 TKO GnP roll removed.
- `TKO_STANDING_HEALTH_THRESHOLD` (15.0), `TKO_STANDING_BASE_CHANCE`
  (0.10) — F7 V7 TKO Standing roll removed.
- `TKO_DURABILITY_FLOOR` (0.35), `TKO_DURABILITY_CHIN_DIVISOR`
  (300.0), `TKO_DURABILITY_HEART_DIVISOR` (350.0),
  `TKO_DURABILITY_COMPOSURE_DIVISOR` (450.0) — GROUND-STOPPAGE-FIX1
  durability multiplier for F6/F7 (dependent — dead-with-parent).
- In-fi hardcoded constants retired inline (bodies removed):
  - F1 clinch-body: threshold 30, cap 0.22, step 0.025, offset 25,
    floor 0.4, heart div 320, composure div 450, muay-thai rate
    1.4 (accumulator increment KEPT).
  - F2 GnP: threshold 75, cap 0.22, step 0.025, offset 70, floor
    0.35, heart div 300, composure div 450, style rate 1.2, mount
    rate 1.1 (accumulator increment KEPT).
  - F4 ref stoppage: cap 0.22, step 0.05, floor 0.35, fight_iq div
    250, heart div 350, composure div 400 (`_rocked_shots` counter
    KEPT for context).
  - F12 doctor-health: health thr 28, damage.head thr 55, cap 0.14,
    step 0.003, offset 55, floor 0.5, heart div 250,
    chin-compromised mult 1.35.
  - F13 corner: round gate 2, health thr 22, KD thr 2, cap 0.18,
    step 0.06, offset 1, floor 0.3, heart div 300.

Approximate count: ~55 (~40 inline + ~11 named + ~4 GROUND-
STOPPAGE-FIX1) → **8 named globals**. Van's "~40 to ~8" spec
target met on order of magnitude.

**GATES (all MEASURED, artifacts under
`outputs/sm1/fight_model/p3_5/p5a/`).**

**G1 LABEL REACHABILITY: PASS.** Old-label set = 25 distinct
method strings. New naming-table output set covers every one via
one of: `check_stoppage._finish_specialty_label` health-zero
branch, `check_stoppage` between-round branch, `check_stoppage`
in-exchange branch, F3 inline carve-out, F11 inline flag-gated cut
path, F10 §5a untouched, F16 scored decision untouched.
**Newly minted labels: 0.** Full mapping at
`g1_label_reachability.md`.

**G2 BEFORE/AFTER METHOD MIX** (fixed-card CRN, seeds 992000+,
N=500 EP1 pairs, pristine C28 worktree at `/tmp/p5a_pristine_c28`
vs staged P5-A). **CRN paired agreement, N=500: winner 88.2%,
method 35.6%.**

| bucket | pristine C28 | staged P5-A | Δ |
|---|---:|---:|---:|
| KO | 228 (45.6%) | 29 (5.8%) | −39.8pp |
| SUB_tap | 120 (24.0%) | 102 (20.4%) | −3.6pp |
| SUB_injury | 41 (8.2%) | 35 (7.0%) | −1.2pp |
| TKO (bare) | 33 (6.6%) | 138 (27.6%) | +21.0pp |
| TKO_doc | 17 (3.4%) | 32 (6.4%) | +3.0pp |
| DEC | 17 (3.4%) | 11 (2.2%) | −1.2pp |
| TKO_gnp | 17 (3.4%) | 115 (23.0%) | +19.6pp |
| TKO_body | 15 (3.0%) | 26 (5.2%) | +2.2pp |
| SUB_sleep | 9 (1.8%) | 9 (1.8%) | 0 |
| TKO_legs | 3 (0.6%) | 3 (0.6%) | 0 |
| TKO_ref | 0 (0.0%) | 0 (0.0%) | 0 |
| TKO_corner | 0 (0.0%) | 0 (0.0%) | 0 |

Drift explanation: pristine's F5 flash-KO explicitly set
`health = 0` on fire → "KO" label. Staged's flash-KO scenarios
flow through apply_damage's normal damage → health drops →
check_stoppage catches while health is still > 0 → "TKO" label.
Same class of finish, different name. Overall finish rate ≈ 97-98%
both arms. Method drift is EXPECTED per §5a precedent; **not
judged here** — banked for P5-C.

Raw: `g2_pristine_c28.json`, `g2_staged_p5a.json`.

**G3 STORY SAMPLES.** Three located empirically + one filed as
reachable-but-not-firing.

| tag | pi | method | round | fighters | verdict |
|---|---:|---|---:|---|---|
| KO | 7 | `KO` | R2 2:27 | w0_116e6ffd (81) vs w1_3eb4b485 (82) | ✓ narrated |
| REF | 1115 | `TKO (Referee Stoppage)` | R1 2:38 | w2_2ef9e9ec (83) vs w7_f9a03859 (82) | ✓ narrated |
| DOC | 5 | `TKO (Doctor Stoppage)` | R1 5:00 | w0_116e6ffd (81) vs w0_f97b69e0 (81) | ✓ narrated |
| CORNER | — | `TKO (Corner Stoppage)` | — | — | 0/3000 EP1 fights; reachable per G1 but empirical rate is P5-C tuning input |

Full samples: `g3_story_samples.md`, `g3_story_samples.json`.

**G4 NEW-STRING PATTERN CHECK: PASS.** Newly minted labels = 0
(from G1). Every emittable label ({KO*, TKO*, TKO (specialty)},
plus untouched Submission*/Decision*/Draw* families) is a
pre-existing string that survives Path A `_run_real_engine`
collapse, Path B `_simulate_card_fights` collapse, and
`awards.canonical_specialty_method`. No consumer code required.

**G5 SYNTAX + IMPORT: PASS.** `python3 -c "import ast; ast.parse(...)"`
on both touched files: OK. End-to-end
`import fight_engine, fight_integration`: OK. `check_stoppage`
binding is the same function object on `fe.check_stoppage` and
`fi.check_stoppage` (same-module import).

**G6 HEART READING (defining instrument).** Fixture: same attacker
(OVR mid-70s, boxing 85, power 85), defender heart=50 vs heart=90,
all other defender attributes matched at 70. N=1000/arm, seeds
993000+.

Stoppage rate:
- HEART=50 → 99.8% (998/1000) ±0.3pp (2SE)
- HEART=90 → 99.3% (993/1000) ±0.5pp (2SE)
- Δ = +0.5pp ±0.60pp (2SE) — not distinguishable from 0 at this
  fixture. Both arms ~99% finish rate.

Health-at-stoppage distribution (loser HP at fight end):
- HEART=50 → mean = 16.4, sd = 11.0, p50 = 16.1, p75 = 22.0
- HEART=90 → mean = 10.2, sd = 10.8, p50 = 8.4, p75 = 13.3
- **Δ mean (H50 − H90) = +6.28 ±0.98 (2SE) — SIGNIFICANT.**

**Verdict: elite heart takes MORE damage before stopping (goes
measurably deeper).** Van's spec target confirmed. Arithmetic:
HEART=90 fighter's effective critical line = 40 − 20*(90−50)/50 =
24; HEART=50's = 40; six-point average gap in stoppage-health
matches the direction.

Method-mix side-effect at HEART=90: `KO` label 9.3% vs 3.5% at
HEART=50 — lower critical line means defenders more often reach
health=0 (KO label) instead of stopping earlier at TKO. Same
finish rate, different naming — consistent with the model.

Full data: `g6_heart_reading.json`.

**V1 PRE-GEN ROUTING VERIFICATION** (session addition,
`v1_routing_probe.py` + `v1_routing_out.txt`). Instrumented both
`fight_engine.simulate_fight` and
`fight_integration.simulate_narrated_fight`, then generated one
fresh world at seed 994000 (120-week history sim, 286 fighters, 40
camps, 120 events, 1606 pre-gen fights, 9 champions).

Call counts:
- `fe.simulate_fight`: **0**
- `fi.simulate_narrated_fight`: **1606**

**Verdict: fe entry NEVER fired.** C18's "fe retained as fallback"
path has not fired in this measurement — pre-gen routes 100%
through fi. Census.md's "fe finish machines still LIVE for pre-gen"
line was a doc error and has been corrected in the same commit;
the census now reads "DEAD post-C18, C29 V1 verified — deletion
candidate at the next legacy-consolidation ship."

**RIDERS FILED (docs-only, C29 carries):**
- **Corner stoppage 0/3000 in EP1** — reachable per G1, empirical
  rate = 0 at the fixture. Between-round KD gate + health
  threshold + round-gate combo is too rare on EP1 elite-peer pool
  (~80 OVR) where back-to-back KDs are rare and fights end
  earlier. **P5-C tuning input** — knob to move if the label
  needs a real live rate.
- **Winner agreement 88.2% at CRN, N=500** — 12% of paired fights
  flip winner between pristine C28 and staged P5-A. Stoppage
  timing legitimately changes outcomes: a fight that ended R2
  under flash-KO explicit-health-zero mechanics can now end R3
  under critical-line pressure with a different scoring cascade.
  Not a defect; measured drift and expected.
- **True-KO share ~7% at HEART=90 vs ~3.5% at HEART=50** —
  critical-line lever. When P5-C tunes
  `FINISH_CRITICAL_LINE_BASE`, expect KO share to move inversely
  (lower critical line → fewer TKOs / more KOs at the same
  underlying finish rate).
- **Method-mix reshape banked** — the full G2 table above is the
  before/after instrument for P5-C's single calibration pass. §9
  target 40% DEC not addressed here (fixture is 97-98% finish
  rate; population-level DEC calibration is a per-pool sweep, not
  this 1v1 fixture).
- **V1 verdict** — fe.simulate_fight is dead code as of C18;
  filed as deletion candidate at the next legacy-consolidation
  ship (not this commit; keeps C29 scope tight).

Full report: `outputs/sm1/fight_model/p3_5/p5a/report.md`.
Spec (verbatim SPEC-START/END): `claude/fight_model_p3_5_spec_v0_1.md`.


### FIGHT MODEL P5-B1 — D17 STAMINA FLOOR + D18 POWER MODEL [COMMITTED as C30, 2026-09-05]

Van rulings D17 + D18 become physics; BF-2 offset-table aliases
fixed in-scope; BF-1 filed with a defining-instrument style-
coherence measurement (STYLECOHERENCE1 queued post-arc). Machinery
only — no calibration. S2 freeze holds — NO DEPLOY.

**D17 STAMINA FLOOR.** New constant `fight_engine.py:627
COMPOSITE_STAMINA_FLOOR = 0.5` at the D9 physics-knobs block. Seven
LIVE composite-scaling sites rewritten from
`x *= (state.stamina / 100)` → `x *= max(COMPOSITE_STAMINA_FLOOR,
state.stamina / 100)`:
- `select_action` stamina_factor (`fight_engine.py:2475`)
- `calculate_strike_success` LIVE D13 (`fight_engine.py:2876-2877`)
- `calculate_grappling_success` LIVE D13 (`fight_engine.py:3114-3115`)
- `attempt_submission` sub_lockin (`fight_engine.py:3598-3599`)
- `attempt_submission` starting-progress offense (`fight_engine.py:3612`)
- `process_submission_progress` tighten offense (`fight_engine.py:3682`)
- `process_submission_progress` sub_escape (`fight_engine.py:3693-3694`)

Five LEGACY-RETIRED sites SKIPPED (dead-with-parent at next
legacy-consolidation ship): fe:2962-63 / 3303-04 / 3760 / 3763 /
3775. DAMAGE-scaling site UNCHANGED per D9-era rule
(`fight_engine.py:819` `damage_stamina_factor()` keeps its inline
0.5 floor). fi has zero composite-scaling sites; all fi stamina
reads are regen/drain arithmetic or state comparison
(grep-verified). One constant, no inline 0.5s.

**D17 (a) — cardio Δwin, N=1000/arm, starting_stamina=40 (drain
zone throughout).** Fixture: mid-tier balanced fighter (all ~65,
striking_defense 75, heart 75) vs same-shape attacker; two
defender variants (cardio=55 low, cardio=75 high, +20 gap). Seeds
995000+.

| | pristine C29 | staged D17 | Δ |
|---|---:|---:|---:|
| high-vs-low share | **73.31%** | **56.03%** | **−17.28pp** |
| high-cardio wins | 703 | 562 | −141 |
| low-cardio wins | 256 | 441 | +185 |
| KO/TKO/SUB/DEC/DRAW | 13/1077/0/825/85 | 10/1326/0/511/153 | — |

**D17 compresses cardio's win Δ by −17.28pp** (73.3% → 56.0%).
Direction is Van's "+25pp god-channel compression" prediction.
TKOs shift up (+249), DECs drop (−314), draws rise (+68) — low-
stamina fighters retain enough contest weight to finish AND to
make cards closer.

**D17 (b) — finish-rate-by-round, 5R at starting_stamina=20
(exhausted-but-dangerous fixture).** Two mid-tier defenders
(cardio 55/60), 5R, seeds 995500+, N=1000.

| round | pristine C29 | staged D17 | shift |
|---|---:|---:|---|
| R1 | 3 | **999** | +996 |
| R2 | 1 | 0 | −1 |
| R3 | 197 | 0 | −197 |
| R4 | 556 | 0 | −556 |
| R5 | 212 | 0 | −212 |
| finish_total | 969 | 999 | +30 |

**Mechanism proven.** Pristine: stamina/100 = 0.20 → contest
weight crippled → fighters can't land clean shots → survive to
R4-R5 for the eventual finish. Staged: floored to 0.5 → contest
weight degraded but not crippled → land finishes R1. Whether
R1-heavy at start-stam=20 is the RIGHT magnitude is a **P5-C
calibration input** (S_r=0.5 is Van's "minimal dose" — the fixture
starts at 1/5 the normal stamina and the model rewards it with the
minimum survival floor). Narration sample owed as follow-up:
`RoundStats.to_dict()` doesn't expose `stamina_end` — mechanism
proven via R1/R4 shift; narrated sample requires commentary-log
inspection (lightweight follow-up, not gate-critical).

**D17 (c) — POP touched-zero R1/R2, N=400, starting_stamina=100
(natural, 5R).** Both arms: 0/400 R1 touched-zero, 0/400 R2
touched-zero. **Null result — honest.** At natural stamina across
a varied POP, no fighter drains to 0 by R1 or R2 on 5R either
arm. D17 is mechanism-neutral on this fixture because stamina
never reaches the range where the floor engages. The (a) reading
already proves the mechanism engages when stamina IS in the drain
zone; (c) shows the POP simply doesn't hit that zone at natural
starting stamina on 5R. Comparable D3 pre-C29 baseline numbers
(under STAMINA-DRAIN1 filing) came from a different generation
code path with different cardio distributions — cross-comparing
would be apples-to-oranges. Filed as P5-C calibration input, not
P5-B1 gate.

**D18 POWER GENERATIVE MODEL UNIFIED.**
- `world_init.py:1001` DELETED `"power": random.randint(low,
  high)` from `generate_attributes`; replaced with a `# D18`
  comment.
- `world_init.py:3096-3145` reshaped: was `if _pw_off and 'power'
  in _fdata: _fdata['power'] = _fdata['power'] + _pw_off`; now
  `_fdata['power'] = clamp(20, 95, _fdata['strength'] + _pw_off +
  random.randint(-8, 8))`.
- BURIED FINDING fix in scope for the D18 site: `getattr(fighter,
  'fighting_style', '')` → `getattr(fighter, 'style', '')`.
  GeneratedFighter's actual attribute is `.style` (line 1115); the
  D18 formula wouldn't reach POWER_STYLE_OFFSET without this fix.
  See BF-1 below for sibling sites.
- Comment notes the ±8 gen vs ±3 derivation band difference is
  intentional (reconstruction narrower than creation).

**D18 (a) — per-style power means, CRN, seed 995500.** Pristine
C29 shows CHAOTIC ordering (Point Fighter −2 at top, Wrestler −6
above Sprawl & Brawl +6, Pressure Fighter +5 below Balanced 0 —
tier confound dominates as documented C23 rider). Staged D18 on
seed 995500 shows **ordering now follows offsets** (Sprawl & Brawl
+6 at 68.48; BJJ Specialist −8 at 51.46; 17-point gap in the
right direction). Seed 995500 also surfaced BF-2 (Ground & Pound
and Striker still at 0 offset). Post-BF-2 fix, re-measured on
seed 995600, N=292:

| style | n | mean | expected |
|---|---:|---:|---:|
| Clinch Fighter | 4 | 63.75 | +2 |
| **Sprawl & Brawl** | 17 | **63.47** | **+6** |
| Pressure Fighter | 35 | 61.71 | +5 |
| Ground & Pound | 25 | 61.64 | +3 |
| Balanced | 38 | 60.87 | 0 |
| Muay Thai | 17 | 60.71 | +2 |
| Striker | 60 | 59.95 | +4 |
| Point Fighter | 10 | 58.20 | −2 |
| Wrestler | 42 | 53.14 | −6 |
| **BJJ Specialist** | 39 | **48.59** | **−8** |
| Counter Striker | 5 | 37.80 | −1 |

**Tier confound dies as predicted.** 15-point spread from Sprawl &
Brawl to BJJ Specialist in the correct direction. Counter Striker
noisy at n=5 — small-cell caveat, not a mechanism defect.

**D18 (b) — power-strength correlation:** pristine C29 = 0.73;
staged D18 = 0.91. +0.18 into strong-positive. One model
everywhere.

**D18 (c) — clamp pins:** 3 total across 292 fighters (~1.0%,
under the 5% wall-effect threshold). Healthy.

**D18 (d) — G2 separability re-check, N=1000, all-70 baseline.**
D18 must not break C23's D7 finding.

| | share | Δ vs baseline | 2SE |
|---|---:|---:|---:|
| pristine baseline | 93.70% | — | ±1.54pp |
| pristine POWER+20 | 95.60% | **+1.90pp** | ±1.30pp |
| pristine STRENGTH+20 | 94.10% | +0.40pp | ±1.49pp |
| staged baseline | 95.00% | — | ±1.38pp |
| staged POWER+20 | 96.60% | **+1.60pp** | ±1.15pp |
| staged STRENGTH+20 | 95.10% | +0.10pp | ±1.37pp |

**D18 does NOT break D7 directionally.** POWER moves the KO+TKO
channel more than STRENGTH does on both arms; STRENGTH stays flat
within 2SE. Saturation caveat: all-70 baseline is at ~95% KO+TKO
share, so 2SE bounds overlap between POWER+20 and STRENGTH+20 —
this is a directional preservation check, not a stat-sig
discrimination. A less-saturated baseline is needed for P5-C's
clean magnitude read.

**BF-2 FIXED IN-SCOPE.** `core/types.py POWER_STYLE_OFFSET` gained
two dispatch-spelling aliases with comment block explaining why:
- `'Ground & Pound': +3` (alias of canonical `'Ground and Pound'`)
- `'Striker': +4` (alias of enum-key `'STRIKER'`)

`generate_style_for_fighter` and the `world_init.py:1078` fallback
list dispatch these display strings that differed from the
canonical PSO entries by punctuation only. Aliases inherit
canonical values so every dispatched string resolves. Grep-
verified post-fix: seed 995600's Ground & Pound cell landed at
mean 61.64 (target ~+3 offset territory); Striker at 59.95
(target ~+4).

**BF-1 FINDING (filed, ship queued as STYLECOHERENCE1).**
`getattr(fighter, 'fighting_style', ...)` at **four**
`world_init.py` sites reads NOTHING — GeneratedFighter's attribute
is `.style` (assigned at world_init.py:1115), not
`.fighting_style`:
1. `world_init.py:3058-3060` — C25 mechanism: `record.fighting_style
   = str(getattr(fighter, 'fighting_style', '') or '')` writes '' on
   every fresh fighter. **The C25 stamp has been dead-in-write
   since C25 shipped.** (Cross-check with C25/C27 KEEP ruling:
   those measurements were reading the bridge-side pipeline —
   `game_bridge.py:2340-2346` runs per-fid seeded random assignment
   AFTER world_init and BACKFILLS `record.fighting_style` from
   that, overwriting world_init's empty stamp. The C25 promotion
   works via the bridge backfill, not via world_init's stamp.
   C25 KEEP ruling stands as-was; BF-1 is a distinct pre-C25
   bug that C25 was designed to fix but the write side never
   worked.)
2. `world_init.py:3128` — style-based clinch_control bonus. Never
   applied.
3. `world_init.py:3142` — style-based training modifier. Never
   applied.
4. `world_init.py:2802-2803` — style census counter. Always empty
   (guard `if getattr(...) is not None` evaluates falsy on '').

**In scope for P5-B1**: D18's own site fixed (formula needs the
style access). Sibling sites left untouched — separate ship.

**STYLE-COHERENCE MEASUREMENT (entry gate for STYLECOHERENCE1).**
Fresh world seed 995700 THROUGH `bridge.new_game` (production
population rule; equivalence-gate standing rule). For every AI
fighter compared:
- (a) `world.fighters[fid].style` — style he was BORN with
- (b) `record.fighting_style` after bridge backfill — style he
  PLAYS with
- (c) `_fighter_data['style']` — bridge cache

| | count | share |
|---|---:|---:|
| population n | 285 | — |
| world_init.style present (a) | 285/285 | 100.0% |
| record.fighting_style present (b) | 285/285 | 100.0% |
| _fighter_data['style'] present (c) | 285/285 | 100.0% |
| **a↔b (born vs played) match** | **29/285** | **10.2%** |
| b↔c (played vs cache) match | 285/285 | 100.0% |
| a↔c (born vs cache) match | 29/285 | 10.2% |

**Mismatch rate 89.8% (256/285).** Consistent with 1/11 uniform-
random matching (1/11 = 9.1%). The bridge picks a style at random
per-fid AND world_init picks a style, and they agree by chance in
~1/11 cases. **Fighters play under styles that are 89.8%
DIFFERENT from what world_init built them as.**

**Consequence for the BF-1 sibling-fix decision**: fixing site 1
(the record.fighting_style stamp) is NOT safe/cosmetic. It moves
89.8% of the AI roster from bridge-random styles to world_init-
born styles. That's a substantive live-behavior change — the
"aggregate" and "distinctive" style patterns that world_init
generates (country-biased, style-family-informed) would ACTUALLY
reach the play surface for the first time since C25. STYLECOHERENCE1
inherits this measurement as its defining problem and needs its
own measurement pass on downstream effects (rankings, matchmaking
patterns, coach interactions, gameplan resolution rates).

Top 5 mismatch examples (seed 995700 second run):

| fid | born_style | played_style | fdata_style |
|---|---|---|---|
| dad1b5a8 | Wrestler | Sprawl & Brawl | Sprawl & Brawl |
| 7c2787fb | Ground & Pound | Striker | Striker |
| ddfc6db8 | BJJ Specialist | Pressure Fighter | Pressure Fighter |
| 174e8fc7 | Pressure Fighter | BJJ Specialist | BJJ Specialist |
| b8bd8172 | Wrestler | Pressure Fighter | Pressure Fighter |

Played-style distribution per BORN-style (seed 995700 second run,
same output file):
- BORN BJJ Specialist (n=35): Sprawl & Brawl=6, BJJ Specialist=5, Wrestler=5
- BORN Wrestler (n=43): Counter Striker=7, Sprawl & Brawl=6, Muay Thai=6
- BORN Ground & Pound (n=24): Wrestler=8, Striker=5, Balanced=2
- BORN Striker (n=53): Striker=11, Muay Thai=7, Sprawl & Brawl=7
- BORN Muay Thai (n=29): Wrestler=5, Sprawl & Brawl=5, Striker=4
- (etc — full distribution in `outputs/sm1/fight_model/p3_5/p5b1/style_coherence_out.txt`)

BF-1's siblings 2 (clinch_control bonus), 3 (training modifier),
and 4 (style census) are broken by the SAME `getattr(fighter,
'fighting_style', '')` bug and pass silently for the same reason
they've passed since C21/C23. Fixing them ALSO activates real
behavior (clinch_control bonus starts applying at world-gen,
training modifiers start being style-informed). All four sites
belong to STYLECOHERENCE1; ship discipline holds P5-B1 to its
scoped concerns.

**STYLECOHERENCE1 filed to post-arc queue** (see scope doc,
POST-ARC DOCKET QUEUE) with this coherence measurement as the
entry gate. Prerequisite: consumer census (rankings, matchmaking,
coach interactions, gameplan patterns) BEFORE fix. Instrument-
before-fix, per standing rule.

Full report: `outputs/sm1/fight_model/p3_5/p5b1/report.md`.
Artifacts under `outputs/sm1/fight_model/p3_5/p5b1/`: census.md,
d17_readings.py + JSON (staged + pristine), d18_readings.py + JSON
(staged + pristine + staged_bf2), style_coherence_probe.py +
style_coherence_out.txt.


### FIGHT MODEL STYLECOHERENCE1 [COMMITTED as C31, 2026-09-05]

Born styles reach the play surface. World-init's country/stat-
informed style generation now flows through to `_resolve_gameplan`,
style windows, counter mechanics, scout reports — every play-time
consumer surface. Promoted from post-arc queue by Van's P5-B2 paste.
S2 freeze holds — NO DEPLOY.

**THE FIX (three parts, forward-only).**
- **T2 (a) — world_init sites 1 + 4 (attribute-read fix, no
  gating).** `world_init.py:3070` (C25 record.fighting_style
  stamp) + `:2801-2807` (style census counter): `getattr(fighter,
  'fighting_style', '')` → `getattr(fighter, 'style', '')`.
  GeneratedFighter's actual attribute is `.style` (line 1115);
  the pre-fix reads returned '' every time.
- **T2 (b) — the coherence fix at `game_bridge.py:2336-2352`.**
  Bridge backfill now reads `record.fighting_style` FIRST
  (populated post-fix by world_init); falls back to per-fid seeded
  random ONLY when the record field is empty (legacy saves +
  defensive). Dropped the pre-P5-B2 `_frec.fighting_style ==
  "Balanced"` special case — under STYLECOHERENCE1 Balanced is a
  real world-init pick, not a placeholder to overwrite. Forward-
  only per Van: legacy saves keep their currently-played styles
  because they hit the outer `if "style" not in _fdata:` guard.
- **T2 (c) — sites 2 + 3 (attribute fix + flag gating).** Added
  `window_registry.py`:
  - `STYLE_CLINCH_BONUS_ENABLED: bool = False` (world_init:3159
    — clinch_control bonus for Clinch Fighter / Muay Thai / Judo
    / Sambo / Wrestler / Pressure Fighter)
  - `STYLE_TDD_BONUS_ENABLED: bool = False` (world_init:3183 —
    takedown_defense bonus for Muay Thai / Sprawl & Brawl / Karate)
  Both blocks fix the getattr and short-circuit to `_bonus = 0`
  under flag OFF (runtime-flip propagation pattern per C22
  CHIN/COMP/POWER wiring).

**BURIED FINDING CHAIN — now three deep.**
1. **C25 stamp dead-in-write since C25 shipped** (BF-1 site 1).
   `record.fighting_style` was stamped as `''` on every fresh
   fighter because the getattr targeted an attribute the source
   object never had. The C25 promotion ledger (record.fighting_style
   as a real field) was correct; the write path was broken from
   day one. C27's KEEP ruling still stands — it measured the
   bridge-side pipeline (`game_bridge.py:2336-2347`), not
   world_init's stamp.
2. **Bridge random deal masked the write bug** (P5-B1 measurement).
   Because world_init's stamp wrote '', the bridge backfill saw
   an empty record and used its own per-fid-seeded random pick.
   Fighters played under styles ~89.8% different from what
   world_init built them as (10.2% match = 1/11 uniform-random
   coincidence rate). AI gameplans dispatched on the random
   played style, not the born style.
3. **`_dominant_coach_type` always returns `boxing_coach`**
   (BF-1 site 4). The style census counter was reading the same
   broken getattr → Counter stayed empty → fallback triggered
   at `world_init.py:2796-2809` returned `"boxing_coach"`
   unconditionally. Every camp received a boxing coach regardless
   of style mix. Fixed here — but the ripple is bounded by (4).
4. **Coach system silent-fail in production** (documented at
   CLAUDE.md "PA silent-fail feature losses"): `from
   systems.coaches import CoachSystem` fails on PA because
   `systems` resolves to `cage_dynasty_web/systems/` stub. So
   world_init's `COACHES_AVAILABLE=False` and the coach block
   never runs. **Site 4's fix is functionally dormant in
   production** until systems.coaches import is unblocked by a
   separate ship. Defensive correctness lands here; the actual
   coach-fits-style ripple activates in a future world where
   COACHES_AVAILABLE=True.

**GATES.**

*G1 COHERENCE — seed 997000 through bridge.new_game.*

| metric | pre-P5-B2 (C30) | staged P5-B2 |
|---|---:|---:|
| n_ai_fighters | 285 | 278 |
| **born-vs-played match** | **10.2%** | **100.00%** (278/278) |
| played-vs-cache match | 100.0% | 100.0% |

**G1 PASS.** Zero mismatches. Born distribution equals played
distribution byte-identically.

*G2 LEGACY SAFETY — synthetic legacy-shaped states.*

| path | n | unchanged | mutated |
|---|---:|---:|---:|
| A (`_fdata['style']` cached) | 50 | 50 | 0 |
| B (record populated, cache absent) | 50 | 50 | 0 |

**G2 PASS.** Path A hits the outer `if "style" not in _fdata:`
guard and skips the whole block. Path B reads
`record.fighting_style` and uses it without rerolling. Forward-
only proven.

*G3 FLAG INERTNESS — sites 2 + 3 flags OFF.*

EP1_200 hand-built fight outcomes MD5:
- pristine C30: `9238a179ba2d0424752b76f45ae63410`
- staged (flags OFF): `9238a179ba2d0424752b76f45ae63410` ✓

**G3(a) PASS — MD5 IDENTICAL.** Fight-engine behavior byte-
identical.

Fresh-world attribute distributions (seed 997250, N=276):

| stat | pristine md5 | staged md5 | match |
|---|---|---|---|
| clinch_control | `60259f45...` | `60259f45...` | ✓ |
| takedown_defense | `0395a8b6...` | `0395a8b6...` | ✓ |
| strength | `86d75d7e...` | `86d75d7e...` | ✓ |
| power | `0d41f312...` | `d9390db3...` | ✗ (Δ=+0.0072 mean) |

**G3(b) PASS with root-cause correction.** Sites 2+3 (flag-gated
bonuses) MD5-identical — confirmed inert. Strength MD5-identical
— generation stage clean.

The power MD5 difference was initially hypothesized to be site 4's
coach-fits-style ripple. **Falsified by two follow-up
measurements this session:**
- **staged vs itself** (same code, two runs): power MD5 differs
  (`d9390db3...` vs `bd0a14c4...`), mean differs by 0.036 —
  LARGER than the staged-vs-pristine 0.007. Power derivation
  depends on RNG state at persist-time, which is downstream of
  uuid.uuid4() nondeterminism (per CLAUDE.md's "same-seed
  measurements have never been reproducible" filing). This is
  a noise floor artifact, not a mechanism-driven ripple.
- **Coach system loading**: both trees show `Coaches: 0` under
  the P5-B2 probe environment (staged AND pristine), matching
  PA production's `COACHES_AVAILABLE=False` state. Site 4's
  code path is DEAD in both arms. It cannot cause the delta
  because it doesn't fire.

Root cause of the delta: measurement noise (uuid-nondeterminism
propagating through world-init RNG order). Site 4's fix is
defensively correct but functionally dormant until a separate
ship unblocks `systems.coaches` import.

*Coach distribution measure* (seed 997500, both trees, through
`bridge.new_game`):

| arm | 40-camp coach-type distribution | verdict |
|---|---|---|
| pristine C30 | 40 × NONE (empty-counter fallback dormant) | dormant |
| staged P5-B2 | 40 × NONE (empty-counter fallback dormant) | dormant |

Van's spec anticipated PATHOLOGICAL vs SANE with SANE required
to proceed. Actual verdict: **DORMANT in this environment** —
the coach path doesn't fire at all. Van's accept-A ruling holds
trivially: with no ripple to accept, the fix commits under the
"defensively correct, functionally-dormant-until-systems-coaches-
loads" reading.

*G4 BEHAVIOR READING — banked for P5-C, not judged here.*
Fixed-card AI-vs-AI, N=300 pairs, seeds 997400+.

Method mix (per 300 fights):
| bucket | pristine | staged | Δ |
|---|---:|---:|---:|
| KO | 4 | 2 | −2 |
| TKO | 198 | 213 | +15 |
| SUB | 44 | 34 | −10 |
| DEC | 50 | 48 | −2 |
| DRAW | 4 | 3 | −1 |

AI plan preset census (600 fighter-slots):
| preset | pristine | staged | Δ |
|---|---:|---:|---:|
| AGGRESSIVE | 179 | 198 | +19 |
| TAKEDOWN | 77 | **117** | **+40** |
| BALANCED | 26 | 70 | +44 |
| CLINCH | 108 | 59 | **−49** |
| DEFENSIVE | 43 | 12 | −31 |
| MEASURED | 37 | 9 | −28 |
| SUBMISSION | 80 | 81 | +1 |
| GNP | 50 | 54 | +4 |

Per-style SUB-attempts/fight (coherent wrestlers visibly wrestle):
| style | pristine | staged |
|---|---:|---:|
| BJJ Specialist | 1.69 | 1.37 |
| **Wrestler** | **0.25** | **0.74 (+195%)** |
| Balanced | 0.17 | 0.61 |
| Ground & Pound | 0.50 | 0.45 |

Per-style finish rate:
| style | pristine | staged | Δ |
|---|---:|---:|---:|
| **Wrestler** | **72.8%** | **85.7%** | **+13pp** |
| Sprawl & Brawl | 89.8% | 97.2% | +7pp |
| BJJ Specialist | 92.3% | 75.8% | **−16.5pp** |
| Ground & Pound | 86.0% | 73.8% | −12pp |
| Counter Striker | 86.0% | 75.0% | −11pp (n=12) |
| Pressure Fighter | 84.0% | 75.7% | −8.3pp |
| Muay Thai | 87.5% | 91.3% | +4pp |
| Striker | 86.9% | 87.2% | +0.3pp |
| Balanced | 82.9% | 82.9% | 0.0pp |
| Clinch Fighter | 79.4% | 72.7% | −6.7pp |
| Point Fighter | 85.3% | 100.0% | +14.7pp (n=9) |

Coherent Wrestlers finish +13pp more, attempt subs ×3 more.
Ground & Pound / Pressure Fighter drop ~10pp — striking-heavy
dispatch dilutes under coherence, filed as P5-C dial input. The
BJJ Specialist −16.5pp drop is a P5-C sub-finish-rate dial
target — coherent BJJ specialists are stat-thinner than the
bridge-random-picked ones were.

*G5 PLAYED-STYLE DISTRIBUTION — fresh-universe flavor change is
intentional world-gen design reaching the surface.*

| style | pristine (bridge uniform) | staged (world-init informed) |
|---|---:|---:|
| Wrestler | 36 | 50 |
| Striker | 33 | 46 |
| Pressure Fighter | 37 | 38 |
| Balanced | 15 | 36 |
| BJJ Specialist | 32 | 36 |
| Ground & Pound | 25 | 25 |
| Muay Thai | 23 | 24 |
| Sprawl & Brawl | 16 | 14 |
| Point Fighter | 16 | 6 |
| Counter Striker | 23 | **5** |
| Clinch Fighter | 27 | **3** |

Bridge weights (`14,8,10,9,12,9,10,8,6,7,7`) → flat-ish uniform.
Post-STYLECOHERENCE1: world_init's country/stat-informed
generation clusters heavier around Wrestler / Striker / Pressure
Fighter / Balanced / BJJ Specialist. Clinch Fighter crashes 27→3
and Counter Striker 23→5 — matching world_init's design intent
(rarer archetypes in real MMA populations).

**RIDERS.**
- **BF-1 site 3 naming correction**: P5-B1 filing labeled site 3
  as "training modifier"; the actual code is a world-gen
  takedown_defense bonus. Flag named `STYLE_TDD_BONUS_ENABLED`
  for accuracy; corrected in the code comment.
- **STYLE-DEAD1 independence**: the outcome-layer style-flip
  mechanism at `game_bridge.py` remains dead-in-write per the
  CLAUDE.md STYLE-DEAD1 filing (constructor value-lookup on
  enum-name string). Coherent styles do NOT activate the
  style_mod branch. Independent ship if Van wants it fixed.
- **Sites 2+3 flag flips are Van rule (a)** (no wiring-flag flips
  without a defining-instrument sensitivity reading in a prior
  verify pass). P5-C or later ships their own before/after
  readings on clinch/tdd bonus effects.
- **Bridge "Balanced" special-case retired**: pre-P5-B2 code
  treated `record.fighting_style == "Balanced"` as empty and
  re-rolled. Under STYLECOHERENCE1 Balanced is a real
  world-init pick (~16% of the pool per G1 born distribution);
  keeping the special case would incorrectly mangle real
  Balanced fighters into other styles.
- **UI safety**: every display consumer (12 templates + 3
  narrative sites) reads through `record.fighting_style` or
  `_fdata['style']`; both now populated with the coherent style.
  No template changes required.
- **Site 4 dormancy**: functionally dormant until
  `systems.coaches` import unblocked on both dev harness and
  PA production. The defensive fix commits here for correctness
  and future-proofing; the actual coach-fits-style ripple
  activates when a separate ship enables COACHES_AVAILABLE=True.

Full report: `outputs/sm1/fight_model/p3_5/p5b2/report.md`.
Artifacts under `outputs/sm1/fight_model/p3_5/p5b2/`: census.md,
g1_coherence.py + JSON, g2_legacy_safety.py, g3_flag_inert.py +
JSON (staged + pristine + staged_run2), g4_g5_behavior.py + JSON
+ txt (staged + pristine), coach_measure.py + JSON (staged +
pristine), report.md.


### FIGHT MODEL P5-B3 [COMMITTED as C32, 2026-09-05]

Structural flip pack. Four `window_registry.py` flags moved from
False → True (cuts writer, sprawl-punish, aggression rules, IQ
execution). No dial moves — magnitudes stay P5-C's per Van
directive. S2 freeze holds — NO DEPLOY.

**FLAGS ON (rule (a) basis per flag).**
- `FI_CUT_WRITER_ENABLED: True` — C21 shipped-dark writer + P5-A
  F11 carve-out at `fight_engine.py:719-722` + fi between-round
  cut check at `fight_integration.py:2266-2278` + P5-B3 wiring-
  verify trace end-to-end + cut readings (below).
- `FI_SPRAWL_PUNISH_ENABLED: True` — C21 shipped-dark
  `_sprawl_counter` consumer at `fi:1395-1403` + C21 fire-rate
  measurement (10.5% of fights, Δwin=0 at ×1.25 provisional).
- `FI_AGGRESSION_RULES_ENABLED: True` — C24 4e Gates G2/G3 + P3-5
  item 11 STEP 0 measurement + P5-B3 R3 hurt-signal fix + 5
  collision-proof hook renames + post-flip readings (below).
- `FI_IQ_EXECUTION_ENABLED: True` — C24 4e Gate G3 ALIVE reading
  (IQ 50 drifts 7.8% of fights vs IQ 90 drifts 0.0%) + P5-B3
  post-flip readings.

**WIRING-VERIFY TRACE (cuts, end-to-end).**

1. **WRITER** at `fight_integration.py:1468-1482`:
   ```python
   if _wreg.FI_CUT_WRITER_ENABLED and target_area == "head":
       _st_val = strike.value or str(strike)
       if _st_val in _CUT_ELBOW_STRIKES:
           _cut_chance = _CUT_BASE_CHANCE + attacker.strength / _CUT_STR_DIV
           if random.random() < _cut_chance:
               defender_state.damage.cuts += 1
               _win(self, "elbow_cut_writer", "write", ...)
   ```
   `CUT_ELBOW_STRIKES` = 6 elbow variants
   (`window_registry.py:108-112`).

2. **ACCUMULATOR** — `defender_state.damage.cuts: int` on the
   `BodyPartDamage` dataclass (`fight_engine.py:764`).

3. **TWO CARVE-OUT CONSUMERS**, both flag-gated:
   - (a) **P5-A F11** at `fight_engine.py:719-722` inside
     `check_stoppage(is_between_round=True)`:
     `if cuts >= FINISH_CUT_STOP_THRESHOLD: return "TKO
     (Doctor Stoppage - Cuts)"`.
   - (b) **fi between-round check** at
     `fight_integration.py:2266-2278`: independent probability
     `min(_CUT_DOC_MAX, (cuts - (thr-1)) * _CUT_DOC_STEP) *
     max(_CUT_DOC_HEART_FLOOR, 1 - heart/_CUT_DOC_HEART_DIV)`.

**Wired end-to-end.** Both consumers emit
`"TKO (Doctor Stoppage - Cuts)"`.

**SPRAWL-PUNISH WIRING** at `fight_integration.py:1395-1403`:
```python
if (_wreg.FI_SPRAWL_PUNISH_ENABLED
        and getattr(attacker_state, '_sprawl_counter', 0) > 0):
    damage *= _SPRAWL_PUNISH_MULT  # = 1.25 provisional
```

**CUT READINGS (banked, not judged).** EP1_500 fixed-card
hand-built pairs, seed 998000+, and POP_200 varied-attribute
fixture, seed 998600+.

| pack | cuts opened mean/fight | cut stoppages (% fights) | cut stoppages (% TKOs) | TKO count |
|---|---:|---:|---:|---:|
| EP1_500 staged (flags ON) | **3.638** | **9.20%** (46/500) | 10.48% | 439 |
| EP1_500 pristine C31 (OFF) | 0.000 | 0.00% | 0.00% | 446 |
| POP_200 staged (flags ON) | **5.100** | **15.00%** (30/200) | 20.41% | 147 |
| POP_200 pristine C31 (OFF) | 0.000 | 0.00% | 0.00% | 139 |

**HOT by 3-5× vs Van's P5-C anchor** ("stoppage 1-3% of fights").
P5-C dials named: `CUT_BASE_CHANCE` (currently 0.25),
`CUT_STR_DIV`, `FINISH_CUT_STOP_THRESHOLD` (currently 2),
`_CUT_DOC_MAX`, `_CUT_DOC_STEP`, `doctor_check_cut_threshold`.
Filed to P5-C. **No dial moves here.**

**R3 HURT-SIGNAL FIX** at `fight_integration.py:827-841`. R3
(opponent gassed) now requires: `opponent stamina ≤ 25 AND round
≥ 2 AND (opponent rocked OR opponent knockdowns_this_round > 0)`.
Pre-fix step0 measured R3 firing at ~45-51% on symmetric-cardio
fixtures — stamina threshold alone too permissive. Structural
change only.

**5 COLLISION-PROOF HOOK LINE RENAMES.** Pre-fix R1 "knows they
need a finish" and R3 "smells blood" collided with
`narrative/commentary.py` corpus (lines 901, 1589, 1887, 3880).
All 5 rewritten with grep-verified unique tokens (zero substring
collisions against `narrative/*.py` + `cage_dynasty_web/*.py`):

| rule | new line (collision-proof) |
|---|---|
| R1 | "{name} enters must-win minutes and cranks the output." |
| R2 | "{name}'s corner calls for tactical distance against the puncher." |
| R3 | "{name} reads the gas tank and steps up the tempo." |
| R4 | "{name} banks the scorecard and manages the remaining minutes." |
| IQ-drift | "{name} discards the game plan on instinct, throwing bombs." |

Step0 Finding #2 ("smells blood false-positives ambient
commentary") **closed** for these 5 hooks.

**SUB-ATT COMPRESSION — DESIGN-CORRECT ARITHMETIC (NOT WIRING).**
Traced to `fight_engine.py:2386-2401`:
```python
if gameplan is not None:
    _agg = int(getattr(gameplan, 'aggression', 0) or 0)
    if _agg > 0:
        strike_weight = int(strike_weight * (1.0 + 0.08 * _exec))
    elif _agg < 0:
        strike_weight = int(strike_weight * (1.0 - 0.05 * _exec))
```

AGGRESSION dial only modifies `strike_weight`. Comment at
`fe:2375-2382` confirms design intent: "aggression only shifts
strike output; grapple/sub bias is RANGE dial's territory". Under
`aggr=+1`, `strike_weight` scales up ×1.08 → pie total
(strike+grapple+sub) grows → `P(sub) = sub/total` shrinks as
arithmetic consequence. **Not a wiring error.** Filed to P5-C
(magnitude dial: increase RANGE tilt for grapple/sub, OR decrease
AGGRESSION strike-scale factor). Code UNTOUCHED per Van.

**POST-FLIP READINGS (banked, not judged).** Fixed-card AI-vs-AI,
N=300, through `bridge.new_game` (production population;
coherent styles from C31).

Plan preset census (600 fighter-slots — **arm-invariant** because
`ai_gameplan_for_style` selects preset from style, and both arms
have coherent styles post-C31; aggression rules layer on top):

| preset | pristine C31 | staged | Δ |
|---|---:|---:|---:|
| AGGRESSIVE | 109 | 112 | +3 |
| SUBMISSION | 49 | 47 | −2 |
| TAKEDOWN | 46 | 47 | +1 |
| BALANCED | 43 | 42 | −1 |
| GNP | 23 | 23 | 0 |
| CLINCH | 15 | 13 | −2 |
| MEASURED | 4 | 6 | +2 |
| DEFENSIVE | 4 | 4 | 0 |

R1-R4 + IQ-drift fire counts (600 slots):

| rule | staged fires | %-slots |
|---|---:|---:|
| R1 (behind, final rd) | 53 | **8.83%** |
| R2 (chin vs power) | 46 | **7.67%** |
| **R3 (gassed + hurt)** | **0** | **0.00%** |
| R4 (cruising, lead) | 0 | 0.00% |
| IQ drift (rocked) | 4 | 0.67% |

**R3 OVERCORRECTION ANALYSIS.** Pre-fix ~45-51% → post-fix 0%.
Van's spec expected 10-20% band; the AND-composition of stamina
+ round-gate + hurt-signal is too restrictive on symmetric-AI-vs-
AI 3R fixtures: opponents rarely reach simultaneously
`stamina ≤ 25` AND `round ≥ 2` AND `(rocked OR knockdowns_this_round
> 0)`. **Three P5-C loosening candidates (dial choice, no code
here):**
1. Loosen stamina threshold to `≤ 35` or `≤ 40` (currently 25).
2. Broaden hurt signal to `opponent health < critical_line`
   instead of rocked/KD (more surface area to trip).
3. **OR** the hurt signal with a lower stamina threshold instead
   of **AND**-ing (fires on either gas-out OR hurt separately),
   preserving the "smells blood" narrative on either signal.

**R4 also 0%** — cruising-with-lead needs a lead-building
fixture (asymmetric-cardio or live-play). R4 mechanism wired;
fire-rate measurement inconclusive on this fixture.

Method mix (N=300):

| bucket | pristine C31 | staged | Δ |
|---|---:|---:|---:|
| KO | 4 | 6 | +2 |
| TKO | 213 | 231 | +18 |
| SUB | 37 | 31 | −6 |
| **DEC** | **45** | **29** | **−16** |
| DRAW | 1 | 3 | +2 |

DEC drops −16 under staged (more decisive fights); TKO rises +18
(cuts stoppages + aggression tilt pushing toward finishes); SUB
drops −6 (compression + earlier TKO endings displacing SUB
opportunities).

Per-style SUB-attempts/fight (compression visible across grappler-
side styles as diagnosed above):

| style | pristine | staged |
|---|---:|---:|
| BJJ Specialist | 1.51 | **0.86** |
| Ground & Pound | 0.75 | **0.32** |
| Wrestler | 0.57 | 0.49 |
| Balanced | 0.25 | 0.12 |
| Pressure Fighter | 0.20 | 0.12 |
| Muay Thai | 0.19 | 0.06 |
| Sprawl & Brawl | 0.06 | 0.10 |
| Striker | 0.05 | 0.07 |
| Counter Striker (n=6) | 0.00 | 0.50 |
| Point Fighter | 0.00 | 0.00 |

Per-style finish rate (all up under staged):

| style | pristine | staged | Δ |
|---|---:|---:|---:|
| Sprawl & Brawl | 83.8% | 94.0% | +10.2pp |
| BJJ Specialist | 83.3% | 88.9% | +5.6pp |
| Ground & Pound | 83.3% | 89.4% | +6.1pp |
| Wrestler | 86.2% | 90.9% | +4.7pp |
| Muay Thai | 78.4% | 82.4% | +4.0pp |
| Pressure Fighter | 86.2% | 88.8% | +2.6pp |
| Balanced | 80.7% | 83.3% | +2.6pp |
| Striker | 90.1% | 91.9% | +1.8pp |
| Counter Striker (n=6) | 83.3% | 100.0% | +16.7pp |
| Point Fighter (n=5→11) | 80.0% | 100.0% | +20.0pp |

**G0 PRE-FLIP SANITY — MD5 IDENTICAL** with all four flags forced
OFF at runtime on staged tree. EP1_200 (seeds 998000+):
- pristine C31 (flags OFF on disk): `684a4ce1b5287a87be862fced9e980e4`
- staged (flags forced OFF at runtime): `684a4ce1b5287a87be862fced9e980e4`

Confirms R3 hurt-signal fix + 5 hook renames byte-inert when
flags OFF (early-return guards preserve structural inertness).

**RIDERS.**
- **Sprawl-punish fire-count instrument LIMITED by
  `WINDOWS_LOG_ENABLED`.** Cuts+sprawl reading arm didn't enable
  it; aggression arm did enable it but only R1-R4/IQ-drift
  substring probes were wired. Sprawl-punish `_win()` dispatch
  requires either `log_window_event` inspection or a monkey-patch
  on `_win` to capture fire count. P5-C should measure sprawl-
  punish fire rate + Δwin with a proper probe **before** tuning
  its magnitude (`SPRAWL_PUNISH_DAMAGE_MULT = 1.25` provisional).
- **Step0 Finding #2 CLOSED** for the 5 renamed hook lines. Other
  collision-prone commentary lines elsewhere in the codebase are
  out of scope; grep audit for future window hooks should stay
  standard.
- **Cut anchor 1-3% is a REAL MMA target, not a fixture-artifact
  overshoot** — the 9-15% observed here is a real magnitude issue
  that needs dial reduction at P5-C.
- **R4 mechanism un-measurable on symmetric fixture** — flag ON is
  safe (fires 0 → no behavior perturbation on this pool), and
  live-play with asymmetric matchups may produce fire events. Do
  not conclude R4 is dead — conclude it needs a lead-differential
  fixture to measure.
- **Sub-att compression is DESIGN-CORRECT** — not scoped as a
  wiring fix. If Van wants coherent grapplers to actually attempt
  more subs, P5-C should either bump RANGE tilt (grapple ×1.20,
  sub ×1.10 → higher) or damp AGGRESSION strike-scale (×1.08 →
  smaller).

Full report:
`outputs/sm1/fight_model/p3_5/p5b3/report.md`. Artifacts under
`outputs/sm1/fight_model/p3_5/p5b3/`: `g0_flags_off_ep1.py` +
JSON (staged_flags_off + pristine_c31), `g_cuts_sprawl_readings.py`
+ JSON (staged_flags_on + pristine_c31_flags_off),
`g_aggression_readings.py` + JSON (staged_agg_on +
pristine_c31_off), report.md.


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

**⚠️ SUPERSEDING NOTE — 2026-07-20:** the "per this file's KEY CONSTANTS"
citation above was documented-was-inherited-false. KEY CONSTANTS itself
was falsified by STAGE 0d (`ba8cece`, 2026-07-12) — see the superseding
correction under `## Key constants` above. At HEAD, FI DOES read
`self.config.damage_multiplier` in the strike-damage path (currently
`fight_integration.py:867`), and no `FI_DAMAGE_MULTIPLIER` module const
exists in the engine files. The consequent claim "numbers below at
effective 0.48, not 0.24" still holds — what changed is the mechanism
(`FightConfig.damage_multiplier` dataclass field now, `FI_DAMAGE_MULTIPLIER`
module const before), not the effective value.

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
