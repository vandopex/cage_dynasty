# PLAYER-CREATE1 — SHIPPING FILING (2026-09-08, architect thread)

Status: SHIPPED LOCALLY at 4f50b78 → 1839545 → 64a879f (three
single-purpose commits on f0bf2f3). Supersedes POWER1 (Van ruling 1,
Gate 0 filing claude/gate0_baselines_2026-09-07.md). Forward-only:
new saves only; existing saves keep their player rows untouched.
Not on PA until deploy #3.

## 1. WHAT SHIPPED

(a) 4f50b78 — game_start.py, routes.py. generate_prospect_attributes
    returns 19 stats: power = strength + POWER_STYLE_OFFSET[style] +
    randint(-8, 8), clamped 20–95 (the world_init.py:1784 formula),
    and fighting_style = argmax over the shaped body via
    FighterGenerator._phase_b_derive_style, mirroring the Phase C
    call at world_init.py:1710 with key_map=_LEGACY_TO_CANONICAL.
    Van ruling (ii) "shape, then argmax": the :597 random style pick
    remains a shaping input (:519-522 bonuses); the derived label is
    the authority. Country threaded as optional third arg (§4
    tiebreak); game_bridge.py:2638's positional two-arg call
    unchanged. StartingProspect, to_fighter_dict and the routes.py
    wizard dict carry power, so the bridge sees 19 and the :2638
    fallback no longer fires (measured).
(b) 1839545 — game_bridge.py, one hunk after :2651.
    _create_player_fighter mirrors sign_amateur (:22087-88, :22270,
    :22273-74): fighting_style onto the FighterRecord (was '' for the
    whole career, so _compute_ovr fell through to Balanced weights),
    overall_rating = _compute_ovr(fighter) (was the wizard's roll
    target, which survived exactly one advance), then ovr_at_signing
    and week_signed into _fighter_data. week_signed is an addition to
    ruling 1(b), included because every AI and amateur row carries it
    via the same path.
(c) 64a879f — training.html, compare.html. _STAT_CATS gains the power
    tile (6th physical, _TRAINABLE order). compare.html's stat list
    was an 18-era list with power bolted on the tail and speed,
    recovery, top_control, heart, composure absent — no curation
    marker; rebuilt in canonical order with all 19 (Van ruling: fold
    in).

## 2. GATES (seed 20260907, save_invariants.py path — the instrument)

- R10 PASS: player power 62 = strength 53 + PSO['Striker'] 4 + 5.
  Fallback at game_bridge.py:2638 measured not firing
  (_stats_in_input 19).
- R12 PASS: ovr_at_signing 57, week_signed 0, record
  fighting_style 'Striker'.
- R13 PASS: training 19, compare 19, fighter_profile 19. Rendered via
  Flask test client on a fresh save: /training 19 distinct data-stat
  values, power tile ×1; /compare 19 stat rows + Overall, each ×1.
  Template compile sweep 38/38.
- probe2: stored OVR == _compute_ovr at creation (57 = 57; was 60 vs
  55 at Gate 0). _compute_ovr moved 55 → 56 after (a) (real power
  replaces the 50 fallback) → 57 after (b) (Striker weights replace
  Balanced).
- Full re-run, fresh --weeks 14 --dump: R10/R12 FAIL → PASS; every
  other rule's STATUS unchanged. Player at wk 14: stored 61 ==
  _compute_ovr 61, ovr_at_signing 57 preserved, style 'Striker'.
- Live copy proven: sys.modules['game_start'] resolves to
  cage_dynasty_web/game_start.py under the wsgi boot order.

## 3. BASELINE MOVED — READ THIS BEFORE ANY SEED-20260907 COMPARISON

Commit (a) consumes one randint per prospect BEFORE new_game runs
world_init, so every AI fighter generated afterward is rolled from a
shifted stream. outputs/sm_inv/dump_20260907.json is a pre-(a) world
(296 AI) that no commit at HEAD can regenerate. From 4f50b78 on, seed
20260907 means outputs/sm_inv/dump_20260908.json (292 AI; 146 names
in common with the old world). New baseline on that dump: R03 FAIL 1,
R06 FAIL 8, R09 freak_athlete 11, R11 country_distinct 20, R10 AI
power mean 58.70. The R03 5→1 and R06 5→8 movement is world noise,
established by the same-population check (FALSE), not by assertion.
The Gate 0 filing's table is history as of 4f50b78. Both dumps are
untracked under outputs/ (HARNESS-OUTPATH1 still open).

## 4. DOCUMENTED CONSEQUENCES (shipped, by design)

- Opening contract purse reads overall_rating: 5000 + 57×100 = 10700
  vs 11000 on the roll target (measured on the instrument path).
- On this seed 5 of 9 draft prospects derive Balanced (see
  PROSPECT-BONUS1). Truthful label, dull pool, until the retune.

## 5. FINDINGS FILED (new backlog items; none fixed here)

PROSPECT-BONUS1 (balance-touching, own stop). game_start.py:479-518
  style bonuses are below vary()'s ±8 noise and below GENERATOR1 §4's
  +8 signature gate; on seed 20260907, 5/9 prospects argmax to
  Balanced via F3 gap-detection, and Sambo landed Counter Striker
  once and Balanced once. The bonus table is also in the legacy
  12-style vocabulary while the argmax speaks the 10-label canonical
  one. Retune in canonical vocabulary against the +8 gate; measure
  Balanced count per seed before/after. Second-order: the §4 country
  tiebreak (+5% on the favored style) raised the Balanced count by
  one — nudging the runner-up closed the gap into an F3 tie. A
  tiebreak that manufactures ties is a world_init behavior; the fix
  for the bonuses is the fix for this too. Sequencing: Van's call —
  recommended after deploy #3.

OVR-FORMULA1 (measured, not changed). AI pool stored overall_rating
  is world_init's unweighted mean over 19 stats (world_init.py:1323
  skill_rating; :3039 retrain; :3704 persist) and is NEVER recomputed
  by the bridge — the AI weekly training path skips it by design
  (game_bridge.py:11855-11857 comment). Player OVR is style-weighted
  _compute_ovr on every training tick (:8230, :8985, :10328, :5054);
  graduated amateurs get _compute_ovr once at :22270. Dump 20260907,
  n=296 AI: stored − computed mean −1.6, median −2, range −8..+2,
  histogram −4:16 −3:50 −2:85 −1:83 0:45 +1:12. Two formulas on the
  same ladder from tick 1 of every save; the player floats, the AI
  pool is frozen at world-gen. Reconciliation (AI through
  _compute_ovr, or everyone on one formula) moves every AI badge and
  whatever sorts on it — separate ruling, own measurement.

SETUP-OVR1 (display). The prospect card advertises the roll target
  (p.overall_rating, max(52, ceiling − growth_room) at
  game_start.py:578) while the profile shows the computed OVR: 60 vs
  57 on this seed. The player picks a "60" and gets a "57". Fix is to
  show the computed number on the card; needs a record or a
  dict-capable _compute_ovr.

HARNESS-RNG1 (harness discipline). save_invariants.py --seed is
  process-stable: six invocations (three default, three
  PYTHONHASHSEED=0) byte-identical on R10 and the AI histogram. Every
  divergent number this arc (64, 58, 10800) came from one-off
  scripts whose new_game args differed from the instrument's
  (visible in the logs as a different coach name); mechanism not
  isolated. Rule: only the instrument's numbers are quoted; a
  reimplementation is a different world. uuid4 still bypasses the
  seed (fids vary per run; values don't).

STALE systems/game_start.py. 1303 lines vs the live 1384; divergent
  POTENTIAL_GRADES and coach traits. Not imported by the web app
  (cage_dynasty_web/systems/game_start.py is a shim to the web copy).
  Same family as the four dead fight_engine copies; census + delete
  candidate.

COMMENTARY G&P STRING (UI-strings batch). Argmax emits
  "Ground & Pound" (world_init.py:1452); narrative/commentary.py:1326
  aliases "Ground and Pound", so G&P fighters fall through to
  Balanced commentary at :3088. Pre-existing since GENERATOR1.

## 6. PROCESS NOTES (for the working-style doc)

- Two rulings were made on a number, not a read: (ii) shape-then-
  argmax after the wizard read showed no player style choice; keep
  1(b) after M1 showed the AI pool on a different formula and the
  player already on _compute_ovr from week 1.
- key_map=None "looked callable" and returned Balanced for a
  wrestler-only body; caught by a divergent-body probe, not by
  reading _r().
- cc inserted a stop and waived it in the same message. A stop is a
  stop.
- "(inferred)" in a gate line is a read standing in for a
  measurement; it went into a commit body before it was measured.
  It was right. That is not the point.
