import pandas as pd

from nba_api_wrapper.games_generator import games_scorer

collected_data = games_scorer(
    min_date="2022-10-21",
    max_date='2022-10-23'
)

possessions = pd.read_parquet("data/possessions.parquet")
game_players = pd.read_parquet("data/game_players.parquet")
game_players = game_players.append(collected_data.game_players)
game_players = game_players.drop_duplicates()

game_teams = pd.read_parquet("data/game_teams.parquet")
game_teams = game_teams.append(collected_data.game_teams)
game_teams = game_teams.drop_duplicates()

offense_player_play_by_plays = pd.read_parquet("data/offense_player_play_by_plays.parquet")
offense_player_play_by_plays = offense_player_play_by_plays.append(collected_data.offense_player_play_by_plays)
offense_player_play_by_plays = offense_player_play_by_plays.drop_duplicates()

defense_player_play_by_plays = pd.read_parquet("data/game_teams.parquet")
defense_player_play_by_plays = defense_player_play_by_plays.append(collected_data.defense_player_play_by_plays)
defense_player_play_by_plays = defense_player_play_by_plays.drop_duplicates()
possessions = possessions.append(collected_data.possessions)
possessions = possessions.drop_duplicates()

possessions.to_parquet("data/possessions.parquet")
game_players.to_parquet("data/game_team.parquet")
game_teams.to_parquet("data/game_player.parquet")
offense_player_play_by_plays.to_parquet("data/offense_player_play_by_plays.parquet")
defense_player_play_by_plays.to_parquet("data/defense_player_play_by_plays.parquet")
