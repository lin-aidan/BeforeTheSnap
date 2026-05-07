def build_model(df):
    grouped = df.groupby(
        ["down", "length", "concept"]
    )["success"].agg(["mean", "count"]).reset_index()

    # Bayesian smoothing
    prior = df["success"].mean()

    grouped["score"] = (
        (grouped["mean"] * grouped["count"] + prior * 5)/(grouped["count"] + 5))

    return grouped

