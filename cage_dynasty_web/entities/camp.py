"""
Camp entity stub — web layer uses CampRecord from game_state.py.
This module exists so `from entities.camp import Camp` doesn't crash.
"""
from game_state import CampRecord as Camp

__all__ = ['Camp']
