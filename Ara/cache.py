from __future__ import annotations

import functools
import inspect
import time

from typing import Any


# ============================================================
# Cache
# ============================================================


def cache(
    ttl: float = 60.0,
    *,
    maxsize: int = 256,
):
    """
    함수 결과를 일정 시간(ttl, 초) 동안 캐싱한다.
    API 호출, DB 조회처럼 비용이 큰 함수에 유용하다.

    인자는 hashable해야 한다.

    사용 예:

        @Ara.cache(ttl=300)
        async def get_user_profile(user_id: int):
            return await api.fetch_profile(user_id)

        @Ara.cache(ttl=10, maxsize=64)
        def get_config(key: str):
            return load_config(key)
    """

    def decorator(func):

        store: dict[Any, tuple[float, Any]] = {}

        def make_key(args, kwargs):

            return (
                args,
                tuple(sorted(kwargs.items())),
            )

        def is_valid(entry) -> bool:

            timestamp, _ = entry

            return (time.monotonic() - timestamp) < ttl

        def evict_if_full():

            if len(store) >= maxsize:

                oldest_key = min(
                    store,
                    key=lambda k: store[k][0],
                )

                store.pop(oldest_key, None)

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(
                *args,
                **kwargs,
            ):

                key = make_key(args, kwargs)

                entry = store.get(key)

                if entry is not None and is_valid(entry):

                    return entry[1]

                result = await func(
                    *args,
                    **kwargs,
                )

                evict_if_full()

                store[key] = (
                    time.monotonic(),
                    result,
                )

                return result

            async_wrapper.cache_clear = store.clear

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(
            *args,
            **kwargs,
        ):

            key = make_key(args, kwargs)

            entry = store.get(key)

            if entry is not None and is_valid(entry):

                return entry[1]

            result = func(
                *args,
                **kwargs,
            )

            evict_if_full()

            store[key] = (
                time.monotonic(),
                result,
            )

            return result

        sync_wrapper.cache_clear = store.clear

        return sync_wrapper

    return decorator


__all__ = [
    "cache",
]
