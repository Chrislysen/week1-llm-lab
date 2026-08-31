from agents import Agent
from budget import Budget
from llm_client import make_client
import argparse


# ==================================================
# EXERCISE C - CHOSEN SCENARIO
# ==================================================
#
# Scenario:
# Two university advisors debate whether universities
# should widely integrate AI into teaching and learning.
#
# Agent A supports broad AI adoption.
# Agent B is cautious and focuses on risks.
# ==================================================


agent_a = Agent(
    name="Dr. Nova",
    system_prompt=(
        "You are Dr. Nova, a university technology advisor. "
        "You strongly support integrating artificial intelligence into "
        "university education. Your goal is to persuade the other advisor "
        "that AI can improve learning through personalized tutoring, "
        "faster feedback, accessibility, and support for instructors. "
        "Respond directly to the other advisor's arguments. "
        "Use evidence-based reasoning and remain professional. "
        "Keep each response to no more than 3 sentences."
    ),
    temperature=0
)


agent_b = Agent(
    name="Dr. Reed",
    system_prompt=(
        "You are Dr. Reed, a university academic-integrity and education advisor. "
        "You are skeptical of widespread AI integration in universities. "
        "Your goal is to challenge the other advisor by focusing on risks such as "
        "over-reliance on AI, hallucinations, academic misconduct, bias, privacy, "
        "and reduced development of independent thinking. "
        "Respond directly to the other advisor's arguments. "
        "Remain professional and acknowledge good arguments when appropriate. "
        "Keep each response to no more than 3 sentences."
    ),
    temperature=0
)


def build_history(history):

    if not history:
        return "The discussion has not started yet."

    text = ""

    for speaker, message in history:
        text += f"{speaker}: {message}\n"

    return text


def run_conversation(mock=False, max_turns=4):

    client = make_client(mock=mock)

    agents = [agent_a, agent_b]

    history = []

    budget = Budget(
        max_turns=max_turns,
        max_tokens=10000,
        max_seconds=600
    )

    print("\n======================================")
    print(" EXERCISE C - UNIVERSITY AI DEBATE")
    print("======================================\n")

    print("Scenario:")
    print(
        "Two university advisors are debating whether AI "
        "should be widely integrated into university education.\n"
    )

    print(f"Turn limit: {max_turns}\n")

    while not budget.exhausted():

        current_agent = agents[len(history) % 2]

        transcript = build_history(history)

        messages = [
            {
                "role": "system",
                "content": current_agent.system_prompt
            },
            {
                "role": "user",
                "content": (
                    "The discussion so far is:\n\n"
                    f"{transcript}\n"
                    "Continue the debate. Respond to the other advisor's "
                    "most recent argument. If nobody has spoken yet, "
                    "make your opening argument."
                )
            }
        ]

        reply = client.chat(
            current_agent.model,
            messages,
            temperature=current_agent.temperature
        )

        history.append(
            (current_agent.name, reply.text)
        )

        budget.record(
            turns=1,
            tokens=reply.tokens
        )

        print(f"{current_agent.name}:")
        print(reply.text)
        print()

    print("======================================")
    print(" DISCUSSION FINISHED")
    print("======================================")
    print(f"Reason: {budget.stop_reason}")
    print(f"Turns completed: {budget.turns}")
    print(f"Tokens used: {budget.tokens}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mock",
        action="store_true"
    )

    parser.add_argument(
        "--turns",
        type=int,
        default=4
    )

    args = parser.parse_args()

    run_conversation(
        mock=args.mock,
        max_turns=args.turns
    )