"""Main orchestrator for simplified regression analysis."""

import logging
from typing import List, Dict
from .identifier import RegressionIdentifier
from .quality_assessor import RegressionQualityAssessor
from .models import RegressionAnalysisResult


class RegressionAnalyzer:
    """Main orchestrator for simplified regression analysis."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.identifier = RegressionIdentifier()
        self.quality_assessor = RegressionQualityAssessor()

    def analyze(self, pr_data: Dict, test_classifications: List) -> List[RegressionAnalysisResult]:
        """
        Analyzes all test files in a PR for regression characteristics.

        Args:
            pr_data: A dictionary containing PR-level data like description, commit messages, and linked issues.
            test_classifications: A list of classification results for the test files in the PR.

        Returns:
            A list of RegressionAnalysisResult objects.
        """
        results = []
        commit_messages = pr_data.get('commit_messages', [])
        pr_description = pr_data.get('description', "")

        for test in test_classifications:
            # 1. Identify regression test and its type
            is_regression, confidence, reg_type = self.identifier.identify(
                commit_messages, pr_description, test.file_path, getattr(test, 'content', '')
            )

            if not is_regression:
                continue  # Skip non-regression tests

            # 2. Perform basic quality assessment
            quality_score, reproduces_issue, is_minimal = self.quality_assessor.assess(
                getattr(test, 'content', ''), pr_description, commit_messages
            )

            # 3. Assemble and store the result
            results.append(RegressionAnalysisResult(
                test_file_path=test.file_path,
                is_regression_test=True,
                identification_confidence=confidence,
                regression_type=reg_type,
                reproduces_issue_heuristically=reproduces_issue,
                is_minimal_heuristic=is_minimal,
                quality_score=quality_score
            ))

        return results