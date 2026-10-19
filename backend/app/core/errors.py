"""Application errors converted to HTTP responses by FastAPI."""

from __future__ import annotations


class AppError(Exception):
    """Expected application failure with an HTTP status code."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
