"""Visual profiler for Python."""
import argparse
import functools
import json
import profile
import stats_server
import subprocess
import sys

_MODULE_DESC = 'Python visual profiler.'
_HOST = 'localhost'
_PORT = 8000


def main():
    parser = argparse.ArgumentParser(description=_MODULE_DESC)
    parser.add_argument('source', metavar='src', nargs=1,
                        help='Python program to profile.')
    args = parser.parse_args()
    sys.argv[:] = args.source

    print('Collecting profile stats...')
    program_info = profile.CProfile(args.source[0]).run()

    partial_handler = functools.partial(
        stats_server.StatsHandler, profile_json=json.dumps(program_info))
    subprocess.call(['open', 'http://%s:%s' % (_HOST, _PORT)])
    stats_server.start(_HOST, _PORT, partial_handler)


if __name__ == "__main__":
    main()
