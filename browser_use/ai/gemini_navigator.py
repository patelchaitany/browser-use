"""
GeminiNavigator module for AI-assisted browser navigation using Google's Gemini AI.

This module provides integration with the Gemini AI model to help navigate
web pages by analyzing screenshots and page content.
"""

import os
import base64
import json
import tempfile
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import asyncio

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image

from browser_use import BrowserUse
from browser_use.utils.logger import setup_logger

logger = setup_logger(__name__)

class GeminiNavigator:
    """
    AI-assisted browser navigation using Google's Gemini AI.
    
    This class uses Gemini AI to:
    - Analyze screenshots of web pages
    - Identify UI elements and their functions
    - Make navigation decisions based on user prompts
    - Execute browser actions based on AI recommendations
    """
    
    def __init__(self, browser_use: BrowserUse, api_key: Optional[str] = None):
        """
        Initialize the Gemini Navigator.
        
        Args:
            browser_use (BrowserUse): Instance of the BrowserUse class
            api_key (Optional[str]): Gemini API key, if not provided, will look for GEMINI_API_KEY in env
        """
        self.browser = browser_use
        
        # Get API key from environment if not provided
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Gemini API key not provided. Either pass it as a parameter or set GEMINI_API_KEY in .env"
            )
            
        # Initialize Gemini
        genai.configure(api_key=self._api_key)
        
        # Set up the Gemini model
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
    
    async def _take_screenshot(self, highlight_elements: bool = True) -> Tuple[str, Image.Image]:
        """
        Take a screenshot of the current page with optional element highlighting.
        
        Args:
            highlight_elements (bool): Whether to highlight interactive elements
            
        Returns:
            Tuple[str, Image.Image]: Path to the saved screenshot and the image object
        """
        # Create a temporary file for the screenshot
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            screenshot_path = temp_file.name
            
        # Take screenshot with highlighted elements
        if highlight_elements:
            elements = await self.browser.extract_interactive_elements(draw_boxes=True)
            await self.browser.take_screenshot(screenshot_path)
        else:
            await self.browser.take_screenshot(screenshot_path)
            
        # Load the image
        img = Image.open(screenshot_path)
        
        return screenshot_path, img
    
    async def _analyze_page(self, img: Image.Image, query: str) -> Dict:
        """
        Analyze a page using Gemini AI.
        
        Args:
            img (Image.Image): Screenshot image
            query (str): Query about what to do on the page
            
        Returns:
            Dict: Gemini response parsed as a dictionary
        """
        # Create a prompt that asks for a structured response
        prompt = f"""
        Look at this screenshot of a web page and answer the following query:
        
        QUERY: {query}
        
        Analyze the page and identify the best UI element to interact with based on the query.
        
        Return a JSON object with the following structure:
        {{
            "action": "the action to take (click, type, scroll, etc.)",
            "element_type": "the type of element (button, link, input field, etc.)",
            "element_text": "visible text of the element, if any",
            "element_position": "approximate x,y position if visible",
            "selector": "CSS selector if you can determine it",
            "input_text": "text to type if action is 'type'",
            "reasoning": "brief explanation of why this is the best element"
        }}
        
        Format the response as a valid JSON object without any additional text or markdown.
        """
        
        # Get response from Gemini
        response = self.model.generate_content([prompt, img])
        
        # Extract and parse the JSON from the response
        response_text = response.text
        
        # Clean up the response if it has markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response: {e}")
            logger.error(f"Response was: {response_text}")
            raise ValueError(f"Gemini did not return a valid JSON response: {e}")
    
    async def _execute_action(self, action_data: Dict) -> None:
        """
        Execute an action based on the AI recommendation.
        
        Args:
            action_data (Dict): Action data from Gemini
        """
        action = action_data.get("action", "").lower()
        
        if action == "click":
            # Try to use selector first, then element text, then position
            selector = action_data.get("selector")
            element_text = action_data.get("element_text")
            position_str = action_data.get("element_position")
            
            position = None
            if position_str and "," in position_str:
                try:
                    x, y = position_str.replace(" ", "").split(",")
                    position = (int(x), int(y))
                except (ValueError, TypeError):
                    position = None
                    
            await self.browser.click_element(
                selector=selector, 
                element_name=element_text, 
                position=position
            )
            logger.info(f"Clicked element: {element_text or selector or position}")
            
        elif action == "type":
            input_text = action_data.get("input_text", "")
            selector = action_data.get("selector")
            
            await self.browser.type_text(input_text, selector=selector)
            logger.info(f"Typed '{input_text}' into {selector or 'focused element'}")
            
        elif action == "scroll":
            direction = "down"  # Default direction
            if "up" in action_data.get("reasoning", "").lower():
                direction = "up"
                
            await self.browser.scroll(direction=direction)
            logger.info(f"Scrolled {direction}")
            
        else:
            logger.warning(f"Unknown action: {action}")
    
    async def navigate(self, query: str) -> Dict:
        """
        Navigate based on a natural language query using Gemini AI.
        
        Args:
            query (str): Natural language query about what to do
            
        Returns:
            Dict: Results of the navigation action
        """
        # Take a screenshot of the current page
        screenshot_path, img = await self._take_screenshot()
        
        try:
            # Analyze the page with Gemini
            logger.info(f"Analyzing page with query: {query}")
            analysis = await self._analyze_page(img, query)
            
            # Execute the recommended action
            logger.info(f"Executing action: {analysis.get('action')} on {analysis.get('element_type')}")
            await self._execute_action(analysis)
            
            # Return the analysis result
            return {
                "query": query,
                "analysis": analysis,
                "screenshot_path": screenshot_path,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error during navigation: {e}")
            return {
                "query": query,
                "error": str(e),
                "screenshot_path": screenshot_path,
                "success": False
            }
        finally:
            # Clean up the temporary screenshot file
            try:
                os.unlink(screenshot_path)
            except Exception:
                pass
    
    async def search_and_navigate(self, search_query: str, navigation_steps: List[str]) -> List[Dict]:
        """
        Search for a topic and then perform a series of navigation steps.
        
        Args:
            search_query (str): Query to search for
            navigation_steps (List[str]): List of navigation steps to perform
            
        Returns:
            List[Dict]: Results of each navigation step
        """
        # Navigate to a search engine
        await self.browser.goto("https://duckduckgo.com")
        
        # Enter the search query
        await self.browser.type_text(search_query, selector="input[name='q']")
        await self.browser.click_element(selector="button[type='submit']")
        
        # Wait for results to load
        await asyncio.sleep(2)
        
        results = []
        
        # Perform each navigation step
        for step in navigation_steps:
            result = await self.navigate(step)
            results.append(result)
            await asyncio.sleep(1)  # Small delay between steps
            
        return results
            
    async def answer_question(self, question: str) -> Dict:
        """
        Use Gemini AI to answer a question about the current page.
        
        Args:
            question (str): Question to answer about the page
            
        Returns:
            Dict: Gemini's response
        """
        # Take a screenshot of the current page without highlighting
        screenshot_path, img = await self._take_screenshot(highlight_elements=False)
        
        # Get the page's HTML content
        page_content = await self.browser.page.content()
        page_title = await self.browser.page.title()
        
        # Create a prompt for Gemini
        prompt = f"""
        I'm looking at a web page with the title: "{page_title}"
        
        I want to know: {question}
        
        Look at the screenshot of the page and answer my question based on what you can see.
        Provide a detailed and accurate answer based on the page content visible in the image.
        """
        
        try:
            # Get response from Gemini
            response = self.model.generate_content([prompt, img])
            
            return {
                "question": question,
                "answer": response.text,
                "screenshot_path": screenshot_path,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting answer from Gemini: {e}")
            return {
                "question": question,
                "error": str(e),
                "screenshot_path": screenshot_path,
                "success": False
            }
        finally:
            # Clean up the temporary screenshot file
            try:
                os.unlink(screenshot_path)
            except Exception:
                pass 