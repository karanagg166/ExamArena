from unittest.mock import AsyncMock, MagicMock

import pytest

from app.school_class.crud import assign_student_to_class, assign_teacher_to_class


@pytest.mark.asyncio
async def test_assign_student_does_not_transfer_between_schools():
    school_class = MagicMock(id="class_1", schoolId="school_1")
    student = MagicMock(id="student_1", classId="class_2", schoolId="school_2")
    class_result = MagicMock()
    class_result.scalar_one_or_none.return_value = school_class
    student_result = MagicMock()
    student_result.scalar_one_or_none.return_value = student
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.execute.side_effect = [class_result, student_result]

    assigned = await assign_student_to_class("class_1", "student_1", session=session)

    assert assigned is False
    assert student.classId == "class_2"
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_teacher_sets_required_subject():
    school_class = MagicMock(id="class_1", schoolId="school_1")
    teacher = MagicMock(id="teacher_1", schoolId="school_1")
    no_existing_assignment = MagicMock()
    no_existing_assignment.scalar_one_or_none.return_value = None
    class_result = MagicMock()
    class_result.scalar_one_or_none.return_value = school_class
    teacher_result = MagicMock()
    teacher_result.scalar_one_or_none.return_value = teacher
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.execute.side_effect = [
        class_result,
        teacher_result,
        no_existing_assignment,
    ]

    assigned = await assign_teacher_to_class("class_1", "teacher_1", session=session)

    assert assigned is True
    assignment = session.add.call_args.args[0]
    assert assignment.subject.value == "MATHS"
    session.commit.assert_awaited_once()
