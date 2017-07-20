"""Module with functions that run profilers."""
# pylint: disable=wrong-import-position
import os
import psutil

try:
    import __builtin__ as builtins
except ImportError:  # __builtin__ was renamed to builtins in Python 3.
    import builtins

# Take initial RSS in order to compute profiler memory overhead
# when profiling single functions.
if not hasattr(builtins, 'initial_rss_size'):
    builtins.initial_rss_size = psutil.Process(os.getpid()).memory_info().rss
# pylint: disable=wrong-import-position

import json

from collections import OrderedDict
from six.moves import urllib
from vprof import code_heatmap
from vprof import flame_graph
from vprof import memory_profiler
from vprof import profiler
from vprof import stats_server

_PROFILERS = (
    ('m', memory_profiler.MemoryProfiler),
    ('c', flame_graph.FlameGraphProfiler),
    ('h', code_heatmap.CodeHeatmapProfiler),
    ('p', profiler.Profiler)
)


class Error(Exception):
    """Base exception for current module."""
    pass


class AmbiguousConfigurationError(Error):
    """Raised when profiler configuration is ambiguous."""
    pass


class BadOptionError(Error):
    """Raised when unknown options are present in the configuration."""
    pass


def run_profilers(run_object, prof_config, verbose=False):
    """Runs profilers on run_object.

    Args:
        run_object: An object (string or tuple) for profiling.
        prof_config: A string with profilers configuration.
        verbose: True if info about running profilers should be shown.
    Returns:
        An ordered dictionary with collected stats.
    Raises:
        AmbiguousConfigurationError: when prof_config is ambiguous.
        BadOptionError: when unknown options are present in configuration.
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
    for option, prof in present_profilers:
        curr_profiler = prof(run_object)
        if verbose:
            print('Running %s...' % curr_profiler.__class__.__name__)
        run_stats[option] = curr_profiler.run()
    return run_stats


def run(func, options, args=(), kwargs={}, host='localhost', port=8000):  # pylint: disable=dangerous-default-value
    """Runs profilers on function.
    Args:
        func: Python function object.
        options: String with profilers configuration (i.e. 'cmh').
        args: Arguments to pass to func.
        kwargs: Keyword arguments to pass to func.
        host: Host to send collected data to.
        port: Port to send collected data to.
    """
    run_stats = run_profilers((func, args, kwargs), options)
    post_data = stats_server.compress_data(
        json.dumps(run_stats).encode('utf-8'))
    urllib.request.urlopen('http://%s:%s' % (host, port), post_data)
