"""Seeds package orchestrator for ExamArena database initialization."""

from sqlalchemy.ext.asyncio import AsyncSession

from seeds.attempts import seed_student_attempts
from seeds.exams import seed_exams
from seeds.notifications import seed_notifications
from seeds.schools import seed_classes, seed_school, seed_school_memberships
from seeds.users import seed_admin, seed_principal, seed_students, seed_teachers


async def run_all_seeds(session: AsyncSession) -> None:
    """Execute complete realistic database seeding routine across all sub-modules."""
    print("==================================================", flush=True)
    print("🚀 Starting ExamArena Realistic Data Seeding...", flush=True)
    print("==================================================", flush=True)

    # 1. Admin User
    admin_user = await seed_admin(session)

    # 2. School
    school = await seed_school(session, admin_user)

    # 3. Principal
    principal_user, _, _ = await seed_principal(session, school)

    # 4. Teachers
    teachers_map = await seed_teachers(session, school)

    # 5. Classes
    classes_map = await seed_classes(session, school, teachers_map)

    # 6. Students
    students_map = await seed_students(session, school, classes_map)

    # 7. Memberships & Enrollments (TeacherSchool, TeacherClass, ClassJoinRequest)
    await seed_school_memberships(
        session, school, principal_user, teachers_map, classes_map, students_map
    )

    # 8. Exams, Sections & Questions
    exams_map = await seed_exams(session, teachers_map)

    # 9. Realistic Student Attempts & Grading
    await seed_student_attempts(session, exams_map, students_map)

    # 10. Contextual Notifications
    await seed_notifications(session, principal_user, teachers_map, students_map)

    print("==================================================", flush=True)
    print("✨ Realistic Seeding Completed Successfully!", flush=True)
    print("==================================================", flush=True)
    print("\n🔑 Ready Test Credentials (Password for all: karan166):", flush=True)
    print(
        "  👨‍🎓 Student:   student@gmail.com        (Alex Morgan - Class 10A)",
        flush=True,
    )
    print(
        "  👩‍🎓 Student:   emma.student@gmail.com   (Emma Watson - Class 10A)",
        flush=True,
    )
    print(
        "  👨‍🎓 Student:   liam.student@gmail.com   (Liam Davies - Class 12B)",
        flush=True,
    )
    print(
        "  👩‍🎓 Student:   sophia.student@gmail.com (Sophia Chen - Class 12B)",
        flush=True,
    )
    print(
        "  👨‍🏫 Teacher:   teacher@gmail.com        (Prof. Marcus Brody - Science)",
        flush=True,
    )
    print(
        "  👩‍🏫 Teacher:   teacher.math@gmail.com   (Dr. Sarah Jenkins - Maths)",
        flush=True,
    )
    print("  🎓 Principal: principal@gmail.com      (Dr. Evelyn Reed)", flush=True)
    print("  🛡️ Admin:     admin@gmail.com          (System Administrator)", flush=True)
    print("==================================================", flush=True)
