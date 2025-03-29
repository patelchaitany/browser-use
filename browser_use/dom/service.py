"""
DOM service for extracting and manipulating DOM elements.
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from playwright.async_api import Page

from browser_use.utils.logger import setup_logger

logger = setup_logger(__name__)

class DOMService:
    """
    Service for working with DOM elements in the browser.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the DOM service.
        
        Args:
            page (Page): Playwright page object
        """
        self.page = page
        self._js_path = Path(__file__).parent / "buildDomTree.js"
        
    async def build_dom_tree(self, highlight_elements: bool = False, 
                            focus_element: int = -1,
                            viewport_expansion: int = 500) -> Dict:
        """
        Build a tree representation of the DOM.
        
        Uses the buildDomTree.js script to extract interactive and useful elements
        from the current page.
        
        Args:
            highlight_elements (bool): Whether to highlight elements on the page
            focus_element (int): Index of element to focus (-1 for none)
            viewport_expansion (int): Expansion of viewport for element detection
            
        Returns:
            Dict: DOM tree representation
        """
        if not os.path.exists(self._js_path):
            raise FileNotFoundError(f"Could not find buildDomTree.js at {self._js_path}")
        
        with open(self._js_path, "r") as f:
            js_code = f.read()
            
        args = {
            "doHighlightElements": highlight_elements,
            "focusHighlightIndex": focus_element,
            "viewportExpansion": viewport_expansion
        }
        
        try:
            # Execute the buildDomTree.js script in the browser
            result = await self.page.evaluate(js_code, args)
            
            # If the result is already a string, parse it to a dictionary
            if isinstance(result, str):
                result = json.loads(result)
                
            return result
        except Exception as e:
            logger.error(f"Error building DOM tree: {e}")
            raise
            
    async def get_element_by_id(self, element_id: str) -> Dict:
        """
        Get element details by its ID.
        
        Args:
            element_id (str): Element ID
            
        Returns:
            Dict: Element details
        """
        js_code = """
        (elementId) => {
            const element = document.getElementById(elementId);
            if (!element) return null;
            
            const rect = element.getBoundingClientRect();
            return {
                id: elementId,
                tagName: element.tagName.toLowerCase(),
                text: element.innerText || element.textContent,
                attributes: Object.fromEntries(
                    Array.from(element.attributes).map(attr => [attr.name, attr.value])
                ),
                boundingBox: {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                }
            };
        }
        """
        return await self.page.evaluate(js_code, element_id)
        
    async def get_elements_by_selector(self, selector: str) -> List[Dict]:
        """
        Get elements by CSS selector.
        
        Args:
            selector (str): CSS selector
            
        Returns:
            List[Dict]: List of element details
        """
        js_code = """
        (selector) => {
            const elements = Array.from(document.querySelectorAll(selector));
            return elements.map((element, index) => {
                const rect = element.getBoundingClientRect();
                return {
                    index,
                    tagName: element.tagName.toLowerCase(),
                    text: element.innerText || element.textContent,
                    attributes: Object.fromEntries(
                        Array.from(element.attributes).map(attr => [attr.name, attr.value])
                    ),
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
        return await self.page.evaluate(js_code, selector)
        
    async def highlight_elements(self, elements: List[Dict], color: str = "red", 
                                duration: int = 1000) -> None:
        """
        Highlight elements on the page.
        
        Args:
            elements (List[Dict]): Elements to highlight
            color (str): Highlight color
            duration (int): Highlight duration in milliseconds
        """
        if not elements:
            return
            
        js_code = """
        (params) => {
            const elements = params.elements;
            const color = params.color;
            const duration = params.duration;
            
            // Create highlight elements
            const highlights = [];
            
            elements.forEach(element => {
                if (!element.boundingBox) return;
                
                const { x, y, width, height } = element.boundingBox;
                
                // Create highlight element
                const highlight = document.createElement('div');
                highlight.style.position = 'absolute';
                highlight.style.border = `2px solid ${color}`;
                highlight.style.backgroundColor = `${color}33`;  // 20% opacity
                highlight.style.zIndex = '10000';
                highlight.style.pointerEvents = 'none';
                highlight.style.top = `${y}px`;
                highlight.style.left = `${x}px`;
                highlight.style.width = `${width}px`;
                highlight.style.height = `${height}px`;
                
                document.body.appendChild(highlight);
                highlights.push(highlight);
            });
            
            // Remove highlights after duration
            setTimeout(() => {
                highlights.forEach(h => h.remove());
            }, duration);
        }
        """
        params = {
            "elements": elements,
            "color": color,
            "duration": duration
        }
        await self.page.evaluate(js_code, params)
        
    async def get_element_by_text(self, text: str, 
                                exact_match: bool = False) -> Optional[Dict]:
        """
        Get an element by its text content.
        
        Args:
            text (str): Text to search for
            exact_match (bool): Whether to require an exact match
            
        Returns:
            Optional[Dict]: Element details if found, None otherwise
        """
        js_code = """
        (params) => {
            const text = params.text;
            const exactMatch = params.exactMatch;
            
            const walkDOM = (node, callback) => {
                callback(node);
                node = node.firstChild;
                while (node) {
                    walkDOM(node, callback);
                    node = node.nextSibling;
                }
            };
            
            let foundElement = null;
            
            walkDOM(document.body, (node) => {
                if (node.nodeType === 3) {  // Text node
                    const nodeText = node.textContent.trim();
                    if (exactMatch ? nodeText === text : nodeText.includes(text)) {
                        foundElement = node.parentElement;
                    }
                }
            });
            
            if (!foundElement) return null;
            
            const rect = foundElement.getBoundingClientRect();
            return {
                tagName: foundElement.tagName.toLowerCase(),
                text: foundElement.innerText || foundElement.textContent,
                attributes: Object.fromEntries(
                    Array.from(foundElement.attributes).map(attr => [attr.name, attr.value])
                ),
                boundingBox: {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                }
            };
        }
        """
        params = {
            "text": text,
            "exactMatch": exact_match
        }
        return await self.page.evaluate(js_code, params) 