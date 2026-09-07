# PLAYTEST NOTES — 2026-09-07 (PA, b6e1d74, fresh new_game, week 0→1)

Status: architect observations from Van's first browser session on the
interim-deployed SHA. NOT a docket, NOT rulings. Everything here is a READ of
rendered pages; each item names the measurement that would confirm it. Items
tagged [DEPLOY] gate the interim-deploy acceptance; everything else is
post-deploy backlog. Van rules on slotting.

## [DEPLOY] 1. Internal server error on Accept & Negotiate (Fight Offers)
Player fighter (0-0, LW, debut) accepted an AI offer vs a #15 (3-2) → 500.
Measurement: PA error-log traceback; then `git log -L` / `git log -S` on the
offer-accept route between 1d8b4e1 and b6e1d74 to classify REGRESSION (route
or its callees changed in the 33-commit chain) vs PRE-EXISTING. Read-only.
Fix is its own docket after classification; not this thread.
MEASURED 2026-09-07: REGRESSION, C23 a8c4847 — Jinja `{# #}` inside a `{% for %}`
list literal. Template compile sweep (38 files) found exactly two: fight_camp.html:138
and compare.html:51. Accept POST succeeded (302); the 500 is the redirect target.
TPLFIX docket drafted; compile sweep becomes a standing deploy gate.

## [DEPLOY-adjacent] 2. Performance: world creation and first Advance Week both long
Measurement, not guess: wall-clock per request from PA server/access log
timestamps for /new_game and the first /advance-week; local equivalents for
comparison. Pre-gen fight count and per-fight cost (local harness: 1.86 s/fight)
give the expected floor. If PA is CPU-throttled (see CPU gate), that is a
separate cause from engine cost.
MEASURED 2026-09-07 (PA access log, N=1 each side, different worlds — hypothesis-grade):
GET /start-game 11.5s at 1d8b4e1 → 31.1s at b6e1d74; POST /advance-week 16.1s → 32.3s.
PA console CPU quota is 100 s/day (web requests unmetered). PERF1 docket: local timing at
both SHAs on one seed to make it a measurement.

## 3. OVR dropped 67 → 63 in one week while every reported stat delta was positive
Training Report: "Sparring · MODERATE, -4 OVR" with Boxing +0.8, TD Def +1.0,
Fight IQ +1.0, Speed +0.4, five coach +0.3s. Offers page shows 63; profile
showed 67 at week 0. Either (a) unlisted stats decayed (the 15 "maintained"
stats atrophied?), (b) OVR display is condition/other-adjusted, or (c) the
formula changed. Measurement: dump the fighter's 18 stats at week 0 and week 1
from the save and recompute OVR both ways. This is the DEVELOPMENT1 "THE RATE"
question showing up in play; strongest engine finding of the session.

## 4. Training page projected OVR reads "67 OVR → 0.0"
Projection renders 0.0. Display or calc bug. Measurement: the template
variable feeding "→ X" and its value for a fresh fighter.

## 5. Career Arc "At Signing" blank for the player's own fresh fighter
Page says "At Signing populates for fighters signed after the data-capture
ship — pre-existing fighters stay blank." A fighter created via setup_fighter
on b6e1d74 is not pre-existing. "Looks wired" candidate: the capture fires on
the AI signing path but not the player setup path. AI champions show At Signing
== Current and Growth "—" (should read 0). Measurement: grep the at_signing
write sites; check the save for the player fighter's field.

## 6. Pre-gen champion stat profiles are god-stat shaped
Diego Prochazka (FLW champ, 88): eleven stats at 95, Chin 64 / Heart 63 /
Recovery 63. Matheus Almeida (LHW champ, 81): six stats at 95. Both "Heavy
Hands + Freak Athlete + Complete Fighter." Van's stated taste: no god stats.
GENERATOR1 shipped (C35–C40) — so this is either the champion path bypassing
it, or the 95 cap being hit by the pre-gen growth loop. Measurement: histogram
of per-stat values across all pre-gen fighters with OVR ≥ 80; count of 95s per
fighter.

## 7. Three of three fighters shown: Brazil, 5'10", 72" reach
Jake Barbosa (player), Prochazka (FLW), Almeida (LHW) — identical height/reach
across FLW and LHW is implausible. Smells like a default not being varied.
Measurement: distribution of nationality, height, reach across the world;
count at exactly (5'10", 72). Also the `72""` double-quote render bug.

## 8. Scout Report "Weaknesses" are relative bottom-3, not absolute
Prochazka's weaknesses list "Fight Iq (86)". An 86 is not a weakness.
Threshold should be absolute (e.g. < 65) with "no notable weaknesses" as the
empty state. Also stat-key formatting leaks: "Fight Iq", "Bjj",
"Kickboxing_coach", "calf_slicer", "General Mma" — title-cased snake_case in
UI. One helper, many call sites.

## 9. Win streak exceeds win count
Record Book: Almeida 8-0-0 with "9 W streak"; Prochazka 7-0-0 with "8 W
streak." The founding-title "WIN 🏆 — TITLE" row is counted in the streak but
not in the record. Pick one. Measurement: streak calc vs record calc on the
same history list.

## 10. Record Book: Sig. Strikes / Sub Attempts / Takedowns "No records yet"
Pre-gen fights carry no stat keys (same shape as the FOTN scorer bug: fight
dicts without stats). Check whether week-1 live fights populated these after
Advance Week; if still empty, the record book reads a key the bridge never
writes.

## 11. Week-1 card finish mix: SUB 4 / DEC 3 / TKO 2 / KO 0 (N=9)
Consistent with the local BEFORE baseline (KO 0.0 at N=145). Third zero-KO
sample. Main and co-main both R1 submissions, main event a title change.
Not a gate; feeds Group D. PA-SMOKE1 shares are the number of record.

## 12. Injury headline: "Shoulder strain via calf_slicer"
Body-part mismatch between injury and causing technique; raw technique key in
headline. Story-facing; cheap. Injury type should be drawn from the
technique's target region.

## 13. Coach's Corner is generic
"Good condition. Now think your way through every session." Not specific, not
actionable — fails the north star by definition. Coach has a Kickboxing
specialty and a fighter with 56 Kicks / 55 Clinch Striking / a Body Attack
recommendation; the line should be built from that.

## 14. Training focus label mismatch
Coach's Corner says "General Mma · Moderate"; Training Report says "Sparring ·
MODERATE" for the same fighter/week. Two labels for one setting, or two
settings.

## 15. Fight Offers screen — Van's question: more info?
Yes. The offer is the decision moment and currently shows: names, records,
OVR, purse, bonus, weeks-out, "Fair," Risk ★★★★★, Reward ★★★★★ (both maxed —
uninformative), "Acceptance: 75%" (undefined). Candidates, all from data the
game already has: opponent archetype + traits; a 4–6 stat side-by-side
(Compare page exists — link it); opponent's last three results with finish
method; opponent camp/facility tier; MC odds if the feature is live for this
matchup; contract context — which of the 3 contracted fights this is, rounds,
weight class, injury/condition of both; what "Fair" and "Acceptance %" mean
in one line each; Risk/Reward as a real spread, not 5/5. Scope for a small
docket after the 500 is fixed, since it's the same screen.

## 16. Economy numbers
$48,175 balance, $125/week overhead, 385 weeks runway. Overhead is trivially
low and runway is meaningless at this scale. Backlog; not measured here.

## 17. Nickname "Grit" for a 6-0 HW champ with 4 subs
Matches the 2026-09-07 architect note: random.choice unrelated to record
shape. Polish, behind deploy.

## 18. Ladder ordering by record puts a 51-OVR at LW #6 above an 80 at #5
Rankings track record, not rating — defensible, but paired with god-stat
champions and low-OVR contenders it reads as noise. Observation only.

## 19. Power (D7, 19th stat) is not on the Training page; player fighter's power looks like a default
Training grid shows Physical = Strength/Speed/Cardio/Chin/Recovery — no Power.
training.html's own comment says "All 18 floors + 18 targets"; power is the
19th. D7 ratification (fight_model_v1_0.md) lists "world-gen, training, and UI
grow a stat" as accepted cost; C23 title says "training/UI"; training_page_notes
says "power joins the trainable roster at P3-4d." Filing claims more than
shipped. Separately: player fighter power 50 with strength 70 — neither
world-gen roll+offset nor the load-time derivation (strength+offset+[-3..+3])
produces that; 50 is fallback-shaped. Hypothesis (unmeasured): setup_fighter
never assigns power → player fighters start with a dead default in the KO
lever (flag ON) and cannot train it. Measurement: grep trainable set +
template loop for 'power'; trace power on setup_fighter vs world_init; from
the PA save, player power/strength and AI power histogram (is 50 a spike?).
Same shape as #5 (player-path capture gap).
MEASURED 2026-09-07: CONFIRMED. training.html _STAT_CATS = 18 (no power); game_bridge
_TRAINABLE = 19 (has power); power decays with the physical group. game_start.py
generate_prospect_attributes returns 18 stats (docstring says 17), no power → player
power = 50 by `.get('power', 50)` fallback, guaranteed (probe: player 50, AI N=292
continuous mean 58.9, 3.8% at 50). POWER1 docket: fix at the function (check other
callers, e.g. amateur→pro signings), add the training tile, forward-only.

## Ordering recommendation (architect, not ruled)
1 (traceback + classification) → CPU gate → PA-SMOKE1 5a → deploy accept →
docs/filing commit (punch list: 6,217→6226; WSGI 610→479 at L1162-1171;
webhook pull-dir at L468-476; token breach + rotation; systems/ shadow;
harness hardcoded output path; deploy mechanism recorded verbatim) → then
dockets: #1 fix, #3 measurement (folds into DEVELOPMENT1 Gate 0), #5, #9,
#15 offer-screen, #19 power-trainable + player-path power, #8/#12/#13/#14 as a UI-strings batch.
