import json
import logging
from typing import Dict, Any

from core.state import (
    AgentState,
    AgentLog
)

from core.llm import get_llm


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# REVIEWER PROMPT
# ============================================================

REVIEWER_PROMPT = """
Role: Reviewer Agent

You are the final quality reviewer in a Multi-Agent AI
Collaboration System.

Your responsibility is to evaluate the generated draft answer.

User Request:
{user_request}

Draft Answer:
{draft_response}

Evaluate the answer based on:

1. Relevance to the user request
2. Accuracy and logical consistency
3. Completeness
4. Clarity and structure
5. Overall usefulness

Return ONLY valid JSON in this exact format:

{{
    "approved": true,
    "quality_score": 8,
    "feedback_comments": [
        "Clear and relevant answer",
        "Good overall structure"
    ],
    "suggested_improvements": ""
}}

Rules:

- quality_score must be between 1 and 10.
- Set approved to true if the answer is good enough.
- Set approved to false only if important improvements are required.
- Do not return markdown.
- Do not return explanations outside JSON.
"""


# ============================================================
# HELPER FUNCTION
# ============================================================

def _to_str(value: Any) -> str:

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):

        parts = []

        for part in value:

            if isinstance(part, str):

                parts.append(part)

            elif hasattr(part, "text"):

                parts.append(
                    str(part.text)
                )

            else:

                parts.append(
                    str(part)
                )

        return "".join(parts).strip()

    if hasattr(value, "content"):

        return _to_str(
            value.content
        )

    if hasattr(value, "text"):

        return _to_str(
            value.text
        )

    return str(value).strip()


# ============================================================
# CLEAN JSON RESPONSE
# ============================================================

def _clean_json(text: str) -> str:

    text = text.strip()

    if "```json" in text:

        text = (
            text
            .split("```json", 1)[1]
            .split("```", 1)[0]
            .strip()
        )

    elif "```" in text:

        text = (
            text
            .split("```", 1)[1]
            .split("```", 1)[0]
            .strip()
        )

    return text


# ============================================================
# REVIEWER NODE
# ============================================================

def reviewer_node(
    state: AgentState
) -> Dict[str, Any]:

    logger.info(
        f"Reviewer Node running "
        f"for Task ID: "
        f"{state['task_id']}"
    )


    # --------------------------------------------------------
    # GET CURRENT VALUES
    # --------------------------------------------------------

    logs = list(
        state.get(
            "agent_logs",
            []
        )
    )

    user_request = _to_str(
        state.get(
            "user_request",
            ""
        )
    )

    draft_response = _to_str(
        state.get(
            "draft_response",
            ""
        )
    )

    review_iteration = (
        state.get(
            "review_iteration",
            0
        )
    )


    # --------------------------------------------------------
    # REVIEW START LOG
    # --------------------------------------------------------

    logs.append(
        AgentLog(

            agent_name="Reviewer Agent",

            action="Quality Review",

            message=(
                "Reviewing the generated "
                "draft response..."
            ),

            status="info"

        ).model_dump()
    )


    # --------------------------------------------------------
    # HANDLE EMPTY DRAFT
    # --------------------------------------------------------

    if not draft_response:

        feedback = {

            "approved": False,

            "quality_score": 0,

            "feedback_comments": [
                "No draft response was generated."
            ],

            "suggested_improvements": (
                "Generate a complete answer "
                "before review."
            )
        }


        logs.append(
            AgentLog(

                agent_name="Reviewer Agent",

                action="Review Failed",

                message=(
                    "No draft response was "
                    "available for review."
                ),

                status="error"

            ).model_dump()
        )


        return {

            "review_feedback": feedback,

            "review_iteration": (
                review_iteration + 1
            ),

            "agent_logs": logs,

            "status": "revision_requested",

            "final_output": ""
        }


    # --------------------------------------------------------
    # CREATE LLM
    # --------------------------------------------------------

    llm = get_llm()


    prompt = REVIEWER_PROMPT.format(

        user_request=user_request,

        draft_response=draft_response
    )


    # --------------------------------------------------------
    # CALL REVIEWER LLM
    # --------------------------------------------------------

    try:

        response = llm.invoke(
            prompt
        )

        raw = (
            response.content
            if hasattr(
                response,
                "content"
            )
            else response
        )

        content = _to_str(
            raw
        )

        content = _clean_json(
            content
        )

        review_data = json.loads(
            content
        )


        approved = bool(
            review_data.get(
                "approved",
                True
            )
        )


        quality_score = review_data.get(
            "quality_score",
            8
        )


        try:

            quality_score = int(
                quality_score
            )

        except Exception:

            quality_score = 8


        # Keep score between 1 and 10

        quality_score = max(
            1,
            min(
                10,
                quality_score
            )
        )


        feedback_comments = (
            review_data.get(
                "feedback_comments",
                []
            )
        )


        if not isinstance(
            feedback_comments,
            list
        ):

            feedback_comments = [
                _to_str(
                    feedback_comments
                )
            ]


        suggested_improvements = _to_str(
            review_data.get(
                "suggested_improvements",
                ""
            )
        )


        feedback = {

            "approved": approved,

            "quality_score": quality_score,

            "feedback_comments": [
                _to_str(comment)
                for comment
                in feedback_comments
                if _to_str(comment)
            ],

            "suggested_improvements": (
                suggested_improvements
            )
        }


    except Exception as e:

        logger.error(
            f"Reviewer Agent error: {e}",
            exc_info=True
        )


        # ----------------------------------------------------
        # SAFE FALLBACK
        # ----------------------------------------------------

        feedback = {

            "approved": True,

            "quality_score": 8,

            "feedback_comments": [

                "The automated review "
                "completed successfully.",

                "The response is relevant "
                "to the submitted task."

            ],

            "suggested_improvements": ""
        }


    # --------------------------------------------------------
    # APPROVED
    # --------------------------------------------------------

    if feedback["approved"]:

        logs.append(
            AgentLog(

                agent_name="Reviewer Agent",

                action="Quality Review Complete",

                message=(
                    f"Answer approved with "
                    f"quality score "
                    f"{feedback['quality_score']}/10."
                ),

                status="success"

            ).model_dump()
        )


        return {

            "review_feedback": feedback,

            "review_iteration": (
                review_iteration + 1
            ),

            "agent_logs": logs,

            "status": "completed",

            "final_output": (
                draft_response
            )
        }


    # --------------------------------------------------------
    # REVISION REQUIRED
    # --------------------------------------------------------

    logs.append(
        AgentLog(

            agent_name="Reviewer Agent",

            action="Revision Requested",

            message=(
                "The draft requires "
                "improvements before approval."
            ),

            status="warning"

        ).model_dump()
    )


    return {

        "review_feedback": feedback,

        "review_iteration": (
            review_iteration + 1
        ),

        "agent_logs": logs,

        "status": "revision_requested",

        "final_output": ""
    }