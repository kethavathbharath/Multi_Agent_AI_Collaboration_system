import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END

from core.state import AgentState
from core.agents.manager import manager_node
from core.agents.research import research_node
from core.agents.analysis import analysis_node
from core.agents.writer import writer_node
from core.agents.reviewer import reviewer_node
from config.settings import settings


logger = logging.getLogger(__name__)


def should_continue_review(
    state: AgentState,
) -> Literal["writer", "__end__"]:

    status = state.get("status", "")

    iterations = state.get(
        "review_iteration",
        0
    )

    max_cycles = state.get(
        "max_review_cycles",
        settings.MAX_REVIEW_ITERATIONS
    )

    if (
        status == "revision_requested"
        and iterations < max_cycles
    ):

        logger.info(
            "Reviewer requested revision. "
            f"Sending back to Writer. "
            f"Iteration: {iterations + 1}"
        )

        return "writer"

    logger.info(
        "Review completed. Ending workflow."
    )

    return END


def build_agent_graph():

    logger.info(
        "Building Multi-Agent workflow..."
    )

    builder = StateGraph(
        AgentState
    )

    builder.add_node(
        "manager",
        manager_node
    )

    builder.add_node(
        "research",
        research_node
    )

    builder.add_node(
        "analysis",
        analysis_node
    )

    builder.add_node(
        "writer",
        writer_node
    )

    builder.add_node(
        "reviewer",
        reviewer_node
    )

    # Main workflow

    builder.add_edge(
        START,
        "manager"
    )

    builder.add_edge(
        "manager",
        "research"
    )

    builder.add_edge(
        "research",
        "analysis"
    )

    builder.add_edge(
        "analysis",
        "writer"
    )

    builder.add_edge(
        "writer",
        "reviewer"
    )

    # Reviewer decision

    builder.add_conditional_edges(
        "reviewer",
        should_continue_review,
        {
            "writer": "writer",
            END: END,
        },
    )

    graph = builder.compile()

    logger.info(
        "Multi-Agent workflow "
        "compiled successfully."
    )

    return graph


# Global compiled graph

agent_graph = build_agent_graph()


def run_multi_agent_workflow(
    task_id: str,
    user_request: str,
    max_review_cycles: int = None,
) -> AgentState:

    logger.info(
        f"Starting Multi-Agent workflow "
        f"for task: {task_id}"
    )

    if max_review_cycles is None:

        max_review_cycles = (
            settings.MAX_REVIEW_ITERATIONS
        )

    max_review_cycles = max(
        1,
        min(
            int(max_review_cycles),
            4
        )
    )

    initial_state: AgentState = {

        "task_id": task_id,

        "user_request": user_request,

        "status": "decomposing",

        # NEW
        "max_review_cycles": max_review_cycles,

        "subtasks": [],

        "research_results": [],

        "analysis_results": [],

        "draft_response": "",

        "review_feedback": {},

        "review_iteration": 0,

        "agent_logs": [],

        "final_output": "",

        "error": None,
    }

    try:

        final_state = agent_graph.invoke(
            initial_state
        )

        logger.info(
            f"Workflow completed successfully "
            f"for task: {task_id}"
        )

        return final_state

    except Exception as e:

        logger.error(
            f"Workflow failed for task "
            f"{task_id}: {e}",
            exc_info=True,
        )

        initial_state[
            "status"
        ] = "failed"

        initial_state[
            "error"
        ] = str(e)

        return initial_state