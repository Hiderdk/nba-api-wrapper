from abc import ABC, abstractmethod

import pandas as pd

from nba_api_wrapper.datastructures import CollectedData


class Storer(ABC):

    @abstractmethod
    def store(self, collected_data: CollectedData):
        pass

    @abstractmethod
    def load_lineups(self) -> pd.DataFrame:
        pass