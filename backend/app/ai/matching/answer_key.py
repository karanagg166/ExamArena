"""Deterministic question matching engine for answer key imports."""

import logging
import re
from typing import Any

from app.ai.schemas.answer_key import (
    ExtractedAnswer,
    ExtractedAnswerKey,
    MatchedAnswer,
    MatchedAnswerKey,
    MatchStatus,
)

logger = logging.getLogger(__name__)


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to read attribute from SQLAlchemy/SQLModel model, Pydantic model, or dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def parse_question_number_from_reference(ref: str | None) -> int | None:
    """Extracts integer question number from strings like '1', 'Q2', 'Question 3', '4(a)', '#5'."""
    if not ref:
        return None
    cleaned = ref.strip()
    match = re.search(r"(?:q(?:uestion)?\s*|\#\s*)?(\d+)", cleaned, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def calculate_text_similarity(text1: str | None, text2: str | None) -> float:
    """Calculates token-level Jaccard similarity between two text snippets."""
    if not text1 or not text2:
        return 0.0

    def tokenize(s: str) -> set[str]:
        words = re.findall(r"\b\w{3,}\b", s.lower())
        return set(words)

    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union > 0 else 0.0


def map_selected_option(
    options: list[Any],
    selected_option: str | None,
    selected_option_text: str | None,
) -> tuple[str | None, str | None]:
    """Maps extracted option identifier ('A', 'B', '1', 'True', etc.) or option text to option.id.

    Returns:
        Tuple of (matched_option_id, warning_message_or_none)
    """
    if not options:
        return None, "No options found on target exam question."

    value = selected_option or selected_option_text
    if not value or not value.strip():
        return None, "No selected option supplied."
    sel = value.strip().casefold()

    # Match complete text, never a substring or a letter inside arbitrary text.
    text_matches = [
        str(_get_attr(opt, "id"))
        for opt in options
        if (_get_attr(opt, "text") or "").strip().casefold() == sel
    ]
    if len(text_matches) == 1:
        return text_matches[0], None
    if len(text_matches) > 1:
        return None, f"Option '{value}' matches multiple option texts."

    sel = sel.strip("()[] .")
    if sel in ("true", "t", "false", "f"):
        aliases = ("true", "t", "yes") if sel in ("true", "t") else ("false", "f", "no")
        matches = [
            str(_get_attr(opt, "id"))
            for opt in options
            if (_get_attr(opt, "text") or "").strip().casefold() in aliases
        ]
        if len(matches) == 1:
            return matches[0], None
        return None, f"Could not uniquely resolve logical option '{value}'."

    target_num = None
    if re.fullmatch(r"[a-z]", sel):
        target_num = ord(sel) - ord("a") + 1
    elif re.fullmatch(r"\d+", sel):
        target_num = int(sel)
    if target_num is not None:
        matches = [
            str(_get_attr(opt, "id"))
            for idx, opt in enumerate(options, start=1)
            if _get_attr(opt, "optionNumber", idx) == target_num
        ]
        if len(matches) == 1:
            return matches[0], None
        if not matches and 1 <= target_num <= len(options):
            return str(_get_attr(options[target_num - 1], "id")), None
        return (
            None,
            f"Option '{value}' does not correspond uniquely to any of the {len(options)} options.",
        )
    return None, f"Could not resolve option label '{value}'."


def normalize_selected_options(values: list[str]) -> list[str]:
    """Split combined labels while preserving full option texts and selection order."""
    normalized: list[str] = []
    label = r"(?:[a-z]|\d+|true|false)"
    for value in values:
        parts = re.split(r"\s*(?:,|/|\band\b)\s*", value.strip(), flags=re.IGNORECASE)
        if not all(
            re.fullmatch(label, p.strip("()[] ."), re.IGNORECASE) for p in parts
        ):
            parts = [value]
        for part in parts:
            token = part.strip().casefold()
            label_token = token.strip("()[] .")
            if re.fullmatch(label, label_token, re.IGNORECASE):
                token = label_token
            token = {"t": "true", "f": "false"}.get(token, token)
            if token not in normalized:
                normalized.append(token)
    return normalized


def match_extracted_answer_key(
    extracted: ExtractedAnswerKey,
    exam_questions: list[Any],
    exam_id: str,
    import_id: str | None = None,
) -> MatchedAnswerKey:
    """Matches an extracted answer key against existing exam questions deterministically."""
    matched_answers: list[MatchedAnswer] = []
    question_by_num: dict[int, list[Any]] = {}
    question_by_id: dict[str, Any] = {}

    for q in exam_questions:
        q_id = str(_get_attr(q, "id"))
        question_by_id[q_id] = q
        q_num = _get_attr(q, "questionNumber")
        if q_num is not None:
            question_by_num.setdefault(int(q_num), []).append(q)

    # First pass: match each answer
    for ans in extracted.answers:
        parsed_num = parse_question_number_from_reference(ans.question_reference)
        warnings: list[str] = list(ans.warnings)

        matched_q: Any | None = None
        status = MatchStatus.UNMATCHED
        confidence = 0.0
        reason: str | None = None
        candidates: list[str] = []

        # 1. Match by extracted question number
        if parsed_num is not None and parsed_num in question_by_num:
            matching_qs = question_by_num[parsed_num]
            if len(matching_qs) == 1:
                matched_q = matching_qs[0]
                status = MatchStatus.MATCHED
                confidence = 0.95
                reason = f"Exact question number match ({parsed_num})"
            else:
                # Multiple questions have this number (e.g. across sections)
                candidates = [str(_get_attr(q, "id")) for q in matching_qs]
                # Try disambiguating using text snippet if available
                if ans.question_text_snippet:
                    best_q = None
                    best_sim = 0.0
                    for candidate in matching_qs:
                        sim = calculate_text_similarity(
                            ans.question_text_snippet, _get_attr(candidate, "text")
                        )
                        if sim > best_sim:
                            best_sim = sim
                            best_q = candidate
                    if best_q and best_sim > 0.4:
                        matched_q = best_q
                        status = MatchStatus.MATCHED
                        confidence = 0.85
                        reason = f"Question number match ({parsed_num}) resolved via text similarity ({best_sim:.2f})"
                    else:
                        status = MatchStatus.AMBIGUOUS
                        reason = f"Multiple questions found with number {parsed_num}."
                else:
                    status = MatchStatus.AMBIGUOUS
                    reason = f"Multiple questions found with number {parsed_num}."

        # 2. If still unmatched, try text similarity across all questions
        if status == MatchStatus.UNMATCHED and ans.question_text_snippet:
            best_q = None
            best_sim = 0.0
            second_sim = 0.0
            for q in exam_questions:
                sim = calculate_text_similarity(
                    ans.question_text_snippet, _get_attr(q, "text")
                )
                if sim > best_sim:
                    second_sim = best_sim
                    best_sim = sim
                    best_q = q
                elif sim > second_sim:
                    second_sim = sim

            if best_q and best_sim >= 0.5 and (best_sim - second_sim) > 0.15:
                matched_q = best_q
                status = MatchStatus.MATCHED
                confidence = min(0.9, best_sim)
                reason = f"Matched by question text snippet similarity ({best_sim:.2f})"
            elif best_q and best_sim >= 0.4:
                status = MatchStatus.AMBIGUOUS
                candidates = [str(_get_attr(best_q, "id"))]
                reason = f"Ambiguous text match similarity ({best_sim:.2f})"

        if status == MatchStatus.UNMATCHED and not reason:
            reason = f"No exam question matched reference '{ans.question_reference}'"

        # Prepare matched answer record
        matched_option_ids: list[str] = []
        matched_q_id: str | None = None
        matched_q_num: int | None = None
        matched_q_text: str | None = None
        matched_q_type: str | None = None

        if matched_q is not None:
            matched_q_id = str(_get_attr(matched_q, "id"))
            matched_q_num = _get_attr(matched_q, "questionNumber")
            matched_q_text = _get_attr(matched_q, "text")
            q_type = _get_attr(matched_q, "questionType")
            matched_q_type = str(q_type) if q_type else None

            # Option matching for objective questions
            q_options = _get_attr(matched_q, "options") or []
            if matched_q_type in ("MULTIPLE_CHOICE", "MULTIPLE_SELECT", "TRUE_FALSE"):
                selections = normalize_selected_options(ans.selected_options)
                option_warnings = []
                for selection in selections:
                    opt_id, opt_warning = map_selected_option(
                        q_options, selection, None
                    )
                    if opt_warning:
                        option_warnings.append(opt_warning)
                    elif opt_id and opt_id not in matched_option_ids:
                        matched_option_ids.append(opt_id)
                if not selections:
                    option_warnings.append(
                        "No selected options supplied for objective answer."
                    )
                if (
                    matched_q_type in ("MULTIPLE_CHOICE", "TRUE_FALSE")
                    and len(selections) != 1
                ):
                    option_warnings.append(
                        "This question requires exactly one selected option."
                    )
                if option_warnings:
                    warnings.extend(option_warnings)
                    status = MatchStatus.AMBIGUOUS
                    reason = "Objective answer requires review: " + " ".join(
                        option_warnings
                    )
                    matched_option_ids = []

            # Validate rubric totals against question marks
            if ans.rubric:
                rubric_total = sum(c.marks for c in ans.rubric)
                q_marks = _get_attr(matched_q, "marks")
                if q_marks is not None and rubric_total > q_marks:
                    warnings.append(
                        f"Rubric total marks ({rubric_total}) exceeds question marks ({q_marks})."
                    )

        matched_answers.append(
            MatchedAnswer(
                question_reference=ans.question_reference,
                question_text_snippet=ans.question_text_snippet,
                selected_options=ans.selected_options,
                reference_answer=ans.reference_answer,
                explanation=ans.explanation,
                rubric=ans.rubric,
                marks=ans.marks,
                confidence=ans.confidence,
                warnings=warnings,
                status=status,
                matched_question_id=matched_q_id,
                matched_question_number=matched_q_num,
                matched_question_text=matched_q_text,
                matched_question_type=matched_q_type,
                matched_option_ids=matched_option_ids,
                match_confidence=confidence,
                match_reason=reason,
                candidate_question_ids=candidates,
            )
        )

    # Second pass: detect duplicate assignments to the same question
    assigned_counts: dict[str, list[int]] = {}
    for idx, ma in enumerate(matched_answers):
        if ma.status == MatchStatus.MATCHED and ma.matched_question_id:
            assigned_counts.setdefault(ma.matched_question_id, []).append(idx)

    for q_id, indices in assigned_counts.items():
        if len(indices) > 1:
            for idx in indices:
                item = matched_answers[idx]
                item.status = MatchStatus.AMBIGUOUS
                item.warnings.append(
                    f"Multiple answer key items matched question #{item.matched_question_number}."
                )
                item.match_reason = (
                    f"Duplicate match on question #{item.matched_question_number}"
                )

    matched_count = sum(1 for a in matched_answers if a.status == MatchStatus.MATCHED)
    ambiguous_count = sum(
        1 for a in matched_answers if a.status == MatchStatus.AMBIGUOUS
    )
    unmatched_count = sum(
        1 for a in matched_answers if a.status == MatchStatus.UNMATCHED
    )

    return MatchedAnswerKey(
        import_id=import_id,
        exam_id=exam_id,
        matched_count=matched_count,
        ambiguous_count=ambiguous_count,
        unmatched_count=unmatched_count,
        total_answers=len(matched_answers),
        answers=matched_answers,
        warnings=extracted.warnings,
    )
