#!/usr/bin/env python3
"""
Script to generate a random sample of files for manual ground-truth validation.

This script will:
1. Load the AIDev dataset (including Human PRs)
2. Run the TestDetector and TestClassifier
3. Sample 100 detected test files (50 AI, 50 Human)
4. Sample 50 non-test files (rejected by TestDetector)
5. Export to a CSV for manual labeling
"""

import os
import sys
import csv
import random
from pathlib import Path
import logging

# Add the project root to the path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import AIDevDataLoader
from src.data_loader.schema_definitions import DataLoaderConfig
from src.test_detector.detector import TestDetector
from src.test_classifier.classifier import TestClassifier
from src.data_structures.pr_data import AIAgent

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - '
               '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Loading dataset...")
    config = DataLoaderConfig(data_directory="./data/raw")
    data_loader = AIDevDataLoader(config)
    prs = data_loader.run()
    
    logger.info("Initializing components...")
    test_detector = TestDetector()
    test_classifier = TestClassifier()
    
    detected_tests_ai = []
    detected_tests_human = []
    non_tests = []
    
    logger.info("Processing PRs to find tests and non-tests...")
    
    for pr in prs:
        is_human = pr.agent in (AIAgent.UNKNOWN, AIAgent.HUMAN)
        detection_results = test_detector.detect_in_pr(pr)
        
        for detection_result in detection_results:
            fc = next((fc for fc in pr.file_changes if fc.file_path == detection_result.file_path), None)
            content = fc.patch if fc and fc.patch else (fc.content if fc and fc.content else "")
            
            # Simple deduplication based on path + repo
            unique_id = f"{pr.repository_id}:{detection_result.file_path}"
            
            if detection_result.is_test:
                classification = test_classifier.classify_test_file(detection_result, content)
                
                record = {
                    'pr_id': pr.pr_id,
                    'repository': pr.repository_id,
                    'file_path': detection_result.file_path,
                    'agent': 'Human' if is_human else 'AI',
                    'predicted_is_test': 'Yes',
                    'predicted_type': classification.primary_type.name,
                    'predicted_quality': classification.quality_level.name,
                    'actual_is_test': '',  # To be filled manually
                    'actual_type': '',     # To be filled manually
                    'actual_quality': '',  # To be filled manually
                    'notes': ''
                }
                
                if is_human:
                    detected_tests_human.append(record)
                else:
                    detected_tests_ai.append(record)
            else:
                # To prevent storing too many non-tests, we sample occasionally
                if random.random() < 0.1:
                    record = {
                        'pr_id': pr.pr_id,
                        'repository': pr.repository_id,
                        'file_path': detection_result.file_path,
                        'agent': 'Human' if is_human else 'AI',
                        'predicted_is_test': 'No',
                        'predicted_type': 'N/A',
                        'predicted_quality': 'N/A',
                        'actual_is_test': '',
                        'actual_type': '',
                        'actual_quality': '',
                        'notes': ''
                    }
                    non_tests.append(record)

    logger.info(f"Found {len(detected_tests_ai)} AI tests, {len(detected_tests_human)} Human tests, {len(non_tests)} sampled non-tests.")

    # Sample the required amounts
    random.seed(42)
    sample_ai = random.sample(detected_tests_ai, min(50, len(detected_tests_ai)))
    sample_human = random.sample(detected_tests_human, min(50, len(detected_tests_human)))
    sample_non_tests = random.sample(non_tests, min(50, len(non_tests)))
    
    final_sample = sample_ai + sample_human + sample_non_tests
    random.shuffle(final_sample)
    
    output_dir = project_root / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'manual_validation_set.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'pr_id', 'repository', 'file_path', 'agent', 
            'predicted_is_test', 'actual_is_test',
            'predicted_type', 'actual_type',
            'predicted_quality', 'actual_quality',
            'notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_sample)
        
    logger.info(f"Successfully generated validation set at {output_file}")
    logger.info(f"Please review {output_file} and fill in the 'actual_*' columns.")

if __name__ == "__main__":
    main()
