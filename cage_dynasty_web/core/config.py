# core/config.py — stub for web app
from typing import Any, Dict

_DEFAULT_CONFIG: Dict[str, Any] = {
    "fight_engine": {
        "stamina_drain_rate": 0.85,
        "ko_base_probability": 0.12,
        "sub_base_probability": 0.08,
        "min_rounds": 3,
        "max_rounds": 5,
    },
    "training": {
        "base_gain_rate": 1.0,
    },
    "economy": {
        "base_purse": 10000,
    },
}

def get_config(path: str = None, default: Any = None) -> Any:
    """Return config values. No-op stub for web app.

    Signature matches the top-level core/config.py: a dotted path and an
    optional default returned when the path does not resolve.
    """
    if path is None:
        return _DEFAULT_CONFIG
    parts = path.split(".")
    val: Any = _DEFAULT_CONFIG
    for p in parts:
        if isinstance(val, dict) and p in val:
            val = val[p]
        else:
            return default
    return val
