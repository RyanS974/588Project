#!/usr/bin/env python3
"""
Comprehensive Visualization Script for Testability Analysis

This script generates 21 publication-ready charts using real pipeline data:
- Test Type Distribution (3 charts)
- Regression Test Charts (3 charts)
- Quality Distribution Charts (3 charts)
- Quantitative Metrics Charts (6 charts)
- Qualitative/Standards Charts (6 charts)

Uses real data from the analysis pipeline instead of mock data.

Can use cached results from a previous pipeline run to avoid re-processing.
"""

import os
import sys
import pickle
from pathlib import Path
import logging
import re
from typing import Dict, List, Tuple, Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# Import pipeline components
from scripts.run_analysis_pipeline import run_complete_pipeline
from src.data_structures.pr_data import AIAgent
from src.data_structures.test_classification import TestType, TestQualityLevel
from src.regression_analyzer.models import RegressionType
from src.standards_comparator.comparator import StandardsComparator


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

# Industry standards thresholds
STANDARDS = {
    'python': {'test_ratio': 0.39, 'assert_density': 0.15},
    'java': {'test_ratio': 0.39, 'assert_density': 0.20}
}

# Color palette for agents (matches enum .value property)
AGENT_COLORS = {
    'OpenAI_Codex': '#1f77b4',
    'Copilot': '#ff7f0e',
    'Devin': '#2ca02c',
    'Cursor': '#d62728',
    'Claude_Code': '#9467bd',
    'Human': '#8c564b'
}

# Quality colors
QUALITY_COLORS = {
    'POOR': '#d62728',
    'FAIR': '#ff7f0e',
    'GOOD': '#2ca02c'
}

# Cache file path
CACHE_FILE = Path('./data/pipeline_results_cache.pkl')


def setup_logging():
    """Set up logging for the visualization generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - '
               '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        handlers=[
            logging.FileHandler('comprehensive_viz_generation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def calculate_assertion_density(test_content: str, patch: str = None) -> float:
    """
    Calculate assertion density from test content.

    Args:
        test_content: Test file content (full content or extracted added lines)
        patch: Git patch string (fallback if test_content is empty)

    Returns:
        Assertion density as a float (0.0 to 1.0)
    """
    import pandas as pd

    # Use test_content if available, otherwise extract from patch
    content_to_analyze = test_content if test_content else patch

    # Handle NaN values and non-string types
    if pd.isna(content_to_analyze) or not isinstance(content_to_analyze, str):
        return 0.0

    if not content_to_analyze or not content_to_analyze.strip():
        return 0.0

    test_lines = len([line for line in content_to_analyze.splitlines() if line.strip()])
    if test_lines == 0:
        return 0.0

    # Assertion patterns for Python and Java
    assert_patterns = [
        r'\bassert\s+',  # Python assert
        r'assertEqual|assertNotEqual|assertTrue|assertFalse|assertIn|assertNotIn|assertRaises|assertIs|assertIsNone',
        r'assertEquals|assertNotEquals|assertTrue|assertFalse|assertNull|assertNotNull',
        r'@Test\s*\n.*expect|Mockito\.verify'
    ]

    assertion_count = 0
    for pattern in assert_patterns:
        assertion_count += len(re.findall(pattern, content_to_analyze, re.IGNORECASE | re.MULTILINE))

    return min(1.0, assertion_count / test_lines)


def get_or_run_pipeline(use_cache: bool = True) -> Dict:
    """
    Get pipeline results from cache or run the pipeline.

    Args:
        use_cache: If True, try to use cached results. If False or cache doesn't exist, run pipeline.

    Returns:
        Dictionary with pipeline results.
    """
    logger = logging.getLogger(__name__)

    if use_cache and CACHE_FILE.exists():
        logger.info(f"Found cached results at {CACHE_FILE}")
        logger.info("Loading cached results...")
        try:
            with open(CACHE_FILE, 'rb') as f:
                results = pickle.load(f)
            logger.info("Successfully loaded cached results")
            return results
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}. Running pipeline...")

    # Run the pipeline
    logger.info("Running analysis pipeline...")
    results = run_complete_pipeline()

    # Cache the results
    try:
        CACHE_FILE.parent.mkdir(exist_ok=True)
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(results, f)
        logger.info(f"Cached results saved to {CACHE_FILE}")
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")

    return results


def extract_metrics_from_pipeline(results: Dict) -> pd.DataFrame:
    """
    Extract and calculate metrics from pipeline results.

    Returns a DataFrame with one row per test file containing:
    - test_file_path, pr_id, agent, language
    - test_type, quality_level
    - test_additions, prod_additions, test_to_code_ratio
    - assertion_density
    - is_regression_test, regression_type
    """
    logger = logging.getLogger(__name__)
    logger.info("Extracting metrics from pipeline results...")

    pr_objects = results['pr_objects']
    classified_tests = results['classified_tests']
    regression_results = results['regression_results']

    # Build lookup dictionaries
    test_to_classification = {tc.file_path: tc for tc in classified_tests}

    # Map test file paths to regression results
    test_to_regression = {}
    for rr in regression_results:
        test_to_regression[rr.test_file_path] = rr

    # Build list of metrics per test file
    metrics_list = []

    for pr in pr_objects:
        # Use .value to get the actual agent name (e.g., "OpenAI_Codex") not the enum name
        agent = pr.agent.value
        language = pr.language.lower()

        # Calculate per-PR totals for test-to-code ratio
        pr_test_additions = 0
        pr_prod_additions = 0

        # First pass: calculate PR-level totals
        for fc in pr.file_changes:
            if not fc.language:
                continue
            if fc.file_path in test_to_classification:
                pr_test_additions += fc.additions if fc.additions and fc.additions > 0 else 0
            else:
                pr_prod_additions += fc.additions if fc.additions and fc.additions > 0 else 0

        # Calculate PR-level test-to-code ratio
        pr_ratio = 0.0
        if pr_prod_additions > 0:
            pr_ratio = min(5.0, pr_test_additions / pr_prod_additions)

        # Second pass: collect per-test-file metrics
        for fc in pr.file_changes:
            if not fc.language:
                continue

            test_file_path = fc.file_path

            # Only analyze classified test files
            if test_file_path not in test_to_classification:
                continue

            classification = test_to_classification[test_file_path]

            # Use PR-level ratio for all test files in this PR
            test_to_code_ratio = pr_ratio

            # Calculate assertion density from content (use patch as fallback)
            assertion_density = calculate_assertion_density(fc.content or '', fc.patch)

            # Get regression info if available
            regression_info = test_to_regression.get(test_file_path)
            is_regression = regression_info.is_regression_test if regression_info else False
            regression_type = regression_info.regression_type.name if regression_info else None

            metrics_list.append({
                'test_file_path': test_file_path,
                'pr_id': pr.pr_id,
                'agent': agent,
                'language': language,
                'test_type': classification.primary_type.name,
                'quality_level': classification.quality_level.name,
                'test_additions': fc.additions if fc.additions and fc.additions > 0 else 0,
                'prod_additions': pr_prod_additions,  # PR-level production additions
                'test_to_code_ratio': test_to_code_ratio,
                'assertion_density': assertion_density,
                'is_regression_test': is_regression,
                'regression_type': regression_type
            })

    df = pd.DataFrame(metrics_list)
    logger.info(f"Created DataFrame with {len(df)} test records")

    return df


def ensure_output_dir():
    """Ensure the visualizations directory exists."""
    output_dir = Path("./visualizations")
    output_dir.mkdir(exist_ok=True)
    return output_dir


# ============================================================================
# A. Test Type Distribution Charts (3 charts)
# ============================================================================

def create_test_type_bar_chart(df: pd.DataFrame, output_dir: Path):
    """Chart 1: Bar chart of UNIT vs INTEGRATION counts."""
    logger = logging.getLogger(__name__)

    # Filter out REGRESSION and UNKNOWN for cleaner comparison
    filtered = df[df['test_type'].isin(['UNIT', 'INTEGRATION'])]
    type_counts = filtered['test_type'].value_counts()

    # Reorder to have UNIT first
    if 'UNIT' in type_counts.index and 'INTEGRATION' in type_counts.index:
        type_counts = type_counts[['UNIT', 'INTEGRATION']]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [QUALITY_COLORS.get('GOOD', '#2ca02c') if t == 'UNIT' else QUALITY_COLORS.get('FAIR', '#ff7f0e')
              for t in type_counts.index]

    bars = ax.bar(type_counts.index, type_counts.values, color=colors, edgecolor='black', linewidth=0.8)
    ax.bar_label(bars, fmt='%d', fontsize=16)

    ax.set_xlabel('Test Type', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Distribution of Test Types (Unit vs Integration)', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    output_path = output_dir / '01_test_type_distribution_bar.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_test_type_by_agent_stacked(df: pd.DataFrame, output_dir: Path):
    """Chart 2: Stacked bar chart of test types by agent."""
    logger = logging.getLogger(__name__)

    # Filter to main agents and UNIT/INTEGRATION
    filtered = df[(df['test_type'].isin(['UNIT', 'INTEGRATION'])) &
                  (df['agent'].isin(AGENT_COLORS.keys()))]

    # Check we have data
    if len(filtered) == 0:
        logger.warning("No data for test type by agent chart")
        return

    # Create crosstab - ensure all agents are included
    cross = pd.crosstab(filtered['agent'], filtered['test_type'])

    # Reorder columns to UNIT then INTEGRATION
    for col in ['UNIT', 'INTEGRATION']:
        if col not in cross.columns:
            cross[col] = 0
    cross = cross[['UNIT', 'INTEGRATION']]

    # Ensure all agents are in the plot (even if they have 0 values)
    for agent in AGENT_COLORS.keys():
        if agent not in cross.index:
            cross.loc[agent] = [0, 0]

    # Sort by agent order
    cross = cross.reindex(AGENT_COLORS.keys())

    fig, ax = plt.subplots(figsize=(10, 6))
    cross.plot(kind='bar', stacked=True, ax=ax,
               color=[QUALITY_COLORS['GOOD'], QUALITY_COLORS['FAIR']],
               edgecolor='black', linewidth=0.5)

    ax.set_xlabel('AI Agent', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Test Type Distribution by AI Agent', fontweight='bold')
    ax.legend(title='Test Type', loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    output_path = output_dir / '02_test_type_by_agent_stacked.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_test_type_pie_chart(df: pd.DataFrame, output_dir: Path):
    """Chart 3: Pie chart of test type distribution percentage."""
    logger = logging.getLogger(__name__)

    filtered = df[df['test_type'].isin(['UNIT', 'INTEGRATION'])]
    type_counts = filtered['test_type'].value_counts()

    # Reorder to UNIT first
    if 'UNIT' in type_counts.index and 'INTEGRATION' in type_counts.index:
        type_counts = type_counts[['UNIT', 'INTEGRATION']]

    fig, ax = plt.subplots(figsize=(8, 8))
    colors = [QUALITY_COLORS['GOOD'], QUALITY_COLORS['FAIR']]
    explode = (0.05, 0.05) if len(type_counts) == 2 else (0.05,)

    wedges, texts, autotexts = ax.pie(
        type_counts.values,
        labels=type_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors[:len(type_counts)],
        explode=explode[:len(type_counts)],
        wedgeprops={'edgecolor': 'black', 'linewidth': 0.8}
    )

    for autotext in autotexts:
        autotext.set_fontweight('bold')

    ax.set_title('Test Type Distribution (Percentage)', fontweight='bold', fontsize=20)
    plt.tight_layout()

    output_path = output_dir / '03_test_type_pie.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


# ============================================================================
# B. Regression Test Charts (3 charts)
# ============================================================================

def create_regression_type_bar_chart(df: pd.DataFrame, output_dir: Path):
    """Chart 4: Bar chart of bug_fix vs feature counts."""
    logger = logging.getLogger(__name__)

    # Get only regression tests with known type
    regressions = df[(df['is_regression_test']) &
                     (df['regression_type'].isin(['BUG_FIX', 'FEATURE']))]

    if len(regressions) == 0:
        logger.warning("No regression tests found - creating empty chart")
        # Create a chart showing 0 values
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(['BUG_FIX', 'FEATURE'], [0, 0], color=['#d62728', '#1f77b4'], edgecolor='black', linewidth=0.8)
        ax.text(0.5, 0.5, 'No regression tests found', ha='center', va='center',
                transform=ax.transAxes, fontsize=20)
    else:
        type_counts = regressions['regression_type'].value_counts()

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#d62728' if t == 'BUG_FIX' else '#1f77b4'
                  for t in type_counts.index]

        bars = ax.bar(type_counts.index, type_counts.values, color=colors, edgecolor='black', linewidth=0.8)
        ax.bar_label(bars, fmt='%d', fontsize=16)

    ax.set_xlabel('Regression Type', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Distribution of Regression Test Types', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    output_path = output_dir / '04_regression_type_bar.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_regression_by_agent_stacked(df: pd.DataFrame, output_dir: Path):
    """Chart 5: Stacked bar chart of regression types by agent."""
    logger = logging.getLogger(__name__)

    regressions = df[(df['is_regression_test']) &
                     (df['regression_type'].isin(['BUG_FIX', 'FEATURE'])) &
                     (df['agent'].isin(AGENT_COLORS.keys()))]

    if len(regressions) == 0:
        logger.warning("No regression tests by agent - creating empty chart")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No regression tests found',
                ha='center', va='center', fontsize=20, transform=ax.transAxes)
    else:
        cross = pd.crosstab(regressions['agent'], regressions['regression_type'])

        # Ensure all columns exist
        for col in ['BUG_FIX', 'FEATURE']:
            if col not in cross.columns:
                cross[col] = 0
        cross = cross[['BUG_FIX', 'FEATURE']]

        # Ensure all agents are included
        for agent in AGENT_COLORS.keys():
            if agent not in cross.index:
                cross.loc[agent] = [0, 0]
        cross = cross.reindex(AGENT_COLORS.keys())

        fig, ax = plt.subplots(figsize=(10, 6))
        cross.plot(kind='bar', stacked=True, ax=ax,
                   color=['#d62728', '#1f77b4'],
                   edgecolor='black', linewidth=0.5)

        ax.legend(title='Regression Type', loc='upper right')
        plt.xticks(rotation=45, ha='right')

    ax.set_xlabel('AI Agent', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Regression Test Types by AI Agent', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    output_path = output_dir / '05_regression_by_agent_stacked.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_regression_type_pie_chart(df: pd.DataFrame, output_dir: Path):
    """Chart 6: Pie chart of regression type distribution."""
    logger = logging.getLogger(__name__)

    regressions = df[(df['is_regression_test']) &
                     (df['regression_type'].isin(['BUG_FIX', 'FEATURE']))]

    if len(regressions) == 0:
        logger.warning("No regression tests - creating placeholder chart")
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.5, 0.5, 'No regression tests found',
                ha='center', va='center', fontsize=20, transform=ax.transAxes)
        ax.set_title('Regression Test Type Distribution', fontweight='bold', fontsize=20)
    else:
        type_counts = regressions['regression_type'].value_counts()

        fig, ax = plt.subplots(figsize=(8, 8))
        colors = ['#d62728', '#1f77b4']
        explode = (0.05, 0.05) if len(type_counts) == 2 else (0.05,)

        wedges, texts, autotexts = ax.pie(
            type_counts.values,
            labels=type_counts.index,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors[:len(type_counts)],
            explode=explode[:len(type_counts)],
            wedgeprops={'edgecolor': 'black', 'linewidth': 0.8}
        )

        for autotext in autotexts:
            autotext.set_fontweight('bold')

        ax.set_title('Regression Test Type Distribution', fontweight='bold', fontsize=20)

    plt.tight_layout()

    output_path = output_dir / '06_regression_type_pie.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


# ============================================================================
# C. Quality Distribution Charts (3 charts)
# ============================================================================

def create_quality_bar_chart(df: pd.DataFrame, output_dir: Path):
    """Chart 7: Bar chart of POOR/FAIR/GOOD counts."""
    logger = logging.getLogger(__name__)

    quality_counts = df['quality_level'].value_counts()

    # Reorder to POOR -> FAIR -> GOOD
    order = ['POOR', 'FAIR', 'GOOD']
    quality_counts = quality_counts.reindex([q for q in order if q in quality_counts.index])

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [QUALITY_COLORS[q] for q in quality_counts.index]

    bars = ax.bar(quality_counts.index, quality_counts.values,
                  color=colors, edgecolor='black', linewidth=0.8)
    ax.bar_label(bars, fmt='%d', fontsize=16)

    ax.set_xlabel('Quality Level', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Distribution of Test Quality Levels', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    output_path = output_dir / '07_quality_distribution_bar.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_quality_by_agent_stacked(df: pd.DataFrame, output_dir: Path):
    """Chart 8: Stacked bar chart of quality by agent."""
    logger = logging.getLogger(__name__)

    filtered = df[df['agent'].isin(AGENT_COLORS.keys())]

    if len(filtered) == 0:
        logger.warning("No data for quality by agent chart")
        return

    cross = pd.crosstab(filtered['agent'], filtered['quality_level'])

    # Reorder columns to POOR -> FAIR -> GOOD
    order = ['POOR', 'FAIR', 'GOOD']
    for col in order:
        if col not in cross.columns:
            cross[col] = 0
    cross = cross[[o for o in order if o in cross.columns]]

    # Ensure all agents are included
    for agent in AGENT_COLORS.keys():
        if agent not in cross.index:
            cross.loc[agent] = [0, 0, 0]
    cross = cross.reindex(AGENT_COLORS.keys())

    fig, ax = plt.subplots(figsize=(10, 6))
    cross.plot(kind='bar', stacked=True, ax=ax,
               color=[QUALITY_COLORS['POOR'], QUALITY_COLORS['FAIR'], QUALITY_COLORS['GOOD']],
               edgecolor='black', linewidth=0.5)

    ax.set_xlabel('AI Agent', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Test Quality Distribution by AI Agent', fontweight='bold')
    ax.legend(title='Quality Level', loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    output_path = output_dir / '08_quality_by_agent_stacked.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_quality_by_type_grouped(df: pd.DataFrame, output_dir: Path):
    """Chart 9: Grouped bar chart of quality by test type."""
    logger = logging.getLogger(__name__)

    filtered = df[df['test_type'].isin(['UNIT', 'INTEGRATION'])]

    if len(filtered) == 0:
        logger.warning("No data for quality by type chart")
        return

    cross = pd.crosstab(filtered['test_type'], filtered['quality_level'])

    # Reorder columns to POOR -> FAIR -> GOOD
    order = ['POOR', 'FAIR', 'GOOD']
    for col in order:
        if col not in cross.columns:
            cross[col] = 0
    cross = cross[[o for o in order if o in cross.columns]]

    # Ensure both test types are included
    for test_type in ['UNIT', 'INTEGRATION']:
        if test_type not in cross.index:
            cross.loc[test_type] = [0, 0, 0]
    cross = cross.reindex(['UNIT', 'INTEGRATION'])

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(cross.index))
    width = 0.25

    for i, quality in enumerate(cross.columns):
        offset = (i - 1) * width
        ax.bar(x + offset, cross[quality], width,
               label=quality, color=QUALITY_COLORS[quality],
               edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Test Type', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Quality Level by Test Type', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['Unit Tests', 'Integration Tests'])
    ax.legend(title='Quality', loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    output_path = output_dir / '09_quality_by_type_grouped.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


# ============================================================================
# D. Quantitative Metrics Charts (6 charts)
# ============================================================================

def create_test_code_ratio_by_agent_boxplot(df: pd.DataFrame, output_dir: Path):
    """Chart 10: Box plot of test_to_code_ratio by agent."""
    logger = logging.getLogger(__name__)

    filtered = df[df['agent'].isin(AGENT_COLORS.keys())]

    if len(filtered) == 0:
        logger.warning("No data for test/code ratio by agent boxplot")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    # Prepare data for boxplot
    data = []
    labels = []
    for agent in AGENT_COLORS.keys():
        agent_data = filtered[filtered['agent'] == agent]['test_to_code_ratio'].values
        if len(agent_data) > 0:
            data.append(agent_data)
            labels.append(agent.replace('_', ' '))

    if len(data) == 0:
        logger.warning("No numeric data for test/code ratio boxplot")
        return

    parts = ax.boxplot(data, labels=labels, patch_artist=True,
                       medianprops=dict(color='black', linewidth=2),
                       boxprops=dict(linewidth=0.8),
                       whiskerprops=dict(linewidth=0.8),
                       capprops=dict(linewidth=0.8))

    for patch, agent in zip(parts['boxes'], AGENT_COLORS.keys()):
        if agent in AGENT_COLORS:
            patch.set_facecolor(AGENT_COLORS[agent])
            patch.set_alpha(0.7)

    ax.set_xlabel('AI Agent', fontweight='bold')
    ax.set_ylabel('Test-to-Code Ratio', fontweight='bold')
    ax.set_title('Test-to-Code Ratio Distribution by AI Agent', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    output_path = output_dir / '10_test_code_ratio_by_agent_boxplot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_assertion_density_by_agent_boxplot(df: pd.DataFrame, output_dir: Path):
    """Chart 11: Box plot of assertion_density by agent."""
    logger = logging.getLogger(__name__)

    filtered = df[df['agent'].isin(AGENT_COLORS.keys())]

    if len(filtered) == 0:
        logger.warning("No data for assertion density by agent boxplot")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    data = []
    labels = []
    for agent in AGENT_COLORS.keys():
        agent_data = filtered[filtered['agent'] == agent]['assertion_density'].values
        if len(agent_data) > 0:
            data.append(agent_data)
            labels.append(agent.replace('_', ' '))

    if len(data) == 0:
        logger.warning("No numeric data for assertion density boxplot")
        return

    parts = ax.boxplot(data, labels=labels, patch_artist=True,
                       medianprops=dict(color='black', linewidth=2),
                       boxprops=dict(linewidth=0.8),
                       whiskerprops=dict(linewidth=0.8),
                       capprops=dict(linewidth=0.8))

    for patch, agent in zip(parts['boxes'], AGENT_COLORS.keys()):
        if agent in AGENT_COLORS:
            patch.set_facecolor(AGENT_COLORS[agent])
            patch.set_alpha(0.7)

    ax.set_xlabel('AI Agent', fontweight='bold')
    ax.set_ylabel('Assertion Density', fontweight='bold')
    ax.set_title('Assertion Density Distribution by AI Agent', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    output_path = output_dir / '11_assertion_density_by_agent_boxplot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_test_code_ratio_by_type_boxplot(df: pd.DataFrame, output_dir: Path):
    """Chart 12: Box plot of test_to_code_ratio by test type."""
    logger = logging.getLogger(__name__)

    filtered = df[df['test_type'].isin(['UNIT', 'INTEGRATION'])]

    if len(filtered) == 0:
        logger.warning("No data for test/code ratio by type boxplot")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    data = []
    for test_type in ['UNIT', 'INTEGRATION']:
        type_data = filtered[filtered['test_type'] == test_type]['test_to_code_ratio'].values
        data.append(type_data)

    labels = ['Unit Tests', 'Integration Tests']

    parts = ax.boxplot(data, labels=labels, patch_artist=True,
                       medianprops=dict(color='black', linewidth=2),
                       boxprops=dict(linewidth=0.8),
                       whiskerprops=dict(linewidth=0.8),
                       capprops=dict(linewidth=0.8))

    colors = [QUALITY_COLORS['GOOD'], QUALITY_COLORS['FAIR']]
    for patch, color in zip(parts['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xlabel('Test Type', fontweight='bold')
    ax.set_ylabel('Test-to-Code Ratio', fontweight='bold')
    ax.set_title('Test-to-Code Ratio by Test Type', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    output_path = output_dir / '12_test_code_ratio_by_type_boxplot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_assertion_density_by_type_boxplot(df: pd.DataFrame, output_dir: Path):
    """Chart 13: Box plot of assertion_density by test type."""
    logger = logging.getLogger(__name__)

    filtered = df[df['test_type'].isin(['UNIT', 'INTEGRATION'])]

    if len(filtered) == 0:
        logger.warning("No data for assertion density by type boxplot")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    data = []
    for test_type in ['UNIT', 'INTEGRATION']:
        type_data = filtered[filtered['test_type'] == test_type]['assertion_density'].values
        data.append(type_data)

    labels = ['Unit Tests', 'Integration Tests']

    parts = ax.boxplot(data, labels=labels, patch_artist=True,
                       medianprops=dict(color='black', linewidth=2),
                       boxprops=dict(linewidth=0.8),
                       whiskerprops=dict(linewidth=0.8),
                       capprops=dict(linewidth=0.8))

    colors = [QUALITY_COLORS['GOOD'], QUALITY_COLORS['FAIR']]
    for patch, color in zip(parts['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xlabel('Test Type', fontweight='bold')
    ax.set_ylabel('Assertion Density', fontweight='bold')
    ax.set_title('Assertion Density by Test Type', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    output_path = output_dir / '13_assertion_density_by_type_boxplot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_ratio_vs_density_scatter(df: pd.DataFrame, output_dir: Path):
    """Chart 14: Scatter plot of test_to_code_ratio vs assertion_density colored by agent."""
    logger = logging.getLogger(__name__)

    filtered = df[df['agent'].isin(AGENT_COLORS.keys())]

    if len(filtered) == 0:
        logger.warning("No data for ratio vs density scatter")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    for agent in AGENT_COLORS.keys():
        agent_data = filtered[filtered['agent'] == agent]
        if len(agent_data) > 0:
            ax.scatter(agent_data['test_to_code_ratio'],
                       agent_data['assertion_density'],
                       label=agent.replace('_', ' '), color=AGENT_COLORS[agent],
                       alpha=0.6, s=30, edgecolors='black', linewidth=0.3)

    ax.set_xlabel('Test-to-Code Ratio', fontweight='bold')
    ax.set_ylabel('Assertion Density', fontweight='bold')
    ax.set_title('Test-to-Code Ratio vs Assertion Density by AI Agent', fontweight='bold')
    ax.legend(loc='best', fontsize=14, ncol=2)
    ax.grid(alpha=0.3, linestyle='--')
    plt.tight_layout()

    output_path = output_dir / '14_ratio_vs_density_scatter.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_mean_metrics_by_agent_grouped(df: pd.DataFrame, output_dir: Path):
    """Chart 15: Grouped bar chart of mean metrics by agent."""
    logger = logging.getLogger(__name__)

    filtered = df[df['agent'].isin(AGENT_COLORS.keys())]

    if len(filtered) == 0:
        logger.warning("No data for mean metrics by agent chart")
        return

    # Calculate mean metrics
    mean_metrics = filtered.groupby('agent')[['test_to_code_ratio', 'assertion_density']].mean()

    # Ensure all agents are included
    for agent in AGENT_COLORS.keys():
        if agent not in mean_metrics.index:
            mean_metrics.loc[agent] = [0, 0]
    mean_metrics = mean_metrics.reindex(AGENT_COLORS.keys())

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(mean_metrics.index))
    width = 0.35

    ax.bar(x - width/2, mean_metrics['test_to_code_ratio'], width,
           label='Test-to-Code Ratio', color='#1f77b4',
           edgecolor='black', linewidth=0.5)
    ax.bar(x + width/2, mean_metrics['assertion_density'], width,
           label='Assertion Density', color='#ff7f0e',
           edgecolor='black', linewidth=0.5)

    ax.set_xlabel('AI Agent', fontweight='bold')
    ax.set_ylabel('Mean Value', fontweight='bold')
    ax.set_title('Mean Metrics by AI Agent', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([a.replace('_', ' ') for a in mean_metrics.index], rotation=45, ha='right')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    output_path = output_dir / '15_mean_metrics_by_agent_grouped.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


# ============================================================================
# E. Qualitative/Standards Charts (5 charts)
# ============================================================================

def create_standards_compliance_bar(df: pd.DataFrame, output_dir: Path):
    """Chart 16: Bar chart of % below/at/above threshold for each metric."""
    logger = logging.getLogger(__name__)

    # Calculate compliance percentages
    metrics_config = {
        'test_to_code_ratio': 0.39,
        'assertion_density': 0.15
    }

    compliance_data = []
    for metric, threshold in metrics_config.items():
        below = (df[metric] < threshold * 0.9).sum() / len(df) * 100
        at = ((df[metric] >= threshold * 0.9) & (df[metric] <= threshold * 1.1)).sum() / len(df) * 100
        above = (df[metric] > threshold * 1.1).sum() / len(df) * 100
        compliance_data.append({'Metric': metric.replace('_', ' ').title(),
                               'Below Standard': below, 'At Standard': at, 'Above Standard': above})

    comp_df = pd.DataFrame(compliance_data)

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(comp_df))
    width = 0.25

    ax.bar(x - width, comp_df['Below Standard'], width, label='Below Standard',
           color='#d62728', edgecolor='black', linewidth=0.5)
    ax.bar(x, comp_df['At Standard'], width, label='At Standard',
           color='#ff7f0e', edgecolor='black', linewidth=0.5)
    ax.bar(x + width, comp_df['Above Standard'], width, label='Above Standard',
           color='#2ca02c', edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Metric', fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontweight='bold')
    ax.set_title('Standards Compliance Distribution', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(comp_df['Metric'])
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    output_path = output_dir / '16_standards_compliance_bar.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_compliance_by_agent_stacked(df: pd.DataFrame, output_dir: Path):
    """Chart 17: Stacked bar chart of standards compliance by agent."""
    logger = logging.getLogger(__name__)

    # Determine compliance for test_to_code_ratio
    threshold = 0.39
    df_copy = df.copy()
    df_copy['compliance'] = df_copy['test_to_code_ratio'].apply(
        lambda x: 'Above' if x > threshold * 1.1 else ('At' if x >= threshold * 0.9 else 'Below')
    )

    filtered = df_copy[df_copy['agent'].isin(AGENT_COLORS.keys())]

    if len(filtered) == 0:
        logger.warning("No data for compliance by agent chart")
        return

    cross = pd.crosstab(filtered['agent'], filtered['compliance'])

    # Ensure consistent column order
    for col in ['Below', 'At', 'Above']:
        if col not in cross.columns:
            cross[col] = 0
    cross = cross[['Below', 'At', 'Above']]

    # Ensure all agents are included
    for agent in AGENT_COLORS.keys():
        if agent not in cross.index:
            cross.loc[agent] = [0, 0, 0]
    cross = cross.reindex(AGENT_COLORS.keys())

    fig, ax = plt.subplots(figsize=(10, 6))
    cross.plot(kind='bar', stacked=True, ax=ax,
               color=['#d62728', '#ff7f0e', '#2ca02c'],
               edgecolor='black', linewidth=0.5)

    ax.set_xlabel('AI Agent', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Test-to-Code Ratio Standards Compliance by Agent', fontweight='bold')
    ax.legend(title='Compliance', loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    output_path = output_dir / '17_compliance_by_agent_stacked.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_agent_metric_compliance_heatmap(df: pd.DataFrame, output_dir: Path):
    """Chart 18: Heatmap of Agent × Metric compliance matrix."""
    logger = logging.getLogger(__name__)

    # Calculate percentage above threshold for each agent-metric pair
    metrics_config = {
        'test_to_code_ratio': 0.39,
        'assertion_density': 0.15
    }

    agents = list(AGENT_COLORS.keys())
    metric_names = ['Test-to-Code\nRatio', 'Assertion\nDensity']

    # Build matrix
    matrix = np.zeros((len(agents), len(metric_names)))
    for i, agent in enumerate(agents):
        agent_data = df[df['agent'] == agent]
        for j, (metric, threshold) in enumerate(metrics_config.items()):
            if len(agent_data) > 0:
                above_pct = (agent_data[metric] > threshold * 1.1).sum() / len(agent_data) * 100
                matrix[i, j] = above_pct
            else:
                matrix[i, j] = 0

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

    ax.set_xticks(np.arange(len(metric_names)))
    ax.set_yticks(np.arange(len(agents)))
    ax.set_xticklabels(metric_names)
    ax.set_yticklabels([a.replace('_', ' ') for a in agents])

    # Add text annotations
    for i in range(len(agents)):
        for j in range(len(metric_names)):
            text = ax.text(j, i, f'{matrix[i, j]:.0f}%',
                          ha="center", va="center", color="black", fontsize=14)

    ax.set_title('Percentage Above Industry Standard by Agent and Metric', fontweight='bold')
    ax.set_xlabel('Metric', fontweight='bold')
    ax.set_ylabel('AI Agent', fontweight='bold')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('% Above Standard', rotation=270, labelpad=20, fontweight='bold')

    plt.tight_layout()

    output_path = output_dir / '18_agent_metric_compliance_heatmap.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_test_ratio_vs_threshold(df: pd.DataFrame, output_dir: Path):
    """Chart 19: Bar chart of mean test-to-code ratio vs threshold."""
    logger = logging.getLogger(__name__)

    filtered = df[df['agent'].isin(AGENT_COLORS.keys())]

    if len(filtered) == 0:
        logger.warning("No data for metrics vs threshold chart")
        return

    mean_metrics = filtered.groupby('agent')[['test_to_code_ratio']].mean()

    threshold = 0.39

    # Ensure all agents are included
    for agent in AGENT_COLORS.keys():
        if agent not in mean_metrics.index:
            mean_metrics.loc[agent] = [0]
    mean_metrics = mean_metrics.reindex(AGENT_COLORS.keys())

    fig, ax = plt.subplots(figsize=(8, 6))

    # Test-to-Code Ratio
    agents = mean_metrics.index
    x = np.arange(len(agents))
    bars = ax.bar(x, mean_metrics['test_to_code_ratio'],
                    color='#1f77b4', edgecolor='black', linewidth=0.8)
    ax.axhline(y=threshold, color='red', linestyle='--',
                linewidth=2, label=f'Threshold ({threshold})')
    ax.set_xlabel('AI Agent', fontweight='bold')
    ax.set_ylabel('Mean Test-to-Code Ratio', fontweight='bold')
    ax.set_title('Test-to-Code Ratio vs Industry Standard', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([a.replace('_', ' ') for a in agents], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.bar_label(bars, fmt='%.2f', fontsize=14)

    plt.tight_layout()

    output_path = output_dir / '19_metrics_vs_threshold_test_ratio.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")

def create_assertion_density_vs_threshold(df: pd.DataFrame, output_dir: Path):
    """Chart 20: Bar chart of mean assertion density vs threshold."""
    logger = logging.getLogger(__name__)

    filtered = df[df['agent'].isin(AGENT_COLORS.keys())]

    if len(filtered) == 0:
        logger.warning("No data for metrics vs threshold chart")
        return

    mean_metrics = filtered.groupby('agent')[['assertion_density']].mean()

    threshold = 0.15

    # Ensure all agents are included
    for agent in AGENT_COLORS.keys():
        if agent not in mean_metrics.index:
            mean_metrics.loc[agent] = [0]
    mean_metrics = mean_metrics.reindex(AGENT_COLORS.keys())

    fig, ax = plt.subplots(figsize=(8, 6))

    # Assertion Density
    agents = mean_metrics.index
    x = np.arange(len(agents))
    bars = ax.bar(x, mean_metrics['assertion_density'],
                    color='#ff7f0e', edgecolor='black', linewidth=0.8)
    ax.axhline(y=threshold, color='red', linestyle='--',
                linewidth=2, label=f'Threshold ({threshold})')
    ax.set_xlabel('AI Agent', fontweight='bold')
    ax.set_ylabel('Mean Assertion Density', fontweight='bold')
    ax.set_title('Assertion Density vs Industry Standard', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([a.replace('_', ' ') for a in agents], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.bar_label(bars, fmt='%.3f', fontsize=14)

    plt.tight_layout()

    output_path = output_dir / '20_metrics_vs_threshold_assertion_density.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


def create_agent_radar_comparison(df: pd.DataFrame, output_dir: Path):
    """Chart 21: Radar chart comparing all agents on all metrics."""
    logger = logging.getLogger(__name__)

    filtered = df[df['agent'].isin(AGENT_COLORS.keys())]

    if len(filtered) == 0:
        logger.warning("No data for radar chart")
        return

    # Calculate normalized scores (0-1) based on thresholds
    thresholds = {'test_to_code_ratio': 0.39, 'assertion_density': 0.15}

    metrics_data = {}
    for agent in AGENT_COLORS.keys():
        agent_data = filtered[filtered['agent'] == agent]
        if len(agent_data) > 0:
            metrics_data[agent] = {
                'Test-to-Code\nRatio': min(2.0, agent_data['test_to_code_ratio'].mean() / thresholds['test_to_code_ratio']),
                'Assertion\nDensity': min(2.0, agent_data['assertion_density'].mean() / thresholds['assertion_density'])
            }
        else:
            metrics_data[agent] = {
                'Test-to-Code\nRatio': 0,
                'Assertion\nDensity': 0
            }

    # Create radar chart
    categories = ['Test-to-Code\nRatio', 'Assertion\nDensity']
    N = len(categories)

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

    for agent in AGENT_COLORS.keys():
        values = [metrics_data[agent][cat] for cat in categories]
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=2, label=agent.replace('_', ' '), color=AGENT_COLORS[agent])
        ax.fill(angles, values, alpha=0.15, color=AGENT_COLORS[agent])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 1.5)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['0.25x', '0.5x', '0.75x', '1.0x'])
    ax.grid(True, linestyle='--', alpha=0.7)

    # Draw threshold circles
    ax.plot(angles, [1.0] * (N + 1), 'r--', linewidth=1, alpha=0.5, label='Standard (1.0x)')

    ax.set_title('AI Agent Performance Comparison\n(Relative to Industry Standards)',
                 fontweight='bold', fontsize=20, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=14)

    plt.tight_layout()

    output_path = output_dir / '21_agent_radar_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Created: {output_path}")


# ============================================================================
# Main Orchestration
# ============================================================================

def generate_all_visualizations(use_cache: bool = True):
    """
    Main function to generate all 21 visualizations.

    Args:
        use_cache: If True, try to use cached pipeline results.
    """
    logger = logging.getLogger(__name__)
    logger.info("="*70)
    logger.info("COMPREHENSIVE VISUALIZATION GENERATION")
    logger.info("="*70)

    output_dir = ensure_output_dir()

    # Step 1: Get pipeline results (from cache or run new)
    logger.info(f"\n[Step 1/3] Getting analysis pipeline results (use_cache={use_cache})...")
    results = get_or_run_pipeline(use_cache=use_cache)

    # Step 2: Extract metrics from pipeline results
    logger.info("\n[Step 2/3] Extracting metrics from pipeline results...")
    df = extract_metrics_from_pipeline(results)

    # Print summary statistics
    logger.info("\n--- Data Summary ---")
    logger.info(f"Total test files: {len(df)}")
    logger.info(f"Agents: {df['agent'].unique().tolist()}")
    logger.info(f"Test types: {df['test_type'].value_counts().to_dict()}")
    logger.info(f"Quality levels: {df['quality_level'].value_counts().to_dict()}")
    if df['is_regression_test'].sum() > 0:
        logger.info(f"Regression tests: {df['is_regression_test'].sum()}")

    # Step 3: Generate all 21 charts
    logger.info("\n[Step 3/3] Generating 21 visualizations...")

    # A. Test Type Distribution (3 charts)
    logger.info("\n--- A. Test Type Distribution Charts ---")
    create_test_type_bar_chart(df, output_dir)
    create_test_type_by_agent_stacked(df, output_dir)
    create_test_type_pie_chart(df, output_dir)

    # B. Regression Test Charts (3 charts)
    logger.info("\n--- B. Regression Test Charts ---")
    create_regression_type_bar_chart(df, output_dir)
    create_regression_by_agent_stacked(df, output_dir)
    create_regression_type_pie_chart(df, output_dir)

    # C. Quality Distribution Charts (3 charts)
    logger.info("\n--- C. Quality Distribution Charts ---")
    create_quality_bar_chart(df, output_dir)
    create_quality_by_agent_stacked(df, output_dir)
    create_quality_by_type_grouped(df, output_dir)

    # D. Quantitative Metrics Charts (6 charts)
    logger.info("\n--- D. Quantitative Metrics Charts ---")
    create_test_code_ratio_by_agent_boxplot(df, output_dir)
    create_assertion_density_by_agent_boxplot(df, output_dir)
    create_test_code_ratio_by_type_boxplot(df, output_dir)
    create_assertion_density_by_type_boxplot(df, output_dir)
    create_ratio_vs_density_scatter(df, output_dir)
    create_mean_metrics_by_agent_grouped(df, output_dir)

    # E. Qualitative/Standards Charts (6 charts)
    logger.info("\n--- E. Qualitative/Standards Charts ---")
    create_standards_compliance_bar(df, output_dir)
    create_compliance_by_agent_stacked(df, output_dir)
    create_agent_metric_compliance_heatmap(df, output_dir)
    create_test_ratio_vs_threshold(df, output_dir)
    create_assertion_density_vs_threshold(df, output_dir)
    create_agent_radar_comparison(df, output_dir)

    # Final summary
    logger.info("\n" + "="*70)
    logger.info("VISUALIZATION GENERATION COMPLETE")
    logger.info("="*70)
    logger.info(f"Generated 21 charts in: {output_dir}/")
    logger.info("\nGenerated files:")
    for i in range(1, 22):
        logger.info(f"  {i:02d}_*.png")

    return output_dir


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate comprehensive visualizations from testability analysis pipeline data.'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Force re-running the pipeline instead of using cached results'
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print(" COMPREHENSIVE VISUALIZATION SCRIPT")
    print(" Generating 21 publication-ready charts from real pipeline data")
    print("="*70 + "\n")

    setup_logging()

    try:
        output_dir = generate_all_visualizations(use_cache=not args.no_cache)

        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"\nAll 21 visualizations saved to: {output_dir}/")
        print("\nNext steps:")
        print("- Review charts for paper selection")
        print("- Verify data accuracy")
        print("- Adjust styling if needed")

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
