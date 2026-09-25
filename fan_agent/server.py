"""Small loopback-only application server; no shell or solver launch endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .study import StudyService, AIError
from .domain import RECIPE
from .geometry import MAX_BYTES
from .reference import reference
from .store import Store
from .analytics import METRIC_DEFINITION

STATIC = Path(__file__).resolve().parent.parent / "web"


def make_server(port=8765, data_root=None):
    store = Store(data_root or Path(__file__).resolve().parent.parent / "data")

    study = StudyService()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, content, kind="application/json; charset=utf-8"):
            if isinstance(content, (dict, list)):
                content = json.dumps(content, allow_nan=False).encode()
            elif isinstance(content, str):
                content = content.encode()
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)

        def local_request(self):
            actual_port = self.server.server_address[1]
            hosts = {f"127.0.0.1:{actual_port}", f"localhost:{actual_port}"}
            if self.headers.get("Host") not in hosts:
                self.send(403, {"error": "Local host required."})
                return False
            origin = self.headers.get("Origin")
            if origin and origin not in {"http://" + h for h in hosts}:
                self.send(403, {"error": "Same-origin request required."})
                return False
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                self.send(403, {"error": "Cross-site request rejected."})
                return False
            return True

        def do_GET(self):
            if not self.local_request():
                return
            path = urlsplit(self.path).path
            try:
                if path == "/api/ai/status":
                    return self.send(200, study.status())
                if path == "/api/reference":
                    return self.send(200, reference())
                if path == "/api/solver-development":
                    report = STATIC.parent / "docs" / "solver-assessment.json"
                    if not report.exists():
                        return self.send(404, {"error": "No development assessment available."})
                    return self.send(200, json.loads(report.read_text()))
                if path == "/api/cases":
                    return self.send(200, store.list_cases())
                if path.startswith("/api/cases/"):
                    return self.send(200, store.read("cases", path.rsplit("/", 1)[-1]))
                if path == "/api/status":
                    return self.send(200, {"version": "0.1.0", "recipe": RECIPE, "solver_execution": "not_implemented", "storage": "local"})
                if path == "/api/metrics":
                    return self.send(200, METRIC_DEFINITION)
                static = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}
                if path in static:
                    filename, kind = static[path]
                    return self.send(200, (STATIC / filename).read_bytes(), kind + "; charset=utf-8")
                self.send(404, {"error": "Not found."})
            except ValueError as exc:
                self.send(404, {"error": str(exc)})

        def do_POST(self):
            if not self.local_request():
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                route = urlsplit(self.path)
                maximum = MAX_BYTES if route.path == "/api/geometry" else 16384
                if not 0 < length <= maximum:
                    return self.send(413, {"error": "Request is empty or exceeds the upload limit."})
                self.connection.settimeout(30)
                data = self.rfile.read(length)
                if len(data) != length:
                    raise ValueError("Incomplete request body.")
                if route.path == "/api/studies/propose":
                    if self.headers.get_content_type() != "application/json":
                        return self.send(415, {"error": "JSON input required."})
                    return self.send(200, study.propose(json.loads(data)))
                if route.path == "/api/geometry":
                    units = parse_qs(route.query).get("units", [""])[0]
                    source_format = parse_qs(route.query).get("format", ["stl"])[0]
                    return self.send(201, store.upload(data, units, source_format))
                if route.path == "/api/cases":
                    if self.headers.get_content_type() != "application/json":
                        return self.send(415, {"error": "JSON input required."})
                    return self.send(201, store.create(json.loads(data)))
                self.send(404, {"error": "No such action. Solver execution is not enabled."})
            except AIError as exc:
                self.send(503, {"error": str(exc)})
            except (ValueError, UnicodeDecodeError) as exc:
                self.send(400, {"error": str(exc)})
            except OSError:
                self.send(500, {"error": "Unable to complete local storage operation."})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
