# simulation shim package
#
# PREGEN-FULL-ENGINE-FIX1: shim `from simulation.fight_engine import ...`
# so it resolves under PA's sys.path.
#
# Background: wsgi.py adds /home/vandopegaming/cage_dynasty/simulation/ (contents)
# to sys.path so bare `import fight_engine` resolves. But
# `from simulation.fight_engine import ...` needs a `simulation` package
# discoverable — the parent dir (/cage_dynasty/) is deliberately NOT on
# sys.path (wsgi.py comment: adding it would shadow the web fight_engine.py
# with the CLI's older version).
#
# Under this failure, world_init.py:71-78 silently caught ImportError and
# set FULL_ENGINE_AVAILABLE=False. Pre-gen history sim then ran
# simulate_fight_simple — a clamped-probability fallback that caps favorite
# win rate at 74% regardless of ability gap. Empirical fingerprint on 1766
# pre-gen fights on the 2026-07-11 local save: 74.9% at 21+ OVR gap, matching
# the simple engine's saturation math to within noise.
#
# Fix: sys.modules['simulation.fight_engine'] = the real fight_engine module.
# Bare `import fight_engine` resolves to cage_dynasty_web/fight_engine.py
# (the WEB engine — same one live-play uses via fight_integration.py), so
# after this shim pre-gen and live-play share one engine. Attribute-set
# alone is NOT enough — Python's import machinery consults sys.modules by
# dotted name, so the sys.modules registration is the load-bearing line.
#
# Failure is LOUD. Same discipline as INJURY-IMPORT-FIX1: silent swallow
# is the recurring villain of this project. If this shim breaks, every
# fresh save reverts to coin-flip pre-gen with no announcement — do not
# lose the signal.
import sys as _sys
try:
    import importlib as _il
    _real_fe = _il.import_module("fight_engine")
    _sys.modules["simulation.fight_engine"] = _real_fe
    fight_engine = _real_fe  # attribute for direct `simulation.fight_engine` refs
    print("✅ [SIMULATION-SHIM] simulation.fight_engine shimmed from bare "
          "fight_engine module (web engine — same as live-play)",
          file=_sys.stderr)
except Exception as _e:
    # Widened from ImportError so syntax errors, module-level raises, or any
    # other failure mode surfaces loudly instead of silently disabling pre-gen.
    print("🚨 [SIMULATION-SHIM] FAILED to shim simulation.fight_engine from bare "
          f"'fight_engine' module: {type(_e).__name__}: {_e}", file=_sys.stderr)
    print("🚨 [SIMULATION-SHIM] world_init.FULL_ENGINE_AVAILABLE will be False.",
          file=_sys.stderr)
    print("🚨 [SIMULATION-SHIM] Pre-gen history sim will fall back to the crude",
          file=_sys.stderr)
    print("🚨 [SIMULATION-SHIM] simulate_fight_simple which caps favorite win rate",
          file=_sys.stderr)
    print("🚨 [SIMULATION-SHIM] at 74% regardless of OVR gap. Every fresh save's",
          file=_sys.stderr)
    print("🚨 [SIMULATION-SHIM] champions, belt lineages, and fight records will",
          file=_sys.stderr)
    print("🚨 [SIMULATION-SHIM] be near-random. Check sys.path — bare",
          file=_sys.stderr)
    print("🚨 [SIMULATION-SHIM] 'import fight_engine' should resolve to",
          file=_sys.stderr)
    print("🚨 [SIMULATION-SHIM] cage_dynasty_web/fight_engine.py.",
          file=_sys.stderr)
