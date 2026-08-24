from __future__ import annotations

import asyncio
import functools
import inspect
import threading
import time

from .errors import AraError


def rate_limit(
    calls: int,
    per: float,
    *,
    wait: bool = True,
):
    """
    토큰 버킷 방식으로 함수 호출 빈도를 제한한다.

    calls:
        기간(per) 동안 허용되는 최대 호출 횟수.

    per:
        기간 (초).

    wait:
        True  - 토큰이 생길 때까지 대기 후 실행.
        False - 토큰이 없으면 즉시 AraError 발생.
    """

    if not isinstance(calls, int):
        raise TypeError("calls must be an integer")

    if calls <= 0:
        raise ValueError("calls must be greater than 0")

    if per <= 0:
        raise ValueError("per must be greater than 0")

    def decorator(func):

        tokens = float(calls)
        last_refill = time.monotonic()

        async_lock = asyncio.Lock()
        sync_lock = threading.Lock()

        refill_rate = calls / per

        def refill():
            nonlocal tokens, last_refill

            now = time.monotonic()
            elapsed = now - last_refill

            if elapsed <= 0:
                return

            tokens = min(
                float(calls),
                tokens + elapsed * refill_rate,
            )

            last_refill = now

        # ----------------------------------------------------
        # Async
        # ----------------------------------------------------

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(
                *args,
                **kwargs,
            ):
                nonlocal tokens

                while True:

                    async with async_lock:
                        refill()

                        if tokens >= 1:
                            tokens -= 1
                            break

                    if not wait:
                        raise AraError(
                            "호출 한도를 초과했습니다. "
                            "잠시 후 다시 시도해주세요."
                        )

                    await asyncio.sleep(
                        max(0.01, 1 / refill_rate)
                    )

                return await func(
                    *args,
                    **kwargs,
                )

            return async_wrapper

        # ----------------------------------------------------
        # Sync
        # ----------------------------------------------------

        @functools.wraps(func)
        def sync_wrapper(
            *args,
            **kwargs,
        ):
            nonlocal tokens

            while True:

                with sync_lock:
                    refill()

                    if tokens >= 1:
                        tokens -= 1
                        break

                if not wait:
                    raise AraError(
                        "호출 한도를 초과했습니다. "
                        "잠시 후 다시 시도해주세요."
                    )

                time.sleep(
                    max(0.01, 1 / refill_rate)
                )

            return func(
                *args,
                **kwargs,
            )

        return sync_wrapper

    return decorator


__all__ = [
    "rate_limit",
]