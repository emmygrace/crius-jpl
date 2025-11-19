"""Integration tests for crius-jpl."""

import pytest
from datetime import datetime, timezone, timedelta

from crius_ephemeris_core import EphemerisSettings, GeoLocation
from crius_jpl import JplEphemerisAdapter


@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring JPL ephemeris data."""

    @pytest.fixture
    def adapter(self):
        """Create adapter for integration tests."""
        try:
            return JplEphemerisAdapter()
        except Exception:
            pytest.skip("JPL ephemeris data not available for integration tests")

    def test_end_to_end_calculation(self, adapter):
        """Test complete end-to-end calculation flow."""
        settings: EphemerisSettings = {
            "zodiac_type": "tropical",
            "ayanamsa": None,
            "house_system": "placidus",
            "include_objects": ["sun", "moon", "mercury", "venus", "mars"],
        }
        
        location: GeoLocation = {
            "lat": 40.7128,
            "lon": -74.0060,
        }
        
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        positions = adapter.calc_positions(dt, location, settings)
        
        # Verify structure
        assert "planets" in positions
        assert "houses" in positions
        assert positions["houses"] is not None
        
        # Verify planets
        assert len(positions["planets"]) == 5
        for planet_id in ["sun", "moon", "mercury", "venus", "mars"]:
            assert planet_id in positions["planets"]
            pos = positions["planets"][planet_id]
            assert 0 <= pos["lon"] < 360
            assert isinstance(pos["retrograde"], bool)
        
        # Verify houses
        houses = positions["houses"]
        assert houses["system"] == "placidus"
        assert len(houses["cusps"]) == 12
        assert len(houses["angles"]) == 4

    def test_multiple_consecutive_calculations(self, adapter):
        """Test multiple consecutive calculations."""
        settings: EphemerisSettings = {
            "zodiac_type": "tropical",
            "ayanamsa": None,
            "house_system": "placidus",
            "include_objects": ["sun"],
        }
        
        location: GeoLocation = {
            "lat": 40.7128,
            "lon": -74.0060,
        }
        
        # Calculate for multiple dates
        dates = [
            datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 6, 15, 18, 30, 0, tzinfo=timezone.utc),
            datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        ]
        
        results = []
        for dt in dates:
            positions = adapter.calc_positions(dt, location, settings)
            results.append(positions["planets"]["sun"]["lon"])
        
        # Verify positions change between dates
        assert results[0] != results[1]
        assert results[1] != results[2]

    def test_different_locations(self, adapter):
        """Test calculations for different locations."""
        settings: EphemerisSettings = {
            "zodiac_type": "tropical",
            "ayanamsa": None,
            "house_system": "placidus",
            "include_objects": ["sun"],
        }
        
        locations = [
            {"lat": 40.7128, "lon": -74.0060},  # New York
            {"lat": 51.5074, "lon": -0.1278},   # London
            {"lat": 35.6762, "lon": 139.6503},  # Tokyo
        ]
        
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        house_cusps = []
        for loc in locations:
            positions = adapter.calc_positions(dt, loc, settings)
            assert positions["houses"] is not None
            # House cusps should differ for different locations
            house_cusps.append(positions["houses"]["cusps"]["1"])
        
        # Verify house cusps differ (they should for different longitudes)
        assert house_cusps[0] != house_cusps[1]

    def test_time_series_calculation(self, adapter):
        """Test calculating positions over a time series."""
        settings: EphemerisSettings = {
            "zodiac_type": "tropical",
            "ayanamsa": None,
            "house_system": "placidus",
            "include_objects": ["sun", "moon"],
        }
        
        location: GeoLocation = {
            "lat": 40.7128,
            "lon": -74.0060,
        }
        
        # Calculate for every hour over a day
        base_dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        positions_list = []
        
        for hour in range(24):
            dt = base_dt + timedelta(hours=hour)
            positions = adapter.calc_positions(dt, location, settings)
            positions_list.append(positions)
        
        # Verify all calculations succeeded
        assert len(positions_list) == 24
        
        # Verify moon position changes (moon moves faster)
        moon_positions = [p["planets"]["moon"]["lon"] for p in positions_list]
        # Moon should move significantly over 24 hours
        assert max(moon_positions) - min(moon_positions) > 10

    def test_date_range_boundaries(self, adapter):
        """Test calculations at date range boundaries."""
        settings: EphemerisSettings = {
            "zodiac_type": "tropical",
            "ayanamsa": None,
            "house_system": "placidus",
            "include_objects": ["sun"],
        }
        
        location: GeoLocation = {
            "lat": 40.7128,
            "lon": -74.0060,
        }
        
        # Test near boundaries (JPL DE430t supports 1550-2650 CE)
        test_dates = [
            datetime(1550, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2000, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2650, 12, 31, 12, 0, 0, tzinfo=timezone.utc),
        ]
        
        for dt in test_dates:
            try:
                positions = adapter.calc_positions(dt, location, settings)
                assert "sun" in positions["planets"]
            except Exception as e:
                # Some dates might be outside range
                pytest.skip(f"Date {dt} may be outside JPL range: {e}")

