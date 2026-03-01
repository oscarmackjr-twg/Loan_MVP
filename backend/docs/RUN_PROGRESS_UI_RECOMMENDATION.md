# Run progress in the UI (for users without AWS/CloudWatch)

## Goal

End users need to see what is happening during a run and get help troubleshooting **without** access to AWS (CloudWatch, logs). A “standard output progress” style panel in the UI was requested.

## Recommendation

### Phase 1 (implemented): **Live phase progress panel**

- **What:** A panel on the Dashboard that appears when a run is in progress. It shows:
  - Run ID
  - **Current step** (human-readable), e.g. “Loading reference data…”, “Running underwriting checks…”, “Exporting reports…”
- **How:** The backend already stores `last_phase` on each run (e.g. `load_reference_data`, `underwriting`, `export_reports`). The UI polls `GET /api/runs` or `GET /api/runs/{run_id}` every few seconds and maps `last_phase` to a short, user-friendly label.
- **Pros:** No new backend services, no shared log store, works with current synchronous pipeline. Gives users a clear “where is it?” and “where did it stop?” for stuck or failed runs.
- **Cons:** Not full log output—only the current step name.

This is implemented so users get immediate value without CloudWatch.

---

### Phase 2 (optional): **Recent log lines in the UI**

- **What:** Show the last N log lines (e.g. 50–100) for the run in progress in a scrollable “Output” or “Progress log” area, with polling every 2–3 seconds.
- **How (options):**
  1. **In-memory buffer per run (single worker):** A custom logging Handler appends lines to a `dict[run_id, list]`. `GET /api/runs/{run_id}/recent-logs` returns that list. Works only if the same process handles both the run and the request; **fails with multiple ECS tasks or workers**.
  2. **Shared store (recommended for production):** Pipeline (or a logging Handler) writes each log line to Redis or a DB table (e.g. `run_logs(run_id, seq, message, created_at)`). The API reads the last N rows for `run_id`. Works across workers and after the run ends (with a TTL or retention policy).
- **Effort:** Medium (logging Handler + Redis or DB table + migration + API endpoint + UI panel).

---

### Phase 3 (optional): **Streaming log tail (SSE)**

- **What:** Live tail of logs in the browser (no polling), like a terminal.
- **How:** Pipeline must run in a **background task** (so the “start run” request returns immediately with `run_id`). Client opens `GET /api/runs/{run_id}/logs` as Server-Sent Events; server streams new lines from the same shared store as Phase 2. Requires background execution + shared log store.
- **Effort:** High (background runner, shared store, SSE endpoint, and possibly run-status polling for “running” vs “completed/failed”).

---

## Summary

| Approach              | User sees              | Backend change              | Multi-worker / ECS |
|-----------------------|------------------------|-----------------------------|---------------------|
| **Phase 1: Step only** | Current step label     | None (use existing `last_phase`) | Yes                 |
| **Phase 2: Log lines** | Last N log lines       | Handler + Redis or DB + API | Yes (with shared store) |
| **Phase 3: Stream**    | Live log stream        | Background run + store + SSE | Yes                 |

**Recommendation:** Ship **Phase 1** so users get progress and basic troubleshooting without AWS. Add **Phase 2** if support/troubleshooting needs justify “see actual log lines” in the UI; use a shared store (Redis or DB) so it works in multi-worker/ECS. Phase 3 is optional for a “terminal-like” experience later.
