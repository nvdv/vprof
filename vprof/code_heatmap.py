"""Module for code heatmap rendering."""
import inspect
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

    def _add_source_for_profiled_files(self, package_code, prof):
        """Returns source code and heatmap for profiled files."""
        resulting_heatmap = []
        for src_fname, (src_code, _) in package_code.items():
            for prof_fname, fname_heatmap in prof.heatmap.items():
                if prof_fname.endswith(src_fname):
                    resulting_heatmap.append({
                        'filename': src_fname,
                        'fileHeatmap': dict(fname_heatmap),
                        'srcCode': src_code})
        return resulting_heatmap

    def run_as_package_path(self):
        """Runs program as package specified with file path."""
        import runpy
        pkg_code = base_profile.get_package_code(
            self._program_name, name_is_path=True)
        with CodeHeatmapCalculator() as prof:
            for _, compiled_code in pkg_code.values():
                prof.add_code(compiled_code)
            try:
                runpy.run_path(self._program_name)
            except SystemExit:
                pass
        return self._add_source_for_profiled_files(pkg_code, prof)

    def run_as_module(self):
        """Runs program as module."""
        try:
            with open(self._program_name, 'r') as srcfile,\
                CodeHeatmapCalculator() as prof:
                src_code = srcfile.read()
                code = compile(src_code, self._program_name, 'exec')
                prof.add_code(code)
                exec(code, self._globs, None)
        except SystemExit:
            pass
        return [{'filename': self._program_name,
                 'fileHeatmap': prof.heatmap[self._program_name],
                 'srcCode': src_code}]

    def run_as_package_in_namespace(self):
        """Runs program as package in Python namespace."""
        import runpy
        pkg_code = base_profile.get_package_code(self._program_name)
        with CodeHeatmapCalculator() as prof:
            for _, compiled_code in pkg_code.values():
                prof.add_code(compiled_code)
            try:
                runpy.run_module(self._program_name)
            except SystemExit:
                pass
            except ImportError:
                raise
        return self._add_source_for_profiled_files(pkg_code, prof)

    def run(self):
        """Calculates code heatmap for specified Python program."""
        run_dispatcher = self.get_run_dispatcher()
        heatmap = run_dispatcher()
        return {
            'programName': self._program_name,
            'heatmap': heatmap
        }
