import logging
from typing import Optional, Tuple

import pandas as pd

from nba_api_wrapper.data_models import RotationNames, TeamPossessionNames, TeamInPlayLineupNames, \
    ShotPlaysNames, PlayByPlay2Names, LineupPlayByPlaysNames, PlayerOffensePlayByPlaysNames, \
    PlayerDefensePlayByPlaysNames

RN = RotationNames
TP = TeamPossessionNames
TIPL = TeamInPlayLineupNames
SP = ShotPlaysNames
PBP = PlayByPlay2Names
LPBP = LineupPlayByPlaysNames
POPBP = PlayerOffensePlayByPlaysNames
PDPBP = PlayerDefensePlayByPlaysNames


def _get_play_type_by_row(text_description: str, row: pd.Series) -> Optional[str]:
    play_type = None
    if text_description is None:
        return None
    if 'MISS' in text_description:
        play_type = 'miss'
    elif 'REBOUND' in text_description or 'Rebound' in text_description:
        play_type = 'rebound'

    elif row['SCORE'] is not None and 'End of' not in text_description and 'Start of' not in text_description:
        play_type = "score"
    elif 'FOUL' in text_description:
        play_type = "defensive foul"
    elif 'offensive foul' in text_description:
        play_type = "offensive foul"
    elif 'Turnover' in text_description:
        play_type = 'turnover'
    elif 'Timeout' in text_description:
        play_type = 'timeout'
    elif 'STEAL' in text_description:
        play_type = 'steal'
    elif 'BLOCK' in text_description:
        play_type = 'block'
    elif 'SUB' in text_description:
        play_type = 'sub'
    elif 'Start' in text_description:
        play_type = 'start'
    elif 'End' in text_description:
        play_type = 'end'
    elif 'STEAL' in text_description:
        play_type = 'steal'
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


def generate_offense_player_play_by_plays(play_by_plays: pd.DataFrame,
                                          lineup_play_by_plays: pd.DataFrame) -> pd.DataFrame:
    offense_player_play_by_plays = {
        POPBP.POINTS: [],
        #  POPBP.ASSISTS: [],
        POPBP.FOULS: [],
        POPBP.REBOUNDS: [],
        POPBP.PLAYER_ID: [],
        POPBP.TEAM_ID: [],
    }
    tot_points = 0
    for lineup_idx, row in lineup_play_by_plays.iterrows():

        defensive_players = row[LPBP.LINEUP_OFFENSE]

        for player_id in defensive_players:

            if player_id == 203076 and lineup_idx ==27:
                i = 2

            play_rows = play_by_plays[
                (play_by_plays[PBP.PLAYER1_ID] == player_id) &
                (play_by_plays[PBP.POSSESSION_ATTEMPT_ID] == row[LPBP.POSSESSION_ATTEMPT_ID])

                ]

            rebounds = 0
            fouls = 0
            points = 0

            for play_row_idx, play_row in play_rows.iterrows():
                home_description = play_row[PBP.HOMEDESCRIPTION]
                away_description = play_row[PBP.VISITORDESCRIPTION]

                home_play_type = _get_play_type_by_row(text_description=home_description, row=play_row)
                away_play_type = _get_play_type_by_row(text_description=away_description, row=play_row)

                if home_play_type is not None and home_play_type in (
                        'score', 'miss', 'rebound', 'offensive foul'):
                    play_type = home_play_type
                    description = home_description
                elif away_play_type is not None and away_play_type in (
                        'score', 'miss', 'rebound', 'offensive foul'):
                    play_type = away_play_type
                    description = away_description
                else:
                    continue

                if play_type == 'rebound':
                    if play_type == 'rebound':
                        miss_is_home = play_row[PBP.HOMEDESCRIPTION] is not None
                        if miss_is_home and play_by_plays.iloc[play_row_idx - 1][PBP.HOMEDESCRIPTION]:
                            rebounds += 1
                        elif not miss_is_home and play_by_plays.iloc[play_row_idx - 1][PBP.VISITORDESCRIPTION]:
                            rebounds += 1

                elif play_type == 'offensive foul':
                    fouls += 1
                elif play_type == 'score':

                    if 'Free Throw' in description:
                        points += 1
                        tot_points += 1
                    elif '3PT' in description:
                        points += 3
                        tot_points += 3
                    elif play_row[PBP.SCORE]:
                        points += 2
                        tot_points +=2
                    else:
                        i = 2


            offense_player_play_by_plays[POPBP.FOULS].append(fouls)
            offense_player_play_by_plays[POPBP.POINTS].append(points)
            offense_player_play_by_plays[POPBP.REBOUNDS].append(rebounds)
            offense_player_play_by_plays[POPBP.PLAYER_ID].append(player_id)
            offense_player_play_by_plays[POPBP.TEAM_ID].append(row[LPBP.TEAM_ID])

    return pd.DataFrame.from_dict(offense_player_play_by_plays)


def generate_defense_player_play_by_plays(play_by_plays: pd.DataFrame,
                                          lineup_play_by_plays: pd.DataFrame) -> pd.DataFrame:
    defense_player_play_by_plays = {
        PDPBP.FOULS: [],
        PDPBP.STEALS: [],
        PDPBP.BLOCKS: [],
        PDPBP.REBOUNDS: [],
        PDPBP.PLAYER_ID: [],
        PDPBP.TEAM_ID: [],
    }

    for lineup_idx, row in lineup_play_by_plays.iterrows():

        defensive_players = row[LPBP.LINEUP_DEFENSE]

        for player_id in defensive_players:

            play_rows = play_by_plays[
                (play_by_plays[PBP.PLAYER1_ID] == player_id) &
                (play_by_plays[PBP.POSSESSION_ATTEMPT_ID] == row[LPBP.POSSESSION_ATTEMPT_ID]) |
                (play_by_plays[PBP.PLAYER2_ID] == player_id) &
                (play_by_plays[PBP.POSSESSION_ATTEMPT_ID] == row[LPBP.POSSESSION_ATTEMPT_ID]) |
                (play_by_plays[PBP.PLAYER3_ID] == player_id) &
                (play_by_plays[PBP.POSSESSION_ATTEMPT_ID] == row[LPBP.POSSESSION_ATTEMPT_ID])
                ]

            rebounds = 0
            fouls = 0
            steals = 0
            blocks = 0

            for play_row_idx, play_row in play_rows.iterrows():
                home_description = play_row[PBP.HOMEDESCRIPTION]
                away_description = play_row[PBP.VISITORDESCRIPTION]

                home_play_type = _get_play_type_by_row(text_description=home_description, row=play_row)
                away_play_type = _get_play_type_by_row(text_description=away_description, row=play_row)

                if home_play_type is not None and home_play_type in (
                        'rebound', 'steal', 'block', 'defensive foul'):
                    play_type = home_play_type
                    description = away_description
                elif away_play_type is not None and away_play_type in (
                        'rebound', 'steal', 'block', 'defensive foul'):
                    play_type = away_play_type
                    description = away_description
                else:
                    continue

                if play_type == 'rebound':
                    if play_type == 'rebound':
                        miss_is_home = play_row[PBP.HOMEDESCRIPTION] is not None
                        if miss_is_home and play_by_plays.iloc[play_row_idx - 1][PBP.VISITORDESCRIPTION]:
                            rebounds += 1
                        elif not miss_is_home and play_by_plays.iloc[play_row_idx - 1][PBP.HOMEDESCRIPTION]:
                            rebounds += 1

                elif play_type == 'defensive foul':
                    fouls += 1
                elif play_type == 'steal':
                    steals += 1
                elif play_type == 'block':
                    blocks += 1

            defense_player_play_by_plays[PDPBP.FOULS].append(fouls)
            defense_player_play_by_plays[PDPBP.STEALS].append(steals)
            defense_player_play_by_plays[PDPBP.BLOCKS].append(blocks)
            defense_player_play_by_plays[PDPBP.REBOUNDS].append(rebounds)
            defense_player_play_by_plays[PDPBP.PLAYER_ID].append(player_id)
            defense_player_play_by_plays[PDPBP.TEAM_ID].append(row[LPBP.TEAM_ID])

    return pd.DataFrame.from_dict(defense_player_play_by_plays)


def generate_lineup_possession_attempts(play_by_plays: pd.DataFrame,
                                        inplay_lineups: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    lineup_possession_attempts = {
        LPBP.TEAM_ID: [],
        LPBP.SCORE_OFFENSE: [],
        LPBP.POSSESSION_ID: [],
        LPBP.POSSESSION_ATTEMPT_ID: [],
        LPBP.SCORE_DEFENSE: [],
        LPBP.LINEUP_OFFENSE: [],
        LPBP.LINEUP_DEFENSE: [],
        LPBP.SECONDS_PLAYED_START: [],
        LPBP.SECONDS_PLAYED_END: [],
        LPBP.POINTS: [],
        #   LPBP.TEAM_PREV_POSSESION: [],
        LPBP.PLAY_END_REASON: [],
        #   LPBP.PRECEEDED_BY: [],
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

    possession_attempt_id = 1
    possession_id = 1
    for idx, row in play_by_plays.iterrows():

        if len(lineup_possession_attempts[LPBP.POSSESSION_ATTEMPT_ID]) == 133:
            i = 2

        seconds_played = row[PBP.SECONDS_PLAYED]
        description = row[PBP.HOMEDESCRIPTION] if row[PBP.HOMEDESCRIPTION] else row['VISITORDESCRIPTION'] if row[
            'VISITORDESCRIPTION'] else row['NEUTRALDESCRIPTION']
        play_type = _get_play_type_by_row(row=row, text_description=description)

        if play_start_seconds_played is None:
            play_start_seconds_played = seconds_played

        if play_type in ('miss',
                         'score', 'steal', 'turnover', 'end', 'offensive foul') or 'Free Throw 1 of 1' in description \
                or 'Free Throw 2 of 2' in description or 'Free Throw 3 of 3' in description:

            team_id = _get_team_id(row=row, play_type=play_type, home_team_id=home_team_id, away_team_id=away_team_id,
                                   last_team_id=last_team_id)

            lineup_row = inplay_lineups[
                (inplay_lineups[TIPL.SECONDS_PLAYED_START] < seconds_played) &
                (inplay_lineups[TIPL.SECONDS_PLAYED_END] >= seconds_played) &
                (inplay_lineups[TIPL.TEAM_ID] == team_id)
                ]
            if len(lineup_row) == 0:
                logging.warning("could not find any lineups")
                continue
            else:
                lineup = lineup_row[TIPL.LINEUP].tolist()[0]
                lineup_defense = lineup_row[TIPL.LINEUP_OPPONENT].tolist()[0]

            points = 0

            if play_type == "score":
                away_score = int(row['SCORE'].split(" -")[0])
                home_score = int(row['SCORE'].split("- ")[1])

                if row[PBP.HOMEDESCRIPTION]:
                    if 'Free Throw' in description:
                        home_score -= 1
                    elif '3PT' in description:
                        home_score -= 3
                    elif row[PBP.SCORE]:
                        home_score -= 2
                else:
                    if 'Free Throw' in description:
                        away_score -= 1
                    elif '3PT' in description:
                        away_score -= 3
                    elif row[PBP.SCORE]:
                        away_score -= 2


            if row[PBP.HOMEDESCRIPTION]:
                score = home_score
                score_defense = away_score

                if prev_home_score is not None:
                    points = home_score - prev_home_score

            else:
                score = away_score
                score_defense = home_score
                if prev_away_score is not None:
                    points = away_score - prev_away_score

            prev_away_score = away_score
            prev_home_score = home_score

            if idx > 0:
                prev_row = play_by_plays.iloc[idx - 1]
                prev_description = prev_row[PBP.HOMEDESCRIPTION] if prev_row[PBP.HOMEDESCRIPTION] else prev_row[
                    'VISITORDESCRIPTION'] if \
                    prev_row[
                        'VISITORDESCRIPTION'] else prev_row['NEUTRALDESCRIPTION']
                prev_play_type = _get_play_type_by_row(row=prev_row, text_description=prev_description)
                if prev_row[PBP.HOMEDESCRIPTION] and row[PBP.HOMEDESCRIPTION] or prev_row[PBP.VISITORDESCRIPTION] and \
                        row[PBP.VISITORDESCRIPTION]:
                    team_prev_posession = True
                else:
                    team_prev_posession = False
            else:
                prev_play_type = None
                team_prev_posession = None

        #  lineup_possession_attempts[LPBP.TEAM_PREV_POSSESION].append(team_prev_posession)
        # lineup_possession_attempts[LPBP.PRECEEDED_BY].append(prev_play_type)

        play_by_plays.at[idx, LPBP.POSSESSION_ID] = possession_id
        play_by_plays.at[idx, LPBP.POSSESSION_ATTEMPT_ID] = possession_attempt_id

        defensive_rebound = False
        if play_type == 'rebound':
            defensive_rebound = False
            miss_is_home = row[PBP.HOMEDESCRIPTION] is not None
            if miss_is_home and play_by_plays.iloc[idx - 1][PBP.VISITORDESCRIPTION]:
                defensive_rebound = True
            elif not miss_is_home and play_by_plays.iloc[idx - 1][PBP.HOMEDESCRIPTION]:
                defensive_rebound = True

        if play_type in ('miss', 'steal', 'turnover', 'end',
                         'offensive foul') or 'Free Throw 1 of 1' in description \
                or 'Free Throw 2 of 2' in description or 'Free Throw 3 of 3' in description or defensive_rebound \
                or 'Free Throw' not in description and play_type == 'score':
            lineup_possession_attempts[LPBP.POSSESSION_ID].append(possession_id)
            lineup_possession_attempts[LPBP.POSSESSION_ATTEMPT_ID].append(possession_attempt_id)
            lineup_possession_attempts[LPBP.SECONDS_PLAYED_START].append(play_start_seconds_played)
            lineup_possession_attempts[LPBP.SECONDS_PLAYED_END].append(seconds_played)
            lineup_possession_attempts[LPBP.PLAY_END_REASON].append(play_type)
            lineup_possession_attempts[LPBP.SCORE_OFFENSE].append(score)
            lineup_possession_attempts[LPBP.SCORE_DEFENSE].append(score_defense)
            lineup_possession_attempts[LPBP.LINEUP_OFFENSE].append(lineup)
            lineup_possession_attempts[LPBP.LINEUP_DEFENSE].append(lineup_defense)
            lineup_possession_attempts[LPBP.TEAM_ID].append(team_id)
            lineup_possession_attempts[LPBP.POINTS].append(points)
            possession_attempt_id += 1

            if play_type in ('score', 'turnover', 'end', 'offensive foul') or defensive_rebound:
                possession_id += 1

        play_start_seconds_played = seconds_played
        last_team_id = team_id

    return pd.DataFrame.from_dict(lineup_possession_attempts), play_by_plays


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
            lineup.sort()
            lineup_opponent.sort()
            inplay_lineups[TIPL.LINEUP].append(tuple(lineup))
            inplay_lineups[TIPL.LINEUP_OPPONENT].append(tuple(lineup_opponent))
            inplay_lineups[TIPL.TEAM_ID].append(team_id)
            inplay_lineups[TIPL.SECONDS_PLAYED_START].append(seconds_played_start)
            inplay_lineups[TIPL.SECONDS_PLAYED_END].append(seconds_played_end)

    return pd.DataFrame.from_dict(inplay_lineups)
