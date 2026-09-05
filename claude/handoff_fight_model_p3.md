# Handoff — FIGHT MODEL P3 (implementation) — written 2026-09-03, post-P3-1 ship

Paste block is canonical; backup at claude/handoff_fight_model_p3.md.
Supersedes claude/handoff_fight_model_p1.md (P1 CLOSED 2026-09-03).

=== STATE (proof-verified) ===
HEAD = 1d8b4e1e71806f04ca070ffc7a2632048d81aa48 (C17). PUSHED and
DEPLOYED to PythonAnywhere on proof (running-file greps primary:
kd_inflicted_by_1 in fe, coin-flip line in fi; PA ref = C17; site
healthy; 2026-09-03 ~21:00 PDT). Working tree CLEAN. Recent chain:
C14 3f9c889 (DMGCURVE1 identity wire + P1 rulings filing) →
C16 e54d3cc (fi fairness fixes + C15 filing + instrument notes) →
C17 1d8b4e1 (#22 scoring-convention fix).
**DEPLOY FREEZE ACTIVE (ruling S2): no deploys until P3-5 gates
pass.** Authoritative record: CLAUDE.md filings C12-C17 at HEAD —
cite filings, not this summary.

=== THE ARC IN SIX SENTENCES ===
P1 (design) closed 2026-09-03 with a ratified contract: fi is the
chassis, roster grows to 19 (POWER split from strength), one contest
function with declared P_even/S_c targets, a windows mechanism, a
two-contest submission model (escape vs tap; chokes sleep, locks
injure), a five-part stoppage-pressure finish model with one sacred
leg-kick dial (~1%), elite-peer method mix 22/20/16/40/~2. The
evidence base: P2 sensitivity (F2 speed god-stat ±49.5pp; F3 five
dead stats; F4 boxing inversion) and the exact-anchored D2 docket
(F6 landing skill-slope ≈ 0; F7 finish-fest = sub-tick collapse
15.7×; F8 submissions the one live wire; F9 upset branch pays
fighters to be worse). P3 scope ratified (S1-S4): fixes →
consolidation → contest rebuild → state/subs/power → finishes
calibrated last → acceptance. P3-1 SHIPPED AND DEPLOYED: slot-
symmetric tie-break (F1 fix — favorites' hidden 100%-of-ties edge
removed; ties measured 50.22%), fi:1240 KD dedupe (10-8 inflation
ended), #22 reversed with affirmative proof (fe 227/227 rounds now
to the KD SCORER, was 227/227 to the sufferer; fi control
unchanged). Six architect instrument errors are filed and each
produced either a discovery or a standing lesson (GE-6: twin gates
use DECIDED-share and pool ≥2 seed blocks). The game live tonight is
fairer than it has ever been; everything else waits behind the
freeze.

=== CANONICAL DOCS (disk copies canonical; project copies backup) ===
Read in this order:
1. claude/fight_model_v1_0.md — THE CONTRACT (RATIFIED; D1-D12).
2. claude/fight_model_p3_scope_v0_1.md — dockets P3-0..6 + status
   addendum (P3-0/P3-1 SHIPPED; P3-2 NEXT; ruled S1-S4).
3. claude/fight_model_v1_design.md — working draft: full findings
   F1-F9, gate-error history GE-1..6, decisions log.
4. CLAUDE.md filings C15-C17 (inside C16's block: C15 + P3-1b
   instrument notes).
Reference: claude/fight_model_asbuilt_v0_1.md (P0 census, both
engines, divergence table, constant inventory).

=== NEXT WORK: DOCKET P3-2 — CONSOLIDATION ===
Pre-gen path moves onto fi; fe retires (retired-not-deleted).
Known call sites from P0: world_init.py:1425 and :2001 iterate
division_rankings in rank order into fe.simulate_fight. Gates per
scope doc: P0 comparison instruments re-run (pre-gen distributions
move to fi's measured values), world-gen wall-time measured (fi is
heavier — measure, don't assume), PRE-REGISTERED: pre-gen worlds get
MORE violent at B9 (fi@B9 EP1 0.94% DEC) — accepted bridge state
per S4(a), invisible under the freeze. Architect opens with
read-only diagnosis of every fe.simulate_fight caller before any
prompt writes code.

=== INSTRUMENTS ===
CARRIED (all proven): ELITE-PEER1 (2455-pair cell + manifest),
POP-POOL1, C1 reference world (32.9% DEC, exact-reproducible at
seed 400000+idx), D2 per-call event harness + banked CSVs
(d2_peven/, exact-anchored both worlds), P2c counterbalanced
sensitivity harness (mirror + no-op + POSITIVE control gates —
a no-op control cannot prove life), div22 trace (proven
discriminating, used for the #22 affirmative proof), corrected
prefix-match method classifier.
RETIRED: the P2b-pattern initiative wrapper — NOT RNG-neutral once
the coin-flip tie-break exists (~1pp artifact); any post-C16
initiative instrument must be rebuilt and proven inert first.
Twin-fight gates: DECIDED-share metric (draws out of denominator),
pool ≥2 seed blocks (cascade variance > naive binomial).
Seed blocks consumed: 400000s (anchors — reusable BY DESIGN for
exact reproduction), 900000-970000 (P2/P2b/P2c/P3-1 — do not
reuse).

=== OPEN ITEMS CARRIED ===
Post-deploy owed trio now runs against the C17 game: PA
violence-shift monitoring, tierA re-vintage, live-roster violence
check on next live card. fi:623/625 K×g-bypass drain re-opens at
consolidation. Amateur-pool cardio distribution unmeasured. PEAK103
queued. Lever two (cardio-scaled regen) lands in P3-4. Method-mix
targets for non-elite matchup classes declared at P3-5. PA timing
pre-N-lock; A3-b/A3-c; landing retune folds into P3-3; personality,
generator-variety, amateur, training dockets per earlier handoffs.

=== STANDING RULES (every one load-bearing this arc) ===
Commits only on Van's literal approval; two-gate discipline (scope
ratification ≠ commit approval). Deploy accepted ONLY on proof:
running-file grep PRIMARY, ref-file SECONDARY (ruled at C14;
phantom deploys have happened). DEPLOY FREEZE until P3-5. Measure
first; absurd measurement → check the instrument before the engine;
adjusted instruments must prove they discriminate; a no-op control
cannot prove life. Verbatim over recall; every table names its
source file; report arithmetic must sum. Decided-share for twin
gates; pool ≥2 blocks. Wrong numbers documented as false; old
constants retired-not-deleted; forward-only data fixes. Fresh
`date` + HEAD gate opens every cc prompt. Never hardcode
saves/fighters. commentary.py lives at narrative/commentary.py
(OUTSIDE cage_dynasty_web/) — greps against the wrong path read as
phantom. COMPACTION HAZARD: cc post-compaction recaps have
misstated rulings — disk docs are the memory; re-read after any
compaction.

=== OPEN COLD ===
Gate HEAD read-only via cc: `git rev-parse HEAD` (expect
1d8b4e1e71806f04ca070ffc7a2632048d81aa48), `git status --porcelain
| grep -v '^??'` (expect EMPTY — clean tree). Attach:
claude/fight_model_v1_0.md, claude/fight_model_p3_scope_v0_1.md,
claude/fight_model_v1_design.md, and CLAUDE.md's C16+C17 blocks.
Then STOP. First moves, in order: (1) architect reads the scope
doc's status addendum + contract verbatim; (2) P3-2 read-only
diagnosis prompt (every fe.simulate_fight caller, verbatim, plus
world-gen timing baseline); (3) Van ratifies the P3-2 execution
prompt; (4) consolidation proceeds gated.

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
