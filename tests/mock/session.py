from collections.abc import Callable, Generator
import json as _json
from typing import Any, Self

Responder = Callable[[str, dict[str, Any]], "MockResponse"]


class UnstubbedRequestError(BaseException):
    """Raised when app code makes an HTTP request the test never stubbed.

    This deliberately inherits from :class:`BaseException` rather than
    :class:`Exception`. Several call sites wrap their requests in a broad
    ``except Exception`` and convert any failure into a benign-looking value
    (``WebhookBase.is_valid`` returns ``False``, for instance). If this error
    were catchable by those handlers, a test that forgot to stub a request
    would still pass -- just for entirely the wrong reason. Inheriting from
    ``BaseException`` means an unstubbed request always fails the test loudly,
    the same trick pytest uses for its own ``Failed`` outcome.
    """


class MockResponse:
    """A stand-in for :class:`aiohttp.ClientResponse`.

    Only the surface the app actually touches is implemented: ``status``,
    ``headers``, ``json()``, ``text()`` and ``read()``.

    When ``json=`` is supplied without ``text=``, the text body is derived from
    it. The qBittorrent and Transmission clients read ``resp.text()`` and parse
    it with ``json.loads`` themselves rather than calling ``resp.json()``, so
    both accessors need to agree on the payload.
    """

    def __init__(
        self,
        status: int = 200,
        *,
        json: Any = None,
        text: str | None = None,
        body: bytes = b"",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self.headers = headers or {}
        self._json = json
        if text is None:
            text = _json.dumps(json) if json is not None else ""
        self._text = text
        self._body = body

    async def json(self, **_: Any) -> Any:
        return self._json

    async def text(self, **_: Any) -> str:
        return self._text

    async def read(self) -> bytes:
        return self._body

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None


class _RequestContextManager:
    """Mirrors aiohttp's request handle, which is awaitable *and* an async CM.

    The codebase uses both forms -- ``async with session.get(...)`` in the
    download clients and ``await session.post(...)`` in the webhooks -- so the
    double life is required, not incidental.
    """

    def __init__(self, response: MockResponse) -> None:
        self._response = response

    def __await__(self) -> Generator[Any, None, MockResponse]:
        async def _resolve() -> MockResponse:
            return self._response

        return _resolve().__await__()

    async def __aenter__(self) -> MockResponse:
        return self._response

    async def __aexit__(self, *_: object) -> None:
        return None


class RecordedRequest:
    def __init__(self, method: str, url: str, kwargs: dict[str, Any]) -> None:
        self.method = method
        self.url = url
        self.kwargs = kwargs

    @property
    def params(self) -> dict[str, Any]:
        return self.kwargs.get("params") or {}

    @property
    def json(self) -> Any:
        return self.kwargs.get("json")

    @property
    def headers(self) -> dict[str, str]:
        return self.kwargs.get("headers") or {}

    def __repr__(self) -> str:
        return f"<RecordedRequest {self.method} {self.url}>"


def _always(response: MockResponse) -> Responder:
    """Adapt a prepared response into a responder callable."""

    def responder(_url: str, _kwargs: dict[str, Any]) -> MockResponse:
        return response

    return responder


class MockClientSession:
    """An offline stand-in for :class:`aiohttp.ClientSession`.

    Stub responses with :meth:`stub`; every request is recorded on
    :attr:`requests` for assertions. Any request that matches no stub raises
    :class:`UnstubbedRequestError`, so tests can never silently exercise a
    network path they did not intend to.
    """

    def __init__(self) -> None:
        self.requests: list[RecordedRequest] = []
        self.closed = False
        self._stubs: list[tuple[str, str, Responder]] = []

    def stub(
        self,
        method: str,
        url: str,
        response: MockResponse | Responder | None = None,
        **response_kwargs: Any,
    ) -> None:
        """Register a response for ``method`` requests whose URL starts with ``url``.

        Pass either a prepared :class:`MockResponse`, a callable taking
        ``(url, kwargs)``, or keyword arguments forwarded to ``MockResponse``
        (``status=``, ``json=``, ``text=``, ``body=``). Later stubs take
        precedence, so a fixture's default can be overridden per-test.
        """
        if response is None:
            response = MockResponse(**response_kwargs)

        responder: Responder = _always(response) if isinstance(response, MockResponse) else response
        self._stubs.append((method.upper(), url, responder))

    def _dispatch(self, method: str, url: str, kwargs: dict[str, Any]) -> _RequestContextManager:
        self.requests.append(RecordedRequest(method, url, kwargs))

        for stub_method, stub_url, responder in reversed(self._stubs):
            if stub_method == method and url.startswith(stub_url):
                return _RequestContextManager(responder(url, kwargs))

        raise UnstubbedRequestError(f"Unstubbed HTTP request: {method} {url}\nRegister one with session.stub({method!r}, {url!r}, json=...) or assert the code path does not make this call.")

    def get(self, url: str, **kwargs: Any) -> _RequestContextManager:
        return self._dispatch("GET", url, kwargs)

    def post(self, url: str, **kwargs: Any) -> _RequestContextManager:
        return self._dispatch("POST", url, kwargs)

    def head(self, url: str, **kwargs: Any) -> _RequestContextManager:
        return self._dispatch("HEAD", url, kwargs)

    def put(self, url: str, **kwargs: Any) -> _RequestContextManager:
        return self._dispatch("PUT", url, kwargs)

    def delete(self, url: str, **kwargs: Any) -> _RequestContextManager:
        return self._dispatch("DELETE", url, kwargs)

    def request(self, method: str, url: str, **kwargs: Any) -> _RequestContextManager:
        return self._dispatch(method.upper(), url, kwargs)

    async def close(self) -> None:
        self.closed = True

    def requests_for(self, method: str, url: str = "") -> list[RecordedRequest]:
        """Every recorded request matching ``method`` and the ``url`` prefix."""
        return [r for r in self.requests if r.method == method.upper() and r.url.startswith(url)]

    def assert_no_requests(self) -> None:
        assert not self.requests, f"expected no HTTP requests, got {self.requests}"
