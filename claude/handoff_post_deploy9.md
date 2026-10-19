# HANDOFF — post deploy #9 (2026-10-19)

Supersedes handoff_post_deploy8.md (+§8–§10). Anchors carry no HEAD; use `git log`.

## 1. Anchors
- PA is at 873b2a8 (deploy #9, 2026-10-19 21:26 UTC). Runtime set N=1 cage_dynasty_web/game_bridge.py, sha256 bedc47fb…14834. Filing claude/deploy9_2026-10-19.md; 12 steps on printed evidence; step 11 against a real pre-reload baseline for the first time. Webhook dead (PA measured at 20b828a before the pull after four docs pushes); docs pushes are inert.
- Last engine commit: 92bd7fa TITLE-HISTORY-RETIRE1 (Slice 3). Before it: 9418952 VACATED-REIGN1 (b), 1791962 VACATED-REIGN1. All three on PA.
- BELT-HISTORY arc COMPLETE on PA: slice 1 (deploys #7–#8), slice 2 + slice 3 (deploy #9). `_belt_history` is the only title store; `_title_history` is gone (zero readers census, claude/slice3_title_history_gate0_2026-10-19.md).
- `git log --oneline 92bd7fa..HEAD | grep -v DOCS` should print nothing.
- PA carries ` M fight_engine.py` (root ghost, 11 insertions, unchanged since deploy #5) and `?? outputs/sm1/`. Console 47103182's CWD is cage_dynasty_web/ — every console command cds first.
- CLAUDE.md 43.3 KB, 601 lines (ARCHIVE4 c1–c3 done; c4 reorder pending). Line numbers cited in handoffs before f091db9 are stale; find by heading or marker.

## 2. Rulings landed (Sat–Sun)
- VACATED-REIGN1 design: a vacated reign ends at the vacate week, lost_to None, lost_event = card label via _dfc_label (so the profile's 🛡️ window closes — template keys on event number, None = open), lost_method = bucket ("Vacated (injury)" / "Vacated (player choice)" / "Vacated (weight move)"). Vacant-belt claim keeps won_from None, distinguished by won_method "Won Vacant Title (…)"; Title Changes exclude it. Same fighter vacates then regains = two reigns (Heavyweight Ulberg rendered this on PA at deploy #9). Forward-only: pre-1791962 saves keep open ghost reigns; CLAUDE.md known-hazard line.
- Slice 3: remove the store, not just the writes. Old saves keep the key unread.
- ARCHIVE4 target 40 KB; Known defects → backlog.md; reorder (c4) last.
- FIGHTNIGHT1: standing corner policy, never a per-round pause (2026-10-02). FIGHTER-GOALS1 shape ratified, design doc pending.

## 3. Measured (filed; do not re-derive)
- Three live vacate sites wrote division + (two of them) _title_history, never _belt_history; ghost reign measured 3/3 on HEAD f091db9, closed 3/3 post-fix (probe v3). Fourth path, live retirement, vacates nothing in any store — RETIRE-VACATE1, inspection-only, no bridge method to probe.
- Pre-gen is seed-stable on non-id fields only; uuid4 ids differ per process. A serialized-dict md5 is not an equivalence gate; save_invariants' pre-gen row compare is (286/286, 34/34 reigns, 0 diffs HEAD vs Slice 3 edit).
- fighter_profile.html L1215–1216 treats lost_event_number None as an open 🛡️ window.
- 2/3 vacated divisions went 40 weeks unfilled in the probe, _book_title_fight returned None — VACANT-FILL1, one seed, probe conditions.
- save_invariants prints SIMULATION-SHIM FAILED (Gameplan import) alongside a success line — HARNESS-ENV1.

## 4. Sequencing
1. Record Book check on PA, owed from deploy #9 step 12 (both cards vs one profile). Van's next PA session; no cc work.
2. RETIRE-VACATE1 Gate 0: hoist both inline retire paths into one helper (aging block ~11390 and the /retirement-decision 'retire' branch), then vacate_belt. Engine tier; probe v4 gains a retire site.
3. VACANT-FILL1 Gate 0: what _book_title_fight needs to produce a fight; why two of three vacant belts stayed empty 40 weeks. Read-only census first.
4. deploy_procedure.md v1.2 — candidates: deploy7 §g (2), deploy8 §5 (4), deploy9 §5 (4). Docs tier, stop before commit.
5. ARCHIVE4 c4: move lines 1–~232 (four 🚨 blocks, deployment state, deploy workflow, Top-of-backlog) below the constitution; the H1 is buried mid-file. One verbatim block, hash-gated. Rename "Current deployment state" → multi-user architecture in the same commit.
6. Then features: GAMEPLAN1 Gate 0 (plan-output census, post-P5-C — check the P3 board), FIGHTER-GOALS1 design doc, CORNER-STATE1 (standalone, any time).
7. Parked: HOF-TUNE1, GOAT-SORT1, RECORD-BOOK-STATS1, DUMP-PROVENANCE1, DEPLOY-GATE-REF1 (3) ghost retirement, HARNESS-ENV1, SIM-PACE1 (time per advance_week by week type — Van notices card weeks vs off weeks), "Won from Inaugural" reign-card phrasing (cosmetic).

## 5. cc-reading patterns (this arc)
- Two narration errors contradicted by cc's own printed JSON in one report (who crowned at week 8; "self-healing" vs active_reigns=2). The probe caught both. Ask for the dump, not the story.
- cc softened its own §4(d) finding in chat after filing it. Findings stand as filed unless re-measured.
- cc substituted a reign *count* for an equivalence gate when the md5 failed. Counts don't discriminate; the adjusted instrument must.
- cc derives gate expectations from the pre-state correctly when told to; this held all weekend. Keep it.
- cc refused a placeholder (step 12 block) and a double-commit. Both right.

## 6. Architect errors (this arc)
- Four hand-derived gate values wrong (hunks, lines ×2, insert line) — rule: cc derives, architect reads.
- Asserted pre-gen byte-stable; SAME SEED says otherwise. Instrument failed; the established tool (save_invariants) was the answer.
- Changed a store write and checked the reader after the commit. Reader grep belongs in Gate 0 of any write-path fix.
- Filter `grep -v '^??'` excluded an untracked file from an "expect exactly N files" gate.
- Sent the deploy prep before the docs commit; cc's diff set was one file short. Commit before prep.
- "Last line of the section" was ambiguous; name the anchor line.

## 7. Opening sequence for the next thread (cc, read-only, then STOP)
Read CLAUDE.md and claude/backlog.md into context (do not print). Then Bash: `git log --oneline -6; git status --short | grep -v '^??'; git ls-remote origin main | cut -c1-7; git log --oneline 92bd7fa..HEAD | grep -v DOCS`. Expect the last command to print nothing. STOP.
