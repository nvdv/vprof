"""End-to-end tests for memory profiler module."""
import builtins
import functools
import gzip
import json
import inspect
import threading
import unittest
import urllib.request

from vprof import memory_profiler
from vprof import stats_server
from vprof import runner

builtins.initial_rss_size = 0

_HOST, _PORT = 'localhost', 0
_MODULE_FILENAME = 'vprof/tests/test_pkg/dummy_module.py'
_PACKAGE_PATH = 'vprof/tests/test_pkg/'
_POLL_INTERVAL = 0.01


class MemoryProfilerModuleEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = memory_profiler.MemoryProfiler(
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
        self.assertEqual(stats['objectName'], f'{_MODULE_FILENAME} (module)')
        self.assertEqual(stats['totalEvents'], 1)
        self.assertEqual(stats['codeEvents'][0][0], 1)
        self.assertEqual(stats['codeEvents'][0][1], 1)
        self.assertEqual(stats['codeEvents'][0][3], '<module>')
        self.assertEqual(
            stats['codeEvents'][0][4], 'vprof/tests/test_pkg/dummy_module.py')


class MemoryProfilerPackageEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = memory_profiler.MemoryProfiler(
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
        self.assertEqual(stats['objectName'], f'{_PACKAGE_PATH} (package)')
        self.assertTrue(stats['totalEvents'] > 0)
        self.assertTrue(len(stats['objectsCount']) > 0)


class MemoryProfilerFunctionEndToEndTest(unittest.TestCase):

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
            self._func, 'm', ('foo', 'bar'),
            host=_HOST, port=self.server.server_port)
        with urllib.request.urlopen(
                f'http://{_HOST}:{self.server.server_port}/profile') as resp:
            response_data = gzip.decompress(resp.read())
        stats = json.loads(response_data.decode('utf-8'))
        curr_filename = inspect.getsourcefile(self._func)
        _, start_line = inspect.getsourcelines(self._func)
        self.assertEqual(stats['m']['objectName'],
                         f'_func @ {curr_filename} (function)')
        self.assertEqual(stats['m']['totalEvents'], 2)
        self.assertEqual(stats['m']['codeEvents'][0][0], 1)
        self.assertEqual(stats['m']['codeEvents'][0][1], start_line + 1)
        self.assertEqual(stats['m']['codeEvents'][0][3], '_func')
        self.assertEqual(stats['m']['codeEvents'][1][0], 2)
        self.assertEqual(stats['m']['codeEvents'][1][1], start_line + 2)
        self.assertEqual(stats['m']['codeEvents'][1][3], '_func')
