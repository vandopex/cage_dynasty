# Known hazards — detail blocks
Moved verbatim from CLAUDE.md at f0684fa4 (ARCHIVE4 commit 3, 2026-10-17). Do not edit; history. The one-line hazards remain in CLAUDE.md ### Known hazards.

## A. Bare-import shadow census (dev C40 PYTHONPATH) — body (CLAUDE.md L326–339)

  A bare `import fight_engine` from repo CWD before `game_bridge` runs its
  `sys.path.insert` + force-delete fixup at `game_bridge.py:190-199` finds
  the WRONG copy. Two shadow candidates, not one:
  - `fight_engine.py` (repo root) — default triple `(55, 0.70, 6)` (dm=0.7).
    CLAUDE.md's original hazard note (see below) named this one.
  - `systems/fight_engine.py` (repo top-level, CLI copy) — default triple
    `(80, 0.43, 6)` (exchanges=80, dm=0.43). Measured 2026-09-07 by the
    step-2 preamble in `outputs/sm1/deploy1/step1_2_report.md`; a preamble
    that imported `fight_engine` before `game_bridge` bound to this file.
  game_bridge's fixup defeats both on the live app. Any diagnostic or
  harness must import `game_bridge` first, THEN read
  `sys.modules['fight_engine']` — never bare-import `fight_engine`. On PA
  the fixup + WSGI's non-repo-root sys.path insulate both shadows; on dev
  the C40 PYTHONPATH exposes them.

## B. Root fight_engine.py on PA, 11 manually-appended constants — full item (CLAUDE.md L344–402)

- **Root `fight_engine.py` on PA has 11 manually-appended constants —
  CONFIRMED REAL 2026-07-12 (not the myth it was suspected of being).**
  Full-tree hash compare of every one of the 227 tracked files, PA vs repo:
  225 byte-match, 1 diff. The diff is root `/home/vandopegaming/cage_dynasty/fight_engine.py`
  — PA is 133782 bytes, repo is 133480 (Δ +302). PA carries 11 lines
  appended after the last function that git doesn't know about:
  ```
  DAMAGE_MULTIPLIER = 0.42
  # Web app compatibility constants
  FLASH_KO_DAMAGE_THRESHOLD = 25.0
  FLASH_KO_BASE_CHANCE = 0.05
  FLASH_KO_MAX_CHANCE = 0.25
  TKO_GNP_HEALTH_THRESHOLD = 30.0
  TKO_GNP_BASE_CHANCE = 0.08
  TKO_GNP_MAX_CHANCE = 0.35
  TKO_STANDING_HEALTH_THRESHOLD = 25.0
  TKO_STANDING_BASE_CHANCE = 0.06
  ```
  **Provenance** (Van, 2026-07-12): fossil of the pre-`sys.path`-hack
  ImportError fix era. Before wsgi.py explicitly excluded repo root
  from `sys.path` and before `game_bridge`'s force-delete-then-reimport
  block landed, bare `import fight_engine` sometimes resolved to root
  `/cage_dynasty/fight_engine.py`. That file didn't have the FLASH_KO /
  TKO_GNP / TKO_STANDING constants FI needed, so `from fight_engine
  import (...)` raised ImportError, `FIGHT_ENGINE_AVAILABLE` fell to
  False, and pre-gen quietly ran on the score-based coin-flip fallback —
  the two-month bug PREGEN-FULL-ENGINE-FIX1 (`e6e295e`, 2026-07-11;
  previously cited `efaf7f6` (which is GAMEPLAN-AI-SELECT1) in error)
  finally closed. Someone (probably Van, in a firefight) diagnosed the
  ImportError correctly but fixed it at the wrong end: hand-appended
  the missing constants to root fight_engine.py on the live box instead
  of fixing which file got imported. The proper fix — the `sys.path`
  insert + force-delete in `game_bridge.py:190-199` — came later and
  made this workaround inert. But the appended lines never got cleaned
  up, and they've sat on PA in a modified-but-tracked state ever since.
  **Values are meaningfully different from what live-play uses today.**
  Root-PA's `TKO_GNP_HEALTH_THRESHOLD = 30.0` vs live web's `18.0`
  post-GROUND-STOPPAGE-FIX1. Root-PA's `FLASH_KO_DAMAGE_THRESHOLD =
  25.0` vs live web's `70.0`. If any code path ever accidentally
  resolves `import fight_engine` to root, these old constants silently
  override the tuned live values and produce different fight outcomes.
  **NOT affecting live behavior today** — IMPORT-PATH-PROOF (`db15e3a`,
  2026-07-12) directly measures `fight_engine.__file__` in the running
  app; it names `/home/vandopegaming/cage_dynasty/cage_dynasty_web/fight_engine.py`,
  not root. That guard is now the standing regression test for this
  specific ghost.
  **Why `git pull` has silently tolerated this for months (the
  deploy-breaker warning):** `git pull` only refuses to overwrite a
  locally-modified tracked file when the incoming merge would touch
  that file. Root `fight_engine.py` hasn't been modified in the repo
  since commit `56bf807` (2026-04-27, initial commit) — nothing to
  overwrite, nothing to complain about. Every deploy has been
  fast-forwarding around it happily. **The trap springs the instant
  that file changes upstream.** Ship 1 (the `git rm` of the three
  orphaned CLI-era fight_engine.py copies, filed for post-arc) IS
  exactly that upstream change. Before shipping it, reconcile PA's
  dirty root copy first — restore it to repo state via console `git
  checkout HEAD -- fight_engine.py` on PA — or the pull will error
  mid-deploy and require manual intervention on a live box.

## C. PA wsgi.py VERIFIED match 2026-07-07 — full item (CLAUDE.md L403–435)

- **PA `wsgi.py` VERIFIED match** as of 2026-07-07 (via Files API fetch of
  `/var/www/vandopegaming_pythonanywhere_com_wsgi.py`, 479 bytes). Byte-
  equivalent to repo's `cage_dynasty_web/wsgi.py` modulo comments. sys.path
  adds `simulation/`, `narrative/`, `systems/`, `cage_dynasty_web/` in that
  insertion order (project_home ends up at index 0). Repo root is
  **explicitly NOT** on sys.path — this is what makes bare `import
  commentary` resolve to `narrative/commentary.py` on PA (see the CRITICAL
  block at the top of this file).
  **[STRIKE-AND-PRESERVE, 2026-08-15 post-`68dbd52` — the "VERIFIED match
  ... 479 bytes" and "Byte-equivalent to repo's `cage_dynasty_web/wsgi.py`
  modulo comments" claims are FALSE-AS-WRITTEN AT HEAD. PA `wsgi.py`
  measured 610 bytes this pass (+131 vs the recorded 479). See
  `### wsgi-610 [MEASURED, filed 2026-08-15]` in the Key constants section
  below. The sys.path insertion order and bare-import resolution behavior
  paragraph remains UNCHANGED-IN-EFFECT (verified independently across
  narrative/commentary + systems/fotn resolutions this pass). Text
  preserved for provenance; the byte-equivalence claim is retired, the
  behavior claim survives.]
  **[SUPERSEDING, 2026-09-07 interim deploy — the 2026-08-15 STRIKE's
  "PA measured 610 bytes" claim is FALSE at HEAD. PA `wsgi.py` measured
  **479 bytes** this pass (md5 `91531930abb2f818ccc21cad7b6c6386`); repo
  `cage_dynasty_web/wsgi.py` is 610 bytes. The 131-byte delta is
  comments + whitespace only; functional `sys.path.insert` lines are
  byte-identical between PA and repo. This exactly matches the 2026-08-20
  correction filed at
  `claude/claude_md_archive_2026b.md:379-407` (`### wsgi-610` re-measured);
  the 2026-08-15 STRIKE was an intermediate observation superseded 5 days
  later and not corrected here until now. sys.path insertion order and
  bare-import resolution behavior UNCHANGED-IN-EFFECT (independently
  re-verified 2026-09-07 for fight_engine + fight_integration +
  commentary resolutions in `outputs/sm1/deploy1/step1_2_report.md` +
  `outputs/sm1/deploy1/pa_wsgi_verbatim.txt`). Full filing:
  `claude/interim_deploy_2026-09-07.md`.]

