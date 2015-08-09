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

_MODULE_DESC = 'Python visual profiler.'
_STATIC_DIR = 'frontend'
_PROFILE_HTML = '%s/profile.html' % _STATIC_DIR
_HOST = 'localhost'
_PORT = 8000


def _annotate_stats(stats):
    """Adds description to cProfile stats."""
    result_stats = {}
    for func_params, stats in stats.items():
        cum_calls, num_calls, time_per_call, cum_time, callers = stats
        result_stats[func_params] = {
            'cum_calls': cum_calls,
            'num_calls': num_calls,
            'time_per_call': time_per_call,
            'cum_time': cum_time,
            'callers': callers,
        }
    return result_stats


# TODO(nvdv): Make this function iterative.
def _fill_stats(curr_node, all_callees, stats):
    """Recursively populates stats in call order."""
    module_name, lineno, func_name = curr_node
    return {
        'module_name': module_name,
        'lineno': lineno,
        'func_name': func_name,
        'cum_calls': stats[curr_node]['cum_calls'],
        'num_calls': stats[curr_node]['num_calls'],
        'time_per_call': stats[curr_node]['time_per_call'],
        'cum_time': stats[curr_node]['cum_time'],
        'children': [_fill_stats(child, all_callees, stats)
                     for child in all_callees[curr_node]
                     if child != curr_node]
    }


def transform_stats(stats):
    """Converts start from cProfile format to recusive dict."""

    def _statcmp(stat):
        _, params = stat
        return params['cum_time']

    stats.calc_callees()
    changed_stats = _annotate_stats(stats.stats)
    root = max(changed_stats.items(), key=_statcmp)
    return _fill_stats(root[0], stats.all_callees, changed_stats)


def get_stats(filename):
    """Returns profile statistics for Python program specified by filename."""
    prof = cProfile.Profile()
    try:
        with open(filename) as srcfile:
            prof.run(srcfile.read())
    except SystemExit:
        pass
    prof.create_stats()
    return pstats.Stats(prof)


class StatsServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True


class StatsHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """Serves profiles stats."""
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
            res_filename = os.path.dirname(__file__) + '/' + _STATIC_DIR + self.path
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

    print('Collecting profile stats...')
    stats = get_stats(args.source[0])
    program_info = {
        'program_name': args.source[0],
        'run_time': stats.total_tt,
        'primitive_calls': stats.prim_calls,
        'total_calls': stats.total_calls,
        'call_stats': transform_stats(stats),
    }

    print('Serving results...')
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
