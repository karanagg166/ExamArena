import unittest.mock as mock
from datetime import UTC, datetime, timedelta

from app.core.models import (
    Correctness,
    GradingStatus,
    QuestionType,
    StudentExamStatus,
)


class MockOption:
    def __init__(self, id: str, text: str, isCorrect: bool):
        self.id = id
        self.text = text
        self.isCorrect = isCorrect


class MockQuestion:
    def __init__(
        self,
        id: str,
        questionType: QuestionType,
        marks: float,
        options: list[MockOption] | None = None,
        negativeMarks: float | None = None,
        section: str = "Section A",
        sectionId: str | None = None,
        examSection=None,
    ):
        self.id = id
        self.questionType = questionType
        self.marks = marks
        self.options = options or []
        self.negativeMarks = negativeMarks
        self.section = section
        self.sectionId = sectionId
        self.examSection = examSection


class MockSelectedOption:
    def __init__(self, optionId: str):
        self.optionId = optionId


class MockStudentExamAnswer:
    def __init__(
        self,
        id: str,
        questionId: str,
        questionType: QuestionType,
        selectedOptions: list[MockSelectedOption] | None = None,
        textAnswer: str | None = None,
    ):
        self.id = id
        self.questionId = questionId
        self.questionType = questionType
        self.selectedOptions = selectedOptions or []
        self.textAnswer = textAnswer
        self.marksAwarded = 0.0
        self.isCorrect = Correctness.INCORRECT
        self.gradingStatus = GradingStatus.PENDING


class MockSection:
    def __init__(
        self,
        id: str,
        name: str,
        negativeMarking: bool = False,
        negativeMarks: float = 0.0,
    ):
        self.id = id
        self.name = name
        self.negativeMarking = negativeMarking
        self.negativeMarks = negativeMarks


class MockExam:
    def __init__(
        self,
        duration: int = 60,
        negativeMarking: bool = False,
        negativeMarks: float = 0.0,
        questions: list[MockQuestion] | None = None,
        sections: list[MockSection] | None = None,
    ):
        self.duration = duration
        self.negativeMarking = negativeMarking
        self.negativeMarks = negativeMarks
        self.questions = questions or []
        self.sections = sections or []


def grade_attempt_pure(
    exam: MockExam,
    answers: list[MockStudentExamAnswer],
) -> tuple[float, bool, list[MockStudentExamAnswer]]:
    """Pure implementation of the core grading engine from crud.py for unit validation."""
    questions_by_id = {q.id: q for q in (exam.questions or [])}
    sections_by_id = {sec.id: sec for sec in (exam.sections or [])}
    sections_by_name = {sec.name: sec for sec in (exam.sections or [])}

    total_marks_obtained = 0.0
    has_pending_subjective = False

    for db_ans in answers:
        q = questions_by_id.get(db_ans.questionId)
        if not q:
            continue

        q_marks = float(q.marks)

        section_obj = (
            q.examSection
            or (sections_by_id.get(q.sectionId) if q.sectionId else None)
            or (sections_by_name.get(q.section) if q.section else None)
        )
        if section_obj:
            sec_has_neg = section_obj.negativeMarking
            sec_neg_marks = float(section_obj.negativeMarks)
        else:
            sec_has_neg = exam.negativeMarking
            sec_neg_marks = float(exam.negativeMarks)

        q_neg = getattr(q, "negativeMarks", None)
        if q_neg is not None:
            neg_marks = float(q_neg)
            has_neg = True
        elif sec_has_neg:
            neg_marks = sec_neg_marks
            has_neg = sec_neg_marks > 0
        else:
            neg_marks = 0.0
            has_neg = False

        penalty = abs(neg_marks) if (has_neg and neg_marks > 0) else 0.0

        selected_opt_ids = {so.optionId for so in (db_ans.selectedOptions or [])}
        correct_opt_ids = {opt.id for opt in (q.options or []) if opt.isCorrect}

        if db_ans.questionType in (
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.TRUE_FALSE,
        ):
            if not selected_opt_ids:
                db_ans.marksAwarded = 0.0
                db_ans.isCorrect = Correctness.INCORRECT
                db_ans.gradingStatus = GradingStatus.AUTO_GRADED
            elif selected_opt_ids == correct_opt_ids:
                db_ans.marksAwarded = q_marks
                db_ans.isCorrect = Correctness.FULLY_CORRECT
                db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                total_marks_obtained += q_marks
            else:
                db_ans.marksAwarded = -penalty
                db_ans.isCorrect = Correctness.INCORRECT
                db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                total_marks_obtained -= penalty

        elif db_ans.questionType == QuestionType.MULTIPLE_SELECT:
            if not selected_opt_ids:
                db_ans.marksAwarded = 0.0
                db_ans.isCorrect = Correctness.INCORRECT
                db_ans.gradingStatus = GradingStatus.AUTO_GRADED
            else:
                wrong_selected = selected_opt_ids - correct_opt_ids
                right_selected = selected_opt_ids & correct_opt_ids
                c_count = len(correct_opt_ids)

                if wrong_selected:
                    db_ans.marksAwarded = -penalty
                    db_ans.isCorrect = Correctness.INCORRECT
                    db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                    total_marks_obtained -= penalty
                elif selected_opt_ids == correct_opt_ids:
                    db_ans.marksAwarded = q_marks
                    db_ans.isCorrect = Correctness.FULLY_CORRECT
                    db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                    total_marks_obtained += q_marks
                elif right_selected and c_count > 0:
                    partial_marks = round((len(right_selected) / c_count) * q_marks, 2)
                    db_ans.marksAwarded = partial_marks
                    db_ans.isCorrect = Correctness.PARTIALLY_CORRECT
                    db_ans.gradingStatus = GradingStatus.AUTO_GRADED
                    total_marks_obtained += partial_marks
                else:
                    db_ans.marksAwarded = 0.0
                    db_ans.isCorrect = Correctness.INCORRECT
                    db_ans.gradingStatus = GradingStatus.AUTO_GRADED

        elif db_ans.questionType in (QuestionType.SHORT_ANSWER, QuestionType.ESSAY):
            has_pending_subjective = True
            db_ans.gradingStatus = GradingStatus.PENDING

    final_marks = max(0.0, round(total_marks_obtained, 2))
    return final_marks, has_pending_subjective, answers


class TestGradingEngineUnit:
    """U13-U29: Detailed unit tests for the grading engine."""

    def test_mcq_all_correct(self):
        q = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_CHOICE,
            marks=4.0,
            options=[MockOption("o1", "A", True), MockOption("o2", "B", False)],
        )
        exam = MockExam(questions=[q])
        ans = [
            MockStudentExamAnswer(
                "a1", "q1", QuestionType.MULTIPLE_CHOICE, [MockSelectedOption("o1")]
            )
        ]

        total, subjective, graded_ans = grade_attempt_pure(exam, ans)
        assert total == 4.0
        assert subjective is False
        assert graded_ans[0].isCorrect == Correctness.FULLY_CORRECT
        assert graded_ans[0].marksAwarded == 4.0

    def test_mcq_wrong_no_negative_marking(self):
        q = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_CHOICE,
            marks=4.0,
            options=[MockOption("o1", "A", True), MockOption("o2", "B", False)],
        )
        exam = MockExam(negativeMarking=False, negativeMarks=0.0, questions=[q])
        ans = [
            MockStudentExamAnswer(
                "a1", "q1", QuestionType.MULTIPLE_CHOICE, [MockSelectedOption("o2")]
            )
        ]

        total, subjective, graded_ans = grade_attempt_pure(exam, ans)
        assert total == 0.0
        assert graded_ans[0].isCorrect == Correctness.INCORRECT
        assert graded_ans[0].marksAwarded == 0.0

    def test_mcq_wrong_with_negative_marking(self):
        q = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_CHOICE,
            marks=4.0,
            options=[MockOption("o1", "A", True), MockOption("o2", "B", False)],
        )
        exam = MockExam(negativeMarking=True, negativeMarks=1.0, questions=[q])
        ans = [
            MockStudentExamAnswer(
                "a1", "q1", QuestionType.MULTIPLE_CHOICE, [MockSelectedOption("o2")]
            )
        ]

        total, subjective, graded_ans = grade_attempt_pure(exam, ans)
        assert total == 0.0  # max(0, -1) = 0
        assert graded_ans[0].marksAwarded == -1.0
        assert graded_ans[0].isCorrect == Correctness.INCORRECT

    def test_mcq_unanswered_no_penalty(self):
        q = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_CHOICE,
            marks=4.0,
            options=[MockOption("o1", "A", True), MockOption("o2", "B", False)],
        )
        exam = MockExam(negativeMarking=True, negativeMarks=1.0, questions=[q])
        ans = [
            MockStudentExamAnswer("a1", "q1", QuestionType.MULTIPLE_CHOICE, [])
        ]  # No selection

        total, subjective, graded_ans = grade_attempt_pure(exam, ans)
        assert total == 0.0
        assert graded_ans[0].marksAwarded == 0.0
        assert graded_ans[0].isCorrect == Correctness.INCORRECT

    def test_true_false_correct_and_wrong(self):
        q1 = MockQuestion(
            id="q1",
            questionType=QuestionType.TRUE_FALSE,
            marks=2.0,
            options=[MockOption("o1", "True", True), MockOption("o2", "False", False)],
        )
        exam = MockExam(negativeMarking=True, negativeMarks=0.5, questions=[q1])

        # Correct
        ans_correct = [
            MockStudentExamAnswer(
                "a1", "q1", QuestionType.TRUE_FALSE, [MockSelectedOption("o1")]
            )
        ]
        total_c, _, _ = grade_attempt_pure(exam, ans_correct)
        assert total_c == 2.0

        # Wrong
        ans_wrong = [
            MockStudentExamAnswer(
                "a1", "q1", QuestionType.TRUE_FALSE, [MockSelectedOption("o2")]
            )
        ]
        total_w, _, graded_w = grade_attempt_pure(exam, ans_wrong)
        assert graded_w[0].marksAwarded == -0.5

    def test_msq_all_correct_selected(self):
        q = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_SELECT,
            marks=6.0,
            options=[
                MockOption("o1", "A", True),
                MockOption("o2", "B", True),
                MockOption("o3", "C", False),
            ],
        )
        exam = MockExam(questions=[q])
        ans = [
            MockStudentExamAnswer(
                "a1",
                "q1",
                QuestionType.MULTIPLE_SELECT,
                [MockSelectedOption("o1"), MockSelectedOption("o2")],
            )
        ]

        total, _, graded_ans = grade_attempt_pure(exam, ans)
        assert total == 6.0
        assert graded_ans[0].isCorrect == Correctness.FULLY_CORRECT
        assert graded_ans[0].marksAwarded == 6.0

    def test_msq_partial_correct_no_wrong(self):
        q = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_SELECT,
            marks=6.0,
            options=[
                MockOption("o1", "A", True),
                MockOption("o2", "B", True),
                MockOption("o3", "C", True),
                MockOption("o4", "D", False),
            ],
        )
        exam = MockExam(questions=[q])
        # Student selects 2 out of 3 correct options, 0 wrong
        ans = [
            MockStudentExamAnswer(
                "a1",
                "q1",
                QuestionType.MULTIPLE_SELECT,
                [MockSelectedOption("o1"), MockSelectedOption("o2")],
            )
        ]

        total, _, graded_ans = grade_attempt_pure(exam, ans)
        # (2/3) * 6.0 = 4.0
        assert total == 4.0
        assert graded_ans[0].isCorrect == Correctness.PARTIALLY_CORRECT
        assert graded_ans[0].marksAwarded == 4.0

    def test_msq_with_one_wrong_option_incurs_penalty(self):
        q = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_SELECT,
            marks=6.0,
            options=[
                MockOption("o1", "A", True),
                MockOption("o2", "B", True),
                MockOption("o3", "C", False),
            ],
        )
        exam = MockExam(negativeMarking=True, negativeMarks=2.0, questions=[q])
        # Student selects 1 correct + 1 wrong
        ans = [
            MockStudentExamAnswer(
                "a1",
                "q1",
                QuestionType.MULTIPLE_SELECT,
                [MockSelectedOption("o1"), MockSelectedOption("o3")],
            )
        ]

        total, _, graded_ans = grade_attempt_pure(exam, ans)
        assert graded_ans[0].isCorrect == Correctness.INCORRECT
        assert graded_ans[0].marksAwarded == -2.0

    def test_msq_empty_selection(self):
        q = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_SELECT,
            marks=6.0,
            options=[MockOption("o1", "A", True)],
        )
        exam = MockExam(negativeMarking=True, negativeMarks=2.0, questions=[q])
        ans = [MockStudentExamAnswer("a1", "q1", QuestionType.MULTIPLE_SELECT, [])]

        total, _, graded_ans = grade_attempt_pure(exam, ans)
        assert total == 0.0
        assert graded_ans[0].marksAwarded == 0.0

    def test_subjective_questions_flag_pending(self):
        q1 = MockQuestion(
            id="q1", questionType=QuestionType.SHORT_ANSWER, marks=5.0, options=[]
        )
        q2 = MockQuestion(
            id="q2", questionType=QuestionType.ESSAY, marks=10.0, options=[]
        )
        exam = MockExam(questions=[q1, q2])
        ans = [
            MockStudentExamAnswer(
                "a1",
                "q1",
                QuestionType.SHORT_ANSWER,
                textAnswer="Short text answer",
            ),
            MockStudentExamAnswer(
                "a2", "q2", QuestionType.ESSAY, textAnswer="Long essay answer..."
            ),
        ]

        total, has_subjective, graded_ans = grade_attempt_pure(exam, ans)
        assert has_subjective is True
        assert graded_ans[0].gradingStatus == GradingStatus.PENDING
        assert graded_ans[1].gradingStatus == GradingStatus.PENDING

    def test_section_level_negative_marking_override(self):
        sec_a = MockSection(
            "sec_a", "Section A", negativeMarking=True, negativeMarks=2.5
        )
        q1 = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_CHOICE,
            marks=4.0,
            options=[MockOption("o1", "A", True), MockOption("o2", "B", False)],
            examSection=sec_a,
        )
        # Exam has 1.0 penalty, but Section A has 2.5 penalty
        exam = MockExam(
            negativeMarking=True,
            negativeMarks=1.0,
            questions=[q1],
            sections=[sec_a],
        )
        ans = [
            MockStudentExamAnswer(
                "a1", "q1", QuestionType.MULTIPLE_CHOICE, [MockSelectedOption("o2")]
            )
        ]

        _, _, graded_ans = grade_attempt_pure(exam, ans)
        assert graded_ans[0].marksAwarded == -2.5

    def test_total_marks_never_negative(self):
        q1 = MockQuestion(
            id="q1",
            questionType=QuestionType.MULTIPLE_CHOICE,
            marks=4.0,
            options=[MockOption("o1", "A", True), MockOption("o2", "B", False)],
        )
        exam = MockExam(negativeMarking=True, negativeMarks=10.0, questions=[q1])
        ans = [
            MockStudentExamAnswer(
                "a1", "q1", QuestionType.MULTIPLE_CHOICE, [MockSelectedOption("o2")]
            )
        ]

        total, _, graded_ans = grade_attempt_pure(exam, ans)
        assert graded_ans[0].marksAwarded == -10.0
        assert total == 0.0  # Clamped to 0
