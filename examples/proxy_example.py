#!/usr/bin/env python3
"""
Proxy Example for AI-Driven Browser Automation

This example demonstrates how to use the AI-driven browser automation with a proxy server.
It performs a geo-specific search and extracts the results, illustrating how proxies can
be used to access region-specific content.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to sys.path to import the browser_use package
sys.path.insert(0, str(Path(__file__).parent.parent))

from browser_use import NativeBrowserAutomation, BrowserType, AIController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables for API keys
load_dotenv()

async def run_proxy_example():
    """Run an example of using AI-driven browser automation with a proxy."""
    
    # Set up proxy configuration
    # Replace with your actual proxy details
    proxy_config = {
        "host": "127.0.0.1",  # Example proxy host
        "port": "8080",       # Example proxy port
        # Uncomment if your proxy requires authentication
        # "username": "user",
        # "password": "pass"
    }
    
    # Output directory for results
    output_dir = "output/proxy_example"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get API key from environment variables
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No API key found in environment variables")
        return
    
    # Create browser automation with proxy
    automation = NativeBrowserAutomation(
        browser_type=BrowserType.CHROME,
        headless=False,  # Set to True for headless mode
        proxy_config=proxy_config,
        output_dir=output_dir
    )
    
    try:
        # Start the browser
        logger.info("Starting browser with proxy configuration")
        await automation.start()
        
        # Verify the proxy is working by checking the IP address
        logger.info("Navigating to IP check website")
        await automation.navigate_to("https://whatismyipaddress.com/")
        
        # Wait a moment to load the page
        await asyncio.sleep(3)
        
        # Create AI controller
        ai_controller = AIController(
            automation=automation,
            api_key=api_key,
            model_name="gpt-4o",  # Change to your preferred model
            output_dir=output_dir
        )
        
        # Run a geo-specific task
        task_description = """
        1. Verify if the proxy is working by checking if the current IP is different from your actual IP
        2. Go to Google and search for "local restaurants near me"
        3. Extract the first 3 restaurant names and their locations
        """
        
        logger.info(f"Running task: {task_description}")
        result = await ai_controller.run_task(
            task_description=task_description,
            max_actions=20
        )
        
        # Save and display results
        with open(f"{output_dir}/proxy_result.json", "w") as f:
            json.dump(result, f, indent=2)
            
        logger.info(f"Task completed with result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in proxy example: {e}")
    finally:
        # Stop the browser
        logger.info("Stopping browser")
        await automation.stop()

if __name__ == "__main__":
    asyncio.run(run_proxy_example()) 