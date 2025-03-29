/**
 * buildDomTree.js
 * 
 * Script to extract a DOM tree representation with a focus on interactive elements.
 * This script is executed in the browser context by the DOM service.
 * 
 * The result is a tree structure representing the DOM with relevant information
 * for extracting interactive elements and their properties.
 */

(options) => {
  function buildDomTree(rootNode, options = {}) {
    // Default options
    const defaultOptions = {
      doHighlightElements: false,
      focusHighlightIndex: -1,
      viewportExpansion: 500
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    // Track index for potentially highlighting elements
    let interactiveElementIndex = 0;
    
    // Create a collection for highlight elements
    const highlightElements = [];
    
    // Get viewport
    const viewport = {
      width: window.innerWidth,
      height: window.innerHeight
    };
    
    // Expanded viewport for detecting elements that might be just outside view
    const expandedViewport = {
      top: -mergedOptions.viewportExpansion,
      left: -mergedOptions.viewportExpansion,
      bottom: viewport.height + mergedOptions.viewportExpansion,
      right: viewport.width + mergedOptions.viewportExpansion
    };
    
    // Check if an element is in the expanded viewport
    function isInExpandedViewport(rect) {
      return !(
        rect.bottom < expandedViewport.top ||
        rect.top > expandedViewport.bottom ||
        rect.right < expandedViewport.left ||
        rect.left > expandedViewport.right
      );
    }
    
    // Check if an element is visible
    function isVisible(element) {
      if (!element) return false;
      
      const style = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      
      return style.display !== 'none' &&
             style.visibility !== 'hidden' &&
             style.opacity !== '0' &&
             rect.width > 0 &&
             rect.height > 0;
    }
    
    // Check if an element is interactive
    function isInteractive(element) {
      // Interactive tag names
      const interactiveTags = [
        'a', 'button', 'input', 'select', 'textarea', 'details',
        'audio', 'video', 'iframe', 'menuitem'
      ];
      
      // Interactive roles
      const interactiveRoles = [
        'button', 'link', 'checkbox', 'menuitem', 'tab', 'switch',
        'radio', 'combobox', 'slider', 'menu', 'menubar'
      ];
      
      const tagName = element.tagName.toLowerCase();
      const role = element.getAttribute('role');
      
      // Check if element has interactive tag
      if (interactiveTags.includes(tagName)) {
        return true;
      }
      
      // Check if element has interactive role
      if (role && interactiveRoles.includes(role)) {
        return true;
      }
      
      // Check for event handlers
      for (const attr of element.attributes) {
        if (attr.name.startsWith('on') || attr.name === 'onclick') {
          return true;
        }
      }
      
      // Check for tabindex
      if (element.hasAttribute('tabindex') && element.getAttribute('tabindex') !== '-1') {
        return true;
      }
      
      // Check for clickable cursors
      const cursor = window.getComputedStyle(element).cursor;
      if (cursor === 'pointer') {
        return true;
      }
      
      return false;
    }
    
    // Process a DOM node and build its tree representation
    function processNode(node) {
      if (!node) return null;
      
      // Skip non-element nodes
      if (node.nodeType !== Node.ELEMENT_NODE) {
        return null;
      }
      
      // Skip invisible elements
      if (!isVisible(node)) {
        return null;
      }
      
      const tagName = node.tagName.toLowerCase();
      
      // Skip certain elements
      if (['script', 'style', 'noscript', 'meta', 'link'].includes(tagName)) {
        return null;
      }
      
      // Get bounding client rect
      const rect = node.getBoundingClientRect();
      
      // Check if in expanded viewport, skip if not
      if (!isInExpandedViewport(rect)) {
        return null;
      }
      
      // Collect attributes
      const attributes = {};
      for (const attr of node.attributes) {
        attributes[attr.name] = attr.value;
      }
      
      // Check if interactive
      const interactive = isInteractive(node);
      
      // Collect text content
      const text = node.innerText || node.textContent || '';
      
      // Create node representation
      const nodeRepresentation = {
        tagName,
        id: node.id || null,
        className: node.className || null,
        attributes,
        text: text.trim(),
        boundingBox: {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height
        },
        interactive
      };
      
      // If this is an interactive element, add it to potential highlight elements
      // and add its index
      if (interactive) {
        nodeRepresentation.interactiveIndex = interactiveElementIndex;
        
        // Add to highlight elements if highlighting is enabled
        if (mergedOptions.doHighlightElements) {
          highlightElements.push({
            index: interactiveElementIndex,
            element: node,
            rect
          });
        }
        
        interactiveElementIndex++;
      }
      
      // Process children
      const children = [];
      for (const child of node.children) {
        const childRepresentation = processNode(child);
        if (childRepresentation) {
          children.push(childRepresentation);
        }
      }
      
      if (children.length > 0) {
        nodeRepresentation.children = children;
      }
      
      return nodeRepresentation;
    }
    
    // Build the tree starting from the root node
    const tree = processNode(rootNode);
    
    // Highlight elements if requested
    if (mergedOptions.doHighlightElements && highlightElements.length > 0) {
      highlightInteractiveElements(
        highlightElements,
        mergedOptions.focusHighlightIndex
      );
    }
    
    return tree;
  }
  
  // Function to highlight interactive elements
  function highlightInteractiveElements(elements, focusIndex = -1) {
    // Remove any existing highlights
    const existingHighlights = document.querySelectorAll('.browser-use-highlight');
    existingHighlights.forEach(el => el.remove());
    
    // Create a container for highlights
    const container = document.createElement('div');
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.pointerEvents = 'none';
    container.style.zIndex = '2147483647'; // Max z-index
    document.body.appendChild(container);
    
    // Create highlights for each element
    elements.forEach(({ index, element, rect }) => {
      const highlight = document.createElement('div');
      highlight.className = 'browser-use-highlight';
      highlight.style.position = 'absolute';
      highlight.style.left = `${rect.x}px`;
      highlight.style.top = `${rect.y}px`;
      highlight.style.width = `${rect.width}px`;
      highlight.style.height = `${rect.height}px`;
      highlight.style.border = `2px solid ${index === focusIndex ? 'red' : 'blue'}`;
      highlight.style.backgroundColor = `${index === focusIndex ? 'rgba(255,0,0,0.1)' : 'rgba(0,0,255,0.1)'}`;
      highlight.style.boxSizing = 'border-box';
      highlight.style.pointerEvents = 'none';
      
      // Add index as label
      const label = document.createElement('div');
      label.style.position = 'absolute';
      label.style.top = '0';
      label.style.left = '0';
      label.style.backgroundColor = index === focusIndex ? 'red' : 'blue';
      label.style.color = 'white';
      label.style.fontSize = '12px';
      label.style.padding = '2px 5px';
      label.style.borderRadius = '3px';
      label.textContent = index.toString();
      highlight.appendChild(label);
      
      container.appendChild(highlight);
    });
    
    // Automatically remove highlights after 5 seconds
    setTimeout(() => {
      container.remove();
    }, 5000);
  }
  
  // Execute buildDomTree with provided options
  const tree = buildDomTree(document.body, options);
  
  // Return the result as JSON string
  return JSON.stringify(tree);
}
