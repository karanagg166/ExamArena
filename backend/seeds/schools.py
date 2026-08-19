"""School, class, and enrollment mapping seeding module for ExamArena."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    ClassJoinRequest,
    JoinRequestStatus,
    School,
    SchoolClass,
    SchoolType,
    Subject,
    Teacher,
    TeacherClass,
    TeacherSchoolJoinRequest,
    User,
)
from seeds.data import CLASSES_FIXTURES, SCHOOL_FIXTURE


async def seed_school(session: AsyncSession, admin_user: User) -> School:
    """Seed or update the primary school organization."""
    s_stmt = select(School).where(School.schoolCode == SCHOOL_FIXTURE["schoolCode"])
    school = (await session.execute(s_stmt)).scalar_one_or_none()
    if not school:
        old_stmt = select(School).where(School.schoolCode == "SCH001")
        school = (await session.execute(old_stmt)).scalar_one_or_none()

    if not school:
        school = School(
            name=SCHOOL_FIXTURE["name"],
            schoolCode=SCHOOL_FIXTURE["schoolCode"],
            createdBy=admin_user.id,
            address=SCHOOL_FIXTURE["address"],
            city=SCHOOL_FIXTURE["city"],
            state=SCHOOL_FIXTURE["state"],
            country=SCHOOL_FIXTURE["country"],
            pincode=SCHOOL_FIXTURE["pincode"],
            type=SchoolType.PRIVATE,
            email=SCHOOL_FIXTURE["email"],
            website=SCHOOL_FIXTURE["website"],
            phoneNo=SCHOOL_FIXTURE["phoneNo"],
        )
        session.add(school)
        await session.commit()
        await session.refresh(school)
        print(f"  [+] Created School: {school.name} ({school.schoolCode})", flush=True)
    else:
        school.name = SCHOOL_FIXTURE["name"]
        school.schoolCode = SCHOOL_FIXTURE["schoolCode"]
        school.address = SCHOOL_FIXTURE["address"]
        school.city = SCHOOL_FIXTURE["city"]
        school.state = SCHOOL_FIXTURE["state"]
        school.email = SCHOOL_FIXTURE["email"]
        school.website = SCHOOL_FIXTURE["website"]
        school.phoneNo = SCHOOL_FIXTURE["phoneNo"]
        await session.commit()
        await session.refresh(school)
        print(f"  [*] Updated School: {school.name} ({school.schoolCode})", flush=True)
    return school


async def seed_classes(
    session: AsyncSession, school: School, teachers_map: dict[str, tuple[User, Teacher]]
) -> dict[str, SchoolClass]:
    """Seed school classes and link class teachers."""
    classes = {}
    for c_cfg in CLASSES_FIXTURES:
        c_stmt = select(SchoolClass).where(
            SchoolClass.schoolId == school.id,
            SchoolClass.year == c_cfg["year"],
            SchoolClass.section == c_cfg["section"],
        )
        sc = (await session.execute(c_stmt)).scalar_one_or_none()
        t_prof = teachers_map[c_cfg["classTeacherKey"]][1]
        if not sc:
            sc = SchoolClass(
                name=c_cfg["name"],
                year=c_cfg["year"],
                section=c_cfg["section"],
                schoolId=school.id,
                teacherId=t_prof.id,
                joinCode=c_cfg["joinCode"],
                nextRollNo=c_cfg["nextRollNo"],
            )
            session.add(sc)
            await session.commit()
            await session.refresh(sc)
            print(
                f"  [+] Created Class: {sc.name}-{sc.section} (Join Code: {sc.joinCode})",
                flush=True,
            )
        else:
            sc.name = c_cfg["name"]
            sc.joinCode = c_cfg["joinCode"]
            sc.teacherId = t_prof.id
            await session.commit()

        classes[f"{c_cfg['name']}-{c_cfg['section']}"] = sc
    return classes


async def seed_school_memberships(
    session: AsyncSession,
    school: School,
    principal_user: User,
    teachers_map: dict[str, tuple[User, Teacher]],
    classes_map: dict[str, SchoolClass],
    students_map: dict[str, tuple[User, Any]],
) -> None:
    """Seed approved teacher school requests, teacher subject mappings, and student class join requests."""
    # 1. Teacher School Join Requests
    for _, (_, t_prof) in teachers_map.items():
        ts_stmt = select(TeacherSchoolJoinRequest).where(
            TeacherSchoolJoinRequest.teacherId == t_prof.id,
            TeacherSchoolJoinRequest.schoolId == school.id,
        )
        ts_req = (await session.execute(ts_stmt)).scalar_one_or_none()
        if not ts_req:
            ts_req = TeacherSchoolJoinRequest(
                teacherId=t_prof.id,
                schoolId=school.id,
                status=JoinRequestStatus.APPROVED,
                decidedAt=datetime.now(UTC),
                decidedBy=principal_user.id,
            )
            session.add(ts_req)
            await session.commit()

    # 2. Teacher-Class Subject Mappings
    t1_prof = teachers_map["teacher1"][1]
    t2_prof = teachers_map["teacher2"][1]
    c10 = classes_map["Class 10-A"]
    c12 = classes_map["Class 12-B"]

    tc_mappings = [
        (t1_prof.id, c10.id, Subject.SCIENCE),
        (t1_prof.id, c12.id, Subject.SCIENCE),
        (t2_prof.id, c10.id, Subject.MATHS),
        (t2_prof.id, c12.id, Subject.MATHS),
    ]
    for t_id, c_id, subj in tc_mappings:
        tc_stmt = select(TeacherClass).where(
            TeacherClass.teacherId == t_id, TeacherClass.classId == c_id
        )
        if not (await session.execute(tc_stmt)).scalar_one_or_none():
            session.add(TeacherClass(teacherId=t_id, classId=c_id, subject=subj))
    await session.commit()

    # 3. Student Class Join Requests
    for s_user, st_prof in students_map.values():
        cjr_stmt = select(ClassJoinRequest).where(
            ClassJoinRequest.studentUserId == s_user.id,
            ClassJoinRequest.classId == st_prof.classId,
        )
        if not (await session.execute(cjr_stmt)).scalar_one_or_none():
            session.add(
                ClassJoinRequest(
                    studentUserId=s_user.id,
                    classId=st_prof.classId,
                    status=JoinRequestStatus.APPROVED,
                    decidedAt=datetime.now(UTC) - timedelta(days=30),
                    decidedBy=principal_user.id,
                )
            )
            await session.commit()
