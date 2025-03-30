"""
Data extraction API for retrieving structured data from web pages.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bs4
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)

class ExtractionStrategy(Enum):
    """Enum for supported extraction strategies."""
    CSS_SELECTOR = "css_selector"
    XPATH = "xpath"
    REGEX = "regex"
    JSON_LD = "json_ld"
    MICRODATA = "microdata"

@dataclass
class ExtractorConfig:
    """Configuration for data extraction."""
    strategy: ExtractionStrategy = ExtractionStrategy.CSS_SELECTOR
    selector: str = ""
    attribute: Optional[str] = None  # If None, get text content
    regex_pattern: Optional[str] = None
    multiple: bool = False
    children: List['ExtractorConfig'] = field(default_factory=list)
    

class DataExtractor:
    """
    Data extraction class that can extract structured data from web pages
    using various strategies like CSS selectors, XPath, regex, JSON-LD, etc.
    """
    
    def __init__(self, html_content: str):
        """
        Initialize the data extractor.
        
        Args:
            html_content: HTML content to extract data from
        """
        self.html = html_content
        self.soup = BeautifulSoup(html_content, 'lxml')
        
    def extract(self, config: Union[ExtractorConfig, Dict[str, Any]]) -> Any:
        """
        Extract data from HTML based on extraction configuration.
        
        Args:
            config: Extraction configuration, either ExtractorConfig object or dict
            
        Returns:
            Extracted data (string, list, dictionary, etc.)
        """
        # Convert dict to ExtractorConfig if needed
        if isinstance(config, dict):
            config = self._dict_to_config(config)
            
        # Choose extraction strategy
        if config.strategy == ExtractionStrategy.CSS_SELECTOR:
            return self._extract_by_css(config)
        elif config.strategy == ExtractionStrategy.XPATH:
            return self._extract_by_xpath(config)
        elif config.strategy == ExtractionStrategy.REGEX:
            return self._extract_by_regex(config)
        elif config.strategy == ExtractionStrategy.JSON_LD:
            return self._extract_json_ld(config)
        elif config.strategy == ExtractionStrategy.MICRODATA:
            return self._extract_microdata(config)
        else:
            raise ValueError(f"Unsupported extraction strategy: {config.strategy}")
            
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> ExtractorConfig:
        """Convert dictionary to ExtractorConfig."""
        # Convert strategy string to enum
        strategy = ExtractionStrategy(config_dict.get('strategy', 'css_selector'))
        
        # Create config
        config = ExtractorConfig(
            strategy=strategy,
            selector=config_dict.get('selector', ''),
            attribute=config_dict.get('attribute'),
            regex_pattern=config_dict.get('regex_pattern'),
            multiple=config_dict.get('multiple', False)
        )
        
        # Add children if any
        if 'children' in config_dict:
            config.children = [self._dict_to_config(c) for c in config_dict['children']]
            
        return config
            
    def _extract_by_css(self, config: ExtractorConfig) -> Any:
        """Extract data using CSS selectors."""
        if config.multiple:
            elements = self.soup.select(config.selector)
            
            if not elements:
                return []
                
            if not config.children:
                # Extract direct data from elements
                return [self._extract_element_data(el, config.attribute) for el in elements]
            else:
                # Extract nested data
                result = []
                for element in elements:
                    item = {}
                    for child_config in config.children:
                        child_soup = BeautifulSoup(str(element), 'lxml')
                        child_extractor = DataExtractor(str(element))
                        key = child_config.selector.replace('#', '').replace('.', '')
                        item[key] = child_extractor.extract(child_config)
                    result.append(item)
                return result
        else:
            element = self.soup.select_one(config.selector)
            
            if not element:
                return None
                
            if not config.children:
                return self._extract_element_data(element, config.attribute)
            else:
                # Extract nested data
                result = {}
                for child_config in config.children:
                    child_soup = BeautifulSoup(str(element), 'lxml')
                    child_extractor = DataExtractor(str(element))
                    key = child_config.selector.replace('#', '').replace('.', '')
                    result[key] = child_extractor.extract(child_config)
                return result
                
    def _extract_by_xpath(self, config: ExtractorConfig) -> Any:
        """
        Extract data using XPath.
        Note: BeautifulSoup doesn't natively support XPath, so we handle it differently.
        """
        from lxml import etree
        
        # Parse HTML with lxml
        parser = etree.HTMLParser()
        tree = etree.fromstring(self.html, parser)
        
        if config.multiple:
            elements = tree.xpath(config.selector)
            
            if not elements:
                return []
                
            # Convert lxml elements to string HTML for BeautifulSoup
            results = []
            for element in elements:
                html_str = etree.tostring(element, encoding='unicode')
                element_soup = BeautifulSoup(html_str, 'lxml')
                
                if not config.children:
                    # Extract direct data
                    results.append(self._extract_element_data(element_soup, config.attribute))
                else:
                    # Extract nested data
                    item = {}
                    child_extractor = DataExtractor(html_str)
                    for child_config in config.children:
                        key = child_config.selector.replace('//', '').replace('/', '')
                        item[key] = child_extractor.extract(child_config)
                    results.append(item)
            return results
        else:
            elements = tree.xpath(config.selector)
            if not elements or len(elements) == 0:
                return None
                
            # Convert lxml element to string HTML for BeautifulSoup
            element = elements[0]
            html_str = etree.tostring(element, encoding='unicode')
            element_soup = BeautifulSoup(html_str, 'lxml')
            
            if not config.children:
                return self._extract_element_data(element_soup, config.attribute)
            else:
                # Extract nested data
                result = {}
                child_extractor = DataExtractor(html_str)
                for child_config in config.children:
                    key = child_config.selector.replace('//', '').replace('/', '')
                    result[key] = child_extractor.extract(child_config)
                return result
                
    def _extract_by_regex(self, config: ExtractorConfig) -> Any:
        """Extract data using regular expressions."""
        if not config.regex_pattern:
            logger.warning("Regex pattern is missing for regex extraction")
            return None
            
        pattern = re.compile(config.regex_pattern, re.DOTALL)
        
        if config.multiple:
            matches = pattern.findall(self.html)
            return matches
        else:
            match = pattern.search(self.html)
            if match:
                # Return the entire match or the first group
                if match.groups():
                    return match.group(1)
                else:
                    return match.group(0)
            return None
            
    def _extract_json_ld(self, config: ExtractorConfig) -> Any:
        """Extract JSON-LD structured data."""
        json_ld_scripts = self.soup.select('script[type="application/ld+json"]')
        results = []
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                results.append(data)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Error parsing JSON-LD: {e}")
                
        if config.multiple:
            return results
        elif results:
            return results[0]
        else:
            return None
            
    def _extract_microdata(self, config: ExtractorConfig) -> Any:
        """Extract microdata structured data."""
        # Find all elements with itemtype attribute for microdata
        microdata_elements = self.soup.select('[itemscope]')
        results = []
        
        for element in microdata_elements:
            item_type = element.get('itemtype', '')
            
            # Skip if not matching the requested type
            if config.selector and item_type != config.selector:
                continue
                
            item_data = {'@type': item_type}
            
            # Extract properties
            for prop in element.select('[itemprop]'):
                prop_name = prop.get('itemprop', '')
                
                # Get property value based on tag type
                if prop.name == 'meta':
                    prop_value = prop.get('content', '')
                elif prop.name == 'img':
                    prop_value = prop.get('src', '')
                elif prop.name == 'a':
                    prop_value = prop.get('href', '')
                elif prop.name == 'time':
                    prop_value = prop.get('datetime', '')
                else:
                    prop_value = prop.get_text(strip=True)
                    
                item_data[prop_name] = prop_value
                
            results.append(item_data)
            
        if config.multiple:
            return results
        elif results:
            return results[0]
        else:
            return None
            
    def _extract_element_data(self, element: bs4.element.Tag, attribute: Optional[str]) -> Any:
        """Extract data from a BeautifulSoup element."""
        if not element:
            return None
            
        if attribute:
            return element.get(attribute)
        else:
            return element.get_text(strip=True)


class WebElementExtractor:
    """
    Data extraction class for Selenium WebElements.
    This is useful for extracting data from elements already found by Selenium.
    """
    
    @staticmethod
    def extract_data(element: WebElement, attribute: Optional[str] = None) -> Any:
        """
        Extract data from a WebElement.
        
        Args:
            element: Selenium WebElement to extract data from
            attribute: Attribute to extract, or None for text content
            
        Returns:
            Extracted data
        """
        if not element:
            return None
            
        if attribute:
            return element.get_attribute(attribute)
        else:
            return element.text.strip()
            
    @staticmethod
    def extract_table(table_element: WebElement) -> List[Dict[str, str]]:
        """
        Extract a HTML table into a list of dictionaries.
        
        Args:
            table_element: Selenium WebElement representing a table
            
        Returns:
            List of dictionaries, each representing a row with column headers as keys
        """
        if not table_element:
            return []
            
        # Get table headers
        header_elements = table_element.find_elements("xpath", ".//th")
        
        if not header_elements:
            # Try finding header cells in the first row
            first_row = table_element.find_elements("xpath", ".//tr")[0]
            header_elements = first_row.find_elements("xpath", ".//td")
            
        # If still no headers, use column indices as headers
        if not header_elements:
            # Get the first row to determine number of columns
            first_row = table_element.find_elements("xpath", ".//tr")[0]
            td_count = len(first_row.find_elements("xpath", ".//td"))
            headers = [f"column_{i}" for i in range(td_count)]
        else:
            headers = [h.text.strip() for h in header_elements]
            
        # Get table rows (skip header row)
        rows = table_element.find_elements("xpath", ".//tr")[1:]
        
        # Extract data from each row
        result = []
        for row in rows:
            cells = row.find_elements("xpath", ".//td")
            if len(cells) > 0:
                row_data = {headers[i]: cell.text.strip() for i, cell in enumerate(cells) if i < len(headers)}
                result.append(row_data)
                
        return result


def extract_structured_data(html_content: str) -> Dict[str, Any]:
    """
    Extract all structured data from HTML (convenience function).
    
    Args:
        html_content: HTML content to extract data from
        
    Returns:
        Dictionary with extracted structured data
    """
    extractor = DataExtractor(html_content)
    
    # Extract all available structured data
    result = {
        'json_ld': extractor.extract({
            'strategy': 'json_ld',
            'multiple': True
        }),
        'microdata': extractor.extract({
            'strategy': 'microdata',
            'multiple': True
        })
    }
    
    # Try to detect and extract common data structures
    detected_data = _detect_and_extract_common_data(html_content)
    if detected_data:
        result.update(detected_data)
        
    return result
    
def _detect_and_extract_common_data(html_content: str) -> Dict[str, Any]:
    """
    Detect and extract common data structures from HTML.
    
    Args:
        html_content: HTML content to extract data from
        
    Returns:
        Dictionary with extracted data
    """
    extractor = DataExtractor(html_content)
    soup = BeautifulSoup(html_content, 'lxml')
    result = {}
    
    # Detect and extract products
    product_elements = soup.select('[itemtype*="Product"]')
    if product_elements:
        result['products'] = extractor.extract({
            'strategy': 'microdata',
            'selector': 'http://schema.org/Product',
            'multiple': True
        })
    
    # Detect and extract articles
    article_elements = soup.select('article, [itemtype*="Article"]')
    if article_elements:
        result['articles'] = extractor.extract({
            'strategy': 'css_selector',
            'selector': 'article',
            'multiple': True,
            'children': [
                {'strategy': 'css_selector', 'selector': 'h1,h2,h3', 'attribute': None},
                {'strategy': 'css_selector', 'selector': 'p', 'attribute': None}
            ]
        })
        
    # Detect and extract tables
    tables = soup.select('table')
    if tables:
        table_data = []
        
        for i, table in enumerate(tables):
            headers = [th.get_text(strip=True) for th in table.select('th')]
            
            if not headers and table.select('tr'):
                # Try getting headers from first row
                first_row = table.select('tr')[0]
                headers = [td.get_text(strip=True) for td in first_row.select('td')]
                rows = table.select('tr')[1:]
            else:
                rows = table.select('tr')
                
            # If still no headers, use column indices
            if not headers and rows:
                first_row = rows[0]
                col_count = len(first_row.select('td'))
                headers = [f"column_{i}" for i in range(col_count)]
                
            # Extract rows
            extracted_rows = []
            for row in rows:
                cells = row.select('td')
                if cells:
                    row_data = {headers[i]: cell.get_text(strip=True) 
                               for i, cell in enumerate(cells) if i < len(headers)}
                    extracted_rows.append(row_data)
                    
            if extracted_rows:
                table_data.append({
                    'table_index': i,
                    'data': extracted_rows
                })
                
        if table_data:
            result['tables'] = table_data
            
    return result 