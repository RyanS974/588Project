#!/usr/bin/env python3
"""
Script to calculate Cohen's Kappa for inter-rater reliability on the regression validation dataset.
"""

import os
import sys
import pandas as pd
from pathlib import Path

def calculate_cohens_kappa(rater1: pd.Series, rater2: pd.Series) -> float:
    """
    Calculates Cohen's Kappa score between two raters.
    Formula: k = (p_o - p_e) / (1 - p_e)
    Where:
      p_o is the relative observed agreement among raters.
      p_e is the hypothetical probability of chance agreement.
    """
    if len(rater1) != len(rater2):
        raise ValueError("Raters must have the same number of observations.")
    
    n = len(rater1)
    
    # Calculate observed agreement (p_o)
    agreement = (rater1 == rater2).sum()
    p_o = agreement / n
    
    # Calculate expected agreement (p_e)
    # Proportion of 1s and 0s for each rater
    p1_1 = (rater1 == 1).sum() / n
    p1_0 = (rater1 == 0).sum() / n
    
    p2_1 = (rater2 == 1).sum() / n
    p2_0 = (rater2 == 0).sum() / n
    
    # Probability of both saying 1 randomly + probability of both saying 0 randomly
    p_e = (p1_1 * p2_1) + (p1_0 * p2_0)
    
    # If p_e is 1, they perfectly agree by chance (all 1s or all 0s), prevent division by zero
    if p_e == 1:
        return 1.0 if p_o == 1 else 0.0
        
    kappa = (p_o - p_e) / (1 - p_e)
    return kappa, p_o

def main():
    project_root = Path(__file__).parent.parent
    csv_file = project_root / 'data' / 'processed' / 'scores_and_consensus.csv'
    
    if not csv_file.exists():
        print(f"Error: Could not find the validation CSV at {csv_file}")
        print("Please run scripts/generate_regression_sample.py first.")
        sys.exit(1)
        
    print(f"Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    
    # Ensure columns exist
    if 'Ryan_Score' not in df.columns or 'Zach_Score' not in df.columns:
        print("Error: The CSV is missing 'Ryan_Score' or 'Zach_Score' columns.")
        sys.exit(1)
        
    # Drop rows where either score is blank/NaN
    df_clean = df.dropna(subset=['Ryan_Score', 'Zach_Score']).copy()
    
    if len(df_clean) == 0:
        print("Error: No scored data found. Please fill out the Ryan_Score and Zach_Score columns with 1s and 0s.")
        sys.exit(1)
        
    print(f"Found {len(df_clean)} scored rows out of {len(df)} total rows.\n")
    
    # Convert to integers just in case they were parsed as strings/floats
    try:
        ryan_scores = df_clean['Ryan_Score'].astype(int)
        zach_scores = df_clean['Zach_Score'].astype(int)
    except ValueError as e:
        print(f"Error parsing scores: {e}. Please ensure all scores are integers (0 or 1).")
        sys.exit(1)
        
    kappa, p_o = calculate_cohens_kappa(ryan_scores, zach_scores)
    
    print("-" * 40)
    print("INTER-RATER RELIABILITY RESULTS")
    print("-" * 40)
    print(f"Total PRs Evaluated: {len(df_clean)}")
    print(f"Raw Agreement (p_o): {p_o * 100:.2f}%")
    print(f"Cohen's Kappa (k):   {kappa:.4f}")
    print("-" * 40)
    
    # Interpretation of Kappa
    if kappa < 0:
        interpretation = "Poor (Less than chance)"
    elif kappa <= 0.20:
        interpretation = "Slight agreement"
    elif kappa <= 0.40:
        interpretation = "Fair agreement"
    elif kappa <= 0.60:
        interpretation = "Moderate agreement"
    elif kappa <= 0.80:
        interpretation = "Substantial agreement"
    else:
        interpretation = "Almost perfect agreement"
        
    print(f"Interpretation:      {interpretation}")
    print("-" * 40)
    
    # Output disagreements if any
    disagreements = df_clean[ryan_scores != zach_scores]
    if not disagreements.empty:
        print(f"\nDisagreements found in {len(disagreements)} PR(s):")
        for idx, row in disagreements.iterrows():
            print(f"- PR_ID: {row['PR_ID']} (Ryan: {int(row['Ryan_Score'])}, Zach: {int(row['Zach_Score'])})")

if __name__ == "__main__":
    main()
