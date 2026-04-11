"""Constants for the test_detector package."""

import re

# Threshold for a file to be considered a test
CONFIDENCE_THRESHOLD: float = 0.5

# Detection method enum
class DetectionMethod:
    """Enumeration of SCOPED test detection methods."""
    FILENAME_PATTERN = "FILENAME_PATTERN"
    DIRECTORY_PATTERN = "DIRECTORY_PATTERN"
    CONTENT_PATTERN = "CONTENT_PATTERN"
    FRAMEWORK_SIGNATURE = "FRAMEWORK_SIGNATURE"

# Language-specific patterns for Python and Java ONLY
LANGUAGE_CONFIGS = {
    "python": {
        "filename_patterns": [re.compile(p) for p in [r"test_.*\.py$", r".*_test\.py$"]],
        "directory_patterns": [re.compile(p) for p in [r"/tests?/", r"/__tests__/"]],
        "content_patterns": {
            DetectionMethod.CONTENT_PATTERN: [re.compile(p) for p in [r"def test_", r"class Test[A-Z]\w*"]],
            DetectionMethod.FRAMEWORK_SIGNATURE: [re.compile(p) for p in [r"import pytest", r"import unittest", r"from unittest"]]
        },
        "frameworks": {
            "pytest": [re.compile(r"import pytest")],
            "unittest": [re.compile(r"import unittest"), re.compile(r"from unittest")]
        }
    },
    "java": {
        "filename_patterns": [re.compile(p) for p in [r".*Test\.java$", r".*Tests\.java$"]],
        "directory_patterns": [re.compile(p) for p in [r"/test/", r"/src/test/java"]],
        "content_patterns": {
            DetectionMethod.CONTENT_PATTERN: [re.compile(p) for p in [r"@Test"]],
             DetectionMethod.FRAMEWORK_SIGNATURE: [re.compile(p) for p in [r"import org\.junit", r"import org\.testng"]]
        },
        "frameworks": {
            "junit": [re.compile(r"import org\.junit")],
            "testng": [re.compile(r"import org\.testng")]
        }
    }
}

# Simplified weights for each detection method
METHOD_WEIGHTS = {
    DetectionMethod.FILENAME_PATTERN: 0.5,
    DetectionMethod.DIRECTORY_PATTERN: 0.4,
    DetectionMethod.CONTENT_PATTERN: 0.3,
    DetectionMethod.FRAMEWORK_SIGNATURE: 0.3  # Treated as strong content evidence
}