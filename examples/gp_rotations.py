import pandas as pd


def create_gp_poss():
    possesions = pd.read_pickle("data/possessions.pickle")
    gp = pd.read_pickle("data/game_player.pickle")

    pn = gp.groupby('player_id')['player_name'].first().reset_index()
    possesions['minutes'] = (possesions['start_time_seconds'] - possesions['end_time_seconds']) / 60

    rot = possesions.groupby(["game_id", "lineup_id_offense", "lineup_id_defense", "lineup_offense", "lineup_defense"])[
        ["points_offense", "minutes"]].sum().reset_index()

    exploded_off = rot.explode("lineup_offense").rename(
        columns={"lineup_offense": "player_id", 'points_offense': 'points_for', 'minutes': 'minutes_offense'})
    exploded_def = rot.explode("lineup_defense").rename(
        columns={"lineup_defense": "player_id", 'points_offense': 'points_against', 'minutes': 'minutes_defense'})
    exploded = exploded_off.merge(exploded_def,
                                  left_on=["game_id", "lineup_id_offense", "lineup_id_defense", "player_id"],
                                  right_on=["game_id", "lineup_id_defense", "lineup_id_offense", "player_id"],
                                  how="outer"
                                  ).reset_index()

    exploded['lineup_id'] = exploded['lineup_id_offense_x']
    exploded['lineup_id'] = exploded['lineup_id'].fillna(exploded['lineup_id_defense_y'])

    exploded['lineup_id_opponent'] = exploded['lineup_id_defense_x']
    exploded['lineup_id_opponent'] = exploded['lineup_id_opponent'].fillna(exploded['lineup_id_offense_y'])

    exploded.drop(columns=['lineup_id_offense_x', 'lineup_id_defense_y', 'lineup_id_defense_x', 'lineup_id_offense_y',
                           'lineup_offense', 'lineup_defense'], inplace=True)

    exploded['points_against'] = exploded['points_against'].fillna(0)
    exploded['points_for'] = exploded['points_for'].fillna(0)
    exploded['minutes_offense'] = exploded['minutes_offense'].fillna(0)
    exploded['minutes_defense'] = exploded['minutes_defense'].fillna(0)


if __name__ == '__main__':
    create_gp_poss()
