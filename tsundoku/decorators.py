from functools import wraps
from typing import Any, Callable, TYPE_CHECKING

from quart import current_app, abort

if TYPE_CHECKING:
    from tsundoku.user import User

    current_user = User(None)
else:
    from quart_auth import current_user


def deny_readonly(func: Callable) -> Callable:
    """A decorator to restrict route access to users with write permissions.

    This should be used to wrap a route handler (or view function) to
    enforce that only authenticated requests can access it. Note that
    it is important that this decorator be wrapped by the route
    decorator and not vice, versa, as below.

    .. code-block:: python

        @app.route('/')
        @deny_readonly
        async def index():
            ...

    If the request is not authenticated a
    `quart.exceptions.Unauthorized` exception will be raised.

    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if await current_user.is_authenticated and await current_user.readonly:
            abort(403)
        else:
            return await current_app.ensure_async(func)(*args, **kwargs)

    return wrapper
