"""Local filesystem storage provider with path traversal defenses."""

import asyncio
import os
import uuid

from app.core.config import settings
from app.storage.base import (
    StorageDeleteError,
    StorageReadError,
    StorageProvider,
    StorageUploadError,
    StoredFile,
)


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str | None = None, base_path: str | None = None):
        target_dir = base_dir or base_path or settings.QUESTION_IMPORT_STORAGE_PATH
        self.base_dir = os.path.abspath(target_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_safe_path(self, key: str) -> str:
        """Resolve a storage key and strictly ensure it resides within the base directory."""
        # Normalize key and prevent relative traversal components
        sanitized_key = os.path.normpath(key).lstrip("/").lstrip("\\")
        full_path = os.path.abspath(os.path.join(self.base_dir, sanitized_key))
        if os.path.commonpath([full_path, self.base_dir]) != self.base_dir:
            raise ValueError(f"Path traversal detected for storage key: {key}")
        return full_path

    async def save_file(
        self,
        content: bytes,
        extension: str,
        directory: str = "",
        resource_type: str = "auto",
    ) -> StoredFile:
        # Sanitize extension
        ext = extension.lower().strip()
        if not ext.startswith("."):
            ext = f".{ext}"

        # Disallow unsafe extensions or characters
        clean_ext = "".join(c for c in ext if c.isalnum() or c == ".")
        if not clean_ext:
            clean_ext = ".bin"

        unique_filename = f"{uuid.uuid4().hex}{clean_ext}"
        if directory:
            clean_dir = "".join(
                c for c in directory if c.isalnum() or c in ("-", "_", "/")
            )
            rel_path = os.path.join(clean_dir, unique_filename)
        else:
            rel_path = unique_filename

        try:
            full_path = self._resolve_safe_path(rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            def _write():
                with open(full_path, "wb") as f:
                    f.write(content)

            await asyncio.to_thread(_write)
        except Exception as e:
            raise StorageUploadError(f"Failed to write local file: {str(e)}") from e

        if resource_type == "auto":
            res_type = "image" if clean_ext in (".png", ".jpg", ".jpeg") else "raw"
        else:
            res_type = resource_type

        return StoredFile(
            key=rel_path,
            provider="local",
            url=None,
            resource_type=res_type,
        )

    async def get_file(self, key: str, resource_type: str = "raw") -> bytes:
        try:
            full_path = self._resolve_safe_path(key)
            if not os.path.isfile(full_path):
                raise FileNotFoundError(f"Storage file not found: {key}")

            def _read() -> bytes:
                with open(full_path, "rb") as f:
                    return f.read()

            return await asyncio.to_thread(_read)
        except FileNotFoundError:
            raise StorageReadError(f"Storage file not found: {key}")
        except Exception as e:
            raise StorageReadError(f"Failed to read local file {key}: {str(e)}") from e

    async def delete_file(self, key: str, resource_type: str = "raw") -> bool:
        try:
            full_path = self._resolve_safe_path(key)
            if os.path.isfile(full_path):
                await asyncio.to_thread(os.remove, full_path)
                return True
            return False
        except Exception as e:
            raise StorageDeleteError(f"Failed to delete local file {key}: {str(e)}") from e

    def get_url(self, key: str, resource_type: str = "raw") -> str | None:
        return None

    def get_local_path(self, key: str) -> str | None:
        try:
            full_path = self._resolve_safe_path(key)
            if os.path.isfile(full_path):
                return full_path
            return None
        except Exception:
            return None
