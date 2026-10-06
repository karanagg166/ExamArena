"""Unit tests for Answer Key deterministic matching engine."""

import pytest

from app.ai.matching.answer_key import (
    calculate_text_similarity,
    map_selected_option,
    match_extracted_answer_key,
    parse_question_number_from_reference,
)
from app.ai.schemas.answer_key import (
    ExtractedAnswer,
    ExtractedAnswerKey,
    MatchStatus,
    RubricCriterion,
)


def test_parse_question_number():
    assert parse_question_number_from_reference("1") == 1
    assert parse_question_number_from_reference("Q2") == 2
    assert parse_question_number_from_reference("Question 15") == 15
    assert parse_question_number_from_reference("1(a)") == 1
    assert parse_question_number_from_reference("#4") == 4
    assert parse_question_number_from_reference("Section B Q.7") == 7
    assert parse_question_number_from_reference("NoNumberHere") is None
    assert parse_question_number_from_reference("") is None
    assert parse_question_number_from_reference(None) is None


def test_calculate_text_similarity():
    sim = calculate_text_similarity(
        "Explain the process of photosynthesis in green plants",
        "Explain photosynthesis in plants and chloroplasts",
    )
    assert sim > 0.35

    zero_sim = calculate_text_similarity(
        "Calculate force and mass", "Shakespeare hamlet poetry"
    )
    assert zero_sim == 0.0


def test_map_selected_option_letters():
    options = [
        {"id": "opt_a", "optionNumber": 1, "text": "Mercury"},
        {"id": "opt_b", "optionNumber": 2, "text": "Venus"},
        {"id": "opt_c", "optionNumber": 3, "text": "Earth"},
        {"id": "opt_d", "optionNumber": 4, "text": "Mars"},
    ]

    opt_id, warn = map_selected_option(options, "A", None)
    assert opt_id == "opt_a"
    assert warn is None

    opt_id, warn = map_selected_option(options, "(B)", None)
    assert opt_id == "opt_b"
    assert warn is None

    opt_id, warn = map_selected_option(options, "4", None)
    assert opt_id == "opt_d"
    assert warn is None

    # Out of range option letter
    opt_id, warn = map_selected_option(options, "E", None)
    assert opt_id is None
    assert "does not correspond" in warn


def test_map_selected_option_true_false():
    options = [
        {"id": "opt_t", "optionNumber": 1, "text": "True"},
        {"id": "opt_f", "optionNumber": 2, "text": "False"},
    ]

    opt_id, warn = map_selected_option(options, "True", None)
    assert opt_id == "opt_t"

    opt_id, warn = map_selected_option(options, "F", None)
    assert opt_id == "opt_f"


def test_map_selected_option_by_text():
    options = [
        {"id": "opt_1", "optionNumber": 1, "text": "Mitochondria"},
        {"id": "opt_2", "optionNumber": 2, "text": "Chloroplast"},
    ]

    opt_id, warn = map_selected_option(options, None, "Chloroplast")
    assert opt_id == "opt_2"


def test_match_extracted_answer_key_full_flow():
    exam_questions = [
        {
            "id": "q1",
            "questionNumber": 1,
            "text": "What is the powerhouse of the cell?",
            "questionType": "MULTIPLE_CHOICE",
            "marks": 2,
            "options": [
                {"id": "opt1_a", "optionNumber": 1, "text": "Nucleus"},
                {"id": "opt1_b", "optionNumber": 2, "text": "Mitochondria"},
            ],
        },
        {
            "id": "q2",
            "questionNumber": 2,
            "text": "Explain Newton's second law of motion.",
            "questionType": "SHORT_ANSWER",
            "marks": 3,
            "options": [],
        },
    ]

    extracted_key = ExtractedAnswerKey(
        title="Science Key",
        answers=[
            ExtractedAnswer(
                question_reference="Q1",
                selected_option="B",
                explanation="Mitochondria produces ATP",
            ),
            ExtractedAnswer(
                question_reference="2",
                reference_answer="F = ma. Force equals mass times acceleration.",
                rubric=[
                    RubricCriterion(criterion="Formula F=ma", marks=1.0),
                    RubricCriterion(criterion="Statement and units", marks=2.0),
                ],
            ),
            ExtractedAnswer(
                question_reference="Q99",
                selected_option="A",
            ),
        ],
    )

    matched = match_extracted_answer_key(
        extracted=extracted_key,
        exam_questions=exam_questions,
        exam_id="exam_001",
    )

    assert matched.total_answers == 3
    assert matched.matched_count == 2
    assert matched.unmatched_count == 1

    ans1 = matched.answers[0]
    assert ans1.status == MatchStatus.MATCHED
    assert ans1.matched_question_id == "q1"
    assert ans1.matched_option_ids == ["opt1_b"]
    assert ans1.explanation == "Mitochondria produces ATP"

    ans2 = matched.answers[1]
    assert ans2.status == MatchStatus.MATCHED
    assert ans2.matched_question_id == "q2"
    assert ans2.reference_answer.startswith("F = ma")
    assert len(ans2.rubric) == 2

    ans3 = matched.answers[2]
    assert ans3.status == MatchStatus.UNMATCHED


def test_rubric_total_exceeding_question_marks_warning():
    exam_questions = [
        {
            "id": "q1",
            "questionNumber": 1,
            "text": "Define velocity.",
            "questionType": "SHORT_ANSWER",
            "marks": 2,
            "options": [],
        }
    ]

    extracted = ExtractedAnswerKey(
        answers=[
            ExtractedAnswer(
                question_reference="1",
                reference_answer="Rate of change of displacement",
                rubric=[
                    RubricCriterion(criterion="Definition", marks=2.0),
                    RubricCriterion(criterion="SI Units", marks=1.5),
                ],
            )
        ]
    )

    matched = match_extracted_answer_key(extracted, exam_questions, "exam_1")
    assert matched.answers[0].status == MatchStatus.MATCHED
    assert any("exceeds question marks" in w for w in matched.answers[0].warnings)


@pytest.mark.parametrize(
    "kind,values,expected",
    [
        ("MULTIPLE_SELECT", ["A,C"], ["a", "c"]),
        ("MULTIPLE_SELECT", ["A, C, D"], ["a", "c", "d"]),
        ("MULTIPLE_SELECT", ["A / C"], ["a", "c"]),
        ("MULTIPLE_SELECT", ["A and C"], ["a", "c"]),
        ("MULTIPLE_SELECT", ["a", "c"], ["a", "c"]),
        ("MULTIPLE_SELECT", ["A.", "(C)"], ["a", "c"]),
        ("MULTIPLE_SELECT", ["1", "3"], ["a", "c"]),
        ("MULTIPLE_SELECT", ["Mercury", "Earth"], ["a", "c"]),
        ("MULTIPLE_SELECT", ["A", "A", "C"], ["a", "c"]),
        ("MULTIPLE_SELECT", ["A,A,C"], ["a", "c"]),
        ("MULTIPLE_SELECT", ["A", "X"], None),
        ("MULTIPLE_SELECT", ["A", "unknown text"], None),
        ("MULTIPLE_SELECT", [], None),
        ("MULTIPLE_SELECT", ["A", ""], None),
        ("MULTIPLE_CHOICE", ["A", "C"], None),
        ("MULTIPLE_CHOICE", ["B"], ["b"]),
        ("TRUE_FALSE", ["T"], ["a"]),
        ("TRUE_FALSE", ["F"], ["b"]),
        ("TRUE_FALSE", ["TRUE"], ["a"]),
        ("TRUE_FALSE", ["false"], ["b"]),
        ("TRUE_FALSE", ["T", "F"], None),
        ("SHORT_ANSWER", [], []),
        ("ESSAY", [], []),
    ],
)
def test_plural_option_matching(kind, values, expected):
    texts = (
        ["True", "False"]
        if kind == "TRUE_FALSE"
        else ["Mercury", "Venus", "Earth", "Mars"]
    )
    question = dict(
        id="q",
        questionNumber=1,
        questionType=kind,
        marks=5,
        options=[
            dict(id=chr(97 + i), optionNumber=i + 1, text=t)
            for i, t in enumerate(texts)
        ],
    )
    result = match_extracted_answer_key(
        ExtractedAnswerKey(
            answers=[ExtractedAnswer(question_reference="1", selected_options=values)]
        ),
        [question],
        "exam",
    )
    answer = result.answers[0]
    assert answer.status == (
        MatchStatus.AMBIGUOUS if expected is None else MatchStatus.MATCHED
    )
    assert answer.matched_option_ids == (expected or [])
    assert result.ambiguous_count == int(expected is None)


@pytest.mark.parametrize(
    "value", ["Water (H2O)", "An explanation.", "(Full option text)", "Salt and pepper"]
)
def test_option_text_punctuation_is_preserved(value):
    question = dict(
        id="q",
        questionNumber=1,
        questionType="MULTIPLE_SELECT",
        options=[
            dict(id="text-option", optionNumber=1, text=value),
            dict(id="other-option", optionNumber=2, text="Other"),
        ],
    )
    result = match_extracted_answer_key(
        ExtractedAnswerKey(
            answers=[ExtractedAnswer(question_reference="1", selected_options=[value])]
        ),
        [question],
        "exam",
    )
    assert result.answers[0].status == MatchStatus.MATCHED
    assert result.answers[0].matched_option_ids == ["text-option"]
