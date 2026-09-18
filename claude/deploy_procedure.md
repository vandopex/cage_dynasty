# Deploy procedure — disk-canonical (v1, 2026-09-18)

Supersedes the procedure text embedded in claude/deploy5_2026-09-15.md §1.
Filings record what happened; this file records what to do. Edit here, never
in a filing. Each deploy filing cites the version of this file it followed.

## Inputs
* prevPA — SHA PA is running before this deploy (from pre-state).
* newPA — SHA being deployed. Must equal `git ls-remote origin main`.

## Steps
0. Console warm-check (unchanged from deploy5 §1).
1. Local `git ls-remote origin main` must equal newPA — first line, no
   exceptions (deploy5 step 1).
2. `GET /webapps/` — 200, target domain listed. Confirms auth token and
   target web-app existence (deploy5 step 2).
3. Pre-state via console: `cd ~/cage_dynasty && git rev-parse HEAD && git status
   --porcelain`. Expected drift: `?? outputs/sm1/` only. Any ` M` line is a
   STOP until DEPLOY-GATE-REF1 step (3) has retired the root fight_engine.py
   ghost; after that, any ` M` line is a STOP, full stop.
4. G0 template compile sweep: `python3 -u claude/tools/template_compile_sweep.py`,
   must return `N/N clean` (deploy5 step 7; CLAUDE.md Standing Gates).
5. Pull: `git fetch origin && git pull --ff-only origin main && git rev-parse
   HEAD`. Output must equal newPA.
6. Reload (unchanged). Record UTC wall-clock start and end — the
   respawn-window check at step 9 depends on it.
7. SHA gate: `git rev-parse HEAD` on PA == newPA.
8. Ship-file hash gate. Runtime set = `git diff --name-only prevPA..newPA`
   minus claude/ and *.md. For EACH path: Files-API fetch PA's copy; compare
   `shasum -a 256` against `git show newPA:<path> | shasum -a 256`. Never a
   working-tree path. All must match. Record every pair in the filing.
   If the runtime set is empty (docs-only deploy), record "runtime set:
   empty" and run the pull-transport check instead: hash PA's
   cage_dynasty_web/game_bridge.py against `git show newPA:` — labelled
   PULL-TRANSPORT, not SHIP-FILE.
9. Reload-window respawn check (server.log half of deploy5 §6c). Files-API
   GET server.log, tail; assert `(RE)spawned uWSGI master` timestamp
   inside step 6's UTC wall-clock window.
10. Import-path gate. From the same server.log fetch, take the two
    `[IMPORT-PATH-PROOF]` lines emitted by the post-reload spawn and assert:
    fight_engine.__file__ == /home/vandopegaming/cage_dynasty/cage_dynasty_web/fight_engine.py
    fight_integration.__file__ == /home/vandopegaming/cage_dynasty/cage_dynasty_web/fight_integration.py
    `?unknown?` or any other path is a FAIL regardless of the ✅ prefix.
11. Error-log delta (error-log half of deploy5 §6c). Files-API GET
    error.log, tail; new lines must be timestamped after step 6's
    wall-clock start; line count reported against step 3's baseline.
12. Browser check on a fresh save (new as a procedure step; from deploy5
    §4 and deploy6 practice). Owed if not performed.
13. Print the gates table (step / expected / observed / PASS-FAIL). STOP.
    No filing until Van reads the table (deploy5 step 8).
14. Filing: claude/deployN_<date>.md, citing this file's version.

## Gate count
Thirteen gates (steps 0..12). Steps 13 and 14 are reporting actions.
Deploy5/deploy6 counted ten because their §6 proof triad was one step with
three sub-items and the import-path check was absent. Step 4 (G0),
step 10 (import-path), and step 11 (error-log delta as its own row) are
the three additions vs deploy6's ten-row table. Steps 8 and 10 are the
DEPLOY-GATE-REF1 changes.
