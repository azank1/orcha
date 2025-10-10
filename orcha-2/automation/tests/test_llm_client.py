import asyncio
import os
import sys

# Make script runnable directly: add project root to sys.path
if __package__ is None:
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.normpath(os.path.join(this_dir, "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from automation.core.llm_client import LLMClient

async def main():
    llm = LLMClient()
    print("-- Scenario: order intent --")
    res1 = await llm.classify_intent("I want to order two pizzas for pickup")
    print(res1)

    print("-- Scenario: search intent --")
    res2 = await llm.classify_intent("Show me available burgers")
    print(res2)

    print("-- Scenario: unknown --")
    res3 = await llm.classify_intent("Tell me a story")
    print(res3)

if __name__ == "__main__":
    asyncio.run(main())
