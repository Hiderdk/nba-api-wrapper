import os

import pandas as pd

from nba_api_wrapper.data_models import LineupNames
from nba_api_wrapper.datastructures import CollectedData

from nba_api_wrapper.storer.base_storer import Storer


class FileStorer(Storer):

    def __init__(self, base_path: str = "", pickle: bool = True):
        self.base_path = base_path
        self.pickle = pickle


    def store(self, collected_data: CollectedData):

        if os.path.exists(os.path.join(self.base_path, "game.pickle")):
            games = pd.read_pickle(os.path.join(self.base_path, "game.pickle"))
            games = pd.concat([games, collected_data.game])
            games = games.drop_duplicates()
        else:
            games = collected_data.game

        if os.path.exists(os.path.join(self.base_path, "game_player.pickle")):
            game_players = pd.read_pickle(os.path.join(self.base_path, "game_player.pickle"))
            game_players = pd.concat([game_players, collected_data.game_players])
            game_players = game_players.drop_duplicates(keep='last')
        else:
            game_players = collected_data.game_players

        if os.path.exists(os.path.join(self.base_path, "game_team.pickle")):
            game_teams = pd.read_pickle(os.path.join(self.base_path, "game_team.pickle"))
            game_teams = pd.concat([game_teams, collected_data.game_teams])
            game_teams = game_teams.drop_duplicates(keep='last')
        else:
            game_teams = collected_data.game_teams


        if os.path.exists(os.path.join(self.base_path, "possessions.pickle")):

            possessions = pd.read_pickle(os.path.join(self.base_path, "possessions.pickle"))
            possessions = pd.concat([possessions, collected_data.possessions])
            possessions = possessions.drop_duplicates(keep='last')
        else:
            possessions = collected_data.possessions

        possessions.to_pickle(os.path.join(self.base_path, "possessions.pickle"))
        game_players.to_pickle(os.path.join(self.base_path, "game_player.pickle"))
        game_teams.to_pickle(os.path.join(self.base_path, "game_team.pickle"))
        games.to_pickle(os.path.join(self.base_path, "game.pickle"))


    def load_lineups(self) -> pd.DataFrame:
        path = os.path.join(self.base_path, "lineups.pickle")
        if os.path.exists(path):
            lineups =  pd.read_pickle(path)
            lineups[LineupNames.LINEUP] = lineups[LineupNames.LINEUP].apply(lambda x: tuple(x))
            return lineups
        else:
            return pd.DataFrame(
                {
                    LineupNames.LINEUP_ID: [],
                    LineupNames.LINEUP: [],
                })


    def load_games(self) -> pd.DataFrame:
        path = os.path.join(self.base_path, "game.pickle")
        if os.path.exists(path):
            return pd.read_pickle(path)
        else:
            return pd.DataFrame(
                {
                    LineupNames.LINEUP_ID: [],
                    LineupNames.LINEUP: [],
                })
