#!/usr/bin/env python3
"""
Script to generate comprehensive reports using the Report Generator Component.

This script will:
1. Run the complete analysis pipeline
2. Extract real metrics from pipeline results
3. Generate various types of reports:
   - Executive Summary
   - Detailed Analysis
   - Compliance Report
   - Metrics Overview
4. Save reports in Markdown format
"""

import os
import sys
import re
from pathlib import Path
import logging
from typing import Dict, List

# Add the project root to the path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.run_analysis_pipeline import run_complete_pipeline
from src.report_generator.generator import ReportGenerator
import pickle
from src.report_generator.constants import ReportType, ReportFormat, ReportData, ReportConfig
from src.data_structures.test_classification import TestType, TestQualityLevel
from src.regression_analyzer.models import RegressionType


# Industry standards thresholds
STANDARDS = {
    'test_to_code_ratio': 0.39,
    'assertion_density': 0.15
}

# Cache file path (same as visualizations script for consistency)
CACHE_FILE = Path('./data/pipeline_results_cache.pkl')


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
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(results, f)
        logger.info(f"Cached results saved to {CACHE_FILE}")
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")

    return results


def setup_logging():
    """Set up logging for the report generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - '
               '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        handlers=[
            logging.FileHandler('report_generation.log'),
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


def calculate_test_type_distribution(classified_tests: List) -> Dict[str, int]:
    """Aggregate test type counts."""
    type_counts = {}
    for tc in classified_tests:
        test_type = tc.primary_type.name
        type_counts[test_type] = type_counts.get(test_type, 0) + 1
    return type_counts


def calculate_quality_distribution(classified_tests: List) -> Dict[str, int]:
    """Aggregate quality level counts."""
    quality_counts = {}
    for tc in classified_tests:
        quality = tc.quality_level.name
        quality_counts[quality] = quality_counts.get(quality, 0) + 1
    return quality_counts


def calculate_regression_statistics(regression_results: List) -> Dict[str, int]:
    """Calculate regression test statistics."""
    bug_fix_count = sum(1 for rr in regression_results if rr.regression_type.name == 'BUG_FIX')
    feature_count = sum(1 for rr in regression_results if rr.regression_type.name == 'FEATURE')
    return {'bug_fix': bug_fix_count, 'feature': feature_count, 'total': len(regression_results)}


def calculate_agent_distribution(pr_objects: List) -> Dict[str, int]:
    """Calculate agent distribution from PR objects."""
    agent_counts = {}
    for pr in pr_objects:
        agent = pr.agent.name
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
    return agent_counts


def calculate_language_distribution(pr_objects: List) -> Dict[str, int]:
    """Calculate language distribution from PR objects."""
    language_counts = {}
    for pr in pr_objects:
        language = pr.language
        language_counts[language] = language_counts.get(language, 0) + 1
    return language_counts


def extract_metrics_from_pipeline(results: Dict) -> Dict:
    """
    Extract and calculate metrics from pipeline results.

    Returns a dictionary with aggregate metrics for report generation.
    """
    logger = logging.getLogger(__name__)
    logger.info("Extracting metrics from pipeline results...")

    pr_objects = results['pr_objects']
    classified_tests = results['classified_tests']
    regression_results = results['regression_results']

    # Basic counts
    total_prs = len(pr_objects)
    total_tests_classified = len(classified_tests)
    total_regression_tests = len(regression_results)

    # Test type distribution
    test_type_dist = calculate_test_type_distribution(classified_tests)
    unit_tests = test_type_dist.get('UNIT', 0)
    integration_tests = test_type_dist.get('INTEGRATION', 0)
    unknown_tests = test_type_dist.get('UNKNOWN', 0)

    # Quality distribution
    quality_dist = calculate_quality_distribution(classified_tests)
    good_quality = quality_dist.get('GOOD', 0)
    fair_quality = quality_dist.get('FAIR', 0)
    poor_quality = quality_dist.get('POOR', 0)

    # Regression statistics
    regression_stats = calculate_regression_statistics(regression_results)

    # Calculate aggregate metrics from PR data
    # Build lookup for test file paths to classifications
    test_to_classification = {tc.file_path: tc for tc in classified_tests}

    # Calculate test_to_code_ratio and assertion_density from PR file changes
    test_to_code_ratios = []
    assertion_densities = []

    for pr in pr_objects:
        # Calculate per-PR test-to-code ratio
        pr_test_additions = 0
        pr_prod_additions = 0

        for fc in pr.file_changes:
            if not fc.language:
                continue

            if fc.file_path in test_to_classification:
                # This is a test file
                pr_test_additions += fc.additions if fc.additions and fc.additions > 0 else 0

                # Calculate assertion density for test files only
                density = calculate_assertion_density(fc.content or '', fc.patch)
                assertion_densities.append(density)
            else:
                # This is a production file (non-test)
                pr_prod_additions += fc.additions if fc.additions and fc.additions > 0 else 0

        # Calculate ratio for this PR (avoid division by zero)
        if pr_prod_additions > 0:
            ratio = pr_test_additions / pr_prod_additions
            # Cap at reasonable values (e.g., max 5.0 for extreme cases)
            ratio = min(5.0, ratio)
            test_to_code_ratios.append(ratio)

    # Calculate averages
    avg_test_to_code_ratio = sum(test_to_code_ratios) / len(test_to_code_ratios) if test_to_code_ratios else 0.0
    avg_assertion_density = sum(assertion_densities) / len(assertion_densities) if assertion_densities else 0.0

    # Calculate pass rate (percentage of tests with GOOD or FAIR quality)
    pass_count = good_quality + fair_quality
    pass_rate = (pass_count / total_tests_classified * 100) if total_tests_classified > 0 else 0.0

    # Calculate test coverage (percentage of PRs with tests)
    prs_with_tests = sum(1 for pr in pr_objects if any(fc.file_path in test_to_classification for fc in pr.file_changes if fc.language))
    test_coverage = (prs_with_tests / total_prs * 100) if total_prs > 0 else 0.0

    # Agent and language distribution
    agent_dist = calculate_agent_distribution(pr_objects)
    language_dist = calculate_language_distribution(pr_objects)

    metrics = {
        'total_prs': total_prs,
        'total_tests_classified': total_tests_classified,
        'total_regression_tests': total_regression_tests,
        'test_coverage': f'{test_coverage:.1f}',
        'pass_rate': f'{pass_rate:.1f}',
        'test_type_distribution': test_type_dist,
        'quality_distribution': quality_dist,
        'regression_statistics': regression_stats,
        'agent_distribution': agent_dist,
        'language_distribution': language_dist,
        'average_test_to_code_ratio': f'{avg_test_to_code_ratio:.3f}',
        'average_assertion_density': f'{avg_assertion_density:.3f}',
        'unit_tests_count': unit_tests,
        'integration_tests_count': integration_tests,
        'good_quality_count': good_quality,
        'fair_quality_count': fair_quality,
        'poor_quality_count': poor_quality,
        'unit_test_percentage': f'{(unit_tests / total_tests_classified * 100):.1f}' if total_tests_classified > 0 else '0.0',
        'integration_test_percentage': f'{(integration_tests / total_tests_classified * 100):.1f}' if total_tests_classified > 0 else '0.0',
        'good_quality_percentage': f'{(good_quality / total_tests_classified * 100):.1f}' if total_tests_classified > 0 else '0.0',
        'fair_quality_percentage': f'{(fair_quality / total_tests_classified * 100):.1f}' if total_tests_classified > 0 else '0.0',
        'poor_quality_percentage': f'{(poor_quality / total_tests_classified * 100):.1f}' if total_tests_classified > 0 else '0.0',
    }

    logger.info(f"Extracted metrics: {total_tests_classified} tests, {test_coverage:.1f}% coverage, {pass_rate:.1f}% pass rate")
    return metrics


def generate_compliance_assessment(metrics: Dict) -> Dict:
    """Generate compliance assessment based on metrics."""
    logger = logging.getLogger(__name__)

    # Parse average values
    try:
        avg_ratio = float(metrics['average_test_to_code_ratio'])
        avg_density = float(metrics['average_assertion_density'])
    except (ValueError, KeyError):
        avg_ratio = 0.0
        avg_density = 0.0

    # Assess compliance
    ratio_compliant = avg_ratio >= STANDARDS['test_to_code_ratio']
    density_compliant = avg_density >= STANDARDS['assertion_density']

    compliance_summary = f"Overall compliance assessment based on {metrics['total_tests_classified']} classified tests:\n\n"
    compliance_summary += f"**Test-to-Code Ratio**: {avg_ratio:.3f} (threshold: {STANDARDS['test_to_code_ratio']}) - "
    compliance_summary += "✅ COMPLIANT\n" if ratio_compliant else "❌ BELOW STANDARD\n"
    compliance_summary += f"**Assertion Density**: {avg_density:.3f} (threshold: {STANDARDS['assertion_density']}) - "
    compliance_summary += "✅ COMPLIANT" if density_compliant else "❌ BELOW STANDARD"

    # Generate action items
    action_items = []
    if not ratio_compliant:
        action_items.append(f"Improve test-to-code ratio: Current {avg_ratio:.3f} is below industry standard of {STANDARDS['test_to_code_ratio']}")
    if not density_compliant:
        action_items.append(f"Increase assertion density: Current {avg_density:.3f} is below industry standard of {STANDARDS['assertion_density']}")
    if metrics['poor_quality_count'] > 0:
        poor_pct = float(metrics['poor_quality_percentage'])
        action_items.append(f"Address poor quality tests: {poor_pct:.1f}% of tests are rated as POOR quality")

    if not action_items:
        action_items.append("All metrics meet or exceed industry standards. Continue current practices.")

    standards_comparison = {
        'Test-to-Code Ratio': {
            'compliant': ratio_compliant,
            'details': f'Average ratio: {avg_ratio:.3f} (Industry standard: {STANDARDS["test_to_code_ratio"]})',
            'recommendations': 'Maintain current test coverage practices' if ratio_compliant else 'Increase test code volume relative to production code'
        },
        'Assertion Density': {
            'compliant': density_compliant,
            'details': f'Average assertion density: {avg_density:.3f} (Industry standard: {STANDARDS["assertion_density"]})',
            'recommendations': 'Continue current assertion practices' if density_compliant else 'Add more assertions to improve test effectiveness'
        }
    }

    return {
        'compliance_summary': compliance_summary,
        'standards_comparison': standards_comparison,
        'action_items': action_items
    }


def generate_executive_summary_content(metrics: Dict) -> Dict:
    """Generate content for the executive summary."""
    total_tests = metrics['total_tests_classified']
    unit_pct = metrics['unit_test_percentage']
    integration_pct = metrics['integration_test_percentage']
    good_pct = metrics['good_quality_percentage']
    fair_pct = metrics['fair_quality_percentage']
    poor_pct = metrics['poor_quality_percentage']

    # Generate key findings
    key_findings = [
        f"Analyzed {metrics['total_prs']} pull requests from {len(metrics['agent_distribution'])} AI agents",
        f"Classified {total_tests} test files with {metrics['test_coverage']}% test coverage",
        f"Test type distribution: {unit_pct}% unit tests, {integration_pct}% integration tests",
        f"Quality assessment: {good_pct}% good, {fair_pct}% fair, {poor_pct}% poor quality",
        f"Identified {metrics['regression_statistics']['total']} regression tests ({metrics['regression_statistics']['bug_fix']} bug fixes, {metrics['regression_statistics']['feature']} feature tests)"
    ]

    # Generate recommendations
    areas_for_improvement = []
    if float(metrics['poor_quality_percentage']) > 20:
        areas_for_improvement.append("High proportion of poor quality tests - review and enhance test completeness")

    if float(metrics['integration_test_percentage']) < 10:
        areas_for_improvement.append("Low integration test coverage - add more comprehensive integration tests")

    if float(metrics['average_assertion_density']) < STANDARDS['assertion_density']:
        areas_for_improvement.append(f"Assertion density below standard ({metrics['average_assertion_density']})")

    if not areas_for_improvement:
        areas_for_improvement.append("Overall test quality is good - minor optimizations possible")

    priority_actions = []
    if float(metrics['poor_quality_percentage']) > 10:
        priority_actions.append(f"Priority: Improve {metrics['poor_quality_percentage']}% of poor quality tests")

    if metrics['regression_statistics']['total'] < 100:
        priority_actions.append("Increase regression test coverage for bug fixes")

    if not priority_actions:
        priority_actions.append("Maintain current testing practices while monitoring for quality degradation")

    # Generate overall assessment
    overall_assessment = f"""This analysis evaluated {total_tests} test files across {metrics['total_prs']} pull requests. The testability assessment reveals:

**Strengths:**
- Strong test coverage at {metrics['test_coverage']}%
- Well-balanced test type distribution ({unit_pct}% unit tests)
- {metrics['good_quality_percentage']}% of tests meet quality standards

**Areas for Improvement:**
- {metrics['poor_quality_percentage']}% of tests require quality enhancement
- Consider increasing integration test coverage
- Monitor assertion density to ensure test effectiveness

**Recommendations:**
{chr(10).join(f'- {action}' for action in priority_actions)}

The analysis provides a baseline for continuous improvement of AI-generated test quality."""

    return {
        'key_findings': key_findings,
        'areas_for_improvement': areas_for_improvement,
        'priority_actions': priority_actions,
        'overall_assessment': overall_assessment
    }


def generate_detailed_analysis_content(metrics: Dict) -> Dict:
    """Generate content for the detailed analysis report."""
    # Build methodology details
    methodology_details = {
        'test_detection': 'Filename patterns, directory structures, and content analysis using TestDetector component',
        'test_classification': 'Heuristic rules for categorizing test types (UNIT, INTEGRATION, REGRESSION, UNKNOWN) using TestClassifier component',
        'coverage_analysis': 'Proxy metrics including test-to-code ratio and assertion density using MetricsCalculator',
        'regression_analysis': 'Keyword matching and change correlation using RegressionAnalyzer component',
        'standards_comparison': f'Comparison against industry standards (test-to-code ratio: {STANDARDS["test_to_code_ratio"]}, assertion density: {STANDARDS["assertion_density"]})'
    }

    # Generate findings
    findings = [
        {
            'category': 'Test Type Distribution',
            'observations': [
                f"Unit tests: {metrics['unit_tests_count']} ({metrics['unit_test_percentage']}%)",
                f"Integration tests: {metrics['integration_tests_count']} ({metrics['integration_test_percentage']}%)",
                f"Total classified tests: {metrics['total_tests_classified']}"
            ]
        },
        {
            'category': 'Test Quality Assessment',
            'observations': [
                f"Good quality: {metrics['good_quality_count']} ({metrics['good_quality_percentage']}%)",
                f"Fair quality: {metrics['fair_quality_count']} ({metrics['fair_quality_percentage']}%)",
                f"Poor quality: {metrics['poor_quality_count']} ({metrics['poor_quality_percentage']}%)"
            ]
        },
        {
            'category': 'Regression Analysis',
            'observations': [
                f"Total regression tests: {metrics['regression_statistics']['total']}",
                f"Bug fix tests: {metrics['regression_statistics']['bug_fix']}",
                f"Feature tests: {metrics['regression_statistics']['feature']}"
            ]
        },
        {
            'category': 'Agent Distribution',
            'observations': [f"{agent}: {count} PRs" for agent, count in metrics['agent_distribution'].items()]
        }
    ]

    # Generate recommendations
    recommendations = [
        f"Maintain test coverage above current {metrics['test_coverage']}% level",
        f"Focus on improving {metrics['poor_quality_percentage']}% of poor quality tests",
        f"Consider increasing integration test coverage from current {metrics['integration_test_percentage']}%",
        "Monitor assertion density to ensure test effectiveness",
        "Continue tracking regression test coverage for bug fixes"
    ]

    # Generate conclusion
    total_tests = metrics['total_tests_classified']
    conclusion = f"""This detailed analysis examined {total_tests} test files across {metrics['total_prs']} pull requests. The analysis employed a comprehensive multi-stage pipeline:

1. **Test Detection**: Identified test files through pattern matching and content analysis
2. **Test Classification**: Categorized tests as UNIT, INTEGRATION, REGRESSION, or UNKNOWN
3. **Quality Assessment**: Evaluated test quality using heuristic scoring (POOR, FAIR, GOOD)
4. **Regression Analysis**: Identified regression tests for bug fixes and feature validation
5. **Standards Comparison**: Benchmarked against industry standards for test-to-code ratio and assertion density

**Key Results:**
- Test type distribution shows {metrics['unit_test_percentage']}% unit tests and {metrics['integration_test_percentage']}% integration tests
- Quality assessment reveals {metrics['good_quality_percentage']}% good, {metrics['fair_quality_percentage']}% fair, and {metrics['poor_quality_percentage']}% poor quality tests
- Aggregate test-to-code ratio: {metrics['average_test_to_code_ratio']}
- Aggregate assertion density: {metrics['average_assertion_density']}

**Conclusion:**
The AI-generated tests demonstrate strong test coverage ({metrics['test_coverage']}%) with a majority ({metrics['good_quality_percentage']}%) meeting quality standards. The primary opportunity for improvement lies in enhancing the {metrics['poor_quality_percentage']}% of tests rated as poor quality and potentially increasing integration test coverage. These findings provide a data-driven foundation for optimizing AI test generation practices."""

    return {
        'methodology_details': methodology_details,
        'findings': findings,
        'recommendations': recommendations,
        'conclusion': conclusion
    }


def generate_reports(use_cache: bool = True):
    """
    Generate comprehensive reports using the Report Generator Component.

    Args:
        use_cache: If True, try to use cached pipeline results.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting comprehensive report generation...")

    # Step 1: Run the complete analysis pipeline (or load from cache)
    logger.info(f"Step 1: Getting analysis pipeline results (use_cache={use_cache})...")
    results = get_or_run_pipeline(use_cache=use_cache)
    pr_objects = results['pr_objects']
    classified_tests = results['classified_tests']
    regression_results = results['regression_results']
    logger.info(f"Pipeline completed: {len(pr_objects)} PRs, {len(classified_tests)} classified tests, {len(regression_results)} regression tests")

    # Step 2: Extract metrics from pipeline results
    logger.info("Step 2: Extracting metrics from pipeline results...")
    metrics = extract_metrics_from_pipeline(results)

    # Step 3: Initialize the report generator
    logger.info("Step 3: Initializing Report Generator...")
    config = ReportConfig(output_dir="./reports")
    report_gen = ReportGenerator(config=config)

    # Step 4: Generate different types of reports
    logger.info("Step 4: Generating different types of reports...")

    # Generate Executive Summary
    logger.info("Generating Executive Summary...")
    exec_content = generate_executive_summary_content(metrics)
    exec_summary_report_data = ReportData(
        project_name="AIDev Testability Analysis",
        metrics={
            "total_prs": metrics['total_prs'],
            "agent_distribution": str(metrics['agent_distribution']),
            "language_distribution": str(metrics['language_distribution']),
            "coverage": metrics['test_coverage'],
            "test_count": metrics['total_tests_classified'],
            "pass_rate": metrics['pass_rate'],
            "areas_for_improvement": exec_content['areas_for_improvement'],
            "priority_actions": exec_content['priority_actions'],
            "overall_assessment": exec_content['overall_assessment']
        },
        analysis_results={"key_findings": exec_content['key_findings']},
        metadata={
            "methodology": "Complete testability analysis framework pipeline",
            "components_used": [
                "Data Loader Component",
                "Test Detector Component",
                "Test Classifier Component",
                "Coverage Analyzer Component",
                "Regression Analyzer Component",
                "Standards Comparator Component"
            ]
        }
    )

    exec_summary_path = report_gen.generate_report(
        report_type=ReportType.EXECUTIVE_SUMMARY,
        report_data=exec_summary_report_data,
        output_format=ReportFormat.MARKDOWN
    )
    logger.info(f"Executive Summary generated: {exec_summary_path}")

    # Generate Detailed Analysis
    logger.info("Generating Detailed Analysis...")
    detailed_content = generate_detailed_analysis_content(metrics)
    detailed_analysis_report_data = ReportData(
        project_name="AIDev Testability Analysis - Detailed Analysis",
        metrics={
            "total_prs": metrics['total_prs'],
            "total_tests_classified": metrics['total_tests_classified'],
            "test_coverage": metrics['test_coverage'],
            "unit_tests": f"{metrics['unit_tests_count']} ({metrics['unit_test_percentage']}%)",
            "integration_tests": f"{metrics['integration_tests_count']} ({metrics['integration_test_percentage']}%)",
            "good_quality": f"{metrics['good_quality_count']} ({metrics['good_quality_percentage']}%)",
            "fair_quality": f"{metrics['fair_quality_count']} ({metrics['fair_quality_percentage']}%)",
            "poor_quality": f"{metrics['poor_quality_count']} ({metrics['poor_quality_percentage']}%)",
            "regression_tests": metrics['regression_statistics']['total'],
            "bug_fix_tests": metrics['regression_statistics']['bug_fix'],
            "feature_tests": metrics['regression_statistics']['feature'],
            "average_test_to_code_ratio": metrics['average_test_to_code_ratio'],
            "average_assertion_density": metrics['average_assertion_density'],
            "agent_distribution": str(metrics['agent_distribution']),
            "language_distribution": str(metrics['language_distribution'])
        },
        analysis_results={
            "methodology_details": detailed_content['methodology_details'],
            "findings": detailed_content['findings'],
            "recommendations": detailed_content['recommendations']
        },
        metadata={
            "methodology": "Complete testability analysis framework pipeline",
            "components_used": [
                "Data Loader Component",
                "Test Detector Component",
                "Test Classifier Component",
                "Coverage Analyzer Component",
                "Regression Analyzer Component",
                "Standards Comparator Component"
            ],
            "conclusion": detailed_content['conclusion']
        }
    )

    detailed_analysis_path = report_gen.generate_report(
        report_type=ReportType.DETAILED_ANALYSIS,
        report_data=detailed_analysis_report_data,
        output_format=ReportFormat.MARKDOWN
    )
    logger.info(f"Detailed Analysis generated: {detailed_analysis_path}")

    # Generate Compliance Report
    logger.info("Generating Compliance Report...")
    compliance_content = generate_compliance_assessment(metrics)
    compliance_report_data = ReportData(
        project_name="AIDev Testability Analysis - Compliance Report",
        metrics={
            "total_prs": metrics['total_prs'],
            "total_tests_classified": metrics['total_tests_classified'],
            "average_test_to_code_ratio": metrics['average_test_to_code_ratio'],
            "average_assertion_density": metrics['average_assertion_density']
        },
        analysis_results={
            "standards_comparison": compliance_content['standards_comparison'],
            "compliance_summary": compliance_content['compliance_summary'],
            "action_items": compliance_content['action_items']
        },
        metadata={
            "methodology": "Complete testability analysis framework pipeline"
        }
    )

    compliance_report_path = report_gen.generate_report(
        report_type=ReportType.COMPLIANCE_REPORT,
        report_data=compliance_report_data,
        output_format=ReportFormat.MARKDOWN
    )
    logger.info(f"Compliance Report generated: {compliance_report_path}")

    # Generate Metrics Overview
    logger.info("Generating Metrics Overview...")
    metrics_overview_report_data = ReportData(
        project_name="AIDev Testability Analysis - Metrics Overview",
        metrics={
            "total_prs": metrics['total_prs'],
            "total_tests_classified": metrics['total_tests_classified'],
            "total_regression_tests": metrics['total_regression_tests'],
            "test_coverage_percentage": metrics['test_coverage'],
            "pass_rate_percentage": metrics['pass_rate'],
            "average_test_to_code_ratio": metrics['average_test_to_code_ratio'],
            "average_assertion_density": metrics['average_assertion_density'],
            "test_type_distribution_UNIT": metrics['test_type_distribution'].get('UNIT', 0),
            "test_type_distribution_INTEGRATION": metrics['test_type_distribution'].get('INTEGRATION', 0),
            "test_type_distribution_UNKNOWN": metrics['test_type_distribution'].get('UNKNOWN', 0),
            "quality_distribution_GOOD": metrics['quality_distribution'].get('GOOD', 0),
            "quality_distribution_FAIR": metrics['quality_distribution'].get('FAIR', 0),
            "quality_distribution_POOR": metrics['quality_distribution'].get('POOR', 0),
            "regression_bug_fix_count": metrics['regression_statistics']['bug_fix'],
            "regression_feature_count": metrics['regression_statistics']['feature'],
            "agent_distribution": str(metrics['agent_distribution']),
            "language_distribution": str(metrics['language_distribution'])
        },
        analysis_results={},
        metadata={
            "methodology": "Complete testability analysis framework pipeline",
            "components_used": [
                "Data Loader Component",
                "Test Detector Component",
                "Test Classifier Component",
                "Coverage Analyzer Component",
                "Regression Analyzer Component",
                "Standards Comparator Component"
            ]
        }
    )

    metrics_overview_path = report_gen.generate_report(
        report_type=ReportType.METRICS_OVERVIEW,
        report_data=metrics_overview_report_data,
        output_format=ReportFormat.MARKDOWN
    )
    logger.info(f"Metrics Overview generated: {metrics_overview_path}")

    # Print summary
    print("\n" + "="*60)
    print("REPORT GENERATION SUMMARY")
    print("="*60)
    print(f"Total PRs analyzed: {metrics['total_prs']}")
    print(f"Tests classified: {metrics['total_tests_classified']}")
    print(f"Test coverage: {metrics['test_coverage']}%")
    print(f"Pass rate: {metrics['pass_rate']}%")
    print(f"Reports generated: 4 types")
    print(f"Output format: Markdown")
    print(f"Output directory: ./reports/")
    print("\nReports created:")
    print(f"  - Executive Summary: {exec_summary_path}")
    print(f"  - Detailed Analysis: {detailed_analysis_path}")
    print(f"  - Compliance Report: {compliance_report_path}")
    print(f"  - Metrics Overview: {metrics_overview_path}")
    print("="*60)

    return {
        "executive_summary_path": exec_summary_path,
        "detailed_analysis_path": detailed_analysis_path,
        "compliance_report_path": compliance_report_path,
        "metrics_overview_path": metrics_overview_path
    }


def main():
    """Main function to run the report generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate comprehensive reports from testability analysis pipeline data.'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Force re-running the pipeline instead of using cached results'
    )

    args = parser.parse_args()

    print("Generating comprehensive reports using the Report Generator Component...\n")

    # Set up logging
    setup_logging()

    try:
        # Generate the reports
        report_paths = generate_reports(use_cache=not args.no_cache)

        print("\n✓ Comprehensive reports generated successfully!")
        print("Reports saved in the './reports/' directory")

        print("\nNext steps:")
        print("- Review the generated reports for accuracy and completeness")
        print("- Create visualizations highlighting key findings")
        print("- Use insights to guide improvements in AI test generation")

        return 0

    except Exception as e:
        print(f"\n✗ Error generating reports: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
