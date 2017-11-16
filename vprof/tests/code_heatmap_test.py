# pylint: disable=protected-access, missing-docstring
import os
import sys
import unittest

from collections import defaultdict
from vprof import code_heatmap


class CheckStandardDirUnittest(unittest.TestCase):

    def setUp(self):
        self.original_paths = code_heatmap._STDLIB_PATHS
        code_heatmap._STDLIB_PATHS = ['/usr/local/python/lib']

    def tearDown(self):
        code_heatmap._STDLIB_PATHS = self.original_paths

    def testCheckStandardDir(self):
        self.assertTrue(
            code_heatmap.check_standard_dir(
                '/usr/local/python/lib/foo'))
        self.assertTrue(
            code_heatmap.check_standard_dir(
                '/usr/local/python/lib/foo/bar'))

        self.assertTrue(
            code_heatmap.check_standard_dir(
                '/Users/foobar/test/lib/python3.6/site-packages'))

        self.assertFalse(
            code_heatmap.check_standard_dir('/usr/local/bin'))
        self.assertFalse(
            code_heatmap.check_standard_dir('/usr/local'))


class CodeHeatmapCalculatorUnittest(unittest.TestCase):
    def setUp(self):
        self._calc = object.__new__(code_heatmap._CodeHeatmapCalculator)

    def testInit(self):
        self._calc.__init__()
        self.assertEqual(self._calc.original_trace_function, sys.gettrace())
        self.assertEqual(
            self._calc._heatmap, defaultdict(lambda: defaultdict(float)))
        self.assertEqual(
            self._calc._execution_count, defaultdict(lambda: defaultdict(int)))

    def testLinesWithoutStdlibSimple(self):
        self._calc.lines = [
            ['foo.py', 1, 0.5],
            ['foo.py', 2, 0.6],
            ['foo.py', 3, 0.1],
        ]
        result = list(self._calc.lines_without_stdlib)
        basename_result = [
            [os.path.basename(abspath), lineno, runtime]
            for abspath, lineno, runtime in result]
        self.assertListEqual(
            basename_result,
            [['foo.py', 1, 0.5],
             ['foo.py', 2, 0.6],
             ['foo.py', 3, 0.1]]
        )

    def testLinesWithoutStdlib(self):
        self._calc.lines = [
            ['foo.py', 1, 0.5],
            ['foo.py', 2, 0.6],
            ['site-packages/bar.py', 1, 0.4],
            ['foo.py', 3, 0.1],
            ['site-packages/baz.py', 1, 0.25],
            ['site-packages/baz.py', 2, 0.11],
            ['site-packages/baz.py', 3, 0.33],
            ['foo.py', 4, 0.77],
        ]
        result = list(self._calc.lines_without_stdlib)
        basename_result = [
            [os.path.basename(abspath), lineno, runtime]
            for abspath, lineno, runtime in result]
        self.assertListEqual(
            basename_result,
            [['foo.py', 1, 0.5],
             ['foo.py', 2, 1.0],
             ['foo.py', 3, 0.79],
             ['foo.py', 4, 0.77]]
        )


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
