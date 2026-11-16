"""M7: AI Concept Help service.

Calls Google AI Studio (Gemini) API server-side with strict constraints:
- Only for wrongly answered questions and only after results are published
- Builds prompt from question, student's answer, and correct answer (NO personal data)
- 15s timeout
- Daily request limit enforced (default 10 or configured by Admin)
- Request logged in AI_HELP_REQUEST
- Graceful error / retry message on timeout or failure
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import get_settings
from app.models.ai_help import AIHelpRequest
from app.models.student import Student
from app.models.question import Question
from app.models.answer import Answer
from app.models.answer_key import AnswerKey
from app.models.attempt import ExamAttempt
from app.models.result import Result
from app.models.settings import PlatformSetting


def get_daily_limit(db: Session) -> int:
    """Get the daily AI help limit configured by Admin or fallback to default."""
    setting = db.query(PlatformSetting).filter(PlatformSetting.key == "AI_HELP_DAILY_LIMIT").first()
    if setting:
        try:
            return int(setting.value)
        except ValueError:
            pass
    return get_settings().AI_HELP_DAILY_LIMIT


async def request_ai_concept_help(
    db: Session, student_user_id: int, attempt_id: int, question_id: int
) -> Dict[str, Any]:
    """Request plain-language concept explanation for a wrongly answered question."""
    # 1. Fetch student
    student = db.query(Student).filter(Student.user_id == student_user_id).first()
    if not student:
        raise ValueError("Student profile not found")

    # 2. Check attempt & result published
    attempt = db.query(ExamAttempt).filter(ExamAttempt.attempt_id == attempt_id).first()
    if not attempt or attempt.student_id != student.student_id:
        raise ValueError("Attempt not found or does not belong to this student")

    result = db.query(Result).filter(Result.attempt_id == attempt_id).first()
    if not result or not result.published_at:
        raise ValueError("Results have not been published for this attempt yet")

    # 3. Fetch question & answer
    question = db.query(Question).filter(Question.question_id == question_id).first()
    if not question or question.exam_id != attempt.exam_id:
        raise ValueError("Question not part of this exam")

    answer = (
        db.query(Answer)
        .filter(Answer.attempt_id == attempt_id, Answer.question_id == question_id)
        .first()
    )
    answer_key = db.query(AnswerKey).filter(AnswerKey.question_id == question_id).first()
    correct_option = answer_key.correct_option if answer_key else "N/A"
    selected_option = answer.selected_option if answer else "None (blank)"

    # Must be wrong answer
    if answer and answer.is_correct is True:
        raise ValueError("AI concept help is only available for questions answered incorrectly")

    # 4. Check daily limit
    limit = get_daily_limit(db)
    now = datetime.now(timezone.utc)
    start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    today_requests = (
        db.query(func.count(AIHelpRequest.help_id))
        .filter(
            AIHelpRequest.student_id == student.student_id,
            AIHelpRequest.created_at >= start_of_day,
        )
        .scalar()
        or 0
    )
    if today_requests >= limit:
        raise ValueError(f"Daily AI help limit of {limit} questions reached. Please try again tomorrow.")

    # 5. Build prompt with NO personal student data
    options_text = ""
    if isinstance(question.options, dict):
        options_text = "\n".join([f"{k}: {v}" for k, v in question.options.items()])

    prompt = (
        "You are an encouraging computer science teacher explaining a question concept to a student who made a mistake.\n"
        f"Question: {question.text}\n"
        f"Options:\n{options_text}\n"
        f"Student's Answer: Option {selected_option}\n"
        f"Correct Answer: Option {correct_option}\n\n"
        "Please provide a clear, concise, plain-language concept explanation in 2-3 short paragraphs explaining:\n"
        "1. Why the correct answer is right.\n"
        "2. Why the student's selected option was incorrect.\n"
        "3. The core principle or rule to remember for similar problems.\n"
        "Do not include greeting or signoff. Keep it under 200 words."
    )

    # 6. Call Google AI Studio (Gemini) API with 15s timeout
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY
    explanation = ""

    if not api_key or api_key == "your-gemini-api-key-here":
        # Fallback explanation if no live key is configured
        explanation = (
            f"Concept Explanation for Question {question_id}:\n\n"
            f"The correct answer is Option {correct_option}. "
            f"Option {selected_option} is incorrect because it confuses the fundamental mechanism tested here.\n\n"
            f"Core takeaway: Make sure to review the core definition of '{question.text[:50]}...' "
            f"and distinguish between alternative operations."
        )
    else:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 400},
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            explanation = parts[0].get("text", "")
                else:
                    raise Exception(f"Gemini API returned {res.status_code}: {res.text}")
        except httpx.TimeoutException:
            raise ValueError("AI service timed out after 15 seconds. Please try again.")
        except Exception:
            raise ValueError("AI concept help service is temporarily unavailable. Please try again.")

    if not explanation:
        explanation = "Unable to generate an explanation at this moment. Please retry shortly."

    # 7. Log to AI_HELP_REQUEST
    log_entry = AIHelpRequest(
        student_id=student.student_id,
        question_id=question_id,
        prompt=prompt,
        ai_response=explanation,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return {
        "help_id": log_entry.help_id,
        "question_id": question_id,
        "question_text": question.text,
        "student_answer": selected_option,
        "correct_answer": correct_option,
        "explanation": explanation,
        "created_at": log_entry.created_at.isoformat(),
    }
