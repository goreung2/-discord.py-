from __future__ import annotations

import functools

from .errors import AraError
from ._utils import _find_bot, _find_member, _permission_message


# ============================================================
# is_owner
# ============================================================


def is_owner(func):
    """
    Bot Owner 전용.

    ARA.ini:

    [permissions]
    owner = 봇 소유자만 사용할 수 있습니다.

    [permissions.secret]
    owner = 개발자만 사용할 수 있습니다.
    """

    try:

        from discord.ext import commands

    except ImportError:

        @functools.wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            bot = _find_bot(
                args,
                kwargs,
            )

            member = _find_member(
                args,
                kwargs,
            )

            message = _permission_message(
                func,
                "owner",
            )

            if bot is None:

                raise AraError(
                    message
                )

            if member is None:

                raise AraError(
                    message
                )

            try:

                allowed = await bot.is_owner(
                    member
                )

            except Exception as error:

                raise AraError(
                    "Bot Owner 확인에 실패했습니다.",
                    original=error,
                ) from error

            if not allowed:

                raise AraError(
                    message
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
            "owner",
        )

        try:

            allowed = await ctx.bot.is_owner(
                ctx.author
            )

        except Exception:

            allowed = False

        if not allowed:

            raise commands.CheckFailure(
                message
            )

        return True

    return predicate(func)


__all__ = [
    "is_owner",
]
