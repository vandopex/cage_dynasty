# WEEK-AXIS1 (c) PREDICATE — SHIPPING FILING (2026-09-11, architect thread)

Status: SHIPPED LOCALLY at ada3955 on 5476783. Not on PA (PA at 7555c35).
Forward-only: new saves + old saves both benefit — the fix is at read/render
time, no data migration. WEEK-AXIS1 (a)-(c) shipped; (d) _recently_fought
open, unmeasured. Deploy #4 payload becomes everything since 7555c35
(dcee687, 266e382, 1ccefa0, 23c7599, 5476783, ada3955, + whatever tools/docs
commits follow).

## 1. WHAT SHIPPED (five edits, one commit)

(1) game_bridge.py:9581 get_fighter_reigns — the sole serialization
    boundary between BeltHistory and the template. Two derived keys added
    per reign dict:
      _won_en = self._event_number_from_name(r.won_event)
      if _won_en is None and 'Founding' in (r.won_event or ''):
          _won_en = 0
      _lost_en = self._event_number_from_name(r.lost_event)
    Founding-by-string over won_week==0 (Van ruling 2026-09-11). Vacated
    reigns filed as VACATED-REIGN1, not fixed here (§5 ruling).
(2) fighter_profile.html:1206-1226 predicate replaced. Division gate
    (r.weight_class == (fight.weight_class or fighter.weight_class));
    unified event_number compare (r.won_event_number == fight.event_number
    for won; won_en < fight_en and (lost_en is none or fight_en < lost_en)
    for defended). Fields bound to locals via .get so a missing key
    becomes real None — Jinja Undefined passes 'is not none' and then
    raises UndefinedError on the compare (§3, central lesson).
(3) save_invariants.py:361-378 template-mirror rewritten to mirror the
    new template exactly (ruling α). Structurally identical to the
    CORRECT predicate; the two now test serializer + mirror agreement,
    not the rendered DOM. Discriminator moved to the render probe (tools
    commit, next paste).
(4) game_bridge.py:7556-7568 _convert_real_fighter cherry-pick augmented
    with 'event_number' and 'weight_class'. Without this, the template
    reads Undefined and no badges render regardless of dump-side
    correctness. ROW-SCHEMA1 expanded to two-stage lossy pipeline (§4).
(5) claude/backlog.md line 18 WEEK-AXIS1 NEXT clause corrected — NOT
    template-only; ROW-SCHEMA1 line updated with the four keys still
    dropped by _convert_real_fighter (was_title_fight, specialty_method,
    opponent_rank_at_fight, round).

## 2. GATES

- Harness R03 (one run, seed 20260907 --weeks 14):
    R03 PASS 0 (template_marks 55, correct_marks 55, FP 0).
    R06 PASS 0 (CHAMP-A holds).
    T-4 event_number_none 0/1809 (STAMP holds).
    R10/R12/R13 PASS.
    WEEK-AXIS1 (b) seeded 291 fighters, range −33..4.
  One run, not two — because the WebFighter change is outside the
  instrument's read path (instrument reads dump directly, not through
  _convert_real_fighter), so a second run adds no independent evidence.
  Stated in the commit body as edit (3)'s rationale.
- template_compile_sweep: 38/38 clean.
- Render probe (Flask test_client, template swap via git show HEAD,
  restore under finally), three fighters, 0 violations:
    Founding HW  Zachary Turner   (0..60):        CD Founding→🏆, CD 23+37→🛡️
    Non-founding Jose Araujo      (SW, 1..9):     CD 1→🏆, CD 5→🛡️
    Multi-reign  Paulo Ferreira   (SW, 9..26 + 33..open): CD 9→🏆, CD 15+21→🛡️, CD 33→🏆, CD 44+53→🛡️
  Validation: every retained badge inside/on a reign window in-division;
  every W inside a window carries a badge; boundaries (lost event) never
  mark.
- Render discrimination NEW vs OLD (git show HEAD:… of the pre-fix
  template rendered against the same context):
    Founding HW:  OLD 🛡️=3 🏆=1  →  NEW 🛡️=2 🏆=1
      Δ 🛡️=−1: OLD wrongly marked a post-reign live fight (CD 69, live wk 13,
      W) as a defense — reign ended at pre-gen event 60, but raw compare
      saw r.won_week=0 < fight.week=13 and r.lost_week=60 > fight.week=13.
      NEW filters via event_number: 60 < 69 → not in window.
    Non-founding SW:  OLD 🛡️=1 🏆=2  →  NEW 🛡️=1 🏆=1
      Δ 🏆=−1: OLD wrongly marked CD 61 (live wk 1) as a belt-won
      because raw r.won_week=1 == fight.week=1 — a pre-gen won_week
      colliding with a live week under the raw axis. NEW filters via
      event_number: won_en=1 != fight_en=61 → no trophy.

## 3. CENTRAL LESSON — WHY THE HARNESS SAID GREEN WHILE THE BROWSER SHOWED NOTHING

The R03 harness reads reign dicts and fight-history rows straight out of
the serialized dump. Serialization for the dump uses BeltHistory.to_dict()
and FighterRecord.fight_history (the raw stored list). Neither passes
through _convert_real_fighter — that's a bridge → WebFighter converter
called only on the render path.

Edits 1-3 as first written passed the harness cleanly. R03 went 1 → 0.
Every marks-count matched. Two independent runs at the tree in question
would still have shown the same green. But the rendered profile showed
zero badges of any kind — because the template read fight.event_number
and the WebFighter cherry-pick at :7556 never included the key. Jinja
returned Undefined; `Undefined is not none` is True (Undefined ≠ None
strictly), so the outer guard passed; the inner compare raised
UndefinedError; Flask served a 500.

The render probe caught it. The harness cannot see the WebFighter
boundary. Rule adopted for future template-touching commits: any change
to a template's predicate must be gated by a render probe that reads
through the same converter routes.py builds context from. R03/α measures
serializer + template-mirror agreement; it does not measure what a
browser paints. Two independent things; two different gates.

Debug trail (retained for the record, not part of the ship):
- First render at status=500 on the elif line — Jinja "'dict object' has
  no attribute 'event_number'".
- Debug canary in the template (`<!-- DEBUG _fight_en=... -->`) surfaced
  `_fight_en=None` on every row. Fight rows do have event_number in the
  dump; the derived WebFighter did not.
- _convert_real_fighter at :7556 cherry-picks 8 of ~12 keys.
- Fix: add 'event_number' + 'weight_class' to the cherry-pick (edit 4).
- Canary removed before commit; template diff confirmed no residue.

## 4. ROW-SCHEMA1 EXPANDED

Two-stage lossy fight_history pipeline:

Stage 1 (raw writes):
  - Live rows write round_finished; pre-gen writes round.
  - Live rows omit weight_class; pre-gen writes it.
  - Both write event_number (post-STAMP).

Stage 2 (_convert_real_fighter at game_bridge.py:7556-7568):
  Cherry-picks 8 keys into WebFighter.fight_history —
    opponent_name, opponent_id, result, method, round_finished,
    event_name, fight_id, week.
  DROPPED from raw rows:
    - event_number    (added back this ship)
    - weight_class    (added back this ship)
    - was_title_fight (still dropped — no template consumer)
    - specialty_method(still dropped — no template consumer)
    - opponent_rank_at_fight (still dropped — no template consumer)
    - round (pre-gen only; still dropped — round_finished substitutes)

Docket disposition: (c) added back the two keys the template needed;
the other four remain dropped. Future unification should either emit the
raw row unchanged (dict-in dict-out) with a schema gate at the write
sites, or list the full contract at the converter. Not this ship.

## 5. RULINGS (Van, 2026-09-11)

1. Choice of derivation: (ii′) — derive at the serializer boundary
   (get_fighter_reigns) over (i) template-side parse. Reigns become the
   uniform data shape the template can read without knowing how it was
   assembled. Symmetric to STAMP for fight rows.
2. Founding detection: 'Founding' in won_event over won_week == 0. String
   is what the serializer actually sees; the week-based fallback would
   also catch legacy season-opener stubs that don't parse the same way.
3. Instrument mirror: α — mirror the new template exactly. R03 discriminates
   at the fix boundary (STATUS FAIL → PASS) and thereafter tests the
   serializer/mirror pair. Regression-sensor role passes to the render
   probe (tools commit, next).
4. VACATED-REIGN1 out of scope for (c). My regression claim in the initial
   proposal ("(c) introduces a new FP window because vacate paths write
   only _title_history") was correct in reasoning but the fix would have
   required a new BeltHistory method + two vacate-site calls + a
   docstring on the off-week _dfc_label collision — 4 lines of code + a
   Gate 0 measurement. Ship the read/render fix cleanly; file the write-
   path fix as its own docket with a browser-check gate. Rationale for
   the "wrong" framing: the docket exists, the harness still can't see
   it (§2 note on WebFighter blindness applies here too), and the
   window is bounded by the successor-crowning event. Real, filed,
   deferred.
5. Row schema unification (ROW-SCHEMA1): add the two keys the template
   needs; do not attempt to unify the pipeline in this commit.
6. Founding row (Gate 0 ruling 3): FOUNDING-ROW2 remains open, unchanged.

## 6. HARNESS-RNG2 STATUS

The render probe is its own process — it builds a fresh bridge via
new_game + 14 advance_week, then renders. Same cross-process variance
that HARNESS-RNG2 documents applies: fighter_ids differ, fight
outcomes differ, which fighter happens to be the Founding HW champion
differs. Discrimination result does NOT depend on this — the probe
searches by role ('Founding HW', 'non-founding with defence',
'multi-reign'), so any fresh run finds fighters that match. The 0-
violations result is architectural (predicate logic), not per-seed.

HARNESS-RNG2 remains non-blocking, unchanged.

## 7. PROCESS NOTES

- The (c) work planned as "template-only, R03 1→0 gate" turned out to be
  4 code edits + 1 board line, not 1 edit. Corrected NEXT clause on the
  board. Every intermediate belief that turned out wrong got named on
  paper: "template-only" (was: 3 files) → "R03 gate is enough" (was: R03
  passes on data the browser can't read) → "vacate is in-scope" (was:
  clean read/render ship, write-path is its own arc).
- The Undefined-is-not-none Jinja gotcha (§3) is worth a lint rule the
  next time template diagnostics come up. Filed only here; not a docket
  by itself.
- Two 4-minute harness runs and one 4-minute render probe run instead
  of the original "template-only" plan. The extra time bought a real
  render measurement — the harness would have shipped a template that
  rendered nothing.
- The render probe's discrimination table (NEW/OLD, named bugs) is the
  first end-to-end proof this arc has produced. Promote to tools next
  paste so it doesn't live in /tmp.
