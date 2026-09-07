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

## 20. 🛡️ defense marker on a non-title win
Andrade (BW #2, not champion) shows 🛡️ on his CD61 prelim win vs Lauzon (#7 v #6).
Flag is not "winner held the belt at fight time." Measurement: the CD61 fight dict
(fight_1_7adb4da7_c57803de) title/defense fields + the template condition. Note the
same card carried two real title fights (LW, HW) — check for event-level leakage.

## 21. KO'd at CD60 (last pre-gen card), fought at CD61 (week 1) — no suspension, no rest window
Andrade KO'd by Hall at CD60, subbed Lauzon at CD61 one week later; Lauzon also fought
both cards. Causes: (a) C22 rider — pre-gen history persists no injuries, so pre-gen
KOs carry no suspension into live play; (b) matchmaker rest window at the pre-gen→live
seam appears to be zero. Measurement: weeks-since-last-fight for all 18 CD61 fighters;
grep live-play post-KO suspension; grep matchmaker min-gap.

## 22. Inaugural-champion display inconsistency
Andrade was the founding BW champ (awarded, not fought) and lost the belt at CD5 —
data consistent (Svensson's reign says "Won from Jose Andrade · CD5"). But the
"WIN 🏆 Founding Champ" history row renders only for fighters who still hold the
crown (Prochazka, Almeida) and inflates their streak (#9); Andrade has no such row.
"Won from Inaugural" is bad copy. Rule: founding row on every inaugural champ's
history or none, and never counted in streak/record.

## 23. "✂️ Cutting from Flyweight" on bantamweights
Svensson and Jedrzejczyk (BW top 10) show it. A natural flyweight competing at BW is
moving UP — copy inverted, or natural class assigned independent of division.
Measurement: natural_class vs division across the world; count of mismatches by direction.

## 24. Age-stage label vs career-arc text disagree
Andrade "35 yrs Prime" header + "Late career fighter" arc text; Svensson 32 / Jedrzejczyk 33
"Prime" + "Veteran"; all three "📈 Maturing" with 3-point ceilings. Two age-stage
functions, or one with two thresholds. PEAK103-adjacent.

## 25. Height/reach constant
Six of six fighters seen (three divisions) are 5'10" / 72". Strengthens #7 from
"smells like" to near-certain. Same measurement.
UPDATE: seven of seven incl. a strawweight (Costa, player path). It is a default.

## 26. Badges — verified against GENERATOR1 spec
Six computed badges (spec §5 kind 2, thresholds ratified at 85): Iron Chin, Heavy Hands,
Gas Tank, Warrior Heart, Freak Athlete, Complete Fighter. Never stored; pure functions of
the current sheet at render time; losable. All four profiles seen today match the
predicates. Not a bug; recorded because Van asked.

## 27. Title lineage gap (observation)
BW: Andrade (inaugural) → Svensson CD5 → Volkov CD24 → ? → Hall (7-0, C). Volkov not in
the top 9. Probably fine; Champions page should show the chain end-to-end.

## 28. Personality label "WARRIOR" on 22 of 24 listed free agents (week 2)
Exceptions: bidding-war fighter CALCULATED, ranked FA CONTENDER. Fallback-shaped.
Measurement: personality distribution across the world split by creation path
(world-gen vs churn/cut vs amateur graduation); WARRIOR share per path.

## 29. Weight-class abbreviation schemes collide
Free-agent filter: STR/FLY/BAN/FEA/LGT/WEL/MID/LHW/HVY. Camp roster table:
STW/FLW/BW/FW/LW/WW/MW/LHW/HW. Weekend recap: 3-letter truncation — week-1 recap
tagged a Light Heavyweight fight `[Lig]` (Araujo v McCarthy), identical to the
Lightweight tag. Three schemes, one collision. One helper + one table. UI-strings batch.

## 30. Unexplained $1,825 weekly balance drop vs stated $125 overhead
$48,175 → $46,350 over week 1→2. Finance panel shows only overhead. Measurement:
the bridge's weekly ledger for the player camp; if no itemized ledger exists, that
is the finding. Folds into the economy docket (#16).

## 31. Free-agent market composition
26 available: 22 of 24 listed are 0-5 to 1-7 with OVR 31–55, several age 22 at 0-6.
Implies (a) the matchmaker books winless fighters 6–7 times, (b) nothing feeds
prospects or veteran bargains into the market. "Sort: Potential" exists but cards do
not show ceiling. Design docket (MARKET1) after the measurement in (a): fights-per-
fighter vs record for all pre-gen fighters. Economy scale mismatch: $36k top bid vs
$46k balance vs $12.6k debut purse vs $125/week overhead.

## 32. Real fighter names in the pool (Van's call)
Darren Till, Joanna Jedrzejczyk, Buakaw Banchamek, Saenchai Petchyindee, Weili Yan,
Bonjasky, Spong, Gane, plus recombinations. Fine private; decide before anything public.

## 33. MATCHMAKING1 — matchmaking rules + card slotting + slot shown on the offer (Van, 2026-09-07)
Backlog already carries "wire calculate_matchup_score / assign_slot for intentional
Main/Co-Main" — unverified whether wired. Week-1 card LOOKED slotted by rank (two title
fights on top, #1v#2s on main card, #6/#7s on prelims); one card is a read.
Gate 0 (read-only, alongside the other read-only tracks): (a) live-caller grep for
assign_slot / calculate_matchup_score on the card-build path; (b) census over every
pre-gen + live card: slot vs rank-sum / title flag / OVR — intentional or accidental;
(c) rest-window census (folds #21): weeks-since-last-fight per booking, fights-per-
fighter vs record (the 0-7s), any booking inside a KO window.
Part 2 (rules, after Gate 0): minimum gap between fights; post-KO/TKO medical
suspension; stop rebooking winless fighters indefinitely; ranked-proximity pairing.
Part 3 (offer surface, merges with OFFER-SCREEN1): offer shows projected slot —
"Cage Dynasty 66 · projected Main Card, bout 3 of 9" — purse scaled to slot, so the
player can trade a prelim now against a main-card slot later. Actionable by design.

## 34. Deploy reload wipes unsaved game state — no autosave
Van's week-2 world (fresh new_game on b6e1d74, accepted fight, CD66 booking) was lost
on the deploy #2 reload; no PA save file had been written since Aug 29. Every reload
(deploy, PA maintenance, idle restart) erases any player who has not manually saved.
Measurement: confirm no autosave hook fires on advance_week / accept / new_game; list
save triggers. Docket: AUTOSAVE1 — autosave on advance-week (at minimum), plus the
existing "auto-load most recent save on landing" backlog item. Player-facing and
data-loss-shaped; should sit high.

## 35. Inbound offer cadence — 11 weeks, no offer for a debut fighter
Session 1: offer at week 1. cc local G2 test: week 3. Session 2 (fresh world, same SHA):
none through week 11. _maybe_generate_inbound_offers is probabilistic; what it keys on
is unmeasured. Measurement: weeks-to-first-offer distribution across ≥20 seeded worlds
for a fresh player fighter; the gate conditions (OVR? rank? condition? camp tier? roster
size?). A debut fighter idle 11 weeks is a player walking away. Folds into MATCHMAKING1
Part 2 or its own OFFERS-CADENCE1.

## 36. POWER1 confirmed live on PA, second fighter
Tyler Costa (player, Wrestler, STR, 65 OVR): Power 50 vs Ankalaev 69; strength 58.
Second player-created fighter, different style, same 50. Closes the loop on #19.

## 37. Condition 16% at week 14 — coach recommendations disagree across screens (CORRECTED)
Correction (Van): the dashboard Coach's Corner DOES warn — "Pull back and reset" and
"running dangerously hot — strongly consider REST". Van had not acted on it. The actual
finding: the fight-camp page's Recommends block said MODERATE with the "Coach" tag on
Light at the same moment the dashboard coach said REST — one coach, two screens, three
answers. Same 16% labelled "Tired" (camp page), "Exhausted" (roster card), "Fatigued"
(Coach's Corner). Fix: one condition→label function, one recommendation source, and the
rest warning on the camp page where the intensity decision is made. The drain itself
(14 idle weeks at MODERATE → 16%) still needs the per-week measurement under
DEVELOPMENT1 Gate 0.
ADDENDUM: training page shows "🔴 Critical fatigue — AUTO-REST ACTIVE this week" at 16%,
but weeks 11–14 ran MODERATE with gains and no trip — threshold is low enough that the
fighter is wrecked before the safety fires. Open question: fight camp (locked MODERATE)
vs auto-rest — which wins on advance? Read next week's Training Log: MODERATE gains =
camp beat auto-rest and the safety is decorative during camps.

## 38. Fight-camp page: three contradictions on one screen
(a) Coach's Corner slot-filling bug: "their ground & pound will exploit your ground
and pound (70)" — opponent style substituted where the player's weakness belongs.
(b) "Coach pick" tag on Counter & Punish while Recommends says Pace & Control.
(c) "Coach" tag on Light intensity while Recommends says MODERATE; Recommends also
shows raw key "Conditioning:chin" where the grid says Toughness. Two sources of truth
for one recommendation. UI-strings batch + coach-corner item (#13).

## 39. Player-path style/stat mismatch
Costa "Wrestler": Boxing 76, Kicks 62, Takedowns 66. GENERATOR1 §4 (style = argmax
over the rolled profile) evidently does not run on generate_prospect_attributes /
setup_fighter. Third player-path gap after at_signing (#5) and power (#19/#36).
Measurement: for N player-generated prospects, does the chosen style match the
argmax family? POWER1 should fix the function, not the symptom — this rides it.

## 40. Card slot is assigned and visible on Upcoming Events — but not on the offer
CD74 list shows 📋 on Costa's fight, 🏆 on the title fight, ⭐ co-main, 🥊 main card.
MATCHMAKING1 Part 3 is therefore surfacing existing data on the offer screen. Separately
the list order is co-main → prelims → main card → main event — neither card order nor
broadcast order. Sort by slot.

## 41. Actual burn ≈ $1,350/week vs stated $125/week
Week 14 balance $29,350 from ~$48k start; Financial Pulse shows −$125/week and "234w
runway". ~$19k left in 14 weeks unitemised (training costs? camp?). Strengthens #30 by
10×; runway figure is false as displayed. Measurement: per-week ledger for the player camp.

## 42. Sig strikes ARE tracked in live play
Headline "Tyler Jackson lands their 100th career significant strike" — so record-book
"No records yet" (#10) is a pre-gen gap, not a missing key. Record book should populate
from live fights; verify after N weeks.

## 43. Compare page shows 14 of 19 stats
Missing: Speed, Recovery, Heart, Composure, Top Control. Training grid shows 18 (no
Power), profile shows 19. Three stat surfaces, three lists. One canonical stat list
(the 19 in core.types) feeding every surface; SAVE-INVARIANTS1 rule: every stat surface
renders all 19.

## 44. WITHDRAWN — profile hero block was a screenshot crop (Van confirmed), not a blank render.

## 45. Fight-camp lock-in posts to `/fight-camp//save` (empty fight id)
Access log at step 4: `POST /fight-camp//save 302`. The form action omits the fight
id. Settings did apply (dashboard showed the camp afterward), so the route resolves
"current fight" somehow — but a blank path segment is a smell, and a 302 is not proof
of a write. Measurement: template form action + route signature; what happens with two
booked fights.

## SAVE-INVARIANTS1 (architect proposal, not ruled)
Read-only checker over any save; one rule per line, violation count per rule; run on a
fresh seeded world and on the PA save. Rules from today: wins-by-method sum to record;
streak ≤ wins; 🛡️ iff winner held the belt at fight time; founding row iff Inaugural
reign, uniformly, never in streak/record; reign lineage chains without gaps; no booking
within N weeks of last fight; no booking inside a KO suspension; age-stage label ==
career-arc stage; badges == predicates; power present and non-default on every fighter;
height/reach/nationality not constant; at_signing populated for every post-capture
fighter. Output is the fix list ordered by count.
RULED (Van, 2026-09-07): runs ALONGSIDE POWER1, together with DEVELOPMENT1 Gate 0, all
read-only. Sequencing inside "alongside": invariants baseline on HEAD → DEVELOPMENT1
Gate 0 baseline on HEAD → POWER1 edit → both re-run on the new HEAD (this is POWER1's
before/after; it needs no separate instrument).

## Ordering recommendation (architect, not ruled)
1 (traceback + classification) → CPU gate → PA-SMOKE1 5a → deploy accept →
docs/filing commit (punch list: 6,217→6226; WSGI 610→479 at L1162-1171;
webhook pull-dir at L468-476; token breach + rotation; systems/ shadow;
harness hardcoded output path; deploy mechanism recorded verbatim) → then
dockets: #1 fix, #3 measurement (folds into DEVELOPMENT1 Gate 0), #5, #9,
#15 offer-screen, #19 power-trainable + player-path power, #8/#12/#13/#14 as a UI-strings batch.
