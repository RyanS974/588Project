"""Constants for the regression_analyzer package."""

import re

# Threshold for confidence to identify a test as a regression test
IDENTIFICATION_CONFIDENCE_THRESHOLD: float = 0.5

# Keywords for identifying and classifying regression tests
# These will be checked in commit messages, PR descriptions, and linked issue data
REGRESSION_KEYWORDS = {
    "bug_fix": [
        "fix", "bug", "defect", "issue", "resolve", "correct", "patch", "repair", "tweak",
        "hotfix", "fixes", "fixed", "fixing", "bugfix"
    ],
    "feature": [
        # Feature additions
        "feature", "implement", "add", "enhance", "refactor", "improve", "modify", "extend",
        "new", "introduce", "support", "enable", "update", "upgrade",
        # Issue-linked (when not bug fix)
        # (detected via issue link patterns without fix keywords)
    ]
}

# Simple patterns to link text to issues
ISSUE_LINK_PATTERNS = [
    re.compile(r"#(\d+)", re.IGNORECASE),  # GitHub #123
    re.compile(r"([A-Z]+-\d+)", re.IGNORECASE),  # JIRA ABC-123
    re.compile(r"closes?\s+#?(\d+)", re.IGNORECASE),  # "closes #123"
    re.compile(r"resolves?\s+#?(\d+)", re.IGNORECASE),  # "resolves #123"
    re.compile(r"fixes?\s+#?(\d+)", re.IGNORECASE),  # "fixes #123"
    re.compile(r"github\.com/[^/]+/[^/]+/issues/(\d+)", re.IGNORECASE),  # GitHub issue URLs
]

# Weights for identification confidence
IDENTIFICATION_METHOD_WEIGHTS = {
    "linked_bug_issue": 0.8,  # Strongest signal
    "commit_message_keywords": 0.5,
}

# Simplified quality assessment
MINIMAL_TEST_LINE_COUNT = 75

class RegressionType:
    """Types of regression a test might address."""
    BUG_FIX = "bug_fix"
    FEATURE = "feature"
    UNKNOWN = "unknown"