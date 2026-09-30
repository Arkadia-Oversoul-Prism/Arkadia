#!/usr/bin/env python3
"""
Render UI CodexBrain Test Script
- Sends queries to Arkana using multi-model chain
- Shows which model responded
- Logs session memory per node
"""

import asyncio
from codex_brain import CodexBrain

async def main():
    brain = CodexBrain()

    # Define multi-model chain
    model_chain = [
        {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": "<YOUR_GEMINI_KEY>"},
        {"provider": "openai", "model": "gpt-4.1", "api_key": "<YOUR_OPENAI_KEY>"},
        {"provider": "local", "model": "llama-2-13b", "api_key": None},
    ]

    # Test nodes
    test_nodes = {
        "NodeA": "Hello Arkana! What is the current Arkadia node status?",
        "NodeB": "Please summarize the Arkadia documents."
    }

    session_memory = {}

    for node, message in test_nodes.items():
        print(f"\n=== Consulting Arkana at {node} ===")
        try:
            response = await brain.generate_reply(node, message, model_chain=model_chain)
            print(f"\n──────────── ARKANA RESPONDS ────────────\n{response}\n─────────────────────────────────────────")
            session_memory[node] = {"User": message, "Arkana": response}
        except Exception as e:
            print(f"Error consulting Arkana at {node}: {e}")

    print("\nSESSION MEMORY:")
    for node, data in session_memory.items():
        print(f"\nNode {node}:")
        for k, v in data.items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    asyncio.run(main())
