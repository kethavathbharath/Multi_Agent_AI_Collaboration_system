import logging
from typing import Any, Dict

from core.state import AgentState, AgentLog
from core.llm import get_llm

logger = logging.getLogger(__name__)


def _to_str(value: Any) -> str:
    """
    Convert Gemini/LLM response into clean plain text.

    Handles:
    - normal strings
    - dictionaries
    - lists of content parts
    - objects having .text
    - objects having .content
    - escaped newlines
    """

    if value is None:
        return ""

    # Normal string
    if isinstance(value, str):
        text = value

        # Convert escaped newlines into real newlines
        text = text.replace("\\r\\n", "\n")
        text = text.replace("\\n", "\n")

        # Remove accidental Python-style wrapper if present
        if text.startswith("{'type': 'text', 'text':"):
            try:
                prefix = "{'type': 'text', 'text': '"

                if text.startswith(prefix) and text.endswith("'}"):
                    text = text[len(prefix):-2]

            except Exception:
                pass

        return text.strip()

    # Dictionary response
    if isinstance(value, dict):

        if "text" in value:
            return _to_str(value["text"])

        for key in [
            "content",
            "output",
            "result",
            "final_output",
            "draft_response"
        ]:
            if key in value:
                result = _to_str(value[key])

                if result:
                    return result

        return ""

    # List of content parts
    if isinstance(value, list):

        parts = []

        for item in value:
            text = _to_str(item)

            if text:
                parts.append(text)

        return "\n".join(parts).strip()

    # Object with .text
    if hasattr(value, "text"):

        try:
            return _to_str(value.text)

        except Exception:
            pass

    # Object with .content
    if hasattr(value, "content"):

        try:
            return _to_str(value.content)

        except Exception:
            pass

    return str(value).strip()


# ============================================================
# WRITER PROMPT
# ============================================================

WRITER_PROMPT = """You are the Writer Agent in a Multi-Agent AI Collaboration System.

Your task is to create a high-quality FINAL ANSWER for the user's request.

USER REQUEST:
{user_request}

RESEARCH FINDINGS:
{research_output}

ANALYSIS FINDINGS:
{analysis_output}

REVIEWER FEEDBACK:
{reviewer_feedback}

IMPORTANT RULES:

1. Answer the user's request directly and completely.

2. Use the research findings and analysis findings as the main source of information.

3. Do NOT mention:
   - agents
   - prompts
   - internal processing
   - reviewer feedback
   - workflow
   - system implementation

4. Do NOT repeat the user's request as an introduction.

5. Do NOT produce generic filler.

6. Make every section useful and specific.

7. Avoid repeating the same information.

8. Use proper Markdown formatting.

9. Use clear headings and bullet points where appropriate.

10. Explain important concepts instead of only listing them.

11. Include relevant real-world examples when supported by the research.

12. If reviewer feedback is provided, improve the answer according to that feedback.

13. The final response must be readable by a normal user.

14. DO NOT return Python dictionaries.

15. DO NOT return JSON.

16. DO NOT return content-part objects.

17. Return ONLY the actual human-readable report.

Use EXACTLY these 5 sections:

## 1. Overview

Explain the main concept clearly, including what it is and how it works.

## 2. Benefits

Explain the important benefits with clear points and brief explanations.

## 3. Real-World Applications

Give relevant real-world applications/examples and explain each briefly.

## 4. Challenges

Explain important limitations, risks, ethical concerns, technical challenges, and practical issues.

## 5. Future Scope

Explain future possibilities, improvements, and potential developments.

Do not add an Executive Summary.

Do not add any section before section 1.

Do not add any section after section 5.

Return ONLY the final report.
"""


# ============================================================
# WRITER NODE
# ============================================================

def writer_node(state: AgentState) -> Dict[str, Any]:

    logger.info(
        f"Writer Node running for Task ID: {state['task_id']}"
    )

    # Copy existing logs
    logs = list(state.get("agent_logs", []))

    # Writer start log
    logs.append(
        AgentLog(
            agent_name="Writer Agent",
            action="Drafting Response",
            message="Creating final report from research and analysis.",
            status="info"
        ).model_dump()
    )

    # Get data from state
    research_results = state.get("research_results", [])
    analysis_results = state.get("analysis_results", [])
    review_feedback = state.get("review_feedback", {})

    # ========================================================
    # Convert research results into text
    # ========================================================

    research_parts = []

    for research in research_results:

        if isinstance(research, dict):
            content = research.get("content", "")
        else:
            content = research

        cleaned = _to_str(content)

        if cleaned:
            research_parts.append(cleaned)

    research_output = "\n\n".join(research_parts)

    if not research_output:
        research_output = "No research findings available."

    # ========================================================
    # Convert analysis results into text
    # ========================================================

    analysis_parts = []

    for analysis in analysis_results:

        if isinstance(analysis, dict):
            content = analysis.get("content", "")
        else:
            content = analysis

        cleaned = _to_str(content)

        if cleaned:
            analysis_parts.append(cleaned)

    analysis_output = "\n\n".join(analysis_parts)

    if not analysis_output:
        analysis_output = "No analysis findings available."

    # ========================================================
    # Reviewer feedback
    # ========================================================

    if review_feedback:

        approved = review_feedback.get("approved", True)

        if not approved:

            comments = review_feedback.get(
                "feedback_comments",
                []
            )

            if isinstance(comments, list):

                comments_text = ", ".join(
                    _to_str(comment)
                    for comment in comments
                )

            else:

                comments_text = _to_str(comments)

            improvements = _to_str(
                review_feedback.get(
                    "suggested_improvements",
                    ""
                )
            )

            feedback_str = (
                f"Reviewer Score: "
                f"{review_feedback.get('quality_score', 'N/A')}/10\n"
                f"Comments: {comments_text}\n"
                f"Suggested Improvements: {improvements}"
            )

        else:

            feedback_str = (
                "The previous response was approved. "
                "Create a polished final report."
            )

    else:

        feedback_str = (
            "No reviewer feedback is available. "
            "Create a high-quality final report."
        )

    # ========================================================
    # Create final writer prompt
    # ========================================================

    prompt = WRITER_PROMPT.format(
        user_request=_to_str(
            state.get("user_request", "")
        ),
        research_output=research_output,
        analysis_output=analysis_output,
        reviewer_feedback=feedback_str
    )

    # ========================================================
    # Call LLM
    # ========================================================

    try:

        llm = get_llm()

        response = llm.invoke(prompt)

        # Get response content safely
        if hasattr(response, "content"):
            raw = response.content
        else:
            raw = response

        # Convert response to clean text
        draft = _to_str(raw)

        # ====================================================
        # Extra cleanup
        # ====================================================

        # Remove Markdown code fence
        if draft.startswith("```markdown"):
            draft = draft[len("```markdown"):].strip()

        elif draft.startswith("```"):
            draft = draft[3:].strip()

        if draft.endswith("```"):
            draft = draft[:-3].strip()

        # Remove accidental content-part representation
        if draft.startswith("{") and "'text':" in draft:

            try:

                text_start = draft.find("'text':")

                if text_start != -1:

                    extracted = draft[text_start + 7:].strip()

                    if extracted.startswith("'"):
                        extracted = extracted[1:]

                    if extracted.endswith("}"):
                        extracted = extracted[:-1]

                    if extracted.endswith("'"):
                        extracted = extracted[:-1]

                    draft = extracted

            except Exception:
                pass

        draft = draft.strip()

        # ====================================================
        # Safety fallback
        # ====================================================

        if not draft:

            draft = (
                "## 1. Overview\n\n"
                "A final report could not be generated.\n\n"

                "## 2. Benefits\n\n"
                "The available research can be reviewed for "
                "the main benefits.\n\n"

                "## 3. Real-World Applications\n\n"
                f"{research_output}\n\n"

                "## 4. Challenges\n\n"
                f"{analysis_output}\n\n"

                "## 5. Future Scope\n\n"
                "Further development can improve the system."
            )

    except Exception as e:

        logger.error(
            f"Error in Writer Agent execution: {e}",
            exc_info=True
        )

        # Fallback output
        draft = (
            "## 1. Overview\n\n"
            "The final report could not be generated "
            "using the language model.\n\n"

            "## 2. Benefits\n\n"
            "Please refer to the available research findings.\n\n"

            "## 3. Real-World Applications\n\n"
            f"{research_output}\n\n"

            "## 4. Challenges\n\n"
            f"{analysis_output}\n\n"

            "## 5. Future Scope\n\n"
            "Further development can improve the system."
        )

    # ========================================================
    # Writer completion log
    # ========================================================

    logs.append(
        AgentLog(
            agent_name="Writer Agent",
            action="Draft Complete",
            message=(
                "Final report generated and sent "
                "to Reviewer Agent."
            ),
            status="success"
        ).model_dump()
    )

    # ========================================================
    # Return updated state
    # ========================================================

    return {
        "draft_response": draft,
        "agent_logs": logs,
        "status": "reviewing"
    }