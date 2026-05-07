from agent_framework.ollama import OllamaChatClient
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework import Agent
from agent_framework.orchestrations import SequentialBuilder

# client = OllamaChatClient(model="qwen3:4b")
client = OpenAIChatCompletionClient(
    model="Qwen/Qwen2.5-7B-Instruct-AWQ",
    api_key="N/A",
    base_url="http://100.109.137.83:8000/v1",
)

offensive_coordinator = Agent(
    client=client,
    name="offensive_coordinator",
    instructions=(
        "You are an offensive coordinator in American football.\n\n"

        "You are given valid play concepts from real data.\n"
        "You MUST choose ONE concept EXACTLY as written.\n\n"

        "Output EXACTLY:\n"
        "Play Concept: <exact concept>\n"
        "Intent: <football reasoning for why this works in this situation>\n\n"

        "Intent should explain:\n"
        "- what the play attacks (coverage/space)\n"
        "- why it fits the down & distance\n\n"

        "Do NOT be generic.\n"
    )
)


analyst = Agent(
    client=client,
    name="analyst",
    instructions=(
        "You are a football analytics expert.\n\n"

        "Evaluate the play call using provided data.\n\n"

        "Output:\n"
        "Aggressiveness: low/medium/high\n"
        "Success Probability: <0-100>%\n"
        "Reasoning: <short explanation>\n\n"

        "Be data-driven.\n"
    )
)


workflow = SequentialBuilder(participants=[offensive_coordinator, analyst]).build()
