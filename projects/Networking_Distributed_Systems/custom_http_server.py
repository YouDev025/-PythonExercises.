"""
custom_http_server.py
A modular, OOP-based HTTP server implementation using Python sockets.
Supports GET/POST, static file serving, dynamic routing, and threading.
"""

import socket
import threading
import os
import json
import mimetypes
import logging
import argparse
from datetime import datetime
from typing import Callable, Dict, Optional, Tuple

# ─── Logging Setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── HTTP Status Codes ────────────────────────────────────────────────────────

HTTP_STATUS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}

# ─── HTTPRequest ──────────────────────────────────────────────────────────────

class HTTPRequest:
    """Parses and encapsulates a raw HTTP request."""

    def __init__(self, raw: bytes):
        self.method: str = ""
        self.path: str = "/"
        self.http_version: str = "HTTP/1.1"
        self.headers: Dict[str, str] = {}
        self.body: bytes = b""
        self.query_params: Dict[str, str] = {}
        self._parse(raw)

    def _parse(self, raw: bytes) -> None:
        try:
            header_section, _, body = raw.partition(b"\r\n\r\n")
            self.body = body
            lines = header_section.decode("utf-8", errors="replace").split("\r\n")

            # Request line
            request_line = lines[0].split(" ")
            if len(request_line) < 2:
                raise ValueError(f"Malformed request line: {lines[0]!r}")

            self.method = request_line[0].upper()
            raw_path = request_line[1]
            self.http_version = request_line[2] if len(request_line) > 2 else "HTTP/1.1"

            # Split path and query string
            if "?" in raw_path:
                self.path, query_string = raw_path.split("?", 1)
                self.query_params = self._parse_query(query_string)
            else:
                self.path = raw_path

            # Headers
            for line in lines[1:]:
                if ": " in line:
                    key, _, value = line.partition(": ")
                    self.headers[key.strip().lower()] = value.strip()

        except Exception as exc:
            logger.warning("Request parse error: %s", exc)

    @staticmethod
    def _parse_query(query_string: str) -> Dict[str, str]:
        params: Dict[str, str] = {}
        for pair in query_string.split("&"):
            if "=" in pair:
                k, _, v = pair.partition("=")
                params[k] = v
        return params

    def json(self) -> Optional[dict]:
        """Attempt to decode the body as JSON."""
        try:
            return json.loads(self.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def __repr__(self) -> str:
        return f"<HTTPRequest {self.method} {self.path}>"


# ─── HTTPResponse ─────────────────────────────────────────────────────────────

class HTTPResponse:
    """Builds and serialises an HTTP response."""

    def __init__(
        self,
        status_code: int = 200,
        body: bytes = b"",
        headers: Optional[Dict[str, str]] = None,
    ):
        self.status_code = status_code
        self.body: bytes = body if isinstance(body, bytes) else body.encode("utf-8")
        self.headers: Dict[str, str] = headers or {}
        self._set_defaults()

    def _set_defaults(self) -> None:
        self.headers.setdefault("Content-Type", "text/plain; charset=utf-8")
        self.headers["Content-Length"] = str(len(self.body))
        self.headers.setdefault("Connection", "close")
        self.headers["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        self.headers["Server"] = "CustomHTTPServer/1.0"

    # ── Convenience constructors ──────────────────────────────────────────────

    @classmethod
    def text(cls, content: str, status_code: int = 200) -> "HTTPResponse":
        return cls(
            status_code,
            content.encode("utf-8"),
            {"Content-Type": "text/plain; charset=utf-8"},
        )

    @classmethod
    def html(cls, content: str, status_code: int = 200) -> "HTTPResponse":
        return cls(
            status_code,
            content.encode("utf-8"),
            {"Content-Type": "text/html; charset=utf-8"},
        )

    @classmethod
    def json_response(cls, data: object, status_code: int = 200) -> "HTTPResponse":
        payload = json.dumps(data, indent=2).encode("utf-8")
        return cls(status_code, payload, {"Content-Type": "application/json"})

    @classmethod
    def not_found(cls, path: str = "") -> "HTTPResponse":
        body = f"<h1>404 Not Found</h1><p>The path <code>{path}</code> was not found.</p>"
        return cls.html(body, 404)

    @classmethod
    def method_not_allowed(cls, allowed: Tuple[str, ...]) -> "HTTPResponse":
        body = f"<h1>405 Method Not Allowed</h1><p>Allowed: {', '.join(allowed)}</p>"
        resp = cls.html(body, 405)
        resp.headers["Allow"] = ", ".join(allowed)
        return resp

    @classmethod
    def internal_error(cls, detail: str = "") -> "HTTPResponse":
        body = f"<h1>500 Internal Server Error</h1><p>{detail}</p>"
        return cls.html(body, 500)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def format(self) -> bytes:
        """Serialise the response to raw bytes."""
        reason = HTTP_STATUS.get(self.status_code, "Unknown")
        status_line = f"HTTP/1.1 {self.status_code} {reason}\r\n"
        header_lines = "".join(f"{k}: {v}\r\n" for k, v in self.headers.items())
        return (status_line + header_lines + "\r\n").encode("utf-8") + self.body

    def __repr__(self) -> str:
        return f"<HTTPResponse {self.status_code}>"


# ─── Router ───────────────────────────────────────────────────────────────────

class Router:
    """Maps (method, path) pairs to handler callables."""

    def __init__(self):
        # { path: { method: handler } }
        self._routes: Dict[str, Dict[str, Callable]] = {}

    def add_route(
        self,
        path: str,
        handler: Callable[[HTTPRequest], HTTPResponse],
        methods: Tuple[str, ...] = ("GET",),
    ) -> None:
        if not path.startswith("/"):
            raise ValueError(f"Route path must start with '/': {path!r}")
        entry = self._routes.setdefault(path, {})
        for method in methods:
            entry[method.upper()] = handler

    def route(
        self, path: str, methods: Tuple[str, ...] = ("GET",)
    ) -> Callable:
        """Decorator for registering routes."""
        def decorator(fn: Callable) -> Callable:
            self.add_route(path, fn, methods)
            return fn
        return decorator

    def resolve(
        self, request: HTTPRequest
    ) -> Tuple[Optional[Callable], Optional[HTTPResponse]]:
        """
        Returns (handler, None) on success,
        (None, error_response) when the route or method is not found.
        """
        if request.path not in self._routes:
            return None, HTTPResponse.not_found(request.path)
        method_map = self._routes[request.path]
        handler = method_map.get(request.method)
        if handler is None:
            return None, HTTPResponse.method_not_allowed(tuple(method_map.keys()))
        return handler, None


# ─── Static File Handler ──────────────────────────────────────────────────────

class StaticFileHandler:
    """Serves files from a directory tree."""

    def __init__(self, root: str):
        self.root = os.path.realpath(root)

    def serve(self, request: HTTPRequest) -> HTTPResponse:
        # Strip leading slash and join safely
        relative = request.path.lstrip("/") or "index.html"
        abs_path = os.path.realpath(os.path.join(self.root, relative))

        # Directory-traversal guard
        if not abs_path.startswith(self.root):
            return HTTPResponse.html("<h1>403 Forbidden</h1>", 403)

        if not os.path.isfile(abs_path):
            return HTTPResponse.not_found(request.path)

        try:
            with open(abs_path, "rb") as fh:
                content = fh.read()
            mime, _ = mimetypes.guess_type(abs_path)
            mime = mime or "application/octet-stream"
            return HTTPResponse(200, content, {"Content-Type": mime})
        except PermissionError:
            return HTTPResponse.html("<h1>403 Forbidden</h1>", 403)
        except OSError as exc:
            return HTTPResponse.internal_error(str(exc))


# ─── HTTPServer ───────────────────────────────────────────────────────────────

class HTTPServer:
    """
    Listens for TCP connections, parses HTTP requests, dispatches to
    Router handlers or a StaticFileHandler, and returns responses.
    """

    BUFFER_SIZE = 65_536  # 64 KB

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        router: Optional[Router] = None,
        static_dir: Optional[str] = None,
        threaded: bool = True,
    ):
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be 1–65535, got {port}")
        self.host = host
        self.port = port
        self.router = router or Router()
        self.static_handler = StaticFileHandler(static_dir) if static_dir else None
        self.threaded = threaded
        self._server_socket: Optional[socket.socket] = None
        self._running = False

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(128)
        self._running = True
        logger.info("Server started → http://%s:%d", self.host, self.port)
        if self.static_handler:
            logger.info("Serving static files from: %s", self.static_handler.root)
        try:
            self._accept_loop()
        except KeyboardInterrupt:
            logger.info("Shutdown requested.")
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        if self._server_socket:
            self._server_socket.close()
        logger.info("Server stopped.")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _accept_loop(self) -> None:
        while self._running:
            try:
                client_sock, addr = self._server_socket.accept()
            except OSError:
                break
            logger.info("Connection from %s:%d", *addr)
            if self.threaded:
                t = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, addr),
                    daemon=True,
                )
                t.start()
            else:
                self._handle_client(client_sock, addr)

    def _handle_client(
        self, client_sock: socket.socket, addr: Tuple[str, int]
    ) -> None:
        try:
            raw = self._recv_all(client_sock)
            if not raw:
                return
            request = HTTPRequest(raw)
            logger.info(
                "%s:%d → %s %s", addr[0], addr[1], request.method, request.path
            )
            response = self._dispatch(request)
            client_sock.sendall(response.format())
            logger.info(
                "%s:%d ← %d %s",
                addr[0],
                addr[1],
                response.status_code,
                HTTP_STATUS.get(response.status_code, ""),
            )
        except Exception as exc:
            logger.error("Error handling %s:%d — %s", addr[0], addr[1], exc)
            try:
                client_sock.sendall(HTTPResponse.internal_error(str(exc)).format())
            except OSError:
                pass
        finally:
            client_sock.close()

    def _recv_all(self, sock: socket.socket) -> bytes:
        """Read data from socket, respecting Content-Length when present."""
        sock.settimeout(5.0)
        chunks: list[bytes] = []
        try:
            while True:
                chunk = sock.recv(self.BUFFER_SIZE)
                if not chunk:
                    break
                chunks.append(chunk)
                data = b"".join(chunks)
                # Check if full headers received
                if b"\r\n\r\n" in data:
                    header_part, _, body_part = data.partition(b"\r\n\r\n")
                    headers_text = header_part.decode("utf-8", errors="replace")
                    content_length = 0
                    for line in headers_text.split("\r\n")[1:]:
                        if line.lower().startswith("content-length:"):
                            content_length = int(line.split(":", 1)[1].strip())
                    if len(body_part) >= content_length:
                        break
        except socket.timeout:
            pass
        return b"".join(chunks)

    def _dispatch(self, request: HTTPRequest) -> HTTPResponse:
        # 1. Dynamic routes take priority
        handler, error_response = self.router.resolve(request)
        if handler:
            try:
                return handler(request)
            except Exception as exc:
                logger.exception("Handler exception: %s", exc)
                return HTTPResponse.internal_error(str(exc))
        # 2. Static files (only if path not found in router)
        if self.static_handler and error_response and error_response.status_code == 404:
            return self.static_handler.serve(request)
        return error_response or HTTPResponse.not_found(request.path)


# ─── Built-in Demo Handlers ───────────────────────────────────────────────────

def make_demo_router() -> Router:
    router = Router()

    @router.route("/")
    def index(req: HTTPRequest) -> HTTPResponse:
        html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>CustomHTTPServer</title>
<style>
  body{font-family:system-ui,sans-serif;max-width:700px;margin:3rem auto;padding:0 1rem}
  code{background:#f4f4f4;padding:2px 6px;border-radius:3px}
  pre{background:#f4f4f4;padding:1rem;border-radius:6px;overflow-x:auto}
  h1{color:#1a1a2e}
</style>
</head>
<body>
<h1>🚀 CustomHTTPServer</h1>
<p>A modular Python HTTP server built with OOP &amp; sockets.</p>
<h2>Available endpoints</h2>
<ul>
  <li><code>GET /</code> — This page</li>
  <li><code>GET /hello?name=World</code> — Dynamic greeting</li>
  <li><code>GET /status</code> — Server status (JSON)</li>
  <li><code>POST /echo</code> — Echo request body as JSON</li>
  <li><code>GET /time</code> — Current UTC time</li>
</ul>
</body>
</html>"""
        return HTTPResponse.html(html)

    @router.route("/hello")
    def hello(req: HTTPRequest) -> HTTPResponse:
        name = req.query_params.get("name", "World")
        return HTTPResponse.html(
            f"<h1>Hello, {name}!</h1><p>Query params: {req.query_params}</p>"
        )

    @router.route("/status")
    def status(req: HTTPRequest) -> HTTPResponse:
        return HTTPResponse.json_response(
            {
                "status": "running",
                "time": datetime.utcnow().isoformat() + "Z",
                "server": "CustomHTTPServer/1.0",
            }
        )

    @router.route("/echo", methods=("POST",))
    def echo(req: HTTPRequest) -> HTTPResponse:
        payload = {
            "method": req.method,
            "path": req.path,
            "headers": req.headers,
            "body": req.body.decode("utf-8", errors="replace"),
            "json": req.json(),
        }
        return HTTPResponse.json_response(payload, 200)

    @router.route("/time")
    def time_handler(req: HTTPRequest) -> HTTPResponse:
        return HTTPResponse.json_response(
            {"utc_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
        )

    return router


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Custom OOP HTTP Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=8080, help="Listen port")
    parser.add_argument(
        "--static-dir",
        default=None,
        help="Directory to serve static files from",
    )
    parser.add_argument(
        "--no-threading",
        action="store_true",
        help="Handle requests sequentially (no threads)",
    )
    args = parser.parse_args()

    router = make_demo_router()
    server = HTTPServer(
        host=args.host,
        port=args.port,
        router=router,
        static_dir=args.static_dir,
        threaded=not args.no_threading,
    )
    server.start()


if __name__ == "__main__":
    main()