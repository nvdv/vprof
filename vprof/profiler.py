"""Module that contains vprof runtime logic."""
import json

from collections import OrderedDict
from six.moves import urllib
from vprof import code_heatmap
from vprof import memory_profile
from vprof import runtime_profile

_PROFILERS = (
    ('c', runtime_profile.RuntimeProfile),
    ('m', memory_profile.MemoryProfile),
    ('h', code_heatmap.CodeHeatmapProfile),
)


class Error(Exception):
    """Base exception for current module."""
    pass


class AmbiguousConfigurationError(Error):
    """Raised when profiler configuration is ambiguous."""
    pass


class BadOptionError(Error):
    """Raised when unknown options is present in configuration."""
    pass


def run_profilers(run_object, prof_config, verbose=False):
    """Runs profilers against run_object.

    Args:
        run_object: An object (string or tuple) to run profilers agaist.
        prof_config: A string with profilers configuration.
        verbose: True if info about running profilers should be shown.
    Returns:
        An ordered dictionary with collected stats.
    Raises:
        AmbiguousConfigurationError: when prof_config is ambiguous.
        BadOptionError: when unknown option is present in configuration.
    """
    if len(prof_config) > len(set(prof_config)):
        raise AmbiguousConfigurationError(
            'Profiler configuration %s is ambiguous' % prof_config)

    available_profilers = {opt for opt, _ in _PROFILERS}
    for option in prof_config:
        if option not in available_profilers:
            raise BadOptionError('Unknown option: %s' % option)

    run_stats = OrderedDict()
    present_profilers = ((o, p) for o, p in _PROFILERS if o in prof_config)
    for option, profiler in present_profilers:
        curr_profiler = profiler(run_object)
        if verbose:
            print('Running %s...' % curr_profiler.__class__.__name__)
        run_stats[option] = curr_profiler.run()
    return run_stats


def run(func, options, args=(), kwargs={}, host='localhost', port=8000):  # pylint: disable=dangerous-default-value
    """Runs profilers specified by options against func.
    Args:
        func: Python function object.
        options: A string with profilers configuration (i.e. 'cmh').
        args: Arguments to pass to func.
        kwargs: Keyword arguments to pass to func.
        host: Host to send profilers data.
        port: Port to send profilers.data.
    """
    run_stats = run_profilers((func, args, kwargs), options)
    post_data = json.dumps(run_stats).encode('utf-8')
    urllib.request.urlopen('http://%s:%s' % (host, port), post_data)
