"""
Main BrowserUse class that provides the API for browser interaction and extraction.
"""

import os
import asyncio
import json
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, ElementHandle, Page, Playwright

from browser_use.dom.service import DOMService
from browser_use.interaction.service import InteractionService
from browser_use.extraction.service import ExtractionService
from browser_use.utils.logger import setup_logger

logger = setup_logger(__name__)

class BrowserUse:
    """
    Main class for browser interaction and data extraction.
    
    This class provides an API for:
    - Extracting useful links and elements
    - Taking screenshots with bounding boxes around links/elements
    - Interacting with the browser (clicking, scrolling, typing)
    - Drawing bounding boxes around found elements
    """
    
    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        """
        Initialize the BrowserUse instance.
        
        Args:
            headless (bool): Whether to run the browser in headless mode
            browser_type (str): Type of browser to use ('chromium', 'firefox', or 'webkit')
        """
        self.headless = headless
        self.browser_type = browser_type
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Services
        self.dom_service = None
        self.interaction_service = None
        self.extraction_service = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def start(self):
        """Start the browser and initialize services."""
        self.playwright = await async_playwright().start()
        
        browser_instance = getattr(self.playwright, self.browser_type)
        self.browser = await browser_instance.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Initialize services
        self.dom_service = DOMService(self.page)
        self.interaction_service = InteractionService(self.page)
        self.extraction_service = ExtractionService(self.page, self.dom_service)
        
        logger.info(f"Browser started: {self.browser_type}")
        return self
    
    async def close(self):
        """Close the browser and clean up resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
        
    async def goto(self, url: str, wait_until: str = "load"):
        """
        Navigate to a URL.
        
        Args:
            url (str): The URL to navigate to
            wait_until (str): When to consider navigation complete 
                              (options: 'load', 'domcontentloaded', 'networkidle')
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call 'start()' first.")
        
        await self.page.goto(url, wait_until=wait_until)
        logger.info(f"Navigated to: {url}")
        
    # Extraction methods
    
    async def extract_links(self, draw_boxes: bool = False) -> List[Dict]:
        """
        Extract all links from the current page.
        
        Args:
            draw_boxes (bool): Whether to highlight links on the page
            
        Returns:
            List[Dict]: List of dictionaries containing link information
        """
        return await self.extraction_service.extract_links(draw_boxes)
    
    async def extract_interactive_elements(self, draw_boxes: bool = False) -> List[Dict]:
        """
        Extract all interactive elements from the current page.
        
        Args:
            draw_boxes (bool): Whether to highlight elements on the page
            
        Returns:
            List[Dict]: List of dictionaries containing element information
        """
        return await self.extraction_service.extract_interactive_elements(draw_boxes)
    
    async def take_screenshot(self, path: str, draw_boxes: bool = True, elements: Optional[List[Dict]] = None):
        """
        Take a screenshot of the current page with optional bounding boxes around elements.
        
        Args:
            path (str): Path to save the screenshot
            draw_boxes (bool): Whether to draw boxes around elements
            elements (Optional[List[Dict]]): Elements to highlight (if None, extract all interactive elements)
        """
        await self.extraction_service.take_screenshot(path, draw_boxes, elements)
        
    # Interaction methods
    
    async def click_element(self, selector: str = None, 
                            element_name: str = None, 
                            position: Tuple[int, int] = None):
        """
        Click an element on the page.
        
        Args:
            selector (str): CSS selector for the element
            element_name (str): Name/text of the element to click
            position (Tuple[int, int]): X, Y coordinates to click
        """
        await self.interaction_service.click_element(selector, element_name, position)
        
    async def scroll(self, direction: str = "down", distance: int = None):
        """
        Scroll the page.
        
        Args:
            direction (str): Direction to scroll ('up', 'down', 'left', 'right')
            distance (int): Distance to scroll in pixels
        """
        await self.interaction_service.scroll(direction, distance)
        
    async def type_text(self, text: str, selector: str = None):
        """
        Type text into an input field.
        
        Args:
            text (str): Text to type
            selector (str): CSS selector for the input field
        """
        await self.interaction_service.type_text(text, selector) 