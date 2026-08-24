from __future__ import annotations

import functools
import time

from typing import Any

from .errors import AraError
from ._utils import _find_member, _find_guild, _find_channel


# ============================================================
# Cooldown
# ============================================================


_buckets: dict[Any, dict[Any, float]] = {}


def _resolve_key(
    scope: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:

    if scope == "user":

        member = _find_member(args, kwargs)

        return getattr(member, "id", None)

    if scope == "guild":

        guild = _find_guild(args, kwargs)

        return getattr(guild, "id", None)

    if scope == "channel":

        channel = _find_channel(args, kwargs)

        return getattr(channel, "id", None)

    # "global"
    return "__global__"


def cooldown(
    seconds: float,
    *,
    scope: str = "user",
    message: str | None = None,
):
    """
    명령어 실행 주기를 제한한다.

    scope:
        "user"    - 사용자별 제한 (기본)
        "guild"   - 서버별 제한
        "channel" - 채널별 제한
        "global"  - 전체 제한

    남은 시간이 있으면 AraError를 발생시킨다.

    사용 예:

        @Ara.cooldown(5)
        async def ping(ctx):
            ...

        @Ara.cooldown(30, scope="guild")
        async def raid_alert(ctx):
            ...
    """

    def decorator(func):

        bucket = _buckets.setdefault(func, {})

        @functools.wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            key = _resolve_key(
                scope,
                args,
                kwargs,
            )

            now = time.monotonic()

            last = bucket.get(key)

            if last is not None:

                remaining = seconds - (now - last)

                if remaining > 0:

                    text = (
                        message
                        or f"{remaining:.1f}초 후에 "
                        "다시 시도해주세요."
                    )

                    raise AraError(text)

            bucket[key] = now

            return await func(
                *args,
                **kwargs,
            )

        return wrapper

    return decorator


__all__ = [
    "cooldown",
]
