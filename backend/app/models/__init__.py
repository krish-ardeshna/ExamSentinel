"""Models package - import all models so Alembic and the app can see them."""

from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.hod import HOD
from app.models.subject import Subject
from app.models.exam import Exam
from app.models.question import Question
from app.models.answer_key import AnswerKey
from app.models.attempt import ExamAttempt
from app.models.answer import Answer
from app.models.violation import ViolationLog
from app.models.result import Result
from app.models.ai_help import AIHelpRequest
from app.models.settings import PlatformSetting

__all__ = [
    "User", "Student", "Teacher", "Parent", "HOD",
    "Subject", "Exam", "Question", "AnswerKey",
    "ExamAttempt", "Answer", "ViolationLog", "Result",
    "AIHelpRequest", "PlatformSetting",
]
