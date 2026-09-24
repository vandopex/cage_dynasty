# LOCAL PLAYTEST COMMAND
Moved verbatim from CLAUDE.md L959–988 at cd6f7e80 (ARCHIVE4, 2026-09-22). Do not edit; history.


[NOTE 2026-09-19: Van does not run local builds; this command is for cc harnesses and cc-side render probes only. The PYTHONPATH is load-bearing for those — see HARNESS-ENV1.]

```
PYTHONPATH="/Users/vandope/Desktop/Games/cage_dynasty/narrative:/Users/vandope/Desktop/Games/cage_dynasty/systems:/Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty_web" python3 /Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty_web/app.py
```

Open `http://localhost:5001/` (root redirects to `/new-game`).

**PYTHONPATH is load-bearing.** Without it, the `SIMULATION-SHIM`
warning fires (`🚨 world_init.FULL_ENGINE_AVAILABLE will be False`)
and pre-gen falls back to `simulate_fight_simple` — the crude 74%-
clamped fallback that produces near-random champions and belt
lineages. The Phase B/C population Van shipped only appears when
the PYTHONPATH is set correctly so `commentary` resolves via
`narrative/`, `systems.injury` resolves via `systems/`, and the
web tree's `fight_engine`/`fight_integration` load into
`simulation.*` via the shim. Verified this session — with the
PYTHONPATH set, boot log shows `✅ [IMPORT-PATH-PROOF]` for all
three plus `✅ Real game modules loaded successfully!`.

Ctrl-C stops the server (or `pkill -f "python3.*app.py"`).


- C41 [COMMITTED as C41, 2026-09-05] — badge/identity-trait dedupe + amateur random stat-traits removed → `claude/claude_md_archive_2026b.md` : L3807-3868 <!-- ARCHIVE2 -->
- C42 [COMMITTED as C42, 2026-09-05] — life-sim design filings → `claude/claude_md_archive_2026b.md` : L3869-3944 <!-- ARCHIVE2 -->
- C43 [COMMITTED as C43, 2026-09-05] — P5-C calibration spec ratified + list reconciliation → `claude/claude_md_archive_2026b.md` : L3945-4009 <!-- ARCHIVE2 -->
- C44 [COMMITTED as C44, 2026-09-05] — P5-C Phase 0 COMPLETE (baseline of record + Van rulings + GAMEPLAN1 / PROTRAIT1) → `claude/claude_md_archive_2026b.md` : L4010-4121 <!-- ARCHIVE2 -->
- Van P5-C RULINGS (2026-09-05, filed) → `claude/claude_md_archive_2026b.md` : L4122-4137 <!-- ARCHIVE2 -->
- Scope-doc backlog additions (this ship) → `claude/claude_md_archive_2026b.md` : L4138-4197 <!-- ARCHIVE2 -->
