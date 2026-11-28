"""Code heatmap module."""
from collections import defaultdict
from collections import deque
from collections.abc import Iterator
import fnmatch
import inspect
import os
import runpy
import sys
import time
from types import FrameType
from typing import Any

from vprof import base_profiler

_PREFIXES = (
    sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix)
_STDLIB_PATHS = [
    os.path.abspath(path) for path in sys.path
    if os.path.isdir(path) and path.startswith(_PREFIXES)]


def check_standard_dir(module_path: str) -> bool:
    """Checks whether path belongs to standard library or installed modules."""
    if 'site-packages' in module_path:
        return True
    for stdlib_path in _STDLIB_PATHS:
        if fnmatch.fnmatchcase(module_path, stdlib_path + '*'):
            return True
    return False


class _CodeHeatmapCalculator:
    """Calculates Python code heatmap.

    Class that contains all logic related to calculating code heatmap
    for a Python program.
    """

    def __init__(self) -> None:
        self.original_trace_function = sys.gettrace()
        self.prev_lineno: int | None = None
        self.prev_timestamp: float | None = None
        self.prev_path: str | None = None
        self.lines: deque[list[Any]] = deque()
        self._execution_count: dict[str, dict[int, int]] = defaultdict(
            lambda: defaultdict(int))
        self._heatmap: dict[str, dict[int, float]] = defaultdict(
            lambda: defaultdict(float))

    def __enter__(self) -> '_CodeHeatmapCalculator':
        """Enables heatmap calculator."""
        sys.settrace(self.record_line)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tbf: Any) -> None:
        """Disables heatmap calculator."""
        sys.settrace(self.original_trace_function)
        if self.prev_timestamp:
            runtime = time.perf_counter() - self.prev_timestamp
            self.lines.append([self.prev_path, self.prev_lineno, runtime])

    def record_line(self, frame: FrameType, event: str, _arg: Any) -> Any:
        """Records line execution time."""
        if event == 'line':
            if self.prev_timestamp:
                runtime = time.perf_counter() - self.prev_timestamp
                self.lines.append([self.prev_path, self.prev_lineno, runtime])
            self.prev_lineno = frame.f_lineno
            self.prev_path = frame.f_code.co_filename
            self.prev_timestamp = time.perf_counter()
        return self.record_line

    @property
    def lines_without_stdlib(self) -> Iterator[list[Any]]:
        """Filters code from standard library from self.lines."""
        prev_line: list[Any] | None = None
        curr_frame = inspect.currentframe()
        src_file = inspect.getsourcefile(curr_frame) if curr_frame else None
        current_module_path = os.path.abspath(src_file or __file__)
        for module_path, lineno, runtime in self.lines:
            module_abspath = os.path.abspath(module_path)
            if not prev_line:
                prev_line = [module_abspath, lineno, runtime]
            else:
                if (not check_standard_dir(module_path) and
                        module_abspath != current_module_path):
                    yield prev_line
                    prev_line = [module_abspath, lineno, runtime]
                else:
                    prev_line[2] += runtime
        if prev_line is not None:
            yield prev_line

    def fill_heatmap(self) -> None:
        """Fills code heatmap and execution count dictionaries."""
        for module_path, lineno, runtime in self.lines_without_stdlib:
            self._execution_count[module_path][lineno] += 1
            self._heatmap[module_path][lineno] += runtime

    @property
    def heatmap(self) -> dict[str, dict[int, float]]:
        """Returns heatmap with absolute path names."""
        if not self._heatmap:
            self.fill_heatmap()
        return self._heatmap

    @property
    def execution_count(self) -> dict[str, dict[int, int]]:
        """Returns execution count map with absolute path names."""
        if not self._execution_count:
            self.fill_heatmap()
        return self._execution_count


class CodeHeatmapProfiler(base_profiler.BaseProfiler):
    """Code heatmap wrapper."""

    SKIP_LINES = 10
    MIN_SKIP_SIZE = 100

    def _calc_skips(
            self, heatmap: dict[int, float], num_lines: int
    ) -> list[tuple[int, int]]:
        """Calculates skip map for large sources.
        Skip map is a list of tuples where first element of tuple is a line
        number and second is a length of the skip region:
            [(1, 10), (15, 10)] means skipping 10 lines after line 1 and
            10 lines after line 15.
        """
        if num_lines < self.MIN_SKIP_SIZE:
            return []
        skips, prev_line = [], 0
        for line in sorted(heatmap):
            curr_skip = line - prev_line - 1
            if curr_skip > self.SKIP_LINES:
                skips.append((prev_line, curr_skip))
            prev_line = line
        if num_lines - prev_line > self.SKIP_LINES:
            skips.append((prev_line, num_lines - prev_line))
        return skips

    @staticmethod
    def _skip_lines(
            src_code: list[str], skip_map: list[tuple[int, int]]
    ) -> list[list[Any]]:
        """Skips lines in src_code specified by a skip map."""
        if not skip_map:
            return [['line', j + 1, l] for j, l in enumerate(src_code)]
        code_with_skips: list[list[Any]] = []
        i = 0
        for line, length in skip_map:
            code_with_skips.extend(
                ['line', i + j + 1, l] for j, l in enumerate(src_code[i:line]))
            if (code_with_skips
                    and code_with_skips[-1][0] == 'skip'):  # Merge skips.
                code_with_skips[-1][1] += length
            else:
                code_with_skips.append(['skip', length])
            i = line + length
        code_with_skips.extend(
            ['line', i + j + 1, l] for j, l in enumerate(src_code[i:]))
        return code_with_skips

    def _profile_package(self) -> dict[str, Any]:
        """Calculates heatmap for a package."""
        with _CodeHeatmapCalculator() as prof:
            try:
                runpy.run_path(self._run_object, run_name='__main__')
            except SystemExit:
                pass

        heatmaps = []
        for filename, heatmap in prof.heatmap.items():
            if os.path.isfile(filename):
                heatmaps.append(
                    self._format_heatmap(
                        filename, heatmap, prof.execution_count[filename]))

        run_time = sum(heatmap['runTime'] for heatmap in heatmaps)
        return {
            'objectName': self._run_object,
            'runTime': run_time,
            'heatmaps': heatmaps
        }

    def profile_package(self) -> dict[str, Any]:
        """Runs package profiler in a separate process."""
        return base_profiler.run_in_separate_process(self._profile_package)

    def _format_heatmap(
            self,
            filename: str,
            heatmap: dict[int, float],
            execution_count: dict[int, int]
    ) -> dict[str, Any]:
        """Formats heatmap for UI."""
        with open(filename, encoding='utf-8') as src_file:
            file_source = src_file.read().split('\n')
            skip_map = self._calc_skips(heatmap, len(file_source))
        run_time = sum(time for time in heatmap.values())
        return {
            'name': filename,
            'heatmap': heatmap,
            'executionCount': execution_count,
            'srcCode': self._skip_lines(file_source, skip_map),
            'runTime': run_time
        }

    def _profile_module(self) -> dict[str, Any]:
        """Calculates heatmap for a module."""
        with open(self._run_object, 'r', encoding='utf-8') as srcfile:
            src_code = srcfile.read()
            code = compile(src_code, self._run_object, 'exec')
        try:
            with _CodeHeatmapCalculator() as prof:
                exec(code, self._globs, None)  # pylint: disable=exec-used
        except SystemExit:
            pass

        heatmaps = []
        for filename, heatmap in prof.heatmap.items():
            if os.path.isfile(filename):
                heatmaps.append(
                    self._format_heatmap(
                        filename, heatmap, prof.execution_count[filename]))

        run_time = sum(heatmap['runTime'] for heatmap in heatmaps)
        return {
            'objectName': self._run_object,
            'runTime': run_time,
            'heatmaps': heatmaps
        }

    def profile_module(self) -> dict[str, Any]:
        """Runs module profiler in a separate process."""
        return base_profiler.run_in_separate_process(self._profile_module)

    def profile_function(self) -> dict[str, Any]:
        """Calculates heatmap for a function."""
        with _CodeHeatmapCalculator() as prof:
            result = self._run_object(*self._run_args, **self._run_kwargs)
        code_lines, start_line = inspect.getsourcelines(self._run_object)

        source_lines = []
        for line in code_lines:
            source_lines.append(('line', start_line, line))
            start_line += 1

        src_file = inspect.getsourcefile(self._run_object) or ''
        filename = os.path.abspath(src_file)
        heatmap = prof.heatmap[filename]
        run_time = sum(time for time in heatmap.values())
        return {
            'objectName': self._object_name,
            'runTime': run_time,
            'result': result,
            'timestamp': int(time.time()),
            'heatmaps': [{
                'name': self._object_name,
                'heatmap': heatmap,
                'executionCount': prof.execution_count[filename],
                'srcCode': source_lines,
                'runTime': run_time
            }]
        }
