#!/usr/bin/env python3
"""STAGE 0c golden-master CHECKER.

Loads fixture.json, replays every entry against the current code, diffs
each result vector byte-for-byte against expected. This is the regression
gate Stage 2a and every Stage 2b refactor run against.

Grading:
  - COVERAGE tier → pure byte-equivalence. ONE diff anywhere = FAIL.
  - MODAL tier → byte-equivalence too, at Stage 2a. At Stage 3 the modal
    tier becomes distributional (pre-gen behavior is supposed to change).
    For now: byte-equivalence.

Exit non-zero on any failure so this can gate a commit.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from dataclasses import fields

REPO = "/Users/vandope/Desktop/Games/cage_dynasty"
WEB = os.path.join(REPO, "cage_dynasty_web")
for _p in (os.path.join(REPO, "simulation"),
           os.path.join(REPO, "narrative"),
           os.path.join(REPO, "systems"),
           WEB):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import fight_engine as fe
import fight_integration as fi
import commentary as cm

FIXTURE_PATH = os.path.join(REPO, "outputs/stage0c_golden_master/fixture.json")


# ── Commentary monkey-patch — same shape as generator ─────────────────
_orig_methods = {}
_PATCH_METHODS = [
    "log_event", "emit_fight_open", "emit_gameplan_setup",
    "start_round", "end_round", "generate_submission_commentary",
    "generate_full_finish_sequence", "_generate_commentary_for_action",
]

def commentary_off():
    Cls = cm.FightCommentarySystem
    for m in _PATCH_METHODS:
        if hasattr(Cls, m):
            _orig_methods[m] = getattr(Cls, m)
    def _noop(self, *a, **kw):
        return None
    for m in _PATCH_METHODS:
        if m in _orig_methods:
            setattr(Cls, m, _noop)

def commentary_restore():
    Cls = cm.FightCommentarySystem
    for m, v in _orig_methods.items():
        setattr(Cls, m, v)
    _orig_methods.clear()


# ── Rehydrate ────────────────────────────────────────────────────────
def dict_to_fighter_attrs(d):
    return fe.FighterAttributes(**d, fighting_style=None)

def make_fi_config(rounds, is_title, is_main):
    # STAGE 0d — pins LIVE_PLAY (55, 0.48, 10) explicitly, no inheritance.
    return fe.FightConfig(
        scheduled_rounds=rounds,
        exchanges_per_round=55,
        damage_multiplier=0.48,
        standup_threshold=10,
        submission_progress_to_finish=70.0,
        submission_escape_threshold=85.0,
        is_title_fight=is_title, is_main_event=is_main,
    )

def make_fe_config(rounds, is_title):
    c = fe.FightConfig.championship_fight() if is_title else fe.FightConfig.standard_fight()
    if rounds == 5 and not is_title:
        c.scheduled_rounds = 5
    return c


def run_fi(entry):
    f1 = dict_to_fighter_attrs(entry["fighter1"])
    f2 = dict_to_fighter_attrs(entry["fighter2"])
    random.seed(entry["seed"])
    cfg = make_fi_config(entry["scheduled_rounds"],
                         entry["is_title"], entry["is_main_event"])
    r = fi.simulate_narrated_fight(
        f1, f2, rounds=entry["scheduled_rounds"],
        is_title_fight=entry["is_title"],
        is_main_event=entry["is_main_event"], config=cfg)
    return {
        "winner_id": r.winner_id, "loser_id": r.loser_id,
        "method": r.method, "finish_round": r.finish_round,
        "finish_time": r.finish_time, "decision_type": r.decision_type,
        "judge_scores": [list(x) for x in (r.judge_scores or [])],
        "fighter1_stats": [dict(s) for s in (r.fighter1_stats or [])],
        "fighter2_stats": [dict(s) for s in (r.fighter2_stats or [])],
        "key_moments_len": len(r.key_moments) if r.key_moments else 0,
    }


def run_fe(entry):
    f1 = dict_to_fighter_attrs(entry["fighter1"])
    f2 = dict_to_fighter_attrs(entry["fighter2"])
    random.seed(entry["seed"])
    cfg = make_fe_config(entry["scheduled_rounds"], entry["is_title"])
    r = fe.simulate_fight(f1, f2, cfg, heat_level=entry["heat_level"])
    return {
        "winner_id": r.winner_id, "loser_id": r.loser_id,
        "method": r.method, "finish_round": r.finish_round,
        "finish_time": r.finish_time,
        "fighter1_stats": r.fighter1_stats or [],
        "fighter2_stats": r.fighter2_stats or [],
        "event_log_len": len(r.event_log) if r.event_log else 0,
        "event_types": [e.event_type for e in (r.event_log or [])],
    }


def _first_diff(expected, got, path=""):
    """Return (path, expected_repr, got_repr) or None if identical."""
    if type(expected) != type(got):
        return (path, f"type={type(expected).__name__}", f"type={type(got).__name__}")
    if isinstance(expected, dict):
        for k in sorted(set(expected.keys()) | set(got.keys())):
            if k not in expected:
                return (f"{path}.{k}", "MISSING", "PRESENT")
            if k not in got:
                return (f"{path}.{k}", "PRESENT", "MISSING")
            d = _first_diff(expected[k], got[k], f"{path}.{k}")
            if d: return d
        return None
    if isinstance(expected, list):
        if len(expected) != len(got):
            return (f"{path}.len", len(expected), len(got))
        for i, (a, b) in enumerate(zip(expected, got)):
            d = _first_diff(a, b, f"{path}[{i}]")
            if d: return d
        return None
    if expected != got:
        return (path, repr(expected)[:100], repr(got)[:100])
    return None


def main():
    t0 = time.time()
    with open(FIXTURE_PATH) as f:
        fx = json.load(f)
    print(f"# STAGE 0c CHECKER")
    print(f"# fixture repo SHA: {fx['metadata']['repo_sha']}")
    print(f"# fixture generated: {fx['metadata']['generated_at']}")
    print(f"# entries: {len(fx['entries'])} "
          f"(modal={fx['metadata']['tier_modal_n']}, "
          f"coverage={fx['metadata']['tier_coverage_n']})")
    print()

    modal_pass = modal_fail = coverage_pass = coverage_fail = 0
    first_fails_by_tier = {"modal": [], "coverage": []}

    commentary_off()
    try:
        for entry in fx["entries"]:
            expected_fi = entry["expected_fi"]
            expected_fe = entry["expected_fe"]

            got_fi = run_fi(entry)
            got_fe = run_fe(entry)

            fi_diff = _first_diff(expected_fi, got_fi, "fi")
            fe_diff = _first_diff(expected_fe, got_fe, "fe")

            tier = entry["tier"]
            if fi_diff is None and fe_diff is None:
                if tier == "modal": modal_pass += 1
                else: coverage_pass += 1
            else:
                if tier == "modal": modal_fail += 1
                else: coverage_fail += 1
                if len(first_fails_by_tier[tier]) < 5:
                    first_fails_by_tier[tier].append({
                        "id": entry["id"], "seed": entry["seed"],
                        "coverage_cell": entry.get("coverage_cell"),
                        "fi_diff": fi_diff, "fe_diff": fe_diff,
                    })
    finally:
        commentary_restore()

    total = modal_pass + modal_fail + coverage_pass + coverage_fail
    elapsed = time.time() - t0

    print("═" * 72)
    print(f"  MODAL    : {modal_pass}/{modal_pass+modal_fail} PASS")
    print(f"  COVERAGE : {coverage_pass}/{coverage_pass+coverage_fail} PASS")
    print(f"  ─ total  : {modal_pass+coverage_pass}/{total} PASS")
    print(f"  ─ time   : {elapsed:.1f}s")
    print("═" * 72)

    if first_fails_by_tier["modal"] or first_fails_by_tier["coverage"]:
        print()
        for tier, fails in first_fails_by_tier.items():
            if fails:
                print(f"── first {len(fails)} {tier} FAILs ──")
                for f in fails:
                    print(f"  id={f['id']}  seed={f['seed']}  cell={f['coverage_cell']}")
                    if f["fi_diff"]:
                        print(f"    FI:  {f['fi_diff'][0]}   exp={f['fi_diff'][1]}   got={f['fi_diff'][2]}")
                    if f["fe_diff"]:
                        print(f"    FE:  {f['fe_diff'][0]}   exp={f['fe_diff'][1]}   got={f['fe_diff'][2]}")
        sys.exit(1)

    print(f"\n  ✓ PASS — every entry byte-identical to fixture.")


if __name__ == "__main__":
    main()
