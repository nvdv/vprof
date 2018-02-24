"""Code heatmap module."""
import inspect
import fnmatch
import os
import runpy
import sys
import time

from collections import defaultdict
from collections import deque
from vprof import base_profiler

_STDLIB_PATHS = [
    os.path.abspath(path) for path in sys.path
    if os.path.isdir(path) and path.startswith(sys.prefix)]


def check_standard_dir(module_path):
    """Checks whether path belongs to standard library or installed modules."""
    if 'site-packages' in module_path:
        return True
    for stdlib_path in _STDLIB_PATHS:
        if fnmatch.fnmatchcase(module_path, stdlib_path + '*'):
            return True
    return False


class _CodeHeatmapCalculator(object):
    """Calculates Python code heatmap.

    Class that contains all logic related to calculating code heatmap
    for a Python program.
    """

    def __init__(self):
        self.original_trace_function = sys.gettrace()
        self.prev_lineno = None
        self.prev_timestamp = None
        self.prev_path = None
        self.lines = deque()
        self._execution_count = defaultdict(lambda: defaultdict(int))
        self._heatmap = defaultdict(lambda: defaultdict(float))

    def __enter__(self):
        """Enables heatmap calculator."""
        sys.settrace(self.record_line)
        return self

    def __exit__(self, exc_type, exc_val, exc_tbf):
        """Disables heatmap calculator."""
        sys.settrace(self.original_trace_function)
        if self.prev_timestamp:
            runtime = time.time() - self.prev_timestamp
            self.lines.append([self.prev_path, self.prev_lineno, runtime])

    def record_line(self, frame, event, arg):  # pylint: disable=unused-argument
        """Records line execution time."""
        if event == 'line':
            if self.prev_timestamp:
                runtime = time.time() - self.prev_timestamp
                self.lines.append([self.prev_path, self.prev_lineno, runtime])
            self.prev_lineno = frame.f_lineno
            self.prev_path = frame.f_code.co_filename
            self.prev_timestamp = time.time()
        return self.record_line

    @property
    def lines_without_stdlib(self):
        """Filters code from standard library from self.lines."""
        prev_line = None
        current_module_path = inspect.getabsfile(inspect.currentframe())
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
        yield prev_line

    def fill_heatmap(self):
        """Fills code heatmap and execution count dictionaries."""
        for module_path, lineno, runtime in self.lines_without_stdlib:
            self._execution_count[module_path][lineno] += 1
            self._heatmap[module_path][lineno] += runtime

    @property
    def heatmap(self):
        """Returns heatmap with absolute path names."""
        if not self._heatmap:
            self.fill_heatmap()
        return self._heatmap

    @property
    def execution_count(self):
        """Returns execution count map with absolute path names."""
        if not self._execution_count:
            self.fill_heatmap()
        return self._execution_count


class CodeHeatmapProfiler(base_profiler.BaseProfiler):
    """Code heatmap wrapper."""

    SKIP_LINES = 10
    MIN_SKIP_SIZE = 100

    def _calc_skips(self, heatmap, num_lines):
        """Calculates skip map for large sources.
        Skip map is a list of tuples where first element of tuple is line
        number and second is length of the skip region:
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
    def _skip_lines(src_code, skip_map):
        """Skips lines in src_code specified by skip map."""
        if not skip_map:
            return [['line', j + 1, l] for j, l in enumerate(src_code)]
        code_with_skips, i = [], 0
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

    def _profile_package(self):
        """Calculates heatmap for package."""
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

    def profile_package(self):
        """Runs package profiler in separate process."""
        return base_profiler.run_in_separate_process(self._profile_package)

    def _format_heatmap(self, filename, heatmap, execution_count):
        """Formats heatmap for UI."""
        with open(filename) as src_file:
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

    def _profile_module(self):
        """Calculates heatmap for module."""
        with open(self._run_object, 'r') as srcfile:
            src_code = srcfile.read()
            code = compile(src_code, self._run_object, 'exec')
        try:
            with _CodeHeatmapCalculator() as prof:
                exec(code, self._globs, None)
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

    def profile_module(self):
        """Runs module profiler in separate process."""
        return base_profiler.run_in_separate_process(self._profile_module)

    def profile_function(self):
        """Calculates heatmap for function."""
        with _CodeHeatmapCalculator() as prof:
            result = self._run_object(*self._run_args, **self._run_kwargs)
        code_lines, start_line = inspect.getsourcelines(self._run_object)

        source_lines = []
        for line in code_lines:
            source_lines.append(('line', start_line, line))
            start_line += 1

        filename = os.path.abspath(inspect.getsourcefile(self._run_object))
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
