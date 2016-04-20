"""Main module for visual profiler."""
import argparse
import os
import sys

from vprof import base_profile
from vprof import stats_server
from vprof import vprof_runtime

_PROGRAN_NAME = 'vprof'
_MODULE_DESC = 'Python visual profiler'
_HOST = 'localhost'
_MODES_DESC = (
    """modes configuration
available modes:
  c - runtime flame chart
  m - memory graph
  h - code heatmap""")
_ERROR_MSG = {
    'ambiguous configuration': {
        'msg': 'Profiler configuration is ambiguous. Remove duplicates.',
        'code': 1
    },
    'bad option': {
        'code': 2
    },
    'runtime error': {
        'code': 3
    },
}


def main():
    """Visual profiler main function."""
    parser = argparse.ArgumentParser(
        prog=_PROGRAN_NAME, description=_MODULE_DESC,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('profilers', metavar='options', help=_MODES_DESC)
    parser.add_argument('source', metavar='src', nargs=1,
                        help='Python module to profile')
    parser.add_argument('--port', dest='port', default=8000, type=int,
                        help='set internal webserver port')
    parser.add_argument('--debug', dest='debug_mode',
                        action='store_true', default=False,
                        help="don't suppress error messages")
    parser.add_argument('-n', '--no-browser', dest='dont_start_browser',
                        action='store_true', default=False,
                        help="don't start browser after profiling")
    args = parser.parse_args()

    try:
        program_stats = vprof_runtime.run_profilers(
            args.source[0], args.profilers, verbose=True)
    except vprof_runtime.AmbiguousConfigurationError:
        print(_ERROR_MSG['ambiguous configuration']['msg'])
        sys.exit(_ERROR_MSG['ambiguous configuration']['code'])
    except vprof_runtime.BadOptionError as exc:
        print(exc)
        sys.exit(_ERROR_MSG['bad option']['code'])
    except base_profile.ProfilerRuntimeException as exc:
        print(exc)
        sys.exit(_ERROR_MSG['runtime error']['code'])

    if not args.debug_mode:
        sys.stderr = open(os.devnull, "w")
    print('Starting HTTP server...')
    stats_server.start(
        _HOST, args.port, program_stats, args.dont_start_browser)

if __name__ == "__main__":
    main()
