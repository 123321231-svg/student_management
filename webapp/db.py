import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .security import hash_password


ROOT_DIR = Path(__file__).resolve().parents[1]


def database_path() -> str:
    configured = os.getenv("DATABASE_PATH")
    if configured:
        return configured
    return str(ROOT_DIR / "students.db")


@contextmanager
def connection():
    conn = sqlite3.connect(database_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL CHECK(age > 0),
                score REAL NOT NULL CHECK(score >= 0 AND score <= 100)
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        admin = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
        if not admin:
            conn.execute(
                """
                INSERT INTO users(username, full_name, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "admin",
                    "系统管理员",
                    hash_password(os.getenv("ADMIN_INITIAL_PASSWORD", "admin123")),
                    "admin",
                ),
            )


def write_audit(conn, user_id: int | None, action: str, detail: str = "") -> None:
    conn.execute(
        "INSERT INTO audit_logs(user_id, action, detail) VALUES (?, ?, ?)",
        (user_id, action, detail),
    )
