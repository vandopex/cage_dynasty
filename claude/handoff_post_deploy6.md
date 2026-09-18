# HANDOFF — post-deploy #6 (written 2026-09-16, architect thread)

For the next architect thread. This doc names no HEAD — by rule (CLAUDE.md
"Commits and handoffs"), carried state is claude/backlog.md plus git log.
Open with: read CLAUDE.md, read backlog.md's top, run
`git log --oneline -8 && git ls-remote origin main`. Then STOP.

## Anchors that do not move when docs commit
* Last CODE commit: 46c094f — FOUNDING-ROW2, canonical filtered streak
  walkers, five consumers unified.
* PA: 46c094f (deploy #6, 2026-09-16, 10/10, file-hash byte-identical,
  filing claude/deploy6_2026-09-16.md). PA is CODE-CURRENT.
* Instrument: claude/tools/save_invariants.py R14 (three bounds, calls
  the live canonical path). HARNESS-ENV1 means --seed runs bind the
  fallback engine locally until fixed; --save replay is unaffected.

## Owed — one ruling, one correction (landed)
* VAN'S RULING, open since 2026-09-15: does a founding champion's awarded
  reign count as a title reign in the record book? Architect rec: counts
  as a REIGN and nothing else — not a win, not a streak link, not a
  defense. Gates the belt-history arc below. Not filed on any docket yet;
  file it inline on RECORD-BOOK1 when ruled.
* DOCS CORRECTION landed (2cda150, bca5687, and this commit): backlog.md
  DRAW-SEMANTICS1 now states the two samples CONTRADICT — Lindqvist vs
  Suzuki (CD15) result='L' on BOTH rows; Usman vs Baker (CD46)
  result='W' on Usman's. Same pre-gen path, two encodings. That
  contradiction IS Gate 0. Baker's row is unprinted; do not assume CD46
  splits. Verify the entry reads this way before scoping.

## Architect's sequencing rec — awaiting Van's ruling
1. BELT-HISTORY arc: RECORD-BOOK1 + BELT-LINEAGE1 + VACATED-REIGN1 are
   one root — belt history split across _belt_history / _title_history
   with every reader picking a different store. Two of three are
   player-visible now (blank record-book boards; Champions page calls
   Machado inaugural when he won the belt at CD59). Read-side, display
   tier, follows the (c) precedent. Needs the ruling above.
2. DRAW-SEMANTICS1: engine tier, write-path, forward-only. Gate 0 is
   the encoding contradiction. Do not start it as an evening.
3. OVR-FORMULA1: Van wants to discuss (2026-09-16). AI OVR is the flat
   19-stat mean; player OVR is style-weighted. Hyun Gyu Park is the
   worked example — 86 by flat mean, ~90 style-weighted, dragged by
   chin 52 / heart 54 on a Counter Striker.
Also open, unranked: RECAP-STALE1, HISTORY-CAP1, NAME-COLLISION1,
DIVISION-GENDER1, HARNESS-ENV1, DUMP-PROVENANCE1, COOLDOWN-CONSTANTS1 /
TITLE-CADENCE1 (corroborated twice 2026-09-16), plus the standing board.

## Reading cc — this arc's patterns
* cc reaches for seed-20260907 fighter names (Whittaker, Kowalkiewicz,
  Jackson) when discussing PA. Corrected twice; it recurred. Those
  fighters do not exist on PA. Look for the shape, not names.
* Arithmetic slips, six this arc: 25-vs-24 readers, five-distinct
  beside a six-row table, "8 days" for two, 180/63 for 178/64, "3
  ahead" for 2, "eight new" dockets for seven. Every count gets summed
  before it is quoted.
* Asserted an exclusive writer without grepping the repo ("wins is
  live-only") and was wrong. Demand the grep, not the claim.
* Self-corrects cleanly when caught, and caught the architect four
  times (longest-streak rule; rationale-line scope; a prompt that
  referenced a paste which never crossed threads — cc stopped rather
  than improvise; deploy_procedure v1 omissions). Acknowledge it.

## The architect was wrong four times, corrected by measurement each time
* Extended ruling 1's week-0 prohibition to event_number. Ruling 1 says
  week. Cost a round trip.
* "Longest over-counts for anyone who won their first post-crown fight."
  Lindqvist refutes it; the rule is peak-run contiguity.
* Told Van months of pre-gen gates were fiction. The DRAW-row test
  proved the baseline real-engine. Retracted.
* Prescribed R14 bounds (a) and (c) when (c) needs longest.
The central lesson applies to this seat too. Measure, then say.

## What worked
* Van's browser: ten minutes on a fresh save closed both owed checks and
  produced most of the day's seven new dockets. Two of the day's biggest
  findings came from measurements aimed at something else. Keep doing
  this.
* Tiered stop-before-commit (CLAUDE.md, 979d0f1). Docs commit freely.
  Apply it from turn one.

## Addendum 2026-09-18 (same architect thread, post-push audit)
* NEW under Owed: DEPLOY-GATE-REF1 filed (576501c). claude/deploy_procedure.md
  v1 is now disk-canonical; deploy #7 follows it, not deploy5 §1. The PA
  ghost-file checkout (`git checkout HEAD -- fight_engine.py`) is a live
  touch — stops before execution, after the import-path gate passes in-app
  once.
* DUMP-PROVENANCE1 Gate 0 result: outputs/ is 784M, 602M of it cited by
  filings, app does not write there, PA pulls via git. Wholesale tracking
  is out; hash manifest generated from claude/*.md is the shape. Not scoped.
* Architect wrong a fifth time: drafted deploy_procedure.md v1 omitting the
  G0 template sweep, the local ls-remote check, and the API auth check, and
  labelled a new step as inherited. cc caught all of it against deploy5 §1
  — fourth catch this arc. Same lesson: a read of one filing is not a diff
  against it.
* Ruling from 2026-09-15 still open.

Supersedes claude/handoff_post_rematch_cooldown1.md.
