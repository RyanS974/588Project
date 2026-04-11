"""
Data structures for representing standards comparison results.
"""

from dataclasses import dataclass


@dataclass
class IndustryStandard:
    """A simplified industry standard definition from a config file."""
    language: str
    # Project type is simplified to 'application' or a single other category.
    project_type: str
    metric_name: str # e.g., 'test_to_code_ratio'
    target_value: float


@dataclass
class StandardsComparison:
    """Comparison result of one metric against an industry standard."""
    pr_id: str
    language: str
    metric_name: str
    actual_value: float
    target_value: float
    gap: float  # actual - target
    meets_standard: bool