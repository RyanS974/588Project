#!/usr/bin/env python3
"""
Script to compare AI-generated tests against industry standards using the Standards Comparator Component.

This script will:
1. Load the AIDev dataset
2. Run the test detection and classification components
3. Generate mock coverage metrics for demonstration purposes
4. Compare these metrics against industry standards
5. Generate a summary of how AI-generated tests perform against standards
"""

import os
import sys
from pathlib import Path
import logging
import random

# Add the project root to the path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import AIDevDataLoader
from src.data_loader.schema_definitions import DataLoaderConfig
from src.test_detector.detector import TestDetector
from src.test_classifier.classifier import TestClassifier
from src.standards_comparator.comparator import StandardsComparator


def setup_logging():
    """Set up logging for the comparison analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - '
               '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        handlers=[
            logging.FileHandler('standards_comparison.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def generate_mock_metrics(test_file_path, language):
    """Generate mock coverage metrics for demonstration purposes."""
    # Generate realistic but random metrics for demo
    metrics = {
        'test_to_code_ratio': round(random.uniform(0.1, 2.0), 2),  # 0.1 to 2.0 ratio
        'assertion_density': round(random.uniform(0.01, 0.5), 3),  # 1% to 50% assertion density
        'edge_case_coverage': round(random.uniform(0.0, 1.0), 2)   # 0% to 100% edge case coverage
    }
    return metrics


def compare_ai_to_standards():
    """Compare AI-generated tests against industry standards."""
    logger = logging.getLogger(__name__)
    logger.info("Starting comparison of AI-generated tests against industry standards...")
    
    # Step 1: Load the dataset
    logger.info("Step 1: Loading AIDev dataset...")
    config = DataLoaderConfig(data_directory="./data/raw")
    data_loader = AIDevDataLoader(config)
    pr_objects = data_loader.run()
    logger.info(f"Loaded {len(pr_objects)} PullRequest objects")
    
    # Step 2: Filter to only AI-generated PRs (exclude UNKNOWN)
    from src.data_structures.pr_data import AIAgent
    ai_prs = [pr for pr in pr_objects if pr.agent != AIAgent.UNKNOWN]
    logger.info(f"Identified {len(ai_prs)} AI-generated PRs")
    
    # Step 3: Initialize components
    logger.info("Step 2: Initializing analysis components...")
    test_detector = TestDetector()
    test_classifier = TestClassifier()
    standards_comparator = StandardsComparator()
    
    # Step 4: Run test detection and classification on AI PRs
    logger.info("Step 3: Running test detection and classification on AI PRs...")
    all_comparison_results = []
    
    for pr in ai_prs:
        logger.info(f"Processing AI PR: {pr.pr_id} by {pr.agent.name}")
        
        # Detect tests in the PR
        detection_results = test_detector.detect_in_pr(pr)
        
        # For each detected test file, generate mock metrics and compare to standards
        for detection_result in detection_results:
            if detection_result.is_test:
                # Generate mock metrics for this test file
                mock_metrics = generate_mock_metrics(detection_result.file_path, detection_result.language)
                
                # Compare against industry standards
                comparison_results = standards_comparator.compare_to_industry_standards(
                    pr_id=pr.pr_id,
                    test_file_path=detection_result.file_path,
                    language=detection_result.language or 'python',  # Default to python if not specified
                    actual_metrics=mock_metrics
                )
                
                all_comparison_results.extend(comparison_results)
                
                # Log individual results
                for result in comparison_results:
                    status = "✓ Meets" if result.meets_standard else "✗ Below"
                    grade = result.qualitative_grade or "N/A"
                    logger.info(f"  {status} Standard: {result.metric_name} "
                               f"(Actual: {result.actual_value:.2f}, "
                               f"Required: {result.standard_threshold:.2f}, "
                               f"Grade: {grade})")
    
    # Step 5: Generate summary statistics
    logger.info("Step 4: Generating summary statistics...")
    
    total_comparisons = len(all_comparison_results)
    if total_comparisons == 0:
        logger.warning("No test files were detected in AI-generated PRs to compare against standards.")
        return []
    
    # Count how many comparisons met the standards
    met_standards_count = sum(1 for r in all_comparison_results if r.meets_standard)
    below_standards_count = total_comparisons - met_standards_count
    
    # Group by metric type
    metric_stats = {}
    for result in all_comparison_results:
        metric_name = result.metric_name
        if metric_name not in metric_stats:
            metric_stats[metric_name] = {'met': 0, 'below': 0, 'total': 0, 'avg_gap': 0}
        
        stats = metric_stats[metric_name]
        stats['total'] += 1
        if result.meets_standard:
            stats['met'] += 1
        else:
            stats['below'] += 1
            stats['avg_gap'] += result.gap
    
    # Calculate average gaps for metrics that didn't meet standards
    for metric_name, stats in metric_stats.items():
        if stats['below'] > 0:
            stats['avg_gap'] = stats['avg_gap'] / stats['below']
        else:
            stats['avg_gap'] = 0

    # Calculate qualitative grade distribution
    grade_distribution = {"Poor": 0, "Fair": 0, "Good": 0, "Excellent": 0, "N/A": 0}
    for result in all_comparison_results:
        grade = result.qualitative_grade or "N/A"
        if grade in grade_distribution:
            grade_distribution[grade] += 1

    # Print summary
    print("\n" + "="*60)
    print("AI TESTS VS INDUSTRY STANDARDS COMPARISON")
    print("="*60)
    print(f"AI PRs analyzed: {len(ai_prs)}")
    print(f"Test files compared: {total_comparisons}")
    print(f"Total metric evaluations: {total_comparisons}")
    print(f"Met standards: {met_standards_count}")
    print(f"Below standards: {below_standards_count}")
    print(f"Success rate: {met_standards_count/total_comparisons*100:.1f}%")

    print(f"\nQualitative Grade Distribution:")
    for grade, count in grade_distribution.items():
        pct = count / total_comparisons * 100 if total_comparisons > 0 else 0
        print(f"  {grade}: {count} ({pct:.1f}%)")
    
    print(f"\nDetailed by Metric:")
    for metric_name, stats in metric_stats.items():
        success_rate = stats['met'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"  {metric_name}:")
        print(f"    Success rate: {success_rate:.1f}% ({stats['met']}/{stats['total']})")
        print(f"    Average gap for failing tests: {stats['avg_gap']:.3f}")
    
    print("="*60)
    
    return all_comparison_results


def main():
    """Main function to run the comparison analysis."""
    print("Comparing AI-generated tests against industry standards...\n")
    
    # Set up logging
    setup_logging()
    
    try:
        # Run the comparison analysis
        comparison_results = compare_ai_to_standards()
        
        if comparison_results:
            print("\n✓ AI vs Industry Standards comparison completed successfully!")
            print(f"Found {len(comparison_results)} metric evaluations")
        else:
            print("\n⚠ No comparisons were made (possibly no test files detected)")
        
        print("\nNext steps:")
        print("- Compare AI-generated tests against human-generated tests")
        print("- Generate comprehensive reports")
        print("- Create visualizations")
        print("- Collect and validate results")
        print("- Document findings and insights")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error running AI vs Standards comparison: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())