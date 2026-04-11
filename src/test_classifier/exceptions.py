"""Custom exceptions for the test_classifier package."""


class ClassificationError(Exception):
    """Base exception for classification-related errors."""
    pass


class UnsupportedLanguageError(ClassificationError):
    """Raised when a file with an unsupported language is processed."""
    pass


class ClassificationConfigurationError(ClassificationError):
    """Raised when there's an issue with the classification configuration."""
    pass