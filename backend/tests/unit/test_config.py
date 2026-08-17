from app.core.config import Settings, settings


class TestConfigAndSettings:
    """U45-U47: Tests for configuration loading and defaults."""

    def test_settings_loaded(self):
        assert isinstance(settings, Settings)
        assert hasattr(settings, "SECRET_KEY")
        assert hasattr(settings, "DATABASE_URL")

    def test_default_algorithm_hs256(self):
        assert settings.ALGORITHM == "HS256"

    def test_default_token_expiry(self):
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES >= 15

    def test_custom_settings_instance(self):
        custom = Settings(
            SECRET_KEY="test-secret",
            ACCESS_TOKEN_EXPIRE_MINUTES=60,
            ALGORITHM="HS256",
        )
        assert custom.SECRET_KEY == "test-secret"
        assert custom.ACCESS_TOKEN_EXPIRE_MINUTES == 60
