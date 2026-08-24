from __future__ import annotations

import functools

from .errors import AraError
from ._utils import _find_guild, _permission_message


# ============================================================
# is_guild
# ============================================================


def is_guild(func):
    """
    Guild 전용.

    ARA.ini:

    [permissions]
    guild = 서버에서만 사용할 수 있습니다.

    [permissions.test]
    guild = DM에서는 사용할 수 없습니다.
    """

    try:

        from discord.ext import commands

    except ImportError:

        @functools.wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            guild = _find_guild(
                args,
                kwargs,
            )

            if guild is None:

                raise AraError(
                    _permission_message(
                        func,
                        "guild",
                    )
                )

            return await func(
                *args,
                **kwargs,
            )

        return wrapper

    @commands.check
    async def predicate(ctx):

        message = _permission_message(
            func,
            "guild",
        )

        if ctx.guild is None:

            raise commands.CheckFailure(
                message
            )

        return True

    return predicate(func)


__all__ = [
    "is_guild",
]
