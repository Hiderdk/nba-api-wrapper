import datetime
from typing import Literal

import numpy as np
import pandas as pd

from nba_api_wrapper.api.api_calls import NBAApi
from nba_api_wrapper.api.data_models import LGFDataNames, BoxscoreV2Names, PlayByPlay2Names, RotationNames
from nba_api_wrapper.config import SUPPORTED_TEAM_NAMES

from nba_api_wrapper.datastructures import PlayByPlay, Game, GameTeam, GamePlayer
from nba_api_wrapper.generators.dataframe_generators import generate_inplay_lineups, generate_shot_plays, \
    generate_transformed_play_by_plays

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

    def generate_game(
            self,
            league_games: pd.DataFrame,
            game_id) -> Game:
        boxscore = self.nba_api.get_boxscore_by_game_id(game_id=game_id)
        league_game_rows = league_games[league_games['GAME_ID'] == game_id]
        game_teams = self._generate_game_team(league_game_rows=league_game_rows, boxscore=boxscore)

        return Game(
            minutes=self._get_game_minutes_played(boxscore),
            teams=game_teams,
            id=str(league_game_rows[LFG.GAME_ID].iloc[0]),
            start_date=league_game_rows[LFG.GAME_DATE].iloc[0],
            season_id=int(league_game_rows[LFG.SEASON_ID].iloc[0])
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
        transformed_play_by_plays = generate_transformed_play_by_plays(play_by_plays=play_by_plays,
                                                                       inplay_lineups=inplay_lineups)

        return PlayByPlay(
            team_rotations=team_rotations,
            inplay_lineups=inplay_lineups,
            play_by_plays=play_by_plays,
            shot_plays=shot_plays,
            transformed_play_by_plays=transformed_play_by_plays,
        )

    def _generate_game_team(self, league_game_rows: pd.DataFrame, boxscore: pd.DataFrame) -> list[GameTeam]:
        game_teams: list[GameTeam] = []

        for _, game_team_row in league_game_rows.iterrows():
            location = self._get_location(game_team_row)
            team_name = game_team_row[LFG.TEAM_NAME]
            opponent_game_team_row = league_game_rows[league_game_rows[LFG.TEAM_NAME] != team_name]
            team_won = self._get_team_won(league_game_rows=league_game_rows, team_name=team_name)
            team_id = game_team_row[BOX.TEAM_ID]

            game_team = GameTeam(
                location=location,
                name=team_name,
                opponent=str(opponent_game_team_row[LFG.TEAM_NAME].iloc[0]),
                name_abbreviation=game_team_row[LFG.TEAM_ABBREVIATION],
                id=team_id,
                points=game_team_row[LFG.POINTS],
                opponent_points=int(opponent_game_team_row[LFG.POINTS].iloc[0]),
                won=team_won,
                players=self._create_game_players(boxscore=boxscore, team_id=team_id)
            )
            game_teams.append(game_team)

        return game_teams

    def _get_location(self, row: pd.Series) -> Literal['home', 'away']:
        if "@" in row[LGFDataNames.MATCHUP]:
            return 'away'
        return 'home'

    def _create_game_players(self, boxscore: pd.DataFrame, team_id: str) -> list[GamePlayer]:
        game_players: list[GamePlayer] = []
        for _, row in boxscore[boxscore[BOX.TEAM_ID] == team_id].iterrows():
            game_player = GamePlayer(
                id=row[BOX.PLAYER_ID],
                name=row[BOX.PLAYER_NAME],
                free_throws_made=row[BOX.FTM],
                free_throws_attempted=row[BOX.FTA],
                three_pointers_made=row[BOX.FG3M],
                three_pointers_attempted=row[BOX.FGA],
                two_pointers_made=row[BOX.FGM] - row[BOX.FG3M],
                two_pointers_attempted=row[BOX.FGA] - row[BOX.FG3A],
                points=row[BOX.PTS],
                plus_minus=row[BOX.PLUS_MINUS],
                minutes=self._get_minutes_played(box_row=row)
            )
            game_players.append(game_player)

        return game_players

    def _get_team_won(self, league_game_rows: pd.DataFrame, team_name: str) -> bool:
        team_points = league_game_rows[league_game_rows[LFG.TEAM_NAME] == team_name][LFG.POINTS].iloc[0]
        opponent_points = league_game_rows[league_game_rows[LFG.TEAM_NAME] != team_name][LFG.POINTS].iloc[0]
        if team_points > opponent_points:
            return True
        return False

    def _get_minutes_played(self, box_row: pd.Series) -> float:
        if box_row[BOX.MIN] != 0:
            secs = float(box_row[BOX.MIN].split(":")[1])
            return round(float(box_row[BOX.MIN].split(":")[0]) + secs / 60, 3)
        else:
            return 0

    def _get_game_minutes_played(self, boxscore: pd.DataFrame):
        mins = 0
        for _, row in boxscore.iterrows():
            mins += self._get_minutes_played(row)

        return round(mins / 10, 2)
