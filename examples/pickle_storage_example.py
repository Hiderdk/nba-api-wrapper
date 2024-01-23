from nba_api_wrapper.generators.generator import GameStorer
from nba_api_wrapper.storer.file_storer import FileStorer



game_storer = GameStorer(storer=FileStorer(base_path="data"), store_frequency=25, newest_games_only=True)
game_storer.generate(min_date="2023-12-20",
                     max_date='2024-01-21')
