import pytest


class MockSchoolClass:
    def __init__(self, id: str, schoolId: str, name: str, nextRollNo: int = 1):
        self.id = id
        self.schoolId = schoolId
        self.name = name
        self.nextRollNo = nextRollNo


def allocate_roll_number(
    school_class: MockSchoolClass,
    custom_roll_no: str | None,
    existing_rolls_in_class: set[str],
) -> tuple[str, int]:
    """Pure helper reflecting roll number allocation logic in crud.py."""
    if custom_roll_no and custom_roll_no.strip():
        assigned = custom_roll_no.strip()
        if not assigned.isdigit():
            raise ValueError("Roll number must contain numbers only.")
        if assigned in existing_rolls_in_class:
            raise ValueError(
                f"Roll number '{assigned}' is already assigned in this class"
            )
        return assigned, school_class.nextRollNo
    else:
        assigned = str(school_class.nextRollNo)
        new_next = school_class.nextRollNo + 1
        return assigned, new_next


class TestJoinRequestRollLogic:
    """U40-U44: Tests for roll number allocation and validation."""

    def test_auto_roll_number_first_student(self):
        cls = MockSchoolClass("c1", "s1", "Class 10-A", nextRollNo=1)
        roll, next_no = allocate_roll_number(cls, None, set())
        assert roll == "1"
        assert next_no == 2

    def test_auto_roll_number_sequential_increment(self):
        cls = MockSchoolClass("c1", "s1", "Class 10-A", nextRollNo=5)
        roll, next_no = allocate_roll_number(cls, "", {"1", "2", "3", "4"})
        assert roll == "5"
        assert next_no == 6

    def test_custom_numeric_roll_accepted(self):
        cls = MockSchoolClass("c1", "s1", "Class 10-A", nextRollNo=1)
        roll, next_no = allocate_roll_number(cls, "42", set())
        assert roll == "42"
        assert next_no == 1  # nextRollNo unchanged for custom roll

    def test_custom_non_numeric_roll_rejected(self):
        cls = MockSchoolClass("c1", "s1", "Class 10-A", nextRollNo=1)
        with pytest.raises(ValueError, match="Roll number must contain numbers only."):
            allocate_roll_number(cls, "ROLL-01", set())

    def test_custom_duplicate_roll_rejected(self):
        cls = MockSchoolClass("c1", "s1", "Class 10-A", nextRollNo=5)
        with pytest.raises(ValueError, match="already assigned in this class"):
            allocate_roll_number(cls, "3", {"1", "2", "3", "4"})
