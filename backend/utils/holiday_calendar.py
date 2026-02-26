"""
Business holiday calendar for US, India, England (UK), and Singapore.

Used for determining pdate (posting date): the next Tuesday that is a US business day,
or the following business day if that Tuesday is a US holiday.

Holidays are loaded for the next 10 years from a reference year.
"""
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Set, Union
import logging

logger = logging.getLogger(__name__)

# Supported countries: US, India, England (UK), Singapore
# holidays library uses ISO 3166-1 alpha-2: US, IN, GB, SG
SUPPORTED_COUNTRIES = {
    "US": "United States",
    "IN": "India",
    "GB": "England (United Kingdom)",
    "SG": "Singapore",
}

# Default country for pdate (posting date) business-day logic
PDATE_COUNTRY = "US"

# Number of years ahead to precompute holidays
HOLIDAY_YEARS_AHEAD = 10


def _get_holiday_lib():
    """Lazy import to avoid import errors if holidays is not installed."""
    try:
        import holidays as hl
        return hl
    except ImportError:
        logger.warning("holidays package not installed; holiday calendar will be empty")
        return None


def _reference_year() -> int:
    """Year to use as base for 'next 10 years' (current year)."""
    return date.today().year


def _holiday_years() -> List[int]:
    """Years to load for the calendar (current - 3 through current + 10 for tests and pdate)."""
    y0 = _reference_year()
    return list(range(max(1970, y0 - 3), y0 + HOLIDAY_YEARS_AHEAD + 1))


def _load_holidays_for_country(country: str) -> Set[date]:
    """Load all holidays for a country for the next 10 years."""
    hl = _get_holiday_lib()
    if hl is None:
        return set()
    try:
        # country_holidays returns a dict-like; we need the set of dates
        obj = hl.country_holidays(country, years=_holiday_years())
        return set(obj.keys())
    except Exception as e:
        logger.warning("Could not load holidays for %s: %s", country, e)
        return set()


# Cache per country (lazy population)
_holiday_cache: Dict[str, Set[date]] = {}


def _get_holidays(country: str) -> Set[date]:
    """Get the set of holiday dates for a country (cached)."""
    if country not in _holiday_cache:
        _holiday_cache[country] = _load_holidays_for_country(country)
    return _holiday_cache[country]


def is_business_day(
    d: Union[date, datetime, str],
    country: str = PDATE_COUNTRY,
) -> bool:
    """
    Return True if the given date is a business day (not weekend, not holiday).

    Args:
        d: Date as date, datetime, or YYYY-MM-DD string.
        country: ISO country code (US, IN, GB, SG). Default US for pdate.

    Returns:
        True if weekday is Mon–Fri and date is not a holiday.
    """
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d").date()
    elif isinstance(d, datetime):
        d = d.date()
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return d not in _get_holidays(country)


def next_business_day(
    d: Union[date, datetime, str],
    country: str = PDATE_COUNTRY,
    include_today: bool = False,
) -> date:
    """
    Return the next business day on or after the given date.

    Args:
        d: Start date.
        country: ISO country code.
        include_today: If True, return d when d is already a business day.

    Returns:
        The next business day as date.
    """
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d").date()
    elif isinstance(d, datetime):
        d = d.date()
    if include_today and is_business_day(d, country):
        return d
    candidate = d + timedelta(days=1)
    while not is_business_day(candidate, country):
        candidate += timedelta(days=1)
    return candidate


def get_holidays_list(
    country: str,
    year: Optional[int] = None,
    year_end: Optional[int] = None,
) -> List[Dict[str, str]]:
    """
    Return a list of holidays for a country as {"date": "YYYY-MM-DD", "name": "..."}.

    Args:
        country: ISO country code (US, IN, GB, SG).
        year: Single year to return; if None, use default 10-year window.
        year_end: If set with year, return range [year, year_end] inclusive.

    Returns:
        List of dicts with "date" and "name" (and optionally "country").
    """
    hl = _get_holiday_lib()
    if hl is None:
        return []
    y0 = _reference_year()
    years = _holiday_years()
    if year is not None:
        if year_end is not None:
            years = [y for y in years if year <= y <= year_end]
        else:
            years = [y for y in years if y == year]
    if not years:
        years = [year or y0]
    try:
        obj = hl.country_holidays(country, years=years)
        out = []
        for d, name in sorted(obj.items()):
            out.append({
                "date": d.strftime("%Y-%m-%d"),
                "name": name,
                "country": country,
            })
        return out
    except Exception as e:
        logger.warning("Could not list holidays for %s: %s", country, e)
        return []


def get_supported_countries() -> Dict[str, str]:
    """Return mapping of country code -> display name."""
    return dict(SUPPORTED_COUNTRIES)
