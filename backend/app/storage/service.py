"""Storage service factory."""

from functools import lru_cache

from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider


@lru_cache
def get_storage_provider() -> StorageProvider:
    """Return the configured storage provider (defaults to LocalStorageProvider)."""
    return LocalStorageProvider()
