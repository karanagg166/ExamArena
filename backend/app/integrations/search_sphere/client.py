"""Central Search-Sphere Integration Client for ExamArena.

Encapsulates:
- Server-to-server authenticated requests
- Multi-tenant headers (X-Client-ID, X-Tenant-ID, X-Subject-ID)
- Request correlation propagation (X-Request-ID)
- Bounded timeouts & connection lifecycle
- Error normalization and strict credential masking
"""

from __future__ import annotations

import logging
from typing import Any
import httpx

from app.audit.context import get_current_request_id
from app.core.config import settings
from app.integrations.search_sphere.exceptions import (
    SearchSphereAuthenticationError,
    SearchSphereAuthorizationError,
    SearchSphereConfigurationError,
    SearchSphereConflictError,
    SearchSphereError,
    SearchSphereNotFoundError,
    SearchSphereTimeoutError,
    SearchSphereUnavailableError,
    SearchSphereValidationError,
)
from app.integrations.search_sphere.identifiers import (
    build_client_id,
    validate_identifier_token,
)

logger = logging.getLogger("exam_arena.search_sphere")


class SearchSphereClient:
    """Async client communicating with Search-Sphere generic /api/v1 endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        client_id: str | None = None,
        timeout_seconds: float | None = None,
    ):
        self._base_url = (
            base_url
            if base_url is not None
            else (settings.SEARCH_SPHERE_URL or "")
        ).rstrip("/")
        self._api_key = api_key if api_key is not None else settings.SEARCH_SPHERE_API_KEY
        self._client_id = client_id or build_client_id()
        self._timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.SEARCH_SPHERE_TIMEOUT_SECONDS
        )

    def _get_headers(
        self,
        tenant_id: str,
        subject_id: str | None = None,
        collection_id: str | None = None,
    ) -> dict[str, str]:
        """Construct secure server-to-server scoped headers."""
        if not self._api_key:
            raise SearchSphereConfigurationError(
                "SEARCH_SPHERE_API_KEY is not configured on the ExamArena server."
            )
        if not self._base_url:
            raise SearchSphereConfigurationError(
                "SEARCH_SPHERE_URL is not configured on the ExamArena server."
            )

        clean_tenant = validate_identifier_token(tenant_id, "tenant_id")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "X-Client-ID": self._client_id,
            "X-Tenant-ID": clean_tenant,
        }

        if subject_id:
            headers["X-Subject-ID"] = validate_identifier_token(
                subject_id, "subject_id"
            )

        if collection_id:
            headers["X-Collection-ID"] = validate_identifier_token(
                collection_id, "collection_id"
            )

        req_id = get_current_request_id()
        if req_id:
            headers["X-Request-ID"] = req_id

        return headers

    def _get_timeout(self) -> httpx.Timeout:
        """Create bounded timeout."""
        total = max(float(self._timeout_seconds), 1.0)
        connect = min(5.0, total)
        return httpx.Timeout(total, connect=connect, read=total, write=10.0)

    def _handle_response(self, response: httpx.Response) -> Any:
        """Normalize response and map errors to safe ExamArena exceptions."""
        if response.status_code in (200, 201, 202):
            return response.json()

        # Extract upstream detail safely if JSON
        detail = ""
        try:
            body = response.json()
            if isinstance(body, dict):
                detail = str(body.get("detail") or body.get("message") or "")
        except Exception:
            detail = response.text[:200]

        if response.status_code == 401:
            raise SearchSphereAuthenticationError(
                f"Search-Sphere authentication failed: {detail or 'Invalid credentials'}",
                status_code=401,
            )
        if response.status_code == 403:
            raise SearchSphereAuthorizationError(
                f"Search-Sphere access forbidden: {detail or 'Tenant access unauthorized'}",
                status_code=403,
            )
        if response.status_code == 404:
            raise SearchSphereNotFoundError(
                f"Search-Sphere resource not found: {detail or 'Not found'}",
                status_code=404,
            )
        if response.status_code == 409:
            raise SearchSphereConflictError(
                f"Search-Sphere resource conflict: {detail or 'Resource already exists'}",
                status_code=409,
            )
        if response.status_code in (400, 422):
            raise SearchSphereValidationError(
                f"Search-Sphere validation rejected: {detail or 'Invalid payload'}",
                status_code=response.status_code,
            )
        if response.status_code >= 500:
            logger.error(
                "Search-Sphere upstream 5xx response code=%d", response.status_code
            )
            raise SearchSphereUnavailableError(
                "Search-Sphere service temporarily unavailable.",
                status_code=response.status_code,
            )

        raise SearchSphereError(
            f"Search-Sphere returned unexpected status code {response.status_code}.",
            status_code=response.status_code,
        )

    # ─────────────────────────────────────────────────────────────
    # Collections API
    # ─────────────────────────────────────────────────────────────

    async def ensure_collection(
        self,
        collection_id: str,
        name: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        """
        Idempotently ensure a collection exists in Search-Sphere.
        If already exists (409 Conflict), retrieves and returns it.
        """
        url = f"{self._base_url}/api/v1/collections"
        headers = self._get_headers(tenant_id=tenant_id)
        payload = {
            "collection_id": collection_id,
            "name": name,
            "description": description,
            "metadata": metadata,
        }

        try:
            async with httpx.AsyncClient(timeout=self._get_timeout()) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 201:
                    return resp.json()
                if resp.status_code == 409:
                    # Already exists, fetch and return
                    return await self.get_collection(
                        collection_id=collection_id, tenant_id=tenant_id
                    )
                return self._handle_response(resp)
        except httpx.TimeoutException as exc:
            raise SearchSphereTimeoutError(
                "Timed out while ensuring collection in Search-Sphere."
            ) from exc
        except httpx.RequestError as exc:
            raise SearchSphereUnavailableError(
                "Unable to connect to Search-Sphere microservice."
            ) from exc

    async def get_collection(
        self,
        collection_id: str,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Fetch collection metadata by ID within a tenant."""
        url = f"{self._base_url}/api/v1/collections/{collection_id}"
        headers = self._get_headers(tenant_id=tenant_id)
        try:
            async with httpx.AsyncClient(timeout=self._get_timeout()) as client:
                resp = await client.get(url, headers=headers)
                return self._handle_response(resp)
        except httpx.TimeoutException as exc:
            raise SearchSphereTimeoutError(
                "Timed out while fetching collection from Search-Sphere."
            ) from exc
        except httpx.RequestError as exc:
            raise SearchSphereUnavailableError(
                "Unable to connect to Search-Sphere microservice."
            ) from exc

    # ─────────────────────────────────────────────────────────────
    # Documents API
    # ─────────────────────────────────────────────────────────────

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        document_id: str,
        collection_id: str | None,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Upload document file bytes to Search-Sphere isolated object storage."""
        url = f"{self._base_url}/api/v1/documents/upload"
        headers = self._get_headers(tenant_id=tenant_id, collection_id=collection_id)
        files = {"file": (filename, file_bytes, content_type)}
        data: dict[str, str] = {"document_id": document_id}
        if collection_id:
            data["collection_id"] = collection_id

        try:
            async with httpx.AsyncClient(timeout=self._get_timeout()) as client:
                resp = await client.post(url, files=files, data=data, headers=headers)
                return self._handle_response(resp)
        except httpx.TimeoutException as exc:
            raise SearchSphereTimeoutError(
                "Timed out while uploading file bytes to Search-Sphere."
            ) from exc
        except httpx.RequestError as exc:
            raise SearchSphereUnavailableError(
                "Unable to connect to Search-Sphere microservice during file upload."
            ) from exc

    async def register_document(
        self,
        external_document_id: str,
        storage_key: str,
        file_name: str,
        mime_type: str,
        file_size: int,
        collection_id: str | None,
        owner_subject_id: str | None,
        document_type: str,
        metadata: dict[str, Any] | None,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Register document metadata in Search-Sphere and enqueue ingestion."""
        url = f"{self._base_url}/api/v1/documents"
        headers = self._get_headers(
            tenant_id=tenant_id,
            subject_id=owner_subject_id,
            collection_id=collection_id,
        )
        payload = {
            "external_document_id": external_document_id,
            "storage_key": storage_key,
            "file_name": file_name,
            "mime_type": mime_type,
            "file_size": file_size,
            "collection_id": collection_id,
            "owner_subject_id": owner_subject_id,
            "document_type": document_type,
            "metadata": metadata,
        }

        try:
            async with httpx.AsyncClient(timeout=self._get_timeout()) as client:
                resp = await client.post(url, json=payload, headers=headers)
                return self._handle_response(resp)
        except httpx.TimeoutException as exc:
            raise SearchSphereTimeoutError(
                "Timed out while registering document in Search-Sphere."
            ) from exc
        except httpx.RequestError as exc:
            raise SearchSphereUnavailableError(
                "Unable to connect to Search-Sphere microservice during document registration."
            ) from exc

    async def get_document(
        self,
        document_id: str,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Fetch document details and indexing status from Search-Sphere."""
        url = f"{self._base_url}/api/v1/documents/{document_id}"
        headers = self._get_headers(tenant_id=tenant_id)

        try:
            async with httpx.AsyncClient(timeout=self._get_timeout()) as client:
                resp = await client.get(url, headers=headers)
                return self._handle_response(resp)
        except httpx.TimeoutException as exc:
            raise SearchSphereTimeoutError(
                "Timed out while querying document status from Search-Sphere."
            ) from exc
        except httpx.RequestError as exc:
            raise SearchSphereUnavailableError(
                "Unable to connect to Search-Sphere microservice."
            ) from exc

    async def delete_document(
        self,
        document_id: str,
        tenant_id: str,
    ) -> bool:
        """Delete document from Search-Sphere DB, object storage, and vector store."""
        url = f"{self._base_url}/api/v1/documents/{document_id}"
        headers = self._get_headers(tenant_id=tenant_id)

        try:
            async with httpx.AsyncClient(timeout=self._get_timeout()) as client:
                resp = await client.delete(url, headers=headers)
                data = self._handle_response(resp)
                return data.get("success", True)
        except httpx.TimeoutException as exc:
            raise SearchSphereTimeoutError(
                "Timed out while deleting document in Search-Sphere."
            ) from exc
        except httpx.RequestError as exc:
            raise SearchSphereUnavailableError(
                "Unable to connect to Search-Sphere microservice during deletion."
            ) from exc

    # ─────────────────────────────────────────────────────────────
    # Semantic Search API
    # ─────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        collection_id: str | None = None,
        owner_subject_id: str | None = None,
        limit: int = 10,
        document_type: str | None = None,
        metadata_filters: dict[str, Any] | None = None,
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        """Execute hybrid semantic search in Search-Sphere within tenant boundary."""
        url = f"{self._base_url}/api/v1/search"
        headers = self._get_headers(
            tenant_id=tenant_id,
            subject_id=owner_subject_id,
            collection_id=collection_id,
        )
        payload: dict[str, Any] = {
            "query": query,
            "limit": limit,
        }
        if collection_id:
            payload["collection_id"] = collection_id
        if owner_subject_id:
            payload["owner_subject_id"] = owner_subject_id
        if document_type:
            payload["document_type"] = document_type
        if metadata_filters:
            payload["metadata_filters"] = metadata_filters

        try:
            async with httpx.AsyncClient(timeout=self._get_timeout()) as client:
                resp = await client.post(url, json=payload, headers=headers)
                return self._handle_response(resp)
        except httpx.TimeoutException as exc:
            raise SearchSphereTimeoutError(
                "Timed out while executing search in Search-Sphere."
            ) from exc
        except httpx.RequestError as exc:
            raise SearchSphereUnavailableError(
                "Unable to connect to Search-Sphere microservice during search."
            ) from exc


_search_sphere_client: SearchSphereClient | None = None


def get_search_sphere_client() -> SearchSphereClient:
    """Dependency / accessor for the singleton SearchSphereClient."""
    global _search_sphere_client
    if _search_sphere_client is None:
        _search_sphere_client = SearchSphereClient()
    return _search_sphere_client
