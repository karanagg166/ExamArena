"""Synthetic bootstrap uses isolated real PostgreSQL, never production credentials."""

import asyncio
import copy
import time

import pytest
from sqlalchemy import func, select, text, update

from app.core.models import Role, School, SchoolClass, Student, Teacher, User
from app.core.security import verify_password
from app.maintenance.release_fixtures import apply_plan, build_plan, credentials, digest
from tests.conftest import TestAsyncSessionLocal

KEY = "public-synthetic-release-fixture-test-key-001"


async def counts():
    async with TestAsyncSessionLocal() as db:
        return [
            await db.scalar(select(func.count()).select_from(model))
            for model in (User, School, Teacher, SchoolClass, Student)
        ]


@pytest.mark.asyncio
async def test_dry_run_and_repeat_verified_apply_do_not_write(db_session):
    before = await counts()
    plan = await build_plan(TestAsyncSessionLocal, KEY)
    assert plan["state"] == "create" and plan["records"] == 13
    assert await counts() == before

    assert "fixtures.invalid" not in str(plan) and "password" not in str(plan)
    result = await apply_plan(TestAsyncSessionLocal, KEY, plan, digest(plan))
    assert result == {"result": "create", "records": 13}
    after = await counts()
    assert [a - b for a, b in zip(after, before, strict=True)] == [4, 2, 2, 3, 2]
    follow = await build_plan(TestAsyncSessionLocal, KEY)
    assert follow["state"] == "verified_existing"
    assert (await apply_plan(TestAsyncSessionLocal, KEY, follow, digest(follow)))[
        "result"
    ] == "verified_existing"
    assert await counts() == after
    identity = credentials(KEY)
    async with TestAsyncSessionLocal() as db:
        for value in identity["accounts"].values():
            user = await db.get(User, value["user_id"])
            assert verify_password(value["password"], user.password)
        student = await db.get(Student, identity["accounts"]["student-a"]["profile_id"])
        assert student.classId == identity["schools"]["a"]["class_id"]
        assert student.schoolId != identity["schools"]["b"]["id"]


@pytest.mark.asyncio
async def test_concurrent_delivery_creates_one_atomic_fixture(db_session):
    plan = await build_plan(TestAsyncSessionLocal, KEY)
    before = await counts()
    results = await asyncio.gather(
        *(apply_plan(TestAsyncSessionLocal, KEY, plan, digest(plan)) for _ in range(2)),
        return_exceptions=True,
    )
    assert (
        sum(
            isinstance(value, dict) and value["result"] == "create" for value in results
        )
        == 1
    )
    assert sum(isinstance(value, ValueError) for value in results) == 1
    assert [a - b for a, b in zip(await counts(), before, strict=True)] == [
        4,
        2,
        2,
        3,
        2,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["role", "school", "class", "password", "partial"])
async def test_changed_identity_or_grants_are_never_overwritten(db_session, change):
    plan = await build_plan(TestAsyncSessionLocal, KEY)
    await apply_plan(TestAsyncSessionLocal, KEY, plan, digest(plan))
    owned = credentials(KEY)
    async with TestAsyncSessionLocal() as db, db.begin():
        if change == "role":
            await db.execute(
                update(User)
                .where(User.id == owned["accounts"]["teacher-a"]["user_id"])
                .values(role=Role.STUDENT)
            )
        elif change == "school":
            await db.execute(
                update(Teacher)
                .where(Teacher.id == owned["accounts"]["teacher-a"]["profile_id"])
                .values(schoolId=owned["schools"]["b"]["id"])
            )
        elif change == "class":
            await db.execute(
                update(Student)
                .where(Student.id == owned["accounts"]["student-a"]["profile_id"])
                .values(classId=owned["schools"]["a"]["other_class_id"])
            )
        elif change == "password":
            await db.execute(
                update(User)
                .where(User.id == owned["accounts"]["teacher-a"]["user_id"])
                .values(password="changed-synthetic-invalid-hash")
            )
        else:
            row = await db.get(Student, owned["accounts"]["student-a"]["profile_id"])
            await db.delete(row)
    before = await counts()
    with pytest.raises(ValueError):
        await build_plan(TestAsyncSessionLocal, KEY)
    with pytest.raises(ValueError):
        await apply_plan(TestAsyncSessionLocal, KEY, plan, digest(plan))
    assert await counts() == before


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["expired", "owner", "target", "digest"])
async def test_invalid_review_plan_cannot_create_any_rows(db_session, change):
    plan = copy.deepcopy(await build_plan(TestAsyncSessionLocal, KEY))
    before = await counts()
    if change == "expired":
        plan["created_at"] = int(time.time()) - 901
    elif change in ("owner", "target"):
        plan[change] = "0" * 64
    reviewed = "0" * 64 if change == "digest" else digest(plan)
    with pytest.raises(ValueError):
        await apply_plan(TestAsyncSessionLocal, KEY, plan, reviewed)
    assert await counts() == before


@pytest.mark.asyncio
async def test_existing_email_collision_preserves_foreign_account(db_session):
    from tests.factories.user_factory import create_user_factory

    value = credentials(KEY)["accounts"]["teacher-a"]
    foreign = await create_user_factory(
        db_session, email=value["email"], role=Role.STUDENT
    )
    await db_session.commit()
    before = await counts()
    with pytest.raises(ValueError, match="owned elsewhere"):
        await build_plan(TestAsyncSessionLocal, KEY)
    assert await counts() == before
    await db_session.refresh(foreign)
    assert foreign.role == Role.STUDENT


@pytest.mark.asyncio
async def test_late_insert_failure_rolls_back_all_fixture_records(
    db_session, monkeypatch
):
    from sqlalchemy.exc import IntegrityError

    from app.maintenance import release_fixtures

    plan = await build_plan(TestAsyncSessionLocal, KEY)
    before = await counts()
    original = release_fixtures.specifications

    def broken_specifications(key):
        groups = original(key)
        groups[-1][0][1]["classId"] = "00000000-0000-0000-0000-000000000001"
        return groups

    monkeypatch.setattr(release_fixtures, "specifications", broken_specifications)
    with pytest.raises(IntegrityError):
        await apply_plan(TestAsyncSessionLocal, KEY, plan, digest(plan))
    assert await counts() == before


@pytest.mark.asyncio
async def test_legacy_naive_birth_column_preserves_verified_fixture_ownership(
    db_session,
):
    plan = await build_plan(TestAsyncSessionLocal, KEY)
    await apply_plan(TestAsyncSessionLocal, KEY, plan, digest(plan))
    async with TestAsyncSessionLocal() as db, db.begin():
        await db.execute(
            text(
                'ALTER TABLE "User" ALTER COLUMN "dateOfBirth" TYPE TIMESTAMP WITHOUT TIME ZONE USING "dateOfBirth" AT TIME ZONE \'UTC\''
            )
        )
    try:
        verified = await build_plan(TestAsyncSessionLocal, KEY)
        assert verified["state"] == "verified_existing"
        assert (
            await apply_plan(TestAsyncSessionLocal, KEY, verified, digest(verified))
        )["result"] == "verified_existing"
    finally:
        async with TestAsyncSessionLocal() as db, db.begin():
            await db.execute(
                text(
                    'ALTER TABLE "User" ALTER COLUMN "dateOfBirth" TYPE TIMESTAMP WITH TIME ZONE USING "dateOfBirth" AT TIME ZONE \'UTC\''
                )
            )
