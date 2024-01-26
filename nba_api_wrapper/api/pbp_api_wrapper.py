import logging
from typing import Any, Union

import pandas as pd
import pendulum
from pbpstats.data_loader.stats_nba.possessions.loader import TeamHasBackToBackPossessionsException
from pbpstats.resources.enhanced_pbp import InvalidNumberOfStartersException
from pbpstats.resources.enhanced_pbp.rebound import EventOrderError

from enums import Location
from nba_api_wrapper.api._base import BaseApi
from nba_api_wrapper.api.api_throttle import APIThrottle
from nba_api_wrapper.api.decorators import retry_on_error
from nba_api_wrapper.data_models import PosessionModel, NBAPBPGamePlayerModel, NbaPbPGameTeamModel, GamePlayerModel, \
    GameModel
from pbpstats.client import Client
from nba_api.stats.endpoints import BoxScoreAdvancedV3, BoxScoreTraditionalV2

api_throttle = APIThrottle(interval_seconds=25, max_calls_per_interval=6)


class PlayByPlayNbaApi(BaseApi):

    def __init__(self):

        self._game_id_to_final_games: dict[Union[str, int], object] = {}
        self._game_id_nba_api_games: dict[Union[str, int], pd.DataFrame] = {}
        self._game_id_to_home_team_id = {}
        self._game_id_to_visitor_team_id = {}
        self._game_id_to_date = {}
        self._adv_game = None

    def get_game_ids_by_date_range(self, min_date: pendulum.DateTime, max_date: pendulum.DateTime) -> list[
        Union[str, int]]:
        game_ids = []
        for date in pendulum.period(min_date, max_date):
            game_ids += self.get_game_ids_by_date(date)
        return game_ids

    def get_game_ids_by_season(self, season_data: dict[str, Any]) -> list[Union[str, int]]:
        game_settings = {
            "Games": {"source": "web", "data_provider": "stats_nba"},
        }
        client = Client(game_settings)
        game_ids = []
        season_games = client.Season(**season_data)
        for game in season_games.games.final_games:
            game_ids.append(game['game_id'])
            self._game_id_to_home_team_id[game['game_id']] = game['home_team_id']
            self._game_id_to_visitor_team_id[game['game_id']] = game['visitor_team_id']
            self._game_id_to_date[game['game_id']] = pd.to_datetime(game['date'])

        return game_ids

    def get_game_ids_by_date(self, date: pendulum.DateTime) -> list[Union[str, int]]:
        game_settings = {
            "Games": {"source": "web", "data_provider": "stats_nba"},
        }
        client = Client(game_settings)
        game_ids = []
        date_str = date.format("MM/DD/YYYY")
        day_games = client.Day(date_str, "nba")
        for game in day_games.games.final_games:
            game_ids.append(game['game_id'])
            self._game_id_to_home_team_id[game['game_id']] = game['home_team_id']
            self._game_id_to_visitor_team_id[game['game_id']] = game['visitor_team_id']
            self._game_id_to_date[game['game_id']] = pd.to_datetime(game['date'])

        return game_ids

    @api_throttle
    @api_throttle
    @retry_on_error
    def get_game_team_by_game_id(self, game_id: int) -> pd.DataFrame:

        game_team_data = {
            NbaPbPGameTeamModel.GAME_ID: [],
            NbaPbPGameTeamModel.TEAM_ID: [],
            NbaPbPGameTeamModel.TEAM_NAME: [],
            NbaPbPGameTeamModel.TEAM_ID_OPPONENT: [],
            NbaPbPGameTeamModel.LOCATION: [],
            NbaPbPGameTeamModel.SCORE: [],
            NbaPbPGameTeamModel.SCORE_OPPONENT: [],
            NbaPbPGameTeamModel.WON: [],
            NbaPbPGameTeamModel.PACE: [],
            NbaPbPGameTeamModel.E_PACE: [],
            NbaPbPGameTeamModel.POSS: [],
            NbaPbPGameTeamModel.PIE: [],

        }

        game_settings = {
            "Games": {"source": "web", "data_provider": "stats_nba"},
            "Boxscore": {"source": "web", "data_provider": "stats_nba"},
            "Possessions": {"source": "web", "data_provider": "stats_nba"},
        }
        try:
            client = Client(game_settings)
            game = client.Game(game_id=game_id)
            self._game_id_to_final_games[game_id] = game
        except (TeamHasBackToBackPossessionsException, EventOrderError, InvalidNumberOfStartersException):
            logging.warning(f"GameId {game_id} TeamHasBackToBackPossessionsException")
            nba_api_game = BoxScoreTraditionalV2(game_id=game_id)
            self._game_id_nba_api_games[game_id] = nba_api_game.get_data_frames()

        self._adv_game = BoxScoreAdvancedV3(game_id=game_id)
        if self._adv_game is not None:
            adv_game_dfs = self._adv_game.get_data_frames()
        else:
            logging.warning(f"gameid {game_id} failed to get boxscore advanced by gameid")
            adv_game_dfs = None

        if game_id not in self._game_id_to_home_team_id:
            raise ValueError(f"Game id {game_id} not found in game id to home team id map")

        if game_id in self._game_id_nba_api_games:

            for idx, row in self._game_id_nba_api_games[game_id][1].iterrows():

                score_opponent = self._game_id_nba_api_games[game_id][1].iloc[-idx + 1]['PTS']
                won = 1 if row['PTS'] > score_opponent else 0

                if row['TEAM_ID'] == self._game_id_to_home_team_id[game_id]:
                    game_team_data[NbaPbPGameTeamModel.LOCATION].append(Location.HOME.value)
                elif row['TEAM_ID'] == self._game_id_to_visitor_team_id[game_id]:
                    game_team_data[NbaPbPGameTeamModel.LOCATION].append(Location.AWAY.value)
                else:
                    game_team_data[NbaPbPGameTeamModel.LOCATION].append(Location.NEUTRAL.value)

                game_team_data[NbaPbPGameTeamModel.GAME_ID].append(game_id)
                game_team_data[NbaPbPGameTeamModel.TEAM_ID].append(row['TEAM_ID'])
                game_team_data[NbaPbPGameTeamModel.TEAM_NAME].append(row['TEAM_NAME'])
                game_team_data[NbaPbPGameTeamModel.TEAM_ID_OPPONENT].append(
                    self._game_id_nba_api_games[game_id][1].iloc[-idx + 1]['TEAM_ID'])
                game_team_data[NbaPbPGameTeamModel.SCORE].append(row['PTS'])
                game_team_data[NbaPbPGameTeamModel.SCORE_OPPONENT].append(score_opponent)
                game_team_data[NbaPbPGameTeamModel.WON].append(won)

        else:

            for idx, team in enumerate(game.boxscore.data['team']):

                won = 1 if team['pts'] > game.boxscore.data['team'][-idx + 1]['pts'] else 0

                if team['team_id'] == self._game_id_to_home_team_id[game_id]:
                    game_team_data[NbaPbPGameTeamModel.LOCATION].append(Location.HOME.value)
                elif team['team_id'] == self._game_id_to_visitor_team_id[game_id]:
                    game_team_data[NbaPbPGameTeamModel.LOCATION].append(Location.AWAY.value)
                else:
                    game_team_data[NbaPbPGameTeamModel.LOCATION].append(Location.NEUTRAL.value)

                game_team_data[NbaPbPGameTeamModel.GAME_ID].append(game_id)
                game_team_data[NbaPbPGameTeamModel.TEAM_ID].append(team['team_id'])
                game_team_data[NbaPbPGameTeamModel.TEAM_NAME].append(team['team_name'])
                game_team_data[NbaPbPGameTeamModel.TEAM_ID_OPPONENT].append(
                    game.boxscore.data['team'][-idx + 1]['team_id'])
                game_team_data[NbaPbPGameTeamModel.SCORE].append(team['pts'])
                game_team_data[NbaPbPGameTeamModel.SCORE_OPPONENT].append(
                    game.boxscore.data['team'][-idx + 1]['pts'])
                game_team_data[NbaPbPGameTeamModel.WON].append(won)

        for team_id in game_team_data[NbaPbPGameTeamModel.TEAM_ID]:

            if self._adv_game is not None and len(adv_game_dfs) > 1:
                adv_game_team = adv_game_dfs[0] if adv_game_dfs[0]['teamId'].iloc[0] == team_id else \
                    adv_game_dfs[1]
                game_team_data[NbaPbPGameTeamModel.PIE].append(adv_game_team['PIE'].iloc[0])
                game_team_data[NbaPbPGameTeamModel.PACE].append(adv_game_team['pace'].iloc[0])
                game_team_data[NbaPbPGameTeamModel.E_PACE].append(adv_game_team['estimatedPace'].iloc[0])
                game_team_data[NbaPbPGameTeamModel.POSS].append(adv_game_team['possessions'].iloc[0])
            else:
                game_team_data[NbaPbPGameTeamModel.PIE].append(None)
                game_team_data[NbaPbPGameTeamModel.PACE].append(None)
                game_team_data[NbaPbPGameTeamModel.E_PACE].append(None)
                game_team_data[NbaPbPGameTeamModel.POSS].append(None)

        return pd.DataFrame(game_team_data)

    def get_game_player_by_game_id(self, game_id: Union[str, int]) -> GamePlayerModel:
        game_player_data = {
            NBAPBPGamePlayerModel.GAME_ID: [],
            NBAPBPGamePlayerModel.TEAM_ID: [],
            NBAPBPGamePlayerModel.PLAYER_ID: [],
            NBAPBPGamePlayerModel.PLAYER_NAME: [],
            NBAPBPGamePlayerModel.START_POSITION: [],
            NBAPBPGamePlayerModel.MINUTES: [],
            NBAPBPGamePlayerModel.POINTS: [],
            NBAPBPGamePlayerModel.THREE_POINTERS_MADE: [],
            NBAPBPGamePlayerModel.THREE_POINTERS_ATTEMPTED: [],
            NBAPBPGamePlayerModel.TWO_POINTERS_MADE: [],
            NBAPBPGamePlayerModel.TWO_POINTERS_ATTEMPTED: [],
            NBAPBPGamePlayerModel.FREE_THROWS_MADE: [],
            NBAPBPGamePlayerModel.FREE_THROWS_ATTEMPTED: [],
            NBAPBPGamePlayerModel.PLUS_MINUS: [],
            NBAPBPGamePlayerModel.BLOCKS: [],
            NBAPBPGamePlayerModel.STEALS: [],
            NBAPBPGamePlayerModel.ASSISTS: [],
            NBAPBPGamePlayerModel.OFFENSIVE_REBOUNDS: [],
            NBAPBPGamePlayerModel.DEFENSIVE_REBOUNDS: [],
            NBAPBPGamePlayerModel.TURNOVERS: [],
            NBAPBPGamePlayerModel.FOULS: [],
            NBAPBPGamePlayerModel.PACE: [],
            NBAPBPGamePlayerModel.POSS: [],
            NBAPBPGamePlayerModel.E_PACE: [],
        }

        if game_id in self._game_id_nba_api_games:
            for _, row in self._game_id_nba_api_games[game_id][0].iterrows():
                game_player_data[NBAPBPGamePlayerModel.GAME_ID].append(game_id)
                game_player_data[NBAPBPGamePlayerModel.TEAM_ID].append(row['TEAM_ID'])
                game_player_data[NBAPBPGamePlayerModel.PLAYER_ID].append(row['PLAYER_ID'])
                game_player_data[NBAPBPGamePlayerModel.PLAYER_NAME].append(row['PLAYER_NAME'])
                game_player_data[NBAPBPGamePlayerModel.START_POSITION].append(row['START_POSITION'])
                game_player_data[NBAPBPGamePlayerModel.MINUTES].append(row['MIN'])
                game_player_data[NBAPBPGamePlayerModel.POINTS].append(row['PTS'])
                game_player_data[NBAPBPGamePlayerModel.THREE_POINTERS_MADE].append(row['FG3M'])
                game_player_data[NBAPBPGamePlayerModel.THREE_POINTERS_ATTEMPTED].append(row['FG3A'])
                game_player_data[NBAPBPGamePlayerModel.TWO_POINTERS_MADE].append(row['FGM'] - row['FG3M'])
                game_player_data[NBAPBPGamePlayerModel.TWO_POINTERS_ATTEMPTED].append(row['FGA'] - row['FG3A'])
                game_player_data[NBAPBPGamePlayerModel.FREE_THROWS_MADE].append(row['FTM'])
                game_player_data[NBAPBPGamePlayerModel.FREE_THROWS_ATTEMPTED].append(row['FTA'])
                game_player_data[NBAPBPGamePlayerModel.PLUS_MINUS].append(row['PLUS_MINUS'])
                game_player_data[NBAPBPGamePlayerModel.BLOCKS].append(row['BLK'])
                game_player_data[NBAPBPGamePlayerModel.STEALS].append(row['STL'])
                game_player_data[NBAPBPGamePlayerModel.ASSISTS].append(row['AST'])
                game_player_data[NBAPBPGamePlayerModel.OFFENSIVE_REBOUNDS].append(row['OREB'])
                game_player_data[NBAPBPGamePlayerModel.DEFENSIVE_REBOUNDS].append(row['DREB'])
                game_player_data[NBAPBPGamePlayerModel.TURNOVERS].append(row['TO'])
                game_player_data[NBAPBPGamePlayerModel.FOULS].append(row['PF'])

        else:

            for idx, player in enumerate(self._game_id_to_final_games[game_id].boxscore.data['player']):
                game_player_data[NBAPBPGamePlayerModel.GAME_ID].append(game_id)
                game_player_data[NBAPBPGamePlayerModel.TEAM_ID].append(player['team_id'])
                game_player_data[NBAPBPGamePlayerModel.PLAYER_ID].append(player['player_id'])
                game_player_data[NBAPBPGamePlayerModel.PLAYER_NAME].append(player['name'])
                game_player_data[NBAPBPGamePlayerModel.START_POSITION].append(player['start_position'])
                game_player_data[NBAPBPGamePlayerModel.MINUTES].append(
                    float(player['min'].split(":")[0]) + float(player['min'].split(":")[1]) / 60)
                game_player_data[NBAPBPGamePlayerModel.POINTS].append(player['pts'])
                game_player_data[NBAPBPGamePlayerModel.THREE_POINTERS_MADE].append(player['fg3m'])
                game_player_data[NBAPBPGamePlayerModel.THREE_POINTERS_ATTEMPTED].append(player['fg3a'])
                game_player_data[NBAPBPGamePlayerModel.TWO_POINTERS_MADE].append(player['fgm'] - player['fg3m'])
                game_player_data[NBAPBPGamePlayerModel.TWO_POINTERS_ATTEMPTED].append(player['fga'] - player['fg3a'])
                game_player_data[NBAPBPGamePlayerModel.FREE_THROWS_MADE].append(player['ftm'])
                game_player_data[NBAPBPGamePlayerModel.FREE_THROWS_ATTEMPTED].append(player['fta'])
                game_player_data[NBAPBPGamePlayerModel.PLUS_MINUS].append(player['plus_minus'])
                game_player_data[NBAPBPGamePlayerModel.BLOCKS].append(player['blk'])
                game_player_data[NBAPBPGamePlayerModel.STEALS].append(player['stl'])
                game_player_data[NBAPBPGamePlayerModel.ASSISTS].append(player['ast'])
                game_player_data[NBAPBPGamePlayerModel.OFFENSIVE_REBOUNDS].append(player['oreb'])
                game_player_data[NBAPBPGamePlayerModel.DEFENSIVE_REBOUNDS].append(player['dreb'])
                game_player_data[NBAPBPGamePlayerModel.TURNOVERS].append(player['to'])
                game_player_data[NBAPBPGamePlayerModel.FOULS].append(player['pf'])

        for player_id in game_player_data[NBAPBPGamePlayerModel.PLAYER_ID]:
            if self._adv_game is not None:
                adv_game_dfs = self._adv_game.get_data_frames()
                adv_game_players = [adv_game_df for _, adv_game_df in adv_game_dfs[0].iterrows() if
                                    adv_game_df['personId'] == player_id]
                if len(adv_game_players) == 0:
                    logging.warning(
                        f"gameid {game_id} failed to get boxscore advanced by gameid for playerid {player['player_id']}")
                    game_player_data[NBAPBPGamePlayerModel.PACE].append(None)
                    game_player_data[NBAPBPGamePlayerModel.POSS].append(None)
                    game_player_data[NBAPBPGamePlayerModel.E_PACE].append(None)
                else:

                    game_player_data[NBAPBPGamePlayerModel.PACE].append(adv_game_players[0]['pace'])
                    game_player_data[NBAPBPGamePlayerModel.POSS].append(adv_game_players[0]['possessions'])
                    game_player_data[NBAPBPGamePlayerModel.E_PACE].append(adv_game_players[0]['estimatedPace'])

            else:

                game_player_data[NBAPBPGamePlayerModel.PACE].append(None)
                game_player_data[NBAPBPGamePlayerModel.POSS].append(None)
                game_player_data[NBAPBPGamePlayerModel.E_PACE].append(None)

        return pd.DataFrame(game_player_data)

    @api_throttle
    @retry_on_error
    def get_possessions_by_game_id(self, game_id: str):

        game = self._game_id_to_final_games[game_id]

        possessions_data: dict[PosessionModel, list[Any]] = {
            PosessionModel.TEAM_ID_OFFENSE: [],
            PosessionModel.TEAM_ID_DEFENSE: [],
            PosessionModel.GAME_ID: [],
            PosessionModel.START_TIME_SECONDS: [],
            PosessionModel.END_TIME_SECONDS: [],
            PosessionModel.POINTS_OFFENSE: [],
            PosessionModel.LINEUP_OFFENSE: [],
            PosessionModel.LINEUP_DEFENSE: [],
            PosessionModel.LINEUP_ID_OFFENSE: [],
            PosessionModel.LINEUP_ID_DEFENSE: [],
            PosessionModel.PERIOD: [],
            PosessionModel.FREE_THROWS_MADE: [],
            PosessionModel.FREE_THROWS_ATTEMPTED: [],
            PosessionModel.TWO_POINTERS_MADE: [],
            PosessionModel.TWO_POINTERS_ATTEMPTED: [],
            PosessionModel.THREE_POINTERS_MADE: [],
            PosessionModel.THREE_POINTERS_ATTEMPTED: [],

        }

        for possession in game.possessions.items:
            team_id_offense = None
            team_id_defense = None
            start_time = int(possession.start_time.split(":")[0]) * 60 + int(possession.start_time.split(":")[1])
            end_time = int(possession.end_time.split(":")[0]) * 60 + int(possession.end_time.split(":")[1])

            team_id_points = {}
            points_offense = 0
            lineup_offense = None
            lineup_defense = None
            lineup_offense_id = None
            lineup_defense_id = None

            two_pointer_attempts = 0
            three_pointer_attempts = 0
            free_throw_attempts = 0
            free_throw_made = 0
            arc_three_pointer_attempts = 0
            corner_three_pointer_attempts = 0
            two_pointer_made = 0
            three_pointer_made = 0

            for event in possession.events:
                if 'Free Throw' in event:
                    free_throw_attempts += 1

            for posession_stat in possession.possession_stats:
                if "Off" in posession_stat['stat_key'] or 'BadPass' in posession_stat['stat_key'] or 'Missed' in \
                        posession_stat['stat_key'] or 'Turnover' in posession_stat['stat_key'] or 'ShotDistance' in \
                        posession_stat['stat_key']:
                    team_id_offense = posession_stat['team_id']
                    team_id_defense = posession_stat['opponent_team_id']
                    lineup_offense = tuple(posession_stat['lineup_id'].split("-"))
                    lineup_offense = [int(player_id) for player_id in lineup_offense]
                    lineup_defense = tuple(posession_stat['opponent_lineup_id'].split("-"))
                    lineup_defense = [int(player_id) for player_id in lineup_defense]
                    lineup_offense.sort()
                    lineup_defense.sort()

                    lineup_offense_id = '_'.join(map(str, lineup_offense))
                    lineup_defense_id = '_'.join(map(str, lineup_defense))


                elif posession_stat['stat_key'] == 'PlusMinus':
                    if posession_stat['stat_value'] > 0:
                        team_id_points[posession_stat['team_id']] = posession_stat['stat_value']
                        team_id_points[posession_stat['opponent_team_id']] = 0

                    if posession_stat['stat_value'] == 1:
                        free_throw_made += 1
                    elif posession_stat['stat_value'] == 2:
                        two_pointer_made += 1
                    elif posession_stat['stat_value'] == 3:
                        three_pointer_made += 1


                elif posession_stat['stat_key'] == "Total2ptShotDistance":
                    two_pointer_attempts += 1

                elif posession_stat['stat_key'] == "Total3ptShotDistance":
                    three_pointer_attempts += 1

            if team_id_offense in team_id_points:
                points_offense = team_id_points[team_id_offense]

            if lineup_offense is None or lineup_defense is None:
                continue

            possessions_data[PosessionModel.TEAM_ID_OFFENSE].append(team_id_offense)
            possessions_data[PosessionModel.TEAM_ID_DEFENSE].append(team_id_defense)
            possessions_data[PosessionModel.GAME_ID].append(game_id)
            possessions_data[PosessionModel.START_TIME_SECONDS].append(start_time)
            possessions_data[PosessionModel.END_TIME_SECONDS].append(end_time)
            possessions_data[PosessionModel.POINTS_OFFENSE].append(points_offense)
            possessions_data[PosessionModel.LINEUP_OFFENSE].append(tuple(lineup_offense))
            possessions_data[PosessionModel.LINEUP_DEFENSE].append(tuple(lineup_defense))
            possessions_data[PosessionModel.LINEUP_ID_OFFENSE].append(lineup_offense_id)
            possessions_data[PosessionModel.LINEUP_ID_DEFENSE].append(lineup_defense_id)
            possessions_data[PosessionModel.PERIOD].append(possession.period)
            possessions_data[PosessionModel.THREE_POINTERS_ATTEMPTED].append(three_pointer_attempts)
            possessions_data[PosessionModel.TWO_POINTERS_ATTEMPTED].append(two_pointer_attempts)
            possessions_data[PosessionModel.THREE_POINTERS_MADE].append(three_pointer_made)
            possessions_data[PosessionModel.TWO_POINTERS_MADE].append(two_pointer_made)

        return pd.DataFrame.from_dict(possessions_data)

    def get_game_by_game_id(self, game_id: Union[str, int]) -> pd.DataFrame:

        if game_id in self._game_id_nba_api_games:
            minutes = float(self._game_id_nba_api_games[game_id][1]['MIN'].iloc[0].split(":")[0]) + float(
                self._game_id_nba_api_games[game_id][1]['MIN'].iloc[0].split(":")[1]) / 60
        else:
            game_data = self._game_id_to_final_games[game_id]
            minutes = float(game_data.boxscore.team_items[0]['min'].split(":")[0]) + float(
                game_data.boxscore.team_items[0]['min'].split(":")[1]) / 60

        game: dict[GameModel, list[Any]] = {
            GameModel.GAME_ID: [game_id],
            GameModel.START_DATE: [self._game_id_to_date[game_id]],
            GameModel.MINUTES: [minutes / 5],
        }

        return pd.DataFrame.from_dict(game)
