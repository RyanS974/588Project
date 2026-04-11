# Testability Analysis - Distribution

This is a minimal distribution of the Testability Analysis framework, designed to evaluate the testability of AI-generated code changes (PRs) in software engineering contexts.

## Setup

### 1. Prerequisites
- Python 3.8+
- pip (package manager)

### 2. Create a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

The distribution includes scripts to set up the dataset, run the analysis pipeline, and generate reports.

### 1. Set Up the Dataset
You can load the actual AIDev dataset from Hugging Face or use sample data for quick testing.

**For full analysis (requires internet):**
```bash
python scripts/setup_aidv_dataset.py
```

**For a quick test (uses local sample data):**
```bash
python scripts/setup_aidv_dataset.py --use-sample
```

### 2. Run the Analysis Pipeline
Execute the complete testability analysis on the loaded dataset.
```bash
python scripts/run_analysis_pipeline.py
```

### 3. Generate Reports & Visualizations
After the pipeline completes, you can generate markdown reports and visualizations.

**Generate Reports:**
```bash
python scripts/generate_reports.py
```

**Generate Visualizations:**
```bash
python scripts/generate_comprehensive_visualizations.py
```

## Directory Structure
- `src/`: Core application logic and components.
- `scripts/`: Execution scripts for data setup, pipeline runs, and reporting.
- `config/`: Configuration files for industry standards.
- `data/`: (Generated) Raw and processed dataset files.
- `reports/`: (Generated) Detailed analysis and compliance reports.
- `visualizations/`: (Generated) Charts and visual metrics.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

<br>