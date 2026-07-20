from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, PrivateAttr

if TYPE_CHECKING:
    from tsundoku.app import TsundokuAppState


class DBModel(BaseModel):
    """Base class for database-backed domain models.

    These models double as the API's response objects: FastAPI derives
    their response schema directly, so there is no separate DTO layer and
    no ``to_dict``. The owning application state is held as a private
    attribute (``_app``) so it is never serialized, and re-exposed as the
    ``app`` property for the persistence methods on each model.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _app: TsundokuAppState = PrivateAttr()

    @property
    def app(self) -> TsundokuAppState:
        return self._app

    def _bind(self, app: TsundokuAppState) -> Self:
        """Attach the application state and return ``self`` for chaining."""
        self._app = app
        return self
