"""FightConfig OBSERVE reference harness.

Constitutional role (CLAUDE.md standing rule, C46 SAVELOAD1
2026-09-06 → committed as tracked artifact at C47):
    Config verifies OBSERVE (wrap-log with caller attribution);
    never IMPOSE (mutate).

This file is the REFERENCE OBSERVE SHAPE cited by that standing
rule. Any future verify that touches FightConfig construction
must OBSERVE, not IMPOSE. Copy this file's pattern, not P3
prod verify's pattern.

Mechanism: wrap FightConfig.__init__ in an observer that (1)
calls the original constructor unchanged, then (2) logs the
resulting (exchanges, damage_multiplier, standup_threshold)
triple plus the nearest caller-frame identity. Zero mutation.

Origin: SAVELOAD1 T5 (2026-09-06) — the spot-check that
uncovered the C45 completeness gap (95.1% of production
FightConfig constructions still landed on the pre-C45
LEGACY_C45 triple through a single drift-pin at
game_bridge.py:17510). Full detail in CLAUDE.md's C46 filing
block. The T5 spot-check that ran was this file's shape.

Original working copy: outputs/sm1/saveload1/t5_bridge_spotcheck.py
(untracked, matches CLAUDE.md's outputs/ convention). This
committed copy is the canonical reference the standing rule
cites. Body is verbatim from the working copy EXCEPT three
changes, all so the harness runs without hand-patching on any
deploy target:
  (a) this docstring block;
  (b) sys.path setup — derived from __file__ (the working copy
      hardcoded absolute dev-machine paths);
  (c) OUT output-path derivation — derived from __file__ (the
      working copy hardcoded an absolute dev-machine path).
Classic `diff` reports 5 change-blocks (`diff -u` reports 2
hunks — adjacent blocks merged). All 5 documented in this
docstring; the tracked copy is otherwise byte-verbatim.

Run:
  PYTHONPATH="<repo>/narrative:<repo>/systems:<repo>/cage_dynasty_web" \\
      python3 -u <repo>/claude/tools/config_observe_harness.py
where <repo> is the absolute path to the Cage Dynasty repo root
(on dev machine, that is /Users/vandope/Desktop/Games/cage_dynasty;
on PA it is /home/vandopegaming/cage_dynasty). The PYTHONPATH
shape mirrors CLAUDE.md's C40 LOCAL PLAYTEST COMMAND section —
without it, world_init falls back to simulate_fight_simple and
the observation is worthless. Output lands under
<repo>/outputs/sm1/saveload1/t5_spotcheck_out.json.
"""
import os, sys, random, json
from collections import Counter

# Repo-relative sys.path setup (C47 fix). __file__ =
# <repo>/claude/tools/config_observe_harness.py; walk up 3 levels
# to <repo>, then add the three subdirs CLAUDE.md's C40 LOCAL
# PLAYTEST COMMAND names as load-bearing. Runs unchanged on dev
# / PA / any deploy target. Docstring's `Run:` line still lists
# PYTHONPATH explicitly because uWSGI-style deploys should set
# it there; this block is a belt-and-suspenders hedge for
# direct-invocation contexts.
_REPO_FOR_SYSPATH = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for p in (os.path.join(_REPO_FOR_SYSPATH, "narrative"),
          os.path.join(_REPO_FOR_SYSPATH, "systems"),
          os.path.join(_REPO_FOR_SYSPATH, "cage_dynasty_web")):
    if p not in sys.path: sys.path.insert(0, p)

import game_bridge as gb
fe = sys.modules['fight_engine']
fi = sys.modules['fight_integration']

# OBSERVATION probe — wrap FightConfig.__init__, DO NOT mutate.
# Van (C46): record the caller — walk the stack, find the nearest
# game_bridge / fight_integration / world_init frame, log its
# function name. Attribution reveals which path constructs which
# triple.
_observations = []
_orig_init = fe.FightConfig.__init__
def _caller_attrib():
    """Walk the stack (skip our wrapper + FightConfig.__init__),
    return the nearest gb/fi/world_init frame identity."""
    import sys as _s
    try:
        f = _s._getframe(2)  # skip _observe_init + FightConfig.__init__
        for _ in range(30):
            if f is None:
                return "<unknown>"
            code = f.f_code
            fn = code.co_filename
            if ('game_bridge.py' in fn or 'fight_integration.py' in fn
                    or 'world_init.py' in fn or 'fight_engine.py' in fn):
                base = fn.rsplit('/', 1)[-1]
                return f"{base}:{code.co_firstlineno}:{code.co_name}"
            f = f.f_back
    except Exception:
        pass
    return "<unknown>"

def _observe_init(self, *args, **kwargs):
    _orig_init(self, *args, **kwargs)
    _observations.append({
        'exchanges': self.exchanges_per_round,
        'dm': self.damage_multiplier,
        'standup': self.standup_threshold,
        'rounds': self.scheduled_rounds,
        'is_title_fight': getattr(self, 'is_title_fight', False),
        'is_main_event': getattr(self, 'is_main_event', False),
        'caller': _caller_attrib(),
    })
fe.FightConfig.__init__ = _observe_init

random.seed(6500000)
bridge = gb.GameBridge()
bridge.new_game(camp_name="T5V", camp_location="X", camp_tier="LOCAL",
    coach_data={"boxing_coach":"None"},
    fighter_data={"id":"t5v_probe","name":"P","weight_class":"Lightweight",
                  "age":24,"country":"United States","stance":"Orthodox",
                  "style":"Balanced","overall":65})

N_WEEKS = 20   # target ≥100 emitted fights per Van addendum
event_fights = 0
import io, contextlib
_null = io.StringIO()
for wk in range(N_WEEKS):
    try:
        # Suppress bridge card-narration prints (Van: count from
        # wrapper record, not log; narration was drowning stdout)
        with contextlib.redirect_stdout(_null):
            bridge.advance_week()
        print(f"  wk{wk+1}: advance OK  (running total obs={len(_observations)})", flush=True)
    except Exception as e:
        print(f"  wk{wk+1}: advance failed: {type(e).__name__}: {str(e)[:120]}", flush=True)

# Count fights emitted by advance_week + method share
_events = getattr(bridge, '_completed_events', [])
_method_ct = Counter()
def _bucket_m(m):
    mu = (m or '').upper()
    if mu == 'DRAW' or 'DRAW' in mu: return 'DRAW'
    if mu == 'SUB' or 'SUBMISSION' in mu: return 'SUB'
    if mu.startswith('KO') and 'TKO' not in mu: return 'KO'
    if 'TKO' in mu or 'STOPPAGE' in mu: return 'TKO'
    if mu == 'DEC' or 'DEC' in mu or 'DECISION' in mu: return 'DEC'
    return 'OTHER'
for evt in _events:
    for f in evt.get('fights', []):
        event_fights += 1
        _method_ct[_bucket_m(f.get('method'))] += 1

print(f"\n{'='*70}")
print(f"T5 BRIDGE OBSERVATION SPOT-CHECK")
print(f"{'='*70}")
print(f"new_game + {N_WEEKS} advance_week; fights emitted: {event_fights}")
print(f"Total FightConfig constructions observed: {len(_observations)}")

# Split by triple observed
_triple_ct = Counter()
for o in _observations:
    _triple_ct[(o['exchanges'], o['dm'], o['standup'])] += 1

print(f"\nTriple distribution across ALL observed FightConfigs:")
for triple, ct in _triple_ct.most_common():
    pct = ct/len(_observations)*100 if _observations else 0
    marker = ""
    if triple == (55, 0.24, 10):
        marker = " ★ LIVE_PLAY (C45)"
    elif triple == (55, 0.42, 6):
        marker = " (PRE_GEN_LEGACY)"
    elif triple == (55, 0.48, 6):
        marker = " (FI_FALLBACK)"
    elif triple == (55, 0.48, 10):
        marker = " ✗ LEGACY_C45 (should be zero post-C46!)"
    print(f"  {triple}: {ct} times ({pct:.1f}%){marker}")

# Van's ask: triple × caller table.
print(f"\nTRIPLE × CALLER table (obs count per pair):")
_by_caller = Counter()
for o in _observations:
    _by_caller[
        ((o['exchanges'], o['dm'], o['standup']), o['caller'])
    ] += 1
print(f"  {'triple':<20}  {'caller':<50}  count")
print(f"  {'-'*20}  {'-'*50}  {'-'*5}")
for (triple, caller), ct in _by_caller.most_common(25):
    print(f"  {str(triple):<20}  {caller:<50}  {ct}")

# Van's spec: every constructed config should read dm=0.24 (LIVE_PLAY).
# Pre-gen constructions inside world_init are exempt — they're
# deliberately pinned to PRE_GEN_LEGACY (0.42). Same for other classmethod
# uses that emit PRE_GEN_LEGACY.
live_play_ct = sum(1 for o in _observations
                     if (o['exchanges'], o['dm'], o['standup']) == (55, 0.24, 10))
pre_gen_ct = sum(1 for o in _observations
                    if (o['exchanges'], o['dm'], o['standup']) == (55, 0.42, 6))
fi_fallback_ct = sum(1 for o in _observations
                       if (o['exchanges'], o['dm'], o['standup']) == (55, 0.48, 6))
legacy_c45_ct = sum(1 for o in _observations
                      if (o['exchanges'], o['dm'], o['standup']) == (55, 0.48, 10))

print(f"\n{'='*70}\nVERDICT")
print(f"{'='*70}")
if event_fights >= 100:
    print(f"  Fight-count target (N≥100): ★ met ({event_fights})")
elif event_fights >= 20:
    print(f"  Fight-count sample: {event_fights} (below Van's ≥100; "
          f"noise widens but directional check stands)")
else:
    print(f"  Fight-count sample TOO LOW: {event_fights}")

if legacy_c45_ct == 0:
    print(f"  LEGACY_C45 constructions: ★ 0 (as required post-C46)")
else:
    print(f"  LEGACY_C45 constructions: ✗ {legacy_c45_ct} still fire")

# On the LIVE_PLAY-critical axis: report share of LIVE_PLAY-triple
# constructions among live-play consumers (exclude PRE_GEN which is
# deliberately different).
non_pregen = len(_observations) - pre_gen_ct
if non_pregen > 0:
    live_share = live_play_ct / non_pregen * 100
    print(f"  LIVE_PLAY share among non-pre-gen constructions: "
          f"{live_share:.1f}% ({live_play_ct}/{non_pregen})")

# First bridge-path finish-rate read (Van: label; not a gate).
print(f"\nFIRST BRIDGE-PATH FINISH-RATE READ, N={event_fights}, "
      f"NOT A GATE (Van C46 spec)")
if event_fights:
    for b in ('KO', 'TKO', 'SUB', 'DEC', 'DRAW', 'OTHER'):
        ct = _method_ct.get(b, 0)
        pct = ct/event_fights*100 if event_fights else 0
        print(f"  {b:<8} {ct:>5} ({pct:>5.1f}%)")

# Repo-relative output path (C47 fix). __file__ resolves to
# <repo>/claude/tools/config_observe_harness.py, so <repo> is
# two levels up. Runs unchanged on dev / PA / any deploy target.
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_OUT_DIR = os.path.join(_REPO, "outputs", "sm1", "saveload1")
os.makedirs(_OUT_DIR, exist_ok=True)
OUT = os.path.join(_OUT_DIR, "t5_spotcheck_out.json")
_out_by_caller = {}
for (triple, caller), ct in _by_caller.most_common():
    _out_by_caller[f"{triple}|{caller}"] = ct
with open(OUT, 'w') as f:
    json.dump({
        'head_head_note': ('captured under whatever tree runs this — '
                            'label PRE-FIX or POST-FIX in report'),
        'total_observations': len(_observations),
        'event_fights': event_fights,
        'triple_distribution': {
            f"{t[0]},{t[1]},{t[2]}": ct
            for t, ct in _triple_ct.most_common()},
        'triple_x_caller': _out_by_caller,
        'method_shares_bridge_fights': dict(_method_ct),
        'live_play_ct': live_play_ct,
        'pre_gen_ct': pre_gen_ct,
        'fi_fallback_ct': fi_fallback_ct,
        'legacy_c45_ct': legacy_c45_ct,
    }, f, indent=2)
print(f"\nBanked to {OUT}")
