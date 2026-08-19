"""User and role profile seeding module for ExamArena."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Principal, Role, School, Student, Teacher, User
from app.core.security import hash_password
from seeds.data import STUDENTS_FIXTURES, USERS_FIXTURES

DEFAULT_PASSWORD = hash_password("karan166")


async def get_or_create_user(
    session: AsyncSession,
    name: str,
    email: str,
    role: Role,
    phone_no: str,
    dob: datetime,
    city: str = "New Delhi",
    state: str = "Delhi",
    country: str = "India",
    pincode: str = "110001",
) -> User:
    """Find existing user by email or create a new user with standard dev credentials."""
    stmt = select(User).where(User.email == email)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if not user:
        user = User(
            name=name,
            email=email,
            password=DEFAULT_PASSWORD,
            phoneNo=phone_no,
            role=role,
            dateOfBirth=dob,
            city=city,
            state=state,
            country=country,
            pincode=pincode,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"  [+] Created User: {name} ({email}) [{role.value}]", flush=True)
    else:
        user.password = DEFAULT_PASSWORD
        user.name = name
        user.role = role
        user.phoneNo = phone_no
        await session.commit()
        await session.refresh(user)
        print(f"  [*] Updated User: {name} ({email}) [{role.value}]", flush=True)
    return user


async def seed_admin(session: AsyncSession) -> User:
    """Seed system administrator user."""
    cfg = USERS_FIXTURES["admin"]
    return await get_or_create_user(
        session, cfg["name"], cfg["email"], Role.ADMIN, cfg["phone_no"], cfg["dob"]
    )


async def seed_principal(
    session: AsyncSession, school: School
) -> tuple[User, Teacher, Principal]:
    """Seed Principal user and link to Teacher and Principal profile records."""
    p_cfg = USERS_FIXTURES["principal"]
    principal_user = await get_or_create_user(
        session,
        p_cfg["name"],
        p_cfg["email"],
        Role.PRINCIPAL,
        p_cfg["phone_no"],
        p_cfg["dob"],
    )

    t_stmt = select(Teacher).where(Teacher.userId == principal_user.id)
    p_teacher = (await session.execute(t_stmt)).scalar_one_or_none()
    if not p_teacher:
        p_teacher = Teacher(
            userId=principal_user.id,
            qualification=p_cfg["qualification"],
            experience=p_cfg["experience"],
            department=p_cfg["department"],
            subjects=p_cfg["subjects"],
            schoolId=school.id,
        )
        session.add(p_teacher)
        await session.commit()
        await session.refresh(p_teacher)
    else:
        p_teacher.schoolId = school.id
        p_teacher.experience = p_cfg["experience"]
        await session.commit()

    pr_stmt = select(Principal).where(Principal.teacherId == p_teacher.id)
    principal_rec = (await session.execute(pr_stmt)).scalar_one_or_none()
    if not principal_rec:
        principal_rec = Principal(
            experience=16,
            schoolId=school.id,
            teacherId=p_teacher.id,
        )
        session.add(principal_rec)
        await session.commit()
        print(f"  [+] Created Principal record for {p_cfg['name']}", flush=True)

    return principal_user, p_teacher, principal_rec


async def seed_teachers(
    session: AsyncSession, school: School
) -> dict[str, tuple[User, Teacher]]:
    """Seed Teacher users and their Teacher profile records."""
    teachers = {}
    for t_key in ["teacher1", "teacher2"]:
        cfg = USERS_FIXTURES[t_key]
        t_user = await get_or_create_user(
            session,
            cfg["name"],
            cfg["email"],
            Role.TEACHER,
            cfg["phone_no"],
            cfg["dob"],
        )
        stmt = select(Teacher).where(Teacher.userId == t_user.id)
        t_profile = (await session.execute(stmt)).scalar_one_or_none()
        if not t_profile:
            t_profile = Teacher(
                userId=t_user.id,
                qualification=cfg["qualification"],
                experience=cfg["experience"],
                department=cfg["department"],
                subjects=cfg["subjects"],
                schoolId=school.id,
            )
            session.add(t_profile)
            await session.commit()
            await session.refresh(t_profile)
            print(f"  [+] Created Teacher Profile: {cfg['name']}", flush=True)
        else:
            t_profile.schoolId = school.id
            t_profile.department = cfg["department"]
            t_profile.subjects = cfg["subjects"]
            await session.commit()

        teachers[t_key] = (t_user, t_profile)
    return teachers


async def seed_students(
    session: AsyncSession, school: School, classes_map: dict[str, Any]
) -> dict[str, tuple[User, Student]]:
    """Seed Student users and Student profile records."""
    students = {}
    for item in STUDENTS_FIXTURES:
        s_user = await get_or_create_user(
            session,
            item["name"],
            item["email"],
            Role.STUDENT,
            item["phone"],
            item["dob"],
        )
        target_class = classes_map[f"{item['class_name']}-{item['class_section']}"]

        st_stmt = select(Student).where(Student.userId == s_user.id)
        st_profile = (await session.execute(st_stmt)).scalar_one_or_none()
        if not st_profile:
            st_profile = Student(
                userId=s_user.id,
                rollNo=item["rollNo"],
                classId=target_class.id,
                schoolId=school.id,
                parentName=item["parentName"],
                parentEmail=item["parentEmail"],
                fatherName=item["fatherName"],
                fatherEmail=item["parentEmail"],
                fatherPhoneNo=item["fatherPhone"],
                motherName=item["motherName"],
                motherEmail=item["parentEmail"],
                motherPhoneNo=item["motherPhone"],
            )
            session.add(st_profile)
            await session.commit()
            await session.refresh(st_profile)
            print(
                f"  [+] Created Student Profile: {item['name']} ({item['rollNo']})",
                flush=True,
            )
        else:
            st_profile.classId = target_class.id
            st_profile.schoolId = school.id
            st_profile.rollNo = item["rollNo"]
            await session.commit()

        students[item["email"]] = (s_user, st_profile)
    return students
