"""Module for statistical profiler."""
import inspect
import runpy
import signal
import time

from collections import defaultdict
from vprof import base_profiler

_SAMPLE_INTERVAL = 0.001


#TODO(nvdv): Some of class methods look complicated. Consider refactoring them.
class _StatProfiler(object):
    """Statistical profiler.

    Samples call stack at regulal intervals specified by _SAMPLE_INTERVAL.
    """

    def __init__(self):
        self._call_tree = {}
        self._stats = defaultdict(int)
        self._start_time = None
        self.base_frame = None
        self.run_time = None

    def __enter__(self):
        """Enables statistical profiler."""
        signal.signal(signal.SIGPROF, self.sample)
        signal.setitimer(signal.ITIMER_PROF, _SAMPLE_INTERVAL)
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tbf):
        """Disables statistical profiler."""
        self.run_time = time.time() - self._start_time
        signal.setitimer(signal.ITIMER_PROF, 0)

    def sample(self, signum, frame):  #pylint: disable=unused-argument
        """Samples current stack and stores result in self._stats.

        Used as callback.

        Args:
            signum: Signal that activates handler.
            frame: Frame on top of the stack when signal is handled.
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
        """Inserts stack into the call tree.

        Also creates all intermediate nodes in the call tree.

        Args:
            stack: Call stack to be inserted.
            sample_count: Sample count for call stack.
            call_tree: Python dict representing the call tree.
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
        """Counts and fills sample counts inside call tree."""
        node['sampleCount'] += sum(
            self._fill_sample_count(child) for child in node['children'])
        return node['sampleCount']

    def _extract_stack_params(self, node, total_samples):
        """Extracts and processes stack parameters from call tree node."""
        funcname, filename, lineno = node['stack']
        funcname = funcname.replace('<', '[').replace('>', ']')
        filename = filename.replace('<', '[').replace('>', ']')
        if total_samples != 0:
            percentage = 100 * round(
                float(node['sampleCount']) / total_samples, 3)
        else:
            percentage = 0.0
        return funcname, filename, lineno, percentage

    def _reformat_tree(self, node, total_samples):
        """Reformats call tree for the UI."""
        stack_params = self._extract_stack_params(node, total_samples)
        func_name = '%s @ %s' % (stack_params[0], stack_params[1])
        return {
            'stack': stack_params,
            'children': [self._reformat_tree(child, total_samples)
                         for child in node['children']],
            'sampleCount': node['sampleCount'],
            'colorHash': base_profiler.hash_name(func_name)
        }

    @property
    def call_tree(self):
        """Returns call tree from statistical profiler."""
        if self._call_tree:
            return self._call_tree

        # Add base node to call tree for convenience,
        call_tree = {
            'stack': ('base', '', 1),
            'children': [],
            'sampleCount': 0}
        for stack, sample_count in self._stats.items():
            self._insert_stack(reversed(stack), sample_count, call_tree)
        self._fill_sample_count(call_tree)
        call_tree = self._reformat_tree(
            call_tree, call_tree['sampleCount'])

        # Omit base node in results.
        if call_tree['children']:
            self._call_tree = call_tree['children'][0]
        return self._call_tree


class FlameGraphProfiler(base_profiler.BaseProfiler):
    """Flame graph profiler wrapper.

    Runs statistical profiler and returns obtained stats.
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
        """Runs statistical profiler and returns stats."""
        run_dispatcher = self.get_run_dispatcher()
        prof = run_dispatcher()
        sample_count = prof.call_tree.get('sampleCount') or 0
        return {
            'objectName': self._object_name,
            'sampleInterval': _SAMPLE_INTERVAL,
            'runTime': prof.run_time,
            'callStats': prof.call_tree,
            'totalSamples': sample_count,
        }
