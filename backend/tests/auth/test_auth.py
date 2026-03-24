# backend/tests/auth/test_auth.py
import pytest
from tests.dummy_data.users import TEST_USER_PAYLOAD


# ═════════════════════════════════════════════════════════════
#  UNIT TESTS — everything mocked, no real DB
# ═════════════════════════════════════════════════════════════

class TestSignupUnit:
    """Tests for POST /api/v1/auth/signup — all mocked."""

    @pytest.mark.asyncio
    async def test_signup_success(self, client, mock_db, fake_user):
        mock_db["get_user_by_email"].return_value = None   
        mock_db["create_user"].return_value = fake_user    

        response = await client.post(
            "/api/v1/auth/signup", json=TEST_USER_PAYLOAD
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == fake_user.email
        assert data["name"] == fake_user.name
        assert "password" not in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_signup_sets_cookie(self, client, mock_db, fake_user):
        mock_db["get_user_by_email"].return_value = None
        mock_db["create_user"].return_value = fake_user

        response = await client.post(
            "/api/v1/auth/signup", json=TEST_USER_PAYLOAD
        )
        assert "access_token" in response.cookies

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client, mock_db, fake_user):
        mock_db["get_user_by_email"].return_value = fake_user 

        response = await client.post(
            "/api/v1/auth/signup", json=TEST_USER_PAYLOAD
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
        mock_db["create_user"].assert_not_called()

    @pytest.mark.asyncio
    async def test_signup_missing_required_fields(self, client, mock_db):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"email": "x@x.com", "password": "pass"},  
        )
        assert response.status_code == 422
        mock_db["get_user_by_email"].assert_not_called()

    @pytest.mark.asyncio
    async def test_signup_invalid_email_format(self, client, mock_db):
        response = await client.post(
            "/api/v1/auth/signup",
            json={**TEST_USER_PAYLOAD, "email": "not-an-email"},
        )
        assert response.status_code == 422
        mock_db["get_user_by_email"].assert_not_called()

    @pytest.mark.asyncio
    async def test_signup_create_user_called_with_correct_data(
        self, client, mock_db, fake_user
    ):
        mock_db["get_user_by_email"].return_value = None
        mock_db["create_user"].return_value = fake_user

        await client.post("/api/v1/auth/signup", json=TEST_USER_PAYLOAD)
        mock_db["create_user"].assert_called_once()


class TestLoginUnit:
    """Tests for POST /api/v1/auth/login — all mocked."""

    @pytest.mark.asyncio
    async def test_login_success(self, client, mock_db, fake_user):
        mock_db["get_user_by_email"].return_value = fake_user
        mock_db["verify_password"].return_value = True

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": fake_user.email, "password": "TestPass123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == fake_user.email
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_login_sets_cookie(self, client, mock_db, fake_user):
        mock_db["get_user_by_email"].return_value = fake_user
        mock_db["verify_password"].return_value = True

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": fake_user.email, "password": "TestPass123!"},
        )
        assert "access_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_wrong_email(self, client, mock_db):
        mock_db["get_user_by_email"].return_value = None  

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@examarena.dev", "password": "anything"},
        )

        assert response.status_code == 400
        assert "invalid email" in response.json()["detail"].lower()
        mock_db["verify_password"].assert_not_called()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, mock_db, fake_user):
        mock_db["get_user_by_email"].return_value = fake_user
        mock_db["verify_password"].return_value = False  

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": fake_user.email, "password": "WrongPass!"},
        )

        assert response.status_code == 400
        assert "invalid password" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, client, mock_db):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-valid", "password": "pass"},
        )
        assert response.status_code == 422
        mock_db["get_user_by_email"].assert_not_called()

    @pytest.mark.asyncio
    async def test_login_token_is_generated(self, client, mock_db, fake_user):
        mock_db["get_user_by_email"].return_value = fake_user
        mock_db["verify_password"].return_value = True

        await client.post(
            "/api/v1/auth/login",
            json={"email": fake_user.email, "password": "TestPass123!"},
        )
        mock_db["create_access_token"].assert_called_once_with(fake_user.id)


class TestLogoutUnit:
    """Tests for POST /api/v1/auth/logout — all mocked."""

    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self, client):
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200


class TestMeUnit:
    """Tests for GET /api/v1/auth/me — all mocked."""

    @pytest.mark.asyncio
    async def test_me_authenticated(self, client, mock_db, fake_user):
        mock_db["verify_token"].return_value = fake_user.id
        mock_db["get_user_by_id"].return_value = fake_user

        client.cookies.set("access_token", "mocked.jwt.token")
        
        # Then make the request without the cookies= parameter
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == fake_user.email
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_me_no_cookie(self, client, mock_db):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, client, mock_db):
        mock_db["verify_token"].return_value = None  

        response = await client.get(
            "/api/v1/auth/me",
            cookies={"access_token": "fake.bad.token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_user_not_found(self, client, mock_db, fake_user):
        mock_db["verify_token"].return_value = fake_user.id
        mock_db["get_user_by_id"].return_value = None  

        response = await client.get(
            "/api/v1/auth/me",
            cookies={"access_token": "mocked.jwt.token"},
        )
        assert response.status_code == 404


# ═════════════════════════════════════════════════════════════
#  INTEGRATION TESTS — hit real NeonDB, minimal set
# ═════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAuthIntegration:

    @pytest.mark.asyncio
    async def test_signup_writes_to_db(
        self, real_client, real_db, cleanup_real_user
    ):
        response = await real_client.post(
            "/api/v1/auth/signup", json=TEST_USER_PAYLOAD
        )

        assert response.status_code == 200
        user_in_db = await real_db.user.find_unique(
            where={"email": TEST_USER_PAYLOAD["email"]}
        )
        assert user_in_db is not None
        assert user_in_db.email == TEST_USER_PAYLOAD["email"]
        assert user_in_db.password != TEST_USER_PAYLOAD["password"]

    @pytest.mark.asyncio
    async def test_signup_unique_email_enforced(
        self, real_client, real_db, cleanup_real_user
    ):
        await real_client.post(
            "/api/v1/auth/signup", json=TEST_USER_PAYLOAD
        )
        response = await real_client.post(
            "/api/v1/auth/signup", json=TEST_USER_PAYLOAD
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_login_reads_from_db(
        self, real_client, real_db, cleanup_real_user
    ):
        await real_client.post(
            "/api/v1/auth/signup", json=TEST_USER_PAYLOAD
        )
        response = await real_client.post(
            "/api/v1/auth/login",
            json={
                "email": TEST_USER_PAYLOAD["email"],
                "password": TEST_USER_PAYLOAD["password"],
            },
        )

        assert response.status_code == 200
        assert response.json()["email"] == TEST_USER_PAYLOAD["email"]