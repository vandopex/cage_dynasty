# THE FIGHT MODEL — v1.0

**Cage Dynasty fight-resolution design contract.**
Assembled 2026-09-03 by the architect from rulings D1–D12 (Van, 2026-09-02 → 2026-09-03).
Status: RATIFIED (Van, 2026-09-03). This is the contract P3 builds against.
Chassis: `fight_integration` (fi) survives consolidation; `fight_engine` (fe) retires as a resolution engine, its unique mechanisms carried over deliberately (§8).

Provenance: every design choice here was made against measurement — the P0 as-built census (both engines, 29 divergences, full constant inventory), the P2 attribute-sensitivity baseline (118K fights, three-gate instrument), and the D2 docket (exact-anchored to both reference worlds, 2455/2455 row-for-row). The measured before-picture is Appendix A. Nothing in this document is a guess about the current engine.

---

## §0 Mandate and north star

Van's mandate: *"pull out everything and look into the fight — make the code make sense."* Math that makes sense; creative, not gimmicky; attributes evenly important where possible (even **expected** importance with floor and cap — exactly-even rejected, attributes have scopes).

The north star is emergent story: a player once wrote an unprompted trilogy about a rivalry nobody scripted. Every mechanism below is judged by whether it can surface something **specific and actionable** a player can act on, ignore, or retell. Realism is a tool, never the goal.

Standing engineering rules inherited by all P3 work: commits only on Van's literal approval; two-gate discipline (scope ratification and constants/commit approval are separate signals); measure first — an absurd measurement means check the instrument before the engine; adjusted instruments must prove they discriminate; mechanical-equivalence gates where behavior shouldn't change, explicit before/after measurement where it should; forward-only data fixes, no backfilled saves; wrong numbers documented as false, old constants retired-not-deleted.

---

## §1 The spine (ratified)

The clock is unchanged from today's engine:

> Round loop (3 or 5) → 55 exchanges per round → per exchange: **initiative → action select → contest → consequence → state update → finish checks → bookkeeping**. Round end: between-round stoppages → scoring → recovery. No finish → decision via the judge model.

Every redesign happens **inside the tick**. Consequence: every proven instrument (ELITE-PEER1, POP-POOL1, C1 reference world, certified ledger, ablation wrappers, method classifier, the D2 per-call event logs) remains valid without modification, and P3 can gate each change against the same measurement surface that diagnosed the old engine.

---

## §2 Attributes and scopes (ratified; roster of 19)

**The contract:** an attribute may appear ONLY in its scoped lanes. A scope it doesn't have is a scope it never touches. Guard rails: no attribute in more than 4 lanes (god-stat cap); every attribute in at least 1 (dead-stat floor). The P3 sensitivity gate (per-build, clone-and-vary ±1 SD → Δ decided-share, counterbalanced instrument with no-op + positive controls) re-measures actual importance against this table on every build.

| Attribute | Offense lanes | Defense lanes | State lanes |
|---|---|---|---|
| speed | initiative **component** (capped input to a composite — never raw-vs-raw); strike-accuracy assist | evasion assist (strike D); TD-D assist | — |
| **power** (new, D7) | damage bonus (power families); KD/flash-KO contribution | — | — |
| strength | throws/slams; clinch break; slam damage | escape/sprawl assist | — |
| boxing | punch-family attack | — | — |
| kicks | kick-family attack | — | — |
| clinch_striking | clinch-strike attack | — | — |
| striking_defense | — | strike defense, all families (defensive *variety* comes from composite blends: +speed = evasive, +clinch_control = clinch D) | — |
| takedowns | TD attack; TD-threat pressure | — | — |
| takedown_defense | — | TD defense (primary) | — |
| top_control | passes; position maintenance; GnP context | standup defense (pinning) | control-time accrual |
| guard | sweeps/standups from bottom | pass defense; sub-**escape** component | — |
| clinch_control | clinch entry; clinch maintenance | clinch-entry defense | — |
| submissions | submission attack | sub-**escape** component | — |
| cardio | — | — | drain rate (shipped, C12); in-round regen rate (lever two — new lane) |
| chin | — | KD/rock resistance | max-health scale |
| heart | — | stoppage resistance (feeds the §6 curve); **tap resistance** (§5a) | — |
| composure | — | rocked-state discipline (shorter, less exploitable windows) | heat resistance |
| fight_iq | counter chance; action-selection quality | exploit avoidance | gameplan execution (§5b) |
| recovery | — | — | between-round refill + health regain; rock duration |

**D7 — the power/strength split.** Power = how much it hurts (the KO lever; the method-mix lever toward knockouts). Strength = physicality (grappling force, throws, breaks). Unlocks previously inexpressible archetypes: the one-punch assassin (power 90 / strength 55) vs the ox who has never knocked anyone out (strength 90 / power 55). Costs accepted: world-gen, training, and UI grow a stat; **existing fighters get a load-time derivation** (power seeded from strength plus a style-informed offset) — forward-only, no save backfills.

**Roster review resolution:** no additional defensive striking or clinch attributes — defense is the least legible feedback in the game and the existing defense stat measured dead; defensive variety comes from composite blends, not roster growth. Roster is 19 and closed unless the archetype test (a fighter you cannot build) reopens it.

**Divisor-zoo retirement:** heart / composure / fight_iq today appear as seven ad-hoc divisors (heart/200 … composure/450), all measured at or near dead. Each now has named lanes with one declared strength per lane; the scattered divisors retire at P3.

---

## §3 Composites (boring by design)

Per event class *c*, each side assembles **one visible number**:

    A_eff = A_base(2–3 scoped attributes, declared weights)
            × situational factors (stamina, position, window effects)
    D_eff = same shape, defender's lanes

One assembly step per side, printable per exchange for debugging. Situational factors scale **composites, never results**. The stamina factor stays linear-down-from-full (ruled at Fork B: no warping stamina curves to fake balance). No naked multipliers anywhere: anything that influences an outcome flows through a composite, visibly.

---

## §4 The contest function (one form, everywhere)

    P_c = clamp(P_min_c, P_max_c,  P_even_c + S_c × (A_eff/(A_eff + D_eff) − ½))

Three declared, designer-readable constants per event class. **P_even_c** = the success rate between equals (a design target, not a fitted additive). **S_c** = how much skill matters. **[P_min, P_max]** = structural no-determinism bounds — nobody is ever blanked, nothing is ever certain, by construction. The bolt-on upset branches are **retired** (D4): their job is done structurally by the floors, the variance, and the windows — and the measurement showed they paid fighters to be worse (F9). Variance: one documented RNG draw shape per class; its shape must let D_eff matter (the old one-sided offense-only variance is a suspected mechanism of the dead defense layer, F3/F6).

### P_even targets (D10, ratified)

| Event class | P_even | Note |
|---|---|---|
| Boxing strikes | 45% | matches measured reality and real-MMA feel |
| Kicks | 42% | slightly riskier than punches |
| Clinch strikes | 48% | close range lands more |
| Takedown at distance | 30% | TDs are earned — fail twice per success |
| Takedown in clinch | 45% | wrestling becomes a two-step gameplan |
| Throws | 38% | high-risk entry for the sambo/judo routing |
| Guard passes | 45% | — |
| Sweeps | 35% | thin measured sample; re-check at calibration |
| Standup from bottom | 50% | bottom is not a prison |
| Clinch entry | 40% | feeds the clinch game §5b rewards |
| Clinch break | 45% | — |
| Submission lock-in | 35% | what happens after locking is §5a's contest |

### S_c targets (D10, ratified: "steeper, but not un-fun")

| Family | 20-point edge does | Character |
|---|---|---|
| Strikes | 45% → **60%** | the better striker clearly runs the stand-up; four in ten still land against him, and one clean shot always matters (§6) |
| Takedowns | 30% → **52%** | elite wrestlers put you where they want you |
| Submissions | steep — as measured today (F8: +13–16pp slope) | the one wire that already worked is the reference for "specialist feels specialist" |
| Passes / sweeps | between strikes and TDs | — |

Declared against measured zero-points: strikes today ≈ 0 slope (F6), submissions today steep and correct (F8), default grappling today *inverted* at extremes (F9). The un-fun ceiling is guarded structurally by P_min floors, not by flattening slopes.

---

## §5 State model and windows (the creativity budget)

**Two currencies (D1):** **Health** answers "how close is this fight to being stopped" — it is the §6 stoppage-pressure meter. **Regional damage accumulators** (legs, cuts, chin erosion) answer "what is permanently breaking." No double-counting between them. Also persistent: stamina (linear), momentum, position, rocked.

**The window mechanism** — one mechanism, many stories:

    WINDOW = (name, trigger, duration, composite/state effects, commentary hook)

Every existing style mechanic restates as a window row: karate patience, point-fighter movement, brawler walk-through → counter, adrenaline surge, the sprawl counter (which finally gets its consumer), the sambo chain, rocked itself. New story beats become **table rows, not code paths**. Window effects scale composites only (§3 discipline). The commentary layer reads the window table — every window is a visible, nameable beat. This is where the trilogy-story bar gets met.

### §5a Submissions (Van-designed, D6)

Two contests inside every locked submission, replacing today's single progress-vs-escape race:

1. **ESCAPE** — technical: can you get out? Defender's guard + submissions composite vs attacker's submissions composite. The escape artist's contest.
2. **TAP** — will and condition: how deep do you survive when you can't get out? **Heart sets the tap threshold** (how far past locked-in the fighter suffers); current damage/stamina state scales it down. Fresh and tough survives deep; gassed and hurt taps early.

These produce distinguishable fighters the current engine cannot tell apart: the high-guard escape artist vs the average-technique iron-heart survivor.

**D6 — refusal resolves by submission type** (SUBMISSION_PROPERTIES gains a `type` field, choke | joint_lock — a table row, not a code path):
- **Choke** + refusal past threshold → out cold. Heart delays the tap but the finish arrives anyway. *"Put to sleep — never tapped."*
- **Joint lock** + refusal past threshold → injury finish, hooked into the existing injury system. *"Never tapped; the arm went."*

Calibration note: the elite finish-fest measured as overwhelmingly submission-tick resolution through gassed defenders (F7, 15.7× config swing). This model rebuilds exactly that spot; sub-resolution calibration happens here, not via a P_even knob.

### §5b Aggression and gameplans (D8)

Three layers, mostly existing machinery:

1. **Tendency** — every fighter generates with a default gameplan leaning. A *trait*, not an attribute (who they are, not how good they are). Feeds the personality docket later.
2. **Choice** — per fight: the user picks via the shipped gameplan dials; AI opponents start from tendency.
3. **Circumstance** — the AI adjusts tendency through a small **legible rule table** (~4 rules), each a nameable story beat: behind on the cards entering R3 → aggression up (*"he knows he needs a finish"* — possible at all only because round scores mean something post-#22); poor chin vs a big puncher → down; opponent visibly gassed → up; big favorite cruising → coast.

**Execution:** fight_iq's gameplan-execution lane governs how faithfully the plan is followed — the low-IQ brawler *has* a smart plan and abandons it the first time he gets clipped. v1 ships tendency + dials + the four-rule table; richer between-round adaptation is deferred.

---

## §6 The finish model (D9 — five parts)

1. **The meter.** Health *is* stoppage pressure (D1 promoted). All strike-family finish questions read this one number. The twelve scattered finish machines' private accumulators and thresholds become damage inputs, not deciders.
2. **The one check.** Once per exchange and once between rounds: *does someone stop this?* One smooth curve — above the critical health line, never; below it, probability rises as health falls. No cliffs. Two modulators only: **heart** lowers the line (a high-heart fighter is allowed to go deeper before rescue — his stoppage-resistance lane made real), and **context** nudges it (rocked and eating unanswered shots → twitchier referee; surviving safely in guard → less).
3. **The naming table.** When the check fires, the label comes from circumstances at that instant — a lookup carrying a commentary hook per row, not a mechanic. One enormous shot carried health under the line → **"KO"** (the flash knockout is a *label* now, not a separate lottery). Dominant ground position → **"TKO (Ground and Pound)."** Standing, rocked, unanswered → **"TKO (Referee Stoppage)."** Between rounds, by dominant damage type → **Doctor** or **Corner**. A new finish flavor is a new row.
4. **The carve-outs.** **Submissions** run their own contest (§5a) — a choke finishes because the choke finishes. **Structural finishes** read the accumulator currency with one plain threshold each: the cut stoppage, and the leg-kick TKO.
5. **The knobs.** ~8 named constants replace ~40: the critical health line, curve steepness, heart modulation strength, a between-round multiplier, two accumulator thresholds, plus the §5a sub dials. Calibrated **last**, against §9. Because method labels emerge from the naming table plus fight flow, fixing the decision rate cannot silently deform which finishes happen.

**D12 — the sacred finish.** The **leg-kick TKO keeps a private dial** — the only finish flavor that does. It reads the leg accumulator, targets **≈1% of all fights**, and gets first-class naming-table and commentary treatment (the crumple, the corner) precisely because it is rare. *"Low percentage — but when you see it, it's like wow."*

---

## §7 Scoring, decisions, fairness (fixes declared)

- **Divergence #22 fixed at consolidation:** fi's inflicted-order KD convention is the standard; `score_round`'s arguments are renamed so the backwards call can never recur. (fe's matched-order call awarded rounds to the knocked-down fighter, 227/227 measured.)
- **fi:1240 double-write fixed:** knockdowns counted once; 10-8s stop being inflated.
- **F1 fixed:** the initiative tie-break becomes slot-symmetric (coin flip). Today fighter1 — systematically the higher-ranked side, per the call-site audit — wins 100% of initiative ties, a hidden ~1–1.5pp favorite's edge. Fixing it slightly **raises** upset rates; calibration absorbs this, it is not compensated away.
- The judge model is kept.

---

## §8 fe carry-overs (merged deliberately at P3, not lost)

- **Cut writer** — the fi chassis has no cut mechanism; fe's elbow-to-head cut writer carries over, feeding the cut accumulator and the structural cut stoppage.
- **Heat system** — fe-only event-heat modifiers carry over.
- **Failed-takedown punishment** — carried as a *window* ("sprawl-and-brawl punish") rather than fe's inline damage, which also finally defines the sprawl counter's consumer.

---

## §9 Target tables (D11, D12)

**Elite-peer, 3 rounds** (the reference class; ruled DEC band 25–45%):

| KO | TKO | SUB | DEC | DRAW |
|---|---|---|---|---|
| 22% | 20% | 16% | 40% | ~2% |

Vision: *"emulate reality, add a touch more finishes."* Real elite MMA runs ≈47–50% decisions; 40% is deliberately more violent than reality and no longer a finish-fest. Subs raised from the C1 anchor (Van: subs felt low; KO/TKO happened often). Leg-kick TKO ≈1% of all fights rides inside the TKO share (D12).

Method-mix targets for other matchup classes (mismatches, grappler-vs-striker, brawler pairs) are declared during calibration against this reference row, by the same draft-and-adjust process. Van's T4 reference shapes (DRAIN1 scope Q5) inform round-by-round closeness.

---

## §10 Implementation and calibration plan (P3 preview)

Order of operations, DRAIN1-gated throughout:

1. **Consolidate onto fi** with mechanical-equivalence gates wherever behavior shouldn't change yet; fe retires (kept retired-not-deleted).
2. **Fairness and scoring fixes** (§7) with before/after measurement — expect a small upset-rate rise from the tie-break fix; measure it, file it.
3. **Contest-function rebuild** (§3–§4) — composites, declared constants, retired upset branches. Gate: signed-slope re-measurement per class against §4's S_c targets (the D2 per-call instrument, already banked, is the gate).
4. **State + windows + submissions + aggression** (§5) — each window proven no-op when not triggered; the sub model measured against F7's before-picture.
5. **Finish model** (§6) — built, then **calibrated last** against §9 with the ~8 knobs.
6. **Standing per-build sensitivity gate:** the P2c counterbalanced instrument (mirror check + no-op control + positive control) runs on every significant build. Acceptance shape: no ±49s, no zeros, boxing positive, all 19 attributes alive in their declared lanes at even-expected importance with floor and cap.
7. Riders re-opening at consolidation: fi:623/625 K×g-bypass drain; lever two (cardio-scaled in-round regen) lands with §5's state model; amateur-pool cardio distribution still unmeasured; PA violence-shift monitoring, tierA re-vintage, and the live-roster violence check remain owed post-deploy.

Old constants retire into CLAUDE.md filings; every wrong number already found is documented as false, not quietly dropped.

---

## Appendix A — The measured before-picture

The engine this document replaces, one line: **skill doesn't help you land, being worse helps you grapple at the extremes, submissions are the only honest wire, speed decides everything else, and the resilience layer is decorative.**

- **F1** — fi slot-1 bias: fighter1 wins 100.00% of initiative ties (21,156/21,156); slot1 is systematically the higher-ranked fighter in live matchmaking and pre-gen — favorites have always held a hidden ~1–1.5pp edge.
- **F2** — speed god-stat: ±1 SD of speed = ±49.5pp of decided-share; a +15-speed twin wins ~99.5% of decided fights, via initiative dominance.
- **F3** — five dead stats (≤2pp detection floor): striking_defense, takedown_defense, chin, heart, composure. Four of five are the defensive/resilience layer.
- **F4** — boxing inversion: +1 SD of boxing = −5.7pp, corroborating ENGINE-STRIKE-SENS1 across two instruments.
- **F6** — the landing skill dial is disconnected: signed slopes +0.2 to +1.7pp per 20-point gap, every strike family, both reference worlds, exact-anchored.
- **F7** — the elite finish-fest has an address: sub-tick finish rate 12.59%/tick under live drain vs 0.80% at identity (15.7×) — submissions resolving through gassed defenders.
- **F8** — submissions are the one live wire: lock-in slope +13 to +16pp, +38pp at extremes.
- **F9** — the upset branch pays fighters to be worse: −9.3pp inverted extreme slope in default grappling (vindicates D4).

Instrument history is preserved in the working draft (GE-1 through GE-5): two gates that discovered engine defects, one that caught its own dead pipeline through a positive control, and the standing lesson — a no-op control cannot prove life; only a positive control can.

## Appendix B — Decisions log

| # | Ruling | Date |
|---|---|---|
| D1 | Health = stoppage proximity; accumulators = structural damage | 09-02 |
| D2 | P_even by measure-draft-adjust; docket delivered exact-anchored | 09-02/03 |
| D3 | Attribute scopes table; contract + guard rails | 09-02 |
| D4 | Upset branches retired (later vindicated by F9) | 09-02 |
| D5 | P2 sensitivity baseline; closed with F2–F5 banked | 09-02/03 |
| D6 | Choke vs joint-lock refusal (sleep vs injury) | 09-02 |
| D7 | Power/strength split; roster to 19 | 09-03 |
| D8 | Aggression: tendency trait + per-fight choice + 4-rule circumstance table | 09-03 |
| D9 | Finish model: five-part stoppage-pressure hybrid | 09-03 |
| D10 | P_even table + steeper S_c tier | 09-03 |
| D11 | Elite-peer method mix 22/20/16/40/2 | 09-03 |
| D12 | Leg-kick TKO: private dial, ~1%, first-class wow | 09-03 |

*End of Fight Model v1.0. On Van's read-through word, this is the contract.*
