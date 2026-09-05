# Post-C13 sequencing — REVISED 2026-09-02 (Fork B ruled)

State: C12 a6b2c05 + C13 727dee8 landed. Working tree carries the
DMGCURVE1 identity wire (fe +15/−1, inert, uncommitted — disposition
decided at Fight Model Phase 1). Deploy still HELD; architect now
recommends DEPLOYING the C6→C13 chain with the elite finish-fest
filed as a known live issue (Fight Model is weeks-scale; holding
buys nothing) — VAN'S CALL, not yet given.

## How we got here (evidence chain, all on disk)

DMGCURVE1 Gate 1b grid: 0/12 cells moved EP1 DEC (1.1-1.5% across
the whole PIVOT×COMPRESS surface) — damage-channel lever REFUTED.
Ablation r1 (pin=20): all channels restored → only 7.8% DEC —
governor "refuted" (wrong: under-dosed; architect's pin choice).
Ablation r2: C1 (true pre-B9 control on EP1) = 32.9% DEC — dead
center of Van's 25-45 band; B9 caused the elite finish-fest;
G-ALL@5 = 67% — channels carry the whole mechanism. Governor story
survives; both earlier fitted stories (damage-channel, one-sided-
cancellation) retired.
Ablation r3: dose curve monotone, C1-equivalent at pin=8; weights
at pin 8: SUB +9.2, DMG +2.4, SEL 0.0 (but inverts finish mix),
SUCC −0.8; super-additivity ~3×; SUB+DMG pair = 24.7%.
MAGNITUDE FINDING: reaching 33% DEC via stamina curves requires
suppressing fresh fighters to near-exhaustion effectiveness (dose-8
damage factor 0.54 < the curve's own s=0 floor) — a curve fix would
make the stamina bar a lie. Sidedness was NOT isolated by the
ablation (pins were two-sided); "offense-side channels do the work"
remains hypothesis, not finding.

## FORK B RULED (Van, 2026-09-02): THE FIGHT MODEL arc

The engine's offense-to-finish balance was calibrated in the
floor-saturated era against fighters at 10-30% effectiveness;
mutual exhaustion was the shim. B9 unmasked an untuned balance.
Fix the calibration, not the stamina curves. Van's design mandate:
"pull out everything and look into the fight — make the code make
sense"; math that makes sense, creative not gimmicky; attributes
evenly important where possible. This arc ABSORBS the two-engine
consolidation (calibrating twice on divergent engines is waste).

Design principles (architect-proposed, Van-aligned):
- NO NAKED MULTIPLIERS: everything flows into attacker/defender
  composites assembled in one visible step per side.
- ONE CONTEST FUNCTION: every contested event = A vs D through a
  standard form (start Bradley-Terry A/(A+D); logistic with one
  spread knob where sharpness needs tuning). Bounded by
  construction → no-determinism becomes structural.
- Situational factors (stamina, aggression, position, rocked, cuts)
  scale composites, never results; curve shapes chosen on purpose.
  Stamina stays linear-down-from-full once base balance is right.
- Finish machinery calibrated LAST against declared target tables
  (elite-peer DEC 25-45; method mixes per matchup class; Van's T4
  reference shapes). Old constants retired-not-deleted.
- NO DEAD STATS, NO GOD STATS, measured: attribute-sensitivity
  table (clone-and-vary ±1 SD per attribute → Δwin%) as a standing
  per-build gate. Exactly-even importance rejected (attributes have
  scopes); even-expected-importance with floor and cap is the
  target.

Phases:
P0 FIGHT-MATH-CENSUS (read-only, ACTIVE): as-built extraction of
   every formula/constant in both engines' strike/grapple/finish
   pipelines + engine-vs-engine comparative evaluation feeding the
   consolidation-direction decision (Van: "take notes on which one
   works best / has better numbers").
P1 THE FIGHT MODEL v1 doc (Van + architect, design phase, no code).
   Includes: which loop survives (evidence from P0), the DMGCURVE1
   wire's disposition, deploy timing if still unresolved.
P2 Attribute-sensitivity baseline on the current engine (before).
P3 Implement = consolidation, gated throughout (DRAIN1 pattern).
Lever two (regen) folds into P1's model rather than shipping
separately. Instruments carried forward: EP1, POP-POOL1, certified
ledger, ablation wrappers, C1 reference world.

## Standing riders (unchanged)

fi:623/625 K×g-bypass fatigue drain: accepted, re-opened at
consolidation (now P1/P3). B4 phantom name: filed at C13. Amateur
pool cardio distribution: unmeasured, open. PA violence-shift
monitoring owed post-deploy. tierA re-vintage owed post-deploy.
Live-roster violence check owed on next live card. M2-behavioral +
fi-fatigue-exclusion riders: answered by cc 2026-09-01, filed.

## P1 RULINGS (Van, 2026-09-02, post-#22 measurement)

1. SURVIVING ENGINE: fi (fight_integration) is the consolidation
   chassis. fe-only mechanisms (cut writer, heat system,
   failed-grappling counter damage) are carry-over candidates to be
   merged deliberately during P3, not lost. Evidence: P0 comparison
   (both engines in-band at identity on EP1 — fi 32.91% / fe 29.74%
   DEC; POP@B9 fi 28.57% / fe 42.04%), fi's richer finish/style
   mechanics, correct KD-scoring call, activity-aware standup.
2. DEPLOY: GO. C6→C13 (9 commits, HEAD 727dee822aeb628813c0467ab38e029044dc0165)
   pushed + deployed to PythonAnywhere on proof (SHA match +
   running-path grep). Elite finish-fest ships as a known live
   issue (Fight Model is weeks-scale). Post-deploy owed items now
   due: PA violence-shift monitoring, tierA re-vintage, live-roster
   violence check on next live card.
3. DMGCURVE1 WIRE: KEEP as a future dial (proven byte-inert,
   3680/3680 at Gate 1a). Remains uncommitted pending Van's literal
   commit word (C14 candidate).

## DIVERGENCE #22 — MEASURED + CONFIRMED (2026-09-02)

fe awards KD-asymmetric decided rounds to the KD SUFFERER 227/227
(100%); fi awards to the SCORER 245/245 (100%) — opposite sides,
instrument discriminates (control gate passed). Consumer grep:
round scores feed ONLY decision resolution in both engines → the
P0 comparison_master DEC/finish RATES are CLEAN; #22 corrupts
decision WINNERS only. Blast radius: ≤1.8% of fe decisions
(54/2935 contained ≥1 KD-asymmetric round; upper bound). Fix is
Fight Model arc work (fe retires at consolidation); forward-only,
no backfilled saves. The earlier "fe DEC rates contaminated"
claim (P1 handoff + retiring-thread recap) is documented FALSE.
Artifacts: outputs/sm1/fight_model/div22/.

NEW FINDING (filed open): fi:1240 double-writes
knockdowns_this_round (apply_damage already increments at fe:616)
→ fi per-round KD counts are 2× actual; inflates 10-8 margins,
does not flip winners on observed rows. Re-opens at consolidation.
