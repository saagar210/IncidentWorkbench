#!/usr/bin/env python3
"""Phase 0 smoke tests for Incident Workbench backend."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    print("✓ Health check passed")


def test_jira_connection():
    """Test Jira connection testing endpoint."""
    response = client.post(
        "/settings/test-jira",
        json={
            "url": "https://test.atlassian.net",
            "email": "test@example.com",
            "api_token": "fake-token",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    print("✓ Jira connection test endpoint working")


def test_slack_connection():
    """Test Slack connection testing endpoint."""
    response = client.post(
        "/settings/test-slack",
        json={"bot_token": "xoxb-fake-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    print("✓ Slack connection test endpoint working")


def test_list_incidents():
    """Test incidents list endpoint."""
    # Ensure deterministic state across repeated/local runs.
    client.delete("/incidents")

    response = client.get("/incidents")
    assert response.status_code == 200
    data = response.json()
    assert "incidents" in data
    assert "total" in data
    assert data["total"] == 0
    print("✓ Incidents list endpoint working")


def test_list_cluster_runs():
    """Test cluster runs list endpoint."""
    response = client.get("/clusters")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0
    print("✓ Cluster runs list endpoint working")


def test_list_reports():
    """Test reports list endpoint."""
    response = client.get("/reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0
    print("✓ Reports list endpoint working")


if __name__ == "__main__":
    print("Running Phase 0 smoke tests...\n")
    test_health()
    test_jira_connection()
    test_slack_connection()
    test_list_incidents()
    test_list_cluster_runs()
    test_list_reports()
    print("\n✅ All Phase 0 endpoints working correctly!")
