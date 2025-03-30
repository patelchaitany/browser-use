# Browser Use - DOM-based Interactive Element Extractor

This Python library provides functionality to extract and highlight interactive elements in a web page using DOM-based analysis. It implements the following features:

- Extract all interactive and clickable elements from a webpage
- Highlight these elements with colored bounding boxes in the browser
- Take screenshots with the highlighted elements
- Interact with elements by clicking on them
- Provide detailed information about each interactive element
- Execute complex browsing tasks with AI assistance
- Break down tasks into logical steps and execute them automatically

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/browser-use.git
cd browser-use
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

4. Set up API keys (for AI-powered features):
   - Copy `.env.example` to `.env` and fill in your API keys
   - Or set environment variables manually (see AI Features section below)

## Usage

### Running the Demo

To see the basic DOM extraction in action, run the demo script:

```bash
python demo.py
```

This will:
1. Open a browser window
2. Navigate to example.com
3. Extract and highlight all interactive elements
4. Save a screenshot with the highlights
5. Click on the first interactive element
6. Save a screenshot after clicking

### Using the Library in Your Code

Here's a simple example of how to use the library in your own code:

```python
import asyncio
from playwright.async_api import async_playwright
from browser_use.dom.service import DomService

async def example():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to a website
        await page.goto("https://example.com")
        await page.wait_for_load_state("networkidle")
        
        # Initialize DOM service
        dom_service = DomService(page)
        
        # Extract and highlight clickable elements
        dom_state = await dom_service.get_clickable_elements()
        
        # Print information about each element
        for idx, element in dom_state.selector_map.items():
            print(f"Element {idx}: {element}")
            
        # Take a screenshot with highlights
        await dom_service.take_screenshot_with_highlights("screenshot.png")
        
        # Click on an element by index
        if 0 in dom_state.selector_map:
            await dom_service.click_element(0)
        
        # Close the browser
        await browser.close()

# Run the example
asyncio.run(example())
```

