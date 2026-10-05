"""Worker settings and ARQ job definitions for question paper imports."""

import logging
from typing import Any

from app.core.config import settings
from app.imports.service import process_question_import

logger = logging.getLogger(__name__)


async def run_import_job(ctx: dict[str, Any], import_id: str) -> None:
    """ARQ job entry point for processing a question paper import."""
    logger.info("ARQ executing import job for import_id: %s", import_id)
    await process_question_import(import_id)


class WorkerSettings:
    """ARQ worker configuration."""

    functions = [run_import_job]
    redis_settings = settings.REDIS_URL
    max_jobs = 10
    job_timeout = 300
