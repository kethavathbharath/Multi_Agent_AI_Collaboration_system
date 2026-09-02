from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):

    user_request: str = Field(
        ...,
        description=(
            "The complex task or prompt submitted "
            "by the user."
        )
    )

    provider: Optional[str] = Field(
        None,
        description="Optional LLM provider"
    )

    model_name: Optional[str] = Field(
        None,
        description="Optional model name"
    )

    # NEW
    max_review_cycles: int = Field(
        default=1,
        ge=1,
        le=4,
        description=(
            "Maximum number of Writer-Reviewer "
            "review cycles."
        )
    )


class TaskResponse(BaseModel):

    task_id: str

    user_request: str

    status: str

    final_output: Optional[str] = None

    subtasks: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    research_results: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    analysis_results: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    agent_logs: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    review_feedback: Dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: Optional[str] = None

    updated_at: Optional[str] = None


class TaskListResponse(BaseModel):

    tasks: List[Dict[str, Any]]