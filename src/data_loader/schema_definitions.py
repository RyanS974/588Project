"""
Module for defining data schemas and configuration for the AIDev dataset.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class AIDevTable(Enum):
    """Enumeration of essential AIDev dataset tables."""
    PULL_REQUEST = "pull_request"
    PR_COMMIT_DETAILS = "pr_commit_details"
    REPOSITORY = "repository"


@dataclass
class TableSchema:
    """Simplified schema definition for a dataset table."""
    table_name: AIDevTable
    required_columns: List[str]
    column_types: Dict[str, type]
    primary_key: str


class AIDevSchema:
    """Scoped schema for the AIDev dataset."""
    SCHEMAS = {
        AIDevTable.PULL_REQUEST: TableSchema(
            table_name=AIDevTable.PULL_REQUEST,
            required_columns=["pr_id", "repository_id", "agent"],
            column_types={"pr_id": str, "repository_id": str, "agent": str},
            primary_key="pr_id"
        ),
        AIDevTable.PR_COMMIT_DETAILS: TableSchema(
            table_name=AIDevTable.PR_COMMIT_DETAILS,
            required_columns=["sha", "pr_id", "file_path"],
            column_types={"sha": str, "pr_id": str, "file_path": str},
            primary_key="sha"
        ),
        AIDevTable.REPOSITORY: TableSchema(
            table_name=AIDevTable.REPOSITORY,
            required_columns=["repository_id", "language", "stars"],
            column_types={"repository_id": str, "language": str, "stars": int},
            primary_key="repository_id"
        )
    }

    @classmethod
    def get_schema(cls, table_name: AIDevTable) -> TableSchema:
        return cls.SCHEMAS[table_name]


@dataclass
class DataLoaderConfig:
    """Simplified configuration for data loading operations."""
    data_directory: str = "./data/raw"
    processed_directory: str = "./data/processed"
    encoding: str = "utf-8"

    # Core filters to scope the analysis
    languages: List[str] = field(default_factory=lambda: ["python", "java"])
    # agents can be None to include all (AI + Human/Unknown)
    agents: Optional[List[str]] = None