#!/usr/bin/env python3
"""
Gemini Task Runner

This script uses the GeminiNavigator to perform general-purpose web browsing tasks 
specified by the user. It handles the browser session and executes a series of
navigation steps to complete the requested task, then provides a detailed report
of actions taken and information found.

Example usage:
    python gemini_task_runner.py "Compare stock prices of Tesla and Apple"
"""

import os
import sys
import asyncio
import argparse
import json
import random
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
# Add the parent directory to the path so we can import from browser_use
sys.path.append(str(Path(__file__).parent.parent.parent))

from browser_use import BrowserUse
from browser_use.ai.gemini_navigator import GeminiNavigator
from browser_use.utils.logger import setup_logger

logger = setup_logger(__name__)
load_dotenv()


class GeminiTaskRunner:
    """
    Class that uses GeminiNavigator to perform user-specified web browsing tasks.
    """
    
    def __init__(self, api_key: str = None, headless: bool = False, output_dir: str = None, 
                 max_retries: int = 5, initial_retry_delay: float = 2.0):
        """
        Initialize the task runner.
        
        Args:
            api_key (str): Gemini API key. If not provided, will look for GEMINI_API_KEY in environment
            headless (bool): Whether to run the browser in headless mode
            output_dir (str): Directory to save screenshots and reports
            max_retries (int): Maximum number of retries for rate-limited API calls
            initial_retry_delay (float): Initial delay in seconds before retrying (will increase exponentially)
        """
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        self.headless = headless
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            # Create output directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = Path(f"gemini_tasks_{timestamp}")
            
        # Create the output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize report data structure
        self.report = {
            "task": "",
            "start_time": "",
            "end_time": "",
            "status": "not_started",
            "steps": [],
            "summary": "",
            "screenshots": [],
            "rate_limit_retries": 0
        }
    
    async def _with_rate_limit_handling(self, func, *args, **kwargs):
        """
        Execute a function with rate limit handling.
        
        Args:
            func: The async function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function
            
        Raises:
            Exception: If the function fails after max retries
        """
        retries = 0
        delay = self.initial_retry_delay
        
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Check if it's a rate limit error
                error_str = str(e).lower()
                is_rate_limit = any(term in error_str for term in [
                    "rate limit", "ratelimit", "429", "too many requests", 
                    "quota exceeded", "resource exhausted"
                ])
                
                if not is_rate_limit or retries >= self.max_retries:
                    # Not a rate limit error or we've reached max retries
                    raise
                
                # It's a rate limit error and we can retry
                retries += 1
                self.report["rate_limit_retries"] += 1
                
                # Calculate delay with exponential backoff and jitter
                jitter = random.uniform(0, 0.1 * delay)
                wait_time = delay + jitter
                
                logger.warning(
                    f"Rate limit encountered. Retrying in {wait_time:.2f} seconds... "
                    f"(Attempt {retries}/{self.max_retries})"
                )
                
                print(f"⚠️ Rate limit reached. Waiting {wait_time:.2f}s before retry {retries}/{self.max_retries}...")
                
                # Wait before retrying
                await asyncio.sleep(wait_time)
                
                # Increase delay for next retry (exponential backoff)
                delay = min(delay * 2, 60)  # Cap at 60 seconds
    
    async def run_task(self, task: str) -> Dict:
        """
        Execute a web browsing task specified by the user.
        
        Args:
            task (str): The task to perform (e.g., "Compare stock prices of Tesla and Apple")
            
        Returns:
            Dict: Report of the task execution
        """
        logger.info(f"Starting task: {task}")
        self.report["task"] = task
        self.report["start_time"] = datetime.now().isoformat()
        self.report["status"] = "in_progress"
        self.report["rate_limit_retries"] = 0
        
        # Initialize the browser
        browser = None
        navigator = None
        
        try:
            # Initialize the browser
            browser = BrowserUse(headless=self.headless)
            await browser.start()
            
            # Initialize the Gemini Navigator
            navigator = GeminiNavigator(browser, api_key=self.api_key)
            
            # First, we ask Gemini to plan the navigation steps needed for this task
            await browser.goto("https://www.google.com/")  # Start with a blank page
            plan = await self._with_rate_limit_handling(
                self._plan_navigation_steps, navigator, task
            )
            print(plan)
            
            # Execute each navigation step
            step_results = []
            for i, step in enumerate(plan["steps"]):
                step_number = i + 1
                logger.info(f"Executing step {step_number}/{len(plan['steps'])}: {step}")
                
                # Track step in report
                step_data = {
                    "step_number": step_number,
                    "description": step,
                    "actions": [],
                    "status": "in_progress"
                }
                self.report["steps"].append(step_data)
                
                # Execute the navigation step with rate limit handling
                result = await self._with_rate_limit_handling(
                    navigator.navigate, step
                )
                
                # Save a screenshot for this step
                screenshot_path = self.output_dir / f"step_{step_number}.png"
                await browser.take_screenshot(str(screenshot_path))
                
                # Track action in report
                action = result.get("analysis", {}).get("action", "unknown")
                element = result.get("analysis", {}).get("element_text") or result.get("analysis", {}).get("selector", "unknown element")
                reasoning = result.get("analysis", {}).get("reasoning", "")
                
                step_data["actions"].append({
                    "action": action,
                    "element": element,
                    "reasoning": reasoning,
                    "success": result.get("success", False)
                })
                
                step_data["status"] = "completed" if result.get("success", False) else "failed"
                step_results.append(result)
                
                # Small delay between steps
                await asyncio.sleep(1)
            
            # Ask Gemini to summarize the task results with rate limit handling
            summary = await self._with_rate_limit_handling(
                self._summarize_task_results, navigator, task, step_results
            )
            
            self.report["summary"] = summary.get("answer", "Failed to generate summary")
            self.report["status"] = "completed"
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            self.report["status"] = "failed"
            self.report["error"] = str(e)
            
        finally:
            self.report["end_time"] = datetime.now().isoformat()
            
            # Save the report to a file
            report_path = self.output_dir / "report.json"
            with open(report_path, "w") as f:
                json.dump(self.report, f, indent=2)
                
            # Generate a human-readable report
            self._generate_human_readable_report()
            
            # Close the browser
            if browser:
                await browser.close()
                
            return self.report
    
    async def _plan_navigation_steps(self, navigator: GeminiNavigator, task: str) -> Dict:
        """
        Ask Gemini to plan the navigation steps needed for the task.
        
        Args:
            navigator (GeminiNavigator): The Gemini Navigator
            task (str): The task to plan for
            
        Returns:
            Dict: Planning information including steps
        """
        planning_prompt = f"""
        I need to perform this web browsing task: "{task}"
        
        Please help me plan the navigation steps I should take to complete this task.
        Break it down into a sequence of specific browser actions (like searching, clicking, scrolling).
        
        Return a JSON with:
        1. A list of navigation steps as clear, specific instructions
        2. The URL I should start with
        
        Format your response as a JSON object with these fields:
        {{
            "start_url": "the URL to start with",
            "steps": ["step 1", "step 2", ...]
        }}
        """
        
        # Ask Gemini for the plan
        result = await navigator.answer_question(planning_prompt)
        
        # Extract the JSON plan from the response
        answer_text = result.get("answer", "")
        
        # Try to extract JSON from the response
        try:
            # If the response is wrapped in code blocks
            if "```json" in answer_text:
                json_text = answer_text.split("```json")[1].split("```")[0].strip()
            elif "```" in answer_text:
                json_text = answer_text.split("```")[1].split("```")[0].strip()
            else:
                # Try to find JSON-like content between curly braces
                start = answer_text.find("{")
                end = answer_text.rfind("}")
                if start >= 0 and end > start:
                    json_text = answer_text[start:end+1]
                else:
                    json_text = answer_text
                    
            plan = json.loads(json_text)
            
            # Go to the start URL
            if "start_url" in plan and plan["start_url"]:
                await navigator.browser.goto(plan["start_url"])
                
            return plan
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing planning response: {e}")
            logger.error(f"Response was: {answer_text}")
            
            # Fallback plan for common scenarios
            if "stock price" in task.lower() or "stock" in task.lower():
                return {
                    "start_url": "https://www.google.com",
                    "steps": [
                        f"Search for {task}",
                        "Look for the stock price information",
                        "Compare the prices",
                        "Summarize the findings"
                    ]
                }
            else:
                return {
                    "start_url": "https://www.google.com",
                    "steps": [
                        f"Search for {task}",
                        "Click on a relevant search result",
                        "Extract the requested information",
                        "If needed, go back and look for more information",
                        "Summarize findings"
                    ]
                }
    
    async def _summarize_task_results(self, navigator: GeminiNavigator, task: str, steps: List[Dict]) -> Dict:
        """
        Ask Gemini to summarize the results of the task.
        
        Args:
            navigator (GeminiNavigator): The Gemini Navigator
            task (str): The original task
            steps (List[Dict]): Results from each step
            
        Returns:
            Dict: Summary information
        """
        # Create a summary prompt
        summary_prompt = f"""
        I've completed the task: "{task}"
        
        Please analyze what you see on this page and provide a summary of the results.
        Focus specifically on providing the information requested in the original task.
        
        Format the summary with:
        1. A brief overview of what was found
        2. The specific data or information requested
        3. Any relevant comparisons or analysis
        
        Make your summary clear, concise and directly answering the original task.
        """
        
        # Ask Gemini for a summary
        return await navigator.answer_question(summary_prompt)
    
    def _generate_human_readable_report(self) -> str:
        """
        Generate a human-readable report from the JSON report data.
        
        Returns:
            str: Path to the report file
        """
        # Create the report text
        report_text = f"TASK REPORT: {self.report['task']}\n"
        report_text += f"=" * 80 + "\n\n"
        report_text += f"Status: {self.report['status'].upper()}\n"
        report_text += f"Started: {self.report['start_time']}\n"
        report_text += f"Completed: {self.report['end_time']}\n"
        report_text += f"Rate limit retries: {self.report.get('rate_limit_retries', 0)}\n\n"
        
        report_text += "STEPS PERFORMED:\n"
        report_text += "-" * 80 + "\n"
        
        for step in self.report["steps"]:
            report_text += f"Step {step['step_number']}: {step['description']} ({step['status']})\n"
            
            for action in step.get("actions", []):
                report_text += f"  - {action['action'].upper()} on '{action['element']}'\n"
                if action.get("reasoning"):
                    report_text += f"    Reason: {action['reasoning']}\n"
                    
            report_text += "\n"
        
        report_text += "SUMMARY:\n"
        report_text += "-" * 80 + "\n"
        report_text += self.report["summary"] + "\n\n"
        
        report_text += "SCREENSHOTS:\n"
        report_text += "-" * 80 + "\n"
        for i in range(len(self.report["steps"])):
            report_text += f"- Step {i+1}: {self.output_dir}/step_{i+1}.png\n"
            
        # Write the report to a file
        report_path = self.output_dir / "report.txt"
        with open(report_path, "w") as f:
            f.write(report_text)
            
        return str(report_path)

async def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run a web browsing task using Gemini AI")
    parser.add_argument("task", type=str, help="The task to perform")
    parser.add_argument("--api-key", type=str, help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--output-dir", type=str, help="Directory to save output")
    parser.add_argument("--max-retries", type=int, default=5, help="Maximum retry attempts for rate limits")
    parser.add_argument("--retry-delay", type=float, default=2.0, help="Initial retry delay in seconds")
    
    args = parser.parse_args()
    
    # Run the task
    runner = GeminiTaskRunner(
        api_key=args.api_key,
        headless=args.headless,
        output_dir=args.output_dir,
        max_retries=args.max_retries,
        initial_retry_delay=args.retry_delay
    )
    
    report = await runner.run_task(args.task)
    
    # Print report summary
    print(f"\nTask completed with status: {report['status'].upper()}")
    if report.get('rate_limit_retries', 0) > 0:
        print(f"Required {report['rate_limit_retries']} retries due to rate limits")
    print(f"Summary: {report['summary'][:200]}...")
    print(f"Full report saved to: {runner.output_dir}/report.txt")

if __name__ == "__main__":
    asyncio.run(main()) 