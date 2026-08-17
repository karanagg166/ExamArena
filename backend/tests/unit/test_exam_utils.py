import re

from app.core.models import Subject, generate_exam_code
from app.exams.crud import normalize_subject


class TestExamUtilities:
    """U30-U39: Tests for exam helper functions, normalization, and code generation."""

    def test_normalize_subject_exact_match(self):
        assert normalize_subject("MATHS") == Subject.MATHS
        assert normalize_subject("SCIENCE") == Subject.SCIENCE
        assert normalize_subject("HISTORY") == Subject.HISTORY
        assert normalize_subject("LITERATURE") == Subject.LITERATURE
        assert normalize_subject("ART") == Subject.ART
        assert normalize_subject("MUSIC") == Subject.MUSIC
        assert normalize_subject("PHYSICAL_EDUCATION") == Subject.PHYSICAL_EDUCATION

    def test_normalize_subject_aliases(self):
        assert normalize_subject("Mathematics") == Subject.MATHS
        assert normalize_subject("Math") == Subject.MATHS
        assert normalize_subject("physics") == Subject.SCIENCE
        assert normalize_subject("chemistry") == Subject.SCIENCE
        assert normalize_subject("biology") == Subject.SCIENCE
        assert normalize_subject("English") == Subject.LITERATURE
        assert normalize_subject("pe") == Subject.PHYSICAL_EDUCATION
        assert normalize_subject("Physical Education") == Subject.PHYSICAL_EDUCATION

    def test_normalize_subject_enum_input(self):
        assert normalize_subject(Subject.MATHS) == Subject.MATHS
        assert normalize_subject(Subject.SCIENCE) == Subject.SCIENCE

    def test_normalize_subject_empty_and_null(self):
        assert normalize_subject("") is None
        assert normalize_subject("   ") is None
        assert normalize_subject(None) is None

    def test_normalize_subject_unknown(self):
        assert normalize_subject("ASTRONOMY") is None
        assert normalize_subject("Unknown") is None

    def test_generate_exam_code_format(self):
        code = generate_exam_code()
        assert isinstance(code, str)
        assert code.startswith("EXM-")
        assert len(code) == 10  # "EXM-" (4) + 6 chars
        assert re.match(r"^EXM-[A-Z0-9]{6}$", code) is not None

    def test_generate_exam_code_uniqueness(self):
        codes = {generate_exam_code() for _ in range(100)}
        assert len(codes) == 100
