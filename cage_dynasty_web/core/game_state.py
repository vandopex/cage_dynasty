"""
Re-exports from the flat game_state.py module.
Allows `from core.game_state import ...` to work without CLI directory structure.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from game_state import (
    DivisionState,    GameState,
    GamePhase,
    FighterRecord,
    CampRecord,
    get_game_state,
    reset_game_state,
)

__all__ = [
    'GameState', 'GamePhase', 'FighterRecord', 'CampRecord',
]
