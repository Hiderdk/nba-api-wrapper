import pandas as pd

from nba_api_wrapper.game_storer import GameStorer
from nba_api_wrapper.storer.file_storer import FileStorer


def already_stored(collected_data):
    possessions = pd.read_pickle("data/possessions.pickle")
    game_players = pd.read_pickle("data/game_player.pickle")
    games = pd.read_pickle("data/game.pickle")
    games = pd.concat([games, collected_data.game])
    games = games.drop_duplicates()

    game_players = pd.concat([game_players, collected_data.game_players])
    game_players = game_players.drop_duplicates()

    game_teams = pd.read_pickle("data/game_team.pickle")
    game_teams = pd.concat([game_teams, collected_data.game_teams])
    game_teams = game_teams.drop_duplicates()

    offense_player_play_by_plays = pd.read_pickle("data/offense_player_play_by_plays.pickle")
    offense_player_play_by_plays = pd.concat(
        [offense_player_play_by_plays, collected_data.offense_player_play_by_plays])
    offense_player_play_by_plays = offense_player_play_by_plays.drop_duplicates()

    defense_player_play_by_plays = pd.read_pickle("data/defense_player_play_by_plays.pickle")
    defense_player_play_by_plays = pd.concat(
        [defense_player_play_by_plays, collected_data.defense_player_play_by_plays])
    defense_player_play_by_plays = defense_player_play_by_plays.drop_duplicates()
    possessions = pd.concat([possessions, collected_data.possessions])
    possessions = possessions.drop_duplicates()

    possessions.to_pickle("data/possessions.pickle")
    game_players.to_pickle("data/game_player.pickle")
    game_teams.to_pickle("data/game_team.pickle")
    offense_player_play_by_plays.to_pickle("data/offense_player_play_by_plays.pickle")
    defense_player_play_by_plays.to_pickle("data/defense_player_play_by_plays.pickle")
    games.to_pickle("data/game.pickle")


if __name__ == '__main__':
    game_storer = GameStorer(storer=FileStorer(base_path="data"), store_frequency=25)
    game_storer.generate(min_date="2022-10-16",
                         max_date='2023-07-17')
