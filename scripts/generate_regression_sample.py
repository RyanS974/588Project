#!/usr/bin/env python3
"""
Script to generate a random sample of 50 Pull Requests for manual validation
of the regression test detection pipeline.
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
    
    logger.info(f"Loaded {len(prs)} PRs.")
    
    # We want a sample of exactly 50 PRs
    # Seed for reproducibility
    random.seed(42)
    sample_size = min(50, len(prs))
    sampled_prs = random.sample(prs, sample_size)
    
    logger.info(f"Sampled {len(sampled_prs)} PRs. Preparing CSV output...")
    
    # Format the data for CSV
    csv_data = []
    for pr in sampled_prs:
        commits = pr.commit_messages if pr.commit_messages else []
        commits_str = " | ".join(commits)
        
        # Clean up description to avoid messy CSVs
        desc = pr.description if pr.description else ""
        desc = desc.replace("\n", " ").replace("\r", " ").strip()
        
        record = {
            'Ryan_Score': '', # 0 or 1
            'Zach_Score': '', # 0 or 1
            'PR_ID': pr.pr_id,
            'Repository': pr.repository_id,
            'Title': pr.title.replace("\n", " ") if pr.title else "",
            'Description': desc,
            'Commit_Messages': commits_str
        }
        csv_data.append(record)

    output_dir = project_root / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'regression_validation_sample.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Ryan_Score', 'Zach_Score', 'PR_ID', 
            'Repository', 'Title', 'Description', 'Commit_Messages'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
        
    logger.info(f"Successfully generated validation set at {output_file}")
    logger.info("Please review the CSV and fill in the 'Ryan_Score' and 'Zach_Score' columns with 1 (regression test present) or 0 (not present).")

if __name__ == "__main__":
    main()
