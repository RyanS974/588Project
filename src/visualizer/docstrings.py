"""
Visualizer Component

This module provides visualization capabilities for the Testability Analysis Framework.
It generates charts and graphs from analysis results, with special consideration for 
inclusion in LaTeX-based academic papers.

Classes:
    VisualizationManager: Main class for managing visualization operations
    ChartConfig: Configuration class for chart appearance
    VisualizationData: Data structure for visualization input

Enums:
    ChartType: Supported chart types (BAR, PIE, LINE, SCATTER)
    ExportFormat: Supported export formats (PNG, PDF, SVG)

Exceptions:
    VisualizationError: Base exception for visualization operations
    ChartGenerationError: Raised when chart generation fails
    InvalidDataError: Raised when invalid data is provided for visualization
    UnsupportedFormatError: Raised when an unsupported export format is requested
"""