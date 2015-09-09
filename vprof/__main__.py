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
    'c': profile.CProfile
}

def main():
    parser = argparse.ArgumentParser(description=_MODULE_DESC)
    parser.add_argument('profilers', metavar='opts',
                        help='Profilers configuration')
    parser.add_argument('source', metavar='src', nargs=1,
                        help='Python program to profile.')
    args = parser.parse_args()

    if len(args.profilers) > len(set(args.profilers)):
        print('Profiler configuration is ambiguous. Remove duplicates.')
        sys.exit(1)

    prof_option = args.profilers[0]
    for prof_option in args.profilers:
        if prof_option not in _PROFILE_MAP:
            print('Unrecognized option: %s' % prof_option)
            sys.exit(2)

    sys.argv[:] = args.source
    print('Collecting profile stats...')
    program_name = args.source[0]
    program_info = _PROFILE_MAP[prof_option](program_name).run()
    print('Starting stats server...')
    sys.stderr = open(os.devnull, "w")
    stats_server.start(_HOST, _PORT, program_info)


if __name__ == "__main__":
    main()
