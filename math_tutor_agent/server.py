from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from math_tutor_agent.agent import MathTutorAgent
from math_tutor_agent.models import ProblemRequest, to_plain_dict
from math_tutor_agent.store import TextbookStore

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CHUNKS = ROOT / "examples" / "textbook_chunks.sample.json"
WEB_INDEX = ROOT / "web" / "index.html"


def create_agent() -> MathTutorAgent:
    store = TextbookStore.from_json(EXAMPLE_CHUNKS) if EXAMPLE_CHUNKS.exists() else TextbookStore()
    return MathTutorAgent(store)


class TutorRequestHandler(BaseHTTPRequestHandler):
    """Dependency-free HTTP handler for local MVP smoke testing.

    FastAPI remains the production-facing app, but this handler lets a fresh checkout
    run immediately with only the Python standard library.
    """

    agent = create_agent()

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib callback name
        self._send_empty(HTTPStatus.NO_CONTENT)

    def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(
                HTTPStatus.OK,
                {"status": "ok", "textbook_chunks": len(self.agent.store.all())},
            )
            return
        if path in ("/", "/index.html") and WEB_INDEX.exists():
            content = WEB_INDEX.read_bytes()
            self._send_bytes(HTTPStatus.OK, content, "text/html; charset=utf-8")
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"detail": "Not Found"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
        path = urlparse(self.path).path
        if path != "/solve":
            self._send_json(HTTPStatus.NOT_FOUND, {"detail": "Not Found"})
            return
        try:
            payload = self._read_json()
            request = ProblemRequest.from_dict(payload)
            response = self.agent.solve(request)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"detail": str(exc)})
            return
        self._send_json(HTTPStatus.OK, to_plain_dict(response))

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_empty(self, status: HTTPStatus) -> None:
        self.send_response(status)
        self._send_common_headers()
        self.end_headers()

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, content, "application/json; charset=utf-8")

    def _send_bytes(self, status: HTTPStatus, content: bytes, content_type: str) -> None:
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), TutorRequestHandler)
    print(f"고1 수학 튜터 MVP server running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the dependency-free math tutor MVP server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
