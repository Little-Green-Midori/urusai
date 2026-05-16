"""LangGraph 1.x StateGraph for URUSAI agent runs.

Builds the LangGraph StateGraph with a pooled AsyncPostgresSaver checkpointer.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Literal

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from urusai.agent.nodes import (
    escalator_node,
    finalize_node,
    integrator_node,
    observer_node,
    retriever_node,
)
from urusai.agent.state import MAX_TURNS, AgentState


def _retriever_route(state: AgentState) -> Literal["enough", "escalate", "give_up"]:
    """Conditional edge after retriever — integrate, escalate, or abstain."""
    if state.abstain_kind == "structural":
        return "enough"
    if state.escalation_count >= MAX_TURNS:
        return "give_up"
    if not state.retrieved_evidence or state.conflict_flags:
        return "escalate"
    return "enough"


@asynccontextmanager
async def build_graph(dsn: str) -> AsyncIterator:
    """Compile the agent graph with a pooled AsyncPostgresSaver checkpointer.

    Pool-mode (AsyncConnectionPool) gives roughly 2.71x throughput vs from_conn_string()
    under two concurrent agent threads.

    prepare_threshold=None + supports_pipeline=False jointly guard against
    LangGraph Issues #3193 / #3716 / #7259 (pipeline mode deadlocks on
    ON CONFLICT + RETURNING + executemany).

    AsyncPostgresSaver takes a raw postgresql:// DSN (no +asyncpg suffix).
    """
    async with AsyncConnectionPool(
        conninfo=dsn,
        min_size=1,
        max_size=20,
        max_idle=300,
        max_lifetime=1800,
        kwargs={
            "autocommit": True,
            "prepare_threshold": None,
            "row_factory": dict_row,
            "keepalives": 1,
            "keepalives_idle": 60,
            "keepalives_interval": 15,
            "keepalives_count": 4,
        },
        open=False,
        check=AsyncConnectionPool.check_connection,
    ) as pool:
        await pool.open()

        checkpointer = AsyncPostgresSaver(pool)  # type: ignore[arg-type]
        checkpointer.supports_pipeline = False
        await checkpointer.setup()

        builder: StateGraph = StateGraph(AgentState)
        builder.add_node("observer", observer_node)
        builder.add_node("retriever", retriever_node)
        builder.add_node("escalator", escalator_node)
        builder.add_node("integrator", integrator_node)
        builder.add_node("finalize", finalize_node)

        builder.add_edge(START, "observer")
        builder.add_edge("observer", "retriever")
        builder.add_conditional_edges(
            "retriever",
            _retriever_route,
            {
                "enough": "integrator",
                "escalate": "escalator",
                "give_up": "integrator",
            },
        )
        builder.add_edge("escalator", "retriever")
        builder.add_edge("integrator", "finalize")
        builder.add_edge("finalize", END)

        yield builder.compile(checkpointer=checkpointer)
