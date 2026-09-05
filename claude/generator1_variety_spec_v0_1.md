# GENERATOR1 — VARIETY BUILD SPEC v0.1 (RATIFIED 2026-09-05)

Status: RATIFIED by Van 2026-09-05, all §9 defaults accepted as ruled.
Architect draft built from Van's August rulings
(claude/generator_variety_notes_2026-08-30.md — NOTE: that doc exists
only in the Claude project, never committed to the repo; it enters git
alongside this spec in the arc's first docs commit) and the GENERATOR1
Phase 1 census (outputs/sm1/generator1/census/report.md, run at C33
2dfb847). Sequencing already ruled: GENERATOR1 lands between P5-B4
(shipped, C33) and P5-C, so calibration runs once against the final
population. Balance-touching: full method — read-only diagnose, staged
gates, stop-before-commit, forward-only (NEW WORLDS ONLY; existing
saves keep their fighters and their hash-derived stats untouched).

Every number in this spec is a PROVISIONAL DEFAULT with its rationale
attached. Van ratifies or overrides per decision point (marked ⚖ VAN).

---

## 0. WHAT THE CENSUS PROVED (the inputs to this design)

- One tier band drives all 18 rolls → every attribute pair correlates
  r = 0.69–0.90 (strength×cardio 0.72). Every fighter is the same
  vector, scaled. Archetypes (cardio-machine/glass-chin, one-punch
  gasser) occur at ~0.1% — effectively never.
- Style is assigned from country/camp, never from stats. Measured
  signature deltas ±0.4–3.8 on SD~15 — a "Wrestler" is not measurably
  better at wrestling than the pool.
- Amateur→pro graduation DISCARDS all 15 rolled amateur attributes and
  all traits; post-graduation stats are md5-seeded random. The amateur
  generator also lacks 4–5 canonical stats and never runs the canonical
  remap.
- height/reach/stance/numeric-weight rolled and dropped. Dormant
  fallback generator (game_state._generate_fighter) rolls no combat
  stats.
- Personality pipeline: fully wired (the one clean path — do not touch).

---

## 1. LAYERED GENERATION (the core rebuild)

Replace "one tier band → 18 independent draws" with a three-layer
variance decomposition. Per fighter:

    stat = clamp(20, 95,
        TIER_CENTER            # shared quality core — one draw
      + CLASS_OFFSET[stat]     # weight-class shift (§3) — constant
      + FAMILY_OFFSET[family]  # one draw per family, N(0, σ_fam)
      + STAT_OFFSET            # one draw per stat,   N(0, σ_stat)
      + TEMPLATE_MOD[stat])    # §2, only for template fighters

Families (⚖ VAN — exact mapping of all 19 canonical stats to families
is a Gate 0 census task for cc; the architecture is ratified here, the
mapping table in the exec spec):

- ATHLETICISM: strength, speed, cardio (power inherits from strength
  via D18 — no separate roll, no separate offset; one mechanism).
- STRIKING SKILLS: the striking-technique stats.
- GRAPPLING SKILLS: the grappling-technique stats.
- FIGHT BRAIN: fight IQ / composure-class stats (if present as rolled
  stats — Gate 0 confirms).
- LOTTERIES (no family, fully independent draws): chin, heart.
- RECOVERY: independent draw with ONE weak coupling term to cardio
  (target r 0.30–0.40; see §1b).

### 1a. Provisional magnitudes and why

Current per-stat SD ≈ 15 (variance ≈ 225). Keep TOTAL spread the same
(the game's 20–95 scale and every downstream tuning assumes it) and
re-split it:

- σ_tier ≈ 8.5 (variance ≈ 72) → cross-family r ≈ 0.32
- σ_fam  ≈ 7.5 (variance ≈ 56) → within-family r ≈ 0.57
- σ_stat ≈ 10  (variance ≈ 97)

MEASURABLE TARGETS (the gates test these, not the sigmas):
- cross-family r: 0.25–0.40
- within-family r: 0.50–0.65
- lottery stats vs anything: r < 0.20
- cardio×recovery: 0.30–0.40
- OVR mean per tier: unchanged within ±2 (the quality core is
  preserved; variety must not silently raise or lower world quality)

⚖ VAN: ratify the r-bands (the sigmas are cc's to derive and may move
to hit the bands — bands are the contract, sigmas are implementation).

### 1b. Chin/heart/recovery as lotteries

Chin and heart: pure independent draws, tier-independent center
(mean ≈ pool mean), FLAT across weight classes. Durability and will
do not follow skill or size in the design — they are the scout-for-it
stats and the story stats.

Recovery: independent draw + weak cardio coupling to land r 0.30–0.40
(down from 0.75). Not 0: the marathon-vs-burst archetype should be
FINDABLE, not the norm. Estimated effect at r≈0.35: high-cardio/
low-recovery (or reverse) tails at ≥85/≤65 rise from ~0.1% to roughly
1–1.5% of the pool — ~3–4 per 280-fighter world instead of ~0.3.
(Estimate, not promise — gate measures it.)

---

## 2. SPECIALIST TEMPLATES (identity layer)

### 2a. Fraction

12% of generated fighters (⚖ VAN — Aug ruling said 10–15%).
At ~280 fighters/world: ~34 template fighters, ~2–4 per division.
Every division has a name-brand freak; freaks stay notable.

### 2b. Template list (⚖ VAN — my proposed 8)

Each template = stat mods + IDENTITY TRAIT (the template's name IS the
trait — one roll, one truth, conflict impossible) + style implication.

| Template | Spikes | Dumps | The story it makes |
|---|---|---|---|
| Knockout Artist | power ++, strength + | cardio −− | one-punch gasser: land early or drown |
| Glass Cannon | power ++, speed + | chin −− | lives and dies by the sword |
| Cardio Machine | cardio ++, heart + | power −− | pillow hands, drowns you in deep water |
| Grappling Savant | grappling family ++ | striking family − | one-dimensional mauler |
| Technician | striking family ++, fight IQ + | power − | precision over violence, wins on craft |
| Granite Brawler | chin ++, heart + | speed − | walks through fire, can't be hurt, can be outrun |
| Freak Athlete | athleticism family ++ | both skill families − | all tools, no craft — the raw prospect |
| Submission Wizard | submissions/guard ++ | takedowns −, striking − | wants to be on his back; dangerous everywhere the fight goes to the mat |

Magnitudes: spike ++ = +12..+18, + = +6..+10; dump −− = −12..−15,
− = −6..−10. Applied before clamp.

### 2c. Class flavor

Template pick weights: uniform base, ×2 for class-flavored matches
(Knockout Artist / Granite Brawler ×2 in the heaviest 3 classes;
Cardio Machine / Technician ×2 in the lightest 3). Not exclusive —
a flyweight Knockout Artist exists and is a headline.

---

## 3. WEIGHT-CLASS TENDENCIES (shifted distributions, NOT caps)

CLASS_OFFSET applies to exactly three stats — speed, cardio, strength
— graded linearly across the 9 classes:

- speed:   +6 (lightest) → −6 (heaviest)
- cardio:  +6 (lightest) → −6 (heaviest)
- strength: −6 (lightest) → +8 (heaviest)

Power inherits the strength shift via D18 (strength-seeded) — no
separate power offset; one mechanism, one lever. Chin FLAT (§1b):
the HW-KO-land / small-division-decision-land gradient should emerge
from power alone; if the per-division finish gate shows the gradient
is too weak, a chin offset is the NEXT lever, added on measurement,
not preemptively. Recovery flat. All skill stats flat.

⚖ VAN: ratify magnitudes. (Strength asymmetric +8 at top because the
real-world strength gap up the scale is larger than the speed gap
down it, and because power/finish gradient hangs off this number.)

---

## 4. STYLE DERIVED FROM THE BUILD

generate_style_for_fighter(country, camp) loses style AUTHORITY.
New rule: style = argmax over the rolled profile (family scores +
signature stats); template fighters get the template's implied style.
Country/camp survive as TIEBREAK flavor only (regional character
persists when the body is ambiguous).

This closes census finding #2 by construction — the label describes
the body because the body picks the label. Same principle as the trait
rework: conflicts prevented by construction, not detected by checking.
C31's bridge preference for record.fighting_style now carries a label
that is true.

Gate: per-style signature-stat delta vs pool mean must be ≥ +8
(currently ±0.4–3.8, i.e., invisible; +8 ≈ half an SD, reliably
visible in play and in the record book).

---

## 5. TRAIT SYSTEM (GENERATOR1 ships kinds 1–2; kinds 3–4 deferred)

- KIND 1 — IDENTITY TRAITS: template names, assigned at the roll (§2).
- KIND 2 — COMPUTED BADGES: never stored; pure functions of the
  current sheet, derived at display time, LOSABLE with aging. Starter
  set of 6 (⚖ VAN — thresholds at 85 ≈ top ~4% of a stat):
  Iron Chin (chin≥85) · Heavy Hands (power≥85) · Gas Tank (cardio≥85
  & recovery≥75) · Warrior Heart (heart≥85) · Freak Athlete (all
  athleticism ≥ class-mean+15) · Complete Fighter (both skill
  families ≥75, no stat <50).
- KIND 3 — EARNED TRAITS and KIND 4 — BEHAVIORAL QUIRKS: DEFERRED to
  a post-arc GENERATOR2 filing. Earned traits need career-event hooks
  into the record book; quirks are engine-behavioral (balance-touching
  in a different direction). Filed, not forgotten.

GUARDRAILS (from Van's August ruling, restated as arc law):
- NO DOUBLE-DIPPING: templates shape STATS; identity traits add zero
  hidden mechanical effect. Stats are the mechanism, the trait is the
  label.
- VALIDATION INVARIANT: every STORED trait carries a predicate over
  stats/history; asserted at generation and after any stat mutation;
  gate requires 100% pass on a fresh world.
- Old traits on old saves untouched (forward-only).

---

## 6. AMATEUR PIPELINE (same arc, phased)

- PHASE A (wiring, ships FIRST, separately gated): graduation
  transfers the amateur's rolled attributes through the canonical
  remap onto the pro record. Kills the census-critical bug (stats
  invented from md5 at signing). Forward-only: already-graduated
  fighters keep their stats.
- PHASE C (after the pro generator lands): amateur generator switched
  to the SAME layered engine (missing canonical stats added, canonical
  names at the source), with amateur-appropriate tier centers.
  Scouting/fog-of-war redesign explicitly OUT of this arc (amateur
  notes doc sequencing: data first, scouts later).

---

## 7. RIDE-ALONG CLEANUPS (small, same arc)

- Persist height/reach/stance on the record (reach already surfaces in
  UI; stance filed for future engine use). Numeric weight: derive from
  class, stop rolling.
- Dormant fallback game_state._generate_fighter: route to the real
  generator or delete; a crash path that silently spawns 225 stat-less
  fighters is a landmine.

---

## 8. PHASING AND GATES

- PHASE A — amateur graduation transfer (wiring). Gate: graduate N
  amateurs on a test world; persisted pro stats == remapped amateur
  stats, field-by-field. Mechanical equivalence elsewhere (non-
  graduation paths untouched, production-population rule applies).
- PHASE B — pro generator rebuild (§1–§5). Gates on a fresh world
  (tolerance bands, not byte-MD5 — uuid4 rule):
  1. Correlation matrix hits the §1a r-bands.
  2. OVR-per-tier unchanged within ±2 mean.
  3. Style signature deltas ≥ +8.
  4. Template fraction 12% ±2pp; every template instantiates.
  5. Archetype census: HL/LH cardio×recovery tails ≥ 1% of pool.
  6. Validation invariant 100%.
  7. BANKED, NOT JUDGED: per-division finish-rate table (before vs
     after) — the KO-gradient reading P5-C will calibrate against.
- PHASE C — amateur generator unification. Same gates 1/2/6 on the
  amateur pool.
- PHASE D — badges + display surface (D14-adjacent; badge computation
  ships here, deeper display redesign stays in D14/P3-6).

Each phase: single-purpose commit, stop-before-commit, staged report
first. P5-C runs after Phase C so calibration sees the real population.

---

## 9. ⚖ DECISION POINTS — RULED (Van 2026-09-05: all defaults accepted)

1. r-bands (§1a) — contract is the bands, not the sigmas.
2. Template list of 8 + magnitudes (§2b) + 12% fraction.
3. Class-offset magnitudes ±6/+8, three stats only, chin flat (§3).
4. Badge starter set + 85 threshold (§5).
5. Earned traits/quirks deferred to GENERATOR2 (§5).
6. Amateur unification in-arc as Phase C (§6) vs deferred.
