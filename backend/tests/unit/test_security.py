from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_token_claims,
    hash_password,
    is_password_hash,
    verify_password,
    verify_token,
)


class TestPasswordSecurity:
    """U1-U4: Tests for password hashing, verification, and hash format identification."""

    def test_hash_password_produces_bcrypt_hash(self):
        pwd = "SecurePassword123!"
        hashed = hash_password(pwd)
        assert hashed != pwd
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert len(hashed) == 60

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
        assert verify_password("ValidPassword", "") is False
        assert verify_password(None, hashed) is False
        assert verify_password("ValidPassword", None) is False

    def test_is_password_hash_recognizes_bcrypt_variants(self):
        # 1. Hashes produced by hash_password
        hash_1 = hash_password("PasswordOne")
        assert is_password_hash(hash_1) is True

        # 2. Standard $2a$ format
        hash_2a = "$2a$12$e8kZ1qU5O7kP6f3G2H1I0u5J7K8L9M0N1O2P3Q4R5S6T7U8V9W0Xa"
        assert is_password_hash(hash_2a) is True

        # 3. Standard $2y$ format
        hash_2y = "$2y$10$e8kZ1qU5O7kP6f3G2H1I0u5J7K8L9M0N1O2P3Q4R5S6T7U8V9W0Xa"
        assert is_password_hash(hash_2y) is True

    def test_is_password_hash_rejects_plaintext_and_invalid_formats(self):
        # Plaintext passwords
        assert is_password_hash("SecretPassword123!") is False
        assert is_password_hash("TRIG2024") is False

        # Long strings that are not bcrypt
        assert is_password_hash("a" * 60) is False
        assert is_password_hash("VeryLongPlaintextPasswordExceedingTwentyCharacters") is False

        # Empty / None
        assert is_password_hash("") is False
        assert is_password_hash(None) is False
        assert is_password_hash(12345) is False

        # Truncated or malformed bcrypt-like prefix
        assert is_password_hash("$2b$12$short") is False
        assert is_password_hash("$2b$XX$" + "a" * 53) is False

    def test_user_and_exam_password_hash_interoperability(self):
        """Verify hash_password and verify_password work consistently for both user and exam passwords."""
        plain_user_pwd = "TeacherSecurePass#2026"
        plain_exam_pwd = "ExamSecretKey#2026"

        user_hash = hash_password(plain_user_pwd)
        exam_hash = hash_password(plain_exam_pwd)

        assert is_password_hash(user_hash) is True
        assert is_password_hash(exam_hash) is True

        # Verification is accurate and cross-checks fail
        assert verify_password(plain_user_pwd, user_hash) is True
        assert verify_password(plain_exam_pwd, exam_hash) is True
        assert verify_password(plain_exam_pwd, user_hash) is False
        assert verify_password(plain_user_pwd, exam_hash) is False

        # Generating hash for identical passwords produces distinct salts
        hash_dup_1 = hash_password("SameSecret")
        hash_dup_2 = hash_password("SameSecret")
        assert hash_dup_1 != hash_dup_2
        assert verify_password("SameSecret", hash_dup_1) is True
        assert verify_password("SameSecret", hash_dup_2) is True


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
        assert verify_token(None) is None

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

    def test_token_without_jti_remains_valid_for_backward_compatibility(self):
        """Tokens without a 'jti' claim (legacy sessions) still verify sub claim until expiry."""
        user_id = "legacy_user_no_jti"
        future_expire = datetime.now(UTC) + timedelta(minutes=30)
        legacy_payload = {"sub": user_id, "exp": future_expire}
        legacy_token = jwt.encode(
            legacy_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        claims = decode_token_claims(legacy_token)
        assert claims is not None
        assert "jti" not in claims
        assert claims["sub"] == user_id

        assert verify_token(legacy_token) == user_id
