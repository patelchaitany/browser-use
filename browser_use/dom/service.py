import gc
import json
import logging
import os
from dataclasses import dataclass
from importlib import resources
from typing import TYPE_CHECKING, Optional, Tuple, Dict, List, Union, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from playwright.async_api import Page

from browser_use.dom.views import (
    DOMElementNode,
    DOMState,
    DOMTextNode,
    SelectorMap,
    ViewportInfo,
)
from browser_use.utils import time_execution_async

logger = logging.getLogger(__name__)


class DomService:
    def __init__(self, page: 'Page'):
        self.page = page
        self.xpath_cache = {}
        
        # Read the JS code from the file
        js_file_path = os.path.join(os.path.dirname(__file__), 'buildDomTree.js')
        with open(js_file_path, 'r') as file:
            self.js_code = file.read()

    @time_execution_async('--get_clickable_elements')
    async def get_clickable_elements(
        self,
        highlight_elements: bool = True,
        focus_element: int = -1,
        viewport_expansion: int = 0,
    ) -> DOMState:
        """
        Extract all clickable elements from the page and highlight them if requested.
        
        Args:
            highlight_elements: Whether to highlight the elements in the browser
            focus_element: The index of the element to focus on (-1 for none)
            viewport_expansion: How much to expand the viewport for detection
            
        Returns:
            A DOMState object containing the element tree and selector map
        """
        element_tree, selector_map = await self._build_dom_tree(highlight_elements, focus_element, viewport_expansion)
        return DOMState(element_tree=element_tree, selector_map=selector_map)

    @time_execution_async('--get_cross_origin_iframes')
    async def get_cross_origin_iframes(self) -> list[str]:
        """
        Get a list of cross-origin iframes in the page that might contain interactive elements.
        Filters out hidden iframes used for ads and tracking.
        
        Returns:
            List of iframe URLs
        """
        # invisible cross-origin iframes are used for ads and tracking, dont open those
        hidden_frame_urls = await self.page.locator('iframe').filter(visible=False).evaluate_all('e => e.map(e => e.src)')

        is_ad_url = lambda url: any(
            domain in urlparse(url).netloc for domain in ('doubleclick.net', 'adroll.com', 'googletagmanager.com')
        )

        return [
            frame.url
            for frame in self.page.frames
            if urlparse(frame.url).netloc  # exclude data:urls and about:blank
            and urlparse(frame.url).netloc != urlparse(self.page.url).netloc  # exclude same-origin iframes
            and frame.url not in hidden_frame_urls  # exclude hidden frames
            and not is_ad_url(frame.url)  # exclude most common ad network tracker frame URLs
        ]

    @time_execution_async('--build_dom_tree')
    async def _build_dom_tree(
        self,
        highlight_elements: bool,
        focus_element: int,
        viewport_expansion: int,
    ) -> Tuple[DOMElementNode, SelectorMap]:
        """
        Build a DOM tree of the page and extract interactive elements.
        
        Args:
            highlight_elements: Whether to highlight the elements in the browser
            focus_element: The index of the element to focus on (-1 for none)
            viewport_expansion: How much to expand the viewport for detection
            
        Returns:
            A tuple containing the element tree and selector map
        """
        if await self.page.evaluate('1+1') != 2:
            raise ValueError('The page cannot evaluate javascript code properly')

        if self.page.url == 'about:blank':
            # short-circuit if the page is a new empty tab for speed, no need to inject buildDomTree.js
            return (
                DOMElementNode(
                    tag_name='body',
                    xpath='',
                    attributes={},
                    children=[],
                    is_visible=False,
                ),
                {},
            )

        # Execute JS code in the browser to extract important DOM information
        debug_mode = logger.getEffectiveLevel() == logging.DEBUG
        args = {
            'doHighlightElements': highlight_elements,
            'focusHighlightIndex': focus_element,
            'viewportExpansion': viewport_expansion,
            'debugMode': debug_mode,
        }

        try:
            eval_page: dict = await self.page.evaluate(self.js_code, args)
        except Exception as e:
            logger.error('Error evaluating JavaScript: %s', e)
            raise

        # Only log performance metrics in debug mode
        if debug_mode and 'perfMetrics' in eval_page:
            logger.debug(
                'DOM Tree Building Performance Metrics for: %s\n%s',
                self.page.url,
                json.dumps(eval_page['perfMetrics'], indent=2),
            )

        return await self._construct_dom_tree(eval_page)

    @time_execution_async('--construct_dom_tree')
    async def _construct_dom_tree(
        self,
        eval_page: dict,
    ) -> Tuple[DOMElementNode, SelectorMap]:
        """
        Construct a DOM tree from the JavaScript evaluation result.
        
        Args:
            eval_page: The result of evaluating the buildDomTree.js
            
        Returns:
            A tuple containing the element tree and selector map
        """
        js_node_map = eval_page['map']
        js_root_id = eval_page['rootId']

        selector_map = {}
        node_map = {}

        for id, node_data in js_node_map.items():
            node, children_ids = self._parse_node(node_data)
            if node is None:
                continue

            node_map[id] = node

            if isinstance(node, DOMElementNode) and node.highlight_index is not None:
                selector_map[node.highlight_index] = node

            # We know that we are building the tree bottom up
            # and all children are already processed.
            if isinstance(node, DOMElementNode):
                for child_id in children_ids:
                    if child_id not in node_map:
                        continue

                    child_node = node_map[child_id]

                    child_node.parent = node
                    node.children.append(child_node)

        html_to_dict = node_map[str(js_root_id)]

        del node_map
        del js_node_map
        del js_root_id

        gc.collect()

        if html_to_dict is None or not isinstance(html_to_dict, DOMElementNode):
            raise ValueError('Failed to parse HTML to dictionary')

        return html_to_dict, selector_map

    def _parse_node(
        self,
        node_data: dict,
    ) -> Tuple[Optional[Union[DOMElementNode, DOMTextNode]], List[int]]:
        """
        Parse a node from the JavaScript evaluation result.
        
        Args:
            node_data: The node data from the JavaScript evaluation
            
        Returns:
            A tuple containing the parsed node and a list of child IDs
        """
        if not node_data:
            return None, []

        # Process text nodes immediately
        if node_data.get('type') == 'TEXT_NODE':
            text_node = DOMTextNode(
                text=node_data['text'],
                is_visible=node_data['isVisible'],
            )
            return text_node, []

        # Process coordinates if they exist for element nodes
        viewport_info = None

        if 'viewport' in node_data:
            viewport_info = ViewportInfo(
                width=node_data['viewport']['width'],
                height=node_data['viewport']['height'],
            )

        element_node = DOMElementNode(
            tag_name=node_data['tagName'],
            xpath=node_data['xpath'],
            attributes=node_data.get('attributes', {}),
            is_visible=node_data.get('isVisible', False),
            is_interactive=node_data.get('isInteractive', False),
            is_top_element=node_data.get('isTopElement', False),
            is_in_viewport=node_data.get('isInViewport', False),
            highlight_index=node_data.get('highlightIndex'),
            shadow_root=node_data.get('shadowRoot', False),
            viewport_info=viewport_info,
        )

        children_ids = node_data.get('children', [])

        return element_node, children_ids

    async def take_screenshot_with_highlights(self, output_path: str) -> str:
        """
        Take a screenshot of the page with highlighted elements.
        
        Args:
            output_path: The path to save the screenshot to
            
        Returns:
            The path to the saved screenshot
        """
        await self.page.screenshot(path=output_path, full_page=True)
        return output_path
        
    async def click_element(self, highlight_index: int) -> bool:
        """
        Click an element by its highlight index.
        
        Args:
            highlight_index: The highlight index of the element to click
            
        Returns:
            True if the element was clicked, False otherwise
        """
        dom_state = await self.get_clickable_elements()
        if highlight_index in dom_state.selector_map:
            element = dom_state.selector_map[highlight_index]
            xpath = element.xpath
            
            try:
                # Click the element by xpath
                element_handle = await self.page.wait_for_selector(f"xpath={xpath}", timeout=2000)
                if element_handle:
                    await element_handle.click()
                    return True
            except Exception as e:
                logger.error(f"Error clicking element with xpath {xpath}: {e}")
        
        return False 