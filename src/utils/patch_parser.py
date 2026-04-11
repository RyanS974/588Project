"""Utility for parsing unified diff patches to extract added code content."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_added_lines(patch: str) -> Optional[str]:
    """
    Extract added lines from a unified diff patch.

    Unified diff format example:
    ```
    @@ -0,0 +1,5 @@
    +def test_calculator_add():
    +    result = add(2, 3)
    +    assert result == 5
    ```

    Args:
        patch: The patch string in unified diff format.

    Returns:
        A string containing the added lines (with '+' prefix removed),
        or None if no patch or no added lines found.
    """
    # Handle None, empty string, and NaN values
    if patch is None or (isinstance(patch, float) and patch != patch):  # NaN check
        return None
    if not patch or not isinstance(patch, str):
        return None

    added_lines = []
    for line in patch.split('\n'):
        # Lines starting with '+' but not '+++' (file header) are added lines
        if line.startswith('+') and not line.startswith('+++'):
            # Remove the '+' prefix and add to content
            added_lines.append(line[1:])

    return '\n'.join(added_lines) if added_lines else None


def extract_test_code_from_patch(patch: str, is_test_file: bool = True) -> Optional[str]:
    """
    Extract test code from a patch, with special handling for test files.

    For test files, this extracts added lines which represent new test code.
    For non-test files, returns None as we typically only analyze test code.

    Args:
        patch: The patch string in unified diff format.
        is_test_file: Whether the file is a test file.

    Returns:
        Extracted code content or None.
    """
    if not patch or not is_test_file:
        return None

    content = extract_added_lines(patch)

    if content:
        # Log sample of extracted content for debugging
        sample = content[:100] if len(content) > 100 else content
        logger.debug(f"Extracted {len(content)} chars from patch. Sample: {sample}")

    return content


def count_assertions_in_patch(patch: str, language: str = 'python') -> int:
    """
    Count assertions in the added lines of a patch.

    Args:
        patch: The patch string in unified diff format.
        language: The programming language ('python' or 'java').

    Returns:
        Number of assertions found in added lines.
    """
    content = extract_added_lines(patch)
    if not content:
        return 0

    if language.lower() == 'python':
        # Python assertions: assert, self.assert*, pytest.raises
        patterns = [
            r'\bassert\s+',  # assert statements
            r'\bassertTrue\b', r'\bassertFalse\b',  # unittest
            r'\bassertEqual\b', r'\bassertNotEqual\b',
            r'\bassertIn\b', r'\bassertNotIn\b',
            r'\bassertRaises\b', r'\bpytest\.raises\b',
        ]
    elif language.lower() == 'java':
        # Java assertions: JUnit assertions
        patterns = [
            r'\bassertEquals\b', r'\bassertNotEquals\b',
            r'\bassertTrue\b', r'\bassertFalse\b',
            r'\bassertNull\b', r'\bassertNotNull\b',
            r'\bassertThrows\b', r'\bassertThat\b',
        ]
    else:
        return 0

    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.IGNORECASE))

    return count
