"""
Cage Dynasty - MMA Management Simulation
Flask Web Application Entry Point
"""

import os as _os
import shutil as _shutil
import sys as _sys

from flask import Flask
from routes import register_routes
from game_bridge import get_bridge, GameBridge


# MULTIUSER-ISOLATION1: legacy save prefix used to bind Van's existing
# pre-multiuser saves to his session identity when he first visits the
# post-migration deployment.
LEGACY_USER_ID = "van"


def _migrate_legacy_saves(saves_dir: str) -> None:
    """One-time migration: rename any un-namespaced `bridge_*.json`
    saves to `bridge_{LEGACY_USER_ID}_*.json` and drop a `.bak`
    alongside each original before renaming.

    Idempotent: if there are no un-namespaced files (fresh deploy or
    already-migrated), does nothing. Never overwrites an existing
    namespaced file — logs and skips if a collision would occur.
    """
    if not _os.path.isdir(saves_dir):
        return
    try:
        files = _os.listdir(saves_dir)
    except OSError:
        return
    # An un-namespaced save looks like `bridge_slot1.json`,
    # `bridge_slot5.json`, `bridge_autosave.json`, etc. A namespaced
    # one looks like `bridge_van_slot1.json` — distinguished by the
    # presence of a second underscore before the trailing `.json`.
    _SLOT_TOKENS = ("slot1", "slot2", "slot3", "slot4", "slot5", "autosave")
    for fn in files:
        if not fn.startswith("bridge_") or not fn.endswith(".json"):
            continue
        stem = fn[len("bridge_"):-len(".json")]  # e.g. "slot5" or "van_slot5"
        # If stem's leading token is one of the raw slot tokens
        # (no user prefix), migrate it.
        if stem in _SLOT_TOKENS:
            src = _os.path.join(saves_dir, fn)
            dst = _os.path.join(
                saves_dir, f"bridge_{LEGACY_USER_ID}_{stem}.json")
            if _os.path.exists(dst):
                print(f"⚠️  [MULTIUSER MIGRATION] Skipping {fn}: "
                      f"target {_os.path.basename(dst)} already exists")
                continue
            bak = src + ".bak"
            try:
                if not _os.path.exists(bak):
                    _shutil.copy2(src, bak)
                _os.rename(src, dst)
                print(f"✅ [MULTIUSER MIGRATION] {fn} → "
                      f"{_os.path.basename(dst)} (backup: {_os.path.basename(bak)})")
            except OSError as e:
                print(f"⚠️  [MULTIUSER MIGRATION] {fn} failed: {e}")


def create_app():
    """Application factory pattern for Flask app creation."""
    _here = _os.path.dirname(_os.path.abspath(__file__))
    app = Flask(__name__,
        template_folder=_os.path.join(_here, 'templates'),
        static_folder=_os.path.join(_here, 'static'))

    # Configuration — env-var overrides for production deployment.
    # SECRET_KEY MUST be set in the environment for session cookies
    # to be unforgeable. The dev fallback is the well-known default
    # committed to git — anyone reading the codebase could sign
    # cookies claiming any user_id, so this is a security warning.
    _key = _os.environ.get('SECRET_KEY')
    if not _key:
        print("⚠️  ⚠️  ⚠️  SECURITY WARNING  ⚠️  ⚠️  ⚠️",
              file=_sys.stderr)
        print("   SECRET_KEY env var is unset — falling back to "
              "the public 'dev-only-fallback-change-in-prod' value.",
              file=_sys.stderr)
        print("   Session cookies signed with this key are FORGEABLE "
              "by anyone who reads the source.",
              file=_sys.stderr)
        print("   Set SECRET_KEY on PA before exposing multiuser to "
              "the internet.", file=_sys.stderr)
        _key = 'dev-only-fallback-change-in-prod'
    app.config['SECRET_KEY'] = _key
    app.config['DEBUG'] = (
        _os.environ.get('FLASK_DEBUG', '').lower() == 'true')

    # MULTIUSER-ISOLATION1: run legacy save migration BEFORE any
    # requests can hit us. Van's existing bridge_slot*.json files
    # get renamed to bridge_van_slot*.json so his first visit (which
    # the legacy-claim logic maps to user_id='van') resolves to them.
    _saves_dir = _os.path.join(_here, 'saves')
    _migrate_legacy_saves(_saves_dir)

    # MULTIUSER-ISOLATION1: per-session bridge dict. Bridges are
    # created lazily by routes.get_bridge() on first request that
    # matches a given user_id.
    app.game_bridges: dict = {}

    # Register all routes
    register_routes(app)

    return app


# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(
        debug=_os.environ.get('FLASK_DEBUG', '').lower() == 'true',
        host='0.0.0.0',
        port=5001,
    )
