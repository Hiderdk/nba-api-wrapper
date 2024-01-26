import datetime
import logging

from typing import Optional, Any

import numpy as np
import pandas as pd
import pendulum

from nba_api_wrapper.api._base import BaseApi
from nba_api_wrapper.data_models import PosessionNames, LGFDataNames, GameTeamModel, BoxscoreV2Names, RotationNames, \
    PlayByPlay2Model, GameModel
from nba_api_wrapper.datastructures import TransformedBoxscore, PlayByPlay, CollectedData
from nba_api_wrapper.generators.boxscore_generators import generate_game_team, generate_game_players, generate_game
from nba_api_wrapper.generators.play_by_play_generators import generate_defense_player_play_by_plays, \
    generate_offense_player_play_by_plays, generate_possession_from_attempts, generate_possession_attempts, \
    generate_inplay_lineups, generate_shot_plays
from nba_api_wrapper.storer.base_storer import Storer
from nba_api_wrapper.storer.file_storer import FileStorer

PN = PosessionNames

LFG = LGFDataNames

BOX = BoxscoreV2Names
LFG = LGFDataNames
RN = RotationNames
PBP = PlayByPlay2Model

logging.basicConfig(level=logging.INFO)


class GameStorer():
    def __init__(self,
                 api: BaseApi,
                 storer: Storer = FileStorer(),
                 store_frequency: int = 20,
                 newest_games_only: bool = False,
                 process_game: bool = True,
                 process_game_team: bool = True,
                 process_game_player: bool = True,
                 process_possession: bool = True,
                 ):

        self.store_frequency = store_frequency
        self.storer = storer
        self.api = api
        self.newest_games_only = newest_games_only
        self.process_game = process_game
        self.process_game_team = process_game_team
        self.process_game_player = process_game_player
        self.process_possession = process_possession

    def generate(self, min_date: Optional[pendulum.Date] = None, max_date: Optional[pendulum.Date] = None,
                 **season_data) -> None:

        if season_data is not None:
            game_ids = self.api.get_game_ids_by_season(season_data)


        else:
            if min_date is None:
                min_date = pendulum.now().subtract(days=5)
            logging.info(f"min_date not provided, using {min_date}")

            if max_date is None:
                max_date = pendulum.now()

            game_ids = self.api.get_game_ids_by_date_range(min_date=min_date, max_date=max_date)

        if self.newest_games_only:
            stored_games = self.storer.load_games()
            if len(stored_games) > 0:
                stored_game_ids = stored_games[GameModel.GAME_ID].unique().tolist()
            else:
                stored_game_ids = []
            to_process_game_ids = [game_id for game_id in game_ids if game_id not in stored_game_ids]
        else:
            to_process_game_ids = game_ids

        logging.info(f"Starting to store {len(to_process_game_ids)} games")

        while len(to_process_game_ids) > 0:
            to_store_game_ids = to_process_game_ids[:self.store_frequency]
            collected_data = self._generate_collected_data(game_ids=to_store_game_ids)
            self.storer.store(collected_data=collected_data)
            to_process_game_ids = to_process_game_ids[self.store_frequency:]
            logging.info(f"Finished storing, {len(to_process_game_ids)} games remaining")

    def _generate_collected_data(self, game_ids: list[int]) -> CollectedData:
        possessions = []
        game_players = []
        game_teams = []
        games = []
        for game_id in game_ids:
            print(f"processing gameid {game_id}")

            if self.process_game:
                try:
                    game_team = self.api.get_game_team_by_game_id(game_id)
                    game_teams.append(game_team)
                except Exception as e:
                    logging.warning(f"gameid {game_id} failed to get boxscore by gameid, error: {e}")
                    raise ValueError

            if self.process_game_player:
                try:
                    game_player = self.api.get_game_player_by_game_id(game_id)
                    game_players.append(game_player)
                except Exception as e:
                    logging.warning(f"gameid {game_id} failed to get boxscore by gameid, error: {e})")
                    raise ValueError

            if self.process_possession:
                try:
                    possession = self.api.get_possessions_by_game_id(game_id=game_id)
                    possessions.append(possession)
                except Exception as e:
                    logging.warning(f"gameid {game_id} failed to get possessions by gameid, error: {e}")

            if self.process_game:
                try:
                    game = self.api.get_game_by_game_id(game_id)
                    games.append(game)
                except Exception as e:
                    logging.warning(f"gameid {game_id} failed to get boxscore by gameid, error: {e})")
                    raise ValueError

        return CollectedData(
            possessions=pd.concat(possessions) if possessions else None,
            game_teams=pd.concat(game_teams) if game_teams else None,
            game_players=pd.concat(game_players) if game_players else None,
            game=pd.concat(games) if games else None,
        )

    def _generated_transformed_boxscore(
            self,
            league_games: pd.DataFrame,
            game_id) -> TransformedBoxscore:
        boxscore = self.api.get_boxscore_by_game_id(game_id=game_id)
        boxscore_adv = self.api.boxscore_advanced_v2_by_game_id(game_id=game_id)
        league_game_rows = league_games[league_games['GAME_ID'] == game_id]
        game_teams = generate_game_team(game_team_adv_df=boxscore_adv.team_data, league_game_rows=league_game_rows)
        game_players = generate_game_players(boxscore=boxscore, boxscore_adv=boxscore_adv)
        game = generate_game(league_game_rows=league_game_rows, boxscore=boxscore.team_data)

        return TransformedBoxscore(
            id=game_id,
            game_players=game_players,
            game_teams=game_teams,
            game=game)
