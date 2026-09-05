# THE FIGHT MODEL v1 — DESIGN WORKING DRAFT (v0.9 archive, 2026-09-03)

Disk copy canonical; project copy is backup. The RATIFIED contract
is claude/fight_model_v1_0.md — THIS file is the working-draft
archive: full findings F1-F9, architect gate-error history GE-1..6,
and the decisions log with dates. Superseded for design content by
the contract; kept for findings/instrument lineage.

## FINDINGS

F1 — fi SLOT-1 BIAS — CONFIRMED (P2b step 2): tie rate 3.34%;
21,156/21,156 ties to slot1 (100.00%); slot1 first-actor 52.56%;
win bias replicated 51.10%. Mechanism = fi:683 `>=` tie-break.
F1-AUDIT: slot1 systematically the higher-ranked / champion /
higher-fitness fighter in live matchmaking (matchmaking.py:1266,
:1273-1306, :1377-1389) AND pre-gen (world_init.py:1425, :2001) —
favorites always held a hidden ~1-1.5pp edge. FIXED at C16.
F1a — twin-fight draw rates: stand-up styles 12-14%, grapplers 0%.
F2 — SPEED GOD STAT (P2c): ±1 SD = ±49.5pp decided-share; +15-speed
twin wins ~99.5%. Mechanism: initiative = speed + randint(-10,10);
1 SD outruns the jitter → ~90% of first actions, compounding.
F3 — FIVE DEAD STATS (P2c, ≤2pp floor): striking_defense,
takedown_defense, chin, heart, composure. Four of five are the
defensive/resilience layer; three are divisor-zoo stats.
F4 — BOXING INVERSION: +1SD → −5.74pp [−7.55,−3.92]; corroborates
ENGINE-STRIKE-SENS1 across two instruments. clinch_control weakly
negative (−1.91, CI edge).
F5 — low-confidence non-monotonic rows (multiple-comparisons
caveat, ~2 false positives expected over 36 cells): submissions
−1SD positive, top_control positive both directions, fight_iq
asymmetry. Logged, not load-bearing.
F6 — LANDING SKILL DIAL DISCONNECTED (D2 v3, signed, exact-anchored
2455/2455 both worlds): all strike classes, both configs, slope
+0.19..+1.72pp per 20-pt signed gap. Unifies F2/F3/F4.
F7 — FINISH-FEST ADDRESS: sub-tick finish 12.59%/tick at B9 vs
0.80% at identity (15.7×; escape 14.6% vs 8.5%); strike landing
barely moves between worlds. Submissions resolving through gassed
defenders.
F8 — SUBMISSIONS THE ONE LIVE WIRE: lock-in slope +13.34 (B9) /
+15.96 (identity); +38.16pp at identity extreme. Mechanism:
sub_diff bonus table (as-built §3.4), up to ±0.35 on lock-in.
F9 — UPSET BRANCH PAYS FIGHTERS TO BE WORSE: GRAP_other extreme
−9.27pp [−14.01,−4.53] at B9 (≥+16 attackers 46.05% vs ≤−16 at
55.31%); identity same direction weaker. Hypothesis: CGS upset
floors (0.65/0.75) exceed the clamped form's payout to the skilled
side. Vindicates D4. GRAP_clinch_entry: real slope under identity
(+6.93pp) washed out under B9.
D2-CONFIG: direct fi.simulate_narrated_fight without config falls
to FI_FALLBACK (standup=6), −5.66pp DEC vs LIVE_PLAY — bundle path
(_assemble_prefight → _run_path_a_ref) REQUIRED for reference
reproduction.
D2-CONFIG amended (P3-2b, 2026-09-03): bundle path is NOT
structurally required. fi.simulate_narrated_fight (fi:2039-2053)
and NarratedFightSimulator.__init__ (fi:343-359) both accept an
explicit `config: FightConfig = None` parameter; passing
`config=FightConfig.standard_fight()` reaches LIVE_PLAY
(standup=10) on the running sim — byte-verified by wrapper-
captured self.config snapshot on one EP1 pair, three call paths.
The D2 anchor values (32.9% DEC at C1's seed 400000+idx, 2455/2455
row-for-row) were reproduced via the bundle path in D2 v2/v3 and
remain self-consistent — they simply weren't the only reachable
form of "LIVE_PLAY on fi." The D2 v1 harness's 26.23% DEC was
purely the no-config FI_FALLBACK, not a structural fi limitation.
AUTOPSY LINE (all measured): skill doesn't help you land, being
worse helps you grapple at extremes, submissions are the only
honest wire, speed decides everything else, resilience is
decorative.

## P3-3 CONTEST REBUILD OUTCOMES (measured 2026-09-04, C19)

F4 FIXED — boxing +1SD → +2.13pp (CI ±1.30 excludes 0). The
three-week boxing inversion (F4 −5.74pp pre-P3-3) LOCATED IN THE
CONTEST LAYER. The landing wire was the whole story: rebuilt CSS
composites + P_c form + symmetric variance + retired result-level
upset branches → boxing turns positive on the same P2c instrument.
F3 FIXED — striking_defense ALIVE (+3.94pp, CI excludes 0). Dead-
stat resurrected on the P3-3 physics; SD now enters every strike
D recipe (0.65 weight in punch/kick, 0.60 in clinch_strike).
F6 direction FIXED — all strike-family signed slopes positive
(punch +5.6, kick +4.2, clinch_strike +3.0pp per 20-pt signed gap;
all were ~0 pre-P3-3 per D2 v3 measurement). Slopes shallow vs
D10 targets (+15pp strikes); calibration deferred to P3-5 (S5).
F8 preserved — sub_lockin slope +13.3pp per 20pt (target +14pp);
new P_c form on sub_lockin class matches the pre-P3-3 signature
almost exactly.
F9 GONE — no −9pp extreme inversion in default grappling.
Result-level upset branches retired per D4 (F9's vindication).

F10 — THE ACTIVITY TAX (new, 2026-09-04). With F2's raw-init
god-mechanism removed (K_SPEED_INIT dampener + coin-flip tie-break),
speed's remaining channels can't reach the +8pp per-1SD target.
K_SPEED_INIT sweep at [0.35, 0.20, 0.10, 0.05, 0.02] all measured
NEGATIVE Δwin_pp: −7.58 / −12.47 / −7.71 / −1.22 / −1.22
(N_dec ≈ 5760 each, CI ±1.29). K=0.05 and K=0.02 collapse to
identical values (below noise threshold at negligible dial).
Mechanism: acting more (via initiative advantage OR composite
weight on speed) now costs stamina that the AMPLIFIED stamina
channel punishes. Cardio +1SD Δwin was +8.95pp at P2c (pre-P3-3);
NOW +18.48pp — cardio's channel doubled in importance because
speed's raw dominance no longer overshadows it. **Speed is CURED
TO NEUTRAL, not to target.** Target re-ruled at P3-5 after lever
two reprices activity (S5). Filed as watch-channel: any docket
that changes stamina physics also changes speed's worth.

D2-CONFIG amended (2026-09-03) unchanged by P3-3.

## ARCHITECT GATE ERRORS (filed, not softened)

GE-1 (P2): twin gate assumed slot symmetry the engine never had —
the "failure" was discovery F1.
GE-2 (P2b): draw-blind denominator; corrected metric = DECIDED
share; under shared-seed CRN twin baselines are mirror-symmetric by
construction (twin gate proves plumbing only).
GE-3 (P2c, cc's, filed by cc): _build override clobber — no-op gate
passed TRIVIALLY on a dead pipeline; only the POSITIVE control
discriminated. Standing lesson: a no-op control cannot prove life.
GE-4 (D2): ±1pp anchor band on a ~2.7pp-2σ between-sample
comparison — a gate that couldn't reliably pass; replaced by EXACT
REPRODUCTION on C1's seed block (400000+idx).
GE-5 (D2): unsigned gap buckets pooled favored/unfavored attempts,
understating slope; closed by the signed re-cut (which delivered
F8/F9 as its reward).
GE-6 (P3-1): the draw-blind twin gate AGAIN (GE-2 repeated by the
architect in the P3-1 prompt); plus the P2b initiative wrapper
found NOT RNG-neutral post-coin-flip (~1pp) and RETIRED; twin gates
now use decided-share and pool >=2 seed blocks.

## DECISIONS LOG (all RATIFIED; dates 2026-09-02/03)

D1 health = stoppage proximity / accumulators = structural damage.
D2 P_even by measure-draft-adjust; docket delivered exact-anchored.
D3 attribute scopes table + guard rails (max 4 / min 1 lanes).
D4 upset branches retired (vindicated by F9).
D5 P2 sensitivity baseline; closed with F2-F5 banked.
D6 choke vs joint-lock refusal (sleep vs injury).
D7 POWER/strength split; roster to 19.
D8 aggression: tendency trait + per-fight choice + 4-rule table;
   fight_iq executes.
D9 finish model: five-part stoppage-pressure hybrid.
D10 P_even table + steeper S_c (strikes 45→60, TD 30→52 at 20-pt
    edge; subs steep as measured).
D11 elite-peer method mix 22/20/16/40/~2.
D12 leg-kick TKO private dial, ~1% of fights, first-class wow.
