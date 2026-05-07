# BeforeTheSnap

A play-recommendation prototype that analyzes historical play data and suggests high-probability play concepts for given downs and distances. This repository includes a Python-based recommendation pipeline and a Streamlit prototype UI to interact with the model.

## Quick Overview
- Model pipeline lives in the `src/` package and produces recommended plays given `down` and `distance`.
- Data CSVs are in the `data/` folder.
- Streamlit prototype (recommended MVP) is available at `web/streamlit_app.py` to interactively query the model.
- The repo's CLI orchestration is in [main.py](main.py) for reference.

## Features
- Parse natural-language queries (e.g., "3rd and 7") using the existing parser.
- Return top plays with scores and optional explanatory text.
- Optional AI agent commentary (offensive_coordinator / analyst) behind a toggle; best-effort call to existing orchestration.

## Getting Started

Prerequisites
- Python 3.9+ recommended
- Install required Python packages:
```bash
pip install -r requirements.txt
```

Run the Streamlit prototype:
```bash
streamlit run web/streamlit_app.py
```

## Data
Place CSV files in the `data/` directory. The repo already contains:
- `data/MU_2025_off.csv` — game/play data
- `data/plays.csv` — play mapping and concepts

Expected data shape (after preprocessing): columns such as `down`, `distance`, `play`, `concept`, `yds_gained`, and a derived `success` flag.

## Important Code References
- Recommendation logic and API:
	- [src/recommend.py](src/recommend.py) — core recommendation functions (recommend_play, recommend, get_bucket)
	- [src/parser.py](src/parser.py) — natural language parser that converts text to (down, distance)
- Data pipeline:
	- [src/load_data.py](src/load_data.py) — CSV loaders
	- [src/preprocess.py](src/preprocess.py) — data merging/cleaning
	- [src/features.py](src/features.py) — feature engineering
	- [src/model.py](src/model.py) — model/bayesian smoothing and bucket stats
- Orchestration / AI agents:
	- [main.py](main.py) — existing orchestration and agent calls (used for optional commentary)

## Streamlit Prototype (what it does)
The recommended Streamlit script (web/streamlit_app.py) should:
- Load the model at startup via the existing `src/` pipeline.
- Present a text input for natural-language queries plus structured inputs (down, distance).
- Show a results table with columns: Play, Concept, Score.
- Provide per-result expanders for explanations when available.
- Provide a sidebar for sample data and model bucket stats.
- Offer a checkbox to toggle AI agent commentary; if enabled, call the repo orchestration (best-effort) and display returned text.

## Example Input / Output
Input (either):
- JSON: `{"query": "3rd and 7"}`
- Structured: `{"down": 3, "distance": 7}`

Example output (list):
```json
[
	{"play": "RPO-Lead", "concept": "Run-Concept", "score": 0.72, "explanation":"High success vs medium-distance defenses"},
	{"play": "Shotgun-Sprint", "concept":"Pass-Concept", "score":0.63},
	{"play": "Zone-Read", "concept":"Run-Concept", "score":0.58}
]
```

## Development & Testing
- Add a smoke test that imports the pipeline and asserts the recommendation function returns a list and expected keys.
- Suggested test file: `web/test_smoke.py` (imports `src` modules and runs a quick end-to-end check).
- Use `pytest` for running tests:
```bash
pip install pytest
pytest
```

## Troubleshooting
- If `streamlit run` fails because of missing packages, ensure `streamlit` is listed in `requirements.txt` and re-run `pip install -r requirements.txt`.
- If model-building fails due to unexpected CSV shapes, inspect `data/` files and run the preprocessing steps interactively in a Python REPL to debug.
- AI agent commentary may require networked LLM access or credentials; the Streamlit checkbox is best-effort and will fall back gracefully if agents are unreachable.

## Next Steps / Improvements
- Add an endpoint-based backend (FastAPI) if you want a separate SPA or mobile UI.
- Add a CSV upload feature in the UI to allow re-training or experimenting with different datasets.
- Add CI that runs the smoke test and (optionally) starts the Streamlit app in headless mode for basic UI checks.

## Files To Add (suggested)
- web/streamlit_app.py — Streamlit app (prototype UI)
- web/test_smoke.py — simple smoke test
- web/README.md — short developer notes for the UI

## License
Add a license file if you intend to open-source the project (e.g., MIT or Apache 2.0).

---

If you want, I can now run the smoke test and start the Streamlit app in the environment; tell me which to run next.