# pylint: disable=protected-access, missing-docstring
import sys
import unittest

from collections import defaultdict
from vprof import code_heatmap

# For Python 2 and Python 3 compatibility.
try:
    import mock
except ImportError:
    from unittest import mock  # pylint: disable=ungrouped-imports


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

    @mock.patch('os.path.abspath')
    def testCalcHeatmap(self, abspath_mock):
        abspath_mock.side_effect = lambda arg: arg
        self._calc.heatmap = defaultdict(lambda: defaultdict(int))
        event, arg = 'line', mock.MagicMock()
        frame1, frame2 = mock.MagicMock(), mock.MagicMock()
        frame1.f_code, frame2.f_code = mock.MagicMock(), mock.MagicMock()
        frame1.f_code.co_filename = 'foo.py'
        frame2.f_code.co_filename = 'foo.py'
        frame1.f_lineno, frame2.f_lineno = 1, 2
        self._calc._all_code = set((frame1.f_code, frame2.f_code))

        self._calc._calc_heatmap(frame1, event, arg)
        self._calc._calc_heatmap(frame2, event, arg)

        self.assertEqual(
            self._calc.heatmap[frame1.f_code.co_filename][frame1.f_lineno], 1)
        self.assertEqual(
            self._calc.heatmap[frame2.f_code.co_filename][frame2.f_lineno], 1)


class CodeHeatmapProfileUnitTest(unittest.TestCase):
    def setUp(self):
        self._profile = object.__new__(code_heatmap.CodeHeatmapProfile)

    def testCalcSkips(self):
        heatmap = {1: 1, 2: 1, 3: 1}
        self.assertListEqual(self._profile._calc_skips(heatmap, 3), [])

        heatmap = {1: 1, 2: 1, 99: 1, 102: 1, 115: 10}
        self.assertListEqual(
            self._profile._calc_skips(heatmap, 115), [(2, 97), (102, 13)])

        heatmap = {1: 1, 102: 1, 103: 1, 104: 1, 105: 1}
        self.assertListEqual(
            self._profile._calc_skips(heatmap, 115), [(1, 101)])

    def testPruneSrcLines(self):
        self._profile._MIN_SKIP_SIZE = 0
        src_lines = [(1, 'foo'), (2, 'bar'), (3, 'baz')]
        skip_map = []
        self.assertListEqual(
            self._profile._prune_src_lines(src_lines, skip_map), src_lines)

        src_lines = [(1, 'foo'), (2, 'bar'), (3, 'baz'), (4, 'hahaha')]
        skip_map = [(1, 1), (3, 1)]
        self.assertListEqual(
            self._profile._prune_src_lines(src_lines, skip_map),
            [(1, 'foo'), (3, 'baz')])

# pylint: enable=protected-access, missing-docstring
