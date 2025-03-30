#!/usr/bin/env python3
"""
AI-Driven Browser Automation Demo

This demo shows how to use the AI controller to automate browser tasks based on
natural language instructions. The AI will analyze the browser state, decide what
actions to take, and perform them automatically.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from browser_use.native_automation import NativeBrowserAutomation
from browser_use.native_browser import BrowserType
from browser_use.ai_controller import AIController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def run_ai_driven_automation(
    task_description: str,
    browser_type: str = "chrome",
    headless: bool = False,
    start_url: str = "https://www.google.com",
    output_dir: str = "output/ai_driven",
    proxy_config: Optional[Dict[str, str]] = None,
    extension_paths: Optional[List[str]] = None,
    model_name: str = "gpt-4o",
    max_actions: int = 20,
    api_key: Optional[str] = None
) -> Dict:
    """
    Run AI-driven browser automation.
    
    Args:
        task_description: Natural language description of the task to perform
        browser_type: Browser to use (chrome or firefox)
        headless: Whether to run in headless mode
        start_url: URL to start the browser at
        output_dir: Directory to save outputs
        proxy_config: Optional proxy configuration
        extension_paths: Optional list of browser extension paths
        model_name: LLM model to use
        max_actions: Maximum number of actions to take
        api_key: API key for the LLM provider
        
    Returns:
        Dictionary with the result of the automation
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Convert browser type string to enum
    browser_enum = BrowserType.CHROME
    if browser_type.lower() == "firefox":
        browser_enum = BrowserType.FIREFOX
    
    # Create the browser automation instance
    automation = NativeBrowserAutomation(
        browser_type=browser_enum,
        headless=headless,
        output_dir=output_dir,
        proxy_config=proxy_config,
        extensions=extension_paths
    )
    
    try:
        # Start the browser
        logger.info(f"Starting {browser_type} browser")
        await automation.start()
        
        # Navigate to the start URL
        logger.info(f"Navigating to start URL: {start_url}")
        await automation.navigate_to(start_url)
        
        # Get API key from environment if not provided
        if not api_key:
            # Check for provider-specific keys based on model
            if "gpt" in model_name.lower() or "openai" in model_name.lower():
                api_key = os.environ.get("OPENAI_API_KEY")
            elif "claude" in model_name.lower():
                api_key = os.environ.get("ANTHROPIC_API_KEY")
            elif "gemini" in model_name.lower():
                api_key = os.environ.get("GOOGLE_API_KEY")
            else:
                api_key = os.environ.get("LITELLM_API_KEY")
                
            if not api_key:
                raise ValueError("No API key provided and none found in environment variables")
        
        # Create the AI controller
        ai_controller = AIController(
            automation=automation,
            api_key=api_key,
            model_name=model_name,
            output_dir=output_dir,
            verbose=False
        )
        
        # Run the task
        logger.info(f"Running task: {task_description}")
        result = await ai_controller.run_task(
            task_description=task_description,
            max_actions=max_actions
        )
        
        # Log the result
        logger.info(f"Task result: {json.dumps(result)}")
        
        # Save the result to a file
        with open(output_path / "task_result.json", "w") as f:
            json.dump(result, f, indent=2)
            
        return result
    
    except Exception as e:
        logger.error(f"Error in AI-driven automation: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}
    
    finally:
        # Stop the browser
        await automation.stop()

async def main():
    """Parse command-line arguments and run the AI-driven browser automation."""
    parser = argparse.ArgumentParser(description="AI-Driven Browser Automation Demo")
    parser.add_argument("--task", type=str, required=True,
                        help="Natural language description of the task to perform")
    parser.add_argument("--browser", choices=["chrome", "firefox"], default="chrome",
                        help="Browser to use")
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode")
    parser.add_argument("--start-url", type=str, default="https://www.google.com",
                        help="URL to start the browser at")
    parser.add_argument("--output-dir", type=str, default="output/ai_driven",
                        help="Directory to save outputs")
    parser.add_argument("--proxy-host", type=str, default=None,
                        help="Proxy host (if using a proxy)")
    parser.add_argument("--proxy-port", type=str, default=None,
                        help="Proxy port (if using a proxy)")
    parser.add_argument("--extension", type=str, action="append", default=[],
                        help="Path to browser extension (.crx for Chrome, .xpi for Firefox)")
    parser.add_argument("--model", type=str, default="gpt-4o",
                        help="LLM model to use")
    parser.add_argument("--max-actions", type=int, default=20,
                        help="Maximum number of actions to take")
    parser.add_argument("--api-key", type=str, default=None,
                        help="API key for the LLM provider")
    
    args = parser.parse_args()
    
    # Set up proxy configuration if provided
    proxy_config = None
    if args.proxy_host and args.proxy_port:
        proxy_config = {
            "host": args.proxy_host,
            "port": args.proxy_port
        }
    
    # Run the AI-driven automation
    await run_ai_driven_automation(
        task_description=args.task,
        browser_type=args.browser,
        headless=args.headless,
        start_url=args.start_url,
        output_dir=args.output_dir,
        proxy_config=proxy_config,
        extension_paths=args.extension,
        model_name=args.model,
        max_actions=args.max_actions,
        api_key=args.api_key
    )

if __name__ == "__main__":
    asyncio.run(main()) 