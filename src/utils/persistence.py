import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseManager:
    """Manages SQLite database for tracking course progress and session state"""

    def __init__(self, db_path: str = "data/automation.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    url TEXT PRIMARY KEY,
                    platform TEXT,
                    status TEXT,
                    progress REAL DEFAULT 0.0,
                    last_updated TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_url TEXT,
                    path TEXT,
                    earned_at TIMESTAMP,
                    FOREIGN KEY (course_url) REFERENCES courses (url)
                )
            """)
            conn.commit()

    def update_course_status(self, url: str, platform: str, status: str, progress: float = 0.0):
        """Update or insert course status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO courses (url, platform, status, progress, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    status = excluded.status,
                    progress = excluded.progress,
                    last_updated = excluded.last_updated
            """, (url, platform, status, progress, datetime.now()))
            conn.commit()

    def get_course_status(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve status for a specific course"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM courses WHERE url = ?", (url,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_certificate(self, course_url: str, path: str):
        """Record a newly earned certificate"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO certificates (course_url, path, earned_at)
                VALUES (?, ?, ?)
            """, (course_url, path, datetime.now()))
            conn.commit()

    def get_all_courses(self) -> List[Dict[str, Any]]:
        """Retrieve all tracked courses"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM courses ORDER BY last_updated DESC")
            return [dict(row) for row in cursor.fetchall()]
