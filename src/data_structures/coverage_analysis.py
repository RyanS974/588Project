"""
Data structures for representing coverage analysis results.
"""

from dataclasses import dataclass


@dataclass
class EdgeCaseAnalysis:
    """Simplified analysis of edge case coverage."""
    boundary_values_tested: bool
    null_handling_tested: bool
    error_conditions_tested: bool

    @property
    def coverage_score(self) -> float:
        """Calculates score based on 3 core checks."""
        true_count = sum([
            self.boundary_values_tested,
            self.null_handling_tested,
            self.error_conditions_tested
        ])
        return true_count / 3.0


@dataclass
class CoverageMetrics:
    """Core coverage proxy metrics."""
    test_to_code_ratio: float  # Test lines / Production lines
    assertion_density: float   # Assertions per test/code line
    edge_case_coverage: float  # Score from 0.0 to 1.0 based on EdgeCaseAnalysis


@dataclass
class PRCoverageAnalysis:
    """Complete coverage analysis for a PR."""
    pr_id: str
    metrics: CoverageMetrics
    edge_cases: EdgeCaseAnalysis
    adequacy_score: float  # Overall score from 0.0 to 1.0