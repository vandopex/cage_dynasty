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
