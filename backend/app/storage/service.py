"""Storage service factory."""

from functools import lru_cache

from app.core.config import settings
from app.storage.base import StorageConfigurationError, StorageProvider
from app.storage.local import LocalStorageProvider


@lru_cache
def get_storage_provider() -> StorageProvider:
    """Return the configured storage provider based on FILE_STORAGE_PROVIDER setting.

    Options:
    - 'local': Local filesystem storage with traversal protection.
    - 'cloudinary': Cloudinary cloud asset storage.

    Raises StorageConfigurationError for unknown or misconfigured providers.
    """
    provider = (settings.FILE_STORAGE_PROVIDER or "local").lower().strip()

    if provider == "local":
        return LocalStorageProvider()

    if provider == "cloudinary":
        from app.storage.cloudinary import CloudinaryStorageProvider

        return CloudinaryStorageProvider()

    raise StorageConfigurationError(
        f"Unsupported storage provider: '{provider}'. "
        "Allowed values are 'local' or 'cloudinary'."
    )
