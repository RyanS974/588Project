"""Data structures and constants for the standards_comparator package."""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Standard:
    """A simplified definition of a single standard for one metric."""
    metric_name: str
    threshold: float
    description: str = ""


@dataclass
class StandardSet:
    """A collection of standards for a specific context (e.g., python-application)."""
    id: str
    language: str
    project_type: str  # e.g., "application"
    standards: List[Standard]


@dataclass
class ComparisonResult:
    """Result of comparing a PR's metric against one standard."""
    pr_id: str
    test_file_path: str
    metric_name: str
    actual_value: float
    standard_threshold: float
    meets_standard: bool
    gap: float  # (actual_value - standard_threshold)
    qualitative_grade: Optional[str] = None  # "Poor", "Fair", "Good", "Excellent"