#!/usr/bin/env python3
"""
Script to compare AI-generated tests against human-generated tests within the same dataset.

This script will:
1. Load the AIDev dataset (including Human PRs from GitHub)
2. Separate AI-generated PRs from human-generated PRs
3. Run the test detection and coverage analyzer components on both
4. Calculate actual metrics
5. Compare metrics between AI and human tests
6. Calculate statistical significance
"""

import os
import sys
from pathlib import Path
import logging
import scipy.stats as stats
import numpy as np

# Add the project root to the path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import AIDevDataLoader
from src.data_loader.schema_definitions import DataLoaderConfig
from src.test_detector.detector import TestDetector
from src.test_classifier.classifier import TestClassifier
from src.coverage_analyzer.analyzer import CoverageAnalyzer
from src.standards_comparator.comparator import StandardsComparator
from src.data_structures.pr_data import AIAgent

def setup_logging():
    """Set up logging for the AI vs Human comparison analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ai_vs_human_comparison.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def extract_metrics_for_prs(prs, test_detector, coverage_analyzer, agent_type_label):
    logger = logging.getLogger(__name__)
    extracted_metrics = {}
    
    for pr in prs:
        # Calculate total production additions
        prod_additions = 0
        for fc in pr.file_changes:
            if fc.file_path and 'test' not in fc.file_path.lower():
                prod_additions += fc.additions
                
        # Detect tests in the PR
        detection_results = test_detector.detect_in_pr(pr)
        
        for detection_result in detection_results:
            if detection_result.is_test:
                fc = next((fc for fc in pr.file_changes if fc.file_path == detection_result.file_path), None)
                if not fc:
                    continue
                    
                test_additions = fc.additions
                test_content = fc.patch if fc.patch else (fc.content if fc.content else "")
                
                if test_additions == 0 and prod_additions == 0:
                    continue
                    
                analysis = coverage_analyzer.analyze(
                    pr_id=pr.pr_id,
                    test_file_path=detection_result.file_path,
                    test_content=test_content,
                    prod_content="", # We typically just have patches
                    test_additions=test_additions,
                    prod_additions=prod_additions
                )
                
                metrics = {
                    'test_to_code_ratio': analysis.metrics.test_to_code_ratio,
                    'assertion_density': analysis.metrics.assertion_density,
                    'edge_case_coverage': analysis.metrics.edge_case_coverage
                }
                
                extracted_metrics[f"{pr.pr_id}_{detection_result.file_path}"] = {
                    'pr_id': pr.pr_id,
                    'file_path': detection_result.file_path,
                    'language': detection_result.language or 'python',
                    'metrics': metrics,
                    'agent_type': agent_type_label
                }
                
    return extracted_metrics


def compare_ai_to_human():
    """Compare AI-generated tests against human-generated tests."""
    logger = logging.getLogger(__name__)
    logger.info("Starting comparison of AI-generated tests vs Human-generated tests...")
    
    # Step 1: Load the dataset
    logger.info("Step 1: Loading AIDev dataset (including Human PRs)...")
    config = DataLoaderConfig(data_directory="./data/raw")
    data_loader = AIDevDataLoader(config)
    pr_objects = data_loader.run()
    logger.info(f"Loaded {len(pr_objects)} PullRequest objects")
    
    # Step 2: Separate AI-generated and human-generated PRs
    ai_prs = [pr for pr in pr_objects if pr.agent not in (AIAgent.UNKNOWN, AIAgent.HUMAN)]
    human_prs = [pr for pr in pr_objects if pr.agent in (AIAgent.UNKNOWN, AIAgent.HUMAN)]

    logger.info(f"Identified {len(ai_prs)} AI-generated PRs")
    logger.info(f"Identified {len(human_prs)} Human-generated PRs")
    
    if len(human_prs) == 0:
        logger.warning("No human PRs found! Please run scripts/fetch_human_prs.py first.")
        # Proceed anyway with empty dicts to avoid crashing, but log the warning
    
    # Step 3: Initialize components
    logger.info("Step 2: Initializing analysis components...")
    test_detector = TestDetector()
    coverage_analyzer = CoverageAnalyzer()
    standards_comparator = StandardsComparator()
    
    # Step 4: Process AI PRs
    logger.info("Step 3: Processing AI-generated PRs...")
    ai_metrics = extract_metrics_for_prs(ai_prs, test_detector, coverage_analyzer, 'AI')
    
    # Step 5: Process Human PRs
    logger.info("Step 4: Processing Human-generated PRs...")
    human_metrics = extract_metrics_for_prs(human_prs, test_detector, coverage_analyzer, 'Human')
    
    # Step 6: Compare AI vs Human metrics and calculate statistical significance
    logger.info("Step 5: Comparing AI vs Human metrics...")
    
    ai_t2c = [m['metrics']['test_to_code_ratio'] for m in ai_metrics.values() if m['metrics']['test_to_code_ratio'] is not None]
    ai_ad = [m['metrics']['assertion_density'] for m in ai_metrics.values() if m['metrics']['assertion_density'] is not None]
    
    hu_t2c = [m['metrics']['test_to_code_ratio'] for m in human_metrics.values() if m['metrics']['test_to_code_ratio'] is not None]
    hu_ad = [m['metrics']['assertion_density'] for m in human_metrics.values() if m['metrics']['assertion_density'] is not None]
    
    print("\n" + "="*60)
    print("AI TESTS VS HUMAN TESTS COMPARISON")
    print("="*60)
    print(f"AI PRs analyzed: {len(ai_prs)}")
    print(f"Human PRs analyzed: {len(human_prs)}")
    print(f"AI test files detected: {len(ai_metrics)}")
    print(f"Human test files detected: {len(human_metrics)}")
    
    if len(hu_t2c) > 0 and len(ai_t2c) > 0:
        # Mann-Whitney U Test for Test-to-Code Ratio
        stat, p_val_t2c = stats.mannwhitneyu(ai_t2c, hu_t2c, alternative='two-sided')
        print(f"\nTest-to-Code Ratio:")
        print(f"  AI Mean: {np.mean(ai_t2c):.3f} | Human Mean: {np.mean(hu_t2c):.3f}")
        print(f"  Mann-Whitney U p-value: {p_val_t2c:.4e} {'(Significant)' if p_val_t2c < 0.05 else '(Not Significant)'}")
        
        # Mann-Whitney U Test for Assertion Density
        stat, p_val_ad = stats.mannwhitneyu(ai_ad, hu_ad, alternative='two-sided')
        print(f"\nAssertion Density:")
        print(f"  AI Mean: {np.mean(ai_ad):.3f} | Human Mean: {np.mean(hu_ad):.3f}")
        print(f"  Mann-Whitney U p-value: {p_val_ad:.4e} {'(Significant)' if p_val_ad < 0.05 else '(Not Significant)'}")
    else:
        print("\nNot enough data to calculate statistical significance.")
    
    print("="*60)
    
    return True


def main():
    """Main function to run the AI vs Human comparison analysis."""
    print("Comparing AI-generated tests against human-generated tests...\n")
    
    # Set up logging
    setup_logging()
    
    try:
        # Run the comparison analysis
        compare_ai_to_human()
        return 0
        
    except Exception as e:
        print(f"\n✗ Error running AI vs Human comparison: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())