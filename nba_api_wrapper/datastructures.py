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
class Game:
    id: str
    start_date: datetime.date
    season_id: int
    minutes: float
    teams: list[GameTeam]


@dataclass
class PlayByPlay:
    play_by_plays: pd.DataFrame
    shot_plays: pd.DataFrame
    team_rotations: list[pd.DataFrame]
    inplay_lineups: pd.DataFrame
    transformed_play_by_plays: pd.DataFrame

