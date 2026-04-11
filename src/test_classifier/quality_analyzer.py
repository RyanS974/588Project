"""Performs a basic assessment of test code quality."""

import re
from typing import Tuple
from .constants import FLAKY_PATTERNS, COMPLEX_TEST_LINE_THRESHOLD
from src.data_structures.test_classification import TestQualityLevel, TestClassificationFeatures


class QualityAnalyzer:
    """Performs a basic assessment of test code quality."""

    def assess(self, features: TestClassificationFeatures, content: str) -> Tuple[TestQualityLevel, float]:
        """
        Calculates a simplified quality score and returns a level.

        Adjusted thresholds to create more balanced distribution:
        - GOOD: Score >= 0.5 (tests with basic quality indicators)
        - FAIR: Score >= 0.3 (tests meeting minimum criteria)
        - POOR: Score < 0.3 (tests lacking basic quality)
        """
        score = 0.4  # Start closer to FAIR threshold

        # Positive indicators (more generous)
        if features.assertion_count > 0:
            score += 0.15
        if features.setup_method_present or features.teardown_present:
            score += 0.1  # Only need one of setup/teardown
        if features.assertion_count >= 2:
            score += 0.1  # Bonus for having multiple assertions
        if features.test_function_count >= 2:
            score += 0.05  # Bonus for multiple test functions

        # Negative indicators (reduced penalties)
        if len(re.findall("|".join(FLAKY_PATTERNS), content, re.IGNORECASE)) > 0:
            score -= 0.1  # Reduced penalty for flaky patterns

        if len(content.splitlines()) > COMPLEX_TEST_LINE_THRESHOLD:
            score -= 0.1  # Reduced penalty for long tests

        if features.assertion_count == 0:
            score -= 0.2  # Reduced penalty for no assertions (from -0.3)

        # Normalize score to be between 0 and 1
        final_score = max(0, min(1, score))

        if final_score >= 0.5:
            return TestQualityLevel.GOOD, final_score
        elif final_score >= 0.3:
            return TestQualityLevel.FAIR, final_score
        else:
            return TestQualityLevel.POOR, final_score