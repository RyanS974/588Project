"""
Constants for the Visualizer Component
Defines chart types, export formats, and other visualization constants
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


class ChartType(Enum):
    """Enumeration of supported chart types"""
    BAR = "bar"
    PIE = "pie"
    LINE = "line"
    SCATTER = "scatter"


class ExportFormat(Enum):
    """Enumeration of supported export formats"""
    PNG = "png"
    PDF = "pdf"
    SVG = "svg"


@dataclass
class ChartConfig:
    """Configuration for chart appearance"""
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    figsize: tuple = (10, 6)
    dpi: int = 300
    color_palette: Optional[List[str]] = None


@dataclass
class VisualizationData:
    """Data structure for visualization input"""
    labels: List[str]
    values: List[float]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if len(self.labels) != len(self.values):
            raise ValueError("Labels and values must have the same length")