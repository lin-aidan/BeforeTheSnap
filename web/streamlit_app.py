import streamlit as st
import pandas as pd
import traceback

from src import load_data, preprocess, features, model as model_mod, recommend, parser
import main as main_orchestration

@st.cache_resource
def build_model():
    try:
        df_game, df_map = load_data.load_data()
    except Exception:
        df_game = pd.read_csv("data/MU_2025_off.csv")
        df_map = pd.read_csv("data/plays.csv")
    try:
        df = preprocess.merge_data(df_game, df_map)
    except Exception:
        df = df_game
    try:
        df = features.add_features(df)
    except Exception:
        pass
    df_model = model_mod.build_model(df)
    return df_model

st.set_page_config(page_title="BeforeTheSnap — Play Recommendation", layout="wide")
st.title("BeforeTheSnap — Play Recommendation")

df_model = build_model()

with st.form("query_form"):
    query = st.text_input("Query (natural language)", placeholder="e.g. 3rd and 7")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        down = st.selectbox("Down", options=[1,2,3,4], index=2)
    with col2:
        distance = st.number_input("Distance (yards)", min_value=0, max_value=99, value=7)
    with col3:
        submit = st.form_submit_button("Recommend")

agent_checkbox = st.checkbox("Show AI agent commentary (may require network/LLM access)")

results_placeholder = st.container()

def parse_and_recommend(query_text, down_val, dist_val):
    try:
        if query_text and query_text.strip():
            d, dist = parser.parse_input(query_text)
        else:
            d, dist = down_val, dist_val
    except Exception:
        d, dist = down_val, dist_val

    try:
        recs = recommend.recommend_play(df_model, int(d), int(dist))
    except Exception:
        try:
            recs = recommend.recommend(df_model, int(d), int(dist))
        except Exception:
            st.error("Recommendation function failed. See console for details.")
            traceback.print_exc()
            return [], (d, dist)

    return recs, (d, dist)

if submit:
    recs, (used_down, used_dist) = parse_and_recommend(query, down, distance)
    with results_placeholder:
        st.subheader(f"Top plays — Down {used_down}, Distance {used_dist}")
        if not recs:
            st.info("No recommendations returned.")
        else:
            df_out = pd.DataFrame(recs)
            display_cols = []
            if "play" in df_out.columns:
                display_cols.append("play")
            if "concept" in df_out.columns:
                display_cols.append("concept")
            if "score" in df_out.columns:
                display_cols.append("score")
            if not display_cols:
                display_cols = list(df_out.columns)[:3]
            st.dataframe(df_out[display_cols])

            for i, row in df_out.iterrows():
                expl = row.get("explanation") or row.get("explain") or row.get("reason")
                if expl:
                    with st.expander(f"Explanation — {row.get('play', row.get('concept', i))}"):
                        st.write(expl)

    if agent_checkbox:
        st.subheader("AI agent commentary")
        try:
            if hasattr(main_orchestration, "explain_query"):
                commentary = main_orchestration.explain_query(query if query else f"{used_down} and {used_dist}")
                st.text_area("Agent output", value=commentary, height=240)
            else:
                st.info("No agent wrapper found in main.py; attempting a best-effort run of `main.py`.")
                import subprocess, sys
                p = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True, input=(query or f"{used_down} and {used_dist}"), timeout=30)
                st.text_area("Raw agent output", value=p.stdout + ("\n\nERR:\n"+p.stderr if p.stderr else ""), height=240)
        except Exception:
            st.error("Agent commentary failed; check server/LLM connectivity.")
            traceback.print_exc()

with st.sidebar:
    st.header("Data & Stats")
    if st.button("Show sample data"):
        try:
            df_game, _ = load_data.load_data()
            st.dataframe(df_game.head(10))
        except Exception:
            st.info("Could not load sample data.")
    try:
        st.write("Model sample:")
        sample_stats = df_model.head(10) if hasattr(df_model, "head") else df_model
        st.dataframe(sample_stats)
    except Exception:
        pass
