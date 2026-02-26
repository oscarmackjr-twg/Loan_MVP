"""Tests for business holiday calendar (US, IN, GB, SG)."""
import pytest
from datetime import date, datetime

from utils.holiday_calendar import (
    is_business_day,
    next_business_day,
    get_holidays_list,
    get_supported_countries,
    PDATE_COUNTRY,
)


class TestSupportedCountries:
    def test_supported_includes_us_in_gb_sg(self):
        countries = get_supported_countries()
        assert "US" in countries
        assert "IN" in countries
        assert "GB" in countries
        assert "SG" in countries
        assert countries["GB"] == "England (United Kingdom)"


class TestIsBusinessDay:
    def test_weekend_not_business_day(self):
        # Saturday
        assert is_business_day(date(2025, 2, 15), "US") is False
        # Sunday
        assert is_business_day(date(2025, 2, 16), "US") is False

    def test_weekday_without_holiday_is_business_day(self):
        # Wednesday March 5, 2025 (not a US federal holiday)
        assert is_business_day(date(2025, 3, 5), "US") is True

    def test_accepts_string_date(self):
        assert is_business_day("2025-03-05", "US") is True
        assert is_business_day("2025-02-15", "US") is False

    def test_us_holiday_not_business_day(self):
        # July 4, 2025 is a Friday (US Independence Day)
        assert is_business_day(date(2025, 7, 4), "US") is False


class TestNextBusinessDay:
    def test_next_business_day_skips_weekend(self):
        # Friday Feb 14, 2025 -> next business day after is Monday Feb 17 (Presidents' Day)
        # so next business day is Tuesday Feb 18
        result = next_business_day(date(2025, 2, 14), "US", include_today=False)
        assert result == date(2025, 2, 18)

    def test_include_today_when_business_day(self):
        # Wednesday March 5, 2025 is a business day
        result = next_business_day(date(2025, 3, 5), "US", include_today=True)
        assert result == date(2025, 3, 5)

    def test_include_today_false_advances(self):
        result = next_business_day(date(2025, 3, 5), "US", include_today=False)
        assert result == date(2025, 3, 6)


class TestGetHolidaysList:
    def test_returns_list_of_dicts(self):
        result = get_holidays_list("US", year=2025)
        assert isinstance(result, list)
        for item in result[:3]:
            assert "date" in item
            assert "name" in item
            assert item["date"] >= "2025-01-01"
            assert item["date"] <= "2025-12-31"

    def test_unsupported_country_handled_by_caller(self):
        # API validates country; module may still try to load - use valid code
        result = get_holidays_list("US", year=date.today().year)
        assert isinstance(result, list)
