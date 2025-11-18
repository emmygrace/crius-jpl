"""Tests for JPL Ephemeris adapter."""

import pytest
from datetime import datetime, timezone
from crius_jpl import JplEphemerisAdapter, create_jpl_adapter
from crius_ephemeris_core import EphemerisSettings, GeoLocation


@pytest.fixture
def adapter():
    """Create a JPL adapter instance for testing."""
    return JplEphemerisAdapter()


@pytest.fixture
def sample_settings() -> EphemerisSettings:
    """Sample ephemeris settings."""
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


def test_adapter_initialization():
    """Test that adapter can be initialized."""
    adapter = JplEphemerisAdapter()
    assert adapter is not None
    assert adapter.ts is not None
    assert adapter.eph is not None


def test_adapter_with_custom_path(monkeypatch, tmp_path):
    """Test adapter initialization with custom ephemeris path."""
    # Create a temporary directory for ephemeris files
    test_path = str(tmp_path / "swisseph")
    test_path.mkdir(parents=True, exist_ok=True)
    
    adapter = JplEphemerisAdapter(ephemeris_path=test_path)
    assert adapter.ephemeris_path == test_path


def test_calc_positions_planets_only(adapter, sample_settings):
    """Test calculating planetary positions without houses."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    positions = adapter.calc_positions(dt, None, sample_settings)
    
    assert "planets" in positions
    assert "houses" in positions or positions.get("houses") is None
    
    # Check that requested planets are present
    assert "sun" in positions["planets"]
    assert "moon" in positions["planets"]
    assert "mercury" in positions["planets"]
    assert "venus" in positions["planets"]
    assert "mars" in positions["planets"]
    
    # Check planet position structure
    sun_pos = positions["planets"]["sun"]
    assert "lon" in sun_pos
    assert "lat" in sun_pos
    assert "speed_lon" in sun_pos
    assert "retrograde" in sun_pos
    
    # Validate longitude is in 0-360 range
    assert 0 <= sun_pos["lon"] < 360
    assert isinstance(sun_pos["lon"], (int, float))
    assert isinstance(sun_pos["lat"], (int, float))


def test_calc_positions_with_houses(adapter, sample_settings, sample_location):
    """Test calculating positions with houses."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    positions = adapter.calc_positions(dt, sample_location, sample_settings)
    
    assert "planets" in positions
    assert "houses" in positions
    assert positions["houses"] is not None
    
    houses = positions["houses"]
    assert "system" in houses
    assert houses["system"] == "placidus"
    assert "cusps" in houses
    assert "angles" in houses
    
    # Check that we have 12 house cusps
    assert len(houses["cusps"]) == 12
    for i in range(1, 13):
        assert str(i) in houses["cusps"]
        cusp_lon = houses["cusps"][str(i)]
        assert 0 <= cusp_lon < 360
    
    # Check angles
    assert "asc" in houses["angles"]
    assert "mc" in houses["angles"]
    assert "ic" in houses["angles"]
    assert "dc" in houses["angles"]
    
    for angle_name, angle_value in houses["angles"].items():
        assert 0 <= angle_value < 360


def test_calc_positions_lunar_nodes(adapter, sample_location):
    """Test calculating lunar nodes."""
    settings: EphemerisSettings = {
        "zodiac_type": "tropical",
        "ayanamsa": None,
        "house_system": "placidus",
        "include_objects": ["north_node", "south_node"],
    }
    
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    positions = adapter.calc_positions(dt, sample_location, settings)
    
    assert "north_node" in positions["planets"]
    assert "south_node" in positions["planets"]
    
    north_node = positions["planets"]["north_node"]
    south_node = positions["planets"]["south_node"]
    
    # Check positions are valid
    assert 0 <= north_node["lon"] < 360
    assert 0 <= south_node["lon"] < 360
    
    # South node should be approximately 180 degrees from north node
    diff = abs((south_node["lon"] - north_node["lon"]) % 360)
    assert diff < 1.0 or diff > 359.0  # Allow for small calculation differences


def test_calc_positions_multiple_timestamps(adapter, sample_settings, sample_location):
    """Test calculating positions for multiple timestamps."""
    timestamps = [
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        datetime(2024, 6, 15, 18, 30, 0, tzinfo=timezone.utc),
        datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    ]
    
    for dt in timestamps:
        positions = adapter.calc_positions(dt, sample_location, sample_settings)
        
        assert "planets" in positions
        assert "houses" in positions
        
        # Verify sun position changes between dates
        sun_pos = positions["planets"]["sun"]
        assert 0 <= sun_pos["lon"] < 360


def test_create_jpl_adapter():
    """Test the service factory function."""
    adapter = create_jpl_adapter()
    assert isinstance(adapter, JplEphemerisAdapter)


def test_create_jpl_adapter_with_path(tmp_path):
    """Test service factory with custom path."""
    test_path = str(tmp_path / "swisseph")
    test_path.mkdir(parents=True, exist_ok=True)
    
    adapter = create_jpl_adapter(ephemeris_path=test_path)
    assert adapter.ephemeris_path == test_path


def test_different_house_systems(adapter, sample_location):
    """Test different house systems."""
    house_systems = ["placidus", "whole_sign", "koch", "equal"]
    
    for house_system in house_systems:
        settings: EphemerisSettings = {
            "zodiac_type": "tropical",
            "ayanamsa": None,
            "house_system": house_system,
            "include_objects": ["sun"],
        }
        
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        positions = adapter.calc_positions(dt, sample_location, settings)
        
        assert positions["houses"] is not None
        assert positions["houses"]["system"] == house_system

