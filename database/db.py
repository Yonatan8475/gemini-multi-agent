import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
 
# ─────────────────────────────────────────────
# DATABASE PATH
# ─────────────────────────────────────────────
 
# Stored in the project root as meetings.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "meetings.db")
 
 
# ─────────────────────────────────────────────
# CONNECTION HELPER
# ─────────────────────────────────────────────
 
def get_connection() -> sqlite3.Connection:
    """
    Opens and returns a SQLite connection.
    row_factory lets us access columns by name (like a dict).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
 
 
# ─────────────────────────────────────────────
# TABLE CREATION
# ─────────────────────────────────────────────
 
def init_db():
    """
    Creates all tables if they don't exist yet.
    Safe to call every time the app starts.
 
    Tables:
        meetings  — stores each transcript + summary + report
        tasks     — stores extracted action items linked to a meeting
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    # --- meetings table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            transcript  TEXT    NOT NULL,
            summary     TEXT    NOT NULL,
            report      TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        )
    """)
 
    # --- tasks table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id  INTEGER NOT NULL,
            task        TEXT    NOT NULL,
            owner       TEXT    NOT NULL DEFAULT 'Unknown',
            deadline    TEXT,
            status      TEXT    NOT NULL DEFAULT 'Pending',
            created_at  TEXT    NOT NULL,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        )
    """)
 
    conn.commit()
    conn.close()
    print(f"✅ Database ready at: {DB_PATH}")
 
 
# ─────────────────────────────────────────────
# WRITE OPERATIONS
# ─────────────────────────────────────────────
 
def save_meeting(
    transcript: str,
    summary: str,
    tasks: List[Dict[str, Any]],
    report: str
) -> int:
    """
    Saves a full pipeline result to the database.
 
    Inserts one row into meetings, then one row per task into tasks.
    Returns the new meeting_id so the API can reference it.
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
 
    try:
        # Insert meeting
        cursor.execute("""
            INSERT INTO meetings (transcript, summary, report, created_at)
            VALUES (?, ?, ?, ?)
        """, (transcript, summary, report, now))
 
        meeting_id = cursor.lastrowid
 
        # Insert each task linked to this meeting
        for t in tasks:
            cursor.execute("""
                INSERT INTO tasks (meeting_id, task, owner, deadline, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                meeting_id,
                t.get("task", "Unknown task"),
                t.get("owner", "Unknown"),
                t.get("deadline", None),
                "Pending",
                now
            ))
 
        conn.commit()
        return meeting_id
 
    except Exception as e:
        conn.rollback()
        raise e
 
    finally:
        conn.close()
 
 
# ─────────────────────────────────────────────
# READ OPERATIONS
# ─────────────────────────────────────────────
 
def get_all_meetings() -> List[Dict]:
    """
    Returns all meetings ordered by most recent first.
    Does NOT include tasks (use get_meeting_by_id for that).
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT id, summary, report, created_at
        FROM meetings
        ORDER BY id DESC
    """)
 
    rows = cursor.fetchall()
    conn.close()
 
    return [dict(row) for row in rows]
 
 
def get_meeting_by_id(meeting_id: int) -> Optional[Dict]:
    """
    Returns a single meeting with all its tasks.
    Returns None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    # Get the meeting
    cursor.execute("""
        SELECT id, transcript, summary, report, created_at
        FROM meetings
        WHERE id = ?
    """, (meeting_id,))
 
    meeting_row = cursor.fetchone()
 
    if not meeting_row:
        conn.close()
        return None
 
    meeting = dict(meeting_row)
 
    # Get its tasks
    cursor.execute("""
        SELECT id, task, owner, deadline, status, created_at
        FROM tasks
        WHERE meeting_id = ?
        ORDER BY id ASC
    """, (meeting_id,))
 
    tasks = [dict(row) for row in cursor.fetchall()]
    meeting["tasks"] = tasks
 
    conn.close()
    return meeting
 
 
def get_tasks_by_meeting(meeting_id: int) -> List[Dict]:
    """
    Returns only the tasks for a given meeting.
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT id, task, owner, deadline, status, created_at
        FROM tasks
        WHERE meeting_id = ?
        ORDER BY id ASC
    """, (meeting_id,))
 
    rows = cursor.fetchall()
    conn.close()
 
    return [dict(row) for row in rows]
 
 
def get_all_tasks() -> List[Dict]:
    """
    Returns every task across all meetings.
    Useful for a global task dashboard.
    """
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT t.id, t.meeting_id, t.task, t.owner,
               t.deadline, t.status, t.created_at
        FROM tasks t
        ORDER BY t.id DESC
    """)
 
    rows = cursor.fetchall()
    conn.close()
 
    return [dict(row) for row in rows]
 
 
# ─────────────────────────────────────────────
# UPDATE OPERATIONS
# ─────────────────────────────────────────────
 
def update_task_status(task_id: int, status: str) -> bool:
    """
    Updates the status of a task (e.g. Pending → Done).
    Returns True if a row was updated, False if task not found.
    """
    allowed = {"Pending", "In Progress", "Done", "Cancelled"}
    if status not in allowed:
        raise ValueError(f"Status must be one of: {allowed}")
 
    conn = get_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        UPDATE tasks SET status = ? WHERE id = ?
    """, (status, task_id))
 
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
 
    return updated
 
 
# ─────────────────────────────────────────────
# TEST — run this file directly to verify setup
# ─────────────────────────────────────────────
 
if __name__ == "__main__":
    print("Initializing database...")
    init_db()
 
    # Insert a test meeting
    test_id = save_meeting(
        transcript="John will build the API. Sarah will clean the dataset. Deadline Friday.",
        summary="Team discussed AI project. Tasks assigned to John and Sarah.",
        tasks=[
            {"task": "Build API backend", "owner": "John", "deadline": "Friday"},
            {"task": "Clean dataset",     "owner": "Sarah", "deadline": "Friday"},
        ],
        report="FOLLOW-UP REPORT\n1. Build API → John → Due: Friday → Pending\n2. Clean dataset → Sarah → Due: Friday → Pending"
    )
 
    print(f"\n✅ Test meeting saved with ID: {test_id}")
 
    # Read it back
    meeting = get_meeting_by_id(test_id)
    print(f"\n📋 Meeting #{test_id}:")
    print(f"   Summary : {meeting['summary']}")
    print(f"   Tasks   : {len(meeting['tasks'])} tasks")
    for t in meeting["tasks"]:
        print(f"   → {t['task']} | {t['owner']} | {t['deadline']} | {t['status']}")
 
    # Update a task
    updated = update_task_status(meeting["tasks"][0]["id"], "Done")
    print(f"\n✅ Task status updated: {updated}")
 
    print("\n✅ All database tests passed!")