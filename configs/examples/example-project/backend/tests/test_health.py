"""Tests for health endpoint."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    """Test that /health endpoint returns 200 and correct JSON."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ping():
    """Test that /ping endpoint returns 200 and correct JSON."""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}

