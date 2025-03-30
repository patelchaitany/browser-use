# LiteLLM-Powered Browser Automation

This extension of the Browser Use library allows you to use any LLM supported by LiteLLM to automate browser interactions based on screenshots and DOM analysis.

## Features

- Automatically analyze web pages using various LLMs (Gemini, GPT-4 Vision, Claude, etc.)
- Extract interactive elements and highlight them in screenshots
- Execute actions based on the LLM's analysis:
  - Click elements
  - Input text
  - Navigate to URLs
  - Scroll the page
- Standardized JSON output format
- Support for multiple LLM providers through LiteLLM

## Prerequisites

1. You need an API key for one of the supported LLM providers:
   - Google AI (Gemini)
   - OpenAI (GPT-4 Vision)
   - Anthropic (Claude)
   - Or any other provider supported by LiteLLM
   
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
    api_key = os.environ["GOOGLE_API_KEY"]  # or OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
    
    # Initialize browser automation
    automation = BrowserAutomation(
        api_key=api_key,
        model_name="gemini-pro-vision",  # or "gpt-4-vision-preview", "claude-3-opus-20240229", etc.
        headless=False
    )
    
    try:
        # Start the browser
        await automation.start()
        
        # Navigate to a website
        await automation.navigate_to("https://www.google.com")
        
        # Use the LLM to analyze the page and perform an action
        result = await automation.execute_ai_command(
            "Search for 'python tutorial' on Google"
        )
        
        print(f"Action result: {result}")
        
    finally:
        # Always stop the browser properly
        await automation.stop()

asyncio.run(main())
```

### Setting the API Key

The API key can be set as an environment variable (the name depends on the provider):

```bash
# For Google Gemini
export GOOGLE_API_KEY="your-api-key-here"

# For OpenAI
export OPENAI_API_KEY="your-api-key-here"

# For Anthropic
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or provided directly in your code:

```python
automation = BrowserAutomation(
    api_key="your-api-key-here",
    model_name="gemini-pro-vision"
)
```

### Running the Demo

We've included a demo script that shows how to use the AI automation:

```bash
# Set your API key
export GOOGLE_API_KEY="your-gemini-api-key-here"

# Run the demo with default model (gemini-pro-vision)
python gemini_demo.py

# Or run with a different model
python gemini_demo.py gpt-4-vision-preview
```

### Supported Models

The library supports any vision-capable model that works with LiteLLM, including:

- **Google**: `gemini-pro-vision`
- **OpenAI**: `gpt-4-vision-preview`
- **Anthropic**: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- And many more via LiteLLM

## How It Works

1. The BrowserAutomation class takes screenshots of the current page
2. It uses DomService to extract interactive elements from the DOM and highlight them
3. It sends the screenshot and element information to the LLM with a task description
4. The LLM analyzes the screenshot and suggests an action in a standardized JSON format
5. The BrowserAutomation class executes the suggested action

## JSON Action Format

The LLM returns actions in a standardized JSON format:

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
    api_key=api_key,
    model_name="gemini-pro-vision",  # Choose any supported model
    provider="custom_provider",  # For custom provider configurations
    headless=True,  # Run in headless mode
    output_dir="my_screenshots",  # Custom output directory
    viewport_width=1920,  # Custom viewport width
    viewport_height=1080  # Custom viewport height
)
```

## Troubleshooting

- **Error: API key environment variable not set**: Make sure to set the appropriate API key for your chosen model
- **Error querying LLM**: Check your API key and internet connection
- **Invalid action format**: The LLM response couldn't be parsed as a valid action
- **Unsupported action**: The action type returned by the LLM is not supported

## Using Custom Providers

For providers not directly supported by default environment variable naming, you can specify a custom provider:

```python
automation = BrowserAutomation(
    api_key="your-api-key",
    model_name="your-model-name",
    provider="custom_provider"  # This will set CUSTOM_PROVIDER_API_KEY
)
``` 