# backend/tests/dummy_data/sections.py
from datetime import datetime
from unittest.mock import MagicMock


def make_fake_section(overrides: dict = None) -> MagicMock:
    if overrides is None:
        overrides = {}

    section = MagicMock()
    section.id = "clxfake_section_001"
    section.name = "Section A"
    section.description = "First section"
    section.questionType = "MULTIPLE_CHOICE"
    section.marksPerQuestion = 5
    section.sortOrder = 1
    section.examId = "clxfake_exam_001"
    section.createdAt = datetime(2026, 1, 1)
    section.updatedAt = datetime(2026, 1, 1)
    section.questions = []

    for k, v in overrides.items():
        setattr(section, k, v)
    return section
