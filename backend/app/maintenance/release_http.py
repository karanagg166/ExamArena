"""Bounded HTTP and generated public PDFs for the authenticated release gate."""

import http.cookiejar
import json
import time
import urllib.error
import urllib.request
import uuid

ROOT = "/api/v1/course-materials"


def require(condition, label):
    if not condition:
        raise AssertionError(label)


APP_URL = "https://exam-arena-mu.vercel.app"
SEARCH_URL = "https://search-sphere-api.onrender.com"


def wait_for_service(session, path, expected_sha, *, ready=False, sleep=time.sleep):
    """Four read-only attempts; no mutation or model request is replayed."""
    for attempt in range(4):
        try:
            code, value = session.request("GET", path)
        except OSError:  # Includes network/SSL timeouts and urllib URLError.
            code, value = 0, None
        if code == 200:
            require(isinstance(value, dict), "Malformed service health response")
            require(
                value.get("git_commit") == expected_sha, "Serving revision mismatch"
            )
            require(
                value.get("status") == ("ready" if ready else "ok"),
                "Service health not ready",
            )
            if ready:
                require(
                    value.get("database") == "connected", "Service database not ready"
                )
            return
        require(code in (0, 502, 503, 504), "Unexpected service health status")
        if attempt < 3:
            print("WAIT bounded service health recovery", flush=True)
            sleep(2)
    raise AssertionError("Service did not recover within four health attempts")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Session:
    def __init__(self, base=APP_URL):
        self.base = base
        self.opener = urllib.request.build_opener(
            NoRedirect(), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

    def request(
        self,
        method,
        path,
        *,
        value=None,
        fields=None,
        pdf=None,
        filename=None,
        timeout=None,
    ):
        deadline = timeout if timeout is not None else (45 if method == "POST" else 15)
        if (
            not isinstance(deadline, (int, float))
            or isinstance(deadline, bool)
            or not 0 < deadline <= 65
        ):
            raise ValueError("Invalid bounded release HTTP timeout.")
        headers = {
            "Accept": "application/json",
            "User-Agent": "ExamArenaSyntheticRelease/1",
        }
        body = None
        if value is not None:
            body = json.dumps(value).encode()
            headers["Content-Type"] = "application/json"
        if fields is not None:
            boundary = "EARelease" + uuid.uuid4().hex
            parts = []
            for name, item in fields.items():
                parts.append(
                    f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{item}\r\n'.encode()
                )
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: application/pdf\r\n\r\n'.encode()
            )
            body = b"".join(parts) + pdf + f"\r\n--{boundary}--\r\n".encode()
            headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
        request = urllib.request.Request(
            self.base + path, method=method, data=body, headers=headers
        )
        try:
            response = self.opener.open(request, timeout=deadline)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            payload = response.read(262145)
            if len(payload) > 262144:
                raise ValueError("Release response exceeded its bound.")
            try:
                value = json.loads(payload)
            except (UnicodeDecodeError, json.JSONDecodeError):
                value = None
            return response.status, value


def synthetic_pdf(statement):
    escaped = statement.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    # Wrap at sentence boundaries to keep the visible marker and supporting fact on-page.
    lines = ["Public synthetic release fixture. No real person or school.", escaped]
    stream = (
        "BT /F1 10 Tf 32 740 Td "
        + " 0 -22 Td ".join("(" + line + ") Tj" for line in lines)
        + " ET"
    )
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 900 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream.encode())} >>\nstream\n{stream}\nendstream",
    ]
    data, offsets = "%PDF-1.4\n", []
    for index, content in enumerate(objects, 1):
        offsets.append(len(data.encode()))
        data += f"{index} 0 obj\n{content}\nendobj\n"
    xref = len(data.encode())
    data += "xref\n0 6\n0000000000 65535 f \n" + "".join(
        f"{offset:010} 00000 n \n" for offset in offsets
    )
    return (
        data + f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    ).encode()
