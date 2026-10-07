"""AI prompts package."""

from app.ai.prompts.grading import (
    SYSTEM_AI_GRADING_PROMPT,
    build_grading_user_prompt,
)
from app.ai.prompts.question_paper import (
    SYSTEM_EXTRACTION_PROMPT,
    build_extraction_user_prompt,
)

__all__ = [
    "SYSTEM_EXTRACTION_PROMPT",
    "build_extraction_user_prompt",
    "SYSTEM_AI_GRADING_PROMPT",
    "build_grading_user_prompt",
]
