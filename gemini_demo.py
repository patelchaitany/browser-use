#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from browser_use.automation import BrowserAutomation

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def run_ai_automation(model_name="gemini/gemini-2.5-pro-exp-03-25"):
    """
    Demo of using AI to automate browser interaction based on screenshots
    and interactive element detection.
    
    Args:
        model_name: The LiteLLM model to use
    """
    # Get API key based on the model
    api_key = None
    
    if "gemini" in model_name.lower():
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set.")
            return
    elif "gpt" in model_name.lower() or "openai" in model_name.lower():
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set.")
            return
    elif "claude" in model_name.lower():
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set.")
            return
    else:
        # Default to LiteLLM API key
        api_key = os.environ.get("LITELLM_API_KEY")
        if not api_key:
            logger.error("No API key found for the specified model. Please set the appropriate environment variable.")
            return
    
    # Initialize the browser automation
    automation = BrowserAutomation(
        api_key=api_key,
        model_name=model_name,
        headless=False,  # Set to True for headless mode
        output_dir="ai_output",
        viewport_width=1280,
        viewport_height=800
    )
    
    try:
        # Start the browser
        await automation.start()
        
        # Navigate to Google
        await automation.navigate_to("https://www.google.com")
        
        # Example 1: Search for something on Google
        result1 = await automation.execute_ai_command(
            "Search for 'python programming language' on Google"
        )
        logger.info(f"Action 1 result: {json.dumps(result1['action'] if 'action' in result1 else result1, indent=2)}")
        
        # Allow time to see the results
        await asyncio.sleep(2)
        
        # Example 2: Click on the first search result
        result2 = await automation.execute_ai_command(
            "Click on the first search result"
        )
        logger.info(f"Action 2 result: {json.dumps(result2['action'] if 'action' in result2 else result2, indent=2)}")
        
        # Allow time to see the results
        await asyncio.sleep(5)
        
        # Example 3: Go to a different website and interact with it
        await automation.navigate_to("https://playwright.dev")
        
        result3 = await automation.execute_ai_command(
            "Click on the 'Get Started' button or link"
        )
        logger.info(f"Action 3 result: {json.dumps(result3['action'] if 'action' in result3 else result3, indent=2)}")
        
        # Allow time to see the results
        await asyncio.sleep(5)
        
    finally:
        # Always stop the browser properly
        await automation.stop()

def main():
    """Main entry point with error handling."""
    # Get model from command-line arguments or use default
    model_name = "gemini/gemini-2.5-pro-exp-03-25"  # Default model
    if len(sys.argv) > 1:
        model_name = sys.argv[1]
        
    try:
        asyncio.run(run_ai_automation(model_name))
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error during demo: {e}", exc_info=True)

if __name__ == "__main__":
    main() 