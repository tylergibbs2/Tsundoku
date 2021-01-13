import json
from typing import Any, Optional

from quart import Response


class APIResponse(Response):
    def __init__(self, status: int=200, result: Any=None, error: str=None, *args, **kwargs):
        kwargs["content_type"] = "application/json"
        kwargs["response"] = self._generate(status, result, error)
        kwargs["status"] = status
        super().__init__(*args, **kwargs)

    def _generate(self, status: int, result: Optional[Any], error: Optional[str]):
        if result is None and error is None:
            status = 500
            return json.dumps({
                "status": 500,
                "error": "The server encountered an error producing a response."
            })
        elif result is None:
            return json.dumps({
                "status": status,
                "error": error
            })
        else:
            return json.dumps({
                "status": status,
                "result": result
            })
