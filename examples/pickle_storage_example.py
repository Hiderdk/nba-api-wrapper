from nba_api_wrapper.generator import GameStorer
from nba_api_wrapper.storer.file_storer import FileStorer



game_storer = GameStorer(storer=FileStorer(base_path="data", overwrite=True), store_frequency=25, newest_games_only=False)
game_storer.generate(min_date="2019-10-16",
                     max_date='2021-11-29')
