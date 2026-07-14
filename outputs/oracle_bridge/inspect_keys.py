"""Dump commentary_all keys after fixture build."""
import _common  # noqa: F401
import io, contextlib, sys, os

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    from game_bridge import GameBridge
    bridge = GameBridge()
    bridge._user_id = "keydump"
    import fixture_generator as fg
    bridge.new_game(camp_name="P", camp_location="LV", camp_tier="GARAGE",
                    coach_data={}, fighter_data=fg.PLAYER_FIGHTER_DATA)
    player_fid = None
    for fid, f in bridge._game_state.fighters.items():
        if getattr(f, "camp_id", None) == bridge._game_state.player_camp_id:
            player_fid = fid; break
    for _ in range(12): bridge.advance_week()
    fg.run_player_tier(bridge, player_fid)

commentary = bridge._fight_commentary
print(f"Total commentary_all keys: {len(commentary)}")
print("First 8:")
for k in list(commentary.keys())[:8]:
    print(f"  {k}")
print("Last 8:")
for k in list(commentary.keys())[-8:]:
    print(f"  {k}")
