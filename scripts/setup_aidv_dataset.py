#!/usr/bin/env python3
"""
Script to prepare the AIDev dataset for analysis.

This script will:
1. Create the necessary directory structure
2. Download the AIDev dataset from Hugging Face (or create sample data)
3. Set up the dataset in the correct format for our analysis pipeline
4. Verify the dataset integrity

Usage:
    python scripts/setup_aidv_dataset.py              # Load real AIDev dataset
    python scripts/setup_aidv_dataset.py --use-sample # Use sample data for testing
"""

import argparse
import os
import sys
from pathlib import Path
import pandas as pd

# Add the project root to the path to enable imports
# __file__ is in scripts/, so parent.parent gives us the project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import AIDevDataLoader
from src.data_loader.schema_definitions import DataLoaderConfig


def create_directories():
    """Create the necessary directory structure for the dataset."""
    data_dir = Path("./data/raw")
    processed_dir = Path("./data/processed")
    
    data_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created directory structure:")
    print(f"- {data_dir}")
    print(f"- {processed_dir}")


def setup_sample_data():
    """Create sample data files that match the expected schema for testing purposes."""
    raw_dir = Path("./data/raw")

    # Create sample pull_request.csv
    pull_request_data = pd.DataFrame({
        "pr_id": ["1", "2", "3", "4"],
        "repository_id": ["repo1", "repo2", "repo1", "repo3"],
        "agent": ["codex", "human", "chatgpt", "human"],
        "status": ["merged", "closed", "merged", "merged"],
        "created_at": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "title": ["Add feature X", "Fix bug Y", "Update docs", "Refactor Z"],
        "description": ["Added new feature X", "Fixed critical bug Y", "Updated documentation", "Refactored module Z"]
    })
    pull_request_data.to_csv(raw_dir / "pull_request.csv", index=False)

    # Create sample pr_commit_details.csv
    commit_details_data = pd.DataFrame({
        "sha": ["c1", "c2", "c3", "c4", "c5"],
        "pr_id": ["1", "1", "2", "3", "4"],
        "file_path": ["src/main.py", "tests/test_main.py", "src/utils.py", "docs/readme.md", "src/refactor.py"],
        "additions": [50, 30, 20, 15, 60],
        "deletions": [10, 5, 0, 5, 20],
        "message": ["Add feature X", "Add tests for feature X", "Fix bug in utils", "Update documentation", "Refactor module"],
        "patch": [
            "@@ -0,0 +1,50 @@\n+def feature_x():\n+    pass",
            "@@ -0,0 +1,30 @@\n+def test_feature_x():\n+    assert True",
            "@@ -10,1 +10,1 @@\n-old_bug\n+fixed_bug",
            "@@ -1,1 +1,1 @@\n-old docs\n+new docs",
            "@@ -1,60 +1,60 @@\n+new_refactored_code"
        ],
        "language": ["python", "python", "python", "markdown", "python"]
    })
    commit_details_data.to_csv(raw_dir / "pr_commit_details.csv", index=False)

    # Create sample repository.csv
    repo_data = pd.DataFrame({
        "repository_id": ["repo1", "repo2", "repo3"],
        "language": ["python", "java", "python"],
        "stars": [100, 250, 75]
    })
    repo_data.to_csv(raw_dir / "repository.csv", index=False)

    print(f"Created sample dataset files in {raw_dir}/:")
    print("- pull_request.csv")
    print("- pr_commit_details.csv")
    print("- repository.csv")


def load_aidev_dataset_from_huggingface():
    """Load actual AIDev dataset from Hugging Face.

    This loads the full AIDev dataset and saves it as CSV files for
    faster subsequent access. The dataset is hosted at:
    https://huggingface.co/datasets/hao-li/AIDev

    Returns:
        bool: True if successful, False otherwise.
    """
    raw_dir = Path("./data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("Loading AIDev dataset from Hugging Face...")
    print("Source: https://huggingface.co/datasets/hao-li/AIDev")
    print()

    try:
        # Check if pyarrow is available (required for parquet reading via hf://)
        try:
            import pyarrow
        except ImportError:
            print("✗ Error: pyarrow is required to read parquet files.")
            print("  Install with: pip install pyarrow")
            return False

        # Load the three essential tables directly from Hugging Face
        # Note: Using AIDev-pop subset (filtered >100 stars) for pull_request and repository
        # pr_commit_details is the full dataset but we'll filter by PR
        print("Loading pull_request table (AIDev-pop subset)...")
        pr_df = pd.read_parquet("hf://datasets/hao-li/AIDev/pull_request.parquet")
        print(f"  ✓ Loaded {len(pr_df):,} pull requests")

        print("Loading repository table (AIDev-pop subset)...")
        repo_df = pd.read_parquet("hf://datasets/hao-li/AIDev/repository.parquet")
        print(f"  ✓ Loaded {len(repo_df):,} repositories")

        print("Loading pr_commit_details table...")
        commit_details_df = pd.read_parquet("hf://datasets/hao-li/AIDev/pr_commit_details.parquet")
        print(f"  ✓ Loaded {len(commit_details_df):,} commit details")

        # Print column names for verification
        print()
        print("=" * 60)
        print("COLUMN NAMES (for verification)")
        print("=" * 60)
        print(f"\npull_request columns: {list(pr_df.columns)}")
        print(f"repository columns: {list(repo_df.columns)}")
        print(f"pr_commit_details columns: {list(commit_details_df.columns)}")

        # Rename columns to match our expected schema
        print()
        print("Renaming columns to match our schema...")

        # pull_request: id -> pr_id, repo_id -> repository_id, state -> status
        pr_column_map = {
            'id': 'pr_id',
            'repo_id': 'repository_id',
            'state': 'status'
        }
        pr_df = pr_df.rename(columns=pr_column_map)
        print(f"  ✓ Renamed pull_request columns: {pr_column_map}")

        # repository: id -> repository_id
        repo_column_map = {
            'id': 'repository_id'
        }
        repo_df = repo_df.rename(columns=repo_column_map)
        print(f"  ✓ Renamed repository columns: {repo_column_map}")

        # pr_commit_details: filename -> file_path
        commit_column_map = {
            'filename': 'file_path'
        }
        commit_details_df = commit_details_df.rename(columns=commit_column_map)
        print(f"  ✓ Renamed pr_commit_details columns: {commit_column_map}")

        print()
        print("Saving to local CSV files for faster subsequent access...")

        # Save to local files
        pr_df.to_csv(raw_dir / "pull_request.csv", index=False)
        print(f"  ✓ Saved pull_request.csv ({len(pr_df):,} rows)")

        repo_df.to_csv(raw_dir / "repository.csv", index=False)
        print(f"  ✓ Saved repository.csv ({len(repo_df):,} rows)")

        commit_details_df.to_csv(raw_dir / "pr_commit_details.csv", index=False)
        print(f"  ✓ Saved pr_commit_details.csv ({len(commit_details_df):,} rows)")

        print()
        print("=" * 60)
        print("DATASET SUMMARY")
        print("=" * 60)

        # Show agent distribution
        if 'agent' in pr_df.columns:
            print("\nAgent Distribution:")
            agent_counts = pr_df['agent'].value_counts()
            for agent, count in agent_counts.items():
                print(f"  - {agent}: {count:,} ({count/len(pr_df)*100:.1f}%)")
        else:
            print("\n⚠ Warning: 'agent' column not found in pull_request table!")
            print("  Available columns:", list(pr_df.columns))

        # Show language distribution
        if 'language' in repo_df.columns:
            print("\nLanguage Distribution (in repositories):")
            lang_counts = repo_df['language'].value_counts().head(10)
            for lang, count in lang_counts.items():
                print(f"  - {lang}: {count:,}")

        # Show repository star distribution
        if 'stars' in repo_df.columns:
            print("\nRepository Star Distribution:")
            print(f"  - Mean: {repo_df['stars'].mean():.0f}")
            print(f"  - Median: {repo_df['stars'].median():.0f}")
            print(f"  - Max: {repo_df['stars'].max():,}")
            print(f"  - Repos with ≥100 stars: {(repo_df['stars'] >= 100).sum():,}")
            print(f"  - Repos with ≥500 stars: {(repo_df['stars'] >= 500).sum():,}")

        print()
        print("=" * 60)
        print("✓ AIDev dataset loaded successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ Error loading AIDev dataset: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_loading():
    """Test that the data loader can successfully load the prepared dataset."""
    config = DataLoaderConfig(data_directory="./data/raw")
    loader = AIDevDataLoader(config)
    
    try:
        pr_objects = loader.run()
        print(f"\n✓ Successfully loaded {len(pr_objects)} PullRequest objects")
        
        # Print summary statistics
        ai_prs = [pr for pr in pr_objects if pr.agent.name.lower() in ['codex', 'chatgpt']]
        human_prs = [pr for pr in pr_objects if pr.agent.name.lower() == 'human']
        
        print(f"- AI-generated PRs: {len(ai_prs)}")
        print(f"- Human-generated PRs: {len(human_prs)}")
        
        languages = set(pr.language for pr in pr_objects)
        print(f"- Languages in dataset: {languages}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error loading dataset: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to orchestrate the dataset preparation."""
    parser = argparse.ArgumentParser(
        description="Prepare the AIDev dataset for analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_aidv_dataset.py              # Load real AIDev dataset from HuggingFace
  python scripts/setup_aidv_dataset.py --use-sample # Use sample data for testing
        """
    )
    parser.add_argument(
        "--use-sample",
        action="store_true",
        help="Use sample data instead of loading the full AIDev dataset from HuggingFace"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("AIDev Dataset Setup")
    print("=" * 60)
    print()

    # Step 1: Create directory structure
    print("Step 1: Creating directory structure...")
    create_directories()
    print()

    # Step 2: Load dataset (real or sample)
    if args.use_sample:
        print("Step 2: Setting up SAMPLE dataset (for testing)...")
        setup_sample_data()
    else:
        print("Step 2: Loading REAL AIDev dataset from HuggingFace...")
        print("  This may take a few minutes...")
        print()
        success = load_aidev_dataset_from_huggingface()
        if not success:
            print()
            print("⚠ Failed to load AIDev dataset from HuggingFace.")
            print("  Possible reasons:")
            print("    - No internet connection")
            print("    - HuggingFace service is down")
            print("    - Missing required packages (pyarrow)")
            print()
            print("  To use sample data instead, run:")
            print("    python scripts/setup_aidv_dataset.py --use-sample")
            return 1

    # Step 3: Test data loading
    print()
    print("Step 3: Testing data loading with our pipeline...")
    success = test_data_loading()

    if success:
        print()
        print("=" * 60)
        print("✓ Dataset preparation completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run the analysis pipeline:")
        print("     python scripts/run_analysis_pipeline.py")
        print("  2. Generate comparisons:")
        print("     python scripts/compare_ai_to_standards.py")
        print("     python scripts/compare_ai_to_human.py")
        print("  3. Generate reports and visualizations:")
        print("     python scripts/generate_reports.py")
        print("     python scripts/generate_visualizations.py")
    else:
        print()
        print("✗ Dataset preparation failed!")
        print("  Check the error messages above for details.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())