"""
Data structures for representing test classification results.
"""

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


class TestType(Enum):
    """Scoped enumeration of software test types."""
    UNIT = "unit"           # Tests with no external dependencies
    INTEGRATION = "integration"  # Tests with external dependencies
    REGRESSION = "regression"
    UNKNOWN = "unknown"


class TestQualityLevel(Enum):
    """Simplified quality levels for tests."""
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class TestClassificationFeatures:
    """Simplified set of features extracted for test classification."""
    assertion_count: int = 0
    mock_count: int = 0
    external_dependency_count: int = 0
    setup_method_present: bool = False
    teardown_present: bool = False
    # Language-specific
    test_function_count: int = 0  # For Python
    test_annotation_count: int = 0  # For Java


@dataclass
class TestClassification:
    """Classification result for a single test file."""
    file_path: str
    primary_type: TestType
    confidence: float
    features: TestClassificationFeatures
    quality_level: TestQualityLevel = TestQualityLevel.FAIR  # Default value
    quality_score: float = 0.5  # Default score


@dataclass
class PRTestClassification:
    """Complete test classification for a PR."""
    pr_id: str
    classifications: List[TestClassification]
    type_distribution: Dict[TestType, int]