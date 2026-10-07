"""Dedicated Cohere API client with structured outputs, bounded retries, and safe error handling."""

import asyncio
import logging
import random
import time
from typing import Any

import cohere
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class CohereClientError(Exception):
    """Base exception for Cohere client operations."""

    pass


class CohereConfigurationError(CohereClientError):
    """Raised when Cohere API key or necessary configuration is missing."""

    pass


class CohereRateLimitError(CohereClientError):
    """Raised when rate limits are exceeded after retries."""

    pass


class CohereTimeoutError(CohereClientError):
    """Raised when API call times out after retries."""

    pass


class CohereAPIError(CohereClientError):
    """Raised for non-retryable or fatal Cohere API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _sanitize_schema_for_cohere(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively removes schema constraints unsupported by Cohere ClientV2 JSON schema validator."""
    if not isinstance(schema, dict):
        return schema
    import copy

    clean = copy.deepcopy(schema)

    def _strip(d: Any) -> None:
        if isinstance(d, dict):
            for k in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
                d.pop(k, None)
            for v in d.values():
                _strip(v)
        elif isinstance(d, list):
            for item in d:
                _strip(item)

    _strip(clean)
    return clean


class CohereClient:
    """Wrapper client for Cohere ClientV2 with structured JSON outputs and retry resiliency."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_retries: int | None = None,
        timeout: float | None = None,
    ):
        self.api_key = api_key or settings.COHERE_API_KEY
        self.model = model or settings.COHERE_MODEL
        self.max_retries = (
            max_retries
            if max_retries is not None
            else settings.QUESTION_IMPORT_MAX_RETRIES
        )
        self.timeout = (
            timeout
            if timeout is not None
            else settings.QUESTION_IMPORT_TIMEOUT_SECONDS
        )
        self._client: cohere.ClientV2 | None = None

    def _get_client(self) -> cohere.ClientV2:
        if not self.api_key:
            raise CohereConfigurationError(
                "Cohere API key is not configured. Please set COHERE_API_KEY in your environment."
            )
        if self._client is None:
            self._client = cohere.ClientV2(
                api_key=self.api_key,
                timeout=self.timeout,
            )
        return self._client

    async def extract_structured_json(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        temperature: float = 0.0,
    ) -> tuple[str, dict[str, Any]]:
        """Call Cohere Chat endpoint with JSON schema structured output and bounded retries.

        Returns:
            Tuple of (raw_json_string, usage_metrics)
        """
        client = self._get_client()

        response_format = {
            "type": "json_object",
            "schema": _sanitize_schema_for_cohere(schema),
        }

        retry_count = 0
        base_delay = 1.0
        start_time = time.time()

        while True:
            try:
                logger.info(
                    "Calling Cohere Chat API with model=%s, retry=%d",
                    self.model,
                    retry_count,
                )

                # ClientV2 is synchronous, wrap in asyncio.to_thread for async non-blocking execution
                def _invoke():
                    return client.chat(
                        model=self.model,
                        messages=messages,
                        response_format=response_format,
                        temperature=temperature,
                    )

                response = await asyncio.to_thread(_invoke)
                duration_ms = round((time.time() - start_time) * 1000, 2)

                # Extract content
                text_content = ""
                if (
                    response
                    and response.message
                    and response.message.content
                    and len(response.message.content) > 0
                ):
                    text_content = response.message.content[0].text
                else:
                    raise CohereAPIError("Cohere returned an empty response message")

                # Extract usage metadata safely
                usage_metrics: dict[str, Any] = {
                    "model": self.model,
                    "duration_ms": duration_ms,
                    "retries": retry_count,
                }

                if hasattr(response, "usage") and response.usage:
                    if hasattr(response.usage, "tokens"):
                        usage_metrics["input_tokens"] = getattr(
                            response.usage.tokens, "input_tokens", None
                        )
                        usage_metrics["output_tokens"] = getattr(
                            response.usage.tokens, "output_tokens", None
                        )
                    elif hasattr(response.usage, "billed_units"):
                        usage_metrics["input_tokens"] = getattr(
                            response.usage.billed_units, "input_tokens", None
                        )
                        usage_metrics["output_tokens"] = getattr(
                            response.usage.billed_units, "output_tokens", None
                        )

                logger.info(
                    "Cohere extraction completed in %sms with %d retries",
                    duration_ms,
                    retry_count,
                )
                return text_content, usage_metrics

            except (
                cohere.TooManyRequestsError,
                cohere.InternalServerError,
                cohere.ServiceUnavailableError,
                cohere.GatewayTimeoutError,
                httpx.TimeoutException,
                httpx.NetworkError,
                TimeoutError,
            ) as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    logger.error(
                        "Exceeded max retries (%d) calling Cohere: %s",
                        self.max_retries,
                        type(e).__name__,
                    )
                    if isinstance(e, cohere.TooManyRequestsError):
                        raise CohereRateLimitError(
                            "Cohere rate limit reached. Please try again later."
                        ) from e
                    if isinstance(e, (httpx.TimeoutException, TimeoutError, cohere.GatewayTimeoutError)):
                        raise CohereTimeoutError(
                            "Cohere API call timed out. Please try again."
                        ) from e
                    raise CohereAPIError(
                        f"Cohere service unavailable: {type(e).__name__}"
                    ) from e

                # Exponential backoff with jitter
                delay = base_delay * (2 ** (retry_count - 1)) + random.uniform(0.1, 0.5)
                logger.warning(
                    "Transient error %s calling Cohere. Retrying in %.2fs (attempt %d/%d)...",
                    type(e).__name__,
                    delay,
                    retry_count,
                    self.max_retries,
                )
                await asyncio.sleep(delay)

            except (
                cohere.BadRequestError,
                cohere.UnauthorizedError,
                cohere.ForbiddenError,
                cohere.UnprocessableEntityError,
            ) as e:
                # Fatal non-retryable errors
                status_code = getattr(e, "status_code", None)
                logger.error(
                    "Non-retryable Cohere API error (status=%s): %s",
                    status_code,
                    type(e).__name__,
                )
                raise CohereAPIError(
                    f"Cohere API request error: {type(e).__name__}",
                    status_code=status_code,
                ) from e

            except Exception as e:
                # Check if it's already one of our custom exceptions
                if isinstance(e, CohereClientError):
                    raise
                logger.exception("Unexpected error calling Cohere: %s", type(e).__name__)
                raise CohereAPIError(
                    f"Unexpected Cohere error occurred: {type(e).__name__}"
                ) from e
