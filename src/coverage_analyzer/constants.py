"""Constants for the coverage_analyzer package."""

import re
from enum import Enum


class CoverageMetricType(Enum):
    """Scoped types of coverage proxy metrics."""
    TEST_TO_CODE_RATIO = "test_to_code_ratio"
    ASSERTION_DENSITY = "assertion_density"
    EDGE_CASE_COVERAGE = "edge_case_coverage"


class EdgeCaseType(Enum):
    """Scoped types of critical edge cases."""
    BOUNDARY_VALUE = "boundary_value"
    NULL_HANDLING = "null_handling"
    ERROR_CONDITION = "error_condition"


# Weights for calculating the final adequacy_score
METRIC_WEIGHTS = {
    CoverageMetricType.TEST_TO_CODE_RATIO: 0.3,
    CoverageMetricType.ASSERTION_DENSITY: 0.3,
    CoverageMetricType.EDGE_CASE_COVERAGE: 0.4,
}

# Simplified patterns for detecting edge cases in source code and tests
EDGE_CASE_PATTERNS = {
    EdgeCaseType.BOUNDARY_VALUE: {
        "code": [re.compile(p) for p in [r"[><=]=?", r"range\("]],
        "test": [re.compile(p) for p in [r"test.*boundary", r"test.*limit", r"\bmax\b", r"\bmin\b", r"\bzero\b"]],
    },
    EdgeCaseType.NULL_HANDLING: {
        "code": [re.compile(p) for p in [r"==\s*None", r"is\s+None", r"==\s*null", r"is\s+null"]],
        "test": [re.compile(p) for p in [r"test.*null", r"assertIsNone", r"assertNotNull", r"assertNull", r"assert_not_none"]],
    },
    EdgeCaseType.ERROR_CONDITION: {
        "code": [re.compile(p) for p in [r"raise", r"throw", r"Exception", r"Error"]],
        "test": [re.compile(p) for p in [r"assertRaises", r"toThrow", r"test.*exception", r"test.*error", r"try.*catch"]],
    },
}

# Basic patterns for metric calculation
ASSERT_PATTERNS = [re.compile(r"assert", re.IGNORECASE)]