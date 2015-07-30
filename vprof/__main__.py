"""Visual profiler for Python."""
import argparse
import cProfile
import json
import os
import pstats
import shutil
import subprocess
import tempfile

_MODULE_DESC = 'Python visual profiler.'
_PROFILE_FILENAME = 'profile.html'
_PROFILE_HTML = 'frontend/%s' % _PROFILE_FILENAME
_PROFILE_JS = 'frontend/vprof.js'
_PROFILE_CSS = 'frontend/vprof.css'
_JSON_FILENAME = 'profile.json'


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
                     for child in all_callees[curr_node]]
    }


def transform_stats(stats):
    """Converts start from cProfile format to recusive dict."""
    stats.calc_callees()
    changed_stats = _annotate_stats(stats.stats)
    root = max(changed_stats.items(), key=lambda s: s[1]['cum_time'])
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


def main():
    parser = argparse.ArgumentParser(description=_MODULE_DESC)
    parser.add_argument('source', metavar='src', nargs=1,
                        help='Python program to profile.')
    args = parser.parse_args()

    stats = get_stats(args.source[0])
    program_info = {
        'program_name': args.source[0],
        'run_time': stats.total_tt,
        'primitive_calls': stats.prim_calls,
        'total_calls': stats.total_calls,
        'call_stats': transform_stats(stats),
    }
    temp_dir = tempfile.mkdtemp()
    profile_json_name = temp_dir + os.sep + _JSON_FILENAME
    with open(profile_json_name, 'w') as json_file:
        json_file.write(json.dumps(program_info, indent=2))
    shutil.copy(os.path.dirname(__file__) + os.sep + _PROFILE_JS, temp_dir)
    shutil.copy(os.path.dirname(__file__) + os.sep + _PROFILE_HTML, temp_dir)
    shutil.copy(os.path.dirname(__file__) + os.sep + _PROFILE_CSS, temp_dir)
    subprocess.call(['open', temp_dir + os.sep + _PROFILE_FILENAME])


if __name__ == "__main__":
    main()
