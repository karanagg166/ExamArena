"""Abstract storage provider interface."""

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    @abstractmethod
    async def save_file(
        self, content: bytes, extension: str, directory: str = ""
    ) -> str:
        """Save file bytes and return a unique storage key/path."""
        pass

    @abstractmethod
    async def get_file(self, key: str) -> bytes:
        """Retrieve file content bytes by storage key."""
        pass

    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """Delete a file by its storage key."""
        pass

    @abstractmethod
    def get_local_path(self, key: str) -> str | None:
        """Return the local filesystem path if available, or None for cloud storage."""
        pass
