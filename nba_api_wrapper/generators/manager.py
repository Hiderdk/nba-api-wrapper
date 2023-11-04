import datetime

import logging

import pandas as pd

from nba_api_wrapper.data_models import LGFDataNames
from nba_api_wrapper.dataclass import Game
from nba_api_wrapper.generators.api_bridge import ApiBridge

print(pd.__version__)

logging.basicConfig(
    level=logging.INFO
)


class IncorrectTeamCount(Exception):
    pass


class NBAData:

    def __init__(self,
                 api_facade: ApiBridge,
                 verbose: bool = True
                 ):
        self.api_bridge = api_facade
        self.verbose = verbose

    def generate_nba_data_by_date_period(self, min_date: datetime.date, max_date: datetime.date) -> list[Game]:

        games = []

        league_games= self.api_bridge.generate_league_games(min_date=min_date, max_date=max_date)
        game_ids = league_games[LGFDataNames.GAME_ID].unique().tolist()

        for game_id in game_ids:

            game = self.api_bridge.generate_boxscore(league_games=league_games, game_id=game_id)

            if len(game.teams) != 2:
                logging.warning(f"incorrect team count for gameid {game_id} - continuing")
                continue

            games.append(game)

            if self.verbose:
                logging.info(f"added gameId {game.id}")

        return games
