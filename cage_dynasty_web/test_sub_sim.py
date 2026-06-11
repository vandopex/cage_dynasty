"""
Submission attempt/finish rate matrix.

For each (attacker_sub, defender_sub+guard, position) cell, runs 200
submission attempts at full stamina/health. Tracks:
- Lock-in rate (attempts that get the sub on)
- Finish rate of locked attempts (process_submission_progress reaches finish)
- Overall finish rate (lock-in × finish-of-locked)

Plus a defense-profile test: same attacker at sub=75 vs four defender
shapes (high guard / high sub / balanced / elite) in BACK_MOUNT.

Highlights cells where overall finish > 50% (too easy) or < 5% (dead zone).
Flags suspicious upset cells (weak attacker / elite defender).
"""

import os
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from fight_engine import (
    FighterAttributes, FighterState, FightState, FightConfig,
    attempt_submission, process_submission_progress,
    SubmissionType, Position, SUBMISSION_PROPERTIES,
)


# Process-loop cap to avoid infinite loops in pathological cases.
# Once a sub is locked, normally finishes in 3-8 ticks; 20 is plenty.
MAX_PROGRESS_STEPS = 20

# Attempts per cell
ATTEMPTS = 200


# ─────────────────────────────────────────────────────────────────────────────
# Fighter builders — minimal, only the stats that submission math reads
# ─────────────────────────────────────────────────────────────────────────────

def make_attacker(sub_skill: int) -> FighterAttributes:
    return FighterAttributes(
        fighter_id="attacker",
        name="Attacker",
        # Sub math reads: submissions, stamina (via state), and danger/escape
        submissions=sub_skill,
        guard=60,  # mid — doesn't affect attacker math
        # Rest default to 50 / mid values
    )

def make_defender(guard: int, submissions: int, heart: int = 50) -> FighterAttributes:
    return FighterAttributes(
        fighter_id="defender",
        name="Defender",
        # Defense math reads: guard, submissions, heart, stamina
        guard=guard,
        submissions=submissions,
        heart=heart,
    )

def fresh_states():
    a = FighterState(fighter_id="attacker", name="Attacker",
                     stamina=100.0, health=100.0)
    d = FighterState(fighter_id="defender", name="Defender",
                     stamina=100.0, health=100.0)
    return a, d

def fresh_fight(position, attacker_state, defender_state):
    fs = FightState(fighter1=attacker_state, fighter2=defender_state)
    fs.position = position
    fs.top_fighter_id = "attacker"  # attacker has the sub
    return fs


# ─────────────────────────────────────────────────────────────────────────────
# Natural sub per position
# ─────────────────────────────────────────────────────────────────────────────

NATURAL_SUB = {
    Position.CLOSED_GUARD_BOTTOM: SubmissionType.TRIANGLE_CHOKE,
    Position.MOUNT:                SubmissionType.ARMBAR,
    Position.BACK_MOUNT:           SubmissionType.REAR_NAKED_CHOKE,
    Position.FULL_GUARD_BOTTOM:    SubmissionType.ARMBAR,
    Position.SIDE_CONTROL_TOP:     SubmissionType.ARM_TRIANGLE,
    Position.FIFTY_FIFTY:          SubmissionType.HEEL_HOOK,
}

POSITION_LABELS = {
    Position.CLOSED_GUARD_BOTTOM: "CLOSED_GUARD_BOT",
    Position.MOUNT:                "MOUNT",
    Position.BACK_MOUNT:           "BACK_MOUNT",
    Position.FULL_GUARD_BOTTOM:    "FULL_GUARD_BOT",
    Position.SIDE_CONTROL_TOP:     "SIDE_CONTROL",
    Position.FIFTY_FIFTY:          "FIFTY_FIFTY",
}


# ─────────────────────────────────────────────────────────────────────────────
# Single cell — runs ATTEMPTS attempts and returns (lock_rate, finish_of_locked, overall)
# ─────────────────────────────────────────────────────────────────────────────

def run_cell(attacker: FighterAttributes,
             defender: FighterAttributes,
             position: Position,
             sub_type: SubmissionType,
             attempts: int = ATTEMPTS):
    config = FightConfig.standard_fight()
    locks = 0
    finishes = 0
    for _ in range(attempts):
        a_state, d_state = fresh_states()
        fight_state = fresh_fight(position, a_state, d_state)

        locked_in, _finished_now, _progress = attempt_submission(
            attacker, defender, sub_type,
            a_state, d_state, fight_state,
        )
        if not locked_in:
            continue
        locks += 1
        # Loop process_submission_progress until finish or escape
        for _ in range(MAX_PROGRESS_STEPS):
            if not fight_state.submission_active:
                break
            escaped, finished = process_submission_progress(
                attacker, defender,
                a_state, d_state,
                fight_state, config,
            )
            if finished:
                finishes += 1
                break
            if escaped:
                break

    lock_rate     = 100.0 * locks / attempts if attempts else 0.0
    fin_of_locked = 100.0 * finishes / locks if locks else 0.0
    overall       = 100.0 * finishes / attempts if attempts else 0.0
    return lock_rate, fin_of_locked, overall


# ─────────────────────────────────────────────────────────────────────────────
# Pretty print helpers
# ─────────────────────────────────────────────────────────────────────────────

def fmt_overall(overall):
    """Return tag if overall outside healthy band."""
    if overall > 50.0:
        return f"{overall:5.1f}% [HIGH]"
    if overall < 5.0:
        return f"{overall:5.1f}% [LOW]"
    return f"{overall:5.1f}%"


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

ATTACKER_SUBS  = [45, 55, 65, 75, 85, 92]
DEFENDER_SKILL = [40, 55, 65, 75, 85]   # used for both guard and submissions
POSITIONS = [
    Position.CLOSED_GUARD_BOTTOM,
    Position.MOUNT,
    Position.BACK_MOUNT,
    Position.FULL_GUARD_BOTTOM,
    Position.SIDE_CONTROL_TOP,
    Position.FIFTY_FIFTY,
]


def main():
    suspicious = []

    print("=" * 78)
    print(f"SUB SIM MATRIX — {ATTEMPTS} attempts/cell, fresh stamina+health")
    print("Position | atkSub × defSkill (guard==sub)")
    print("=" * 78)

    for position in POSITIONS:
        sub_type = NATURAL_SUB[position]
        danger, escape_diff, _ = SUBMISSION_PROPERTIES[sub_type]
        print()
        print(f"── {POSITION_LABELS[position]}  ({sub_type.name}, "
              f"danger={danger}, escape={escape_diff}) ──")
        # Header row of defender skills
        header = f"{'atkSub':<8}" + "".join(f"{d:>14}" for d in DEFENDER_SKILL)
        print(header)
        print("-" * len(header))

        for atk_sub in ATTACKER_SUBS:
            attacker = make_attacker(atk_sub)
            row = f"{atk_sub:<8}"
            for def_skill in DEFENDER_SKILL:
                defender = make_defender(guard=def_skill, submissions=def_skill)
                lock_rate, fin_of_locked, overall = run_cell(
                    attacker, defender, position, sub_type
                )
                # Cell shows overall finish %
                cell = f"{overall:5.1f}%"
                if overall > 50.0:
                    cell = f"{overall:5.1f}*"  # HIGH marker
                elif overall < 5.0:
                    cell = f"{overall:5.1f}_"  # LOW marker
                row += f"{cell:>14}"

                # Suspicious upset: weak attacker overpowering elite defender
                if atk_sub <= 50 and def_skill >= 85 and overall > 10.0:
                    suspicious.append(
                        f"  {POSITION_LABELS[position]}: atk={atk_sub} "
                        f"vs def={def_skill} → overall {overall:.1f}% finish"
                    )
            print(row)

    print()
    print("  Legend: * = overall finish > 50% (too easy)  "
          "_ = overall finish < 5% (dead zone)")

    # ── Detail row — show lock vs finish-of-locked for one diagonal slice ───
    print()
    print("=" * 78)
    print("DETAIL — lock-in % | finish-of-locked % | overall %  "
          "(matched-skill diagonal)")
    print("=" * 78)
    print(f"{'position':<18}{'atkSub':>8}{'defSkill':>10}"
          f"{'lock%':>12}{'finLock%':>14}{'overall%':>14}")
    print("-" * 78)
    for position in POSITIONS:
        sub_type = NATURAL_SUB[position]
        for skill in [55, 65, 75, 85]:
            attacker = make_attacker(skill)
            defender = make_defender(guard=skill, submissions=skill)
            lock_rate, fin_of_locked, overall = run_cell(
                attacker, defender, position, sub_type
            )
            print(f"{POSITION_LABELS[position]:<18}"
                  f"{skill:>8}{skill:>10}"
                  f"{lock_rate:>11.1f}%"
                  f"{fin_of_locked:>13.1f}%"
                  f"{fmt_overall(overall):>14}")

    # ── Defense-profile test ────────────────────────────────────────────────
    print()
    print("=" * 78)
    print("DEFENSE PROFILE TEST — attacker sub=75 in BACK_MOUNT, "
          f"{ATTEMPTS} attempts/profile")
    print("=" * 78)
    print(f"{'profile':<32}{'lock%':>10}{'finLock%':>12}{'overall%':>14}")
    print("-" * 78)
    profiles = [
        ("High guard / low sub  (70G/40S)",  70, 40),
        ("High sub / low guard  (40G/70S)",  40, 70),
        ("Balanced              (60G/60S)",  60, 60),
        ("Elite defender        (80G/80S)",  80, 80),
    ]
    attacker = make_attacker(75)
    sub_type = NATURAL_SUB[Position.BACK_MOUNT]
    for label, g, s in profiles:
        defender = make_defender(guard=g, submissions=s)
        lock_rate, fin_of_locked, overall = run_cell(
            attacker, defender, Position.BACK_MOUNT, sub_type
        )
        print(f"{label:<32}{lock_rate:>9.1f}%{fin_of_locked:>11.1f}%"
              f"{fmt_overall(overall):>14}")

    # ── Flagged cells ───────────────────────────────────────────────────────
    print()
    print("=" * 78)
    print("FLAGGED — weak attacker vs elite defender producing > 10% finish")
    print("=" * 78)
    if suspicious:
        for s in suspicious:
            print(s)
    else:
        print("  None — defense scaling looks reasonable at the upset edge.")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
