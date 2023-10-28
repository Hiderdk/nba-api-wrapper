import json
import logging
import time

import pandas as pd
import requests
from nba_api.stats.endpoints import LeagueGameFinder, BoxScoreTraditionalV2, PlayByPlayV2, GameRotation

from nba_api_wrapper.api.api_throttle import APIThrottle
from nba_api_wrapper.api.decorators import retry_on_error

api_throttle = APIThrottle(interval_seconds=60, max_calls_per_interval=10)


class NBAApi:

    def __init__(self,
                 max_calls_per_interval: int = 8,
                 interval_seconds: int = 20,
                 ):
        self.max_calls_per_interval = max_calls_per_interval
        self.interval_seconds = interval_seconds
        self._game_ids = None
        self._interval_begin_time = None
        self._interval_counts = 0

    @retry_on_error
    @api_throttle
    def get_league_game_finder_data(self, min_date: str, max_date: str) -> pd.DataFrame:
        self._api_calls_counter()

        league_game_finder_data = LeagueGameFinder(
            date_from_nullable=min_date,
            date_to_nullable=max_date)

        return league_game_finder_data.get_data_frames()[0]

    @retry_on_error
    @api_throttle
    def get_play_by_play_by_game_id(self, game_id: int) -> pd.DataFrame:
        play_by_play_data = PlayByPlayV2(game_id=game_id)
        return play_by_play_data.get_data_frames()[0]


    @retry_on_error
    @api_throttle
    def get_shot_data_by_game_id(self, game_id: int) -> pd.DataFrame:



    @retry_on_error
    @api_throttle
    def get_rotations_by_game_id(self, game_id: int) -> list[pd.DataFrame]:
        rotation_data = GameRotation(game_id=game_id)
        return rotation_data.get_data_frames()

    @retry_on_error
    @api_throttle
    def get_boxscore_by_game_id(self, game_id: int) -> pd.DataFrame:
        boxscore_traditional_v2_data = BoxScoreTraditionalV2(game_id=game_id)
        box_score_trad_df = boxscore_traditional_v2_data.get_data_frames()[0]

        box_score_trad_df = box_score_trad_df.fillna(0)
        return box_score_trad_df

    @property
    def game_ids(self) -> list[int]:
        return self._game_ids

    def _api_calls_counter(self):

        current_time = time.time()

        if self._interval_begin_time is None:
            self._interval_counts = 1
            self._interval_begin_time = current_time
            return
        if current_time - self._interval_begin_time < self.interval_seconds:
            self._interval_counts += 1
            if self._interval_counts > self.max_calls_per_interval:
                sleep_seconds = 60 - (current_time - self._interval_begin_time)
                time.sleep(sleep_seconds)
                self._interval_counts = 0
                self._interval_begin_time = time.time()
