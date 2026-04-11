"""
Main interface for loading the scoped AIDev dataset.

This module contains the AIDevDataLoader class which orchestrates the entire
data loading, validation, preprocessing, and formatting workflow by combining
the functionalities of the other modules.
"""

import logging
from typing import List
from .csv_loader import AIDevCSVLoader
from .data_validator import AIDevDataValidator
from .data_preprocessor import AIDevDataPreprocessor
from .data_formatter import AIDevDataFormatter
from .schema_definitions import AIDevTable, DataLoaderConfig
from src.data_structures import PullRequest


class AIDevDataLoader:
    """Main interface for loading the scoped AIDev dataset."""

    def __init__(self, config: DataLoaderConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.loader = AIDevCSVLoader(config)
        self.validator = AIDevDataValidator()
        self.preprocessor = AIDevDataPreprocessor(config)
        self.formatter = AIDevDataFormatter()

    def run(self) -> List[PullRequest]:
        """
        Executes the full data loading and preparation pipeline.

        Returns:
            A list of fully populated PullRequest objects ready for analysis.
        """
        # 1. Load essential tables
        self.logger.info("Step 1: Loading raw data...")
        raw_prs = self.loader.load_table(AIDevTable.PULL_REQUEST)
        raw_commits = self.loader.load_table(AIDevTable.PR_COMMIT_DETAILS)
        raw_repos = self.loader.load_table(AIDevTable.REPOSITORY)

        # 2. Perform basic validation
        self.logger.info("Step 2: Performing basic validation...")
        self.validator.validate_table(raw_prs, AIDevTable.PULL_REQUEST)
        self.validator.validate_table(raw_commits, AIDevTable.PR_COMMIT_DETAILS)
        self.validator.validate_table(raw_repos, AIDevTable.REPOSITORY)

        # 3. Preprocess and filter tables
        self.logger.info("Step 3: Preprocessing and filtering data...")
        # CRITICAL: Filter repos by language *first* to reduce the dataset size
        processed_repos = self.preprocessor.preprocess_table(raw_repos, AIDevTable.REPOSITORY)

        # Filter PRs and commits to only those in the selected repos
        relevant_pr_ids = raw_prs[raw_prs['repository_id'].isin(processed_repos['repository_id'])]['pr_id']
        processed_prs = self.preprocessor.preprocess_table(raw_prs[raw_prs['pr_id'].isin(relevant_pr_ids)], AIDevTable.PULL_REQUEST)
        processed_commits = self.preprocessor.preprocess_table(raw_commits[raw_commits['pr_id'].isin(relevant_pr_ids)], AIDevTable.PR_COMMIT_DETAILS)

        # 4. Format into final objects
        self.logger.info("Step 4: Formatting data into PullRequest objects...")
        pr_objects = self.formatter.create_pr_dataset(processed_prs, processed_commits, processed_repos)

        # 5. Load human PRs from JSON files
        human_prs = self._load_human_prs()
        if human_prs:
            self.logger.info(f"Adding {len(human_prs)} human PRs to the dataset.")
            pr_objects.extend(human_prs)

        self.logger.info(f"Data loading complete. Generated {len(pr_objects)} PullRequest objects.")
        return pr_objects

    def _load_human_prs(self) -> List[PullRequest]:
        """Loads human PRs fetched via GitHub API."""
        import os
        import json
        from pathlib import Path
        from datetime import datetime
        from src.data_structures import AIAgent, PRStatus, FileChange

        human_prs = []
        human_prs_dir = Path(self.config.data_directory) / "human_prs"
        if not human_prs_dir.exists() or not human_prs_dir.is_dir():
            return human_prs

        self.logger.info(f"Step 5: Loading human PRs from {human_prs_dir}...")
        
        for file_path in human_prs_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    prs_data = json.load(f)
                
                # Repository name is often filename minus .json (e.g. owner_repo)
                repo_id = file_path.stem

                for pr_data in prs_data:
                    file_changes = []
                    for file_item in pr_data.get("files", []):
                        file_path = file_item.get("filename", "")
                        lang = "python" if file_path.endswith(".py") else "java" if file_path.endswith(".java") else "unknown"
                        file_changes.append(FileChange(
                            file_path=file_path,
                            additions=file_item.get("additions", 0),
                            deletions=file_item.get("deletions", 0),
                            patch=file_item.get("patch"),
                            language=lang
                        ))
                    
                    created_at_str = pr_data.get("created_at")
                    try:
                        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ") if created_at_str else datetime.now()
                    except ValueError:
                        created_at = datetime.now()

                    pr = PullRequest(
                        pr_id=str(pr_data.get("id", "")),
                        repository_id=repo_id,
                        agent=AIAgent.HUMAN,
                        status=PRStatus.MERGED,
                        created_at=created_at,
                        title=pr_data.get("title", ""),
                        description=pr_data.get("body"),
                        file_changes=file_changes,
                        language="unknown", # Will be inferred later or set based on the files
                        stars=0, # Not strictly needed for human comparison but should match schema
                        commit_messages=[] 
                    )
                    human_prs.append(pr)
            except Exception as e:
                self.logger.error(f"Failed to load human PRs from {file_path}: {e}")

        return human_prs

__all__ = ['AIDevDataLoader', 'DataLoaderConfig']