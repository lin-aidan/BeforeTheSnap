def get_bucket(distance):
    if distance <= 3:
        return "short"
    elif distance <= 7:
        return "medium"
    return "long"


def recommend(grouped, down, distance):
    bucket = get_bucket(distance)

    filtered = grouped[
        (grouped["down"] == down) &
        (grouped["length"] == bucket)
    ]

    return filtered.sort_values("score", ascending=False)


def recommend_play(df_model, down, distance):
    top = recommend(df_model, down, distance).head(3)
    return top.to_dict(orient="records")

