"""End-to-end test for Phase 4: Generate report from real cluster run."""

import base64
import json
import time
from io import BytesIO

import requests
from PIL import Image

BASE_URL = "http://127.0.0.1:8765"


def create_test_chart_png() -> str:
    """Create a test chart PNG."""
    img = Image.new("RGB", (800, 600), color="#3b82f6")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def test_e2e_report_generation():
    """Test complete report generation flow."""
    print("=" * 60)
    print("Phase 4 E2E Test: Report Generation")
    print("=" * 60)

    # Step 1: Check health
    print("\n1. Checking backend health...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    health = response.json()
    print(f"   ✓ Backend is healthy: {health['status']}")
    print(f"   Database: {health['database']}")

    # Step 2: Get cluster runs
    print("\n2. Fetching cluster runs...")
    response = requests.get(f"{BASE_URL}/clusters")
    assert response.status_code == 200, f"Failed to fetch cluster runs: {response.text}"
    runs = response.json()

    if not runs:
        print("   ⚠️  No cluster runs found. Please run clustering first.")
        print("   Skipping report generation test.")
        return

    latest_run = runs[0]
    print(f"   ✓ Found {len(runs)} cluster run(s)")
    print(f"   Latest run: {latest_run['run_id']} with {latest_run['n_clusters']} clusters")

    # Step 3: Generate test charts
    print("\n3. Generating test chart PNGs...")
    chart_pngs = {
        "severity_breakdown": create_test_chart_png(),
        "monthly_trend": create_test_chart_png(),
        "mttr_by_severity": create_test_chart_png(),
    }
    print(f"   ✓ Generated {len(chart_pngs)} chart images")

    # Step 4: Generate report
    print("\n4. Generating DOCX report...")

    request_data = {
        "cluster_run_id": latest_run["run_id"],
        "title": "Q1 2024 Incident Review (E2E Test)",
        "quarter_label": "Q1 2024",
        "chart_pngs": chart_pngs,
    }

    start_time = time.time()
    response = requests.post(f"{BASE_URL}/reports/generate", json=request_data)
    elapsed = time.time() - start_time

    assert response.status_code == 200, f"Report generation failed: {response.text}"
    result = response.json()

    print(f"   ✓ Report generated in {elapsed:.1f}s")
    print(f"   Report ID: {result['report_id']}")
    print(f"   DOCX Path: {result['docx_path']}")

    # Step 5: List reports
    print("\n5. Listing all reports...")
    response = requests.get(f"{BASE_URL}/reports")
    assert response.status_code == 200, f"Failed to list reports: {response.text}"
    reports = response.json()
    print(f"   ✓ Found {len(reports)} report(s)")

    # Verify our report is in the list
    our_report = next((r for r in reports if r["report_id"] == result["report_id"]), None)
    assert our_report is not None, "Generated report not found in list"
    print(f"   Title: {our_report['title']}")
    print(f"   Incidents: {our_report['metrics']['total_incidents']}")
    print(f"   Executive Summary (first 150 chars): {our_report['executive_summary'][:150]}...")

    # Step 6: Download report
    print("\n6. Testing report download...")
    response = requests.get(f"{BASE_URL}/reports/{result['report_id']}/download")
    assert response.status_code == 200, f"Download failed: {response.status_code}"
    assert (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        in response.headers.get("content-type", "")
    ), "Invalid content type for DOCX"
    print(f"   ✓ Downloaded {len(response.content):,} bytes")
    print(f"   Content-Type: {response.headers.get('content-type')}")

    print("\n" + "=" * 60)
    print("✓ All E2E tests passed!")
    print("=" * 60)
    print(f"\nReport available at: {BASE_URL}/reports/{result['report_id']}/download")


if __name__ == "__main__":
    try:
        test_e2e_report_generation()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
