# systems stub package
#
# INJURY-IMPORT-FIX1: shim the real /systems/injury.py in as systems.injury.
#
# Background: wsgi.py adds /home/vandopegaming/cage_dynasty/systems/ (contents)
# to sys.path so `import injury` resolves to the real module. But this stub
# package under cage_dynasty_web/systems/ shadows the `systems` name, so
# `from systems.injury import ...` fails against this package's empty namespace.
#
# Fix: re-register the real injury module in sys.modules under the fully-
# qualified name systems.injury. Attribute-set alone (systems.injury = X) is
# NOT enough — Python's import machinery consults sys.modules by dotted name,
# so the sys.modules registration is the load-bearing line.
#
# Failure is LOUD. The previous silent-swallow (⚠️ one-line at Flask startup)
# is what let INJURY_AVAILABLE=False go unnoticed across many deploys. If this
# shim fails, downstream ~10 booking gates and the entire champion-injury arc
# stay dark; do not lose the signal.
import sys as _sys
try:
    import importlib as _il
    _real_injury = _il.import_module("injury")
    _sys.modules["systems.injury"] = _real_injury
    injury = _real_injury  # attribute for direct `systems.injury` refs
    print("✅ [SYSTEMS-SHIM] systems.injury shimmed from bare injury module",
          file=_sys.stderr)
except Exception as _e:
    # Widened from ImportError to catch syntax errors, module-level raises,
    # and any other failure mode that would leave the shim silently broken
    # — the exact class of hole this ship exists to close.
    print("🚨 [SYSTEMS-SHIM] FAILED to shim systems.injury from bare "
          f"'injury' module: {type(_e).__name__}: {_e}", file=_sys.stderr)
    print("🚨 [SYSTEMS-SHIM] INJURY_AVAILABLE will be False. All downstream:",
          file=_sys.stderr)
    print("🚨 [SYSTEMS-SHIM]   - booking gates (~10 is_cleared_to_fight sites)",
          file=_sys.stderr)
    print("🚨 [SYSTEMS-SHIM]   - champion-injury slices (auto-vacate, hold, defense delay)",
          file=_sys.stderr)
    print("🚨 [SYSTEMS-SHIM]   - post-fight injury rolls (game_bridge.py:13774, 18227)",
          file=_sys.stderr)
    print("🚨 [SYSTEMS-SHIM]   - injury news headlines",
          file=_sys.stderr)
    print("🚨 [SYSTEMS-SHIM] will be disabled. Check sys.path — need /systems/ "
          "contents on it (see wsgi.py).", file=_sys.stderr)
