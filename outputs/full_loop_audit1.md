# FULL-LOOP-AUDIT1 — findings memo

Read-only audit of the decision → outcome spine, full-loop integrity, edge
cases, and code quality. **No code changed.** Every finding cites file:line
or a reproducible sim result. Ranked A (broken / dead decision / state
corruption) > B (unhandled edge case) > C (duplication / dead code / drift).

**Depth-vs-breadth call**: prioritized Phase 1 (decision → outcome). Phase 2
save/load run once (parity confirmed on 10/11 sampled fields). Phase 3
edge-case work done from code + one sim signal (EXTREME intensity outlier).
Phase 4 dead-code done via grep and confirmed. Full multi-year rollover sim
NOT executed — too expensive for this pass; scoped as follow-up. See §STOP.

**PA drift hazards to keep in mind when reading this memo:**
- `fight_engine.py` constants were reported manually-appended on PA in a
  prior audit (CLAUDE.md L204-208). All engine-constant findings below are
  from the repo working tree — live behavior may differ.
- `wsgi.py` reportedly drifted on PA (L209-212). Not in any of this deploy's
  file paths, but any future memory-lifecycle finding must be verified
  PA-side before shipping a fix.

---

## Phase 1 — Decision → outcome propagation

### 1a. Coach hire (specialty + rating) → LIVE, with one confirmed dead surface

**Trained-stat gains — LIVE.**
- `game_bridge.py:8619` — `cs_passive = max(0.3, (cs_rating - 50) / 50 + 0.5)`
  (COACH-RATING-CURVE1, comment doc-block says spread is r=45→0.4× ·
  95→1.4×).
- `game_bridge.py:8699-8701` — the multiplier feeds per-attr gain:
  `_base_per_attr_gain = ((cs_passive / len(cs_attrs)) * cs_boost *
  _trait_mult * _rate * _focus_bonus)`.
- **Empirical sim**: identical camp/fighter/plan, only coach rating varies.
  Over 10 weeks with `specialty=boxing_coach`, LIGHT default plan:
  - rating 45: bucket sum +12 (boxing 68→76)
  - rating 95: bucket sum +21 (boxing 70→79)
  - **Observed ratio 1.75× · Formula-predicted 3.5×**. Delta is diluted by
    diminishing gain (higher stats grow slower — floor at 8710
    `_diminishing_gain`), focus emphasis, and random noise. Direction and
    order of magnitude both correct. **Rating is not cosmetic.**

**Corner advice — LIVE.**
- `corner_advice.py:1084` — `rating = coach_dict.get("rating", 60)` picks
  the CORNER_IQ tier via `_rating_tier()` at :66. Elite pool vs basic.
- `corner_advice.py:1131` — between-round bonus:
  `CORNER_BONUS_BASE + max(0, rating - 60) * CORNER_BONUS_PER_RATING_POINT`
  (base 1.0, +0.04 per point over 60).
- `corner_advice.py:1169` — pre-fight buff mirrors the same formula.

**S&C fatigue reduction — LIVE.**
- `game_bridge.py:7804-7807` — takes best `rating` across staff with
  `resolve_specialty(...) == 'sc_coach'`; if rating ≥ 60, applies
  `_sc_mod = max(0.70, 1.0 - (_sc_rating - 60) * 0.015)`. r=90 → 0.55×
  fatigue accumulation, r=60 → 1.0×.

**Fight-night engine integration — INDIRECT ONLY (via pre-fight stat pump).**
- Grep of `fight_engine.py` and `fight_integration.py` for `coach` returns
  zero matches. Engine physically never reads a coach object.
- But `game_bridge.py:17142-17175` `_apply_coach_iq_prefight_buff` bridges
  the gap: takes `max(_sc.get('fight_iq', 60) for _sc in staff)`, and if
  ≥ COACH_IQ_ELITE_THRESHOLD grants **+3 fight_iq**, ≥ COACH_IQ_BONUS
  grants **+2**, else nothing. Front-loaded before `_simulate_narrated_fight_fn`
  at 17713. Similarly `_apply_corner_prefight_buff` at 17116 buffs
  stats pre-fight based on coach rating.
- **Verdict**: coach *rating* → fight outcome path exists but goes through
  a front-loaded stat pump, not through per-round IQ. Adequate for the
  Sandman-style narrative goal, but note there's **no per-round coach
  hook** in the engine — corner advice affects the between-rounds
  narrative surface, not sim mechanics.

**Coach specialty routing (post JUDO-SAMBO-BUCKET-FIX1) — CONSISTENT.**
Verified all consumers now route via `_SPECIALTY_ALIASES` (game_bridge.py:529)
or `COACH_TYPE_MIGRATION` (:474) after this session's fix at
:499-500 / :597-598. `get_coach_trained_stats` (:713), `resolve_specialty`
(:609), the training loop (:8620), the S&C fatigue read (:7804), and the
hire-card display all read from the corrected tables.

### 1b. Training (focus / intensity / floors / queue) — ALL LIVE

**Focus — LIVE.**
- `game_bridge.py:7745-7748` — emphasis table maps focus tokens to per-stat
  weights (1.0 primary / 0.5 secondary / 0.25 tertiary).
- `game_bridge.py:7867-7875` — `weighted_gain = raw_gain * weight`;
  followed by fighting-style affinity (1.3× on-style, 0.75× off-style),
  equipment bonus, coach coverage penalty (0.85× if no coach covers the
  stat), tier multiplier. Writes to `_fdata[stat]` at :7944.

**Intensity — LIVE.**
- `game_bridge.py:7378-7380` — `_INTENSITY_GAIN = {"REST":0, "LIGHT":1,
  "MODERATE":2, "INTENSE":3, "EXTREME":4}`.
- `game_bridge.py:7751-7753` — fatigue delta table `{"REST":-15, "LIGHT":2,
  "MODERATE":5, "INTENSE":10, "EXTREME":18}`.
- `game_bridge.py:8089-8091` — `_INJURY_BASE = {"MODERATE":0.01,
  "INTENSE":0.03, "EXTREME":0.08}`. Injury roll at :8004, gains halved
  at :8011.

- **Empirical sim** (STRIKING:boxing focus, coach rating 65, 10 weeks):

  | intensity | Σ gain | end fatigue |
  |---|---|---|
  | LIGHT | 21 | 20 |
  | MODERATE | 29 | 50 |
  | INTENSE | 36 | 52 |
  | EXTREME | **25** | **6** |

  LIGHT→INTENSE is monotonic. **EXTREME anomaly**: less gain than INTENSE
  AND lower final fatigue than LIGHT. See Phase 3 §3d — likely
  injury-halving is *over-firing* at EXTREME, dropping the fighter into
  recovery weeks that reset fatigue. Whether this is intended tuning or a
  regression is worth checking.

**Floors — LIVE but ONLY BLOCKS DECAY, not training.**
- `game_bridge.py:8140-8144` — floors stored in plan `'floors'` dict.
- `game_bridge.py:11199-11204` — maintenance decay reads floor; if
  `current <= floor`, decay skipped; otherwise `max(floor, new_val)`.
- **The floor does NOT gate training upward.** Comment doc-block at
  the training-plan setter (game_bridge.py:8337-8339) auto-locks floors
  when a queue goal is hit. This is the design, but worth naming as
  a documentation nit — the UI label "floor" could reasonably be read as
  "won't fall below during hard training" AND "won't grow below" but only
  the maintenance path enforces it.

**Queue — LIVE.**
- `game_bridge.py:8328-8339` — pop-when-hit, floor auto-lock at
  `max(50, min(100, int(_goal_target)))`.
- `game_bridge.py:8295-8301` — `'maintain'` mode replaces active plan
  with `SPARRING:sparring + LIGHT + _queue_mode: maintain`.

**100 cap — enforced.**
- `game_bridge.py:7944` and `:8715` — both training and coach passive
  clamp with `min(100.0, current + effective)`.

### 1c. Gameplan / camp style — **DEAD in real engine (finding A1)**

**Storage — writes reach the fight dict.**
- `routes.py:2371-2375` → `bridge.save_fight_camp(fight_id, gameplan,
  focus, intensity)`.
- `game_bridge.py:13224-13232` — writes into `_fight_camps` and stamps
  the scheduled fight: `fight["gameplan"] = gameplan`,
  `fight["training_focus"] = training_focus`.

**Real engine — the ONLY consumer never gets it.**
- `game_bridge.py:17705-17721` builds `_fight_cfg` and calls
  `_simulate_narrated_fight_fn(fa1, fa2, rounds=..., is_title_fight=...,
  is_main_event=..., starting_stamina_f1=..., starting_stamina_f2=...,
  config=...)`. **No `gameplan` argument. No `training_focus` argument.**
- `fight_integration.py:1770-1802` — `simulate_narrated_fight` signature:
  `(fighter1, fighter2, rounds=3, is_title_fight=False, is_main_event=False,
  starting_stamina_f1=100.0, starting_stamina_f2=100.0, config=None)`.
  No gameplan parameter.
- `fight_engine.py` grep for `gameplan` / `training_focus`: **0 hits.**
- `_make_fighter_attrs` at `game_bridge.py:17074-17113` (the `fa1`/`fa2`
  builder) does not stamp gameplan onto FighterAttributes either.
- Gameplan IS used in the SCORE-BASED FALLBACK path (`game_bridge.py:5023-5049`),
  but this is the fallback, not the primary sim path used for player
  fights and any fight that runs the real engine.
- `_apply_gameplan_payoff` (`game_bridge.py:4603`) reads gameplan
  **post-fight** to grade RIGHT_READ / WRONG_READ narrative surfacing —
  narrative payoff, not a mechanical modifier.

**Verdict — decision is stored, grades a narrative surface, but does NOT
change the fight sim.** This is the largest finding in the audit. If Van's
Sandman-north-star goal is "gameplan choice creates the story," gameplan
needs to reach the engine — currently a player choosing GRAPPLE vs
STAND_AND_BANG has zero effect on how the fight plays out. Fix direction:
either extend `simulate_narrated_fight` signature to accept a gameplan
enum + modify aggression/takedown/submission propensity, OR bake gameplan
into pre-fight stat modifiers (à la `_apply_coach_iq_prefight_buff`).

### 1d. Fight acceptance (opponent choice) — SEMI-LIVE

**Opponent choice reaches attributes, not tactics.**
- `routes.py:1050-1054` → `game_bridge.py:6225-6320`
  (`accept_fight_offer`). Offer dict has one opponent — no A/B chooser.
- Fields written to scheduled fight (`game_bridge.py:6284-6292`):
  `fighter2_id, fighter2_name, purse, win_bonus, is_title_fight,
  weeks_away, opponent_rank`.
- Fight outcome uses fighter attributes via `_make_fighter_attrs` (real
  engine) or score-based path at `game_bridge.py:5067-5068`.

**Cosmetic-only fields carried through accept path but never read in
outcome:**
- `purse`, `win_bonus` — never consumed by fight engine. Only affect
  post-fight balance.
- `opponent_rank` on the offer — surfaced in UI only; not used in either
  win-probability path.
- `rounds` — NOT taken from user input; derived from card_slot at
  `game_bridge.py:17666`.

**Fix direction if this matters**: whether purse should influence
motivation (a Rocky I trope — big payday = big performance) is a design
call, not a bug. Filing as A-level *ambiguous* only because Van's
Sandman-goal cares about story texture.

### 1e. Facility / other spend — mostly LIVE with three dead-money candidates

**LIVE spend → outcome pairs:**

| spend | debit site | outcome site |
|---|---|---|
| Camp tier upgrade | `game_bridge.py:5628` | Training cap + efficiency mult + roster size + equipment tier (`facilities.py:80/94/134`, `game_bridge.py:7458/7902`); weekly overhead `:9357` |
| Equipment (bags/mats/tank) | `game_bridge.py:5734` | Gain bonus `:5748/7901`; decay reduction `:11165/14916` |
| Coach salary | `game_bridge.py:9373` | Coach retention via morale decay `:9383/18662/18691/18705` |
| Fighter signing/purse | `game_bridge.py:10289` | Morale / holdout via `MORALE_HOLDOUT` `:352 + :18995`; +15 morale on re-sign `:20884` |
| Overseas trip | `game_bridge.py:9898` | Stat gain 2-4 (success) / 1-2 (fail) at `:9928-9982` |
| Sponsor accept | (inbound) | Pre-fight attr boost `_apply_sponsor_boost` `:17176-17194`, called `:17661-17662` |

**Dead-money candidates:**
1. **`elite_passive` field** at `game_bridge.py:7446` — string value assigned
   in ELITE equipment tier definition. Grep for `elite_passive` returns
   only the definition site. **No consumer anywhere in the tree.**
2. **Weekly facility overhead** deducted per tier at `game_bridge.py:9325-9328`.
   Debit works; grep for downstream reads of the overhead line-item shows
   no formula consumes it — only financial-UI display. (Cost creates
   scarcity, so this isn't purely cosmetic, but the "you pay more, you
   get more" contract isn't backed by any specific outcome tied to the
   overhead cost itself.)
3. **Coach underpaid morale decay** at `game_bridge.py:18691-18693` — decays
   morale, but decay does NOT gate the coach's training-gain contribution
   (grep for `morale` in `_apply_weekly_training`: no consumer). Only
   retention/walkout gates on morale. So underpaying an elite coach is
   free performance while the coach hasn't quit yet. Design question:
   should morale multiply `cs_passive`?

---

## Phase 2 — Full-loop integrity

### 2a. Save/load parity — 10/11 fields match

Sim: new game → 8 weeks → snapshot → save → new bridge → load → snapshot →
compare.

| field | before | after | match |
|---|---|---|---|
| week | 8 | 8 | ✅ |
| balance | 9000 | 9000 | ✅ |
| wins/losses | 0/0 | 0/0 | ✅ |
| boxing / takedowns | 69 / 76 | 69 / 76 | ✅ |
| fatigue | 40 | 40 | ✅ |
| coach_rating | 70 | 70 | ✅ |
| training_plan | {} | {} | ✅ |
| scheduled_fights | 0 | 0 | ✅ |
| fighter_id | player_fighter_… | (same) | ✅ |
| **news_count** | **164** | **85** | ❌ |

**News truncation at save** — `game_bridge.py:2597`:
`"news_items": self._news_items[-100:]`. Last-100 slice. Observed pre-save
164 items → post-load 85 (the reader also filters, so the drop is
100-cap + reader filter combined).

Whether this matters depends on how "history" is exposed. If the news
feed is meant to hold long-arc history (Sandman-scale — "when I signed
this guy back in year 1"), the -100 cap silently drops it. If news is
just a rolling recap surface, this is intentional and fine. Design call.

### 2b. Full year-rollover audit — NOT COMPLETED THIS PASS

Simulating 52 weeks end-to-end for a rollover audit costs 45-90s of sim
per condition plus post-hoc state inspection. Deferred. **What I didn't
verify**:
- Rankings carry-over across December→January
- Belt history's `defenses` counter across rollover
- Contract expirations at year boundary
- `last_title_defense_week` (if present) across boundary
- Camp / coach / fighter age increments (`Ship #23` aging was audited
  during world-gen only — the runtime aging path in advance_week hasn't
  been touched in this pass)

Filing as a follow-up scoped ship: `FULL-LOOP-AUDIT2-ROLLOVER` — sim
w52 → w53 boundary, snapshot before/after all persistence-sensitive
fields. Small ship, but needs to actually run.

---

## Phase 3 — Modifiers & edge cases

### 3a. Modifier stack composition — spot check clean; full audit deferred

Sampled the training-gain stack at `game_bridge.py:8699-8710`:
`cs_passive × cs_boost × _trait_mult × _rate × _focus_bonus ×
_specialist_mult × _diminishing_gain(...)`. Each factor comes from a
distinct source (coach rating / archetype / traits / same-domain
diminishing / focus-match / stat-specific specialist / current-stat
level). No obvious double-application. **Style affinity multiplier
(1.3× on-style / 0.75× off-style) is applied inside `_diminishing_gain`
per the training-loop trace**, so the on-style bonus and the focus
bonus stack multiplicatively — worth Van validating this is intentional
(they could reasonably be additive, or capped).

Fight-side modifier stack (pre-fight buffs at `game_bridge.py:17646-17662`)
is cleaner: coach prefight → coach IQ prefight → sponsor prefight, each
mutating `fa1`/`fa2` in place with `min(99, ...)` clamps. Order matters
only for the clamp — same fighter can't be pumped past 99 by any single
call.

### 3b. Draw handling — LIVE but two-consumer surface

Draws are a known third case in an otherwise binary win/lose world. Quick
grep — `is_draw` and `draw_count` are read across:
- `game_bridge.py` post-fight resolution ~4275 area
- `matchmaking.py` (unverified this pass)
- Career-stat accumulator
- News category

Not deep-audited. **Recommendation**: pull draw handling into its own
scoped audit — it's the pattern most likely to no-op silently in one
of 8+ consumers.

### 3c. Champion with no valid challenger

Not directly reproduced in this pass. Existing Slice 2/2.5/3 champion-
injury shipwork established the auto-vacate + player invite flow, but
a champion in a DIVISION with fewer than 2 valid ranked contenders and
no injury is a distinct edge. Worth flagging for a specific test:
create a 12-fighter division, retire everyone but champion+#1, then
book the next event and see if `_book_title_fight` fails cleanly or
crashes on empty contender pool.

### 3d. **EXTREME training intensity is anomalously bad — finding B1**

Empirical sim (§1b): EXTREME 10-week total gain 25 is **less than
INTENSE (36) and MODERATE (29)**, and end fatigue is only 6 (lower than
LIGHT's 20). Almost certainly injury-halving over-firing:
- Injury base for EXTREME is `0.08` (`:8089-8091`) — 8% per week per
  fighter. Over 10 weeks: `1 - (1-0.08)^10 ≈ 57%` injury chance.
- Injuries halve gains at `:8011` AND force recovery weeks (during
  which the fighter isn't training, resetting fatigue).

**This isn't necessarily a bug** — it may be intentional "EXTREME breaks
fighters" tuning. But player expectation is "higher intensity = higher
gain with more fatigue," and the actual model is "higher intensity =
occasionally big gain but usually worse than INTENSE." Worth Van
confirming this is intentional; if so, the UI should hint at it.

### 3e. Stat cap at 100

Verified enforced at `:7944` and `:8715`. A fighter at 100 stops gaining
that stat — no crash, gain silently drops to 0. **Not tested**: whether
a stat-at-100 fighter also correctly handles decay (does floor system
allow decay from 100→99 to still fire)? Deferred.

### 3f. Draws / stub fighters / released fighters — deferred

Read-only inspection of full edge-case matrix from the ask (0-0-0 debut,
defaulted stats, empty card weeks, retired/released, stat-at-100 decay)
NOT completed. Scoping observation: the codebase has recent shipwork
around thin-week cards (`CARDSLOT-BACKFILL1`), so this ground is
partly covered; but no comprehensive audit exists.

---

## Phase 4 — Code quality: duplication, dead code, drift

### 4a. Duplicated logic — confirmed instances

**Save-slot list hardcoded (`game_bridge.py`):**
- `:3104` inside `list_web_saves` → `slots = ["slot1", "slot2", "slot3",
  "slot4", "slot5", "autosave"]`
- `:3142` inside `get_newest_save_slot` → same literal
- Plus routes.py saves-menu view (unverified this pass) likely
  hand-rolls the same set
- **Fix direction**: hoist to a module-level constant `_SAVE_SLOT_NAMES`.

**Style-string → engine-enum map — two independent copies:**
- `game_bridge.py:17045` — `_STYLE_MAP` on the bridge instance
  (short form, few entries)
- `game_bridge.py:17672-17696` — `_STYLE_STR_MAP` inline inside
  `_run_real_engine` (long form, ~20 entries including Judo, Sambo,
  Submissions, Grappling, Karate, Sprawl & Brawl)
- The inline map at :17672 is a superset of `_STYLE_MAP`. **Two sources
  of truth for the same concept**; the second lives inside a function
  and drifts silently.
- **Fix direction**: hoist to module-level; delete `_STYLE_MAP`.

**Per-route `game_started` inline check — 20 hand-rolls in `routes.py`:**
- `grep -c "if not bridge.game_started"` returns **20** — each route
  re-implements the guard while a `require_game_started` decorator sits
  defined but unused at `:291-298`.
- **Fix direction**: apply the decorator; delete the inline guards.

**Fighter attribute string list — inferred, needs verification.**
The `_STATS` / attr list appears in `_make_fighter_attrs` (`:17091-17112`),
in `_diminishing_gain`, in save/load, and in the training loop. Whether
these are a single source or drifted forks not verified this pass.

### 4b. Dead code — confirmed

- **`require_game_started` decorator** at `routes.py:291-298`. Grep for
  `@require_game_started`: **0 hits**. Dead.
- **`elite_passive` equipment field** at `game_bridge.py:7446`. Grep
  for the literal returns only the definition site. Dead.
- **`is_rivalry` parameter** on `card_builder.calculate_matchup_score`
  at `card_builder.py:260`. The 12.0 flat bonus at `:348` never fires:
  only caller `game_bridge.py:15740` doesn't pass the param (default
  False), and `_matchup_score` adds `_rivalry_heat_bonus` at `:15751`
  after the return instead. Dead branch.
- **`fight["training_focus"]` on the scheduled-fight dict**
  (`game_bridge.py:13231`). Written by `save_fight_camp`; grep for
  fight-side reads returns none. Dead field.
- **`fight["gameplan"]` on the scheduled-fight dict** — half-dead
  (still read by score-based fallback at `:5023-5049` and by
  `_apply_gameplan_payoff`, but the primary sim path ignores it).
  See §1c A1.
- **`generate_corner_commentary`** defined at `commentary.py:4270` and
  `narrative/commentary.py:4076` (two copies!). Web app uses
  `generate_corner_advice` (corner_advice.py:1048) instead. Dead in
  the web-app context; CLI status unverified.

### 4c. Standard drift — spots below the discipline of recent ships

**Silent-fallback that masks errors:**
- `game_bridge.py:8622` — `cs_boost = self._ARCHETYPE_BOOST.get(cs_focus,
  1.0)`. If a coach's specialty doesn't resolve, they still contribute
  1.0× boost — silently equal to a valid coach. Legitimate — matches the
  `mma_coach` fallthrough — but worth naming.
- `game_bridge.py:17702` — `except Exception: pass` swallows all style-map
  errors during style-matchup lookup. If the map ever fails, style_mod
  silently → 0.0 with no signal. Fix direction: at minimum log the
  exception once per session; ideally narrow the exception type.

**Magic numbers that should be named:**
- `game_bridge.py:8619` — `(cs_rating - 50) / 50 + 0.5` — the "50" pivot
  and the "0.5" additive shift. The doc-block above says "compressed from
  the old (rating-50)/25 curve" — future re-tuners will want named
  constants like `COACH_RATING_PIVOT = 50`, `COACH_RATING_SLOPE = 1/50`,
  `COACH_RATING_BASELINE = 0.5`.
- `game_bridge.py:17706-17712` — `_FightConfig(scheduled_rounds=..., ...,
  damage_multiplier=0.24)`. `0.24` here is **DIFFERENT** from the
  `FI_DAMAGE_MULTIPLIER = 0.32` documented in CLAUDE.md and different
  from `fight_engine.DAMAGE_MULTIPLIER = 0.55`. Three damage multipliers
  in three sites. Worth Van confirming which is authoritative — CLAUDE.md
  may be stale, or one path may be silently unused.
- `corner_advice.py:1131` — bonus formula uses `+0.04/pt`. Live constant
  but hardcoded in-formula; if there's a `CORNER_BONUS_PER_RATING_POINT`
  module constant it should be pulled from there.

**Binary-assumption drift where a third case exists:**
- Style-matchup returns 0.0 on any exception (`game_bridge.py:17702`) —
  hides "no match" case that Van might want to know about vs. actual
  balanced matchup.
- `is_title_fight` / `is_main_event` are binary but `card_slot` has
  4-5 values; `total_rounds = 5 if (is_title or main_event or co_main)
  else 3` at `:17666` is currently correct but the 3-way logic is
  written as a chain of `or`s — sub-bug O.1 precedent (asymmetric
  round override at `fight_integration.py:1228-1229`) shows this
  family is fragile.

---

## Phase 5 — Ranked findings + fix directions

### A — broken / decision doesn't propagate / state corruption

- **A1. Gameplan never reaches the real fight engine.**
  Storage: `game_bridge.py:13224-13232`. Real engine sim:
  `game_bridge.py:17705-17721` calls `simulate_narrated_fight` with no
  gameplan parameter; `fight_integration.py:1770-1802` signature has no
  gameplan; `fight_engine.py` has zero gameplan reads. Player's tactical
  choice is silently discarded before hitting the sim; only score-based
  fallback (`:5023-5049`) uses it. **Fix direction**: extend engine
  signature and modify per-round tendencies (aggression, takedown
  frequency, submission attempts) based on gameplan, OR fold gameplan
  into a pre-fight stat modifier alongside sponsor / coach IQ buffs.
  Largest player-facing finding in this audit.

- **A2. News history silently truncated to last 100 items on save.**
  `game_bridge.py:2597` → `"news_items": self._news_items[-100:]`.
  Confirmed empirically: 164 in-memory → 85 post-load (reader also
  filters). **Fix direction**: design call. If news is meant to hold
  long-arc history (Sandman "when I signed him back in year 1"), raise
  or remove the cap; if news is a rolling recap surface, leave as is
  and delete the news items that would have grown beyond the cap
  intentionally.

### B — edge case unhandled or off-tune

- **B1. EXTREME training intensity is worse than INTENSE.**
  Empirical: 10w sums LIGHT 21 · MODERATE 29 · INTENSE 36 · **EXTREME 25**.
  Injury rate 0.08/wk (`:8089-8091`) probably compounds too aggressively
  over 10w. **Fix direction**: measure whether Van intends the reversal.
  If not, either lower EXTREME's injury base or reduce the injury-halving
  penalty. If yes, add a UI hint.

- **B2. Damage-multiplier drift across three sites.**
  `fight_engine.py:DAMAGE_MULTIPLIER = 0.55`, `fight_integration.py:
  FI_DAMAGE_MULTIPLIER = 0.32`, `game_bridge.py:17711 damage_multiplier=0.24`.
  CLAUDE.md's "key constants" section names 0.55 and 0.32 only — the
  0.24 in the bridge overrides both. **Fix direction**: audit whether
  the 0.24 is Van's intended live value; if so, update CLAUDE.md and
  probably the constant at the source rather than by param.

- **B3. Coach morale doesn't gate training contribution.**
  Underpaying a coach decays their morale (`:18691-18693`) but the
  coach still provides full `cs_passive` boost until they walk out.
  **Fix direction**: multiply `cs_passive` by `(morale / 100)` clamped
  to some floor; or accept that morale gates retention only (design
  call).

- **B4. Cosmetic accept-flow fields.**
  `purse`, `win_bonus`, `opponent_rank` stored on the offer/fight but
  never consumed by outcome calc. Design call whether purse should
  affect motivation (Rocky trope). Not a bug per se; low priority.

- **B5. Champion / thin-card edge cases NOT verified this pass.**
  See §3c/3f. Deferred.

- **B6. Full year-rollover NOT simulated this pass.**
  See §2b. Deferred as `FULL-LOOP-AUDIT2-ROLLOVER`.

### C — duplication / dead code / drift

- **C1. `require_game_started` decorator is dead**, but 20 inline
  copies of the guard exist across `routes.py`. Fix direction: apply
  decorator, delete inline.
- **C2. Save-slot list hardcoded at `game_bridge.py:3104` and
  `:3142`** (plus possibly `routes.py` saves-menu). Fix: hoist constant.
- **C3. Style-map `_STYLE_MAP` at `:17045` vs `_STYLE_STR_MAP` at
  `:17672`** — two independent sources of truth. Fix: hoist superset.
- **C4. Dead code: `elite_passive` string (`:7446`), `is_rivalry`
  branch (`card_builder.py:348`), `fight["training_focus"]` field
  (`:13231`), `generate_corner_commentary` (CLI-only fork, exists in
  two files).**
- **C5. Silent-except style-map at `:17702`** — masks errors.
- **C6. Magic numbers**: coach rating pivot/slope at `:8619`,
  corner-bonus per-point at `corner_advice.py:1131`.
- **C7. Auto-load-save covers only `/`** — bookmarks bounce
  (see AUTOLOAD-SAVE-DIAG1.md §7a).

---

## STOP — where this audit ends

Deep coverage: Phase 1 (all 5 decisions), Phase 2a (save/load parity —
single 8-week sim), Phase 4 (dead code + duplication grep-verified).

Partial: Phase 3 modifier stack (one spot-check + one sim-flagged
anomaly), Phase 4c drift (spot-checked, not comprehensive).

**Not done in this pass** — filing as follow-ups rather than skimming:
- Phase 2 year-rollover boundary sim (`FULL-LOOP-AUDIT2-ROLLOVER`)
- Phase 3 draw-consumer audit (`FULL-LOOP-AUDIT3-DRAWS`)
- Phase 3 champion-no-challenger + thin-card edge (`FULL-LOOP-AUDIT4-EDGES`)
- Phase 4c comprehensive drift scan (`FULL-LOOP-AUDIT5-DRIFT`)
- Fighter/attr-list duplication check (§4a fourth bullet)

I'd rather have Phase 1 deep than 5 phases thin — you asked for that
explicitly. If you want any of the deferred items done next, name it
and I'll spawn a scoped follow-up.
