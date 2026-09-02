import pytest
import json
from frontend.app import generate_markdown_report, get_agent_actual_output, extract_clean_content

def test_generate_markdown_report():
    sample_res = {
        "task_id": "task-test1234",
        "user_request": "Analyze the impact of AI on education.",
        "status": "completed",
        "created_at": "2026-08-28 20:00:00",
        "subtasks": [
            {
                "id": "st-1",
                "title": "Data Gathering",
                "assigned_agent": "Research Agent",
                "description": "Collect research background.",
                "status": "completed",
                "result": "AI aids personalized learning tools."
            },
            {
                "id": "st-2",
                "title": "Trend Analysis",
                "assigned_agent": "Analysis Agent",
                "description": "Evaluate trends and implications.",
                "status": "completed",
                "result": "Custom tutoring improves student retention."
            }
        ],
        "research_results": [
            {
                "subtask_id": "st-1",
                "subtask_title": "Data Gathering",
                "content": "AI aids personalized learning tools."
            }
        ],
        "analysis_results": [
            {
                "subtask_id": "st-2",
                "subtask_title": "Trend Analysis",
                "content": "Custom tutoring improves student retention."
            }
        ],
        "review_feedback": {
            "approved": True,
            "quality_score": 9,
            "feedback_comments": ["Clear structure and relevant details."],
            "suggested_improvements": "None"
        },
        "final_output": "# Report Title\n\nThis is the final synthesized output."
    }

    report = generate_markdown_report(sample_res)

    assert "# Executive Report: Multi-Agent Task Collaboration" in report
    assert "Task ID**: `task-test1234`" in report
    assert "## 📌 1. User Task Details" in report
    assert "## 📋 2. Task Decomposition & Subtasks Breakdown" in report
    assert "Assigned Agent**: `Research Agent`" in report
    assert "## 🛡️ 3. Quality Audit & Reviewer Feedback" in report
    assert "Quality Score**: `9 / 10`" in report
    assert "## 📄 4. Final Synthesized Output" in report
    assert "## 🎯 5. Final Answer / Actual Output" in report
    assert "# Report Title" in report

def test_agent_actual_output_no_metadata_json():
    sample_res = {
        "task_id": "task-test999",
        "user_request": "Analyze AI in education.",
        "status": "completed",
        "subtasks": [
            {
                "id": "st-1",
                "title": "Research Task",
                "description": "Gather data",
                "assigned_agent": "Research Agent",
                "result": "Actual research finding: Intelligent tutoring tools increase math scores by 20%."
            },
            {
                "id": "st-2",
                "title": "Analysis Task",
                "description": "Analyze trends",
                "assigned_agent": "Analysis Agent",
                "result": "Actual analytical finding: Cost of deployment is offset by long-term faculty efficiency."
            }
        ],
        "research_results": [
            {"subtask_id": "st-1", "content": "Actual research finding: Intelligent tutoring tools increase math scores by 20%."}
        ],
        "analysis_results": [
            {"subtask_id": "st-2", "content": "Actual analytical finding: Cost of deployment is offset by long-term faculty efficiency."}
        ]
    }

    research_output = get_agent_actual_output(sample_res, "Research Agent", "st-1")
    analysis_output = get_agent_actual_output(sample_res, "Analysis Agent", "st-2")

    # Assert actual response text is returned
    assert "Actual research finding: Intelligent tutoring tools increase math scores by 20%." in research_output
    assert "Actual analytical finding: Cost of deployment is offset by long-term faculty efficiency." in analysis_output

    # Assert subtask metadata JSON strings are filtered out
    raw_metadata_json = json.dumps({
        "id": "st-1",
        "title": "Research Task",
        "description": "Gather data",
        "assigned_agent": "Research Agent"
    })
    cleaned = extract_clean_content(raw_metadata_json)
    assert cleaned == ""
    assert '"assigned_agent"' not in cleaned
    assert '"id":' not in cleaned
