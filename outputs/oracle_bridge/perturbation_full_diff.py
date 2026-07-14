"""Run one perturbation, dump ALL field diffs (not just first).

Reveals what a perturbation actually localizes to when the vector
is inspected exhaustively.
"""
import _common  # noqa: F401
import io
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = _common.REPO_ROOT
_GB = os.path.join(_REPO, "cage_dynasty_web", "game_bridge.py")

# Import perturbation catalog
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import perturbation_test as pt

def revert():
    subprocess.run(["git", "-C", _REPO, "checkout", "HEAD", "--", _GB], check=True)

def run_full_diff():
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["HOME"] = "/tmp"
    p = subprocess.run([sys.executable, os.path.join(_HERE, "full_diff.py")],
                       env=env, capture_output=True, text=True, timeout=180)
    return p.stdout + p.stderr

def main():
    if len(sys.argv) < 2:
        print("Usage: perturbation_full_diff.py <pert_name>")
        print("Available:", ", ".join(p.name for p in pt.PERTURBATIONS))
        sys.exit(1)
    name = sys.argv[1]
    pert = next((p for p in pt.PERTURBATIONS if p.name == name), None)
    if pert is None:
        print(f"unknown perturbation: {name}")
        sys.exit(1)

    print(f"─" * 78)
    print(f"FULL DIFF — {pert.name}: {pert.description}")
    print(f"─" * 78)
    try:
        pert.apply_fn()
        out = run_full_diff()
    finally:
        revert()
    print(out)

if __name__ == "__main__":
    main()
