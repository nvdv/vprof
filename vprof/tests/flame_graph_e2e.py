"""End-to-end tests for flame graph module."""
# pylint: disable=missing-docstring, protected-access, disallowed-name
import functools
import gzip
import json
import inspect
import signal
import threading
import unittest
import urllib.request

from vprof import flame_graph
from vprof import stats_server
from vprof import runner
from vprof.tests import test_pkg # pylint: disable=unused-import

_HOST, _PORT = 'localhost', 0
_MODULE_FILENAME = 'vprof/tests/test_pkg/dummy_module.py'
_PACKAGE_PATH = 'vprof/tests/test_pkg/'
_POLL_INTERVAL = 0.01


@unittest.skipUnless(
    hasattr(signal, 'SIGPROF'), 'SIGPROF is not available on this platform')
class FlameGraphModuleEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = flame_graph.FlameGraphProfiler(
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
                f'http://{_HOST}:{self.server.server_port}/profile') as response:
            response_data = gzip.decompress(response.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertEqual(stats['objectName'], f'{_MODULE_FILENAME} (module)')
        self.assertEqual(stats['sampleInterval'], flame_graph._SAMPLE_INTERVAL)
        self.assertTrue(stats['runTime'] > 0)
        self.assertTrue(len(stats['callStats']) >= 0)
        self.assertTrue(stats['totalSamples'] >= 0)


@unittest.skipUnless(
    hasattr(signal, 'SIGPROF'), 'SIGPROF is not available on this platform')
class FlameGraphPackageEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = flame_graph.FlameGraphProfiler(
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
                f'http://{_HOST}:{self.server.server_port}/profile') as response:
            response_data = gzip.decompress(response.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertEqual(stats['objectName'], f'{_PACKAGE_PATH} (package)')
        self.assertEqual(stats['sampleInterval'], flame_graph._SAMPLE_INTERVAL)
        self.assertTrue(stats['runTime'] > 0)
        self.assertTrue(len(stats['callStats']) >= 0)
        self.assertTrue(stats['totalSamples'] >= 0)


@unittest.skipUnless(
    hasattr(signal, 'SIGPROF'), 'SIGPROF is not available on this platform')
class FlameGraphFunctionEndToEndTest(unittest.TestCase):

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
            self._func, 'c', ('foo', 'bar'),
            host=_HOST, port=self.server.server_port)
        with urllib.request.urlopen(
                f'http://{_HOST}:{self.server.server_port}/profile') as response:
            response_data = gzip.decompress(response.read())
        stats = json.loads(response_data.decode('utf-8'))
        curr_filename = inspect.getsourcefile(self._func)
        self.assertEqual(stats['c']['objectName'],
                         f'_func @ {curr_filename} (function)')
        self.assertEqual(
            stats['c']['sampleInterval'], flame_graph._SAMPLE_INTERVAL)
        self.assertTrue(stats['c']['runTime'] > 0)
        self.assertTrue(len(stats['c']['callStats']) >= 0)
        self.assertTrue(stats['c']['totalSamples'] >= 0)

# pylint: enable=missing-docstring, disallowed-name, protected-access
