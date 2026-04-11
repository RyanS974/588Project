"""
Data structures for representing test detection results.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TestDetectionResult:
    """Results from test file detection."""
    file_path: str
    is_test: bool
    confidence: float  # 0.0 to 1.0
    detection_methods: List[str]  # e.g., ['FILENAME_PATTERN', 'CONTENT_PATTERN']
    language: str
    framework: Optional[str] = None  # e.g., 'pytest', 'junit'
    content: Optional[str] = None  # File content for classification


@dataclass
class PRTestDetection:
    """Test detection results for a complete PR."""
    pr_id: str
    detected_tests: List[TestDetectionResult]