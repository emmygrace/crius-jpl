# crius-jpl

**Crius** - JPL Ephemeris adapter implementation for astrological calculations.

Named after [Crius](https://en.wikipedia.org/wiki/Crius), the Titan of constellations and measuring the year in Greek mythology.

## Overview

This package provides a JPL Ephemeris adapter implementation that conforms to the `crius-ephemeris-core` protocol. It uses NASA JPL's DE430t ephemeris data via the `skyfield` library for high-precision planetary positions.

**License Notice**: This package is licensed under MIT. JPL ephemeris data is in the public domain, and skyfield is BSD licensed. House calculations use Swiss Ephemeris (AGPL/LGPL licensed).

## Installation

```bash
pip install crius-jpl
```

Or for development:

```bash
pip install -e crius-jpl
```

**Note**: On first use, skyfield will automatically download the DE430t ephemeris file (~16MB). This is a one-time download that is cached locally.

## Usage

### Basic Usage

```python
from crius_jpl import JplEphemerisAdapter
from crius_ephemeris_core import EphemerisSettings, GeoLocation
from datetime import datetime, timezone

# Initialize adapter (optionally specify Swiss Ephemeris path for houses)
adapter = JplEphemerisAdapter(ephemeris_path="/path/to/swisseph")

# Define settings and location
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

# Calculate positions
dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
positions = adapter.calc_positions(dt, location, settings)

print(positions["planets"]["sun"])
```

### Using the Service Entrypoint

For convenience, you can use the service factory function:

```python
from crius_jpl import create_jpl_adapter, calc_positions
from datetime import datetime, timezone

# Create adapter using factory (respects SWISS_EPHEMERIS_PATH env var)
adapter = create_jpl_adapter()

# Or use the convenience function directly
positions = calc_positions(
    dt_utc=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    location={"lat": 40.7128, "lon": -74.0060},
    settings={
        "zodiac_type": "tropical",
        "ayanamsa": None,
        "house_system": "placidus",
        "include_objects": ["sun", "moon"],
    }
)
```

### Configuration via Environment Variables

The adapter can be configured using environment variables:

- `SWISS_EPHEMERIS_PATH`: Path to Swiss Ephemeris data files (default: `/usr/local/share/swisseph`)

Example:

```bash
export SWISS_EPHEMERIS_PATH=/custom/path/to/swisseph
python your_script.py
```

## Features

- **High Precision**: Uses NASA JPL DE430t ephemeris data (accurate from 1550-2650 CE)
- **Planetary Positions**: All major planets (Sun, Moon, Mercury through Pluto)
- **Chiron Support**: Hybrid approach using Swiss Ephemeris for Chiron
- **Lunar Nodes**: Accurate node calculations using Swiss Ephemeris
- **House Calculations**: Uses Swiss Ephemeris for house system calculations
- **Protocol Compliant**: Implements `EphemerisAdapter` from `crius-ephemeris-core`
- **MIT Licensed**: Unlike Swiss Ephemeris, JPL data is public domain
- **Performance Optimized**: Shared loader instances and body caching
- **Error Handling**: Comprehensive error handling with retry logic for downloads

## Supported Objects

- **Planets**: sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto
- **Lunar Nodes**: north_node, south_node (calculated using Swiss Ephemeris for accuracy)
- **Chiron**: Supported via hybrid approach (uses Swiss Ephemeris for Chiron calculations)

## Configuration

The adapter uses:
1. **JPL Ephemeris**: Automatically downloaded and cached by skyfield (DE430t)
   - Downloaded on first use (~16MB)
   - Cached locally for subsequent uses
   - Shared across adapter instances for efficiency
2. **Swiss Ephemeris**: For house calculations, lunar nodes, and Chiron
   - Looks for data files in:
     - Path specified in constructor (`ephemeris_path`)
     - `SWISS_EPHEMERIS_PATH` environment variable
     - Default: `/usr/local/share/swisseph`

### Error Handling

The adapter includes comprehensive error handling:

- **Download Failures**: Automatic retry with exponential backoff
- **Date Range Validation**: Clear errors for dates outside 1550-2650 CE
- **Load Errors**: Detailed error messages for troubleshooting

```python
from crius_jpl import JplEphemerisAdapter, DateRangeError, EphemerisDownloadError

try:
    adapter = JplEphemerisAdapter(retry_downloads=True)
except EphemerisDownloadError as e:
    print(f"Failed to download ephemeris: {e}")
    # Handle download failure
```

### Performance

The adapter is optimized for performance:

- **Shared Loaders**: Skyfield loader instances are shared across adapter instances
- **Body Caching**: Planet body objects are cached for faster lookups
- **Efficient Calculations**: Optimized position calculations

You can disable shared loaders if needed:

```python
# Use separate loader (less efficient but more isolated)
adapter = JplEphemerisAdapter(use_shared_loader=False)
```

## House Systems

House calculations use Swiss Ephemeris and support:
- Placidus (default)
- Whole Sign
- Koch
- Equal
- Regiomontanus
- Campanus
- Alcabitius
- Morinus

## License

**MIT License** - JPL ephemeris data is in the public domain, and skyfield is BSD licensed.

Note: House calculations use Swiss Ephemeris, which is dual-licensed under AGPL or a commercial license. For house calculations only, this typically doesn't affect the MIT license of this package, but users should be aware of Swiss Ephemeris licensing for house calculations.

## Progressed Charts

The adapter supports progressed chart calculations. To calculate progressed positions, simply use a different datetime:

```python
# Natal chart
natal_dt = datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
natal_positions = adapter.calc_positions(natal_dt, location, settings)

# Progressed chart (1 day = 1 year progression)
progressed_dt = datetime(1990, 1, 1 + days_since_birth, 12, 0, 0, tzinfo=timezone.utc)
progressed_positions = adapter.calc_positions(progressed_dt, location, settings)
```

**Note**: Progressed calculations work the same as regular calculations - just use the progressed datetime. The adapter doesn't distinguish between natal and progressed charts.

## Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=crius_jpl --cov-report=html

# Run performance tests
pytest tests/test_performance.py -m performance
```

## Dependencies

- `crius-ephemeris-core` - Core types and interfaces
- `skyfield` - JPL ephemeris library
- `pyswisseph` - Swiss Ephemeris for house calculations
- `numpy` - Required by skyfield
- `pytz` - Timezone support

### Development Dependencies

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `mypy` - Type checking
- `black` - Code formatting
- `ruff` - Linting

## Related Packages

- `crius-ephemeris-core` - Core types and interfaces (MIT licensed)
- `crius-swiss` - Swiss Ephemeris adapter implementation (AGPL licensed)

## Time Range

JPL DE430t ephemeris data supports dates from **1550 CE to 2650 CE**. Dates outside this range will raise a `DateRangeError`.

```python
from crius_jpl import JplEphemerisAdapter, DateRangeError, JPL_MIN_DATE, JPL_MAX_DATE
from datetime import datetime, timezone

adapter = JplEphemerisAdapter()

# Valid date (within range)
dt_valid = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
positions = adapter.calc_positions(dt_valid, location, settings)  # OK

# Invalid date (outside range)
dt_invalid = datetime(1000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
try:
    positions = adapter.calc_positions(dt_invalid, location, settings)
except DateRangeError as e:
    print(f"Date out of range: {e}")
```

You can check the supported range:

```python
from crius_jpl import JPL_MIN_DATE, JPL_MAX_DATE

print(f"Supported range: {JPL_MIN_DATE} to {JPL_MAX_DATE}")
```

For dates outside this range, consider using `crius-swiss` which supports a much wider range (6000 BCE - 10000 CE).

## Lunar Nodes

Lunar nodes (north and south) are calculated using Swiss Ephemeris for accuracy, even though planetary positions use JPL ephemeris. This hybrid approach ensures accurate node calculations.

```python
settings: EphemerisSettings = {
    "zodiac_type": "tropical",
    "ayanamsa": None,
    "house_system": "placidus",
    "include_objects": ["north_node", "south_node"],
}

positions = adapter.calc_positions(dt, location, settings)

north_node = positions["planets"]["north_node"]
south_node = positions["planets"]["south_node"]

# South node is always 180 degrees from north node
assert abs((south_node["lon"] - north_node["lon"]) % 360 - 180) < 1.0
```

**Calculation Method**: The adapter uses Swiss Ephemeris's `TRUE_NODE` calculation for accurate lunar node positions. This provides high precision node calculations that match Swiss Ephemeris results.

## Chiron Support

Chiron is supported via a hybrid approach: while most planets use JPL ephemeris, Chiron calculations use Swiss Ephemeris (since Chiron is not available in JPL ephemeris data).

```python
settings: EphemerisSettings = {
    "zodiac_type": "tropical",
    "ayanamsa": None,
    "house_system": "placidus",
    "include_objects": ["chiron"],
}

positions = adapter.calc_positions(dt, location, settings)
chiron_pos = positions["planets"]["chiron"]
```

**Note**: Chiron support requires Swiss Ephemeris data files to be available (same as for house calculations). If Swiss Ephemeris is not available, Chiron will be skipped.

## Comparison with crius-swiss

| Feature | crius-jpl | crius-swiss |
|---------|-----------|-------------|
| Ephemeris Source | NASA JPL DE430t | Swiss Ephemeris |
| License | MIT | AGPL-3.0 |
| Time Range | 1550-2650 CE | 6000 BCE - 10000 CE |
| Precision | Very High | High |
| Chiron Support | Yes (via Swiss Ephemeris) | Yes (native) |
| House Systems | Via Swiss Ephemeris | Native |
| Lunar Nodes | Via Swiss Ephemeris | Native |
| Data Download | Automatic (~16MB) | Manual installation required |

### When to Use crius-jpl

- You need **MIT licensing** (JPL data is public domain)
- You're working with dates in the **1550-2650 CE range**
- You want **very high precision** planetary positions
- You can accept automatic download of ephemeris data

### When to Use crius-swiss

- You need dates **outside 1550-2650 CE** (e.g., historical charts)
- You prefer **AGPL licensing** or have a commercial Swiss Ephemeris license
- You want **native support** for all features (no hybrid approach)
- You prefer **manual control** over ephemeris data files

Both adapters are protocol-compliant and can be used interchangeably in most cases.

