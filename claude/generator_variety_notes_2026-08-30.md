# Fighter-generation variety + trait system — design docket item (2026-08-30)

Status: DESIGN NOTES, Van-initiated ("i want more variety in generation —
some guys are great at some stuff and suck at other stuff"; extended by
Van: "lets not have traits that conflict with stats"; extended by Van:
weight-class tendencies). Not scoped, not ratified. Sequenced AFTER the
STAMINA-MODEL1 design arc. Candidate arc name: GENERATOR-VARIETY1
(trait rework + weight-class tendencies are part of the same arc — one
generation function, one before/after measurement).

## Measured basis (Gate 1 session, 2026-08-30)

- Tier-band generation (world_init tier_ranges: every stat drawn
  independently within the fighter's tier band) produces population-level
  cardio×recovery Pearson r = 0.7531 (n=290, world #1; mechanism
  source-verified). Off-diagonal archetypes (HL/LH at ≥85/≤65) occur at
  ~0.10% each — 5 found per ~4,900 fighters across 17 worlds.
- Van's ratified cardio ruling requires marathon-vs-burst archetypes to
  be POSSIBLE; the current generator almost never creates the bodies.

## Problems this one root causes (all separately filed)

1. Archetype scarcity (this doc; Gate 1 pool evidence).
2. Style-label vs stats incoherence ("Striker" with TD 91/TDD 93 —
   playthrough notes item 11) — style assigned independently of stats.
3. Trait-text vs stats mismatch (three sightings, playthrough notes
   item 15) — trait flavor rolled without consulting the sheet.
4. Scouting-redesign undermining: if stats ≈ tier, OVR tells all and
   scouting has no skill component (amateur notes doc's fog-of-war
   design needs spiky profiles to be worth scouting).
5. Weight-class sameness: a 135er and a 265er are statistically the same
   animal — likely root of the record-book oddity (strawweights leading
   KO lists, playthrough notes item 8).

## Generation direction (discussed with Van, architect sketch — Van: "love this")

Layered generation, NOT full independence (real athletes correlate;
r→0 is as fake as r=0.75):
- Keep a shared quality core (tier) — overall level still real.
- Stat FAMILIES correlated internally, loosely coupled across:
  athleticism (strength/speed/cardio), striking skills, grappling
  skills; chin / heart / recovery as near-independent lotteries
  (durability and gas don't follow skill in real MMA).
- SPECIALIST LAYER: ~10-15% of fighters get a build template — spike
  1-2 stats hard, dump 1-2 (respecting tier caps). This manufactures
  burst fighters, glass cannons, cardio machines with pillow hands.
- DERIVE style label + trait text FROM the rolled build (template =
  archetype = label = trait). Fixes problems 2 and 3 for free.

## Weight-class tendencies (Van-directed 2026-08-30)

Van's ruling: divisions should have physical tendencies — bantamweights
GENERALLY faster, better cardio, weaker; heavyweights stronger, slower,
less cardio — "BUT not impossible" to break type.

Design shape: SHIFTED DISTRIBUTIONS, NOT CAPS. Per-weight-class mean
offsets on the physical stats (speed/cardio center higher and strength
lower as weight drops; reversed going up; graded across the 9 classes),
with spread wide enough that tails overlap. A fast heavyweight exists,
is rare, and is therefore NOTABLE — free scouting/story material, and
badge/trait-worthy ("Freak Athlete" as a computed badge candidate).

Expected bonuses beyond flavor:
- Should organically fix the strawweight-KO-leader oddity: with strength
  and chin distributed by class, HW becomes KO-land and small divisions
  volume/decision-land WITHOUT engine changes — matching real MMA finish
  distributions.
- Cross-division surfaces (record book, compare, any future P4P feel)
  read believably.

Measurement note: balance-touching PER DIVISION — the arc's before/after
gate needs per-division finish-rate tables, not just the pool rate.

## Trait system rework (Van-directed 2026-08-30: no stat-conflicting traits)

Principle: conflicts are prevented by CONSTRUCTION, not by checking —
every trait is downstream of the thing it describes. Four trait kinds,
each with its own source of truth:

1. IDENTITY TRAITS — assigned by the build template at the same roll
   that shapes the stats. "Knockout Artist" is the NAME of the template
   that spiked power and dumped chin; one roll, one truth, conflict
   impossible.
2. COMPUTED BADGES — never stored; pure functions of the current sheet,
   derived at display time ("Durable" = chin≥85 & recovery≥80). Always
   true when shown, and LOSABLE: an aging fighter's chin eroding past
   the threshold silently drops "Iron Chin" — free storytelling and a
   scoutable signal (north-star compliant).
3. EARNED TRAITS — written by career events, not dice ("Comeback Kid":
   won N fights after being badly hurt; "Spoiler": upset wins over
   ranked opponents; "Big-Fight Fighter": title-fight record). History
   is the receipt; cannot conflict with anything. Highest emergent-story
   value — players watch these get earned. Record book already tracks
   most inputs.
4. BEHAVIORAL QUIRKS — tendencies, not capabilities ("slow starter",
   "headhunter", "fades in hostile crowds"). Random assignment is safe
   here because they claim nothing about ability; this is where dice
   keep their job and flavor-variety lives.

Guardrails (write into the arc spec):
- NO DOUBLE-DIPPING: if the template spiked power, the trait adds NO
  hidden damage bonus — stats are the mechanism, the trait is the
  label. Mechanical trait effects allowed only where stats cannot
  express the behavior (mostly bucket 4). Same principle as the ratified
  cardio-channel rule.
- VALIDATION INVARIANT: every STORED trait carries a predicate over
  stats/history; generation-time and post-mutation assertion that every
  fighter passes. Turns "no conflicting traits" into a measurable,
  cc-testable invariant, not an intention.
- Migration forward-only: old saves keep old traits; new worlds get the
  new system.

## Sequencing rules (architect, stated to Van)

- AFTER the stamina design arc ships and is measured. Wiring cardio is
  "fix the engine"; variety is "feed the engine better inputs" —
  reversing the order destroys before/after attribution.
- BALANCE-TOUCHING: population-distribution change moves finish rates,
  upsets, decision rates. Own arc, before/after population-level
  measurement (Tier-B-style extraction pre/post, PER DIVISION for the
  weight-class tendencies), forward-only (new saves only),
  stop-before-commit, full method.
- Amateur-circuit generator should get the same treatment in the same
  arc (or an explicit decision not to) — scouting design sits on top
  of amateur generation.

## Open design questions for the arc's spec (when scoped)

- Target population r for cardio×recovery (and per-family r values).
- Specialist fraction and template list (which archetypes exist, per
  weight class? HW burst-KO artists more common, FLW cardio machines?).
- Per-class offset table: which stats shift, by how much, per division
  (graded across 9 classes); how offsets interact with tier bands and
  the 20-100 stat bounds.
- Whether tiers keep current ranges or widen at the extremes.
- Interaction with Chin/Heart trainability question (training notes doc,
  parked): fixed-trait lotteries pair naturally with scout-for-it design.
- Trait taxonomy details: which existing traits map to which of the four
  kinds; badge thresholds; earned-trait trigger list; quirk pool size.
- Whether computed badges appear in scouting with fog (scout reports a
  badge probabilistically before stats are known — ties to amateur
  redesign).
