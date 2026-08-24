from __future__ import annotations

import functools
import inspect
import logging

from .errors import AraError
from ._utils import _find_respondable, _reply


# ============================================================
# Catch
# ============================================================


def catch(
    *exceptions: type[BaseException],
    message: str | None = None,
    reraise: bool = False,
    ephemeral: bool = False,
    log: bool = True,
):
    """
    함수 실행 중 예외를 잡아 사용자에게 자동으로 안내 메시지를 보낸다.

    사용 예:

        @Ara.catch()
        async def buy(ctx, item: str):
            ...

        @Ara.catch(ValueError, message="잘못된 입력입니다.")
        async def divide(ctx, a: int, b: int):
            return a / b

    AraError는 error.reason을 그대로 사용자에게 전달한다.
    reraise=True로 설정하면 안내 후 예외를 다시 던진다
    (전역 에러 핸들러와 함께 사용할 때 유용).
    """

    handled = exceptions or (Exception,)

    def decorator(func):

        if not inspect.iscoroutinefunction(func):

            raise TypeError(
                "@Ara.catch는 async 함수에서만 "
                "사용할 수 있습니다."
            )

        logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            try:

                return await func(
                    *args,
                    **kwargs,
                )

            except handled as error:

                if isinstance(error, AraError):
                    text = error.reason

                elif message is not None:
                    text = message

                else:
                    text = f"오류가 발생했습니다: {error}"

                if log:

                    logger.exception(
                        "[Ara] %s() 예외 발생",
                        func.__qualname__,
                    )

                target = _find_respondable(
                    args,
                    kwargs,
                )

                await _reply(
                    target,
                    text,
                    ephemeral=ephemeral,
                )

                if reraise:
                    raise

                return None

        return wrapper

    return decorator


__all__ = [
    "catch",
]
