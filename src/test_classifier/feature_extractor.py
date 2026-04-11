"""Extracts a focused set of features from test file content."""

import re
from typing import List
from .constants import (
    MOCK_PATTERNS, 
    ASSERT_PATTERNS, 
    EXTERNAL_DEP_PATTERNS, 
    SETUP_PATTERNS, 
    TEARDOWN_PATTERNS
)
from src.data_structures.test_classification import TestClassificationFeatures


class FeatureExtractor:
    """Extracts a focused set of features from test file content."""

    def extract(self, content: str, language: str) -> TestClassificationFeatures:
        """Extracts features using simple regex searches."""

        def count_patterns(patterns: List[str]) -> int:
            count = 0
            for pattern in patterns:
                count += len(re.findall(pattern, content, re.IGNORECASE))
            return count

        features = TestClassificationFeatures(
            assertion_count=count_patterns(ASSERT_PATTERNS),
            mock_count=count_patterns(MOCK_PATTERNS),
            external_dependency_count=count_patterns(EXTERNAL_DEP_PATTERNS),
            setup_method_present=count_patterns(SETUP_PATTERNS) > 0,
            teardown_present=count_patterns(TEARDOWN_PATTERNS) > 0
        )

        # Language-specific feature extraction
        if language.lower() == 'python':
            features.test_function_count = len(re.findall(r"def test_", content))
        elif language.lower() == 'java':
            features.test_annotation_count = len(re.findall(r"@Test", content))

        return features