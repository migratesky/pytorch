#!/usr/bin/env python3
"""
GitHub CI Status Investigation Tool

This script helps investigate and understand the discrepancy between
GitHub API status checks and the UI display of checks.
"""

import sys
import subprocess
import logging
import json
from typing import Dict, List, Any

def run_gh_command(cmd: List[str]) -> Dict[str, Any]:
    """Run a GitHub CLI command and return parsed JSON result."""
    try:
        result = subprocess.run(['gh'] + cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except subprocess.CalledProcessError as e:
        logging.error(f"GitHub CLI command failed: {e}")
        logging.error(f"STDERR: {e.stderr}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON response: {e}")
        return {}

def check_workflow_runs(owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    """Check workflow runs associated with the PR."""
    cmd = ['api', f'repos/{owner}/{repo}/actions/runs', 
           '--jq', f'.workflow_runs[] | select(.pull_requests[]?.number == {pr_number})']
    
    try:
        result = subprocess.run(['gh'] + cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            # Parse each line as separate JSON object
            runs = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        runs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return runs
        return []
    except Exception as e:
        logging.error(f"Failed to get workflow runs: {e}")
        return []

def check_check_runs(owner: str, repo: str, commit_sha: str) -> List[Dict[str, Any]]:
    """Check check runs for a specific commit."""
    cmd = ['api', f'repos/{owner}/{repo}/commits/{commit_sha}/check-runs']
    result = run_gh_command(cmd)
    return result.get('check_runs', [])

def check_status_checks(owner: str, repo: str, commit_sha: str) -> Dict[str, Any]:
    """Check status checks for a specific commit."""
    cmd = ['api', f'repos/{owner}/{repo}/commits/{commit_sha}/status']
    return run_gh_command(cmd)

def analyze_pr_checks(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """Comprehensive analysis of PR checks and status."""
    logging.info(f"Analyzing PR #{pr_number} in {owner}/{repo}")
    
    # Get PR details
    pr_cmd = ['api', f'repos/{owner}/{repo}/pulls/{pr_number}']
    pr_data = run_gh_command(pr_cmd)
    
    if not pr_data:
        logging.error("Failed to get PR data")
        return {}
    
    head_sha = pr_data.get('head', {}).get('sha')
    if not head_sha:
        logging.error("Could not get HEAD SHA from PR")
        return {}
    
    logging.info(f"HEAD SHA: {head_sha}")
    
    # Get various types of checks
    workflow_runs = check_workflow_runs(owner, repo, pr_number)
    check_runs = check_check_runs(owner, repo, head_sha)
    status_checks = check_status_checks(owner, repo, head_sha)
    
    return {
        'pr_data': pr_data,
        'head_sha': head_sha,
        'workflow_runs': workflow_runs,
        'check_runs': check_runs,
        'status_checks': status_checks
    }

def print_analysis_report(analysis: Dict[str, Any]):
    """Print a comprehensive analysis report."""
    print("\n" + "="*60)
    print("GitHub CI Status Analysis Report")
    print("="*60)
    
    pr_data = analysis.get('pr_data', {})
    print(f"PR Number: #{pr_data.get('number', 'Unknown')}")
    print(f"Title: {pr_data.get('title', 'Unknown')}")
    print(f"State: {pr_data.get('state', 'Unknown')}")
    print(f"HEAD SHA: {analysis.get('head_sha', 'Unknown')}")
    
    # Workflow runs analysis
    workflow_runs = analysis.get('workflow_runs', [])
    print(f"\n📋 Workflow Runs: {len(workflow_runs)}")
    for run in workflow_runs:
        status = run.get('status', 'unknown')
        conclusion = run.get('conclusion', 'none')
        name = run.get('name', 'Unknown')
        print(f"  - {name}: {status} ({conclusion})")
    
    # Check runs analysis
    check_runs = analysis.get('check_runs', [])
    print(f"\n✅ Check Runs: {len(check_runs)}")
    for check in check_runs:
        status = check.get('status', 'unknown')
        conclusion = check.get('conclusion', 'none')
        name = check.get('name', 'Unknown')
        print(f"  - {name}: {status} ({conclusion})")
    
    # Status checks analysis
    status_checks = analysis.get('status_checks', {})
    statuses = status_checks.get('statuses', [])
    print(f"\n🔍 Status Checks: {len(statuses)}")
    state = status_checks.get('state', 'unknown')
    print(f"Overall State: {state}")
    for status in statuses:
        state = status.get('state', 'unknown')
        context = status.get('context', 'Unknown')
        description = status.get('description', '')
        print(f"  - {context}: {state} - {description}")
    
    # Summary
    total_checks = len(workflow_runs) + len(check_runs) + len(statuses)
    print(f"\n📊 Summary:")
    print(f"  Total Workflow Runs: {len(workflow_runs)}")
    print(f"  Total Check Runs: {len(check_runs)}")
    print(f"  Total Status Checks: {len(statuses)}")
    print(f"  Combined Total: {total_checks}")
    
    if total_checks > 0:
        print(f"\n💡 Explanation:")
        print(f"  The GitHub UI may show {total_checks} checks because it combines:")
        print(f"  - Workflow runs from GitHub Actions")
        print(f"  - Check runs from apps and integrations")
        print(f"  - Traditional status checks")
        print(f"  The GitHub API status endpoint only shows traditional status checks.")
    else:
        print(f"\n⚠️  No checks found. This could indicate:")
        print(f"  - Workflows haven't been triggered yet")
        print(f"  - Repository doesn't have CI configured")
        print(f"  - Permissions issue with GitHub CLI")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze GitHub PR CI status')
    parser.add_argument('owner', help='Repository owner')
    parser.add_argument('repo', help='Repository name')
    parser.add_argument('pr_number', type=int, help='Pull request number')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    # Check if GitHub CLI is available
    try:
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: GitHub CLI (gh) is not installed or not in PATH")
        print("Please install it from: https://cli.github.com/")
        sys.exit(1)
    
    # Perform analysis
    analysis = analyze_pr_checks(args.owner, args.repo, args.pr_number)
    
    if analysis:
        print_analysis_report(analysis)
    else:
        print("Failed to analyze PR checks")
        sys.exit(1)

if __name__ == '__main__':
    main()
