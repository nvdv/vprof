"""Runtime profile end to end tests."""
# pylint: disable=missing-docstring, blacklisted-name
import json
import functools
import threading
import unittest

from six.moves import urllib

from vprof import flame_graph
from vprof import stats_server
from vprof import profiler
from vprof.tests import test_pkg # pylint: disable=unused-import

_HOST, _PORT = 'localhost', 12345
_MODULE_FILENAME = 'vprof/tests/test_pkg/dummy_module.py'
_PACKAGE_PATH = 'vprof/tests/test_pkg/'


class FlameGraphModuleEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = flame_graph.FlameGraphProfiler(
            _MODULE_FILENAME).run()
        stats_handler = functools.partial(
            stats_server.StatsHandler, program_stats)
        self.server = stats_server.StatsServer(
            (_HOST, _PORT), stats_handler)
        threading.Thread(target=self.server.serve_forever).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def testRequest(self):
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        response_data = stats_server.decompress_data(response.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertEqual(stats['objectName'], '%s (module)' % _MODULE_FILENAME)
        self.assertTrue('sampleInterval' in stats)
        self.assertTrue('runTime' in stats)
        self.assertTrue('totalSamples' in stats)


class FlameGraphPackageEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = flame_graph.FlameGraphProfiler(
            _PACKAGE_PATH).run()
        stats_handler = functools.partial(
            stats_server.StatsHandler, program_stats)
        self.server = stats_server.StatsServer(
            (_HOST, _PORT), stats_handler)
        threading.Thread(target=self.server.serve_forever).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def testRequest(self):
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        response_data = stats_server.decompress_data(response.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertEqual(stats['objectName'], '%s (package)' % _PACKAGE_PATH)
        self.assertTrue('sampleInterval' in stats)
        self.assertTrue('runTime' in stats)
        self.assertTrue('totalSamples' in stats)


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
        threading.Thread(target=self.server.serve_forever).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def testRequest(self):
        profiler.run(
            self._func, 'c', ('foo', 'bar'), host=_HOST, port=_PORT)
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        response_data = stats_server.decompress_data(response.read())
        stats = json.loads(response_data.decode('utf-8'))
        self.assertEqual(stats['c']['objectName'], '_func (function)')
        self.assertTrue('sampleInterval' in stats['c'])
        self.assertTrue('runTime' in stats['c'])
        self.assertTrue('totalSamples' in stats['c'])


# pylint: enable=missing-docstring, blacklisted-name
