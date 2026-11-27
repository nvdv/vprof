"""End-to-end tests for code heatmap module."""
import functools
import gzip
import json
import inspect
import threading
import os
import unittest
import urllib.request

from vprof import code_heatmap
from vprof import stats_server
from vprof import runner

_HOST, _PORT = 'localhost', 0
_MODULE_FILENAME = 'vprof/tests/test_pkg/dummy_module.py'
_PACKAGE_PATH = 'vprof/tests/test_pkg/'
_DUMMY_MODULE_SOURCELINES = [
    ['line', 1, 'def dummy_fib(n):'],
    ['line', 2, '    if n < 2:'],
    ['line', 3, '        return n'],
    ['line', 4, '    return dummy_fib(n - 1) + dummy_fib(n - 2)'],
    ['line', 5, '']]
_MAIN_MODULE_SOURCELINES = [
    ['line', 1, 'from test_pkg import dummy_module'],
    ['line', 2, ''],
    ['line', 3, 'dummy_module.dummy_fib(5)'],
    ['line', 4, '']]
_POLL_INTERVAL = 0.01


class CodeHeatmapModuleEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = code_heatmap.CodeHeatmapProfiler(
            _MODULE_FILENAME).run()
        stats_handler = functools.partial(
            stats_server.StatsHandler, program_stats)
        self.server = stats_server.StatsServer(
            (_HOST, _PORT), stats_handler)
        threading.Thread(
            target=self.server.serve_forever,
            kwargs={'poll_interval': _POLL_INTERVAL}).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def testRequest(self):
        with urllib.request.urlopen(
                f'http://{_HOST}:{self.server.server_port}/profile') as resp:
            response_data = gzip.decompress(resp.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertEqual(stats['objectName'], _MODULE_FILENAME)
        self.assertTrue(stats['runTime'] > 0)
        heatmaps = stats['heatmaps']
        self.assertEqual(len(heatmaps), 1)
        self.assertTrue(
            os.path.abspath(_MODULE_FILENAME) in heatmaps[0]['name'])
        self.assertDictEqual(heatmaps[0]['executionCount'], {'1': 1})
        self.assertListEqual(heatmaps[0]['srcCode'], _DUMMY_MODULE_SOURCELINES)


class CodeHeatmapPackageEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = code_heatmap.CodeHeatmapProfiler(
            _PACKAGE_PATH).run()
        stats_handler = functools.partial(
            stats_server.StatsHandler, program_stats)
        self.server = stats_server.StatsServer(
            (_HOST, _PORT), stats_handler)
        threading.Thread(
            target=self.server.serve_forever,
            kwargs={'poll_interval': _POLL_INTERVAL}).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def testRequest(self):
        with urllib.request.urlopen(
                f'http://{_HOST}:{self.server.server_port}/profile') as resp:
            response_data = gzip.decompress(resp.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertEqual(stats['objectName'], _PACKAGE_PATH)
        self.assertTrue(stats['runTime'] > 0)
        heatmap_files = {heatmap['name'] for heatmap in stats['heatmaps']}
        self.assertTrue(os.path.abspath(
            'vprof/tests/test_pkg/__main__.py') in heatmap_files)
        self.assertTrue(os.path.abspath(
            'vprof/tests/test_pkg/dummy_module.py') in heatmap_files)


class CodeHeatmapFunctionEndToEndTest(unittest.TestCase):

    def setUp(self):

        def _func(arg1, arg2):
            result = arg1 + arg2
            return result
        self._func = _func

        stats_handler = functools.partial(
            stats_server.StatsHandler, {})
        self.server = stats_server.StatsServer(
            (_HOST, _PORT), stats_handler)
        threading.Thread(
            target=self.server.serve_forever,
            kwargs={'poll_interval': _POLL_INTERVAL}).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def testRequest(self):
        runner.run(
            self._func, 'h', ('foo', 'bar'),
            host=_HOST, port=self.server.server_port)
        with urllib.request.urlopen(
                f'http://{_HOST}:{self.server.server_port}/profile') as resp:
            response_data = gzip.decompress(resp.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertTrue(stats['h']['runTime'] > 0)
        heatmaps = stats['h']['heatmaps']
        curr_filename = inspect.getsourcefile(self._func)
        _, start_line = inspect.getsourcelines(self._func)
        self.assertEqual(stats['h']['objectName'],
                         f'_func @ {curr_filename} (function)')
        self.assertEqual(len(heatmaps), 1)
        self.assertDictEqual(
            heatmaps[0]['executionCount'],
            {str(start_line + 1): 1, str(start_line + 2): 1})
        self.assertListEqual(
            heatmaps[0]['srcCode'],
            [['line', start_line, '        def _func(arg1, arg2):\n'],
             ['line', start_line + 1, '            result = arg1 + arg2\n'],
             ['line', start_line + 2, '            return result\n']])
