# HANDOFF — post BELT-HISTORY slice 1 commits 1–2 (written 2026-09-19, architect thread opened 2026-09-18)

> PROJECT-STORE MIRROR. Canonical copy is `claude/handoff_post_slice1.md` in the committed repo. If the repo copy differs, the repo wins. This mirror was written from the architect's draft at the moment cc was asked to commit it; verify against `git show HEAD:claude/handoff_post_slice1.md` before relying on any line.

Names no HEAD by rule. Carried state is claude/backlog.md plus git log.
Open with: read CLAUDE.md, read backlog.md, `git log --oneline -12 && git ls-remote origin main`. Then STOP.

## Anchors that do not move when docs commit
* Last CODE commits: 25adadd (CHAMPIONS-PAGE1) and 6540d3c (RECORD-BOOK-REPOINT1). Both game_bridge.py only. Pushed.
* PA: 46c094f (deploy #6). PA is TWO code commits behind. Deploy #7 owed.
* Procedure of record for deploy #7: claude/deploy_procedure.md v1 (9b69d3f). Van has NOT read it. Step 3 as written STOPs on ` M fight_engine.py`, which is expected pre-state — needs Van's wording ruling before cc runs it (DEPLOY-GATE-REF1 v2 owed (a)).

## Rulings landed this thread (all filed inline on dockets)
* Founding reign = a reign and nothing else (RECORD-BOOK1). Extends to HOF: 25/reign untouched until measured (BELT-LINEAGE1).
* Single canonical belt store: _belt_history (BELT-LINEAGE1).
* Docs tier: show diff, STOP, commit on Van's word next turn (CLAUDE.md L838).
* Display tier: render probe pre-commit; Van's browser check is on PA post-deploy. Van does not run local (CLAUDE.md L838, L802, L957).

## Sequencing
1. Deploy #7 — carries 25adadd + 6540d3c. Runtime diff set = game_bridge.py only. Van's PA check on a fresh save at week 0: Champions page chains founder→current with no "Season Opener"; record book's two title cards populated. That check CLOSES RECORD-BOOK1 and BELT-LINEAGE1's display half.
2. Slice 1 commit 3 — _compute_hof_score (:4393) reads _belt_history. ENGINE TIER. Before/after measurement designed before the edit: fresh world advanced one season, HOF inductees old-store vs new-store, per-inductee reign share of score. BeltReign is a dataclass; _title_history rows were dicts.
3. Slice 2 — VACATED-REIGN1: BeltHistory.vacate_reign, both vacate sites (:4058, :6939) call it. Engine tier.
4. Slice 3 — retire _title_history writes once no reader remains (readers after slice 1–2: :2977 save only).
Then DRAW-SEMANTICS1 (Gate 0 is Baker's row), OVR-FORMULA1 (discussion). Quick wins unchanged: RECAP-STALE1, HISTORY-CAP1, FOUNDER-LABEL1.

## Reading cc — this thread
* Arithmetic slips, three: "nine" commits reported as eight from a log that could not show it; "5, not 6" beside a six-item list; 22/27 narrated for a 20/25 commit. Sum every number before quoting it.
* Instruments that did not discriminate, two: a delegated (Explore subagent) grep produced a phantom line :9907; a card-row counter read past the card and reported 7 rows on a top-5 card. Print the rows, not the count. No delegated greps in a filing — cc self-greps.
* Narrated from a stale run once (Middleweight BEFORE described from pre-web_save stdout, not the JSON G2 tested). Narrate from the artifact.
* Offered a design ruling (HOF founding points) that was Van's to give. Not taken.
* Caught the architect once: "five files" for three. Right.

## The architect was wrong — this thread
* Counted three files as four, and five as three. Twice.
* Wrote a real-engine stop condition on fight_engine.__file__; it passed a fallback world. The gate is world_init.FULL_ENGINE_AVAILABLE (HARNESS-ENV1). cc caught it.
* Wrote "local browser check" into two prompts before asking whether Van runs local. He does not.

## What worked
* Gate 0 before scoping: the arc's tier came out of a print, not a guess, and the HOF reader would have been missed otherwise.
* Verbatim filing plus §6 corrections layer, body hash-diffed before commit.
* Van's PA session produced the cleanest before-evidence of the arc (Gadjiev: two reigns on profile, one on lineage) without a harness.

Supersedes claude/handoff_post_deploy6.md.

## Commits this thread (docs unless marked CODE) — for orientation only; git log is the source
6fe622d docs-tier release step + deploy_procedure supersession marker + DUMP-PROVENANCE1 Gate 0 + 9b69d3f breach filed
6cdb737 BELT-HISTORY Gate 0 filed (claude/belt_history_gate0_2026-09-18.md) + founding-reign ruling + HARNESS-ENV1 note
25adadd CODE — CHAMPIONS-PAGE1
6540d3c CODE — RECORD-BOOK-REPOINT1
e5f89ce slice 1 commits 1–2 filed; display-tier check moves to PA; FOUNDER-LABEL1
(next) handoff_post_slice1 — this file

## §6 Corrections layer — added 2026-09-18 (PDT) by the architect thread that opened on this handoff. Body above is verbatim from the project-store mirror (created 2026-09-19T00:58Z); nothing above this heading was edited.
1. PROVENANCE. The body's "canonical copy is in the committed repo" was false when written: at e5f89ce the file existed in neither HEAD nor the working tree (`git show HEAD:claude/handoff_post_slice1.md` → does not exist; `ls` → no such file). The "(next) handoff_post_slice1 — this file" commit never happened. This file was created from the project-store mirror by heredoc through the architect seat — SINGLE PATH, model in the byte path; the sha256 gate covers the transcription, not the mirror.
2. DATE. "written 2026-09-19" is the mirror's UTC creation date (00:58Z). Local date was 2026-09-18.
3. ANCHOR. `_compute_hof_score` is at game_bridge.py:4388, not :4393. :4393 is the `_title_history` read inside it (cc self-grep at e5f89ce). Reader census at e5f89ce, four: :2977 save, :4058 vacate-injury, :4393 HOF, :6939 vacate-player.
4. RULING LANDED. DEPLOY-GATE-REF1 v2 (a) ruled 2026-09-18, option (a): step 3 tolerates ` M fight_engine.py` (root ghost, April 2026 code, 56bf807) pending step (3) retirement. deploy_procedure.md is now v1.1 (cf201ee). The "needs Van's wording ruling" line above is closed. Verified before ruling: `git diff --name-only 46c094f..e5f89ce | grep fight_engine` → no match.
5. RUNTIME SET. "Runtime diff set = game_bridge.py only" is true of runtime files. Step 8's hash gate takes the whole prevPA..newPA set — 7 files at e5f89ce (CLAUDE.md, game_bridge.py, five claude/ docs), more after docs commits. cc computes it at deploy time; do not quote it from here.
6. cc PATTERN, this thread. Substituted a file/directory tool for a Bash read four times in three turns (List for `ls` ×2, Read for `wc -l` ×2), each after an explicit "Bash only." Goes next to "print the rows, not the count." Also: followed a struck instruction the architect left in a prompt and STOPped correctly — that was the architect's error, and the STOP was right.
