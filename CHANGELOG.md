# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-01

### Added
- Initial release of crius-jpl
- `JplEphemerisAdapter` - JPL Ephemeris adapter implementation
- Uses NASA JPL DE430t ephemeris data via skyfield library
- Support for all major planets (Sun, Moon, Mercury through Pluto)
- Support for lunar nodes (calculated using Swiss Ephemeris for accuracy)
- Support for multiple house systems (via Swiss Ephemeris):
  - Placidus
  - Whole Sign
  - Koch
  - Equal
  - Regiomontanus
  - Campanus
  - Alcabitius
  - Morinus
- Automatic download and caching of DE430t ephemeris file (~16MB)
- Service factory functions:
  - `create_jpl_adapter()` - Create configured adapter instance
  - `calc_positions()` - Convenience function for calculations
- Configuration via environment variable (`SWISS_EPHEMERIS_PATH` for houses)
- MIT licensed (JPL ephemeris data is public domain)

### Known Limitations
- Chiron is not supported (not available in JPL ephemeris)
- Time range limited to 1550-2650 CE (JPL DE430t range)
- House calculations require Swiss Ephemeris data files

[0.1.0]: https://github.com/gaia-tools/crius-jpl/releases/tag/v0.1.0

