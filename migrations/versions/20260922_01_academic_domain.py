"""add academic analytics domain

Revision ID: 20260922_01
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = "20260922_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "class_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("grade", sa.String(20), nullable=False),
        sa.Column("major", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    with op.batch_alter_table("students") as batch:
        batch.add_column(sa.Column("class_group_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("email", sa.String(120), nullable=True))
        batch.add_column(sa.Column("enrollment_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("status", sa.String(20), nullable=False, server_default="active"))
        batch.create_foreign_key("fk_students_class_group", "class_groups", ["class_group_id"], ["id"])
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("credits", sa.Float(), nullable=False),
        sa.Column("teacher_name", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "score_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("assessment_id", sa.Integer(), sa.ForeignKey("assessments.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "assessment_id"),
    )


def downgrade():
    op.drop_table("score_records")
    op.drop_table("assessments")
    op.drop_table("courses")
    with op.batch_alter_table("students") as batch:
        batch.drop_constraint("fk_students_class_group", type_="foreignkey")
        batch.drop_column("status")
        batch.drop_column("enrollment_date")
        batch.drop_column("email")
        batch.drop_column("class_group_id")
    op.drop_table("class_groups")
