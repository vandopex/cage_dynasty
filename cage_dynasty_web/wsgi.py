import sys
import os

game_root    = '/home/vandopegaming/cage_dynasty'
project_home = '/home/vandopegaming/cage_dynasty/cage_dynasty_web'

# project_home MUST come before game_root
if game_root not in sys.path:
    sys.path.append(game_root)
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Force web versions of modules that exist in both web and CLI
for mod in ['fight_engine', 'fight_integration', 'game_state']:
    if mod in sys.modules:
        del sys.modules[mod]

from app import app as application
