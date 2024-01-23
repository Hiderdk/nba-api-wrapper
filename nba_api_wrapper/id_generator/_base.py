from abc import ABC, abstractmethod


class IdGenerator(ABC):

    @abstractmethod
    def get_lineup_id(self, lineup: list[str]) -> str:
        pass

    @abstractmethod
    def get_player_id(self, player_name: str) -> str:
        pass