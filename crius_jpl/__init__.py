"""
Crius JPL - JPL Ephemeris adapter implementation.

Named after Crius, the Titan of constellations and measuring the year.
"""

from .adapter import JplEphemerisAdapter
from .service import create_jpl_adapter, calc_positions
from .exceptions import (
    CriusJplError,
    EphemerisDownloadError,
    DateRangeError,
    EphemerisLoadError,
)
from .validation import validate_date_range, check_date_range, JPL_MIN_DATE, JPL_MAX_DATE

__all__ = [
    "JplEphemerisAdapter",
    "create_jpl_adapter",
    "calc_positions",
    "CriusJplError",
    "EphemerisDownloadError",
    "DateRangeError",
    "EphemerisLoadError",
    "validate_date_range",
    "check_date_range",
    "JPL_MIN_DATE",
    "JPL_MAX_DATE",
]

__version__ = "0.1.0"

