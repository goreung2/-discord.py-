from __future__ import annotations

from .errors import AraError
from .is_owner import is_owner
from .is_admin import is_admin
from .is_guild import is_guild
from .has_role import has_role
from .has_permissions import has_permissions
from .cooldown import cooldown
from .rate_limit import rate_limit
from .lock import lock
from .catch import catch
from .retry import retry
from .auto_reply import auto_reply
from .cache import cache
from .log import log


class Ara:
    """Minimal Ara Framework API."""

    AraError = AraError

    is_owner = staticmethod(is_owner)
    is_admin = staticmethod(is_admin)
    is_guild = staticmethod(is_guild)
    has_role = staticmethod(has_role)
    has_permissions = staticmethod(has_permissions)

    cooldown = staticmethod(cooldown)
    rate_limit = staticmethod(rate_limit)
    lock = staticmethod(lock)

    catch = staticmethod(catch)
    retry = staticmethod(retry)

    auto_reply = staticmethod(auto_reply)

    cache = staticmethod(cache)
    log = staticmethod(log)


__all__ = [
    "Ara",
    "AraError",
    "is_owner",
    "is_admin",
    "is_guild",
    "has_role",
    "has_permissions",
    "cooldown",
    "rate_limit",
    "lock",
    "catch",
    "retry",
    "auto_reply",
    "cache",
    "log",
]
