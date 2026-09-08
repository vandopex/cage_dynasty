# GATE 0 BASELINES — 2026-09-07 (HEAD cf2fecf, local, seed 20260907)

Status: FILING. Architect's record of the SAVE-INVARIANTS1 + DEVELOPMENT1
Gate 0 baseline runs executed by cc in the post-addendum thread. Every number
below is MEASURED unless tagged READ. Rulings at the end are Van's,
2026-09-07/08. This file is history; CLAUDE.md carries an index line only.

Instruments (claude/tools/, committed with this filing):
  _harness_env.py        sys.path/CWD setup so bare imports resolve to the WEB copies
  save_invariants.py     v4. 13-rule checker; --save PATH (bridge save or harness dump) | --seed N --weeks W [--dump PATH]
  dev1_gate0.py          probe1 intensity sweep / probe2 OVR attribution / probe3 camp-vs-autorest
  phase2_holes.py        H-1 week axis, H-2 probe3B, H-4 style, H-6 vacuity, H-7 gen-time height/reach
Outputs under outputs/sm_inv/, outputs/dev1_gate0/, outputs/h_phase2/ (untracked harness dumping ground; HARNESS-OUTPATH1 pending).
World dump: outputs/sm_inv/dump_20260907.json (876 KB). --save DUMP replays the rule table in 0.04 s,
byte-identical to the 4:27 fresh sim. Rule iterations run against the dump; sims only for new worlds.

## GATE — instrument discriminates the player creation path
Player path verified READ: routes.py:472 → generate_starting_prospects → generate_prospect_attributes
(game_start.py:442, returns 18 stats, no power) → bridge.new_game → _create_player_fighter
(game_bridge.py:2571) → _STAT_KEYS 19 at :2628-2633 → `.get(k, 50)` at :2650.
MEASURED --weeks 0: R10 FAIL, player power = 50. AI N=296 mean 57.5, 2.4% at 50 (noise, not a spike).

## FINDINGS OF RECORD

F1. TWO-AXIS WEEK FIELD (root of playtest #20 AND #21).
  Pre-gen HistorySimulator writes fight_history[].week on its own 0..60 clock with event_number 1..60
  (Founding rows: week 0, event_number 0 per world_init.py:1984-1995). bridge.new_game resets
  week_number to 0 (game_bridge.py:2322-2325); live events write week 1.. and are named "Cage Dynasty
  61+". Live fight_history writes NEVER stamp event_number — all three paths omit it: game_bridge.py
  :5716-5717 (_simulate_card_fights), :14248-14262 (_simulate_ai_fights_week), :18451-18463
  (_run_real_engine). 202 of 1809 history rows in the dump have event_number None = every live fight.
  The only axis marker on a live row is the N in event_name. (An earlier cc claim that some live rows
  carried 61+ was a misread of event_name; corrected.)
  BeltReign carries NO provenance field (world_init.py:508-559); a reign's axis is only recoverable
  by parsing won_event/lost_event.
  fighter_profile.html:1207-1213 compares reign weeks to fight.week with no axis awareness. Measured
  in the seeded world (R03 v4): template marks 64 defenses, axis-unified predicate marks 67, 5 false
  positives in two directions — a live-era reign (won CD69, live wk 13) retro-stamps 🛡️ on four
  pre-gen wins at raw weeks 23/30/53/58; a pre-gen reign (CD7–CD28) stamps 🛡️ on a live wk-10 win.
  R06 v4 (axis-unified, founding excluded): pre-gen 0, live 0, SEAM 5 — fighters booked at CD59 or
  CD60 (pre-gen wk 59/60) and again at CD61/CD62 (live wk 1/2), true gap 2 weeks against a 4-week
  floor. Playtest #21's seam hypothesis is CONFIRMED (an earlier "refuted" reading was the v2/v3
  instrument mis-filing live rows as pre-gen). Mechanism — whether the live matchmaker's cooldown
  reads pre-gen last-fight weeks at all — is unmeasured; MATCHMAKING1 Gate 0 / WEEK-AXIS1.

F2. THE −4 OVR (playtest #3) SPLITS 3 + 1, NEITHER IS DECAY.
  probe2 (MODERATE, wk0→1): all 19 stats non-negative (8 rose), stats_with_data 19 (legacy guard
  at :7876-7879 does not fire). Stored overall_rating 60 → 56. _compute_ovr on the BEFORE sheet = 55.
  Creation stamps the wizard's p.overall_rating (game_bridge.py:2589); the first advance of ANY
  intensity (REST included) overwrites it with _compute_ovr (:8985). 3 points = wizard-vs-formula
  disagreement at creation. 1 point = style weighting: FighterRecord.fighting_style is never set
  for the player (constructor :2581-2596 omits it; dataclass default '' at game_state.py:113) while
  _fdata['style'] IS set (:2614) — two style fields, one empty; _compute_ovr reads the empty one.
  The browser path has the same empty record style; the harness mirrored it correctly.
  With style set, _compute_ovr = 57 before and after; stored drop becomes −3.

F3. CAMP BEATS SAFETY (playtest #37, measured).
  probe3B: fatigue set to 84 at boot, fight booked 9w out, camp locked MODERATE. wk1 (out of camp)
  auto-rest fires "fatigue critical (84%)" → 72. wk2 enters camp (≤7w, :8689-8690) → auto-rest
  silent for every remaining week while fatigue climbs 78 → 84 → 90 → 92 → 94 (wk2–6). 🏕️ taper at
  4w/3w ("tapering to LIGHT") is an intensity cap, not a safety trip; LIGHT still adds +2/wk. The
  taper's own REST at 2w/1w (:8721-8738) pulls 94 → 82 → 70; the fighter enters fight week at
  fatigue 70 against a 30 target. :8744-8746 clears the hysteresis flag each camp week.
  probe3 (fatigue 0 start) never reached the threshold and is NOT evidence either way.

F4. INTENSITY DIAL — cost side exact, gain side monotonic, EXTREME self-limits.
  Fatigue/wk observed: REST 0 (floor), LIGHT +2, MODERATE +6, INTENSE +12, EXTREME +21 — the
  :8004-8006 table × recovery modifier. Auto-rest at 84 (≥80 rule), hysteresis to 40, reasons verbatim
  "Auto-rest: fatigue critical (84%)" / "Auto-recovering (72% → target 40%)".
  Gain, sum of 19 stat deltas over 8 weeks: REST 7.53 (5 stats; coach passive MC1b loop :8817+ fires
  regardless of plan), LIGHT 21.11, MODERATE 33.61, INTENSE 41.39, EXTREME 33.68 (4 of 8 weeks lost
  to auto-rest). Per working week: 0.94 / 2.64 / 4.20 / 5.78 / 7.51. At an 8-week horizon EXTREME
  yields less than INTENSE.

F5. FOUNDING ROW IS A PHANTOM WIN (playtest #9/#22) — CONFIRMED BY EXCLUSION.
  9 inaugural champions, 9 founding rows (R04 not vacuous). With founding rows excluded from the
  history walk: R01 9 → 0, R02 7 → 0. The `wins` field does not count the founding row;
  fight_history does, and so does any streak computed from history.

F6. PLAYER CREATION PATH — four gaps in one neighborhood.
  power = 50 fallback (GATE); fighting_style not set on the record (F2); ovr_at_signing missing —
  R12 sole violator is the player fighter (playtest #5); creation OVR is the wizard number, not the
  formula (F2). AI signings capture at_signing correctly.

F7. HEIGHT/REACH ARE VARIED AT GENERATION, DROPPED AT PERSIST, DEFAULTED ON READ (playtest #7/#25).
  Runtime wrap of world_init.FighterGenerator.generate_fighter over 296 fighters: height 47 distinct
  (modal 173 cm, 4.4%), reach 53 distinct (modal 194, 4.7%), country 19 distinct (US 20.6%).
  world_init.py:3854-3865 persists age/country/potential/body_frame/natural_weight_class/personality —
  not height or reach. game_bridge.py:7473-7474: `height=str(fdata.get("height", "5'10\""))`,
  `reach=str(fdata.get("reach", "72\""))` — the profile renders the fallback for every fighter.
  fighter_profile.html:290-291 guards on truthiness, which the default always satisfies.
  Fix is persist + render-absent-as-absent, forward-only; not the generator.

F8. TWO CONDITION→LABEL FUNCTIONS (playtest #37).
  game_bridge.py:7397-7406: ≤20/≤40/≤60/≤80/>80 → Fresh/Rested/Ready/Tired/Exhausted.
  game_bridge.py:9298-9310: <20/[20,40]/(40,65]/>65 → Fresh/Ready/Tired/Fatigued.

F9. OTHER MEASURED
  R13: training.html 18 stats (no power), compare.html 14 (missing speed, recovery, heart, composure,
  top_control), fighter_profile.html 19. R07: no KO/TKO suspension mechanism exists (cooldowns only,
  matchmaking.py:103-107). Matchmaker does not book the player fighter without an offer (probe logs
  grep clean). Player and AI training use different gain tables (ints 0–4 at :7623 vs floats
  0.15–0.85 at :11723) — out of scope, logged for THE RATE.

## BASELINE TABLE AT HEAD (v4, dump replay outputs/sm_inv/run_v4_from_dump.txt)
  R01 PASS · R02 PASS · R03 FAIL 5 (template 64 / unified 67 / FP 5 / unclassifiable 0) · R04 PASS ·
  R05 PASS · R06 FAIL 5 (pre-gen 0 / seam 5 / live 0 / unclassifiable 0) · R07 SKIP · R08 SKIP ·
  R09 INFO · R10 FAIL (player 50) · R11 SKIP-in-save (gen-time varied) · R12 FAIL (player only) ·
  R13 FAIL (training 18, compare 14).
  Real failures at HEAD: R03, R06 (WEEK-AXIS1 population) and R10, R12, R13 (PLAYER-CREATE1 population).
  Instrument history: v1 R06=118 (cross-axis subtraction) → v2 3 (founding pairs) → v3 0 (live rows
  mis-filed as pre-gen) → v4 5 (real). Each step was an instrument change proven to move the number
  for a stated reason.

## INSTRUMENT NOTES
  R08 SKIP (two age-stage labelers not yet located). R09 INFO only. _reign_unified_weeks depends on
  parsing won_event; a reign with an unparseable event name defaults to the pre-gen axis silently —
  add an unclassifiable count if reigns ever carry custom names.
  Wall-clock: --seed --weeks 14 ≈ 4:27; probe1 W=8 ≈ 4:34; probe2 ≈ 0:30; probe3/3B ≈ 2:25; dump replay 0.04 s.

## RULINGS (Van, 2026-09-07/08 — "go on all 4")
  1. PLAYER-CREATE1 (supersedes POWER1 as scoped): (a) generate_prospect_attributes returns 19 stats
     incl. power, style derived per GENERATOR1 §4; (b) _create_player_fighter sets fighting_style on
     the record, captures at_signing via the AI path, sets creation OVR = _compute_ovr(sheet);
     (c) training.html power tile. Three single-purpose commits, each gated by dump-replay + probe2,
     stop before each commit. Forward-only.
  2. Instruments (claude/tools/*) + this filing are committed as standing gates BEFORE the engine work.
  3. Founding-row rule: a founding row on every inaugural champion's history, never counted in
     streak or record.
  4. WEEK-AXIS1, sequenced after PLAYER-CREATE1: stamp event_number on the three live write paths;
     add a provenance or absolute-week field to fight rows and reigns; fix the template predicate;
     measure what the matchmaker's cooldown reads at the seam before touching it. Forward-only.
     R03/R06 are its instrument.
