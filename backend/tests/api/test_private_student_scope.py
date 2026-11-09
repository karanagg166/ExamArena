"""Real PostgreSQL regression matrix for private student records and aliases."""

import pytest
from sqlalchemy import delete, select, update

from app.core.models import Principal, Role, School, Subject, Teacher, TeacherClass
from tests.factories.class_factory import create_class_factory
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import create_teacher_factory
from tests.factories.user_factory import create_user_factory


@pytest.fixture
async def records(db_session):
    school = await create_school_factory(db_session)
    principal = await db_session.scalar(
        select(Teacher.userId).join(Principal).where(Principal.schoolId == school.id)
    )
    from app.core.models import User

    principal_user = await db_session.get(User, principal)
    teacher_user = await create_user_factory(db_session, role=Role.TEACHER)
    teacher = await create_teacher_factory(db_session, user=teacher_user, school=school)
    assigned = await create_class_factory(db_session, school=school, section="ASSIGNED")
    other = await create_class_factory(db_session, school=school, section="OTHER")
    primary = await create_class_factory(
        db_session, school=school, teacher=teacher, section="PRIMARY"
    )
    db_session.add(
        TeacherClass(teacherId=teacher.id, classId=assigned.id, subject=Subject.SCIENCE)
    )
    own = await create_student_factory(db_session, school_class=assigned)
    peer = await create_student_factory(db_session, school_class=assigned)
    unassigned = await create_student_factory(db_session, school_class=other)
    primary_student = await create_student_factory(db_session, school_class=primary)
    foreign = await create_student_factory(db_session)
    own_user = await db_session.get(User, own.userId)
    no_grants = await create_user_factory(db_session, role=Role.TEACHER)
    await create_teacher_factory(db_session, user=no_grants, school=school)
    await db_session.commit()
    return dict(
        school=school,
        principal=principal_user,
        teacher=teacher_user,
        teacher_profile=teacher,
        assigned=assigned,
        other=other,
        own=own,
        peer=peer,
        unassigned=unassigned,
        foreign=foreign,
        primary_student=primary_student,
        student=own_user,
        no_grants=no_grants,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("suffix", ["", "/exams", "/results"])
@pytest.mark.parametrize(
    "caller,target,expected",
    [
        ("student", "own", 200),
        ("student", "peer", 403),
        ("teacher", "own", 200),
        ("teacher", "primary_student", 200),
        ("teacher", "unassigned", 403),
        ("teacher", "foreign", 403),
        ("no_grants", "own", 403),
        ("principal", "unassigned", 200),
        ("principal", "foreign", 403),
    ],
)
async def test_student_record_access(
    records, auth_client_factory, suffix, caller, target, expected
):
    client = await auth_client_factory(records[caller])
    response = await client.get(f"/api/v1/students/{records[target].id}{suffix}")
    assert response.status_code == expected, response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "caller,expected",
    [
        ("student", {"own"}),
        ("teacher", {"own", "peer", "primary_student"}),
        ("principal", {"own", "peer", "primary_student", "unassigned"}),
        ("no_grants", set()),
    ],
)
async def test_list_is_filtered_in_database(
    records, auth_client_factory, caller, expected
):
    client = await auth_client_factory(records[caller])
    response = await client.get("/api/v1/students")
    assert response.status_code == 200, response.text
    assert {x["id"] for x in response.json()} == {records[key].id for key in expected}


@pytest.mark.asyncio
@pytest.mark.parametrize("suffix", ["students", "results", "analytics", "leaderboard"])
@pytest.mark.parametrize(
    "caller,class_key,expected",
    [
        ("student", "assigned", 403),
        ("teacher", "assigned", 200),
        ("teacher", "other", 403),
        ("principal", "other", 200),
    ],
)
async def test_class_routes_share_boundary(
    records, auth_client_factory, suffix, caller, class_key, expected
):
    client = await auth_client_factory(records[caller])
    response = await client.get(f"/api/v1/classes/{records[class_key].id}/{suffix}")
    assert response.status_code == expected, response.text


@pytest.mark.asyncio
async def test_revoked_assignment_denies_existing_login(
    records, auth_client_factory, db_session
):
    client = await auth_client_factory(records["teacher"])
    path = f'/api/v1/students/{records["own"].id}/results'
    assert (await client.get(path)).status_code == 200
    await db_session.execute(
        delete(TeacherClass).where(
            TeacherClass.teacherId == records["teacher_profile"].id
        )
    )
    await db_session.commit()
    assert (await client.get(path)).status_code == 403


@pytest.mark.asyncio
async def test_role_alone_never_grants_global_private_record_access(
    records, auth_client_factory, db_session
):
    user = await create_user_factory(db_session, role=Role.ADMIN)
    await db_session.commit()
    client = await auth_client_factory(user)
    assert (await client.get("/api/v1/students")).status_code == 403
    assert (
        await client.get(f'/api/v1/students/{records["own"].id}')
    ).status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_transfer_student_to_gain_access(
    records, auth_client_factory
):
    client = await auth_client_factory(records["teacher"])
    response = await client.post(
        f'/api/v1/classes/{records["assigned"].id}/assign-student',
        json={"studentId": records["unassigned"].id},
    )
    assert response.status_code == 403
    assert (
        await client.get(f'/api/v1/students/{records["unassigned"].id}')
    ).status_code == 403


@pytest.mark.asyncio
async def test_principal_link_revocation_denies_existing_login(
    records, auth_client_factory, db_session
):
    client = await auth_client_factory(records["principal"])
    path = f'/api/v1/students/{records["unassigned"].id}/exams'
    assert (await client.get(path)).status_code == 200
    await db_session.execute(
        delete(Principal).where(Principal.schoolId == records["school"].id)
    )
    await db_session.execute(
        update(School)
        .where(School.id == records["school"].id)
        .values(createdBy=records["no_grants"].id)
    )
    await db_session.commit()
    assert (await client.get(path)).status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "caller,target,expected",
    [("teacher", "own", 200), ("teacher", "unassigned", 403), ("student", "peer", 403)],
)
async def test_analytics_student_alias_has_same_grants(
    records, auth_client_factory, caller, target, expected
):
    client = await auth_client_factory(records[caller])
    response = await client.get(
        f"/api/v1/analytics/students/{records[target].id}/results"
    )
    assert response.status_code == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["ADMIN", "PRINCIPAL", None])
async def test_self_profile_cannot_change_role(records, auth_client_factory, role):
    client = await auth_client_factory(records["teacher"])
    response = await client.put("/api/v1/auth/me", json={"role": role})
    assert response.status_code == 422
    assert (await client.get("/api/v1/auth/me")).json()["role"] == "TEACHER"
    assert (
        await client.get(f'/api/v1/students/{records["unassigned"].id}')
    ).status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_initialize_another_schools_principal(
    records, auth_client_factory
):
    client = await auth_client_factory(records["teacher"])
    response = await client.post(
        "/api/v1/principals", json={"schoolId": records["school"].id, "experience": 1}
    )
    assert response.status_code == 403
    assert (await client.get("/api/v1/auth/me")).json()["role"] == "TEACHER"


@pytest.mark.asyncio
async def test_owner_can_reinitialize_principal_profile(
    records, auth_client_factory, db_session
):
    await db_session.execute(
        delete(Principal).where(Principal.schoolId == records["school"].id)
    )
    await db_session.commit()
    client = await auth_client_factory(records["principal"])
    response = await client.post(
        "/api/v1/principals", json={"schoolId": records["school"].id, "experience": 1}
    )
    assert response.status_code == 201
    assert (
        await client.get(f'/api/v1/students/{records["unassigned"].id}')
    ).status_code == 200


@pytest.mark.asyncio
async def test_principal_cannot_move_own_authority_to_foreign_school(
    records, auth_client_factory
):
    client = await auth_client_factory(records["principal"])
    response = await client.put(
        "/api/v1/principals/me", json={"schoolId": records["foreign"].schoolId}
    )
    assert response.status_code == 422
    assert (
        await client.get(f'/api/v1/students/{records["foreign"].id}')
    ).status_code == 403


@pytest.mark.asyncio
async def test_public_signup_cannot_create_platform_administrator(client):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "synthetic-admin@example.com",
            "name": "Synthetic admin",
            "password": "Synthetic-only-password-1!",
            "phoneNo": "9999999999",
            "pincode": "110001",
            "city": "Synthetic",
            "state": "Synthetic",
            "country": "India",
            "dateOfBirth": "2000-01-01T00:00:00Z",
            "role": "ADMIN",
        },
    )
    assert response.status_code == 422
