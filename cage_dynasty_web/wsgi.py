import sys

game_root    = '/home/vandopegaming/cage_dynasty'
project_home = '/home/vandopegaming/cage_dynasty/cage_dynasty_web'

# project_home MUST come before game_root so web app modules
# shadow CLI modules with the same name (fight_engine, game_state etc.)
if game_root not in sys.path:
    sys.path.append(game_root)
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application
