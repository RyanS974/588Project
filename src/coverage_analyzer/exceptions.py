"""Custom exceptions for the coverage_analyzer package."""


class CoverageAnalysisError(Exception):
    """Base exception for coverage analysis-related errors."""
    pass


class UnsupportedLanguageError(CoverageAnalysisError):
    """Raised when a file with an unsupported language is processed."""
    pass


class CoverageConfigurationError(CoverageAnalysisError):
    """Raised when there's an issue with the coverage analysis configuration."""
    pass