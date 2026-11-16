# Online Exam Proctoring & Management System (OEPMS)

> A full-lifecycle, production-ready online examination platform featuring automated browser-level screen proctoring, server-enforced timer and autosave, automated grading against official answer keys, role-based dashboards, and Google Gemini AI-powered concept remediation.

---

## 1. System Overview

OEPMS replaces fragmented manual workflows (shared documents, video invigilation, manual mark spreadsheets) with an integrated web platform:
- **Teachers** schedule exams for assigned subjects, author MCQs with custom weights, submit hidden answer keys, and publish.
- **Students** enter fullscreen mode, take assessments within strictly enforced time windows, receive real-time answer autosaving, and view evaluation reports.
- **Automated Proctoring (M4)** continuously monitors screen visibility and fullscreen state via HTML5 Web APIs. Any tab switch or fullscreen exit automatically logs a violation, flags the attempt, and locks the exam immediately with partial answers saved and graded as *"Terminated (violation)"*.
- **Automated Evaluation (M5)** compares answers with official answer keys instantaneously upon submission or violation lock, producing idempotent score reports.
- **AI Concept Help (M7)** allows students to request plain-language conceptual explanations from Google Gemini 1.5 Flash for wrongly answered questions without transmitting any personal student data.
- **Role-Based Portals (M6)** provide dedicated interfaces for Student, Teacher, Parent (linked children only), HOD (30s auto-refresh live monitor and filtered reports), and Admin (user lifecycle governance and platform parameters).

---

## 2. Technology Stack

- **Frontend**: React 18, Vite, React Router v6, Lucide Icons, Fullscreen API, Page Visibility API
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0 ORM, Alembic migrations, Pydantic v2
- **Database**: PostgreSQL 16 (production), SQLite in-memory (automated testing)
- **Security**: JWT role-embedded bearer tokens, bcrypt password hashing, 5-strike 15-minute account lockouts
- **AI Integration**: Google AI Studio (Gemini 1.5 Flash API), server-side only with 15s timeout
- **Testing**: pytest (72 unit tests across UT-USR, UT-EXM, UT-ATT), Vitest + React Testing Library

---

## 3. Demo Accounts & Seed Credentials

The database is pre-seeded with all roles, linked parent-student relationships, subjects, and published exams. You can also use the **Quick Demo Autofill buttons** on the login page:

| Role | Name | Email | Password | Description / Linkage |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | System Admin | `admin@oepms.edu` | `Admin@1234` | Full user management and platform config |
| **HOD** | Dr. Nagresh Kumar | `hod@oepms.edu` | `Hod@12345` | Real-time live monitor and department reports |
| **Teacher 1**| Prof. Rajesh Sharma | `rajesh.teacher@oepms.edu` | `Teach@1234` | Teaches CS501 (Data Structures), CS502 (DBMS) |
| **Teacher 2**| Dr. Sunita Verma | `sunita.teacher@oepms.edu` | `Teach@1234` | Teaches CS503 (Software Engineering) |
| **Student 1**| Riya Sharma | `riya.student@oepms.edu` | `Stud@1234` | Sem 5 (CSE2024001) - High score demo result |
| **Student 2**| Aman Sharma | `aman.student@oepms.edu` | `Stud@1234` | Sem 5 (CSE2024002) - Auto-Locked violation demo |
| **Student 3**| Rohit Gupta | `rohit.student@oepms.edu` | `Stud@1234` | Sem 5 (CSE2024003) - Completed Exam 2 attempt |
| **Student 4**| Sneha Gupta | `sneha.student@oepms.edu` | `Stud@1234` | Sem 5 (CSE2024004) - Active student |
| **Student 5**| Vikram Singh | `vikram.student@oepms.edu` | `Stud@1234` | Sem 5 (CSE2024005) - Active student |
| **Parent 1** | Mr. Suresh Sharma | `suresh.parent@oepms.edu` | `Parent@123` | Linked to Riya Sharma & Aman Sharma |
| **Parent 2** | Mrs. Anita Gupta | `anita.parent@oepms.edu` | `Parent@123` | Linked to Rohit Gupta & Sneha Gupta |

---

## 4. Quickstart with Docker Compose

Ensure Docker and Docker Compose are installed and running.

1. Clone or navigate to the project directory:
   ```bash
   cd oepms
   ```

2. Copy the environment variables:
   ```bash
   cp .env.example .env
   ```
   *(Optional: Add your `GEMINI_API_KEY` in `.env` to enable live Google Gemini calls; fallback mock explanations are provided automatically if omitted).*

3. Build and launch all services:
   ```bash
   docker-compose up --build
   ```

4. Access the applications:
   - **Frontend Web Portal**: [http://localhost:5173](http://localhost:5173)
   - **Backend REST API**: [http://localhost:8000](http://localhost:8000)
   - **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **PostgreSQL Database**: `localhost:5433`

---

## 5. Local Development (Without Docker)

### Backend Setup:
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

---

## 6. Running the 72 Unit Test Suite (Lab-9 / UT-USR, UT-EXM, UT-ATT)

All 72 test cases defined in `OEPMS_Unit_Testing_Experiment.docx` are implemented with exact identifiers and strict error message matching.

To run the automated test runner and generate the results CSV:
```bash
cd backend
python scripts/run_unit_tests.py
```

### Execution Output:
```text
============================================================
OEPMS UNIT TESTING EXECUTION SUMMARY
Total Test Cases Executed: 72/72
Passed: 72
Failed: 0
CSV Report written to: docs/unit_test_results.csv
============================================================
```

The generated CSV file `docs/unit_test_results.csv` contains:
```csv
ID,Test Date,Result (Pass/Fail)
UT_ATT_01,16/11/2026,Pass
UT_ATT_02,16/11/2026,Pass
...
UT_USR_24,16/11/2026,Pass
```

---

## 7. Interactive OpenAPI Specification

- OpenAPI schema is exported to: `docs/oepms_openapi.json`
- Live interactive Swagger UI available at: `http://localhost:8000/docs`
- ReDoc documentation available at: `http://localhost:8000/redoc`

---

## 8. Frontend Screenshots & UI Walkthrough

1. **Login Portal (`/login`)**:
   - Clean card-based login with role indicator and 1-click demo account switcher.
2. **Student Dashboard (`/dashboard/student`)**:
   - Displays student enrollment, active exams available to take, and past examination scores.
3. **Proctored Exam Gate & Screen (`/exam/:attemptId`)**:
   - Fullscreen gate modal with strict anti-cheat policy warnings.
   - Server-synchronized countdown clock.
   - Question palette with answered/unanswered color codes.
   - Real-time autosave status indicator.
   - **Auto-Locked Alert Overlay**: High-visibility warning displayed instantly if student switches tabs or exits fullscreen.
4. **Results & AI Concept Remediation (`/results/:attemptId`)**:
   - Full question breakdown showing student's answer vs official correct answer.
   - High-contrast "Ask AI (Concept Help)" button on wrongly answered questions.
   - AI modal presenting plain-language remediation with retry capability.
5. **Teacher Dashboard & Paper Builder (`/dashboard/teacher`, `/teacher/exam/new`)**:
   - Subject-wise performance metrics, exam creation form, MCQ question builder, and answer key submitter.
6. **Parent Performance Portal (`/dashboard/parent`)**:
   - Ward selector and report card showing marks and proctoring status for linked children.
7. **HOD Live Monitor & Department Analytics (`/dashboard/hod`)**:
   - Auto-refreshing live dashboard (30s) displaying in-progress, submitted, and locked counts.
   - Live violation event stream.
   - Paginated historical reports with semester, subject, and date range filters.
8. **Admin Control Console (`/dashboard/admin`)**:
   - User CRUD, account suspension/activation, and platform parameters (Daily AI Limit).
