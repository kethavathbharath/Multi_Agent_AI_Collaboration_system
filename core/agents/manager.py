import json
import logging
from typing import Dict, Any, List
from core.state import AgentState, AgentLog, SubTask
from core.llm import get_llm

logger = logging.getLogger(__name__)

MANAGER_PROMPT = """Role: Manager Agent
System Instruction: You are the Manager Agent performing Task Decomposition in a Multi-Agent AI Collaboration System.
Your job is to analyze the user request, break it down into 2 to 4 distinct, non-overlapping subtasks, and assign each subtask to an appropriate specialized agent ('Research Agent' or 'Analysis Agent').

User Request: {user_request}

Return a strict JSON object with the key "subtasks", containing a list of subtasks with the following fields:
- "id": unique string ID (e.g. "st-1", "st-2")
- "title": short title of the subtask
- "description": clear explanation of what needs to be done
- "assigned_agent": either "Research Agent" or "Analysis Agent"

Respond ONLY with valid JSON.
"""

def manager_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Manager Node running for Task ID: {state['task_id']}")
    
    logs = list(state.get("agent_logs", []))
    logs.append(AgentLog(
        agent_name="Manager Agent",
        action="Task Decomposition",
        message="Analyzing user prompt and creating subtasks breakdown...",
        status="info"
    ).model_dump())

    llm = get_llm()
    prompt = MANAGER_PROMPT.format(user_request=state["user_request"])
    
    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Clean JSON if wrapped in markdown codeblocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        raw_subtasks = data.get("subtasks", [])
        
        subtasks = []
        for idx, st in enumerate(raw_subtasks):
            subtasks.append(SubTask(
                id=st.get("id", f"st-{idx+1}"),
                title=st.get("title", f"Subtask {idx+1}"),
                description=st.get("description", ""),
                assigned_agent=st.get("assigned_agent", "Research Agent"),
                status="pending"
            ).model_dump())

    except Exception as e:
        logger.error(f"Error during Manager Agent decomposition: {e}")
        subtasks = [
            SubTask(
                id="st-1",
                title="Gather Domain Research",
                description="Collect relevant data, facts, and context for the user request.",
                assigned_agent="Research Agent",
                status="pending"
            ).model_dump(),
            SubTask(
                id="st-2",
                title="Analytical Evaluation",
                description="Analyze research findings and identify strategic implications.",
                assigned_agent="Analysis Agent",
                status="pending"
            ).model_dump()
        ]

    logs.append(AgentLog(
        agent_name="Manager Agent",
        action="Task Decomposition Complete",
        message=f"Created {len(subtasks)} subtasks and assigned to specialized agents.",
        status="success"
    ).model_dump())

    return {
        "subtasks": subtasks,
        "agent_logs": logs,
        "status": "executing_subtasks"
    }
