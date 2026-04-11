"""Compares analysis metrics against a predefined, simple set of standards."""

import logging
import yaml
from typing import List, Dict, Optional, Tuple
from .constants import Standard, StandardSet, ComparisonResult


class StandardsComparator:
    """
    Compares analysis metrics against a predefined, simple set of standards.
    Also supports comparison between AI-generated PRs and human PRs (scaffolding for future implementation).
    """

    # Thresholds for qualitative grading (percentage above/below standard)
    EXCELLENT_THRESHOLD = 0.20  # 20% above standard
    GOOD_THRESHOLD = 0.10  # 10% above standard
    FAIR_THRESHOLD = 0.0  # Meets standard
    POOR_THRESHOLD = -0.10  # Within 10% below standard
    VERY_POOR_THRESHOLD = -0.20  # Within 20% below standard
    """
    Compares analysis metrics against a predefined, simple set of standards.
    Also supports comparison between AI-generated PRs and human PRs (scaffolding for future implementation).
    """

    def __init__(self, standards_filepath: str = "config/standards_definitions.yaml"):
        self.logger = logging.getLogger(__name__)
        self.standards = self._load_standards(standards_filepath)

    def _load_standards(self, filepath: str) -> Dict[str, StandardSet]:
        """Loads and parses the simple standards definition YAML file."""
        try:
            with open(filepath, 'r') as f:
                raw_standards = yaml.safe_load(f)

            loaded_standards = {}
            for std_set_data in raw_standards:
                # Assuming the YAML structure matches the StandardSet dataclass
                standard_objects = [Standard(**s) for s in std_set_data.get('standards', [])]
                standard_set = StandardSet(
                    id=std_set_data['id'],
                    language=std_set_data['language'],
                    project_type=std_set_data['project_type'],
                    standards=standard_objects
                )
                # Create a key like 'python-application' for easy lookup
                key = f"{standard_set.language}-{standard_set.project_type}"
                loaded_standards[key] = standard_set

            self.logger.info(f"Successfully loaded {len(loaded_standards)} standard sets.")
            return loaded_standards
        except FileNotFoundError:
            self.logger.error(f"Standards definition file not found at {filepath}. Comparator will not function.")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading standards from {filepath}: {e}")
            return {}

    def _get_qualitative_grade(self, actual_value: float, threshold: float) -> str:
        """
        Calculate qualitative grade based on how far the actual value is from the threshold.

        Args:
            actual_value: The measured metric value
            threshold: The standard threshold value

        Returns:
            Qualitative grade: "Excellent", "Good", "Fair", or "Poor"
        """
        # Calculate the gap as a percentage of the threshold
        # This normalizes the grading across different metric scales
        if threshold == 0:
            # Avoid division by zero - use absolute difference for zero thresholds
            gap = actual_value
        else:
            gap = (actual_value - threshold) / abs(threshold)

        if gap >= self.EXCELLENT_THRESHOLD:
            return "Excellent"
        elif gap >= self.GOOD_THRESHOLD:
            return "Good"
        elif gap >= self.FAIR_THRESHOLD:
            return "Fair"
        elif gap >= self.POOR_THRESHOLD:
            return "Fair"
        elif gap >= self.VERY_POOR_THRESHOLD:
            return "Poor"
        else:
            return "Poor"

    def compare_to_industry_standards(self, pr_id: str, test_file_path: str, language: str, actual_metrics: Dict[str, float]) -> List[ComparisonResult]:
        """
        Compares a set of actual metrics against the relevant industry standard set.

        Args:
            pr_id: The ID of the PR being analyzed.
            test_file_path: Path of the test file being analyzed.
            language: The language of the file (e.g., 'python').
            actual_metrics: A dictionary of metric names to their calculated values.

        Returns:
            A list of ComparisonResult objects for each relevant standard.
        """
        results = []

        # Use a simplified project_type. We assume 'application' for all cases.
        project_type = "application"

        # Find the appropriate standard set
        standard_set_key = f"{language.lower()}-{project_type}"
        standard_set = self.standards.get(standard_set_key)

        if not standard_set:
            self.logger.warning(f"No standard set found for key '{standard_set_key}'. Skipping comparison for {test_file_path}.")
            return []

        # Compare each metric defined in the standard set
        for standard in standard_set.standards:
            metric_name = standard.metric_name
            if metric_name in actual_metrics:
                actual_value = actual_metrics[metric_name]
                meets_standard = actual_value >= standard.threshold
                gap = (actual_value - standard.threshold)
                qualitative_grade = self._get_qualitative_grade(actual_value, standard.threshold)

                results.append(ComparisonResult(
                    pr_id=pr_id,
                    test_file_path=test_file_path,
                    metric_name=metric_name,
                    actual_value=actual_value,
                    standard_threshold=standard.threshold,
                    meets_standard=meets_standard,
                    gap=gap,
                    qualitative_grade=qualitative_grade
                ))

        return results

    def compare_ai_to_human_prs(self, ai_pr_id: str, human_pr_id: str, test_file_path: str, 
                                language: str, ai_metrics: Dict[str, float], 
                                human_metrics: Dict[str, float]) -> List[ComparisonResult]:
        """
        Compares AI-generated PR metrics against human PR metrics (scaffolding for future implementation).
        
        This method is designed to compare metrics between AI-generated PRs and human PRs
        from the AIDev dataset, which will be implemented in Phase 3.

        Args:
            ai_pr_id: The ID of the AI-generated PR being analyzed.
            human_pr_id: The ID of the human PR for comparison.
            test_file_path: Path of the test file being analyzed.
            language: The language of the file (e.g., 'python').
            ai_metrics: Metrics from the AI-generated PR.
            human_metrics: Metrics from the human PR for comparison.

        Returns:
            A list of ComparisonResult objects showing how AI metrics compare to human metrics.
        """
        self.logger.info(f"Comparing AI PR {ai_pr_id} to Human PR {human_pr_id} for file {test_file_path}")
        
        results = []
        
        # For each metric in AI metrics, compare against the corresponding human metric
        for metric_name, ai_value in ai_metrics.items():
            if metric_name in human_metrics:
                human_value = human_metrics[metric_name]

                # Calculate how the AI metric compares to the human baseline
                # If ai_value >= human_value, we consider it meets the "human standard"
                meets_standard = ai_value >= human_value
                gap = (ai_value - human_value)
                qualitative_grade = self._get_qualitative_grade(ai_value, human_value)

                results.append(ComparisonResult(
                    pr_id=f"AI-{ai_pr_id}_vs_Human-{human_pr_id}",
                    test_file_path=test_file_path,
                    metric_name=metric_name,
                    actual_value=ai_value,
                    standard_threshold=human_value,  # Using human value as the "standard" to meet
                    meets_standard=meets_standard,
                    gap=gap,
                    qualitative_grade=qualitative_grade
                ))
        
        return results

    def compare(self, pr_id: str, test_file_path: str, language: str, actual_metrics: Dict[str, float]) -> List[ComparisonResult]:
        """
        Compares a set of actual metrics against the relevant industry standard set.
        This is maintained for backward compatibility.

        Args:
            pr_id: The ID of the PR being analyzed.
            test_file_path: Path of the test file being analyzed.
            language: The language of the file (e.g., 'python').
            actual_metrics: A dictionary of metric names to their calculated values.

        Returns:
            A list of ComparisonResult objects for each relevant standard.
        """
        return self.compare_to_industry_standards(pr_id, test_file_path, language, actual_metrics)