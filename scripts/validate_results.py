#!/usr/bin/env python3
"""
Script to collect and validate results from the testability analysis framework.

This script will:
1. Gather all outputs from the analysis components
2. Validate the completeness and correctness of the results
3. Cross-reference reports and visualizations
4. Generate a validation summary
"""

import os
import sys
from pathlib import Path
import logging
import json
from datetime import datetime

# Add the project root to the path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import AIDevDataLoader
from src.data_loader.schema_definitions import DataLoaderConfig


def setup_logging():
    """Set up logging for the validation process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - '
               '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        handlers=[
            logging.FileHandler('validation_summary.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def collect_and_validate_results():
    """Collect and validate all results from the analysis framework."""
    logger = logging.getLogger(__name__)
    logger.info("Starting collection and validation of results...")
    
    # Step 1: Load the dataset to establish baseline
    logger.info("Step 1: Loading AIDev dataset...")
    config = DataLoaderConfig(data_directory="./data/raw")
    data_loader = AIDevDataLoader(config)
    pr_objects = data_loader.run()
    logger.info(f"Loaded {len(pr_objects)} PullRequest objects")
    
    # Step 2: Validate reports directory
    logger.info("Step 2: Validating reports...")
    reports_dir = Path("./reports")
    if not reports_dir.exists():
        logger.warning(f"Reports directory does not exist: {reports_dir}")
        report_files = []
    else:
        report_files = list(reports_dir.glob("*.markdown")) + list(reports_dir.glob("*.json"))
        logger.info(f"Found {len(report_files)} report files")
    
    # Step 3: Validate visualizations directory
    logger.info("Step 3: Validating visualizations...")
    viz_dir = Path("./visualizations")
    if not viz_dir.exists():
        logger.warning(f"Visualizations directory does not exist: {viz_dir}")
        viz_files = []
    else:
        viz_files = list(viz_dir.glob("*.png"))
        logger.info(f"Found {len(viz_files)} visualization files")
    
    # Step 4: Check for expected report types
    logger.info("Step 4: Checking for expected report types...")
    expected_reports = {
        'executive_summary': False,
        'detailed_analysis': False,
        'compliance_report': False,
        'metrics_overview': False
    }
    
    for report_file in report_files:
        report_name = report_file.name.lower()
        if 'executive_summary' in report_name:
            expected_reports['executive_summary'] = True
        elif 'detailed_analysis' in report_name:
            expected_reports['detailed_analysis'] = True
        elif 'compliance_report' in report_name:
            expected_reports['compliance_report'] = True
        elif 'metrics_overview' in report_name:
            expected_reports['metrics_overview'] = True
    
    # Step 5: Check for expected visualization types
    logger.info("Step 5: Checking for expected visualization types...")
    expected_viz = {
        'ai_test_metrics': False,
        'human_test_metrics': False,
        'agent_distribution': False,
        'test_code_ratio': False,
        'metrics_trend': False
    }
    
    for viz_file in viz_files:
        viz_name = viz_file.name.lower()
        if 'ai_test_metrics' in viz_name:
            expected_viz['ai_test_metrics'] = True
        elif 'human_test_metrics' in viz_name:
            expected_viz['human_test_metrics'] = True
        elif 'agent_distribution' in viz_name:
            expected_viz['agent_distribution'] = True
        elif 'test_code_ratio' in viz_name:
            expected_viz['test_code_ratio'] = True
        elif 'metrics_trend' in viz_name:
            expected_viz['metrics_trend'] = True
    
    # Step 6: Validate content of reports
    logger.info("Step 6: Validating content of reports...")
    report_validation_results = []
    
    for report_file in report_files:
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic validation checks
            has_title = '# ' in content or 'title:' in content
            has_metrics = any(word in content.lower() for word in ['metrics', 'coverage', 'test', 'quality'])
            has_date = any(word in content for word in [datetime.now().strftime('%Y'), datetime.now().strftime('%Y-%m')])
            
            validation_result = {
                'file': str(report_file),
                'valid': has_title and has_metrics,
                'checks': {
                    'has_title': has_title,
                    'has_metrics': has_metrics,
                    'has_date': has_date
                }
            }
            report_validation_results.append(validation_result)
            
        except Exception as e:
            logger.error(f"Error validating report {report_file}: {e}")
            report_validation_results.append({
                'file': str(report_file),
                'valid': False,
                'checks': {},
                'error': str(e)
            })
    
    # Step 7: Validate content of visualizations
    logger.info("Step 7: Validating content of visualizations...")
    viz_validation_results = []
    
    for viz_file in viz_files:
        try:
            # Check if file exists and has non-zero size
            file_size = viz_file.stat().st_size
            is_valid_image = file_size > 0
            
            validation_result = {
                'file': str(viz_file),
                'valid': is_valid_image,
                'size': file_size
            }
            viz_validation_results.append(validation_result)
            
        except Exception as e:
            logger.error(f"Error validating visualization {viz_file}: {e}")
            viz_validation_results.append({
                'file': str(viz_file),
                'valid': False,
                'error': str(e)
            })
    
    # Step 8: Generate validation summary
    logger.info("Step 8: Generating validation summary...")
    
    all_reports_valid = all(result['valid'] for result in report_validation_results)
    all_viz_valid = all(result['valid'] for result in viz_validation_results)
    
    missing_reports = [k for k, v in expected_reports.items() if not v]
    missing_viz = [k for k, v in expected_viz.items() if not v]
    
    summary = {
        "validation_date": datetime.now().isoformat(),
        "dataset_info": {
            "total_prs": len(pr_objects),
            "agents_found": list(set(pr.agent.name for pr in pr_objects))
        },
        "reports": {
            "total_found": len(report_files),
            "expected_types_found": dict(expected_reports),
            "missing_types": missing_reports,
            "all_valid": all_reports_valid,
            "details": report_validation_results
        },
        "visualizations": {
            "total_found": len(viz_files),
            "expected_types_found": dict(expected_viz),
            "missing_types": missing_viz,
            "all_valid": all_viz_valid,
            "details": viz_validation_results
        },
        "overall_status": all_reports_valid and all_viz_valid and not missing_reports and not missing_viz
    }
    
    # Save validation summary
    summary_path = Path("./validation_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Validation summary saved to {summary_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Dataset PRs analyzed: {len(pr_objects)}")
    print(f"Reports generated: {len(report_files)}")
    print(f"Visualizations generated: {len(viz_files)}")
    print(f"All reports valid: {all_reports_valid}")
    print(f"All visualizations valid: {all_viz_valid}")
    print(f"Missing report types: {missing_reports}")
    print(f"Missing visualization types: {missing_viz}")
    print(f"Overall status: {'✓ PASS' if summary['overall_status'] else '✗ FAIL'}")
    
    print("\nReport Validation Details:")
    for result in report_validation_results:
        status = "✓" if result['valid'] else "✗"
        print(f"  {status} {Path(result['file']).name}")
    
    print("\nVisualization Validation Details:")
    for result in viz_validation_results:
        status = "✓" if result['valid'] else "✗"
        print(f"  {status} {Path(result['file']).name}")
    
    print("="*60)
    
    return summary


def main():
    """Main function to run the validation process."""
    print("Collecting and validating results from the testability analysis framework...\n")
    
    # Set up logging
    setup_logging()
    
    try:
        # Run the validation process
        validation_summary = collect_and_validate_results()
        
        print("\n✓ Collection and validation completed successfully!")
        
        if validation_summary['overall_status']:
            print("✓ All components validated successfully!")
        else:
            print("⚠ Some components require attention (see validation details above)")
        
        print("\nNext step:")
        print("- Document findings and insights")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())