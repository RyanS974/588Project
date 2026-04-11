"""Main test file detection logic."""

import logging
from typing import List, Optional
from .constants import LANGUAGE_CONFIGS, CONFIDENCE_THRESHOLD, DetectionMethod
from .pattern_matcher import PatternMatcher
from .confidence_scorer import ConfidenceScorer
from src.data_structures.pr_data import PullRequest, FileChange
from src.data_structures.test_detection import TestDetectionResult


class TestDetector:
    """Orchestrates test file detection using simplified, focused strategies."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pattern_matcher = PatternMatcher(LANGUAGE_CONFIGS)
        self.confidence_scorer = ConfidenceScorer()

    def detect_in_pr(self, pr: PullRequest) -> List[TestDetectionResult]:
        """
        Detects test files within a single PullRequest object.

        Args:
            pr: The PullRequest object from the data_loader.

        Returns:
            A list of TestDetectionResult objects for each file in the PR.
        """
        results = []
        for file_change in pr.file_changes:
            # Skip unsupported languages or files without language
            if not file_change.language or file_change.language.lower() not in ['python', 'java']:
                continue

            result = self._detect_single_file(file_change)
            results.append(result)

        return results

    def _detect_single_file(self, file: FileChange) -> TestDetectionResult:
        """Applies detection logic to a single file."""
        evidence = []
        language = file.language.lower()

        # 1. Filename pattern check
        evidence.extend(self.pattern_matcher.check_filename(file.file_path, language))

        # 2. Directory pattern check
        evidence.extend(self.pattern_matcher.check_directory(file.file_path, language))

        # 3. Content-based checks (if content is available)
        # First try file.content, then fall back to extracting from patch
        content = file.content
        if not content and file.patch:
            from src.utils.patch_parser import extract_added_lines
            content = extract_added_lines(file.patch)
            self.logger.debug(f"Extracted content from patch for {file.file_path}")

        if content:
            lang_config = LANGUAGE_CONFIGS.get(language, {})
            # Check for general content patterns (e.g., 'def test_')
            for pattern in lang_config.get("content_patterns", {}).get(DetectionMethod.CONTENT_PATTERN, []):
                if pattern.search(content):
                    evidence.append(DetectionMethod.CONTENT_PATTERN)
            # Check for framework signatures (e.g., 'import pytest')
            for pattern in lang_config.get("content_patterns", {}).get(DetectionMethod.FRAMEWORK_SIGNATURE, []):
                 if pattern.search(content):
                    evidence.append(DetectionMethod.FRAMEWORK_SIGNATURE)

        # 4. Score confidence and make decision
        unique_evidence = sorted(list(set(evidence)), key=lambda x: x)
        confidence = self.confidence_scorer.calculate(unique_evidence)
        is_test = confidence >= CONFIDENCE_THRESHOLD

        # 5. Identify framework (simplified)
        framework = self._identify_framework(content, language) if is_test and content else None

        # Store the extracted content (from patch if available) for downstream analysis
        # This ensures test_classifier and regression_analyzer have access to the code
        return TestDetectionResult(
            file_path=file.file_path,
            is_test=is_test,
            confidence=confidence,
            detection_methods=unique_evidence,
            language=file.language,
            framework=framework,
            content=content  # Use extracted content from patch if available
        )

    def _identify_framework(self, content: str, language: str) -> Optional[str]:
        """A simple heuristic to name the testing framework."""
        lang_config = LANGUAGE_CONFIGS.get(language, {})
        for framework, patterns in lang_config.get("frameworks", {}).items():
            for pattern in patterns:
                if pattern.search(content):
                    return framework
        return None