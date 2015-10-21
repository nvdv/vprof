"""Visual profiler for Python."""
import argparse
import profile
import stats_server
import os
import sys

_MODULE_DESC = 'Python visual profiler.'
_HOST = 'localhost'
_PORT = 8000

_PROFILE_MAP = {
    'c': profile.CProfile,
    'm': profile.MemoryProfile,
}

def main():
    """Visual profiler main function."""
    parser = argparse.ArgumentParser(description=_MODULE_DESC)
    parser.add_argument('profilers', metavar='opts',
                        help='Profilers configuration')
    parser.add_argument('source', metavar='src', nargs=1,
                        help='Python program to profile.')
    args = parser.parse_args()

    if len(args.profilers) > len(set(args.profilers)):
        print('Profiler configuration is ambiguous. Remove duplicates.')
        sys.exit(1)

    for option in args.profilers:
        if option not in _PROFILE_MAP:
            print('Unrecognized option: %s' % option)
            sys.exit(2)

    sys.argv[:] = args.source
    program_name, program_stats = args.source[0], {}
    for option in args.profilers:
        program_stats[option] = _PROFILE_MAP[option](program_name).run()
    sys.stderr = open(os.devnull, "w")
    print('Starting stats server...')
    stats_server.start(_HOST, _PORT, program_stats)

if __name__ == "__main__":
    main()
