from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal

import pandas as pd


@dataclass
class GamePlayer:
    name: str
    id: str
    minutes: float
    points: int
    three_pointers_made: int
    three_pointers_attempted: int
    two_pointers_made: int
    two_pointers_attempted: int
    free_throws_made: int
    free_throws_attempted: int
    plus_minus: int


@dataclass
class GameTeam:
    name_abbreviation: str
    name: str
    opponent: str
    id: int
    location: str
    points: int
    opponent_points: int
    won: bool
    players: Optional[list[GamePlayer]] = None



@dataclass
class PlayByPlay:
    team_id: int



@dataclass
class Rotation:
    team_id: int

@dataclass
class TeamPossession:
    period: int
    seconds_remaining: int
    duration: int
    team_id: int
    in_possession: bool
    prior_play_ending: Literal['shot_miss', "rebound", "rebound_opponent", "score", "score_opponent", "foul", "foul_opponent", None]
    lineup: list[int]
    lineup_opponent: list[int]
    points: int
    points_opponent: int
    three_pointers_shot: int
    two_pointers_shot: int
    three_pointers_shot_opponent: int
    two_pointers_shot_opponent: int
    fouls: int
    fouls_opponent: int
    rebounds: int
    rebounds_opponent: int




@dataclass
class Game:
    id: str
    start_date: datetime.date
    season_id: int
    minutes: float
    teams: list[GameTeam]


@dataclass
class Possessions:
    play_by_plays: pd.DataFrame
    team_rotations: list[pd.DataFrame]
    inplay_lineups: pd.DataFrame
    posessions: pd.DataFrame
    play_lineups: list[pd.DataFrame]

