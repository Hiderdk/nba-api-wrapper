import os
from typing import Optional

import pandas as pd

from nba_api_wrapper.data_models import LineupNames
from nba_api_wrapper.datastructures import CollectedData

from nba_api_wrapper.storer.base_storer import Storer


class FileStorer(Storer):

    def __init__(self, base_path: str = "", pickle: bool = True, overwrite: bool = False):
        self.base_path = base_path
        self.pickle = pickle
        self.overwrite = overwrite


    def store(self, collected_data: CollectedData):
        game_players = pd.concat([game_players, collected_data.game_players])
        game_players = game_players.drop_duplicates()

        game_teams = pd.read_pickle("data/game_team.pickle")
        game_teams = pd.concat([game_teams, collected_data.game_teams])
        game_teams = game_teams.drop_duplicates()

        offense_player_play_by_plays = pd.read_pickle("data/offense_player_play_by_plays.pickle")
        offense_player_play_by_plays = pd.concat(
            [offense_player_play_by_plays, collected_data.offense_player_play_by_plays])
        offense_player_play_by_plays = offense_player_play_by_plays.drop_duplicates()

        defense_player_play_by_plays = pd.read_pickle("data/defense_player_play_by_plays.pickle")
        defense_player_play_by_plays = pd.concat(
            [defense_player_play_by_plays, collected_data.defense_player_play_by_plays])
        defense_player_play_by_plays = defense_player_play_by_plays.drop_duplicates()
        possessions = pd.concat([possessions, collected_data.possessions])
        possessions = possessions.drop_duplicates()

        possessions.to_pickle("data/possessions.pickle")
        game_players.to_pickle("data/game_player.pickle")
        game_teams.to_pickle("data/game_team.pickle")
        offense_player_play_by_plays.to_pickle("data/offense_player_play_by_plays.pickle")
        defense_player_play_by_plays.to_pickle("data/defense_player_play_by_plays.pickle")
        games.to_pickle("data/game.pickle")


    def load_lineups(self) -> pd.DataFrame:
        path = os.path.join(self.base_path, "lineups.pickle")
        if os.path.exists(path):
            lineups =  pd.read_pickle(path)
            lineups[LineupNames.LINEUP_ID] = lineups[LineupNames.LINEUP_ID].apply(lambda x: tuple(x))
        else:
            return pd.DataFrame(
                {
                    LineupNames.LINEUP_ID: [],
                    LineupNames.LINEUP: [],
                })

