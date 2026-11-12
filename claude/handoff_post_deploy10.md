# HANDOFF — post deploy #10 (2026-11-11)

Supersedes handoff_post_deploy9.md. Anchors carry no HEAD; use `git log`.

## §1 How to start a thread

Read `git log` before trusting this file. Opening commands:

```
git log --oneline -6
git status --short | grep -v '^??'
git ls-remote origin main | cut -c1-7
git log --oneline a19a921..HEAD | grep -v ' DOCS'
```

Output for the architect seat goes to a file, then `cat`, then `pbcopy < file`.

## §2 Commits since deploy #9 (git log 873b2a8..HEAD at time of writing)

- `227367d` 2026-11-11 DOCS: deploy #10 filing + corrections.
- `a19a921` 2026-11-11 DOCS: backlog filing 2026-11-11 — 14 PA-playthrough rows + cosmetic batch, EXPORT-500 shipped local, EXPORT-RECORDS1 cause named, SLOW-WEEK1, VENUE-US1, AGING-AGE1 lead, CLAUDE-LEN1, WORKTREE-STALE1, deploy #9 step 12 Record Book PASS, parked features with Van's rulings.
- `21dedee` 2026-11-11 EXPORT-500: engine — `get_universe_export` reads `bridge.get_champion(wc)`; retires `self._game_state.champions`.
- `d2aefc5` 2026-11-11 DOCS: cc operating rules (three zones GREEN/YELLOW/RED, worktree sandbox, definition of done; outputs/ untracked by convention).
- `45046fc` 2026-11-01 DOCS: RETIRE-VACATE1 Gate 3 filing + §7 AGING-AGE1 census; PLAYER-RETIRE-REGISTRY1, VACANT-FILL1 4th data point, seed-non-reproducibility finding.
- `e459701` 2026-10-29 RETIRE-VACATE1: engine — `_vacate_on_retire` helper + two call sites (aging block, `/retirement-decision`).
- `0dff271` 2026-10-23 DOCS: RETIRE-VACATE1 backlog + index follow-up for d9005dc.
- `d9005dc` 2026-10-23 DOCS: RETIRE-VACATE1 Gate 0–2 filings + RETIRE-PATH-UNIFY1, PREGEN-RETIRE-EVENT1, DEAD-HANDLER1, VACATE-REASON-RENDER1, HOF a/an cosmetic.
- `f45dba9` 2026-10-19 DOCS: handoff_post_deploy9 — BELT-HISTORY arc complete on PA at 873b2a8; sequencing to RETIRE-VACATE1, VACANT-FILL1, v1.2, ARCHIVE4 c4, features.
- `281ec76` 2026-10-19 DOCS: deploy #9 filing (873b2a8 to PA; three engine + six docs; step 12 browser PASS at week 10; error-log baseline closed deploy8 §4a; four v1.2 candidates).
- Deploy #10 shipped engine `e459701` + `21dedee` on PA at `a19a921`; steps 0–11 cc PASS; step 12 Van PASS.

## §3 Rulings by Van, 2026-11-11 (architect seat, 2026-11-11)

- Sandbox lane adopted: cc may try and measure; Van and the architect seat decide and ship. Authority `claude/cc-operating-rules.md`.
- Venues: at least half of events in US cities; no Las Vegas preference.
- Submissions: the current rate is too high. Target not yet set. Architect proposal awaiting Van: about 55% of fights finishing, submissions 35–40% of finishes.
- Belts: a champion who leaves the weight class does not keep the belt; a champion injured 26+ weeks gives it up (deploy #9 filing says 25; reconcile when touched).
- Top-four tournament to fill an empty belt is the preferred shape for VACANT-FILL1. Rival promotion declined. Other feature ideas are parked until the found bugs are fixed.
- First-fight purse: Van changed nothing in negotiation.

## §4 Sequencing (architect seat, 2026-11-11)

1. **SUB-RATE1 Phase 0, read-only**: repair the method-mix probe's round and takedown counters; attempts per fight and success per attempt by style and round; how submissions are entered; success against defender sub-defense; strike-versus-submission choice for Ground & Pound and Wrestler; identify the OTHER results; name the governing constants and the commits that last changed them. No fix proposed in Phase 0.
2. **SLOW-WEEK1 sandbox**: reduce the odds precompute cost without moving the odds. Candidates to compare: a non-narrated simulation path for odds; fewer simulations per bout; both. Measure event-week wall time and odds agreement against current.
3. **Money probe, read-only**: log every balance change over 12 weeks against what the offer card, recap and dashboard display (OVERHEAD-DISPLAY1, PURSE-PAYOUT1).
4. **VENUE-US1 build**. Architect proposal, not ruled: target 55%, more US cities in the list, per-save seed as a separate change.
5. Remaining 2026-11-11 playthrough rows in backlog order.

## §5 Open cells

- **RECAP-STALE-CARD1** — UNEXPLAINED.
- **AGING-AGE1 addendum** — LEAD, not measured.
- **METHOD-MIX1** — round split and takedown-to-sub link NOT MEASURED (probe field mismatches; counters read zero); OTHER category (16 of 1080) not identified.
- **PURSE-PAYOUT1** — "Cause not measured" (body).

## §6 Instrument notes from this session (architect seat, 2026-11-11)

- `tee /dev/tty` fails in cc's shell; write to a file, `cat`, then `pbcopy`.
- `ctrl+o` expands the whole transcript, not one call.
- PA consoles must be opened in the browser before deploy step 0; a cold console returns 412.
- A cold request to `/` returns 302 to `/new-game`.
- Expectations in a prompt are derived from pre-state, including the architect seat's; three of today's stops were architect-seat errors in expectations or line ranges.
- A check that compares an accessor with itself cannot fail; use an independent source and a corrupted control (EXPORT-500).
- cc backgrounds long probes; the report file is written once at the end and is the evidence.

## §7 What is not known

- Submission target rate: not ruled; architect proposal awaits Van.
- PURSE-PAYOUT1 cause (paid = 2× purse): not measured.
- AGING-AGE1 fix direction (write side / read side / both): not chosen.
- Whether the current method-mix differs from a prior engine's readings by design or defect: not determined.
