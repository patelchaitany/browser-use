#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from browser_use.automation import BrowserAutomation

# Configure logging with colors
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

logger = logging.getLogger('task_runner')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class RateLimiter:
    """Simple rate limiter to prevent too many requests to the LLM API"""
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.interval = 60 / requests_per_minute
        self.last_request_time = 0
    
    async def wait(self):
        """Wait if necessary to respect the rate limit"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.interval:
            wait_time = self.interval - time_since_last_request
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()

class TaskRunner:
    """
    Task runner that uses an LLM to break down a task into steps and executes them
    using browser automation.
    """
    
    def __init__(
        self, 
        api_key: str,
        model_name: str = "gemini/gemini-2.5-pro-exp-03-25",
        max_steps: int = 10,
        output_dir: str = "task_output",
        headless: bool = False,
        requests_per_minute: int = 10
    ):
        """
        Initialize the task runner.
        
        Args:
            api_key: API key for the LLM provider
            model_name: Model to use for generating steps
            max_steps: Maximum number of steps to execute
            output_dir: Directory to save outputs
            headless: Whether to run the browser in headless mode
            requests_per_minute: Maximum LLM requests per minute
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_steps = max_steps
        self.output_dir = Path(output_dir)
        self.headless = headless
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(requests_per_minute)
        
        # Browser automation will be initialized in start()
        self.automation = None
        
        # Task state
        self.task_description = None
        self.step_history = []
        self.current_step_number = 0
        
    async def start(self):
        """Start the browser and initialize automation"""
        logger.info("Starting task runner...")
        
        self.automation = BrowserAutomation(
            api_key=self.api_key,
            model_name=self.model_name,
            headless=self.headless,
            output_dir=str(self.output_dir / "browser"),
            viewport_width=1280,
            viewport_height=800
        )
        
        await self.automation.start()
        logger.info("Task runner started successfully")
    
    async def stop(self):
        """Stop the browser and clean up resources"""
        if self.automation:
            await self.automation.stop()
            logger.info("Task runner stopped")
    
    async def execute_task(self, task_description: str, start_url: Optional[str] = None):
        """
        Execute a high-level task by breaking it down into steps and executing them.
        
        Args:
            task_description: Description of the task to execute
            start_url: Optional starting URL (if not provided, will use current page)
        """
        if not self.automation:
            raise RuntimeError("Task runner not started. Call start() first.")
        
        # Initialize task state
        self.task_description = task_description
        self.step_history = []
        self.current_step_number = 0
        
        # Navigate to starting URL if provided
        if start_url:
            logger.info(f"Navigating to starting URL: {start_url}")
            await self.automation.navigate_to(start_url)
        
        # Create a task-specific directory for outputs
        task_id = str(int(time.time()))
        task_dir = self.output_dir / f"task_{task_id}"
        task_dir.mkdir(exist_ok=True)
        
        # Save task description
        with open(task_dir / "task.txt", "w") as f:
            f.write(task_description)
        
        # Execute steps until max_steps is reached or task is completed
        while self.current_step_number < self.max_steps:
            try:
                # Generate next step
                await self.rate_limiter.wait()
                next_step = await self._generate_next_step()
                
                if not next_step or "completed" in next_step.lower() or "finished" in next_step.lower():
                    logger.info("Task completed successfully!")
                    break
                
                # Execute the step
                await self.rate_limiter.wait()
                result = await self._execute_step(next_step)
                
                # Save step results
                self._save_step_result(task_dir, next_step, result)
                
                # Add jitter to avoid hitting rate limits
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                logger.error(f"Error executing task: {e}", exc_info=True)
                # Save error information
                with open(task_dir / f"error_step_{self.current_step_number}.txt", "w") as f:
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"Step: {next_step if 'next_step' in locals() else 'unknown'}\n")
                break
        
        # Save final task summary
        self._save_task_summary(task_dir)
        
        return {
            "status": "completed" if self.current_step_number < self.max_steps else "max_steps_reached",
            "steps_executed": self.current_step_number,
            "task_dir": str(task_dir)
        }
    
    async def _generate_next_step(self) -> str:
        """
        Generate the next step using the LLM.
        
        Returns:
            Description of the next step
        """
        # Get page information
        page_url = self.automation.page.url
        page_title = await self.automation.browser.get_page_title()
        
        # Take screenshot for analysis
        screenshot_path = str(self.output_dir / "current_state.jpg")
        await self.automation.browser.take_screenshot(screenshot_path)
        
        # Get DOM information
        dom_state = await self.automation.dom_service.get_clickable_elements()
        
        # Extract relevant information about elements
        elements_info = []
        for idx, element in dom_state.selector_map.items():
            elements_info.append({
                "index": idx,
                "tag_name": element.tag_name,
                "text": element.get_all_text_till_next_clickable_element()[:100],  # Limit text
                "is_interactive": element.is_interactive,
                "is_in_viewport": element.is_in_viewport,
            })
        
        # Create prompt for generating next step
        prompt = f"""
        # Task Execution Planning
        
        You are an AI assistant helping to break down and execute a complex task in a web browser.
        
        ## Overall Task
        {self.task_description}
        
        ## Current State
        - Current URL: {page_url}
        - Page Title: {page_title}
        - Step Number: {self.current_step_number + 1} of {self.max_steps} maximum steps
        
        ## Interactive Elements Available
        {json.dumps(elements_info, indent=2)}
        
        ## History of Steps Executed
        {self._format_step_history()}
        
        ## Instructions
        1. Based on the overall task and current state, determine the next specific step to take.
        2. Respond with ONLY a single instruction describing what to do next.
        3. Be specific (e.g., "Click on the 'Login' button" rather than "Navigate to the login page").
        4. If the task appears to be completed, respond with only "TASK COMPLETED".
        5. Do not include reasoning or explain your choice, ONLY provide the single step instruction.
        
        Respond with the next step instruction only:
        """
        
        # Call LLM to generate next step
        messages = [{"role": "user", "content": prompt}]
        
        # For simplicity, reuse the automation's LLM controller
        try:
            with open(screenshot_path, "rb") as img_file:
                import base64
                image_data = base64.b64encode(img_file.read()).decode("utf-8")
            
            response = await self.automation.llm_controller._query_llm(prompt, image_data)
            
            # Clean up response (remove markdown, code blocks, etc.)
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.replace("```", "", 1)
                if "```" in clean_response:
                    clean_response = clean_response.split("```")[0].strip()
            
            # Log the next step
            logger.info(f"Generated next step: {clean_response}")
            
            return clean_response
        
        except Exception as e:
            logger.error(f"Error generating next step: {e}")
            raise
    
    async def _execute_step(self, step_description: str) -> Dict[str, Any]:
        """
        Execute a single step using browser automation.
        
        Args:
            step_description: Description of the step to execute
            
        Returns:
            Result of the step execution
        """
        logger.info(f"Executing step {self.current_step_number + 1}: {step_description}")
        
        # Use the browser automation to execute the step
        try:
            result = await self.automation.execute_ai_command(step_description)
            
            # Increment step counter
            self.current_step_number += 1
            
            # Add to step history
            self.step_history.append({
                "step_number": self.current_step_number,
                "description": step_description,
                "result": "success" if result.get("status") == "success" else "failed"
            })
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing step: {e}")
            # Add failed step to history
            self.step_history.append({
                "step_number": self.current_step_number + 1,
                "description": step_description,
                "result": "error",
                "error": str(e)
            })
            raise
    
    def _format_step_history(self) -> str:
        """Format step history for inclusion in prompts"""
        if not self.step_history:
            return "No steps executed yet."
        
        history = "Previously completed steps:\n"
        for step in self.step_history:
            history += f"{step['step_number']}. {step['description']} ({step['result']})\n"
        
        return history
    
    def _save_step_result(self, task_dir: Path, step_description: str, result: Dict[str, Any]):
        """Save step result to disk"""
        step_dir = task_dir / f"step_{self.current_step_number}"
        step_dir.mkdir(exist_ok=True)
        
        # Save step description
        with open(step_dir / "description.txt", "w") as f:
            f.write(step_description)
        
        # Save result as JSON
        with open(step_dir / "result.json", "w") as f:
            json.dump(result, f, indent=2)
        
        # Copy screenshots if they exist
        if "before_screenshot" in result and os.path.exists(result["before_screenshot"]):
            import shutil
            shutil.copy(result["before_screenshot"], step_dir / "before.jpg")
        
        if "after_screenshot" in result and os.path.exists(result["after_screenshot"]):
            import shutil
            shutil.copy(result["after_screenshot"], step_dir / "after.jpg")
    
    def _save_task_summary(self, task_dir: Path):
        """Save task summary to disk"""
        with open(task_dir / "summary.json", "w") as f:
            summary = {
                "task_description": self.task_description,
                "steps_executed": self.current_step_number,
                "step_history": self.step_history,
                "completed": self.current_step_number < self.max_steps
            }
            json.dump(summary, f, indent=2)

async def main():
    """Main entry point for the task runner."""
    # Get API key from environment variable
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("No API key found. Please set GOOGLE_API_KEY or GEMINI_API_KEY.")
        return
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Task Runner for Web Browser Automation")
    parser.add_argument("--task", required=True, help="Description of the task to execute")
    parser.add_argument("--url", help="Starting URL for the task")
    parser.add_argument("--model", default="gemini/gemini-2.5-pro-exp-03-25", help="LLM model to use")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--max-steps", type=int, default=10, help="Maximum number of steps to execute")
    parser.add_argument("--output-dir", default="task_output", help="Directory to store outputs")
    args = parser.parse_args()
    
    # Initialize and run the task runner
    task_runner = TaskRunner(
        api_key=api_key,
        model_name=args.model,
        max_steps=args.max_steps,
        output_dir=args.output_dir,
        headless=args.headless
    )
    
    try:
        await task_runner.start()
        result = await task_runner.execute_task(args.task, args.url)
        logger.info(f"Task execution completed with result: {result}")
    except Exception as e:
        logger.error(f"Error in task execution: {e}", exc_info=True)
    finally:
        await task_runner.stop()

if __name__ == "__main__":
    asyncio.run(main()) 