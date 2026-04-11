#!/usr/bin/env python3
"""
Generate visualizations focused on Human vs AI comparisons.
"""

import os
import sys
from pathlib import Path
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.generate_comprehensive_visualizations import (
    get_or_run_pipeline, 
    extract_metrics_from_pipeline,
    AGENT_COLORS,
    QUALITY_COLORS
)

# Configuration for paper-quality visualizations
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 16
plt.rcParams['axes.labelsize'] = 18
plt.rcParams['axes.titlesize'] = 20
plt.rcParams['xtick.labelsize'] = 16
plt.rcParams['ytick.labelsize'] = 16
plt.rcParams['legend.fontsize'] = 16
plt.rcParams['figure.figsize'] = (10, 6)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - '
               '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def create_aggregated_ai_vs_human_bar(df: pd.DataFrame, output_dir: Path):
    logger = logging.getLogger(__name__)
    
    # Create an 'AuthorType' column: 'AI' vs 'Human'
    df['author_type'] = df['agent'].apply(lambda x: 'Human' if x == 'Human' else 'AI')
    
    # Group by author type
    mean_metrics = df.groupby('author_type')[['test_to_code_ratio', 'assertion_density']].mean()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.arange(len(mean_metrics.columns))
    width = 0.35
    
    # Ensure order is AI, Human
    order = ['AI', 'Human']
    mean_metrics = mean_metrics.reindex(order)
    
    ax.bar(x - width/2, mean_metrics.loc['AI'], width, label='AI (Aggregated)', color='#1f77b4', edgecolor='black', linewidth=0.5)
    ax.bar(x + width/2, mean_metrics.loc['Human'], width, label='Human Baseline', color='#8c564b', edgecolor='black', linewidth=0.5)
    
    ax.set_ylabel('Mean Value', fontweight='bold')
    ax.set_title('AI vs. Human: Mean Metrics', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['Test-to-Code Ratio', 'Assertion Density'], fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    output_path = output_dir / '22_ai_vs_human_aggregated_metrics_bar.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")

def create_human_test_type_pie(df: pd.DataFrame, output_dir: Path):
    logger = logging.getLogger(__name__)
    human_df = df[df['agent'] == 'Human']
    if human_df.empty:
        logger.warning("No human data found for test type pie.")
        return
        
    counts = human_df['test_type'].value_counts()
    
    # Use consistent colors for test types
    type_colors = {'UNIT': '#1f77b4', 'INTEGRATION': '#ff7f0e', 'UNKNOWN': '#7f7f7f'}
    colors = [type_colors.get(idx, '#cccccc') for idx in counts.index]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, colors=colors, textprops={'fontsize': 14, 'fontweight': 'bold'}, wedgeprops={'edgecolor': 'black', 'linewidth': 0.5})
    ax.set_title('Human Baseline: Test Type Distribution', fontweight='bold')
    
    output_path = output_dir / '23_human_test_type_pie.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")

def create_human_quality_pie(df: pd.DataFrame, output_dir: Path):
    logger = logging.getLogger(__name__)
    human_df = df[df['agent'] == 'Human']
    if human_df.empty:
        logger.warning("No human data found for quality pie.")
        return
        
    counts = human_df['quality_level'].value_counts()
    
    # Use consistent colors for quality
    colors = [QUALITY_COLORS.get(idx, '#cccccc') for idx in counts.index]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, colors=colors, textprops={'fontsize': 14, 'fontweight': 'bold'}, wedgeprops={'edgecolor': 'black', 'linewidth': 0.5})
    ax.set_title('Human Baseline: Test Quality Distribution', fontweight='bold')
    
    output_path = output_dir / '24_human_quality_pie.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")

def create_ai_vs_human_quality_grouped(df: pd.DataFrame, output_dir: Path):
    logger = logging.getLogger(__name__)
    
    df['author_type'] = df['agent'].apply(lambda x: 'Human' if x == 'Human' else 'AI')
    
    # Calculate percentages
    quality_counts = df.groupby(['author_type', 'quality_level']).size().unstack(fill_value=0)
    # Normalize by author type total
    quality_pct = quality_counts.div(quality_counts.sum(axis=1), axis=0) * 100
    
    # Ensure all columns exist
    for col in ['GOOD', 'FAIR', 'POOR']:
        if col not in quality_pct.columns:
            quality_pct[col] = 0
            
    quality_pct = quality_pct[['GOOD', 'FAIR', 'POOR']]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    x = np.arange(len(quality_pct.columns))
    width = 0.35
    
    # Ensure order
    if 'AI' in quality_pct.index:
        ax.bar(x - width/2, quality_pct.loc['AI'], width, label='AI (Aggregated)', color='#1f77b4', edgecolor='black')
    if 'Human' in quality_pct.index:
        ax.bar(x + width/2, quality_pct.loc['Human'], width, label='Human Baseline', color='#8c564b', edgecolor='black')
        
    ax.set_ylabel('Percentage (%)', fontweight='bold')
    ax.set_title('AI vs. Human: Test Quality Distribution', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(quality_pct.columns, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    output_path = output_dir / '25_ai_vs_human_quality_grouped.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    output_dir = Path('./visualizations')
    output_dir.mkdir(exist_ok=True, parents=True)
    
    logger.info("Loading pipeline results...")
    results = get_or_run_pipeline(use_cache=True)
    
    logger.info("Extracting metrics...")
    df = extract_metrics_from_pipeline(results)
    
    logger.info("Creating Human-focused visualizations...")
    create_aggregated_ai_vs_human_bar(df, output_dir)
    create_human_test_type_pie(df, output_dir)
    create_human_quality_pie(df, output_dir)
    create_ai_vs_human_quality_grouped(df, output_dir)
    
    logger.info("Done generating new visualizations!")

if __name__ == '__main__':
    main()