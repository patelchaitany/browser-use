#!/usr/bin/env python3
"""
Example script demonstrating the Browser Use API.

This script:
1. Opens a browser and navigates to a website
2. Extracts links and takes a screenshot with boxes around them
3. Extracts interactive elements and takes a screenshot with boxes around them
4. Interacts with elements on the page (clicking, scrolling, typing)
5. Extracts structured data from the page
"""

import os
import asyncio
import json
from pathlib import Path

from browser_use import BrowserUse

async def main():
    # Create output directory for screenshots
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize the browser (non-headless mode to see the interaction)
    async with BrowserUse(headless=False) as browser:
        print("Browser started")
        
        # Navigate to a URL
        print("Navigating to example.com...")
        await browser.goto("https://google.com")
        print("Navigated to example.com")
        
        # Extract all links and take a screenshot with boxes around them
        print("Extracting links...")
        links = await browser.extract_links(draw_boxes=True)
        await browser.take_screenshot(str(output_dir / "example_links.png"))
        
        # Print the extracted links
        print(f"Found {len(links)} links:")
        for i, link in enumerate(links[:5]):  # Print first 5 links
            print(f"  {i+1}. {link['text']} -> {link['href']}")
        if len(links) > 5:
            print(f"  ... and {len(links) - 5} more")
            
        # Extract interactive elements
        print("\nExtracting interactive elements...")
        elements = await browser.extract_interactive_elements(draw_boxes=True)
        await browser.take_screenshot(str(output_dir / "example_elements.png"))
        
        # Print the extracted elements
        print(f"Found {len(elements)} interactive elements:")
        for i, element in enumerate(elements[:5]):  # Print first 5 elements
            print(f"  {i+1}. <{element['tagName']}> {element['text'][:50]}")
        if len(elements) > 5:
            print(f"  ... and {len(elements) - 5} more")
        
        # Save the extracted data to JSON files
        with open(output_dir / "links.json", "w") as f:
            json.dump(links, f, indent=2)
        with open(output_dir / "elements.json", "w") as f:
            json.dump(elements, f, indent=2)
            
        print("\nNavigation and interaction example...")
        # Navigate to a search engine
        print("Navigating to DuckDuckGo...")
        await browser.goto("https://duckduckgo.com")
        print("Navigated to duckduckgo.com")
        
        # Type into the search box
        await browser.type_text("Python browser automation", selector="input[name='q']")
        print("Typed search query")
        
        # Click the search button
        await browser.click_element(selector="button[type='submit']")
        print("Clicked search button")
        
        # Wait for results to load
        await asyncio.sleep(2)
        
        # Take a screenshot of the search results
        await browser.take_screenshot(str(output_dir / "search_results.png"))
        
        # Scroll down to see more results
        print("Scrolling down...")
        await browser.scroll(direction="down")
        await asyncio.sleep(1)
        await browser.take_screenshot(str(output_dir / "search_results_scrolled.png"))
        
        # Extract structured data from the page
        print("\nExtracting structured data...")
        data = await browser.extraction_service.extract_structured_data()
        
        # Save structured data to a JSON file
        with open(output_dir / "structured_data.json", "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"Page title: {data['title']}")
        
        print("\nExample completed. See output directory for results.")

if __name__ == "__main__":
    asyncio.run(main()) 