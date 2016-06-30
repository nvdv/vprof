"""Main module for visual profiler."""
import argparse
import os
import sys

from vprof import stats_server
from vprof import profiler

__version__ = '0.32'

_PROGRAN_NAME = 'vprof'
_MODULE_DESC = 'Python visual profiler'
_HOST, _PORT = 'localhost', 8000
_MODES_DESC = (
    """modes configuration
available modes:
  c - flame graph
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
    'config error': {
        'msg': 'Remote and config options cannot be used together.',
        'code': 4
    },
    'no config': {
        'msg': 'Please, specify profiler configuration.',
        'code': 5
    }
}


def main():
    """Visual profiler main function."""
    parser = argparse.ArgumentParser(
        prog=_PROGRAN_NAME, description=_MODULE_DESC,
        formatter_class=argparse.RawTextHelpFormatter)
    exclusive_group = parser.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument('-r', '--remote', dest='remote',
                                 action='store_true', default=False,
                                 help='launch in remote mode')
    exclusive_group.add_argument('-s', '--source', metavar='src', nargs=1,
                                 help='Python module or package to profile')
    parser.add_argument('-c', '--config', metavar='options',
                        help=_MODES_DESC)
    parser.add_argument('-H', '--host', dest='host', default=_HOST, type=str,
                        help='set internal webserver host')
    parser.add_argument('-p', '--port', dest='port', default=_PORT, type=int,
                        help='set internal webserver port')
    parser.add_argument('-n', '--no-browser', dest='dont_start_browser',
                        action='store_true', default=False,
                        help="don't start browser automatically")
    parser.add_argument('--debug', dest='debug_mode',
                        action='store_true', default=False,
                        help="don't suppress error messages")
    parser.add_argument('--version', action='version',
                        version='vprof %s' % __version__)
    args = parser.parse_args()

    if args.config and args.remote:
        print(_ERROR_MSG['config error']['msg'])
        sys.exit(_ERROR_MSG['config error']['code'])

    if not args.config and not args.remote:
        print(_ERROR_MSG['no config']['msg'])
        sys.exit(_ERROR_MSG['no config']['code'])

    program_stats = {}
    if not args.remote:
        try:
            program_stats = profiler.run_profilers(  # pylint: disable=redefined-variable-type
                args.source[0], args.config, verbose=True)
        except profiler.AmbiguousConfigurationError:
            print(_ERROR_MSG['ambiguous configuration']['msg'])
            sys.exit(_ERROR_MSG['ambiguous configuration']['code'])
        except profiler.BadOptionError as exc:
            print(exc)
            sys.exit(_ERROR_MSG['bad option']['code'])

    if not args.debug_mode:
        sys.stderr = open(os.devnull, "w")
    print('Starting HTTP server...')
    stats_server.start(
        args.host, args.port, program_stats, args.dont_start_browser)

if __name__ == "__main__":
    main()
