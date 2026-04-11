"""Module containing data structures for the coverage_analyzer package."""
from dataclasses import dataclass
from .constants import EdgeCaseType


@dataclass
class EdgeCaseAnalysis:
    """Simplified analysis of a single edge case type."""
    edge_case_type: EdgeCaseType
    detected_in_code: bool
    is_tested: bool