"""
Data structures for representing regression analysis results.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RegressionTest:
    """Identified regression test with simplified quality assessment."""
    test_file_path: str
    linked_issue_id: Optional[str]
    # Type is focused on 'BUG_FIX' or 'FUNCTIONAL_CHANGE'
    regression_type: str
    confidence: float
    quality_score: float  # Score based on minimal criteria
    reproduces_issue: bool  # Heuristic: checks for issue ID/keywords in test
    minimal: bool       # Heuristic: checks test size/scope


@dataclass
class RegressionAnalysis:
    """Regression test analysis for a PR."""
    pr_id: str
    regression_tests: List[RegressionTest]
    has_regression_tests: bool