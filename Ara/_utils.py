from __future__ import annotations

import configparser
import logging

from pathlib import Path
from typing import Any


logger = logging.getLogger("ara")


# ============================================================
# Internal Helpers
# ============================================================


def _find_bot(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any | None:

    for value in (*args, *kwargs.values()):

        if value is None:
            continue

        # Context
        if hasattr(value, "bot"):
            return value.bot

        # Interaction
        if hasattr(value, "client"):
            return value.client

        # Bot 자체
        if (
            hasattr(value, "reload_extension")
            and hasattr(value, "is_owner")
        ):
            return value

    return None


def _find_guild(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any | None:

    for value in (*args, *kwargs.values()):

        if value is None:
            continue

        if hasattr(value, "guild"):
            return value.guild

    return None


def _find_member(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any | None:

    for value in (*args, *kwargs.values()):

        if value is None:
            continue

        # Context
        if hasattr(value, "author"):
            return value.author

        # Interaction
        if hasattr(value, "user"):
            return value.user

        # Member 자체
        if hasattr(value, "guild_permissions"):
            return value

    return None


def _find_channel(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any | None:

    for value in (*args, *kwargs.values()):

        if value is None:
            continue

        # Context / Interaction / Message
        if hasattr(value, "channel"):
            return value.channel

        # Channel 자체
        if (
            hasattr(value, "send")
            and hasattr(value, "id")
            and not hasattr(value, "author")
        ):
            return value

    return None


def _find_respondable(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any | None:
    """
    사용자에게 메시지를 보낼 수 있는 대상을 찾는다.

    Context / Interaction 순으로 탐색한다.
    """

    interaction = _find_interaction(
        args,
        kwargs,
    )

    if interaction is not None:
        return interaction

    for value in (*args, *kwargs.values()):

        if value is None:
            continue

        if (
            hasattr(value, "send")
            and hasattr(value, "message")
        ):
            return value

    return None


async def _reply(
    target: Any,
    content: str,
    *,
    ephemeral: bool = False,
) -> None:
    """
    Context / Interaction 모두에 대응하는 응답 헬퍼.
    """

    if target is None:
        return

    # Interaction
    if (
        hasattr(target, "response")
        and hasattr(target, "followup")
    ):

        if not target.response.is_done():

            await target.response.send_message(
                content,
                ephemeral=ephemeral,
            )

        else:

            await target.followup.send(
                content,
                ephemeral=ephemeral,
            )

        return

    # Context
    if hasattr(target, "send"):

        await target.send(content)


def _find_interaction(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any | None:

    for value in (*args, *kwargs.values()):

        if value is None:
            continue

        if (
            hasattr(value, "response")
            and hasattr(value, "followup")
        ):
            return value

    return None


# ============================================================
# ARA.ini
# ============================================================


def _load_ini() -> configparser.ConfigParser:

    parser = configparser.ConfigParser()

    path = Path("ARA.ini")

    if not path.exists():
        return parser

    try:

        parser.read(
            path,
            encoding="utf-8",
        )

    except OSError as error:

        logger.warning(
            "[Ara] ARA.ini 로드 실패: %s",
            error,
        )

    return parser


def _load_retry_config() -> dict[str, Any]:
    """
    [retry]

    default = 3
    delay = 1
    backoff = true
    """

    config = {
        "retries": 3,
        "delay": 1.0,
        "backoff": True,
    }

    parser = _load_ini()

    if not parser.has_section("retry"):
        return config

    section = parser["retry"]

    try:

        if "default" in section:

            config["retries"] = max(
                1,
                int(section["default"]),
            )

        if "delay" in section:

            config["delay"] = max(
                0.0,
                float(section["delay"]),
            )

        if "backoff" in section:

            config["backoff"] = (
                section["backoff"].lower()
                in {
                    "1",
                    "true",
                    "yes",
                    "on",
                }
            )

    except ValueError as error:

        logger.warning(
            "[Ara] retry 설정값 오류: %s",
            error,
        )

    return config


def _permission_message(
    func,
    permission: str,
) -> str:
    """
    권한 실패 메시지를 ARA.ini에서 가져온다.

    우선순위:

        1. [permissions.module.qualname]
        2. [permissions.function]
        3. [permissions]
        4. Ara 기본 메시지
    """

    defaults = {
        "owner":
            "이 명령어는 봇 소유자만 사용할 수 있습니다.",

        "guild":
            "이 명령어는 서버에서만 사용할 수 있습니다.",

        "admin":
            "이 명령어는 관리자 권한이 필요합니다.",

        "dm":
            "이 명령어는 DM에서만 사용할 수 있습니다.",

        "nsfw":
            "이 명령어는 NSFW 채널에서만 사용할 수 있습니다.",

        "role":
            "이 명령어를 사용할 권한이 없습니다.",
    }

    fallback = defaults.get(
        permission,
        "이 기능을 사용할 권한이 없습니다.",
    )

    parser = _load_ini()

    if not parser.sections():
        return fallback

    module = getattr(
        func,
        "__module__",
        "",
    )

    qualname = getattr(
        func,
        "__qualname__",
        "",
    )

    function_name = getattr(
        func,
        "__name__",
        "",
    )

    sections = [
        f"permissions.{module}.{qualname}",
        f"permissions.{function_name}",
        "permissions",
    ]

    for section_name in sections:

        if not parser.has_section(
            section_name
        ):
            continue

        section = parser[section_name]

        if permission not in section:
            continue

        message = section[
            permission
        ].strip()

        if message:
            return message

    return fallback
