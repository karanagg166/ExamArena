"""Public synthetic transport fixtures verify cookies, redirect refusal and bounds."""

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from PyPDF2 import PdfReader

from app.maintenance.release_http import Session, synthetic_pdf


@pytest.fixture
def server():
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            calls.append(self.path)
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/should-not-follow")
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header("Set-Cookie", "synthetic=session; HttpOnly; Path=/")
                self.end_headers()
                self.wfile.write(b"{}")

        def do_GET(self):
            calls.append(self.path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"x" * 262145
                if self.path == "/oversize"
                else json.dumps({"cookie": self.headers.get("Cookie")}).encode()
            )

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield Session("http://127.0.0.1:" + str(http.server_port)), calls
    finally:
        http.shutdown()
        thread.join(timeout=2)
        http.server_close()


def test_redirect_is_not_followed(server):
    session, calls = server
    assert (
        session.request("POST", "/redirect", value={"password": "public synthetic"})[0]
        == 302
    )
    assert calls == ["/redirect"]


def test_session_preserves_login_cookie(server):
    session, _ = server
    assert session.request("POST", "/login", value={})[0] == 200
    assert session.request("GET", "/protected") == (
        200,
        {"cookie": "synthetic=session"},
    )


def test_response_size_is_bounded(server):
    session, _ = server
    with pytest.raises(ValueError, match="exceeded"):
        session.request("GET", "/oversize")


def test_generated_pdf_has_visible_marker_and_supported_fact():
    statement = "EA_MARKER_public_fixture: The synthetic atlas color is violet."
    reader = PdfReader(io.BytesIO(synthetic_pdf(statement)))
    assert len(reader.pages) == 1
    assert statement in reader.pages[0].extract_text()


@pytest.mark.parametrize("timeout", [0, -1, 66, True, "65", float("inf"), float("nan")])
def test_release_http_rejects_unbounded_or_invalid_deadlines(timeout):
    with pytest.raises(ValueError):
        Session("https://synthetic.example.com").request(
            "GET", "/health", timeout=timeout
        )


def test_release_http_uses_explicit_answer_deadline_and_preserves_other_defaults(
    monkeypatch,
):
    import io

    calls = []

    class Response(io.BytesIO):
        status = 200

    session = Session("https://synthetic.example.com")

    def opening(request, timeout):
        calls.append(timeout)
        return Response(b"{}")

    monkeypatch.setattr(session.opener, "open", opening)
    session.request("POST", "/api/v1/course-materials/answer", value={}, timeout=65)
    session.request("POST", "/other", value={})
    session.request("GET", "/health")
    assert calls == [65, 45, 15]
