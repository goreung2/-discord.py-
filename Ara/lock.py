from __future__ import annotations

import asyncio
import functools

from typing import Any

from .errors import AraError
from ._utils import _find_member


# ============================================================
# Lock
# ============================================================


_locks: dict[Any, dict[Any, asyncio.Lock]] = {}


def lock(
    *,
    scope: str = "user",
    wait: bool = False,
    message: str = "이전 요청이 아직 처리 중입니다. 잠시 후 다시 시도해주세요.",
):
    """
    함수의 동시 실행을 막는다. (버튼 연타, 중복 명령 방지 등)

    scope:
        "user"   - 사용자별로 동시 실행 방지 (기본)
        "global" - 함수 전체를 통틀어 동시 실행 방지

    wait:
        False (기본) - 이미 실행 중이면 즉시 AraError 발생
        True         - 이미 실행 중이면 끝날 때까지 대기 후 순차 실행

    사용 예:

        @Ara.lock()                      # 사용자당 중복 클릭 방지
        async def buy(ctx, item: str):
            ...

        @Ara.lock(scope="global", wait=True)  # 전역 자원 보호
        async def update_leaderboard():
            ...
    """

    def decorator(func):

        locks = _locks.setdefault(func, {})

        @functools.wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            if scope == "global":
                key = "__global__"

            else:

                member = _find_member(
                    args,
                    kwargs,
                )

                key = getattr(member, "id", None)

            func_lock = locks.setdefault(
                key,
                asyncio.Lock(),
            )

            if not wait and func_lock.locked():

                raise AraError(message)

            async with func_lock:

                return await func(
                    *args,
                    **kwargs,
                )

        return wrapper

    return decorator


__all__ = [
    "lock",
]
