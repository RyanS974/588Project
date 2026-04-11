"""
Custom exceptions for the Report Generator Component
"""
class ReportGenerationError(Exception):
    """Base exception for report generation operations"""
    pass


class InvalidDataError(ReportGenerationError):
    """Raised when invalid data is provided for report generation"""
    pass


class UnsupportedFormatError(ReportGenerationError):
    """Raised when an unsupported report format is requested"""
    pass


class TemplateError(ReportGenerationError):
    """Raised when there's an issue with report templates"""
    pass