from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from .exceptions import ElementNotFoundException


def find_element_by_text(driver, text):
    """
    Find an element by its visible text content
    
    Args:
        driver: Selenium WebDriver instance
        text (str): Text to search for
        
    Returns:
        WebElement: The found element
        
    Raises:
        ElementNotFoundException: If element not found
    """
    # Try to find by exact text match first
    try:
        # Look for links, buttons, and elements with text
        for xpath in [
            f"//a[contains(text(), '{text}')]",
            f"//button[contains(text(), '{text}')]",
            f"//*[contains(text(), '{text}')]",
            f"//*[@aria-label='{text}']",
            f"//*[@alt='{text}']",
            f"//*[@title='{text}']",
            f"//input[@value='{text}']",
            f"//input[@placeholder='{text}']"
        ]:
            try:
                element = driver.find_element(By.XPATH, xpath)
                if element.is_displayed():
                    return element
            except NoSuchElementException:
                continue
    except Exception:
        pass
        
    # If we get here, no element was found
    raise ElementNotFoundException(f"No element found with text: {text}")


def get_clickable_elements(driver):
    """
    Get all potentially clickable elements on the page
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        list: List of WebElements that are potentially clickable
    """
    clickable_elements = []
    
    # Common clickable elements
    selectors = [
        "a", "button", "input[type='button']", "input[type='submit']",
        "input[type='checkbox']", "input[type='radio']",
        "[role='button']", "[role='link']", "[role='checkbox']", "[role='menuitem']",
        "[role='tab']", "[onclick]", "[class*='btn']", "[class*='button']"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    clickable_elements.append(element)
        except:
            continue
            
    return clickable_elements 