# REMATCH-COOLDOWN1 — SHIPPING FILING (2026-09-14, architect thread)

Status: SHIPPED LOCALLY at eeff834 on 55c7233. Not on PA (PA at 54e3b68 —
this is engine-touching so deploy #5 is a separate decision; docs
committed before the move).

Forward-only: new saves and old saves both benefit. Fix is at read
time; no data migration. Legacy saves without a persisted
`_dfc_event_offset` collapse to raw formula (unchanged behavior) with
a one-time inert-axis notice.

## 1. WHAT SHIPPED (one method rewrite + one class-state pair, one commit)

(1) cage_dynasty_web/game_bridge.py:15615-15715 (`_weeks_since_fought`
    body + docstring). Old body: two loops (`fight_history`, then
    `_fighter_data[fid]['fight_history']`), each returning
    `current_week - fought_week` on first match. New body:
      span = int(getattr(self, '_dfc_event_offset', 0) or 0)
      # find first-match (fw, en) across both lists, or return None
      # (never fought — the only path that yields None)
      if span == 0: warn once if any en present, return raw
      if en is None: return raw (LIVE default; pre-gen always sets en)
      if int(en) > span: return raw (live row; span cancels)
      if int(en) != int(fw): warn once per pair, return raw (drift guard)
      return (span + current_week) - fw       # unified pre-gen return
    The four call sites in `_build_card_for_week` (post-fix line
    numbers 16504/16523/16567/16663) are unchanged in signature and
    keep their integer week thresholds (20/20/16/6). Comment states
    explicitly that a missing `event_number` defaults to LIVE
    treatment because pre-gen rows always carry one (world_init.py:
    2398/2413 set it on both winner and loser copies).
(2) cage_dynasty_web/game_bridge.py:2065-2080 (class-level state
    `_rc1_inert_axis_warned: bool = False` and
    `_rc1_drift_warned_pairs: set = set()`), so the warning
    suppression is once-per-process across every bridge instance in a
    multi-user session.
(3) claude/backlog.md — PREGEN-SPAN1 filed as its own docket, queued
    after this ship: persist `history_weeks` as a second bridge
    attribute so span and axis-classifier are two constants for two
    jobs, saveload round-trip + legacy fallback, retires the per-row
    `en != fw` guard.

## 2. GATES

- Gate 0 (before the fix, seed 20260907 --weeks 14, two runs, probe
  wrapping `_weeks_since_fought` with no return change):
    site               calls Run1/Run2   OVER Run1/Run2
    pledge_title       0/0                 0/0     (inferred-not-measured)
    rankings_top10     71/118              47/98
    ranked_v_ranked    290/232             65/82
    unranked           383/333             112/117
  Raw returns for pre-gen rows were negative (e.g. -22 when
  current_week=5 and row.week=27), and every gate blocks on
  `last < N`, so the deeper into pre-gen a pair fought, the more
  certainly they were BLOCKED. Cooldown was inverted.
- Gate 1 (probe on guarded body, same seed, two runs):
    OVER = 0 at every measured site in both runs
    UNDER = 0 at every measured site in both runs
    sup_raw == sup_axis at every site (raw and axis returns agree
    when the axis transform doesn't shift them, which for live rows
    is always the case)
  UNDER = 0 by construction: unified return = raw + span for pre-gen
  rows (span > 0), = raw for live rows and every fallback. No pair
  raw permitted becomes blocked. Guarantee holds independent of
  seed.
- Gate 2 (card-composition census, two independent processes,
  method-swap for before/after within each process):
    Run 1: total_fights 95→98 (+3), distinct_pairings tracks total,
           title_fights 7→8, repeats 0/0
    Run 2: total_fights 94→101 (+7), distinct_pairings tracks total,
           title_fights 6→9, repeats 0/0
  Zero repeat pairings post-fix in both runs (no pair booked twice in
  the 14-week window under the relaxed gates). distinct_pairings
  equals total_fights in every case.
- Gate 3 (title cadence in 14 weeks): 7→8 and 6→9 across the two
  runs. Direction is up, stable across HARNESS-RNG2. Measurement
  attached to TITLE-CADENCE1 (§5).
- Gate 4 (pre-gen equivalence vs dump_20260908 by structural
  signature, ignoring uuid4-derived fighter_ids): 0 differing rows.
  fix does not touch the world_init path.
- Gate 5 (save_invariants full pass, seed 20260907 --weeks 14):
    R01/R02/R03/R04/R10/R12/R13 PASS
    R05 FAIL 4 post-fix (Featherweight + Middleweight); FAIL 2 with
        pre-fix method swapped in at the same seed (Middleweight);
        FAIL 2 on a second post-fix run (Strawweight, different
        divisions). Count wanders, matches LINEAGE1. All 6
        violations across the three dumps share LINEAGE1's signature
        (reign[i].lost_to != reign[i+1].champion_id, class 1). Zero
        secondary R05 shape (lost_week != won_week).
    R06 PASS 0. pregen_to_live_seam = 0 (CHAMP-A holds through).
    T-4 event_number_none = 0/1823.
- Gate 6 (live copy path resolution): game_bridge.__file__ resolves
  to cage_dynasty_web/game_bridge.py; loaded body contains the guard
  code (`_rc1_drift_warned_pairs` referenced; `_dfc_event_offset`
  read).
- Guard fire test (synthetic, span=60, current_week=14, drift row
  en=27 fw=20):
    Call 1: return=-6 (matches raw), stdout=1 line
      "⚠️ [REMATCH-COOLDOWN1] pre-gen cadence drift on
      fighter- vs opp-guar: en=27 fw=20 span=60 — raw
      fallback for this call. See
      claude/rematch_cooldown1_filing_2026-09-14.md"
    Call 2: return=-6, stdout=0 lines (no re-warn on same pair)
- Discrimination proof (a) — probe attribution: post-fix line
  registry + pre-fix body via class-level swap reproduces
  709/744 total calls with OVER > 0 at every site
  (top10 56/67, ranked 82/129, unranked 69/126). No site collapsed
  to 0 calls; the Gate 1 zero is a real fix outcome, not
  misattribution.
- Discrimination proof (b) — multiset comparator: swapped-in dump
  generated at seed 42 reports 3020 differing rows across 1992
  signatures against the same reference dump that reports 0 at seed
  20260907. The Gate 4 zero is a real equivalence result under a
  comparator that can fail.

## 3. CENTRAL LESSON — THE DOCKET NAMED THE WRONG FUNCTION

Backlog line 18 said the next scoping item after WEEK-AXIS1 (a)+(b)+(c)
was `(d) _recently_fought (measure first)`. `_recently_fought` (at
`game_bridge.py:12384`) had exactly one caller —
`_maybe_generate_inbound_offers` at `:4638` — and that caller iterated
player fighters only. Player fighters carry no pre-gen history, so a
cross-axis week comparison in `_recently_fought` could never misfire.
The docket was naming a function whose bug surface was empty.

`_weeks_since_fought` (at `game_bridge.py:15609`) lived one screen
away in the same file and had FOUR callers, all in
`_build_card_for_week`, all consulted per week per division per
matchup attempt. Same two-axis week comparison; live surface.

A read found it (single grep for `_since_fought\|_recently_fought` in
the module surfaces both). A measurement made it shippable — Gate 0
counted the miss (OVER > 0 at every exercised site, both runs, N=
744/683) rather than reasoning about it in the docstring. The old
raw formula's failure mode had been sitting in code review distance
since STAMP (`dcee687`, 2026-09-09) made the two axes distinguishable
by event_number — and until Gate 0, was still described as an
inference. The lesson: when a docket points at a function, verify the
CALLERS are the ones that would exercise the described failure mode.
The named function may not be the one that hurts.

## 4. RULINGS OF RECORD (Van, 2026-09-14)

1. TWO DOCKETS, NOT ONE. RECENTLY-FOUGHT1 (`_recently_fought`,
   player-only, negligible) and REMATCH-COOLDOWN1
   (`_weeks_since_fought`, live surface) are separate. RECENTLY-
   FOUGHT1 remains filed (backlog) and not-fixed; REMATCH-COOLDOWN1
   ships here. Merging them into a single "cross-axis in
   game_bridge.py" docket would have hidden which callers were doing
   the damage.
2. UNIFIED WEEKS, NOT EVENT GAPS. The alternative return —
   `current_event_number - fought_event_number` — was rejected
   before Gate 0 because pre-gen produces one event per week but
   live-play produces one event every ~three weeks (measured from
   the dump: 9 completed events across 14 live weeks). An event-gap
   return would have silently retuned all four thresholds by ~3×;
   the title gate would go from a week 20 minimum to somewhere north
   of a year. Unified WEEKS keeps thresholds meaning what they were
   written to mean.
3. GUARD FALLS BACK TO RAW, NEVER None. On the pre-gen cadence
   drift path (en != fw within a row classified as pre-gen), the
   function returns `current_week - fw`, the pre-fix formula. It
   MUST NOT return None. Every caller reads None as "never fought"
   and treats the pair as fully eligible — maximally permissive,
   silently defeating cooldowns for that pair. Raw is worse than
   unified but bounded; None is unbounded.
4. TITLE-FIGHT CADENCE DELIBERATELY NOT TUNED INSIDE A BUG FIX.
   Gate 3 measured 6→10 title fights in 14 weeks (§5); the ship
   moves the number without setting it. A threshold change bundled
   into this commit would hide the engine's behavior behind the
   commit's output — the reader would not know whether the movement
   was the bug fix or the tuning. Own docket (TITLE-CADENCE1),
   deliberately.

## 5. FINDINGS

### R05 sort finding (LINEAGE1 amendment queued)

Save_invariants `r05_reign_chains` at `save_invariants.py:481` sorts
reigns per-division by `won_week`:
```python
sorted_r = sorted(reigns, key=lambda r: int(r.get("won_week", 0) or 0))
```
`won_week` is a split-axis field. Pre-gen reigns carry won_week in
0..history_weeks (0 for founding, 1..60 for pre-gen title changes);
live-play reigns carry won_week starting again at 1 for the first
title change after the world starts. Sorting them together places
live-play won_week=1 BEFORE pre-gen won_week=19, out of order on the
unified timeline.

All 6 R05 violations observed across three dumps (pre-fix run 1: 2,
Middleweight; post-fix run 1: 4, Featherweight + Middleweight;
post-fix run 2: 2, Strawweight — different divisions) share this
shape: reign[i] with won_week ∈ 0..19 (pre-gen axis), reign[i+1]
with won_week ∈ 1..11 (live-play axis), and the lost_to →
champion_id chain fails at the split. Same two-axis-week hazard
REMATCH-COOLDOWN1 addressed in `_weeks_since_fought`, present in the
comparator itself.

LINEAGE1's line "Engine bug, not harness noise" is marked DOUBTFUL
in the backlog amendment — it may be a comparator artifact. New
Gate 0: fix the sort to unified weeks (or filter by axis and check
each axis independently) and re-measure BEFORE hunting an engine
write path.

### OPENCARD-REMATCH1 (finding named, not filed as docket)

Pre-gen rematch census showed 9-10 pre-gen pairs already
rebooked in the pre-fix 14-week window, via booking paths that never
consult `_weeks_since_fought`. Three of those pairs recur in every
run — Nikolaev vs Volkov, Araujo vs Rivera, Whittaker vs Nemkov —
all at Cage Dynasty 61/62 (live wk 1/2), which are opening-card
title fights. The opening-card path pairs the champion against the
#1 they lost the belt to in pre-gen. Not caused by this fix (present
in pre-fix runs unchanged); confirms from a second direction that
pre-gen rematches are a real signal (they exist in both branches,
this fix only opens the four cooldown-gated sites).

Filed only in this filing under the name OPENCARD-REMATCH1 for
discoverability; not on the board as a separate docket (design
question is out of scope for a cooldown fix). If future work wants
to control which opening-card rematches book, it starts here.

### Call-count drop (unpredicted side effect)

Total `_weeks_since_fought` calls per 14-week window dropped from
683/744 pre-fix to 485/542 post-fix — ~28-33% across both seeds.
Fewer over-suppressions means the matchmaker finds valid pairs
earlier per division/week iteration and exits the retry loop
sooner. Not a targeted outcome; recorded because the "matchmaker
cadence looked slow" playtest note class was traceable to work the
matchmaker was doing on inverted-blocked pairs, and this fix
reduces that work by roughly a third. Neither a wall-clock claim
nor a scoping input to any PERF docket — just naming the
mechanism.

## 6. HARNESS-RNG2 STATUS

Every count in Gate 1, Gate 2, Gate 3, Gate 5 was measured across
two fresh runs (two independent processes at seed 20260907). Where
counts differ between runs, direction is quoted; magnitudes are
paired (Run 1 / Run 2). The Gate 4 comparator ignores fighter_ids
because uuid4() is not process-stable — cross-process fighter_id
inequality was the finding that killed row-tuple diffs at 3254/1627
before the multiset switch (see §7).

HARNESS-RNG2 remains non-blocking, unchanged.

## 7. PROCESS NOTES

- Gate 4 hit a comparator switch mid-run. First implementation used
  row tuples keyed on fighter_id / opponent_id and reported every
  row as differing (only-in-REF = 1627, only-in-POST = 1627) because
  uuid4() is not process-stable. Second implementation switched to
  a Counter over the row's structural signature (event_number,
  result, method, round, week, weight_class, was_title_fight,
  specialty_method) and reported 0. Van required a discrimination
  proof for the new comparator (Item 3 of the pre-commit checklist);
  the seed-42 dump reports 3020 differing rows across 1992
  signatures, confirming the comparator can fail. Rule adopted:
  when a gate swaps its comparator mid-arc, prove the new one can
  fail before quoting a zero.
- The docstring on the first fix revision claimed "equals
  history_weeks by construction, so the same integer serves as both
  event classifier and week span." Van rejected the docstring as
  the load-bearing artifact — a claim in prose does not protect
  against a future pre-gen cadence change. Guard added, docstring
  trimmed to ~28 lines pointing here.
- Guard fire test (Item 4 of the pre-commit checklist) exists
  because the guard's error path was untested — the guard has
  never fired in any real run, so the assertion "return equals raw
  on drift" was an untested claim. Synthetic drift row exercised
  the path; three assertions passed (return, single warn, no
  re-warn) with the class-level state reset around the test.
- Commit body item 4 ("pre-gen rematches up in both runs — direction,
  not magnitude") quotes the magnitudes (10→18, 9→15, +8, +6) in
  the same sentence that says "magnitude is not quoted." Flagged
  to Van pre-commit as an internal inconsistency; not amended.
  Recording here so the filing reads honestly against the commit.
- Discrimination proofs surfaced two separate risks the initial
  Gate 1 zero couldn't distinguish: (a) attribution — line-number
  registry could be pointing at UNKNOWN sites, making OVER=0
  vacuous; (b) comparator — the multiset could return 0 for any
  input pair. Both proofs took 4-5 minutes together and would have
  been the difference between "0 measured" and "the gate happens to
  return 0" in a future re-read. Same lesson as the (c) filing's
  render-probe / R03-harness split — one measurement isn't a gate;
  a measurement plus a discrimination is.
