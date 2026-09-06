# Gameplan / fight-camp loop — design notes (2026-09-05)

Status: DESIGN NOTES, Van-approved shape 2026-09-05 ("sounds good to
me... i think we have more written than you think, but in the end, i
think i like it"). Candidate arc name: GAMEPLAN1. Companion to
claude/scheduling_notes_2026-09-05.md (camps) and
claude/life_sim_notes_2026-09-05.md (FIGHTNIGHT1 pointer).

VAN'S CAUTION AS ARC LAW: "we have more written than you think."
Gate 0 is a full inventory census of existing gameplan/camp/tactics
code BEFORE any design lands — the coach-system rule (never rebuild
what exists) applies. Known-existing at filing time: AI plan menu
(ai_gameplan_for_style — SUBMISSION/TAKEDOWN/CLINCH/AGGRESSIVE/
DEFENSIVE/MEASURED/GNP/BALANCED, live since C27), tendency system
(style+personality → aggr/range, C24), IQ-execution drift (fighters
abandon plans, C24/C32), personality→plan resolution (C39),
aggression-drain coupling (D19), fight_camp.html page, dormant coach
infra. Known-dead: Gameplan.finish_seek (buried-findings chain) —
revive-or-delete decision inside Gate 0.

## The loop (Van-approved shape)

1. PLAYER PLAN CHOICE (pre-fight): player picks from the SAME plan
   vocabulary the AI uses, routed through the same resolution path.
   UI + one wire, no new engine. The choice screen shows one
   judgment line from existing machinery ("Torres has the IQ to
   stick to this" / "he'll abandon this the first time he gets
   tagged") — north-star compliant, a free read off IQ+personality.
2. CAMP LEANS INTO THE PLAN (inside SCHEDULING1): camp weeks tilt
   training toward the plan; camp length (8-12wk top / 6-8 lower,
   Van's ruling) × relevant per-family coach quality feeds a plan-
   EXECUTION modifier (via the existing dial_execution shape).
   Short-notice fight = fighting on instinct. Chain: what you chose
   × how long you had × who prepared him.
3. FIGHT NIGHT: plan expresses through existing tendencies; IQ-drift
   is the drama (low-IQ Warrior abandons the plan — already
   simulated). FIGHTNIGHT1 (between-round instructions) layers on
   later.
4. AFTERMATH AS INTEL: fights record the plan used; scouting later
   surfaces opponents' plan histories ("expect early takedowns").
   Plans become predictable/counterable — the intelligence war.
   Rides the amateur/scouting arc.

## Gates (arc law)

- GATE 0 — INVENTORY + PLAN-OUTPUT CENSUS: what does each plan label
  measurably change in fight output TODAY (TD attempts, sub
  attempts, pace, method mix per plan)? Same harness family as
  STYLE-OUTPUT1 — one instrument, two filings. A plan that changes
  nothing is a placebo button and gets wired or cut before any UI.
  finish_seek ruled here.
- BALANCE GATE — NO DOMINANT PLAN: per-plan win rates across
  matchups; no plan above threshold pool-wide, or the choice
  collapses into a ritual click.
- Plan effects are BALANCE-TOUCHING: full method, before/after,
  stop-before-commit.

## Sequencing

- Gate 0 census + Layer 1 (choice screen): post-P5-C (no plan-delta
  measurement while finish knobs are moving).
- Layer 2 (camp link + execution modifier): inside SCHEDULING1,
  with per-family coach revival (DEVELOPMENT1) as its quality input.
- Layer 3 (intel): amateur/scouting arc.
