import json
import html
import requests
from typing import Any

import streamlit as st


from settings import settings


st.set_page_config(
    page_title="Multi-Agent AI Collaboration System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# BACKEND
# ============================================================

BACKEND_URL = f"http://{settings.HOST}:{settings.PORT}"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_text(value: Any) -> str:

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):

        for key in [
            "content",
            "result",
            "output",
            "text",
            "final_output",
            "draft_response"
        ]:

            if key in value:

                text = safe_text(value[key])

                if text:
                    return text

        return ""

    if isinstance(value, list):

        parts = []

        for item in value:

            text = safe_text(item)

            if text:
                parts.append(text)

        return "\n".join(parts).strip()

    if hasattr(value, "content"):
        return safe_text(value.content)

    if hasattr(value, "text"):
        return safe_text(value.text)

    return str(value).strip()


def clean_content(value: Any) -> str:

    text = safe_text(value)

    if not text:
        return ""

    stripped = text.strip()

    if stripped.startswith("{") or stripped.startswith("["):

        try:

            parsed = json.loads(stripped)

            if isinstance(parsed, dict):

                for key in [
                    "content",
                    "result",
                    "output",
                    "final_output",
                    "draft_response",
                    "text"
                ]:

                    if key in parsed:

                        extracted = safe_text(parsed[key])

                        if extracted:
                            return extracted

            elif isinstance(parsed, list):

                return safe_text(parsed)

        except Exception:
            pass

    return text


def generate_report(result: dict) -> str:

    task_id = safe_text(result.get("task_id", "N/A"))
    request = safe_text(result.get("user_request", ""))
    status = safe_text(result.get("status", "completed"))

    lines = []

    lines.append("# Multi-Agent AI Collaboration System")
    lines.append("")
    lines.append(f"**Task ID:** {task_id}")
    lines.append(f"**Status:** {status}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 1. User Request")
    lines.append("")
    lines.append(request)
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 2. Task Decomposition Breakdown")
    lines.append("")

    subtasks = result.get("subtasks", [])

    if subtasks:

        for i, task in enumerate(subtasks, 1):

            if not isinstance(task, dict):
                continue

            lines.append(
                f"### Subtask {i}: "
                f"{safe_text(task.get('title', f'Subtask {i}'))}"
            )

            lines.append(
                f"**Assigned Agent:** "
                f"{safe_text(task.get('assigned_agent', 'Agent'))}"
            )

            description = safe_text(
                task.get("description", "")
            )

            if description:
                lines.append(
                    f"**Objective:** {description}"
                )

            lines.append("")

    else:

        lines.append("No subtasks available.")
        lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 3. Agents Output")
    lines.append("")

    for item in result.get("research_results", []):

        if isinstance(item, dict):

            output = clean_content(
                item.get("content")
                or item.get("result")
            )

            if output:

                lines.append("### Research Agent")
                lines.append("")
                lines.append(output)
                lines.append("")

    for item in result.get("analysis_results", []):

        if isinstance(item, dict):

            output = clean_content(
                item.get("content")
                or item.get("result")
            )

            if output:

                lines.append("### Analysis Agent")
                lines.append("")
                lines.append(output)
                lines.append("")

    lines.append("---")
    lines.append("")

    lines.append("## 4. Automated Quality Audit")
    lines.append("")

    review = result.get("review_feedback", {})

    if review:

        lines.append(
            f"**Quality Score:** "
            f"{review.get('quality_score', 'N/A')}/10"
        )

        approved = review.get("approved", True)

        lines.append(
            f"**Status:** "
            f"{'Approved' if approved else 'Revision Required'}"
        )

        comments = review.get(
            "feedback_comments",
            []
        )

        for comment in comments:

            lines.append(
                f"- {safe_text(comment)}"
            )

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 5. Final Answer")
    lines.append("")

    final_output = clean_content(
        result.get("final_output", "")
    )

    lines.append(
        final_output
        if final_output
        else "No final answer generated."
    )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### END OF REPORT")

    return "\n".join(lines)




# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🤖 Multi-Agent AI")
    st.caption("Collaboration Dashboard")
    st.divider()

    st.subheader("⚙️ System Settings")

    provider = st.selectbox(
        "LLM Provider",
        ["ollama"],
        index=0
    )

    model_name = st.selectbox(
        "Model",
        ["llama3.2:3b"],
        index=0
    )

    st.success("🟢 Local Ollama")
    st.caption("Model: llama3.2:3b")

    st.divider()

    max_review_cycles = st.slider(
        "🔄 Max Review Cycles",
        min_value=1,
        max_value=4,
        value=int(settings.MAX_REVIEW_ITERATIONS),
        help=(
            "Maximum number of times the Reviewer Agent can send "
            "the answer back to the Writer Agent for improvement."
        )
    )

    st.caption(f"Current review cycle limit: {max_review_cycles}")

    st.divider()
    st.subheader("🔌 Backend")
    st.caption(BACKEND_URL)
    st.caption("FastAPI backend connection")


# ============================================================
# HEADER
# ============================================================

st.title("🤖 Multi-Agent AI Collaboration System")
st.caption(
    "Autonomous multi-agent workflow for task decomposition, "
    "specialized execution and automated quality review."
)


# ============================================================
# TABS
# ============================================================

tab_new, tab_history = st.tabs(
    ["🚀 New Collaboration Task", "📜 Task History"]
)


# ============================================================
# NEW COLLABORATION TASK
# ============================================================

with tab_new:
    st.subheader("Submit a Complex Task")

    example_prompts = [
        "Select an example prompt...",
        (
            "Analyze the impact of Artificial Intelligence on higher "
            "education and prepare a comprehensive report."
        ),
        (
            "Evaluate strategies for enterprises moving from traditional "
            "systems to cloud-native microservices."
        ),
        (
            "Explain the role of Artificial Intelligence in cybersecurity, "
            "including applications, benefits, limitations, ethical concerns "
            "and future scope."
        )
    ]

    selected_example = st.selectbox(
        "Quick Sample Prompts",
        example_prompts
    )

    default_prompt = (
        selected_example
        if selected_example != "Select an example prompt..."
        else ""
    )

    user_prompt = st.text_area(
        "Enter your task or question:",
        value=default_prompt,
        height=130,
        placeholder="Enter a complex task for the AI agents..."
    )

    start_btn = st.button(
        "✨ Run Collaboration",
        type="primary"
    )

    if start_btn:
        if not user_prompt.strip():
            st.warning("Please enter a task before running.")
        else:
            payload = {
                "user_request": user_prompt.strip(),
                "provider": provider,
                "model_name": model_name,
                "max_review_cycles": max_review_cycles
            }

            with st.spinner("Agents are collaborating on your task..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/tasks",
                        json=payload,
                        timeout=None
                    )

                    if response.status_code == 200:
                        st.session_state["active_result"] = response.json()
                        st.success("Task completed successfully!")
                    else:
                        st.error(
                            f"Backend API error: {response.text}"
                        )

                except requests.exceptions.ConnectionError:
                    st.error(
                        f"Could not connect to backend: {BACKEND_URL}"
                    )

                except requests.exceptions.Timeout:
                    st.error(
                        "The task took too long. Please check the backend terminal."
                    )

                except Exception as e:
                    st.error(f"Unexpected error: {e}")


    # ========================================================
    # RESULTS
    # ========================================================

    if "active_result" in st.session_state:
        result = st.session_state["active_result"]

        task_id = safe_text(result.get("task_id", "N/A"))
        status = safe_text(result.get("status", "completed"))

        st.divider()
        st.subheader("📊 Executive Overview")

        overview_left, overview_right, overview_status = st.columns(3)

        with overview_left:
            st.metric("Task ID", task_id)

        with overview_right:
            st.metric("Review Cycles", max_review_cycles)

        with overview_status:
            st.metric("Status", status.upper())

        st.divider()

        # ====================================================
        # WORKFLOW
        # ====================================================

        st.subheader("🔄 Agent Workflow")

        steps = [
            ("👔", "Manager Agent", "Decomposed"),
            ("🔎", "Research Agent", "Gathered Facts"),
            ("📊", "Analysis Agent", "Evaluated"),
            ("✍️", "Writer Agent", "Drafted"),
            ("🛡️", "Reviewer Agent", "Audit Complete")
        ]

        workflow_columns = st.columns(5)

        for column, step in zip(workflow_columns, steps):
            icon, name, step_status = step
            with column:
                st.info(f"{icon} **{name}**\n\n✓ {step_status}")


        # ====================================================
        # TASK DECOMPOSITION
        # ====================================================

        st.subheader("📋 Task Decomposition Breakdown")

        subtasks = result.get("subtasks", [])

        if subtasks:
            for index, subtask in enumerate(subtasks, 1):
                if not isinstance(subtask, dict):
                    continue

                agent = safe_text(
                    subtask.get(
                        "assigned_agent",
                        "Specialized Agent"
                    )
                )

                title = safe_text(
                    subtask.get(
                        "title",
                        f"Subtask {index}"
                    )
                )

                description = safe_text(
                    subtask.get(
                        "description",
                        ""
                    )
                )

                task_status = safe_text(
                    subtask.get(
                        "status",
                        "completed"
                    )
                )

                with st.container(border=True):
                    st.markdown(f"### {index}. {title}")
                    st.caption(f"Assigned Agent: {agent}")
                    if description:
                        st.write(description)
                    st.success(
                        f"Status: {task_status.title()}"
                    )
        else:
            st.info("No explicit subtasks available.")


        # ====================================================
        # AGENTS OUTPUT
        # ====================================================

        st.subheader("🤝 Agents Output")

        agent_outputs = []

        for item in result.get("research_results", []):
            if isinstance(item, dict):
                output = clean_content(
                    item.get("content")
                    or item.get("result")
                )

                if output:
                    agent_outputs.append({
                        "name": "Research Agent",
                        "icon": "🔎",
                        "description": "Information gathering and research",
                        "output": output
                    })

        for item in result.get("analysis_results", []):
            if isinstance(item, dict):
                output = clean_content(
                    item.get("content")
                    or item.get("result")
                )

                if output:
                    agent_outputs.append({
                        "name": "Analysis Agent",
                        "icon": "📊",
                        "description": "Evaluation and strategic insights",
                        "output": output
                    })

        writer_output = clean_content(
            result.get("final_output", "")
        )

        if writer_output:
            agent_outputs.append({
                "name": "Writer Agent",
                "icon": "✍️",
                "description": "Structured final response",
                "output": writer_output
            })

        if agent_outputs:
            for row_start in range(0, len(agent_outputs), 3):
                row_agents = agent_outputs[
                    row_start:row_start + 3
                ]

                columns = st.columns(len(row_agents))

                for column, agent_data in zip(
                    columns,
                    row_agents
                ):
                    with column:
                        with st.container(border=True):
                            st.markdown(
                                f"### {agent_data['icon']} "
                                f"{agent_data['name']}"
                            )
                            st.caption(
                                agent_data["description"]
                            )

                            preview = agent_data["output"][:500]

                            if len(agent_data["output"]) > 500:
                                preview += "..."

                            st.text(preview)

                            with st.expander(
                                "📄 View Full Output",
                                expanded=False
                            ):
                                st.markdown(
                                    agent_data["output"]
                                )
        else:
            st.info("No agent outputs available.")


        # ====================================================
        # QUALITY AUDIT
        # ====================================================

        st.subheader("🛡️ Automated Quality Audit")

        review = result.get(
            "review_feedback",
            {}
        )

        if review:
            score = review.get(
                "quality_score",
                "N/A"
            )

            approved = review.get(
                "approved",
                True
            )

            comments = review.get(
                "feedback_comments",
                []
            )

            improvements = safe_text(
                review.get(
                    "suggested_improvements",
                    ""
                )
            )

            audit_left, audit_right = st.columns(2)

            with audit_left:
                st.metric(
                    "Quality Score",
                    f"{score} / 10"
                )

            with audit_right:
                if approved:
                    st.success("✓ APPROVED")
                else:
                    st.warning("⚠ REVISION REQUIRED")

            if comments:
                st.markdown("**Reviewer Comments**")

                for comment in comments:
                    st.write(f"• {safe_text(comment)}")

            if improvements:
                st.markdown("**Suggested Improvements**")
                st.info(improvements)

        else:
            st.info(
                "No automated review feedback recorded."
            )


        # ====================================================
        # FINAL ANSWER
        # ====================================================

        st.subheader("🎯 Final Answer")

        final_output = clean_content(
            result.get(
                "final_output",
                ""
            )
        )

        if final_output:
            with st.container(border=True):
                st.markdown(final_output)

            st.caption("───────── END OF REPORT ─────────")

            report = generate_report(result)

            st.download_button(
                label="📥 Download Report (.md)",
                data=report,
                file_name=f"report_{task_id}.md",
                mime="text/markdown"
            )
        else:
            st.info("No final answer generated.")


# ============================================================
# TASK HISTORY
# ============================================================

with tab_history:
    st.subheader("📜 Past Execution History")

    if st.button("🔄 Refresh History"):
        st.rerun()

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/tasks",
            timeout=10
        )

        if response.status_code == 200:
            tasks = response.json().get(
                "tasks",
                []
            )

            if not tasks:
                st.info(
                    "No past execution records found."
                )
            else:
                for task in tasks:
                    if not isinstance(task, dict):
                        continue

                    task_id = safe_text(
                        task.get(
                            "task_id",
                            "N/A"
                        )
                    )

                    request = safe_text(
                        task.get(
                            "user_request",
                            ""
                        )
                    )

                    status = safe_text(
                        task.get(
                            "status",
                            ""
                        )
                    )

                    created_at = safe_text(
                        task.get(
                            "created_at",
                            ""
                        )
                    )

                    with st.expander(
                        f"📌 {task_id} — {request[:60]}..."
                    ):
                        st.write(
                            f"**Task Prompt:** {request}"
                        )
                        st.write(
                            f"**Status:** {status}"
                        )
                        st.write(
                            f"**Created At:** {created_at}"
                        )

                        if st.button(
                            "📂 Load Details",
                            key=f"load_{task_id}"
                        ):
                            detail_response = requests.get(
                                f"{BACKEND_URL}/api/tasks/{task_id}",
                                timeout=20
                            )

                            if detail_response.status_code == 200:
                                st.session_state[
                                    "active_result"
                                ] = detail_response.json()

                                st.success(
                                    "Task details loaded. Open the "
                                    "New Collaboration Task tab."
                                )
                            else:
                                st.error(
                                    "Could not load task details."
                                )
        else:
            st.error(
                f"History API error: {response.text}"
            )

    except requests.exceptions.ConnectionError:
        st.warning(
            f"Could not connect to backend at {BACKEND_URL}"
        )

    except Exception as e:
        st.warning(
            f"Could not load task history: {e}"
        )
