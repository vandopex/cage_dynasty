# INTERIM DEPLOY — 2026-09-07 (b6e1d74)

First deploy since the S2 freeze. Van-ruled exception at C47 (option b).
Deploy accepted on proof by Van 2026-09-07 after step-4 triad + 5b.
Mechanism ruled: console `git pull --ff-only` from `~/cage_dynasty` +
PA API reload. NOT `deploy.sh` / webhook. TPLFIX (`f113004`) commits
after, deploy #2 pending.

All artifacts referenced below are captured under `outputs/sm1/deploy1/`
(untracked, per the ARCHIVE1 convention). Every number cites the file
it comes from so a future session can retrace without rerunning.

## HEAD gate

- local HEAD before pull: `b6e1d745b44cb9cdf074d885a2714dcc3db32e37`
- origin/main: same
- `git status --porcelain | grep -v '^??'`: EMPTY (tracked-only clean)
- C47 CLAUDE.md line count: **6226** (`git show 62d3fc6:CLAUDE.md | wc -l`).
  The C47 handoff body said "6,217" — FALSE. ARCHIVE2 measured 6226.

## Fight_engine census (5 tracked copies at HEAD b6e1d74)

Source: `outputs/sm1/deploy1/step1_2_report.md` §Step 1a.

| Path | md5 | Default triple | Role |
|------|-----|----------------|------|
| `cage_dynasty_web/fight_engine.py` | `751cee2219fea8b09e8bafa25532212d` | **(55, 0.24, 10)** | **live web** |
| `fight_engine.py` (root) | `9f1db99aac3d32e82ef3fca12235ad3f` | (55, 0.70, 6) | dead-per-CLAUDE.md |
| `interface/fight_engine.py` | `58869fa029fa00572279bb489fd041cf` | (55, 0.70, 6) | CLI |
| `simulation/fight_engine.py` | `5b02647ee906048a67aeeefdb6ad4e74` | (55, DAMAGE_MULTIPLIER=0.45, 6) | CLI shim |
| `systems/fight_engine.py` | `b530cfaa3b2da1a3cb09e55bfa1fcaee` | (80, 0.43, 6) | CLI |

## PA state pre-pull

Source: `outputs/sm1/deploy1/pa_wsgi_verbatim.txt`, `errlog_before_full.txt`,
`step_A_B_C_D_report.md`.

- PA HEAD (Files-API read of `.git/refs/heads/main` at
  `/home/vandopegaming/cage_dynasty/`): `1d8b4e1e71806f04ca070ffc7a2632048d81aa48` = C17.
- PA `git status --porcelain` (console 47055546):
  ```
   M fight_engine.py
  ```
  Single line. Root `fight_engine.py` carries CLAUDE.md's documented 11
  appended constants (untracked bytes; hazard filed at CLAUDE.md L1095).
- PA WSGI (`/var/www/vandopegaming_pythonanywhere_com_wsgi.py`): **479 bytes**,
  md5 `91531930abb2f818ccc21cad7b6c6386`. Diff vs repo `cage_dynasty_web/wsgi.py`
  (610 bytes, md5 `c0e973b6691d431c13a82115a8528975`) is exactly the archived
  2026-08-20 delta at `claude/claude_md_archive_2026b.md:379-407` — 2 extra
  comment lines + 1 whitespace shift in the repo copy; functional
  `sys.path.insert` lines byte-identical. No fresh drift.
  **CLAUDE.md L1162-1171's "PA measured 610 bytes" is stale-doc; PA is 479.**
- Running import path (WSGI-defined sys.path prefix):
  1. `/home/vandopegaming/cage_dynasty/cage_dynasty_web` (project_home; last inserted → index 0)
  2. `/home/vandopegaming/cage_dynasty/systems`
  3. `/home/vandopegaming/cage_dynasty/narrative`
  4. `/home/vandopegaming/cage_dynasty/simulation`

## Overlap check (pre-pull)

Source: `outputs/sm1/deploy1/step_A_B_C_D_report.md` §B, this session's terminal.

- PA-modified paths: `fight_engine.py` (root) — one file.
- `git diff --stat 1d8b4e1 b6e1d74 -- fight_engine.py` → EMPTY.
- Full `1d8b4e1..b6e1d74` diff touches `cage_dynasty_web/fight_engine.py`
  (1266 lines), NOT root. Overlap = zero. Safe to `git pull --ff-only`.

## Deploy mechanism of record

Console 47055546 (cwd `~`, activated by Van in browser during the deploy
session). One-shot commands run from `~/cage_dynasty`:

```
cd ~/cage_dynasty && git fetch origin && git pull --ff-only origin main \
  && git rev-parse HEAD && git status --porcelain
```

Raw console output banked at
`outputs/sm1/deploy1/pa_pull_console_clean.txt` (ANSI-stripped) and
`pa_pull_console_raw.json`. Fast-forward line verbatim:

```
Updating 1d8b4e1..b6e1d74
Fast-forward
 CLAUDE.md                                       | 5794 ++----
 cage_dynasty_web/aging.py                       |    4 +-
 [...45 files total, 19067 insertions(+), 6473 deletions(-)...]
```

PA API reload (deploy.sh's mechanism, invoked directly not via webhook):

```
curl -X POST -H "Authorization: Token $PA_TOKEN" \
  https://www.pythonanywhere.com/api/v0/user/vandopegaming/webapps/vandopegaming.pythonanywhere.com/reload/
```

Response: `{"status":"OK"}` HTTP 200. Banked at
`outputs/sm1/deploy1/pa_reload_response.txt`.

## Proof triad (step 4)

Source: `outputs/sm1/deploy1/pa_web_fight_engine.py`, `pa_commentary.py`,
`errlog_after_full.txt`.

- **4a. PA `git rev-parse HEAD`** = `b6e1d745b44cb9cdf074d885a2714dcc3db32e37`
  (console re-check, independent of the pull-line inline read).
- **4b. Files-API marker greps on the RUNNING import path files:**
  - `/home/vandopegaming/cage_dynasty/cage_dynasty_web/fight_engine.py`
    (229,656 bytes):
    - `def main_event`: **0 hits** (DEAD_042_STRIP applied).
    - `_TRIPLE_LIVE_PLAY = (55, 0.24, 10)`: **1 hit, line 1316**.
  - `/home/vandopegaming/cage_dynasty/narrative/commentary.py`
    (200,912 bytes):
    - `def log_window_event`: **1 hit, line 3731** (C21 `304ceff`).
  - Path check: `narrative/commentary.py` is at `narrative/` OUTSIDE
    `cage_dynasty_web/`. Grep confirms the exact path.
- **4c. Error log after reload** (`errlog_after_full.txt`): 94 lines /
  9,399 bytes. Diff vs before (`errlog_before_full.txt`, 92 lines /
  9,101 bytes) = exactly 2 new lines, both benign pre-uWSGI shim
  confirmations timestamped `2026-09-07 17:48:38`:
  ```
  ✅ [SIMULATION-SHIM] simulation.fight_engine shimmed ...
  ✅ [SIMULATION-SHIM] simulation.fight_integration shimmed ...
  ```
  Zero new tracebacks. Baseline is clean; fresh process is up.

## 5b probe (WSGI-reproducing python -c on console)

Source: `outputs/sm1/deploy1/step_5b_report` (inline in this thread).

```
BEGIN_5B
PY_VERSION= 3.13.1
SYS_PATH_PREFIX= ['/home/vandopegaming/cage_dynasty/cage_dynasty_web',
                  '/home/vandopegaming/cage_dynasty/systems',
                  '/home/vandopegaming/cage_dynasty/narrative',
                  '/home/vandopegaming/cage_dynasty/simulation']
[app-load lines including IMPORT-PATH-PROOF for fe, fi, commentary]
FE_FILE= /home/vandopegaming/cage_dynasty/cage_dynasty_web/fight_engine.py
DEFAULT_TRIPLE= (55, 0.24, 10)
SANCTIONED= {(55, 0.24, 10)}
TRIPLE_LIVE_PLAY= (55, 0.24, 10)
END_5B
```

- WSGI has NO `chdir` — only `sys.path.insert` (reported as-is, not
  fabricated).
- `fight_engine.__file__` on PA matches local BEFORE byte-exactly.
- Default triple, `_SANCTIONED_TRIPLES`, and `_TRIPLE_LIVE_PLAY` all
  identical to local BEFORE.
- Also surfaced: `⚠️ SECURITY WARNING SECRET_KEY env var is unset`
  at PA startup. Not deploy-related; CLAUDE.md L1172-1176 already
  flags this. Adds SECRET_KEY to the post-deploy punch list.

## PA-SMOKE1 5a (small-N smoke, N_WEEKS=2 instrument change)

Source: `outputs/sm1/deploy1/pa_smoke1_wrapper.py`,
`pa_smoke1_out.json`.

Instrument change (declared in wrapper header before run):
- Mechanism: text-sub in-memory on tracked harness source, exec
  modified src. Two subs, both required-hit-once:
  - `N_WEEKS = 20` → `N_WEEKS = 2` (line 121)
  - `"sm1", "saveload1"` → `"sm1", "deploy1", "pa_smoke1"` (line 239)
- Van's ruling at this deploy: N≥500-on-PA reconciliation RETIRED
  (infeasible under 100 s/day console CPU quota; PA's cost was
  ~30 CPU-s/week). Replacement: local harness-vs-local-bridge N≥500
  + PA bridge shares from played weeks.

Results (from `pa_smoke1_out.json`):

- Wrapper md5 (local): `55c05ab81dfe04eb18fcd52c5c186103`.
  Uploaded to PA, fetch-back md5 MATCH.
- Wall clock: 62 s (well under 90 s timeout).
- CPU consumed: 60.43 s (`/cpu/` before=3.317s, after=63.746s).
- N fights emitted: **18** (target ≥100 not met by design — N=2 weeks).
- FightConfig constructions: **3140**, distribution:
  - `(55, 0.24, 10)`: 3140 (**100.0%** LIVE_PLAY)
  - Zero at every retired triple: `(55, 0.48, 10)`, `(55, 0.42, 6)`,
    `(55, 0.48, 6)`, dm=0.7, dm=0.43.
- Callers:
  - `game_bridge.py:17357:_assemble_prefight`: 2318 (73.8%)
  - `fight_engine.py:1272:standard_fight`: 762 (24.3%)
  - `fight_engine.py:1282:championship_fight`: 60 (1.9%)

**Parity check** (caught by Van's adversarial read): 3140 − 2318 = 822
= 762 + 60. The seeded pre-gen count (world_init's HistorySimulator
constructs one config per fight over 60 weeks + championship fights)
is byte-identical on PA and local; only the live-play portion scaled
with the shorter run. Stronger parity than finish shares at N=18 could
be.

Finish shares (N=18, reported not compared per Van C46 spec):
- KO 0.0% (0), TKO 27.8% (5), SUB 55.6% (10), DEC 16.7% (3), DRAW 0.0% (0).

## Perf hypothesis (HYPOTHESIS-GRADE, N=1 each, different worlds)

Source: `outputs/sm1/deploy1/access_log_5e_full.txt` (top-5 slowest requests).

| request | 1d8b4e1 | b6e1d74 | ratio |
|---------|---------|---------|-------|
| GET /start-game (world creation) | 11.513 s | 31.113 s | 2.7× |
| POST /advance-week (week 1) | 16.148 s | 32.345 s | 2.0× |

33 commits between the two SHAs added compute-heavier fight-model
paths (C29 finish model, C30 stamina floor + power model, C31
STYLECOHERENCE1, C32 P5-B3 cuts/sprawl/aggression pack, etc.).
Not deploy-blocking; not a docket.

**PERF1** (docket, filed): local timing 1d8b4e1 vs b6e1d74 on ONE
seed to make it a measurement. `outputs/sm1/deploy1/access_log_5e_full.txt`
is the raw PA log the hypothesis derives from.

## TPLFIX regression (this deploy's coverage lesson)

Source: `outputs/sm1/deploy1/errlog_5e.txt`,
`outputs/sm1/deploy1/template_sweep.txt`, TPLFIX commit `f113004`.

- 5e (Van's browser new_game + one card + Accept & Negotiate) returned
  **500 on `/fight-camp/<fight_id>`** after `POST /offer/.../accept`
  succeeded (302).
- Traceback: `jinja2.exceptions.TemplateSyntaxError: unexpected char
  '#' at 7997` at `templates/fight_camp.html:138`.
- Root cause: **C23 `a8c4847`** ("P3-4d power/strength split") placed
  `{# ... #}` Jinja comments INSIDE `{% for/set ... in [<Python list
  literal>] %}` expression bodies. Jinja comments are template-level;
  don't compose inside another tag's expression body.
- Local template compile sweep (script per Step 2b) then caught the
  same-shape bug at `templates/compare.html:51`. Exactly 2 broken
  templates out of 38.
- Fix: `f113004` (TPLFIX). Diff: 2 files, 1 insertion(+), 2 deletions(-).
- **Coverage lesson**: no per-template compile gate existed on any
  prior deploy. Filed as a standing gate at CLAUDE.md § Deploy workflow
  (Step 2c). The tracked sweep tool at `claude/tools/template_compile_sweep.py`
  is the deploy-time check.

## Power finding (POWER1 docket)

Source: `outputs/sm1/deploy1/power_probe.py`, `power_probe_out.txt`.

Two schemas coexist. Neither is wrong on its face; the mismatch
is the bug.

- `training.html` `_STAT_CATS` (18 stats): striking 5, grappling 5,
  physical 5 (strength, speed, cardio, chin, recovery — **no power**),
  mental 3.
- `game_bridge.py:_TRAINABLE` (19 stats): same 18 + `power`. Comment
  above the list acknowledges "P3-4d added `power`".
- `maintenance_training.py:PHYSICAL_STATS` includes `power`; the
  athletic-decay set at :379-380 includes `power`. So power decays with
  the physical group.
- Player creation path (`game_bridge.py:_create_player_fighter:2571-2650`):
  iterates 19 keys including `power`; missing keys fall back to
  `generate_prospect_attributes(...).get(k, 50)`.
- `cage_dynasty_web/game_start.py:generate_prospect_attributes:442`
  returns 18 stats (docstring says "17 total" — schema drifted twice).
  **Does NOT include `power` in its returned dict.**
- Consequence: player's `power` always = **50 by fallback**, guaranteed.
- AI creation path (`world_init.py:1785`):
  `attrs['power'] = _clamp(attrs['strength'] + pw_off + random.randint(-8, 8))`.
  Real derived value.

Local probe (seed 6500000, 292 AI + 1 player, from `power_probe_out.txt`):

- **Player**: `power=50`, `strength=60`. `power == 50` exactly: True.
- **AI (N=292)**: all populated. min=20, max=95, mean=58.9. Continuous
  bell-shaped distribution. 11 of 292 (3.8%) at power == 50 (noise
  around strength≈50, NOT a default flag).

POWER1 fix should live at `generate_prospect_attributes`, not
`_create_player_fighter`. Other callers to audit: amateur → pro signing
graduation path (GENERATOR1 Phase C, `world_init._phase_c_...` chain).
Forward-only; existing saves keep their 50.

## Token breach filing

Source: this thread's turn 1-2 transcript, `deploy.sh`.

**Standing rule (implicit from prior arcs, now made explicit):**
credentials referenced by `$VAR` name, never echoed in plain text.

**Breach**: cc's step-1 transcript included three Bash calls that set
`PA_TOKEN="1df5…"` inline (unredacted). Literal token appeared 3× in
scrollback / session log / this thread. From turn 2 onward every PA
call uses `source <(grep '^PA_' deploy.sh)` + `$PA_TOKEN` by env-var
reference.

**Verified**: `git ls-files deploy.sh` = EMPTY. `.gitignore:16` names
`deploy.sh`. `git log --all --oneline -- deploy.sh` = EMPTY. Token
was NEVER in git history; the exposure is limited to this thread's
transcript.

**Rotation**: deferred to after deploy #2 acceptance (rotating
mid-arc would strand cc mid-procedure). `deploy.sh` will need the
new token pasted; the new value doesn't touch git.

ROTATED 2026-09-07 14:47 PDT, old token invalidated, new token last4=4f5a.

## N≥500-on-PA retirement (Van ruling, this deploy)

Van C47 spec called for a one-time harness-vs-bridge reconciliation
N≥500 at interim-deploy mini-acceptance. Measured: PA console CPU
quota is **100 s/day**; PA-SMOKE1 5a consumed 60 s CPU for 18 fights
(3.3 s/fight). Projected: N≥500 fights would need ~1650 s CPU, 16.5×
the daily budget.

Van's ruling 2026-09-07: RETIRED. Replacement:
1. Local harness-vs-local-bridge N≥500 (local machine; no CPU quota).
2. PA bridge shares from played weeks (as Van plays, cumulative
   card-finish shares are the number of record).

## Deploy acceptance

Van accepted the deploy on the step-4 triad + 5b (2026-09-07).
DOCS + TPLFIX ride into deploy #2. HEAD after DOCS commit will be
one commit past TPLFIX `f113004`.
