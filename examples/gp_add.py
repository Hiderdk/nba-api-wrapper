import json

import pandas as pd


def gp_add():
    gp = pd.read_pickle("data/game_player.pickle")
    for col in ['tp', 'possessions_defense_count', 'possessions_offense_count', 'points_for', 'points_against',
                'team_points_for']:
        if col in gp.columns:
            gp = gp.drop(columns=[col])
    possessions = pd.read_pickle("data/possessions.pickle")

    possessions['net_seconds'] = possessions['start_time_seconds'] - possessions['end_time_seconds']
    gp_rot = pd.read_pickle("data/game_player_rotations.pickle")
    gp_rot["minutes"] = gp_rot["minutes_offense"] + gp_rot["minutes_defense"]
    game_ids = gp_rot['game_id'].unique()

    gp_rot['matchup_id'] = gp_rot['lineup_id'] + "_" + gp_rot['lineup_id_opponent']

    if 'team_player_mins' not in gp.columns:
        gp['team_player_mins'] = None
    gp = gp.astype({'team_player_mins': 'object'})

    for game_id in game_ids:
        print(game_id)
        player_to_team_mins = {}
        player_to_opp_mins = {}
        poss_game = gp_rot[gp_rot['game_id'] == game_id]

        for _, row in poss_game.iterrows():
            player_id = row['player_id']
            player_id = int(player_id)
            if player_id not in player_to_team_mins:
                player_to_team_mins[player_id] = {}
                player_to_opp_mins[player_id] = {}

            lineup = row['lineup_id'].split("_")
            for team_player_id in lineup:
                if team_player_id == player_id:
                    continue

                if team_player_id not in player_to_team_mins[player_id]:
                    player_to_team_mins[player_id][team_player_id] = 0

                player_to_team_mins[player_id][team_player_id] += round(row['minutes_offense'] + row["minutes_defense"],
                                                                        2)
                player_to_team_mins[player_id][team_player_id] = round(player_to_team_mins[player_id][team_player_id],
                                                                       2)

            lineup_opponent = row['lineup_id_opponent'].split("_")
            for opp_player_id in lineup_opponent:
                opp_player_id = int(opp_player_id)
                if opp_player_id not in player_to_opp_mins[player_id]:
                    player_to_opp_mins[player_id][opp_player_id] = 0

                player_to_opp_mins[player_id][opp_player_id] += round(row['minutes_offense'] + row["minutes_defense"],
                                                                      2)
                player_to_opp_mins[player_id][opp_player_id] = round(player_to_opp_mins[player_id][opp_player_id], 2)

        for player_id, team_player_mins in player_to_team_mins.items():
            json_str = json.dumps(team_player_mins)

            gp.loc[
                (gp['player_id'] == player_id) &
                (gp['game_id'] == game_id),
                'team_player_mins'] = json_str

            for player_id, opp_player_mins in player_to_opp_mins.items():
                json_str = json.dumps(opp_player_mins)
                gp.loc[
                    (gp['player_id'] == player_id) &
                    (gp['game_id'] == game_id),
                    'opp_player_mins'] = json_str

    exploded = possessions.explode(['lineup_offense']).rename(columns={'lineup_offense': 'player_id'}).rename(
        columns={'points_offense': 'possessions_points_for'})

    exploded_def = possessions.explode(['lineup_defense']).rename(columns={'lineup_defense': 'player_id'}).rename(
        columns={'points_offense': 'possessions_points_against'})

    grp_off = exploded.groupby(['game_id', 'player_id']).agg(
        {
            'possessions_points_for': 'sum',
            'net_seconds': 'mean',
            'player_id': 'count'
        }).rename(
        columns={'player_id': 'possessions_offense_count',
                 'net_seconds': 'possessions_offense_mean_duration'}).reset_index()

    grp_def = exploded_def.groupby(['game_id', 'player_id']).agg(
        {
            'possessions_points_against': 'sum',
            'net_seconds': 'mean',
            'player_id': 'count'
        }).rename(
        columns={'player_id': 'possessions_defense_count',
                 'net_seconds': 'possessions_defense_mean_duration'}).reset_index()

    # possessions = exploded.groupby(['game_id', 'player_id'])['points', 'net_seconds'].sum().reset_index()

    gp = gp.merge(grp_off[['game_id', 'player_id', 'possessions_points_for', 'possessions_offense_count',
                           'possessions_offense_mean_duration']],
                  on=['game_id', 'player_id'], how='left')
    gp = gp.merge(grp_def[['game_id', 'player_id', 'possessions_points_against', 'possessions_defense_count',
                           'possessions_defense_mean_duration']],
                  on=['game_id', 'player_id'], how='left')

    gp.to_pickle("data/game_player.pickle")

    def comp():
        grp_team_off = exploded.groupby(['game_id', 'team_id_offense'])['points_for'].sum().reset_index().rename(
            columns={'points_for': 'team_points_for'})

        grp_team_off['team_points_for'] = grp_team_off['team_points_for'] / 5
        gp = gp.merge(grp_team_off, left_on=['game_id', 'team_id'], right_on=['game_id', 'team_id_offense'], how='left')
        gp['tp'] = gp.groupby(['game_id', 'team_id'])['points'].transform('sum')
        gp['player_id'] = gp['player_id'].astype('int')
        grp_off['player_id'] = grp_off['player_id'].astype('int')
        grp_def['player_id'] = grp_def['player_id'].astype('int')

        gp['plus_minus_2'] = gp['points_for'] - gp['points_against']
        i = gp[(gp['plus_minus_2'] != gp['plus_minus']) & (gp['plus_minus_2'].notna())]
        i2 = gp[(gp['plus_minus_2'] == gp['plus_minus']) & (gp['plus_minus_2'].notna())]


if __name__ == '__main__':
    gp_add()
