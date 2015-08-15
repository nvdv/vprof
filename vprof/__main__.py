"""Visual profiler for Python."""
import argparse
import cProfile
import functools
import json
import os
import pstats
import SimpleHTTPServer
import SocketServer
import subprocess
import sys
from collections import defaultdict

_MODULE_DESC = 'Python visual profiler.'
_STATIC_DIR = 'frontend'
_PROFILE_HTML = '%s/profile.html' % _STATIC_DIR
_HOST = 'localhost'
_PORT = 8000


def _build_callees(stats):
    """Extracts call tree from cProfile stats."""
    callees = defaultdict(list)
    for func, (_, _, _, _, callers) in stats.iteritems():
        for caller in callers:
            callees[caller].append(func)
    return callees


def _build_call_tree(node, callees, stats, seen=set()):
    """Builds call tree from callees tree and cProfile stats.

    Args:
        node: Call to build tree from.
        callees: Calless tree with call dependencies.
        stats: Profile stats.
        seen: Set to track previously seen nodes to handle recursion.
    Returns:
        A dict representing call tree with all necessary parameters.
    """
    seen.add(node)
    module_name, lineno, func_name = node
    cum_calls, num_calls, time_per_call, cum_time, _ = stats[node]
    return {
        'module_name': module_name,
        'lineno': lineno,
        'func_name': func_name,
        'prim_calls': cum_calls,
        'total_calls': num_calls,
        'time_per_call': time_per_call,
        'cum_time': cum_time,
        'children': [_build_call_tree(child, callees, stats, seen)
                     for child in callees[node] if child not in seen]
    }


def transform_stats(stats):
    """Converts stats from cProfile format to call tree format."""

    def _statcmp(stat):
        """Comparator by cummulative time."""
        _, params = stat
        return params[3]

    stats.calc_callees()
    callees = _build_callees(stats.stats)
    root, _ = max(stats.stats.iteritems(), key=_statcmp)
    return _build_call_tree(root, callees, stats.stats)


def get_stats(filename):
    """Returns profile statistics for Python program specified by filename."""
    globs = {
        '__file__': filename,
        '__name__': '__main__',
        '__package__': None,
    }
    sys.path.insert(0, os.path.dirname(filename))
    prof = cProfile.Profile()
    try:
        with open(filename, 'rb') as srcfile:
            code = compile(srcfile.read(), filename, 'exec')
        prof.runctx(code, globs, None)
    except SystemExit:
        pass
    prof.create_stats()
    return pstats.Stats(prof)


class StatsServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True


class StatsHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """Profile stats server."""
    ROOT_URI = '/'
    PROFILE_URI = '/profile'

    def __init__(self, *args, **kwargs):
        self._profile_json = kwargs['profile_json']
        del kwargs['profile_json']
        # Since this class is old-style - call parent method directly.
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(
            self, *args, **kwargs)

    def do_GET(self):
        """Handles HTTP GET request."""
        if self.path == self.ROOT_URI:
            res_filename = os.path.dirname(__file__) + '/' + _PROFILE_HTML
            with open(res_filename) as res_file:
                output = res_file.read()
            content_type = 'text/html'
        elif self.path == self.PROFILE_URI:
            output = self._profile_json
            content_type = 'text/json'
        else:
            res_filename = (
                os.path.dirname(__file__) + '/' + _STATIC_DIR + self.path)
            with open(res_filename) as res_file:
                output = res_file.read()
            _, extension = os.path.splitext(self.path)
            content_type = 'text/%s' % extension

        self._send_response(
            200, headers=(('Content-type', '%s; charset=utf-8' % content_type),
                          ('Content-Length', len(output))))
        self.wfile.write(output)

    def _send_response(self, http_code, message=None, headers=None):
        """Sends HTTP response code, message and headers."""
        self.send_response(http_code, message)
        if headers:
            for header in headers:
                self.send_header(*header)
            self.end_headers()


def main():
    parser = argparse.ArgumentParser(description=_MODULE_DESC)
    parser.add_argument('source', metavar='src', nargs=1,
                        help='Python program to profile.')
    args = parser.parse_args()
    sys.argv[:] = args.source

    print('Collecting profile stats...')
    stats = get_stats(args.source[0])
    program_info = {
        'program_name': args.source[0],
        'run_time': stats.total_tt,
        'primitive_calls': stats.prim_calls,
        'total_calls': stats.total_calls,
        'call_stats': transform_stats(stats),
    }

    partial_handler = functools.partial(
        StatsHandler, profile_json=json.dumps(program_info))
    subprocess.call(['open', 'http://%s:%s' % (_HOST, _PORT)])
    try:
        StatsServer((_HOST, _PORT), partial_handler).serve_forever()
    except KeyboardInterrupt:
        print('Stopping...')
        sys.exit(0)


if __name__ == "__main__":
    main()
