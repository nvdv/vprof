"""Program stats server."""
import functools
import io
import json
import os
import sys
import webbrowser

from six.moves import socketserver
from six.moves import SimpleHTTPServer as http_server

_STATIC_DIR = 'frontend'
_PROFILE_HTML = '%s/profile.html' % _STATIC_DIR


class StatsServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Declares multithreaded HTTP server."""
    allow_reuse_address = True


class StatsHandler(http_server.SimpleHTTPRequestHandler):
    """Program stats request handler."""

    def __init__(self, profile_json, *args, **kwargs):
        self._profile_json = profile_json
        self.uri_map = {
            '/': self.handle_root,
            '/profile': self.handle_profile,
        }
        # Since this class is old-style - call parent method directly.
        http_server.SimpleHTTPRequestHandler.__init__(
            self, *args, **kwargs)

    def handle_root(self):
        """Handles index.html requests."""
        res_filename = os.path.join(
            os.path.dirname(__file__), _PROFILE_HTML)
        with io.open(res_filename, 'rb') as res_file:
            content = res_file.read()
        return content, 'text/html'

    def handle_profile(self):
        """Handles profile stats requests."""
        return json.dumps(self._profile_json), 'text/json'

    def handle_other(self):
        """Handles static files requests."""
        res_basename = os.path.basename(self.path)
        # TODO(nvdv): Replace this workaround with real favicon.
        if res_basename == 'favicon.ico':
            return '', ''
        res_filename = os.path.join(
            os.path.dirname(__file__), _STATIC_DIR,
            res_basename)
        with io.open(res_filename, 'rb') as res_file:
            content = res_file.read()
        _, extension = os.path.splitext(self.path)
        return content, 'text/%s' % extension

    def do_GET(self):
        """Handles HTTP GET requests."""
        handler = self.uri_map.get(self.path) or self.handle_other
        content, content_type = handler()
        self._send_response(
            200, headers=(('Content-type', '%s; charset=utf-8' % content_type),
                          ('Content-Length', len(content))))
        # Convert to bytes for Python 3.
        if (sys.version_info[0] >= 3) and isinstance(content, str):
            self.wfile.write(bytes(content, 'utf-8'))
        else:
            self.wfile.write(content)

    def do_POST(self):
        """Handles HTTP POST requests."""
        post_data = self.rfile.read(int(self.headers['Content-Length']))
        self._profile_json.update(json.loads(post_data.decode('utf-8')))
        self._send_response(
            200, headers=(('Content-type', '%s; charset=utf-8' % 'text/json'),
                          ('Content-Length', len(post_data))))

    def _send_response(self, http_code, message=None, headers=None):
        """Sends HTTP response code, message and headers."""
        self.send_response(http_code, message)
        if headers:
            for header in headers:
                self.send_header(*header)
            self.end_headers()


def start(host, port, profile_stats, dont_start_browser):
    """Starts HTTP server with specified parameters.

    Args:
        host: Server hostname.
        port: Server port.
        profile_stats: Dict with collected progran stats.
        dont_start_browser: Whether to start browser after profiling.
    """
    stats_handler = functools.partial(StatsHandler, profile_stats)
    if not dont_start_browser:
        webbrowser.open('http://{}:{}/'.format(host, port))
    try:
        StatsServer((host, port), stats_handler).serve_forever()
    except KeyboardInterrupt:
        print('Stopping...')
        sys.exit(0)
