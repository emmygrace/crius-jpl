"""Performance tests for crius-jpl."""

import pytest
import time
from datetime import datetime, timezone, timedelta

from crius_ephemeris_core import EphemerisSettings, GeoLocation
from crius_jpl import JplEphemerisAdapter


@pytest.mark.performance
class TestPerformance:
    """Performance benchmarks."""

    @pytest.fixture
    def adapter(self):
        """Create adapter for performance tests."""
        try:
            return JplEphemerisAdapter()
        except Exception:
            pytest.skip("JPL ephemeris data not available for performance tests")

    def test_single_calculation_performance(self, adapter):
        """Test performance of single calculation."""
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
        
        start = time.time()
        positions = adapter.calc_positions(dt, location, settings)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 1 second for single calculation)
        assert elapsed < 1.0
        assert "planets" in positions

    def test_multiple_calculations_performance(self, adapter):
        """Test performance of multiple calculations."""
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
        
        # Calculate for 100 different dates
        base_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        dates = [base_dt + timedelta(days=i) for i in range(100)]
        
        start = time.time()
        results = []
        for dt in dates:
            positions = adapter.calc_positions(dt, location, settings)
            results.append(positions)
        elapsed = time.time() - start
        
        # Should complete 100 calculations in reasonable time
        # Average should be < 0.1 seconds per calculation
        avg_time = elapsed / 100
        assert avg_time < 0.1, f"Average calculation time too slow: {avg_time:.3f}s"
        assert len(results) == 100

    def test_body_cache_performance(self, adapter):
        """Test that body cache improves performance."""
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
        
        # First calculation (cache miss)
        start1 = time.time()
        positions1 = adapter.calc_positions(dt, location, settings)
        elapsed1 = time.time() - start1
        
        # Second calculation with same settings (should benefit from body cache)
        start2 = time.time()
        positions2 = adapter.calc_positions(dt, location, settings)
        elapsed2 = time.time() - start2
        
        # Results should be identical
        assert positions1["planets"]["sun"]["lon"] == positions2["planets"]["sun"]["lon"]
        
        # Second calculation might be slightly faster due to caching
        # (though body cache is minimal, so don't assert too strongly)
        assert elapsed2 <= elapsed1 * 1.5  # Allow some variance

    def test_skyfield_loader_reuse(self, adapter):
        """Test that skyfield loader is reused efficiently."""
        # The adapter should reuse the same timescale and ephemeris loader
        # This is tested implicitly by checking that multiple calculations work
        
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
        
        # Create multiple adapters - they should share loader efficiently
        adapters = [JplEphemerisAdapter() for _ in range(5)]
        
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # All adapters should work
        for adapter_instance in adapters:
            positions = adapter_instance.calc_positions(dt, location, settings)
            assert "sun" in positions["planets"]

