"""Runtime profile end to end tests."""
# pylint: disable=missing-docstring, blacklisted-name
import json
import functools
import threading
import unittest

from six.moves import urllib

from vprof import runtime_profile
from vprof import stats_server
from vprof import vprof_runtime
from vprof.tests import test_pkg # pylint: disable=unused-import

_HOST, _PORT = 'localhost', 12345
_MODULE_FILENAME = 'vprof/tests/test_pkg/dummy_module.py'
_PACKAGE_PATH = 'vprof/tests/test_pkg/'
_PACKAGE_NAME = 'vprof.tests.test_pkg'


class RuntimeProfileModuleEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = runtime_profile.RuntimeProfile(
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
        stats = json.loads(response.read().decode('utf-8'))
        self.assertEqual(stats['programName'], _MODULE_FILENAME)
        self.assertTrue('primitiveCalls' in stats)
        self.assertTrue('runTime' in stats)
        self.assertTrue('totalCalls' in stats)


class RuntimeProfilePackageAsPathEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = runtime_profile.RuntimeProfile(
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
        stats = json.loads(response.read().decode('utf-8'))
        self.assertEqual(stats['programName'], _PACKAGE_PATH)
        self.assertTrue('primitiveCalls' in stats)
        self.assertTrue('runTime' in stats)
        self.assertTrue('totalCalls' in stats)


class RuntimeProfileImportedPackageEndToEndTest(unittest.TestCase):

    def setUp(self):
        program_stats = runtime_profile.RuntimeProfile(
            _PACKAGE_NAME).run()
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
        stats = json.loads(response.read().decode('utf-8'))
        self.assertEqual(stats['programName'], _PACKAGE_NAME)
        self.assertTrue('primitiveCalls' in stats)
        self.assertTrue('runTime' in stats)
        self.assertTrue('totalCalls' in stats)


class RuntimeProfileFunctionEndToEndTest(unittest.TestCase):

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
        vprof_runtime.run(
            self._func, 'c', ('foo', 'bar'), host=_HOST, port=_PORT)
        response = urllib.request.urlopen(
            'http://%s:%s/profile' % (_HOST, _PORT))
        stats = json.loads(response.read().decode('utf-8'))
        self.assertTrue('function _func' in stats['c']['programName'])
        self.assertEqual(stats['c']['totalCalls'], 2)

# pylint: enable=missing-docstring, blacklisted-name
