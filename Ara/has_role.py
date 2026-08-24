from __future__ import annotations

import functools

from .errors import AraError
from ._utils import _find_member, _permission_message


# ============================================================
# has_role
# ============================================================


def has_role(*roles: str | int):
    """
    지정한 역할(이름 또는 ID) 중 하나라도 가지고 있어야 실행 가능.

    사용 예:

        @Ara.has_role("Moderator")
        async def warn(ctx, member): ...

        @Ara.has_role(123456789012345678, "Admin")
        async def announce(ctx): ...

    ARA.ini:

    [permissions]
    role = 이 명령어를 사용할 권한이 없습니다.
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

            member_roles = getattr(
                member,
                "roles",
                None,
            )

            if member_roles is None:

                raise AraError(
                    _permission_message(
                        func,
                        "role",
                    )
                )

            allowed = False

            for role in member_roles:

                if (
                    role.id in roles
                    or role.name in roles
                ):

                    allowed = True
                    break

            if not allowed:

                raise AraError(
                    _permission_message(
                        func,
                        "role",
                    )
                )

            return await func(
                *args,
                **kwargs,
            )

        return wrapper

    return decorator


__all__ = [
    "has_role",
]
