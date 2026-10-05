"""Local filesystem storage provider with path traversal defenses."""

import asyncio
import os
import uuid
from pathlib import Path

from app.core.config import settings
from app.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = os.path.abspath(
            base_dir or settings.QUESTION_IMPORT_STORAGE_PATH
        )
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
        self, content: bytes, extension: str, directory: str = ""
    ) -> str:
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
                c for c in directory if c.isalnum() or c in ("-", "_")
            )
            rel_path = os.path.join(clean_dir, unique_filename)
        else:
            rel_path = unique_filename

        full_path = self._resolve_safe_path(rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        def _write():
            with open(full_path, "wb") as f:
                f.write(content)

        await asyncio.to_thread(_write)
        return rel_path

    async def get_file(self, key: str) -> bytes:
        full_path = self._resolve_safe_path(key)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Storage file not found: {key}")

        def _read() -> bytes:
            with open(full_path, "rb") as f:
                return f.read()

        return await asyncio.to_thread(_read)

    async def delete_file(self, key: str) -> bool:
        try:
            full_path = self._resolve_safe_path(key)
            if os.path.isfile(full_path):
                await asyncio.to_thread(os.remove, full_path)
                return True
            return False
        except Exception:
            return False

    def get_local_path(self, key: str) -> str | None:
        try:
            full_path = self._resolve_safe_path(key)
            if os.path.isfile(full_path):
                return full_path
            return None
        except Exception:
            return None
