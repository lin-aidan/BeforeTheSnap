import asyncio
import re

from src.load_data import load_data
from src.preprocess import merge_data
from src.features import add_features
from src.model import build_model
from src.recommend import recommend_play
from src.parser import parse_input

from agents import offensive_coordinator, analyst


def extract_concept(text):
    match = re.search(r'Play Concept:\s*([a-zA-Z_]+)', text, re.IGNORECASE)
    return match.group(1).lower() if match else None


async def main():

    # ===============================
    # 🔹 LOAD MODEL ONCE
    # ===============================
    df_game, df_map = load_data()
    df = merge_data(df_game, df_map)
    df = add_features(df)
    df_model = build_model(df)

    while True:

        prompt = input("\nEnter situation (or 'quit'): ")

        if prompt.lower() == "quit":
            break

        # ===============================
        # 🔹 PARSE INPUT
        # ===============================
        try:
            down, distance = parse_input(prompt)
        except:
            print("Could not understand input.")
            continue

        # ===============================
        # 🔹 GET TOP PLAYS (DATA MODEL)
        # ===============================
        plays = recommend_play(df_model, down, distance)

        if not plays:
            print("No plays returned from model.")
            continue

        # ===============================
        # 🧠 DETERMINISTIC PLAY SELECTION
        # ===============================
        top_play = plays[0]
        concept = top_play["concept"].lower()
        play_stats = [top_play]

        # ===============================
        # 🧠 STEP 1 — OFFENSIVE COORDINATOR
        # ===============================
        oc_prompt = f"""
Situation:
{prompt}

Down: {down}
Distance: {distance}

Selected Play Concept (from model):
{concept}

Explain why this is the best play call in this situation.
"""

        oc_response = await offensive_coordinator.run(oc_prompt + " /no_think")

        if not oc_response or not oc_response.text:
            print("No response from offensive coordinator.")
            continue

        oc_output = oc_response.text

        # ===============================
        # 📊 STEP 2 — ANALYST
        # ===============================
        analyst_prompt = f"""
Situation:
{prompt}

Parsed:
Down: {down}
Distance: {distance}

Coordinator Decision:
{oc_output}

Play Data Used:
{play_stats}

Evaluate:
- Aggressiveness
- Success Probability
- Data-driven reasoning only
"""

        analyst_response = await analyst.run(analyst_prompt + " /no_think")

        if not analyst_response or not analyst_response.text:
            print("No response from analyst.")
            continue

        analyst_output = analyst_response.text

        # ===============================
        # 🖨️ OUTPUT
        # ===============================
        print("\n--- Offensive Coordinator ---")
        print(oc_output)

        print("\n--- Analyst ---")
        print(analyst_output)

        print("\n--- Data Used ---")
        print(play_stats)


if __name__ == "__main__":
    asyncio.run(main())
