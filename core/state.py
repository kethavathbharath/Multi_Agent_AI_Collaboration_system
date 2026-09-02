from typing import List, Dict, Any, Optional, TypedDict

from pydantic import BaseModel, Field
from datetime import datetime


class SubTask(BaseModel):

    id: str

    title: str

    description: str

    assigned_agent: str

    status: str = "pending"

    result: Optional[str] = None


class AgentLog(BaseModel):

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )

    agent_name: str

    action: str

    message: str

    status: str = "info"


class ReviewResult(BaseModel):

    approved: bool = False

    quality_score: int = 0

    feedback_comments: List[str] = Field(
        default_factory=list
    )

    suggested_improvements: str = ""


class AgentState(TypedDict):

    task_id: str

    user_request: str

    status: str

    # NEW: selected from dashboard
    max_review_cycles: int

    subtasks: List[Dict[str, Any]]

    research_results: List[Dict[str, Any]]

    analysis_results: List[Dict[str, Any]]

    draft_response: str

    review_feedback: Dict[str, Any]

    review_iteration: int

    agent_logs: List[Dict[str, Any]]

    final_output: str

    error: Optional[str]