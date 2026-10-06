"""Cloudinary remote storage provider implementation."""

import asyncio
import io
import logging
import uuid
from typing import Any

import httpx

from app.core.config import settings
from app.storage.base import (
    StorageConfigurationError,
    StorageDeleteError,
    StorageProvider,
    StorageReadError,
    StorageUploadError,
    StoredFile,
)

logger = logging.getLogger(__name__)

# Track central initialization to avoid re-configuring
_CLOUDINARY_INITIALIZED = False


def ensure_cloudinary_configured(
    cloud_name: str | None = None,
    api_key: str | None = None,
    api_secret: str | None = None,
    force: bool = False,
) -> None:
    """Validate environment settings and configure Cloudinary centrally."""
    global _CLOUDINARY_INITIALIZED
    if _CLOUDINARY_INITIALIZED and not force and not (cloud_name or api_key or api_secret):
        return

    c_name = cloud_name or settings.CLOUDINARY_CLOUDNAME
    a_key = api_key or settings.CLOUDINARY_APIKEY
    a_secret = api_secret or settings.CLOUDINARY_APISECRET

    if not a_key or not a_secret or not c_name:
        missing = []
        if not a_key:
            missing.append("CLOUDINARY_APIKEY")
        if not a_secret:
            missing.append("CLOUDINARY_APISECRET")
        if not c_name:
            missing.append("CLOUDINARY_CLOUDNAME")
        raise StorageConfigurationError(
            f"Cloudinary credentials are not properly configured: {', '.join(missing)}. "
            "Please configure them in your environment or set FILE_STORAGE_PROVIDER='local'."
        )

    try:
        import cloudinary

        cloudinary.config(
            cloud_name=c_name,
            api_key=a_key,
            api_secret=a_secret,
            secure=True,
        )
        _CLOUDINARY_INITIALIZED = True
        logger.info("Cloudinary storage provider initialized successfully for cloud '%s'", c_name)
    except Exception as e:
        raise StorageConfigurationError(f"Failed to configure Cloudinary SDK: {str(e)}") from e


class CloudinaryStorageProvider(StorageProvider):
    """Storage provider leveraging Cloudinary for cloud document and image assets."""

    def __init__(
        self,
        cloud_name: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        if cloud_name is not None or api_key is not None or api_secret is not None:
            if cloud_name and api_key and api_secret:
                self._configure(cloud_name, api_key, api_secret)
        else:
            self._ensure_configured()

    def _ensure_configured(self) -> None:
        c_name = self.cloud_name or settings.CLOUDINARY_CLOUDNAME
        a_key = self.api_key or settings.CLOUDINARY_APIKEY
        a_secret = self.api_secret or settings.CLOUDINARY_APISECRET

        if not c_name or not a_key or not a_secret:
            missing = []
            if not a_key:
                missing.append("CLOUDINARY_APIKEY")
            if not a_secret:
                missing.append("CLOUDINARY_APISECRET")
            if not c_name:
                missing.append("CLOUDINARY_CLOUDNAME")
            raise StorageConfigurationError(
                f"Cloudinary credentials are not properly configured: {', '.join(missing)}. "
                "Please configure them in your environment or set FILE_STORAGE_PROVIDER='local'."
            )
        self._configure(c_name, a_key, a_secret)

    def _configure(self, cloud_name: str, api_key: str, api_secret: str) -> None:
        ensure_cloudinary_configured(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            force=True,
        )


    def _determine_resource_type(self, clean_ext: str, requested: str) -> str:
        """Map file extension to explicit Cloudinary resource type.

        PDFs are stored as 'raw' to preserve exact byte-for-byte content without rasterization.
        Images (PNG, JPG, JPEG) are stored as 'image'.
        """
        if requested and requested != "auto":
            return requested
        if clean_ext in (".png", ".jpg", ".jpeg"):
            return "image"
        return "raw"

    async def save_file(
        self,
        content: bytes,
        extension: str,
        directory: str = "",
        resource_type: str = "auto",
    ) -> StoredFile:
        """Upload file bytes to Cloudinary with server-controlled public ID and folder."""
        import cloudinary.uploader

        # Sanitize extension
        ext = extension.lower().strip()
        if not ext.startswith("."):
            ext = f".{ext}"
        clean_ext = "".join(c for c in ext if c.isalnum() or c == ".")
        if not clean_ext:
            clean_ext = ".bin"

        res_type = self._determine_resource_type(clean_ext, resource_type)

        # Build clean folder path under examarena namespace
        # e.g., examarena/question-imports/{examId} or examarena/answer-key-imports/{examId}
        if directory:
            clean_dir = directory.strip("/").replace("\\", "/")
            folder = f"examarena/{clean_dir}"
        else:
            folder = "examarena"

        # Generate unique server-controlled public ID (UUID hex)
        # Note: For raw files, Cloudinary requires the file extension in public_id for proper delivery
        unique_id = uuid.uuid4().hex
        public_id = f"{unique_id}{clean_ext}" if res_type == "raw" else unique_id

        def _upload() -> dict[str, Any]:
            file_obj = io.BytesIO(content)
            return cloudinary.uploader.upload(
                file_obj,
                public_id=public_id,
                folder=folder,
                resource_type=res_type,
                overwrite=True,
            )

        try:
            res = await asyncio.to_thread(_upload)
        except Exception as e:
            logger.error("Cloudinary upload failed: %s", e)
            raise StorageUploadError(f"Cloudinary upload failed: {str(e)}") from e

        uploaded_public_id = res.get("public_id") or f"{folder}/{public_id}"
        secure_url = res.get("secure_url") or res.get("url")
        actual_res_type = res.get("resource_type") or res_type

        return StoredFile(
            key=uploaded_public_id,
            provider="cloudinary",
            url=secure_url,
            resource_type=actual_res_type,
        )

    async def get_file(self, key: str, resource_type: str = "raw") -> bytes:
        """Retrieve stored asset bytes by public ID."""
        import cloudinary.utils

        try:
            url, _ = cloudinary.utils.cloudinary_url(
                key,
                resource_type=resource_type,
                secure=True,
            )
        except Exception as e:
            raise StorageReadError(f"Failed to generate Cloudinary URL for key '{key}': {str(e)}") from e

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    raise FileNotFoundError(f"Asset not found in Cloudinary: {key}")
                if resp.status_code != 200:
                    raise StorageReadError(
                        f"Failed to download asset from Cloudinary: HTTP {resp.status_code}"
                    )
                return resp.content
        except FileNotFoundError:
            raise
        except StorageReadError:
            raise
        except Exception as e:
            logger.error("Failed to read Cloudinary asset '%s': %s", key, e)
            raise StorageReadError(f"Failed to download Cloudinary asset: {str(e)}") from e

    async def delete_file(
        self,
        key: str | None = None,
        resource_type: str = "raw",
        storage_key: str | None = None,
    ) -> bool:
        """Delete an asset from Cloudinary using exact public ID and resource type."""
        import cloudinary.uploader

        target_key = key or storage_key
        if not target_key:
            return False

        def _destroy() -> dict[str, Any]:
            return cloudinary.uploader.destroy(
                target_key,
                resource_type=resource_type,
            )

        try:
            res = await asyncio.to_thread(_destroy)
            return res.get("result") in ("ok", "not found")
        except Exception as e:
            logger.error("Failed to delete Cloudinary asset '%s': %s", target_key, e)
            raise StorageDeleteError(f"Failed to delete Cloudinary asset: {str(e)}") from e

    def get_url(self, key: str, resource_type: str = "raw") -> str | None:
        """Return public URL for the stored Cloudinary asset."""
        import cloudinary.utils

        try:
            url, _ = cloudinary.utils.cloudinary_url(
                key,
                resource_type=resource_type,
                secure=True,
            )
            return url
        except Exception:
            return None

    def get_local_path(self, key: str) -> str | None:
        """Cloudinary files have no local filesystem path."""
        return None
