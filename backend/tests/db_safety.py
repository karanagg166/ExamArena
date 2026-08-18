"""Database safety and verification utilities for isolated test execution."""

import os
from urllib.parse import urlparse


def verify_database_safety(database_url: str) -> None:
    """Validate that the configured database is strictly an isolated test database.

    Aborts execution if attempting to run against production, staging, or dev databases.
    """
    if not database_url:
        raise RuntimeError("DATABASE SAFETY CHECK FAILED: DATABASE_URL is not set.")

    # Remove driver prefix for standard URL parsing if needed
    clean_url = database_url
    if "+asyncpg" in clean_url:
        clean_url = clean_url.replace("+asyncpg", "")

    parsed = urlparse(clean_url)
    db_name = parsed.path.lstrip("/")
    hostname = (parsed.hostname or "").lower()

    # Disallow remote production / staging cloud providers
    prohibited_hosts = [
        "neon.tech",
        "supabase.co",
        "aws.neon.tech",
        "render.com",
        "railway.app",
        "amazonaws.com",
    ]
    for forbidden in prohibited_hosts:
        if forbidden in hostname:
            raise RuntimeError(
                f"DATABASE SAFETY CHECK FAILED: Host '{hostname}' belongs to a remote/cloud "
                "environment. Automated test suite must only run against a local test database."
            )

    # Disallow production and development database names
    prohibited_names = ["neondb", "exam_arena", "production", "prod", "staging"]
    if db_name in prohibited_names or "test" not in db_name.lower():
        raise RuntimeError(
            f"DATABASE SAFETY CHECK FAILED: Database name '{db_name}' is not an authorized test database. "
            "Database name must contain 'test' (e.g. 'exam_arena_test')."
        )


def get_test_database_url() -> str:
    """Return the canonical test database URL."""
    # Check if TEST_DATABASE_URL is explicitly set
    env_test_url = os.getenv("TEST_DATABASE_URL")
    if env_test_url:
        verify_database_safety(env_test_url)
        return env_test_url

    # Check if DATABASE_URL is set in environment and is a local database
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        clean_url = db_url.replace("+asyncpg", "")
        parsed = urlparse(clean_url)
        db_name = parsed.path.lstrip("/")
        hostname = (parsed.hostname or "").lower()
        is_cloud = any(
            forbidden in hostname
            for forbidden in [
                "neon.tech",
                "supabase.co",
                "render.com",
                "railway.app",
                "amazonaws.com",
            ]
        )
        if db_name and hostname and not is_cloud:
            test_url = db_url.replace(f"/{db_name}", "/exam_arena_test")
            try:
                verify_database_safety(test_url)
                return test_url
            except RuntimeError:
                pass

    # Check host vs container default
    # Inside docker compose network, 'db' is reachable.
    # On host, 'localhost' is reachable.
    default_host = (
        "db"
        if (os.path.exists("/.dockerenv") or os.getenv("ENVIRONMENT") == "ci")
        else "localhost"
    )
    url = f"postgresql+asyncpg://postgres:postgres@{default_host}:5432/exam_arena_test"
    verify_database_safety(url)
    return url
