"""
Module for formatting raw data into structured PullRequest objects for analysis.
"""

import pandas as pd
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .data_structures.pr_data import PullRequest

from src.data_structures import PullRequest, FileChange, AIAgent, PRStatus


class AIDevDataFormatter:
    """Formats raw data into structured PullRequest objects for analysis."""

    @staticmethod
    def _extract_content_from_patch(patch: str) -> str:
        """
        Extract added lines from a git patch for content analysis.

        Git patch format uses '+' to show added lines.
        We extract lines starting with '+' but exclude '+++' (file headers).

        Args:
            patch: Git patch string

        Returns:
            String containing only the added lines (without the '+' prefix)
        """
        if not patch or not isinstance(patch, str):
            return ""

        added_lines = []
        for line in patch.split('\n'):
            # Skip diff headers (---, +++ lines) and empty context lines
            if line.startswith('+++') or line.startswith('---') or line.startswith('@@') or line == '\\ No newline at end of file':
                continue
            # Extract added lines (start with '+', but not '+++')
            if line.startswith('+') and not line.startswith('+++'):
                # Remove the '+' prefix and add to content
                added_lines.append(line[1:])

        return '\n'.join(added_lines)

    def create_pr_dataset(self,
                         pull_requests: pd.DataFrame,
                         commit_details: pd.DataFrame,
                         repositories: pd.DataFrame) -> List['PullRequest']:
        """Creates a list of PullRequest objects from the processed DataFrames."""
        pr_objects = []

        # Join tables for easier lookup
        pr_with_repo = pd.merge(pull_requests, repositories, on='repository_id', how='left')

        # Group file changes by PR
        commits_by_pr = commit_details.groupby('pr_id').apply(
            lambda x: [
                FileChange(
                    file_path=row['file_path'],
                    additions=row['additions'],
                    deletions=row['deletions'],
                    patch=row.get('patch'),  # Extract patch for content analysis
                    content=self._extract_content_from_patch(row.get('patch')),  # Extract added lines from patch
                    language=row.get('language')  # Include language for test detection
                ) for row in x.to_dict('records')
            ]
        ).to_dict()

        # Group commit messages by PR for regression analysis
        messages_by_pr = commit_details.groupby('pr_id')['message'].apply(list).to_dict()

        for _, pr_row in pr_with_repo.iterrows():
            pr_id = pr_row['pr_id']
            file_changes = commits_by_pr.get(pr_id, [])

            # Map DataFrame row to PullRequest dataclass
            # Use 'description' field from the original pull_requests table
            description_val = pr_row.get('description_x', pr_row.get('description', 'No description'))
            
            # Handle case-insensitive matching for enums
            agent_value = pr_row['agent'].lower() if isinstance(pr_row['agent'], str) else pr_row['agent']
            status_value = pr_row['status'].lower() if isinstance(pr_row['status'], str) else pr_row['status']
            
            # Get the correct enum value, default to UNKNOWN/CLOSED if not found
            agent_enum = AIAgent.UNKNOWN
            for agent in AIAgent:
                if agent.value.lower() == agent_value.lower():
                    agent_enum = agent
                    break
            
            status_enum = PRStatus.CLOSED
            for status in PRStatus:
                if status.value.lower() == status_value.lower():
                    status_enum = status
                    break
            
            pr_object = PullRequest(
                pr_id=pr_id,
                repository_id=pr_row['repository_id'],
                agent=agent_enum,
                status=status_enum,
                created_at=pd.to_datetime(pr_row['created_at']),
                title=pr_row['title'],
                description=description_val,
                file_changes=file_changes,
                language=pr_row.get('language', 'unknown'),
                stars=int(pr_row.get('stars', 0)),
                commit_messages=messages_by_pr.get(pr_id, [])
            )
            pr_objects.append(pr_object)

        return pr_objects