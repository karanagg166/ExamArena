"""AI prompts package."""

from app.ai.prompts.question_paper import (
    SYSTEM_EXTRACTION_PROMPT,
    build_extraction_user_prompt,
)

__all__ = ["SYSTEM_EXTRACTION_PROMPT", "build_extraction_user_prompt"]
