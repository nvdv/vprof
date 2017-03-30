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
        self._calc = object.__new__(code_heatmap._CodeHeatmapCalculator)

    def testInit(self):
        self._calc.__init__()
        self.assertEqual(self._calc.all_code, set())
        self.assertEqual(self._calc.original_trace_function, sys.gettrace())
        self.assertEqual(self._calc.heatmap, defaultdict(int))

    def testAddCode(self):
        code = mock.MagicMock()
        self._calc.all_code = set()
        self._calc.add_code(code)
        self.assertIn(code, self._calc.all_code)

    @mock.patch('os.path.abspath')
    def testCalcHeatmap(self, abspath_mock):
        abspath_mock.side_effect = lambda arg: arg
        self._calc._heatmap = defaultdict(lambda: defaultdict(int))
        self._calc._execution_count = defaultdict(lambda: defaultdict(float))
        self._calc.prev_lineno = None
        event, arg = 'line', mock.MagicMock()
        frame1, frame2 = mock.MagicMock(), mock.MagicMock()
        frame1.f_code, frame2.f_code = mock.MagicMock(), mock.MagicMock()
        frame1.f_code.co_filename = 'foo.py'
        frame2.f_code.co_filename = 'foo.py'
        frame1.f_lineno, frame2.f_lineno = 1, 2
        self._calc.all_code = set((frame1.f_code, frame2.f_code))

        self._calc.calc_heatmap(frame1, event, arg)
        self._calc.calc_heatmap(frame2, event, arg)

        fname, lineno = frame1.f_code.co_filename, frame1.f_lineno
        self.assertEqual(self._calc._execution_count[fname][lineno], 1)
        self.assertEqual(self._calc._execution_count[fname][lineno], 1)


class CodeHeatmapProfileUnitTest(unittest.TestCase):
    def setUp(self):
        self._profile = object.__new__(code_heatmap.CodeHeatmapProfiler)

    def testCalcSkips(self):
        heatmap = {1: 1, 2: 1, 3: 1}
        self.assertListEqual(self._profile._calc_skips(heatmap, 3), [])

        heatmap = {1: 1, 2: 1, 99: 1, 102: 1, 115: 10}
        self.assertListEqual(
            self._profile._calc_skips(heatmap, 115), [(2, 96), (102, 12)])

        heatmap = {1: 1, 102: 1, 103: 1, 104: 1, 105: 1}
        self.assertListEqual(
            self._profile._calc_skips(heatmap, 115), [(1, 100)])

    def testSkipLines(self):
        self._profile._MIN_SKIP_SIZE = 0

        src_lines, skip_map = ['foo', 'bar', 'baz'], []
        expected_result = [
            ['line', 1, 'foo'], ['line', 2, 'bar'], ['line', 3, 'baz']]
        self.assertListEqual(
            self._profile._skip_lines(src_lines, skip_map), expected_result)

        src_lines, skip_map = ['foo', 'bar', 'baz', 'hahaha'], [(1, 2)]
        self._profile._SKIP_LINES = 1
        expected_result = [
            ['line', 1, 'foo'], ['skip', 2], ['line', 4, 'hahaha']]
        self.assertListEqual(
            self._profile._skip_lines(src_lines, skip_map), expected_result)

        src_lines = ['foo', 'bar', 'baz', 'ha', 'haha']
        skip_map = [(2, 2)]
        expected_result = [
            ['line', 1, 'foo'], ['line', 2, 'bar'],
            ['skip', 2], ['line', 5, 'haha']]
        self.assertListEqual(
            self._profile._skip_lines(src_lines, skip_map), expected_result)

        src_lines = ['foo', 'bar', 'baz', 'ha', 'haha']
        skip_map = [(2, 1), (3, 1)]
        expected_result = [
            ['line', 1, 'foo'], ['line', 2, 'bar'],
            ['skip', 2], ['line', 5, 'haha']]
        self.assertListEqual(
            self._profile._skip_lines(src_lines, skip_map), expected_result)

# pylint: enable=protected-access, missing-docstring
