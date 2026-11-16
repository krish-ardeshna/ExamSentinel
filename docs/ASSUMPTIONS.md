# Assumptions & Design Decisions

This document details the engineering assumptions and design choices made during the implementation of the **Online Exam Proctoring & Management System (OEPMS)**, derived from `Software_Engineering_Lab_Report_BCS522.pdf` and `OEPMS_Unit_Testing_Experiment.docx`.

---

## 1. Precedence Rule
- **Validation Rules & Error Messages**: As instructed in the system specification, whenever a minor conflict arose between the Lab Report narrative and the Unit Testing Experiment document, **the Unit Testing document took absolute precedence** for exact validation rules, boundary conditions, and exact string error formats (e.g. `<field>: <rule>`).
- **Database Schema & Relational Workflows**: The Lab-8 ER diagram and table specifications took precedence for entity definitions, primary keys, foreign keys, and cardinalities.

---

## 2. Field Validations & Assumed Range Constraints
1. **Exam Duration (`duration_min`)**: Assumed to be an integer between 1 and 180 minutes inclusive, matching test case `UT_EXM_13` through `UT_EXM_15`.
2. **Exam Total Marks (`total_marks`)**: Assumed to be an integer between 1 and 100 inclusive, matching test cases `UT_EXM_16` through `UT_EXM_18`.
3. **Exam Status Lifecyle**: Valid statuses are `Draft`, `Published`, and `Completed`, as specified in `UT_EXM_19` through `UT_EXM_21`.
4. **Attempt Status Lifecycle**: Valid statuses are `In Progress`, `Submitted`, and `Auto-Locked`, matching `UT_ATT_13` through `UT_ATT_15`.
5. **User Roles**: The five recognized human roles are `Admin`, `Teacher`, `Student`, `Parent`, and `HOD`. Proctoring and auto-evaluation are automated backend processes inside the system boundary, not human actor roles.
6. **User Status**: Accounts may be `Active` or `Suspended`. Only `Active` users are permitted to authenticate.
7. **Password Complexity**: 8-20 characters with at least one uppercase letter, one lowercase letter, one decimal digit, and one special character, with no whitespace permitted (`UT_USR_09` through `UT_USR_12`). Passwords are never stored in plaintext and are salted using bcrypt.

---

## 3. Proctoring & Locking Policies (M4)
1. **Zero-Tolerance Single-Violation Lock**: As stated in UC-SYS1 and UT-ATT-19/20, the violation policy specifies that **one violation leads to an immediate lock**. A student switching tabs or exiting full-screen mode causes the attempt to transition to `Auto-Locked` and `flagged = true`.
2. **Duplicate Event Window**: Events of the same violation type occurring within **1 second** of each other are merged/suppressed to prevent duplicate noise from browser event cascades.
3. **Late Event Discarding**: Events sent for attempts that are not currently `In Progress` (such as already submitted or previously locked attempts) are safely ignored without altering state (`UT_ATT_21`).
4. **Partial Evaluation on Lock**: When an attempt is auto-locked due to a violation, the answers recorded up to that second are preserved and immediately auto-evaluated. In dashboards and reports, the attempt outcome is labeled with **"Terminated (violation)"** (`UT_ATT_23`).

---

## 4. Evaluation & Results (M5)
1. **Strict Binary Scoring for MCQs**: For each question, an answer exactly matching the official answer key receives full question marks; wrong options or unattempted/blank questions receive 0 marks.
2. **Idempotency**: Multiple calls to `evaluate(attempt_id)` do not create duplicate `Result` records or alter scores (`UT_ATT_24`).
3. **Question Paper Immutability**: Teachers cannot edit or alter questions once the exam's `start_time` has elapsed (`UT_EXM_24`).

---

## 5. AI Concept Help (M7)
1. **Remediation Eligibility**: AI concept assistance is strictly gated to questions that were **answered incorrectly** by the student and only **after results have been published** (`UC-S3`, `UC-AI1`).
2. **Privacy & Data Protection**: Prompts constructed for the Google Gemini API contain only the question text, student's selected answer, and correct option. **No student names, user IDs, or personal identification data are ever transmitted to the AI API.**
3. **Security**: The `GEMINI_API_KEY` is kept strictly server-side in the backend environment and is never exposed or transmitted to client browsers.
4. **Resilience & Timeouts**: Calls to the Google AI Studio API have an enforced **15-second timeout**. If the API fails or times out, a clean retry prompt is returned to the user without crashing the application.
5. **Daily Quotas**: A student's requests are constrained by a configurable daily limit (default 10 questions/day), adjustable by the Administrator in Platform Settings.

---

## 6. Multi-Tenant Role Isolation (M6)
1. **Parent Privacy**: Parents have visibility only into the academic schedules, marks, and history of students explicitly linked via `parent_id` in the `STUDENT` entity.
2. **Teacher Privacy**: Teachers can only view, edit, schedule, and grade exams belonging to `Subject` records where `teacher_id` matches their own faculty profile.
3. **Admin Safety Guard**: The last remaining Administrator account cannot be deleted (`UT_USR_24`). Students currently in an active `In Progress` exam attempt cannot be deleted (`UT_USR_23`).
