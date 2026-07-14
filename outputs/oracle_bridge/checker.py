"""ORACLE-BRIDGE1 checker.

Replays the fixture: same seed, same uuid patch, same player fighter,
same MAIN weeks + PLAYER tier. Captures the same wide vector, byte-
diffs against the stored fixture. PASS iff every captured fight
matches every field byte-equal.

Exit non-zero on any diff so this can gate a commit.
"""
import _common  # noqa: F401
import io
import json
import os
import sys
import contextlib

# Ensure this directory is on sys.path for local module imports
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Reuse generator's capture machinery
import fixture_generator as fg

FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixture.json")

def _collect_diffs(expected, got, path, out):
    if type(expected) != type(got):
        out.append((path, f"type={type(expected).__name__}", f"type={type(got).__name__}"))
        return
    if isinstance(expected, dict):
        for k in sorted(set(expected.keys()) | set(got.keys())):
            if k not in expected:
                out.append((f"{path}.{k}", "MISSING", "PRESENT"))
                continue
            if k not in got:
                out.append((f"{path}.{k}", "PRESENT", "MISSING"))
                continue
            _collect_diffs(expected[k], got[k], f"{path}.{k}", out)
        return
    if isinstance(expected, list):
        if len(expected) != len(got):
            out.append((f"{path}.len", len(expected), len(got)))
        for i, (a, b) in enumerate(zip(expected, got)):
            _collect_diffs(a, b, f"{path}[{i}]", out)
        return
    if expected != got:
        e_repr = repr(expected)[:80] if not isinstance(expected, str) else expected[:80]
        g_repr = repr(got)[:80] if not isinstance(got, str) else got[:80]
        out.append((path, e_repr, g_repr))

# Prioritized field-shape patterns — report these before commentary_*
# so a perturbation's LOCALIZED signal surfaces, not the alphabetically-first
# noisy field. Order = priority.
_INFORMATIVE_PATTERNS = [
    # Direct-input signals (perturbation targets)
    ".config.",
    ".gameplan_f",
    ".starting_stamina_f",
    ".fa1.fighting_style",
    ".fa2.fighting_style",
    ".fa1.",
    ".fa2.",
    ".intro_f",
    ".stored_commentary_",
    # Direct-output signals
    ".engine_result.winner_id",
    ".engine_result.loser_id",
    ".engine_result.method",
    ".engine_result.finish_round",
    ".engine_result.finish_time",
    ".engine_result.decision_type",
    ".engine_result.sub_type",
    # Post-fight state deltas
    ".f1_post.",
    ".f2_post.",
    ".engine_result.fighter1_stats",
    ".engine_result.fighter2_stats",
    ".engine_result.judge_scores",
]

def _priority(path):
    for i, pat in enumerate(_INFORMATIVE_PATTERNS):
        if pat in path:
            return i
    # commentary_len / commentary_sha16 / key_moments_len — LAST
    return 999

def first_diff(expected, got, path=""):
    """Return the highest-priority divergent field, not just the alphabetically-first.

    A first_diff that returns commentary_len when winner_id/method/round
    also diff is misleading — it hides the localized catch. This version
    collects all diffs then returns the one with the informative-pattern
    lowest priority index.
    """
    all_d = []
    _collect_diffs(expected, got, path, all_d)
    if not all_d:
        return None
    # Sort by (priority, path) — lower priority = more informative
    all_d.sort(key=lambda d: (_priority(d[0]), d[0]))
    return all_d[0]

def main():
    if not os.path.exists(FIXTURE_PATH):
        print(f"!!! fixture not found: {FIXTURE_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(FIXTURE_PATH) as f:
        fixture = json.load(f)

    # Reset generator's global capture list (it's a module import; live list)
    fg._captured_fights.clear()

    # Build the current fixture via the same generator machinery
    current, _log = fg.build_fixture()

    expected_meta = fixture.get("meta", {})
    got_meta = current.get("meta", {})

    print("=" * 78)
    print("ORACLE-BRIDGE1 CHECKER")
    print("=" * 78)
    print(f"  fixture: {FIXTURE_PATH}")
    print(f"  fixture meta:  {expected_meta}")
    print(f"  live meta:     {got_meta}")
    print()

    # Meta-level fields — total counts only (not session-wide hashes,
    # which localize nothing and produced a fake 7/7 in v1). If these
    # differ, the fixture ran a different number of things — that's
    # structural and worth an early exit, but it's still a coarse signal.
    for meta_key in ("total_captured_fights", "total_events"):
        e = expected_meta.get(meta_key)
        g = got_meta.get(meta_key)
        if e != g:
            print(f"  ❌ FAIL — meta.{meta_key} differs")
            print(f"    at path: meta.{meta_key}")
            print(f"    expected: {e}")
            print(f"    got:      {g}")
            sys.exit(1)

    # Session-hash fields (commentary_session_sha16, commentary_stored_key_count)
    # are captured in the fixture but the checker DOES NOT gate on them.
    # They exist as a backstop for future forensics — not as a discrimination
    # signal. A perturbation that only trips a hash without changing any
    # fight-level field is a perturbation the vector cannot localize.

    # Compare fight vectors — the meat of the check
    expected_fights = fixture.get("fights", [])
    got_fights = current.get("fights", [])

    n_expected = len(expected_fights)
    n_got = len(got_fights)

    if n_expected != n_got:
        print(f"  ❌ FAIL — fight count differs: expected {n_expected}, got {n_got}")
        sys.exit(1)

    # Round-trip through JSON to normalize types (int vs str keys, etc.)
    expected_normalized = json.loads(json.dumps(expected_fights, sort_keys=True, default=str))
    got_normalized = json.loads(json.dumps(got_fights, sort_keys=True, default=str))

    matches = 0
    first_bad = None
    for i, (e, g) in enumerate(zip(expected_normalized, got_normalized)):
        if e == g:
            matches += 1
        else:
            if first_bad is None:
                first_bad = (i, first_diff(e, g, f"fights[{i}]"))

    print(f"  matched: {matches}/{n_got}")

    if first_bad is None:
        print()
        print("  ✓ PASS — every fight vector byte-identical to fixture.")
        sys.exit(0)
    else:
        idx, (path, exp, got) = first_bad
        print()
        print(f"  ❌ FAIL — first divergent fight at index {idx}")
        print(f"    at path: {path}")
        print(f"    expected: {exp}")
        print(f"    got:      {got}")
        sys.exit(1)

if __name__ == "__main__":
    main()
