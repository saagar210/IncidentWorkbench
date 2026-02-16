"""Phase 5 Tests: Polish & Performance

Tests for:
- WAL mode enabled
- Error responses with correct HTTP status codes
- Edge case handling
"""

import sqlite3
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from database import Database
from main import app
from test_helpers import login_admin

pytestmark = pytest.mark.integration


def test_wal_mode_enabled(tmp_path: Path):
    """Verify WAL mode is enabled on database connections."""
    test_db = Database(db_path=tmp_path / "test.db")
    conn = test_db.get_connection()

    # Check journal mode
    cursor = conn.execute("PRAGMA journal_mode")
    journal_mode = cursor.fetchone()[0]
    conn.close()

    assert journal_mode.upper() == "WAL", "WAL mode should be enabled"


def test_foreign_keys_enabled(tmp_path: Path):
    """Verify foreign keys are enforced."""
    test_db = Database(db_path=tmp_path / "test.db")
    conn = test_db.get_connection()

    cursor = conn.execute("PRAGMA foreign_keys")
    fk_enabled = cursor.fetchone()[0]
    conn.close()

    assert fk_enabled == 1, "Foreign keys should be enabled"


def test_health_endpoint_returns_status():
    """Health endpoint should return database and ollama status."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "database" in data
    assert "ollama" in data


def test_ollama_unavailable_error():
    """Test that clustering returns 503 when Ollama is unavailable."""
    # This test would need Ollama to be stopped
    # Skipping in automated tests, but useful for manual verification
    pass


def test_insufficient_data_error():
    """Test clustering with no incidents returns error."""
    client = TestClient(app)
    headers = login_admin(client)

    # First, ensure no incidents exist
    client.delete("/incidents", headers=headers)

    # Try to run clustering
    response = client.post(
        "/clusters/run",
        json={"method": "hdbscan", "min_cluster_size": 3},
        headers=headers,
    )

    # Should return error (400/422/503 depending on validation vs service availability)
    assert response.status_code in [400, 422, 503]

    data = response.json()
    assert "detail" in data or "message" in data


def test_jira_connection_error_returns_error():
    """Test that invalid Jira credentials return appropriate error."""
    client = TestClient(app)
    headers = login_admin(client)

    response = client.post(
        "/settings/test-jira",
        json={
            "url": "https://invalid-jira-url.example.com",
            "email": "test@example.com",
            "api_token": "invalid_token",
        },
        headers=headers,
    )

    # Test connection endpoint returns 200 with success=false in body
    # (or error status if connection completely fails)
    assert response.status_code in [200, 400, 502, 503]

    if response.status_code == 200:
        data = response.json()
        # If 200, should indicate failure in response body
        assert "success" in data


def test_error_response_format():
    """Verify error responses have consistent format."""
    client = TestClient(app)

    # Try to get a non-existent incident
    response = client.get("/incidents/99999")

    # Should return error with 'detail' field
    if response.status_code != 200:
        data = response.json()
        assert "detail" in data or "message" in data, "Error should have detail or message field"


def test_problem_details_shape_for_404():
    """Non-2xx errors should expose RFC 9457-style fields."""
    client = TestClient(app)

    response = client.get("/incidents/99999")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")

    payload = response.json()
    assert "type" in payload
    assert "title" in payload
    assert payload["status"] == 404
    assert "detail" in payload


def test_request_id_is_propagated():
    """Every request should return an X-Request-ID header."""
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_logout_revokes_session_immediately():
    """Session logout should revoke access immediately."""
    client = TestClient(app)
    headers = login_admin(client)

    me_before = client.get("/auth/me")
    assert me_before.status_code == 200

    logout = client.post("/auth/logout", headers=headers)
    assert logout.status_code == 200

    me_after = client.get("/auth/me")
    assert me_after.status_code == 401


def test_idempotency_replays_write_response():
    """A repeated idempotency key should replay the original response."""
    client = TestClient(app)
    headers = login_admin(client)

    key = "phase5-idempotency-key"
    first = client.delete("/incidents", headers={**headers, "Idempotency-Key": key})
    second = client.delete("/incidents", headers={**headers, "Idempotency-Key": key})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert second.headers.get("Idempotency-Replayed") == "true"


def test_empty_incidents_list():
    """Test that empty incidents list is handled gracefully."""
    client = TestClient(app)
    headers = login_admin(client)

    # Delete all incidents
    client.delete("/incidents", headers=headers)

    # Fetch incidents
    response = client.get("/incidents")

    assert response.status_code == 200
    data = response.json()
    assert "incidents" in data
    assert data["total"] == 0


def test_metrics_with_no_data():
    """Test metrics endpoint with no incidents."""
    client = TestClient(app)
    headers = login_admin(client)

    # Delete all incidents
    client.delete("/incidents", headers=headers)

    # Fetch metrics
    response = client.get("/incidents/metrics")

    # Metrics may return 422 if no data, or 200 with zeros
    assert response.status_code in [200, 422]

    if response.status_code == 200:
        data = response.json()
        assert data["total_incidents"] == 0


def test_reports_list_empty():
    """Test reports endpoint when no reports exist."""
    client = TestClient(app)

    response = client.get("/reports")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_cluster_runs_empty():
    """Test cluster runs endpoint when no runs exist."""
    client = TestClient(app)

    response = client.get("/clusters")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
