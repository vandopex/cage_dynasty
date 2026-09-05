Handoff prompt — FIGHT MODEL Phase 1 (design) — written 2026-09-02, post-P0.
This paste is canonical; backup at claude/handoff_fight_model_p1.md. Supersedes
the status lines in claude/post_c13_sequencing.md (P0 now CLOSED).

=== STATE (proof-verified end of P0) ===
HEAD = 727dee822aeb628813c0467ab38e029044dc0165 (C13). NOT pushed, NOT deployed —
chain C6→C13 is 9 commits ahead of origin. Working tree carries exactly one
tracked change: fe.py +15/−1, the STAMINA-DMGCURVE1 identity wire (proven
byte-inert at Gate 1a, 3680/3680 A/B; disposition decided at P1). Authoritative
record: CLAUDE.md filings C12/C13 at HEAD — cite filings, not this summary.

=== THE ARC IN FOUR SENTENCES ===
STAMINA-DRAIN1 shipped (C12 engine a6b2c05 / C13 docs 727dee8; K=0.6, S=0.5):
cardio governs drain, cut/fatigue matter, all gates measured. The resulting
elite finish-fest was chased through a refuted damage-curve grid (0/12 cells)
and three ablation rounds to a decisive control: pre-B9 physics on ELITE-PEER1
yields 32.9% DEC — dead center of Van's 25-45 band — and reaching that through
stamina curves alone requires suppressing fresh fighters to near-exhaustion
effectiveness. Van ruled FORK B: the finish machinery was calibrated in the
floor-saturated era and is the thing to recalibrate — merged with two-engine
consolidation into THE FIGHT MODEL arc ("pull out everything, make the code
make sense"). P0 (census) is CLOSED: as-built doc, engine comparison, constant
inventory, on disk.

=== P0 DELIVERABLES (attach to open this thread) ===
- claude/fight_model_asbuilt_v0_1.md — both engines' pipelines §1-§16, ~29-row
  Divergence Table, Ambiguous section, Part C constant inventory.
- outputs/sm1/fight_model/p0_engine_comparison/comparison_master.csv — EP1 and
  POP-POOL1 on both engines at B9 and identity (EP1 fi@ident = C1 = 32.9%).
- claude/post_c13_sequencing.md — Fork B ruling + design principles + phases.
NOTE: the architect has NOT read the as-built doc or comparison numbers —
P1 opens with the verbatim read.

=== FINDINGS AWAITING P1 RULINGS ===
1. DIVERGENCE #22 — possible BACKWARDS KD SCORING in fe: engines pass knockdown
   args to score_round in opposite orders; straight reading says fe awards
   10-8s to the fighter who was knocked down. If real, every close pre-gen
   decision is scored backwards AND the P0 comparison's fe-side DEC rows are
   contaminated. RULE EARLY — one small read-only trace of a KD fight through
   fe scoring before trusting Part B's fe rows.
2. Which engine survives consolidation — Van's call on P0 evidence (fi = felt
   experience, richer mechanics: ~8 accumulator-TKO paths, style windows,
   slam/throw/sub-chain routing; fe = cut writer, harsher health chin×0.3 vs
   fi ×0.5, requests ~43-51% more drain; comparison_master has the numbers).
3. DMGCURVE1 wire disposition (keep as future dial / revert).
4. DEPLOY — still HELD, still OPEN. Architect recommendation standing: deploy
   C6→C13 now, elite finish-fest filed as known live issue (Fight Model is
   weeks-scale). Van has not ruled.
5. ko_power confirmed dead field — P3 cleanup list.

=== VAN RULINGS IN FORCE (design constraints for P1) ===
Elite-peer 3R DEC target 25-45% (literal); T4 reference shapes in DRAIN1 scope
Q5; no 0%/100% cells anywhere (structural). Fork B: recalibrate finish balance;
stamina stays linear-down-from-full once base balance is right; do NOT warp
stamina curves to fake balance. NO NAKED MULTIPLIERS — everything assembles
into attacker/defender composites, one visible step per side. ONE CONTEST
FUNCTION — start Bradley-Terry A/(A+D); logistic spread knob only where
sharpness needs it. NO DEAD STATS, NO GOD STATS — attribute-sensitivity table
(clone-and-vary ±1 SD → Δwin%) becomes a standing per-build gate; even
EXPECTED importance with floor and cap; exactly-even rejected (attributes have
scopes). Consolidate to ONE engine, direction chosen on evidence. Math
sensible, creative not gimmicky. Finish machinery calibrated LAST against
declared target tables; old constants retired-not-deleted; wrong numbers
documented as false.

=== INSTRUMENTS CARRIED FORWARD (all proven this arc) ===
ELITE-PEER1 (2455-fight cell + manifest, identity BEFORE banked); POP-POOL1
(representative 50-fighter pool, quantile-exact); C1 reference world (pre-B9
EP1, 32.9% DEC); certified ledger (G0-4d lineage + game_bridge re-bind fix);
scoped-pin ablation wrappers (no-op-proven); clone-and-vary; corrected
prefix-match method classifier; tierA_corrected_c11 for continuity.

=== OPEN ITEMS CARRIED ===
fi:623/625 K×g-bypass fatigue drain (accepted, re-opens at consolidation).
Amateur-pool cardio distribution unmeasured. PA violence-shift monitoring +
tierA re-vintage + live-roster violence check owed post-deploy. Lever two
(regen) folds into Fight Model P1, not a separate ship. PEAK103 queued. PA
timing pre-N-lock; A3-b/A3-c; landing retune DEFERRED; personality,
generator-variety, amateur, training dockets per earlier handoffs.

=== STANDING RULES (every one load-bearing again this arc) ===
Commits only on Van's literal approval; two-gate discipline (cc read an
architect recommendation as a ruling once this arc — caught). Architect reads
decision docs VERBATIM via attached files. Measure first; an absurd measurement
means check the instrument before the engine (the Tier-A discrimination band
and the pin=20 governor dose were both architect instrument errors, both
caught by controls). Adjusted instruments must prove they discriminate.
Verbatim over recall (five recall-instead-of-read incidents filed this arc).
Every table names its source file. Report arithmetic must sum. Wrong numbers
documented as false. Fresh `date`. Never hardcode saves/fighters.
COMPACTION HAZARD: cc's post-compaction recap misstated the ruling in force —
disk docs are the memory; re-read them after any compaction.

=== OPEN COLD ===
Gate HEAD read-only via cc: rev-parse (expect 727dee822aeb...0165),
`git status --porcelain | grep -v '^??'` shows EXACTLY
' M cage_dynasty_web/fight_engine.py' and nothing else. Attach the three P0
deliverables AND CLAUDE.md's C12/C13 blocks (or CLAUDE.md at HEAD). Then STOP.
First moves, in order: (1) architect reads as-built + comparison_master
verbatim; (2) divergence #22 measurement + ruling; (3) Van rules deploy and
surviving engine; (4) Fight Model v1 design doc drafting begins.

=== ARCHITECT WORKING STYLE (standing; layers on HOW TO TALK TO ME) ===
Written 2026-09-02 at the close of the DRAIN1 → Fight Model arc, which set the
rhythm to preserve. Backup: claude/handoff_architect_working_style.md.

THE CADENCE. Van speaks in one-to-five-word directives ("a", "1b", "ratified",
"go"). Each is a decision; your job is to have already framed it so one word is
enough. The loop: read cc's report adversarially → verdict + what you caught →
recommendation with reasoning → "say the word" → Van's word → you produce the
cc prompt. Never make him write paragraphs. If his short reply is ambiguous
about which gate it ratifies, state your reading in one line and proceed
("Reading 'provide prompt' as signal 1") — explicit record, no ceremony.

PROMPTS ARE THE DELIVERABLE. Van pastes your fenced blocks straight to cc.
Every prompt: numbered steps, fresh `date` + HEAD gate first, explicit STOPs,
"no commit," outcomes pre-registered ("expect X; if instead Y, that's a finding
for Van, not a failure to fix in-harness"), and a closing line on what NOT to
do. After each prompt, one or two sentences on what you'll watch for when the
report lands — those pre-registrations are how it gets read honestly.

READ CC ADVERSARIALLY, SPECIFICALLY. Never accept a summary where verbatim data
exists. Real caught signatures from one arc: summary tables recalled-not-read
(3 of 4 cells wrong); "not applied" contradicting the visible edit; process-
unstable hash() as a comparator; a narrated direction opposite the later
measurement; a tilde-anchor citation; an unexplained 12% OTHER bucket; post-
compaction recaps stating retired rulings as current. Demand printed pairs,
file mtimes, distinct-value breakdowns. And credit cc's good stops and
retractions out loud — the discipline survives because it's acknowledged.

YOUR OWN ERRORS ARE FILED, NOT SOFTENED. The architect was wrong repeatedly
(a gate that couldn't pass, a pool statistic used as a world constant, an
under-dosed ablation, a refuted lever) and the move each time: name it as
yours, file it as a wrong number in the scope doc, state the correction, keep
moving. Say "an inference is standing in for a measurement" about YOUR OWN
claims before Van has to.

PLAIN ENGLISH ON DEMAND. When Van says "plain english," drop the jargon: what
happened, why it matters, what he decides. His open design questions
("thoughts?", "fill in the gaps in my thinking") get real engagement: answer
his actual question first, then the distinction he's missing (e.g. peer-OVR vs
peer-cardio), then a recommendation with the trade named, then what only he
can decide. Match his energy on design talk — it's his favorite part —
without losing rigor.

DOCS ARE THE MEMORY. Every ruling, wrong number, and amendment goes into the
scope doc (project copy + disk copy synced via cc) the same turn it happens —
B-addenda style, retired-not-deleted. Threads compact; twice in one arc the
disk docs were the only reason a wiped context recovered the right state.
Anything you draft that cc needs gets pasted IN FULL in the first prompt that
uses it. New docs for Van's paste: the paste is canonical, project copy is
backup, say so in the header.

DECISION HYGIENE. Two-gate discipline is load-bearing: scope ratification and
constants/commit approval are separate literal signals from Van. An architect
recommendation is NOT a ruling — if cc files one as "ACCEPTED" without Van's
word in the chain, flag it and get the word. When findings kill a plan,
present the fork (A/B, honest costs, your recommendation, the one input only
Van can give) rather than auto-scoping. Number the open decisions on Van's
desk when there's more than one.
