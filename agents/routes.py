from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app as langgraph_app
from database.db import (
    save_meeting,
    get_all_meetings,
    get_meeting_by_id,
    get_all_tasks,
    update_task_status
)

router = APIRouter()


# ─────────────────────────────────────────────
# REQUEST & RESPONSE MODELS
# ─────────────────────────────────────────────

class TranscriptRequest(BaseModel):
    transcript: str

    class Config:
        json_schema_extra = {
            "example": {
                "transcript": (
                    "The team discussed the Gemini AI project. "
                    "John will build the API backend. "
                    "Sarah will clean the dataset. "
                    "Deadline is Friday."
                )
            }
        }


class TaskItem(BaseModel):
    task: str
    owner: str
    deadline: Optional[str] = None


class MeetingResponse(BaseModel):
    meeting_id: int          # ← now returned so client can look it up later
    summary: str
    tasks: List[TaskItem]
    report: str


class SummaryOnlyResponse(BaseModel):
    summary: str


class TasksOnlyResponse(BaseModel):
    tasks: List[TaskItem]


class HealthResponse(BaseModel):
    status: str
    message: str


class StatusUpdateRequest(BaseModel):
    status: str

    class Config:
        json_schema_extra = {
            "example": {"status": "Done"}
        }


# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def normalize_tasks(raw_tasks: Any) -> List[Dict]:
    if isinstance(raw_tasks, list):
        return raw_tasks
    return [{"task": str(raw_tasks), "owner": "Unknown", "deadline": None}]


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Gemini Multi-Agent API is running."}


# ── MAIN PIPELINE ──────────────────────────────

@router.post(
    "/process-meeting",
    response_model=MeetingResponse,
    tags=["Pipeline"],
    summary="Run full 3-agent pipeline and save to database"
)
def process_meeting(request: TranscriptRequest):
    """
    Runs transcript through all 3 agents, saves result to SQLite,
    and returns the full output including the new meeting_id.
    """
    if not request.transcript.strip():
        raise HTTPException(status_code=422, detail="Transcript cannot be empty.")

    # Run LangGraph pipeline
    try:
        result = langgraph_app.invoke({
            "transcript": request.transcript,
            "summary": "",
            "tasks": [],
            "report": ""
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    tasks = normalize_tasks(result.get("tasks", []))
    summary = result.get("summary", "")
    report = result.get("report", "")

    # Save to database
    try:
        meeting_id = save_meeting(
            transcript=request.transcript,
            summary=summary,
            tasks=tasks,
            report=report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return MeetingResponse(
        meeting_id=meeting_id,
        summary=summary,
        tasks=[TaskItem(**t) for t in tasks],
        report=report
    )


# ── MEETING HISTORY ────────────────────────────

@router.get(
    "/meetings",
    tags=["Meetings"],
    summary="Get all past meetings"
)
def list_meetings():
    """
    Returns all processed meetings, most recent first.
    """
    try:
        return get_all_meetings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/meetings/{meeting_id}",
    tags=["Meetings"],
    summary="Get a single meeting with all its tasks"
)
def get_meeting(meeting_id: int):
    """
    Returns a full meeting record including all extracted tasks.
    """
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found.")
    return meeting


# ── TASK MANAGEMENT ────────────────────────────

@router.get(
    "/tasks",
    tags=["Tasks"],
    summary="Get all tasks across all meetings"
)
def list_all_tasks():
    """
    Returns every task from every meeting — useful for a global task board.
    """
    try:
        return get_all_tasks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/tasks/{task_id}/status",
    tags=["Tasks"],
    summary="Update a task status"
)
def update_status(task_id: int, body: StatusUpdateRequest):
    """
    Updates a task's status.
    Allowed values: Pending | In Progress | Done | Cancelled
    """
    try:
        updated = update_task_status(task_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    return {"task_id": task_id, "status": body.status, "updated": True}


# ── AGENT ISOLATION ────────────────────────────

@router.post(
    "/summarize",
    response_model=SummaryOnlyResponse,
    tags=["Agents"],
    summary="Run Agent 1 only — Summarizer"
)
def summarize_only(request: TranscriptRequest):
    if not request.transcript.strip():
        raise HTTPException(status_code=422, detail="Transcript cannot be empty.")
    try:
        from agents.summarizer import summarize_meeting
        return SummaryOnlyResponse(summary=summarize_meeting(request.transcript))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarizer error: {str(e)}")


@router.post(
    "/extract",
    response_model=TasksOnlyResponse,
    tags=["Agents"],
    summary="Run Agent 2 only — Extractor"
)
def extract_only(request: TranscriptRequest):
    if not request.transcript.strip():
        raise HTTPException(status_code=422, detail="Transcript cannot be empty.")
    try:
        from agents.extractor import extract_action_items
        tasks = normalize_tasks(extract_action_items(request.transcript))
        return TasksOnlyResponse(tasks=[TaskItem(**t) for t in tasks])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extractor error: {str(e)}")


