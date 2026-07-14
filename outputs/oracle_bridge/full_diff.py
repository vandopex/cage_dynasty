"""ORACLE-BRIDGE1 full-diff mode.

Runs the game with the current tree, compares against fixture.json,
and dumps EVERY divergent field (not just the first).

Used to see what the vector actually localizes vs what the checker
just reports first in alphabetical order.
"""
import _common  # noqa: F401
import io
import json
import os
import sys
import contextlib
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import fixture_generator as fg

FIXTURE_PATH = os.path.join(_HERE, "fixture.json")

def all_diffs(expected, got, path="", out=None):
    if out is None:
        out = []
    if type(expected) != type(got):
        out.append((path, f"type={type(expected).__name__}", f"type={type(got).__name__}"))
        return out
    if isinstance(expected, dict):
        for k in sorted(set(expected.keys()) | set(got.keys())):
            if k not in expected:
                out.append((f"{path}.{k}", "MISSING", "PRESENT"))
                continue
            if k not in got:
                out.append((f"{path}.{k}", "PRESENT", "MISSING"))
                continue
            all_diffs(expected[k], got[k], f"{path}.{k}", out)
        return out
    if isinstance(expected, list):
        if len(expected) != len(got):
            out.append((f"{path}.len", len(expected), len(got)))
        for i, (a, b) in enumerate(zip(expected, got)):
            all_diffs(a, b, f"{path}[{i}]", out)
        return out
    if expected != got:
        e_repr = repr(expected)[:60] if not isinstance(expected, str) else expected[:60]
        g_repr = repr(got)[:60] if not isinstance(got, str) else got[:60]
        out.append((path, e_repr, g_repr))
    return out

def field_name(path):
    """Strip fights[N] prefix and array indices, leaving the field shape."""
    # e.g. fights[74].engine_result.fighter1_stats[2].sig_strikes_landed
    #  → engine_result.fighter1_stats[].sig_strikes_landed
    import re
    s = path
    s = re.sub(r"^fights\[\d+\]\.", "", s)
    s = re.sub(r"\[\d+\]", "[]", s)
    return s

def main():
    with open(FIXTURE_PATH) as f:
        fixture = json.load(f)

    fg._captured_fights.clear()
    current, _ = fg.build_fixture()

    # Normalize both through JSON to strip type differences
    exp = json.loads(json.dumps(fixture, sort_keys=True, default=str))
    got = json.loads(json.dumps(current, sort_keys=True, default=str))

    diffs = all_diffs(exp, got, "")

    print(f"Total divergent paths: {len(diffs)}")
    print()
    # Group by field type
    by_field = Counter()
    for path, e, g in diffs:
        by_field[field_name(path)] += 1
    print("Diffs grouped by field shape:")
    for f, n in by_field.most_common(30):
        print(f"  {n:>5}  {f}")

if __name__ == "__main__":
    main()
