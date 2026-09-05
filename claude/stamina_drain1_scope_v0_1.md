# STAMINA-DRAIN1 — design scope v0.1 (2026-08-31) + addenda A, B

Status: **SHIPPED 2026-09-01** — C12 (engine, `a6b2c05`) + C13
(docs, `727dee8`) split commits landed. Full B1-B9 arc complete
through Gate 1c CERTIFY at file-constants K=0.6, S=0.5. Deploy
HELD pending STAMINA-OFFENSE-CURVE1 docket verdict (Van ruling)
— docket parked at `claude/stamina_offense_curve1_docket_v0_1.md`.
Baseline HEAD pre-ship 71e94de; post-ship HEAD 727dee8.
Signal 1 = scope + B2, given 2026-09-01. Mid-arc rulings B7 (donor
recipe), B8 (frontier rerun scope), B8-a (discrimination-criterion
amendment) all given 2026-09-01. Signal 2 (= B9 constants) given
2026-09-01 after Gate 1b frontier report on POP-POOL1.
Gate history: Gate 1a PASS (2nd pass, B4/B5/B6); Gate 1b frontier
report on POP-POOL1; Gate 1c CERTIFY at file-constants + closeout
(REVEALED-not-created two-engine finding, rider filed to TWO-ENGINE
CONSOLIDATION arc at CLAUDE.md:691-711).

## The questions and the answers taken

Q1 What cardio means: cardio = cost of every action DURING a round;
   recovery = refill at the bell. Two stats, two channels, no overlap.
   In-round regen (+0.5/exchange, fi:1651-52) is realistically cardio
   too — lever TWO, after this one is measured alone (no double-dip).
Q2 Mechanism: multiplier on every spend at the choke point fe:611
   spend_stamina (13/13 sites). props[2] relative costs untouched
   (strike identity preserved). Payer's cardio scales payer's cost —
   defender drains (body, KD, TD impact) scale by the defender's cardio.
   Aggression ±15% (fi:1291) stacks before the choke, untouched.
   RULED 2026-09-01: defender-side scaling KEPT (one rule, one site;
   see addendum B for the measurement condition).
Q3 Shape: g(cardio) = 1 + S*(60 − cardio)/40. Linear about the
   population mean; one spread knob. NOT clamped (see addendum A2).
Q4 Global scale: K at the same choke point: effective = amount*K*g.
   This is the "drain constants" lever in one place. Expected 0.6–0.8;
   found by measurement.
Q5 Targets — stated where the mechanism is isolable, NOT per bin
   (bins are confounded by activity volume 2.4× HH:LL, Gate 0):
   T1 cardio's worth (clone-and-vary, same fighter, cardio 30 vs 90,
      fixed opponent): R1 round-close differs ≥25; R3-end ≥20.
      Today ≈0 (floor-saturated).
   T2 floor stops being the norm: R1 zero-fraction <25% (today 55–69%);
      R2 <40% (today 62–75%).
   T3 population not wrecked: median R1 round-close on Tier A-corrected
      35–50.
   T4 archetype signature REPORTED not gated: per-bin round-close;
      LH/HL crossing should appear. Van's reference shape:
      HH 55/45/40, HL 35/30/28, LH 50/35/25, LL 30/18/12.
Q6 Balance consequence: fresher fighters defend better → fewer late
   finishes, more decisions. Measured per pairing; DEC vs
   POOL-DEC-RATE1 band with explicit in/out call. Out-of-band = a
   second decision for Van, never silently tuned back.
Q7 What the player sees: "breathing heavy already" becomes true;
   training cardio changes R1 visibly; camp + cut (C11) finally bite;
   aggression dial becomes a real trade (personality hook, later).
Q8 Not decided here: regen scaling; floor behavior at zero;
   PREGEN-PEAK103; fatigue accumulation in live play; any
   action-selection change.

## Spec

CHANGE (single site): fe.FighterState.spend_stamina(amount):
  effective = amount * DRAIN_SCALE_K * (1 + DRAIN_CARDIO_S*(60 - cardio)/40)
  self.stamina = max(0, self.stamina - effective)
Two named module constants beside the method. FighterState carries
cardio_rating (class default 60 → 1.0×, fail-open like C11's != 1).
Pass cardio_rating= at BOTH FighterState constructions: fi (inside
_init_fight — see B4; "_init_engine" was a phantom name, retired) and
fe.simulate_fight (f{1,2}_state = FighterState(...)). Anchors
grep-verified at edit time.

GATE 1a — MECHANICAL EQUIVALENCE at K=1.0, S=0.0 — as originally
  written this gate was WRONG (architect error, retired-not-deleted):
  it compared post-C11 code against the pre-C11 tierA_corrected
  baseline, which C11's W2 filing already showed drifts on cut fights
  (115 winner flips). RE-SCOPED 2026-09-01 and EXECUTED as:
  same-HEAD A/B (stash vs working tree) on the full 2100, row-by-row
  JSON; corroboration split no-cut 1308/1308, cut 677/792 vs old
  baseline (the C11 W2 numbers); 7 fixture hashes unchanged; ledger
  residual 0; consumption proof 20/20 cardio_rating == fighter.cardio
  live AND pre-gen with values printed (discrimination: non-default,
  varying). Result: PASS — see B5/B6.

GATE 1b — BOUNDED SEARCH, report only:
  PRECONDITION (ruled 2026-09-01): regenerate tierA_corrected at HEAD
  (post-C11 vintage; old retired-not-deleted, C8 pattern) BEFORE 1b,
  else per-cell method/DEC comparisons are confounded by C11's cut
  effect. DONE 2026-09-01: tierA_corrected_c11/ accepted on no-cut
  1308/1308 identity + C11 W2 115-flip match. The landing-CSV proxy
  used in that run's 4c analysis is BANNED (contradicts certified
  Gate 0 numbers on the same data); ledger only.
  Donors (2): heart=60, chin=60, clinch_control=50, clinch_striking=50
  (defeats Clinch gate fe:1453 and Pressure gates fe:1458/1492 across
  legal cardio); different striking/grappling mixes. Style tag logged
  per fight; GATE: identical across all cardio levels per donor, else
  donor rejected. Cardio 30/50/70/90, N=200 each, fixed all-60 opponent.
  Per level: R1/R2/R3 round-close; first-zero call index (median, p25,
  p75); requested vs effective drain; regen; zero-fraction; ACTION-FAMILY
  MIX (addendum A3); SELF vs OPPONENT-INFLICTED drain split (addendum B).
  Grid K ∈ {0.5,0.6,0.7,0.8,1.0} × S ∈ {0.3,0.5,0.7} (15 cells,
  ~55k fights, ~40 min). Per cell also Tier A-corrected 2100 same seeds
  (post-C11 vintage): median R1 close, zero census, per-bin round-close
  (T4), method distribution per pairing vs baseline, g-range flag
  (addendum A2). One 15-row table with T1/T2/T3 marks. STOP. Van +
  architect choose (K,S) → signal 2.

GATE 1c — CERTIFY chosen constants: full before/after on Tier A-corrected
  (bins, zero census, method shifts, DEC vs POOL-DEC-RATE1 in/out);
  clone T1 at chosen constants; 7 fixture hashes EXPECTED to break →
  re-baseline (new table + new probe sha256; old retired-not-deleted,
  C8 pattern); pre-gen parity (one clone pair live vs pre-gen, same
  cardio, R1 drain agrees to the ledger); ledger residual 0; diff shape
  declared before edit. Consequences filed: violence shift; cut/fatigue
  now MATTER (re-run C11 cut-direction table — expect a direction);
  PEAK103 exposure widens marginally as K shrinks (scope unchanged);
  live baselines re-vintage on deploy. STOP before commit; docs block
  read verbatim by architect.

## Addendum A (post cc review, 2026-08-31)

A1 Anchors — SUPERSEDED by B1 (HEAD-verified 2026-09-01).
A2 No clamp on g. Edge at S=0.7: g(99)=0.32, g(1)=2.03. Gate 1b reports
   g-range per cell and flags cells with g(99)<0.4 or g(1)>1.8 as
   "outside intended envelope." K=0.5×S=0.7 is expected to fail T3 and
   the method check — it brackets; say so before the numbers arrive.
A3 Un-pinnable confound: fe:2073-2084 late-round _cardio_gap action
   multiplier reads cardio directly (gap 30 at cardio 90 vs all-60
   opponent → up to 1.30 from R1). Changes action MIX, not cost.
   Gate 0(c) bound: ≤7pp outcome effect worst case, hence T1 ≥25.
   Gate 1b logs action-family mix per cardio level per donor; filing
   states T1 = drain wire + pre-existing fe:2073 channel, mix table as
   evidence. Neutralizing fe:2073 is out of scope (lever-two double-dip
   review).
A4 Grid cost ≈ 15 × 3,700 fights ≈ 40 min wall. Feasible in one pass.
A5 PEAK103: exposure window widens slightly as K<1 (first spend drains
   less); still bounded by first recover (fe:3813/3814). Filed at 1c.

## Addendum B (cold open + Gate 1a execution, 2026-09-01)

B1 HEAD-verified anchors (cc grep, 71e94de): fi._init_fight (B4)
   constructions fi:510-517 (fighter1_state) and fi:518-525
   (fighter2_state); fe.simulate_fight constructions fe:4067-4074
   (f1_state) and fe:4076-4083 (f2_state). Each ends with the C8
   recovery_rating= kwarg; cardio_rating= goes on the line after it.
   The v0.1 numbers (fi:503-515, fe:4068-4082) were pre-C8 and are
   retired as wrong.
B2 Defender-side scaling ruling: KEPT. Rationale: one rule at the one
   choke point; tagging 13 sites payer-vs-victim is a looks-wired
   surface. Risk (cardio becomes both offense cost and defense tax,
   may be what breaks T3) is measured, not pre-empted.
B3 Measurement condition for B2: Gate 1b per-level report splits
   effective drain into SELF-inflicted (own actions) vs
   OPPONENT-inflicted (body, KD, TD impact, any drain the other
   fighter's action charges). Instrument-only; no engine change.
   Ambiguous spend sites are LISTED, never guessed. If the
   opponent-inflicted share is what fails T3 at otherwise-good
   cells, that is a Van decision at signal 2, not a silent narrowing.
B4 PHANTOM NAME RETIRED: fight_integration.py has no _init_engine.
   The method constructing FighterState in NarratedFightSimulator is
   _init_fight (fi:482). Every earlier citation of "_init_engine"
   (this doc v0.1, Gate 1a harness comments) was false. Rider owed to
   next docs commit.
B5 GATE 1a RESULT (2nd pass, 2026-09-01, HEAD 71e94de + uncommitted
   +22/-4): same-HEAD A/B 2100/2100 identical (winner, method, round);
   no-cut 1308/1308 and cut 677/792 vs old baseline (matches C11 W2);
   fixtures 7/7 raw + 7/7 norm (norm baselines = C8 filed table,
   CLAUDE.md:5274-5282, corroborated by pv15's dict); ledger 7204
   fighter-rounds, max |residual| 7.1e-14; wiring 20/20 both paths,
   verbatim pairs on disk (gate_1a_2nd_step3_pairs_out.txt), 14
   distinct cardio values [33..95], zero on default-60, live/pre-gen
   agree per fid. PASS. Harness hazard filed: game_bridge force-reload
   invalidates pre-bound monkey-patches (re-bind fe/fi after first
   _make_test_bridge; gate_1a.py carries the latent form).
B6 SUMMARY-TABLE FABRICATION CAUGHT (filed as a wrong number): cc's
   pass-2 report's per-cell summary claimed HL cardio 85..90,
   LH 33..65, LL max 52. The verbatim listing shows HL 62–65,
   LH 85, LL max 55 — three of four cells wrong. Gate verdict
   unaffected (criterion was wiring, not cells), but the summary was
   recalled, not read. Evidence beats summary; verbatim printing
   stays mandatory. Rule: every report table names the output file
   it was computed from.
B9 CONSTANTS RATIFIED — signal 2 (2026-09-01, Van): K=0.6, S=0.5.
   Chosen from the POP-POOL1 frontier report over K=0.5/S=0.5
   (the T1-passing corner) because T3 (population median R1 close
   in 35-50 band) is the load-bearing population-health gate; T1's
   "cardio-lever worth" question can be re-measured at file-
   constants (this Gate 1c orders it). MEASURED at K=0.6/S=0.5 on
   POP-POOL1 (source: gate_1b/pop_pool1/frontier_table.csv):
     • T1 (cited from grid, clone arm): T1_R1 = 39.8pp (passes ≥25);
       T1_R3 = 14.3pp (fails <20). Grid used B7 donor recipe
       (heart=50, chin=50). T1_R3 RE-MEASURED in Gate 1c at
       file-constants — see 3c.
     • T2 PARTIALLY MET: R1 zero-frac 35.5% (target <25%, misses
       by 10.5pp); R2 zero-frac 48.1% (target <40%, misses by
       8.1pp). REMAINDER ASSIGNED TO LEVER TWO — Q1's in-round
       regen +0.5/exchange at fi:1651-52, a separate ship on the
       same cardio-governs-breath axis. THRESHOLDS NOT BENT: the
       T2 target survives; STAMINA-DRAIN1 delivers the drain half,
       a future lever-two ship delivers the recovery half.
     • T3 IN-BAND: median R1 close 46.3 (in [35, 50]).
     • DEC shift (Q6 direction inverted): identity 52.2% DEC →
       K=0.6/S=0.5 28.6% DEC (−23.6pp). Q6 predicted "more
       decisions" from fresher fighters (defends-better dominant);
       measured "more finishes" (presses-better dominant on
       balance). ACCEPTED-OPEN as a separate design question;
       Gate 1c reports the DEC-per-pairing shift on tierA_c11 for
       the record but does NOT resolve. PA violence-shift
       monitoring owed post-deploy.
     • g-envelope: g_lo=0.51, g_hi=1.74. Within A2 [0.4, 1.8].
   Gate 1c orders: fe constants edit (2 lines + Hunk A comment
   update, no other hunks); BEFORE/AFTER on POP-POOL1 (must
   reproduce K=0.6/S=0.5 frontier cell exactly — file vs setattr
   parity) + tierA_c11 2100; fresh T1_R3 clone measurement at
   file-constants; 7 fixture hashes EXPECTED to break with
   re-baseline (unchanged arm is a red flag, not a pass); pre-gen
   parity (one clone pair live vs pre-gen R1 drain agreement);
   C11 cut-direction re-run (drain fix should surface a direction
   floor saturation previously swallowed). STOP before commit.

B8-a DISCRIMINATION CRITERION AMENDMENT (2026-09-01, ratified by
   Van, Option A). MEASURED: POP-POOL1 built to match world-gen
   population cardio quantiles exactly (median 57 / p10 39 / p90 78,
   all gaps 0 pts). Identity run (K=1.0, S=0.0) on POP-POOL1
   produced R1 zero-fraction 0.5498, R2 zero-fraction 0.6118 —
   both marginally below Gate 0's 55-69% / 62-75% bands. Van's
   adversarial re-read: at identity, cardio does not touch drain
   (S=0 → g=1.0 for every fighter regardless of cardio); so a
   lower-cardio pool at identity differs from the skewed Tier A
   pool only through cardio's five non-drain consumers (fe:2073
   action multiplier + siblings) and attribute co-generation, not
   through drain. Gate 0's 55-69% band was measured on the
   *skewed* Tier A pool, not on world-gen population — it is a
   Tier-A-pool statistic, not a world constant. Requiring
   POP-POOL1 to land inside it is the same pool-specific-metric-
   as-universal category error B8 was filed to fix, one level up.
   BAND RETIRED as pool-specific (retired-not-deleted; the source
   measurement in Gate 0(b) filing remains as a Tier A statistic).
   AMENDED CRITERION for pool discrimination: "pool reproduces
   the broken-world signature at identity — majority of R1
   fighter-rounds hit the stamina floor, and median R1 close
   sits at the floor (0.50, the min-observable value)." Both
   overwhelmingly true on POP-POOL1 identity (R1 zero-frac 55%,
   R2 61%, R3 63%; median R1 close = 0.50). The pool discriminates
   the broken world from any plausible frontier cell — the gap
   between identity's ~55% R1 flooring and T2's <25% target is
   30pp, and the criterion-miss of 0.02pp is noise relative to
   effects the frontier is measuring. POP-POOL1 identity run
   BANKS as BEFORE for the frontier cells; not re-run. Proceeding
   straight to five frontier cells (K, S) ∈ {(0.5, 0.5), (0.6,
   0.5), (0.6, 0.4), (0.5, 0.4), (0.7, 0.5)} on the same schedule
   / same seeds / same ledger.

B8 FRONTIER RERUN ON POP-POOL1 (2026-09-01, ratified by Van;
   project copy carries the full arc through the frontier plan;
   cc-constructed from Van's frontier-plan prompt when no distinct
   paste was included — Van may resync a different version if this
   diverges). MEASURED PREMISE: Gate 1b's original 20-fighter Tier A
   pool OVERREPRESENTED cardio. Direct measurement via
   bridge.new_game() production path across 4 fresh worlds (N=1155):
   population median 57.0, p10 39, p25 47, p75 68, p90 78; Tier A
   pool median 75.0, gap +18pp. Source:
   outputs/sm1/stamina_drain1/gate_1b/cardio_distribution.txt.
   The Tier A HH/HL/LH/LL bin selection was designed to sample at
   cardio ~85+ / ~<65 bin boundaries, which under-samples the
   population's [50-60) modal bin (306 fighters, 26.5% of the pop).
   CONSEQUENCE: Gate 1b's T2 (population zero-fraction) and T3
   (population median R1 close) as reported are population-specific
   artifacts of pool composition; the "unpassable" bracket in the
   corrected master table is not established on the world the
   complaint originated from. FRONTIER SCOPE: build POP-POOL1
   (~50 fighters stratified from world-gen output to match measured
   distribution's median/p10/p90 within ~2pp) and rerun T2/T3 on
   five cells around the T1-passing corner and its T3-adjacent
   neighbor: (K,S) ∈ {(0.5,0.5), (0.6,0.5), (0.6,0.4), (0.5,0.4),
   (0.7,0.5)}. T1 NOT rerun — clone arm did not depend on pool;
   grid values cited. DISCRIMINATION PROOF (load-bearing): POP-POOL1
   at IDENTITY (K=1.0, S=0.0) must reproduce Gate 0's R1 55-69% /
   R2 62-75% zero-fraction ranges on the same instrument. In range
   → pool certified, doubles as BEFORE. Out of range → STOP; pool
   or schedule is broken, not the world; do not tune. Schedule
   declared once and held identical across identity + all frontier
   cells. Method distribution per cell reported vs identity run
   (Q6 signal, report only). Ratification signal 2 (constants K,S)
   remains pending frontier report.

B7 DONOR RECIPE SUBSTITUTION + ANCHOR DRIFT (Gate 1b style-tag
   gate, 2026-09-01, RULED by Van): heart=50, chin=50 for BOTH
   donors, both sides. Cardio spread 30/50/70/90 unchanged.
   Wrong number in v0.1 spec + Addendum-A recipe: "heart=60,
   chin=60 defeats Pressure gates fe:1458/1492 across legal
   cardio" is FALSE-BY-1 at cardio=90. Measured on striking donor
   (boxing=80, kicks=75): pressure_score = (cardio+heart+chin)/3
   = (90+60+60)/3 = 70.00 EXACTLY MATCHES the primary
   pressure_fighter gate threshold at fe:1478-1481
   (`if pressure_score >= 70 and striking_score >= 60`). Tag
   flipped from kickboxer at cardio 30/50/70 to pressure_fighter
   at cardio=90 — donor-rejected per scope's style-tag gate.
   Anchor drift: v0.1 cited fe:1458/1492 for the two pressure
   gates; at HEAD 71e94de the primary is fe:1478-1481 and the
   secondary (`pressure_score >= 65 and striking_score >= 58`) is
   fe:1512-1515. 20-line drift each. Grappling donor unaffected
   at any cardio (striking_score = (55*2+50)/3 = 53.33 defeats
   the striking_score>=58/60 half of both gates). Option A
   ratified: heart=50, chin=50 → pressure_score(cardio=90)
   = (90+50+50)/3 = 63.33, which defeats both primary (>=70) and
   secondary (>=65) with 1.67-point margin. Cardio 30/50/70
   pressure_scores drop to 43.33/50.00/56.67 — well below either
   gate. SIDE EFFECT accepted knowingly: chin=50 (was 60) means
   donor takes 5 fewer health points (health=100 + chin*0.5),
   so gets finished slightly more often; fewer fights reach R3;
   T1 R3-end sample thins. Instrument reports R3_n per cardio
   level in clone.csv; no compensation applied. Rule reiterated:
   "looks wired, boundary says otherwise" — measurement precedes
   assumption. Third instance of the recall-instead-of-read
   pattern this arc.

## Ratification signals
Signal 1 (scope): GIVEN 2026-09-01.
Signal 2 (constants): Van's literal choice of (K,S) after Gate 1b.
Commit approval: separate, after Gate 1c report + diff read verbatim.
