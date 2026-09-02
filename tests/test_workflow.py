import pytest
from core.workflow import run_multi_agent_workflow

def test_full_multi_agent_workflow():
    task_id = "test-e2e-1"
    prompt = "Analyze the impact of Artificial Intelligence on software engineering."

    final_state = run_multi_agent_workflow(task_id, prompt)

    assert final_state["task_id"] == task_id
    assert final_state["status"] == "completed"
    assert len(final_state["subtasks"]) > 0
    assert len(final_state["research_results"]) > 0
    assert len(final_state["analysis_results"]) > 0
    assert final_state["draft_response"] != ""
    assert final_state["final_output"] != ""
    assert final_state["review_feedback"]["approved"] is True
