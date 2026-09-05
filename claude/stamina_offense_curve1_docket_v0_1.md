# STAMINA-OFFENSE-CURVE1 — diagnostic docket v0.1 (2026-09-01)

Status: ACTIVE 2026-09-01. C12 (engine, a6b2c05) + C13 (docs,
727dee8) landed; tracked tree clean; PA DEPLOY HELD pending this
docket's verdict (Van ruling — the unpushed chain ends in a build
where elite fights never go the distance; the docket decides
whether a curve fix ships before the deploy or the deploy goes
as-is). Read-only docket — three measurements, ZERO edits.
Successor question to B9's accepted-open DEC shift. Sequencing
ruling: this docket runs BEFORE lever two (regen scaling) — if
freshness→finishes is the mechanism, regen increases freshness and
pushes DEC lower, so lever two must not ship blind into this
coupling.

## The question

B9 (K=0.6, S=0.5) collapsed decision rates: POP-POOL1 52%→29%;
tierA_c11 elite-cardio pairings −37 to −54pp, with HHxHH and HHxLH
at 0% DEC — peer high-cardio matchups now finish 100%. Van's design
taste: more KOs up the ladder is GOOD flavor; always-KO is not.
Van's hoped-for shape if a fix is warranted: finishes split by
CAUSE — peer elites both managing the tank go to decisions; a
cardio mismatch opens an effectiveness gap and produces the finish.
Hypothesis to test, not assume: in the pre-B9 world both fighters
spent fights at 10-20 stamina, and stamina feeds strike
success/damage somewhere — mutual exhaustion was a hidden damage
governor. B9 removed the governor; fresh fighters hit near full
effectiveness and someone's chin gives out. If true, the lost
decisions were never real decisions (two dead fighters leaning on
each other), and the design lever is the stamina→effectiveness
curve shape, NOT K/S (retuning drain to restore DEC = tuning output
to hide the engine — forbidden).

## Measurements (all read-only, all grep-anchored, all tables name
source files)

M1 CONSUMER CENSUS: every code site where fight-time stamina (the
   FighterState.stamina value, not the cardio attribute) feeds
   strike success, damage, defense, or action selection. Grep both
   engines (fe AND fi — two exchange loops; the closeout Item 1b
   rider proved their loops diverge, so a consumer present in one
   and absent in the other is itself a finding). For each site:
   file:line at current HEAD (a6b2c05+), the formula verbatim,
   which channel (success / damage / defense / selection), and
   whose stamina (self / opponent). The B3 pattern: classify, list
   ambiguous, never guess.

M2 EFFECTIVENESS-VS-STAMINA CURVE: measured, not read. Clone pair
   (B7 recipe donors), pin one fighter's stamina at fixed levels
   (10/25/40/55/70/85/100) via instrument wrapper — RNG-neutral,
   wrapper proven non-perturbing at the no-op level before use
   (A5 discipline: adjusted instrument must discriminate). Per
   level: strike success rate, mean damage per landed strike,
   damage throughput per exchange. Output: one table = the curve,
   per engine path. The curve's shape (linear vs saturating vs
   threshold) is the finding.

M3 FINISH RATE VS SKILL GAP: Van's ladder question. POP-POOL1
   manifest carries records/tiers. Bucket the 1225 B9-cell fights
   by skill gap (tier delta or a declared composite — declare it
   before computing) and report finish rate + method mix per bucket,
   B9 vs identity BEFORE (both on disk — no new fights needed
   unless bucketing needs more N; say so if it does). Answers:
   does finishing scale with the gap (ladder flavor, keep) or is it
   uniform freshness (governor removal, tune)?

## Explicitly out of scope

Any engine edit. Any K/S change. Lever two design. Choosing the
curve fix — that is a Van design call AFTER the curve is on the
table. If M2 shows saturation already exists, the DEC collapse
needs a different explanation and this docket's hypothesis is
retired-not-deleted.

## Deliverable

One report: M1 census table, M2 curve table + shape call, M3 gap
table, and a mechanism verdict (hypothesis confirmed / refuted /
mixed) with the evidence line for each. Then Van decides: brand
(keep it violent), tune (curve bend, own scoped arc with its own
gates), or defer — and the deploy hold lifts with that decision.

## Standing rules apply in full

Measure first; instrument before engine when a measurement looks
absurd; verbatim over recall; tables name source files; STOP at
the report.
