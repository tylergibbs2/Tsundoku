from datetime import datetime
import json
from typing import Any

from quart import Response


def recursive_json_modify(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: recursive_json_modify(v) for k, v in obj.items()}
    if isinstance(obj, list) or isinstance(obj, set):
        return [recursive_json_modify(item) for item in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()

    return obj


class APIResponse(Response):
    def __init__(
        self,
        status: int = 200,
        result: Any = None,
        error: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        kwargs["content_type"] = "application/json"
        kwargs["response"] = self._generate(status, result, error)
        kwargs["status"] = status
        super().__init__(*args, **kwargs)

    def _generate(self, status: int, result: Any | None, error: str | None) -> str:
        if result is None and error is None:
            status = 500
            return json.dumps(
                {
                    "status": 500,
                    "error": "The server encountered an error producing a response.",
                },
                ensure_ascii=False,
            )
        if result is None:
            return json.dumps({"status": status, "error": error}, ensure_ascii=False)
        return json.dumps(
            {"status": status, "result": recursive_json_modify(result)},
            ensure_ascii=False,
        )
