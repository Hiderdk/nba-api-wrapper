from abc import ABC, abstractmethod
from typing import Union

import pandas as pd
import pendulum

from nba_api_wrapper.data_models import GamePlayerModel


class BaseApi(ABC):

    @abstractmethod
    def get_game_ids_by_date_range(self, min_date: pendulum.DateTime, max_date: pendulum.DateTime) -> list[Union[str, int]]:
        pass

    @abstractmethod
    def get_game_ids_by_date(self, date: pendulum.DateTime ) -> list[Union[str, int]]:
        pass

    @abstractmethod
    def get_possessions_by_game_id(self, game_id: Union[str, int]) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_game_team_by_game_id(self, int: Union[str, int]) -> GamePlayerModel:
        pass

    @abstractmethod
    def get_game_player_by_game_id(self, int: Union[str, int]) -> GamePlayerModel:
        pass

    @abstractmethod
    def get_game_by_game_id(self, int: Union[str, int]) -> GamePlayerModel:
        pass