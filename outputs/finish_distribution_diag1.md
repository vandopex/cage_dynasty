# FINISH-DISTRIBUTION DIAG1 — 2026-07-11

Diagnostic prompted by Van after FINISH-DETAIL-PERSIST (`4e9d058`) surfaced
82% of TKOs on a fresh 60-week pre-gen world reading as "TKO (Doctor
Stoppage - Cuts)" and 2% of finishes being submissions. Van's prompt:
"we don't know yet, and that's the first thing to find out." Read-only.
No fix. No tuning.

Probe: `outputs/finish_distribution_probe.py`, direct engine calls, no
save. Verified WEB `fight_engine.py` loaded (not the CLI simulation/
sibling — sys.path order matches wsgi.py insertion sequence).

## Headline

**Live-play and pre-gen are two entirely separate simulators, not one
engine with two configs.** Both share type definitions (`FighterAttributes`,
`FighterState.apply_damage`, `SubmissionType`, `SUBMISSION_PROPERTIES`) and
the submission math (`attempt_submission` / `process_submission_progress`)
— but the round/exchange loop and damage application are **duplicated
code**, not shared. That is the structural fact under everything else in
this memo.

- Pre-gen path: `world_init.simulate_fight_full_engine` → `fight_engine.simulate_fight`
- Live-play path: bridge → `fight_integration.simulate_narrated_fight` → `NarratedFightSimulator.simulate`

They also apply damage in fundamentally different ways:

| Path | Damage scale | Source |
|---|---|---|
| Pre-gen | `config.damage_multiplier = 0.42` (default) | `FightConfig.standard_fight()` inside world_init |
| Live-play | `FI_DAMAGE_MULTIPLIER = 0.48` (module const) | `fight_integration.py:82`, applied at `:832` |
| Live-play (bridge intent) | `config.damage_multiplier = 0.24` | **DEAD — never read by fight_integration** |

The "damage_multiplier = 0.24" the bridge passes into `_FightConfig(...)` at
`game_bridge.py:{13540, 14061, 18001}` is silently ignored. `fight_integration`
reads `config.scheduled_rounds`, `config.is_title_fight`,
`config.exchanges_per_round`, `config.submission_progress_to_finish`,
`config.standup_threshold` — **not** `config.damage_multiplier`. Grep-verified
(`grep -n "damage_mul\|\.damage_m\|config\.dam" fight_integration.py` returns
only a docstring hit). CLAUDE.md's Key-constants section claim that
`0.48 × 0.24 = 0.1152` compounds is **wrong**; effective live-play per-strike
scale is just 0.48.

## Q1 — Does the cut-stoppage anomaly hit live-play, or only pre-gen?

**Pre-gen only.** Live-play has a completely different problem.

Measurements: 400 fights per matchup per path, seed=1000, OVR ~75 fighters.

### Balanced vs Balanced

| | Pre-gen | Raw+lp cfg | **Live-play (real)** |
|---|---|---|---|
| KO | 10.0% | 0.2% | 31.8% |
| TKO total | 4.0% | 6.5% | 17.0% |
|  — cuts | 2.8% | 5.8% | **0.0%** |
|  — doctor | 0.0% | 0.0% | 4.5% |
|  — accumulated | 0.2% | 0.0% | 11.8% |
| SUB | 2.8% | 5.2% | 7.2% |
| DEC | 83.2% | 88.0% | 44.0% |
| Finish rate | 16.8% | 12.0% | 56.0% |
| Within-TKO cut% | 68.8% | 88.5% | 0.0% |

### Striker vs Striker

| | Pre-gen | **Live-play (real)** |
|---|---|---|
| KO | 18.2% | 71.2% |
| TKO total | 7.8% | 27.0% |
|  — cuts | 1.5% | 0.0% |
| SUB | 0.0% | 0.0% |
| DEC | 74.0% | 1.8% |
| Finish rate | 26.0% | **98.2%** |

### Striker vs BJJ

| | Pre-gen | **Live-play (real)** |
|---|---|---|
| KO | 3.5% | 43.2% |
| TKO cuts | 3.2% | 0.0% |
| SUB | 11.5% | 17.0% |
| DEC | 81.5% | 20.8% |
| Finish rate | 18.5% | **79.2%** |
| Within-TKO cut% | 92.9% | 0.0% |

### Grappler vs BJJ

| | Pre-gen | **Live-play (real)** |
|---|---|---|
| KO | 4.0% | 22.2% |
| SUB | 10.5% | 25.0% |
| DEC | 80.0% | 36.0% |
| Finish rate | 20.0% | 64.0% |
| Within-TKO cut% | 81.8% | 0.0% |

### Named divergences

1. **Live-play cut stoppages are structurally impossible.** The only site
   that increments `defender_state.damage.cuts` is `fight_engine.py:3234`
   inside `simulate_fight`. `fight_integration._execute_strike` (line
   812-905) computes damage and calls `defender_state.apply_damage(damage,
   target_area)` — which does NOT touch `damage.cuts`.
   `fight_integration.py:1717` reads `_ftr_state.damage.cuts >= 3`, but
   without a writer the value stays at 0 forever. Verified by grep on the
   full file for `damage.cuts +=` and `cuts +=` — zero hits.

2. **Live-play OVER-finishes; pre-gen UNDER-finishes.** Same fighters,
   same seeds, wildly different results. Live-play striker-vs-striker
   finishes at 98.2% (target 50-55%). Pre-gen at 26.0%.

3. **The 82% cut-stoppage FINISH-DETAIL-PERSIST observation was
   pre-gen data.** That save was a fresh world with the pre-gen
   history-sim just ripped by PREGEN-FULL-ENGINE-FIX1 to actually
   hit the real engine. So we saw pre-gen's cut-stoppage pathology
   surface for the first time. Live-play histories built from that
   point forward will not have this shape.

4. **Pre-gen "cuts dominate TKOs" is a denominator effect, not per-elbow
   spike.** In absolute numbers, pre-gen cuts fire at ~2.8-4.5% of all
   fights, which is ~2-4× real-MMA (~1-2% of fights). But non-cut TKOs
   in pre-gen are near-zero because raw `simulate_fight` at
   `damage_multiplier=0.42` doesn't accumulate enough damage to hit the
   accumulated-TKO threshold; cuts stand out as the only TKO path that
   fires. So "cuts are 82% of TKOs" reads as a bug but is actually two
   compounding bugs (cuts fire a bit too often + everything else fires
   almost never).

## Q2 — Cut mechanism

Both engines have their own cut-stoppage check, but only one has a
cut-accumulation writer.

**Cut accumulation (fight_engine.py:3225-3234):**
```
if _st_val in _elbow_types and target == "head":
    _cut_chance = 0.25 + (attacker.strength / 400)
    if random.random() < _cut_chance:
        defender_state.damage.cuts += 1
```
- Trigger: elbow strikes only (`elbow_horizontal, elbow_vertical,
  elbow_spinning, elbow_upward, gnp_elbow, clinch_elbow`) to head.
- Per-elbow-landed probability: **25% at str=0, 50% at str=100**. Elite
  striker at str=75 → 43.75% per landed elbow to head.
- Severity: never scales, integer count only.

**Cut stoppage between rounds (fight_engine.py:3999-4006 and
fight_integration.py:1716-1722):**
```
if _ftr_state.damage.cuts >= 3:
    _cut_stop_chance = min(0.35, (_ftr_state.damage.cuts - 2) * 0.08)
    _cut_stop_chance *= max(0.4, 1 - (_ftr.heart / 200))
```
- Threshold: **hardcoded at ≥3**. `FightConfig.doctor_check_cut_threshold=2`
  is a config field that no code path ever reads. Dead knob.
- At cuts=3 with heart=75: `min(0.35, 0.08) * max(0.4, 0.625)` = 5.0% per
  round-break.
- With 3 round-break checkpoints in a 5-round fight, a fighter with
  cuts=3 has ~14% cumulative chance of losing to a between-round doctor
  stoppage.

## Q3 — Submission mechanism

Same code path in BOTH engines — both call `attempt_submission` and
`process_submission_progress` from `fight_engine.py`.

**Attempt lock-in (fight_engine.py:2803-2854):**
- Gated by position: sub type must match a position in
  `SUBMISSION_PROPERTIES[sub_type][2]`. E.g. `REAR_NAKED_CHOKE` requires
  `BACK_MOUNT` or `STANDING_BACK`.
- `lock_in_chance = 0.30 + sub_bonus + (offense/(offense+defense+1)) * 0.55`
- Capped by skill: `_sub_cap = min(0.70, 0.50 + max(0, submissions - 75) * 0.013)`
  → at sub=75 cap is 0.50, at sub=90 cap is 0.70.

**Progress race (fight_engine.py:2934-2947):**
- Tighten rate: `0.65 if submissions >= 92 else 0.45`
- Each tick attacker adds `offense * 0.45 * rand(0.75, 1.25)` to progress
- Defender adds `defense * 0.38 * rand(0.75, 1.25)` to escape progress
- Finish when `progress >= config.submission_progress_to_finish` (70.0
  default; live-play override 70.0 identical)

**Round-boundary wipe (fight_integration.py:594):**
```
self.fight_state.submission_active = False
```
Every round start wipes `submission_active`. Analogous line in
`fight_engine.simulate_fight` at similar location (not spot-checked here
but confirmed by the tighten_rate comment at 2922-2933 that FIX2 was
specifically motivated by this wipe pattern). **Consequence: subs must
finish in the round they lock in, or die.**

### Attempt density measurements (per fight)

| Matchup | Pre-gen atts | Pre-gen fin | conv | Live-play atts | Live-play fin | conv |
|---|---|---|---|---|---|---|
| Balanced-vs-Balanced | 2.77 | 2.8% | 1.0% | 4.14 | 7.2% | 1.8% |
| Striker-vs-Striker | 0.00 | 0.0% | — | 0.00 | 0.0% | — |
| Striker-vs-BJJ | 0.64 | 11.5% | 18.1% | 1.28 | 17.0% | 13.2% |
| Grappler-vs-BJJ | 3.48 | 10.5% | 3.0% | 4.37 | 25.0% | 5.7% |
| Striker-vs-Grappler | 0.96 | 3.0% | 3.1% | 1.77 | 9.0% | 5.1% |

Live-play has consistently ~1.4-1.5× more sub attempts per fight than pre-gen (longer commentary exchange loop → more selection ticks per round → more attempts).

**Live-play sub finish rate is in-band for grappler matchups (17-25%)
against the engine's own 15-20% target.** The "2% subs" concern from
FINISH-DETAIL-PERSIST was pre-gen data. Non-grappler live-play matchups
still hit 7-9%, which is under target but not catastrophic — mostly a
sub-density-per-attempt story rather than a broken mechanism.

## Q4 — Cross-check attributes

Skipped for this pass. The mechanism divergences answer Van's question
without needing an attribute-distribution cross-check. Note for later:
CLAUDE.md's certified-baselines section notes live-booked BJJ Specialist
sub-offense mean is ~59, synthetic harness inflated it to ~74. My probe
used 92 for BJJ (matching the harness). Live BJJ specialists at 59
would sit under the sub_cap boundary (0.50 cap) and produce fewer
finishes than my measurements show — pushing real live-play SUB rates
down from the 17-25% I measured to something closer to what the pool
extraction showed (1.3%). That is a matchup-density story about the
roster, not an engine mechanism issue.

## Q5 — Real-MMA target

Engine docstring (`fight_engine.py:756-764`) states:
- KO/TKO: 35-40%
- SUB: 15-20%
- DEC: 45-50%
- Finish rate: 50-55%

Ground truth (UFC, aggregated over recent years):
- KO: 15-18%
- TKO: 18-22% total
  - Of TKOs: doctor/cut stoppages are **5-10% of TKOs** = **~1-2% of all fights**
  - Corner stoppages: ~5-10% of TKOs = ~1-2% of all fights
  - Accumulated damage: the remaining ~75-85% of TKOs
- SUB: 15-18%
- DEC: 45-50%

The engine's docstring pools KO+TKO together at 35-40%. That's within
target if you use its numbers. But it doesn't break down *within-TKO*
composition. Reasonable within-TKO split target:
- Accumulated damage: 75-85% of TKOs
- Doctor stoppage (cuts + head damage): 10-15% of TKOs
- Corner stoppage: 5-10% of TKOs

That gives cuts-of-all-fights ~1-2%. The pre-gen 2.8-4.5% cut rate is
2-4× that. The live-play 0.0% cut rate is under.

## What's fixable vs. what's a design decision

### Fixable, low-blast-radius, near-mechanical

1. **`config.damage_multiplier` is dead in `fight_integration`.** Either
   plumb it (multiply after `FI_DAMAGE_MULTIPLIER` at :832) or delete
   the field's rhetorical use in the bridge. Not doing so means the
   bridge's per-fight tuning intent silently doesn't apply.
2. **`config.doctor_check_cut_threshold` is dead in both engines.**
   Same choice: plumb or delete. Currently misleading — reads like a
   knob but isn't.
3. **`fight_integration` never increments cuts.** Either port the
   `fight_engine.py:3226-3234` elbow-cut block into
   `fight_integration._execute_strike` (so live-play can produce cuts),
   or accept that live-play has zero cut mechanics and reword the
   between-round check (currently dead code).

### Design decisions, not fixes

4. **Two-engine architecture.** These simulators diverged over years. Any
   tuning that changes both requires the same change applied twice, with
   the ever-present risk of one drifting. Whether to consolidate is a
   big design call (fight_integration adds commentary hooks; unifying
   them means either commentary bloats the raw engine or the raw engine
   loop is factored out from fight_integration — both are non-trivial).
5. **Live-play over-finishes at striker matchups (98.2% finish rate).**
   The FI_DAMAGE_MULTIPLIER=0.48 (module const) plus the extended
   exchange loop compounds to a KO-heavy engine. If you tune 0.48 down,
   the striker-vs-striker distribution normalizes but the sub finish
   rate drops too (fewer submissions land because opponents finish
   faster). Van's own "fix the engine, not the output" principle applies:
   `damage_multiplier` in FI would be per-fight tunable if the config
   plumbing (fix #1) landed first.
6. **Pre-gen under-finishes.** Fixable by tuning
   `FightConfig.standard_fight()`'s `damage_multiplier` up from 0.42 —
   the same knob the docstring already flags as "was 0.70, tuned down
   for 73% finish rate." But tuning it back up to match live-play
   introduces a *new* class of bug: pre-gen histories will KO-spike,
   champion lineages will churn faster than intended, and the "aging
   in sim" arc's fight-density assumptions change. Design call.

## Recommended shape of any tuning ship

Van, on your call:

- If you want the cut-stoppage share fixed:
  - **In pre-gen (world_init path)**: this is a real engine issue. The
    fastest lever is not "reduce cut rate" but "increase all-other-TKO
    rate" so cuts stop dominating by denominator. That means tuning
    `damage_multiplier` up on the pregen `FightConfig.standard_fight()`
    OR reworking the `simulate_fight` exchange loop to more closely
    match `fight_integration`'s length/pacing.
  - **In live-play**: no action needed, cut stoppages don't fire.
- If you want the sub rate fixed:
  - **In pre-gen**: subs conversion is 1-3%. Both the round-boundary
    wipe and the low fight_engine sub-attempt density contribute. Real
    fix is either fewer attempts with higher conversion (raise
    lock_in_chance bar) or more per-round ticks after lock-in (raise
    tighten_rate more aggressively than the FIX2 arc did).
  - **In live-play**: sub rate is close to healthy for grappler
    matchups (17-25%). Non-grappler is 7-9% — under target but not
    broken.
- If you want the two paths to unify: don't tune, refactor. That is a
  multi-session arc. In the interim, DUAL-TUNE any change you make and
  add a test that runs both paths side-by-side against a fixed roster
  and asserts distribution parity within a tolerance. The probe
  (`outputs/finish_distribution_probe.py`) is 90% of that test's shape.

## What I did NOT do (per Van's constraints)

- No production save read (would show real live-play finish rates on Van's actual roster; skipped because Q1 is answered from mechanism alone).
- No code changes.
- No tuning proposal beyond "which lever, in which engine, would move which number."
- Did not measure `fight_integration`'s KO-spike at unhealthy matchups
  (e.g. striker-vs-striker 98.2% is clearly broken) beyond noting it.
  If Van wants that traced next, the KO logic in `_execute_strike`
  (line 726-905) is the mechanism to walk.

## Findings that update CLAUDE.md

- Key-constants section's `0.48 × 0.24 = 0.1152` compounding claim is
  wrong. `fight_integration` never reads `config.damage_multiplier`.
  Effective live-play scale is 0.48.
- `FI_DAMAGE_MULTIPLIER = 0.48` at `fight_integration.py:82` IS the
  only per-strike damage scaling in live-play. `fight_engine.FightConfig
  .damage_multiplier` at `:735` is the only per-strike damage scaling
  in pre-gen (and in the dead-code path of `fight_engine.simulate_fight`
  called with a live-play config, which nothing actually does).
- `FightConfig.doctor_check_cut_threshold=2` is dead in BOTH engines.
  Cut stoppage threshold is hardcoded at `>= 3` in both.
- `fight_engine.simulate_fight` and `fight_integration.simulate_narrated_fight`
  are TWO DIFFERENT SIMULATORS with a shared submission-math and dataclass
  layer, not a single engine. Any tuning has to hit both to unify.
