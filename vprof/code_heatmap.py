"""Code heatmap module."""
import inspect
import operator
import os
import runpy
import sys
import time

from collections import defaultdict
from vprof import base_profiler


class _CodeHeatmapCalculator(object):
    """Calculates Python code heatmap.

    Class that contains all logic related to calculating code heatmap
    for a Python program.
    """

    def __init__(self):
        self.all_code = set()
        self.original_trace_function = sys.gettrace()
        self._execution_count = defaultdict(lambda: defaultdict(int))
        self._heatmap = defaultdict(lambda: defaultdict(float))
        self.prev_lineno = None
        self.prev_filename = None
        self.prev_timestamp = None

    def add_code(self, code):
        """Recursively adds code to be examined."""
        if code not in self.all_code:
            self.all_code.add(code)
            for subcode in filter(inspect.iscode, code.co_consts):
                self.add_code(subcode)

    def __enter__(self):
        """Enables heatmap calculator."""
        sys.settrace(self.calc_heatmap)
        return self

    def __exit__(self, exc_type, exc_val, exc_tbf):
        """Disables heatmap calculator."""
        if self.prev_lineno:
            self._heatmap[self.prev_filename][self.prev_lineno] += (
                time.time() - self.prev_timestamp)
            self.prev_lineno = None
        sys.settrace(self.original_trace_function)

    def calc_heatmap(self, frame, event, arg):  # pylint: disable=unused-argument
        """Calculates code heatmap."""
        if event == 'line' and frame.f_code in self.all_code:
            if self.prev_lineno:
                self._heatmap[self.prev_filename][self.prev_lineno] += (
                    time.time() - self.prev_timestamp)
                self.prev_lineno = None
            self._execution_count[frame.f_code.co_filename][frame.f_lineno] += 1
            self.prev_filename = frame.f_code.co_filename
            self.prev_lineno = frame.f_lineno
            self.prev_timestamp = time.time()
        return self.calc_heatmap

    @property
    def heatmap(self):
        """Returns heatmap with absolute path names."""
        return {os.path.abspath(fname): self._heatmap[fname]
                for fname in self._heatmap}

    @property
    def execution_count(self):
        """Returns execution count map with absolute path names."""
        return {os.path.abspath(fname): self._execution_count[fname]
                for fname in self._heatmap}


class CodeHeatmapProfiler(base_profiler.BaseProfiler):
    """Code heatmap wrapper."""

    SKIP_LINES = 10
    MIN_SKIP_SIZE = 100

    def _consodalidate_stats(self, package_code, prof):
        """Merges profiler stats and package_code."""
        package_heatmap = []
        for modname, (src_code, _) in package_code.items():
            abs_path = (modname if os.path.isabs(modname)
                        else os.path.abspath(modname))
            heatmap = prof.heatmap.get(abs_path)
            if not heatmap:
                continue
            exec_count = prof.execution_count[abs_path]
            sources = src_code.split('\n')
            skip_map = self._calc_skips(heatmap, len(sources))
            run_time = sum(time for time in heatmap.values())
            package_heatmap.append({
                'name': modname,
                'heatmap': heatmap,
                'executionCount': exec_count,
                'srcCode': self._skip_lines(sources, skip_map),
                'runTime': run_time
            })
        return sorted(package_heatmap, key=operator.itemgetter('name'))

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
        pkg_code = base_profiler.get_package_code(self._run_object)
        with _CodeHeatmapCalculator() as prof:
            for _, compiled_code in pkg_code.values():
                prof.add_code(compiled_code)
            try:
                runpy.run_path(self._run_object, run_name='__main__')
            except SystemExit:
                pass
        package_heatmap = self._consodalidate_stats(pkg_code, prof)
        run_time = sum(heatmap['runTime'] for heatmap in package_heatmap)
        return {
            'objectName': self._run_object,
            'runTime': run_time,
            'heatmaps': package_heatmap
        }

    def profile_package(self):
        """Runs package profiler in separate process."""
        return base_profiler.run_in_separate_process(self._profile_package)

    def _profile_module(self):
        """Calculates heatmap for module."""
        try:
            with open(self._run_object, 'r') as srcfile, \
                    _CodeHeatmapCalculator() as prof:
                src_code = srcfile.read()
                code = compile(src_code, self._run_object, 'exec')
                prof.add_code(code)
                exec(code, self._globs, None)
        except SystemExit:
            pass
        abspath = os.path.abspath(self._run_object)
        heatmap = prof.heatmap[abspath]
        execution_count = prof.execution_count[abspath]
        sources = src_code.split('\n')
        skip_map = self._calc_skips(heatmap, len(sources))
        run_time = sum(time for time in heatmap.values())
        return {
            'objectName': self._run_object,
            'runTime': run_time,
            'heatmaps': [{
                'name': self._run_object,
                'heatmap': heatmap,
                'executionCount': execution_count,
                'srcCode': self._skip_lines(sources, skip_map),
                'runTime': run_time
            }]
        }

    def profile_module(self):
        """Runs module profiler in separate process."""
        return base_profiler.run_in_separate_process(self._profile_module)

    def profile_function(self):
        """Calculates heatmap for function."""
        with _CodeHeatmapCalculator() as prof:
            prof.add_code(self._run_object.__code__)
            self._run_object(*self._run_args, **self._run_kwargs)
        code_lines, start_line = inspect.getsourcelines(self._run_object)
        filename = os.path.abspath(inspect.getsourcefile(self._run_object))

        source_lines = []
        for line in code_lines:
            source_lines.append(('line', start_line, line))
            start_line += 1

        heatmap = prof.heatmap[filename]
        object_name = 'function %s @ %s' % (self._run_object.__name__, filename)
        run_time = sum(time for time in heatmap.values())
        return {
            'objectName': object_name,
            'runTime': run_time,
            'heatmaps': [{
                'name': object_name,
                'heatmap': heatmap,
                'executionCount': prof.execution_count[filename],
                'srcCode': source_lines,
                'runTime': run_time
            }]
        }
