"""SQLAlchemy models for the v3 academic domain.

The v2 pages keep their stable SQLite access while the v3 domain uses this
portable ORM layer. With ``DATABASE_URL`` it can target PostgreSQL; without it
the same models use the local SQLite file, which keeps learning and EXE usage
simple.
"""

import os
from contextlib import contextmanager
from datetime import UTC, date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import NullPool

from .db import database_path
from .security import hash_password


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


class ClassGroup(Base):
    __tablename__ = "class_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    grade: Mapped[str] = mapped_column(String(20))
    major: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    students: Mapped[list["Student"]] = relationship(back_populates="class_group")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    full_name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    is_active: Mapped[int] = mapped_column(default=1, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    age: Mapped[int]
    score: Mapped[float] = mapped_column(Float, default=0)
    class_group_id: Mapped[int | None] = mapped_column(ForeignKey("class_groups.id"))
    email: Mapped[str | None] = mapped_column(String(120))
    enrollment_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default=text("'active'")
    )
    class_group: Mapped[ClassGroup | None] = relationship(back_populates="students")
    scores: Mapped[list["ScoreRecord"]] = relationship(back_populates="student")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    credits: Mapped[float] = mapped_column(Float)
    teacher_name: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="course")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    name: Mapped[str] = mapped_column(String(100))
    exam_date: Mapped[date] = mapped_column(Date)
    max_score: Mapped[float] = mapped_column(Float, default=100)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    course: Mapped[Course] = relationship(back_populates="assessments")
    scores: Mapped[list["ScoreRecord"]] = relationship(back_populates="assessment")


class ScoreRecord(Base):
    __tablename__ = "score_records"
    __table_args__ = (UniqueConstraint("student_id", "assessment_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    student: Mapped[Student] = relationship(back_populates="scores")
    assessment: Mapped[Assessment] = relationship(back_populates="scores")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None]
    action: Mapped[str] = mapped_column(String(80))
    detail: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )


def _database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured.replace("postgres://", "postgresql+psycopg://", 1)
    return f"sqlite:///{database_path()}"


database_url = _database_url()
engine_options = {"connect_args": {"check_same_thread": False}, "poolclass": NullPool} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_orm() -> None:
    Base.metadata.create_all(engine)


def seed_admin() -> None:
    from sqlalchemy import select

    with orm_session() as session:
        if not session.scalar(select(User).where(User.username == "admin")):
            session.add(
                User(
                    username="admin",
                    full_name="系统管理员",
                    password_hash=hash_password(os.getenv("ADMIN_INITIAL_PASSWORD", "admin123")),
                    role="admin",
                    is_active=1,
                )
            )


@contextmanager
def orm_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
