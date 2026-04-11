"""Main test file classification logic."""

import logging
from .feature_extractor import FeatureExtractor
from .type_rules import TypeRuleEngine
from .quality_analyzer import QualityAnalyzer
from src.data_structures.test_detection import TestDetectionResult
from src.data_structures.test_classification import TestClassification, TestClassificationFeatures


class TestClassifier:
    """Orchestrates test file classification using simplified, heuristic-based logic."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feature_extractor = FeatureExtractor()
        self.rule_engine = TypeRuleEngine()
        self.quality_analyzer = QualityAnalyzer()

    def classify_test_file(self, test_file: TestDetectionResult, content: str) -> TestClassification:
        """
        Classifies a single test file.

        Args:
            test_file: The TestDetectionResult object for the file.
            content: The full content of the file.

        Returns:
            A TestClassification object.
        """
        # 1. Extract a limited set of features
        features = self.feature_extractor.extract(content, test_file.language)

        # 2. Apply simple rules to determine the test type
        test_type, confidence = self.rule_engine.classify(features)

        # 3. Assess basic quality
        quality_level, quality_score = self.quality_analyzer.assess(features, content)

        # 4. Assemble the result
        return TestClassification(
            file_path=test_file.file_path,
            primary_type=test_type,
            confidence=confidence,
            features=features,
            quality_level=quality_level,
            quality_score=quality_score
        )