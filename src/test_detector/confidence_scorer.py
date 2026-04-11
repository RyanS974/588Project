"""Calculates a simple, additive confidence score."""

from typing import List
from .constants import METHOD_WEIGHTS, DetectionMethod, CONFIDENCE_THRESHOLD


class ConfidenceScorer:
    """Calculates a simple, additive confidence score."""

    def calculate(self, evidence: List[str]) -> float:
        """
        Calculates confidence by summing weights of unique evidence found.

        Args:
            evidence: A list of unique DetectionMethod enums found.

        Returns:
            A confidence score between 0.0 and 1.0.
        """
        score = 0.0
        for method in evidence:
            score += METHOD_WEIGHTS.get(method, 0.0)

        # Apply a simple bonus multiplier if multiple strong indicators are present
        if DetectionMethod.FILENAME_PATTERN in evidence and DetectionMethod.DIRECTORY_PATTERN in evidence:
            score *= 1.2

        return min(score, 1.0)  # Cap score at 1.0