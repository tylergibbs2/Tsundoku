import json

from quart import Response


class APIResponse(Response):
    def __init__(self, status: int=200, *args, **kwargs):
        result = kwargs.pop("result", None)
        error = kwargs.pop("error", None)
        self.status = status

        kwargs["content_type"] = "application/json"
        kwargs["response"] = self._generate(result, error)
        kwargs["status"] = status
        super().__init__(*args, **kwargs)

    def _generate(self, result, error):
        if result is None and error is None:
            self.status = 500
            return json.dumps({
                "status": 500,
                "error": "The server encountered an error producing a response."
            })
        elif result is None:
            return json.dumps({
                "status": self.status,
                "error": error
            })
        else:
            return json.dumps({
                "status": self.status,
                "result": result
            })
