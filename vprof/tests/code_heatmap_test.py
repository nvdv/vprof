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
