"""Unit tests for CloudinaryStorageProvider and StorageProvider abstraction."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.storage.base import (
    StorageConfigurationError,
    StorageDeleteError,
    StorageReadError,
    StorageUploadError,
    StoredFile,
)
from app.storage.cloudinary import CloudinaryStorageProvider
from app.storage.local import LocalStorageProvider
from app.storage.service import get_storage_provider


@pytest.mark.asyncio
async def test_local_storage_provider_saves_and_retrieves(tmp_path):
    provider = LocalStorageProvider(base_path=str(tmp_path))

    data = b"Hello local file storage"
    res = await provider.save_file(content=data, extension=".txt", directory="test_dir")

    assert isinstance(res, StoredFile)
    assert res.provider == "local"
    assert res.key.endswith(".txt")
    assert str(res) == res.key  # Backwards compatibility check

    # Retrieve
    retrieved = await provider.get_file(res.key)
    assert retrieved == data

    # Delete
    deleted = await provider.delete_file(res.key)
    assert deleted is True

    # Delete again returns False (doesn't crash)
    assert await provider.delete_file(res.key) is False


def test_cloudinary_provider_raises_when_credentials_missing(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.CLOUDINARY_CLOUDNAME", None)
    monkeypatch.setattr("app.core.config.settings.CLOUDINARY_APIKEY", None)
    monkeypatch.setattr("app.core.config.settings.CLOUDINARY_APISECRET", None)
    provider = CloudinaryStorageProvider(
        cloud_name="", api_key="key", api_secret="secret"
    )
    with pytest.raises(StorageConfigurationError) as exc:
        provider._ensure_configured()
    assert "credentials are not properly configured" in str(exc.value)


@pytest.mark.asyncio
async def test_cloudinary_save_pdf_uses_raw_resource_type():
    provider = CloudinaryStorageProvider(
        cloud_name="test_cloud", api_key="test_key", api_secret="test_secret"
    )

    mock_upload_response = {
        "public_id": "examarena/test_dir/abc-123.pdf",
        "secure_url": "https://res.cloudinary.com/test_cloud/raw/upload/v1/examarena/test_dir/abc-123.pdf",
        "bytes": 100,
        "format": "pdf",
        "resource_type": "raw",
    }

    with patch("cloudinary.uploader.upload", return_value=mock_upload_response) as mock_upload:
        stored = await provider.save_file(
            content=b"%PDF-1.4 mock pdf data",
            extension=".pdf",
            directory="test_dir",
        )

        assert mock_upload.called
        call_kwargs = mock_upload.call_args[1]
        assert call_kwargs["resource_type"] == "raw"
        assert "examarena/test_dir" in call_kwargs["folder"]

        assert stored.provider == "cloudinary"
        assert stored.resource_type == "raw"
        assert stored.url == mock_upload_response["secure_url"]
        assert stored.key == mock_upload_response["public_id"]


@pytest.mark.asyncio
async def test_cloudinary_save_image_uses_image_resource_type():
    provider = CloudinaryStorageProvider(
        cloud_name="test_cloud", api_key="test_key", api_secret="test_secret"
    )

    mock_upload_response = {
        "public_id": "examarena/test_dir/img-123",
        "secure_url": "https://res.cloudinary.com/test_cloud/image/upload/v1/examarena/test_dir/img-123.png",
        "bytes": 50,
        "format": "png",
        "resource_type": "image",
    }

    with patch("cloudinary.uploader.upload", return_value=mock_upload_response) as mock_upload:
        stored = await provider.save_file(
            content=b"\x89PNG\r\n\x1a\n mock image bytes",
            extension=".png",
            directory="test_dir",
        )

        assert mock_upload.called
        call_kwargs = mock_upload.call_args[1]
        assert call_kwargs["resource_type"] == "image"
        assert stored.resource_type == "image"


@pytest.mark.asyncio
async def test_cloudinary_delete_file_calls_destroy():
    provider = CloudinaryStorageProvider(
        cloud_name="test_cloud", api_key="test_key", api_secret="test_secret"
    )

    with patch("cloudinary.uploader.destroy", return_value={"result": "ok"}) as mock_destroy:
        success = await provider.delete_file(
            storage_key="examarena/test/doc", resource_type="raw"
        )
        assert success is True
        mock_destroy.assert_called_once_with("examarena/test/doc", resource_type="raw")


@pytest.mark.asyncio
async def test_cloudinary_get_file_reads_from_url():
    provider = CloudinaryStorageProvider(
        cloud_name="test_cloud", api_key="test_key", api_secret="test_secret"
    )

    fake_bytes = b"Sample document bytes from cloudinary"

    class FakeHttpxResponse:
        status_code = 200
        content = fake_bytes

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=FakeHttpxResponse()):
        content = await provider.get_file("examarena/test/doc")
        assert content == fake_bytes


def test_get_storage_provider_factory(monkeypatch):
    get_storage_provider.cache_clear()
    monkeypatch.setattr("app.core.config.settings.FILE_STORAGE_PROVIDER", "local")
    provider = get_storage_provider()
    assert isinstance(provider, LocalStorageProvider)

    get_storage_provider.cache_clear()
    monkeypatch.setattr("app.core.config.settings.FILE_STORAGE_PROVIDER", "cloudinary")
    monkeypatch.setattr("app.core.config.settings.CLOUDINARY_CLOUDNAME", "demo")
    monkeypatch.setattr("app.core.config.settings.CLOUDINARY_APIKEY", "123")
    monkeypatch.setattr("app.core.config.settings.CLOUDINARY_APISECRET", "sec")
    provider_c = get_storage_provider()
    assert isinstance(provider_c, CloudinaryStorageProvider)
    get_storage_provider.cache_clear()
