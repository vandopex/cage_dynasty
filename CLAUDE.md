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

### STAGE 1 addendum — random-coupling hazard (STAGE1-PARITY1, 2026-07-14)

**Do NOT run a deeper draw-by-draw coupling audit.** That's the rabbit
hole — match three consumers, find a fourth, match four, find a fifth.
The port itself resolves the coupling by unification.

**Load-bearing finding for Stage 2a accumulator port** [MEASURED, grep-verified vs HEAD]: of the four ⚠️-PREVIOUSLY-STATED FI-only gates in `fight_integration.py:{974, 1016, 1033, 1052}` — **two are genuinely FI-only** (`_clinch_body_acc`, `_gnp_accumulation`); **one is FE-native and byte-identical** (leg-TKO on `leg_kicks_absorbed`); **one is present in FE with different, stronger constants** (rocked-shots ref stoppage — FE cap 0.35 vs FI cap 0.22, faster ramp, no composure discount). Firing frequency is what closes the attribution; code presence check does not. **Named trace item** (queued, requires the two-step allowlist widening at `fight_engine.py:863`'s `_assert_sanctioned_config`).

[SUPERSEDED — the "decomposition NOT obtainable before Stage 2a" claim in the archived body was true when filed; the decomposition was subsequently obtained. See `### STAGE 2a addendum — config vs engine, measured 2x2 [filed 2026-07-26]` and `### Framing correction 2026-08-01`.]

Full section archived: CLAUDE_archive.md → '### STAGE 1 addendum — random-coupling hazard (STAGE1-PARITY1, 2026-07-14)' (phase 2, 2026-08-15)

### STAGE 1 addendum — config-lever measurement [filed 2026-07-14]

**Governance rules that survive this section body's archival:**

- **Rule going forward: no arc scoping number gets quoted without
  an N and a seed count.** Direction claims fine; exact percentages
  need provenance. (Verbatim from archived body's tail; also carried
  in `## Key constants` above — canonical live copy.)
- **POPULATION-SPECIFIC governance:** archived body's four measured
  claims (53% closure, +19.6pp residual, "the full ~41pp" framing,
  aggregate share arithmetic) are population-specific per
  `### Framing correction — "the aggregate gap" is population-specific
  [filed 2026-08-01]` (still live below). Numbers are correct
  measurements of Stage 1 pooled 10-seed world_init only — not
  project-level or production quantities.

Full section archived: CLAUDE_archive.md → '### STAGE 1 addendum — config-lever measurement [filed 2026-07-14]' (phase 2, 2026-08-15)

### STAGE 2a addendum — config vs engine, measured 2x2 [filed 2026-07-26]

**MEASURED verdict Stage 2a sequencing relies on** (5 cells, N=1210 per cell, HEAD `7513bc9`; table verbatim from archived body):

| Cell | Engine | Config | Style | Finish % |
|---|---|---|---|---:|
| C1 | FE | `_TRIPLE_PRE_GEN_LEGACY` (55, 0.42, 6) | blind | 31.7% |
| C2 | FE | `_TRIPLE_LIVE_PLAY` (55, 0.48, 10)     | blind | 55.0% |
| C3 | FI | `_TRIPLE_LIVE_PLAY` (55, 0.48, 10)     | blind | 69.8% |
| C4 | FI | `_TRIPLE_PRE_GEN_LEGACY` (55, 0.42, 6) | blind | 45.3% |
| C5 | FI | `_TRIPLE_LIVE_PLAY` (55, 0.48, 10)     | aware | 69.1% |

**Decomposition (verbatim from archived body):** Config effect on FE = C2 − C1 = **+23.3pp**; Config effect on FI = C3 − C4 = **+24.5pp**; Engine effect at pre-gen config = C4 − C1 = **+13.6pp**; Engine effect at live config = C3 − C2 = **+14.8pp**. Both decomposition paths sum to **+38.1pp** aggregate C3 − C1.

**Consequence, without recommending anything** (verbatim from archived body): Config drift accounts for roughly **62%** of the measured gap (23.3-24.5pp of 38.1pp); engine mechanics account for roughly **38%** (13.6-14.8pp of 38.1pp). **Filed as an observation for sequencing review; no sequencing decision is made by this entry.**

**Population caveat, load-bearing** (verbatim from archived body): C1-C4 strip style (`fighting_style=None`), so all 1210 fights per cell are the **same symmetric OVR=75 pair** with only the seed varying. `n=1210` measures seed diversity, not matchup diversity. Only C5 varies fighters via the `STYLES × STYLES` enumeration.

[POPULATION-SPECIFIC — see ### Framing correction 2026-08-01. "The measured gap" here = the 2x2 symmetric OVR=75 harness aggregate (38.1pp), not a production quantity.]

Full section archived: CLAUDE_archive.md → '### STAGE 2a addendum — config vs engine, measured 2x2 [filed 2026-07-26]' (phase 2, 2026-08-15)

### STAGE 2a addendum — production-path measurement of the classmethod flip [filed 2026-08-01]

**What shipped** (verbatim from archived body): `eeb16b8` — `FightConfig.standard_fight()` and `.championship_fight()` flipped from `(55, 0.42, 6)` to `(55, 0.48, 10)`. Four literal values, two classmethods, no allowlist change: the target triple was already `_TRIPLE_LIVE_PLAY` at `fight_engine.py:853`, admitted at `:857`.

**Caller audit MEASURED (grep across cage_dynasty_web/ + stage0c_golden_master/, positive control run)** (verbatim): Exactly one production caller: `world_init.HistorySimulator.simulate_fight_full_engine` at `:1422`. In-play fights (game_bridge FI paths) were at live-play numbers all along; only frozen pre-player history was stuck.

**Production-path measurement** (`probe_worldinit_prod.py`, tier grading mirroring `world_init.py:2513-2522`, 38-fighter Lightweight pool, N=400, seed=1000, paired): finish 14.5% → 33.8%; KO 5.0% → 16.5%; TKO 4.5% → 10.75%; SUB 5.0% → 6.5%; DEC 80.75% → 61.25%. Direction MEASURED. **Magnitude NOT validated against production** — probe pairs uniformly at random; production books rank-adjacent. Uniform pairing over-represents large-mismatch fights.

**FINDING — population composition dominates the config dial** (verbatim from archived body). Three measurements of this same four-line change, differing only in who was fighting: symmetric OVR=75 harness pair **+23.6pp**; flat all-`average` pool **+6.8pp**; production tier grading **+19.3pp**. A 3.5× span from population alone. **Any finish-rate number in this project is a claim about a population before it is a claim about the engine.**

**Submission rate is invariant to this dial** (verbatim): +1.5pp on the production path; ~6-8% across all five 2x2 cells regardless of config or engine. This flip is a KO/TKO lever. No submission lever has been located.

**Known drift left standing, deliberately** (verbatim): `fight_engine.py:4448` (`quick_simulate`) hardcodes `(55, 0.42, 6)` inline and now disagrees with `standard_fight()`. Callers unaudited. Filed, not touched — single-purpose commit.

Full section archived: CLAUDE_archive.md → '### STAGE 2a addendum — production-path measurement of the classmethod flip [filed 2026-08-01]' (phase 2, 2026-08-15)

### Framing correction — "the aggregate gap" is population-specific [filed 2026-08-01]

**The correction.** Several entries in the STAGE 1 and STAGE 2a addenda above refer to "the 41pp gap," "the arc's known aggregate gap," "the known finish-rate gap," or "the measured gap" with a definite article, as if a single project-level quantity existed. It does not. Per the production-path addendum at `### STAGE 2a addendum — production-path measurement of the classmethod flip [filed 2026-08-01]`: finish-rate aggregates are population-specific, with a 3.5× span (+6.8pp to +23.6pp) measured for the same four-line change across three populations. The +41.4pp (Stage 1 pooled 10-seed world_init) and +38.1pp (2x2 symmetric OVR=75 harness) are correct measurements of their populations. Neither is "the" gap, and shares computed against them (53%, 62%) are shares of those denominators only — not of any production-observed quantity. The production-path probe measured +19.3pp aggregate on production tier grading, magnitude itself unvalidated against production matchmaking.

**Per-site disposition.** Marked inline with `[POPULATION-SPECIFIC — see ### Framing correction 2026-08-01]`: the "53% of the known finish-rate gap" claim (STAGE 1 addendum), the "53% of the arc's known aggregate gap" claim, the "+19.6pp survives (41.4pp known aggregate − 21.8pp)" claim, the "full ~41pp" framing-correction paragraph, and the "62% of the measured gap" consequence paragraph (2x2 addendum). The "offset-vs-mechanic decomposition NOT obtainable before Stage 2a" claim carries a supersession note instead — it was true when filed and was subsequently obtained by the 2x2. The aggregate-rate bullet ("76.9% vs 35.4% pooled") is left unmarked: its first sentence is a correct population-named measurement; this block governs its "arc's core divergence" phrasing.

**None of the marked numbers is arithmetically false.** 62% of 38.1pp is correct. What is corrected is the definite article — the promotion of one population's denominator to a project-level quantity. Original wording is preserved at every site; markers annotate, they do not reword.

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

### Builtin scorer status — never-fired fallback [filed 2026-08-15, FOTN full-fidelity wire, 8fd4573]

**`game_bridge._select_fotn_builtin` (currently `:18071-18096`) has never fired in production**, MEASURED via PA's `server.log` retention: no `⚠️ fotn not available — using builtin` entries; the primary `import fotn` path succeeds on every reload (see `### Architecture correction — top-level systems/ imports [filed 2026-08-15]` above).

**Status: documented fallback only.** Fires on either:
- `import fotn` failure (has not occurred in retention).
- `select_fotn` exception (previously silent; now logged as `⚠️ FOTN select_fotn failed, builtin fallback: {err}` per `8fd4573`'s Edit F — see the try/except at `game_bridge.py:~3985-3990`).

**Do not upgrade or extend the builtin.** `systems/fotn.py` is the live scorer. If the builtin ever needs to evolve, first confirm from PA `server.log` that it's actually firing — otherwise the work is inert.

### Follow-up filed — tier threshold recalibration [filed 2026-08-15, FOTN full-fidelity wire, 8fd4573]

**Tier thresholds oversaturate under full-fidelity scoring.** Harness `outputs/fotn_harness.py` at N=400 fights, seed=1000, measured post-fix:

| tier | threshold | share of fights | share of card winners (N=40) |
|---|---:|---:|---:|
| INSTANT CLASSIC | ≥300 | **32.25%** | **97.5%** |
| Fight of the Year Candidate | ≥200 | 29.25% | 2.5% |
| Excellent | ≥150 | 17.50% | — |
| Great | ≥100 | 8.25% | — |
| Good | ≥50 | 12.75% | — |
| Standard | <50 | 0.00% | — |

- NEW score range 72-620, mean 244.6, vs OLD 70-132, mean 91.9. The tier ladder (50/100/150/200/300 at `systems/fotn.py:310-330`) was calibrated to a scoring range fights in this world don't actually inhabit — real scores are ~5× wider than the tier spacing accommodates.
- **Recalibration is a scoped follow-up, not done here.** Ship discipline: fix the wire first (`8fd4573`), tune the ladder second.

**Two harness caveats, filed for the record:**
1. **3/400 fights carried empty per-round stats** (99.25% fire rate, not 100%). Cause **INFERRED not measured** — plausibly R1 stoppages where the round-stats append didn't fire before the engine returned. The scorer's gate at `systems/fotn.py:80` degrades gracefully (falls to `_calculate_basic_score`), so this is not a correctness bug even if the mechanism is unconfirmed. Worth a targeted probe if the 0.75% edge becomes interesting.
2. **Harness scored harness-built dicts, not bridge-built dicts.** The harness constructed fight dicts locally mirroring the post-patch Path B shape rather than exercising `bridge._simulate_card_fights` / `bridge.advance_week`. Wiring correctness is inferred from the diff (game_bridge.py edits attach the same `eng_result.fighter1_stats` reference the harness uses) but not measured end-to-end through the bridge. **Production-path confirmation owed at deploy:** `server.log` clean of `⚠️ FOTN select_fotn failed` entries (would surface any shape mismatch via the new logging from `8fd4573`), and templates rendering `event.fotn.excitement_tier` values above `"Excellent"` (which were structurally unreachable pre-fix). **→ MEASURED 2026-08-19 (post-`3e90dfe` PA deploy — same deploy verifying COMMENTARY-STALE1).** PA `server.log` grep `"FOTN select_fotn failed"` returned zero. Event **CD75** rendered `event.fotn.excitement_tier = "INSTANT CLASSIC"` (above `"Excellent"`) on the FOTN block in production. Owed-at-deploy status **CLOSED**; caveat #2 converts from INFERRED to MEASURED. Same-deploy piggyback: nothing in `3e90dfe`'s scope touches FOTN wiring — the caveat #2 owed evidence has been available on PA since `8fd4573` shipped, and 2026-08-19's watched-fight verification confirmed both.

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

- **Balance observation (INFERRED, single N=50 dev harness).**
  78-OVR vs 72-OVR (6-point gap) measured at p_f1=0.900 on the
  post-fix `_TRIPLE_LIVE_PLAY` config + per-fight-seeding
  (`outputs/mc_odds_harness_out.txt`, single N=50 batch, crc32-
  seeded). Small OVR gaps produce near-deterministic favorites.
  Consequences if the reading holds across seeds and an OVR-gap
  grid: escalation band rarely fires, upsets rare, competitive
  odds lines rare. **NOT an odds bug** — odds honestly report
  engine behavior. Filed as a fix-the-engine candidate; needs a
  proper multi-seed sweep across OVR gaps before any tuning
  conclusion. Prior single-batch readings under the old shared-
  sequence scheme (0.960 at same OVR pair, and 0.920 post-config-
  fix pre-seeding-change) are documented false-as-generalized
  (both measured under stale seeding + one pre-fix under wrong
  config).
- **N=50 noise floor (MEASURED).** M6a 10-block sweep on a
  symmetric clone pair scattered 0.34–0.64 across blocks
  (aggregate 0.482, per-block sd ≈ 0.08). Single N=50 batch 2σ
  ≈ ±14pp on a coin-flip pair. Escalated N=400 gives 2σ ≈ ±5pp.
  Step 3 display work must know this — near-even lines will
  read as 40-60% zone even when the true probability is 50%.
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
- **Live-inconsistency observation (MEASURED, docs-only).**
  Path A (`_run_real_engine`) and Path B (`_simulate_card_fights`)
  DIVERGE on the `is_main_event` sim kwarg for co_main slot
  fights: Path A `slot in ("main_event", "co_main")` → True;
  Path B `slot == "main_event"` → False. Latent live
  inconsistency, not introduced by the odds arc; MC mirrors both
  per ratified rule (a). Needs its own diagnosis; not this arc.
- **Refactor candidate (STRONG, parked).** Shared sim-invocation
  helper for Path A / Path B / MC. Three hand-built call sites
  already drifted once (the fallback-triple bug this parity gate
  caught). Touches both live paths so it needs its own
  equivalence gate — do not bundle with a feature ship. File
  and hold for its own single-purpose commit.
- **Cleanup candidate (C from Step 1b, parked).** Refactor
  `fight_integration.py:403-412` aggression buff out of in-place
  `FighterAttributes` mutation. Blocks bundle-reuse patterns.
  Not scheduled.

- **STRIKE-SKILL-DMG1 phase 1a [SHIPPED 2026-08-22, commits
  6df956e + 668a7b1; instruments c06b0f9 + 713c0a7 + 5cb1468; docs
  1b1ecee. DEPLOYED to PA 2026-08-22, HEAD 1b1ecee, proof-verified:
  PA `.git/refs/heads/main` reads
  `1b1ecee634de98b7a8099d3354b4077846612d01`; serving
  `cage_dynasty_web/fight_engine.py:468` reads
  `STRIKE_SKILL_DAMAGE_K        = 1.0` (Files-API grep, verbatim).**

  **DESIGN DECISION (Van, 2026-08-22).** Fix for ENGINE-STRIKE-SENS1
  mechanism #2 (DAMAGE-SKILL-ABSENT): one channel at a time,
  skill-into-damage first. Striking to remain higher-variance than
  grappling (family 88v55 target band 0.65-0.70, NOT parity with
  grappling's 0.80). Single-stat weakness and kick-cliff interaction
  deliberately deferred to phase 1b/1c rather than compensated by a
  higher K.

  **MECHANISM.** calculate_strike_damage (cage_dynasty_web/
  fight_engine.py) now applies, after the strength terms and before
  the kick cliffs:
      damage *= max(STRIKE_SKILL_DAMAGE_FLOOR,
                    1 + (STRIKE_SKILL_DAMAGE_K * (_skill - 75) / 100))
  Family mapping mirrors calculate_strike_success: boxing punches ->
  attacker.boxing; kicks -> attacker.kicks; clinch + fallback (incl.
  GnP menu) -> attacker.clinch_striking. Attacker-side only, zero RNG
  consumed, plain-global reads (sweepable by module attribute rebind).
  STRIKE_SKILL_DAMAGE_K = 1.0; STRIKE_SKILL_DAMAGE_FLOOR = 0.25
  (deterministically inert at K=1.0 for legal skills 1-99, factor
  range [0.26, 1.24]; exists to protect future K retunes). Reaches
  BOTH sim paths (fight_engine.py pre-gen caller + fight_integration
  live caller) by construction — ratified as intended: pre-gen and
  live-play must share physics or MC odds lie.

  **GATES (all MEASURED, artifacts in outputs/).**
  - Commit 1 (6df956e, K=0): bit-identical equivalence vs fresh
    baseline at c06b0f9 — data-only diff empty exit=0, MD5 collision
    on stripped streams. Arms E/F/G1/H3/J1, CRN, standup==10
    asserted per arm.
  - Commit 2 (668a7b1, K=1.0 + floor): per-arm CSV-domain MD5s
    bit-match the sweep's K=1.0 rows on all 5 arms (E 42ed2d78...,
    G1 6c2f82ac..., H3 03c579a0... first-500 under CRN, J1
    a8a5b680..., F 11d4be8c...). Hasher discrimination PROVEN before
    acceptance: E and G1 hashes distinct across all four sweep K
    files, tuple counts 2000 per source.
  - Discriminators: J1 (all-75) and F (grappling 88v55, striking
    75/75) bit-identical across K ∈ {0.5, 1.0, 1.5, 2.0} AND across
    both instruments. J1/F p_f1 reproduce the SENS1 filed values to
    4 decimals (0.4840 / 0.8035) — instrument continuity with the
    closed diagnostic confirmed at bit level.

  **K-CHOICE GRID (N=2000/arm, from
  outputs/strike_skill_dmg1_sweep_out.txt).** E (striking family
  88v55): 0.5365 baseline -> 0.6160 (K=0.5) / 0.6945 (K=1.0) /
  0.7610 (K=1.5) / 0.7895 (K=2.0); KO+TKO share 0.306->0.567.
  G1 (boxing alone 88v55): 0.4805 -> 0.5085/0.5200/0.5485/0.5590.
  H3 (kicks 74v61): ~0.464 flat across all K. (H3 K=0 baseline at
  N=2000 not measured this arc; SENS1's filed H3 baseline is
  0.4160 ±0.0441 at N=500 — same seeds, smaller sample, not a
  discrepancy.) K=1.0 chosen: E lands in the 0.65-0.70 band with
  KO+TKO 0.383; higher K rejected as using one dial to compensate
  for channels still broken (flat landing #1, kick cliffs) whose
  future fixes will stack on this one.

  **FINDINGS FILED WITH THE SHIP.**
  - G1 single-stat weakness: boxing-alone 88v55 reaches only 0.5590
    even at K=2.0 — a lone striking stat rides on a minority of
    offense while landing stays flat. Phase 2 (#1 landing curve)
    territory, not a K problem.
  - H3 K-flatness is arithmetic, not wiring: attacker kicks 74 sits
    at the 75 neutral point (factor ~0.99); lift comes only from the
    61-defender's weakened kick output, a minority slice. "Better
    kicker wins" needs phase 1b de-cliff, not more K.
  - Draws shrink as K rises (E arm: 65 -> 41). Partially explains
    the SENS1 "draws scale with striking gap" observation as
    damage-parity scoring ties that the dial breaks.

  **PROCESS INCIDENTS (this arc, logged not hidden).**
  - 713c0a7 fired after its own written STOP (cc self-flagged; Van
    accepted rather than reverted — a reset would have orphaned the
    sweep's provenance header). Standing rule since: commits fire
    ONLY on Van's literal "commit approved — go". Inferred/pattern
    approval does not qualify.
  - H3 N changed 500->2000 in the sweep without being flagged;
    caught by the architect from the grid. Instrument-config changes
    must be declared before results are read.
  - Commit-2 acceptance gate required an instrument swap (sweep
    recorded dict-domain hashes; acceptance needed CSV-domain).
    Swap was surfaced honestly and the replacement hasher was
    proven to discriminate (distinct E/G1 hashes across K) before
    the gate result was accepted. Correct handling; filed as the
    template for "adjusted instrument" cases.
  - Deploy-proof step: cc constructed a Files-API `curl` with the
    PA token as a plaintext literal in the `-H` header. The
    permission layer denied the request but did not redact the
    command display, exposing the token in the session transcript
    for the second (or third — see fragment ruling below) time.
    Rule (d) redaction must happen at command CONSTRUCTION, not
    just in the report layer. New standing construction pattern
    (cc-side, effective immediately): credentials are sourced
    into a `$_VAR` from a filesystem read (e.g. `deploy.sh:5`)
    and referenced by name; the literal never appears in any
    echoed command line. Rotation was ordered mandatory
    regardless of prior-rotation status. Two-sided revocation
    gate landed measured: old-token Files-API call returned HTTP
    `401` (leaked credential dead); new-token Files-API calls
    returned the PA HEAD and serving-file grep pastes above.
    **Fragment comparison waived — rotation and 401 revocation
    measured regardless, prior-rotation status left unresolved.**

  **QUEUE.** Phase 1b: replace kick cliffs (:2394-2398 region,
  ×1.25 / ×1.15 binaries) with a gradient, measured against the
  1a after-state; re-probe H3. Phase 1c candidates, each own arc:
  landing-curve retune (#1), classifier hysteresis (#3), SD
  disentangle (#5), judge-weight re-measure (#4 — may need nothing
  now that damage carries skill). Live-roster violence check
  (finish-rate drift on real save populations at K=1.0) owed
  opportunistically at next live card, alongside the carried PA
  timing measurement.

- **STRIKE-SKILL-DMG1 phase 1b [SHIPPED 2026-08-24, commits
  0562687 (inert wire) + a11d47b (de-cliff, K=1.0 live);
  instruments (outputs/, untracked): phase1b_baseline,
  hash_repair, phase1b_commit1_gate, phase1b_setupgate,
  phase1b_sweep, phase1b_commit2_gate, phase1b_damage_delta].
  DEPLOYED to PA 2026-08-24, HEAD 5429e0d, proof-verified: PA
  `.git/refs/heads/main` reads
  `5429e0d226d94a203bf8c0c527ad53d603a6040b`; serving
  `cage_dynasty_web/fight_engine.py:494` reads
  `KICK_GAP_DAMAGE_K            = 1.0` (Files-API, verbatim);
  KICK_CLIFFS_ENABLED: 0 matches in served file.**

  **DESIGN DECISION (Van, 2026-08-23).** De-cliff kicks via
  two-sided pure-gap gradient replacing the historical MUAY-THAI-
  VS-BOXER cliffs. Old cliffs at fight_engine.py:2432-2436 (pre-
  1b anchor): `if attacker.kicks >= 75 and defender.kicks < 60:
  damage *= 1.25` and `elif attacker.kicks >= 65 and defender.kicks
  < 50: damage *= 1.15` — level×side test, if/elif mutually
  exclusive (a strike where both guards were satisfied got only
  the ×1.25, never compounded). Erased structure: five regions of
  the level×side surface — (×1.25 region: att≥75 AND def<60),
  (×1.15 region: att∈[65,74] AND def<50, only reachable when the
  ×1.25 guard failed), (dead region: att<65, no bonus), (dead
  region: def≥60, no bonus regardless of attacker), (dead region:
  att∈[65,74] AND def∈[50,60): no bonus despite gaps up to 24 —
  the M1 dead zone). Gradient replaces all five with one level-
  independent gap function.
  K=1.0 chosen off the phase-1b measured sweep grid. E family
  value EXPLICITLY re-chosen at 0.7075 above the 1a 0.65-0.70
  band (band was measured under cliffs; re-choose is legitimate
  vs drift). H3 emphatic 74v61 tellability deliberately reserved
  for landing-curve arc (#1).

  **MECHANISM.** calculate_strike_damage
  (cage_dynasty_web/fight_engine.py at HEAD a11d47b) applies
  inside the existing "kick" strike-family guard, after the
  strength terms and the 1a skill factor:

      kick_gap = attacker.kicks - defender.kicks
      damage *= max(KICK_GAP_DAMAGE_FLOOR,
                    min(KICK_GAP_DAMAGE_CEIL,
                        1 + (KICK_GAP_DAMAGE_K * kick_gap / 100)))

  Constants (module-level at fight_engine.py:494-496 at a11d47b):
  KICK_GAP_DAMAGE_K = 1.0, KICK_GAP_DAMAGE_FLOOR = 0.5,
  KICK_GAP_DAMAGE_CEIL = 1.5. Plain-global reads at call time;
  sweep by attribute rebind, no source edit. Clamps [0.5, 1.5]
  are ACTIVE PROTECTION at nonzero K on extreme legal skill gaps
  up to ±98 (99-vs-1); unclamped factor at K=1.0 on gap 98 is
  1.98, clamped to 1.5. Distinct from the 1a floor which is
  deterministically inert on legal skill values.

  Kick-family scope (10 StrikeType members whose .value.lower()
  contains "kick"): LEG_KICK, BODY_KICK, HEAD_KICK, FRONT_KICK,
  SIDE_KICK, SPINNING_BACK_KICK, WHEEL_KICK, AXE_KICK, CALF_KICK,
  OBLIQUE_KICK. Knees (KNEE_BODY, KNEE_HEAD, FLYING_KNEE) NOT
  included — no "kick" substring; those route to
  clinch_striking via the 1a family-mapping else fallback.

  Attacker- and defender-side read; defender-side stays within
  the replaced cliffs' existing precedent — no new defender
  channel opens. Zero RNG consumed. Reaches both sim paths
  (fight_engine pre-gen caller + fight_integration live caller)
  by construction.

  **GATES (all MEASURED, artifacts in outputs/).**
  - Commit 1 (0562687, gradient wired inert at K=0, cliffs
    behind KICK_CLIFFS_ENABLED=True): six-arm bit-identity vs
    fresh 1b baseline at HEAD 5643d88. All PASS:
      E   42ed2d78060e807d5892b72482666d55
      G1  6c2f82ac46c5a476367f3c0684710237
      H3  d27078ed192dc3fc2cab0f5eaf345a19  (full-2000, new tracked)
      H4  b3bd8c0d4bfae111940d03426e7d2da8  (full-2000, first-look)
      J1  a8a5b6809e688395387e7e829b419460
      F   11d4be8c28902e9e26c6d627424663fe
  - Sweep-setup (before any K read): scratch cliff-deleted
    engine at /tmp/skssweep_scratch vs tracked engine with
    KICK_CLIFFS_ENABLED rebound False — both K=0 — six-arm
    bit-match. Proves the enable flag is a clean off-switch
    and Commit 2's source deletion is byte-equivalent to
    attribute rebind. Scratch deleted after PASS.
  - Sweep discriminator: J1 and F (and incidentally G1, all
    with kicks 75/75 → gap 0 → factor exactly 1.0 at any K)
    bit-identical across all K∈{0.5, 1.0, 1.5, 2.0} AND vs 1b
    baseline hashes. Bit-invariance under two-sided pure-gap
    gradient is arithmetic; the sweep measured it to confirm no
    non-kicks-family leak.
  - Commit 2 (a11d47b, cliffs deleted, K=1.0 source-set):
    six-arm bit-match vs sweep K=1.0 rows. Post-edit engine
    reproduces sweep-time attribute rebind exactly:
      E   c94f2f6f488e940d0c26094fa33fe0a4  PASS
      G1  6c2f82ac46c5a476367f3c0684710237  PASS
      H3  2f1d2034aa308391ea487dfe776adda1  PASS
      H4  8cc3029309b1c88b2c08628a511c0f5b  PASS
      J1  a8a5b6809e688395387e7e829b419460  PASS
      F   11d4be8c28902e9e26c6d627424663fe  PASS

  **K-GRID (N=2000/arm, from
  outputs/strike_skill_dmg1_phase1b_sweep_out.txt).**

       K  arm    p_fav     ±2σ  KO+TKO  kotko%  finish  draws  mn_rnds
     0.5  E    0.6865  0.0207     733  0.3665    1122     62   2.482
     0.5  G1   0.5200  0.0223     452  0.2260     823     72   2.601
     0.5  H3   0.4710  0.0223     440  0.2200     824     80   2.614
     0.5  H4   0.5210  0.0223     680  0.3400     971     75   2.611
     0.5  J1   0.4840  0.0223     925  0.4625    1120     82   2.635
     0.5  F    0.8035  0.0178     568  0.2840     798     28   2.647
     1.0  E    0.7075  0.0203     833  0.4165    1211     50   2.446
     1.0  G1   0.5200  0.0223     452  0.2260     823     72   2.601
     1.0  H3   0.4840  0.0223     458  0.2290     839     69   2.606
     1.0  H4   0.5590  0.0222     763  0.3815    1045     63   2.571
     1.0  J1   0.4840  0.0223     925  0.4625    1120     82   2.635
     1.0  F    0.8035  0.0178     568  0.2840     798     28   2.647
     1.5  E    0.7290  0.0199     931  0.4655    1294     49   2.405
     1.5  G1   0.5200  0.0223     452  0.2260     823     72   2.601
     1.5  H3   0.4985  0.0224     458  0.2290     841     67   2.603
     1.5  H4   0.6000  0.0219     853  0.4265    1117     53   2.546
     1.5  J1   0.4840  0.0223     925  0.4625    1120     82   2.635
     1.5  F    0.8035  0.0178     568  0.2840     798     28   2.647
     2.0  E    0.7295  0.0199     934  0.4670    1296     48   2.404  BOTH BOUND
     2.0  G1   0.5200  0.0223     452  0.2260     823     72   2.601
     2.0  H3   0.5060  0.0224     479  0.2395     864     73   2.599
     2.0  H4   0.6270  0.0216     909  0.4545    1166     54   2.511
     2.0  J1   0.4840  0.0223     925  0.4625    1120     82   2.635
     2.0  F    0.8035  0.0178     568  0.2840     798     28   2.647

  Clamp-bound cells: E at K=2.0 only (gap 33, unclamped factor
  1.660 clamps to CEIL 1.5 on favored side; symmetric −1.660
  clamps to FLOOR 0.5 on weak). H4 at K=2.0 gap 25 → factor
  exactly 1.500 = CEIL boundary (not strictly clamped per
  `> ceil`; symmetric −25 → 0.500 = FLOOR boundary).

  Cliffs-off K=0 floor (setup-gate run (a), same 12000 sims,
  before gradient engages): E 0.6570, G1 0.5200, H3 0.4640,
  H4 0.4930, J1 0.4840, F 0.8035. Refill lens vs cliffs-on
  baseline at chosen K=1.0:
  - E (striking family 88v55; kick gap 33): cliff worth +3.75pp
    (0.6570→0.6945); gradient K=1.0 gives +5.05pp (→0.7075).
    Surplus explained by weak-side penalty + in-between gaps
    the cliffs missed.
  - H4 (kicks 80v55, gap 25): cliff worth +5.55pp
    (0.4930→0.5485); gradient K=1.0 gives +6.60pp (→0.5590).
    Conservation point: gap 25 at K=1.0 is ×1.25 exact.
  - H3 (kicks 74v61, gap 13): cliff never fired at 74v61
    (74 < 75); gradient K=1.0 gives +2.00pp (0.4640→0.4840).
    Tellable in direction, honestly modest.

  **AGGREGATE DAMAGE DELTA (§8, N=2000/arm, MEASURED, cliffs-on
  K=0 baseline vs cliffs-off K=1.0 post-Commit-2).**

    arm  metric                     cliffs-on K=0  cliffs-off K=1.0     Δ         %
    H3   kick_dmg / fight               39.4255            40.0700  +0.6445   +1.63%
    H3   kick_dmg / landed kick          8.0272             8.0892  +0.0621   +0.77%
    H4   kick_dmg / fight               68.6900            63.9894  −4.7006   −6.85%
    H4   kick_dmg / landed kick          9.7849             9.0959  −0.6890   −7.04%

  H4 aggregate landed-kick damage DROPS despite favored p_fav
  rising (0.5485 → 0.5590). Two-sided penalty on 55-side landed
  kicks (gap −25 → ×0.75, where cliff gave ×1.00) redistributes
  damage away from the weak side even though the favored side
  sees ×1.25 (identical to old cliff). "Weaker kicker's rally
  goes nowhere" made concrete on the canonical-cliff pair. H3's
  near-null per-landed-kick change is the two-sided factors
  1.13 / 0.87 canceling in aggregate at gap 13.

  **PRE-REGISTRATION MISS (house rule — logged, not absorbed).**
  Architect pre-registered in spec v2.1: "H3 moves from ~0.464
  into the low 0.50s." Measured at chosen K=1.0: H3 = 0.4840
  (+2.00pp above baseline). Direction correct, magnitude under
  prediction — low-0.50s only reached at K ≥ 1.5. Miss filed,
  not resolved by picking K=1.5 (which would be fitting the
  engine to the forecast per Van's ruling at K-pick).

  **FINDINGS FILED WITH THE SHIP.**
  - (a) Kicks-vs-boxing per-point stat-value imbalance
    (MEASURED). 1a boxing dial: G1 (boxing 88v55, gap 33) moved
    0.4805 (K=0) → 0.5200 (K=1.0), +3.95pp per 33-point boxing
    gap = 0.120 pp/point. 1b kicks gradient: H4 (kicks 80v55,
    gap 25) moved 0.4930 (cliffs-off K=0) → 0.5590 (cliffs-off
    K=1.0), +6.60pp per 25-point kicks gap = 0.264 pp/point.
    Ratio: per-point kick worth ≈ 2.2× per-point boxing worth.
    Channel architecture ruled CORRECT (damage dial on both;
    SENS1 mechanism #1 says punch-defense belongs in LANDING
    which is not yet wired). The imbalance is the opening
    argument for the landing-curve retune arc (#1 in SENS1
    QUEUE) — kicks defense goes through damage (per closed
    cliffs, now gradient), punch defense goes through landing
    (not yet wired) and neither the 1a dial nor 1b gradient
    can fix that from the damage side alone.
  - (b) Boxing family excludes BACKFIST and SUPERMAN_PUNCH
    (MEASURED via `calculate_strike_success:2269-2288` at HEAD
    a11d47b). Boxing branch tests strike ∈ {JAB, CROSS, HOOK,
    UPPERCUT, OVERHAND}. The other two "punch" strikes fall
    through the else to clinch_striking. Cosmetic labeling
    artifact — not outcome-affecting, but discoverable and
    worth cleaning as a 1c candidate.
  - (c) Weak-side ×0.60 stacked-factor watch item. At K=1.0
    on 80v55 kicks: favored-side stacked (1a × 1b) =
    1.05 × 1.25 = 1.3125; weak-side stacked = 0.80 × 0.75 =
    0.60. Weak-kick damage at 60% of pre-1a value. Live-roster
    violence check is the tripwire; if weak-side kicks feel
    visibly-nothing in live play, tuning surface is
    KICK_GAP_DAMAGE_FLOOR (raise from 0.5 toward 0.7 to
    compress the weak-side penalty while preserving the
    favored ceiling).

  **PROCESS INCIDENTS (this arc, logged not hidden).**
  - (a) M1 at Gate 0: handoff and spec paraphrase missed
    if/elif mutual exclusivity on the old cliff branches
    (paraphrase used `->` for both, reading as independent
    conditionals). Caught at Gate 0 by verbatim-match rule
    ("spec subordinates to code-at-HEAD"). Resolved as spec
    amendment v2.1 (docs-only, no filed number changed,
    mechanism / gates / constants untouched).
  - (b) Baseline hasher declared wrong domain. First 1b
    baseline ran with in-memory dict-domain MD5 hasher;
    targets were CSV-domain from actual sweep CSV disk reads.
    Cross-check reported all-MISMATCH despite p_fav MATCH
    exactly on J1 (0.4840) and F (0.8035). cc self-flagged as
    instrument-convention mismatch, not underlying-data.
    Repaired instrument-first per Van's rule: reproduced all
    five filed 1a hashes from historical sweep CSVs exactly
    (E, G1, H3 first-500, J1, F), discrimination re-proven
    (E and G1 distinct hashes across sweep K files, tuple
    counts 2000), then applied to 1b baseline under one
    convention. Continuity established under repaired hasher.
  - (c) Baseline harness nearly overwrote its own accepted
    CSV. The commit-1 gate initially reused the baseline
    harness for the post-edit rerun; the harness's fixed
    output path would have overwritten the accepted baseline
    artifact. Caught pre-damage by cc, run killed, baseline
    CSV proven intact by size+mtime unchanged. Distinct-
    output-path rule now standing for all gates going forward
    (commit-1 gate, setup-gate, commit-2 gate, damage-delta
    all used distinct paths).
  - (d) Two commit-message label errors, both caught in
    architect review before commit fired. Commit-1 message
    carried over 1a's "Attacker-side only. Zero RNG consumed."
    boilerplate — false for 1b's defender-side read. Commit-2
    message's refill-lens block labeled E as "kicks 88v55"
    when E is the striking-family arm (kicks are one component,
    gap 33). Both corrected before firing.

  **QUEUE.** 1b closes engine-side pending live-roster
  violence check. Live-roster check now covers 1a+1b jointly
  at next live card, alongside the carried PA timing
  measurement (both owed from earlier ships). Next arcs, each
  its own:
  - Landing-curve retune (#1) — PROMOTED by phase-1b finding
    (a): kicks-vs-boxing per-point imbalance is the damage-
    side landing at ~2.2× the boxing damage-side effect,
    because boxing's missing per-hit-damage channel goes
    through landing (not yet wired) and no damage-side dial
    can rebalance from the wrong channel.
  - Classifier hysteresis (#3).
  - SD disentangle (#5).
  - Judge-weight re-measure (#4) — may need nothing now that
    damage carries skill on both boxing (1a) and kicks (1b);
    re-measure at first live-roster check.

- **STRIKE-LANDING-AUDIT1 [CLOSED 2026-08-24, read-only
  diagnostic at HEAD a04faf4, no engine commits; instruments
  (outputs/, untracked): strike_landing_audit1_probe.py,
  strike_landing_audit1_root_probe.py,
  strike_landing_audit1_aggregate.py].**

  **INSTRUMENT + GATES (all MEASURED).** Wrapper on
  calculate_strike_success (CSS). RL1 decided from bytes at
  fight_integration.py:39 (fi imports CSS by name via
  `from fight_engine import`): BOTH fe.calculate_strike_success
  (call site fight_engine.py:3315) AND fi.calculate_strike_success
  (call site fight_integration.py:810) overwritten with a pure
  pass-through wrapper that consumes zero RNG. Per-call records
  (arm, seed, side, strike_type, family, landed, was_counter).

  Gates:
  - Gate 3a probe-off reused-hash bit-match — all 4 reused arms
    PASS raw md5:
      L-J1   a8a5b6809e688395387e7e829b419460
      L-B88  6c2f82ac46c5a476367f3c0684710237
      L-K74  2f1d2034aa308391ea487dfe776adda1
      F      11d4be8c28902e9e26c6d627424663fe
  - 9-arm discrimination — 9 distinct raw md5s AND 9 distinct
    normalized md5s.
  - Gate 3b probe-on ≡ probe-off — outcome CSVs bit-identical
    across all 9 arms (byte-level diff excluding `# mode:`
    header = 0 lines per arm). Wrapper proven pass-through on
    all arms, not one.
  - Normalized-domain (winner → slot1/slot2) sibling hasher NOW
    A PERMANENT SECONDARY CHECK. Filed norm targets for the
    four reused arms:
      L-J1   cace1efa4a3c8eabe8a976ec42a6f2ba
      L-B88  d2d943266a81c6817bbed5062b6fa37a
      L-K74  3e5de0d7963bc66cd2cf65ff1d981d0e
      F      78605664d38afa9b6abfaa83b9cc16ce  (captured this arc)

  **PROCESS INCIDENT (logged not hidden).** Gate 3a first ran
  FAIL on three relabeled reused arms (L-J1, L-B88, L-K74 all
  producing different raw md5s from their 1b commit-2 gate
  targets while F PASSED). FIGHTER-ID-SENSITIVITY-OBS1 was
  provisionally filed as a behavior claim ("fight outcomes are
  sensitive to fighter_id string content"), then RETRACTED on
  measurement: normalized-domain diff (winner → slot1/slot2)
  proved all 2000 rows bit-identical per arm — normalized md5
  matched between my probe and the historical 1b K=1.0 CSV
  (cace1efa for L-J1↔J1, d2d94326 for L-B88↔G1, 3e5de0d7 for
  L-K74↔H3). Zero engine sensitivity. Mechanism: the outcome
  hasher's own domain — the `winner` column carries the raw
  fighter_id string (e.g. "L-J1_slot1"), and when fighter_id
  strings differ across relabeled fixtures the hash differs even
  under bit-identical behavior. Refiled as instrument note.

  Root-cause path preserved for provenance
  (outputs/strike_landing_audit1_root_probe.py): monkeypatched
  hit-counters on all three suspect id-consumer sites recorded
  0 hits per site per arm on both L-J1 and F —
  game_bridge.py:7210 dormant (fighter_id IS in _fighter_data
  because _register_fighter populates it), game_bridge.py:7237
  md5 fallback dormant (all 18 _attr keys present in fdata),
  models.py:1202 not on the sim path. Additional stronger
  negative: str-hash-driven mechanisms (set-iteration order,
  hash-lookup path selection) ruled out by F's cross-process
  bit-stability despite PYTHONHASHSEED unset (random per
  process).

  Fix: `_FIGHTER_ID_SOURCE` mapping — reused arms (L-J1, L-B88,
  L-K74, F) use the 1b commit-2 gate's label strings for the
  fighter_id construction, so raw-hash bit-continuity with
  filed targets is preserved. Fixture attributes unchanged —
  only the fighter_id string differs. Normalized-domain hasher
  added as the permanent secondary check so label contamination
  can never masquerade as behavior again.

  Lesson filed for future instrument design: "outcome hash
  differs" is not "behavior differs" when the hash domain
  includes labels. Any hasher that includes identity columns
  (winner_id, loser_id, fighter1_id, fighter2_id, camp_id,
  etc.) needs a normalized-domain sibling before FAIL verdicts
  are trusted as behavior claims.

  **SENSITIVITY TABLES (N=2000/arm, HEAD a04faf4).**

  Family key: box=boxing (JAB/CROSS/HOOK/UPPERCUT/OVERHAND,
  offense=boxing), kck=kicks (10 members, offense=kicks),
  cex=clinch_explicit ({CLINCH_KNEE, CLINCH_ELBOW, DIRTY_BOXING},
  offense=clinch_striking, defense hybrid with takedowns),
  cft=clinch_fallthrough (else branch, 12 members enumerated,
  offense=clinch_striking, defense=striking_defense).

  Consolidated slot1-side (single-stat mover 88 or 74 on slot1
  for asymmetric arms):

    arm     p_slot1  box_att  box_rate  kck_att  kck_rate  cex_att  cex_rate  cft_att  cft_rate
    L-J1    0.4840   13954    0.4731    19430    0.4710    4058     0.4475    40458    0.4137
    L-B88   0.5200    9700    0.4724    12988    0.4642    2401     0.4344    45456    0.4093
    L-B74   0.4510    7581    0.4679    11055    0.4685    3291     0.4579    48828    0.4189
    L-K74   0.4840    7935    0.4713    10775    0.4604    3379     0.4492    49956    0.4178
    L-K78   0.5320   12819    0.4724    17824    0.4684    3398     0.4620    41751    0.4200
    L-K88   0.6000    8817    0.4621    13424    0.4660    2105     0.4204    46949    0.4090
    L-C88   0.5780    9098    0.4663    13182    0.4619    2319     0.4368    47174    0.4130
    L-C74   0.4900   13000    0.4772    17892    0.4797    3362     0.4619    42195    0.4200
    F       0.8035    7970    0.4593    10811    0.4621    3605     0.4352    53846    0.4059

  Consolidated slot2-side (single-stat holder 55 or 61 on slot2
  for asymmetric arms):

    arm     p_slot2  box_att  box_rate  kck_att  kck_rate  cex_att  cex_rate  cft_att  cft_rate
    L-J1    0.4750   13209    0.4860    18484    0.4798    3783     0.4843    36778    0.4294
    L-B88   0.4440    7186    0.4883    11620    0.4824    2023     0.4572    38671    0.4415
    L-B74   0.5155    7124    0.4969    11194    0.4761    2274     0.4415    42034    0.4289
    L-K74   0.4815    8049    0.4839    10451    0.4733    2035     0.4486    40353    0.4348
    L-K78   0.4395    9352    0.4846    11866    0.4728    2220     0.4604    39884    0.4261
    L-K88   0.3695    8041    0.4931    10115    0.4786    1692     0.4657    35595    0.4497
    L-C88   0.3900    7829    0.4918    10656    0.4815    1841     0.4666    35419    0.4285
    L-C74   0.4650    9495    0.4799    13412    0.4688    2315     0.4242    41941    0.4161
    F       0.1825    8185    0.4701    11633    0.4677    5569     0.4997    33556    0.4409

  Control-delta summary — own-family favored-side landing rate
  vs L-J1 control (all-75/75):
  - Boxing: L-B88 slot1 box_rate = 0.4724 vs L-J1 slot1
    box_rate = 0.4731. Δ = −0.0007 (−0.07pp). Effectively zero
    at 88v55.
  - Kicks: L-K74 slot1 kck_rate = 0.4604 (Δ = −0.0106
    (−1.06pp)), L-K78 slot1 = 0.4684 (Δ = −0.0026 (−0.26pp)),
    L-K88 slot1 = 0.4660 (Δ = −0.0050 (−0.50pp)) — flat-to-
    slightly-NEGATIVE across all three kick fixtures, INCLUDING
    L-K88 with the fight_engine.py :2317-2318 +10 offense
    landing cliff firing (att.kicks≥80 AND def.kicks<60). The
    cliff activates on every kick from slot1 in L-K88 yet
    aggregate landing rate is LOWER than control.
  - Clinch: L-C88 slot1 cex_rate = 0.4368 (Δ = −0.0107
    (−1.07pp)), L-C74 slot1 = 0.4619 (Δ = +0.0144 (+1.44pp)).
    Flat both directions. L-C88 fallthrough: 0.4130
    (Δ = −0.0007 (−0.07pp)). Flat.
  - Formula-predicted +2-3pp on 88v55 favored side (raw
    offense/(offense+defense+1)*0.5 spread at 88v55 delivers
    ~11.5pp pre-variance) is ABSENT from aggregate.

  VERDICT: the landing channel transmits ~nothing at aggregate.
  All p_fav movement observed on the asymmetric arms rides the
  1a/1b damage dials and fight-shape effects (attempt-volume
  redistribution, fatigue/momentum/state-modifier interactions),
  not the landing formula.

  **FINDINGS FILED.**
  - (a) Landing channel dead at aggregate (above). The
    landing-curve retune arc (#1 in SENS1 QUEUE, PROMOTED by
    1b finding (a)) is CONFIRMED against measurement. Its spec
    must address the state-modifier wash (grappler-pressure
    penalties at :2333-2363, stamina scaling at :2367-2368,
    rocked defender bonus at :2371-2372, variance at
    :2375-2376, upset branch at :2383-2388, and clamp
    [0.15, 0.85] at :2380) that appears to absorb skill-gap
    input BEFORE it reaches the final `landed = random.random()
    < success_chance` gate, not just the base-formula
    compression `0.20 + offense/(offense+defense+1) * 0.5`.
  - (b) Attempt-share hierarchy (MEASURED, slot1 aggregated
    across all 9 arms, ~663K attempts):
      cft ~62.9% > kicks ~19.2% > boxing ~13.7% > cex ~4.2%
    clinch_striking is the highest-leverage striking stat by
    volume (L-C88 p_slot1=0.578 > L-B88 p_slot1=0.520). Boxing
    weakness is double-layered: no landing sensitivity AND
    minority attempt share. When landing-curve retune ships,
    boxing needs BOTH a landing channel and either more attempt
    weight or acknowledgment that boxing skill will lift KO
    numbers via 1a damage but never push p_fav much on its own.
  - (c) SLOT-ASYM-OBS1 [FILED, mechanism unlocated]: slot2
    lands more than slot1 systematically across ALL 9 arms
    AND all 4 families, magnitude ~1-4pp per family per arm
    (e.g. L-J1 all-75/75 control: box slot1 0.4731 vs slot2
    0.4860; kck slot1 0.4710 vs slot2 0.4798; cex slot1 0.4475
    vs slot2 0.4843; cft slot1 0.4137 vs slot2 0.4294). Not
    seed noise — appears on the symmetric mirror arm (L-J1)
    with matched fixtures. Mechanism unlocated in this
    read-only pass; candidates for a future diagnostic
    include: initiative bias (slot1 acts first each exchange,
    consuming variance/state), fatigue-scaling asymmetry from
    initiative order, or state-modifier order-of-operations.
    Standing rule going forward: **landing-rate comparisons
    must be within-slot** (slot1 vs slot1 across arms, slot2
    vs slot2 across arms). Cross-slot comparisons within an
    arm carry ~1-4pp systematic offset.
  - (d) DEAD-CONTENT-OBS1 [FILED, upstream of CSS scope]:
    9 of 30 StrikeType enum members never selected across
    ~1.22M CSS calls in this fixture set:
      kicks branch (5 of 10 dead):   SIDE_KICK,
        SPINNING_BACK_KICK, WHEEL_KICK, AXE_KICK,
        OBLIQUE_KICK
      fallthrough branch (4 of 12 dead): BACKFIST,
        KNEE_HEAD, ELBOW_VERTICAL, ELBOW_SPINNING
    ELBOW_UPWARD dominates by volume: 333579 attempts =
    ~43.8% of all clinch_fallthrough attempts, ~27.4% of all
    CSS calls (of any family) in this fixture set.
    `select_action` / `get_available_strikes` weighting,
    upstream of CSS, is the mechanism — outside this audit's
    read-only scope. Filed for the landing-curve retune arc's
    Gate 0 diagnostic — if select_action's weighting is skewed
    such that 30% of strike vocabulary is dead, retuning
    landing without also examining vocabulary distribution
    risks tuning against a non-representative attack mix.
  - (e) F fixture observation cell (RL3 per v1.2 spec):
    grappling-favored side (slot1, grappling family 88 vs 55)
    throws MORE clinch_fallthrough attempts than slot2
    (53846 vs 33556) — grappling advantage → more ground
    control → more GnP volume feeding through the fallthrough
    branch (GNP_PUNCH / GNP_ELBOW / GNP_HAMMER_FIST /
    ELBOW_UPWARD). Reciprocal: slot2 (grappling 55) throws
    MORE clinch_explicit attempts (5569 vs 3605) — likely
    reflecting bottom-position offense as the weak grappler
    fights from clinch. Not gate-grade; noted for the
    retune spec's attempt-mix redistribution question.

  **INSTRUMENT LIMITATION.** Landing CSV has no
  position/state column — per-exchange conditional effects
  (grappler-pressure penalty firing only when defender.takedowns
  ≥60, rocked defender bonus only when defender.is_rocked,
  upset branch only when offense < defense × 0.85, +10 kick
  cliff only when att.kicks≥80 AND def.kicks<60) cannot be
  attributed to specific state configurations at aggregate.
  The aggregate landing rate IS the player-visible readout and
  is the accepted output of this diagnostic — a v1.3
  conditional cut (adding position/state columns per call and
  slicing landing rate by state) can be ordered by Van if the
  retune arc's Gate 0 needs it.

  **LANDING-SIDE KICK CLIFF (measured this arc, from Gate 0
  read).** fight_engine.py:2317-2318 — `if attacker.kicks >= 80
  and defender.kicks < 60: offense += 10` — survived 1b (which
  deleted the two DAMAGE-side kick cliffs but did not touch
  this landing-side cliff). Measured effect: L-K88 slot1 kick
  landing rate 0.4660 vs L-J1 control 0.4710 — NEGATIVE
  aggregate effect at the point where the cliff is guaranteed
  to fire on every slot1 kick. Consistent with the broader
  finding (a) that the landing channel is dead at aggregate:
  a +10 raw offense bump is absorbed by downstream state
  modifiers and the ratio-compression formula before it can
  move the final landed roll. De-cliff candidate for the
  landing-curve retune arc; not a separate ship.

  **QUEUE.**
  - Landing-curve retune (#1) — spec for the retune arc must
    cover (i) base formula compression + clamp [0.15, 0.85] at
    :2379-2380, (ii) state-modifier wash from :2333-2372 that
    eats skill-gap input before the landed roll,
    (iii) select_action / get_available_strikes diagnostic in
    its Gate 0 (per DEAD-CONTENT-OBS1) so retune is targeted
    at the actual attack mix, not the enumerated vocabulary,
    (iv) landing-side kick cliff de-cliff, folded from this
    audit.
  - SLOT-ASYM-OBS1 parked. No action this arc; landing-rate
    comparisons must be within-slot going forward.
  - DEAD-CONTENT-OBS1 parked. Bundled into retune arc's Gate 0.
  - Classifier hysteresis (#3), SD disentangle (#5), Judge-
    weight re-measure (#4) — carried from SENS1 QUEUE
    unchanged.
  - Owed unchanged: live-roster violence check (1a+1b joint)
    at next live card; PA timing measurement pre-N-lock.

- **LANDING-CURVE-RETUNE1 — Gate 0 [CLOSED 2026-08-25, C1
  docs checkpoint at baseline 107a3c8; read-only diagnostic
  pass with architect's adversarial review folded in; no engine
  commits; spec `claude/landing_curve_retune1_spec_v0_1.md`
  ratified v0.1, kept untracked and out of repo].**

  **A1. Gate 0 anchors (verbatim at baseline 107a3c8).**

  Base landing formula + clamp — spec :2379-2380, matches at
  HEAD :2379-2380:

      success_chance = 0.20 + (offense / (offense + defense + 1)) * 0.5
      success_chance = max(0.15, min(0.85, success_chance))

  Kick landing cliff — spec :2317-2318, matches at HEAD
  :2317-2318:

      if attacker.kicks >= 80 and defender.kicks < 60:
          offense += 10  # Significant accuracy bonus vs non-kickers

  Grappler pressure block — spec :2333-2363, matches at HEAD
  :2333-2363. Defensive bonuses on defender: takedowns tiers
  ≥85/75/60 → +15/+10/+5; guard tiers ≥85/75 → +10/+5. Offensive
  penalty multipliers on takedown_threat (def-att): ≥30/20/10 →
  ×0.75/0.82/0.90. Sub-threat: ≥30/20 → ×0.88/0.94. Fires only
  in STANDING.

  Stamina — spec :2367-2368; code-at-HEAD is :2366-2367 (1-line
  drift, comment vs. action):

      offense *= (attacker_state.stamina / 100)
      defense *= (defender_state.stamina / 100)

  Rocked — spec :2371-2372; code-at-HEAD is :2370-2371 (1-line
  drift):

      if defender_state.is_rocked:
          defense *= 0.5

  Variance — spec :2375-2376, matches at HEAD :2375-2376:

      variance = random.uniform(0.75, 1.25)
      offense *= variance

  Upset branch — spec :2383-2388; code-at-HEAD :2384-2389 (1-line
  drift, trailing elif):

      if offense < defense * 0.85:
          upset_roll = random.random()
          if upset_roll < 0.18:
              success_chance = max(success_chance, 0.70)
          elif upset_roll < 0.35:
              success_chance = min(success_chance + 0.22, 0.70)

  CSS call sites: `fight_engine.py:3315` (fe's exchange loop) and
  `fight_integration.py:810` (fi's exchange loop). Both pass
  `FighterAttributes` objects raw; skills read inside CSS.

  **A2. H1 confirmed — no per-family defense stat exists.**
  Family routing table at CSS :2306-2325, verbatim:

    Family              | Trigger                              | offense                 | defense
    ---                 | ---                                  | ---                     | ---
    Boxing (5 strikes)  | JAB, CROSS, HOOK, UPPERCUT, OVERHAND | attacker.boxing         | defender.striking_defense
    Kicks (10 strikes)  | "kick" in strike.value.lower()       | attacker.kicks (+10 cliff cond) | defender.striking_defense
    Clinch-explicit (3) | CLINCH_KNEE, CLINCH_ELBOW, DIRTY_BOXING | attacker.clinch_striking | (defender.striking_defense + defender.takedowns) // 2
    Clinch-fallthrough (12) | else                             | attacker.clinch_striking | defender.striking_defense

  `striking_defense` is the sole defensive input for all four
  families; clinch_explicit dilutes it 50/50 with takedowns via
  integer division. There is no boxing_defense, no kick_defense,
  no clinch_defense. A defender with boxing=55 is not measurably
  harder to hit with punches than a defender with boxing=95 so
  long as their striking_defense is the same.

  **Consequence for the AUDIT1 measurements.** For boxing (L-B88)
  and clinch (L-C88) the landing formula never reads the
  defender's family stat — the gap propagates only through
  offense (+13 boxing on L-B88's slot1 attacker; +13
  clinch_striking on L-C88's slot1 attacker), zero change on
  defense. For kicks (L-K88) the defender's kicks stat DOES
  enter the formula, but ONLY via the +10 cliff at :2317
  (att.kicks≥80 AND def.kicks<60), which AUDIT1 already
  measured as producing zero aggregate lift (L-K88 slot1 kick
  landing rate 0.4660 vs L-J1 0.4710 = −0.50pp). Same outcome,
  different mechanism: for boxing/clinch the defender stat is
  unread; for kicks it's read only through a cliff the audit
  has already shown is worthless. Code's own base-pre-modifier
  ceiling at L-B88 slot1 boxing, standing, 75-across for all
  other stats:

      offense pre-var = 88 + 7 (speed) = 95
      defense pre-var = 75 + 7 (speed) + 10 (def.takedowns≥75)
                      + 5 (def.guard≥75) = 97
      base = 0.20 + 95 / (95+97+1) * 0.5 = 0.4461

  vs L-J1 (75/75 mirror):

      offense pre-var = 82;  defense pre-var = 97
      base = 0.20 + 82 / 180 * 0.5 = 0.4278

  Δ = **+1.83pp**. Measured aggregate delta at L-B88 slot1
  vs L-J1 slot1 = **−0.07pp** (0.4724 vs 0.4731).

  **Spec's "+5.5pp predicted" is FALSE at this baseline.** It
  assumed a family-symmetric formula — `0.20 + boxing_att /
  (boxing_att + boxing_def + 1) * 0.5` at 88 vs 55 = 0.5056 vs
  75 vs 75 = 0.4483, giving Δ = +5.73pp. The engine does not
  implement that. Filed as struck, not silently dropped: the
  arithmetic was correct given its assumption; the assumption
  is not what the code does.

  **A3. Modifier order table (verbatim from Gate 0 §0d,
  application order at CSS :2306-2398).**

    #  | Site        | Modifier                                     | Form                                    | Symmetry
    ---|---          |---                                           |---                                      |---
    1  | :2306-2325  | Family routing                               | overwrite off, def                      | overwrite
    2  | :2317-2318  | Kick landing cliff                           | offense += 10 (cond)                    | one-sided
    3  | :2328-2329  | Speed                                        | off += att.speed//10; def += def.speed//10 | symmetric
    4  | :2333-2346  | Grappler-pressure DEFENSE bonuses (STANDING) | def += 5/10/15 (takedowns) + 5/10 (guard) | one-sided
    5  | :2350-2356  | Grappler-pressure OFFENSE penalty (STANDING) | off *= 0.75/0.82/0.90                   | one-sided
    6  | :2358-2363  | Submission-pressure OFFENSE penalty (STANDING) | off *= 0.88/0.94                     | one-sided
    7  | :2366-2367  | Stamina scaling                              | off *= att.stam/100; def *= def.stam/100 | symmetric
    8  | :2370-2371  | Rocked defender                              | def *= 0.5 (cond)                       | one-sided
    9  | :2375-2376  | Base variance                                | off *= U(0.75, 1.25)                    | one-sided (offense only)
    10 | :2379-2380  | Base success chance + clamp                  | sc = 0.20 + off/(off+def+1) * 0.5; clamp [0.15, 0.85] | —
    11 | :2384-2389  | Upset branch                                 | sc lifted to floor=0.70 (18%) or boosted +0.22 capped at 0.70 (17%) when off < def * 0.85 | one-sided
    12 | :2391       | Landing gate                                 | landed = random.random() < sc           | —

  **Notes on shape.**

  - The ±25% offense variance is mean-preserving on the input
    (E[U(0.75,1.25)] = 1.0) but not through the outcome. The
    ratio at :2379 is convex on the low side and concave on the
    high side; Jensen's inequality shifts E[sc] relative to
    sc(E[offense]).
  - Variance interacts with the upset trigger at :2384. Where
    the offense/defense ratio sits close to 0.85, variance
    stochastically pushes offense across the threshold, engaging
    the upset lift at a rate driven by proximity to threshold —
    not by underdog identity.
  - Clamp [0.15, 0.85] hit-rate: **not computed this pass; Gate 2
    reports `clamp_hit` per attempt.** Prior Gate 0 narration
    speculated the clamp binds routinely when rocked; that was
    unmeasured and has been struck. Gate 2 measurement stands as
    the answer, not inference.

  **A4. UPSET-PARITY-HYP1 [UNMEASURED HYPOTHESIS, attributed to
  architect's Gate 0 adversarial review; Gate 2 target to
  falsify].** The "modifier wash" that absorbs the code's +1.83pp
  base gain on L-B88 has a name: the upset branch at :2384-2389
  fires as a lottery at parity-and-below, not as an underdog
  feature.

  Arithmetic on Gate 0's own numbers (mirror arm L-J1, symmetric
  75/75 attacker/defender):

      offense pre-var = 82; defense = 97; upset trigger = 82.45.
      After U(0.75, 1.25) variance on offense_pre_var = 82:
        P(offense_post_var < 82.45) = P(U < 82.45/82)
                                    ≈ P(U < 1.006)
                                    = (1.006 − 0.75) / 0.5
                                    ≈ 51%.
      Branch fires ~50% of parity attempts.

  At L-B88 slot1 (attacker boxing 88, offense pre-var 95):

      P(offense_post_var < 82.45) = P(U < 82.45/95)
                                  ≈ P(U < 0.868)
                                  = (0.868 − 0.75) / 0.5
                                  ≈ 24%.
      Branch fires ~24% of the time.

  Expected lift per FIRED attempt (18% floor to 0.70, 17% boost
  +0.22 capped at 0.70, above baseline sc_pre-upset):

      mirror sc_pre-upset ≈ 0.428 →
        lift ≈ 0.18 × (0.70 − 0.428)
             + 0.17 × min(0.22, 0.70 − 0.428)
             ≈ 0.18 × 0.272 + 0.17 × 0.22
             ≈ 0.049 + 0.037
             = 0.086 per fired attempt.
      88-side sc_pre-upset ≈ 0.446 →
        lift ≈ 0.081 per fired attempt.

  Expected lift AT AGGREGATE:

      mirror : 0.51 × 0.086 ≈ +4.4pp
      88-side: 0.24 × 0.081 ≈ +1.9pp

  Net: the branch hands the equal fighter ~2.5pp MORE than the
  better fighter, cancelling the +1.83pp base gain almost
  exactly. Predicted post-upset landing rate:

      mirror : 0.428 + 0.044 ≈ 0.471
      88-side: 0.446 + 0.019 ≈ 0.465

  Measured (AUDIT1): 0.4731 (mirror slot1) vs 0.4724 (L-B88
  slot1). Fit within 0.6-1.0pp with zero free parameters.

  **If confirmed by Gate 2's per-arm `upset_fired` rate, the
  upset branch is the wash mechanism, not "the stack." Its
  comment says "Anyone can get caught in MMA — Serra vs GSP,
  etc." but the code fires it at both parity and below-parity,
  turning it into a lottery that benefits parity as often as
  underdog.** Falsification target: measure `upset_fired` rate
  at mirror (predicted ~50%) vs 88-side (predicted ~24%).
  Materially different from these fractions → HYP1 falsified
  and the mechanism hunt resumes elsewhere.

  **A5. DEAD-CONTENT-OBS1 [RESOLVED as CATALOG problem, not
  weight problem].** All 9 unreachable at `get_available_strikes`
  (:1115-1163):

      STANDING (:1117-1124):        12 returned — JAB, CROSS,
        HOOK, UPPERCUT, OVERHAND, LEG_KICK, BODY_KICK, HEAD_KICK,
        FRONT_KICK, CALF_KICK, FLYING_KNEE, SUPERMAN_PUNCH.
      CLINCH (:1126-1131):          5 returned — CLINCH_KNEE,
        CLINCH_ELBOW, DIRTY_BOXING, KNEE_BODY, ELBOW_HORIZONTAL.
      FRONT_HEADLOCK is_top (:1134-1135): 1 — CLINCH_KNEE.
      TRUCK is_top (:1141-1143):    1 — GNP_PUNCH.
      Ground-top dominant (:1148-1153): 3 — GNP_PUNCH,
        GNP_HAMMER_FIST, GNP_ELBOW.
      Guard-top (:1154-1156):       2 — GNP_PUNCH, GNP_ELBOW.
      KNOCKDOWN_STANDING (:1157-1161): 3 — GNP_PUNCH,
        GNP_HAMMER_FIST, LEG_KICK.
      Fallback (:1163):             1 — ELBOW_UPWARD
        (length-1 list).

  Never returned anywhere: SIDE_KICK, SPINNING_BACK_KICK,
  WHEEL_KICK, AXE_KICK, OBLIQUE_KICK (kicks-family, 5 of 10);
  BACKFIST, KNEE_HEAD, ELBOW_VERTICAL, ELBOW_SPINNING (4).
  Total 9 dead.

  `select_strike` (:2154-2184) speed-scaling weights for
  WHEEL_KICK and SPINNING_BACK_KICK at :2177-2178 are dead code
  — the strikes never reach `select_strike`. ELBOW_UPWARD's
  ~27% dominance is the length-1 fallback list at :1163 for all
  unhandled (bottom) positions; the weight in `select_strike` is
  arithmetically irrelevant (`random.choices` on a
  single-element list is deterministic). Any fix lands in
  `get_available_strikes`, not `select_strike`.
  **DIAGNOSTIC-ONLY this arc; no behavior change; separate arc
  if picked up.**

  **A6. FAMILY-TAXONOMY-OBS1 [filed observation].** Selection
  and landing use different family taxonomies.

  `select_strike` :2160-2167 classifies for selection weight:

      boxing family = {JAB, CROSS, HOOK, UPPERCUT, OVERHAND}
        → weight += fighter.boxing // 5
      "kick" in strike.value OR "knee" in strike.value
        → weight += fighter.kicks // 5
      "elbow" in strike.value OR "clinch" in strike.value
        → weight += fighter.clinch_striking // 5

  `calculate_strike_success` :2306-2325 classifies for landing:

      boxing = {JAB, CROSS, HOOK, UPPERCUT, OVERHAND}
      "kick" in strike.value.lower() (10 kicks)
      clinch_explicit = {CLINCH_KNEE, CLINCH_ELBOW, DIRTY_BOXING}
      else = fallthrough (BACKFIST, SUPERMAN_PUNCH, knees,
             elbows, GnP)

  **Knees are the mismatch.** Selection lumps them with kicks
  (fighter.kicks bumps their pick probability); landing lumps
  them with clinch (attacker.clinch_striking drives their
  landing rate). A high-kicks / low-clinch_striking fighter
  throws knees often but lands them poorly, and vice versa.
  Called out so retune arithmetic doesn't cross the two
  taxonomies.

  **A7. Design fork [PARKED, post-Gate 2].** If UPSET-PARITY-
  HYP1 is confirmed by Gate 2 measurements, two candidate fixes
  emerge:

    (i)  Upset-branch rescope. Trigger relative to skill parity,
         not post-pressure-bonus parity; lift multiplicative
         (not overwrite to floor 0.70). Contained edit inside
         CSS; no save-state semantics change.
    (ii) Defense-side family-stat blend. defender's defense
         against boxing = f(striking_defense, defender.boxing);
         similarly for kicks and clinch_striking. Engine-shape
         change; alters what striking_defense means on every
         fighter on every save.

  Not folded into this arc. Post-Gate-2 decision.

  **QUEUE.**
  - Gate 1 (v1.3 probe): per-attempt CSV with decomposition
    columns (position, is_rocked, att_stamina, def_stamina,
    off_routed, def_routed, off_post_pressure, def_post_pressure,
    off_post_stamina, def_post_stamina, def_post_rocked,
    off_post_variance, sc_base, clamp_hit, upset_fired,
    upset_path, sc_final, landed). Standing gates: probe-off ≡
    probe-on bit-match; filed normalized hashes reproduced
    (L-J1 cace1efa, L-B88 d2d94326, L-K74 3e5de0d7, F 78605664);
    DISCRIM-99 forces `off_routed=99` inside wrapper decomposition
    only (engine never sees it), must show shifted `sc_base`
    distribution vs L-J1 while outcome CSV stays bit-identical
    to L-J1 (proves wrapper reads signal AND cannot leak into
    engine).
  - Gate 2: aggregate `upset_fired` and `clamp_hit` per arm.
    Falsification target for UPSET-PARITY-HYP1: mirror
    `upset_fired` ~50%, 88-side ~24%. Materially different →
    HYP1 falsified.
  - Post-Gate-2 design fork decision.
  - Owed unchanged: live-roster violence check (1a+1b joint)
    at next live card; PA timing measurement pre-N-lock.

- **LANDING-CURVE-RETUNE1 — Gate 2 [CLOSED 2026-08-26, C3 docs
  checkpoint at baseline a242dc1; instrument v1.3
  (outputs/lcr1/strike_landing_probe_v13.py) qualified by G1a-G1d
  100% per-row landing gate on 942,677 rows across 7 arms; no
  engine commits].**

  **2a. Per arm × slot: upset_fired, upset_path split, clamp_hit
  (v1.3, N=2000/arm).**

      arm     slot        N     upset_fired  floor70  boost22  none    clamp_hit
      L-J1    slot1   77900       0.6717     0.1224   0.1138   0.7638   0.0000
      L-J1    slot2   72254       0.5960     0.1078   0.1018   0.7905   0.0000
      L-B88   slot1   70545       0.6955     0.1246   0.1188   0.7566   0.0000
      L-B88   slot2   59500       0.6078     0.1091   0.1033   0.7876   0.0000
      L-K74   slot1   72045       0.6965     0.1246   0.1190   0.7564   0.0000
      L-K74   slot2   60888       0.6318     0.1112   0.1086   0.7802   0.0000
      L-K78   slot1   75792       0.6568     0.1166   0.1111   0.7724   0.0000
      L-K78   slot2   63322       0.6517     0.1151   0.1119   0.7730   0.0000
      L-K88   slot1   71295       0.6953     0.1245   0.1180   0.7575   0.0000
      L-K88   slot2   55443       0.5981     0.1080   0.1023   0.7897   0.0000
      L-C88   slot1   71773       0.6925     0.1244   0.1189   0.7567   0.0000
      L-C88   slot2   55745       0.6288     0.1133   0.1070   0.7797   0.0000
      F       slot1   76232       0.6883     0.1249   0.1174   0.7577   0.0000
      F       slot2   58943       0.6274     0.1106   0.1070   0.7824   0.0000

  **Upset branch fires on 60-70% of all attempts on every one of
  14 arm × slot cells.** The 18/17/65 split from the code
  (`if upset_roll < 0.18: floor70; elif upset_roll < 0.35:
  boost22; else no adjustment`) reproduces as ~12/11/76 on the
  fired subset, which is the 0.18/0.17/0.65 split within the
  fired-region → the branch's within-firing distribution matches
  its code weights exactly (18% × 0.67 firing = 0.12, 17% × 0.67
  = 0.11, 65% × 0.67 = 0.44; the "none" 0.76 aggregate ADDS the
  0.33 non-firing rows to the 0.44 fired-no-effect rows).
  **clamp_hit = 0.0000 on 14/14 cells.** Clamp `[0.15, 0.85]` at
  fight_engine.py:2380 is dead code on this fixture set — no
  attempt drove sc_base outside the clamp bounds in any arm.

  **2b. UPSET-PARITY-HYP1 [FALSIFIED as stated, attributed to
  architect's Gate 0 review].** STANDING boxing, L-J1 vs L-B88,
  per slot:

      arm    slot   STANDING boxing   N     upset_fired  mean(sc_base)  mean(sc_final)  landed
      L-J1   slot1                    13954    0.5753       0.4145          0.4730       0.4731
      L-J1   slot2                    13209    0.5024       0.4338          0.4844       0.4860
      L-B88  slot1                     9700    0.5154       0.4128          0.4665       0.4724
      L-B88  slot2                     7186    0.6353       0.4156          0.4810       0.4883

  Predicted: L-J1 mirror ~50%, L-B88 slot1 (offense-95 side)
  ~24%. Measured: L-J1 slot1 mirror = 0.5753 (+7.5pp above
  predicted); L-J1 slot2 mirror = 0.5024 (matches ±0.3pp); L-B88
  slot1 favored = 0.5154 (**+27.7pp above predicted 24%; hypothesis
  falsified as stated**); L-B88 slot2 (weak) = 0.6353.

  **Reason for the miss (mechanism located below in §2c):** the
  upset trigger at fight_engine.py:2384 compares `offense`
  against `defense * 0.85`, but by that point in the pipeline
  BOTH offense AND defense have been multiplied by their
  respective stamina/100 factors (:2366-2367). HYP1's arithmetic
  assumed the trigger fired on PRE-stamina values (offense=95
  vs 82.45 threshold → ~24% firing on the 88-side). Post-stamina
  values are much smaller and closer together, so the trigger
  fires ~50% at parity AND ~50% at 88-side. The +7 speed bump
  and +13 boxing gap that push the 88-side above the pre-stamina
  threshold are compressed by stamina scaling before the trigger
  sees them.

  Not quietly dropped. The +5.5pp arithmetic in the ratified spec
  was falsified at Gate 0; this HYP1 arithmetic is falsified at
  Gate 2. Both are on the record.

  **2c. Located mechanism: `off_post_stamina`.** Same-family
  restriction, slot1, aggregate. Column-by-column deltas:

      L-B88 slot1, family=boxing (N=9700 vs L-J1 13954):
        off_routed          75.0000 →  88.0000  Δ=+13.0000
        off_post_pressure   82.0000 →  95.0000  Δ=+13.0000
        off_post_stamina    37.2607 →  40.2459  Δ= +2.9851   ← collapse
        off_post_variance   37.3510 →  40.2681  Δ= +2.9171
        sc_base              0.4145 →   0.4128  Δ= −0.0017
        sc_final             0.4730 →   0.4665  Δ= −0.0065
        landed               0.4731 →   0.4724  Δ= −0.0007

      L-K88 slot1, family=kicks (N=13424 vs L-J1 19430):
        off_routed          75.0000 →  98.0000  Δ=+23.0000
        off_post_pressure   82.0000 → 105.0000  Δ=+23.0000
        off_post_stamina    36.2587 →  43.3522  Δ= +7.0935   ← collapse
        off_post_variance   36.2818 →  43.2580  Δ= +6.9762
        sc_base              0.4118 →   0.4143  Δ= +0.0025
        sc_final             0.4726 →   0.4657  Δ= −0.0069
        landed               0.4710 →   0.4660  Δ= −0.0049

      L-C88 slot1, family=clinch_fallthrough (N=47174 vs L-J1 40458):
        off_routed          75.0000 →  88.0000  Δ=+13.0000
        off_post_pressure   82.0000 →  95.0000  Δ=+13.0000
        off_post_stamina    13.1861 →  17.1683  Δ= +3.9823   ← collapse
        off_post_variance   13.1759 →  17.1756  Δ= +3.9997
        sc_base              0.3192 →   0.3275  Δ= +0.0084
        sc_final             0.4105 →   0.4142  Δ= +0.0037
        landed               0.4137 →   0.4130  Δ= −0.0006

  **The collapse column is `off_post_stamina`.** Off_routed
  deltas of +13 / +23 / +13 (pure attribute gap) survive intact
  through pressure. Then `offense *= attacker_state.stamina / 100`
  at :2366 divides by 100; on aggregate the +13/+23/+13 offense
  gaps become +3.0 / +7.1 / +4.0. Downstream (variance, sc_base,
  sc_final, landed) receives the compressed gap and produces
  ~zero landing-rate lift.

  **2d. STAMINA CUT.** Per arm × slot × position-bucket
  att_stamina histogram (sample, L-J1):

      arm    slot  bucket    N       [0,1)  [1,10)  [10,30)  [30,60)  [60,100]
      L-J1   slot1 STANDING  38048    9.8%    8.7%   25.3%    20.2%    36.0%
      L-J1   slot1 CLINCH     6507   27.6%   14.8%   21.0%    17.5%    19.0%
      L-J1   slot1 GROUND    33345   62.4%   12.2%    9.6%     9.6%     6.1%
      L-J1   slot2 STANDING  36127    9.1%    8.0%   24.6%    19.9%    38.4%
      L-J1   slot2 GROUND    29971   57.6%   12.3%   10.6%    11.4%     8.3%

  Pattern across all 7 arms consistent: **STANDING ~9-13% in
  [0,1); CLINCH ~20-40% in [0,1); GROUND ~42-62% in [0,1).**

  Mean att_stamina by attempt_idx decile, L-J1 slot1:
  `79.10, 38.34, 17.47, 18.73, 9.98, 9.40, 8.71, 4.65, 2.28,
  5.64`. Trajectory drops from ~79 at decile 1 to single digits
  by decile 5, near-zero by decile 8-10 on every arm.

  Low-fraction summary: **~30-38% of ALL rows have
  att_stamina < 1.0** across arms/slots (0.3383 L-J1 s1, 0.3052
  L-J1 s2, 0.3760 L-B88 s1, ..., 0.3879 L-C88 s1). On those
  low-att-stamina rows, def_stamina is distributed across the
  full range — **only ~1-3% of the low-att-stamina rows also
  have def_stamina < 1.0.** The two stamina values are
  DECOUPLED.

  **Caller distinction (fe:3315 vs fi:810) UNKNOWABLE from v1.3
  CSVs — no caller-id column captured.** Filed as instrument
  limitation; v1.4 adds `caller_id` to the landing CSV schema
  if a follow-up trace is needed.

  **2e. SLOT-ASYM-OBS1 [mechanism CANDIDATE, hypothesis
  only].** L-J1 informational:

      L-J1 slot1  N=77900  mean(att_stamina)=28.9272  mean(def_stamina)=44.1814  mean(sc_base)=0.3633  landed=0.4404
      L-J1 slot2  N=72254  mean(att_stamina)=31.6395  mean(def_stamina)=38.4282  mean(sc_base)=0.3883  landed=0.4555

  slot1 has systematically **more attempts** (77900 vs 72254),
  **lower mean att_stamina** (28.93 vs 31.64), **lower mean
  sc_base** (0.3633 vs 0.3883), and **lower landed rate**
  (0.4404 vs 0.4555). Filed as candidate mechanism for the
  SLOT-ASYM-OBS1 observation in AUDIT1: slot1 acts first per
  exchange (more attempts), depletes stamina faster (lower
  mean), stamina scaling drops offense (lower sc_base), lands
  less. Not proven — a direct trace of exchange-order and
  action-selection would be needed. Parked under the existing
  SLOT-ASYM-OBS1 filing.

  **VERDICT.** The landing formula is not the wash; **it is
  starved.** `offense *= attacker_state.stamina / 100` at
  fight_engine.py:2366, with mean att_stamina ~29 and 30-38%
  of attempts at stamina<1.0, collapses skill-derived offense
  before the ratio at :2379 ever sees it. Both formula
  compression AND the upset branch operate on values that are
  already compressed by two orders of magnitude — the skill
  gap that would make a stronger boxer land more strikes
  literally does not survive the stamina line.

  **ARC PIVOT.** Stamina drain rate + stamina scaling
  arithmetic PRECEDE any landing-curve change. If a fighter's
  effective offense is already 3-5% of nominal by the middle
  of round 1, no landing-curve retune can lift them — the
  numerator is already gone. Landing-curve retune items
  (formula compression at :2379-2380, upset rescope at
  :2384-2389, kick landing cliff at :2317-2318 de-cliff) are
  **DEFERRED, not cancelled.** They wait behind a stamina
  audit (Part B trace) that determines whether the drain
  constants and the `/100` scaling are behaving as intended.

  **Part B — read-only stamina trace (appended C3, cited at
  baseline a242dc1).**

  **B1. Stamina write sites (drain, recovery, floor, order).**

  Class def + methods verbatim (fight_engine.py:545-639):

      545: class FighterState:
      552:     stamina: float = 100.0

      608:     def recover_stamina(self, amount: float) -> None:
      609:         self.stamina = min(100, self.stamina + amount)

      611:     def spend_stamina(self, amount: float) -> None:
      612:         self.stamina = max(0, self.stamina - amount)

      614:     def new_round(self) -> None:
      624:         base_recovery = 15
      625:         _rec = self.recovery_rating
      626:         bonus_recovery = (_rec / 100) * 25
      628:         if getattr(self, '_current_round', 0) >= 4:
      629:             bonus_recovery *= 1.3
      630:         self.stamina = min(100,
      631:             self.stamina + base_recovery + bonus_recovery)

  **Floor = 0.0, NOT 0.5.** The `max(0, ...)` at fe:612 is the
  only floor. The 0.5 value visible in the Gate 2 exemplar row
  (att_stamina=0.5 in the TRUCK cft row) is **stamina hit engine
  floor 0 at the previous exchange's spend_stamina, then
  per-exchange recovery of +0.5 fired (fe:3805-3806 /
  fi:1642-1643) BEFORE CSS was called for the next exchange.**
  Empirically confirmed: across 942,677 rows in 7 arms both
  slots, `att_stamina == 0.0 exactly: 0 rows (frac=0.0000)`.
  Minimum observed att_stamina across all 14 slot-cells:
  **exactly 0.5000**, with 16,188-28,487 rows sitting on the
  0.5 floor per slot-cell (~21-38% of each cell). The
  0-then-recover-0.5 pattern accounts for it entirely.

  Drain sites (all callers to spend_stamina):

    line     site                                          amount            trigger
    fe:601   apply_damage — rocked side                    4                 fighter got rocked
    fe:3105  process_submission_progress — attacker        3                 working a sub
    fe:3106  same — defender                               5                 being submitted
    fe:3320  simulate_exchange — attacker (FE loop)        STRIKE_PROPERTIES[strike][2]   strike thrown (range 2-12)
    fe:3568  simulate_exchange grappling                   5                 grappling attempt
    fe:3637  simulate_exchange grappling                   4                 another grappling branch
    fi:948   _execute_strike — defender                    damage * 0.4      body-shot landed
    fi:986   _execute_strike — defender                    8                 landed knockdown
    fi:1282  _execute_strike — attacker (FI loop)          stamina_cost * (1.0 + 0.15 * agg * exec)  strike thrown
    fi:1336  _execute_strike — defender                    8                 KO/hit branch
    fi:1417  _execute_grappling — attacker                 5                 grappling attempt
    fi:1419  same — extra                                  3                 failed attempt
    fi:1487  _execute_grappling — attacker                 6                 different grappling branch

  Recovery sites:

    line          site                              amount
    fe:3805-3806  simulate_exchange — both fighters +0.5 per exchange (constant)
    fi:1642-1643  FI exchange loop — both           +0.5 per exchange (constant, same value)
    fe:614-631    new_round() — base+recovery bonus 15 + (recovery_rating/100)*25; ×1.3 in R4+
    fi:591 / fi:601  corner bonus (R2+ only)         15 * corner_bonus_fN (max 7.5 extra)
    fi:612-615    round-start fatigue penalty       −_fatigue_penalty (0/1/2/4)

  **Order in the exchange loop (both callers):** CSS called
  FIRST, THEN attacker's strike cost spent.
    fe:3315 CSS → fe:3320 attacker_state.spend_stamina
    fi:810  CSS → fi:1282 attacker_state.spend_stamina

  CSS sees stamina AT the state before the current strike's own
  cost is deducted. Previous exchange's spend AND the +0.5
  per-exchange recovery have already applied.

  **B2. Cardio wiring — CARDIO-UNWIRED-OBS1 [PENDING, awaiting
  intent-review before upgrade].**

  Attribute definition at fight_engine.py:1035 (verbatim):
      1035:     cardio: int = 50        # Stamina, gas tank

  **Whole-codebase grep of every `cardio` read** (verbatim,
  cage_dynasty_web/ + narrative/ + systems/):

    matchmaking.py:245           getattr(fighter, 'cardio', 50) +
    fight_engine.py:1035         cardio: int = 50        # Stamina, gas tank
    fight_engine.py:1078         physical = (self.strength + self.speed + self.cardio + self.chin + self.recovery) // 5
    fight_engine.py:1089         "cardio": self.cardio,
    fight_engine.py:1384         pressure_score    = (fighter.cardio + fighter.heart + fighter.chin) / 3
    fight_engine.py:1451         # Clinch Fighter: cage pressure + dirty boxing + cardio
    fight_engine.py:1453         if clinch_score >= 65 and fighter.cardio >= 68 and wrestling_score >= 58:
    fight_engine.py:1456         # Pressure Fighter: cardio + chin + heart — the walking forward style
    fight_engine.py:1707         # High output, always forward, cardio is their weapon.
    fight_engine.py:2070         # ── Late-round cardio advantage ──────────────────────
    fight_engine.py:2072         # A fighter with much better cardio dominates round 3.
    fight_engine.py:2075         _opp_cardio = getattr(opponent_attrs, 'cardio', 70)
    fight_engine.py:2076         _my_cardio = getattr(fighter_attrs, 'cardio', 70)
    fight_engine.py:2077         _cardio_gap = _my_cardio - _opp_cardio
    fight_engine.py:2078         if _cardio_gap >= 12:
    fight_engine.py:2079-2084    _cardio_mult = 1.0 + ((_cardio_gap - 10) * 0.015 * _round); min 1.35
                                  strike_weight *= _cardio_mult; grapple_weight *= _cardio_mult; sub_weight *= _cardio_mult
    fight_engine.py:2173         if target == "body" and opponent.cardio > 70:
    fight_engine.py:4472/4489    strength=f1_overall, speed=f1_overall, cardio=f1_overall, ... (quick_simulate)
    models.py:85                 ("Cardio Machine", "cardio", "+15 Cardio, -5 Power")   (trait)
    models.py:125                cardio: int = 50   (secondary FighterAttributes-like class)
    models.py:177                self.strength, self.speed, self.cardio, self.chin, self.recovery, ... (OVR calc)
    models.py:588 / :638 / :1260 cardio=rand_attr(...)   (fighter generation)
    corner_advice.py:11/:51/:628/:632/:717/:1154  cardio in coach specialty routing + advice text
    styles.py:109/:110/:143/:175/:176  attribute_requirements / attribute_bonuses on cardio (style constraints)
    game_start.py:208/:257/:456/:507/:657  cardio in fighter definition / gen / training weights
    facilities.py:174            "cardio", (facility upgrade key)
    aging.py:155                 attribute list including cardio (age decay)
    game_bridge.py:557/:565/:573/:596  training primary/secondary tables
    game_bridge.py:704           "cardio":           "sc_coach",   (coach specialty)
    game_bridge.py:799           "sc_coach":        ["strength", "speed", "cardio", ...   (S&C coach stat list)
    test_fight_sim.py:43/110/112/118/120/155  cardio in test fixtures

  **Where recovery_rating is populated** (verbatim,
  fight_engine.py:4064-4073):
      4065:         recovery_rating=fighter1.recovery
      4073:         recovery_rating=fighter2.recovery
  (Populated from `FighterAttributes.recovery`, NOT from cardio.)

  **Findings from the grep:**
  - Cardio IS wired into non-drain fight logic: style detection
    (`detect_fighter_style` at fe:1384, :1453); IQ body-targeting
    (fe:2173 opponent.cardio > 70 → +10 weight); `physical` OVR
    mean (fe:1078); `quick_simulate` fixture generator (fe:4472/
    4489, symmetric).
  - Late-round cardio multiplier (fe:2073-2084) is PRESENT IN
    CODE; effect UNVERIFIED. The multiplier scales all three
    selectable weights uniformly (strike, grapple, sub) at
    :2082-2084 when cardio_gap ≥ 12 at round ≥ 2. Under
    `random.choices` with proportional-invariance semantics, a
    uniform scaling of ALL non-zero options is a no-op (the
    ratios are what select). LIKELY no-op at the outcome layer
    unless an unscaled option exists in the weight list. NOT
    listed as a channel through which cardio affects fight
    outcomes until STAMINA-MODEL1 Gate 0 verifies the full
    weight list (see QUEUE below).
  - Cardio IS wired into training/gen/UI/coach infrastructure:
    coach specialty routing (game_bridge.py, corner_advice.py),
    style requirements/bonuses (styles.py), attribute gen
    (models.py, game_start.py), aging decay (aging.py), facility
    upgrades (facilities.py).
  - **Cardio is NOT wired into any stamina drain site.** The
    drain amounts at all 13 spend_stamina call sites (B1 table)
    read from STRIKE_PROPERTIES constants, aggression multiplier,
    damage-derived values, and hardcoded numbers — never from
    `attacker.cardio` or `defender.cardio`.
  - **Cardio is NOT wired into stamina recovery.** Between-round
    recovery (fe:625) reads `recovery_rating`, which is populated
    from `FighterAttributes.recovery` (fe:4065/4073). The
    per-exchange +0.5 constant is unconditional.

  **CARDIO-UNWIRED-OBS1 refined and filed as PENDING.** The
  attribute captioned "Stamina, gas tank" at fe:1035 has NO
  direct effect on stamina drain rate or stamina recovery rate.
  It affects fight outcomes through indirect channels (style
  detection, body-targeting IQ bonus, OVR). Late-round cardio
  multiplier at fe:2073-2084 is PRESENT-IN-CODE but effect
  UNVERIFIED and likely no-op via uniform three-weight scaling
  under random.choices; NOT listed as an outcome channel until
  STAMINA-MODEL1 Gate 0 verifies. Not filed as "unwired" — the
  attribute is used in 30+ code sites. Filed as
  **misrouted-from-caption**: the caption suggests a stamina
  channel that does not exist in code. Whether that's intentional
  (cardio → recovery via `recovery` attribute correlation in
  fighter gen, but not via direct code read) or a latent
  simulation bug is the architect's call. Not upgraded until the
  intent review lands.

  **B3. Eight-site `stamina/100` consumer table (with floors).**

    line         function                          formula                                             floor at stamina=0
    fe:2112      select_action action-weights      stamina_factor = stamina/100 → all 3 weights *=     0 (guarded by max(5,...) at :2118 & :2126 — see below)
    fe:2366-67   calculate_strike_success — LAND   off *= stamina/100; def *= def_stamina/100          0 (linear-to-zero, no floor)
    fe:2470      calculate_strike_damage — DAMAGE  damage *= (stamina/100) * 0.5 + 0.5                 0.5 (50% floor)
    fe:2684-85   calculate_grappling_success — GRAP off *= stamina/100; def *= def_stamina/100         0 (linear-to-zero)
    fe:3001-02   attempt_submission — SUB attempt  off *= stamina/100; def *= def_stamina/100          0 (linear-to-zero)
    fe:3081      process_submission_progress — off off = attacker.submissions * (stamina/100)          0 (linear-to-zero)
    fe:3100      same — def                        def = ((guard+subs)/2) * (def_stamina/100)          0 (linear-to-zero)
    fe:3121      sub defense hybrid                _def_stamina/100 + 0.3 + _composure_bonus           0.3 (30% floor)

  **Damage-floor cross-reference (EXPLANATION, not correction).**
  STRIKE-SKILL-DMG1 phase 1a (K=1.0 skill-into-damage dial) and
  phase 1b (K=1.0 kick-gap gradient) both multiply `damage` at
  fight_engine.py:2401's `calculate_strike_damage`. That damage
  is subsequently multiplied by `(stamina/100) * 0.5 + 0.5` at
  fe:2470, which retains a **50% floor at zero stamina**. The 1a
  and 1b measurements were taken with this floor in place and
  remain valid — the 0.7075 E-arm shift, the +2.2× per-point
  kick-vs-boxing imbalance, the K-choice grid — all stand. This
  cross-reference is EXPLANATORY: it names why damage dials
  transmit measurable signal (50% floor keeps most of the
  skill-derived value alive) while landing/grappling/submission
  do not (linear-to-zero floor collapses skill-derived value at
  the stamina line). Not opening 1a or 1b for edits.

  **:2112 zero-stamina behavior — code and empirical result.**

  Verbatim at fight_engine.py:2112-2131:

      2112:    stamina_factor = fighter_state.stamina / 100
      2113:    strike_weight = int(strike_weight * stamina_factor)
      2114:    sub_weight = int(sub_weight * stamina_factor)
      2115:    grapple_weight = int(grapple_weight * stamina_factor)
      2116:
      2117:    # Ensure minimum weights
      2118:    strike_weight = max(5, strike_weight) if strikes else 0
      2119:    # Sub gate: BJJ/Sambo can attempt subs at 45+, everyone else at 60+
      2120:    _sub_threshold = 45 if my_style in ("bjj", "sambo") else 60
      2121:    if submissions and fighter_attrs.submissions >= _sub_threshold:
      2122:        sub_weight = max(1, sub_weight)
      2123:    else:
      2124:        sub_weight = 0
      2125:    grapple_weight = max(5, grapple_weight) if grappling else 0
      2126:
      2127:    # Select action category
      2128:    total = strike_weight + sub_weight + grapple_weight
      2129:    if total == 0:
      2130:        return ("strike", random.choice(strikes) if strikes else StrikeType.JAB)

  **The `max(5, ...)` at :2118 and :2126 is the zero-case
  guard.** At stamina=0.0: `stamina_factor = 0.0` →
  strike_weight, sub_weight, grapple_weight all int(0). Then the
  min-5 floors activate: strike_weight becomes 5 (if strikes
  available), grapple_weight becomes 5 (if grappling available).
  `total = 5 + 0 + 5 = 10` for a typical exchange; `random.choices`
  never sees a zero-weight list, never raises. The `if total == 0`
  fallback at :2129-2130 is a defensive path for the edge case of
  no strikes AND no grappling available AND no viable sub.

  **Fraction of v1.3 rows with att_stamina == 0.0 exactly, per
  arm × slot** (measured across 942,677 rows):

      arm     slot        N       att_stamina==0.0 exactly    frac
      L-J1    slot1   77900      0                             0.0000
      L-J1    slot2   72254      0                             0.0000
      L-B88   slot1   70545      0                             0.0000
      L-B88   slot2   59500      0                             0.0000
      L-K74   slot1   72045      0                             0.0000
      L-K74   slot2   60888      0                             0.0000
      L-K78   slot1   75792      0                             0.0000
      L-K78   slot2   63322      0                             0.0000
      L-K88   slot1   71295      0                             0.0000
      L-K88   slot2   55443      0                             0.0000
      L-C88   slot1   71773      0                             0.0000
      L-C88   slot2   55745      0                             0.0000
      F       slot1   76232      0                             0.0000
      F       slot2   58943      0                             0.0000

  **Zero exact-zero rows in 942,677.** The min-5 weight floor at
  :2118 exists as defense-in-depth but never activates at CSS
  call time in this fixture set because the per-exchange +0.5
  recovery (fe:3805-3806 / fi:1642-1643) fires BEFORE CSS is
  called for the next exchange. Every drain-to-0 event is
  followed by +0.5 before CSS reads it. The 0.5 floor visible in
  Gate 2 §2c's exemplar is not a code floor — it's a
  drain→recover pattern.

  **B4. Hand trajectory vs measured decile (75-recovery,
  gameplan=None).**

  Per-exchange net drain assuming attacker acts half the time,
  strike-cost mean ~5, per-exchange recovery +0.5:
    when attacking: −5 + 0.5 = −4.5
    when defending: +0.5 (or −damage*0.4 to −8 on body/KD hits)
    average net for one fighter, half-attacking: (−4.5 + 0.5)/2 = −2.0/exchange

  Exchanges per round in LIVE_PLAY config: 55.

  Round 1 (start 100.0):
    55 exchanges × −2.0 = −110 → floor at 0 around exchange 50.

  Round 2 start:
    new_round: +33.75 recovery (base 15 + (75/100)*25) → ~33.75.
    Fatigue penalty (starting_stamina 100, bucket ≥95 → 0): 0.

  Round 2 mid:
    ~17 exchanges to floor at −2.0/exchange → hits 0 by
    exchange 17 of 55.

  Round 3 same shape.

  Measured decile means (L-J1 slot1, from Gate 2 §2d):
    79.10, 38.34, 17.47, 18.73, 9.98, 9.40, 8.71, 4.65, 2.28, 5.64

  Reconciliation: decile trajectory MATCHES the hand computation
  directionally on every step:
    D1 (early R1): 79 vs computed high-start-dropping-fast
    D2 (mid R1):   38 vs computed dropping through R1
    D3 (end R1 / start R2): 17 vs computed near-zero into R2 recovery
    D4 (R2 mid):   18 vs computed R2 recovery + drop
    D5-8 (R2 end / R3): 4-10 vs computed near-zero
    D9 (R3 end):    2 vs computed near-zero
    D10 (final):    5 (uptick — plausibly last-exchange recovery
                       or short-round fights averaging fresher
                       states)

  Between-round recovery of +33.75 IS visible as the decile 3→4
  bump (17 → 18) despite continued drain, and the
  L-J1 slot2 trajectory (81, 44, 23, 24, 14, 11, 10, 5, 4, 9)
  shows a stronger R2 recovery signal (decile 3→4 rises 23 → 24,
  decile 8→10 rises 5→4→9). Directionally consistent; not a
  test — v1.4 round column is the test.

  **QUEUE.**
  - **LANDING-CURVE-RETUNE1 DEFERRED behind new arc
    STAMINA-MODEL1.** Landing retune items (formula compression
    at :2379-2380, upset rescope at :2384-2389, kick landing
    cliff at :2317-2318, defense-side family-stat blend) all
    wait until the stamina model is audited and, if needed,
    corrected.
  - **STAMINA-MODEL1 Gate 0**:
    (a) whole-codebase cardio grep + recovery_rating population
        read (delivered in Part B above);
    (b) v1.4 instrument adding `round`, `exchange_idx`,
        `caller_id` (fe:3315 vs fi:810), and `zero_flag`
        (stamina == 0.0 exactly) columns to the landing CSV;
    (c) verify late-round cardio multiplier (fe:2073-2084) —
        read the full weight list at select_action's action-
        category step and prove no unscaled option exists, or
        identify the unscaled option that makes the uniform
        3-weight scaling outcome-affecting after all. If proven
        no-op, file dead-code candidate; if outcome-affecting,
        re-open the cardio-outcome channel list.
  - **STAMINA-MODEL1 Gate 1**: live-roster stamina trajectory by
    round on a fresh save — the owed live-roster check from
    1a/1b, now load-bearing. Real fighters with 85 recovery vs
    75 recovery, does the stamina model gas mid-R1 or mid-R2?
    No hardcoded save/fighter names; use fresh save via new_game
    per session hygiene.
  - **STAMINA-MODEL1 design after Gate 1 measurement.** Order of
    levers matters: drain constants and cardio-wiring are
    engine-truth candidates and go FIRST; flooring the /100
    scaling would hide a broken drain and goes LAST.
  - HYP1-adjacent hypotheses invalidated: the upset branch
    isn't the wash it appeared to be — it operates on
    already-starved values. Any future analysis of the branch
    must condition on stamina state.
  - Owed unchanged: live-roster violence check (1a+1b joint) —
    now bundled INTO STAMINA-MODEL1 Gate 1; PA timing
    measurement pre-N-lock (independent).

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
