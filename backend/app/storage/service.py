"""Storage service factory."""

import logging
import os
from functools import lru_cache

from app.core.config import settings
from app.storage.base import (
    StorageConfigurationError,
    StorageProvider,
    StorageReadError,
)
from app.storage.local import LocalStorageProvider

logger = logging.getLogger(__name__)


def resolve_storage_resource_type(resource_type: str | None, file_type: str) -> str:
    """Use persisted storage metadata, inferring legacy null types from verified MIME."""
    if resource_type in ("raw", "image"):
        return resource_type
    if resource_type is None:
        inferred = {
            "application/pdf": "raw",
            "image/png": "image",
            "image/jpeg": "image",
        }.get(file_type)
        if inferred:
            return inferred
    raise StorageReadError(
        "Cannot determine storage resource type from persisted metadata "
        "or verified file MIME type."
    )


@lru_cache
def get_storage_provider() -> StorageProvider:
    """Return the configured storage provider based on FILE_STORAGE_PROVIDER setting.

    Options:
    - 'local': Local filesystem storage with traversal protection.
    - 'cloudinary': Cloudinary cloud asset storage.

    On serverless environments (e.g. Vercel, AWS Lambda), if Cloudinary credentials
    are provided, automatically use Cloudinary to ensure durable shared storage across
    API and worker instances.

    Raises StorageConfigurationError for unknown or misconfigured providers.
    """
    is_serverless = bool(
        os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    )
    provider = (settings.FILE_STORAGE_PROVIDER or "local").lower().strip()

    if is_serverless:
        if (
            settings.CLOUDINARY_APIKEY
            and settings.CLOUDINARY_APISECRET
            and settings.CLOUDINARY_CLOUDNAME
        ):
            logger.info(
                "Serverless execution environment detected with Cloudinary configured: "
                "selecting durable CloudinaryStorageProvider."
            )
            from app.storage.cloudinary import CloudinaryStorageProvider

            return CloudinaryStorageProvider()
        else:
            logger.warning(
                "Running in serverless environment with LocalStorageProvider. "
                "Warning: ephemeral /tmp storage is not shared across worker and serverless instances."
            )

    if provider == "local":
        return LocalStorageProvider()

    if provider == "cloudinary":
        from app.storage.cloudinary import CloudinaryStorageProvider

        return CloudinaryStorageProvider()

    raise StorageConfigurationError(
        f"Unsupported storage provider: '{provider}'. "
        "Allowed values are 'local' or 'cloudinary'."
    )
