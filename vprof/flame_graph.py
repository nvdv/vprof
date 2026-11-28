"""Flame graph module."""
from collections import defaultdict
from collections.abc import Iterable
import inspect
import runpy
import signal
import time
from types import FrameType
from typing import Any

from vprof import base_profiler

_SAMPLE_INTERVAL = 0.001
StackFrame = tuple[str, str, int]


class _StatProfiler:
    """Statistical profiler.

    Samples call stack at regular intervals specified by _SAMPLE_INTERVAL.
    """

    def __init__(self, base_frame: FrameType | None = None) -> None:
        self._stats: dict[tuple[StackFrame, ...], int] = defaultdict(int)
        self._start_time: float = 0.0
        self.base_frame: FrameType | None = base_frame
        self.run_time: float = 0.0

    def __enter__(self) -> '_StatProfiler':
        """Enables statistical profiler."""
        signal.signal(signal.SIGPROF, self.sample)
        signal.setitimer(signal.ITIMER_PROF, _SAMPLE_INTERVAL)
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tbf: Any) -> None:
        """Disables statistical profiler."""
        self.run_time = time.perf_counter() - self._start_time
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.signal(signal.SIGPROF, signal.SIG_IGN)

    def sample(self, _signum: int, frame: FrameType | None) -> None:
        """Samples current stack and writes result in self._stats.

        Args:
            _signum: Signal that activates handler.
            frame: Frame on top of the stack when signal is handled.
        """
        stack = []
        while frame and frame != self.base_frame:
            stack.append((
                frame.f_code.co_name,
                frame.f_code.co_filename,
                frame.f_code.co_firstlineno))
            frame = frame.f_back
        if stack:
            self._stats[tuple(stack)] += 1
        signal.setitimer(signal.ITIMER_PROF, _SAMPLE_INTERVAL)

    @staticmethod
    def _insert_stack(
            stack: Iterable[StackFrame],
            sample_count: int,
            call_tree: dict[str, Any]
    ) -> None:
        """Inserts a stack into the call tree.

        Args:
            stack: Call stack.
            sample_count: Sample count of call stack.
            call_tree: Call tree.
        """
        curr_level = call_tree
        for func in stack:
            next_level_index = {
                node['stack']: node for node in curr_level['children']}
            if func not in next_level_index:
                new_node: dict[str, Any] = {
                    'stack': func, 'children': [], 'sampleCount': 0}
                curr_level['children'].append(new_node)
                curr_level = new_node
            else:
                curr_level = next_level_index[func]
        curr_level['sampleCount'] = sample_count

    def _fill_sample_count(self, node: dict[str, Any]) -> int:
        """Counts and fills sample counts inside call tree."""
        node['sampleCount'] += sum(
            self._fill_sample_count(child) for child in node['children'])
        return node['sampleCount']

    @staticmethod
    def _get_percentage(sample_count: int, total_samples: int) -> float:
        """Return percentage of sample_count in total_samples."""
        if total_samples != 0:
            return 100 * round(float(sample_count) / total_samples, 3)
        return 0.0

    def _format_tree(
            self, node: dict[str, Any], total_samples: int
    ) -> dict[str, Any]:
        """Reformats call tree for the UI."""
        funcname, filename, _ = node['stack']
        sample_percent = self._get_percentage(
            node['sampleCount'], total_samples)
        color_hash = base_profiler.hash_name(f'{funcname} @ {filename}')
        return {
            'stack': node['stack'],
            'children': [self._format_tree(child, total_samples)
                         for child in node['children']],
            'sampleCount': node['sampleCount'],
            'samplePercentage': sample_percent,
            'colorHash': color_hash
        }

    @property
    def call_tree(self) -> dict[str, Any]:
        """Returns call tree."""
        call_tree: dict[str, Any] = {
            'stack': 'base', 'sampleCount': 0, 'children': []}
        for stack, sample_count in self._stats.items():
            self._insert_stack(reversed(stack), sample_count, call_tree)
        self._fill_sample_count(call_tree)
        if not call_tree['children']:
            return {}
        root_node = max(
            call_tree['children'], key=lambda node: node['sampleCount'])
        return self._format_tree(root_node, call_tree['sampleCount'])


class FlameGraphProfiler(base_profiler.BaseProfiler):
    """Statistical profiler wrapper.

    Runs statistical profiler and returns collected stats.
    """

    def _profile_package(self) -> dict[str, Any]:
        """Runs statistical profiler on a package."""
        with _StatProfiler(base_frame=inspect.currentframe()) as prof:
            try:
                runpy.run_path(self._run_object, run_name='__main__')
            except SystemExit:
                pass

        call_tree = prof.call_tree
        return {
            'objectName': self._object_name,
            'sampleInterval': _SAMPLE_INTERVAL,
            'runTime': prof.run_time,
            'callStats': call_tree,
            'totalSamples': call_tree.get('sampleCount', 0),
            'timestamp': int(time.time())
        }

    def profile_package(self) -> dict[str, Any]:
        """Runs package profiler in a separate process."""
        return base_profiler.run_in_separate_process(self._profile_package)

    def _profile_module(self) -> dict[str, Any]:
        """Runs statistical profiler on a module."""
        with open(self._run_object, 'rb') as srcfile:
            code = compile(srcfile.read(), self._run_object, 'exec')
        with _StatProfiler(base_frame=inspect.currentframe()) as prof:
            try:
                exec(code, self._globs, None)  # pylint: disable=exec-used
            except SystemExit:
                pass

        call_tree = prof.call_tree
        return {
            'objectName': self._object_name,
            'sampleInterval': _SAMPLE_INTERVAL,
            'runTime': prof.run_time,
            'callStats': call_tree,
            'totalSamples': call_tree.get('sampleCount', 0),
            'timestamp': int(time.time())
        }

    def profile_module(self) -> dict[str, Any]:
        """Runs module profiler in a separate process."""
        return base_profiler.run_in_separate_process(self._profile_module)

    def profile_function(self) -> dict[str, Any]:
        """Runs statistical profiler on a function."""
        with _StatProfiler() as prof:
            result = self._run_object(*self._run_args, **self._run_kwargs)

        call_tree = prof.call_tree
        return {
            'objectName': self._object_name,
            'sampleInterval': _SAMPLE_INTERVAL,
            'runTime': prof.run_time,
            'callStats': call_tree,
            'totalSamples': call_tree.get('sampleCount', 0),
            'result': result,
            'timestamp': int(time.time())
        }
