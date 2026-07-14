# ORACLE-BRIDGE1 — save-level golden master

**Scope:** a wider-than-Stage-0c oracle that observes `game_bridge`'s
orchestration layer. Prerequisite for Stage 2a (fight-integration loop
relocation into `fight_engine`). Complementary to, not replacing,
`outputs/stage0c_golden_master/`.

## Files

| File | Purpose |
|------|---------|
| `_common.py` | sys.path + `uuid.uuid4` seed patch. Import first; every other module depends on it. |
| `fixture_generator.py` | Runs the game deterministically, captures wide vector, writes `fixture.json`. |
| `fixture.json` | Baseline: seed=42, 12-wk MAIN tier + 4-fight PLAYER tier, 78 captured fights. |
| `checker.py` | Re-runs the game, diffs each fight vector, exits non-zero on any localized field divergence. |
| `perturbation_test.py` | Sabotages 6 named `game_bridge` decisions + 1 narrow-vector case, confirms fixture catches each on a localized field. |
| `perturbation_full_diff.py` | Forensic: dump every divergent field for one perturbation (not just first). |
| `full_diff.py` | Same forensic, unperturbed diff. |
| `seed_scan.py` | Coverage scan: title fights + injuries across seeds. |
| `inspect_keys.py` | Debug: dump `_fight_commentary` keys after a run. |
| `README.md` | This file. |

## Usage

```
# Regenerate fixture — ONLY when you deliberately change what's captured
PYTHONHASHSEED=0 python3 outputs/oracle_bridge/fixture_generator.py

# Check current tree against fixture (should PASS after a no-behavior-change edit)
PYTHONHASHSEED=0 python3 outputs/oracle_bridge/checker.py

# Prove the checker discriminates on real fight fields (should print 7/7)
PYTHONHASHSEED=0 python3 outputs/oracle_bridge/perturbation_test.py

# Forensic: dump every divergent field for one perturbation
PYTHONHASHSEED=0 python3 outputs/oracle_bridge/perturbation_full_diff.py 2_gameplan_flip
```

## Determinism

`uuid.uuid4()` normally uses `os.urandom`, which ignores `random.seed()`.
`_common.py` monkey-patches `uuid.uuid4` to a seeded `random.Random(42)`
stream. Every fighter / camp / fight / event ID becomes reproducible;
set iteration over those IDs becomes deterministic; the whole world sim
becomes byte-equal across subprocess-fresh runs.

**The patch lives in the fixture harness only. Production code is
untouched** — live app still calls stdlib `uuid.uuid4()`. See CLAUDE.md's
`DOCS-SEED-NONDETERMINISM1` critical block for the load-bearing
consequence.

## Coverage (seed=42, 12 weeks + 4 player fights)

- 78 captured fights (74 Path A / 4 PLAYER tier)
- 7 events, all 5 card slots
- All 9 weight classes, 11 fighting styles
- **7 title fights** (5R config path — was 0 in v1 due to Path A never
  passing `is_title_fight` as a kwarg to `simulate_narrated_fight`; v2
  reads the flag from `_completed_events` in an enrichment pass)
- **20 fight-adjacent injuries** (read from `_news_items` category='injury')

The Path A `is_title_fight` finding is itself worth reading —
`game_bridge.py:13633-13644` calls `_simulate_narrated_fight_fn(...)`
WITHOUT the `is_title_fight` kwarg. The engine determines title-ness
purely from `rounds=5`. Any fixture that captures only the fight-fn
kwargs will under-count title fights across the whole Path A world.

## Vector — INPUTS, OUTPUTS, STATE DELTAS

### Inputs to `simulate_narrated_fight` (what game_bridge passes)

- `fa1`, `fa2` — `FighterAttributes` dicts: per-stat vector, fighting_style,
  weight, height, reach.
- `rounds`, `is_title_fight`, `is_main_event`.
- `starting_stamina_f1/f2` — the post-fatigue-wiring values (this is
  what perturbation #3 catches).
- `gameplan_f1/f2` — `Gameplan` dict: aggression + range_bias + other
  levers (what perturbations #2 and #N catch).
- `card_slot`.
- `intro_f1/f2_present` — bool (intro dicts don't hash cleanly; presence
  is the signal).
- `config` — `FightConfig` dict: damage_multiplier, exchanges_per_round,
  standup_threshold, submission thresholds (what perturbation #1 catches).

### Pre-fight state per fighter (added because inputs matter — outputs might look plausible)

- `wins`, `losses`, `draws`, `ko_wins`, `sub_wins`, `ko_losses`, `sub_losses`
- `overall_rating`, `fighting_style`, `weight_class`, `is_champion`
- `fatigue`, `chin`, `cardio` (from `_fighter_data`)
- `career_strikes`, `career_takedowns`, `career_sub_attempts`, `career_control_time`
- `career_fotn_awards`
- `fight_history_len`
- `injury_active`

Same fields captured **post-fight** to observe deltas.

### Outputs from the engine

- `engine_result.{winner_id, loser_id, method, finish_round, finish_time, decision_type, sub_type}`
- `engine_result.fighter1_stats[]`, `fighter2_stats[]` — per-round dicts
- `engine_result.judge_scores`
- `engine_result.commentary_sha16`, `commentary_len`, `key_moments_len`

### Session-total (backstop only — the checker does NOT gate on these)

- `meta.commentary_stored_key_count`
- `meta.commentary_session_sha16`

Recorded for forensics. **A perturbation that only trips a hash without
changing any per-fight localized field is a perturbation the vector
cannot localize.** The v1 revision proved that gating on session hashes
produces a fake catch rate; every perturbation needs a per-fight signal.

### Enrichment fields (added post-run from source of truth)

- `source_is_title_fight` (from `_completed_events[i]['fights'][j]`)
- `source_card_slot`
- `source_fight_id_prefix`
- `stored_commentary_sha16` (per-fight hash, matched by `(week, f1_id, f2_id)`)
- `stored_commentary_key` (`PRESENT`/`MISSING` — what perturbation #6 catches)
- `injury_after_fighter1/2` (from `_news_items` matched by fighter+week)

## Discrimination — honest 7/7 on localized fight fields

Every perturbation is caught by a specific field on a specific fight
index. Not a session hash. The checker prioritizes informative fields
(direct inputs, direct outputs, per-fight state) over
alphabetically-first noise fields like `commentary_len`.

| # | Perturbation | Caught by | Baseline → Perturbed |
|---|--------------|-----------|----------------------|
| 1 | Config `submission_progress_to_finish` 70.0→65.0 | `fights[0].config.submission_progress_to_finish` | 70.0 != 65.0 |
| 2 | Gameplan map `AGGRESSIVE`: 1 → -1 | `fights[74].gameplan_f1.aggression` | 1 != -1 |
| 3 | Path A + player-tier stamina forced to constant 100.0 | `fights[75].starting_stamina_f1` | 95.0 != 100.0 |
| 4 | `_make_fighter_attrs` `fighting_style` → None | `fights[0].fa1.fighting_style` | str != NoneType |
| 5 | `_build_intro_dict` returns `{}` | `fights[0].stored_commentary_sha16` | different (intro line missing) |
| 6 | Skip `_fight_commentary[key] = ...` at Path A | `fights[0].stored_commentary_key` | PRESENT != MISSING |
| N | Narrow-vector: `BALANCED`: 0 → 1 | `fights[0].gameplan_f1` | NoneType != dict |

**Notes on individual catches:**

- **#1 is NOT `damage_multiplier`.** Any change to
  `damage_multiplier`, `exchanges_per_round`, or `standup_threshold`
  trips Stage 0d's `_assert_sanctioned_config` (fight_engine.py:~863)
  before the fight runs. See CLAUDE.md's KNOWN DEFECTS section — this
  is the same "early loud tripwire" pattern that limits Stage 0c
  discrimination testing. The perturbation targets
  `submission_progress_to_finish` instead, a non-asserted `FightConfig`
  field.
- **#5 catches ONLY on `stored_commentary_sha16`.** Full-diff verified:
  the intro dict feeds ONLY commentary text, doesn't affect fight
  simulation. No cleaner signal exists. Per-fight sha (not session) —
  meets the localized-field rule.
- **#6 catches on structural `PRESENT != MISSING`.** Not a hash
  comparison — a per-fight presence check.

## Rules

- Perturbation tests **must** revert every edit at the end.
  `perturbation_test.py` uses `git checkout HEAD -- cage_dynasty_web/game_bridge.py`
  as the final revert step. If the run exits with non-zero, verify
  `git status` is clean before assuming anything.
- Regenerate `fixture.json` **only** when the vector shape changes or
  a deliberate behavior change is documented. Regenerating hides bugs.
- The Stage 0c fixture (`outputs/stage0c_golden_master/`) is not
  modified by this suite. Two instruments, different scopes.

## What this fixture does NOT observe

- Card assembly / matchmaking / pipeline density (unrelated to fight-fn).
- Route rendering / Flask session.
- Save/load round-trip.
- Any state whose change isn't downstream of a fight-fn call.

Filed for a later tier if needed: repeat matchups (would need 26-52 wk
window), interim titles, contract expiration effects on fight rosters.
