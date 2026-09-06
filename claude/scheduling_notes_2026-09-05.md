# Scheduling / career-agent model — design notes (2026-09-05)

Status: DESIGN NOTES, Van-initiated mid-GENERATOR1 ("i am interested in
different personality having different wait times... once the fight is
picked, there is a fight camp... loser has a potential consecutive
stacking lock out"). Not scoped, not ratified. Candidate arc name:
SCHEDULING1. Sequenced AFTER P3-6 (does not touch the fight engine, but
changes fight frequency → records, rankings, record-book feel — needs a
measured baseline first). MATCHMAKING1's booking census is this arc's
Gate 0.

## What exists today (evidence, 2026-09-05)

- Injury system wired end-to-end: durations, weekly recovery ticks
  ("[RECOVERY] <name> cleared" per advance_week in harness logs),
  medical-staff recovery reduction (C22 filing).
- Booking lead-time queue: fights matched weeks ahead of their event
  ("LEAD-TIME QUEUE ... → Cage Dynasty 64 (-2w)").
- Contracts count fights ("N fights left" on roster).
- Personality generated per fighter, wired to in-cage tendencies (C24).
- NOT present (no evidence anywhere): offer-patience logic, camp-length
  model, post-loss lockouts, strategic AI healing decisions. The clocks
  exist; the decision layer is at zero.

## Van's design (stated 2026-09-05)

1. OFFER PATIENCE BY PERSONALITY. Different personalities wait
   different lengths to pick the "best" offer for them. Architect
   mapping onto existing personality types: Warrior/Hungry = take
   short-notice fights (Cinderella-story supply); Calculated/Political
   = hold out for money/rank (ducking narratives, frustration arcs).
   "Best offer" should be personality-weighted too (money vs rank vs
   revenge vs activity).

2. FIGHT CAMPS. Once a fight is picked, a camp runs before the fight:
   - Top level: 8-10 weeks, maybe 12 → fewer fights per year at the
     top. This is a PACING LAW: elite champions land at 2-3 fights/yr,
     matching real MMA and making title fights scarce events.
   - Lower levels: 6-8 weeks → prospects stay active (4-6/yr).
   - (Open: does camp interact with the training system — camp = the
     training focus for those weeks? Does a camp target the specific
     opponent? Ties to gameplan/coach systems.)

3. LOSS LOCKOUTS. Loser gets a potential lockout that STACKS with
   consecutive losses, running CONCURRENT with any injury (not
   additive). Models commission suspensions + psychological reset.
   Manufactures comeback arcs (the two-KO fighter disappears for
   months and returns as a story).

4. WINNER FLOW. Winners can start selecting the next opponent
   immediately; their pick time is governed by their patience (item 1).

5. SMART AI HEALING. AI should have the option to wait and heal when
   needed — "but smarted up." Architect shape: an OPPORTUNITY-VALUE
   decision, not a rule: title shot on the table → wait and heal fully;
   prelim fighter who can't afford to sit → takes the fight at 80%,
   accruing long-term damage (emergent tragedy). Keyed off injury
   severity × opportunity value × personality (Hungry fights hurt,
   Calculated doesn't).

## Constraints (architect, stated to Van)

- ROSTER LIQUIDITY IS THE HIDDEN CONSTRAINT. Camps + lockouts +
  patience all remove supply from the matchmaker at once. Mis-tuned,
  cards go thin / events fire empty (zero-fight events already seen in
  harness logs, unexplained). Gate 0 = MATCHMAKING1 booking census:
  fights/fighter/year by tier, empty-card rate, orphaned contenders —
  measured BEFORE and AFTER.
- Balance-touching at the population level (records, rankings, title
  frequency): own arc, before/after per-tier activity measurement,
  forward-only, stop-before-commit, full method.
- Per-division event cadence must be checked against camp lengths —
  9 divisions × fewer fights/fighter needs enough events or cards
  thin out.

## Open design questions for the arc's spec (when scoped)

- Patience table: weeks-to-accept by personality type; what makes an
  offer "best" per personality (money/rank/revenge/activity weights).
- Camp length table by tier/level; whether camps interact with
  training focus and opponent-specific prep.
- Lockout schedule: base weeks per loss, stacking rule for consecutive
  losses, finish-loss vs decision-loss distinction, cap.
- Healing decision: severity × opportunity × personality formula;
  what "fighting hurt" costs (temporary stat down vs long-term).
- Player-side parity: does the player face the same camp/lockout
  rules? (Presumably yes — "3 fights left" contracts already bind.)
- Interaction with amateur/prospect activity rates (prospects should
  fight often — that is their development).

## Item 6 — Burnout / time off (Van ruled 2026-09-05)

Van ruling: YES, personality-driven, folded into SCHEDULING1.
Companion filing to claude/life_sim_notes_2026-09-05.md.

FATIGUE ACCUMULATOR (one new stored field). Rises with training
intensity + fight frequency; falls with rest weeks. Not visible to
opponents as a scoutable stat by default — it's private state that
DRIVES time-off requests via the SCHEDULING1 clock, and its shape
is a design choice for the arc's spec (rise/fall rates, cap,
zero-floor, interaction with camp intensity).

TIME-OFF REQUEST = SELF-IMPOSED LOCKOUT on the SCHEDULING1 clock.
Once a fighter's fatigue crosses their personality-derived
threshold, they exit the offer pool for N weeks (also personality-
derived). Winners returning from lockout re-enter with fatigue
reset to zero (rest works); losers whose lockout was extended by
injury (running CONCURRENT with fatigue lockout per Item 3) re-
enter when the LATER clock expires.

PERSONALITY MODULATION (both threshold AND expression):
- Warrior: NEVER asks for time off. Fatigue accumulates unchecked
  → injury risk rises silently → the two-KO tragedy arc (short
  career, big finishes, then the wall). No news event fires; the
  fighter just gets hurt.
- Political: DEMANDS PUBLICLY. Fatigue-triggered lockout arrives
  with a news feed story ("[FIGHTER] needs time to focus on
  family, sources say"). Camp reads it in the news, not from the
  fighter. Public expression = maximum drama.
- Calculated: SCHEDULES post-fight. Fatigue lockout fires quietly
  after a fight, no news, standard cooldown extended by the
  fatigue amount. Predictable, no story friction.
- Hungry: TRAINS THROUGH the fatigue signal. Ignores the threshold
  during the ascent; burns bright; eventually crashes hard when
  fatigue caps and forces an injury event. The "meteor" archetype.
- Competitor: normal threshold, normal expression. Baseline.

PED/DRUG EVENTS DEFERRED (Van, conflicted on tone). The SUSPENSION
MECHANIC ships free with SCHEDULING1 lockouts — the clock is
already generic, PEDs would just be another lockout source. The
SCANDAL LABEL (specific PED accusations, drug-test failures) is a
later opt-in. Tone-safe alternative filed under LIFE_SIM notes:
generic "personal issues" events (missed camp, unprepared, six
weeks gone) driven by the same personality mapping — same clock,
same drama, no syringes.

Design gates for whichever session picks this up:
- Fatigue accumulator: rise/fall rates by intensity band; cap;
  interaction with camp length; visible-to-player-vs-scouted.
- Personality threshold + duration tables per type.
- News copy pool for Political/Calculated public/quiet expressions.
- Injury-risk multiplier curve for Warrior/Hungry fatigue-through-
  wall archetypes (needs coordination with the injury system's
  existing severity distribution).
- Player-side parity: player faces the same rules (presumably yes
  — the "3 fights left" contracts already bind the player).
