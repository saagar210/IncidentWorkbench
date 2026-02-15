# Phase 3 Verification Guide

Quick guide to verify Phase 3 implementation works correctly.

## Quick Start

### Option 1: Visual Test (Recommended)

1. **Start the application:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python -m uvicorn main:app --reload --port 8765

   # Terminal 2 - Frontend (Tauri)
   npm run tauri dev
   ```

2. **Load sample data** (if database is empty):
   ```bash
   python backend/test_metrics_endpoint.py
   ```

3. **Navigate to Dashboard:**
   - Click "Dashboard" in the left sidebar
   - You should see:
     - 5 summary stat cards at top
     - Filter dropdowns (source, severity)
     - 4 charts in a 2x2 grid
     - "Export Charts for Report" button

4. **Verify Charts Render:**
   - **Top Left:** Severity Pie Chart (colored slices)
   - **Top Right:** MTTR Stat Card (big number with P50/P90)
   - **Bottom Left:** Monthly Trend Bar Chart (blue bars)
   - **Bottom Right:** Top Assignees Horizontal Bar (green bars)

5. **Test Export:**
   - Click "Export Charts for Report"
   - Button should show "Exporting Charts..."
   - Success message appears: "✓ Charts exported successfully"
   - Green debug box appears: "4 charts exported and ready for DOCX"
   - Open browser console (F12) to see base64 data logged

6. **Test Filters:**
   - Select "Jira" from source dropdown
   - Charts update to show only Jira incidents
   - Select "SEV1" from severity dropdown
   - Charts update again
   - Click "Clear Filters" to reset

### Option 2: Backend API Test

Test the metrics endpoint directly:

```bash
# Test basic metrics
curl http://localhost:8765/incidents/metrics | jq .

# Test with source filter
curl "http://localhost:8765/incidents/metrics?source=jira" | jq .

# Test with severity filter
curl "http://localhost:8765/incidents/metrics?severity=SEV1" | jq .

# Test with both filters
curl "http://localhost:8765/incidents/metrics?source=jira&severity=SEV2" | jq .
```

Expected response structure:
```json
{
  "total_incidents": 5,
  "sev1_count": 2,
  "sev2_count": 1,
  "sev3_count": 1,
  "sev4_count": 1,
  "unknown_count": 0,
  "mean_resolution_hours": 6.8,
  "median_resolution_hours": 3.0,
  "p50_resolution_hours": 3.0,
  "p90_resolution_hours": 24.0,
  "mttr_by_severity": {
    "SEV1": 2.5,
    "SEV2": 4.0,
    "SEV3": 1.0,
    "SEV4": 24.0
  },
  "by_severity": {
    "SEV1": 2,
    "SEV2": 1,
    "SEV3": 1,
    "SEV4": 1
  },
  "by_month": {
    "2026-01": 5
  },
  "by_assignee": {
    "alice": 2,
    "bob": 2,
    "charlie": 1
  },
  "by_project": {}
}
```

### Option 3: Automated Test

Run the backend test script:

```bash
cd backend
python test_metrics_endpoint.py
```

Expected output:
```
Initializing database...
Found 5 existing incidents

Testing MetricsCalculator...

=== Metrics Results ===
Total incidents: 5
SEV1: 2, SEV2: 1, SEV3: 1, SEV4: 1
MTTR: 6.80h
P50: 3.00h
P90: 24.00h

By Severity: {'SEV1': 2, 'SEV2': 1, 'SEV3': 1, 'SEV4': 1}
By Month: {'2026-01': 5}
By Assignee: {'alice': 2, 'bob': 2, 'charlie': 1}

✓ Metrics endpoint test complete!
✓ Backend is ready for Phase 3 visualization
```

## Expected UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Incident Metrics Dashboard                                 │
│  Visualize and analyze incident data                        │
├─────────────────────────────────────────────────────────────┤
│  [Total: 5] [SEV1: 2] [SEV2: 1] [SEV3: 1] [SEV4: 1]       │
├─────────────────────────────────────────────────────────────┤
│  Filters: [All Sources ▼] [All Severities ▼] [Clear]      │
├─────────────────────────────────────────────────────────────┤
│  [Export Charts for Report] ✓ Charts exported              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Severity Pie     │  │ MTTR Stat        │                │
│  │  SEV1 🔴         │  │  6.8 hrs         │                │
│  │  SEV2 🟠         │  │  P50: 3.0h       │                │
│  │  SEV3 🟡         │  │  P90: 24.0h      │                │
│  │  SEV4 🔵         │  │                  │                │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Monthly Trend    │  │ Top Assignees    │                │
│  │  ▂▂▂▂▅▅▅█       │  │  alice    ▬▬▬    │                │
│  │  Jan Feb Mar     │  │  bob      ▬▬▬    │                │
│  │                  │  │  charlie  ▬      │                │
│  └──────────────────┘  └──────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  Debug: 4 charts exported and ready for DOCX generation    │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Charts not rendering
- Check browser console for errors
- Ensure backend is running on port 8765
- Verify data exists: `curl http://localhost:8765/incidents | jq .`

### Export fails
- Check that all 4 chart elements exist in DOM
- Verify html2canvas is installed: `npm list html2canvas`
- Check console for specific error messages

### Empty charts
- Run test script to create sample data
- Or import real data via Settings > Jira/Slack

### TypeScript errors
- Run `npm run build` to check for compilation errors
- Ensure all dependencies are installed: `npm install`

## Success Criteria

Phase 3 is successfully implemented when:

1. ✅ Dashboard page loads without errors
2. ✅ All 4 charts render with data
3. ✅ Filters update charts in real-time
4. ✅ Export button captures all charts as PNG
5. ✅ Console shows 4 base64 strings
6. ✅ Backend endpoint returns correct JSON
7. ✅ No TypeScript compilation errors

## What's Next

With Phase 3 complete, the exported chart PNGs are ready for Phase 4:
- DOCX report generation
- Chart embedding
- Summary text generation
- Download functionality

See `PHASE3_COMPLETE.md` for full technical details.
