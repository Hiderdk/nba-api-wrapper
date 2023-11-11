import logging

import pandas as pd

from nba_api_wrapper.data_models import GameTeamNames, GameNames, GamePlayerNames, LGFDataNames, BoxscoreV2Names

GT = GameTeamNames
G = GameNames
GP = GamePlayerNames
LGF = LGFDataNames
BOX = BoxscoreV2Names


def _get_team_won(league_game_rows: pd.DataFrame, team_name: str) -> bool:
    team_points = league_game_rows[league_game_rows[LGF.TEAM_NAME] == team_name][LGF.POINTS].iloc[0]
    opponent_points = league_game_rows[league_game_rows[LGF.TEAM_NAME] != team_name][LGF.POINTS].iloc[0]
    if team_points > opponent_points:
        return True
    return False


def _get_minutes_played(box_row: pd.Series) -> float:
    if box_row[BOX.MIN] != 0:
        secs = float(box_row[BOX.MIN].split(":")[1])
        return round(float(box_row[BOX.MIN].split(":")[0]) + secs / 60, 3)
    else:
        return 0


def _get_game_minutes_played(boxscore: pd.DataFrame):
    mins = 0
    for _, row in boxscore.iterrows():
        mins += _get_minutes_played(row)

    return round(mins / 10, 2)


def generate_game(boxscore: pd.DataFrame, league_game_rows: pd.DataFrame) -> pd.DataFrame:
    game = {
        G.MINUTES: [_get_game_minutes_played(boxscore=boxscore)],
        G.GAME_ID: [boxscore[BOX.GAME_ID].iloc[0]],
        G.SEASON_ID: [league_game_rows[LGF.SEASON_ID].iloc[0]],
        G.START_DATE: [league_game_rows[LGF.GAME_DATE].iloc[0]]
    }
    return pd.DataFrame.from_dict(game)


def generate_game_team(league_game_rows: pd.DataFrame) -> pd.DataFrame:
    game_team_dict = {
        GT.GAME_ID: [],
        GT.TEAM_ID: [],
        GT.SCORE: [],
        GT.SCORE_OPPONENT: [],
        GT.LOCATION: [],
        GT.TEAM_ID_OPPONENT: [],
        GT.TEAM_NAME_ABBR: [],
        GT.TEAM_NAME: [],
        GT.WON: [],
    }

    for _, game_team_row in league_game_rows.iterrows():

        if "@" in game_team_row[LGF.MATCHUP]:
            location = 'away'
        else:
            location = 'home'

        team_name = game_team_row[LGF.TEAM_NAME]
        opponent_game_team_row = league_game_rows[league_game_rows[LGF.TEAM_NAME] != team_name]
        if len(opponent_game_team_row) == 0:
            logging.warning(f"gameid {game_team_row[LGF.GAME_ID]} team {team_name} has no opponent")
            raise ValueError
        team_won = _get_team_won(league_game_rows=league_game_rows, team_name=team_name)
        team_id = game_team_row[LGF.TEAM_ID]

        game_team_dict[GT.GAME_ID].append(game_team_row[LGF.GAME_ID])
        game_team_dict[GT.LOCATION].append(location)
        game_team_dict[GT.TEAM_ID].append(team_id)
        game_team_dict[GT.TEAM_NAME].append(team_name)
        game_team_dict[GT.TEAM_ID_OPPONENT].append(opponent_game_team_row[LGF.TEAM_ID].iloc[0])
        game_team_dict[GT.SCORE].append(game_team_row[LGF.POINTS])
        game_team_dict[GT.SCORE_OPPONENT].append(opponent_game_team_row[LGF.POINTS].iloc[0])
        game_team_dict[GT.TEAM_NAME_ABBR].append(game_team_row[LGF.TEAM_ABBREVIATION])
        game_team_dict[GT.WON].append(team_won)

    return pd.DataFrame.from_dict(game_team_dict)


def generate_game_players(boxscore: pd.DataFrame) -> pd.DataFrame:
    game_player_dict = {
        GT.GAME_ID: [],
        GP.TEAM_ID: [],
        GP.PLAYER_ID: [],
        GP.PLAYER_NAME: [],
        GP.PLUS_MINUS: [],
        GP.POINTS: [],
        GP.MINUTES: [],
        GP.FREE_THROWS_ATTEMPTED: [],
        GP.FREE_THROWS_MADE: [],
        GP.THREE_POINTERS_MADE: [],
        GP.THREE_POINTERS_ATTEMPTED: [],
        GP.TWO_POINTERS_MADE: [],
        GP.TWO_POINTERS_ATTEMPTED: [],
        GP.TURNOVERS: [],
        GP.STEALS: [],
        GP.ASSISTS: [],
        GP.BLOCKS: [],
        GP.DEFENSIVE_REBOUNDS: [],
        GP.OFFENSIVE_REBOUNDS: [],
    }
    for _, row in boxscore.iterrows():
        game_player_dict[GT.GAME_ID].append(row[BOX.GAME_ID])
        game_player_dict[GP.TEAM_ID].append(row[BOX.TEAM_ID])
        game_player_dict[GP.PLAYER_ID].append(row[BOX.PLAYER_ID])
        game_player_dict[GP.PLAYER_NAME].append(row[BOX.PLAYER_NAME])
        game_player_dict[GP.FREE_THROWS_MADE].append(row[BOX.FTM])
        game_player_dict[GP.FREE_THROWS_ATTEMPTED].append(row[BOX.FTA])
        game_player_dict[GP.THREE_POINTERS_MADE].append(row[BOX.FG3M])
        game_player_dict[GP.THREE_POINTERS_ATTEMPTED].append(row[BOX.FG3A])
        game_player_dict[GP.TWO_POINTERS_MADE].append(row[BOX.FGM] - row[BOX.FG3M])
        game_player_dict[GP.TWO_POINTERS_ATTEMPTED].append(row[BOX.FGA] - row[BOX.FG3A])
        game_player_dict[GP.PLUS_MINUS].append(row[BOX.PLUS_MINUS])
        game_player_dict[GP.MINUTES].append(_get_minutes_played(box_row=row))
        game_player_dict[GP.POINTS].append(row[BOX.PTS])
        game_player_dict[GP.STEALS].append(row[BOX.STL])
        game_player_dict[GP.ASSISTS].append(row[BOX.AST])
        game_player_dict[GP.BLOCKS].append(row[BOX.BLK])
        game_player_dict[GP.TURNOVERS].append(row[BOX.TO])
        game_player_dict[GP.OFFENSIVE_REBOUNDS].append(row[BOX.OREB])
        game_player_dict[GP.DEFENSIVE_REBOUNDS].append(row[BOX.DREB])

    return pd.DataFrame.from_dict(game_player_dict)
