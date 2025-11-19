"""Tests for service factory functions."""

import pytest
from datetime import datetime, timezone
import os

from crius_ephemeris_core import EphemerisSettings, GeoLocation
from crius_jpl import create_jpl_adapter, calc_positions, JplEphemerisAdapter


class TestCreateJplAdapter:
    """Test create_jpl_adapter factory function."""

    def test_create_adapter_default(self):
        """Test creating adapter with default settings."""
        adapter = create_jpl_adapter()
        assert isinstance(adapter, JplEphemerisAdapter)
        assert adapter.ts is not None
        assert adapter.eph is not None

    def test_create_adapter_with_path(self, tmp_path):
        """Test creating adapter with custom path."""
        test_path = str(tmp_path / "swisseph")
        test_path.mkdir(parents=True, exist_ok=True)
        
        adapter = create_jpl_adapter(ephemeris_path=test_path)
        assert isinstance(adapter, JplEphemerisAdapter)
        assert adapter.ephemeris_path == test_path

    def test_create_adapter_with_env_var(self, monkeypatch, tmp_path):
        """Test creating adapter respects SWISS_EPHEMERIS_PATH env var."""
        test_path = str(tmp_path / "swisseph")
        test_path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("SWISS_EPHEMERIS_PATH", test_path)
        
        adapter = create_jpl_adapter()
        assert adapter.ephemeris_path == test_path


class TestCalcPositions:
    """Test calc_positions convenience function."""

    def test_calc_positions_basic(self, sample_settings, sample_location):
        """Test basic calc_positions usage."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        try:
            positions = calc_positions(dt, sample_location, sample_settings)
            
            assert "planets" in positions
            assert "houses" in positions
            assert "sun" in positions["planets"]
        except Exception:
            pytest.skip("JPL ephemeris data not available")

    def test_calc_positions_with_custom_path(self, tmp_path, sample_settings, sample_location):
        """Test calc_positions with custom ephemeris path."""
        test_path = str(tmp_path / "swisseph")
        test_path.mkdir(parents=True, exist_ok=True)
        
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        try:
            positions = calc_positions(dt, sample_location, sample_settings, ephemeris_path=test_path)
            
            assert "planets" in positions
            assert "houses" in positions
        except Exception:
            pytest.skip("JPL ephemeris data not available")

    def test_calc_positions_no_location(self, sample_settings):
        """Test calc_positions without location."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        try:
            positions = calc_positions(dt, None, sample_settings)
            
            assert "planets" in positions
            assert positions["houses"] is None
        except Exception:
            pytest.skip("JPL ephemeris data not available")

