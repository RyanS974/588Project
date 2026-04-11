"""
Custom exceptions for the Visualizer Component
"""
class VisualizationError(Exception):
    """Base exception for visualization operations"""
    pass


class ChartGenerationError(VisualizationError):
    """Raised when chart generation fails"""
    pass


class InvalidDataError(VisualizationError):
    """Raised when invalid data is provided for visualization"""
    pass


class UnsupportedFormatError(VisualizationError):
    """Raised when an unsupported export format is requested"""
    pass