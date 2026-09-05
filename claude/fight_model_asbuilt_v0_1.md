# FIGHT MODEL — AS-BUILT v0.1 (2026-09-02)

Status: EXTRACTION ONLY, no redesign proposals. HEAD `727dee8`. Both engines'
fight-resolution pipelines documented in order (selection → attempt →
contest → damage → state update → finish checks → round/fight end → scoring).
Per-item file:line anchors, formulas verbatim, constants with literal values,
RNG draws named, hidden state tracked. Divergence table + ambiguous section
are first-class. Constant inventory is Part C at the tail.

Scope: fight resolution only. World-gen, matchmaking, training, aging out
of scope. Coverage: `cage_dynasty_web/fight_engine.py` (fe, 4574 lines) +
`cage_dynasty_web/fight_integration.py` (fi, 2186 lines).

Tagging convention: `[fe]` = fight_engine only, `[fi]` = fight_integration
only, `[both]` = same code path (fi imports the fe primitive), `[fe|fi]` =
similar behavior in both engines but each has its own site (asymmetry
recorded in the Divergence Table).

---

## §0 Entry points + top-level fight loop

### 0.1 [fe] `fe.simulate_fight(fighter1, fighter2, config=None, fighter1_fatigue=0, fighter2_fatigue=0, heat_level=0)` — fe:4003
Returns `FightResult`. Config default → `FightConfig.standard_fight()`
(3 rounds, 55 exchanges/round, damage_multiplier=0.48, standup_threshold=10).
`_assert_sanctioned_config(config)` at fe:4032 (raises if triple not in
allowlist: LIVE_PLAY (55, 0.48, 10) / PRE_GEN_LEGACY (55, 0.42, 6) /
FI_FALLBACK (55, 0.48, 6)).

**Heat modifiers** (fe:4034-4055) — reads `heat_level` (0-100):
| heat > | damage_mult | composure penalty | aggression bonus |
|---|---:|---:|---:|
| 80 | 1.20 | 12 | 0.20 |
| 60 | 1.15 | 8 | 0.15 |
| 40 | 1.10 | 5 | 0.10 |
| 20 | 1.05 | 3 | 0.05 |
| ≤20 | 1.00 | 0 | 0.00 |

Heat damage multiplier gets applied to `config.damage_multiplier` via
`dataclasses.replace` at fe:4127-4130 — **sanctioned config mutation** (the
only legal one; per fe:4119-4126 comment, produces post-heat
damage_multiplier outside the allowlist e.g. 0.48 × 1.20 = 0.576). Heat is
fe-only; fi has no equivalent (filed for Stage 1 parity map). Heat
composure penalty applied at fe:4086-4087 as `max(20, fighter.composure -
heat_composure_penalty)`.

**Starting stamina from fatigue** (fe:4059-4082): local function
`get_starting_stamina(fatigue)` → 6-bucket step function `≤10:103, ≤20:100,
≤40:95, ≤60:88, ≤80:78, >80:65`. Note the >100 peak-condition value
(subject to Category-B `stamina/100` consumers at PREGEN-PEAK103 exposure
window per prior filings).

**Max health** (fe:4089-4092): `f_max_health = 100.0 + fighter.chin * 0.3`.
Comment: "Lowered to 100 + chin*0.3 for raised finish rate". Chin scaling
factor 0.3 is a load-bearing balance knob.

**FighterState construction** (fe:4095-4112) passes
`recovery_rating=fighter.recovery` + `cardio_rating=fighter.cardio` (C8
RECOVERY-WIRE1 + C12 STAMINA-DRAIN1 wire).

**Main loop** (fe:4147-4197):
```python
for round_num in range(1, config.scheduled_rounds + 1):
    fight_state.current_round = round_num
    fight_state.new_round()
    for _ in range(config.exchanges_per_round):
        result = simulate_exchange(...)
        if result:
            winner_id, method = result
            return FightResult(...)
    # end-of-round processing (between-round stoppages, scoring)
```

Structure: outer round loop, inner 55-exchange loop, early return on any
finish. If no finish, proceeds to decision after all rounds.

### 0.2 [fi] `fi.simulate_narrated_fight(...)` — fi:2031
Entry-level function; instantiates `NarratedFightSimulator` and calls
`.simulate()` at fi:2101-2102. No-config-passed path constructs a default
`FightConfig(55, 0.48, 6, is_title_fight=...)` at fi:2062-2086 (FI_FALLBACK
triple, NOT LIVE_PLAY — differs from `fe.simulate_fight`'s default).
Downstream bridges (`game_bridge._assemble_prefight`) always pass an
explicit `config=` per B9 LIVE_PLAY discipline.

### 0.3 [fi] `NarratedFightSimulator.__init__` + `_init_fight()` — fi:335, fi:482
`__init__` stores fighter1/fighter2/config, gameplans, starting stamina.
`_init_fight` constructs `fighter1_state` + `fighter2_state` at fi:510-525:
```python
self.fighter1_state = FighterState(
    fighter_id=..., name=..., health=100.0 + self.fighter1.chin * 0.5,
    stamina=self.starting_stamina_f1,
    recovery_rating=self.fighter1.recovery,
    cardio_rating=self.fighter1.cardio,
)
```
**Divergence — health formula**: fi uses `chin * 0.5` (fi:513); fe uses
`chin * 0.3` (fe:4091). fi fighters have **more HP** at the same chin. See
Divergence Table.

### 0.4 [fi] `NarratedFightSimulator.simulate()` — fi:1829
Outer round loop, calls `_init_round()` per round transition, then
55-exchange inner loop calling `_simulate_exchange(exchange_num)`. On any
finish returns `NarratedFightResult` via `_build_finish_result` (fi:1849).
Between-round doctor/corner stoppage checks at fi:1755-1800 mirror fe's
between-round stoppages BUT **no cut stoppage branch** (per fi:1762-1770
comment: "the cut-stoppage branch that used to sit here was unreachable —
fight_integration never writes damage.cuts").

---

## §1 Exchange loop — pre-action bookkeeping

### 1.1 [fe] `simulate_exchange(...)` — fe:3171
Increments `fight_state.exchanges_this_round` (fe:3187), `total_exchanges`,
`position_duration`. Structure per exchange:
1. If `submission_active` → route to `process_submission_progress` (fe:3218-3237)
2. Compute initiative (fe:3239-3327)
3. Coin-flip near-tie / else max-initiative → attacker (fe:3329-3343)
4. `select_action(attacker, defender, fight_state, attacker_state)` (fe:3346)
5. Dispatch: strike / submission / grappling branches (fe:3349, 3597, 3642)
6. Post-action bookkeeping: control time, referee standup, back-control stalemate, per-exchange stamina recovery, rock duration decrement (fe:3784-3855)

### 1.2 [fi] `_simulate_exchange(exchange_num)` — fi:685
Similar structure. Extra:
- **Sambo chain forcing** (fi:729-745): if actor has `_sambo_chain=True`, force-select a position-appropriate submission (BACK_MOUNT→RNC, MOUNT→ARMBAR, SIDE_CONTROL_TOP→KIMURA).
- Threading of `_gameplan_f1`/`_gameplan_f2` onto FighterStates before `select_action` (fi:714-721).
- Passes `gameplan=_actor_gameplan` to `select_action` (fi:724-727).
- **Initiative via `_determine_initiative()`** (fi:704) — a separate method, not the inline code fe uses.

**Divergence — initiative computation**: fi has its own `_determine_initiative` method (not extracted here — cited as a divergence site). fe's inline initiative (fe:3239-3327) reads:
```python
f1_initiative = fighter1.speed + fighter1_state.momentum // 2 + random.randint(-15, 15)
f2_initiative = fighter2.speed + fighter2_state.momentum // 2 + random.randint(-15, 15)
```
Plus underdog aggression, takedown bonus, submission threat, position bonus, guard bonus, coin flip if `|f1 - f2| ≤ 3`. RNG: 2× `random.randint(-15, 15)` per exchange + 1× `random.random()` for coin flip.

---

## §2 Action selection

### 2.1 [both] `fe.select_action(fighter_attrs, opponent_attrs, fight_state, fighter_state, gameplan=None)` — fe:1568
Shared primitive. Both engines call the same function. Returns
`(action_type, action_data)` where action_type ∈ `{"strike", "submission",
"grappling"}`.

Available actions computed via `get_available_strikes(position, is_top)`,
`get_available_submissions(position, is_top, fighter_attrs)`,
`get_available_grappling_actions(position, is_top, fighter_attrs,
fight_state)` (fe:1588-1590).

**Position secured check** (fe:1596-1613) — gates submissions:
- DOMINANT_CLUSTER (BACK_MOUNT, TRUCK, MOUNT, SIDE_CONTROL_TOP, CRUCIFIX_TOP,
  NORTH_SOUTH_TOP): `position_secured = dominant_control_duration >= 3`
- Else: threshold = 2 if subs≥85 and pos in GUARD∪INFERIOR; 4 if subs≥75; 5 otherwise
- Threshold checked against `fight_state.position_duration`

**Base weights** (fe:1666-1668):
- `strike_weight = 120`
- `sub_weight = 0` (starts zero; only added under specific conditions)
- `grapple_weight = 13`

**Style adjustments** (fe:1680-2050+): dozens of `if my_style == "..."` branches modify weights per style/matchup. Structure: STANDING > CLINCH > GROUND positional branches, each with style-vs-opponent-style rules. Examples (verbatim):
```python
if my_style in ("wrestler", "sambo") and opp_style in ("striker", ...):
    strike_weight = 55
    grapple_weight = 35
    if GrapplingAction.CLINCH_ENTRY in grappling:
        grapple_weight += 15
```
(fe:1685-1691)

Muay Thai gets +22 grapple for CLINCH_ENTRY (fe:1704), +12 strike vs strikers (fe:1706-1707). BJJ / sambo / GnP / clinch-fighter / pressure-fighter / point-fighter / karate / brawler branches each have their own weight adjustments — full inventory is style-dependent code.

**Cardio-gap multiplier** (fe:2109-2120), R2+:
```python
if _cardio_gap >= 12:
    _cardio_mult = 1.0 + ((_cardio_gap - 10) * 0.015 * _round)
    _cardio_mult = min(_cardio_mult, 1.35)
    strike_weight = int(strike_weight * _cardio_mult)
    grapple_weight = int(grapple_weight * _cardio_mult)
    sub_weight = int(sub_weight * _cardio_mult)
```
UNIFORMLY scales all three action-type weights → RATIO-invariant under `random.choices` proportional selection, but int-truncation + min-floors below produce measurable outcome effects (per Gate 0(c) Step 1c: +7.08pp p_strike at starved-stamina cell, N=100k).

**Stamina factor** (fe:2147-2151):
```python
stamina_factor = fighter_state.stamina / 100
strike_weight = int(strike_weight * stamina_factor)
sub_weight = int(sub_weight * stamina_factor)
grapple_weight = int(grapple_weight * stamina_factor)
```
Reads `fighter_state.stamina` — Consumer #1 in M1 census.

**Minimum weights** (fe:2153-2161):
```python
strike_weight = max(5, strike_weight) if strikes else 0
_sub_threshold = 45 if my_style in ("bjj", "sambo") else 60
if submissions and fighter_attrs.submissions >= _sub_threshold:
    sub_weight = max(1, sub_weight)
else:
    sub_weight = 0
grapple_weight = max(5, grapple_weight) if grappling else 0
```

**Action selection** (fe:2163-2180): `random.random() * total` → strike / submission / grappling. Uses `random.random()` × 1 for category, then `select_strike` / `random.choice` / `select_grappling_action` picks specific.

### 2.2 [both] `select_strike(available, fighter, opponent, position)` — fe:2183
Skill-weighted `random.choices`:
- Boxing family: `weight += fighter.boxing // 5`
- Kick/knee family: `weight += fighter.kicks // 5`
- Elbow/clinch family: `weight += fighter.clinch_striking // 5`
- fight_iq > 60: +10 for leg strike if opponent.speed > 70; +10 for body if opponent.cardio > 70
- Wheel/spinning-back kick: `weight = int(weight * (fighter.speed / 70))`

### 2.3 [both] `select_grappling_action(available, fighter, position, is_top, gameplan, fighter_state)` — fe:2223
Skill-weighted with per-action-family bias:
- Takedown family: `weight += fighter.takedowns // 4`
- Guard/sweep family: `weight += fighter.guard // 4`
- Top control family: `weight += fighter.top_control // 4`
- CLINCH_ENTRY: `weight += (fighter.takedowns + fighter.clinch_control) // 6`; +15 if clinch_control≥70
- STAND_UP: +15 if guard>60 or strength>60
- CLINCH_BREAK: +20 if boxing > takedowns

GAMEPLAN-DIAL-RANGE-CORE1 modifiers (§1b/1c): if gameplan.range_bias != 0, additional biases scaled by `dial_execution(fighter, fighter_state)` — takedowns, sweeps, STAND_UP, CLINCH_BREAK all sensitive per position.

---

## §3 Contest primitives

### 3.1 [both] `calculate_strike_success(attacker, defender, strike, attacker_state, defender_state, fight_state)` → `Tuple[bool, bool]` — fe:2330
Returns `(landed, was_counter)`.

**Skill routing** (fe:2343-2361):
| strike family | offense | defense |
|---|---|---|
| Boxing (JAB/CROSS/HOOK/UPPERCUT/OVERHAND) | `attacker.boxing` | `defender.striking_defense` |
| Kicks (all `"kick" in strike.value.lower()`) | `attacker.kicks` | `defender.striking_defense` |
| Clinch explicit (CLINCH_KNEE/CLINCH_ELBOW/DIRTY_BOXING) | `attacker.clinch_striking` | `(defender.striking_defense + defender.takedowns) // 2` |
| Else (fallback: knees, other elbows, GnP, BACKFIST, SUPERMAN_PUNCH) | `attacker.clinch_striking` | `defender.striking_defense` |

**Muay-Thai kick cliff** (fe:2353-2354): `if attacker.kicks >= 80 and defender.kicks < 60: offense += 10`. (Note: STRIKE-LANDING-AUDIT1 measured this cliff as producing zero aggregate landing lift at the aggregate — cliff fires but downstream state modifiers wash the +10 offense before the landed roll.)

**Speed modifier** (fe:2363-2365): `offense += attacker.speed // 10`; `defense += defender.speed // 10`.

**Grappler pressure (STANDING only, fe:2369-2399)**:
- defender.takedowns ≥ 85 → defense +15; ≥75 → +10; ≥60 → +5
- defender.guard ≥ 85 → defense +10; ≥75 → +5
- takedown_threat (def-att) ≥30 → offense ×0.75; ≥20 → ×0.82; ≥10 → ×0.90
- sub_threat (def-att) ≥30 → offense ×0.88; ≥20 → ×0.94

**Stamina scaling** (fe:2401-2403) — M1 Consumer #2 + #3:
```python
offense *= (attacker_state.stamina / 100)
defense *= (defender_state.stamina / 100)
```

**Rocked defender** (fe:2405-2407): `if defender_state.is_rocked: defense *= 0.5`.

**Variance** (fe:2409-2412): `variance = random.uniform(0.75, 1.25); offense *= variance` — ±25% one-sided (offense only). RNG: 1× `random.uniform`.

**Base success chance** (fe:2414-2416):
```python
success_chance = 0.20 + (offense / (offense + defense + 1)) * 0.5
success_chance = max(0.15, min(0.85, success_chance))
```
Bounded [0.15, 0.85]. Additive-constant `1` in denominator matters at very low offense+defense.

**Upset branch** (fe:2418-2425) — fires when `offense < defense * 0.85`:
```python
upset_roll = random.random()
if upset_roll < 0.18:
    success_chance = max(success_chance, 0.70)
elif upset_roll < 0.35:
    success_chance = min(success_chance + 0.22, 0.70)
```
RNG: 1× `random.random()` conditional.

**Land roll** (fe:2427): `landed = random.random() < success_chance`. RNG: 1× `random.random()`.

**Counter check** (fe:2429-2432): `if landed and defender.fight_iq > 60 and random.random() < 0.15: was_counter = True`. RNG: 1× `random.random()` conditional.

### 3.2 [both] `calculate_strike_damage(attacker, defender, strike, attacker_state, defender_state, was_counter=False, is_dominant_position=False)` → `Tuple[float, str]` — fe:2423

Returns `(damage, target_area)`.

**Base damage** (fe:2456-2459):
```python
base_damage, ko_power, stamina_cost, target = STRIKE_PROPERTIES[strike]
damage = base_damage + (attacker.strength - 50) / 10
```

**Power puncher bonus** (fe:2461-2463): CROSS/HOOK/OVERHAND → `damage *= 1 + (attacker.strength / 200)` (up to +47.5% at str=95).

**Skill-into-damage (STRIKE-SKILL-DMG1 phase 1a, fe:2465-2485)**:
```python
_skill = attacker.boxing        # or .kicks or .clinch_striking per family
damage *= max(STRIKE_SKILL_DAMAGE_FLOOR,
              1 + (STRIKE_SKILL_DAMAGE_K * (_skill - 75) / 100))
```
Constants: `STRIKE_SKILL_DAMAGE_K = 1.0`, `STRIKE_SKILL_DAMAGE_FLOOR = 0.25`. At K=1.0, legal skill 1-99, factor range [0.26, 1.24] (floor deterministically inert).

**Kick-gap damage (STRIKE-SKILL-DMG1 phase 1b, fe:2495-2499)**:
```python
if "kick" in strike.value.lower():
    _kick_gap = attacker.kicks - defender.kicks
    damage *= max(KICK_GAP_DAMAGE_FLOOR,
                  min(KICK_GAP_DAMAGE_CEIL,
                      1 + (KICK_GAP_DAMAGE_K * _kick_gap / 100)))
```
Constants: `KICK_GAP_DAMAGE_K = 1.0`, floor `0.5`, ceil `1.5`. Clamps ACTIVE at gap ±98 (99-vs-1 legal skill range).

**Counter bonus** (fe:2501-2503): `if was_counter: damage *= 1.3`.

**Stamina-to-damage factor (STAMINA-DMGCURVE1 wire, fe:2505-2506)** — M1 Consumer #4:
```python
damage *= damage_stamina_factor(attacker_state.stamina)
```
`damage_stamina_factor(stamina)` at fe:557-562 = `(s/100)*0.5 + 0.5` at identity (DMG_PIVOT=0.0, DMG_COMPRESS=1.0). Range [0.5, 1.0] at stamina [0, 100]. **50% floor at zero stamina** — the sole non-linear stamina consumer.

**Compromised chin bump** (fe:2508-2510): `if target == "head" and defender_state.chin_compromised: damage *= 1.2`.

**GNP-DAMAGE-BUFF1** (fe:2519-2521): `if is_dominant_position: damage *= GNP_DOMINANT_DAMAGE_MULT` (= 1.25). Read from top-of-dominant-position check downstream in `simulate_exchange` (fe:3388-3394 for fe path; fi has a different composition — see Divergence Table).

**Variance** (fe:2523-2524): `damage *= random.uniform(0.8, 1.2)` — ±20%. RNG: 1× `random.uniform`.

### 3.3 [both] `calculate_grappling_success(attacker, defender, action, attacker_state, defender_state, fight_state)` → `bool` — fe:2529

Per-action-family `(offense, defense, base_chance, multiplier)` tuples:
| action family | offense | defense | base | mult |
|---|---|---|---:|---:|
| SINGLE_LEG / DOUBLE_LEG | `attacker.takedowns` | `defender.takedown_defense + defender.speed//4` | 0.08 | 0.32 |
| BODY_LOCK_TAKEDOWN | `(attacker.takedowns + attacker.top_control) // 2` | `defender.takedown_defense + defender.strength//4` | 0.22 | 0.38 |
| TRIP / HIP_TOSS / SUPLEX | `(attacker.takedowns + attacker.top_control) // 2` | `(defender.takedowns + defender.top_control) // 2 + defender.strength//4` | 0.20 | 0.40 |
| PASS_TO_SIDE / PASS_TO_MOUNT / KNEE_SLICE | `attacker.top_control` | `defender.guard` | 0.28 | 0.55 |
| SCISSOR/BUTTERFLY/FLOWER SWEEP | `attacker.guard` | `defender.top_control + defender.strength//4` | 0.20 | 0.45 |
| SHRIMP/BRIDGE ESCAPE | `(attacker.guard + attacker.takedowns)//2 + attacker.strength//2` | `defender.top_control + defender.strength//2` | 0.48 | 0.50 |
| STAND_UP | `(attacker.guard + attacker.takedowns)//2 + attacker.strength//3` | `defender.top_control + defender.strength//3` | 0.28 | 0.45 |
| CLINCH_ENTRY | `(attacker.takedowns + attacker.clinch_control) // 2` | `defender.striking_defense + defender.speed//3` | 0.20 | 0.35 |
| CLINCH_BREAK | `attacker.strength//2 + attacker.speed//4` | `defender.top_control + defender.strength//2` | 0.15 | 0.38 |
| default | `attacker.takedowns` | `defender.guard` | 0.25 | 0.55 |

Each family also has per-attribute-threshold ±bonuses to `base_chance` (e.g. `takedown_diff >= 35: base_chance += 0.04`).

**Stamina scaling** (fe:2719-2721) — M1 Consumers #5, #6:
```python
offense *= (attacker_state.stamina / 100)
defense *= (defender_state.stamina / 100)
```

**Variance** (fe:2723-2726): `variance = random.uniform(0.75, 1.25); offense *= variance` — ±25% one-sided.

**Success chance** (fe:2728-2730):
```python
success_chance = base_chance + (offense / (offense + defense + 1)) * multiplier
success_chance = max(0.12, min(0.88, success_chance))
```
Bounded [0.12, 0.88].

**Upset branch** (fe:2732-2738) — same shape as strike upset, `offense < defense * 0.85`:
- upset_roll < 0.18: `success_chance = max(success_chance, 0.65)`
- upset_roll < 0.35: `success_chance = min(success_chance + 0.25, 0.75)`

Land: `return random.random() < success_chance`.

### 3.4 [both] `attempt_submission(attacker, defender, sub_type, attacker_state, defender_state, fight_state)` → `Tuple[bool, bool, float]` — fe:2981
Returns `(locked_in, finished, progress)`.

**Position gate** (fe:3003-3004): `if fight_state.position not in SUBMISSION_PROPERTIES[sub_type][2]: return False, False, 0.0` — sub only attemptable from position set defined at fe:303-343.

**Offense/defense composition** (fe:3006-3010):
```python
offense = attacker.submissions + (danger / 10)
defense = (defender.guard + defender.submissions) // 2 + (escape_diff / 10)
```
Where `danger` and `escape_diff` come from `SUBMISSION_PROPERTIES[sub_type]`.

**Sub differential bonus** (fe:3012-3028) — MASSIVE modifier via `sub_diff = attacker.submissions - defender.submissions`:
| sub_diff | sub_bonus |
|---:|---:|
| ≥40 | +0.35 |
| ≥30 | +0.28 |
| ≥20 | +0.20 |
| ≥10 | +0.12 |
| ≤−10 | −0.08 |
| ≤−20 | −0.18 |
| ≤−30 | −0.30 |

**Specialist bonus** (fe:3030-3034): attacker.submissions ≥92 → +0.15; ≥88 → +0.08.

**Stamina scaling** (fe:3036-3038) — M1 Consumers #7, #8:
```python
offense *= (attacker_state.stamina / 100)
defense *= (defender_state.stamina / 100)
```

**Lock-in chance** (fe:3046-3052):
```python
lock_in_chance = 0.30 + sub_bonus + (offense / (offense + defense + 1)) * 0.55
_sub_cap = min(0.70, 0.50 + max(0, attacker.submissions - 75) * 0.013)
lock_in_chance = min(_sub_cap, lock_in_chance)
```
Cap: 60 subs → 0.50; 80 subs → 0.70. `locked_in = random.random() < lock_in_chance`.

If not locked: return `(False, False, 0.0)`.

**On lock-in** (fe:3057-3083): sets `fight_state.submission_active=True`, `submission_type=sub_type`, `submission_attacker_id=attacker.fighter_id`. Starting progress:
```python
base_progress = offense * 0.15  # low base — race plays out
if attacker.submissions >= 92: base_progress *= 1.4
elif attacker.submissions >= 88: base_progress *= 1.2
if sub_diff >= 30: base_progress *= 1.6
elif sub_diff >= 20: base_progress *= 1.25
elif sub_diff >= 10: base_progress *= 1.2
fight_state.submission_progress = base_progress
fight_state.submission_escape_progress = 0.0
```

### 3.5 [both] `process_submission_progress(attacker, defender, attacker_state, defender_state, fight_state, config)` → `Tuple[bool, bool]` — fe:3086
Returns `(escaped, finished)`. Called each exchange while `submission_active`.

**Tighten (attacker offense)** (fe:3117, fe:3131-3132) — M1 Consumer #9:
```python
offense = attacker.submissions * (attacker_state.stamina / 100)
tighten_rate = 0.65 if attacker.submissions >= 92 else 0.45
fight_state.submission_progress += offense * tighten_rate * random.uniform(0.75, 1.25)
```
RNG: 1× `random.uniform`.

**Escape (defender)** (fe:3136-3138) — M1 Consumer #10:
```python
defense = ((defender.guard + defender.submissions) // 2) * (defender_state.stamina / 100)
defense += defender.heart * 0.03
fight_state.submission_escape_progress += defense * 0.38 * random.uniform(0.75, 1.25)
```
RNG: 1× `random.uniform`.

**Stamina drain** (fe:3141-3142):
```python
attacker_state.spend_stamina(3)
defender_state.spend_stamina(5)
```
Defender takes MORE drain (fe:3105 comment: "Being submitted is exhausting").

**Finish check** (fe:3144-3147):
```python
if fight_state.submission_progress >= config.submission_progress_to_finish:  # default 70.0
    fight_state.submission_active = False
    return False, True
```

**Escape check** (fe:3149-3164):
```python
_def_stamina = defender_state.stamina
_composure = defender.composure
_composure_bonus = (_composure - 70) * 0.002
_fatigue_escape_mult = max(0.55, _def_stamina / 100 + 0.3 + _composure_bonus)
effective_escape = config.submission_escape_threshold * _fatigue_escape_mult  # 85.0 × factor
if fight_state.submission_escape_progress >= effective_escape:
    fight_state.submission_active = False
    return True, False
```
Effective threshold dynamic based on defender stamina + composure. RANGE: at fresh defender + composure=70, mult=1.3; at gassed + composure=70, mult=0.55; effective escape at 0.55×85=46.75 (easier to escape when gassed... but defender's escape progress also lower when gassed via defender_state.stamina scaling above).

---

## §4 Strike execution (exchange integration)

### 4.1 [fe] Strike branch in `simulate_exchange` — fe:3349-3595

After `select_action` returns `("strike", strike)`:

1. **Success roll**: `landed, was_counter = calculate_strike_success(...)` (fe:3351-3353).
2. **Stamina cost** (fe:3355-3356): `_, _, stamina_cost, _ = STRIKE_PROPERTIES[strike]; attacker_state.spend_stamina(stamina_cost)`.
3. **Round stat**: `round_stats[attacker.fighter_id].significant_strikes_attempted += 1`.
4. If landed:
   - `damage, target = calculate_strike_damage(...)` (fe:3362-3364)
   - **Wrestler-threat damage reduction** (fe:3369-3383, STANDING only):
     ```python
     takedown_threat = defender.takedowns - attacker.takedowns
     if takedown_threat >= 30: damage *= 0.65
     elif takedown_threat >= 20: damage *= 0.75
     elif takedown_threat >= 10: damage *= 0.85
     sub_threat = defender.submissions - attacker.submissions
     if sub_threat >= 30: damage *= 0.85
     elif sub_threat >= 20: damage *= 0.92
     ```
   - **GNP dominant-position bump** (fe:3388-3394): DOMINANT positions (BACK_MOUNT, MOUNT, SIDE_CONTROL_TOP, CRUCIFIX_TOP, NORTH_SOUTH_TOP) → `damage *= GNP_DOMINANT_DAMAGE_MULT` (1.25).
   - **Config damage multiplier** (fe:3397): `damage *= config.damage_multiplier` (=0.48 LIVE_PLAY, may be scaled up to 0.576 by heat).
   - **Apply damage** (fe:3399): `is_knockdown, is_finish = defender_state.apply_damage(damage, target)`.
   - **Leg-kick TKO check** (fe:3404-3421): if target=="legs" and `defender_state.damage.is_compromised_legs`:
     ```python
     _leg_tko_chance = min(0.15, (leg_kicks_absorbed - 6) * 0.02)
     if defender_state.stamina < 50: _leg_tko_chance *= 1.4  # M1 Consumer #11
     if random.random() < _leg_tko_chance: return (attacker.fighter_id, "TKO (Leg Kicks)")
     ```
     **Finish path #A [fe]**.
   - **Cut accumulation from elbows** (fe:3423-3432) — WRITE to `defender_state.damage.cuts`:
     ```python
     _elbow_types = {"elbow_horizontal", "elbow_vertical", "elbow_spinning",
                     "elbow_upward", "gnp_elbow", "clinch_elbow"}
     if _st_val in _elbow_types and target == "head":
         _cut_chance = 0.25 + (attacker.strength / 400)
         if random.random() < _cut_chance:
             defender_state.damage.cuts += 1
     ```
     **fe-only cut writer** — fi doesn't have this (per fi:1762-1770 comment). Cuts read by between-round doctor stoppage.
   - **Flash-KO** (fe:3434-3447):
     ```python
     if not is_finish and target == "head" and damage >= 5:
         flash_ko_chance = 0.01
         if attacker.boxing >= 75 or attacker.strength >= 75:
             flash_ko_chance *= 1.5
         elif attacker.boxing >= 65 or attacker.strength >= 65:
             flash_ko_chance *= 1.2
         if defender_state.health < 40: flash_ko_chance *= 2.0
         flash_ko_chance = min(0.12, flash_ko_chance)
         if random.random() < flash_ko_chance: is_finish = True
     ```
     Note: fe-side flash KO uses base 0.01 with skill-tiered multipliers. **Differs from fi's flash-KO** which uses module constants `FLASH_KO_DAMAGE_THRESHOLD=70.0`, `FLASH_KO_BASE_CHANCE=0.03`, `FLASH_KO_MAX_CHANCE=0.12`. See Divergence Table.
   - **Momentum** (fe:3459): `attacker_state.momentum = min(100, attacker_state.momentum + damage * 0.3)`.
   - **Named finish types on `is_finish`** (fe:3474-3501): specialty map — flying_knee → "KO (Flying Knee)", wheel_kick, spinning_elbow, head_kick, knee_head, spinning_back_kick, superman_punch, body_kick/knee_body/front_kick → "TKO (Body Shot)". Else → "KO" or "TKO (Body Shot)" if target=="body". **Finish path #B [fe]**.
   - **Referee stoppage — unanswered shots while rocked** (fe:3503-3524):
     ```python
     if not is_finish and defender_state.is_rocked and target == "head":
         defender_state._rocked_shots_taken += 1  # accumulator
         _ref_stop_chance = min(0.35, _rocked_shots_taken * 0.08)
         _ref_stop_chance *= max(0.4, 1 - (defender.fight_iq / 250) - (defender.heart / 350))
         if random.random() < _ref_stop_chance:
             return (attacker.fighter_id, "TKO (Referee Stoppage)")
     ```
     **Finish path #C [fe]**. Accumulator: `_rocked_shots_taken`, reset when rock ends (fe:3849/3854).
   - **Rocked → grappler exploit** (fe:3526-3570): if defender rocked + target head + STANDING:
     - attacker.takedowns ≥ 68: chance to force position to BACK_MOUNT (55%) or MOUNT.
     - attacker.submissions ≥ 65 (+ ≥2 rocked shots): chance to STANDING_BACK.
     NO finish returned here — position change only.
   - **Knockdown side effect** (fe:3572-3583): sets `fight_state.position = Position.KNOCKDOWN_STANDING`, `top_fighter_id = attacker.fighter_id`.

### 4.2 [fi] `_execute_strike(...)` — fi:767 (spans ~530 lines to fi:1300)

Same shape, more mechanics. Additions/differences vs fe:
- **Adrenaline surge decrement** (fi:780-784): `_surge_exchanges` window per attacker_state, decays momentum.
- **Style-specific pre-strike modifiers** (fi:800-870): Counter Striker `_counter_mult`, Brawler `_brawler_mult`, Karate patience flag consumption, Point Fighter movement window bump.
- **Strength KO amplification** (fi:880-886) [fe lacks equivalent]:
  ```python
  if target_area == 'head':
      _str = attacker.strength
      _str_mod = 1.0 + max(0, _str - 70) * 0.003
      damage *= _str_mod
  ```
- **Muay Thai knee amplification** (fi:888-900) [fe lacks]: `knee_head` → ×1.30×1.10 = ×1.43; `knee_body` → ×1.30.
- **Counter Striker damage multiplier** (fi:902-904) [fe lacks].
- **Brawler counter damage** (fi:906-908) [fe lacks].
- **Karate patience power** (fi:910-915) [fe lacks]: `damage *= 1.40` on next head strike after patience window.
- **Point Fighter defender movement dampen** (fi:917-922) [fe lacks]: `damage *= 0.80` when defender in movement window.
- **Brawler walk-through** (fi:924-941) [fe lacks]: chin-tiered chance to reduce incoming damage ×0.75 and set counter power.
- **Point Fighter movement window write** (fi:943-948) [fe lacks]: `attacker_state._movement_window = 2` on landing.
- **Apply damage** (fi:951-953): `caused_knockdown, is_finish = defender_state.apply_damage(damage, target_area)` — same primitive as fe.
- **Body-shot stamina drain** (fi:955-959) [fe lacks equivalent]: `defender_state.spend_stamina(damage * 0.4)`.
- **Clinch body accumulator TKO** (fi:961-991) [fe lacks — fi-only accumulator #1]:
  ```python
  if target_area == 'body' and _in_clinch_pos:
      _cb_rate = 1.4 if 'MUAY_THAI' in _att_style else 1.0
      defender_state._clinch_body_acc = _prev_cb + damage * _cb_rate
      if defender_state._clinch_body_acc >= 30:
          _cb_tko = min(0.22, (_clinch_body_acc - 25) * 0.025)
          _cb_tko *= max(0.4, 1 - defender.heart/320 - defender.composure/450)
          if random.random() < _cb_tko:
              return (attacker.fighter_id, "TKO (Body Shots)")
  ```
  **Finish path #1 [fi]**. Accumulator: `_clinch_body_acc`, reset when position not in CLINCH_POSITIONS.
- **Knockdown stamina tax** (fi:993-997) [fe lacks equivalent]: `defender_state.spend_stamina(8)` on knockdown.
- **GnP accumulator TKO** (fi:999-1033) [fe lacks — fi-only accumulator #2]:
  ```python
  if not is_finish and _in_gnp_pos and target_area == 'head':
      _rate = 1.2 if 'GROUND' in _att_gnp_style else 1.0
      if 'MOUNT' in _gnp_pos_check: _rate *= 1.1
      defender_state._gnp_accumulation = _prev_gnp + damage * _rate
      if defender_state._gnp_accumulation >= 75:
          _gnp_tko = min(0.22, (_gnp_accumulation - 70) * 0.025)
          _gnp_tko *= max(0.35, 1 - defender.heart/300 - defender.composure/450)
          if random.random() < _gnp_tko:
              return (attacker.fighter_id, "TKO (Ground and Pound)")
  ```
  **Finish path #2 [fi]**. Accumulator: `_gnp_accumulation`, reset when position in STANDING_POSITIONS.
- **Leg-kick TKO** (fi:1035-1047) — identical to fe:3404-3421. Both engines. **Finish path #3 [fi] / #A [fe]**.
- **Referee stoppage on unanswered rocked shots** (fi:1049-1066) — SIMILAR to fe's but different constants:
  ```python
  defender_state._rocked_shots += 1
  _ref_chance = min(0.22, _rocked_shots * 0.05)  # fe: min 0.35, mult 0.08
  _ref_chance *= max(0.35, 1 - fight_iq/250 - heart/350 - composure/400)
  ```
  fi's max is 0.22 vs fe's 0.35, per-shot 0.05 vs 0.08, and fi includes composure/400. **Finish path #4 [fi]** — see Divergence Table.
- **Rocked → grappler exploit** (fi:1068-1096) — SAME structure as fe:3526-3570.
- **V7 FLASH KO** (fi:1098-1124) [uses module constants; different from fe's inline]:
  ```python
  if not is_finish and target_area == "head" and damage >= FLASH_KO_DAMAGE_THRESHOLD:  # 70.0
      flash_ko_chance = (damage - 70) * FLASH_KO_BASE_CHANCE  # 0.03
      if attacker.boxing >= 85 or attacker.kicks >= 85: flash_ko_chance += 0.022
      if attacker.strength >= 85: flash_ko_chance += 0.015
      if defender_state.is_rocked or defender_state.health < 40: flash_ko_chance += 0.035
      flash_ko_chance = min(flash_ko_chance, FLASH_KO_MAX_CHANCE)  # 0.12
      if random.random() < flash_ko_chance:
          caused_knockdown = True; is_finish = True; defender_state.health = 0
  ```
  **Finish path #5 [fi]**. Hard-writes `defender_state.health = 0` (fe's flash KO just sets `is_finish=True` without touching health).
- **V7 TKO GNP** (fi:1126-1159) [fi-only accumulator #3 — health-threshold]:
  ```python
  if not is_finish and top_fighter_id == attacker.fighter_id \
       and defender_state.health < TKO_GNP_HEALTH_THRESHOLD (18.0) \
       and position in DOMINANT_POSITIONS:
      tko_chance = TKO_GNP_BASE_CHANCE  # 0.15
      if defender_state.is_rocked: tko_chance += 0.03
      if defender_state.knockdowns_this_round >= 2: tko_chance += 0.04
      if attacker.top_control >= 85: tko_chance += 0.02
      tko_chance = min(tko_chance, TKO_GNP_MAX_CHANCE)  # 0.45
      tko_chance *= _tko_durability_mult(defender)  # GROUND-STOPPAGE-FIX1
      if random.random() < tko_chance: is_finish = True
  ```
  **Finish path #6 [fi]**.
- **V7 TKO STANDING** (fi:1161-1186) [fi-only accumulator #4 — health-threshold]:
  ```python
  if not is_finish and defender_state.is_rocked \
       and defender_state.health < TKO_STANDING_HEALTH_THRESHOLD (15.0) \
       and position in STANDING_POSITIONS:
      tko_standing_chance = TKO_STANDING_BASE_CHANCE  # 0.10
      if defender_state.health < 20: tko_standing_chance += 0.05
      if defender_state.knockdowns_this_round >= 1: tko_standing_chance += 0.04
      tko_standing_chance *= _tko_durability_mult(defender)
      if random.random() < tko_standing_chance: is_finish = True
  ```
  **Finish path #7 [fi]**.
- **Named specialty finishes on `is_finish`** (fi:1211-1235) — similar map to fe but classifies method differently:
  - `if defender_state.health <= 0: method = _specialty_map.get(_sv, "KO")`
  - Else: `if target_area == "body": method = _specialty_map.get(_sv, "TKO (Body Shot)"); else: method = "TKO"`
  **Finish path #8 [fi]**.
- **Miss** (fi:1255-1257): only `significant_strikes_attempted += 1`.

**`_tko_durability_mult(defender)` helper** (fi, exact site not extracted; per GROUND-STOPPAGE-FIX1 filing):
```python
max(TKO_DURABILITY_FLOOR (0.35),
    1 - chin/CHIN_DIVISOR (300) - heart/HEART_DIVISOR (350) - composure/COMP_DIVISOR (450))
```
Applied to V7 TKO_GNP + V7 TKO_STANDING. Elite (chin/heart/composure=90) → clamps to 0.35 (halves TKO roll). Poor (all 40) → 0.67 (unclamped).

---

## §5 Grappling execution

### 5.1 [fe] Grappling branch — fe:3642-3782

After `select_action` returns `("grappling", action)`:
1. `success = calculate_grappling_success(...)` (fe:3644-3646)
2. Round stats: takedowns_attempted/landed on SINGLE_LEG/DOUBLE_LEG/BODY_LOCK_TAKEDOWN; reversals on sweep_actions or escape_actions if success.
3. Stamina cost (fe:3673): `attacker_state.spend_stamina(4)` (fe:3659 for another grappling branch: `spend_stamina(4)`).
4. If success: `apply_position_change(fight_state, action, attacker.fighter_id, True)` returns `new_pos`. Momentum shift +10 attacker / −10 defender on DOMINANT_POSITIONS transition (fe:3731-3733).
5. If failure: **failed grappling counter damage** (fe:3749-3782, STANDING or CLINCH):
   - clinch_skill = `max(defender.clinch_striking, defender.clinch_control)`
   - clinch_skill ≥ 85: counter_damage = `random.uniform(5, 10)`
   - ≥ 75: `random.uniform(3, 7)`
   - ≥ 65: `random.uniform(2, 5)`
   - Else defender.boxing ≥ 80: `random.uniform(3, 6)`
   - `counter_damage *= config.damage_multiplier`
   - `attacker_state.apply_damage(counter_damage, "head")` + momentum shift ±8

### 5.2 [both] `apply_position_change(fight_state, action, attacker_id, success)` — fe:2743
Deterministic-in-action, weighted-random-in-outcome via `_weighted_choice`. Each action has its outcome distribution:
- SINGLE_LEG: 50 HALF_GUARD_TOP / 30 FULL_GUARD_TOP / 15 SIDE_CONTROL_TOP / 5 STANDING_OPEN
- DOUBLE_LEG: 45 FULL_GUARD_TOP / 30 HALF_GUARD_TOP / 20 SIDE_CONTROL_TOP / 5 MOUNT
- BODY_LOCK_TAKEDOWN: 50 SIDE_CONTROL_TOP / 25 HALF_GUARD_TOP / 18 MOUNT / 7 BACK_MOUNT
- PASS_TO_SIDE: 70 SIDE_CONTROL_TOP / 25 HALF_GUARD_TOP / 5 NORTH_SOUTH_TOP
- SCISSOR_SWEEP / FLOWER_SWEEP: 50 MOUNT / 35 FULL_GUARD_TOP / 15 SIDE_CONTROL_TOP
- (etc — full outcome distributions at fe:2757-2960)

Also updates `fight_state.dominant_control_duration` (+1 in dominant cluster, reset otherwise, fe:2962-2965).

### 5.3 [fi] `_execute_grappling(...)` — fi:1303
Similar dispatch; NOT extracted line-by-line for this pass. Key: fi has its own `_execute_grappling` and `_execute_submission_attempt` (fi:1445) methods that mirror fe's inline logic but with fi-specific commentary hooks and its own accumulator writes.

---

## §6 Damage & state updates

### 6.1 [both] `FighterState.apply_damage(amount, target="head")` — fe:591-630
Returns `(is_knockdown, is_finish)`.

**Writes**:
- `self.damage.apply_damage(amount, target)` (fe:593) — dispatches to head/body/legs accumulators + increments `leg_kicks_absorbed` on legs.
- `self.health = max(0, self.health - amount)` (fe:594)
- `self.momentum = max(0, self.momentum - amount * 0.5)` (fe:595)

**Finish paths (inside apply_damage)**:
- `health <= 0` → `is_finish = True` (fe:600-601). **Finish path #D [both]**.
- Body damage TKO (fe:602-607): `target == "body" and damage.body >= 65` → chance `min(0.40, (body - 65) * 0.04)` → `is_finish`. **Finish path #E [both]** — CO-RESIDENT in both engines (same primitive).
- Head damage with amount ≥ 12 (fe:608-628):
  - **Chin erosion accumulator** [both, via primitive]: `_erosion = getattr(self, '_chin_erosion', 0)`; `_erosion_mult = 1.0 + min(0.30, _erosion * 0.025)`.
  - Knockdown roll: `random.random() < amount * 0.015 * _erosion_mult` → set `is_knockdown`; `knockdowns_this_round += 1`; `knockdowns_total += 1`; `_chin_erosion = _erosion + 4`.
  - Else, rock roll: `random.random() < amount * 0.025 * _erosion_mult` → `is_rocked = True`; `spend_stamina(4)` (rocked stamina drain); `rock_duration = max(1, random.randint(1,3) - reduction)` where reduction = 1 if recovery ≥ 80 else 0.

**Hidden state**: `_chin_erosion` (INT, defaulted via getattr — never explicitly written outside apply_damage, never reset). Accumulates for the whole fight per fighter.

### 6.2 [both] `FighterState.spend_stamina(amount)` — fe:635-640 (STAMINA-DRAIN1 wire)
```python
def spend_stamina(self, amount: float) -> None:
    effective = amount * DRAIN_SCALE_K * (1 + DRAIN_CARDIO_S * (60 - self.cardio_rating) / 40)
    self.stamina = max(0, self.stamina - effective)
```
Constants: `DRAIN_SCALE_K=0.6`, `DRAIN_CARDIO_S=0.5`, `cardio_rating` default 60. Floor at 0 via `max(0, ...)`.

### 6.3 [both] `FighterState.recover_stamina(amount)` — fe:632-633
```python
def recover_stamina(self, amount: float) -> None:
    self.stamina = min(100, self.stamina + amount)
```
Ceiling 100 via `min(100, ...)`. Unscaled by any dial.

### 6.4 [both] `FighterState.new_round()` — fe:642-672
- Reset per-round: `knockdowns_this_round = 0`, `is_knocked_down = False`.
- R1-REFILL1 guard (fe:656): `if getattr(self, '_current_round', 0) != 1:` — refill only fires R2+.
- Refill formula (fe:657-664):
  ```python
  base_recovery = 15
  bonus_recovery = (recovery_rating / 100) * 25
  if _current_round >= 4: bonus_recovery *= 1.3  # championship-round bonus
  self.stamina = min(100, self.stamina + base_recovery + bonus_recovery)
  ```
- Health regain (fe:667-669): `health_regain = recovery_rating * 0.08`; `self.health = min(max_health, self.health + health_regain)`.
- Reset rocked: `is_rocked = False; rock_duration = 0` (fe:671-672).

### 6.5 [fi] `_init_round()` — fi:590+ (per prior filings; not fully extracted this pass)
Between-round side of fi's loop. Calls `FightState.new_round()` (which per C10 PREGEN-ROUND-WIRE1 propagates `_current_round` to each FighterState). Also applies:
- Corner bonus recovery (fi:600-612): `bonus_stamina = 15 * corner_bonus_f{1,2}`; adds via `self.fighter{1,2}_state.stamina = min(100, ... + bonus_stamina)` [fi-only recovery site, K×g bypass by design per B7].
- Fatigue penalty subtraction (fi:623-625): `self.fighter{1,2}_state.stamina = max(0.0, ... - self._fatigue_penalty_f{1,2})` [fi-only drain site, K×g bypass per B7/DMGCURVE1 mutation census].

### 6.6 [both] `FightState.new_round()` — fe:769-782 (per prior filings)
- Reset per-round FightState fields (`exchanges_this_round`, `ground_inactivity`, `dominant_control_duration`, `submission_active`).
- C10 propagation: `self.fighter1._current_round = self.current_round; self.fighter2._current_round = self.current_round`.
- Calls `self.fighter1.new_round()` + `self.fighter2.new_round()` (fe:781-782).

### 6.7 [both] `BodyPartDamage.apply_damage(amount, target)` — fe:525-532
Just accumulates:
- `target == "head"`: `self.head += amount`
- `target == "body"`: `self.body += amount`
- `target == "legs"`: `self.legs += amount; self.leg_kicks_absorbed += 1`

Properties: `total`, `is_compromised_legs = leg_kicks_absorbed >= 6 or legs >= 50`, `is_cut_badly = cuts >= 3`. `cuts` field written only by fe:3432 (elbow-to-head cut writer); fi doesn't write.

---

## §7 Post-exchange bookkeeping

### 7.1 [fe] Control time (fe:3784-3792)
```python
if fight_state.is_ground and fight_state.top_fighter_id:
    round_stats[top].ground_control_time += 1
    round_stats[top].control_time += 1
elif fight_state.is_clinch:
    if fight_state.cage_controller_id:
        round_stats[controller].clinch_control_time += 1
        round_stats[controller].control_time += 1
```

### 7.2 [fe] Referee standup (fe:3794-3803)
```python
if fight_state.is_ground and not fight_state.submission_active:
    fight_state.ground_inactivity += 1
    if fight_state.ground_inactivity >= config.standup_threshold:  # 10
        fight_state.position = Position.STANDING_OPEN
        fight_state.top_fighter_id = None
        fight_state.ground_inactivity = 0
        fight_state.dominant_control_duration = 0
elif not fight_state.is_ground:
    fight_state.ground_inactivity = 0
```

**Divergence**: fi tracks `_ground_action_this_exchange` (fi:696, fi:1190-1192, fi:759) and gates referee-standup on `not _ground_action_this_exchange`. fe has no such guard — standup fires purely on `ground_inactivity` counter. See Divergence Table.

### 7.3 [fe] Back-control stalemate break (fe:3805-3838)
Prevents infinite BACK_MOUNT ↔ TRUCK cycling:
```python
_BACK_CONTROL_POSITIONS = {BACK_MOUNT, TRUCK, BACK_MOUNT_BOTTOM}
if position in _BACK_CONTROL_POSITIONS and not submission_active \
   and dominant_control_duration >= 12:
    escape_roll = random.random()
    if escape_roll < 0.45:
        fight_state.position = Position.STANDING_OPEN
        ...  # escape logs
    else:
        fight_state.dominant_control_duration = 8  # reset partway
```
RNG: 1× `random.random()` conditional.

### 7.4 [fe] Per-exchange stamina recovery (fe:3840-3842)
```python
attacker_state.recover_stamina(0.5)
defender_state.recover_stamina(0.5)
```
Constant +0.5 per exchange BOTH fighters. Unaffected by K×g (recover_stamina is unscaled). **fi has the same** at fi:1651-1652 per prior filings.

### 7.5 [fe] Rock duration decrement (fe:3844-3854)
```python
if fighter1_state.is_rocked:
    fighter1_state.rock_duration -= 1
    if rock_duration <= 0:
        fighter1_state.is_rocked = False
        fighter1_state._rocked_shots_taken = 0  # accumulator reset
# same for fighter2
```
`_rocked_shots_taken` accumulator reset here — the only site.

---

## §8 Round-end + between-round stoppages

### 8.1 [fe] Between-round stoppages — fe:4206-4280

Fires when `round_num < config.scheduled_rounds`. Loops both fighters (each as `_ftr`, `_ftr_state`, `_opp = other`):

1. **Cut stoppage** (fe:4220-4226):
   ```python
   _cut_thr = config.doctor_check_cut_threshold  # default 3
   if _ftr_state.damage.cuts >= _cut_thr:
       _cut_stop_chance = min(0.35, (cuts - (thr-1)) * 0.08)
       _cut_stop_chance *= max(0.4, 1 - _ftr.heart / 200)
       if random.random() < _cut_stop_chance: _stop = "TKO (Doctor Stoppage - Cuts)"
   ```
   **fe-only** (fi:1762-1770 comment: "cut-stoppage branch that used to sit here was unreachable — fight_integration never writes damage.cuts").
   **Finish path #F [fe]**.

2. **Doctor stoppage** (fe:4229-4239) [both engines have this]:
   ```python
   if health < 28 and damage.head > 55:
       _doc_chance = min(0.14, (55 - health) * 0.003)
       _doc_chance *= max(0.5, 1 - heart / 250)
       if chin_compromised: _doc_chance *= 1.35
       if random.random() < _doc_chance: _stop = "TKO (Doctor Stoppage)"
   ```
   **Finish path #G [fe] / #9 [fi]** — fi:1772-1782 mirrors this exactly.

3. **Corner stoppage** (fe:4242-4251) [both engines]:
   ```python
   if round_num >= 2 and health < 22 and knockdowns_total >= 2:
       _corner_chance = min(0.18, (knockdowns_total - 1) * 0.06)
       _corner_chance *= max(0.3, 1 - heart / 300)
       if random.random() < _corner_chance: _stop = "TKO (Corner Stoppage)"
   ```
   **Finish path #H [fe] / #10 [fi]** — fi:1784-1794 mirrors.

### 8.2 [fe] Round scoring — after between-round-stoppage check
```python
s1, s2 = score_round(
    round_stats[fighter1.fighter_id],
    round_stats[fighter2.fighter_id],
    f1_state.knockdowns_this_round,
    f2_state.knockdowns_this_round
)
round_scores.append((s1, s2))
```

### 8.3 [fi] Round scoring — fi:1802-1812 [swapped KD arg convention]:
```python
score1, score2 = score_round(
    self.round_stats[fighter1.fighter_id],
    self.round_stats[fighter2.fighter_id],
    self.fighter2_state.knockdowns_this_round,  # KDs INFLICTED BY f1 (suffered by f2)
    self.fighter1_state.knockdowns_this_round,  # KDs INFLICTED BY f2 (suffered by f1)
)
```
**Divergence**: fe passes `knockdowns_this_round` matched-order (fe:4286-4287); fi passes swapped (fi:1808-1809) with comment claiming score_round expects inflicted-not-suffered. See Divergence Table.

---

## §9 Scoring (`score_round`) — fe:3863-3933 [both]

Shared primitive.

**Component scoring** (fe:3874-3890):
```python
score1 = (
    stats1.damage_dealt * 1.5 +
    stats1.significant_strikes_landed * 1.0 +
    stats1.takedowns_landed * 8.0 +
    stats1.control_time * 1.5 +
    stats1.knockdowns * 20.0 +
    stats1.submission_attempts * 4.0
)
# score2 identical structure
```

**Weighting** (constants inline):
| stat | weight |
|---|---:|
| damage_dealt | 1.5 |
| significant_strikes_landed | 1.0 |
| takedowns_landed | 8.0 |
| control_time | 1.5 |
| knockdowns | 20.0 |
| submission_attempts | 4.0 |

**Automatic 10-8/10-7 for multi-KD** (fe:3893-3896): 2+ KDs vs 0 → (10, 8) if exactly 2 else (10, 7).

**Single KD advantage** (fe:3899-3906): + score-ratio check for 10-8 vs 10-9.

**No knockdowns — ratio-based** (fe:3908-3933):
- total < 10: winner by score, 10-9 or 10-10 draw
- ratio ≥ 0.75 AND score1 ≥ 30: (10, 8)
- ratio ≤ 0.25 AND score2 ≥ 30: (8, 10)
- ratio ≥ 0.52: (10, 9)
- ratio ≤ 0.48: (9, 10)
- else: (10, 10) — even round

---

## §10 Decision resolution — fe:4310-4570 (fi similar)

**Dominance computation** (fe:4310-4329):
```python
f1_rounds = sum(1 for s1, s2 in round_scores if s1 > s2)
f2_rounds = sum(1 for s1, s2 in round_scores if s2 > s1)
if f1_rounds > f2_rounds:
    winner_dominance = 0.5 + (f1_rounds - f2_rounds) / (scheduled_rounds * 2)
elif f2_rounds > f1_rounds:
    winner_dominance = 0.5 - (f2_rounds - f1_rounds) / (scheduled_rounds * 2)
else:  # tied rounds
    if f1_total_strikes > f2_total_strikes: winner_dominance = 0.52
    elif f2 > f1: winner_dominance = 0.48
    else: winner_dominance = 0.5
```

**Judges system** (fe:4332-4400) — if `JUDGES_AVAILABLE`:
`generate_decision(winner_dominance, total_rounds, is_title_fight, fighter1_name, fighter2_name)` returns per-judge scorecards. Tiebreaker: cumulative-judge-totals; only "true draw" when sums exactly equal. `decision_type` from `decision_result.decision_type.value` (Unanimous / Majority / Split); tiebreaker case forces "Split".

---

## §11 DIVERGENCE TABLE (first-class)

Every asymmetry between fe and fi in the fight-resolution pipeline. Row per divergence.

| # | Divergence | fe site | fi site | shape |
|---:|---|---|---|---|
| 1 | Max health formula | `100.0 + chin * 0.3` (fe:4091) | `100.0 + chin * 0.5` (fi:513) | fi fighters have MORE HP at same chin — 100+chin×0.5 vs 100+chin×0.3 → at chin=70, fe=121 vs fi=135, Δ=14 (11.6%). |
| 2 | Heat scaling | present (fe:4034-4130) | absent | fe scales damage_multiplier + composure penalty + aggression bonus by heat_level (0-100). fi has no equivalent — heat is fe-only. |
| 3 | Default FightConfig triple | `standard_fight()` → LIVE_PLAY (55, 0.48, 10) | `_no_config` path → FI_FALLBACK (55, 0.48, 6) | fi's no-config fallback uses standup_threshold=6 vs fe's 10. Both sanctioned. |
| 4 | Cut writer + cut stoppage | writes cuts on elbow-to-head (fe:3423-3432); reads cuts in between-round stoppage (fe:4220-4226) | **absent** (fi:1762-1770 comment: "unreachable — fight_integration never writes damage.cuts") | fi has no cut mechanism. Cuts as a finish-mode exist only in fe. |
| 5 | Body-shot stamina drain | absent | `defender_state.spend_stamina(damage * 0.4)` (fi:959) | fi drains defender stamina on body-shot; fe doesn't. Extra finish-pressure channel in fi. |
| 6 | Clinch body accumulator TKO | absent | `_clinch_body_acc` accumulator + TKO threshold ≥30 (fi:961-991) | fi-only finish path #1. |
| 7 | Knockdown stamina tax | absent | `defender_state.spend_stamina(8)` on knockdown (fi:996-997) | fi-only. |
| 8 | GnP accumulator TKO | absent | `_gnp_accumulation` accumulator + TKO threshold ≥75 (fi:999-1033) | fi-only finish path #2. Muay Thai ×1.1 MOUNT rate bonus. |
| 9 | Referee stoppage on rocked shots | max 0.35, per-shot 0.08, factors fight_iq+heart (fe:3503-3524) | max 0.22, per-shot 0.05, factors fight_iq+heart+composure (fi:1049-1066) | Different constants + fi adds composure. |
| 10 | Flash KO | `chance = 0.01 * skill_mult * hurt_mult`, min 0.12 (fe:3437-3446) | `chance = (damage-70)*0.03 + skill+power+hurt bumps`, capped 0.12; hard-writes health=0 (fi:1098-1124) | Wholly different formulas. fi requires damage ≥ FLASH_KO_DAMAGE_THRESHOLD (70.0); fe requires damage ≥ 5. |
| 11 | V7 TKO GNP | absent | `TKO_GNP_HEALTH_THRESHOLD=18.0`, dominant + health-under → chance up to 0.45 × durability (fi:1126-1159) | fi-only accumulator #3 (health-threshold, not damage-accumulator). |
| 12 | V7 TKO STANDING | absent | `TKO_STANDING_HEALTH_THRESHOLD=15.0`, rocked + standing → chance up to 0.10-0.19 × durability (fi:1161-1186) | fi-only accumulator #4. |
| 13 | Style-specific damage modifiers | absent (fe strike branch does not apply style-specific damage multipliers) | Muay Thai knee ×1.30-1.43 (fi:888-900), Karate patience ×1.40 (fi:910-915), Point Fighter movement dampen ×0.80 (fi:917-922), Brawler walk-through ×0.75 (fi:924-941), Counter/Brawler counter mults (fi:902-908) | fi has ~6 style windows fe lacks (per TWO-ENGINE CONSOLIDATION filing). |
| 14 | Adrenaline surge window | absent | `_surge_exchanges` decrement (fi:780-784) | fi-only mechanic. |
| 15 | Sambo chain forcing | absent | `_sambo_chain` flag → force-select position-appropriate sub (fi:729-745) | fi-only. |
| 16 | Point Fighter movement window | absent | `_movement_window` write on land (fi:943-948), read on defender damage (fi:917-922) | fi-only accumulator. |
| 17 | Brawler counter power | absent | `_brawler_counter` power (fi:924-941) | fi-only accumulator. |
| 18 | Karate patience flag | consumed nowhere in fe | `_karate_patience` write in select_action (fe:2141-2145, module-shared) + consume in fi damage (fi:910-915) | Written by shared primitive, consumed only in fi. Dead write in fe. |
| 19 | Strength KO amplification | absent | `_str_mod = 1.0 + max(0, str-70) * 0.003` on head strikes (fi:880-886) | fi-only. |
| 20 | Corner bonus recovery | absent | `bonus_stamina = 15 * corner_bonus_f{1,2}` at round start (fi:600-612) | fi-only (fi:602/612 — K×g bypasses per B7). |
| 21 | Between-round fatigue penalty | absent | `.stamina = max(0.0, .stamina - _fatigue_penalty_f{1,2})` (fi:623-625) | fi-only DRAIN that bypasses K×g. Filed under DMGCURVE1 mutation census B7 accepted. |
| 22 | `score_round` KD argument convention | matched-order (fe:4286-4287): pass f1's own KDs then f2's own | swapped (fi:1808-1809): f2's KDs then f1's, per fi comment "score_round expects KDs INFLICTED" | Meaning: if `score_round(stats1, stats2, kd1, kd2)` treats kd1 as "KDs BY fighter1" then fe passes correctly and fi swaps wrongly. Or vice versa. Sign of divergence: needs source-of-truth ruling. **AMBIGUOUS as-written** — either fe or fi is calling it wrong. |
| 23 | Referee standup activity guard | absent (fires purely on `ground_inactivity` counter, fe:3794-3803) | `_ground_action_this_exchange` guard prevents standup during active ground fighting (fi:696, fi:1190-1192, fi:759) | fi has activity-aware standup; fe doesn't. |
| 24 | Exchange loop structure | Function-local `simulate_exchange` (fe:3171) called by `simulate_fight` outer loop | Method `_simulate_exchange` (fi:685) on `NarratedFightSimulator` class with commentary hooks | Structural divergence — noted at TWO-ENGINE CONSOLIDATION filing (CLAUDE.md:691-711). |
| 25 | Initiative computation | Inline in `simulate_exchange` (fe:3241-3327) | Delegated to `_determine_initiative()` method (fi:704) | Function-level divergence; formulas may differ (fi's method not extracted this pass — filed as unresolved). |
| 26 | Health hard-write on flash KO | flash KO sets `is_finish = True` only (fe:3446-3447), doesn't touch health | flash KO sets `caused_knockdown=True; is_finish=True; defender_state.health = 0` (fi:1122-1124) | fi zeroes health explicitly; fe doesn't. Affects downstream health-threshold reads (V7 TKO paths only fi has anyway; so this divergence is coupled to #10). |
| 27 | Round scoring dispatch | `score_round(stats1, stats2, kd_f1, kd_f2)` from fe:4283-4288 | Same primitive but with swapped KD args per #22 | See #22. |

---

## §12 AMBIGUOUS (extraction couldn't classify without judgment)

- **#22 `score_round` KD-arg convention**: fe and fi pass KDs in opposite order. Without reading `score_round`'s expected argument semantics in the docstring or code inspection, I can't say which is correct. `score_round(stats1, stats2, knockdowns1, knockdowns2)` at fe:3863 — the docstring says "Score a round using 10-point must system" and the body reads `knockdowns1` and `knockdowns2` symmetrically (fe:3893-3906) with `if knockdowns1 >= 2 and knockdowns2 == 0: return (10, 8)...`. So param name suggests `kd1` = KDs BY fighter1, and awarding (10, 8) TO fighter1 (score1, score2) when `kd1 ≥ 2`. Under that interpretation:
   - fe passes `f1_state.knockdowns_this_round` (KDs SUFFERED BY f1) as `knockdowns1` — WRONG semantically per docstring.
   - fi passes `f2_state.knockdowns_this_round` (KDs SUFFERED BY f2) as `knockdowns1` — CORRECT per docstring's "kd1 = KDs BY f1", since KDs SUFFERED BY f2 = KDs INFLICTED BY f1.
   Under this reading, fe is calling `score_round` with swapped semantics — awarding 10-8s to the fighter who WAS knocked down instead of who knocked down. **Filed for architect judgment** — could be a real bug in fe's decision path or a semantic misreading of the docstring; measurement (compare fe-decision-winners vs fi-decision-winners on identical stats) would settle it.

- **fi's `_determine_initiative()` method**: not extracted line-by-line this pass. Whether it matches fe's inline initiative logic (fe:3241-3327) is unverified.

- **fi's `_execute_grappling` + `_execute_submission_attempt`**: not extracted line-by-line. Structural mirrors of fe's grappling/submission branches, but any per-branch constant differences are unaudited.

- **`_tko_durability_mult` helper**: cited from GROUND-STOPPAGE-FIX1 filing formula, exact fi:line not grepped this pass.

- **STRIKE_PROPERTIES full table** (fe:220-261): 32 strikes × 4-tuple (base_damage, ko_power, stamina_cost, target). Extracted into Part C constant inventory; each row is a shared primitive.

---

## PART C — CONSTANT INVENTORY

Every tunable constant in the fight-resolution pipeline. Flat table. Governs = what it controls; Engine = fe / fi / both.

### C.1 Module-level named constants (`fe` only — fi imports)

| Name | Site | Value | Governs | Engine |
|---|---|---:|---|:---:|
| `DRAIN_SCALE_K` | fe:547 | 0.6 | Global stamina-drain scale (STAMINA-DRAIN1 B9) | both |
| `DRAIN_CARDIO_S` | fe:548 | 0.5 | Cardio-spread on drain (STAMINA-DRAIN1 B9) | both |
| `DMG_PIVOT` | fe:554 | 0.0 | Stamina pivot for damage curve (STAMINA-DMGCURVE1 identity wire, uncommitted) | both |
| `DMG_COMPRESS` | fe:555 | 1.0 | Damage-curve compression above pivot (identity) | both |
| `GNP_DOMINANT_DAMAGE_MULT` | fe:459 | 1.25 | Damage multiplier when attacker in dominant top position | both |
| `STRIKE_SKILL_DAMAGE_K` | fe:468 | 1.0 | Skill-into-damage dial (STRIKE-SKILL-DMG1 phase 1a) | both |
| `STRIKE_SKILL_DAMAGE_FLOOR` | fe:477 | 0.25 | Safety floor on skill-damage multiplier | both |
| `KICK_GAP_DAMAGE_K` | fe:494 | 1.0 | Kick-family gap-into-damage dial (phase 1b) | both |
| `KICK_GAP_DAMAGE_FLOOR` | fe:495 | 0.5 | Kick-gap damage floor | both |
| `KICK_GAP_DAMAGE_CEIL` | fe:496 | 1.5 | Kick-gap damage ceiling | both |
| `FLASH_KO_DAMAGE_THRESHOLD` | fe:418 | 70.0 | fi flash-KO minimum damage to trigger | fi |
| `FLASH_KO_BASE_CHANCE` | fe:419 | 0.03 | fi flash-KO per-damage-point base | fi |
| `FLASH_KO_MAX_CHANCE` | fe:420 | 0.12 | fi flash-KO cap | fi |
| `TKO_GNP_HEALTH_THRESHOLD` | fe:421 | 18.0 | fi V7 TKO_GNP health floor to trigger | fi |
| `TKO_GNP_BASE_CHANCE` | fe:422 | 0.15 | fi V7 TKO_GNP base chance | fi |
| `TKO_GNP_MAX_CHANCE` | fe:423 | 0.45 | fi V7 TKO_GNP cap | fi |
| `TKO_STANDING_HEALTH_THRESHOLD` | fe:424 | 15.0 | fi V7 TKO_STANDING health floor | fi |
| `TKO_STANDING_BASE_CHANCE` | fe:425 | 0.10 | fi V7 TKO_STANDING base chance | fi |
| `TKO_DURABILITY_FLOOR` | fe:445 | 0.35 | Floor on chin+heart+composure durability multiplier | fi |
| `TKO_DURABILITY_CHIN_DIVISOR` | fe:446 | 300.0 | Chin divisor in durability calc | fi |
| `TKO_DURABILITY_HEART_DIVISOR` | fe:447 | 350.0 | Heart divisor | fi |
| `TKO_DURABILITY_COMPOSURE_DIVISOR` | fe:448 | 450.0 | Composure divisor | fi |

### C.2 FightConfig fields

| Field | Site | Default (LIVE_PLAY) | Alt (FI_FALLBACK) | Alt (PRE_GEN_LEGACY) | Governs |
|---|---|---:|---:|---:|---|
| `scheduled_rounds` | fe:868 | 3 | 3 | 3 | Rounds per fight |
| `exchanges_per_round` | fe:870 | 55 | 55 | 55 | Inner loop iterations |
| `damage_multiplier` | fe:871 | 0.48 | 0.48 | 0.42 | Global damage scale |
| `standup_threshold` | fe:872 | 10 | 6 | 6 | Ground-inactivity ticks before ref stands them up |
| `submission_progress_to_finish` | fe:880 | 70.0 | — | — | Sub-progress needed to finish |
| `submission_escape_threshold` | fe:881 | 85.0 | — | — | Sub-escape progress needed to escape |
| `doctor_check_cut_threshold` | (per ENGINE-DEAD-KNOBS1) | 3 | — | — | Cuts needed to trigger between-round doctor check |
| `is_title_fight` | fe:884 | False | — | — | Metadata (5R gate not automatic; scheduled_rounds separate) |

### C.3 Heat modifier table (fe:4040-4055)

| heat > | damage_mult | composure_penalty | aggression_bonus |
|---:|---:|---:|---:|
| 80 | 1.20 | 12 | 0.20 |
| 60 | 1.15 | 8 | 0.15 |
| 40 | 1.10 | 5 | 0.10 |
| 20 | 1.05 | 3 | 0.05 |

### C.4 Starting stamina from fatigue (fe:4067-4079)

| fatigue ≤ | starting_stamina |
|---:|---:|
| 10 | 103.0 |
| 20 | 100.0 |
| 40 | 95.0 |
| 60 | 88.0 |
| 80 | 78.0 |
| >80 | 65.0 |

### C.5 Max health formulas

| Engine | Formula | Site |
|---|---|---|
| fe | `100.0 + fighter.chin * 0.3` | fe:4091 |
| fi | `100.0 + fighter.chin * 0.5` | fi:513 |

### C.6 STRIKE_PROPERTIES table (fe:219-261) — `(base_damage, ko_power, stamina_cost, target)`

| Strike | base_dmg | ko_power | stamina | target |
|---|---:|---:|---:|---|
| JAB | 3 | 0.01 | 2 | head |
| CROSS | 8 | 0.03 | 4 | head |
| HOOK | 10 | 0.05 | 5 | head |
| UPPERCUT | 9 | 0.04 | 5 | head |
| OVERHAND | 12 | 0.06 | 6 | head |
| BACKFIST | 6 | 0.02 | 4 | head |
| SUPERMAN_PUNCH | 11 | 0.05 | 8 | head |
| LEG_KICK | 7 | 0.00 | 4 | legs |
| BODY_KICK | 10 | 0.01 | 6 | body |
| HEAD_KICK | 15 | 0.12 | 8 | head |
| FRONT_KICK | 8 | 0.02 | 5 | body |
| SIDE_KICK | 9 | 0.02 | 6 | body |
| SPINNING_BACK_KICK | 14 | 0.08 | 10 | body |
| WHEEL_KICK | 16 | 0.15 | 12 | head |
| AXE_KICK | 12 | 0.06 | 8 | head |
| CALF_KICK | 6 | 0.00 | 3 | legs |
| OBLIQUE_KICK | 5 | 0.00 | 3 | legs |
| KNEE_BODY | 9 | 0.02 | 5 | body |
| KNEE_HEAD | 14 | 0.10 | 7 | head |
| FLYING_KNEE | 18 | 0.18 | 12 | head |
| ELBOW_HORIZONTAL | 8 | 0.03 | 4 | head |
| ELBOW_VERTICAL | 10 | 0.04 | 5 | head |
| ELBOW_SPINNING | 14 | 0.08 | 8 | head |
| ELBOW_UPWARD | 9 | 0.04 | 5 | head |
| GNP_PUNCH | 7 | 0.02 | 4 | head |
| GNP_HAMMER_FIST | 6 | 0.02 | 3 | head |
| GNP_ELBOW | 9 | 0.03 | 5 | head |
| CLINCH_KNEE | 10 | 0.04 | 5 | body |
| CLINCH_ELBOW | 8 | 0.03 | 4 | head |
| DIRTY_BOXING | 5 | 0.01 | 3 | head |

Note: `ko_power` field is defined in the tuple but reading in fight-resolution logic is limited (grep found no consumer this pass — filed as potential dead field).

### C.7 SUBMISSION_PROPERTIES table (fe:303-343) — `(danger_level, escape_difficulty, positions_available)`

| Submission | danger | escape_diff |
|---|---:|---:|
| REAR_NAKED_CHOKE | 95 | 70 |
| GUILLOTINE | 80 | 60 |
| ARM_TRIANGLE | 75 | 55 |
| DARCE_CHOKE | 70 | 50 |
| ANACONDA_CHOKE | 70 | 50 |
| NORTH_SOUTH_CHOKE | 65 | 45 |
| TRIANGLE_CHOKE | 85 | 65 |
| GOGOPLATA | 60 | 40 |
| BULLDOG_CHOKE | 55 | 40 |
| VON_FLUE_CHOKE | 50 | 35 |
| ARMBAR | 90 | 65 |
| KIMURA | 75 | 55 |
| AMERICANA | 60 | 45 |
| OMOPLATA | 55 | 40 |
| WRIST_LOCK | 40 | 30 |
| HEEL_HOOK | 95 | 75 |
| KNEEBAR | 70 | 55 |
| TOE_HOLD | 55 | 45 |
| CALF_SLICER | 50 | 40 |
| ANKLE_LOCK | 60 | 50 |
| NECK_CRANK | 45 | 35 |
| CAN_OPENER | 30 | 25 |
| TWISTER | 55 | 45 |

### C.8 Contest-function additive constants + bounds

| Function | Base additive | Slope | Bounds | Site |
|---|---:|---:|---|---|
| calculate_strike_success | 0.20 | 0.50 | [0.15, 0.85] | fe:2414-2416 |
| calculate_grappling_success | per-action `base_chance` | per-action `multiplier` | [0.12, 0.88] | fe:2728-2730 |
| attempt_submission (lock-in) | 0.30 + sub_bonus | 0.55 | cap = min(0.70, 0.50 + max(0, subs-75) × 0.013) | fe:3046-3052 |

### C.9 Upset branch thresholds + payouts

| Function | Trigger | Upset roll < | Effect |
|---|---|---|---|
| CSS | `offense < defense * 0.85` | 0.18 | `max(chance, 0.70)` (fe:2422-2423) |
| CSS | (same) | 0.35 | `min(chance + 0.22, 0.70)` (fe:2424-2425) |
| CGS | `offense < defense * 0.85` | 0.18 | `max(chance, 0.65)` (fe:2735-2736) |
| CGS | (same) | 0.35 | `min(chance + 0.25, 0.75)` (fe:2737-2738) |

### C.10 Variance constants (RNG draws)

| Site | Distribution | Applied to |
|---|---|---|
| fe:2411 | `random.uniform(0.75, 1.25)` | CSS offense variance |
| fe:2524 | `random.uniform(0.8, 1.2)` | Strike-damage variance |
| fe:2725 | `random.uniform(0.75, 1.25)` | CGS offense variance |
| fe:3132 | `random.uniform(0.75, 1.25)` | Sub tighten progress |
| fe:3138 | `random.uniform(0.75, 1.25)` | Sub escape progress |
| fe:3241-3242 | `random.randint(-15, 15)` × 2 | Initiative jitter |

### C.11 Chin erosion / rock / KD constants (fe:608-628)

| Constant | Value | Governs |
|---|---:|---|
| Damage threshold for erosion path | 12 | Min head damage to trigger KD/rock rolls |
| Erosion increment | 4 (per KD) | Added to `_chin_erosion` counter |
| Erosion max multiplier | 1.30 (at 12 pts erosion) | Cap on `_erosion_mult` |
| KD chance base | `damage × 0.015` | Multiplied by `_erosion_mult` |
| Rock chance base | `damage × 0.025` | Multiplied by `_erosion_mult` |
| Rocked stamina drain | 4 | `spend_stamina(4)` on getting rocked |
| Rock duration | `random.randint(1, 3) - reduction` | reduction = 1 if recovery ≥ 80, else 0 |

### C.12 Between-round stoppage constants

| Path | Trigger | Chance formula | Site |
|---|---|---|---|
| Cut (fe only) | `cuts >= config.doctor_check_cut_threshold` (3) | `min(0.35, (cuts-2)*0.08) * max(0.4, 1-heart/200)` | fe:4220-4226 |
| Doctor (both) | `health < 28 AND damage.head > 55` | `min(0.14, (55-health)*0.003) * max(0.5, 1-heart/250) × 1.35 if chin_compromised` | fe:4229-4239, fi:1772-1782 |
| Corner (both) | `round >= 2 AND health < 22 AND knockdowns_total >= 2` | `min(0.18, (KDs-1)*0.06) * max(0.3, 1-heart/300)` | fe:4242-4251, fi:1784-1794 |

### C.13 Referee stoppage from unanswered rocked shots

| Engine | Trigger | Chance formula | Site |
|---|---|---|---|
| fe | rocked defender + head strike | `min(0.35, _rocked_shots*0.08) * max(0.4, 1-iq/250-heart/350)` | fe:3503-3524 |
| fi | rocked defender + head strike | `min(0.22, _rocked_shots*0.05) * max(0.35, 1-iq/250-heart/350-composure/400)` | fi:1049-1066 |

### C.14 V7 accumulator TKO constants (fi only)

| Path | Trigger | Base chance formula | Cap | Durability |
|---|---|---|---:|---|
| Clinch body accum | `_clinch_body_acc >= 30`, target=body, in clinch | `min(0.22, (acc-25)*0.025) * max(0.4, 1-heart/320-composure/450)` | 0.22 | inline |
| GnP accum | `_gnp_accumulation >= 75`, target=head, in GnP position | `min(0.22, (acc-70)*0.025) * max(0.35, 1-heart/300-composure/450)` | 0.22 | inline |
| V7 TKO GNP | health<18, in DOMINANT pos, top_fighter=attacker | 0.15 + rocked +0.03 + KDs≥2 +0.04 + tc≥85 +0.02, cap 0.45, × `_tko_durability_mult` | 0.45 | `_tko_durability_mult(defender)` |
| V7 TKO STANDING | rocked, health<15, in STANDING | 0.10 + hp<20 +0.05 + KD≥1 +0.04, × `_tko_durability_mult` | | `_tko_durability_mult(defender)` |
| Leg TKO (both) | target=legs + `is_compromised_legs` | `min(0.15, (leg_kicks-6)*0.02) × 1.4 if stamina<50` | 0.15 | none |

### C.15 Failed grappling counter damage (fe:3752-3782)

| Trigger | clinch_skill | Damage range |
|---|---:|---|
| Failed TD/clinch-entry counter | ≥ 85 | `random.uniform(5, 10)` |
| Same | ≥ 75 | `random.uniform(3, 7)` |
| Same | ≥ 65 | `random.uniform(2, 5)` |
| Same, else boxing ≥ 80 | — | `random.uniform(3, 6)` |

### C.16 Score-round weights (fe:3874-3890, both engines)

| Stat | Weight |
|---|---:|
| damage_dealt | 1.5 |
| significant_strikes_landed | 1.0 |
| takedowns_landed | 8.0 |
| control_time | 1.5 |
| knockdowns | 20.0 |
| submission_attempts | 4.0 |

### C.17 Score-round ratio thresholds (fe:3924-3931)

| ratio | Round score |
|---|---|
| ≥ 0.75 AND score ≥ 30 | (10, 8) |
| ≤ 0.25 AND score ≥ 30 | (8, 10) |
| ≥ 0.52 | (10, 9) |
| ≤ 0.48 | (9, 10) |
| in (0.48, 0.52) | (10, 10) draw |

### C.18 Between-round FighterState refill (fe:657-664)

| Constant | Value |
|---|---:|
| `base_recovery` | 15 |
| Recovery bonus scale | `(recovery_rating / 100) * 25` (0-25 range) |
| Championship-round multiplier (R4+) | 1.3 |
| Refill ceiling | 100 (via `min(100, ...)`) |
| R1 guard | Skip if `_current_round == 1` (R1-REFILL1) |
| Health regain | `recovery_rating * 0.08` per round |

### C.19 Per-exchange stamina recovery (fe:3841-3842, fi:1651-1652)

`recover_stamina(0.5)` for BOTH fighters per exchange. Unscaled by K×g.

### C.20 Position-secured thresholds (fe:1596-1613)

| Position class | secured after |
|---|---|
| DOMINANT_CLUSTER | `dominant_control_duration >= 3` |
| GUARD/INFERIOR + subs ≥ 85 | `position_duration >= 2` |
| Elsewhere + subs ≥ 75 | `position_duration >= 4` |
| Elsewhere + subs < 75 | `position_duration >= 5` |

### C.21 Action-selection weights (fe:1666-1668)

| Category | Base weight | Min-floor |
|---|---:|---:|
| strike | 120 | 5 (if strikes available) |
| submission | 0 (starts zero, +conditions) | 1 (BJJ/sambo subs≥45, else subs≥60) |
| grappling | 13 | 5 (if grappling available) |

### C.22 Body-damage TKO (both)

| Constant | Value | Site |
|---|---:|---|
| Trigger threshold | `damage.body >= 65` | fe:602 |
| Chance formula | `min(0.40, (body - 65) * 0.04)` | fe:605 |

### C.23 Compromised-legs threshold (both)

`damage.leg_kicks_absorbed >= 6 OR damage.legs >= 50` → `is_compromised_legs = True` (fe:519). Referenced by leg-TKO paths (fe:3405, fi:1037).

---

## End of extraction

This document is v0.1 — as-built only, no proposals. Companion data at
`outputs/sm1/fight_model/p0_engine_comparison/` (Part B) provides the
engine-vs-engine comparison table. P1 Fight Model design decisions
(consolidation direction, calibration targets, DMGCURVE1 disposition,
deploy timing) live in a separate P1 doc, not here.

Coverage caveats — remaining after v0.1 closeout pass:
- `_tko_durability_mult` helper implementation not grepped (formula cited from GROUND-STOPPAGE-FIX1 filing).
- `score_round` KD-arg convention: fe vs fi divergence #22 flagged as AMBIGUOUS — needs source-of-truth ruling from architect.
- fi `_sprawl_counter` accumulator: written at fi:1411 on failed sprawl-defense; consumer line not grepped this pass.

Coverage caveats CLOSED in v0.1 closeout pass (see §13-§16 below):
- fi's `_determine_initiative` — EXTRACTED (§13.1), initiative divergence expanded (§16).
- fi's `_execute_grappling` — EXTRACTED (§13.2).
- fi's `_execute_submission_attempt` — EXTRACTED (§13.3).
- fi's `_process_submission_exchange` — EXTRACTED (§13.4, bonus during closeout).
- STRIKE_PROPERTIES `ko_power` field — CONFIRMED DEAD (§14).

---

## §13 [fi] Uncovered methods — closeout extraction

### 13.1 [fi] `_determine_initiative()` → `str` — fi:649

Returns fighter_id of the actor for this exchange.

**Base initiative** (fi:651-652):
```python
f1_init = self.fighter1.speed + random.randint(-10, 10)
f2_init = self.fighter2.speed + random.randint(-10, 10)
```
RNG: 2× `random.randint(-10, 10)` per exchange.

**Momentum bonus** (fi:655-658):
```python
if self.fight_state.momentum_fighter_id == self.fighter1.fighter_id:
    f1_init += 5
elif self.fight_state.momentum_fighter_id == self.fighter2.fighter_id:
    f2_init += 5
```

**Position advantage** (fi:661-664):
```python
if self.fight_state.top_fighter_id == self.fighter1.fighter_id:
    f1_init += 10
elif self.fight_state.top_fighter_id == self.fighter2.fighter_id:
    f2_init += 10
```

**Gameplan aggression** (fi:674-681) — GAMEPLAN-DIAL-AGGR1:
```python
if self._gameplan_f1 is not None:
    _a1 = int(getattr(self._gameplan_f1, 'aggression', 0) or 0)
    if _a1 != 0:
        f1_init += 2 * _a1
# same for f2
```
Per-aggression-step ±2; NOT IQ-gated per code comment.

**Tie-break**: `return fighter1_id if f1_init >= f2_init else fighter2_id` (fi:683). fighter1 wins pure ties.

**Divergence — initiative** (extends Divergence Table #25): fi and fe compute initiative from DIFFERENT inputs:
- **fi**: speed + `randint(-10, 10)` variance + momentum_id +5 + top_fighter_id +10 + gameplan aggression ±2/step. Tie → fighter1.
- **fe** (fe:3241-3327 inline): speed + `momentum // 2` (numeric, not id-based) + `randint(-15, 15)` variance + underdog aggression + takedown bonus + submission threat + position bonus + guard bonus + coin flip if `|Δ| ≤ 3`.

Structurally different: fi's momentum bonus is a fixed +5 IF a fighter is flagged as "momentum holder" (boolean-ish via id compare); fe's is a proportional bonus `momentum // 2` (numeric read of `.momentum` accumulator, range 0-100 → 0-50 point bonus). fe's variance range is wider (±15 vs ±10). fi has NO underdog / takedown-threat / submission-threat / position / guard / coin-flip modifiers. fe has NO gameplan-aggression modifier at this site.

**Consequence**: same fighter pair on same seed produces DIFFERENT initiative outcomes per exchange between the two engines. This propagates into who-acts-first and cascades RNG state. Flagged for Fight Model P1 as a structural consolidation choice.

### 13.2 [fi] `_execute_grappling(attacker, defender, attacker_state, defender_state, action, exchange_num)` → `Optional[Tuple[str, str]]` — fi:1303

Grappling branch (140 lines). Structural mirror of fe:3642-3782 with fi-side additions.

**Success roll** (fi:1314-1317): `success = calculate_grappling_success(attacker, defender, action, attacker_state, defender_state, self.fight_state)` — same primitive as fe.

**On success — position change** (fi:1322-1326): `new_position = apply_position_change(self.fight_state, action, attacker.fighter_id, True)` — same primitive as fe.

**Ground-action flag** (fi:1330-1331): `if new_position and new_position not in STANDING_POSITIONS: self._ground_action_this_exchange = True` — fi-only bookkeeping for referee-standup guard (Divergence #23).

**Takedown stats + drain** (fi:1334-1347):
```python
takedown_actions = {SINGLE_LEG, DOUBLE_LEG, BODY_LOCK_TAKEDOWN, HIP_TOSS,
                    TRIP, SLAM, SUPLEX}
if action in takedown_actions:
    round_stats[attacker.fighter_id].takedowns_attempted += 1
    round_stats[attacker.fighter_id].takedowns_landed += 1
    defender_state.spend_stamina(8)  # takedown impact drain
```
**fi-only defender drain**: `spend_stamina(8)` on takedown impact — fe has no equivalent (Divergence #7 was for KD tax; this is a separate fi-only drain on takedown-landed).

**SLAM damage** (fi:1350-1352) [fi-only]:
```python
if action == GrapplingAction.SLAM:
    slam_damage = 5 + attacker.strength * 0.1
    defender_state.apply_damage(slam_damage, "body")
```
Body damage from slam — a fi-only damage path.

**Sambo/Judo throw-to-position routing** (fi:1354-1386) [fi-only]:
```python
_throw_style = str(getattr(attacker.fighting_style, 'name', '') or ...).upper()
_is_sambo = 'SAMBO' in _throw_style
_is_judo = 'JUDO' in _throw_style
if _is_sambo or _is_judo:
    _td = getattr(attacker, 'takedowns', 70)
    _iq = getattr(attacker, 'fight_iq', 70)
    _pos_skill = (_td * 0.6 + _iq * 0.4) / 100
    if _is_judo:
        _back_mount_pct = min(0.88, 0.70 + (_pos_skill - 0.70) * 0.60)
        _side_ctrl_pct = min(0.10, 0.20 - (_pos_skill - 0.70) * 0.30)
    else:  # sambo
        _back_mount_pct = min(0.82, 0.60 + (_pos_skill - 0.65) * 0.55)
        _side_ctrl_pct = 0.30
    _r = random.random()
    if _r < _back_mount_pct: new_pos = Position.BACK_MOUNT
    elif _r < _back_mount_pct + _side_ctrl_pct: new_pos = Position.SIDE_CONTROL_TOP
    else: new_pos = Position.FULL_GUARD_TOP
    self.fight_state.position = new_pos
    self.fight_state.top_fighter_id = attacker.fighter_id
```
**Constants**: Judo back-mount cap 0.88 (0.70 base + 0.60 slope from pos_skill 0.70); Sambo back-mount cap 0.82 (0.60 + 0.55 × from 0.65). RNG: 1× `random.random()` conditional. This OVERWRITES the `apply_position_change` result for Sambo/Judo throws → they nearly always land in back mount at elite level. fi-only.

**Sambo immediate sub chain** (fi:1388-1399) [fi-only]:
```python
if _is_sambo and attacker.submissions >= 65:
    _chain_chance = (0.35 if _td >= 85 and _iq >= 75
                     else 0.25 if _td >= 80
                     else 0.22 if _td >= 75
                     else 0.12)
    if random.random() < _chain_chance:
        attacker_state._sambo_chain = True
```
Sets `_sambo_chain` flag consumed by `_simulate_exchange` at fi:729-745 (Divergence #15) to force-select a position-appropriate submission next exchange. RNG: 1× `random.random()` conditional.

**On failure** (fi:1400-1411):
```python
if action in {SINGLE_LEG, DOUBLE_LEG}:
    round_stats[attacker.fighter_id].takedowns_attempted += 1
    _s_style = str(getattr(defender.fighting_style, 'name', '') or ...).upper()
    if 'SPRAWL' in _s_style:
        defender_state._sprawl_counter = 2
```
**fi-only accumulator**: `_sprawl_counter = 2` (2-exchange counter window for sprawl-and-brawl fighters). Consumer line not grepped this pass — filed as sub-caveat.

**Note**: fi does NOT have fe's failed-grappling counter-damage path (fe:3749-3782). fi failure just increments stats and sets `_sprawl_counter`; fe failure does damage on strong-clinch or strong-boxing defenders. **Divergence** — added below as row #28.

**Log grappling** (fi:1413-1425): commentary.log_event — no engine effect.

**Post-branch stamina** (fi:1427-1430):
```python
attacker_state.spend_stamina(5)
if not success:
    attacker_state.spend_stamina(3)
```
Attacker drains 5 unconditional + 3 more on failure. Compare fe:3673 which does `spend_stamina(4)` in the grappling branch (asymmetry in drain constants — filed).

**Control time** (fi:1432-1434): `if success and new_position in DOMINANT_POSITIONS: round_stats[attacker.fighter_id].control_time += 1.0`. fe uses control_time per-exchange while attacker in top position (fe:3784-3792); fi adds +1.0 at position-change moment. Different accounting shape.

**Ground-action flag (position-based)** (fi:1440-1441):
```python
if self.fight_state.position not in STANDING_POSITIONS:
    self._ground_action_this_exchange = True
```
Bug-V comment: any grappling resolved on the ground counts as activity (success or fail) for the standup guard.

### 13.3 [fi] `_execute_submission_attempt(attacker, defender, attacker_state, defender_state, submission, exchange_num)` → `Optional[Tuple[str, str, str]]` — fi:1445

Returns 3-tuple `(winner_id, "Submission", sub_name)` on finish, else None. **Divergence**: fi returns 3-tuple, fe returns 2-tuple `(winner_id, method_str)`. Row #29 in Divergence Table.

**Attempt** (fi:1456-1459): `locked_in, finished, progress = attempt_submission(attacker, defender, submission, attacker_state, defender_state, self.fight_state)` — shared primitive.

**Stat + ground-action flag** (fi:1461-1465):
```python
round_stats[attacker.fighter_id].submission_attempts += 1
self._ground_action_this_exchange = True  # sub attempts always count as activity
```

**On lock-in** (fi:1467-1486):
```python
self.fight_state.submission_active = True
self.fight_state.submission_type = submission
self.fight_state.submission_attacker_id = attacker.fighter_id
self.fight_state.submission_progress = progress
# log commentary
if finished:
    self._log_finish(attacker.fighter_id, f"Submission ({submission.value})", exchange_num)
    return (attacker.fighter_id, "Submission", submission.value)
```
**Finish path #11 [fi]** — Submission at first-tick lock-in. Method string includes sub name in parens.

**Failure** (fi:1487-1496): commentary only.

**Stamina** (fi:1498): `attacker_state.spend_stamina(6)`. Compare fe:3141 which drains `spend_stamina(3)` for attacker in `process_submission_progress`. Different drain constant + different site.

### 13.4 [fi] `_process_submission_exchange(exchange_num)` → `Optional[Tuple[str, str, str]]` — fi:1502

Called each exchange while `submission_active`. Wraps shared `process_submission_progress` primitive with fi commentary.

**Progress** (fi:1508-1512): `escaped, finished = process_submission_progress(attacker, defender, attacker_state, defender_state, self.fight_state, self.config)` — shared primitive from fe:3086.

**On finish** (fi:1514-1517):
```python
if finished:
    sub_name = self.fight_state.submission_type.value
    self._log_finish(attacker_id, f"Submission ({sub_name})", exchange_num)
    return (attacker_id, "Submission", sub_name)
```
**Finish path #12 [fi]** — Submission at any subsequent tick (post-lock-in progress).

**On escape** (fi:1519-1585): tier the escape by `_progress_pct = submission_progress / config.submission_progress_to_finish` (default 70.0):
- `≥ 0.85` → `_stage = "escape_dramatic"` (near-tap escape — "Sandman moment")
- `≥ 0.55` → `_stage = "escape_tight"`
- else → `_stage = "escape"` (flat deflection)

Commentary hooks fire; fight_state fields reset (`submission_active=False`, `submission_type=None`, `submission_attacker_id=None`, `submission_progress=0.0`, `submission_escape_progress=0.0`).

**Divergence** (already row #24): fe has no equivalent commentary-driven submission-exchange wrapper — fe just calls `process_submission_progress` inline in `simulate_exchange` (fe:3218-3237) and returns the finish tuple directly without a tiered-escape narrative.

---

## §14 STRIKE_PROPERTIES `ko_power` — CONFIRMED DEAD

Grep across `fight_engine.py` + `fight_integration.py`:
```
fe:218   # Strike properties: (base_damage, ko_power, stamina_cost, target_area)   # comment
fe:2193  base_damage, ko_power, stamina, target = STRIKE_PROPERTIES[strike]        # select_strike
fe:2456  base_damage, ko_power, stamina_cost, target = STRIKE_PROPERTIES[strike]   # calculate_strike_damage
```
Three hits total. The two runtime hits (fe:2193, fe:2456) UNPACK the tuple with `ko_power` bound to a local variable, then **NEVER READ IT** downstream in either function body. `select_strike` (fe:2183-2220) uses only `target` (fe:2207, fe:2209). `calculate_strike_damage` (fe:2447-2526) uses only `base_damage` and `target` — the whole flash-KO / rocked / KD path lives in `apply_damage` and downstream in exchange logic, none of which reads STRIKE_PROPERTIES.

**Verdict**: `ko_power` field on the STRIKE_PROPERTIES tuple is a **dead field at runtime**. Values (JAB 0.01 → FLYING_KNEE 0.18 → WHEEL_KICK 0.15 → HEAD_KICK 0.12) encode design intent but flow nowhere. Removal would require dropping the second tuple slot everywhere (fe:220-261 table) + updating the two `_, ko_power, _, _` unpacks — mechanical, no behavior change.

Filed as a **CONFIRMED dead field**. Not a fe-vs-fi divergence — fe-internal dead-field. Not a P1 blocker; a P3 cleanup candidate.

---

## §15 DIVERGENCE TABLE — closeout additions (rows #28-#29)

| # | Divergence | fe site | fi site | shape |
|---:|---|---|---|---|
| 28 | Failed-grappling counter damage | Damage 2-10 by clinch_skill tier + optional boxing ≥80 fallback (fe:3749-3782), scaled by `config.damage_multiplier` | **absent** — fi failed grappling just sets `_sprawl_counter=2` for sprawl-and-brawl defenders (fi:1400-1411), no damage | fe punishes failed takedowns/clinches with strike damage; fi doesn't. |
| 29 | Submission-attempt return arity | Returns 2-tuple `(winner_id, method_str)` via `simulate_exchange` (fe:3597-3640) | Returns 3-tuple `(winner_id, "Submission", sub_name)` from `_execute_submission_attempt` (fi:1486) and `_process_submission_exchange` (fi:1517) | fi's caller must handle 3-tuple; fe caller handles 2-tuple. Structural interface asymmetry. |

Additional fi-only mechanics surfaced during §13 extraction (not new Divergence Table rows — captured as fi-side details):
- **SLAM body-damage** (fi:1350-1352): `slam_damage = 5 + attacker.strength * 0.1`, applied via `apply_damage(_, "body")`.
- **Sambo/Judo throw-routing** (fi:1354-1386): OVERWRITES `apply_position_change` result; elite skill → BACK_MOUNT with 82-88% probability.
- **Takedown impact drain** (fi:1347): `defender_state.spend_stamina(8)` on landed takedown — separate from KD tax (fi:996).
- **Grappling attacker drain** (fi:1428-1430): 5 unconditional + 3 more on failure = 8 max; fe drains 4 (asymmetric drain constants).

---

## §16 Divergence Table — expanded initiative comparison (extends row #25)

Row #25 flagged fi's `_determine_initiative` as separate from fe's inline. Closeout §13.1 extracted the full formula. Key facts pulled forward here:

| Aspect | fe (inline, fe:3241-3327) | fi (`_determine_initiative`, fi:649) |
|---|---|---|
| Base | `speed + momentum // 2 + randint(-15, 15)` | `speed + randint(-10, 10)` |
| Momentum | `momentum // 2` (numeric, 0-50 pt range) | `+5` if momentum_fighter_id matches (boolean) |
| Position | Position/guard/underdog bonuses | `+10` if top_fighter_id matches (single flat bonus) |
| Aggression | absent | `+2 * aggression_step` per gameplan aggression |
| Threat modifiers | underdog + takedown + submission | none |
| Variance range | ±15 | ±10 |
| Coin-flip tiebreak | if `|Δ| ≤ 3` | fighter1 wins pure ties |
| RNG per exchange | 2× randint(-15,15) + up to 1× random() | 2× randint(-10,10) |

**Consequence for consolidation** (Fight Model P1): whichever engine survives, the OTHER engine's initiative modifiers are lost unless deliberately merged. fi's gameplan-aggression tilt and fe's numeric momentum accumulation are both load-bearing for different mechanics that ship in the current game.
