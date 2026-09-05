# FIGHT MODEL P3 — IMPLEMENTATION SCOPE v0.1 (2026-09-03)
# STATUS: P3-0/1 SHIPPED+DEPLOYED; P3-2 (C18), P3-3 (C19), P3-4a
# (C20), P3-4b (C21), P3-4c (C22), P3-4d (C23) SHIPPED; P3-4e (C24)
# SHIPPED DARK (both flags False on disk — bridge measurement (d)
# tripped, (b) instrument failed); next: 4f/4g remainder + P3-5
# calibration. Updated 2026-09-04 (C24 dark ship).

Disk copy canonical; this project copy is backup. Implements the
ratified contract claude/fight_model_v1_0.md on the fi chassis.
Signal 1 GIVEN (Van, 2026-09-03; S1-S4). Gated staircase.

## DOCKET P3-0 — C15 DOCS COMMIT — SHIPPED (rode with C16)

## DOCKET P3-1 — FAIRNESS & SCORING — SHIPPED + DEPLOYED

C16 e54d3cc + C17 1d8b4e1 (#22 fix, 227/227 scorer proof). Deployed
on proof 2026-09-03. **DEPLOY FREEZE ACTIVE (S2)** — PA runs C17.

## DOCKET P3-2 — CONSOLIDATION — SHIPPED as C18 53077ad

world_init → fi explicit config; fe.simulate_fight retired-not-
deleted; bridge DEC 45.1→29.2% (in-band). S4(a).

## DOCKET P3-3 — CONTEST REBUILD — SHIPPED-STRUCTURAL as C19 4405884

One P_c form; D13 composites; upsets retired; initiative dampened.
S5: magnitudes to P3-5. F4 FIXED (boxing +2.13), F3 SD ALIVE
(+3.94), F9 GONE, F8 preserved, F6 direction fixed. F10 ACTIVITY
TAX filed (cardio channel doubled).

## DOCKET P3-4 — STATE, WINDOWS, SUBS, AGGRESSION, POWER

### 4a LEVER TWO — SHIPPED as C20 cb1dcd8 (S6)
Cardio-owned regen S_r=0.5; fatigue routing (fi:623/625 bypass
closed). T1_R3 DEBT PAID (14.12→29.2). B9's T2 assignment refined-
false on the defining touched-zero instrument; T2 → P3-5. Inputs
forward: cardio +25.25pp; speed −16.5pp; POP ~50% DEC vs EP1 99%.

### 4b WINDOWS + CARRY-OVERS — SHIPPED as C21 304ceff (2026-09-04)
window_registry.py: 10 rows (7 restated mechanics + elbow_cut_writer
+ doctor_cut_stoppage + sprawl_punish_attack). Byte-equivalence
700/700 vs pristine C20 worktree; all no-op proofs MD5-identical.
CUTS RETURN (43/700 fights; POP rate ~2× fe baseline — CUT-RATE
flagged to P3-5). Sprawl-punish live (10.5% of fights, Δwin 0 at
×1.25 — P3-5 dials). Heat socket ready (level 80 → +15pp finishes;
zero live callers). Commentary gains log_window_event (12 hooks,
narrative/commentary.py — live path). Filed: karate_patience cross-
module dep; heat composure/aggression dead-in-fe; new method string
"TKO (Doctor Stoppage - Cuts)" needs downstream pattern check at
P3-6. Census: outputs/sm1/fight_model/p3_4b/census.md.

### 4c SUBMISSION MODEL — SHIPPED as C22 c4266a0 (2026-09-04)
§5a REPLACEMENT (no toggle): tap/sleep/injury split via heart-
modulated tap threshold + refusal band; choke→sleep ("Technical
Submission"), joint_lock→injury ("Submission (Injury - <sub>)")
with severity by overshoot (MODERATE/SEVERE/CAREER). New sub_escape
contest class (P_EVEN=0.10, EDGE20=0.28, S≈3.96 — P3-5 ratifies the
"+20 on primary vs both-stats" convention). Chin + composure wiring
FLIPPED ON (Van-approved via C22 paste on verify.md T4 defining-
instrument readings: HEART sub-loss −21.5pp ~10σ; CHIN kd_mean
−18% rel; COMPOSURE rock_duration −32% rel; N=1000/cell, positive
controls proven-discriminating). FIVE RESURRECTIONS COMPLETE —
heart/chin/composure ALIVE on defining instruments. FIX A 3-tuple
unpack (fe fallback + test_sub_sim). FIX B method routing: all
three sub forms → SUB at gb Path A, gb Path B, awards.canonical_
specialty_method (pre-fix, sleeps collapsed to DEC in AI fights and
persisted as truncated "Technical " in player history). FIX C
injury persistence: GameBridge._sub_injury_hook → real
systems.injury API, wired Path A + Path B (NOT MC odds — estimator
would multi-count). Gates G1 18/18 routing, G2 bridge smoke
(persisted injury Δ=1, real fields), G3 EP1_500 flags-ON (127 subs:
tap=100 sleep=7 injury=20; hook fires match), G4 syntax/import.
RIDERS: legacy escape fields dead-in-legacy-only (delete when
_legacy_process_submission_progress retires); pre-existing Path A
KO/TKO specialty truncation "KO (Head K" (gb:17931 [:10] slice) —
cleanup at next natural gb touch or P3-6 UI nits; pre-gen history
sim does NOT persist injuries (world_init owns no InjurySystem —
fresh saves start clean, accepted design, revisit at INJURY1);
fight_history stores plain "SUB" for all three flavors — flavor
lives in commentary/watch page; whether history rows should show
choke-out/injury distinctly is a D14/D16-batch display decision.
Verify artifacts: outputs/sm1/fight_model/p3_4c/verify/.
### 4d POWER (D7) — SHIPPED as C23 (2026-09-04)
19th stat POWER split from STRENGTH. Striking-damage lanes at
fe:2833/2837 + flash-KO at fi:1328 now read attacker.power under
FI_POWER_WIRING_ENABLED=True (flag ON on disk, Van-approved per
G2 separability). Strength keeps grappling-physicality (throws/
slams/clinch break/escape assist). World-gen un-drops the pre-4d
dropped `power` key at world_init:3068 and applies style-informed
offset via canonical POWER_STYLE_OFFSET (core.types.py, 28-entry
dict keyed by both display names AND enum-string keys; single
source of truth for world_init + game_bridge derivation). Load-time
derivation for pre-4d saves at game_bridge._make_fighter_attrs:
`power = clamp(strength + style_offset + crc32(fid)_noise[-3..+3])`,
FORWARD-ONLY (no write-back to _fighter_data). MEASURE 1 verbatim:
OVR wobble |ΔOVR| mean=0.304, max=1.0, only 1/289 fighters shift
≥1 point — imperceptible. Training + profile + compare + tale-of-
tape all render Power. Gates G1-G6 all PASS (G1 MD5 byte-identical
flag-OFF; G2 POWER+20 → KO+TKO +3.0pp ±2.4pp ALIVE; STRENGTH+20
FLAT; G3 derivation deterministic+no-write-back; G4 zero remaining
5-physical enumerations in web-tree production code; G5 UI smoke;
G6 no god-stat). D15 POSITION CENSUS delivered as ride-along at
outputs/sm1/fight_model/p3_4d/position_census.md.

### 4e AGGRESSION (D8) — SHIPPED DARK as C24 (2026-09-04)
Machinery present, both flags False on disk. TENDENCY function
(styles.tendency_for_fighter, pure function of personality × style,
reload-stable by construction), 4-rule circumstance table (R1
behind-on-cards / R2 chin-vs-power / R3 opponent-gassed / R4
cruising), FIGHT_IQ execution lane (rock-triggered drift; ≥80
elite composure blocks 100%). BURIED FINDING: FighterRecord has
no baseline `fighting_style` attribute; style lives in
`_fighter_data['style']`. Pre-C24 AI gameplans were 100% None
since GAMEPLAN-AI-SELECT1 (bridge-scale measurement: 19026/19026
None OFF; 26.4% None + 73.6% real presets ON). G1 byte-identical
OFF (`b6f7dac91ce983f4449152445477488f`); G2 all 4 rules fire
correctly (dial + commentary); G3 IQ execution ALIVE on defining
instrument at N=1000 (IQ 50 drift 7.8%, IQ 90 drift 0.0% —
elite composure gate holds); G4 tendency table 292 fighters
deterministic 20/20 repeat-load stable. **BRIDGE-PATH DECISION
GATE (from C24 spec) fired DARK:** (b) instrument failed
(_engine_result not persisted on Path B fight dict → td/sub per
style all n=0, cannot verify grappler-vs-striker differentiation
direction); (d) win-rate swings Wrestler 55%→27% (Δ=−28.3pp) and
Striker 60%→33% (Δ=−26.7pp) both on n=20 OFF — collapses in the
strict architect-intent reading. Filed to P3-5 with numbers.

### 4f/4g REMAINDER — SUB MODEL follow-ups, POWER dial follow-ups,
future POSITION-VALUE rebalance (D15 step 2) — as they arise.

## DOCKET P3-5 — FINISH MODEL + SINGLE CALIBRATION (LAST)

§6 five parts + leg-kick dial (~1%). One pass, final physics, §9.
FREEZE LIFTS on green. CALIBRATION LIST:
1. Contest constants (P_EVEN/S), K_SPEED_INIT, speed-worth.
2. T2 remainder (touched-zero; drain-side/activity economy).
3. STAMINA FLOOR question (Van rules): contest composites → 0 at
   0 stamina vs damage's 0.5 floor; candidate ~0.4-0.5 floor,
   "exhausted but dangerous."
4. JUDGE-WEIGHT AUDIT (TD 8.0 vs strike 1.0; new physics lands
   more TDs — measure decision skew).
5. td_distance flat-slope diagnostic.
6. POSITION-VALUE DIFFERENTIATION (D15 step 2): per-position
   damage mults (flat ×1.25 today), initiative bonus, control
   nuance.
7. CUT-RATE + FREQUENCY ONLY (rate calibration; the full cut-
   system reality audit is CUTS1, post-arc). Reality anchor:
   ~1-3% of real MMA fights END on cuts, but cuts OCCUR far more
   often than they stop fights — occurrence and stoppage get
   separate targets. POP stoppage measured ~2× fe baseline at
   C21. Sprawl-punish magnitude rides here too.
8. Per-class method mixes + finish knobs against §9.
9. SUB-MODEL DIALS (C22 inputs): tap threshold width, refusal
   band (REFUSAL_WIDTH_BASE — all-MODERATE severity mix today,
   SEVERE/CAREER unreachable at current tuning),
   CHIN_KD_RESIST_SPREAD, COMPOSURE_ROCK_DUR_SPREAD, sub_escape
   S convention, chin damage-threshold (wiring only fires on
   head strikes ≥12 dmg = 4.5% of head strikes), guard+20
   inversion diagnosis (−17pp via select_action routing).
   Before/after instruments: verify.md T4 + gate_tables.md +
   g3_ep1_flags_on.
10. POWER DIALS (C23 inputs): unify the TWO generative models —
    world-gen power = independent tier roll + offset
    (strength-uncorrelated) vs legacy derivation = strength +
    offset + noise (strength-correlated); architect lean: seed
    world-gen from strength like derivation, one model everywhere
    (Van rules). Tier-confound fix if per-style separation should
    be world-scan-visible; enum-collapse offsets (collapsed styles
    derive with the shared enum offset); offset magnitudes.
11. AGGRESSION DIALS (C24 inputs — machinery is dark on disk;
    calibration to flip it on). Fix (b) instrument: persist
    `_engine_result` on the Path B fight dict so per-style
    td_attempts/sub_attempts are measurable at bridge scale.
    Diagnose Wrestler collapse: TAKEDOWN preset applies
    `range_bias=+1` (grapple_weight ×1.20, sub_weight ×1.10) —
    likely over-commits Wrestlers to takedowns, they get sprawled,
    opponent counters; candidate softens the range tilt when
    opponent is a Sprawl & Brawl / high-TDD style. R3 fires
    64.5% on symmetric-cardio fixtures (fixture-specific but
    ubiquitous — trigger too permissive); tighten stamina
    threshold OR require a rock/hurt signal alongside stamina.
    R2/R4 fire rates measured 0% on their fixtures — need real
    calibration data. TENDENCY tilt magnitudes (±1 per axis) may
    be too aggressive when composed with 4-rule adjustments.

## DOCKET P3-6 — ACCEPTANCE + SHIP

Full P2c sweep (19 alive, no god/dead, boxing positive); method-mix
+ DEC green EP1 + POP; new-method-string pattern check in
downstream analytics (now includes C21 "TKO (Doctor Stoppage -
Cuts)" AND C22 "Technical Submission"/"Submission (Injury -" —
G1/G2 proved the three known consumers; sweep the rest); live
playtest on fresh save; deploy on proof. Post-deploy owed: PA
violence monitoring, tierA re-vintage, live-roster check.

D14 UI (Van): attribute-display redesign — fingerprint cards (~5
grouped axes) + STANDOUT/FLAW; full 19-sheet on profile (note: the
existing Scout Report strengths/weaknesses section is the primitive
to grow into); scouting-ranges future system. UI NITS batch: reach
renders as 72"" (doubled inch mark) on fighter profile; Path A
KO/TKO specialty truncation "KO (Head K" (C22 rider); fight-
history method display decision — show choke-out ("never tapped")
and injury finishes distinctly in history rows, or keep plain SUB.

D16 (Van, 2026-09-05) — RANK-AT-FIGHT-TIME: stamp BOTH fighters'
current divisional rank (and champion status) onto the fight record
at resolution time, in live play AND world-gen history sim; display
in Fight History rows ("WIN vs #4 Oscar Torres"). FORWARD-ONLY —
existing saves' past fights show a dash, no backfill; post-freeze
universes get it from birth. Downstream payoff: quality-wins become
computable (HoF, record book, media "never beaten a ranked
opponent", D14 standout lines). Schema change — census the fight-
record shape read-only first. Lands with the D14/P3-6 batch.

## POST-ARC DOCKET QUEUE (D15)

POSITIONS1: fence/cage → front headlock → standing-over-downed →
scrambles-as-windows → back-mount quality.

CUTS1 (Van, 2026-09-05) — CUT-SYSTEM (LACERATIONS) REALITY AUDIT.
P3-5 item 7 covers rate only; this docket covers the system. Scope:
- SEVERITY + LOCATION model: cuts get a location (brow, eyelid,
  bridge, hairline, scalp) and a severity that grows if re-struck;
  location drives stoppage risk (eyelid/brow ≫ scalp) and
  blood-in-eye impairment.
- IN-FIGHT IMPAIRMENT: a cut is not just a stoppage lottery —
  blood-in-eye applies a composite penalty (vision-side striking
  defense/accuracy) via the 4b WINDOW machinery while active;
  cutman quality between rounds shrinks/clears the window.
- IN-ROUND DOCTOR CHECKS: doctor can pause the action mid-round on
  severe cuts, not only between rounds; ref-initiated.
- CUTMAN / CORNER QUALITY: camp or corner rating modulates
  between-round severity reduction — a reason camp quality matters
  in-fight.
- SCAR TISSUE / RECURRENCE: career-persistent cut history raises
  re-open probability at the same location (forward-only data,
  no backfill).
- LEGIBLE DOCTOR DECISION: stoppage is a decision model, not a
  bare probability — inputs are severity, location, round context
  (round 1 vs championship round 5 leniency), title fight, and
  fighter/corner pleading; commentary narrates the inspection so
  the player understands WHY.
Emergent-story payoff: "he's fighting blind through round 5" and
"one more clean elbow ends this on cuts" are exactly the specific,
actionable beats the north star demands.

WEIGHTCUT1 (Van, 2026-09-05) — WEIGHT-CUTTING REALITY AUDIT.
Purpose/timing/consequences/decision, audited against reality.
Exists today (per stale snapshots — live census required):
body_frame 1-10 at world-gen → natural_weight_class; cut-severity
helper (0/1/2 classes below natural); coach advice channel
(hard-cut/outmuscled/aging-cut alerts, 12-wk cooldown); AI class
moves (26-wk cooldown, champions never move); player ±1 class
moves with belt-vacate + fight cancellation.
STEP 1 (read-only, fold into a convenient cc prompt): CONSUMER
CENSUS — does cut severity feed ANYTHING on fight night? Classic
looks-wired risk: a computed severity passed to nothing. The
census answer decides wiring-fix vs system-build.
Audit dimensions:
- PURPOSE: reality's reason to cut is a size advantage in the
  cage; game currently models no fight-night size edge — cost is
  signaled (coach) but benefit absent. Model the edge (frame vs
  frame within class) so the cut is a real tradeoff.
- TIMING: no fight week, weigh-in, or rehydration window exists.
  Candidate: weigh-in event with cut-difficulty roll (frame gap,
  age, camp quality) → drained/normal/strong state into fight
  night.
- CONSEQUENCES: bad cut → fight-night cardio/chin/durability
  penalty (measured, not narrated); MISSED WEIGHT event — purse
  penalty, cancelled or catchweight fight, title ineligibility,
  media story. Forward-only.
- DECISION: class choice becomes a legible tradeoff (size edge vs
  cut cost, aging curve steepens cost); coach advice already
  exists — point it at the real numbers once they exist.
Emergent-story payoff: "missed weight, title shot gone" and "the
drained champ gassed in 3" are north-star beats.

INJURY1 (Van, 2026-09-05) — INJURY-SYSTEM REALITY AUDIT.
Purpose/timing/consequences/decision, filed FROM C22 measurement
(not guesswork). Known-wired (proven): AI-card fights persist
injuries via generate_fight_injury (gb:13898-13930 pattern —
InjurySystem, recovery weeks, medical-staff reduction, news);
C22 sub injuries persist on BOTH paths via _sub_injury_hook (G2:
real injury, real fields, Δ=1); training injuries + champion-
injury-decision page exist; weight-class moves gated on
is_cleared_to_fight. Open questions (audit these):
- Do PLAYER-fight KO/TKO injuries persist? C22 mirrored the
  Path B pattern; a Path A pre-C22 equivalent was never
  confirmed. Measure, don't read.
- LIFECYCLE: medical suspensions after wars (real MMA: mandatory
  30/60/180-day), injuries lingering into next camp (training
  penalties while healing?), re-injury risk on early return,
  age interaction.
- DECISION: fight-through-it vs pull-out choices for player;
  AI pull-outs creating short-notice replacement drama (major
  emergent-story source in real MMA).
- PRE-GEN: history-sim injuries not persisted (accepted design —
  fresh saves clean); confirm this stays intentional.
Emergent-story payoff: "champ pulls out, short-notice challenger
shocks the world" and "he came back too soon and his chin never
recovered" are north-star beats.

Then: scouting-ranges, personality, generator-variety, amateur,
training dockets; PEAK103; PA timing pre-N-lock; A3-b/A3-c.

FIGHTERRECORD-FIGHTING-STYLE (Van, 2026-09-04, from C24 BURIED
FINDING) — small separate cleanup ship: promote `fighting_style`
to a real field on `FighterRecord` (`game_state.py`) with proper
serialization in `to_dict` / `from_dict`. Consequence closes the
"AI plans have been None since GAMEPLAN-AI-SELECT1" defect at
its root; makes the C24 `_fighter_data['style']` fallback
unnecessary. Scope: FighterRecord field + serialization + a
world_init write-side stamp so fresh AI fighters carry the real
field. Should ride before P3-5 item 11's calibration lands so
the AGGRESSION-DIALS work is against a clean lookup.

## STANDING RULES

Fresh date + HEAD gate (HEAD C24 — placeholder, actual sha in
commit message); diagnose read-only
first; single-purpose commits on Van's word; stop before commit;
adjusted instruments prove discrimination; a no-op control cannot
prove life; instruments match the DEFINING instrument; verbatim
over recall; arithmetic sums; docs same turn; never hardcode
saves/fighters; re-read disk docs after compaction; twin gates
decided-share, ≥2 blocks; no wiring-flag flips without a
defining-instrument sensitivity reading in a prior verify pass
(C22 rule a); hook sockets land in the same commit as their
production wire absent a stated scoping reason (C22 rule b —
heat_level is the standing counter-example).

## RULED SCOPING DECISIONS

S1 order · S2 freeze ACTIVE · S3 executed · S4 bridge accepted ·
S5 structural/single-calibration · S6 lever-two word · D14
attribute display (P3-6) · D15 positions three-tier · D16
rank-at-fight-time stamp (P3-6 batch, forward-only) · CUTS1
cut-system reality audit (post-arc) · WEIGHTCUT1 weight-cutting
reality audit (post-arc; consumer census first, foldable as a
ride-along) · INJURY1 injury-system reality audit (post-arc;
filed from C22 measurement) · C22 flag-flip approved on T4
defining instruments.
