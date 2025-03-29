"""
Extraction service for extracting data from web pages.
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from playwright.async_api import Page

from browser_use.dom.service import DOMService
from browser_use.utils.logger import setup_logger

logger = setup_logger(__name__)

class ExtractionService:
    """
    Service for extracting data from web pages.
    
    Provides methods for:
    - Extracting links
    - Extracting interactive elements
    - Taking screenshots with bounding boxes
    """
    
    def __init__(self, page: Page, dom_service: DOMService):
        """
        Initialize the extraction service.
        
        Args:
            page (Page): Playwright page object
            dom_service (DOMService): DOM service for working with DOM elements
        """
        self.page = page
        self.dom_service = dom_service
        
    async def extract_links(self, draw_boxes: bool = False) -> List[Dict]:
        """
        Extract all links from the current page.
        
        Args:
            draw_boxes (bool): Whether to highlight links on the page
            
        Returns:
            List[Dict]: List of dictionaries containing link information
        """
        js_code = """
        () => {
            const links = Array.from(document.querySelectorAll('a[href]'));
            return links.map((link, index) => {
                const rect = link.getBoundingClientRect();
                return {
                    index,
                    href: link.href,
                    text: link.innerText || link.textContent,
                    title: link.title,
                    visible: rect.width > 0 && rect.height > 0,
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }
                };
            });
        }
        """
        
        links = await self.page.evaluate(js_code)
        
        # Filter out links that are not visible
        visible_links = [link for link in links if link["visible"]]
        
        # Optionally highlight the links
        if draw_boxes and visible_links:
            await self.dom_service.highlight_elements(visible_links, color="blue")
            
        logger.info(f"Extracted {len(visible_links)} visible links from page")
        return visible_links
        
    async def extract_interactive_elements(self, draw_boxes: bool = False) -> List[Dict]:
        """
        Extract all interactive elements from the current page.
        
        Uses the DOM service's build_dom_tree method to get a complete DOM tree
        and extracts interactive elements from it.
        
        Args:
            draw_boxes (bool): Whether to highlight elements on the page
            
        Returns:
            List[Dict]: List of dictionaries containing element information
        """
        # Build the DOM tree
        dom_tree = await self.dom_service.build_dom_tree(highlight_elements=draw_boxes)
        
        # Extract interactive elements from the DOM tree
        interactive_elements = self._extract_interactive_from_tree(dom_tree)
        
        logger.info(f"Extracted {len(interactive_elements)} interactive elements from page")
        return interactive_elements
        
    def _extract_interactive_from_tree(self, dom_tree: Dict) -> List[Dict]:
        """
        Extract interactive elements from a DOM tree.
        
        Args:
            dom_tree (Dict): DOM tree representation
            
        Returns:
            List[Dict]: List of interactive elements
        """
        interactive_elements = []
        
        def process_node(node):
            # Check if node is interactive
            if self._is_interactive_node(node):
                interactive_elements.append(self._format_interactive_element(node))
                
            # Process children
            if "children" in node and node["children"]:
                for child in node["children"]:
                    process_node(child)
        
        # Start processing from the root
        process_node(dom_tree)
        
        return interactive_elements
        
    def _is_interactive_node(self, node: Dict) -> bool:
        """
        Check if a node is interactive.
        
        Args:
            node (Dict): Node from DOM tree
            
        Returns:
            bool: True if node is interactive, False otherwise
        """
        # Interactive HTML tags
        interactive_tags = [
            "a", "button", "input", "select", "textarea", "details",
            "audio", "video", "iframe", "menuitem"
        ]
        
        # Check tag
        if "tagName" in node and node["tagName"].lower() in interactive_tags:
            return True
            
        # Check attributes
        if "attributes" in node:
            attrs = node["attributes"]
            
            # Check for role attribute
            if "role" in attrs and attrs["role"] in [
                "button", "link", "checkbox", "menuitem", "tab", "switch",
                "radio", "combobox", "slider", "menu", "menubar"
            ]:
                return True
                
            # Check for event handlers
            for attr in attrs:
                if attr.startswith("on") or attr == "onclick" or attr == "tabindex":
                    return True
                    
        return False
        
    def _format_interactive_element(self, node: Dict) -> Dict:
        """
        Format an interactive element for output.
        
        Args:
            node (Dict): Node from DOM tree
            
        Returns:
            Dict: Formatted element information
        """
        result = {
            "tagName": node.get("tagName", "unknown"),
            "text": node.get("text", ""),
            "attributes": node.get("attributes", {}),
        }
        
        # Add bounding box if available
        if "boundingBox" in node:
            result["boundingBox"] = node["boundingBox"]
            
        # Add href if it's a link
        if "attributes" in node and "href" in node["attributes"]:
            result["href"] = node["attributes"]["href"]
            
        return result
        
    async def take_screenshot(self, path: str, draw_boxes: bool = True, 
                             elements: Optional[List[Dict]] = None) -> str:
        """
        Take a screenshot of the current page with optional bounding boxes around elements.
        
        Args:
            path (str): Path to save the screenshot
            draw_boxes (bool): Whether to draw boxes around elements
            elements (Optional[List[Dict]]): Elements to highlight (if None, extract all interactive elements)
            
        Returns:
            str: Path to the saved screenshot
        """
        # Extract elements if not provided
        if draw_boxes and elements is None:
            elements = await self.extract_interactive_elements(draw_boxes=False)
            
        # Draw bounding boxes if requested
        if draw_boxes and elements:
            await self.dom_service.highlight_elements(elements, color="red", duration=2000)
            
        # Take screenshot
        await self.page.screenshot(path=path, full_page=True)
        
        logger.info(f"Screenshot saved to {path}")
        return path
        
    async def extract_structured_data(self) -> Dict:
        """
        Extract structured data from the page.
        
        Returns:
            Dict: Structured data extracted from the page
        """
        js_code = """
        () => {
            // Extract JSON-LD data
            const jsonLdData = Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                .map(script => {
                    try {
                        return JSON.parse(script.textContent);
                    } catch (e) {
                        return null;
                    }
                })
                .filter(data => data !== null);
                
            // Extract meta data
            const metaData = {};
            Array.from(document.querySelectorAll('meta[name], meta[property]'))
                .forEach(meta => {
                    const name = meta.getAttribute('name') || meta.getAttribute('property');
                    const content = meta.getAttribute('content');
                    if (name && content) {
                        metaData[name] = content;
                    }
                });
                
            // Extract main content
            let mainContent = "";
            const mainElement = document.querySelector('main') || 
                                document.querySelector('article') || 
                                document.querySelector('#main') ||
                                document.querySelector('.main');
            if (mainElement) {
                mainContent = mainElement.innerText;
            }
            
            // Return all structured data
            return {
                url: window.location.href,
                title: document.title,
                jsonLd: jsonLdData,
                meta: metaData,
                mainContent
            };
        }
        """
        
        structured_data = await self.page.evaluate(js_code)
        logger.info("Extracted structured data from page")
        return structured_data 