import os

import pandas as pd

from nba_api_wrapper.data_models import LineupNames, GameModel, GamePlayerModel, GameTeamModel, PosessionModel
from nba_api_wrapper.datastructures import CollectedData

from nba_api_wrapper.storer.base_storer import Storer


class FileStorer(Storer):

    def __init__(self, base_path: str = "", pickle: bool = True):
        self.base_path = base_path
        self.pickle = pickle

    def store(self, collected_data: CollectedData):

        if os.path.exists(os.path.join(self.base_path, "game.pickle")):
            games = pd.read_pickle(os.path.join(self.base_path, "game.pickle"))
            if collected_data.game is not None:
                games = pd.concat([games, collected_data.game])
                games = games.drop_duplicates(subset=GameModel.GAME_ID, keep='last')
        else:
            games = collected_data.game

        if os.path.exists(os.path.join(self.base_path, "game_player.pickle")):
            game_players = pd.read_pickle(os.path.join(self.base_path, "game_player.pickle"))
            if collected_data.game_players is not None:
                game_players = pd.concat([game_players, collected_data.game_players])
                game_players = game_players.drop_duplicates(subset=[GamePlayerModel.GAME_ID, GamePlayerModel.PLAYER_ID],
                                                            keep='last')
        else:
            game_players = collected_data.game_players

        if os.path.exists(os.path.join(self.base_path, "game_team.pickle")):
            game_teams = pd.read_pickle(os.path.join(self.base_path, "game_team.pickle"))
            if collected_data.game_teams is not None:
                game_teams = pd.concat([game_teams, collected_data.game_teams])
                game_teams = game_teams.drop_duplicates(subset=[GameTeamModel.GAME_ID, GameTeamModel.TEAM_ID],
                                                        keep='last')
        else:
            game_teams = collected_data.game_teams

        if os.path.exists(os.path.join(self.base_path, "possessions.pickle")):

            possessions = pd.read_pickle(os.path.join(self.base_path, "possessions.pickle"))
            if collected_data.possessions is not None:
                possessions = pd.concat([possessions, collected_data.possessions])
                count=len(possessions)
                possessions = possessions.drop_duplicates(
                    subset=[PosessionModel.GAME_ID, PosessionModel.START_TIME_SECONDS, PosessionModel.TEAM_ID_OFFENSE,
                            PosessionModel.PERIOD], keep='last')
                if len(possessions) != count:
                    print("Duplicates found in possessions")
        else:
            possessions = collected_data.possessions

        if possessions is not None:
            possessions.to_pickle(os.path.join(self.base_path, "possessions.pickle"))
        if game_players is not None:
            game_players.to_pickle(os.path.join(self.base_path, "game_player.pickle"))

        if game_teams is not None:
            game_teams.to_pickle(os.path.join(self.base_path, "game_team.pickle"))
        if games is not None:
            games.to_pickle(os.path.join(self.base_path, "game.pickle"))

    def load_lineups(self) -> pd.DataFrame:
        path = os.path.join(self.base_path, "lineups.pickle")
        if os.path.exists(path):
            lineups = pd.read_pickle(path)
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
