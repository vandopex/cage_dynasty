# FINISH-DIST-DATA1 — baseline finish-method distribution

**Read-only measurement.** No code changes, no tuning.
Engine: `fight_integration.quick_narrated_fight` (real engine, not mock).

- Fighter pairings: 11 × 11 = 121
- Fights per pairing: 8
- Total fights: 968
- Rounds: 3
- OVR (both fighters, all attrs): 70

## Aggregate KO / TKO / SUB / DEC / DRAW split

| Bucket | Count | Share |
|---|---:|---:|
| KO | 94 | 9.7% |
| TKO | 229 | 23.7% |
| SUB | 21 | 2.2% |
| DEC | 585 | 60.4% |
| DRAW | 39 | 4.0% |

**KO+TKO combined:** 33.4%   **SUB:** 2.2%   **DEC:** 60.4%   **DRAW:** 4.0%

## Per winning-style: designed vs realized

Designed rates from `styles.py` `StyleDefinition.ko_rate/sub_rate/dec_rate`. Realized shares are of that style's WINS (draws excluded). KO+TKO combined for comparison to designed `ko_rate` (styles.py labels it as 'KO/TKO rate').

| Style | Wins | KO+TKO realized | designed | Δ | SUB realized | designed | Δ | DEC realized | designed | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Striker | 80 | 48% | 45% | +2% | 0% | 5% | -5% | 52% | 50% | +3% |
| Counter Striker | 89 | 52% | 35% | +17% | 2% | 5% | -3% | 46% | 60% | -14% |
| Pressure Fighter | 79 | 39% | 40% | -1% | 4% | 10% | -6% | 57% | 50% | +7% |
| Point Fighter | 106 | 39% | 20% | +19% | 0% | 5% | -5% | 61% | 75% | -14% |
| Muay Thai | 82 | 38% | 40% | -2% | 1% | 5% | -4% | 61% | 55% | +6% |
| Wrestler | 82 | 26% | 15% | +11% | 2% | 20% | -18% | 72% | 65% | +7% |
| Ground & Pound | 85 | 21% | 45% | -24% | 4% | 20% | -16% | 75% | 35% | +40% |
| BJJ Specialist | 88 | 22% | 10% | +12% | 2% | 55% | -53% | 76% | 35% | +41% |
| Clinch Fighter | 87 | 26% | 25% | +1% | 5% | 15% | -10% | 69% | 60% | +9% |
| Sprawl & Brawl | 71 | 45% | 50% | -5% | 1% | 5% | -4% | 54% | 45% | +9% |
| Balanced | 80 | 29% | 30% | -1% | 4% | 20% | -16% | 68% | 50% | +18% |

### Biggest drifts (|realized − designed|)

| Style | Method | Realized | Designed | Δ |
|---|---|---:|---:|---:|
| BJJ Specialist | SUB | 2% | 55% | -53% |
| BJJ Specialist | DEC | 76% | 35% | +41% |
| Ground & Pound | DEC | 75% | 35% | +40% |
| Ground & Pound | KO+TKO | 21% | 45% | -24% |
| Point Fighter | KO+TKO | 39% | 20% | +19% |
| Wrestler | SUB | 2% | 20% | -18% |
| Balanced | DEC | 68% | 50% | +18% |
| Counter Striker | KO+TKO | 52% | 35% | +17% |

## Submissions: attempt → conversion

- Engine `submission_progress_to_finish` threshold: **70.0** (FightConfig.standard_fight() default)
- Total submission ATTEMPTS logged across all fights, both fighters: **4405**
- Total submission FINISHES: **21**
- **Conversion rate (finishes / attempts): 0.5%**

Note: `sub_att` counts every submission attempt logged in RoundStats (entries into a submission position or lock-in attempts), not only 'DEEP' ones. The engine's `submission_progress` tightens over rounds; a finish requires progress ≥ threshold. Progress-reaching-threshold isn't exposed per-attempt on the result object, so this ratio is the closest proxy for 'attempts that convert to finish' the engine surfaces.

## TKO subtype breakdown

Of all 229 TKO finishes:

| Subtype | Count | Share of TKOs |
|---|---:|---:|
| TKO | 194 | 84.7% |
| TKO (Doctor Stoppage) | 19 | 8.3% |
| TKO (Body Shot) | 11 | 4.8% |
| TKO (Leg Kicks) | 5 | 2.2% |

## PA drift caveat

This measures the local repo engine at `cage_dynasty_web/fight_engine.py`. Per the known PA hazard (CLAUDE.md), fight_engine.py on the PA deploy may carry hand-appended constants not in the repo (last audit 2026-07-01). If live in-game finish rates differ noticeably from these numbers, hand-diff PA's copy of fight_engine.py against the repo before trusting this baseline for tuning targets.
