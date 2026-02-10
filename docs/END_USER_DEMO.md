# End-User Demo: Loan Processing Visibility & Rejection Criteria

This guide is for **demo-only** use. The goal is to show end-users how the application **logs loan processing** and provides **visibility to rejected loans** with clear **rejection criteria** (why each loan did not meet requirements). Feedback from this demo will drive the implementation roadmap.

---

## 1. Demo Priorities

| Priority | What to show |
|----------|--------------|
| **Logging of loan processing** | When a run executes, the app records run metadata (start time, end time, total loans processed, exception count). On **Run Detail**, the "Processing summary" and run timeline show this. |
| **Visibility to rejected loans** | **Exceptions** page and **Rejected Loans** page list every loan that failed validation. **Run Detail** shows rejected loans for that run. |
| **Rejection criteria (why rejected)** | Each exception and each rejected loan shows **Rejection criteria**: the specific rule that was not met (e.g. Purchase price mismatch, Underwriting SFY, CoMAP Prime). This maps directly to the notebook logic. |

---

## 2. What You Can Demonstrate (Working Today)

### 2.1 Log in

- **Where**: http://localhost:5173 → Login
- **Action**: **admin** / **admin123**
- **Shows**: Auth and redirect to Dashboard.

### 2.2 Dashboard

- **Where**: After login → Dashboard
- **Shows**: Recent pipeline runs, summary stats (total runs, loans processed, **total exceptions**), and **Trigger run**.
- **Demo tip**: "Each run is one execution of the loan pipeline; we track how many loans were processed and how many had exceptions."

### 2.3 Pipeline Runs & Run Detail (Processing visibility)

- **Where**: **Pipeline Runs** in nav → click a run
- **Shows**:
  - **Run information**: Status, total loans, total balance, **exceptions count**, created/started/completed times.
  - **Processing summary**: When the run started and completed, how many loans were processed, how many exceptions (rejections) were found.
  - **Rejected loans for this run**: Table of loans that were **rejected** in this run, with **Rejection criteria** (the exact reason each loan failed).
- **Demo tip**: "This is the logging of loan processing for one run. Here we see which loans were rejected and the criteria that were not met."

### 2.4 Exceptions (Rejection criteria per exception)

- **Where**: **Exceptions** in nav
- **Shows**:
  - All loan-level exceptions (purchase price, underwriting, CoMAP, etc.).
  - **Rejection criteria** column: human-readable reason (e.g. "Purchase price mismatch", "Underwriting (SFY)", "CoMAP (Prime)").
  - Filters: exception type, severity, **rejection criteria**.
- **Demo tip**: "Every row is a loan that failed a check. The rejection criteria column tells you exactly which rule was not met."

### 2.5 Rejected Loans (Dedicated view)

- **Where**: **Rejected Loans** in nav
- **Shows**:
  - Select a **run** from the dropdown.
  - Table of all loans **rejected** in that run: loan number, **rejection criteria**, and optional loan details.
- **Demo tip**: "This view is focused only on rejected loans and the criteria that caused rejection—ideal for reviewing what did not get met."

### 2.6 API (Technical audience)

- **Where**: http://localhost:8000/docs
- **Shows**:
  - `GET /api/exceptions` with `rejection_criteria` in the response and as a filter.
  - `GET /api/loans?run_id=...&disposition=rejected` returning loans with `rejection_criteria`.
- **Demo tip**: "The same rejection criteria and disposition data are available via API for reporting or integration."

---

## 3. Suggested Demo Flow (5–10 minutes)

1. **Login** → Dashboard. Briefly explain that runs represent one execution of the pipeline.
2. **Pipeline Runs** → Open a **completed** run. Point out:
   - **Processing summary**: when it ran, how many loans processed, how many exceptions.
   - **Rejected loans** table: loan number + **rejection criteria** (why each loan was rejected).
3. **Exceptions** → Show the full list of exceptions; highlight the **Rejection criteria** column and filter by **rejection criteria** to show e.g. "Purchase price mismatch" or "Underwriting (SFY)".
4. **Rejected Loans** → Select the same run; show that this page is focused only on rejected loans and their criteria.
5. **Wrap-up**: "We log each run, expose every rejected loan, and tag each with the specific criteria that were not met. Your feedback will drive the next steps on the roadmap."

---

## 4. Setup Required for Demo

- **Backend**: `.\scripts\start-backend.ps1`
- **Frontend**: `.\scripts\start-frontend.ps1`
- **Database**: PostgreSQL up; tables created; admin user (e.g. `python backend/scripts/seed_admin.py` or `reset_admin_password.py`)
- **Data**: To show a completed run with exceptions and rejected loans, place valid input files as in `backend/docs/FILE_STRUCTURE.md` and trigger a run. Without files, you can still demo UI and "no data" / failed-run behavior.

---

## 5. Post-Demo: Implementation Roadmap

After the demo, collect end-user feedback and prioritize:

- **Phase 1 (current demo)**: Logging of runs, visibility to rejected loans, rejection criteria in UI and API.
- **Phase 2 (roadmap)**: Features and priorities to be defined from feedback (e.g. more filters, export, additional eligibility checks, scheduling, reporting). See **`docs/NOTEBOOK_GAP_ANALYSIS.md`** for notebook vs app gaps.

Use this doc and the gap analysis to present a clear **roadmap for implementation** based on user input.
