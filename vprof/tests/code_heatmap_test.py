import sys
import unittest

from collections import defaultdict
from vprof import code_heatmap

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock


class CodeHeatmapCalculator(unittest.TestCase):
    def setUp(self):
        self._calc = object.__new__(code_heatmap.CodeHeatmapCalculator)

    def testInit(self):
        self._calc.__init__()
        self.assertEqual(self._calc._all_code, set())
        self.assertEqual(self._calc._original_trace_function, sys.gettrace())
        self.assertEqual(self._calc.heatmap, defaultdict(int))

    def testAddCode(self):
        code = mock.MagicMock()
        self._calc._all_code = set()
        self._calc.add_code(code)
        self.assertIn(code, self._calc._all_code)

    def testCalcHeatmap(self):
        self._calc.heatmap = defaultdict(int)
        event, arg = 'line', mock.MagicMock()
        frame1, frame2 = mock.MagicMock(), mock.MagicMock()
        frame1.f_code, frame1.f_code = 'foo1', 'foo2'
        frame1.f_lineno, frame2.f_lineno = 1, 2
        self._calc._all_code = set((frame1.f_code, frame2.f_code))

        self._calc._calc_heatmap(frame1, event, arg)
        self._calc._calc_heatmap(frame2, event, arg)

        self.assertEqual(self._calc.heatmap[frame1.f_lineno], 1)
        self.assertEqual(self._calc.heatmap[frame2.f_lineno], 1)
