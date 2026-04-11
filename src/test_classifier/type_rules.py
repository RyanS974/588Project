"""A simple, heuristic-based classifier for test types."""

from typing import Tuple
from src.data_structures.test_classification import TestType, TestClassificationFeatures


class TypeRuleEngine:
    """A simple, heuristic-based classifier for test types."""

    def classify(self, features: TestClassificationFeatures) -> Tuple[TestType, float]:
        """
        Classifies a test based on a simple set of rules.
        Returns the classified type and a confidence score.

        Classification logic:
        - UNIT: Tests with no external dependencies (with or without mocks)
        - INTEGRATION: Tests with external dependencies and few or no mocks
        - REGRESSION: Tests identified as regression tests (handled by regression_analyzer)
        - UNKNOWN: Fallback for tests that don't fit clear patterns
        """
        # Rule for UNIT tests: Presence of mocks, absence of external dependencies (high confidence)
        if features.mock_count > 0 and features.external_dependency_count == 0:
            return TestType.UNIT, 0.8

        # Rule for INTEGRATION tests: Presence of external deps, few or no mocks
        if features.external_dependency_count > 0 and features.mock_count <= 1:
            return TestType.INTEGRATION, 0.7

        # Fallback: If no external dependencies, lean towards UNIT
        if features.external_dependency_count == 0:
            return TestType.UNIT, 0.5

        # Default classification
        return TestType.UNKNOWN, 0.3