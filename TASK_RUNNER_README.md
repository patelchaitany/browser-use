# AI Task Runner for Browser Automation

This task runner uses an LLM (Large Language Model) to break down a high-level task into individual steps and then automates those steps in a web browser.

## How It Works

1. You provide a high-level task description (e.g., "Search for Python documentation and download the latest PDF").
2. The AI breaks this down into individual steps.
3. For each step:
   - The AI analyzes the current browser state (screenshot + DOM).
   - It determines the next action to take.
   - The browser automation executes that action.
   - The cycle repeats until the task is completed or max steps reached.

## Features

- Automatic task breakdown and planning
- Visual browser automation with screenshot capture
- Rate limiting to prevent API abuse
- Error handling and logging
- Detailed output with screenshots and action history
- Support for various LLM models via litellm

## Requirements

- Python 3.8+
- The dependencies listed in `requirements.txt`
- An API key for a supported LLM (Gemini, GPT, Claude, etc.)

## Installation

1. Clone this repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Install browser dependencies for Playwright:

```bash
playwright install chromium
```

4. Set up your API key in a `.env` file:

```
GOOGLE_API_KEY=your_api_key_here
# OR
OPENAI_API_KEY=your_api_key_here
# OR
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

Run the task runner from the command line:

```bash
python task_runner.py --task "Search for Python documentation and go to the latest version page" --url "https://www.google.com"
```

### Command Line Arguments

- `--task`: Description of the task to execute (required)
- `--url`: Starting URL for the task (optional)
- `--model`: LLM model to use (default: gemini/gemini-2.5-pro-exp-03-25)
- `--headless`: Run browser in headless mode (default: false)
- `--max-steps`: Maximum number of steps to execute (default: 10)
- `--output-dir`: Directory to store outputs (default: task_output)

## Output

The task runner creates a directory for each task run with:

- `task.txt`: Original task description
- `summary.json`: Summary of the task execution
- Step directories: One for each executed step, containing:
  - `description.txt`: Step description
  - `result.json`: Result of the step execution
  - `before.jpg`: Screenshot before the step
  - `after.jpg`: Screenshot after the step

## Example

```bash
# Search for Python documentation
python task_runner.py --task "Go to google.com, search for 'Python documentation', and click on the official Python docs link" --url "https://www.google.com"

# Complete a form
python task_runner.py --task "Fill out the contact form on the website with name 'John Doe', email 'john@example.com', and message 'Hello, this is a test'" --url "https://example.com/contact"
```

## Limitations

- The task runner may not handle highly dynamic websites perfectly
- Complex authentication flows may require additional handling
- The quality of task execution depends on the LLM's ability to understand the task and page structure
- May not work correctly with websites that use anti-bot measures

## License

This project is licensed under the MIT License - see the LICENSE file for details. 