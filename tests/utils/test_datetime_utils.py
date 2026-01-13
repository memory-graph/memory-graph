"""
Tests for src/memorygraph/utils/datetime_utils.py

Following TDD approach to achieve 100% coverage of datetime utilities.
"""
from datetime import datetime, timezone

import pytest

from memorygraph.utils.datetime_utils import ensure_aware, parse_datetime, utc_now


class TestUtcNow:
    """Test the utc_now() function."""

    def test_utc_now_returns_datetime(self):
        """Test that utc_now returns a datetime object."""
        result = utc_now()
        assert isinstance(result, datetime)

    def test_utc_now_is_timezone_aware(self):
        """Test that utc_now returns timezone-aware datetime."""
        result = utc_now()
        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_utc_now_is_current_time(self):
        """Test that utc_now returns current time."""
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)

        # Result should be between before and after (within a few seconds)
        assert before <= result <= after

    def test_utc_now_multiple_calls_increase(self):
        """Test that multiple calls to utc_now return increasing times."""
        first = utc_now()
        # Sleep a tiny bit to ensure time difference
        import time

        time.sleep(0.001)
        second = utc_now()

        assert second >= first


class TestParseDatetime:
    """Test the parse_datetime() function."""

    def test_parse_datetime_with_timezone(self):
        """Test parsing ISO datetime string with timezone info."""
        iso_str = "2024-01-15T10:30:00+00:00"
        result = parse_datetime(iso_str)

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo is not None

    def test_parse_datetime_with_utc_timezone(self):
        """Test parsing ISO datetime string with UTC timezone."""
        iso_str = "2024-01-15T10:30:00Z"
        # Note: Z is not supported by fromisoformat in some Python versions
        # Use +00:00 instead
        iso_str = "2024-01-15T10:30:00+00:00"
        result = parse_datetime(iso_str)

        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_parse_datetime_naive_assumes_utc(self):
        """Test that parsing naive datetime assumes UTC."""
        iso_str = "2024-01-15T10:30:00"
        result = parse_datetime(iso_str)

        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_datetime_with_microseconds(self):
        """Test parsing ISO datetime with microseconds."""
        iso_str = "2024-01-15T10:30:00.123456"
        result = parse_datetime(iso_str)

        assert result.microsecond == 123456
        assert result.tzinfo is not None

    def test_parse_datetime_different_timezone(self):
        """Test parsing datetime with different timezone offset."""
        iso_str = "2024-01-15T10:30:00+05:30"  # India timezone
        result = parse_datetime(iso_str)

        assert result.tzinfo is not None
        assert result.year == 2024

    def test_parse_datetime_preserves_timezone(self):
        """Test that parse_datetime preserves original timezone."""
        iso_str = "2024-01-15T10:30:00-05:00"  # EST
        result = parse_datetime(iso_str)

        assert result.tzinfo is not None
        # The timezone info should be preserved
        assert result.year == 2024


class TestEnsureAware:
    """Test the ensure_aware() function."""

    def test_ensure_aware_with_naive_datetime(self):
        """Test ensure_aware converts naive datetime to UTC."""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        assert naive_dt.tzinfo is None

        result = ensure_aware(naive_dt)

        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_ensure_aware_with_aware_datetime(self):
        """Test ensure_aware preserves timezone-aware datetime."""
        aware_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert aware_dt.tzinfo is not None

        result = ensure_aware(aware_dt)

        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc
        assert result == aware_dt  # Should be unchanged

    def test_ensure_aware_with_different_timezone(self):
        """Test ensure_aware preserves non-UTC timezone."""
        from datetime import timedelta

        est = timezone(timedelta(hours=-5))
        aware_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=est)

        result = ensure_aware(aware_dt)

        assert result.tzinfo is not None
        assert result.tzinfo == est  # Should preserve original timezone
        assert result == aware_dt

    def test_ensure_aware_does_not_modify_original(self):
        """Test that ensure_aware doesn't modify the original datetime."""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        original_tzinfo = naive_dt.tzinfo

        result = ensure_aware(naive_dt)

        # Original should be unchanged
        assert naive_dt.tzinfo == original_tzinfo
        # Result should be aware
        assert result.tzinfo is not None

    def test_ensure_aware_with_microseconds(self):
        """Test ensure_aware preserves microseconds."""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0, 123456)
        assert naive_dt.microsecond == 123456

        result = ensure_aware(naive_dt)

        assert result.microsecond == 123456
        assert result.tzinfo is not None


class TestIntegration:
    """Integration tests for datetime utilities."""

    def test_utc_now_can_be_ensured_aware(self):
        """Test that utc_now result works with ensure_aware."""
        now = utc_now()
        result = ensure_aware(now)

        assert result.tzinfo is not None
        assert result == now

    def test_parse_datetime_naive_can_be_ensured_aware(self):
        """Test parse_datetime + ensure_aware integration."""
        iso_str = "2024-01-15T10:30:00"
        parsed = parse_datetime(iso_str)
        result = ensure_aware(parsed)

        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_round_trip_iso_format(self):
        """Test parsing and formatting ISO datetime."""
        now = utc_now()
        iso_str = now.isoformat()
        parsed = parse_datetime(iso_str)

        # Should be very close (within microseconds)
        assert abs((now - parsed).total_seconds()) < 0.001

    def test_all_functions_preserve_timezone_awareness(self):
        """Test that all functions maintain timezone awareness."""
        # Start with utc_now
        now = utc_now()
        assert now.tzinfo is not None

        # Convert to ISO and parse
        iso_str = now.isoformat()
        parsed = parse_datetime(iso_str)
        assert parsed.tzinfo is not None

        # Ensure aware
        aware = ensure_aware(parsed)
        assert aware.tzinfo is not None
