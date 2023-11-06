import datetime
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from nba_api_wrapper.data_models import PosessionNames, LGFDataNames
from nba_api_wrapper.generators.api_bridge import ApiBridge

PN = PosessionNames

LFG = LGFDataNames

@dataclass
class CollectedData:
    possession_attempts: pd.DataFrame
    offense_player_play_by_plays: pd.DataFrame
    defense_player_play_by_plays: pd.DataFrame
    possessions: pd.DataFrame
    game_teams: pd.DataFrame
    game_players: pd.DataFrame
    game: pd.DataFrame




def games_scorer(
        min_date: str = "2023-10-22",
        max_date: Optional[str] = None,
) -> CollectedData:
    if max_date is None:
        max_date_time = datetime.datetime.now()
    else:
        max_date_time = datetime.datetime.strptime(max_date, "%Y-%m-%d")


    bridge = ApiBridge()
    league_games = bridge.generate_league_games(min_date=datetime.datetime.strptime(min_date, "%Y-%m-%d"),
                                                max_date=max_date_time)

    possessions = []
    game_players = []
    game_teams = []
    offense_player_play_by_plays = []
    defense_player_play_by_plays = []
    possession_attempts = []
    games = []

    game_ids = league_games[LFG.GAME_ID].unique().tolist()
    for game_id in game_ids:
        boxscore = bridge.generate_boxscore(game_id=game_id, league_games=league_games)
        play_by_play = bridge.generate_play_by_play(game_id=game_id)


        possessions.append(play_by_play.possessions)
        offense_player_play_by_plays.append(play_by_play.offense_player_play_by_plays)
        defense_player_play_by_plays.append(play_by_play.defense_player_play_by_plays)
        possession_attempts.append(play_by_play.possessions)
        game_teams.append(boxscore.game_teams)
        game_players.append(boxscore.game_players)
        games.append(boxscore.game)

    return CollectedData(
        possessions=pd.concat(possessions),
        game_teams=pd.concat(game_teams),
        game_players = pd.concat(game_players),
        offense_player_play_by_plays=pd.concat(offense_player_play_by_plays),
        defense_player_play_by_plays=pd.concat(defense_player_play_by_plays),
        possession_attempts=pd.concat(possession_attempts),
        game=pd.concat(games)
    )
