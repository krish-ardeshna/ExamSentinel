"""M6: Dashboards & Reports service.

Provides role-specific data:
- Student: personal marks, subject-wise history, upcoming exams, flagged attempts
- Teacher: own subjects, attempts, averages, locked attempts, violation counts
- Parent: linked children only, their exam schedules and published marks
- HOD: live exam activity (refresh 30s), all users and results, filters by subject, semester, date range, paginated
- Admin: user stats, system health, platform configuration
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.hod import HOD
from app.models.subject import Subject
from app.models.exam import Exam
from app.models.attempt import ExamAttempt
from app.models.result import Result
from app.models.violation import ViolationLog
from app.models.settings import PlatformSetting


def get_student_dashboard(db: Session, student_user_id: int) -> Dict[str, Any]:
    """Get dashboard data for a student."""
    user = db.query(User).filter(User.user_id == student_user_id).first()
    if not user or not user.student:
        raise ValueError("Student profile not found")

    student_id = user.student.student_id

    # Published results for this student
    attempts_with_results = (
        db.query(ExamAttempt, Result, Exam, Subject)
        .join(Result, ExamAttempt.attempt_id == Result.attempt_id)
        .join(Exam, ExamAttempt.exam_id == Exam.exam_id)
        .join(Subject, Exam.subject_id == Subject.subject_id)
        .filter(ExamAttempt.student_id == student_id)
        .filter(Result.published_at.isnot(None))
        .all()
    )

    results_data = []
    for att, res, ex, sub in attempts_with_results:
        status_label = "Terminated (violation)" if att.status == "Auto-Locked" else att.status
        results_data.append({
            "attempt_id": att.attempt_id,
            "exam_id": ex.exam_id,
            "exam_title": ex.title,
            "subject_name": sub.name,
            "subject_code": sub.code,
            "score": float(res.score),
            "total_marks": ex.total_marks,
            "percentage": float(res.percentage),
            "status": status_label,
            "flagged": att.flagged,
            "published_at": res.published_at.isoformat() if res.published_at else None,
        })

    # Upcoming / active published exams
    now = datetime.now(timezone.utc)
    all_exams = (
        db.query(Exam, Subject)
        .join(Subject, Exam.subject_id == Subject.subject_id)
        .filter(Exam.status == "Published")
        .all()
    )

    upcoming_exams = []
    attempted_exam_ids = {
        att.exam_id for att in db.query(ExamAttempt.exam_id).filter(ExamAttempt.student_id == student_id).all()
    }

    for ex, sub in all_exams:
        start_tz = ex.start_time if ex.start_time.tzinfo else ex.start_time.replace(tzinfo=timezone.utc)
        end_tz = ex.end_time if ex.end_time.tzinfo else ex.end_time.replace(tzinfo=timezone.utc)
        is_active = start_tz <= now <= end_tz
        is_upcoming = start_tz > now

        upcoming_exams.append({
            "exam_id": ex.exam_id,
            "title": ex.title,
            "subject_name": sub.name,
            "start_time": ex.start_time.isoformat(),
            "end_time": ex.end_time.isoformat(),
            "duration_min": ex.duration_min,
            "total_marks": ex.total_marks,
            "is_active": is_active,
            "is_upcoming": is_upcoming,
            "already_attempted": ex.exam_id in attempted_exam_ids,
        })

    return {
        "student_info": {
            "name": user.name,
            "email": user.email,
            "enrollment_no": user.student.enrollment_no,
            "semester": user.student.semester,
            "program": user.student.program,
        },
        "results": results_data,
        "upcoming_exams": upcoming_exams,
    }


def get_teacher_dashboard(db: Session, teacher_user_id: int, subject_id: Optional[int] = None) -> Dict[str, Any]:
    """Get dashboard data for a teacher's subjects."""
    user = db.query(User).filter(User.user_id == teacher_user_id).first()
    if not user or not user.teacher:
        raise ValueError("Teacher profile not found")

    teacher = user.teacher
    query_subjects = db.query(Subject).filter(Subject.teacher_id == teacher.teacher_id)
    if subject_id:
        query_subjects = query_subjects.filter(Subject.subject_id == subject_id)
    subjects = query_subjects.all()

    subject_data = []
    for sub in subjects:
        exams = db.query(Exam).filter(Exam.subject_id == sub.subject_id).all()
        exam_list = []
        for ex in exams:
            attempts = db.query(ExamAttempt).filter(ExamAttempt.exam_id == ex.exam_id).all()
            locked_count = sum(1 for a in attempts if a.status == "Auto-Locked" or a.flagged)
            results = (
                db.query(Result)
                .join(ExamAttempt, Result.attempt_id == ExamAttempt.attempt_id)
                .filter(ExamAttempt.exam_id == ex.exam_id)
                .all()
            )
            avg_score = (
                sum(float(r.score) for r in results) / len(results) if results else 0.0
            )
            violations_count = (
                db.query(ViolationLog)
                .join(ExamAttempt, ViolationLog.attempt_id == ExamAttempt.attempt_id)
                .filter(ExamAttempt.exam_id == ex.exam_id)
                .count()
            )

            exam_list.append({
                "exam_id": ex.exam_id,
                "title": ex.title,
                "status": ex.status,
                "start_time": ex.start_time.isoformat(),
                "end_time": ex.end_time.isoformat(),
                "total_marks": ex.total_marks,
                "total_attempts": len(attempts),
                "locked_attempts": locked_count,
                "violations_count": violations_count,
                "average_score": round(avg_score, 2),
            })

        subject_data.append({
            "subject_id": sub.subject_id,
            "code": sub.code,
            "name": sub.name,
            "semester": sub.semester,
            "exams": exam_list,
        })

    return {
        "teacher_name": user.name,
        "department": teacher.department,
        "subjects": subject_data,
    }


def get_parent_dashboard(db: Session, parent_user_id: int, student_id: Optional[int] = None) -> Dict[str, Any]:
    """Get dashboard data for a parent (linked children only)."""
    user = db.query(User).filter(User.user_id == parent_user_id).first()
    if not user or not user.parent:
        raise ValueError("Parent profile not found")

    parent = user.parent
    children = db.query(Student).filter(Student.parent_id == parent.parent_id).all()
    if not children:
        return {"parent_name": user.name, "children": [], "selected_child": None}

    # If student_id specified, ensure it belongs to this parent
    target_child = None
    if student_id:
        target_child = next((c for c in children if c.student_id == student_id), None)
        if not target_child:
            raise ValueError("Child not linked to this parent")
    else:
        target_child = children[0]

    # Get results for selected child
    child_user = target_child.user
    attempts = (
        db.query(ExamAttempt, Result, Exam, Subject)
        .join(Result, ExamAttempt.attempt_id == Result.attempt_id)
        .join(Exam, ExamAttempt.exam_id == Exam.exam_id)
        .join(Subject, Exam.subject_id == Subject.subject_id)
        .filter(ExamAttempt.student_id == target_child.student_id)
        .filter(Result.published_at.isnot(None))
        .all()
    )

    results_data = []
    for att, res, ex, sub in attempts:
        status_label = "Terminated (violation)" if att.status == "Auto-Locked" else att.status
        results_data.append({
            "exam_title": ex.title,
            "subject_name": sub.name,
            "score": float(res.score),
            "total_marks": ex.total_marks,
            "percentage": float(res.percentage),
            "status": status_label,
            "flagged": att.flagged,
            "published_at": res.published_at.isoformat() if res.published_at else None,
        })

    return {
        "parent_name": user.name,
        "children": [
            {
                "student_id": c.student_id,
                "name": c.user.name,
                "enrollment_no": c.enrollment_no,
            }
            for c in children
        ],
        "selected_child": {
            "student_id": target_child.student_id,
            "name": child_user.name,
            "enrollment_no": target_child.enrollment_no,
            "results": results_data,
        },
    }


def get_hod_monitor(db: Session, hod_user_id: int, subject_id: Optional[int] = None) -> Dict[str, Any]:
    """Get live exam monitor for HOD (refreshes every 30s).

    Shows ongoing exams, attempts In Progress, Submitted, Locked, and violations.
    """
    user = db.query(User).filter(User.user_id == hod_user_id).first()
    if not user or not user.hod:
        raise ValueError("HOD profile not found")

    # Scope to HOD department if applicable
    department = user.hod.department

    # Active/ongoing exams
    query = (
        db.query(Exam, Subject)
        .join(Subject, Exam.subject_id == Subject.subject_id)
        .filter(Exam.status.in_(["Published"]))
    )
    if subject_id:
        query = query.filter(Exam.subject_id == subject_id)

    exams = query.all()

    active_exams_data = []
    for ex, sub in exams:
        attempts = db.query(ExamAttempt).filter(ExamAttempt.exam_id == ex.exam_id).all()
        in_progress = sum(1 for a in attempts if a.status == "In Progress")
        submitted = sum(1 for a in attempts if a.status == "Submitted")
        locked = sum(1 for a in attempts if a.status == "Auto-Locked")

        # Recent violations
        violations = (
            db.query(ViolationLog, ExamAttempt, Student, User)
            .join(ExamAttempt, ViolationLog.attempt_id == ExamAttempt.attempt_id)
            .join(Student, ExamAttempt.student_id == Student.student_id)
            .join(User, Student.user_id == User.user_id)
            .filter(ExamAttempt.exam_id == ex.exam_id)
            .order_by(desc(ViolationLog.occurred_at))
            .limit(10)
            .all()
        )

        v_list = []
        for v, att, st, u in violations:
            v_list.append({
                "log_id": v.log_id,
                "attempt_id": att.attempt_id,
                "student_name": u.name,
                "type": v.type,
                "occurred_at": v.occurred_at.isoformat(),
            })

        active_exams_data.append({
            "exam_id": ex.exam_id,
            "title": ex.title,
            "subject_name": sub.name,
            "start_time": ex.start_time.isoformat(),
            "end_time": ex.end_time.isoformat(),
            "in_progress_count": in_progress,
            "submitted_count": submitted,
            "locked_count": locked,
            "recent_violations": v_list,
        })

    return {
        "hod_name": user.name,
        "department": department,
        "active_exams": active_exams_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_hod_reports(
    db: Session,
    hod_user_id: int,
    subject_id: Optional[int] = None,
    semester: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Get comprehensive reports for HOD with filters and pagination."""
    user = db.query(User).filter(User.user_id == hod_user_id).first()
    if not user or not user.hod:
        raise ValueError("HOD profile not found")

    # Date range validation
    if start_date and end_date:
        try:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            e_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if s_dt > e_dt:
                raise ValueError("Start date must not be after end date")
        except ValueError as e:
            if "Start date" in str(e):
                raise
            raise ValueError("Invalid date format (YYYY-MM-DD)")

    query = (
        db.query(Result, ExamAttempt, Exam, Subject, Student, User)
        .join(ExamAttempt, Result.attempt_id == ExamAttempt.attempt_id)
        .join(Exam, ExamAttempt.exam_id == Exam.exam_id)
        .join(Subject, Exam.subject_id == Subject.subject_id)
        .join(Student, ExamAttempt.student_id == Student.student_id)
        .join(User, Student.user_id == User.user_id)
    )

    if subject_id:
        query = query.filter(Subject.subject_id == subject_id)
    if semester:
        query = query.filter(Subject.semester == semester)
    if start_date:
        s_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Result.published_at >= s_dt)
    if end_date:
        e_dt = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(Result.published_at <= e_dt)

    total_count = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(desc(Result.published_at)).offset(offset).limit(page_size).all()

    report_items = []
    for res, att, ex, sub, st, u in items:
        status_label = "Terminated (violation)" if att.status == "Auto-Locked" else att.status
        report_items.append({
            "result_id": res.result_id,
            "student_name": u.name,
            "enrollment_no": st.enrollment_no,
            "subject_name": sub.name,
            "subject_code": sub.code,
            "semester": sub.semester,
            "exam_title": ex.title,
            "score": float(res.score),
            "total_marks": ex.total_marks,
            "percentage": float(res.percentage),
            "status": status_label,
            "flagged": att.flagged,
            "published_at": res.published_at.isoformat() if res.published_at else None,
        })

    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "items": report_items,
    }


def get_admin_dashboard(db: Session, admin_user_id: int) -> Dict[str, Any]:
    """Get dashboard stats for Admin."""
    user = db.query(User).filter(User.user_id == admin_user_id).first()
    if not user or user.role != "Admin":
        raise ValueError("Admin profile not found")

    total_users = db.query(User).count()
    users_by_role = db.query(User.role, func.count(User.user_id)).group_by(User.role).all()
    total_exams = db.query(Exam).count()
    total_attempts = db.query(ExamAttempt).count()
    flagged_attempts = db.query(ExamAttempt).filter(ExamAttempt.flagged.is_(True)).count()

    settings = db.query(PlatformSetting).all()
    settings_dict = {s.key: s.value for s in settings}

    return {
        "admin_name": user.name,
        "stats": {
            "total_users": total_users,
            "users_by_role": {role: count for role, count in users_by_role},
            "total_exams": total_exams,
            "total_attempts": total_attempts,
            "flagged_attempts": flagged_attempts,
        },
        "settings": settings_dict,
    }
