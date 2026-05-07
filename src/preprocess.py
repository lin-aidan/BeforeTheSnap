def clean_col(df, col):
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df


def merge_data(df_game, df_map):
    df_game = clean_col(df_game, "play")
    df_map = clean_col(df_map, "play")

    return df_game.merge(df_map, on="play", how="left")

