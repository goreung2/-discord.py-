from __future__ import annotations

import functools
import inspect
import logging


# ============================================================
# Log
# ============================================================


def log(
    level: int = logging.INFO,
    *,
    name: str | None = None,
):
    """
    함수 실행 로그.
    """

    def decorator(func):

        logger = logging.getLogger(
            name or func.__module__
        )

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(
                *args,
                **kwargs,
            ):

                logger.log(
                    level,
                    "[Ara] %s() 실행",
                    func.__qualname__,
                )

                try:

                    result = await func(
                        *args,
                        **kwargs,
                    )

                    logger.log(
                        level,
                        "[Ara] %s() 성공",
                        func.__qualname__,
                    )

                    return result

                except Exception:

                    logger.exception(
                        "[Ara] %s() 실패",
                        func.__qualname__,
                    )

                    raise

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(
            *args,
            **kwargs,
        ):

            logger.log(
                level,
                "[Ara] %s() 실행",
                func.__qualname__,
            )

            try:

                result = func(
                    *args,
                    **kwargs,
                )

                logger.log(
                    level,
                    "[Ara] %s() 성공",
                    func.__qualname__,
                )

                return result

            except Exception:

                logger.exception(
                    "[Ara] %s() 실패",
                    func.__qualname__,
                )

                raise

        return sync_wrapper

    return decorator


__all__ = [
    "log",
]
