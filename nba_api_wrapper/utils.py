import logging
import os
import datetime
from typing import Optional

import pandas as pd

from nba.data_generation import NBAData
from nba.utils import convert_to_dataframe


def generate_and_store_as_csv(
        file_path_name: str,
        append: bool = True,
        min_date: Optional[datetime.date] = datetime.datetime.now() - datetime.timedelta(days=10),
        max_date: Optional[datetime.date] = datetime.datetime.now() + datetime.timedelta(days=1)
):
    current_df = None
    if append:
        if not os.path.isfile(file_path_name):
            logging.warning(
                f"{file_path_name} does not exist - will not load file - will utilize min date of {max_date}")
            min_date = min_date
            max_date = max_date

        else:
            current_df = pd.read_csv(file_path_name)
            if min_date is None:
                min_date = pd.to_datetime(
                    current_df.sort_values(by='start_date', ascending=False)['start_date'].iloc[0])
            if max_date is None:
                max_date = min_date + min_date + datetime.timedelta(days=10)

    else:
        min_date = min_date
        max_date = max_date

    nbaDataGenerator = NBAData()
    games = nbaDataGenerator.generate_nba_data_by_date_period(min_date=min_date, max_date=max_date)
    df = convert_to_dataframe(games)
    if append:
        if current_df is not None:
            df = current_df.append(df, ignore_index=True)
            df = df.drop_duplicates(subset=['game_id', 'player_id'])

    df.to_csv(file_path_name, index_label=False)


from dataclasses import asdict

import pandas as pd

from nba.dataclass import Game, GamePlayer, GameTeam


def _get_column_name(column, entity) -> str:
    if column == 'id' and entity == '':
        return 'game_id'
    if entity in column or 'opponent' in column:
        return column
    else:
        return f"{entity}_{column}"


def convert_to_dataframe(games: list[Game]) -> pd.DataFrame:
    game_player_data = {}
    game_player_columns = GamePlayer.__annotations__
    game_team_columns = GameTeam.__annotations__
    game_columns = Game.__annotations__

    for column in game_columns:
        if column == "teams":
            continue
        column_name = _get_column_name(column=column, entity="")
        game_player_data[column_name] = []

    for column in game_team_columns:
        if column == "players":
            continue
        column_name = _get_column_name(column=column, entity="team")
        game_player_data[column_name] = []

    for column in game_player_columns:
        column_name = _get_column_name(column=column, entity="player")

        game_player_data[column_name] = []

    for game in games:
        game_dict = asdict(game)

        for game_team in game.teams:
            game_team_dict = asdict(game_team)

            for game_player in game_team.players:
                game_player_dict = asdict(game_player)
                for column, value in game_player_dict.items():
                    column_name = _get_column_name(column=column, entity="player")
                    if column_name not in game_player_data:
                        continue
                    game_player_data[column_name].append(value)

                for column, value in game_team_dict.items():

                    column_name = _get_column_name(column=column, entity="team")
                    if column_name not in game_player_data:
                        continue
                    game_player_data[column_name].append(value)

                for column, value in game_dict.items():
                    column_name = _get_column_name(column=column, entity="")
                    if column_name not in game_player_data:
                        continue
                    game_player_data[column_name].append(value)

    return pd.DataFrame(game_player_data)
