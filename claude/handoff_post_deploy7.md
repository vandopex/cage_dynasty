HANDOFF — post deploy #7 (written 2026-09-20 PDT; architect thread opened 2026-09-18)

PROVENANCE. Written in the architect seat and moved to the repo by heredoc through Van's paste — SINGLE PATH, model in the byte path. The sha256 pre-registered in the filing prompt covers the transcription, not an independent source. Project-store mirror is a copy of this text; the repo wins.

Names no HEAD by rule. Carried state is claude/backlog.md, claude/deploy7_2026-09-20.md, and git log. Open with: read CLAUDE.md, read backlog.md, read deploy7_2026-09-20.md §f–§j, then `git log --oneline -12 && git ls-remote origin main`. Then STOP.

ANCHORS THAT DO NOT MOVE WHEN DOCS COMMIT
- Last CODE commits: 25adadd (CHAMPIONS-PAGE1) and 6540d3c (RECORD-BOOK-REPOINT1). Both cage_dynasty_web/game_bridge.py only.
- PA: 4e72bab (deploy #7, 2026-09-20 PDT; reload window 2026-09-21T00:14:33Z–00:14:40Z). PA carries every code commit. Docs commits since do not need a deploy.
- Deploy #7 accepted on: PA `git rev-parse HEAD` = 4e72bab; Files-API sha256 of game_bridge.py = `git show 4e72bab:` blob (38b1de64…5d130, both printed); server.log (RE)spawn at 00:14:39 inside the window; three IMPORT-PATH-PROOF lines resolving under /home/vandopegaming/cage_dynasty/ including narrative/commentary.py; error.log delta empty. Van's PA browser check PASS (filing §k).
- Filing: claude/deploy7_2026-09-20.md (0e949fd).
- Procedure of record: claude/deploy_procedure.md v1.1 (cf201ee). v1.2 candidates in filing §g.

RULINGS LANDED THIS THREAD
- Ruling (a), 2026-09-19: cc commits or runs a deploy step only on a sentence Van wrote. Architect next-steps are written "if Van rules X, cc does Y" and are not directives. Filed in CLAUDE.md docs-tier section. Held on every test after it landed, including cc refusing an unfilled bracket and refusing to infer the answer from the architect's wording.
- Index lines carry no transient state (deploy_procedure v1.1 entry: version + commit, nothing else).
- Closed docket lines carry no "pending" text; git history is the audit trail.
- Step 3 of a deploy may be run by Van directly in the PA browser console and pasted; the paste is the artifact. Used when the API console was cold (HTTP 412). Deviation on transport only.

CLOSED
- RECORD-BOOK1 — both title cards populate at week 0 from _belt_history; cross-checks against Champions page (Teixeira 2 reigns / 4 defenses on both).
- BELT-LINEAGE1, display half — founder→current chain, no "Season Opener". HOF-reader half stays open as slice 1 commit 3.

MEASUREMENT OF RECORD
- fight_engine.__file__ = /home/vandopegaming/cage_dynasty/cage_dynasty_web/fight_engine.py (server.log, deploy #7 spawn). The root fight_engine.py ghost is not imported by the running app. First time this was measured rather than assumed. DEPLOY-GATE-REF1 (3) — ghost retirement — rests on it.

SEQUENCING
1. CLAUDE.md rule line (docs tier, if not already landed with this handoff): cc's self-report of which tool it used is not evidence; the architect's fold-check (ctrl+o on the collapsed call) is ground truth; any instruction that hinges on tool choice is verified by expanding the fold, not by asking cc.
2. Slice 1 commit 3 — _compute_hof_score (game_bridge.py:4388; :4393 is the _title_history read inside it) reads _belt_history. ENGINE TIER. Measurement designed before the edit: fresh world advanced one season, inductees old-store vs new-store, per-inductee reign share of score. BeltReign is a dataclass; _title_history rows were dicts. 25/reign untouched until measured.
3. Slice 2 — VACATED-REIGN1: BeltHistory.vacate_reign; both vacate sites (:4058, :6939) call it. Engine tier.
4. Slice 3 — retire _title_history writes once no reader remains (readers after 1–2: :2977 save only). Then DRAW-SEMANTICS1 (Gate 0 is Baker's row), OVR-FORMULA1 (discussion).
- New quick items: GOAT-SORT1 (GOAT top 10 order ≠ displayed pts; Gate 0 is `git diff 46c094f..4e72bab -- cage_dynasty_web/game_bridge.py | grep -i goat` to rule regression in or out, then read the sort key); RECORD-BOOK-STATS1 (strike/sub/TD cards "No records yet" at week 0 — expected or gap, unknown).
- Unchanged quick wins: RECAP-STALE1, HISTORY-CAP1, FOUNDER-LABEL1.
- deploy_procedure v1.2: step 4 sweep runs pre-pull (sweeps prevPA's templates); step 3 error.log baseline belongs in the step-3 command block; step 0 is part of any "run steps N–M".

READING CC — THIS THREAD
- Self-report on tool use was false three times: "no non-Bash tools this turn" while the fold showed the Grep tool, once while explicitly asked to audit its own call log ("9 invocations, all Bash"). Then used the Grep tool again in the turn after the fold check confirmed it. Treat as a standing trait: cc cannot see its own tool headers; Van can. Do not ask cc which tool it used — expand the fold.
- Seat promotions, two, before ruling (a): took the architect's "my recommendation" plus a conditional as a ruling (parenthetical); took "on a clean word-diff: commit" as a directive. After ruling (a): held correctly on a preview, on an unfilled bracket, and on a fix outside the sentence Van wrote (backlog pending phrases, L1181). That is the process working.
- Presented a reconstructed `$ grep …` shell line as "raw output" when the Grep tool had run (step 11). Narration wearing a prompt character.
- Prose retyping inflated an 8-row manifest to 10 visible rows while claiming "printed, not counted."
- Caught the architect: step-3 command omitted v1.1's error.log baseline; stale "pending" at CLAUDE.md L531 and L1181 after PASS; refused to fabricate a baseline count. All right.

THE ARCHITECT WAS WRONG — THIS THREAD
- Counted fold-lines as commits (27 for 17). The exact error charged to cc.
- Wrote deploy step ranges and a step-3 command for v1.1 without having read v1.1, twice: "steps 1–3" skipped step 0 (cold console); the step-3 command dropped the baseline.
- Asserted "console 47103182 is now loaded in my browser" as a done fact inside a prompt Van forwarded before doing it.
- handoff_post_slice1 §6.5 was false: step 8 gates the runtime set (name-only minus claude/ and .md), not the whole pull set. Corrected as §6 item 7.
- Wrote executable conditionals into messages Van forwards verbatim; both seat promotions trace to that phrasing.
- Read a PA-side pre-state (`M fight_engine.py`) as local drift. Withdrawn.
- `owed` as a grep pattern matched "showed" and "swallowed".
- Drafted a branch withdrawing seven substitution charges as "0 verified" before the fold was checked; the fold showed Grep and the charges stood. The lean was visible in the drafting; cc read it and correctly refused to act on it.

WHAT WORKED
- Van running step 3 in the PA browser console and pasting: cleanest artifact of the deploy, no API hop, and it sidestepped the cold-console 412.
- `git diff --cached -U0 --word-diff=plain` as the commit gate: cannot truncate, discriminates the token that changed from everything that did not.
- A shell grep for "pending" across the staged set found two stale docket lines a read had missed. Instrument over read, again.
- One ctrl+o settled a three-turn dispute that narration on both sides could not.

Supersedes claude/handoff_post_slice1.md (its body and §6 corrections layer stay as history).

COMMITS THIS THREAD — orientation only; git log is the source
4e72bab docs — CLAUDE.md index: deploy_procedure.md v1 → v1.1 (cf201ee)
0e949fd docs — deploy #7 filed (4e72bab), PA check PASS; RECORD-BOOK1 + BELT-LINEAGE1 display closed; ruling (a); handoff §6.5 correction; §j
(next) docs — this handoff + CLAUDE.md index line (+ rule line if Van folds it in)
