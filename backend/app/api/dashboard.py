"""Dashboard endpoints for each role (M6)."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.user import User
from app.services.dashboard_service import (
    get_student_dashboard,
    get_teacher_dashboard,
    get_parent_dashboard,
    get_hod_monitor,
    get_hod_reports,
    get_admin_dashboard,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboards"])


@router.get("/student")
def student_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Student"])),
):
    """Student dashboard: marks, upcoming exams, attempt history."""
    try:
        return get_student_dashboard(db, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/teacher")
def teacher_dashboard_endpoint(
    subject_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Teacher"])),
):
    """Teacher dashboard: own subjects, attempts, averages, violation counts."""
    try:
        return get_teacher_dashboard(db, current_user.user_id, subject_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/parent")
def parent_dashboard_endpoint(
    student_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Parent"])),
):
    """Parent dashboard: linked children exams and published results."""
    try:
        return get_parent_dashboard(db, current_user.user_id, student_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/hod/monitor")
def hod_monitor_endpoint(
    subject_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["HOD", "Admin"])),
):
    """HOD live exam activity (refreshes every 30s)."""
    try:
        return get_hod_monitor(db, current_user.user_id, subject_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/hod/reports")
def hod_reports_endpoint(
    subject_id: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["HOD", "Admin"])),
):
    """HOD all users and results reports with filters and pagination."""
    try:
        return get_hod_reports(
            db=db,
            hod_user_id=current_user.user_id,
            subject_id=subject_id,
            semester=semester,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/admin")
def admin_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"])),
):
    """Admin dashboard overview and settings."""
    try:
        return get_admin_dashboard(db, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
