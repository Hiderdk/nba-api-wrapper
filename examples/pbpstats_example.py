from typing import Any

import pandas as pd
from pbpstats.client import Client
from pbpstats.data_loader import DataNbaEnhancedPbpLoader, DataNbaEnhancedPbpWebLoader

from nba_api_wrapper.api.api_throttle import APIThrottle
from nba_api_wrapper.api.decorators import retry_on_error
from nba_api_wrapper.api.pbp_api_wrapper import PlayByPlayNbaApi
from nba_api_wrapper.data_models import PosessionModel
from nba_api_wrapper.generators.generator import GameStorer
from nba_api_wrapper.storer.file_storer import FileStorer


def main():


    # pbp_loader = DataNbaEnhancedPbpLoader("0021900001", source_loader)
    api = PlayByPlayNbaApi()

    game_storer = GameStorer(api=api, newest_games_only=True, store_frequency=10, storer=FileStorer(base_path="data"))
    game_storer.generate(league="nba", season="2020-21", season_type="Regular Season")


if __name__ == '__main__':
    main()
