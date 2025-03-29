#!/usr/bin/env python3
"""
Example script demonstrating AI-assisted browser navigation using Gemini AI.

This script:
1. Opens a browser and navigates to a website
2. Uses Gemini AI to analyze the page and determine what actions to take
3. Executes the recommended actions
4. Answers questions about the page content using AI

Make sure to set your GEMINI_API_KEY in the .env file before running.
"""

import os
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

from browser_use import BrowserUse, GeminiNavigator

# Load environment variables from .env file
load_dotenv()

async def main():
    # Create output directory for screenshots
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize the browser (non-headless mode to see the interaction)
    async with BrowserUse(headless=False) as browser:
        print("Browser started")
        
        # Initialize Gemini Navigator
        gemini = GeminiNavigator(browser)
        print("Gemini Navigator initialized")
        
        # Example 1: Simple search and navigation
        print("\n---Example 1: Simple navigation---")
        print("Navigating to Wikipedia...")
        await browser.goto("https://www.wikipedia.org")
        
        # Use Gemini to search for Python programming language
        print("Using Gemini to search for Python programming language...")
        result = await gemini.navigate("Search for Python programming language")
        
        # Wait for the page to load
        await asyncio.sleep(2)
        
        # Example 2: Answer questions about the page
        print("\n---Example 2: Answering questions about the page---")
        print("Asking Gemini about the Python programming language...")
        answer = await gemini.answer_question("What is the creator of Python and when was it created?")
        
        print(f"Answer: {answer['answer']}")
        
        # Save the answer to a file
        with open(output_dir / "python_info.txt", "w") as f:
            f.write(answer['answer'])
        
        # Example 3: Multi-step navigation
        print("\n---Example 3: Multi-step navigation---")
        print("Starting a multi-step navigation task...")
        
        # Search for something and then navigate through results
        results = await gemini.search_and_navigate(
            "best practices for Python web development",
            [
                "Find and click on a link about Flask or Django",
                "Look for information about database integration",
                "Find a code example and take note of it"
            ]
        )
        
        # Save the navigation results
        with open(output_dir / "navigation_results.json", "w") as f:
            # Convert complex objects to strings for JSON serialization
            serializable_results = []
            for result in results:
                result_copy = result.copy()
                if 'screenshot_path' in result_copy:
                    result_copy['screenshot_path'] = str(result_copy['screenshot_path'])
                serializable_results.append(result_copy)
            
            json.dump(serializable_results, f, indent=2)
        
        print("\nExamples completed. See output directory for results.")

if __name__ == "__main__":
    asyncio.run(main()) 