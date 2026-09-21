"""Versioned REST API for academic data and analytics."""

from collections.abc import Callable
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from .analytics import build_data_quality, build_student_trend
from .orm import Assessment, AuditLog, ClassGroup, Course, ScoreRecord, Student, orm_session


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    grade: str = Field(min_length=1, max_length=20)
    major: str = Field(min_length=1, max_length=80)


class StudentCreate(BaseModel):
    student_id: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=80)
    age: int = Field(gt=0, le=100)
    class_group_id: int | None = None
    email: str | None = Field(default=None, max_length=120)


class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=100)
    credits: float = Field(gt=0, le=20)
    teacher_name: str | None = Field(default=None, max_length=80)


class AssessmentCreate(BaseModel):
    course_id: int
    name: str = Field(min_length=1, max_length=100)
    exam_date: date
    max_score: float = Field(default=100, gt=0, le=1000)


class ScoreCreate(BaseModel):
    student_id: int
    assessment_id: int
    score: float = Field(ge=0, le=100)


def create_api_router(get_current_user: Callable) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["v3 academic API"])

    def require_api_user(request: Request, write: bool = False):
        user = get_current_user(request)
        if not user or not user["is_active"]:
            raise HTTPException(status_code=401, detail="请先登录")
        if write and user["role"] not in {"admin", "teacher"}:
            raise HTTPException(status_code=403, detail="没有写入权限")
        return user

    @router.post("/classes", status_code=status.HTTP_201_CREATED)
    def create_class(payload: ClassCreate, request: Request):
        user = require_api_user(request, write=True)
        try:
            with orm_session() as session:
                item = ClassGroup(name=payload.name.strip(), grade=payload.grade.strip(), major=payload.major.strip())
                session.add(item)
                session.flush()
                session.add(AuditLog(user_id=user["id"], action="create_class", detail=payload.name))
                return {"id": item.id, **payload.model_dump()}
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="班级名称已存在") from exc

    @router.post("/students", status_code=status.HTTP_201_CREATED)
    def create_student(payload: StudentCreate, request: Request):
        user = require_api_user(request, write=True)
        try:
            with orm_session() as session:
                if payload.class_group_id and not session.get(ClassGroup, payload.class_group_id):
                    raise HTTPException(status_code=404, detail="班级不存在")
                item = Student(
                    student_id=payload.student_id.strip(),
                    name=payload.name.strip(),
                    age=payload.age,
                    score=0,
                    class_group_id=payload.class_group_id,
                    email=payload.email,
                    status="active",
                )
                session.add(item)
                session.flush()
                session.add(AuditLog(user_id=user["id"], action="create_student", detail=payload.student_id))
                return {"id": item.id, **payload.model_dump()}
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="学号已存在或班级无效") from exc

    @router.get("/students")
    def list_students(
        request: Request,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        q: str = Query(default="", max_length=80),
    ):
        require_api_user(request)
        keyword = q.strip()
        conditions = []
        if keyword:
            pattern = f"%{keyword}%"
            conditions.append(or_(Student.student_id.like(pattern), Student.name.like(pattern)))
        with orm_session() as session:
            count_query = select(func.count(Student.id))
            data_query = select(Student)
            if conditions:
                count_query = count_query.where(*conditions)
                data_query = data_query.where(*conditions)
            total = session.scalar(count_query) or 0
            rows = session.scalars(
                data_query.order_by(Student.id.desc()).offset((page - 1) * page_size).limit(page_size)
            ).all()
        return {
            "items": [
                {
                    "id": row.id,
                    "student_id": row.student_id,
                    "name": row.name,
                    "age": row.age,
                    "class_group_id": row.class_group_id,
                    "status": row.status,
                }
                for row in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        }

    @router.post("/courses", status_code=status.HTTP_201_CREATED)
    def create_course(payload: CourseCreate, request: Request):
        user = require_api_user(request, write=True)
        try:
            with orm_session() as session:
                item = Course(
                    code=payload.code.strip(),
                    name=payload.name.strip(),
                    credits=payload.credits,
                    teacher_name=payload.teacher_name,
                )
                session.add(item)
                session.flush()
                session.add(AuditLog(user_id=user["id"], action="create_course", detail=payload.code))
                return {"id": item.id, **payload.model_dump()}
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="课程编号已存在") from exc

    @router.post("/assessments", status_code=status.HTTP_201_CREATED)
    def create_assessment(payload: AssessmentCreate, request: Request):
        user = require_api_user(request, write=True)
        with orm_session() as session:
            if not session.get(Course, payload.course_id):
                raise HTTPException(status_code=404, detail="课程不存在")
            item = Assessment(
                course_id=payload.course_id,
                name=payload.name.strip(),
                exam_date=payload.exam_date,
                max_score=payload.max_score,
            )
            session.add(item)
            session.flush()
            session.add(AuditLog(user_id=user["id"], action="create_assessment", detail=payload.name))
            return {"id": item.id, **payload.model_dump(mode="json")}

    @router.post("/scores", status_code=status.HTTP_201_CREATED)
    def create_score(payload: ScoreCreate, request: Request):
        user = require_api_user(request, write=True)
        with orm_session() as session:
            if not session.get(Student, payload.student_id) or not session.get(Assessment, payload.assessment_id):
                raise HTTPException(status_code=404, detail="学生或考试不存在")
            item = session.scalar(
                select(ScoreRecord).where(
                    ScoreRecord.student_id == payload.student_id,
                    ScoreRecord.assessment_id == payload.assessment_id,
                )
            )
            if item:
                item.score = payload.score
            else:
                item = ScoreRecord(**payload.model_dump())
                session.add(item)
            session.flush()
            session.add(AuditLog(user_id=user["id"], action="save_score", detail=f"学生 {payload.student_id}"))
            return {"id": item.id, **payload.model_dump()}

    @router.get("/analytics/overview")
    def analytics_overview(request: Request):
        require_api_user(request)
        with orm_session() as session:
            class_count = session.scalar(select(func.count(ClassGroup.id))) or 0
            course_count = session.scalar(select(func.count(Course.id))) or 0
            assessment_count = session.scalar(select(func.count(Assessment.id))) or 0
            score_rows = session.scalars(select(ScoreRecord).order_by(ScoreRecord.id)).all()
            scores = [float(row.score) for row in score_rows]
            failed_by_student: dict[int, int] = {}
            for row in score_rows:
                if row.score < 60:
                    failed_by_student[row.student_id] = failed_by_student.get(row.student_id, 0) + 1
            risk_count = sum(count >= 2 for count in failed_by_student.values())
        count = len(scores)
        return {
            "class_count": class_count,
            "course_count": course_count,
            "assessment_count": assessment_count,
            "score_count": count,
            "average": round(sum(scores) / count, 2) if count else 0,
            "pass_rate": round(sum(score >= 60 for score in scores) / count * 100, 1) if count else 0,
            "risk_student_count": risk_count,
        }

    @router.get("/analytics/students/{student_id}/trend")
    def student_trend(student_id: int, request: Request):
        require_api_user(request)
        with orm_session() as session:
            if not session.get(Student, student_id):
                raise HTTPException(status_code=404, detail="学生不存在")
            rows = session.execute(
                select(ScoreRecord.score, Assessment.id, Assessment.name, Assessment.exam_date)
                .join(Assessment, Assessment.id == ScoreRecord.assessment_id)
                .where(ScoreRecord.student_id == student_id)
                .order_by(Assessment.exam_date, Assessment.id)
            ).all()
        records = [
            {"score": row.score, "assessment_id": row.id, "assessment_name": row.name, "exam_date": row.exam_date}
            for row in rows
        ]
        return build_student_trend(records)

    @router.get("/analytics/data-quality")
    def data_quality(request: Request):
        require_api_user(request)
        with orm_session() as session:
            students = [{"id": row.id, "email": row.email} for row in session.scalars(select(Student)).all()]
            scores = [{"student_id": row.student_id} for row in session.scalars(select(ScoreRecord)).all()]
        return build_data_quality(students, scores)

    return router
