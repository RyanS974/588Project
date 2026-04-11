"""
Main visualization manager for the Visualizer Component
Handles chart generation and export functionality
"""
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any, List, Optional
from .constants import ChartType, ExportFormat, ChartConfig, VisualizationData
from .exceptions import ChartGenerationError, InvalidDataError, UnsupportedFormatError


class VisualizationManager:
    """
    Main class for managing visualization operations
    """
    
    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the VisualizationManager
        
        Args:
            output_dir: Directory to save generated visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Register chart generators
        self._chart_generators = {
            ChartType.BAR: self._generate_bar_chart,
            ChartType.PIE: self._generate_pie_chart,
            ChartType.LINE: self._generate_line_chart,
            ChartType.SCATTER: self._generate_scatter_plot
        }
    
    def create_chart(
        self,
        chart_type: ChartType,
        data: VisualizationData,
        config: Optional[ChartConfig] = None,
        filename: Optional[str] = None,
        export_format: ExportFormat = ExportFormat.PNG
    ) -> str:
        """
        Create a chart of the specified type
        
        Args:
            chart_type: Type of chart to create
            data: Visualization data to plot
            config: Chart configuration options
            filename: Name for the output file (without extension)
            export_format: Format to save the chart in
            
        Returns:
            Path to the saved chart file
        """
        if chart_type not in self._chart_generators:
            raise UnsupportedFormatError(f"Unsupported chart type: {chart_type}")
        
        if config is None:
            config = ChartConfig()
        
        # Generate the chart
        fig, ax = plt.subplots(figsize=config.figsize)
        self._chart_generators[chart_type](ax, data, config)
        
        # Apply configuration
        if config.title:
            ax.set_title(config.title)
        if config.xlabel:
            ax.set_xlabel(config.xlabel)
        if config.ylabel:
            ax.set_ylabel(config.ylabel)
        
        # Save the chart
        if filename is None:
            filename = f"chart_{chart_type.value}"
        
        filepath = self.output_dir / f"{filename}.{export_format.value}"
        fig.savefig(filepath, dpi=config.dpi, bbox_inches='tight')
        plt.close(fig)
        
        return str(filepath)
    
    def _generate_bar_chart(self, ax, data: VisualizationData, config: ChartConfig):
        """Generate a bar chart"""
        try:
            bars = ax.bar(data.labels, data.values)
            ax.bar_label(bars, fmt='%.2f')
        except Exception as e:
            raise ChartGenerationError(f"Failed to generate bar chart: {str(e)}")
    
    def _generate_pie_chart(self, ax, data: VisualizationData, config: ChartConfig):
        """Generate a pie chart"""
        try:
            ax.pie(
                data.values,
                labels=data.labels,
                autopct='%1.1f%%',
                startangle=90
            )
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        except Exception as e:
            raise ChartGenerationError(f"Failed to generate pie chart: {str(e)}")
    
    def _generate_line_chart(self, ax, data: VisualizationData, config: ChartConfig):
        """Generate a line chart"""
        try:
            ax.plot(data.labels, data.values, marker='o')
        except Exception as e:
            raise ChartGenerationError(f"Failed to generate line chart: {str(e)}")
    
    def _generate_scatter_plot(self, ax, data: VisualizationData, config: ChartConfig):
        """Generate a scatter plot"""
        try:
            # For scatter plots, we need numeric x values
            x_values = range(len(data.labels))
            ax.scatter(x_values, data.values)
            ax.set_xticks(x_values)
            ax.set_xticklabels(data.labels, rotation=45, ha="right")
        except Exception as e:
            raise ChartGenerationError(f"Failed to generate scatter plot: {str(e)}")
    
    def export_chart_from_data(
        self,
        chart_type: ChartType,
        data: VisualizationData,
        config: ChartConfig,
        export_format: ExportFormat,
        output_filename: str
    ) -> str:
        """
        Export a chart directly from data in the specified format
        
        Args:
            chart_type: Type of chart to create
            data: Visualization data to plot
            config: Chart configuration options
            export_format: Desired export format
            output_filename: Name for the output file (without extension)
            
        Returns:
            Path to the exported chart file
        """
        if chart_type not in self._chart_generators:
            raise UnsupportedFormatError(f"Unsupported chart type: {chart_type}")
        
        # Generate the chart
        fig, ax = plt.subplots(figsize=config.figsize)
        self._chart_generators[chart_type](ax, data, config)
        
        # Apply configuration
        if config.title:
            ax.set_title(config.title)
        if config.xlabel:
            ax.set_xlabel(config.xlabel)
        if config.ylabel:
            ax.set_ylabel(config.ylabel)
        
        output_path = self.output_dir / f"{output_filename}.{export_format.value}"
        fig.savefig(output_path, dpi=config.dpi, bbox_inches='tight')
        plt.close(fig)
        
        return str(output_path)
    
    def export_to_format(
        self,
        source_path: str,
        export_format: ExportFormat,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Convert an existing chart to a different format.
        
        Args:
            source_path: Path to the source chart file
            export_format: Desired export format
            output_filename: Name for the output file (without extension)
            
        Returns:
            Path to the converted chart file
        """
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source chart file not found: {source_path}")
        
        if output_filename is None:
            output_filename = source_path.stem
        
        output_path = self.output_dir / f"{output_filename}.{export_format.value}"
        
        # Copy the file to the new format
        import shutil
        shutil.copy(source_path, output_path)
        
        return str(output_path)