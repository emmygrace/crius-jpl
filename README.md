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

## Features

- **High Precision**: Uses NASA JPL DE430t ephemeris data (accurate from 1550-2650 CE)
- **Planetary Positions**: All major planets (Sun, Moon, Mercury through Pluto)
- **House Calculations**: Uses Swiss Ephemeris for house system calculations
- **Protocol Compliant**: Implements `EphemerisAdapter` from `crius-ephemeris-core`
- **MIT Licensed**: Unlike Swiss Ephemeris, JPL data is public domain

## Supported Objects

- **Planets**: sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto
- **Lunar Nodes**: north_node, south_node (calculated using Swiss Ephemeris for accuracy)
- **Chiron**: Not currently supported (not in JPL ephemeris)

## Configuration

The adapter uses:
1. **JPL Ephemeris**: Automatically downloaded and cached by skyfield (DE430t)
2. **Swiss Ephemeris**: For house calculations and lunar nodes
   - Looks for data files in:
     - Path specified in constructor (`ephemeris_path`)
     - `SWISS_EPHEMERIS_PATH` environment variable
     - Default: `/usr/local/share/swisseph`

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

## Dependencies

- `crius-ephemeris-core` - Core types and interfaces
- `skyfield` - JPL ephemeris library
- `pyswisseph` - Swiss Ephemeris for house calculations
- `numpy` - Required by skyfield
- `pytz` - Timezone support

## Related Packages

- `crius-ephemeris-core` - Core types and interfaces (MIT licensed)
- `crius-swiss` - Swiss Ephemeris adapter implementation (AGPL licensed)

## Comparison with crius-swiss

| Feature | crius-jpl | crius-swiss |
|---------|-----------|-------------|
| Ephemeris Source | NASA JPL DE430t | Swiss Ephemeris |
| License | MIT | AGPL-3.0 |
| Time Range | 1550-2650 CE | 6000 BCE - 10000 CE |
| Precision | Very High | High |
| Chiron Support | No | Yes |
| House Systems | Via Swiss Ephemeris | Native |

Choose `crius-jpl` if you need MIT licensing and JPL precision. Choose `crius-swiss` if you need Chiron support or extended time ranges.

