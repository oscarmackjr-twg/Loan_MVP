# Business Holiday Calendar

The application includes a business holiday calendar used to determine **pdate** (posting date) and to support multi-country holiday data.

## Supported countries

- **US** – United States (used for pdate)
- **IN** – India
- **GB** – England (United Kingdom)
- **SG** – Singapore

Holidays are loaded for a rolling window: from 3 years before the current year through **10 years ahead**, so the calendar stays valid for the next 10 years as requested.

## How pdate is determined

- **Default rule:** pdate is the **next Tuesday** that is a **US business day**.
- If that Tuesday is a **US holiday** (or falls on a weekend), pdate is the **following US business day**.
- So: *next Tuesday, or the next US business day after it if that Tuesday is not a business day.*

Examples:

- If “today” is Monday and next Tuesday is a normal weekday → pdate = that Tuesday.
- If next Tuesday is July 4 (US Independence Day) → pdate = Wednesday (next business day).
- If next Tuesday is Saturday or Sunday → pdate = next Monday (or next business day after that if Monday is a holiday).

## Implementation

- **`backend/utils/holiday_calendar.py`** – Holiday and business-day logic:
  - Uses the [holidays](https://pypi.org/project/holidays/) library for US, IN, GB, SG.
  - `is_business_day(date, country)` – not weekend and not holiday.
  - `next_business_day(date, country)` – first business day on or after the given date.
  - `get_holidays_list(country, year, year_end)` – list of holidays for API/UI.
- **`backend/utils/date_utils.py`** – `calculate_next_tuesday(base_date)` now:
  1. Computes the next calendar Tuesday from `base_date`.
  2. If that day is a US business day, returns it.
  3. Otherwise returns `next_business_day(..., country="US")`.
- **Run context / API** – When `pdate` is not provided, `RunContext.create(...)` and `calculate_pipeline_dates(...)` use this logic so the default pdate always respects US holidays.

## API endpoints

- **`GET /api/calendar/countries`** – Supported country codes and display names.
- **`GET /api/calendar/holidays?country=US&year=2025&year_end=2030`** – Holidays for a country (optional year range).
- **`GET /api/calendar/next-posting-date?tday=2025-02-15`** – Next pdate from optional base date (tday); uses US business-day logic.

All calendar endpoints require authentication.

## Dependency

- **holidays** (>=0.50) – added to `backend/requirements.txt`.
