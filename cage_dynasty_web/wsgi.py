import sys
import os

project_home = '/home/vandopegaming/cage_dynasty/cage_dynasty_web'
# Add specific subdirs from game root — NOT the root itself
# (adding root would expose CLI fight_engine.py which shadows the web one)
systems_path  = '/home/vandopegaming/cage_dynasty/systems'
narrative_path = '/home/vandopegaming/cage_dynasty/narrative'
simulation_path = '/home/vandopegaming/cage_dynasty/simulation'

for path in [simulation_path, narrative_path, systems_path, project_home]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

from app import app as application
