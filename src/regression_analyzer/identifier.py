"""Identifies and classifies regression tests using simple heuristics."""

import re
from typing import List, Tuple, Optional
from .constants import REGRESSION_KEYWORDS, IDENTIFICATION_CONFIDENCE_THRESHOLD, IDENTIFICATION_METHOD_WEIGHTS, ISSUE_LINK_PATTERNS
from .models import RegressionType


class RegressionIdentifier:
    """Identifies and classifies regression tests using simple heuristics."""

    def identify(self, commit_messages: List[str], pr_description: str, test_file_path: str, test_content: str) -> Tuple[bool, float, RegressionType]:
        """
        Identifies if a test is a regression test and classifies its type.

        Returns:
            A tuple: (is_regression, confidence, regression_type).
        """
        all_text = pr_description + " " + " ".join(commit_messages)
        confidence = 0.0

        # Extract all issue links from the text
        linked_issues = self._extract_issue_links(all_text)

        # Check if test content references any of the linked issues
        has_linked_issue_reference = False
        if linked_issues:
            if any(issue_id in test_content for issue_id in linked_issues):
                confidence += IDENTIFICATION_METHOD_WEIGHTS["linked_bug_issue"]
                has_linked_issue_reference = True

        # Determine regression type based on keyword analysis
        regression_type = self._classify_regression_type(all_text, linked_issues)

        # Boost confidence if we have clear regression indicators
        if regression_type != RegressionType.UNKNOWN:
            confidence += IDENTIFICATION_METHOD_WEIGHTS["commit_message_keywords"]

        is_regression = confidence >= IDENTIFICATION_CONFIDENCE_THRESHOLD

        if is_regression:
            return True, min(1.0, confidence), regression_type
        else:
            return False, confidence, regression_type

    def _extract_issue_links(self, text: str) -> List[str]:
        """
        Extract issue references from text using multiple patterns.

        Returns:
            List of issue IDs found in the text.
        """
        linked_issues = []
        for pattern in ISSUE_LINK_PATTERNS:
            matches = pattern.findall(text)
            linked_issues.extend(matches)
        return linked_issues

    def _classify_regression_type(self, text: str, linked_issues: List[str]) -> RegressionType:
        """
        Classify the regression type based on keywords and issue links.

        Classification logic:
        - Bug fix: Contains fix/bug keywords OR issue link with fix keywords
        - Feature: Feature keywords OR issue link without fix keywords
        - Unknown: No clear indicators
        """
        text_lower = text.lower()

        # Check for bug fix keywords
        has_bug_fix_keywords = any(
            kw in text_lower for kw in REGRESSION_KEYWORDS["bug_fix"]
        )

        # Check for feature keywords
        has_feature_keywords = any(
            kw in text_lower for kw in REGRESSION_KEYWORDS["feature"]
        )

        # Determine type based on keyword analysis
        if has_bug_fix_keywords:
            return RegressionType.BUG_FIX
        elif has_feature_keywords:
            # Check if this is actually a bug fix being described with feature terms
            # e.g., "implement fix for bug #123"
            if "fix" in text_lower or "bug" in text_lower:
                return RegressionType.BUG_FIX
            return RegressionType.FEATURE
        elif linked_issues:
            # Has issue link but no clear keywords - default to feature
            # (issue-linked changes are typically feature work unless explicitly marked as fixes)
            return RegressionType.FEATURE

        return RegressionType.UNKNOWN