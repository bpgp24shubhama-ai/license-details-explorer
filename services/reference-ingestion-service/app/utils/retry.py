from collections.abc import Awaitable, Callable
from typing import Any

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential


async def run_with_retry(
    fn: Callable[..., Awaitable[Any]],
    *args: Any,
    attempts: int = 3,
    base_seconds: float = 1.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=base_seconds, min=base_seconds, max=10),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    ):
        with attempt:
            return await fn(*args, **kwargs)

    return None
