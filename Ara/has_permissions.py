from __future__ import annotations

import functools

from .errors import AraError
from ._utils import _find_member, _permission_message


# ============================================================
# has_permissions
# ============================================================


def has_permissions(**perms: bool):
    """
    지정한 Discord 권한을 모두 가지고 있어야 실행 가능.

    사용 예:

        @Ara.has_permissions(manage_messages=True)
        async def clear(ctx, amount: int): ...

        @Ara.has_permissions(kick_members=True, ban_members=True)
        async def kickban(ctx, member): ...

    권한 이름은 discord.Permissions의 속성명과 동일하게 사용한다.
    (manage_messages, kick_members, ban_members, manage_roles ...)
    """

    def decorator(func):

        @functools.wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            member = _find_member(
                args,
                kwargs,
            )

            permissions = getattr(
                member,
                "guild_permissions",
                None,
            )

            message = _permission_message(
                func,
                "role",
            )

            if permissions is None:

                raise AraError(message)

            missing = [
                name
                for name, required in perms.items()
                if required
                and not getattr(
                    permissions,
                    name,
                    False,
                )
            ]

            if missing:

                raise AraError(
                    message
                    + f" (필요 권한: {', '.join(missing)})"
                )

            return await func(
                *args,
                **kwargs,
            )

        return wrapper

    return decorator


__all__ = [
    "has_permissions",
]
