"""Database seeder for OEPMS.

Creates:
- 1 Admin
- 1 HOD
- 2 Teachers
- 5 Students
- 2 Parents (linked to students)
- 3 Subjects
- 2 Published Exams with questions and answer keys
- Sample attempts, including 1 locked attempt with a violation, and results
"""

import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
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
from app.models.settings import PlatformSetting


def seed_database():
    """Populate database with demo accounts and data."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "admin@oepms.edu").first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding OEPMS database...")

        # 1. Platform Settings
        db.add(PlatformSetting(key="AI_HELP_DAILY_LIMIT", value="10"))
        db.add(PlatformSetting(key="MAX_EXAM_DURATION_MIN", value="180"))
        db.add(PlatformSetting(key="SESSION_TIMEOUT_MIN", value="60"))
        db.flush()

        # 2. Admin (1)
        admin = User(
            name="System Admin",
            email="admin@oepms.edu",
            password_hash=hash_password("Admin@1234"),
            role="Admin",
            status="Active",
        )
        db.add(admin)
        db.flush()

        # 3. HOD (1)
        hod_user = User(
            name="Dr. Nagresh Kumar",
            email="hod@oepms.edu",
            password_hash=hash_password("Hod@12345"),
            role="HOD",
            status="Active",
        )
        db.add(hod_user)
        db.flush()
        hod = HOD(user_id=hod_user.user_id, department="Computer Science & Engineering")
        db.add(hod)
        db.flush()

        # 4. Teachers (2)
        t1_user = User(
            name="Prof. Rajesh Sharma",
            email="rajesh.teacher@oepms.edu",
            password_hash=hash_password("Teach@1234"),
            role="Teacher",
            status="Active",
        )
        t2_user = User(
            name="Dr. Sunita Verma",
            email="sunita.teacher@oepms.edu",
            password_hash=hash_password("Teach@1234"),
            role="Teacher",
            status="Active",
        )
        db.add_all([t1_user, t2_user])
        db.flush()

        t1 = Teacher(user_id=t1_user.user_id, department="CSE", designation="Associate Professor")
        t2 = Teacher(user_id=t2_user.user_id, department="CSE", designation="Assistant Professor")
        db.add_all([t1, t2])
        db.flush()

        # 5. Parents (2)
        p1_user = User(
            name="Mr. Suresh Sharma",
            email="suresh.parent@oepms.edu",
            password_hash=hash_password("Parent@123"),
            role="Parent",
            status="Active",
        )
        p2_user = User(
            name="Mrs. Anita Gupta",
            email="anita.parent@oepms.edu",
            password_hash=hash_password("Parent@123"),
            role="Parent",
            status="Active",
        )
        db.add_all([p1_user, p2_user])
        db.flush()

        p1 = Parent(user_id=p1_user.user_id, phone="9876543210")
        p2 = Parent(user_id=p2_user.user_id, phone="9876543211")
        db.add_all([p1, p2])
        db.flush()

        # 6. Students (5)
        # s1 and s2 linked to p1; s3, s4 linked to p2; s5 standalone
        student_configs = [
            ("Riya Sharma", "riya.student@oepms.edu", "Stud@1234", p1.parent_id, "CSE2024001", "B.Tech CSE", 5),
            ("Aman Sharma", "aman.student@oepms.edu", "Stud@1234", p1.parent_id, "CSE2024002", "B.Tech CSE", 5),
            ("Rohit Gupta", "rohit.student@oepms.edu", "Stud@1234", p2.parent_id, "CSE2024003", "B.Tech CSE", 5),
            ("Sneha Gupta", "sneha.student@oepms.edu", "Stud@1234", p2.parent_id, "CSE2024004", "B.Tech CSE", 5),
            ("Vikram Singh", "vikram.student@oepms.edu", "Stud@1234", None, "CSE2024005", "B.Tech CSE", 5),
        ]
        students = []
        for name, email, pwd, parent_id, enr, prog, sem in student_configs:
            u = User(
                name=name,
                email=email,
                password_hash=hash_password(pwd),
                role="Student",
                status="Active",
            )
            db.add(u)
            db.flush()
            st = Student(
                user_id=u.user_id,
                parent_id=parent_id,
                enrollment_no=enr,
                program=prog,
                semester=sem,
            )
            db.add(st)
            students.append(st)
        db.flush()

        # 7. Subjects (3)
        sub1 = Subject(
            teacher_id=t1.teacher_id,
            hod_id=hod.hod_id,
            code="CS501",
            name="Data Structures and Algorithms",
            semester=5,
        )
        sub2 = Subject(
            teacher_id=t1.teacher_id,
            hod_id=hod.hod_id,
            code="CS502",
            name="Database Management Systems",
            semester=5,
        )
        sub3 = Subject(
            teacher_id=t2.teacher_id,
            hod_id=hod.hod_id,
            code="CS503",
            name="Software Engineering",
            semester=5,
        )
        db.add_all([sub1, sub2, sub3])
        db.flush()

        # 8. Exams (2 Published Exams)
        now = datetime.now(timezone.utc)
        # Exam 1: Data Structures Unit Test (active window covering today)
        ex1 = Exam(
            subject_id=sub1.subject_id,
            title="Data Structures Unit Test 1",
            start_time=now - timedelta(hours=2),
            end_time=now + timedelta(days=2),
            duration_min=60,
            total_marks=10,
            status="Published",
        )
        # Exam 2: Software Engineering Mid-Term
        ex2 = Exam(
            subject_id=sub3.subject_id,
            title="Software Engineering Mid-Term Exam",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(days=3),
            duration_min=90,
            total_marks=10,
            status="Published",
        )
        db.add_all([ex1, ex2])
        db.flush()

        # 9. Questions & Answer Keys for Exam 1 (10 MCQs = 10 marks)
        ex1_questions = [
            ("What is the time complexity of searching an element in a balanced Binary Search Tree?", {"A": "O(1)", "B": "O(log n)", "C": "O(n)", "D": "O(n log n)"}, "B"),
            ("Which data structure operates on a Last In First Out (LIFO) basis?", {"A": "Queue", "B": "Array", "C": "Stack", "D": "Linked List"}, "C"),
            ("Which sorting algorithm has the best average-case performance?", {"A": "Bubble Sort", "B": "Insertion Sort", "C": "Quick Sort", "D": "Selection Sort"}, "C"),
            ("What data structure is typically used for Breadth-First Search (BFS) in a graph?", {"A": "Stack", "B": "Queue", "C": "Priority Queue", "D": "Hash Map"}, "B"),
            ("In a singly linked list, what is the time complexity to insert a node at the beginning?", {"A": "O(1)", "B": "O(n)", "C": "O(log n)", "D": "O(n^2)"}, "A"),
            ("Which collision resolution technique uses linked lists in hash tables?", {"A": "Linear Probing", "B": "Quadratic Probing", "C": "Chaining", "D": "Double Hashing"}, "C"),
            ("What is the minimum number of queues needed to implement a stack?", {"A": "1", "B": "2", "C": "3", "D": "4"}, "B"),
            ("A max-heap guarantees that:", {"A": "Root is smallest", "B": "Root is largest", "C": "Tree is perfectly balanced", "D": "All leaves are equal"}, "B"),
            ("What is the worst-case time complexity of Quick Sort?", {"A": "O(n log n)", "B": "O(n)", "C": "O(n^2)", "D": "O(log n)"}, "C"),
            ("Which traversal of a binary search tree visits nodes in ascending order?", {"A": "Pre-order", "B": "In-order", "C": "Post-order", "D": "Level-order"}, "B"),
        ]

        for text, opts, correct in ex1_questions:
            q = Question(exam_id=ex1.exam_id, text=text, options=opts, marks=1)
            db.add(q)
            db.flush()
            ak = AnswerKey(question_id=q.question_id, correct_option=correct)
            db.add(ak)
        db.flush()

        # Questions for Exam 2 (10 MCQs = 10 marks)
        ex2_questions = [
            ("Which software life cycle model is most suitable when requirements are well understood upfront?", {"A": "Waterfall Model", "B": "Spiral Model", "C": "Agile Scrum", "D": "RAD Model"}, "A"),
            ("What does the acronym 'SOLID' stand for in software design principles?", {"A": "Five design principles for OOP", "B": "Database normalization", "C": "Unit testing standard", "D": "Deployment model"}, "A"),
            ("Which testing technique checks internal logic and code structure?", {"A": "Black box testing", "B": "White box testing", "C": "Alpha testing", "D": "Beta testing"}, "B"),
            ("In Agile development, what is a Sprint?", {"A": "A bug fixing session", "B": "A timeboxed iteration (1-4 weeks)", "C": "A client meeting", "D": "Final deployment phase"}, "B"),
            ("Which diagram models the static structure of a system in UML?", {"A": "Sequence Diagram", "B": "Activity Diagram", "C": "Class Diagram", "D": "Statechart Diagram"}, "C"),
            ("What is coupling in software engineering?", {"A": "Degree of interdependence between modules", "B": "Strength of elements within a module", "C": "Code execution speed", "D": "Data security level"}, "A"),
            ("High cohesion and low coupling is a hallmark of:", {"A": "Fragile architecture", "B": "Good software design", "C": "Spaghetti code", "D": "Monolithic failure"}, "B"),
            ("Which git command creates a new isolated line of development?", {"A": "git commit", "B": "git merge", "C": "git branch", "D": "git push"}, "C"),
            ("Regression testing ensures that:", {"A": "New changes did not break existing features", "B": "The database is backed up", "C": "System handles high load", "D": "Documentation is complete"}, "A"),
            ("What is the primary objective of software refactoring?", {"A": "Add new features", "B": "Improve internal code structure without changing behavior", "C": "Fix compiler errors", "D": "Increase code size"}, "B"),
        ]

        for text, opts, correct in ex2_questions:
            q = Question(exam_id=ex2.exam_id, text=text, options=opts, marks=1)
            db.add(q)
            db.flush()
            ak = AnswerKey(question_id=q.question_id, correct_option=correct)
            db.add(ak)
        db.flush()

        # 10. Sample Attempts and Results
        # Student 1 (Riya): Completed attempt on Exam 1 with high score (9/10 = 90%)
        att1 = ExamAttempt(
            exam_id=ex1.exam_id,
            student_id=students[0].student_id,
            start_at=now - timedelta(hours=1),
            submit_at=now - timedelta(minutes=15),
            status="Submitted",
            flagged=False,
        )
        db.add(att1)
        db.flush()

        # Answers for att1
        q_ex1 = db.query(Question).filter(Question.exam_id == ex1.exam_id).all()
        for idx, q in enumerate(q_ex1):
            key = db.query(AnswerKey).filter(AnswerKey.question_id == q.question_id).first()
            # Give 9 correct, 1 wrong (question 2)
            selected = key.correct_option if idx != 1 else "A"
            is_corr = (selected == key.correct_option)
            ans = Answer(
                attempt_id=att1.attempt_id,
                question_id=q.question_id,
                selected_option=selected,
                is_correct=is_corr,
            )
            db.add(ans)

        res1 = Result(
            attempt_id=att1.attempt_id,
            score=9.0,
            percentage=90.0,
            published_at=now - timedelta(minutes=14),
        )
        db.add(res1)
        db.flush()

        # Student 2 (Aman): Locked attempt due to Tab Switch violation!
        att2 = ExamAttempt(
            exam_id=ex1.exam_id,
            student_id=students[1].student_id,
            start_at=now - timedelta(minutes=40),
            submit_at=now - timedelta(minutes=25),
            status="Auto-Locked",
            flagged=True,
        )
        db.add(att2)
        db.flush()

        # Violation log for att2
        v_log = ViolationLog(
            attempt_id=att2.attempt_id,
            type="TAB_SWITCH",
            occurred_at=now - timedelta(minutes=25),
        )
        db.add(v_log)

        # 4 answers saved before lock (3 correct, 1 wrong)
        for idx in range(4):
            q = q_ex1[idx]
            key = db.query(AnswerKey).filter(AnswerKey.question_id == q.question_id).first()
            selected = key.correct_option if idx < 3 else "D"
            ans = Answer(
                attempt_id=att2.attempt_id,
                question_id=q.question_id,
                selected_option=selected,
                is_correct=(selected == key.correct_option),
            )
            db.add(ans)

        res2 = Result(
            attempt_id=att2.attempt_id,
            score=3.0,
            percentage=30.0,
            published_at=now - timedelta(minutes=24),
        )
        db.add(res2)
        db.flush()

        # Student 3 (Rohit): Completed attempt on Exam 2 (8/10 = 80%)
        att3 = ExamAttempt(
            exam_id=ex2.exam_id,
            student_id=students[2].student_id,
            start_at=now - timedelta(minutes=50),
            submit_at=now - timedelta(minutes=10),
            status="Submitted",
            flagged=False,
        )
        db.add(att3)
        db.flush()

        q_ex2 = db.query(Question).filter(Question.exam_id == ex2.exam_id).all()
        for idx, q in enumerate(q_ex2):
            key = db.query(AnswerKey).filter(AnswerKey.question_id == q.question_id).first()
            selected = key.correct_option if idx not in [2, 5] else "C"
            ans = Answer(
                attempt_id=att3.attempt_id,
                question_id=q.question_id,
                selected_option=selected,
                is_correct=(selected == key.correct_option),
            )
            db.add(ans)

        res3 = Result(
            attempt_id=att3.attempt_id,
            score=8.0,
            percentage=80.0,
            published_at=now - timedelta(minutes=9),
        )
        db.add(res3)
        db.flush()

        db.commit()
        print("Database seeded successfully with all roles, subjects, exams, and demo attempts!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
