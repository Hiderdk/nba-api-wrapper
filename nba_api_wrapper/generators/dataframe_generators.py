import logging
from typing import Optional, Tuple

import pandas as pd

from nba_api_wrapper.api.data_models import RotationNames, TeamPossessionNames, TeamInPlayLineupNames, \
    ShotPlaysNames, PlayByPlay2Names, TransformedPlayByPlaysNames

RN = RotationNames
TP = TeamPossessionNames
TIPL = TeamInPlayLineupNames
SP = ShotPlaysNames
PBP = PlayByPlay2Names
TPBP = TransformedPlayByPlaysNames


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
        shot_distance = None
    return shot_distance


def _get_team_id(play_type: str, row: pd.Series, home_team_id, away_team_id, last_team_id):
    if play_type != 'end':
        if play_type == 'turnover':
            if row[PBP.HOMEDESCRIPTION]:
                team_id = home_team_id
            else:
                team_id = away_team_id

        else:

            team_id = int(row[PBP.PLAYER1_TEAM_ID]) if row[PBP.PLAYER1_TEAM_ID] else int(
                row[PBP.PLAYER2_TEAM_ID]) if \
                row[
                    PBP.PLAYER2_TEAM_ID] else int(row[
                                                      PBP.PLAYER3_TEAM_ID])
    else:
        team_id = last_team_id
    return team_id


def generate_transformed_play_by_plays(play_by_plays: pd.DataFrame, inplay_lineups: pd.DataFrame) -> pd.DataFrame:
    transformed_play_by_plays = {
        TPBP.SECONDS_PLAYED_START: [],
        TPBP.SECONDS_PLAYED_END: [],
        TPBP.SCORE: [],
        TPBP.SCORE_OPPONENT: [],
        TPBP.LINEUP: [],
        TPBP.LINEUP_OPPONENT: [],
        TPBP.TEAM_ID: [],
        TPBP.PLAY_END_REASON: [],
        TPBP.PRECEEDED_BY: [],
        TPBP.POINTS: [],
    }
    play_by_plays = play_by_plays.sort_values(by=PBP.SECONDS_PLAYED, ascending=True)
    play_by_plays = play_by_plays.reset_index(drop=True)
    play_start_seconds_played = None
    home_score = None
    away_score = None

    home_team_id = play_by_plays[
        (play_by_plays[PBP.HOMEDESCRIPTION] != '') &
        (play_by_plays[PBP.HOMEDESCRIPTION].notna()) &
        (play_by_plays[PBP.PLAYER1_TEAM_ID] != '') &
        (play_by_plays[PBP.PLAYER1_TEAM_ID].notna())][PBP.PLAYER1_TEAM_ID].iloc[0]

    away_team_id = play_by_plays[
        (play_by_plays[PBP.VISITORDESCRIPTION] != '') &
        (play_by_plays[PBP.VISITORDESCRIPTION].notna()) &
        (play_by_plays[PBP.PLAYER1_TEAM_ID].notna()) &
        (play_by_plays[PBP.PLAYER1_TEAM_ID] != '')][PBP.PLAYER1_TEAM_ID].iloc[0]

    last_team_id = None
    team_id = None

    prev_home_score = None
    prev_away_score = None

    for idx, row in play_by_plays.iterrows():
        seconds_played = row[PBP.SECONDS_PLAYED]
        description = row[PBP.HOMEDESCRIPTION] if row[PBP.HOMEDESCRIPTION] else row['VISITORDESCRIPTION'] if row[
            'VISITORDESCRIPTION'] else row['NEUTRALDESCRIPTION']
        play_type = _get_play_type_by_row(row=row, text_description=description)

        if play_start_seconds_played is None:
            play_start_seconds_played = seconds_played

        if play_type in ('miss', 'score', 'steal', 'turnover', 'end', 'offensive foul', 'foul'):

            team_id = _get_team_id(row=row, play_type=play_type, home_team_id=home_team_id, away_team_id=away_team_id,
                                   last_team_id=last_team_id)

            lineup_row = inplay_lineups[
                (inplay_lineups[TIPL.SECONDS_PLAYED_START] <= seconds_played) &
                (inplay_lineups[TIPL.SECONDS_PLAYED_END] >= seconds_played) &
                (inplay_lineups[TIPL.TEAM_ID] == team_id)
                ]
            if len(lineup_row) == 0:
                logging.warning("could not find any lineups")
                continue
            else:
                lineup = lineup_row[TIPL.LINEUP].tolist()[0]
                lineup_opponent = lineup_row[TIPL.LINEUP_OPPONENT].tolist()[0]

            points = 0

            if play_type == "score":
                away_score = int(row['SCORE'].split(" -")[0])
                home_score = int(row['SCORE'].split("- ")[1])

            if row[PBP.HOMEDESCRIPTION]:
                score = home_score
                score_opponent = away_score

                if prev_home_score is not None:
                    points = home_score - prev_home_score

            else:
                score = away_score
                score_opponent = home_score
                if prev_away_score is not None:
                    points = away_score - prev_away_score

            prev_away_score = away_score
            prev_home_score = home_score

            transformed_play_by_plays[TPBP.SECONDS_PLAYED_START].append(play_start_seconds_played)
            transformed_play_by_plays[TPBP.SECONDS_PLAYED_END].append(seconds_played)
            transformed_play_by_plays[TPBP.PLAY_END_REASON].append(play_type)
            transformed_play_by_plays[TPBP.SCORE].append(score)
            transformed_play_by_plays[TPBP.SCORE_OPPONENT].append(score_opponent)
            transformed_play_by_plays[TPBP.LINEUP].append(lineup)
            transformed_play_by_plays[TPBP.LINEUP_OPPONENT].append(lineup_opponent)
            transformed_play_by_plays[TPBP.TEAM_ID].append(team_id)
            transformed_play_by_plays[TPBP.POINTS].append(points)

            if idx > 0:
                prev_row = play_by_plays.iloc[idx - 1]
                prev_description = prev_row[PBP.HOMEDESCRIPTION] if prev_row[PBP.HOMEDESCRIPTION] else prev_row[
                    'VISITORDESCRIPTION'] if \
                    prev_row[
                        'VISITORDESCRIPTION'] else prev_row['NEUTRALDESCRIPTION']
                prev_play_type = _get_play_type_by_row(row=prev_row, text_description=prev_description)
            else:
                prev_play_type = None

            transformed_play_by_plays[TPBP.PRECEEDED_BY].append(prev_play_type)

        play_start_seconds_played = seconds_played
        last_team_id = team_id

    return pd.DataFrame.from_dict(transformed_play_by_plays)


def generate_shot_plays(play_by_plays: pd.DataFrame, inplay_lineups: pd.DataFrame) -> pd.DataFrame:
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
    }
    play_by_plays = play_by_plays.reset_index(drop=True)
    home_score = None
    away_score = None
    for ix, row in play_by_plays.iterrows():

        seconds_played = row[PBP.SECONDS_PLAYED]
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
        team_id = int(row[PBP.PLAYER1_TEAM_ID]) if row[PBP.PLAYER1_TEAM_ID] else int(row[PBP.PLAYER2_TEAM_ID]) if row[
            PBP.PLAYER2_TEAM_ID] else int(row[
                                              PBP.PLAYER3_TEAM_ID])

        if 'miss' in play_type:
            success = False
        else:
            success = True

        lineup_row = inplay_lineups[
            (inplay_lineups[TIPL.SECONDS_PLAYED_START] <= seconds_played) &
            (inplay_lineups[TIPL.SECONDS_PLAYED_END] > seconds_played) &
            (inplay_lineups[TIPL.TEAM_ID] == team_id)
            ]
        if len(lineup_row) == 0:
            logging.warning("could not find any lineups")
            continue
        else:
            lineup = lineup_row[TIPL.LINEUP].tolist()[0]
            lineup_opponent = lineup_row[TIPL.LINEUP_OPPONENT].tolist()[0]

        if play_type == "score":
            away_score = int(row['SCORE'].split(" -")[0])
            home_score = int(row['SCORE'].split("- ")[1])

        if row[PBP.HOMEDESCRIPTION]:
            score = home_score
            score_opponent = away_score
        else:
            score = away_score
            score_opponent = home_score

        shot_plays[SP.SHOT_TYPE].append(shot_attempt_type)
        shot_plays[SP.SECONDS_PLAYED].append(row[PBP.SECONDS_PLAYED])
        shot_plays[SP.PLAYER_ID].append(player_id)
        shot_plays[SP.TEAM_ID].append(team_id)
        shot_plays[SP.SHOT_DISTANCE].append(shot_distance)
        shot_plays[SP.SUCCESS].append(success)
        shot_plays[SP.LINEUP].append(lineup)
        shot_plays[SP.LINEUP_OPPONENT].append(lineup_opponent)
        shot_plays[SP.SCORE].append(score)
        shot_plays[SP.SCORE_OPPONENT].append(score_opponent)

    return pd.DataFrame.from_dict(shot_plays)


def generate_inplay_lineups(team_rotations: list[pd.DataFrame]) -> pd.DataFrame:
    inplay_lineups = {
        TIPL.TEAM_ID: [],
        TIPL.SECONDS_PLAYED_START: [],
        TIPL.SECONDS_PLAYED_END: [],
        TIPL.LINEUP: [],
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

            in_player_ids = game_team_rotation[game_team_rotation[RN.IN_TIME_SECONDS_PLAYED] == seconds_played_start][
                RN.PERSON_ID].unique().tolist()
            out_player_ids = game_team_rotation[game_team_rotation[RN.OUT_TIME_SECONDS_PLAYED] == seconds_played_start][
                RN.PERSON_ID].unique().tolist()

            for out_player_id in out_player_ids:
                team_current_lineup[team_id].remove(out_player_id)

            for in_player_id in in_player_ids:
                if in_player_id in team_current_lineup[team_id]:
                    logging.warning(f"player {in_player_id} already in lineup")
                    continue
                team_current_lineup[team_id].append(in_player_id)

        if idx + 1 == len(switch_times):
            seconds_played_end = game_seconds_duration
        else:
            seconds_played_end = switch_times[idx + 1]

        for team_id, lineup in team_current_lineup.items():
            lineup_opponent = [team_current_lineup[t] for t in team_current_lineup if t != team_id][0]
            if len(lineup) != 5:
                raise ValueError("lineup doesn't have 5 players")
            if len(lineup_opponent) != 5:
                raise ValueError("lineup doesn't have 5 players")
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
