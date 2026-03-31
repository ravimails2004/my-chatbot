"""
Interactive CLI for testing the Claude agent locally without Teams.

Usage:
    python test_agent.py
"""
import asyncio
import agent


async def main():
    print("Azure DevOps Pipeline Assistant (local test mode)")
    print("Type 'exit' to quit, 'reset' to clear conversation history.\n")

    history: list[dict] = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            break
        if user_input.lower() == "reset":
            history.clear()
            print("Conversation history cleared.\n")
            continue

        print("Agent: ", end="", flush=True)
        response = await agent.run_agent(user_input, history)
        print(response)

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        print()


if __name__ == "__main__":
    asyncio.run(main())
