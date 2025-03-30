import asyncio
import functools
import logging
import time
from typing import Any, Callable, Optional, TypeVar, cast

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Any])


def time_execution_sync(message: str) -> Callable[[F], F]:
    """Decorator to time synchronous function execution time."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000
            logger.debug(f"{message}: {execution_time:.2f}ms")
            return result

        return cast(F, wrapper)

    return decorator


def time_execution_async(message: str) -> Callable[[AsyncF], AsyncF]:
    """Decorator to time asynchronous function execution time."""

    def decorator(func: AsyncF) -> AsyncF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000
            logger.debug(f"{message}: {execution_time:.2f}ms")
            return result

        return cast(AsyncF, wrapper)

    return decorator 