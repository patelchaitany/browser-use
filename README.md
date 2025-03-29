# Browser Use API for Python

A Python library for browser interaction and extraction of web page content. This library provides a simple API for automating web browser tasks, extracting structured information, and interacting with web pages.

## Features

### Extraction
- Extract all links from a web page
- Take screenshots with highlighted boxes around links
- Extract structured content (headings, paragraphs, links, images)

### Interaction
- Navigate to URLs
- Click elements (by identifier or by position)
- Type text into elements
- Scroll the page
- Wait for elements to appear on the page
- Highlight elements on the page for better visibility
- Dynamic element finding by scanning the entire page

## Installation

```bash
pip install -r requirements.txt
```

## Usage Examples

### Basic Browser Initialization

```python
from browser_use import BrowserUse

# Initialize a browser (Chrome by default)
browser = BrowserUse(headless=False)

# Navigate to a URL
browser.navigate("https://www.example.com")

# Close the browser when done
browser.close()
```

### Extracting Links and Taking Screenshots

```python
# Extract all links from the current page
links = browser.extract_links()
for link in links:
    print(f"Text: {link['text']}, URL: {link['href']}")

# Take a screenshot with boxes around links
screenshot_path = "example_screenshot.png"
browser.screenshot_with_link_boxes(screenshot_path)
print(f"Screenshot saved to {screenshot_path}")

# Extract structured content
content = browser.extract_page_content()
print(f"Page title: {content['title']}")
print(f"Number of headings: {len(content['headings'])}")
print(f"Number of paragraphs: {len(content['paragraphs'])}")
```

### Interacting with the Page

```python
# Click an element by CSS selector (with highlighting)
browser.click_element("#submit-button", highlight=True)

# Click an element by visible text
browser.click_element("Sign In", by=None, highlight=True)  # Uses text search

# Click at specific coordinates
browser.click_element(position=(100, 200))

# Type text into an input field with element highlighting
browser.type_text("Hello, world!", "#search-box", highlight=True)

# Scroll the page
browser.scroll(direction="down", amount=500)
browser.scroll(direction="bottom")  # Scroll to the bottom of the page

# Wait for an element to appear
element = browser.wait_for_element("#loading-complete", timeout=15)
```

### Finding and Highlighting Elements

```python
# Find and highlight an element by CSS selector
element = browser.find_and_highlight("#main-heading", duration=3)

# Find and highlight an element by text
element = browser.find_and_highlight("Sign In", by=None, duration=2)

# Highlight an existing WebElement
element = browser.wait_for_element("#loading-complete")
browser.highlight_element(element, color="green", border_width=5, duration=3)
```

### Dynamic Element Finding

```python
# Scan the page for all interactive elements (with highlighting)
elements = browser.scan_interactive_elements(highlight=True)
print(f"Found {len(elements)} interactive elements")

# Find elements by their content (text or attributes)
element = browser.find_element_by_content("Add to Cart", highlight=True)

# Find elements by content with type filtering
button = browser.find_element_by_content("Submit", element_type="button")

# Clear all highlights from the page
browser.clear_highlights()
```

### Error Handling

```python
from browser_use.utils.exceptions import ElementNotFoundException, BrowserOperationError

try:
    browser.click_element("Non-existent element")
except ElementNotFoundException as e:
    print(f"Element not found: {e}")
except BrowserOperationError as e:
    print(f"Browser operation failed: {e}")
```

## Requirements

- Python 3.7 or later
- Chrome browser and appropriate ChromeDriver (automatically managed)

## Dependencies

- selenium
- webdriver-manager
- Pillow (PIL) 