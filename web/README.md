# BeforeTheSnap — Streamlit prototype

Install:
```
pip install -r requirements.txt
```

Run:
```
streamlit run web/streamlit_app.py
```

Notes:
- The app loads the existing `src/` pipeline at startup.
- AI agent commentary is optional and may require network/LLM access or a wrapper `explain_query` in `main.py`.
