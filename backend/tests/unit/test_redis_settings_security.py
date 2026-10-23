"""Unit tests for secure Redis URL parsing, credentials masking, and fail-secure ARQ configuration."""

import pytest
from arq.connections import RedisSettings

from app.core.config import settings
from app.imports.worker import get_redis_settings, sanitize_redis_url


class TestRedisUrlSanitization:
    def test_sanitize_redis_url_with_password(self):
        url = "rediss://:supersecretpass123@my-redis.cloud.com:6380/0"
        sanitized = sanitize_redis_url(url)
        assert "supersecretpass123" not in sanitized
        assert "my-redis.cloud.com:6380/0" in sanitized
        assert sanitized == "rediss://:***@my-redis.cloud.com:6380/0"

    def test_sanitize_redis_url_with_user_and_password(self):
        url = "redis://admin:supersecretpass123@redis-cluster:6379/2"
        sanitized = sanitize_redis_url(url)
        assert "admin" not in sanitized
        assert "supersecretpass123" not in sanitized
        assert sanitized == "redis://***:***@redis-cluster:6379/2"

    def test_sanitize_redis_url_without_auth(self):
        url = "redis://redis-host:6379/0"
        sanitized = sanitize_redis_url(url)
        assert sanitized == "redis://redis-host:6379/0"

    def test_sanitize_redis_url_empty_or_none(self):
        assert sanitize_redis_url("") == ""
        assert sanitize_redis_url(None) == ""


class TestGetRedisSettingsParsing:
    def test_rediss_tls_parsing(self):
        url = "rediss://:secretpass999@redis.example.com:6380/3"
        redis_settings = get_redis_settings(url)
        assert isinstance(redis_settings, RedisSettings)
        assert redis_settings.host == "redis.example.com"
        assert redis_settings.port == 6380
        assert redis_settings.password == "secretpass999"
        assert redis_settings.database == 3
        assert redis_settings.ssl is True

    def test_redis_tcp_parsing_with_implied_scheme(self):
        url = "redis.example.com:6379/1"
        redis_settings = get_redis_settings(url)
        assert redis_settings.host == "redis.example.com"
        assert redis_settings.port == 6379
        assert redis_settings.database == 1
        assert redis_settings.ssl is False

    def test_malformed_dsn_raises_value_error_without_raw_password(self, monkeypatch):
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")
        bad_url = "rediss://:supersecretpass@invalid-host:99999999/0"
        with pytest.raises(ValueError) as excinfo:
            get_redis_settings(bad_url)
        msg = str(excinfo.value)
        assert "supersecretpass" not in msg
        assert "Failed to parse Redis DSN" in msg
        assert "***" in msg

    def test_production_rejects_localhost_redis(self, monkeypatch):
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        with pytest.raises(ValueError, match="Localhost Redis .* is not permitted in production"):
            get_redis_settings("redis://localhost:6379/0")

        with pytest.raises(ValueError, match="Localhost Redis .* is not permitted in production"):
            get_redis_settings("redis://127.0.0.1:6379/0")

    def test_production_rejects_empty_redis_url(self, monkeypatch):
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        with pytest.raises(ValueError, match="REDIS_URL must be configured with a valid non-empty DSN"):
            get_redis_settings("")

    def test_development_allows_empty_redis_url_with_default_settings(self, monkeypatch):
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")
        redis_settings = get_redis_settings("")
        assert isinstance(redis_settings, RedisSettings)
        assert redis_settings.host == "localhost"
        assert redis_settings.port == 6379
