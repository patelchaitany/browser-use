#!/usr/bin/env python3
"""
Compare Stock Prices Example

This script demonstrates how to use the GeminiTaskRunner to compare
stock prices of specified companies. It provides a simple interface to run
stock comparison tasks with the Gemini-powered browser automation.

Usage:
    python compare_stocks.py "Tesla Apple"
    python compare_stocks.py "Microsoft Google Amazon" --headless
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import from browser_use
sys.path.append(str(Path(__file__).parent.parent.parent))

from browser_use.examples.gemini_task_runner import GeminiTaskRunner

async def compare_stocks(companies, headless=False, api_key=None, output_dir=None, 
                        max_retries=5, initial_retry_delay=2.0):
    """
    Compare stock prices of the specified companies.
    
    Args:
        companies (list): List of company names to compare
        headless (bool): Whether to run the browser in headless mode
        api_key (str): Gemini API key (optional)
        output_dir (str): Output directory for reports and screenshots (optional)
        max_retries (int): Maximum number of retries for rate-limited API calls
        initial_retry_delay (float): Initial delay before retrying rate-limited calls
        
    Returns:
        str: Path to the generated report
    """
    # Format the task string
    companies_str = ", ".join(companies[:-1]) + f" and {companies[-1]}" if len(companies) > 1 else companies[0]
    task = f"Compare the current stock prices of {companies_str} and summarize the key differences"
    
    # Create the task runner
    runner = GeminiTaskRunner(
        api_key=api_key,
        headless=headless,
        output_dir=output_dir,
        max_retries=max_retries,
        initial_retry_delay=initial_retry_delay
    )
    
    # Run the task
    print(f"Starting stock price comparison for: {companies_str}")
    report = await runner.run_task(task)
    
    # Print a summary
    print("\n" + "=" * 80)
    print(f"STOCK COMPARISON COMPLETE - Status: {report['status'].upper()}")
    if report.get('rate_limit_retries', 0) > 0:
        print(f"Rate limit retries needed: {report.get('rate_limit_retries')} times")
    print("=" * 80 + "\n")
    
    if report['status'] == 'completed':
        print("SUMMARY:")
        print("-" * 80)
        print(report['summary'])
        print("\nFull report and screenshots saved to:", runner.output_dir)
    else:
        print(f"Task failed with error: {report.get('error', 'Unknown error')}")
    
    return str(runner.output_dir / "report.txt")

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Compare stock prices of specified companies")
    parser.add_argument("companies", type=str, help="Space-separated list of companies to compare (e.g., 'Tesla Apple')")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--api-key", type=str, help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--output-dir", type=str, help="Directory to save output")
    parser.add_argument("--max-retries", type=int, default=5, help="Maximum retry attempts for rate limits")
    parser.add_argument("--retry-delay", type=float, default=2.0, help="Initial retry delay in seconds")
    
    args = parser.parse_args()
    
    # Split the companies string into a list
    companies = args.companies.split()
    
    if not companies:
        print("Error: Please specify at least one company")
        sys.exit(1)
    
    # Run the comparison
    await compare_stocks(
        companies=companies,
        headless=args.headless,
        api_key=args.api_key,
        output_dir=args.output_dir,
        max_retries=args.max_retries,
        initial_retry_delay=args.retry_delay
    )

if __name__ == "__main__":
    asyncio.run(main()) 