"""Shared fixtures for crius-jpl tests."""

import pytest
import os
from datetime import datetime, timezone
from pathlib import Path

from crius_ephemeris_core import EphemerisSettings, GeoLocation
from crius_jpl import JplEphemerisAdapter


@pytest.fixture
def sample_settings() -> EphemerisSettings:
    """Sample ephemeris settings for testing."""
    return {
        "zodiac_type": "tropical",
        "ayanamsa": None,
        "house_system": "placidus",
        "include_objects": ["sun", "moon", "mercury", "venus", "mars"],
    }


@pytest.fixture
def sample_location() -> GeoLocation:
    """Sample geographic location (New York)."""
    return {
        "lat": 40.7128,
        "lon": -74.0060,
    }


@pytest.fixture
def sample_datetime() -> datetime:
    """Sample datetime for testing."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def adapter():
    """Create adapter instance for testing."""
    try:
        return JplEphemerisAdapter()
    except Exception:
        pytest.skip("JPL ephemeris data not available")


@pytest.fixture
def adapter_with_path(tmp_path):
    """Create adapter with custom ephemeris path."""
    test_path = str(tmp_path / "swisseph")
    test_path.mkdir(parents=True, exist_ok=True)
    
    try:
        return JplEphemerisAdapter(ephemeris_path=test_path)
    except Exception:
        pytest.skip("JPL ephemeris data not available")

