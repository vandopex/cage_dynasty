# SUB-RATE1 cut filing (2026-11-16)

Docs for the SUB-RATE1 cut committed at d1f2568. This file records the
numbers measured during the arc. Every number is copied from one of the
seven files embedded below, except where an item states its source is
not embedded; none is recomputed in this header.

Sections, in order:
- MEASURED
- RULINGS (Van, 2026-11-16)
- FALSE AS WRITTEN
- NOT MEASURED
- ARCHITECT ERRORS
- CC PROCESS
- Embedded files (seven, verbatim, each preceded by its sha256)

## MEASURED

The committed change (d1f2568) — from outputs/cut_build_2026-11-16.txt.
- Edit site: cage_dynasty_web/fight_engine.py; one file; diff --stat
  `10 insertions(+), 5 deletions(-)`.
- Main-tree fight_engine.py sha256
  `191e616573a13bbf4117250997fd0e147b50568e0c0a26f7b856a158447abf48`;
  build-tree sha256 equal to main after apply.
- Six gates PASS: G1 syntax + diff, G2 build-tree sha equality,
  G3 fixed-population five-seed match, G4 clean-c7fe846 discrimination,
  G5 live seed-1 equivalence, G6 main-tree status.

Paired live result per arm and per seed — from
outputs/cut_paired_2026-11-16.txt. Seeds `20261114 / 20261115 / 20261116`
with the paired-uuid worker, PYTHONHASHSEED=0:

- arm C0 (control, /tmp/cd-exp-cut-c0): per-world SUB `89 / 92 / 95`;
  pooled `276/1206 = 22.89%`.
- arm C0r (same tree, LOJ_LIVE_RESEED=1, noise arm): per-world SUB
  `92 / 90 / 97`; pooled `279/1206 = 23.13%`. SUB count minus C0:
  `+3, -2, +2`; pooled `+3`. SUB% minus C0: `+0.75, -0.50, +0.50`;
  pooled `+0.25`.
- arm F1 (C7s, 0.45 / 0.4 / 0.5 + skill floor 80): per-world SUB
  `75 / 75 / 82`; pooled `232/1221 = 19.00%`. SUB count minus C0:
  `-14, -17, -13`; pooled `-44`. SUB% minus C0: `-3.48, -4.55, -3.63`;
  pooled `-3.88`.
- arm F2 (C5s, 0.3 / 0.3 / 0.4 + skill floor 80): per-world SUB
  `67 / 81 / 84`; pooled `232/1205 = 19.25%`. SUB count minus C0:
  `-22, -11, -11`; pooled `-44`. SUB% minus C0: `-5.43, -2.74, -2.74`;
  pooled `-3.63`.

Pooled per-winner-label on the paired arms — from
outputs/cut_paired_2026-11-16.txt:
- C0  BJJ Specialist `wins=177 wsub=128 app=331 win_rate=53.47 wsub%=72.32`
- C0  Wrestler        `wins=152 wsub=63  app=298 win_rate=51.01 wsub%=41.45`
- C0  Ground & Pound  `wins=255 wsub=47  app=455 win_rate=56.04 wsub%=18.43`
- C0  Clinch Fighter  `wins=116 wsub=17  app=222 win_rate=52.25 wsub%=14.66`
- C0r BJJ Specialist `wins=182 wsub=135 app=344 win_rate=52.91 wsub%=74.18`
- C0r Wrestler        `wins=164 wsub=65  app=310 win_rate=52.90 wsub%=39.63`
- C0r Ground & Pound  `wins=245 wsub=43  app=437 win_rate=56.06 wsub%=17.55`
- C0r Clinch Fighter  `wins=114 wsub=15  app=227 win_rate=50.22 wsub%=13.16`
- F1  BJJ Specialist `wins=173 wsub=136 app=359 win_rate=48.19 wsub%=78.61`
- F1  Wrestler        `wins=146 wsub=41  app=299 win_rate=48.83 wsub%=28.08`
- F1  Ground & Pound  `wins=254 wsub=28  app=451 win_rate=56.32 wsub%=11.02`
- F1  Clinch Fighter  `wins=114 wsub=16  app=234 win_rate=48.72 wsub%=14.04`
- F2  BJJ Specialist `wins=189 wsub=142 app=348 win_rate=54.31 wsub%=75.13`
- F2  Wrestler        `wins=163 wsub=35  app=310 win_rate=52.58 wsub%=21.47`
- F2  Ground & Pound  `wins=248 wsub=29  app=439 win_rate=56.49 wsub%=11.69`
- F2  Clinch Fighter  `wins=90  wsub=4   app=201 win_rate=44.78 wsub%=4.44`

Balanced per arm — from outputs/cut_paired_2026-11-16.txt:
- C0  `wins=47 wsub=4 app=162 win_rate=29.01 wsub%=8.51`
- C0r `wins=40 wsub=1 app=142 win_rate=28.17 wsub%=2.50`
- F1  `wins=56 wsub=4 app=143 win_rate=39.16 wsub%=7.14`
- F2  `wins=46 wsub=3 app=143 win_rate=32.17 wsub%=6.52`

Fixed-population build equivalence — from outputs/cut_build_2026-11-16.txt
G3 block. Five seed sets, 5400 fights:
- s1 sha `0938c4a6eefbc845a82e9ce6638a80feee5aaab185d32f30b21340d41d45a721`
   SUB 202 (matches C7s screen).
- s2 sha `0d3b8a0ec9f0efbb4c0602760369195b57f2ae6c79cc636fb38c2536b211ea9b`
   SUB 188.
- s3 sha `232866f4a08e1cd8954fb312c7bba361c2b638e0df94fba376c587ff5970c7c8`
   SUB 201.
- s4 sha `a2ffeb33113bb5ade095f82ff7fa02837ff3b5495fa4b976b3695141fb8e4637`
   SUB 175.
- s5 sha `babf3a7ad94cc941d2c2d6c88d385ae45be69752c0c59dfb69415b77a056a172`
   SUB 177.
- pooled SUB 943 (expected 943).
- discrimination against clean c7fe846: five S0 shas match filed L1,
  pooled 1147; 0 of 5 collide with the C7s shas.

Live seed-1 equivalence — from outputs/cut_build_2026-11-16.txt G5 block.
- build-tree row-list sha
  `425424cc9c94f7d116ec2aad23a507b61c3544b9c7792189e185c6d8f86797b3`;
  fights 402, SUB 75; equal to F1/w1 from the round-5 paired run.

Bridge-label control — from outputs/bridge_label_control_2026-11-16.txt.

RUN A (fresh new_game + 10 live weeks, counters reset post-new_game):
- `site_17404_make_fighter_attrs`: total 15832, fallback 0,
  `fallback_labels={}`.
- `site_18367_resolve_gameplan`: total 15832, fallback 15832,
  fallback_labels across the 11 canonical display names (designed
  passthrough; the map holds only legacy→canonical keys).
- `site_7467_convert_real_fighter`: total 256, fallback 256,
  `fallback_labels={'Balanced': 256}`.
- engine `_STYLE1_LABEL_COUNTER` per fe module object:
  `simulation.fight_engine = {'missing': 0, 'unmapped': {}}`;
  `fight_engine = {'missing': 0, 'unmapped': {}}`.
- Sites that fired 0 times in 10 weeks: `site_5289_resolve_ai_gp`,
  `site_17688_assemble_prefight_s1`, `site_17689_assemble_prefight_s2`,
  `site_22265_sign_amateur`.

RUN B (planted control, one week):
- plant_week 1; f1 Eduardo Magalhaes (`e9969da2`) label
  `'BJJ Specialist' -> None`; f2 Leandro Pereira (`9c4b40f2`) label
  `'BJJ Specialist' -> 'Not A Style'`. Both fought.
- engine received for each fighter: `BALANCED` on every one of 51
  `_make_fighter_attrs` calls per fighter.
- `site_17404_make_fighter_attrs`: total 2318, fallback 102,
  `fallback_labels={'None': 51, 'Not A Style': 51}`.
- engine `_STYLE1_LABEL_COUNTER` per fe module object:
  `simulation.fight_engine = {'missing': 0, 'unmapped': {}}`;
  `fight_engine = {'missing': 0, 'unmapped': {}}`.

## RULINGS (Van, 2026-11-16)

- Submission column: WRESTLER 0.45, GROUND_AND_POUND 0.4,
  CLINCH_FIGHTER 0.5.
- Skill floor: at the sub gate, `max(1, sub_weight)` applies when the
  style key is BJJ_SPECIALIST or `fighter_attrs.submissions >= 80`;
  every non-BJJ style below 80 keeps its computed sub_weight.
- Cut committed local (d1f2568), not pushed.
- One-judge (48f9704) deploys alone first.

## FALSE AS WRITTEN

1. "One-judge live 24.21% SUB" as the rate on the one-judge engine.
   That number is one three-world draw (filed in
   outputs/live_onejudge_2026-11-14.txt). Same-engine arms in this
   arc read `21.76%` (outputs/cut_sandbox_2026-11-14.txt, arm c0
   pooled), `22.89%` (outputs/cut_paired_2026-11-16.txt, arm C0
   pooled) and `23.13%` (outputs/cut_paired_2026-11-16.txt, arm C0r
   pooled).
2. Seeds 20261114 / 20261115 / 20261116 as pairing arms. Without the
   seeded-uuid worker the same seed gives a different live world: in
   outputs/cut_sandbox_2026-11-14.txt, arms loj_filed and c0 run the
   same engine on the same three seeds and read per-world SUB
   95 / 99 / 98 and 87 / 98 / 77. A fighter-id intersection of 1 was
   reported in cc's terminal on 2026-11-14 and is not in any embedded
   file.
3. 48f9704 commit message "same seed twice gives the same world".
   Holds for new_game and pre-generation: the pre-generation counter
   line (the smaller of the two ===CUT_COUNTERS=== lines per world;
   both lines carry module_name "fight_engine") is identical between
   the unseeded c0 worlds in outputs/cut_sandbox_2026-11-14.txt and
   the seeded C0 / C0r worlds printed in
   outputs/cut_gate0_2026-11-16.txt item 1, on all three seeds. Does
   not hold for live weeks: see item 2.
4. outputs/cut_round2_gates_2026-11-14.txt GATE 0c "no sub_weight
   assignment in :2496-2597". Assignments exist at :2540, :2544 and
   :2568. Read 2026-11-16 from the c7fe846 engine file, sub_weight is
   assigned at :2115, :2120, :2491, :2540, :2544, :2568, :2598, :2606
   and :2608. That list is not in any embedded file: the round-3 read
   appended to outputs/cut_screen_2026-11-16.txt (embed 2) printed only
   :2491 and :2598, because its search pattern did not match.
5. outputs/cut_gate0_2026-11-16.txt item 1 "byte-equal (pre-gen):
   True". The check searched for a module name that does not occur
   and compared two empty strings on all three seeds; it could not
   fail. The equality is read from the counter lines printed in that
   same item: seeds 20261115 and 20261116 directly (C0 against C0r);
   seed 20261114 from the C0r line against the c0/w1 line in
   outputs/cut_sandbox_2026-11-14.txt.
6. Round-5 C0r roster gate (outputs/cut_round5_gates_2026-11-16.txt
   (not embedded)). The roster probe does not reference
   `LOJ_LIVE_RESEED`; the probe's roster for the c0 tree at a given
   seed is the same whether the worker will later reseed or not. The
   gate as written cannot fail.
7. BRIDGE-LABEL-FALLBACK1 marked READ in the backlog. The Run B
   control in outputs/bridge_label_control_2026-11-16.txt measures
   it: planted `None` and planted `"Not A Style"` reach the fight as
   `BALANCED` on every call, with zero engine counter ticks. Status
   is MEASURED.

## NOT MEASURED

- Live comparison on the committed tree beyond seed 20261114. G5
  confirmed one row-list sha; seeds 20261115 and 20261116 against the
  build tree were not run.
- Odds shift: whether MC-odds win-probability output per bout shifts
  with the cut is not on file.
- PA import context for d1f2568; the engine has not been deployed.
- Pre-generation method mix after the cut (SUB / KO / TKO / DEC) is
  not reported in any embedded file.
- `site_22265_sign_amateur` fired 0 times in RUN A; its fallback
  behavior on `None` and on unmapped labels is unmeasured.
- Player-label paths (PLAYER-LABEL-PATHS1) are not re-measured here.
- Bridge-label fallback behavior beyond one world and ten weeks
  (RUN A) and one planted week (RUN B).

## ARCHITECT ERRORS

- The round-2 Gate 1 required row-list equality across two fresh
  processes against a filed JSON; uuid4 is unseeded, so it could not
  pass on the engine at HEAD.
- The round-3 Gate P2 required byte-equal rosters across arms with
  the same seed; divergent pre-gen trajectories under different
  engine values break roster byte-equality even when the uuid4
  patch is in place. The gate was stricter than the question.
- Three wrong reads of the attempt floor. 2026-11-14: inferred the
  floor cancelled the weight cuts, before reading the code.
  2026-11-15: read "about 85% of gate passes are floor binds" (c0
  counters, outputs/cut_sandbox_2026-11-14.txt) as the floor being
  the main lever; that counter says where attempts are allowed, not
  where finishes come from. 2026-11-16: read one fixed-population
  seed set as the floor contributing little. The screen in
  outputs/cut_screen_2026-11-16.txt put floor removal (C4, 1013)
  beside the weight cuts (C2, 999) against S0 1147.
- A 19-20% gate was applied to an unpaired three-world live
  instrument (the round-2 arms in outputs/cut_sandbox_2026-11-14.txt);
  three worlds against an unseeded live RNG cannot tell 19% from 21%.
- Three live rounds were run before the fixed-population screen
  ranked the levers. The screen is faster and strictly a ranking
  tool; running it first would have shortened the arc.
- Cited the round-3 read as holding the full sub_weight list without
  having read that file; it held two lines.

## CC PROCESS

- Bytecode introspection for the sandbox table-value print returned
  nothing on the first pass; the second instrument captured
  `_STYLE_WEIGHTS[...]` directly from the live select_action body.
- Three checks that could not fail: the 2026-11-15 rerun of Gate 0c
  returned empty from a broken search with no control; the cut_gate0
  item 1 equality compared empty strings; the round-5 C0r roster
  probe ignored the reseed setting.
- Stopped after the round-5 screen and finalist selection without
  running the live arms and without stating a reason.
- BJJ-WINRATE-WATCH1 was first drafted with seven per-arm win counts
  attributed to a file with six cut arms; corrected before commit.
  The seven values written (675 / 675 / 673 / 673 / 673 / 673 / 673)
  were not copied from any file; they did not match either the
  round-4 file (outputs/cut_screen_2026-11-16.txt pooled BJJ Specialist
  wins read 673 / 676 / 678 / 673 / 675 / 678 / 686 for S0 / C1..C6)
  or the round-5 file (outputs/cut_round5_screen_2026-11-16.txt pooled
  BJJ Specialist wins read 673 / 676 / 675 / 675 / 677 for S0 / C7 /
  C7s / C7t / C5s). Corrected to the two numbers actually cited,
  S0 673 and C7s 675.
- The round-3 closing message listed seven sub_weight line numbers as
  the read's result; the file held two.

## Embedded files

Seven source files, byte-identical to their outputs/ copies, each
preceded by its sha256.


## Embed 1/7 — outputs/cut_sandbox_2026-11-14.txt
sha256 23726ab30dbcac50d1f34aa078aa858b2ecb3a898d9e6c949a547e1433bb7ade

=== CUT SANDBOX report (c0 instrument-only, c1/c2/c3 cut values; loj_filed is the filed control arm) ===

--- arm loj_filed ---
  world       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%   t_live
  ------------------------------------------------------------------
  w1        402    95    3   165   132     7      0   23.63    684.7
  w2        402    99    2   147   149     5      0   24.63    615.8
  w3        402    98    6   169   120     9      0   24.38    633.1
  pooled   1206   292   11   481   401    21      0   24.21   1933.6
  per-world SUB%: [23.6318407960199, 24.62686567164179, 24.378109452736318]  mean=24.21  sd=0.518

  per winner_style, loj_filed (pooled across 3 worlds):
    label                   wins   wins_sub   wsub%
    BJJ Specialist           186        145   77.96
    Wrestler                 134         54   40.30
    Ground & Pound           249         45   18.07
    Clinch Fighter           101         18   17.82
    Muay Thai                102          7    6.86
    Striker                   39          0    0.00
    Counter Striker          162         10    6.17
    Pressure Fighter          83          7    8.43
    Sprawl & Brawl            62          0    0.00
    Point Fighter             23          0    0.00
    Balanced                  44          6   13.64

  appearances + win rate per label, loj_filed (pooled):
    label                   app    wins    win%
    BJJ Specialist          340     186   54.71
    Wrestler                289     134   46.37
    Ground & Pound          455     249   54.73
    Clinch Fighter          208     101   48.56
    Muay Thai               185     102   55.14
    Striker                  94      39   41.49
    Counter Striker         338     162   47.93
    Pressure Fighter        168      83   49.40
    Sprawl & Brawl          130      62   47.69
    Point Fighter            46      23   50.00
    Balanced                138      44   31.88


--- arm c0 ---
  world       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%   t_live
  ------------------------------------------------------------------
  w1        400    87    3   156   152     2      0   21.75    972.6
  w2        402    98    1   146   155     2      0   24.38   1911.7
  w3        402    77    4   176   140     5      0   19.15   2371.3
  pooled   1204   262    8   478   447     9      0   21.76   5255.6
  per-world SUB%: [21.75, 24.378109452736318, 19.154228855721392]  mean=21.76  sd=2.612

  per winner_style, c0 (pooled across 3 worlds):
    label                   wins   wins_sub   wsub%
    BJJ Specialist           177        133   75.14
    Wrestler                 165         52   31.52
    Ground & Pound           239         36   15.06
    Clinch Fighter           110         17   15.45
    Muay Thai                 86          7    8.14
    Striker                   39          0    0.00
    Counter Striker          171          6    3.51
    Pressure Fighter          75          3    4.00
    Sprawl & Brawl            60          2    3.33
    Point Fighter             25          1    4.00
    Balanced                  48          5   10.42

  appearances + win rate per label, c0 (pooled):
    label                   app    wins    win%
    BJJ Specialist          330     177   53.64
    Wrestler                309     165   53.40
    Ground & Pound          439     239   54.44
    Clinch Fighter          222     110   49.55
    Muay Thai               172      86   50.00
    Striker                 106      39   36.79
    Counter Striker         319     171   53.61
    Pressure Fighter        168      75   44.64
    Sprawl & Brawl          132      60   45.45
    Point Fighter            50      25   50.00
    Balanced                152      48   31.58

  cut counters c0/w1 module=fight_engine:
    table: WRESTLER_sub=None G&P_sub=None CF_sub=None BJJ_sub=None thr_bjj_sambo=None thr_other=None  table_captured=None
    gate: passed=1481399 failed=3754512 floor_binds=1261765  subs_hist={'<60': 2583973, '60-69': 1239235, '70-79': 915681, '80+': 497022}
    lookups (subset): {'WRESTLER': 1077283, 'BJJ_SPECIALIST': 449620, 'GROUND_AND_POUND': 1238909, 'CLINCH_FIGHTER': 439253, 'SAMBO': 0}  default_fallbacks={}
  cut counters c0/w1 module=fight_engine:
    table: WRESTLER_sub=None G&P_sub=None CF_sub=None BJJ_sub=None thr_bjj_sambo=None thr_other=None  table_captured=None
    gate: passed=22536 failed=75989 floor_binds=19138  subs_hist={'<60': 56504, '60-69': 18574, '70-79': 14323, '80+': 9124}
    lookups (subset): {'WRESTLER': 16098, 'BJJ_SPECIALIST': 10210, 'GROUND_AND_POUND': 21166, 'CLINCH_FIGHTER': 8033, 'SAMBO': 0}  default_fallbacks={}
  cut counters c0/w2 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=1870091 failed=4096491 floor_binds=1610840  subs_hist={'<60': 2255566, '60-69': 1570819, '70-79': 1522809, '80+': 617388}
    lookups (subset): {'WRESTLER': 504581, 'BJJ_SPECIALIST': 798978, 'GROUND_AND_POUND': 1197064, 'CLINCH_FIGHTER': 799126, 'SAMBO': 0}  default_fallbacks={}
  cut counters c0/w2 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=25856 failed=71631 floor_binds=22554  subs_hist={'<60': 45908, '60-69': 24927, '70-79': 17409, '80+': 9243}
    lookups (subset): {'WRESTLER': 8006, 'BJJ_SPECIALIST': 10388, 'GROUND_AND_POUND': 19289, 'CLINCH_FIGHTER': 11451, 'SAMBO': 0}  default_fallbacks={}
  cut counters c0/w3 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=1471080 failed=4284752 floor_binds=1256609  subs_hist={'<60': 2999268, '60-69': 939391, '70-79': 724579, '80+': 1092594}
    lookups (subset): {'WRESTLER': 796426, 'BJJ_SPECIALIST': 667413, 'GROUND_AND_POUND': 1093172, 'CLINCH_FIGHTER': 439964, 'SAMBO': 0}  default_fallbacks={}
  cut counters c0/w3 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=24562 failed=72232 floor_binds=21104  subs_hist={'<60': 51064, '60-69': 18729, '70-79': 12642, '80+': 14359}
    lookups (subset): {'WRESTLER': 15004, 'BJJ_SPECIALIST': 10268, 'GROUND_AND_POUND': 16533, 'CLINCH_FIGHTER': 8456, 'SAMBO': 0}  default_fallbacks={}


--- arm c1 ---
  world       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%   t_live
  ------------------------------------------------------------------
  w1        408    91    3   150   160     4      0   22.30   1798.0
  w2        401    78    3   165   154     1      0   19.45   2373.6
  w3        409    83    1   175   144     6      0   20.29   1203.6
  pooled   1218   252    7   490   458    11      0   20.69   5375.2
  per-world SUB%: [22.30392156862745, 19.45137157107232, 20.293398533007334]  mean=20.68  sd=1.466

  per winner_style, c1 (pooled across 3 worlds):
    label                   wins   wins_sub   wsub%
    BJJ Specialist           180        137   76.11
    Wrestler                 142         37   26.06
    Ground & Pound           248         38   15.32
    Clinch Fighter           112         10    8.93
    Muay Thai                100          9    9.00
    Striker                   46          2    4.35
    Counter Striker          158          9    5.70
    Pressure Fighter          85          4    4.71
    Sprawl & Brawl            69          4    5.80
    Point Fighter             24          0    0.00
    Balanced                  43          2    4.65

  appearances + win rate per label, c1 (pooled):
    label                   app    wins    win%
    BJJ Specialist          354     180   50.85
    Wrestler                280     142   50.71
    Ground & Pound          455     248   54.51
    Clinch Fighter          224     112   50.00
    Muay Thai               197     100   50.76
    Striker                  98      46   46.94
    Counter Striker         311     158   50.80
    Pressure Fighter        169      85   50.30
    Sprawl & Brawl          143      69   48.25
    Point Fighter            47      24   51.06
    Balanced                147      43   29.25

  cut counters c1/w1 module=fight_engine:
    table: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=1611571 failed=3810594 floor_binds=1375164  subs_hist={'<60': 2390605, '60-69': 1442473, '70-79': 868643, '80+': 720444}
    lookups (subset): {'WRESTLER': 795950, 'BJJ_SPECIALIST': 781418, 'GROUND_AND_POUND': 1429599, 'CLINCH_FIGHTER': 528561, 'SAMBO': 0}  default_fallbacks={}
  cut counters c1/w1 module=fight_engine:
    table: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=25307 failed=73695 floor_binds=20570  subs_hist={'<60': 53505, '60-69': 21532, '70-79': 12867, '80+': 11098}
    lookups (subset): {'WRESTLER': 15648, 'BJJ_SPECIALIST': 9512, 'GROUND_AND_POUND': 22765, 'CLINCH_FIGHTER': 8598, 'SAMBO': 0}  default_fallbacks={}
  cut counters c1/w2 module=fight_engine:
    table: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=1828843 failed=3969691 floor_binds=1568670  subs_hist={'<60': 2187837, '60-69': 1557700, '70-79': 1336959, '80+': 716038}
    lookups (subset): {'WRESTLER': 711291, 'BJJ_SPECIALIST': 655102, 'GROUND_AND_POUND': 1436049, 'CLINCH_FIGHTER': 691335, 'SAMBO': 0}  default_fallbacks={}
  cut counters c1/w2 module=fight_engine:
    table: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=26798 failed=70910 floor_binds=22796  subs_hist={'<60': 45025, '60-69': 24377, '70-79': 17934, '80+': 10372}
    lookups (subset): {'WRESTLER': 7898, 'BJJ_SPECIALIST': 10548, 'GROUND_AND_POUND': 20081, 'CLINCH_FIGHTER': 11278, 'SAMBO': 0}  default_fallbacks={}
  cut counters c1/w3 module=fight_engine:
    table: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=1848952 failed=4187161 floor_binds=1571105  subs_hist={'<60': 2468093, '60-69': 1553988, '70-79': 1032266, '80+': 981766}
    lookups (subset): {'WRESTLER': 730740, 'BJJ_SPECIALIST': 720688, 'GROUND_AND_POUND': 1354747, 'CLINCH_FIGHTER': 631246, 'SAMBO': 0}  default_fallbacks={}
  cut counters c1/w3 module=fight_engine:
    table: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=24839 failed=72946 floor_binds=20518  subs_hist={'<60': 51434, '60-69': 19741, '70-79': 13266, '80+': 13344}
    lookups (subset): {'WRESTLER': 14436, 'BJJ_SPECIALIST': 11044, 'GROUND_AND_POUND': 15763, 'CLINCH_FIGHTER': 9017, 'SAMBO': 0}  default_fallbacks={}


--- arm c2 ---
  world       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%   t_live
  ------------------------------------------------------------------
  w1        411    75    3   159   171     3      0   18.25   1940.1
  w2        401    76    3   173   145     4      0   18.95   2376.3
  w3        402    84    6   181   123     8      0   20.90   1111.3
  pooled   1214   235   12   513   439    15      0   19.36   5427.7
  per-world SUB%: [18.248175182481752, 18.952618453865338, 20.895522388059703]  mean=19.37  sd=1.371

  per winner_style, c2 (pooled across 3 worlds):
    label                   wins   wins_sub   wsub%
    BJJ Specialist           189        129   68.25
    Wrestler                 155         46   29.68
    Ground & Pound           258         31   12.02
    Clinch Fighter           100         14   14.00
    Muay Thai                 83          2    2.41
    Striker                   43          0    0.00
    Counter Striker          151          2    1.32
    Pressure Fighter          78          3    3.85
    Sprawl & Brawl            81          2    2.47
    Point Fighter             19          0    0.00
    Balanced                  42          6   14.29

  appearances + win rate per label, c2 (pooled):
    label                   app    wins    win%
    BJJ Specialist          366     189   51.64
    Wrestler                293     155   52.90
    Ground & Pound          462     258   55.84
    Clinch Fighter          229     100   43.67
    Muay Thai               182      83   45.60
    Striker                  98      43   43.88
    Counter Striker         302     151   50.00
    Pressure Fighter        155      78   50.32
    Sprawl & Brawl          149      81   54.36
    Point Fighter            42      19   45.24
    Balanced                135      42   31.11

  cut counters c2/w1 module=fight_engine:
    table: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=1738684 failed=4256706 floor_binds=1462523  subs_hist={'<60': 2929604, '60-69': 1523239, '70-79': 890416, '80+': 652131}
    lookups (subset): {'WRESTLER': 965900, 'BJJ_SPECIALIST': 586208, 'GROUND_AND_POUND': 1812816, 'CLINCH_FIGHTER': 603279, 'SAMBO': 0}  default_fallbacks={}
  cut counters c2/w1 module=fight_engine:
    table: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=24290 failed=74654 floor_binds=20614  subs_hist={'<60': 54350, '60-69': 20804, '70-79': 13212, '80+': 10578}
    lookups (subset): {'WRESTLER': 15647, 'BJJ_SPECIALIST': 10657, 'GROUND_AND_POUND': 24377, 'CLINCH_FIGHTER': 7371, 'SAMBO': 0}  default_fallbacks={}
  cut counters c2/w2 module=fight_engine:
    table: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=1934865 failed=3838139 floor_binds=1660029  subs_hist={'<60': 1936853, '60-69': 1759583, '70-79': 1311239, '80+': 765329}
    lookups (subset): {'WRESTLER': 575591, 'BJJ_SPECIALIST': 852896, 'GROUND_AND_POUND': 996624, 'CLINCH_FIGHTER': 748719, 'SAMBO': 0}  default_fallbacks={}
  cut counters c2/w2 module=fight_engine:
    table: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=26192 failed=72553 floor_binds=21972  subs_hist={'<60': 46842, '60-69': 23440, '70-79': 17787, '80+': 10676}
    lookups (subset): {'WRESTLER': 8995, 'BJJ_SPECIALIST': 9925, 'GROUND_AND_POUND': 18310, 'CLINCH_FIGHTER': 12418, 'SAMBO': 0}  default_fallbacks={}
  cut counters c2/w3 module=fight_engine:
    table: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=1822895 failed=3557562 floor_binds=1540055  subs_hist={'<60': 2213822, '60-69': 1298375, '70-79': 819829, '80+': 1048431}
    lookups (subset): {'WRESTLER': 746760, 'BJJ_SPECIALIST': 893946, 'GROUND_AND_POUND': 1205086, 'CLINCH_FIGHTER': 491112, 'SAMBO': 0}  default_fallbacks={}
  cut counters c2/w3 module=fight_engine:
    table: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=60  table_captured=True
    gate: passed=25565 failed=73977 floor_binds=21551  subs_hist={'<60': 52989, '60-69': 17776, '70-79': 15050, '80+': 13727}
    lookups (subset): {'WRESTLER': 14780, 'BJJ_SPECIALIST': 10287, 'GROUND_AND_POUND': 17996, 'CLINCH_FIGHTER': 8873, 'SAMBO': 0}  default_fallbacks={}


--- arm c3 ---
  world       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%   t_live
  ------------------------------------------------------------------
  w1        409    78    0   153   173     5      0   19.07   1782.7
  w2        400    72    3   159   161     5      0   18.00   2357.4
  w3        400    93    4   139   156     8      0   23.25   1072.3
  pooled   1209   243    7   451   490    18      0   20.10   5212.4
  per-world SUB%: [19.070904645476773, 18.0, 23.25]  mean=20.11  sd=2.774

  per winner_style, c3 (pooled across 3 worlds):
    label                   wins   wins_sub   wsub%
    BJJ Specialist           189        144   76.19
    Wrestler                 151         38   25.17
    Ground & Pound           238         36   15.13
    Clinch Fighter           109          9    8.26
    Muay Thai                 86          5    5.81
    Striker                   41          1    2.44
    Counter Striker          163          6    3.68
    Pressure Fighter          70          3    4.29
    Sprawl & Brawl            72          1    1.39
    Point Fighter             20          0    0.00
    Balanced                  52          0    0.00

  appearances + win rate per label, c3 (pooled):
    label                   app    wins    win%
    BJJ Specialist          356     189   53.09
    Wrestler                296     151   51.01
    Ground & Pound          427     238   55.74
    Clinch Fighter          223     109   48.88
    Muay Thai               178      86   48.31
    Striker                 100      41   41.00
    Counter Striker         325     163   50.15
    Pressure Fighter        150      70   46.67
    Sprawl & Brawl          149      72   48.32
    Point Fighter            50      20   40.00
    Balanced                146      52   35.62

  cut counters c3/w1 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=70  table_captured=True
    gate: passed=966428 failed=4384848 floor_binds=821650  subs_hist={'<60': 2516716, '60-69': 1222499, '70-79': 1022745, '80+': 589316}
    lookups (subset): {'WRESTLER': 769622, 'BJJ_SPECIALIST': 472247, 'GROUND_AND_POUND': 1728937, 'CLINCH_FIGHTER': 359259, 'SAMBO': 0}  default_fallbacks={}
  cut counters c3/w1 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=70  table_captured=True
    gate: passed=13722 failed=86991 floor_binds=11775  subs_hist={'<60': 57408, '60-69': 21173, '70-79': 13833, '80+': 8299}
    lookups (subset): {'WRESTLER': 14955, 'BJJ_SPECIALIST': 9908, 'GROUND_AND_POUND': 21485, 'CLINCH_FIGHTER': 9438, 'SAMBO': 0}  default_fallbacks={}
  cut counters c3/w2 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=70  table_captured=True
    gate: passed=926986 failed=4755236 floor_binds=800796  subs_hist={'<60': 2483136, '60-69': 1446597, '70-79': 1110686, '80+': 641803}
    lookups (subset): {'WRESTLER': 569927, 'BJJ_SPECIALIST': 614061, 'GROUND_AND_POUND': 1199952, 'CLINCH_FIGHTER': 777767, 'SAMBO': 0}  default_fallbacks={}
  cut counters c3/w2 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=70  table_captured=True
    gate: passed=15901 failed=80867 floor_binds=13633  subs_hist={'<60': 46018, '60-69': 22902, '70-79': 17197, '80+': 10651}
    lookups (subset): {'WRESTLER': 7663, 'BJJ_SPECIALIST': 10541, 'GROUND_AND_POUND': 18558, 'CLINCH_FIGHTER': 11220, 'SAMBO': 0}  default_fallbacks={}
  cut counters c3/w3 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=70  table_captured=True
    gate: passed=1028237 failed=4105261 floor_binds=879714  subs_hist={'<60': 2665378, '60-69': 671071, '70-79': 720394, '80+': 1076655}
    lookups (subset): {'WRESTLER': 588212, 'BJJ_SPECIALIST': 730991, 'GROUND_AND_POUND': 759853, 'CLINCH_FIGHTER': 685083, 'SAMBO': 0}  default_fallbacks={}
  cut counters c3/w3 module=fight_engine:
    table: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj_sambo=45 thr_other=70  table_captured=True
    gate: passed=17745 failed=83647 floor_binds=15159  subs_hist={'<60': 54041, '60-69': 17563, '70-79': 15652, '80+': 14136}
    lookups (subset): {'WRESTLER': 13017, 'BJJ_SPECIALIST': 12694, 'GROUND_AND_POUND': 16243, 'CLINCH_FIGHTER': 9418, 'SAMBO': 0}  default_fallbacks={}


=== per-arm SUB% mean + sd (cut arms vs loj_filed) ===
  arm          pooled%     mean%      sd  per-world
  loj_filed      24.21     24.21   0.518  [23.63, 24.63, 24.38]
  c0             21.76     21.76   2.612  [21.75, 24.38, 19.15]
  c1             20.69     20.68   1.466  [22.30, 19.45, 20.29]
  c2             19.36     19.37   1.371  [18.25, 18.95, 20.90]
  c3             20.10     20.11   2.774  [19.07, 18.00, 23.25]

NOTE: all cut-arm worlds were run under concurrency (4 or 3 processes in parallel, one per worktree); t_live inflated vs the filed loj_* arm which ran sequentially.

## Embed 2/7 — outputs/cut_screen_2026-11-16.txt
sha256 a2fe567d7fee6a967ed6aee7d3f6be9e2791c0b1e76011d43002fb2dc33d84b3

=== CUT SANDBOX round-4 fixed-population screen ===
arms: S0 C1 C2 C3 C4 C5 C6
seed sets: (1, 2, 3, 4, 5) (offsets 0, 10M, 20M, 30M, 40M; 1080 fights each)

--- arm S0 ---
  seed       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%  dSUB_vs_S0
  s1      1080   244    7   406   412    11      0   22.59  +0
  s2      1080   227    7   425   408    13      0   21.02  +0
  s3      1080   233    6   411   416    14      0   21.57  +0
  s4      1080   227    7   414   413    19      0   21.02  +0
  s5      1080   216    3   441   404    16      0   20.00  +0
  pool    5400  1147   30  2097  2053    73      0   21.24  +0

--- arm C1 ---
  seed       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%  dSUB_vs_S0
  s1      1080   220    7   412   430    11      0   20.37  -24
  s2      1080   210    7   438   412    13      0   19.44  -17
  s3      1080   227    6   413   420    14      0   21.02  -6
  s4      1080   201    7   426   427    19      0   18.61  -26
  s5      1080   202    3   446   413    16      0   18.70  -14
  pool    5400  1060   30  2135  2102    73      0   19.63  -87

--- arm C2 ---
  seed       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%  dSUB_vs_S0
  s1      1080   198    7   424   440    11      0   18.33  -46
  s2      1080   202    7   443   415    13      0   18.70  -25
  s3      1080   219    6   414   427    14      0   20.28  -14
  s4      1080   185    7   438   431    19      0   17.13  -42
  s5      1080   195    4   448   417    16      0   18.06  -21
  pool    5400   999   31  2167  2130    73      0   18.50  -148

--- arm C3 ---
  seed       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%  dSUB_vs_S0
  s1      1080   209    7   412   441    11      0   19.35  -35
  s2      1080   205    7   428   427    13      0   18.98  -22
  s3      1080   207    6   414   439    14      0   19.17  -26
  s4      1080   199    9   419   435    18      0   18.43  -28
  s5      1080   190    3   448   423    16      0   17.59  -26
  pool    5400  1010   32  2121  2165    72      0   18.70  -137

--- arm C4 ---
  seed       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%  dSUB_vs_S0
  s1      1080   223    7   413   426    11      0   20.65  -21
  s2      1080   202    7   434   421    16      0   18.70  -25
  s3      1080   202    6   423   434    15      0   18.70  -31
  s4      1080   198    9   425   430    18      0   18.33  -29
  s5      1080   188    4   455   417    16      0   17.41  -28
  pool    5400  1013   33  2150  2128    76      0   18.76  -134

--- arm C5 ---
  seed       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%  dSUB_vs_S0
  s1      1080   172    7   435   454    12      0   15.93  -72
  s2      1080   173    7   451   433    16      0   16.02  -54
  s3      1080   181    6   432   446    15      0   16.76  -52
  s4      1080   150    9   453   450    18      0   13.89  -77
  s5      1080   163    5   463   433    16      0   15.09  -53
  pool    5400   839   34  2234  2216    77      0   15.54  -308

--- arm C6 ---
  seed       n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%  dSUB_vs_S0
  s1      1080   124    7   463   474    12      0   11.48  -120
  s2      1080   112    7   475   470    16      0   10.37  -115
  s3      1080   117    5   468   475    15      0   10.83  -116
  s4      1080   103   10   477   472    18      0    9.54  -124
  s5      1080   111    4   493   456    16      0   10.28  -105
  pool    5400   567   33  2376  2347    77      0   10.50  -580

--- arm S0, pooled 5 seeds, per winner label ---
  label                   wins   wins_sub     app   wsub%
  BJJ Specialist           673        494    1055   73.40
  Wrestler                 932        343    1585   36.80
  Ground & Pound          1012        186    1590   18.38
  Clinch Fighter           290         22     725    7.59
  Muay Thai                392         18    1035    4.59
  Striker                  235          8     705    3.40
  Counter Striker          582         30    1405    5.15
  Pressure Fighter         377         14     800    3.71
  Sprawl & Brawl           600         15    1015    2.50
  Point Fighter             68          0     220    0.00
  Balanced                 166         17     665   10.24

--- arm C1, pooled 5 seeds, per winner label ---
  label                   wins   wins_sub     app   wsub%
  BJJ Specialist           676        495    1055   73.22
  Wrestler                 930        293    1585   31.51
  Ground & Pound          1011        153    1590   15.13
  Clinch Fighter           290         18     725    6.21
  Muay Thai                392         17    1035    4.34
  Striker                  235          8     705    3.40
  Counter Striker          582         29    1405    4.98
  Pressure Fighter         376         14     800    3.72
  Sprawl & Brawl           600         15    1015    2.50
  Point Fighter             68          0     220    0.00
  Balanced                 167         18     665   10.78

--- arm C2, pooled 5 seeds, per winner label ---
  label                   wins   wins_sub     app   wsub%
  BJJ Specialist           678        497    1055   73.30
  Wrestler                 930        254    1585   27.31
  Ground & Pound          1009        130    1590   12.88
  Clinch Fighter           290         17     725    5.86
  Muay Thai                392         17    1035    4.34
  Striker                  235          8     705    3.40
  Counter Striker          581         29    1405    4.99
  Pressure Fighter         376         14     800    3.72
  Sprawl & Brawl           601         15    1015    2.50
  Point Fighter             68          0     220    0.00
  Balanced                 167         18     665   10.78

--- arm C3, pooled 5 seeds, per winner label ---
  label                   wins   wins_sub     app   wsub%
  BJJ Specialist           673        494    1055   73.40
  Wrestler                 932        271    1585   29.08
  Ground & Pound          1014        147    1590   14.50
  Clinch Fighter           289         15     725    5.19
  Muay Thai                392         17    1035    4.34
  Striker                  235          8     705    3.40
  Counter Striker          582         23    1405    3.95
  Pressure Fighter         375         10     800    2.67
  Sprawl & Brawl           602         12    1015    1.99
  Point Fighter             69          0     220    0.00
  Balanced                 165         13     665    7.88

--- arm C4, pooled 5 seeds, per winner label ---
  label                   wins   wins_sub     app   wsub%
  BJJ Specialist           675        494    1055   73.19
  Wrestler                 931        304    1585   32.65
  Ground & Pound          1009        140    1590   13.88
  Clinch Fighter           292         14     725    4.79
  Muay Thai                391         12    1035    3.07
  Striker                  235          4     705    1.70
  Counter Striker          586         22    1405    3.75
  Pressure Fighter         375          9     800    2.40
  Sprawl & Brawl           598          6    1015    1.00
  Point Fighter             69          0     220    0.00
  Balanced                 163          8     665    4.91

--- arm C5, pooled 5 seeds, per winner label ---
  label                   wins   wins_sub     app   wsub%
  BJJ Specialist           678        495    1055   73.01
  Wrestler                 922        193    1585   20.93
  Ground & Pound          1008         79    1590    7.84
  Clinch Fighter           292         11     725    3.77
  Muay Thai                393         12    1035    3.05
  Striker                  235          4     705    1.70
  Counter Striker          586         22    1405    3.75
  Pressure Fighter         377          9     800    2.39
  Sprawl & Brawl           600          6    1015    1.00
  Point Fighter             69          0     220    0.00
  Balanced                 163          8     665    4.91

--- arm C6, pooled 5 seeds, per winner label ---
  label                   wins   wins_sub     app   wsub%
  BJJ Specialist           686        502    1055   73.18
  Wrestler                 905          0    1585    0.00
  Ground & Pound          1009          0    1590    0.00
  Clinch Fighter           290          0     725    0.00
  Muay Thai                395         13    1035    3.29
  Striker                  235          4     705    1.70
  Counter Striker          587         23    1405    3.92
  Pressure Fighter         378          9     800    2.38
  Sprawl & Brawl           603          8    1015    1.33
  Point Fighter             70          0     220    0.00
  Balanced                 165          8     665    4.85

=== Per-arm SUB count minus S0 (per seed + pooled) ===
  arm      s1     s2     s3     s4     s5   pool
  S0       +0     +0     +0     +0     +0     +0
  C1      -24    -17     -6    -26    -14    -87
  C2      -46    -25    -14    -42    -21   -148
  C3      -35    -22    -26    -28    -26   -137
  C4      -21    -25    -31    -29    -28   -134
  C5      -72    -54    -52    -77    -53   -308
  C6     -120   -115   -116   -124   -105   -580

=== Per-arm wins-by-SUB count minus S0 for key labels (per seed + pooled) ===

  label: Wrestler
    arm      s1     s2     s3     s4     s5   pool
    S0       +0     +0     +0     +0     +0     +0
    C1      -14    -12     -3    -16     -5    -50
    C2      -31    -17     -4    -29     -8    -89
    C3      -20    -16     -7    -14    -15    -72
    C4       -5     -7     -4    -12    -11    -39
    C5      -41    -28    -15    -45    -21   -150
    C6      -75    -69    -64    -75    -60   -343

  label: Ground & Pound
    arm      s1     s2     s3     s4     s5   pool
    S0       +0     +0     +0     +0     +0     +0
    C1       -9     -5     -1    -10     -8    -33
    C2      -15     -8     -8    -12    -13    -56
    C3       -7     -4    -10    -12     -6    -39
    C4       -7    -11    -10    -11     -7    -46
    C5      -23    -19    -19    -24    -22   -107
    C6      -35    -41    -36    -40    -34   -186

  label: Clinch Fighter
    arm      s1     s2     s3     s4     s5   pool
    S0       +0     +0     +0     +0     +0     +0
    C1       -1     +0     -1     -2     +0     -4
    C2       +0     +0     -1     -4     +0     -5
    C3       -1     -1     -2     -1     -2     -7
    C4       -1     -1     -2     -2     -2     -8
    C5       +0     -1     -3     -5     -2    -11
    C6       -5     -2     -5     -6     -4    -22

  label: BJJ Specialist
    arm      s1     s2     s3     s4     s5   pool
    S0       +0     +0     +0     +0     +0     +0
    C1       +0     +0     +0     +2     -1     +1
    C2       +0     +0     +0     +3     +0     +3
    C3       -1     +1     +0     +0     +0     +0
    C4       +0     -1     +1     +1     -1     +0
    C5       +0     -1     +1     +2     -1     +1
    C6       +2     +0     +4     +2     +0     +8

=== Counters + table snapshot per arm (bare fight_engine module; one row per seed) ===

--- arm S0 counters ---
  s1: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=32379 gate_failed=89280 floor_binds=27121
  s2: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=32331 gate_failed=88957 floor_binds=26716
  s3: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33561 gate_failed=87830 floor_binds=27624
  s4: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=32541 gate_failed=89005 floor_binds=27239
  s5: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=32573 gate_failed=88049 floor_binds=27156

--- arm C1 counters ---
  s1: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33702 gate_failed=89979 floor_binds=27532
  s2: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33042 gate_failed=89324 floor_binds=26843
  s3: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33859 gate_failed=88224 floor_binds=27865
  s4: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33911 gate_failed=89707 floor_binds=27748
  s5: WRESTLER_sub=0.45 G&P_sub=0.4 CF_sub=0.5 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33348 gate_failed=88526 floor_binds=27469

--- arm C2 counters ---
  s1: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=34843 gate_failed=90633 floor_binds=27904
  s2: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33372 gate_failed=89524 floor_binds=26925
  s3: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=34232 gate_failed=88451 floor_binds=28006
  s4: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=34436 gate_failed=89917 floor_binds=27969
  s5: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33884 gate_failed=88694 floor_binds=27537

--- arm C3 counters ---
  s1: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=70
         gate_passed=22185 gate_failed=102093 floor_binds=18136
  s2: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=70
         gate_passed=21694 gate_failed=100951 floor_binds=17163
  s3: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=70
         gate_passed=22732 gate_failed=100778 floor_binds=18069
  s4: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=70
         gate_passed=22264 gate_failed=101420 floor_binds=17968
  s5: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=70
         gate_passed=21824 gate_failed=100924 floor_binds=17749

--- arm C4 counters ---
  s1: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33763 gate_failed=89754 floor_binds=28112
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s2: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33435 gate_failed=89469 floor_binds=27648
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s3: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=34932 gate_failed=88883 floor_binds=28619
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s4: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33953 gate_failed=89837 floor_binds=28300
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s5: WRESTLER_sub=0.9 G&P_sub=0.6 CF_sub=0.7 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=33718 gate_failed=88973 floor_binds=28031
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}

--- arm C5 counters ---
  s1: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=36340 gate_failed=91160 floor_binds=29010
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s2: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=34809 gate_failed=90181 floor_binds=28003
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s3: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=35895 gate_failed=89558 floor_binds=29102
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s4: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=35862 gate_failed=90874 floor_binds=29140
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s5: WRESTLER_sub=0.3 G&P_sub=0.3 CF_sub=0.4 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=35361 gate_failed=89674 floor_binds=28643
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}

--- arm C6 counters ---
  s1: WRESTLER_sub=0.0 G&P_sub=0.0 CF_sub=0.0 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=38360 gate_failed=91983 floor_binds=36821
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s2: WRESTLER_sub=0.0 G&P_sub=0.0 CF_sub=0.0 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=38015 gate_failed=91303 floor_binds=36719
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s3: WRESTLER_sub=0.0 G&P_sub=0.0 CF_sub=0.0 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=38765 gate_failed=90804 floor_binds=37276
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s4: WRESTLER_sub=0.0 G&P_sub=0.0 CF_sub=0.0 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=38128 gate_failed=92063 floor_binds=36875
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
  s5: WRESTLER_sub=0.0 G&P_sub=0.0 CF_sub=0.0 BJJ_sub=2.0 thr_bjj=45 thr_other=60
         gate_passed=37656 gate_failed=90739 floor_binds=36556
         gate_passed_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}
         wouldhave_bound_by_style: {WRESTLER=0, GROUND_AND_POUND=0, CLINCH_FIGHTER=0, BJJ_SPECIALIST=0, SAMBO=0}}


============================================================
=== APPENDED VERBATIM: outputs/cut_round3_gates_2026-11-15.txt ===
============================================================
=== READS ===

--- READ 1. sub_weight assignments in select_action, unmodified c7fe846 ---

  Control: :2491 and :2598 must appear above.
  :2491 present:
    sub_weight = int(sub_weight * _sw["submission"])
  :2598 present:
    sub_weight = int(sub_weight * stamina_factor)

--- READ 2a. Section 'P7. Same seed twice through new_game (pre-edit)' — lines 291-345 ---
291: ### P7. Same seed twice through new_game (pre-edit)
292: ```
293: run A: n=292  sig=1ac6c8f0fa9ee25256b6985284726744f39fd85da26ce6b0c3fe95cb81553d69
294: run B: n=292  sig=1ac6c8f0fa9ee25256b6985284726744f39fd85da26ce6b0c3fe95cb81553d69
295: identical worlds? True
296: ```
297: 
298: ### P8. Pre-gen 10 fixed seeds (deferred; see Step 4 table below for HEAD arm numbers)
299: 
300: ### P9. cage_dynasty_web/test_fight_sim.py (HEAD)
301: ```
302: rc = 0
303: Total fights:    220
304: Errors caught:   0
305: Finish rate:     19/220 = 8.6%
306: Decision rate:   193/220 = 87.7%
307: Draws:           8/220 = 3.6%
308: Method distribution:
309:   KO:     0  (  0.0%)
310:   TKO:   12  (  5.5%)
311:   SUB:    7  (  3.2%)
312:   DEC:  193  ( 87.7%)
313: ```
314: 
315: ## PHASE 1 — EDIT (git diff for the two named paths only)
316: 
317: ```diff
318: diff --git a/cage_dynasty_web/fight_engine.py b/cage_dynasty_web/fight_engine.py
319: index f9bbfda..ebd4db0 100644
320: --- a/cage_dynasty_web/fight_engine.py
321: +++ b/cage_dynasty_web/fight_engine.py
322: @@ -1805,6 +1805,22 @@ def get_available_grappling_actions(
323:  # FIGHTER STYLE DETECTION
324:  # ============================================================================
325:  
326: +# STYLE1 ONE-JUDGE: module-level counter for label-resolution outcomes.
327: +# Keyed 'missing' (count of calls with no label) and 'unmapped' (dict of
328: +# label-string -> count, for labels not in the hint map).
329: +_STYLE1_LABEL_COUNTER = {"missing": 0, "unmapped": {}}
330: +
331: +def _style1_label_counter_read():
332: +    """Return a snapshot of the one-judge label-resolution counter."""
333: +    return {"missing": _STYLE1_LABEL_COUNTER["missing"],
334: +            "unmapped": dict(_STYLE1_LABEL_COUNTER["unmapped"])}
335: +
336: +def _style1_label_counter_reset():
337: +    """Reset the one-judge label-resolution counter to zero."""
338: +    _STYLE1_LABEL_COUNTER["missing"] = 0
339: +    _STYLE1_LABEL_COUNTER["unmapped"] = {}
340: +
341: +
342:  def detect_fighter_style(fighter: FighterAttributes) -> str:
343:      """
344:      Detect a fighter's primary style based on attributes.
345: @@ -1812,6 +1828,38 @@ def detect_fighter_style(fighter: FighterAttributes) -> str:

--- READ 2b. Section 'Gate D — same seed twice gives same world (post-edit)' — lines 462-500 ---
462: ### Gate D — same seed twice gives same world (post-edit)
463: 
464: P7 at HEAD held YES (sig `1ac6c8f0…553d69`). Post-edit:
465: ```
466: run A: n=289  sig=64a556bc7e24d8e9ced6e12efa179b49a9ee283e07389f9bde8626db03d197b1
467: run B: n=289  sig=64a556bc7e24d8e9ced6e12efa179b49a9ee283e07389f9bde8626db03d197b1
468: identical worlds? True
469: ```
470: Gate D: PASS. (sig differs from HEAD because the edit changes pre-gen
471: outcomes; both post-edit runs still match each other.)
472: 
473: ### Gate E — P9 rerun post-edit
474: 
475: Expected: same pass/fail counts, or report each change.
476: Observed post-edit:
477: ```
478: rc = 0  (same as HEAD)
479: Total fights:    220  (same)
480: Errors caught:   0    (same)
481: Finish rate:     26/220 = 11.8%   (HEAD: 19/220 = 8.6%)
482: Decision rate:   185/220 = 84.1%  (HEAD: 193/220 = 87.7%)
483: Draws:           9/220 = 4.1%     (HEAD: 8/220 = 3.6%)
484: Method distribution:
485:   KO:     0  (  0.0%)   (HEAD:  0)
486:   TKO:   15  (  6.8%)   (HEAD: 12)
487:   SUB:   11  (  5.0%)   (HEAD:  7)
488:   DEC:  185  ( 84.1%)   (HEAD: 193)
489: 
490: Style-detection table changes (per-builder detected string):
491:   make_muay_thai       MUAY_THAI    detected change: 'striker'   -> 'muay_thai'
492:   make_clinch_fighter  CLINCH_FIGHTER detected change: 'wrestler' -> 'clinch_fighter'
493:   (other 9 builders: detected string unchanged)
494: ```
495: Gate E: PASS (same error count 0/0, same 220/220 run count). Behavioral
496: deltas reported above.
497: 
498: ## STEP 4 — pre-gen, same 10 seeds, three arms (HEAD | edited | weight_off)
499: 
500: Seeds: 20261113..20261122 (ten consecutive seeds).

--- READ 3. July ORACLE-BRIDGE1 uuid4 patch ---
Script: outputs/oracle_bridge_determinism_probe2.py
sha256:
53f811e6480ed380554343c147cfccc7491c007bd445c7b01f9dc215dc913b14  outputs/oracle_bridge_determinism_probe2.py

Patch lines (:28-34):
28:     # Monkey-patch uuid.uuid4 BEFORE any imports use it
29:     import uuid as _uuid
30:     _det_rng = random.Random(SEED)
31:     def seeded_uuid4():
32:         # Build a UUID from seeded random bytes
33:         return _uuid.UUID(int=_det_rng.getrandbits(128))
34:     _uuid.uuid4 = seeded_uuid4

=== HARNESS ===
paired worker: /tmp/live_cut_worker_paired.py
sha256: 8a03e3c2c993c7d25ed1190e0937a1d8dd4499d596173db002c84e4dd174206e

--- diff /tmp/live_onejudge_worker.py vs /tmp/live_cut_worker_paired.py ---
--- /tmp/live_onejudge_worker.py	2026-11-14 10:17:54
+++ /tmp/live_cut_worker_paired.py	2026-11-16 06:21:30
@@ -9,7 +9,15 @@
 SEED = int(os.environ["LOJ_SEED"])
 WORLD_LABEL = os.environ.get("LOJ_LABEL", "w?")
 
-REPO = "/tmp/cd-exp-live-onejudge"
+# PAIRED HARNESS: monkey-patch uuid.uuid4 BEFORE any game import.
+# Pattern from outputs/oracle_bridge_determinism_probe2.py :28-34.
+import uuid as _uuid
+_det_rng = random.Random(SEED)
+def _paired_uuid4():
+    return _uuid.UUID(int=_det_rng.getrandbits(128))
+_uuid.uuid4 = _paired_uuid4
+
+REPO = os.environ["LOJ_REPO"]
 WEB = f"{REPO}/cage_dynasty_web"
 for p in (f"{REPO}/simulation", f"{REPO}/narrative", f"{REPO}/systems", WEB):
     if os.path.isdir(p) and p not in sys.path:

=== C4 ARM ===
--- git -C /tmp/cd-exp-cut-c4 diff cage_dynasty_web/fight_engine.py ---
diff --git a/cage_dynasty_web/fight_engine.py b/cage_dynasty_web/fight_engine.py
index ebd4db0..c632a08 100644
--- a/cage_dynasty_web/fight_engine.py
+++ b/cage_dynasty_web/fight_engine.py
@@ -1810,6 +1810,69 @@ def get_available_grappling_actions(
 # label-string -> count, for labels not in the hint map).
 _STYLE1_LABEL_COUNTER = {"missing": 0, "unmapped": {}}
 
+# CUT-SANDBOX INSTRUMENT (identical across c0/c1/c2/c3; never draws from
+# RNG; never changes any value). Counters keyed by resolved _style_key
+# and gate outcome.
+_CUT_COUNTERS = {
+    "lookups": {},            # style_key -> count (at _STYLE_WEIGHTS.get)
+    "default_fallbacks": {},  # raw style_key (that fell to DEFAULT) -> count
+    "gate_passed": 0,         # submissions and fighter_attrs.submissions >= threshold
+    "gate_failed": 0,
+    "floor_binds": 0,         # gate passed AND sub_weight was 0 pre-max(1,...)
+    "subs_hist": {"<60": 0, "60-69": 0, "70-79": 0, "80+": 0},
+    # C4 ONLY: per-style gate-passed and "would-have-bound" counters.
+    "c4_gate_passed_by_style": {},
+    "c4_wouldhave_bound_by_style": {},
+}
+
+def _cut_counters_read():
+    return {
+        "lookups": dict(_CUT_COUNTERS["lookups"]),
+        "default_fallbacks": dict(_CUT_COUNTERS["default_fallbacks"]),
+        "gate_passed": _CUT_COUNTERS["gate_passed"],
+        "gate_failed": _CUT_COUNTERS["gate_failed"],
+        "floor_binds": _CUT_COUNTERS["floor_binds"],
+        "subs_hist": dict(_CUT_COUNTERS["subs_hist"]),
+    }
+
+def _cut_counters_reset():
+    _CUT_COUNTERS["lookups"] = {}
+    _CUT_COUNTERS["default_fallbacks"] = {}
+    _CUT_COUNTERS["gate_passed"] = 0
+    _CUT_COUNTERS["gate_failed"] = 0
+    _CUT_COUNTERS["floor_binds"] = 0
+    _CUT_COUNTERS["subs_hist"] = {"<60": 0, "60-69": 0, "70-79": 0, "80+": 0}
+
+# CUT-SANDBOX: module-level table snapshot filled lazily on the first
+# select_action call per module object.
+_CUT_TABLE = {
+    "table_captured": False,
+    "WRESTLER_sub": None,
+    "GROUND_AND_POUND_sub": None,
+    "CLINCH_FIGHTER_sub": None,
+    "BJJ_SPECIALIST_sub": None,
+    "threshold_bjj_sambo": None,  # 45 branch
+    "threshold_other": None,       # else branch (60 or 70 per arm)
+}
+
+def _cut_table_read():
+    return dict(_CUT_TABLE)
+
+# CUT-SANDBOX: atexit emission so the worker's subprocess prints the
+# counter per module-object before exit. Tag includes the module's own
+# __name__ so simulation.fight_engine vs fight_engine can be distinguished.
+import atexit as _cut_atexit
+import json as _cut_json
+def _cut_atexit_emit(_mod_name=__name__):
+    _payload = {
+        "module_name": _mod_name,
+        "fe_file": __file__,
+        "table_snapshot": _cut_table_read(),
+        "counters": _cut_counters_read(),
+    }
+    print(f"===CUT_COUNTERS===  {_cut_json.dumps(_payload, default=str)}", flush=True)
+_cut_atexit.register(_cut_atexit_emit)
+
 def _style1_label_counter_read():
     """Return a snapshot of the one-judge label-resolution counter."""
     return {"missing": _STYLE1_LABEL_COUNTER["missing"],
@@ -2484,6 +2547,20 @@ def select_action(
     }
     _style_key = _STYLE_ALIASES.get(
         _style_key, _style_key.replace(' ', '_'))
+    # CUT-SANDBOX INSTRUMENT: on the first call per module, capture the
+    # four submission-column values from the just-built _STYLE_WEIGHTS.
+    if not _CUT_TABLE["table_captured"]:
+        _CUT_TABLE["WRESTLER_sub"] = _STYLE_WEIGHTS["WRESTLER"]["submission"]
+        _CUT_TABLE["GROUND_AND_POUND_sub"] = _STYLE_WEIGHTS["GROUND_AND_POUND"]["submission"]
+        _CUT_TABLE["CLINCH_FIGHTER_sub"] = _STYLE_WEIGHTS["CLINCH_FIGHTER"]["submission"]
+        _CUT_TABLE["BJJ_SPECIALIST_sub"] = _STYLE_WEIGHTS["BJJ_SPECIALIST"]["submission"]
+        _CUT_TABLE["table_captured"] = True
+    # CUT-SANDBOX INSTRUMENT: tally lookups + default fallbacks (pre-read).
+    _CUT_COUNTERS["lookups"][_style_key] = \
+        _CUT_COUNTERS["lookups"].get(_style_key, 0) + 1
+    if _style_key not in _STYLE_WEIGHTS:
+        _CUT_COUNTERS["default_fallbacks"][_style_key] = \
+            _CUT_COUNTERS["default_fallbacks"].get(_style_key, 0) + 1
     _sw = _STYLE_WEIGHTS.get(_style_key,
         {"strike":1.0,"grapple":1.0,"submission":1.0})
     strike_weight = int(strike_weight * _sw["strike"])
@@ -2602,9 +2679,38 @@ def select_action(
     strike_weight = max(5, strike_weight) if strikes else 0
     # Sub gate: BJJ/Sambo can attempt subs at 45+, everyone else at 60+
     _sub_threshold = 45 if my_style in ("bjj", "sambo") else 60
+    # CUT-SANDBOX INSTRUMENT: capture the two threshold branch values
+    # as they are encountered (once each per module).
+    if my_style in ("bjj", "sambo"):
+        if _CUT_TABLE["threshold_bjj_sambo"] is None:
+            _CUT_TABLE["threshold_bjj_sambo"] = _sub_threshold
+    else:
+        if _CUT_TABLE["threshold_other"] is None:
+            _CUT_TABLE["threshold_other"] = _sub_threshold
+    # CUT-SANDBOX INSTRUMENT: histogram at the gate, pass/fail + floor_binds.
+    _cut_subs_val = fighter_attrs.submissions
+    if _cut_subs_val < 60:
+        _CUT_COUNTERS["subs_hist"]["<60"] += 1
+    elif _cut_subs_val < 70:
+        _CUT_COUNTERS["subs_hist"]["60-69"] += 1
+    elif _cut_subs_val < 80:
+        _CUT_COUNTERS["subs_hist"]["70-79"] += 1
+    else:
+        _CUT_COUNTERS["subs_hist"]["80+"] += 1
     if submissions and fighter_attrs.submissions >= _sub_threshold:
-        sub_weight = max(1, sub_weight)
+        _CUT_COUNTERS["gate_passed"] += 1
+        _CUT_COUNTERS["c4_gate_passed_by_style"][_style_key] = \
+            _CUT_COUNTERS["c4_gate_passed_by_style"].get(_style_key, 0) + 1
+        if sub_weight == 0:
+            _CUT_COUNTERS["floor_binds"] += 1
+            _CUT_COUNTERS["c4_wouldhave_bound_by_style"][_style_key] = \
+                _CUT_COUNTERS["c4_wouldhave_bound_by_style"].get(_style_key, 0) + 1
+        # C4 CHANGE: floor only applies to BJJ_SPECIALIST; others keep
+        # their computed sub_weight (including 0).
+        if _style_key == "BJJ_SPECIALIST":
+            sub_weight = max(1, sub_weight)
     else:
+        _CUT_COUNTERS["gate_failed"] += 1
         sub_weight = 0
     grapple_weight = max(5, grapple_weight) if grappling else 0
     

=== C4 fixed-pop s1 check ===
C4 record sha: 5bc04cca19ae6a8e61efeec37b1b1086f8b06c0b3b2175b2f42eeb7513c9ac4e  sim=1080  SUB=223
Filed L1_s1:   784c5d38210cfd33b125f6009f39700912287a7d025231226378f36d316f796e
DIFFERS: True

=== GATE P1 — paired C0 seed 20261114, two fresh processes ===
p1a rows sha: a83bfaae2f82dad72d73b7a57dc463e88c7a36f9deaf514e242d7e0e178a4d73  fights=402  SUB=89
p1b rows sha: a83bfaae2f82dad72d73b7a57dc463e88c7a36f9deaf514e242d7e0e178a4d73  fights=402  SUB=89
EQUAL: True

=== GATE P2 — week-0 roster equality across arms, row-list inequality ===

Roster shas (name + label + 18 engine stats, sorted by name):
  C0 sha: 45c8502d9df070b9448b7b35691a69cfbb36032022efd9c257a5b661c54f4451
  C2 sha: 6d4f4be7ea2b7fa091be4495e80e13c76bca2942d8388d388432e072066bbb6c
  roster EQUAL: False

Diagnosis of roster divergence under the paired uuid4 harness:
  Both arms post-new_game: n=294 fighters
  Name set intersection: 293 common; 1 only in C0 (Eric Collins); 1 only in C2 (Zabit Ankalaev)
  On the 293 common names: 33 fighters have differing stats; 0 fighters have differing labels
  First stats-differ example (Alexei Ivanov, label Wrestler same in both):
    C0 boxing=50 strength=69 cardio=78 recovery=57 submissions=71
    C2 boxing=49 strength=68 cardio=77 recovery=59 submissions=70
  Small per-stat deltas on 33 fighters are consistent with divergent in-pre-gen
  attribute changes (training-gain / aging-decay / injury-recovery); the 1-name
  swap is consistent with a divergent pre-gen retirement (C0 retires a fighter
  that C2 does not, pulling a different amateur to promote). The engine
  difference (c0=baseline vs c2=WRESTLER 0.3 / G&P 0.3 / CF 0.4) changes
  select_action's random.random() consumption per fight; pre-gen fight outcomes
  differ; retirement and training events during pre-gen differ. Under the uuid4
  patch, fighter_id generation is driven by _det_rng (seeded random.Random);
  _det_rng is consumed each time new_game or pre-gen creates a fighter or
  fight_id. Divergent pre-gen promotion counts consume _det_rng at different
  points, producing different fighter_ids for subsequent fighters.

C0 row-list sha (p1a): a83bfaae2f82dad72d73b7a57dc463e88c7a36f9deaf514e242d7e0e178a4d73  fights=402  SUB=89
C2 row-list sha (p2_c2): 1394a1f8915aa12cb9e3da9e2a417ce8bceeb9f94509c2b5758a0c02abec40d5  fights=408  SUB=83
rows DIFFERENT (as expected if the edit applies to anything).

STOP per spec: 'Roster differs -> STOP and report where generation diverges.'

## Embed 3/7 — outputs/cut_round5_screen_2026-11-16.txt
sha256 a14cd3d22313f6f79caaf8fbacff2367bceda47b03c8ed07a735ed46ff862026

=== CUT SANDBOX round-5 screen ===
arms: S0 C7 C7s C7t C5s
records carry fighter_submissions: True

=== SUB per seed, pooled, minus S0, pooled cut as % of S0's 1147 ===
  arm      s1     s2     s3     s4     s5   pool   dvsS0   cut%1147
  S0      244    227    233    227    216   1147      +0      0.00%
  C7      194    184    191    167    174    910    -237     20.66%
  C7s     202    188    201    175    177    943    -204     17.79%
  C7t     204    194    203    179    179    959    -188     16.39%
  C5s     180    179    191    159    167    876    -271     23.63%

--- arm S0, pooled 5 seeds, per winner label ---
  label                   wins    wsub     app    w<80   w>=80   ws<80  ws>=80
  BJJ Specialist           673     494    1055     320     353     192     302
  Wrestler                 932     343    1585     663     269     135     208
  Ground & Pound          1012     186    1590     891     121     125      61
  Clinch Fighter           290      22     725     285       5      22       0
  Muay Thai                392      18    1035     256     136       8      10
  Striker                  235       8     705     214      21       5       3
  Counter Striker          582      30    1405     369     213       8      22
  Pressure Fighter         377      14     800     267     110       6       8
  Sprawl & Brawl           600      15    1015     542      58      11       4
  Point Fighter             68       0     220      68       0       0       0
  Balanced                 166      17     665     166       0      17       0

--- arm C7, pooled 5 seeds, per winner label ---
  label                   wins    wsub     app    w<80   w>=80   ws<80  ws>=80
  BJJ Specialist           676     493    1055     321     355     193     300
  Wrestler                 922     236    1585     655     267      63     173
  Ground & Pound          1010     108    1590     890     120      68      40
  Clinch Fighter           292      12     725     287       5      12       0
  Muay Thai                393      12    1035     258     135       5       7
  Striker                  235       4     705     214      21       1       3
  Counter Striker          588      22    1405     376     212       4      18
  Pressure Fighter         377       9     800     267     110       3       6
  Sprawl & Brawl           598       6    1015     541      57       5       1
  Point Fighter             69       0     220      69       0       0       0
  Balanced                 163       8     665     163       0       8       0

--- arm C7s, pooled 5 seeds, per winner label ---
  label                   wins    wsub     app    w<80   w>=80   ws<80  ws>=80
  BJJ Specialist           675     493    1055     321     354     193     300
  Wrestler                 924     249    1585     654     270      63     186
  Ground & Pound          1010     116    1590     890     120      68      48
  Clinch Fighter           292      12     725     287       5      12       0
  Muay Thai                394      15    1035     258     136       5      10
  Striker                  235       5     705     214      21       1       4
  Counter Striker          587      25    1405     376     211       4      21
  Pressure Fighter         375      11     800     265     110       3       8
  Sprawl & Brawl           599       9    1015     541      58       5       4
  Point Fighter             69       0     220      69       0       0       0
  Balanced                 163       8     665     163       0       8       0

--- arm C7t, pooled 5 seeds, per winner label ---
  label                   wins    wsub     app    w<80   w>=80   ws<80  ws>=80
  BJJ Specialist           675     494    1055     321     354     193     301
  Wrestler                 925     251    1585     655     270      65     186
  Ground & Pound          1011     125    1590     891     120      77      48
  Clinch Fighter           291      14     725     286       5      14       0
  Muay Thai                394      15    1035     258     136       5      10
  Striker                  235       5     705     214      21       1       4
  Counter Striker          587      26    1405     375     212       5      21
  Pressure Fighter         375      12     800     265     110       4       8
  Sprawl & Brawl           599       9    1015     541      58       5       4
  Point Fighter             69       0     220      69       0       0       0
  Balanced                 163       8     665     163       0       8       0

--- arm C5s, pooled 5 seeds, per winner label ---
  label                   wins    wsub     app    w<80   w>=80   ws<80  ws>=80
  BJJ Specialist           677     495    1055     321     356     193     302
  Wrestler                 925     207    1585     656     269      50     157
  Ground & Pound          1008      90    1590     888     120      49      41
  Clinch Fighter           292      11     725     287       5      11       0
  Muay Thai                394      15    1035     258     136       5      10
  Striker                  235       5     705     214      21       1       4
  Counter Striker          585      25    1405     374     211       4      21
  Pressure Fighter         375      11     800     265     110       3       8
  Sprawl & Brawl           600       9    1015     542      58       5       4
  Point Fighter             69       0     220      69       0       0       0
  Balanced                 163       8     665     163       0       8       0

=== LIVE FINALISTS ===
pool cut% of 1147:
  C7s: 17.79% (pool SUB 943, delta -204)
  C7t: 16.39% (pool SUB 959, delta -188)
  C5s: 23.63% (pool SUB 876, delta -271)
  at most 19%: {'C7s': 17.785527462946817, 'C7t': 16.390584132519617}
  above 19%:   {'C5s': 23.626852659110725}
  F1 = C7s (cut 17.79%, largest at-most-19%)
  F2 = C5s (cut 23.63%, smallest above-19%)

## Embed 4/7 — outputs/cut_paired_2026-11-16.txt
sha256 51d9ba04dbffb99f6772e710ccd16b7632e1e2c29cad25bc1df568a90beacde6

=== CUT SANDBOX round-5 LIVE paired ===
arms: C0 C0r F1 F2; F1=C7s (0.45/0.4/0.5 + skill_floor 80); F2=C5s (0.3/0.3/0.4 + skill_floor 80); C0r=C0 tree with LOJ_LIVE_RESEED=1

--- arm C0 ---
  world  seed           n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%   t_live
  w1    20261114     402    89    0   166   142     5      0   22.14    977.2
  w2    20261115     402    92    1   152   153     4      0   22.89   1514.7
  w3    20261116     402    95    2   168   132     5      0   23.63    900.1
  pool              1206   276    3   486   427    14      0   22.89   3392.0

--- arm C0r ---
  world  seed           n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%   t_live
  w1    20261114     402    92    2   154   150     4      0   22.89    886.7
  w2    20261115     402    90    4   149   150     9      0   22.39    649.6
  w3    20261116     402    97    2   170   129     4      0   24.13    566.4
  pool              1206   279    8   473   429    17      0   23.13   2102.7

--- arm F1 ---
  world  seed           n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%   t_live
  w1    20261114     402    75    2   159   166     0      0   18.66   1521.8
  w2    20261115     409    75    3   176   148     7      0   18.34   1052.3
  w3    20261116     410    82    7   157   155     9      0   20.00   1037.8
  pool              1221   232   12   492   469    16      0   19.00   3611.9

--- arm F2 ---
  world  seed           n   SUB   KO   TKO   DEC  DRAW  OTHER    SUB%   t_live
  w1    20261114     401    67    5   170   155     4      0   16.71   1509.4
  w2    20261115     402    81    3   163   149     6      0   20.15    871.2
  w3    20261116     402    84    3   165   146     4      0   20.90    993.9
  pool              1205   232   11   498   450    14      0   19.25   3374.5

--- arm C0, pooled 3 worlds, per winner label ---
  label                  wins   wsub    app  win_rate   wsub%
  BJJ Specialist          177    128    331     53.47   72.32
  Wrestler                152     63    298     51.01   41.45
  Ground & Pound          255     47    455     56.04   18.43
  Clinch Fighter          116     17    222     52.25   14.66
  Muay Thai                95      7    195     48.72    7.37
  Striker                  36      1     92     39.13    2.78
  Counter Striker         159      5    313     50.80    3.14
  Pressure Fighter         65      3    149     43.62    4.62
  Sprawl & Brawl           65      1    132     49.24    1.54
  Point Fighter            25      0     49     51.02    0.00
  Balanced                 47      4    162     29.01    8.51

--- arm C0r, pooled 3 worlds, per winner label ---
  label                  wins   wsub    app  win_rate   wsub%
  BJJ Specialist          182    135    344     52.91   74.18
  Wrestler                164     65    310     52.90   39.63
  Ground & Pound          245     43    437     56.06   17.55
  Clinch Fighter          114     15    227     50.22   13.16
  Muay Thai                96     10    191     50.26   10.42
  Striker                  40      0     98     40.82    0.00
  Counter Striker         148      8    301     49.17    5.41
  Pressure Fighter         71      1    164     43.29    1.41
  Sprawl & Brawl           66      1    135     48.89    1.52
  Point Fighter            23      0     46     50.00    0.00
  Balanced                 40      1    142     28.17    2.50

--- arm F1, pooled 3 worlds, per winner label ---
  label                  wins   wsub    app  win_rate   wsub%
  BJJ Specialist          173    136    359     48.19   78.61
  Wrestler                146     41    299     48.83   28.08
  Ground & Pound          254     28    451     56.32   11.02
  Clinch Fighter          114     16    234     48.72   14.04
  Muay Thai                93      3    190     48.95    3.23
  Striker                  50      1     97     51.55    2.00
  Counter Striker         160      3    316     50.63    1.88
  Pressure Fighter         69      0    150     46.00    0.00
  Sprawl & Brawl           64      0    135     47.41    0.00
  Point Fighter            26      0     52     50.00    0.00
  Balanced                 56      4    143     39.16    7.14

--- arm F2, pooled 3 worlds, per winner label ---
  label                  wins   wsub    app  win_rate   wsub%
  BJJ Specialist          189    142    348     54.31   75.13
  Wrestler                163     35    310     52.58   21.47
  Ground & Pound          248     29    439     56.49   11.69
  Clinch Fighter           90      4    201     44.78    4.44
  Muay Thai               106      8    203     52.22    7.55
  Striker                  41      1    100     41.00    2.44
  Counter Striker         143      5    312     45.83    3.50
  Pressure Fighter         69      4    160     43.12    5.80
  Sprawl & Brawl           72      0    138     52.17    0.00
  Point Fighter            24      1     42     57.14    4.17
  Balanced                 46      3    143     32.17    6.52

=== Per-arm SUB count minus C0 (per seed + pooled) ===
  arm      w1     w2     w3   pool
  C0       +0     +0     +0     +0
  C0r      +3     -2     +2     +3
  F1      -14    -17    -13    -44
  F2      -22    -11    -11    -44

=== Per-arm SUB% minus C0's (per seed + pooled, percentage points) ===
  arm       w1      w2      w3    pool
  C0     +0.00   +0.00   +0.00   +0.00
  C0r    +0.75   -0.50   +0.50   +0.25
  F1     -3.48   -4.55   -3.63   -3.88
  F2     -5.43   -2.74   -2.74   -3.63


--- label: Wrestler — wins-by-SUB and win_rate (as % of appearances) deltas vs C0 ---
  wins_by_SUB count minus C0:
    arm      w1     w2     w3   pool
    C0       +0     +0     +0     +0
    C0r      +4     -1     -1     +2
    F1       -9     -9     -4    -22
    F2      -10     -8    -10    -28
  win_rate (wins / appearances) in percentage points minus C0:
    arm       w1      w2      w3    pool
    C0     +0.00   +0.00   +0.00   +0.00
    C0r    +5.73   +3.81   -3.72   +1.90
    F1     -0.26   -4.23   -2.78   -2.18
    F2     +5.73   +4.37   -5.09   +1.57

--- label: Ground & Pound — wins-by-SUB and win_rate (as % of appearances) deltas vs C0 ---
  wins_by_SUB count minus C0:
    arm      w1     w2     w3   pool
    C0       +0     +0     +0     +0
    C0r      -1     -8     +5     -4
    F1       -8     -8     -3    -19
    F2       -8    -11     +1    -18
  win_rate (wins / appearances) in percentage points minus C0:
    arm       w1      w2      w3    pool
    C0     +0.00   +0.00   +0.00   +0.00
    C0r    -1.15   +4.16   -1.87   +0.02
    F1     +2.73   -2.49   -0.38   +0.28
    F2     +3.95   -0.59   -2.93   +0.45

--- label: Clinch Fighter — wins-by-SUB and win_rate (as % of appearances) deltas vs C0 ---
  wins_by_SUB count minus C0:
    arm      w1     w2     w3   pool
    C0       +0     +0     +0     +0
    C0r      -3     +2     -1     -2
    F1       -2     +0     +1     -1
    F2       -6     -2     -5    -13
  win_rate (wins / appearances) in percentage points minus C0:
    arm       w1      w2      w3    pool
    C0     +0.00   +0.00   +0.00   +0.00
    C0r    -4.14   +1.01   -4.85   -2.03
    F1     -4.98   -6.32   +0.02   -3.53
    F2    -17.47   -3.95   -2.54   -7.48

--- label: BJJ Specialist — wins-by-SUB and win_rate (as % of appearances) deltas vs C0 ---
  wins_by_SUB count minus C0:
    arm      w1     w2     w3   pool
    C0       +0     +0     +0     +0
    C0r      +4     +5     -2     +7
    F1       +6     +6     -4     +8
    F2       +3    +12     -1    +14
  win_rate (wins / appearances) in percentage points minus C0:
    arm       w1      w2      w3    pool
    C0     +0.00   +0.00   +0.00   +0.00
    C0r    -1.42   -2.56   +2.40   -0.57
    F1     -1.02   -6.95   -7.21   -5.28
    F2    -10.48   +3.16   +9.73   +0.84

## Embed 5/7 — outputs/cut_gate0_2026-11-16.txt
sha256 2cd823ac3ca885051024d2a69b88a4f83ccce46eb11b1070f33b6a8e3d252a9d

=== GATE 0 (read-only) ===

=== 1. Round-5 pre-generation ===CUT_COUNTERS=== for C0 and C0r per seed + byte-equal check ===
  (Note on source: each worker atexit emits one ===CUT_COUNTERS=== per fe module object.
   The 'simulation.fight_engine' row reflects pre-generation calls; the bare 'fight_engine'
   row reflects live. Both are shown per seed.)

--- C0 seed-slot s1 file /tmp/cut_paired_C0_s1_stdout.txt ---
  (file missing)

--- C0 seed-slot s2 file /tmp/cut_paired_C0_s2_stdout.txt ---
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"STRIKER": 109121, "GROUND_AND_POUND": 1313491, "SPRAWL_AND_BRAWL": 372160, "PRESSURE_FIGHTER": 378074, "COUNTER_STRIKER": 555049, "MUAY_THAI": 542539, "BJJ_SPECIALIST": 921088, "CLINCH_FIGHTER": 772539, "WRESTLER": 566468, "BALANCED": 392335, "POINT_FIGHTER": 12579}, "default_fallbacks": {}, "gate_passed": 1903690, "gate_failed": 4031753, "floor_binds": 1653981, "subs_hist": {"<60": 2340339, "60-69": 1495461, "70-79": 1372758, "80+": 726885}}}
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"WRESTLER": 8006, "STRIKER": 3873, "MUAY_THAI": 10210, "GROUND_AND_POUND": 19289, "COUNTER_STRIKER": 10520, "CLINCH_FIGHTER": 11451, "BJJ_SPECIALIST": 10388, "PRESSURE_FIGHTER": 8112, "BALANCED": 8234, "SPRAWL_AND_BRAWL": 6851, "POINT_FIGHTER": 553}, "default_fallbacks": {}, "gate_passed": 25856, "gate_failed": 71631, "floor_binds": 22554, "subs_hist": {"<60": 45908, "60-69": 24927, "70-79": 17409, "80+": 9243}}}

--- C0 seed-slot s3 file /tmp/cut_paired_C0_s3_stdout.txt ---
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"BJJ_SPECIALIST": 803730, "GROUND_AND_POUND": 903994, "WRESTLER": 851449, "CLINCH_FIGHTER": 334345, "STRIKER": 176627, "MUAY_THAI": 248418, "SPRAWL_AND_BRAWL": 151902, "POINT_FIGHTER": 261265, "COUNTER_STRIKER": 730180, "PRESSURE_FIGHTER": 269324, "BALANCED": 502772}, "default_fallbacks": {}, "gate_passed": 1707828, "gate_failed": 3526178, "floor_binds": 1481799, "subs_hist": {"<60": 1997086, "60-69": 1601861, "70-79": 563894, "80+": 1071165}}}
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"BJJ_SPECIALIST": 10268, "COUNTER_STRIKER": 14518, "GROUND_AND_POUND": 16533, "CLINCH_FIGHTER": 8456, "WRESTLER": 15004, "STRIKER": 4935, "MUAY_THAI": 5076, "POINT_FIGHTER": 2714, "BALANCED": 7673, "PRESSURE_FIGHTER": 4399, "SPRAWL_AND_BRAWL": 7218}, "default_fallbacks": {}, "gate_passed": 24562, "gate_failed": 72232, "floor_binds": 21104, "subs_hist": {"<60": 51064, "60-69": 18729, "70-79": 12642, "80+": 14359}}}

--- C0r seed-slot s1 file /tmp/cut_paired_C0r_s1_stdout.txt ---
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"PRESSURE_FIGHTER": 380971, "GROUND_AND_POUND": 1276015, "WRESTLER": 886231, "BJJ_SPECIALIST": 559195, "COUNTER_STRIKER": 378501, "CLINCH_FIGHTER": 491573, "POINT_FIGHTER": 190410, "STRIKER": 131599, "MUAY_THAI": 136921, "BALANCED": 249246, "SPRAWL_AND_BRAWL": 285025}, "default_fallbacks": {}, "gate_passed": 1505832, "gate_failed": 3459855, "floor_binds": 1287685, "subs_hist": {"<60": 2187043, "60-69": 1042008, "70-79": 1018111, "80+": 718525}}}
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"GROUND_AND_POUND": 21166, "COUNTER_STRIKER": 10453, "BJJ_SPECIALIST": 10210, "POINT_FIGHTER": 2786, "CLINCH_FIGHTER": 8033, "WRESTLER": 16098, "PRESSURE_FIGHTER": 5097, "SPRAWL_AND_BRAWL": 6746, "BALANCED": 6617, "MUAY_THAI": 5734, "STRIKER": 5585}, "default_fallbacks": {}, "gate_passed": 22536, "gate_failed": 75989, "floor_binds": 19138, "subs_hist": {"<60": 56504, "60-69": 18574, "70-79": 14323, "80+": 9124}}}

--- C0r seed-slot s2 file /tmp/cut_paired_C0r_s2_stdout.txt ---
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"STRIKER": 141227, "GROUND_AND_POUND": 1111940, "SPRAWL_AND_BRAWL": 327604, "PRESSURE_FIGHTER": 389270, "COUNTER_STRIKER": 610916, "MUAY_THAI": 626346, "BJJ_SPECIALIST": 736673, "CLINCH_FIGHTER": 663874, "WRESTLER": 498967, "BALANCED": 353182, "POINT_FIGHTER": 9925}, "default_fallbacks": {}, "gate_passed": 1711986, "gate_failed": 3757938, "floor_binds": 1485773, "subs_hist": {"<60": 2149657, "60-69": 1653542, "70-79": 1165126, "80+": 501599}}}
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"WRESTLER": 8006, "STRIKER": 3873, "MUAY_THAI": 10210, "GROUND_AND_POUND": 19289, "COUNTER_STRIKER": 10520, "CLINCH_FIGHTER": 11451, "BJJ_SPECIALIST": 10388, "PRESSURE_FIGHTER": 8112, "BALANCED": 8234, "SPRAWL_AND_BRAWL": 6851, "POINT_FIGHTER": 553}, "default_fallbacks": {}, "gate_passed": 25856, "gate_failed": 71631, "floor_binds": 22554, "subs_hist": {"<60": 45908, "60-69": 24927, "70-79": 17409, "80+": 9243}}}

--- C0r seed-slot s3 file /tmp/cut_paired_C0r_s3_stdout.txt ---
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"BJJ_SPECIALIST": 779929, "GROUND_AND_POUND": 976593, "WRESTLER": 769228, "CLINCH_FIGHTER": 408985, "STRIKER": 218337, "MUAY_THAI": 206224, "SPRAWL_AND_BRAWL": 289424, "POINT_FIGHTER": 169590, "COUNTER_STRIKER": 794764, "PRESSURE_FIGHTER": 214694, "BALANCED": 295787}, "default_fallbacks": {}, "gate_passed": 1652652, "gate_failed": 3470903, "floor_binds": 1423100, "subs_hist": {"<60": 1936056, "60-69": 1105993, "70-79": 948895, "80+": 1132611}}}
===CUT_COUNTERS===  {"module_name": "fight_engine", "fe_file": "/tmp/cd-exp-cut-c0/cage_dynasty_web/fight_engine.py", "table_snapshot": {"table_captured": true, "WRESTLER_sub": 0.9, "GROUND_AND_POUND_sub": 0.6, "CLINCH_FIGHTER_sub": 0.7, "BJJ_SPECIALIST_sub": 2.0, "threshold_bjj_sambo": 45, "threshold_other": 60}, "counters": {"lookups": {"BJJ_SPECIALIST": 10268, "COUNTER_STRIKER": 14518, "GROUND_AND_POUND": 16533, "CLINCH_FIGHTER": 8456, "WRESTLER": 15004, "STRIKER": 4935, "MUAY_THAI": 5076, "POINT_FIGHTER": 2714, "BALANCED": 7673, "PRESSURE_FIGHTER": 4399, "SPRAWL_AND_BRAWL": 7218}, "default_fallbacks": {}, "gate_passed": 24562, "gate_failed": 72232, "floor_binds": 21104, "subs_hist": {"<60": 51064, "60-69": 18729, "70-79": 12642, "80+": 14359}}}

--- byte-equality check: C0 pre-gen vs C0r pre-gen per seed (simulation.fight_engine row only) ---
ugrep: warning: /tmp/cut_paired_C0_s1_stdout.txt: No such file or directory
ugrep: warning: /tmp/cut_paired_C0_s1_stdout.txt: No such file or directory

s1 simulation.fight_engine (pre-gen):
  C0 : 
  C0r: 
  byte-equal (pre-gen): True
s1 fight_engine (live, bare):
  byte-equal (bare live): False

s2 simulation.fight_engine (pre-gen):
  C0 : 
  C0r: 
  byte-equal (pre-gen): True
s2 fight_engine (live, bare):
  byte-equal (bare live): False

s3 simulation.fight_engine (pre-gen):
  C0 : 
  C0r: 
  byte-equal (pre-gen): True
s3 fight_engine (live, bare):
  byte-equal (bare live): False

--- v2 worker diff in full (vs /tmp/live_cut_worker_paired.py) ---
--- /tmp/live_cut_worker_paired.py	2026-11-16 06:21:30
+++ /tmp/live_cut_worker_paired_v2.py	2026-11-16 18:16:24
@@ -139,6 +139,12 @@
 bridge._user_id = f"loj_{WORLD_LABEL}"
 assert bridge.new_game("Probe Camp","Las Vegas, NV","GARAGE",COACH,fd)
 
+# PAIRED v2: optional live reseed, fired exactly once, after new_game
+# returns and before the first live week. No other behavior change.
+_LIVE_RESEED = os.environ.get("LOJ_LIVE_RESEED", "")
+if _LIVE_RESEED:
+    random.seed(SEED * 1000 + int(_LIVE_RESEED))
+
 # Re-wrap (new modules may have appeared during new_game)
 wrap_all_fe()
 

=== 2. Every reader of the select_action sub gate and _STYLE_WEIGHTS in cage_dynasty_web/ ===

--- readers of _STYLE_WEIGHTS (grep -n) ---
cage_dynasty_web/fight_engine.py:2436:    _STYLE_WEIGHTS = {
cage_dynasty_web/fight_engine.py:2487:    _sw = _STYLE_WEIGHTS.get(_style_key,
cage_dynasty_web/fight_engine.py:2494:    # Aggression multiplies AFTER _STYLE_WEIGHTS so it composes with
cage_dynasty_web/styles.py:306:COUNTRY_STYLE_WEIGHTS: Dict[str, Dict[FightingStyle, float]] = {
cage_dynasty_web/styles.py:365:DEFAULT_STYLE_WEIGHTS: Dict[FightingStyle, float] = {
cage_dynasty_web/styles.py:417:    if country and country in COUNTRY_STYLE_WEIGHTS and random.random() < 0.05:
cage_dynasty_web/styles.py:419:        country_weights = COUNTRY_STYLE_WEIGHTS[country]
cage_dynasty_web/styles.py:446:    if country and country in COUNTRY_STYLE_WEIGHTS:
cage_dynasty_web/styles.py:447:        weights = dict(COUNTRY_STYLE_WEIGHTS[country])
cage_dynasty_web/styles.py:449:        weights = dict(DEFAULT_STYLE_WEIGHTS)
cage_dynasty_web/styles.py:768:    "COUNTRY_STYLE_WEIGHTS", "DEFAULT_STYLE_WEIGHTS", "CAMP_STYLE_PRESETS",
cage_dynasty_web/game_bridge.py:2464:            _STYLE_WEIGHTS = [14, 8, 10, 9, 12, 9, 10, 8, 6, 7, 7]
cage_dynasty_web/game_bridge.py:2490:                        _style = _srnd.choices(_STYLE_POOL, weights=_STYLE_WEIGHTS, k=1)[0]

--- callers of select_action (grep -n, excluding the definition) ---
cage_dynasty_web/window_registry.py:146:        write_site="fight_engine.select_action (~:2148-2156)",
cage_dynasty_web/fight_integration.py:38:    get_available_grappling_actions, select_action,
cage_dynasty_web/fight_integration.py:151:    Applied on top of base select_action weights.
cage_dynasty_web/fight_integration.py:153:    Mirrors the inline dict in fight_engine.select_action."""
cage_dynasty_web/fight_integration.py:485:        # select_action + _determine_initiative. Stored verbatim; None
cage_dynasty_web/fight_integration.py:1156:        # GAMEPLAN-DIAL-AGGR1: hand the actor's gameplan to select_action
cage_dynasty_web/fight_integration.py:1172:        action_type, action_data = select_action(
cage_dynasty_web/fight_integration.py:2658:    simulator and on to select_action, but are not yet consumed
cage_dynasty_web/fight_engine.py:1355:    simulate_narrated_fight → NarratedFightSimulator → select_action
cage_dynasty_web/fight_engine.py:1357:    Gameplan get byte-identical behavior. select_action accepts the
cage_dynasty_web/fight_engine.py:4088:    action_type, action_data = select_action(attacker, defender, fight_state, attacker_state)
cage_dynasty_web/game_bridge.py:292:# +8%×IQ inside select_action).

--- Positive control: must return fight_engine.py:2436 ---
2436:    _STYLE_WEIGHTS = {

--- Sub gate readers: lines that assign or read _sub_threshold or the gate predicate ---
cage_dynasty_web/fight_engine.py:1717:        if fighter_attrs.submissions >= 60:
cage_dynasty_web/fight_engine.py:1757:            if fighter_attrs.submissions >= 65 and _bm_duration < 3:
cage_dynasty_web/fight_engine.py:2319:                if fighter_attrs.submissions >= 60:
cage_dynasty_web/fight_engine.py:2321:                elif fighter_attrs.submissions >= 50:
cage_dynasty_web/fight_engine.py:2326:                if fighter_attrs.submissions >= 85:
cage_dynasty_web/fight_engine.py:2328:                elif fighter_attrs.submissions >= 75:
cage_dynasty_web/fight_engine.py:2330:                elif fighter_attrs.submissions >= 60:
cage_dynasty_web/fight_engine.py:2342:                if fighter_attrs.submissions >= 55:
cage_dynasty_web/fight_engine.py:2344:                elif fighter_attrs.submissions >= 45:
cage_dynasty_web/fight_engine.py:2347:                if fighter_attrs.submissions >= 85:
cage_dynasty_web/fight_engine.py:2349:                elif fighter_attrs.submissions >= 75:
cage_dynasty_web/fight_engine.py:2351:                elif fighter_attrs.submissions >= 60:
cage_dynasty_web/fight_engine.py:2359:                if fighter_attrs.submissions >= 55:
cage_dynasty_web/fight_engine.py:2361:                elif fighter_attrs.submissions >= 45:
cage_dynasty_web/fight_engine.py:2364:                if fighter_attrs.submissions >= 60:
cage_dynasty_web/fight_engine.py:2366:                elif fighter_attrs.submissions >= 50:
cage_dynasty_web/fight_engine.py:2369:                if fighter_attrs.submissions >= 85:
cage_dynasty_web/fight_engine.py:2371:                elif fighter_attrs.submissions >= 75:
cage_dynasty_web/fight_engine.py:2373:                elif fighter_attrs.submissions >= 60:
cage_dynasty_web/fight_engine.py:2388:                    if fighter_attrs.submissions >= 55:
cage_dynasty_web/fight_engine.py:2390:                    elif fighter_attrs.submissions >= 45:
cage_dynasty_web/fight_engine.py:2392:                    elif fighter_attrs.submissions >= 35:
cage_dynasty_web/fight_engine.py:2395:                    if fighter_attrs.submissions >= 85:
cage_dynasty_web/fight_engine.py:2397:                    elif fighter_attrs.submissions >= 75:
cage_dynasty_web/fight_engine.py:2399:                    elif fighter_attrs.submissions >= 60:
cage_dynasty_web/fight_engine.py:2604:    _sub_threshold = 45 if my_style in ("bjj", "sambo") else 60
cage_dynasty_web/fight_engine.py:2605:    if submissions and fighter_attrs.submissions >= _sub_threshold:

=== 3. FI-WEIGHT-TABLE-DEAD1 twin + its readers ===
--- fight_integration.py :149-180 (get_style_action_weights) ---
def get_style_action_weights(style) -> Dict[str, float]:
    """Action weight multipliers by fighting style.
    Applied on top of base select_action weights.
    Grapplers get more submission/grapple; strikers more striking.
    Mirrors the inline dict in fight_engine.select_action."""
    weights = {
        "ORTHODOX_BOXER":    {"strike":1.4,"grapple":0.7,"submission":0.3},
        "KICKBOXER":         {"strike":1.4,"grapple":0.7,"submission":0.3},
        "MUAY_THAI":         {"strike":1.3,"grapple":0.9,"submission":0.4},
        "PRESSURE_FIGHTER":  {"strike":1.2,"grapple":1.0,"submission":0.4},
        "COUNTER_STRIKER":   {"strike":1.3,"grapple":0.8,"submission":0.3},
        "POINT_FIGHTER":     {"strike":1.4,"grapple":0.6,"submission":0.2},
        "KARATE":            {"strike":1.3,"grapple":0.7,"submission":0.3},
        "WRESTLER":          {"strike":0.8,"grapple":1.4,"submission":0.9},
        "BJJ_SPECIALIST":    {"strike":0.6,"grapple":1.2,"submission":2.0},
        "SAMBO":             {"strike":0.9,"grapple":1.3,"submission":1.4},
        "JUDO":              {"strike":0.8,"grapple":1.5,"submission":0.9},
        "GROUND_AND_POUND":  {"strike":1.0,"grapple":1.4,"submission":0.6},
        "SPRAWL_AND_BRAWL":  {"strike":1.3,"grapple":0.7,"submission":0.4},
        "CLINCH_FIGHTER":    {"strike":1.0,"grapple":1.3,"submission":0.7},
        "BRAWLER":           {"strike":1.3,"grapple":0.8,"submission":0.4},
        "HYBRID":            {"strike":1.0,"grapple":1.0,"submission":0.8},
        "STRIKER":           {"strike":1.4,"grapple":0.7,"submission":0.3},
        "BALANCED":          {"strike":1.0,"grapple":1.0,"submission":1.0},
    }
    s = getattr(style, 'name', '') or str(style)
    return weights.get(s.upper(),
        {"strike":1.0,"grapple":1.0,"submission":1.0})

# Event logging types
class FightEventType(Enum):
    """Types of events that can occur in a fight."""

--- grep for callers of get_style_action_weights in cage_dynasty_web/ ---

=== 4. git diff c7fe846 for /tmp/cd-exp-cut-c7s split into (a) instrument vs (b) behavior ===

--- (b) BEHAVIOR lines (table values + gate branch), with context ---
  (1) Table submission column change for WRESTLER (0.9 -> 0.45):
84:-        "WRESTLER":          {"strike":0.8,"grapple":1.4,"submission":0.9},
85:+        "WRESTLER":          {"strike":0.8,"grapple":1.4,"submission":0.45},

  (2) Table submission column change for GROUND_AND_POUND (0.6 -> 0.4):
89:-        "GROUND_AND_POUND":  {"strike":1.0,"grapple":1.4,"submission":0.6},
90:+        "GROUND_AND_POUND":  {"strike":1.0,"grapple":1.4,"submission":0.4},

  (3) Table submission column change for CLINCH_FIGHTER (0.7 -> 0.5):
92:-        "CLINCH_FIGHTER":    {"strike":1.0,"grapple":1.3,"submission":0.7},
93:+        "CLINCH_FIGHTER":    {"strike":1.0,"grapple":1.3,"submission":0.5},

  (4) Gate branch rewrite (conditional floor):
152:+        if _style_key == "BJJ_SPECIALIST":
153-+            sub_weight = max(1, sub_weight)
154-+        elif fighter_attrs.submissions >= _CUT_SKILL_FLOOR_N:
155-+            sub_weight = max(1, sub_weight)
156-     else:
157-+        _CUT_COUNTERS["gate_failed"] += 1

--- (a) instrument-only lines (not behavior): counter dicts, atexit, hist/table captures. NOT listed per spec. ---

=== 5. C7s per-seed record shas + SUB counts from outputs/cut_screen/ ===
  s1: sha=0938c4a6eefbc845a82e9ce6638a80feee5aaab185d32f30b21340d41d45a721  sim=1080  SUB=202
  s2: sha=0d3b8a0ec9f0efbb4c0602760369195b57f2ae6c79cc636fb38c2536b211ea9b  sim=1080  SUB=188
  s3: sha=232866f4a08e1cd8954fb312c7bba361c2b638e0df94fba376c587ff5970c7c8  sim=1080  SUB=201
  s4: sha=a2ffeb33113bb5ade095f82ff7fa02837ff3b5495fa4b976b3695141fb8e4637  sim=1080  SUB=175
  s5: sha=babf3a7ad94cc941d2c2d6c88d385ae45be69752c0c59dfb69415b77a056a172  sim=1080  SUB=177

=== 6. Paths reaching select_action: live, odds, pre-gen (caller file:line) ===

--- A. select_action definition ---
2016:def select_action(

--- B. direct call sites of select_action (caller file:line) ---
cage_dynasty_web/fight_engine.py:4088:    action_type, action_data = select_action(attacker, defender, fight_state, attacker_state)
cage_dynasty_web/fight_integration.py:1172:        action_type, action_data = select_action(

--- C. path provenance per call site ---
  fight_engine.py:4088  — inside fight_engine.simulate_fight (pre-generation path; world_init -> simulate_fight)
    Pre-gen trace (world_init.py readers of simulate_fight):
74:        simulate_fight as engine_simulate_fight,
80:    # discipline. fe.simulate_fight retained above so a fi import
92:    # simulate_fight_simple fallback since project launch — see fingerprint
101:          "simulate_fight_simple (clamps favorite win rate at 74% "
2041:        simulate_fight_simple. Even with FULL_ENGINE_AVAILABLE=True after the
2122:            print(f"🚨   → this fight will fall back to simulate_fight_simple; "
2127:    def simulate_fight_full_engine(
2219:    def simulate_fight_simple(
2226:        FINISH-DETAIL-PERSIST: returns 5-tuple to match simulate_fight_full_engine.
2288:                self.simulate_fight_full_engine(

  fight_integration.py:1172  — inside fight_integration.simulate_narrated_fight
    live card (Path A / Path B) caller sites in game_bridge.py:
219:    _simulate_narrated_fight_fn = _fem.simulate_narrated_fight
14007:                    _eng = _simulate_narrated_fight_fn(
17766:        if not FIGHT_ENGINE_AVAILABLE or _simulate_narrated_fight_fn is None:
17827:                    _eng = _simulate_narrated_fight_fn(
18431:        eng_result: _NarratedFightResult = _simulate_narrated_fight_fn(
    MC-odds compute site (_compute_mc_odds_for_fight):
17753:    def _compute_mc_odds_for_fight(
17880:    def _precompute_odds_for_fights(self, fights: List[Dict]) -> None:

## Embed 6/7 — outputs/cut_build_2026-11-16.txt
sha256 7f369371f326d8e362ef4d9e859fe537577186a1f9cb36f0bc49c01ec3aa6d79

=== CUT BUILD — pre-state ===

--- a. HEAD + status --short -uno ---
fe4d8b3f9a016b3cf1980c3c6dd9d3d5fa12b679

status --short -uno (expect empty):
  (above: empty = clean tracked state)

--- b. cage_dynasty_web/fight_engine.py :2436-2455 and :2600-2610 ---
    _STYLE_WEIGHTS = {
        "ORTHODOX_BOXER":    {"strike":1.4,"grapple":0.7,"submission":0.3},
        "KICKBOXER":         {"strike":1.4,"grapple":0.7,"submission":0.3},
        "MUAY_THAI":         {"strike":1.3,"grapple":0.9,"submission":0.4},
        "PRESSURE_FIGHTER":  {"strike":1.2,"grapple":1.0,"submission":0.4},
        "COUNTER_STRIKER":   {"strike":1.3,"grapple":0.8,"submission":0.3},
        "POINT_FIGHTER":     {"strike":1.4,"grapple":0.6,"submission":0.2},
        "KARATE":            {"strike":1.3,"grapple":0.7,"submission":0.3},
        "WRESTLER":          {"strike":0.8,"grapple":1.4,"submission":0.9},
        "BJJ_SPECIALIST":    {"strike":0.6,"grapple":1.2,"submission":2.0},
        "SAMBO":             {"strike":0.9,"grapple":1.3,"submission":1.4},
        "JUDO":              {"strike":0.8,"grapple":1.5,"submission":0.9},
        "GROUND_AND_POUND":  {"strike":1.0,"grapple":1.4,"submission":0.6},
        "SPRAWL_AND_BRAWL":  {"strike":1.3,"grapple":0.7,"submission":0.4},
        "CLINCH_FIGHTER":    {"strike":1.0,"grapple":1.3,"submission":0.7},
        "BRAWLER":           {"strike":1.3,"grapple":0.8,"submission":0.4},
        "HYBRID":            {"strike":1.0,"grapple":1.0,"submission":0.8},
        "STRIKER":           {"strike":1.4,"grapple":0.7,"submission":0.3},
        "BALANCED":          {"strike":1.0,"grapple":1.0,"submission":1.0},
    }
    
    # Ensure minimum weights
    strike_weight = max(5, strike_weight) if strikes else 0
    # Sub gate: BJJ/Sambo can attempt subs at 45+, everyone else at 60+
    _sub_threshold = 45 if my_style in ("bjj", "sambo") else 60
    if submissions and fighter_attrs.submissions >= _sub_threshold:
        sub_weight = max(1, sub_weight)
    else:
        sub_weight = 0
    grapple_weight = max(5, grapple_weight) if grappling else 0
    

--- c. Expectations (read from disk) ---
  Five C7s record shas + SUB counts (outputs/cut_screen/C7s_s{1..5}.json):
    s1: sha=0938c4a6eefbc845a82e9ce6638a80feee5aaab185d32f30b21340d41d45a721  sim=1080  SUB=202
    s2: sha=0d3b8a0ec9f0efbb4c0602760369195b57f2ae6c79cc636fb38c2536b211ea9b  sim=1080  SUB=188
    s3: sha=232866f4a08e1cd8954fb312c7bba361c2b638e0df94fba376c587ff5970c7c8  sim=1080  SUB=201
    s4: sha=a2ffeb33113bb5ade095f82ff7fa02837ff3b5495fa4b976b3695141fb8e4637  sim=1080  SUB=175
    s5: sha=babf3a7ad94cc941d2c2d6c88d385ae45be69752c0c59dfb69415b77a056a172  sim=1080  SUB=177
    pooled SUB: 943  (expected 943)

  F1/w1 row-list sha (outputs/cut_paired/F1/w1.json):
    row-list sha: 425424cc9c94f7d116ec2aad23a507b61c3544b9c7792189e185c6d8f86797b3
    fight_count: 402   SUB: 75

  Five S0 (filed L1) shas + pooled SUB 1147:
    s1: 784c5d38210cfd33b125f6009f39700912287a7d025231226378f36d316f796e  SUB 244
    s2: b1189bb9affe73d111c825bcff773edabce21cd89de0ef3d3219078f4e3ab0db  SUB 227
    s3: 7ac3f3c2a61660c7abc07f89e590cb4087bf80bac1badc1486c900c59d553295  SUB 233
    s4: 9ba5d31916ce6855e85ced5ab5b2904750ac2d985782b9f8cffa633624f6532a  SUB 227
    s5: 562cf436f3edf0513da99d9b9609b8d734aa14c15b4a49ac6e15a2d0f542e4a3  SUB 216
    pooled SUB: 1147

=== EDIT applied to main tree ===

=== G1 — syntax + diff ===
syntax OK

--- git diff --stat ---
 cage_dynasty_web/fight_engine.py | 15 ++++++++++-----
 1 file changed, 10 insertions(+), 5 deletions(-)

--- git diff in full ---
diff --git a/cage_dynasty_web/fight_engine.py b/cage_dynasty_web/fight_engine.py
index ebd4db0..09b7571 100644
--- a/cage_dynasty_web/fight_engine.py
+++ b/cage_dynasty_web/fight_engine.py
@@ -2441,13 +2441,13 @@ def select_action(
         "COUNTER_STRIKER":   {"strike":1.3,"grapple":0.8,"submission":0.3},
         "POINT_FIGHTER":     {"strike":1.4,"grapple":0.6,"submission":0.2},
         "KARATE":            {"strike":1.3,"grapple":0.7,"submission":0.3},
-        "WRESTLER":          {"strike":0.8,"grapple":1.4,"submission":0.9},
+        "WRESTLER":          {"strike":0.8,"grapple":1.4,"submission":0.45},
         "BJJ_SPECIALIST":    {"strike":0.6,"grapple":1.2,"submission":2.0},
         "SAMBO":             {"strike":0.9,"grapple":1.3,"submission":1.4},
         "JUDO":              {"strike":0.8,"grapple":1.5,"submission":0.9},
-        "GROUND_AND_POUND":  {"strike":1.0,"grapple":1.4,"submission":0.6},
+        "GROUND_AND_POUND":  {"strike":1.0,"grapple":1.4,"submission":0.4},
         "SPRAWL_AND_BRAWL":  {"strike":1.3,"grapple":0.7,"submission":0.4},
-        "CLINCH_FIGHTER":    {"strike":1.0,"grapple":1.3,"submission":0.7},
+        "CLINCH_FIGHTER":    {"strike":1.0,"grapple":1.3,"submission":0.5},
         "BRAWLER":           {"strike":1.3,"grapple":0.8,"submission":0.4},
         "HYBRID":            {"strike":1.0,"grapple":1.0,"submission":0.8},
         "STRIKER":           {"strike":1.4,"grapple":0.7,"submission":0.3},
@@ -2600,10 +2600,15 @@ def select_action(
     
     # Ensure minimum weights
     strike_weight = max(5, strike_weight) if strikes else 0
-    # Sub gate: BJJ/Sambo can attempt subs at 45+, everyone else at 60+
+    # Sub gate: BJJ/Sambo can attempt subs at 45+, everyone else at 60+.
+    # Floor rule (Van, 2026-11-16): max(1, sub_weight) applies only when
+    # the style key is BJJ_SPECIALIST or fighter_attrs.submissions >= 80;
+    # any other non-BJJ style below 80 keeps its computed sub_weight
+    # (which may be 0 after int() truncation of the style-weight multiply).
     _sub_threshold = 45 if my_style in ("bjj", "sambo") else 60
     if submissions and fighter_attrs.submissions >= _sub_threshold:
-        sub_weight = max(1, sub_weight)
+        if _style_key == "BJJ_SPECIALIST" or fighter_attrs.submissions >= 80:
+            sub_weight = max(1, sub_weight)
     else:
         sub_weight = 0
     grapple_weight = max(5, grapple_weight) if grappling else 0

sha256 of main tree fight_engine.py:
191e616573a13bbf4117250997fd0e147b50568e0c0a26f7b856a158447abf48  cage_dynasty_web/fight_engine.py

=== G2 — build tree ===
Preparing worktree (detached HEAD fe4d8b3)
HEAD is now at fe4d8b3 DOCS: STYLE1 live-measure filing (one-judge c7fe846 live SUB 292/1206 = 24.21% vs baseline 450eb08 324/1211 = 26.75%, same worker bar the REPO line, seeds 20261114/15/16, three worlds per arm, different populations, TREND; fixed population had shown 28.04 to 21.24; BJJ Specialist 77.96% of wins by SUB, Wrestler 40.30%, G&P 18.07%; PA at a19a921 by Van's console rev-parse; false-as-written, not-measured, architect errors, cc process; three reports embedded verbatim with sha256). Rulings (Van, 2026-11-14): one-judge deploys alone; SUB working target 19-20% live with BJJ Specialists untouched; style_mod winner flip removed, never fixed. Backlog: STYLE1 status, SUB-RATE1 ruling, ODDS-ONEJUDGE1 partial, SAMBO-ENUM1 addendum (four maps), STYLE-MOD-REMOVE1, PLAYER-LABEL-PATHS1, FI-WEIGHT-TABLE-DEAD1, FIXEDPOP-LIVE-GAP1. Index +1. No engine change.
error: affected file '/tmp/cd-build-cut/cage_dynasty_web/fight_engine.py' is beyond a symbolic link
  (apply fallback: cp from main tree)

--- sha equality check ---
  main  : 191e616573a13bbf4117250997fd0e147b50568e0c0a26f7b856a158447abf48
  build : 191e616573a13bbf4117250997fd0e147b50568e0c0a26f7b856a158447abf48
  EQUAL : True

--- build tree status ---
fe4d8b3f9a016b3cf1980c3c6dd9d3d5fa12b679
 M cage_dynasty_web/fight_engine.py
--- build tree diff --stat ---
 cage_dynasty_web/fight_engine.py | 15 ++++++++++-----
 1 file changed, 10 insertions(+), 5 deletions(-)

=== G3 — fixed population, 5 seed sets, build tree ===
[st1r2 worker] done sim=1080 dt=14.0s sha=0938c4a6eefbc845 wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_screen/build_s1.json
[st1r2 worker] done sim=1080 dt=14.2s sha=0d3b8a0ec9f0efbb wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_screen/build_s2.json
[st1r2 worker] done sim=1080 dt=16.7s sha=232866f4a08e1cd8 wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_screen/build_s3.json
[st1r2 worker] done sim=1080 dt=15.6s sha=a2ffeb33113bb5ad wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_screen/build_s4.json
[st1r2 worker] done sim=1080 dt=14.0s sha=babf3a7ad94cc941 wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_screen/build_s5.json

=== G3 compare ===
seed  exp_sha                                                             exp_SUB  got_sha                                                             got_SUB  match
s1    0938c4a6eefbc845a82e9ce6638a80feee5aaab185d32f30b21340d41d45a721        202  0938c4a6eefbc845a82e9ce6638a80feee5aaab185d32f30b21340d41d45a721        202  YES
s2    0d3b8a0ec9f0efbb4c0602760369195b57f2ae6c79cc636fb38c2536b211ea9b        188  0d3b8a0ec9f0efbb4c0602760369195b57f2ae6c79cc636fb38c2536b211ea9b        188  YES
s3    232866f4a08e1cd8954fb312c7bba361c2b638e0df94fba376c587ff5970c7c8        201  232866f4a08e1cd8954fb312c7bba361c2b638e0df94fba376c587ff5970c7c8        201  YES
s4    a2ffeb33113bb5ade095f82ff7fa02837ff3b5495fa4b976b3695141fb8e4637        175  a2ffeb33113bb5ade095f82ff7fa02837ff3b5495fa4b976b3695141fb8e4637        175  YES
s5    babf3a7ad94cc941d2c2d6c88d385ae45be69752c0c59dfb69415b77a056a172        177  babf3a7ad94cc941d2c2d6c88d385ae45be69752c0c59dfb69415b77a056a172        177  YES
pooled SUB: 943  (expected 943)   match: True
G3 PASS: True

=== G4 — discrimination: clean c7fe846 tree must give S0 shas + 1147 ===
[st1r2 worker] done sim=1080 dt=13.6s sha=784c5d38210cfd33 wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_discr/clean_s1.json
[st1r2 worker] done sim=1080 dt=13.3s sha=b1189bb9affe73d1 wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_discr/clean_s2.json
[st1r2 worker] done sim=1080 dt=13.1s sha=7ac3f3c2a61660c7 wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_discr/clean_s3.json
[st1r2 worker] done sim=1080 dt=13.1s sha=9ba5d31916ce6855 wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_discr/clean_s4.json
[st1r2 worker] done sim=1080 dt=14.3s sha=562cf436f3edf051 wrote /Users/vandope/Desktop/Games/cage_dynasty/outputs/cut_build_discr/clean_s5.json

=== G4 discrimination ===
seed  got_sha                                                             got_SUB  S0_match   C7s_match
s1    784c5d38210cfd33b125f6009f39700912287a7d025231226378f36d316f796e        244       YES          NO
s2    b1189bb9affe73d111c825bcff773edabce21cd89de0ef3d3219078f4e3ab0db        227       YES          NO
s3    7ac3f3c2a61660c7abc07f89e590cb4087bf80bac1badc1486c900c59d553295        233       YES          NO
s4    9ba5d31916ce6855e85ced5ab5b2904750ac2d985782b9f8cffa633624f6532a        227       YES          NO
s5    562cf436f3edf0513da99d9b9609b8d734aa14c15b4a49ac6e15a2d0f542e4a3        216       YES          NO
pooled SUB: 1147  (expected 1147)   match: True
G4 PASS: True

=== G5 — live path (paired v2) on build tree, seed 20261114 ===
build-tree g5 : sha=425424cc9c94f7d116ec2aad23a507b61c3544b9c7792189e185c6d8f86797b3  fights=402  SUB=75
F1/w1 expected: sha=425424cc9c94f7d116ec2aad23a507b61c3544b9c7792189e185c6d8f86797b3  fights=402  SUB=75
EQUAL: True
G5 PASS: True

=== G6 — main tree status --short -uno ===
 M cage_dynasty_web/fight_engine.py
  (expected: one line '  M cage_dynasty_web/fight_engine.py')

=== ALL GATES PASS ===
  G1 syntax + diff        : PASS (10/5, one file)
  G2 build tree sha-equal : PASS (191e6165... both)
  G3 fixed-pop 5 seeds    : PASS (all five C7s shas + 943)
  G4 discrimination clean : PASS (S0 shas + 1147; 0 of 5 collide with C7s)
  G5 live paired seed 1   : PASS (425424cc... == F1/w1 sha; 402/75)
  G6 main tree status     : PASS (one line, fight_engine.py only)

=== Proposed commit message ===

SUB-RATE1 CUT: non-BJJ sub weights + skill-80 floor rule in
select_action (fight_engine.py). WRESTLER submission 0.9->0.45,
GROUND_AND_POUND 0.6->0.4, CLINCH_FIGHTER 0.7->0.5. At the sub gate,
max(1, sub_weight) now applies only when the style key is
BJJ_SPECIALIST or fighter_attrs.submissions >= 80; any other non-BJJ
style below 80 keeps its computed sub_weight (which may be 0 after
int-truncation of the style-weight multiply). BJJ_SPECIALIST and the
outer BJJ/Sambo-at-45 vs others-at-60 threshold are unchanged. No
instrument, no new imports, no edits to fight_integration.py.
Rulings: Van, 2026-11-16.

MEASURED (fixed-population screen, five seed sets × 1080 pairs =
5400 fights, outputs/style1_round2_worker.py):
  before (c7fe846 / S0): 1147 SUB pooled, 21.24%
  after  (this edit)   :  943 SUB pooled, 17.46% (-204, cut 17.79%)
  five per-seed record shas match the C7s screen entry;
  five clean-c7fe846 shas match the filed S0 L1 entry (discrimination).
MEASURED (live-paired, outputs/live_cut_worker_paired_v2.py,
seed 20261114, PYTHONHASHSEED=0, uuid4 seeded, one world):
  row-list sha equals F1/w1 from round-5 (425424cc...);
  402 fights, 75 SUB (18.66%).

NOT MEASURED: live-path pooled SUB across the full 3-world + 3-seed
set in this release-grade build tree (only the P1 seed was re-run
for byte equality); live vs the filed pre-cut baseline (26.75%);
odds-path shift; any PA import/behavior.

NOT DEPLOYED. Build tree /tmp/cd-build-cut carries the applied diff;
main tree carries the uncommitted edit; no engine changes anywhere
else.

=== Exact commands I would run (DO NOT RUN) ===
  git add cage_dynasty_web/fight_engine.py
  git commit -m "$(cat <<'MSG'
  <the message above>
  MSG
  )"

## Embed 7/7 — outputs/bridge_label_control_2026-11-16.txt
sha256 6514f7cee46a198c79bc8449fa1a33d7509f867f61d70ed4e92b2125c72614bd

=== PHASE 0 — read-only from c7fe846 (via /tmp/cd-exp-live-onejudge) ===

--- 1a. Named maps (sanity: must find _STYLE_TO_CANONICAL, _STYLE_MAP, _LEGACY_STYLE_REMAP, _STYLE_STR_MAP) ---
447:_STYLE_TO_CANONICAL = {
17354:    _STYLE_MAP = {
17661:                    _STYLE_STR_MAP = {
22250:                _LEGACY_STYLE_REMAP = {

--- 1b. Every '.get(...DEFAULT...)' / fallback site reading these maps ---
5289:            _canonical = _STYLE_TO_CANONICAL.get(_raw, _raw)
7467:        fighting_style = _STYLE_TO_CANONICAL.get(_raw_style, _raw_style)
17404:        style_key = self._STYLE_MAP.get(style_str, "BALANCED")
17688:                    fs1 = _FightingStyleEnum(_STYLE_STR_MAP.get(s1, 'BALANCED'))
17689:                    fs2 = _FightingStyleEnum(_STYLE_STR_MAP.get(s2, 'BALANCED'))
18367:            _canonical = _STYLE_TO_CANONICAL.get(_raw, _raw)
22265:                _canonical_style = _LEGACY_STYLE_REMAP.get(

--- 1c. Context around each .get() call, 5 lines each ---
--- :5289 (context 5286-5292) ---
        # own compositional model — see BRIDGE-WIRE-DIAG1 §2 for why).
        def _ai_gp(f):
            _raw = getattr(f, 'fighting_style', '') or ''
            _canonical = _STYLE_TO_CANONICAL.get(_raw, _raw)
            return ai_gameplan_for_style(_canonical)

        player_fids = set()

--- :7467 (context 7464-7470) ---
        # Translate legacy martial art names to canonical display names.
        # Table lifted to module scope as _STYLE_TO_CANONICAL for reuse
        # by the AI-side gameplan resolver (GAMEPLAN-AI-SELECT1).
        fighting_style = _STYLE_TO_CANONICAL.get(_raw_style, _raw_style)
        nickname       = fighter.nickname or fdata.get("nickname")
        fatigue        = int(fdata.get("fatigue", 0))


--- :17404 (context 17401-17407) ---
            return max(1, min(99, int(fdata.get(attr, getattr(fighter, attr, ovr + offset)))))

        style_str = fdata.get("style", getattr(fighter, 'fighting_style', "Balanced"))
        style_key = self._STYLE_MAP.get(style_str, "BALANCED")

        from core.types import FightingStyle
        style = FightingStyle[style_key]

--- :17688 (context 17685-17691) ---
                    }
                    s1 = self._game_state._fighter_data.get(f1_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
                    s2 = self._game_state._fighter_data.get(f2_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
                    fs1 = _FightingStyleEnum(_STYLE_STR_MAP.get(s1, 'BALANCED'))
                    fs2 = _FightingStyleEnum(_STYLE_STR_MAP.get(s2, 'BALANCED'))
                    style_mod = get_style_matchup_modifier(fs1, fs2)
                except Exception:

--- :17689 (context 17686-17692) ---
                    s1 = self._game_state._fighter_data.get(f1_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
                    s2 = self._game_state._fighter_data.get(f2_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
                    fs1 = _FightingStyleEnum(_STYLE_STR_MAP.get(s1, 'BALANCED'))
                    fs2 = _FightingStyleEnum(_STYLE_STR_MAP.get(s2, 'BALANCED'))
                    style_mod = get_style_matchup_modifier(fs1, fs2)
                except Exception:
                    pass

--- :18367 (context 18364-18370) ---
                _fd = (self._game_state._fighter_data.get(_fid, {})
                       if (self._game_state and _fid) else {})
                _raw = str(_fd.get('style', '') or '')
            _canonical = _STYLE_TO_CANONICAL.get(_raw, _raw)
            if _tend_on:
                _pers = str(getattr(_record, 'personality', '') or '')
                if not _pers:

--- :22265 (context 22262-22268) ---
                }
                _raw_style = str(
                    getattr(amateur, 'fighting_style', '') or '')
                _canonical_style = _LEGACY_STYLE_REMAP.get(
                    _raw_style, _raw_style if _raw_style else 'Balanced')
                # Post-Phase-C amateurs come in with canonical styles
                # already; the remap is a no-op for them (canonical

--- 1d. Positive control: GameBridge._STYLE_MAP (the class-level map) must appear ---
2072:class GameBridge:
17354:    _STYLE_MAP = {

--- 2. Path classification per fallback site ---

--- site :7467 — enclosing def (backscan) ---
7341:    def _convert_real_fighter(self, fighter) -> WebFighter:
--- site :17404 — enclosing def (backscan) ---
17383:    def _make_fighter_attrs(self, fighter, name: str, fighter_id: str):
--- site :17677 — enclosing def (backscan) ---
17542:    def _assemble_prefight(
--- site :17688 — enclosing def (backscan) ---
17542:    def _assemble_prefight(
--- site :17689 — enclosing def (backscan) ---
17542:    def _assemble_prefight(
--- site :18367 — enclosing def (backscan) ---
18295:    def _resolve_gameplan(self, fighter_attrs, fight, player_fids):
--- site :22265 — enclosing def (backscan) ---
22193:    def sign_amateur(self, amateur_id: str) -> Dict[str, Any]:

--- 1b (rerun to pick up missed sites, including the one at :17677) ---
5289:            _canonical = _STYLE_TO_CANONICAL.get(_raw, _raw)
7467:        fighting_style = _STYLE_TO_CANONICAL.get(_raw_style, _raw_style)
17404:        style_key = self._STYLE_MAP.get(style_str, "BALANCED")
17688:                    fs1 = _FightingStyleEnum(_STYLE_STR_MAP.get(s1, 'BALANCED'))
17689:                    fs2 = _FightingStyleEnum(_STYLE_STR_MAP.get(s2, 'BALANCED'))
18367:            _canonical = _STYLE_TO_CANONICAL.get(_raw, _raw)
22265:                _canonical_style = _LEGACY_STYLE_REMAP.get(

--- 1e. Previously-hidden site at :5289 context ---
        # own compositional model — see BRIDGE-WIRE-DIAG1 §2 for why).
        def _ai_gp(f):
            _raw = getattr(f, 'fighting_style', '') or ''
            _canonical = _STYLE_TO_CANONICAL.get(_raw, _raw)
            return ai_gameplan_for_style(_canonical)

        player_fids = set()

--- enclosing def for :5289 ---
5183:    def _simulate_fight(self, fight: Dict) -> Dict:

--- 1f. Full site inventory + path classification ===
  line      symbol                enclosing_def         code_path_tag
  ----      ------                -------------         -------------
  5289      _STYLE_TO_CANONICAL.get  (scan below)          DISPLAY + AI gameplan
  7467      _STYLE_TO_CANONICAL.get  _convert_real_fighter  DISPLAY (WebFighter render)
  17404     self._STYLE_MAP.get   _make_fighter_attrs   LIVE + ODDS + PRE-GEN (engine-input FighterAttributes.fighting_style)
  17677     _STYLE_STR_MAP (literal)  _assemble_prefight    LIVE + ODDS (style_mod flip; STYLE-DEAD1 pins to 0.0)
  17688     _STYLE_STR_MAP.get    _assemble_prefight    LIVE + ODDS (style_mod flip; STYLE-DEAD1 pins to 0.0)
  17689     _STYLE_STR_MAP.get    _assemble_prefight    LIVE + ODDS (style_mod flip; STYLE-DEAD1 pins to 0.0)
  18367     _STYLE_TO_CANONICAL.get  _resolve_gameplan     LIVE (AI gameplan resolution)
  22265     _LEGACY_STYLE_REMAP.get  sign_amateur          PRE-GEN promotion path + live sign-amateur route

=== SANDBOX — instrument-only diff (7 bump sites + module-level counter) ===
diff --git a/cage_dynasty_web/game_bridge.py b/cage_dynasty_web/game_bridge.py
index 6364685..da30150 100644
--- a/cage_dynasty_web/game_bridge.py
+++ b/cage_dynasty_web/game_bridge.py
@@ -13,6 +13,41 @@ import zlib
 from typing import Dict, List, Optional, Any, Set
 from dataclasses import dataclass, field
 
+# BRIDGE-LABEL CONTROL: module-level instrument. Counts every call to
+# the four style-name maps' .get() sites. On fallback (raw label not
+# in the map dict) the raw label is recorded. No behavior change: the
+# bump runs BEFORE the actual .get() call and does not alter the
+# returned value.
+_BRIDGE_LABEL_COUNTERS = {"sites": {}}
+def _bl_bump(site_tag, raw_label, map_obj):
+    rec = _BRIDGE_LABEL_COUNTERS["sites"].setdefault(
+        site_tag, {"total": 0, "fallback": 0, "fallback_labels": {}})
+    rec["total"] += 1
+    if raw_label not in map_obj:
+        rec["fallback"] += 1
+        key = raw_label if isinstance(raw_label, str) else repr(raw_label)
+        rec["fallback_labels"][key] = rec["fallback_labels"].get(key, 0) + 1
+
+def _bl_read():
+    out = {"sites": {}}
+    for tag, rec in _BRIDGE_LABEL_COUNTERS["sites"].items():
+        out["sites"][tag] = {
+            "total": rec["total"], "fallback": rec["fallback"],
+            "fallback_labels": dict(rec["fallback_labels"]),
+        }
+    return out
+
+def _bl_reset():
+    _BRIDGE_LABEL_COUNTERS["sites"] = {}
+
+import atexit as _bl_atexit
+import json as _bl_json
+def _bl_atexit_emit():
+    print("===BRIDGE_LABEL_COUNTERS===  " + _bl_json.dumps(_bl_read(), default=str),
+          flush=True)
+_bl_atexit.register(_bl_atexit_emit)
+
+
 # FOUNDING-ROW2 (2026-09-15): single source of truth for founding-row
 # detection. Module-scope import — safe because world_init does not
 # import game_bridge (no cycle risk). Used by the canonical streak
@@ -5286,6 +5321,7 @@ class GameBridge:
         # own compositional model — see BRIDGE-WIRE-DIAG1 §2 for why).
         def _ai_gp(f):
             _raw = getattr(f, 'fighting_style', '') or ''
+            _bl_bump("site_5289_resolve_ai_gp", _raw, _STYLE_TO_CANONICAL)
             _canonical = _STYLE_TO_CANONICAL.get(_raw, _raw)
             return ai_gameplan_for_style(_canonical)
 
@@ -7464,6 +7500,7 @@ class GameBridge:
         # Translate legacy martial art names to canonical display names.
         # Table lifted to module scope as _STYLE_TO_CANONICAL for reuse
         # by the AI-side gameplan resolver (GAMEPLAN-AI-SELECT1).
+        _bl_bump("site_7467_convert_real_fighter", _raw_style, _STYLE_TO_CANONICAL)
         fighting_style = _STYLE_TO_CANONICAL.get(_raw_style, _raw_style)
         nickname       = fighter.nickname or fdata.get("nickname")
         fatigue        = int(fdata.get("fatigue", 0))
@@ -17401,6 +17438,7 @@ class GameBridge:
             return max(1, min(99, int(fdata.get(attr, getattr(fighter, attr, ovr + offset)))))
 
         style_str = fdata.get("style", getattr(fighter, 'fighting_style', "Balanced"))
+        _bl_bump("site_17404_make_fighter_attrs", style_str, self._STYLE_MAP)
         style_key = self._STYLE_MAP.get(style_str, "BALANCED")
 
         from core.types import FightingStyle
@@ -17685,6 +17723,8 @@ class GameBridge:
                     }
                     s1 = self._game_state._fighter_data.get(f1_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
                     s2 = self._game_state._fighter_data.get(f2_id, {}).get('style', 'Balanced') if self._game_state else 'Balanced'
+                    _bl_bump("site_17688_assemble_prefight_s1", s1, _STYLE_STR_MAP)
+                    _bl_bump("site_17689_assemble_prefight_s2", s2, _STYLE_STR_MAP)
                     fs1 = _FightingStyleEnum(_STYLE_STR_MAP.get(s1, 'BALANCED'))
                     fs2 = _FightingStyleEnum(_STYLE_STR_MAP.get(s2, 'BALANCED'))
                     style_mod = get_style_matchup_modifier(fs1, fs2)
@@ -18364,6 +18404,7 @@ class GameBridge:
                 _fd = (self._game_state._fighter_data.get(_fid, {})
                        if (self._game_state and _fid) else {})
                 _raw = str(_fd.get('style', '') or '')
+            _bl_bump("site_18367_resolve_gameplan", _raw, _STYLE_TO_CANONICAL)
             _canonical = _STYLE_TO_CANONICAL.get(_raw, _raw)
             if _tend_on:
                 _pers = str(getattr(_record, 'personality', '') or '')
@@ -22262,6 +22303,7 @@ class GameBridge:
                 }
                 _raw_style = str(
                     getattr(amateur, 'fighting_style', '') or '')
+                _bl_bump("site_22265_sign_amateur", _raw_style, _LEGACY_STYLE_REMAP)
                 _canonical_style = _LEGACY_STYLE_REMAP.get(
                     _raw_style, _raw_style if _raw_style else 'Balanced')
                 # Post-Phase-C amateurs come in with canonical styles

=== RUN A — real world, fresh new_game + 10 live weeks (counters reset post-new_game) ===
bridge-label counters per site:
  site_17404_make_fighter_attrs:
    total conversions: 15832
    fallbacks taken: 0
    raw labels that fell back: {}
  site_18367_resolve_gameplan:
    total conversions: 15832
    fallbacks taken: 15832
    raw labels that fell back: {'BJJ Specialist': 2369, 'Pressure Fighter': 1006, 'Wrestler': 3018, 'Counter Striker': 1363, 'Clinch Fighter': 2362, 'Ground & Pound': 3477, 'Muay Thai': 510, 'Sprawl & Brawl': 306, 'Balanced': 306, 'Point Fighter': 153, 'Striker': 962}
  site_7467_convert_real_fighter:
    total conversions: 256
    fallbacks taken: 256
    raw labels that fell back: {'Balanced': 256}

engine _STYLE1_LABEL_COUNTER per fe module object:
  fight_engine: {'missing': 0, 'unmapped': {}}
  simulation.fight_engine: {'missing': 0, 'unmapped': {}}

=== RUN B — control planted in the real path ===
[RUN B] current week = 0
[RUN B] plant_week=1, card has 9 fights
[RUN B] f1_id=e9969da2 (from fight 0 slot 1)   f2_id=9c4b40f2 (from fight 1 slot 1)
[RUN B] BEFORE planting:
  f1 (Eduardo Magalhaes): record.fighting_style='BJJ Specialist'  fdata['style']='BJJ Specialist'
  f2 (Leandro Pereira): record.fighting_style='BJJ Specialist'  fdata['style']='BJJ Specialist'
[RUN B] AFTER planting:
  f1: record.fighting_style=None  fdata['style']=None
  f2: record.fighting_style='Not A Style'  fdata['style']='Not A Style'

--- RUN B result ---
plant_week: 1  weeks_done: 1
f1_id: e9969da2 (Eduardo Magalhaes)  fought on plant week: True
f2_id: 9c4b40f2 (Leandro Pereira)  fought on plant week: True

engine received style for each planted fighter (per _make_fighter_attrs call):
  e9969da2: 51 calls; unique enum values = ['BALANCED']
  9c4b40f2: 51 calls; unique enum values = ['BALANCED']

engine _STYLE1_LABEL_COUNTER per fe module object:
  fight_engine: {'missing': 0, 'unmapped': {}}
  simulation.fight_engine: {'missing': 0, 'unmapped': {}}

bridge-label counters per site:
  site_17404_make_fighter_attrs:
    total=2318  fallback=102
    fallback_labels: {'None': 51, 'Not A Style': 51}
  site_18367_resolve_gameplan:
    total=2318  fallback=2318
    fallback_labels: {'': 51, 'BJJ Specialist': 904, 'Not A Style': 51, 'Pressure Fighter': 153, 'Wrestler': 452, 'Counter Striker': 102, 'Clinch Fighter': 51, 'Ground & Pound': 554}
  site_7467_convert_real_fighter:
    total=33  fallback=33
    fallback_labels: {'Balanced': 33}
