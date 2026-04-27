"""
Fighter entity stub — web layer uses FighterRecord from game_state.py.
This module exists so `from entities.fighter import Fighter` doesn't crash.
"""
from game_state import FighterRecord as Fighter

__all__ = ['Fighter']
