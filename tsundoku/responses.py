from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Success(BaseModel, Generic[T]):
    """The standard success envelope: ``{"status": ..., "result": ...}``.

    Endpoints declare ``Success[ConcreteModel]`` as their return type, so
    FastAPI derives a fully typed response schema for the payload rather
    than emitting an opaque object.
    """

    status: int = 200
    result: T


class ErrorEnvelope(BaseModel):
    """The standard error envelope: ``{"status": ..., "error": ...}``."""

    status: int
    error: str


class APIError(Exception):
    """An error raised inside an API handler.

    The registered exception handler turns this into an
    :class:`ErrorEnvelope` with a matching HTTP status code.
    """

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
