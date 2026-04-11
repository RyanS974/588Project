"""
Module for performing basic validation on loaded DataFrames.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    from .schema_definitions import AIDevTable

from .schema_definitions import AIDevSchema


class AIDevDataValidator:
    """Performs basic validation on loaded DataFrames."""

    def validate_table(self, df: 'pd.DataFrame', table_name: 'AIDevTable') -> bool:
        """
        Validates a table against its basic schema.
        Checks for required columns and non-null primary keys.
        """
        schema = AIDevSchema.get_schema(table_name)

        # 1. Check for required columns
        missing_cols = [col for col in schema.required_columns if col not in df.columns]
        if missing_cols:
            logging.error(f"Table '{table_name.value}' is missing required columns: {missing_cols}")
            return False

        # 2. Check for nulls in primary key column
        pk_nulls = df[schema.primary_key].isnull().sum()
        if pk_nulls > 0:
            logging.warning(f"Table '{table_name.value}' has {pk_nulls} nulls in primary key column '{schema.primary_key}'.")
            # This is a warning, not a failure, but should be noted.

        logging.info(f"Basic validation passed for table '{table_name.value}'.")
        return True