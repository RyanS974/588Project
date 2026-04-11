"""
Data structures for representing pull request data and related entities.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class AIAgent(Enum):
    """Enumeration of AI agents. 'UNKNOWN' is used for the human comparison group."""
    # AIDev dataset agent names (exact match)
    OPENAI_CODEX = "OpenAI_Codex"
    COPILOT = "Copilot"
    DEVIN = "Devin"
    CURSOR = "Cursor"
    CLAUDE_CODE = "Claude_Code"
    # Legacy names for backward compatibility
    CODEX = "codex"
    CLAUDE = "claude"
    # Human/Unknown
    HUMAN = "Human"
    UNKNOWN = "unknown"


class PRStatus(Enum):
    """Pull Request status."""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    REJECTED = "rejected"


@dataclass
class FileChange:
    """Represents a single file change in a PR."""
    file_path: str
    additions: int
    deletions: int
    patch: Optional[str] = None
    content: Optional[str] = None
    file_type: Optional[str] = None  # 'production', 'test', 'other'
    language: Optional[str] = None  # 'Python', 'Java'


@dataclass
class PullRequest:
    """Complete pull request data structure."""
    pr_id: str
    repository_id: str
    agent: AIAgent
    status: PRStatus
    created_at: datetime
    title: str
    description: Optional[str]
    file_changes: List[FileChange]
    language: str  # Primary language of the PR, limited to Python/Java
    stars: int     # Repository star count, used for simple heuristics
    commit_messages: List[str] = None  # Commit messages for regression analysis