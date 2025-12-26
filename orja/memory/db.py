from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


@dataclass
class Message:
    id: int
    timestamp_utc: str
    role: str
    content: str
    session_id: str


class MemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tables()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _ensure_tables(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    session_id TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add_message(self, role: str, content: str, session_id: str, timestamp: datetime) -> None:
        iso_ts = timestamp.isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (timestamp_utc, role, content, session_id) VALUES (?, ?, ?, ?)",
                (iso_ts, role, content, session_id),
            )
            conn.commit()

    def recent_messages(self, limit: int = 20) -> List[Message]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, timestamp_utc, role, content, session_id FROM messages "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
        return [
            Message(
                id=row[0],
                timestamp_utc=row[1],
                role=row[2],
                content=row[3],
                session_id=row[4],
            )
            for row in rows
        ]

