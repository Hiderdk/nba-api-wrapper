import logging
from typing import Optional

import pandas as pd

from nba_api_wrapper.api.data_models import LGFDataNames, RotationNames, TeamPossessionNames, TeamInPlayLineupNames, \
    ShotPlaysNames, PlayByPlay2Names

RN = RotationNames
TP = TeamPossessionNames
TIPL = TeamInPlayLineupNames
SP = ShotPlaysNames
PBP = PlayByPlay2Names


def _get_play_type_by_row(text_description: str, row: pd.Series) -> Optional[str]:
    play_type = None
    if 'MISS' in text_description:
        play_type = 'miss'
    elif 'REBOUND' in text_description or 'Rebound' in text_description:
        play_type = "rebound"
    elif row['SCORE'] is not None and 'End of' not in text_description and 'Start of' not in text_description:
        play_type = "score"
    elif 'FOUL' in text_description:
        play_type = "foul"
    elif 'Offensive Foul' in text_description:
        play_type = 'offensive foul'
    elif 'Turnover' in text_description:
        play_type = 'turnover'
    elif 'Timeout' in text_description:
        play_type = 'timeout'
    elif 'STEAL' in text_description:
        play_type = 'steal'
    elif 'SUB' in text_description:
        play_type = 'sub'
    elif 'Start' in text_description:
        play_type = 'start'
    elif 'End' in text_description:
        play_type = 'end'
    elif 'Jump Ball' in text_description:
        play_type = 'jump ball'

    return play_type


def _get_shot_attempt_type_by_text_description_and_play_type(text_description: str, play_type) -> Optional[str]:
    shot_attempt_type = None
    if 'Free Throw' in text_description:
        shot_attempt_type = "Free Throw"
    elif '3PT' in text_description:
        shot_attempt_type = '3pt'
    elif play_type in ('miss', 'score'):
        shot_attempt_type = '2pt'
    return shot_attempt_type


def _get_shot_distance_by_text_description(text_description: str):
    if "'" in text_description:
        shot_distance = text_description.split("' ")[0]
        shot_distance = shot_distance[len(shot_distance) - 2:]
        if shot_distance[0] == " ":
            shot_distance = shot_distance[1:]
        try:
            shot_distance = int(shot_distance)
        except:
            shot_distance = None
    else:
        logging.warning("could not get shot distance")
        shot_distance = None
    return shot_distance


def generate_shot_plays(play_by_plays: pd.DataFrame):
    shot_plays = {
        SP.SECONDS_PLAYED: [],
        SP.SCORE: [],
        SP.SCORE_OPPONENT: [],
        SP.LINEUP: [],
        SP.LINEUP_OPPONENT: [],
        SP.TEAM_ID: [],
        SP.PLAYER_ID: [],
        SP.SHOT_TYPE: [],
        SP.SHOT_DISTANCE: [],
        SP.SUCCESS: [],
        SP.PRECEEDING_PLAY: [],
        SP.SUCCEEDING_PLAY: [],
    }
    for ix, row in play_by_plays.iterrows():
        description = row[PBP.HOMEDESCRIPTION] if row[PBP.HOMEDESCRIPTION] else row['VISITORDESCRIPTION'] if row[
            'VISITORDESCRIPTION'] else row['NEUTRALDESCRIPTION']

        play_type = _get_play_type_by_row(row=row, text_description=description)
        if play_type not in ('miss', 'score'):
            continue
        shot_attempt_type = _get_shot_attempt_type_by_text_description_and_play_type(text_description=description,
                                                                                     play_type=play_type)
        if shot_attempt_type in ('2pt', '3pt'):
            shot_distance = _get_shot_distance_by_text_description(text_description=description)
        else:
            shot_distance = None

        player_id = row[PBP.PLAYER1_ID] if row[PBP.PLAYER1_ID] else row[PBP.PLAYER2_ID] if row[PBP.PLAYER2_ID] else row[
            PBP.PLAYER3_ID]
        team_id = row[PBP.PLAYER1_TEAM_ID] if row[PBP.PLAYER1_TEAM_ID] else row[PBP.PLAYER2_TEAM_ID] if row[
            PBP.PLAYER2_TEAM_ID] else row[
            PBP.PLAYER3_TEAM_ID]

        shot_plays[SP.SHOT_TYPE].append(shot_attempt_type)
        shot_plays[SP.SECONDS_PLAYED].append(row[PBP.SECONDS_PLAYED])
        shot_plays[SP.PLAYER_ID].append(player_id)
        shot_plays[SP.TEAM_ID].append(team_id)
        shot_plays[SP.SHOT_DISTANCE].append(shot_distance)


def generate_player_inplay_lineups(inplay_lineups: pd.DataFrame, ):


def generate_inplay_lineups(team_rotations: list[pd.DataFrame]) -> pd.DataFrame:
    inplay_lineups = {
        TIPL.TEAM_ID: [],
        TIPL.LINEUP: [],
        TIPL.SECONDS_PLAYED_START: [],
        TIPL.SECONDS_PLAYED_END: [],
        TIPL.LINEUP_OPPONENT: [],
    }
    game_rotations = pd.concat(team_rotations)

    players_in = []
    game_rotations = game_rotations.sort_values(by=[RN.IN_TIME_SECONDS_PLAYED, RN.OUT_TIME_SECONDS_PLAYED],
                                                ascending=True)

    switch_times = game_rotations[RN.IN_TIME_SECONDS_PLAYED].unique().tolist()
    team_ids = game_rotations[RN.TEAM_ID].unique().tolist()

    game_seconds_duration = game_rotations[RN.OUT_TIME_SECONDS_PLAYED].max()

    team_current_lineup = {t: [] for t in team_ids}
    for idx, seconds_played_start in enumerate(switch_times):
        for team_id in team_ids:
            game_team_rotation = game_rotations[game_rotations[RN.TEAM_ID] == team_id]

            in_players = game_team_rotation[game_team_rotation[RN.IN_TIME_SECONDS_PLAYED] == seconds_played_start][
                RN.PERSON_ID].unique().tolist()
            out_players = game_team_rotation[game_team_rotation[RN.OUT_TIME_SECONDS_PLAYED] == seconds_played_start][
                RN.PERSON_ID].unique().tolist()

            for out_player in out_players:
                team_current_lineup[team_id].remove(out_player)

            for in_player in in_players:
                if in_player in players_in:
                    h = 2
                team_current_lineup[team_id].append(in_player)

        if idx + 1 == len(switch_times):
            seconds_played_end = game_seconds_duration
        else:
            seconds_played_end = switch_times[idx + 1]

        for team_id, lineup in team_current_lineup.items():
            lineup_opponent = [team_current_lineup[t] for t in team_current_lineup if t != team_ids][0]
            if len(lineup) != 5:
                h = 2
            if len(lineup_opponent) != 5:
                h = 2
            inplay_lineups[TIPL.LINEUP].append(lineup)
            inplay_lineups[TIPL.LINEUP_OPPONENT].append(lineup_opponent)
            inplay_lineups[TIPL.TEAM_ID].append(team_id)
            inplay_lineups[TIPL.SECONDS_PLAYED_START].append(seconds_played_start)
            inplay_lineups[TIPL.SECONDS_PLAYED_END].append(seconds_played_end)

    return pd.DataFrame.from_dict(inplay_lineups)


def generate_team_possessions(play_by_plays: pd.DataFrame, team_rotations: list[pd.DataFrame]) -> list[pd.DataFrame]:
    team_possessions_dict = {
        TP.PERIOD: [],
        TP.SECONDS_REMAINING: [],
        TP.DURATION: [],
        TP.TEAM_ID: [],
        TP.IN_POSSESSION: [],
        TP.PRIOR_PLAY_ENDING: [],
        TP.LINEUP: [],
        TP.LINEUP_OPPONENT: [],
        TP.POINTS: [],
        TP.POINTS_OPPONENT: [],
        TP.THREE_POINTERS_SHOT: [],
        TP.TWO_POINTERS_SHOT: [],
        TP.THREE_POINTERS_SHOT_OPPONENT: [],
        TP.TWO_POINTERS_SHOT_OPPONENT: [],
        TP.FOULS: [],
        TP.FOULS_OPPONENT: [],
        TP.REBOUNDS: [],
        TP.REBOUNDS_OPPONENT: []
    }
    for _, play_by_play in play_by_plays.iterrows():
        pass

    for team_rotation in team_rotations:
        team_rotation = team_rotation.sort_values(by=[RN.IN_TIME_REAL, RN.OUT_TIME_REAL], ascending=True)
