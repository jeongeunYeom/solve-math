import json
from http import HTTPStatus
from io import BytesIO
from types import SimpleNamespace

from math_tutor_agent.server import TutorRequestHandler


class DummyHandler(TutorRequestHandler):
    def __init__(self, body: bytes = b"", path: str = "/solve") -> None:
        self.path = path
        self.headers = {"Content-Length": str(len(body))}
        self.rfile = BytesIO(body)
        self.wfile = BytesIO()
        self.status = None
        self.sent_headers = []

    def send_response(self, code: int, message: str | None = None) -> None:
        self.status = code

    def send_header(self, keyword: str, value: str) -> None:
        self.sent_headers.append((keyword, value))

    def end_headers(self) -> None:
        return


def test_dependency_free_solve_handler() -> None:
    body = json.dumps({"problem_text": "2x + 4 = 10"}).encode("utf-8")
    handler = DummyHandler(body)

    handler.do_POST()

    payload = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert handler.status == HTTPStatus.OK
    assert payload["status"] == "verified"
    assert payload["answer"] == "x = 3"


def test_dependency_free_health_handler() -> None:
    handler = DummyHandler(path="/health")
    handler.requestline = "GET /health HTTP/1.1"
    handler.request_version = "HTTP/1.1"
    handler.command = "GET"
    handler.server = SimpleNamespace(server_version="test")

    handler.do_GET()

    payload = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert handler.status == HTTPStatus.OK
    assert payload["status"] == "ok"
