# GOLDEN MASTER IS A FIGHT-ENGINE ORACLE, NOT A LIVE-PLAY ORACLE
Moved verbatim from CLAUDE.md L92–199 at cd6f7e80 (ARCHIVE4, 2026-09-22). Do not edit; history.


**Measured empirically 2026-07-13** by the POISON-0.42 diagnostic. The
Stage 0c golden master at `outputs/stage0c_golden_master/checker.py`
imports `fight_engine` and `fight_integration` **directly** at
`:35-36`. It **never** imports `game_bridge`. Verified by installing
poison RuntimeErrors at three fallbacks in `game_bridge.py:210/212/269`
that raise on live-app import: the fixture returned **928/928 PASS
with the poison in place** because the fixture never loaded the module
that would have fired it.

**Consequence, load-bearing for the consolidation arc:**

- `game_bridge.py` is ~21,400 lines and is the orchestration layer
  through which every live fight actually runs. **The golden master
  does not cover it.** Any bug living in `game_bridge`'s fight path —
  a wrong config passed, a fallback captured, a knob dropped, a
  matchmaker firing that shouldn't — is **invisible to the gate this
  arc has been trusting**.
- **PATH-B-BOOKING1 is the proof this already happened**: 548 lines
  of broken booking, resolving ~53% of every fight for months, and
  the golden master was byte-identical the entire time it ran AND
  after we deleted it (`8ecec6f`). "928/928 unchanged" was recorded
  as confirmation the scoping held. It was equally confirmation that
  **the oracle can't see that layer at all**.
- Everywhere the arc's language says "928/928 proves live-play
  unchanged" is **overclaiming**. The correct claim is "928/928 proves
  the fight-engine layer is unchanged for the inputs in the fixture."
  Whether live-play behavior changed is a separate question the
  fixture does not answer.

**Prerequisite for Stage 2a:** Stage 2a physically relocates FI's
loop body into `fight_engine`. If `game_bridge` sits between the caller
and the code being moved (probable but unverified as of this notice),
then the gate for that relocation is not observing the caller. **The
oracle-coverage gap needs closing before Stage 2a, not after.** Filed
as ORACLE-COVERAGE1 (diagnostic).

**Fixture inputs and fixture module coverage are two different limits.**
Section §2 of "PRE-GEN WORLD COHERENCE epic" below already noted a
*fixture-input* gap (fixture lacks 5R non-title mains). This notice is
about the *fixture-module* gap — a strictly larger blind spot. Both
apply. Do not conflate.

**Fixture `repo_sha` records "generation-time HEAD", not "write-commit".**
The generator's `_repo_sha()` (`generator.py:415-417`) stamps
`git rev-parse HEAD` at generation — a different question from which
commit contains the fixture in git. For this fixture: `repo_sha` =
`6fdc341` (HEAD when generator ran); write-commit = `a475a82` (child
of `6fdc341`, adding the fixture and generator's synth-cell edits
together). Both true, different questions; the recorded value is not
a stale mistake to correct — it's accurate under the field's design.
Secondary limit: `git rev-parse HEAD` captures committed HEAD, not
working-tree, so a fixture generated from a dirty tree can't be fully
identified by `repo_sha` alone. Filed so a future session doesn't
re-investigate.

[STRIKE-AND-PRESERVE, 2026-08-15 post-`68dbd52` — see
`### STYLE-DEAD1 [MEASURED, bytes at HEAD 68dbd52]` in the Key
constants section below. The "production live-play is style-aware"
framing is MEASURED-FALSE at the OUTCOME layer: `_STYLE_STR_MAP`
in `game_bridge.py` emits enum NAMES; the `_FightingStyleEnum(...)`
construction two lines below is VALUE lookup; ValueError swallowed
by `except Exception: pass` → `style_mod = 0.0` every fight since
the map was written. The `fighting_style` enum IS populated on
`FighterAttributes` at construction (that part of the block below
remains correct), but the branch that would make style
outcome-affecting has never fired in production. Retroactive
re-reading also owed for any upset-probe / outcome-attribution
memo under `outputs/odds_*` that inherited this framing. Text
preserved for provenance; corrected reading is under the
STYLE-DEAD1 section.]

**Fixture is style-blind; production live-play is style-aware. Third
coverage limit on the 928/928 gate.**
Bytes-confirmed at HEAD `1f98b5f`, both bridges + both fixture replay
paths. Pre-gen's `world_init._fighter_to_attributes` constructs
`FighterAttributes` **without** the `fighting_style` kwarg → the enum
defaults to `None`. Live-play's `game_bridge._make_fighter_attrs`
constructs **with** `fighting_style = FightingStyle[_STYLE_MAP.get(...)]`
→ enum populated. Fixture's serialize path `fighter_attrs_to_dict` at
`outputs/stage0c_golden_master/generator.py` explicitly excludes
`fighting_style` (`if f.name != "fighting_style"`). Fixture's rehydrate
path `dict_to_fighter_attrs` at both `checker.py` and `generator.py`
is byte-identical: `return fe.FighterAttributes(**d, fighting_style=None)`.
So `expected_fe` faithfully mirrors production pre-gen (both style-blind),
but `expected_fi` diverges from production live-play (fixture blind,
production aware). FI's style-gated branches (7 clusters, grep-locatable
via the single-line fragment `.fighting_style, 'name', ''` in
`fight_integration.py` — the getattr call is broken across two lines so
the fuller pattern doesn't resolve as a one-line grep) fire the else
path in the fixture and enum paths in production. Consequence for the
arc: **928/928 certifies engine equivalence under style-blind conditions
only.** Whether a merged engine post-Stage-2a preserves live-play
behavior is not answerable from the fixture — the style-aware condition
production actually runs was never sampled. Same "coverage limit, not
coverage bug" framing as the two paragraphs above: FE-side is faithful,
FI-side is a distinct gap. Third limit alongside fixture-inputs and
fixture-modules; all three apply. Do not conflate.

Corollary, filed so a future v2-fixture audit doesn't re-scope it:
three FI style branches keyed on `'BRAWLER'` / `'SAMBO'` / `'JUDO'`
substrings in `fight_integration.py` are structurally unreachable in
production. `_STYLE_MAP` in `game_bridge.py` normalizes those strings to
`PRESSURE_FIGHTER` / `WRESTLER` / `WRESTLER` before enum construction,
and neither `FightingStyle` (11 members in `core/types.py`, none named
BRAWLER/SAMBO/JUDO) nor `world_init` generation ever emits them. Dead
in production under any fixture design.

