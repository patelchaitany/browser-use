#!/usr/bin/env python3
"""
Demo script for native browser automation with data extraction.

This demo performs a complete automation flow:
1. Log into a popular website (Wikipedia)
2. Perform a search with user-specified keywords
3. Navigate through search results
4. Parse necessary information in a structured format

It also demonstrates proxy configuration and browser extension integration.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from browser_use.native_automation import NativeBrowserAutomation
from browser_use.native_browser import BrowserType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def run_wikipedia_demo(
    search_query: str,
    browser_type: str = "chrome",
    headless: bool = False,
    output_dir: str = "output",
    proxy_config: Optional[Dict[str, str]] = None,
    extension_paths: Optional[List[str]] = None
) -> None:
    """
    Run the Wikipedia search and data extraction demo.
    
    Args:
        search_query: Search query to use
        browser_type: Browser to use (chrome or firefox)
        headless: Whether to run in headless mode
        output_dir: Directory to save results
        proxy_config: Optional proxy configuration
        extension_paths: Optional list of extension paths
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Convert browser type string to enum
    browser_enum = BrowserType.CHROME
    if browser_type.lower() == "firefox":
        browser_enum = BrowserType.FIREFOX
        
    # Create the browser automation instance
    automation = NativeBrowserAutomation(
        browser_type=browser_enum,
        headless=headless,
        output_dir=output_dir,
        proxy_config=proxy_config,
        extensions=extension_paths
    )
    
    try:
        # Start the browser
        logger.info(f"Starting {browser_type} browser")
        await automation.start()
        
        # Step 1: Go to Wikipedia
        logger.info("Navigating to Wikipedia")
        await automation.navigate_to("https://www.wikipedia.org/")
        
        # Take a screenshot
        await automation.take_screenshot(str(output_path / "wikipedia_home.png"))
        
        # Step 2: Search for the query
        logger.info(f"Searching for: {search_query}")
        
        # On Wikipedia, the search field has id 'searchInput'
        search_selector = "#searchInput"
        submit_selector = "button[type='submit']"
        
        # Perform search
        await automation.input_text(search_selector, search_query)
        await automation.click(submit_selector)
        
        # Wait for search results to load
        await asyncio.sleep(2)
        
        # Take a screenshot of the search results
        await automation.take_screenshot(str(output_path / "search_results.png"))
        
        # Step 3: Extract page information
        logger.info("Extracting article content")
        
        # Extract structured data from the page
        structured_data = await automation.extract_all_structured_data()
        
        # Save structured data to file
        with open(output_path / "structured_data.json", "w") as f:
            json.dump(structured_data, f, indent=2)
            
        # Extract main article content
        article_content = await automation.extract_data({
            "strategy": "css_selector",
            "selector": "#mw-content-text",
            "multiple": False,
            "children": [
                {"strategy": "css_selector", "selector": "p", "multiple": True},
                {"strategy": "css_selector", "selector": "h2", "multiple": True}
            ]
        })
        
        # Save article content to file
        with open(output_path / "article_content.json", "w") as f:
            json.dump(article_content, f, indent=2)
        
        # Step 4: Extract references/citations
        logger.info("Extracting references")
        references = await automation.extract_data({
            "strategy": "css_selector",
            "selector": ".reference",
            "multiple": True
        })
        
        # Save references to file
        with open(output_path / "references.json", "w") as f:
            json.dump(references, f, indent=2)
            
        # Step 5: Extract links to related articles
        logger.info("Extracting related links")
        related_links = await automation.extract_data({
            "strategy": "css_selector",
            "selector": "#mw-content-text a",
            "multiple": True,
            "attribute": "href"
        })
        
        # Save related links to file
        with open(output_path / "related_links.json", "w") as f:
            json.dump(related_links, f, indent=2)
            
        # Click on the first interesting link (if available)
        try:
            # Find a link that looks interesting (contains part of the search query)
            await automation.execute_script(f"""
                const links = Array.from(document.querySelectorAll('#mw-content-text a'));
                const interestingLink = links.find(link => 
                    link.textContent.toLowerCase().includes('{search_query.lower()}') && 
                    !link.href.includes('#cite_') &&
                    link.href.startsWith('http')
                );
                if (interestingLink) interestingLink.click();
            """)
            
            # Wait for navigation
            await asyncio.sleep(2)
            
            # Take screenshot of the new page
            await automation.take_screenshot(str(output_path / "related_article.png"))
            
            # Get the current URL
            current_url = await automation.browser.get_current_url()
            logger.info(f"Navigated to related article: {current_url}")
            
            # Extract content from this page as well
            related_content = await automation.extract_data({
                "strategy": "css_selector",
                "selector": "#mw-content-text",
                "multiple": False,
                "children": [
                    {"strategy": "css_selector", "selector": "p", "multiple": True},
                    {"strategy": "css_selector", "selector": "h2", "multiple": True}
                ]
            })
            
            # Save related content to file
            with open(output_path / "related_content.json", "w") as f:
                json.dump(related_content, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not navigate to related article: {e}")
        
        # Get browser cookies
        cookies = await automation.get_cookies()
        
        # Save cookies to file
        with open(output_path / "cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)
        
        logger.info(f"Demo completed successfully! Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error during demo execution: {e}")
    finally:
        # Stop the browser
        await automation.stop()

async def run_github_demo(
    username: str,
    password: str,
    repo_to_search: str,
    browser_type: str = "chrome",
    headless: bool = False,
    output_dir: str = "output/github",
    proxy_config: Optional[Dict[str, str]] = None,
    extension_paths: Optional[List[str]] = None
) -> None:
    """
    Run the GitHub login, search, and data extraction demo.
    
    Args:
        username: GitHub username
        password: GitHub password
        repo_to_search: Repository name to search for
        browser_type: Browser to use (chrome or firefox)
        headless: Whether to run in headless mode
        output_dir: Directory to save results
        proxy_config: Optional proxy configuration
        extension_paths: Optional list of extension paths
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Convert browser type string to enum
    browser_enum = BrowserType.CHROME
    if browser_type.lower() == "firefox":
        browser_enum = BrowserType.FIREFOX
        
    # Create the browser automation instance
    automation = NativeBrowserAutomation(
        browser_type=browser_enum,
        headless=headless,
        output_dir=output_dir,
        proxy_config=proxy_config,
        extensions=extension_paths
    )
    
    try:
        # Start the browser
        logger.info(f"Starting {browser_type} browser")
        await automation.start()
        
        # Step 1: Login to GitHub
        logger.info("Logging into GitHub")
        login_success = await automation.login_flow(
            url="https://github.com/login",
            username_selector="#login_field",
            password_selector="#password",
            submit_selector="input[type='submit']",
            username=username,
            password=password
        )
        
        if not login_success:
            logger.error("GitHub login failed")
            return
            
        logger.info("Successfully logged into GitHub")
        
        # Step 2: Search for repositories
        logger.info(f"Searching for repository: {repo_to_search}")
        search_results = await automation.search_flow(
            url="https://github.com/search",
            search_selector=".header-search-input",
            submit_selector=".header-search-button",
            search_query=repo_to_search,
            results_selector=".repo-list-item"
        )
        
        if not search_results:
            logger.error("No search results found")
            return
            
        logger.info(f"Found {len(search_results)} repositories")
        
        # Step 3: Click the first result
        repo_links = await automation.extract_data({
            "strategy": "css_selector",
            "selector": ".repo-list-item a",
            "multiple": True,
            "attribute": "href"
        })
        
        if not repo_links:
            logger.error("No repository links found")
            return
            
        # Navigate to the first repository
        first_repo = repo_links[0]
        full_url = f"https://github.com{first_repo}" if first_repo.startswith('/') else first_repo
        logger.info(f"Navigating to repository: {full_url}")
        await automation.navigate_to(full_url)
        
        # Take screenshot of repository page
        await automation.take_screenshot(str(output_path / "repository.png"))
        
        # Step 4: Extract repository information
        logger.info("Extracting repository information")
        
        # Extract basic repository info
        repo_info = await automation.extract_data({
            "strategy": "css_selector",
            "selector": ".repository-content",
            "multiple": False,
            "children": [
                {"strategy": "css_selector", "selector": ".f1-light", "multiple": False},  # Description
                {"strategy": "css_selector", "selector": ".BorderGrid-row", "multiple": True}  # Info rows
            ]
        })
        
        # Save repository info to file
        with open(output_path / "repository_info.json", "w") as f:
            json.dump(repo_info, f, indent=2)
            
        # Extract file tree
        files = await automation.extract_data({
            "strategy": "css_selector",
            "selector": ".js-navigation-container .js-navigation-item",
            "multiple": True,
            "children": [
                {"strategy": "css_selector", "selector": ".js-navigation-open", "attribute": None},  # Filename
                {"strategy": "css_selector", "selector": ".js-navigation-open", "attribute": "href"}  # File link
            ]
        })
        
        # Save file tree to file
        with open(output_path / "file_tree.json", "w") as f:
            json.dump(files, f, indent=2)
            
        logger.info(f"GitHub demo completed successfully! Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error during GitHub demo execution: {e}")
    finally:
        # Stop the browser
        await automation.stop()

async def main():
    """Parse command-line arguments and run the appropriate demo."""
    parser = argparse.ArgumentParser(description="Native browser automation demo")
    parser.add_argument("--demo", choices=["wikipedia", "github"], default="wikipedia",
                        help="Demo to run (wikipedia or github)")
    parser.add_argument("--query", type=str, default="Python programming language",
                        help="Search query for Wikipedia demo")
    parser.add_argument("--browser", choices=["chrome", "firefox"], default="chrome",
                        help="Browser to use")
    parser.add_argument("--headless", action="store_true",
                        help="Run in headless mode")
    parser.add_argument("--output-dir", type=str, default="output",
                        help="Directory to save results")
    parser.add_argument("--proxy-host", type=str, default=None,
                        help="Proxy host (if using a proxy)")
    parser.add_argument("--proxy-port", type=str, default=None,
                        help="Proxy port (if using a proxy)")
    parser.add_argument("--extension", type=str, action="append", default=[],
                        help="Path to browser extension (.crx for Chrome, .xpi for Firefox)")
    parser.add_argument("--github-username", type=str, default=None,
                        help="GitHub username (for GitHub demo)")
    parser.add_argument("--github-repo", type=str, default="python/cpython",
                        help="GitHub repository to search for (for GitHub demo)")
    
    args = parser.parse_args()
    
    # Set up proxy configuration if provided
    proxy_config = None
    if args.proxy_host and args.proxy_port:
        proxy_config = {
            "host": args.proxy_host,
            "port": args.proxy_port
        }
    
    # Run the appropriate demo
    if args.demo == "wikipedia":
        await run_wikipedia_demo(
            search_query=args.query,
            browser_type=args.browser,
            headless=args.headless,
            output_dir=args.output_dir,
            proxy_config=proxy_config,
            extension_paths=args.extension
        )
    elif args.demo == "github":
        # Get GitHub credentials
        github_username = args.github_username or os.environ.get("GITHUB_USERNAME")
        github_password = os.environ.get("GITHUB_PASSWORD")
        
        if not github_username or not github_password:
            logger.error("GitHub username and password required for GitHub demo")
            logger.error("Set GITHUB_USERNAME and GITHUB_PASSWORD environment variables")
            return
        
        await run_github_demo(
            username=github_username,
            password=github_password,
            repo_to_search=args.github_repo,
            browser_type=args.browser,
            headless=args.headless,
            output_dir=f"{args.output_dir}/github",
            proxy_config=proxy_config,
            extension_paths=args.extension
        )

if __name__ == "__main__":
    asyncio.run(main()) 