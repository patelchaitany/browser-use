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

## AI-Powered Features

The library offers multiple AI-powered features for advanced browser automation.

### LLM-Powered Browser Automation

Execute browser actions using natural language commands:

```python
import asyncio
from browser_use.browser_automation import BrowserAutomation

async def example():
    # Initialize with your API key
    automation = BrowserAutomation(api_key="your-api-key")
    
    try:
        # Start the browser
        await automation.start()
        
        # Navigate to a URL
        await automation.browser.navigate("https://example.com")
        
        # Execute a command using AI
        result = await automation.execute_command(
            "Find all links on this page and click on the one about products"
        )
        
        print(f"Command executed: {result}")
        
    finally:
        # Always close the browser
        await automation.stop()

asyncio.run(example())
```

For more details on LLM-powered automation, see [`README_LITELLM.md`](README_LITELLM.md).

### Task Agent for Complex Web Tasks

Execute complex web browsing tasks using natural language instructions:

```python
import asyncio
from browser_use.agent.task_planner import TaskPlanner

async def run_task():
    # Create the task planner
    planner = TaskPlanner(
        api_key="your-api-key",
        planning_model="gpt-4-turbo",
        execution_model="gemini/gemini-2.5-pro-exp-03-25"
    )
    
    try:
        # Execute a complex task
        history = await planner.execute_task(
            "Research the latest iPhone model and compare prices from 3 different retailers"
        )
        
        # Get the final result
        final_result = history.all_results[-1] if history.all_results else None
        if final_result and final_result.success and final_result.extracted_content:
            print(f"Task completed. Results: {final_result.extracted_content}")
        
    finally:
        # Always close the browser
        await planner.stop()

asyncio.run(run_task())
```

For quick testing, use the provided demo script:

```bash
python task_demo.py "Search for the latest news about AI"
```

For more details on the Task Agent, see [`README_TASK_AGENT.md`](README_TASK_AGENT.md).

## Advanced Usage

### Getting Element Details

You can get detailed information about each interactive element:

```python
# Get the DOM state which contains all interactive elements
dom_state = await dom_service.get_clickable_elements()

# Get a specific element by its highlight index
element = dom_state.selector_map[0]

# Get element properties
tag_name = element.tag_name          # HTML tag (e.g., 'a', 'button')
xpath = element.xpath                # XPath to the element
attributes = element.attributes      # Dictionary of HTML attributes
text = element.get_all_text_till_next_clickable_element()  # Text content
is_interactive = element.is_interactive  # Whether it's interactive
is_in_viewport = element.is_in_viewport  # Whether it's visible in viewport
```

### Customizing Highlighting

You can customize the element highlighting:

```python
# Highlight elements with specific focus on element index 2
dom_state = await dom_service.get_clickable_elements(
    highlight_elements=True,
    focus_element=2,
    viewport_expansion=100  # Expand the viewport detection area by 100px
)
```

## How It Works

The library uses a combination of JavaScript DOM analysis and Python processing:

1. It injects JavaScript code (buildDomTree.js) into the page
2. The JS code analyzes the DOM to find interactive elements
3. It highlights these elements with colored overlays
4. The data is returned to Python
5. Python constructs a tree representation of the DOM
6. You can then interact with this tree or with the highlighted elements

The interactive element detection looks for:
- Clickable elements (buttons, links, etc.)
- Form controls (inputs, selects, etc.)
- Elements with click handlers
- Elements with appropriate CSS properties (cursor: pointer)
- Elements that are visually apparent and accessible

For AI-powered features, the library uses:
- Various LLM providers (OpenAI, Google Gemini, Anthropic Claude) via LiteLLM
- Task planning and execution using sophisticated prompt engineering
- Browser automation through Playwright
- Screenshot-based visual understanding for complex web pages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 