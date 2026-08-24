from __future__ import annotations

import functools
import inspect

from .errors import AraError
from ._utils import _find_interaction


# ============================================================
# Auto Reply
# ============================================================


def auto_reply(
    *,
    ephemeral: bool = False,
):
    """
    함수 반환값을 Discord에 자동 전송.

    return "Hello"

    -> Discord에 Hello 전송
    """

    def decorator(func):

        if not inspect.iscoroutinefunction(func):

            raise TypeError(
                "@Ara.auto_reply는 async 함수에서만 "
                "사용할 수 있습니다."
            )

        @functools.wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            result = await func(
                *args,
                **kwargs,
            )

            if result is None:

                return None

            # --------------------------------------------
            # Interaction
            # --------------------------------------------

            interaction = _find_interaction(
                args,
                kwargs,
            )

            if interaction is not None:

                if not interaction.response.is_done():

                    await interaction.response.send_message(
                        result,
                        ephemeral=ephemeral,
                    )

                else:

                    await interaction.followup.send(
                        result,
                        ephemeral=ephemeral,
                    )

                return result

            # --------------------------------------------
            # Context
            # --------------------------------------------

            ctx = next(
                (
                    value
                    for value
                    in (*args, *kwargs.values())
                    if (
                        hasattr(value, "send")
                        and hasattr(value, "message")
                    )
                ),
                None,
            )

            if ctx is not None:

                await ctx.send(
                    result
                )

                return result

            raise AraError(
                f"{func.__qualname__}의 "
                "Discord Context를 찾을 수 없습니다."
            )

        return wrapper

    return decorator


__all__ = [
    "auto_reply",
]
