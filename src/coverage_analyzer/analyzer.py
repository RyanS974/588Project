"""Orchestrates coverage analysis using simplified proxy metrics."""

import logging
from typing import Dict, Optional
from .metrics_calculator import MetricsCalculator
from .edge_case_detector import EdgeCaseDetector
from .constants import METRIC_WEIGHTS, CoverageMetricType, EdgeCaseType
from .models import EdgeCaseAnalysis
from src.data_structures.coverage_analysis import (
    CoverageMetrics,
    EdgeCaseAnalysis as DataStructuresEdgeCaseAnalysis,
    PRCoverageAnalysis
)


class CoverageAnalyzer:
    """Orchestrates coverage analysis using simplified proxy metrics."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_calculator = MetricsCalculator()
        self.edge_case_detector = EdgeCaseDetector()

    def analyze(self, pr_id: str, test_file_path: str, test_content: str, prod_content: str,
                test_additions: Optional[int] = None, prod_additions: Optional[int] = None) -> PRCoverageAnalysis:
        """
        Analyzes a single test/production code pair.

        Args:
            pr_id: The ID of the pull request being analyzed
            test_file_path: Path to the test file
            test_content: Content of the test file
            prod_content: Content of the corresponding production code file
            test_additions: Number of lines added in test file (from patch data)
            prod_additions: Number of lines added in production file (from patch data)

        Returns:
            A PRCoverageAnalysis object with all calculated data.
        """
        # 1. Calculate the 3 core metrics
        # Pass additions counts if available for accurate patch-based metrics
        metrics = self.metrics_calculator.calculate_all(
            test_content, prod_content, test_additions, prod_additions
        )

        # 2. Detect edge cases and assess their coverage
        edge_case_analyses = self.edge_case_detector.analyze(test_content, prod_content)

        # Calculate edge case coverage score
        edge_case_coverage_score = self.metrics_calculator.calculate_edge_case_coverage_score(edge_case_analyses)
        metrics[CoverageMetricType.EDGE_CASE_COVERAGE] = edge_case_coverage_score

        # 3. Calculate a final, weighted adequacy score
        adequacy_score = self._calculate_adequacy_score(metrics)

        # 4. Create the data structure representations for the results
        # Convert the internal EdgeCaseAnalysis objects to the data structure format
        boundary_values_tested = any(
            ec.is_tested for ec in edge_case_analyses
            if ec.edge_case_type == EdgeCaseType.BOUNDARY_VALUE
        )
        null_handling_tested = any(
            ec.is_tested for ec in edge_case_analyses
            if ec.edge_case_type == EdgeCaseType.NULL_HANDLING
        )
        error_conditions_tested = any(
            ec.is_tested for ec in edge_case_analyses
            if ec.edge_case_type == EdgeCaseType.ERROR_CONDITION
        )

        edge_case_result = DataStructuresEdgeCaseAnalysis(
            boundary_values_tested=boundary_values_tested,
            null_handling_tested=null_handling_tested,
            error_conditions_tested=error_conditions_tested
        )

        # Create the metrics object
        coverage_metrics = CoverageMetrics(
            test_to_code_ratio=metrics[CoverageMetricType.TEST_TO_CODE_RATIO],
            assertion_density=metrics[CoverageMetricType.ASSERTION_DENSITY],
            edge_case_coverage=metrics[CoverageMetricType.EDGE_CASE_COVERAGE]
        )

        # 5. Assemble the result
        return PRCoverageAnalysis(
            pr_id=pr_id,
            metrics=coverage_metrics,
            edge_cases=edge_case_result,
            adequacy_score=adequacy_score
        )

    def _calculate_adequacy_score(self, metrics: Dict[CoverageMetricType, float]) -> float:
        """Calculates a simple weighted score from the core metrics."""
        score = 0.0
        for metric, weight in METRIC_WEIGHTS.items():
            score += metrics.get(metric, 0.0) * weight
        return min(1.0, score)  # Ensure score is capped at 1.0