"""Module for code heatmap rendering."""
import inspect
import operator
import os
import sys

from collections import defaultdict
from vprof import base_profile


class Error(Exception):
    """Base exception for current module."""
    pass


class CodeHeatmapRunError(Error, base_profile.ProfilerRuntimeException):
    """Runtime exception for code heatmap profiler."""
    pass


class CodeHeatmapCalculator(object):
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

    def _calc_heatmap(self, frame, event, arg):  #pylint: disable=unused-argument
        """Calculates code heatmap."""
        if event == 'line' and frame.f_code in self._all_code:
            abs_filename = os.path.abspath(frame.f_code.co_filename)
            self.heatmap[abs_filename][frame.f_lineno] += 1
        return self._calc_heatmap


class CodeHeatmapProfile(base_profile.BaseProfile):
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
            src_lines = [
                (i + 1, l) for i, l in enumerate(src_code.split('\n'))]
            skip_map = []
            if len(src_lines) > self._MIN_SKIP_SIZE:
                skip_map = self._calc_skips(heatmap, len(src_lines))
            package_heatmap.append({
                'objectName': modname,
                'heatmap': heatmap,
                'srcCode': src_lines,
                'skipMap': skip_map
            })
        return sorted(package_heatmap, key=operator.itemgetter('objectName'))

    def _calc_skips(self, heatmap, num_lines):
        """Calculates line skip map for large sources."""
        skips, prev_line = [], 0
        for line in sorted(heatmap):
            curr_skip = line - prev_line
            if curr_skip > self._SKIP_LINES:
                skips.append((prev_line, curr_skip))
            prev_line = line
        if num_lines - prev_line > self._SKIP_LINES:
            skips.append((prev_line, num_lines - prev_line))
        return skips

    def _prune_src_lines(self, src_lines, skip_map):
        """Removes lines specified by skip_map from src_lines."""
        pruned_sources, i = [], 0
        for line, length in skip_map:
            pruned_sources.extend(src_lines[i:line])
            i = line + length
        return pruned_sources

    def run_as_package_path(self):
        """Runs program as package specified with file path."""
        import runpy
        pkg_code = base_profile.get_package_code(
            self._run_object, name_is_path=True)
        with CodeHeatmapCalculator() as prof:
            for _, compiled_code in pkg_code.values():
                prof.add_code(compiled_code)
            try:
                runpy.run_path(self._run_object)
            except ImportError:
                raise CodeHeatmapRunError(
                    'Unable to run package %s' % self._run_object)
            except SystemExit:
                pass
        return self._consodalidate_stats(pkg_code, prof)

    def run_as_module(self):
        """Runs program as module."""
        try:
            with open(self._run_object, 'r') as srcfile,\
                CodeHeatmapCalculator() as prof:
                src_code = srcfile.read()
                code = compile(src_code, self._run_object, 'exec')
                prof.add_code(code)
                exec(code, self._globs, None)
        except SystemExit:
            pass
        src_lines = [(i + 1, l) for i, l in enumerate(src_code.split('\n'))]
        heatmap = prof.heatmap[os.path.abspath(self._run_object)]
        skip_map = self._calc_skips(heatmap, len(src_lines))
        if not skip_map or len(src_lines) > self._MIN_SKIP_SIZE:
            pruned_sources = src_lines
        else:
            pruned_sources = self._prune_src_lines(src_lines, skip_map)
        return [{
            'objectName': self._run_object,
            'heatmap': heatmap,
            'srcCode': pruned_sources,
            'skipMap': skip_map
        }]

    def run_as_package_in_namespace(self):
        """Runs program as package in Python namespace."""
        import runpy
        pkg_code = base_profile.get_package_code(self._run_object)
        with CodeHeatmapCalculator() as prof:
            for _, compiled_code in pkg_code.values():
                prof.add_code(compiled_code)
            try:
                runpy.run_module(self._run_object)
            except ImportError:
                raise CodeHeatmapRunError(
                    'Unable to run package %s' % self._run_object)
            except SystemExit:
                pass
        return self._consodalidate_stats(pkg_code, prof)

    def run_as_function(self):
        """Runs object as function."""
        with CodeHeatmapCalculator() as prof:
            prof.add_code(self._run_object.__code__)
            self._run_object(*self._run_args, **self._run_kwargs)
        code_lines, start_line = inspect.getsourcelines(self._run_object)
        filename = os.path.abspath(inspect.getsourcefile(self._run_object))

        source_lines = []
        for line in code_lines:
            source_lines.append((start_line, line))
            start_line += 1

        object_name = 'function %s @ %s' % (
            self._run_object.__name__, filename)
        return [{
            'objectName': object_name,
            'heatmap': prof.heatmap[filename],
            'srcCode': source_lines,
            'skipMap': [],
        }]

    def run(self):
        """Calculates code heatmap for specified Python program."""
        run_dispatcher = self.get_run_dispatcher()
        return run_dispatcher()
