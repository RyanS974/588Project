"""Custom exceptions for the standards_comparator package."""


class StandardsComparisonError(Exception):
    """Base exception for standards comparison-related errors."""
    pass


class InvalidStandardError(StandardsComparisonError):
    """Raised when an invalid standard is encountered."""
    pass


class MissingMetricError(StandardsComparisonError):
    """Raised when a required metric is missing for comparison."""
    pass