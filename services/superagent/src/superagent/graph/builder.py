"""Build the SuperAgent LangGraph StateGraph.

Topology:
    orchestrator_llm ──(agent_calls)──► execute_agent_calls ──► orchestrator_llm
          │                                                             (loop)
          └──(respond)──► respond ──► END
"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ..graph.state import AgentState


def route_after_orchestrator(state: dict[str, Any]) -> str:
    """Route based on whether the LLM emitted tool calls."""
    messages = state.get("messages", [])
    if not messages:
        return "respond"
    last = messages[-1]
    tool_calls = getattr(last, "tool_calls", None)
    if tool_calls:
        return "agent_calls"
    return "respond"


def build_superagent_graph(
    checkpointer_override: Any = None,
) -> Any:
    """
    Construct and compile the SuperAgent StateGraph.

    Args:
        checkpointer_override: Pass ``MemorySaver()`` in tests; in production
            the lifespan wires a ``RedisSaver`` and injects it here.

    Returns:
        A compiled LangGraph ``CompiledGraph``.
    """
    # Import node functions here to avoid circular imports
    from ..nodes.execute_agent_calls import execute_agent_calls_node
    from ..nodes.orchestrator import orchestrator_llm_node
    from ..nodes.respond import respond_node

    graph = StateGraph(AgentState)  # type: ignore[arg-type]

    graph.add_node("orchestrator_llm", orchestrator_llm_node)
    graph.add_node("execute_agent_calls", execute_agent_calls_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("orchestrator_llm")

    graph.add_conditional_edges(
        "orchestrator_llm",
        route_after_orchestrator,
        {
            "agent_calls": "execute_agent_calls",
            "respond": "respond",
        },
    )
    graph.add_edge("execute_agent_calls", "orchestrator_llm")
    graph.add_edge("respond", END)

    checkpointer = checkpointer_override or MemorySaver()
    return graph.compile(checkpointer=checkpointer)
