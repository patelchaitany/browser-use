# Proxy Configuration Updates

## Using Proxies with Browser Automation

The browser automation system now supports proxy configuration for both the standard and AI-driven automation. This feature allows you to route your browser traffic through proxy servers for various purposes including:

- Accessing geo-restricted content
- Distributing web scraping requests across multiple IPs
- Testing websites from different geographical locations
- Enhancing privacy during automated browsing
- Working within corporate networks that require proxies

### Command-Line Interface

The demo scripts support proxy configuration via command-line arguments:

```bash
# Basic proxy configuration
python ai_driven_browser_demo.py --task "Your task" --proxy-host "192.168.1.1" --proxy-port "8080"

# For native browser demo
python native_browser_demo.py --action "search" --keyword "python" --proxy-host "192.168.1.1" --proxy-port "8080"
```

### Python API

```python
from browser_use import NativeBrowserAutomation, BrowserType

# Configure proxy
proxy_config = {
    "host": "192.168.1.100",
    "port": "8080",
    # Optional authentication
    "username": "proxyuser",
    "password": "proxypassword"
}

# Create browser automation with proxy
automation = NativeBrowserAutomation(
    browser_type=BrowserType.CHROME,
    proxy_config=proxy_config
)
```

### Example Script

A dedicated example is available showing how to use proxies with the AI-driven browser automation:

```bash
# Run the proxy example
python examples/proxy_example.py
```

This example:
1. Configures a browser with proxy settings
2. Verifies the proxy is working by checking the IP address
3. Performs a location-based search
4. Extracts results that would typically be different based on location

For detailed documentation on proxy features, see [README_AI_BROWSER.md](README_AI_BROWSER.md#proxy-configuration). 