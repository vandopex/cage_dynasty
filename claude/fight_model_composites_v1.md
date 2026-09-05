# FIGHT MODEL COMPOSITES v1 — D13 RATIFIED (2026-09-04)

Disk copy canonical; project copy is backup. Composites for the P_c
contest form declared in fight_model_v1_0.md §4. Ratified by Van
as D13 on 2026-09-04. Contract: `A_eff = A_base(2-3 scoped
attributes, declared weights) × situational factors`;
`P_c = clamp(P_MIN, P_MAX, P_EVEN + S × (A_eff/(A_eff+D_eff) − ½))`.

## STRIKING

| Event | Attack recipe | Defense recipe |
|---|---|---|
| Punches | boxing 70 / speed 30 | striking_defense 65 / speed 35 |
| Kicks | kicks 70 / speed 30 | striking_defense 65 / speed 35 |
| Clinch strikes | clinch_striking 75 / speed 25 | striking_defense 60 / clinch_control 40 |

## GRAPPLING

| Event | Attack recipe | Defense recipe |
|---|---|---|
| TD at distance | takedowns 100 | takedown_defense 70 / speed 30 |
| TD in clinch | takedowns 60 / clinch_control 40 | takedown_defense 60 / strength 40 |
| Throws | strength 50 / takedowns 50 | takedown_defense 60 / strength 40 |
| Guard passes | top_control 100 | guard 100 |
| Sweeps | guard 80 / strength 20 | top_control 100 |
| Standup from bottom | guard 70 / strength 30 | top_control 100 |
| Clinch entry | clinch_control 60 / takedowns 40 | clinch_control 60 / striking_defense 40 |
| Clinch break | strength 100 | clinch_control 70 / strength 30 |

## SUBMISSIONS (per §5a)

| Contest | Attacker | Defender |
|---|---|---|
| Lock-in | submissions 100 | guard 50 / submissions 50 |
| Escape (technical) | submissions 100 | guard 50 / submissions 50 |
| Tap (will) | — | heart threshold × damage/stamina state (§5a dials, not a composite) |

## LANE GRANTS (D13, updating fight_model_v1_0.md §2 scopes)

1. **takedowns** — offense column adds "clinch-entry assist" (used in
   Clinch entry attack recipe). Total lanes: 3 offense (TD attack;
   TD-threat pressure; clinch-entry assist). Under 4-lane cap.

2. **clinch_control** — defense column adds "clinch strike defense"
   (the "maintenance" umbrella; used in Clinch strikes defense recipe).
   Total lanes: 2 offense (clinch entry; clinch maintenance) + 2
   defense (clinch-entry defense; clinch strike defense) = 4. At cap.

## INITIATIVE — SENSITIVITY TARGET (D13, not a formula)

Not a recipe. Declared as a gate target:

    +1 SD of speed → +8pp ±3 twin decided-share on the P2c
    counterbalanced instrument (pooled ≥2 seed blocks per GE-6).

Speed enters initiative dampened via `K_SPEED_INIT` dial; the
constant is set at the P3-3 gate by iterating against the target.
Momentum (+5), position (+10), and aggression (±2×dial) keep their
existing situational seats. Coin-flip tie-break (F1 fix, C16) unchanged.

## POWER — DEFERRED TO P3-4

Power isn't in these recipes yet — it arrives at P3-4 with world-gen.
Damage recipes (a separate table) will read power at that ship. Until
then, damage keeps reading strength as today; the swap-in is a P3-4
line item.

## RIDERS (P3-3 execution)

- **S_c derivation:** from `(P_even, 20pt-edge target)` pairs
  analytically, then gate-verified. Given P_c formula and A_eff / D_eff
  at a 20-point recipe-weighted edge, solve for S that hits the
  declared edge target.
- **Bounds:** `P_MIN = 0.4 × P_EVEN`; `P_MAX = P_EVEN + 1.5 × edge-gain`
  capped at 0.90.
- **Variance:** symmetric two-sided uniform `1 ± 0.15` on both A_eff
  and D_eff (independent). Initial. Adjustable at calibration.

## DERIVATION SCAFFOLD (worked at implementation)

For each event class with `P_EVEN` and `EDGE20_TARGET`:

    at equal skill: A_eff = D_eff, so A/(A+D)-½ = 0, P_c = P_EVEN
    at 20-pt attacker edge on primary stat:
      A_eff = base_stat_A × primary_weight (+ assist terms)
      D_eff = base_stat_D × primary_weight (+ assist terms)
      solve: EDGE20_TARGET = P_EVEN + S × (A_eff/(A_eff+D_eff) − ½)
      → S = (EDGE20_TARGET − P_EVEN) / (A_eff/(A_eff+D_eff) − ½)

S is derived once per class from D10 targets, printed in the
CONTEST_CONSTANTS table, then gate-verified at §5b (±3pp of
EDGE20_TARGET per non-thin class).
