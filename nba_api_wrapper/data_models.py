from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Union


@dataclass
class LGFDataNames:
    SEASON_ID = 'SEASON_ID'
    TEAM_ID = 'TEAM_ID'
    TEAM_ABBREVIATION = "TEAM_ABBREVIATION"
    TEAM_NAME = "TEAM_NAME"
    GAME_ID = "GAME_ID"
    GAME_DATE = "GAME_DATE"
    MATCHUP = "MATCHUP"
    MINUTES = "MIN"
    POINTS = "PTS"
    WIN_LOSS = "WL"


@dataclass
class BoxscoreV2Names:
    GAME_ID = "GAME_ID"
    TEAM_ID = "TEAM_ID"
    TEAM_ABBREVIATION = "TEAM_ABBREVIATION"
    PLAYER_ID = "PLAYER_ID"
    PLAYER_NAME = "PLAYER_NAME"
    START_POSITION = "START_POSITION"
    MIN = "MIN"
    FGM = "FGM"
    FGA = "FGA"
    FG3M = "FG3M"
    FG3A = "FG3A"
    FTM = "FTM"
    FTA = "FTA"
    OREB = "OREB"
    DREB = "DREB"
    AST = "AST"
    STL = "STL"
    BLK = "BLK"
    TO = "TO"
    PF = "PF"
    PTS = "PTS"
    PLUS_MINUS = "PLUS_MINUS"


@dataclass
class BoxscoreAdvV2Names:
    GAME_ID = "GAME_ID"
    TEAM_ID = "TEAM_ID"
    TEAM_ABBREVIATION = "TEAM_ABBREVIATION"
    PLAYER_ID = "PLAYER_ID"
    PLAYER_NAME = "PLAYER_NAME"
    START_POSITION = "START_POSITION"
    MIN = "MIN"
    E_OFF_RATING = "E_OFF_RATING"
    OFF_RATING = "OFF_RATING"
    E_DEF_RATING = "E_DEF_RATING"
    DEF_RATING = "DEF_RATING"
    E_NET_RATING = "E_NET_RATING"
    NET_RATING = "NET_RATING"
    AST_PCT = "AST_PCT"
    AST_TOV = "AST_TOV"
    AST_RATIO = "AST_RATIO"
    OREB_PCT = "OREB_PCT"
    DREB_PCT = "DREB_PCT"
    REB_PCT = "REB_PCT"
    TM_TOV_PCT = "TM_TOV_PCT"
    EFG_PCT = "EFG_PCT"
    TS_PCT = "TS_PCT"
    USG_PCT = "USG_PCT"
    E_USG_PCT = "E_USG_PCT"
    E_PACE = "E_PACE"
    PACE = "PACE"
    POSS = "POSS"
    PACE_PER40 = "PACE_PER40"
    PIE = "PIE"


@dataclass
class BoxscoreAdvV2TeamNames:
    GAME_ID = "GAME_ID"
    TEAM_ID = "TEAM_ID"
    TEAM_NAME = "TEAM_NAME"
    TEAM_ABBREVIATION = "TEAM_ABBREVIATION"
    MIN = "MIN"
    E_OFF_RATING = "E_OFF_RATING"
    OFF_RATING = "OFF_RATING"
    E_DEF_RATING = "E_DEF_RATING"
    DEF_RATING = "DEF_RATING"
    E_NET_RATING = "E_NET_RATING"
    NET_RATING = "NET_RATING"
    AST_PCT = "AST_PCT"
    AST_TOV = "AST_TOV"
    AST_RATIO = "AST_RATIO"
    OREB_PCT = "OREB_PCT"
    DREB_PCT = "DREB_PCT"
    REB_PCT = "REB_PCT"
    E_TM_TOV_PCT = "E_TM_TOV_PCT"
    TM_TOV_PCT = "TM_TOV_PCT"
    EFG_PCT = "EFG_PCT"
    TS_PCT = "TS_PCT"
    USG_PCT = "USG_PCT"
    E_USG_PCT = "E_USG_PCT"
    E_PACE = "E_PACE"
    PACE = "PACE"
    PACE_PER40 = "PACE_PER40"
    POSS = "POSS"
    PIE = "PIE"


@dataclass
class PlayByPlay2Model:
    GAME_ID = "GAME_ID"
    HOMEDESCRIPTION = "HOMEDESCRIPTION"
    VISITORDESCRIPTION = "VISITORDESCRIPTION"
    NEUTRALDESCRIPTION = "NEUTRALDESCRIPTION"
    SECONDS_PLAYED = "SECONDS_PLAYED"
    SCORE = "SCORE"
    PLAYER1_ID = "PLAYER1_ID"
    PLAYER1_NAME = "PLAYER1_NAME"
    PLAYER1_TEAM_ID = "PLAYER1_TEAM_ID"
    PLAYER2_ID = "PLAYER2_ID"
    PLAYER2_NAME = "PLAYER2_NAME"
    PLAYER2_TEAM_ID = "PLAYER2_TEAM_ID"
    PLAYER3_ID = "PLAYER3_ID"
    PLAYER3_NAME = "PLAYER3_NAME"
    PLAYER3_TEAM_ID = "PLAYER3_TEAM_ID"
    EVENTNUM = "EVENTNUM"
    POSSESSION_ID = "possession_id"
    POSSESSION_ATTEMPT_ID = "possession_attempt_id"


@dataclass
class ShotPlaysModel:
    GAME_ID = "GAME_ID"
    SECONDS_PLAYED = "SECONDS_PLAYED"
    SCORE = "SCORE"
    SCORE_OPPONENT = "SCORE_OPPONENT"
    TEAM_ID = "TEAM_ID"
    PLAYER_ID = "PLAYER_ID"
    LINEUP = "LINEUP"
    LINEUP_OPPONENT = "LINEUP_OPPONENT"
    SHOT_DISTANCE = "DISTANCE"
    SUCCESS = "SUCCESS"
    SHOT_TYPE = "SHOT_TYPE"
    INPLAY_ID = "INPLAY_ID"


@dataclass
class RotationNames:
    GAME_ID = "GAME_ID"
    TEAM_ID = "TEAM_ID"
    PERSON_ID = "PERSON_ID"
    IN_TIME_REAL = "IN_TIME_REAL"
    OUT_TIME_REAL = "OUT_TIME_REAL"
    PLAYERS_PTS = "PLAYERS_PTS"
    PD_DIFF = "PT_DIFF"
    IN_TIME_SECONDS_PLAYED = "IN_TIME_SECONDS_PLAYED"
    OUT_TIME_SECONDS_PLAYED = "OUT_TIME_SECONDS_PLAYED"


@dataclass
class PosessionModel:
    GAME_ID = "game_id"
    START_TIME_SECONDS = "start_time_seconds"
    END_TIME_SECONDS = "end_time_seconds"
    TEAM_ID_OFFENSE = "team_id_offense"
    TEAM_ID_DEFENSE = "team_id_defense"
    LINEUP_OFFENSE = "lineup_offense"
    LINEUP_DEFENSE = "lineup_defense"
    POINTS_OFFENSE = "points_offense"
    LINEUP_ID_OFFENSE = "lineup_id_offense"
    LINEUP_ID_DEFENSE = "lineup_id_defense"
    THREE_POINTERS_MADE = "three_pointers_made"
    THREE_POINTERS_ATTEMPTED = "three_pointers_attempted"
    TWO_POINTERS_MADE = "two_pointers_made"
    TWO_POINTERS_ATTEMPTED = "two_pointers_attempted"
    FREE_THROWS_MADE = "free_throws_made"
    FREE_THROWS_ATTEMPTED = "free_throws_attempted"
    PLUS_MINUS = "plus_minus"
    BLOCKS = "blocks"
    STEALS = "steals"
    ASSISTS = "assists"
    OFFENSIVE_REBOUNDS = "offensive_rebounds"
    DEFENSIVE_REBOUNDS = "defensive_rebounds"
    TURNOVERS = "turnovers"
    PERIOD = "period"


@dataclass
class TeamInPlayLineupNames:
    GAME_ID = "game_id"
    TEAM_ID = "team_id"
    PERIOD = "period"
    SECONDS_PLAYED_START = "seconds_played_start"
    LINEUP_ID = "lineup_id"
    LINEUP_ID_OPPONENT = "lineup_id_opponent"
    SECONDS_PLAYED_END = "seconds_played_end"
    LINEUP = "lineup"
    LINEUP_OPPONENT = "lineup_opponent"
    INPLAY_ID = "inplay_id"


@dataclass
class LineupPlayByPlaysNames:
    GAME_ID = "game_id"
    TEAM_ID_OFFENSE = "team_id_offense"
    TEAM_ID_DEFENSE = "team_id_defense"
    POSSESSION_ID = "possession_id"
    POSSESSION_ATTEMPT_ID = "possession_attempt_id"
    SCORE_OFFENSE = "score_offense"
    SCORE_DEFENSE = "score_defense"
    SECONDS_PLAYED_START = "seconds_played_start"
    SECONDS_PLAYED_END = "seconds_played_end"
    FIELD_GOAL_ATTEMPTS = "field_goal_attempts"
    POINTS = "points"
    FREE_THROW_ATTEMPTS = "free_throw_attempts"
    LINEUP_ID_OFFENSE = "lineup_id_offense"
    LINEUP_ID_DEFENSE = "lineup_id_defense"
    INPLAY_ID = "inplay_id"
    PLAY_END_REASON = "play_end_reason"


@dataclass
class PosessionNames:
    GAME_ID = "game_id"
    TEAM_ID_OFFENSE = "team_id_offense"
    TEAM_ID_DEFENSE = "team_id_defense"
    POSSESSION_ID = "possession_id"
    SECONDS_PLAYED_START = "seconds_played_start"
    SECONDS_PLAYED_END = "seconds_played_end"
    LINEUP_OFFENSE = "lineup_offense"
    LINEUP_DEFENSE = "lineup_defense"
    POINTS = "points"
    FIELD_GOAL_ATTEMPTS = "field_goal_attempts"
    FREE_THROW_ATTEMPTS = "free_throw_attempts"
    SCORE_OFFENSE = "score_offense"
    SCORE_DEFENSE = "score_defense"


@dataclass
class PlayerOffensePlayByPlaysNames:
    GAME_ID = "game_id"
    TEAM_ID = "team_id"
    POSSESSION_ID = "possession_id"
    PLAYER_ID = "player_id"
    POINTS = "player_points"
    ASSISTS = "player_assists"
    REBOUNDS = "player_rebounds"
    TURNOVERS = "player_turnovers"
    FOULS = "player_fouls"
    THREE_POINTERS_ATTEMPTED = "player_three_pointers_attempted"
    THREE_POINTERS_MADE = "player_three_pointers_made"
    TWO_POINTERS_ATTEMPTED = "player_two_pointers_attempted"
    TWO_POINTERS_MADE = "player_two_pointers_made"
    FREE_THROWS_ATTEMPTED = "player_free_throws_attempted"
    FREE_THROWS_MADE = "player_free_throws_made"


@dataclass
class PlayerDefensePlayByPlaysNames:
    GAME_ID = "game_id"
    TEAM_ID = "team_id"
    POSSESSION_ID = "possession_id"
    PLAYER_ID = "player_id"
    REBOUNDS = "player_rebounds"
    BLOCKS = "player_blocks"
    STEALS = "player_steals"
    FOULS = "player_fouls"


@dataclass
class GamePlayerModel():
    PLAYER_ID = "player_id"
    GAME_ID = "game_id"
    TEAM_ID = "team_id"
    TEAM_NAME = "team_name"
    PLAYER_NAME = "player_name"


@dataclass
class NBAPBPGamePlayerModel(GamePlayerModel):
    START_POSITION = "start_position"
    MINUTES = "minutes"
    POINTS = "points"
    THREE_POINTERS_MADE = "three_pointers_made"
    THREE_POINTERS_ATTEMPTED = "three_pointers_attempted"
    TWO_POINTERS_MADE = "two_pointers_made"
    TWO_POINTERS_ATTEMPTED = "two_pointers_attempted"
    FREE_THROWS_MADE = "free_throws_made"
    FREE_THROWS_ATTEMPTED = "free_throws_attempted"
    PLUS_MINUS = "plus_minus"
    BLOCKS = "blocks"
    STEALS = "steals"
    ASSISTS = "assists"
    OFFENSIVE_REBOUNDS = "offensive_rebounds"
    DEFENSIVE_REBOUNDS = "defensive_rebounds"
    TURNOVERS = "turnovers"
    FOULS = "fouls"
    PACE = "pace"
    POSS = "possessions"
    E_PACE = "e_pace"


@dataclass
class GameTeamModel():
    GAME_ID = "game_id"
    TEAM_ID = "team_id"
    TEAM_NAME = "team_name"
    TEAM_ID_OPPONENT = "team_id_opponent"
    WON = "won"


@dataclass
class NbaPbPGameTeamModel(GameTeamModel):
    LOCATION = "location"
    SCORE = "score"
    SCORE_OPPONENT = "score_opponent"
    PACE = "pace"
    E_PACE = "e_pace"
    POSS = "possessions"
    PIE = "pie"


@dataclass
class GameModel:
    GAME_ID = "game_id"
    START_DATE = "start_date"
    MINUTES = "minutes"


@dataclass
class LineupNames:
    LINEUP_ID = "lineup_id"
    LINEUP = "lineup"
