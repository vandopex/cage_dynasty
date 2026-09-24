# HANDOFF — post deploy #8 (2026-09-21)

Supersedes handoff_post_deploy7.md. Anchors carry no HEAD (CLAUDE.md L842); use `git log`.

## 1. Anchors
- PA is at 20b828a (deploy #8, 2026-09-22 UTC). Runtime set was N=1 game_bridge.py; hash c6604c2b…994af. Filing: claude/deploy8_2026-09-22.md. All 12 gates on printed evidence; step 11 passed on timestamp test only (§4a).
- Last engine commit: 0c4bfb6 HOF-REPOINT1 — `_compute_hof_score` reads `_belt_history.get_fighter_reigns`; None store raises. Gate: outputs/hof/hof_predict_v1.py → hof_verify_v1.py, 290/290 on save slot hof_harness (user_id hof_predict, seed 20260921, week 26). Both harness files and the save are untracked.
- BELT-HISTORY slice 1 COMPLETE on PA: 25adadd, 6540d3c, 0c4bfb6.
- Everything after 0c4bfb6 is docs-only. `git log --oneline 0c4bfb6..HEAD` should show only DOCS commits; anything else is unreleased.
- PA carries ` M fight_engine.py` (root ghost, +11 lines, inert per IMPORT-PATH-PROOF) and `?? outputs/sm1/`. Not present locally.

## 2. Rulings landed this thread
- Deploy #8: Van typed "deploy" into cc directly. Ruling (a) satisfied by that sentence.
- `_belt_history is None` inside `_compute_hof_score` raises (architect recommendation shipped on Van's commit word; not separately ruled — say so if it comes up).
- No tuning of HOF_THRESHOLD or 25/reign. HOF-TUNE1 waits for a multi-season world.

## 3. Measured this thread (filed; do not re-derive)
- 0 Grep tool calls in 8 cc sessions 2026-09-04→20 (deploy7 §k). Collapsed "Searched for N patterns" headers are summaries, not evidence of tool. CLAUDE.md L841.
- Harness world: `_belt_history` 19 reigns (9 founding + 10 pre-gen transfers), `_title_history` 0 rows but 8 keys — defense writes init the key without a row (`_record_title_result` :15765, guard :15882). TITLE-KEYS1.
- 56/290 fighters ≥ HOF threshold 60 at week 26, 43 with zero reigns. HOF-TUNE1.
- PA browser (deploy #8 step 12): live defense reached `_belt_history` (Byrne, Most Defenses); pre-gen rows carry no stat keys, live rows do (RECORD-BOOK-STATS1 confirmed).

## 4. Sequencing
1. Slice 2 VACATED-REIGN1. Gate 0 read-only: both vacate sites (game_bridge.py :4058 injury, :6939 player), `BeltHistory.vacate_belt` world_init.py:684, and what each site currently writes to each store. Design the measurement (a saved world with at least one vacate on each path) before any edit. Engine tier.
2. Slice 3: retire `_title_history` writes once no reader remains (readers left: :2977 save, :4058, :6939). TITLE-KEYS1 closes with it.
3. deploy_procedure.md v1.2 — candidates in deploy7 §g and deploy8 §5. Docs tier, but stop before commit; it is load-bearing.
4. Parked: HOF-TUNE1, GOAT-SORT1 Gate 0, RECORD-BOOK-STATS1 design question, ARCHIVE3 second pass (CLAUDE.md >70k chars), HARNESS-ENV1, DEPLOY-GATE-REF1 (3) ghost retirement, DUMP-PROVENANCE1 (harness files untracked).

## 5. cc-reading patterns (this thread)
- Gates-table rows are narration until the printed line is cited; #8 step 11 reported a baseline fetch that never happened. Ask for the mechanism, not the verdict.
- cc substituted Read for a requested `cat` twice, folding the content out of the paste. Say "Bash only" when the output must arrive inline.
- cc turned an unfilled prompt bracket into a WAIVED verdict. cc does not convert placeholders into rulings.
- cc opened a readiness turn with "Recommendation: DEPLOY." Not cc's seat.
- cc's post-`/clear` framing of "what's left" was stale (claimed commits 1–2 unshipped). Scope from filings, not from cc.
- Console sends: `--data-urlencode` always; `-d` truncates at `&`. Poll bodies to disk.

## 6. Architect errors (this thread)
- "(Grep tool)" reading of a fold label — false, corrected deploy7 §k.
- Wrote a HEAD-naming line into CLAUDE.md against L842; reverted before commit.
- Mis-targeted a correction at handoff_post_slice1 §6.6, which makes no Grep charge; rewritten as item 8.
- Left a fill-in bracket in a prompt Van pastes verbatim → phantom waiver (deploy8 §4d).
- Asserted step 10 gates commentary.py; v1.1 does not (the diagnostic prints it, but it is not a gate).

## 7. Opening sequence for the next thread (cc, read-only, then STOP)
Read CLAUDE.md and claude/backlog.md into context (do not print). Then Bash: `git log --oneline -8; git status --short | grep -v '^??'; git ls-remote origin main | cut -c1-7; git log --oneline 0c4bfb6..HEAD | grep -v DOCS`. Expect the last command to print nothing. STOP.

## 8. Addendum 2026-09-23 — ARCHIVE4 commit 1 landed (supersedes §4 item 4 "ARCHIVE3 second pass")
- c5f0d35 DOCS ARCHIVE4 commit 1: four verbatim extractions, CLAUDE.md 1195→906 lines, 76078→60083 bytes (pre cd6f7e80…, post 62d6241…). New library files: claude/golden_master_oracle.md, claude/local_playtest_command.md, claude/claude_md_archive_2026c.md, claude/certified_cell_baselines.md. Gates: per-block md5 4/4 vs HEAD blob, hunk headers -92,108 / -959,50 / -1010,139 / -1191,0, 8 added lines, all printed. Census: outputs/archive4/census_2026-09-22.txt (untracked).
- LINE REFERENCES: every CLAUDE.md line number cited in this handoff, deploy7, deploy8, and slice1 predates c5f0d35 and is off by up to 297 lines. Re-find by heading or `<!-- ARCHIVE2 -->`/`<!-- ARCHIVE4 -->` marker, never by L-number. §1 "CLAUDE.md L842" and §3 "L841" are the first two to re-find.
- Remaining ARCHIVE4 commits, in order, each stop-before-commit:
  2. Known defects (5 items, filed 2026-07-13..24, ~9.9k) + "SAME SEED" 🚨 section (~2.3k): census each against `git log` for a fixing SHA. Fixed → claude_md_archive_2026c.md; open → claude/backlog.md. Van ruled backlog.md, not a defects file.
  3. Known hazards (### under Architecture, ~9.3k) live/dead census; ## Archive index (~6.9k — why an index is 7k); Top-of-backlog vs Current top-of-list dedup; Current deployment state (PA SHA goes stale by design).
  4. Reorder: constitution (Project overview..Commits and handoffs) to the top, 🚨 blocks below it. Last, once, because it moves every line number again. NEW STANDING RULE relocates out from under Key constants here.
  Target 40 KB. Rulings: 40 KB, backlog.md, reorder last — Van 2026-09-22.
- cc pattern, add to §5: cc appends a Co-Authored-By trailer to every -m via heredoc. Harmless; the approved message is never quite the landed message. Say "no trailer" if it matters.
- Transport: this architect thread clipped the top of pastes and folded the middle on three consecutive gate turns. Reset both seats before commit 2.
