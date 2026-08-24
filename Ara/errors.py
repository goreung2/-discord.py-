from __future__ import annotations


# ============================================================
# Ara Error
# ============================================================


class AraError(Exception):
    """
    Ara Framework 기본 예외.

    original:
        실제로 발생한 원본 예외.
    """

    def __init__(
        self,
        reason: str,
        *,
        original: BaseException | None = None,
    ):
        super().__init__(reason)

        self.reason = reason
        self.original = original


__all__ = [
    "AraError",
]
