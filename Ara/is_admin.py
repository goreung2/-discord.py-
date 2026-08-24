from __future__ import annotations

import functools

from .errors import AraError
from ._utils import _find_guild, _find_member, _permission_message


# ============================================================
# is_admin
# ============================================================


def is_admin(func):
    """
    Administrator 전용.

    ARA.ini:

    [permissions]
    admin = 관리자 권한이 필요합니다.

    [permissions.ban]
    admin = 이 명령어는 관리자만 사용할 수 있습니다.
    """

    try:

        from discord.ext import commands

    except ImportError:

        @functools.wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            message = _permission_message(
                func,
                "admin",
            )

            guild = _find_guild(
                args,
                kwargs,
            )

            member = _find_member(
                args,
                kwargs,
            )

            if guild is None:

                raise AraError(
                    message
                )

            if member is None:

                raise AraError(
                    message
                )

            permissions = getattr(
                member,
                "guild_permissions",
                None,
            )

            if not permissions:

                raise AraError(
                    message
                )

            if not permissions.administrator:

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
            "admin",
        )

        if ctx.guild is None:

            raise commands.CheckFailure(
                message
            )

        permissions = getattr(
            ctx.author,
            "guild_permissions",
            None,
        )

        if not permissions:

            raise commands.CheckFailure(
                message
            )

        if not permissions.administrator:

            raise commands.CheckFailure(
                message
            )

        return True

    return predicate(func)


__all__ = [
    "is_admin",
]
