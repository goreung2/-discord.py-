from __future__ import annotations

import asyncio
import functools
import inspect
import time

from .errors import AraError
from ._utils import _load_retry_config


# ============================================================
# Retry
# ============================================================


def retry(
    retries: int | None = None,
    *,
    delay: float | None = None,
    backoff: bool | None = None,
    exceptions: tuple[
        type[BaseException],
        ...
    ] = (Exception,),
):
    """
    함수 실행 실패 시 재시도.

    retries:
        최대 실행 횟수.

    delay:
        재시도 전 대기시간.

    backoff:
        exponential backoff.

    exceptions:
        재시도할 예외.
    """

    config = _load_retry_config()

    attempts = (
        config["retries"]
        if retries is None
        else max(1, retries)
    )

    base_delay = (
        config["delay"]
        if delay is None
        else max(0.0, delay)
    )

    use_backoff = (
        config["backoff"]
        if backoff is None
        else backoff
    )

    def decorator(func):

        # ------------------------------------------------
        # Async
        # ------------------------------------------------

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(
                *args,
                **kwargs,
            ):

                for attempt in range(
                    1,
                    attempts + 1,
                ):

                    try:

                        return await func(
                            *args,
                            **kwargs,
                        )

                    except asyncio.CancelledError:

                        raise

                    except exceptions as error:

                        if attempt >= attempts:

                            raise AraError(
                                f"{func.__qualname__} "
                                "실행에 실패했습니다.",
                                original=error,
                            ) from error

                        wait = (
                            base_delay
                            * (
                                2 ** (attempt - 1)
                                if use_backoff
                                else 1
                            )
                        )

                        if wait:

                            await asyncio.sleep(
                                wait
                            )

            return async_wrapper

        # ------------------------------------------------
        # Sync
        # ------------------------------------------------

        @functools.wraps(func)
        def sync_wrapper(
            *args,
            **kwargs,
        ):

            for attempt in range(
                1,
                attempts + 1,
            ):

                try:

                    return func(
                        *args,
                        **kwargs,
                    )

                except exceptions as error:

                    if attempt >= attempts:

                        raise AraError(
                            f"{func.__qualname__} "
                            "실행에 실패했습니다.",
                            original=error,
                        ) from error

                    wait = (
                        base_delay
                        * (
                            2 ** (attempt - 1)
                            if use_backoff
                            else 1
                        )
                    )

                    if wait:

                        time.sleep(
                            wait
                        )

        return sync_wrapper

    return decorator


__all__ = [
    "retry",
]
