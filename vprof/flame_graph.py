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

    Samples call stack at regulal intervals specified by _SAMPLE_INTERVAL.
    """

    def __init__(self):
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
            next_level_index = {
                node['stack']: node for node in curr_level['children']}
            if func not in next_level_index:
                new_node = {'stack': func, 'children': [], 'sampleCount': 0}
                curr_level['children'].append(new_node)
                curr_level = new_node
            else:
                curr_level = next_level_index[func]
        curr_level['sampleCount'] = sample_count

    def _fill_sample_count(self, node):
        """Counts and fills sample counts inside call tree."""
        node['sampleCount'] += sum(
            self._fill_sample_count(child) for child in node['children'])
        return node['sampleCount']

    def _get_percentage(self, sample_count, total_samples):
        """Return percentage of sample_count in total_samples."""
        if total_samples != 0:
            return 100 * round(float(sample_count) / total_samples, 3)
        return 0.0

    def _format_tree(self, node, total_samples):
        """Reformats call tree for the UI."""
        funcname, filename, _ = node['stack']
        funcname = funcname.replace('<', '[').replace('>', ']')
        filename = filename.replace('<', '[').replace('>', ']')
        sample_percent = self._get_percentage(
            node['sampleCount'], total_samples)
        color_hash = base_profiler.hash_name('%s @ %s' % (funcname, filename))
        return {
            'stack': node['stack'],
            'children': [self._format_tree(child, total_samples)
                         for child in node['children']],
            'sampleCount': node['sampleCount'],
            'samplePercentage': sample_percent,
            'colorHash': color_hash
        }

    @property
    def call_tree(self):
        """Returns call tree from statistical profiler."""
        call_tree = {'stack': 'base', 'sampleCount': 0, 'children': []}
        for stack, sample_count in self._stats.items():
            self._insert_stack(reversed(stack), sample_count, call_tree)
        self._fill_sample_count(call_tree)
        if not call_tree['children']:
            return {}
        return self._format_tree(
            call_tree['children'][0], call_tree['sampleCount'])


class FlameGraphProfiler(base_profiler.BaseProfiler):
    """Flame graph profiler wrapper.

    Runs statistical profiler and returns obtained stats.
    """

    @base_profiler.run_in_another_process
    def run_as_package(self):
        """Runs program as a Python package."""
        with _StatProfiler() as prof:
            try:
                runpy.run_path(self._run_object, run_name='__main__')
            except SystemExit:
                pass

        call_tree = prof.call_tree
        return {
            'runTime': prof.run_time,
            'callStats': call_tree,
            'totalSamples': call_tree.get('sampleCount') or 0
        }

    @base_profiler.run_in_another_process
    def run_as_module(self):
        """Runs program as a Python module."""
        with open(self._run_object, 'rb') as srcfile, _StatProfiler() as prof:
            code = compile(srcfile.read(), self._run_object, 'exec')
            prof.base_frame = inspect.currentframe()
            try:
                exec(code, self._globs, None)
            except SystemExit:
                pass

        call_tree = prof.call_tree
        return {
            'runTime': prof.run_time,
            'callStats': call_tree,
            'totalSamples': call_tree.get('sampleCount') or 0
        }

    def run_as_function(self):
        """Runs object as a function."""
        with _StatProfiler() as prof:
            self._run_object(*self._run_args, **self._run_kwargs)

        call_tree = prof.call_tree
        return {
            'runTime': prof.run_time,
            'callStats': call_tree,
            'totalSamples': call_tree.get('sampleCount') or 0
        }

    def run(self):
        """Runs statistical profiler and returns stats."""
        run_dispatcher = self.get_run_dispatcher()
        profiler_output = run_dispatcher()
        return {
            'objectName': self._object_name,
            'sampleInterval': _SAMPLE_INTERVAL,
            'runTime': profiler_output['runTime'],
            'callStats': profiler_output['callStats'],
            'totalSamples': profiler_output['totalSamples'],
        }
