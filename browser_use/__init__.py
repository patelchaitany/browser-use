# browser_use package
from browser_use.automation import BrowserAutomation
from browser_use.native_browser import NativeBrowser, BrowserType
from browser_use.native_automation import NativeBrowserAutomation
from browser_use.extract import (
    DataExtractor, 
    WebElementExtractor, 
    extract_structured_data,
    ExtractionStrategy,
    ExtractorConfig
)
from browser_use.ai_controller import AIController

__all__ = [
    'BrowserAutomation',
    'NativeBrowser',
    'BrowserType',
    'NativeBrowserAutomation',
    'DataExtractor',
    'WebElementExtractor',
    'extract_structured_data',
    'ExtractionStrategy',
    'ExtractorConfig',
    'AIController'
] 