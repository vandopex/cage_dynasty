# HANDOFF — post-REMATCH-COOLDOWN1 + deploy #5 (written 2026-09-15, architect thread)

For the next architect thread. Read alongside CLAUDE.md (disk, canonical),
`claude/backlog.md` (the LIVE board, disk canonical, edited in place), and the
three filings this thread produced: `claude/week_axis1_c_filing_2026-09-11.md`,
`claude/rematch_cooldown1_filing_2026-09-14.md`,
`claude/deploy5_2026-09-15.md`. This doc is thread-state only — anything here
that contradicts the committed repo is stale; say so out loud and trust the
repo. Supersedes `claude/handoff_post_week_axis1_b.md`.

## WHERE THINGS STAND

* HEAD: a1fd40c, pushed, remote matches, tracked tree clean. Untracked:
  `outputs/` (harness residue, HARNESS-OUTPATH1). Confirm with
  `git log --oneline -3 && git ls-remote origin main && git status --porcelain | grep -v '^?? outputs/'`
  — first paste, every thread.
* PA: 6d7abc2 (deploy #5, 2026-09-15, 10/10 gates,
  `claude/deploy5_2026-09-15.md`). a1fd40c is docs-only, so PA is CODE-CURRENT.
  This is the first arc in project history where PA is not behind on code.
* CLAUDE.md: ~68 KB against the 40 KB guidance. cc prints a startup warning
  every session. The `## Top-of-backlog` Next-in-order marker has also grown
  from a short pointer into a paragraph carrying resolution history — both are
  ARCHIVE3 second-pass work, filed, not done.
* Baseline for seed 20260907 pre-gen comparison: `outputs/sm_inv/dump_20260908.json`.
* Instruments: `claude/tools/save_invariants.py`,
  `claude/tools/template_compile_sweep.py`, and NEW this arc
  `claude/tools/render_probe.py` — the only instrument that crosses the
  WebFighter boundary (renders fighter_profile.html via Flask test_client,
  validates every badge against reign windows, optional `--against <git-ref>`
  template swap with sha-checked restore).

## WHAT SHIPPED

* **ada3955 — WEEK-AXIS1 (c) PREDICATE.** Five edits: `get_fighter_reigns`
  emits won/lost_event_number (Founding by string); fighter_profile.html
  predicate gains a division gate and compares unified event numbers;
  save_invariants mirrors the new template (ruling α); `_convert_real_fighter`
  forwards `event_number` + `weight_class` to WebFighter; backlog. R03 FP 0,
  render probe 0 violations across 3 fighters incl. multi-reign.
* **54e3b68 — TOOLS render_probe.py.** Promoted out of /tmp.
* **Deploy #4 (2026-09-11)** — first cc-driven deploy via PA API. 12/12.
  PA 7555c35 → 54e3b68.
* **9faeba8 — REMATCH-COOLDOWN1** (amended from eeff834, message-only, one
  sentence; reflog preserves the pre-amend body). `_weeks_since_fought` returns
  unified-week distance with a per-row pre-gen cadence guard. Six gates + guard
  fire test + two discrimination proofs. Pre-gen rematches up in both runs.
* **Deploy #5 (2026-09-15)** — 10/10. PA 54e3b68 → 6d7abc2.
* **a1fd40c — DOCS.** deploy5 filing; RECORD-BOOK1, OVR-FORMULA1, HEIGHT-REACH1
  amended; PREGEN-BOOKING-SKEW1 filed.

## RULINGS OF RECORD (Van, 2026-09-11 → 09-15)

1. (c) derives event numbers at the READ-side serializer, not at write time —
   no data change, works on every existing save. Founding detected by the
   string in `won_event`, never by `won_week == 0` (the season-opener stub is
   also a live write at week 0 — same two-clocks collision).
2. Instrument mirror = ruling α, with the caveat named in the filing: post-(c),
   R03 verifies the serializer derivation and the mirrored predicate, NOT the
   rendered template. The template is covered by compile sweep + render probe
   + browser check only.
3. VACATED-REIGN1 out of (c)'s scope — the architect's claim that the new
   predicate *introduced* a vacate regression was WRONG; cc's print showed
   vacates never reach `_belt_history` at all, so the old predicate had the
   same behavior. Pre-existing, own docket.
4. (d) resolves into TWO dockets, not one: RECENTLY-FOUGHT1 (player-only
   caller, player fighters carry no pre-gen history, cannot misfire — deferred)
   and REMATCH-COOLDOWN1 (`_weeks_since_fought`, AI card builder, shipped).
5. Unified WEEKS, never event gaps. An event-gap return would have silently
   retuned all four cooldown thresholds by ~3× (events fire every ~3 weeks) —
   a balance change wearing a bug fix's clothes.
6. The cadence guard falls back to RAW, never to None. None reads as "never
   fought" to every caller and is the most permissive answer possible; a guard
   must never reach the permissive answer by accident.
7. Title-fight cadence deliberately NOT tuned inside the bug fix. Tuning a
   threshold inside a fix hides the engine behind the output.
8. PREGEN-SPAN1 filed, not done: persist the pre-gen week span as its own
   bridge attribute so span and axis-classifier are two constants for two jobs.
   Retires the per-row guard.

## STANDING RULES THIS ARC EARNED

* **File hash is the deploy gate.** Fetch the running file via the Files API,
  sha256 it, compare to the committed file. Marker greps stay as readable
  confirmation but are no longer the proof — a grep pattern containing brackets
  is a regex character class and returns empty, which reads as a phantom. This
  bit deploy #4 and produced a false negative that cc caught only on re-run.
  The log half of the triad is unchanged and still required: the hash proves
  the file on disk, the respawn timestamps prove the process imported it.
* **Console warm-check is step 0.** A cold PA console 412s on send_input and
  cannot be started via API. Cost a mid-flight round trip on two consecutive
  deploys before being promoted.
* **Direction, not magnitude, under HARNESS-RNG2** — and when magnitudes are
  recorded, they are recorded as observed values, never as a gate.
* **An instrument adjusted mid-gate must be proven to still discriminate**
  before its pass counts. Applied twice this arc: the probe's line-number
  registry (run the new registry against the old body, reproduce the known-bad
  result) and the pre-gen multiset comparator (run it against a different seed,
  confirm a large nonzero).
* **Harness green ≠ player-visible correct.** See the central lesson below.

## THE CENTRAL LESSON (two, both expensive)

1. **The docket named the wrong function.** `_recently_fought` was on the board
   for weeks as "(d)". Its sole caller is player-fighters-only, and player
   fighters have no pre-gen history, so the cross-axis bug could never fire
   there. The real one was `_weeks_since_fought` in the AI card builder, next
   door, unnamed. A read found it; a measurement is what made it shippable.
2. **Three harness gates passed while the feature was dead at render time.**
   During (c), R03 PASS, compile sweep clean, pre-gen equivalence 0 — and the
   template was reading `fight.event_number`, a key `_convert_real_fighter`
   cherry-picked away before the browser ever saw it. The harness reads dumps;
   the browser reads WebFighter. Every template-facing gate must cross that
   boundary or it isn't a gate. `render_probe.py` exists because of this.

## OWED

* **Browser check for REMATCH-COOLDOWN1.** Fresh save on PA, advance to ~week
  10-11, find a live card fight where BOTH fighters already met at a Cage
  Dynasty event numbered below 61. Event 61 is the first live card by
  construction, so any pre-61 meeting is pre-gen. That pairing was structurally
  impossible before 9faeba8. Harness pairs from the filing are seed- and
  process-specific and will NOT appear on PA — look for the shape, not names.

## NEXT — the marker's sequence is stale; the architect argues for a re-rank

The `<!-- ARCHIVE3 -->` marker still carries Van's 2026-09-10 sequencing:
PROSPECT-BONUS1 instrument rule → PROSPECT-BONUS1 retune. That ruling predates
everything found since. Van rules; the case for re-ranking:

1. **LINEAGE1 comparator (cheapest, highest information).** R05 sorts reigns by
   `won_week`, a SPLIT-AXIS field. All 6 violations observed across 3 dumps pair
   a pre-gen-axis reign (won_week 0-19) with a live-axis reign (won_week 1-11),
   ordered wrong on the unified timeline; the count wanders 4/2/2 across
   divisions. Fixing the comparator's sort may close a docket that has been
   filed as an ENGINE bug for weeks without an engine change. Do this before
   hunting a write path.
2. **COOLDOWN-CONSTANTS1 + TITLE-CADENCE1 as ONE arc.** `_cooldown_weeks`
   returns 0 for champions and all winners; COOLDOWN_CHAMPION=8 is dead on the
   bridge path. Winners have no cooldown at all — which means the inverted axis
   compare was the ONLY brake spacing champions out, and REMATCH-COOLDOWN1
   removed it. Title fights measured 6 → 10 in 14 weeks, overshooting the
   pre-CHAMP-A 9 that CHAMP-A deliberately took to 6. These are not two
   dockets. Measure the rate across 52 weeks on 2-3 seeds before touching a
   threshold — the 14-week window is front-loaded by the opening-card builder.
3. **OVR-FORMULA1.** Now player-visible without any instrument. Lightweight
   ladder: champion 87, #1 75, #2 62, #3 80, #10 47, #11 70. Bantamweight:
   champion 79, the #1 who took the belt off him 86. Rank and rating are nearly
   uncorrelated on the most-read page in the game, because AI OVR is frozen at
   world-gen while rank is earned by results. Same root as the filed north-star
   gap (a rival cannot decline in the number the game shows), seen from the
   reader's side.
4. **RECORD-BOOK1.** Two sections blank on a player-facing page, and now known
   to be two code paths — Most Title Reigns / Most Defenses render nothing at
   all while the stat sections correctly print "No records yet".
5. **PROSPECT-BONUS1** (the marker's current head) affects the first ten
   seconds of a save. Its instrument rule is still the right first step when it
   comes up: the 5/9-Balanced figure came from a one-off script and is not a
   baseline until save_invariants prints it. Worth printing at its Gate 0
   whether AI styles come from weighted random at world-gen while player
   prospect styles are derived from stats — if so the fix is narrower than it
   looks.

Also open, unranked: VACATED-REIGN1, BADGE-SEMANTICS1, PREGEN-BOOKING-SKEW1
(new — "Most Fights" top five came entirely from one division in two saves on
different seeds, different division each time; skew is in booking volume, not
outcomes), HEIGHT-REACH1, FOUNDING-ROW2 + streak symptom, OPENCARD-REMATCH1,
ROW-SCHEMA1, PREGEN-SPAN1, TOKEN-HYGIENE1 (half done) + SECRET_KEY, PERF1,
HARNESS-OUTPATH1, ARCHIVE3 second pass.

## HARNESS-RNG2 — unchanged, read before quoting any live-play number

Live play is not cross-process reproducible. Pre-gen is stable. A live-play
count gates a commit only when shown stable across ≥2 fresh runs on each side,
and what gets quoted is the DIRECTION. This arc saw over-suppression counts
swing 47→98 at one site between runs on the same seed while the sign held in
every run — that sign is the finding; the numbers are observations.

## HOW THIS THREAD WORKED (keep doing this)

* Read-only diagnose → edit → gates → STOP → commit on Van's word → push its
  own paste → deploy its own paste. Held throughout, including on docs commits.
* Every count gated on two fresh runs per side, and the gate was named before
  the run wherever possible.
* cc self-reported two of its own errors unprompted: a regex false negative
  that would have read as a phantom, and a commit-body sentence that stated a
  rule and broke it in the same clause. That behavior is the process working;
  it should be acknowledged, not just corrected.
* cc's reframes were right twice where the architect's framing was incomplete —
  option (ii′) at the serializer instead of write-time, and recognizing that
  `_recently_fought` was the wrong target.
* Architect's own errors this thread, all corrected on printed evidence:
  claimed the (c) predicate introduced a vacate regression (pre-existing —
  cc's print killed it); wrote "then commit" into a paste, pre-approving a
  commit that is Van's alone to approve; accepted a 6→10 title-fight change as
  a footnote before recognizing it undoes a deliberate CHAMP-A outcome.
* Van's browser sessions out-yield harness runs per minute spent. Ten minutes
  clicking a week-0 save produced four dockets — two of them player-visible
  defects no instrument was looking for.
