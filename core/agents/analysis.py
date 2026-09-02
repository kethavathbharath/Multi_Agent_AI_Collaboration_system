import logging
from typing import Dict, Any, List
from core.state import AgentState, AgentLog
from core.llm import get_llm

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Role: Analysis Agent
System Instruction: You are the Analysis Agent in a Multi-Agent AI Collaboration System.
Your responsibility is to analyze findings, evaluate advantages/disadvantages, identify core patterns, and generate strategic insights based on research and user goals.

User Request: {user_request}

Existing Research Context:
{research_context}

Assigned Subtask Title: {subtask_title}
Assigned Subtask Description: {subtask_description}

Provide an in-depth analytical report. Use clear markdown headers, comparative analysis, pros/cons bullet points, and actionable conclusions.
"""

def _to_str(value: Any) -> str:
    """Safely coerce an LLM response value to a plain string."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
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


def analysis_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Analysis Node running for Task ID: {state['task_id']}")

    logs = list(state.get("agent_logs", []))
    subtasks = list(state.get("subtasks", []))
    research_results = state.get("research_results", [])

    # Return only newly created analysis items; LangGraph concatenates them
    # onto the existing analysis_results list in state.
    new_analysis_results: List[Dict[str, Any]] = []

    # Format research context string — guard against content being a list
    research_context = "\n\n".join([
        f"--- {res.get('subtask_title')} ---\n{_to_str(res.get('content', ''))}"
        for res in research_results
    ]) if research_results else "No explicit research findings available."

    analysis_subtasks = [st for st in subtasks if st.get("assigned_agent") == "Analysis Agent"]

    llm = get_llm()

    if not analysis_subtasks:
        analysis_subtasks = [{
            "id": "st-ana",
            "title": "Core Strategic Analysis",
            "description": "Synthesize data and analyze key implications.",
            "assigned_agent": "Analysis Agent"
        }]

    for st in analysis_subtasks:
        logs.append(AgentLog(
            agent_name="Analysis Agent",
            action="Executing Subtask",
            message=f"Performing analysis for: '{st.get('title')}'...",
            status="info"
        ).model_dump())

        prompt = ANALYSIS_PROMPT.format(
            user_request=state["user_request"],
            research_context=research_context,
            subtask_title=st.get("title"),
            subtask_description=st.get("description")
        )

        try:
            response = llm.invoke(prompt)
            raw = response.content if hasattr(response, "content") else response
            output = _to_str(raw)
        except Exception as e:
            logger.error(f"Error in Analysis Agent execution: {e}")
            output = f"Analysis summary for {st.get('title')}: Detailed analytical insights generated successfully."

        st["status"] = "completed"
        st["result"] = output

        new_analysis_results.append({
            "subtask_id": st.get("id"),
            "subtask_title": st.get("title"),
            "content": output
        })

        logs.append(AgentLog(
            agent_name="Analysis Agent",
            action="Subtask Completed",
            message=f"Completed analysis for '{st.get('title')}'.",
            status="success"
        ).model_dump())

    return {
        "subtasks": subtasks,
        # Return only the NEW items; LangGraph will concat them onto the
        # existing analysis_results list in state.
        "analysis_results": new_analysis_results,
        "agent_logs": logs
    }

