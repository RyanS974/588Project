"""Calculates a focused set of coverage proxy metrics."""

import re
import logging
from typing import Dict, List, Optional
from .constants import ASSERT_PATTERNS, CoverageMetricType
from .models import EdgeCaseAnalysis

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculates a focused set of coverage proxy metrics."""

    def calculate_all(self, test_content: str, prod_content: str,
                     test_additions: Optional[int] = None,
                     prod_additions: Optional[int] = None) -> Dict[CoverageMetricType, float]:
        """
        Calculates all scoped metrics.

        When working with patches, use additions counts for accurate line counts.
        Otherwise, falls back to counting lines in content strings.

        Args:
            test_content: Test file content (from patch or full file)
            prod_content: Production file content (from patch or full file)
            test_additions: Number of lines added in test file (from patch data)
            prod_additions: Number of lines added in production file (from patch data)
        """
        return {
            CoverageMetricType.TEST_TO_CODE_RATIO: self._calculate_test_to_code_ratio(
                test_content, prod_content, test_additions, prod_additions
            ),
            CoverageMetricType.ASSERTION_DENSITY: self._calculate_assertion_density(test_content),
        }

    def _calculate_test_to_code_ratio(self, test_content: str, prod_content: str,
                                      test_additions: Optional[int] = None,
                                      prod_additions: Optional[int] = None) -> float:
        """
        Calculates ratio of test lines to production code lines.

        Uses additions counts when available (for patch-based analysis),
        otherwise counts non-empty lines from content strings.
        """
        # Use additions counts from patch data if available
        if test_additions is not None and prod_additions is not None:
            test_lines = test_additions
            prod_lines = prod_additions
            logger.debug(f"Using patch additions: test={test_lines}, prod={prod_lines}")
        else:
            # Fall back to counting lines in content
            test_lines = len([line for line in test_content.splitlines() if line.strip()])
            prod_lines = len([line for line in prod_content.splitlines() if line.strip()])
            logger.debug(f"Using content line counts: test={test_lines}, prod={prod_lines}")

        if prod_lines == 0:
            return 0.0
        return min(1.0, test_lines / prod_lines)  # Cap at 1.0 for scoring

    def _calculate_assertion_density(self, test_content: str) -> float:
        """Calculates ratio of assertions to non-empty test lines."""
        test_lines = len([line for line in test_content.splitlines() if line.strip()])
        if test_lines == 0:
            return 0.0
        assertion_count = sum(len(re.findall(p.pattern, test_content, re.IGNORECASE)) for p in ASSERT_PATTERNS)
        return min(1.0, assertion_count / test_lines)  # Cap at 1.0 for scoring

    def calculate_edge_case_coverage_score(self, edge_cases: List[EdgeCaseAnalysis]) -> float:
        """Calculates a score based on the results from EdgeCaseDetector."""
        detected_cases = [ec for ec in edge_cases if ec.detected_in_code]
        if not detected_cases:
            return 1.0  # Perfect score if no edge cases were applicable/detected.

        tested_cases = sum(1 for ec in detected_cases if ec.is_tested)
        return tested_cases / len(detected_cases) if detected_cases else 0.0