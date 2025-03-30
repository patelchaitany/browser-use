import logging
import sys
from typing import Optional

# Set up logging format
LOGGER_FORMAT = "%(levelname)-8s [%(name)s] %(message)s"

# Create a logger for the agent
agent_logger = logging.getLogger("agent")


def setup_logging(level: str = "INFO") -> None:
    """
    Set up logging for the browser-use agent.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers to avoid duplicate logs
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(LOGGER_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    root_logger.addHandler(console_handler)
    
    # Configure browser_use logger
    browser_use_logger = logging.getLogger("browser_use")
    browser_use_logger.setLevel(numeric_level)
    browser_use_logger.info("BrowserUse logging setup complete with level %s", level)
    
    # Configure agent logger
    agent_logger.setLevel(numeric_level)


def log_task_start(task: str) -> None:
    """Log the start of a task."""
    agent_logger.info("🚀 Starting task: %s", task)


def log_step(step_number: int) -> None:
    """Log the start of a new step."""
    agent_logger.info("📍 Step %d", step_number)


def log_eval(status: str, message: str) -> None:
    """Log the evaluation of a step."""
    icon = {
        "success": "👍",
        "failure": "❌",
        "unknown": "🤷"
    }.get(status.lower(), "🔄")
    agent_logger.info("%s Eval: %s - %s", icon, status.capitalize(), message)


def log_memory(message: str) -> None:
    """Log the agent's memory state."""
    agent_logger.info("🧠 Memory: %s", message)


def log_goal(goal: str) -> None:
    """Log the next goal."""
    agent_logger.info("🎯 Next goal: %s", goal)


def log_action(action_number: int, total_actions: int, action_json: str) -> None:
    """Log an action being taken."""
    agent_logger.info("🛠️  Action %d/%d: %s", action_number, total_actions, action_json)


def log_action_failure(attempt: int, max_attempts: int, error: str) -> None:
    """Log an action failure."""
    agent_logger.error("❌ Result failed %d/%d times:\n %s", attempt, max_attempts, error)


def log_action_success(message: str) -> None:
    """Log a successful action result."""
    agent_logger.info("✅ Result: %s", message)


def log_task_completed(success: bool) -> None:
    """Log task completion."""
    agent_logger.info("✅ Task completed")
    if success:
        agent_logger.info("✅ Successfully")
    else:
        agent_logger.info("❌ With failures") 