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
            self.heatmap[frame.f_code.co_filename][frame.f_lineno] += 1
        return self._calc_heatmap


class CodeHeatmapProfile(base_profile.BaseProfile):
    """Code heatmap wrapper.

    Contains all logic related to heatmap calculation and processing.
    """

    def _consodalidate_stats(self, package_code, prof):
        """Merges profiler stats and package_code."""
        package_heatmap = []
        for modname, (src_code, _) in package_code.items():
            abs_path = (modname if os.path.isabs(modname)
                        else os.path.abspath(modname))
            source_lines = [
                (i + 1, l) for i, l in enumerate(src_code.split('\n'))]
            package_heatmap.append({
                'objectName': os.path.relpath(abs_path),
                'heatmap': prof.heatmap[abs_path],
                'srcCode': source_lines
            })
        return sorted(package_heatmap, key=operator.itemgetter('objectName'))

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
        source_lines = [(i + 1, l) for i, l in enumerate(src_code.split('\n'))]
        return [{
            'objectName': self._run_object,
            'heatmap': prof.heatmap[self._run_object],
            'srcCode': source_lines
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
        filename = inspect.getsourcefile(self._run_object)

        source_lines = []
        for line in code_lines:
            source_lines.append((start_line, line))
            start_line += 1

        return [{
            'objectName': 'function %s' % self._run_object.__name__,
            'heatmap': prof.heatmap[filename],
            'srcCode': source_lines,
        }]

    def run(self):
        """Calculates code heatmap for specified Python program."""
        # Process script arguments properly.
        if self._run_args:
            sys.argv[:] = [self._run_object, self._run_args]
        else:
            sys.argv[:] = [self._run_object]
        run_dispatcher = self.get_run_dispatcher()
        return run_dispatcher()
