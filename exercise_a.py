from llm_client import make_client

client = make_client(mock=False)
model = "llama3.2:3b"

# --------------------------------------------------
# CALL 1
# --------------------------------------------------

name = input("Give the AI a name: ")

messages = [
    {
        "role": "system",
        "content": "You are a short and helpful assistant."
    },
    {
        "role": "user",
        "content": f"Your name is {name}. What is your name?"
    }
]

reply1 = client.chat(model, messages, temperature=0)

print("\nCALL 1:")
print("AI:", reply1.text)


# --------------------------------------------------
# CALL 2 - FRESH CALL
# --------------------------------------------------

input("\nPress ENTER to make a completely fresh call...")

fresh_messages = [
    {
        "role": "system",
        "content": "You are a short and helpful assistant."
    },
    {
        "role": "user",
        "content": "What is your name?"
    }
]

reply2 = client.chat(model, fresh_messages, temperature=0)

print("\nCALL 2 - NO HISTORY:")
print("AI:", reply2.text)


# --------------------------------------------------
# CALL 3 - HISTORY RESTORED
# --------------------------------------------------

input("\nPress ENTER to send the original history again...")

messages.append({
    "role": "assistant",
    "content": reply1.text
})

messages.append({
    "role": "user",
    "content": "What is your name?"
})

reply3 = client.chat(model, messages, temperature=0)

print("\nCALL 3 - WITH HISTORY:")
print("AI:", reply3.text)


print("\nExercise A complete.")