"""ORACLE-BRIDGE1 two-step config-triple discrimination.

Closes the last hole in the gate. Van's spec:

  Widen the allowlist temporarily, perturb each of the three, prove
  the fixture catches on outcome fields, revert.

The three fields are damage_multiplier / exchanges_per_round /
standup_threshold — the exact fields the consolidation arc is about.
Normal perturbation_test.py can't touch them because Stage 0d's
_assert_sanctioned_config raises before the fight runs.

This script:
  1. Widens `_SANCTIONED_TRIPLES` in fight_engine.py to include the
     three perturbed triples we're about to test.
  2. For each of the three fields, apply the game_bridge perturbation
     (both call sites — Path A + player), run the checker, verify
     it catches on real outcome fields (not corpse count, not assertion
     error), revert the game_bridge edit.
  3. Reverts fight_engine.py.
  4. Final gates: Stage 0c 928/928, ORACLE-BRIDGE1 baseline 78/78.

Rule: nothing gets committed. Every edit reverts. If any step fails
the wrong way, `git status` at the end must still be clean.
"""
import _common  # noqa: F401
import io
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = _common.REPO_ROOT
_GB = os.path.join(_REPO, "cage_dynasty_web", "game_bridge.py")
_FE = os.path.join(_REPO, "cage_dynasty_web", "fight_engine.py")

# Perturbed triples we're about to test. Small nudges — each maintains
# the (55, damage, standup) shape but changes one field.
PERTURBED_TRIPLES = {
    "damage_0.48→0.49":        (55, 0.49, 10),
    "exchanges_55→56":         (56, 0.48, 10),
    "standup_10→11":           (55, 0.48, 11),
}

def _read(p):
    with open(p) as f:
        return f.read()

def _write(p, s):
    with open(p, "w") as f:
        f.write(s)

def _rewrite_once(path, needle, replacement):
    src = _read(path)
    if src.count(needle) < 1:
        raise RuntimeError(f"needle not found in {path}: {needle!r}")
    # Replace only the first occurrence
    idx = src.find(needle)
    new_src = src[:idx] + replacement + src[idx + len(needle):]
    _write(path, new_src)

def _rewrite_all(path, needle, replacement):
    src = _read(path)
    if needle not in src:
        raise RuntimeError(f"needle not found in {path}: {needle!r}")
    _write(path, src.replace(needle, replacement))

def revert(path):
    subprocess.run(["git", "-C", _REPO, "checkout", "HEAD", "--", path], check=True)

def git_status_clean(paths):
    p = subprocess.run(["git", "-C", _REPO, "status", "--porcelain"] + paths,
                       capture_output=True, text=True)
    return p.stdout.strip() == ""

def run_checker():
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["HOME"] = "/tmp"
    p = subprocess.run(
        [sys.executable, os.path.join(_HERE, "checker.py")],
        env=env, capture_output=True, text=True, timeout=180)
    return p.returncode, p.stdout + p.stderr

def run_full_diff():
    """Return dict of {field_shape: count} for all divergent paths."""
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["HOME"] = "/tmp"
    p = subprocess.run(
        [sys.executable, os.path.join(_HERE, "full_diff.py")],
        env=env, capture_output=True, text=True, timeout=180)
    # Parse "  N  fieldshape" lines
    shapes = {}
    for line in p.stdout.split("\n"):
        m = re.match(r"^\s+(\d+)\s+(\.\S+)\s*$", line)
        if m:
            shapes[m.group(2)] = int(m.group(1))
    return shapes

# ── Widen the allowlist ────────────────────────────────────────────

def widen_allowlist():
    """Temporarily add PERTURBED_TRIPLES to _SANCTIONED_TRIPLES."""
    # Original: _SANCTIONED_TRIPLES = {
    #     _TRIPLE_LIVE_PLAY,
    #     _TRIPLE_PRE_GEN_LEGACY,
    #     _TRIPLE_FI_FALLBACK,
    # }
    # Add explicit tuples inside the set literal.
    needle = "_SANCTIONED_TRIPLES = {\n    _TRIPLE_LIVE_PLAY,"
    additions = "\n".join(
        f"    {t},  # ORACLE-BRIDGE1 two-step: {name}"
        for name, t in PERTURBED_TRIPLES.items()
    )
    replacement = f"_SANCTIONED_TRIPLES = {{\n{additions}\n    _TRIPLE_LIVE_PLAY,"
    _rewrite_once(_FE, needle, replacement)
    # Sanity: file still parses
    subprocess.run([sys.executable, "-c",
                    f"import ast; ast.parse(open({_FE!r}).read())"],
                   check=True, capture_output=True)

# ── Field-specific perturbations ────────────────────────────────────

def apply_damage_nudge():
    _rewrite_all(_GB, "damage_multiplier=0.48,", "damage_multiplier=0.49,")

def apply_exchanges_nudge():
    _rewrite_all(_GB, "exchanges_per_round=55,", "exchanges_per_round=56,")

def apply_standup_nudge():
    _rewrite_all(_GB, "standup_threshold=10,", "standup_threshold=11,")

PERTURBATIONS = [
    ("T1_damage_multiplier_0.48_to_0.49",
     "damage_multiplier: 0.48 → 0.49 (both game_bridge sites)",
     apply_damage_nudge),
    ("T2_exchanges_per_round_55_to_56",
     "exchanges_per_round: 55 → 56 (both game_bridge sites)",
     apply_exchanges_nudge),
    ("T3_standup_threshold_10_to_11",
     "standup_threshold: 10 → 11 (both game_bridge sites)",
     apply_standup_nudge),
]

# ── Runner ─────────────────────────────────────────────────────────

def check_stage0c():
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["HOME"] = "/tmp"
    p = subprocess.run(
        [sys.executable, os.path.join(_REPO, "outputs", "stage0c_golden_master", "checker.py")],
        env=env, capture_output=True, text=True, timeout=180)
    return p.returncode == 0 and "928/928 PASS" in p.stdout

def main():
    # Preconditions
    if not git_status_clean([_GB, _FE]):
        print(f"!!! not starting from clean state — resolve first", file=sys.stderr)
        p = subprocess.run(["git", "-C", _REPO, "diff", "--stat", _GB, _FE],
                           capture_output=True, text=True)
        print(p.stdout, file=sys.stderr)
        sys.exit(1)

    print("=" * 78)
    print("ORACLE-BRIDGE1 TWO-STEP CONFIG-TRIPLE DISCRIMINATION")
    print("=" * 78)
    print(f"Widening Stage 0d _SANCTIONED_TRIPLES with:")
    for name, t in PERTURBED_TRIPLES.items():
        print(f"  {name:>24s}  = {t}")
    print()

    results = []
    try:
        widen_allowlist()
        print("✓ allowlist widened (fight_engine.py edited, unstaged)")
        print()

        # Baseline check under widened allowlist — should still pass 78/78
        # (only added ENTRIES, didn't remove; existing configs unchanged)
        print("[BASELINE (widened allowlist)] checker must still pass 78/78...")
        rc, out = run_checker()
        m = re.search(r"matched: (\d+)/(\d+)", out)
        if rc != 0 or not m or m.group(1) != m.group(2):
            print(f"  ❌ baseline BROKE under widened allowlist — abort")
            print(out[-500:])
            revert(_FE)
            sys.exit(2)
        print(f"  ✓ baseline: {m.group(0)}")
        print()

        # Now the three perturbations
        for name, desc, apply_fn in PERTURBATIONS:
            print(f"[{name}] {desc}")
            try:
                apply_fn()
                print(f"  perturbation applied to game_bridge")
            except Exception as e:
                print(f"  ⚠️  apply FAILED: {e}")
                results.append((name, "APPLY_ERROR", str(e)))
                revert(_GB)
                continue

            try:
                rc, out = run_checker()
                # Also collect full-diff to prove propagation to outcome fields
                shapes = run_full_diff()
            finally:
                revert(_GB)
                if not git_status_clean([_GB]):
                    print(f"  ⚠️  revert did not clean game_bridge!")

            if rc == 0:
                print(f"  ❌ MISS — checker passed with perturbation in place")
                results.append((name, "MISS", "no divergence"))
                continue

            # Verify the catch is on outcome fields, not an AssertionError,
            # not a fight-count crash
            if "AssertionError" in out or "UNSANCTIONED" in out:
                print(f"  ❌ ASSERTION FIRED — allowlist widening didn't cover this triple")
                results.append((name, "ASSERTION_ERROR", "widening incomplete"))
                continue
            if "fight count differs" in out:
                print(f"  ⚠️  CRASH — perturbation broke the run (not a real catch)")
                results.append((name, "CRASH", "fight count mismatch"))
                continue

            m_path = re.search(r"at path:\s+(\S+)", out)
            m_exp  = re.search(r"expected:\s+(.+)", out)
            m_got  = re.search(r"got:\s+(.+)", out)
            if m_path:
                path = m_path.group(1)
                exp = (m_exp.group(1).strip() if m_exp else "?")[:60]
                got = (m_got.group(1).strip() if m_got else "?")[:60]
                if ".config." in path:
                    axis = "config (direct input)"
                elif ".engine_result.method" in path or ".engine_result.finish_round" in path or ".engine_result.winner_id" in path:
                    axis = "outcome (winner/method/round)"
                elif ".engine_result.fighter" in path:
                    axis = "per-round stats"
                elif ".engine_result.judge_scores" in path:
                    axis = "judge scores"
                elif ".engine_result." in path:
                    axis = "engine_result other"
                else:
                    axis = "other localized"
                print(f"  ✓ CAUGHT on {axis}")
                print(f"    first-diff: {path}")
                print(f"      expected: {exp}")
                print(f"      got:      {got}")
                # Report outcome-field spread from full_diff
                outcome_shapes = {k: v for k, v in shapes.items()
                                  if ".engine_result.method" in k
                                  or ".engine_result.finish_round" in k
                                  or ".engine_result.finish_time" in k
                                  or ".engine_result.winner_id" in k
                                  or ".engine_result.loser_id" in k
                                  or ".engine_result.fighter1_stats" in k
                                  or ".engine_result.fighter2_stats" in k
                                  or ".engine_result.judge_scores" in k}
                total_outcome_diffs = sum(outcome_shapes.values())
                if total_outcome_diffs:
                    print(f"    also diffs on OUTCOME fields ({total_outcome_diffs} paths):")
                    for k, n in sorted(outcome_shapes.items(), key=lambda x: -x[1])[:6]:
                        print(f"      {n:>4}  {k}")
                    axis_final = f"{axis} + outcome propagation ({total_outcome_diffs} paths)"
                else:
                    print(f"    NO outcome-field propagation — config value passed but engine unaffected")
                    axis_final = f"{axis} ONLY (no propagation)"
                results.append((name, "CAUGHT", axis_final))
            else:
                tail = "\n    ".join(out.strip().split("\n")[-6:])
                print(f"  ✓ CAUGHT (unparsed rc={rc}), tail:")
                print(f"    {tail}")
                results.append((name, "CAUGHT_UNPARSED", f"rc={rc}"))
    finally:
        # Always revert allowlist widening
        revert(_FE)
        if not git_status_clean([_FE]):
            print("!!! fight_engine.py NOT clean after revert — manual check")
        else:
            print()
            print("✓ allowlist reverted (fight_engine.py back to HEAD)")

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    caught = 0
    outcome_hits = 0
    for name, res, detail in results:
        marker = "✓" if res == "CAUGHT" else ("×" if res == "MISS" else "⚠️")
        print(f"  {marker} {name:<38s} → {res:<20s} {detail[:60]}")
        if res == "CAUGHT":
            caught += 1
            if "outcome" in detail or "per-round" in detail or "engine_result" in detail:
                outcome_hits += 1
    print()
    print(f"CATCH RATE:            {caught}/{len(results)}")
    print(f"caught on OUTCOME axis: {outcome_hits}/{len(results)}")
    print(f"                       ({'good' if outcome_hits == len(results) else 'note: config-input catches also count per Van'})")

    # Final gates
    print()
    print("=" * 78)
    print("FINAL GATES")
    print("=" * 78)
    print(f"  ORACLE-BRIDGE1 baseline (post-revert): ", end="", flush=True)
    rc, out = run_checker()
    m = re.search(r"matched: (\d+)/(\d+)", out)
    print(m.group(0) if m else f"UNKNOWN (rc={rc})")
    print(f"  Stage 0c golden master (post-revert):  ", end="", flush=True)
    ok = check_stage0c()
    print("928/928 PASS" if ok else "FAILED")

    # Final: confirm tree clean
    print()
    if git_status_clean([_GB, _FE]):
        print("✓ working tree clean under cage_dynasty_web/")
    else:
        print("!!! WORKING TREE NOT CLEAN — manual reset required")
        subprocess.run(["git", "-C", _REPO, "status", "--porcelain",
                        "cage_dynasty_web/"], check=False)
        sys.exit(2)

    sys.exit(0 if caught == len(results) else 1)

if __name__ == "__main__":
    main()
