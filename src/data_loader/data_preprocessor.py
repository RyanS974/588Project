"""
Module for preprocessing and cleaning the AIDev dataset with a simplified rule set.
"""

import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schema_definitions import AIDevTable, DataLoaderConfig

from .schema_definitions import AIDevTable


class AIDevDataPreprocessor:
    """Preprocesses and cleans the AIDev dataset with a simplified rule set."""

    def __init__(self, config: 'DataLoaderConfig'):
        self.config = config

    def preprocess_table(self, df: pd.DataFrame, table_name: 'AIDevTable') -> pd.DataFrame:
        """Applies a scoped set of preprocessing steps to a DataFrame."""
        processed_df = df.copy()

        if table_name == AIDevTable.PULL_REQUEST:
            processed_df = self._filter_by_agent(processed_df)
            # Note: 'additions' and 'deletions' columns belong to pr_commit_details table, not pull_request table
            # PR size calculation will be done later during data formatting after merging with commit details

        if table_name == AIDevTable.PR_COMMIT_DETAILS:
            processed_df['language'] = processed_df.apply(
                lambda row: self._infer_language_from_filename(row['file_path']) if pd.isna(row.get('language')) else row.get('language'), axis=1
            )
            processed_df['file_extension'] = processed_df['file_path'].str.extract(r'(\.[^.]+)$', expand=False).fillna('')
            processed_df['filename'] = processed_df['file_path'].str.split('/').str[-1]

        if table_name == AIDevTable.REPOSITORY:
            processed_df = self._filter_by_language(processed_df)
            # Only add description column if it exists
            if 'description' in processed_df.columns:
                processed_df['description'] = processed_df['description'].fillna('')

        return processed_df.reset_index(drop=True)

    def _filter_by_language(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.config.languages and 'language' in df.columns:
            # Case-insensitive filter to handle 'Python' vs 'python'
            config_langs_lower = [lang.lower() for lang in self.config.languages]
            return df[df['language'].str.lower().isin(config_langs_lower)]
        return df

    def _filter_by_agent(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.config.agents and 'agent' in df.columns:
            return df[df['agent'].isin(self.config.agents)]
        return df

    def _infer_language_from_filename(self, filepath: str) -> str:
        if not isinstance(filepath, str): 
            return ''
        if filepath.endswith('.py'): 
            return 'python'
        if filepath.endswith('.java'): 
            return 'java'
        return ''