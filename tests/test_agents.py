import pytest
from core.state import AgentState
from core.agents import manager_node, research_node, analysis_node, writer_node, reviewer_node
from core.agents.reviewer import parse_reviewer_response

def test_parse_reviewer_response_robustness():
    # 1. Plain text with leading commentary
    text_response = "Here is the audit:\n{\n  \"approved\": true,\n  \"quality_score\": 9,\n  \"feedback_comments\": [\"Solid analysis\"],\n  \"suggested_improvements\": \"None\"\n}"
    res1 = parse_reviewer_response(text_response)
    assert res1.approved is True
    assert res1.quality_score == 9
    assert "Solid analysis" in res1.feedback_comments

    # 2. Non-JSON plain text response
    plain_text = "The response looks great and covers all required aspects."
    res2 = parse_reviewer_response(plain_text)
    assert res2.approved is True
    assert res2.quality_score == 8
    assert len(res2.feedback_comments) > 0

def test_manager_node():
    initial_state: AgentState = {
        "task_id": "test-task-1",
        "user_request": "Analyze the impact of AI on education.",
        "status": "decomposing",
        "subtasks": [],
        "research_results": [],
        "analysis_results": [],
        "draft_response": "",
        "review_feedback": {},
        "review_iteration": 0,
        "agent_logs": [],
        "final_output": "",
        "error": None
    }

    result = manager_node(initial_state)
    assert "subtasks" in result
    assert len(result["subtasks"]) > 0
    assert result["status"] == "executing_subtasks"
    assert len(result["agent_logs"]) > 0

def test_research_and_analysis_nodes():
    state: AgentState = {
        "task_id": "test-task-2",
        "user_request": "Analyze AI on education.",
        "status": "executing_subtasks",
        "subtasks": [
            {
                "id": "st-1",
                "title": "Educational Research",
                "description": "Gather facts on AI learning tools.",
                "assigned_agent": "Research Agent",
                "status": "pending"
            },
            {
                "id": "st-2",
                "title": "Impact Analysis",
                "description": "Analyze trends and impact.",
                "assigned_agent": "Analysis Agent",
                "status": "pending"
            }
        ],
        "research_results": [],
        "analysis_results": [],
        "draft_response": "",
        "review_feedback": {},
        "review_iteration": 0,
        "agent_logs": [],
        "final_output": "",
        "error": None
    }

    res_state = research_node(state)
    assert len(res_state["research_results"]) > 0
    res_content = res_state["research_results"][0]["content"]
    # Dynamic MockLLM always returns relevant text with these markers
    assert "Research" in res_content or "Background" in res_content or "Overview" in res_content or "Applications" in res_content
    assert '"assigned_agent"' not in res_content

    state.update(res_state)
    ana_state = analysis_node(state)
    assert len(ana_state["analysis_results"]) > 0
    ana_content = ana_state["analysis_results"][0]["content"]
    assert "Analysis" in ana_content or "Analytical" in ana_content or "Evaluation" in ana_content or "Benefits" in ana_content
    assert '"assigned_agent"' not in ana_content

def test_writer_and_reviewer_nodes():
    state: AgentState = {
        "task_id": "test-task-3",
        "user_request": "Analyze AI on education.",
        "status": "executing_subtasks",
        "subtasks": [],
        "research_results": [{"subtask_title": "Research", "content": "AI aids personalized learning."}],
        "analysis_results": [{"subtask_title": "Analysis", "content": "Custom tutoring improves outcomes."}],
        "draft_response": "",
        "review_feedback": {},
        "review_iteration": 0,
        "agent_logs": [],
        "final_output": "",
        "error": None
    }

    writer_state = writer_node(state)
    assert writer_state["draft_response"] != ""
    assert writer_state["status"] == "reviewing"
    assert '"assigned_agent"' not in writer_state["draft_response"]

    state.update(writer_state)
    rev_state = reviewer_node(state)
    assert "review_feedback" in rev_state
    assert rev_state["final_output"] != ""
    assert '"assigned_agent"' not in rev_state["final_output"]

def test_dynamic_output_relevance():
    """Verify that the dynamic MockLLM generates content relevant to the actual user topic."""
    from core.llm import _build_research_response, _build_analysis_response, _build_writer_response

    topic = "Explain the importance of cybersecurity for businesses."

    research = _build_research_response(topic)
    assert "cybersecurity" in research.lower() or topic[:15].lower() in research.lower()
    assert "applications" in research.lower() or "use cases" in research.lower()
    assert '"assigned_agent"' not in research

    analysis = _build_analysis_response(topic)
    assert "benefit" in analysis.lower() or "advantage" in analysis.lower()
    assert "challenge" in analysis.lower() or "limitation" in analysis.lower()
    assert '"assigned_agent"' not in analysis

    writer = _build_writer_response(topic, research, analysis)
    assert "# Comprehensive Analysis Report" in writer
    assert "Benefits" in writer
    assert "Challenges" in writer
    assert "Future Scope" in writer
    assert "Conclusion" in writer
    assert len(writer) > 500
