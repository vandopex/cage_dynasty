# JUDO-SAMBO-BUCKET-DIAG1 — read-only scoping memo

**Read-only.** No code changes made. Findings and minimal-fix scope for
review.

---

## Summary

**Judo and Sambo DO have entries** in the canonical alias table
(`_SPECIALTY_ALIASES` at `game_bridge.py:522`) — they resolve to
`clinch_coach`. That bucket trains **`clinch_control` + `clinch_striking`**.

**Every other part of the codebase treats Judo/Sambo as grappling/
wrestler-family** — style-inference, attribute weights, gameplan bucket,
engine style-family sets. The specialty→bucket mapping is the outlier.

**Concrete symptom:** a coach with specialty `"judo"` (legacy save)
trains dirty-boxing clinch stats instead of the takedowns/top-control
grappling stats every other system says Judo emphasizes. Same for Sambo.

**Minimal fix scope:** 2 entries changed in `_SPECIALTY_ALIASES`. All
downstream consumers (`get_coach_trained_stats`, training-loop routing,
sc-check predicate) auto-inherit through the shared table — the
COACH-LOOKUP-REFACTOR-SHIP1 payoff. No six-site parallel edit needed.

---

## 1. Where Judo/Sambo currently route

### `_SPECIALTY_ALIASES` (`game_bridge.py:580-581`) — the canonical alias table

```python
"judo":             "clinch_coach",
"sambo":            "clinch_coach",
```

### `COACH_BUCKET_ATTRS['clinch_coach']` (`game_bridge.py:640`)

```python
"clinch_coach":    ["clinch_control", "clinch_striking"],
```

### Resolution flow

- `resolve_specialty("judo")` → `"clinch_coach"` (from `_SPECIALTY_ALIASES.get(key, 'mma_coach')` at line 609)
- `get_coach_trained_stats("judo")` → `["clinch_control", "clinch_striking"]` (via strict-key check at line 709 → bucket lookup at line 711)
- Training loop at `_apply_weekly_training:8603`: `cs_focus = resolve_specialty(cs_specialty)` → same clinch_coach bucket

---

## 2. What Judo/Sambo *should* train — evidence from the game's own tables

Every non-coach-mapping site that touches Judo/Sambo treats them as
**Wrestler-family grappling**, not clinch-family striking:

| Site | Judo | Sambo |
|---|---|---|
| `game_bridge.py:7124-7125` (fighter style translation) | → `"Wrestler"` | → `"Wrestler"` |
| `game_bridge.py:17045, 17051, 17671, 17676` (engine bucket) | → `"WRESTLER"` | → `"WRESTLER"` |
| `game_bridge.py:7520` (Judo attribute weights) | `takedowns 2.0, top_control 1.8, takedown_defense 1.6` | — |
| `game_bridge.py:7526` (Sambo attribute weights) | — | `takedowns 1.8, submissions 1.8, top_control 1.6` |
| `game_bridge.py:11306, 11312` (primary attribute) | `takedowns` | `takedowns` |
| `game_bridge.py:4994` (opponent gameplan category) | `"TAKEDOWN"` | `"TAKEDOWN"` |
| `game_bridge.py:19538` (`_specialty_to_archetype`) | `'grappling'` | `'grappling'` |
| `game_bridge.py:13162` (`_gameplan_from_specialty`) | `"SUBMISSION"` | `"SUBMISSION"` |
| `fight_engine.py:1422, 1466` (engine style family) | — | Grouped with `"wrestler"` |

**Nothing anywhere in the game codebase treats Judo or Sambo as
dirty-boxing/clinch-striking styles.** They are consistently
throw/pin/takedown grappling.

The `COACH_TYPES['clinch_coach']['style_match']` list at line 456 —
`['Judo', 'Sambo', 'Clinch Fighter', 'Pressure Fighter']` — is the
lone outlier. That aspirational list appears to be where the current
mapping originated: "the Clinch coach's specialty covers Judo/Sambo
fighters." But `clinch_coach`'s actual training bucket is
`clinch_control + clinch_striking`, which trains the wrong side of
the clinch — the *dirty boxing* side, not the *throw* side. The
aspirational list and the bucket contents drifted apart in the
Clinch split (COACH-CLINCH-SPLIT1), and the judo/sambo aliases were
routed on the aspirational reading rather than the bucket-actual
reading.

---

## 3. Consumer sites — do they route correctly?

Six consumer patterns exist per the COACH-LOOKUP-REFACTOR-DIAG1
enumeration. Because they all normalize through `_SPECIALTY_ALIASES`
(directly or via `resolve_specialty`), Judo/Sambo route consistently
through the same wrong bucket everywhere. Below is the audit:

| # | Site | Reads from | Judo/Sambo today | Correct? |
|---|---|---|---|---|
| 1 | `get_coach_trained_stats` (`game_bridge.py:696`) | `_SPECIALTY_ALIASES` | → `["clinch_control", "clinch_striking"]` | **WRONG** — routes to dirty-boxing stats |
| 2 | Training loop (`game_bridge.py:8603`) | `resolve_specialty` → `_SPECIALTY_ALIASES` | → `clinch_coach` bucket | **WRONG** — same source, same bug |
| 3 | sc-check predicate (`game_bridge.py:7783, 7787`) | `resolve_specialty(...) == 'sc_coach'` | → `clinch_coach` ≠ `sc_coach` → `False` | correct (Judo isn't S&C) |
| 4 | `_specialty_to_archetype` (`game_bridge.py:19538`) | inline set including `'judo', 'sambo'` | → `'grappling'` | **correct** — independent set membership |
| 5 | `_gameplan_from_specialty` (`game_bridge.py:13162`) | inline tuple including `"judo", "sambo"` | → `"SUBMISSION"` | correct — added by COACH-LOOKUP-REFACTOR-SHIP1 |
| 6 | `COACH_TYPE_MIGRATION` (`game_bridge.py:492-493`) | own dict | → `'clinch_coach'` display type | **display drift** — see §5 |

The two behavior-load-bearing sites (`get_coach_trained_stats` and the
training-loop routing) both read from the same alias table. **Fixing
`_SPECIALTY_ALIASES` fixes both simultaneously.** The other four sites
are either already correct on Judo/Sambo (`_specialty_to_archetype`,
`_gameplan_from_specialty`, sc-check) or handle display-only
attribution (`COACH_TYPE_MIGRATION`).

---

## 4. Are Judo/Sambo specialty strings actually generated today?

**No.** `game_start.py:723-731` — the modern `generate_starting_coaches`
canonical-type set — writes only the 7 Coach-3 keys (`boxing_coach`,
`muay_thai_coach`, `kickboxing_coach`, `wrestling_coach`, `bjj_coach`,
`clinch_coach`, `sc_coach`). Grep of `game_start.py` for `judo` /
`sambo`: zero matches.

**So the fix affects legacy saves only.** Any modern save whose
generation ran under current world_init writes `clinch_coach` as
the canonical string, and modern generation never emits `"judo"` or
`"sambo"` at all. But legacy saves (older world-gen shipped before
Coach-3, or manually-edited saves) can carry those specialty strings
— and today they train the wrong stats.

Not a hot-path bug on new games, but a real legacy-save correctness
gap. If a player loads a save with a Judo-specialty assistant coach,
that coach silently trains the wrong stats every training week.

---

## 5. `COACH_TYPE_MIGRATION` display drift

At `game_bridge.py:492-493`:
```python
'judo':             'clinch_coach',
'sambo':            'clinch_coach',
```

This routes legacy Judo/Sambo specialty strings to the **canonical
coach-type key** `clinch_coach` for display purposes (icon, banner
name in `COACH_TYPES`). If the training bucket for `"judo"` moves
from `clinch_coach` to `wrestling_coach` but this display migration
stays pointing at `clinch_coach`, the hire-card would show the
🥋-icon Clinch Coach banner while the coach trains Wrestling stats.
Consistency-only — not a bug, but a small display drift.

Optional secondary fix: point both to `wrestling_coach` too. Or leave
as-is if Van wants to preserve the "Clinch & Judo Coach" display
identity from `COACH_TYPES['clinch_coach']['name']` while the actual
training bucket routes correctly. Both are defensible.

---

## 6. Minimal fix — recommendation

**Change 2 lines in `_SPECIALTY_ALIASES`** (`game_bridge.py:580-581`):

```python
-    "judo":             "clinch_coach",
-    "sambo":            "clinch_coach",
+    "judo":             "wrestling_coach",
+    "sambo":            "wrestling_coach",
```

Rationale for `wrestling_coach` as the target:
- Judo attribute-weight table at line 7520 is `takedowns/top_control/takedown_defense` — pure wrestling stats.
- Style-family translation at line 7124/7125 returns `"Wrestler"` for both.
- Engine style bucket (`fight_engine.py:1422+`) groups Sambo with Wrestler.
- `wrestling_coach` bucket contents (`takedowns, takedown_defense, top_control`) match the throw/pin philosophy every other site attributes to Judo.

Sambo has some BJJ character too (line 7526 weights it `takedowns 1.8, submissions 1.8`), but a split "sambo → bjj_coach" case argues weaker: the primary attribute per line 11306 is `takedowns`, and the engine style-family sets group it with wrestler more consistently than with BJJ. Uniform `wrestling_coach` routing for both is the simpler minimal fix. If Van wants Sambo split off to `bjj_coach` later, that's a separate one-line decision.

**Consumer inheritance from the shared-table fix:**
- ✅ `get_coach_trained_stats("judo")` → `["takedowns", "takedown_defense", "top_control"]` (fixed)
- ✅ Training-loop `cs_focus = resolve_specialty("judo")` → `"wrestling_coach"` bucket (fixed)
- ✅ sc-check predicate: unchanged (`wrestling_coach` still ≠ `sc_coach`)
- ✅ `_specialty_to_archetype`: already correct at `'grappling'`
- ✅ `_gameplan_from_specialty`: already correct at `'SUBMISSION'`
- ⚠ `COACH_TYPE_MIGRATION`: still points at `'clinch_coach'` display type — display drift only, decide separately

**No six-site refactor needed.** The COACH-LOOKUP-REFACTOR-SHIP1
consolidation shipped exactly to make this kind of fix a single-table
edit. Two lines close both real symptoms; the display migration is an
optional consistency tweak Van should call separately.

---

## Recommendation

Two-line diff in `_SPECIALTY_ALIASES`. Balance-adjacent (training
correctness) — worth Van's review of the target bucket choice before
committing, but the scope is tight. Follow-up open: decide whether
`COACH_TYPE_MIGRATION`'s Judo/Sambo → clinch_coach display migration
should be aligned too, and whether Sambo deserves `bjj_coach` routing
distinct from Judo.

Read-only diagnostic ends here — nothing was changed.
