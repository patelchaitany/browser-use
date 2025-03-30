"""
Native browser automation module that integrates the native browser controllers
with the data extraction API.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from selenium.webdriver.common.by import By

from browser_use.extract import DataExtractor, WebElementExtractor, extract_structured_data
from browser_use.native_browser import BrowserType, NativeBrowser

logger = logging.getLogger(__name__)

class NativeBrowserAutomation:
    """
    Native browser automation class that integrates browser control with data extraction.
    Provides a complete automation solution for controlling browsers and extracting data.
    """
    
    def __init__(self, 
                 browser_type: BrowserType = BrowserType.CHROME,
                 headless: bool = False,
                 user_data_dir: Optional[str] = None,
                 proxy_config: Optional[Dict[str, str]] = None,
                 extensions: Optional[List[str]] = None,
                 output_dir: str = "output",
                 viewport_width: int = 1280,
                 viewport_height: int = 720):
        """
        Initialize the native browser automation.
        
        Args:
            browser_type: Type of browser (CHROME or FIREFOX)
            headless: Whether to run in headless mode
            user_data_dir: Path to browser user data directory for profiles/sessions
            proxy_config: Proxy configuration (dict with host, port, username, password)
            extensions: List of paths to browser extension files (.crx for Chrome, .xpi for Firefox)
            output_dir: Directory to save screenshots and other outputs
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
        """
        self.browser_type = browser_type
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.proxy_config = proxy_config
        self.extensions = extensions or []
        self.output_dir = Path(output_dir)
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize browser
        self.browser = NativeBrowser(
            browser_type=browser_type,
            headless=headless,
            user_data_dir=user_data_dir,
            proxy_config=proxy_config,
            extensions=extensions,
            output_dir=str(output_dir),
            viewport_width=viewport_width,
            viewport_height=viewport_height
        )
        
    async def start(self) -> None:
        """Start the browser and initialize the automation."""
        await self.browser.start()
        logger.info("Native browser automation started")
        
    async def stop(self) -> None:
        """Stop the browser and clean up resources."""
        await self.browser.stop()
        logger.info("Native browser automation stopped")
        
    async def navigate_to(self, url: str) -> None:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
        """
        await self.browser.navigate_to(url)
        
    async def take_screenshot(self, path: Optional[str] = None) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            path: The path to save the screenshot to, or None to use default path
            
        Returns:
            The path to the saved screenshot
        """
        return await self.browser.take_screenshot(path)
        
    async def extract_data(self, extraction_config: Dict[str, Any]) -> Any:
        """
        Extract data from the current page using the specified configuration.
        
        Args:
            extraction_config: Configuration for data extraction
            
        Returns:
            Extracted data
        """
        # Get page source
        html_content = await self.browser.get_page_source()
        
        # Create extractor and extract data
        extractor = DataExtractor(html_content)
        return extractor.extract(extraction_config)
        
    async def extract_all_structured_data(self) -> Dict[str, Any]:
        """
        Extract all structured data from the current page.
        
        Returns:
            Dictionary with all structured data
        """
        html_content = await self.browser.get_page_source()
        return extract_structured_data(html_content)
        
    async def click(self, selector: str, by: By = By.CSS_SELECTOR) -> bool:
        """
        Click on an element.
        
        Args:
            selector: Element selector (CSS selector, XPath, etc.)
            by: Selenium By type for selector
            
        Returns:
            True if successful, False otherwise
        """
        return await self.browser.click(selector, by)
        
    async def input_text(self, selector: str, text: str, by: By = By.CSS_SELECTOR) -> bool:
        """
        Input text into an element.
        
        Args:
            selector: Element selector (CSS selector, XPath, etc.)
            text: Text to input
            by: Selenium By type for selector
            
        Returns:
            True if successful, False otherwise
        """
        return await self.browser.input_text(selector, text, by)
        
    async def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 10) -> bool:
        """
        Wait for an element to be present on the page.
        
        Args:
            selector: Element selector (CSS selector, XPath, etc.)
            by: Selenium By type for selector
            timeout: Maximum wait time in seconds
            
        Returns:
            True if element is found, False otherwise
        """
        element = await self.browser.wait_for_element(selector, by, timeout)
        return element is not None
        
    async def extract_table(self, table_selector: str, by: By = By.CSS_SELECTOR) -> List[Dict[str, str]]:
        """
        Extract a HTML table into a list of dictionaries.
        
        Args:
            table_selector: Selector for the table element
            by: Selenium By type for selector
            
        Returns:
            List of dictionaries, each representing a row with column headers as keys
        """
        # Get page source and find table element
        html_content = await self.browser.get_page_source()
        
        # Note: Using Selenium here would be more robust for tables rendered by JavaScript,
        # but for this example we'll use the DataExtractor for consistency
        extractor = DataExtractor(html_content)
        
        if by == By.XPATH:
            # If using XPath, adapt to XPath strategy
            table_data = extractor.extract({
                'strategy': 'xpath',
                'selector': table_selector,
                'multiple': False,
                'children': [
                    {'strategy': 'xpath', 'selector': './/tr', 'multiple': True}
                ]
            })
        else:
            # Using CSS selector
            table_data = extractor.extract({
                'strategy': 'css_selector',
                'selector': table_selector,
                'multiple': False,
                'children': [
                    {'strategy': 'css_selector', 'selector': 'tr', 'multiple': True}
                ]
            })
            
        return table_data if table_data else []
        
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """
        Get all cookies from the browser.
        
        Returns:
            List of cookie dictionaries
        """
        return await self.browser.get_cookies()
        
    async def add_cookie(self, cookie: Dict[str, Any]) -> None:
        """
        Add a cookie to the browser.
        
        Args:
            cookie: Cookie dictionary (name, value, domain, etc.)
        """
        await self.browser.add_cookie(cookie)
        
    async def delete_all_cookies(self) -> None:
        """Delete all cookies in the browser."""
        await self.browser.delete_all_cookies()
        
    async def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the browser.
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script
            
        Returns:
            Result of the script execution
        """
        return await self.browser.execute_script(script, *args)
    
    # Complete automation flows
    
    async def login_flow(self, 
                        url: str, 
                        username_selector: str, 
                        password_selector: str,
                        submit_selector: str, 
                        username: str, 
                        password: str) -> bool:
        """
        Complete login flow for a website.
        
        Args:
            url: Login page URL
            username_selector: Selector for username field
            password_selector: Selector for password field
            submit_selector: Selector for submit button
            username: Username to enter
            password: Password to enter
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Navigate to login page
            await self.navigate_to(url)
            
            # Wait for username field
            if not await self.wait_for_element(username_selector):
                logger.error(f"Username field not found: {username_selector}")
                return False
                
            # Enter username
            if not await self.input_text(username_selector, username):
                logger.error(f"Could not input username into {username_selector}")
                return False
                
            # Enter password
            if not await self.input_text(password_selector, password):
                logger.error(f"Could not input password into {password_selector}")
                return False
                
            # Click submit button
            if not await self.click(submit_selector):
                logger.error(f"Could not click submit button: {submit_selector}")
                return False
                
            # Wait for navigation to complete
            await asyncio.sleep(3)  # Wait for page to load after login
            
            # Take screenshot for verification
            screenshot_path = await self.take_screenshot(str(self.output_dir / "login_result.png"))
            logger.info(f"Login flow completed, screenshot saved to {screenshot_path}")
            
            # Should implement better login success verification here,
            # such as checking for specific elements or cookies
            
            return True
        except Exception as e:
            logger.error(f"Error in login flow: {e}")
            return False
            
    async def search_flow(self, 
                        url: str, 
                        search_selector: str, 
                        submit_selector: str, 
                        search_query: str,
                        results_selector: str) -> List[Dict[str, Any]]:
        """
        Complete search flow for a website and extract search results.
        
        Args:
            url: Search page URL
            search_selector: Selector for search input field
            submit_selector: Selector for search submit button
            search_query: Search terms to enter
            results_selector: Selector for search results elements
            
        Returns:
            List of extracted search results
        """
        try:
            # Navigate to search page
            await self.navigate_to(url)
            
            # Wait for search field
            if not await self.wait_for_element(search_selector):
                logger.error(f"Search field not found: {search_selector}")
                return []
                
            # Enter search query
            if not await self.input_text(search_selector, search_query):
                logger.error(f"Could not input search query into {search_selector}")
                return []
                
            # Click search button
            if not await self.click(submit_selector):
                logger.error(f"Could not click search button: {submit_selector}")
                return []
                
            # Wait for results to load
            if not await self.wait_for_element(results_selector):
                logger.error(f"Search results not found: {results_selector}")
                return []
                
            # Take screenshot of search results
            screenshot_path = await self.take_screenshot(str(self.output_dir / "search_results.png"))
            logger.info(f"Search results screenshot saved to {screenshot_path}")
            
            # Extract search results
            results = await self.extract_data({
                'strategy': 'css_selector',
                'selector': results_selector,
                'multiple': True,
                'children': [
                    {'strategy': 'css_selector', 'selector': 'a', 'attribute': 'href'},
                    {'strategy': 'css_selector', 'selector': 'h3,h2,h1', 'attribute': None},
                    {'strategy': 'css_selector', 'selector': 'p', 'attribute': None}
                ]
            })
            
            # Save results to file
            results_file = self.output_dir / "search_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
                
            logger.info(f"Extracted {len(results)} search results and saved to {results_file}")
            
            return results
        except Exception as e:
            logger.error(f"Error in search flow: {e}")
            return []
            
    async def navigate_and_extract_flow(self, 
                                      url: str, 
                                      extraction_config: Dict[str, Any],
                                      output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Navigate to a URL and extract data using specified configuration.
        
        Args:
            url: URL to navigate to
            extraction_config: Configuration for data extraction
            output_file: Optional file to save extracted data
            
        Returns:
            Extracted data
        """
        try:
            # Navigate to the URL
            await self.navigate_to(url)
            
            # Extract data
            data = await self.extract_data(extraction_config)
            
            # Save data to file if specified
            if output_file:
                file_path = self.output_dir / output_file
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Extracted data saved to {file_path}")
                
            return data
        except Exception as e:
            logger.error(f"Error in navigate and extract flow: {e}")
            return {} 