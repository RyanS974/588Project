"""
Main module for all data structures used in the Testability Analysis project.

This module imports and re-exports all data structures for easy access.
"""

from .pr_data import (
    AIAgent,
    PRStatus,
    FileChange,
    PullRequest
)
from .test_detection import (
    TestDetectionResult,
    PRTestDetection
)
from .test_classification import (
    TestType,
    TestClassificationFeatures,
    TestClassification,
    PRTestClassification
)
from .coverage_analysis import (
    EdgeCaseAnalysis,
    CoverageMetrics,
    PRCoverageAnalysis
)
from .regression_analysis import (
    RegressionTest,
    RegressionAnalysis
)
from .standards_comparison import (
    IndustryStandard,
    StandardsComparison
)
from .aggregate_results import (
    AnalysisSummary,
    StatisticalTestResult
)
from .data_manager import DataManager

__all__ = [
    # PR Data
    'AIAgent', 'PRStatus', 'FileChange', 'PullRequest',
    
    # Test Detection
    'TestDetectionResult', 'PRTestDetection',
    
    # Test Classification
    'TestType', 'TestClassificationFeatures', 'TestClassification', 'PRTestClassification',
    
    # Coverage Analysis
    'EdgeCaseAnalysis', 'CoverageMetrics', 'PRCoverageAnalysis',
    
    # Regression Analysis
    'RegressionTest', 'RegressionAnalysis',
    
    # Standards Comparison
    'IndustryStandard', 'StandardsComparison',
    
    # Aggregate Results
    'AnalysisSummary', 'StatisticalTestResult',
    
    # Data Manager
    'DataManager'
]