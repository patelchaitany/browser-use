"""
Native browser controllers for Chrome and Firefox direct access.
This module provides direct access to native browsers using their APIs without relying on
third-party browser automation frameworks like Playwright.
"""

import logging
import os
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from selenium import webdriver
from selenium.common.exceptions import (ElementClickInterceptedException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

logger = logging.getLogger(__name__)

class BrowserType(Enum):
    """Enum for supported browser types."""
    CHROME = "chrome"
    FIREFOX = "firefox"

class NativeBrowser:
    """
    Native browser class that provides direct control over Chrome and Firefox.
    Uses Selenium WebDriver with direct browser-specific interfaces.
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
        Initialize the native browser controller.
        
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
        
        # WebDriver instance
        self.driver = None
        self.wait = None
        
    async def start(self) -> None:
        """Start the browser and initialize it."""
        if self.browser_type == BrowserType.CHROME:
            self._start_chrome()
        elif self.browser_type == BrowserType.FIREFOX:
            self._start_firefox()
        else:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")
        
        # Create a WebDriverWait instance for waiting operations
        self.wait = WebDriverWait(self.driver, 10)
        
        logger.info(f"Started {self.browser_type.value} browser")
        
    def _start_chrome(self) -> None:
        """Start Chrome browser with configured options."""
        options = ChromeOptions()
        
        # Configure headless mode if requested
        if self.headless:
            options.add_argument("--headless=new")
            
        # Set window size
        options.add_argument(f"--window-size={self.viewport_width},{self.viewport_height}")
        
        # Set user data directory if provided
        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            
        # Add extensions if provided
        for extension_path in self.extensions:
            options.add_extension(extension_path)
            
        # Configure proxy if provided
        if self.proxy_config:
            proxy_str = f"{self.proxy_config.get('host', '')}:{self.proxy_config.get('port', '')}"
            if self.proxy_config.get('username') and self.proxy_config.get('password'):
                auth = f"{self.proxy_config['username']}:{self.proxy_config['password']}@"
                proxy_str = f"{auth}{proxy_str}"
                
            proxy = Proxy()
            proxy.proxy_type = ProxyType.MANUAL
            proxy.http_proxy = proxy_str
            proxy.ssl_proxy = proxy_str
            proxy.socks_proxy = proxy_str
            
            options.add_argument(f'--proxy-server={proxy_str}')
        
        # Add common Chrome options for better performance and compatibility
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Create and start Chrome driver
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
    def _start_firefox(self) -> None:
        """Start Firefox browser with configured options."""
        options = FirefoxOptions()
        
        # Configure headless mode if requested
        if self.headless:
            options.add_argument("--headless")
            
        # Set window size
        options.add_argument(f"--width={self.viewport_width}")
        options.add_argument(f"--height={self.viewport_height}")
        
        # Set user data directory if provided (Firefox profile)
        if self.user_data_dir:
            options.add_argument("-profile")
            options.add_argument(self.user_data_dir)
            
        # Add extensions if provided
        for extension_path in self.extensions:
            options.add_extension(extension_path)
            
        # Configure proxy if provided
        if self.proxy_config:
            host = self.proxy_config.get('host', '')
            port = self.proxy_config.get('port', '')
            
            options.set_preference("network.proxy.type", 1)
            options.set_preference("network.proxy.http", host)
            options.set_preference("network.proxy.http_port", int(port))
            options.set_preference("network.proxy.ssl", host)
            options.set_preference("network.proxy.ssl_port", int(port))
            options.set_preference("network.proxy.socks", host)
            options.set_preference("network.proxy.socks_port", int(port))
            
            if self.proxy_config.get('username') and self.proxy_config.get('password'):
                options.set_preference("network.proxy.username", self.proxy_config['username'])
                options.set_preference("network.proxy.password", self.proxy_config['password'])
        
        # Create and start Firefox driver
        service = FirefoxService(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=options)
        
    async def stop(self) -> None:
        """Stop the browser and clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
            
        logger.info(f"Stopped {self.browser_type.value} browser")
        
    async def navigate_to(self, url: str) -> None:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        logger.info(f"Navigating to {url}")
        self.driver.get(url)
        
        # Wait for page to load
        self._wait_for_page_load()
        
    def _wait_for_page_load(self, timeout: int = 30) -> None:
        """
        Wait for the page to fully load.
        
        Args:
            timeout: Maximum wait time in seconds
        """
        old_page = self.driver.find_element(By.TAG_NAME, "html")
        
        # Wait for the DOM to be in ready state
        end_time = time.time() + timeout
        while time.time() < end_time:
            page_state = self.driver.execute_script("return document.readyState")
            if page_state == "complete":
                # Additional wait for any JavaScript to finish
                time.sleep(0.5)
                return
            time.sleep(0.1)
            
        logger.warning("Page load timed out")
        
    async def take_screenshot(self, path: Optional[str] = None) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            path: The path to save the screenshot to, or None to use default path
            
        Returns:
            The path to the saved screenshot
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        if not path:
            path = str(self.output_dir / f"screenshot_{int(time.time())}.png")
            
        logger.info(f"Taking screenshot: {path}")
        self.driver.save_screenshot(path)
        return path
    
    async def get_current_url(self) -> str:
        """
        Get the current URL.
        
        Returns:
            The current URL
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        return self.driver.current_url
    
    async def get_page_title(self) -> str:
        """
        Get the current page title.
        
        Returns:
            The page title
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        return self.driver.title
    
    async def get_page_source(self) -> str:
        """
        Get the HTML source of the current page.
        
        Returns:
            The page HTML source
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        return self.driver.page_source
    
    async def click(self, selector: str, by: By = By.CSS_SELECTOR) -> bool:
        """
        Click on an element.
        
        Args:
            selector: Element selector (CSS selector, XPath, etc.)
            by: Selenium By type for selector
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            # Handle XPath selectors
            if selector.startswith("//") and by == By.CSS_SELECTOR:
                by = By.XPATH
                
            # Wait for element to be clickable and click it
            element = self.wait.until(
                EC.element_to_be_clickable((by, selector))
            )
            element.click()
            return True
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
            logger.warning(f"Error clicking element {selector}: {e}")
            return False
            
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
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            # Handle XPath selectors
            if selector.startswith("//") and by == By.CSS_SELECTOR:
                by = By.XPATH
                
            # Wait for element to be present, clear it, and input text
            element = self.wait.until(
                EC.presence_of_element_located((by, selector))
            )
            element.clear()
            element.send_keys(text)
            return True
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f"Error inputting text to {selector}: {e}")
            return False
            
    async def get_element_text(self, selector: str, by: By = By.CSS_SELECTOR) -> Optional[str]:
        """
        Get text from an element.
        
        Args:
            selector: Element selector (CSS selector, XPath, etc.)
            by: Selenium By type for selector
            
        Returns:
            Element text if found, None otherwise
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            # Handle XPath selectors
            if selector.startswith("//") and by == By.CSS_SELECTOR:
                by = By.XPATH
                
            element = self.wait.until(
                EC.presence_of_element_located((by, selector))
            )
            return element.text
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f"Error getting text from {selector}: {e}")
            return None
    
    async def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 10) -> Optional[WebElement]:
        """
        Wait for an element to be present on the page.
        
        Args:
            selector: Element selector (CSS selector, XPath, etc.)
            by: Selenium By type for selector
            timeout: Maximum wait time in seconds
            
        Returns:
            The WebElement if found, None otherwise
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            # Handle XPath selectors
            if selector.startswith("//") and by == By.CSS_SELECTOR:
                by = By.XPATH
                
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(f"Element {selector} not found within {timeout} seconds: {e}")
            return None
    
    async def find_elements(self, selector: str, by: By = By.CSS_SELECTOR) -> List[WebElement]:
        """
        Find all elements matching a selector.
        
        Args:
            selector: Element selector (CSS selector, XPath, etc.)
            by: Selenium By type for selector
            
        Returns:
            List of matching WebElements, empty list if none found
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            # Handle XPath selectors
            if selector.startswith("//") and by == By.CSS_SELECTOR:
                by = By.XPATH
                
            return self.driver.find_elements(by, selector)
        except Exception as e:
            logger.warning(f"Error finding elements {selector}: {e}")
            return []
    
    async def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the browser.
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script
            
        Returns:
            Result of the script execution
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.warning(f"Error executing script: {e}")
            return None
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """
        Get all cookies from the browser.
        
        Returns:
            List of cookie dictionaries
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        return self.driver.get_cookies()
    
    async def add_cookie(self, cookie: Dict[str, Any]) -> None:
        """
        Add a cookie to the browser.
        
        Args:
            cookie: Cookie dictionary (name, value, domain, etc.)
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        self.driver.add_cookie(cookie)
    
    async def delete_all_cookies(self) -> None:
        """Delete all cookies in the browser."""
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        self.driver.delete_all_cookies()
    
    async def get_browser_logs(self) -> List[Dict[str, Any]]:
        """
        Get browser console logs.
        
        Returns:
            List of log entries (Chrome only)
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start() first.")
        
        if self.browser_type == BrowserType.CHROME:
            return self.driver.get_log('browser')
        else:
            logger.warning("Browser logs are only available in Chrome")
            return [] 