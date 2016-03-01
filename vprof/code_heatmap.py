"""Module for code heatmap rendering."""
import inspect
import sys

from collections import defaultdict
from vprof import base_profile


class CodeHeatmapCalculator(object):
    """Calculates Python code heatmap.

    Class that contains all logic related to calculating execution heatmap
    for Python program.
    """

    def __init__(self):
        self._all_code = set()
        self._original_trace_function = sys.gettrace()
        self.heatmap = defaultdict(int)

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
            self.heatmap[frame.f_lineno] += 1
        return self._calc_heatmap


class CodeHeatmapProfile(base_profile.BaseProfile):
    """Code heatmap wrapper.

    Contains all logic related to heatmap calculation and processing.
    """

    def run(self):
        """Calculates code heatmap for specified Python program."""
        try:
            with open(self._program_name, 'r') as srcfile,\
                CodeHeatmapCalculator() as prof:
                src_code = srcfile.read()
                code = compile(src_code, self._program_name, 'exec')
                prof.add_code(code)
                exec(code, self._globs, None)
        except SystemExit:
            pass
        return {
            'programName': self._program_name,
            'srcCode': src_code,
            'heatmap': prof.heatmap
        }
