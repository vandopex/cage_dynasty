"""ORACLE-BRIDGE1 shared harness setup.

Two responsibilities:
  1. wsgi.py-mirroring sys.path setup (repo root NOT on path)
  2. uuid.uuid4 monkey-patch to a seeded RNG for determinism

MUST be imported BEFORE game_bridge. Production code unchanged.
"""
import os
import sys
import random
import uuid as _uuid

# Determinism seed for the fixture. Baked in — do not vary.
SEED = 42

# ── sys.path mirror ────────────────────────────────────────────────
os.environ["HOME"] = "/tmp"
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
               if p != '' and os.path.abspath(p) not in (_REPO_ROOT, _SCRIPT_DIR)]
for _p in [os.path.join(_REPO_ROOT, "simulation"),
           os.path.join(_REPO_ROOT, "narrative"),
           os.path.join(_REPO_ROOT, "systems"),
           os.path.join(_REPO_ROOT, "cage_dynasty_web")]:
    if os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

# ── uuid monkey-patch ──────────────────────────────────────────────
# uuid.uuid4() uses os.urandom → nondeterministic under fixed seed.
# Replace it with a seeded generator to make the whole run reproducible.
# Production code untouched — this patch lives in the fixture harness
# and reverts when the process exits.
_uuid_rng = random.Random(SEED)
def _seeded_uuid4():
    return _uuid.UUID(int=_uuid_rng.getrandbits(128))
_uuid.uuid4 = _seeded_uuid4

# Also seed the main random module for the same reason.
random.seed(SEED)

REPO_ROOT = _REPO_ROOT
