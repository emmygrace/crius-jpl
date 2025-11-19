"""Custom exceptions for crius-jpl."""


class CriusJplError(Exception):
    """Base exception for crius-jpl errors."""

    pass


class EphemerisDownloadError(CriusJplError):
    """Raised when skyfield fails to download JPL ephemeris data."""

    def __init__(self, message: str = None, url: str = None):
        """
        Initialize exception.

        Args:
            message: Optional custom message
            url: Optional URL that failed to download
        """
        self.url = url
        if message is None:
            message = (
                "Failed to download JPL ephemeris data.\n"
                "This usually indicates a network connectivity issue.\n"
                "Please check your internet connection and try again.\n"
            )
            if url:
                message += f"\nFailed URL: {url}"
        super().__init__(message)


class DateRangeError(CriusJplError):
    """Raised when a date is outside the supported JPL range."""

    def __init__(self, date, min_date=None, max_date=None):
        """
        Initialize exception.

        Args:
            date: Date that is out of range
            min_date: Minimum supported date (default: 1550-01-01)
            max_date: Maximum supported date (default: 2650-12-31)
        """
        self.date = date
        self.min_date = min_date or "1550-01-01"
        self.max_date = max_date or "2650-12-31"
        message = (
            f"Date {date} is outside the supported JPL DE430t range.\n"
            f"Supported range: {self.min_date} to {self.max_date}\n"
            f"For dates outside this range, consider using crius-swiss instead."
        )
        super().__init__(message)


class EphemerisLoadError(CriusJplError):
    """Raised when JPL ephemeris data fails to load."""

    def __init__(self, message: str = None, filepath: str = None):
        """
        Initialize exception.

        Args:
            message: Optional custom message
            filepath: Optional path to file that failed to load
        """
        self.filepath = filepath
        if message is None:
            message = "Failed to load JPL ephemeris data."
            if filepath:
                message += f"\nFile: {filepath}"
        super().__init__(message)

