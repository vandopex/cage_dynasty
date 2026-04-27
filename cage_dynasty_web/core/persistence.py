"""
Persistence stub — web layer uses game_bridge.web_save / web_load instead.
These functions are imported by game_bridge.py but the web save system
overrides them entirely.
"""
import json, os
from typing import Optional

SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saves')

def save_game(game_state, slot_name: str) -> bool:
    """Stub — web layer handles saves via web_save()."""
    return True

def load_game(slot_name: str):
    """Stub — web layer handles loads via web_load()."""
    return None

def list_saves():
    """Return available save slots."""
    os.makedirs(SAVES_DIR, exist_ok=True)
    saves = []
    for f in os.listdir(SAVES_DIR):
        if f.endswith('.json'):
            saves.append(f.replace('.json', ''))
    return saves
