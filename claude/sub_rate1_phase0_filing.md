# SUB-RATE1 Phase 0 — filing (2026-11-12)

Phase 0 of SUB-RATE1 was read-only measurement and read of the engine. Sub-phases ran against HEAD `ccfc553`; no tracked-file edits, no PA mutation. Per-step reports under `outputs/`:

* `outputs/sub_rate1_phase0_A.txt` (transport + grep)
* `outputs/sub_rate1_phase0_B.txt` (field census, 5 real fights)
* `outputs/sub_rate1_phase0_CD.txt` (`records.json` build, 1080 pairs; `outputs/sub_rate1_phase0_records.json`)
* `outputs/sub_rate1_phase0b.txt` (tables from records: method mix, round split, TD-to-sub)
* `outputs/sub_rate1_phase0c.txt` (live-path via `card_builder`+`matchmaking`; `outputs/sub_rate1_phase0c_live_records.json`)
* `outputs/sub_rate1_phase0d.txt` (live dedupe, live injury share, dose-response first pass)
* `outputs/sub_rate1_phase0e.txt` (defender redo with validity gate, engine threshold READ)
* `outputs/sub_rate1_injury_info.txt` (injury path probe: MECHANIC READ, SHAPE on 1080 records, LIVE PATH + CONSEQUENCE on 44-week MC-filtered run)
* `outputs/sub_rate1_injury_validate.txt` (per-event capture/stored/MC equivalence for the flag-based MC guard; 44 weeks, 342/342 match)
* `outputs/sub_rate1_specialty_harvest.txt` (specialty_method harvest; 932 unique stored fights, 215 SUB, 14 distinct specialty_method values)

Tags used below: **MEASURED** (from one of the above persisted record files or a direct run), **READ** (from the source tree), **INFERRED** (not measured but derived from a MEASURED + READ combination; stated explicitly).

## §1 Headline numbers

**Live card_builder path at HEAD `ccfc553`** — `MEASURED` on the 591 unique live fights from 76 weeks (`outputs/sub_rate1_phase0c_live_records.json`, deduped in 0d):

| method | share | SE | n |
|---|---|---|---|
| SUB  | 26.06% | 1.81pp | 154 |
| TKO  | 36.21% | 1.98pp | 214 |
| KO   | 1.18%  | 0.45pp |   7 |
| DEC  | 35.20% | 1.96pp | 208 |
| DRAW | 1.35%  | 0.48pp |   8 |
| OTHER | 0%    | 0.00pp |   0 |

**Direct engine path, cross-matched pairs from a wk-0 roster (seed 20261113)** — `MEASURED` on `outputs/sub_rate1_phase0_records.json` (n=1080):

| method | share | SE |
|---|---|---|
| SUB  | 27.96% | 1.37pp |
| TKO  | 33.98% | 1.44pp |
| KO   |  0.37% | 0.18pp |
| DEC  | 36.94% | 1.47pp |
| DRAW |  0.74% | 0.26pp |
| OTHER | 0%    | 0.00pp |

Finish rate and composition reconcile within overlapping CIs between the two paths; the main difference is the live path's KO share (1.18%) vs direct (0.37%), small absolute.

**Engine wiring (READ):**

* Attempt filter — `fight_engine.py:2024-2060`: standard subs gated by `_sub_skill >= 60`; intermediate by `>= 55`; exotic by `(grappler-family and >= 75) or >= 85`.
* Position-secure threshold — `fight_engine.py:1990-2010`: dominant cluster `position_duration >= 3`; `subs >= 85` in guard/inferior: 2; `subs >= 75`: 4; else 5.
* Sub finish roll — `fight_engine.py:3716-3812` (`process_submission_progress`). Defender stats read: `submissions` (sub_escape "d" 1.0), `guard` (sub_escape "a" 0.5 via escaper composite), `heart` (TAP_HEART_SPREAD mod on tap_base), `chin` (via `_def_max_hp = 100 + chin*0.3` into state_mult); also `defender_state.stamina`/`.health`.
* Composite stats — `fight_engine.py:2762,2766` (SKILL_COMPOSITES) and `:2783,2787` (CONTEST_P_EVEN/EDGE20_TARGET).

## Live baseline (three separately generated worlds)

Three live-path samples at HEAD `ccfc553`, each a separately generated world (new_game with a different random seed and therefore a different roster, matchmaking order, and card_builder output); numbers sed'd from each sample's report file; SE values derived as √(p(1−p)/n):

| source | n (unique fights) | SUB count | share | SE |
|---|---:|---:|---:|---:|
| 0c/0d (`outputs/sub_rate1_phase0c_live_records.json`, deduped in 0d) | 591 | 154 | 26.058% | 1.806pp |
| Harvest (`outputs/sub_rate1_specialty_harvest.txt`) — stopped at 120-week cap, under the ≥1000 gate | 932 | 215 | 23.069% | 1.380pp |
| Injury probe (`outputs/sub_rate1_injury_info.txt`, flag-based MC guard, 44 weeks) | 342 | 101 | 29.532% | 2.467pp |
| **POOLED** (sum of n and k across the three; assumes exchangeable — see note) | **1865** | **470** | **25.201%** | **1.005pp** |

Note on the pool: the three samples are three separately generated worlds (different roster, different matchmaking seed), not three replicates of one world. Treating the row as a simple pool assumes between-world variance is negligible relative to within-world — that assumption is not independently verified here. The per-sample 95% intervals overlap pair-wise (0c/0d vs harvest; harvest vs injury probe; 0c/0d vs injury probe), consistent with a single underlying live-path SUB rate in the 23–30% band, but a world-level variance component is not pulled out.

## §2 Defender-wiring confirmation (Phase 0e)

`MEASURED` — attacker = Wanderlei Magalhaes (submissions=95, fresh new_game); defender submissions fixed at 40, guard swept; 600 fights per cell:

| D guard | A att | A att/f | A subs | A sub% | A conv | D att | D subs |
|---|---|---|---|---|---|---|---|
| 30 | 1045 | 1.742 | 500 | 83.3% | 47.8% | 0 | 0 |
| 50 | 1410 | 2.350 | 469 | 78.2% | 33.3% | 0 | 0 |
| 70 | 2032 | 3.387 | 393 | 65.5% | 19.3% | 0 | 0 |
| 90 | 2469 | 4.115 | 351 | 58.5% | 14.2% | 0 | 0 |

**Direction:** higher defender guard → lower sub finish rate and lower conversion per attempt. Attempts/fight rise with defender guard (`INFERRED`: likely more time on the ground once defender survives initial attempts). Defender attempts = 0 across 2400 fights (`MEASURED`), consistent with the attempt-threshold `READ` (`submissions >= 55/60/85` all above D.submissions=40).

## §3 Finds that are not FAILs but worth recording

* **Live method strings lack sub_type / Injury suffix** — 0d read only `method_raw` on the 591 live records and reported all 154 SUB as (unknown) sub_type; superseded — see §4 and LIVE-METHOD-FORMAT1.
* **26 fights have no round-1 fighter-rounds** — `MEASURED` on the 1080-record file. Pattern: 17 `TKO (Doctor Stoppage - Cuts)` + 2 `TKO (Doctor Stoppage)` + 7 `Draw`, all landing without populating `fighter{1,2}_stats[0]`. Filed as STATS-EMPTY-DOCSTOP1.
* **Position-secure counter is skill-tiered** — `READ` only; not measured as a variable. A fighter at `submissions >= 85` reaches position-secure in 2 ticks from guard/inferior; a mid-tier fighter at 60 needs 5. Documents the mechanism; not a defect.

## §4 Known-false (document, do not quietly correct)

* **0c filing's live "22215 fights"** was a dedup bug (`logged_ids` stored event_idx ints but was compared against tuple fid keys). The raw 22215 is a 37.59× inflation of the true 591 unique fights (`MEASURED` in Phase 0d §1). Every downstream "n=22215" cited from 0c is false; use 0d's unique-591 values.
* **0c filing's "SE ±0.29pp" on live method mix** derives from the bogus 22215. True SE on n=591 is roughly 1.8–2.0pp (Phase 0d §1). Marked `false-as-reported`.
* **0d §3b finding "sub rate increases with defender stat"** was CONFOUNDED — 0d varied D.submissions AND D.guard together at low attacker baselines (template submissions 49, overridden to 85), producing very small attempt counts per cell (2–26 subs). Phase 0e §1 holds D.submissions fixed at 40 and sweeps D.guard with an elite attacker (subs=95), restoring 350–500 SUB per cell, and the direction reverses to the expected monotone (sub rate falls as D.guard rises). Marked `false-as-reported; superseded by Phase 0e §1`.
* **0d §2's "all 154 live SUB methods parse as (unknown) sub_type"** is `false-as-reported` — the probe read only `method_raw` from the 591 live records; the stored record carries `specialty_method='SUB (<sub_type>)'` (215 of 215 non-empty in the 2026-11-12 harvest). See LIVE-METHOD-FORMAT1 for the corrected statement.

## §5 New backlog rows preview

Additions filed under 2026-11-12:

```
- **LIVE-METHOD-FORMAT1** [filed 2026-11-12, MEASURED] — on the live card_builder path the raw engine result carries one of three method forms — "Submission (<sub_type>)", "Submission (Injury - <sub_type>)", "Technical Submission" — and the "Injury -" marker is dropped at the gb-store boundary. At store, method='SUB' for all three raw forms; specialty_method='SUB (<sub_type>)' keeps the hold identity. Measured: 215 SUB fights out of 932 unique stored (2026-11-12 harvest), 215/215 non-empty specialty_method, 14 distinct values (armbar 58, twister 32, calf_slicer 29, rear_naked_choke 29, neck_crank 16, arm_triangle 15, americana 12, kimura 11, triangle_choke 4, wrist_lock 3, guillotine 2, von_flue_choke 2, darce_choke 1, kneebar 1), 0 of 215 containing "Injury" in either method or specialty_method; 0 of 101 stored SUB methods containing "Injury" in INJURY-INFO §3 (30 of 101 raw results did carry "Injury -" before the collapse). News feed does carry the injury text (observed: "🤕 <name> injured — <body_part> via <sub_type>. Out ~Nw.").
- **STATS-EMPTY-DOCSTOP1** [filed 2026-11-12, MEASURED, 26/1080 fights] — fights ending by TKO (Doctor Stoppage[-Cuts]) at R1 5:00 and 7 of 8 draws persist with empty `fighter{1,2}_stats[0]`. 2108 R1 fighter-rounds observed (ideal 2160); gap 52 = 26 fights × 2 sides. [INFERRED] Readers computing per-round stats from `stats_per_round[fr-1]` get an IndexError or "no stats" bucket for these fights.
```

Existing row update:

```
- **METHOD-MIX1** ... (unchanged tail) ... Phase 0 filing pointer appended.
```

## §6 Not known

* Whether the live-path `card_builder` method string is normalized at write time or at read time. Not traced.
* Whether the 26-doctor-stoppage/draw `stats_per_round=[]` pattern is deliberate (fight aborted before R1 stats write) or an incomplete-write bug. Not traced.
* The relationship between the `position_secured` threshold ladder (`READ`) and empirical attempts-per-fight at different submissions tiers. 0d §3c did run an attacker-stat sweep on a D(G=50, S=50) template, A subs ∈ {40,45,50,55,65,80,90}, n=300 per cell; A=40–55 produced sub_rate=0.000% (0 of 300), A=65 sub_rate=0.667% (2 of 300, att/fight=0.010), A=80 sub_rate=2.333% (7 of 300, att/fight=0.033), A=90 sub_rate=1.333% (4 of 300, att/fight=0.027). The 0d §3b cell with "0.010 attempts per fight" belongs to A=85 vs D(G=30,S=30) and A=85 vs D(G=50,S=50), not §3c. An attacker-stat sweep on a grappler template was not run; 0e §1 ran the defender-guard sweep.
* Whether the live-path method-mix at `ccfc553` differs from pre-reload PA. The error-log in deploy #10 §3b showed EXPORT-500 as the newest line pre-reload; no AI-vs-AI pool measurement exists on PA at a19a921.

## §7 Rulings (Van, 2026-11-12)

* Target: 16–20% SUB on the live path, measured over ≥1000 unique fights.
* A specialist floor is a gate on the sandbox table; its definition is not yet ruled.

## §8 Injury path — MECHANIC + SHAPE + LIVE PATH + CONSEQUENCE

Source: `outputs/sub_rate1_injury_info.txt` (2026-11-12 run).

**MECHANIC** — `READ`, `fight_engine.py:3801-3807` (`process_submission_progress`). Tap vs. injury vs. sleep is decided by the refusal band: if `submission_progress ≥ effective_tap + refusal_width` the fighter refuses to tap, and the result splits on `kind` — `choke → "sleep"` (persisted as `"Technical Submission"`), `joint_lock → "injury"` (persisted as `"Submission (Injury - <sub>)"`); inside the band the defender taps. Stats read in the decision: defender `heart` (scales `tap_base` via `TAP_HEART_SPREAD` and widens the refusal band via `REFUSAL_HEART_SPREAD`); defender `chin` (feeds `_def_max_hp = 100 + chin*0.3` into the state-mult); defender stamina and health via `defender_state`. Sub_type → kind mapping is a static dict (`SUBMISSION_KIND`).

**SHAPE** — `MEASURED` on `outputs/sub_rate1_phase0_records.json` (direct-engine, n=1080; 302 SUB rows).

| sub_type | tap | injury | tech_sub |
|---|---|---|---|
| armbar | 58 | 20 | 0 |
| calf_slicer | 31 | 25 | 0 |
| rear_naked_choke | 38 | 0 | 10 |
| twister | 26 | 17 | 0 |
| arm_triangle | 19 | 0 | 5 |
| neck_crank | 8 | 9 | 0 |
| americana | 9 | 1 | 0 |
| kimura | 7 | 2 | 0 |
| von_flue_choke | 7 | 0 | 2 |
| wrist_lock | 4 | 0 | 0 |
| ankle_lock | 0 | 2 | 0 |
| darce_choke | 1 | 0 | 0 |
| north_south_choke | 1 | 0 | 0 |
| **TOTAL** | **209** | **76** | **17** |

Injury share by round: R1 32.0% (56/175), R2 11.9% (10/84), R3 23.3% (10/43). By winner grappling tier: elite 35.7% (50/140), high 20.6% (26/126), mid 0% (0/36). Chokes carry 0 injuries in the table — matches the `kind` mapping `READ`.

Loser heart (10-point bins): **NOT MEASURED**. The per-fight dict in `sub_rate1_phase0_records.json` does not carry a `loser_heart` field — only `loser_style` and `loser_sub_defense_tier`. Not rebuilt from seed in this filing.

**TREND** — calf_slicer (56) + twister (43) = 99 of 302 submissions (32.8%). The two exotic joint-lock types together carry the single largest slice of the sub table even though the attempt filter at `fight_engine.py:2024-2060` gates exotics on `_is_grappler and _sub_skill ≥ 75` OR `_sub_skill ≥ 85`. Hold mix (chokes vs. joint-locks, from the SHAPE table above): chokes 83 of 302 (rear_naked_choke 48 = 38 tap + 10 tech_sub; arm_triangle 24; von_flue_choke 9; darce_choke 1; north_south_choke 1); zero guillotine finishes and zero triangle_choke finishes (specific to the 302 direct-engine sample; the harvest of 215 live SUB finishes DID produce 2 guillotine and 4 triangle_choke — see below). Harvest hold counts (`outputs/sub_rate1_specialty_harvest.txt`, 215 SUB of 932 unique, all 14 distinct specialty_method values): armbar 58, twister 32, calf_slicer 29, rear_naked_choke 29, neck_crank 16, arm_triangle 15, americana 12, kimura 11, triangle_choke 4, wrist_lock 3, guillotine 2, von_flue_choke 2, darce_choke 1, kneebar 1. The population for the 302 was from a wk-0 fresh roster (seed 20261113); the 215 sample was from a different live-path world (see Live baseline above).

**LIVE PATH + CONSEQUENCE** — `MEASURED` on a flag-based MC-guarded 44-week probe (see Instrument notes). 342 captured real card fights, 101 SUB finishes. 30 of 101 (29.7%) carried `"Injury -"` in the raw `NarratedFightResult.method`. **0** of 101 (0%) retained `"Injury -"` in the stored `_completed_events[*].fights[*].method` field; stored `method='SUB'` for all three raw forms, stored `specialty_method='SUB (<sub_type>)'` drops the `"Injury -"` prefix. News feed carries the injury verbatim at the headline level (headline shape: `"🤕 <name> injured — <body_part> via <sub_type>. Out ~Nw."`); coverage across the 30 NOT MEASURED — the final MC-filtered report file does not enumerate the news-feed hits per injury finish.

Consequence (30/30 injury finishes):
* 30/30 → a stored injury record in `bridge._injury_system.get_injuries(loser_id)` with `source='submission:<sub_type>'`
* 30/30 → `bridge._fighter_cooldowns[loser_id] > 0` post-event
* Injury recovery_weeks distribution: 2w: 2; 3w: 1; 4w: 7; 5w: 3; 6w: 3; 7w: 3; 8w: 6; 10w: 6; 16w: 1; 20w: 1; 23w: 1. 34 records across 30 events; excess not reconciled. The file's `Per-event detail` block enumerates only the first 10 events (11 records): 9 events carry one post-event injury record each (source `submission:<sub_type>` matching the trigger); event [7] at wk 11 (armbar) carries two records (`submission:armbar` + a `fight`-source `Minor ankle injury`). The remaining 20 events (23 records) are not enumerated in the file; the 34↔30 excess beyond event [7] is not settled.
* Cooldown delta (post − pre) distribution: Δ=6w: 1; Δ=7w: 1; Δ=9w: 1; Δ=10w: 2; Δ=11w: 2; Δ=12w: 2; Δ=13w: 5; Δ=15w: 3; Δ=16w: 1; Δ=17w: 1; Δ=18w: 2; Δ=19w: 2; Δ=20w: 1; Δ=21w: 1; Δ=22w: 2; Δ=23w: 1; Δ=30w: 2.

**Van's decision on the injury path: pending.**

## Instrument notes

* **MC guard implementation.** The Phase 0 INJURY-INFO `inspect.stack` wrapper is replaced with a flag-based guard: wrap `GameBridge._compute_mc_odds_for_fight` and `._precompute_odds_for_fights` in a `_MC_FLAG` counter; the engine wrapper checks the counter instead of walking the stack. Validation 2026-11-12: 44 weeks, 342 captures, 342 stored fights, 33900 MC calls skipped — captures == stored, mc_skipped > 0, zero mismatched events (`outputs/sub_rate1_injury_validate.txt`).
* **MC_FRAMES cleanup.** `_compute_fight_odds_mc` was never a real symbol in the tree (`grep -rn 'def _compute_fight_odds_mc'` → 0 defs). The two real MC entry points are `_compute_mc_odds_for_fight` (game_bridge.py:17753) and `_precompute_odds_for_fights` (game_bridge.py:17880). The flag-based guard wraps exactly those two.
