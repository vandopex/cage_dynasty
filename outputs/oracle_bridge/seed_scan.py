"""Seed-scan: find a seed producing ≥2 title fights AND ≥1 injury in 12wk.

Van's non-negotiable coverage: title fights are 5-round on a different
config path; a gate that's never seen one can't protect one.

Also reports how many player-tier fights land — the PLAYER tier is
seed-independent (hand-booked) so player counts should stay stable.
"""
import _common  # noqa: F401 — sys.path setup + initial uuid patch
import io
import os
import random
import subprocess
import sys
import json

_HERE = os.path.dirname(os.path.abspath(__file__))

def run_one_seed(seed):
    """Run a subprocess-fresh fixture generator with the given seed, return summary."""
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["HOME"] = "/tmp"
    env["ORACLE_BRIDGE_SEED"] = str(seed)
    # We'll write a small runner that overrides SEED and dumps summary
    _here_abs = os.path.abspath(_HERE)
    script = f"""
import sys, os
os.environ['ORACLE_BRIDGE_SEED_OVERRIDE'] = '{seed}'
sys.path.insert(0, {_here_abs!r})
import _common as c
if {_here_abs!r} not in sys.path:
    sys.path.insert(0, {_here_abs!r})
c.SEED = {seed}
import random, uuid
c._uuid_rng = random.Random({seed})
def _seeded_uuid4():
    return uuid.UUID(int=c._uuid_rng.getrandbits(128))
uuid.uuid4 = _seeded_uuid4
random.seed({seed})

# Instead of using fixture_generator (which counts kwargs only —
# Path A doesn't pass is_title_fight as a kwarg), run the game directly
# and inspect _completed_events which HAS is_title_fight from the
# fight-dict source of truth.
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    from game_bridge import GameBridge
    bridge = GameBridge()
    bridge._user_id = 'seed_probe'
    ok = bridge.new_game(camp_name='P', camp_location='LV',
                         camp_tier='GARAGE', coach_data={{}}, fighter_data={{}})
    for _ in range(12):
        bridge.advance_week()

title_count = 0
injury_count = 0  # From news_items category='injury'
total_fights = 0
events = bridge._completed_events
for ev in events:
    for f in ev.get('fights', []):
        total_fights += 1
        if f.get('is_title_fight'):
            title_count += 1
# Injuries: count news_items with category='injury' created during the 12wk run
if hasattr(bridge, '_news_items'):
    for n in bridge._news_items:
        if n.get('category') == 'injury':
            injury_count += 1

import json
print(json.dumps({{'seed': {seed}, 'events': len(events),
                  'total_fights': total_fights,
                  'title_count': title_count, 'injury_count': injury_count}}))
"""
    p = subprocess.run([sys.executable, "-c", script], env=env,
                       capture_output=True, text=True, timeout=180)
    # Find JSON line in stdout
    for line in p.stdout.split("\n"):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass
    return {'seed': seed, 'error': 'no_json', 'tail': p.stdout[-300:]}

def main():
    seeds_to_try = [42, 100, 200, 300, 1000, 1001, 1002, 1003, 1004,
                    1005, 1006, 1007, 1008, 1009, 2000, 3000, 4242, 8675309]
    print(f"{'seed':>8} {'events':>7} {'fights':>7} {'titles':>7} {'injuries':>9}  target?")
    print("-" * 60)
    winners = []
    for s in seeds_to_try:
        r = run_one_seed(s)
        if 'error' in r:
            print(f"  {s:>6}  ERROR: {r['error']}")
            continue
        hit = "✓ YES" if (r['title_count'] >= 2 and r['injury_count'] >= 1) else ""
        print(f"  {r['seed']:>6}  {r['events']:>5}  {r['total_fights']:>5}  {r['title_count']:>5}  {r['injury_count']:>7}   {hit}")
        if r['title_count'] >= 2 and r['injury_count'] >= 1:
            winners.append(r)

    print()
    if winners:
        best = winners[0]
        print(f"✓ First seed matching ≥2 titles AND ≥1 injury: {best['seed']}")
        print(f"   titles: {best['title_count']}, injuries: {best['injury_count']}, total: {best['total_fights']}")
    else:
        print("× no seed in the tried set landed ≥2 titles + ≥1 injury in 12 weeks.")
        print("  Van's spec: 'If no seed delivers both in 12 weeks, extend the window")
        print("  or hand-book them in the PLAYER tier.'")

if __name__ == "__main__":
    main()
