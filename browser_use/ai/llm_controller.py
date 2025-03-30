import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import litellm
from litellm.utils import get_secret

from browser_use.dom.service import DomService

logger = logging.getLogger(__name__)

class LLMController:
    """
    Controller that uses LiteLLM to analyze browser screenshots and DOM structure
    to determine the next actions to take. Compatible with various LLM providers.
    """
    
    def __init__(self, 
                 api_key: str, 
                 model_name: str = "gemini/gemini-2.5-pro-exp-03-25",
                 provider: Optional[str] = None):
        """
        Initialize the LLM controller.
        
        Args:
            api_key: API key for the LLM provider
            model_name: The model to use (default: gemini-pro-vision)
            provider: Optional provider name (if using non-default mappings)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.provider = provider
        self._setup_litellm()
        
    def _setup_litellm(self):
        """Configure LiteLLM with the provided API key."""
        # Set default API keys based on model 
        if "gemini" in self.model_name.lower():
            os.environ["GOOGLE_API_KEY"] = self.api_key
        elif "gpt" in self.model_name.lower() or "openai" in self.model_name.lower():
            os.environ["OPENAI_API_KEY"] = self.api_key
        elif "claude" in self.model_name.lower():
            os.environ["ANTHROPIC_API_KEY"] = self.api_key
        else:
            # For custom providers
            if self.provider:
                os.environ[f"{self.provider.upper()}_API_KEY"] = self.api_key
            else:
                # Default fallback
                os.environ["LITELLM_API_KEY"] = self.api_key
        
        # Set safe defaults for LiteLLM to avoid timeouts
        litellm.set_verbose = False
        litellm.timeout = 60  # Longer timeout for processing images
        
    async def analyze_page(self, dom_service: DomService, screenshot_path: str, task_description: str) -> Dict[str, Any]:
        """
        Analyze a page using both the DOM structure and a screenshot, then determine the next action to take.
        
        Args:
            dom_service: The DOM service instance with the current page
            screenshot_path: Path to the screenshot of the current page
            task_description: Description of what the user wants to accomplish
            
        Returns:
            A dictionary with the action to take (click_element, input_text, go_to_url, etc.)
        """
        # Get the DOM tree and interactive elements
        dom_state = await dom_service.get_clickable_elements(highlight_elements=True)
        
        # Take a screenshot with highlighted elements
        await dom_service.take_screenshot_with_highlights(screenshot_path)
        
        # Extract useful information about interactive elements
        elements_info = []
        for idx, element in dom_state.selector_map.items():
            elements_info.append({
                "index": idx,
                "tag_name": element.tag_name,
                "text": element.get_all_text_till_next_clickable_element()[:100],  # Limit text length
                "is_interactive": element.is_interactive,
                "is_in_viewport": element.is_in_viewport,
                "attributes": {k: v for k, v in element.attributes.items() if k in ['id', 'class', 'name', 'type', 'role', 'href']}
            })
        
        # Create the prompt for the LLM
        prompt = self._create_prompt(task_description, elements_info)
        
        # Convert screenshot to base64 for the API
        with open(screenshot_path, "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode("utf-8")
        
        # Send to LLM for analysis
        response = await self._query_llm(prompt, image_data)
        
        # Parse and return the action
        return self._parse_llm_response(response)
    
    def _create_prompt(self, task_description: str, elements_info: list) -> str:
        """Create a prompt for the LLM model."""
        prompt = f"""
        # Browser Interaction Task
        
        You are an AI assistant that helps users interact with web browsers. You analyze screenshots of web pages 
        that have interactive elements highlighted with colored boxes. Each element has an index number.
        
        ## Your Task
        {task_description}
        
        ## Interactive Elements on the Page
        The following interactive elements are detected on the page with their index numbers:
        
        ```
        {json.dumps(elements_info, indent=2)}
        ```
        
        ## Instructions
        1. Analyze the screenshot and identify the interactive elements with colored highlight boxes
        2. Based on the task description, decide what action should be taken next
        3. Respond with ONLY a JSON object specifying the action in this format:
           - For clicking an element: {{"click_element": {{"index": <element_index>}}}}
           - For entering text: {{"input_text": {{"index": <element_index>, "text": "<text_to_enter>"}}}}
           - For navigating to a URL: {{"go_to_url": {{"url": "<url_to_navigate>"}}}}
           - For scrolling: {{"scroll": {{"direction": "<up|down|left|right>", "amount": <pixels>}}}}
        
        Return ONLY the JSON object and nothing else. Do not include explanations or additional text.
        """
        return prompt
    
    async def _query_llm(self, prompt: str, image_data: str) -> str:
        """
        Query the LLM with a prompt and image using LiteLLM.
        
        Args:
            prompt: The text prompt to send to the LLM
            image_data: Base64-encoded image data
            
        Returns:
            The response from the LLM
        """
        try:
            # Create a message list with text and image
            messages = [
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }
            ]
            
            # Generate response using asyncio and litellm
            response = await asyncio.to_thread(
                lambda: litellm.completion(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=1024
                )
            )
            
            # Extract the content from the response
            if hasattr(response, 'choices') and len(response.choices) > 0:
                if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                    return response.choices[0].message.content
                
            # Fallback for different response structures
            return str(response)
            
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            return json.dumps({"error": str(e)})
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the response from the LLM and extract the action.
        
        Args:
            response: The raw response from the LLM
            
        Returns:
            A dictionary with the action to take
        """
        try:
            # Clean up response to extract just the JSON part
            # Sometimes the model might include markdown code blocks or extra text
            clean_response = response.strip()
            
            # If response is wrapped in markdown code blocks, extract the JSON
            if clean_response.startswith("```json"):
                clean_response = clean_response.replace("```json", "", 1)
                if "```" in clean_response:
                    clean_response = clean_response.split("```")[0]
            elif clean_response.startswith("```"):
                clean_response = clean_response.replace("```", "", 1)
                if "```" in clean_response:
                    clean_response = clean_response.split("```")[0]
            
            # Parse the JSON
            action = json.loads(clean_response.strip())
            
            # Validate the action format
            valid_actions = ["click_element", "input_text", "go_to_url", "scroll"]
            action_type = next((a for a in valid_actions if a in action), None)
            
            if action_type is None:
                raise ValueError(f"Invalid action format: {action}")
                
            return action
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Original response: {response}")
            return {"error": f"Failed to parse response: {str(e)}"} 