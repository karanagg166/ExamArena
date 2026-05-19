import asyncio
from datetime import datetime, timezone
import sys
import os

# Ensure the backend directory is in the sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prisma import Prisma
from app.core.security import hash_password

async def main():
    prisma = Prisma()
    await prisma.connect()
    
    try:
        print("Starting database seeding...")
        
        # 1. Create Admin User (Creator of the School)
        admin_email = "admin@gmail.com"
        admin_user = await prisma.user.find_unique(where={"email": admin_email})
        if not admin_user:
            admin_user = await prisma.user.create(
                data={
                    "name": "System Admin",
                    "email": admin_email,
                    "password": hash_password("admin123"),
                    "phoneNo": "1234567890",
                    "role": "ADMIN",
                    "dateOfBirth": datetime(1980, 1, 1, tzinfo=timezone.utc),
                    "city": "Admin City",
                    "country": "Admin Country",
                    "pincode": "000000",
                    "state": "Admin State"
                }
            )
            print("Created Admin User.")

        # 2. Create School
        school_code = "SCH001"
        school = await prisma.school.find_unique(where={"schoolCode": school_code})
        if not school:
            school = await prisma.school.create(
                data={
                    "name": "Exam Arena High School",
                    "schoolCode": school_code,
                    "createdBy": admin_user.id,
                    "address": "123 Education Lane",
                    "city": "Knowledge City",
                    "state": "State of Learning",
                    "country": "Country",
                    "pincode": "123456",
                    "type": "PUBLIC",
                    "email": "contact@gmail.com"
                }
            )
            print("Created School.")

        # 3. Create Principal User -> Teacher -> Principal
        principal_email = "principal@gmail.com"
        principal_user = await prisma.user.find_unique(where={"email": principal_email})
        if not principal_user:
            principal_user = await prisma.user.create(
                data={
                    "name": "Dr. Principal",
                    "email": principal_email,
                    "password": hash_password("principal123"),
                    "phoneNo": "9876543210",
                    "role": "PRINCIPAL",
                    "dateOfBirth": datetime(1975, 5, 5, tzinfo=timezone.utc),
                    "city": "Knowledge City",
                    "country": "Country",
                    "pincode": "123456",
                    "state": "State of Learning"
                }
            )
            
            # Principal is also a Teacher in schema
            principal_teacher = await prisma.teacher.create(
                data={
                    "userId": principal_user.id,
                    "experience": 20,
                    "department": "Administration",
                    "schoolId": school.id
                }
            )
            
            await prisma.principal.create(
                data={
                    "experience": 20,
                    "schoolId": school.id,
                    "teacherId": principal_teacher.id
                }
            )
            print("Created Principal User, Teacher profile, and Principal profile.")
            
        # 4. Create Teacher User
        teacher_email = "teacher@gmail.com"
        teacher_user = await prisma.user.find_unique(where={"email": teacher_email})
        teacher_profile = None
        if not teacher_user:
            teacher_user = await prisma.user.create(
                data={
                    "name": "Karan Teacher",
                    "email": teacher_email,
                    "password": hash_password("karan166"),
                    "phoneNo": "5551234567",
                    "role": "TEACHER",
                    "dateOfBirth": datetime(1990, 10, 10, tzinfo=timezone.utc),
                    "city": "Knowledge City",
                    "country": "Country",
                    "pincode": "123456",
                    "state": "State of Learning"
                }
            )
            
            teacher_profile = await prisma.teacher.create(
                data={
                    "userId": teacher_user.id,
                    "experience": 5,
                    "department": "Science",
                    "schoolId": school.id
                }
            )
            print("Created Teacher User and Profile.")
        else:
            teacher_profile = await prisma.teacher.find_unique(where={"userId": teacher_user.id})

        # 5. Create School Class
        class_name = "Class 10"
        class_year = "2024"
        class_section = "A"
        
        # We need to find by unique constraint [schoolId, year, section]
        school_class = await prisma.schoolclass.find_unique(
            where={
                "schoolId_year_section": {
                    "schoolId": school.id,
                    "year": class_year,
                    "section": class_section
                }
            }
        )
        if not school_class:
            school_class = await prisma.schoolclass.create(
                data={
                    "name": class_name,
                    "year": class_year,
                    "section": class_section,
                    "schoolId": school.id,
                    "teacherId": teacher_profile.id if teacher_profile else None
                }
            )
            print("Created School Class.")
            
        # 6. Create Student User -> Student
        student_email = "student@gmail.com"
        student_user = await prisma.user.find_unique(where={"email": student_email})
        if not student_user:
            student_user = await prisma.user.create(
                data={
                    "name": "Alice Student",
                    "email": student_email,
                    "password": hash_password("student123"),
                    "phoneNo": "4445556666",
                    "role": "STUDENT",
                    "dateOfBirth": datetime(2010, 1, 1, tzinfo=timezone.utc),
                    "city": "Knowledge City",
                    "country": "Country",
                    "pincode": "123456",
                    "state": "State of Learning"
                }
            )
            
            await prisma.student.create(
                data={
                    "userId": student_user.id,
                    "rollNo": "R001",
                    "parentName": "Bob Parent",
                    "parentEmail": "parent@gmail.com",
                    "classId": school_class.id,
                    "schoolId": school.id
                }
            )
            print("Created Student User and Profile.")
            
        print("Database seeding completed successfully.")

    except Exception as e:
        print(f"Error during seeding: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
