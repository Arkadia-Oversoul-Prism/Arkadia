#!/usr/bin/env python3
"""
Render Test Script — Arkadia Console Preview

Purpose:
- Launch Arkadia Console in a web-friendly loop
- Demonstrate CodexBrain multi-node session memory
- Uses fallback responses (no API keys required)
"""

import asyncio
from codex_brain import CodexBrain

# Initialize brain
brain = CodexBrain()

# Multi-node session memory
session_memory = {
    "NodeA": [],
    "NodeB": []
}

# Example nodes
nodes = ["NodeA", "NodeB"]

async def test_node(node_name: str, message: str):
    """Send message to Arkana and store response in session memory."""
    response = await brain.generate_reply(node_name, message)
    session_memory[node_name].append({
        "User": message,
        "Arkana": response
    })
    print(f"\n=== Node {node_name} ===")
    print(f"User: {message}")
    print(f"Arkana: {response}")
    print("─" * 50)

async def main():
    """Main loop for testing multiple nodes."""
    print("────────────────── ARKADIA CONSOLE TEST ──────────────────")
    print("Fallback responses only (no API keys). Session memory enabled.\n")

    # Example messages
    messages = [
        "Hello Arkana, what is the current node status?",
        "Please summarize the Arkadia documents.",
        "Explain the JOY-Fuel Protocol in brief."
    ]

    # Loop through nodes and messages
    for node in nodes:
        for msg in messages:
            await test_node(node, msg)

    # Print session memory
    print("\nSESSION MEMORY:\n")
    for node, logs in session_memory.items():
        print(f"Node {node}:")
        for entry in logs:
            print(f"  User: {entry['User']}")
            print(f"  Arkana: {entry['Arkana']}")
        print("─" * 50)

if __name__ == "__main__":
    asyncio.run(main())
