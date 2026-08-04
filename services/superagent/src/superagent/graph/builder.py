"""Build the SuperAgent LangGraph StateGraph.

Topology (Slice 1 — DAG edges are inert unless active_plan is running):
    orchestrator_llm ──(agent_calls)──► execute_agent_calls ──► orchestrator_llm
          │                                  ▲      │                (loop)
          │(respond)──► respond ──► END      │      │(plan running)
          │                                  │      ▼
          └──(plan running)────────────► execute_dag_plan
"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ..graph.state import AgentState


def _plan_running(state: dict[str, Any]) -> bool:
    plan = state.get("active_plan")
    return isinstance(plan, dict) and plan.get("status") == "running"


def route_after_orchestrator(state: dict[str, Any]) -> str:
    """Route based on plan state, CDV stop guard, then emitted tool calls."""
    if _plan_running(state):
        return "execute_dag_plan"
    from ..config import settings as _settings

    if _settings.cdv_verification_enabled:
        from ..verification.cdv_integration import stopper_should_stop

        if stopper_should_stop(state):
            return "respond"
    messages = state.get("messages", [])
    if not messages:
        return "respond"
    last = messages[-1]
    tool_calls = getattr(last, "tool_calls", None)
    if tool_calls:
        return "agent_calls"
    return "respond"


def route_after_execution(state: dict[str, Any]) -> str:
    """After tool execution: continue the plan, or loop back to the LLM."""
    if _plan_running(state):
        return "execute_dag_plan"
    return "orchestrator_llm"


def route_after_dag_step(state: dict[str, Any]) -> str:
    """After the DAG node dispatched a synthetic call (or finished the plan)."""
    messages = state.get("messages", [])
    last = messages[-1] if messages else None
    if getattr(last, "tool_calls", None):
        return "execute_agent_calls"
    return "orchestrator_llm"


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
    from ..nodes.execute_dag_plan import execute_dag_plan_node
    from ..nodes.orchestrator import orchestrator_llm_node
    from ..nodes.respond import respond_node

    graph = StateGraph(AgentState)  # type: ignore[arg-type]

    graph.add_node("orchestrator_llm", orchestrator_llm_node)
    graph.add_node("execute_agent_calls", execute_agent_calls_node)
    graph.add_node("execute_dag_plan", execute_dag_plan_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("orchestrator_llm")

    graph.add_conditional_edges(
        "orchestrator_llm",
        route_after_orchestrator,
        {
            "agent_calls": "execute_agent_calls",
            "respond": "respond",
            "execute_dag_plan": "execute_dag_plan",
        },
    )
    graph.add_conditional_edges(
        "execute_agent_calls",
        route_after_execution,
        {
            "orchestrator_llm": "orchestrator_llm",
            "execute_dag_plan": "execute_dag_plan",
        },
    )
    graph.add_conditional_edges(
        "execute_dag_plan",
        route_after_dag_step,
        {
            "execute_agent_calls": "execute_agent_calls",
            "orchestrator_llm": "orchestrator_llm",
        },
    )
    graph.add_edge("respond", END)

    checkpointer = checkpointer_override or MemorySaver()
    return graph.compile(checkpointer=checkpointer)
