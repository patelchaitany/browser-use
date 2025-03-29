from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import json
from PIL import Image, ImageDraw
from io import BytesIO
import base64

from browser_use.utils.element_finder import find_element_by_text, get_clickable_elements
from browser_use.utils.exceptions import ElementNotFoundException, BrowserOperationError


class BrowserUse:
    """
    A class for browser interactions and data extraction using Selenium WebDriver.
    """
    def __init__(self, headless=False, browser_type="chrome"):
        """
        Initialize the browser instance.
        
        Args:
            headless (bool): Whether to run browser in headless mode
            browser_type (str): Type of browser to use (only "chrome" supported currently)
        """
        self.browser_type = browser_type.lower()
        
        if self.browser_type == "chrome":
            options = Options()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
        
        # Set default timeout for finding elements
        self.timeout = 10
        
    def __del__(self):
        """Clean up resources when object is destroyed"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except:
            pass
            
    def navigate(self, url):
        """
        Navigate to specified URL
        
        Args:
            url (str): URL to navigate to
            
        Returns:
            bool: True if navigation successful
        """
        try:
            self.driver.get(url)
            return True
        except Exception as e:
            raise BrowserOperationError(f"Failed to navigate to {url}: {str(e)}")
    
    # --- EXTRACTION METHODS ---
    
    def extract_links(self):
        """
        Extract all links from the current page
        
        Returns:
            list: Dictionary objects containing {'text': link_text, 'href': link_url, 'location': {'x': x, 'y': y}}
        """
        try:
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            result = []
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip() or link.get_attribute('aria-label') or href
                    location = link.location
                    size = link.size
                    
                    if href:  # Only include links with a valid href
                        result.append({
                            'text': text,
                            'href': href,
                            'location': {
                                'x': location['x'],
                                'y': location['y'],
                                'width': size['width'],
                                'height': size['height']
                            }
                        })
                except:
                    # Skip links that can't be processed
                    continue
                    
            return result
        except Exception as e:
            raise BrowserOperationError(f"Failed to extract links: {str(e)}")
    
    def screenshot_with_link_boxes(self, output_path=None):
        """
        Take a screenshot of the current page with boxes around all links
        
        Args:
            output_path (str, optional): Path to save the screenshot, if None returns PIL Image
            
        Returns:
            str or PIL.Image: Path to saved image or PIL Image object if output_path is None
        """
        try:
            # Get the page screenshot
            screenshot = self.driver.get_screenshot_as_png()
            img = Image.open(BytesIO(screenshot))
            draw = ImageDraw.Draw(img)
            
            # Get all links and draw boxes
            links = self.extract_links()
            for link in links:
                loc = link['location']
                x, y = loc['x'], loc['y']
                width, height = loc['width'], loc['height']
                
                # Draw red rectangle around the link
                draw.rectangle(
                    [(x, y), (x + width, y + height)],
                    outline="red",
                    width=2
                )
            
            if output_path:
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                img.save(output_path)
                return output_path
            else:
                return img
        except Exception as e:
            raise BrowserOperationError(f"Failed to create screenshot with link boxes: {str(e)}")
    
    def extract_page_content(self):
        """
        Extract structured content from the current page
        
        Returns:
            dict: Dictionary with page title, headings, paragraphs, and links
        """
        try:
            content = {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'headings': [],
                'paragraphs': [],
                'links': self.extract_links(),
                'images': []
            }
            
            # Extract headings
            for level in range(1, 7):
                headings = self.driver.find_elements(By.TAG_NAME, f'h{level}')
                for heading in headings:
                    content['headings'].append({
                        'level': level,
                        'text': heading.text.strip(),
                        'location': heading.location
                    })
            
            # Extract paragraphs
            paragraphs = self.driver.find_elements(By.TAG_NAME, 'p')
            for para in paragraphs:
                if para.text.strip():
                    content['paragraphs'].append({
                        'text': para.text.strip(),
                        'location': para.location
                    })
            
            # Extract images
            images = self.driver.find_elements(By.TAG_NAME, 'img')
            for img in images:
                try:
                    src = img.get_attribute('src')
                    alt = img.get_attribute('alt') or ''
                    
                    if src:
                        content['images'].append({
                            'src': src,
                            'alt': alt,
                            'location': img.location,
                            'size': img.size
                        })
                except:
                    continue
            
            return content
        except Exception as e:
            raise BrowserOperationError(f"Failed to extract page content: {str(e)}")
    
    # --- INTERACTION METHODS ---
    
    def highlight_element(self, element, duration=2, color="yellow", border_width=2):
        """
        Highlight an element on the page by changing its style
        
        Args:
            element: The WebElement to highlight
            duration (int): How long to highlight the element (in seconds)
            color (str): Color name or hex code for the highlight
            border_width (int): Width of the highlight border in pixels
            
        Returns:
            bool: True if highlighting was successful
        """
        try:
            # Store the original style to revert back after highlighting
            original_style = self.driver.execute_script("return arguments[0].getAttribute('style');", element)
            
            # Add a highlight style
            style = f"border: {border_width}px solid {color}; background-color: rgba(255, 255, 0, 0.3);"
            self.driver.execute_script(f"arguments[0].setAttribute('style', '{style}');", element)
            
            # Keep the highlight for the specified duration
            if duration > 0:
                time.sleep(duration)
                
                # Revert to original style
                if original_style:
                    self.driver.execute_script(f"arguments[0].setAttribute('style', '{original_style}');", element)
                else:
                    self.driver.execute_script("arguments[0].removeAttribute('style');", element)
            
            return True
        except Exception as e:
            raise BrowserOperationError(f"Failed to highlight element: {str(e)}")
    
    def find_and_highlight(self, element_identifier, by=By.CSS_SELECTOR, duration=2):
        """
        Find an element and highlight it on the page
        
        Args:
            element_identifier (str): Element identifier (CSS selector by default)
            by (selenium.webdriver.common.by.By, optional): Method to find element
            duration (int): How long to highlight the element (in seconds)
            
        Returns:
            WebElement: The found and highlighted element
        """
        try:
            # First try to find the element using the provided selector
            try:
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((by, element_identifier))
                )
            except TimeoutException:
                # If the selector fails, try to find by visible text
                try:
                    element = find_element_by_text(self.driver, element_identifier)
                except:
                    raise ElementNotFoundException(f"Element not found with identifier: {element_identifier}")
            
            # Highlight the element
            self.highlight_element(element, duration)
            
            return element
            
        except ElementNotFoundException as e:
            raise e
        except Exception as e:
            raise BrowserOperationError(f"Failed to find and highlight element: {str(e)}")
    
    def scan_interactive_elements(self, highlight=True, include_hidden=False):
        """
        Scan the entire page and identify all potentially interactive elements
        
        Args:
            highlight (bool): Whether to highlight found elements
            include_hidden (bool): Whether to include non-visible elements
            
        Returns:
            list: List of dictionaries containing element information
        """
        try:
            # JavaScript to find and analyze all interactive elements on the page
            script = """
            return (function() {
                const interactiveElements = [];
                let highlightIndex = 0;
                
                // Helper function to check if element is visible
                function isElementVisible(element) {
                    if (!element) return false;
                    
                    const style = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    
                    return (
                        element.offsetWidth > 0 &&
                        element.offsetHeight > 0 &&
                        style.visibility !== "hidden" &&
                        style.display !== "none" &&
                        rect.width > 0 &&
                        rect.height > 0
                    );
                }
                
                // Helper function to check if an element is interactive
                function isInteractiveElement(element) {
                    if (!element || element.nodeType !== Node.ELEMENT_NODE) {
                        return false;
                    }
                    
                    // Check for interactive cursor
                    const style = window.getComputedStyle(element);
                    const interactiveCursors = ["pointer", "move", "text", "grab", "cell"];
                    if (interactiveCursors.includes(style.cursor)) return true;
                    
                    // Base interactive elements and roles
                    const interactiveElements = [
                        "a", "button", "details", "embed", "input", "menu", "menuitem",
                        "object", "select", "textarea", "canvas", "summary", "dialog"
                    ];
                    
                    const interactiveRoles = [
                        "button", "link", "checkbox", "radio", "menuitem", "option", 
                        "switch", "tab", "textbox", "combobox", "slider", "searchbox"
                    ];
                    
                    const tagName = element.tagName.toLowerCase();
                    const role = element.getAttribute("role");
                    const tabIndex = element.getAttribute("tabindex");
                    
                    // Check for common interactive attributes
                    if (
                        interactiveElements.includes(tagName) ||
                        (role && interactiveRoles.includes(role)) ||
                        element.onclick !== null ||
                        element.getAttribute("onclick") !== null ||
                        element.classList.contains("button") ||
                        element.getAttribute("aria-haspopup") === "true" ||
                        element.contentEditable === "true" ||
                        element.isContentEditable ||
                        element.draggable ||
                        (tabIndex !== null && tabIndex !== "-1") ||
                        element.getAttribute("data-action") !== null
                    ) {
                        return true;
                    }
                    
                    // Check ARIA properties 
                    if (
                        element.hasAttribute("aria-expanded") ||
                        element.hasAttribute("aria-pressed") ||
                        element.hasAttribute("aria-selected") ||
                        element.hasAttribute("aria-checked")
                    ) {
                        return true;
                    }
                    
                    return false;
                }
                
                // Helper function to get element XPath
                function getElementXPath(element) {
                    if (!element) return "";
                    
                    const parts = [];
                    while (element && element.nodeType === Node.ELEMENT_NODE) {
                        let index = 0;
                        let sibling = element.previousSibling;
                        while (sibling) {
                            if (sibling.nodeType === Node.ELEMENT_NODE && 
                                sibling.tagName === element.tagName) {
                                index++;
                            }
                            sibling = sibling.previousSibling;
                        }
                        
                        const tagName = element.tagName.toLowerCase();
                        const indexStr = index > 0 ? `[${index+1}]` : "";
                        parts.unshift(`${tagName}${indexStr}`);
                        element = element.parentNode;
                    }
                    
                    return "/" + parts.join("/");
                }
                
                // Function to process an element and its children
                function processElement(element, depth = 0, maxDepth = 20) {
                    if (!element || depth > maxDepth) return;
                    
                    // Check if this element is interactive
                    const isVisible = arguments[1] || isElementVisible(element);
                    if ((isVisible || arguments[1]) && isInteractiveElement(element)) {
                        const rect = element.getBoundingClientRect();
                        
                        // Get basic element information
                        const elementInfo = {
                            tagName: element.tagName.toLowerCase(),
                            id: element.id || null,
                            className: element.className || null,
                            text: element.textContent?.trim().substring(0, 100) || null,
                            xpath: getElementXPath(element),
                            attributes: {},
                            location: {
                                x: rect.left,
                                y: rect.top,
                                width: rect.width,
                                height: rect.height
                            },
                            isVisible: isVisible,
                            highlightIndex: highlightIndex++
                        };
                        
                        // Get important attributes
                        const importantAttrs = [
                            "role", "href", "src", "alt", "title", "aria-label",
                            "name", "value", "placeholder", "type", "action", "method"
                        ];
                        
                        for (const attr of importantAttrs) {
                            if (element.hasAttribute(attr)) {
                                elementInfo.attributes[attr] = element.getAttribute(attr);
                            }
                        }
                        
                        interactiveElements.push(elementInfo);
                    }
                    
                    // Process child elements
                    for (const child of element.children) {
                        processElement(child, depth + 1, maxDepth);
                    }
                    
                    // Process shadow DOM if present
                    if (element.shadowRoot) {
                        for (const child of element.shadowRoot.children) {
                            processElement(child, depth + 1, maxDepth);
                        }
                    }
                }
                
                // Start processing from the body
                processElement(document.body, false, """ + str(include_hidden).lower() + """);
                
                return interactiveElements;
            })();
            """
            
            # Execute the JavaScript to find all interactive elements
            elements = self.driver.execute_script(script)
            
            # Highlight elements if requested
            if highlight and elements:
                for element in elements:
                    if element['isVisible']:
                        # Construct a unique XPath for the element
                        xpath = element['xpath']
                        try:
                            # Find the element using XPath
                            web_element = self.driver.find_element(By.XPATH, xpath)
                            # Highlight with a different color based on index
                            color_index = element['highlightIndex'] % 10
                            colors = [
                                "#FF0000", "#00FF00", "#0000FF", "#FF00FF", "#00FFFF",
                                "#FFFF00", "#FFA500", "#800080", "#008080", "#FF69B4"
                            ]
                            self.highlight_element(
                                web_element, 
                                duration=0,  # Don't automatically remove highlight
                                color=colors[color_index],
                                border_width=2
                            )
                        except Exception as e:
                            # Skip elements that can't be highlighted
                            continue
            
            return elements
            
        except Exception as e:
            raise BrowserOperationError(f"Failed to scan interactive elements: {str(e)}")
    
    def find_element_by_content(self, text_or_pattern, element_type=None, highlight=True):
        """
        Find an element by scanning the page for matching content
        
        Args:
            text_or_pattern (str): Text or pattern to look for
            element_type (str, optional): Filter by element type (e.g., 'button', 'link')
            highlight (bool): Whether to highlight the found element
            
        Returns:
            WebElement: The found element
        """
        try:
            # Scan all interactive elements
            elements = self.scan_interactive_elements(highlight=False, include_hidden=False)
            
            text_or_pattern = text_or_pattern.lower()
            matched_elements = []
            
            for element in elements:
                # Skip if element type filter is provided and doesn't match
                if element_type and element['tagName'] != element_type.lower():
                    continue
                
                # Check element text content
                if element['text'] and text_or_pattern in element['text'].lower():
                    matched_elements.append(element)
                    continue
                
                # Check important attributes like aria-label, title, alt, etc.
                for attr_name, attr_value in element['attributes'].items():
                    if attr_value and text_or_pattern in attr_value.lower():
                        matched_elements.append(element)
                        break
            
            if not matched_elements:
                raise ElementNotFoundException(f"No element found matching: {text_or_pattern}")
            
            # Sort by visibility and closest match
            matched_elements.sort(key=lambda e: (
                not e['isVisible'],  # Visible elements first
                0 if e['text'] and e['text'].lower() == text_or_pattern else 1,  # Exact text match first
                0 if any(v and v.lower() == text_or_pattern for v in element['attributes'].values()) else 1  # Exact attribute match
            ))
            
            # Get the best match
            best_match = matched_elements[0]
            
            # Find the element using its XPath
            web_element = self.driver.find_element(By.XPATH, best_match['xpath'])
            
            # Highlight the element if requested
            if highlight:
                self.highlight_element(web_element, duration=2)
            
            return web_element
            
        except ElementNotFoundException as e:
            raise e
        except Exception as e:
            raise BrowserOperationError(f"Failed to find element by content: {str(e)}")
    
    def clear_highlights(self):
        """
        Clear all current element highlights from the page
        
        Returns:
            bool: True if successful
        """
        try:
            # Execute JavaScript to remove all highlights
            script = """
            const elements = document.querySelectorAll('*');
            for (let i = 0; i < elements.length; i++) {
                const element = elements[i];
                if (element.hasAttribute('style') && 
                    (element.getAttribute('style').includes('border:') || 
                     element.getAttribute('style').includes('background-color:'))) {
                    element.removeAttribute('style');
                }
            }
            return true;
            """
            self.driver.execute_script(script)
            return True
        except Exception as e:
            raise BrowserOperationError(f"Failed to clear highlights: {str(e)}")
    
    def click_element(self, element_identifier=None, position=None, by=By.CSS_SELECTOR, highlight=True):
        """
        Click an element on the page either by identifier or position
        
        Args:
            element_identifier (str, optional): Element identifier (CSS selector by default)
            position (tuple, optional): (x, y) coordinates to click
            by (selenium.webdriver.common.by.By, optional): Method to find element
            highlight (bool): Whether to highlight the element before clicking
            
        Returns:
            bool: True if click was successful
        """
        try:
            if position:
                # Click at specific position
                x, y = position
                actions = ActionChains(self.driver)
                actions.move_by_offset(x, y).click().perform()
                return True
                
            elif element_identifier:
                # First, try to find by standard methods
                try:
                    # Try explicit selector/identifier
                    if by != By.XPATH or by != By.CSS_SELECTOR:
                        element = WebDriverWait(self.driver, self.timeout).until(
                            EC.element_to_be_clickable((by, element_identifier))
                        )
                    else:
                        # Try content-based search for text or pattern
                        element = self.find_element_by_content(element_identifier, highlight=False)
                    
                    # Highlight the element if requested
                    if highlight:
                        self.highlight_element(element, duration=1)
                        
                    element.click()
                    return True
                except (TimeoutException, ElementNotFoundException):
                    # If standard methods fail, try with our dynamic scanner
                    try:
                        element = self.find_element_by_content(element_identifier, highlight=highlight)
                        element.click()
                        return True
                    except ElementNotFoundException:
                        raise ElementNotFoundException(f"Element not found with identifier: {element_identifier}")
            else:
                raise ValueError("Either element_identifier or position must be provided")
                
        except ElementNotFoundException as e:
            raise e
        except Exception as e:
            raise BrowserOperationError(f"Failed to click element: {str(e)}")
    
    def type_text(self, text, element_identifier=None, by=By.CSS_SELECTOR, highlight=True):
        """
        Type text into an element
        
        Args:
            text (str): Text to type
            element_identifier (str, optional): Element to type into (if None, types at current focus)
            by (selenium.webdriver.common.by.By, optional): Method to find element
            highlight (bool): Whether to highlight the element before typing
            
        Returns:
            bool: True if typing was successful
        """
        try:
            if element_identifier:
                try:
                    element = WebDriverWait(self.driver, self.timeout).until(
                        EC.element_to_be_clickable((by, element_identifier))
                    )
                    
                    # Highlight the element if requested
                    if highlight:
                        self.highlight_element(element, duration=1)
                        
                except TimeoutException:
                    raise ElementNotFoundException(f"Element not found with identifier: {element_identifier}")
                
                element.clear()
                element.send_keys(text)
            else:
                # Type at current focus
                actions = ActionChains(self.driver)
                actions.send_keys(text).perform()
                
            return True
        except ElementNotFoundException as e:
            raise e
        except Exception as e:
            raise BrowserOperationError(f"Failed to type text: {str(e)}")
    
    def scroll(self, direction="down", amount=300):
        """
        Scroll the page
        
        Args:
            direction (str): "up", "down", "left", "right", "top", or "bottom"
            amount (int): Pixels to scroll (ignored for "top" and "bottom")
            
        Returns:
            bool: True if scroll was successful
        """
        try:
            if direction == "top":
                self.driver.execute_script("window.scrollTo(0, 0);")
            elif direction == "bottom":
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            elif direction == "up":
                self.driver.execute_script(f"window.scrollBy(0, -{amount});")
            elif direction == "down":
                self.driver.execute_script(f"window.scrollBy(0, {amount});")
            elif direction == "left":
                self.driver.execute_script(f"window.scrollBy(-{amount}, 0);")
            elif direction == "right":
                self.driver.execute_script(f"window.scrollBy({amount}, 0);")
            else:
                raise ValueError(f"Invalid scroll direction: {direction}")
                
            return True
        except Exception as e:
            raise BrowserOperationError(f"Failed to scroll: {str(e)}")
    
    def wait_for_element(self, element_identifier, timeout=None, by=By.CSS_SELECTOR):
        """
        Wait for an element to be present on the page
        
        Args:
            element_identifier (str): Element identifier
            timeout (int, optional): Timeout in seconds (uses default if None)
            by (selenium.webdriver.common.by.By, optional): Method to find element
            
        Returns:
            WebElement: The found element
        """
        if timeout is None:
            timeout = self.timeout
            
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, element_identifier))
            )
            return element
        except TimeoutException:
            raise ElementNotFoundException(f"Element not found with identifier: {element_identifier}")
        except Exception as e:
            raise BrowserOperationError(f"Failed to wait for element: {str(e)}")
            
    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit() 