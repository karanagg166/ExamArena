from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)


class TestPasswordSecurity:
    """U1-U4: Tests for password hashing and verification."""

    def test_hash_password_produces_bcrypt_hash(self):
        pwd = "SecurePassword123!"
        hashed = hash_password(pwd)
        assert hashed != pwd
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_password_correct(self):
        pwd = "CorrectHorseBatteryStaple!"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True

    def test_verify_password_wrong(self):
        pwd = "CorrectPassword"
        hashed = hash_password(pwd)
        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_empty(self):
        hashed = hash_password("ValidPassword")
        assert verify_password("", hashed) is False


class TestJWTSecurity:
    """U5-U12: Tests for JWT generation, claims, and verification."""

    def test_create_access_token_returns_jwt(self):
        user_id = "usr_123456"
        token = create_access_token(user_id)
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_verify_valid_token_extracts_user_id(self):
        user_id = "usr_abcdef"
        token = create_access_token(user_id)
        extracted_id = verify_token(token)
        assert extracted_id == user_id

    def test_verify_expired_token_returns_none(self):
        past_expire = datetime.now(UTC) - timedelta(minutes=10)
        payload = {"sub": "expired_user", "exp": past_expire}
        expired_token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        assert verify_token(expired_token) is None

    def test_verify_malformed_token_returns_none(self):
        assert verify_token("not.a.valid.jwt") is None
        assert verify_token("gibberish") is None

    def test_verify_empty_token_returns_none(self):
        assert verify_token("") is None

    def test_token_contains_sub_claim(self):
        user_id = "user_test_sub"
        token = create_access_token(user_id)
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload.get("sub") == user_id

    def test_token_contains_unique_jti_claim(self):
        user_id = "user_jti_test"
        token1 = create_access_token(user_id)
        token2 = create_access_token(user_id)

        payload1 = jwt.decode(
            token1, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        payload2 = jwt.decode(
            token2, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        assert "jti" in payload1
        assert "jti" in payload2
        assert payload1["jti"] != payload2["jti"]

    def test_token_expiry_matches_config(self):
        user_id = "user_expiry_test"
        before = datetime.now(UTC)
        token = create_access_token(user_id)
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        exp_timestamp = payload["exp"]
        exp_dt = datetime.fromtimestamp(exp_timestamp, tz=UTC)
        expected_expiry = before + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        # Difference should be within 5 seconds of expected
        diff = abs((exp_dt - expected_expiry).total_seconds())
        assert diff < 5
