# CLAUDE.md ARCHIVE 2026A — pre-fight-model-arc history

This file was created 2026-09-05 by C28 (ARCHIVE1). Its content was MOVED VERBATIM from CLAUDE.md at HEAD `c507b4f` (C27); it was not summarized, reworded, or edited. Any change to this file is a defect.

Pointer back: CLAUDE.md § Key constants carries four pointer blocks (BLOCK 1-4) naming the sections that live here now. See CLAUDE.md at HEAD C27 or `git show c507b4f:CLAUDE.md` for the pre-split source-of-truth arrangement.
### STAGE 1 addendum — random-coupling hazard (STAGE1-PARITY1, 2026-07-14)

**Do NOT run a deeper draw-by-draw coupling audit.** That's the rabbit
hole — match three consumers, find a fourth, match four, find a fifth.
The port itself resolves the coupling by unification.

**Load-bearing finding for Stage 2a accumulator port** [MEASURED, grep-verified vs HEAD]: of the four ⚠️-PREVIOUSLY-STATED FI-only gates in `fight_integration.py:{974, 1016, 1033, 1052}` — **two are genuinely FI-only** (`_clinch_body_acc`, `_gnp_accumulation`); **one is FE-native and byte-identical** (leg-TKO on `leg_kicks_absorbed`); **one is present in FE with different, stronger constants** (rocked-shots ref stoppage — FE cap 0.35 vs FI cap 0.22, faster ramp, no composure discount). Firing frequency is what closes the attribution; code presence check does not. **Named trace item** (queued, requires the two-step allowlist widening at `fight_engine.py:863`'s `_assert_sanctioned_config`).

[SUPERSEDED — the "decomposition NOT obtainable before Stage 2a" claim in the archived body was true when filed; the decomposition was subsequently obtained. See `### STAGE 2a addendum — config vs engine, measured 2x2 [filed 2026-07-26]` and `### Framing correction 2026-08-01`.]

Full section archived: CLAUDE_archive.md → '### STAGE 1 addendum — random-coupling hazard (STAGE1-PARITY1, 2026-07-14)' (phase 2, 2026-08-15)

### STAGE 1 addendum — config-lever measurement [filed 2026-07-14]

**Governance rules that survive this section body's archival:**

- **Rule going forward: no arc scoping number gets quoted without
  an N and a seed count.** Direction claims fine; exact percentages
  need provenance. (Verbatim from archived body's tail; also carried
  in `## Key constants` above — canonical live copy.)
- **POPULATION-SPECIFIC governance:** archived body's four measured
  claims (53% closure, +19.6pp residual, "the full ~41pp" framing,
  aggregate share arithmetic) are population-specific per
  `### Framing correction — "the aggregate gap" is population-specific
  [filed 2026-08-01]` (still live below). Numbers are correct
  measurements of Stage 1 pooled 10-seed world_init only — not
  project-level or production quantities.

Full section archived: CLAUDE_archive.md → '### STAGE 1 addendum — config-lever measurement [filed 2026-07-14]' (phase 2, 2026-08-15)

### STAGE 2a addendum — config vs engine, measured 2x2 [filed 2026-07-26]

**MEASURED verdict Stage 2a sequencing relies on** (5 cells, N=1210 per cell, HEAD `7513bc9`; table verbatim from archived body):

| Cell | Engine | Config | Style | Finish % |
|---|---|---|---|---:|
| C1 | FE | `_TRIPLE_PRE_GEN_LEGACY` (55, 0.42, 6) | blind | 31.7% |
| C2 | FE | `_TRIPLE_LIVE_PLAY` (55, 0.48, 10)     | blind | 55.0% |
| C3 | FI | `_TRIPLE_LIVE_PLAY` (55, 0.48, 10)     | blind | 69.8% |
| C4 | FI | `_TRIPLE_PRE_GEN_LEGACY` (55, 0.42, 6) | blind | 45.3% |
| C5 | FI | `_TRIPLE_LIVE_PLAY` (55, 0.48, 10)     | aware | 69.1% |

**Decomposition (verbatim from archived body):** Config effect on FE = C2 − C1 = **+23.3pp**; Config effect on FI = C3 − C4 = **+24.5pp**; Engine effect at pre-gen config = C4 − C1 = **+13.6pp**; Engine effect at live config = C3 − C2 = **+14.8pp**. Both decomposition paths sum to **+38.1pp** aggregate C3 − C1.

**Consequence, without recommending anything** (verbatim from archived body): Config drift accounts for roughly **62%** of the measured gap (23.3-24.5pp of 38.1pp); engine mechanics account for roughly **38%** (13.6-14.8pp of 38.1pp). **Filed as an observation for sequencing review; no sequencing decision is made by this entry.**

**Population caveat, load-bearing** (verbatim from archived body): C1-C4 strip style (`fighting_style=None`), so all 1210 fights per cell are the **same symmetric OVR=75 pair** with only the seed varying. `n=1210` measures seed diversity, not matchup diversity. Only C5 varies fighters via the `STYLES × STYLES` enumeration.

[POPULATION-SPECIFIC — see ### Framing correction 2026-08-01. "The measured gap" here = the 2x2 symmetric OVR=75 harness aggregate (38.1pp), not a production quantity.]

Full section archived: CLAUDE_archive.md → '### STAGE 2a addendum — config vs engine, measured 2x2 [filed 2026-07-26]' (phase 2, 2026-08-15)

### STAGE 2a addendum — production-path measurement of the classmethod flip [filed 2026-08-01]

**What shipped** (verbatim from archived body): `eeb16b8` — `FightConfig.standard_fight()` and `.championship_fight()` flipped from `(55, 0.42, 6)` to `(55, 0.48, 10)`. Four literal values, two classmethods, no allowlist change: the target triple was already `_TRIPLE_LIVE_PLAY` at `fight_engine.py:853`, admitted at `:857`.

**Caller audit MEASURED (grep across cage_dynasty_web/ + stage0c_golden_master/, positive control run)** (verbatim): Exactly one production caller: `world_init.HistorySimulator.simulate_fight_full_engine` at `:1422`. In-play fights (game_bridge FI paths) were at live-play numbers all along; only frozen pre-player history was stuck.

**Production-path measurement** (`probe_worldinit_prod.py`, tier grading mirroring `world_init.py:2513-2522`, 38-fighter Lightweight pool, N=400, seed=1000, paired): finish 14.5% → 33.8%; KO 5.0% → 16.5%; TKO 4.5% → 10.75%; SUB 5.0% → 6.5%; DEC 80.75% → 61.25%. Direction MEASURED. **Magnitude NOT validated against production** — probe pairs uniformly at random; production books rank-adjacent. Uniform pairing over-represents large-mismatch fights.

**FINDING — population composition dominates the config dial** (verbatim from archived body). Three measurements of this same four-line change, differing only in who was fighting: symmetric OVR=75 harness pair **+23.6pp**; flat all-`average` pool **+6.8pp**; production tier grading **+19.3pp**. A 3.5× span from population alone. **Any finish-rate number in this project is a claim about a population before it is a claim about the engine.**

**Submission rate is invariant to this dial** (verbatim): +1.5pp on the production path; ~6-8% across all five 2x2 cells regardless of config or engine. This flip is a KO/TKO lever. No submission lever has been located.

**Known drift left standing, deliberately** (verbatim): `fight_engine.py:4448` (`quick_simulate`) hardcodes `(55, 0.42, 6)` inline and now disagrees with `standard_fight()`. Callers unaudited. Filed, not touched — single-purpose commit.

Full section archived: CLAUDE_archive.md → '### STAGE 2a addendum — production-path measurement of the classmethod flip [filed 2026-08-01]' (phase 2, 2026-08-15)

### Framing correction — "the aggregate gap" is population-specific [filed 2026-08-01]

**The correction.** Several entries in the STAGE 1 and STAGE 2a addenda above refer to "the 41pp gap," "the arc's known aggregate gap," "the known finish-rate gap," or "the measured gap" with a definite article, as if a single project-level quantity existed. It does not. Per the production-path addendum at `### STAGE 2a addendum — production-path measurement of the classmethod flip [filed 2026-08-01]`: finish-rate aggregates are population-specific, with a 3.5× span (+6.8pp to +23.6pp) measured for the same four-line change across three populations. The +41.4pp (Stage 1 pooled 10-seed world_init) and +38.1pp (2x2 symmetric OVR=75 harness) are correct measurements of their populations. Neither is "the" gap, and shares computed against them (53%, 62%) are shares of those denominators only — not of any production-observed quantity. The production-path probe measured +19.3pp aggregate on production tier grading, magnitude itself unvalidated against production matchmaking.

**Per-site disposition.** Marked inline with `[POPULATION-SPECIFIC — see ### Framing correction 2026-08-01]`: the "53% of the known finish-rate gap" claim (STAGE 1 addendum), the "53% of the arc's known aggregate gap" claim, the "+19.6pp survives (41.4pp known aggregate − 21.8pp)" claim, the "full ~41pp" framing-correction paragraph, and the "62% of the measured gap" consequence paragraph (2x2 addendum). The "offset-vs-mechanic decomposition NOT obtainable before Stage 2a" claim carries a supersession note instead — it was true when filed and was subsequently obtained by the 2x2. The aggregate-rate bullet ("76.9% vs 35.4% pooled") is left unmarked: its first sentence is a correct population-named measurement; this block governs its "arc's core divergence" phrasing.

**None of the marked numbers is arithmetically false.** 62% of 38.1pp is correct. What is corrected is the definite article — the promotion of one population's denominator to a project-level quantity. Original wording is preserved at every site; markers annotate, they do not reword.

### Builtin scorer status — never-fired fallback [filed 2026-08-15, FOTN full-fidelity wire, 8fd4573]

**`game_bridge._select_fotn_builtin` (currently `:18071-18096`) has never fired in production**, MEASURED via PA's `server.log` retention: no `⚠️ fotn not available — using builtin` entries; the primary `import fotn` path succeeds on every reload (see `### Architecture correction — top-level systems/ imports [filed 2026-08-15]` above).

**Status: documented fallback only.** Fires on either:
- `import fotn` failure (has not occurred in retention).
- `select_fotn` exception (previously silent; now logged as `⚠️ FOTN select_fotn failed, builtin fallback: {err}` per `8fd4573`'s Edit F — see the try/except at `game_bridge.py:~3985-3990`).

**Do not upgrade or extend the builtin.** `systems/fotn.py` is the live scorer. If the builtin ever needs to evolve, first confirm from PA `server.log` that it's actually firing — otherwise the work is inert.

### Follow-up filed — tier threshold recalibration [filed 2026-08-15, FOTN full-fidelity wire, 8fd4573]

**Tier thresholds oversaturate under full-fidelity scoring.** Harness `outputs/fotn_harness.py` at N=400 fights, seed=1000, measured post-fix:

| tier | threshold | share of fights | share of card winners (N=40) |
|---|---:|---:|---:|
| INSTANT CLASSIC | ≥300 | **32.25%** | **97.5%** |
| Fight of the Year Candidate | ≥200 | 29.25% | 2.5% |
| Excellent | ≥150 | 17.50% | — |
| Great | ≥100 | 8.25% | — |
| Good | ≥50 | 12.75% | — |
| Standard | <50 | 0.00% | — |

- NEW score range 72-620, mean 244.6, vs OLD 70-132, mean 91.9. The tier ladder (50/100/150/200/300 at `systems/fotn.py:310-330`) was calibrated to a scoring range fights in this world don't actually inhabit — real scores are ~5× wider than the tier spacing accommodates.
- **Recalibration is a scoped follow-up, not done here.** Ship discipline: fix the wire first (`8fd4573`), tune the ladder second.

**Two harness caveats, filed for the record:**
1. **3/400 fights carried empty per-round stats** (99.25% fire rate, not 100%). Cause **INFERRED not measured** — plausibly R1 stoppages where the round-stats append didn't fire before the engine returned. The scorer's gate at `systems/fotn.py:80` degrades gracefully (falls to `_calculate_basic_score`), so this is not a correctness bug even if the mechanism is unconfirmed. Worth a targeted probe if the 0.75% edge becomes interesting.
2. **Harness scored harness-built dicts, not bridge-built dicts.** The harness constructed fight dicts locally mirroring the post-patch Path B shape rather than exercising `bridge._simulate_card_fights` / `bridge.advance_week`. Wiring correctness is inferred from the diff (game_bridge.py edits attach the same `eng_result.fighter1_stats` reference the harness uses) but not measured end-to-end through the bridge. **Production-path confirmation owed at deploy:** `server.log` clean of `⚠️ FOTN select_fotn failed` entries (would surface any shape mismatch via the new logging from `8fd4573`), and templates rendering `event.fotn.excitement_tier` values above `"Excellent"` (which were structurally unreachable pre-fix). **→ MEASURED 2026-08-19 (post-`3e90dfe` PA deploy — same deploy verifying COMMENTARY-STALE1).** PA `server.log` grep `"FOTN select_fotn failed"` returned zero. Event **CD75** rendered `event.fotn.excitement_tier = "INSTANT CLASSIC"` (above `"Excellent"`) on the FOTN block in production. Owed-at-deploy status **CLOSED**; caveat #2 converts from INFERRED to MEASURED. Same-deploy piggyback: nothing in `3e90dfe`'s scope touches FOTN wiring — the caveat #2 owed evidence has been available on PA since `8fd4573` shipped, and 2026-08-19's watched-fight verification confirmed both.

- **Balance observation (INFERRED, single N=50 dev harness).**
  78-OVR vs 72-OVR (6-point gap) measured at p_f1=0.900 on the
  post-fix `_TRIPLE_LIVE_PLAY` config + per-fight-seeding
  (`outputs/mc_odds_harness_out.txt`, single N=50 batch, crc32-
  seeded). Small OVR gaps produce near-deterministic favorites.
  Consequences if the reading holds across seeds and an OVR-gap
  grid: escalation band rarely fires, upsets rare, competitive
  odds lines rare. **NOT an odds bug** — odds honestly report
  engine behavior. Filed as a fix-the-engine candidate; needs a
  proper multi-seed sweep across OVR gaps before any tuning
  conclusion. Prior single-batch readings under the old shared-
  sequence scheme (0.960 at same OVR pair, and 0.920 post-config-
  fix pre-seeding-change) are documented false-as-generalized
  (both measured under stale seeding + one pre-fix under wrong
  config).
- **N=50 noise floor (MEASURED).** M6a 10-block sweep on a
  symmetric clone pair scattered 0.34–0.64 across blocks
  (aggregate 0.482, per-block sd ≈ 0.08). Single N=50 batch 2σ
  ≈ ±14pp on a coin-flip pair. Escalated N=400 gives 2σ ≈ ±5pp.
  Step 3 display work must know this — near-even lines will
  read as 40-60% zone even when the true probability is 50%.
- **Live-inconsistency observation (MEASURED, docs-only).**
  Path A (`_run_real_engine`) and Path B (`_simulate_card_fights`)
  DIVERGE on the `is_main_event` sim kwarg for co_main slot
  fights: Path A `slot in ("main_event", "co_main")` → True;
  Path B `slot == "main_event"` → False. Latent live
  inconsistency, not introduced by the odds arc; MC mirrors both
  per ratified rule (a). Needs its own diagnosis; not this arc.
- **Refactor candidate (STRONG, parked).** Shared sim-invocation
  helper for Path A / Path B / MC. Three hand-built call sites
  already drifted once (the fallback-triple bug this parity gate
  caught). Touches both live paths so it needs its own
  equivalence gate — do not bundle with a feature ship. File
  and hold for its own single-purpose commit.
- **Cleanup candidate (C from Step 1b, parked).** Refactor
  `fight_integration.py:403-412` aggression buff out of in-place
  `FighterAttributes` mutation. Blocks bundle-reuse patterns.
  Not scheduled.

- **STRIKE-SKILL-DMG1 phase 1a [SHIPPED 2026-08-22, commits
  6df956e + 668a7b1; instruments c06b0f9 + 713c0a7 + 5cb1468; docs
  1b1ecee. DEPLOYED to PA 2026-08-22, HEAD 1b1ecee, proof-verified:
  PA `.git/refs/heads/main` reads
  `1b1ecee634de98b7a8099d3354b4077846612d01`; serving
  `cage_dynasty_web/fight_engine.py:468` reads
  `STRIKE_SKILL_DAMAGE_K        = 1.0` (Files-API grep, verbatim).**

  **DESIGN DECISION (Van, 2026-08-22).** Fix for ENGINE-STRIKE-SENS1
  mechanism #2 (DAMAGE-SKILL-ABSENT): one channel at a time,
  skill-into-damage first. Striking to remain higher-variance than
  grappling (family 88v55 target band 0.65-0.70, NOT parity with
  grappling's 0.80). Single-stat weakness and kick-cliff interaction
  deliberately deferred to phase 1b/1c rather than compensated by a
  higher K.

  **MECHANISM.** calculate_strike_damage (cage_dynasty_web/
  fight_engine.py) now applies, after the strength terms and before
  the kick cliffs:
      damage *= max(STRIKE_SKILL_DAMAGE_FLOOR,
                    1 + (STRIKE_SKILL_DAMAGE_K * (_skill - 75) / 100))
  Family mapping mirrors calculate_strike_success: boxing punches ->
  attacker.boxing; kicks -> attacker.kicks; clinch + fallback (incl.
  GnP menu) -> attacker.clinch_striking. Attacker-side only, zero RNG
  consumed, plain-global reads (sweepable by module attribute rebind).
  STRIKE_SKILL_DAMAGE_K = 1.0; STRIKE_SKILL_DAMAGE_FLOOR = 0.25
  (deterministically inert at K=1.0 for legal skills 1-99, factor
  range [0.26, 1.24]; exists to protect future K retunes). Reaches
  BOTH sim paths (fight_engine.py pre-gen caller + fight_integration
  live caller) by construction — ratified as intended: pre-gen and
  live-play must share physics or MC odds lie.

  **GATES (all MEASURED, artifacts in outputs/).**
  - Commit 1 (6df956e, K=0): bit-identical equivalence vs fresh
    baseline at c06b0f9 — data-only diff empty exit=0, MD5 collision
    on stripped streams. Arms E/F/G1/H3/J1, CRN, standup==10
    asserted per arm.
  - Commit 2 (668a7b1, K=1.0 + floor): per-arm CSV-domain MD5s
    bit-match the sweep's K=1.0 rows on all 5 arms (E 42ed2d78...,
    G1 6c2f82ac..., H3 03c579a0... first-500 under CRN, J1
    a8a5b680..., F 11d4be8c...). Hasher discrimination PROVEN before
    acceptance: E and G1 hashes distinct across all four sweep K
    files, tuple counts 2000 per source.
  - Discriminators: J1 (all-75) and F (grappling 88v55, striking
    75/75) bit-identical across K ∈ {0.5, 1.0, 1.5, 2.0} AND across
    both instruments. J1/F p_f1 reproduce the SENS1 filed values to
    4 decimals (0.4840 / 0.8035) — instrument continuity with the
    closed diagnostic confirmed at bit level.

  **K-CHOICE GRID (N=2000/arm, from
  outputs/strike_skill_dmg1_sweep_out.txt).** E (striking family
  88v55): 0.5365 baseline -> 0.6160 (K=0.5) / 0.6945 (K=1.0) /
  0.7610 (K=1.5) / 0.7895 (K=2.0); KO+TKO share 0.306->0.567.
  G1 (boxing alone 88v55): 0.4805 -> 0.5085/0.5200/0.5485/0.5590.
  H3 (kicks 74v61): ~0.464 flat across all K. (H3 K=0 baseline at
  N=2000 not measured this arc; SENS1's filed H3 baseline is
  0.4160 ±0.0441 at N=500 — same seeds, smaller sample, not a
  discrepancy.) K=1.0 chosen: E lands in the 0.65-0.70 band with
  KO+TKO 0.383; higher K rejected as using one dial to compensate
  for channels still broken (flat landing #1, kick cliffs) whose
  future fixes will stack on this one.

  **FINDINGS FILED WITH THE SHIP.**
  - G1 single-stat weakness: boxing-alone 88v55 reaches only 0.5590
    even at K=2.0 — a lone striking stat rides on a minority of
    offense while landing stays flat. Phase 2 (#1 landing curve)
    territory, not a K problem.
  - H3 K-flatness is arithmetic, not wiring: attacker kicks 74 sits
    at the 75 neutral point (factor ~0.99); lift comes only from the
    61-defender's weakened kick output, a minority slice. "Better
    kicker wins" needs phase 1b de-cliff, not more K.
  - Draws shrink as K rises (E arm: 65 -> 41). Partially explains
    the SENS1 "draws scale with striking gap" observation as
    damage-parity scoring ties that the dial breaks.

  **PROCESS INCIDENTS (this arc, logged not hidden).**
  - 713c0a7 fired after its own written STOP (cc self-flagged; Van
    accepted rather than reverted — a reset would have orphaned the
    sweep's provenance header). Standing rule since: commits fire
    ONLY on Van's literal "commit approved — go". Inferred/pattern
    approval does not qualify.
  - H3 N changed 500->2000 in the sweep without being flagged;
    caught by the architect from the grid. Instrument-config changes
    must be declared before results are read.
  - Commit-2 acceptance gate required an instrument swap (sweep
    recorded dict-domain hashes; acceptance needed CSV-domain).
    Swap was surfaced honestly and the replacement hasher was
    proven to discriminate (distinct E/G1 hashes across K) before
    the gate result was accepted. Correct handling; filed as the
    template for "adjusted instrument" cases.
  - Deploy-proof step: cc constructed a Files-API `curl` with the
    PA token as a plaintext literal in the `-H` header. The
    permission layer denied the request but did not redact the
    command display, exposing the token in the session transcript
    for the second (or third — see fragment ruling below) time.
    Rule (d) redaction must happen at command CONSTRUCTION, not
    just in the report layer. New standing construction pattern
    (cc-side, effective immediately): credentials are sourced
    into a `$_VAR` from a filesystem read (e.g. `deploy.sh:5`)
    and referenced by name; the literal never appears in any
    echoed command line. Rotation was ordered mandatory
    regardless of prior-rotation status. Two-sided revocation
    gate landed measured: old-token Files-API call returned HTTP
    `401` (leaked credential dead); new-token Files-API calls
    returned the PA HEAD and serving-file grep pastes above.
    **Fragment comparison waived — rotation and 401 revocation
    measured regardless, prior-rotation status left unresolved.**

  **QUEUE.** Phase 1b: replace kick cliffs (:2394-2398 region,
  ×1.25 / ×1.15 binaries) with a gradient, measured against the
  1a after-state; re-probe H3. Phase 1c candidates, each own arc:
  landing-curve retune (#1), classifier hysteresis (#3), SD
  disentangle (#5), judge-weight re-measure (#4 — may need nothing
  now that damage carries skill). Live-roster violence check
  (finish-rate drift on real save populations at K=1.0) owed
  opportunistically at next live card, alongside the carried PA
  timing measurement.

- **STRIKE-SKILL-DMG1 phase 1b [SHIPPED 2026-08-24, commits
  0562687 (inert wire) + a11d47b (de-cliff, K=1.0 live);
  instruments (outputs/, untracked): phase1b_baseline,
  hash_repair, phase1b_commit1_gate, phase1b_setupgate,
  phase1b_sweep, phase1b_commit2_gate, phase1b_damage_delta].
  DEPLOYED to PA 2026-08-24, HEAD 5429e0d, proof-verified: PA
  `.git/refs/heads/main` reads
  `5429e0d226d94a203bf8c0c527ad53d603a6040b`; serving
  `cage_dynasty_web/fight_engine.py:494` reads
  `KICK_GAP_DAMAGE_K            = 1.0` (Files-API, verbatim);
  KICK_CLIFFS_ENABLED: 0 matches in served file.**

  **DESIGN DECISION (Van, 2026-08-23).** De-cliff kicks via
  two-sided pure-gap gradient replacing the historical MUAY-THAI-
  VS-BOXER cliffs. Old cliffs at fight_engine.py:2432-2436 (pre-
  1b anchor): `if attacker.kicks >= 75 and defender.kicks < 60:
  damage *= 1.25` and `elif attacker.kicks >= 65 and defender.kicks
  < 50: damage *= 1.15` — level×side test, if/elif mutually
  exclusive (a strike where both guards were satisfied got only
  the ×1.25, never compounded). Erased structure: five regions of
  the level×side surface — (×1.25 region: att≥75 AND def<60),
  (×1.15 region: att∈[65,74] AND def<50, only reachable when the
  ×1.25 guard failed), (dead region: att<65, no bonus), (dead
  region: def≥60, no bonus regardless of attacker), (dead region:
  att∈[65,74] AND def∈[50,60): no bonus despite gaps up to 24 —
  the M1 dead zone). Gradient replaces all five with one level-
  independent gap function.
  K=1.0 chosen off the phase-1b measured sweep grid. E family
  value EXPLICITLY re-chosen at 0.7075 above the 1a 0.65-0.70
  band (band was measured under cliffs; re-choose is legitimate
  vs drift). H3 emphatic 74v61 tellability deliberately reserved
  for landing-curve arc (#1).

  **MECHANISM.** calculate_strike_damage
  (cage_dynasty_web/fight_engine.py at HEAD a11d47b) applies
  inside the existing "kick" strike-family guard, after the
  strength terms and the 1a skill factor:

      kick_gap = attacker.kicks - defender.kicks
      damage *= max(KICK_GAP_DAMAGE_FLOOR,
                    min(KICK_GAP_DAMAGE_CEIL,
                        1 + (KICK_GAP_DAMAGE_K * kick_gap / 100)))

  Constants (module-level at fight_engine.py:494-496 at a11d47b):
  KICK_GAP_DAMAGE_K = 1.0, KICK_GAP_DAMAGE_FLOOR = 0.5,
  KICK_GAP_DAMAGE_CEIL = 1.5. Plain-global reads at call time;
  sweep by attribute rebind, no source edit. Clamps [0.5, 1.5]
  are ACTIVE PROTECTION at nonzero K on extreme legal skill gaps
  up to ±98 (99-vs-1); unclamped factor at K=1.0 on gap 98 is
  1.98, clamped to 1.5. Distinct from the 1a floor which is
  deterministically inert on legal skill values.

  Kick-family scope (10 StrikeType members whose .value.lower()
  contains "kick"): LEG_KICK, BODY_KICK, HEAD_KICK, FRONT_KICK,
  SIDE_KICK, SPINNING_BACK_KICK, WHEEL_KICK, AXE_KICK, CALF_KICK,
  OBLIQUE_KICK. Knees (KNEE_BODY, KNEE_HEAD, FLYING_KNEE) NOT
  included — no "kick" substring; those route to
  clinch_striking via the 1a family-mapping else fallback.

  Attacker- and defender-side read; defender-side stays within
  the replaced cliffs' existing precedent — no new defender
  channel opens. Zero RNG consumed. Reaches both sim paths
  (fight_engine pre-gen caller + fight_integration live caller)
  by construction.

  **GATES (all MEASURED, artifacts in outputs/).**
  - Commit 1 (0562687, gradient wired inert at K=0, cliffs
    behind KICK_CLIFFS_ENABLED=True): six-arm bit-identity vs
    fresh 1b baseline at HEAD 5643d88. All PASS:
      E   42ed2d78060e807d5892b72482666d55
      G1  6c2f82ac46c5a476367f3c0684710237
      H3  d27078ed192dc3fc2cab0f5eaf345a19  (full-2000, new tracked)
      H4  b3bd8c0d4bfae111940d03426e7d2da8  (full-2000, first-look)
      J1  a8a5b6809e688395387e7e829b419460
      F   11d4be8c28902e9e26c6d627424663fe
  - Sweep-setup (before any K read): scratch cliff-deleted
    engine at /tmp/skssweep_scratch vs tracked engine with
    KICK_CLIFFS_ENABLED rebound False — both K=0 — six-arm
    bit-match. Proves the enable flag is a clean off-switch
    and Commit 2's source deletion is byte-equivalent to
    attribute rebind. Scratch deleted after PASS.
  - Sweep discriminator: J1 and F (and incidentally G1, all
    with kicks 75/75 → gap 0 → factor exactly 1.0 at any K)
    bit-identical across all K∈{0.5, 1.0, 1.5, 2.0} AND vs 1b
    baseline hashes. Bit-invariance under two-sided pure-gap
    gradient is arithmetic; the sweep measured it to confirm no
    non-kicks-family leak.
  - Commit 2 (a11d47b, cliffs deleted, K=1.0 source-set):
    six-arm bit-match vs sweep K=1.0 rows. Post-edit engine
    reproduces sweep-time attribute rebind exactly:
      E   c94f2f6f488e940d0c26094fa33fe0a4  PASS
      G1  6c2f82ac46c5a476367f3c0684710237  PASS
      H3  2f1d2034aa308391ea487dfe776adda1  PASS
      H4  8cc3029309b1c88b2c08628a511c0f5b  PASS
      J1  a8a5b6809e688395387e7e829b419460  PASS
      F   11d4be8c28902e9e26c6d627424663fe  PASS

  **K-GRID (N=2000/arm, from
  outputs/strike_skill_dmg1_phase1b_sweep_out.txt).**

       K  arm    p_fav     ±2σ  KO+TKO  kotko%  finish  draws  mn_rnds
     0.5  E    0.6865  0.0207     733  0.3665    1122     62   2.482
     0.5  G1   0.5200  0.0223     452  0.2260     823     72   2.601
     0.5  H3   0.4710  0.0223     440  0.2200     824     80   2.614
     0.5  H4   0.5210  0.0223     680  0.3400     971     75   2.611
     0.5  J1   0.4840  0.0223     925  0.4625    1120     82   2.635
     0.5  F    0.8035  0.0178     568  0.2840     798     28   2.647
     1.0  E    0.7075  0.0203     833  0.4165    1211     50   2.446
     1.0  G1   0.5200  0.0223     452  0.2260     823     72   2.601
     1.0  H3   0.4840  0.0223     458  0.2290     839     69   2.606
     1.0  H4   0.5590  0.0222     763  0.3815    1045     63   2.571
     1.0  J1   0.4840  0.0223     925  0.4625    1120     82   2.635
     1.0  F    0.8035  0.0178     568  0.2840     798     28   2.647
     1.5  E    0.7290  0.0199     931  0.4655    1294     49   2.405
     1.5  G1   0.5200  0.0223     452  0.2260     823     72   2.601
     1.5  H3   0.4985  0.0224     458  0.2290     841     67   2.603
     1.5  H4   0.6000  0.0219     853  0.4265    1117     53   2.546
     1.5  J1   0.4840  0.0223     925  0.4625    1120     82   2.635
     1.5  F    0.8035  0.0178     568  0.2840     798     28   2.647
     2.0  E    0.7295  0.0199     934  0.4670    1296     48   2.404  BOTH BOUND
     2.0  G1   0.5200  0.0223     452  0.2260     823     72   2.601
     2.0  H3   0.5060  0.0224     479  0.2395     864     73   2.599
     2.0  H4   0.6270  0.0216     909  0.4545    1166     54   2.511
     2.0  J1   0.4840  0.0223     925  0.4625    1120     82   2.635
     2.0  F    0.8035  0.0178     568  0.2840     798     28   2.647

  Clamp-bound cells: E at K=2.0 only (gap 33, unclamped factor
  1.660 clamps to CEIL 1.5 on favored side; symmetric −1.660
  clamps to FLOOR 0.5 on weak). H4 at K=2.0 gap 25 → factor
  exactly 1.500 = CEIL boundary (not strictly clamped per
  `> ceil`; symmetric −25 → 0.500 = FLOOR boundary).

  Cliffs-off K=0 floor (setup-gate run (a), same 12000 sims,
  before gradient engages): E 0.6570, G1 0.5200, H3 0.4640,
  H4 0.4930, J1 0.4840, F 0.8035. Refill lens vs cliffs-on
  baseline at chosen K=1.0:
  - E (striking family 88v55; kick gap 33): cliff worth +3.75pp
    (0.6570→0.6945); gradient K=1.0 gives +5.05pp (→0.7075).
    Surplus explained by weak-side penalty + in-between gaps
    the cliffs missed.
  - H4 (kicks 80v55, gap 25): cliff worth +5.55pp
    (0.4930→0.5485); gradient K=1.0 gives +6.60pp (→0.5590).
    Conservation point: gap 25 at K=1.0 is ×1.25 exact.
  - H3 (kicks 74v61, gap 13): cliff never fired at 74v61
    (74 < 75); gradient K=1.0 gives +2.00pp (0.4640→0.4840).
    Tellable in direction, honestly modest.

  **AGGREGATE DAMAGE DELTA (§8, N=2000/arm, MEASURED, cliffs-on
  K=0 baseline vs cliffs-off K=1.0 post-Commit-2).**

    arm  metric                     cliffs-on K=0  cliffs-off K=1.0     Δ         %
    H3   kick_dmg / fight               39.4255            40.0700  +0.6445   +1.63%
    H3   kick_dmg / landed kick          8.0272             8.0892  +0.0621   +0.77%
    H4   kick_dmg / fight               68.6900            63.9894  −4.7006   −6.85%
    H4   kick_dmg / landed kick          9.7849             9.0959  −0.6890   −7.04%

  H4 aggregate landed-kick damage DROPS despite favored p_fav
  rising (0.5485 → 0.5590). Two-sided penalty on 55-side landed
  kicks (gap −25 → ×0.75, where cliff gave ×1.00) redistributes
  damage away from the weak side even though the favored side
  sees ×1.25 (identical to old cliff). "Weaker kicker's rally
  goes nowhere" made concrete on the canonical-cliff pair. H3's
  near-null per-landed-kick change is the two-sided factors
  1.13 / 0.87 canceling in aggregate at gap 13.

  **PRE-REGISTRATION MISS (house rule — logged, not absorbed).**
  Architect pre-registered in spec v2.1: "H3 moves from ~0.464
  into the low 0.50s." Measured at chosen K=1.0: H3 = 0.4840
  (+2.00pp above baseline). Direction correct, magnitude under
  prediction — low-0.50s only reached at K ≥ 1.5. Miss filed,
  not resolved by picking K=1.5 (which would be fitting the
  engine to the forecast per Van's ruling at K-pick).

  **FINDINGS FILED WITH THE SHIP.**
  - (a) Kicks-vs-boxing per-point stat-value imbalance
    (MEASURED). 1a boxing dial: G1 (boxing 88v55, gap 33) moved
    0.4805 (K=0) → 0.5200 (K=1.0), +3.95pp per 33-point boxing
    gap = 0.120 pp/point. 1b kicks gradient: H4 (kicks 80v55,
    gap 25) moved 0.4930 (cliffs-off K=0) → 0.5590 (cliffs-off
    K=1.0), +6.60pp per 25-point kicks gap = 0.264 pp/point.
    Ratio: per-point kick worth ≈ 2.2× per-point boxing worth.
    Channel architecture ruled CORRECT (damage dial on both;
    SENS1 mechanism #1 says punch-defense belongs in LANDING
    which is not yet wired). The imbalance is the opening
    argument for the landing-curve retune arc (#1 in SENS1
    QUEUE) — kicks defense goes through damage (per closed
    cliffs, now gradient), punch defense goes through landing
    (not yet wired) and neither the 1a dial nor 1b gradient
    can fix that from the damage side alone.
  - (b) Boxing family excludes BACKFIST and SUPERMAN_PUNCH
    (MEASURED via `calculate_strike_success:2269-2288` at HEAD
    a11d47b). Boxing branch tests strike ∈ {JAB, CROSS, HOOK,
    UPPERCUT, OVERHAND}. The other two "punch" strikes fall
    through the else to clinch_striking. Cosmetic labeling
    artifact — not outcome-affecting, but discoverable and
    worth cleaning as a 1c candidate.
  - (c) Weak-side ×0.60 stacked-factor watch item. At K=1.0
    on 80v55 kicks: favored-side stacked (1a × 1b) =
    1.05 × 1.25 = 1.3125; weak-side stacked = 0.80 × 0.75 =
    0.60. Weak-kick damage at 60% of pre-1a value. Live-roster
    violence check is the tripwire; if weak-side kicks feel
    visibly-nothing in live play, tuning surface is
    KICK_GAP_DAMAGE_FLOOR (raise from 0.5 toward 0.7 to
    compress the weak-side penalty while preserving the
    favored ceiling).

  **PROCESS INCIDENTS (this arc, logged not hidden).**
  - (a) M1 at Gate 0: handoff and spec paraphrase missed
    if/elif mutual exclusivity on the old cliff branches
    (paraphrase used `->` for both, reading as independent
    conditionals). Caught at Gate 0 by verbatim-match rule
    ("spec subordinates to code-at-HEAD"). Resolved as spec
    amendment v2.1 (docs-only, no filed number changed,
    mechanism / gates / constants untouched).
  - (b) Baseline hasher declared wrong domain. First 1b
    baseline ran with in-memory dict-domain MD5 hasher;
    targets were CSV-domain from actual sweep CSV disk reads.
    Cross-check reported all-MISMATCH despite p_fav MATCH
    exactly on J1 (0.4840) and F (0.8035). cc self-flagged as
    instrument-convention mismatch, not underlying-data.
    Repaired instrument-first per Van's rule: reproduced all
    five filed 1a hashes from historical sweep CSVs exactly
    (E, G1, H3 first-500, J1, F), discrimination re-proven
    (E and G1 distinct hashes across sweep K files, tuple
    counts 2000), then applied to 1b baseline under one
    convention. Continuity established under repaired hasher.
  - (c) Baseline harness nearly overwrote its own accepted
    CSV. The commit-1 gate initially reused the baseline
    harness for the post-edit rerun; the harness's fixed
    output path would have overwritten the accepted baseline
    artifact. Caught pre-damage by cc, run killed, baseline
    CSV proven intact by size+mtime unchanged. Distinct-
    output-path rule now standing for all gates going forward
    (commit-1 gate, setup-gate, commit-2 gate, damage-delta
    all used distinct paths).
  - (d) Two commit-message label errors, both caught in
    architect review before commit fired. Commit-1 message
    carried over 1a's "Attacker-side only. Zero RNG consumed."
    boilerplate — false for 1b's defender-side read. Commit-2
    message's refill-lens block labeled E as "kicks 88v55"
    when E is the striking-family arm (kicks are one component,
    gap 33). Both corrected before firing.

  **QUEUE.** 1b closes engine-side pending live-roster
  violence check. Live-roster check now covers 1a+1b jointly
  at next live card, alongside the carried PA timing
  measurement (both owed from earlier ships). Next arcs, each
  its own:
  - Landing-curve retune (#1) — PROMOTED by phase-1b finding
    (a): kicks-vs-boxing per-point imbalance is the damage-
    side landing at ~2.2× the boxing damage-side effect,
    because boxing's missing per-hit-damage channel goes
    through landing (not yet wired) and no damage-side dial
    can rebalance from the wrong channel.
  - Classifier hysteresis (#3).
  - SD disentangle (#5).
  - Judge-weight re-measure (#4) — may need nothing now that
    damage carries skill on both boxing (1a) and kicks (1b);
    re-measure at first live-roster check.

- **STRIKE-LANDING-AUDIT1 [CLOSED 2026-08-24, read-only
  diagnostic at HEAD a04faf4, no engine commits; instruments
  (outputs/, untracked): strike_landing_audit1_probe.py,
  strike_landing_audit1_root_probe.py,
  strike_landing_audit1_aggregate.py].**

  **INSTRUMENT + GATES (all MEASURED).** Wrapper on
  calculate_strike_success (CSS). RL1 decided from bytes at
  fight_integration.py:39 (fi imports CSS by name via
  `from fight_engine import`): BOTH fe.calculate_strike_success
  (call site fight_engine.py:3315) AND fi.calculate_strike_success
  (call site fight_integration.py:810) overwritten with a pure
  pass-through wrapper that consumes zero RNG. Per-call records
  (arm, seed, side, strike_type, family, landed, was_counter).

  Gates:
  - Gate 3a probe-off reused-hash bit-match — all 4 reused arms
    PASS raw md5:
      L-J1   a8a5b6809e688395387e7e829b419460
      L-B88  6c2f82ac46c5a476367f3c0684710237
      L-K74  2f1d2034aa308391ea487dfe776adda1
      F      11d4be8c28902e9e26c6d627424663fe
  - 9-arm discrimination — 9 distinct raw md5s AND 9 distinct
    normalized md5s.
  - Gate 3b probe-on ≡ probe-off — outcome CSVs bit-identical
    across all 9 arms (byte-level diff excluding `# mode:`
    header = 0 lines per arm). Wrapper proven pass-through on
    all arms, not one.
  - Normalized-domain (winner → slot1/slot2) sibling hasher NOW
    A PERMANENT SECONDARY CHECK. Filed norm targets for the
    four reused arms:
      L-J1   cace1efa4a3c8eabe8a976ec42a6f2ba
      L-B88  d2d943266a81c6817bbed5062b6fa37a
      L-K74  3e5de0d7963bc66cd2cf65ff1d981d0e
      F      78605664d38afa9b6abfaa83b9cc16ce  (captured this arc)

  **PROCESS INCIDENT (logged not hidden).** Gate 3a first ran
  FAIL on three relabeled reused arms (L-J1, L-B88, L-K74 all
  producing different raw md5s from their 1b commit-2 gate
  targets while F PASSED). FIGHTER-ID-SENSITIVITY-OBS1 was
  provisionally filed as a behavior claim ("fight outcomes are
  sensitive to fighter_id string content"), then RETRACTED on
  measurement: normalized-domain diff (winner → slot1/slot2)
  proved all 2000 rows bit-identical per arm — normalized md5
  matched between my probe and the historical 1b K=1.0 CSV
  (cace1efa for L-J1↔J1, d2d94326 for L-B88↔G1, 3e5de0d7 for
  L-K74↔H3). Zero engine sensitivity. Mechanism: the outcome
  hasher's own domain — the `winner` column carries the raw
  fighter_id string (e.g. "L-J1_slot1"), and when fighter_id
  strings differ across relabeled fixtures the hash differs even
  under bit-identical behavior. Refiled as instrument note.

  Root-cause path preserved for provenance
  (outputs/strike_landing_audit1_root_probe.py): monkeypatched
  hit-counters on all three suspect id-consumer sites recorded
  0 hits per site per arm on both L-J1 and F —
  game_bridge.py:7210 dormant (fighter_id IS in _fighter_data
  because _register_fighter populates it), game_bridge.py:7237
  md5 fallback dormant (all 18 _attr keys present in fdata),
  models.py:1202 not on the sim path. Additional stronger
  negative: str-hash-driven mechanisms (set-iteration order,
  hash-lookup path selection) ruled out by F's cross-process
  bit-stability despite PYTHONHASHSEED unset (random per
  process).

  Fix: `_FIGHTER_ID_SOURCE` mapping — reused arms (L-J1, L-B88,
  L-K74, F) use the 1b commit-2 gate's label strings for the
  fighter_id construction, so raw-hash bit-continuity with
  filed targets is preserved. Fixture attributes unchanged —
  only the fighter_id string differs. Normalized-domain hasher
  added as the permanent secondary check so label contamination
  can never masquerade as behavior again.

  Lesson filed for future instrument design: "outcome hash
  differs" is not "behavior differs" when the hash domain
  includes labels. Any hasher that includes identity columns
  (winner_id, loser_id, fighter1_id, fighter2_id, camp_id,
  etc.) needs a normalized-domain sibling before FAIL verdicts
  are trusted as behavior claims.

  **SENSITIVITY TABLES (N=2000/arm, HEAD a04faf4).**

  Family key: box=boxing (JAB/CROSS/HOOK/UPPERCUT/OVERHAND,
  offense=boxing), kck=kicks (10 members, offense=kicks),
  cex=clinch_explicit ({CLINCH_KNEE, CLINCH_ELBOW, DIRTY_BOXING},
  offense=clinch_striking, defense hybrid with takedowns),
  cft=clinch_fallthrough (else branch, 12 members enumerated,
  offense=clinch_striking, defense=striking_defense).

  Consolidated slot1-side (single-stat mover 88 or 74 on slot1
  for asymmetric arms):

    arm     p_slot1  box_att  box_rate  kck_att  kck_rate  cex_att  cex_rate  cft_att  cft_rate
    L-J1    0.4840   13954    0.4731    19430    0.4710    4058     0.4475    40458    0.4137
    L-B88   0.5200    9700    0.4724    12988    0.4642    2401     0.4344    45456    0.4093
    L-B74   0.4510    7581    0.4679    11055    0.4685    3291     0.4579    48828    0.4189
    L-K74   0.4840    7935    0.4713    10775    0.4604    3379     0.4492    49956    0.4178
    L-K78   0.5320   12819    0.4724    17824    0.4684    3398     0.4620    41751    0.4200
    L-K88   0.6000    8817    0.4621    13424    0.4660    2105     0.4204    46949    0.4090
    L-C88   0.5780    9098    0.4663    13182    0.4619    2319     0.4368    47174    0.4130
    L-C74   0.4900   13000    0.4772    17892    0.4797    3362     0.4619    42195    0.4200
    F       0.8035    7970    0.4593    10811    0.4621    3605     0.4352    53846    0.4059

  Consolidated slot2-side (single-stat holder 55 or 61 on slot2
  for asymmetric arms):

    arm     p_slot2  box_att  box_rate  kck_att  kck_rate  cex_att  cex_rate  cft_att  cft_rate
    L-J1    0.4750   13209    0.4860    18484    0.4798    3783     0.4843    36778    0.4294
    L-B88   0.4440    7186    0.4883    11620    0.4824    2023     0.4572    38671    0.4415
    L-B74   0.5155    7124    0.4969    11194    0.4761    2274     0.4415    42034    0.4289
    L-K74   0.4815    8049    0.4839    10451    0.4733    2035     0.4486    40353    0.4348
    L-K78   0.4395    9352    0.4846    11866    0.4728    2220     0.4604    39884    0.4261
    L-K88   0.3695    8041    0.4931    10115    0.4786    1692     0.4657    35595    0.4497
    L-C88   0.3900    7829    0.4918    10656    0.4815    1841     0.4666    35419    0.4285
    L-C74   0.4650    9495    0.4799    13412    0.4688    2315     0.4242    41941    0.4161
    F       0.1825    8185    0.4701    11633    0.4677    5569     0.4997    33556    0.4409

  Control-delta summary — own-family favored-side landing rate
  vs L-J1 control (all-75/75):
  - Boxing: L-B88 slot1 box_rate = 0.4724 vs L-J1 slot1
    box_rate = 0.4731. Δ = −0.0007 (−0.07pp). Effectively zero
    at 88v55.
  - Kicks: L-K74 slot1 kck_rate = 0.4604 (Δ = −0.0106
    (−1.06pp)), L-K78 slot1 = 0.4684 (Δ = −0.0026 (−0.26pp)),
    L-K88 slot1 = 0.4660 (Δ = −0.0050 (−0.50pp)) — flat-to-
    slightly-NEGATIVE across all three kick fixtures, INCLUDING
    L-K88 with the fight_engine.py :2317-2318 +10 offense
    landing cliff firing (att.kicks≥80 AND def.kicks<60). The
    cliff activates on every kick from slot1 in L-K88 yet
    aggregate landing rate is LOWER than control.
  - Clinch: L-C88 slot1 cex_rate = 0.4368 (Δ = −0.0107
    (−1.07pp)), L-C74 slot1 = 0.4619 (Δ = +0.0144 (+1.44pp)).
    Flat both directions. L-C88 fallthrough: 0.4130
    (Δ = −0.0007 (−0.07pp)). Flat.
  - Formula-predicted +2-3pp on 88v55 favored side (raw
    offense/(offense+defense+1)*0.5 spread at 88v55 delivers
    ~11.5pp pre-variance) is ABSENT from aggregate.

  VERDICT: the landing channel transmits ~nothing at aggregate.
  All p_fav movement observed on the asymmetric arms rides the
  1a/1b damage dials and fight-shape effects (attempt-volume
  redistribution, fatigue/momentum/state-modifier interactions),
  not the landing formula.

  **FINDINGS FILED.**
  - (a) Landing channel dead at aggregate (above). The
    landing-curve retune arc (#1 in SENS1 QUEUE, PROMOTED by
    1b finding (a)) is CONFIRMED against measurement. Its spec
    must address the state-modifier wash (grappler-pressure
    penalties at :2333-2363, stamina scaling at :2367-2368,
    rocked defender bonus at :2371-2372, variance at
    :2375-2376, upset branch at :2383-2388, and clamp
    [0.15, 0.85] at :2380) that appears to absorb skill-gap
    input BEFORE it reaches the final `landed = random.random()
    < success_chance` gate, not just the base-formula
    compression `0.20 + offense/(offense+defense+1) * 0.5`.
  - (b) Attempt-share hierarchy (MEASURED, slot1 aggregated
    across all 9 arms, ~663K attempts):
      cft ~62.9% > kicks ~19.2% > boxing ~13.7% > cex ~4.2%
    clinch_striking is the highest-leverage striking stat by
    volume (L-C88 p_slot1=0.578 > L-B88 p_slot1=0.520). Boxing
    weakness is double-layered: no landing sensitivity AND
    minority attempt share. When landing-curve retune ships,
    boxing needs BOTH a landing channel and either more attempt
    weight or acknowledgment that boxing skill will lift KO
    numbers via 1a damage but never push p_fav much on its own.
  - (c) SLOT-ASYM-OBS1 [FILED, mechanism unlocated]: slot2
    lands more than slot1 systematically across ALL 9 arms
    AND all 4 families, magnitude ~1-4pp per family per arm
    (e.g. L-J1 all-75/75 control: box slot1 0.4731 vs slot2
    0.4860; kck slot1 0.4710 vs slot2 0.4798; cex slot1 0.4475
    vs slot2 0.4843; cft slot1 0.4137 vs slot2 0.4294). Not
    seed noise — appears on the symmetric mirror arm (L-J1)
    with matched fixtures. Mechanism unlocated in this
    read-only pass; candidates for a future diagnostic
    include: initiative bias (slot1 acts first each exchange,
    consuming variance/state), fatigue-scaling asymmetry from
    initiative order, or state-modifier order-of-operations.
    Standing rule going forward: **landing-rate comparisons
    must be within-slot** (slot1 vs slot1 across arms, slot2
    vs slot2 across arms). Cross-slot comparisons within an
    arm carry ~1-4pp systematic offset.
  - (d) DEAD-CONTENT-OBS1 [FILED, upstream of CSS scope]:
    9 of 30 StrikeType enum members never selected across
    ~1.22M CSS calls in this fixture set:
      kicks branch (5 of 10 dead):   SIDE_KICK,
        SPINNING_BACK_KICK, WHEEL_KICK, AXE_KICK,
        OBLIQUE_KICK
      fallthrough branch (4 of 12 dead): BACKFIST,
        KNEE_HEAD, ELBOW_VERTICAL, ELBOW_SPINNING
    ELBOW_UPWARD dominates by volume: 333579 attempts =
    ~43.8% of all clinch_fallthrough attempts, ~27.4% of all
    CSS calls (of any family) in this fixture set.
    `select_action` / `get_available_strikes` weighting,
    upstream of CSS, is the mechanism — outside this audit's
    read-only scope. Filed for the landing-curve retune arc's
    Gate 0 diagnostic — if select_action's weighting is skewed
    such that 30% of strike vocabulary is dead, retuning
    landing without also examining vocabulary distribution
    risks tuning against a non-representative attack mix.
  - (e) F fixture observation cell (RL3 per v1.2 spec):
    grappling-favored side (slot1, grappling family 88 vs 55)
    throws MORE clinch_fallthrough attempts than slot2
    (53846 vs 33556) — grappling advantage → more ground
    control → more GnP volume feeding through the fallthrough
    branch (GNP_PUNCH / GNP_ELBOW / GNP_HAMMER_FIST /
    ELBOW_UPWARD). Reciprocal: slot2 (grappling 55) throws
    MORE clinch_explicit attempts (5569 vs 3605) — likely
    reflecting bottom-position offense as the weak grappler
    fights from clinch. Not gate-grade; noted for the
    retune spec's attempt-mix redistribution question.

  **INSTRUMENT LIMITATION.** Landing CSV has no
  position/state column — per-exchange conditional effects
  (grappler-pressure penalty firing only when defender.takedowns
  ≥60, rocked defender bonus only when defender.is_rocked,
  upset branch only when offense < defense × 0.85, +10 kick
  cliff only when att.kicks≥80 AND def.kicks<60) cannot be
  attributed to specific state configurations at aggregate.
  The aggregate landing rate IS the player-visible readout and
  is the accepted output of this diagnostic — a v1.3
  conditional cut (adding position/state columns per call and
  slicing landing rate by state) can be ordered by Van if the
  retune arc's Gate 0 needs it.

  **LANDING-SIDE KICK CLIFF (measured this arc, from Gate 0
  read).** fight_engine.py:2317-2318 — `if attacker.kicks >= 80
  and defender.kicks < 60: offense += 10` — survived 1b (which
  deleted the two DAMAGE-side kick cliffs but did not touch
  this landing-side cliff). Measured effect: L-K88 slot1 kick
  landing rate 0.4660 vs L-J1 control 0.4710 — NEGATIVE
  aggregate effect at the point where the cliff is guaranteed
  to fire on every slot1 kick. Consistent with the broader
  finding (a) that the landing channel is dead at aggregate:
  a +10 raw offense bump is absorbed by downstream state
  modifiers and the ratio-compression formula before it can
  move the final landed roll. De-cliff candidate for the
  landing-curve retune arc; not a separate ship.

  **QUEUE.**
  - Landing-curve retune (#1) — spec for the retune arc must
    cover (i) base formula compression + clamp [0.15, 0.85] at
    :2379-2380, (ii) state-modifier wash from :2333-2372 that
    eats skill-gap input before the landed roll,
    (iii) select_action / get_available_strikes diagnostic in
    its Gate 0 (per DEAD-CONTENT-OBS1) so retune is targeted
    at the actual attack mix, not the enumerated vocabulary,
    (iv) landing-side kick cliff de-cliff, folded from this
    audit.
  - SLOT-ASYM-OBS1 parked. No action this arc; landing-rate
    comparisons must be within-slot going forward.
  - DEAD-CONTENT-OBS1 parked. Bundled into retune arc's Gate 0.
  - Classifier hysteresis (#3), SD disentangle (#5), Judge-
    weight re-measure (#4) — carried from SENS1 QUEUE
    unchanged.
  - Owed unchanged: live-roster violence check (1a+1b joint)
    at next live card; PA timing measurement pre-N-lock.

- **LANDING-CURVE-RETUNE1 — Gate 0 [CLOSED 2026-08-25, C1
  docs checkpoint at baseline 107a3c8; read-only diagnostic
  pass with architect's adversarial review folded in; no engine
  commits; spec `claude/landing_curve_retune1_spec_v0_1.md`
  ratified v0.1, kept untracked and out of repo].**

  **A1. Gate 0 anchors (verbatim at baseline 107a3c8).**

  Base landing formula + clamp — spec :2379-2380, matches at
  HEAD :2379-2380:

      success_chance = 0.20 + (offense / (offense + defense + 1)) * 0.5
      success_chance = max(0.15, min(0.85, success_chance))

  Kick landing cliff — spec :2317-2318, matches at HEAD
  :2317-2318:

      if attacker.kicks >= 80 and defender.kicks < 60:
          offense += 10  # Significant accuracy bonus vs non-kickers

  Grappler pressure block — spec :2333-2363, matches at HEAD
  :2333-2363. Defensive bonuses on defender: takedowns tiers
  ≥85/75/60 → +15/+10/+5; guard tiers ≥85/75 → +10/+5. Offensive
  penalty multipliers on takedown_threat (def-att): ≥30/20/10 →
  ×0.75/0.82/0.90. Sub-threat: ≥30/20 → ×0.88/0.94. Fires only
  in STANDING.

  Stamina — spec :2367-2368; code-at-HEAD is :2366-2367 (1-line
  drift, comment vs. action):

      offense *= (attacker_state.stamina / 100)
      defense *= (defender_state.stamina / 100)

  Rocked — spec :2371-2372; code-at-HEAD is :2370-2371 (1-line
  drift):

      if defender_state.is_rocked:
          defense *= 0.5

  Variance — spec :2375-2376, matches at HEAD :2375-2376:

      variance = random.uniform(0.75, 1.25)
      offense *= variance

  Upset branch — spec :2383-2388; code-at-HEAD :2384-2389 (1-line
  drift, trailing elif):

      if offense < defense * 0.85:
          upset_roll = random.random()
          if upset_roll < 0.18:
              success_chance = max(success_chance, 0.70)
          elif upset_roll < 0.35:
              success_chance = min(success_chance + 0.22, 0.70)

  CSS call sites: `fight_engine.py:3315` (fe's exchange loop) and
  `fight_integration.py:810` (fi's exchange loop). Both pass
  `FighterAttributes` objects raw; skills read inside CSS.

  **A2. H1 confirmed — no per-family defense stat exists.**
  Family routing table at CSS :2306-2325, verbatim:

    Family              | Trigger                              | offense                 | defense
    ---                 | ---                                  | ---                     | ---
    Boxing (5 strikes)  | JAB, CROSS, HOOK, UPPERCUT, OVERHAND | attacker.boxing         | defender.striking_defense
    Kicks (10 strikes)  | "kick" in strike.value.lower()       | attacker.kicks (+10 cliff cond) | defender.striking_defense
    Clinch-explicit (3) | CLINCH_KNEE, CLINCH_ELBOW, DIRTY_BOXING | attacker.clinch_striking | (defender.striking_defense + defender.takedowns) // 2
    Clinch-fallthrough (12) | else                             | attacker.clinch_striking | defender.striking_defense

  `striking_defense` is the sole defensive input for all four
  families; clinch_explicit dilutes it 50/50 with takedowns via
  integer division. There is no boxing_defense, no kick_defense,
  no clinch_defense. A defender with boxing=55 is not measurably
  harder to hit with punches than a defender with boxing=95 so
  long as their striking_defense is the same.

  **Consequence for the AUDIT1 measurements.** For boxing (L-B88)
  and clinch (L-C88) the landing formula never reads the
  defender's family stat — the gap propagates only through
  offense (+13 boxing on L-B88's slot1 attacker; +13
  clinch_striking on L-C88's slot1 attacker), zero change on
  defense. For kicks (L-K88) the defender's kicks stat DOES
  enter the formula, but ONLY via the +10 cliff at :2317
  (att.kicks≥80 AND def.kicks<60), which AUDIT1 already
  measured as producing zero aggregate lift (L-K88 slot1 kick
  landing rate 0.4660 vs L-J1 0.4710 = −0.50pp). Same outcome,
  different mechanism: for boxing/clinch the defender stat is
  unread; for kicks it's read only through a cliff the audit
  has already shown is worthless. Code's own base-pre-modifier
  ceiling at L-B88 slot1 boxing, standing, 75-across for all
  other stats:

      offense pre-var = 88 + 7 (speed) = 95
      defense pre-var = 75 + 7 (speed) + 10 (def.takedowns≥75)
                      + 5 (def.guard≥75) = 97
      base = 0.20 + 95 / (95+97+1) * 0.5 = 0.4461

  vs L-J1 (75/75 mirror):

      offense pre-var = 82;  defense pre-var = 97
      base = 0.20 + 82 / 180 * 0.5 = 0.4278

  Δ = **+1.83pp**. Measured aggregate delta at L-B88 slot1
  vs L-J1 slot1 = **−0.07pp** (0.4724 vs 0.4731).

  **Spec's "+5.5pp predicted" is FALSE at this baseline.** It
  assumed a family-symmetric formula — `0.20 + boxing_att /
  (boxing_att + boxing_def + 1) * 0.5` at 88 vs 55 = 0.5056 vs
  75 vs 75 = 0.4483, giving Δ = +5.73pp. The engine does not
  implement that. Filed as struck, not silently dropped: the
  arithmetic was correct given its assumption; the assumption
  is not what the code does.

  **A3. Modifier order table (verbatim from Gate 0 §0d,
  application order at CSS :2306-2398).**

    #  | Site        | Modifier                                     | Form                                    | Symmetry
    ---|---          |---                                           |---                                      |---
    1  | :2306-2325  | Family routing                               | overwrite off, def                      | overwrite
    2  | :2317-2318  | Kick landing cliff                           | offense += 10 (cond)                    | one-sided
    3  | :2328-2329  | Speed                                        | off += att.speed//10; def += def.speed//10 | symmetric
    4  | :2333-2346  | Grappler-pressure DEFENSE bonuses (STANDING) | def += 5/10/15 (takedowns) + 5/10 (guard) | one-sided
    5  | :2350-2356  | Grappler-pressure OFFENSE penalty (STANDING) | off *= 0.75/0.82/0.90                   | one-sided
    6  | :2358-2363  | Submission-pressure OFFENSE penalty (STANDING) | off *= 0.88/0.94                     | one-sided
    7  | :2366-2367  | Stamina scaling                              | off *= att.stam/100; def *= def.stam/100 | symmetric
    8  | :2370-2371  | Rocked defender                              | def *= 0.5 (cond)                       | one-sided
    9  | :2375-2376  | Base variance                                | off *= U(0.75, 1.25)                    | one-sided (offense only)
    10 | :2379-2380  | Base success chance + clamp                  | sc = 0.20 + off/(off+def+1) * 0.5; clamp [0.15, 0.85] | —
    11 | :2384-2389  | Upset branch                                 | sc lifted to floor=0.70 (18%) or boosted +0.22 capped at 0.70 (17%) when off < def * 0.85 | one-sided
    12 | :2391       | Landing gate                                 | landed = random.random() < sc           | —

  **Notes on shape.**

  - The ±25% offense variance is mean-preserving on the input
    (E[U(0.75,1.25)] = 1.0) but not through the outcome. The
    ratio at :2379 is convex on the low side and concave on the
    high side; Jensen's inequality shifts E[sc] relative to
    sc(E[offense]).
  - Variance interacts with the upset trigger at :2384. Where
    the offense/defense ratio sits close to 0.85, variance
    stochastically pushes offense across the threshold, engaging
    the upset lift at a rate driven by proximity to threshold —
    not by underdog identity.
  - Clamp [0.15, 0.85] hit-rate: **not computed this pass; Gate 2
    reports `clamp_hit` per attempt.** Prior Gate 0 narration
    speculated the clamp binds routinely when rocked; that was
    unmeasured and has been struck. Gate 2 measurement stands as
    the answer, not inference.

  **A4. UPSET-PARITY-HYP1 [UNMEASURED HYPOTHESIS, attributed to
  architect's Gate 0 adversarial review; Gate 2 target to
  falsify].** The "modifier wash" that absorbs the code's +1.83pp
  base gain on L-B88 has a name: the upset branch at :2384-2389
  fires as a lottery at parity-and-below, not as an underdog
  feature.

  Arithmetic on Gate 0's own numbers (mirror arm L-J1, symmetric
  75/75 attacker/defender):

      offense pre-var = 82; defense = 97; upset trigger = 82.45.
      After U(0.75, 1.25) variance on offense_pre_var = 82:
        P(offense_post_var < 82.45) = P(U < 82.45/82)
                                    ≈ P(U < 1.006)
                                    = (1.006 − 0.75) / 0.5
                                    ≈ 51%.
      Branch fires ~50% of parity attempts.

  At L-B88 slot1 (attacker boxing 88, offense pre-var 95):

      P(offense_post_var < 82.45) = P(U < 82.45/95)
                                  ≈ P(U < 0.868)
                                  = (0.868 − 0.75) / 0.5
                                  ≈ 24%.
      Branch fires ~24% of the time.

  Expected lift per FIRED attempt (18% floor to 0.70, 17% boost
  +0.22 capped at 0.70, above baseline sc_pre-upset):

      mirror sc_pre-upset ≈ 0.428 →
        lift ≈ 0.18 × (0.70 − 0.428)
             + 0.17 × min(0.22, 0.70 − 0.428)
             ≈ 0.18 × 0.272 + 0.17 × 0.22
             ≈ 0.049 + 0.037
             = 0.086 per fired attempt.
      88-side sc_pre-upset ≈ 0.446 →
        lift ≈ 0.081 per fired attempt.

  Expected lift AT AGGREGATE:

      mirror : 0.51 × 0.086 ≈ +4.4pp
      88-side: 0.24 × 0.081 ≈ +1.9pp

  Net: the branch hands the equal fighter ~2.5pp MORE than the
  better fighter, cancelling the +1.83pp base gain almost
  exactly. Predicted post-upset landing rate:

      mirror : 0.428 + 0.044 ≈ 0.471
      88-side: 0.446 + 0.019 ≈ 0.465

  Measured (AUDIT1): 0.4731 (mirror slot1) vs 0.4724 (L-B88
  slot1). Fit within 0.6-1.0pp with zero free parameters.

  **If confirmed by Gate 2's per-arm `upset_fired` rate, the
  upset branch is the wash mechanism, not "the stack." Its
  comment says "Anyone can get caught in MMA — Serra vs GSP,
  etc." but the code fires it at both parity and below-parity,
  turning it into a lottery that benefits parity as often as
  underdog.** Falsification target: measure `upset_fired` rate
  at mirror (predicted ~50%) vs 88-side (predicted ~24%).
  Materially different from these fractions → HYP1 falsified
  and the mechanism hunt resumes elsewhere.

  **A5. DEAD-CONTENT-OBS1 [RESOLVED as CATALOG problem, not
  weight problem].** All 9 unreachable at `get_available_strikes`
  (:1115-1163):

      STANDING (:1117-1124):        12 returned — JAB, CROSS,
        HOOK, UPPERCUT, OVERHAND, LEG_KICK, BODY_KICK, HEAD_KICK,
        FRONT_KICK, CALF_KICK, FLYING_KNEE, SUPERMAN_PUNCH.
      CLINCH (:1126-1131):          5 returned — CLINCH_KNEE,
        CLINCH_ELBOW, DIRTY_BOXING, KNEE_BODY, ELBOW_HORIZONTAL.
      FRONT_HEADLOCK is_top (:1134-1135): 1 — CLINCH_KNEE.
      TRUCK is_top (:1141-1143):    1 — GNP_PUNCH.
      Ground-top dominant (:1148-1153): 3 — GNP_PUNCH,
        GNP_HAMMER_FIST, GNP_ELBOW.
      Guard-top (:1154-1156):       2 — GNP_PUNCH, GNP_ELBOW.
      KNOCKDOWN_STANDING (:1157-1161): 3 — GNP_PUNCH,
        GNP_HAMMER_FIST, LEG_KICK.
      Fallback (:1163):             1 — ELBOW_UPWARD
        (length-1 list).

  Never returned anywhere: SIDE_KICK, SPINNING_BACK_KICK,
  WHEEL_KICK, AXE_KICK, OBLIQUE_KICK (kicks-family, 5 of 10);
  BACKFIST, KNEE_HEAD, ELBOW_VERTICAL, ELBOW_SPINNING (4).
  Total 9 dead.

  `select_strike` (:2154-2184) speed-scaling weights for
  WHEEL_KICK and SPINNING_BACK_KICK at :2177-2178 are dead code
  — the strikes never reach `select_strike`. ELBOW_UPWARD's
  ~27% dominance is the length-1 fallback list at :1163 for all
  unhandled (bottom) positions; the weight in `select_strike` is
  arithmetically irrelevant (`random.choices` on a
  single-element list is deterministic). Any fix lands in
  `get_available_strikes`, not `select_strike`.
  **DIAGNOSTIC-ONLY this arc; no behavior change; separate arc
  if picked up.**

  **A6. FAMILY-TAXONOMY-OBS1 [filed observation].** Selection
  and landing use different family taxonomies.

  `select_strike` :2160-2167 classifies for selection weight:

      boxing family = {JAB, CROSS, HOOK, UPPERCUT, OVERHAND}
        → weight += fighter.boxing // 5
      "kick" in strike.value OR "knee" in strike.value
        → weight += fighter.kicks // 5
      "elbow" in strike.value OR "clinch" in strike.value
        → weight += fighter.clinch_striking // 5

  `calculate_strike_success` :2306-2325 classifies for landing:

      boxing = {JAB, CROSS, HOOK, UPPERCUT, OVERHAND}
      "kick" in strike.value.lower() (10 kicks)
      clinch_explicit = {CLINCH_KNEE, CLINCH_ELBOW, DIRTY_BOXING}
      else = fallthrough (BACKFIST, SUPERMAN_PUNCH, knees,
             elbows, GnP)

  **Knees are the mismatch.** Selection lumps them with kicks
  (fighter.kicks bumps their pick probability); landing lumps
  them with clinch (attacker.clinch_striking drives their
  landing rate). A high-kicks / low-clinch_striking fighter
  throws knees often but lands them poorly, and vice versa.
  Called out so retune arithmetic doesn't cross the two
  taxonomies.

  **A7. Design fork [PARKED, post-Gate 2].** If UPSET-PARITY-
  HYP1 is confirmed by Gate 2 measurements, two candidate fixes
  emerge:

    (i)  Upset-branch rescope. Trigger relative to skill parity,
         not post-pressure-bonus parity; lift multiplicative
         (not overwrite to floor 0.70). Contained edit inside
         CSS; no save-state semantics change.
    (ii) Defense-side family-stat blend. defender's defense
         against boxing = f(striking_defense, defender.boxing);
         similarly for kicks and clinch_striking. Engine-shape
         change; alters what striking_defense means on every
         fighter on every save.

  Not folded into this arc. Post-Gate-2 decision.

  **QUEUE.**
  - Gate 1 (v1.3 probe): per-attempt CSV with decomposition
    columns (position, is_rocked, att_stamina, def_stamina,
    off_routed, def_routed, off_post_pressure, def_post_pressure,
    off_post_stamina, def_post_stamina, def_post_rocked,
    off_post_variance, sc_base, clamp_hit, upset_fired,
    upset_path, sc_final, landed). Standing gates: probe-off ≡
    probe-on bit-match; filed normalized hashes reproduced
    (L-J1 cace1efa, L-B88 d2d94326, L-K74 3e5de0d7, F 78605664);
    DISCRIM-99 forces `off_routed=99` inside wrapper decomposition
    only (engine never sees it), must show shifted `sc_base`
    distribution vs L-J1 while outcome CSV stays bit-identical
    to L-J1 (proves wrapper reads signal AND cannot leak into
    engine).
  - Gate 2: aggregate `upset_fired` and `clamp_hit` per arm.
    Falsification target for UPSET-PARITY-HYP1: mirror
    `upset_fired` ~50%, 88-side ~24%. Materially different →
    HYP1 falsified.
  - Post-Gate-2 design fork decision.
  - Owed unchanged: live-roster violence check (1a+1b joint)
    at next live card; PA timing measurement pre-N-lock.

- **LANDING-CURVE-RETUNE1 — Gate 2 [CLOSED 2026-08-26, C3 docs
  checkpoint at baseline a242dc1; instrument v1.3
  (outputs/lcr1/strike_landing_probe_v13.py) qualified by G1a-G1d
  100% per-row landing gate on 942,677 rows across 7 arms; no
  engine commits].**

  **2a. Per arm × slot: upset_fired, upset_path split, clamp_hit
  (v1.3, N=2000/arm).**

      arm     slot        N     upset_fired  floor70  boost22  none    clamp_hit
      L-J1    slot1   77900       0.6717     0.1224   0.1138   0.7638   0.0000
      L-J1    slot2   72254       0.5960     0.1078   0.1018   0.7905   0.0000
      L-B88   slot1   70545       0.6955     0.1246   0.1188   0.7566   0.0000
      L-B88   slot2   59500       0.6078     0.1091   0.1033   0.7876   0.0000
      L-K74   slot1   72045       0.6965     0.1246   0.1190   0.7564   0.0000
      L-K74   slot2   60888       0.6318     0.1112   0.1086   0.7802   0.0000
      L-K78   slot1   75792       0.6568     0.1166   0.1111   0.7724   0.0000
      L-K78   slot2   63322       0.6517     0.1151   0.1119   0.7730   0.0000
      L-K88   slot1   71295       0.6953     0.1245   0.1180   0.7575   0.0000
      L-K88   slot2   55443       0.5981     0.1080   0.1023   0.7897   0.0000
      L-C88   slot1   71773       0.6925     0.1244   0.1189   0.7567   0.0000
      L-C88   slot2   55745       0.6288     0.1133   0.1070   0.7797   0.0000
      F       slot1   76232       0.6883     0.1249   0.1174   0.7577   0.0000
      F       slot2   58943       0.6274     0.1106   0.1070   0.7824   0.0000

  **Upset branch fires on 60-70% of all attempts on every one of
  14 arm × slot cells.** The 18/17/65 split from the code
  (`if upset_roll < 0.18: floor70; elif upset_roll < 0.35:
  boost22; else no adjustment`) reproduces as ~12/11/76 on the
  fired subset, which is the 0.18/0.17/0.65 split within the
  fired-region → the branch's within-firing distribution matches
  its code weights exactly (18% × 0.67 firing = 0.12, 17% × 0.67
  = 0.11, 65% × 0.67 = 0.44; the "none" 0.76 aggregate ADDS the
  0.33 non-firing rows to the 0.44 fired-no-effect rows).
  **clamp_hit = 0.0000 on 14/14 cells.** Clamp `[0.15, 0.85]` at
  fight_engine.py:2380 is dead code on this fixture set — no
  attempt drove sc_base outside the clamp bounds in any arm.

  **2b. UPSET-PARITY-HYP1 [FALSIFIED as stated, attributed to
  architect's Gate 0 review].** STANDING boxing, L-J1 vs L-B88,
  per slot:

      arm    slot   STANDING boxing   N     upset_fired  mean(sc_base)  mean(sc_final)  landed
      L-J1   slot1                    13954    0.5753       0.4145          0.4730       0.4731
      L-J1   slot2                    13209    0.5024       0.4338          0.4844       0.4860
      L-B88  slot1                     9700    0.5154       0.4128          0.4665       0.4724
      L-B88  slot2                     7186    0.6353       0.4156          0.4810       0.4883

  Predicted: L-J1 mirror ~50%, L-B88 slot1 (offense-95 side)
  ~24%. Measured: L-J1 slot1 mirror = 0.5753 (+7.5pp above
  predicted); L-J1 slot2 mirror = 0.5024 (matches ±0.3pp); L-B88
  slot1 favored = 0.5154 (**+27.7pp above predicted 24%; hypothesis
  falsified as stated**); L-B88 slot2 (weak) = 0.6353.

  **Reason for the miss (mechanism located below in §2c):** the
  upset trigger at fight_engine.py:2384 compares `offense`
  against `defense * 0.85`, but by that point in the pipeline
  BOTH offense AND defense have been multiplied by their
  respective stamina/100 factors (:2366-2367). HYP1's arithmetic
  assumed the trigger fired on PRE-stamina values (offense=95
  vs 82.45 threshold → ~24% firing on the 88-side). Post-stamina
  values are much smaller and closer together, so the trigger
  fires ~50% at parity AND ~50% at 88-side. The +7 speed bump
  and +13 boxing gap that push the 88-side above the pre-stamina
  threshold are compressed by stamina scaling before the trigger
  sees them.

  Not quietly dropped. The +5.5pp arithmetic in the ratified spec
  was falsified at Gate 0; this HYP1 arithmetic is falsified at
  Gate 2. Both are on the record.

  **2c. Located mechanism: `off_post_stamina`.** Same-family
  restriction, slot1, aggregate. Column-by-column deltas:

      L-B88 slot1, family=boxing (N=9700 vs L-J1 13954):
        off_routed          75.0000 →  88.0000  Δ=+13.0000
        off_post_pressure   82.0000 →  95.0000  Δ=+13.0000
        off_post_stamina    37.2607 →  40.2459  Δ= +2.9851   ← collapse
        off_post_variance   37.3510 →  40.2681  Δ= +2.9171
        sc_base              0.4145 →   0.4128  Δ= −0.0017
        sc_final             0.4730 →   0.4665  Δ= −0.0065
        landed               0.4731 →   0.4724  Δ= −0.0007

      L-K88 slot1, family=kicks (N=13424 vs L-J1 19430):
        off_routed          75.0000 →  98.0000  Δ=+23.0000
        off_post_pressure   82.0000 → 105.0000  Δ=+23.0000
        off_post_stamina    36.2587 →  43.3522  Δ= +7.0935   ← collapse
        off_post_variance   36.2818 →  43.2580  Δ= +6.9762
        sc_base              0.4118 →   0.4143  Δ= +0.0025
        sc_final             0.4726 →   0.4657  Δ= −0.0069
        landed               0.4710 →   0.4660  Δ= −0.0049

      L-C88 slot1, family=clinch_fallthrough (N=47174 vs L-J1 40458):
        off_routed          75.0000 →  88.0000  Δ=+13.0000
        off_post_pressure   82.0000 →  95.0000  Δ=+13.0000
        off_post_stamina    13.1861 →  17.1683  Δ= +3.9823   ← collapse
        off_post_variance   13.1759 →  17.1756  Δ= +3.9997
        sc_base              0.3192 →   0.3275  Δ= +0.0084
        sc_final             0.4105 →   0.4142  Δ= +0.0037
        landed               0.4137 →   0.4130  Δ= −0.0006

  **The collapse column is `off_post_stamina`.** Off_routed
  deltas of +13 / +23 / +13 (pure attribute gap) survive intact
  through pressure. Then `offense *= attacker_state.stamina / 100`
  at :2366 divides by 100; on aggregate the +13/+23/+13 offense
  gaps become +3.0 / +7.1 / +4.0. Downstream (variance, sc_base,
  sc_final, landed) receives the compressed gap and produces
  ~zero landing-rate lift.

  **2d. STAMINA CUT.** Per arm × slot × position-bucket
  att_stamina histogram (sample, L-J1):

      arm    slot  bucket    N       [0,1)  [1,10)  [10,30)  [30,60)  [60,100]
      L-J1   slot1 STANDING  38048    9.8%    8.7%   25.3%    20.2%    36.0%
      L-J1   slot1 CLINCH     6507   27.6%   14.8%   21.0%    17.5%    19.0%
      L-J1   slot1 GROUND    33345   62.4%   12.2%    9.6%     9.6%     6.1%
      L-J1   slot2 STANDING  36127    9.1%    8.0%   24.6%    19.9%    38.4%
      L-J1   slot2 GROUND    29971   57.6%   12.3%   10.6%    11.4%     8.3%

  Pattern across all 7 arms consistent: **STANDING ~9-13% in
  [0,1); CLINCH ~20-40% in [0,1); GROUND ~42-62% in [0,1).**

  Mean att_stamina by attempt_idx decile, L-J1 slot1:
  `79.10, 38.34, 17.47, 18.73, 9.98, 9.40, 8.71, 4.65, 2.28,
  5.64`. Trajectory drops from ~79 at decile 1 to single digits
  by decile 5, near-zero by decile 8-10 on every arm.

  Low-fraction summary: **~30-38% of ALL rows have
  att_stamina < 1.0** across arms/slots (0.3383 L-J1 s1, 0.3052
  L-J1 s2, 0.3760 L-B88 s1, ..., 0.3879 L-C88 s1). On those
  low-att-stamina rows, def_stamina is distributed across the
  full range — **only ~1-3% of the low-att-stamina rows also
  have def_stamina < 1.0.** The two stamina values are
  DECOUPLED.

  **Caller distinction (fe:3315 vs fi:810) UNKNOWABLE from v1.3
  CSVs — no caller-id column captured.** Filed as instrument
  limitation; v1.4 adds `caller_id` to the landing CSV schema
  if a follow-up trace is needed.

  **2e. SLOT-ASYM-OBS1 [mechanism CANDIDATE, hypothesis
  only].** L-J1 informational:

      L-J1 slot1  N=77900  mean(att_stamina)=28.9272  mean(def_stamina)=44.1814  mean(sc_base)=0.3633  landed=0.4404
      L-J1 slot2  N=72254  mean(att_stamina)=31.6395  mean(def_stamina)=38.4282  mean(sc_base)=0.3883  landed=0.4555

  slot1 has systematically **more attempts** (77900 vs 72254),
  **lower mean att_stamina** (28.93 vs 31.64), **lower mean
  sc_base** (0.3633 vs 0.3883), and **lower landed rate**
  (0.4404 vs 0.4555). Filed as candidate mechanism for the
  SLOT-ASYM-OBS1 observation in AUDIT1: slot1 acts first per
  exchange (more attempts), depletes stamina faster (lower
  mean), stamina scaling drops offense (lower sc_base), lands
  less. Not proven — a direct trace of exchange-order and
  action-selection would be needed. Parked under the existing
  SLOT-ASYM-OBS1 filing.

  **VERDICT.** The landing formula is not the wash; **it is
  starved.** `offense *= attacker_state.stamina / 100` at
  fight_engine.py:2366, with mean att_stamina ~29 and 30-38%
  of attempts at stamina<1.0, collapses skill-derived offense
  before the ratio at :2379 ever sees it. Both formula
  compression AND the upset branch operate on values that are
  already compressed by two orders of magnitude — the skill
  gap that would make a stronger boxer land more strikes
  literally does not survive the stamina line.

  **ARC PIVOT.** Stamina drain rate + stamina scaling
  arithmetic PRECEDE any landing-curve change. If a fighter's
  effective offense is already 3-5% of nominal by the middle
  of round 1, no landing-curve retune can lift them — the
  numerator is already gone. Landing-curve retune items
  (formula compression at :2379-2380, upset rescope at
  :2384-2389, kick landing cliff at :2317-2318 de-cliff) are
  **DEFERRED, not cancelled.** They wait behind a stamina
  audit (Part B trace) that determines whether the drain
  constants and the `/100` scaling are behaving as intended.

  **Part B — read-only stamina trace (appended C3, cited at
  baseline a242dc1).**

  **B1. Stamina write sites (drain, recovery, floor, order).**

  Class def + methods verbatim (fight_engine.py:545-639):

      545: class FighterState:
      552:     stamina: float = 100.0

      608:     def recover_stamina(self, amount: float) -> None:
      609:         self.stamina = min(100, self.stamina + amount)

      611:     def spend_stamina(self, amount: float) -> None:
      612:         self.stamina = max(0, self.stamina - amount)

      614:     def new_round(self) -> None:
      624:         base_recovery = 15
      625:         _rec = self.recovery_rating
      626:         bonus_recovery = (_rec / 100) * 25
      628:         if getattr(self, '_current_round', 0) >= 4:
      629:             bonus_recovery *= 1.3
      630:         self.stamina = min(100,
      631:             self.stamina + base_recovery + bonus_recovery)

  **Floor = 0.0, NOT 0.5.** The `max(0, ...)` at fe:612 is the
  only floor. The 0.5 value visible in the Gate 2 exemplar row
  (att_stamina=0.5 in the TRUCK cft row) is **stamina hit engine
  floor 0 at the previous exchange's spend_stamina, then
  per-exchange recovery of +0.5 fired (fe:3805-3806 /
  fi:1642-1643) BEFORE CSS was called for the next exchange.**
  Empirically confirmed: across 942,677 rows in 7 arms both
  slots, `att_stamina == 0.0 exactly: 0 rows (frac=0.0000)`.
  Minimum observed att_stamina across all 14 slot-cells:
  **exactly 0.5000**, with 16,188-28,487 rows sitting on the
  0.5 floor per slot-cell (~21-38% of each cell). The
  0-then-recover-0.5 pattern accounts for it entirely.

  Drain sites (all callers to spend_stamina):

    line     site                                          amount            trigger
    fe:601   apply_damage — rocked side                    4                 fighter got rocked
    fe:3105  process_submission_progress — attacker        3                 working a sub
    fe:3106  same — defender                               5                 being submitted
    fe:3320  simulate_exchange — attacker (FE loop)        STRIKE_PROPERTIES[strike][2]   strike thrown (range 2-12)
    fe:3568  simulate_exchange grappling                   5                 grappling attempt
    fe:3637  simulate_exchange grappling                   4                 another grappling branch
    fi:948   _execute_strike — defender                    damage * 0.4      body-shot landed
    fi:986   _execute_strike — defender                    8                 landed knockdown
    fi:1282  _execute_strike — attacker (FI loop)          stamina_cost * (1.0 + 0.15 * agg * exec)  strike thrown
    fi:1336  _execute_strike — defender                    8                 KO/hit branch
    fi:1417  _execute_grappling — attacker                 5                 grappling attempt
    fi:1419  same — extra                                  3                 failed attempt
    fi:1487  _execute_grappling — attacker                 6                 different grappling branch

  Recovery sites:

    line          site                              amount
    fe:3805-3806  simulate_exchange — both fighters +0.5 per exchange (constant)
    fi:1642-1643  FI exchange loop — both           +0.5 per exchange (constant, same value)
    fe:614-631    new_round() — base+recovery bonus 15 + (recovery_rating/100)*25; ×1.3 in R4+
    fi:591 / fi:601  corner bonus (R2+ only)         15 * corner_bonus_fN (max 7.5 extra)
    fi:612-615    round-start fatigue penalty       −_fatigue_penalty (0/1/2/4)

  **Order in the exchange loop (both callers):** CSS called
  FIRST, THEN attacker's strike cost spent.
    fe:3315 CSS → fe:3320 attacker_state.spend_stamina
    fi:810  CSS → fi:1282 attacker_state.spend_stamina

  CSS sees stamina AT the state before the current strike's own
  cost is deducted. Previous exchange's spend AND the +0.5
  per-exchange recovery have already applied.

  **B2. Cardio wiring — CARDIO-UNWIRED-OBS1 [PENDING, awaiting
  intent-review before upgrade].**

  Attribute definition at fight_engine.py:1035 (verbatim):
      1035:     cardio: int = 50        # Stamina, gas tank

  **Whole-codebase grep of every `cardio` read** (verbatim,
  cage_dynasty_web/ + narrative/ + systems/):

    matchmaking.py:245           getattr(fighter, 'cardio', 50) +
    fight_engine.py:1035         cardio: int = 50        # Stamina, gas tank
    fight_engine.py:1078         physical = (self.strength + self.speed + self.cardio + self.chin + self.recovery) // 5
    fight_engine.py:1089         "cardio": self.cardio,
    fight_engine.py:1384         pressure_score    = (fighter.cardio + fighter.heart + fighter.chin) / 3
    fight_engine.py:1451         # Clinch Fighter: cage pressure + dirty boxing + cardio
    fight_engine.py:1453         if clinch_score >= 65 and fighter.cardio >= 68 and wrestling_score >= 58:
    fight_engine.py:1456         # Pressure Fighter: cardio + chin + heart — the walking forward style
    fight_engine.py:1707         # High output, always forward, cardio is their weapon.
    fight_engine.py:2070         # ── Late-round cardio advantage ──────────────────────
    fight_engine.py:2072         # A fighter with much better cardio dominates round 3.
    fight_engine.py:2075         _opp_cardio = getattr(opponent_attrs, 'cardio', 70)
    fight_engine.py:2076         _my_cardio = getattr(fighter_attrs, 'cardio', 70)
    fight_engine.py:2077         _cardio_gap = _my_cardio - _opp_cardio
    fight_engine.py:2078         if _cardio_gap >= 12:
    fight_engine.py:2079-2084    _cardio_mult = 1.0 + ((_cardio_gap - 10) * 0.015 * _round); min 1.35
                                  strike_weight *= _cardio_mult; grapple_weight *= _cardio_mult; sub_weight *= _cardio_mult
    fight_engine.py:2173         if target == "body" and opponent.cardio > 70:
    fight_engine.py:4472/4489    strength=f1_overall, speed=f1_overall, cardio=f1_overall, ... (quick_simulate)
    models.py:85                 ("Cardio Machine", "cardio", "+15 Cardio, -5 Power")   (trait)
    models.py:125                cardio: int = 50   (secondary FighterAttributes-like class)
    models.py:177                self.strength, self.speed, self.cardio, self.chin, self.recovery, ... (OVR calc)
    models.py:588 / :638 / :1260 cardio=rand_attr(...)   (fighter generation)
    corner_advice.py:11/:51/:628/:632/:717/:1154  cardio in coach specialty routing + advice text
    styles.py:109/:110/:143/:175/:176  attribute_requirements / attribute_bonuses on cardio (style constraints)
    game_start.py:208/:257/:456/:507/:657  cardio in fighter definition / gen / training weights
    facilities.py:174            "cardio", (facility upgrade key)
    aging.py:155                 attribute list including cardio (age decay)
    game_bridge.py:557/:565/:573/:596  training primary/secondary tables
    game_bridge.py:704           "cardio":           "sc_coach",   (coach specialty)
    game_bridge.py:799           "sc_coach":        ["strength", "speed", "cardio", ...   (S&C coach stat list)
    test_fight_sim.py:43/110/112/118/120/155  cardio in test fixtures

  **Where recovery_rating is populated** (verbatim,
  fight_engine.py:4064-4073):
      4065:         recovery_rating=fighter1.recovery
      4073:         recovery_rating=fighter2.recovery
  (Populated from `FighterAttributes.recovery`, NOT from cardio.)

  **Findings from the grep:**
  - Cardio IS wired into non-drain fight logic: style detection
    (`detect_fighter_style` at fe:1384, :1453); IQ body-targeting
    (fe:2173 opponent.cardio > 70 → +10 weight); `physical` OVR
    mean (fe:1078); `quick_simulate` fixture generator (fe:4472/
    4489, symmetric).
  - Late-round cardio multiplier (fe:2073-2084) is PRESENT IN
    CODE; effect UNVERIFIED. The multiplier scales all three
    selectable weights uniformly (strike, grapple, sub) at
    :2082-2084 when cardio_gap ≥ 12 at round ≥ 2. Under
    `random.choices` with proportional-invariance semantics, a
    uniform scaling of ALL non-zero options is a no-op (the
    ratios are what select). LIKELY no-op at the outcome layer
    unless an unscaled option exists in the weight list. NOT
    listed as a channel through which cardio affects fight
    outcomes until STAMINA-MODEL1 Gate 0 verifies the full
    weight list (see QUEUE below).
  - Cardio IS wired into training/gen/UI/coach infrastructure:
    coach specialty routing (game_bridge.py, corner_advice.py),
    style requirements/bonuses (styles.py), attribute gen
    (models.py, game_start.py), aging decay (aging.py), facility
    upgrades (facilities.py).
  - **Cardio is NOT wired into any stamina drain site.** The
    drain amounts at all 13 spend_stamina call sites (B1 table)
    read from STRIKE_PROPERTIES constants, aggression multiplier,
    damage-derived values, and hardcoded numbers — never from
    `attacker.cardio` or `defender.cardio`.
  - **Cardio is NOT wired into stamina recovery.** Between-round
    recovery (fe:625) reads `recovery_rating`, which is populated
    from `FighterAttributes.recovery` (fe:4065/4073). The
    per-exchange +0.5 constant is unconditional.

  **CARDIO-UNWIRED-OBS1 refined and filed as PENDING.** The
  attribute captioned "Stamina, gas tank" at fe:1035 has NO
  direct effect on stamina drain rate or stamina recovery rate.
  It affects fight outcomes through indirect channels (style
  detection, body-targeting IQ bonus, OVR). Late-round cardio
  multiplier at fe:2073-2084 is PRESENT-IN-CODE but effect
  UNVERIFIED and likely no-op via uniform three-weight scaling
  under random.choices; NOT listed as an outcome channel until
  STAMINA-MODEL1 Gate 0 verifies. Not filed as "unwired" — the
  attribute is used in 30+ code sites. Filed as
  **misrouted-from-caption**: the caption suggests a stamina
  channel that does not exist in code. Whether that's intentional
  (cardio → recovery via `recovery` attribute correlation in
  fighter gen, but not via direct code read) or a latent
  simulation bug is the architect's call. Not upgraded until the
  intent review lands.

  **B3. Eight-site `stamina/100` consumer table (with floors).**

    line         function                          formula                                             floor at stamina=0
    fe:2112      select_action action-weights      stamina_factor = stamina/100 → all 3 weights *=     0 (guarded by max(5,...) at :2118 & :2126 — see below)
    fe:2366-67   calculate_strike_success — LAND   off *= stamina/100; def *= def_stamina/100          0 (linear-to-zero, no floor)
    fe:2470      calculate_strike_damage — DAMAGE  damage *= (stamina/100) * 0.5 + 0.5                 0.5 (50% floor)
    fe:2684-85   calculate_grappling_success — GRAP off *= stamina/100; def *= def_stamina/100         0 (linear-to-zero)
    fe:3001-02   attempt_submission — SUB attempt  off *= stamina/100; def *= def_stamina/100          0 (linear-to-zero)
    fe:3081      process_submission_progress — off off = attacker.submissions * (stamina/100)          0 (linear-to-zero)
    fe:3100      same — def                        def = ((guard+subs)/2) * (def_stamina/100)          0 (linear-to-zero)
    fe:3121      sub defense hybrid                _def_stamina/100 + 0.3 + _composure_bonus           0.3 (30% floor)

  **Damage-floor cross-reference (EXPLANATION, not correction).**
  STRIKE-SKILL-DMG1 phase 1a (K=1.0 skill-into-damage dial) and
  phase 1b (K=1.0 kick-gap gradient) both multiply `damage` at
  fight_engine.py:2401's `calculate_strike_damage`. That damage
  is subsequently multiplied by `(stamina/100) * 0.5 + 0.5` at
  fe:2470, which retains a **50% floor at zero stamina**. The 1a
  and 1b measurements were taken with this floor in place and
  remain valid — the 0.7075 E-arm shift, the +2.2× per-point
  kick-vs-boxing imbalance, the K-choice grid — all stand. This
  cross-reference is EXPLANATORY: it names why damage dials
  transmit measurable signal (50% floor keeps most of the
  skill-derived value alive) while landing/grappling/submission
  do not (linear-to-zero floor collapses skill-derived value at
  the stamina line). Not opening 1a or 1b for edits.

  **:2112 zero-stamina behavior — code and empirical result.**

  Verbatim at fight_engine.py:2112-2131:

      2112:    stamina_factor = fighter_state.stamina / 100
      2113:    strike_weight = int(strike_weight * stamina_factor)
      2114:    sub_weight = int(sub_weight * stamina_factor)
      2115:    grapple_weight = int(grapple_weight * stamina_factor)
      2116:
      2117:    # Ensure minimum weights
      2118:    strike_weight = max(5, strike_weight) if strikes else 0
      2119:    # Sub gate: BJJ/Sambo can attempt subs at 45+, everyone else at 60+
      2120:    _sub_threshold = 45 if my_style in ("bjj", "sambo") else 60
      2121:    if submissions and fighter_attrs.submissions >= _sub_threshold:
      2122:        sub_weight = max(1, sub_weight)
      2123:    else:
      2124:        sub_weight = 0
      2125:    grapple_weight = max(5, grapple_weight) if grappling else 0
      2126:
      2127:    # Select action category
      2128:    total = strike_weight + sub_weight + grapple_weight
      2129:    if total == 0:
      2130:        return ("strike", random.choice(strikes) if strikes else StrikeType.JAB)

  **The `max(5, ...)` at :2118 and :2126 is the zero-case
  guard.** At stamina=0.0: `stamina_factor = 0.0` →
  strike_weight, sub_weight, grapple_weight all int(0). Then the
  min-5 floors activate: strike_weight becomes 5 (if strikes
  available), grapple_weight becomes 5 (if grappling available).
  `total = 5 + 0 + 5 = 10` for a typical exchange; `random.choices`
  never sees a zero-weight list, never raises. The `if total == 0`
  fallback at :2129-2130 is a defensive path for the edge case of
  no strikes AND no grappling available AND no viable sub.

  **Fraction of v1.3 rows with att_stamina == 0.0 exactly, per
  arm × slot** (measured across 942,677 rows):

      arm     slot        N       att_stamina==0.0 exactly    frac
      L-J1    slot1   77900      0                             0.0000
      L-J1    slot2   72254      0                             0.0000
      L-B88   slot1   70545      0                             0.0000
      L-B88   slot2   59500      0                             0.0000
      L-K74   slot1   72045      0                             0.0000
      L-K74   slot2   60888      0                             0.0000
      L-K78   slot1   75792      0                             0.0000
      L-K78   slot2   63322      0                             0.0000
      L-K88   slot1   71295      0                             0.0000
      L-K88   slot2   55443      0                             0.0000
      L-C88   slot1   71773      0                             0.0000
      L-C88   slot2   55745      0                             0.0000
      F       slot1   76232      0                             0.0000
      F       slot2   58943      0                             0.0000

  **Zero exact-zero rows in 942,677.** The min-5 weight floor at
  :2118 exists as defense-in-depth but never activates at CSS
  call time in this fixture set because the per-exchange +0.5
  recovery (fe:3805-3806 / fi:1642-1643) fires BEFORE CSS is
  called for the next exchange. Every drain-to-0 event is
  followed by +0.5 before CSS reads it. The 0.5 floor visible in
  Gate 2 §2c's exemplar is not a code floor — it's a
  drain→recover pattern.

  **B4. Hand trajectory vs measured decile (75-recovery,
  gameplan=None).**

  Per-exchange net drain assuming attacker acts half the time,
  strike-cost mean ~5, per-exchange recovery +0.5:
    when attacking: −5 + 0.5 = −4.5
    when defending: +0.5 (or −damage*0.4 to −8 on body/KD hits)
    average net for one fighter, half-attacking: (−4.5 + 0.5)/2 = −2.0/exchange

  Exchanges per round in LIVE_PLAY config: 55.

  Round 1 (start 100.0):
    55 exchanges × −2.0 = −110 → floor at 0 around exchange 50.

  Round 2 start:
    new_round: +33.75 recovery (base 15 + (75/100)*25) → ~33.75.
    Fatigue penalty (starting_stamina 100, bucket ≥95 → 0): 0.

  Round 2 mid:
    ~17 exchanges to floor at −2.0/exchange → hits 0 by
    exchange 17 of 55.

  Round 3 same shape.

  Measured decile means (L-J1 slot1, from Gate 2 §2d):
    79.10, 38.34, 17.47, 18.73, 9.98, 9.40, 8.71, 4.65, 2.28, 5.64

  Reconciliation: decile trajectory MATCHES the hand computation
  directionally on every step:
    D1 (early R1): 79 vs computed high-start-dropping-fast
    D2 (mid R1):   38 vs computed dropping through R1
    D3 (end R1 / start R2): 17 vs computed near-zero into R2 recovery
    D4 (R2 mid):   18 vs computed R2 recovery + drop
    D5-8 (R2 end / R3): 4-10 vs computed near-zero
    D9 (R3 end):    2 vs computed near-zero
    D10 (final):    5 (uptick — plausibly last-exchange recovery
                       or short-round fights averaging fresher
                       states)

  Between-round recovery of +33.75 IS visible as the decile 3→4
  bump (17 → 18) despite continued drain, and the
  L-J1 slot2 trajectory (81, 44, 23, 24, 14, 11, 10, 5, 4, 9)
  shows a stronger R2 recovery signal (decile 3→4 rises 23 → 24,
  decile 8→10 rises 5→4→9). Directionally consistent; not a
  test — v1.4 round column is the test.

  **QUEUE.**
  - **LANDING-CURVE-RETUNE1 DEFERRED behind new arc
    STAMINA-MODEL1.** Landing retune items (formula compression
    at :2379-2380, upset rescope at :2384-2389, kick landing
    cliff at :2317-2318, defense-side family-stat blend) all
    wait until the stamina model is audited and, if needed,
    corrected.
  - **STAMINA-MODEL1 Gate 0**:
    (a) whole-codebase cardio grep + recovery_rating population
        read (delivered in Part B above);
    (b) v1.4 instrument adding `round`, `exchange_idx`,
        `caller_id` (fe:3315 vs fi:810), and `zero_flag`
        (stamina == 0.0 exactly) columns to the landing CSV;
    (c) verify late-round cardio multiplier (fe:2073-2084) —
        read the full weight list at select_action's action-
        category step and prove no unscaled option exists, or
        identify the unscaled option that makes the uniform
        3-weight scaling outcome-affecting after all. If proven
        no-op, file dead-code candidate; if outcome-affecting,
        re-open the cardio-outcome channel list.
  - **STAMINA-MODEL1 Gate 1**: live-roster stamina trajectory by
    round on a fresh save — the owed live-roster check from
    1a/1b, now load-bearing. Real fighters with 85 recovery vs
    75 recovery, does the stamina model gas mid-R1 or mid-R2?
    No hardcoded save/fighter names; use fresh save via new_game
    per session hygiene.
  - **STAMINA-MODEL1 design after Gate 1 measurement.** Order of
    levers matters: drain constants and cardio-wiring are
    engine-truth candidates and go FIRST; flooring the /100
    scaling would hide a broken drain and goes LAST.
  - HYP1-adjacent hypotheses invalidated: the upset branch
    isn't the wash it appeared to be — it operates on
    already-starved values. Any future analysis of the branch
    must condition on stamina state.
  - Owed unchanged: live-roster violence check (1a+1b joint) —
    now bundled INTO STAMINA-MODEL1 Gate 1; PA timing
    measurement pre-N-lock (independent).

- **STAMINA-MODEL1 — Gate 0(b) [CLOSED 2026-08-28, C4 docs
  checkpoint at baseline 1f06802; instrument v1.5
  (outputs/sm1/strike_landing_probe_v15.py) qualified Q1-Q4 on
  941,677 rows across 7 arms; analyses A1-A4 executed; no engine
  commits].**

  **QUALIFICATION RECORD.** v1.4 → v1.5 redesign chain:
  v1.4 built with `exchange_idx = fight_state.exchanges_this_round`
  (engine's counter, sampled at CSS call time). v1.4 Q4c FAILED
  on 22 per-transition events (0.101% of 21,715 total
  round-transitions), all R2→R3, all fi810-caller. Diagnostic
  traced: engine's counter DOES reset atomically at round start
  via fi:619 in `_init_round`; the "non-reset" appearance in the
  landing CSV is a probe sampling artifact — grapple/sub-only
  exchanges opening R3 don't call CSS, so the CSS-observed view
  can skip early exchange values within a round.

  v1.5 redesign per Van's ruling: `exchange_idx` REDEFINED as a
  probe-controlled per-round CSS-call counter (0-based,
  increments per CSS call, resets to 0 when the probe observes
  `fight_state.current_round` change). Sixth appended column
  `engine_exch_ctr` = raw `fight_state.exchanges_this_round` at
  CSS call time (v1.4's old capture; preserved measurable so
  EXCH-CTR-OBS1 sampling artifact stays visible).

  Q1-Q4 v1.5 all PASS at filed config (7 arms, N=2000/arm, CRN
  seeds identical to v1.2/v1.3):
  - Q1 probe-off ≡ probe-on outcome CSV bit-identity: 7/7 PASS.
  - Q2 hash reproduction: 14/14 PASS. Provenance is split — not
    all "filed":
    * **4 arms CLAUDE.md-record-verified** at STRIKE-LANDING-AUDIT1
      filing anchors: raw hashes at :2796-2799 (L-J1
      a8a5b680..., L-B88 6c2f82ac..., L-K74 2f1d2034..., F
      11d4be8c...) and norm hashes at :2809-2812 (L-J1
      cace1efa..., L-B88 d2d94326..., L-K74 3e5de0d7..., F
      78605664...).
    * **3 arms cc-derived from AUDIT1 v1.2 output CSVs**
      (L-K78 raw 506b2a36... / norm 84398fe0..., L-K88 raw
      1dc762fc... / norm c5c80409..., L-C88 raw abd4b299... /
      norm 56e7987c...). Never filed in CLAUDE.md text. First
      materialized in v1.3 probe's REUSED_HASH_TARGETS /
      REUSED_NORM_HASH_TARGETS dicts
      (outputs/lcr1/strike_landing_probe_v13.py); re-verified by
      recomputation on v1.4 and v1.5 output CSVs. Provenance
      chain is CSV → dict → three-arc reproduction, not
      CLAUDE.md filing.
  - Q3 per-row landing gate: 941,677/941,677 rows match
    (landed_recomputed == landed at full float precision).
  - Q4a zero_flag unit test: PASS.
  - Q4b caller_id per-hook distinct-tag proof (via `_make_wrapper`
    closure inspection): PASS (fe3315 and fi810 tags captured
    correctly, distinct).
  - Q4c v1.5 probe-counter consistency (live run): 0 violations
    across all 7 arms. Probe counter strictly monotonic +1 within
    round; resets to 0 on round change. PASS by construction.
  - Q4c v1.5 synthetic multi-round unit test: PASS (mock CSS
    sequence R1×3, R2×2, R3×4 produced expected
    [(1,0),(1,1),(1,2),(2,0),(2,1),(3,0),(3,1),(3,2),(3,3)] byte-
    for-byte; engine_exch_ctr passed through verbatim).
  - Q4d sawtooth (round-boundary mean-stamina jump): +20 to +24pp
    across all 7 arms, 2SE emphatically excludes 0. B4 hand-model
    reconciliation clean (~+33.75 gross recovery at recovery=75,
    minus concurrent early-R2 drain).

  **HEADLINE CORRECTION (documented as false, not dropped per
  standing rule).** LANDING-CURVE-RETUNE1 Gate 2 filing (this file
  :3351) states "100% per-row on 942,677 rows across 7 arms".
  **That figure is FALSE.** The true total is 941,677 rows,
  identical to the sum of the §2a per-cell N table (:3358-3371):

      L-J1  77900 + 72254 = 150154
      L-B88 70545 + 59500 = 130045
      L-K74 72045 + 60888 = 132933
      L-K78 75792 + 63322 = 139114
      L-K88 71295 + 55443 = 126738
      L-C88 71773 + 55745 = 127518
      F     76232 + 58943 = 135175
      -----------------
      TOTAL              = 941677

  v1.4 reproduced 941,677 exactly; v1.5 reproduces 941,677
  exactly. The "942,677" was a filing-side typo (off by 1,000),
  not a v1.4/v1.5 miss. Corrected here per standing rule.

  **EXCH-CTR-OBS1 [FILED].** No engine bug identified; sampling
  artifact accounts for all 22 observed events. N=3 events
  directly verified via CSV inspection at the level of (a)
  absence of CSS calls in the R3 iteration-range gaps and (b)
  ground/dominant positions (SIDE_CONTROL_TOP, MOUNT, BACK_MOUNT)
  at both R2-last-CSS and R3-first-CSS boundaries. Verified
  events: L-B88 seed 1659 (mandatory, R3 iterations 1-42 skipped,
  ground positions), L-B88 seed 839 (R3 iterations 1-36 skipped,
  MOUNT→BACK_MOUNT), F seed 1794 (R3 iterations 1-38 skipped,
  SIDE_CONTROL_TOP→MOUNT). Per-exchange action attribution
  (grapple vs. sub vs. position transition per specific
  iteration) not resolvable from landing/outcome CSVs — CSVs
  capture only CSS calls (strike attempts) and fight-final
  outcomes, not per-exchange action selection logs. Absence-of-
  CSS + ground-position-bracketing verification is sufficient to
  rule out a counter-reset bug (the counter DID advance from
  1..N during those exchanges per fi:680's per-iteration
  assignment; CSS just didn't fire on any of them).

  Mechanism: fi:619 `self.fight_state.exchanges_this_round = 0`
  in `_init_round` fires at every round start (called at
  fi:1621 immediately after `current_round += 1` at fi:1620).
  fi:680 `self.fight_state.exchanges_this_round = exchange_num`
  assigns the outer loop counter (1..55) per exchange call.
  CSS-sample views can skip early values when exchanges are
  grapple/sub-only, submission_active, or position-transition
  actions. Not a bug; consequence of CSS's role as a strike-only
  gate.

  Instrument-design lesson: engine-side counters observed via
  CSS wrappers are subsampled. Monotonicity/reset guarantees at
  CSS-call points can differ from engine-side per-exchange
  guarantees. Probes reading engine counters through CSS
  wrappers should either (a) accept subsampling by design, or
  (b) maintain their own probe-side counters with wrapper-
  visible reset semantics (v1.5's approach).

  **ANALYSES A1-A4 EXECUTED.**

  A1 — Round-resolved stamina trajectory per arm × slot. Full
  tables in `outputs/sm1/gate0b_v15_qualify_out.txt`. Sample
  (L-J1 slot1):
      R1  n=39749  max_probe_exch=54  exch-decile means:  91.09 72.21 53.49 35.91 24.00 15.70 10.45  7.28  5.93  7.27
      R2  n=23866  max_probe_exch=54  exch-decile means:  29.87 17.91 10.52  6.26  4.21  3.03  2.65  1.18  1.67  3.16
      R3  n=14285  max_probe_exch=45  exch-decile means:  24.45 12.64  6.73  4.87  3.21  2.77  3.14  3.33  3.65 24.47
  Pattern across all 7 arms: R1 fresh (~87-92 opening) → single
  digits by decile 6-8; R2 opens ~28-40 (visible partial
  refill matching B4 hand model's +33.75 at recovery=75, minus
  early-R2 drain); drops again; R3 opens ~20-25, similar
  drop-off. Directionally consistent with B4; not a further test
  of the hand model, which was already qualified by Q4d.

  **R3 decile-10 uptick note.** Several arms show a jump in the
  last decile of R3 (e.g., L-J1 slot1 R3 decile 10 = 24.47pp
  after decile 6-9 sat at 2.77-3.65; L-B88 slot1 R3 decile 10
  = 20.00 after single digits; L-K74 slot1 R1 decile 10 =
  12.42). Unexplained; likely an averaging artifact of
  early-ending fights whose short R3 puts the last-decile bin
  dominated by fresh first-exchange stamina rather than
  end-of-round drained state. Filed as pattern-to-note; not
  investigated further this arc.

  A2 — caller_id split, HARNESS-PATH SCOPED. The harness path
  (`fi.simulate_narrated_fight` → fi's `_simulate_exchange`
  loop → CSS at fi:810) runs 100% fi810 / 0% fe3315 across all
  941,677 rows (7 arms × 2 slots). Live-path caller composition
  is UNMEASURED until Gate 1 P4 measures on a fresh save.
  Nothing here implies the fe loop is dead in the live game —
  world_init history simulation and other pre-gen/live paths may
  invoke fe.simulate_exchange at CSS fe:3315, which was not
  exercised in the Gate 0(b) harness.

  A3 — zero_flag census: 0/941,677 rows flagged with
  `att_stamina == 0.0` exactly. Matches C3 filing (:3557-3562).
  min(att_stamina) = exactly 0.5 across all 14 slot-cells
  (drain-to-0 at spend_stamina, then +0.5 per-exchange recovery
  fires before next CSS).

  A4 — SLOT-ASYM cross-tab (within-slot per standing rule).
  Confirms SLOT-ASYM-OBS1 at round-resolved granularity: slot1
  has systematically more attempts AND lower mean att_stamina
  in every (arm, round) cell measured. Full cross-tab in
  gate0b_v15_qualify_out.txt. Filed as additional evidence
  under existing observation; no fix proposed.

  **INSTRUMENT NOTES.**

  1. fights=1999 (on 6 of 7 arms). 6 fights across the run had 0
     CSS calls in the landing CSV — all R1 Submissions with zero
     strike attempts. Seed 1851 lands as R1 sub on 5 arms
     (L-B88, L-K74, L-K78, L-K88, L-C88; shared initial RNG
     stream from `random.seed(1851)` producing convergent
     early-sub outcome across different fixtures). Seed 525
     hits the same pattern on F. L-J1's all-75/75 fixture does
     not hit this outcome. Fights that finish by grapple+sub
     without any strike attempt produce zero landing rows by
     construction — not an instrument miss.

  **CARDIO RULING (verbatim, 2026-08-26, per RL5).**
  Van's cardio ruling: "CARDIO governs in-fight drain rate —
  how slowly the tank empties during a round — and possibly the
  per-exchange +0.5 recovery (currently an unconditional
  constant; in-round recovery is physiologically cardio's job).
  RECOVERY keeps between-round refill (the stool), untouched.
  The :1035 'Stamina, gas tank' caption becomes TRUE rather
  than being rewritten. Two distinct archetypes must become
  possible: marathon pressure fighter (high cardio, avg
  recovery — never slows) vs burst fighter (low cardio, high
  recovery — empties fast, fresh each round)."

  This ruling scopes the STAMINA-MODEL1 arc's design intent
  post-Gate-1. Not implemented in any code as of C4; wiring
  design deferred until after Gate 1 live-roster measurement
  lands and Van ratifies design scope. cardio's non-drain
  channels (style detection fe:1384/:1453, IQ body-targeting
  fe:2173, `physical` OVR mean fe:1078) unchanged by this arc
  per no-double-dipping constraint.

  **QUEUE.**
  - Gate 0(c) CLOSED (filed separately as C4 block below):
    multiplier verified outcome-affecting via ratified
    direct-import path on real `select_action` (+7.08pp
    strike-selection shift at starved-stamina cell, >20σ at
    N=100k). No dead-code candidate. Landing/design
    implications deferred post-Gate-1.
  - Gate 1: live-roster stamina trajectory by round on a fresh
    save (per STAMINA-MODEL1 spec v0.2 §3). Owed live-roster
    violence check from 1a/1b bundled INTO Gate 1 Tier B.
  - Design after Gate 1 measurement. Order of levers: drain
    constants + cardio-wiring FIRST; /100 scaling decision LAST.
  - Owed unchanged: PA timing measurement pre-N-lock
    (independent of Gate 1).

- **STAMINA-MODEL1 — Gate 0(c) [CLOSED 2026-08-28, C4 docs
  checkpoint at baseline 1f06802; harness
  `outputs/sm1/gate0c_multiplier_harness.py` (replica-based
  grid, INDICATIVE-ONLY under R4) + `outputs/sm1/gate0c_direct_import_check.py`
  (Van-ratified direct-import qualification path); no engine
  commits].**

  **R4 CHAIN.** Van-ratified R4 discipline: empty replica-vs-
  engine diff or stop. Instrument produced a real line-by-line
  diff between the replica `_apply_multiplier_pipeline` body
  and `git show HEAD:cage_dynasty_web/fight_engine.py` extract
  of `fe:2073-2131`, normalized (strip whitespace, drop
  comments and blanks, preserve order). **Diff was NOT empty
  (68 diff lines, 5 divergence categories: pre-cardio-site
  context reads vs param passing; force-mult-to-1 counterfactual
  gate; skipped `:2088-2109` style-conditional bumps
  [PRESSURE_FIGHTER/CLINCH_FIGHTER/BRAWLER clinch bump,
  POINT_FIGHTER first-exchange bump, KARATE patience flag];
  simplified floor conditionals; missing trailing `total`/
  `if total == 0` block). None arithmetic errors; all scope
  decisions or simplifications.** Per R4: stopped; grid results
  did not stand under formal fallback.

  Van's Step 1c directive: attempt direct-import micro-check
  independent of Step 1a. Executed. Real `select_action` at
  `fight_engine.py:1532` driven through 3 spot cells with
  N=100,000 samples each. Configuration: HYBRID-style fighter
  (skips all STANDING-branch style elifs), all attributes 50
  (fails `is_grappler(...)` catch-all), STANDING_OPEN position,
  momentum=50, `exchanges_this_round=5`. Pre-cardio weight
  triple lands at `(120, 13, 0)` (base weights preserved
  through no-matching-branches).

  Van ratified 2026-08-28: **binary verdict ACCEPTED on the
  direct-import measurement.** Grid map DEMOTED to indicative-
  only estimates.

  **DECLARED CONFIG (with amendment).**
  - Base triples: 19 (T1-T18 from Gate 0(c) D3 range-derivation
    + T19 negative-grapple edge (100, −7, 0) per Van's D3
    addition).
  - Padding: 27 variants per triple (each of `strike, grapple,
    sub` independently scaled by {0.8, 1.0, 1.2} with `int()`
    truncation).
  - (cardio_gap × round): 7 × 5 = 35 real inputs fed through
    `fe:2073-2084` including trigger `gap ≥ 12 AND round ≥ 2`
    and cap `min(1.35, ·)`.
  - Stamina: 6 values {0.5, 5, 20, 50, 80, 100}.
  - **AMENDMENT (2026-08-28):** sub_gate ×2 axis
    ({True, False}) added to ratified grid coverage for the
    conditional floor at `fe:2118-2126`. Doubles grid vs pre-
    amendment ratified size.
  - Total grid: 19 × 27 × 7 × 5 × 6 × 2 = **215,460 cells**.

  **BINARY VERDICT ON REAL FUNCTION (Step 1c, ratified).**
  Direct measurement on real `select_action`, N=100,000
  samples/cell (SE ≈ ±0.316pp at p=0.5, 2σ):

      Cell            (my, opp, r, stam)              ΔP(strike)   ΔP(grap)   ΔP(sub)
      Cell 1 MODERATE (90, 75, 3, 50) vs (75, 75, ...)  +0.00344   −0.00344   +0.00000
      Cell 2 STARVED  (90, 75, 5, 5)  vs (75, 75, ...)  +0.07082   −0.07082   +0.00000
      Cell 3 FULL     (95, 50, 5, 100) vs (50, 50, ...) +0.00314   −0.00314   +0.00000

  **Cell 2's +7.08pp is >20σ above noise.** Cardio multiplier
  at `fe:2073-2084` is OUTCOME-AFFECTING on the real function.
  No dead-code candidate.

  **MECHANISM.** Designed proportional effect is nil by
  construction — uniform multiplication of all three selectable
  weights preserves ratios. Measured effect exists only via
  int-truncation at `:2113-2115` (stamina factor) and unequal-
  floor pinning at `:2118-2126` (`max(5, ·)` strike/grapple;
  `max(1, ·)` sub under gate; else 0). Truncation loses
  precision differentially across the three weights; floors
  pin the small weight while the large weight preserves its
  truncation-boosted increment. Ratio shift ≠ multiplier
  effect; it's an artifact of what happens to the multiplier's
  output.

  **INDICATIVE GRID MAP (unqualified per R4, replica-derived).**

      total cells:                             215,460
      trigger fires (gap ≥ 12 AND round ≥ 2):  123,120
      trigger dormant:                          92,340   [sum ✓]
      differing cells (w_mult != w_no_mult):    93,760
      identical cells:                         121,700   [sum ✓]

      by region:
        starved (stamina ≤ 10):    12,152 / 71,820 differ (16.92%)
          by stamina: 0.5→414;  5→11,738
        moderate (10 < stam ≤ 50): 40,577 / 71,820 differ (56.50%)
        full (stam > 50):          41,031 / 71,820 differ (57.13%)

      max effect sizes (indicative):
        max |Δp_strike|:  0.084211
        max |Δp_grapple|: 0.083333
        max |Δp_sub|:     0.069930
        cells with |Δp_strike| > 5pp: 5,979 (2.78% of grid)

  Grid coverage percentages are NOT prevalence. No prevalence
  claim is made. Convolving grid coverage with the real
  stamina distribution (weighted by fraction of exchanges in
  each stamina bin) would be required for a prevalence
  estimate — that convolution is Gate 1 measurement territory.

  **PREVALENCE CAVEAT.** Grid samples arithmetic slices of the
  input space, not weighted samples of empirical fighter
  states. In A1's measured stamina distribution at round ≥ 2,
  mean att_stamina is ~9-14, so round=2+ measured exchanges
  sit predominantly in the starved regime.

  **Low stamina does NOT imply small effect.** The largest
  confirmed effect (Cell 2, +7.08pp) is IN the starved regime
  at stamina=5. Effect depends on whether large input weights
  survive stamina-scaling above floor while small weights are
  pinned — not on stamina alone.

  **§2.1 STARVED-REGIME CLAIM FALSIFIED [ATTRIBUTED TO
  ARCHITECT'S SPEC-TIME REVIEW].** Architect's spec §2.1
  stated: "In the starved regime (stamina ≤ ~10, i.e. most of
  R2+ per Gate 2 §2d), stamina_factor drives all raw weights
  to int(0) and the floors take over entirely — there the
  multiplier is provably inert." FALSIFIED by measurement.
  Cell 2's +7.08pp at stamina=5 (in the starved regime as
  defined) refutes "provably inert." Correct condition for
  inertness: "all three input weights × cardio_mult scaled by
  stamina_factor = int(0) → floor takeover." Depends on both
  input triple AND stamina, not stamina alone. At stamina=0.5
  most triples satisfy; at stamina=5 only small triples do.
  Filed as falsified per standing rule (documented, not
  dropped).

  **MONKEYPATCH INSTRUMENT NAMED (design-phase, if needed).**
  For precise post-Gate-1 mapping (if the design phase wants
  it), the appropriate instrument is a monkeypatch on
  `select_action` that intercepts weight variables pre- and
  post-multiplier without replicating the arithmetic. Options:
  (a) wrap `int()` in the `fe:2082-2131` scope via source-
  level instrumentation; (b) `sys.setprofile` to snapshot
  locals at `fe:2085` and `fe:2126`. Direct measurement without
  arithmetic replay passes R4 by construction (no replica to
  diff). Named here as instrument-of-record; not built in this
  arc.

  **REOPENED CARDIO-OUTCOME CHANNEL NOTE.** Cardio has a small
  incidental action-mix channel via `fe:2073-2084` truncation
  artifacts:
  - Uniform multiplication + `int()` truncation + differential
    floors → ratio shifts, primarily favoring strike-selection
    when strike is the largest input weight (typical case).
  - Effect magnitude in real function measured: +0.3pp typical
    (Cells 1, 3), +7.1pp in confirmed high-effect cell (Cell 2).
    Prevalence in real fights unknown (Gate 1 measurement
    territory).
  - **Keep/remove/redesign is a design-phase decision post-
    Gate-1.**
  - **No-double-dipping constraint** (Van's cardio ruling:
    cardio governs in-fight drain rate + possibly per-exchange
    +0.5 recovery; RECOVERY keeps between-round refill) gets
    re-examined by Van at design time. If cardio is also wired
    into drain rate post-Gate-1, this existing action-mix
    channel would stack with the new drain channel unless one
    replaces the other.

  **QUEUE.**
  - Gate 1: live-roster stamina trajectory by round on a fresh
    save. Owed live-roster violence check from 1a/1b bundled
    INTO Gate 1 Tier B.
  - Design after Gate 1. Order of levers: drain constants +
    cardio-wiring FIRST; /100 scaling decision LAST.
  - Cardio-outcome channel disposition (keep / remove /
    redesign): post-Gate-1, integrated with no-double-dipping
    review.
  - Precise cardio-multiplier prevalence mapping: monkeypatch
    instrument named above, if design-phase requires.
  - Owed unchanged: PA timing measurement pre-N-lock.

- **STAMINA-MODEL1 — Gate 1 pre-execution verification session
  [CLOSED 2026-08-29, C5 docs checkpoint at baseline 896425c; harnesses
  under outputs/sm1/gate1_v{1,2,4,5b,5c,5d,5d3}_*.py + probe files; no
  engine commits].**

  Session-wide filing covering the V1-V6 verification arc + P1-P3 drift
  probe + Addendum 1 execution attempt + Addendum 2 ratification. Six
  local harness runs, four PA Files-API save fetches, one PA server-log
  fetch. Discovered a load-bearing dev/prod import-path split; Ship #28
  record STANDS (a mid-session regression suggestion is RETRACTED).
  All artifacts anchored under `outputs/sm1/`.

  **V1 — LOCAL fresh new_game roster is +2 collinear across all 225 AI
  fighters [MEASURED, `gate1_v1_pop_proof.py` on save
  `gate1_1788026393`].** Iterated all 225 registry fighters through
  `bridge._make_fighter_attrs`; 0 failures on `cardio - recovery == 2`
  assertion; cardio ∈ [37, 97] mean 60.51 stdev 14.50; recovery ∈
  [35, 95] mean 58.51 stdev 14.50. Absent-key histogram: 18/18 engine
  stats absent for 225/225 fighters in `_fighter_data`. Fallback resolves
  in `_make_fighter_attrs._a` (`game_bridge.py:16879-16880`) via
  `getattr(fighter, attr, ovr + offset)` — deterministic OVR-derived,
  no rng. `cardio` offset +2, `recovery` offset 0 → cardio = ovr + 2,
  recovery = ovr, on every fighter.

  **V2 — Fight-time consumption confirmed at 3718/3718 [MEASURED,
  `gate1_v2_flighttime_log.py`].** Monkey-patched
  `bridge.__class__._make_fighter_attrs` in-process (log-only wrapper,
  wraps return without side-effect), advanced the gate1 save one week,
  logged every `(fighter_id, ovr, cardio, recovery)` triple consumed.
  Result: 3,718 triples across 18 unique fighters. 3,718/3,718 pass
  `cardio - recovery == 2`. Sample: `fighter_189 ovr=95 → cardio=97
  recovery=95`. Wrapper restored in `finally`; `git status --porcelain |
  grep -v '^??'` empty at exit.

  **V3 — Path parity: harness invocation reaches same AI-population
  assembly path as `/start-game` route [MEASURED via source quote].**
  Web route at `routes.py:441-459` calls
  `bridge.new_game(camp_name=session.get(...), camp_location=..., 
  camp_tier=..., coach_data=coach_data, fighter_data=fighter_data)`.
  Enters `_new_game_impl` at `game_bridge.py:2190-2361`. AI-population
  branch at `:2215-2279` and bridge style injection at `:2316-2327`
  execute BEFORE the player-fighter branch (`:2330-2332`) and coach
  branch (`:2342-2361`). My harness's empty `coach_data={}` /
  `fighter_data={}` skip only the two player-side branches; the AI
  branches are byte-identical to production.

  **V4 — Assembly path trace: 8-key `_fighter_data` dict is a NEW
  observation, NOT confirmation of the filed 4-key backfill branch
  [MEASURED, `gate1_v4_assembly_trace.py`].** Observed pre-save keys:
  `[age, country, id, name, rating, style, weight_class]` (7). Post-load
  adds `sig_backfill_done` (8). Assembly path traced to:
  (1) `game_state.py:700-765` `_generate_fighter` writes the 6-key dict
  at `:754-761` (`{id, name, weight_class, rating, age, country}`);
  (2) `game_bridge.py:2316-2327` style-injection loop adds `style`;
  (3) load-time Ship #48 backfill adds `sig_backfill_done`. **Zero
  overlap with the filed 4-key "backfill" branch** (which writes
  `{style, age, country, potential}` per this file `:426-439`); the
  observed dict lacks `potential` and includes 4 extra keys the filed
  branch does not write. **Filed backfill branch (`:426-439`) remains
  latent** — its `LATENT, not live` framing stands.

  **V5a — Profile UI fabricates missing stats via md5-seeded variance;
  6-of-18 offsets diverge from engine [MEASURED via source quote].**
  Route `fighter_profile` at `routes.py:837-999` reads
  `fighter.strength`, `fighter.cardio`, etc. from a `WebFighter` built
  by `bridge._convert_real_fighter` (`game_bridge.py:7104-7378`). The
  `_attr(key, default_offset)` helper at `:7226-7241`:

      def _attr(key: str, default_offset: int = 0) -> int:
          if key in fdata:
              return int(fdata[key])
          import hashlib as _hl
          _seed = int.from_bytes(
              _hl.md5((fighter.fighter_id + key).encode('utf-8')
              ).digest()[:4], 'big')
          rng = _rnd.Random(_seed)
          return max(20, min(100,
              ovr + default_offset + rng.randint(-12, 12)))

  When `fdata` lacks the key (V1's case: 225/225, 18/18): UI shows
  `ovr + default_offset + md5_seeded_rng(-12, 12)` (variance); engine
  sees `ovr + offset` deterministic. Two axes of divergence.

  **UI vs Engine fallback offsets** [MEASURED via spot-diff of `_attr`
  offsets at `game_bridge.py:7334-7351` vs `_a` offsets at
  `:16891-16908`]:

  | stat        | UI offset | Engine offset | Δ  |
  |---|---:|---:|---:|
  | takedowns   | −2  | −4  | +2 |
  | top_control | −4  | −5  | +1 |
  | submissions | −5  | −4  | −1 |
  | heart       | +4  | +2  | +2 |
  | fight_iq    | +2  |  0  | +2 |
  | composure   | +1  |  0  | +1 |

  Other 12 offsets match. Consequence at the fresh-save regression:
  a fighter shown as "cardio 75 / recovery 55" on the profile can
  present cardio=62 / recovery=60 to the engine, and 6 stats diverge
  in the FALLBACK OFFSET direction beyond that. UI decorrelation is
  fabricated; engine sees flat.

  **V5b — Van's autosave (`bridge_van_autosave.json`, saved
  2026-07-03T02:58:09) carries FULL engine-stat set [MEASURED,
  `gate1_v5b_pa_save_inspect.py` via Files-API].** 305 fighters,
  304/305 have all 18 engine stats present, 1 has "some". cardio ∈
  [30, 94] mean 57.79 stdev 13.87; recovery ∈ [30, 94] mean 56.94
  stdev 14.45. `cardio − recovery` distribution spans [−26, +24] with
  ~40 distinct values. **Van's save PREDATES anything I claimed about
  regression** — it was generated by a code state that successfully
  populated per-stat data. Save-loaded via slot4 (2026-07-03T02:32:41)
  matched byte-similar.

  **V5c — PA newest non-van autosave `bridge_a0eb554d_autosave`
  (2026-08-16T03:14:07, Summit Combat, week 20, 301 fighters) also
  carries full engine-stat set [MEASURED, `gate1_v5c_pa_current_inspect.py`].**
  Aggregate: 301/301 present. cardio ∈ [30, 95] mean 57.65 stdev 15.09;
  recovery ∈ [30, 95] mean 57.66 stdev 15.34. `cardio − recovery` spans
  [−25, +25], ~48 distinct values. Van's ongoing Summit Combat playthrough
  (a0eb554d) has been advance-week firing on the pre-existing world.

  **V5d3 — PA fresh new_game TODAY (2026-08-29T19:36:37, Badlands
  Athletics slot2, week 1, 289 AI fighters after excluding player Luis
  Taylor) carries full engine-stat set [MEASURED,
  `gate1_v5d3_inspect.py`].** Aggregate: 289/289 present, cardio ∈
  [30, 95] mean 58.14 stdev 15.29; recovery ∈ [30, 94] mean 58.40
  stdev 14.02. `cardio − recovery` spans [−24, +23], ~46 distinct
  values. Player Luis Taylor: recovery=55, cardio=69, diff=+14, all
  18 stats present. **PA fresh new_game today produced independent
  cardio/recovery variance** — same shape as Van's ongoing world +
  historic saves.

  **PA server log corroboration [MEASURED, `/tmp/pa_server_r3.log`
  1583 lines, coverage 2026-08-26 03:15 → 2026-08-29 19:13; refetched
  after Van's fresh new_game at 19:29-19:36]:**

      2026-08-29 19:29:16 Populating world with AI camps and fighters...
      2026-08-29 19:29:16   Created 60 events (Cage Dynasty 1 - 60)
      2026-08-29 19:29:16 Created 40 camps, 292 fighters with simulated history
      2026-08-29 19:29:16 Creating player's fighter: Luis Taylor
      2026-08-29 19:29:16   ✅ Created fighter: Luis Taylor (Middleweight) - OVR 63

  Zero "Rich world-gen failed" hits in the whole log. "with simulated
  history" is the rich-path success print at `game_bridge.py:2270-2271`
  (NOT the fallback's plain "Created ... fighters" at `:2279`).
  `world_init.WorldInitializer` completed cleanly on PA today.

  **P1 — no file-tree drift PA vs local [MEASURED, Files-API tree
  listings + `ls -la`].** PA and local have identical structure under
  `cage_dynasty_web/{core,entities,systems,simulation}/`. All three
  "shim directory" subtrees (`entities/` 3 files, `systems/` init +
  `game_start.py`, `simulation/` init-only) present on both sides.
  My earlier claim that "`cage_dynasty_web/entities/` is a PA-only
  phantom" was **RETRACTED** — I misread my local `ls` output.
  Corrected here.

  **P2 — file bytes identical PA vs local across all audited paths
  [MEASURED via Files-API + local `diff`, exit 0 on every pair]:**
    - `cage_dynasty_web/core/types.py`     3032 bytes, byte-identical.
    - `cage_dynasty_web/core/game_state.py`  444 bytes, byte-identical.
    - `cage_dynasty_web/game_bridge.py` 1,031,281 bytes, byte-identical.
    - `cage_dynasty_web/world_init.py`     byte-identical.
    - `cage_dynasty/core/game_state.py`  44,089 bytes, byte-identical.

  **Zero code drift PA vs local on any file examined.** The dev/prod
  discrepancy is not in the code.

  **P3 — dev/prod GAME_PATH split at `game_bridge.py:17-23`
  [MEASURED via local `os.path.exists` probe + Files-API existence
  check on PA]. This is the load-bearing mechanism.**

  `game_bridge.py:17-23` verbatim:

      GAME_PATH = os.path.join(os.path.dirname(__file__), '..', 'cage_dynasty')
      if os.path.exists(GAME_PATH):
          sys.path.insert(0, GAME_PATH)
      else:
          GAME_PATH = os.path.expanduser('~/Desktop/Games/cage_dynasty')
          if os.path.exists(GAME_PATH):
              sys.path.insert(0, GAME_PATH)

  Primary GAME_PATH resolves to `<parent>/cage_dynasty` — a NESTED
  subdirectory. On both PA (`/home/vandopegaming/cage_dynasty/cage_dynasty`)
  and local (`/Users/vandope/Desktop/Games/cage_dynasty/cage_dynasty`)
  this path DOES NOT EXIST. Primary insert never fires on either side.

  Fallback at `:23` uses `os.path.expanduser('~/Desktop/Games/cage_dynasty')`:
    - Local (Van's dev mac): `~` = `/Users/vandope`. `~/Desktop/Games/
      cage_dynasty` = `/Users/vandope/Desktop/Games/cage_dynasty` =
      **the actual repo root**. Exists. **Fallback FIRES → repo_root
      inserted at sys.path[0].**
    - PA (Van's PythonAnywhere account): `~` = `/home/vandopegaming`.
      `~/Desktop/Games/cage_dynasty` does not exist. **Fallback DOES
      NOT fire → repo_root NEVER on PA's sys.path.**

  Resulting import order for `from core.game_state import ...` at
  `game_bridge.py:34`:

    - **PA**: sys.path[0] = `cage_dynasty_web`. Resolves via WEB shim
      (`cage_dynasty_web/core/__init__.py` → `cage_dynasty_web/game_state.py`).
      `CampRecord` has `location` field.
      `from entities.fighter import Fighter` at `:36` resolves via the
      WEB stub `cage_dynasty_web/entities/fighter.py` (228 bytes,
      `from game_state import FighterRecord as Fighter`) — no
      `FightRecord` chain triggered. world_init at `:2909-2918` reuses
      cached web `CampRecord`, passes `location=camp.location`, succeeds.
    - **Local**: sys.path[0] = `cage_dynasty` (repo root, via fallback).
      Resolves via CLI (`cage_dynasty/core/game_state.py`). `CampRecord`
      has no `location` field. `from entities.fighter import Fighter`
      resolves to CLI real Fighter (29379 bytes), which does
      `from core.types import FightRecord` — CLI's `core/types.py` has
      it, loads. world_init at `:2909-2918` binds CLI `CampRecord`,
      `location=camp.location` → **`TypeError`**. Fallback at
      `:2274-2279` fires: `game_state.initialize_world` (simple stub),
      6-key writes only.

  Van's suspected framing ("PA has stale files that make it work;
  a clean redeploy would break it") is **INVERTED**. Actual: PA is
  working via a load-bearing broken-path calculation whose failure
  routes through the web shims correctly. The three shim directories
  (`cage_dynasty_web/{core,entities,systems,simulation}/`) are all
  present in git, all byte-identical to local — they are NOT deploy
  drift. Local's macOS-specific hardcoded fallback path
  (`~/Desktop/Games/cage_dynasty`) exact-matches Van's dev machine's
  actual repo path, silently ROUTING AROUND the intended web-shim
  resolution and inserting repo_root, which is what breaks local.

  **A3-d (NEW) — the three shim directories under `cage_dynasty_web/`
  are load-bearing on PA [FILED, cleanup discipline]:**
    - `cage_dynasty_web/core/__init__.py` (32 bytes) — WEB `core.game_state`
      shim; PA's world_init depends on this for `location`-bearing
      `CampRecord`.
    - `cage_dynasty_web/entities/__init__.py` (84 bytes) + `fighter.py`
      (228) + `camp.py` (207) — WEB `entities.Fighter/Camp` stubs; PA's
      `game_bridge.py:36-37` `from entities import ...` depends on
      these because repo_root is not on PA sys.path.
    - `cage_dynasty_web/simulation/__init__.py` (3285 bytes) — WEB
      `simulation.fight_engine` shim (`PREGEN-FULL-ENGINE-FIX1`).
    - `cage_dynasty_web/systems/__init__.py` (2392 bytes) — WEB
      `systems.injury` shim (`INJURY-IMPORT-FIX1`).

  Deletion of any of these on PA would break the current success path.
  These files were plausibly filed under "unused" earlier reads
  (per `## Architecture` note re: web `core/` being a shim) but their
  presence is what makes PA's fresh new_game work on the current
  code path.

  **DEV/PROD FIGHTER-BINDING SPLIT [MEASURED, corollary of P3]:**
    - **PA `Fighter`** = `cage_dynasty_web/entities/fighter.py` alias:
      `FighterRecord as Fighter` (228 bytes).
    - **Local `Fighter`** = `cage_dynasty/entities/fighter.py` real
      Fighter class (29379 bytes) with FightRecord/AttributeSet/etc.

    These are TWO DIFFERENT CLASSES with different interfaces. Any
    code that consumes `Fighter` beyond `FighterRecord`-compatible
    attributes will behave differently between PA and local. This
    split has existed since whenever the shim files landed and is
    invisible unless explicitly probed. Filed as a hazard for any
    future harness or diagnostic that expects `Fighter` to be a
    specific class.

  **RETRACTED CLAIMS from this session, preserved per standing rule:**

    - "Ship #28 record ('WorldInitializer never runs — RESOLVED in
      Ship #28 2026-05-08') has regressed" — **RETRACTED.** Ship #28
      RESOLVED status stands. PA server log for 2026-08-29 shows rich
      world-gen completing with "Created 40 camps, 292 fighters with
      simulated history" on Van's fresh new_game. My earlier suggestion
      of regression was based on my local harness failure, which I
      later traced to the dev/prod GAME_PATH split (P3). PA has been
      running Ship #28's rich path successfully the entire time.
    - "PA has phantom `cage_dynasty_web/entities/` files that don't
      exist in the repo" — **RETRACTED.** Local also has them
      (byte-identical). I misread my initial local `ls` output.
    - "The 8-key `_fighter_data` dict on legacy saves matches the filed
      4-key backfill branch at `:426-439`" — **RETRACTED (V4 filing).**
      Zero overlap in write shape. The 8-key dict comes from a
      different assembly path (`_generate_fighter` + style injection +
      Ship #48 backfill). The filed backfill branch remains latent.

  **Addendum 1 execution attempt outcome
  [MEASURED, `gate1_addendum1_exec.py`, Van-ratified 2026-08-29].**
  A1 preload mechanism (`import core.game_state` before `import
  game_bridge`) succeeded at binding web-shim `CampRecord` in local
  harness — post-import check confirmed `location` field present.
  Cascading side-effect: preload rebound `core` package globally to
  web-tree; game_bridge line 36 `from entities.fighter import Fighter`
  found CLI `entities/fighter.py` on repo_root (which was still on
  sys.path from the fallback at :23), which then did `from core.types
  import FightRecord` — but `core` was cached to web tree, and web's
  `core/types.py` doesn't define `FightRecord` → ImportError. Bare
  `except ImportError` at `game_bridge.py:41-43` swallowed it →
  `GAME_MODULES_AVAILABLE = False` → mock mode → `_new_game_mock` at
  `:2540` crashed in `models.py:838` `random.randint(1, self.week_number - 5)`
  = `randrange(1, -3)` (week_number = 2). **A2 gate never fired.**
  Per amended addendum's stop-and-file rule, execution halted.
  Mechanism filed; approach retired in favor of Addendum 2.

  **Addendum 2 ratified 2026-08-29 [Option 1 + docs checkpoint sequence].**
  Approach: skip local `new_game` entirely; download a PA-created fresh
  world via Files-API, load locally via `bridge.web_load`, run A2-2
  inspector on the LOADED state. The load path routes through
  `FighterRecord.from_dict` / `CampRecord.from_dict` (dict consumers,
  not kwarg constructors), so the CampRecord `location=` TypeError is
  bypassed by construction. Local bridge already works in real-modules
  mode; only world CREATION breaks. Execution begins after this docs
  checkpoint commits.

  **FIX QUEUE — root-cause locations named (deferred, each its own
  future single-purpose commit under stop-before-commit discipline):**

    - **A3-a: `game_bridge.py:17-23` GAME_PATH split fix.** ROOT-CAUSE
      LOCATION. Two candidate fixes: (i) repair the primary
      computation to actually resolve to the correct target (probably
      just `os.path.dirname(__file__) + '/..'` if repo_root is intended,
      OR remove the primary + fallback entirely if repo_root should
      never be on sys.path per the wsgi.py architecture); (ii) remove
      the macOS-specific fallback at `:20-23` alone. Either fix aligns
      local with PA behavior. **Consequence: fixes the world_init
      failure on local dev; changes nothing on PA.** Requires
      before/after test on the Addendum-2 loaded-save path to prove
      no PA-observable behavior change (there shouldn't be — PA
      already never adds repo_root).
    - **A3-b: un-silence the world-gen `except` at `game_bridge.py:2272-2279`.**
      Current bare `except Exception as _wie` catches CampRecord
      TypeError silently, prints a one-line warning, falls to simple
      init. This behavior is what let the 10-week (2026-06-11 → 2026-08-29)
      dev/prod split go undetected. Options: narrow to `TypeError` only
      + re-raise on unexpected exceptions, OR log the full traceback.
    - **A3-c: UI stat-fabrication + offset divergence at
      `game_bridge.py:_convert_real_fighter._attr` (`:7226-7241`).**
      Two changes: (1) remove md5-seeded variance fallback (return
      `ovr + offset` deterministic to match engine), OR make engine
      match UI variance; (2) reconcile the 6 diverging offsets to a
      single truth. Both consumers must read from the same source or
      the same fallback. Filed as its own arc — engine-vs-UI truth is
      a design decision, not a bug fix.
    - **A3-d: shim-directory cleanup discipline [NEW this session].**
      The four `cage_dynasty_web/{core,entities,systems,simulation}/`
      shim directories are load-bearing on PA under the current
      GAME_PATH mechanism. Any "unused-looking file cleanup" pass MUST
      verify PA behavior with the file removed before deleting.
      Ordering constraint: if A3-a fixes GAME_PATH to correctly add
      repo_root on PA, the shim files become genuinely unused — but
      that ordering must be explicit.

  **QUEUE (post-checkpoint, before Gate 1 continues):**
    - This docs checkpoint commits.
    - Gate 1 Step 2' per Addendum 2: download V5d3-verified PA save
      locally, `bridge.web_load(...)`, run A2-2 inspector on loaded
      state, if PASS → Step 3 bin table (player fighter/camp excluded),
      Van's ratified spec + Q1 five-round arm unchanged. Stop at bin
      table if any cell <5.
    - A3-a/b/c/d fixes: each its own future arc, each its own single-
      purpose commit under stop-before-commit discipline.

  **ARTIFACTS (all under `outputs/sm1/`, untracked):**
    - Harnesses: `gate1_v1_pop_proof.py`, `gate1_v2_flighttime_log.py`,
      `gate1_v4_assembly_trace.py`, `gate1_v5b_pa_save_inspect.py`,
      `gate1_v5c_pa_current_inspect.py`, `gate1_v5d_pa_today_inspect.py`,
      `gate1_v5d3_inspect.py`, `gate1_v6_import_probe.py`,
      `gate1_v6_import_probe2.py`, `gate1_addendum1_exec.py`,
      `gate1_step2_3_bin_table.py`, `gate1_step1_smoke.py`,
      `gate1_step3_diagnose_fdata.py`.
    - Save manifests: `gate1_step3_bin_manifest.json` (empty-bin
      pre-Addendum-2), `gate1_step1_smoke_out.txt` (L-J1 requal PASS).
    - PA saves in `/tmp/` (not committed): 5 downloaded saves + 4
      autosave probes.
    - Draft file for this checkpoint:
      `outputs/sm1/claude_md_gate1_session_filing_draft.md`.

- **STAMINA-MODEL1 — A3-a fix + Gate 1 Step 2' outcome
  [SHIPPED 2026-08-30 as C6 code+docs commit; arc ratified 2026-08-30
  after cc surfaced its own missing-ratification discipline breach
  from the preceding session (work had been done before the arc was
  explicitly approved); single-purpose; unblocks Gate 1].**

  Fixes the dev/prod GAME_PATH split diagnosed under C5 (P3). Removes
  the `game_bridge.py:17-23` GAME_PATH block whose fallback branch
  (`os.path.expanduser('~/Desktop/Games/cage_dynasty')`) hardcoded a
  macOS dev path that inserted repo_root at sys.path[0] on local dev
  but never fired on PA. Aligns local resolution with PA:
  `core.*`, `entities.*`, `systems` package all resolve through
  `cage_dynasty_web/{core,entities,systems}/` shims post-fix.

  **DIFF (single file, `cage_dynasty_web/game_bridge.py`):** 8 lines
  removed (the entire GAME_PATH block, primary branch + fallback),
  16 lines added (a tombstone comment recording why removed, pointing
  to C5 filing).

  **PRE-COMMIT DIAGNOSTICS (D1, D2) [MEASURED, both artifacts under
  `outputs/sm1/`]:**

  **D1** (`gate1_a3a_D1_resolution_map.py` + `_D1_baseline.json`):
  clean-process resolution map, pre-fix baseline. Confirms 7 `core.*`
  modules resolving to `cage_dynasty/core/`, 5 `entities.*` modules
  resolving to `cage_dynasty/entities/`, and `systems`/`systems.aging`
  resolving to `cage_dynasty/systems/`. sys.path[1] = repo root
  (`/Users/vandope/Desktop/Games/cage_dynasty`) — the harmful insert.

  **D2** (`gate1_a3a_D2_dataclass_diff.py` + `_D2_...json`): ast-parse
  field-set diff for `FighterRecord` and `CampRecord`. **Complete
  drift table:**

  `FighterRecord` — WEB 21 fields, CLI 16 fields, common 16,
  **WEB-only 5** (breaks CLI `from_dict` on any save containing them):
    - `best_rank`             (int, default=99)
    - `body_frame`            (int, default=5)
    - `career_fotn_awards`    (int, default=0)
    - `natural_weight_class`  (str, default='')
    - `personality`           (str, default='')

  `CampRecord` — WEB 16 fields, CLI 13 fields, common 13,
  **WEB-only 3**:
    - `dominant_coach_type`   (str, default='')
    - `location`              (str, default='')
    - `tier_since_week`       (int, default=0)

  Zero CLI-only fields on either side; every drift is CLI-missing.
  In Van's V5d3 Badlands Athletics PA save: **all 5 WEB-only
  FighterRecord fields appear on 290/290 records; all 3 WEB-only
  CampRecord fields appear on 41/41 records.** Concrete proof of
  what CLI-side `from_dict` chokes on. The `natural_weight_class`
  TypeError observed at Step 2' pre-fix was one of these — Van's
  save happens to hit `FighterRecord.from_dict` before any
  CampRecord construction.

  **POST-FIX GATES (G1-G4), all PASS [MEASURED, artifacts under
  `outputs/sm1/`]:**

  **G1** (`gate1_a3a_G1_resolution_map.py` + `_G1_postfix.json`):
  post-fix resolution map, diff vs D1. **Names are the discriminator;
  the pass/fail bit alone hides gate-widening.** Two widenings applied
  during G1 (`systems` added to expected-rebind set; missing-rebind
  logic corrected to distinguish "no longer loaded" from "still CLI-*").
  Both had substantive rationale below, but the discipline concern
  stands: an adjusted gate must prove it still discriminates —
  presented here at name-level.

  **11 REBOUND modules (all CLI/SYS→WEB, all PA-parity per disposition):**

  | Module | Before | After | Disposition |
  |---|---|---|---|
  | `core` | `cage_dynasty/core/__init__.py` | `cage_dynasty_web/core/__init__.py` | Package rebind; enables the 7 core.* file rebinds below. |
  | `core.game_state` | CLI | WEB shim | The load-bearing rebind. WEB CampRecord has `location`; CLI does not (D2). |
  | `core.types` | CLI (`3379 B`) | WEB (`3032 B`, different bytes) | CLI has FightRecord (line 334), WEB does not. Consumers under WEB shim don't need it. |
  | `core.persistence` | CLI | WEB | WEB has its own persistence shim. |
  | `core.calendar` | CLI | WEB | Same. |
  | `core.events` | CLI | WEB | Same. |
  | `core.config` | CLI | WEB | Same. |
  | `entities` | CLI real package | WEB stub package (`__init__.py`, 84 B) | Package rebind; enables the 2 entities.* file rebinds below. |
  | `entities.fighter` | CLI real Fighter class (29,379 B) | WEB stub (`from game_state import FighterRecord as Fighter`, 228 B) | This is the DEV/PROD FIGHTER-BINDING SPLIT resolved: local `Fighter` now equals `FighterRecord` alias, matching PA. |
  | `entities.camp` | CLI real Camp (2,824 B) | WEB stub (`from game_state import CampRecord as Camp`, 207 B) | Same story. |
  | `systems` | CLI `systems/__init__.py` (auto-imports aging/training/matchmaking/rankings/economy) | WEB shim `cage_dynasty_web/systems/__init__.py` (INJURY-IMPORT-FIX1, 2392 B) | PA-parity confirmed via server-log evidence below. |

  **3 NO-LONGER-LOADED (all legitimate consequences; PA doesn't load
  them either):**

  | Module | Why gone | Why PA-safe |
  |---|---|---|
  | `entities.contract` | CLI `entities/__init__.py` auto-imported it (indirectly through import chains); WEB stub `__init__.py` doesn't. | No consumer downstream calls `entities.contract` — grep on `cage_dynasty_web/` for `entities.contract` returns zero hits. PA doesn't load it either (WEB `entities/` contains only `__init__.py`, `fighter.py`, `camp.py`, verified via Files-API tree). |
  | `entities.promotion` | Same story. | Same story. Zero web-tree consumers; no PA presence. |
  | `systems.aging` | CLI `systems/__init__.py:9-13` auto-imports `aging`+`training`+`matchmaking`+`rankings`+`economy` on package import; WEB shim doesn't. | Consumers use the BARE name `aging` (flat file `cage_dynasty_web/aging.py`) which still loads via cage_dynasty_web on sys.path[0] — see the `aging  UNCHANGED  WEB` line in the resolution map. Same on PA. |

  **1 NEWLY-LOADED:**

  | Module | Why now | Disposition |
  |---|---|---|
  | `game_state` (bare name) | WEB `cage_dynasty_web/core/__init__.py` shim executes `from game_state import ...` at package-import time; the bare name gets cached in sys.modules as a side-effect. Pre-fix, CLI's `core.game_state` didn't re-import bare `game_state`. | PA-parity: PA's server log shows `✅ Real game modules loaded successfully!` following the same import chain, so `game_state` bare name is cached on PA too (not visible in log, but forced by the shim's import statement). |

  **21 UNCHANGED:** listed in `_G1_postfix.json.modules` with matching
  `__file__` between D1 and G1; no dispositions needed.

  **PA-parity evidence for the `systems` package rebind** (the
  widening that most needed proof beyond the pass/fail bit): PA's
  `cage_dynasty_web/systems/__init__.py:24` contains
  `print("✅ [SYSTEMS-SHIM] systems.injury shimmed from bare injury
  module", file=_sys.stderr)`. That print fires only if the WEB shim's
  module body executed. Server log `/tmp/pa_server_r3.log`, coverage
  2026-08-26 → 2026-08-29 (4 uWSGI worker spawns in retention):

      2026-08-26 04:07:58 ✅ [SYSTEMS-SHIM] systems.injury shimmed from bare injury module
      2026-08-26 05:06:11 ✅ [SYSTEMS-SHIM] systems.injury shimmed from bare injury module
      2026-08-28 02:01:09 ✅ [SYSTEMS-SHIM] systems.injury shimmed from bare injury module
      2026-08-29 05:33:15 ✅ [SYSTEMS-SHIM] systems.injury shimmed from bare injury module

  4/4 worker spawns hit the WEB shim. **PA resolves `import systems`
  to `cage_dynasty_web/systems/__init__.py`** (the WEB shim), not
  `cage_dynasty/systems/__init__.py` (the SYS-tree real package).
  G1's post-fix `systems  REBOUND  SYS → WEB` on local matches this.

  **Total: 11 rebound + 3 no-longer-loaded + 1 newly loaded + 21
  unchanged = 36 tracked modules; zero unexpected rebinds; zero
  still-CLI-tree modules that should have rebound.**

  **G2** (`gate1_a3a_G2_G3_freshworld.py`): fresh `new_game()` fires
  the rich world-gen path.
      "Populating world with AI camps and fighters..."         hits=1
      "Created 40 camps, 306 fighters with simulated history"  hits=1
      "Rich world-gen failed"                                  hits=0
  Same shape as PA's server log on Van's 2026-08-29 Badlands
  new_game (per C5 filing).

  **G3** (same harness as G2): A2-2 inspector on the fresh 306-fighter
  world. All 4 criteria PASS:
    - 306/306 have all 18 engine stats present.
    - cardio ∈ [30, 94] mean 57.04 stdev 14.75; recovery ∈ [30, 95]
      mean 58.54 stdev 14.43.
    - `cardio − recovery` diff span [−25, +24] with 49 distinct
      values (≥[−15,+15] cleared).
    - 10/10 consumption records via `bridge._make_fighter_attrs`
      exact-match `_fighter_data`; consumed diff span [−17, +21].

  **G4** (`gate1_step1_smoke.py` re-run): Step 1 L-J1 smoke requal
  reproduces filed hashes exactly. Proves the fight-engine import
  path (which the qualified v1.5 instruments depend on) is
  unchanged by A3-a.
    raw_md5     a8a5b6809e688395387e7e829b419460  ✓ (target :2796)
    norm_md5    cace1efa4a3c8eabe8a976ec42a6f2ba  ✓ (target :2809)
    landing     150,154   (slot1 77,900 / slot2 72,254)  ✓

  **CORRECTIONS RIDING THIS COMMIT (per Van's bundling directive):**

    - **C5 filing anchor correction**: text at (former) line 4302
      said "Enters `_new_game_impl` at `game_bridge.py:2190-2361`".
      Actual function range is `:2190-2533` (`_new_game_mock` starts
      at `:2534`). The `:2361` was the tail of the coach branch, not
      the function end. The four sub-anchor ranges within the
      function (`:2215-2279` AI branch, `:2316-2327` style,
      `:2330-2332` player-fighter, `:2342-2361` coach) remain
      correct. C5 text preserved as-written per standing rule; this
      C6 filing carries the corrected range.

    - **Addendum 2 outcome — RETIRED [MEASURED,
      `gate1_step2prime_load_and_inspect.py`, 2026-08-29 pre-A3-a-fix].**
      Attempted at Gate 1 Step 2': copied Van's V5d3-verified
      Badlands save into local `saves/`, called
      `bridge.web_load('probeload')`. TypeErrored at
      `game_bridge.py:3019` inside `_web_load_impl` on
      `FighterRecord.from_dict(fd)` → `core/game_state.py:154`
      `cls(**data)` → `TypeError: FighterRecord.__init__() got an
      unexpected keyword argument 'natural_weight_class'`. Same P3
      root cause as world_init failure; different symptom (fires on
      LOAD path, not world_init path). Van's Addendum 2 pre-approval
      hypothesis "load path routes through from_dict (dict consumer,
      not kwarg constructor), so CampRecord `location=` TypeError is
      bypassed by construction" — **FALSIFIED by measurement.**
      `from_dict` at CLI's `game_state.py:154` is a kwarg constructor
      via `cls(**data)` and errors on the first unknown key. And
      `FighterRecord.from_dict` fires before any CampRecord
      construction, so it TypeErrors on `natural_weight_class`
      (WEB-only per D2), not `location`. Approach retired.
      **Post-A3-a-fix: Gate 1 resumes on the ORIGINAL ratified
      Step 2** (local fresh new_game, now proven to work via G2).

    - **CLI FighterRecord + CampRecord drift filed as A3-d expansion.**
      D2's field diff enumerates the full surface. Both classes are
      strict subsets of their WEB counterparts (0 CLI-only fields on
      either). Consequence: any future consumer that reads from
      either save-loaded or fresh dict data via CLI-side dataclass
      construction will error on WEB-only keys. Post-A3-a-fix, all
      such consumers resolve through WEB dataclasses, so this is
      inert in production. Filed as a hazard for any future harness
      that pre-imports `core.game_state` from repo root explicitly.

    - **A3-d shim-directory disposition update.** C5 filed the four
      `cage_dynasty_web/{core,entities,systems,simulation}/` shim
      dirs as load-bearing under the (pre-fix) GAME_PATH mechanism.
      Post-A3-a-fix, they are STILL load-bearing on BOTH PA and
      local — the fix removed the mechanism that WAS routing local
      through CLI; now both environments resolve `core.*` /
      `entities.*` / `systems` via these shims. The C5 warning
      remains in force: **do not delete these shim dirs without
      re-verifying end-to-end**. A3-d ordering constraint at C5
      ("if A3-a fixes GAME_PATH to correctly add repo_root on PA,
      the shim files become genuinely unused") **no longer applies**
      — the ratified A3-a shipped as REMOVAL of the GAME_PATH block,
      not as a fix that adds repo_root. Shim files are load-bearing
      forever under the current architecture.

  **QUEUE (post-C6):**
    - **A3-b**: un-silence world-gen `except` at
      `game_bridge.py:2272-2279` (narrow to specific exceptions +
      full traceback). Its own gates, its own single-purpose commit.
    - **A3-c**: UI stat-fabrication + 6/18 offset divergence at
      `_convert_real_fighter._attr`. Its own arc.
    - **Gate 1 resumes on original ratified Step 2**: local fresh
      `new_game` (now working — G2 proof), A2-2 inspector on it
      (G3 proof), then Step 3 bin table + Q1 five-round arm per
      the v0.2 ratified execution prompt. Addendum 2 formally
      retired.

  **ARTIFACTS this commit (all under `outputs/sm1/`, untracked):**
    - `gate1_a3a_D1_resolution_map.py` + `_D1_baseline.json`
    - `gate1_a3a_D2_dataclass_diff.py` + `_D2_dataclass_diff.json`
    - `gate1_a3a_G1_resolution_map.py` + `_G1_postfix.json`
    - `gate1_a3a_G2_G3_freshworld.py`
    - `gate1_step2prime_load_and_inspect.py` (Addendum 2 attempt +
      retirement evidence)
    - `gate1_step1_smoke.py` (re-run for G4)

- **STAMINA-MODEL1 — Gate 1 CLOSED + G1F findings + Q4d premise
  correction [SHIPPED 2026-08-30 as C7 docs checkpoint; no engine
  edits; RECOVERY-WIRE1 fix arc queued as separate single-purpose ship].**

  Session covers: Gate 1 execution (bin pool R2 + Tier A + Tier B),
  Van-ordered G1F followups (F1-F4), and one C4-era correction owed
  under the standing wrong-numbers rule. Full reports at
  `outputs/sm1/gate1_report.md` (246 lines) and
  `outputs/sm1/gate1_G1F_report.md` (172 lines). All harnesses under
  `outputs/sm1/gate1_*_run.py`, `_analysis_and_report.py`,
  `_G1F_*.py`. Save states under `cage_dynasty_web/saves/` (gitignored).

  **Bin pool (R2, ratified 2026-08-30).** 17 fresh worlds (10 cached
  from R1 + 7 generated under R2 extension), 4,920 AI fighters total.
  Bin thresholds unchanged (rec≥85/≤65 × car≥85/≤65). Selected 5
  lowest-fid per cell (deterministic, name-free). Van's docket item on
  generator archetype scarcity filed at
  `claude/generator_variety_notes_2026-08-30.md` (world #1 population
  Pearson r=0.7531; HL/LH each ~0.10% per world). Pool-population
  question closed; downstream is engine mechanics.

  **Tier A — 2,100 instrumented fights** (2,000 3R + 100 5R HH-HH),
  20 pooled fighters, v1.5 wrapper on fe.CSS + fi.CSS, base seed 1000.
  Wall time 54.1s. Method distributions per pairing in report §2. All
  11 pairings ran clean; landing rows total ~132K.

  **P3 target-trajectory table** (report §3), last-CSS att_stamina
  per (slot_bin, round), 3-round arm:

  | bin | R1-end | R2-end | R3-end |
  |---|---|---|---|
  | HH | 13.4±27.5 (n=891) | 7.5±20.1 (n=817) | 8.0±20.3 (n=598) |
  | HL | 26.1±38.6 (n=812) | 17.8±33.1 (n=764) | 13.8±28.8 (n=669) |
  | LH | 19.1±33.2 (n=864) | 10.8±25.4 (n=802) | 9.6±22.7 (n=655) |
  | LL | 24.9±36.2 (n=360) | 19.2±33.4 (n=361) | 15.6±30.7 (n=358) |

  **F3 accounting caveat, load-bearing for LL cell interpretation:**
  LL rounds are 60-64% CSS-blind. Per (bin, round), expected
  fighter-rounds from schedule vs observed:
      HH R1 891/1000, R2 817/1000, R3 598/1000 (early finish 30% by R3)
      HL R1 812/1000, R2 764/1000, R3 669/1000
      LH R1 864/1000, R2 802/1000, R3 655/1000
      LL R1 360/1000, R2 361/1000, R3 358/1000  ← 64% no_CSS_gap
  LL fighters run grapple/sub-heavy exchanges that don't fire the CSS
  wrapper (same shape as EXCH-CTR-OBS1 filed at Gate 0(b)). LL n
  counts of ~361 are the strike-active subset; the majority of LL
  rounds are unobserved by this instrument. HH/HL/LH attrition is
  dominated by early finish (KO+TKO in R1-R2), not sampling. **This
  caveat MUST accompany any tank-vs-refill design conclusion drawn
  from the P3 LL row.**

  **P4 resolved.** 3 weeks of live-play advance_week on world #1 with
  v1.5 wrappers on both hook sites → **206,224 CSS calls captured,
  100% caller_id=fi810, 0% fe3315.** Same shape as harness path per
  Gate 0(b) A2 filing. fe.simulate_exchange (fe:3315) is dead on
  live-play. Tier A's harness path (fi810) IS the live-play path —
  fixture arithmetic transfers by construction. (But see G1F P2 below
  for the fi-side wiring defect that affects both harness and live.)

  **Tier B — N=93 fights over 15 weeks of world #1 (advance_week).**
  DEC 43.01% / SUB 3.23% / KO+TKO 50.54%. In-band vs POOL-DEC-RATE1
  (this file, filed at :4364-4406): 44.6% / 1.3% / 54.1%, N=157,
  pre-e1be619 vintage. **N=93 accepted-as-observational per Van
  2026-08-30**, no week extension; clean violence re-read deferred
  until post-stamina-arc when the population dynamics stabilize.

  ─────────────────────────────────────────────────────────────────
  ## G1F findings (Van-ordered follow-up, 2026-08-30)
  ─────────────────────────────────────────────────────────────────

  **P1 disposition RESTATED — CONFOUNDED-UNRESOLVED (was: refuted
  by Gate 1 §5).** [MEASURED, `gate1_G1F_followups.py` F1 + source
  read at `fight_integration.py:1276-1282`.]

  Source verification: the drain formula at `fi:1276-1282` reads:

      _stamina_cost = float(props[2])   # per-strike stamina cost
      _att_gp_s = getattr(attacker_state, '_gameplan', None)
      if _att_gp_s is not None:
          _att_agg_s = int(getattr(_att_gp_s, 'aggression', 0) or 0)
          if _att_agg_s != 0:
              _exec_s = dial_execution(attacker, attacker_state)
              _stamina_cost *= (1.0 + 0.15 * _att_agg_s * _exec_s)
      attacker_state.spend_stamina(_stamina_cost)

  Tier A ran default BALANCED gameplan → aggression=0 → dial_execution
  branch never fires → drain per exchange = `props[2]` alone. **Cardio
  is not an input to the drain formula on this path.**

  Per-bin stat profile of the 20 pooled fighters (mean±stdev, n=5 per
  cell) — HH vs HL differ on multiple aggression-relevant channels
  beyond cardio:

  | stat | HH mean | HL mean | Δ |
  |---|---:|---:|---:|
  | fight_iq         | 86.6 | 72.4 | +14.2 |
  | cardio           | 91.6 | 63.4 | +28.2 (by construction) |
  | recovery         | 88.0 | 85.0 | +3.0 |
  | boxing           | 78.8 | 73.0 | +5.8 |
  | kicks            | 81.2 | 65.4 | +15.8 |
  | clinch_striking  | 78.2 | 65.8 | +12.4 |
  | takedowns        | 82.6 | 69.0 | +13.6 |
  | submissions      | 77.4 | 70.6 | +6.8 |

  The measured HH−HL slope delta (+0.34 pts/exchange in R1) originates
  in strike-selection confounds — HH fighters' higher kicks (+15.8)
  and clinch_striking (+12.4) and fight_iq (+14.2) shift their action
  distribution toward different strike TYPES with different `props[2]`
  costs. Not a cardio-in-formula effect. P1 moves from 'refuted' to
  'confounded-unresolved'. **A design edit wiring cardio into drain
  will need remeasurement on a schedule where cardio-in-drain is the
  only variable.**

  ─────────────────────────────────────────────────────────────────

  **P2 disposition RESTATED — WIRING DEFECT at `fi:503-515` (was:
  under-response to recovery, attributed to CSS-sampling artifact in
  Gate 1 §6).** [MEASURED, `gate1_G1F_followups.py` F2 +
  `gate1_G1F_F2_debug.py` + source reads at `fi:503-515` and
  `fe:4060-4074`.]

  F2 log-only wrapper on `fe.FighterState.new_round` across 200
  diagnostic fights (HH×LH + HL×LL, 50 fights per orient, declared
  seeds base=1000, pairing_idx ∈ {105, 108}). **1,114 refill events
  captured. Variance of recovery_rating_consumed = 0 across all 20
  fighters** despite real recovery stats spanning 33-94.

  Root cause quoted from source (`fight_integration.py:503-515`,
  `simulate_narrated_fight._init_engine`):

      self.fighter1_state = FighterState(
          fighter_id=self.fighter1.fighter_id,
          name=self.fighter1.name,
          health=100.0 + self.fighter1.chin * 0.5,
          stamina=self.starting_stamina_f1
      )
      self.fighter2_state = FighterState(
          fighter_id=self.fighter2.fighter_id,
          name=self.fighter2.name,
          health=100.0 + self.fighter2.chin * 0.5,
          stamina=self.starting_stamina_f2
      )

  **No `recovery_rating` kwarg.** Falls to `FighterState.recovery_rating:
  int = 50` class default at `fight_engine.py:565`. Formula at
  `fe:614-631` fires correctly with whatever `recovery_rating` is —
  but the source value is dead on this path.

  **Pre-gen path is wired correctly**: `fe.simulate_fight` at
  `fe:4060-4074` constructs FighterState WITH `recovery_rating=
  fighter1.recovery` and `recovery_rating=fighter2.recovery`.
  **Pre-gen and live-play use different stamina refill formulas
  by construction** — pre-gen respects per-fighter recovery, live-play
  applies rec=50 to everyone. This split predates every measurement
  in this arc.

  Single-fight trace confirms directly
  (`outputs/sm1/gate1_G1F_F2_debug.py`, one 3R fight between LL
  `00090425` (rec=33) and HL `42dab69a` (rec=85)):

      new_round: fid=00090425 cur_round=2 rec_rating=50 stam_before=46.31 stam_after=73.81 delta=+27.50
      new_round: fid=42dab69a cur_round=2 rec_rating=50 stam_before=0.50  stam_after=28.00 delta=+27.50

  Both fighters `rec_rating=50` despite real stats 33 vs 85. Formula
  output identical: `15 + (50/100)*25 = 27.5` for both. **Elite
  recovery (94) and poor recovery (33) fighters get identical refills
  in live play.**

  **Recovery is a design attribute with a dead consumer on the
  runtime path production uses.** RECOVERY-WIRE1 fix arc queued as
  separate single-purpose ship — spec draft under
  `outputs/sm1/gate1_RECOVERY_WIRE1_spec_draft.md`, awaiting Van's
  ratification.

  **Gate 1 §6 P2 finding (~0.007 slope) restated:** was two artifacts
  stacked: (a) CSS-sampling attenuation of first-CSS-of-round
  measurement (real, EXCH-CTR-OBS1 shape); (b) wiring defect above
  — the recovery source is dead so the slope is genuinely 0 on the
  live path regardless of measurement instrument.

  ─────────────────────────────────────────────────────────────────

  **×1.3 championship-round ratio CONFIRMED.** [MEASURED, Gate 1 §6
  5-round arm, HH×HH pairing_idx=10.] Across 5 HH fighters, mean
  late/early refill ratio = **1.212** (stdev 0.137, n=5). Prediction
  1.3 per `fe:628-629` `bonus_recovery *= 1.3 if _current_round >= 4`.
  Slightly under 1.3, consistent with the same CSS-sampling
  attenuation as P2. Formula fires correctly; the ×1.3 multiplier
  IS active on R4+ boundaries in the harness. (Note: fires with
  rec_rating=50 for the same wiring reason as P2; post-fix expected
  behavior is unchanged in RATIO but different in ABSOLUTE refill
  magnitude.)

  ─────────────────────────────────────────────────────────────────
  ## CORRECTION — Gate 0(b) Q4d filing (owed under standing rule)
  ─────────────────────────────────────────────────────────────────

  C4 checkpoint at (this file, currently :3928 in the Q4d bullet
  of the "STAMINA-MODEL1 — Gate 0(b)" block) filed:

    > "Q4d sawtooth (round-boundary mean-stamina jump): +20 to +24pp
    > across all 7 arms, 2SE emphatically excludes 0. B4 hand-model
    > reconciliation clean (~+33.75 gross recovery at recovery=75,
    > minus concurrent early-R2 drain)."

  **The ~33.75 gross-refill premise is documented-was-wrong.**
  Derivation assumed `recovery_rating=75` (the L-J1 all-75 fixture
  stat). Per F2 above, the v1.5 probe's `_run_path_a_ref` calls
  `fi.simulate_narrated_fight`, which per fi:503-515 uses
  `recovery_rating=50` regardless of the fighter's fixture stat.
  **Actual gross refill was `15 + (50/100)*25 = 27.5`**, not 33.75.

  The sawtooth finding itself STANDS: +20 to +24pp measured
  round-boundary jump across all 7 arms, 2SE excludes 0 — the shape
  is real. The measured 20-24 range fits the corrected premise of
  27.5 gross minus concurrent early-R2 drain, just as it fit the
  wrong 33.75-minus-larger-drain premise. Sawtooth existence
  reconciles either way; the premise number was wrong.

  Related same-family correction at :3999-4000: the A1 subsection
  paragraph "R2 opens ~28-40 (visible partial refill matching B4 hand
  model's +33.75 at recovery=75, minus early-R2 drain)" — same
  33.75→27.5 substitution applies. R2 opening in the L-J1 fixture was 27.5-pt gross refill
  minus early-R2 drain, not 33.75-pt.

  Per standing rule (documented, not dropped): original C4 text
  preserved as-written; this C7 filing carries the corrected premise.
  Post-RECOVERY-WIRE1: L-J1 will run at recovery_rating=75 (from
  fighter.recovery=75), gross refill returns to the intended 33.75.
  Fixture hashes will break (expected, gated in RECOVERY-WIRE1 W3).

  ─────────────────────────────────────────────────────────────────
  ## Queue
  ─────────────────────────────────────────────────────────────────

  - **RECOVERY-WIRE1** — single-purpose fix arc, Van-ratified in
    principle 2026-08-30, spec awaiting ratification. Fix: pass
    `recovery_rating=<fighter>.recovery` at fi:503-515, mirroring
    fe:4060-4074. Gates W1-W4 (F2 rerun, Tier A P3 rerun, L-J1
    hash break certification, tree cleanliness). Behavior-changing
    arc; L-J1 fixture hashes EXPECTED to break. Spec draft at
    `outputs/sm1/gate1_RECOVERY_WIRE1_spec_draft.md`.
  - **Post-RECOVERY-WIRE1**: Van fills target-trajectory table using
    RERUN P3 (Tier A schedule against real per-fighter recovery).
  - **Post-target-table**: stamina-model design phase begins. Docket
    items already filed for that phase: (a) generator archetype
    scarcity (`claude/generator_variety_notes_2026-08-30.md`);
    (b) P1's cardio-into-drain design question; (c) Tier B clean
    violence re-read (deferred until post-stamina-arc per Van
    2026-08-30).

  ─────────────────────────────────────────────────────────────────
  ## Artifacts (all under `outputs/sm1/`, untracked)
  ─────────────────────────────────────────────────────────────────

  - `gate1_report.md` (246 lines, Gate 1 full report — unmodified)
  - `gate1_G1F_report.md` (172 lines, F1-F4 followups)
  - `gate1_step3_pool_manifest_R2.json` (bin pool + selection +
    provenance + world #1 correlation)
  - `gate1_tierA/` (46 files: 22 outcome CSVs + 22 landing CSVs +
    manifest + done flag; 2,100 fights, ~132K landing rows)
  - `gate1_tierB/` (5c landing CSV + manifest + done flag)
  - Harnesses: `gate1_tierA_run.py`, `gate1_tierB_run.py`,
    `gate1_analysis_and_report.py`, `gate1_G1F_followups.py`,
    `gate1_G1F_F2_debug.py`
  - Multi-world pool harnesses: `gate1_step3_multiworld_pool.py` +
    `..._extend.py`
  - RECOVERY-WIRE1 spec draft: `gate1_RECOVERY_WIRE1_spec_draft.md`
  - Save states under `cage_dynasty_web/saves/bridge_anon_gate1_mw_*`
    (17 world saves) and `bridge_gate1tierB_w1*` (Tier B anchor +
    5b mid-checkpoint) — all gitignored.

- **STAMINA-MODEL1 — RECOVERY-WIRE1 fix + fixture re-baseline
  [SHIPPED 2026-08-30 as C8 code+docs commit; single-purpose fix per
  Van-ratified spec; unblocks target-trajectory table].**

  Fixes the wiring defect diagnosed at C7 P2 (fi:503-515 constructs
  `FighterState` without `recovery_rating` kwarg → falls to class
  default 50 → per-fighter recovery attribute is a dead input to the
  between-round refill formula on the live-play path). Fix passes
  `recovery_rating=<fighter>.recovery` per FighterState construction,
  mirroring the correctly-wired pre-gen path at fe:4060-4074. Amended
  spec at `outputs/sm1/gate1_RECOVERY_WIRE1_spec_draft.md`
  (amendments B + C ratified 2026-08-30).

  **DIFF (single tracked file, `cage_dynasty_web/fight_integration.py`):**
  +11 / −2 lines. Two `recovery_rating=` kwargs added; two trailing
  commas added on the preceding `stamina=` lines; a 7-line comment
  block above the constructions documenting the fix + cross-referring
  C7 filing.

  **W1 — wiring PASS gate + slope report** [MEASURED,
  `outputs/sm1/gate1_G1F_followups.py` F2 block rerun post-fix]:
    - 200 diagnostic fights (HH×LH pairing_idx=105 + HL×LL
      pairing_idx=108, 50 fights per orient, declared seeds base=1000).
    - 1,096 refill events captured across 20 pooled fighters.
    - **PASS GATE: 20/20 fighters have `recovery_rating_consumed
      == fighter.recovery`.** Variance of rec_used now > 0 (range
      33-94, was exactly 50 for all 20 pre-fix).
    - Report-not-gate: aggregate R2 refill vs recovery slope = 0.470
      (>0, 2SE excludes zero); attenuators named per amendment B —
      `min(100, ·)` ceiling clamp truncates high-recovery refills
      (HH fighters' stamina_before was already high → measured deltas
      undershoot formula's 0.25 slope); LL contamination amplifies
      slope estimate above 0.25 because LL measured refills undershoot
      formula more than HL measured refills.
    - Per-fighter clean cases (predicted vs measured R2 refill for the
      5 HL fighters, all at recovery=85, formula predicts 36.25):
      42dab69a 36.25 (n=20), 5f03bb6c 36.25 (n=19), 60a65022 36.25
      (n=20), 85f73bf3 36.25 (n=19), f6750bf7 36.25 (n=20). **HL
      fighters' measured refill hits the formula prediction exactly**
      — clamp doesn't reach them since their pre-refill stamina is
      low. Formula fires as designed with real recovery input.

  **W2 — Tier A P3 rerun + before/after table** [MEASURED,
  `outputs/sm1/gate1_tierA_run.py` rerun; report at
  `gate1_recovery_wire1_W2_report.md`]:

  2,100 instrumented fights rerun on the same 20 pooled fighters,
  same seeds, same 11 pairings. Wall time: pre 54.1s vs post 53.9s.

  **P3 target-trajectory table (post-fix)** — last-CSS att_stamina
  per (slot_bin, round), 3-round arm:

  | bin | R1-end (mean±sd, n) | R2-end (mean±sd, n) | R3-end (mean±sd, n) |
  |---|---|---|---|
  | HH | 14.9±29.3 (n=894) | 8.5±20.4 (n=789) | 9.4±20.7 (n=543) |
  | HL | 26.8±39.0 (n=814) | 19.4±34.1 (n=749) | 16.7±30.9 (n=656) |
  | LH | 18.5±32.6 (n=861) | 11.4±26.5 (n=798) | 10.5±24.2 (n=652) |
  | LL | 24.6±35.6 (n=360) | 19.3±33.4 (n=364) | 15.3±30.4 (n=359) |

  **Δ (POST − PRE mean, per cell)**:

  | bin | ΔR1-end | ΔR2-end | ΔR3-end |
  |---|---:|---:|---:|
  | HH | +1.45 | +0.93 | +1.38 |
  | HL | +0.67 | +1.52 | +2.94 |
  | LH | −0.54 | +0.60 | +0.90 |
  | LL | −0.30 | +0.11 | −0.30 |

  Direction of Δ matches arithmetic predictions: HL fighters (rec=85)
  get the biggest jumps (+2.94 R3-end) because their recovery-scaled
  refill jumped 27.5→36.25 (+8.75 per boundary, compounding across R2
  and R3). LL fighters (rec 33-52) see slight decreases — their
  refills fell 27.5→~25 per boundary. LH fighters mid.

  **5R HH×HH arm — R4-end and R5-end (championship-bonus rounds)**:

  | round | pre  | post | Δ |
  |---|---|---|---:|
  | R4 | 9.6±14.9 (n=66) | 12.2±20.7 (n=63) | +2.6 |
  | R5 | 10.0±16.1 (n=18) | 18.1±24.9 (n=19) | +8.1 |

  The ×1.3 championship-bonus compounds with the corrected recovery
  input — R5-end jumped +8.1 pts. Pre-fix, ×1.3 fires on rec=50 →
  bonus 12.5×1.3=16.25 → gross refill 15+16.25=31.25 (vs unchamp
  27.5, only +3.75). Post-fix at rec=85: bonus 21.25×1.3=27.625 →
  gross 42.625 (vs unchamp 36.25, +6.375). Championship rounds now
  meaningfully favor high-recovery fighters.

  **Method distribution shifts, largest first**:

  | pairing | Δ KO+TKO% | Δ DEC% |
  |---|---:|---:|
  | P06 HHxLL_3R | +8.0 | −7.0 |
  | P08 HLxLL_3R | +8.0 | −8.0 |
  | P02 LHxLH_3R | −5.5 | +7.0 |
  | P00 HHxHH_3R | +5.0 | −2.5 |
  | P07 HLxLH_3R | −4.0 | +4.0 |

  High-recovery vs low-recovery pairings finish MORE (HH×LL +8.0pp
  KO+TKO); mid-recovery symmetric pairings decision MORE (LH×LH +7.0pp
  DEC). The recovery-scaled refill differentiates cardio-heavy vs
  cardio-light fighters where the wiring bug was masking that
  differentiation.

  **W3 — fixture-hash EXPECTED BREAK: all 7 arms failed old hashes**
  [MEASURED, `outputs/sm1/strike_landing_probe_v15.py` full 7-arm
  rerun at N=2000 with wrappers ON].

  **All 7 fixture hashes broke as designed.** Every arm's fighters
  have recovery != 50 (L-J1 fixture all-75 symmetric; single-stat
  arms modify one stat but not recovery unless it's the modified
  stat; grappling fixture has default 75). Recovery-scaled refill
  changes outcome shapes on every fixture.

  **Retirement table — OLD hashes (pre-fix relic, correct
  measurements of the recovery_rating=50 buggy behavior)**:

  | arm | OLD raw md5 | OLD norm md5 |
  |---|---|---|
  | L-J1  | a8a5b6809e688395387e7e829b419460 | cace1efa4a3c8eabe8a976ec42a6f2ba |
  | L-B88 | 6c2f82ac46c5a476367f3c0684710237 | d2d943266a81c6817bbed5062b6fa37a |
  | L-K74 | 2f1d2034aa308391ea487dfe776adda1 | 3e5de0d7963bc66cd2cf65ff1d981d0e |
  | L-K78 | 506b2a36c75597c6966bc9db0ca5f7cc | 84398fe0269ee06968643ca3b10dc570 |
  | L-K88 | 1dc762fcd6a399c623a958cc50989009 | c5c8040941c25b2f7ecff1afce049a20 |
  | L-C88 | abd4b299ef565d5b1ae6fccf792510c2 | 56e7987c0bbf99d78db8cccf29fa3ef8 |
  | F     | 11d4be8c28902e9e26c6d627424663fe | 78605664d38afa9b6abfaa83b9cc16ce |

  Retired as regression targets; preserved per standing wrong-numbers
  rule. Previous filings at STRIKE-LANDING-AUDIT1 (this file
  :2796-2799 raw, :2809-2812 norm), STAMINA-MODEL1 Gate 0(b) v1.5
  qualification (:3897-3914), Gate 1 Step 1 smoke requal
  (`outputs/sm1/gate1_step1_smoke.py`), Gate 1 A3-a G4 smoke requal
  (part of C6 filing) are all documented-was-correct-for-pre-fix.
  Any future regression check against those specific values must be
  qualified with "pre-RECOVERY-WIRE1 (C8)".

  **NEW post-RECOVERY-WIRE1 hashes (certified baseline)**:

  | arm | NEW raw md5 | NEW norm md5 | landing rows |
  |---|---|---|---:|
  | L-J1  | 02b9a62ea1a581da43cda0074a3c36f7 | 9271a4e60a35247ba0613b10dd715382 | 154,913 |
  | L-B88 | b421b5c01534d8f1013b8fdf4f4d97be | 483cd4dea135b6ce7753d2977669036d | 134,147 |
  | L-K74 | 4dae6c6be0f100763cde137d6cffef1b | e31e79d9546dcf77330a67496b1afc14 | 136,972 |
  | L-K78 | 52387566b8d2d29fb1e85e1aa4de0985 | 9532ce8cc061de1ddc106a65709e3b4a | 143,393 |
  | L-K88 | 547966e1913ecd2a32bf8d1b5ee15412 | c025febdf78d3e81429cc671f05a3ac3 | 130,897 |
  | L-C88 | 041dae4ffc41d431ab6b97c1b66fcdec | 065172df2b40face63d839a73392c03e | 131,357 |
  | F     | 00f41d144dea015f675b177725f20c41 | d74f66f5d1c33927fbc2d17d0c1e2fd5 | 136,899 |

  L-J1 landing row count went 150,154 → 154,913 (+4,759). Consistent
  with fighters lasting longer per round-boundary (more refill → more
  exchanges → more CSS calls). Direction is uniform across arms.

  Probe file (`outputs/sm1/strike_landing_probe_v15.py`)
  `REUSED_HASH_TARGETS` and `REUSED_NORM_HASH_TARGETS` dicts updated
  in place to the NEW post-fix values. Future re-anchor gates against
  the probe check the new hashes.

  **Probe file sha256 transition (per amendment C)**:

  | epoch | sha256 |
  |---|---|
  | pre-fix (retiring — was the certified fingerprint through C5+C6+C7) | `aef08f57cba1be6c694a7c8d10d151ed439bccd1246a77c0e5290d7a8bb98093` |
  | post-fix (certified 2026-08-30 as C8 baseline) | `3ca1f644828c1277f7118229f2438235c6ead51a2e81431a8e08ed0669b88a52` |

  Future sessions' instrument re-anchor gates should compare against
  the NEW sha256. The old value is retired as the pre-fix fingerprint.
  Same standing rule as fixture hashes — old preserved as accurate
  measurement of its era, new certified as the post-fix baseline.

  **W4 — tree cleanliness**:
    - Single tracked file modified: `cage_dynasty_web/fight_integration.py`
      (+11 / −2).
    - Probe file untracked (session artifact under `outputs/sm1/`,
      which is not gitignored but has never been tracked); dict
      updates + comment there are captured in the sha256 transition
      above.
    - `git status --porcelain | grep -v '^??'` shows only the one
      tracked file modified.
    - **Diff shape deviates from spec §1's declared +2/−0** (7-line
      explanatory comment block added above the FighterState
      constructions cross-referring C7 + G1F F2 measurement);
      deviation reviewed and accepted by Van at commit approval.

  **CORRECTIONS RIDING THIS COMMIT (per bundling directive)**:

    - **C7 Q4d correction's forward-looking claim reverts**: C7 filed
      (currently `~L4830`, "Post-RECOVERY-WIRE1: L-J1 will run at
      recovery_rating=75 (from fighter.recovery=75), gross refill
      returns to the intended 33.75. Fixture hashes will break
      (expected, gated in RECOVERY-WIRE1 W3)."). **Prediction
      confirmed by W3.** L-J1's `fighter.recovery=75` reaches the
      formula; L-J1's between-round refill is now 33.75 (=15 +
      75/100*25) per the C7 correction; hashes broke as expected.

    - **Any Van-facing analytical filing that depended on
      recovery_rating=50 as the wire-truth is now pre-C8 vintage**:
      Gate 0(b) L-J1 sawtooth measurement (+20-24pp per Q4d in C7);
      Gate 1 §6 P2 slope (~0.007) and mean refill (20.52); Gate 1
      §6 5R HH ratio (1.212, n=5 pre-fix). All were correct
      measurements of the pre-fix behavior. Post-fix, corresponding
      numbers land elsewhere on the same axes — the shapes remain
      (sawtooth, ratio ~1.3, refill positively correlated with
      recovery) but the specific numeric anchors shift. Future
      regression checks against those anchors must qualify as
      "pre-C8 (RECOVERY-WIRE1)".

    - **Pre-gen vs live-play stamina physics unified as of C8.**
      C7 P2 filing noted the split: pre-gen (fe.simulate_fight)
      correctly wired at fe:4060-4074, live-play (fi.simulate_narrated_fight)
      wrong at fi:503-515. C8 removes the split — both paths now
      pass per-fighter recovery. The historical filing's "pre-gen
      and live-play use different stamina refill formulas by
      construction" line is documented-was-true-through-C7,
      resolved as of C8.

  **QUEUE (post-C8)**:
    - **Target-trajectory table is now Van's to fill** using the
      W2 post-fix P3 table above as the measurement anchor.
    - **Framework-gate cascade re-baselines** (own arcs, filed but
      not scheduled): Gate 0c golden master, Stage 0d, MC ODDS
      invariants, and any other filed test-fixture arithmetic that
      pinned to the recovery_rating=50 behavior. Each needs its own
      before/after certification pass.
    - **Deploy decision is Van's** — separate from this commit.
      Post-deploy, live-play behavior shifts population-wide: any
      Van-facing analytical filing that measured decision rates,
      finish rates, upset rates, etc. on the pre-C8 live path
      becomes vintage on deploy day.
    - **Post-target-table: stamina-model design phase begins.** Docket
      items from C7 unchanged: (a) generator archetype scarcity,
      (b) P1 cardio-into-drain design question, (c) Tier B clean
      violence re-read post-stamina.

  **ARTIFACTS (all under `outputs/sm1/`, untracked)**:
    - `gate1_RECOVERY_WIRE1_spec_draft.md` (amended spec)
    - `gate1_recovery_wire1_W2_report.md` (before/after P3 + method
      shifts)
    - `gate1_recovery_wire1_analysis.py` (analysis harness)
    - `gate1_tierA_prefix/` (pre-fix Tier A run, preserved for
      side-by-side)
    - `gate1_tierA/` (post-fix Tier A rerun; 46 files)
    - `gate1_step1_smoke_out.txt` (W3 evidence for L-J1)
    - `strike_landing_v15_on_landing_*.csv` and `_outcome_*.csv`
      (full 7-arm probe rerun for hash re-baselining)
    - `strike_landing_probe_v15.py` UPDATED: REUSED_HASH_TARGETS +
      REUSED_NORM_HASH_TARGETS to new hashes; new sha256
      `3ca1f644828c1277f7118229f2438235c6ead51a2e81431a8e08ed0669b88a52`.

- **STAMINA-MODEL1 — Design Gate 0 [CLOSED 2026-08-31, docs
  checkpoint at baseline `0ca052c`, no engine edits; read-only
  measurement pass ordered G0-1 → G0-1b → G0-1c → G0-3 → G0-4 →
  G0-4b → G0-4c → G0-4d → G0-2].**

  Scope: characterize starting-stamina wiring, drain accounting,
  cardio consumers, and pre-fix baselines needed for design phase
  and Gate 1. Read-only throughout; every claim measured or
  source-quoted.

  Artifacts:
   - Harnesses: outputs/sm1/design0/g0_{1,1b,1c,3,4,4b,4c,4d,2}*.py
   - Manifests: outputs/sm1/design0/g0_{...}_manifest.json
   - Corrections draft: outputs/sm1/design0/gate0_corrections.md
   - Certified corrected Tier A CSVs:
     outputs/sm1/design0/tierA_corrected/ (2100 outcomes + 2100
     landing CSVs from outputs/sm1/design0/tierA_corrected_run.py)

  ═══════════════════════════════════════════════════════════════════
  ## MEASUREMENTS

  **G0-1 — starting_stamina fatigue-channel wiring.**
   - Verdict per channel (initial reading, later corrected —
     see CORRECTIONS #1):
     * CH1 starting_stamina from fatigue: WIRED to constructor
       (15/15 samples match `condition.get_starting_stamina(fatigue)`).
     * CH2 per-round fatigue penalty (fi:427-434 inline table):
       PARTIAL — inline table returns half or less of condition's
       intended per-round penalty (READY→0 vs cond 1; TIRED→1 vs
       cond 2; EXHAUSTED→2 vs cond 4). The `return 4` at fi:432 is
       reachable only if starting_stamina < 65; not directly
       reachable via fatigue alone (condition floors at 65) but
       IS reachable via cut floor 60 — see G0-1c Item 5.
     * CH3 pre-gen inline get_starting_stamina at fe:4023-4043:
       PARTIAL — pre-gen adds a fatigue ≤ 10 → 103.0 "peak
       condition" bucket that condition module clips at 100.
   - Anchor: `outputs/sm1/design0/g0_1_manifest.json`,
     `g0_1_condition_wiring.py`.

  **G0-1b — cut-severity population distribution + histogram.**
     Initial reading (later corrected — see CORRECTIONS #2):
     cut ON aggregate mean 89.48; 25/290 at floor 60 exactly;
     severity dist {0:178, 1:35, 2:26, 3:34, 4:17}.
   - Instrument: `g0_1b_starting_stamina_origin.py`. Anchor world
     `gate1_mw_1_1788106887` (290 AI fighters).
   - Contamination discovered in G0-1c: harness read
     `fdata.get("weight_class", "Lightweight")`, but fighter_data
     lacks the key. All 290 fighters defaulted to Lightweight in
     the harness → cut_severity computed against real natural
     inflated up to 4. **G0-1b numbers preserved as WRONG-and-
     documented per standing rule.**

  **G0-1c — cut confound + natural_weight_class origin trace +
   corrected pool table.**
   - Corrected population cut-severity distribution (N=290):
     * severity 0: 270  (268 confirmed + 2 empty-natural fighters
       fdata-fid 331f9ba4, 46645ab7 which route through gb:19780
       empty-nat fallback → severity 0)
     * severity 1: 20
     * severity ≥ 2: 0
   - Corrected 20-pool table: 16 at starting_stamina=100, 4 at
     [85, 90) (00090425 LL 85.71, 074cd4d1 HH 88.66, 85f73bf3 HL
     88.75, a218b4d7 LH 89.39). None below 85. Matches
     `world_init.py:2548-2555` generator arithmetic (gap ∈
     {-1, 0, +1} by construction).
   - HH<HL at R1-end SURVIVES on cut-0 fighters only:
     ALL slice Δ(HH−HL) = −11.88 (n_HH=894, n_HL=814)
     CUT-0 slice Δ(HH−HL) = −9.01 (n_HH=720, n_HL=684)
     Cut explains ~24% of the HH<HL gap; ~76% is intrinsic.
     **Both numbers computed on the pre-correction Tier A CSVs
     (`gate1_tierA/`, WC-bug population). Not certified against
     the corrected population.** The certified corrected-population
     version of the HH−HL cut-0 R1 comparison is G0-4d Item 2d
     (Δ = +7.87 ±3.71 total-drain on the total-drain axis, not
     the CSS-last_ss axis).
   - Empty-natural fallback at gb:19780 SILENTLY returns severity 0.
     No crash, no warning. 2 anchor-world fighters exercise this
     path today.
   - Anchor: `outputs/sm1/design0/g0_1c_manifest.json`,
     `g0_1c_cut_confound_and_origin.py`.

  **G0-3 — drain-side inventory: STRIKE_PROPERTIES, aggression
   multiplier, per-round drain (CSS-strike-only, later completed
   by wrapper in G0-4d).**
   - STRIKE_PROPERTIES props[2] cost table dumped by family
     (fight_engine.py:219-261). Ranges:
     * boxing (5 strikes): mean 4.4, [2, 6]
     * kicks (10 strikes): mean 6.5, [3, 12]
     * clinch_explicit (3 strikes): mean 4.0, [3, 5]
     * clinch_fallthrough (12 strikes): mean 5.5, [3, 12]
   - Aggression multiplier fi:1276-1284:
     `_stamina_cost *= 1 + 0.15 * aggression * dial_execution`.
     Reachable range [0.850, 1.150]. **BALANCED gameplan (Tier A
     default) → aggression=0 → multiplier=1.000 → DORMANT on
     every measurement in this gate.**
   - Per-round strike-drain (CSS-only, ALL pool):
     HH R1 drain 79.6, HL R1 70.1, LH R1 75.7, LL R1 68.1.
     R2/R3 lower (fewer exchanges, floor-clipped).
   - Coverage limit noted upfront: CSS captures STRIKE attempts
     only; grapple/sub/body/KD/rocked drain sites are invisible
     to CSS. Numbers are LOWER BOUND on total drain.
   - Cut-fighter slice vs cut-0 slice per bin: cut fighters
     showed LOWER strike drain per R1 in every bin, driven by
     LOWER strike-attempt count, not lower per-strike cost.
     Rider filed by Van; investigated in G0-4/G0-4c: body_frame
     ruled out as engine consumer (G0-4 grep — zero fe/fi hits).
     Remaining explanation: n=1 cut fighter per bin, individual
     identity confound.
   - Anchor: `outputs/sm1/design0/g0_3_manifest.json`,
     `g0_3_drain_decomposition.py`.
   - **Anchor note:** G0-3's report body cited fi:1417/1419/1487,
     fi:948, fi:986 for grapple/body/KD spend sites — origin
     unknown; wrong. Every subsequent
     filing in this gate (G0-4 onward, including this checkpoint)
     uses current-HEAD anchors verified at `0ca052c`: fi:1426
     (grapple attempt +5), fi:1428 (grapple failed +3), fi:1496
     (sub failed +6), fi:957 (body shot damage×0.4), fi:995 (KD +8).

  **G0-4 — total-drain wrapper instrument + zero-floor census +
   body_frame consumer grep.**
   - Instrument: log-only wrapper on fe.FighterState.new_round
     (round transitions) + fe.FighterState.spend_stamina (drain
     sites). Discrimination proof on one HH×HH fight seed 1000:
     wrapper R2 total drain 36.25 vs CSS R2 strike drain 8.75 —
     27.5 pts of R2 drain occur BEFORE the first CSS call (grapple
     opening exchanges). Wrapper sees ~2-3× more drain than CSS
     on grapple-heavy rounds.
   - Zero-floor census (2280 fights, initial count later corrected
     to 2100 in G0-4b — see CORRECTIONS #7):
     * HH R1: 65% hit floor 0, median call to first-zero = 23
     * HH R2: 71% hit floor 0, median call = 9
     * HL R1: 53% / 23
     * LH R1: 64% / 24
     * LL R1: 23% / 25 (weakest fighters throw fewer actions →
       don't reach floor as often)
     * R2/R3 for HH/HL/LH: 60-70% of fighter-rounds spend the
       LAST ~46 exchanges at stamina=0.
   - Clamp anchor at fe:611-612: `max(0, self.stamina - amount)`.
     Stamina cannot cross zero; recovery capped at min(100, ·).
   - body_frame grep across fe.py + fi.py + gb.py:
     * fight_engine.py: ZERO hits
     * fight_integration.py: ZERO hits
     * game_bridge.py: hits at 1504 (field def), 7324-7325
       (WebFighter backfill), 19810-19811 (weight-class news),
       19893 (weight-class-move logic)
     **body_frame is NOT a fight-engine consumer. Cut-fighter
     identity confound in G0-3 is not driven by body_frame
     directly.** Initial reading in G0-4 that "R1 refill wipes
     cut/fatigue to 100 for everyone" was overstated — see
     CORRECTIONS #5 and G0-4c Item 4.
   - Anchor: `outputs/sm1/design0/g0_4_manifest.json`,
     `g0_4_total_drain_and_zero_floor.py`.

  **G0-4b — three closures before G0-2 (condition live/dead
   probe + effective-delta ledger + same-fights proof).**
   - CH1 fatigue-refill probe on donor 012d6319 (cardio 91,
     recovery 85), fatigue {0, 50, 100}:
     assemble_ss = 100.00 / 88.00 / 65.00 respectively
     R1 post-new_round stamina = 100.00 in ALL THREE cases
     (recovery 85 refill overshoots any starting deficit → clamp
     100). fi:592 `new_round()` runs unconditionally at R1 with
     no round>1 guard. **G0-1 CH1 verdict corrected: wired to
     constructor, value discarded by R1 refill when recovery is
     sufficient — see CORRECTIONS #1.**
   - Effective-delta ledger + same-fights proof: 2100 fights via
     Tier A verbatim seed scheme. Wrapper N=2100 = Tier A N=2100
     (fixes G0-4's 2280 miscount).
   - Winner agreement wrapper vs Tier A: 92.0% (168 disagreements
     across 2100). Attribution to config + wrappers in G0-4b was
     partial; fully bisected in G0-4c as builder/entry difference,
     not wrapper — see CORRECTIONS #8.
   - Effective-delta ledger showed residuals ranging −0.79 to
     −2.04pt per fighter-round — direction indicates unwrapped
     stamina writes (identified as fi:620-624 fatigue penalty +
     fi:600/610 corner bonus). Fix landed in G0-4d.
   - Anchor: `outputs/sm1/design0/g0_4b_manifest.json`,
     `g0_4b_closures.py`.

  **G0-4c — instrument certification bisect + R1-refill sizing
   baseline.**
   - Bisect (three 2100-fight runs vs gate1_tierA/ CSVs):
     * (a) Tier A verbatim builder+entry, wrappers OFF: winner
       agree 100.0% (2100/2100), method agree 100.0%
     * (b) Tier A verbatim builder+entry, wrappers ON: winner
       agree 100.0% (2100/2100), method agree 100.0%
     * (c) Corrected builder + hardcoded fight dict, wrappers ON:
       winner agree 92.5% (1942/2100), method agree 79.9% (1678/2100)
     Draw-serialization was identified as a comparator artifact
     (Tier A CSV empty-string winner vs my None on Draws); fixed
     in comparator, agreement resolved to 100.0% for (a)+(b).
     **Wrappers RNG-neutral. G0-4b's 8% drift is cause = corrected
     builder + fight-dict weight_class differ from Tier A's
     Lightweight-default builder + `pv15._make_fight_const`.**
   - Ledger residual gate BEFORE _init_round hook: max 4.0, mean
     1.14, 36% of fighter-rounds > 0.01. Attribution: unwrapped
     fi:620-624 fatigue-penalty direct writes to `.stamina`.
   - R1-refill sizing baseline (anchor 290 at fatigue=0):
     * 20 cut fighters differ from assemble_ss (all severity 1;
       assemble ~85-89 → R1 refill boosts to 100 → R1 open ≠
       assemble_ss). Expected.
     * 270 non-cut fighters have R1 open == assemble_ss ==
       100.00. Expected.
     5-fighter recovery spread (rec 33..94) at fatigue=100:
     | fid | rec | cardio | assemble_ss | R1_open | deficit |
     |---|---:|---:|---:|---:|---:|
     | 00090425 | 33 | 33 | 60.00 | 83.25 | 16.75 |
     | c170cb47 | 60 | 85 | 65.00 | 95.00 | 5.00 |
     | 012d6319 | 85 | 91 | 65.00 | 100.00 | 0.00 |
     | 85f73bf3 | 85 | 65 | 60.00 | 96.25 | 3.75 |
     | 119a9190 | 94 | 88 | 65.00 | 100.00 | 0.00 |
     **The condition/cut channel is NOT universally dead. It's
     dead for high-recovery fighters (rec ≥ 80) whose refill
     overshoots 100; it's LIVE with deficits 5-17pts for
     low/mid-recovery fighters at high fatigue.** Overstated
     "R1 wipes everything" from G0-4 corrected — see
     CORRECTIONS #5.
   - Anchor: `outputs/sm1/design0/g0_4c_manifest.json`,
     `g0_4c_instrument_cert.py`.

  **G0-4d — corrected baseline + ledger close.**
   - LEDGER CLOSE (Tier A verbatim, 7276 fighter-rounds):
     max |residual| = 0.000000, mean 0.000000, over-0.01 count 0.
     **GATE PASS.** `_init_round` hook captures fi:620-624
     penalty + fi:600/610 corner writes and updates round-open
     to post-adjustment stamina. Ledger equation `(open−close)
     = (Σspend_eff − Σrecover)` holds to zero on every row.
   - Ran corrected population (via G0-4d Item 2 in-harness
     rerun, N=2100, wall=46.3s per `g0_4d_out.txt`; standalone
     `tierA_corrected_run.py` produced the CSVs at 57.2s wall).
     Ledger also closes to zero on corrected run. Outputs at
     `outputs/sm1/design0/tierA_corrected/`.
   - 2a per-fighter assemble_ss (corrected): 16 at 100.00, 4 in
     [85, 90) (00090425, 074cd4d1, 85f73bf3, a218b4d7), 0 below
     85. Matches world_init.py:2548-2555 arithmetic.
   - 2b CSS P3 side-by-side (corrected vs W2 post-fix). Δ per
     cell all ≤ ±1.4pp:
     | bin | ΔR1 | ΔR2 | ΔR3 |
     |---|---:|---:|---:|
     | HH | +0.69 | +1.38 | +0.61 |
     | HL | +0.47 | −0.39 | −0.39 |
     | LH | +0.56 | +0.41 | +0.76 |
     | LL | −0.40 | −1.17 | −0.24 |
     **W2's P3 trajectory numbers are directionally trustworthy
     at aggregate; magnitude bias from the WC bug is <1.5pp per
     cell.** Individual fight outcomes differ on 168 fights
     (7.5%), but aggregate absorbed the bias.
   - 2c certified ledger table (corrected population, all
     residuals ≈ 0 to two decimals):
     HH R1: open 100.00, close 22.50, drain 77.50
            = strike 64.01 + grapple 27.97 + body 1.14
            + KD 2.60 + other 7.35 (spend total 103.07)
            − regen 25.58 = 77.49 ≈ drain 77.50 ✓
     HL R1: open 100.00, close 35.25, drain 64.75
            = strike 57.23 + grapple 19.30 + body 1.27
            + KD 3.44 + other 7.69 (spend total 88.93)
            − regen 24.18 = 64.75 = drain 64.75 ✓
     LH R1: open 100.00, close 25.04, drain 74.96 ✓
     LL R1: open 99.80, close 57.59, drain 42.21 ✓
     **Regen column ≈ 22-26 pts/round from breath recovery
     (+0.5/exchange × ~45-52 exchanges).**
     LL R1/R2 also carry a small `penalty` column of 0.20
     from the cut fighter 00090425's fi:620-624 fires (see
     G0-2 Item E arithmetic).
   - 2d HH vs HL cut-0 R1 with 2SE:
     * HH cut-0 R1 drain: 78.76 ±2.39, n=870
     * HL cut-0 R1 drain: 70.88 ±2.84, n=768
     * **Δ (HH − HL) = +7.87 ±3.71 (2SE)** — statistically
       significant (|Δ| > 2SE)
     Channel decomposition of +7.87 total-drain gap:
     strike +1.99, **grapple +6.72**, body +0.10, KD −0.59,
     other +0.50. **Grapple channel carries 85% of the
     HH>HL drain gap.** HH fighters grapple more per R1
     (28.02 vs 21.30 pts) — likely correlated wrestling stats
     in the HH bin, not a pure cardio effect.
   - 2e method distribution corrected vs Tier A per pairing
     (details in output). Aggregate 92.5% winner agree, 79.9%
     method — same as G0-4c(c), same population difference.
   - Anchor: `outputs/sm1/design0/g0_4d_manifest.json`,
     `g0_4d_corrected_baseline.py`.

  **G0-2 — cardio consumer map + insertion-point coverage +
   clone-and-vary pilot + LL penalty arithmetic + run(c) identity.**
   - Cardio consumers grep across fe.py + fi.py + gb.py: FIVE
     fight-time live consumers, plus one field def and one OVR-
     derived non-fight-time consumer:
     1. fe:1384 `pressure_score = (cardio+heart+chin)/3` in
        detect_fighter_style — STYLE CLASSIFIER (fight-time)
     2. fe:1453 Clinch Fighter gate
        `if clinch_score ≥ 65 AND cardio ≥ 68 AND wrestling ≥ 58`
        — STYLE CLASSIFIER (fight-time)
     3. fe:2073-2084 late-round `_cardio_gap` multiplier applied
        uniformly to strike/grapple/sub weights — ACTION-SELECT
        (fight-time, int-truncation effective per Gate 0(c) Step
        1c live probe: +7.08pp starved-stamina cell)
     4. fe:2173 IQ body-targeting bonus
        `if fight_iq > 60 AND target == body AND opponent.cardio > 70`
        — STRIKE-SELECT (fight-time)
     5. gb:17064 cut penalty cardio offset
        `_cardio_offset = (cardio - 50) / 200` — STARTING-STAMINA
        (pre-fight, cut-gated)
     Zero .cardio attribute reads in fight_integration.py at
     fight time. **Cardio is NOT a direct input to spend_stamina,
     recover_stamina, new_round refill, STRIKE_PROPERTIES costs,
     or any drain formula.**
   - Insertion-point coverage for a hypothetical future cardio-
     into-drain wire (coverage only, no recommendation):
     * (i) fe:611 `def spend_stamina` — CHOKE POINT, covers
       ALL 13 spend_stamina call sites (6 fe + 7 fi enumerated
       in `g0_2_out.txt`)
     * (ii) fi:1291 strike-cost only — covers 1 of 13 sites (7.7%);
       leaves grapple/body/KD/TD/sub/rocked untouched
     * (iii) fi:1651-52 breath recover — 4 recover sites; NOT a
       spend site (modifies +0.5/exch regen, not drain)
   - Clone-and-vary pilot (donor 012d6319, cardio 30/50/70/90,
     N=200 per level, vs fixed all-75 balanced opponent, certified
     ledger residual 0.0 on every level):
     | cardio | nR1 | R1 open | R1 close ±2SE | R1 drain |
     |---:|---:|---:|---:|---:|
     | 30 | 184 | 100.00 | 5.78 ±2.30 | 94.22 |
     | 50 | 183 | 100.00 | 4.64 ±1.81 | 95.36 |
     | 70 | 169 | 100.00 | 3.25 ±1.62 | 96.75 |
     | 90 | 176 | 100.00 | 2.96 ±1.43 | 97.04 |
     **PILOT IS FLOOR-SATURATED.** Every cardio level closes R1
     at 3-6 out of 100. A drain of 94-97 means "everything the
     fighter had." Differences between levels are inside the
     clip zone and are NOT a mechanism slope. The 2.82pp
     range across cardio 30→90 is a clip-zone artifact, not a
     measured slope. **The pilot proves the instrument RUNS
     (residual 0.0 everywhere); it does NOT prove it
     DISCRIMINATES, because nothing in the current engine can
     move a fighter off the floor.** Design headline number:
     **an elite-cardio (91) elite-recovery (85) fighter vs a
     mediocre opponent who goes the distance is empty after
     R1.** Gate 1 fix: report first-zero call index + requested
     drain per level alongside close — those keep discriminating
     when close cannot.
   - LL R1 penalty arithmetic (fix): 0.20 pt/round in G0-4d
     Item 2c comes from LL cut fighter 00090425 whose
     assemble_ss=85.71 → fi._fatigue_to_penalty(85.71) returns
     1.0 (s≥78 branch fires). Cut fighter appears in ~20% of
     LL R1 slot-events (1 of 5 LL fighters × pairing schedule),
     so mean per LL R1 event = 0.20 × 1.0 = 0.20 pt. Matches
     observed exactly.
   - run(c) identity: G0-4c run(c) ≡ G0-4d Item 2 ≡
     tierA_corrected_run.py. All three use identical builder,
     fight-dict weight_class, seed scheme, and pairing
     schedule; wrappers (CSS pv15 + certified ledger) are
     RNG-neutral per G0-4c Item 1 bisect. Same 2100 fights,
     byte-identical outcomes, differ only in captured
     instrumentation.
   - Anchor: `outputs/sm1/design0/g0_2_manifest.json`,
     `g0_2_cardio_map_and_pilot.py`.

  ═══════════════════════════════════════════════════════════════════
  ## CORRECTIONS

  Standing wrong-numbers rule applied: original text preserved
  at each cited filing; correction annotates. Anchors given by
  grep-locatable identifier rather than line number to survive
  file drift.

  **CORRECTION #1 — G0-1 Channel 1 verdict is refined.**
   - Original claim (grep anchor: "G0-1 Channel 1 verdict"):
     "CHANNEL 1 (starting_stamina from fatigue): WIRED (15/15
     samples match condition module)."
   - Where filed: G0-1 report + inherited into any downstream
     analysis that treated fatigue starting-stamina as
     outcome-affecting.
   - Corrected: WIRED at construction (fi:503-515 post-C8
     RECOVERY-WIRE1 assigns starting_stamina to condition-
     computed value), but VALUE DISCARDED by unconditional R1
     new_round refill IF `assemble_ss + 15 + recovery*0.25 ≥
     100`. Dead for high-recovery fighters at any fatigue; LIVE
     with deficits 5-17pts for low-to-mid-recovery fighters at
     high fatigue.
   - Retired-not-deleted: "WIRED (15/15 samples match)" was a
     correct CONSTRUCTION-layer measurement — kept as such.
     The OUTCOME-layer inference from that measurement is what
     the correction refines.
   - Anchor: G0-4b Item 1 probe; G0-4c Item 4 5-fighter
     recovery spread.

  **CORRECTION #2 — G0-1b population cut-severity histogram.**
   - Original claim (grep anchor: "cut-severity dist" G0-1b):
     "cut ON aggregate mean 89.48; 25/290 at floor 60 exactly;
     severity dist {0:178, 1:35, 2:26, 3:34, 4:17}"; bimodal
     histogram with 178 at [100-105), 50 at [60-65), etc.
   - Where filed: G0-1b manifest + report + any downstream
     analysis citing 8.6% at floor / 17.6% severity ≥ 3.
   - Corrected: cut ON mean 99.15; 0/290 at floor 60; severity
     dist {0: 270, 1: 20, 2+: 0}.
   - **Attribution (stated plainly):**
     `gate1_tierA_run.py`'s `_make_real_fighter` (the source-of-
     truth for the Tier A / W2 / C7 / C8 population) set
     `f.weight_class = fdata.get("weight_class", "Lightweight")`
     — but `fighter_data` doesn't carry `weight_class` (it lives
     on `FighterRecord`). All fighters in that run defaulted to
     "Lightweight". `pv15._make_fight_const` reinforced the same
     default in the fight dict. **Tier A came first (C7);
     G0-1b's harness inherited the same pattern from the Tier A
     harness, and G0-1b's phantom severity 2/3/4 fighters are
     the downstream signature of that inherited pattern applied
     to the whole 290-fighter anchor population.**
   - Retired-not-deleted: G0-1b histogram is preserved as a
     correct measurement of the buggy population. The claim
     "severity 3+ covers 17.6% of the population" is
     population-artifact, not world_init output.
   - Anchor: G0-1c Rider; G0-4c Item 4.

  **CORRECTION #3 — C7 P3 population framing.**
   - Original claim (grep anchor: `**P3 target-trajectory table**
     (report §3)` — verified at CLAUDE.md's C7 filing block,
     currently ~L4890): pre-RECOVERY-WIRE1 P3 table:
     HH R1-end 13.4±27.5 (n=891); HL R1-end 26.1±38.6 (n=812);
     LH R1-end 19.1±33.2 (n=864); LL R1-end 24.9±36.2 (n=360).
   - Where filed: CLAUDE.md C7 filing under
     "**STAMINA-MODEL1 — Gate 1 CLOSED + G1F findings + Q4d
     premise correction [SHIPPED 2026-08-30 as C7 docs
     checkpoint]**".
   - Corrected framing (not corrected numbers): numbers are
     true measurements of the run's population, but that
     population was produced by `gate1_tierA_run.py`'s
     `_make_real_fighter` (Lightweight-default WC bug) +
     `pv15._make_fight_const` (WC always "Lightweight" in fight
     dict). Cut fighter classification and per-fighter cut
     penalties were computed against a Lightweight-defaulted
     population for the whole 20-pool. Direction of HH<HL
     inversion SURVIVES on the corrected population; aggregate
     magnitudes differ by ≤1.4pp per cell (measured G0-4d
     Item 2b Δ table).
   - Retired-not-deleted: the C7 P3 numbers themselves are
     retained as-filed; they measure a population accurately.
     The framing "trajectories with production wiring" is what
     the correction refines to "trajectories with production
     wiring under the `_make_real_fighter` + `_make_fight_const`
     Lightweight-default pattern documented in CORRECTION #2."
   - Anchor: G0-4d Item 2b Δ table; G0-4c Item 1 bisect proving
     wrapper-neutrality + attribution to builder/entry-dict.

  **CORRECTION #4 — C8 W2 before/after P3 population framing.**
   - Original claim (grep anchor: `**P3 target-trajectory table
     (post-fix)**` — verified at CLAUDE.md's C8 filing block,
     currently ~L5185): post-RECOVERY-WIRE1 P3 table:
     HH R1-end 14.9±29.3 (n=894); HL R1-end 26.8±39.0 (n=814);
     LH R1-end 18.5±32.6 (n=861); LL R1-end 24.6±35.6 (n=360).
     Δ (POST − PRE) table also filed (HL R3-end +2.94, etc.).
   - Where filed: CLAUDE.md C8 filing under
     "**STAMINA-MODEL1 — RECOVERY-WIRE1 fix + fixture
     re-baseline [SHIPPED 2026-08-30 as C8 code+docs commit]**".
   - Corrected framing: before/after deltas are correct
     measurements of the RECOVERY-WIRE1 code change; the
     population reference frame is the SAME Tier A population
     produced by `_make_real_fighter` + `_make_fight_const`
     (per CORRECTION #2 attribution). Same-population delta
     remains valid; absolute post-fix trajectory numbers carry
     the same WC-default population bias as C7's pre-fix numbers.
   - Retired-not-deleted: C8 W2 numbers stand as before/after
     evidence of RECOVERY-WIRE1 effect on the shared population.
   - Anchor: G0-4d Item 2b Δ table (corrected vs W2 post-fix,
     |Δ| ≤ 1.4pp per cell).

  **CORRECTION #5 — G0-4 / G0-4b "R1 refill wipes cut/fatigue
   to 100 for everyone" is overstated.**
   - Original claim (grep anchor: G0-4 Item 4b "cut penalty is
     functionally dead"): R1 new_round refill always brings
     stamina to 100, making cut and fatigue starting-stamina
     penalties dormant at fight time.
   - Where filed: G0-4 Item 4b conclusion + G0-4b Item 1
     interpretation.
   - Corrected: R1 refill formula = `min(100, assemble_ss + 15
     + recovery/100 × 25)`. TRUE for fresh-world fighters and
     any fighter whose refill overshoots 100. FALSE for
     exhausted low/mid-recovery fighters. Rec 33 exhausted →
     deficit 17pt. Rec 60 exhausted → deficit 5pt.
   - Retired-not-deleted: original claim is correct for the
     pool fighters G0-4 measured (all fatigue=0). Overstates
     universality.
   - Anchor: G0-4c Item 4 5-fighter recovery spread table.

  **CORRECTION #6 — G0-4 site sum > total_drain accounting bug.**
   - Original claim (grep anchor: G0-4 Item 2 "sum-of-channels
     residual"): per-fighter-round site sums exceed total drain
     by ~35-100pt; attributed to "wasted drain against floor."
   - Where filed: G0-4 Item 2 discussion.
   - Corrected: two accounting bugs stacked:
     (a) In-round `recover_stamina(+0.5)` breath regen (fi:1651-52)
         NOT tracked — injects 22-27 pts per round;
     (b) master site accumulator included drain from rounds
         without close capture (rounds that ended the fight);
         n_events denominator excluded those events → per-event
         mean inflated.
     G0-4c wrapped recover; G0-4d hooked _init_round and
     restricted master to fighter-rounds with both endpoints.
     Residual gate PASS at 0.000000 in G0-4d Item 1.
   - Retired-not-deleted: G0-4 "wasted drain" framing is a
     valid measurement of REQUESTED drain vs ACTUAL drain
     (with the +27pt regen and event-count bias baked in).
   - Anchor: G0-4d Item 1 gate result.

  **CORRECTION #7 — G0-4 fight count 2280 vs Tier A 2100.**
   - Original claim: G0-4 loop reported "total fights: 2280".
   - Corrected: 2,100 fights via Tier A's verbatim seed scheme
     (`pairs[fight_idx % len(pairs)]` cycling). Extra 180
     came from G0-4's alternative pair-first seed distribution.
     G0-4b (and all downstream harnesses) use verbatim scheme
     for 2,100 count matching Tier A.
   - Anchor: G0-4b Item 3 count reconciliation; G0-4c Item 1.

  **CORRECTION #8 — G0-4b "wrappers cause 8% drift" attribution.**
   - Original claim (grep anchor: G0-4b Item 3 "wrappers
     introduce measurable outcome drift"): wrapper run vs Tier
     A showed 92% winner agreement; attributed partially to
     wrappers, partially to P10 config mismatch.
   - Where filed: G0-4b Item 3 discussion.
   - Corrected: WRAPPERS ARE RNG-NEUTRAL. G0-4c bisect: (a)
     verbatim builder+entry, wrappers OFF → 100% agreement;
     (b) verbatim builder+entry, wrappers ON → 100% agreement;
     (c) corrected builder + hardcoded fight dict, wrappers ON
     → 92.5%. The 8% drift comes ENTIRELY from builder/entry
     difference (corrected `weight_class` from FighterRecord;
     hardcoded fight-dict `weight_class` differs from
     `pv15._make_fight_const`'s always-Lightweight).
   - Retired-not-deleted: G0-4b's 92% number is a real
     measurement of run(c)-shape vs Tier A; the attribution
     framing is what corrects.
   - Anchor: G0-4c Item 1 bisect summary.

  **CORRECTION #9 — G0-1 "penalty-4 branch unreachable" claim.**
   - Original claim (grep anchor: G0-1 Item 5 verdict text —
     "unreachable"): fi:432 `return 4.0` branch is unreachable
     because condition.get_starting_stamina floors at 65 (never
     produces s < 65).
   - Where filed: G0-1 report Item 5 conclusion + inherited into
     G0-1 manifest.
   - Corrected: **reachable via cut floor 60.** `gb:17066`'s
     `max(60, ...)` clamp can produce starting_stamina = 60 for
     cut fighters; fi:432 `if s >= 65: return 2.0` fails at
     s=60, so `return 4.0` fires. G0-1c Item 5 measured
     `fi._fatigue_to_penalty(60.0) = 4.0`.
   - Dormancy scope refined: **dormant at fatigue=0** because
     all 20 anchor cut fighters have assemble_ss ≥ 85 (G0-1c
     pool table + G0-4d Item 2a) → fi:427-434 lands in the
     `s ≥ 78 → return 1.0` branch, never the `return 4.0`
     branch. **REACHABLE in live play for cut+exhausted
     fighters:** a severity-1 fighter at high fatigue whose
     condition-derived assemble = 65 further reduced by
     ~12pt cut → floor 60 → fi:432 fires → penalty = 4/round.
     Not exercised in world_init T0 (all fighters fatigue=0),
     LIVE post-fights-accumulate-fatigue for the cut subset.
   - Retired-not-deleted: "unreachable" was source-read reasoning
     that ignored the cut channel — falsified by direct
     measurement in G0-1c/G0-4c.
   - Anchor: G0-1c Item 5 (measurement); G0-4d Item 2a (all 20
     cut fighters ≥ 85 assemble evidence).

  **CORRECTION #10 — C7 P1 composition explanation.**
   - Original claim (grep anchor: `**P1 disposition RESTATED —
     CONFOUNDED-UNRESOLVED (was: refuted by Gate 1 §5).**` —
     verified at CLAUDE.md's C7 filing block, currently ~L4934):
     "The measured HH−HL slope delta (+0.34 pts/exchange in R1)
     originates in strike-selection confounds — HH fighters'
     higher kicks (+15.8) and clinch_striking (+12.4) and
     fight_iq (+14.2) shift their action distribution toward
     different strike TYPES with different `props[2]` costs."
   - Where filed: CLAUDE.md C7 filing under P1 disposition
     restatement.
   - Correction (annotation, not deletion): G0-3 measured
     mean per-strike cost in HH cut-0 R1 slice at 4.81 vs HL
     cut-0 R1 at 4.93 — essentially equal, both bins throw a
     similar per-attempt cost mix. G0-4d Item 2d then located
     85% of the HH>HL total-drain gap (+6.72 of +7.87) in
     **grapple VOLUME**, not strike-type composition. Grapple
     and sub-failed sites drain fixed 5/3/6 pts respectively at
     fi:1426 (grapple attempt +5) / fi:1428 (grapple failed
     extra +3) / fi:1496 (sub failed +6) — no skill input; HH
     fighters attempt more grapples per R1 (28.02 vs 21.30 pts).
   - Retired-not-deleted: C7 P1's "strike-type composition
     explanation" stands as a hypothesis for a small residual
     component. The dominant channel (85% of the gap) is
     measured to be grapple volume, not strike composition. C7
     P1's `props[2]` cost-mix hypothesis is measured-insufficient
     as the primary mechanism.
   - Anchor: G0-3 (mean_cost per bin/slice); G0-4d Item 2d
     (channel decomposition).

  **CORRECTION #11 — G0-1c HH−HL cut-0 re-slice population
   annotation.**
   - Original claim (this filing, MEASUREMENTS/G0-1c bullet):
     the −11.88 (ALL slice) and −9.01 (CUT-0 slice) R1-end
     inversion figures.
   - Where filed: G0-1c report Item 2 + inherited framing.
   - Correction: those figures were computed by re-slicing the
     PRE-CORRECTION Tier A landing CSVs at `gate1_tierA/`
     (produced by `gate1_tierA_run.py` under the WC-default
     builder). The "cut-0" filter used `_make_correct_fighter`'s
     natural/wc classification, but the FIGHTS themselves were
     the WC-default-population runs. Cut classification and
     underlying sim outcomes are from two different populations
     for that measurement.
   - Corrected version: G0-4d Item 2d computes HH cut-0 R1
     drain 78.76 ±2.39 vs HL cut-0 R1 drain 70.88 ±2.84 →
     **Δ = +7.87 ±3.71 (2SE)** on the CERTIFIED corrected
     population. Direction survives; the total-drain axis (not
     the CSS-last_ss axis of G0-1c) is the certified basis.
   - Retired-not-deleted: G0-1c's numbers stand as evidence the
     HH<HL inversion is present under a mixed-population filter;
     the certified magnitude is G0-4d Item 2d.
   - Anchor: G0-4d Item 2d.

  ═══════════════════════════════════════════════════════════════════
  ## DESIGN INPUTS (facts only, no recommendations)

  Numbers arithmetic-consistent within each row. Every figure
  cites the manifest that produced it.

  **1. TANK-VS-BILL ARITHMETIC (corrected population, ledger
  residual 0.000000; source: g0_4d_manifest.json for effective,
  g0_4b_manifest.json for requested).**
   - R1 income = 100.0 (fresh start; refill formula caps at 100
     for pool fighters at fatigue=0).
   - R1 in-round regen (breath +0.5/exch): **22-26 pts** across
     bins (EFFECTIVE, ledger-captured).
   - R1 spend REQUESTED (all channels sum, uncapped by floor;
     source: G0-4b Item 2 uncapped ledger): **175-215 pts**
     across HH/HL/LH bins depending on cell; LL requested ~88
     (fewer actions).
   - R1 spend EFFECTIVE (post-floor, ledger-captured; source:
     G0-4d Item 2c): **88.9-104.5 pts** across HH/HL/LH bins;
     LL effective ~63.
   - REQUESTED − EFFECTIVE gap ≈ 86-110 pts per fighter-round
     for HH/HL/LH R1 → the engine's action-select formula wants
     to drain 2-2.4× more than the fighter has to give. That gap
     is "wasted drain" against `fe:611-612`'s `max(0, ...)` floor.
   - R1 net drain (open − close): 42-77.5 depending on bin.
   - Endpoint identity holds: **open − close = spend_effective −
     recover, per fighter-round, to zero.** (Requested does NOT
     appear in the identity because floor-clipped calls don't
     move stamina.)

  **2. ZERO-FLOOR CENSUS (corrected population; source:
  g0_4d_manifest.json).**
   | bin | R | nEv | n_zero | frac | median call at first-zero |
   |---|---:|---:|---:|---:|---:|
   | HH | 1 | 1079 | 747 | 69.2% | 23 |
   | HH | 2 | 760 | 569 | 74.9% | 10 |
   | HL | 1 | 963 | 524 | 54.4% | 23 |
   | HL | 2 | 817 | 508 | 62.2% | 9 |
   | LH | 1 | 945 | 627 | 66.3% | 24 |
   | LH | 2 | 760 | 573 | 75.4% | 8 |
   | LL | 1 | 959 | 236 | 24.6% | 25 |
   | LL | 2 | 825 | 325 | 39.4% | 8 |
   By R2, ≥60% of HH/HL/LH fighter-rounds spend the last ~46
   exchanges at stamina=0. LL fighters throw less, drain
   less, hit floor less. Clamp at fe:611-612 `max(0, ...)`.

  **3. THREE STAMINA CHANNELS. CARDIO IN NONE.**
   - DRAIN channel: 13 `spend_stamina(...)` call sites (6 fe
     + 7 fi enumerated in g0_2_out.txt Item C). All route
     through fe:611 `def spend_stamina`. Amounts are literals
     (2-12 per strike via STRIKE_PROPERTIES[k][2]; fixed
     3-8 for grapple/sub/KD/TD; damage×0.4 for body-shot;
     aggression multiplier [0.85, 1.15] dormant when
     gameplan=BALANCED). **No cardio input at any drain site.**
   - BETWEEN-ROUND channel: fe:614-631 `def new_round`.
     Formula: `stamina = min(100, stamina + 15 + recovery/100
     × 25)` with ×1.3 championship bonus at round ≥ 4. **Reads
     recovery, not cardio.**
   - IN-ROUND REGEN channel: fi:1651-1652
     `recover_stamina(0.5)` both fighters, unconditional
     per-exchange. **Flat 0.5 constant; no cardio input.**

  **4. R1 REFILL RECOVERY-GATED ERASURE (source: g0_4c manifest,
  5-fighter table).**
   | fatigue | recovery | assemble_ss | R1_open | deficit |
   |---:|---:|---:|---:|---:|
   | 100 | 33 | 60.00 | 83.25 | 16.75 |
   | 100 | 60 | 65.00 | 95.00 | 5.00 |
   | 100 | 85 | 65.00 | 100.00 | 0.00 |
   | 100 | 94 | 65.00 | 100.00 | 0.00 |
   Any fatigue-cut deficit gets erased when `assemble_ss + 15 +
   recovery×0.25 ≥ 100`. Rec ≥ 80 → always erased regardless of
   starting deficit. Rec ≤ 50 → deficit persists.

  **5. CUT / FATIGUE FUNCTIONAL STATUS.**
   - CUT (gb:17064 offset formula): FIRES pre-fight; produces
     4-14pt starting-stamina reduction on ~7% of world_init
     population (20/290 anchor, all severity=1). **Always erased
     at R1 for cut-only fighters (fatigue=0) under current
     world_init output:** world_init.py:2548-2555 produces
     severity ≤ 1, so cut-only assemble_ss ≥ ~86 (severity 1
     max ~14pt reduction on age-adjusted formula). Minimum
     refill = 15 + recovery×0.25 = 15 + 8.25 = 23.25 (at rec 33,
     the floor recovery in the world-gen distribution). 86 +
     23.25 = 109.25 > 100 → clamp fires → R1 open = 100 for
     every cut-only fighter regardless of recovery. **CUT IS
     LIVE ONLY STACKED ON FATIGUE:** a cut+fatigued fighter
     whose assemble_ss lands below `100 − 15 − recovery×0.25`
     carries a deficit at R1 open. Not exercised in world_init
     T0 (all fighters fatigue=0).
   - FATIGUE (condition.get_starting_stamina): DORMANT in
     fresh worlds — every AI at fatigue=0. LIVE mechanism
     available: post-fight fatigue accumulation would produce
     R1 deficits per the recovery-gated table (DESIGN INPUTS #4)
     for low-to-mid-recovery fighters. Not exercised in
     world_init T0.
   - fi:427-434 inline `_fatigue_to_penalty` fires 0-4pt
     subtraction at every _init_round when
     `_fatigue_penalty_f{1,2}` is set. Half-strength vs
     condition module's intended table (READY 0 vs cond 1,
     TIRED 1 vs cond 2, EXHAUSTED 2 vs cond 4). LIVE effect
     magnitude: ≤4pt per round per fighter for cut/fatigued
     fighters at assemble_ss<95.

  **6. GRAPPLE SHARE OF THE HH−HL R1 DRAIN GAP (source:
  g0_4d Item 2d, corrected population).**
   - HH cut-0 R1 drain: 78.76 ±2.39 (2SE), n=870
   - HL cut-0 R1 drain: 70.88 ±2.84 (2SE), n=768
   - Δ (HH − HL) = +7.87 ±3.71 (statistically significant,
     |Δ| > 2SE)
   - Channel decomposition of +7.87 gap:
     * strike: +1.99
     * **grapple: +6.72 (85% of the gap)**
     * body: +0.10
     * KD: −0.59
     * other: +0.50
   HH fighters grapple more per R1 (28.02 vs 21.30 pts),
   correlated with high wrestling stats in HH-bin construction.
   A drain-side fix touching only strike cost would leave 85%
   of the gap intact.

  **7. FIVE CARDIO CONSUMERS AT FIGHT TIME (source:
  g0_2_manifest.json).**
   1. fe:1384 pressure_score = (cardio+heart+chin)/3 — style
      classifier
   2. fe:1453 Clinch Fighter gate (cardio ≥ 68 required) —
      style classifier
   3. fe:2073-2084 late-round cardio_gap multiplier applied
      uniformly to strike/grapple/sub weights — action-select
      (int-truncation effective; +7.08pp starved-stamina cell
      per Gate 0(c) Step 1c)
   4. fe:2173 IQ body-target bonus (opponent.cardio > 70) —
      strike-select
   5. gb:17064 cut penalty cardio offset — pre-fight,
      cut-gated
   None of the 5 reach a `spend_stamina`, `recover_stamina`, or
   `new_round` call.

  **8. PILOT FLOOR-SATURATION NOTE.**
   Cardio 30/50/70/90 pilot (donor 012d6319, N=200/level, ledger
   residual 0.0) produced R1 close of 5.78 / 4.64 / 3.25 / 2.96
   respectively. All four levels sit inside the [0, ~6] clip
   zone at fe:611-612's `max(0, ...)` floor. The 2.82pp
   apparent range is NOT a slope — it's what remains uncrossed
   in the clip zone. **Instrument runs (residual 0.0);
   instrument does NOT discriminate cardio effects today because
   no engine channel can move a fighter off the floor.** Gate 1
   fix: report first-zero call index + requested drain per level
   alongside close — those keep discriminating in the clip zone.
   **Design headline from the pilot: an elite-cardio (91) elite-
   recovery (85) fighter vs a mediocre opponent who goes the
   distance is empty after one round.**

  ═══════════════════════════════════════════════════════════════════
  ## QUEUE

  **R1-REFILL1** — single-purpose fix arc. **Defect:** fi:592
  `new_round()` fires at R1 entry unconditionally (per G0-4b
  Item 1 source read + measured triple 100/88/65 → all post-
  new_round 100). The construction-layer wiring of
  starting_stamina (fi:503-515) is discarded at R1 for any
  fighter whose refill overshoots 100. Per G0-4c Item 4, this
  erases cut penalty and any fatigue deficit up to `100 − 15 −
  recovery×0.25`. **Before-baseline:** G0-4c Item 4 five-fighter
  recovery-spread table (rec 33/60/85/85/94, fatigue=100,
  deficit 16.75/5.00/0.00/3.75/0.00 respectively) is the anchor
  post-fix regressions verify against. **Mechanism deferred to
  spec:** cap-refill-at-starting_stamina, skip-refill-at-R1,
  gate-refill-on-current_round>1, and other candidates are all
  distinct fixes with different side effects. Not chosen here.
  Ship discipline: single-purpose commit, own gate (rerun G0-4c
  Item 4 probe post-fix and confirm the deficit column moves per
  whichever mechanism the ratified spec adopts).

  **Design Gate 1 instrument** — clone-and-vary as in G0-2 Item
  D, with the following required additions per the floor-
  saturation finding:
   1. Report `first_zero_call_index` per cardio level (median,
      p25, p75). Keeps discriminating when close is clipped.
   2. Report `requested_drain` sum per cardio level (uncapped
      by floor). Cardio-into-drain wire will move requested
      drain before it moves close.
   3. Report `regen_total` per cardio level. If regen channel is
      chosen, it moves regen; if drain channel is chosen, it
      leaves regen constant.
   4. STYLE-PIN INSPECTION (see below): confirm whether the
      engine supports pinning fighting_style to bypass
      detect_fighter_style. If not, Gate 1 must control for
      style-classifier confounds via holding all inputs to
      pressure_score + clinch_score + cardio thresholds constant
      alongside cardio itself.

  **STYLE-PIN CHECK — answered by source read + measured pair.**
   Source (fe:1372-1503):
   - `detect_fighter_style` at fe:1372 reads `fighter.fighting_style`
     at fe:1394-1414 as `_hint` via `_HINT_MAP`.
   - `_hint` is used ONLY at fe:1501-1502 as a LAST-RESORT
     fallback (`if _hint: return _hint`) that fires ONLY when
     no primary check (fe:1416-1478) AND no secondary check
     (fe:1482-1497) fires.
   - Primary/secondary checks are pure stat-threshold gates —
     they do NOT consult fighter.fighting_style.
   Measured pair (this checkpoint):
   - Strong-wrestler fighter (takedowns=80, top_control=75,
     others=60):
     * fighting_style=None       → detect returns "wrestler"
     * fighting_style=BJJ_SPECIALIST → detect returns "wrestler"
     * fighting_style=MUAY_THAI  → detect returns "wrestler"
     Hint IGNORED when stats trigger.
   - Weak fighter (all attributes=55):
     * fighting_style=None       → detect returns "balanced"
     * fighting_style=BJJ_SPECIALIST → detect returns "bjj"
     Hint FIRES only in the fallback case.
   Verdict: **fighting_style CANNOT PIN style at fight-time.**
   Setting the attribute only routes borderline fighters (those
   who miss every threshold) to a specific fallback. Any
   Gate 1 clone-and-vary that sweeps cardio across the
   fe:1453 threshold (cardio ≥ 68) will produce a style-tag
   flip regardless of the fighting_style attribute. The style
   confound cannot be pinned via the existing engine API.
   Alternatives for Gate 1: (a) hold cardio in a range that
   doesn't cross fe:1453 (e.g. sweep 30-65 only, or 68-99 only),
   (b) hold clinch_score OR wrestling_score below the Clinch
   Fighter gate's threshold to prevent triggering regardless of
   cardio, (c) accept the style-classifier confound and control
   for it via post-run style-tag inspection (extra column in
   the ledger). Not part of Gate 0 scope.

  ═══════════════════════════════════════════════════════════════════

  Gate 0 CLOSED as measurement pass. Design phase begins at
  Van's ruling; **design decisions pending Van's rulings; nothing
  in this filing is a lever decision.** The CLAUDE.md filing is
  measurement + corrections + design inputs. Lever decisions
  (drain-side yes/no, insertion point, R1-REFILL1 mechanism,
  regen policy, floor policy, deploy queue) live in the ship
  filings that follow this checkpoint.

- **PREGEN-ROUND-WIRE1 [SHIPPED 2026-08-31 as C10 engine+docs commit;
  single-purpose fix, Van-ratified spec + mechanism confirmation;
  first of two commits landing R1-REFILL1 (Commit B follows)].**

  Fixes the pre-gen missing-propagation defect diagnosed at Gate 0
  D3/D5: `fe.simulate_fight` at fe:4111 calls `fight_state.new_round()`
  which at fe:769-782 calls `self.fighter1.new_round() /
  self.fighter2.new_round()` — but `_current_round` was NEVER set on
  those FighterState objects in the pre-gen path (unset across 6
  events in D3 probe; probe read −1 via its own `getattr` fallback,
  engine fallback at fe:628 evaluates 0). Live-play (fi._init_round)
  sets `_current_round` correctly before its new_round calls; pre-gen
  didn't. Fix adds 2 propagation lines + 1 comment in
  `FightState.new_round`.

  **DIFF (single tracked file, `cage_dynasty_web/fight_engine.py`):**
  +3/−0 exactly as declared pre-edit.

  ```
  @@ -774,6 +774,9 @@ class FightState:
           self.ground_inactivity = 0
           self.dominant_control_duration = 0
           self.submission_active = False
  +        # PREGEN-ROUND-WIRE1: propagate round to fighters (live path sets this in fi._init_round)
  +        self.fighter1._current_round = self.current_round
  +        self.fighter2._current_round = self.current_round
           self.fighter1.new_round()
           self.fighter2.new_round()
  ```

  **MECHANISM.** In `FightState.new_round`, set
  `fighter1._current_round = self.current_round` and same for
  `fighter2` immediately before their `new_round()` calls. That is
  the only change. All other side effects preserved. Live-play path
  (fi._init_round) unchanged — it bypasses FightState.new_round per
  D5 caller census and continues to set `_current_round` at
  fi:590-591 as before. CLI parallel copy `systems/fight_engine.py`
  (dead-in-runtime per PREGEN-FULL-ENGINE-FIX1 sys.path shim) not
  touched.

  **GATES A1-A6 (all MEASURED, artifacts under
  `outputs/sm1/r1refill1/`).**

  - **A1 propagation lands** — PASS. Original A1 seed=2000 ended R4
    KO (each fighter saw sequence 1..4, missed R5 in the championship-
    bonus domain). A1 rerun with seed=1003 (first sweep hit that
    goes 5R Unanimous Decision post-fix; D5's original seed=1000
    now ends R4 TKO post-fix due to championship-bonus outcome drift)
    observed the full 1..5 sequence for each fighter across 10
    events. R4 F1 (rec 85) refill = +42.62 (matches 15+85/100*25*1.3);
    R5 F2 (rec 70) refill = +37.75 (matches 15+70/100*25*1.3).
    Both ×1.3 activations directly measured.
  - **A2 pre-gen 3R identical** — PASS. N=200 pre-gen 3R fights,
    same seeds base=3000, before/after: **200/200 winner AND method
    identical.** Championship-bonus `>= 4` gate never fires in 3R,
    so refill formula produces byte-identical output regardless of
    propagation.
  - **A3 pre-gen 5R drift expected** — measured. N=200 pre-gen 5R
    fights, same seeds base=5000: 177/200 winner match (23 flipped),
    140/200 method match (60 flipped). Refill delta measurement on
    seed=4000 shows R4 F1 (rec 85) refill went from +36.25 to +42.62
    post-fix (+6.37 pt championship ×1.3 activation). Cascades into
    subsequent action-select/landing/damage formulas → outcome drift.
    **EXPECTED — this is the pre-gen championship-bonus dormancy
    closing.** Same C7 P2 family (pre-gen/live-play physics split).
  - **A4 Tier A-corrected live 100% identical** — PASS. 2100 fights
    via Tier A-corrected schedule (pool from
    `gate1_step3_pool_manifest_R2.json`, seed scheme verbatim per
    gate1_tierA_run.py), before/after: **2100/2100 winner AND method
    identical.** Wall: before 40.2s, after 40.2s. Mechanically
    guaranteed — fi._init_round bypasses FightState.new_round.
  - **A5 7 fixture hashes vs C8 baseline** — PASS. All 7 raw + norm
    hashes byte-match filed C8 baseline. First-run failed because cc
    invented a custom hasher instead of using pv15's
    `_hash_outcome_rows` / `_hash_normalized_rows`; A5 redo used
    pv15's own functions and all 7 arms matched. Instrument-artifact
    caught pre-report. First-run output preserved at
    `commitA_gates_out.txt`; certified result at
    `commitA_gate_A5_redo_out.txt`.
  - **A6 tree** — PASS. `git diff --stat`: 1 file changed
    (`cage_dynasty_web/fight_engine.py`), 3 insertions, 0 deletions.
    Porcelain otherwise `??` only (untracked outputs).

  **CHAMPIONSHIP-BONUS DORMANCY CLOSED (side effect, filed).** The
  fe:628 branch `if getattr(self, '_current_round', 0) >= 4:
  bonus_recovery *= 1.3` has been dormant in pre-gen since inception:
  `_current_round` was never set on FighterState in the fe path, so
  the getattr fallback returned 0, always failing the `>= 4` gate.
  Post-Commit-A, pre-gen R4/R5 refills activate the ×1.3 bonus (F1
  rec 85: 36.25 → 42.62 per round; F2 rec 70 already clamps to 100).
  Same class as C7 P2 (RECOVERY-WIRE1's pre-gen/live-play split);
  this closes the ×1.3 half. Live-play was already correct via
  fi:590-591.

  **QUEUE.** Commit B (R1-REFILL1) is next — wraps
  `FighterState.new_round`'s stamina refill block in `if getattr(self,
  '_current_round', 0) != 1:` guard. Depends on this commit's
  propagation to fire correctly in pre-gen. Gates W1-W7 declared in
  the R1-REFILL1 spec. Commit A ships alone first per Van's
  ratification.

- **R1-REFILL1 [SHIPPED 2026-08-31 as C11 engine+docs commit;
  single-purpose fix, Van-ratified spec + mechanism confirmation;
  second of two commits landing R1-REFILL1 (Commit A = PREGEN-ROUND-
  WIRE1 = C10 precedes)].**

  Fixes the R1 refill-at-fight-start defect diagnosed at Gate 0
  D1/D2/G0-4b Item 1: `FighterState.new_round` at fe:614-639
  unconditionally refilled stamina every round including R1, erasing
  condition-derived starting_stamina (cut penalty, fatigue). Fix
  wraps the refill block in `if getattr(self, '_current_round', 0)
  != 1:` guard. All other side effects (KD reset, is_knocked_down
  clear, health regen, is_rocked clear, rock_duration reset) fire
  unguarded every round. `!= 1` chosen over `>= 2` so any caller
  that doesn't propagate `_current_round` (default 0) still triggers
  the refill — protects against future unwrapped call sites.

  **DIFF (single tracked file, `cage_dynasty_web/fight_engine.py`):**
  +13/−8 exactly as declared pre-edit.

  ```
  @@ -621,14 +621,19 @@ class FighterState:
           # Bonus: scales 0-25 with recovery stat (was 0-10)
           # Elite (90+) gets back ~40 stamina between rounds;
           # poor (40-) gets back ~18.
  -        base_recovery = 15
  -        _rec = self.recovery_rating
  -        bonus_recovery = (_rec / 100) * 25
  -        # Championship round bonus — adrenaline in late rounds
  -        if getattr(self, '_current_round', 0) >= 4:
  -            bonus_recovery *= 1.3
  -        self.stamina = min(100,
  -            self.stamina + base_recovery + bonus_recovery)
  +        # R1-REFILL1: skip refill at R1 to preserve condition-derived
  +        # starting_stamina (cut/fatigue). `!= 1` means unset
  +        # _current_round (default 0) still refills — protects any
  +        # caller that doesn't propagate round explicitly.
  +        if getattr(self, '_current_round', 0) != 1:
  +            base_recovery = 15
  +            _rec = self.recovery_rating
  +            bonus_recovery = (_rec / 100) * 25
  +            # Championship round bonus — adrenaline in late rounds
  +            if getattr(self, '_current_round', 0) >= 4:
  +                bonus_recovery *= 1.3
  +            self.stamina = min(100,
  +                self.stamina + base_recovery + bonus_recovery)
  ```

  **GATES W1-W7 (all MEASURED, artifacts under
  `outputs/sm1/r1refill1/`).**

  - **W1 origin** — PASS.
    * W1a: 5-fighter recovery-spread table at fatigue=100. Live-path
      assemble_ss pattern **60/65/65/60/65** (cut fighters 00090425
      and 85f73bf3 clamp to 60 via gb:17066 `max(60, ...)` floor;
      non-cut land at 65 per condition table exhausted bucket).
      R1_open == assemble_ss for all five (deficit=0.00 across all).
      Compare G0-4c Item 4 pre-fix table (deficits 16.75, 5.00,
      0.00, 3.75, 0.00 respectively) — that erasure gap is closed.
      W4 (pre-gen path) reads 65 for all five including the cut
      fighters because fe.simulate_fight applies no cut penalty
      (Gate 0 Item 4a: zero cut-related hits in fight_engine.py) —
      pre-gen/live-play cut split remains a known filing.
    * W1b: anchor world `gate1_mw_1_1788106887` at fatigue=0, 290
      fighters probed: 270 non-cut open at 100.00, 20 cut open at
      their assemble_ss (85-89). Zero deviations.
  - **W2 equivalence (split)** — **NO-CUT PASS**, cut drift expected.
    2100-fight Tier A-corrected schedule (same pool, same seeds)
    post-fix vs `outputs/sm1/design0/tierA_corrected/` pre-fix
    baseline:
    * **NO cut in either slot (n=1308): 1308/1308 winner AND 1308/
      1308 method identical.** STOP condition satisfied.
    * ≥1 cut in slot (n=792): 677/792 winner (85.5%), 472/792
      method (59.6%). 115 winner-flips, 320 method-flips. Drift
      EXPECTED — cut fighters now enter R1 at their assemble_ss.
    * Cut-fighter R1 open/close from ledger (post-fix means), with
      84.71 explanation:
      | fid | nR1 | R1 open | R1 close | assemble_ss | fi:427-434 penalty |
      |---|---:|---:|---:|---:|---:|
      | 00090425 | 193 | **84.71** | 57.89 | 85.71 | **1.0 (s≥78)** |
      | 074cd4d1 | 215 | 88.66 | 27.15 | 88.66 | 0.0 (s≥88) |
      | 85f73bf3 | 195 | 88.75 | 57.41 | 88.75 | 0.0 (s≥88) |
      | a218b4d7 | 191 | 89.39 | 38.43 | 89.39 | 0.0 (s≥88) |
      The 84.71 vs 85.71 gap on 00090425: ledger captures R1 open
      POST fi:620-624 penalty subtraction. 00090425's assemble_ss =
      85.71 → `fi._fatigue_to_penalty(85.71)` returns 1.0 (falls
      into `s ≥ 78` branch, since 85.71 < 88). 85.71 − 1.0 = 84.71.
      Other three: assemble_ss ≥ 88 → penalty 0 → open = assemble
      exactly.
      **Pre-fix direct evidence: G0-4 Item 4b** showed every slice's
      R1 open mean = 100.00 INCLUDING the CUT slice — cut fighters
      entered R1 at 100 pre-fix. Post-fix: 84.71-89.39.
    * **Cut-fighter direction (per-fighter + aggregate, 792 cut
      fights):**
      | fid | fights | Δwin% | ΔKO/TKO-loss% |
      |---|---:|---:|---:|
      | 00090425 | 200 | +1.5pp | −2.5pp |
      | 074cd4d1 | 240 | −1.7pp | +1.2pp |
      | 85f73bf3 | 200 | +2.0pp | −3.0pp |
      | a218b4d7 | 200 | −1.0pp | +4.0pp |
      Aggregate (all 4 pooled cut-side, 840 fighter-fights, 48
      double-counted from cross-cell both-cut pairings):
      **Δwin% = +0.1pp**, **ΔKO/TKO-loss% = +0.0pp**. **No systemic
      direction observed on the current 4-fighter pool** (all sev=1,
      ages 27-32, recovery 33-88). Individual variance ±3pp reads
      as seed-cascade noise. Broader-population direction claim
      deferred.
  - **W3 fixture** — PASS. All 7 v1.5 arms N=2000, pv15's own
    `_hash_outcome_rows` + `_hash_normalized_rows`. All 7 raw +
    7 norm hashes match C8 baseline byte-for-byte. Probe sha256
    unchanged: `3ca1f644828c1277f7118229f2438235c6ead51a2e81431a8e08ed0669b88a52`.
    Fixture fighters have `weight_class == natural_weight_class`
    (Lightweight both) and fatigue=0 → assemble_ss = 100 → refill
    formula produces `min(100, 100 + 15 + rec*0.25) = 100` with
    or without the R1 skip. Wall 228.6s. Used pv15's own hashers
    per A5 lesson.
  - **W4 pre-gen** — PASS. 5-fighter recovery-spread via
    `fe.simulate_fight`, fatigue=100: R1_open == assemble_ss
    (65.00) for all 5. Pre-gen path now honors starting_stamina
    at R1 open. Depends on Commit A's `_current_round`
    propagation in FightState.new_round.
  - **W5 ledger** — PASS. 7,204 fighter-rounds captured on W2
    rerun; max |residual| = 7.1e-14 (floating-point noise);
    mean = 0.
  - **W6 tree** — PASS. `git diff --stat`: 1 file changed
    (`cage_dynasty_web/fight_engine.py`), 13 insertions, 8
    deletions. Porcelain otherwise `??` only.
  - **W7 pre-gen 103 exposure** — measured.
    * R1 open (post-refill-guard): **103.00** (matches fe:4023-4043
      peak-condition branch for fatigue ≤ 10).
    * Max stamina at any event in R1: **103.00** (only the initial
      new_round_post value; every subsequent touch either reduces
      it or triggers the clamp).
    * **Does fe:3813/3814 recover_stamina fire in pre-gen? YES
      (measured, 55 calls per fight for the W7 donor).** Line-
      anchor note: this is the same code G0-2 called "fe:3805/3806";
      Commits A (+3 lines around fe:774) + B (+5 net lines around
      fe:614) shifted subsequent lines by +8. G0-2's "dead on
      live-play" claim (fi bypasses fe.simulate_exchange) is
      unchanged; the site DOES fire in pre-gen.
    * **Exposure window:** bounded to the interval between R1
      open and the first spend_stamina or recover_stamina call
      on the pre-gen path, whichever fires first. Typically a
      single-exchange window per fighter per fight for pre-gen
      fatigue-≤10 fighters.
    * Consumer census (grep-verified pre-W7, unchanged post-W7):
      * Category A (`min(100, ·)` clamps at fe:609, fe:630, fi:600,
        fi:610): SAFE, clamp 103 → 100 on first fire.
      * Category B (`stamina / 100` factors at 11 sites: fe:2112,
        2366, 2367, 2470, 2684, 2685, 3001, 3002, 3081, 3100,
        3121): 1-3% lift for exchanges before first clamp. Time-
        bounded by the exposure window above.
      * Category D (strict `> 100` or `== 100` branches): NONE. No
        crash path.
    * **PREGEN-PEAK103 remains queued as follow-up** — 4 candidate
      fixes (i-iv) named in prior spec, chosen in its own arc.
      W7 measurement above is the before-baseline that fix will
      be gated against.

  **CONSEQUENCES FILED (not gated).**
  1. **Cut-fighter R1 stamina is now visible in-fight for the first
     time.** 4 fighters in the current pool with severity=1 enter
     R1 at ~85-89 (their assemble_ss) instead of 100. Cut penalty
     is now a live outcome-affecting mechanism instead of a
     construction-only stat.
  2. **Fatigue channel is now LIVE for any fighter with
     `assemble_ss < 100 − 15 − recovery×0.25`.** In world_init T0,
     all fighters have fatigue=0 → no deficit. As post-fight fatigue
     accumulates, low-recovery fighters develop R1 deficits per
     G0-4c Item 4 arithmetic. **Whether fatigue actually accumulates
     in live play across weeks is an open owed measurement**, not
     investigated in this arc. Filed for the next stamina-arc
     ship.
  3. **Live-play championship ×1.3 R4/R5 was already correctly
     wired** (fi:590-591 sets `_current_round`). C10 closed the
     pre-gen leg. This commit doesn't affect either.
  4. **Floor-interaction: C9 CORRECTION #9's "reachable via cut
     floor 60, dormant at fatigue=0" branch is now LIVE for the
     cut+exhausted subset.** An exhausted cut fighter's assemble_ss
     clamps to 60 at gb:17066 (`max(60, ...)`); post-B, R1 opens
     at 60 (no more refill overshoot); fi:620-624 immediately
     subtracts fi:427-434's penalty per its inline table, and
     `fi._fatigue_to_penalty(60.0) = 4.0` (falls into the `else:
     return 4.0` branch, s<65). R1 open post-init_round = 56 for
     that subset. Not observed in current world_init T0 (all
     fighters fatigue=0 → no exhausted cut fighters in the anchor
     pool), but the exact fighter class C9 CORRECTION #9 predicted
     would activate is now measurable the moment any fighter
     accumulates enough fatigue while carrying a cut.

  **QUEUE.** PREGEN-PEAK103 (single-purpose follow-up, own spec
  per prior message). Fatigue-accumulation-in-live-play measurement
  (owed, unscheduled). Design phase for cardio-into-drain resumes
  post-C11 per Van's rulings.

- **STAMINA-DRAIN1 [SHIPPED as C12 engine + C13 docs, split commits,
      2026-09-01. C12 ships the FULL cardio-scaled drain wire — the
      `cardio_rating` field on `FighterState`, the multiplier body in
      `spend_stamina`, four constructor kwargs at `fe.simulate_fight`
      and `fi.NarratedFightSimulator._init_fight`, and the module-level
      constants `DRAIN_SCALE_K=0.6, DRAIN_CARDIO_S=0.5`. NOTHING from
      Gate 1a was ever committed; the identity-value working-tree edit
      that sat in the tree from Gate 1a through Gate 1c is part of this
      C12 ship, at B9-ratified constants.]**

  Fixes the flat drain physics diagnosed across STAMINA-MODEL1 Gate 0 →
  Design Gate 0 → Design Gate 1a/1b/1c. B7 donor pool + POP-POOL1
  stratified sample + tierA_corrected_c11 re-vintage established the
  measurement surface; Gate 1b frontier + B8-a discrimination-criterion
  amendment + Gate 1c file-constants certification chose (K=0.6, S=0.5)
  from the K∈{0.5,0.6,0.7,0.8,1.0}×S∈{0.3,0.5,0.7} bounded search.

  **Design ratifications (B1-B9 arc, each dated separately):**
  - **Signal 1 (scope), 2026-09-01** — spec + B2 (defender-side scaling
    KEPT) ratified together as the original scope of STAMINA-DRAIN1.
  - **B7 (2026-09-01)** — donor recipe substitution heart=50, chin=50
    (mid-Gate-1a rulingafter the original heart=60/chin=60 recipe
    tripped the style-tag gate at cardio=90 pressure_fighter boundary).
  - **B8 (2026-09-01)** — frontier rerun scope on POP-POOL1 after the
    cardio-distribution measurement discovered Tier A pool cardio-
    skewed +18pp vs world-gen population median.
  - **B8-a (2026-09-01)** — discrimination-criterion amendment
    (majority R1 fighter-rounds hit floor, median R1 close = floor)
    after POP-POOL1 at IDENTITY missed Van's Gate-0-shape band by
    0.02pp — the band was a Tier-A-pool statistic, not a world constant.
  - **Signal 2 (constants), 2026-09-01 (= B9)** — K=0.6, S=0.5 chosen
    from the POP-POOL1 frontier report over K=0.5/S=0.5 because T3
    (population health) is the load-bearing gate; T1 partial pass at
    K=0.6/S=0.5 (R1 39.8 passes, R3 14.3 fails, owed to lever two).

  **DIFF (two tracked engine files, whole-arc vs C11 = R1-REFILL1 at
  HEAD `71e94de`):** `cage_dynasty_web/fight_engine.py` +20/−4,
  `cage_dynasty_web/fight_integration.py` +2/−0. Shape:

  - **Module-level Hunk A** (`fe.py` above the FighterState class): two
    new constants `DRAIN_SCALE_K = 0.6` and `DRAIN_CARDIO_S = 0.5`
    with the equation comment naming the multiplier.
  - **`FighterState` field** (`fe.py`): new `cardio_rating: int = 60`
    (default 60 → g=1 at any S → fail-open, class default matches
    C11's `!= 1` pattern for `_current_round`).
  - **`FighterState.spend_stamina` body** (`fe.py`): the multiplier
    itself — `effective = amount * DRAIN_SCALE_K * (1 + DRAIN_CARDIO_S
    * (60 - cardio_rating) / 40)` then `self.stamina = max(0,
    self.stamina - effective)`. The `max(0, ...)` floor semantics are
    unchanged; only the amount is scaled.
  - **Constructor kwargs, four sites**: `fe.simulate_fight` at
    fe:4084-4085 and fe:4093-4094 (`f1_state`, `f2_state`);
    `fi.NarratedFightSimulator._init_fight` at fi:513 and fi:522
    (`fighter1_state`, `fighter2_state`). Each passes
    `cardio_rating=fighter{1,2}.cardio` alongside C11's
    `recovery_rating=fighter{1,2}.recovery`.

  The Gate 1a working-tree edit (which held identity constants K=1.0,
  S=0.0) never landed as its own commit — the whole wire ships here
  at B9 constants. The two numeric literals below are the only pieces
  whose values were re-chosen between Gate 1a's identity and C12's
  ship:

  ```
  + DRAIN_SCALE_K   = 0.6
  + DRAIN_CARDIO_S  = 0.5
  ```

  **MECHANISM.** `fe.FighterState.spend_stamina(amount)` (fe:619-624)
  applies `effective = amount * DRAIN_SCALE_K * (1 + DRAIN_CARDIO_S *
  (60 - cardio_rating) / 40)`. At K=0.6, S=0.5: cardio=60 fighter
  drains at 0.6× nominal; cardio=30 at 0.6 * 1.375 = 0.825× nominal;
  cardio=90 at 0.6 * 0.625 = 0.375× nominal. Cardio-90/cardio-30
  per-spend ratio = 0.455 (elite drains at 45% of poor's rate).
  Attacker-side spend sites use payer's own cardio_rating; defender-
  side (body-shot, KD-tax, TD-impact, rocked-drain, being-submitted;
  5 of 13 sites) use defender's cardio_rating per B2 ruling. All
  plain-global reads at call time; sweep by attribute rebind for
  future work (setattr-live proven Gate 1a Step 3(a) at Δ = 0.00e+00).

  **GATES (all MEASURED, artifacts under `outputs/sm1/stamina_drain1/gate_1c/`):**

  - **3a file-vs-setattr parity** (source: `3a_pop_pool1_outcomes.csv`
    vs `gate_1b/pop_pool1/cell_K0.6_S0.5/outcomes.csv`):
    1225/1225 winner + method + round IDENTICAL on POP-POOL1
    round-robin. File constants reproduce the setattr grid cell
    exactly. Ledger residual max 1.28e-13.
  - **3b tierA_corrected_c11 2100 after-run** (source: `3b_tierA_c11_after.csv`,
    `3b_per_bin_stats.csv`, `3b_method_dist_per_pairing.csv`):
    ledger residual 9.95e-14. Per-bin close (median R1/R2/R3) reported
    vs Van's Q5 T4 reference; T4 REPORTED not gated per scope. Method
    dist per pairing: DEC in-band (|Δ|≤5pp vs c11 baseline) = 2/11;
    9 pairings drop 20-54pp DEC toward finishes (Q6 direction inverted,
    accepted-open per B9).
  - **3c fresh T1 at file-constants** (source: `3c_clone_T1.csv`):
    T1_R1 = 39.87 (passes ≥25). T1_R3 = 14.12 — **NOT ESTABLISHED**:
    the R3 sample is selection-thinned (striking-cardio-90 R3_n=3,
    because high-cardio strikers finish fights before R3 under drain-
    active physics) and grappling-cardio-90 closes R3 at floor 0.50
    despite the 0.375× per-spend drain factor — a flat-regen
    cumulative-cost ceiling: even a light-drain fighter accumulates
    enough total spend over 3 rounds to reach the floor when the
    per-exchange +0.5 recovery doesn't scale with cardio. **Re-measure
    T1_R3 after lever two ships** (in-round regen at fi:1651-52 is the
    cardio-owned recovery channel Q1 named; scaling that with cardio
    restores headroom above the floor at R3). The T1_R3 miss at file-
    constants matches the grid measurement (grid 14.31, file 14.12)
    and is not a Gate 1c defect — it's a joint constraint on the
    drain lever alone that lever two is designed to relieve.
    B7 donors (heart=50, chin=50), cardio 30 vs 90, N=200 each.
  - **4 fixture re-baseline** (source: `4_fixture_hashes.csv`):
    7/7 raw + 7/7 norm hashes BROKE as expected; zero arms unchanged
    (no red flag). Old C11 baseline retired-not-deleted at
    CLAUDE.md:5274-5282. **pv15 probe file edited alongside fe** to
    update `REUSED_HASH_TARGETS` and `REUSED_NORM_HASH_TARGETS` to
    the new B9 baseline; probe sha256 transition MEASURED:
      - PRE-C12 (C11 baseline, RETIRED): `3ca1f644828c1277f7118229f2438235c6ead51a2e81431a8e08ed0669b88a52`
      - POST-C12 (B9 baseline, CERTIFIED): `62d05b560954838816fe3e9e6fcbad0bd9d7274b10d52f9ba4d75e428fb0a517`

    **New B9 fixture baseline (certified 2026-09-01):**

    | arm | new raw md5 | new norm md5 |
    |---|---|---|
    | L-J1 | `da069edf204e80e9d4f3ad1a17b61d9b` | `d179ae234eeb159a6a18995db129d01e` |
    | L-B88 | `2fe2dc05d8001d8f784974236e4e3142` | `d3119dd87a9b2bb221c2209a25593694` |
    | L-K74 | `bf90f37e02759fc5d6f26131c8dd59e5` | `ec3d2d278fe6b2d8dc642b27d61d65c6` |
    | L-K78 | `2a174ca9678d1d22c9a48c32dce319be` | `596618a7c535cbb9fa6a5f97817651da` |
    | L-K88 | `269d0a1317ea8813ce34892ca6d7b8bf` | `adfde80199982e80236fedf8eb26ec3f` |
    | L-C88 | `6fc46439b6f9885ebc1bcda541906d02` | `565b8de33307dcfba6daebfe774d2a9b` |
    | F | `c4059b6c5b4c56e22860ca9db47aa188` | `1be7dae543bccc14ca725781735e6ea7` |

    **Old C11 baseline retired here (not deleted from CLAUDE.md's C8
    filing at :5274-5282):**

    | arm | old raw md5 (retired) | old norm md5 (retired) |
    |---|---|---|
    | L-J1 | `02b9a62ea1a581da43cda0074a3c36f7` | `9271a4e60a35247ba0613b10dd715382` |
    | L-B88 | `b421b5c01534d8f1013b8fdf4f4d97be` | `483cd4dea135b6ce7753d2977669036d` |
    | L-K74 | `4dae6c6be0f100763cde137d6cffef1b` | `e31e79d9546dcf77330a67496b1afc14` |
    | L-K78 | `52387566b8d2d29fb1e85e1aa4de0985` | `9532ce8cc061de1ddc106a65709e3b4a` |
    | L-K88 | `547966e1913ecd2a32bf8d1b5ee15412` | `c025febdf78d3e81429cc671f05a3ac3` |
    | L-C88 | `041dae4ffc41d431ab6b97c1b66fcdec` | `065172df2b40face63d839a73392c03e` |
    | F | `00f41d144dea015f675b177725f20c41` | `d74f66f5d1c33927fbc2d17d0c1e2fd5` |

  - **5 pre-gen parity + REVEALED-not-created verdict** (source:
    `gate_1c/5_pregen_parity.csv` + `gate_1c/two_engine_verify.py`).
    Same clone pair (striking c=70 vs all-60, seed 999, 3R), donor R1:

    | config | engine | requested drain | actual drain | req−act | open→close |
    |---|---|---:|---:|---:|---|
    | IDENTITY (K=1.0, S=0.0) | live | 121.00 | 121.00 | 0.00 | 100 → 5.5 |
    | IDENTITY (K=1.0, S=0.0) | pre-gen | 183.00 | 129.00 | 54.00 | 103 → 0.5 |
    | B9 (K=0.6, S=0.5) | live | 81.90 | 81.90 | 0.00 | 100 → 44.6 |
    | B9 (K=0.6, S=0.5) | pre-gen | 117.08 | 117.07 | 0.00 | 103 → 11.0 |

    Proportional REQUESTED gap (pre-gen − live) / live:
      - IDENTITY: **51.2%**
      - B9: **43.0%**

    Proportional ACTUAL gap:
      - IDENTITY: 6.6% (floor clipping absorbed 54pt of pre-gen's excess
        request into equal-actual on both engines)
      - B9: 43.0% (no clipping — both engines' actual == requested)

    **VERDICT — REVEALED, not created.** The engines always disagreed
    on requested drain by ~43-51%. At IDENTITY, live's requested drain
    (121) fits inside the tank plus regen; pre-gen's (183) overshoots,
    and the fe:611-612 `max(0, ...)` floor clip discards 54pt as waste
    — smoothing both engines down to nearly-equal actual drain. Under
    B9, K=0.6 × g(70)=0.875 = 0.525× per-spend factor keeps both
    fighters well above the floor at R1 end; no clipping fires; the
    latent requested-drain divergence surfaces at the actual layer for
    the first time. Ledger CLOSES independently on each path (both
    residuals ~1e-13). Drain physics correct per path; the divergence
    is upstream in the engines' action-selection loops. Filed as a
    RIDER to the TWO-ENGINE CONSOLIDATION arc at CLAUDE.md:691-711
    (which had measured finish-rate divergence, not drain divergence
    under a shared dial) — the widening was pre-existing under drain
    physics, hidden by universal flooring; B9 didn't create it.
  - **6 C11 cut-direction re-run** (source: `6_cut_direction.csv`;
    792 cut fights from tierA_c11 baseline schedule):
    Cut fighters aggregate: Δwin = +0.6pp (essentially flat);
    **ΔKO/TKO-loss = +7.9pp** (26.8% → 34.6%). Per fighter, biggest
    ΔKO/TKO-loss jump: 85f73bf3 (HL cardio 65) at +16.0pp. Direction
    MEASURED — cut fighters lose the same amount but lose worse
    (more knockouts, fewer decisions). C11's "cut penalty is
    functionally dead" reading (already refined at C7 for high-recovery
    cases) is now falsified at the outcome layer for the low/mid-cardio
    cut subset under drain-active physics.

  **CONSEQUENCES FILED WITH THE SHIP:**

  1. **DEC/violence shift is population-wide.** POP-POOL1 identity 52%
     DEC → K=0.6/S=0.5 28.6% (Gate 1b frontier, N=1225). tierA_c11
     drops 20-54pp DEC on 9/11 pairings (Gate 1c 3b, N=2100). Q6
     predicted "more decisions from fresher fighters (defends-better
     dominant)"; measured direction inverted ("more finishes,
     presses-better dominant"). B9 accepts-open. **PA violence-shift
     monitoring owed post-deploy**: watch the DFC N per-week fight
     summary (📊 terminal diagnostic) for KO+TKO+SUB share vs decision
     share; if the shift is game-feel-negative in live play, a
     subsequent design ship (lever-two regen tuning, or a
     compensating dial elsewhere) is the response, not a rollback of
     B9's drain physics.
  2. **T2 partially met; remainder assigned to lever two.** K=0.6/S=0.5
     delivers T2_R1 35.5% (target <25%, misses by 10.5pp) and T2_R2
     48.1% (target <40%, misses by 8.1pp) on POP-POOL1 (Gate 1b
     frontier). B9 rules the remainder goes to Q1's in-round regen
     (fi:1651-52), not to bending T2's thresholds. STAMINA-DRAIN1
     delivers the drain half; a future lever-two ship delivers the
     recovery half.
  3. **T1_R3 not established at file-constants; owed to lever-two
     re-measurement.** T1_R3 = 14.12 (grid 14.31 within rounding),
     below the 20 target. Two joint constraints: (a) the R3 sample
     thins under drain-active physics for high-cardio strikers who
     finish fights before R3 (striking-90 R3_n=3 on N=200), and
     (b) a flat-regen cumulative-cost ceiling exists — grappling-90
     closes R3 at 0.50 despite drain at 0.375× nominal, because the
     per-exchange +0.5 recovery (fi:1651-52) doesn't scale with cardio
     and the fighter accumulates enough spend across R1-R3 to floor
     regardless of per-hit efficiency. Both constraints relieve when
     lever two scales in-round recovery with cardio. Re-measure T1_R3
     post-lever-two.
  4. **PEAK103 exposure widens slightly** at K=0.6 vs K=1.0. First
     pre-gen `spend_stamina` call drains less (K=0.6), leaving the
     103.0 starting stamina exposed to Category B (`stamina/100`
     consumer) lift for a slightly longer window before the first
     `recover_stamina` call at fe:3813/3814 clamps to 100. Still
     bounded by first regen; still exists only for the pre-gen
     fatigue≤10 "peak condition" branch at fe:4023-4043. Filed for
     potential PREGEN-PEAK103 arc; NOT blocking B9 commit.
  5. **tierA_corrected_c11 baseline retired on B9 deploy.** New post-B9
     baseline generation owed (C8 pattern). MC ODDS invariants +
     Stage 0d `_assert_sanctioned_config` allowlist may need re-check
     against B9-shipped numbers; MC ODDS storage schema and Stage 0d
     sanctioned triple LIVE_PLAY = (55, 0.48, 10) are unaffected (B9
     changes drain constants, not config triples).
  6. **Two-engine drain divergence REVEALED (rider to
     TWO-ENGINE CONSOLIDATION arc at CLAUDE.md:691-711).** Gate 1c
     Step 5 + closeout Item 1b MEASURED that the engines request
     drastically different drain totals per round (pre-gen requests
     ~43-51% more than live on the same seed/donor/opponent). Under
     IDENTITY constants (K=1.0, S=0.0), fe:611-612's `max(0, ...)`
     floor clipped 54pt of pre-gen's excess request into equal-actual
     drain on both engines — floor saturation was hiding the
     requested-drain divergence. Under B9 (K=0.6, S=0.5), no
     clipping fires on this pair and the divergence surfaces at the
     actual layer for the first time (43.0% actual gap == the
     pre-existing requested-drain gap). B9 does NOT create the
     divergence; it REVEALS it. Filed as a rider to the TWO-ENGINE
     arc — the parent arc measured finish-rate divergence (~39pp),
     not drain divergence under a shared dial; this rider adds the
     drain axis. Consolidation is already scoped HIGH; no additional
     ship is required by B9. Per-exchange action-mix investigation
     folds into that arc, not into C12.

  **RIDERS OWED (docs-only, C12 carries):**

  - **B4 PHANTOM NAME RETIRED**: fi has no `_init_engine`. The method
    constructing FighterState in NarratedFightSimulator is `_init_fight`
    at fi:482. Every prior citation of "_init_engine" (v0.1 spec, Gate
    1a harness comments) is FALSE — retired-not-deleted.
  - **C11 cut-direction refinement**: C11 W2 filing recorded "no
    systemic direction observed on the current 4-fighter pool" for
    cut-fighter Δwin. That reading is CORRECT for Δwin (Gate 1c
    measures Δwin_agg = +0.6pp, still flat). It is INCOMPLETE for the
    broader cut-direction question: **ΔKO/TKO-loss_agg = +7.9pp** at
    B9-active drain (Gate 1c Step 6). The "cut penalty is functionally
    dead" corollary reading (already refined at C7 for high-recovery
    cases) is now falsified at the outcome layer post-B9.

  **PROCESS INCIDENTS THIS ARC (logged not hidden):**

  - Gate 1a 1st pass filed T2 on the wrong population (clone-donor
    median instead of Tier A population). Caught by Van at report
    read; T2 recomputed from Tier A population; corrected metric
    became the record.
  - Gate 1a 1st pass DEC in/out compared per-pairing rate to pool-wide
    44.6%±5pp band; baseline itself violated that band on P03/P10.
    Corrected metric = per-pairing Δ vs c11 baseline.
  - Gate 1b summary table mis-recalled donor bin cardio ranges
    (three of four cells wrong); caught by Van comparing to verbatim
    clone.csv output. B6 discipline enforced.
  - Gate 1c cardio-distribution measurement discovered Tier A pool
    cardio-skewed +18pp vs world-gen population median; B8 filed;
    POP-POOL1 stratified sample built for frontier rerun.
  - POP-POOL1 discrimination FAILED by 0.02pp on Van's Gate 0-shape
    band; B8-a amendment ruled by Van (Option A) that the band was
    Tier-A-pool statistic, not world constant; amended criterion is
    "reproduces broken-world signature at identity" (both
    overwhelmingly true).
  - Gate 1c initial two-engine parity framing ("gap is pre-existing
    per TWO-ENGINE CONSOLIDATION") was too comfortable — the parent
    arc measured finish-rate divergence, not drain-under-shared-dial.
    Van caught the framing; closeout Item 1b MEASURED requested drain
    at IDENTITY, confirmed the divergence was hidden by floor
    clipping (REVEALED not created). Framing corrected in consequence
    #6 above; rider filed to TWO-ENGINE arc.

  **QUEUE POST-C12:**

  - STAMINA-OFFENSE-CURVE1 docket parked at
    `claude/stamina_offense_curve1_docket_v0_1.md` — three measurements
    (consumer census, effectiveness-vs-stamina curve per engine,
    finish-rate-vs-skill-gap). SEQUENCING RULED: runs BEFORE lever
    two, because if regen makes the finish-fest worse and lever two
    shipping blind would compound it.
  - Lever-two (in-round regen +0.5/exchange at fi:1651-52) as the
    next stamina-arc ship, delivering T2's remainder — SEQUENCED
    AFTER the offense-curve docket per above.
  - PA violence-shift monitoring post-deploy (Q6 direction shift).
  - tierA_corrected_c11 → tierA_corrected_c12 re-vintage (C8 pattern).
  - Live-roster violence check on next live card (owed from Gate 0(b)
    R2 A5, was carried into STAMINA-MODEL1 Gate 1 Tier B — B9 changes
    the underlying physics; the check comes due).
  - TWO-ENGINE CONSOLIDATION arc continues to carry both the
    finish-rate divergence (its original scope) and the drain-under-
    shared-dial divergence (new rider from this ship's Gate 1c Step 5
    + closeout Item 1b).

  **ARTIFACTS (all under `outputs/sm1/stamina_drain1/gate_1c/`, untracked):**

  - `harness.py` — Gate 1c 6-step consolidated harness
  - `harness_stdout.txt` — full session log (mtime 2026-09-01 21:11)
  - `gate_1c_out.txt` — cc's structured session log
  - `3a_pop_pool1_outcomes.csv` — 1225 file-constants outcomes for parity
  - `3b_tierA_c11_after.csv` — 2100 tierA after-run outcomes
  - `3b_per_bin_stats.csv` — per-bin close+zero at file-constants
  - `3b_method_dist_per_pairing.csv` — DEC delta table vs c11
  - `3c_clone_T1.csv` — clone T1 measurements
  - `4_fixture_hashes.csv` — 7-arm hash old-vs-new
  - `5_pregen_parity.csv` — pre-gen parity numbers (actual only)
  - `6_cut_direction.csv` — 792 cut fights, Δwin + ΔKO/TKO-loss
  - `two_engine_verify.py` — closeout Item 1b: 2×2 requested+actual
  - `C12_claude_md_draft.md` — this docs block

  Scope doc: `claude/stamina_drain1_scope_v0_1.md` carries B1-B9 +
  B7 + B8 + B8-a addenda; updated in-session as each was ratified.

