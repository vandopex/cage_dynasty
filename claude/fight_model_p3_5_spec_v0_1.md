# FIGHT MODEL P3-5 — EXECUTION SPEC v0.1 (2026-09-05)
# STATUS: RATIFIED (Van, 2026-09-05, via P5-A kickoff paste).
# The arc's final docket before P3-6 acceptance; FREEZE LIFTS on
# P5-C green.

Inputs: contract §6 (D9 five-part finish model), §9 target tables
(D11/D12), rulings D17/D18/D19 (2026-09-05), validated baseline
(outputs/sm1/fight_model/p3_5/phase0_bis/report.md), calibration
list items 1-11 (scope doc). Chassis: fi, HEAD C28 cf85a21.

## THE SHAPE

Three phases, strictly ordered. Build the finish model FIRST (it
defines the labels and the ~8 knobs everything tunes through),
then complete the physics (flips + structural rulings), then ONE
calibration pass over final physics (S5 — no dial is tuned twice).

## P5-A — FINISH MODEL BUILD (D9, structural)

REPLACEMENT, measured not equivalence-gated (the §5a precedent).
1. THE METER: health = stoppage pressure (D1 promoted). The
   twelve scattered finish machines' private accumulators and
   thresholds become damage INPUTS, not deciders. Census first
   (read-only): enumerate every current finish decision site in
   fi with path:line before touching any.
2. THE ONE CHECK: once per exchange + once between rounds — one
   smooth curve on health below the critical line; no cliffs.
   Modulators: HEART lowers the line (stoppage-resistance lane
   made real); CONTEXT nudges (rocked-unanswered → twitchier ref;
   safe in guard → less).
3. THE NAMING TABLE: label from circumstances at fire time — KO /
   TKO (GnP) / TKO (Referee Stoppage) / Doctor / Corner — each
   row carries a commentary hook. Flash KO becomes a label, not a
   lottery. EVERY method string the old machines could emit must
   be reachable from the table (gate: label-reachability census,
   old-set vs new-set diff = explicit, none silently lost).
4. CARVE-OUTS: submissions keep §5a's contest; structural cuts +
   leg-kick TKO read their accumulators with one plain threshold
   each (D12: leg-kick keeps its private dial, ~1% target,
   first-class commentary).
5. THE KNOBS: ~8 named constants replace ~40 (critical line,
   curve steepness, heart modulation, between-round mult, two
   accumulator thresholds, + §5a dials). Old constants retire
   into CLAUDE.md as documented-false-or-superseded, per rule.
GATES: naming-table reachability; before/after method mix banked
on fixed-card EP1/POP (drift expected, judged at P5-C not here);
finish-story samples (a KO, a corner stoppage, a doctor stoppage
each narrated legibly); downstream method-string pattern check
(the P3-6 sweep pulled forward for any NEW strings minted here).

## P5-B — PHYSICS COMPLETION (rulings + flips)

Each lands with its own defining-instrument reading; rule (a)
governs every flip; production-population gates throughout.
1. D17 STAMINA FLOOR: composite scalar floors at 0.5. Reading:
   cardio channel before/after (expect the +25pp god-channel to
   compress); gassed-fighter KO capability sample ("exhausted but
   dangerous" story check).
2. D18 POWER MODEL: world-gen power = strength + offset + ±8
   noise (replaces tier roll). Reading: per-style power means now
   order by offset (the tier confound dies); separability G2
   re-check; forward-only.
3. CUTS FLIP: FI_CUT_WRITER_ENABLED + doctor-stop path ON with
   fresh occurrence/stoppage readings; calibrate to anchors
   (occurrence common, stoppage ~1-3% of fights); sprawl-punish
   magnitude reading + dial.
4. AGGRESSION PACK: fix R3 trigger (require hurt-signal alongside
   stamina; target fire rate ~10-20%), rename collision-prone
   hook lines, diagnose sub-att compression; THEN flip
   FI_AGGRESSION_RULES_ENABLED + FI_IQ_EXECUTION_ENABLED on
   fixed-card readings (tendency plan spread replaces the
   lopsided 42%-AGGRESSIVE style map).
5. ITEM 4 JUDGE RE-WEIGHT: TD 8.0 near-absolute (99-100% of
   split rounds) → re-weight so a takedown is strong but not
   automatic; reading: split-round win share by path, target
   wrestler ~65-80% (real MMA judges favor control, not 100%).
   #22-style affirmative proof on re-scored round sample.
6. D19 plumbing (activity cost → aggression, not speed) lands
   here; speed's VALUE is tuned in P5-C.

## P5-C — THE SINGLE CALIBRATION PASS (S5)

All dials, one pass, final physics, fixed-card CRN instrument
suite (EP1 / POP / MISMATCH built to actually mismatch / per-class
pools). ACCEPTANCE (freeze-lift gates):
- §9: EP1 3R method mix 22/20/16/40/~2 within ±5pp per bucket;
  DEC inside the ruled 25-45 band. (Baseline: 47/18/30/4.8 —
  the finish-fest dies here.)
- P2c full sweep: all 19 attributes ALIVE in declared lanes, no
  god (nothing > ~2× the family norm), no dead (≥ detection
  floor), boxing positive, speed +6pp/20 ± 3 (D19), cardio off
  the +25pp channel (D17 assist).
- Touched-zero: POP R1 <25 / R2 <40 (T2 remainder).
- Cuts: stoppage 1-3% of fights; leg-kick TKO ≈1% (D12).
- Sub mix: severity spread reaches SEVERE/CAREER in production at
  plausible rates (runway dial); tap/sleep/injury proportions
  sane per class.
- Per-class mixes declared + measured (item 8) by draft-and-
  adjust against the EP1 reference row.
Wrong numbers from old constants documented as false in CLAUDE.md.
Every dial's before/after banked. FREEZE LIFTS on all-green →
P3-6 acceptance + ship (P2c sweep re-run, live playtest fresh
save, deploy on proof, D14/D16 batch, post-deploy owed items).

## RULES OF THE DOCKET

Everything inherited: fresh date + HEAD gate; read-only census
before touch; single-purpose commits on Van's word; stop before
commit; rule (a) flips; production-population gates; fixed-card
CRN comparisons; instruments match the DEFINING instrument; no-op
controls cannot prove life; verbatim over recall; docs same turn;
never hardcode saves/fighters; forward-only. Seed ledger continues
from 992000+. Van rules any target-band change; architect drafts,
cc executes, nothing self-ratifies.
