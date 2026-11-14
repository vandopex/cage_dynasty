New thread — Cage Dynasty architect seat. Treat this as potentially stale: read
git log first. HEAD was 27b9284 when written. NOTHING was committed in the prior
thread or the one before it. PA was reported at a19a921 two handoffs ago; never
re-verified.

==========================================================================
1. IN FLIGHT, UNCOMMITTED
==========================================================================
- cc is running "STYLE1 Phase 0" (prompt sent 2026-11-13 ~15:00 PT).
  Report: outputs/style1_phase0.txt. Worktree: /tmp/cd-exp-style1-sandbox1.
  PART A, read-only census:
    A1 crosstab stored fighting_style x detect_fighter_style; which branch of
       detect returned, per fighter
    A2 every reader of fighting_style / caller of detect_fighter_style in the
       whole repo incl. narrative/; positive control must find fe:2017, fi:1893
    A3 FightingStyle enum members; generator + player-creation code that sets
       fighting_style; which members each can produce
    A4 detected-style changes week 0 -> week 90, only if round 4 JSONs hold
       snapshots
    A5 sambo and bjj brains by (highest, second-highest composite); OVR >= 70
       fighters by brain and by highest composite
  PART B, sandbox on the fixed population:
    Control: dials off, s1 -> hash 48fc32af744c37b24b5099c97c9a88795e904e2d33d7bf35f5d38dfc850235f1
    T1 sambo guard: both sambo returns (fe:1856, fe:1918) also require
       wrestling and bjj to be the fighter's two highest composites
    T2 = T1 + each grappling return also requires its own composite to be
       the fighter's highest
    These are measurements, not ship candidates.
- Untracked in outputs/ (reports, scripts, JSONs): everything named
  sub_rate1_* from Phase 1 through round 6, plus style1_phase0.* when done.
  New this thread: sub_rate1_live_dose.txt, _round4b.txt, _round5.txt,
  _round5b.txt, _round5c.txt, _round6.txt (383 lines after an appended
  addendum; the architect seat read lines 1-281 only).
- Worktrees alive (remove only on Van's word):
  /tmp/cd-exp-sub-rate1-{injury-off,sandbox,sandbox2,sandbox3,sandbox4,
  sandbox5,sandbox6}, /tmp/cd-exp-style1-sandbox1, and
  /private/tmp/p5a_pristine_c28 (prunable, unrelated).
- DO NOT DELETE /tmp/sub_rate1_phase1b_saves while fixed-population work
  continues. The round 5/6 workers default SB_SAVES_DIR to it (uid
  sub_rate1_phase1, slot base). It is the fixed instrument's save.
- Still in the REAL cage_dynasty_web/saves/ (gitignored, a prompt violation
  from Phase 1): bridge_sub_rate1_phase1_base.json.

==========================================================================
2. VAN'S RULINGS (none are in claude/backlog.md yet)
==========================================================================
2026-11-12
- Target: 16-20% SUB on the live path over >= 1000 unique fights.
- Injury-sub finish type REMOVED: locks past the band resolve as tap;
  injuries come from the normal injury system.
- The cut comes from non-specialists; BJJ Specialists keep their identity.
- Specialist floor: >= 60% of BJJ Specialist wins by SUB, provisional.
2026-11-13
- "Specialist" = the BJJ Specialist fighting_style label, not the engine's
  detected base. Sambo base is a middle tier: below BJJ, above a plain
  Wrestler. (Van: "i dont know much, but ill go with your rec".)
- STYLE SYSTEM: Van is sold on one system where the label the player sees is
  the brain the engine runs. His words: what we have "is stupid and defeats
  the purpose of half of what is created"; "make a smart system"; other
  systems may need looking over too, "specially fight engine, commentary".
- MULTI-STYLE: Van "loves" primary + earned secondary style. He has long
  wanted fighters to be able to learn more than one style.
- TIMING: delegated to the architect seat ("add it when you think it fits
  best and we can discuss more at that point"). Architect answer: now, as
  the next work item. Van sent the Phase 0 prompt.

NOT RULED (do not treat as decided)
- Method-mix targets. Architect proposal: SUB 16-20, KO/TKO 34-40,
  DEC 42-48, finish 52-58.
- Whether Sambo becomes a visible type (implied by the one-system ruling;
  not said in so many words).
- How the 60% specialist floor is restated once label = brain. Labelled BJJ
  Specialists sub 72.8% of wins; all bjj-brain fighters sub 37.3%.
- Pausing SUB-RATE1 tuning and folding it into method-mix tuning on the new
  style system. Architect recommendation; Van proceeded without objecting.
- Pushing SLOW-WEEK1 -> money probe -> VENUE-US1 behind STYLE1. Flagged to
  Van as his queue; no answer.
- Should a non-specialist with sub weight 1-2 keep a small chance or go to
  zero. Asked; superseded by events; unanswered.
- Can a player see a fighter's base discipline anywhere? Asked twice;
  unanswered.

==========================================================================
3. WHAT WAS MEASURED ("file" = architect read the report itself)
==========================================================================
Fixed instrument (file): one save, 293 fighters, 1080 in-division pairs,
5 seed sets (offsets 0 / 10M / 20M / 30M / 40M), 5400 fights per arm,
~25 s per arm-seed. Baseline hash above. Baseline pooled: SUB 28.04%,
TKO 33.96%, KO 26 fights, DEC 36.31%, draws 65, finish 62.48%; per-seed SUB
26.7-30.1%.

Live dose run (file): Step 1 FAILED its gate, Step 2 never ran. THERE IS NO
TEN-WORLD DATA. Within the F arm, post/pre ratio: Wrestler 0.397, G&P 0.377,
BJJ Specialist 1.000. One world is ~700 unique fights and ~60 s for 90 weeks.

Round 4b (file)
- F line is byte-identical in sandbox3 and sandbox4: int(sub_weight * m).
- int() truncation explains the ratio gap exactly (pred = obs to 4 dp).
- The selector (fe:2564-2573) accepts float weights. F sits after the
  max(1, sub_weight) floor at fe:2558 and directly before the choice.
- Sub gate fe:2556-2560: base bjj/sambo need submissions >= 45, everyone
  else >= 60; below the gate sub_weight is forced to 0.
- Injuries on the live path, one world: 46 sub-hook (41 MODERATE, 4 SEVERE,
  1 CAREER) + 185 generate_fight_injury calls vs 232 injury records.

Round 5 / 5c (file), pooled 5400 fights, multiplier 0.4286
  arm                              SUB%   finish%
  baseline                         28.0   62.5
  A  current F (floor off + x m)   21.3   59.0
  B  float x m                     22.8   59.8
  C  floor off only                25.6   61.2
  D  real openings x m only        24.2   60.6
- Baseline sub picks: 1339 FLOOR, 6887 REAL. Picks per fight mean 1.50,
  p95 7, max 42, 294 fights with >= 7.
- SUB wins by detected base, baseline -> A: sambo 957 -> 767, bjj 329 -> 283,
  other 228 -> 102. Sambo base = 63% of all subs. F is mis-aimed.
- Submissions attribute: sambo median 80 (63 of 69 >= 60), bjj median 69,
  other median 49. Only 15 fighters pass on the 45 gate alone (6 SUB wins
  in s1): the gate is immaterial.
- By label, baseline SUB share of wins: BJJ Specialist 72.8, Wrestler 43.8,
  G&P 32.9, Pressure 18.7, Balanced 16.8, Counter 11.5, Clinch 11.2,
  Striker 10.4, Muay Thai 8.0, Sprawl & Brawl 7.6, Point 0.
- By submissions tier (elite >= 80, high >= 65, mid >= 50, low < 50):
  55.8 / 34.0 / 12.1 / 0.

Round 5b (file)
- s1 waterfall: selector picks 1747 = attempts entered 1747 = counter line
  reached 1747. Zero lost, zero gained. SELECTOR PICKS ARE THE ATTEMPT UNIT.
- Engine bug: a between-round doctor stoppage returns at fi:2399-2402 before
  the round-stats flush at fi:2419-2422, so the final round's stats are
  dropped from the fight record. s1: 16 attempts in 7 fights (7 FLOOR,
  9 REAL). s2-s5 gaps (33, 30, 17, 44) are assumed the same cause, not traced.
- Sambo chain (fi:1182-1198, armed at fi:1935) fired 0 times. Its trigger
  needs 'SAMBO' in the stored fighting_style; no fighter in the save has it.

Style facts (file)
- select_action runs on my_style = detect_fighter_style(fighter_attrs)
  (fe:2017). detect (fe:1808-1939) decides from attributes; the stored
  fighting_style is only a last-resort hint.
- detect checks sambo FIRST (wrestling >= 72 and bjj >= 68) and never
  compares striking. bjj requires wrestling < 68.
- 69 fighters detect as sambo, 40 as bjj. Of the 40 bjj brains, 18 carry the
  BJJ Specialist label. 28 fighters carry that label: 18 bjj brain, 8 sambo
  brain, 2 other.
- Sub-weight block fe:2262-2352: bjj/sambo get large adds at low skill
  thresholds; "else" needs submissions >= 85 for comparable adds. Sambo
  exceeds bjj only in leg entanglement (200/120 vs 180/100).

Round 6 (file), sambo sub weights, no multiplier
  S1 sambo takes "else" values      25.4%
  S2 sambo takes the midpoint       27.2%
  S3 = S2 + floor off               25.1%
- BJJ Specialist label gate holds at ~72.8% in every arm.
- Win rate by detected base, baseline: sambo 81.8% (2036/2490), bjj 56.4%,
  ground_and_pound 46.8%, wrestler 44.6%, all other 32.6%. Did not move in
  any arm.

Round 6 addendum (cc narration; NOT read from file)
- Mean OVR by brain: sambo 71.1; bjj 56.0; all others 49-60.
- Sambo vs bjj win rate at matched OVR: 60-69 76% vs 73%; 70-79 tied;
  < 60 64% vs 43% (8 sambo fighters, thin).
- Top-two composite gap: within 5 for 165 fighters (56%), 5-10 for 78,
  > 10 for 50. Top-two bjj/wrestling in either order: 42 fighters.
- Wrestler brains (OVR 49) win 45%; striker / muay thai / pressure / counter
  brains (OVR 51-54) win 27-33%. All groups thin. TREND, not a finding.

Real-world reference (looked up 2026-11-13)
- UFC all-time: KO/TKO 32.6, SUB 19.3, DEC 46.8. UFC 2025: 32 / 18 / 49.
  All tracked promotions 2025: 38 / 15 / 47. UFC finish rate 44% in 2024.
- KO/TKO share runs ~46% at light heavyweight to ~15% at women's
  strawweight (since 2016); SUB share only 13-23% across divisions.

==========================================================================
4. FALSE AS WRITTEN (mark in the filing, do not drop)
==========================================================================
The ten items in the previous handoff's list still stand. Add:
- live_dose Step 0: mc_odds readers "popularity signals, FOTN-candidate
  selection, AI decision helpers". cc's own grep found none. The four hits
  (gb:5498, 14229, 14405, 18725) are payload pass-throughs. The grep covered
  cage_dynasty_web/ only and had no positive control.
- live_dose Step 0: "distinct random sequences produce distinct outcome
  distributions" as the reason for 25.2% vs 28.5%. Wrong reasoning; the gap
  is inside the world-to-world spread. That text was hard-coded in the
  driver, not measured.
- live_dose workers: "injuries=0". Logging was switched off, not a result.
- round 5 Control 3: "should be 0 to a few". The tolerance was cc's; the gap
  is engine-side stat loss, not telemetry.
- round 5 narration: five candidate causes for the gap. None was the cause.
- round 5b diagnostic: "k=721: 4 REAL + 1 FLOOR lost". Only 1 FLOOR was lost.
- round 5c: FLOOR/REAL split by base (sambo = 0 in every arm). Styles were
  assigned to their most common base. Unusable.
- round 5c: baseline expected-picks and floor-call totals were in the spec
  and silently dropped.
- round 6: site-table line numbers are off by one against the bytes.
- round 6: "FightingStyle.SAMBO is never assigned by the generator". The
  positive control only found styles.py tables; the enum print was blank.
  UNVERIFIED until Phase 0 A3.
- Previous handoff: "elite-skill Wrestlers get the same cut as unskilled
  ones". Non-specialists under 60 submissions never attempt a sub.
- Previous handoff OPEN item "why Wrestlers did not respond to F on the live
  path": not wiring. F reaches them. Likely sambo-brain Wrestlers; the live
  run was never split by base, so that is still an inference.

==========================================================================
5. OPEN
==========================================================================
- Does grappling beat striking at equal rating, or does OVR undervalue
  grappling? Trend only.
- Why the roster's elite is almost all sambo-tagged. Phase 0 A5 and T1/T2.
- MC odds: "only shifts the RNG stream" is a read. Needs a fighter-state
  snapshot before/after _compute_mc_odds_for_fight. Whether MC was on in
  Phase 0's 25.2% is inferred from the absence of a patch.
- PA: does the error log show a SYSTEMS-SHIM line; does live have injuries.
- Live Wrestler SUB share (52.6%) vs fixed population (43.8%).
- Carried, unresolved: pair-list sha mismatch (Phase 1); tech-sub overshoot
  branch; exotic-hold frequency row.

BACKLOG ROW CANDIDATES (none filed)
- Doctor-stoppage flush skip loses the final round's stats.
- Sub-attempt spam: up to 42 attempts in one fight; 294 of 5400 with >= 7.
- KO label: 26 clean KOs in 5400 fights; nearly all strike finishes say TKO.
- Sambo chain is dead code in this population.
- Weight-class finish gradient: unmeasured against the real pattern.
- int() truncation convention on every sub_weight modifier.
- Harness: injury counter counts gfi calls, not returned injuries; severity
  labels differ in case (Moderate vs MODERATE) between store and hook.

==========================================================================
6. ARCHITECT-SEAT ERRORS THIS THREAD
==========================================================================
- Set the Step 1 ratio gate at 0.43 +/- 0.03 without knowing about int().
- Asked for an mc_odds count in a harness that patches MC off: circular.
- Called the max(1, ...) floor a likely bug before seeing its skill gate.
- Suspected the 45 gate drove the sambo share. Dead.
- Guessed round 6's S1/S2 would bracket the 16-20% band. Best arm was 25.1%.
- Control 3 did not anticipate engine-side stat loss.
- Estimated "+/- 3pp at ten worlds" from three worlds. Never tested.
- Spec'd rounds from cc summaries more than once before the file arrived.

==========================================================================
7. STYLE SYSTEM DESIGN, AS DISCUSSED WITH VAN (nothing built)
==========================================================================
Principles Van liked ("make it smart")
1. A fighter's best skill area decides the primary style.
2. A second style is EARNED by reaching a real level, not by being close.
   (56% of fighters have top-two within 5 points; closeness alone would give
   nearly everyone two styles.)
3. Styles change only at review points and by a clear margin.
4. The label you see is the brain that fights.
5. Cap at two styles; strong everywhere = Balanced.
6. Learning a style is an event: news, scouting change, opponent planning.
   Age and fight IQ set the pace; decline can take a style away.
7. Engine blends the primary and secondary action tables; sambo then emerges
   from wrestler + bjj with no special case.
8. Everything that reads one style today reads the primary.
Later wrinkle, not now: Pressure / Counter / Point describe approach, not
discipline. A cleaner model separates the two.

Proposed slices
1. Census (Phase 0, in flight).
2. Label = brain: store the detected style; hash-neutral.
3. Show the secondary, display only; Van playtests.
4. Engine blends: measured balance change; method-mix targets tuned here.
5. Learning events and commentary.

Proposed win-method profile by type (design targets, not data; unruled)
  type                              SUB     KO/TKO   DEC
  BJJ Specialist                    60-70   5-10     25-30
  Sambo (if visible)                30-40   20-25    40-45
  Wrestler                          15-20   15-20    60-65
  Ground & Pound                    10-15   45-55    30-40
  Pressure Fighter                  5-10    40-45    45-50
  Clinch Fighter                    8-12    30       60
  Striker / Muay Thai / S&B         3-6     50-55    40
  Counter Striker                   3-6     30-35    60
  Point Fighter                     0-3     15       80+

==========================================================================
8. HOW WE WORK (communication keys)
==========================================================================
Van
- Writes brief directives. "prompt sent" means cc is running it.
- Usually pastes cc's terminal summary first, then drags the report file.
  The file is the evidence; the paste is not.
- Says plainly when he does not know, and takes the recommendation. So every
  recommendation must carry what is measured vs inferred.
- For design questions he wants plain English: what it is, how it fits the
  game, pros, cons, size, does it undo work, is it worth it.
- Delegates timing; wants to be consulted again at the design point.
- Uses the UFC as the reference for realism; open to something more
  interesting than one number.
- Has not answered: player visibility of base; queue order; finish target.

Reply shape that worked
- Verdict first. Then what the file shows, what is only narration,
  corrections, the cc prompt in one code block, at most one question.
- Say out loud when a handoff or paste is stale or is narration.
- Own architect errors by name.

cc, observed this thread
- Used head / tail pipes three times after prompts forbade them; ran one
  driver in the background. State the exact run command in the prompt.
- Reruns and debugs its own analysis past a FAIL, then reports the last run.
- Rewrote one report after the run (4b). Reports are append-only since.
- Ran all arms before evaluating controls (round 5).
- Substitutes an approximation when the data cannot answer, and says so in
  a note (5c by-base split). Read the notes.
- Makes sensible deviations and flags them (0.4286 for 0.43).
- Positive controls are often too weak to prove what they claim.
- Closing summaries carry errors; candidate-cause lists are guesses.
- Stops correctly on a failed gate and does not pick winners.

Prompt conventions in use
- CLEARED list on every diagnostic prompt.
- FOREGROUND, python3 -u, exact run command, no pipes, sim stdout to a
  separate log, report append-only and never rewritten.
- Control 1 is always the baseline hash on s1. A second control proves new
  plumbing is neutral before any candidate runs.
- Branches written in: control fails -> STOP with the failing cell.
- "Do not pick." "Forks are Van's."
- Up to three candidates per sandbox round, one table.

==========================================================================
9. SEQUENCE FROM HERE
==========================================================================
1. Read outputs/style1_phase0.txt adversarially (the file).
2. Design discussion with Van from that table: primary rule, secondary
   rule, Sambo visibility, what happens to a created fighter's chosen style.
3. Docs commit, on Van's sentence, paths named: SUB-RATE1 Phase 1 through
   round 6 filings, both false-as-written lists, all rulings in section 2,
   the backlog-row candidates.
4. Engine commit, separate: injury-sub removal (ruled 2026-11-12).
   awards.py:55-62 keeps parsing old "Submission (Injury - X)" strings.
   Decide the dead hook wiring. Before/after injuries per 100 fights, live.
5. STYLE1 slices 2-5, each its own arc with its own gates.
6. Method-mix tuning on the new system; SUB-RATE1 closes there.
7. Then SLOW-WEEK1 -> money probe -> VENUE-US1, unless Van reorders.

FIRST WORK ITEM: read outputs/style1_phase0.txt in this order, before any
rate in it:
  (a) Part B control hash equals 48fc32af...35f1
  (b) A2 positive control found fe:2017 and fi:1893
  (c) the brain census from -> to table for T1 and T2: how many of the 69
      sambo brains moved, and where to
  (d) only then SUB%, win rate by brain, and the changed-fighter table.
If T1 moves few fighters or barely moves SUB%, the "elite strikers misfiled
as sambo" explanation is dead and the grappling-vs-striking balance question
becomes the lead.