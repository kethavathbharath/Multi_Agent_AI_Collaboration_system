import uuid
import json
import asyncio
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config.settings import settings
from backend.db import init_db, save_task, get_task, get_all_tasks
from backend.schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskListResponse
)
from core.workflow import (
    agent_graph,
    run_multi_agent_workflow
)
from core.state import AgentState


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Initializing database...")

    init_db()

    logger.info("Application startup complete.")

    yield

    logger.info("Application shutdown complete.")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.APP_TITLE,
    description=(
        "Backend API for Multi-Agent AI Collaboration System."
    ),
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_db()


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "app": settings.APP_TITLE,
        "docs_url": "/docs"
    }


# ============================================================
# CREATE AND RUN TASK
# ============================================================

@app.post(
    "/api/tasks",
    response_model=TaskResponse
)
def create_and_run_task(
    payload: TaskCreateRequest
):

    task_id = (
        f"task-{uuid.uuid4().hex[:8]}"
    )

    logger.info(
        f"Received new task request "
        f"[ID: {task_id}]: "
        f"{payload.user_request[:50]}..."
    )

    logger.info(
        f"Maximum review cycles selected: "
        f"{payload.max_review_cycles}"
    )

    try:

        # ----------------------------------------------------
        # RUN MULTI-AGENT WORKFLOW
        # ----------------------------------------------------

        final_state = run_multi_agent_workflow(
            task_id=task_id,
            user_request=payload.user_request,
            max_review_cycles=payload.max_review_cycles
        )


        # ----------------------------------------------------
        # SAVE TASK TO DATABASE
        # ----------------------------------------------------

        save_task(
            task_id=task_id,
            user_request=payload.user_request,
            status=final_state.get(
                "status",
                "completed"
            ),
            state_dict=final_state,
            final_output=final_state.get(
                "final_output",
                ""
            )
        )


        # ----------------------------------------------------
        # RETURN RESPONSE
        # ----------------------------------------------------

        return TaskResponse(
            task_id=task_id,

            user_request=payload.user_request,

            status=final_state.get(
                "status",
                "completed"
            ),

            final_output=final_state.get(
                "final_output",
                ""
            ),

            subtasks=final_state.get(
                "subtasks",
                []
            ),

            research_results=final_state.get(
                "research_results",
                []
            ),

            analysis_results=final_state.get(
                "analysis_results",
                []
            ),

            agent_logs=final_state.get(
                "agent_logs",
                []
            ),

            review_feedback=final_state.get(
                "review_feedback",
                {}
            )
        )


    except Exception as e:

        logger.error(
            f"Error executing task "
            f"{task_id}: {e}",
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET TASK HISTORY
# ============================================================

@app.get(
    "/api/tasks",
    response_model=TaskListResponse
)
def list_tasks():

    tasks = get_all_tasks()

    return TaskListResponse(
        tasks=tasks
    )


# ============================================================
# GET SINGLE TASK DETAILS
# ============================================================

@app.get(
    "/api/tasks/{task_id}",
    response_model=TaskResponse
)
def get_task_details(
    task_id: str
):

    task_data = get_task(task_id)

    if not task_data:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )


    state = task_data.get(
        "state",
        {}
    )


    return TaskResponse(

        task_id=task_id,

        user_request=task_data.get(
            "user_request",
            ""
        ),

        status=task_data.get(
            "status",
            ""
        ),

        final_output=task_data.get(
            "final_output",
            ""
        ),

        subtasks=state.get(
            "subtasks",
            []
        ),

        research_results=state.get(
            "research_results",
            []
        ),

        analysis_results=state.get(
            "analysis_results",
            []
        ),

        agent_logs=state.get(
            "agent_logs",
            []
        ),

        review_feedback=state.get(
            "review_feedback",
            {}
        ),

        created_at=task_data.get(
            "created_at"
        ),

        updated_at=task_data.get(
            "updated_at"
        )
    )


# ============================================================
# STREAM TASK PROGRESS
# ============================================================

@app.get(
    "/api/tasks/{task_id}/stream"
)
async def stream_task_progress(
    task_id: str,
    user_request: str,
    max_review_cycles: int = 1
):

    async def event_generator() -> AsyncGenerator[
        str,
        None
    ]:

        initial_state: AgentState = {

            "task_id": task_id,

            "user_request": user_request,

            "status": "decomposing",

            "subtasks": [],

            "research_results": [],

            "analysis_results": [],

            "draft_response": "",

            "review_feedback": {},

            "review_iteration": 0,

            # Selected maximum review cycles
            "max_review_cycles": max_review_cycles,

            "agent_logs": [],

            "final_output": "",

            "error": None
        }


        for event in agent_graph.stream(
            initial_state
        ):

            for (
                node_name,
                state_update
            ) in event.items():

                data = {

                    "node": node_name,

                    "status": state_update.get(
                        "status",
                        "running"
                    ),

                    "subtasks": state_update.get(
                        "subtasks",
                        []
                    ),

                    "agent_logs": state_update.get(
                        "agent_logs",
                        []
                    ),

                    "draft_response": state_update.get(
                        "draft_response",
                        ""
                    ),

                    "final_output": state_update.get(
                        "final_output",
                        ""
                    )
                }


                yield (
                    f"data: "
                    f"{json.dumps(data)}\n\n"
                )


                await asyncio.sleep(0.3)


    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )