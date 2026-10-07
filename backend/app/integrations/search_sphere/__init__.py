"""Search-Sphere RAG microservice integration package."""

from app.integrations.search_sphere.client import SearchSphereClient, get_search_sphere_client
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
    build_collection_id,
    build_external_document_id,
    build_owner_subject_id,
    build_tenant_id,
)

__all__ = [
    "SearchSphereClient",
    "get_search_sphere_client",
    "SearchSphereError",
    "SearchSphereConfigurationError",
    "SearchSphereAuthenticationError",
    "SearchSphereAuthorizationError",
    "SearchSphereNotFoundError",
    "SearchSphereConflictError",
    "SearchSphereValidationError",
    "SearchSphereTimeoutError",
    "SearchSphereUnavailableError",
    "build_client_id",
    "build_tenant_id",
    "build_collection_id",
    "build_owner_subject_id",
    "build_external_document_id",
]
