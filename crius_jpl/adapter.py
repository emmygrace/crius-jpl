"""
JPL Ephemeris adapter implementation.

This module provides a JPL Ephemeris adapter that conforms to the
crius-ephemeris-core EphemerisAdapter protocol, using NASA JPL DE430t
ephemeris data via the skyfield library.
"""

from datetime import datetime
from typing import Optional
import os
import swisseph as swe
import pytz
from skyfield.api import load
from skyfield.framelib import ecliptic_frame

from crius_ephemeris_core import (
    EphemerisSettings,
    GeoLocation,
    PlanetPosition,
    HousePositions,
    LayerPositions,
    EphemerisAdapter,
)

from .exceptions import (
    EphemerisDownloadError,
    EphemerisLoadError,
    DateRangeError,
)
from .validation import check_date_range

# Skyfield planet body mapping
SKYFIELD_BODIES = {
    "sun": "sun",
    "moon": "moon",
    "mercury": "mercury",
    "venus": "venus",
    "mars": "mars",
    "jupiter": "jupiter barycenter",
    "saturn": "saturn barycenter",
    "uranus": "uranus barycenter",
    "neptune": "neptune barycenter",
    "pluto": "pluto barycenter",
}

# Shared skyfield loader instances (class-level cache)
_shared_timescale = None
_shared_ephemeris = None
_loader_lock = None


def _get_shared_loader():
    """Get or create shared skyfield loader instances."""
    global _shared_timescale, _shared_ephemeris, _loader_lock
    
    if _loader_lock is None:
        import threading
        _loader_lock = threading.Lock()
    
    with _loader_lock:
        if _shared_timescale is None:
            try:
                _shared_timescale = load.timescale()
            except Exception as e:
                raise EphemerisLoadError(f"Failed to load skyfield timescale: {str(e)}") from e
        
        if _shared_ephemeris is None:
            try:
                _shared_ephemeris = load('de430t.bsp')
            except Exception as e:
                error_str = str(e).lower()
                if 'download' in error_str or 'network' in error_str or 'connection' in error_str:
                    raise EphemerisDownloadError(
                        f"Failed to download JPL ephemeris data: {str(e)}"
                    ) from e
                else:
                    raise EphemerisLoadError(
                        f"Failed to load JPL ephemeris data: {str(e)}"
                    ) from e
    
    return _shared_timescale, _shared_ephemeris

# House system mapping (using Swiss Ephemeris for houses)
HOUSE_SYSTEM_MAP = {
    "placidus": b'P',
    "whole_sign": b'W',
    "koch": b'K',
    "equal": b'E',
    "regiomontanus": b'R',
    "campanus": b'C',
    "alcabitius": b'A',
    "morinus": b'M',
}


def _datetime_to_jd(dt_utc: datetime) -> float:
    """Convert UTC datetime to Julian Day."""
    return swe.julday(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
        swe.GREG_CAL
    )


def _get_house_system_bytes(house_system: str) -> bytes:
    """Convert house system string to bytes format."""
    return HOUSE_SYSTEM_MAP.get(house_system.lower(), b'P')  # Default to Placidus


class JplEphemerisAdapter:
    """
    JPL Ephemeris adapter implementation.
    
    Uses NASA JPL DE430t ephemeris data via skyfield for planetary positions,
    and Swiss Ephemeris for house calculations.
    
    Thin wrapper that conforms to the EphemerisAdapter protocol from crius-ephemeris-core.
    """
    
    def __init__(self, ephemeris_path: Optional[str] = None, retry_downloads: bool = True, use_shared_loader: bool = True):
        """
        Initialize adapter with JPL ephemeris data.
        
        Args:
            ephemeris_path: Optional path for Swiss Ephemeris data files (for houses).
                          If None, uses default /usr/local/share/swisseph
                          or SWISS_EPHEMERIS_PATH environment variable.
            retry_downloads: Whether to retry failed downloads (default: True)
            use_shared_loader: Whether to use shared loader instances (default: True, more efficient)
        
        Raises:
            EphemerisDownloadError: If ephemeris download fails
            EphemerisLoadError: If ephemeris data fails to load
        """
        # Use shared loader instances for efficiency (shared across all adapter instances)
        if use_shared_loader:
            self.ts, self.eph = _get_shared_loader()
        else:
            # Load JPL ephemeris (skyfield automatically downloads DE430t on first use)
            try:
                self.ts = load.timescale()
            except Exception as e:
                raise EphemerisLoadError(f"Failed to load skyfield timescale: {str(e)}") from e
            
            # Try to load ephemeris with retry logic
            max_retries = 3 if retry_downloads else 1
            
            for attempt in range(max_retries):
                try:
                    self.eph = load('de430t.bsp')
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        # Wait before retry (exponential backoff)
                        import time
                        time.sleep(2 ** attempt)
                    else:
                        # Check if it's a network/download error
                        error_str = str(e).lower()
                        if 'download' in error_str or 'network' in error_str or 'connection' in error_str:
                            raise EphemerisDownloadError(
                                f"Failed to download JPL ephemeris data after {max_retries} attempts: {str(e)}"
                            ) from e
                        else:
                            raise EphemerisLoadError(
                                f"Failed to load JPL ephemeris data: {str(e)}"
                            ) from e
        
        # Initialize Swiss Ephemeris for house calculations
        if ephemeris_path is None:
            ephemeris_path = os.getenv("SWISS_EPHEMERIS_PATH", "/usr/local/share/swisseph")
        swe.set_ephe_path(ephemeris_path)
        self.ephemeris_path = ephemeris_path
        
        # Cache for skyfield bodies (instance-level for thread safety)
        self._body_cache: dict[str, any] = {}

    def _get_body(self, planet_id: str):
        """Get Skyfield body object for a planet ID."""
        if planet_id in self._body_cache:
            return self._body_cache[planet_id]
        
        if planet_id not in SKYFIELD_BODIES:
            return None
        
        body_name = SKYFIELD_BODIES[planet_id]
        body = self.eph[body_name]
        self._body_cache[planet_id] = body
        return body

    def calc_positions(
        self,
        dt_utc: datetime,
        location: Optional[GeoLocation],
        settings: EphemerisSettings,
    ) -> LayerPositions:
        """
        Calculate planetary and house positions using JPL ephemeris.
        
        Planetary positions use JPL DE430t via skyfield.
        House calculations use Swiss Ephemeris.
        
        Args:
            dt_utc: UTC datetime for calculation
            location: Optional geographic location (required for houses)
            settings: Ephemeris calculation settings
            
        Returns:
            LayerPositions with planetary positions and optionally house positions
        
        Raises:
            DateRangeError: If date is outside JPL DE430t supported range (1550-2650 CE)
        """
        # Validate date range
        check_date_range(dt_utc, raise_error=True)
        
        # Convert datetime to Skyfield Time
        t = self.ts.utc(
            dt_utc.year,
            dt_utc.month,
            dt_utc.day,
            dt_utc.hour,
            dt_utc.minute,
            dt_utc.second + dt_utc.microsecond / 1_000_000.0
        )
        
        # Calculate planets
        planets: dict[str, PlanetPosition] = {}
        include_objects = settings.get("include_objects", [])

        for obj_id in include_objects:
            obj_id_lower = obj_id.lower()
            
            # Handle special cases
            if obj_id_lower == "south_node":
                # South Node is 180 degrees from North Node
                north_node_pos = self._calc_planet_position("north_node", t, dt_utc)
                if north_node_pos:
                    south_lon = (north_node_pos["lon"] + 180) % 360
                    planets["south_node"] = {
                        "lon": south_lon,
                        "lat": 0.0,
                        "speed_lon": north_node_pos["speed_lon"],
                        "retrograde": north_node_pos["retrograde"],
                    }
                continue

            if obj_id_lower == "north_node":
                # Calculate lunar nodes from moon's orbit
                node_pos = self._calc_lunar_node(t, dt_utc)
                if node_pos:
                    planets["north_node"] = node_pos
                continue

            if obj_id_lower == "chiron":
                # Chiron not available in JPL, use Swiss Ephemeris (hybrid approach)
                chiron_pos = self._calc_chiron_swiss(dt_utc, settings)
                if chiron_pos:
                    planets["chiron"] = chiron_pos
                continue

            planet_pos = self._calc_planet_position(obj_id_lower, t, dt_utc)
            if planet_pos:
                planets[obj_id_lower] = planet_pos

        # Calculate houses if location is provided (using Swiss Ephemeris)
        houses: Optional[HousePositions] = None
        if location:
            jd = _datetime_to_jd(dt_utc)
            house_system_bytes = _get_house_system_bytes(settings["house_system"])
            houses = self._calc_houses(jd, location["lat"], location["lon"], house_system_bytes, settings["house_system"])

        return {
            "planets": planets,
            "houses": houses,
        }

    def _calc_planet_position(self, planet_id: str, t: any, dt_utc: datetime) -> Optional[PlanetPosition]:
        """Calculate position for a single planet using JPL ephemeris."""
        if planet_id not in SKYFIELD_BODIES:
            return None

        try:
            body = self._get_body(planet_id)
            if body is None:
                return None

            # Get position relative to Earth (geocentric)
            earth = self.eph['earth']
            astrometric = earth.at(t).observe(body)
            
            # Convert to ecliptic coordinates
            lat, lon, distance = astrometric.frame_latlon(ecliptic_frame)
            
            # Convert to degrees
            longitude = lon.degrees % 360
            latitude = lat.degrees
            
            # Calculate speed by computing position at slightly different time
            # Use 1 hour difference for speed calculation
            from datetime import timedelta
            dt_next = dt_utc + timedelta(hours=1)
            t_next = self.ts.utc(
                dt_next.year,
                dt_next.month,
                dt_next.day,
                dt_next.hour,
                dt_next.minute,
                dt_next.second + dt_next.microsecond / 1_000_000.0
            )
            astrometric_next = earth.at(t_next).observe(body)
            lat_next, lon_next, _ = astrometric_next.frame_latlon(ecliptic_frame)
            
            # Calculate speed in degrees per day
            lon_diff = (lon_next.degrees - lon.degrees) % 360
            if lon_diff > 180:
                lon_diff -= 360
            speed_longitude = lon_diff * 24.0  # Convert from per-hour to per-day
            
            is_retrograde = speed_longitude < 0

            return {
                "lon": longitude,
                "lat": latitude,
                "speed_lon": speed_longitude,
                "retrograde": is_retrograde,
            }
        except Exception as e:
            # Log error but don't fail the entire calculation
            # In a package context, we might want to use a logger if available
            # For now, we'll just return None
            pass
        return None

    def _calc_lunar_node(self, t: any, dt_utc: datetime) -> Optional[PlanetPosition]:
        """Calculate lunar north node position from moon's orbit."""
        try:
            moon = self.eph['moon']
            earth = self.eph['earth']
            
            # Get moon's position relative to Earth
            astrometric = earth.at(t).observe(moon)
            lat, lon, distance = astrometric.frame_latlon(ecliptic_frame)
            
            # Lunar node is where moon crosses ecliptic (latitude = 0)
            # For simplicity, we'll use the ascending node approximation
            # More accurate calculation would find the actual node crossing
            
            # Use Swiss Ephemeris for accurate node calculation
            jd = _datetime_to_jd(dt_utc)
            result = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SWIEPH)
            if result and len(result) > 0:
                positions = result[0]
                longitude = positions[0] % 360
                speed_longitude = positions[3] if len(positions) > 3 else 0.0
                is_retrograde = speed_longitude < 0
                
                return {
                    "lon": longitude,
                    "lat": 0.0,
                    "speed_lon": speed_longitude,
                    "retrograde": is_retrograde,
                }
        except Exception:
            pass
        return None

    def _calc_chiron_swiss(self, dt_utc: datetime, settings: EphemerisSettings) -> Optional[PlanetPosition]:
        """
        Calculate Chiron position using Swiss Ephemeris (hybrid approach).
        
        Chiron is not available in JPL ephemeris, so we use Swiss Ephemeris
        for Chiron calculations while using JPL for other planets.
        
        Args:
            dt_utc: UTC datetime for calculation
            settings: Ephemeris settings (for zodiac type/flags)
            
        Returns:
            PlanetPosition for Chiron or None if calculation fails
        """
        try:
            jd = _datetime_to_jd(dt_utc)
            
            # Configure flags based on settings
            flags = swe.FLG_SWIEPH
            if settings.get("zodiac_type") == "sidereal":
                flags |= swe.FLG_SIDEREAL
                # Set ayanamsa if specified
                ayanamsa = settings.get("ayanamsa")
                if ayanamsa:
                    # Map ayanamsa to Swiss Ephemeris constant
                    from crius_swiss.adapter import AYANAMSA_MAP, DEFAULT_AYANAMSA
                    mode = AYANAMSA_MAP.get(ayanamsa.lower(), DEFAULT_AYANAMSA)
                    swe.set_sid_mode(mode, 0, 0)
            
            # Calculate Chiron using Swiss Ephemeris
            result = swe.calc_ut(jd, swe.CHIRON, flags)
            if result and len(result) > 0:
                positions = result[0]
                longitude = positions[0] % 360
                latitude = positions[1] if len(positions) > 1 else 0.0
                speed_longitude = positions[3] if len(positions) > 3 else 0.0
                is_retrograde = speed_longitude < 0
                
                return {
                    "lon": longitude,
                    "lat": latitude,
                    "speed_lon": speed_longitude,
                    "retrograde": is_retrograde,
                }
        except Exception:
            # If Swiss Ephemeris is not available or Chiron calculation fails,
            # return None (Chiron will be skipped)
            pass
        return None

    def _calc_houses(
        self,
        jd: float,
        lat: float,
        lon: float,
        house_system_bytes: bytes,
        house_system_str: str,
    ) -> HousePositions:
        """Calculate house cusps and angles using Swiss Ephemeris."""
        result = swe.houses_ex2(jd, lat, lon, house_system_bytes, swe.FLG_SWIEPH)

        if not result or len(result) == 0:
            return {
                "system": house_system_str,
                "cusps": {},
                "angles": {},
            }

        cusps = result[0]
        ascmc = result[1]

        # Extract house cusps
        cusps_dict: dict[str, float] = {}
        
        if len(cusps) == 12:
            # Whole Sign: cusps are indices 0-11 for houses 1-12
            for i in range(12):
                cusps_dict[str(i + 1)] = cusps[i] % 360
        else:
            # Placidus or other: indices 1-12 are houses 1-12
            for i in range(1, 13):
                if i < len(cusps):
                    cusps_dict[str(i)] = cusps[i] % 360

        # Extract angles
        asc = ascmc[0] % 360 if len(ascmc) > 0 else 0.0
        mc = ascmc[1] % 360 if len(ascmc) > 1 else 0.0
        ic = (mc + 180) % 360
        dc = (asc + 180) % 360

        return {
            "system": house_system_str,
            "cusps": cusps_dict,
            "angles": {
                "asc": asc,
                "mc": mc,
                "ic": ic,
                "dc": dc,
            },
        }

