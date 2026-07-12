# TWO-ENGINE CONSOLIDATION DIAG1 — 2026-07-11

Structural analysis of `fight_engine.simulate_fight` (pre-gen path,
called by `world_init`) vs `fight_integration.simulate_narrated_fight`
(live-play path, called by `game_bridge`). Read-only. No code. No
tuning. Successor to FINISH-DISTRIBUTION-DIAG1.

## TL;DR

`fight_integration` is a **fork of `fight_engine.simulate_fight`, not a
narration decorator around it.** Both files were introduced together
in commit `56bf807` (2026-04-27), the very first commit of the repo.
FI's docstring still reads "Bridges fight_engine and commentary systems"
— consistent with the *intended* narration-wrapper design. But over the
2026-06-13 → 2026-06-16 tuning arc, ~10 commits shipped simulation
logic *into* the FI layer instead of into FE. FE's simulate_fight was
not kept in step. That is the drift; the "two-engine" state is
accidental, not designed.

**Consolidation is possible.** All the simulation primitives FI uses are
imported from FE (`select_action`, `calculate_strike_success`,
`calculate_strike_damage`, `apply_position_change`, `attempt_submission`,
`process_submission_progress`, `score_round`) and the roles of the two
`FighterState`/`FightState` classes are identical. What differs is the
composition of exchange-level modifiers around those primitives, and
whether commentary hooks fire. The cleanest structural direction is:

**One simulator, commentary as an optional event-driven decorator over
its output.** FE already emits every event via `event_log: List[FightEvent]`
— that's the seam. FI's `NarratedFightSimulator` gets refactored to a
`NarrationBuilder(fight_result)` post-processor over that stream. The
between-round + per-exchange mechanics that FI added (V7 flash-KO
system, GnP accumulation, clinch body accumulation, Muay Thai / Karate /
Point Fighter / Brawler style windows, rocked-shots referee stoppage,
etc.) get **ported into FE's `simulate_exchange`** rather than deleted.

## 1. What does `fight_integration` actually do?

Enumerating every top-level responsibility:

### Presentation-only (would move to a NarrationBuilder decorator)

- `class NarratedFightResult` — extends `FightResult` with `round_summaries`,
  `key_moments`, `full_commentary`, `fight_narrative` (:206-209). Every
  commentary field is downstream of an event stream FE already emits.
- `self.commentary.emit_fight_open()` (:504), `emit_gameplan_setup()`
  (:541), `start_round(n)` (:1589), `end_round(s1, s2, control_time)`
  (:1777), `log_event(...)` (~15 call sites), `generate_submission_commentary`
  (:1504), `generate_full_finish_sequence` (:1556).
- `get_time_str`, `get_fight_narrative`, `get_key_moments`,
  `get_full_commentary` (:1806-1851) — pure retrieval.
- `strike_to_action_type` (:264), `grappling_to_action_type` (:293) —
  event-type mapping for the commentary system.
- `_log_finish(winner_id, method, exchange_num)` (:1543) — commentary hook.

### Simulation — shared with FE (already imported, no divergence)

- `calculate_strike_success(...)` (:780) — imported from FE.
- `calculate_strike_damage(...)` (:824) — imported from FE.
- `apply_position_change(...)` — imported from FE, used inside
  `_execute_grappling`.
- `attempt_submission`, `process_submission_progress` — imported and
  used in `_execute_submission_attempt` / `_process_submission_exchange`.
- `select_action` (imported), `score_round` (imported).
- `FighterAttributes`, `FighterState`, `FightState`, `FightConfig`,
  `RoundStats`, `FightResult`, `BodyPartDamage`, `Position`,
  `StrikeType`, `SubmissionType`, `GrapplingAction`, `Gameplan`,
  `dial_execution` — all imported.
- `DAMAGE_MULTIPLIER`, `FLASH_KO_*`, `TKO_GNP_*`, `TKO_STANDING_*`,
  `TKO_DURABILITY_*` — imported balance constants.

### Simulation — reimplemented in FI (parallel to FE, drifted)

- Exchange loop (`_simulate_exchange` :644, `_execute_strike` :726,
  `_execute_grappling` :1257, `_execute_submission_attempt` :1399,
  `_process_submission_exchange` :1456)
- Round loop (`_simulate_round` :1583)
- Fight loop (`simulate` :1781)
- Initiative determination (`_determine_initiative` :608) — has ±2×aggression
  gameplan tilt that FE's version lacks
- Between-round stoppages (cut / doctor / corner :1706-1746)
- Between-round health/stamina recovery (:562-593, corner-bonus logic)
- Referee standup logic (:1656-1702) — the asymmetric-dominant version
  from `GROUND-TIME-L2-SHIP1` (`53e0f27`, 2026-07-06). **Ported to FE**
  by the same commit — FE version at :3597-3605 is the flat version.
  Different formulas today.
- Rock duration decrement (:1628-1654) with corner-bonus + adrenaline-
  surge burst. **FE version at :3646-3656 is a plain decrement** with
  no corner bonus and no surge.
- Referee stoppage for unanswered shots while rocked (:1003-1020) —
  `_rocked_shots` accumulator. **Absent from FE.**
- Rocked-grappler exploit — takedown/back-take when defender is
  rocked (:1022-1050). **Absent from FE.**
- V7 flash KO system (:1052-1078) — reads `FLASH_KO_*` constants.
  **FE has its own inline flash KO** at :3236-3249 that DOES NOT read
  the V7 constants; it uses a fixed `0.01` base scaled by boxing/
  strength/health.
- V7 TKO GnP system (:1080-1113) reading `TKO_GNP_*` constants and
  `_tko_durability_mult`. **Absent from FE** — FE has no analogous
  ground-and-pound TKO path.
- V7 TKO Standing system (:1115-1140). **Absent from FE.**
- Clinch body accumulation :915-945 — Muay Thai bonus, `_clinch_body_acc`
  threshold TKO. **Absent from FE.**
- Ground-and-pound accumulation :954-987 — `_gnp_accumulation` threshold
  TKO with mount/back-mount rate bonuses. **Absent from FE.**
- Leg kick TKO :989-1001 — a version exists in both, but FI's checks
  stamina scaling differently (`stamina < 50 → ×1.4`) than FE's version
  at :3203-3223 (identical formula, same file diff).
- Adrenaline surge on rock-clear (:1636-1642, 12% chance). **Absent from FE.**
- Sprawl counter momentum window (:746-751). **Absent from FE.**
- Counter-window damage multiplier (:753-769) — IQ/speed-gated tiers.
  **Absent from FE** (FE has counter mechanics but not this specific
  window multiplier).
- Brawler walk-through / brawler counter (:878-895, 771-777). **Absent from FE.**
- Karate patience power bonus (:864-869). **Absent from FE.**
- Point Fighter movement window (:871-876, 897-902). **Absent from FE.**
- Muay Thai knee amplification (:842-854). **Absent from FE.**
- Body-shot stamina drain (:909-913). **Absent from FE.**
- Named specialty finishes (:1164-1234 via `_specialty_map`) — 10-entry
  strike-to-KO-name map. **FE has its own parallel map** at :3278-3294 —
  overlaps significantly but not byte-identical.
- Chin erosion during a rocked window — driven by FI's `_rocked_shots`
  accumulator (chin_compromised gate).

### Diagnostic scorecard

| Category | FI methods | Shared with FE? |
|---|---|---|
| Presentation (commentary, event mapping, retrieval) | ~14 methods | No — pure FI |
| Simulation primitives (strike calc, damage calc, submission math, position, select_action, score_round) | 0 methods reimplemented | All imported from FE |
| Simulation composition (exchange loop, round loop, fight loop, TKO paths, style windows, rock/standup) | ~15 methods, ~1300 lines | Parallel to FE, drifted |

**~1300 of FI's 2114 lines are duplicated simulation logic**, not
presentation. That is the "two-engine" surface.

## 2. Where do the two engines diverge mechanically?

Side-by-side, every place they make different decisions about the same
event. Ordered from most-impactful to least:

### 2A. Damage scaling — different constants, same intent

| | Pre-gen (FE) | Live-play (FI) |
|---|---|---|
| Per-strike scale | `config.damage_multiplier = 0.42` (default) | `FI_DAMAGE_MULTIPLIER = 0.48` (module const) |
| Rivalry heat multiplier | Compounds into `config.damage_multiplier` at :3915 (`replace(config, damage_multiplier=... * heat_damage_mult)`) | Not read — FI would compound heat manually if it wanted to |
| Bridge-passed `damage_multiplier=0.24` | Not used — pre-gen doesn't run through bridge | **Silently dead** — FI's grep for `config.damage_multiplier` returns zero hits |

**Consequence**: pre-gen scales damage by `0.42`, live-play by `0.48`.
The `0.24` the bridge configures at three sites is a documented but
non-functional knob. CLAUDE.md's "0.48 × 0.24 = 0.1152 effective per-
strike scale" is fiction — the multiplication never happens.

### 2B. Cut mechanism — writer exists in FE, cut stoppage check exists in both

| | FE | FI |
|---|---|---|
| Cut increment | `simulate_fight.py:3225-3234` — elbows to head, 25-50% per land | **No writer. Cuts are always 0.** |
| Cut stoppage check | `:3999-4006` — cuts ≥ 3 → `min(0.35, (cuts-2)×0.08) × heart_mod` | `:1717-1722` — identical formula, reads a value nothing writes |
| Config knob `doctor_check_cut_threshold=2` | Defined at :771, **never read** | Never read either |

**Consequence**: cut stoppages fire in pre-gen but are structurally
impossible in live-play. The 82% within-TKO cut rate FINISH-DETAIL-PERSIST
surfaced was pre-gen only. Live-play cut rate is 0.0% across all matchups
in the 400-fight probe.

### 2C. Finish rate — 4× divergence at same fighters, same seeds

From FINISH-DISTRIBUTION-DIAG1, striker-vs-striker:

| Path | Finish rate |
|---|---|
| Pre-gen (FE) | 26.0% |
| Live-play (FI) | **98.2%** |

Balanced-vs-Balanced:

| Path | Finish rate |
|---|---|
| Pre-gen (FE) | 16.8% |
| Live-play (FI) | 56.0% |

**Root cause**: FI has ~8 accumulator-TKO paths FE lacks (V7 flash KO
using shared constants, V7 TKO GnP, V7 TKO Standing, GnP accumulation
tracker, clinch body accumulation, rocked-shots referee stoppage,
Muay Thai knee amplifier, chin erosion during rock windows). FE has
its own inline flash KO but at a lower base rate, and no GnP/clinch/
standing accumulator TKOs at all. Same damage multiplier order — FI
still finishes ~4× more because it has ~4× more finish paths.

### 2D. Between-round mechanics — parallel implementations

| | FE (`:3987-4060`) | FI (`:1706-1752`) |
|---|---|---|
| Cut stoppage | Yes | Yes (unreachable — cuts never writ) |
| Doctor stoppage (health < 28, head damage > 55) | Yes | Yes — identical formula |
| Corner stoppage (round ≥ 2, health < 22, KDs ≥ 2) | Yes | Yes — identical formula |
| Corner-bonus rock recovery | No | Yes (`self.corner_bonus_f{1,2}` from init) |
| Adrenaline surge on rock-clear (12%) | No | Yes |
| Composure penalty from heat | Yes (`heat_composure_penalty`) | No (FI doesn't read `heat_level`) |

### 2E. Round-boundary submission wipe — same in both

`fight_state.submission_active = False` at round start. FE resets in
`FightState.new_round()` (:730-740, called from :3934); FI wipes
explicitly at `_init_round`:594. Same behavior. This is the
"in-round race must resolve or die" pattern that both engines share.

### 2F. Per-exchange strike composition — many drift points

Between FE's `simulate_exchange` (`:2973-3658`) and FI's
`_execute_strike` (`:726-1234`), the following modifiers differ:

- **Wrestler-threat damage reduction** — FE:3168-3185. **FI: none.**
- **GnP dominant-position bonus** — FE inline at :3195 (×1.35), FI
  passes an `is_dominant_position` flag into `calculate_strike_damage`
  itself (:822-828). Different plumbing, similar intent.
- **Body-shot stamina drain (`damage * 0.4`)** — FI-only.
- **Muay Thai knee_head ×1.30 × 1.10** — FI-only.
- **Karate patience head-damage ×1.40** — FI-only.
- **Point Fighter movement window −20%** — FI-only.
- **Brawler walk-through 10-25% chance ×0.75** — FI-only.
- **Sprawl counter and adrenaline surge windows** — FI-only.
- **Counter-window IQ×speed damage multiplier** — FI-only.
- **Elbow cut accumulation** — FE-only.

Each is a "situation-based advantage" from the 2026-06-15 ship arc
that only landed in FI. Individually small; collectively they explain
why live-play finishes 4× more often than pre-gen.

### 2G. Selection & scoring — genuinely shared

`select_action`, `select_strike`, `select_grappling_action`,
`calculate_strike_success`, `calculate_strike_damage`,
`calculate_grappling_success`, `apply_position_change`,
`attempt_submission`, `process_submission_progress`, `score_round`
— all imported from FE, both engines use the same functions. This is
the load-bearing evidence that consolidation is feasible: the primitive
math is not forked.

## 3. Does `fight_engine` have everything `fight_integration` needs?

**Almost — but not quite.** Two categories of gap.

### 3A. Data model gaps — small, mechanical

`FightResult` (FE:3743) has: `winner_id`, `loser_id`, `method`,
`finish_round`, `finish_time`, `fighter1_stats: List[Dict]`,
`fighter2_stats: List[Dict]`, `fighter1_final_state: Dict`,
`fighter2_final_state: Dict`, `event_log: List[FightEvent]`.

`NarratedFightResult` (FI:173) adds: `winner_name`, `loser_name`,
`sub_type`, `total_rounds`, `judge_scores`, `decision_type`,
`fighter1_final_health`, `fighter2_final_health`, `round_summaries`,
`key_moments`, `full_commentary`, `fight_narrative`.

All of these are downstream of the event log — a NarrationBuilder over
`FightResult.event_log` could compute every field on the FI side. `sub_type`
is technically new information (FE currently embeds it as
`"Submission (armbar)"` in `method`) but `awards.canonical_specialty_method`
already parses that out, so no data is lost.

### 3B. Simulation coverage gaps — where FE would need to grow

If FE became the single simulator, it would need to add these
FI-only mechanics to reach parity with live-play's current behavior:

- V7 flash KO system reading `FLASH_KO_*` constants (currently FE has
  its own inline flash KO with a different formula)
- V7 TKO GnP + TKO Standing accumulator paths (currently FE has none)
- Clinch body accumulator TKO (Muay Thai)
- GnP accumulator TKO
- Rocked-shots referee stoppage
- Style-specific damage windows: Muay Thai knees, Karate patience,
  Point Fighter movement, Brawler walk-through/counter
- Corner-bonus rock recovery + adrenaline surge burst
- Sprawl counter momentum window
- Counter-window IQ×speed damage multiplier
- Rocked-grappler exploit (takedown/back-take when defender rocked)

**Every one of these is a "port from FI into FE" — no research needed.**
Formulas exist and have been tuned. It's move-and-integrate work.

### 3C. Commentary reproducibility — the big question

The commentary system currently receives events at trigger points during
simulation (`self.commentary.log_event(action_type, actor, target,
action, success, damage, exchange_num)` — 15+ call sites). Every one of
those calls is triggered by an event that FE also emits into
`event_log` — the primitive `log_event` helper at FE:2996 wraps every
strike, submission, position change, escape, and finish. So a decorator
that walks `event_log` post-fight and re-triggers `commentary.log_event(...)`
would produce byte-identical commentary output for byte-identical fights.

The catch: **FI's commentary calls include context FE's events don't
carry.** Specifically:
- `_forward_lines` / `_patient_lines` gameplan-intent lines (`:520-534`)
  are triggered pre-fight from `_init_fight` reading the `Gameplan`
  passed to the FI constructor. FE's `simulate_fight` doesn't accept a
  gameplan (though `simulate_exchange`, which FE uses internally, does —
  via `select_action`).
- The "surviving the storm surge" burst at `:1636-1642` is a simulation
  event that FI emits mid-round; there's no matching FightEvent type
  emitted by FE today.
- `emit_gameplan_setup`, `emit_fight_open` are FI-side calls that
  correspond to "fight begins" — no matching FE event.

None of these are hard blockers. Adding FightEvent event types
`"gameplan_intent"`, `"rock_surge"`, `"fight_open"` at the appropriate
FE emission sites closes the gap without breaking FE's API (event types
are string tags in the FightEvent dataclass).

## 4. Does `fight_integration` have anything `fight_engine` lacks?

Yes — the simulation additions listed in §3B are real work that's been
tuned. Most are "situation-based advantages" landed 2026-06-15 in the
FI-only tuning arc. Deleting them would regress live-play behavior in
ways players would notice.

**Ports worth keeping (into FE):**
1. V7 flash KO system that reads the shared `FLASH_KO_*` constants —
   these constants live in FE already, but FE's simulate_exchange uses
   its own inline formula instead of the constants. Unifying to the
   V7 formula is a genuine improvement.
2. V7 TKO GnP + TKO Standing paths — real mechanics that pre-gen currently
   lacks. Champion belt lineages in pre-gen worlds are less finish-heavy
   than live-play would produce; adding these to FE narrows the gap.
3. Style windows (Muay Thai / Karate / Point Fighter / Brawler /
   Counter). These are the "signature identity" mechanics that make
   the roster feel differentiated. Pre-gen histories currently render
   flat because they don't fire.
4. Rocked-shots ref stoppage, sprawl counter, adrenaline surge — all
   contribute to "the fight has flow" texture.

**Ports NOT worth keeping (delete instead of porting):**
- FI's parallel between-round doctor/corner/cut stoppage block — replace
  with FE's version once FI is retired. Same formula.
- FI's parallel referee standup — the `GROUND-TIME-L2-SHIP1` asymmetric
  version at FI:1686-1689 IS the intended behavior; port to FE, delete
  FE's flat `+= 1` at :3598.
- Named specialty finishes map — one canonical map in FE, delete FI's
  duplicate.

## 5. Why do two exist?

**Not deliberate. Accidental drift.** Evidence:

### 5A. Origin

Both files were introduced together in the very first commit
`56bf807` (2026-04-27). FI's docstring at the top of the file still
reads:
> "Bridges fight_engine and commentary systems for complete
> narrated fight simulation with play-by-play commentary."

That's a design intent for a narration decorator, not a distinct
simulator.

### 5B. Divergence timeline

- **2026-06-10** (`dd2fab9`): "Ship1/Ship2/StyleSync: **full 11-style
  fight engine rewrite**" — touched FI. This is the pivot point.
- **2026-06-14** (`d347de9`): "named finishes + SUB rate fix +
  ref/doctor/corner stoppages — **all in fight_integration layer**".
  This commit message states the choice explicitly: "in FI, not FE."
- **2026-06-15** (`ace5e76`, `c16053a`, `1e82fc2`, `93ca5df`, `dff7b6e`,
  `9a5d173`): six commits landing style-defining moments, situation-
  based advantages, stamina economy, strength head damage,
  recovery/composure wiring, GnP threshold, flash KO, clinch body
  threshold, stamina drains — **all in FI**. FE received none of these.
- **2026-06-19** (`fa14e06`): "clinch_control as 18th stat — data layer
  only, no engine integration yet" — foreshadowing more FI-only work.
- **2026-07-05** (`ec78b3b`, `d1d927d`, `b97e7bd`): Gameplan wire —
  landed in both FE and FI (touched `simulate_narrated_fight`,
  `NarratedFightSimulator`, AND `select_action` in FE). Bilateral.
- **2026-07-06** (`53e0f27`): `GROUND-TIME-L2-SHIP1` — asymmetric ref
  standup. Landed in FI only per commit stats.

### 5C. The rationale

Reading `d347de9`'s message ("all in fight_integration layer") and
the follow-up 2026-06-15 tuning arc: **the ship discipline treated FI
as the live simulator and let FE become a legacy layer** without ever
saying so out loud. Pre-gen was still using `simulate_fight_simple`
(coin-flip fallback) until 2026-07-06, so nobody was measuring FE's
finish rates in production. There was no signal that FE had drifted.

**Then `PREGEN-FULL-ENGINE-FIX1` (`efaf7f6`, 2026-07-11) wired pre-gen
to FE.** Suddenly there were two simulators producing two different
worlds for the same fighters. That's the moment the drift became a
visible bug. It's a week old.

### 5D. Perf rationale is real but not load-bearing

FI is fatter per fight (55 exchanges × more style modifiers × commentary
event calls). Rough measured cost from the 400-fight probe: FI ~2x FE
runtime. Pre-gen at 60 weeks × ~40 fights/week × ~2400 fights,
FE takes ~12s locally, FI would take ~24s. Real but not prohibitive.
`PREGEN-HISTORY-SHORTEN1` (60w instead of 130w) already made the perf
budget less tight. If pre-gen ran the unified engine at FI's cost,
world-gen goes from ~12s to ~24s. That is not a design constraint that
should force two-engine architecture.

**The performance rationale would justify SKIPPING commentary during
pre-gen** (pass `event_log=None`), not maintaining two simulators.

## 6. What would consolidation cost?

Rough shape (informational only; not a scoped ship plan):

### 6A. Direction A — port FI-only mechanics into FE, retire FI's simulator, keep NarratedFightResult as decorator

**Blast radius:**
- 1 file heavily rewritten: `fight_engine.py` (add ~800 lines of FI-only
  mechanics into `simulate_exchange` + `simulate_fight`)
- 1 file substantially shrunk: `fight_integration.py` (delete the
  `NarratedFightSimulator._simulate_exchange/_execute_*/_simulate_round/simulate`
  duplicated loops, keep only `NarratedFightResult`, `simulate_narrated_fight`
  becomes a thin wrapper: run FE, build narration from `event_log`)
- Bridge call sites unchanged (all three keep calling
  `simulate_narrated_fight(...)`)
- `game_bridge.py:{13540, 14061, 18001}` — the dead `damage_multiplier=0.24`
  becomes live (finally read by the consolidated engine); need to decide
  whether to keep 0.24 or drop the field back to default 0.42
- CLAUDE.md updates for the constant table
- Save files: no format change, forward-compatible
- Tests: the probe I built (`outputs/finish_distribution_probe.py`) becomes
  a regression test — should assert pre-gen and live-play finish
  distributions parity within tolerance

**Rough size:** ~1200 net lines changed (add ~800 to FE, delete ~1300 from
FI, add ~300 for NarrationBuilder). Multi-session arc but well-scoped
per-session. Two saves-compat concerns: existing saves have fights
generated by the CURRENT FE and CURRENT FI — those persist. Fights
generated AFTER the ship use the consolidated engine. Same as any
engine-tuning ship's provenance issue.

### 6B. Direction B — keep two simulators, but wire the dead knobs and unify constants

Cheaper. Just fix the specific bugs:
- Plumb `config.damage_multiplier` into FI (multiply after
  FI_DAMAGE_MULTIPLIER at :832) OR delete the field from bridge calls
- Delete `config.doctor_check_cut_threshold` (or plumb into both
  between-round blocks)
- Add cut accumulation to FI's `_execute_strike` (10 lines, copy from
  FE:3225-3234)
- Add a maintenance discipline: any FI mechanic that lands must land in
  FE too. Formalize this in CLAUDE.md.

**Cost:** ~50 lines total across three files. One session. Does NOT
fix the underlying finish-rate divergence — that requires either
tuning both engines against a shared target (double-tune every future
ship) or Direction A.

### 6C. Direction C — leave two, tune independently against separate targets

Cheapest today. Highest long-term maintenance cost. Every future
engine-touching ship has to hit both files or drift accelerates.

## 7. Recommendation

**Direction A**, but sequenced:

1. **First**: land Direction B's specific fixes so the immediate false
   surface area (dead knobs, unreachable cut stoppage) is closed.
   ~50 lines, one session. Removes the "confidently wrong CLAUDE.md
   constant" class of hazard.

2. **Second**: land NarrationBuilder as a decorator over
   `FightResult.event_log`. Doesn't touch simulation yet. FI's
   `NarratedFightSimulator.simulate` still runs; NarrationBuilder
   builds the same output from the event stream. Add a test: on the
   same seed, `NarrationBuilder(fe.simulate_fight(...))` and
   `fi.simulate_narrated_fight(...)` produce equivalent commentary
   for the events they share. This proves the seam works before we
   rebuild it.

3. **Third**: port the FI-only mechanics into FE's `simulate_exchange`
   one family at a time (V7 flash KO, V7 TKO GnP+Standing, style
   windows, rock/surge). After each family: run the probe, confirm
   pre-gen finish rates converge on live-play's.

4. **Fourth**: retire FI's simulator (`_execute_strike` /
   `_execute_grappling` / `_simulate_round` / `simulate`). Keep
   `NarratedFightResult`, `simulate_narrated_fight` as a wrapper:
   `result = fe.simulate_fight(...); return NarrationBuilder(result).build()`.
   Bridge calls unchanged.

5. **Fifth**: revisit tuning against ONE target now that there's one
   engine. This is where the FINISH-DISTRIBUTION knobs finally get
   turned — with confidence they'll produce the same behavior in
   both paths.

Do NOT tune finish rates before consolidation. Any number you land
today has to be re-tuned twice: once for the interim divergent state,
once again after unification. That's the trap.

## What I did NOT do (per Van's constraints)

- No code.
- No specific tuning proposals.
- Did not decide whether pre-gen should skip commentary (perf-vs-consistency
  design call, deferred).
- Did not port anything.
- Did not delete anything.
