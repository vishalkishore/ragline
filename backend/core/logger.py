import asyncio
import logging
import traceback
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [CALLER: %(name)s] - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S.%f",
    )


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get a logger specifically for an agent"""
    return logging.getLogger(agent_name)


def log_exception(
    logger: logging.Logger, error: Exception, additional_msg: str = ""
) -> None:
    logger.error(f"{error}\n{additional_msg}\n{traceback.format_exc()}")


def log_execution(func: Callable[P, Any]) -> Callable[P, Any]:
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            logger = (
                getattr(args[0], "agent_name", func.__name__) if args else func.__name__
            )
            logger = logging.getLogger(logger)
            try:
                logger.info(f"Executing {func.__name__}")
                result = await func(*args, **kwargs)
                logger.info(f"Completed {func.__name__}")
                return result
            except Exception as e:
                log_exception(logger, e, f"Error in {func.__name__}")
                raise

        return async_wrapper
    else:

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            logger = (
                getattr(args[0], "agent_name", func.__name__)
                if args
                else (func.__name__)
            )
            logger = logging.getLogger(logger)
            try:
                logger.info(f"Executing {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"Completed {func.__name__}")
                return result
            except Exception as e:
                log_exception(logger, e, f"Error in {func.__name__}")
                raise

        return sync_wrapper
