"""Exact-owner, reviewed creation of synthetic school/enrollment release fixtures."""

import hashlib
import hmac
import json
import time
import uuid
from datetime import UTC, datetime

from sqlalchemy import select, text

from app.core.models import (
    Role,
    School,
    SchoolClass,
    SchoolType,
    Student,
    Teacher,
    User,
)
from app.core.security import hash_password, verify_password

PLAN_TTL = 900


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def token(key, label):
    if not isinstance(key, str) or len(key) < 32:
        raise ValueError("A private fixture key of at least 32 characters is required.")
    return hmac.new(
        key.encode(), ("exam-arena-release-v1:" + label).encode(), "sha256"
    ).hexdigest()


def identifier(key, label):
    return str(uuid.UUID(token(key, label)[:32]))


def credentials(key):
    result = {"version": 1, "schools": {}, "accounts": {}}
    for school in ("a", "b"):
        result["schools"][school] = {
            "id": identifier(key, "school-" + school),
            "class_id": identifier(key, "class-" + school),
        }
        for role in ("teacher", "student"):
            label = role + "-" + school
            result["accounts"][label] = {
                "user_id": identifier(key, label),
                "profile_id": identifier(key, "profile-" + label),
                "email": "ss-release-" + token(key, label)[:24] + "@example.com",
                "password": token(key, "password-" + label)[:48] + "!Aa7",
            }
    result["schools"]["a"]["other_class_id"] = identifier(key, "other-class-a")
    return result


def specifications(key):
    values = credentials(key)
    users, schools, teachers, classes, students = [], [], [], [], []
    for school in ("a", "b"):
        scope = values["schools"][school]
        teacher = values["accounts"]["teacher-" + school]
        student = values["accounts"]["student-" + school]
        for role, account in ((Role.TEACHER, teacher), (Role.STUDENT, student)):
            users.append(
                (
                    User,
                    dict(
                        id=account["user_id"],
                        email=account["email"],
                        name="Search Sphere SYNTHETIC release "
                        + role.value
                        + " "
                        + school,
                        phoneNo="0000000000",
                        role=role,
                        dateOfBirth=datetime(2000, 1, 1, tzinfo=UTC),
                        city="SYNTHETIC",
                        state="SYNTHETIC",
                        country="SYNTHETIC",
                        pincode="000000",
                    ),
                )
            )
        schools.append(
            (
                School,
                dict(
                    id=scope["id"],
                    name="Search Sphere SYNTHETIC school " + school,
                    createdBy=teacher["user_id"],
                    address="Synthetic release fixture only",
                    city="SYNTHETIC",
                    state="SYNTHETIC",
                    country="SYNTHETIC",
                    pincode="000000",
                    schoolCode="SSR-" + token(key, "school-" + school)[:20],
                    type=SchoolType.PRIVATE,
                ),
            )
        )
        teachers.append(
            (
                Teacher,
                dict(
                    id=teacher["profile_id"],
                    userId=teacher["user_id"],
                    schoolId=scope["id"],
                    qualification="[]",
                    experience=0,
                    department="SYNTHETIC",
                    subjects='["SCIENCE"]',
                ),
            )
        )
        for suffix, class_id in (
            (school, scope["class_id"]),
            ("other-a", scope.get("other_class_id")),
        ):
            if class_id:
                classes.append(
                    (
                        SchoolClass,
                        dict(
                            id=class_id,
                            name="SYNTHETIC release class " + suffix,
                            year="SYNTHETIC",
                            section=suffix,
                            schoolId=scope["id"],
                            teacherId=teacher["profile_id"],
                            joinCode=token(key, "join-" + suffix)[:32],
                        ),
                    )
                )
        students.append(
            (
                Student,
                dict(
                    id=student["profile_id"],
                    userId=student["user_id"],
                    schoolId=scope["id"],
                    classId=scope["class_id"],
                    rollNo="SYNTHETIC-1",
                ),
            )
        )
    return [users, schools, teachers, classes, students]


def target_digest(sessions):
    url = sessions.kw["bind"].url
    return digest(url.set(password=None).render_as_string(hide_password=True))


async def inspect_state(db, key):
    """Read only expected fixture columns and scoped credential verification."""
    present, snapshots = 0, []
    passwords = {
        value["user_id"]: value["password"]
        for value in credentials(key)["accounts"].values()
    }
    groups = specifications(key)
    for group in groups:
        for model, expected in group:
            columns = [getattr(model, field) for field in expected] + [model.updatedAt]
            row = (
                (await db.execute(select(*columns).where(model.id == expected["id"])))
                .mappings()
                .one_or_none()
            )
            # Guard reserved unique values even when an unowned row uses another ID.
            unique_field = {
                User: "email",
                School: "schoolCode",
                SchoolClass: "joinCode",
            }.get(model)
            if unique_field:
                collision = await db.scalar(
                    select(model.id).where(
                        getattr(model, unique_field) == expected[unique_field]
                    )
                )
                if collision is not None and collision != expected["id"]:
                    raise ValueError(
                        "Reserved synthetic identity is already owned elsewhere."
                    )
            if row is None:
                snapshots.append([model.__tablename__, expected["id"], "absent"])
                continue
            current = dict(row)
            # Production's Prisma-era DOB column is timestamp without time zone.
            # The fixture's fixed UTC midnight compares the same through either schema.
            birth = current.get("dateOfBirth")
            if model is User and isinstance(birth, datetime) and birth.tzinfo is None:
                current["dateOfBirth"] = birth.replace(tzinfo=UTC)
            if any(current[field] != value for field, value in expected.items()):
                raise ValueError(
                    "Existing fixture ownership or grants changed; refusing to overwrite."
                )
            if model is User:
                stored_hash = await db.scalar(
                    select(User.password).where(User.id == expected["id"])
                )
                if not verify_password(passwords[expected["id"]], stored_hash):
                    raise ValueError(
                        "Existing fixture credentials changed; refusing to overwrite."
                    )
            present += 1
            snapshots.append(
                [model.__tablename__, expected["id"], str(row["updatedAt"])]
            )
    total = sum(len(group) for group in groups)
    if present not in (0, total):
        raise ValueError(
            "Partial fixture state requires operator review; refusing repair."
        )
    return {
        "state": "create" if present == 0 else "verified_existing",
        "fingerprint": digest(snapshots),
        "records": total,
    }


async def build_plan(sessions, key):
    async with sessions() as db, db.begin():
        await db.execute(text("SET TRANSACTION READ ONLY"))
        state = await inspect_state(db, key)
    return {
        "version": 1,
        "created_at": int(time.time()),
        "owner": token(key, "owner"),
        "target": target_digest(sessions),
        **state,
    }


async def apply_plan(sessions, key, plan, reviewed_digest):
    if (
        not isinstance(plan, dict)
        or set(plan)
        != {
            "version",
            "created_at",
            "owner",
            "target",
            "state",
            "fingerprint",
            "records",
        }
        or plan["version"] != 1
        or type(plan["created_at"]) is not int
        or not 0 <= time.time() - plan["created_at"] <= PLAN_TTL
    ):
        raise ValueError("Invalid or expired synthetic fixture plan.")
    if (
        not hmac.compare_digest(digest(plan), reviewed_digest)
        or plan["owner"] != token(key, "owner")
        or plan["target"] != target_digest(sessions)
    ):
        raise ValueError("Reviewed plan owner, target or digest mismatch.")
    async with sessions() as db, db.begin():
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:owner, 0))"),
            {"owner": plan["owner"]},
        )
        current = await inspect_state(db, key)
        if any(current[field] != plan[field] for field in current):
            raise ValueError(
                "Fixture state changed after review; create a new dry run."
            )
        if current["state"] == "create":
            passwords = {
                value["user_id"]: value["password"]
                for value in credentials(key)["accounts"].values()
            }
            for group in specifications(key):
                for model, expected in group:
                    fields = dict(expected)
                    if model is User:
                        fields["password"] = hash_password(passwords[fields["id"]])
                    db.add(model(**fields))
                await db.flush()
        return {"result": current["state"], "records": current["records"]}
