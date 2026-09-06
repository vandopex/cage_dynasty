# Life-sim layer notes — MMA Manager feature review (2026-09-05)

Status: DESIGN NOTES from Van's review of MMA Manager (3T Games /
Stepico) features, with rulings stated 2026-09-05. Companion to
claude/scheduling_notes_2026-09-05.md (SCHEDULING1). The finding
that frames everything: that game's life-sim layer reduces almost
entirely to clocks, locks, personality, morale, and a news surface
— four of which Cage Dynasty has, one of which SCHEDULING1 designs.
The features below are mostly LABELS on machinery already planned.

## Van rulings (2026-09-05)

- NO multiple major pro leagues. One pro org; the title stays
  singular and meaningful.
- AMATEUR CIRCUITS: YES. Formalize existing regional amateur pools
  into named circuits with standings and amateur titles. Gives the
  scouting redesign geography and structure (region familiarity,
  grades measured against real standings), fixes tournament-winner
  selection inside a system that finally consumes it, and feeds
  story carry-over ("they met in the Americas final, Week 12").
- TIME OFF / BURNOUT: YES, personality-driven. See scheduling notes
  item 6. One new stored field (fatigue); everything else reuses
  personality, morale, intensity, weekly tick, news feed, and
  SCHEDULING1 lockout clocks.
- PED/DRUG SCANDALS: DEFERRED (tone call). The suspension mechanic
  ships free with SCHEDULING1 lockouts; the scandal label is a
  later opt-in. Tone-safe alternative filed: generic "personal
  issues" events (missed camp, unprepared, six weeks gone) driven
  by personality — same clock, same drama, no syringes.
- PERSONALITY METERS: NO new stored hidden meters. Greed /
  discipline / ambition / happiness behavior DERIVES from the five
  personality types plus existing morale via one derivation table.
  Hidden stored numbers are where looks-wired bugs breed.

## Feature verdicts (architect, discussed with Van)

- Time off / burnout: worth it, cheapest, highest story yield.
  Inside SCHEDULING1.
- Missed weight: worth it — stakes are purse, ranking, opponent
  fury. SEQUENCED BEHIND the WEIGHTCUT1 audit (no drama on
  unmeasured plumbing). Discipline derived from personality.
- Contract greed / purse %: worth it eventually. Popularity already
  exists as the star-power driver; missing pieces are the
  negotiation loop and economy balance. Own small arc (CONTRACTS1),
  after SCHEDULING1 — a fighter demanding 30% only matters once
  fighters control their own careers.
- PEDs: deferred per ruling above.
- Stat decay (theirs: decay toward baseline per neglected
  discipline): design agreed, but Cage Dynasty's own decay is
  currently a READ, not a measurement — DEVELOPMENT1 must verify it
  fires before anything builds on it. Pairs with per-family
  coaches: neglect the grappling coach, watch the GRP family sag.

## Coach revival shape (for DEVELOPMENT1)

Measured fact (C31): the coach system is DORMANT —
COACHES_AVAILABLE=False, worlds generate zero coaches,
_dominant_coach_type always answers boxing_coach off an empty
census. Revival order: (1) census what the dead system already
implements — never rebuild what exists; (2) revive as PER-FAMILY
coaches: striking coach boosts STK-family training gains, grappling
coach GRP, strength & conditioning ATH. The Phase B family map is
the coaching org chart — a hook that did not exist before
GENERATOR1.

## Borrowed idea filed separately

FIGHTNIGHT1 (post-arc): player-issued corner instructions between
rounds. The machinery already exists without a UI: R1-R4 aggression
rules ARE corner calls, read from live scorecards, executed through
fighter IQ (fighters who ignore the corner are already modeled). A
between-rounds choice UI is a layer, not a system.

## Open questions (for whichever arc picks each up)

- Fatigue accumulator: rise/fall rates; interaction with camp
  intensity in SCHEDULING1; visible to player or scouted?
- Personality derivation table: per-type values for patience,
  discipline, greed, time-off threshold, public-vs-private
  expression.
- Amateur circuit count/naming; standings format; amateur title
  lineage feeding pro-side story carry-over.
- Contract model: purse % bands by popularity tier; morale hit
  curve on lowball; AI camp counter-offers.
- Generic "personal issues" event pool: triggers, durations, news
  copy — if Van opts in post-SCHEDULING1.
- parity: does the player face the same fatigue rules? Presumably yes.
