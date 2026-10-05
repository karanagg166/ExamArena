"""Abstract storage provider interface and data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class StorageConfigurationError(StorageError):
    """Raised when storage credentials or settings are missing or invalid."""
    pass


class StorageUploadError(StorageError):
    """Raised when uploading a file fails."""
    pass


class StorageReadError(StorageError):
    """Raised when retrieving or downloading a file fails."""
    pass


class StorageDeleteError(StorageError):
    """Raised when deleting a stored asset fails."""
    pass


@dataclass
class StoredFile:
    """Represents a persisted file in local or cloud storage."""

    key: str
    provider: str
    url: str | None = None
    resource_type: str = "raw"

    def __str__(self) -> str:
        """Allow backwards-compatible string usage where storage key is expected."""
        return self.key


class StorageProvider(ABC):
    @abstractmethod
    async def save_file(
        self,
        content: bytes,
        extension: str,
        directory: str = "",
        resource_type: str = "auto",
    ) -> StoredFile:
        """Save file bytes and return a StoredFile metadata object."""
        pass

    @abstractmethod
    async def get_file(self, key: str, resource_type: str = "raw") -> bytes:
        """Retrieve file content bytes by storage key."""
        pass

    @abstractmethod
    async def delete_file(self, key: str, resource_type: str = "raw") -> bool:
        """Delete a file by its storage key."""
        pass

    @abstractmethod
    def get_url(self, key: str, resource_type: str = "raw") -> str | None:
        """Return the public/signed URL if available."""
        pass

    @abstractmethod
    def get_local_path(self, key: str) -> str | None:
        """Return the local filesystem path if available, or None for cloud storage."""
        pass
