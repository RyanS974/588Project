"""Detects a limited set of critical edge cases and checks if they are tested."""

import re
from typing import List
from .constants import EDGE_CASE_PATTERNS
from .models import EdgeCaseType, EdgeCaseAnalysis


class EdgeCaseDetector:
    """Detects a limited set of critical edge cases and checks if they are tested."""

    def analyze(self, test_content: str, prod_content: str) -> List[EdgeCaseAnalysis]:
        """
        Analyzes the code for the presence and testing of the three core edge cases.
        """
        results = []
        for ec_type, patterns in EDGE_CASE_PATTERNS.items():
            detected_in_code = any(p.search(prod_content) for p in patterns["code"])
            is_tested = any(p.search(test_content) for p in patterns["test"])

            results.append(EdgeCaseAnalysis(
                edge_case_type=ec_type,
                detected_in_code=detected_in_code,
                is_tested=is_tested
            ))
        return results