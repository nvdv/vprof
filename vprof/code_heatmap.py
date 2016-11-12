"""Module for code heatmap rendering."""
import inspect
import operator
import os
import runpy
import sys

from collections import defaultdict
from vprof import base_profiler


class _CodeHeatmapCalculator(object):
    """Calculates Python code heatmap.

    Class that contains all logic related to calculating execution heatmap
    for Python program.
    """

    def __init__(self):
        self._all_code = set()
        self._original_trace_function = sys.gettrace()
        self.heatmap = defaultdict(lambda: defaultdict(int))

    def add_code(self, code):
        """Recursively adds code to be examined."""
        if code not in self._all_code:
            self._all_code.add(code)
            for subcode in filter(inspect.iscode, code.co_consts):
                self.add_code(subcode)

    def __enter__(self):
        """Enables heatmap calculator."""
        sys.settrace(self._calc_heatmap)
        return self

    def __exit__(self, exc_type, exc_val, exc_tbf):
        """Disables heatmap calculator."""
        sys.settrace(self._original_trace_function)

    def _calc_heatmap(self, frame, event, arg):  # pylint: disable=unused-argument
        """Calculates code heatmap."""
        if event == 'line' and frame.f_code in self._all_code:
            abs_filename = os.path.abspath(frame.f_code.co_filename)
            self.heatmap[abs_filename][frame.f_lineno] += 1
        return self._calc_heatmap


class CodeHeatmapProfiler(base_profiler.BaseProfiler):
    """Code heatmap wrapper.

    Contains all logic related to heatmap calculation and processing.
    """

    _SKIP_LINES = 10
    _MIN_SKIP_SIZE = 100

    def _consodalidate_stats(self, package_code, prof):
        """Merges profiler stats and package_code."""
        package_heatmap = []
        for modname, (src_code, _) in package_code.items():
            abs_path = (modname if os.path.isabs(modname)
                        else os.path.abspath(modname))
            heatmap = prof.heatmap[abs_path]
            if not heatmap:  # If no heatmap - skip module.
                continue
            sources = src_code.split('\n')
            skip_map = self._calc_skips(heatmap, len(sources))
            package_heatmap.append({
                'objectName': modname,
                'heatmap': heatmap,
                'srcCode': self._skip_lines(sources, skip_map)
            })
        return sorted(package_heatmap, key=operator.itemgetter('objectName'))

    def _calc_skips(self, heatmap, num_lines):
        """Calculates line skip map for large sources.
        Skip map is list of tuples, where first element of tuple is line
        number and second is length of skip region:
            [(1, 10), (15, 10)] means skip 10 lines after line 1 and
            10 lines after line 15.
        """
        if num_lines < self._MIN_SKIP_SIZE:
            return []
        skips, prev_line = [], 0
        for line in sorted(heatmap):
            curr_skip = line - prev_line - 1
            if curr_skip > self._SKIP_LINES:
                skips.append((prev_line, curr_skip))
            prev_line = line
        if num_lines - prev_line > self._SKIP_LINES:
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

    def run_as_package(self):
        """Runs program as Python package."""
        pkg_code = base_profiler.get_package_code(self._run_object)
        with _CodeHeatmapCalculator() as prof:
            for _, compiled_code in pkg_code.values():
                prof.add_code(compiled_code)
            try:
                runpy.run_path(self._run_object)
            except SystemExit:
                pass
        return self._consodalidate_stats(pkg_code, prof)

    def run_as_module(self):
        """Runs program as module."""
        try:
            with open(self._run_object, 'r') as srcfile, \
                    _CodeHeatmapCalculator() as prof:
                src_code = srcfile.read()
                code = compile(src_code, self._run_object, 'exec')
                prof.add_code(code)
                exec(code, self._globs, None)
        except SystemExit:
            pass
        heatmap = prof.heatmap[os.path.abspath(self._run_object)]
        sources = src_code.split('\n')
        skip_map = self._calc_skips(heatmap, len(sources))
        return [{
            'objectName': self._run_object,
            'heatmap': heatmap,
            'srcCode': self._skip_lines(sources, skip_map)
        }]

    def run_as_function(self):
        """Runs object as function."""
        with _CodeHeatmapCalculator() as prof:
            prof.add_code(self._run_object.__code__)
            self._run_object(*self._run_args, **self._run_kwargs)
        code_lines, start_line = inspect.getsourcelines(self._run_object)
        filename = os.path.abspath(inspect.getsourcefile(self._run_object))

        source_lines = []
        for line in code_lines:
            source_lines.append(('line', start_line, line))
            start_line += 1

        object_name = 'function %s @ %s' % (
            self._run_object.__name__, filename)
        return [{
            'objectName': object_name,
            'heatmap': prof.heatmap[filename],
            'srcCode': source_lines,
        }]

    def run(self):
        """Calculates code heatmap for specified Python program."""
        run_dispatcher = self.get_run_dispatcher()
        return run_dispatcher()
