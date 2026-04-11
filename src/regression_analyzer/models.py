"""Data structures for the regression_analyzer package."""

from dataclasses import dataclass
from enum import Enum


class RegressionType(Enum):
    """Scoped types of regression a test might address."""
    BUG_FIX = "bug_fix"
    FEATURE = "feature"
    UNKNOWN = "unknown"


@dataclass
class RegressionAnalysisResult:
    """A simplified, combined result for a single identified regression test."""
    test_file_path: str
    is_regression_test: bool
    identification_confidence: float  # 0.0 to 1.0
    regression_type: RegressionType

    # Basic quality assessment fields
    reproduces_issue_heuristically: bool  # True if test content mentions a linked bug/issue ID
    is_minimal_heuristic: bool  # True if test file has a low line/function count
    quality_score: float  # A simple score from 0.0 to 1.0