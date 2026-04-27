"""
systems.game_start stub — re-exports from flat game_start.py.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from game_start import (
    generate_starting_coaches,
    generate_starting_prospects,
)

__all__ = ['generate_starting_coaches', 'generate_starting_prospects']
