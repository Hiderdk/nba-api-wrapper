import datetime

from nba_api_wrapper.api.data_models import LGFDataNames
from nba_api_wrapper.generators.api_bridge import ApiBridge

bridge = ApiBridge()

league_games = bridge.generate_league_games(min_date=datetime.datetime(year=2023, month=10, day=22),
                             max_date=datetime.datetime(year=2023, month=10, day=25))
LFG = LGFDataNames
game_id = league_games[LFG.GAME_ID].iloc[0]
bridge.generate_play_by_play(game_id=game_id)
