"""Custom exceptions for the test_detector package."""


class DetectionError(Exception):
    """Base exception for detection-related errors."""
    pass


class UnsupportedLanguageError(DetectionError):
    """Raised when a file with an unsupported language is processed."""
    pass


class DetectionConfigurationError(DetectionError):
    """Raised when there's an issue with the detection configuration."""
    pass