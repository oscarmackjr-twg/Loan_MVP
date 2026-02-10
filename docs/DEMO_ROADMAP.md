# Demo & Implementation Roadmap

Use this when presenting the application to end-users and when outlining next steps after feedback.

---

## What the demo shows (current)

1. **Logging of loan processing**
   - Each pipeline run is recorded with: start/end time, total loans processed, number of rejections (exceptions).
   - Visible on **Run Detail** under “Loan processing summary”.

2. **Visibility to rejected loans**
   - **Exceptions** page: every loan that failed a validation, with type and message.
   - **Rejected Loans** page: select a run and see all loans rejected in that run.
   - **Run Detail**: “Rejected loans for this run” table.

3. **Rejection criteria (why a loan was rejected)**
   - Each exception and each rejected loan has a **rejection criteria** value that maps to the notebook (e.g. “Purchase price mismatch”, “Underwriting (SFY)”, “CoMAP (Prime)”).
   - Shown in Exceptions table and filter, Run Detail rejected table, and Rejected Loans page.

---

## Suggested demo flow

1. Log in → Dashboard → point out recent runs and exception counts.
2. Open a **Pipeline Run** → **Run Detail**: show “Loan processing summary” and “Rejected loans for this run” with rejection criteria.
3. **Exceptions**: show list and **Rejection criteria** column; filter by a criterion.
4. **Rejected Loans**: pick same run; show list focused on rejected loans and criteria.
5. Close with: “We’re collecting your feedback to shape the next phase of implementation.”

---

## Post-demo: implementation roadmap (draft)

| Phase | Scope | Driven by |
|-------|--------|-----------|
| **Phase 1 (done)** | Logging of runs, visibility to rejected loans, rejection criteria in UI/API | Demo requirements |
| **Phase 2** | Prioritized from end-user feedback (e.g. export, more filters, scheduling, reporting) | User feedback |
| **Phase 3** | Notebook parity and advanced features (see `NOTEBOOK_GAP_ANALYSIS.md`) | Product backlog |

After the demo, replace or expand Phase 2/3 with concrete items from user feedback and from `docs/NOTEBOOK_GAP_ANALYSIS.md`.
