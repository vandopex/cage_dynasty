# WEEK-AXIS1 (a)+(b) — SHIPPING FILING (2026-09-10, architect thread)

Status: SHIPPED LOCALLY, four single-purpose commits on a8e675a:
  dcee687  (a) STAMP        live rows carry event_number
  266e382  (b) SEED         _fighter_cooldowns initialised from pre-gen history
  1ccefa0  (b) BOOKER1      opening-card builder honours _is_available (Phases 2/2.5)
  23c7599  (b) CHAMP-A      opening-card title booking checks the champion
Not on PA (PA at 7555c35, deploy #3). Forward-only throughout: new saves only.
Gate 0 filing: claude/week_axis1_gate0_2026-09-09.md. Line numbers below are
at 23c7599 — re-grep before editing.

## 1. WHAT SHIPPED AND WHY EACH ONE

(a) STAMP. Helper _event_number_from_name (game_bridge.py, above _dfc_label)
    parses the trailing int of the row's own event_name; None when absent.
    Four write sites add the key (winner+loser dicts in _simulate_card_fights,
    _simulate_ai_fights_week, _run_real_engine). NOT computed from week:
    _dfc_label's (week − week//3) collides on off-weeks, and the row's week
    is stamped at simulation time while the name was fixed at booking. One
    source of truth per row.
(b) SEED. After _dfc_event_offset is set (~:2396): for each fighter with
    pre-gen rows, _fighter_cooldowns[fid] = (last pre-gen week −
    _initializer.history_weeks) + COOLDOWN_WINNER. 291 seeded on the seed,
    range −33..4 — predicted from dump_20260908 before the run and matched
    exactly. Loser/champion cooldowns not reconstructed (Van ruling
    2026-09-09). COOLDOWN_WINNER added to the matchmaking import (:376).
(b) BOOKER1. _build_card_for_week_planned (initialize_card_pipeline, weeks
    1-3) never called _is_available in Phase 2 (ranks 6-14) or Phase 2.5
    (top-5 non-title); the general _build_card_for_week does (:16370). Two
    comprehension filters added, same shape.
(b) CHAMP-A. Phase 1 gated the contender and never the champion. Two
    lines: skip the division's title fight that week when the champion is
    unavailable. Live cadence untouched — see §4 COOLDOWN-CONSTANTS1.

## 2. GATES (instrument path, seed 20260907 --weeks 14, two fresh runs each)

R06 pregen_to_live_seam:  8 (7/7 pre-fix runs) → 7 (SEED) → 2 (BOOKER1) →
  0 (CHAMP-A), each step's count and the names of the survivors predicted
  before the run and confirmed by name (Azamat Kovalev, Oliver Jackson —
  champions — were the last two). pregen_only 0 and live_only 0 throughout.
T-4 none_at_wk_positive: 202 → 0 (STAMP), held at 0 through (b).
Name/number agreement on live rows: 1806/1806 (STAMP).
Pre-gen rows vs dump_20260908: 0 len / 0 row diffs on every dump in the arc.
R10/R12/R13 PASS throughout; R10 AI histogram byte-identical.
Live copy: sys.modules['game_bridge'].__file__ = cage_dynasty_web/game_bridge.py.
R03: 1 / 2 / 4 / 6 / 7 across runs — live-play dependent (§3); STATUS only.

Player-visible, recorded: opening cards weeks 1-3 drop 12 → 9 fights each
(BOOKER1) while seeded cooldowns hold; LW and FW title fights leave the
opening two cards (CHAMP-A); Azamat's defence moves wk 2 → wk 11; live title
fights in the 14-week window 9 → 6 (TITLE-CADENCE1, §4).

## 3. HARNESS-RNG2 — MEASURED, NON-BLOCKING

Same code, two processes, seed 20260907 --weeks 14: 85/293 fighters differ
in history length, 120/1289 paired live rows differ; pre-gen rows 0/1618.
PYTHONHASHSEED=0 pair: 120 — hash salt is NOT the cause. uuid4-pinned pair:
52, but those runs took 47-57 min vs 5.6; 4,657 uuid4 calls in a 2-week run
cannot cost that, so the wrapper slowdown is UNEXPLAINED and the 52 is not
quoted. Third source unnamed. Stable across all runs: R06 seam count,
pre-gen rows, T-4, R10. Rule adopted: a live-play count may gate a commit
only when shown stable across ≥2 fresh runs on each side; HARNESS-RNG1's
"process-stable" claim was pre-gen only. Van ruling 2026-09-10: (b)
unblocked on R06 seam stability (8 in 7/7 runs).
LINEAGE1: R05 FAIL 2 (Middleweight reign[0].lost_to != reign[1].champion_id)
in 3 of 7 identical-code runs, PASS in 4 — a live belt transition
intermittently writes an inconsistent lineage. Engine bug the harness makes
visible; Gate 0 = diff a FAIL dump's Middleweight belt_history against a PASS dump's.

## 4. FINDINGS FILED (none fixed here)

COOLDOWN-CONSTANTS1. _cooldown_weeks (game_bridge.py ~:15464) returns 0 for
  champions and for every winner (Ship M2). COOLDOWN_CHAMPION = 8 in
  matchmaking.py is dead on the bridge path; COOLDOWN_WINNER = 4 is used by
  exactly one thing, SEED. Live gaps stay ≥ 4 only because booking lead time
  (_weeks_out_for_fight, 10-12 for title) is longer. R06's "floor 4" is the
  instrument's floor, not the engine's. The seam is now stricter than live
  play — SEED's 4 is a documented placeholder.
DAMAGE-COOLDOWN1 (design, own arc). Cooldown today is a penalty for losing
  (losers 6 + 2/loss, winners 0). Recovery should derive from the fight —
  method, rounds, damage — not the result; that is what produces "both out
  until spring after that war" and a champion who can't defend because the
  last defence cost him. R07 already notes no medical-suspension mechanism.
  Sequenced after playtesting the seeded opening cards.
TITLE-CADENCE1 (observation, n=1 seed). A champion skipped for cooldown at
  wk 2 was not rebooked until wk 11: the planned builder fires only for
  weeks 1-3, after which title fights wait for lead-time booking. Measure
  across seeds before scoping; north-star reading is that a champion coming
  off cooldown should be the first thing the booker reaches for.
OFFWEEK-CARD1 (waste, harmless). initialize_card_pipeline builds cards for
  weeks 1..3 with num_cards=3 hardcoded; week 3 is an off-week (week % 3 ==
  0), so a 9-12-fight card is built, labelled "Cage Dynasty 62" (colliding
  with week 2's label), and discarded at advance (:3782-3784). Zero rows
  reach fight_history — census confirmed no label collisions in data.
ROW-SCHEMA1 (filed 2026-09-10, unchanged). Live rows write round_finished,
  pre-gen writes round; live rows omit weight_class.

## 5. RULINGS (Van, 2026-09-09/10)

1. Four forward-only commits for WEEK-AXIS1; (a) STAMP parses the row's own
   event_name rather than computing from week (architect call on the
   printed source, ratified).
2. (b) SEED blanket COOLDOWN_WINNER only; no loser/champion reconstruction;
   _fighter_signing_available untouched.
3. (b) unblocked on R06 seam stability rather than full reproducibility.
4. CHAMP-COOLDOWN1 shipped as Option A (seam-only availability check);
   Option B (give champions/winners a live cooldown) deferred to
   DAMAGE-COOLDOWN1 — Van: winners should have cooldowns, derived from the
   fight, not the result; not inside this arc.
5. Founding row (Gate 0 ruling 3) stands; FOUNDING-ROW2 open.
6. (c) PREDICATE next, then deploy #4; (d) _recently_fought after deploy.

## 6. PROCESS NOTES

- Every step's R06 count AND survivor names were written down before the
  run. Three predictions, three exact matches. That is what made 8 → 7 → 2
  → 0 legible as three causes instead of one partial fix.
- The architect's hypothesis for the 7 survivors ("cards booked before the
  seed ran") was wrong; a week-0 probe killed it in one run (seed present,
  _is_available False, booked anyway). The measurement, not the read,
  pointed at _build_card_for_week_planned.
- cc's "cleanest" for STAMP (factor a helper, compute from week) was
  overruled on the printed source: the off-week collision was in
  _dfc_label's own docstring.
- cc's §4 cadence table walked pre-gen history (75 gaps from 9 live title
  fights) — a number that could not be what it was labelled. Caught by
  arithmetic, not by re-running.
- Paste 21's uuid experiment cost two 47-minute runs because the paste said
  "patch uuid4" and not "cheaply". The PYTHONHASHSEED test (10 minutes)
  should have run first. cc self-scheduled polls while waiting; first
  unattended cc time this arc; nothing was edited.
- A "read" offered as a measurement was caught three times this arc (streak
  filter "worth a diagnostic session" when R01/R02 PASS already existed; the
  reader grep result collapsed in a report and then reprinted on request;
  "4 grep hits" that were 5). The pattern holds: ask for the print.
