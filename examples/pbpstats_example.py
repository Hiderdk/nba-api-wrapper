from typing import Any

import pandas as pd
from pbpstats.client import Client
from pbpstats.data_loader import DataNbaEnhancedPbpLoader, DataNbaEnhancedPbpWebLoader


from nba_api_wrapper.api.api_throttle import APIThrottle
from nba_api_wrapper.api.decorators import retry_on_error
from nba_api_wrapper.api.pbp_api_wrapper import PlayByPlayNbaApi
from nba_api_wrapper.data_models import PosessionModel
from nba_api_wrapper.generators.generator import GameStorer

api_throttle = APIThrottle(interval_seconds=60, max_calls_per_interval=4)

@api_throttle
@retry_on_error
def get_possession_df(game_id):

    client = Client(game_settings)

    game = client.Game(game_id)



def main():
    settings = {
        "Games": {"source": "web", "data_provider": "stats_nba"},
        "Boxscore": {"source": "web", "data_provider": "stats_nba"},
        "Possessions": {"source": "web", "data_provider": "stats_nba"},
    }
    source_loader = DataNbaEnhancedPbpWebLoader()

    #pbp_loader = DataNbaEnhancedPbpLoader("0021900001", source_loader)
    api = PlayByPlayNbaApi()

    game_storer = GameStorer(api=api, newest_games_only=False)
    game_storer.generate()




if __name__ == '__main__':
    main()