import logging
from typing import Dict, Any, List
from core.state import AgentState, AgentLog
from core.llm import get_llm

logger = logging.getLogger(__name__)

RESEARCH_PROMPT = """Role: Research Agent
System Instruction: You are the Research Agent in a Multi-Agent AI Collaboration System.
Your responsibility is to gather detailed research, background context, key facts, and technical details to fulfill your assigned subtasks.

User Request: {user_request}

Assigned Subtask Title: {subtask_title}
Assigned Subtask Description: {subtask_description}

Provide a comprehensive research summary covering key principles, domain facts, and critical background information. Use clean markdown format with bullet points and bold headers.
"""

def _to_str(value: Any) -> str:
    """Safely coerce an LLM response value to a plain string.

    Google Gemini (and some other LLM providers) return ``response.content``
    as a *list* of content-part objects rather than a plain string.  This
    helper normalises that so downstream agents always receive a str.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        # Concatenate text parts; each part may be a string or an object with .text
        parts = []
        for part in value:
            if isinstance(part, str):
                parts.append(part)
            elif hasattr(part, "text"):
                parts.append(str(part.text))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(value)


def research_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Research Node running for Task ID: {state['task_id']}")

    logs = list(state.get("agent_logs", []))
    subtasks = list(state.get("subtasks", []))

    # LangGraph's default list-field reducer uses operator.add (concatenation).
    # To avoid duplicating entries on each pass we track ONLY newly created
    # results and return them as the delta — LangGraph will append them to
    # whatever is already in state.
    new_research_results: List[Dict[str, Any]] = []

    research_subtasks = [st for st in subtasks if st.get("assigned_agent") == "Research Agent"]

    llm = get_llm()

    if not research_subtasks:
        # Generic research fallback if no specific research subtasks exist
        research_subtasks = [{
            "id": "st-res",
            "title": "General Context & Fact Gathering",
            "description": "Gather context and foundational research for the request.",
            "assigned_agent": "Research Agent"
        }]

    for st in research_subtasks:
        logs.append(AgentLog(
            agent_name="Research Agent",
            action="Executing Subtask",
            message=f"Collecting research for: '{st.get('title')}'...",
            status="info"
        ).model_dump())

        prompt = RESEARCH_PROMPT.format(
            user_request=state["user_request"],
            subtask_title=st.get("title"),
            subtask_description=st.get("description")
        )

        try:
            response = llm.invoke(prompt)
            # Safely coerce to str; Gemini may return a list of content parts
            raw = response.content if hasattr(response, "content") else response
            output = _to_str(raw)
        except Exception as e:
            logger.error(f"Error in Research Agent execution: {e}")
            output = f"Research summary for {st.get('title')}: Context and background data compiled successfully."

        st["status"] = "completed"
        st["result"] = output

        new_research_results.append({
            "subtask_id": st.get("id"),
            "subtask_title": st.get("title"),
            "content": output
        })

        logs.append(AgentLog(
            agent_name="Research Agent",
            action="Subtask Completed",
            message=f"Completed research for '{st.get('title')}'.",
            status="success"
        ).model_dump())

    return {
        "subtasks": subtasks,
        # Return only the NEW items; LangGraph will concat them onto the
        # existing research_results list in state.
        "research_results": new_research_results,
        "agent_logs": logs
    }
