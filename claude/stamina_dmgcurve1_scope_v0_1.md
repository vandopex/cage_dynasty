# STAMINA-DMGCURVE1 — design scope v0.1 (2026-09-01)

Status: **RATIFIED by Van 2026-09-01 (signal 1)**. Constants
ratified separately after Gate 1b (signal 2). Commit approval
separate after Gate 1c. Baseline HEAD 727dee8 (C13). Gate 0 +
Gate 1a executing at this baseline; STOP before Gate 1b.
Successor to OFFENSE-CURVE1 docket (verdict: confirmed-with-nuance).
Van rulings already in hand: TUNE ruled; DEC target band for
cardio-elite peer 3R fights = 25-45% (literal, 2026-09-01); blowouts
finishing heavily is expected and preserved; structural 0% or 100%
cells forbidden anywhere (determinism kills emergent story).

## The question and the mechanism

B9 lifted fighters onto the effectiveness plateau; the DEC collapse
concentrates in cardio-elite peer fights (HHxHH 0% DEC) because at
stamina parity the success and defense channels roughly cancel
(both scale stamina/100 on opposite sides of the same check) while
the DAMAGE channel does not — fe:2492 scales only the attacker:
damage *= (stamina/100)*0.5 + 0.5. Fresh-vs-fresh means every
landed shot is near max power for 15 minutes, both ways. M2
measured damage/landed 5.6→11.5 across the stamina range (curve +
strike-mix selection). The lever is the TOP of the damage factor;
the steep zone below ~55 is untouched — gassing stays fatal, cuts
and cardio keep their story. NOT touched: K/S (ratified at B9),
success/defense linears (they cancel at parity and carry the
asymmetric-gassing story), regen (lever two, post-consolidation),
action selection (fe:2134), sub channels (fe:3023/3024/3103/3122 —
reported, not bent, this pass).

## Spec

CHANGE (single site): fe:2492's inline factor becomes a named
module function beside two constants (DRAIN1 pattern):

  def damage_stamina_factor(stamina):
      f = (stamina / 100) * 0.5 + 0.5          # current curve
      p = (DMG_PIVOT / 100) * 0.5 + 0.5        # factor at the pivot
      if stamina <= DMG_PIVOT: return f
      return p + DMG_COMPRESS * (f - p)

  DMG_PIVOT    = 0.0   # identity: no stamina is above a 0 pivot's
                       # special zone in a way that changes f —
                       # verified by Gate 1a, not asserted
  DMG_COMPRESS = 1.0   # identity: full slope above pivot

Identity check by construction: at DMG_COMPRESS=1.0 the function
returns f for every stamina regardless of pivot. Continuous at the
pivot by construction. Below the pivot the curve is byte-identical
to today's. Two named constants, one function, one call site
(fe:2492). Both engines get it for free — fe:2492 is a shared
primitive (M1: 11 of 12 consumers in fe, called by both loops).

## Instrument: ELITE-PEER1 cell (new, Gate 0)

The 25-45% target is gated on the population that is actually
broken and that the post-B9 ladder will breed at the top: pairs of
world-gen fighters with cardio ≥ 85 AND |ΔOVR| ≤ 2 (ovr_at_signing),
production new_game path, no lab donors (chin-50 clones inflate
finishes; the target is a game-feel number, it gets measured on
game fighters). Pool size and pairing count declared at build; N ≥
400 fights per measurement, 3R non-title, fixed seeds, schedule
declared once. DISCRIMINATION PROOF: at current constants
(identity curve) the cell must reproduce the broken regime —
finish-heavy, DEC well below 25% (HHxHH analog showed 0%). If it
comes back at 40% DEC at identity, the cell doesn't capture the
problem; STOP, rebuild, don't tune.

## Targets

T1 (the point, Van's band): ELITE-PEER1 3R DEC in [25%, 45%].
T2 (ladder guardrail): M3-style finish% by OVR-gap bucket stays
   monotone increasing; blowout bucket (11+) finish% ≥ 60%
   (B9 measured 70.7%; report the number, gate at 60).
T3 (steep zone untouched): M2 pinned-curve at stamina 10/25/40
   within ±5% of the B9 baseline curve values, both engines.
T4 (no determinism): no measured cell — ELITE-PEER1, any POP-POOL1
   OVR bucket, any tierA pairing reported — at exactly 0% or 100%
   finish. Gated on ELITE-PEER1; reported elsewhere.
T5 (DRAIN1 not regressed): POP-POOL1 stamina metrics (median R1
   close, zero census) within noise of B9 values — the damage curve
   must not touch stamina physics; drift here means the wire leaked.

## Gates (DRAIN1 pattern, two signals + commit approval)

GATE 0 — build ELITE-PEER1, discrimination proof (above). Also
  carries two owed docket riders: (a) M2's curve is behavioral —
  attempt counts vary with pin level, selection effects included;
  named in filings. (b) cc states the reason fi's between-round
  fatigue site was excluded from the M1 census.

GATE 1a — MECHANICAL EQUIVALENCE at identity constants: same-HEAD
  A/B (stash vs working tree) row-by-row on POP-POOL1 1225 +
  ELITE-PEER1, expect 100% identical; 7 fixture hashes unchanged
  vs B9 baseline; consumption proof that the function is actually
  called (one traced fight shows damage_stamina_factor invoked at
  fe:2492's path, per engine). Any drift = wiring wrong; STOP.

GATE 1b — BOUNDED SEARCH, report only: grid DMG_PIVOT ∈
  {50, 55, 60, 65} × DMG_COMPRESS ∈ {0.0, 0.25, 0.5} (12 cells,
  in-process setattr, override proven live first). Per cell:
  ELITE-PEER1 DEC + method mix (T1), OVR-gap ladder (T2), pinned
  steep-zone spot check (T3), POP-POOL1 stamina metrics (T5),
  0%/100% census (T4). One 12-row master table, T-marks, no
  recommendation column. Expect DMG_COMPRESS=0.0 cells to bracket
  (fully flat plateau — probably overshoots T1's ceiling; said
  before the numbers arrive, A2 pattern). STOP. Van + architect
  choose (PIVOT, COMPRESS) → signal 2.

GATE 1c — CERTIFY at file-constants: file-vs-setattr parity on the
  chosen cell (exact reproduction); full T1-T5 at file constants;
  fixtures EXPECTED to break → re-baseline (new table + new probe
  sha256, old retired-not-deleted); both-engine verification (one
  matched pair per loop shows the bent factor in effect); DEC
  per-pairing tables vs B9 baseline for the record; cut-direction
  spot check (expect direction preserved). Consequences filed. STOP
  before commit → verbatim docs read → Van approves the commit.

## Not decided here

Success/defense curve shapes; sub-channel bends; regen (lever two,
post-consolidation); consolidation itself (next major arc per
claude/post_c13_sequencing.md); deploy (lifts after this ships).

## Ratification signals

Signal 1 (scope): Van's literal "ratified" on this document.
Signal 2 (constants): Van's literal (PIVOT, COMPRESS) after Gate 1b.
Commit approval: separate, after Gate 1c report + docs read verbatim.
