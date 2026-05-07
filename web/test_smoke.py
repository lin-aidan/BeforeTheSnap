def test_recommend_smoke():
    from src import load_data, preprocess, features, model as model_mod, recommend
    df_game, df_map = load_data.load_data()
    try:
        df = preprocess.merge_data(df_game, df_map)
    except Exception:
        df = df_game
    df = features.add_features(df)
    df_model = model_mod.build_model(df)
    recs = recommend.recommend_play(df_model, 3, 7)
    assert isinstance(recs, list)
    assert len(recs) >= 1
    first = recs[0]
    assert any(k in first for k in ("score", "concept", "play"))
