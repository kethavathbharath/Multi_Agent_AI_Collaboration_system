import os
import json
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite tables for task history and agent execution logs."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        user_request TEXT NOT NULL,
        status TEXT NOT NULL,
        final_output TEXT,
        state_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        action TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks (task_id)
    )
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")

def save_task(task_id: str, user_request: str, status: str, state_dict: Dict[str, Any], final_output: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    state_json = json.dumps(state_dict)

    cursor.execute("""
    INSERT INTO tasks (task_id, user_request, status, final_output, state_json, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(task_id) DO UPDATE SET
        status = excluded.status,
        final_output = excluded.final_output,
        state_json = excluded.state_json,
        updated_at = excluded.updated_at
    """, (task_id, user_request, status, final_output, state_json, now, now))

    # Save agent logs
    agent_logs = state_dict.get("agent_logs", [])
    cursor.execute("DELETE FROM agent_logs WHERE task_id = ?", (task_id,))
    for log in agent_logs:
        cursor.execute("""
        INSERT INTO agent_logs (task_id, agent_name, action, message, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            log.get("agent_name", "System"),
            log.get("action", "Log"),
            log.get("message", ""),
            log.get("status", "info"),
            log.get("timestamp", now)
        ))

    conn.commit()
    conn.close()

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    task_data = dict(row)
    if task_data.get("state_json"):
        task_data["state"] = json.loads(task_data["state_json"])
    return task_data

def get_all_tasks(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT task_id, user_request, status, created_at, updated_at FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]

