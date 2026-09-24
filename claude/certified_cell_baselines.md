# Certified cell baselines (symmetric skill)
Moved verbatim from CLAUDE.md L1010–1148 at cd6f7e80 (ARCHIVE4, 2026-09-22). Do not edit; history.


**Principle**: certified balance numbers live in this committed record
with their harness shape + N + CI, never in session conversation — an
uncommitted number mutates. Both of the entries below drifted precisely
because they lived only in chat. If you find yourself citing a balance
figure that isn't in this section, verify it against a fresh probe
before treating it as authoritative.

All numbers below are at symmetric OVR=75, 3-round non-title, gameplan=None
(neutral). Harness config passes `damage_multiplier=0.24`
(documented-was-misleading: per this file's KEY CONSTANTS,
`fight_integration` ignores config damage and uses
`FI_DAMAGE_MULTIPLIER=0.48`; numbers below at effective 0.48, not 0.24).
Probe harnesses were
committed inline in the referenced diag memos.

**⚠️ SUPERSEDING NOTE — 2026-07-20:** the "per this file's KEY CONSTANTS"
citation above was documented-was-inherited-false. KEY CONSTANTS itself
was falsified by STAGE 0d (`ba8cece`, 2026-07-12) — see the superseding
correction under `## Key constants` above. At HEAD, FI DOES read
`self.config.damage_multiplier` in the strike-damage path (currently
`fight_integration.py:867`), and no `FI_DAMAGE_MULTIPLIER` module const
exists in the engine files. The consequent claim "numbers below at
effective 0.48, not 0.24" still holds — what changed is the mechanism
(`FightConfig.damage_multiplier` dataclass field now, `FI_DAMAGE_MULTIPLIER`
module const before), not the effective value.

### Wr-BJJ (Wrestler vs BJJ Specialist)

- **Wrestler win rate ~48%** (Harness A 47.3% CI [43.3, 51.4] N=577;
  reproduces 47-49% across 3 harness shapes — see
  `outputs/wr_bjj_drift_diag1.md`).
- **BJJ submission path intact ~16.5%** (99/600 subs, all landed by
  the BJJ side).
- Verified byte-identical across the 8e3f670→efaf7f6 boundary by
  WR-BJJ-DRIFT-DIAG1 (2026-07-07) — the "this is the correct stable
  baseline, **not a regression**" framing was documented-was-overreach.
  Certifies the LIVE-PLAY path only, across GAMEPLAN-AI-SELECT1; does
  NOT cover the pre-gen engine (PREGEN-FULL-ENGINE-FIX1, `e6e295e`) —
  see coverage gap subsection below.
- **RETIRED**: the "60.2% CI [56.2, 64.0] N=600" figure never existed
  in any committed artifact — a mis-reference, likely conflated with
  Wr-Str's 60-70% band that GNP-BUFF certified. Do not treat 60.2%
  as a prior baseline in any future work.
- **48% is a design point, not a bug**: BJJ's off-back sub path has
  no symmetric wrestler answer at OVR=75-vs-OVR=75. Moving wrestler%
  upward here is a deliberate new tuning decision, not a
  restoration.

### Wr-BJJ — pre-gen coverage gap

The pre-gen coverage gap is REASONED from a proven-empty transitive import
graph, NOT measured by running fights across the e6e295e~1 → e6e295e
boundary. **No fight was run.** The measurement was scoped in the
reconciliation thread and then dropped because the import graph proved the
harness structurally cannot observe the pre-gen path — running fights would
have produced a null-by-construction diff, and reading that null as
"baseline survives" would have been false reassurance (the golden-master
coverage-gap pattern this file's own CRITICAL block at "GOLDEN MASTER IS A
FIGHT-ENGINE ORACLE" already warns against).

Reasoning voice, not measurement voice, is the honest attribution.

**Consequence:** the certified Wr-BJJ numbers above measure LIVE-PLAY only.
The pre-gen engine (PREGEN-FULL-ENGINE-FIX1, `e6e295e`) writes rival records
during world_init history simulation and is not covered by any certified
number in this section. No pre-gen Wr-BJJ baseline currently exists.

### Wr-Str (Wrestler vs Striker) — post-GNP-BUFF

- **Wrestler win rate 50.3%**, 95% CI [46.3, 54.3], N=600 (variance
  probe, stable, dispersion 0.67×).
- **RETIRED**: the GNP-BUFF commit message's "40%→67%, into 60-70%
  band" claim is retired — overstated from a single N=30 lucky draw
  matrix. Real gain was ~40%→50%.
- Residual gap to any 60% target is addressed by the asymmetric §7
  lever from `outputs/control_conversion_diag1.md` §7, **NOT another
  `GNP_DOMINANT_DAMAGE_MULT` bump** — that shared constant would
  re-break Wr-BJJ.

### Pool decision rate (live-save extraction, POOL-DEC-RATE1 2026-07-10)

- **DEC 44.6%** pool, 157 AI-vs-AI fights, `bridge_van_autosave.json`
  week 15 — read from `completed_events[].fights[].method`, zero
  simulation. In-band vs the 40-50% target.
- **SUB 1.3%** pool (2/157). Ground truth from the same extraction.
- Slot breakdown: main_event 7.7% DEC (13 fights, 9 title fights, all
  9 finished), co_main 26.7%, main_card 48.8%, prelim 50.8%,
  early_prelim 51.7%.
- **HEADLINE-FINISH-TRACE (2026-07-10)** — the headline finish spike is
  the 5-round confound, not a slot mechanic. Apples-to-apples restricted
  to finished-by-R3 (what prelims can reach): headline 50.0% vs prelim
  49.2%, statistically identical (P=0.56). 47% of headline finishes land
  in R4-R5, rounds prelims don't have. Code trace exhaustive:
  `is_title_fight` / `is_main_event` / `card_slot` do nothing in the
  fight-resolution path beyond setting `scheduled_rounds=5`. No damage
  boost, no threshold change, no attribute mutation — `FightConfig`
  constants (damage_multiplier=0.24, standup_threshold=10, submission
  thresholds) identical across slots. **No slot-specific finishing
  mechanism to fix.**
- Title-fight caveat (watch-on-accumulation, no task filed): 9/9
  finished on N=9 is significant vs prelim rate (P=0.0017) but Wilson
  CI on the underlying title finish rate is [70.1%, 100.0%] — could be
  anywhere from ~75% to ~99%. If another 10-20 title fights keep
  finishing, the CI tightens and the rate itself may become worth a
  fresh read.
- **RETIRED**: any citation of the decision rate at ~18-22%. That
  number was a main-event-slice observation (7.7% DEC on 13
  title-heavy headliners) mistaken for the pool rate. It never
  appeared in this doc — recording preemptively so a future session
  can't re-derive it from headline eyeballing and relaunch a
  finish-rate chase.
- **RETIRED**: any citation of the sub rate at 8-10%. Harness
  population artifact — synthetic BJJ Specialists rolled sub-offense
  means around 74; live-booked population means around 59. The sub
  gate is not broken; the synthetic pool inflated it. Live is 1.3%
  and stable.
- Caveats: N=157 is thin (single save, week 15). Sample is pre-fix
  engine (`e1be619`). The three 2026-07-10 ships are deployed but
  their AI-vs-AI-pool effect is unmeasured until fresh fights
  accumulate. In-band is confirmed for pre-fix, presumed for
  post-fix. Worth one clean re-read after enough post-fix fights
  land; not blocking.


- GROUP A — FINISH ECONOMY LANDED [COMMITTED as C45, 2026-09-06] → `claude/claude_md_archive_2026b.md` : L4198-4365 <!-- ARCHIVE2 -->
- C45 REFUTATION LEDGER → `claude/claude_md_archive_2026b.md` : L4366-4434 <!-- ARCHIVE2 -->
- MODULE-RELOAD1 (harness-pattern note, NOT scheduled) [filed C45] → `claude/claude_md_archive_2026b.md` : L4435-4468 <!-- ARCHIVE2 -->
- SUB-DRIFT → Group D (handoff from C45) → `claude/claude_md_archive_2026b.md` : L4469-4496 <!-- ARCHIVE2 -->
- C46 [COMMITTED as C46, 2026-09-06, engine only] — SAVELOAD1 T5: drop drift dm=0.48 pins + retire two triples → `claude/claude_md_archive_2026b.md` : L4497-4703 <!-- ARCHIVE2 -->
- INTERIM DEPLOY 2026-09-07 — b6e1d74 deployed, TPLFIX `f113004` follow-up → `claude/interim_deploy_2026-09-07.md`

**Number-of-record corrections (2026-09-07 interim deploy):**
- Handoff body's "6,217 lines at C47" is **FALSE**. True count is
  **6226** (`git show 62d3fc6:CLAUDE.md | wc -l`). ARCHIVE2's
  measurement was right; the handoff drift is filed only, not fixed
  in that doc (it's frozen-in-time thread state per its own header;
  the correction lives here + in `claude/interim_deploy_2026-09-07.md`).

