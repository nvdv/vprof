"""Profiler's main module."""
# pylint: disable=wrong-import-position
import os
import psutil

# Take process RSS in order to compute profiler memory overhead.
try:
    import __builtin__ as builtins
except ImportError:  # __builtin__ was renamed to builtins in Python 3.
    import builtins
builtins.initial_rss_size = psutil.Process(os.getpid()).memory_info().rss
# pylint: disable=wrong-import-position

import argparse
import json
import sys

from vprof import runner
from vprof import stats_server

__version__ = '0.37'

_PROGRAN_NAME = 'vprof'
_MODULE_DESC = 'Visual profiler for Python'
_HOST, _PORT = 'localhost', 8000
_CONFIG_DESC = (
    """profile program SRC with configuration CONFIG
available CONFIG options
  c - flame graph
  m - memory graph
  h - code heatmap""")
_ERR_CODES = {
    'ambiguous_configuration': 1,
    'bad_option': 2,
    'input_file_error': 3
}


def main():
    """Main function of the module."""
    parser = argparse.ArgumentParser(
        prog=_PROGRAN_NAME, description=_MODULE_DESC,
        formatter_class=argparse.RawTextHelpFormatter)
    launch_modes = parser.add_mutually_exclusive_group(required=True)
    launch_modes.add_argument('-r', '--remote', dest='remote',
                              action='store_true', default=False,
                              help='launch in remote mode')
    launch_modes.add_argument('-i', '--input-file', dest='input_file',
                              type=str, default='',
                              help='render UI from file')
    launch_modes.add_argument('-c', '--config', nargs=2, dest='config',
                              help=_CONFIG_DESC, metavar=('CONFIG', 'SRC'))
    parser.add_argument('-H', '--host', dest='host', default=_HOST, type=str,
                        help='set internal webserver host')
    parser.add_argument('-p', '--port', dest='port', default=_PORT, type=int,
                        help='set internal webserver port')
    parser.add_argument('-n', '--no-browser', dest='dont_start_browser',
                        action='store_true', default=False,
                        help="don't start browser automatically")
    parser.add_argument('-o', '--output-file', dest='output_file',
                        type=str, default='', help='save profile to file')
    parser.add_argument('--debug', dest='debug_mode',
                        action='store_true', default=False,
                        help="don't suppress error messages")
    parser.add_argument('--version', action='version',
                        version='vprof %s' % __version__)
    args = parser.parse_args()

    # Render UI from file.
    if args.input_file:
        with open(args.input_file) as ifile:
            saved_stats = json.loads(ifile.read())
            if saved_stats['version'] != __version__:
                print('Incorrect profiler version - %s. %s is required.' % (
                    saved_stats['version'], __version__))
                sys.exit(_ERR_CODES['input_file_error'])
            stats_server.start(args.host, args.port, saved_stats,
                               args.dont_start_browser, args.debug_mode)
    # Launch in remote mode.
    elif args.remote:
        stats_server.start(args.host, args.port, {},
                           args.dont_start_browser, args.debug_mode)
    # Profiler mode.
    else:
        config, source = args.config
        try:
            program_stats = runner.run_profilers(source, config, verbose=True)
        except runner.AmbiguousConfigurationError:
            print('Profiler configuration %s is ambiguous. '
                  'Please, remove duplicates.' % config)
            sys.exit(_ERR_CODES['ambiguous_configuration'])
        except runner.BadOptionError as exc:
            print(exc)
            sys.exit(_ERR_CODES['bad_option'])

        if args.output_file:
            with open(args.output_file, 'w') as outfile:
                program_stats['version'] = __version__
                outfile.write(json.dumps(program_stats, indent=2))
        else:
            stats_server.start(
                args.host, args.port, program_stats,
                args.dont_start_browser, args.debug_mode)

if __name__ == "__main__":
    main()
