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

**[SUPERSEDED 2026-09-07 — see mechanism of record below.]**

**Mechanism of record (2026-09-07 interim deploy onward):** console
`git pull --ff-only` from `~/cage_dynasty` (repo root; NOT
`cage_dynasty_web`) + PA API POST `/webapps/<domain>/reload/`. `deploy.sh`
webhook is fallback, never proof. Full procedure + raw output:
`claude/interim_deploy_2026-09-07.md`.

**Standing gates (2026-09-07 onward, before every deploy):**
- **G0. Template compile sweep** N/N clean required
  (`python3 -u claude/tools/template_compile_sweep.py` from repo root).
  Detail: `claude/interim_deploy_2026-09-07.md`.
- **G1. PA console CPU quota** 100 s/day (Hacker tier); console harness
  runs CPU-metered, web-app requests unmetered. N≥500-on-PA RETIRED
  (Van 2026-09-07). Detail: `claude/interim_deploy_2026-09-07.md`.
- **G2. Deploy mechanism recorded verbatim** in every deploy filing.
  Template: `claude/interim_deploy_2026-09-07.md`.

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

<!-- ARCHIVE3 --> The live backlog is `claude/backlog.md` (disk canonical, edited in place). Read it before scoping any docket. Moved verbatim from here at f9b1b8a (md5 0062f1d92a7116dead4842959130cc88, 524 lines).
<!-- ARCHIVE3 --> Next in order (Van's ruling 2026-09-08): WEEK-AXIS1 Gate 0 (read-only) → PROSPECT-BONUS1 instrument rule (tools commit, own stop) → PROSPECT-BONUS1 retune (balance-touching, own stop). Behind: see the board.

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
- **Bare-import shadow census (dev C40 PYTHONPATH, `narrative:systems:cage_dynasty_web`).**
  A bare `import fight_engine` from repo CWD before `game_bridge` runs its
  `sys.path.insert` + force-delete fixup at `game_bridge.py:190-199` finds
  the WRONG copy. Two shadow candidates, not one:
  - `fight_engine.py` (repo root) — default triple `(55, 0.70, 6)` (dm=0.7).
    CLAUDE.md's original hazard note (see below) named this one.
  - `systems/fight_engine.py` (repo top-level, CLI copy) — default triple
    `(80, 0.43, 6)` (exchanges=80, dm=0.43). Measured 2026-09-07 by the
    step-2 preamble in `outputs/sm1/deploy1/step1_2_report.md`; a preamble
    that imported `fight_engine` before `game_bridge` bound to this file.
  game_bridge's fixup defeats both on the live app. Any diagnostic or
  harness must import `game_bridge` first, THEN read
  `sys.modules['fight_engine']` — never bare-import `fight_engine`. On PA
  the fixup + WSGI's non-repo-root sys.path insulate both shadows; on dev
  the C40 PYTHONPATH exposes them.
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
  **[SUPERSEDING, 2026-09-07 interim deploy — the 2026-08-15 STRIKE's
  "PA measured 610 bytes" claim is FALSE at HEAD. PA `wsgi.py` measured
  **479 bytes** this pass (md5 `91531930abb2f818ccc21cad7b6c6386`); repo
  `cage_dynasty_web/wsgi.py` is 610 bytes. The 131-byte delta is
  comments + whitespace only; functional `sys.path.insert` lines are
  byte-identical between PA and repo. This exactly matches the 2026-08-20
  correction filed at
  `claude/claude_md_archive_2026b.md:379-407` (`### wsgi-610` re-measured);
  the 2026-08-15 STRIKE was an intermediate observation superseded 5 days
  later and not corrected here until now. sys.path insertion order and
  bare-import resolution behavior UNCHANGED-IN-EFFECT (independently
  re-verified 2026-09-07 for fight_engine + fight_integration +
  commentary resolutions in `outputs/sm1/deploy1/step1_2_report.md` +
  `outputs/sm1/deploy1/pa_wsgi_verbatim.txt`). Full filing:
  `claude/interim_deploy_2026-09-07.md`.]
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

Standing rule (C46 SAVELOAD1, 2026-09-06):
**Config verifies OBSERVE (wrap-log with caller attribution);
never IMPOSE (mutate).** A verify that monkey-patches
`FightConfig.__init__` to force a value can't observe hard
pins; C45's P3 verify made that error and hid the drift the
T5 spot-check later found. Reference OBSERVE shape (committed
into the repo at C47 per Van ruling R2 so the rule is not
wired-to-nothing): `claude/tools/config_observe_harness.py`.
It wraps `FightConfig.__init__` in an observer that logs
`(exchanges, dm, standup)` + caller-frame identity, then calls
the original. Full detail in CLAUDE.md's C46 filing block.

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

See `claude/backlog.md` for the live backlog board (moved out 2026-09-09 by ARCHIVE3; rewritten 2026-07-03 prior). <!-- ARCHIVE3 -->
The April-May items previously listed here (FOTN wire, fighter profile polish,
card-builder slot assignment) all shipped and were removed to prevent stale
references. Historical ship recaps are in `CLAUDE_archive.md`.

## Key constants (don't change without telling me)

**Truth at HEAD** [MEASURED, sourced to STAGE 0d `ba8cece` 2026-07-12,
correction-layer narrative retained; C45–DEAD_042_STRIP updates applied
in-place per the false-numbers-documented-as-false rule]**:** live-play
per-strike damage scale is `self.config.damage_multiplier`, read live in
the strike-damage path (currently `fight_integration.py:867`). The
`FightConfig.damage_multiplier` dataclass field defaults to `0.48`
[FALSE since C45 `a4fe627` — measured default 0.24 at `b824a42`;
retained for provenance] (currently `fight_engine.py:798`). The value
the config carries is
pinned by the atomic-config-invariant contract via `_SANCTIONED_TRIPLES`
(currently `fight_engine.py:1317-1319`) to the single surviving triple
`{(55, 0.24, 10)}`. `_TRIPLE_LIVE_PLAY = (55, 0.24, 10)` is annotated as
"the surviving contract" in the `_SANCTIONED_TRIPLES` set (currently
`fight_engine.py:1318`), promoted from the pre-Group-A value at C45
`a4fe627`. The 0.48 value survives 0d by design [FALSE since C45
`a4fe627` — measured default 0.24 at `b824a42`; retained for
provenance] — the read site's own comment (currently
`fight_integration.py:866`) states "Byte-identical to the pre-0d
FI_DAMAGE_MULTIPLIER=0.48." Every line reference above is
tagged "currently" because line numbers drift; the identity of each
fact is its symbol (`config.damage_multiplier`, `FI_DAMAGE_MULTIPLIER`,
`_SANCTIONED_TRIPLES`, `_assert_sanctioned_config`, `_TRIPLE_LIVE_PLAY`,
`FightConfig.damage_multiplier`).

**Retired triples (kept for reader trust; do not re-introduce):**
- `(55, 0.48, 10)` — was `_TRIPLE_LIVE_PLAY` pre-Group-A; FALSE at C45
  `a4fe627` (Van ruled dm 0.48 → 0.24). Kept briefly as
  `_TRIPLE_LIVE_PLAY_LEGACY_C45` in the allowlist; dropped at C46
  `612f918` when the T5 spot-check found all 5 remaining constructors
  were drift-pins, not deliberate legacy.
- `(55, 0.48, 6)` — was `_TRIPLE_FI_FALLBACK`; dropped at C46 `612f918`
  alongside the LEGACY_C45 entry (the 4 fi drift-pins at fi:420 +
  fi:2670/2679/2687 were converted to inherit defaults).
- `(55, 0.42, 6)` — was `_TRIPLE_PRE_GEN_LEGACY`; deleted at
  DEAD_042_STRIP `b824a42` (2026-09-07) with the two dead constructors
  (`FightConfig.main_event()`, `quick_simulate()`) that were its only
  producers by grep and by 20-week observation.

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

- Measurement hazard — runtime-rebind sweeps vs source literals [filed 2026-08-14, AMP-RECONCILIATION arc, dec968b] → `claude/claude_md_archive_2026b.md` : L7-38 <!-- ARCHIVE2 -->
- Site-3293 census — scope correction [filed 2026-08-14, AMP-RECONCILIATION arc, dec968b] → `claude/claude_md_archive_2026b.md` : L39-51 <!-- ARCHIVE2 -->
- STAGE 2a addendum — amp placement + FE-defined/FI-consumed constants [filed 2026-08-14, AMP-RECONCILIATION arc, dec968b] → `claude/claude_md_archive_2026b.md` : L52-63 <!-- ARCHIVE2 -->
- Architecture correction — top-level `systems/` imports [filed 2026-08-15, FOTN full-fidelity wire, 8fd4573] → `claude/claude_md_archive_2026b.md` : L64-83 <!-- ARCHIVE2 -->
- Regression + doc-hygiene sweep — post-`68dbd52` [filed 2026-08-15] → `claude/claude_md_archive_2026b.md` : L84-445 <!-- ARCHIVE2 -->
- Belt-marker diagnostic — 3 sources + Bug X/Y split [filed 2026-08-19] → `claude/claude_md_archive_2026b.md` : L446-574 <!-- ARCHIVE2 -->
- MC ODDS — SPEC (Phase 3 step 2, pre-implementation) [filed 2026-08-18] → `claude/claude_md_archive_2026b.md` : L575-722 <!-- ARCHIVE2 -->
- MC ODDS — SHIPPED (Phase 3 step 2) [ratified 2026-08-19, code `4ef0bd4`] → `claude/claude_md_archive_2026b.md` : L723-827 <!-- ARCHIVE2 -->
- FILED OBSERVATIONS (from MC ODDS ship 2026-08-19, code `4ef0bd4`) → `claude/claude_md_archive_2026b.md` : L828-1932 <!-- ARCHIVE2 -->
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


- FIGHT MODEL P5-A FINISH MODEL [COMMITTED as C29, 2026-09-05] → `claude/claude_md_archive_2026b.md` : L1933-2183 <!-- ARCHIVE2 -->
- FIGHT MODEL P5-B1 — D17 STAMINA FLOOR + D18 POWER MODEL [COMMITTED as C30, 2026-09-05] → `claude/claude_md_archive_2026b.md` : L2184-2457 <!-- ARCHIVE2 -->
- FIGHT MODEL STYLECOHERENCE1 [COMMITTED as C31, 2026-09-05] → `claude/claude_md_archive_2026b.md` : L2458-2724 <!-- ARCHIVE2 -->
- FIGHT MODEL P5-B3 [COMMITTED as C32, 2026-09-05] → `claude/claude_md_archive_2026b.md` : L2725-2982 <!-- ARCHIVE2 -->
- FIGHT MODEL P5-B4 [COMMITTED as C33, 2026-09-05] → `claude/claude_md_archive_2026b.md` : L2983-3169 <!-- ARCHIVE2 -->
- GENERATOR1 DOCS INTO GIT [COMMITTED as C34, 2026-09-05, docs-only] → `claude/claude_md_archive_2026b.md` : L3170-3204 <!-- ARCHIVE2 -->
- GENERATOR1 PHASE A [COMMITTED as C35, 2026-09-05] → `claude/claude_md_archive_2026b.md` : L3205-3312 <!-- ARCHIVE2 -->
- GENERATOR1 PHASE B [COMMITTED as C38, 2026-09-05] → `claude/claude_md_archive_2026b.md` : L3313-3486 <!-- ARCHIVE2 -->
- GENERATOR1 PHASE C [COMMITTED as C39, 2026-09-05] → `claude/claude_md_archive_2026b.md` : L3487-3675 <!-- ARCHIVE2 -->
- GENERATOR1 PHASE D [COMMITTED as C40, 2026-09-05] → `claude/claude_md_archive_2026b.md` : L3676-3806 <!-- ARCHIVE2 -->
### LOCAL PLAYTEST COMMAND (verified C40, 2026-09-05)

```
PYTHONPATH="/Users/vandope/Desktop/Games/cage_dynasty/narrative:/Users/vandope/Desktop/Games/cage_dynasty/systems:/Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty_web" python3 /Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty_web/app.py
```

Open `http://localhost:5001/` (root redirects to `/new-game`).

**PYTHONPATH is load-bearing.** Without it, the `SIMULATION-SHIM`
warning fires (`🚨 world_init.FULL_ENGINE_AVAILABLE will be False`)
and pre-gen falls back to `simulate_fight_simple` — the crude 74%-
clamped fallback that produces near-random champions and belt
lineages. The Phase B/C population Van shipped only appears when
the PYTHONPATH is set correctly so `commentary` resolves via
`narrative/`, `systems.injury` resolves via `systems/`, and the
web tree's `fight_engine`/`fight_integration` load into
`simulation.*` via the shim. Verified this session — with the
PYTHONPATH set, boot log shows `✅ [IMPORT-PATH-PROOF]` for all
three plus `✅ Real game modules loaded successfully!`.

Ctrl-C stops the server (or `pkill -f "python3.*app.py"`).


- C41 [COMMITTED as C41, 2026-09-05] — badge/identity-trait dedupe + amateur random stat-traits removed → `claude/claude_md_archive_2026b.md` : L3807-3868 <!-- ARCHIVE2 -->
- C42 [COMMITTED as C42, 2026-09-05] — life-sim design filings → `claude/claude_md_archive_2026b.md` : L3869-3944 <!-- ARCHIVE2 -->
- C43 [COMMITTED as C43, 2026-09-05] — P5-C calibration spec ratified + list reconciliation → `claude/claude_md_archive_2026b.md` : L3945-4009 <!-- ARCHIVE2 -->
- C44 [COMMITTED as C44, 2026-09-05] — P5-C Phase 0 COMPLETE (baseline of record + Van rulings + GAMEPLAN1 / PROTRAIT1) → `claude/claude_md_archive_2026b.md` : L4010-4121 <!-- ARCHIVE2 -->
- Van P5-C RULINGS (2026-09-05, filed) → `claude/claude_md_archive_2026b.md` : L4122-4137 <!-- ARCHIVE2 -->
- Scope-doc backlog additions (this ship) → `claude/claude_md_archive_2026b.md` : L4138-4197 <!-- ARCHIVE2 -->
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


- GROUP A — FINISH ECONOMY LANDED [COMMITTED as C45, 2026-09-06] → `claude/claude_md_archive_2026b.md` : L4198-4365 <!-- ARCHIVE2 -->
- C45 REFUTATION LEDGER → `claude/claude_md_archive_2026b.md` : L4366-4434 <!-- ARCHIVE2 -->
- MODULE-RELOAD1 (harness-pattern note, NOT scheduled) [filed C45] → `claude/claude_md_archive_2026b.md` : L4435-4468 <!-- ARCHIVE2 -->
- SUB-DRIFT → Group D (handoff from C45) → `claude/claude_md_archive_2026b.md` : L4469-4496 <!-- ARCHIVE2 -->
- C46 [COMMITTED as C46, 2026-09-06, engine only] — SAVELOAD1 T5: drop drift dm=0.48 pins + retire two triples → `claude/claude_md_archive_2026b.md` : L4497-4703 <!-- ARCHIVE2 -->
- INTERIM DEPLOY 2026-09-07 — b6e1d74 deployed, TPLFIX `f113004` follow-up → `claude/interim_deploy_2026-09-07.md`

**Number-of-record corrections (2026-09-07 interim deploy):**
- Handoff body's "6,217 lines at C47" is **FALSE**. True count is
  **6226** (`git show 62d3fc6:CLAUDE.md | wc -l`). ARCHIVE2's
  measurement was right; the handoff drift is filed only, not fixed
  in that doc (it's frozen-in-time thread state per its own header;
  the correction lives here + in `claude/interim_deploy_2026-09-07.md`).

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

- `claude/claude_md_archive_2026a.md` — pre-fight-model-arc history (created 2026-09-05, C28/ARCHIVE1) <!-- ARCHIVE2 -->
- `claude/claude_md_archive_2026b.md` — C22–C46 shipping filings (created 2026-09-07, ARCHIVE2; 30 blocks, in-place pointers tagged <!-- ARCHIVE2 -->) <!-- ARCHIVE2 -->
- `claude/backlog.md` — LIVE backlog board (ARCHIVE3, 2026-09-09; moved verbatim from CLAUDE.md Top-of-backlog at f9b1b8a; edited in place thereafter) <!-- ARCHIVE3 -->
- `claude/interim_deploy_2026-09-07.md` — interim deploy filing (b6e1d74 deploy proof triad, 5b probe, PA-SMOKE1 5a, perf hypothesis, TPLFIX regression, power finding, token breach, N≥500-on-PA retirement)
- `claude/gate0_baselines_2026-09-07.md` — Gate 0 baselines at cf2fecf: week-axis, creation path, camp-vs-safety (measured; rulings 1–4)
- `claude/player_create1_filing_2026-09-08.md` — PLAYER-CREATE1 shipping filing: three commits, gates, baseline move, six findings (2026-09-08)
- `claude/deploy3_2026-09-08.md` — Deploy #3 (PLAYER-CREATE1 to PA) filing: mechanism, proof triad at 7555c35, browser check week 0→1, TOKEN-HYGIENE1.
- `claude/playtest_notes_2026-09-07.md` — architect playtest notes on b6e1d74 (Van's first browser session, 19 items, 3 measured)
- `claude/tools/template_compile_sweep.py` — deploy-time standing gate (N/N template compile check; ships with the 2026-09-07 DOCS commit)
- `claude/tools/{_harness_env,save_invariants,dev1_gate0,phase2_holes}.py` — SAVE-INVARIANTS1 checker (--dump/--save replay) + DEVELOPMENT1 Gate 0 probes; standing before/after instruments for PLAYER-CREATE1 and WEEK-AXIS1
Detailed ship recaps from before 2026-05-23 live in `CLAUDE_archive.md`
at the project root. That file is for historical reference — Claude
Code does not auto-load it. Open it manually when researching past
ships' diagnosis details or architectural patterns.
