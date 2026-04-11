"""Handles pattern matching for filenames and directories."""

from typing import List
from .constants import LANGUAGE_CONFIGS, DetectionMethod


class PatternMatcher:
    """Handles pattern matching for filenames and directories."""

    def __init__(self, lang_configs: dict = LANGUAGE_CONFIGS):
        self.configs = lang_configs

    def check_filename(self, file_path: str, language: str) -> List[str]:
        """Checks filename against language-specific patterns."""
        patterns = self.configs.get(language, {}).get("filename_patterns", [])
        for pattern in patterns:
            if pattern.search(file_path):
                return [DetectionMethod.FILENAME_PATTERN]
        return []

    def check_directory(self, file_path: str, language: str) -> List[str]:
        """Checks directory path against language-specific patterns."""
        patterns = self.configs.get(language, {}).get("directory_patterns", [])
        for pattern in patterns:
            if pattern.search(file_path):
                return [DetectionMethod.DIRECTORY_PATTERN]
        return []