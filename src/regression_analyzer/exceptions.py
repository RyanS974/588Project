"""Custom exceptions for the regression_analyzer package."""


class RegressionAnalysisError(Exception):
    """Base exception for regression analysis-related errors."""
    pass


class InvalidInputError(RegressionAnalysisError):
    """Raised when invalid input is provided to the analyzer."""
    pass


class ConfigurationError(RegressionAnalysisError):
    """Raised when there's an issue with the regression analysis configuration."""
    pass