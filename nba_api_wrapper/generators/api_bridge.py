import datetime

import numpy as np
import pandas as pd

from nba_api_wrapper.api.api_calls import NBAApi
from nba_api_wrapper.data_models import LGFDataNames, BoxscoreV2Names, PlayByPlay2Names, RotationNames
from nba_api_wrapper.config import SUPPORTED_TEAM_NAMES

from nba_api_wrapper.datastructures import PlayByPlay, Boxscore
from nba_api_wrapper.generators.boxscore_generators import generate_game_players, generate_game_team, generate_game

from nba_api_wrapper.generators.play_by_play_generators import generate_inplay_lineups, generate_shot_plays, \
    generate_offense_player_play_by_plays, generate_defense_player_play_by_plays, \
    generate_possession_attempts, generate_possession_from_attempts

BOX = BoxscoreV2Names
LFG = LGFDataNames
RN = RotationNames
PBP = PlayByPlay2Names


class ApiBridge():

    def __init__(self,
                 nba_api: NBAApi = NBAApi(),
                 game_team_player_data: bool = True,
                 supported_team_names=SUPPORTED_TEAM_NAMES,
                 ):
        self.supported_team_names = supported_team_names
        self.nba_api = nba_api
        self.game_team_player_data = game_team_player_data

    def generate_league_games(self, min_date: datetime.date, max_date: datetime.date) -> pd.DataFrame:
        date_from_nullable = min_date.strftime('%m/%d/%Y')
        date_to_nullable = max_date.strftime('%m/%d/%Y')

        data = self.nba_api.get_league_game_finder_data(min_date=date_from_nullable,
                                                        max_date=date_to_nullable)

        return (data[data[LGFDataNames.TEAM_NAME].isin(self.supported_team_names)]
                .sort_values(by=[LGFDataNames.GAME_DATE, LGFDataNames.GAME_ID], ascending=True)
                )

    def generate_boxscore(
            self,
            league_games: pd.DataFrame,
            game_id) -> Boxscore:
        boxscore = self.nba_api.get_boxscore_by_game_id(game_id=game_id)
        league_game_rows = league_games[league_games['GAME_ID'] == game_id]
        game_teams = generate_game_team(league_game_rows=league_game_rows)
        game_players = generate_game_players(boxscore=boxscore)
        game = generate_game(league_game_rows=league_game_rows, boxscore=boxscore)

        return Boxscore(
            id=game_id,
            game_players=game_players,
            game_teams=game_teams,
            game=game

        )

    def generate_play_by_play(self, game_id: int) -> PlayByPlay:
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
        inplay_lineups = generate_inplay_lineups(team_rotations=team_rotations)
        shot_plays = generate_shot_plays(play_by_plays=play_by_plays, inplay_lineups=inplay_lineups)
        possession_attempts, play_by_plays = generate_possession_attempts(play_by_plays=play_by_plays,
                                                                           inplay_lineups=inplay_lineups)

        possessions = generate_possession_from_attempts(possession_attempts=possession_attempts)

        defense_player_play_by_plays = generate_defense_player_play_by_plays(play_by_plays=play_by_plays,
                                                                             possessions=possessions)
        offense_player_play_by_plays = generate_offense_player_play_by_plays(play_by_plays=play_by_plays,
                                                                             possessions=possessions)


        return PlayByPlay(
            team_rotations=team_rotations,
            inplay_lineups=inplay_lineups,
            play_by_plays=play_by_plays,
            shot_plays=shot_plays,
            possessions=possessions,
            lineup_play_by_plays=possession_attempts,
            offense_player_play_by_plays=offense_player_play_by_plays,
            defense_player_play_by_plays=defense_player_play_by_plays,
        )
