# STYLE1 ONE-JUDGE — Gate 0 filing (2026-11-13, addendum arc)

**Status: FILED with this commit.** This filing captures the Gate 0 /
ADDENDUM 1-5 arc as of 2026-11-13. Every number cites a report file at
file:line.

Nothing built. Reads only; three docs files (this filing + backlog edits
+ CLAUDE.md index line).

Report files, by sha256:

```
25112c7cae1c00bc1f892a6899ac2d2dd039b89001ad7969e9267d976b661e4f  outputs/style1_onejudge_gate0_192719.md
d93066ac60abc637ec90fb09b2f52cfed1db4d5f9a280654a7ce2eb80afe19e2  outputs/style1_onejudge_gate0_addendum_194044.md  (crashed run, not cited)
b3128bcb9c5f9dc4381f8478e601102ca84f8c186cd6b2ce56a4060909b6a1a9  outputs/style1_onejudge_gate0_addendum_194144.md
3e73aa89a2fe7ef2e0db607682833575b1c9b9ae2e19a466c3e646032f625db0  outputs/style1_onejudge_gate0_addendum2_195418.md
21928bcaf3939e4b04ecfec5f55995dfd03a2dbfcc290c05b415f6cc21b87706  outputs/style1_onejudge_gate0_addendum3_201314.md
8f407f18953f65f422476b3bd410e7d21070af801986547b2a08aba56379e034  outputs/style1_onejudge_gate0_addendum4_204842.md
79b1887ad2c8f12e08ae11065431c797eb88c8e1990bb8099d184f6597059787  outputs/style1_onejudge_gate0_addendum5_212547.md
```

## 1. MEASURED

Every row below cites the source report at `file:line`.

- **The two stored fields disagree for 0 of 293 fighters on P2** — on the
  fixed-instrument save, `_fighter_data['style']` equals
  `record.fighting_style` for every fighter. Cite:
  `outputs/style1_onejudge_gate0_192719.md:945`.
- **Detector reads the label as a fallback** for **102 of 293** fighters on P2
  (detector output changes when `fa.fighting_style` is set to None). Cite:
  `outputs/style1_onejudge_gate0_addendum2_195418.md:1217` (T ≠ S)
  and the raw detect-with/without-label trace at
  `outputs/style1_onejudge_gate0_addendum_194144.md`.
- **Today's engine's detect-key vs the stored label (T ≠ L) = 140** on P2.
  This is "how often does today's engine's chosen style disagree with the
  stored label?". Cite:
  `outputs/style1_onejudge_gate0_addendum2_195418.md:1215`.
- **Label-stripped detect vs label (S ≠ L) = 242** on P2. Cite:
  `outputs/style1_onejudge_gate0_addendum2_195418.md:1216`.
- **Per-label T == L table** (holders and matches; every label has ≥1 match).
  Cite: `outputs/style1_onejudge_gate0_addendum2_195418.md:1298`.
- **Sandbox edit sites** (the edit that produced 21.24%): ONE modified tracked
  file `cage_dynasty_web/fight_engine.py` in worktree `/tmp/cd-exp-style1-
  sandbox1`; full diff at
  `outputs/style1_onejudge_gate0_addendum2_195418.md:30`. The
  edit lives INSIDE `detect_fighter_style` (the function body), gated by env
  dials `ST1R2_L1/L2/L3`.
- **L1 resolution — 0 label-coercion leaks**: under sandbox1's L1 arm, the
  count of non-Balanced labels returning `'balanced'` is **0 / 293**. Cite:
  `outputs/style1_onejudge_gate0_addendum3_201314.md:48`. Both
  C1 controls pass (Balanced label → `'balanced'`; unmapped in-memory label
  → `'balanced'`).
- **Bridge passes an enum**: for all 11 labels on P2, the FighterAttributes
  reaching `detect_fighter_style` carries a `core.types.FightingStyle` member
  (not a raw display string). Cite:
  `outputs/style1_onejudge_gate0_addendum3_201314.md:7`.
- **Pre-gen 821 / 821 None**: during a fresh `new_game`, the engine entry
  `simulate_narrated_fight` was called 821 times, and ALL 821 calls had
  `fighter.fighting_style == None` on both sides (no label flows through
  world_init's pre-gen path). Cite:
  `outputs/style1_onejudge_gate0_addendum2_195418.md:1352` +
  path block at line 1350.
- **Same-seed rebuild identical**: P1 built twice with seed 20261113 — the
  sha256 of the sorted `(name, label, 19-stat-tuple)` list is byte-identical
  across the two runs. Cite:
  `outputs/style1_onejudge_gate0_addendum2_195418.md:1339`.

### 1a. Live and MC paths on a COPY of fixed save (ADDENDUM 4 + 5)

- Save copy loaded cleanly; sha256 of copy matches baseline
  `99a1b3191c54386a7f568e858feecc1386b33ebe155c96f233daac3aeb628f78`
  (`outputs/style1_onejudge_gate0_addendum4_204842.md:10`; re-verified
  `outputs/style1_onejudge_gate0_addendum5_212547.md:17`).
- Initial `fight_history` total (sum over 293 fighters) = **1645** on the
  loaded P2 copy. Cite: `outputs/style1_onejudge_gate0_addendum5_212547.md:18`.
- advance_week × 8 cap on the loaded P2 copy; per-week
  `fight_history` deltas (sum over fighters) as the Addendum 4 report
  prints them: week 1 = +18 (1645→1663), week 2 = +18 (1663→1681),
  week 3 = +0 (1681→1681), week 4 = +0 (1681→1681), week 5 = +22
  (1681→1703), week 6 = +0 (1703→1703), week 7 = +22 (1703→1725),
  week 8 = +24 (1725→1749). Cite:
  `outputs/style1_onejudge_gate0_addendum4_204842.md:19-55`.
  Addendum 4's engine-entry wrappers caught 0 calls [INFERRED cause:
  bridge holds an
  in-namespace reference to `simulate_narrated_fight` imported at bridge
  load time; a module-attribute rebind after bridge load does not reach
  that stale reference. Not confirmed by reading bridge's import block;
  cause is INFERRED from behavior. Candidate, untested:
  `claude/style1_filing_2026-11-13.md` section 6 records
  `game_bridge.py:213-216` deleting and re-importing the engine modules].
  Detect was wrapped via module attribute
  and DID catch: 1,375,006 calls over the 8 weeks
  (`outputs/style1_onejudge_gate0_addendum4_204842.md:15`), every call
  carrying a `core.types.FightingStyle` enum. Addendum 4's statement that
  "MC frame was not seen" was an artifact of its frame walker
  [INFERRED: `inspect.stack()[2:16]` filtered out `fight_engine.py`, so
  the actual caller — which is in fe.py — was invisible; not re-tested
  with a modified inspect call, cause INFERRED from the walker's filter
  code and Addendum 5's f_back result].
  Addendum 5 replaces that walk with `f_back` depth 40.
- **ADDENDUM 5 — one advance_week on the copy, f_back depth 40**:
  - **MC-tagged detect calls: 247,710**; **LIVE-tagged detect calls: 2,172**
    (MC is `_compute_mc_odds_for_fight` in the chain; LIVE is any other).
    Cite: `outputs/style1_onejudge_gate0_addendum5_212547.md:33-35`.
  - Three callers of `detect_fighter_style` by file:line (what E1's caller
    column shows, nothing more):
    `fight_engine.py:1666 (get_available_grappling_actions)`,
    `fight_engine.py:2017 (select_action)`,
    `fight_engine.py:2018 (select_action)`. Each caller is split equally
    across MC (82,570) and LIVE (724), outermost fi/fe entry
    `fight_integration.py:2704 (simulate_narrated_fight)` for all six rows.
    Cite: `outputs/style1_onejudge_gate0_addendum5_212547.md:23-31`.
  - `NONE` count on every caller row: **0** — the label is ALWAYS present
    on the FighterAttributes reaching detect through the live + MC paths
    on this save (distinct from the pre-gen path which had 821/821 None).
    Cite: `outputs/style1_onejudge_gate0_addendum5_212547.md:23-31`.
  - **Controls PASS**: direct `detect(fa, fighting_style=None)` recorded
    `repr=None`; stub function named `_compute_mc_odds_for_fight` was
    tagged MC. Cite:
    `outputs/style1_onejudge_gate0_addendum5_212547.md:38-41`.
  - E2 (direct MC-odds call) SKIPPED because E1's MC row was nonzero.
    Cite: `outputs/style1_onejudge_gate0_addendum5_212547.md:45`.
  - **`fight_engine.py:3998-3999` recorded ZERO detect calls** on both the
    LIVE and MC paths during the advance_week window (those two call sites
    are missing from the Addendum 5 table rows, which list only fe:1666,
    fe:2017, fe:2018 as callers). The path that reaches `fe:3998-3999`
    (the "MUAY THAI VS WRESTLER IN CLINCH" initiative-adjust block the
    first report described) was not identified by this gate. Cite:
    `outputs/style1_onejudge_gate0_addendum5_212547.md:23-31`.
- Rehash of original /tmp save AND `cage_dynasty_web/saves/` copy both
  match baseline after the whole run (reads did NOT mutate either file).
  Cite: `outputs/style1_onejudge_gate0_addendum5_212547.md:10-13`.

### 1b. READ (code read, not measured)

- **Label in scope as `fighter.style`** at the pre-gen FighterAttributes
  build (`cage_dynasty_web/world_init.py:2064`). The attribute is on the
  `GeneratedFighter` object in scope and is unread by the FighterAttributes
  kwargs at this call. Cite:
  `outputs/style1_onejudge_gate0_addendum3_201314.md:267`.
- **Amateur fight-decision at `cage_dynasty_web/amateur.py:1259`** reads
  `f1_win_prob` (computed at :1255 from composite effective scores on
  `.attributes.get(<stat>, <default>)`). No reference to
  `fight_engine.detect_fighter_style` or to `FighterAttributes`. Cite:
  `outputs/style1_onejudge_gate0_addendum4_204842.md:96`.

## 2. FALSE AS WRITTEN

- **293 (first report Step 5 count)** compared raw-upper(label) vs
  raw-lower(detect) — neither side through the engine's normalize+alias chain,
  so every fighter trivially mismatched and the count saturated at N. Not
  "the mismatch count". Cite:
  `outputs/style1_onejudge_gate0_addendum2_195418.md:1522`.
- **158 (first report's RERUN section)** compared `upper(label-via-alias-chain)`
  vs `upper(raw detect)` — label through the chain, detect uppercased only.
  Not "the mismatch count"; derivable but not a comparison via the same
  engine chain on both sides. Cite:
  `outputs/style1_onejudge_gate0_addendum2_195418.md:1522`.
- **"Simulated 1642 fights across 60 events" (world_init stdout)** — the
  engine wrapper counts **821** per-fight calls to `simulate_narrated_fight`,
  and the per-fighter history sum is 1651 (/2 = ~825). The stdout string
  reads "1642 fights", but 1642 = 2 × 821 exactly; this is a double-count
  shape (per-fighter-side entries, not per-fight). Cite:
  `outputs/style1_onejudge_gate0_addendum3_201314.md:295`.
- **ARCHITECT-SEAT ERROR, not a filing error**:
  `claude/style1_filing_2026-11-13.md` section 2a lists fe:1666,
  :2017-2018, :3998-3999 correctly as `detect_fighter_style` CALL SITES.
  The thread-opening note and the first Gate 0 prompt called them edit
  sites. The edit that produced 21.24% is inside the detector body.
  Sandbox diff bytes at
  `outputs/style1_onejudge_gate0_addendum2_195418.md:30`.
- **Strike list** of UNSUPPORTED lines from the first report's RERUN section
  (RERUN P1/P2 case-normalized count = 158; RERUN controls as stated) —
  marked UNSUPPORTED until A3/B3 reproduced or replaced. Cite:
  `outputs/style1_onejudge_gate0_addendum2_195418.md:1447`.
- **Addendum 2 B6 "live: calls_recorded 0 (MEASURED)" and
  "mc_odds: calls_recorded 0 (MEASURED)"** at
  `outputs/style1_onejudge_gate0_addendum2_195418.md:1345-1348` and
  `:1365-1368`. FALSE AS WRITTEN as evidence that live/MC do not fire.
  Cause of the blind wrappers NOT ESTABLISHED. Candidate, untested:
  `claude/style1_filing_2026-11-13.md` section 6 records
  `game_bridge.py:213-216` deleting and re-importing the engine modules.
  Replaced by Addendum 5's f_back depth-40 walk at
  `outputs/style1_onejudge_gate0_addendum5_212547.md:33-35`: 247,710
  MC-tagged and 2,172 LIVE-tagged detect calls in one week, 0 None.
- **Addendum 3 C3 "weeks 1-20: 0 live, 0 mc"** at
  `outputs/style1_onejudge_gate0_addendum3_201314.md:98-127` is
  **UNSUPPORTED**, not false. No detect wrapper was installed and
  `fight_history` growth was not recorded, so whether any fight ran in
  those 20 weeks is unknown. The "cards do not materialize" explanation
  was not measured. The wrappers in that run were installed before
  `game_bridge` was imported.
- **DRAFT ERROR (this filing, pre-Addendum-5)** — an earlier revision of
  Section 3 contained the sentence "live-week detect did not fire during
  the 8-week advance window on this save; no measurement of the per-call
  fighting_style." That was wrong. **Measured replacement**: live-week
  detect fires copiously on the loaded P2 copy — 1,375,006 calls over
  8 weeks (Addendum 4), 249,884 in one week via f_back (Addendum 5), all
  with a `core.types.FightingStyle` enum on `fa.fighting_style`, zero
  `None`s on either side through live or MC paths. The MC path dominates
  LIVE at ~114:1 (247,710 MC vs 2,172 LIVE in one week), consistent with
  the SLOW-WEEK1 finding of ≥95% event-week time in the MC precompute
  (`claude/backlog.md:38`). Cite:
  `outputs/style1_onejudge_gate0_addendum5_212547.md:33-35`. Reconciliation
  of 249,884 total vs 247,710 + 2,172 = 249,882: the two-call gap is the
  two control calls made after the advance_week (Addendum 5 reports
  "total detect calls this run (incl. control calls): 249884" at
  `outputs/style1_onejudge_gate0_addendum5_212547.md:19`).

## 3. NOT MEASURED

- **Amateur bout through the engine**: as read at `cage_dynasty_web/
  amateur.py:1208-1310`, amateur has its own fight sim and does not route
  through `fight_engine.simulate_fight` or
  `fight_integration.simulate_narrated_fight`. The engine-wrapper harness
  cannot see amateur fights.
- **Why P1 and P2 share 287 of 292 names** despite different fighter_id's
  and different stat tuples. Cause unknown.
- **Direct `_compute_mc_odds_for_fight(…)` call** — Addendum 5 E2 was
  correctly skipped (E1's MC row was 247,710, nonzero); so the MC path is
  established by the live advance, not by a direct invocation. The
  function's signature is pinned at `cage_dynasty_web/game_bridge.py:17753-
  17772`.
- **Live and MC paths on a FRESH save** — all live/MC detect measurements
  in this filing were made on a COPY of the fixed-instrument save (P2),
  which arrives at advance-time with scheduled fights ready to fire.
  Whether a FRESH `new_game` world would reach the same detect call
  shape on advance_week is NOT MEASURED — Addendum 3 C3 tried to measure
  it with blind engine-entry wrappers only (no detect wrapper), so its
  "0 live, 0 mc per week" result is uninformative about detect itself.
- **The type of `fighter.style`** at the pre-gen FighterAttributes build
  (`cage_dynasty_web/world_init.py:2064`). The attribute is in scope on
  the `GeneratedFighter` object (`world_init.py:3770` reads it as
  `str(getattr(fighter, 'style', '') or '')`), but whether it is a raw
  `str` or a `core.types.FightingStyle` enum on the object itself at
  :2064 was not measured by this gate.
- **The effect on pre-gen fights of the style-weight table** at
  `cage_dynasty_web/fight_engine.py:2388-2407` — pre-gen's 821/821 engine
  calls pass `fighter.fighting_style=None`, so the style-weight lookup
  falls through to the default `{"strike":1.0, "grapple":1.0,
  "submission":1.0}` row (fe:2439-2440) for every pre-gen fight (READ).
  How this shapes the pre-gen outcome distribution (champion lineages,
  win-rate by stored label, SUB share) was not measured.
- **What reaches `fight_engine.py:3998-3999`** — Addendum 5 recorded
  zero detect calls at those two lines on both LIVE and MC paths
  during the advance_week window. The block is the "MUAY THAI VS
  WRESTLER IN CLINCH" initiative-adjust path (READ). The condition that
  gates entry into this block was not identified, and no fight
  during the measured week fell into it.

## 4. RULINGS (Van, 2026-11-13)

Recommended by the architect seat; accepted by Van 2026-11-13.

- **Edit inside `detect_fighter_style`.** The one-judge slice is the
  detector body. Not the call sites.
- **Missing or unmapped label fights as `'balanced'` and is counted**;
  the gate requires that count to be zero before the slice ships.
- **Ladder code stays this slice.** The baseline ladder (post-L1 return)
  remains in place; the slice is strictly additive at the top (early
  return based on the label).
- **Pre-gen passes the label in the same commit.** Fixes
  `world_init.py:2064-2093` so pre-gen history fights see the same label
  the live engine sees.

## 4a. ARCHITECT-SEAT ERRORS

- **(a)** Addendum 1 A3 specified the label-stripped comparison and
  produced the 242 number. 242 is not the change size. The change size
  is `T ≠ L = 140` (Addendum 2 B3), the count where today's engine's
  detector return disagrees with the stored label via the same engine
  chain on both sides. 242 is the count where a label-stripped detector
  disagrees with the stored label — a different quantity.
- **(b)** The docs prompt that introduced "edit sites" asserted
  section 9 of `claude/style1_filing_2026-11-13.md` named edit sites
  without reading it. Section 2a of that filing lists fe:1666, :2017-
  2018, :3998-3999 correctly as CALL SITES (see the ARCHITECT-SEAT ERROR
  entry in section 2).
- **(c)** The first Gate 0 prompt adopted the opener's edit-site
  framing and carried it forward into this filing's early drafts. The
  edit that produced 21.24% is inside the detector body
  (sandbox1's `cage_dynasty_web/fight_engine.py:detect_fighter_style`
  early-return at the L1 arm); the three call sites are reads, not
  writes.

## 5. BACKLOG ROWS (updated / new)

- **STYLE1** (updated) — now carries T ≠ L = 140, S ≠ L = 242, T ≠ S = 102 on
  P2; pre-gen 821 / 821 None; label-coercion gate 0 / 293; same-seed
  reproducibility YES; sandbox-edit lives inside detector; pre-gen label
  owed in the same commit as the detector edit.
- **AMATEUR-STYLE1** (new, READ) — amateur bouts do NOT use the fighter's
  `fighting_style`. The decision line is `if random.random() < f1_win_prob:`
  at `cage_dynasty_web/amateur.py:1259`; `f1_win_prob` (amateur.py:1253-1256)
  is a function of effective-score diffs on `.attributes.get(<stat>, …)`.
  `amateur._simulate_fight` does not call `fight_engine.simulate_fight`,
  does not call `fight_integration.simulate_narrated_fight`, and does not
  read `FighterAttributes.fighting_style` for fight resolution. The
  `fighting_style` reach inside the :1370-1420 window is POST-fight
  attribute-gain, not fight resolution. If "the label is the one judge"
  is meant to apply to amateur bouts too, amateur needs its own slice.
- **PREGEN-FIGHTCOUNT1** (new, INFERRED) — `world_init.py`'s
  HistorySimulator stdout line `Simulated N fights across M events` reads
  `N = 1642` on a fresh `new_game` while the engine-wrapper per-fight call
  count is 821 (measured,
  `outputs/style1_onejudge_gate0_addendum3_201314.md`). The per-fighter
  `fight_history` aggregate (1651 entries across 293 fighters, half-sum
  825) sitting at ~2× the engine call count is EXPECTED — each fight
  writes one entry on each side (winner + loser), so 821 fights produce
  **1642 per-side entries**; the measured sum was **1651**; **9 entries
  are unexplained**. The only open question is what `N` in the stdout
  line `Simulated N fights` counts: fights (should equal 821), or
  per-side entries (matches 1642 but is not "fights"). INFERRED pending
  a read of `world_init.HistorySimulator`'s own `fight_history` append
  path at :2426 + extend at :2918.
