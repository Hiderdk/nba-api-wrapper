from abc import abstractmethod, ABC

from nba_api_wrapper.api._base import BaseApi
from nba_api_wrapper.datastructures import CollectedData


class GameCollector(ABC):

    def __init__(self, api: BaseApi):
        self.api = api

    @abstractmethod
    def collect(self, game_id: str) -> CollectedData:
        pass


class NBAPbPGameCollector(GameCollector):

    def __init__(self,
                 api: BaseApi
                 ):
        super().__init__(api=api)

    def collect(self, game_id: str) -> CollectedData:
        boxscore = self.api.get_game_team_by_game_id(game_id=game_id)
        possessions = self.api.get_possessions_by_game_id(game_id=game_id)

        return CollectedData(
            possessions=possessions

        )
