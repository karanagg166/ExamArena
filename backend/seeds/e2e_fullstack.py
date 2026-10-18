"""Full-stack E2E test database fixture seeder.

Creates deterministic School, Class, Teacher, 2 Class Students, 1 Outsider Student,
and an Exam with MCQ + Subjective questions for unmocked Playwright tests.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Exam,
    ExamType,
    Question,
    QuestionOption,
    QuestionType,
    Role,
    School,
    SchoolClass,
    Student,
    Subject,
    Teacher,
    TeacherClass,
    User,
)
from app.core.security import hash_password

E2E_PASSWORD_HASH = hash_password("Password123!")


async def seed_fullstack_e2e_fixtures(session: AsyncSession) -> dict[str, str]:
    """Idempotently seed the database with synthetic users and exam for real E2E lifecycle testing."""
    now = datetime.now(UTC)

    # 1. Clean existing E2E seed records if any
    e2e_emails = [
        "teacher.e2e@examarena.dev",
        "student1.e2e@examarena.dev",
        "student2.e2e@examarena.dev",
        "outsider.e2e@examarena.dev",
        "principal.e2e@examarena.dev",
    ]
    existing_users = (
        await session.execute(select(User).where(User.email.in_(e2e_emails)))
    ).scalars().all()
    user_ids = [u.id for u in existing_users]
    if user_ids:
        # Cascade through deletes
        await session.execute(delete(Exam).where(Exam.name == "E2E Mastery Certification"))
        await session.execute(delete(Student).where(Student.userId.in_(user_ids)))
        await session.execute(delete(Teacher).where(Teacher.userId.in_(user_ids)))
        await session.execute(delete(SchoolClass).where(SchoolClass.joinCode.in_(["APEX10A", "OUTSIDER1"])))
        await session.execute(delete(School).where(School.schoolCode.in_(["SCH-E2E-APEX", "SCH-E2E-OUT"])))
        await session.execute(delete(User).where(User.id.in_(user_ids)))
        await session.commit()

    # 2. Create Principal & School
    principal_user = User(
        name="Principal Apex",
        email="principal.e2e@examarena.dev",
        password=E2E_PASSWORD_HASH,
        phoneNo="+919800000001",
        role=Role.PRINCIPAL,
        dateOfBirth=datetime(1980, 1, 1, tzinfo=UTC),
        city="Bengaluru",
        state="Karnataka",
        country="India",
        pincode="560001",
    )
    session.add(principal_user)
    await session.flush()

    school = School(
        name="Apex E2E Academy",
        schoolCode="SCH-E2E-APEX",
        createdBy=principal_user.id,
        address="100 Test Avenue",
        city="Bengaluru",
        state="Karnataka",
        country="India",
        pincode="560001",
    )
    session.add(school)
    await session.flush()

    # 3. Create Class: Grade 10-A
    school_class = SchoolClass(
        name="Grade 10-A",
        year="2026",
        section="A",
        schoolId=school.id,
        joinCode="APEX10A",
        nextRollNo=10,
    )
    session.add(school_class)
    await session.flush()

    # 4. Create Teacher
    teacher_user = User(
        name="Prof. FullStack",
        email="teacher.e2e@examarena.dev",
        password=E2E_PASSWORD_HASH,
        phoneNo="+919800000002",
        role=Role.TEACHER,
        dateOfBirth=datetime(1985, 5, 12, tzinfo=UTC),
        city="Bengaluru",
        state="Karnataka",
        country="India",
        pincode="560001",
    )
    session.add(teacher_user)
    await session.flush()

    teacher = Teacher(
        userId=teacher_user.id,
        schoolId=school.id,
        experience=8,
        department="Computer Science",
        qualification='["M.Tech Computer Science"]',
        subjects='["SCIENCE"]',
    )
    session.add(teacher)
    await session.flush()

    # Associate Teacher with Class
    tc = TeacherClass(
        teacherId=teacher.id,
        classId=school_class.id,
        subject=Subject.SCIENCE,
    )
    session.add(tc)

    # 5. Create Students in Class 10-A
    student1_user = User(
        name="Student Alice",
        email="student1.e2e@examarena.dev",
        password=E2E_PASSWORD_HASH,
        phoneNo="+919800000003",
        role=Role.STUDENT,
        dateOfBirth=datetime(2008, 3, 15, tzinfo=UTC),
        city="Bengaluru",
        state="Karnataka",
        country="India",
        pincode="560001",
    )
    student2_user = User(
        name="Student Bob",
        email="student2.e2e@examarena.dev",
        password=E2E_PASSWORD_HASH,
        phoneNo="+919800000004",
        role=Role.STUDENT,
        dateOfBirth=datetime(2008, 7, 20, tzinfo=UTC),
        city="Bengaluru",
        state="Karnataka",
        country="India",
        pincode="560001",
    )
    session.add_all([student1_user, student2_user])
    await session.flush()

    student1 = Student(
        userId=student1_user.id,
        schoolId=school.id,
        classId=school_class.id,
        rollNo="1",
        parentName="Alice Parent",
        parentEmail="parent.alice@examarena.dev",
        dateOfAdmission=now,
    )
    student2 = Student(
        userId=student2_user.id,
        schoolId=school.id,
        classId=school_class.id,
        rollNo="2",
        parentName="Bob Parent",
        parentEmail="parent.bob@examarena.dev",
        dateOfAdmission=now,
    )
    session.add_all([student1, student2])
    await session.flush()

    # 6. Create Outsider Student in a different school
    outsider_school = School(
        name="Outsider Secondary School",
        schoolCode="SCH-E2E-OUT",
        createdBy=principal_user.id,
        address="200 Other Road",
        city="Mumbai",
        state="Maharashtra",
        country="India",
        pincode="400001",
    )
    session.add(outsider_school)
    await session.flush()

    outsider_class = SchoolClass(
        name="Grade 11-B",
        year="2026",
        section="B",
        schoolId=outsider_school.id,
        joinCode="OUTSIDER1",
        nextRollNo=5,
    )
    session.add(outsider_class)
    await session.flush()

    outsider_user = User(
        name="Student Charlie (Outsider)",
        email="outsider.e2e@examarena.dev",
        password=E2E_PASSWORD_HASH,
        phoneNo="+919800000005",
        role=Role.STUDENT,
        dateOfBirth=datetime(2007, 11, 5, tzinfo=UTC),
        city="Mumbai",
        state="Maharashtra",
        country="India",
        pincode="400001",
    )
    session.add(outsider_user)
    await session.flush()

    outsider_student = Student(
        userId=outsider_user.id,
        schoolId=outsider_school.id,
        classId=outsider_class.id,
        rollNo="101",
        parentName="Charlie Parent",
        parentEmail="parent.charlie@examarena.dev",
        dateOfAdmission=now,
    )
    session.add(outsider_student)
    await session.flush()

    # 7. Create Exam: E2E Mastery Certification
    exam = Exam(
        name="E2E Mastery Certification",
        description="Comprehensive full-stack verification exam with MCQ and subjective questions.",
        scheduledAt=now - timedelta(hours=1),  # Already active
        duration=60,
        maxMarks=10,
        isPublished=True,
        isPublic=False,
        isResultsReleased=False,
        negativeMarking=False,
        type=ExamType.FINAL,
        subject=Subject.SCIENCE,
        teacherId=teacher.id,
        examCode="E2E-MASTERY-101",
        accessPassword=hash_password("E2E-MASTERY-101"),
    )
    session.add(exam)
    await session.flush()

    # 8. Questions
    # Q1: MCQ (5 marks)
    q1 = Question(
        examId=exam.id,
        questionNumber=1,
        text="What is the average time complexity of quickselect?",
        marks=5.0,
        questionType=QuestionType.MULTIPLE_CHOICE,
        explanation="Quickselect partitions the array in O(n) expected time using divide-and-conquer.",
    )
    session.add(q1)
    await session.flush()

    opt1 = QuestionOption(questionId=q1.id, optionNumber=1, text="O(n^2)", isCorrect=False)
    opt2 = QuestionOption(questionId=q1.id, optionNumber=2, text="O(n)", isCorrect=True)
    opt3 = QuestionOption(questionId=q1.id, optionNumber=3, text="O(log n)", isCorrect=False)
    session.add_all([opt1, opt2, opt3])

    # Q2: Short Answer (5 marks) with reference answer and rubric
    q2 = Question(
        examId=exam.id,
        questionNumber=2,
        text="Explain ACID properties in relational database management systems.",
        marks=5.0,
        questionType=QuestionType.SHORT_ANSWER,
        referenceAnswer="Atomicity guarantees all or nothing transactions. Consistency ensures state invariants. Isolation keeps concurrent operations separate. Durability guarantees committed transactions survive failures.",
        gradingRubric=[
            {
                "criterion": "Mentions Atomicity, Consistency, Isolation, and Durability with accurate definitions.",
                "maxMarks": 5.0,
            }
        ],
        explanation="ACID stands for Atomicity, Consistency, Isolation, and Durability.",
    )
    session.add(q2)
    await session.commit()

    print("✅ Seeded Full-Stack E2E Fixtures successfully!", flush=True)
    return {
        "examId": exam.id,
        "schoolId": school.id,
        "classId": school_class.id,
        "teacherUserId": teacher_user.id,
        "student1UserId": student1_user.id,
        "student2UserId": student2_user.id,
        "outsiderUserId": outsider_user.id,
    }
