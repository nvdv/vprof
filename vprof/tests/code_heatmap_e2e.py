"""End-to-end tests for code heatmap module."""
# pylint: disable=missing-docstring, blacklisted-name
import functools
import json
import threading
import unittest

from six.moves import urllib

from vprof import code_heatmap
from vprof import stats_server
from vprof import runner
from vprof.tests import test_pkg # pylint: disable=unused-import

_HOST, _PORT = 'localhost', 12345
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
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        response_data = stats_server.decompress_data(response.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertEqual(stats['objectName'], _MODULE_FILENAME)
        self.assertTrue(stats['runTime'] > 0)
        heatmaps = stats['heatmaps']
        self.assertEqual(len(heatmaps), 1)
        self.assertEqual(heatmaps[0]['name'], _MODULE_FILENAME)
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
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        response_data = stats_server.decompress_data(response.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertEqual(stats['objectName'], _PACKAGE_PATH)
        self.assertTrue(stats['runTime'] > 0)
        heatmaps = stats['heatmaps']
        self.assertEqual(len(heatmaps), 2)
        self.assertTrue(
            'vprof/tests/test_pkg/__main__.py' in heatmaps[0]['name'])
        self.assertTrue(
            'vprof/tests/test_pkg/dummy_module.py' in heatmaps[1]['name'])
        self.assertListEqual(heatmaps[0]['srcCode'], _MAIN_MODULE_SOURCELINES)
        self.assertTrue(heatmaps[0]['runTime'] > 0)
        self.assertListEqual(heatmaps[1]['srcCode'], _DUMMY_MODULE_SOURCELINES)
        self.assertTrue(heatmaps[1]['runTime'] > 0)


class CodeHeatmapFunctionEndToEndTest(unittest.TestCase):

    def setUp(self):

        def _func(foo, bar):
            baz = foo + bar
            return baz
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
            self._func, 'h', ('foo', 'bar'), host=_HOST, port=_PORT)
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        response_data = stats_server.decompress_data(response.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertTrue(stats['h']['runTime'] > 0)
        heatmaps = stats['h']['heatmaps']
        self.assertEqual(len(heatmaps), 1)
        self.assertTrue('function _func' in heatmaps[0]['name'])
        self.assertDictEqual(
            heatmaps[0]['executionCount'], {'104': 1, '105': 1})
        self.assertListEqual(
            heatmaps[0]['srcCode'],
            [['line', 103, '        def _func(foo, bar):\n'],
             ['line', 104, u'            baz = foo + bar\n'],
             ['line', 105, u'            return baz\n']])

# pylint: enable=missing-docstring, blacklisted-name
