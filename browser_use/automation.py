import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import Page, async_playwright

from browser_use.dom.service import DomService
from browser_use.ai.llm_controller import LLMController

logger = logging.getLogger(__name__)

class Browser:
    """
    Browser wrapper class that provides common browser operations.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the browser wrapper.
        
        Args:
            page: The Playwright page object
        """
        self.page = page
    
    async def get_page(self) -> Page:
        """
        Get the current page object.
        
        Returns:
            The Playwright page object
        """
        return self.page
    
    async def navigate(self, url: str) -> None:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
        """
        logger.info(f"Navigating to {url}")
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")
    
    async def take_screenshot(self, path: str) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            path: The path to save the screenshot to
            
        Returns:
            The path to the saved screenshot
        """
        logger.info(f"Taking screenshot: {path}")
        await self.page.screenshot(path=path)
        return path
    
    async def get_page_content(self) -> str:
        """
        Get the text content of the current page.
        
        Returns:
            The page text content
        """
        try:
            content = await self.page.evaluate("""
                () => {
                    return document.body.innerText || document.body.textContent || '';
                }
            """)
            return content
        except Exception as e:
            logger.warning(f"Error getting page content: {e}")
            return ""
    
    async def get_current_url(self) -> str:
        """
        Get the current URL.
        
        Returns:
            The current URL
        """
        return self.page.url
    
    async def get_page_title(self) -> str:
        """
        Get the current page title.
        
        Returns:
            The page title
        """
        return await self.page.title()
    
    async def click(self, selector: str) -> bool:
        """
        Click on an element.
        
        Args:
            selector: CSS selector or XPath to the element
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if selector.startswith("//"):
                # XPath
                await self.page.click(f"xpath={selector}")
            else:
                # CSS selector
                await self.page.click(selector)
            return True
        except Exception as e:
            logger.warning(f"Error clicking element {selector}: {e}")
            return False
    
    async def input_text(self, selector: str, text: str) -> bool:
        """
        Input text into an element.
        
        Args:
            selector: CSS selector or XPath to the element
            text: Text to input
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if selector.startswith("//"):
                # XPath
                await self.page.fill(f"xpath={selector}", text)
            else:
                # CSS selector
                await self.page.fill(selector, text)
            return True
        except Exception as e:
            logger.warning(f"Error inputting text to {selector}: {e}")
            return False
    
    async def scroll(self, x: int = 0, y: int = 0) -> bool:
        """
        Scroll the page.
        
        Args:
            x: Horizontal scroll amount (positive is right, negative is left)
            y: Vertical scroll amount (positive is down, negative is up)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.page.mouse.wheel(x=x, y=y)
            return True
        except Exception as e:
            logger.warning(f"Error scrolling page: {e}")
            return False

class BrowserAutomation:
    """
    Browser automation class that can execute commands from AI models
    to interact with web pages.
    """
    
    def __init__(self, 
                 api_key: str,
                 model_name: str = "gemini/gemini-2.5-pro-exp-03-25",
                 provider: Optional[str] = None,
                 headless: bool = False, 
                 output_dir: str = "output",
                 viewport_width: int = 1280,
                 viewport_height: int = 720):
        """
        Initialize the browser automation class.
        
        Args:
            api_key: The API key for the chosen LLM provider
            model_name: The model name to use (default: gemini-pro-vision)
            provider: Optional provider name (when using non-default providers)
            headless: Whether to run the browser in headless mode
            output_dir: Directory to save screenshots and other outputs
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
        """
        self.api_key = api_key
        self.model_name = model_name
        self.provider = provider
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize state variables
        self.playwright = None
        self.browser_instance = None
        self.page = None
        self.browser = None
        self.dom_service = None
        self.llm_controller = None
    
    async def start(self) -> None:
        """Start the browser and initialize controllers."""
        # Initialize Playwright
        self.playwright = await async_playwright().start()
        
        # Launch browser
        self.browser_instance = await self.playwright.chromium.launch(headless=self.headless)
        
        # Create a page with specified viewport
        self.page = await self.browser_instance.new_page(viewport={
            "width": self.viewport_width, 
            "height": self.viewport_height
        })
        
        # Initialize browser wrapper
        self.browser = Browser(self.page)
        
        # Initialize DOM service
        self.dom_service = DomService(self.page)
        
        # Initialize LLM controller
        self.llm_controller = LLMController(
            api_key=self.api_key,
            model_name=self.model_name,
            provider=self.provider
        )
        
        logger.info("Browser automation started")
    
    async def stop(self) -> None:
        """Stop the browser and clean up resources."""
        if self.browser_instance:
            await self.browser_instance.close()
        if self.playwright:
            await self.playwright.stop()
        
        # Clean up
        self.browser = None
        self.page = None
        
        logger.info("Browser automation stopped")
    
    async def navigate_to(self, url: str) -> None:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
        """
        if not self.browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        await self.browser.navigate(url)
    
    async def get_browser(self) -> Browser:
        """
        Get the browser wrapper object.
        
        Returns:
            The Browser object
        """
        if not self.browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        return self.browser
    
    async def execute_ai_command(self, task_description: str) -> Dict[str, Any]:
        """
        Use AI to analyze the current page and execute the recommended action.
        
        Args:
            task_description: Description of what to accomplish on the current page
            
        Returns:
            Dictionary with the executed action and its result
        """
        if not self.page or not self.dom_service or not self.llm_controller:
            raise RuntimeError("Browser not started. Call start() first.")
        
        # Take a screenshot for AI to analyze
        screenshot_path = str(self.output_dir / "current_page.jpg")
        
        # Get action recommendation from AI
        action = await self.llm_controller.analyze_page(
            dom_service=self.dom_service,
            screenshot_path=screenshot_path,
            task_description=task_description
        )
        
        # Check if there was an error
        if "error" in action:
            logger.error(f"AI returned an error: {action['error']}")
            return {"status": "error", "message": action["error"]}
        
        # Execute the action
        result = await self._execute_action(action)
        
        # After action, wait for any navigation or load state change
        try:
            await self.page.wait_for_load_state("networkidle", timeout=3000)
        except:
            pass  # Ignore timeout
        
        # Take an "after" screenshot
        after_screenshot_path = str(self.output_dir / "after_action.jpg")
        await self.page.screenshot(path=after_screenshot_path)
        
        return {
            "status": "success",
            "action": action,
            "result": result,
            "before_screenshot": screenshot_path,
            "after_screenshot": after_screenshot_path
        }
    
    # For backward compatibility
    async def execute_gemini_command(self, task_description: str) -> Dict[str, Any]:
        """Alias for execute_ai_command for backward compatibility."""
        return await self.execute_ai_command(task_description)
    
    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a browser action based on AI's recommendation.
        
        Args:
            action: Dictionary with the action to execute
            
        Returns:
            Result of the action
        """
        # Click an element
        if "click_element" in action:
            element_index = action["click_element"]["index"]
            logger.info(f"Clicking element with index {element_index}")
            success = await self.dom_service.click_element(element_index)
            return {"clicked": success}
        
        # Input text
        elif "input_text" in action:
            element_index = action["input_text"]["index"]
            text = action["input_text"]["text"]
            logger.info(f"Inputting text '{text}' into element with index {element_index}")
            
            # Get the element from the DOM state
            dom_state = await self.dom_service.get_clickable_elements()
            if element_index in dom_state.selector_map:
                element = dom_state.selector_map[element_index]
                xpath = element.xpath
                
                try:
                    # Focus on the element by xpath
                    element_handle = await self.page.wait_for_selector(f"xpath={xpath}", timeout=2000)
                    if element_handle:
                        await element_handle.click()
                        await self.page.keyboard.type(text)
                        return {"typed": True}
                except Exception as e:
                    logger.error(f"Error typing text: {e}")
            
            return {"typed": False}
        
        # Navigate to URL
        elif "go_to_url" in action:
            url = action["go_to_url"]["url"]
            logger.info(f"Navigating to URL: {url}")
            await self.navigate_to(url)
            return {"navigated": True}
        
        # Scroll the page
        elif "scroll" in action:
            direction = action["scroll"]["direction"]
            amount = action["scroll"]["amount"]
            logger.info(f"Scrolling {direction} by {amount} pixels")
            
            # Convert direction to x,y coordinates
            x, y = 0, 0
            if direction == "down":
                y = amount
            elif direction == "up":
                y = -amount
            elif direction == "right":
                x = amount
            elif direction == "left":
                x = -amount
            
            # Execute the scroll
            await self.page.mouse.wheel(x=x, y=y)
            return {"scrolled": True}
        
        else:
            unsupported_action = list(action.keys())[0] if action else "unknown"
            logger.warning(f"Unsupported action: {unsupported_action}")
            return {"error": f"Unsupported action: {unsupported_action}"} 