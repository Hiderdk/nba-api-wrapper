import datetime
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from nba_api_wrapper.api.api_calls import NBAApi
from nba_api_wrapper.config import SUPPORTED_TEAM_NAMES
from nba_api_wrapper.data_models import PosessionNames, LGFDataNames, GameTeamNames, BoxscoreV2Names, RotationNames, \
    PlayByPlay2Names, GameNames
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
PBP = PlayByPlay2Names

logging.basicConfig(level=logging.INFO)


class GameStorer():
    def __init__(self,
                 storer: Storer = FileStorer(),
                 store_frequency: int = 20,
                 nba_api: NBAApi = NBAApi(),
                 game_team_player_data: bool = True,
                 newest_games_only: bool = False,
                 supported_team_names=SUPPORTED_TEAM_NAMES,
                 ):

        self.store_frequency = store_frequency

        self.storer = storer
        self.nba_api = nba_api
        self.game_team_player_data = game_team_player_data
        self.supported_team_names = supported_team_names
        self.newest_games_only = newest_games_only

    def generate(self, min_date: Optional[str] = None, max_date: Optional[str] = None) -> None:
        if min_date is None:
            min_date_time = datetime.datetime.now() - datetime.timedelta(days=365)
            logging.info(f"min_date not provided, using {min_date_time}")
        else:

            min_date_time = datetime.datetime.strptime(min_date, "%Y-%m-%d")
        if max_date is None:
            max_date_time = datetime.datetime.now()
            logging.info(f"max_date not provided, using {max_date_time}")
        else:
            max_date_time = datetime.datetime.strptime(max_date, "%Y-%m-%d")

        league_games = self.generate_league_games(min_date=min_date_time,
                                                  max_date=max_date_time)

        remaining_game_ids = league_games[LFG.GAME_ID].unique().tolist()
        if self.newest_games_only:
            stored_games = self.storer.load_games()
            stored_game_ids = stored_games[GameNames.GAME_ID].unique().tolist()
            remaining_game_ids = [game_id for game_id in remaining_game_ids if game_id not in stored_game_ids]

        logging.info(f"Starting to store {len(remaining_game_ids)} games")

        while len(remaining_game_ids) > 0:
            game_ids = remaining_game_ids[:self.store_frequency]
            lineups = self.storer.load_lineups()
            collected_data = self._generate_collected_data(game_ids=game_ids, lineups=lineups,
                                                           league_games=league_games)
            self.storer.store(collected_data=collected_data)
            remaining_game_ids = remaining_game_ids[self.store_frequency:]
            logging.info(f"Finished storing, {len(remaining_game_ids)} games remaining")

    def _generate_collected_data(self, game_ids: list[int], league_games: pd.DataFrame,
                                 lineups: pd.DataFrame) -> CollectedData:
        possessions = []
        game_players = []
        game_teams = []
        offense_player_play_by_plays = []
        defense_player_play_by_plays = []
        possession_attempts = []
        games = []
        for game_id in game_ids:
            print(f"processing gameid {game_id}")

            try:
                transformed_boxscore = self._generated_transformed_boxscore(game_id=game_id, league_games=league_games)
            except ValueError as e:
                logging.warning(f"gameid {game_id} failed to generate boxscore, error: {e}")

            home_team_id = \
                transformed_boxscore.game_teams[transformed_boxscore.game_teams[GameTeamNames.LOCATION] == 'home'][
                    GameTeamNames.TEAM_ID].iloc[
                    0]
            away_team_id = \
                transformed_boxscore.game_teams[transformed_boxscore.game_teams[GameTeamNames.LOCATION] != 'home'][
                    GameTeamNames.TEAM_ID].iloc[
                    0]
            play_by_play = self._generate_play_by_play(game_id=game_id, home_team_id=home_team_id,
                                                       away_team_id=away_team_id, lineups=lineups)

            possessions.append(play_by_play.possessions)
            offense_player_play_by_plays.append(play_by_play.offense_player_play_by_plays)
            defense_player_play_by_plays.append(play_by_play.defense_player_play_by_plays)

            possession_attempts.append(play_by_play.possessions)
            game_teams.append(transformed_boxscore.game_teams)
            game_players.append(transformed_boxscore.game_players)
            games.append(transformed_boxscore.game)

            lineups = play_by_play.lineups

        return CollectedData(
            possessions=pd.concat(possessions) if possessions else [],
            game_teams=pd.concat(game_teams) if game_teams else [],
            game_players=pd.concat(game_players) if game_players else [],
            offense_player_play_by_plays=pd.concat(
                offense_player_play_by_plays) if offense_player_play_by_plays else [],
            defense_player_play_by_plays=pd.concat(
                defense_player_play_by_plays) if defense_player_play_by_plays else [],
            possession_attempts=pd.concat(possession_attempts) if possession_attempts else [],
            game=pd.concat(games) if games else [],
            lineups=lineups
        )

    def generate_league_games(self, min_date: datetime.date, max_date: datetime.date) -> pd.DataFrame:
        date_from_nullable = min_date.strftime('%m/%d/%Y')
        date_to_nullable = max_date.strftime('%m/%d/%Y')

        data = self.nba_api.get_league_game_finder_data(min_date=date_from_nullable,
                                                        max_date=date_to_nullable)

        return (data[data[LGFDataNames.TEAM_NAME].isin(self.supported_team_names)]
                .sort_values(by=[LGFDataNames.GAME_DATE, LGFDataNames.GAME_ID], ascending=True)
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
