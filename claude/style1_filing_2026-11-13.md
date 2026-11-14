# STYLE1 - Phase 0 through Gate 0b filing (2026-11-13, architect thread)

Status: NOTHING BUILT. No tracked file changed in this arc. Every measurement
below was taken at code state 27b928474a51e542d62877f5983783b0f847a8c5, either
read-only or in the sandbox worktree /tmp/cd-exp-style1-sandbox1. This filing
also records the SUB-RATE1 rulings and carried state that had not been filed.

## 0. PROVENANCE - read this before any number

Three kinds of claim appear below, and each is tagged.

- FILE: the architect seat read the report file itself in this thread. The
  four STYLE1 reports were hashed in the architect seat and again on disk by
  cc; all four matched.
- CARRIED: taken from claude/handoff_style1_2026-11-13.md, which is committed
  verbatim next to this filing. That handoff records the SUB-RATE1 live-dose
  run and rounds 4b-6 as read by an earlier architect thread. This seat did
  NOT re-read those reports.
- TRANSCRIBED: section 6, copied from the 2026-11-12 architect thread's
  handoff as it displays in chat. No byte-level original was available.

outputs/ is untracked by convention. The reports are pinned by sha256:

    39c96e1c0acb52cf484eafec50995f05af5ed8ed7af2a5e7ccf0cd002aee3297  outputs/style1_phase0.txt
    295968ca746abf0bbdf3776c0316fe4e224da52f446c63d5154997c467188c4b  outputs/style1_round2.txt
    da0455cee412696ff2e7d38cf4d5080e521225828e5784210e4d1e3a386b366d  outputs/style1_gate0.txt
    3492c46a706e6747d1427e64ad8468cc724519cc1ec86077d4e385f621d4c68a  outputs/style1_gate0b.txt
    99afe405127d8dddce32e4b7011a53ec5345bbbb7ea5a4e720e65914613dd6b0  outputs/sub_rate1_live_confirm.txt
    5eb657a011756133d63a398b57f13295b8f69bd920ca3ae5fc0f907c30d8c0f0  outputs/sub_rate1_live_dose.txt
    7c68fc3106d612a242c7f569819f74c72420846d37f95778e6f6cf31fd12edb0  outputs/sub_rate1_phase1_prep.txt
    b3f0e8293d18372964c97e53c0977215508310d69757e726e9aa3182afbe54f9  outputs/sub_rate1_phase1b.txt
    7846f0525b40f4b2718fc0d9b9ce1dc8416e7a6a9c7f4333d62374266c472260  outputs/sub_rate1_round4b.txt
    2d97ee101d36404ed3ab834086fff4e4b92baf7f780a3df5dd7790737f11dd1b  outputs/sub_rate1_round5.txt
    da2a22901eb57c1e3eebf3faac165086ee845981770ad59b20d3f5de606c642f  outputs/sub_rate1_round5b.txt
    4242bf8874e9c7fce3b6c18f476ead47535c63f07c19062d7900bb0056da4e8c  outputs/sub_rate1_round5c.txt
    a14eec62ac0dd8317067e3eacd94b11f83809804527726dcac75c4b23d6bd2a7  outputs/sub_rate1_round6.txt
    76965b3d9f242a2225a8e561121ee82b2a7cd1aede7f6672704f9fd44dde1bd4  outputs/sub_rate1_sandbox.txt
    0726d4009b3cd64319592a6b62f8c56656e3ed87f9931d844b040c3a2024bfef  outputs/sub_rate1_sandbox2.txt
    f9d86e878fab6253a60d06dcd3f7ff9bff5f63cc4c06440f9b3d27b7163ea4a9  outputs/sub_rate1_sandbox3.txt

The twelve sub_rate1 hashes were copied by the architect seat from cc's
terminal output; the commit gate recomputes them.

The fixed instrument (one save, 293 fighters, 1080 in-division pairs, five
seed sets, 5400 fights per arm):

    99a1b3191c54386a7f568e858feecc1386b33ebe155c96f233daac3aeb628f78  /tmp/sub_rate1_phase1b_saves/bridge_sub_rate1_phase1_base.json  (5,183,441 bytes)
    da494a8740322df2fbe1fa072b47e81e80e40769d2dd18a9f3b65428659a666c  outputs/sub_rate1_phase1_pairs.json  (45,400 bytes)
    baseline, dials off, seed set 1: 48fc32af744c37b24b5099c97c9a88795e904e2d33d7bf35f5d38dfc850235f1

The save lives in /tmp, which is not durable. A file of the same size exists at
cage_dynasty_web/saves/bridge_sub_rate1_phase1_base.json (gitignored). Whether
the two are byte-identical was NOT measured at filing time.

## 1. RULINGS (Van)

2026-11-12 (CARRIED; the 16-20% target was already filed)
- Injury-sub finish type REMOVED: locks past the band resolve as tap; injuries
  come from the normal injury system.
- The cut comes from non-specialists; BJJ Specialists keep their identity.
- Specialist floor: >= 60% of BJJ Specialist wins by SUB, provisional.

2026-11-13 (CARRIED)
- "Specialist" means the BJJ Specialist fighting_style label, not the engine's
  detected base. Sambo base is a middle tier: below BJJ, above a plain Wrestler.
- One style system: the label the player sees is the brain the engine runs.
- Primary style plus an EARNED secondary style: liked; not scoped.
- Timing delegated to the architect seat; STYLE1 became the next work item.

2026-11-13 (this thread)
- THE STORED LABEL IS THE ONE JUDGE. The engine fights by the fighting_style
  label on the profile, not by a separately detected style.
- SAMBO IS ITS OWN VISIBLE FIGHTING TYPE, not a combination of Wrestler + BJJ.
  This supersedes, going forward, the Sambo -> Wrestler conversions at
  game_bridge.py:455, :17371 and :22254. The comment at :22246-22247 marks the
  :22254 mapping "Van RATIFIED mapping 2026-09-05".
- The docs commit goes before any engine work.

NOT RULED
- Method-mix targets (architect proposal: SUB 16-20, KO/TKO 34-40, DEC 42-48,
  finish 52-58).
- How the 60% floor is restated once label = brain.
- Pausing SUB-RATE1 tuning and folding it into method-mix tuning on the new
  system (architect recommendation; Van proceeded without objecting).
- Queue order of SLOW-WEEK1 -> money probe -> VENUE-US1 relative to STYLE1.
- Review points: whether and when a fighter's label is re-derived after
  creation (section 3, item 12).
- The Sambo label rule, its submission weights, and its roster share.

## 2. MEASURED - STYLE1 (FILE)

### 2a. Phase 0 (outputs/style1_phase0.txt)

- Two rules classify every fighter from the same stats: the stored label and
  detect_fighter_style. Stored label x detected style, 293 fighters: the
  diagonal holds 153, so 140 differ. The report's "agree=171 disagree=122" uses
  a loose rule that counts Wrestler label + sambo detect as agreement.
- Detected styles: sambo 69, bjj 40. Of 28 BJJ Specialist labels: 18 detect as
  bjj, 8 as sambo, 2 as point_fighter. Labels of the 69 sambo detects: Wrestler
  18, Ground & Pound 17, BJJ Specialist 8, Counter Striker 5, Clinch Fighter 5,
  Pressure Fighter 5, Sprawl & Brawl 4, Muay Thai 4, Striker 2, Point Fighter 1.
- Which branch of detect returned: primary 122, hint_fallback 102, secondary
  49, balanced_default 12, balanced_gate 8. For 102 fighters the detected style
  is the stored label.
- Fighters with OVR >= 70: 52. By detected style: sambo 39, balanced 6,
  ground_and_pound 3, bjj 2, clinch_fighter 1, muay_thai 1. By highest
  composite: bjj 16, defense 13, striking 9, wrestling 7, clinch 7.
- Highest composite among the 69 sambo detects: wrestling 23, bjj 22, defense
  10, striking 7, clinch 6, pressure 1. Wrestling and bjj are the top two, in
  either order, for 27.
- Control: dials off, seed set 1, full hash equal to the baseline hash. PASS.
- T1 (sambo returns also require wrestling and bjj to be the two highest of
  SIX composites) and T2 (T1 plus each grappling return requires its own
  composite to be highest). Measurements, not ship candidates.

      arm       SUB%    TKO%    KO%    DEC%    finish%  per-seed SUB%
      baseline  28.04   33.96   0.48   36.31   62.48    26.7-30.1
      T1        23.65   37.56   0.65   36.87   61.85    22.2-24.9
      T2        23.02   38.78   0.69   36.04   62.48    21.6-23.9

- T1 moved 42 of the 69 sambo detects: 22 to muay_thai, 8 wrestler, 6
  sprawl_and_brawl, 3 clinch_fighter, 2 pressure_fighter, 1 counter_striker.
  Those 42, baseline -> T1 over 1500 appearances: wins 1276 -> 1242 (85.07% ->
  82.80%), SUB 467 -> 233, TKO 583 -> 773, DEC 219 -> 220.
- The 27 that stayed sambo under T1: mean OVR 66.48, 760 of 990 won (76.77%),
  485 SUB wins (63.82% of wins). Baseline sambo, all 69: mean OVR 71.07, 2036
  of 2490 (81.77%), 957 SUB wins (47.00%).
- BJJ Specialist label, SUB share of wins: baseline 488/670 = 72.8%; T1 461/668
  = 69.0%; T2 464/671 = 69.2%.
- Sub picks per fight, mean / p95 / max: baseline 1.50 / 7 / 42; T1 1.23 / 6 /
  42; T2 1.22 / 6 / 41.
- FightingStyle (core/types.py:32-43) has 11 members and no SAMBO.
  game_start.FIGHTING_STYLES (:66-80) is a separate 12-name list that includes
  "Sambo"; the pick from it at :645 only shapes stats.
- detect_fighter_style call sites in cage_dynasty_web/ outside tests:
  fight_engine.py:1666, :2017-2018, :3998-3999.

### 2b. Round 2 (outputs/style1_round2.txt)

Arms: L1 = detected style replaced by the stored label. L2 = L1, except sambo
when wrestling and bjj are the two highest of the FOUR discipline composites
and pass 72 / 68. L3 = baseline ladder with the sambo returns also requiring
that same four-composite test. Every arm-seed printed sim=1080.

      arm       SUB%    TKO%    KO%    DEC%    finish%  per-seed SUB%   changed  sambo
      baseline  28.04   33.96   0.48   36.31   62.48    26.67-30.09     -        69
      L1        21.24   38.83   0.56   38.02   60.63    20.00-22.59     140      0
      L2        23.00   37.76   0.54   37.41   61.30    21.94-24.91     116      24
      L3        24.54   36.89   0.65   36.65   62.07    23.06-26.02     34       35

SUB share of wins by stored label (SUB wins / wins):

      label            baseline          L1                L2                L3
      BJJ Specialist   488/670  72.84%   494/673  73.40%   494/672  73.51%   461/666  69.22%
      Wrestler         399/912  43.75%   343/932  36.80%   384/939  40.89%   374/915  40.87%
      Ground & Pound   328/996  32.93%   186/1012 18.38%   227/1007 22.54%   272/989  27.50%
      Pressure Fighter  74/395  18.73%    14/377   3.71%    14/377   3.71%    38/388   9.79%
      Counter Striker   68/591  11.51%    30/582   5.15%    37/579   6.39%    60/591  10.15%

Win rate by OVR band (wins / appearances):

      band    baseline            L1                  L2                  L3
      <60     1925/6295 30.58%    1951/6295 30.99%    1953/6295 31.02%    1940/6295 30.82%
      60-69   1795/2675 67.10%    1761/2675 65.83%    1758/2675 65.72%    1797/2675 67.18%
      70+     1615/1830 88.25%    1615/1830 88.25%    1619/1830 88.47%    1594/1830 87.10%

Sub picks per fight, mean / p95 / max: baseline 1.50 / 7 / 42; L1 1.07 / 5 /
51; L2 1.22 / 6 / 41; L3 1.30 / 6 / 42.

Controls. C1 (dials off, seed set 1, full hash): PASS. C2 (count of fighters
whose detected style changes under L1, predicted from the Phase 0 crosstab vs
computed from the patched engine): the first run printed 242 vs 140 and
failed. cc edited the driver three times, all the same normalization of a
display string ("Counter Striker") to the enum-name form ("COUNTER_STRIKER"),
re-ran, and C2 printed 140 = 140. The report's addendum states the engine patch
was not edited between the runs. The arms ran after that re-run and before the
architect seat or Van saw the failure. The first run's output is not in the
report file; the file begins at 15:34:00.

Why 140 is accepted: the architect seat counted 140 from the Phase 0 crosstab
before round 2 ran; the display-string bug reproduces 242 exactly from the same
crosstab; and the L1 detected-style counts equal the Phase 0 label row totals.

Not established: the driver holds its own copy of the detect ladder. C2
compared L1 only. Whether the L2 and L3 "changed" and "sambo" columns came from
that copy or from the patched engine was not checked. The method-mix, by-label
and OVR-band tables come from fight records and do not depend on it.

Player creation: game_start.py:570 overwrites the picked style with the derived
label; :704 passes it on; game_bridge.py:2695 stores it.

### 2c. Gate 0 and Gate 0b (outputs/style1_gate0.txt, outputs/style1_gate0b.txt)

1. The label multiplies action weights in every select_action call:
   _STYLE_WEIGHTS at fight_engine.py:2388-2407, read by label at :2409-2439,
   applied with int() at :2441-2443. Submission multipliers: BJJ_SPECIALIST
   2.0, SAMBO 1.4, BALANCED 1.0, WRESTLER 0.9, JUDO 0.9, HYBRID 0.8,
   CLINCH_FIGHTER 0.7, GROUND_AND_POUND 0.6, MUAY_THAI / PRESSURE_FIGHTER /
   SPRAWL_AND_BRAWL / BRAWLER 0.4, STRIKER / COUNTER_STRIKER / ORTHODOX_BOXER /
   KICKBOXER / KARATE 0.3, POINT_FIGHTER 0.2. A missing key gets 1.0 across.
2. The same 18-row table is repeated at fight_integration.py:154-173. What
   reads that copy was not established.
3. Seven label reads in fight_integration.py, each a substring test on the
   upper-cased label: :1312 'COUNTER', :1381 'MUAY_THAI', :1443 'BRAWLER',
   :1468 'POINT', :1585 'GROUND', :1896-1897 'SAMBO' and 'JUDO', :1946
   'SPRAWL'. No FightingStyle member contains BRAWLER, SAMBO or JUDO.
4. The label reaches the engine through _make_fighter_attrs
   (game_bridge.py:17383-17459): style_str is read from _fighter_data["style"]
   first and record.fighting_style second (:17403), mapped through _STYLE_MAP
   (:17354-17381, default "BALANCED" at :17404) and passed as a FightingStyle
   member (:17407, :17458). _STYLE_MAP sends "Sambo" and "Judo" to WRESTLER.
5. Sambo is converted to Wrestler in three places: _STYLE_TO_CANONICAL
   (game_bridge.py:455), _STYLE_MAP (:17371), _LEGACY_STYLE_REMAP at amateur
   signing (:22254).
6. Sambo already has rows in: _STYLE_WEIGHTS (both copies), the detect hint
   map (fight_engine.py:1837), _STYLE_OVR_WEIGHTS (game_bridge.py:7873-7878),
   POWER_STYLE_OFFSET (core/types.py:145, -4), game_start.style_bonuses (:493).
   It has none in: the FightingStyle enum, the label rule's scores dict
   (world_init.py:1479-1490), STYLE_MATCHUPS (styles.py:210),
   _AI_STYLE_TO_GAMEPLAN (styles.py:613), _STYLE_AGGR_TILT (styles.py:674),
   _STYLE_RANGE_TILT (styles.py:692), _STYLE_AFFINITY (game_bridge.py:8186),
   STYLE_OFFENSE_HINTS (:979), style_tendencies (:13445), STYLE_THREATS
   (:13628), and four tables in narrative/commentary.py (:86, :242, :297,
   :1152).
7. Fallbacks on a missing key: _STYLE_OVR_WEIGHTS -> the Balanced row
   (game_bridge.py:7966-7967); STYLE_MATCHUPS -> 0.0 (styles.py:394-395);
   _AI_STYLE_TO_GAMEPLAN -> "BALANCED" (styles.py:646); the two tilt tables ->
   0 (styles.py:730, :732); _STYLE_AFFINITY -> {} (game_bridge.py:8202);
   STYLE_OFFENSE_HINTS -> {} (:1012); STYLE_THREATS -> a generic pair (:13641).
   style_tendencies is subscripted directly at :13456; any guard above it was
   not shown.
8. OVR is style-weighted. _compute_ovr reads record.fighting_style
   (game_bridge.py:7964) and weights the stats by the label's row.
9. The label rule (world_init.py:1413-1557): template fighters take the
   template's style; otherwise argmax over ten scores, each a signature stat
   x 3.0 (BJJ Specialist x 2.7, Pressure Fighter x 2.5, Point Fighter x 2.7)
   plus supporting stats; a country-favored style gets x 1.05 (:1503-1514);
   "Balanced" when the top score is within 8% of the second, the four family
   means are within 12, and the top signature stat is under 72.
10. Callers of the label rule: world_init.py:1362 (pros), :1743 (thin delegate
    used by amateur.py:731-737), game_start.py:552 (player prospects).
11. Pre-generation history fights pass no label. The FighterAttributes call at
    world_init.py:2064-2093 has no fighting_style argument, so the engine's
    label reads see None there.
12. No write of fighting_style appears in a training, aging or weekly-advance
    function among the 43 write sites listed in Gate 0 R4. This is the
    architect seat's reading of that list; the report gave no verdict.
13. At new game, a record with an empty label gets a seeded random style from
    _STYLE_POOL (game_bridge.py:2484-2493). How many fighters take that branch
    in a real world was not measured.
14. Web-app imports of the engine resolve to cage_dynasty_web/fight_engine.py
    through the shim in cage_dynasty_web/simulation/__init__.py. No web-app
    import of the top-level systems/ or simulation/ engine copies was found.
15. models.py: _generate_fighters is called only at models.py:427 and :1146.
    Whether anything live constructs the class that owns them was not checked.

## 3. ARCHITECT ARITHMETIC AND READINGS - not measurements

- The 42 fighters T1 moved off sambo average about 74 OVR:
  (69 x 71.07 - 27 x 66.48) / 42.
- 19 of the 69 sambo detects have defense or pressure among their top two
  composites; T1 excluded them for that reason.
- Under L1, Wrestler + BJJ Specialist + Ground & Pound labels hold 1023 of 1147
  SUB wins (89%). If Wrestlers fell to about 20% of wins by SUB and nothing
  else moved, the pooled rate would be near 18%. Not measured.
- A 5% country boost on a score near 280 is worth roughly four to five points
  on the signature stat. How many labels it decides was not measured.
- Readings: the sambo test in detect behaves as a high-rating test (39 of the
  52 fighters at OVR 70+). The detected style changed how the moved fighters
  won, not how often. Both are trends on one roster.

## 4. FALSE AS WRITTEN - this thread (kept, not dropped)

cc terminal summaries
1. Phase 0: sambo top-two "wrestling -> bjj: 20, bjj -> wrestling: 22". The
   report says 14 and 13.
2. Phase 0: "Roster OVR >= 70 (n=103): sambo 39, bjj 15, balanced 11 ...". The
   report says n=52: sambo 39, balanced 6, ground_and_pound 3, bjj 2.
3. Phase 0: "FightingStyle enum: 12 members including SAMBO, ORTHODOX_BOXER,
   KICKBOXER, KARATE, BRAWLER, SUBMISSION_ARTIST". The enum has 11 members and
   none of those; the 12 names are game_start.FIGHTING_STYLES.
4. Phase 0: detect call sites "fe:4288 simulate_exchange, fi:3185". Neither is
   in the report.
5. Phase 0: BJJ Specialist label share "T1 ~488/670, T2 ~488/670 (label
   unchanged by patches)". The report says 461/668 and 464/671.
6. Phase 0: sub picks "T1 1.27 / 6 / 42; T2 1.23 / 6 / 38". The report says
   1.23 / 6 / 42 and 1.22 / 6 / 41.
7. Phase 0: "Both controls satisfied in context". The report prints
   "fi:1893 reads fighting_style: False"; the control as written failed.
8. Round 2: "the patched detect returned HEAD ladder results instead of the L1
   hint-only returns". The patched engine was right; the driver's prediction
   was wrong.
9. Round 2: "BJJ Specialist label SUB-share is essentially unchanged across
   arms (patch touches detected brains, not stored labels)". The report says
   72.84 / 73.40 / 73.51 / 69.22.
10. Round 2: sub picks "L1 1.17, L2 1.26, L3 1.30 (p95 6-7, max 42 all)". The
    report says L1 1.07 / 5 / 51 and L2 1.22 / 6 / 41.
11. Round 2: "the SUB drop comes from mid-OVR fighters who lose sambo weights
    at BACK_MOUNT / LEG_ENTANGLEMENT". No table in the report supports it.
12. Gate 0b: "models.py is dead". Not established (section 2c, item 15).
13. Gate 0b: the fight_integration.py:154 table "is never referenced outside
    its own declaration line". The report prints "table name: <unknown>" and
    lists no references.

Report files
14. Phase 0 A3: "player creation CAN produce any FightingStyle enum value shown
    to the user". The grep under it is blank; round 2 A3 shows the stored label
    is the derived one.
15. Phase 0 A2b: hits tagged display or logic by file name; 245 hits counted,
    a subset listed. Superseded by Gate 0 R2.
16. Round 2 header: "report: append-only". The first run's output is absent.
17. Gate 0 R5: "game_bridge.py:17436 ... fighting_style passed? NO". Line
    :17458 passes it. Every R5 yes/no flag was computed on a cut-off window.
18. Gate 0 R6: no verdict given.

Inventory run
19. Step 3, first pass: four MATCH lines printed while each shasum call
    returned "command not found". cc re-ran with direct calls and printed the
    four hashes, equal to the pre-registered values.

Carried handoff (claude/handoff_style1_2026-11-13.md)
20. "the stored fighting_style is only a last-resort hint". False: section 2c
    items 1 and 3, and 102 of 293 detected styles are the label.
21. Proposed slice 2, "Label = brain: store the detected style; hash-neutral".
    Superseded by the 2026-11-13 ruling that the label is the judge. Label-as-
    brain is a measured change (L1), not a neutral one.
22. Round 6 item "FightingStyle.SAMBO is never assigned by the generator ...
    UNVERIFIED until Phase 0 A3". Resolved: the enum has no SAMBO member and
    the label rule has no 'Sambo' score.

## 5. ARCHITECT-SEAT ERRORS - this thread

- T1 was specified as "the fighter's two highest composites" without naming
  the composites. cc used six, including defense and pressure.
- The round 2 prompt did not require the brain census to come from the patched
  engine for every arm.
- Gate 0b B1 did not ask for the function enclosing fight_integration.py:154,
  and B7 asked for callers when the question was whether models.py is live.

## 6. FALSE AS WRITTEN - 2026-11-12 thread (TRANSCRIBED)

- Phase 1: CONTEST_P_EVEN / EDGE20_TARGET "SHARED across all 13 classes". They
  are per-class (fe:2771-2788).
- Phase 1b B6: "gap=1, no cooldown". The t column was the event index.
- Phase 1b summary: "1 live call at game_bridge.py:18514". Comments only.
- Phase 1b C4 summary: heart trend "monotonic". 40.0 / 20.9 / 23.3 / 13.9.
- Phase 1b "noise floor 1.30pp": too small; seed sets span 26.7-30.1%.
- Round 3 Step 1a first pass: "separation is tiny" printed from zero events.
- Round 3 Step 1b first pass: "blocked=0" from a dead counter.
- Round 2 hook probe: "hook is a no-op" was a harness import-path artifact.
- All "RUNTIME DIALS" readbacks before the round 3 worker fix read a stale
  module object (game_bridge.py:213-216 deletes and re-imports the engine
  modules). Hashes and outcomes, not the readback, are the proof dials took
  effect.
- Phase 1 pair-list sha 77a18bda... does not match the file (da494a87...). cc
  labelled it false; the cause is UNEXPLAINED.

The twelve further items from the 2026-11-13 thread (live dose, rounds 5-6)
are in the carried handoff, section 4.

## 7. OPEN

- The Sambo label rule; its effect with the SAMBO throw routing
  (fight_integration.py:1896 onward) and the takedown-to-submission chain (the
  carried handoff places it at fi:1182-1198, armed at fi:1935) reachable for
  the first time; its roster share; the generator's share gates.
- Review points (section 2c, item 12).
- Pre-generation fights and the label (item 11). claude/backlog.md
  HISTORY-METHOD-GAP records pre-gen lineages as almost all TKO; no link to
  item 11 has been measured.
- Two stores of the label (item 4): no check that they agree for every fighter.
- The random-style fallback count (item 13).
- Whether models.py is live (item 15); what reads fight_integration.py:154.
- The L2 / L3 census source (section 2b).
- Whether the /tmp instrument save equals the copy in cage_dynasty_web/saves/.
- Everything under OPEN in the carried handoff, section 5.

## 8. BACKLOG ROW CANDIDATES - none filed by this commit

From the carried handoff: doctor-stoppage flush skip; sub-attempt spam; KO
label; weight-class finish gradient; int() truncation on sub_weight modifiers;
harness injury counter.

New in this thread:
- Sub-attempt maximum rises to 51 in one fight under L1.
- _STYLE_AFFINITY has seven keys; Muay Thai, Clinch Fighter, Sprawl & Brawl and
  Point Fighter train with no style affinity.
- _STYLE_WEIGHTS carries rows no label can reach through _STYLE_MAP
  (ORTHODOX_BOXER, KICKBOXER, KARATE, JUDO, BRAWLER, HYBRID, SAMBO), and the
  table is duplicated in fight_integration.py.
- The 'BRAWLER' branch at fight_integration.py:1443 cannot fire.

## 9. SEQUENCE

1. This docs commit (Van, 2026-11-13).
2-5 are the architect seat's recommendation, not rulings:
2. One judge: the engine fights by the label; pre-generation fights pass it.
3. Sambo: sandbox for the label rule with the SAMBO branches reachable, then
   the table rows. Deploys together with 2.
4. Review points.
5. Method-mix tuning on the new system; SUB-RATE1 closes there.

## 10. TEXT THIS COMMIT APPLIES TO OTHER FILES

Each item below is exactly one line of this file. The commit prompt copies the
lines by number.

A. Appended to the end of the SUB-RATE1 row in claude/backlog.md, after one space:
Addendum 2026-11-13: rulings (Van, 2026-11-12) — injury-sub finish type removed (locks past the band resolve as tap; injuries come from the normal injury system); the cut comes from non-specialists, BJJ Specialists keep their identity; specialist floor ≥ 60% of BJJ Specialist wins by SUB, provisional. Ruling (Van, 2026-11-13): "specialist" = the BJJ Specialist fighting_style label. Fixed-population baseline 28.04% SUB over 5400 fights (five seed sets, 26.7–30.1%); no candidate through round 6 reached 16–20% (carried, claude/handoff_style1_2026-11-13.md). Tuning is paused behind STYLE1 on the architect seat's recommendation, not a ruling. Nothing built.

B. New row inserted directly after the SUB-RATE1 row in claude/backlog.md:
- **STYLE1** [filed 2026-11-13, MEASURED sandbox + READ] — one style system. Two rules classify every fighter from the same stats: the stored fighting_style label (world_init._phase_b_derive_style, set at creation) and detect_fighter_style (fight_engine.py:1808, run inside each fight); they differ for 140 of 293 fighters on the fixed population. Rulings (Van, 2026-11-13): the stored label is the one judge — the engine fights by the label; Sambo is its own visible fighting type, which supersedes going forward the Sambo→Wrestler conversions at game_bridge.py:455, :17371 and :22254 (the last marked ratified 2026-09-05). Sandbox, 5400 fights, baseline 28.04% SUB: label-as-brain 21.24% (per-seed 20.00–22.59%), BJJ Specialist 73.40% of wins by SUB, OVR 70+ win rate 88.25% in both arms. Pre-generation history fights pass no label to the engine (world_init.py:2064-2093). Nothing built. Filing claude/style1_filing_2026-11-13.md. Next (architect recommendation): one-judge engine slice; Sambo label-rule sandbox.

C. Two lines inserted directly after CLAUDE.md line 609:
- `claude/style1_filing_2026-11-13.md` — STYLE1 Phase 0 → Gate 0b filing (sandbox + read-only, nothing built): stored label vs detect_fighter_style differ for 140 of 293; label-as-brain 21.24% SUB vs 28.04% baseline on the fixed population; rulings 2026-11-13 (label is the one judge; Sambo is its own visible type); SUB-RATE1 rulings 2026-11-12/13; 22 false-as-written items; reader and table census for fighting_style
- `claude/handoff_style1_2026-11-13.md` — architect handoff, committed verbatim as history (SUB-RATE1 live dose and rounds 4b–6, rulings, false-as-written list); carried state, not re-verified
