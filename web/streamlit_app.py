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

df_model = build_model()

import base64
import pathlib
import os
import re

# Helper to find a static file in common locations
def find_static_file(name_variants):
    for p in name_variants:
        pth = pathlib.Path(p)
        if pth.exists():
            return pth
    return None

# Preferred static logo locations (user can drop files here)
logo_candidates = [
    "web/static/logo.png",
    "web/static/logo.jpg",
    "web/static/logo.jpeg",
    "assets/logo.png",
    "assets/logo.jpg",
    "logo.png",
    "logo.jpg",
]
bg_candidates = [
    "web/static/background.png",
    "web/static/background.jpg",
    "web/static/background.jpeg",
    "assets/background.png",
    "assets/background.jpg",
    "background.png",
    "background.jpg",
]

static_logo = find_static_file(logo_candidates)
static_bg = find_static_file(bg_candidates)

# Header: centered logo (static preferred). If no static logo, allow upload.
def _render_centered_image(img_bytes, mime, max_width_px=420):
    b64 = base64.b64encode(img_bytes).decode()
    html = (
        f"<div id='logo-header' style='display:flex;justify-content:center;align-items:center;margin:6px 0;padding:6px;'>"
        f"<img src=\"data:{mime};base64,{b64}\" style=\"max-width:{max_width_px}px;max-height:140px;height:auto;display:block;\"/>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)

logo_rendered = False
if static_logo is not None:
    try:
        with open(static_logo, "rb") as f:
            logo_bytes = f.read()
        ext = static_logo.suffix.lower()
        logo_mime = "image/png" if ext == ".png" else "image/jpeg"
        _render_centered_image(logo_bytes, logo_mime)
        logo_rendered = True
    except Exception:
        st.warning("Could not display static logo image.")

if not logo_rendered:
    logo_file = st.file_uploader("Upload logo (will be centered)", type=["png", "jpg", "jpeg", "svg"], key="logo_uploader")
    if logo_file is not None:
        try:
            logo_bytes = logo_file.read()
            logo_mime = logo_file.type or "image/png"
            _render_centered_image(logo_bytes, logo_mime)
            logo_rendered = True
        except Exception:
            st.warning("Could not display uploaded logo image.")

# Background image: use static file from repository if present
bg_to_use = None
if static_bg is not None:
    try:
        with open(static_bg, "rb") as f:
            bg_to_use = f.read()
        # derive mime from suffix
        ext = static_bg.suffix.lower()
        bg_mime = "image/png" if ext == ".png" else "image/jpeg"
    except Exception:
        bg_to_use = None

if bg_to_use is not None:
    try:
        b64 = base64.b64encode(bg_to_use).decode()
        # Apply CSS to app container so background covers entire app
        css = (
            "<style>"
            f"body, html, .stApp, [data-testid=\"stAppViewContainer\"] {{background-image: url(\"data:{bg_mime};base64,{b64}\"); background-size: cover; background-repeat: no-repeat; background-attachment: fixed;}}"
            "</style>"
        )
        st.markdown(css, unsafe_allow_html=True)
    except Exception:
        st.warning("Could not set background image.")

# Add CSS to fix logo at top and make main content a white panel below it
app_css = """
<style>
/* Logo header in normal document flow (not fixed) */
#logo-header { position: relative; top: 0; left: auto; right: auto; z-index: 1; padding-top: 8px; pointer-events: auto; }

/* Make main content area distinct; sits below the logo */
div[data-testid="stAppViewContainer"] .main .block-container {
    background: rgba(255,255,255,0.96);
    padding: 20px 24px;
    border-radius: 10px;
    margin-top: 20px; /* space below logo */
    max-height: none;
    overflow: visible;
}
</style>
"""
st.markdown(app_css, unsafe_allow_html=True)

with st.form("query_form"):
    query = st.text_input("Query (natural language)", placeholder="e.g. 3rd and 7")
    submit = st.form_submit_button("Recommend")

results_placeholder = st.container()

def parse_and_recommend(query_text):
    try:
        if not (query_text and query_text.strip()):
            raise ValueError("Empty query")
        d, dist = parser.parse_input(query_text)
    except Exception:
        st.error("Could not parse query. Please use a format like '3rd and 7'.")
        return [], (None, None)

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
    recs, (used_down, used_dist) = parse_and_recommend(query)
    with results_placeholder:
        if used_down is None:
            st.subheader(f"Top plays — Query: {query}")
        else:
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

    # Automatic agent commentary and structured display
    try:
        # prepare agent input
        if used_down is not None:
            agent_input = f"{used_down} and {used_dist}"
        else:
            agent_input = query

        # pick top recommendation
        top_rec = recs[0] if recs else None

        # Compute success probability from recommendation if available
        success_prob = None
        if top_rec is not None:
            success_prob = top_rec.get("score") or top_rec.get("mean")

        # Call orchestrator for Offensive Coordinator and Analyst commentary separately
        off_text = None
        anl_text = None

        if hasattr(main_orchestration, "explain_query"):
            try:
                off_text = main_orchestration.explain_query(f"Offensive coordinator — given '{agent_input}', provide the play concept and the intent in 2-3 short sentences.")
            except Exception:
                off_text = None
            try:
                anl_text = main_orchestration.explain_query(f"Analyst — given '{agent_input}', summarize aggressiveness, success probability, and data-driven reasoning in 2-3 short sentences.")
            except Exception:
                anl_text = None
        else:
            # best-effort: run main.py with prefixed role text
            import subprocess, sys
            try:
                p_off = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True, input=(f"OFFENSIVE: {agent_input}"), timeout=30)
                off_text = p_off.stdout
            except Exception:
                off_text = None
            try:
                p_anl = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True, input=(f"ANALYST: {agent_input}"), timeout=30)
                anl_text = p_anl.stdout
            except Exception:
                anl_text = None

        # Layout: two columns for Offensive Coordinator and Analyst
        col_off, col_anl = st.columns(2)

        # helper: clean raw agent text and strip out dict/list dumps
        def clean_agent_text(t: str) -> str:
            if not t:
                return ""
            # remove interactive prompts
            t = re.sub(r"Enter situation.*", "", t, flags=re.IGNORECASE)
            # remove lines that are just role separators like '--- Offensive Coordinator ---'
            t = re.sub(r"^-{2,}.*?-{2,}$", "", t, flags=re.MULTILINE)
            # remove standalone role labels
            t = re.sub(r"^\s*(Offensive Coordinator|Analyst|OFFENSIVE|ANALYST)\s*$", "", t, flags=re.MULTILINE)
            # remove printed python dict/list dump blocks (e.g. [{'down':...}])
            t = re.sub(r"\[\s*\{.*?\}\s*\]", "", t, flags=re.DOTALL)
            t = re.sub(r"\{\s*'down':.*?\}\s*", "", t, flags=re.DOTALL)
            # collapse multiple blank lines
            t = re.sub(r"\n\s*\n+", "\n\n", t)
            return t.strip()

        def extract_field(text: str, label: str):
            if not text:
                return None
            # stop when we hit another known label to avoid grabbing multiple fields in one match
            stop_labels = r"Play Concept|Play|Intent|Aggressiveness|Aggression|Success Probability|Success probability|Success rate|Success|Reasoning|Data-driven reasoning|Data driven reasoning|Analyst|Offensive Coordinator|Coach commentary|Analyst commentary"
            pattern = rf"{label}\s*[:\-]\s*(.*?)(?=(?:{stop_labels})|$)"
            m = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if not m:
                return None
            g = m.group(1)
            if g is None:
                return None
            # normalize whitespace and return
            return re.sub(r"\s+", " ", g).strip()

        with col_off:
            panel_start = "<div style='background: #ffffff; padding: 12px; border-radius: 8px;'>"
            st.markdown(panel_start, unsafe_allow_html=True)
            st.subheader("Offensive Coordinator")
            # prefer play/concept/intent from agent output, fallback to top_rec
            cleaned_off = clean_agent_text(off_text) if off_text else ""
            off_play = extract_field(cleaned_off, r"Play Concept|Play") or (top_rec.get("play") or top_rec.get("concept") if top_rec else None)
            off_intent = extract_field(cleaned_off, r"Intent") or (top_rec.get("explanation") or top_rec.get("intent") if isinstance(top_rec, dict) else None)

            st.markdown(f"**Play concept:** {off_play or '—'}")
            st.markdown(f"**Intent:** {off_intent or '—'}")

            # remove extracted lines and any analyst/stat fields from coach commentary
            coach_commentary = cleaned_off
            if coach_commentary:
                coach_commentary = re.sub(r"(?i)Play Concept\s*[:\-].*", "", coach_commentary)
                coach_commentary = re.sub(r"(?i)Intent\s*[:\-].*", "", coach_commentary)
                coach_commentary = re.sub(r"(?i)(Aggressiveness|Aggression)\s*[:\-].*", "", coach_commentary)
                coach_commentary = re.sub(r"(?i)(Success Probability|Success rate|Success)\s*[:\-].*", "", coach_commentary)
                coach_commentary = re.sub(r"(?i)(Reasoning|Data-driven reasoning|Data driven reasoning)\s*[:\-].*", "", coach_commentary)
                coach_commentary = coach_commentary.strip()

            if coach_commentary:
                st.markdown("**Coach commentary:**")
                st.write(coach_commentary)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_anl:
            panel_start = "<div style='background: #ffffff; padding: 12px; border-radius: 8px;'>"
            st.markdown(panel_start, unsafe_allow_html=True)
            st.subheader("Analyst")
            cleaned_anl = clean_agent_text(anl_text) if anl_text else ""

            # Extract fields from analyst text, fallback to computed values
            agg = extract_field(cleaned_anl, r"Aggressiveness|Aggression")
            sp_text = extract_field(cleaned_anl, r"Success Probability|Success probability|Success rate|Success")
            reasoning = extract_field(cleaned_anl, r"Reasoning|Data-driven reasoning|Data driven reasoning")

            # normalize success probability: prefer analyst extract, else top_rec-derived
            sp_val = None
            if sp_text:
                # try percent
                m_pct = re.search(r"([0-9]{1,3})\s*%", sp_text)
                if m_pct:
                    try:
                        sp_val = float(m_pct.group(1)) / 100.0
                    except Exception:
                        sp_val = None
                else:
                    try:
                        sp_val = float(sp_text)
                        if sp_val > 1:
                            # assume percent-like value 64 -> 0.64
                            sp_val = sp_val / 100.0
                    except Exception:
                        sp_val = None

            if sp_val is None and success_prob is not None:
                try:
                    sp_val = float(success_prob)
                except Exception:
                    sp_val = None

            # normalize aggressiveness: map synonyms and derive from text or success probability when missing
            def normalize_agg(a: str) -> str:
                if not a:
                    return None
                a_low = a.lower()
                if any(k in a_low for k in ["high", "aggressive", "aggression"]):
                    return "high"
                if any(k in a_low for k in ["medium", "moderate", "balanced", "mild", "normal"]):
                    return "medium"
                if any(k in a_low for k in ["low", "conservative", "cautious", "safe"]):
                    return "low"
                return a.strip()

            agg_norm = normalize_agg(agg)
            # try to infer from analyst free text if still missing
            if not agg_norm and cleaned_anl:
                if re.search(r"\b(high|aggressive|aggressiveness)\b", cleaned_anl, flags=re.IGNORECASE):
                    agg_norm = "high"
                elif re.search(r"\b(medium|moderate|balanced)\b", cleaned_anl, flags=re.IGNORECASE):
                    agg_norm = "medium"
                elif re.search(r"\b(low|conservative|cautious|safe)\b", cleaned_anl, flags=re.IGNORECASE):
                    agg_norm = "low"

            # infer from success probability if still unknown
            if not agg_norm and sp_val is not None:
                try:
                    if sp_val >= 0.6:
                        agg_norm = "high"
                    elif sp_val >= 0.4:
                        agg_norm = "medium"
                    else:
                        agg_norm = "low"
                except Exception:
                    agg_norm = None

            if agg_norm:
                st.markdown(f"**Aggressiveness:** {agg_norm}")
            else:
                st.markdown("**Aggressiveness:** —")

            if sp_val is not None:
                try:
                    st.markdown(f"**Success probability:** {sp_val:.0%}")
                except Exception:
                    st.markdown(f"**Success probability:** {sp_val}")
            else:
                st.markdown("**Success probability:** —")

            # Data-driven reasoning / sample evidence (from model)
            if top_rec is not None:
                concept = (top_rec.get("concept") or top_rec.get("play")) if isinstance(top_rec, dict) else None
                if concept and hasattr(df_model, "loc"):
                    try:
                        df_match = df_model[df_model.apply(lambda r: concept.lower() in str(r).lower(), axis=1)].head(5)
                        if not df_match.empty:
                            st.markdown("**Data-driven evidence (sample):**")
                            st.dataframe(df_match)
                    except Exception:
                        pass

            # analyst commentary: don't restate play concept/intent; show extracted reasoning separately
            anl_commentary = cleaned_anl
            if anl_commentary:
                anl_commentary = re.sub(r"(?i)Play Concept\s*[:\-].*", "", anl_commentary)
                anl_commentary = re.sub(r"(?i)Intent\s*[:\-].*", "", anl_commentary)
                # remove fields we've extracted so they don't duplicate
                anl_commentary = re.sub(r"(?i)(Aggressiveness|Aggression)\s*[:\-].*", "", anl_commentary)
                anl_commentary = re.sub(r"(?i)(Success Probability|Success rate|Success)\s*[:\-].*", "", anl_commentary)
                # keep reasoning extracted separately (do not remove it here if we will display separately)
                anl_commentary = re.sub(r"(?i)(Reasoning|Data-driven reasoning|Data driven reasoning)\s*[:\-].*", "", anl_commentary)
                anl_commentary = anl_commentary.strip()

            # Display extracted reasoning first (preferred)
            if reasoning:
                st.markdown("**Data-driven reasoning:**")
                st.write(re.sub(r"\s+", " ", reasoning).strip())
            elif anl_commentary:
                # if no explicit reasoning field, show evidence or remaining commentary
                st.markdown("**Analyst commentary:**")
                st.write(anl_commentary)
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception:
        st.error("Failed to compute agent commentary.")
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
