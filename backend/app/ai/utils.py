import asyncio
import logging

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code


class RateLimitError(ProviderError):
    pass


class TimeoutError_(ProviderError):
    pass


async def retry_async(
    coro_factory,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff: float = 2.0,
    retryable_exceptions: tuple = (RateLimitError, TimeoutError_),
):
    last_exc = None
    delay = base_delay

    for attempt in range(max_retries + 1):
        try:
            return await coro_factory()
        except retryable_exceptions as e:
            last_exc = e
            if attempt < max_retries:
                jitter = delay * (0.5 + asyncio.get_event_loop().time() % 0.5)
                logger.warning(
                    "Retry %d/%d after %s: %s",
                    attempt + 1, max_retries, e.message, f"{delay:.1f}s",
                )
                await asyncio.sleep(min(delay, max_delay))
                delay *= backoff
            else:
                logger.error("All retries exhausted: %s", e.message)

    raise last_exc
