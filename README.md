# Browser Use API for Python

A Python API for browser interaction and data extraction. This API allows you to:

- Extract useful links and interactive elements from web pages
- Take screenshots with bounding boxes around links and elements
- Interact with the browser (clicking, scrolling, typing)
- Extract data in a structured manner

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/browser-use.git
cd browser-use
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Example

```python
import asyncio
from browser_use import BrowserUse

async def main():
    # Initialize the browser (headless mode)
    async with BrowserUse(headless=True) as browser:
        # Navigate to a URL
        await browser.goto("https://example.com")
        
        # Extract all links and take a screenshot with boxes around them
        links = await browser.extract_links(draw_boxes=True)
        await browser.take_screenshot("example_links.png")
        
        # Print the extracted links
        for link in links:
            print(f"Link: {link['text']} -> {link['href']}")
            
        # Extract interactive elements
        elements = await browser.extract_interactive_elements(draw_boxes=True)
        await browser.take_screenshot("example_elements.png")
        
        # Click a button on the page
        await browser.click_element(element_name="Submit")
        
        # Type text into an input field
        await browser.type_text("Hello, world!", selector="input[name='search']")
        
        # Extract structured data from the page
        data = await browser.extraction_service.extract_structured_data()
        print(f"Page title: {data['title']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Extraction Examples

#### Extract Links

```python
# Extract all links from the page
links = await browser.extract_links()

# Extract links and highlight them on the page
links = await browser.extract_links(draw_boxes=True)
```

#### Extract Interactive Elements

```python
# Extract all interactive elements from the page
elements = await browser.extract_interactive_elements()

# Extract and highlight interactive elements
elements = await browser.extract_interactive_elements(draw_boxes=True)
```

#### Take Screenshots

```python
# Take a screenshot of the current page
await browser.take_screenshot("screenshot.png")

# Take a screenshot with bounding boxes around elements
await browser.take_screenshot("screenshot_with_boxes.png", draw_boxes=True)
```

### Interaction Examples

#### Click Elements

```python
# Click by selector
await browser.click_element(selector="#submit-button")

# Click by element name/text
await browser.click_element(element_name="Submit")

# Click at specific coordinates
await browser.click_element(position=(100, 200))
```

#### Scroll

```python
# Scroll down
await browser.scroll(direction="down")

# Scroll up with specific distance
await browser.scroll(direction="up", distance=500)
```

#### Type Text

```python
# Type into a specific input field
await browser.type_text("Hello, world!", selector="input[name='search']")

# Type into the currently focused element
await browser.type_text("Hello, world!")
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 