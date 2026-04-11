"""
A simplified, central data manager for storing and accessing analysis data.
It acts as a shared dictionary with basic persistence capabilities.
"""

import pickle
from typing import Any, Dict
import logging


class DataManager:
    """
    A simplified, central data manager for storing and accessing analysis data.
    It acts as a shared dictionary with basic persistence capabilities.
    """

    def __init__(self, config: dict = None):
        """Initializes the DataManager."""
        self.config = config or {}
        self._storage: Dict[str, Any] = {
            'raw_data': None,             # Raw dataset from data_loader
            'pr_data': None,              # List[PullRequest] objects
            'test_files': None,           # List[PRTestDetection]
            'test_classifications': None, # List[PRTestClassification]
            'coverage_metrics': None,     # List[PRCoverageAnalysis]
            'regression_analysis': None,  # List[RegressionAnalysis]
            'standards_comparison': None, # List of comparison results
            'visualization_data': None,   # Dict of data for charts/tables
            'reports': None               # Final generated reports (str or dict)
        }
        self.logger = logging.getLogger(__name__)
        self.logger.info("DataManager initialized in simplified mode.")

    def set_data(self, key: str, data: Any) -> None:
        """
        Stores data in the manager's dictionary under a specific key.
        If the key already exists, it will be overwritten.
        """
        if key not in self._storage:
            self.logger.warning(f"Key '{key}' is not a predefined key in DataManager. Storing anyway.")

        self._storage[key] = data
        self.logger.debug(f"Data for key '{key}' has been set.")

    def get_data(self, key: str) -> Any:
        """
        Retrieves data from the manager's dictionary.

        Raises:
            KeyError: If the data key is not found.
        """
        if key not in self._storage:
            self.logger.error(f"Data key '{key}' not found in DataManager.")
            raise KeyError(f"Data key '{key}' not found")

        data = self._storage.get(key)
        if data is None:
            self.logger.warning(f"Data for key '{key}' was requested but is None.")

        return data

    def save_state(self, filepath: str) -> None:
        """
        Saves the entire current state of the DataManager's storage to a file
        using pickle for simple and direct serialization.
        """
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self._storage, f)
            self.logger.info(f"DataManager state successfully saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save DataManager state to {filepath}: {e}")
            raise

    def load_state(self, filepath: str) -> None:
        """
        Loads the DataManager's storage from a file, overwriting the current state.
        This allows for resuming analysis from a checkpoint.
        """
        try:
            with open(filepath, 'rb') as f:
                self._storage = pickle.load(f)
            self.logger.info(f"DataManager state successfully loaded from {filepath}")
        except FileNotFoundError:
            self.logger.error(f"Failed to load state. File not found: {filepath}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load DataManager state from {filepath}: {e}")
            raise