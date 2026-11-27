"""Module with functions that run profilers."""
# pylint: disable=wrong-import-position, wrong-import-order
import builtins
import gzip
import os
import urllib.request

import psutil

# Take initial RSS in order to compute profiler memory overhead
# when profiling single functions.
if not hasattr(builtins, 'initial_rss_size'):
    builtins.initial_rss_size = psutil.Process(os.getpid()).memory_info().rss

import json

from vprof import code_heatmap
from vprof import flame_graph
from vprof import memory_profiler
from vprof import profiler

_PROFILERS = (
    ('m', memory_profiler.MemoryProfiler),
    ('c', flame_graph.FlameGraphProfiler),
    ('h', code_heatmap.CodeHeatmapProfiler),
    ('p', profiler.Profiler)
)


class Error(Exception):
    """Base exception for current module."""


class AmbiguousConfigurationError(Error):
    """Raised when profiler configuration is ambiguous."""


class BadOptionError(Error):
    """Raised when unknown options are present in the configuration."""


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
            f'Profiler configuration {prof_config} is ambiguous')

    available_profilers = {opt for opt, _ in _PROFILERS}
    for option in prof_config:
        if option not in available_profilers:
            raise BadOptionError(f'Unknown option: {option}')

    run_stats = {}
    present_profilers = ((o, p) for o, p in _PROFILERS if o in prof_config)
    for option, prof in present_profilers:
        curr_profiler = prof(run_object)
        if verbose:
            print(f'Running {curr_profiler.__class__.__name__}...')
        run_stats[option] = curr_profiler.run()
    return run_stats


# pylint: disable=too-many-arguments, too-many-positional-arguments
def run(func, options, args=(), kwargs=None, host='localhost', port=8000):
    """Runs profilers on a function.

    Args:
        func: A Python function.
        options: A string with profilers configuration (i.e. 'cmh').
        args: func non-keyword arguments.
        kwargs: func keyword arguments.
        host: Host name to send collected data.
        port: Port number to send collected data.

    Returns:
        A result of func execution.
    """
    if kwargs is None:
        kwargs = {}
    run_stats = run_profilers((func, args, kwargs), options)

    result = None
    for prof_stats in run_stats.values():
        if result is None:
            result = prof_stats['result']
        del prof_stats['result']  # Don't send result to remote host

    post_data = gzip.compress(
        json.dumps(run_stats).encode('utf-8'))
    with urllib.request.urlopen(f'http://{host}:{port}', post_data):
        pass
    return result
