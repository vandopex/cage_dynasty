# FIGHT MODEL P3 — IMPLEMENTATION SCOPE v0.1 (2026-09-03)
# STATUS: P3-0/1 SHIPPED+DEPLOYED; P3-2 (C18), P3-3 (C19), P3-4a
# (C20), P3-4b (C21), P3-4c (C22), P3-4d (C23) SHIPPED; P3-4e (C24)
# SHIPPED DARK; C25 promoted FighterRecord.fighting_style to a real
# field; C26 landed measurement plumbing; C27 measured C25's
# activation delta on the production population + ruled KEEP; C28
# ARCHIVE1 (CLAUDE.md split); P5-A FINISH MODEL SHIPPED as C29
# (2026-09-05, machinery only — no calibration); P5-B1 SHIPPED as
# C30 (2026-09-05, D17 stamina floor + D18 unified power model +
# BF-2 offset-table aliases); STYLECOHERENCE1 SHIPPED as C31
# (2026-09-05, born styles reach the play surface); P5-B3 SHIPPED
# as C32 (2026-09-05, cuts + sprawl-punish + aggression pack + IQ
# execution ON — structural); P5-B4 SHIPPED as C33 (2026-09-05,
# judge re-weight CONTROL 1.5→4.0 PROVISIONAL + D19 aggression-
# drain constants +15%/-10% asymmetric — structural; magnitudes to
# P5-C); C34 GENERATOR1 docs (ratified spec v0.1 + August notes
# enter git); C35 GENERATOR1 Phase A (amateur graduation transfers
# real stats, 15 remapped + 4 derived, forward-only); next:
# GENERATOR1 Phase B (pro generator rebuild) → Phase C (amateur
# unification) → P5-C calibration → P3-6 ship.
# Updated 2026-09-05 (C35 docs-and-engine ship).

Disk copy canonical; this project copy is backup. Implements the
ratified contract claude/fight_model_v1_0.md on the fi chassis.
Signal 1 GIVEN (Van, 2026-09-03; S1-S4). Gated staircase.

## DOCKET P3-0 — C15 DOCS COMMIT — SHIPPED (rode with C16)

## DOCKET P3-1 — FAIRNESS & SCORING — SHIPPED + DEPLOYED

C16 e54d3cc + C17 1d8b4e1 (#22 fix, 227/227 scorer proof). Deployed
on proof 2026-09-03. **DEPLOY FREEZE ACTIVE (S2)** — PA runs C17.

## DOCKET P3-2 — CONSOLIDATION — SHIPPED as C18 53077ad

world_init → fi explicit config; fe.simulate_fight retired-not-
deleted; bridge DEC 45.1→29.2% (in-band). S4(a).

## DOCKET P3-3 — CONTEST REBUILD — SHIPPED-STRUCTURAL as C19 4405884

One P_c form; D13 composites; upsets retired; initiative dampened.
S5: magnitudes to P3-5. F4 FIXED (boxing +2.13), F3 SD ALIVE
(+3.94), F9 GONE, F8 preserved, F6 direction fixed. F10 ACTIVITY
TAX filed (cardio channel doubled).

## DOCKET P3-4 — STATE, WINDOWS, SUBS, AGGRESSION, POWER

### 4a LEVER TWO — SHIPPED as C20 cb1dcd8 (S6)
Cardio-owned regen S_r=0.5; fatigue routing (fi:623/625 bypass
closed). T1_R3 DEBT PAID (14.12→29.2). B9's T2 assignment refined-
false on the defining touched-zero instrument; T2 → P3-5. Inputs
forward: cardio +25.25pp; speed −16.5pp; POP ~50% DEC vs EP1 99%.

### 4b WINDOWS + CARRY-OVERS — SHIPPED as C21 304ceff (2026-09-04)
window_registry.py: 10 rows (7 restated mechanics + elbow_cut_writer
+ doctor_cut_stoppage + sprawl_punish_attack). Byte-equivalence
700/700 vs pristine C20 worktree; all no-op proofs MD5-identical.
CUTS RETURN (43/700 fights; POP rate ~2× fe baseline — CUT-RATE
flagged to P3-5). Sprawl-punish live (10.5% of fights, Δwin 0 at
×1.25 — P3-5 dials). Heat socket ready (level 80 → +15pp finishes;
zero live callers). Commentary gains log_window_event (12 hooks,
narrative/commentary.py — live path). Filed: karate_patience cross-
module dep; heat composure/aggression dead-in-fe; new method string
"TKO (Doctor Stoppage - Cuts)" needs downstream pattern check at
P3-6. Census: outputs/sm1/fight_model/p3_4b/census.md.

### 4c SUBMISSION MODEL — SHIPPED as C22 c4266a0 (2026-09-04)
§5a REPLACEMENT (no toggle): tap/sleep/injury split via heart-
modulated tap threshold + refusal band; choke→sleep ("Technical
Submission"), joint_lock→injury ("Submission (Injury - <sub>)")
with severity by overshoot (MODERATE/SEVERE/CAREER). New sub_escape
contest class (P_EVEN=0.10, EDGE20=0.28, S≈3.96 — P3-5 ratifies the
"+20 on primary vs both-stats" convention). Chin + composure wiring
FLIPPED ON (Van-approved via C22 paste on verify.md T4 defining-
instrument readings: HEART sub-loss −21.5pp ~10σ; CHIN kd_mean
−18% rel; COMPOSURE rock_duration −32% rel; N=1000/cell, positive
controls proven-discriminating). FIVE RESURRECTIONS COMPLETE —
heart/chin/composure ALIVE on defining instruments. FIX A 3-tuple
unpack (fe fallback + test_sub_sim). FIX B method routing: all
three sub forms → SUB at gb Path A, gb Path B, awards.canonical_
specialty_method (pre-fix, sleeps collapsed to DEC in AI fights and
persisted as truncated "Technical " in player history). FIX C
injury persistence: GameBridge._sub_injury_hook → real
systems.injury API, wired Path A + Path B (NOT MC odds — estimator
would multi-count). Gates G1 18/18 routing, G2 bridge smoke
(persisted injury Δ=1, real fields), G3 EP1_500 flags-ON (127 subs:
tap=100 sleep=7 injury=20; hook fires match), G4 syntax/import.
RIDERS: legacy escape fields dead-in-legacy-only (delete when
_legacy_process_submission_progress retires); pre-existing Path A
KO/TKO specialty truncation "KO (Head K" (gb:17931 [:10] slice) —
cleanup at next natural gb touch or P3-6 UI nits; pre-gen history
sim does NOT persist injuries (world_init owns no InjurySystem —
fresh saves start clean, accepted design, revisit at INJURY1);
fight_history stores plain "SUB" for all three flavors — flavor
lives in commentary/watch page; whether history rows should show
choke-out/injury distinctly is a D14/D16-batch display decision.
Verify artifacts: outputs/sm1/fight_model/p3_4c/verify/.
### 4d POWER (D7) — SHIPPED as C23 (2026-09-04)
19th stat POWER split from STRENGTH. Striking-damage lanes at
fe:2833/2837 + flash-KO at fi:1328 now read attacker.power under
FI_POWER_WIRING_ENABLED=True (flag ON on disk, Van-approved per
G2 separability). Strength keeps grappling-physicality (throws/
slams/clinch break/escape assist). World-gen un-drops the pre-4d
dropped `power` key at world_init:3068 and applies style-informed
offset via canonical POWER_STYLE_OFFSET (core.types.py, 28-entry
dict keyed by both display names AND enum-string keys; single
source of truth for world_init + game_bridge derivation). Load-time
derivation for pre-4d saves at game_bridge._make_fighter_attrs:
`power = clamp(strength + style_offset + crc32(fid)_noise[-3..+3])`,
FORWARD-ONLY (no write-back to _fighter_data). MEASURE 1 verbatim:
OVR wobble |ΔOVR| mean=0.304, max=1.0, only 1/289 fighters shift
≥1 point — imperceptible. Training + profile + compare + tale-of-
tape all render Power. Gates G1-G6 all PASS (G1 MD5 byte-identical
flag-OFF; G2 POWER+20 → KO+TKO +3.0pp ±2.4pp ALIVE; STRENGTH+20
FLAT; G3 derivation deterministic+no-write-back; G4 zero remaining
5-physical enumerations in web-tree production code; G5 UI smoke;
G6 no god-stat). D15 POSITION CENSUS delivered as ride-along at
outputs/sm1/fight_model/p3_4d/position_census.md.

### 4e AGGRESSION (D8) — SHIPPED DARK as C24 (2026-09-04)
Machinery present, both flags False on disk. TENDENCY function
(styles.tendency_for_fighter, pure function of personality × style,
reload-stable by construction), 4-rule circumstance table (R1
behind-on-cards / R2 chin-vs-power / R3 opponent-gassed / R4
cruising), FIGHT_IQ execution lane (rock-triggered drift; ≥80
elite composure blocks 100%). BURIED FINDING: FighterRecord has
no baseline `fighting_style` attribute; style lives in
`_fighter_data['style']`. Pre-C24 AI gameplans were 100% None
since GAMEPLAN-AI-SELECT1 (bridge-scale measurement: 19026/19026
None OFF; 26.4% None + 73.6% real presets ON). G1 byte-identical
OFF (`b6f7dac91ce983f4449152445477488f`); G2 all 4 rules fire
correctly (dial + commentary); G3 IQ execution ALIVE on defining
instrument at N=1000 (IQ 50 drift 7.8%, IQ 90 drift 0.0% —
elite composure gate holds); G4 tendency table 292 fighters
deterministic 20/20 repeat-load stable. **BRIDGE-PATH DECISION
GATE (from C24 spec) fired DARK:** (b) instrument failed
(_engine_result not persisted on Path B fight dict → td/sub per
style all n=0, cannot verify grappler-vs-striker differentiation
direction); (d) win-rate swings Wrestler 55%→27% (Δ=−28.3pp) and
Striker 60%→33% (Δ=−26.7pp) both on n=20 OFF — collapses in the
strict architect-intent reading. Filed to P3-5 with numbers.


## DOCKET P3-5 — FINISH MODEL + SINGLE CALIBRATION (LAST)

### P5-B4 JUDGE RE-WEIGHT + D19 PLUMBING — SHIPPED as C33 (2026-09-05)

Two structural changes; magnitudes stay P5-C's per Van directive.

**Judge re-weight (item 4).** Six inline scoring weights at
`fight_engine.py:4537-4551` extracted to `SCORE_WEIGHT_*` named
constants at fe:638-643. `SCORE_WEIGHT_CONTROL` moved 1.5 → 4.0;
other five weights unchanged. **PROVISIONAL — P5-C certifies.**

**BASELINE INVERSION (unattributed).** Van's spec cited "baseline
99-100% wrestler share per phase0-bis T4"; measured on current
tree found **44.1% at strike_diff≥3** (production population, N=500
fights). Inversion happened somewhere between phase0-bis and C32 —
predates C29, C30, C31, C32 alike; **unattributed**. Fix direction
REVERSES from spec-as-written (target 65-80% requires INCREASING
grappling weights).

**Gate (a) BOTH ARMS FILED**:
- **Pristine C32 arm (clean instrument)**: same-rounds re-score
  OLD 46.3% → NEW 75.6% (31/41). In band on point estimate;
  Wilson CI ~±13pp at n=41 so "in band" cannot be certified.
- **Staged live-play**: OLD 22.4% → NEW 61.2% (30/49). Marginally
  BELOW band. Compound of (i) D19 asymmetry, (ii) CRN divergence,
  (iii) judge feedback via R1/R4 rules reading `self.round_scores`
  mid-fight at fi:797-803.
Gate (b) non-split flip 0.91% staged / 1.15% pristine (both under
5% threshold). Gate (c) method mix nearly unchanged (DEC −0.80pp,
draws +3).

**D19 plumbing.** Census found NO speed→stamina-cost surcharge in
the codebase; speed's stamina disadvantage is entirely emergent
action frequency. D19 as landed = named constants + Van's
asymmetric provisional. Nothing removed from speed. Aggression
drain magnitudes now at `AGGRESSION_DRAIN_SCALE_FWD = 0.15` +
`AGGRESSION_DRAIN_SCALE_PATIENT = 0.10`. Formula at fi:1747-1770.
Speed's K_SPEED_INIT and contest-composite roles untouched.

**Readings**: (a) speed+20 Δwin −18.50pp both arms (identical) —
D19 doesn't touch speed's frequency-drain net-win problem; filed
to P5-C. (b) Aggression-drain measurable: measured − aggressive
gap +8.96pp staged vs +11.25pp pristine — Van's ×0.90 patient
adopted exactly. (c) D17 cardio compression preserved (54.10%
staged / 53.82% pristine, no regression from P5-B1's ~56%).

Full filing under CLAUDE.md "FIGHT MODEL P5-B4 [COMMITTED as C33,
2026-09-05]".

NO DEPLOY (S2 freeze holds).

### P5-B3 CUTS + SPRAWL + AGGRESSION PACK + IQ — SHIPPED as C32 (2026-09-05)

Four `window_registry.py` flags flipped False → True under rule
(a) with defining-instrument sensitivity readings backing each:

- `FI_CUT_WRITER_ENABLED = True` (elbow-family cut writer at
  fi:1468-1482 → damage.cuts accumulator → two carve-out
  consumers: fe:719-722 P5-A F11 + fi:2266-2278 between-round
  cut check).
- `FI_SPRAWL_PUNISH_ENABLED = True` (sprawl-punish damage
  multiplier at fi:1395-1403 reading `_sprawl_counter`).
- `FI_AGGRESSION_RULES_ENABLED = True` (4-rule circumstance
  table at fi:703-867; R3 hurt-signal fix in this ship).
- `FI_IQ_EXECUTION_ENABLED = True` (rocked-drift lane at
  fi:869-981).

**Structural fixes this ship** (all byte-inert under flags OFF —
G0 EP1_200 MD5 identical vs pristine C31):
- **R3 hurt-signal tightening** (fi:827-841): now requires
  `opp.stamina ≤ 25 AND round ≥ 2 AND (opp.rocked OR
  opp.knockdowns_this_round > 0)`. Pre-fix step0 measured R3
  firing at ~45-51% on symmetric fixtures — stamina threshold
  alone too permissive.
- **5 collision-proof hook renames** (R1-R4 + IQ-drift):
  grep-verified zero substring collisions vs narrative/*.py +
  cage_dynasty_web/*.py. Step0 Finding #2 closed for these.

**READINGS BANKED, NOT JUDGED** (per Van's structural-only
directive):
- **Cuts HOT by 3-5×**: EP1_500 = 9.20% cut stoppages of fights
  (46/500), POP_200 = 15.00% (30/200). Van's P5-C anchor is
  1-3% of fights. P5-C dials: `CUT_BASE_CHANCE` (0.25),
  `CUT_STR_DIV`, `FINISH_CUT_STOP_THRESHOLD` (2),
  `_CUT_DOC_MAX`, `_CUT_DOC_STEP`, `doctor_check_cut_threshold`.
- **R3 overcorrection**: post-fix 0.00% fires (spec expected
  10-20% band). Three loosening candidates filed: (1) stamina
  ≤35 or ≤40, (2) broaden hurt to `health < critical_line`,
  (3) OR-instead-of-AND the two triggers.
- **R4 also 0%**: cruising-with-lead needs a lead-building
  fixture (asymmetric-cardio or live-play). Mechanism wired;
  fire-rate un-measurable on symmetric AI-vs-AI.
- **Method mix drift**: DEC −16, TKO +18, KO +2, SUB −6 on
  N=300 (cuts + aggression tilt push toward decisive endings).
- **Per-style SUB compression** (design-correct arithmetic, not
  wiring): AGGRESSION's ×1.08 strike_weight scale grows the
  action-pie total → P(sub) = sub/total shrinks. Fixed by
  design intent at fe:2375-2382. Filed to P5-C as dial choice
  (bump RANGE tilt OR damp AGGRESSION strike scaling).
- **Per-style finish rate up** across all n≥5 styles (+1.8 to
  +10.2pp under staged).

**Rider — sprawl-punish fire-count instrument limited by
`WINDOWS_LOG_ENABLED`**. P5-C should measure sprawl-punish fire
rate + Δwin with a proper probe **before** tuning
`SPRAWL_PUNISH_DAMAGE_MULT` (currently 1.25 provisional).

Full filing under CLAUDE.md "FIGHT MODEL P5-B3 [COMMITTED as
C32, 2026-09-05]".

NO DEPLOY (S2 freeze holds).

### STYLECOHERENCE1 — SHIPPED as C31 (2026-09-05)

Born styles reach the play surface. Three-part fix:
- **world_init sites 1 + 4**: attribute-read fix
  (`fighter.fighting_style` → `fighter.style`) at
  `world_init.py:3070` (C25 record stamp — dead-in-write since C25
  shipped) and `world_init.py:2801-2807` (style census counter
  feeding `_dominant_coach_type`).
- **Bridge coherence fix**: `game_bridge.py:2336-2352` reads
  `record.fighting_style` first (populated post-fix by
  world_init); falls back to per-fid seeded random only when
  empty (legacy saves + defensive). Dropped the
  `== "Balanced"` special case (Balanced is now a real world-init
  pick, not a placeholder). Forward-only per Van.
- **Sites 2+3 flag-gated**: attribute-read fix AND behavior
  wrapped behind `STYLE_CLINCH_BONUS_ENABLED` +
  `STYLE_TDD_BONUS_ENABLED` (both default False, in
  `window_registry.py`). Flip flags in later ships with their own
  readings per Van rule (a). P5-B1 filing labeled site 3
  "training modifier"; corrected here — actual code is a
  world-gen takedown_defense bonus.

Gates: **G1 COHERENCE 100.00% (278/278) — was 10.2%**;
G2 legacy safety both paths (Path A cache present, Path B record
present) 50/50 unchanged; G3 flag inertness EP1 MD5 identical,
sites 2+3 stat MD5s identical (only power MD5 differs — falsified
as noise via staged-vs-staged run, coach system dormant in probe
matching PA production `COACHES_AVAILABLE=False`); G4 behavior
banked for P5-C (Wrestler sub-att ×3, finish +13pp; BJJ Specialist
finish −16.5pp as sub-finish-rate dial input; TAKEDOWN preset
+40, BALANCED +44, CLINCH −49); G5 played-style distribution
verbatim (Wrestler 36→50, Clinch Fighter 27→3, Counter Striker
23→5 — world-init's country/stat-informed clusters reach the
surface).

Buried-finding chain now three deep: (1) C25 stamp dead-in-write
since C25 shipped, (2) bridge random deal masked the write bug,
(3) `_dominant_coach_type` always returns `boxing_coach` when
counter is empty. Site 4's fix is functionally dormant until a
separate ship unblocks `systems.coaches` import (documented at
CLAUDE.md "PA silent-fail feature losses" and reconfirmed in
this session's probe: both trees show `Coaches: 0`).

STYLE-DEAD1 (outcome-layer style-flip constructor bug) remains
independent; coherent styles do not activate that branch.

Full filing under CLAUDE.md "FIGHT MODEL STYLECOHERENCE1
[COMMITTED as C31, 2026-09-05]".

NO DEPLOY (S2 freeze holds).

### P5-B1 D17 STAMINA FLOOR + D18 POWER MODEL — SHIPPED as C30 (2026-09-05)

D17 physics: contest composites now floored at 0.5 via
`fight_engine.py:627 COMPOSITE_STAMINA_FLOOR = 0.5`. Seven LIVE
composite-scaling sites rewritten (`select_action` stamina_factor
+ `calculate_strike_success` + `calculate_grappling_success` +
`attempt_submission` sub_lockin/starting-progress +
`process_submission_progress` tighten/sub_escape). Five LEGACY
sites SKIPPED (dead-with-parent). DAMAGE-scaling floor untouched
(already 0.5 by construction). Cardio compression measured
−17.28pp (73.31% → 56.03% high-vs-low share, N=1000/arm,
starting_stamina=40); mechanism proven via R1-vs-R4 finish shift
at starting_stamina=20 (P5-C magnitude input). POP touched-zero at
natural stamina: 0/400 both arms (null result, honest — fixture
doesn't reach drain zone on 5R at natural start).

D18 physics: world-gen power unified onto strength-derivation
shape. Independent tier roll in `world_init.generate_attributes`
DELETED; persist-time formula becomes `power = clamp(20, 95,
strength + POWER_STYLE_OFFSET[style] + uniform(-8, +8))`. Per-style
ordering now follows offsets (Sprawl & Brawl +6 at mean 63.47;
BJJ Specialist −8 at mean 48.59; 15-point spread in correct
direction). Corr strength→power 0.73 → 0.91. Clamp pins healthy
(~1% of 292 fighters). D18 does NOT break D7 (POWER moves KO+TKO
channel +1.60pp vs baseline; STRENGTH flat +0.10pp — direction
preserved, saturation caveat filed).

BF-2 fixed in-scope: `core.types.POWER_STYLE_OFFSET` gained
dispatch-spelling aliases `'Ground & Pound': +3` and `'Striker':
+4`. Every dispatched style string now resolves.

BF-1 filed (STYLECOHERENCE1, post-arc). Four `world_init.py` sites
use `getattr(fighter, 'fighting_style', ...)` on GeneratedFighter
whose attribute is `.style` — reads return ''. C25 stamp dead-in-
write since C25 shipped; sibling clinch_control bonus + training
modifier + style census also silently inert. Only D18's own site
fixed here (single-purpose scope). STYLE-COHERENCE MEASUREMENT
through `bridge.new_game` (production population, seed 995700,
n=285): **10.2% born-vs-played match rate** (89.8% mismatch,
consistent with 1/11 uniform-random). Bridge overwrites world-init
style via per-fid random assignment. STYLECOHERENCE1 inherits this
as defining problem.

Full filing under CLAUDE.md "FIGHT MODEL P5-B1 — D17 STAMINA FLOOR
+ D18 POWER MODEL [COMMITTED as C30, 2026-09-05]".

NO DEPLOY (S2 freeze holds).

### P5-A FINISH MODEL — SHIPPED as C29 (2026-09-05)

D9 build: health as stoppage pressure, one check
(`fe.check_stoppage`), naming table
(`fe._finish_specialty_label`). fi's ~55 scattered stoppage
constants collapse to **8 named globals in fe.py** + §5a
already-named subs + 2 D12 carve-out thresholds (F3 leg-kick,
F11 doctor-cut writer). Rolls in F1/F2/F4/F5/F6/F7/F12/F13
removed; accumulator state kept for context; F3/F11 carve-outs
preserved; F10/F16/F0 body-cumulative untouched. New knobs:
`FINISH_CRITICAL_LINE_BASE=40.0`, `FINISH_CURVE_STEEPNESS=0.90`,
`FINISH_HEART_LINE_SHIFT=20.0`, `FINISH_CONTEXT_ROCKED_BUMP=8.0`,
`FINISH_CONTEXT_GUARD_DAMP=5.0`, `FINISH_BETWEEN_ROUND_MULT=2.5`,
`FINISH_LEG_KICK_ACCUM_THRESHOLD=6`, `FINISH_CUT_STOP_THRESHOLD=2`.
Machinery only — magnitude calibration deferred to P5-C (single
pass, item 8 below). Gates PASS: G1 label reachability (25 old
labels covered, 0 newly minted); G2 method-mix drift measured
(N=500 EP1 CRN, winner agreement 88.2%, method 35.6%; drift
expected per §5a precedent, not judged); G3 story samples
(KO/REF/DOC narrated; CORNER 0/3000 on EP1, filed as P5-C
tuning input); G4 new-string pattern check (0 newly minted);
G5 syntax + import; G6 heart defining instrument (Δ mean HP at
stoppage = +6.28pp per 40-heart-point gap, direction confirmed).
V1 pre-gen routing verification: seed 994000 fresh world, fe.
simulate_fight call count **0**, fi.simulate_narrated_fight call
count **1606**; census.md's "fe finish machines still LIVE for
pre-gen" corrected to "DEAD post-C18, deletion candidate at next
legacy-consolidation ship." NO DEPLOY (S2 freeze holds). Full
report: `outputs/sm1/fight_model/p3_5/p5a/report.md`. Full
filing under CLAUDE.md "FIGHT MODEL P5-A FINISH MODEL [COMMITTED
as C29, 2026-09-05]".

### P5-C — CALIBRATION LIST

§6 five parts + leg-kick dial (~1%). One pass, final physics, §9.
FREEZE LIFTS on green.

**P5-B4 (C33) additions**:
- **Judge wrestler-share certification** (item 4 follow-up):
  measure at LARGE N (≥300 split rounds per strike-diff threshold)
  across MULTIPLE thresholds (diff≥3, ≥5, ≥8, ≥10 at minimum).
  P5-B4 gate (a) landed at n=41 (pristine arm) / n=49 (staged) —
  Wilson CI ~±13pp, wider than the 15pp target band, so "in band"
  cannot be certified at that n. Filter sensitivity at baseline
  weights (P5-B4 measurement): 40.8% at diff≥3 → 18.2% at diff≥10.
  P5-C picks the target threshold or reports the whole curve.
  `SCORE_WEIGHT_CONTROL` (currently 4.0 provisional) is the
  primary lever; TD in the 5-15 range barely moves share at
  fixed CONTROL.
- **Speed net-win fix** (D19 follow-up): D19 formalized aggression
  drain but the census confirmed there is no speed→stamina-cost
  surcharge to remove. Speed's −18.50pp net-win rate on the P5-B4
  no-gameplan fixture is unchanged from baseline (C20's −16.5pp).
  P5-C candidates: (a) K_SPEED_INIT retune (currently the initiative
  damper), (b) speed↔cardio interaction (speed above threshold
  triggers cardio-scaled recovery bonus), (c) speed reduces
  per-action stamina cost directly (would be a new mechanism, not
  a retune). Van picks.

**GENERATOR1 Phase A (C35) additions**:
- **Pre-Phase-C graduate correlation cluster** — EXCLUDE from
  correlation-gate calibration OR expect. Phase A derives 4
  missing canonical stats (recovery/power/top_control/submissions)
  at graduation via family-adjacent formulas seeded from cardio/
  strength/takedowns/guard respectively. Those derivations
  produce graduate-only r ≈ 0.85 on the derived pairs —
  **intentionally violates the ratified variety spec §1b r-targets**
  (recovery×cardio 0.30-0.40; other family pairs 0.50-0.65).
  Bridge only: retired when Phase C makes the amateur generator
  roll all 19 canonical stats independently (graduation then
  becomes a pure transfer, no derivation). P5-C's correlation
  gates must filter graduates-generated-pre-Phase-C out, or
  expect this cluster on that sub-population.
- **Graduate-quality incoherence** (pending Van ruling per
  C35 STEP 3): graduates carry combat stats 5-8pp below the pro
  pool while `overall_rating` is set independently from
  `amateur.overall_rating` (mean of amateur's 15 pre-remap
  attrs — misses recovery/power/top_control/submissions). Downstream
  OVR readers see one number; the engine sees a different stat
  pool. Not resolved by Phase A. If Van rules recompute-at-
  graduation, P5-C inherits a consistent OVR-vs-stats relationship;
  if Van rules keep-as-is, P5-C measures the visible pool skew on
  graduated fighters and calibrates matchmaking around it.

CALIBRATION LIST:
1. Contest constants (P_EVEN/S), K_SPEED_INIT, speed-worth.
2. T2 remainder (touched-zero; drain-side/activity economy).
3. STAMINA FLOOR question (Van rules): contest composites → 0 at
   0 stamina vs damage's 0.5 floor; candidate ~0.4-0.5 floor,
   "exhausted but dangerous."
4. JUDGE-WEIGHT AUDIT (TD 8.0 vs strike 1.0; new physics lands
   more TDs — measure decision skew).
5. td_distance flat-slope diagnostic.
6. POSITION-VALUE DIFFERENTIATION (D15 step 2): per-position
   damage mults (flat ×1.25 today), initiative bonus, control
   nuance.
7. CUT-RATE + FREQUENCY ONLY (rate calibration; the full cut-
   system reality audit is CUTS1, post-arc). Reality anchor:
   ~1-3% of real MMA fights END on cuts, but cuts OCCUR far more
   often than they stop fights — occurrence and stoppage get
   separate targets. POP stoppage measured ~2× fe baseline at
   C21. Sprawl-punish magnitude rides here too.
   **P5-B3 (C32) update — cut dials for calibration**:
   `CUT_BASE_CHANCE` (0.25), `CUT_STR_DIV`,
   `FINISH_CUT_STOP_THRESHOLD` (2), `_CUT_DOC_MAX`,
   `_CUT_DOC_STEP`, `doctor_check_cut_threshold`. Post-flip
   measurement: EP1_500 = 9.20% cut stoppages of fights; POP_200
   = 15.00%. Hot by 3-5× vs the 1-3% anchor.
   **Sprawl instrument prerequisite**: sprawl-punish fire count
   isn't visible via commentary_log without `WINDOWS_LOG_ENABLED`
   for the sprawl `_win()` call. P5-C sprawl tuning needs either
   a direct `log_window_event` probe or a monkey-patch on `_win`
   to capture fire count + Δwin before touching
   `SPRAWL_PUNISH_DAMAGE_MULT` (currently 1.25 provisional).
8. Per-class method mixes + finish knobs against §9.
9. SUB-MODEL DIALS (C22 inputs): tap threshold width, refusal
   band (REFUSAL_WIDTH_BASE — all-MODERATE severity mix today,
   SEVERE/CAREER unreachable at current tuning),
   CHIN_KD_RESIST_SPREAD, COMPOSURE_ROCK_DUR_SPREAD, sub_escape
   S convention, chin damage-threshold (wiring only fires on
   head strikes ≥12 dmg = 4.5% of head strikes), guard+20
   inversion diagnosis (−17pp via select_action routing).
   Before/after instruments: verify.md T4 + gate_tables.md +
   g3_ep1_flags_on.
10. POWER DIALS (C23 inputs): unify the TWO generative models —
    world-gen power = independent tier roll + offset
    (strength-uncorrelated) vs legacy derivation = strength +
    offset + noise (strength-correlated); architect lean: seed
    world-gen from strength like derivation, one model everywhere
    (Van rules). Tier-confound fix if per-style separation should
    be world-scan-visible; enum-collapse offsets (collapsed styles
    derive with the shared enum offset); offset magnitudes.
11. AGGRESSION DIALS (C24 inputs — machinery is dark on disk;
    calibration to flip it on).
    STEP 0 — RE-MEASURE on FIXED card sets (same pairings both
    arms, N≥100 per style of interest, CRN seeds): C24's (d)
    swings were n≤20 per style across two structurally divergent
    worlds — noise-level; no dial moves until a collapse is
    CONFIRMED. Also explain the 19026-vs-11822 plan-resolution
    count asymmetry between arms (structurally divergent worlds
    schedule fights differently under different AI plans, so
    the resolve_gameplan call counts diverge; not a per-fight
    discrepancy).
    Then: fix (b) instrument (C26 shipped this — per-fighter
    td_att / td_landed / sub_att aggregates now on the Path B
    fight dict; harness reads these directly instead of a
    nonexistent `_engine_result` key).
    Diagnose Wrestler collapse: TAKEDOWN preset applies
    `range_bias=+1` (grapple_weight ×1.20, sub_weight ×1.10) —
    likely over-commits Wrestlers to takedowns, they get sprawled,
    opponent counters; candidate softens the range tilt when
    opponent is a Sprawl & Brawl / high-TDD style. R3 fires
    64.5% on symmetric-cardio fixtures (fixture-specific but
    ubiquitous — trigger too permissive); tighten stamina
    threshold OR require a rock/hurt signal alongside stamina.
    R2/R4 fire rates measured 0% on their fixtures — need real
    calibration data. TENDENCY tilt magnitudes (±1 per axis) may
    be too aggressive when composed with 4-rule adjustments.

    **P5-B3 (C32) additions**:
    - **R3 trigger dial** — post-fix (opp stamina ≤25 AND round
      ≥2 AND hurt) landed at 0.00% fires on symmetric-AI-vs-AI
      N=300; expected 10-20% band. Three loosening candidates:
      (1) stamina ≤35 or ≤40, (2) broaden hurt to
      `health < critical_line`, (3) OR-instead-of-AND the
      stamina/hurt triggers.
    - **R4 trigger dial** — cruising-with-lead 0.00% fires on
      symmetric fixture; needs asymmetric-cardio or live-play to
      measure fire rate. Mechanism wired.
    - **Sub-att compression dial** (DESIGN-CORRECT arithmetic;
      P5-B3 C32 filed): AGGRESSION dial at fe:2386-2401 scales
      `strike_weight` ×1.08 when aggr=+1, arithmetically
      shrinking `P(sub) = sub/total`. Measured cross-style
      compression on N=300: BJJ Specialist 1.51 → 0.86, Ground
      & Pound 0.75 → 0.32, Wrestler 0.57 → 0.49. Dial choice:
      (a) bump RANGE tilt (grapple ×1.20 → higher, sub ×1.10 →
      higher), OR (b) damp AGGRESSION strike-scale factor
      (×1.08 → smaller).

    STEP 0 VERDICTS (measured 2026-09-05, 720 fixed pairings
    N=120/focal-style, CRN seeds 988100+, disk flags False):
    - Wrestler-collapse REFUTED: 49.2%→49.2% (Δ=+0.0pp,
      ±2SE=12.9pp). C24's ±28pp swing was n=20 noise.
    - No confirmed >10pp swing on any focal style at n=120/arm.
    - Grappler-vs-striker td/fight direction correct but small:
      +0.14 gap (grapplers seek ground more under flag ON).
    - Sub_att/fight drops slightly for all 6 focal styles under
      flag ON — TENDENCY aggression tilt likely compresses
      grapple/sub weights against strike_weight; diagnostic
      lead for the calibration ship.
    - R3 fires ~51% of fights (after Finding #2 hook-collision
      correction: ~45%) — trigger too permissive; needs real
      gassed-signal (rock duration alongside stamina).
    - R1/R2/R4 fire rates now measured on realistic pool:
      R1 16.1%, R2 7.9%, R4 16.7%.
    - Finding #2 (measurement instrument): "smells blood"
      substring false-positives ambient commentary lines.
      Rename R3 (and other collision-prone) hook lines at the
      next fi touch to collision-proof tokens.
    - Finding #1 (out of item-11 scope but material): C25
      silently activated style-based AI plans at flag OFF for
      live production; ruled KEEP at C27 (measurement in
      `outputs/sm1/fight_model/p3_5/item11_c27/`); byte-
      identical MD5 gate on synthetic fixtures did not observe
      the change. Prompted new standing rule "equivalence gates
      run on production population when the change touches
      record shape or bridge lookups."

## DOCKET P3-6 — ACCEPTANCE + SHIP

Full P2c sweep (19 alive, no god/dead, boxing positive); method-mix
+ DEC green EP1 + POP; new-method-string pattern check in
downstream analytics (now includes C21 "TKO (Doctor Stoppage -
Cuts)" AND C22 "Technical Submission"/"Submission (Injury -" —
G1/G2 proved the three known consumers; sweep the rest); live
playtest on fresh save; deploy on proof. Post-deploy owed: PA
violence monitoring, tierA re-vintage, live-roster check.

**PRE-GEN INPUT PARITY check** (Van, 2026-09-05): pre-gen fights
via `world_init._simulate_single_fight` → `engine_simulate_narrated_fight`
carry **no gameplans / no injury_hook** by design (world_init.py:1441
site does not thread either). Live-play fights via bridge pass
gameplans (STYLECOHERENCE1 populates them from born style) and
injury_hook (bridge `_sub_injury_hook`). At acceptance: measure
pre-gen vs live-path method mix on the same population (fresh
world seed X → pre-gen fight_history bucket rates; then N=300
bridge AI-vs-AI on the SAME roster → live-path method mix). Confirm
parity, or rule the divergence deliberate (aggregate direction of
pre-gen coin-flip-fallback → real engine at C29 P5-A means pre-gen
now runs the same engine but with different inputs — expect some
divergence in finish types since AGGRESSION and IQ execution can't
fire pre-gen). Landed here so acceptance doesn't discover the
divergence at deploy time.

**Sequencing note** (Van ruling via architect rec, 2026-09-05):
**GENERATOR1 slots between P5-B4 and P5-C**. Order: P5-B4 lands
structural engine (judge weights + D19 plumbing) → GENERATOR1
lands the variety build (August rulings from the generation arc
— wiring census first, then the actual variety) → P5-C
calibrates ONCE against the final population (post-generator
distributions differ from current fresh-world distributions) →
P3-6 ships. Rationale: calibrating P5-C against pre-GENERATOR1
distributions would require re-tuning after GENERATOR1 lands,
duplicating work. One calibration pass, right population.

D14 UI (Van): attribute-display redesign — fingerprint cards (~5
grouped axes) + STANDOUT/FLAW; full 19-sheet on profile (note: the
existing Scout Report strengths/weaknesses section is the primitive
to grow into); scouting-ranges future system. UI NITS batch: reach
renders as 72"" (doubled inch mark) on fighter profile; Path A
KO/TKO specialty truncation "KO (Head K" (C22 rider); fight-
history method display decision — show choke-out ("never tapped")
and injury finishes distinctly in history rows, or keep plain SUB.

D16 (Van, 2026-09-05) — RANK-AT-FIGHT-TIME: stamp BOTH fighters'
current divisional rank (and champion status) onto the fight record
at resolution time, in live play AND world-gen history sim; display
in Fight History rows ("WIN vs #4 Oscar Torres"). FORWARD-ONLY —
existing saves' past fights show a dash, no backfill; post-freeze
universes get it from birth. Downstream payoff: quality-wins become
computable (HoF, record book, media "never beaten a ranked
opponent", D14 standout lines). Schema change — census the fight-
record shape read-only first. Lands with the D14/P3-6 batch.

## POST-ARC DOCKET QUEUE (D15)

STYLECOHERENCE1 — PROMOTED and SHIPPED as C31 (2026-09-05). See
DOCKET P3-5 section above and CLAUDE.md filing. Post-C31 queue:
- **STYLE_CLINCH_BONUS_ENABLED flip** (world_init:3159) — flag
  dark, needs before/after reading on clinch_control-driven
  behavior (clinch entries, clinch-strike damage, cage-control
  time) per C22 rule (a).
- **STYLE_TDD_BONUS_ENABLED flip** (world_init:3183) — same
  discipline; measure takedown-defense-driven behavior (TD
  landing rates for Muay Thai / Sprawl & Brawl / Karate
  matchups).
- **`systems.coaches` import unblock** — separate ship (not
  scoped for the fight-model arc). Once `COACHES_AVAILABLE=True`
  in production, site 4's coach-fits-style ripple activates
  naturally without further code changes.
- **STYLE-DEAD1 outcome-layer style-flip** — independent
  mechanism, dead-in-write at the constructor value-lookup site;
  P5-C or a later ship if Van wants style-matchup modifier
  active.

POSITIONS1: fence/cage → front headlock → standing-over-downed →
scrambles-as-windows → back-mount quality.

CUTS1 (Van, 2026-09-05) — CUT-SYSTEM (LACERATIONS) REALITY AUDIT.
P3-5 item 7 covers rate only; this docket covers the system. Scope:
- SEVERITY + LOCATION model: cuts get a location (brow, eyelid,
  bridge, hairline, scalp) and a severity that grows if re-struck;
  location drives stoppage risk (eyelid/brow ≫ scalp) and
  blood-in-eye impairment.
- IN-FIGHT IMPAIRMENT: a cut is not just a stoppage lottery —
  blood-in-eye applies a composite penalty (vision-side striking
  defense/accuracy) via the 4b WINDOW machinery while active;
  cutman quality between rounds shrinks/clears the window.
- IN-ROUND DOCTOR CHECKS: doctor can pause the action mid-round on
  severe cuts, not only between rounds; ref-initiated.
- CUTMAN / CORNER QUALITY: camp or corner rating modulates
  between-round severity reduction — a reason camp quality matters
  in-fight.
- SCAR TISSUE / RECURRENCE: career-persistent cut history raises
  re-open probability at the same location (forward-only data,
  no backfill).
- LEGIBLE DOCTOR DECISION: stoppage is a decision model, not a
  bare probability — inputs are severity, location, round context
  (round 1 vs championship round 5 leniency), title fight, and
  fighter/corner pleading; commentary narrates the inspection so
  the player understands WHY.
Emergent-story payoff: "he's fighting blind through round 5" and
"one more clean elbow ends this on cuts" are exactly the specific,
actionable beats the north star demands.

WEIGHTCUT1 (Van, 2026-09-05) — WEIGHT-CUTTING REALITY AUDIT.
Purpose/timing/consequences/decision, audited against reality.
Exists today (per stale snapshots — live census required):
body_frame 1-10 at world-gen → natural_weight_class; cut-severity
helper (0/1/2 classes below natural); coach advice channel
(hard-cut/outmuscled/aging-cut alerts, 12-wk cooldown); AI class
moves (26-wk cooldown, champions never move); player ±1 class
moves with belt-vacate + fight cancellation.
STEP 1 (read-only, fold into a convenient cc prompt): CONSUMER
CENSUS — does cut severity feed ANYTHING on fight night? Classic
looks-wired risk: a computed severity passed to nothing. The
census answer decides wiring-fix vs system-build.
Audit dimensions:
- PURPOSE: reality's reason to cut is a size advantage in the
  cage; game currently models no fight-night size edge — cost is
  signaled (coach) but benefit absent. Model the edge (frame vs
  frame within class) so the cut is a real tradeoff.
- TIMING: no fight week, weigh-in, or rehydration window exists.
  Candidate: weigh-in event with cut-difficulty roll (frame gap,
  age, camp quality) → drained/normal/strong state into fight
  night.
- CONSEQUENCES: bad cut → fight-night cardio/chin/durability
  penalty (measured, not narrated); MISSED WEIGHT event — purse
  penalty, cancelled or catchweight fight, title ineligibility,
  media story. Forward-only.
- DECISION: class choice becomes a legible tradeoff (size edge vs
  cut cost, aging curve steepens cost); coach advice already
  exists — point it at the real numbers once they exist.
Emergent-story payoff: "missed weight, title shot gone" and "the
drained champ gassed in 3" are north-star beats.

INJURY1 (Van, 2026-09-05) — INJURY-SYSTEM REALITY AUDIT.
Purpose/timing/consequences/decision, filed FROM C22 measurement
(not guesswork). Known-wired (proven): AI-card fights persist
injuries via generate_fight_injury (gb:13898-13930 pattern —
InjurySystem, recovery weeks, medical-staff reduction, news);
C22 sub injuries persist on BOTH paths via _sub_injury_hook (G2:
real injury, real fields, Δ=1); training injuries + champion-
injury-decision page exist; weight-class moves gated on
is_cleared_to_fight. Open questions (audit these):
- Do PLAYER-fight KO/TKO injuries persist? C22 mirrored the
  Path B pattern; a Path A pre-C22 equivalent was never
  confirmed. Measure, don't read.
- LIFECYCLE: medical suspensions after wars (real MMA: mandatory
  30/60/180-day), injuries lingering into next camp (training
  penalties while healing?), re-injury risk on early return,
  age interaction.
- DECISION: fight-through-it vs pull-out choices for player;
  AI pull-outs creating short-notice replacement drama (major
  emergent-story source in real MMA).
- PRE-GEN: history-sim injuries not persisted (accepted design —
  fresh saves clean); confirm this stays intentional.
Emergent-story payoff: "champ pulls out, short-notice challenger
shocks the world" and "he came back too soon and his chin never
recovered" are north-star beats.

Then: scouting-ranges, personality, generator-variety, amateur,
training dockets; PEAK103; PA timing pre-N-lock; A3-b/A3-c.

FIGHTERRECORD-FIGHTING-STYLE — SHIPPED as C25 5e84d43
(2026-09-05, C24 buried finding, architect-filed). Promoted
`fighting_style` to a real field on `FighterRecord`
(`game_state.py`) with `to_dict` / `from_dict` serialization;
world_init stamps it at fresh-fighter creation. Legacy saves
without the field default to `''` and continue to resolve style
via the C24 `_fighter_data['style']` fallback in
`_resolve_gameplan` — kept as dead-code-for-post-C25-universes /
live-for-legacy. Gates PASS: legacy load smoke; fresh world
289/289 records match `_fighter_data['style']`; EP1_200 MD5
byte-identical vs pristine C24 (`b6f7dac91ce983f4449152445477488f`).

## STANDING RULES

Fresh date + HEAD gate (last shipped: C32 35834ec. Standing
convention as of C26: the HEAD line names the LAST SHIPPED commit
and is updated in the NEXT ship's docs pass. No placeholders);
diagnose read-only first; single-purpose commits on Van's word;
stop before commit; adjusted instruments prove discrimination; a
no-op control cannot prove life; instruments match the DEFINING
instrument; verbatim over recall; arithmetic sums; docs same turn;
never hardcode saves/fighters; re-read disk docs after compaction;
twin gates decided-share, ≥2 blocks; no wiring-flag flips without a
defining-instrument sensitivity reading in a prior verify pass
(C22 rule a); hook sockets land in the same commit as their
production wire absent a stated scoping reason (C22 rule b —
heat_level is the standing counter-example); **equivalence gates
run on the PRODUCTION population when the change touches record
shape or bridge lookups — a synthetic-fixture MD5 cannot certify
bridge behavior (C27 rule, from C25 lesson)**.

## RULED SCOPING DECISIONS

S1 order · S2 freeze ACTIVE · S3 executed · S4 bridge accepted ·
S5 structural/single-calibration · S6 lever-two word · D14
attribute display (P3-6) · D15 positions three-tier · D16
rank-at-fight-time stamp (P3-6 batch, forward-only) · CUTS1
cut-system reality audit (post-arc) · WEIGHTCUT1 weight-cutting
reality audit (post-arc; consumer census first, foldable as a
ride-along) · INJURY1 injury-system reality audit (post-arc;
filed from C22 measurement) · C22 flag-flip approved on T4
defining instruments.

D17 (Van, 2026-09-05) — STAMINA FLOOR: contest-composite
stamina scalar floors at 0.5, matching damage's floor
("exhausted but dangerous"); lands in the P3-5 pass.
D18 (Van, 2026-09-05) — POWER GENERATIVE MODEL UNIFIED:
world-gen power = strength + style offset + noise (~±8 band),
same shape as legacy derivation; replaces the independent tier
roll; one model everywhere; forward-only.
D19 (Van, 2026-09-05) — SPEED-WORTH: target ≈ +6pp per +20
(in family with other single stats); activity cost routes via
AGGRESSION, not speed; K_SPEED_INIT + assist lanes calibrate
to target.
ARCHIVE1 — SHIPPED as C28 cf85a21 (CLAUDE.md split; archive at
claude/claude_md_archive_2026a.md; hash-verified verbatim).
