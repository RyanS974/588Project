"""
Constants for the Report Generator Component
Defines report formats, types, and other report-related constants
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


class ReportFormat(Enum):
    """Enumeration of supported report formats"""
    MARKDOWN = "md"
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


class ReportType(Enum):
    """Enumeration of supported report types"""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    COMPLIANCE_REPORT = "compliance_report"
    METRICS_OVERVIEW = "metrics_overview"


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    title: str = "Analysis Report"
    author: str = ""
    date: str = ""
    include_executive_summary: bool = True
    include_detailed_metrics: bool = True
    output_dir: str = "./reports"


@dataclass
class ReportData:
    """Data structure for report input"""
    project_name: str
    metrics: Dict[str, Any]
    analysis_results: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}