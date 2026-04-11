#!/usr/bin/env python3
"""
Script to fetch human-authored pull requests from GitHub repositories
present in the AIDev-pop dataset.

This script will:
1. Load the AIDev dataset to extract the unique list of repositories.
2. Query the GitHub API for closed, merged PRs from these repositories.
3. Filter out known AI bots.
4. Save the fetched PRs to `data/raw/human_prs/`.
"""

import os
import sys
import json
import time
import logging
import random
from pathlib import Path

import requests

# Add the project root to the path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import AIDevDataLoader
from src.data_loader.schema_definitions import DataLoaderConfig

# Known bot accounts to exclude
BOT_ACCOUNTS = [
    'dependabot[bot]', 'github-actions[bot]', 'renovate[bot]', 
    'dependabot-preview[bot]', 'snyk-bot', 'greenkeeper[bot]'
]

# GitHub API setup
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
HEADERS = {
    'Accept': 'application/vnd.github.v3+json',
}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'

OUTPUT_DIR = project_root / 'data' / 'raw' / 'human_prs'

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - '
               '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def handle_rate_limit(response):
    """Handle GitHub API rate limiting with exponential backoff."""
    if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
        if response.headers['X-RateLimit-Remaining'] == '0':
            reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
            sleep_time = max(reset_time - time.time(), 0) + 1
            logging.warning(f"Rate limit exceeded. Sleeping for {sleep_time:.0f} seconds.")
            time.sleep(sleep_time)
            return True
    elif response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        logging.warning(f"Secondary rate limit exceeded. Sleeping for {retry_after} seconds.")
        time.sleep(retry_after)
        return True
    return False

def make_request_with_backoff(url, params=None):
    """Make a request with exponential backoff for rate limits."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            
            if handle_rate_limit(response):
                continue
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            if attempt < max_retries - 1:
                sleep_time = 2 ** attempt * 5
                logging.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logging.error(f"Max retries exceeded for URL: {url}")
                return None

def fetch_prs_for_repo(owner, repo, target_count=10):
    """Fetch closed, merged PRs for a specific repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {
        'state': 'closed',
        'sort': 'updated',
        'direction': 'desc',
        'per_page': 100,
    }
    
    prs_fetched = []
    page = 1
    
    logging.info(f"Fetching PRs for {owner}/{repo}...")
    
    while len(prs_fetched) < target_count and page <= 5:  # Limit pages to prevent infinite loops
        params['page'] = page
        data = make_request_with_backoff(url, params)
        
        if not data:
            break
            
        if not isinstance(data, list):
            logging.warning(f"Unexpected response format for {owner}/{repo}")
            break
            
        if len(data) == 0:
            break
            
        for pr in data:
            # Check if merged and authored by a human
            if pr.get('merged_at') is not None and pr.get('user', {}).get('login') not in BOT_ACCOUNTS:
                # We need to fetch the files for this PR to match our AIDev dataset schema
                files_url = pr.get('url') + '/files'
                files_data = make_request_with_backoff(files_url)
                
                if files_data and isinstance(files_data, list):
                    # Only include PRs that have changes
                    if len(files_data) > 0:
                        pr['files'] = files_data
                        prs_fetched.append(pr)
                        logging.debug(f"Fetched human PR #{pr['number']} from {owner}/{repo}")
                        
                        if len(prs_fetched) >= target_count:
                            break
        page += 1
        
    return prs_fetched

def main():
    setup_logging()
    
    if not GITHUB_TOKEN:
        logging.warning("GITHUB_TOKEN environment variable not set. API rate limits will be strictly enforced (60 req/hr).")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load the AIDev dataset to extract the unique list of repositories
    logging.info("Loading AIDev dataset to identify target repositories...")
    config = DataLoaderConfig(data_directory="./data/raw")
    data_loader = AIDevDataLoader(config)
    
    # We just need the raw repos, no need to run the full pipeline
    try:
        from src.data_loader.schema_definitions import AIDevTable
        raw_repos = data_loader.loader.load_table(AIDevTable.REPOSITORY)
        processed_repos = data_loader.preprocessor.preprocess_table(raw_repos, AIDevTable.REPOSITORY)
        
        # Get repository names (e.g., 'owner/repo')
        # Assuming the 'name' column exists or we can extract it from URL
        repo_names = []
        if 'name' in processed_repos.columns:
            repo_names = processed_repos['name'].unique().tolist()
        elif 'url' in processed_repos.columns:
            # Extract from github.com/owner/repo
            urls = processed_repos['url'].dropna().unique().tolist()
            repo_names = [url.replace('https://api.github.com/repos/', '') for url in urls if 'api.github.com/repos/' in url]
        
        if not repo_names:
            logging.error("Could not extract repository names from the dataset. Proceeding with a fallback list.")
            # Fallback for demonstration based on our AIDev dataset understanding
            repo_names = ['pallets/flask', 'django/django', 'psf/requests', 'spring-projects/spring-boot']
            
    except Exception as e:
        logging.error(f"Failed to load repositories from dataset: {e}")
        repo_names = ['pallets/flask', 'django/django', 'psf/requests', 'spring-projects/spring-boot']
        
    logging.info(f"Identified {len(repo_names)} target repositories. Selecting a subset for human PR fetching.")
    
    # For Phase 3, we don't need all repos, just a representative sample to get ~1000 PRs
    # Shuffle and pick top N
    random.seed(42)
    sample_repos = random.sample(repo_names, min(50, len(repo_names)))
    
    target_prs_per_repo = 20  # 50 repos * 20 PRs = 1000 PRs
    total_fetched = 0
    
    for repo_full_name in sample_repos:
        parts = repo_full_name.split('/')
        if len(parts) != 2:
            continue
            
        owner, repo = parts
        
        # Check if we already fetched this repo
        repo_file = OUTPUT_DIR / f"{owner}_{repo}.json"
        if repo_file.exists():
            logging.info(f"Skipping {owner}/{repo}, already fetched.")
            with open(repo_file, 'r') as f:
                data = json.load(f)
                total_fetched += len(data)
            continue
            
        prs = fetch_prs_for_repo(owner, repo, target_count=target_prs_per_repo)
        
        if prs:
            with open(repo_file, 'w') as f:
                json.dump(prs, f, indent=2)
            total_fetched += len(prs)
            logging.info(f"Saved {len(prs)} PRs for {owner}/{repo}")
        
        # Small delay to respect API guidelines
        time.sleep(1)
        
    logging.info(f"Finished fetching human PRs. Total PRs: {total_fetched}")

if __name__ == "__main__":
    main()
