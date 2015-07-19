"""Visual profiler for Python."""
import argparse
import cProfile
import json
import os
import pstats
import subprocess
import tempfile

_MODULE_DESC = 'Python visual profiler.'
_TMP_FILE = '/tmp/tempstats'
_PROFILE_FILENAME = 'profile.html'
_PROFILE_HTML = 'vprof/template/%s' % _PROFILE_FILENAME


def _change_stats_format(stats):
    """Changes format of stats from cProfile."""
    result_stats = {}
    for func_params, stats in stats.items():
        cum_calls, num_calls, time_per_call, cum_time, callers = stats
        func_name = func_params
        result_stats[func_name] = {
            'cum_calls': cum_calls,
            'num_calls': num_calls,
            'time_per_call': time_per_call,
            'cum_time': cum_time,
            'callers': callers,
        }
    return result_stats


# TODO(nvdv): Make this function iterative.
def _fill_stats(curr_node, all_callees, stats):
    """Recursively populates starts in call order."""
    curr_stats = {}
    curr_stats['name'] = ':'.join(str(token) for token in curr_node)
    curr_stats['cum_calls'] = stats[curr_node]['cum_calls']
    curr_stats['num_calls'] = stats[curr_node]['num_calls']
    curr_stats['time_per_call'] = stats[curr_node]['time_per_call']
    curr_stats['cum_time'] = stats[curr_node]['cum_time']
    curr_stats['children'] = [
        _fill_stats(child, all_callees, stats)
        for child in all_callees[curr_node]]
    return curr_stats


def transform_stats(stats):
    """Converts start from cProfile format to recusive dict."""
    stats.calc_callees()
    changed_stats = _change_stats_format(stats.stats)
    root = max(changed_stats.items(), key=lambda s: s[1]['cum_time'])
    return _fill_stats(root[0], stats.all_callees, changed_stats)


def main():
    parser = argparse.ArgumentParser(description=_MODULE_DESC)
    parser.add_argument('source', metavar='src', nargs=1,
                        help='Python program to profile.')
    args = parser.parse_args()

    with open(args.source[0]) as srcfile:
        cProfile.run(srcfile.read(), _TMP_FILE)
    stats = pstats.Stats(_TMP_FILE)
    transformed_stats = transform_stats(stats)
    os.remove(_TMP_FILE)

    program_info = {
        'program_name': args.source[0],
        'run_time': stats.total_tt,
        'primitive_calls': stats.prim_calls,
        'total_calls': stats.total_calls,
        'call_stats': transformed_stats,
    }
    with tempfile.NamedTemporaryFile(delete=False) as outfile:
        outfile.write(json.dumps(program_info, indent=2))
        stats_filename = outfile.name
    temp_dir = os.path.dirname(stats_filename)
    temp_filename = os.path.basename(stats_filename)

    with open(_PROFILE_HTML) as prof_html:
        html_data = prof_html.read()
    # TODO(nvdv): Find another way to do substitution.
    output_html = html_data.replace(
        'insert_json_filename_here', temp_filename)
    output_html_filename = temp_dir + os.sep + _PROFILE_FILENAME
    with open(output_html_filename, 'w') as output_file:
        output_file.write(output_html)

    subprocess.call(['open', output_html_filename])


if __name__ == "__main__":
    main()