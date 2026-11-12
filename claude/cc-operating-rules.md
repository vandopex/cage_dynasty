# cc OPERATING RULES — standing for every Claude Code session

The split in one line: cc is free to TRY and MEASURE; the architect seat and Van DECIDE and SHIP.

## THE THREE ZONES

GREEN — no approval needed:
- Read anything in the repo.
- Write and run probes under outputs/ (untracked by convention, not by .gitignore; see RED).
- Follow a finding to its root cause. Stop when the function, line, or mechanism is named, or when the next step is a design choice.
- Experiment in a sandbox (below).
- Profile anything slow.
- On a PASSED read-only gate, go straight to the next step's read-only Phase 0 and report. A pass never waits for a "continue".

YELLOW — sandbox only; report before it touches main:
- Any change to a file in the deploy path (`cage_dynasty_web/`, `narrative/`, and anything else the PA import path reaches).
- Any new constant or new value.
- Any harness change that alters what a gate measures. The adjusted harness must be shown to still DISCRIMINATE before its result is accepted.

RED — only on Van's explicit release, routed through the architect seat:
- Any commit to main (engine, balance, or docs — stop-before-commit has already proven load-bearing on docs).
- Any push. Any deploy. Any edit to CLAUDE.md or claude/.
- Any git add of a path under outputs/. git add -A and git add . are never used; every commit names its paths.
- Adding or changing a harness in claude/tools/ is a claude/ edit and is RED.
- Moving sandbox work into the working tree.
- Changing, relaxing, or relabeling a gate.
- Choosing between designs, or deciding what "realistic" means.
- Continuing past a failed gate.
- Two levers in one accepted step.
- Backfilling historical saves. Data fixes are forward-only.

## THE SANDBOX

- `git worktree add /tmp/cd-exp-<name> HEAD`. The working tree is never the experiment.
- One lever per experiment. Up to THREE candidates per question without checking in. Report the losers alongside the winner, with numbers.
- Screen first (small n), full gate only for survivors. A screen can kill a candidate; it can never pass one.
- To compare against what is live: `git worktree add /tmp/cd-live <PA SHA from the newest deploy filing indexed in CLAUDE.md>`.
- After the ruling, the accepted change is rebuilt in the real tree and gated there. That run is the gate of record. Nothing ships from a sandbox. Sandbox worktrees are removed after the ruling so they cannot become stale evidence.
- Sandbox scope is empirical questions: "which of these moves the number." It is not for forks that are design calls. cc surfaces those and stops.

## DEFINITION OF DONE FOR A REPORT

- Measured, never inferred. A number computed by assumption is labeled ESTIMATE with its assumption and never shares a table with measurements.
- Negatives verified with a tool, command shown. A zero-result grep carries a positive control.
- Nothing unexplained is called variance. Runs that differ beyond SE with no named cause are UNEXPLAINED, then profiled or bisected.
- n and SE on every comparison. Small n is a TREND. One save or one seed is an example.
- The gate of record is a run started after the last edit to anything it imports. Confirm by mtime.
- Pre-state measured in the same session as post-state. Gate expectations are derived from the pre-state before any edit.
- Any write-path change greps its readers in Gate 0.
- Output that must be read by the architect seat arrives via Bash only, short lines, no folds.
- A plain statement of what is not known.

## RULES THAT DO NOT BEND (unchanged; restated so this file stands alone)

- Wrong premise in a prompt → STOP and report.
- A failed gate is a STOP. "Essentially at tolerance" is a fail. A mis-specified gate is reported and replaced by ruling, never tuned around.
- Fix the engine, not the output.
- Wrong numbers are documented as false in CLAUDE.md, never quietly dropped.
- Deploy is proven by `git rev-parse HEAD` match plus a Files-API grep of the running import path. commentary.py lives at narrative/commentary.py; greps against cage_dynasty_web/ for it come back empty and read as phantom.
- Never hardcode an active save or fighter name.
