# Product Roadmap: Loan Engine — Epics & Stories

**Audience:** End-user decision makers, product owners, and business stakeholders  
**Purpose:** Review epics and stories, apply feedback and business logic, and prioritize work before development starts.  
**Status:** Draft for review — stories and acceptance criteria to be refined with business.

---

## Vision & Business Context

The application supports the **daily analysis of loans** to determine which loans should be **purchased** based on criteria defined in the Jupyter Notebook. For each completed daily run, the business must:

1. **Prepare wire instructions** to send money to counterparties for selected loans.
2. **Forward loan data** to other organizations for repackaging into structured products or for holding and interest accrual.

The **longer-term vision** includes:

- **Reviewing money sent over time** and **cash flow analysis**.
- **Portfolio-level analytics**: trend data, system triggers, and alerts.

To achieve this, requirements are grouped into **three epics**. Each epic contains **user stories** that can be estimated, refined, and prioritized with business input.

---

## Current State (What Exists Today)

- **Daily loan analysis (pipeline):** Run pipeline; apply notebook-derived rules; identify loans to purchase vs. rejected; record rejection criteria.
- **Visibility:** Dashboard, pipeline runs, exceptions, rejected loans, rejection criteria in UI and API.
- **Export:** Loan exceptions export to CSV/Excel.
- **Auth & data isolation:** User roles; sales-team scoping where applicable.
- **Operational:** Stuck-run handling, demo reset, logging/phases for troubleshooting.

*Gaps vs. notebook and desired workflow are documented in `NOTEBOOK_GAP_ANALYSIS.md` and `END_USER_DEMO.md`.*

---

## Epic 1: Daily Loan Analysis & Wire Instructions

**Objective:** Complete the daily workflow from loan analysis to **actionable wire instructions** and **handoff of selected loans** to downstream systems or organizations.

**Outcome for the business:** For each completed daily run, the business can see which loans to purchase, generate or prepare wire instructions for counterparties, and forward loan data for repackaging or holding.

| # | Story | Acceptance Criteria (to be refined) |
|---|--------|-------------------------------------|
| 1.1 | **Select loans to purchase from a run** | User can view a run’s “loans to purchase” list; select/deselect loans (e.g. final approval); optional notes or reasons for exclusion. Selections are saved and associated with the run. |
| 1.2 | **Generate or export wire instruction data** | From selected loans for a run, user can generate or export data needed for wire instructions (e.g. counterparty, amount, reference, loan IDs). Format may be CSV, Excel, or template-based — to be defined with Treasury/Operations. |
| 1.3 | **Wire instruction template and validation** | Support a configurable wire template (fields, validations) and/or integration with existing wire workflows. Business rules for amounts and counterparties documented and enforced where applicable. |
| 1.4 | **Forward loan data for downstream use** | User can export or send the list of selected loans (and required attributes) to other systems or organizations (e.g. for repackaging or holding). Format and delivery mechanism (file export, API, SFTP, etc.) to be defined with downstream owners. |
| 1.5 | **Audit trail for daily decisions** | Key actions (selections, wire data generation, forwards) are logged with user, timestamp, and run ID for compliance and dispute resolution. |
| 1.6 | **Run-level summary for operations** | A single “run summary” view or report shows: loans to purchase count/amount, exceptions count, wire-ready totals, and status of wire/forward steps — suitable for daily ops review. |

*Stories 1.1–1.6 are intended for prioritization and refinement with business (e.g. wire format, counterparty data source, and handoff process).*

---

## Epic 2: Portfolio Holdings & Cash Flow

**Objective:** Shift focus from **single-day runs** to **portfolio holdings over time** and **cash flow analysis**.

**Outcome for the business:** Visibility into total money sent over time, positions held, and cash flow to support reconciliation, reporting, and planning.

| # | Story | Acceptance Criteria (to be refined) |
|---|--------|-------------------------------------|
| 2.1 | **Track money sent (wire totals) over time** | System records or imports wire execution data (e.g. date, amount, counterparty, run/loan reference). Users can view “total money sent” by period (day, week, month, quarter) and filter by counterparty, run, or other dimensions. |
| 2.2 | **Portfolio holdings over time** | Model and display “holdings” (loans purchased and held or forwarded) over time — e.g. by run date, purchase date, or as-of date. Support aggregation by segment (product, counterparty, program) as defined by business. |
| 2.3 | **Cash flow view** | Provide a cash flow view: inflows and outflows over time, linked to runs and wires where applicable. Time granularity and categories to be defined with Finance. |
| 2.4 | **Reconciliation support** | Support reconciliation of wires vs. runs (e.g. “expected vs. sent”) and of loan counts/amounts vs. downstream systems, with clear exception reporting. |
| 2.5 | **Portfolio and cash flow reporting** | Standard reports or exports for portfolio holdings and cash flow (e.g. monthly summary, counterparty summary) in formats agreed with business (Excel, CSV, or BI export). |

*Epic 2 assumes Epic 1 delivers wire-related data and loan selection so that “money sent” and “holdings” can be defined and populated.*

---

## Epic 3: Portfolio Analytics — Trends, Triggers & Alerts

**Objective:** Expand into **portfolio-level analytics**: trend data, system triggers, and alerts to support risk and operations.

**Outcome for the business:** Proactive visibility into trends and anomalies, and configurable alerts to reduce operational and financial risk.

| # | Story | Acceptance Criteria (to be refined) |
|---|--------|-------------------------------------|
| 3.1 | **Trend data and visualizations** | Display trend data (e.g. volume of loans purchased, exception rates, wire volumes, cash flow) over configurable periods. Basic charts or export to BI tools; dimensions (product, counterparty, program) as defined by business. |
| 3.2 | **Configurable thresholds and triggers** | Allow configuration of thresholds (e.g. exception rate above X%, volume below Y) that trigger internal flags or “triggered” states for review. |
| 3.3 | **Alerts and notifications** | When a trigger fires (or other defined events), notify designated users (email, in-app, or integration). Alert rules and recipients configurable by role or group. |
| 3.4 | **Exception and anomaly detection** | Extend analytics to highlight anomalies (e.g. sudden change in rejection rate, counterparty concentration, or cash flow variance) for investigation. |
| 3.5 | **Portfolio analytics dashboard** | A dedicated analytics dashboard (or section) for trends, triggers status, and key portfolio metrics, with drill-down where needed. |
| 3.6 | **Export and integration for analytics** | Support export of trend and trigger data (or APIs) for use in external BI, reporting, or risk systems. |

*Epic 3 builds on Epic 2 data (holdings, cash flow, wires) so trends and triggers are meaningful.*

---

## Dependencies & Suggested Phasing

- **Epic 1** is the foundation: it closes the loop from “daily analysis” to “wire instructions” and “loan handoff.” It should be started first and refined with Operations/Treasury.
- **Epic 2** depends on Epic 1 (wire and selection data). It can start once wire/selection data is available and the business has agreed on how “money sent” and “holdings” are defined.
- **Epic 3** depends on Epic 2 (holdings and cash flow). It can start once sufficient history and data exist for trends and triggers.

Within each epic, stories can be reordered or split based on business priority and capacity.

---

## Next Steps for Decision Makers

1. **Review** this roadmap and the story list; confirm or adjust epic objectives and outcomes.
2. **Prioritize** stories within Epic 1 (and optionally Epic 2/3); add or remove stories as needed.
3. **Refine** acceptance criteria with product and technical leads (wire format, counterparty data, reporting dimensions, alert rules).
4. **Approve** Epic 1 scope and timeline so development can start; plan Epic 2/3 based on dependency and resource availability.
5. **Capture** feedback and business rules in a single place (e.g. Confluence, product backlog) and link to this roadmap.

---

## Document Control

| Version | Date       | Author / Notes        |
|---------|------------|------------------------|
| 0.1     | Draft      | Initial epic/story breakdown for review |

*This roadmap is intended to be updated as feedback is applied and stories are refined or reprioritized.*
