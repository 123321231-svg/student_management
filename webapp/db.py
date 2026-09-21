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


class PostgresConnection:
    """Small qmark adapter that keeps the stable v2 SQL compatible with psycopg."""

    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql: str, params=()):
        return self.conn.execute(sql.replace("?", "%s"), params)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


@contextmanager
def connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        import psycopg
        from psycopg.rows import dict_row

        postgres_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        conn = PostgresConnection(psycopg.connect(postgres_url, row_factory=dict_row))
    else:
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
    if os.getenv("DATABASE_URL"):
        return
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL CHECK(age > 0),
                score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
                class_group_id INTEGER,
                email TEXT,
                enrollment_date TEXT,
                status TEXT NOT NULL DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS class_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                grade TEXT NOT NULL,
                major TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                credits REAL NOT NULL CHECK(credits > 0),
                teacher_name TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                max_score REAL NOT NULL DEFAULT 100 CHECK(max_score > 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(course_id) REFERENCES courses(id)
            );

            CREATE TABLE IF NOT EXISTS score_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                assessment_id INTEGER NOT NULL,
                score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, assessment_id),
                FOREIGN KEY(student_id) REFERENCES students(id),
                FOREIGN KEY(assessment_id) REFERENCES assessments(id)
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
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(students)").fetchall()}
        for column, definition in {
            "class_group_id": "INTEGER",
            "email": "TEXT",
            "enrollment_date": "TEXT",
            "status": "TEXT NOT NULL DEFAULT 'active'",
        }.items():
            if column not in columns:
                conn.execute(f"ALTER TABLE students ADD COLUMN {column} {definition}")
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
