"""Profiler server."""
from collections.abc import Callable, Sequence
import functools
import gzip
from http import server
import json
import mimetypes
import os
import socketserver
import sys
from typing import Any
import urllib.parse
import webbrowser

_STATIC_DIR = 'ui'
_PROFILE_HTML = f'{_STATIC_DIR}/profile.html'


class StatsServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Declares multithreaded HTTP server."""
    allow_reuse_address = True

    @property
    def server_port(self) -> int:
        """Returns bound server port."""
        return int(self.server_address[1])


class StatsHandler(server.SimpleHTTPRequestHandler):
    """Program stats request handler."""

    def __init__(
            self,
            profile_json: dict[str, Any],
            *args: Any,
            debug_mode: bool = True,
            **kwargs: Any
    ) -> None:
        self._profile_json = profile_json
        self._debug_mode = debug_mode
        self.uri_map: dict[str, Callable[[], tuple[bytes, str]]] = {
            '/': self._handle_root,
            '/profile': self._handle_profile,
        }
        super().__init__(*args, **kwargs)

    def log_message(self, *args: Any) -> None:
        """Logs HTTP server messages only when debug_mode is enabled."""
        if self._debug_mode:
            super().log_message(*args)

    @staticmethod
    def _handle_root() -> tuple[bytes, str]:
        """Handles index.html requests."""
        res_filename = os.path.join(
            os.path.dirname(__file__), _PROFILE_HTML)
        with open(res_filename, 'rb') as res_file:
            content = res_file.read()
        return content, 'text/html'

    def _handle_profile(self) -> tuple[bytes, str]:
        """Handles profile stats requests."""
        return json.dumps(self._profile_json).encode(), 'application/json'

    def _handle_other(self) -> tuple[bytes | None, str | None]:
        """Handles static files requests."""
        static_root = os.path.realpath(
            os.path.join(os.path.dirname(__file__), _STATIC_DIR))
        rel_path = urllib.parse.unquote(self.path.split('?', 1)[0]).lstrip('/')
        res_filename = os.path.realpath(os.path.join(static_root, rel_path))
        if (os.path.commonpath([static_root, res_filename]) != static_root or
                not os.path.isfile(res_filename)):
            return None, None
        with open(res_filename, 'rb') as res_file:
            content = res_file.read()
        content_type, _ = mimetypes.guess_type(res_filename)
        return content, content_type or 'application/octet-stream'

    def do_GET(self) -> None:
        """Handles HTTP GET requests."""
        handler = self.uri_map.get(self.path) or self._handle_other
        content, content_type = handler()
        if content is None:
            self.send_error(404, 'File not found')
            return
        compressed_content = gzip.compress(content)
        self._send_response(
            200, headers=(('Content-type', f'{content_type}; charset=utf-8'),
                          ('Content-Encoding', 'gzip'),
                          ('Content-Length', str(len(compressed_content)))))
        self.wfile.write(compressed_content)

    def do_POST(self) -> None:
        """Handles HTTP POST requests."""
        post_data = self.rfile.read(int(self.headers['Content-Length']))
        json_data = gzip.decompress(post_data)
        self._profile_json.update(json.loads(json_data.decode('utf-8')))
        self._send_response(
            200, headers=(('Content-type', 'application/json; charset=utf-8'),
                          ('Content-Encoding', 'gzip'),
                          ('Content-Length', str(len(post_data)))))

    def _send_response(
            self,
            http_code: int,
            message: str | None = None,
            headers: Sequence[tuple[str, str]] | None = None
    ) -> None:
        """Sends HTTP response code, message and headers."""
        self.send_response(http_code, message)
        if headers:
            for header in headers:
                self.send_header(*header)
            self.end_headers()


def start(
        host: str,
        port: int,
        profiler_stats: dict[str, Any],
        dont_start_browser: bool,
        debug_mode: bool
) -> None:
    """Starts HTTP server with specified parameters.

    Args:
        host: Server host name.
        port: Server port.
        profiler_stats: A dict with collected program stats.
        dont_start_browser: Whether to open browser after profiling.
        debug_mode: Whether to log HTTP requests to stderr.
    """
    stats_handler = functools.partial(
        StatsHandler, profiler_stats, debug_mode=debug_mode)
    print('Starting HTTP server...')
    if not dont_start_browser:
        webbrowser.open(f'http://{host}:{port}/')
    try:
        StatsServer((host, port), stats_handler).serve_forever()
    except KeyboardInterrupt:
        print('Stopping...')
        sys.exit(0)
