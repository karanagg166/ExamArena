# backend/tests/dummy_data/users.py
from unittest.mock import MagicMock

# ── Reusable dummy data ───────────────────────────────────────
TEST_USER_PAYLOAD = {
    "email": "testuser@examarena.dev",
    "name": "Test User",
    "password": "TestPass123!",
    "phoneNo": "9999999999",
    "pincode": "400001",
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "role": "USER",
}


def make_fake_user(overrides: dict = None):
    """
    Returns a MagicMock that looks like a Prisma User object.
    Use overrides to customise specific fields per test.
    """
    if overrides is None:
        overrides = {}

    user = MagicMock()
    user.id = "clxfake000000testuser"
    user.email = TEST_USER_PAYLOAD["email"]
    user.name = TEST_USER_PAYLOAD["name"]
    user.password = "$2b$12$hashedpasswordvalue"  # already hashed
    user.phoneNo = TEST_USER_PAYLOAD["phoneNo"]
    user.pincode = TEST_USER_PAYLOAD["pincode"]
    user.city = TEST_USER_PAYLOAD["city"]
    user.state = TEST_USER_PAYLOAD["state"]
    user.country = TEST_USER_PAYLOAD["country"]
    user.role = "USER"

    for k, v in overrides.items():
        setattr(user, k, v)
    return user
