"""Assesses the quality of regression tests with a few simple heuristics."""

import re
from typing import Tuple, List
from .constants import MINIMAL_TEST_LINE_COUNT, ISSUE_LINK_PATTERNS


class RegressionQualityAssessor:
    """Assesses the quality of regression tests with a few simple heuristics."""

    def assess(self, test_content: str, pr_description: str, commit_messages: List[str]) -> Tuple[float, bool, bool]:
        """
        Performs a basic quality assessment.
        Returns: (quality_score, reproduces_issue, is_minimal)
        """
        score = 0.5  # Start at a neutral score

        # 1. Reproduces Issue Heuristic
        reproduces_issue = False
        all_context = pr_description + " ".join(commit_messages)
        linked_issues = []
        for pattern in ISSUE_LINK_PATTERNS:
            linked_issues.extend(pattern.findall(all_context))

        if linked_issues and any(issue_id in test_content for issue_id in linked_issues):
            reproduces_issue = True
            score += 0.4

        # 2. Minimal Heuristic
        line_count = len(test_content.splitlines())
        is_minimal = line_count < MINIMAL_TEST_LINE_COUNT
        if is_minimal:
            score += 0.2
        else:
            score -= 0.1

        # 3. Clarity Heuristic (presence of assertions)
        # Look for assert statements, not just the word "assert" in comments
        if re.search(r"(^|\s)assert\s", test_content, re.IGNORECASE):
            score += 0.1
        else:
            score -= 0.3  # Penalize regression tests with no assertions

        return max(0, min(1, score)), reproduces_issue, is_minimal