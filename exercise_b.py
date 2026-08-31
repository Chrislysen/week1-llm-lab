from agents import Agent
from budget import Budget
from llm_client import make_client
import argparse


# --------------------------------------------------
# TWO DIFFERENT AGENTS
# --------------------------------------------------

agent_a = Agent(
    name="Agent A",
    system_prompt=(
        "You strongly believe artificial intelligence should be widely used "
        "in university education. Give clear arguments supporting your position. "
        "Keep every response to 2 sentences maximum."
    ),
    temperature=0
)

agent_b = Agent(
    name="Agent B",
    system_prompt=(
        "You are skeptical about artificial intelligence being widely used "
        "in university education. Challenge the other agent's arguments and "
        "point out risks or weaknesses. Keep every response to 2 sentences maximum."
    ),
    temperature=0
)


# --------------------------------------------------
# TURN THE TRANSCRIPT INTO TEXT FOR THE NEXT AGENT
# --------------------------------------------------

def show_history(history):

    if len(history) == 0:
        return "No one has spoken yet."

    text = ""

    for speaker, message in history:
        text += f"{speaker}: {message}\n"

    return text


# --------------------------------------------------
# RUN THE TWO-AGENT CONVERSATION
# --------------------------------------------------

def run_conversation(mock, max_turns):

    # Mock model for testing, real Ollama model otherwise
    client = make_client(mock=mock)

    agents = [agent_a, agent_b]

    # Shared conversation history
    history = []

    # HARD SAFETY CAP
    budget = Budget(
        max_turns=max_turns,
        max_tokens=10000,
        max_seconds=600
    )

    print("\n===== TWO AGENT CONVERSATION =====")
    print(f"Maximum turns: {max_turns}\n")

    while not budget.exhausted():

        # Alternate between Agent A and Agent B
        current_agent = agents[len(history) % 2]

        conversation = show_history(history)

        messages = [
            {
                "role": "system",
                "content": current_agent.system_prompt
            },
            {
                "role": "user",
                "content": (
                    "Here is the conversation so far:\n\n"
                    f"{conversation}\n"
                    "It is now your turn. Respond to the other agent."
                )
            }
        ]

        # Call the model
        reply = client.chat(
            current_agent.model,
            messages,
            temperature=current_agent.temperature
        )

        # Save response in shared history
        history.append(
            (current_agent.name, reply.text)
        )

        # Tell Budget that one turn happened
        budget.record(
            turns=1,
            tokens=reply.tokens
        )

        # Print transcript
        print(f"{current_agent.name}: {reply.text}\n")

    print("===== CONVERSATION STOPPED =====")
    print(f"Reason: {budget.stop_reason}")
    print(f"Turns completed: {budget.turns}")
    print(f"Tokens used: {budget.tokens}")


# --------------------------------------------------
# COMMAND LINE OPTIONS
# --------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use the fake model instead of Ollama"
    )

    parser.add_argument(
        "--turns",
        type=int,
        default=4,
        help="Number of conversation turns"
    )

    args = parser.parse_args()

    run_conversation(
        mock=args.mock,
        max_turns=args.turns
    )