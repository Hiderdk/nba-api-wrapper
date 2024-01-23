import datetime
import logging

from typing import Optional

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
                 ):

        self.store_frequency = store_frequency
        self.storer = storer
        self.nba_api = api
        self.newest_games_only = newest_games_only

    def generate(self, min_date: Optional[pendulum.Date] = None, max_date: Optional[pendulum.Date] = None) -> None:
        if min_date is None:
            min_date = pendulum.now().subtract(days=5)
            logging.info(f"min_date not provided, using {min_date}")

        if max_date is None:
            max_date = pendulum.now()

        game_ids = self.nba_api.get_game_ids_by_date_range(min_date=min_date, max_date=max_date)

        if self.newest_games_only:
            stored_games = self.storer.load_games()
            stored_game_ids = stored_games[GameModel.GAME_ID].unique().tolist()
            to_process_game_ids = [game_id for game_id in game_ids if game_id not in stored_game_ids]
        else:
            to_process_game_ids = game_ids

        logging.info(f"Starting to store {len(to_process_game_ids)} games")

        while len(to_process_game_ids) > 0:
            to_store_game_ids = to_process_game_ids[:self.store_frequency]
            collected_data = self._generate_collected_data(game_ids=to_store_game_ids)
            self.storer.store(collected_data=collected_data)
            to_process_game_Ids = to_process_game_ids[self.store_frequency:]
            logging.info(f"Finished storing, {len(to_process_game_Ids)} games remaining")

    def _generate_collected_data(self, game_ids: list[int]) -> CollectedData:
        possessions = []
        game_players = []
        game_teams = []
        games = []
        for game_id in game_ids:
            print(f"processing gameid {game_id}")

            try:
                game_team = self.nba_api.get_game_team_by_game_id(game_id)
                game_teams.append(game_team)
            except Exception as e:
                logging.warning(f"gameid {game_id} failed to get boxscore by gameid, error: {e}")
                raise ValueError

            try:
                game_player = self.nba_api.get_game_player_by_game_id(game_id)
                game_players.append(game_player)
            except Exception as e:
                logging.warning(f"gameid {game_id} failed to get boxscore by gameid, error: {e})")
                raise ValueError
            try:
                possession = self.nba_api.get_possessions_by_game_id(game_id=game_id)
                possessions.append(possession)
            except Exception as e:
                logging.warning(f"gameid {game_id} failed to get possessions by gameid, error: {e}")

            try:
                game = self.nba_api.get_game_by_game_id(game_id)
                games.append(game)
            except Exception as e:
                logging.warning(f"gameid {game_id} failed to get boxscore by gameid, error: {e})")
                raise ValueError

        return CollectedData(
            possessions=pd.concat(possessions) if possessions else [],
            game_teams=pd.concat(game_teams) if game_teams else [],
            game_players=pd.concat(game_players) if game_players else [],
            game=pd.concat(games) if games else [],
        )

    def _generated_transformed_boxscore(
            self,
            league_games: pd.DataFrame,
            game_id) -> TransformedBoxscore:
        boxscore = self.nba_api.get_boxscore_by_game_id(game_id=game_id)
        boxscore_adv = self.nba_api.boxscore_advanced_v2_by_game_id(game_id=game_id)
        league_game_rows = league_games[league_games['GAME_ID'] == game_id]
        game_teams = generate_game_team(game_team_adv_df=boxscore_adv.team_data, league_game_rows=league_game_rows)
        game_players = generate_game_players(boxscore=boxscore, boxscore_adv=boxscore_adv)
        game = generate_game(league_game_rows=league_game_rows, boxscore=boxscore.team_data)

        return TransformedBoxscore(
            id=game_id,
            game_players=game_players,
            game_teams=game_teams,
            game=game

        )

    def _generate_play_by_play(self, game_id: int, home_team_id: int, away_team_id: int,
                               lineups: pd.DataFrame) -> PlayByPlay:
        play_by_plays = self.nba_api.get_play_by_play_by_game_id(game_id=game_id)
        play_by_plays = (
            play_by_plays.assign(
                MINUTES=play_by_plays['PCTIMESTRING'].str.split(":").str[0].astype(int),
                SECONDS=play_by_plays['PCTIMESTRING'].str.split(":").str[1].astype(int)
            )
            .assign(SECONDS_REMAINING=lambda x: x['MINUTES'] * 60 + x['SECONDS'])
            .assign(
                OVERTIME_PERIODS=(play_by_plays['PERIOD'] - 4).clip(lower=0),
                BASE_SECONDS=play_by_plays['PERIOD'].clip(upper=4) * 12 * 60,
                OVERTIME_SECONDS=lambda x: x['OVERTIME_PERIODS'] * 5 * 60
            )
            .assign(
                SECONDS_PLAYED=lambda x: np.where(
                    play_by_plays['PERIOD'] > 4,
                    4 * 12 * 60 + x['OVERTIME_SECONDS'] - x['SECONDS_REMAINING'],
                    x['BASE_SECONDS'] - x['SECONDS_REMAINING']
                )
            )
            .drop(['MINUTES', 'SECONDS', 'SECONDS_REMAINING', 'OVERTIME_PERIODS', 'BASE_SECONDS', 'OVERTIME_SECONDS',
                   'PCTIMESTRING'], axis=1)
        )

        team_rotations = self.nba_api.get_rotations_by_game_id(game_id=game_id)
        for idx, rotation in enumerate(team_rotations):
            team_rotations[idx][RN.IN_TIME_SECONDS_PLAYED] = team_rotations[idx][RN.IN_TIME_REAL] / 10
            team_rotations[idx][RN.OUT_TIME_SECONDS_PLAYED] = team_rotations[idx][RN.OUT_TIME_REAL] / 10
        inplay_lineups, lineups = generate_inplay_lineups(team_rotations=team_rotations, lineups=lineups)
        shot_plays = generate_shot_plays(play_by_plays=play_by_plays, inplay_lineups=inplay_lineups)
        possession_attempts, play_by_plays = generate_possession_attempts(play_by_plays=play_by_plays,
                                                                          inplay_lineups=inplay_lineups,
                                                                          home_team_id=home_team_id,
                                                                          away_team_id=away_team_id)

        possessions = generate_possession_from_attempts(possession_attempts=possession_attempts)

        defense_player_play_by_plays = generate_defense_player_play_by_plays(play_by_plays=play_by_plays,
                                                                             possessions=possessions, lineups=lineups)

        offense_player_play_by_plays = generate_offense_player_play_by_plays(play_by_plays=play_by_plays,
                                                                             possessions=possessions, lineups=lineups)

        return PlayByPlay(
            team_rotations=team_rotations,
            inplay_lineups=inplay_lineups,
            play_by_plays=play_by_plays,
            shot_plays=shot_plays,
            possessions=possessions,
            possession_attempts=possession_attempts,
            offense_player_play_by_plays=offense_player_play_by_plays,
            defense_player_play_by_plays=defense_player_play_by_plays,
            lineups=lineups
        )
