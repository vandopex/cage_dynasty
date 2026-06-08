import sys

project_home = '/home/vandopegaming/cage_dynasty/cage_dynasty_web'
game_root = '/home/vandopegaming/cage_dynasty'

for path in [project_home, game_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

from app import app as application
