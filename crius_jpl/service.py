"""
Service entrypoint for JPL Ephemeris adapter.

Provides a factory function to create and configure the adapter instance.
"""

import os
from typing import Optional
from .adapter import JplEphemerisAdapter


def create_jpl_adapter(ephemeris_path: Optional[str] = None) -> JplEphemerisAdapter:
    """
    Create a configured JPL Ephemeris adapter instance.
    
    Args:
        ephemeris_path: Optional path to Swiss Ephemeris data files (for houses).
                       If None, uses SWISS_EPHEMERIS_PATH env var or default path.
    
    Returns:
        Configured JplEphemerisAdapter instance.
    """
    if ephemeris_path is None:
        ephemeris_path = os.getenv("SWISS_EPHEMERIS_PATH", "/usr/local/share/swisseph")
    
    return JplEphemerisAdapter(ephemeris_path=ephemeris_path)


def calc_positions(
    dt_utc,
    location: Optional[dict],
    settings: dict,
    ephemeris_path: Optional[str] = None,
) -> dict:
    """
    Calculate positions using JPL ephemeris (convenience function).
    
    This is a thin wrapper around JplEphemerisAdapter.calc_positions that
    creates an adapter instance and calls calc_positions.
    
    Args:
        dt_utc: UTC datetime for calculation
        location: Optional geographic location dict with 'lat' and 'lon'
        settings: EphemerisSettings dict
        ephemeris_path: Optional path to Swiss Ephemeris data files
    
    Returns:
        LayerPositions dict with planets and optionally houses
    """
    adapter = create_jpl_adapter(ephemeris_path=ephemeris_path)
    return adapter.calc_positions(dt_utc, location, settings)

