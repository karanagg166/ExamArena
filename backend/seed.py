import asyncio
import os
import sys
from datetime import UTC, datetime

# Ensure the backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select

import app.core.database as db
from app.core.models import (
    Principal,
    Role,
    School,
    SchoolClass,
    SchoolType,
    Student,
    Teacher,
    User,
)
from app.core.security import hash_password


async def main():
    await db.init_db()

    async with db.AsyncSessionLocal() as session:
        try:
            print("Starting database seeding...")

            # 1. Create Admin User (Creator of the School)
            admin_email = "admin@gmail.com"
            admin_stmt = select(User).where(User.email == admin_email)
            admin_user = (await session.execute(admin_stmt)).scalar_one_or_none()
            if not admin_user:
                admin_user = User(
                    name="System Admin",
                    email=admin_email,
                    password=hash_password("admin123"),
                    phoneNo="1234567890",
                    role=Role.ADMIN,
                    dateOfBirth=datetime(1980, 1, 1, tzinfo=UTC),
                    city="Admin City",
                    country="Admin Country",
                    pincode="000000",
                    state="Admin State",
                )
                session.add(admin_user)
                await session.commit()
                await session.refresh(admin_user)
                print("Created Admin User.")

            # 2. Create School
            school_code = "SCH001"
            school_stmt = select(School).where(School.schoolCode == school_code)
            school = (await session.execute(school_stmt)).scalar_one_or_none()
            if not school:
                school = School(
                    name="Exam Arena High School",
                    schoolCode=school_code,
                    createdBy=admin_user.id,
                    address="123 Education Lane",
                    city="Knowledge City",
                    state="State of Learning",
                    country="Country",
                    pincode="123456",
                    type=SchoolType.PUBLIC,
                    email="contact@gmail.com",
                )
                session.add(school)
                await session.commit()
                await session.refresh(school)
                print("Created School.")

            # 3. Create Principal User -> Teacher -> Principal
            principal_email = "principal@gmail.com"
            p_user_stmt = select(User).where(User.email == principal_email)
            principal_user = (await session.execute(p_user_stmt)).scalar_one_or_none()
            if not principal_user:
                principal_user = User(
                    name="Dr. Principal",
                    email=principal_email,
                    password=hash_password("principal123"),
                    phoneNo="9876543210",
                    role=Role.PRINCIPAL,
                    dateOfBirth=datetime(1975, 5, 5, tzinfo=UTC),
                    city="Knowledge City",
                    country="Country",
                    pincode="123456",
                    state="State of Learning",
                )
                session.add(principal_user)
                await session.commit()
                await session.refresh(principal_user)

                principal_teacher = Teacher(
                    userId=principal_user.id,
                    experience=20,
                    department="Administration",
                    schoolId=school.id,
                )
                session.add(principal_teacher)
                await session.commit()
                await session.refresh(principal_teacher)

                principal = Principal(
                    experience=20,
                    schoolId=school.id,
                    teacherId=principal_teacher.id,
                )
                session.add(principal)
                await session.commit()
                print("Created Principal User, Teacher profile, and Principal profile.")

            # 4. Create Teacher User
            teacher_email = "teacher@gmail.com"
            t_user_stmt = select(User).where(User.email == teacher_email)
            teacher_user = (await session.execute(t_user_stmt)).scalar_one_or_none()
            teacher_profile = None
            if not teacher_user:
                teacher_user = User(
                    name="Karan Teacher",
                    email=teacher_email,
                    password=hash_password("karan166"),
                    phoneNo="5551234567",
                    role=Role.TEACHER,
                    dateOfBirth=datetime(1990, 10, 10, tzinfo=UTC),
                    city="Knowledge City",
                    country="Country",
                    pincode="123456",
                    state="State of Learning",
                )
                session.add(teacher_user)
                await session.commit()
                await session.refresh(teacher_user)

                teacher_profile = Teacher(
                    userId=teacher_user.id,
                    experience=5,
                    department="Science",
                    schoolId=school.id,
                )
                session.add(teacher_profile)
                await session.commit()
                await session.refresh(teacher_profile)
                print("Created Teacher User and Profile.")
            else:
                t_profile_stmt = select(Teacher).where(
                    Teacher.userId == teacher_user.id
                )
                teacher_profile = (
                    await session.execute(t_profile_stmt)
                ).scalar_one_or_none()

            # 5. Create School Class
            class_name = "Class 10"
            class_year = "2024"
            class_section = "A"

            sc_stmt = select(SchoolClass).where(
                SchoolClass.schoolId == school.id,
                SchoolClass.year == class_year,
                SchoolClass.section == class_section,
            )
            school_class = (await session.execute(sc_stmt)).scalar_one_or_none()
            if not school_class:
                school_class = SchoolClass(
                    name=class_name,
                    year=class_year,
                    section=class_section,
                    schoolId=school.id,
                    teacherId=teacher_profile.id if teacher_profile else None,
                )
                session.add(school_class)
                await session.commit()
                await session.refresh(school_class)
                print("Created School Class.")

            # 6. Create Student User -> Student
            student_email = "student@gmail.com"
            st_user_stmt = select(User).where(User.email == student_email)
            student_user = (await session.execute(st_user_stmt)).scalar_one_or_none()
            if not student_user:
                student_user = User(
                    name="Alice Student",
                    email=student_email,
                    password=hash_password("student123"),
                    phoneNo="4445556666",
                    role=Role.STUDENT,
                    dateOfBirth=datetime(2010, 1, 1, tzinfo=UTC),
                    city="Knowledge City",
                    country="Country",
                    pincode="123456",
                    state="State of Learning",
                )
                session.add(student_user)
                await session.commit()
                await session.refresh(student_user)

                student = Student(
                    userId=student_user.id,
                    rollNo="R001",
                    parentName="Bob Parent",
                    parentEmail="parent@gmail.com",
                    classId=school_class.id,
                    schoolId=school.id,
                )
                session.add(student)
                await session.commit()
                print("Created Student User and Profile.")

            print("Database seeding completed successfully.")

        except Exception as e:
            print(f"Error during seeding: {e}")
        finally:
            await db.close_db()


if __name__ == "__main__":
    asyncio.run(main())
