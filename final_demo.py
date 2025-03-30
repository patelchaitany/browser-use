#!/usr/bin/env python3
import asyncio
import logging
import os
from pathlib import Path

import asyncio
from playwright.async_api import async_playwright

from browser_use.dom.service import DomService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    """
    Demo script to show how to extract and highlight interactive elements on a webpage.
    """
    # Create output directory for screenshots
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser (headless=False to see the highlight boxes)
        browser = await p.chromium.launch(headless=False)
        
        # Create a new page with a decent window size
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        
        # Navigate to a website
        url = "https://google.com"
        logger.info(f"Navigating to {url}")
        await page.goto(url)
        
        # Wait for page to load completely
        await page.wait_for_load_state("networkidle")
        
        # Initialize our DOM service
        dom_service = DomService(page)
        
        # Extract and highlight clickable elements
        logger.info("Extracting clickable elements and highlighting them")
        dom_state = await dom_service.get_clickable_elements(
            highlight_elements=True,
            focus_element=-1,  # No specific focus element
            viewport_expansion=100  # Expand viewport detection area by 100px
        )
        
        # Display information about the detected elements
        logger.info(f"Found {len(dom_state.selector_map)} interactive elements")
        
        for idx, element in dom_state.selector_map.items():
            logger.info(f"Element {idx}: {element.tag_name} - Text: {element.get_all_text_till_next_clickable_element()[:50]}...")
        
        # Take a screenshot with highlights
        screenshot_path = output_dir / "highlighted_elements.png"
        await dom_service.take_screenshot_with_highlights(str(screenshot_path))
        logger.info(f"Screenshot saved to {screenshot_path}")
        
        # Demonstrate clicking an element (click the first element if available)
        if dom_state.selector_map:
            first_element_idx = min(dom_state.selector_map.keys())
            logger.info(f"Clicking element with index {first_element_idx}")
            
            success = await dom_service.click_element(first_element_idx)
            
            if success:
                logger.info("Element clicked successfully")
                # Wait for any navigation or changes
                await page.wait_for_load_state("networkidle")
                
                # Take another screenshot after clicking
                after_click_path = output_dir / "after_click.png"
                await page.screenshot(path=str(after_click_path))
                logger.info(f"After-click screenshot saved to {after_click_path}")
            else:
                logger.error("Failed to click element")
        
        # Allow time to see the highlights
        logger.info("Waiting 5 seconds to view the highlighted elements...")
        await asyncio.sleep(5)
        
        # Close the browser
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 
