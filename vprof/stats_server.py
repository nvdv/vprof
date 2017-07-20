"""Profiler server."""
import functools
import gzip
import io
import json
import os
import sys
import webbrowser

from six import BytesIO
from six.moves import SimpleHTTPServer as http_server
from six.moves import socketserver

_STATIC_DIR = 'ui'
_PROFILE_HTML = '%s/profile.html' % _STATIC_DIR


def compress_data(data):
    """Compresses data with gzip.

    Longer version is needed since gzip.compress is supported
    in Python 3 only.
    """
    out_fileobj = BytesIO()
    with gzip.GzipFile(fileobj=out_fileobj, mode="w") as f:
        if sys.version_info[0] >= 3 and isinstance(data, str):
            f.write(bytes(data, 'utf-8'))
        else:
            f.write(data)
    return out_fileobj.getvalue()


def decompress_data(data):
    """Decompresses gzipped data."""
    compressed_file = BytesIO(data)
    with gzip.GzipFile(fileobj=compressed_file, mode="r") as f:
        out_data = f.read()
    return out_data


class StatsServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Declares multithreaded HTTP server."""
    allow_reuse_address = True


class StatsHandler(http_server.SimpleHTTPRequestHandler):
    """Program stats request handler."""

    def __init__(self, profile_json, *args, **kwargs):
        self._profile_json = profile_json
        self.uri_map = {
            '/': self._handle_root,
            '/profile': self._handle_profile,
        }
        # Since this class is old-style - call parent method directly.
        http_server.SimpleHTTPRequestHandler.__init__(
            self, *args, **kwargs)

    @staticmethod
    def _handle_root():
        """Handles index.html requests."""
        res_filename = os.path.join(
            os.path.dirname(__file__), _PROFILE_HTML)
        with io.open(res_filename, 'rb') as res_file:
            content = res_file.read()
        return content, 'text/html'

    def _handle_profile(self):
        """Handles profile stats requests."""
        return json.dumps(self._profile_json), 'text/json'

    def _handle_other(self):
        """Handles static files requests."""
        res_filename = os.path.join(
            os.path.dirname(__file__), _STATIC_DIR, self.path[1:])
        with io.open(res_filename, 'rb') as res_file:
            content = res_file.read()
        _, extension = os.path.splitext(self.path)
        return content, 'text/%s' % extension[1:]  # Skip dot in the extension.

    def do_GET(self):
        """Handles HTTP GET requests."""
        handler = self.uri_map.get(self.path) or self._handle_other
        content, content_type = handler()
        compressed_content = compress_data(content)
        self._send_response(
            200, headers=(('Content-type', '%s; charset=utf-8' % content_type),
                          ('Content-Encoding', 'gzip'),
                          ('Content-Length', len(compressed_content))))
        self.wfile.write(compressed_content)

    def do_POST(self):
        """Handles HTTP POST requests."""
        post_data = self.rfile.read(int(self.headers['Content-Length']))
        json_data = decompress_data(post_data)
        self._profile_json.update(json.loads(json_data.decode('utf-8')))
        self._send_response(
            200, headers=(('Content-type', '%s; charset=utf-8' % 'text/json'),
                          ('Content-Encoding', 'gzip'),
                          ('Content-Length', len(post_data))))

    def _send_response(self, http_code, message=None, headers=None):
        """Sends HTTP response code, message and headers."""
        self.send_response(http_code, message)
        if headers:
            for header in headers:
                self.send_header(*header)
            self.end_headers()


def start(host, port, profiler_stats, dont_start_browser, debug_mode):
    """Starts HTTP server with specified parameters.

    Args:
        host: Server host name.
        port: Server port.
        profiler_stats: A dict with collected program stats.
        dont_start_browser: Whether to open browser after profiling.
        debug_mode: Whether to redirect stderr to /dev/null.
    """
    stats_handler = functools.partial(StatsHandler, profiler_stats)
    if not debug_mode:
        sys.stderr = open(os.devnull, 'w')
    print('Starting HTTP server...')
    if not dont_start_browser:
        webbrowser.open('http://{}:{}/'.format(host, port))
    try:
        StatsServer((host, port), stats_handler).serve_forever()
    except KeyboardInterrupt:
        print('Stopping...')
        sys.exit(0)
