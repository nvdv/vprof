"""Visual profiler for Python."""
import argparse
import cProfile
import functools
import json
import os
import pstats
import stats_server
import subprocess
import sys

from collections import defaultdict

_MODULE_DESC = 'Python visual profiler.'
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
        stats_server.StatsHandler, profile_json=json.dumps(program_info))
    subprocess.call(['open', 'http://%s:%s' % (_HOST, _PORT)])
    stats_server.start(_HOST, _PORT, partial_handler)


if __name__ == "__main__":
    main()
