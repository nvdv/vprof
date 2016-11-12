"""Module for statistical profiler."""
import inspect
import runpy
import signal
import time

from collections import defaultdict
from vprof import base_profiler

_SAMPLE_INTERVAL = 0.001


class _StatProfiler(object):
    """Statistical profiler.

    Samples call stack at regulal interval specified by _SAMPLE_INTERVAL.
    """

    def __init__(self):
        self._call_tree = {}
        self._stats = defaultdict(int)
        self._start_time = None
        self.base_frame = None
        self.run_time = None

    def __enter__(self):
        """Enables profiler."""
        signal.signal(signal.SIGPROF, self.sample)
        signal.setitimer(signal.ITIMER_PROF, _SAMPLE_INTERVAL)
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tbf):
        """Disables profiler."""
        self.run_time = time.time() - self._start_time
        signal.setitimer(signal.ITIMER_PROF, 0)

    def sample(self, signum, frame):  #pylint: disable=unused-argument
        """Callback that samples current stack and stores result in
        self._stats.

        Args:
            signum: Signal that activated handler.
            frame: Current frame when signal is handled.
        """
        stack = []
        while frame and frame != self.base_frame:
            stack.append((
                frame.f_code.co_name,
                frame.f_code.co_filename,
                frame.f_code.co_firstlineno))
            frame = frame.f_back
        self._stats[tuple(stack)] += 1
        signal.setitimer(signal.ITIMER_PROF, _SAMPLE_INTERVAL)

    def _insert_stack(self, stack, sample_count, call_tree):
        """Inserts stack with sample count creating all intermediate nodes in the
        call tree.

        Args:
            stack: Stack to insert into call_tree.
            sample_count: Sample count for stack.
            call_tree: Dict representing call tree.
        """
        curr_level = call_tree
        for func in stack:
            next_level = {
                node['stack']: node for node in curr_level['children']}
            if func not in next_level:
                new_stack = {
                    'stack': func,
                    'children': [],
                    'sampleCount': 0
                }
                curr_level['children'].append(new_stack)
                curr_level = new_stack
            else:
                curr_level = next_level[func]
        curr_level['sampleCount'] = sample_count

    def _fill_sample_count(self, node):
        """Fills proper sample counts inside call tree."""
        node['sampleCount'] += sum(
            self._fill_sample_count(child) for child in node['children'])
        return node['sampleCount']

    def _reformat_tree(self, node, total_samples):
        """Preprocesses call tree for UI."""
        funcname, filename, lineno = node['stack']
        funcname = funcname.replace('<', '[').replace('>', ']')
        filename = filename.replace('<', '[').replace('>', ']')
        percentage = 100 * round(float(node['sampleCount']) / total_samples, 3)
        return {
            'stack': (funcname, filename, lineno, percentage),
            'children': [self._reformat_tree(child, total_samples)
                         for child in node['children']],
            'sampleCount': node['sampleCount']
        }

    @property
    def call_tree(self):
        """Fills and returns the call tree obtained from profiler run."""
        if self._call_tree:
            return self._call_tree
        self._call_tree = {
            'stack': ('base', '', 1),
            'children': [],
            'sampleCount': 0}
        for stack, sample_count in self._stats.items():
            self._insert_stack(reversed(stack), sample_count, self._call_tree)
        self._fill_sample_count(self._call_tree)
        return self._reformat_tree(
            self._call_tree, self._call_tree['sampleCount'])


class FlameGraphProfiler(base_profiler.BaseProfiler):
    """Flame graph profiler wrapper.

    Runs statistical profiler and processes obtained stats.
    """

    def run_as_package(self):
        """Runs program as a Python package."""
        with _StatProfiler() as prof:
            try:
                runpy.run_path(self._run_object, run_name='__main__')
            except SystemExit:
                pass
        return prof

    def run_as_module(self):
        """Runs program as a Python module."""
        with open(self._run_object, 'rb') as srcfile, _StatProfiler() as prof:
            code = compile(srcfile.read(), self._run_object, 'exec')
            prof.base_frame = inspect.currentframe()
            try:
                exec(code, self._globs, None)
            except SystemExit:
                pass
        return prof

    def run_as_function(self):
        """Runs object as a function."""
        with _StatProfiler() as prof:
            self._run_object(*self._run_args, **self._run_kwargs)
        return prof

    def run(self):
        """Runs stat profiler and returns processed stats."""
        run_dispatcher = self.get_run_dispatcher()
        prof = run_dispatcher()
        return {
            'objectName': self._object_name,
            'sampleInterval': _SAMPLE_INTERVAL,
            'runTime': prof.run_time,
            'callStats': prof.call_tree,
            'totalSamples': prof.call_tree['sampleCount'],
        }
