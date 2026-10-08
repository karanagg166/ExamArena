"""Unit tests for CohereClient (mocked, contract, retry resilience)."""

from unittest.mock import MagicMock, patch

import cohere
import httpx
import pytest

from app.ai.clients.cohere_client import (
    CohereAPIError,
    CohereClient,
    CohereConfigurationError,
    CohereRateLimitError,
    CohereTimeoutError,
)


def test_cohere_missing_api_key_raises_configuration_error():
    with patch("app.ai.clients.cohere_client.settings.COHERE_API_KEY", None):
        client = CohereClient(api_key=None)
        with pytest.raises(CohereConfigurationError):
            client._get_client()


@pytest.mark.asyncio
async def test_cohere_extract_structured_json_success():
    client = CohereClient(api_key="fake-test-key", max_retries=2)

    mock_chat_response = MagicMock()
    mock_chat_response.message.content = [MagicMock(text='{"title": "Test Paper", "questions": []}')]
    mock_chat_response.usage.tokens.input_tokens = 100
    mock_chat_response.usage.tokens.output_tokens = 50

    with patch("cohere.ClientV2") as mock_v2:
        mock_v2.return_value.chat.return_value = mock_chat_response
        client._client = mock_v2.return_value

        res_text, metrics = await client.extract_structured_json(
            messages=[{"role": "user", "content": "extract"}],
            schema={"type": "object"},
        )

        assert '{"title": "Test Paper"' in res_text
        assert metrics["input_tokens"] == 100
        assert metrics["output_tokens"] == 50
        assert metrics["retries"] == 0


@pytest.mark.asyncio
async def test_cohere_rate_limit_retry_then_success():
    client = CohereClient(api_key="fake-test-key", max_retries=3)

    mock_chat_response = MagicMock()
    mock_chat_response.message.content = [MagicMock(text='{"title": "Success After Retry"}')]
    mock_chat_response.usage.tokens.input_tokens = 50
    mock_chat_response.usage.tokens.output_tokens = 20

    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise cohere.TooManyRequestsError(body={"message": "Rate limit reached"})
        return mock_chat_response

    mock_co_instance = MagicMock()
    mock_co_instance.chat.side_effect = side_effect
    client._client = mock_co_instance

    with patch("asyncio.sleep", return_value=None):
        res_text, metrics = await client.extract_structured_json(
            messages=[{"role": "user", "content": "extract"}],
            schema={"type": "object"},
        )

    assert "Success After Retry" in res_text
    assert metrics["retries"] == 1
    assert call_count == 2


@pytest.mark.asyncio
async def test_cohere_rate_limit_exceeded_raises_error():
    client = CohereClient(api_key="fake-test-key", max_retries=2)

    mock_co_instance = MagicMock()
    mock_co_instance.chat.side_effect = cohere.TooManyRequestsError(
        body={"message": "Rate limit reached"}
    )
    client._client = mock_co_instance

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(CohereRateLimitError):
            await client.extract_structured_json(
                messages=[{"role": "user", "content": "extract"}],
                schema={"type": "object"},
            )


@pytest.mark.asyncio
async def test_cohere_timeout_retry_and_exceeded():
    client = CohereClient(api_key="fake-test-key", max_retries=1)

    mock_co_instance = MagicMock()
    mock_co_instance.chat.side_effect = httpx.TimeoutException("Read timeout")
    client._client = mock_co_instance

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(CohereTimeoutError):
            await client.extract_structured_json(
                messages=[{"role": "user", "content": "extract"}],
                schema={"type": "object"},
            )


@pytest.mark.asyncio
async def test_cohere_non_retryable_400_bad_request_fails_immediately():
    client = CohereClient(api_key="fake-test-key", max_retries=3)

    mock_co_instance = MagicMock()
    mock_co_instance.chat.side_effect = cohere.BadRequestError(
        body={"message": "Bad Schema Request"}
    )
    client._client = mock_co_instance

    with patch("asyncio.sleep", return_value=None) as mock_sleep:
        with pytest.raises(CohereAPIError):
            await client.extract_structured_json(
                messages=[{"role": "user", "content": "extract"}],
                schema={"type": "object"},
            )
        # Verify no sleeps/retries were performed for a 400 error
        mock_sleep.assert_not_called()

