"""
Aggregate data structures for analysis results and reporting.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .pr_data import AIAgent


@dataclass
class AnalysisSummary:
    """High-level summary of analysis across all PRs."""
    total_prs_analyzed: int
    test_inclusion_rate: float
    regression_test_rate: float
    # Metrics aggregated by agent (e.g., 'CODEX' vs. 'UNKNOWN')
    agent_performance: Dict[AIAgent, Dict[str, float]]


@dataclass
class StatisticalTestResult:
    """Generic holder for results of a statistical test (e.g., t-test)."""
    test_name: str
    p_value: float
    is_significant: bool
    details: Dict[str, Any]