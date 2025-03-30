#!/usr/bin/env python3
"""
Web Assistant - AI-Powered Web Task Automation

This script provides a general-purpose web assistant that can complete
a wide variety of web-based tasks using the GeminiNavigator.

Examples:
    python web_assistant.py "Find the top 5 most visited tourist attractions in Paris"
    python web_assistant.py "Check the weather forecast for New York City this weekend"
    python web_assistant.py "Compare prices of iPhone 15 Pro across major retailers"
    python web_assistant.py "Find and summarize recent news about renewable energy"
"""

import os
import sys
import asyncio
import argparse
import time
from pathlib import Path

# Add the parent directory to the path so we can import from browser_use
sys.path.append(str(Path(__file__).parent.parent.parent))

from browser_use.examples.gemini_task_runner import GeminiTaskRunner

class WebAssistant:
    """
    AI-powered web assistant that can complete a wide variety of web tasks.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the web assistant.
        
        Args:
            api_key (str): Gemini API key (optional)
        """
        self.api_key = api_key
    
    async def perform_task(self, task, headless=False, output_dir=None, verbose=True):
        """
        Perform a specified web task.
        
        Args:
            task (str): The task to perform
            headless (bool): Whether to run the browser in headless mode
            output_dir (str): Directory to save results (optional)
            verbose (bool): Whether to print detailed progress
            
        Returns:
            dict: Task report
        """
        if verbose:
            print(f"\n🔍 STARTING TASK: {task}")
            print("=" * 80)
            print("Initializing AI web assistant...")
        
        # Create timestamp-based output directory if none provided
        if not output_dir:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            task_slug = task.lower().replace(" ", "_")[:30]  # Create slug from task
            output_dir = f"web_assistant_{timestamp}_{task_slug}"
        
        # Create the task runner
        runner = GeminiTaskRunner(
            api_key=self.api_key,
            headless=headless,
            output_dir=output_dir,
            max_retries=5,
            initial_retry_delay=2.0
        )
        
        # Show progress indicator if in verbose mode
        if verbose:
            print("Browser starting... AI assistant planning task...")
        
        # Run the task
        start_time = time.time()
        report = await runner.run_task(task)
        elapsed_time = time.time() - start_time
        
        # Print task results
        if verbose:
            print("\n" + "=" * 80)
            print(f"✅ TASK COMPLETED - Status: {report['status'].upper()}")
            print(f"⏱️  Time taken: {elapsed_time:.2f} seconds")
            print("=" * 80 + "\n")
            
            if report['status'] == 'completed':
                print("📋 SUMMARY:")
                print("-" * 80)
                print(report['summary'])
                print("\n📸 Screenshots and detailed report saved to:", runner.output_dir)
                
                # Print steps taken
                print("\n🔄 ACTIONS PERFORMED:")
                print("-" * 80)
                for step in report["steps"]:
                    print(f"Step {step['step_number']}: {step['description']} ({step['status']})")
                    for action in step.get("actions", []):
                        print(f"  - {action['action'].upper()} on '{action['element']}'")
            else:
                print(f"❌ Task failed with error: {report.get('error', 'Unknown error')}")
        
        return report

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AI-powered web assistant for completing web tasks")
    parser.add_argument("--task", type=str, help="The web task to perform")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--api-key", type=str, help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--output-dir", type=str, help="Directory to save output")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    
    args = parser.parse_args()
    
    # Create and run the web assistant
    assistant = WebAssistant(api_key=args.api_key)
    await assistant.perform_task(
        task=args.task,
        headless=args.headless,
        output_dir=args.output_dir,
        verbose=not args.quiet
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTask cancelled by user. Exiting...")
        sys.exit(1) 