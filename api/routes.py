from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meeting_id: int
    summary: str
    tasks: List[TaskItem]
    report: str


class TranscriptionResponse(BaseModel):
    transcript: str
    language: str
    duration: float


class TranscribeAndProcessResponse(BaseModel):
    meeting_id: int
    transcript: str
    language: str
    duration: float
    summary: str
    tasks: List[TaskItem]
    report: str
    report_text: str    # the full formatted .txt content


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
# HEALTH
# ─────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Gemini Multi-Agent API is running."}


# ─────────────────────────────────────────────
# TRANSCRIPTION — Agent 0
# ─────────────────────────────────────────────

@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    tags=["Transcription"],
    summary="Transcribe audio to text — English or Amharic"
)
async def transcribe_audio_endpoint(
    file: UploadFile = File(...),
    language: str = Form(default="en")
):
    """
    Accepts an audio file and returns the transcript.

    Language options:
    - "en"   -> English
    - "am"   -> Amharic
    - "auto" -> Auto-detect

    Supported formats: webm, mp3, wav, m4a, ogg
    """
    if not file:
        raise HTTPException(status_code=422, detail="No audio file provided.")

    audio_bytes = await file.read()

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=422, detail="Audio file is empty.")

    try:
        from agents.transcriber import transcribe_audio
        result = transcribe_audio(audio_bytes, language)
        return TranscriptionResponse(
            transcript=result["transcript"],
            language=result.get("language", language),
            duration=result.get("duration", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")


@router.post(
    "/transcribe-and-process",
    response_model=TranscribeAndProcessResponse,
    tags=["Transcription"],
    summary="Transcribe audio AND run full 3-agent pipeline — returns formatted report"
)
async def transcribe_and_process(
    file: UploadFile = File(...),
    language: str = Form(default="en")
):
    """
    The all-in-one endpoint:
    1. Transcribes audio using Groq Whisper (English or Amharic)
    2. Runs transcript through all 3 agents
    3. Generates a professional formatted .txt report
    4. Saves to database
    5. Returns everything including the full formatted report text
    """
    if not file:
        raise HTTPException(status_code=422, detail="No audio file provided.")

    audio_bytes = await file.read()

    if len(audio_bytes) == 0:
        raise HTTPException(status_code=422, detail="Audio file is empty.")

    # Step 1: Transcribe
    try:
        from agents.transcriber import transcribe_audio
        transcription = transcribe_audio(audio_bytes, language)
        transcript_text = transcription["transcript"]
        duration = transcription.get("duration", 0.0)
        detected_lang = transcription.get("language", language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

    if not transcript_text.strip():
        raise HTTPException(status_code=422, detail="Transcription returned empty text.")

    # Step 2: Run pipeline
    try:
        from main import pipeline as langgraph_app
        result = langgraph_app.invoke({
            "transcript": transcript_text,
            "summary": "",
            "tasks": [],
            "report": ""
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    tasks = normalize_tasks(result.get("tasks", []))
    summary = result.get("summary", "")
    report = result.get("report", "")

    # Step 3: Save to database
    try:
        meeting_id = save_meeting(
            transcript=transcript_text,
            summary=summary,
            tasks=tasks,
            report=report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Step 4: Generate formatted .txt report
    try:
        from agents.report_generator import generate_meeting_report, save_report_to_file
        report_text = generate_meeting_report(
            transcript=transcript_text,
            summary=summary,
            tasks=tasks,
            report=report,
            language=detected_lang,
            duration=duration,
            meeting_id=meeting_id
        )
        # Save to file automatically
        save_report_to_file(report_text, meeting_id=meeting_id)
    except Exception as e:
        report_text = report  # fallback to plain report

    return TranscribeAndProcessResponse(
        meeting_id=meeting_id,
        transcript=transcript_text,
        language=detected_lang,
        duration=duration,
        summary=summary,
        tasks=[TaskItem(**t) for t in tasks],
        report=report,
        report_text=report_text
    )


# ─────────────────────────────────────────────
# DOWNLOAD REPORT AS .TXT FILE
# ─────────────────────────────────────────────

@router.get(
    "/meetings/{meeting_id}/download",
    tags=["Meetings"],
    summary="Download meeting report as a formatted .txt file"
)
def download_meeting_report(meeting_id: int):
    """
    Generates and downloads the full meeting report as a .txt file.
    Includes transcript, summary, action items, and follow-up report.
    """
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found.")

    try:
        from agents.report_generator import generate_meeting_report, save_report_to_file

        report_text = generate_meeting_report(
            transcript=meeting.get("transcript", ""),
            summary=meeting.get("summary", ""),
            tasks=meeting.get("tasks", []),
            report=meeting.get("report", ""),
            language="en",
            duration=0.0,
            meeting_id=meeting_id
        )

        # Save to file
        filepath = save_report_to_file(report_text, meeting_id=meeting_id)

        return FileResponse(
            path=filepath,
            filename=f"meeting_{meeting_id}_report.txt",
            media_type="text/plain"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/meetings/{meeting_id}/report-text",
    tags=["Meetings"],
    summary="Get meeting report as plain text — no download"
)
def get_meeting_report_text(meeting_id: int):
    """
    Returns the formatted report as plain text in the response body.
    Useful for displaying in the frontend without downloading.
    """
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found.")

    try:
        from agents.report_generator import generate_meeting_report

        report_text = generate_meeting_report(
            transcript=meeting.get("transcript", ""),
            summary=meeting.get("summary", ""),
            tasks=meeting.get("tasks", []),
            report=meeting.get("report", ""),
            language="en",
            duration=0.0,
            meeting_id=meeting_id
        )

        return PlainTextResponse(content=report_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

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

    try:
        from main import pipeline as langgraph_app
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

    try:
        meeting_id = save_meeting(
            transcript=request.transcript,
            summary=summary,
            tasks=tasks,
            report=report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Auto-generate and save formatted report
    try:
        from agents.report_generator import generate_meeting_report, save_report_to_file
        report_text = generate_meeting_report(
            transcript=request.transcript,
            summary=summary,
            tasks=tasks,
            report=report,
            meeting_id=meeting_id
        )
        save_report_to_file(report_text, meeting_id=meeting_id)
    except Exception:
        pass  # don't fail the main response if report saving fails

    return MeetingResponse(
        meeting_id=meeting_id,
        summary=summary,
        tasks=[TaskItem(**t) for t in tasks],
        report=report
    )


# ─────────────────────────────────────────────
# MEETING HISTORY
# ─────────────────────────────────────────────

@router.get(
    "/meetings",
    tags=["Meetings"],
    summary="Get all past meetings"
)
def list_meetings():
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
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found.")
    return meeting


# ─────────────────────────────────────────────
# TASK MANAGEMENT
# ─────────────────────────────────────────────

@router.get(
    "/tasks",
    tags=["Tasks"],
    summary="Get all tasks across all meetings"
)
def list_all_tasks():
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


# ─────────────────────────────────────────────
# AGENT ISOLATION
# ─────────────────────────────────────────────

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




