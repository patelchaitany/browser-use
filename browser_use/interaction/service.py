"""
Interaction service for browser interactions like clicking, scrolling, and typing.
"""

from typing import Optional, Tuple, Union

from playwright.async_api import Page

from browser_use.utils.logger import setup_logger

logger = setup_logger(__name__)

class InteractionService:
    """
    Service for interacting with the browser.
    
    Provides methods for:
    - Clicking elements
    - Scrolling the page
    - Typing text
    """
    
    def __init__(self, page: Page):
        """
        Initialize the interaction service.
        
        Args:
            page (Page): Playwright page object
        """
        self.page = page
        
    async def click_element(self, selector: str = None, 
                           element_name: str = None, 
                           position: Tuple[int, int] = None) -> None:
        """
        Click an element on the page.
        
        Args:
            selector (str): CSS selector for the element
            element_name (str): Name/text of the element to click
            position (Tuple[int, int]): X, Y coordinates to click
        
        Raises:
            ValueError: If no method to identify the element is provided
        """
        if position:
            # Click at specific coordinates
            await self.page.mouse.click(position[0], position[1])
            logger.info(f"Clicked at position {position}")
            return
            
        if selector:
            # Click element by selector
            await self.page.click(selector)
            logger.info(f"Clicked element with selector: {selector}")
            return
            
        if element_name:
            # Click element by text content
            # Try exact text first
            try:
                await self.page.click(f"text='{element_name}'")
                logger.info(f"Clicked element with text: {element_name}")
                return
            except Exception:
                # Try contains text
                try:
                    await self.page.click(f"text={element_name}")
                    logger.info(f"Clicked element containing text: {element_name}")
                    return
                except Exception as e:
                    logger.error(f"Could not find element with text: {element_name}")
                    raise
        
        raise ValueError("Must provide selector, element_name, or position to click")
        
    async def scroll(self, direction: str = "down", distance: Optional[int] = None) -> None:
        """
        Scroll the page.
        
        Args:
            direction (str): Direction to scroll ('up', 'down', 'left', 'right')
            distance (int): Distance to scroll in pixels
        
        Raises:
            ValueError: If direction is invalid
        """
        if direction not in ("up", "down", "left", "right"):
            raise ValueError(f"Invalid scroll direction: {direction}")
            
        # Default distance if not specified
        if distance is None:
            # Use 1/4 of the viewport height or width for vertical or horizontal scrolling
            viewport_size = self.page.viewport_size
            if direction in ("up", "down"):
                distance = viewport_size["height"] // 4
            else:
                distance = viewport_size["width"] // 4
                
        # Apply correct sign based on direction
        if direction == "up":
            distance = -distance
        elif direction == "left":
            distance = -distance
            
        # Execute the scroll
        if direction in ("up", "down"):
            await self.page.evaluate(f"window.scrollBy(0, {distance})")
            logger.info(f"Scrolled {direction} by {abs(distance)} pixels")
        else:
            await self.page.evaluate(f"window.scrollBy({distance}, 0)")
            logger.info(f"Scrolled {direction} by {abs(distance)} pixels")
            
    async def type_text(self, text: str, selector: str = None) -> None:
        """
        Type text into an input field.
        
        Args:
            text (str): Text to type
            selector (str): CSS selector for the input field
        """
        if selector:
            # Type into a specific element
            await self.page.fill(selector, text)
            logger.info(f"Typed text into element with selector: {selector}")
        else:
            # Type into the focused element
            await self.page.keyboard.type(text)
            logger.info("Typed text into focused element")
            
    async def press_key(self, key: str) -> None:
        """
        Press a keyboard key.
        
        Args:
            key (str): Key to press (e.g., 'Enter', 'ArrowDown', 'Escape')
        """
        await self.page.keyboard.press(key)
        logger.info(f"Pressed key: {key}")
        
    async def hover_element(self, selector: str = None, 
                           position: Tuple[int, int] = None) -> None:
        """
        Hover over an element or position.
        
        Args:
            selector (str): CSS selector for the element
            position (Tuple[int, int]): X, Y coordinates to hover over
            
        Raises:
            ValueError: If neither selector nor position is provided
        """
        if position:
            # Hover at specific coordinates
            await self.page.mouse.move(position[0], position[1])
            logger.info(f"Hovered over position {position}")
            return
            
        if selector:
            # Hover over element by selector
            await self.page.hover(selector)
            logger.info(f"Hovered over element with selector: {selector}")
            return
            
        raise ValueError("Must provide selector or position to hover") 