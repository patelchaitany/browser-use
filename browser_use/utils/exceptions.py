class BrowserUseException(Exception):
    """Base exception for all browser use errors"""
    pass


class ElementNotFoundException(BrowserUseException):
    """Raised when an element is not found on the page"""
    pass


class BrowserOperationError(BrowserUseException):
    """Raised when a browser operation fails"""
    pass 