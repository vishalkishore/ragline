import logging
import traceback
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [AGENT: %(name)s] - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S.%f",
    )


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get a logger specifically for an agent"""
    return logging.getLogger(agent_name)


def log_exception(
    logger: logging.Logger, error: Exception, additional_msg: str = ""
) -> None:
    logger.error(f"{error}\n{additional_msg}\n{traceback.format_exc()}")


# Decorator to log the execution of a function and handle exceptions
def log_execution(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        agent_name = (
            args[0].agent_name
            if args and hasattr(args[0], "agent_name")
            else func.__name__
        )
        logger = logging.getLogger(agent_name)
        try:
            logger.info(f"Executing {func.__name__}")
            result = await func(*args, **kwargs)
            logger.info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            log_exception(logger, e, f"Error in {func.__name__}")
            raise

    return wrapper
