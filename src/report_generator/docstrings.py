"""
Report Generator Component

This module provides report generation capabilities for the Testability Analysis Framework.
It creates various types of reports from analysis results in multiple formats suitable 
for different audiences and purposes.

Classes:
    ReportGenerator: Main class for managing report generation operations
    ReportConfig: Configuration class for report generation
    ReportData: Data structure for report input

Enums:
    ReportFormat: Supported report formats (MARKDOWN, CSV, JSON, PDF)
    ReportType: Supported report types (EXECUTIVE_SUMMARY, DETAILED_ANALYSIS, COMPLIANCE_REPORT, METRICS_OVERVIEW)

Exceptions:
    ReportGenerationError: Base exception for report generation operations
    InvalidDataError: Raised when invalid data is provided for reports
    UnsupportedFormatError: Raised when an unsupported report format is requested
    TemplateError: Raised when there's an issue with report templates
"""