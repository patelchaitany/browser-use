# AI-Driven Browser Automation

This enhancement adds AI-driven control to the browser automation system, allowing the AI to make decisions and control the browser based on natural language instructions.

## Features

- **Natural Language Task Description**: Describe tasks in plain language and let the AI figure out how to accomplish them
- **Visual Analysis**: The AI analyzes screenshots of the browser to understand the page layout and content
- **Autonomous Decision Making**: The AI decides what actions to take based on the current state of the browser
- **Multi-step Reasoning**: The AI can reason through complex tasks step by step
- **Self-correction**: The AI can adjust its approach if initial attempts don't succeed
- **Structured Data Extraction**: The AI can extract structured data from web pages as part of its tasks

## How It Works

1. The system captures the current state of the browser (screenshot, URL, HTML content)
2. The AI analyzes the state and decides what action to take next
3. The system executes the action (click, input text, navigate, etc.)
4. The process repeats until the task is complete or a maximum number of steps is reached

## Usage

### Command-Line Interface

```bash
# Basic usage
python ai_driven_browser_demo.py --task "Search for Python programming language on Wikipedia and extract the first paragraph"

# Specify browser and model
python ai_driven_browser_demo.py --task "Find images of cats on Google" --browser firefox --model "gpt-4o"

# Start at a specific URL
python ai_driven_browser_demo.py --task "Find the latest news about AI" --start-url "https://news.google.com"

# Run in headless mode with custom output directory
python ai_driven_browser_demo.py --task "Check the weather for New York" --headless --output-dir "output/weather"
```

### Python API

```python
from browser_use import NativeBrowserAutomation, BrowserType, AIController

async def run_ai_task():
    # Create browser automation
    automation = NativeBrowserAutomation(
        browser_type=BrowserType.CHROME,
        headless=False
    )
    
    await automation.start()
    try:
        # Navigate to starting URL
        await automation.navigate_to("https://www.google.com")
        
        # Create AI controller
        ai_controller = AIController(
            automation=automation,
            api_key="your-api-key",
            model_name="gpt-4o"
        )
        
        # Run the task
        result = await ai_controller.run_task(
            task_description="Search for the current weather in Paris and extract the temperature",
            max_actions=20
        )
        
        print(result)
    finally:
        await automation.stop()
```

## Example Tasks

The AI can perform a wide variety of tasks, such as:

- **Information Gathering**: "Find information about quantum computing on Wikipedia and extract key concepts"
- **E-commerce**: "Search for running shoes on Amazon, filter by price under $100, and extract the top 5 results"
- **Travel Planning**: "Find flights from New York to London for next month and extract the cheapest options"
- **Research**: "Find recent scientific papers about climate change and extract their abstracts"
- **Social Media**: "Go to Twitter and find trending topics in the Technology category"

## AI Decision Process

The AI makes decisions using the following framework:

1. **Observation**: Analyze the current page content, layout, and available interactive elements
2. **Planning**: Determine the next step towards completing the task
3. **Action Selection**: Choose the most appropriate action (click, input, navigate, etc.)
4. **Execution**: Perform the selected action
5. **Verification**: Check if the action had the intended effect and adjust if needed

## Requirements

- Python 3.7+
- One of the following LLM API keys:
  - OpenAI API key for GPT models
  - Anthropic API key for Claude models
  - Google API key for Gemini models
- Same requirements as the native browser automation system

## Notes and Limitations

- The AI's ability to complete tasks depends on the capabilities of the underlying LLM
- Complex tasks may require multiple steps and might not always succeed
- The system works best with common web interfaces and standard UI patterns
- Websites with complex JavaScript interactions or CAPTCHA might be challenging
- The AI might need to try different approaches for some tasks

## Contributing

Contributions to improve the AI decision-making capabilities are welcome. Key areas for enhancement include:

- Better handling of dynamic content
- Improved error recovery strategies
- Support for more complex interaction patterns
- Better screenshot analysis capabilities
- Task planning and optimization

## License

This project is licensed under the same license as the main project. 