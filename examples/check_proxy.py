#!/usr/bin/env python3
"""
Proxy Connectivity Checker

This script provides a quick way to test if a proxy configuration is working correctly.
It connects to an IP checking service both directly and through the proxy to show
the difference in detected IP addresses.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to sys.path to import the browser_use package
sys.path.insert(0, str(Path(__file__).parent.parent))

from browser_use import NativeBrowserAutomation, BrowserType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def check_ip(use_proxy=False, proxy_host=None, proxy_port=None, 
                  proxy_username=None, proxy_password=None, headless=False):
    """
    Check your IP address with and without proxy to verify proxy functionality.
    
    Args:
        use_proxy: Whether to use a proxy
        proxy_host: Proxy host address
        proxy_port: Proxy port
        proxy_username: Proxy username for authentication (optional)
        proxy_password: Proxy password for authentication (optional)
        headless: Whether to run in headless mode
    """
    # Configure proxy if needed
    proxy_config = None
    if use_proxy and proxy_host and proxy_port:
        proxy_config = {
            "host": proxy_host,
            "port": proxy_port
        }
        if proxy_username and proxy_password:
            proxy_config["username"] = proxy_username
            proxy_config["password"] = proxy_password
    
    # Create browser automation
    automation = NativeBrowserAutomation(
        browser_type=BrowserType.CHROME,
        headless=headless,
        proxy_config=proxy_config
    )
    
    try:
        # Start the browser
        logger.info(f"Starting browser {'' if not use_proxy else 'with proxy configuration'}")
        await automation.start()
        
        # Navigate to IP checking service
        logger.info("Checking your IP address...")
        await automation.navigate_to("https://api.ipify.org?format=json")
        
        # Extract the IP address from the page
        html_content = await automation.browser.get_page_content()
        
        # The page should contain a JSON response like {"ip":"123.456.789.0"}
        try:
            # Extract JSON from the page (it's in a pre tag)
            ip_data = json.loads(html_content.split("<pre>")[1].split("</pre>")[0])
            ip_address = ip_data.get("ip", "Unknown")
            
            logger.info(f"Your detected IP address: {ip_address}")
            logger.info(f"Using proxy: {use_proxy}")
            
            return ip_address
        except Exception as e:
            logger.error(f"Error extracting IP address: {e}")
            return "Error"
    
    except Exception as e:
        logger.error(f"Error checking IP: {e}")
        return "Error"
    
    finally:
        # Stop the browser
        await automation.stop()

async def main():
    """Parse command-line arguments and run the proxy check."""
    parser = argparse.ArgumentParser(description="Proxy Connectivity Checker")
    parser.add_argument("--proxy-host", type=str, help="Proxy host address")
    parser.add_argument("--proxy-port", type=str, help="Proxy port")
    parser.add_argument("--proxy-username", type=str, help="Proxy username (optional)")
    parser.add_argument("--proxy-password", type=str, help="Proxy password (optional)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    
    # First check without proxy
    logger.info("=============================================")
    logger.info("Checking IP address without proxy...")
    direct_ip = await check_ip(use_proxy=False, headless=args.headless)
    
    # Then check with proxy if configured
    if args.proxy_host and args.proxy_port:
        logger.info("=============================================")
        logger.info("Checking IP address with proxy...")
        proxy_ip = await check_ip(
            use_proxy=True,
            proxy_host=args.proxy_host,
            proxy_port=args.proxy_port,
            proxy_username=args.proxy_username,
            proxy_password=args.proxy_password,
            headless=args.headless
        )
        
        logger.info("=============================================")
        logger.info("Proxy Test Results:")
        logger.info(f"Direct IP: {direct_ip}")
        logger.info(f"Proxy IP:  {proxy_ip}")
        
        if direct_ip != proxy_ip and proxy_ip != "Error":
            logger.info("PROXY IS WORKING CORRECTLY! The IPs are different.")
        else:
            logger.info("PROXY TEST FAILED. The IPs are the same or there was an error.")
    else:
        logger.info("=============================================")
        logger.info("No proxy configuration provided.")
        logger.info(f"Your direct IP address is: {direct_ip}")
        logger.info("To test with a proxy, use the --proxy-host and --proxy-port arguments.")

if __name__ == "__main__":
    asyncio.run(main()) 