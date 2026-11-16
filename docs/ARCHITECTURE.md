# OEPMS System Architecture & Module Mapping

The **Online Exam Proctoring & Management System (OEPMS)** is architected as a modern, decoupled full-stack platform covering the complete examination lifecycle: user access governance, exam authoring, browser-enforced proctoring, server-side grading, role-specific analytical dashboards, and AI-assisted concept remediation.

---

## 1. System Technology Stack

| Layer | Technology | Key Responsibilities |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, React Router v6, Lucide Icons | Responsive UI, Page Visibility API & Fullscreen API proctoring, real-time timer countdown, question navigator, lock overlay |
| **Backend API** | FastAPI (Python 3.11+), Pydantic v2 | High-throughput REST API, custom validation formatting, automated background grading, JWT authentication |
| **ORM & Migrations**| SQLAlchemy 2.0, Alembic | Type-safe entity mappings conforming to Lab-8 ER model, schema migration scripts |
| **Database** | PostgreSQL 16 (production/docker), SQLite in-memory (pytest) | Relational persistence, unique constraints, foreign keys, cascade deletes |
| **AI Integration** | Google AI Studio (Gemini 1.5 Flash) API | Server-side concept remediation for wrong answers with 15s timeout and daily quota controls |
| **Testing** | pytest, pytest-asyncio, Vitest, RTL | 72 unit tests across UT-USR, UT-EXM, UT-ATT; frontend render testing |
| **Containerization**| Docker & Docker Compose | Multi-container deployment (`db`, `backend`, `frontend`) |

---

## 2. Top-Down Module Hierarchy & Folder Mapping (M1 - M7)

| Module ID | Module Name | Architectural Responsibility | Key Source Files |
| :--- | :--- | :--- | :--- |
| **M1** | **User & Access Management** | Authentication, JWT issuance, bcrypt password hashing, 5-strike 15-minute account lockout, user CRUD, role protection, deletion safety rules | `backend/app/models/user.py`<br>`backend/app/schemas/user.py`<br>`backend/app/services/user_service.py`<br>`backend/app/api/auth.py`<br>`backend/app/api/users.py` |
| **M2** | **Exam Management** | Teacher subject verification, exam scheduling, MCQ authoring with options and marks, official answer key submission, paper locking at start time, publish rule validation | `backend/app/models/exam.py`<br>`backend/app/models/question.py`<br>`backend/app/models/answer_key.py`<br>`backend/app/schemas/exam.py`<br>`backend/app/services/exam_service.py`<br>`backend/app/api/exams.py`<br>`frontend/src/pages/ExamBuilder.jsx` |
| **M3** | **Exam Attempt** | Window validation, one attempt per student constraint, server-enforced countdown timer, atomic autosave of answers, manual or timer submission | `backend/app/models/attempt.py`<br>`backend/app/models/answer.py`<br>`backend/app/schemas/attempt.py`<br>`backend/app/services/attempt_service.py`<br>`backend/app/api/attempts.py`<br>`frontend/src/pages/ExamScreen.jsx` |
| **M4** | **Automated Proctoring** | Browser Page Visibility (`visibilitychange`) and Fullscreen API listener, server-side duplicate suppression (1s window), violation logging (`TAB_SWITCH`, `FULLSCREEN_EXIT`), auto-lock transition, trigger partial evaluation | `backend/app/models/violation.py`<br>`backend/app/services/attempt_service.py:on_event`<br>`backend/app/api/attempts.py`<br>`frontend/src/pages/ExamScreen.jsx` |
| **M5** | **Automated Evaluation & Results** | Idempotent comparison with answer key, full marks for correct and 0 for incorrect/blank, total score and percentage calculation, results publication, terminated violation labeling | `backend/app/models/result.py`<br>`backend/app/services/attempt_service.py:evaluate`<br>`backend/app/api/results.py`<br>`frontend/src/pages/ResultReviewPage.jsx` |
| **M6** | **Dashboards & Reporting** | Role-tailored dashboards: Student (marks & upcoming), Teacher (subject averages & violation counts), Parent (linked children only), HOD (30s auto-refresh live monitor and filtered paginated reports), Admin (user management & settings) | `backend/app/services/dashboard_service.py`<br>`backend/app/api/dashboard.py`<br>`frontend/src/pages/*Dashboard.jsx` |
| **M7** | **AI Concept Help** | Server-side Gemini API invocation for wrongly answered questions after results publication, no personal data leakage, 15s timeout, daily quota enforcement, failure retry support | `backend/app/models/ai_help.py`<br>`backend/app/services/ai_service.py`<br>`backend/app/api/ai_help.py`<br>`frontend/src/pages/ResultReviewPage.jsx` |

---

## 3. Database Schema Overview (Lab-8 ER Diagram)

The relational schema implements 15 tables strictly aligned with the Lab-8 specification:

```mermaid
erDiagram
    USER ||--o| STUDENT : "extends (user_id)"
    USER ||--o| TEACHER : "extends (user_id)"
    USER ||--o| PARENT : "extends (user_id)"
    USER ||--o| HOD : "extends (user_id)"
    
    PARENT ||--o{ STUDENT : "monitors (parent_id)"
    TEACHER ||--o{ SUBJECT : "teaches (teacher_id)"
    HOD ||--o{ SUBJECT : "oversees (hod_id)"
    
    SUBJECT ||--o{ EXAM : "has (subject_id)"
    EXAM ||--o{ QUESTION : "contains (exam_id)"
    QUESTION ||--|| ANSWER_KEY : "has key (question_id)"
    
    EXAM ||--o{ EXAM_ATTEMPT : "attempted as (exam_id)"
    STUDENT ||--o{ EXAM_ATTEMPT : "makes (student_id)"
    
    EXAM_ATTEMPT ||--o{ ANSWER : "contains (attempt_id)"
    QUESTION ||--o{ ANSWER : "answered for (question_id)"
    
    EXAM_ATTEMPT ||--o{ VIOLATION_LOG : "flags (attempt_id)"
    EXAM_ATTEMPT ||--|| RESULT : "produces (attempt_id)"
    
    STUDENT ||--o{ AI_HELP_REQUEST : "asks (student_id)"
    QUESTION ||--o{ AI_HELP_REQUEST : "targets (question_id)"
```

---

## 4. Proctoring & Automated Evaluation Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Browser as React Frontend
    participant API as FastAPI Backend
    participant DB as PostgreSQL / DB
    participant Gemini as Google AI Studio

    Student->>Browser: Opens Exam (Clicks Enter Fullscreen)
    Browser->>API: POST /attempts?exam_id=X
    API->>DB: Check window & create attempt (In Progress)
    API-->>Browser: Attempt created & questions paper returned
    
    loop During Assessment
        Student->>Browser: Selects Option
        Browser->>API: PUT /attempts/{id}/answers (Autosave)
        API->>DB: Upsert Answer row
    end

    alt Tab Switch or Fullscreen Exit Detected
        Browser->>API: POST /attempts/{id}/events (TAB_SWITCH)
        API->>DB: Write VIOLATION_LOG, set flagged=true, status=Auto-Locked
        API->>DB: Trigger evaluate(attempt_id) on saved partial answers
        API-->>Browser: { locked: true, status: 'Auto-Locked' }
        Browser->>Student: Display Auto-Locked Red Warning Modal
    else Normal Submission
        Student->>Browser: Clicks Submit (or Timer reaches 0)
        Browser->>API: POST /attempts/{id}/submit
        API->>DB: Mark status=Submitted, submit_at=now
        API->>DB: Trigger evaluate(attempt_id)
        API-->>Browser: Submission confirmed
    end

    opt Student Requests Concept Remediation (Wrong Question)
        Student->>Browser: Clicks "Ask AI (Concept Help)"
        Browser->>API: POST /ai-help { attempt_id, question_id }
        API->>DB: Verify wrong answer, result published, check daily limit
        API->>Gemini: POST Prompt (Question + Option Selected + Correct Answer)
        Gemini-->>API: Plain-language concept explanation (15s timeout)
        API->>DB: Write AI_HELP_REQUEST log
        API-->>Browser: Return explanation to student
    end
```
