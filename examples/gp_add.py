import pandas as pd


def gp_add():
    gp = pd.read_pickle("data/game_player.pickle")
    for col in ['tp', 'possessions_defense_count', 'possessions_offense_count', 'points_for', 'points_against', 'team_points_for']:
        if col in gp.columns:
            gp = gp.drop(columns=[col])
    possessions = pd.read_pickle("data/possessions.pickle")


    possessions['net_seconds'] = possessions['start_time_seconds'] - possessions['end_time_seconds']
    exploded = possessions.explode(['lineup_offense']).rename(columns={'lineup_offense': 'player_id'}).rename(
        columns={'points_offense': 'possessions_points_for'})

    exploded_def = possessions.explode(['lineup_defense']).rename(columns={'lineup_defense': 'player_id'}).rename(
        columns={'points_offense': 'possessions_points_against'})

    grp_off = exploded.groupby(['game_id', 'player_id']).agg({'possessions_points_for': 'sum', 'player_id': 'count'}).rename(
        columns={'player_id': 'possessions_offense_count'}).reset_index()

    grp_def = exploded_def.groupby(['game_id', 'player_id']).agg(
        {'possessions_points_against': 'sum', 'player_id': 'count'}).rename(
        columns={'player_id': 'possessions_defense_count'}).reset_index()



    # possessions = exploded.groupby(['game_id', 'player_id'])['points', 'net_seconds'].sum().reset_index()

    gp = gp.merge(grp_off[['game_id', 'player_id', 'possessions_points_for', 'possessions_offense_count']],
                  on=['game_id', 'player_id'], how='left')
    gp = gp.merge(grp_def[['game_id', 'player_id', 'possessions_points_against', 'possessions_defense_count']],
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
