#!/usr/bin/env python3
"""
Example script demonstrating the use of the browser_use library.
"""

import os
import time
from browser_use import BrowserUse
from browser_use.utils.exceptions import ElementNotFoundException, BrowserOperationError


def main():
    # Initialize browser (use headless=True for no GUI)
    browser = BrowserUse(headless=False)
    
    try:
        # Example 1: Basic navigation and extraction
        print("Example 1: Basic navigation and extraction")
        browser.navigate("https://www.example.com")
        
        # Extract all links
        links = browser.extract_links()
        print(f"Found {len(links)} links:")
        for i, link in enumerate(links[:5], 1):  # Show first 5 links
            print(f"  {i}. '{link['text']}' -> {link['href']}")
        
        if len(links) > 5:
            print(f"  ... and {len(links) - 5} more")
        
        # Demonstrate element highlighting
        print("\nDemonstrating element highlighting:")
        try:
            # Find and highlight the main heading
            heading = browser.find_and_highlight("h1", duration=3)
            print(f"Highlighted heading: {heading.text}")
            
            # Find and highlight a paragraph
            paragraph = browser.find_and_highlight("p", duration=3)
            print(f"Highlighted paragraph: {paragraph.text[:50]}...")
        except ElementNotFoundException as e:
            print(f"Could not find element to highlight: {e}")
            
        # Example 1.5: Dynamic element finding
        print("\nExample 1.5: Dynamic element finding")
        try:
            print("Scanning page for all interactive elements...")
            # Scan all interactive elements and highlight them
            elements = browser.scan_interactive_elements(highlight=True)
            print(f"Found {len(elements)} interactive elements")
            
            # Wait for user to see the highlights
            time.sleep(3)
            
            # Clear all highlights
            browser.clear_highlights()
            print("Cleared all highlights")
            
            # Find an element by its content
            print("\nFinding 'More information...' link by content")
            more_info = browser.find_element_by_content("More information", element_type="a")
            print(f"Found element: {more_info.text}")
            
            # Click the element
            time.sleep(1)
            more_info.click()
            print("Clicked on the element")
            time.sleep(2)
            
            # Go back to the example.com page
            browser.navigate("https://www.example.com")
            time.sleep(1)
        except (ElementNotFoundException, BrowserOperationError) as e:
            print(f"Error during dynamic element finding: {e}")
        
        # Take screenshot with link boxes
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshots_dir, "example_com_links.png")
        browser.screenshot_with_link_boxes(screenshot_path)
        print(f"Screenshot with link boxes saved to: {screenshot_path}")
        
        # Extract structured content
        content = browser.extract_page_content()
        print(f"Page title: {content['title']}")
        print(f"Number of headings: {len(content['headings'])}")
        print(f"Number of paragraphs: {len(content['paragraphs'])}")
        print()
        
        # Example 2: Browser interaction with a search engine
        print("Example 2: Browser interaction")
        browser.navigate("https://www.google.com")
        time.sleep(1)  # Wait for the page to load
        
        # Type in the search box
        try:
            # Try to find the search box and type in it (with highlighting)
            print("Finding and highlighting search box...")
            browser.type_text("Python selenium tutorial", "input[name='q']", highlight=True)
            time.sleep(1)
            
            # Press enter to search
            browser.type_text("\n", "input[name='q']")
            time.sleep(2)
            
            # Dynamically scan and highlight all interactive elements on search results
            print("\nScanning search results for all interactive elements...")
            elements = browser.scan_interactive_elements(highlight=True)
            print(f"Found {len(elements)} interactive elements on search results page")
            time.sleep(3)
            browser.clear_highlights()
            
            # Take screenshot of search results
            screenshot_path = os.path.join(screenshots_dir, "search_results.png")
            browser.screenshot_with_link_boxes(screenshot_path)
            print(f"Search results screenshot saved to: {screenshot_path}")
            
            # Scroll down the page
            print("Scrolling down the page...")
            browser.scroll("down", 500)
            time.sleep(1)
            
            # Try to find and click a search result using the new dynamic content finder
            try:
                print("Finding a search result using dynamic content finder...")
                result_element = browser.find_element_by_content("Selenium Python Tutorial", highlight=True)
                print(f"Found result: {result_element.text[:50]}...")
                time.sleep(2)
                
                # Now click the found element
                result_element.click()
                time.sleep(2)
                print("Clicked on the dynamically found search result")
                
                # Take a final screenshot
                screenshot_path = os.path.join(screenshots_dir, "final_page.png")
                browser.driver.save_screenshot(screenshot_path)
                print(f"Final page screenshot saved to: {screenshot_path}")
                
            except ElementNotFoundException as e:
                print(f"Could not find search result with dynamic finder: {e}")
                # Fallback to try clicking using general content
                try:
                    print("Trying to click using general content matcher...")
                    browser.click_element("Selenium Python", highlight=True)
                    time.sleep(2)
                    print("Clicked on a search result using general content matcher")
                except ElementNotFoundException as e:
                    print(f"Could not find any matching search result: {e}")
                
        except (ElementNotFoundException, BrowserOperationError) as e:
            print(f"Error during interaction: {e}")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Always close the browser at the end
        browser.close()
        print("Browser closed")


if __name__ == "__main__":
    main() 