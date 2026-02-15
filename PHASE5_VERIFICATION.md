# Phase 5 Verification Checklist

Run through these steps to verify Phase 5 implementation.

## Automated Tests

### Backend Tests
```bash
cd backend
source .venv/bin/activate
pytest test_phase5.py -v
```

**Expected:** ✅ 11/11 tests passing
- WAL mode enabled
- Foreign keys enforced
- Health endpoint works
- Error handling correct
- Edge cases handled

### TypeScript Build
```bash
npm run build
```

**Expected:** ✅ Clean build, no TypeScript errors

---

## Manual Verification

### 1. Dark Mode Toggle
- [ ] Start the app
- [ ] Click the sun/moon icon in the sidebar header
- [ ] Verify theme changes (background, text, borders)
- [ ] Reload the page
- [ ] Verify theme preference persists
- [ ] Toggle again to test light mode

**Pass Criteria:** Theme switches smoothly, persists across reloads

---

### 2. Error Boundary
- [ ] Open browser DevTools Console
- [ ] Deliberately introduce a React error (e.g., modify a component to throw)
- [ ] Verify error boundary catches it
- [ ] Verify "Something went wrong" message displays
- [ ] Click "Retry" button
- [ ] Verify page reloads

**Pass Criteria:** App doesn't crash completely, shows error UI

---

### 3. Toast Notifications - Jira Ingestion

- [ ] Go to Settings page
- [ ] Save invalid Jira credentials (or leave empty)
- [ ] Verify toast appears: "Please fill in all Jira fields" (error, red)
- [ ] Fill in valid credentials
- [ ] Click "Save Credentials"
- [ ] Verify toast appears: "Jira credentials saved securely" (success, green)
- [ ] Click "Test Connection" with invalid credentials
- [ ] Verify toast appears with connection error (error, red)

**Pass Criteria:** All toasts appear bottom-right, auto-dismiss after 5 seconds

---

### 4. Toast Notifications - Incidents

- [ ] Go to Incidents page
- [ ] Click "Fetch from Jira" without credentials
- [ ] Verify error toast: "Please configure Jira credentials in Settings first"
- [ ] Configure credentials in Settings
- [ ] Return to Incidents, fetch from Jira
- [ ] Verify success toast: "Fetched X new incidents (Y duplicates skipped)"

**Pass Criteria:** Toast messages are informative and actionable

---

### 5. Ollama Status

**If Ollama is running:**
- [ ] Go to Settings page
- [ ] Verify green dot next to "Ollama is running"
- [ ] Verify no help section displayed

**If Ollama is not running:**
- [ ] Stop Ollama: `killall ollama` (or stop the service)
- [ ] Go to Settings page
- [ ] Verify red dot next to "Ollama is not available"
- [ ] Verify help section shows:
  - Required models list
  - `ollama pull` commands
  - Link to ollama.ai

**Pass Criteria:** Status accurately reflects Ollama availability

---

### 6. Clustering Error Handling

**With no incidents:**
- [ ] Go to Incidents page
- [ ] Ensure no incidents loaded (or delete all)
- [ ] Go to Clusters page
- [ ] Click "Run Clustering"
- [ ] Verify error toast: "Clustering failed: ..." (mentions insufficient data or no incidents)

**With Ollama stopped:**
- [ ] Stop Ollama
- [ ] Ensure incidents are loaded
- [ ] Click "Run Clustering"
- [ ] Verify error toast mentions Ollama unavailable

**Pass Criteria:** Errors are clear and actionable

---

### 7. Report Generation

- [ ] Go to Reports page
- [ ] Click "Generate Report" without selecting cluster run
- [ ] Verify error toast: "Please select a cluster run"
- [ ] Select a cluster run
- [ ] Click "Generate Report" without exporting charts
- [ ] Verify error toast: "Please export charts first"
- [ ] Export charts from Dashboard
- [ ] Generate report successfully
- [ ] Verify success toast: "Report generated successfully!"

**Pass Criteria:** Validation prevents invalid submissions, success shows clear feedback

---

### 8. Loading States

- [ ] Go to Dashboard page (with metrics)
- [ ] Reload page
- [ ] Verify "Loading metrics..." appears briefly
- [ ] Go to Incidents page
- [ ] Click "Fetch from Jira"
- [ ] Verify button changes to "Fetching..." and disables during operation
- [ ] Go to Clusters page
- [ ] Click "Run Clustering"
- [ ] Verify loading state during clustering

**Pass Criteria:** Users see feedback during async operations

---

### 9. Empty States

- [ ] Delete all incidents (Incidents page has delete button)
- [ ] Go to Incidents page
- [ ] Verify incidents table is empty (shows 0 incidents, not error)
- [ ] Go to Clusters page
- [ ] Verify "No cluster runs yet" or similar empty state
- [ ] Go to Reports page
- [ ] Verify empty reports list

**Pass Criteria:** Empty states are handled gracefully, no crashes

---

### 10. Settings Input Validation

- [ ] Go to Settings page
- [ ] Try to save Jira credentials with empty URL
- [ ] Verify error toast
- [ ] Try to save Slack credentials with empty bot token
- [ ] Verify error toast
- [ ] Fill in all fields and save
- [ ] Verify success toast

**Pass Criteria:** Validation prevents invalid inputs

---

### 11. Dark Mode Across All Pages

- [ ] Enable dark mode
- [ ] Navigate through all pages: Dashboard, Incidents, Clusters, Reports, Settings
- [ ] Verify all pages respect dark mode
- [ ] Check charts, tables, forms, buttons
- [ ] Verify no white flashes or theme breaks

**Pass Criteria:** Consistent theming across entire app

---

### 12. Performance Check

- [ ] Open browser DevTools > Performance
- [ ] Record app startup
- [ ] Verify startup takes < 3 seconds
- [ ] Navigate between pages
- [ ] Verify page transitions are smooth (< 100ms)
- [ ] Toggle dark mode multiple times
- [ ] Verify transitions are smooth (< 200ms)

**Pass Criteria:** App feels responsive, no janky animations

---

### 13. Error Response Format

- [ ] Open browser DevTools > Network tab
- [ ] Trigger a Jira connection error (invalid credentials)
- [ ] Check response in Network tab
- [ ] Verify response has `detail` field
- [ ] Verify HTTP status code is 502 or 503
- [ ] Trigger clustering with no incidents
- [ ] Verify response has `detail` field
- [ ] Verify HTTP status code is 400/422

**Pass Criteria:** API errors follow consistent format

---

### 14. Database Performance

- [ ] Ingest 100+ incidents
- [ ] Run clustering
- [ ] Generate report
- [ ] Verify all operations complete without timeout
- [ ] Check database file: `~/.local/share/com.incident-workbench.app/incidents.db`
- [ ] Verify `-wal` and `-shm` files exist (WAL mode active)

**Pass Criteria:** Operations complete successfully, WAL files present

---

## Regression Tests

Run these to ensure Phase 5 didn't break existing functionality:

- [ ] Phase 1: Jira ingestion still works
- [ ] Phase 1: Slack ingestion still works
- [ ] Phase 2: Clustering still works (HDBSCAN, K-means)
- [ ] Phase 3: Dashboard metrics display correctly
- [ ] Phase 3: Charts render without errors
- [ ] Phase 4: Report generation still works
- [ ] Phase 4: DOCX download still works

**Pass Criteria:** All previous phases still functional

---

## Known Issues to Ignore

These are expected and documented:

1. Pydantic deprecation warnings in test output (harmless)
2. Vite bundle size warning (acceptable for desktop app)
3. Chart.js not fully themed in dark mode (limitation of library)

---

## Sign-Off

- [ ] All automated tests passing
- [ ] All manual verifications passing
- [ ] No console errors in normal operation
- [ ] Dark mode works across all pages
- [ ] Toast notifications appear for all operations
- [ ] Error messages are user-friendly
- [ ] Loading states visible during async operations
- [ ] Documentation updated (README.md)

**Verified by:** _________________
**Date:** _________________
**Phase 5 Status:** ✅ Complete
