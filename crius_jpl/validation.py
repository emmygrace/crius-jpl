"""Validation utilities for crius-jpl."""

from datetime import datetime
from typing import Tuple

from .exceptions import DateRangeError

# JPL DE430t supported date range
JPL_MIN_DATE = datetime(1550, 1, 1)
JPL_MAX_DATE = datetime(2650, 12, 31)


def validate_date_range(dt: datetime) -> Tuple[bool, str]:
    """
    Validate that a date is within the JPL DE430t supported range.

    Args:
        dt: Datetime to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if dt < JPL_MIN_DATE:
        return False, f"Date {dt} is before minimum supported date {JPL_MIN_DATE}"
    
    if dt > JPL_MAX_DATE:
        return False, f"Date {dt} is after maximum supported date {JPL_MAX_DATE}"
    
    return True, ""


def check_date_range(dt: datetime, raise_error: bool = True) -> bool:
    """
    Check if date is within supported range, optionally raising an error.

    Args:
        dt: Datetime to check
        raise_error: If True, raise DateRangeError for out-of-range dates

    Returns:
        True if date is valid, False if out of range (only if raise_error=False)

    Raises:
        DateRangeError: If date is out of range and raise_error is True
    """
    is_valid, error_msg = validate_date_range(dt)
    
    if not is_valid:
        if raise_error:
            raise DateRangeError(dt, min_date=JPL_MIN_DATE.isoformat(), max_date=JPL_MAX_DATE.isoformat())
        return False
    
    return True

