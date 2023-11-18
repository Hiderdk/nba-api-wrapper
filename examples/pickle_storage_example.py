import pandas as pd

from nba_api_wrapper.generator import GameStorer
from nba_api_wrapper.storer.file_storer import FileStorer



game_storer = GameStorer(storer=FileStorer(base_path="data"), store_frequency=25)
game_storer.generate(min_date="2021-10-10",
                     max_date='2021-11-24')
