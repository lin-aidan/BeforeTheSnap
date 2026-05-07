import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def load_data():
    game_path = os.path.join(BASE_DIR, "data", "MU_2025_off.csv")
    plays_path = os.path.join(BASE_DIR, "data", "plays.csv")

    df_game = pd.read_csv(game_path)
    df_map = pd.read_csv(plays_path)

    return df_game, df_map

