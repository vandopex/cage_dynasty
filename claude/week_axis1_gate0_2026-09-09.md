# WEEK-AXIS1 — GATE 0 FILING (2026-09-09, HEAD 1f1f08a, read-only)

Status: FILING. Measurements by cc on the instrument path (seed 20260907;
dump outputs/sm_inv/dump_20260908.json, the post-(a) baseline). Rulings at
the end are Van's, 2026-09-09. History; CLAUDE.md carries an index line only.
Serves Gate 0 filing (claude/gate0_baselines_2026-09-07.md) rulings 3 and 4.
Line numbers are at 1f1f08a — re-grep before editing.

## 1. THE MEASUREMENT (closes F1's open mechanism question)

At week 0, immediately after new_game on the instrument path:
  len(_fighter_cooldowns) = 0, len(_fighter_signing_available) = 0.
World-gen ran 1618 pre-gen fights and wrote nothing to either structure.
_fighter_cooldowns is initialised empty at game_bridge.py:2245, written
only by _apply_cooldown (:15467, `week + cooldown`) from the four call
sites inside _advance_week_impl (:3828, :3840, :3853, :3865), read by
_is_available (:15477, `.get(fighter_id, 0) <= week`). world_init.py and
matchmaking.py: 0 hits. Serialised/deserialised at :2923/:3254; :14591/
:14604 reuse the dict as a seen-flag for OVR-milestone news (not cooldown
semantics — noted, not touched).

Consequence: `.get(fid, 0) <= week` is true for every fighter with no
entry, so every fighter is available at live week 1 regardless of when
they last fought in pre-gen. The R06 seam violations (8 on the dump:
last pre-gen week 58/59, first live week 1/2, true gap 2-3 weeks against
a 4-week floor) are a missing-initialisation defect at the new_game
handoff, not a cooldown-arithmetic defect.

Caveat on the per-name table cc printed: the probe's log showed a coach
name that may not be the instrument's (HARNESS-RNG1). The dict being
empty at week 0 does not depend on which world was built; the eight
"ABSENT" rows are consistent with it but are not independent evidence.

## 2. THE SOLE R03 VIOLATOR (Founding reign)

fid 46708243, Heavyweight. Reign won_week 0 / lost_week 60,
won_event "Cage Dynasty Founding — Heavyweight Championship". Fight at
live week 7 (unified 67, parsed from "Cage Dynasty 67"; event_number
None as on every live row). fighter_profile.html:1207-1211 compares raw:
0 < 7 and 60 > 7 → reign active → 🛡️. Unified predicate: reign spans
pre-gen 0..60, fight is 67 → inactive → no defense. R03 detail:
template marks 54, correct 54, false positives 1, unclassifiable 0.
This is the template-predicate half of ruling 4, not a founding-row
defect; the founding row itself (world_init.py:1984-1995, week 0,
event_number 0, method "Inaugural Crown") is unchanged post-(a).

## 3. CENSUS — who compares weeks across axes

- fighter_profile.html:1207-1211 belt-defense predicate: the ONLY
  cross-axis compare among 56 `.week` reads in templates + bridge. All
  others are single-axis (weeks_until on scheduled fights, write-time
  week on events/news, week_number display).
- _recently_fought (game_bridge.py:12328+): iterates fight_history by
  opponent_id and compares `h.get('week', 0) >= cutoff` raw. Cross-axis
  by construction; effect UNMEASURED. If cutoff = live_week − N, every
  pre-gen row satisfies it during early live play — rematch prevention
  would be over-suppressing pairings against anyone the fighter met in
  pre-gen. Inference, not a number. Measure before touching.
- Streak: game_bridge.py:7288-7310 (current) and :7315-7327 (best) both
  carry STREAK-INAUGURAL-FILTER1 (:7285-7292, method == 'Inaugural
  Crown'). R01/R02 PASS on the dump. Ruling 3's streak half is already
  in force; its remaining consequence is the R03 hit above.
- 17 fight_history iterators in game_bridge + 1 in templates; most are
  opponent-id lookups, injury, nickname earning. None axis-filtered;
  only _recently_fought reads .week across the seam.

## 4. THE THREE LIVE WRITES AND WHERE N COMES FROM

fight_history.append sites: game_bridge.py:5734/5735
(_simulate_card_fights), :14266 (_simulate_ai_fights_week), :18469
(_run_real_engine). None stamps event_number (4 `event_number` hits in
the bridge, all _dfc_event_offset bookkeeping). (b) added
ovr_at_signing/week_signed and did not touch these.
Live event N: _dfc_event_offset captured from world-gen's
next_event_number at :2386-2388; _dfc_label(week) at :2835-2854 computes
event_num = (week − week // 3) + offset (offset 60 on a fresh save →
first live card "Cage Dynasty 61"). The name string is the only carrier.
Note: N is not week + 60 — the //3 term means live weeks and live event
numbers are not one-to-one. A stamp must use _dfc_label's arithmetic (or
the fight dict's already-computed event name), never week + offset.

## 5. RULINGS (Van, 2026-09-09 — "go with your recs")

1. WEEK-AXIS1 ships as four single-purpose commits, each read-only
   diagnose → edit → gate → STOP → commit, forward-only (new saves;
   existing saves' rows untouched):
   (a) STAMP: event_number on the three live writes, computed the same
       way the event name is (§4). Gate: fresh --weeks 14 dump has 0
       live rows with event_number None; pre-gen rows unchanged; every
       instrument rule's STATUS unchanged.
   (b) SEED: at new_game, seed _fighter_cooldowns only, one blanket
       value per fighter with pre-gen history: (last pre-gen week − 60)
       + COOLDOWN_WINNER, so a week-59 fighter is available at live
       week 3. Loser/champion cooldowns are NOT reconstructed from
       history (documented simplification). _fighter_signing_available
       untouched (free agency, not fights). Gate: R06 seam 8 → 0 on the
       instrument, pre-gen/live counts unchanged, every other rule's
       STATUS unchanged, printed count + min/max of seeded entries.
   (c) PREDICATE: fighter_profile.html belt-defense compare on the
       unified axis (a provenance/absolute-week field on rows and
       reigns, or the instrument's parse — decided at (c)'s Gate 0).
       Gate: R03 1 → 0, template marks == correct marks.
   (d) _recently_fought: measured first (how many pairings it suppresses
       at live weeks 1-14 with raw vs axis-aware weeks), then fixed if
       the number says so. Own Gate 0.
2. Founding row (Gate 0 ruling 3) stands for this arc. Filed as an open
   question, not re-ruled: a row that is not a fight living in
   fight_history and filtered by consumers is output-side; the
   engine-side shape is founding provenance on the reign. FOUNDING-ROW2,
   backlog, no ship date.
3. The eight-name table in cc's report is not quoted anywhere (§1
   caveat). Only the instrument's numbers are quoted.

## 6. PROCESS NOTES

- The decision rule was written into the paste before the measurement
  ("if empty → seed; if populated-but-raw → translate"). The number
  picked the branch; nobody argued about it afterwards.
- cc's "worth a diagnostic session" on streaks was a read offered in
  place of a measurement that already existed (R01/R02 PASS). Caught.
- cc noticed the //3 term in _dfc_label. Without it, (a) would have
  stamped week + 60 and produced event numbers that disagree with the
  event names on the same row — a "looks wired" defect written by the
  fix itself.
