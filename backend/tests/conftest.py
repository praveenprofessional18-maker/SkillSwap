import os
import shutil
import tempfile
from pathlib import Path

import pytest

TEST_DIRECTORY = Path(tempfile.mkdtemp(prefix="skillswap-tests-"))
os.environ["JWT_SECRET"] = "pytest-secret-must-contain-at-least-thirty-two-characters"
os.environ["DATABASE_URL"] = "sqlite:///" + (TEST_DIRECTORY / "test.db").as_posix()
os.environ["UPLOAD_DIR"] = str(TEST_DIRECTORY / "uploads")
os.environ["RATE_LIMIT_AUTH"] = "100/minute"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "secure-admin-password-123"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def create_account(client):
    def create(username, email=None):
        email = email or f"{username}@example.com"
        response = client.post("/api/auth/register", json={
            "username": username, "email": email, "password": "secure-password-123",
            "full_name": username.title(), "language": "English",
        })
        assert response.status_code == 201, response.text
        token_response = client.post("/api/auth/login", json={
            "email": email, "password": "secure-password-123",
        })
        assert token_response.status_code == 200, token_response.text
        token = token_response.json()["access_token"]
        return response.json(), {"Authorization": f"Bearer {token}"}
    return create


@pytest.fixture(scope="session", autouse=True)
def remove_test_data():
    yield
    engine.dispose()
    shutil.rmtree(TEST_DIRECTORY)
