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

#### wsgi-610 [MEASURED, filed 2026-08-15]

**PA `/var/www/vandopegaming_pythonanywhere_com_wsgi.py` is 610
bytes at HEAD, contradicting CLAUDE.md's 2026-07-07 "VERIFIED match
... 479 bytes" claim.** Measured this pass. The +131-byte delta is
not audited yet; not blocking (module-load prints on PA still
resolve to expected paths — bare `import commentary` still hits
`narrative/commentary.py`, `importlib.import_module("fotn")` still
hits `systems/fotn.py`, per verifications since 2026-07-07 that
continue to hold). Hand-diff on PA when convenient.

**Strike-and-preserve applied** to the `## Architecture / Known
hazards` bullet claiming byte-equivalence — the byte-equivalence
claim is retired for the current PA wsgi.py; the sys.path insertion
order and bare-import resolution behavior claims following it
remain UNCHANGED-IN-EFFECT. The file has grown; its role has not.

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
