"""Shared env setup for save_invariants + dev1_gate0 harnesses.

Ensures the cage_dynasty_web/ directory is at sys.path[0] so
bare `import fight_engine` / `import fight_integration` resolve
to the WEB copies, not the root/systems CLI shadows. Also puts
narrative/ and systems/ on the path (matching wsgi.py's setup).

Import this module FIRST — before any project module.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))  # …/cage_dynasty
_WEB = os.path.join(_REPO, "cage_dynasty_web")
_NARR = os.path.join(_REPO, "narrative")
_SYS = os.path.join(_REPO, "systems")

# Order matches wsgi.py (project_home ends up at index 0):
for p in [_WEB, _SYS, _NARR]:
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

# Move CWD to web dir so runtime file writes (saves) go into the
# right place. Original CWD saved so the harness can still write
# outputs under repo root.
ORIG_CWD = os.getcwd()
os.chdir(_WEB)

WEB_DIR = _WEB
REPO_DIR = _REPO
