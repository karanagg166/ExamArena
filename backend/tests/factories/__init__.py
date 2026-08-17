"""Test factories package for ExamArena integration tests."""

from tests.factories.attempt_factory import (
    create_attempt_answer_factory,
    create_attempt_factory,
)
from tests.factories.class_factory import create_class_factory
from tests.factories.exam_factory import (
    create_exam_factory,
    create_question_factory,
    create_section_factory,
)
from tests.factories.school_factory import create_school_factory
from tests.factories.student_factory import create_student_factory
from tests.factories.teacher_factory import (
    assign_teacher_to_class_factory,
    create_teacher_factory,
)
from tests.factories.user_factory import create_user_factory

__all__ = [
    "create_user_factory",
    "create_school_factory",
    "create_class_factory",
    "create_teacher_factory",
    "assign_teacher_to_class_factory",
    "create_student_factory",
    "create_exam_factory",
    "create_section_factory",
    "create_question_factory",
    "create_attempt_factory",
    "create_attempt_answer_factory",
]
