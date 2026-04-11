import csv
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.regression_analyzer.identifier import RegressionIdentifier

def run_predictions():
    csv_file = project_root / "data/processed/regression_validation_sample.csv"
    picks_file = project_root / "data/processed/code_picks.md"
    
    identifier = RegressionIdentifier()
    
    predictions = []
    
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pr_id = row['PR_ID']
            description = row['Description'] if row['Description'] != "No description" else ""
            commit_messages = row['Commit_Messages'].split(" | ")
            
            # Use identifier logic
            is_regression, confidence, reg_type = identifier.identify(
                commit_messages=commit_messages,
                pr_description=description,
                test_file_path="",
                test_content=""
            )
            
            predictions.append({
                'pr_id': pr_id,
                'is_regression': 1 if is_regression else 0,
                'confidence': confidence,
                'type': reg_type
            })
            
    # Write to code_picks.md
    with open(picks_file, mode='w', encoding='utf-8') as f:
        f.write("# Regression Test Predictions (Code)\n\n")
        f.write("This document outlines the predictions made by the actual project code for each PR in the validation sample.\n\n")
        f.write("| PR_ID | Prediction | Confidence | Type |\n")
        f.write("|-------|------------|------------|------|\n")
        for p in predictions:
            f.write(f"| {p['pr_id']} | {p['is_regression']} | {p['confidence']:.2f} | {p['type']} |\n")

if __name__ == "__main__":
    run_predictions()
    print("Predictions completed and written to data/processed/code_picks.md")
