"""
Module for loading raw data from CSV files into pandas DataFrames.
Supports loading from local CSV files or from Hugging Face as fallback.
"""

import pandas as pd
from pathlib import Path
import logging
from .schema_definitions import AIDevTable, AIDevSchema, DataLoaderConfig
from .exceptions import DataLoadingError


class AIDevCSVLoader:
    """Core CSV loader for the AIDev dataset with Hugging Face fallback."""

    # Hugging Face dataset mapping
    HF_DATASET = "hao-li/AIDev"
    HF_TABLE_MAPPING = {
        AIDevTable.PULL_REQUEST: "pull_request",
        AIDevTable.PR_COMMIT_DETAILS: "pr_commit_details",
        AIDevTable.REPOSITORY: "repository",
    }

    def __init__(self, config: DataLoaderConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_path = Path(config.data_directory)

    def load_table(self, table_name: AIDevTable) -> pd.DataFrame:
        """Loads a specific table from a CSV file or Hugging Face."""
        csv_path = self.data_path / f"{table_name.value}.csv"

        # Try local CSV first
        if csv_path.exists():
            self.logger.info(f"Loading table from CSV: {csv_path}")
            try:
                df = pd.read_csv(csv_path, encoding=self.config.encoding, low_memory=False)
                self.logger.info(f"Successfully loaded {table_name.value} from CSV ({len(df)} rows)")
                return df
            except Exception as e:
                self.logger.warning(f"Failed to load CSV, trying Hugging Face: {e}")

        # Fallback to Hugging Face
        return self._load_from_hugging_face(table_name)

    def _load_from_hugging_face(self, table_name: AIDevTable) -> pd.DataFrame:
        """Load table from Hugging Face dataset."""
        hf_table = self.HF_TABLE_MAPPING.get(table_name)
        if not hf_table:
            raise DataLoadingError(f"No Hugging Face mapping for {table_name}")

        hf_path = f"hf://datasets/{self.HF_DATASET}/{hf_table}.parquet"
        self.logger.info(f"Loading from Hugging Face: {hf_path}")

        try:
            df = pd.read_parquet(hf_path)
            self.logger.info(f"Successfully loaded {table_name.value} from Hugging Face ({len(df)} rows)")

            # Rename columns to match our expected schema
            # HuggingFace dataset uses different column names
            df = self._rename_columns(df, table_name)

            return df
        except Exception as e:
            self.logger.error(f"Failed to load from Hugging Face: {e}")
            raise DataLoadingError(f"Failed to load {table_name.value} from Hugging Face") from e

    def _rename_columns(self, df: pd.DataFrame, table_name: AIDevTable) -> pd.DataFrame:
        """Rename HuggingFace columns to match our expected schema."""
        # Column mapping based on HuggingFace dataset schema
        column_mappings = {
            AIDevTable.PULL_REQUEST: {
                'id': 'pr_id',
                'repo_id': 'repository_id',
                'state': 'status',
            },
            AIDevTable.PR_COMMIT_DETAILS: {
                'filename': 'file_path',
                'commit_id': 'sha',
            },
            AIDevTable.REPOSITORY: {
                'id': 'repository_id',
            }
        }

        mapping = column_mappings.get(table_name, {})
        if mapping:
            # Only rename columns that exist
            rename_dict = {k: v for k, v in mapping.items() if k in df.columns}
            if rename_dict:
                df = df.rename(columns=rename_dict)
                self.logger.info(f"Renamed columns: {rename_dict}")

        return df