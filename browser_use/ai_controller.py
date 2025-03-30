"""
AI Controller for browser automation.

This module provides AI-driven control for browser automation, allowing the AI to make
decisions about what actions to take based on the current state of the browser.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import litellm
from litellm.utils import get_secret

from browser_use.extract import DataExtractor
from browser_use.native_automation import NativeBrowserAutomation

logger = logging.getLogger(__name__)

class AIController:
    """
    AI Controller for browser automation.
    
    This class provides AI-driven control for browser automation, allowing the AI to make
    decisions about what actions to take based on the current state of the browser.
    """
    
    def __init__(self, 
                automation: NativeBrowserAutomation,
                api_key: str, 
                model_name: str = "gpt-4o",
                provider: Optional[str] = None,
                max_thinking_steps: int = 5,
                output_dir: str = "output",
                verbose: bool = False):
        """
        Initialize the AI controller.
        
        Args:
            automation: The browser automation instance to control
            api_key: API key for the LLM provider
            model_name: The model to use
            provider: Optional provider name (if using non-default mappings)
            max_thinking_steps: Maximum number of thinking steps before taking action
            output_dir: Directory to save outputs
            verbose: Whether to print verbose logging
        """
        self.automation = automation
        self.api_key = api_key
        self.model_name = model_name
        self.provider = provider
        self.max_thinking_steps = max_thinking_steps
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up LLM
        self._setup_llm()
        
        # State tracking
        self.state_history = []
        self.action_history = []
        
    def _setup_llm(self):
        """Configure LiteLLM with the provided API key."""
        # Set default API keys based on model
        if "gpt" in self.model_name.lower() or "openai" in self.model_name.lower():
            os.environ["OPENAI_API_KEY"] = self.api_key
        elif "claude" in self.model_name.lower():
            os.environ["ANTHROPIC_API_KEY"] = self.api_key
        elif "gemini" in self.model_name.lower():
            os.environ["GOOGLE_API_KEY"] = self.api_key
        else:
            # For custom providers
            if self.provider:
                os.environ[f"{self.provider.upper()}_API_KEY"] = self.api_key
            else:
                # Default fallback
                os.environ["LITELLM_API_KEY"] = self.api_key
        
        # Set safe defaults for LiteLLM
        litellm.set_verbose = self.verbose
        litellm.timeout = 60
        
    async def capture_browser_state(self) -> Dict[str, Any]:
        """
        Capture the current state of the browser.
        
        Returns:
            Dictionary containing browser state information
        """
        # Get basic browser information
        current_url = await self.automation.browser.get_current_url()
        page_title = await self.automation.browser.get_page_title()
        
        # Take screenshot
        screenshot_path = await self.automation.take_screenshot(
            str(self.output_dir / f"state_{len(self.state_history)}.png")
        )
        
        # Extract structured data
        try:
            structured_data = await self.automation.extract_all_structured_data()
        except Exception as e:
            logger.warning(f"Error extracting structured data: {e}")
            structured_data = {}
            
        # Create state object
        state = {
            "url": current_url,
            "title": page_title,
            "screenshot_path": screenshot_path,
            "structured_data": structured_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Add to history
        self.state_history.append(state)
        
        return state
        
    async def _query_llm(self, 
                         prompt: str, 
                         image_paths: Optional[List[str]] = None, 
                         system_message: Optional[str] = None) -> str:
        """
        Query the LLM with a prompt and optional images.
        
        Args:
            prompt: The text prompt to send to the LLM
            image_paths: Optional list of image file paths to include
            system_message: Optional system message for the LLM
            
        Returns:
            The response from the LLM
        """
        try:
            # Create messages list
            messages = []
            
            # Add system message if provided
            if system_message:
                messages.append({
                    "role": "system", 
                    "content": system_message
                })
            
            # Create content list for user message
            content = [{"type": "text", "text": prompt}]
            
            # Add images if provided
            if image_paths and len(image_paths) > 0:
                for image_path in image_paths:
                    if os.path.exists(image_path):
                        import base64
                        with open(image_path, "rb") as img_file:
                            base64_image = base64.b64encode(img_file.read()).decode("utf-8")
                            content.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            })
            
            # Add user message
            messages.append({
                "role": "user",
                "content": content
            })
            
            # Generate response
            response = await asyncio.to_thread(
                lambda: litellm.completion(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=2048
                )
            )
            
            # Extract content from response
            if hasattr(response, 'choices') and len(response.choices) > 0:
                if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                    return response.choices[0].message.content
                
            # Fallback for different response structures
            return str(response)
            
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            return json.dumps({"error": str(e)})
            
    async def analyze_and_suggest_action(self, 
                                       task_description: str, 
                                       state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the current browser state and suggest the next action to take.
        
        Args:
            task_description: Description of the task to accomplish
            state: Optional browser state (if not provided, will be captured)
            
        Returns:
            Dictionary with the suggested action
        """
        if state is None:
            state = await self.capture_browser_state()
            
        # Create system message
        system_message = """
        You are an AI assistant that helps with browser automation. Your task is to analyze the 
        current state of a browser and suggest the next action to take to accomplish a given task.
        
        You should respond with a JSON object specifying the action to take. The actions you can suggest are:
        1. {"action": "navigate", "url": "<url>"}
        2. {"action": "click", "selector": "<css_selector>"}
        3. {"action": "input", "selector": "<css_selector>", "text": "<text>"}
        4. {"action": "extract", "extraction_config": {...}}
        5. {"action": "wait", "seconds": <seconds>}
        6. {"action": "scroll", "direction": "up|down|left|right", "amount": <pixels>}
        7. {"action": "think", "reasoning": "<thinking step>"}
        8. {"action": "complete", "result": "<task completion result>"}
        
        The "think" action is for when you need to reason through the next steps but aren't ready
        to suggest a concrete browser action yet. Multiple "think" steps can be used, but try to
        be efficient and don't exceed 3 thinking steps before taking action.
        
        The "complete" action is for when you believe the task is complete.
        """
        
        # Create prompt
        prompt = f"""
        # Current Task
        {task_description}
        
        # Current Browser State
        URL: {state['url']}
        Title: {state['title']}
        
        # Previous Actions
        {json.dumps(self.action_history[-5:] if len(self.action_history) > 5 else self.action_history, indent=2)}
        
        The screenshot of the current page state is attached to this message.
        
        Analyze the current state and suggest the next action to take to accomplish the task.
        Respond with a JSON object as specified. Don't use markdown for the JSON.
        """
        
        # Get suggestion from LLM
        response = await self._query_llm(
            prompt=prompt, 
            image_paths=[state['screenshot_path']], 
            system_message=system_message
        )
        
        # Parse response to get action
        try:
            # Extract JSON from response (it might be wrapped in ```json ... ```)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                
            action = json.loads(json_str)
            
            # Add to action history
            self.action_history.append(action)
            
            return action
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Response was: {response}")
            
            # Fall back to a think action
            fallback_action = {
                "action": "think",
                "reasoning": f"Error parsing response. Will try to continue with a simpler action. Error: {str(e)}"
            }
            self.action_history.append(fallback_action)
            return fallback_action
            
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the suggested action.
        
        Args:
            action: The action to execute
            
        Returns:
            Dictionary with the result of the action
        """
        action_type = action.get("action", "")
        
        # Navigate to URL
        if action_type == "navigate":
            url = action.get("url", "")
            if not url:
                return {"success": False, "message": "No URL provided"}
                
            try:
                await self.automation.navigate_to(url)
                return {"success": True, "message": f"Navigated to {url}"}
            except Exception as e:
                return {"success": False, "message": f"Error navigating to {url}: {str(e)}"}
                
        # Click on element
        elif action_type == "click":
            selector = action.get("selector", "")
            if not selector:
                return {"success": False, "message": "No selector provided"}
                
            try:
                result = await self.automation.click(selector)
                return {"success": result, "message": f"Clicked on {selector}" if result else f"Failed to click on {selector}"}
            except Exception as e:
                return {"success": False, "message": f"Error clicking on {selector}: {str(e)}"}
                
        # Input text
        elif action_type == "input":
            selector = action.get("selector", "")
            text = action.get("text", "")
            if not selector:
                return {"success": False, "message": "No selector provided"}
            if text is None:  # Allow empty string
                return {"success": False, "message": "No text provided"}
                
            try:
                result = await self.automation.input_text(selector, text)
                return {"success": result, "message": f"Input text to {selector}" if result else f"Failed to input text to {selector}"}
            except Exception as e:
                return {"success": False, "message": f"Error inputting text to {selector}: {str(e)}"}
                
        # Extract data
        elif action_type == "extract":
            extraction_config = action.get("extraction_config", {})
            if not extraction_config:
                return {"success": False, "message": "No extraction configuration provided"}
                
            try:
                data = await self.automation.extract_data(extraction_config)
                
                # Save data to file
                output_file = self.output_dir / f"extracted_data_{len(self.action_history)}.json"
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)
                
                return {"success": True, "message": f"Data extracted and saved to {output_file}", "data": data}
            except Exception as e:
                return {"success": False, "message": f"Error extracting data: {str(e)}"}
                
        # Wait for some time
        elif action_type == "wait":
            seconds = action.get("seconds", 1)
            
            try:
                await asyncio.sleep(seconds)
                return {"success": True, "message": f"Waited for {seconds} seconds"}
            except Exception as e:
                return {"success": False, "message": f"Error waiting: {str(e)}"}
                
        # Scroll the page
        elif action_type == "scroll":
            direction = action.get("direction", "down")
            amount = action.get("amount", 300)
            
            try:
                # Translate direction to x,y coordinates
                x, y = 0, 0
                if direction == "down":
                    y = amount
                elif direction == "up":
                    y = -amount
                elif direction == "right":
                    x = amount
                elif direction == "left":
                    x = -amount
                
                # Execute scroll using JavaScript
                script = f"window.scrollBy({x}, {y});"
                await self.automation.execute_script(script)
                
                return {"success": True, "message": f"Scrolled {direction} by {amount} pixels"}
            except Exception as e:
                return {"success": False, "message": f"Error scrolling: {str(e)}"}
                
        # Thinking step (no action)
        elif action_type == "think":
            return {"success": True, "message": "Thinking step completed", "thinking": action.get("reasoning", "")}
            
        # Complete task
        elif action_type == "complete":
            return {"success": True, "message": "Task completed", "result": action.get("result", "")}
        
        # Unknown action
        else:
            return {"success": False, "message": f"Unknown action type: {action_type}"}
            
    async def run_task(self, task_description: str, max_actions: int = 20) -> Dict[str, Any]:
        """
        Run a complete task using AI control.
        
        Args:
            task_description: Description of the task to accomplish
            max_actions: Maximum number of actions to take
            
        Returns:
            Dictionary with the task execution result
        """
        logger.info(f"Starting task: {task_description}")
        
        thinking_steps = 0
        action_count = 0
        final_result = {"success": False, "message": "Task exceeded maximum actions"}
        
        while action_count < max_actions:
            # Capture current state
            state = await self.capture_browser_state()
            
            # Get next action
            action = await self.analyze_and_suggest_action(task_description, state)
            action_count += 1
            
            # Log action
            logger.info(f"Action {action_count}: {json.dumps(action)}")
            
            # Check if we're just thinking
            if action.get("action") == "think":
                thinking_steps += 1
                logger.info(f"Thinking: {action.get('reasoning', '')}")
                
                # Check if we've been thinking too much
                if thinking_steps > self.max_thinking_steps:
                    logger.warning("Too many thinking steps, forcing an action")
                    prompt = f"""
                    You've been thinking for {thinking_steps} steps without taking action.
                    Please suggest a concrete action now (navigate, click, input, etc.) based on your thinking so far.
                    
                    Current URL: {state['url']}
                    Current Page Title: {state['title']}
                    """
                    
                    # Get forced action
                    response = await self._query_llm(
                        prompt=prompt, 
                        image_paths=[state['screenshot_path']]
                    )
                    
                    try:
                        # Extract JSON from response
                        json_str = response
                        if "```json" in response:
                            json_str = response.split("```json")[1].split("```")[0].strip()
                        elif "```" in response:
                            json_str = response.split("```")[1].split("```")[0].strip()
                            
                        action = json.loads(json_str)
                        
                        # Add to action history
                        self.action_history.append(action)
                        
                        # Reset thinking steps
                        thinking_steps = 0
                    except Exception as e:
                        logger.error(f"Error parsing forced action: {e}")
                        # Continue with next iteration
                        continue
                else:
                    # Continue thinking
                    continue
            else:
                # Reset thinking steps
                thinking_steps = 0
            
            # Check if task is complete
            if action.get("action") == "complete":
                final_result = {
                    "success": True,
                    "message": "Task completed successfully",
                    "result": action.get("result", ""),
                    "actions_taken": action_count,
                    "action_history": self.action_history
                }
                break
            
            # Execute action
            result = await self.execute_action(action)
            logger.info(f"Action result: {json.dumps(result)}")
            
            # Add result to action for history
            action["result"] = result
            
            # Wait a moment between actions
            await asyncio.sleep(1)
        
        # Task done or max actions reached
        return final_result 