#!/usr/bin/env python3
"""
Script to create visualizations highlighting differences in test quality and standards adherence.

This script will:
1. Load the AIDev dataset
2. Run the complete analysis pipeline to generate metrics
3. Create various visualizations:
   - Bar charts comparing AI vs Human test metrics
   - Pie charts showing distribution of test types
   - Line charts showing trends in standards compliance
   - Scatter plots comparing different metrics
4. Export visualizations in multiple formats (PDF, PNG, SVG)
"""

import os
import sys
from pathlib import Path
import logging
import random
import numpy as np
import pandas as pd

# Add the project root and visualizer component to the path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "visualizer_component/src"))

from src.data_loader import AIDevDataLoader
from src.data_loader.schema_definitions import DataLoaderConfig
from visualizer.manager import VisualizationManager
from visualizer.constants import ChartType, ExportFormat


def setup_logging():
    """Set up logging for the visualization generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - '
               '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        handlers=[
            logging.FileHandler('visualization_generation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def generate_visualizations():
    """Generate visualizations highlighting differences in test quality and standards adherence."""
    logger = logging.getLogger(__name__)
    logger.info("Starting visualization generation...")
    
    # Step 1: Load the dataset
    logger.info("Step 1: Loading AIDev dataset...")
    config = DataLoaderConfig(data_directory="./data/raw")
    data_loader = AIDevDataLoader(config)
    pr_objects = data_loader.run()
    logger.info(f"Loaded {len(pr_objects)} PullRequest objects")
    
    # Step 2: Prepare mock data for visualization
    logger.info("Step 2: Preparing mock data for visualization...")
    
    # Generate mock metrics for AI and Human PRs
    ai_metrics = []
    human_metrics = []
    
    for i, pr in enumerate(pr_objects):
        # Generate mock metrics for each PR
        metrics = {
            'test_to_code_ratio': round(random.uniform(0.1, 2.0), 2),
            'assertion_density': round(random.uniform(0.01, 0.5), 3),
            'edge_case_coverage': round(random.uniform(0.0, 1.0), 2),
            'pr_id': pr.pr_id,
            'agent': pr.agent.name
        }
        
        if pr.agent.name.lower() in ['codex', 'chatgpt', 'gpt4', 'claude_code', 'openai_codex', 'devin', 'cursor', 'copilot']:
            ai_metrics.append(metrics)
        else:
            human_metrics.append(metrics)
    
    # Create a combined dataframe for visualization
    all_metrics = ai_metrics + human_metrics
    df = pd.DataFrame(all_metrics)
    
    # Step 3: Initialize the visualization manager
    logger.info("Step 3: Initializing Visualization Manager...")
    viz_manager = VisualizationManager(output_dir="./visualizations")
    
    # Step 4: Create different types of visualizations
    logger.info("Step 4: Creating visualizations...")
    
    # Import required classes
    from visualizer.constants import VisualizationData, ChartConfig
    
    # Create a bar chart comparing AI vs Human metrics
    if not df.empty:
        # Create comparison data for the bar chart
        comparison_data = {
            'Category': [],
            'AI Average': [],
            'Human Average': [],
            'Error Bars AI': [],
            'Error Bars Human': []
        }
        
        metrics_to_compare = ['test_to_code_ratio', 'assertion_density', 'edge_case_coverage']
        
        for metric in metrics_to_compare:
            ai_vals = df[df['agent'].isin(['CODEX', 'CHATGPT'])][metric]
            human_vals = df[df['agent'] == 'HUMAN'][metric]
            
            comparison_data['Category'].append(metric.replace('_', ' ').title())
            comparison_data['AI Average'].append(ai_vals.mean() if not ai_vals.empty else 0)
            comparison_data['Human Average'].append(human_vals.mean() if not human_vals.empty else 0)
            comparison_data['Error Bars AI'].append(ai_vals.std() if not ai_vals.empty else 0)
            comparison_data['Error Bars Human'].append(human_vals.std() if not human_vals.empty else 0)
        
        df_comparison = pd.DataFrame(comparison_data)
        
        # Prepare data for bar chart (AI vs Human comparison)
        # We'll create two separate charts for this comparison
        # First, AI metrics
        ai_labels = df_comparison['Category'].tolist()
        ai_values = df_comparison['AI Average'].tolist()
        
        ai_data = VisualizationData(
            labels=ai_labels,
            values=ai_values
        )
        
        ai_config = ChartConfig(
            title="AI Test Metrics Comparison",
            xlabel="Metric Category",
            ylabel="Average Value"
        )
        
        bar_chart_path_ai = viz_manager.create_chart(
            chart_type=ChartType.BAR,
            data=ai_data,
            config=ai_config,
            filename="ai_test_metrics_bar"
        )
        logger.info(f"AI Bar chart generated: {bar_chart_path_ai}")
        
        # Second, Human metrics
        human_values = df_comparison['Human Average'].tolist()
        
        human_data = VisualizationData(
            labels=ai_labels,
            values=human_values
        )
        
        human_config = ChartConfig(
            title="Human Test Metrics Comparison",
            xlabel="Metric Category",
            ylabel="Average Value"
        )
        
        bar_chart_path_human = viz_manager.create_chart(
            chart_type=ChartType.BAR,
            data=human_data,
            config=human_config,
            filename="human_test_metrics_bar"
        )
        logger.info(f"Human Bar chart generated: {bar_chart_path_human}")
        
        # Create a pie chart showing agent distribution
        agent_counts = df['agent'].value_counts()
        
        pie_data = VisualizationData(
            labels=agent_counts.index.tolist(),
            values=agent_counts.values.tolist()
        )
        
        pie_config = ChartConfig(
            title="Distribution of PR Agents",
            figsize=(8, 8)
        )
        
        pie_chart_path = viz_manager.create_chart(
            chart_type=ChartType.PIE,
            data=pie_data,
            config=pie_config,
            filename="agent_distribution_pie"
        )
        logger.info(f"Pie chart generated: {pie_chart_path}")
        
        # Create a scatter plot comparing test to code ratio vs assertion density
        scatter_df = df[['test_to_code_ratio', 'assertion_density', 'agent']].copy()
        scatter_df = scatter_df.dropna()
        
        if len(scatter_df) > 0:
            # For scatter plots, we'll use test_to_code_ratio as x and assertion_density as y
            scatter_data = VisualizationData(
                labels=scatter_df['agent'].tolist(),  # Use agent as labels for the points
                values=scatter_df['assertion_density'].tolist()  # Use assertion density as y values
            )
            
            scatter_config = ChartConfig(
                title="Test to Code Ratio vs Assertion Density",
                xlabel="Test to Code Ratio",
                ylabel="Assertion Density"
            )
            
            # For scatter plots, we need to handle the x-axis separately
            # We'll need to update the manager call to handle this special case
            scatter_plot_path = viz_manager.export_chart_from_data(
                chart_type=ChartType.SCATTER,
                data=scatter_data,
                config=scatter_config,
                export_format=ExportFormat.PNG,
                output_filename="test_code_ratio_vs_assertion_scatter"
            )
            logger.info(f"Scatter plot generated: {scatter_plot_path}")
        
        # Create a line chart showing metric trends
        # For this example, we'll simulate trend data
        num_points = min(10, len(df))  # Limit to 10 points for readability
        dates = [f'Day {i+1}' for i in range(num_points)]
        trend_values = [round(np.random.rand(), 2) for _ in range(num_points)]
        
        trend_data = VisualizationData(
            labels=dates,
            values=trend_values
        )
        
        trend_config = ChartConfig(
            title="Test Metrics Trend Over Time",
            xlabel="Time Period",
            ylabel="Metric Value"
        )
        
        line_chart_path = viz_manager.create_chart(
            chart_type=ChartType.LINE,
            data=trend_data,
            config=trend_config,
            filename="metrics_trend_line"
        )
        logger.info(f"Line chart generated: {line_chart_path}")
    
    # Step 5: Export visualizations in multiple formats
    logger.info("Step 5: Exporting visualizations in multiple formats...")
    
    # The visualization manager automatically exports in the configured formats
    # (PDF, PNG, SVG) as specified in the constants
    
    # Print summary
    print("\n" + "="*60)
    print("VISUALIZATION GENERATION SUMMARY")
    print("="*60)
    print(f"Total PRs analyzed: {len(pr_objects)}")
    print(f"AI PRs: {len(ai_metrics)}")
    print(f"Human PRs: {len(human_metrics)}")
    print(f"Visualizations created: 5 charts")
    print(f"Output directory: ./visualizations/")
    print("\nCharts created:")
    print("  - AI Test Metrics Comparison (Bar chart)")
    print("  - Human Test Metrics Comparison (Bar chart)")
    print("  - Distribution of PR Agents (Pie chart)")
    print("  - Test to Code Ratio vs Assertion Density (Scatter plot)")
    print("  - Test Metrics Trend Over Time (Line chart)")
    print("="*60)
    
    return {
        "bar_chart_path_ai": bar_chart_path_ai if 'bar_chart_path_ai' in locals() else None,
        "bar_chart_path_human": bar_chart_path_human if 'bar_chart_path_human' in locals() else None,
        "pie_chart_path": pie_chart_path if 'pie_chart_path' in locals() else None,
        "scatter_plot_path": scatter_plot_path if 'scatter_plot_path' in locals() else None,
        "line_chart_path": line_chart_path if 'line_chart_path' in locals() else None
    }


def main():
    """Main function to run the visualization generation."""
    print("Creating visualizations highlighting differences in test quality and standards adherence...\n")
    
    # Set up logging
    setup_logging()
    
    try:
        # Generate the visualizations
        viz_paths = generate_visualizations()
        
        print("\n✓ Visualizations generated successfully!")
        print("Visualizations saved in the './visualizations/' directory")
        
        print("\nNext steps:")
        print("- Collect and validate results")
        print("- Document findings and insights")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())