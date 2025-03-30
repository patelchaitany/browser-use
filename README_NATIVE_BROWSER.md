# Native Browser Automation & Data Extraction API

This extension enhances the browser automation capabilities of the project to directly control native browsers (Chrome/Firefox) through their respective browser-specific interfaces, rather than relying on third-party browser automation frameworks like Playwright.

## Features

### Native Browser Control

- **Direct browser integration**: Control Chrome and Firefox browsers directly through Selenium WebDriver and browser-specific interfaces
- **Proxy configuration**: Configure browser to use HTTP, HTTPS, or SOCKS proxies with optional authentication
- **Browser extension integration**: Load and use browser extensions (.crx for Chrome, .xpi for Firefox)
- **User profiles**: Use existing browser profiles for maintaining session state, cookies, and preferences
- **Browser debugging**: Access browser console logs and detailed browser information

### Structured Data Extraction

- **Multiple extraction strategies**:
  - CSS selectors
  - XPath expressions
  - Regular expressions
  - JSON-LD structured data
  - Microdata structured data
- **Composite extraction**: Extract complex nested data structures with parent-child relationships
- **Table extraction**: Convert HTML tables to structured data with headers as keys
- **Attribute extraction**: Extract specific attributes from elements or their text content
- **Automatic data detection**: Automatically detect and extract common data structures (articles, products, tables)

### Complete Automation Flows

- **Login flow**: Automate login to websites with username/password
- **Search flow**: Perform searches and extract structured results
- **Navigation and extraction**: Navigate between pages and extract data in sequence
- **Cookie management**: Get, set, and delete cookies

## Modules

### `native_browser.py`

The core module for direct browser control:

- `BrowserType`: Enum for supported browser types (Chrome, Firefox)
- `NativeBrowser`: Class that provides direct control over browsers
  - Browser initialization with various configuration options
  - Navigation, interaction, and state management

### `extract.py`

Data extraction capabilities:

- `ExtractionStrategy`: Enum for different extraction approaches
- `ExtractorConfig`: Configuration for data extraction
- `DataExtractor`: Main class for extracting data from HTML content
- `WebElementExtractor`: Helper for extracting data from Selenium WebElements
- Utility functions for common extraction tasks

### `native_automation.py`

Integration of browser control and data extraction:

- `NativeBrowserAutomation`: Class that combines browser control with data extraction
  - Navigation and interaction methods
  - Data extraction methods
  - Complete automation flows (login, search, etc.)

## Usage Examples

### Basic Browser Control

```python
from browser_use.native_browser import NativeBrowser, BrowserType

async def example():
    # Initialize Chrome browser
    browser = NativeBrowser(
        browser_type=BrowserType.CHROME,
        headless=False
    )
    
    # Start the browser
    await browser.start()
    
    try:
        # Navigate to a website
        await browser.navigate_to("https://www.example.com")
        
        # Click an element
        await browser.click("#some-button")
        
        # Input text
        await browser.input_text("#search-input", "search query")
        
        # Take a screenshot
        await browser.take_screenshot("example.png")
        
    finally:
        # Stop the browser
        await browser.stop()
```

### Data Extraction

```python
from browser_use.extract import DataExtractor

# Extract data from HTML
html_content = "<html>...</html>"
extractor = DataExtractor(html_content)

# Extract using CSS selectors
data = extractor.extract({
    "strategy": "css_selector",
    "selector": ".product",
    "multiple": True,
    "children": [
        {"strategy": "css_selector", "selector": ".title", "attribute": None},
        {"strategy": "css_selector", "selector": ".price", "attribute": None},
        {"strategy": "css_selector", "selector": "img", "attribute": "src"}
    ]
})

# Extract structured data automatically
from browser_use.extract import extract_structured_data
all_structured_data = extract_structured_data(html_content)
```

### Complete Automation Flow

```python
from browser_use.native_automation import NativeBrowserAutomation
from browser_use.native_browser import BrowserType

async def automation_flow():
    # Initialize automation with proxy and extensions
    automation = NativeBrowserAutomation(
        browser_type=BrowserType.CHROME,
        headless=False,
        proxy_config={"host": "proxy.example.com", "port": "8080"},
        extensions=["path/to/extension.crx"]
    )
    
    # Start automation
    await automation.start()
    
    try:
        # Login to a website
        await automation.login_flow(
            url="https://example.com/login",
            username_selector="#username",
            password_selector="#password",
            submit_selector="#login-button",
            username="user123",
            password="pass123"
        )
        
        # Perform a search
        results = await automation.search_flow(
            url="https://example.com/search",
            search_selector="#search-input",
            submit_selector="#search-button",
            search_query="example query",
            results_selector=".search-result"
        )
        
        # Extract specific data
        data = await automation.extract_data({
            "strategy": "css_selector",
            "selector": ".main-content",
            "multiple": False,
            "children": [
                {"strategy": "css_selector", "selector": "h1", "attribute": None},
                {"strategy": "css_selector", "selector": "p", "multiple": True}
            ]
        })
        
    finally:
        # Stop automation
        await automation.stop()
```

## Run the Demo

The project includes a demo script that demonstrates the capabilities of the native browser automation and data extraction:

```bash
# Run the Wikipedia demo
python native_browser_demo.py --demo wikipedia --query "Artificial Intelligence"

# Run the GitHub demo (requires GitHub credentials)
export GITHUB_USERNAME=your_username
export GITHUB_PASSWORD=your_password
python native_browser_demo.py --demo github --github-repo "tensorflow/tensorflow"

# Use Firefox instead of Chrome
python native_browser_demo.py --browser firefox

# Run in headless mode
python native_browser_demo.py --headless

# Use a proxy
python native_browser_demo.py --proxy-host proxy.example.com --proxy-port 8080

# Use a browser extension
python native_browser_demo.py --extension path/to/extension.crx
```

## Requirements

- Python 3.7+
- Selenium
- WebDriver Manager
- BeautifulSoup4
- lxml
- requests-html

## License

This project is licensed under the same license as the main project.

## Credits

This extension was developed by [Your Name] as an enhancement to the browser automation capabilities of the project. 