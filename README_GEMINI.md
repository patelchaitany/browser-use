# Gemini-Powered Browser Automation

This extension of the Browser Use library allows you to use Google's Gemini AI model to automate browser interactions based on screenshots and DOM analysis.

## Features

- Automatically analyze web pages using Gemini AI
- Extract interactive elements and highlight them in screenshots
- Execute actions based on Gemini's analysis:
  - Click elements
  - Input text
  - Navigate to URLs
  - Scroll the page
- Standardized JSON output format

## Prerequisites

1. You need a Google AI API key to use Gemini. Get one at: https://ai.google.dev/
2. Install the required dependencies: `pip install -r requirements.txt`
3. Install Playwright browsers: `playwright install`

## Usage

### Basic Usage

```python
import asyncio
import os
from browser_use.automation import BrowserAutomation

async def main():
    # Get API key from environment variable
    gemini_api_key = os.environ["GEMINI_API_KEY"]
    
    # Initialize browser automation
    automation = BrowserAutomation(gemini_api_key=gemini_api_key)
    
    try:
        # Start the browser
        await automation.start()
        
        # Navigate to a website
        await automation.navigate_to("https://www.google.com")
        
        # Use Gemini to analyze the page and perform an action
        result = await automation.execute_gemini_command(
            "Search for 'python tutorial' on Google"
        )
        
        print(f"Action result: {result}")
        
    finally:
        # Always stop the browser properly
        await automation.stop()

asyncio.run(main())
```

### Setting the API Key

The Gemini API key can be set as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or provided directly in your code:

```python
automation = BrowserAutomation(gemini_api_key="your-api-key-here")
```

### Running the Demo

We've included a demo script that shows how to use the Gemini automation:

```bash
# Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Run the demo
python gemini_demo.py
```

The demo will:
1. Open Google and search for "python programming language"
2. Click on the first search result
3. Navigate to Playwright website and click on "Get Started"

## How It Works

1. The BrowserAutomation class takes screenshots of the current page
2. It uses DomService to extract interactive elements from the DOM and highlight them
3. It sends the screenshot and element information to Gemini with a task description
4. Gemini analyzes the screenshot and suggests an action in a standardized JSON format
5. The BrowserAutomation class executes the suggested action

## JSON Action Format

Gemini returns actions in a standardized JSON format:

### Clicking Elements
```json
{
  "click_element": {
    "index": 5
  }
}
```

### Entering Text
```json
{
  "input_text": {
    "index": 10,
    "text": "python tutorial"
  }
}
```

### Navigating to URLs
```json
{
  "go_to_url": {
    "url": "https://www.python.org"
  }
}
```

### Scrolling
```json
{
  "scroll": {
    "direction": "down",
    "amount": 300
  }
}
```

## Customization

You can customize the behavior of the automation:

```python
automation = BrowserAutomation(
    gemini_api_key=gemini_api_key,
    headless=True,  # Run in headless mode
    output_dir="my_screenshots",  # Custom output directory
    viewport_width=1920,  # Custom viewport width
    viewport_height=1080,  # Custom viewport height
    model_name="gemini-1.5-pro"  # Specific Gemini model
)
```

## Troubleshooting

- **Error: GEMINI_API_KEY environment variable not set**: Make sure to set your Gemini API key
- **Error querying Gemini**: Check your API key and internet connection
- **Invalid action format**: The Gemini response couldn't be parsed as a valid action
- **Unsupported action**: The action type returned by Gemini is not supported 