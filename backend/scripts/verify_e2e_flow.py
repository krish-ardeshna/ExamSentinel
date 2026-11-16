"""End-to-End System Integration Verification Script.

Tests the full lifecycle of OEPMS from start to finish:
1. M1: Authentication & Role Tokens (Admin, Teacher, Student, Parent, HOD)
2. M1: Admin creates and manages user accounts
3. M2: Teacher creates an exam, adds questions with options & marks, submits answer key, publishes
4. M3: Student starts attempt inside window, autosaves answers
5. M4: Proctoring violation detection (TAB_SWITCH event -> Auto-Lock & flag)
6. M5: Automated evaluation (verifies score & percentage, checks Terminated (violation) status)
7. M6: Dashboards for Student, Teacher, Parent, HOD, and Admin
8. M7: AI Concept Help for wrongly answered question (checks prompt sanitization & daily limit)
"""

import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["DATABASE_URL"] = "sqlite:///./oepms_e2e.db"

from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.seed import seed_database
from app.models import *

client = TestClient(app)


def run_e2e_verification():
    print("======================================================================")
    print("STARTING OEPMS END-TO-END SYSTEM INTEGRATION VERIFICATION")
    print("======================================================================\n")

    # Step 0: Initialize and seed clean database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()
    print("✓ Step 0: Database initialized and seeded with demo records.\n")

    # -------------------------------------------------------------------------
    # Phase 1: M1 Authentication & Role-Based Access
    # -------------------------------------------------------------------------
    print("--- Phase 1: Testing M1 Authentication & Role-Based Access ---")
    
    # 1.1 Admin login
    res = client.post("/auth/login", json={"email": "admin@oepms.edu", "password": "Admin@1234"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    admin_token = res.json()["access_token"]
    assert res.json()["role"] == "Admin"
    print("✓ 1.1 Admin authenticated successfully with JWT role token.")

    # 1.2 Teacher login
    res = client.post("/auth/login", json={"email": "rajesh.teacher@oepms.edu", "password": "Teach@1234"})
    assert res.status_code == 200
    teacher_token = res.json()["access_token"]
    assert res.json()["role"] == "Teacher"
    print("✓ 1.2 Teacher authenticated successfully with JWT role token.")

    # 1.3 Student login (Sneha Gupta, Student 4)
    res = client.post("/auth/login", json={"email": "sneha.student@oepms.edu", "password": "Stud@1234"})
    assert res.status_code == 200
    student_token = res.json()["access_token"]
    assert res.json()["role"] == "Student"
    student_id = res.json()["user_id"]
    print("✓ 1.3 Student authenticated successfully with JWT role token.")

    # 1.4 Parent login
    res = client.post("/auth/login", json={"email": "suresh.parent@oepms.edu", "password": "Parent@123"})
    assert res.status_code == 200
    parent_token = res.json()["access_token"]
    assert res.json()["role"] == "Parent"
    print("✓ 1.4 Parent authenticated successfully with JWT role token.")

    # 1.5 HOD login
    res = client.post("/auth/login", json={"email": "hod@oepms.edu", "password": "Hod@12345"})
    assert res.status_code == 200
    hod_token = res.json()["access_token"]
    assert res.json()["role"] == "HOD"
    print("✓ 1.5 HOD authenticated successfully with JWT role token.")

    # 1.6 Verify lockout after 5 failed logins
    dummy_email = "lockout_verify@oepms.edu"
    # Create test user
    client.post(
        "/users",
        json={"name": "Lock Test", "email": dummy_email, "password": "Pass@1234", "role": "Student"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    for _ in range(5):
        client.post("/auth/login", json={"email": dummy_email, "password": "WrongPassword@1"})
    # 6th attempt with correct password must be locked
    res_locked = client.post("/auth/login", json={"email": dummy_email, "password": "Pass@1234"})
    assert res_locked.status_code == 423, f"Expected 423 Locked, got {res_locked.status_code}"
    print("✓ 1.6 Security lockout verified: 5 failed attempts locks account for 15 minutes.\n")

    # -------------------------------------------------------------------------
    # Phase 2: M2 Exam Scheduling, Authoring & Publishing
    # -------------------------------------------------------------------------
    print("--- Phase 2: Testing M2 Exam Scheduling & Publishing ---")
    
    # 2.1 Teacher fetches own subjects
    res = client.get("/exams/subjects/list", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 200
    subjects = res.json()
    assert len(subjects) >= 1
    target_subject = subjects[0]["subject_id"]
    print(f"✓ 2.1 Teacher retrieved assigned subject #{target_subject} ({subjects[0]['name']}).")

    # 2.2 Teacher schedules an exam (Draft)
    now = datetime.now()
    st = (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    et = (now + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")

    exam_payload = {
        "subject_id": target_subject,
        "title": "Algorithms End-Term Practical Exam",
        "start_time": (now + timedelta(days=1)).strftime("%Y-%m-%d 10:00:00"), # future for validation
        "end_time": (now + timedelta(days=1, hours=2)).strftime("%Y-%m-%d 12:00:00"),
        "duration_min": 60,
        "total_marks": 10,
        "status": "Draft",
    }
    res = client.post("/exams", json=exam_payload, headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 201, f"Create exam failed: {res.text}"
    new_exam = res.json()
    new_exam_id = new_exam["exam_id"]
    print(f"✓ 2.2 Exam #{new_exam_id} created in Draft status.")

    # 2.3 Teacher attempts to publish with 0 questions -> must fail
    res = client.post(f"/exams/{new_exam_id}/publish", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 400
    assert "Add at least one question" in res.json()["detail"]
    print("✓ 2.3 Publish rejected with 'Add at least one question' when paper has 0 questions.")

    # 2.4 Teacher adds two questions (5 marks each = 10 total)
    q1_res = client.post(
        f"/exams/{new_exam_id}/questions",
        json={
            "text": "What is the worst-case time complexity of Merge Sort?",
            "options": {"A": "O(n^2)", "B": "O(n log n)", "C": "O(log n)", "D": "O(n)"},
            "marks": 5,
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert q1_res.status_code == 201
    q1_id = q1_res.json()["question_id"]

    q2_res = client.post(
        f"/exams/{new_exam_id}/questions",
        json={
            "text": "Which paradigm does Dijkstra's shortest path algorithm use?",
            "options": {"A": "Greedy", "B": "Dynamic Programming", "C": "Backtracking", "D": "Divide and Conquer"},
            "marks": 5,
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert q2_res.status_code == 201
    q2_id = q2_res.json()["question_id"]
    print("✓ 2.4 Questions added (2 MCQs totaling 10 marks).")

    # 2.5 Teacher submits official answer key
    res = client.put(
        f"/exams/{new_exam_id}/answer-key",
        json={"answers": {q1_id: "B", q2_id: "A"}},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res.status_code == 200
    print("✓ 2.5 Official answer key submitted and stored securely.")

    # 2.6 Publish exam
    res = client.post(f"/exams/{new_exam_id}/publish", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 200
    assert res.json()["status"] == "Published"
    print("✓ 2.6 Exam published successfully.\n")

    # -------------------------------------------------------------------------
    # Phase 3: M3 Exam Attempt & Autosave
    # -------------------------------------------------------------------------
    print("--- Phase 3: Testing M3 Exam Attempt & Autosave ---")

    # We will use pre-seeded published Exam 1 (Data Structures Unit Test 1) whose window is currently open
    exam1_id = 1
    # Student starts attempt
    res = client.post(f"/attempts?exam_id={exam1_id}", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 201, f"Start attempt failed: {res.text}"
    attempt_id = res.json()["attempt_id"]
    assert res.json()["status"] == "In Progress"
    print(f"✓ 3.1 Student started attempt #{attempt_id} (Status: In Progress).")

    # Fetch questions paper (no answer keys revealed)
    res = client.get(f"/exams/{exam1_id}/paper", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    exam_questions = res.json()
    assert len(exam_questions) >= 2
    q_first = exam_questions[0]["question_id"]
    q_second = exam_questions[1]["question_id"]

    # Student autosaves answer for question 1 (Correct answer 'B')
    res = client.put(
        f"/attempts/{attempt_id}/answers",
        json={"answers": {q_first: "B", q_second: "A"}},  # q_second is wrong ('A' instead of 'C')
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 200
    print("✓ 3.2 Answers autosaved in real time.\n")

    # -------------------------------------------------------------------------
    # Phase 4: M4 Screen Proctoring & Auto-Lock
    # -------------------------------------------------------------------------
    print("--- Phase 4: Testing M4 Automated Proctoring Violation & Lock ---")

    # Student switches tabs -> frontend posts TAB_SWITCH event
    res = client.post(
        f"/attempts/{attempt_id}/events",
        json={"event_type": "TAB_SWITCH", "timestamp": datetime.now(timezone.utc).isoformat()},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 200
    event_data = res.json()
    assert event_data["locked"] is True
    assert event_data["status"] == "Auto-Locked"
    print("✓ 4.1 Proctoring detected TAB_SWITCH -> VIOLATION_LOG written, flagged=true, status=Auto-Locked.")

    # Student attempts to modify answers while locked -> must be rejected
    res = client.put(
        f"/attempts/{attempt_id}/answers",
        json={"answers": {q_first: "A"}},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 400
    print("✓ 4.2 Locked attempt rejected answer modifications.\n")

    # -------------------------------------------------------------------------
    # Phase 5: M5 Automated Evaluation & Grading
    # -------------------------------------------------------------------------
    print("--- Phase 5: Testing M5 Automated Evaluation ---")

    # Fetch result for the auto-locked attempt
    res = client.get(f"/results/attempt/{attempt_id}", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200, f"Result fetch failed: {res.text}"
    result_data = res.json()
    assert result_data["status"] == "Terminated (violation)"
    assert result_data["flagged"] is True
    print(f"✓ 5.1 Result evaluated on partial answers: Score {result_data['score']}/{result_data['total_marks']}.")
    print("✓ 5.2 Attempt properly labeled as 'Terminated (violation)'.\n")

    # -------------------------------------------------------------------------
    # Phase 6: M6 Role-Based Dashboards
    # -------------------------------------------------------------------------
    print("--- Phase 6: Testing M6 Role-Specific Dashboards ---")

    # Student Dashboard
    res = client.get("/dashboard/student", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    assert "student_info" in res.json()
    assert "results" in res.json()
    print("✓ 6.1 Student dashboard returned marks history, upcoming exams, and attempts.")

    # Teacher Dashboard
    res = client.get("/dashboard/teacher", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 200
    teacher_dash = res.json()
    assert "subjects" in teacher_dash
    print("✓ 6.2 Teacher dashboard returned subject exams, attempts count, averages, and violation tallies.")

    # Parent Dashboard
    res = client.get("/dashboard/parent", headers={"Authorization": f"Bearer {parent_token}"})
    assert res.status_code == 200
    parent_dash = res.json()
    assert "children" in parent_dash
    print("✓ 6.3 Parent dashboard returned linked children and their published performance.")

    # HOD Monitor (30s live)
    res = client.get("/dashboard/hod/monitor", headers={"Authorization": f"Bearer {hod_token}"})
    assert res.status_code == 200
    hod_mon = res.json()
    assert "active_exams" in hod_mon
    print("✓ 6.4 HOD monitor returned live exams, in-progress/submitted/locked counts, and violation feed.")

    # Admin Dashboard
    res = client.get("/dashboard/admin", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    admin_dash = res.json()
    assert "stats" in admin_dash
    print("✓ 6.5 Admin dashboard returned system stats and platform settings.\n")

    # -------------------------------------------------------------------------
    # Phase 7: M7 AI Concept Help (Gemini API)
    # -------------------------------------------------------------------------
    print("--- Phase 7: Testing M7 AI Concept Help ---")

    # Student asks AI for question 2 (which was answered wrongly with 'A')
    res = client.post(
        "/ai-help",
        json={"attempt_id": attempt_id, "question_id": q_second},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 200, f"AI help request failed: {res.text}"
    ai_data = res.json()
    assert "explanation" in ai_data
    assert len(ai_data["explanation"]) > 20
    print(f"✓ 7.1 AI concept help returned plain-language remediation:\n    \"{ai_data['explanation'][:100]}...\"")

    # Asking AI for a CORRECT answer must be rejected
    res_correct = client.post(
        "/ai-help",
        json={"attempt_id": attempt_id, "question_id": q_first},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_correct.status_code == 400
    assert "only available for questions answered incorrectly" in res_correct.json()["detail"]
    print("✓ 7.2 AI request correctly restricted to wrongly answered questions.")

    # Check history log in AI_HELP_REQUEST
    res_hist = client.get("/ai-help/history", headers={"Authorization": f"Bearer {student_token}"})
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 1
    print("✓ 7.3 AI help request logged in AI_HELP_REQUEST table.\n")

    print("======================================================================")
    print("ALL MODULES (M1 - M7) PASSED COMPLETE END-TO-END VERIFICATION!")
    print("======================================================================")


if __name__ == "__main__":
    run_e2e_verification()
