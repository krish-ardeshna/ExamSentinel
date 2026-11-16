"""Initial database schema matching Lab-8 ER diagram.

Revision ID: 001_initial_tables
Revises: None
Create Date: 2026-11-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Active"),
        sa.Column("failed_login_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
    )

    # 2. parents
    op.create_table(
        "parents",
        sa.Column("parent_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=15), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("parent_id"),
        sa.UniqueConstraint("user_id"),
    )

    # 3. students
    op.create_table(
        "students",
        sa.Column("student_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("enrollment_no", sa.String(length=30), nullable=True),
        sa.Column("program", sa.String(length=100), nullable=True),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.parent_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("student_id"),
        sa.UniqueConstraint("enrollment_no"),
        sa.UniqueConstraint("user_id"),
    )

    # 4. teachers
    op.create_table(
        "teachers",
        sa.Column("teacher_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("designation", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("teacher_id"),
        sa.UniqueConstraint("user_id"),
    )

    # 5. hods
    op.create_table(
        "hods",
        sa.Column("hod_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("hod_id"),
        sa.UniqueConstraint("user_id"),
    )

    # 6. subjects
    op.create_table(
        "subjects",
        sa.Column("subject_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("hod_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["hod_id"], ["hods.hod_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.teacher_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("subject_id"),
        sa.UniqueConstraint("code"),
    )

    # 7. exams
    op.create_table(
        "exams",
        sa.Column("exam_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("total_marks", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Draft"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.subject_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("exam_id"),
    )

    # 8. questions
    op.create_table(
        "questions",
        sa.Column("question_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("marks", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id"),
    )

    # 9. answer_keys
    op.create_table(
        "answer_keys",
        sa.Column("key_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("correct_option", sa.String(length=5), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.question_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("key_id"),
        sa.UniqueConstraint("question_id"),
    )

    # 10. exam_attempts
    op.create_table(
        "exam_attempts",
        sa.Column("attempt_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="In Progress"),
        sa.Column("flagged", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.student_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("attempt_id"),
        sa.UniqueConstraint("exam_id", "student_id", name="uq_exam_student"),
    )

    # 11. answers
    op.create_table(
        "answers",
        sa.Column("answer_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_option", sa.String(length=5), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["exam_attempts.attempt_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.question_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("answer_id"),
    )

    # 12. violation_logs
    op.create_table(
        "violation_logs",
        sa.Column("log_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["exam_attempts.attempt_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("log_id"),
    )

    # 13. results
    op.create_table(
        "results",
        sa.Column("result_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["exam_attempts.attempt_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("result_id"),
        sa.UniqueConstraint("attempt_id"),
    )

    # 14. ai_help_requests
    op.create_table(
        "ai_help_requests",
        sa.Column("help_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("ai_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.question_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.student_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("help_id"),
    )

    # 15. platform_settings
    op.create_table(
        "platform_settings",
        sa.Column("setting_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("setting_id"),
        sa.UniqueConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("platform_settings")
    op.drop_table("ai_help_requests")
    op.drop_table("results")
    op.drop_table("violation_logs")
    op.drop_table("answers")
    op.drop_table("exam_attempts")
    op.drop_table("answer_keys")
    op.drop_table("questions")
    op.drop_table("exams")
    op.drop_table("subjects")
    op.drop_table("hods")
    op.drop_table("teachers")
    op.drop_table("students")
    op.drop_table("parents")
    op.drop_table("users")
