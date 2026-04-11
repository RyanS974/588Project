#!/usr/bin/env python3
"""
Script to calculate confusion matrix metrics from the manually labeled ground-truth dataset.

This script reads `data/processed/manual_validation_set.csv` and outputs:
1. Test Detection Confusion Matrix
2. Quality Classification Confusion Matrix
3. Precision, Recall, and F1-scores.
"""

import os
import sys
import csv
from pathlib import Path

def calculate_metrics(tp, fp, tn, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    return precision, recall, f1, accuracy

def main():
    project_root = Path(__file__).parent.parent
    csv_file = project_root / 'data' / 'processed' / 'manual_validation_set.csv'
    
    if not csv_file.exists():
        print(f"Error: Could not find {csv_file}")
        print("Please run scripts/generate_ground_truth_sample.py first and manually label the results.")
        sys.exit(1)
        
    print(f"Loading manual validation data from {csv_file}...\n")
    
    # 1. Test Detection metrics
    det_tp, det_fp, det_tn, det_fn = 0, 0, 0, 0
    
    # 2. Quality Classification metrics (GOOD vs. POOR/FAIR) - Treating GOOD as positive class
    qual_tp, qual_fp, qual_tn, qual_fn = 0, 0, 0, 0
    
    # 3. Type Classification (UNIT vs. INTEGRATION) - Treating UNIT as positive class
    type_tp, type_fp, type_tn, type_fn = 0, 0, 0, 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # If the user hasn't filled in the 'actual' columns, we skip or treat as missing
            if not row.get('actual_is_test'):
                continue
                
            pred_is_test = row['predicted_is_test'].strip().lower() == 'yes'
            actual_is_test = row['actual_is_test'].strip().lower() == 'yes'
            
            # Test Detection CM
            if pred_is_test and actual_is_test:
                det_tp += 1
            elif pred_is_test and not actual_is_test:
                det_fp += 1
            elif not pred_is_test and not actual_is_test:
                det_tn += 1
            elif not pred_is_test and actual_is_test:
                det_fn += 1
                
            # If it is actually a test, check classification and quality
            if actual_is_test and pred_is_test:
                # Quality: Good (Positive) vs others (Negative)
                pred_good = row['predicted_quality'].strip().upper() == 'GOOD'
                actual_good = row['actual_quality'].strip().upper() == 'GOOD'
                
                if pred_good and actual_good: qual_tp += 1
                elif pred_good and not actual_good: qual_fp += 1
                elif not pred_good and not actual_good: qual_tn += 1
                elif not pred_good and actual_good: qual_fn += 1
                
                # Type: Unit (Positive) vs Integration/other (Negative)
                pred_unit = row['predicted_type'].strip().upper() == 'UNIT'
                actual_unit = row['actual_type'].strip().upper() == 'UNIT'
                
                if pred_unit and actual_unit: type_tp += 1
                elif pred_unit and not actual_unit: type_fp += 1
                elif not pred_unit and not actual_unit: type_tn += 1
                elif not pred_unit and actual_unit: type_fn += 1

    total_records = det_tp + det_fp + det_tn + det_fn
    if total_records == 0:
        print("No labeled data found in the CSV. Please fill in the 'actual_*' columns.")
        sys.exit(1)
        
    print("=" * 60)
    print("CONFUSION MATRIX ANALYSIS")
    print("=" * 60)
    print(f"Total labeled records processed: {total_records}")
    
    # Print Test Detection
    p, r, f1, acc = calculate_metrics(det_tp, det_fp, det_tn, det_fn)
    print("\n--- 1. Test Detection (Is it a test file?) ---")
    print(f"True Positives (TP):  {det_tp}")
    print(f"False Positives (FP): {det_fp}")
    print(f"True Negatives (TN):  {det_tn}")
    print(f"False Negatives (FN): {det_fn}")
    print(f"Precision: {p:.3f} | Recall: {r:.3f} | F1-Score: {f1:.3f} | Accuracy: {acc:.3f}")
    
    # Print Quality Classification
    total_qual = qual_tp + qual_fp + qual_tn + qual_fn
    if total_qual > 0:
        p, r, f1, acc = calculate_metrics(qual_tp, qual_fp, qual_tn, qual_fn)
        print("\n--- 2. Quality Classification (GOOD vs POOR/FAIR) ---")
        print(f"True Positives (TP):  {qual_tp}")
        print(f"False Positives (FP): {qual_fp}")
        print(f"True Negatives (TN):  {qual_tn}")
        print(f"False Negatives (FN): {qual_fn}")
        print(f"Precision: {p:.3f} | Recall: {r:.3f} | F1-Score: {f1:.3f} | Accuracy: {acc:.3f}")
        
    # Print Type Classification
    total_type = type_tp + type_fp + type_tn + type_fn
    if total_type > 0:
        p, r, f1, acc = calculate_metrics(type_tp, type_fp, type_tn, type_fn)
        print("\n--- 3. Type Classification (UNIT vs INTEGRATION) ---")
        print(f"True Positives (TP):  {type_tp}")
        print(f"False Positives (FP): {type_fp}")
        print(f"True Negatives (TN):  {type_tn}")
        print(f"False Negatives (FN): {type_fn}")
        print(f"Precision: {p:.3f} | Recall: {r:.3f} | F1-Score: {f1:.3f} | Accuracy: {acc:.3f}")
        
    print("\nNote: Use these values to populate Section 6 (Experiments) in the Phase 3 LaTeX paper.")
    print("=" * 60)

if __name__ == "__main__":
    main()
