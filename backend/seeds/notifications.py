"""Contextual notification seeding module for ExamArena."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Notification, Student, Teacher, User


async def seed_notifications(
    session: AsyncSession,
    principal_user: User,
    teachers_map: dict[str, tuple[User, Teacher]],
    students_map: dict[str, tuple[User, Student]],
) -> None:
    """Seed relevant contextual notifications for Students, Teachers, and Principal."""
    print("\n🔔 Creating Contextual Notifications...", flush=True)

    alex_user = students_map["student@gmail.com"][0]
    t1_user = teachers_map["teacher1"][0]
    t2_user = teachers_map["teacher2"][0]

    notifications_list = [
        (
            alex_user.id,
            "🎉 Results for 'CBSE Class 10 Science: Force, Work & Chemical Bonding' have been released. Your score: 28/30 (93.3% - Rank 1).",
        ),
        (
            alex_user.id,
            "📢 New assessment 'Cellular Biology & Genetics Periodic Quiz' is now active for Class 10-A.",
        ),
        (
            alex_user.id,
            "🏫 Welcome to Oakridge International Academy! You are enrolled in Class 10 - Section A.",
        ),
        (
            t1_user.id,
            "📝 2 student submissions graded for 'CBSE Class 10 Science: Force, Work & Chemical Bonding'.",
        ),
        (
            t1_user.id,
            "✅ Principal Dr. Evelyn Reed approved your science curriculum schedule.",
        ),
        (
            t2_user.id,
            "⭐ Liam Davies scored 100% on 'Senior Mathematics: Matrices, Vector Algebra & Calculus'.",
        ),
        (
            t2_user.id,
            "🔒 Private assignment 'Trigonometry & Coordinate Geometry Challenge' is scheduled with access code TRIG2024.",
        ),
        (
            principal_user.id,
            "🏫 Oakridge International Academy has 4 registered students across Class 10-A and Class 12-A.",
        ),
        (principal_user.id, "📊 Class 10-A Science Mid-Term overall average: 85.0%."),
    ]

    for user_id, msg in notifications_list:
        stmt = select(Notification).where(
            Notification.userId == user_id, Notification.message == msg
        )
        if not (await session.execute(stmt)).scalar_one_or_none():
            session.add(Notification(userId=user_id, message=msg, read=False))

    await session.commit()
