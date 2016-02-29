"""Main module for visual profiler."""
import argparse
import os
import sys

from collections import OrderedDict
from vprof import code_heatmap
from vprof import memory_profile
from vprof import runtime_profile
from vprof import stats_server

_PROGRAN_NAME = 'vprof'
_MODULE_DESC = 'Python visual profiler'
_HOST = 'localhost'
_PROFILERS = (
    ('c', runtime_profile.RuntimeProfile),
    ('m', memory_profile.MemoryProfile),
    ('h', code_heatmap.CodeHeatmapProfile),
)


def main():
    """Visual profiler main function."""
    parser = argparse.ArgumentParser(
        prog=_PROGRAN_NAME, description=_MODULE_DESC)
    parser.add_argument('profilers', metavar='options',
                        help='profiler configuration')
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

    if len(args.profilers) > len(set(args.profilers)):
        print('Profiler configuration is ambiguous. Remove duplicates.')
        sys.exit(1)

    available_profilers = {opt for opt, _ in _PROFILERS}
    for option in args.profilers:
        if option not in available_profilers:
            print('Unrecognized option: %s' % option)
            sys.exit(2)

    sys.argv[:] = args.source
    program_name, program_stats = args.source[0], OrderedDict()
    present_profilers = ((s, p) for s, p in _PROFILERS if s in args.profilers)
    for option, profiler in present_profilers:
        curr_profiler = profiler(program_name)
        print('Running %s...' % curr_profiler.__class__.__name__)
        program_stats[option] = curr_profiler.run()
    if not args.debug_mode:
        sys.stderr = open(os.devnull, "w")
    print('Starting HTTP server...')
    stats_server.start(
        _HOST, args.port, program_stats, args.dont_start_browser)

if __name__ == "__main__":
    main()
