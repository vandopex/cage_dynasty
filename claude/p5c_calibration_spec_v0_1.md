# P5-C — SINGLE CALIBRATION PASS — EXEC SPEC v0.1 (RATIFIED 2026-09-05)

Status: RATIFIED by Van 2026-09-05, all §5 items accepted as ruled.
Successor to the ratified P3-5 spec (claude/fight_model_p3_5_spec_v0_1.md):
P5-A (C29) and P5-B (C30-C33) shipped structure with magnitudes
deliberately deferred HERE. GENERATOR1 (C35-C42) shipped the final
population first, per Van's sequencing ruling — one calibration pass,
right population. **FREEZE LIFTS on P5-C green** (per the ratified
P3-5 contract), followed by P3-6 acceptance + deploy.

PRINCIPLE. This is a TUNING arc, not a building arc. Dials move;
mechanisms do not. If a target proves unreachable by dials alone,
that is a finding filed for Van — never an excuse to quietly add a
mechanism mid-calibration ("fix the engine, not the output" cuts both
ways: no new engine parts sneak in dressed as tuning).

SOURCE-OF-TRUTH NOTE. The canonical accumulated calibration list
lives in the DISK scope doc (claude/fight_model_p3_scope_v0_1.md,
"P5-C — CALIBRATION LIST" + its C30/C33/C35 addition blocks). This
spec defines the STRUCTURE, ORDER, TARGETS, and GATES; exec STEP 0
reconciles the disk list against this spec's dial groups verbatim and
reports any item not covered (those land in Group E with a note —
nothing silently dropped).

---

## 0. TARGETS (the ratified §9 contract, fight_model_v1_0)

Method mix on the production population (bridge AI-vs-AI, fresh
worlds, N large enough that each bucket's Wilson CI is under ±3pp):

- KO ~22% · SUB ~20% · TKO ~16% · DEC ~40% (acceptance BANDS, not
  points: ±5pp per bucket unless Van tightens at ratification)
- Cut stoppages: 1-3% of fights (currently 9-15% — HOT 3-5×)
- Split-round wrestler share: 65-80% CERTIFIED at large N
  (≥300 split rounds per threshold, multiple strike-diff thresholds)
- Per-division gradient: heavier divisions finish more, lighter
  divisions decide more (direction + monotonic-ish trend, exact
  magnitudes banked not gated — first arc with the D18/class-offset
  population, so this is a MEASURE-AND-RULE, not a pass/fail)

Known distance at last measurement: finish rate ~89% vs ~60%,
true-KO ~7% vs 22, DEC ~10% vs 40. The gap is large and expected —
every finish knob shipped structural-not-tuned.

## 1. PHASE 0 — THE DASHBOARD (read-only, one instrumented run)

One baseline measurement on the C42 tree before ANY dial moves.
Everything after is judged against this. Per-arm N ≥ 500 fights.

Dashboard contents (one JSON + one table set):
a. Method mix — pool + per-division + per-round-of-stoppage.
b. Cut-stoppage rate; doctor/corner/referee label distribution.
c. Rule fire rates: R1/R2/R3/R4, IQ-drift, sprawl-punish (proper
   probe, not the C32 proxy), cut-writer.
d. Judge: split-round share at strike-diff ≥3/≥5/≥8/≥10; non-split
   flip stability.
e. Sensitivity ladder on the DEFINING instruments (fixed-card CRN):
   speed+20, cardio+20, chin+20, power+20, heart+20 → Δwin each.
   (Power+20 has never been measured post-D18 — first reading.)
f. Per-style output census: method mix, TD/sub attempt rates, pace
   per style (doubles as STYLE-OUTPUT1's baseline — one run, two
   filings).
g. Stamina economy: touched-zero rate per round, R2 touched-zero
   (POP target <40%, last read 52.1%).
h. Graduate-population note: pre-Phase-C graduates EXCLUDED from any
   correlation-derived reading (C35 bridge cluster, filed).

RIDE-ALONG READ-ONLY CHECK (from C41): is the PRO-side trait
assignment predicated on stats or random? If random stat-claiming
labels exist in the pro pool, file for a C41-style cleanup ship —
do not fix inside P5-C.

## 2. DIAL GROUPS, IN ORDER (dependency-sorted)

GROUP A — FINISH ECONOMY (biggest gap first).
Dials: the 8 finish knobs (FINISH_CRITICAL_LINE_BASE, HEART_LINE_
SHIFT, CURVE_STEEPNESS, BETWEEN_ROUND_MULT, rocked bump, guard damp,
LEG_KICK_ACCUM, CUT_STOP_THRESHOLD) + FI_CUT_WRITER magnitudes +
SPRAWL_PUNISH_DAMAGE_MULT (1.25 provisional since C21).
Targets: overall finish rate into band; cut rate 1-3%; KO-vs-TKO
split moving toward 22/16 (KO share is partly Group A steepness,
partly power distribution — measure which before blaming either).
Rule: sweep on fixed-card CRN sets; verify on production population
(C27 rule); every accepted dial re-runs the dashboard deltas.

GROUP B — DECISION QUALITY (only after A lands, since DEC volume
depends on A). Dials: judge SCORE_WEIGHT_* (CONTROL=4.0 provisional).
Targets: wrestler-share certification at large N across thresholds;
non-split flips <5%; draw rate sane (<2%). NOTE: judge weights are a
BEHAVIOR dial too (R1/R4 read cards) — expect coupled movement,
measure both surfaces.

GROUP C — RULE FIRE RATES. Dials: R3 loosening candidates (three
filed at C32), R4 conditions, IQ-drift scale, aggression-drain
magnitudes if pacing distorts (D19 constants).
Targets: R3 and R4 fire at plausible rates (>0, <30% of eligible
rounds — exact bands proposed from Phase 0 data, Van rules); the
C24-C32 machinery finally observable in live output.

GROUP D — ATTRIBUTE WORTH. Dials: contest constants (P_EVEN/S per
class), K_SPEED_INIT, COMPOSITE_STAMINA_FLOOR (0.5, Van may revisit),
sub-attempt weight scale.
Targets: sensitivity ladder lands every +20 in a POSITIVE, bounded
band (Van ratifies the band at Phase 0 review; speed's -18.5pp is
the known pathology — Van picks among the three C33-filed options
when the Phase 0 ladder is in hand). Sub-attempt rate: wrestler/BJJ
attempt profile preserved (C31's ×3) while pool sub-finish lands
near 20%.

GROUP E — RECONCILED REMAINDER. Whatever the disk-list reconciliation
surfaces that Groups A-D don't cover (touched-zero economy, leg-kick
dial, etc.). Each gets: dial named, target named, or explicitly
DEFERRED with Van's initials in the filing.

## 3. METHOD RULES (arc law, inherited + specific)

- One group at a time; dashboard re-run between groups; a group's
  accepted dials FREEZE before the next group starts (no cross-group
  drift hunting).
- Fixed-card CRN for sweeps; production population for acceptance
  (C27 rule); tolerance bands not byte-MD5 (uuid4 rule).
- Instruments must match the DEFINING instrument; any instrument
  adjustment must re-prove discrimination before its reading counts.
- Every dial change: single-purpose commit, stop-before-commit,
  before/after deltas in the filing. Expect 3-6 commits, not one.
- Unreachable target = finding for Van, never a silent mechanism add
  and never a quiet target rewrite. Wrong numbers documented as
  false, not dropped.
- Pre-Phase-C graduate exclusion honored in every correlation-based
  reading.

## 4. ACCEPTANCE + FREEZE LIFT

P5-C is GREEN when: §0 method-mix bands hit on production population
(or Van explicitly rules an exception band); cut rate in 1-3%; judge
certification done; R3/R4 alive; sensitivity ladder positive across
all five attributes or Van-ruled otherwise; dashboard archived as the
new baseline in the filing.

On green: FREEZE LIFTS. Then P3-6 acceptance (P2c sweep, method-
string sweep, SAVELOAD1 deploy gate, live playtest, D14 UI batch +
nits, D16 rank-stamp, PRE-GEN INPUT PARITY check) and deploy ON
PROOF (SHA match + Files-API grep; commentary.py path caveat).

## 5. ⚖ RULED (Van 2026-09-05: all four accepted)

1. §0 target bands (±5pp per method bucket) + cut 1-3%.
2. Group order A→E and the freeze-between-groups rule.
3. Phase-0-then-rule cadence for the open Van-picks (speed fix
   option, R3 bands, stamina-floor revisit) — decided when the
   dashboard is in hand, not before.
4. Expected shape: 3-6 tuning commits inside one arc, each gated.
