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
class Boxscore:
    id: str
    game_teams: pd.DataFrame
    game_players: pd.DataFrame
    game: pd.DataFrame


@dataclass
class PlayByPlay:
    play_by_plays: pd.DataFrame
    shot_plays: pd.DataFrame
    team_rotations: list[pd.DataFrame]
    inplay_lineups: pd.DataFrame
    possession_attempts: pd.DataFrame
    offense_player_play_by_plays: pd.DataFrame
    defense_player_play_by_plays: pd.DataFrame
    possessions: pd.DataFrame

@dataclass
class CollectedData:
    possession_attempts: pd.DataFrame
    offense_player_play_by_plays: pd.DataFrame
    defense_player_play_by_plays: pd.DataFrame
    possessions: pd.DataFrame
    game_teams: pd.DataFrame
    game_players: pd.DataFrame
    game: pd.DataFrame

