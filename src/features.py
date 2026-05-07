def add_features(df):
    def bucket(d):
        if d <= 3:
            return "short"
        elif d <= 7:
            return "medium"
        else:
            return "long"

    df["length"] = df["distance"].apply(bucket)

    # success = gained enough yards
    df["success"] = (df["yds_gained"] >= df["distance"]).astype(int)

    return df

