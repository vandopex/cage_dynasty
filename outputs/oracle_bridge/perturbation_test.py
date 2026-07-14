"""ORACLE-BRIDGE1 discrimination suite.

Six sabotages, one per named game_bridge decision. Plus one narrow-
vector sub-case that verifies the fixture catches a gameplan flip
producing the SAME winner but different round.

Each test:
  1. Verify clean baseline: checker passes 78/78.
  2. Apply a one-token edit to a game_bridge source line.
  3. Run the checker. Expect FAIL. Record the first divergence.
  4. Revert the edit. Confirm HEAD and working tree are clean.

Report the catch rate at the end.

Rule: NEVER leave a perturbation in place. NEVER git-commit anything.
"""
import _common  # noqa: F401
import io
import os
import re
import subprocess
import sys
import contextlib
from copy import copy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

_REPO = _common.REPO_ROOT
_GB = os.path.join(_REPO, "cage_dynasty_web", "game_bridge.py")

def run_checker():
    """Run the checker in a subprocess (clean state). Return (rc, stdout)."""
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["HOME"] = "/tmp"
    p = subprocess.run(
        [sys.executable, os.path.join(_HERE, "checker.py")],
        env=env, capture_output=True, text=True, timeout=120)
    return (p.returncode, p.stdout + p.stderr)

def git_status_clean(paths):
    p = subprocess.run(["git", "-C", _REPO, "status", "--porcelain"] + paths,
                       capture_output=True, text=True)
    return p.stdout.strip() == ""

def revert_file(path):
    subprocess.run(["git", "-C", _REPO, "checkout", "HEAD", "--", path], check=True)

class Perturbation:
    def __init__(self, name, description, apply_fn, revert_fn=None,
                 expected_catch_axis=""):
        self.name = name
        self.description = description
        self.apply_fn = apply_fn
        self.revert_fn = revert_fn or (lambda: revert_file(_GB))
        self.expected_catch_axis = expected_catch_axis

# ── Perturbation implementations ───────────────────────────────────

def _rewrite_gb(needle, replacement, occurrence=1):
    """Replace nth occurrence of needle in game_bridge.py. In-place, byte-preserving otherwise."""
    with open(_GB) as f:
        src = f.read()
    parts = src.split(needle)
    if len(parts) - 1 < occurrence:
        raise RuntimeError(f"needle not found (occurrence={occurrence}): {needle!r}")
    # Rebuild: keep first `occurrence-1` needles as-is, replace the `occurrence`-th
    new_parts = []
    for i, p in enumerate(parts):
        new_parts.append(p)
        if i < len(parts) - 1:
            if i + 1 == occurrence:
                new_parts.append(replacement)
            else:
                new_parts.append(needle)
    new_src = "".join(new_parts)
    with open(_GB, "w") as f:
        f.write(new_src)

def apply_1_config_submission():
    """submission_progress_to_finish=70.0 → 65.0 at Path A config (line ~13602).

    Original plan was to nudge `damage_multiplier=0.48`. That doesn't
    work: Stage 0d's `_assert_sanctioned_config` at fight_engine.py:~863
    raises AssertionError on any config outside the three sanctioned
    triples LIVE_PLAY/PRE_GEN_LEGACY/FI_FALLBACK. The assertion is
    the (55, damage, standup) tuple. Any damage_multiplier ≠ 0.48
    with (55, X, 10) trips the assertion. The `_eng UnboundLocalError`
    cascade at game_bridge.py:13816 (except block doesn't set _eng=None)
    then propagates → 74/78 fights fail to resolve. Fixture 'catches'
    on the corpse count via meta.total_captured_fights — not on
    fight-outcome divergence.

    This perturbation targets `submission_progress_to_finish`, which
    is a FightConfig field NOT in the sanctioned tuple. Assertion
    passes; all 78 fights complete; fight outcomes shift on submission
    dynamics; fixture catches on real outcome fields.

    Two findings from the tuning:
      A. The Stage 0d assertion IS itself a coverage tripwire — it
         catches config-triple perturbations before the fixture can
         see them. Not a bug in the fixture; a fact about the config
         defense-in-depth stack.
      B. The `_eng UnboundLocalError` at game_bridge.py:13816 is a
         real bug in the fight-resolution fallback path (except at
         :13741 sets winner/loser/method/rnd but not _eng). Not this
         ship — but the fragility is real.
    """
    _rewrite_gb(
        "submission_progress_to_finish=70.0,",
        "submission_progress_to_finish=65.0,",
        occurrence=1,
    )

def apply_2_gameplan_flip():
    """Force AGGRESSIVE gameplan aggression map from +1 to -1."""
    # _GAMEPLAN_AGGRESSION dict — actual pattern is `"AGGRESSIVE": 1,` (no +)
    _rewrite_gb('"AGGRESSIVE": 1,', '"AGGRESSIVE": -1,', occurrence=1)

def apply_3_stamina_bypass():
    """Force starting_stamina to a constant 100 at BOTH fight-call sites."""
    # Path A (:13635):   starting_stamina_f1=_f1_stam,     → 100.0
    # Player (:17556):   starting_stamina_f1=_f1_stamina,  → 100.0
    # Path A world-init fighters have fatigue=0 → get_starting_stamina(0)==100,
    # so Path A perturbation is a noop for this seed. Player tier loads
    # fatigue={0,25,50,75} explicitly, so player perturbation catches.
    _rewrite_gb("starting_stamina_f1=_f1_stam,", "starting_stamina_f1=100.0,", occurrence=1)
    _rewrite_gb("starting_stamina_f1=_f1_stamina,", "starting_stamina_f1=100.0,", occurrence=1)

def apply_4_style_null():
    """Force fighting_style=None on FighterAttributes for ALL fighters."""
    # _make_fighter_attrs at ~16878 uses `fighting_style = style,` as the
    # kwarg. Force to None. Exercises fighter-attr construction path for
    # every fight in the fixture.
    _rewrite_gb(
        "fighting_style      = style,",
        "fighting_style      = None,  # POISON",
        occurrence=1,
    )

def apply_5_intro_null():
    """Force intro dict to empty in _build_intro_dict."""
    # Rewrite _build_intro_dict to return {} always. Simplest: modify the
    # first return path.
    # Function def: `def _build_intro_dict(fighter) -> dict:` at line ~444
    _rewrite_gb(
        "def _build_intro_dict(fighter) -> dict:",
        "def _build_intro_dict(fighter) -> dict: return {}\ndef _build_intro_dict_orig(fighter) -> dict:",
        occurrence=1,
    )

def apply_6_commentary_skip():
    """Skip _fight_commentary storage in Path A."""
    # Path A stores at ~13649-13671 with:  self._fight_commentary[_ai_fight_id] = _ai_lines
    _rewrite_gb(
        "self._fight_commentary[_ai_fight_id] = _ai_lines",
        "pass  # POISON: skip commentary storage",
        occurrence=1,
    )

# Narrow-vector case: gameplan flip → same winner, different round.
def apply_narrow_vector():
    """Flip BALANCED gameplan aggression from 0 → +1. In many player fights
    the ~74 OVR player vs ~50s OVR opponents will still win, but the
    per-round stats (pace, damage progression, stamina drain) should shift.
    Verifies the wide vector catches gameplan effects that a winner-only
    checker would miss.
    """
    # _GAMEPLAN_AGGRESSION dict — actual pattern is `"BALANCED":   0,`
    # (note the extra spaces from column alignment)
    _rewrite_gb(
        '"BALANCED":   0,',
        '"BALANCED":   1,  # POISON: narrow-vector case',
        occurrence=1,
    )

PERTURBATIONS = [
    Perturbation("1_config_submission",
                 "Path A _FightConfig submission_progress_to_finish 70.0 → 65.0",
                 apply_1_config_submission,
                 expected_catch_axis="config.submission_progress_to_finish + engine_result deltas"),
    Perturbation("2_gameplan_flip",
                 "_GAMEPLAN_AGGRESSION AGGRESSIVE +1 → -1",
                 apply_2_gameplan_flip,
                 expected_catch_axis="PLAYER-tier gameplan_f1.aggression + engine_result deltas"),
    Perturbation("3_stamina_bypass",
                 "Path A starting_stamina_f1 fatigue-wired → constant 100.0",
                 apply_3_stamina_bypass,
                 expected_catch_axis="starting_stamina_f1 + engine_result"),
    Perturbation("4_style_null",
                 "_make_fighter_attrs fighting_style → None",
                 apply_4_style_null,
                 expected_catch_axis="fa1.fighting_style + engine_result"),
    Perturbation("5_intro_null",
                 "_build_intro_dict returns {} always",
                 apply_5_intro_null,
                 expected_catch_axis="commentary_sha16 (intro line missing)"),
    Perturbation("6_commentary_skip",
                 "Skip self._fight_commentary storage",
                 apply_6_commentary_skip,
                 expected_catch_axis="commentary_sha16 (stored value empty)"),
    Perturbation("N_narrow_vector",
                 "BALANCED gameplan aggression 0 → +1 (probably same winners, different rounds)",
                 apply_narrow_vector,
                 expected_catch_axis="per-round fighter1_stats/fighter2_stats"),
]

# ── Runner ─────────────────────────────────────────────────────────

def main():
    # Sanity: baseline must be clean
    if not git_status_clean([_GB]):
        print(f"!!! game_bridge.py is not at HEAD — resolve before running", file=sys.stderr)
        p = subprocess.run(["git", "-C", _REPO, "diff", "--stat", _GB],
                           capture_output=True, text=True)
        print(p.stdout, file=sys.stderr)
        sys.exit(1)

    print("=" * 78)
    print("ORACLE-BRIDGE1 PERTURBATION SUITE")
    print("=" * 78)

    # Baseline: checker must PASS unperturbed
    print("\n[BASELINE] Running checker unperturbed...")
    rc, out = run_checker()
    if rc != 0:
        print(f"  ❌ BASELINE FAIL — checker returned {rc}")
        print(out[-500:])
        sys.exit(2)
    # Extract "matched: N/M" line
    m = re.search(r"matched: (\d+)/(\d+)", out)
    print(f"  ✓ baseline: {m.group(0) if m else 'unknown'}")

    results = []
    for pert in PERTURBATIONS:
        print(f"\n[{pert.name}] {pert.description}")
        try:
            pert.apply_fn()
            print(f"  perturbation applied")
        except Exception as e:
            print(f"  ⚠️  apply FAILED: {e}")
            results.append((pert.name, "APPLY_ERROR", str(e)))
            pert.revert_fn()
            continue

        try:
            rc, out = run_checker()
        finally:
            pert.revert_fn()
            if not git_status_clean([_GB]):
                print(f"  ⚠️  revert did not restore clean state!")

        if rc == 0:
            print(f"  ❌ MISS — checker still PASSED with perturbation in place")
            results.append((pert.name, "MISS", "no divergence"))
        else:
            # Extract first-diff path from the checker output
            m_path = re.search(r"at path:\s+(\S+)", out)
            m_exp  = re.search(r"expected:\s+(.+)", out)
            m_got  = re.search(r"got:\s+(.+)", out)
            m_fcnt = re.search(r"fight count differs:.+", out)
            if m_path:
                path = m_path.group(1)
                exp = (m_exp.group(1).strip() if m_exp else "?")[:60]
                got = (m_got.group(1).strip() if m_got else "?")[:60]
                print(f"  ✓ CAUGHT at {path}")
                print(f"    expected: {exp}")
                print(f"    got:      {got}")
                results.append((pert.name, "CAUGHT", f"{path} :: {exp} != {got}"))
            elif m_fcnt:
                # Different fight-count divergence (e.g., perturbation shifted
                # tick counts, changed injury rolls, etc.)
                print(f"  ✓ CAUGHT (count) {m_fcnt.group(0)}")
                results.append((pert.name, "CAUGHT", m_fcnt.group(0)))
            else:
                # Non-zero exit but no parseable divergence — likely crashed
                tail = "\n    ".join(out.strip().split("\n")[-8:])
                print(f"  ✓ CAUGHT (unparsed) — checker returned rc={rc}, tail:")
                print(f"    {tail}")
                results.append((pert.name, "CAUGHT", f"unparsed (rc={rc})"))

    # Summary
    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    caught = sum(1 for _, r, _ in results if r == "CAUGHT")
    n = len(results)
    for name, res, detail in results:
        marker = "✓" if res == "CAUGHT" else ("×" if res == "MISS" else "⚠️")
        print(f"  {marker} {name:<22s} → {res:<12s} {detail[:80]}")
    print()
    print(f"CATCH RATE: {caught}/{n}")

    # Final revert-sanity
    if not git_status_clean([_GB]):
        print("\n  ⚠️  WARNING: game_bridge.py is NOT clean at end of run")
        subprocess.run(["git", "-C", _REPO, "checkout", "HEAD", "--", _GB], check=True)
        print("  reset via checkout HEAD --")

    sys.exit(0 if caught == n else 1)

if __name__ == "__main__":
    main()
